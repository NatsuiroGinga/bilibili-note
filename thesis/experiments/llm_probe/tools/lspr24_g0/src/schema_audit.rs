//! LSPR24 冻结模式的页脚级审计与去重内容投影清单。
//!
//! 本模块只读取 Parquet 页脚元数据（列名、Arrow 类型、行数、行组数），
//! 绝不构造数据页读取器，也绝不读取任何数据行。

use std::collections::BTreeSet;
use std::error::Error;
use std::fmt::{Display, Formatter};
use std::fs::File;
use std::path::{Path, PathBuf};

use arrow_schema::DataType;
use parquet::arrow::arrow_reader::{ArrowReaderMetadata, ArrowReaderOptions};
use parquet::errors::ParquetError;
use serde::{Deserialize, Serialize};

use crate::canonical::{CanonicalError, CanonicalValue, sha256, tuple_encode};
use crate::output::{OutputError, PartialOutput};
use crate::types::Sha256Digest;

/// 模式审计文档的冻结版本串。
pub const SCHEMA_AUDIT_VERSION: &str = "lspr24-schema-audit-v1";
/// 去重投影清单文档的冻结版本串。
pub const DEDUP_PROJECTION_MANIFEST_VERSION: &str = "lspr24-dedup-projection-v1";
/// 冻结输入 `lspr24_v2.parquet` 的列数。
pub const LSPR24_EXPECTED_COLUMN_COUNT: usize = 101;
/// 冻结输入 `lspr24_v2.parquet` 的行数。
pub const LSPR24_EXPECTED_ROW_COUNT: u64 = 20_227_356;
/// 不在冻结映射内的 Arrow 类型占位名，任何审计都必须拒绝它。
pub const UNSUPPORTED_ARROW_TYPE: &str = "<unsupported>";

/// 合同 §6.2 的标签列，禁止进入去重内容投影。
pub const LABEL_COLUMNS: [&str; 3] = ["Label", "Label_dst", "Label_src"];
/// 合同 §6.2 的 IDS 告警列，禁止进入去重内容投影。
pub const IDS_ALERT_COLUMNS: [&str; 4] =
    ["Anomaly_event", "Category", "Severity", "SigID revision"];

const LABEL_EXCLUSION_REASON: &str = "label-column-forbidden-by-contract-6.2";
const IDS_EXCLUSION_REASON: &str = "ids-alert-column-forbidden-by-contract-6.2";

/// 页脚审计中的一列。
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuditedColumn {
    /// 零基源列序号。
    pub index: usize,
    /// 精确源列名，不做裁剪或大小写规范化。
    pub name: String,
    /// 冻结的 Arrow 类型名。
    pub arrow_type: String,
    /// 源模式声明的可空性。
    pub nullable: bool,
}

impl AuditedColumn {
    /// 创建一列审计记录。
    #[must_use]
    pub const fn new(index: usize, name: String, arrow_type: String, nullable: bool) -> Self {
        Self {
            index,
            name,
            arrow_type,
            nullable,
        }
    }
}

/// 去重内容投影中被剔除的一列及其原因。
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExcludedColumn {
    /// 零基源列序号。
    pub index: usize,
    /// 精确源列名。
    pub name: String,
    /// 冻结的 Arrow 类型名。
    pub arrow_type: String,
    /// 剔除原因标识。
    pub reason: String,
}

