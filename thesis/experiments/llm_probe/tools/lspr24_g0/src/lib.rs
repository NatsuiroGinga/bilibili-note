//! LSPR24 G0-D 的确定性开发数据物化库。

pub mod canonical;
pub mod config;
pub mod development_router;
pub mod external_sort;
pub mod field_manifest;
pub mod formal_parquet;
pub mod gates;
pub mod input;
pub mod lspr_crossyear;
pub mod materialize;
pub mod output;
pub mod parquet_scan;
pub mod receipt;
pub mod schema_audit;
pub mod screen;
pub mod types;

pub use canonical::{
    CanonicalError, CanonicalValue, DatasetSemanticHasher, dataset_semantic_hash, sha256,
    tuple_encode,
};
pub use config::ScanConfig;
pub use development_router::{
    DevelopmentLabelRow, DevelopmentMemberId, DevelopmentRouter, DevelopmentRouting,
    DevelopmentSegment, DevelopmentSelectionMember, DevelopmentSplitReceipt,
    LSPR24_G0_CONTRACT_SHA256, LSPR24_G0_CONTRACT_VERSION, NormalizedLabel, RoutedDevelopmentLabel,
    RoutingError,
};
pub use external_sort::{
    ExternalSortConfig, ExternalSortError, ExternalSortSummary, stable_external_sort,
};
pub use field_manifest::{
    AVAILABILITY_TIME_WINDOW_END, AggOp, CONN_STATE_FALLBACK_BUCKET, CONN_STATE_VOCABULARY,
    Direction, FIELD_MANIFEST_REQUIRED_KEYS, FIELD_MANIFEST_VERSION, FORBIDDEN_SOURCE_COLUMNS,
    FieldManifestEntry, FieldManifestError, MISSING_RULE_ALWAYS_EMITTED, MISSING_RULE_COUNT_ONLY,
    MISSING_RULE_NEGATIVE_AS_MISSING, MISSING_RULE_OBSERVED_ONLY, MISSING_RULE_ZERO_DENOMINATOR,
    SemanticGroup, WINDOW_AGG_FORMULA_VERSION, build_field_manifest, field_manifest_json_bytes,
    output_column_slug, validate_field_manifest, write_field_manifest_json,
};
pub use formal_parquet::{
    FORMAL_DEVELOPMENT_CONFIG_SCHEMA_VERSION, FormalDevelopmentConfig,
    FormalDevelopmentMaterializationReceipt, FormalEntryError, UnlabeledDevelopmentSplitReceipt,
    prepare_unlabeled_development_split, run_formal_development_materialization,
};
pub use gates::{GateEvaluation, OverallDecision, evaluate_receipts};
pub use input::{
    InputSchemaError, TIME_COLUMN_NAMES, TIMESTAMP_LAST_COLUMN, TIMESTAMP_START_COLUMN,
};
pub use lspr_crossyear::{
    CROSSYEAR_CONFIG_VERSION, CrossyearConfig, CrossyearError, CrossyearReceipt,
    materialize_crossyear,
};
pub use materialize::{
    DevelopmentFeatureRow, DevelopmentMaterializationReceipt, MaterializeError, RawGateArtifacts,
    materialize_development, recompute_raw_gate_statuses,
};
pub use output::{
    CommitStage, OutputError, PartialOutput, PostPublishOperations, SystemPostPublishOperations,
};
pub use parquet_scan::{ScanError, TimeRow, TimeRowReader};
pub use receipt::{
    ArtifactRef, GateConfig, GateId, GateReceipt, GateStatus, ReceiptError, parse_gate_config,
    parse_gate_receipt,
};
pub use schema_audit::{
    AuditedColumn, DEDUP_PROJECTION_MANIFEST_VERSION, DedupProjectionManifest, ExcludedColumn,
    IDS_ALERT_COLUMNS, LABEL_COLUMNS, LSPR24_EXPECTED_COLUMN_COUNT, LSPR24_EXPECTED_ROW_COUNT,
    SCHEMA_AUDIT_VERSION, SchemaAudit, SchemaAuditError, UNSUPPORTED_ARROW_TYPE, arrow_type_name,
};
pub use screen::{
    EndpointAssignment, EndpointDirection, NS_PER_MICROSECOND, NumericColumn, ScreenSourceError,
    parse_external_marker, resolve_protected_endpoints, utc_ns_from_micros,
};
pub use types::{
    EndpointRoleOrder, IntegerOverflow, Sha256Digest, SortableRecord, SourceRowIndex, StableSortKey,
};
