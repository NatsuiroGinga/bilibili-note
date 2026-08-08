//! 真实 Parquet 的 G0-D 无标签切分与受限开发物化入口。

use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fmt::{Display, Formatter};
use std::fs::{self, File};
use std::io::{self, Read};
use std::path::{Path, PathBuf};

use arrow_array::{Array, Int32Array, Int64Array, RecordBatch, StringArray};
use arrow_schema::{DataType, Schema};
use parquet::arrow::ProjectionMask;
use parquet::arrow::arrow_reader::ParquetRecordBatchReaderBuilder;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::development_router::{
    DevelopmentMemberId, DevelopmentSegment, LSPR24_G0_CONTRACT_SHA256,
    LSPR24_G0_CONTRACT_VERSION,
};
use crate::{
    NumericColumn, OutputError, PartialOutput, ScreenSourceError, Sha256Digest,
    parse_external_marker, resolve_protected_endpoints, utc_ns_from_micros,
};

/// 正式开发配置模式版本。
pub const FORMAL_DEVELOPMENT_CONFIG_SCHEMA_VERSION: &str =
    "lspr24-g0-development-config-v2";
const SPLIT_RECEIPT_SCHEMA_VERSION: &str = "lspr24-g0-development-split-v1";
const SPLIT_ALGORITHM_SPEC: &[u8] = b"lspr24-activity-rank-split-v4\0ceil-40-50-60-80\0source-order-members";
const BILLION: i64 = 1_000_000_000;

const UNLABELED_COLUMNS: [&str; 10] = [
    "mTimestampStart",
    "mTimestampLast",
    "SrcIP",
    "DstIP",
    "External_src",
    "External_dst",
    "SrcPort",
    "DstPort",
    "Protocol",
    "Flow ID",
];

/// 不接受调用者成员选择的正式 Parquet 配置。
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FormalDevelopmentConfig {
    schema_version: String,
    contract_version: String,
    contract_sha256: String,
    parquet_path: PathBuf,
    split_receipt_path: PathBuf,
    output_path: PathBuf,
    feature_columns: Vec<String>,
}

impl FormalDevelopmentConfig {
    /// 创建绑定当前合同的正式开发配置。
    #[must_use]
    pub fn new(
        parquet_path: impl Into<PathBuf>,
        split_receipt_path: impl Into<PathBuf>,
        output_path: impl Into<PathBuf>,
        feature_columns: Vec<String>,
    ) -> Self {
        Self {
            schema_version: FORMAL_DEVELOPMENT_CONFIG_SCHEMA_VERSION.to_owned(),
            contract_version: LSPR24_G0_CONTRACT_VERSION.to_owned(),
            contract_sha256: LSPR24_G0_CONTRACT_SHA256.to_owned(),
            parquet_path: parquet_path.into(),
            split_receipt_path: split_receipt_path.into(),
            output_path: output_path.into(),
            feature_columns,
        }
    }

    /// 从严格 JSON 字节解析配置。
    pub fn from_json(bytes: &[u8]) -> Result<Self, FormalEntryError> {
        let config: Self = serde_json::from_slice(bytes)
            .map_err(|error| FormalEntryError::Config(error.to_string()))?;
        config.validate()?;
        Ok(config)
    }

    /// 返回输入 Parquet 路径。
    #[must_use]
    pub fn parquet_path(&self) -> &Path {
        &self.parquet_path
    }

    /// 返回外部无标签切分收据路径。
    #[must_use]
    pub fn split_receipt_path(&self) -> &Path {
        &self.split_receipt_path
    }

    /// 返回开发输出路径。
    #[must_use]
    pub fn output_path(&self) -> &Path {
        &self.output_path
    }

    fn validate(&self) -> Result<(), FormalEntryError> {
        if self.schema_version != FORMAL_DEVELOPMENT_CONFIG_SCHEMA_VERSION {
            return Err(FormalEntryError::Config("开发配置模式版本不匹配".to_owned()));
        }
        if self.contract_version != LSPR24_G0_CONTRACT_VERSION
            || self.contract_sha256 != LSPR24_G0_CONTRACT_SHA256
        {
            return Err(FormalEntryError::Config(
                "开发配置未绑定当前分阶段合同".to_owned(),
            ));
        }
        if self.feature_columns.is_empty() {
            return Err(FormalEntryError::Config("合法特征列不能为空".to_owned()));
        }
        let mut unique = BTreeSet::new();
        for column in &self.feature_columns {
            if !unique.insert(column.as_str()) || forbidden_feature_column(column) {
                return Err(FormalEntryError::Config(format!(
                    "非法或重复的开发特征列：{column}"
                )));
            }
        }
        Ok(())
    }
}

