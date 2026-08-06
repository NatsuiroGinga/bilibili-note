use std::fs::{self, File, OpenOptions};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

use arrow_array::{
    ArrayRef, BooleanArray, Int32Array, Int64Array, RecordBatch, StringArray,
};
use arrow_schema::{DataType, Field, Schema};
use lspr24_g0::{
    FormalDevelopmentConfig, FormalEntryError, LSPR24_G0_CONTRACT_SHA256,
    LSPR24_G0_CONTRACT_VERSION, prepare_unlabeled_development_split,
    run_formal_development_materialization,
};
use parquet::arrow::ArrowWriter;
use parquet::file::properties::WriterProperties;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

static NEXT_ID: AtomicU64 = AtomicU64::new(0);

struct FixtureRoot {
    path: PathBuf,
}

impl FixtureRoot {
    fn create(label: &str) -> Self {
        let id = NEXT_ID.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "lspr24-g0-formal-entry-{}-{id}-{label}",
            std::process::id()
        ));
        fs::create_dir(&path).expect("人工测试根应可创建");
        Self { path }
    }

    fn join(&self, path: &str) -> PathBuf {
        self.path.join(path)
    }
}

impl Drop for FixtureRoot {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn synthetic_batch() -> RecordBatch {
    let schema = Arc::new(Schema::new(vec![
        Field::new("mTimestampStart", DataType::Int64, true),
        Field::new("mTimestampLast", DataType::Int64, true),
        Field::new("SrcIP", DataType::Utf8, true),
        Field::new("DstIP", DataType::Utf8, true),
        Field::new("External_src", DataType::Boolean, true),
        Field::new("External_dst", DataType::Boolean, true),
        Field::new("SrcPort", DataType::Int32, true),
        Field::new("DstPort", DataType::Int32, true),
        Field::new("Protocol", DataType::Int32, true),
        Field::new("Flow ID", DataType::Utf8, true),
        Field::new("Label", DataType::Int32, true),
        Field::new("Packets", DataType::Int64, true),
    ]));
    let seconds = (0_i64..10).collect::<Vec<_>>();
    let flow_ids = (0..10).map(|index| format!("flow-{index}")).collect::<Vec<_>>();
    RecordBatch::try_new(
        schema,
        vec![
            Arc::new(Int64Array::from_iter_values(
                seconds.iter().map(|second| second * 1_000_000_000),
            )) as ArrayRef,
            Arc::new(Int64Array::from_iter_values(
                seconds
                    .iter()
                    .map(|second| second * 1_000_000_000 + 1),
            )) as ArrayRef,
            Arc::new(StringArray::from(vec![Some("10.0.0.1"); 10])) as ArrayRef,
            Arc::new(StringArray::from(vec![Some("203.0.113.1"); 10])) as ArrayRef,
            Arc::new(BooleanArray::from(vec![Some(false); 10])) as ArrayRef,
            Arc::new(BooleanArray::from(vec![Some(true); 10])) as ArrayRef,
            Arc::new(Int32Array::from(vec![Some(1234); 10])) as ArrayRef,
            Arc::new(Int32Array::from(vec![Some(443); 10])) as ArrayRef,
            Arc::new(Int32Array::from(vec![Some(6); 10])) as ArrayRef,
            Arc::new(StringArray::from(
                flow_ids.iter().map(String::as_str).collect::<Vec<_>>(),
            )) as ArrayRef,
            Arc::new(Int32Array::from(vec![
                Some(0),
                Some(1),
                Some(0),
                Some(1),
                Some(0),
                Some(1),
                Some(0),
                Some(1),
                Some(99),
                Some(99),
            ])) as ArrayRef,
            Arc::new(Int64Array::from_iter_values(100_i64..110)) as ArrayRef,
        ],
    )
    .expect("人工正式入口批应满足模式")
}

fn write_parquet(path: &Path) {
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .expect("人工 Parquet 应可排他创建");
    let properties = WriterProperties::builder()
        .set_max_row_group_size(3)
        .build();
    let batch = synthetic_batch();
    let mut writer = ArrowWriter::try_new(file, batch.schema(), Some(properties))
        .expect("人工 Parquet 写入器应可创建");
    writer.write(&batch).expect("人工批应可写入");
    writer.close().expect("人工 Parquet 应可关闭");
}

fn formal_config(root: &FixtureRoot) -> FormalDevelopmentConfig {
    FormalDevelopmentConfig::new(
        root.join("source.parquet"),
        root.join("split-receipt.json"),
        root.join("development.jsonl"),
        vec!["Packets".to_owned()],
    )
}

#[test]
fn external_split_receipt_binds_source_algorithm_cut_and_development_members() {
    let root = FixtureRoot::create("binding");
    write_parquet(&root.join("source.parquet"));
    let config = formal_config(&root);

    let split = prepare_unlabeled_development_split(&config)
        .expect("无标签第一阶段应生成外部切分收据");
    assert_eq!(split.contract_version(), LSPR24_G0_CONTRACT_VERSION);
    assert_eq!(split.contract_sha256(), LSPR24_G0_CONTRACT_SHA256);
    assert_ne!(split.parquet_sha256(), [0; 32]);
    assert_ne!(split.split_algorithm_sha256(), [0; 32]);
    assert_eq!(
        split.cut_ns(),
        [
            4_000_000_000,
            5_000_000_000,
            6_000_000_000,
            8_000_000_000,
        ]
    );
    assert_eq!(split.development_member_count(), 8);
    assert_ne!(split.development_member_sha256(), [0; 32]);

    let receipt = run_formal_development_materialization(&config)
        .expect("第二阶段应只读取并物化前 80%");
    assert_eq!(receipt.development_row_count(), 8);
    let rows = fs::read_to_string(root.join("development.jsonl"))
        .expect("开发输出应可读取")
        .lines()
        .map(|line| serde_json::from_str::<Value>(line).expect("开发行应为 JSON"))
        .collect::<Vec<_>>();
    assert_eq!(rows.len(), 8);
    assert!(rows.iter().all(|row| row["label"] == 0 || row["label"] == 1));
}

#[test]
fn self_rehashed_split_tamper_is_rejected_before_any_output() {
    let root = FixtureRoot::create("tamper");
    write_parquet(&root.join("source.parquet"));
    let config = formal_config(&root);
    prepare_unlabeled_development_split(&config).expect("初始切分收据应可生成");

    let receipt_path = root.join("split-receipt.json");
    let mut value: Value = serde_json::from_reader(
        File::open(&receipt_path).expect("收据应存在"),
    )
    .expect("收据应为 JSON");
    value["cut_ns"][3] = json!(9_000_000_000_i64);
    value["development_member_count"] = json!(9_u64);
    value["receipt_sha256"] = Value::String(receipt_self_hash(&value));
    fs::write(
        &receipt_path,
        serde_json::to_vec(&value).expect("篡改收据应可编码"),
    )
    .expect("篡改收据应可写入");

    let error = run_formal_development_materialization(&config)
        .expect_err("自洽重哈希也不能伪造实际开发选择");
    assert!(matches!(error, FormalEntryError::SplitBindingMismatch { .. }));
    assert!(!root.join("development.jsonl").exists());
    assert!(!root.join("development.jsonl.partial").exists());
}

#[test]
fn cli_rejects_selection_injection_and_never_claims_ready_without_core_receipts() {
    let root = FixtureRoot::create("cli");
    write_parquet(&root.join("source.parquet"));
    let config_path = root.join("config.json");
    let base = json!({
        "schema_version": "lspr24-g0-development-config-v2",
        "contract_version": LSPR24_G0_CONTRACT_VERSION,
        "contract_sha256": LSPR24_G0_CONTRACT_SHA256,
        "parquet_path": root.join("source.parquet"),
        "split_receipt_path": root.join("split-receipt.json"),
        "output_path": root.join("development.jsonl"),
        "feature_columns": ["Packets"]
    });
    fs::write(&config_path, serde_json::to_vec(&base).expect("配置应可编码"))
        .expect("配置应可写入");
    let command = Command::new(env!("CARGO_BIN_EXE_lspr24_g0_materialize"))
        .arg(&config_path)
        .output()
        .expect("开发命令应可运行");
    assert!(command.status.success());
    let status: Value = serde_json::from_slice(&command.stdout).expect("状态应为 JSON");
    assert_eq!(status["g0_d"], "NOT_READY");
    assert_eq!(status["g0_f"], "NOT_READY");
    assert_eq!(status["a12"], "NOT_READY");
    assert_eq!(status["final_access_authorized"], false);

    let injected_path = root.join("injected-config.json");
    let mut injected = base;
    injected["output_path"] = json!(root.join("injected-development.jsonl"));
    injected["split_receipt_path"] = json!(root.join("injected-split.json"));
    injected["selection"] = json!([{
        "raw_flow_id": vec![9; 32],
        "source_row_index": 9,
        "segment": "development-4"
    }]);
    fs::write(
        &injected_path,
        serde_json::to_vec(&injected).expect("注入配置应可编码"),
    )
    .expect("注入配置应可写入");
    let rejected = Command::new(env!("CARGO_BIN_EXE_lspr24_g0_materialize"))
        .arg(&injected_path)
        .output()
        .expect("开发命令应可运行");
    assert!(!rejected.status.success());
    assert!(!root.join("injected-development.jsonl").exists());
    assert!(!root.join("injected-development.jsonl.partial").exists());
}

fn receipt_self_hash(value: &Value) -> String {
    let mut unsigned = value.clone();
    unsigned
        .as_object_mut()
        .expect("收据顶层应为对象")
        .remove("receipt_sha256");
    let bytes = serde_json::to_vec(&unsigned).expect("无签名收据应可规范编码");
    let digest = Sha256::digest(bytes);
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}