/// 模式审计失败。
#[derive(Debug)]
pub enum SchemaAuditError {
    /// 无法打开输入文件。
    OpenInput {
        /// 输入路径。
        path: PathBuf,
        /// 底层输入输出错误。
        source: std::io::Error,
    },
    /// 无法读取 Parquet 页脚元数据。
    ReadMetadata(ParquetError),
    /// Parquet 页脚声明了负行数。
    NegativeRowCount {
        /// 页脚原始值。
        actual: i64,
    },
    /// 列数与冻结值不一致。
    UnexpectedColumnCount {
        /// 冻结列数。
        expected: usize,
        /// 实际列数。
        actual: usize,
    },
    /// 行数与冻结值不一致。
    UnexpectedRowCount {
        /// 冻结行数。
        expected: u64,
        /// 实际行数。
        actual: u64,
    },
    /// 列清单为空。
    EmptyColumnCatalog,
    /// 列序号不是从零开始的连续序列。
    ColumnIndexOutOfOrder {
        /// 期望序号。
        expected: usize,
        /// 实际序号。
        actual: usize,
    },
    /// 列名为空。
    EmptyColumnName {
        /// 出问题的列序号。
        index: usize,
    },
    /// 列名重复。
    DuplicateColumnName {
        /// 重复的列名。
        name: String,
    },
    /// Arrow 类型不在冻结映射内。
    UnsupportedArrowType {
        /// 列名。
        name: String,
    },
    /// 文档版本串与冻结值不一致。
    UnexpectedAuditVersion {
        /// 冻结版本串。
        expected: &'static str,
        /// 实际版本串。
        actual: String,
    },
    /// 文档声明的列数与列清单长度不一致。
    ColumnCountFieldMismatch {
        /// 文档声明值。
        declared: usize,
        /// 列清单长度。
        actual: usize,
    },
    /// 文档声明的 `schema_sha256` 与按列清单复算值不一致。
    SchemaHashMismatch {
        /// 按列清单复算的十六进制摘要。
        expected: String,
        /// 文档声明的十六进制摘要。
        actual: String,
    },
    /// 规范元组编码失败。
    Canonical(CanonicalError),
    /// JSON 序列化或解析失败。
    Json(serde_json::Error),
    /// 排他输出发布失败。
    Output(OutputError),
}

impl Display for SchemaAuditError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::OpenInput { path, .. } => {
                write!(formatter, "无法打开 Parquet 输入 {}", path.display())
            }
            Self::ReadMetadata(_) => write!(formatter, "无法读取 Parquet 页脚元数据"),
            Self::NegativeRowCount { actual } => {
                write!(formatter, "Parquet 页脚行数不能为负数：{actual}")
            }
            Self::UnexpectedColumnCount { expected, actual } => write!(
                formatter,
                "列数与冻结值不一致：期望 {expected}，实际 {actual}"
            ),
            Self::UnexpectedRowCount { expected, actual } => write!(
                formatter,
                "行数与冻结值不一致：期望 {expected}，实际 {actual}"
            ),
            Self::EmptyColumnCatalog => write!(formatter, "列清单不得为空"),
            Self::ColumnIndexOutOfOrder { expected, actual } => write!(
                formatter,
                "列序号必须是从零开始的连续序列：期望 {expected}，实际 {actual}"
            ),
            Self::EmptyColumnName { index } => {
                write!(formatter, "第 {index} 列的列名为空")
            }
            Self::DuplicateColumnName { name } => write!(formatter, "列名重复：{name}"),
            Self::UnsupportedArrowType { name } => {
                write!(formatter, "列 {name} 的 Arrow 类型不在冻结映射内")
            }
            Self::UnexpectedAuditVersion { expected, actual } => write!(
                formatter,
                "模式审计版本串不一致：期望 {expected}，实际 {actual}"
            ),
            Self::ColumnCountFieldMismatch { declared, actual } => write!(
                formatter,
                "文档声明列数 {declared} 与列清单长度 {actual} 不一致"
            ),
            Self::SchemaHashMismatch { expected, actual } => write!(
                formatter,
                "schema_sha256 复算不一致：期望 {expected}，实际 {actual}"
            ),
            Self::Canonical(error) => write!(formatter, "规范元组编码失败：{error}"),
            Self::Json(error) => write!(formatter, "模式审计 JSON 处理失败：{error}"),
            Self::Output(error) => write!(formatter, "模式审计输出发布失败：{error}"),
        }
    }
}

impl Error for SchemaAuditError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::OpenInput { source, .. } => Some(source),
            Self::ReadMetadata(source) => Some(source),
            Self::Canonical(source) => Some(source),
            Self::Json(source) => Some(source),
            Self::Output(source) => Some(source),
            _ => None,
        }
    }
}