/// 外部无标签切分收据的已验证摘要。
#[derive(Debug, Clone)]
pub struct UnlabeledDevelopmentSplitReceipt {
    stored: StoredSplitReceipt,
}

impl UnlabeledDevelopmentSplitReceipt {
    /// 返回合同版本。
    #[must_use]
    pub fn contract_version(&self) -> &str {
        &self.stored.contract_version
    }

    /// 返回合同摘要文本。
    #[must_use]
    pub fn contract_sha256(&self) -> &str {
        &self.stored.contract_sha256
    }

    /// 返回来源 Parquet 摘要。
    #[must_use]
    pub const fn parquet_sha256(&self) -> Sha256Digest {
        self.stored.parquet_sha256
    }

    /// 返回切分算法摘要。
    #[must_use]
    pub const fn split_algorithm_sha256(&self) -> Sha256Digest {
        self.stored.split_algorithm_sha256
    }

    /// 返回 40%、50%、60%、80% 的活动秒切点。
    #[must_use]
    pub const fn cut_ns(&self) -> [i64; 4] {
        self.stored.cut_ns
    }

    /// 返回开发成员数；不包含最终成员数。
    #[must_use]
    pub const fn development_member_count(&self) -> u64 {
        self.stored.development_member_count
    }

    /// 返回开发成员摘要；不计算最终成员摘要。
    #[must_use]
    pub const fn development_member_sha256(&self) -> Sha256Digest {
        self.stored.development_member_sha256
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct StoredSplitReceipt {
    schema_version: String,
    contract_version: String,
    contract_sha256: String,
    #[serde(with = "hex_digest")]
    parquet_sha256: Sha256Digest,
    #[serde(with = "hex_digest")]
    split_algorithm_sha256: Sha256Digest,
    cut_ns: [i64; 4],
    development_member_count: u64,
    quarantined_non_finite_feature_count: u64,
    #[serde(with = "hex_digest")]
    development_member_sha256: Sha256Digest,
    #[serde(with = "hex_digest")]
    receipt_sha256: Sha256Digest,
}

/// 正式开发物化的开发侧收据。
#[derive(Debug, Clone)]
pub struct FormalDevelopmentMaterializationReceipt {
    output_path: PathBuf,
    development_row_count: u64,
    development_semantic_sha256: Sha256Digest,
    split_receipt_sha256: Sha256Digest,
    quarantined_non_finite_feature_count: u64,
}

impl FormalDevelopmentMaterializationReceipt {
    /// 返回开发输出路径。
    #[must_use]
    pub fn output_path(&self) -> &Path {
        &self.output_path
    }

    /// 返回开发输出行数。
    #[must_use]
    pub const fn development_row_count(&self) -> u64 {
        self.development_row_count
    }

    /// 返回开发输出语义摘要。
    #[must_use]
    pub const fn development_semantic_sha256(&self) -> Sha256Digest {
        self.development_semantic_sha256
    }

    /// 返回已验证外部切分收据摘要。
    #[must_use]
    pub const fn split_receipt_sha256(&self) -> Sha256Digest {
        self.split_receipt_sha256
    }

    /// 返回因非有限数值特征而隔离的开发行数。
    #[must_use]
    pub const fn quarantined_non_finite_feature_count(&self) -> u64 {
        self.quarantined_non_finite_feature_count
    }
}

/// 第一阶段只读取无标签列，生成排他的外部切分收据。
pub fn prepare_unlabeled_development_split(
    config: &FormalDevelopmentConfig,
) -> Result<UnlabeledDevelopmentSplitReceipt, FormalEntryError> {
    config.validate()?;
    let parquet_sha256 = file_sha256(&config.parquet_path)?;
    let facts = recompute_split_facts(&config.parquet_path, &config.feature_columns)?;
    let mut stored = StoredSplitReceipt {
        schema_version: SPLIT_RECEIPT_SCHEMA_VERSION.to_owned(),
        contract_version: LSPR24_G0_CONTRACT_VERSION.to_owned(),
        contract_sha256: LSPR24_G0_CONTRACT_SHA256.to_owned(),
        parquet_sha256,
        split_algorithm_sha256: split_algorithm_sha256(),
        cut_ns: facts.cut_ns,
        development_member_count: facts.development_member_count,
        quarantined_non_finite_feature_count: facts.quarantined_non_finite_feature_count,
        development_member_sha256: facts.development_member_sha256,
        receipt_sha256: [0; 32],
    };
    stored.receipt_sha256 = stored_receipt_sha256(&stored)?;
    let bytes = serde_json::to_vec(&stored)
        .map_err(|error| FormalEntryError::Receipt(error.to_string()))?;
    let mut output = PartialOutput::create(&config.split_receipt_path)
        .map_err(FormalEntryError::Output)?;
    output.write_all(&bytes).map_err(FormalEntryError::Output)?;
    output.commit().map_err(FormalEntryError::Output)?;
    Ok(UnlabeledDevelopmentSplitReceipt { stored })
}

/// 复验外部无标签切分收据后，只路由并物化前 80% 开发行。
pub fn run_formal_development_materialization(
    config: &FormalDevelopmentConfig,
) -> Result<FormalDevelopmentMaterializationReceipt, FormalEntryError> {
    config.validate()?;
    let receipt_bytes = fs::read(&config.split_receipt_path).map_err(|source| {
        FormalEntryError::Io {
            path: config.split_receipt_path.clone(),
            source,
        }
    })?;
    let stored: StoredSplitReceipt = serde_json::from_slice(&receipt_bytes)
        .map_err(|error| FormalEntryError::Receipt(error.to_string()))?;
    verify_receipt_self_hash(&stored)?;
    verify_split_binding(config, &stored)?;

    let output_result = write_development_rows(config, &stored);
    output_result.map(|mut receipt| {
        receipt.split_receipt_sha256 = stored.receipt_sha256;
        receipt
    })
}

fn verify_receipt_self_hash(stored: &StoredSplitReceipt) -> Result<(), FormalEntryError> {
    if stored.receipt_sha256 != stored_receipt_sha256(stored)? {
        return Err(FormalEntryError::ReceiptHashMismatch);
    }
    Ok(())
}

fn verify_split_binding(
    config: &FormalDevelopmentConfig,
    stored: &StoredSplitReceipt,
) -> Result<(), FormalEntryError> {
    if stored.schema_version != SPLIT_RECEIPT_SCHEMA_VERSION {
        return Err(binding_mismatch("schema_version"));
    }
    if stored.contract_version != LSPR24_G0_CONTRACT_VERSION {
        return Err(binding_mismatch("contract_version"));
    }
    if stored.contract_sha256 != LSPR24_G0_CONTRACT_SHA256 {
        return Err(binding_mismatch("contract_sha256"));
    }
    if stored.parquet_sha256 != file_sha256(&config.parquet_path)? {
        return Err(binding_mismatch("parquet_sha256"));
    }
    if stored.split_algorithm_sha256 != split_algorithm_sha256() {
        return Err(binding_mismatch("split_algorithm_sha256"));
    }
    let facts = recompute_split_facts(&config.parquet_path, &config.feature_columns)?;
    if stored.cut_ns != facts.cut_ns {
        return Err(binding_mismatch("cut_ns"));
    }
    if stored.development_member_count != facts.development_member_count {
        return Err(binding_mismatch("development_member_count"));
    }
    if stored.quarantined_non_finite_feature_count != facts.quarantined_non_finite_feature_count {
        return Err(binding_mismatch("quarantined_non_finite_feature_count"));
    }
    if stored.development_member_sha256 != facts.development_member_sha256 {
        return Err(binding_mismatch("development_member_sha256"));
    }
    Ok(())
}

fn binding_mismatch(field: &'static str) -> FormalEntryError {
    FormalEntryError::SplitBindingMismatch { field }
}

#[derive(Debug)]
struct SplitFacts {
    cut_ns: [i64; 4],
    development_member_count: u64,
    development_member_sha256: Sha256Digest,
    quarantined_non_finite_feature_count: u64,
}

fn recompute_split_facts(
    path: &Path,
    feature_columns: &[String],
) -> Result<SplitFacts, FormalEntryError> {
    let mut active_seconds = BTreeSet::new();
    let projected = projected_columns(feature_columns);
    let projected_refs = projected.iter().map(String::as_str).collect::<Vec<_>>();
    let mut quarantined_non_finite_feature_count = 0_u64;
    let mut first_pass_source_row_index = 0_u64;
    for batch in read_projected_batches(path, &projected_refs)? {
        let batch = batch?;
        let columns = UnlabeledBatch::try_new(&batch)?;
        let features = FeatureBatch::try_new(&batch, feature_columns)?;
        for row in 0..batch.num_rows() {
            if features.has_non_finite(row) {
                quarantined_non_finite_feature_count = quarantined_non_finite_feature_count
                    .checked_add(1)
                    .ok_or(FormalEntryError::CountOverflow)?;
                first_pass_source_row_index = first_pass_source_row_index
                    .checked_add(1)
                    .ok_or(FormalEntryError::CountOverflow)?;
                continue;
            }
            if let Some(values) = columns.valid_row(row, first_pass_source_row_index)? {
                active_seconds.insert(values.last_ns.div_euclid(BILLION));
            }
            first_pass_source_row_index = first_pass_source_row_index
                .checked_add(1)
                .ok_or(FormalEntryError::CountOverflow)?;
        }
    }
    let seconds = active_seconds.into_iter().collect::<Vec<_>>();
    let cut_ns = activity_cut_ns(&seconds)?;

    let mut member_hasher = Sha256::new();
    member_hasher.update(b"lspr24-g0-development-members-v1\0");
    let mut development_member_count = 0_u64;
    let mut source_row_index = 0_u64;
    for batch in read_projected_batches(path, &projected_refs)? {
        let batch = batch?;
        let columns = UnlabeledBatch::try_new(&batch)?;
        let features = FeatureBatch::try_new(&batch, feature_columns)?;
        for row in 0..batch.num_rows() {
            if features.has_non_finite(row) {
                source_row_index = source_row_index
                    .checked_add(1)
                    .ok_or(FormalEntryError::CountOverflow)?;
                continue;
            }
            if let Some(values) = columns.valid_row(row, source_row_index)? {
                if values.last_ns < cut_ns[3] {
                    let member = DevelopmentMemberId::new(
                        sha256_bytes(values.flow_id.as_bytes()),
                        source_row_index,
                    );
                    hash_development_member(
                        &mut member_hasher,
                        member,
                        segment_for(values.last_ns, cut_ns),
                    );
                    development_member_count = development_member_count
                        .checked_add(1)
                        .ok_or(FormalEntryError::CountOverflow)?;
                }
            }
            source_row_index = source_row_index
                .checked_add(1)
                .ok_or(FormalEntryError::CountOverflow)?;
        }
    }
    Ok(SplitFacts {
        cut_ns,
        development_member_count,
        development_member_sha256: member_hasher.finalize().into(),
        quarantined_non_finite_feature_count,
    })
}

fn activity_cut_ns(seconds: &[i64]) -> Result<[i64; 4], FormalEntryError> {
    if seconds.is_empty() {
        return Err(FormalEntryError::CutPrecondition);
    }
    let n = seconds.len();
    let ceil_index = |percent: usize| {
        percent
            .checked_mul(n)
            .and_then(|value| value.checked_add(99))
            .map(|value| value / 100)
            .ok_or(FormalEntryError::CountOverflow)
    };
    let b40 = ceil_index(40)?;
    let b50 = ceil_index(50)?;
    let b60 = ceil_index(60)?;
    let b80 = ceil_index(80)?;
    if !(0 < b40 && b40 < b50 && b50 < b60 && b60 < b80 && b80 < n) {
        return Err(FormalEntryError::CutPrecondition);
    }
    Ok([
        seconds[b40]
            .checked_mul(BILLION)
            .ok_or(FormalEntryError::CountOverflow)?,
        seconds[b50]
            .checked_mul(BILLION)
            .ok_or(FormalEntryError::CountOverflow)?,
        seconds[b60]
            .checked_mul(BILLION)
            .ok_or(FormalEntryError::CountOverflow)?,
        seconds[b80]
            .checked_mul(BILLION)
            .ok_or(FormalEntryError::CountOverflow)?,
    ])
}

fn segment_for(last_ns: i64, cut_ns: [i64; 4]) -> DevelopmentSegment {
    if last_ns < cut_ns[0] {
        DevelopmentSegment::First
    } else if last_ns < cut_ns[1] {
        DevelopmentSegment::Second
    } else if last_ns < cut_ns[2] {
        DevelopmentSegment::Third
    } else {
        DevelopmentSegment::Fourth
    }
}

fn hash_development_member(
    hasher: &mut Sha256,
    member: DevelopmentMemberId,
    segment: DevelopmentSegment,
) {
    hasher.update(member.raw_flow_id());
    hasher.update(member.source_row_index().to_be_bytes());
    hasher.update([segment_byte(segment)]);
}

fn segment_byte(segment: DevelopmentSegment) -> u8 {
    match segment {
        DevelopmentSegment::First => 0,
        DevelopmentSegment::Second => 1,
        DevelopmentSegment::Third => 2,
        DevelopmentSegment::Fourth => 3,
    }
}

fn segment_name(segment: DevelopmentSegment) -> &'static str {
    match segment {
        DevelopmentSegment::First => "train-fit",
        DevelopmentSegment::Second => "architecture-selection",
        DevelopmentSegment::Third => "dev-validation",
        DevelopmentSegment::Fourth => "calibration",
    }
}

#[derive(Serialize)]
struct FormalOutputRow {
    segment: &'static str,
    raw_flow_id: String,
    source_row_index: u64,
    label: i32,
    features: BTreeMap<String, f64>,
}

fn write_development_rows(
    config: &FormalDevelopmentConfig,
    stored: &StoredSplitReceipt,
) -> Result<FormalDevelopmentMaterializationReceipt, FormalEntryError> {
    let mut projected = UNLABELED_COLUMNS.iter().map(|value| (*value).to_owned()).collect::<Vec<_>>();
    projected.push("Label".to_owned());
    projected.extend(config.feature_columns.iter().cloned());
    let projected_refs = projected.iter().map(String::as_str).collect::<Vec<_>>();
    let mut output = PartialOutput::create(&config.output_path).map_err(FormalEntryError::Output)?;
    let mut output_hasher = Sha256::new();
    let mut member_hasher = Sha256::new();
    member_hasher.update(b"lspr24-g0-development-members-v1\0");
    let mut development_row_count = 0_u64;
    let mut source_row_index = 0_u64;

    for batch in read_projected_batches(&config.parquet_path, &projected_refs)? {
        let batch = batch?;
        let columns = FormalBatch::try_new(&batch, &config.feature_columns)?;
        for row in 0..batch.num_rows() {
            let last_ns = columns.last_ns(row)?;
            if last_ns.is_some_and(|value| value >= stored.cut_ns[3]) {
                source_row_index = source_row_index
                    .checked_add(1)
                    .ok_or(FormalEntryError::CountOverflow)?;
                continue;
            }
            if columns.has_non_finite(row) {
                source_row_index = source_row_index
                    .checked_add(1)
                    .ok_or(FormalEntryError::CountOverflow)?;
                continue;
            }
            if let Some(values) = columns.unlabeled.valid_row(row, source_row_index)? {
                let member = DevelopmentMemberId::new(
                    sha256_bytes(values.flow_id.as_bytes()),
                    source_row_index,
                );
                let segment = segment_for(values.last_ns, stored.cut_ns);
                hash_development_member(&mut member_hasher, member, segment);
                let label = columns.label(row).ok_or(
                    FormalEntryError::InvalidDevelopmentLabel { source_row_index },
                )?;
                if !matches!(label, 0 | 1) {
                    return Err(FormalEntryError::InvalidDevelopmentLabel {
                        source_row_index,
                    });
                }
                let row = FormalOutputRow {
                    segment: segment_name(segment),
                    raw_flow_id: encode_hex(&member.raw_flow_id()),
                    source_row_index,
                    label,
                    features: columns.features(row)?,
                };
                let mut bytes = serde_json::to_vec(&row)
                    .map_err(|error| FormalEntryError::Serialization(error.to_string()))?;
                bytes.push(b'\n');
                output.write_all(&bytes).map_err(FormalEntryError::Output)?;
                output_hasher.update(&bytes);
                development_row_count = development_row_count
                    .checked_add(1)
                    .ok_or(FormalEntryError::CountOverflow)?;
            }
            source_row_index = source_row_index
                .checked_add(1)
                .ok_or(FormalEntryError::CountOverflow)?;
        }
    }

    let member_sha256: Sha256Digest = member_hasher.finalize().into();
    if development_row_count != stored.development_member_count
        || member_sha256 != stored.development_member_sha256
    {
        return Err(binding_mismatch("second_pass_development_members"));
    }
    let output_path = output.commit().map_err(FormalEntryError::Output)?;
    Ok(FormalDevelopmentMaterializationReceipt {
        output_path,
        development_row_count,
        development_semantic_sha256: output_hasher.finalize().into(),
        split_receipt_sha256: [0; 32],
        quarantined_non_finite_feature_count: stored.quarantined_non_finite_feature_count,
    })
}

fn projected_columns(feature_columns: &[String]) -> Vec<String> {
    let mut projected = UNLABELED_COLUMNS
        .iter()
        .map(|value| (*value).to_owned())
        .collect::<Vec<_>>();
    projected.extend(feature_columns.iter().cloned());
    projected
}

struct ValidUnlabeledRow<'a> {
    last_ns: i64,
    flow_id: &'a str,
}

