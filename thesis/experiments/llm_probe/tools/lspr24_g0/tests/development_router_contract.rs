use std::collections::BTreeSet;

use lspr24_g0::{
    DevelopmentLabelRow, DevelopmentMemberId, DevelopmentRouter, DevelopmentSegment,
    DevelopmentSelectionMember, DevelopmentSplitReceipt, NormalizedLabel, RoutingError,
};

fn member(flow_byte: u8, source_row_index: u64) -> DevelopmentMemberId {
    DevelopmentMemberId::new([flow_byte; 32], source_row_index)
}

fn split_receipt(members: Vec<DevelopmentSelectionMember>) -> DevelopmentSplitReceipt {
    DevelopmentSplitReceipt::new(members).expect("无标签开发选择收据应有效")
}

#[test]
fn routes_only_selected_development_members_before_label_normalization() {
    let selected = vec![
        DevelopmentSelectionMember::new(member(1, 1), DevelopmentSegment::First),
        DevelopmentSelectionMember::new(member(2, 2), DevelopmentSegment::Second),
        DevelopmentSelectionMember::new(member(3, 3), DevelopmentSegment::Third),
        DevelopmentSelectionMember::new(member(4, 4), DevelopmentSegment::Fourth),
    ];
    let receipt = split_receipt(selected);
    let receipt_sha256 = receipt.receipt_sha256();
    let router = DevelopmentRouter::new(receipt);

    let routed = router
        .route([
            DevelopmentLabelRow::new(member(1, 1), " benign "),
            DevelopmentLabelRow::new(member(2, 2), "MALICIOUS"),
            DevelopmentLabelRow::new(member(3, 3), "normal"),
            DevelopmentLabelRow::new(member(4, 4), "attack"),
            DevelopmentLabelRow::new(member(99, 99), "不是合法标签"),
        ])
        .expect("非开发成员必须在标签规范化前被静默丢弃");

    assert_eq!(routed.split_receipt_sha256(), receipt_sha256);
    assert_eq!(routed.labels().len(), 4);
    assert_eq!(routed.labels()[0].label(), NormalizedLabel::Benign);
    assert_eq!(routed.labels()[1].label(), NormalizedLabel::Malicious);
    assert_eq!(routed.labels()[2].label(), NormalizedLabel::Benign);
    assert_eq!(routed.labels()[3].label(), NormalizedLabel::Malicious);
    assert_eq!(
        routed
            .labels()
            .iter()
            .map(|row| row.segment())
            .collect::<BTreeSet<_>>(),
        BTreeSet::from([
            DevelopmentSegment::First,
            DevelopmentSegment::Second,
            DevelopmentSegment::Third,
            DevelopmentSegment::Fourth,
        ])
    );
}

#[test]
fn conflicting_duplicate_class_isolated_as_a_whole_with_development_only_counts() {
    let conflict_a = member(7, 10);
    let conflict_b = member(7, 11);
    let kept = member(8, 12);
    let receipt = split_receipt(vec![
        DevelopmentSelectionMember::new(conflict_a, DevelopmentSegment::First),
        DevelopmentSelectionMember::new(conflict_b, DevelopmentSegment::Second),
        DevelopmentSelectionMember::new(kept, DevelopmentSegment::Third),
    ]);

    let routed = DevelopmentRouter::new(receipt)
        .route([
            DevelopmentLabelRow::new(conflict_a, "benign"),
            DevelopmentLabelRow::new(conflict_b, "malicious"),
            DevelopmentLabelRow::new(kept, "benign"),
            DevelopmentLabelRow::new(member(9, 90), "malicious"),
            DevelopmentLabelRow::new(member(9, 91), "benign"),
        ])
        .expect("开发区冲突应隔离而不是中止路由");

    assert_eq!(routed.labels().len(), 1);
    assert_eq!(routed.labels()[0].member(), kept);
    assert_eq!(routed.isolated_conflict_classes(), 1);
    assert_eq!(routed.isolated_development_members(), 2);
}

#[test]
fn invalid_selected_label_fails_closed() {
    let selected = member(5, 5);
    let receipt = split_receipt(vec![DevelopmentSelectionMember::new(
        selected,
        DevelopmentSegment::First,
    )]);
    let error = DevelopmentRouter::new(receipt)
        .route([DevelopmentLabelRow::new(selected, "未知")])
        .expect_err("开发成员的非法标签必须失败关闭");
    assert!(matches!(
        error,
        RoutingError::InvalidDevelopmentLabel { member, .. } if member == selected
    ));
}
