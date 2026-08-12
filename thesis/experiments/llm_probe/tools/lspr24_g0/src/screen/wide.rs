use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fmt::{Display, Formatter};
use std::fs::{self, File, OpenOptions};
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};

use arrow_array::{Array, Int32Array, Int64Array, RecordBatch, StringArray};
use arrow_schema::{DataType, Schema};
use parquet::arrow::ProjectionMask;
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use serde::Serialize;
use sha2::{Digest, Sha256};

use super::config::{DevelopmentWideConfig, DevelopmentWideConfigError};
use super::history::HistoryRelationRow;
use super::output::{
    DevelopmentParquetWriters, ScreenOutputError, write_json_document, write_receipt_json,
};
use super::{
    EndpointDirection, NumericColumn, ScreenSourceError, resolve_protected_endpoints,
    utc_ns_from_micros,
};
use crate::{
    AggOp, Direction, FieldManifestEntry, FieldManifestError, SchemaAudit, SchemaAuditError,
    build_field_manifest, write_field_manifest_json,
};

/// 窗口长度：纪元对齐、左闭右开 5 秒。
pub const DEVELOPMENT_WIDE_WINDOW_NS: i64 = 5_000_000_000;
const HISTORY_HORIZONS: [usize; 4] = [1, 4, 16, 32];
const PARTITION_COUNT: usize = 192;
const OUTPUT_BATCH_SIZE: usize = 8_192;
const SCAN_PROGRESS_INTERVAL: u64 = 1_000_000;

/// 单次开发宽表物化收据。
#[derive(Debug, Clone, Serialize)]
pub struct DevelopmentWideReceipt {
    pub schema_version: &'static str,
    pub contract_version: String,
    pub contract_sha256: String,
    pub wide_path: PathBuf,
    pub label_path: PathBuf,
    pub field_manifest_path: PathBuf,
    pub temporal_relations_path: PathBuf,
    pub dataset_manifest_path: PathBuf,
    pub development_window_count: u64,
    pub training_window_count: u64,
    pub validation_window_count: u64,
    pub final_window_count_discarded: u64,
    pub non_finite_flow_count: u64,
    pub timestamp_order_corrected_flow_count: u64,
    pub screen_ready: bool,
    pub formal_evidence: bool,
    pub final_accessed: bool,
}

/// 数据产品唯一入口中的单个制品记录。
#[derive(Debug, Clone, Serialize)]
pub struct DatasetArtifact {
    pub path: PathBuf,
    pub sha256: String,
}

/// 供所有基线和序列模型消费的大宽表数据清单。
#[derive(Debug, Clone, Serialize)]
pub struct DatasetManifest {
    pub schema_version: &'static str,
    pub contract_version: String,
    pub contract_sha256: String,
    pub primary_key: Vec<&'static str>,
    pub training_split: &'static str,
    pub validation_split: &'static str,
    pub final_split: &'static str,
    pub model_feature_columns: Vec<String>,
    pub artifacts: BTreeMap<String, DatasetArtifact>,
}

/// 已排序的开发宽表行。
#[derive(Debug, Clone)]
pub(crate) struct WideRow {
    pub(crate) window_row_index: u64,
    pub(crate) window_start_ns: i64,
    pub(crate) window_end_ns: i64,
    pub(crate) protected_endpoint_sha256: String,
    pub(crate) split_name: String,
    pub(crate) has_activity: bool,
    pub(crate) seconds_since_previous_active_window: i64,
    pub(crate) consecutive_empty_window_count: u64,
    pub(crate) label: i32,
    pub(crate) features: Vec<f64>,
}

/// 开发宽表物化失败。
#[derive(Debug)]
pub enum DevelopmentWideError {
    Config(DevelopmentWideConfigError),
    InputRoot(PathBuf),
    Io {
        path: PathBuf,
        source: std::io::Error,
    },
    Parquet(String),
    Schema(String),
    Source(ScreenSourceError),
    SchemaAudit(SchemaAuditError),
    FieldManifest(FieldManifestError),
    Output(ScreenOutputError),
    TimestampOrder {
        source_row_index: u64,
    },
    WindowOverflow {
        value: i64,
    },
    InsufficientActivityWindows,
    CountOverflow,
}

impl Display for DevelopmentWideError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Config(error) => write!(formatter, "开发宽表配置错误：{error}"),
            Self::InputRoot(path) => write!(formatter, "运行根目录不可用：{}", path.display()),
            Self::Io { path, source } => {
                write!(formatter, "访问 {} 失败：{source}", path.display())
            }
            Self::Parquet(message) => write!(formatter, "Parquet 读取失败：{message}"),
            Self::Schema(message) => write!(formatter, "原始模式错误：{message}"),
            Self::Source(error) => write!(formatter, "原始行解析失败：{error}"),
            Self::SchemaAudit(error) => write!(formatter, "模式审计失败：{error}"),
            Self::FieldManifest(error) => write!(formatter, "字段清单失败：{error}"),
            Self::Output(error) => write!(formatter, "开发宽表输出失败：{error}"),
            Self::TimestampOrder { source_row_index } => {
                write!(formatter, "源行 {source_row_index} 的起止时间逆序")
            }
            Self::WindowOverflow { value } => write!(formatter, "窗口边界溢出：{value}"),
            Self::InsufficientActivityWindows => {
                formatter.write_str("活动窗口不足以建立 60/20/20 切分")
            }
            Self::CountOverflow => formatter.write_str("开发宽表计数溢出"),
        }
    }
}