struct UnlabeledBatch {
    start: Int64Array,
    last: Int64Array,
    src_ip: StringArray,
    dst_ip: StringArray,
    external_src: StringArray,
    external_dst: StringArray,
    src_port: Int32Array,
    dst_port: Int32Array,
    protocol: Int32Array,
    flow_id: StringArray,
}

impl UnlabeledBatch {
    fn try_new(batch: &RecordBatch) -> Result<Self, FormalEntryError> {
        Ok(Self {
            start: int64_column(batch, "mTimestampStart")?,
            last: int64_column(batch, "mTimestampLast")?,
            src_ip: string_column(batch, "SrcIP")?,
            dst_ip: string_column(batch, "DstIP")?,
            external_src: string_column(batch, "External_src")?,
            external_dst: string_column(batch, "External_dst")?,
            src_port: int32_column(batch, "SrcPort")?,
            dst_port: int32_column(batch, "DstPort")?,
            protocol: int32_column(batch, "Protocol")?,
            flow_id: string_column(batch, "Flow ID")?,
        })
    }

    fn valid_row(
        &self,
        row: usize,
        source_row_index: u64,
    ) -> Result<Option<ValidUnlabeledRow<'_>>, FormalEntryError> {
        if self.start.is_null(row)
            || self.last.is_null(row)
            || self.src_ip.is_null(row)
            || self.dst_ip.is_null(row)
            || self.src_port.is_null(row)
            || self.dst_port.is_null(row)
            || self.protocol.is_null(row)
            || self.flow_id.is_null(row)
        {
            return Ok(None);
        }
        let start_ns = timestamp_ns(self.start.value(row))?;
        let last_ns = timestamp_ns(self.last.value(row))?;
        let src_port = self.src_port.value(row);
        let dst_port = self.dst_port.value(row);
        let protocol = self.protocol.value(row);
        let src_ip = self.src_ip.value(row);
        let dst_ip = self.dst_ip.value(row);
        let flow_id = self.flow_id.value(row);
        let external_src = parse_external_marker(
            (!self.external_src.is_null(row)).then(|| self.external_src.value(row)),
            "External_src",
            source_row_index,
        )
        .map_err(FormalEntryError::Screen)?;
        let external_dst = parse_external_marker(
            (!self.external_dst.is_null(row)).then(|| self.external_dst.value(row)),
            "External_dst",
            source_row_index,
        )
        .map_err(FormalEntryError::Screen)?;
        if start_ns > last_ns
            || !(0..=65_535).contains(&src_port)
            || !(0..=65_535).contains(&dst_port)
            || !(0..=255).contains(&protocol)
            || (external_src && external_dst)
            || flow_id.is_empty()
        {
            return Ok(None);
        }
        resolve_protected_endpoints(
            Some(src_ip),
            Some(dst_ip),
            Some(if external_src { "1" } else { "0" }),
            Some(if external_dst { "1" } else { "0" }),
            source_row_index,
        )
        .map_err(FormalEntryError::Screen)?;
        Ok(Some(ValidUnlabeledRow { last_ns, flow_id }))
    }
}

