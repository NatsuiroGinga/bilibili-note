//! 稳定排序所需的新类型与记录类型。

use std::error::Error;
use std::fmt::{Display, Formatter};

/// SHA-256 摘要的固定字节表示。
pub type Sha256Digest = [u8; 32];

/// 受检查整数运算失败。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IntegerOverflow {
    /// 源行号无法继续递增。
    SourceRowIndex,
    /// 外部排序输出行数无法继续递增。
    SortedRowCount,
}

impl Display for IntegerOverflow {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::SourceRowIndex => write!(formatter, "源行号递增溢出"),
            Self::SortedRowCount => write!(formatter, "外部排序输出行数递增溢出"),
        }
    }
}

impl Error for IntegerOverflow {}

/// 过滤前的零基 Parquet 逻辑源行号。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct SourceRowIndex(u64);

impl SourceRowIndex {
    /// 从已验证的零基值创建源行号。
    #[must_use]
    pub const fn new(value: u64) -> Self {
        Self(value)
    }

    /// 返回底层无符号整数。
    #[must_use]
    pub const fn get(self) -> u64 {
        self.0
    }

    /// 返回下一个源行号，溢出时失败而不是回绕。
    ///
    /// # Errors
    ///
    /// 当前值为 `u64::MAX` 时返回 [`IntegerOverflow::SourceRowIndex`]。
    pub const fn checked_next(self) -> Result<Self, IntegerOverflow> {
        match self.0.checked_add(1) {
            Some(next) => Ok(Self(next)),
            None => Err(IntegerOverflow::SourceRowIndex),
        }
    }
}

/// 同一物理流分配到端点序列时的冻结角色顺序。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(u8)]
pub enum EndpointRoleOrder {
    /// 被防御端点位于源侧。
    Source = 0,
    /// 被防御端点位于目的侧。
    Destination = 1,
}

impl EndpointRoleOrder {
    pub(crate) const fn from_byte(value: u8) -> Option<Self> {
        match value {
            0 => Some(Self::Source),
            1 => Some(Self::Destination),
            _ => None,
        }
    }

    pub(crate) const fn as_byte(self) -> u8 {
        self as u8
    }
}

/// 合同冻结的完整流到端点稳定排序键。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct StableSortKey {
    protected_endpoint_id: Sha256Digest,
    last_ns: i64,
    start_ns: i64,
    raw_flow_id: Sha256Digest,
    endpoint_role_order: EndpointRoleOrder,
    source_row_index: SourceRowIndex,
}

impl StableSortKey {
    /// 按合同字段顺序创建完整稳定键。
    #[must_use]
    pub const fn new(
        protected_endpoint_id: Sha256Digest,
        last_ns: i64,
        start_ns: i64,
        raw_flow_id: Sha256Digest,
        endpoint_role_order: EndpointRoleOrder,
        source_row_index: SourceRowIndex,
    ) -> Self {
        Self {
            protected_endpoint_id,
            last_ns,
            start_ns,
            raw_flow_id,
            endpoint_role_order,
            source_row_index,
        }
    }

    pub(crate) const fn protected_endpoint_id(&self) -> &Sha256Digest {
        &self.protected_endpoint_id
    }

    pub(crate) const fn last_ns(&self) -> i64 {
        self.last_ns
    }

    pub(crate) const fn start_ns(&self) -> i64 {
        self.start_ns
    }

    pub(crate) const fn raw_flow_id(&self) -> &Sha256Digest {
        &self.raw_flow_id
    }

    pub(crate) const fn endpoint_role_order(&self) -> EndpointRoleOrder {
        self.endpoint_role_order
    }

    pub(crate) const fn source_row_index(&self) -> SourceRowIndex {
        self.source_row_index
    }
}

/// 带完整稳定键和规范行字节的待排序记录。
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SortableRecord {
    key: StableSortKey,
    payload: Vec<u8>,
}

impl SortableRecord {
    /// 创建待排序记录；载荷必须是已经完成的规范行编码。
    #[must_use]
    pub const fn new(key: StableSortKey, payload: Vec<u8>) -> Self {
        Self { key, payload }
    }

    /// 返回完整稳定键。
    #[must_use]
    pub const fn key(&self) -> &StableSortKey {
        &self.key
    }

    /// 返回用于语义行哈希的规范行字节。
    #[must_use]
    pub fn payload(&self) -> &[u8] {
        &self.payload
    }

    pub(crate) fn into_parts(self) -> (StableSortKey, Vec<u8>) {
        (self.key, self.payload)
    }
}
