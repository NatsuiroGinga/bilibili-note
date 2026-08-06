//! 合同冻结的规范元组编码与语义 SHA-256。

use std::error::Error;
use std::fmt::{Display, Formatter};

use sha2::{Digest, Sha256};

use crate::types::{IntegerOverflow, Sha256Digest};

const NULL_TAG: u8 = 0x00;
const BOOL_TAG: u8 = 0x01;
const I64_TAG: u8 = 0x02;
const U8_TAG: u8 = 0x03;
const U16_TAG: u8 = 0x04;
const U64_TAG: u8 = 0x05;
const UTF8_TAG: u8 = 0x06;
const BYTES_TAG: u8 = 0x07;
const IP16_TAG: u8 = 0x08;
const SHA256_TAG: u8 = 0x09;
const FIXED_DECIMAL_12_TAG: u8 = 0x0a;
const FIELD_HEADER_BYTES: usize = 5;

/// 一个规范元组字段。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CanonicalValue<'a> {
    /// 独立类型标记的空值。
    Null,
    /// 单字节 `0/1` 布尔值。
    Bool(bool),
    /// 八字节大端补码有符号整数。
    I64(i64),
    /// 单字节无符号整数。
    U8(u8),
    /// 两字节大端无符号整数。
    U16(u16),
    /// 八字节大端无符号整数。
    U64(u64),
    /// 未经裁剪或规范化的 UTF-8 字节。
    Utf8(&'a str),
    /// 不带隐式语义的原始字节。
    Bytes(&'a [u8]),
    /// 十六字节网络序规范 IP。
    Ip16(&'a [u8; 16]),
    /// 三十二字节 SHA-256 摘要。
    Sha256(&'a Sha256Digest),
    /// 已按十二位小数半偶舍入的有符号定点整数。
    FixedDecimal12(i128),
}

/// 规范编码失败。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CanonicalError {
    /// 单字段长度无法写入四字节无符号大端前缀。
    FieldLengthOverflow { length: usize },
    /// 完整元组缓冲区长度溢出本机地址空间。
    TupleLengthOverflow,
}

impl Display for CanonicalError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::FieldLengthOverflow { length } => {
                write!(formatter, "规范字段长度 {length} 超过 u32")
            }
            Self::TupleLengthOverflow => write!(formatter, "规范元组总长度溢出"),
        }
    }
}

impl Error for CanonicalError {}