/// 返回 Arrow 类型的冻结名称；不在冻结映射内时返回 [`UNSUPPORTED_ARROW_TYPE`]。
#[must_use]
pub fn arrow_type_name(data_type: &DataType) -> &'static str {
    match data_type {
        DataType::Boolean => "Boolean",
        DataType::Int8 => "Int8",
        DataType::Int16 => "Int16",
        DataType::Int32 => "Int32",
        DataType::Int64 => "Int64",
        DataType::UInt8 => "UInt8",
        DataType::UInt16 => "UInt16",
        DataType::UInt32 => "UInt32",
        DataType::UInt64 => "UInt64",
        DataType::Float32 => "Float32",
        DataType::Float64 => "Float64",
        DataType::Utf8 => "Utf8",
        DataType::LargeUtf8 => "LargeUtf8",
        DataType::Binary => "Binary",
        DataType::LargeBinary => "LargeBinary",
        _ => UNSUPPORTED_ARROW_TYPE,
    }
}

/// 冻结输入的页脚级模式审计。
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SchemaAudit {
    source_file_name: String,
    row_count: u64,
    row_group_count: usize,
    columns: Vec<AuditedColumn>,
    schema_sha256: Sha256Digest,
}

#[derive(Debug, Serialize, Deserialize)]
struct SchemaAuditDocument {
    audit_version: String,
    source_file_name: String,
    row_count: u64,
    row_group_count: usize,
    column_count: usize,
    schema_sha256: String,
    columns: Vec<AuditedColumn>,
}

impl SchemaAudit {
    /// 只读 Parquet 页脚构造审计，并核对列数与行数等于冻结值。
    ///
    /// 本函数不构造任何数据页读取器，因此不会读取数据行。
    ///
    /// # Errors
    ///
    /// 文件不可读、页脚不可解析、列数或行数与冻结值不一致，或存在冻结映射外的
    /// Arrow 类型时返回错误。
    pub fn from_parquet_footer(path: impl AsRef<Path>) -> Result<Self, SchemaAuditError> {
        let path = path.as_ref();
        let file = File::open(path).map_err(|source| SchemaAuditError::OpenInput {
            path: path.to_path_buf(),
            source,
        })?;
        let metadata = ArrowReaderMetadata::load(&file, ArrowReaderOptions::new())
            .map_err(SchemaAuditError::ReadMetadata)?;

        let schema = metadata.schema();
        let actual_columns = schema.fields().len();
        if actual_columns != LSPR24_EXPECTED_COLUMN_COUNT {
            return Err(SchemaAuditError::UnexpectedColumnCount {
                expected: LSPR24_EXPECTED_COLUMN_COUNT,
                actual: actual_columns,
            });
        }

        let declared_rows = metadata.metadata().file_metadata().num_rows();
        let row_count =
            u64::try_from(declared_rows).map_err(|_| SchemaAuditError::NegativeRowCount {
                actual: declared_rows,
            })?;
        if row_count != LSPR24_EXPECTED_ROW_COUNT {
            return Err(SchemaAuditError::UnexpectedRowCount {
                expected: LSPR24_EXPECTED_ROW_COUNT,
                actual: row_count,
            });
        }

        let mut columns = Vec::with_capacity(actual_columns);
        for (index, field) in schema.fields().iter().enumerate() {
            columns.push(AuditedColumn::new(
                index,
                field.name().clone(),
                arrow_type_name(field.data_type()).to_owned(),
                field.is_nullable(),
            ));
        }

        let source_file_name = path.file_name().map_or_else(
            || path.display().to_string(),
            |name| name.to_string_lossy().into_owned(),
        );
        Self::from_columns(
            source_file_name,
            row_count,
            metadata.metadata().num_row_groups(),
            columns,
        )
    }

    /// 从已验证的列清单构造审计。
    ///
    /// # Errors
    ///
    /// 列清单为空、列序号不连续、列名为空或重复、Arrow 类型不在冻结映射内，
    /// 或规范元组编码失败时返回错误。
    pub fn from_columns(
        source_file_name: String,
        row_count: u64,
        row_group_count: usize,
        columns: Vec<AuditedColumn>,
    ) -> Result<Self, SchemaAuditError> {
        if columns.is_empty() {
            return Err(SchemaAuditError::EmptyColumnCatalog);
        }
        let mut seen: BTreeSet<&str> = BTreeSet::new();
        for (expected, column) in columns.iter().enumerate() {
            if column.index != expected {
                return Err(SchemaAuditError::ColumnIndexOutOfOrder {
                    expected,
                    actual: column.index,
                });
            }
            if column.name.is_empty() {
                return Err(SchemaAuditError::EmptyColumnName { index: expected });
            }
            if column.arrow_type.is_empty() || column.arrow_type == UNSUPPORTED_ARROW_TYPE {
                return Err(SchemaAuditError::UnsupportedArrowType {
                    name: column.name.clone(),
                });
            }
            if !seen.insert(column.name.as_str()) {
                return Err(SchemaAuditError::DuplicateColumnName {
                    name: column.name.clone(),
                });
            }
        }

        let schema_sha256 = compute_schema_sha256(&columns)?;
        Ok(Self {
            source_file_name,
            row_count,
            row_group_count,
            columns,
            schema_sha256,
        })
    }

