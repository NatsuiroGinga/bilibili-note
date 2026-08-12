//! 字段清单的唯一事实源：实施计划任务 1 的聚合规则表逐行展开。
//!
//! 本文件不得引入规则表之外的输出列，也不得手抄源列类型；类型一律由
//! [`crate::schema_audit::SchemaAudit`] 在展开阶段回填。

use std::collections::BTreeSet;

use super::build::output_column_slug;
use super::{
    AggOp, CONN_STATE_FALLBACK_BUCKET, CONN_STATE_VOCABULARY, Direction,
    MISSING_RULE_ALWAYS_EMITTED, MISSING_RULE_COUNT_ONLY, MISSING_RULE_NEGATIVE_AS_MISSING,
    MISSING_RULE_OBSERVED_ONLY, MISSING_RULE_ZERO_DENOMINATOR, SemanticGroup,
};

const UNIT_FLOWS: &str = "flows";
const UNIT_PACKETS: &str = "packets";
const UNIT_BYTES: &str = "bytes";
const UNIT_BYTES_SQUARED: &str = "bytes_squared";
const UNIT_MICROSECONDS: &str = "microseconds";
const UNIT_RATIO: &str = "ratio";
const UNIT_FLAG: &str = "flag";
const UNIT_BYTES_PER_SECOND: &str = "bytes_per_second";
const UNIT_PACKETS_PER_SECOND: &str = "packets_per_second";
const UNIT_LOG1P_FLOWS: &str = "log1p_flows";
const UNIT_LOG1P_PACKETS: &str = "log1p_packets";
const UNIT_LOG1P_BYTES: &str = "log1p_bytes";

const TRANSFORM_LOG1P: &str = "log1p";

const EXTERNAL_SRC: &str = "External_src";
const EXTERNAL_DST: &str = "External_dst";
const PROTOCOL_COLUMN: &str = "Protocol";
const CONN_STATE_COLUMN: &str = "Conn_state";

/// 流量规模行：双向包数与字节数的和及其 `log1p`。
const VOLUME_SUM_COLUMNS: [(&str, &str, &str); 4] = [
    ("Tot Fwd Pkts", UNIT_PACKETS, UNIT_LOG1P_PACKETS),
    ("Tot Bwd Pkts", UNIT_PACKETS, UNIT_LOG1P_PACKETS),
    ("Total Length of Fwd Packet", UNIT_BYTES, UNIT_LOG1P_BYTES),
    ("Total Length of Bwd Packet", UNIT_BYTES, UNIT_LOG1P_BYTES),
];

/// 方向行的三个度量：名称、源列与单位。
const DIRECTION_METRICS: [(&str, &[&str], &str, AggOp); 3] = [
    (
        "flow_count",
        &[EXTERNAL_SRC, EXTERNAL_DST],
        UNIT_FLOWS,
        AggOp::CountState,
    ),
    (
        "pkts_sum",
        &["Tot Fwd Pkts", "Tot Bwd Pkts", EXTERNAL_SRC, EXTERNAL_DST],
        UNIT_PACKETS,
        AggOp::Sum,
    ),
    (
        "bytes_sum",
        &[
            "Total Length of Fwd Packet",
            "Total Length of Bwd Packet",
            EXTERNAL_SRC,
            EXTERNAL_DST,
        ],
        UNIT_BYTES,
        AggOp::Sum,
    ),
];

const FLOW_DURATION_COLUMNS: [(&str, &str); 1] = [("Flow Duration", UNIT_MICROSECONDS)];