impl Error for DevelopmentWideError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Config(error) => Some(error),
            Self::Io { source, .. } => Some(source),
            Self::Source(error) => Some(error),
            Self::SchemaAudit(error) => Some(error),
            Self::FieldManifest(error) => Some(error),
            Self::Output(error) => Some(error),
            _ => None,
        }
    }
}

/// 从原始 Parquet 一次构建开发宽表、标签旁车、历史索引、字段清单与收据。
pub fn materialize_development_wide(
    config: &DevelopmentWideConfig,
) -> Result<DevelopmentWideReceipt, DevelopmentWideError> {
    config.validate().map_err(DevelopmentWideError::Config)?;
    if !config.run_root().is_dir() {
        return Err(DevelopmentWideError::InputRoot(
            config.run_root().to_path_buf(),
        ));
    }

    let audit = SchemaAudit::from_parquet_footer(config.parquet_path())
        .map_err(DevelopmentWideError::SchemaAudit)?;
    let entries = build_field_manifest(&audit).map_err(DevelopmentWideError::FieldManifest)?;
    let field_manifest_path = config.field_manifest_path().to_path_buf();
    write_field_manifest_json(&entries, &field_manifest_path)
        .map_err(DevelopmentWideError::FieldManifest)?;

    let projected = projected_columns(&entries);
    let numeric_names = numeric_source_columns(&entries);
    let numeric_indices = numeric_names
        .iter()
        .enumerate()
        .map(|(index, name)| (name.clone(), index))
        .collect::<BTreeMap<_, _>>();
    let working_path = config.run_root().join("working");
    fs::create_dir(&working_path).map_err(|source| DevelopmentWideError::Io {
        path: working_path.clone(),
        source,
    })?;
    let partition_paths = (0..PARTITION_COUNT)
        .map(|index| working_path.join(format!("raw-part-{index:03}.bin")))
        .collect::<Vec<_>>();
    let mut partition_writers = create_partition_writers(&partition_paths)?;
    let mut active_window_starts = BTreeSet::new();
    let mut source_row_index = 0_u64;
    let mut non_finite_flow_count = 0_u64;
    let mut timestamp_order_corrected_flow_count = 0_u64;
    for batch in read_projected_batches(config.parquet_path(), &projected)? {
        let batch = batch?;
        let columns = SourceBatch::try_new(&batch, &entries)?;
        for row in 0..batch.num_rows() {
            partition_row(
                &columns,
                row,
                source_row_index,
                &numeric_names,
                &mut partition_writers,
                &mut active_window_starts,
                &mut non_finite_flow_count,
                &mut timestamp_order_corrected_flow_count,
            )?;
            source_row_index = source_row_index
                .checked_add(1)
                .ok_or(DevelopmentWideError::CountOverflow)?;
            if source_row_index % SCAN_PROGRESS_INTERVAL == 0 {
                println!("已分区扫描 {source_row_index} 条原始流");
            }
        }
    }
    for writer in &mut partition_writers {
        writer.flush().map_err(|source| DevelopmentWideError::Io {
            path: working_path.clone(),
            source,
        })?;
    }
    drop(partition_writers);

    let split = ActivitySplit::from_active_windows(&active_window_starts)?;
    let wide_path = config.run_root().join("development-wide.parquet");
    let label_path = config.run_root().join("development-labels.parquet");
    let temporal_relations_path = config.run_root().join("temporal-relations.parquet");
    let mut parquet_writers = DevelopmentParquetWriters::create(
        &wide_path,
        &label_path,
        &temporal_relations_path,
        &entries,
    )
    .map_err(DevelopmentWideError::Output)?;
    let mut counts = MaterializationCounts::default();
    for (index, partition_path) in partition_paths.iter().enumerate() {
        let mut windows = aggregate_partition(
            partition_path,
            &entries,
            &numeric_indices,
            numeric_names.len(),
        )?;
        fill_no_flow_windows(&mut windows, entries.len())?;
        write_partition_rows(&windows, &entries, split, &mut counts, &mut parquet_writers)?;
        drop(windows);
        fs::remove_file(partition_path).map_err(|source| DevelopmentWideError::Io {
            path: partition_path.clone(),
            source,
        })?;
        println!(
            "已聚合分区 {}/{}，累计开发窗口 {}",
            index + 1,
            PARTITION_COUNT,
            counts.development_window_count
        );
    }
    parquet_writers
        .finish()
        .map_err(DevelopmentWideError::Output)?;
    fs::remove_dir(&working_path).map_err(|source| DevelopmentWideError::Io {
        path: working_path,
        source,
    })?;

    let dataset_manifest_path = config.run_root().join("dataset-manifest.json");
    let receipt_path = config.run_root().join("development-wide-receipt.json");
    let receipt = DevelopmentWideReceipt {
        schema_version: "lspr24-development-wide-receipt-v1",
        contract_version: config.contract_version().to_owned(),
        contract_sha256: config.contract_sha256().to_owned(),
        wide_path,
        label_path,
        field_manifest_path,
        temporal_relations_path,
        dataset_manifest_path: dataset_manifest_path.clone(),
        development_window_count: counts.development_window_count,
        training_window_count: counts.training_window_count,
        validation_window_count: counts.validation_window_count,
        final_window_count_discarded: counts.final_window_count_discarded,
        non_finite_flow_count,
        timestamp_order_corrected_flow_count,
        screen_ready: true,
        formal_evidence: false,
        final_accessed: false,
    };
    write_receipt_json(&receipt_path, &receipt).map_err(DevelopmentWideError::Output)?;
    let manifest = DatasetManifest {
        schema_version: "lspr24-screen-dataset-manifest-v1",
        contract_version: config.contract_version().to_owned(),
        contract_sha256: config.contract_sha256().to_owned(),
        primary_key: vec!["protected_endpoint_sha256", "window_start_ns"],
        training_split: "train",
        validation_split: "validation",
        final_split: "final-not-materialized",
        model_feature_columns: entries
            .iter()
            .map(|entry| entry.output_name.clone())
            .collect(),
        artifacts: artifact_manifest(&receipt, &receipt_path)?,
    };
    write_json_document(&dataset_manifest_path, &manifest).map_err(DevelopmentWideError::Output)?;
    Ok(receipt)
}

