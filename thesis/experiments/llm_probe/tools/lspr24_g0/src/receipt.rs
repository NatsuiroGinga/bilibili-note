//! 严格的 G0-A 配置与机器收据合同。

use std::collections::BTreeMap;
use std::error::Error;
use std::fmt::{Display, Formatter};
use std::path::{Path, PathBuf};

use serde::de::Error as DeserializeError;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use serde_json::Value;

use crate::canonical::sha256;
use crate::types::Sha256Digest;

/// 配置模式版本。
pub const GATE_CONFIG_SCHEMA_VERSION: &str = "g0-config-v3";
/// 收据模式版本。
pub const GATE_RECEIPT_SCHEMA_VERSION: &str = "g0-receipt-v3";

/// G0-A 门禁编号闭集。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum GateId {
    A01,
    A02,
    A03,
    A04,
    A05,
    A06,
    A07,
    A08,
    A09,
    A10,
    A11,
    A12,
    A13,
    A14,
}

impl GateId {
    /// 按冻结拓扑顺序排列的全部门禁。
    pub const ALL: [Self; 14] = [
        Self::A01,
        Self::A02,
        Self::A03,
        Self::A04,
        Self::A05,
        Self::A06,
        Self::A07,
        Self::A08,
        Self::A09,
        Self::A10,
        Self::A11,
        Self::A12,
        Self::A13,
        Self::A14,
    ];

    /// 返回机器可读门禁名称。
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::A01 => "A01",
            Self::A02 => "A02",
            Self::A03 => "A03",
            Self::A04 => "A04",
            Self::A05 => "A05",
            Self::A06 => "A06",
            Self::A07 => "A07",
            Self::A08 => "A08",
            Self::A09 => "A09",
            Self::A10 => "A10",
            Self::A11 => "A11",
            Self::A12 => "A12",
            Self::A13 => "A13",
            Self::A14 => "A14",
        }
    }

    /// 返回冻结合同规定的直接依赖，顺序不可改变。
    #[must_use]
    pub const fn required_dependencies(self) -> &'static [Self] {
        match self {
            Self::A01 => &[],
            Self::A02 => &[Self::A01],
            Self::A03 => &[Self::A01, Self::A02],
            Self::A04 => &[Self::A02, Self::A03],
            Self::A05 => &[Self::A04],
            Self::A06 => &[Self::A01, Self::A03],
            Self::A07 => &[Self::A06],
            Self::A08 => &[Self::A05, Self::A07],
            Self::A09 => &[Self::A08],
            Self::A10 => &[Self::A09],
            Self::A11 => &[
                Self::A02,
                Self::A03,
                Self::A04,
                Self::A05,
                Self::A06,
                Self::A07,
                Self::A08,
            ],
            Self::A12 => &[Self::A01, Self::A02, Self::A03, Self::A04, Self::A05],
            Self::A13 => &[Self::A06, Self::A08, Self::A09, Self::A11, Self::A12],
            Self::A14 => &[
                Self::A01,
                Self::A02,
                Self::A03,
                Self::A04,
                Self::A05,
                Self::A06,
                Self::A07,
                Self::A08,
                Self::A09,
                Self::A11,
                Self::A12,
                Self::A13,
            ],
        }
    }
}

impl Display for GateId {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(self.as_str())
    }
}

/// 单项门禁状态闭集。
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GateStatus {
    #[serde(rename = "PASS")]
    Pass,
    #[serde(rename = "FAIL")]
    Fail,
    #[serde(rename = "NOT_READY")]
    NotReady,
}

impl GateStatus {
    /// 返回机器可读状态名称。
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Pass => "PASS",
            Self::Fail => "FAIL",
            Self::NotReady => "NOT_READY",
        }
    }
}

/// 输入制品路径与预期 SHA-256。
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArtifactRef {
    path: PathBuf,
    #[serde(
        serialize_with = "serialize_digest",
        deserialize_with = "deserialize_digest"
    )]
    sha256: Sha256Digest,
}