const PACKET_LENGTH_COLUMNS: [(&str, &str); 13] = [
    ("Fwd Packet Length Min", UNIT_BYTES),
    ("Fwd Packet Length Max", UNIT_BYTES),
    ("Fwd Packet Length Mean", UNIT_BYTES),
    ("Fwd Packet Length Std", UNIT_BYTES),
    ("Bwd Packet Length Min", UNIT_BYTES),
    ("Bwd Packet Length Max", UNIT_BYTES),
    ("Bwd Packet Length Mean", UNIT_BYTES),
    ("Bwd Packet Length Std", UNIT_BYTES),
    ("Packet Length Min", UNIT_BYTES),
    ("Packet Length Max", UNIT_BYTES),
    ("Packet Length Mean", UNIT_BYTES),
    ("Packet Length Std", UNIT_BYTES),
    ("Packet Length Variance", UNIT_BYTES_SQUARED),
];

const IAT_COLUMNS: [(&str, &str); 14] = [
    ("Flow IAT Mean", UNIT_MICROSECONDS),
    ("Flow IAT Min", UNIT_MICROSECONDS),
    ("Flow IAT Max", UNIT_MICROSECONDS),
    ("Flow IAT Stddev", UNIT_MICROSECONDS),
    ("Fwd IAT Min", UNIT_MICROSECONDS),
    ("Fwd IAT Max", UNIT_MICROSECONDS),
    ("Fwd IAT Mean", UNIT_MICROSECONDS),
    ("Fwd IAT Std", UNIT_MICROSECONDS),
    ("Fwd IAT Tot", UNIT_MICROSECONDS),
    ("Bwd IAT Min", UNIT_MICROSECONDS),
    ("Bwd IAT Max", UNIT_MICROSECONDS),
    ("Bwd IAT Mean", UNIT_MICROSECONDS),
    ("Bwd IAT Std", UNIT_MICROSECONDS),
    ("Bwd IAT Tot", UNIT_MICROSECONDS),
];

const ACTIVE_IDLE_COLUMNS: [(&str, &str); 8] = [
    ("Active Min", UNIT_MICROSECONDS),
    ("Active Mean", UNIT_MICROSECONDS),
    ("Active Max", UNIT_MICROSECONDS),
    ("Active Std", UNIT_MICROSECONDS),
    ("Idle Min", UNIT_MICROSECONDS),
    ("Idle Mean", UNIT_MICROSECONDS),
    ("Idle Max", UNIT_MICROSECONDS),
    ("Idle Std", UNIT_MICROSECONDS),
];

const RATE_COLUMNS: [(&str, &str); 8] = [
    ("Flow Bytes/s", UNIT_BYTES_PER_SECOND),
    ("Flow Packets/s", UNIT_PACKETS_PER_SECOND),
    ("Fwd Packets/s", UNIT_PACKETS_PER_SECOND),
    ("Bwd Packets/s", UNIT_PACKETS_PER_SECOND),
    ("Down/Up Ratio", UNIT_RATIO),
    ("Average Packet Size", UNIT_BYTES),
    ("Fwd Segment Size Avg", UNIT_BYTES),
    ("Bwd Segment Size Avg", UNIT_BYTES),
];

const HEADER_COLUMNS: [(&str, &str); 4] = [
    ("Fwd Header Length", UNIT_BYTES),
    ("Bwd Header Length", UNIT_BYTES),
    ("Fwd Act Data Pkts", UNIT_PACKETS),
    ("Fwd Seg Size Min", UNIT_BYTES),
];

const BULK_SUBFLOW_COLUMNS: [(&str, &str); 10] = [
    ("Fwd Bytes/Bulk Avg", UNIT_BYTES),
    ("Fwd Packet/Bulk Avg", UNIT_PACKETS),
    ("Fwd Bulk Rate Avg", UNIT_BYTES_PER_SECOND),
    ("Bwd Bytes/Bulk Avg", UNIT_BYTES),
    ("Bwd Packet/Bulk Avg", UNIT_PACKETS),
    ("Bwd Bulk Rate Avg", UNIT_BYTES_PER_SECOND),
    ("Subflow Fwd Packets", UNIT_PACKETS),
    ("Subflow Fwd Bytes", UNIT_BYTES),
    ("Subflow Bwd Packets", UNIT_PACKETS),
    ("Subflow Bwd Bytes", UNIT_BYTES),
];