#[derive(Debug, Default)]
struct MaterializationCounts {
    development_window_count: u64,
    training_window_count: u64,
    validation_window_count: u64,
    final_window_count_discarded: u64,
}

fn projected_columns(entries: &[FieldManifestEntry]) -> Vec<String> {
    let mut columns = BTreeSet::new();
    for column in [
        "mTimestampStart",
        "mTimestampLast",
        "SrcIP",
        "DstIP",
        "External_src",
        "External_dst",
        "Protocol",
        "Conn_state",
        "Label",
    ] {
        columns.insert(column.to_owned());
    }
    for entry in entries {
        for column in &entry.source_columns {
            columns.insert(column.clone());
        }
    }
    columns.into_iter().collect()
}

fn numeric_source_columns(entries: &[FieldManifestEntry]) -> Vec<String> {
    let mut columns = BTreeSet::new();
    for entry in entries {
        for column in &entry.source_columns {
            if !matches!(
                column.as_str(),
                "External_src" | "External_dst" | "Protocol" | "Conn_state"
            ) {
                columns.insert(column.clone());
            }
        }
    }
    columns.into_iter().collect()
}

fn create_partition_writers(
    paths: &[PathBuf],
) -> Result<Vec<BufWriter<File>>, DevelopmentWideError> {
    paths
        .iter()
        .map(|path| {
            OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(path)
                .map(BufWriter::new)
                .map_err(|source| DevelopmentWideError::Io {
                    path: path.clone(),
                    source,
                })
        })
        .collect()
}

fn partition_row(
    columns: &SourceBatch<'_>,
    row: usize,
    source_row_index: u64,
    numeric_names: &[String],
    partition_writers: &mut [BufWriter<File>],
    active_window_starts: &mut BTreeSet<i64>,
    non_finite_flow_count: &mut u64,
    timestamp_order_corrected_flow_count: &mut u64,
) -> Result<(), DevelopmentWideError> {
    if columns.start.is_null(row)
        || columns.last.is_null(row)
        || columns.src_ip.is_null(row)
        || columns.dst_ip.is_null(row)
    {
        return Ok(());
    }
    let raw_start_ns =
        utc_ns_from_micros(columns.start.value(row)).map_err(DevelopmentWideError::Source)?;
    let raw_last_ns =
        utc_ns_from_micros(columns.last.value(row)).map_err(DevelopmentWideError::Source)?;
    let (_start_ns, last_ns) = if raw_start_ns <= raw_last_ns {
        (raw_start_ns, raw_last_ns)
    } else {
        *timestamp_order_corrected_flow_count = timestamp_order_corrected_flow_count
            .checked_add(1)
            .ok_or(DevelopmentWideError::CountOverflow)?;
        (raw_last_ns, raw_start_ns)
    };
    let assignments = resolve_protected_endpoints(
        Some(columns.src_ip.value(row)),
        Some(columns.dst_ip.value(row)),
        (!columns.external_src.is_null(row)).then(|| columns.external_src.value(row)),
        (!columns.external_dst.is_null(row)).then(|| columns.external_dst.value(row)),
        source_row_index,
    )
    .map_err(DevelopmentWideError::Source)?;
    if assignments.is_empty() {
        return Ok(());
    }
    let window_start_ns = window_start(last_ns)?;
    active_window_starts.insert(window_start_ns);
    let label = (!columns.label.is_null(row))
        .then(|| columns.label.value(row))
        .unwrap_or(-1);
    let has_non_finite = columns
        .numeric
        .values()
        .any(|values| values.is_non_finite(row));
    for assignment in assignments {
        let partition = endpoint_partition(&assignment.canonical_ip);
        write_partition_record(
            &mut partition_writers[partition],
            assignment.canonical_ip,
            window_start_ns,
            label,
            assignment.direction,
            columns.protocol_value(row),
            conn_state_code(columns.conn_state_value(row)),
            has_non_finite,
            columns,
            numeric_names,
            row,
        )?;
    }
    if has_non_finite {
        *non_finite_flow_count = non_finite_flow_count
            .checked_add(1)
            .ok_or(DevelopmentWideError::CountOverflow)?;
    }
    Ok(())
}

fn endpoint_partition(canonical_ip: &[u8; 16]) -> usize {
    let hash = canonical_ip
        .iter()
        .fold(0xcbf2_9ce4_8422_2325_u64, |hash, byte| {
            (hash ^ u64::from(*byte)).wrapping_mul(0x0000_0100_0000_01b3)
        });
    usize::try_from(hash % PARTITION_COUNT as u64).unwrap_or(0)
}

