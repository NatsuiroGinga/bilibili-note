use std::collections::BTreeMap;
use std::io;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use lspr24_g0::{
    DevelopmentFeatureRow, DevelopmentLabelRow, DevelopmentMemberId, DevelopmentRouter,
    DevelopmentSegment, DevelopmentSelectionMember, DevelopmentSplitReceipt, GateId, GateStatus,
    CommitStage, MaterializeError, PostPublishOperations, RawGateArtifacts,
    SystemPostPublishOperations, materialize_development, recompute_raw_gate_statuses,
};
use serde_json::json;

static NEXT_ID: AtomicU64 = AtomicU64::new(0);

fn temp_path(label: &str) -> PathBuf {
    let id = NEXT_ID.fetch_add(1, Ordering::Relaxed);
    std::env::temp_dir().join(format!(
        "lspr24-g0-materialize-{}-{id}-{label}",
        std::process::id()
    ))
}

fn member(flow_byte: u8, source_row_index: u64) -> DevelopmentMemberId {
    DevelopmentMemberId::new([flow_byte; 32], source_row_index)
}

fn routed_members(members: &[(DevelopmentMemberId, DevelopmentSegment)]) -> lspr24_g0::DevelopmentRouting {
    let receipt = DevelopmentSplitReceipt::new(
        members
            .iter()
            .map(|(member, segment)| DevelopmentSelectionMember::new(*member, *segment))
            .collect(),
    )
    .expect("开发选择收据应有效");
    DevelopmentRouter::new(receipt)
        .route(
            members
                .iter()
                .map(|(member, _)| DevelopmentLabelRow::new(*member, "benign")),
        )
        .expect("开发标签应可路由")
}

fn partial_path(formal: &Path) -> PathBuf {
    let mut value = formal.as_os_str().to_os_string();
    value.push(".partial");
    PathBuf::from(value)
}

#[test]
fn materializes_only_four_development_segments_and_ignores_nonmembers() {
    let root = temp_path("development-only");
    fs::create_dir(&root).expect("测试目录应可创建");
    let output_a = root.join("development-a.jsonl");
    let output_b = root.join("development-b.jsonl");
    let members = [
        (member(1, 1), DevelopmentSegment::First),
        (member(2, 2), DevelopmentSegment::Second),
        (member(3, 3), DevelopmentSegment::Third),
        (member(4, 4), DevelopmentSegment::Fourth),
    ];
    let routed = routed_members(&members);
    let development_features = members
        .iter()
        .map(|(member, _)| DevelopmentFeatureRow::new(*member, vec![member.source_row_index() as u8]))
        .collect::<Vec<_>>();
    let mut features_with_nonmember = development_features.clone();
    features_with_nonmember.push(DevelopmentFeatureRow::new(member(99, 99), b"hidden".to_vec()));

    let receipt_a = materialize_development(&routed, &features_with_nonmember, &output_a)
        .expect("只应物化开发选择成员");
    let receipt_b = materialize_development(&routed, &development_features, &output_b)
        .expect("开发输出应可重复确定性生成");

    assert_eq!(fs::read(&output_a).expect("输出应存在"), fs::read(&output_b).expect("输出应存在"));
    assert_eq!(receipt_a.development_row_count(), 4);
    assert_eq!(receipt_a.development_semantic_sha256(), receipt_b.development_semantic_sha256());
    assert_eq!(receipt_a.split_receipt_sha256(), routed.split_receipt_sha256());
    assert_eq!(receipt_a.gate_status(GateId::A12), GateStatus::NotReady);
    assert_eq!(receipt_a.final_hash_status(), GateStatus::NotReady);
    fs::remove_dir_all(root).expect("测试目录应可清理");
}

#[test]
fn validation_failure_and_existing_output_never_leave_or_replace_partial_state() {
    let root = temp_path("exclusive");
    fs::create_dir(&root).expect("测试目录应可创建");
    let output = root.join("development.jsonl");
    let members = [
        (member(1, 1), DevelopmentSegment::First),
        (member(2, 2), DevelopmentSegment::Second),
    ];
    let routed = routed_members(&members);

    let error = materialize_development(
        &routed,
        &[DevelopmentFeatureRow::new(member(1, 1), vec![1])],
        &output,
    )
    .expect_err("缺少开发特征必须在发布前失败");
    assert!(matches!(error, MaterializeError::MissingDevelopmentFeature { .. }));
    assert!(!output.exists());
    assert!(!partial_path(&output).exists());

    fs::write(&output, b"existing").expect("既有文件应可建立");
    let error = materialize_development(
        &routed,
        &[
            DevelopmentFeatureRow::new(member(1, 1), vec![1]),
            DevelopmentFeatureRow::new(member(2, 2), vec![2]),
        ],
        &output,
    )
    .expect_err("正式输出不得覆盖");
    assert!(matches!(error, MaterializeError::Output(_)));
    assert_eq!(fs::read(&output).expect("既有文件应保持"), b"existing");
    assert!(!partial_path(&output).exists());
    fs::remove_dir_all(root).expect("测试目录应可清理");
}

#[test]
fn producer_summary_is_not_raw_evidence_and_a12_stays_not_ready() {
    let artifacts = RawGateArtifacts::new(BTreeMap::from([
        (
            GateId::A01,
            json!({"gate_id":"A01", "checks":{"producer_summary_pass":true}}),
        ),
        (
            GateId::A12,
            json!({"gate_id":"A12", "evidence":{"complete":true}}),
        ),
        (
            GateId::A02,
            json!({"gate_id":"A02", "evidence":{"complete":true}}),
        ),
    ]));
    let statuses = recompute_raw_gate_statuses(&artifacts);
    assert_eq!(statuses.get(&GateId::A01), Some(&GateStatus::NotReady));
    assert_eq!(statuses.get(&GateId::A02), Some(&GateStatus::NotReady));
    assert_eq!(statuses.get(&GateId::A12), Some(&GateStatus::NotReady));
}

struct FailAt {
    stage: CommitStage,
}

impl PostPublishOperations for FailAt {
    fn before_operation(&self, stage: CommitStage) -> io::Result<()> {
        if stage == self.stage {
            Err(io::Error::other("人工发布后故障"))
        } else {
            Ok(())
        }
    }
}

#[test]
fn post_link_partial_removal_failure_rolls_back_both_names() {
    assert_post_publish_failure_rolls_back(CommitStage::RemovePartial);
}

#[test]
fn parent_fsync_failure_rolls_back_both_names() {
    assert_post_publish_failure_rolls_back(CommitStage::SyncParent);
}

fn assert_post_publish_failure_rolls_back(stage: CommitStage) {
    let root = temp_path("post-publish-failure");
    fs::create_dir(&root).expect("测试目录应可创建");
    let output = root.join("development.jsonl");
    let mut partial = lspr24_g0::PartialOutput::create(&output).expect("暂存输出应可创建");
    partial.write_all(b"development").expect("暂存输出应可写入");
    partial
        .commit_with_operations(&FailAt { stage })
        .expect_err("发布后故障必须失败关闭");
    assert!(!output.exists(), "失败时不得留下正式对象");
    assert!(!partial_path(&output).exists(), "失败时不得留下暂存对象");

    let mut retry = lspr24_g0::PartialOutput::create(&output)
        .expect("清理完成后同一路径应可重新排他创建");
    retry.write_all(b"development").expect("重试暂存应可写入");
    retry
        .commit_with_operations(&SystemPostPublishOperations)
        .expect("无故障发布应成功");
    fs::remove_dir_all(root).expect("测试目录应可清理");
}