const INIT_WIN_COLUMNS: [(&str, &str); 2] = [
    ("FWD Init Win Bytes", UNIT_BYTES),
    ("Bwd Init Win Bytes", UNIT_BYTES),
];

const FLAG_COLUMNS: [&str; 12] = [
    "Fwd PSH flags",
    "Bwd PSH flags",
    "Fwd URG flags",
    "Bwd URG flags",
    "FIN Flag Cnt",
    "SYN Flag Cnt",
    "RST Flag Cnt",
    "PSH Flag Cnt",
    "ACK Flag Cnt",
    "URG Flag Cnt",
    "CWR Flag Cnt",
    "ECE Flag Cnt",
];

/// 粗粒度协议类：不依赖端口或身份，只由 IANA 协议号推导。
const PROTOCOL_CLASSES: [&str; 4] = ["tcp", "udp", "icmp", "other"];

const MIN_MAX_MEAN: [AggOp; 3] = [AggOp::Min, AggOp::Max, AggOp::Mean];
const SUM_MIN_MAX_MEAN: [AggOp; 4] = [AggOp::Sum, AggOp::Min, AggOp::Max, AggOp::Mean];
const SUM_MEAN: [AggOp; 2] = [AggOp::Sum, AggOp::Mean];

/// 规则表展开后的一个输出列草案，源列类型尚未回填。
#[derive(Debug, Clone)]
pub(crate) struct RuleEntry {
    pub(crate) output_name: String,
    pub(crate) semantic_group: SemanticGroup,
    pub(crate) source_columns: Vec<&'static str>,
    pub(crate) aggregation_operator: AggOp,
    pub(crate) unit: &'static str,
    pub(crate) direction_semantics: Option<Direction>,
    pub(crate) missing_rule: &'static str,
    pub(crate) transform: Option<&'static str>,
    pub(crate) generation_target: bool,
}

/// 逐行展开聚合规则表。
pub(crate) fn rule_entries() -> Vec<RuleEntry> {
    let mut entries = Vec::new();
    push_volume(&mut entries);
    push_direction(&mut entries);
    push_flow_stats(&mut entries);
    push_protocol(&mut entries);
    push_quality(&mut entries);
    entries
}

fn push_volume(entries: &mut Vec<RuleEntry>) {
    entries.push(RuleEntry {
        output_name: "win_flow_count".to_owned(),
        semantic_group: SemanticGroup::Volume,
        source_columns: Vec::new(),
        aggregation_operator: AggOp::CountState,
        unit: UNIT_FLOWS,
        direction_semantics: Some(Direction::Both),
        missing_rule: MISSING_RULE_COUNT_ONLY,
        transform: None,
        generation_target: true,
    });
    entries.push(RuleEntry {
        output_name: "win_log1p_flow_count".to_owned(),
        semantic_group: SemanticGroup::Volume,
        source_columns: Vec::new(),
        aggregation_operator: AggOp::LogOneP,
        unit: UNIT_LOG1P_FLOWS,
        direction_semantics: Some(Direction::Both),
        missing_rule: MISSING_RULE_COUNT_ONLY,
        transform: Some(TRANSFORM_LOG1P),
        generation_target: true,
    });

    for (column, unit, log_unit) in VOLUME_SUM_COLUMNS {
        let slug = output_column_slug(column);
        entries.push(RuleEntry {
            output_name: format!("win_{slug}_sum"),
            semantic_group: SemanticGroup::Volume,
            source_columns: vec![column],
            aggregation_operator: AggOp::Sum,
            unit,
            direction_semantics: Some(Direction::Both),
            missing_rule: MISSING_RULE_OBSERVED_ONLY,
            transform: None,
            generation_target: true,
        });
        entries.push(RuleEntry {
            output_name: format!("win_log1p_{slug}_sum"),
            semantic_group: SemanticGroup::Volume,
            source_columns: vec![column],
            aggregation_operator: AggOp::LogOneP,
            unit: log_unit,
            direction_semantics: Some(Direction::Both),
            missing_rule: MISSING_RULE_OBSERVED_ONLY,
            transform: Some(TRANSFORM_LOG1P),
            generation_target: true,
        });
    }
}

