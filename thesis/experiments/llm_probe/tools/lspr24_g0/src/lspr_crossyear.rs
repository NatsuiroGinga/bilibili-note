//! LSPR23 到 LSPR24 的流级跨年度开发数据物化。

use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fmt::{Display, Formatter};
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, BufWriter, Read, Write};
use std::net::IpAddr;
use std::num::NonZeroUsize;
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdout, Command, Stdio};
use std::sync::Arc;
use std::time::Instant;

use arrow_array::builder::FixedSizeBinaryBuilder;
use arrow_array::{
    Array, ArrayRef, FixedSizeListArray, Float32Array, Int32Array, Int64Array, RecordBatch,
    StringArray, UInt8Array, UInt16Array,
};
use arrow_schema::{DataType, Field, Schema};
use parquet::arrow::ArrowWriter;
use parquet::arrow::ProjectionMask;
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::canonical::{CanonicalValue, sha256, tuple_encode};
use crate::external_sort::{ExternalSortConfig, stable_external_sort};
use crate::output::{OutputError, PartialOutput};
use crate::screen::NumericColumn;
use crate::types::{EndpointRoleOrder, SortableRecord, SourceRowIndex, StableSortKey};

/// 跨年度物化配置版本。
pub const CROSSYEAR_CONFIG_VERSION: &str = "lspr-crossyear-c12-seed42-v1";
const CONTRACT_VERSION: &str = "lspr23-lspr24-crossyear-contract-v1";
const PAIR_KEY_DOMAIN: &str = "lspr-crossyear-2ip-v1";
const SAMPLE_ID_DOMAIN: &str = "lspr-crossyear-sample-v1";
const SEQUENCE_ID_DOMAIN: &str = "lspr-crossyear-sequence-v1";
const BUCKET_COUNT: usize = 256;
const MAX_BATCH_SIZE: usize = 65_536;
const MAX_SEQUENCE_LENGTH: usize = 128;
const GIB: u64 = 1024 * 1024 * 1024;
const COMMON_FIELD_COUNT: usize = 77;
const NUMERIC_FIELD_COUNT: usize = COMMON_FIELD_COUNT - 1;

/// 冻结的 77 个共同模型字段，顺序即张量顺序。
pub const COMMON_FIELDS: [&str; COMMON_FIELD_COUNT] = [
    "Protocol",
    "Flow Duration",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Tot Fwd Pkts",
    "Tot Bwd Pkts",
    "Total Length of Fwd Packet",
    "Total Length of Bwd Packet",
    "Fwd Packet Length Min",
    "Fwd Packet Length Max",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Min",
    "Bwd Packet Length Max",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    "Flow IAT Mean",
    "Flow IAT Min",
    "Flow IAT Max",
    "Flow IAT Stddev",
    "Fwd IAT Min",
    "Fwd IAT Max",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Tot",
    "Bwd IAT Min",
    "Bwd IAT Max",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Tot",
    "Fwd PSH flags",
    "Bwd PSH flags",
    "Fwd URG flags",
    "Bwd URG flags",
    "Fwd Header Length",
    "Bwd Header Length",
    "Fwd Packets/s",
    "Bwd Packets/s",
    "Packet Length Min",
    "Packet Length Max",
    "Packet Length Mean",
    "Packet Length Std",
    "Packet Length Variance",
    "FIN Flag Cnt",
    "SYN Flag Cnt",
    "RST Flag Cnt",
    "PSH Flag Cnt",
    "ACK Flag Cnt",
    "URG Flag Cnt",
    "CWR Flag Cnt",
    "ECE Flag Cnt",
    "Down/Up Ratio",
    "Average Packet Size",
    "Fwd Segment Size Avg",
    "Bwd Segment Size Avg",
    "Fwd Bytes/Bulk Avg",
    "Fwd Packet/Bulk Avg",
    "Fwd Bulk Rate Avg",
    "Bwd Bytes/Bulk Avg",
    "Bwd Packet/Bulk Avg",
    "Bwd Bulk Rate Avg",
    "Subflow Fwd Packets",
    "Subflow Fwd Bytes",
    "Subflow Bwd Packets",
    "Subflow Bwd Bytes",
    "FWD Init Win Bytes",
    "Bwd Init Win Bytes",
    "Fwd Act Data Pkts",
    "Fwd Seg Size Min",
    "Active Min",
    "Active Mean",
    "Active Max",
    "Active Std",
    "Idle Min",
    "Idle Mean",
    "Idle Max",
    "Idle Std",
];

const FORBIDDEN_FIELDS: [&str; 24] = [
    "Flow ID",
    "SrcIP",
    "DstIP",
    "SrcPort",
    "DstPort",
    "mTimestampStart",
    "mTimestampLast",
    "SigID revision",
    "Category",
    "Severity",
    "Anomaly_event",
    "L3/L4 Protocol",
    "Int/Ext Dst IP",
    "Service",
    "Label_src",
    "Label_dst",
    "Label",
    "External_src",
    "External_dst",
    "Segment_src",
    "Segment_dst",
    "Expoid_src",
    "Expoid_dst",
    "source_row_index",
];

/// 单角色的全部输出路径。
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RoleArtifacts {
    cache: PathBuf,
    labels: Option<PathBuf>,
}

/// 顶层输出路径。
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct OutputArtifacts {
    dataset_manifest: PathBuf,
    experiment_manifest: PathBuf,
    field_manifest: PathBuf,
    normalizer: PathBuf,
    sample_manifest: PathBuf,
    sequence_manifest: PathBuf,
    selection_receipt: PathBuf,
    final_isolation_receipt: PathBuf,
    run_receipt: PathBuf,
    roles: BTreeMap<String, RoleArtifacts>,
}

/// 固定资源上界与运行估算。
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResourceLimits {
    stable_hash_buckets: usize,
    max_batch_rows: usize,
    max_sequence_flows: usize,
    max_open_bucket_files: usize,
    max_active_seconds_per_year: usize,
    max_selection_candidates: usize,
    quantile_sample_per_field: usize,
    output_batch_rows: usize,
    temporary_directory_limit_gib: u64,
    disk_low_watermark_gib: u64,
    estimated_peak_memory_gib: f64,
    estimated_input_gib: f64,
    estimated_output_gib: f64,
    estimated_total_io_gib: f64,
    progress_interval_rows: u64,
}

/// 严格跨年度物化配置。
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CrossyearConfig {
    schema_version: String,
    contract_version: String,
    materialization_mode: String,
    budget_tier: String,
    project_root: PathBuf,
    lspr23_zip_path: PathBuf,
    lspr23_zip_member: String,
    lspr24_parquet_path: PathBuf,
    output_root: PathBuf,
    temporary_root: PathBuf,
    source_train_fraction: f64,
    target_prefix_fraction: f64,
    target_development_end_fraction: f64,
    normalization_epsilon: f64,
    normalization_clip: f64,
    fields: Vec<String>,
    variants: Vec<String>,
    role_row_limits: BTreeMap<String, u64>,
    pair_hash_keep_thresholds: BTreeMap<String, u16>,
    resources: ResourceLimits,
    outputs: OutputArtifacts,
}

impl CrossyearConfig {
    /// 从严格 JSON 解析并验证配置。
    ///
    /// # Errors
    ///
    /// JSON 非法、未知字段、冻结常量变化或路径越界时失败。
    pub fn from_json(bytes: &[u8]) -> Result<Self, CrossyearError> {
        let config: Self = serde_json::from_slice(bytes)
            .map_err(|error| CrossyearError::Config(error.to_string()))?;
        config.validate()?;
        Ok(config)
    }

    fn validate(&self) -> Result<(), CrossyearError> {
        ensure_config(
            self.schema_version == CROSSYEAR_CONFIG_VERSION,
            "schema_version",
        )?;
        ensure_config(
            self.contract_version == CONTRACT_VERSION,
            "contract_version",
        )?;
        ensure_config(
            self.materialization_mode == "bounded_quick_cache",
            "materialization_mode 必须为 bounded_quick_cache",
        )?;
        ensure_config(
            self.project_root.is_absolute(),
            "project_root 必须为绝对路径",
        )?;
        ensure_config(self.output_root.is_absolute(), "output_root 必须为绝对路径")?;
        ensure_config(
            self.temporary_root.is_absolute(),
            "temporary_root 必须为绝对路径",
        )?;
        ensure_config(
            self.lspr23_zip_path.is_absolute(),
            "LSPR23 路径必须为绝对路径",
        )?;
        ensure_config(
            self.lspr24_parquet_path.is_absolute(),
            "LSPR24 路径必须为绝对路径",
        )?;
        ensure_config(self.lspr23_zip_member == "ls23pr_v1.csv", "LSPR23 ZIP 成员")?;
        for path in [
            &self.lspr23_zip_path,
            &self.lspr24_parquet_path,
            &self.output_root,
            &self.temporary_root,
        ] {
            ensure_config(path.starts_with(&self.project_root), "路径必须位于项目根内")?;
        }
        ensure_config(
            (self.source_train_fraction - 0.80).abs() < f64::EPSILON,
            "source_train_fraction",
        )?;
        ensure_config(
            (self.target_prefix_fraction - 0.10).abs() < f64::EPSILON,
            "target_prefix_fraction",
        )?;
        ensure_config(
            (self.target_development_end_fraction - 0.80).abs() < f64::EPSILON,
            "target_development_end_fraction",
        )?;
        ensure_config(self.normalization_epsilon > 0.0, "normalization_epsilon")?;
        ensure_config(self.normalization_clip == 10.0, "normalization_clip")?;
        ensure_config(
            self.fields.iter().map(String::as_str).eq(COMMON_FIELDS),
            "77 字段顺序",
        )?;
        ensure_config(self.variants == ["B0", "M1", "M2", "M1M2"], "四变体")?;
        ensure_config(
            self.resources.stable_hash_buckets == BUCKET_COUNT,
            "哈希桶数",
        )?;
        ensure_config(self.resources.max_batch_rows == MAX_BATCH_SIZE, "批行数")?;
        ensure_config(
            self.resources.max_sequence_flows == MAX_SEQUENCE_LENGTH,
            "序列长度",
        )?;
        ensure_config(self.resources.max_open_bucket_files > 0, "打开桶文件上限")?;
        ensure_config(
            self.resources.output_batch_rows > 0
                && self.resources.output_batch_rows <= MAX_BATCH_SIZE,
            "输出批行数",
        )?;
        ensure_config(
            self.resources.quantile_sample_per_field > 0,
            "分位数保留样本上限",
        )?;
        ensure_config(
            self.resources.max_selection_candidates > 0,
            "序列候选状态上限",
        )?;
        ensure_config(
            matches!(self.resources.temporary_directory_limit_gib, 1..=24),
            "临时目录上限必须位于 1..=24 GiB",
        )?;
        ensure_config(self.resources.disk_low_watermark_gib >= 5, "磁盘低水位")?;
        ensure_config(self.resources.progress_interval_rows > 0, "进度行间隔")?;
        let expected_roles = BTreeSet::from([
            "source-train",
            "source-validation",
            "target-prefix",
            "target-development",
        ]);
        ensure_config(
            self.outputs
                .roles
                .keys()
                .map(String::as_str)
                .collect::<BTreeSet<_>>()
                == expected_roles,
            "角色制品",
        )?;
        ensure_config(
            self.role_row_limits
                .keys()
                .map(String::as_str)
                .collect::<BTreeSet<_>>()
                == expected_roles,
            "角色行预算",
        )?;
        ensure_config(
            self.pair_hash_keep_thresholds
                .keys()
                .map(String::as_str)
                .collect::<BTreeSet<_>>()
                == expected_roles,
            "角色 2-IP 哈希预筛阈值",
        )?;
        ensure_config(
            self.pair_hash_keep_thresholds
                .values()
                .all(|threshold| matches!(threshold, 1..=256)),
            "2-IP 哈希预筛阈值必须位于 1..=256",
        )?;
        let total_budget = self.role_row_limits.values().try_fold(0u64, |total, value| {
            total
                .checked_add(*value)
                .ok_or_else(|| CrossyearError::Config("角色总预算溢出".to_owned()))
        })?;
        let expected_total = match self.budget_tier.as_str() {
            "Q0" => {
                ensure_config(
                    self.role_row_limits.values().all(|limit| *limit == 262_144),
                    "Q0 四角色必须各为 262144",
                )?;
                1_048_576
            }
            "Q1" => {
                ensure_config(
                    self.role_row_limits[YearRole::SourceTrain.name()] == 1_048_576
                        && self.role_row_limits[YearRole::SourceValidation.name()] == 262_144
                        && self.role_row_limits[YearRole::TargetPrefix.name()] == 262_144
                        && self.role_row_limits[YearRole::TargetDevelopment.name()] == 1_048_576,
                    "Q1 角色预算",
                )?;
                2_621_440
            }
            _ => return Err(CrossyearError::Config("budget_tier 只允许 Q0 或 Q1".to_owned())),
        };
        ensure_config(total_budget == expected_total, "预算级别与角色总预算")?;
        let quantile_capacity = u64::try_from(self.resources.quantile_sample_per_field)
            .map_err(|_| CrossyearError::Config("精确分位数容量无法转换".to_owned()))?;
        ensure_config(
            quantile_capacity >= self.role_row_limits[YearRole::SourceTrain.name()],
            "精确分位数容量必须覆盖 source-train 行预算",
        )?;
        for path in self.all_output_paths() {
            ensure_config(path.is_absolute(), "输出制品路径必须为绝对路径")?;
            ensure_config(
                path.starts_with(&self.output_root),
                "输出制品必须位于 output_root",
            )?;
        }
        ensure_config(
            self.outputs.roles["target-prefix"].labels.is_none(),
            "目标前缀不得配置标签制品",
        )?;
        Ok(())
    }

