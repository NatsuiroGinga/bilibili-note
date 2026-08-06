//! 仅面向前 80% 开发选择的标签路由。

use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fmt::{Display, Formatter};

use sha2::{Digest, Sha256};

use crate::Sha256Digest;

/// 当前分阶段合同版本。
pub const LSPR24_G0_CONTRACT_VERSION: &str = "lspr24-g0-v5-staged";
/// 当前分阶段合同 SHA-256。
pub const LSPR24_G0_CONTRACT_SHA256: &str =
    "877488f3529c6c862b060a74782d1904aae81512ea1169c713ba20d8c3f31a0e";

/// 无标签切分收据中的开发成员标识。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct DevelopmentMemberId {
    raw_flow_id: Sha256Digest,
    source_row_index: u64,
}

impl DevelopmentMemberId {
    /// 创建开发成员标识。
    #[must_use]
    pub const fn new(raw_flow_id: Sha256Digest, source_row_index: u64) -> Self {
        Self {
            raw_flow_id,
            source_row_index,
        }
    }

    /// 返回重复类所绑定的原始流标识。
    #[must_use]
    pub const fn raw_flow_id(self) -> Sha256Digest {
        self.raw_flow_id
    }

    /// 返回过滤前源行号。
    #[must_use]
    pub const fn source_row_index(self) -> u64 {
        self.source_row_index
    }
}

/// 前 80% 开发区唯一可构造的四个时间段。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum DevelopmentSegment {
    First,
    Second,
    Third,
    Fourth,
}

impl DevelopmentSegment {
    pub(crate) const fn as_byte(self) -> u8 {
        match self {
            Self::First => 0,
            Self::Second => 1,
            Self::Third => 2,
            Self::Fourth => 3,
        }
    }

    pub(crate) const fn as_str(self) -> &'static str {
        match self {
            Self::First => "development-1",
            Self::Second => "development-2",
            Self::Third => "development-3",
            Self::Fourth => "development-4",
        }
    }
}

/// 无标签开发选择收据中的一项成员及其时间段。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DevelopmentSelectionMember {
    member: DevelopmentMemberId,
    segment: DevelopmentSegment,
}

impl DevelopmentSelectionMember {
    /// 创建不含标签的开发选择成员。
    #[must_use]
    pub const fn new(member: DevelopmentMemberId, segment: DevelopmentSegment) -> Self {
        Self { member, segment }
    }
}

/// 仅包含开发成员的无标签切分收据。
#[derive(Debug, Clone)]
pub struct DevelopmentSplitReceipt {
    members: BTreeMap<DevelopmentMemberId, DevelopmentSegment>,
    receipt_sha256: Sha256Digest,
}

impl DevelopmentSplitReceipt {
    /// 从前 80% 开发成员构造确定性无标签切分收据。
    ///
    /// # Errors
    ///
    /// 成员为空或同一成员重复声明时失败。
    pub fn new(members: Vec<DevelopmentSelectionMember>) -> Result<Self, RoutingError> {
        if members.is_empty() {
            return Err(RoutingError::EmptyDevelopmentSelection);
        }

        let mut selected = BTreeMap::new();
        for item in members {
            if selected.insert(item.member, item.segment).is_some() {
                return Err(RoutingError::DuplicateSelectionMember(item.member));
            }
        }
        let receipt_sha256 = selection_receipt_sha256(&selected);
        Ok(Self {
            members: selected,
            receipt_sha256,
        })
    }

    /// 返回只由合同和无标签开发成员计算的收据摘要。
    #[must_use]
    pub const fn receipt_sha256(&self) -> Sha256Digest {
        self.receipt_sha256
    }

    fn segment(&self, member: DevelopmentMemberId) -> Option<DevelopmentSegment> {
        self.members.get(&member).copied()
    }
}

/// 尚未规范化的标签行。
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DevelopmentLabelRow {
    member: DevelopmentMemberId,
    raw_label: String,
}

impl DevelopmentLabelRow {
    /// 创建输入标签行；标签值只会在成员验证通过后规范化。
    #[must_use]
    pub fn new(member: DevelopmentMemberId, raw_label: impl Into<String>) -> Self {
        Self {
            member,
            raw_label: raw_label.into(),
        }
    }
}

/// 模型侧唯一可见的规范二元标签。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum NormalizedLabel {
    Benign,
    Malicious,
}

impl NormalizedLabel {
    pub(crate) const fn as_str(self) -> &'static str {
        match self {
            Self::Benign => "benign",
            Self::Malicious => "malicious",
        }
    }
}

/// 已验证属于开发选择的标签行。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RoutedDevelopmentLabel {
    member: DevelopmentMemberId,
    segment: DevelopmentSegment,
    label: NormalizedLabel,
}

impl RoutedDevelopmentLabel {
    /// 返回开发成员标识。
    #[must_use]
    pub const fn member(&self) -> DevelopmentMemberId {
        self.member
    }

    /// 返回开发时间段。
    #[must_use]
    pub const fn segment(&self) -> DevelopmentSegment {
        self.segment
    }

    /// 返回规范标签。
    #[must_use]
    pub const fn label(&self) -> NormalizedLabel {
        self.label
    }
}

/// 仅含开发区可观察量的路由结果。
#[derive(Debug, Clone)]
pub struct DevelopmentRouting {
    split_receipt_sha256: Sha256Digest,
    labels: Vec<RoutedDevelopmentLabel>,
    isolated_conflict_classes: u64,
    isolated_development_members: u64,
}

impl DevelopmentRouting {
    /// 返回绑定的无标签开发切分收据摘要。
    #[must_use]
    pub const fn split_receipt_sha256(&self) -> Sha256Digest {
        self.split_receipt_sha256
    }