fn push_direction(entries: &mut Vec<RuleEntry>) {
    for (metric, columns, unit, operator) in DIRECTION_METRICS {
        for (prefix, direction) in [
            ("inbound", Direction::Inbound),
            ("outbound", Direction::Outbound),
        ] {
            entries.push(RuleEntry {
                output_name: format!("win_{prefix}_{metric}"),
                semantic_group: SemanticGroup::Direction,
                source_columns: columns.to_vec(),
                aggregation_operator: operator,
                unit,
                direction_semantics: Some(direction),
                missing_rule: MISSING_RULE_OBSERVED_ONLY,
                transform: None,
                generation_target: true,
            });
        }
        entries.push(RuleEntry {
            output_name: format!("win_out_ratio_{metric}"),
            semantic_group: SemanticGroup::Direction,
            source_columns: columns.to_vec(),
            aggregation_operator: AggOp::Ratio,
            unit: UNIT_RATIO,
            direction_semantics: Some(Direction::Both),
            missing_rule: MISSING_RULE_ZERO_DENOMINATOR,
            transform: None,
            generation_target: false,
        });
        entries.push(RuleEntry {
            output_name: format!("win_out_minus_in_{metric}"),
            semantic_group: SemanticGroup::Direction,
            source_columns: columns.to_vec(),
            aggregation_operator: AggOp::Diff,
            unit,
            direction_semantics: Some(Direction::Both),
            missing_rule: MISSING_RULE_OBSERVED_ONLY,
            transform: None,
            generation_target: false,
        });
    }
}

fn push_flow_stats(entries: &mut Vec<RuleEntry>) {
    push_stat_group(
        entries,
        &FLOW_DURATION_COLUMNS,
        &MIN_MAX_MEAN,
        MISSING_RULE_OBSERVED_ONLY,
        true,
    );
    push_stat_group(
        entries,
        &PACKET_LENGTH_COLUMNS,
        &MIN_MAX_MEAN,
        MISSING_RULE_OBSERVED_ONLY,
        true,
    );
    push_stat_group(
        entries,
        &IAT_COLUMNS,
        &MIN_MAX_MEAN,
        MISSING_RULE_OBSERVED_ONLY,
        true,
    );
    push_stat_group(
        entries,
        &ACTIVE_IDLE_COLUMNS,
        &MIN_MAX_MEAN,
        MISSING_RULE_OBSERVED_ONLY,
        true,
    );
    push_stat_group(
        entries,
        &RATE_COLUMNS,
        &MIN_MAX_MEAN,
        MISSING_RULE_OBSERVED_ONLY,
        false,
    );
    push_stat_group(
        entries,
        &HEADER_COLUMNS,
        &SUM_MIN_MAX_MEAN,
        MISSING_RULE_OBSERVED_ONLY,
        false,
    );
    push_stat_group(
        entries,
        &BULK_SUBFLOW_COLUMNS,
        &SUM_MEAN,
        MISSING_RULE_OBSERVED_ONLY,
        false,
    );
    push_stat_group(
        entries,
        &INIT_WIN_COLUMNS,
        &MIN_MAX_MEAN,
        MISSING_RULE_NEGATIVE_AS_MISSING,
        false,
    );
}

fn push_stat_group(
    entries: &mut Vec<RuleEntry>,
    columns: &[(&'static str, &'static str)],
    operators: &[AggOp],
    missing_rule: &'static str,
    generation_target: bool,
) {
    for (column, unit) in columns {
        let slug = output_column_slug(column);
        for operator in operators {
            entries.push(RuleEntry {
                output_name: format!("win_{slug}_{}", operator.output_suffix()),
                semantic_group: SemanticGroup::FlowStats,
                source_columns: vec![column],
                aggregation_operator: *operator,
                unit,
                direction_semantics: Some(Direction::Both),
                missing_rule,
                transform: None,
                generation_target,
            });
        }
    }
}