struct FeatureBatch<'a> {
    features: Vec<(String, NumericColumn<'a>)>,
}

impl<'a> FeatureBatch<'a> {
    fn try_new(batch: &'a RecordBatch, feature_columns: &[String]) -> Result<Self, FormalEntryError> {
        let features = feature_columns
            .iter()
            .map(|column| Ok((column.clone(), numeric_column(batch, column)?)))
            .collect::<Result<Vec<_>, FormalEntryError>>()?;
        Ok(Self { features })
    }

    fn has_non_finite(&self, row: usize) -> bool {
        self.features
            .iter()
            .any(|(_, values)| values.is_non_finite(row))
    }
}

struct FormalBatch<'a> {
    unlabeled: UnlabeledBatch,
    label: Int32Array,
    features: FeatureBatch<'a>,
}

impl<'a> FormalBatch<'a> {
    fn try_new(batch: &'a RecordBatch, feature_columns: &[String]) -> Result<Self, FormalEntryError> {
        Ok(Self {
            unlabeled: UnlabeledBatch::try_new(batch)?,
            label: int32_column(batch, "Label")?,
            features: FeatureBatch::try_new(batch, feature_columns)?,
        })
    }

    fn last_ns(&self, row: usize) -> Result<Option<i64>, FormalEntryError> {
        (!self.unlabeled.last.is_null(row))
            .then(|| timestamp_ns(self.unlabeled.last.value(row)))
            .transpose()
    }