    fn all_output_paths(&self) -> Vec<&Path> {
        let mut paths = vec![
            self.outputs.dataset_manifest.as_path(),
            self.outputs.experiment_manifest.as_path(),
            self.outputs.field_manifest.as_path(),
            self.outputs.normalizer.as_path(),
            self.outputs.sample_manifest.as_path(),
            self.outputs.sequence_manifest.as_path(),
            self.outputs.selection_receipt.as_path(),
            self.outputs.final_isolation_receipt.as_path(),
            self.outputs.run_receipt.as_path(),
        ];
        for role in self.outputs.roles.values() {
            paths.push(&role.cache);
            if let Some(path) = &role.labels {
                paths.push(path);
            }
        }
        paths
    }

    fn staged_path(&self, formal: &Path, staging_root: &Path) -> Result<PathBuf, CrossyearError> {
        let relative = formal
            .strip_prefix(&self.output_root)
            .map_err(|_| CrossyearError::Config("输出路径不在 output_root 内".to_owned()))?;
        Ok(staging_root.join(relative))
    }
}

fn ensure_config(condition: bool, field: &'static str) -> Result<(), CrossyearError> {
    if condition {
        Ok(())
    } else {
        Err(CrossyearError::Config(format!("冻结配置不匹配：{field}")))
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(rename_all = "kebab-case")]
enum YearRole {
    SourceTrain,
    SourceValidation,
    TargetPrefix,
    TargetDevelopment,
}

impl YearRole {
    const ALL: [Self; 4] = [
        Self::SourceTrain,
        Self::SourceValidation,
        Self::TargetPrefix,
        Self::TargetDevelopment,
    ];

    const fn name(self) -> &'static str {
        match self {
            Self::SourceTrain => "source-train",
            Self::SourceValidation => "source-validation",
            Self::TargetPrefix => "target-prefix",
            Self::TargetDevelopment => "target-development",
        }
    }

    const fn index(self) -> usize {
        match self {
            Self::SourceTrain => 0,
            Self::SourceValidation => 1,
            Self::TargetPrefix => 2,
            Self::TargetDevelopment => 3,
        }
    }
}

/// 完成收据。
#[derive(Debug, Clone, Serialize)]
pub struct CrossyearReceipt {
    pub schema_version: &'static str,
    pub output_root: PathBuf,
    pub dataset_manifest: PathBuf,
    pub experiment_manifest: PathBuf,
    pub role_rows: BTreeMap<&'static str, u64>,
    pub role_sequences: BTreeMap<&'static str, u64>,
    pub isolated_rows: BTreeMap<String, u64>,
    pub final_accessed: bool,
}

/// 跨年度物化失败。
#[derive(Debug)]
pub enum CrossyearError {
    Config(String),
    Io {
        operation: &'static str,
        path: PathBuf,
        source: io::Error,
    },
    Csv(String),
    Zip(String),
    Parquet(String),
    Schema(String),
    Data(String),
    Output(OutputError),
    Serialization(String),
    TemporaryLimit {
        actual: u64,
        limit: u64,
    },
}

impl Display for CrossyearError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Config(message) => write!(formatter, "跨年度配置错误：{message}"),
            Self::Io {
                operation,
                path,
                source,
            } => write!(formatter, "{operation} {} 失败：{source}", path.display()),
            Self::Csv(message) => write!(formatter, "LSPR23 CSV 错误：{message}"),
            Self::Zip(message) => write!(formatter, "LSPR23 ZIP 错误：{message}"),
            Self::Parquet(message) => write!(formatter, "LSPR24 Parquet 错误：{message}"),
            Self::Schema(message) => write!(formatter, "输入模式错误：{message}"),
            Self::Data(message) => write!(formatter, "数据合同错误：{message}"),
            Self::Output(error) => write!(formatter, "原子输出错误：{error}"),
            Self::Serialization(message) => write!(formatter, "制品序列化错误：{message}"),
            Self::TemporaryLimit { actual, limit } => {
                write!(formatter, "临时数据 {actual} 字节超过上限 {limit} 字节")
            }
        }
    }
}

impl Error for CrossyearError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Io { source, .. } => Some(source),
            Self::Output(source) => Some(source),
            _ => None,
        }
    }
}

impl From<OutputError> for CrossyearError {
    fn from(value: OutputError) -> Self {
        Self::Output(value)
    }
}

impl Write for PartialOutput {
    fn write(&mut self, buffer: &[u8]) -> io::Result<usize> {
        PartialOutput::write_all(self, buffer)
            .map(|()| buffer.len())
            .map_err(io::Error::other)
    }

    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

fn io_error(operation: &'static str, path: &Path, source: io::Error) -> CrossyearError {
    CrossyearError::Io {
        operation,
        path: path.to_path_buf(),
        source,
    }
}

struct StageProgress {
    name: &'static str,
    started: Instant,
    processed: u64,
    next_report: u64,
    interval: u64,
}

impl StageProgress {
    fn start(name: &'static str, interval: u64) -> Self {
        eprintln!("阶段开始：{name}");
        Self {
            name,
            started: Instant::now(),
            processed: 0,
            next_report: interval,
            interval,
        }
    }

    fn advance(&mut self) {
        self.processed = self.processed.saturating_add(1);
        if self.processed >= self.next_report {
            let elapsed = self.started.elapsed().as_secs_f64().max(0.001);
            eprintln!(
                "阶段进度：{}，已处理={}，吞吐={:.1}行/秒，累计={:.1}秒，预计剩余=未知",
                self.name,
                self.processed,
                self.processed as f64 / elapsed,
                elapsed
            );
            self.next_report = self.next_report.saturating_add(self.interval);
        }
    }

    fn finish(self) {
        eprintln!(
            "阶段结束：{}，处理量={}，累计={:.1}秒",
            self.name,
            self.processed,
            self.started.elapsed().as_secs_f64()
        );
    }
}

#[derive(Debug, Clone)]
struct FlowRow {
    role: YearRole,
    source_row_index: u64,
    available_ns: i64,
    start_ns: i64,
    pair_key: [u8; 32],
    sample_id: [u8; 32],
    label: Option<u8>,
    protocol: Option<u8>,
    numeric: Vec<Option<f64>>,
}

impl FlowRow {
    fn encode(&self) -> Result<Vec<u8>, CrossyearError> {
        let mut bytes = Vec::with_capacity(96 + self.numeric.len() * 8);
        bytes.push(
            u8::try_from(self.role.index())
                .map_err(|_| CrossyearError::Data("角色索引溢出".to_owned()))?,
        );
        bytes.extend_from_slice(&self.source_row_index.to_be_bytes());
        bytes.extend_from_slice(&self.available_ns.to_be_bytes());
        bytes.extend_from_slice(&self.start_ns.to_be_bytes());
        bytes.extend_from_slice(&self.pair_key);
        bytes.extend_from_slice(&self.sample_id);
        bytes.push(self.label.unwrap_or(u8::MAX));
        bytes.push(self.protocol.unwrap_or(u8::MAX));
        let count = u16::try_from(self.numeric.len())
            .map_err(|_| CrossyearError::Data("数值字段数超过 u16".to_owned()))?;
        bytes.extend_from_slice(&count.to_be_bytes());
        for value in &self.numeric {
            bytes.extend_from_slice(&value.unwrap_or(f64::NAN).to_bits().to_be_bytes());
        }
        Ok(bytes)
    }

    fn decode(bytes: &[u8]) -> Result<Self, CrossyearError> {
        let mut cursor = BinaryCursor::new(bytes);
        let role = match cursor.u8()? {
            0 => YearRole::SourceTrain,
            1 => YearRole::SourceValidation,
            2 => YearRole::TargetPrefix,
            3 => YearRole::TargetDevelopment,
            value => return Err(CrossyearError::Data(format!("桶记录角色非法：{value}"))),
        };
        let source_row_index = cursor.u64()?;
        let available_ns = cursor.i64()?;
        let start_ns = cursor.i64()?;
        let pair_key = cursor.array32()?;
        let sample_id = cursor.array32()?;
        let label = match cursor.u8()? {
            u8::MAX => None,
            value => Some(value),
        };
        let protocol = match cursor.u8()? {
            u8::MAX => None,
            value => Some(value),
        };
        let numeric_count = usize::from(cursor.u16()?);
        if numeric_count != NUMERIC_FIELD_COUNT {
            return Err(CrossyearError::Data(format!(
                "桶记录数值字段数为 {numeric_count}"
            )));
        }
        let mut numeric = Vec::with_capacity(numeric_count);
        for _ in 0..numeric_count {
            let value = f64::from_bits(cursor.u64()?);
            numeric.push(value.is_finite().then_some(value));
        }
        if !cursor.is_finished() {
            return Err(CrossyearError::Data("桶记录含尾随字节".to_owned()));
        }
        Ok(Self {
            role,
            source_row_index,
            available_ns,
            start_ns,
            pair_key,
            sample_id,
            label,
            protocol,
            numeric,
        })
    }
}

struct BinaryCursor<'a> {
    bytes: &'a [u8],
    offset: usize,
}

impl<'a> BinaryCursor<'a> {
    const fn new(bytes: &'a [u8]) -> Self {
        Self { bytes, offset: 0 }
    }

    fn bytes(&mut self, count: usize) -> Result<&'a [u8], CrossyearError> {
        let end = self
            .offset
            .checked_add(count)
            .ok_or_else(|| CrossyearError::Data("桶记录长度溢出".to_owned()))?;
        let value = self
            .bytes
            .get(self.offset..end)
            .ok_or_else(|| CrossyearError::Data("桶记录提前结束".to_owned()))?;
        self.offset = end;
        Ok(value)
    }

    fn u8(&mut self) -> Result<u8, CrossyearError> {
        Ok(self.bytes(1)?[0])
    }
    fn u16(&mut self) -> Result<u16, CrossyearError> {
        Ok(u16::from_be_bytes(self.bytes(2)?.try_into().map_err(
            |_| CrossyearError::Data("u16 解码失败".to_owned()),
        )?))
    }
    fn u64(&mut self) -> Result<u64, CrossyearError> {
        Ok(u64::from_be_bytes(self.bytes(8)?.try_into().map_err(
            |_| CrossyearError::Data("u64 解码失败".to_owned()),
        )?))
    }
    fn i64(&mut self) -> Result<i64, CrossyearError> {
        Ok(i64::from_be_bytes(self.bytes(8)?.try_into().map_err(
            |_| CrossyearError::Data("i64 解码失败".to_owned()),
        )?))
    }
    fn array32(&mut self) -> Result<[u8; 32], CrossyearError> {
        self.bytes(32)?
            .try_into()
            .map_err(|_| CrossyearError::Data("32 字节摘要解码失败".to_owned()))
    }
    const fn is_finished(&self) -> bool {
        self.offset == self.bytes.len()
    }
}

struct ZipCsvReader {
    child: Child,
    reader: BufReader<ChildStdout>,
    buffer: Vec<u8>,
}

impl ZipCsvReader {
    fn open(path: &Path, member: &str) -> Result<Self, CrossyearError> {
        let mut child = Command::new("unzip")
            .arg("-p")
            .arg("--")
            .arg(path)
            .arg(member)
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|source| io_error("启动 ZIP 流式解码", path, source))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| CrossyearError::Zip("无法取得 unzip 标准输出".to_owned()))?;
        Ok(Self {
            child,
            reader: BufReader::with_capacity(256 * 1024, stdout),
            buffer: Vec::with_capacity(4096),
        })
    }

    fn next_record(&mut self) -> Result<Option<Vec<String>>, CrossyearError> {
        self.buffer.clear();
        loop {
            let read = self
                .reader
                .read_until(b'\n', &mut self.buffer)
                .map_err(|source| CrossyearError::Csv(source.to_string()))?;
            if read == 0 {
                if self.buffer.is_empty() {
                    return Ok(None);
                }
                break;
            }
            if csv_record_complete(&self.buffer) {
                break;
            }
        }
        parse_csv_record(&self.buffer).map(Some)
    }

    fn finish(mut self) -> Result<(), CrossyearError> {
        drop(self.reader);
        let status = self
            .child
            .wait()
            .map_err(|source| CrossyearError::Zip(source.to_string()))?;
        if status.success() {
            Ok(())
        } else {
            Err(CrossyearError::Zip(format!("unzip 退出码={status}")))
        }
    }
}

fn csv_record_complete(bytes: &[u8]) -> bool {
    let mut quoted = false;
    let mut index = 0usize;
    while index < bytes.len() {
        if bytes[index] == b'"' {
            if quoted && bytes.get(index + 1) == Some(&b'"') {
                index = index.saturating_add(2);
                continue;
            }
            quoted = !quoted;
        }
        index = index.saturating_add(1);
    }
    !quoted
}

fn parse_csv_record(bytes: &[u8]) -> Result<Vec<String>, CrossyearError> {
    let mut fields = Vec::with_capacity(101);
    let mut field = Vec::new();
    let mut quoted = false;
    let mut index = 0usize;
    while index < bytes.len() {
        let byte = bytes[index];
        match byte {
            b'"' if quoted && bytes.get(index + 1) == Some(&b'"') => {
                field.push(b'"');
                index = index.saturating_add(2);
                continue;
            }
            b'"' => quoted = !quoted,
            b',' if !quoted => {
                fields.push(
                    String::from_utf8(std::mem::take(&mut field))
                        .map_err(|_| CrossyearError::Csv("字段不是 UTF-8".to_owned()))?,
                );
            }
            b'\n' | b'\r' if !quoted => {}
            _ => field.push(byte),
        }
        index = index.saturating_add(1);
    }
    if quoted {
        return Err(CrossyearError::Csv("引号未闭合".to_owned()));
    }
    fields.push(
        String::from_utf8(field).map_err(|_| CrossyearError::Csv("字段不是 UTF-8".to_owned()))?,
    );
    Ok(fields)
}

