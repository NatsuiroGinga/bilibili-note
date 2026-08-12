use std::error::Error;
use std::fmt::{Display, Formatter};
use std::fs::{self, File, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::sync::Arc;

use arrow_array::{
    ArrayRef, BooleanArray, Float64Array, Int32Array, RecordBatch, StringArray, UInt32Array,
    UInt64Array,
};
use arrow_schema::{DataType, Field, Schema};
use parquet::arrow::ArrowWriter;
use serde::Serialize;

use super::history::HistoryRelationRow;
use super::wide::{DevelopmentWideReceipt, WideRow};
use crate::FieldManifestEntry;

/// 宽表输出失败。
#[derive(Debug)]
pub enum ScreenOutputError {
    AlreadyExists(PathBuf),
    Io { path: PathBuf, source: io::Error },
    Parquet(String),
    Json(String),
    Schema(String),
}

impl Display for ScreenOutputError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::AlreadyExists(path) => write!(formatter, "输出路径已存在：{}", path.display()),
            Self::Io { path, source } => {
                write!(formatter, "输出 {} 失败：{source}", path.display())
            }
            Self::Parquet(message) => write!(formatter, "Parquet 输出失败：{message}"),
            Self::Json(message) => write!(formatter, "JSON 输出失败：{message}"),
            Self::Schema(message) => write!(formatter, "输出模式错误：{message}"),
        }
    }
}

impl Error for ScreenOutputError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Io { source, .. } => Some(source),
            _ => None,
        }
    }
}

pub(crate) struct DevelopmentParquetWriters {
    wide_writer: ArrowWriter<File>,
    label_writer: ArrowWriter<File>,
    history_writer: ArrowWriter<File>,
    wide_output: ExclusiveFile,
    label_output: ExclusiveFile,
    history_output: ExclusiveFile,
    wide_schema: Arc<Schema>,
    label_schema: Arc<Schema>,
    history_schema: Arc<Schema>,
}

impl DevelopmentParquetWriters {
    pub(crate) fn create(
        wide_path: &Path,
        label_path: &Path,
        history_path: &Path,
        entries: &[FieldManifestEntry],
    ) -> Result<Self, ScreenOutputError> {
        let wide_schema = wide_schema(entries);
        let label_schema = Arc::new(Schema::new(vec![
            Field::new("window_row_index", DataType::UInt64, false),
            Field::new("label", DataType::Int32, false),
        ]));
        let history_schema = Arc::new(Schema::new(vec![
            Field::new("horizon", DataType::UInt32, false),
            Field::new("target_window_row_index", DataType::UInt64, false),
            Field::new("next_window_row_index", DataType::UInt64, true),
            Field::new("lag", DataType::UInt32, false),
            Field::new("history_window_row_index", DataType::UInt64, false),
        ]));
        let (wide_output, wide_writer) = create_parquet_writer(wide_path, wide_schema.clone())?;
        let (label_output, label_writer) = create_parquet_writer(label_path, label_schema.clone())?;
        let (history_output, history_writer) =
            create_parquet_writer(history_path, history_schema.clone())?;
        Ok(Self {
            wide_writer,
            label_writer,
            history_writer,
            wide_output,
            label_output,
            history_output,
            wide_schema,
            label_schema,
            history_schema,
        })
    }