fn push_protocol(entries: &mut Vec<RuleEntry>) {
    for column in FLAG_COLUMNS {
        let slug = output_column_slug(column);
        entries.push(RuleEntry {
            output_name: format!("win_{slug}_sum"),
            semantic_group: SemanticGroup::Protocol,
            source_columns: vec![column],
            aggregation_operator: AggOp::Sum,
            unit: UNIT_PACKETS,
            direction_semantics: Some(Direction::Both),
            missing_rule: MISSING_RULE_OBSERVED_ONLY,
            transform: None,
            generation_target: true,
        });
    }

    for class in PROTOCOL_CLASSES {
        entries.push(RuleEntry {
            output_name: format!("win_protocol_{class}_flow_count"),
            semantic_group: SemanticGroup::Protocol,
            source_columns: vec![PROTOCOL_COLUMN],
            aggregation_operator: AggOp::CountState,
            unit: UNIT_FLOWS,
            direction_semantics: Some(Direction::Both),
            missing_rule: MISSING_RULE_COUNT_ONLY,
            transform: None,
            generation_target: true,
        });
    }

    for state in CONN_STATE_VOCABULARY
        .iter()
        .copied()
        .chain(std::iter::once(CONN_STATE_FALLBACK_BUCKET))
    {
        let slug = output_column_slug(state);
        entries.push(RuleEntry {
            output_name: format!("win_conn_state_{slug}_flow_count"),
            semantic_group: SemanticGroup::Protocol,
            source_columns: vec![CONN_STATE_COLUMN],
            aggregation_operator: AggOp::CountState,
            unit: UNIT_FLOWS,
            direction_semantics: Some(Direction::Both),
            missing_rule: MISSING_RULE_COUNT_ONLY,
            transform: None,
            generation_target: true,
        });
    }
}

fn push_quality(entries: &mut Vec<RuleEntry>) {
    let mut ordered: Vec<&'static str> = Vec::new();
    let mut seen: BTreeSet<&'static str> = BTreeSet::new();
    for entry in entries.iter() {
        if entry.semantic_group != SemanticGroup::FlowStats {
            continue;
        }
        for column in &entry.source_columns {
            if seen.insert(column) {
                ordered.push(column);
            }
        }
    }

    for column in ordered {
        let slug = output_column_slug(column);
        for (operator, unit) in [
            (AggOp::ObservedCount, UNIT_FLOWS),
            (AggOp::MissingCount, UNIT_FLOWS),
            (AggOp::MissingRate, UNIT_RATIO),
        ] {
            entries.push(RuleEntry {
                output_name: format!("win_{slug}_{}", operator.output_suffix()),
                semantic_group: SemanticGroup::Quality,
                source_columns: vec![column],
                aggregation_operator: operator,
                unit,
                direction_semantics: None,
                missing_rule: MISSING_RULE_ALWAYS_EMITTED,
                transform: None,
                generation_target: false,
            });
        }
    }

    entries.push(RuleEntry {
        output_name: "win_no_flow_window".to_owned(),
        semantic_group: SemanticGroup::Quality,
        source_columns: Vec::new(),
        aggregation_operator: AggOp::NoFlowFlag,
        unit: UNIT_FLAG,
        direction_semantics: None,
        missing_rule: MISSING_RULE_ALWAYS_EMITTED,
        transform: None,
        generation_target: false,
    });
    entries.push(RuleEntry {
        output_name: "win_nonfinite_isolated_count".to_owned(),
        semantic_group: SemanticGroup::Quality,
        source_columns: Vec::new(),
        aggregation_operator: AggOp::CountState,
        unit: UNIT_FLOWS,
        direction_semantics: None,
        missing_rule: MISSING_RULE_ALWAYS_EMITTED,
        transform: None,
        generation_target: false,
    });
}
