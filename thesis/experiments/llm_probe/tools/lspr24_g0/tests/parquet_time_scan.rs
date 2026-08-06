use std::fs::{File, OpenOptions};
use std::num::NonZeroUsize;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

use arrow_array::{ArrayRef, Int32Array, Int64Array, RecordBatch, StringArray};
use arrow_schema::{DataType, Field, Schema};
use lspr24_g0::{
    InputSchemaError, ScanConfig, ScanError, TIMESTAMP_LAST_COLUMN, TimeRow, TimeRowReader,
};
use parquet::arrow::ArrowWriter;
use parquet::file::properties::WriterProperties;

static NEXT_FIXTURE_ID: AtomicU64 = AtomicU64::new(0);

struct ParquetFixture {
    path: PathBuf,
}

impl ParquetFixture {
    fn create() -> (Self, File) {
        let fixture_id = NEXT_FIXTURE_ID.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "lspr24-g0-parquet-time-scan-{}-{fixture_id}.parquet",
            std::process::id()
        ));
        let file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&path)
            .expect("应能创建唯一的人工 Parquet 夹具");

        (Self { path }, file)
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for ParquetFixture {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.path);
    }
}

fn write_fixture(batch: &RecordBatch, max_row_group_size: usize) -> ParquetFixture {
    let (fixture, file) = ParquetFixture::create();
    let properties = WriterProperties::builder()
        .set_max_row_group_size(max_row_group_size)
        .build();
    let mut writer = ArrowWriter::try_new(file, batch.schema(), Some(properties))
        .expect("人工夹具模式应可写入 Parquet");
    writer.write(batch).expect("人工夹具数据应可写入");
    writer.close().expect("人工夹具应能完成写入");
    fixture
}

fn valid_batch() -> RecordBatch {
    let schema = Arc::new(Schema::new(vec![
        Field::new("unusedText", DataType::Utf8, false),
        Field::new("mTimestampLast", DataType::Int64, true),
        Field::new("mTimestampStart", DataType::Int64, true),
    ]));
    RecordBatch::try_new(
        schema,
        vec![
            Arc::new(StringArray::from(vec!["a", "b", "c", "d", "e"])) as ArrayRef,
            Arc::new(Int64Array::from(vec![
                Some(11),
                Some(21),
                None,
                Some(41),
                None,
            ])) as ArrayRef,
            Arc::new(Int64Array::from(vec![
                Some(10),
                None,
                Some(30),
                Some(40),
                None,
            ])) as ArrayRef,
        ],
    )
    .expect("人工有效批应满足模式")
}

fn collect_rows(path: &Path, batch_size: usize) -> Vec<TimeRow> {
    let config = ScanConfig::new(NonZeroUsize::new(batch_size).expect("测试批大小必须非零"));
    TimeRowReader::try_new(path, config)
        .expect("有效人工夹具应能打开")
        .collect::<Result<Vec<_>, _>>()
        .expect("有效人工夹具应能完整扫描")
}

#[test]
fn named_time_columns_keep_global_indices_across_batches_nulls_and_row_groups() {
    let fixture = write_fixture(&valid_batch(), 2);
    let expected = vec![
        TimeRow::new(0, Some(10), Some(11)),
        TimeRow::new(1, None, Some(21)),
        TimeRow::new(2, Some(30), None),
        TimeRow::new(3, Some(40), Some(41)),
        TimeRow::new(4, None, None),
    ];

    let one_row_batches = collect_rows(fixture.path(), 1);
    let three_row_batches = collect_rows(fixture.path(), 3);
    let oversized_batches = collect_rows(fixture.path(), 65_536);

    assert_eq!(one_row_batches, expected);
    assert_eq!(three_row_batches, expected);
    assert_eq!(oversized_batches, expected);
}

#[test]
fn missing_required_time_column_is_rejected_before_scanning() {
    let schema = Arc::new(Schema::new(vec![
        Field::new("mTimestampStart", DataType::Int64, true),
        Field::new("unusedText", DataType::Utf8, false),
    ]));
    let batch = RecordBatch::try_new(
        schema,
        vec![
            Arc::new(Int64Array::from(vec![Some(10)])) as ArrayRef,
            Arc::new(StringArray::from(vec!["x"])) as ArrayRef,
        ],
    )
    .expect("人工缺列批应能写入");
    let fixture = write_fixture(&batch, 1);
    let config = ScanConfig::new(NonZeroUsize::new(1).expect("测试批大小必须非零"));

    let error = match TimeRowReader::try_new(fixture.path(), config) {
        Err(error) => error,
        Ok(_) => panic!("缺少必需时间列时必须失败"),
    };

    assert!(matches!(
        error,
        ScanError::InputSchema(InputSchemaError::MissingColumn { column })
            if column == TIMESTAMP_LAST_COLUMN
    ));
}

#[test]
fn non_int64_time_column_is_rejected_before_scanning() {
    let schema = Arc::new(Schema::new(vec![
        Field::new("mTimestampStart", DataType::Int32, true),
        Field::new("mTimestampLast", DataType::Int64, true),
    ]));
    let batch = RecordBatch::try_new(
        schema,
        vec![
            Arc::new(Int32Array::from(vec![Some(10)])) as ArrayRef,
            Arc::new(Int64Array::from(vec![Some(11)])) as ArrayRef,
        ],
    )
    .expect("人工错类型批应能写入");
    let fixture = write_fixture(&batch, 1);
    let config = ScanConfig::new(NonZeroUsize::new(1).expect("测试批大小必须非零"));

    let error = match TimeRowReader::try_new(fixture.path(), config) {
        Err(error) => error,
        Ok(_) => panic!("时间列不是 Int64 时必须失败"),
    };

    assert!(matches!(
        error,
        ScanError::InputSchema(InputSchemaError::UnexpectedType { column, actual })
            if column == "mTimestampStart" && actual == DataType::Int32
    ));
}

