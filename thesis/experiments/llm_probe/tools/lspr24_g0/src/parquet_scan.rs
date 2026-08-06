//! Parquet 时间列的顺序流式扫描。

use std::error::Error;
use std::fmt::{Display, Formatter};
use std::fs::File;
use std::path::{Path, PathBuf};

use arrow_array::{Array, Int64Array, RecordBatch};
use arrow_schema::ArrowError;
use parquet::arrow::ProjectionMask;
use parquet::arrow::arrow_reader::{
    ParquetRecordBatchReader, ParquetRecordBatchReaderBuilder,
};
use parquet::errors::ParquetError;

use crate::config::ScanConfig;
use crate::input::{
    InputSchemaError, TIMESTAMP_LAST_COLUMN, TIMESTAMP_START_COLUMN,
    required_time_column_indices,
};

/// 一条物理源记录的时间值与零基全局行号。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TimeRow {
    /// 过滤、隔离或去重之前的 Parquet 物理行号。
    pub source_row_index: u64,
    /// 原始流起始时间；空值保持为空。
    pub timestamp_start: Option<i64>,
    /// 原始流结束时间；空值保持为空。
    pub timestamp_last: Option<i64>,
}

impl TimeRow {
    /// 创建一条时间扫描记录。
    #[must_use]
    pub const fn new(
        source_row_index: u64,
        timestamp_start: Option<i64>,
        timestamp_last: Option<i64>,
    ) -> Self {
        Self {
            source_row_index,
            timestamp_start,
            timestamp_last,
        }
    }
}

/// 时间列扫描失败。
#[derive(Debug)]
pub enum ScanError {
    /// 无法打开输入文件。
    OpenInput {
        path: PathBuf,
        source: std::io::Error,
    },
    /// 无法读取 Parquet 元数据。
    ReadMetadata(ParquetError),
    /// 输入时间列模式不满足冻结约束。
    InputSchema(InputSchemaError),
    /// Parquet 元数据给出了负行数。
    NegativeRowCount { actual: i64 },
    /// 无法构建投影读取器。
    BuildReader(ParquetError),
    /// 无法读取下一个 Arrow 批。
    ReadBatch(ArrowError),
    /// 投影批包含了时间列之外的列。
    UnexpectedProjectedColumnCount { actual: usize },
    /// 投影数组与已验证模式不一致。
    UnexpectedProjectedArrayType { column: &'static str },
    /// 读取行数超过 Parquet 元数据声明值。
    RowCountExceeded { expected: u64 },
    /// 读取结束时的行数与 Parquet 元数据不一致。
    RowCountMismatch { expected: u64, actual: u64 },
    /// 全局物理行号无法继续递增。
    SourceRowIndexOverflow,
}

impl Display for ScanError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::OpenInput { path, .. } => {
                write!(formatter, "无法打开 Parquet 输入 {}", path.display())
            }
            Self::ReadMetadata(_) => write!(formatter, "无法读取 Parquet 元数据"),
            Self::InputSchema(error) => write!(formatter, "输入时间列模式错误：{error}"),
            Self::NegativeRowCount { actual } => {
                write!(formatter, "Parquet 元数据行数不能为负数：{actual}")
            }
            Self::BuildReader(_) => write!(formatter, "无法构建 Parquet 时间列投影读取器"),
            Self::ReadBatch(_) => write!(formatter, "无法读取 Parquet 时间列批"),
            Self::UnexpectedProjectedColumnCount { actual } => {
                write!(formatter, "时间列投影应包含 2 列，实际为 {actual} 列")
            }
            Self::UnexpectedProjectedArrayType { column } => {
                write!(formatter, "投影时间列 {column} 的数组类型不是 Int64")
            }
            Self::RowCountExceeded { expected } => {
                write!(formatter, "扫描行数超过 Parquet 元数据声明值 {expected}")
            }
            Self::RowCountMismatch { expected, actual } => write!(
                formatter,
                "扫描行数与 Parquet 元数据不一致：期望 {expected}，实际 {actual}"
            ),
            Self::SourceRowIndexOverflow => write!(formatter, "全局物理行号溢出"),
        }
    }
}

impl Error for ScanError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::OpenInput { source, .. } => Some(source),
            Self::ReadMetadata(source) | Self::BuildReader(source) => Some(source),
            Self::InputSchema(source) => Some(source),
            Self::ReadBatch(source) => Some(source),
            Self::NegativeRowCount { .. }
            | Self::UnexpectedProjectedColumnCount { .. }
            | Self::UnexpectedProjectedArrayType { .. }
            | Self::RowCountExceeded { .. }
            | Self::RowCountMismatch { .. }
            | Self::SourceRowIndexOverflow => None,
        }
    }
}

/// 顺序产出两个时间列及其全局物理行号的流式读取器。
pub struct TimeRowReader {
    reader: ParquetRecordBatchReader,
    current_batch: Option<BatchCursor>,
    next_source_row_index: u64,
    expected_rows: u64,
    finished: bool,
}