#[allow(clippy::too_many_arguments)]
fn write_partition_record(
    writer: &mut BufWriter<File>,
    canonical_ip: [u8; 16],
    window_start_ns: i64,
    label: i32,
    direction: EndpointDirection,
    protocol: Option<i32>,
    conn_state: u8,
    has_non_finite: bool,
    columns: &SourceBatch<'_>,
    numeric_names: &[String],
    row: usize,
) -> Result<(), DevelopmentWideError> {
    writer
        .write_all(&canonical_ip)
        .and_then(|()| writer.write_all(&window_start_ns.to_le_bytes()))
        .and_then(|()| writer.write_all(&label.to_le_bytes()))
        .and_then(|()| {
            writer.write_all(&[match direction {
                EndpointDirection::Outbound => 0,
                EndpointDirection::Inbound => 1,
            }])
        })
        .and_then(|()| writer.write_all(&protocol.unwrap_or(i32::MIN).to_le_bytes()))
        .and_then(|()| writer.write_all(&[conn_state, u8::from(has_non_finite)]))
        .map_err(|source| DevelopmentWideError::Io {
            path: PathBuf::from("working/raw-partition"),
            source,
        })?;
    for name in numeric_names {
        let value = columns
            .numeric
            .get(name)
            .and_then(|column| column.value_as_f64(row))
            .unwrap_or(f64::NAN);
        writer
            .write_all(&value.to_le_bytes())
            .map_err(|source| DevelopmentWideError::Io {
                path: PathBuf::from("working/raw-partition"),
                source,
            })?;
    }
    Ok(())
}

fn conn_state_code(value: Option<&str>) -> u8 {
    match value.unwrap_or("other") {
        "S0" => 0,
        "S1" => 1,
        "S2" => 2,
        "S3" => 3,
        "SF" => 4,
        "REJ" => 5,
        "RSTO" => 6,
        "RSTR" => 7,
        "RSTOS0" => 8,
        "RSTRH" => 9,
        "SH" => 10,
        "SHR" => 11,
        "OTH" => 12,
        _ => 13,
    }
}

fn conn_state_name(code: u8) -> &'static str {
    match code {
        0 => "s0",
        1 => "s1",
        2 => "s2",
        3 => "s3",
        4 => "sf",
        5 => "rej",
        6 => "rsto",
        7 => "rstr",
        8 => "rstos0",
        9 => "rstrh",
        10 => "sh",
        11 => "shr",
        12 => "oth",
        _ => "other",
    }
}

struct PartitionRecord {
    canonical_ip: [u8; 16],
    window_start_ns: i64,
    label: i32,
    direction: EndpointDirection,
    protocol: Option<i32>,
    conn_state: u8,
    has_non_finite: bool,
}