fn header_indices(
    header: &[String],
    required: &[&str],
) -> Result<BTreeMap<String, usize>, CrossyearError> {
    let mut indices = BTreeMap::new();
    for name in required {
        let index = header
            .iter()
            .position(|value| value == name)
            .ok_or_else(|| CrossyearError::Schema(format!("缺少列 {name}")))?;
        if indices.insert((*name).to_owned(), index).is_some() {
            return Err(CrossyearError::Schema(format!("重复列 {name}")));
        }
    }
    Ok(indices)
}

fn required_input_columns(include_label: bool) -> Vec<&'static str> {
    let mut columns = vec![
        "SrcIP",
        "DstIP",
        "mTimestampStart",
        "mTimestampLast",
    ];
    columns.extend(COMMON_FIELDS);
    if include_label {
        columns.push("Label");
    }
    columns
}

fn parse_micros(value: &str) -> Option<i64> {
    value.trim().parse::<i64>().ok()
}

fn micros_to_ns(value: i64) -> Option<i64> {
    value.checked_mul(1_000)
}

fn canonical_ip(value: &str) -> Option<[u8; 16]> {
    match value.parse::<IpAddr>().ok()? {
        IpAddr::V4(ip) => Some(ip.to_ipv6_mapped().octets()),
        IpAddr::V6(ip) => Some(ip.octets()),
    }
}

fn pair_key(src: &str, dst: &str) -> Result<Option<[u8; 32]>, CrossyearError> {
    let Some(src) = canonical_ip(src) else {
        return Ok(None);
    };
    let Some(dst) = canonical_ip(dst) else {
        return Ok(None);
    };
    let (low, high) = if src <= dst { (src, dst) } else { (dst, src) };
    let encoded = tuple_encode(&[
        CanonicalValue::Utf8(PAIR_KEY_DOMAIN),
        CanonicalValue::Ip16(&low),
        CanonicalValue::Ip16(&high),
    ])
    .map_err(|error| CrossyearError::Data(error.to_string()))?;
    Ok(Some(sha256(&encoded)))
}

fn sample_id(year: u16, source_row_index: u64) -> Result<[u8; 32], CrossyearError> {
    let encoded = tuple_encode(&[
        CanonicalValue::Utf8(SAMPLE_ID_DOMAIN),
        CanonicalValue::U16(year),
        CanonicalValue::U64(source_row_index),
    ])
    .map_err(|error| CrossyearError::Data(error.to_string()))?;
    Ok(sha256(&encoded))
}

fn sequence_id(
    role: YearRole,
    pair_key: &[u8; 32],
    block: u64,
) -> Result<[u8; 32], CrossyearError> {
    let encoded = tuple_encode(&[
        CanonicalValue::Utf8(SEQUENCE_ID_DOMAIN),
        CanonicalValue::Utf8(role.name()),
        CanonicalValue::Sha256(pair_key),
        CanonicalValue::U64(block),
    ])
    .map_err(|error| CrossyearError::Data(error.to_string()))?;
    Ok(sha256(&encoded))
}

fn role_for_2023(available_ns: i64, cut_ns: i64) -> YearRole {
    if available_ns < cut_ns {
        YearRole::SourceTrain
    } else {
        YearRole::SourceValidation
    }
}

fn role_for_2024(available_ns: i64, prefix_ns: i64, final_ns: i64) -> Option<YearRole> {
    if available_ns >= final_ns {
        None
    } else if available_ns < prefix_ns {
        Some(YearRole::TargetPrefix)
    } else {
        Some(YearRole::TargetDevelopment)
    }
}

fn active_cut(active_seconds: &BTreeSet<i64>, fraction: f64) -> Result<i64, CrossyearError> {
    if active_seconds.len() < 2 {
        return Err(CrossyearError::Data("活动秒不足以形成时间切分".to_owned()));
    }
    let index = active_rank_index(active_seconds.len(), fraction)?;
    let second = active_seconds
        .iter()
        .nth(index)
        .ok_or_else(|| CrossyearError::Data("活动秒切点越界".to_owned()))?;
    second
        .checked_mul(1_000_000_000)
        .ok_or_else(|| CrossyearError::Data("活动秒转纳秒溢出".to_owned()))
}

fn active_rank_index(length: usize, fraction: f64) -> Result<usize, CrossyearError> {
    if length < 2 || !(0.0..1.0).contains(&fraction) {
        return Err(CrossyearError::Data(
            "活动秒秩切分前置条件不成立".to_owned(),
        ));
    }
    let index = (fraction * length as f64).ceil() as usize;
    if index >= length {
        return Err(CrossyearError::Data("活动秒秩切点越界".to_owned()));
    }
    Ok(index)
}

fn scan_lspr23_activity(config: &CrossyearConfig) -> Result<BTreeSet<i64>, CrossyearError> {
    let mut progress = StageProgress::start(
        "扫描 LSPR23 活动秒",
        config.resources.progress_interval_rows,
    );
    let mut csv = ZipCsvReader::open(&config.lspr23_zip_path, &config.lspr23_zip_member)?;
    let header = csv
        .next_record()?
        .ok_or_else(|| CrossyearError::Csv("缺少表头".to_owned()))?;
    let indices = header_indices(&header, &["mTimestampStart", "mTimestampLast"])?;
    let mut active = BTreeSet::new();
    while let Some(record) = csv.next_record()? {
        let start = record
            .get(indices["mTimestampStart"])
            .and_then(|value| parse_micros(value));
        let last = record
            .get(indices["mTimestampLast"])
            .and_then(|value| parse_micros(value));
        if let (Some(start), Some(last)) = (start, last) {
            if start <= last {
                active.insert(last.div_euclid(1_000_000));
                if active.len() > config.resources.max_active_seconds_per_year {
                    return Err(CrossyearError::Data(
                        "LSPR23 活动秒状态超过配置上限".to_owned(),
                    ));
                }
            }
        }
        progress.advance();
    }
    csv.finish()?;
    progress.finish();
    Ok(active)
}

fn scan_lspr24_activity(config: &CrossyearConfig) -> Result<BTreeSet<i64>, CrossyearError> {
    let mut progress = StageProgress::start(
        "扫描 LSPR24 活动秒",
        config.resources.progress_interval_rows,
    );
    let file = File::open(&config.lspr24_parquet_path)
        .map_err(|source| io_error("打开 LSPR24 Parquet", &config.lspr24_parquet_path, source))?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)
        .map_err(|error| CrossyearError::Parquet(error.to_string()))?;
    let indices = parquet_indices(builder.schema(), &["mTimestampStart", "mTimestampLast"])?;
    let projection = ProjectionMask::roots(builder.parquet_schema(), indices);
    let reader = builder
        .with_projection(projection)
        .with_batch_size(MAX_BATCH_SIZE)
        .build()
        .map_err(|error| CrossyearError::Parquet(error.to_string()))?;
    let mut active = BTreeSet::new();
    for batch in reader {
        let batch = batch.map_err(|error| CrossyearError::Parquet(error.to_string()))?;
        let start = int64_column(&batch, "mTimestampStart")?;
        let last = int64_column(&batch, "mTimestampLast")?;
        for row in 0..batch.num_rows() {
            if !start.is_null(row) && !last.is_null(row) && start.value(row) <= last.value(row) {
                active.insert(last.value(row).div_euclid(1_000_000));
                if active.len() > config.resources.max_active_seconds_per_year {
                    return Err(CrossyearError::Data(
                        "LSPR24 活动秒状态超过配置上限".to_owned(),
                    ));
                }
            }
            progress.advance();
        }
    }
    progress.finish();
    Ok(active)
}

fn parquet_indices(schema: &Schema, names: &[&str]) -> Result<Vec<usize>, CrossyearError> {
    names
        .iter()
        .map(|name| {
            schema
                .fields()
                .iter()
                .position(|field| field.name() == *name)
                .ok_or_else(|| CrossyearError::Schema(format!("缺少列 {name}")))
        })
        .collect()
}

fn typed_column<'a, T: Array + 'static>(
    batch: &'a RecordBatch,
    name: &str,
    expected: &str,
) -> Result<&'a T, CrossyearError> {
    let index = batch
        .schema()
        .fields()
        .iter()
        .position(|field| field.name() == name)
        .ok_or_else(|| CrossyearError::Schema(format!("缺少投影列 {name}")))?;
    batch
        .column(index)
        .as_any()
        .downcast_ref::<T>()
        .ok_or_else(|| CrossyearError::Schema(format!("列 {name} 必须为 {expected}")))
}

fn int64_column<'a>(batch: &'a RecordBatch, name: &str) -> Result<&'a Int64Array, CrossyearError> {
    typed_column(batch, name, "Int64")
}

fn int32_column<'a>(batch: &'a RecordBatch, name: &str) -> Result<&'a Int32Array, CrossyearError> {
    typed_column(batch, name, "Int32")
}

fn string_column<'a>(
    batch: &'a RecordBatch,
    name: &str,
) -> Result<&'a StringArray, CrossyearError> {
    typed_column(batch, name, "Utf8")
}

fn numeric_column<'a>(
    batch: &'a RecordBatch,
    name: &str,
) -> Result<NumericColumn<'a>, CrossyearError> {
    let index = batch
        .schema()
        .fields()
        .iter()
        .position(|field| field.name() == name)
        .ok_or_else(|| CrossyearError::Schema(format!("缺少投影列 {name}")))?;
    NumericColumn::try_new(name, batch.column(index).as_ref())
        .map_err(|error| CrossyearError::Schema(error.to_string()))
}

struct WriterSlot {
    writer: BufWriter<File>,
    last_used: u64,
}

struct BucketWriters {
    root: PathBuf,
    slots: Vec<Option<WriterSlot>>,
    order: BTreeSet<(u64, usize)>,
    clock: u64,
    open_limit: usize,
    bytes_written: u64,
    byte_limit: u64,
    disk_low_watermark: u64,
    next_space_check: u64,
}

impl BucketWriters {
    fn new(
        root: PathBuf,
        open_limit: usize,
        byte_limit: u64,
        disk_low_watermark: u64,
    ) -> Result<Self, CrossyearError> {
        fs::create_dir(&root).map_err(|source| io_error("创建桶目录", &root, source))?;
        Ok(Self {
            root,
            slots: (0..YearRole::ALL.len() * BUCKET_COUNT)
                .map(|_| None)
                .collect(),
            order: BTreeSet::new(),
            clock: 0,
            open_limit,
            bytes_written: 0,
            byte_limit,
            disk_low_watermark,
            next_space_check: 512 * 1024 * 1024,
        })
    }

    fn path(&self, role: YearRole, bucket: usize) -> PathBuf {
        self.root
            .join(format!("{}-bucket-{bucket:03}.bin", role.name()))
    }

    fn write(&mut self, row: &FlowRow) -> Result<(), CrossyearError> {
        let bucket = usize::from(row.pair_key[0]);
        let index = row.role.index() * BUCKET_COUNT + bucket;
        self.clock = self
            .clock
            .checked_add(1)
            .ok_or_else(|| CrossyearError::Data("桶写入时钟溢出".to_owned()))?;
        if let Some(slot) = self.slots[index].as_mut() {
            self.order.remove(&(slot.last_used, index));
            slot.last_used = self.clock;
            self.order.insert((slot.last_used, index));
        } else {
            if self.order.len() == self.open_limit {
                let (old_clock, old_index) = *self
                    .order
                    .iter()
                    .next()
                    .ok_or_else(|| CrossyearError::Data("桶文件 LRU 状态为空".to_owned()))?;
                self.order.remove(&(old_clock, old_index));
                if let Some(mut old) = self.slots[old_index].take() {
                    old.writer
                        .flush()
                        .map_err(|source| io_error("刷新桶文件", &self.root, source))?;
                }
            }
            let path = self.path(row.role, bucket);
            let file = OpenOptions::new()
                .create(true)
                .append(true)
                .open(&path)
                .map_err(|source| io_error("打开桶文件", &path, source))?;
            self.slots[index] = Some(WriterSlot {
                writer: BufWriter::with_capacity(256 * 1024, file),
                last_used: self.clock,
            });
            self.order.insert((self.clock, index));
        }
        let payload = row.encode()?;
        let length = u32::try_from(payload.len())
            .map_err(|_| CrossyearError::Data("桶记录长度超过 u32".to_owned()))?;
        let increment = u64::try_from(payload.len())
            .ok()
            .and_then(|value| value.checked_add(4))
            .ok_or_else(|| CrossyearError::Data("临时字节计数溢出".to_owned()))?;
        self.bytes_written = self
            .bytes_written
            .checked_add(increment)
            .ok_or_else(|| CrossyearError::Data("临时字节计数溢出".to_owned()))?;
        if self.bytes_written > self.byte_limit {
            return Err(CrossyearError::TemporaryLimit {
                actual: self.bytes_written,
                limit: self.byte_limit,
            });
        }
        if self.bytes_written >= self.next_space_check {
            let available = available_bytes(&self.root)?;
            if available < self.disk_low_watermark {
                return Err(CrossyearError::Data(format!(
                    "桶写入期间可用磁盘 {available} 字节低于低水位 {}",
                    self.disk_low_watermark
                )));
            }
            self.next_space_check = self
                .next_space_check
                .checked_add(512 * 1024 * 1024)
                .ok_or_else(|| CrossyearError::Data("桶空间检查阈值溢出".to_owned()))?;
        }
        let slot = self.slots[index]
            .as_mut()
            .ok_or_else(|| CrossyearError::Data("桶文件未打开".to_owned()))?;
        slot.writer
            .write_all(&length.to_be_bytes())
            .and_then(|()| slot.writer.write_all(&payload))
            .map_err(|source| io_error("写入桶记录", &self.root, source))
    }