    pub(crate) fn write_rows(
        &mut self,
        entries: &[FieldManifestEntry],
        rows: &[WideRow],
    ) -> Result<(), ScreenOutputError> {
        if rows.is_empty() {
            return Ok(());
        }
        let mut columns: Vec<ArrayRef> = vec![
            Arc::new(UInt64Array::from_iter_values(
                rows.iter().map(|row| row.window_row_index),
            )),
            Arc::new(arrow_array::Int64Array::from_iter_values(
                rows.iter().map(|row| row.window_start_ns),
            )),
            Arc::new(arrow_array::Int64Array::from_iter_values(
                rows.iter().map(|row| row.window_end_ns),
            )),
            Arc::new(StringArray::from_iter_values(
                rows.iter()
                    .map(|row| row.protected_endpoint_sha256.as_str()),
            )),
            Arc::new(StringArray::from_iter_values(
                rows.iter().map(|row| row.split_name.as_str()),
            )),
            Arc::new(BooleanArray::from_iter(
                rows.iter().map(|row| Some(row.has_activity)),
            )),
            Arc::new(arrow_array::Int64Array::from_iter_values(
                rows.iter()
                    .map(|row| row.seconds_since_previous_active_window),
            )),
            Arc::new(UInt64Array::from_iter_values(
                rows.iter().map(|row| row.consecutive_empty_window_count),
            )),
        ];
        for feature_index in 0..entries.len() {
            columns.push(Arc::new(Float64Array::from_iter_values(
                rows.iter().map(|row| row.features[feature_index]),
            )));
        }
        let wide_batch = RecordBatch::try_new(self.wide_schema.clone(), columns)
            .map_err(|error| ScreenOutputError::Schema(error.to_string()))?;
        self.wide_writer
            .write(&wide_batch)
            .map_err(|error| ScreenOutputError::Parquet(error.to_string()))?;

        let label_batch = RecordBatch::try_new(
            self.label_schema.clone(),
            vec![
                Arc::new(UInt64Array::from_iter_values(
                    rows.iter().map(|row| row.window_row_index),
                )) as ArrayRef,
                Arc::new(Int32Array::from_iter_values(
                    rows.iter().map(|row| row.label),
                )) as ArrayRef,
            ],
        )
        .map_err(|error| ScreenOutputError::Schema(error.to_string()))?;
        self.label_writer
            .write(&label_batch)
            .map_err(|error| ScreenOutputError::Parquet(error.to_string()))
    }

    pub(crate) fn write_history(
        &mut self,
        rows: &[HistoryRelationRow],
    ) -> Result<(), ScreenOutputError> {
        if rows.is_empty() {
            return Ok(());
        }
        let batch = RecordBatch::try_new(
            self.history_schema.clone(),
            vec![
                Arc::new(UInt32Array::from_iter_values(
                    rows.iter().map(|row| row.horizon),
                )) as ArrayRef,
                Arc::new(UInt64Array::from_iter_values(
                    rows.iter().map(|row| row.target_window_row_index),
                )) as ArrayRef,
                Arc::new(UInt64Array::from_iter(
                    rows.iter().map(|row| row.next_window_row_index),
                )) as ArrayRef,
                Arc::new(UInt32Array::from_iter_values(
                    rows.iter().map(|row| row.lag),
                )) as ArrayRef,
                Arc::new(UInt64Array::from_iter_values(
                    rows.iter().map(|row| row.history_window_row_index),
                )) as ArrayRef,
            ],
        )
        .map_err(|error| ScreenOutputError::Schema(error.to_string()))?;
        self.history_writer
            .write(&batch)
            .map_err(|error| ScreenOutputError::Parquet(error.to_string()))
    }

    pub(crate) fn finish(mut self) -> Result<(), ScreenOutputError> {
        self.wide_writer
            .close()
            .map_err(|error| ScreenOutputError::Parquet(error.to_string()))?;
        self.label_writer
            .close()
            .map_err(|error| ScreenOutputError::Parquet(error.to_string()))?;
        self.history_writer
            .close()
            .map_err(|error| ScreenOutputError::Parquet(error.to_string()))?;
        self.wide_output.commit()?;
        self.label_output.commit()?;
        self.history_output.commit()
    }
}

fn wide_schema(entries: &[FieldManifestEntry]) -> Arc<Schema> {
    let mut fields = vec![
        Field::new("window_row_index", DataType::UInt64, false),
        Field::new("window_start_ns", DataType::Int64, false),
        Field::new("window_end_ns", DataType::Int64, false),
        Field::new("protected_endpoint_sha256", DataType::Utf8, false),
        Field::new("split_name", DataType::Utf8, false),
        Field::new("has_activity", DataType::Boolean, false),
        Field::new(
            "seconds_since_previous_active_window",
            DataType::Int64,
            false,
        ),
        Field::new("consecutive_empty_window_count", DataType::UInt64, false),
    ];
    fields.extend(
        entries
            .iter()
            .map(|entry| Field::new(&entry.output_name, DataType::Float64, false)),
    );
    Arc::new(Schema::new(fields))
}