impl ArtifactRef {
    /// 创建一个输入制品引用。
    #[must_use]
    pub fn new(path: impl Into<PathBuf>, sha256: Sha256Digest) -> Self {
        Self {
            path: path.into(),
            sha256,
        }
    }

    /// 返回制品路径。
    #[must_use]
    pub fn path(&self) -> &Path {
        &self.path
    }

    /// 返回预期摘要。
    #[must_use]
    pub const fn sha256(&self) -> Sha256Digest {
        self.sha256
    }
}

/// 直接依赖收据及其绑定摘要。
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct ReceiptDependency {
    pub(crate) gate_id: GateId,
    #[serde(
        serialize_with = "serialize_digest",
        deserialize_with = "deserialize_digest"
    )]
    pub(crate) receipt_sha256: Sha256Digest,
}

/// 门禁程序的严格配置。
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GateConfig {
    schema_version: String,
    contract_version: String,
    contract_sha256: String,
    receipt_paths: BTreeMap<GateId, PathBuf>,
}

impl GateConfig {
    /// 创建供库调用方使用的空路径配置。
    #[must_use]
    pub fn new(contract_version: impl Into<String>, contract_sha256: impl Into<String>) -> Self {
        Self {
            schema_version: GATE_CONFIG_SCHEMA_VERSION.to_owned(),
            contract_version: contract_version.into(),
            contract_sha256: contract_sha256.into(),
            receipt_paths: BTreeMap::new(),
        }
    }

    /// 返回合同版本。
    #[must_use]
    pub fn contract_version(&self) -> &str {
        &self.contract_version
    }

    /// 返回配置中声明的合同摘要文本。
    #[must_use]
    pub fn contract_sha256(&self) -> &str {
        &self.contract_sha256
    }

    /// 返回有序收据路径映射。
    #[must_use]
    pub fn receipt_paths(&self) -> &BTreeMap<GateId, PathBuf> {
        &self.receipt_paths
    }

    pub(crate) fn expected_contract_sha256(&self) -> Option<Sha256Digest> {
        decode_digest(&self.contract_sha256).ok()
    }

    pub(crate) fn schema_version(&self) -> &str {
        &self.schema_version
    }
}

/// 一项严格机器收据。
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GateReceipt {
    gate_id: GateId,
    contract_version: String,
    #[serde(
        serialize_with = "serialize_digest",
        deserialize_with = "deserialize_digest"
    )]
    contract_sha256: Sha256Digest,
    #[serde(
        serialize_with = "serialize_digest",
        deserialize_with = "deserialize_digest"
    )]
    producer_binary_sha256: Sha256Digest,
    input_artifacts: Vec<ArtifactRef>,
    schema_version: String,
    checks: Value,
    status: GateStatus,
    created_at_utc: String,
    #[serde(
        serialize_with = "serialize_digest",
        deserialize_with = "deserialize_digest"
    )]
    receipt_sha256: Sha256Digest,
    depends_on: Vec<ReceiptDependency>,
}

impl GateReceipt {
    /// 返回门禁编号。
    #[must_use]
    pub const fn gate_id(&self) -> GateId {
        self.gate_id
    }

    /// 返回生产者声明状态。门禁归约不会把它当作独立复算结果。
    #[must_use]
    pub const fn producer_status(&self) -> GateStatus {
        self.status
    }

    /// 返回收据自哈希。
    #[must_use]
    pub const fn receipt_sha256(&self) -> Sha256Digest {
        self.receipt_sha256
    }

    /// 返回可变输入制品数组，供生产者在签名前构造收据。
    #[must_use]
    pub fn input_artifacts_mut(&mut self) -> &mut Vec<ArtifactRef> {
        &mut self.input_artifacts
    }

    /// 按冻结顺序设置直接依赖。
    pub fn set_dependencies(&mut self, dependencies: Vec<(GateId, Sha256Digest)>) {
        self.depends_on = dependencies
            .into_iter()
            .map(|(gate_id, receipt_sha256)| ReceiptDependency {
                gate_id,
                receipt_sha256,
            })
            .collect();
    }