    fn finish(mut self) -> Result<u64, CrossyearError> {
        for slot in &mut self.slots {
            if let Some(mut slot) = slot.take() {
                slot.writer
                    .flush()
                    .map_err(|source| io_error("刷新桶文件", &self.root, source))?;
            }
        }
        Ok(self.bytes_written)
    }
}

struct NormalizerSampler {
    fields: Vec<Vec<f64>>,
    capacity: usize,
    observed_rows: usize,
    protocol_vocabulary: BTreeSet<u8>,
}

impl NormalizerSampler {
    fn new(capacity: usize) -> Self {
        Self {
            fields: (0..NUMERIC_FIELD_COUNT)
                .map(|_| Vec::with_capacity(capacity))
                .collect(),
            capacity,
            observed_rows: 0,
            protocol_vocabulary: BTreeSet::new(),
        }
    }

    fn observe(&mut self, row: &FlowRow) -> Result<(), CrossyearError> {
        if self.observed_rows >= self.capacity {
            return Err(CrossyearError::Data(
                "入选 source-train 行数超过精确分位数容量".to_owned(),
            ));
        }
        self.observed_rows += 1;
        if let Some(protocol) = row.protocol {
            self.protocol_vocabulary.insert(protocol);
        }
        for (index, value) in row.numeric.iter().copied().enumerate() {
            let Some(value) = value else { continue };
            self.fields[index].push(value);
        }
        Ok(())
    }

    fn finish(self, epsilon: f64, clip: f64) -> Result<Normalizer, CrossyearError> {
        let fitted_row_count = u64::try_from(self.observed_rows)
            .map_err(|_| CrossyearError::Data("归一化拟合行数无法转换".to_owned()))?;
        let mut statistics = Vec::with_capacity(NUMERIC_FIELD_COUNT);
        for (index, mut values) in self.fields.into_iter().enumerate() {
            if values.is_empty() {
                return Err(CrossyearError::Data(format!(
                    "源训练字段 {} 全缺失",
                    COMMON_FIELDS[index + 1]
                )));
            }
            values.sort_unstable_by(f64::total_cmp);
            let q1 = quantile(&values, 0.25);
            let median = quantile(&values, 0.50);
            let q3 = quantile(&values, 0.75);
            statistics.push(FieldStatistic {
                field: COMMON_FIELDS[index + 1].to_owned(),
                median,
                iqr: (q3 - q1).max(epsilon),
                retained_count: u64::try_from(values.len()).unwrap_or(u64::MAX),
            });
        }
        Ok(Normalizer {
            schema_version: "lspr-crossyear-normalizer-v1",
            fitted_role: YearRole::SourceTrain.name(),
            quantile_algorithm: "full-selected-source-train-nearest-index-v1",
            quantile_rank_error_bound: 0,
            fitted_row_count,
            epsilon,
            clip,
            protocol_missing_index: 0,
            protocol_unknown_index: 1,
            protocol_vocabulary_start_index: 2,
            protocol_vocabulary: self.protocol_vocabulary.into_iter().collect(),
            statistics,
        })
    }
}

fn quantile(values: &[f64], probability: f64) -> f64 {
    let index = ((values.len().saturating_sub(1)) as f64 * probability).round() as usize;
    values[index.min(values.len().saturating_sub(1))]
}

#[derive(Debug, Clone, Serialize)]
struct FieldStatistic {
    field: String,
    median: f64,
    iqr: f64,
    retained_count: u64,
}

#[derive(Debug, Clone, Serialize)]
struct Normalizer {
    schema_version: &'static str,
    fitted_role: &'static str,
    quantile_algorithm: &'static str,
    quantile_rank_error_bound: u64,
    fitted_row_count: u64,
    epsilon: f64,
    clip: f64,
    protocol_missing_index: u8,
    protocol_unknown_index: u8,
    protocol_vocabulary_start_index: u8,
    protocol_vocabulary: Vec<u8>,
    statistics: Vec<FieldStatistic>,
}

impl Normalizer {
    fn transform(&self, row: &FlowRow, clip: f64) -> (Vec<f32>, Vec<u8>) {
        let mut values = Vec::with_capacity(COMMON_FIELD_COUNT);
        let mut missing = Vec::with_capacity(COMMON_FIELD_COUNT);
        match row.protocol {
            Some(protocol) => {
                let encoded = self
                    .protocol_vocabulary
                    .binary_search(&protocol)
                    .map(|index| index.saturating_add(2))
                    .unwrap_or(1);
                values.push(encoded as f32);
                missing.push(0);
            }
            None => {
                values.push(0.0);
                missing.push(1);
            }
        }
        for (value, statistic) in row.numeric.iter().zip(&self.statistics) {
            let raw = value.unwrap_or(statistic.median);
            values.push(((raw - statistic.median) / statistic.iqr).clamp(-clip, clip) as f32);
            missing.push(u8::from(value.is_none()));
        }
        (values, missing)
    }
}

#[derive(Default)]
struct IsolationCounts {
    counts: BTreeMap<String, u64>,
}

impl IsolationCounts {
    fn add(&mut self, reason: impl Into<String>) {
        let count = self.counts.entry(reason.into()).or_default();
        *count = count.saturating_add(1);
    }
}

fn pair_hash_prescreened(config: &CrossyearConfig, role: YearRole, pair_key: &[u8; 32]) -> bool {
    u16::from(pair_key[0]) < config.pair_hash_keep_thresholds[role.name()]
}

fn parse_numeric_text(value: Option<&String>) -> Option<f64> {
    let value = value?.trim();
    if value.is_empty() {
        return None;
    }
    value
        .parse::<f64>()
        .ok()
        .filter(|number| number.is_finite() && *number >= 0.0)
}

fn parse_protocol_text(value: Option<&String>) -> Option<u8> {
    value?.trim().parse::<u8>().ok()
}

fn parse_label_text(value: Option<&String>) -> Option<u8> {
    match value?.trim() {
        "0" => Some(0),
        "1" => Some(1),
        _ => None,
    }
}

fn process_lspr23(
    config: &CrossyearConfig,
    cut_ns: i64,
    buckets: &mut BucketWriters,
    isolation: &mut IsolationCounts,
) -> Result<(), CrossyearError> {
    let mut progress = StageProgress::start(
        "路由 LSPR23 开发流",
        config.resources.progress_interval_rows,
    );
    let mut csv = ZipCsvReader::open(&config.lspr23_zip_path, &config.lspr23_zip_member)?;
    let header = csv
        .next_record()?
        .ok_or_else(|| CrossyearError::Csv("缺少表头".to_owned()))?;
    if header.len() != 101 || header.iter().collect::<BTreeSet<_>>().len() != 101 {
        return Err(CrossyearError::Schema(
            "LSPR23 必须恰有 101 个唯一列名".to_owned(),
        ));
    }
    let required = required_input_columns(true);
    let indices = header_indices(&header, &required)?;
    let mut source_row_index = 0u64;
    while let Some(record) = csv.next_record()? {
        if record.len() != header.len() {
            isolation.add("lspr23-column-count");
            source_row_index = source_row_index
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("LSPR23 行号溢出".to_owned()))?;
            progress.advance();
            continue;
        }
        let start_us = record
            .get(indices["mTimestampStart"])
            .and_then(|value| parse_micros(value));
        let last_us = record
            .get(indices["mTimestampLast"])
            .and_then(|value| parse_micros(value));
        let Some((start_ns, available_ns)) = start_us.zip(last_us).and_then(|(start, last)| {
            (start <= last)
                .then(|| micros_to_ns(start).zip(micros_to_ns(last)))
                .flatten()
        }) else {
            isolation.add("lspr23-invalid-time");
            source_row_index = source_row_index
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("LSPR23 行号溢出".to_owned()))?;
            progress.advance();
            continue;
        };
        let role = role_for_2023(available_ns, cut_ns);
        let Some(pair_key) = pair_key(&record[indices["SrcIP"]], &record[indices["DstIP"]])? else {
            isolation.add("lspr23-invalid-ip");
            source_row_index = source_row_index
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("LSPR23 行号溢出".to_owned()))?;
            progress.advance();
            continue;
        };
        if !pair_hash_prescreened(config, role, &pair_key) {
            isolation.add(format!("{}-pair-hash-prescreen-excluded", role.name()));
            source_row_index = source_row_index
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("LSPR23 行号溢出".to_owned()))?;
            progress.advance();
            continue;
        }
        let Some(label) = parse_label_text(record.get(indices["Label"])) else {
            isolation.add("lspr23-invalid-label");
            source_row_index = source_row_index
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("LSPR23 行号溢出".to_owned()))?;
            progress.advance();
            continue;
        };
        let protocol = parse_protocol_text(record.get(indices["Protocol"]));
        let numeric = COMMON_FIELDS[1..]
            .iter()
            .map(|name| parse_numeric_text(record.get(indices[*name])))
            .collect::<Vec<_>>();
        let row = FlowRow {
            role,
            source_row_index,
            available_ns,
            start_ns,
            pair_key,
            sample_id: sample_id(2023, source_row_index)?,
            label: Some(label),
            protocol,
            numeric,
        };
        buckets.write(&row)?;
        source_row_index = source_row_index
            .checked_add(1)
            .ok_or_else(|| CrossyearError::Data("LSPR23 行号溢出".to_owned()))?;
        progress.advance();
    }
    csv.finish()?;
    progress.finish();
    Ok(())
}

fn process_lspr24(
    config: &CrossyearConfig,
    prefix_ns: i64,
    final_ns: i64,
    buckets: &mut BucketWriters,
    isolation: &mut IsolationCounts,
) -> Result<(), CrossyearError> {
    let mut progress = StageProgress::start(
        "路由 LSPR24 开发流",
        config.resources.progress_interval_rows,
    );
    let file = File::open(&config.lspr24_parquet_path)
        .map_err(|source| io_error("打开 LSPR24 Parquet", &config.lspr24_parquet_path, source))?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)
        .map_err(|error| CrossyearError::Parquet(error.to_string()))?;
    if builder.schema().fields().len() != 101 {
        return Err(CrossyearError::Schema("LSPR24 必须恰有 101 列".to_owned()));
    }
    let required = required_input_columns(true);
    let indices = parquet_indices(builder.schema(), &required)?;
    let projection = ProjectionMask::roots(builder.parquet_schema(), indices);
    let reader = builder
        .with_projection(projection)
        .with_batch_size(MAX_BATCH_SIZE)
        .build()
        .map_err(|error| CrossyearError::Parquet(error.to_string()))?;
    let mut source_row_index = 0u64;
    for batch in reader {
        let batch = batch.map_err(|error| CrossyearError::Parquet(error.to_string()))?;
        let start = int64_column(&batch, "mTimestampStart")?;
        let last = int64_column(&batch, "mTimestampLast")?;
        let src_ip = string_column(&batch, "SrcIP")?;
        let dst_ip = string_column(&batch, "DstIP")?;
        let protocol = int32_column(&batch, "Protocol")?;
        let label = int32_column(&batch, "Label")?;
        let numeric = COMMON_FIELDS[1..]
            .iter()
            .map(|name| numeric_column(&batch, name))
            .collect::<Result<Vec<_>, _>>()?;
        for row_index in 0..batch.num_rows() {
            let current_source_row = source_row_index;
            source_row_index = source_row_index
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("LSPR24 行号溢出".to_owned()))?;
            progress.advance();
            if start.is_null(row_index) || last.is_null(row_index) {
                isolation.add("lspr24-invalid-time");
                continue;
            }
            let Some(start_ns) = micros_to_ns(start.value(row_index)) else {
                isolation.add("lspr24-invalid-time");
                continue;
            };
            let Some(available_ns) = micros_to_ns(last.value(row_index)) else {
                isolation.add("lspr24-invalid-time");
                continue;
            };
            if start_ns > available_ns {
                isolation.add("lspr24-invalid-time");
                continue;
            }
            let Some(role) = role_for_2024(available_ns, prefix_ns, final_ns) else {
                continue;
            };
            if src_ip.is_null(row_index) || dst_ip.is_null(row_index) {
                isolation.add("lspr24-invalid-ip");
                continue;
            }
            let Some(pair_key) = pair_key(src_ip.value(row_index), dst_ip.value(row_index))? else {
                isolation.add("lspr24-invalid-ip");
                continue;
            };
            if !pair_hash_prescreened(config, role, &pair_key) {
                isolation.add(format!("{}-pair-hash-prescreen-excluded", role.name()));
                continue;
            }
            let label_value = if role == YearRole::TargetPrefix {
                None
            } else if label.is_null(row_index) || !matches!(label.value(row_index), 0 | 1) {
                isolation.add("lspr24-invalid-label");
                continue;
            } else {
                u8::try_from(label.value(row_index)).ok()
            };
            let protocol_value = if protocol.is_null(row_index) {
                None
            } else {
                u8::try_from(protocol.value(row_index)).ok()
            };
            let numeric_values = numeric
                .iter()
                .map(|column| column.value_as_f64(row_index).filter(|value| *value >= 0.0))
                .collect::<Vec<_>>();
            let row = FlowRow {
                role,
                source_row_index: current_source_row,
                available_ns,
                start_ns,
                pair_key,
                sample_id: sample_id(2024, current_source_row)?,
                label: label_value,
                protocol: protocol_value,
                numeric: numeric_values,
            };
            buckets.write(&row)?;
        }
    }
    progress.finish();
    Ok(())
}

