//! 任务 1 合同测试：页脚级模式审计、schema_sha256 金标准与去重投影清单。

mod common;

use std::collections::BTreeSet;
use std::fs::{File, OpenOptions};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

use arrow_array::{ArrayRef, Float64Array, Int32Array, Int64Array, RecordBatch, StringArray};
use arrow_schema::{DataType, Field, Schema};
use lspr24_g0::{
    AuditedColumn, LSPR24_EXPECTED_COLUMN_COUNT, LSPR24_EXPECTED_ROW_COUNT, SchemaAudit,
    SchemaAuditError, arrow_type_name,
};
use parquet::arrow::ArrowWriter;

/// 4 列合成模式的 schema_sha256 金标准，由独立 Python 参考实现按
/// `tuple_encode([Utf8(列名), Utf8(类型名)] 逐列展开)` 计算。
const SYNTHETIC_SCHEMA_SHA256: &str =
    "b88b3df6dcd870c99a5eb6e2bee649eb1ec5fa6da27985cf168b923bd7c772cb";
/// 真实 101 列模式的 schema_sha256 金标准，由同一独立 Python 参考实现计算。
const FROZEN_SCHEMA_SHA256: &str =
    "184f21952f7bff184e711f231bdb8232a3f1d3085bed0939b35d4b9f1b5cf349";
/// 合同 §6.2 要求在去重内容投影中剔除的标签与 IDS 列。
const EXPECTED_EXCLUDED_COLUMNS: [&str; 7] = [
    "Anomaly_event",
    "Category",
    "Label",
    "Label_dst",
    "Label_src",
    "Severity",
    "SigID revision",
];

static NEXT_FIXTURE_ID: AtomicU64 = AtomicU64::new(0);

struct ParquetFixture {
    path: PathBuf,
}