    /// 设置收据摘要，主要用于收据读取器和故障测试。
    pub const fn set_receipt_sha256(&mut self, receipt_sha256: Sha256Digest) {
        self.receipt_sha256 = receipt_sha256;
    }

    /// 计算并写入规范 JSON 自哈希。
    ///
    /// 自哈希输入是删除 `receipt_sha256` 字段后，按对象键字典序编码的紧凑 JSON。
    ///
    /// # Errors
    ///
    /// 收据无法转换为规范 JSON 时返回错误。
    pub fn with_computed_hash(mut self) -> Result<Self, ReceiptError> {
        self.receipt_sha256 = self.computed_sha256()?;
        Ok(self)
    }

    pub(crate) fn computed_sha256(&self) -> Result<Sha256Digest, ReceiptError> {
        let mut value = serde_json::to_value(self)
            .map_err(|error| ReceiptError::Serialization(error.to_string()))?;
        let object = value
            .as_object_mut()
            .ok_or_else(|| ReceiptError::Serialization("收据根节点不是 JSON 对象".to_owned()))?;
        object.remove("receipt_sha256");
        let mut encoded = Vec::new();
        write_canonical_json(&value, &mut encoded)?;
        Ok(sha256(&encoded))
    }

    pub(crate) fn contract_version(&self) -> &str {
        &self.contract_version
    }

    pub(crate) const fn contract_sha256(&self) -> Sha256Digest {
        self.contract_sha256
    }

    pub(crate) fn schema_version(&self) -> &str {
        &self.schema_version
    }

    pub(crate) fn input_artifacts(&self) -> &[ArtifactRef] {
        &self.input_artifacts
    }

    pub(crate) fn dependencies(&self) -> &[ReceiptDependency] {
        &self.depends_on
    }
}

/// 配置或收据解析失败。
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReceiptError {
    /// JSON 结构、字段、枚举或约束不符合模式。
    Schema(String),
    /// 规范 JSON 序列化失败。
    Serialization(String),
}

impl Display for ReceiptError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Schema(message) => write!(formatter, "收据模式错误：{message}"),
            Self::Serialization(message) => write!(formatter, "收据序列化错误：{message}"),
        }
    }
}

impl Error for ReceiptError {}

/// 严格解析门禁配置。
///
/// # Errors
///
/// JSON 无效、存在未知字段或枚举、版本不符、哈希或路径无效时返回错误。
pub fn parse_gate_config(bytes: &[u8]) -> Result<GateConfig, ReceiptError> {
    let config: GateConfig =
        serde_json::from_slice(bytes).map_err(|error| ReceiptError::Schema(error.to_string()))?;
    if config.schema_version != GATE_CONFIG_SCHEMA_VERSION {
        return Err(ReceiptError::Schema(format!(
            "schema_version 必须为 {GATE_CONFIG_SCHEMA_VERSION}"
        )));
    }
    if config.contract_version.is_empty() {
        return Err(ReceiptError::Schema("contract_version 不能为空".to_owned()));
    }
    decode_digest(&config.contract_sha256)
        .map_err(|message| ReceiptError::Schema(format!("contract_sha256 {message}")))?;
    for path in config.receipt_paths.values() {
        validate_path(path, "receipt_paths")?;
    }
    Ok(config)
}

