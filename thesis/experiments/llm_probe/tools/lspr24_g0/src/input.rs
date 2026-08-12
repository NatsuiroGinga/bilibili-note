//! 输入时间列名称与模式校验。

use std::error::Error;
use std::fmt::{Display, Formatter};

use arrow_schema::{DataType, Schema};

/// 流起始时间列的冻结名称。
pub const TIMESTAMP_START_COLUMN: &str = "mTimestampStart";
/// 流结束时间列的冻结名称。
pub const TIMESTAMP_LAST_COLUMN: &str = "mTimestampLast";
/// 第一遍扫描唯一允许投影的列。
pub const TIME_COLUMN_NAMES: [&str; 2] = [TIMESTAMP_START_COLUMN, TIMESTAMP_LAST_COLUMN];

/// 输入 Parquet 的时间列模式错误。
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum InputSchemaError {
    /// 缺少必需列。
    MissingColumn { column: &'static str },
    /// 同名必需列不唯一。
    DuplicateColumn { column: &'static str },
    /// 必需列不是冻结的 `Int64` 类型。
    UnexpectedType {
        column: &'static str,
        actual: DataType,
    },
    /// 必需列未声明为可空。
    NonNullableColumn { column: &'static str },
}

impl Display for InputSchemaError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::MissingColumn { column } => write!(formatter, "缺少必需时间列 {column}"),
            Self::DuplicateColumn { column } => write!(formatter, "必需时间列 {column} 不唯一"),
            Self::UnexpectedType { column, actual } => {
                write!(formatter, "时间列 {column} 必须为 Int64，实际为 {actual}")
            }
            Self::NonNullableColumn { column } => {
                write!(formatter, "时间列 {column} 必须声明为可空")
            }
        }
    }
}

impl Error for InputSchemaError {}

pub(crate) fn required_time_column_indices(
    schema: &Schema,
) -> Result<[usize; 2], InputSchemaError> {
    Ok([
        required_column_index(schema, TIMESTAMP_START_COLUMN)?,
        required_column_index(schema, TIMESTAMP_LAST_COLUMN)?,
    ])
}

fn required_column_index(schema: &Schema, column: &'static str) -> Result<usize, InputSchemaError> {
    let mut matches = schema
        .fields()
        .iter()
        .enumerate()
        .filter(|(_, field)| field.name() == column);
    let (index, field) = matches
        .next()
        .ok_or(InputSchemaError::MissingColumn { column })?;
    if matches.next().is_some() {
        return Err(InputSchemaError::DuplicateColumn { column });
    }
    if field.data_type() != &DataType::Int64 {
        return Err(InputSchemaError::UnexpectedType {
            column,
            actual: field.data_type().clone(),
        });
    }
    if !field.is_nullable() {
        return Err(InputSchemaError::NonNullableColumn { column });
    }

    Ok(index)
}
