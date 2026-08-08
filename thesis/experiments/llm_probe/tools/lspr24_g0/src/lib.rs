//! LSPR24 G0-D 的确定性开发数据物化库。

pub mod canonical;
pub mod config;
pub mod development_router;
pub mod external_sort;
pub mod formal_parquet;
pub mod gates;
pub mod input;
pub mod materialize;
pub mod output;
pub mod parquet_scan;
pub mod receipt;
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
    LSPR24_G0_CONTRACT_SHA256, LSPR24_G0_CONTRACT_VERSION, NormalizedLabel,
    RoutedDevelopmentLabel, RoutingError,
};
pub use external_sort::{
    ExternalSortConfig, ExternalSortError, ExternalSortSummary, stable_external_sort,
};
pub use formal_parquet::{
    FORMAL_DEVELOPMENT_CONFIG_SCHEMA_VERSION, FormalDevelopmentConfig,
    FormalDevelopmentMaterializationReceipt, FormalEntryError,
    UnlabeledDevelopmentSplitReceipt, prepare_unlabeled_development_split,
    run_formal_development_materialization,
};
pub use input::{
    InputSchemaError, TIMESTAMP_LAST_COLUMN, TIMESTAMP_START_COLUMN, TIME_COLUMN_NAMES,
};
pub use materialize::{
    DevelopmentFeatureRow, DevelopmentMaterializationReceipt, MaterializeError, RawGateArtifacts,
    materialize_development, recompute_raw_gate_statuses,
};
pub use gates::{GateEvaluation, OverallDecision, evaluate_receipts};
pub use output::{
    CommitStage, OutputError, PartialOutput, PostPublishOperations,
    SystemPostPublishOperations,
};
pub use parquet_scan::{ScanError, TimeRow, TimeRowReader};
pub use receipt::{
    ArtifactRef, GateConfig, GateId, GateReceipt, GateStatus, ReceiptError, parse_gate_config,
    parse_gate_receipt,
};
pub use screen::{
    EndpointAssignment, EndpointDirection, NS_PER_MICROSECOND, NumericColumn, ScreenSourceError,
    parse_external_marker, resolve_protected_endpoints, utc_ns_from_micros,
};
pub use types::{
    EndpointRoleOrder, IntegerOverflow, Sha256Digest, SortableRecord, SourceRowIndex,
    StableSortKey,
};
