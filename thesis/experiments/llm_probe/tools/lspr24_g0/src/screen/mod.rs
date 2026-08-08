//! LSPR24 原始行的模式归一化。

mod source;

pub use source::{
    EndpointAssignment, EndpointDirection, NS_PER_MICROSECOND, NumericColumn, ScreenSourceError,
    parse_external_marker, resolve_protected_endpoints, utc_ns_from_micros,
};