impl ParquetFixture {
    fn create() -> (Self, File) {
        let fixture_id = NEXT_FIXTURE_ID.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "lspr24-g0-schema-audit-{}-{fixture_id}.parquet",
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

fn write_four_column_fixture() -> ParquetFixture {
    let schema = Arc::new(Schema::new(vec![
        Field::new("Flow ID", DataType::Utf8, true),
        Field::new("mTimestampStart", DataType::Int64, true),
        Field::new("Tot Fwd Pkts", DataType::Int32, true),
        Field::new("Flow Bytes/s", DataType::Float64, true),
    ]));
    let batch = RecordBatch::try_new(
        schema,
        vec![
            Arc::new(StringArray::from(vec![Some("a"), Some("b")])) as ArrayRef,
            Arc::new(Int64Array::from(vec![Some(1), Some(2)])) as ArrayRef,
            Arc::new(Int32Array::from(vec![Some(3), Some(4)])) as ArrayRef,
            Arc::new(Float64Array::from(vec![Some(5.0), Some(6.0)])) as ArrayRef,
        ],
    )
    .expect("人工 4 列批应满足模式");
    let (fixture, file) = ParquetFixture::create();
    let mut writer =
        ArrowWriter::try_new(file, batch.schema(), None).expect("人工夹具模式应可写入 Parquet");
    writer.write(&batch).expect("人工夹具数据应可写入");
    writer.close().expect("人工夹具应能完成写入");
    fixture
}

fn synthetic_columns() -> Vec<AuditedColumn> {
    vec![
        AuditedColumn::new(0, "Flow ID".to_owned(), "Utf8".to_owned(), true),
        AuditedColumn::new(1, "mTimestampStart".to_owned(), "Int64".to_owned(), true),
        AuditedColumn::new(2, "Tot Fwd Pkts".to_owned(), "Int32".to_owned(), true),
        AuditedColumn::new(3, "Flow Bytes/s".to_owned(), "Float64".to_owned(), true),
    ]
}

fn encode_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[test]
fn footer_audit_rejects_column_count_other_than_frozen_value() {
    let fixture = write_four_column_fixture();

    let error = match SchemaAudit::from_parquet_footer(fixture.path()) {
        Err(error) => error,
        Ok(_) => panic!("列数不等于冻结值时必须失败"),
    };

    assert!(
        matches!(
            error,
            SchemaAuditError::UnexpectedColumnCount { expected, actual }
                if expected == LSPR24_EXPECTED_COLUMN_COUNT && actual == 4
        ),
        "实际错误：{error}"
    );
}

#[test]
fn arrow_type_names_match_frozen_strings() {
    assert_eq!(arrow_type_name(&DataType::Utf8), "Utf8");
    assert_eq!(arrow_type_name(&DataType::Int32), "Int32");
    assert_eq!(arrow_type_name(&DataType::Int64), "Int64");
    assert_eq!(arrow_type_name(&DataType::Float64), "Float64");
}

#[test]
fn schema_sha256_matches_independently_computed_golden() {
    let audit = SchemaAudit::from_columns("synthetic.parquet".to_owned(), 2, 1, synthetic_columns())
        .expect("合成 4 列审计应可构造");

    assert_eq!(encode_hex(&audit.schema_sha256()), SYNTHETIC_SCHEMA_SHA256);
}

#[test]
fn frozen_catalog_matches_golden_hash_and_round_trips() {
    let audit = common::load_frozen_schema_audit();

    assert_eq!(audit.columns().len(), LSPR24_EXPECTED_COLUMN_COUNT);
    assert_eq!(audit.row_count(), LSPR24_EXPECTED_ROW_COUNT);
    assert_eq!(audit.row_group_count(), 21);
    assert_eq!(encode_hex(&audit.schema_sha256()), FROZEN_SCHEMA_SHA256);

    let serialized = audit.to_json_bytes().expect("模式审计应可序列化");
    let reparsed = SchemaAudit::from_json(&serialized).expect("模式审计应可往返解析");
    assert_eq!(reparsed.columns(), audit.columns());
    assert_eq!(reparsed.schema_sha256(), audit.schema_sha256());
    assert_eq!(
        reparsed.to_json_bytes().expect("往返后仍应可序列化"),
        serialized
    );
}

#[test]
fn tampered_schema_hash_is_rejected_on_parse() {
    let bytes = common::frozen_schema_audit_bytes();
    let text = String::from_utf8(bytes).expect("夹具应为 UTF-8");
    let tampered = text.replace(FROZEN_SCHEMA_SHA256, &format!("0{}", &FROZEN_SCHEMA_SHA256[1..]));
    assert_ne!(tampered, text, "篡改替换必须真实发生");

    let error = match SchemaAudit::from_json(tampered.as_bytes()) {
        Err(error) => error,
        Ok(_) => panic!("schema_sha256 被篡改时必须失败"),
    };

    assert!(
        matches!(error, SchemaAuditError::SchemaHashMismatch { .. }),
        "实际错误：{error}"
    );
}

#[test]
fn dedup_projection_manifest_excludes_exactly_label_and_ids_columns() {
    let audit = common::load_frozen_schema_audit();

    let manifest = audit.dedup_projection_manifest();
    let excluded: BTreeSet<&str> = manifest
        .excluded_columns()
        .iter()
        .map(|column| column.name.as_str())
        .collect();
    let expected: BTreeSet<&str> = EXPECTED_EXCLUDED_COLUMNS.into_iter().collect();

    assert_eq!(excluded, expected);
    assert_eq!(
        manifest.content_columns().len(),
        LSPR24_EXPECTED_COLUMN_COUNT - EXPECTED_EXCLUDED_COLUMNS.len()
    );
    for column in manifest.content_columns() {
        assert!(
            !expected.contains(column.name.as_str()),
            "内容投影不得包含被剔除列 {}",
            column.name
        );
    }
    let content_indices: Vec<usize> = manifest
        .content_columns()
        .iter()
        .map(|column| column.index)
        .collect();
    let mut sorted = content_indices.clone();
    sorted.sort_unstable();
    assert_eq!(content_indices, sorted, "内容投影必须保持源列顺序");
    assert!(
        manifest
            .excluded_columns()
            .iter()
            .all(|column| !column.reason.is_empty()),
        "每个被剔除列必须记录原因"
    );
}