    /// 返回通过路由且未被冲突隔离的开发标签。
    #[must_use]
    pub fn labels(&self) -> &[RoutedDevelopmentLabel] {
        &self.labels
    }

    /// 返回开发选择内部的冲突重复类数。
    #[must_use]
    pub const fn isolated_conflict_classes(&self) -> u64 {
        self.isolated_conflict_classes
    }

    /// 返回开发选择内部因冲突被隔离的成员数。
    #[must_use]
    pub const fn isolated_development_members(&self) -> u64 {
        self.isolated_development_members
    }
}

/// 只掌握无标签开发选择的受限路由器。
#[derive(Debug)]
pub struct DevelopmentRouter {
    selection: DevelopmentSplitReceipt,
}

impl DevelopmentRouter {
    /// 将路由器绑定到单个无标签开发切分收据。
    #[must_use]
    pub const fn new(selection: DevelopmentSplitReceipt) -> Self {
        Self { selection }
    }

    /// 先验证开发成员身份，再规范标签并隔离冲突重复类。
    ///
    /// # Errors
    ///
    /// 开发成员标签非法或缺失时失败；未入选成员在规范化前静默丢弃。
    pub fn route<I>(self, rows: I) -> Result<DevelopmentRouting, RoutingError>
    where
        I: IntoIterator<Item = DevelopmentLabelRow>,
    {
        let mut labels_by_member = BTreeMap::new();
        let mut labels_by_class = BTreeMap::<Sha256Digest, BTreeSet<NormalizedLabel>>::new();

        for row in rows {
            let Some(segment) = self.selection.segment(row.member) else {
                continue;
            };
            let label = normalize_label(&row.raw_label).ok_or_else(|| {
                RoutingError::InvalidDevelopmentLabel {
                    member: row.member,
                    raw_label: row.raw_label,
                }
            })?;
            if let Some(previous) = labels_by_member.insert(row.member, (segment, label)) {
                labels_by_class
                    .entry(row.member.raw_flow_id())
                    .or_default()
                    .insert(previous.1);
            }
            labels_by_class
                .entry(row.member.raw_flow_id())
                .or_default()
                .insert(label);
        }

        if let Some(member) = self
            .selection
            .members
            .keys()
            .find(|member| !labels_by_member.contains_key(member))
        {
            return Err(RoutingError::MissingDevelopmentLabel(*member));
        }

        let conflict_classes = labels_by_class
            .iter()
            .filter_map(|(class, labels)| (labels.len() > 1).then_some(*class))
            .collect::<BTreeSet<_>>();
        let mut labels = labels_by_member
            .into_iter()
            .filter_map(|(member, (segment, label))| {
                (!conflict_classes.contains(&member.raw_flow_id())).then_some(
                    RoutedDevelopmentLabel {
                        member,
                        segment,
                        label,
                    },
                )
            })
            .collect::<Vec<_>>();
        labels.sort_unstable_by_key(|row| (row.segment, row.member));

        let isolated_development_members = self
            .selection
            .members
            .keys()
            .filter(|member| conflict_classes.contains(&member.raw_flow_id()))
            .count()
            .try_into()
            .map_err(|_| RoutingError::DevelopmentCountOverflow)?;
        let isolated_conflict_classes = conflict_classes
            .len()
            .try_into()
            .map_err(|_| RoutingError::DevelopmentCountOverflow)?;

        Ok(DevelopmentRouting {
            split_receipt_sha256: self.selection.receipt_sha256,
            labels,
            isolated_conflict_classes,
            isolated_development_members,
        })
    }
}

fn normalize_label(raw_label: &str) -> Option<NormalizedLabel> {
    match raw_label.trim().to_ascii_lowercase().as_str() {
        "benign" | "normal" => Some(NormalizedLabel::Benign),
        "malicious" | "attack" => Some(NormalizedLabel::Malicious),
        _ => None,
    }
}

fn selection_receipt_sha256(
    members: &BTreeMap<DevelopmentMemberId, DevelopmentSegment>,
) -> Sha256Digest {
    let mut hasher = Sha256::new();
    hasher.update(b"lspr24-g0-development-selection\0");
    hasher.update(LSPR24_G0_CONTRACT_VERSION.as_bytes());
    hasher.update([0]);
    hasher.update(LSPR24_G0_CONTRACT_SHA256.as_bytes());
    for (member, segment) in members {
        hasher.update(member.raw_flow_id);
        hasher.update(member.source_row_index.to_be_bytes());
        hasher.update([segment.as_byte()]);
    }
    hasher.finalize().into()
}

/// 开发受限路由失败。
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RoutingError {
    EmptyDevelopmentSelection,
    DuplicateSelectionMember(DevelopmentMemberId),
    InvalidDevelopmentLabel {
        member: DevelopmentMemberId,
        raw_label: String,
    },
    MissingDevelopmentLabel(DevelopmentMemberId),
    DevelopmentCountOverflow,
}

impl Display for RoutingError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::EmptyDevelopmentSelection => formatter.write_str("开发选择不能为空"),
            Self::DuplicateSelectionMember(member) => write!(
                formatter,
                "开发选择成员重复：源行 {}",
                member.source_row_index()
            ),
            Self::InvalidDevelopmentLabel { member, .. } => write!(
                formatter,
                "开发成员标签非法：源行 {}",
                member.source_row_index()
            ),
            Self::MissingDevelopmentLabel(member) => write!(
                formatter,
                "开发成员标签缺失：源行 {}",
                member.source_row_index()
            ),
            Self::DevelopmentCountOverflow => formatter.write_str("开发路由计数溢出"),
        }
    }
}

impl Error for RoutingError {}