pub(crate) fn write_receipt_json(
    path: &Path,
    receipt: &DevelopmentWideReceipt,
) -> Result<(), ScreenOutputError> {
    write_json_document(path, receipt)
}

pub(crate) fn write_json_document<T: Serialize>(
    path: &Path,
    value: &T,
) -> Result<(), ScreenOutputError> {
    let mut bytes = serde_json::to_vec_pretty(value)
        .map_err(|error| ScreenOutputError::Json(error.to_string()))?;
    bytes.push(b'\n');
    write_exclusive(path, &bytes)
}

fn write_exclusive(path: &Path, bytes: &[u8]) -> Result<(), ScreenOutputError> {
    let mut output = ExclusiveFile::create(path)?;
    output.write_all(bytes)?;
    output.commit()
}

fn create_parquet_writer(
    path: &Path,
    schema: Arc<Schema>,
) -> Result<(ExclusiveFile, ArrowWriter<File>), ScreenOutputError> {
    let mut output = ExclusiveFile::create(path)?;
    let file = output.take_file()?;
    let writer = ArrowWriter::try_new(file, schema, None)
        .map_err(|error| ScreenOutputError::Parquet(error.to_string()))?;
    Ok((output, writer))
}

struct ExclusiveFile {
    formal_path: PathBuf,
    partial_path: PathBuf,
    file: Option<File>,
    committed: bool,
}

impl ExclusiveFile {
    fn create(path: &Path) -> Result<Self, ScreenOutputError> {
        reject_existing(path)?;
        let partial_path = partial_path(path);
        reject_existing(&partial_path)?;
        let file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&partial_path)
            .map_err(|source| map_io(&partial_path, source))?;
        Ok(Self {
            formal_path: path.to_path_buf(),
            partial_path,
            file: Some(file),
            committed: false,
        })
    }

    fn take_file(&mut self) -> Result<File, ScreenOutputError> {
        self.file.take().ok_or_else(|| ScreenOutputError::Io {
            path: self.partial_path.clone(),
            source: io::Error::other("暂存输出已关闭"),
        })
    }

    fn write_all(&mut self, bytes: &[u8]) -> Result<(), ScreenOutputError> {
        let file = self.file.as_mut().ok_or_else(|| ScreenOutputError::Io {
            path: self.partial_path.clone(),
            source: io::Error::other("暂存输出已关闭"),
        })?;
        file.write_all(bytes)
            .map_err(|source| map_io(&self.partial_path, source))
    }

    fn commit(mut self) -> Result<(), ScreenOutputError> {
        if let Some(file) = self.file.take() {
            file.sync_all()
                .map_err(|source| map_io(&self.partial_path, source))?;
        } else {
            File::open(&self.partial_path)
                .and_then(|file| file.sync_all())
                .map_err(|source| map_io(&self.partial_path, source))?;
        }
        fs::hard_link(&self.partial_path, &self.formal_path)
            .map_err(|source| map_io(&self.formal_path, source))?;
        fs::remove_file(&self.partial_path).map_err(|source| map_io(&self.partial_path, source))?;
        self.committed = true;
        Ok(())
    }
}

impl Drop for ExclusiveFile {
    fn drop(&mut self) {
        if !self.committed {
            let _ = fs::remove_file(&self.formal_path);
            let _ = fs::remove_file(&self.partial_path);
        }
    }
}

fn reject_existing(path: &Path) -> Result<(), ScreenOutputError> {
    match fs::symlink_metadata(path) {
        Ok(_) => Err(ScreenOutputError::AlreadyExists(path.to_path_buf())),
        Err(source) if source.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(source) => Err(map_io(path, source)),
    }
}

fn partial_path(path: &Path) -> PathBuf {
    let mut value = path.as_os_str().to_os_string();
    value.push(".partial");
    PathBuf::from(value)
}

fn map_io(path: &Path, source: io::Error) -> ScreenOutputError {
    if source.kind() == io::ErrorKind::AlreadyExists {
        ScreenOutputError::AlreadyExists(path.to_path_buf())
    } else {
        ScreenOutputError::Io {
            path: path.to_path_buf(),
            source,
        }
    }
}
