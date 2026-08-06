//! 前 80% 开发区确定性物化与开发阶段门禁状态。

use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fmt::{Display, Formatter};
use std::path::{Path, PathBuf};

use serde::Serialize;
use serde_json::Value;

use crate::canonical::sha256;
use crate::development_router::{
    DevelopmentMemberId, DevelopmentRouting, NormalizedLabel, RoutedDevelopmentLabel,
};
use crate::{GateId, GateStatus, OutputError, PartialOutput, Sha256Digest};

/// 已完成身份隔离的候选特征行。
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DevelopmentFeatureRow {
    member: DevelopmentMemberId,
    canonical_features: Vec<u8>,
}

impl DevelopmentFeatureRow {
    /// 创建候选特征行；只有路由结果中的开发成员会进入物化。
    #[must_use]
    pub const fn new(member: DevelopmentMemberId, canonical_features: Vec<u8>) -> Self {
        Self {
            member,
            canonical_features,
        }
    }
}

/// 成功发布后的开发物化收据。
#[derive(Debug, Clone)]
pub struct DevelopmentMaterializationReceipt {
    output_path: PathBuf,
    split_receipt_sha256: Sha256Digest,
    development_row_count: u64,
    development_semantic_sha256: Sha256Digest,
}

impl DevelopmentMaterializationReceipt {
    /// 返回正式开发输出路径。
    #[must_use]
    pub fn output_path(&self) -> &Path {
        &self.output_path
    }

    /// 返回物化的开发行数。
    #[must_use]
    pub const fn development_row_count(&self) -> u64 {
        self.development_row_count
    }

    /// 返回仅由开发输出计算的语义摘要。
    #[must_use]
    pub const fn development_semantic_sha256(&self) -> Sha256Digest {
        self.development_semantic_sha256
    }

    /// 返回所绑定的无标签开发切分收据摘要。
    #[must_use]
    pub const fn split_receipt_sha256(&self) -> Sha256Digest {
        self.split_receipt_sha256
    }

    /// 开发阶段不得把 A12 置为通过。
    #[must_use]
    pub const fn gate_status(&self, gate_id: GateId) -> GateStatus {
        match gate_id {
            GateId::A12 => GateStatus::NotReady,
            _ => GateStatus::NotReady,
        }
    }

    /// 最终哈希在 G0-D 阶段固定未就绪。
    #[must_use]
    pub const fn final_hash_status(&self) -> GateStatus {
        GateStatus::NotReady
    }
}

#[derive(Serialize)]
struct OutputRow<'a> {
    segment: &'static str,
    raw_flow_id: String,
    source_row_index: u64,
    label: &'static str,
    canonical_features: &'a [u8],
}

/// 只物化已路由开发成员，并以排他语义发布单个正式文件。
///
/// # Errors
///
/// 开发成员特征缺失或重复、序列化失败、输出已存在或文件系统失败时返回错误。
pub fn materialize_development(
    routing: &DevelopmentRouting,
    features: &[DevelopmentFeatureRow],
    output_path: &Path,
) -> Result<DevelopmentMaterializationReceipt, MaterializeError> {
    let routed_members = routing
        .labels()
        .iter()
        .map(RoutedDevelopmentLabel::member)
        .collect::<BTreeSet<_>>();
    let mut features_by_member = BTreeMap::new();
    for feature in features {
        if !routed_members.contains(&feature.member) {
            continue;
        }
        if features_by_member
            .insert(feature.member, feature.canonical_features.as_slice())
            .is_some()
        {
            return Err(MaterializeError::DuplicateDevelopmentFeature {
                member: feature.member,
            });
        }
    }

    let mut bytes = Vec::new();
    for label in routing.labels() {
        let canonical_features = features_by_member.get(&label.member()).ok_or(
            MaterializeError::MissingDevelopmentFeature {
                member: label.member(),
            },
        )?;
        let row = OutputRow {
            segment: label.segment().as_str(),
            raw_flow_id: encode_hex(&label.member().raw_flow_id()),
            source_row_index: label.member().source_row_index(),
            label: normalized_label_str(label.label()),
            canonical_features,
        };
        serde_json::to_writer(&mut bytes, &row)
            .map_err(|error| MaterializeError::Serialization(error.to_string()))?;
        bytes.push(b'\n');
    }

    let development_row_count = routing
        .labels()
        .len()
        .try_into()
        .map_err(|_| MaterializeError::DevelopmentCountOverflow)?;
    let development_semantic_sha256 = sha256(&bytes);
    let mut output = PartialOutput::create(output_path).map_err(MaterializeError::Output)?;
    output.write_all(&bytes).map_err(MaterializeError::Output)?;
    let output_path = output.commit().map_err(MaterializeError::Output)?;

    Ok(DevelopmentMaterializationReceipt {
        output_path,
        split_receipt_sha256: routing.split_receipt_sha256(),
        development_row_count,
        development_semantic_sha256,
    })
}