struct AtomicParquetWriter {
    schema: Arc<Schema>,
    writer: ArrowWriter<PartialOutput>,
}

impl AtomicParquetWriter {
    fn create(path: &Path, schema: Arc<Schema>) -> Result<Self, CrossyearError> {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .map_err(|source| io_error("创建输出父目录", parent, source))?;
        }
        let output = PartialOutput::create(path)?;
        let writer = ArrowWriter::try_new(output, schema.clone(), None)
            .map_err(|error| CrossyearError::Parquet(error.to_string()))?;
        Ok(Self { schema, writer })
    }

    fn write(&mut self, columns: Vec<ArrayRef>) -> Result<(), CrossyearError> {
        let batch = RecordBatch::try_new(self.schema.clone(), columns)
            .map_err(|error| CrossyearError::Parquet(error.to_string()))?;
        self.writer
            .write(&batch)
            .map_err(|error| CrossyearError::Parquet(error.to_string()))
    }

    fn finish(self) -> Result<(), CrossyearError> {
        let output = self
            .writer
            .into_inner()
            .map_err(|error| CrossyearError::Parquet(error.to_string()))?;
        output.commit()?;
        Ok(())
    }
}

fn fixed_binary(
    values: impl Iterator<Item = [u8; 32]>,
    capacity: usize,
) -> Result<ArrayRef, CrossyearError> {
    let mut builder = FixedSizeBinaryBuilder::with_capacity(capacity, 32);
    for value in values {
        builder
            .append_value(value)
            .map_err(|error| CrossyearError::Parquet(error.to_string()))?;
    }
    Ok(Arc::new(builder.finish()))
}

fn fixed_list_f32(values: Vec<f32>) -> Result<ArrayRef, CrossyearError> {
    let values: ArrayRef = Arc::new(Float32Array::from(values));
    let field = Arc::new(Field::new("item", DataType::Float32, false));
    Ok(Arc::new(
        FixedSizeListArray::try_new(field, COMMON_FIELD_COUNT as i32, values, None)
            .map_err(|error| CrossyearError::Parquet(error.to_string()))?,
    ))
}

fn fixed_list_u8(values: Vec<u8>) -> Result<ArrayRef, CrossyearError> {
    let values: ArrayRef = Arc::new(UInt8Array::from(values));
    let field = Arc::new(Field::new("item", DataType::UInt8, false));
    Ok(Arc::new(
        FixedSizeListArray::try_new(field, COMMON_FIELD_COUNT as i32, values, None)
            .map_err(|error| CrossyearError::Parquet(error.to_string()))?,
    ))
}

#[derive(Debug)]
struct MaterializedRow {
    row: FlowRow,
    sequence_id: [u8; 32],
    position: u16,
    valid_length: u16,
    delta_t_us: i64,
    x_value: Vec<f32>,
    x_missing: Vec<u8>,
    cache_selected: bool,
}

#[derive(Debug, Clone)]
struct SequenceRow {
    sequence_id: [u8; 32],
    role: YearRole,
    group_key: [u8; 32],
    valid_length: u16,
    first_available_ns: i64,
    last_available_ns: i64,
    cache_selected: bool,
}

struct RoleWriters {
    role: YearRole,
    cache: AtomicParquetWriter,
    labels: Option<AtomicParquetWriter>,
    rows: Vec<MaterializedRow>,
    batch_size: usize,
    selected_sequences: Arc<BTreeSet<[u8; 32]>>,
    cache_rows: u64,
    total_rows: u64,
    sequence_count: u64,
}

impl RoleWriters {
    fn create(
        role: YearRole,
        paths: &RoleArtifacts,
        config: &CrossyearConfig,
        staging: &Path,
        selected_sequences: Arc<BTreeSet<[u8; 32]>>,
    ) -> Result<Self, CrossyearError> {
        let cache = AtomicParquetWriter::create(
            &config.staged_path(&paths.cache, staging)?,
            cache_schema(),
        )?;
        let labels = paths
            .labels
            .as_ref()
            .map(|path| {
                AtomicParquetWriter::create(&config.staged_path(path, staging)?, label_schema())
            })
            .transpose()?;
        Ok(Self {
            role,
            cache,
            labels,
            rows: Vec::with_capacity(config.resources.output_batch_rows),
            batch_size: config.resources.output_batch_rows,
            selected_sequences,
            cache_rows: 0,
            total_rows: 0,
            sequence_count: 0,
        })
    }

    fn push_sequence(
        &mut self,
        rows: Vec<FlowRow>,
        block: u64,
        normalizer: &Normalizer,
        clip: f64,
        manifests: &mut ManifestWriters,
    ) -> Result<(), CrossyearError> {
        let first = rows
            .first()
            .ok_or_else(|| CrossyearError::Data("空序列".to_owned()))?;
        let sequence_id = sequence_id(self.role, &first.pair_key, block)?;
        let valid_length = u16::try_from(rows.len())
            .map_err(|_| CrossyearError::Data("序列长度超过 u16".to_owned()))?;
        let cache_selected = self.selected_sequences.contains(&sequence_id);
        if !cache_selected {
            return Ok(());
        }
        self.cache_rows = self
            .cache_rows
            .checked_add(u64::from(valid_length))
            .ok_or_else(|| CrossyearError::Data("缓存行数溢出".to_owned()))?;
        let mut previous_available = None;
        let first_available_ns = first.available_ns;
        let last_available_ns = rows
            .last()
            .map(|row| row.available_ns)
            .unwrap_or(first_available_ns);
        let group_key = first.pair_key;
        let sequence = SequenceRow {
            sequence_id,
            role: self.role,
            group_key,
            valid_length,
            first_available_ns,
            last_available_ns,
            cache_selected,
        };
        manifests.push_sequence(&sequence, &rows)?;
        for (position, row) in rows.into_iter().enumerate() {
            let delta_t_us = previous_available
                .map(|previous: i64| row.available_ns.saturating_sub(previous).div_euclid(1_000))
                .unwrap_or(0);
            previous_available = Some(row.available_ns);
            let (x_value, x_missing) = normalizer.transform(&row, clip);
            self.rows.push(MaterializedRow {
                row,
                sequence_id,
                position: u16::try_from(position)
                    .map_err(|_| CrossyearError::Data("序列位置溢出".to_owned()))?,
                valid_length,
                delta_t_us,
                x_value,
                x_missing,
                cache_selected,
            });
            self.total_rows = self
                .total_rows
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("角色行数溢出".to_owned()))?;
            if self.rows.len() >= self.batch_size {
                self.flush()?;
            }
        }
        self.sequence_count = self
            .sequence_count
            .checked_add(1)
            .ok_or_else(|| CrossyearError::Data("序列计数溢出".to_owned()))?;
        Ok(())
    }

    fn flush(&mut self) -> Result<(), CrossyearError> {
        if self.rows.is_empty() {
            return Ok(());
        }
        self.write_labels()?;
        self.write_cache()?;
        self.rows.clear();
        Ok(())
    }

    fn write_labels(&mut self) -> Result<(), CrossyearError> {
        let Some(writer) = self.labels.as_mut() else {
            return Ok(());
        };
        if self.rows.iter().any(|item| item.row.label.is_none()) {
            return Err(CrossyearError::Data(format!(
                "角色 {} 标签缺失",
                self.role.name()
            )));
        }
        let count = self.rows.len();
        writer.write(vec![
            fixed_binary(self.rows.iter().map(|item| item.row.sample_id), count)?,
            Arc::new(UInt8Array::from_iter_values(
                self.rows.iter().map(|item| item.row.label.unwrap_or(0)),
            )) as ArrayRef,
        ])
    }

    fn write_cache(&mut self) -> Result<(), CrossyearError> {
        let selected = self
            .rows
            .iter()
            .filter(|item| item.cache_selected)
            .collect::<Vec<_>>();
        if selected.is_empty() {
            return Ok(());
        }
        let count = selected.len();
        let x_value = selected
            .iter()
            .flat_map(|item| item.x_value.iter().copied())
            .collect::<Vec<_>>();
        let x_missing = selected
            .iter()
            .flat_map(|item| item.x_missing.iter().copied())
            .collect::<Vec<_>>();
        self.cache.write(vec![
            fixed_binary(selected.iter().map(|item| item.row.sample_id), count)?,
            Arc::new(StringArray::from_iter_values(
                selected.iter().map(|_| self.role.name()),
            )) as ArrayRef,
            fixed_binary(selected.iter().map(|item| item.sequence_id), count)?,
            Arc::new(UInt16Array::from_iter_values(
                selected.iter().map(|item| item.position),
            )) as ArrayRef,
            Arc::new(UInt16Array::from_iter_values(
                selected.iter().map(|item| item.valid_length),
            )) as ArrayRef,
            Arc::new(Int64Array::from_iter_values(
                selected.iter().map(|item| item.row.available_ns),
            )) as ArrayRef,
            Arc::new(Int64Array::from_iter_values(
                selected.iter().map(|item| item.delta_t_us),
            )) as ArrayRef,
            fixed_list_f32(x_value)?,
            fixed_list_u8(x_missing)?,
            Arc::new(UInt8Array::from_iter_values((0..count).map(|_| 1))) as ArrayRef,
            fixed_binary(selected.iter().map(|item| item.row.pair_key), count)?,
        ])
    }

    fn finish(mut self) -> Result<(u64, u64, u64), CrossyearError> {
        self.flush()?;
        self.cache.finish()?;
        if let Some(labels) = self.labels {
            labels.finish()?;
        }
        Ok((self.total_rows, self.sequence_count, self.cache_rows))
    }
}

fn cache_schema() -> Arc<Schema> {
    Arc::new(Schema::new(vec![
        Field::new("sample_id", DataType::FixedSizeBinary(32), false),
        Field::new("year_role", DataType::Utf8, false),
        Field::new("sequence_id", DataType::FixedSizeBinary(32), false),
        Field::new("position", DataType::UInt16, false),
        Field::new("valid_length", DataType::UInt16, false),
        Field::new("available_ns", DataType::Int64, false),
        Field::new("delta_t_us", DataType::Int64, false),
        Field::new(
            "x_value",
            DataType::FixedSizeList(
                Arc::new(Field::new("item", DataType::Float32, false)),
                COMMON_FIELD_COUNT as i32,
            ),
            false,
        ),
        Field::new(
            "x_missing",
            DataType::FixedSizeList(
                Arc::new(Field::new("item", DataType::UInt8, false)),
                COMMON_FIELD_COUNT as i32,
            ),
            false,
        ),
        Field::new("padding_mask", DataType::UInt8, false),
        Field::new("group_key_ref", DataType::FixedSizeBinary(32), false),
    ]))
}

fn label_schema() -> Arc<Schema> {
    Arc::new(Schema::new(vec![
        Field::new("sample_id", DataType::FixedSizeBinary(32), false),
        Field::new("label", DataType::UInt8, false),
    ]))
}

#[derive(Debug)]
struct SampleManifestRow {
    sample_id: [u8; 32],
    role: YearRole,
    sequence_id: [u8; 32],
    position: u16,
    valid_length: u16,
    available_ns: i64,
    cache_selected: bool,
}

struct ManifestWriters {
    samples: AtomicParquetWriter,
    sequences: AtomicParquetWriter,
    sample_rows: Vec<SampleManifestRow>,
    sequence_rows: Vec<SequenceRow>,
    batch_size: usize,
}

impl ManifestWriters {
    fn create(config: &CrossyearConfig, staging: &Path) -> Result<Self, CrossyearError> {
        Ok(Self {
            samples: AtomicParquetWriter::create(
                &config.staged_path(&config.outputs.sample_manifest, staging)?,
                sample_manifest_schema(),
            )?,
            sequences: AtomicParquetWriter::create(
                &config.staged_path(&config.outputs.sequence_manifest, staging)?,
                sequence_manifest_schema(),
            )?,
            sample_rows: Vec::with_capacity(config.resources.output_batch_rows),
            sequence_rows: Vec::with_capacity(config.resources.output_batch_rows),
            batch_size: config.resources.output_batch_rows,
        })
    }

    fn push_sequence(
        &mut self,
        sequence: &SequenceRow,
        rows: &[FlowRow],
    ) -> Result<(), CrossyearError> {
        for (position, row) in rows.iter().enumerate() {
            self.sample_rows.push(SampleManifestRow {
                sample_id: row.sample_id,
                role: sequence.role,
                sequence_id: sequence.sequence_id,
                position: u16::try_from(position)
                    .map_err(|_| CrossyearError::Data("样本位置溢出".to_owned()))?,
                valid_length: sequence.valid_length,
                available_ns: row.available_ns,
                cache_selected: sequence.cache_selected,
            });
            if self.sample_rows.len() >= self.batch_size {
                self.flush_samples()?;
            }
        }
        self.sequence_rows.push(sequence.clone());
        if self.sequence_rows.len() >= self.batch_size {
            self.flush_sequences()?;
        }
        Ok(())
    }

