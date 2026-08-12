//! 合同 §6.1 字段清单：规则表驱动的输出列冻结与禁入断言。
//!
//! 本模块只处理清单结构，不读取任何数据行；源列类型一律来自
//! [`crate::schema_audit::SchemaAudit`]，禁止在代码中手抄列类型。

mod build;
mod json;
mod rules;

use std::error::Error;
use std::fmt::{Display, Formatter};

use serde::Serialize;

pub use build::{build_field_manifest, output_column_slug, validate_field_manifest};
pub use json::{FIELD_MANIFEST_VERSION, field_manifest_json_bytes, write_field_manifest_json};

/// 窗口聚合公式的冻结版本串。
pub const WINDOW_AGG_FORMULA_VERSION: &str = "lspr24-window-agg-v1";
/// 全部输出列的可用时点。
pub const AVAILABILITY_TIME_WINDOW_END: &str = "window_end";
/// 合同 §6.1 要求每个条目登记的键，序列化结果必须与之逐项一致。
pub const FIELD_MANIFEST_REQUIRED_KEYS: [&str; 14] = [
    "output_name",
    "semantic_group",
    "source_columns",
    "source_schema_types",
    "availability_time",
    "aggregation_operator",
    "formula_version",
    "unit",
    "direction_semantics",
    "missing_rule",
    "transform",
    "train_fit_parameter_hash",
    "generation_target",
    "allowed_models",
];

/// 合同 §6.2 与本计划 §1 冻结的禁入源列黑名单。
///
/// 任何字段清单条目的 `source_columns` 命中其一即构造失败。
pub const FORBIDDEN_SOURCE_COLUMNS: [&str; 21] = [
    "Anomaly_event",
    "Category",
    "DstIP",
    "DstPort",
    "Expoid_dst",
    "Expoid_src",
    "Flow ID",
    "Int/Ext Dst IP",
    "L3/L4 Protocol",
    "Label",
    "Label_dst",
    "Label_src",
    "Segment_dst",
    "Segment_src",
    "Service",
    "SigID revision",
    "Severity",
    "SrcIP",
    "SrcPort",
    "mTimestampLast",
    "mTimestampStart",
];

/// `Conn_state` 的冻结先验词表（Zeek 闭集，不做训练区拟合）。
pub const CONN_STATE_VOCABULARY: [&str; 13] = [
    "S0", "S1", "S2", "S3", "SF", "REJ", "RSTO", "RSTR", "RSTOS0", "RSTRH", "SH", "SHR", "OTH",
];
/// 落在冻结词表之外的连接状态的兜底桶名。
pub const CONN_STATE_FALLBACK_BUCKET: &str = "other";

/// 观测值优先、全缺失写 0 并置掩码。
pub const MISSING_RULE_OBSERVED_ONLY: &str = "observed-only; all-missing => 0 + mask";
/// 负值按缺失处理（`Init Win Bytes` 的 CICFlowMeter 语义），其余同观测值优先。
pub const MISSING_RULE_NEGATIVE_AS_MISSING: &str =
    "negative-as-missing; observed-only; all-missing => 0 + mask";
/// 纯计数列不做任何填补。
pub const MISSING_RULE_COUNT_ONLY: &str = "count-only; no imputation";
/// 分母为零时置缺失掩码。
pub const MISSING_RULE_ZERO_DENOMINATOR: &str = "zero-denominator => missing mask";
/// 质量列在任何窗口都必须写出。
pub const MISSING_RULE_ALWAYS_EMITTED: &str = "quality-metric; always emitted";

/// 合同 §6.1 的五类语义分组。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
pub enum SemanticGroup {
    /// 流量规模。
    #[serde(rename = "volume")]
    Volume,
    /// 方向行为。
    #[serde(rename = "direction")]
    Direction,
    /// 流完成统计。
    #[serde(rename = "flow_stats")]
    FlowStats,
    /// 协议行为。
    #[serde(rename = "protocol")]
    Protocol,
    /// 质量信息。
    #[serde(rename = "quality")]
    Quality,
}

/// 相对被防御端点的方向语义，不携带任何端点身份。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
pub enum Direction {
    /// 流向被防御端点。
    #[serde(rename = "inbound")]
    Inbound,
    /// 由被防御端点流出。
    #[serde(rename = "outbound")]
    Outbound,
    /// 双向合计。
    #[serde(rename = "both")]
    Both,
}

/// 冻结的窗口聚合算子。
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
pub enum AggOp {
    /// 求和。
    #[serde(rename = "sum")]
    Sum,
    /// 对同名求和结果取 `log1p`。
    #[serde(rename = "log1p")]
    LogOneP,
    /// 最小值。
    #[serde(rename = "min")]
    Min,
    /// 最大值。
    #[serde(rename = "max")]
    Max,
    /// 均值。
    #[serde(rename = "mean")]
    Mean,
    /// 按类别或整体计数。
    #[serde(rename = "count_state")]
    CountState,
    /// 比例。
    #[serde(rename = "ratio")]
    Ratio,
    /// 差值。
    #[serde(rename = "diff")]
    Diff,
    /// 缺失计数。
    #[serde(rename = "missing_count")]
    MissingCount,
    /// 缺失率。
    #[serde(rename = "missing_rate")]
    MissingRate,
    /// 观测计数。
    #[serde(rename = "observed_count")]
    ObservedCount,
    /// 无流窗标记。
    #[serde(rename = "no_flow_flag")]
    NoFlowFlag,
}

