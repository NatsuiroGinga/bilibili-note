use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use lspr24_g0::{
    ArtifactRef, GateConfig, GateId, GateReceipt, GateStatus, OverallDecision, OutputError,
    PartialOutput, ReceiptError, evaluate_receipts, parse_gate_config, parse_gate_receipt,
};

const CONTRACT_VERSION: &str = "lspr24-g0-v3-review-pending";
const CONTRACT_SHA256: &str =
    "17a86b71e2858b420a73759437a5301e6efd3ba6179f949ea9d4d87adeeb24af";
static NEXT_TEMP_ID: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new(label: &str) -> Self {
        let id = NEXT_TEMP_ID.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "lspr24-g0-receipt-{}-{id}-{label}",
            std::process::id()
        ));
        fs::create_dir(&path).expect("人工测试目录应可创建");
        Self { path }
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn valid_config_json(extra: &str) -> String {
    format!(
        r#"{{
          "schema_version":"g0-config-v3",
          "contract_version":"{CONTRACT_VERSION}",
          "contract_sha256":"{CONTRACT_SHA256}",
          "receipt_paths":{{"A01":"receipts/a01.json"}}{extra}
        }}"#
    )
}

fn unsigned_receipt(gate_id: GateId, status: GateStatus) -> GateReceipt {
    let json = format!(
        r#"{{
          "gate_id":"{}",
          "contract_version":"{CONTRACT_VERSION}",
          "contract_sha256":"{CONTRACT_SHA256}",
          "producer_binary_sha256":"1111111111111111111111111111111111111111111111111111111111111111",
          "input_artifacts":[],
          "schema_version":"g0-receipt-v3",
          "checks":{{"producer_summary_pass":true}},
          "status":"{}",
          "created_at_utc":"2026-08-06T00:00:00Z",
          "receipt_sha256":"0000000000000000000000000000000000000000000000000000000000000000",
          "depends_on":[]
        }}"#,
        gate_id.as_str(),
        status.as_str()
    );
    parse_gate_receipt(json.as_bytes()).expect("人工收据应满足严格模式")
}

fn signed_receipt(gate_id: GateId, status: GateStatus) -> GateReceipt {
    unsigned_receipt(gate_id, status)
        .with_computed_hash()
        .expect("人工收据应可计算自哈希")
}

#[test]
fn config_and_receipt_reject_unknown_fields_and_unknown_enums() {
    let config_error = parse_gate_config(valid_config_json(
        r#", "unexpected":"must-not-be-ignored""#,
    ).as_bytes())
    .expect_err("配置未知字段必须拒绝");
    assert!(matches!(config_error, ReceiptError::Schema(_)));

    let unknown_gate = br#"{
      "gate_id":"A15",
      "contract_version":"lspr24-g0-v3-review-pending",
      "contract_sha256":"17a86b71e2858b420a73759437a5301e6efd3ba6179f949ea9d4d87adeeb24af",
      "producer_binary_sha256":"1111111111111111111111111111111111111111111111111111111111111111",
      "input_artifacts":[],
      "schema_version":"g0-receipt-v3",
      "checks":{},
      "status":"PASS",
      "created_at_utc":"2026-08-06T00:00:00Z",
      "receipt_sha256":"2222222222222222222222222222222222222222222222222222222222222222",
      "depends_on":[]
    }"#;
    let gate_error = parse_gate_receipt(unknown_gate).expect_err("未知门禁枚举必须拒绝");
    assert!(matches!(gate_error, ReceiptError::Schema(_)));

    let unknown_status = String::from_utf8(unknown_gate.to_vec())
        .expect("人工 JSON 应为 UTF-8")
        .replace("\"A15\"", "\"A01\"")
        .replace("\"PASS\"", "\"WARN\"");
    let status_error =
        parse_gate_receipt(unknown_status.as_bytes()).expect_err("未知状态枚举必须拒绝");
    assert!(matches!(status_error, ReceiptError::Schema(_)));
}