fn normalized_label_str(label: NormalizedLabel) -> &'static str {
    label.as_str()
}

fn encode_hex(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut encoded = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        encoded.push(char::from(HEX[usize::from(byte >> 4)]));
        encoded.push(char::from(HEX[usize::from(byte & 0x0f)]));
    }
    encoded
}

/// 原始门禁制品映射；生产者汇总字段不具备证明力。
#[derive(Debug, Clone, Default)]
pub struct RawGateArtifacts {
    artifacts: BTreeMap<GateId, Value>,
}

impl RawGateArtifacts {
    /// 创建原始门禁制品集合。
    #[must_use]
    pub const fn new(artifacts: BTreeMap<GateId, Value>) -> Self {
        Self { artifacts }
    }

    /// 移除单项原始制品。
    pub fn remove(&mut self, gate_id: GateId) -> Option<Value> {
        self.artifacts.remove(&gate_id)
    }

    /// 返回单项原始制品。
    #[must_use]
    pub fn get(&self, gate_id: GateId) -> Option<&Value> {
        self.artifacts.get(&gate_id)
    }
}

/// 对尚未接入独立谓词的原始制品执行失败关闭归约。
///
/// 任意生产者布尔值都不具备证明力；A12 及其他未独立复算项保持 `NOT_READY`。
#[must_use]
pub fn recompute_raw_gate_statuses(artifacts: &RawGateArtifacts) -> BTreeMap<GateId, GateStatus> {
    let _ = artifacts;
    GateId::ALL
        .into_iter()
        .map(|gate_id| (gate_id, GateStatus::NotReady))
        .collect()
}

/// 开发物化失败。
#[derive(Debug)]
pub enum MaterializeError {
    MissingDevelopmentFeature { member: DevelopmentMemberId },
    DuplicateDevelopmentFeature { member: DevelopmentMemberId },
    DevelopmentCountOverflow,
    Serialization(String),
    Output(OutputError),
}

impl Display for MaterializeError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::MissingDevelopmentFeature { member } => write!(
                formatter,
                "开发成员特征缺失：源行 {}",
                member.source_row_index()
            ),
            Self::DuplicateDevelopmentFeature { member } => write!(
                formatter,
                "开发成员特征重复：源行 {}",
                member.source_row_index()
            ),
            Self::DevelopmentCountOverflow => formatter.write_str("开发物化计数溢出"),
            Self::Serialization(error) => write!(formatter, "开发行序列化失败：{error}"),
            Self::Output(error) => write!(formatter, "开发区物化输出失败：{error}"),
        }
    }
}

impl Error for MaterializeError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Output(error) => Some(error),
            Self::MissingDevelopmentFeature { .. }
            | Self::DuplicateDevelopmentFeature { .. }
            | Self::DevelopmentCountOverflow
            | Self::Serialization(_) => None,
        }
    }
}