fn aggregate_partition(
    path: &Path,
    entries: &[FieldManifestEntry],
    numeric_indices: &BTreeMap<String, usize>,
    numeric_count: usize,
) -> Result<BTreeMap<WindowKey, WindowAggregate>, DevelopmentWideError> {
    let file = File::open(path).map_err(|source| DevelopmentWideError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    let mut reader = BufReader::new(file);
    let mut numeric_values = vec![0.0; numeric_count];
    let mut windows = BTreeMap::new();
    while let Some(record) = read_partition_record(path, &mut reader, &mut numeric_values)? {
        let aggregate = windows
            .entry(WindowKey {
                canonical_ip: record.canonical_ip,
                window_start_ns: record.window_start_ns,
            })
            .or_insert_with(|| WindowAggregate::new(entries.len()));
        if record.has_non_finite {
            aggregate.non_finite_flow_count = aggregate
                .non_finite_flow_count
                .checked_add(1)
                .ok_or(DevelopmentWideError::CountOverflow)?;
        } else {
            aggregate.update(
                entries,
                numeric_indices,
                &numeric_values,
                record.protocol,
                record.conn_state,
                record.direction,
                record.label,
            );
        }
    }
    Ok(windows)
}

fn read_partition_record(
    path: &Path,
    reader: &mut BufReader<File>,
    numeric_values: &mut [f64],
) -> Result<Option<PartitionRecord>, DevelopmentWideError> {
    let mut canonical_ip = [0_u8; 16];
    let first_count =
        reader
            .read(&mut canonical_ip)
            .map_err(|source| DevelopmentWideError::Io {
                path: path.to_path_buf(),
                source,
            })?;
    if first_count == 0 {
        return Ok(None);
    }
    if first_count < canonical_ip.len() {
        reader
            .read_exact(&mut canonical_ip[first_count..])
            .map_err(|source| DevelopmentWideError::Io {
                path: path.to_path_buf(),
                source,
            })?;
    }
    let window_start_ns = read_i64(path, reader)?;
    let label = read_i32(path, reader)?;
    let direction = match read_u8(path, reader)? {
        0 => EndpointDirection::Outbound,
        1 => EndpointDirection::Inbound,
        value => {
            return Err(DevelopmentWideError::Schema(format!(
                "分区方向编码非法：{value}"
            )));
        }
    };
    let protocol_value = read_i32(path, reader)?;
    let protocol = (protocol_value != i32::MIN).then_some(protocol_value);
    let conn_state = read_u8(path, reader)?;
    let has_non_finite = match read_u8(path, reader)? {
        0 => false,
        1 => true,
        value => {
            return Err(DevelopmentWideError::Schema(format!(
                "分区非有限标记非法：{value}"
            )));
        }
    };
    for value in numeric_values {
        *value = f64::from_le_bytes(read_bytes::<8>(path, reader)?);
    }
    Ok(Some(PartitionRecord {
        canonical_ip,
        window_start_ns,
        label,
        direction,
        protocol,
        conn_state,
        has_non_finite,
    }))
}

fn read_u8(path: &Path, reader: &mut BufReader<File>) -> Result<u8, DevelopmentWideError> {
    Ok(read_bytes::<1>(path, reader)?[0])
}

fn read_i32(path: &Path, reader: &mut BufReader<File>) -> Result<i32, DevelopmentWideError> {
    Ok(i32::from_le_bytes(read_bytes::<4>(path, reader)?))
}

fn read_i64(path: &Path, reader: &mut BufReader<File>) -> Result<i64, DevelopmentWideError> {
    Ok(i64::from_le_bytes(read_bytes::<8>(path, reader)?))
}

fn read_bytes<const N: usize>(
    path: &Path,
    reader: &mut BufReader<File>,
) -> Result<[u8; N], DevelopmentWideError> {
    let mut bytes = [0_u8; N];
    reader
        .read_exact(&mut bytes)
        .map_err(|source| DevelopmentWideError::Io {
            path: path.to_path_buf(),
            source,
        })?;
    Ok(bytes)
}

fn window_start(value: i64) -> Result<i64, DevelopmentWideError> {
    value
        .div_euclid(DEVELOPMENT_WIDE_WINDOW_NS)
        .checked_mul(DEVELOPMENT_WIDE_WINDOW_NS)
        .ok_or(DevelopmentWideError::WindowOverflow { value })
}

fn fill_no_flow_windows(
    windows: &mut BTreeMap<WindowKey, WindowAggregate>,
    entry_count: usize,
) -> Result<(), DevelopmentWideError> {
    let mut extents = BTreeMap::<[u8; 16], (i64, i64)>::new();
    for key in windows.keys() {
        extents
            .entry(key.canonical_ip)
            .and_modify(|extent| {
                extent.0 = extent.0.min(key.window_start_ns);
                extent.1 = extent.1.max(key.window_start_ns);
            })
            .or_insert((key.window_start_ns, key.window_start_ns));
    }
    for (canonical_ip, (first, last)) in extents {
        let mut window_start_ns = first;
        loop {
            windows
                .entry(WindowKey {
                    canonical_ip,
                    window_start_ns,
                })
                .or_insert_with(|| WindowAggregate::new(entry_count));
            if window_start_ns == last {
                break;
            }
            window_start_ns = window_start_ns
                .checked_add(DEVELOPMENT_WIDE_WINDOW_NS)
                .ok_or(DevelopmentWideError::WindowOverflow {
                    value: window_start_ns,
                })?;
        }
    }
    Ok(())
}

fn write_partition_rows(
    windows: &BTreeMap<WindowKey, WindowAggregate>,
    entries: &[FieldManifestEntry],
    split: ActivitySplit,
    counts: &mut MaterializationCounts,
    parquet_writers: &mut DevelopmentParquetWriters,
) -> Result<(), DevelopmentWideError> {
    let mut rows = Vec::with_capacity(OUTPUT_BATCH_SIZE);
    let mut history_rows = Vec::with_capacity(OUTPUT_BATCH_SIZE * 2);
    let mut current_endpoint = None;
    let mut endpoint_row_indices = Vec::new();
    let mut previous_active_window = None;
    let mut consecutive_empty_windows = 0_u64;
    for (key, aggregate) in windows {
        if current_endpoint != Some(key.canonical_ip) {
            append_endpoint_history(&endpoint_row_indices, &mut history_rows, parquet_writers)?;
            endpoint_row_indices.clear();
            current_endpoint = Some(key.canonical_ip);
            previous_active_window = None;
            consecutive_empty_windows = 0;
        }
        let split_name = split.name_for(key.window_start_ns);
        if split_name == "final" {
            counts.final_window_count_discarded = counts
                .final_window_count_discarded
                .checked_add(1)
                .ok_or(DevelopmentWideError::CountOverflow)?;
            continue;
        }
        let window_end_ns = key
            .window_start_ns
            .checked_add(DEVELOPMENT_WIDE_WINDOW_NS)
            .ok_or(DevelopmentWideError::WindowOverflow {
                value: key.window_start_ns,
            })?;
        let has_activity = aggregate.flow_count > 0 || aggregate.non_finite_flow_count > 0;
        let seconds_since_previous_active_window = previous_active_window
            .map(|previous| {
                key.window_start_ns
                    .saturating_sub(previous)
                    .div_euclid(1_000_000_000)
            })
            .unwrap_or(-1);
        let consecutive_empty_window_count = if has_activity {
            previous_active_window = Some(key.window_start_ns);
            consecutive_empty_windows = 0;
            0
        } else {
            consecutive_empty_windows = consecutive_empty_windows.saturating_add(1);
            consecutive_empty_windows
        };
        let window_row_index = counts.development_window_count;
        rows.push(WideRow {
            window_row_index,
            window_start_ns: key.window_start_ns,
            window_end_ns,
            protected_endpoint_sha256: endpoint_digest_hex(&key.canonical_ip),
            split_name: split_name.to_owned(),
            has_activity,
            seconds_since_previous_active_window,
            consecutive_empty_window_count,
            label: aggregate.label,
            features: aggregate.final_values(entries),
        });
        endpoint_row_indices.push(window_row_index);
        counts.development_window_count = counts
            .development_window_count
            .checked_add(1)
            .ok_or(DevelopmentWideError::CountOverflow)?;
        match split_name {
            "train" => {
                counts.training_window_count = counts
                    .training_window_count
                    .checked_add(1)
                    .ok_or(DevelopmentWideError::CountOverflow)?;
            }
            "validation" => {
                counts.validation_window_count = counts
                    .validation_window_count
                    .checked_add(1)
                    .ok_or(DevelopmentWideError::CountOverflow)?;
            }
            _ => {}
        }
        if rows.len() == OUTPUT_BATCH_SIZE {
            parquet_writers
                .write_rows(entries, &rows)
                .map_err(DevelopmentWideError::Output)?;
            rows.clear();
        }
    }
    append_endpoint_history(&endpoint_row_indices, &mut history_rows, parquet_writers)?;
    parquet_writers
        .write_rows(entries, &rows)
        .map_err(DevelopmentWideError::Output)?;
    parquet_writers
        .write_history(&history_rows)
        .map_err(DevelopmentWideError::Output)
}

fn append_endpoint_history(
    endpoint_rows: &[u64],
    output: &mut Vec<HistoryRelationRow>,
    parquet_writers: &mut DevelopmentParquetWriters,
) -> Result<(), DevelopmentWideError> {
    for horizon in HISTORY_HORIZONS {
        for (index, target_window_row_index) in endpoint_rows.iter().copied().enumerate() {
            if index < horizon {
                continue;
            }
            let next_window_row_index = endpoint_rows.get(index + 1).copied();
            for (offset, history_window_row_index) in endpoint_rows[index - horizon..index]
                .iter()
                .copied()
                .enumerate()
            {
                output.push(HistoryRelationRow {
                    horizon: u32::try_from(horizon).unwrap_or(u32::MAX),
                    target_window_row_index,
                    next_window_row_index,
                    lag: u32::try_from(horizon - offset).unwrap_or(u32::MAX),
                    history_window_row_index,
                });
                if output.len() == OUTPUT_BATCH_SIZE {
                    parquet_writers
                        .write_history(output)
                        .map_err(DevelopmentWideError::Output)?;
                    output.clear();
                }
            }
        }
    }
    Ok(())
}

fn endpoint_digest_hex(canonical_ip: &[u8; 16]) -> String {
    Sha256::digest(canonical_ip)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn artifact_manifest(
    receipt: &DevelopmentWideReceipt,
    receipt_path: &Path,
) -> Result<BTreeMap<String, DatasetArtifact>, DevelopmentWideError> {
    let mut artifacts = BTreeMap::new();
    for (name, path) in [
        ("wide_table", receipt.wide_path.as_path()),
        ("labels", receipt.label_path.as_path()),
        ("field_manifest", receipt.field_manifest_path.as_path()),
        (
            "temporal_relations",
            receipt.temporal_relations_path.as_path(),
        ),
        ("receipt", receipt_path),
    ] {
        artifacts.insert(
            name.to_owned(),
            DatasetArtifact {
                path: fs::canonicalize(path).map_err(|source| DevelopmentWideError::Io {
                    path: path.to_path_buf(),
                    source,
                })?,
                sha256: file_sha256(path)?,
            },
        );
    }
    Ok(artifacts)
}

fn file_sha256(path: &Path) -> Result<String, DevelopmentWideError> {
    let mut file = File::open(path).map_err(|source| DevelopmentWideError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let count = file
            .read(&mut buffer)
            .map_err(|source| DevelopmentWideError::Io {
                path: path.to_path_buf(),
                source,
            })?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
    }
    Ok(hasher
        .finalize()
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect())
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
struct WindowKey {
    canonical_ip: [u8; 16],
    window_start_ns: i64,
}

#[derive(Debug, Clone)]
struct WindowAggregate {
    cells: Vec<AggregateCell>,
    flow_count: u64,
    non_finite_flow_count: u64,
    label: i32,
}

impl WindowAggregate {
    fn new(entry_count: usize) -> Self {
        Self {
            cells: vec![AggregateCell::default(); entry_count],
            flow_count: 0,
            non_finite_flow_count: 0,
            label: -1,
        }
    }

    fn update(
        &mut self,
        entries: &[FieldManifestEntry],
        numeric_indices: &BTreeMap<String, usize>,
        numeric_values: &[f64],
        protocol: Option<i32>,
        conn_state: u8,
        direction: EndpointDirection,
        label: i32,
    ) {
        self.flow_count = self.flow_count.saturating_add(1);
        self.label = self.label.max(label);
        for (index, entry) in entries.iter().enumerate() {
            if !matches_direction(entry.direction_semantics, direction) {
                continue;
            }
            let cell = &mut self.cells[index];
            match entry.aggregation_operator {
                AggOp::NoFlowFlag | AggOp::Ratio | AggOp::Diff => {}
                AggOp::CountState => {
                    if count_state_matches(entry, protocol, conn_state) {
                        cell.add(1.0);
                    }
                }
                AggOp::MissingCount | AggOp::MissingRate | AggOp::ObservedCount => {
                    if let Some(column) = entry.source_columns.first() {
                        match prepared_numeric_value(column, numeric_indices, numeric_values) {
                            Some(_) => cell.observed = cell.observed.saturating_add(1),
                            None => cell.missing = cell.missing.saturating_add(1),
                        }
                    }
                }
                AggOp::Sum | AggOp::LogOneP | AggOp::Min | AggOp::Max | AggOp::Mean => {
                    let value = aggregate_value(entry, numeric_indices, numeric_values, direction);
                    if let Some(value) = value {
                        cell.add(value);
                    }
                }
            }
        }
    }

    fn final_values(&self, entries: &[FieldManifestEntry]) -> Vec<f64> {
        let values = entries
            .iter()
            .zip(&self.cells)
            .map(|(entry, cell)| match entry.aggregation_operator {
                AggOp::Sum | AggOp::CountState => cell.sum,
                AggOp::LogOneP => cell.sum.max(0.0).ln_1p(),
                AggOp::Min => cell.min.unwrap_or(0.0),
                AggOp::Max => cell.max.unwrap_or(0.0),
                AggOp::Mean => {
                    if cell.count == 0 {
                        0.0
                    } else {
                        cell.sum / cell.count as f64
                    }
                }
                AggOp::MissingCount => cell.missing as f64,
                AggOp::MissingRate => {
                    let total = cell.missing.saturating_add(cell.observed);
                    if total == 0 {
                        0.0
                    } else {
                        cell.missing as f64 / total as f64
                    }
                }
                AggOp::ObservedCount => cell.observed as f64,
                AggOp::NoFlowFlag => {
                    if self.flow_count == 0 {
                        1.0
                    } else {
                        0.0
                    }
                }
                AggOp::Ratio | AggOp::Diff => 0.0,
            })
            .collect::<Vec<_>>();
        entries
            .iter()
            .enumerate()
            .map(|(index, entry)| match entry.aggregation_operator {
                AggOp::Ratio => directional_ratio(&entry.output_name, entries, &values),
                AggOp::Diff => directional_difference(&entry.output_name, entries, &values),
                AggOp::CountState if entry.output_name == "win_nonfinite_isolated_count" => {
                    self.non_finite_flow_count as f64
                }
                _ => values[index],
            })
            .collect()
    }
}

#[derive(Debug, Clone, Default)]
struct AggregateCell {
    sum: f64,
    count: u64,
    min: Option<f64>,
    max: Option<f64>,
    observed: u64,
    missing: u64,
}

impl AggregateCell {
    fn add(&mut self, value: f64) {
        self.sum += value;
        self.count = self.count.saturating_add(1);
        self.min = Some(self.min.map_or(value, |current| current.min(value)));
        self.max = Some(self.max.map_or(value, |current| current.max(value)));
    }
}

fn matches_direction(direction: Option<Direction>, endpoint_direction: EndpointDirection) -> bool {
    matches!(
        (direction, endpoint_direction),
        (None | Some(Direction::Both), _)
            | (Some(Direction::Inbound), EndpointDirection::Inbound)
            | (Some(Direction::Outbound), EndpointDirection::Outbound)
    )
}

fn count_state_matches(entry: &FieldManifestEntry, protocol: Option<i32>, conn_state: u8) -> bool {
    match entry.source_columns.first().map(String::as_str) {
        None => true,
        Some("Protocol") => protocol_class(protocol)
            .is_some_and(|class| entry.output_name == format!("win_protocol_{class}_flow_count")),
        Some("Conn_state") => {
            let bucket = conn_state_name(conn_state);
            entry.output_name == format!("win_conn_state_{bucket}_flow_count")
        }
        _ => true,
    }
}

fn protocol_class(protocol: Option<i32>) -> Option<&'static str> {
    match protocol? {
        6 => Some("tcp"),
        17 => Some("udp"),
        1 | 58 => Some("icmp"),
        _ => Some("other"),
    }
}

fn aggregate_value(
    entry: &FieldManifestEntry,
    numeric_indices: &BTreeMap<String, usize>,
    numeric_values: &[f64],
    direction: EndpointDirection,
) -> Option<f64> {
    let source = if entry.semantic_group == crate::SemanticGroup::Direction {
        directional_source(entry, direction)?
    } else {
        entry.source_columns.first()?.as_str()
    };
    prepared_numeric_value(source, numeric_indices, numeric_values)
        .filter(|value| !(entry.missing_rule.starts_with("negative-as-missing") && *value < 0.0))
}

fn prepared_numeric_value(
    source: &str,
    numeric_indices: &BTreeMap<String, usize>,
    numeric_values: &[f64],
) -> Option<f64> {
    let value = *numeric_values.get(*numeric_indices.get(source)?)?;
    value.is_finite().then_some(value)
}

fn directional_source(entry: &FieldManifestEntry, direction: EndpointDirection) -> Option<&str> {
    let is_outbound_metric = entry.direction_semantics == Some(Direction::Outbound);
    let source =
        match (
            entry.output_name.contains("pkts_sum"),
            direction,
            is_outbound_metric,
        ) {
            (true, EndpointDirection::Outbound, true)
            | (true, EndpointDirection::Inbound, false) => "Tot Fwd Pkts",
            (true, _, _) => "Tot Bwd Pkts",
            (false, EndpointDirection::Outbound, true)
            | (false, EndpointDirection::Inbound, false) => "Total Length of Fwd Packet",
            (false, _, _) => "Total Length of Bwd Packet",
        };
    (entry.output_name.contains("pkts_sum") || entry.output_name.contains("bytes_sum"))
        .then_some(source)
}

fn directional_ratio(name: &str, entries: &[FieldManifestEntry], values: &[f64]) -> f64 {
    let metric = name.strip_prefix("win_out_ratio_").unwrap_or_default();
    let outbound = lookup_feature(entries, values, &format!("win_outbound_{metric}"));
    let inbound = lookup_feature(entries, values, &format!("win_inbound_{metric}"));
    if inbound == 0.0 {
        0.0
    } else {
        outbound / inbound
    }
}

fn directional_difference(name: &str, entries: &[FieldManifestEntry], values: &[f64]) -> f64 {
    let metric = name.strip_prefix("win_out_minus_in_").unwrap_or_default();
    lookup_feature(entries, values, &format!("win_outbound_{metric}"))
        - lookup_feature(entries, values, &format!("win_inbound_{metric}"))
}

fn lookup_feature(entries: &[FieldManifestEntry], values: &[f64], name: &str) -> f64 {
    entries
        .iter()
        .position(|entry| entry.output_name == name)
        .map(|index| values[index])
        .unwrap_or(0.0)
}

struct SourceBatch<'a> {
    start: &'a Int64Array,
    last: &'a Int64Array,
    src_ip: &'a StringArray,
    dst_ip: &'a StringArray,
    external_src: &'a StringArray,
    external_dst: &'a StringArray,
    protocol: &'a Int32Array,
    conn_state: &'a StringArray,
    label: &'a Int32Array,
    numeric: BTreeMap<String, NumericColumn<'a>>,
}

impl<'a> SourceBatch<'a> {
    fn try_new(
        batch: &'a RecordBatch,
        entries: &[FieldManifestEntry],
    ) -> Result<Self, DevelopmentWideError> {
        let mut numeric = BTreeMap::new();
        for entry in entries {
            for name in &entry.source_columns {
                if matches!(
                    name.as_str(),
                    "External_src" | "External_dst" | "Protocol" | "Conn_state"
                ) {
                    continue;
                }
                if !numeric.contains_key(name) {
                    numeric.insert(name.clone(), numeric_column(batch, name)?);
                }
            }
        }
        Ok(Self {
            start: int64_column(batch, "mTimestampStart")?,
            last: int64_column(batch, "mTimestampLast")?,
            src_ip: string_column(batch, "SrcIP")?,
            dst_ip: string_column(batch, "DstIP")?,
            external_src: string_column(batch, "External_src")?,
            external_dst: string_column(batch, "External_dst")?,
            protocol: int32_column(batch, "Protocol")?,
            conn_state: string_column(batch, "Conn_state")?,
            label: int32_column(batch, "Label")?,
            numeric,
        })
    }

    fn protocol_value(&self, row: usize) -> Option<i32> {
        (!self.protocol.is_null(row)).then(|| self.protocol.value(row))
    }

    fn conn_state_value(&self, row: usize) -> Option<&str> {
        (!self.conn_state.is_null(row)).then(|| self.conn_state.value(row))
    }
}

type BatchIterator = Box<dyn Iterator<Item = Result<RecordBatch, DevelopmentWideError>>>;

fn read_projected_batches(
    path: &Path,
    columns: &[String],
) -> Result<BatchIterator, DevelopmentWideError> {
    let file = File::open(path).map_err(|source| DevelopmentWideError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)
        .map_err(|error| DevelopmentWideError::Parquet(error.to_string()))?;
    let indices = required_indices(builder.schema(), columns)?;
    let projection = ProjectionMask::roots(builder.parquet_schema(), indices);
    let reader = builder
        .with_projection(projection)
        .with_batch_size(65_536)
        .build()
        .map_err(|error| DevelopmentWideError::Parquet(error.to_string()))?;
    Ok(Box::new(reader.map(|batch| {
        batch.map_err(|error| DevelopmentWideError::Parquet(error.to_string()))
    })))
}

fn required_indices(
    schema: &Schema,
    columns: &[String],
) -> Result<Vec<usize>, DevelopmentWideError> {
    columns
        .iter()
        .map(|column| {
            schema
                .fields()
                .iter()
                .position(|field| field.name() == column)
                .ok_or_else(|| DevelopmentWideError::Schema(format!("缺少列 {column}")))
        })
        .collect()
}

fn typed_column<'a, T: Array + 'static>(
    batch: &'a RecordBatch,
    column: &str,
    expected: DataType,
) -> Result<&'a T, DevelopmentWideError> {
    let index = batch
        .schema()
        .fields()
        .iter()
        .position(|field| field.name() == column)
        .ok_or_else(|| DevelopmentWideError::Schema(format!("缺少投影列 {column}")))?;
    batch
        .column(index)
        .as_any()
        .downcast_ref::<T>()
        .ok_or_else(|| DevelopmentWideError::Schema(format!("列 {column} 必须为 {expected}")))
}

