//! 任务 1 合同测试：字段清单规则表展开、禁入断言与 JSON 冻结形状。

mod common;

use std::collections::{BTreeMap, BTreeSet};

use lspr24_g0::{
    AggOp, AuditedColumn, Direction, FIELD_MANIFEST_REQUIRED_KEYS, FieldManifestEntry,
    FieldManifestError, FORBIDDEN_SOURCE_COLUMNS, SchemaAudit, SemanticGroup,
    WINDOW_AGG_FORMULA_VERSION, build_field_manifest, output_column_slug, validate_field_manifest,
};

fn frozen_entries() -> Vec<FieldManifestEntry> {
    let audit = common::load_frozen_schema_audit();
    build_field_manifest(&audit).expect("冻结模式下规则表必须能完整展开")
}

fn injected_entry(source_column: &str) -> FieldManifestEntry {
    FieldManifestEntry {
        output_name: "win_injected_probe".to_owned(),
        semantic_group: SemanticGroup::FlowStats,
        source_columns: vec![source_column.to_owned()],
        source_schema_types: vec!["Int64".to_owned()],
        availability_time: "window_end",
        aggregation_operator: AggOp::Sum,
        formula_version: WINDOW_AGG_FORMULA_VERSION,
        unit: "bytes".to_owned(),
        direction_semantics: Some(Direction::Both),
        missing_rule: "observed-only; all-missing => 0 + mask",
        transform: None,
        train_fit_parameter_hash: None,
        generation_target: false,
        allowed_models: vec!["ALL".to_owned()],
    }
}

#[test]
fn output_names_are_unique_across_the_expanded_rule_table() {
    let entries = frozen_entries();

    let unique: BTreeSet<&str> = entries
        .iter()
        .map(|entry| entry.output_name.as_str())
        .collect();

    assert!(!entries.is_empty(), "规则表展开不得为空");
    assert_eq!(unique.len(), entries.len(), "输出列名不得重名");
    assert!(
        entries
            .iter()
            .all(|entry| entry.output_name.starts_with("win_")),
        "全部输出列必须使用 win_ 前缀"
    );
}

#[test]
fn every_source_column_exists_in_the_audit_with_matching_type() {
    let audit = common::load_frozen_schema_audit();
    let types: BTreeMap<&str, &str> = audit
        .columns()
        .iter()
        .map(|column| (column.name.as_str(), column.arrow_type.as_str()))
        .collect();
    let entries = build_field_manifest(&audit).expect("冻结模式下规则表必须能完整展开");

    for entry in &entries {
        assert_eq!(
            entry.source_columns.len(),
            entry.source_schema_types.len(),
            "{} 的源列与源类型必须一一对应",
            entry.output_name
        );
        for (column, declared) in entry
            .source_columns
            .iter()
            .zip(entry.source_schema_types.iter())
        {
            assert!(!column.contains('*'), "源列不得含通配符：{column}");
            let actual = types
                .get(column.as_str())
                .unwrap_or_else(|| panic!("{} 引用了审计清单外的源列 {column}", entry.output_name));
            assert_eq!(declared, actual, "{} 的源列 {column} 类型不一致", entry.output_name);
        }
    }
}

#[test]
fn forbidden_source_column_is_rejected_by_construction() {
    let mut entries = frozen_entries();
    entries.push(injected_entry("Severity"));

    let error = match validate_field_manifest(&entries, &common::load_frozen_schema_audit()) {
        Err(error) => error,
        Ok(()) => panic!("含禁入源列的条目必须构造失败"),
    };

    assert!(
        matches!(
            &error,
            FieldManifestError::ForbiddenSourceColumn { output_name, column }
                if output_name == "win_injected_probe" && column == "Severity"
        ),
        "实际错误：{error}"
    );
}

#[test]
fn every_blacklisted_column_is_rejected_individually() {
    let audit = common::load_frozen_schema_audit();

    for column in FORBIDDEN_SOURCE_COLUMNS {
        let entries = vec![injected_entry(column)];
        let error = match validate_field_manifest(&entries, &audit) {
            Err(error) => error,
            Ok(()) => panic!("禁入源列 {column} 必须被拒绝"),
        };
        assert!(
            matches!(
                &error,
                FieldManifestError::ForbiddenSourceColumn { column: rejected, .. }
                    if rejected == column
            ),
            "禁入源列 {column} 的实际错误：{error}"
        );
    }
}

#[test]
fn unknown_source_column_is_rejected() {
    let audit = common::load_frozen_schema_audit();
    let entries = vec![injected_entry("NotAnLspr24Column")];

    let error = match validate_field_manifest(&entries, &audit) {
        Err(error) => error,
        Ok(()) => panic!("审计清单外的源列必须被拒绝"),
    };

    assert!(
        matches!(
            &error,
            FieldManifestError::UnknownSourceColumn { column, .. }
                if column == "NotAnLspr24Column"
        ),
        "实际错误：{error}"
    );
}