impl TimeRowReader {
    /// 打开 Parquet，并在读取任何记录前验证和投影时间列。
    ///
    /// # Errors
    ///
    /// 文件不可读、模式不匹配、行数非法或投影读取器构建失败时返回错误。
    pub fn try_new(path: impl AsRef<Path>, config: ScanConfig) -> Result<Self, ScanError> {
        let path = path.as_ref();
        let file = File::open(path).map_err(|source| ScanError::OpenInput {
            path: path.to_path_buf(),
            source,
        })?;
        let builder = ParquetRecordBatchReaderBuilder::try_new(file)
            .map_err(ScanError::ReadMetadata)?;
        let time_column_indices = required_time_column_indices(builder.schema())
            .map_err(ScanError::InputSchema)?;
        let projection = ProjectionMask::roots(builder.parquet_schema(), time_column_indices);
        let metadata_rows = builder.metadata().file_metadata().num_rows();
        let expected_rows = u64::try_from(metadata_rows)
            .map_err(|_| ScanError::NegativeRowCount { actual: metadata_rows })?;
        let reader = builder
            .with_projection(projection)
            .with_batch_size(config.batch_size())
            .build()
            .map_err(ScanError::BuildReader)?;

        Ok(Self {
            reader,
            current_batch: None,
            next_source_row_index: 0,
            expected_rows,
            finished: false,
        })
    }

    fn fail(&mut self, error: ScanError) -> Option<Result<TimeRow, ScanError>> {
        self.finished = true;
        self.current_batch = None;
        Some(Err(error))
    }
}

impl Iterator for TimeRowReader {
    type Item = Result<TimeRow, ScanError>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.finished {
            return None;
        }

        loop {
            if let Some((timestamp_start, timestamp_last)) = self
                .current_batch
                .as_mut()
                .and_then(BatchCursor::next_values)
            {
                if self.next_source_row_index >= self.expected_rows {
                    return self.fail(ScanError::RowCountExceeded {
                        expected: self.expected_rows,
                    });
                }
                let source_row_index = self.next_source_row_index;
                let Some(next_source_row_index) = source_row_index.checked_add(1) else {
                    return self.fail(ScanError::SourceRowIndexOverflow);
                };
                self.next_source_row_index = next_source_row_index;
                return Some(Ok(TimeRow::new(
                    source_row_index,
                    timestamp_start,
                    timestamp_last,
                )));
            }
            self.current_batch = None;

            match self.reader.next() {
                Some(Ok(batch)) => match BatchCursor::try_new(batch) {
                    Ok(cursor) => self.current_batch = Some(cursor),
                    Err(error) => return self.fail(error),
                },
                Some(Err(error)) => return self.fail(ScanError::ReadBatch(error)),
                None => {
                    self.finished = true;
                    if self.next_source_row_index != self.expected_rows {
                        return Some(Err(ScanError::RowCountMismatch {
                            expected: self.expected_rows,
                            actual: self.next_source_row_index,
                        }));
                    }
                    return None;
                }
            }
        }
    }
}

struct BatchCursor {
    timestamp_start: Int64Array,
    timestamp_last: Int64Array,
    row_offset: usize,
    row_count: usize,
}

impl BatchCursor {
    fn try_new(batch: RecordBatch) -> Result<Self, ScanError> {
        if batch.num_columns() != 2 {
            return Err(ScanError::UnexpectedProjectedColumnCount {
                actual: batch.num_columns(),
            });
        }
        let [timestamp_start_index, timestamp_last_index] =
            required_time_column_indices(batch.schema().as_ref())
                .map_err(ScanError::InputSchema)?;
        let timestamp_start = batch
            .column(timestamp_start_index)
            .as_any()
            .downcast_ref::<Int64Array>()
            .ok_or(ScanError::UnexpectedProjectedArrayType {
                column: TIMESTAMP_START_COLUMN,
            })?
            .clone();
        let timestamp_last = batch
            .column(timestamp_last_index)
            .as_any()
            .downcast_ref::<Int64Array>()
            .ok_or(ScanError::UnexpectedProjectedArrayType {
                column: TIMESTAMP_LAST_COLUMN,
            })?
            .clone();

        Ok(Self {
            timestamp_start,
            timestamp_last,
            row_offset: 0,
            row_count: batch.num_rows(),
        })
    }

    fn next_values(&mut self) -> Option<(Option<i64>, Option<i64>)> {
        if self.row_offset >= self.row_count {
            return None;
        }
        let row_offset = self.row_offset;
        self.row_offset = self
            .row_offset
            .checked_add(1)
            .expect("批内偏移小于批行数时递增不得溢出");

        Some((
            (!self.timestamp_start.is_null(row_offset))
                .then(|| self.timestamp_start.value(row_offset)),
            (!self.timestamp_last.is_null(row_offset))
                .then(|| self.timestamp_last.value(row_offset)),
        ))
    }
}
