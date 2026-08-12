use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

/// 当前快速筛选合同版本。
pub const SCREEN_CONTRACT_VERSION: &str = "lspr24-screen-6-2-2-v1";
/// 当前快速筛选合同 SHA-256。
pub const SCREEN_CONTRACT_SHA256: &str =
    "715da51fc8b6d95aea20c02722e7555d3b2e574c4844668f3947e83c8c12cbc0";

/// 开发宽表物化配置版本。
pub const DEVELOPMENT_WIDE_CONFIG_VERSION: &str = "lspr24-development-wide-v1";

/// 只允许开发区输出的宽表物化配置。
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DevelopmentWideConfig {
    schema_version: String,
    contract_version: String,
    contract_sha256: String,
    parquet_path: PathBuf,
    run_root: PathBuf,
    field_manifest_path: PathBuf,
}

impl DevelopmentWideConfig {
    /// 创建绑定当前合同和指定运行目录的配置。
    #[must_use]
    pub fn new(
        parquet_path: impl Into<PathBuf>,
        run_root: impl Into<PathBuf>,
        field_manifest_path: impl Into<PathBuf>,
    ) -> Self {
        Self {
            schema_version: DEVELOPMENT_WIDE_CONFIG_VERSION.to_owned(),
            contract_version: SCREEN_CONTRACT_VERSION.to_owned(),
            contract_sha256: SCREEN_CONTRACT_SHA256.to_owned(),
            parquet_path: parquet_path.into(),
            run_root: run_root.into(),
            field_manifest_path: field_manifest_path.into(),
        }
    }

    /// 从严格 JSON 解析配置。
    pub fn from_json(bytes: &[u8]) -> Result<Self, DevelopmentWideConfigError> {
        let config: Self = serde_json::from_slice(bytes)
            .map_err(|error| DevelopmentWideConfigError::Json(error.to_string()))?;
        config.validate()?;
        Ok(config)
    }

    /// 返回原始 LSPR24 Parquet 路径。
    #[must_use]
    pub fn parquet_path(&self) -> &Path {
        &self.parquet_path
    }

    /// 返回本次运行的唯一输出根目录。
    #[must_use]
    pub fn run_root(&self) -> &Path {
        &self.run_root
    }

    /// 返回字段清单的排他发布位置。
    #[must_use]
    pub fn field_manifest_path(&self) -> &Path {
        &self.field_manifest_path
    }

    /// 返回绑定的筛选合同版本。
    #[must_use]
    pub fn contract_version(&self) -> &str {
        &self.contract_version
    }

    /// 返回绑定的筛选合同摘要。
    #[must_use]
    pub fn contract_sha256(&self) -> &str {
        &self.contract_sha256
    }

    pub(crate) fn validate(&self) -> Result<(), DevelopmentWideConfigError> {
        if self.schema_version != DEVELOPMENT_WIDE_CONFIG_VERSION {
            return Err(DevelopmentWideConfigError::InvalidBinding("schema_version"));
        }
        if self.contract_version != SCREEN_CONTRACT_VERSION {
            return Err(DevelopmentWideConfigError::InvalidBinding(
                "contract_version",
            ));
        }
        if self.contract_sha256 != SCREEN_CONTRACT_SHA256 {
            return Err(DevelopmentWideConfigError::InvalidBinding(
                "contract_sha256",
            ));
        }
        if self.parquet_path.as_os_str().is_empty()
            || self.run_root.as_os_str().is_empty()
            || self.field_manifest_path.as_os_str().is_empty()
        {
            return Err(DevelopmentWideConfigError::EmptyPath);
        }
        if self.parquet_path.is_absolute()
            || self.run_root.is_absolute()
            || self.field_manifest_path.is_absolute()
        {
            return Err(DevelopmentWideConfigError::AbsolutePath);
        }
        Ok(())
    }
}

/// 开发宽表配置不可用。
#[derive(Debug)]
pub enum DevelopmentWideConfigError {
    Json(String),
    InvalidBinding(&'static str),
    EmptyPath,
    AbsolutePath,
}

impl std::fmt::Display for DevelopmentWideConfigError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Json(message) => write!(formatter, "开发宽表配置 JSON 错误：{message}"),
            Self::InvalidBinding(field) => write!(formatter, "开发宽表配置绑定不匹配：{field}"),
            Self::EmptyPath => formatter.write_str("开发宽表配置路径不能为空"),
            Self::AbsolutePath => formatter.write_str("开发宽表配置必须使用项目根相对路径"),
        }
    }
}

impl std::error::Error for DevelopmentWideConfigError {}
