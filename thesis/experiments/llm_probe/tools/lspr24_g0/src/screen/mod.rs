//! LSPR24 原始行的模式归一化。

mod config;
mod history;
mod output;
mod source;
mod wide;

pub use config::{
    DEVELOPMENT_WIDE_CONFIG_VERSION, DevelopmentWideConfig, DevelopmentWideConfigError,
};
pub use wide::{
    DEVELOPMENT_WIDE_WINDOW_NS, DevelopmentWideError, DevelopmentWideReceipt,
    materialize_development_wide,
};

pub use source::{
    EndpointAssignment, EndpointDirection, NS_PER_MICROSECOND, NumericColumn, ScreenSourceError,
    parse_external_marker, resolve_protected_endpoints, utc_ns_from_micros,
};