    fn label(&self, row: usize) -> Option<i32> {
        (!self.label.is_null(row)).then(|| self.label.value(row))
    }

    fn has_non_finite(&self, row: usize) -> bool {
        self.features.has_non_finite(row)
    }

    fn features(&self, row: usize) -> Result<BTreeMap<String, f64>, FormalEntryError> {
        self.features
            .features
            .iter()
            .map(|(name, values)| {
                values
                    .value_as_f64(row)
                    .map(|value| (name.clone(), value))
                    .ok_or_else(|| FormalEntryError::MissingDevelopmentFeature {
                        column: name.clone(),
                    })
            })
            .collect()
    }
}

type BatchIterator = Box<dyn Iterator<Item = Result<RecordBatch, FormalEntryError>>>;

fn read_projected_batches(path: &Path, columns: &[&str]) -> Result<BatchIterator, FormalEntryError> {
    let file = File::open(path).map_err(|source| FormalEntryError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    let builder = ParquetRecordBatchReaderBuilder::try_new(file)
        .map_err(|error| FormalEntryError::Parquet(error.to_string()))?;
    let indices = required_indices(builder.schema(), columns)?;
    let projection = ProjectionMask::roots(builder.parquet_schema(), indices);
    let reader = builder
        .with_projection(projection)
        .with_batch_size(65_536)
        .build()
        .map_err(|error| FormalEntryError::Parquet(error.to_string()))?;
    Ok(Box::new(reader.map(|batch| {
        batch.map_err(|error| FormalEntryError::Parquet(error.to_string()))
    })))
}

fn required_indices(schema: &Schema, columns: &[&str]) -> Result<Vec<usize>, FormalEntryError> {
    columns
        .iter()
        .map(|column| {
            schema
                .fields()
                .iter()
                .position(|field| field.name() == *column)
                .ok_or_else(|| FormalEntryError::Schema(format!("缺少列 {column}")))
        })
        .collect()
}

fn typed_column<T: Array + Clone + 'static>(
    batch: &RecordBatch,
    column: &str,
    expected: DataType,
) -> Result<T, FormalEntryError> {
    let index = batch
        .schema()
        .fields()
        .iter()
        .position(|field| field.name() == column)
        .ok_or_else(|| FormalEntryError::Schema(format!("缺少投影列 {column}")))?;
    batch
        .column(index)
        .as_any()
        .downcast_ref::<T>()
        .cloned()
        .ok_or_else(|| FormalEntryError::Schema(format!("列 {column} 必须为 {expected}")))
}