fn int64_column<'a>(
    batch: &'a RecordBatch,
    column: &str,
) -> Result<&'a Int64Array, DevelopmentWideError> {
    typed_column(batch, column, DataType::Int64)
}

fn int32_column<'a>(
    batch: &'a RecordBatch,
    column: &str,
) -> Result<&'a Int32Array, DevelopmentWideError> {
    typed_column(batch, column, DataType::Int32)
}

fn string_column<'a>(
    batch: &'a RecordBatch,
    column: &str,
) -> Result<&'a StringArray, DevelopmentWideError> {
    typed_column(batch, column, DataType::Utf8)
}

fn numeric_column<'a>(
    batch: &'a RecordBatch,
    column: &str,
) -> Result<NumericColumn<'a>, DevelopmentWideError> {
    let index = batch
        .schema()
        .fields()
        .iter()
        .position(|field| field.name() == column)
        .ok_or_else(|| DevelopmentWideError::Schema(format!("缺少投影列 {column}")))?;
    NumericColumn::try_new(column, batch.column(index).as_ref())
        .map_err(DevelopmentWideError::Source)
}

#[derive(Debug, Clone, Copy)]
struct ActivitySplit {
    validation_start_ns: i64,
    final_start_ns: i64,
}

impl ActivitySplit {
    fn from_active_windows(active: &BTreeSet<i64>) -> Result<Self, DevelopmentWideError> {
        let values = active.iter().copied().collect::<Vec<_>>();
        if values.len() < 5 {
            return Err(DevelopmentWideError::InsufficientActivityWindows);
        }
        let training_count = values.len() * 60 / 100;
        let development_count = values.len() * 80 / 100;
        if training_count == 0
            || training_count >= development_count
            || development_count >= values.len()
        {
            return Err(DevelopmentWideError::InsufficientActivityWindows);
        }
        Ok(Self {
            validation_start_ns: values[training_count],
            final_start_ns: values[development_count],
        })
    }

    fn name_for(self, window_start_ns: i64) -> &'static str {
        if window_start_ns < self.validation_start_ns {
            "train"
        } else if window_start_ns < self.final_start_ns {
            "validation"
        } else {
            "final"
        }
    }
}