    fn flush_samples(&mut self) -> Result<(), CrossyearError> {
        if self.sample_rows.is_empty() {
            return Ok(());
        }
        let count = self.sample_rows.len();
        self.samples.write(vec![
            fixed_binary(self.sample_rows.iter().map(|row| row.sample_id), count)?,
            Arc::new(StringArray::from_iter_values(
                self.sample_rows.iter().map(|row| row.role.name()),
            )) as ArrayRef,
            fixed_binary(self.sample_rows.iter().map(|row| row.sequence_id), count)?,
            Arc::new(UInt16Array::from_iter_values(
                self.sample_rows.iter().map(|row| row.position),
            )) as ArrayRef,
            Arc::new(UInt16Array::from_iter_values(
                self.sample_rows.iter().map(|row| row.valid_length),
            )) as ArrayRef,
            Arc::new(Int64Array::from_iter_values(
                self.sample_rows.iter().map(|row| row.available_ns),
            )) as ArrayRef,
            Arc::new(UInt8Array::from_iter_values(
                self.sample_rows
                    .iter()
                    .map(|row| u8::from(row.cache_selected)),
            )) as ArrayRef,
        ])?;
        self.sample_rows.clear();
        Ok(())
    }

    fn flush_sequences(&mut self) -> Result<(), CrossyearError> {
        if self.sequence_rows.is_empty() {
            return Ok(());
        }
        let count = self.sequence_rows.len();
        self.sequences.write(vec![
            fixed_binary(self.sequence_rows.iter().map(|row| row.sequence_id), count)?,
            Arc::new(StringArray::from_iter_values(
                self.sequence_rows.iter().map(|row| row.role.name()),
            )) as ArrayRef,
            fixed_binary(self.sequence_rows.iter().map(|row| row.group_key), count)?,
            Arc::new(UInt16Array::from_iter_values(
                self.sequence_rows.iter().map(|row| row.valid_length),
            )) as ArrayRef,
            Arc::new(Int64Array::from_iter_values(
                self.sequence_rows.iter().map(|row| row.first_available_ns),
            )) as ArrayRef,
            Arc::new(Int64Array::from_iter_values(
                self.sequence_rows.iter().map(|row| row.last_available_ns),
            )) as ArrayRef,
            Arc::new(UInt8Array::from_iter_values(
                self.sequence_rows
                    .iter()
                    .map(|row| u8::from(row.cache_selected)),
            )) as ArrayRef,
        ])?;
        self.sequence_rows.clear();
        Ok(())
    }

    fn finish(mut self) -> Result<(), CrossyearError> {
        self.flush_samples()?;
        self.flush_sequences()?;
        self.samples.finish()?;
        self.sequences.finish()
    }
}

fn sample_manifest_schema() -> Arc<Schema> {
    Arc::new(Schema::new(vec![
        Field::new("sample_id", DataType::FixedSizeBinary(32), false),
        Field::new("year_role", DataType::Utf8, false),
        Field::new("sequence_id", DataType::FixedSizeBinary(32), false),
        Field::new("position", DataType::UInt16, false),
        Field::new("valid_length", DataType::UInt16, false),
        Field::new("available_ns", DataType::Int64, false),
        Field::new("cache_selected", DataType::UInt8, false),
    ]))
}

fn sequence_manifest_schema() -> Arc<Schema> {
    Arc::new(Schema::new(vec![
        Field::new("sequence_id", DataType::FixedSizeBinary(32), false),
        Field::new("year_role", DataType::Utf8, false),
        Field::new("group_key_ref", DataType::FixedSizeBinary(32), false),
        Field::new("valid_length", DataType::UInt16, false),
        Field::new("first_available_ns", DataType::Int64, false),
        Field::new("last_available_ns", DataType::Int64, false),
        Field::new("cache_selected", DataType::UInt8, false),
    ]))
}

struct SequenceAssembler {
    current_pair: Option<[u8; 32]>,
    block: u64,
    rows: Vec<FlowRow>,
}

impl SequenceAssembler {
    fn new() -> Self {
        Self {
            current_pair: None,
            block: 0,
            rows: Vec::with_capacity(MAX_SEQUENCE_LENGTH),
        }
    }

    fn push(
        &mut self,
        row: FlowRow,
        writer: &mut RoleWriters,
        normalizer: &Normalizer,
        clip: f64,
        manifests: &mut ManifestWriters,
    ) -> Result<(), CrossyearError> {
        if self.current_pair.is_some_and(|pair| pair != row.pair_key) {
            self.flush(writer, normalizer, clip, manifests)?;
            self.block = 0;
        }
        self.current_pair = Some(row.pair_key);
        self.rows.push(row);
        if self.rows.len() == MAX_SEQUENCE_LENGTH {
            self.flush(writer, normalizer, clip, manifests)?;
            self.block = self
                .block
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("2-IP 块号溢出".to_owned()))?;
        }
        Ok(())
    }

    fn flush(
        &mut self,
        writer: &mut RoleWriters,
        normalizer: &Normalizer,
        clip: f64,
        manifests: &mut ManifestWriters,
    ) -> Result<(), CrossyearError> {
        if self.rows.is_empty() {
            return Ok(());
        }
        let rows = std::mem::replace(&mut self.rows, Vec::with_capacity(MAX_SEQUENCE_LENGTH));
        writer.push_sequence(rows, self.block, normalizer, clip, manifests)
    }
}

struct BucketRecords {
    path: PathBuf,
    reader: BufReader<File>,
    error: Option<CrossyearError>,
}

impl BucketRecords {
    fn open(path: &Path) -> Result<Self, CrossyearError> {
        let file = File::open(path).map_err(|source| io_error("打开桶输入", path, source))?;
        Ok(Self {
            path: path.to_path_buf(),
            reader: BufReader::with_capacity(256 * 1024, file),
            error: None,
        })
    }

    fn take_error(&mut self) -> Option<CrossyearError> {
        self.error.take()
    }

    fn read_record(&mut self) -> Result<Option<SortableRecord>, CrossyearError> {
        let mut length_bytes = [0u8; 4];
        match self.reader.read(&mut length_bytes[..1]) {
            Ok(0) => return Ok(None),
            Ok(1) => self
                .reader
                .read_exact(&mut length_bytes[1..])
                .map_err(|source| io_error("读取桶长度前缀", &self.path, source))?,
            Ok(_) => return Err(CrossyearError::Data("桶长度首字节读取异常".to_owned())),
            Err(source) => return Err(io_error("读取桶文件", &self.path, source)),
        }
        let length = usize::try_from(u32::from_be_bytes(length_bytes))
            .map_err(|_| CrossyearError::Data("桶记录长度无法转换".to_owned()))?;
        let mut payload = vec![0u8; length];
        self.reader
            .read_exact(&mut payload)
            .map_err(|source| io_error("读取桶记录", &self.path, source))?;
        let row = FlowRow::decode(&payload)?;
        let key = StableSortKey::new(
            row.pair_key,
            row.available_ns,
            row.start_ns,
            [0; 32],
            EndpointRoleOrder::Source,
            SourceRowIndex::new(row.source_row_index),
        );
        Ok(Some(SortableRecord::new(key, payload)))
    }
}

impl Iterator for BucketRecords {
    type Item = SortableRecord;

    fn next(&mut self) -> Option<Self::Item> {
        match self.read_record() {
            Ok(value) => value,
            Err(error) => {
                self.error = Some(error);
                None
            }
        }
    }
}

struct RawSequenceAssembler<F> {
    current_pair: Option<[u8; 32]>,
    block: u64,
    rows: Vec<FlowRow>,
    emit: F,
}

impl<F> RawSequenceAssembler<F>
where
    F: FnMut(&[FlowRow], u64) -> Result<(), CrossyearError>,
{
    fn new(emit: F) -> Self {
        Self {
            current_pair: None,
            block: 0,
            rows: Vec::with_capacity(MAX_SEQUENCE_LENGTH),
            emit,
        }
    }

    fn push(&mut self, row: FlowRow) -> Result<(), CrossyearError> {
        if self.current_pair.is_some_and(|pair| pair != row.pair_key) {
            self.flush()?;
            self.block = 0;
        }
        self.current_pair = Some(row.pair_key);
        self.rows.push(row);
        if self.rows.len() == MAX_SEQUENCE_LENGTH {
            self.flush()?;
            self.block = self
                .block
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("原始序列块号溢出".to_owned()))?;
        }
        Ok(())
    }

    fn flush(&mut self) -> Result<(), CrossyearError> {
        if self.rows.is_empty() {
            return Ok(());
        }
        (self.emit)(&self.rows, self.block)?;
        self.rows.clear();
        Ok(())
    }

    fn finish(mut self) -> Result<(), CrossyearError> {
        self.flush()
    }
}

fn for_each_role_sequence<F>(
    config: &CrossyearConfig,
    bucket_root: &Path,
    role: YearRole,
    pass: &str,
    mut emit: F,
) -> Result<(), CrossyearError>
where
    F: FnMut(&[FlowRow], u64) -> Result<(), CrossyearError>,
{
    let mut assembler = RawSequenceAssembler::new(|rows: &[FlowRow], block| emit(rows, block));
    for bucket in 0..BUCKET_COUNT {
        let path = bucket_root.join(format!("{}-bucket-{bucket:03}.bin", role.name()));
        if !path.exists() {
            continue;
        }
        let mut records = BucketRecords::open(&path)?;
        let work_dir = config
            .temporary_root
            .join(format!("{pass}-{}-{bucket:03}", role.name()));
        let sort_config = ExternalSortConfig::new(
            &work_dir,
            NonZeroUsize::new(MAX_BATCH_SIZE)
                .ok_or_else(|| CrossyearError::Data("排序批大小为零".to_owned()))?,
        );
        let mut emit_error = None;
        let sort_result = stable_external_sort(&mut records, &sort_config, |record| {
            if emit_error.is_some() {
                return Err(io::Error::other("先前序列遍历已失败"));
            }
            match FlowRow::decode(record.payload()).and_then(|row| assembler.push(row)) {
                Ok(()) => Ok(()),
                Err(error) => {
                    emit_error = Some(error);
                    Err(io::Error::other("序列遍历失败"))
                }
            }
        });
        if let Some(error) = records.take_error() {
            return Err(error);
        }
        if let Some(error) = emit_error {
            return Err(error);
        }
        sort_result.map_err(|error| CrossyearError::Data(format!("稳定外排失败：{error}")))?;
    }
    assembler.finish()
}

#[derive(Debug, Clone)]
struct SelectionCandidate {
    sequence_id: [u8; 32],
    selection_hash: [u8; 32],
    valid_length: u16,
    first_available_ns: i64,
    stratum: Option<u8>,
    contains_malicious: Option<bool>,
}

struct ActivityStrata {
    source_validation_seconds: Vec<i64>,
    target_development_seconds: Vec<i64>,
}

impl ActivityStrata {
    fn stratum(&self, role: YearRole, available_ns: i64) -> Result<Option<u8>, CrossyearError> {
        let seconds = match role {
            YearRole::SourceValidation => &self.source_validation_seconds,
            YearRole::TargetDevelopment => &self.target_development_seconds,
            _ => return Ok(None),
        };
        let second = available_ns.div_euclid(1_000_000_000);
        let rank = seconds
            .binary_search(&second)
            .map_err(|_| CrossyearError::Data(format!("角色 {} 的活动秒未登记", role.name())))?;
        let stratum = rank
            .checked_mul(64)
            .and_then(|value| value.checked_div(seconds.len()))
            .unwrap_or(0)
            .min(63);
        Ok(Some(u8::try_from(stratum).unwrap_or(63)))
    }
}

fn candidate_hash(role: YearRole, sequence_id: &[u8; 32]) -> Result<[u8; 32], CrossyearError> {
    let encoded = tuple_encode(&[
        CanonicalValue::Utf8("lspr-crossyear-sequence-selection-v1"),
        CanonicalValue::Utf8(role.name()),
        CanonicalValue::Sha256(sequence_id),
    ])
    .map_err(|error| CrossyearError::Data(error.to_string()))?;
    Ok(sha256(&encoded))
}

fn collect_selection_candidates(
    config: &CrossyearConfig,
    bucket_root: &Path,
    strata: &ActivityStrata,
) -> Result<BTreeMap<YearRole, Vec<SelectionCandidate>>, CrossyearError> {
    let mut candidates = BTreeMap::new();
    let mut total = 0usize;
    for role in YearRole::ALL {
        let mut role_candidates = Vec::new();
        for_each_role_sequence(config, bucket_root, role, "select", |rows, block| {
            total = total
                .checked_add(1)
                .ok_or_else(|| CrossyearError::Data("序列候选计数溢出".to_owned()))?;
            if total > config.resources.max_selection_candidates {
                return Err(CrossyearError::Data("序列候选状态超过配置上限".to_owned()));
            }
            let first = rows
                .first()
                .ok_or_else(|| CrossyearError::Data("候选序列为空".to_owned()))?;
            let id = sequence_id(role, &first.pair_key, block)?;
            let contains_malicious = if role == YearRole::SourceTrain {
                Some(rows.iter().any(|row| row.label == Some(1)))
            } else {
                None
            };
            role_candidates.push(SelectionCandidate {
                sequence_id: id,
                selection_hash: candidate_hash(role, &id)?,
                valid_length: u16::try_from(rows.len())
                    .map_err(|_| CrossyearError::Data("候选序列长度溢出".to_owned()))?,
                first_available_ns: first.available_ns,
                stratum: strata.stratum(role, first.available_ns)?,
                contains_malicious,
            });
            Ok(())
        })?;
        candidates.insert(role, role_candidates);
    }
    Ok(candidates)
}

fn select_with_budget<'a, I>(candidates: I, budget: u64, selected: &mut BTreeSet<[u8; 32]>) -> u64
where
    I: IntoIterator<Item = &'a SelectionCandidate>,
{
    let mut rows = 0u64;
    for candidate in candidates {
        let length = u64::from(candidate.valid_length);
        if rows
            .checked_add(length)
            .is_some_and(|value| value <= budget)
        {
            selected.insert(candidate.sequence_id);
            rows += length;
        }
    }
    rows
}