#[test]
fn missing_dependency_and_contract_or_artifact_hash_mismatch_are_not_ready() {
    let temp = TempDir::new("hashes");
    let artifact_path = temp.path().join("artifact.bin");
    fs::write(&artifact_path, b"actual").expect("人工制品应可写入");

    let a01 = signed_receipt(GateId::A01, GateStatus::Pass);
    let mut a02 = unsigned_receipt(GateId::A02, GateStatus::Pass);
    a02.input_artifacts_mut().push(ArtifactRef::new(
        artifact_path,
        [0x44; 32],
    ));
    let a02 = a02
        .with_computed_hash()
        .expect("人工收据应可计算自哈希");

    let config = GateConfig::new(CONTRACT_VERSION, CONTRACT_SHA256);
    let result = evaluate_receipts(&config, &[a01, a02], &BTreeMap::new());

    assert_eq!(result.status(GateId::A02), GateStatus::NotReady);
    assert_eq!(result.overall(), OverallDecision::NotReady);

    let wrong_contract = GateConfig::new(CONTRACT_VERSION, "00".repeat(32));
    let result = evaluate_receipts(
        &wrong_contract,
        &[signed_receipt(GateId::A01, GateStatus::Pass)],
        &BTreeMap::from([(GateId::A01, GateStatus::Pass)]),
    );
    assert_eq!(result.status(GateId::A01), GateStatus::NotReady);
}

#[test]
fn receipt_self_hash_and_fixed_a01_to_a14_dependencies_are_verified() {
    let mut receipts = Vec::new();
    for gate_id in GateId::ALL {
        let mut receipt = unsigned_receipt(gate_id, GateStatus::Pass);
        let dependencies = gate_id
            .required_dependencies()
            .iter()
            .map(|dependency| {
                let dependency_receipt = receipts
                    .iter()
                    .find(|candidate: &&GateReceipt| candidate.gate_id() == *dependency)
                    .expect("固定依赖必须先于当前门禁");
                (*dependency, dependency_receipt.receipt_sha256())
            })
            .collect();
        receipt.set_dependencies(dependencies);
        receipts.push(
            receipt
                .with_computed_hash()
                .expect("人工收据应可计算自哈希"),
        );
    }

    let config = GateConfig::new(CONTRACT_VERSION, CONTRACT_SHA256);
    let recomputed = GateId::ALL
        .into_iter()
        .map(|gate_id| (gate_id, GateStatus::Pass))
        .collect();
    let result = evaluate_receipts(&config, &receipts, &recomputed);

    assert_eq!(result.overall(), OverallDecision::GoToBaselinesAndEarlyStopping);
    assert!(GateId::ALL
        .into_iter()
        .all(|gate_id| result.status(gate_id) == GateStatus::Pass));

    receipts[0].set_receipt_sha256([0xaa; 32]);
    let result = evaluate_receipts(&config, &receipts, &recomputed);
    assert_eq!(result.status(GateId::A01), GateStatus::NotReady);
    assert_eq!(result.status(GateId::A02), GateStatus::NotReady);
}

#[test]
fn producer_summary_booleans_never_replace_independent_recomputation() {
    let receipt = signed_receipt(GateId::A01, GateStatus::Pass);
    let config = GateConfig::new(CONTRACT_VERSION, CONTRACT_SHA256);

    let no_raw_recomputation = evaluate_receipts(&config, &[receipt], &BTreeMap::new());

    assert_eq!(no_raw_recomputation.status(GateId::A01), GateStatus::NotReady);
    assert_eq!(no_raw_recomputation.overall(), OverallDecision::NotReady);
}

#[test]
fn formal_and_partial_paths_both_refuse_overwrite() {
    let temp = TempDir::new("exclusive-output");
    let formal = temp.path().join("receipt.json");
    let partial = temp.path().join("receipt.json.partial");

    fs::write(&formal, b"existing-formal").expect("人工正式文件应可写入");
    let error = PartialOutput::create(&formal).expect_err("正式路径存在时必须拒绝覆盖");
    assert!(matches!(error, OutputError::AlreadyExists(path) if path == formal));
    assert_eq!(fs::read(&formal).expect("正式文件应保持可读"), b"existing-formal");

    fs::remove_file(&formal).expect("人工正式文件应可移除");
    fs::write(&partial, b"existing-partial").expect("人工暂存文件应可写入");
    let error = PartialOutput::create(&formal).expect_err("暂存路径存在时必须拒绝覆盖");
    assert!(matches!(error, OutputError::AlreadyExists(path) if path == partial));
    assert_eq!(fs::read(&partial).expect("暂存文件应保持可读"), b"existing-partial");
}