fn int64_column(batch: &RecordBatch, column: &str) -> Result<Int64Array, FormalEntryError> {
    typed_column(batch, column, DataType::Int64)
}

fn int32_column(batch: &RecordBatch, column: &str) -> Result<Int32Array, FormalEntryError> {
    typed_column(batch, column, DataType::Int32)
}

fn string_column(batch: &RecordBatch, column: &str) -> Result<StringArray, FormalEntryError> {
    typed_column(batch, column, DataType::Utf8)
}

fn numeric_column<'a>(
    batch: &'a RecordBatch,
    column: &str,
) -> Result<NumericColumn<'a>, FormalEntryError> {
    let index = batch
        .schema()
        .fields()
        .iter()
        .position(|field| field.name() == column)
        .ok_or_else(|| FormalEntryError::Schema(format!("缺少投影列 {column}")))?;
    NumericColumn::try_new(column, batch.column(index).as_ref()).map_err(FormalEntryError::Screen)
}

fn timestamp_ns(value: i64) -> Result<i64, FormalEntryError> {
    utc_ns_from_micros(value).map_err(FormalEntryError::Screen)
}

fn stored_receipt_sha256(stored: &StoredSplitReceipt) -> Result<Sha256Digest, FormalEntryError> {
    let mut value = serde_json::to_value(stored)
        .map_err(|error| FormalEntryError::Receipt(error.to_string()))?;
    value
        .as_object_mut()
        .ok_or_else(|| FormalEntryError::Receipt("切分收据顶层不是对象".to_owned()))?
        .remove("receipt_sha256");
    let bytes = serde_json::to_vec(&value)
        .map_err(|error| FormalEntryError::Receipt(error.to_string()))?;
    Ok(sha256_bytes(&bytes))
}