fn selected_digest(selected: &BTreeSet<[u8; 32]>) -> String {
    let mut hasher = Sha256::new();
    hasher.update(b"lspr-crossyear-selected-sequences-v1\0");
    for sequence_id in selected {
        hasher.update(sequence_id);
    }
    hex_digest(&hasher.finalize())
}

struct SelectionResult {
    selected: BTreeMap<YearRole, Arc<BTreeSet<[u8; 32]>>>,
    selected_rows: BTreeMap<&'static str, u64>,
    receipt: serde_json::Value,
}

fn select_sequences(
    config: &CrossyearConfig,
    mut candidates: BTreeMap<YearRole, Vec<SelectionCandidate>>,
) -> Result<SelectionResult, CrossyearError> {
    let mut selected_map = BTreeMap::new();
    let mut selected_rows = BTreeMap::new();
    let mut role_receipts = BTreeMap::new();
    for role in YearRole::ALL {
        let mut role_candidates = candidates
            .remove(&role)
            .ok_or_else(|| CrossyearError::Data("缺少角色候选".to_owned()))?;
        let budget = config.role_row_limits[role.name()];
        let mut selected = BTreeSet::new();
        let mut rows = 0u64;
        let detail = match role {
            YearRole::SourceTrain => {
                let half_budget = budget / 2;
                let mut malicious = role_candidates
                    .iter()
                    .filter(|candidate| candidate.contains_malicious == Some(true))
                    .collect::<Vec<_>>();
                let mut benign = role_candidates
                    .iter()
                    .filter(|candidate| candidate.contains_malicious == Some(false))
                    .collect::<Vec<_>>();
                malicious.sort_unstable_by_key(|candidate| candidate.selection_hash);
                benign.sort_unstable_by_key(|candidate| candidate.selection_hash);
                let mut malicious_selected = BTreeSet::new();
                let mut benign_selected = BTreeSet::new();
                let malicious_rows =
                    select_with_budget(malicious, half_budget, &mut malicious_selected);
                let benign_rows = select_with_budget(benign, half_budget, &mut benign_selected);
                rows = malicious_rows.saturating_add(benign_rows);
                selected.extend(malicious_selected.iter().copied());
                selected.extend(benign_selected.iter().copied());
                serde_json::json!({
                    "algorithm": "sequence-label-pools-1-to-1-stable-hash-v1",
                    "per_pool_row_budget": half_budget,
                    "malicious_pool_rows": malicious_rows,
                    "benign_pool_rows": benign_rows,
                    "malicious_pool_sequence_count": malicious_selected.len(),
                    "benign_pool_sequence_count": benign_selected.len(),
                    "malicious_pool_sequence_sha256": selected_digest(&malicious_selected),
                    "benign_pool_sequence_sha256": selected_digest(&benign_selected)
                })
            }
            YearRole::SourceValidation | YearRole::TargetDevelopment => {
                let per_stratum_budget = budget / 64;
                let mut stratum_rows = Vec::with_capacity(64);
                for stratum in 0u8..64 {
                    let mut stratum_candidates = role_candidates
                        .iter()
                        .filter(|candidate| candidate.stratum == Some(stratum))
                        .collect::<Vec<_>>();
                    stratum_candidates.sort_unstable_by_key(|candidate| candidate.selection_hash);
                    let count =
                        select_with_budget(stratum_candidates, per_stratum_budget, &mut selected);
                    rows = rows.saturating_add(count);
                    stratum_rows.push(count);
                }
                serde_json::json!({
                    "algorithm": "label-blind-64-active-second-rank-strata-stable-hash-v1",
                    "per_stratum_row_budget": per_stratum_budget,
                    "stratum_rows": stratum_rows
                })
            }
            YearRole::TargetPrefix => {
                role_candidates.sort_unstable_by(|left, right| {
                    left.first_available_ns
                        .cmp(&right.first_available_ns)
                        .then_with(|| left.selection_hash.cmp(&right.selection_hash))
                });
                rows = select_with_budget(&role_candidates, budget, &mut selected);
                serde_json::json!({"algorithm": "earliest-complete-sequences-v1"})
            }
        };
        let selected_sequence_count = selected.len();
        let digest = selected_digest(&selected);
        role_receipts.insert(
            role.name(),
            serde_json::json!({
                "candidate_sequence_count": role_candidates.len(),
                "selected_sequence_count": selected_sequence_count,
                "selected_row_count": rows,
                "selected_sequence_sha256": digest,
                "detail": detail
            }),
        );
        selected_rows.insert(role.name(), rows);
        selected_map.insert(role, Arc::new(selected));
    }
    Ok(SelectionResult {
        selected: selected_map,
        selected_rows,
        receipt: serde_json::json!({
            "schema_version": "lspr-crossyear-sequence-selection-v1",
            "materialization_mode": config.materialization_mode,
            "budget_tier": config.budget_tier,
            "role_row_limits": config.role_row_limits,
            "pair_hash_prescreen": {
                "algorithm": "label-blind-pair-key-sha256-leading-byte-v1",
                "keep_when": "pair_key[0] < role_threshold",
                "denominator": 256,
                "role_thresholds": config.pair_hash_keep_thresholds
            },
            "roles": role_receipts,
            "target_label_used_for_selection": false,
            "sequence_split_allowed": false,
            "final_accessed": false
        }),
    })
}

fn fit_selected_source_normalizer(
    config: &CrossyearConfig,
    bucket_root: &Path,
    selected: &BTreeSet<[u8; 32]>,
    expected_rows: u64,
) -> Result<Normalizer, CrossyearError> {
    let capacity = config.resources.quantile_sample_per_field;
    let mut sampler = NormalizerSampler::new(capacity);
    let mut observed = 0u64;
    for_each_role_sequence(
        config,
        bucket_root,
        YearRole::SourceTrain,
        "normalizer",
        |rows, block| {
            let first = rows
                .first()
                .ok_or_else(|| CrossyearError::Data("归一化序列为空".to_owned()))?;
            let id = sequence_id(YearRole::SourceTrain, &first.pair_key, block)?;
            if selected.contains(&id) {
                for row in rows {
                    sampler.observe(row)?;
                    observed = observed
                        .checked_add(1)
                        .ok_or_else(|| CrossyearError::Data("归一化行计数溢出".to_owned()))?;
                }
            }
            Ok(())
        },
    )?;
    if observed != expected_rows {
        return Err(CrossyearError::Data(format!(
            "归一化入选行数不匹配：期望 {expected_rows}，实际 {observed}"
        )));
    }
    sampler.finish(config.normalization_epsilon, config.normalization_clip)
}

#[derive(Serialize)]
struct FieldManifest<'a> {
    schema_version: &'static str,
    common_model_fields: &'a [&'a str],
    forbidden_fields: &'a [&'a str],
    model_feature_count: usize,
    missing_mask_emitted: bool,
    protocol_role: &'static str,
    available_time: &'static str,
}

#[derive(Serialize)]
struct FinalIsolationReceipt {
    schema_version: &'static str,
    final_accessed: bool,
    final_feature_artifacts: Vec<String>,
    final_label_artifacts: Vec<String>,
    final_member_artifacts: Vec<String>,
    final_specific_statistics: Vec<String>,
    routing_rule: &'static str,
}

fn write_json<T: Serialize>(path: &Path, value: &T) -> Result<(), CrossyearError> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|source| io_error("创建 JSON 父目录", parent, source))?;
    }
    let mut bytes = serde_json::to_vec_pretty(value)
        .map_err(|error| CrossyearError::Serialization(error.to_string()))?;
    bytes.push(b'\n');
    let mut output = PartialOutput::create(path)?;
    PartialOutput::write_all(&mut output, &bytes)?;
    output.commit()?;
    Ok(())
}

fn hash_file(path: &Path) -> Result<String, CrossyearError> {
    let mut file = File::open(path).map_err(|source| io_error("打开哈希输入", path, source))?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 1024 * 1024];
    loop {
        let count = file
            .read(&mut buffer)
            .map_err(|source| io_error("读取哈希输入", path, source))?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
    }
    Ok(hex_digest(&hasher.finalize()))
}

fn hex_digest(bytes: &[u8]) -> String {
    use std::fmt::Write as _;
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        let _ = write!(output, "{byte:02x}");
    }
    output
}

fn available_bytes(path: &Path) -> Result<u64, CrossyearError> {
    let output = Command::new("df")
        .arg("-Pk")
        .arg(path)
        .output()
        .map_err(|source| io_error("查询磁盘空间", path, source))?;
    if !output.status.success() {
        return Err(CrossyearError::Data(format!("df 退出码={}", output.status)));
    }
    let text = String::from_utf8(output.stdout)
        .map_err(|_| CrossyearError::Data("df 输出不是 UTF-8".to_owned()))?;
    let line = text
        .lines()
        .last()
        .ok_or_else(|| CrossyearError::Data("df 输出为空".to_owned()))?;
    let blocks = line
        .split_whitespace()
        .nth(3)
        .ok_or_else(|| CrossyearError::Data("df 输出列不足".to_owned()))?
        .parse::<u64>()
        .map_err(|_| CrossyearError::Data("df 可用空间无法解析".to_owned()))?;
    blocks
        .checked_mul(1024)
        .ok_or_else(|| CrossyearError::Data("df 可用空间溢出".to_owned()))
}

fn ensure_sort_workspace_limit(
    bucket_root: &Path,
    bucket_bytes: u64,
    limit: u64,
) -> Result<(), CrossyearError> {
    let mut largest_bucket = 0u64;
    let entries =
        fs::read_dir(bucket_root).map_err(|source| io_error("枚举桶目录", bucket_root, source))?;
    for entry in entries {
        let entry = entry.map_err(|source| io_error("读取桶目录项", bucket_root, source))?;
        let metadata = entry
            .metadata()
            .map_err(|source| io_error("读取桶文件元数据", &entry.path(), source))?;
        if metadata.is_file() {
            largest_bucket = largest_bucket.max(metadata.len());
        }
    }
    // 外排只处理一个桶；两倍最大桶为排序键与段文件保守预留。
    let required = largest_bucket
        .checked_mul(2)
        .and_then(|workspace| bucket_bytes.checked_add(workspace))
        .ok_or_else(|| CrossyearError::Data("临时空间需求溢出".to_owned()))?;
    if required > limit {
        return Err(CrossyearError::TemporaryLimit {
            actual: required,
            limit,
        });
    }
    eprintln!(
        "资源门禁：桶字节={bucket_bytes}，最大桶字节={largest_bucket}，外排保守需求={required}，临时上限={limit}"
    );
    Ok(())
}

fn staged_artifact_hashes(
    config: &CrossyearConfig,
    staging: &Path,
) -> Result<BTreeMap<String, serde_json::Value>, CrossyearError> {
    let mut artifacts = BTreeMap::new();
    for (name, formal) in [
        ("field_manifest", &config.outputs.field_manifest),
        ("normalizer", &config.outputs.normalizer),
        ("sample_manifest", &config.outputs.sample_manifest),
        ("sequence_manifest", &config.outputs.sequence_manifest),
        ("selection_receipt", &config.outputs.selection_receipt),
        (
            "final_isolation_receipt",
            &config.outputs.final_isolation_receipt,
        ),
    ] {
        let staged = config.staged_path(formal, staging)?;
        artifacts.insert(
            name.to_owned(),
            serde_json::json!({"path": formal, "sha256": hash_file(&staged)?}),
        );
    }
    for (role_name, paths) in &config.outputs.roles {
        for (kind, formal) in [
            ("cache", Some(&paths.cache)),
            ("labels", paths.labels.as_ref()),
        ] {
            if let Some(formal) = formal {
                let staged = config.staged_path(formal, staging)?;
                artifacts.insert(
                    format!("{role_name}:{kind}"),
                    serde_json::json!({"path": formal, "sha256": hash_file(&staged)?}),
                );
            }
        }
    }
    Ok(artifacts)
}

fn process_sorted_roles(
    config: &CrossyearConfig,
    staging: &Path,
    bucket_root: &Path,
    normalizer: &Normalizer,
    selections: &BTreeMap<YearRole, Arc<BTreeSet<[u8; 32]>>>,
) -> Result<
    (
        BTreeMap<&'static str, u64>,
        BTreeMap<&'static str, u64>,
        BTreeMap<&'static str, u64>,
        BTreeMap<&'static str, String>,
    ),
    CrossyearError,