/// 把字段序列编码为类型标记、四字节大端长度和值字节。
///
/// # Errors
///
/// 任一字段长度超过 `u32::MAX` 或总缓冲区长度溢出时返回错误。
pub fn tuple_encode(values: &[CanonicalValue<'_>]) -> Result<Vec<u8>, CanonicalError> {
    let mut capacity = 0usize;
    for value in values {
        let length = value_length(*value);
        let _ = u32::try_from(length)
            .map_err(|_| CanonicalError::FieldLengthOverflow { length })?;
        capacity = capacity
            .checked_add(FIELD_HEADER_BYTES)
            .and_then(|current| current.checked_add(length))
            .ok_or(CanonicalError::TupleLengthOverflow)?;
    }

    let mut encoded = Vec::with_capacity(capacity);
    for value in values {
        encode_value(*value, &mut encoded)?;
    }
    Ok(encoded)
}

/// 计算任意字节序列的 SHA-256。
#[must_use]
pub fn sha256(bytes: &[u8]) -> Sha256Digest {
    Sha256::digest(bytes).into()
}

/// 对有序行哈希做四字节长度前缀串联后计算数据集 SHA-256。
#[must_use]
pub fn dataset_semantic_hash(row_hashes: &[Sha256Digest]) -> Sha256Digest {
    let mut hasher = Sha256::new();
    for row_hash in row_hashes {
        hasher.update(32u32.to_be_bytes());
        hasher.update(row_hash);
    }
    hasher.finalize().into()
}

/// 流式构造有序数据集语义哈希和受检查行数。
pub struct DatasetSemanticHasher {
    hasher: Sha256,
    row_count: u64,
}

impl DatasetSemanticHasher {
    /// 创建空数据集哈希器。
    #[must_use]
    pub fn new() -> Self {
        Self {
            hasher: Sha256::new(),
            row_count: 0,
        }
    }

    /// 追加一个已经计算的规范行哈希。
    ///
    /// # Errors
    ///
    /// 行数超过 `u64::MAX` 时返回 [`IntegerOverflow::SortedRowCount`]。
    pub fn push(&mut self, row_hash: &Sha256Digest) -> Result<(), IntegerOverflow> {
        self.row_count = self
            .row_count
            .checked_add(1)
            .ok_or(IntegerOverflow::SortedRowCount)?;
        self.hasher.update(32u32.to_be_bytes());
        self.hasher.update(row_hash);
        Ok(())
    }

    /// 返回已追加的行数。
    #[must_use]
    pub const fn row_count(&self) -> u64 {
        self.row_count
    }

    /// 完成并返回数据集语义哈希。
    #[must_use]
    pub fn finalize(self) -> Sha256Digest {
        self.hasher.finalize().into()
    }
}

impl Default for DatasetSemanticHasher {
    fn default() -> Self {
        Self::new()
    }
}

fn value_length(value: CanonicalValue<'_>) -> usize {
    match value {
        CanonicalValue::Null => 0,
        CanonicalValue::Bool(_) | CanonicalValue::U8(_) => 1,
        CanonicalValue::U16(_) => 2,
        CanonicalValue::I64(_) | CanonicalValue::U64(_) => 8,
        CanonicalValue::Utf8(value) => value.len(),
        CanonicalValue::Bytes(value) => value.len(),
        CanonicalValue::Ip16(_) | CanonicalValue::FixedDecimal12(_) => 16,
        CanonicalValue::Sha256(_) => 32,
    }
}

fn encode_value(value: CanonicalValue<'_>, encoded: &mut Vec<u8>) -> Result<(), CanonicalError> {
    let length = value_length(value);
    let length = u32::try_from(length)
        .map_err(|_| CanonicalError::FieldLengthOverflow { length })?;
    encoded.push(value_tag(value));
    encoded.extend_from_slice(&length.to_be_bytes());
    match value {
        CanonicalValue::Null => {}
        CanonicalValue::Bool(value) => encoded.push(u8::from(value)),
        CanonicalValue::I64(value) => encoded.extend_from_slice(&value.to_be_bytes()),
        CanonicalValue::U8(value) => encoded.push(value),
        CanonicalValue::U16(value) => encoded.extend_from_slice(&value.to_be_bytes()),
        CanonicalValue::U64(value) => encoded.extend_from_slice(&value.to_be_bytes()),
        CanonicalValue::Utf8(value) => encoded.extend_from_slice(value.as_bytes()),
        CanonicalValue::Bytes(value) => encoded.extend_from_slice(value),
        CanonicalValue::Ip16(value) => encoded.extend_from_slice(value),
        CanonicalValue::Sha256(value) => encoded.extend_from_slice(value),
        CanonicalValue::FixedDecimal12(value) => encoded.extend_from_slice(&value.to_be_bytes()),
    }
    Ok(())
}

fn value_tag(value: CanonicalValue<'_>) -> u8 {
    match value {
        CanonicalValue::Null => NULL_TAG,
        CanonicalValue::Bool(_) => BOOL_TAG,
        CanonicalValue::I64(_) => I64_TAG,
        CanonicalValue::U8(_) => U8_TAG,
        CanonicalValue::U16(_) => U16_TAG,
        CanonicalValue::U64(_) => U64_TAG,
        CanonicalValue::Utf8(_) => UTF8_TAG,
        CanonicalValue::Bytes(_) => BYTES_TAG,
        CanonicalValue::Ip16(_) => IP16_TAG,
        CanonicalValue::Sha256(_) => SHA256_TAG,
        CanonicalValue::FixedDecimal12(_) => FIXED_DECIMAL_12_TAG,
    }
}