    /// 返回源文件名。
    #[must_use]
    pub fn source_file_name(&self) -> &str {
        &self.source_file_name
    }

    /// 返回页脚声明的行数。
    #[must_use]
    pub const fn row_count(&self) -> u64 {
        self.row_count
    }

    /// 返回页脚声明的行组数。
    #[must_use]
    pub const fn row_group_count(&self) -> usize {
        self.row_group_count
    }

    /// 返回按源列序排列的列清单。
    #[must_use]
    pub fn columns(&self) -> &[AuditedColumn] {
        &self.columns
    }

    /// 返回指定列的冻结 Arrow 类型名。
    #[must_use]
    pub fn arrow_type_of(&self, name: &str) -> Option<&str> {
        self.columns
            .iter()
            .find(|column| column.name == name)
            .map(|column| column.arrow_type.as_str())
    }

    /// 返回 `sha256(tuple_encode([Utf8(列名), Utf8(类型名)] 逐列展开))`。
    #[must_use]
    pub const fn schema_sha256(&self) -> Sha256Digest {
        self.schema_sha256
    }

    /// 返回剔除标签与 IDS 告警列后的去重内容投影清单。
    #[must_use]
    pub fn dedup_projection_manifest(&self) -> DedupProjectionManifest {
        let mut content_columns = Vec::with_capacity(self.columns.len());
        let mut excluded_columns = Vec::new();
        for column in &self.columns {
            let reason = if LABEL_COLUMNS.contains(&column.name.as_str()) {
                Some(LABEL_EXCLUSION_REASON)
            } else if IDS_ALERT_COLUMNS.contains(&column.name.as_str()) {
                Some(IDS_EXCLUSION_REASON)
            } else {
                None
            };
            match reason {
                Some(reason) => excluded_columns.push(ExcludedColumn {
                    index: column.index,
                    name: column.name.clone(),
                    arrow_type: column.arrow_type.clone(),
                    reason: reason.to_owned(),
                }),
                None => content_columns.push(column.clone()),
            }
        }

        DedupProjectionManifest {
            manifest_version: DEDUP_PROJECTION_MANIFEST_VERSION.to_owned(),
            source_file_name: self.source_file_name.clone(),
            schema_sha256: encode_hex(&self.schema_sha256),
            content_column_count: content_columns.len(),
            content_columns,
            excluded_columns,
        }
    }

    /// 序列化为确定性 JSON 文档。
    ///
    /// # Errors
    ///
    /// JSON 序列化失败时返回错误。
    pub fn to_json_bytes(&self) -> Result<Vec<u8>, SchemaAuditError> {
        let document = SchemaAuditDocument {
            audit_version: SCHEMA_AUDIT_VERSION.to_owned(),
            source_file_name: self.source_file_name.clone(),
            row_count: self.row_count,
            row_group_count: self.row_group_count,
            column_count: self.columns.len(),
            schema_sha256: encode_hex(&self.schema_sha256),
            columns: self.columns.clone(),
        };
        let mut bytes = serde_json::to_vec_pretty(&document).map_err(SchemaAuditError::Json)?;
        bytes.push(b'\n');
        Ok(bytes)
    }

