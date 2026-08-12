//! 字段清单的确定性 JSON 文档与排他发布。

use std::path::Path;

use serde::Serialize;

use crate::canonical::sha256;
use crate::schema_audit::write_exclusive;
use crate::types::Sha256Digest;

use super::{
    CONN_STATE_FALLBACK_BUCKET, CONN_STATE_VOCABULARY, FIELD_MANIFEST_REQUIRED_KEYS,
    FORBIDDEN_SOURCE_COLUMNS, FieldManifestEntry, FieldManifestError, WINDOW_AGG_FORMULA_VERSION,
};

/// 字段清单文档的冻结版本串。
pub const FIELD_MANIFEST_VERSION: &str = "lspr24-field-manifest-v1";

const STATISTIC_PARQUET_TYPE: &str = "Decimal128(38,12)";
const COUNT_PARQUET_TYPE: &str = "Int64";
const MASK_PARQUET_TYPE: &str = "Int8";

#[derive(Debug, Serialize)]
struct OutputPhysicalTypes {
    statistic: &'static str,
    count: &'static str,
    mask: &'static str,
}

#[derive(Debug, Serialize)]
struct FieldManifestDocument<'a> {
    manifest_version: &'static str,
    formula_version: &'static str,
    entry_count: usize,
    generation_target_count: usize,
    required_entry_keys: [&'static str; 14],
    /// 本版本窗口内分位数聚合器为空集；扩展需要新的清单版本。
    quantile_aggregators: [&'static str; 0],
    conn_state_vocabulary: [&'static str; 13],
    conn_state_fallback_bucket: &'static str,
    forbidden_source_columns: [&'static str; 21],
    output_physical_types: OutputPhysicalTypes,
    entries: &'a [FieldManifestEntry],
}

/// 序列化字段清单为逐字节稳定的 JSON 文档。
///
/// # Errors
///
/// JSON 序列化失败时返回错误。
pub fn field_manifest_json_bytes(
    entries: &[FieldManifestEntry],
) -> Result<Vec<u8>, FieldManifestError> {
    let generation_target_count = entries
        .iter()
        .filter(|entry| entry.generation_target)
        .count();
    let document = FieldManifestDocument {
        manifest_version: FIELD_MANIFEST_VERSION,
        formula_version: WINDOW_AGG_FORMULA_VERSION,
        entry_count: entries.len(),
        generation_target_count,
        required_entry_keys: FIELD_MANIFEST_REQUIRED_KEYS,
        quantile_aggregators: [],
        conn_state_vocabulary: CONN_STATE_VOCABULARY,
        conn_state_fallback_bucket: CONN_STATE_FALLBACK_BUCKET,
        forbidden_source_columns: FORBIDDEN_SOURCE_COLUMNS,
        output_physical_types: OutputPhysicalTypes {
            statistic: STATISTIC_PARQUET_TYPE,
            count: COUNT_PARQUET_TYPE,
            mask: MASK_PARQUET_TYPE,
        },
        entries,
    };
    let mut bytes = serde_json::to_vec_pretty(&document).map_err(FieldManifestError::Json)?;
    bytes.push(b'\n');
    Ok(bytes)
}

/// 以排他发布语义写出字段清单 JSON，返回文件内容的 SHA-256。
///
/// # Errors
///
/// 序列化或排他发布失败时返回错误。
pub fn write_field_manifest_json(
    entries: &[FieldManifestEntry],
    out: impl AsRef<Path>,
) -> Result<Sha256Digest, FieldManifestError> {
    let bytes = field_manifest_json_bytes(entries)?;
    write_exclusive(out.as_ref(), &bytes).map_err(FieldManifestError::Output)?;
    Ok(sha256(&bytes))
}