fn split_algorithm_sha256() -> Sha256Digest {
    sha256_bytes(SPLIT_ALGORITHM_SPEC)
}

fn file_sha256(path: &Path) -> Result<Sha256Digest, FormalEntryError> {
    let mut file = File::open(path).map_err(|source| FormalEntryError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let read = file.read(&mut buffer).map_err(|source| FormalEntryError::Io {
            path: path.to_path_buf(),
            source,
        })?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(hasher.finalize().into())
}

fn sha256_bytes(bytes: &[u8]) -> Sha256Digest {
    Sha256::digest(bytes).into()
}

fn forbidden_feature_column(column: &str) -> bool {
    UNLABELED_COLUMNS.contains(&column)
        || column == "Label"
        || column.starts_with("Label_")
        || column.contains("IDS")
        || column.contains("IP")
        || column.contains("Port")
        || column.contains("Timestamp")
        || column == "Service"
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

/// 正式 Parquet 入口失败。
#[derive(Debug)]
pub enum FormalEntryError {
    Config(String),
    Io { path: PathBuf, source: io::Error },
    Parquet(String),
    Schema(String),
    Screen(ScreenSourceError),
    CutPrecondition,
    CountOverflow,
    Receipt(String),
    ReceiptHashMismatch,
    SplitBindingMismatch { field: &'static str },
    InvalidDevelopmentLabel { source_row_index: u64 },
    MissingDevelopmentFeature { column: String },
    Serialization(String),
    Output(OutputError),
}

impl Display for FormalEntryError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Config(message) => write!(formatter, "正式开发配置错误：{message}"),
            Self::Io { path, source } => write!(formatter, "读取 {} 失败：{source}", path.display()),
            Self::Parquet(message) => write!(formatter, "Parquet 读取失败：{message}"),
            Self::Schema(message) => write!(formatter, "Parquet 模式错误：{message}"),
            Self::Screen(error) => write!(formatter, "真实源行错误：{error}"),
            Self::CutPrecondition => formatter.write_str("活动秒切点前置条件不成立"),
            Self::CountOverflow => formatter.write_str("正式开发计数溢出"),
            Self::Receipt(message) => write!(formatter, "切分收据错误：{message}"),
            Self::ReceiptHashMismatch => formatter.write_str("切分收据自哈希不匹配"),
            Self::SplitBindingMismatch { field } => write!(formatter, "切分收据绑定不匹配：{field}"),
            Self::InvalidDevelopmentLabel { source_row_index } => {
                write!(formatter, "开发标签非法：源行 {source_row_index}")
            }
            Self::MissingDevelopmentFeature { column } => {
                write!(formatter, "开发特征缺失：{column}")
            }
            Self::Serialization(message) => write!(formatter, "开发输出序列化失败：{message}"),
            Self::Output(error) => write!(formatter, "正式开发输出失败：{error}"),
        }
    }
}

impl Error for FormalEntryError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Io { source, .. } => Some(source),
            Self::Output(error) => Some(error),
            Self::Screen(error) => Some(error),
            _ => None,
        }
    }
}

mod hex_digest {
    use serde::de::Error as DeserializeError;
    use serde::{Deserialize, Deserializer, Serializer};

    use crate::Sha256Digest;

    pub fn serialize<S>(digest: &Sha256Digest, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let encoded = digest.iter().map(|byte| format!("{byte:02x}")).collect::<String>();
        serializer.serialize_str(&encoded)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<Sha256Digest, D::Error>
    where
        D: Deserializer<'de>,
    {
        let encoded = String::deserialize(deserializer)?;
        if encoded.len() != 64 || !encoded.bytes().all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase()) {
            return Err(D::Error::custom("SHA-256 必须为 64 位小写十六进制"));
        }
        let mut digest = [0_u8; 32];
        for (index, byte) in digest.iter_mut().enumerate() {
            *byte = u8::from_str_radix(&encoded[index * 2..index * 2 + 2], 16)
                .map_err(D::Error::custom)?;
        }
        Ok(digest)
    }
}