> {
    let mut manifests = ManifestWriters::create(config, staging)?;
    let mut role_rows = BTreeMap::new();
    let mut role_sequences = BTreeMap::new();
    let mut cache_rows = BTreeMap::new();
    let mut role_semantic_hashes = BTreeMap::new();
    for role in YearRole::ALL {
        let paths = config
            .outputs
            .roles
            .get(role.name())
            .ok_or_else(|| CrossyearError::Config(format!("缺少角色 {} 输出", role.name())))?;
        let selected = selections
            .get(&role)
            .ok_or_else(|| CrossyearError::Data(format!("缺少角色 {} 选择集合", role.name())))?;
        let mut writer = RoleWriters::create(role, paths, config, staging, Arc::clone(selected))?;
        let mut assembler = SequenceAssembler::new();
        let mut progress = StageProgress::start(
            "稳定排序并写出角色",
            config.resources.progress_interval_rows,
        );
        let mut role_semantic_hasher = Sha256::new();
        role_semantic_hasher.update(b"lspr-crossyear-role-semantic-v1\0");
        role_semantic_hasher.update(role.name().as_bytes());
        for bucket in 0..BUCKET_COUNT {
            let path = bucket_root.join(format!("{}-bucket-{bucket:03}.bin", role.name()));
            if !path.exists() {
                continue;
            }
            let mut records = BucketRecords::open(&path)?;
            let work_dir = config
                .temporary_root
                .join(format!("sort-{}-{bucket:03}", role.name()));
            let sort_config = ExternalSortConfig::new(
                &work_dir,
                NonZeroUsize::new(MAX_BATCH_SIZE)
                    .ok_or_else(|| CrossyearError::Data("排序批大小为零".to_owned()))?,
            );
            let mut emit_error = None;
            let sort_result = stable_external_sort(&mut records, &sort_config, |record| {
                if emit_error.is_some() {
                    return Err(io::Error::other("先前写出已失败"));
                }
                let result = FlowRow::decode(record.payload()).and_then(|row| {
                    progress.advance();
                    assembler.push(
                        row,
                        &mut writer,
                        normalizer,
                        config.normalization_clip,
                        &mut manifests,
                    )
                });
                if let Err(error) = result {
                    emit_error = Some(error);
                    return Err(io::Error::other("角色写出失败"));
                }
                Ok(())
            });
            if let Some(error) = records.take_error() {
                return Err(error);
            }
            if let Some(error) = emit_error {
                return Err(error);
            }
            let summary = sort_result
                .map_err(|error| CrossyearError::Data(format!("稳定外排失败：{error}")))?;
            role_semantic_hasher.update(
                u16::try_from(bucket)
                    .map_err(|_| CrossyearError::Data("桶编号溢出".to_owned()))?
                    .to_le_bytes(),
            );
            role_semantic_hasher.update(summary.row_count().to_le_bytes());
            role_semantic_hasher.update(summary.dataset_sha256());
            fs::remove_file(&path).map_err(|source| io_error("删除已处理桶", &path, source))?;
        }
        assembler.flush(
            &mut writer,
            normalizer,
            config.normalization_clip,
            &mut manifests,
        )?;
        progress.finish();
        let (rows, sequences, cached) = writer.finish()?;
        role_rows.insert(role.name(), rows);
        role_sequences.insert(role.name(), sequences);
        cache_rows.insert(role.name(), cached);
        role_semantic_hashes.insert(role.name(), hex_digest(&role_semantic_hasher.finalize()));
    }
    manifests.finish()?;
    Ok((role_rows, role_sequences, cache_rows, role_semantic_hashes))
}

/// 直接从两年度官方输入生成四角色共享的冻结有界快速缓存。
///
/// # Errors
///
/// 配置、输入模式、边界、隔离、资源上限、Parquet 写出或原子发布失败时返回错误。
pub fn materialize_crossyear(config: &CrossyearConfig) -> Result<CrossyearReceipt, CrossyearError> {
    config.validate()?;
    eprintln!(
        "启动跨年度有界快速缓存：预算级别={}，桶数={}，批行数={}，序列上限={}，序列候选上限={}，精确分位数状态上限={}×{}，峰值内存估算={:.2}GiB，临时上限={}GiB，输入估算={:.2}GiB，输出估算={:.2}GiB，总I/O估算={:.2}GiB，磁盘低水位={}GiB",
        config.budget_tier,
        config.resources.stable_hash_buckets,
        config.resources.max_batch_rows,
        config.resources.max_sequence_flows,
        config.resources.max_selection_candidates,
        NUMERIC_FIELD_COUNT,
        config.resources.quantile_sample_per_field,
        config.resources.estimated_peak_memory_gib,
        config.resources.temporary_directory_limit_gib,
        config.resources.estimated_input_gib,
        config.resources.estimated_output_gib,
        config.resources.estimated_total_io_gib,
        config.resources.disk_low_watermark_gib,
    );
    for input in [&config.lspr23_zip_path, &config.lspr24_parquet_path] {
        if !input.is_file() {
            return Err(CrossyearError::Config(format!(
                "输入不存在：{}",
                input.display()
            )));
        }
    }
    if config.output_root.exists() {
        return Err(CrossyearError::Config(format!(
            "输出根已存在：{}",
            config.output_root.display()
        )));
    }
    let mut staging_os = config.output_root.as_os_str().to_os_string();
    staging_os.push(".partial");
    let staging = PathBuf::from(staging_os);
    if staging.exists() || config.temporary_root.exists() {
        return Err(CrossyearError::Config(
            "暂存目录或临时目录已存在".to_owned(),
        ));
    }
    let available = available_bytes(&config.project_root)?;
    let low_water = config
        .resources
        .disk_low_watermark_gib
        .checked_mul(GIB)
        .ok_or_else(|| CrossyearError::Config("磁盘低水位溢出".to_owned()))?;
    if available < low_water {
        return Err(CrossyearError::Data(format!(
            "可用磁盘 {} 字节低于低水位",
            available
        )));
    }
    fs::create_dir_all(&staging).map_err(|source| io_error("创建输出暂存根", &staging, source))?;
    fs::create_dir(&config.temporary_root)
        .map_err(|source| io_error("创建临时根", &config.temporary_root, source))?;

    let hash_stage = StageProgress::start("计算输入哈希", config.resources.progress_interval_rows);
    let lspr23_sha256 = hash_file(&config.lspr23_zip_path)?;
    let lspr24_sha256 = hash_file(&config.lspr24_parquet_path)?;
    hash_stage.finish();

    let active_2023 = scan_lspr23_activity(config)?;
    let active_2024 = scan_lspr24_activity(config)?;
    let source_cut_ns = active_cut(&active_2023, config.source_train_fraction)?;
    let target_prefix_ns = active_cut(&active_2024, config.target_prefix_fraction)?;
    let target_final_ns = active_cut(&active_2024, config.target_development_end_fraction)?;
    let source_seconds = active_2023.iter().copied().collect::<Vec<_>>();
    let target_seconds = active_2024.iter().copied().collect::<Vec<_>>();
    let source_cut_index = active_rank_index(source_seconds.len(), config.source_train_fraction)?;
    let target_prefix_index =
        active_rank_index(target_seconds.len(), config.target_prefix_fraction)?;
    let target_final_index =
        active_rank_index(target_seconds.len(), config.target_development_end_fraction)?;
    let strata = ActivityStrata {
        source_validation_seconds: source_seconds[source_cut_index..].to_vec(),
        target_development_seconds: target_seconds[target_prefix_index..target_final_index]
            .to_vec(),
    };
    drop(active_2023);
    drop(active_2024);

    let temp_limit = config
        .resources
        .temporary_directory_limit_gib
        .checked_mul(GIB)
        .ok_or_else(|| CrossyearError::Config("临时目录上限溢出".to_owned()))?;
    let bucket_root = config.temporary_root.join("buckets");
    let mut buckets = BucketWriters::new(
        bucket_root.clone(),
        config.resources.max_open_bucket_files,
        temp_limit,
        low_water,
    )?;
    let mut isolation = IsolationCounts::default();
    process_lspr23(config, source_cut_ns, &mut buckets, &mut isolation)?;
    process_lspr24(
        config,
        target_prefix_ns,
        target_final_ns,
        &mut buckets,
        &mut isolation,
    )?;
    let temporary_bytes = buckets.finish()?;
    ensure_sort_workspace_limit(&bucket_root, temporary_bytes, temp_limit)?;
    eprintln!("阶段结束：输入分桶，临时字节={temporary_bytes}");

    let candidates = collect_selection_candidates(config, &bucket_root, &strata)?;
    let selection = select_sequences(config, candidates)?;
    eprintln!(
        "阶段结束：完整序列选择，角色缓存行数={:?}",
        selection.selected_rows
    );
    write_json(
        &config.staged_path(&config.outputs.selection_receipt, &staging)?,
        &selection.receipt,
    )?;
    let source_selected = selection
        .selected
        .get(&YearRole::SourceTrain)
        .ok_or_else(|| CrossyearError::Data("缺少 source-train 选择集合".to_owned()))?;
    let source_selected_rows = selection.selected_rows[YearRole::SourceTrain.name()];
    let normalizer = fit_selected_source_normalizer(
        config,
        &bucket_root,
        source_selected,
        source_selected_rows,
    )?;

    write_json(
        &config.staged_path(&config.outputs.field_manifest, &staging)?,
        &FieldManifest {
            schema_version: "lspr-crossyear-field-manifest-v1",
            common_model_fields: &COMMON_FIELDS,
            forbidden_fields: &FORBIDDEN_FIELDS,
            model_feature_count: COMMON_FIELD_COUNT,
            missing_mask_emitted: true,
            protocol_role: "source-train-vocabulary-with-unk-and-missing",
            available_time: "mTimestampLast*1000",
        },
    )?;
    write_json(
        &config.staged_path(&config.outputs.normalizer, &staging)?,
        &normalizer,
    )?;
    let (role_rows, role_sequences, cache_rows, role_semantic_hashes) = process_sorted_roles(
        config,
        &staging,
        &bucket_root,
        &normalizer,
        &selection.selected,
    )?;
    if cache_rows != selection.selected_rows {
        return Err(CrossyearError::Data(
            "正式缓存行数与选择收据不匹配".to_owned(),
        ));
    }
    let final_receipt = FinalIsolationReceipt {
        schema_version: "lspr-crossyear-final-isolation-v1",
        final_accessed: false,
        final_feature_artifacts: Vec::new(),
        final_label_artifacts: Vec::new(),
        final_member_artifacts: Vec::new(),
        final_specific_statistics: Vec::new(),
        routing_rule: "LSPR24 行 available_ns >= target_final_cut_ns 时，在访问 IP、标签和特征前丢弃",
    };
    write_json(
        &config.staged_path(&config.outputs.final_isolation_receipt, &staging)?,
        &final_receipt,
    )?;

    let artifacts = staged_artifact_hashes(config, &staging)?;
    let dataset_manifest = serde_json::json!({
        "schema_version": "lspr-crossyear-dataset-manifest-v1",
        "contract_version": CONTRACT_VERSION,
        "materialization_mode": config.materialization_mode,
        "budget_tier": config.budget_tier,
        "role_row_limits": config.role_row_limits,
        "pair_hash_keep_thresholds": config.pair_hash_keep_thresholds,
        "inputs": {
            "lspr23_zip": {"path": config.lspr23_zip_path, "member": config.lspr23_zip_member, "sha256": lspr23_sha256},
            "lspr24_parquet": {"path": config.lspr24_parquet_path, "sha256": lspr24_sha256}
        },
        "splits": {
            "source_train_cut_ns": source_cut_ns,
            "target_prefix_cut_ns": target_prefix_ns,
            "target_final_cut_ns": target_final_ns,
            "algorithm": "ceil-active-second-rank-v1"
        },
        "role_rows": role_rows,
        "role_sequences": role_sequences,
        "cache_rows": cache_rows,
        "prescreen_role_semantic_sha256": role_semantic_hashes,
        "isolated_rows": isolation.counts,
        "artifacts": artifacts,
        "final_feature_artifacts": [],
        "final_label_artifacts": [],
        "final_member_artifacts": [],
        "final_specific_statistics": [],
        "final_accessed": false
    });
    let dataset_staged = config.staged_path(&config.outputs.dataset_manifest, &staging)?;
    write_json(&dataset_staged, &dataset_manifest)?;
    let dataset_manifest_sha256 = hash_file(&dataset_staged)?;
    let experiment_manifest = serde_json::json!({
        "schema_version": "lspr-crossyear-experiment-manifest-v1",
        "materialization_mode": config.materialization_mode,
        "budget_tier": config.budget_tier,
        "dataset_manifest": {"path": config.outputs.dataset_manifest, "sha256": dataset_manifest_sha256},
        "model_fields": COMMON_FIELDS.as_slice(),
        "field_count": COMMON_FIELD_COUNT,
        "variants": config.variants,
        "cache_rows": cache_rows,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "normalizer": {"path": config.outputs.normalizer, "fitted_role": "source-train"},
        "labels_outside_features": true,
        "group_key_outside_features": true,
        "final_accessed": false
    });
    let experiment_staged = config.staged_path(&config.outputs.experiment_manifest, &staging)?;
    write_json(&experiment_staged, &experiment_manifest)?;
    let experiment_manifest_sha256 = hash_file(&experiment_staged)?;
    let run_receipt = serde_json::json!({
        "schema_version": "lspr-crossyear-materialization-receipt-v1",
        "status": "succeeded",
        "materialization_mode": config.materialization_mode,
        "budget_tier": config.budget_tier,
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "experiment_manifest_sha256": experiment_manifest_sha256,
        "temporary_bytes": temporary_bytes,
        "role_rows": role_rows,
        "role_sequences": role_sequences,
        "cache_rows": cache_rows,
        "final_accessed": false
    });
    write_json(
        &config.staged_path(&config.outputs.run_receipt, &staging)?,
        &run_receipt,
    )?;

    fs::remove_dir_all(&config.temporary_root)
        .map_err(|source| io_error("清理临时根", &config.temporary_root, source))?;
    fs::rename(&staging, &config.output_root)
        .map_err(|source| io_error("发布输出根", &config.output_root, source))?;
    eprintln!("跨年度物化完成：final_accessed=false");
    Ok(CrossyearReceipt {
        schema_version: "lspr-crossyear-materialization-receipt-v1",
        output_root: config.output_root.clone(),
        dataset_manifest: config.outputs.dataset_manifest.clone(),
        experiment_manifest: config.outputs.experiment_manifest.clone(),
        role_rows,
        role_sequences,
        isolated_rows: isolation.counts,
        final_accessed: false,
    })
}