#[test]
fn rule_table_fails_on_an_audit_missing_required_columns() {
    let audit = SchemaAudit::from_columns(
        "partial.parquet".to_owned(),
        2,
        1,
        vec![AuditedColumn::new(
            0,
            "Tot Fwd Pkts".to_owned(),
            "Int32".to_owned(),
            true,
        )],
    )
    .expect("单列审计应可构造");

    let error = match build_field_manifest(&audit) {
        Err(error) => error,
        Ok(_) => panic!("审计缺列时规则表展开必须失败"),
    };

    assert!(
        matches!(error, FieldManifestError::UnknownSourceColumn { .. }),
        "实际错误：{error}"
    );
}

#[test]
fn semantic_groups_cover_at_least_five_categories() {
    let entries = frozen_entries();

    let groups: BTreeSet<SemanticGroup> =
        entries.iter().map(|entry| entry.semantic_group).collect();

    assert!(groups.len() >= 5, "语义组至少覆盖 5 类，实际 {}", groups.len());
    for expected in [
        SemanticGroup::Volume,
        SemanticGroup::Direction,
        SemanticGroup::FlowStats,
        SemanticGroup::Protocol,
        SemanticGroup::Quality,
    ] {
        assert!(groups.contains(&expected), "缺少语义组 {expected:?}");
    }
}

#[test]
fn every_flow_stats_source_column_has_quality_outputs() {
    let entries = frozen_entries();
    let names: BTreeSet<&str> = entries
        .iter()
        .map(|entry| entry.output_name.as_str())
        .collect();

    let mut flow_stats_columns: BTreeSet<&str> = BTreeSet::new();
    for entry in &entries {
        if entry.semantic_group == SemanticGroup::FlowStats {
            flow_stats_columns.extend(entry.source_columns.iter().map(String::as_str));
        }
    }

    assert!(!flow_stats_columns.is_empty(), "流完成统计组不得为空");
    for column in flow_stats_columns {
        let slug = output_column_slug(column);
        for suffix in ["observed_count", "missing_count", "missing_rate"] {
            let expected = format!("win_{slug}_{suffix}");
            assert!(names.contains(expected.as_str()), "缺少质量列 {expected}");
        }
    }
}

#[test]
fn representative_outputs_of_each_rule_row_are_present() {
    let entries = frozen_entries();
    let names: BTreeSet<&str> = entries
        .iter()
        .map(|entry| entry.output_name.as_str())
        .collect();

    for expected in [
        "win_flow_count",
        "win_log1p_flow_count",
        "win_tot_fwd_pkts_sum",
        "win_log1p_total_length_of_bwd_packet_sum",
        "win_inbound_flow_count",
        "win_outbound_bytes_sum",
        "win_out_ratio_pkts_sum",
        "win_out_minus_in_flow_count",
        "win_flow_duration_mean",
        "win_packet_length_variance_max",
        "win_bwd_iat_tot_min",
        "win_idle_std_mean",
        "win_fwd_header_length_sum",
        "win_subflow_bwd_bytes_mean",
        "win_fwd_init_win_bytes_min",
        "win_syn_flag_cnt_sum",
        "win_protocol_icmp_flow_count",
        "win_conn_state_rstos0_flow_count",
        "win_conn_state_other_flow_count",
        "win_no_flow_window",
        "win_nonfinite_isolated_count",
    ] {
        assert!(names.contains(expected), "缺少代表性输出列 {expected}");
    }
}

#[test]
fn json_document_is_stable_and_carries_every_required_key() {
    let entries = frozen_entries();

    let first = lspr24_g0::field_manifest_json_bytes(&entries).expect("字段清单应可序列化");
    let second = lspr24_g0::field_manifest_json_bytes(&entries).expect("字段清单应可重复序列化");
    assert_eq!(first, second, "同一清单的 JSON 必须逐字节稳定");

    let document: serde_json::Value =
        serde_json::from_slice(&first).expect("字段清单 JSON 应可解析");
    let parsed_entries = document
        .get("entries")
        .and_then(serde_json::Value::as_array)
        .expect("字段清单必须含 entries 数组");
    assert_eq!(parsed_entries.len(), entries.len());
    assert_eq!(
        document.get("quantile_aggregators"),
        Some(&serde_json::Value::Array(Vec::new())),
        "本版本分位数聚合器必须为空集"
    );

    let required: BTreeSet<&str> = FIELD_MANIFEST_REQUIRED_KEYS.into_iter().collect();
    for entry in parsed_entries {
        let object = entry.as_object().expect("每个条目必须是 JSON 对象");
        let keys: BTreeSet<&str> = object.keys().map(String::as_str).collect();
        assert_eq!(keys, required, "条目键集合必须与合同 §6.1 完全一致");
    }
}