    /// 解析 JSON 文档并复算 `schema_sha256`。
    ///
    /// # Errors
    ///
    /// JSON 不可解析、版本串不一致、声明列数不一致、`schema_sha256` 复算不一致，
    /// 或列清单本身不合法时返回错误。
    pub fn from_json(bytes: &[u8]) -> Result<Self, SchemaAuditError> {
        let document: SchemaAuditDocument =
            serde_json::from_slice(bytes).map_err(SchemaAuditError::Json)?;
        if document.audit_version != SCHEMA_AUDIT_VERSION {
            return Err(SchemaAuditError::UnexpectedAuditVersion {
                expected: SCHEMA_AUDIT_VERSION,
                actual: document.audit_version,
            });
        }
        if document.column_count != document.columns.len() {
            return Err(SchemaAuditError::ColumnCountFieldMismatch {
                declared: document.column_count,
                actual: document.columns.len(),
            });
        }

        let audit = Self::from_columns(
            document.source_file_name,
            document.row_count,
            document.row_group_count,
            document.columns,
        )?;
        let recomputed = encode_hex(&audit.schema_sha256);
        if recomputed != document.schema_sha256 {
            return Err(SchemaAuditError::SchemaHashMismatch {
                expected: recomputed,
                actual: document.schema_sha256,
            });
        }
        Ok(audit)
    }

    /// 以排他发布语义写出模式审计 JSON，返回文件内容的 SHA-256。
    ///
    /// # Errors
    ///
    /// 序列化或排他发布失败时返回错误。
    pub fn write_json(&self, path: impl AsRef<Path>) -> Result<Sha256Digest, SchemaAuditError> {
        let bytes = self.to_json_bytes()?;
        write_exclusive(path.as_ref(), &bytes).map_err(SchemaAuditError::Output)?;
        Ok(sha256(&bytes))
    }
}

/// 去重内容投影清单：逐列冻结参与 `content_digest` 的源列。
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DedupProjectionManifest {
    manifest_version: String,
    source_file_name: String,
    schema_sha256: String,
    content_column_count: usize,
    content_columns: Vec<AuditedColumn>,
    excluded_columns: Vec<ExcludedColumn>,
}

impl DedupProjectionManifest {
    /// 返回按源列序排列的内容投影列。
    #[must_use]
    pub fn content_columns(&self) -> &[AuditedColumn] {
        &self.content_columns
    }

    /// 返回被剔除的列及其原因。
    #[must_use]
    pub fn excluded_columns(&self) -> &[ExcludedColumn] {
        &self.excluded_columns
    }

    /// 序列化为确定性 JSON 文档。
    ///
    /// # Errors
    ///
    /// JSON 序列化失败时返回错误。
    pub fn to_json_bytes(&self) -> Result<Vec<u8>, SchemaAuditError> {
        let mut bytes = serde_json::to_vec_pretty(self).map_err(SchemaAuditError::Json)?;
        bytes.push(b'\n');
        Ok(bytes)
    }

    /// 以排他发布语义写出投影清单 JSON，返回文件内容的 SHA-256。
    ///
    /// # Errors
    ///
    /// 序列化或排他发布失败时返回错误。
    pub fn write_json(&self, path: impl AsRef<Path>) -> Result<Sha256Digest, SchemaAuditError> {
        let bytes = self.to_json_bytes()?;
        write_exclusive(path.as_ref(), &bytes).map_err(SchemaAuditError::Output)?;
        Ok(sha256(&bytes))
    }
}

/// 以排他发布语义写出字节。
pub(crate) fn write_exclusive(path: &Path, bytes: &[u8]) -> Result<(), OutputError> {
    let mut output = PartialOutput::create(path)?;
    output.write_all(bytes)?;
    output.commit()?;
    Ok(())
}

/// 把摘要编码为小写十六进制。
#[must_use]
pub(crate) fn encode_hex(bytes: &[u8]) -> String {
    let mut text = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        text.push_str(&format!("{byte:02x}"));
    }
    text
}

fn compute_schema_sha256(columns: &[AuditedColumn]) -> Result<Sha256Digest, SchemaAuditError> {
    let mut values = Vec::with_capacity(columns.len() * 2);
    for column in columns {
        values.push(CanonicalValue::Utf8(column.name.as_str()));
        values.push(CanonicalValue::Utf8(column.arrow_type.as_str()));
    }
    let encoded = tuple_encode(&values).map_err(SchemaAuditError::Canonical)?;
    Ok(sha256(&encoded))
}