/// 严格解析单项门禁收据，但不把生产者状态当作独立复算结果。
///
/// # Errors
///
/// JSON 无效、存在未知字段或枚举、版本不符、哈希或路径无效时返回错误。
pub fn parse_gate_receipt(bytes: &[u8]) -> Result<GateReceipt, ReceiptError> {
    let receipt: GateReceipt =
        serde_json::from_slice(bytes).map_err(|error| ReceiptError::Schema(error.to_string()))?;
    if receipt.schema_version != GATE_RECEIPT_SCHEMA_VERSION {
        return Err(ReceiptError::Schema(format!(
            "schema_version 必须为 {GATE_RECEIPT_SCHEMA_VERSION}"
        )));
    }
    if receipt.contract_version.is_empty() {
        return Err(ReceiptError::Schema("contract_version 不能为空".to_owned()));
    }
    if receipt.created_at_utc.is_empty() || !receipt.created_at_utc.ends_with('Z') {
        return Err(ReceiptError::Schema(
            "created_at_utc 必须是以 Z 结尾的非空 UTC 时间".to_owned(),
        ));
    }
    if !receipt.checks.is_object() {
        return Err(ReceiptError::Schema("checks 必须是 JSON 对象".to_owned()));
    }
    for artifact in &receipt.input_artifacts {
        validate_path(&artifact.path, "input_artifacts.path")?;
    }
    Ok(receipt)
}

fn validate_path(path: &Path, field: &str) -> Result<(), ReceiptError> {
    let Some(path) = path.to_str() else {
        return Err(ReceiptError::Schema(format!("{field} 必须是 UTF-8 路径")));
    };
    if path.is_empty() || path.contains('*') || path.contains('?') {
        return Err(ReceiptError::Schema(format!(
            "{field} 不能为空或包含通配符"
        )));
    }
    Ok(())
}

fn decode_digest(value: &str) -> Result<Sha256Digest, String> {
    if value.len() != 64 {
        return Err("必须是 64 位小写十六进制".to_owned());
    }
    let mut digest = [0u8; 32];
    for (index, pair) in value.as_bytes().chunks_exact(2).enumerate() {
        let high = decode_nibble(pair[0])?;
        let low = decode_nibble(pair[1])?;
        digest[index] = (high << 4) | low;
    }
    Ok(digest)
}

fn decode_nibble(value: u8) -> Result<u8, String> {
    match value {
        b'0'..=b'9' => Ok(value - b'0'),
        b'a'..=b'f' => Ok(value - b'a' + 10),
        _ => Err("必须是 64 位小写十六进制".to_owned()),
    }
}

fn encode_digest(value: &Sha256Digest) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut encoded = String::with_capacity(64);
    for byte in value {
        encoded.push(char::from(DIGITS[usize::from(byte >> 4)]));
        encoded.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    encoded
}

fn serialize_digest<S>(value: &Sha256Digest, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    serializer.serialize_str(&encode_digest(value))
}

fn deserialize_digest<'de, D>(deserializer: D) -> Result<Sha256Digest, D::Error>
where
    D: Deserializer<'de>,
{
    let value = String::deserialize(deserializer)?;
    decode_digest(&value).map_err(D::Error::custom)
}

fn write_canonical_json(value: &Value, output: &mut Vec<u8>) -> Result<(), ReceiptError> {
    match value {
        Value::Null => output.extend_from_slice(b"null"),
        Value::Bool(value) => output.extend_from_slice(if *value { b"true" } else { b"false" }),
        Value::Number(value) => output.extend_from_slice(value.to_string().as_bytes()),
        Value::String(value) => {
            let encoded = serde_json::to_vec(value)
                .map_err(|error| ReceiptError::Serialization(error.to_string()))?;
            output.extend_from_slice(&encoded);
        }
        Value::Array(values) => {
            output.push(b'[');
            for (index, value) in values.iter().enumerate() {
                if index > 0 {
                    output.push(b',');
                }
                write_canonical_json(value, output)?;
            }
            output.push(b']');
        }
        Value::Object(values) => {
            output.push(b'{');
            let mut keys = values.keys().collect::<Vec<_>>();
            keys.sort_unstable();
            for (index, key) in keys.into_iter().enumerate() {
                if index > 0 {
                    output.push(b',');
                }
                let encoded_key = serde_json::to_vec(key)
                    .map_err(|error| ReceiptError::Serialization(error.to_string()))?;
                output.extend_from_slice(&encoded_key);
                output.push(b':');
                write_canonical_json(&values[key], output)?;
            }
            output.push(b'}');
        }
    }
    Ok(())
}