impl AggOp {
    /// 返回该算子在输出列名中的后缀。
    #[must_use]
    pub const fn output_suffix(self) -> &'static str {
        match self {
            Self::Sum | Self::LogOneP => "sum",
            Self::Min => "min",
            Self::Max => "max",
            Self::Mean => "mean",
            Self::CountState => "count",
            Self::Ratio => "ratio",
            Self::Diff => "diff",
            Self::MissingCount => "missing_count",
            Self::MissingRate => "missing_rate",
            Self::ObservedCount => "observed_count",
            Self::NoFlowFlag => "flag",
        }
    }
}

/// 字段清单中的一个输出列。
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct FieldManifestEntry {
    /// 输出列名，统一 `win_` 前缀且全局唯一。
    pub output_name: String,
    /// 语义分组。
    pub semantic_group: SemanticGroup,
    /// 有序精确源列名，不得含通配符。
    pub source_columns: Vec<String>,
    /// 与 `source_columns` 一一对应的源模式类型。
    pub source_schema_types: Vec<String>,
    /// 可用时点，固定为窗口结束。
    pub availability_time: &'static str,
    /// 聚合算子。
    pub aggregation_operator: AggOp,
    /// 公式版本串。
    pub formula_version: &'static str,
    /// 输出单位。
    pub unit: String,
    /// 相对被防御端点的方向语义。
    pub direction_semantics: Option<Direction>,
    /// 缺失规则。
    pub missing_rule: &'static str,
    /// 冻结变换，本版本仅 `log1p`。
    pub transform: Option<&'static str>,
    /// 训练区拟合参数哈希，本版本无拟合参数。
    pub train_fit_parameter_hash: Option<String>,
    /// 是否作为生成目标。
    pub generation_target: bool,
    /// 允许消费该列的模型集合。
    pub allowed_models: Vec<String>,
}

/// 字段清单构造或校验失败。
#[derive(Debug)]
pub enum FieldManifestError {
    /// 条目的源列命中禁入黑名单。
    ForbiddenSourceColumn {
        /// 出问题的输出列名。
        output_name: String,
        /// 命中黑名单的源列名。
        column: String,
    },
    /// 条目引用了模式审计清单之外的源列。
    UnknownSourceColumn {
        /// 出问题的输出列名。
        output_name: String,
        /// 未登记的源列名。
        column: String,
    },
    /// 条目声明的源列类型与模式审计不一致。
    SourceTypeMismatch {
        /// 出问题的输出列名。
        output_name: String,
        /// 源列名。
        column: String,
        /// 模式审计中的类型。
        expected: String,
        /// 条目声明的类型。
        actual: String,
    },
    /// 源列与源类型数量不一致。
    SourceArityMismatch {
        /// 出问题的输出列名。
        output_name: String,
        /// 源列数量。
        columns: usize,
        /// 源类型数量。
        types: usize,
    },
    /// 源列名含通配符。
    WildcardSourceColumn {
        /// 出问题的输出列名。
        output_name: String,
        /// 含通配符的源列名。
        column: String,
    },
    /// 输出列名重复。
    DuplicateOutputName {
        /// 重复的输出列名。
        output_name: String,
    },
    /// 输出列名不满足冻结前缀。
    InvalidOutputName {
        /// 出问题的输出列名。
        output_name: String,
    },
    /// 清单为空。
    EmptyManifest,
    /// JSON 序列化失败。
    Json(serde_json::Error),
    /// 排他输出发布失败。
    Output(crate::output::OutputError),
}

impl Display for FieldManifestError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::ForbiddenSourceColumn {
                output_name,
                column,
            } => write!(formatter, "输出列 {output_name} 引用了禁入源列 {column}"),
            Self::UnknownSourceColumn {
                output_name,
                column,
            } => write!(
                formatter,
                "输出列 {output_name} 引用了模式审计之外的源列 {column}"
            ),
            Self::SourceTypeMismatch {
                output_name,
                column,
                expected,
                actual,
            } => write!(
                formatter,
                "输出列 {output_name} 的源列 {column} 类型不一致：审计为 {expected}，声明为 {actual}"
            ),
            Self::SourceArityMismatch {
                output_name,
                columns,
                types,
            } => write!(
                formatter,
                "输出列 {output_name} 的源列数 {columns} 与源类型数 {types} 不一致"
            ),
            Self::WildcardSourceColumn {
                output_name,
                column,
            } => write!(formatter, "输出列 {output_name} 的源列 {column} 含通配符"),
            Self::DuplicateOutputName { output_name } => {
                write!(formatter, "输出列名重复：{output_name}")
            }
            Self::InvalidOutputName { output_name } => {
                write!(formatter, "输出列名必须使用 win_ 前缀：{output_name}")
            }
            Self::EmptyManifest => write!(formatter, "字段清单不得为空"),
            Self::Json(error) => write!(formatter, "字段清单 JSON 处理失败：{error}"),
            Self::Output(error) => write!(formatter, "字段清单输出发布失败：{error}"),
        }
    }
}

impl Error for FieldManifestError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Json(source) => Some(source),
            Self::Output(source) => Some(source),
            _ => None,
        }
    }
}
