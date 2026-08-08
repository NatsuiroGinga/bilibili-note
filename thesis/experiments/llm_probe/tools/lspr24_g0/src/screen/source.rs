use std::error::Error;
use std::fmt::{Display, Formatter};
use std::net::IpAddr;

use arrow_array::{Array, Float64Array, Int32Array, Int64Array};
use arrow_schema::DataType;

/// 一微秒包含的纳秒数。
pub const NS_PER_MICROSECOND: i64 = 1_000;

/// 受保护端点相对于流方向的位置。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EndpointDirection {
    /// 受保护端点是流量源端。
    Outbound,
    /// 受保护端点是流量目的端。
    Inbound,
}

/// 一条流记录映射出的受保护端点。
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EndpointAssignment {
    /// 统一为 IPv6 16 字节表示；IPv4 使用 IPv4 映射 IPv6。
    pub canonical_ip: [u8; 16],
    /// 相对于该端点的流方向。
    pub direction: EndpointDirection,
}

/// 真实原始列解析失败。
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ScreenSourceError {
    /// 微秒时间转换为纳秒时超出 i64 范围。
    TimestampOverflow { value: i64 },
    /// 外部标记为空。
    MissingExternalMarker {
        column: &'static str,
        source_row_index: u64,
    },
    /// 外部标记不是严格的 `0` 或 `1`。
    InvalidExternalMarker {
        value: String,
        column: &'static str,
        source_row_index: u64,
    },
    /// 内部端点 IP 缺失。
    MissingIpAddress {
        column: &'static str,
        source_row_index: u64,
    },
    /// 内部端点 IP 不是合法 IPv4 或 IPv6。
    InvalidIpAddress {
        value: String,
        column: &'static str,
        source_row_index: u64,
    },
    /// 特征列不是受支持的数值 Arrow 类型。
    UnsupportedNumericColumnType { column: String, actual: DataType },
}

impl Display for ScreenSourceError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::TimestampOverflow { value } => write!(formatter, "微秒时间转换溢出：{value}"),
            Self::MissingExternalMarker {
                column,
                source_row_index,
            } => write!(formatter, "外部标记 {column} 在源行 {source_row_index} 缺失"),
            Self::InvalidExternalMarker {
                value,
                column,
                source_row_index,
            } => write!(
                formatter,
                "外部标记 {column} 在源行 {source_row_index} 非法：{value}"
            ),
            Self::MissingIpAddress {
                column,
                source_row_index,
            } => write!(formatter, "内部端点 {column} 在源行 {source_row_index} 缺失"),
            Self::InvalidIpAddress {
                value,
                column,
                source_row_index,
            } => write!(
                formatter,
                "内部端点 {column} 在源行 {source_row_index} 非法：{value}"
            ),
            Self::UnsupportedNumericColumnType { column, actual } => {
                write!(formatter, "数值列 {column} 类型不受支持：{actual}")
            }
        }
    }
}

impl Error for ScreenSourceError {}

/// 将真实数据集的 UTC 微秒时间转换为 UTC 纳秒时间。
pub fn utc_ns_from_micros(value: i64) -> Result<i64, ScreenSourceError> {
    value
        .checked_mul(NS_PER_MICROSECOND)
        .ok_or(ScreenSourceError::TimestampOverflow { value })
}

/// 严格解析真实 Parquet 中以字符串存储的外部标记。
pub fn parse_external_marker(
    value: Option<&str>,
    column: &'static str,
    source_row_index: u64,
) -> Result<bool, ScreenSourceError> {
    match value {
        Some("0") => Ok(false),
        Some("1") => Ok(true),
        Some(value) => Err(ScreenSourceError::InvalidExternalMarker {
            value: value.to_owned(),
            column,
            source_row_index,
        }),
        None => Err(ScreenSourceError::MissingExternalMarker {
            column,
            source_row_index,
        }),
    }
}

/// 将内部端点展开为可重复排序的统一端点归属。
pub fn resolve_protected_endpoints(
    src_ip: Option<&str>,
    dst_ip: Option<&str>,
    external_src: Option<&str>,
    external_dst: Option<&str>,
    source_row_index: u64,
) -> Result<Vec<EndpointAssignment>, ScreenSourceError> {
    let external_src = parse_external_marker(external_src, "External_src", source_row_index)?;
    let external_dst = parse_external_marker(external_dst, "External_dst", source_row_index)?;
    let mut assignments = Vec::with_capacity(2);
    if !external_src {
        assignments.push(EndpointAssignment {
            canonical_ip: canonical_ip(src_ip, "SrcIP", source_row_index)?,
            direction: EndpointDirection::Outbound,
        });
    }
    if !external_dst {
        assignments.push(EndpointAssignment {
            canonical_ip: canonical_ip(dst_ip, "DstIP", source_row_index)?,
            direction: EndpointDirection::Inbound,
        });
    }
    Ok(assignments)
}

fn canonical_ip(
    value: Option<&str>,
    column: &'static str,
    source_row_index: u64,
) -> Result<[u8; 16], ScreenSourceError> {
    let value = value.ok_or(ScreenSourceError::MissingIpAddress {
        column,
        source_row_index,
    })?;
    let ip = value
        .parse::<IpAddr>()
        .map_err(|_| ScreenSourceError::InvalidIpAddress {
            value: value.to_owned(),
            column,
            source_row_index,
        })?;
    Ok(match ip {
        IpAddr::V4(value) => value.to_ipv6_mapped().octets(),
        IpAddr::V6(value) => value.octets(),
    })
}

/// 对真实模式中允许的数值 Arrow 数组的借用视图。
#[derive(Debug, Clone, Copy)]
pub enum NumericColumn<'a> {
    Int32(&'a Int32Array),
    Int64(&'a Int64Array),
    Float64(&'a Float64Array),
}

impl<'a> NumericColumn<'a> {
    /// 构造受支持类型的数值列视图。
    pub fn try_new(column: impl Into<String>, values: &'a dyn Array) -> Result<Self, ScreenSourceError> {
        if let Some(values) = values.as_any().downcast_ref::<Int32Array>() {
            return Ok(Self::Int32(values));
        }
        if let Some(values) = values.as_any().downcast_ref::<Int64Array>() {
            return Ok(Self::Int64(values));
        }
        if let Some(values) = values.as_any().downcast_ref::<Float64Array>() {
            return Ok(Self::Float64(values));
        }
        Err(ScreenSourceError::UnsupportedNumericColumnType {
            column: column.into(),
            actual: values.data_type().clone(),
        })
    }

    /// 返回有限 `f64`；空值和非有限浮点数显式表示为缺失。
    #[must_use]
    pub fn value_as_f64(&self, row: usize) -> Option<f64> {
        match self {
            Self::Int32(values) => (!values.is_null(row)).then(|| f64::from(values.value(row))),
            Self::Int64(values) => (!values.is_null(row)).then(|| values.value(row) as f64),
            Self::Float64(values) => (!values.is_null(row))
                .then(|| values.value(row))
                .filter(|value| value.is_finite()),
        }
    }

    /// 判断当前行是否因非有限浮点数进入隔离。
    #[must_use]
    pub fn is_non_finite(&self, row: usize) -> bool {
        matches!(self, Self::Float64(values) if !values.is_null(row) && !values.value(row).is_finite())
    }
}
