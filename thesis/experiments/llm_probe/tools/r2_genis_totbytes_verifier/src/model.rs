use serde::{Deserialize, Serialize};

pub const SCHEMA_VERSION: &str = "flow_probe_r2_genis_totbytes_rust_v1";
pub const MEMBER_MAP_SCHEMA_VERSION: &str = "flow_probe_r2_genis_member_map_v1";
pub const PACKET_ARCHIVE_LOGICAL_PATH: &str = "zenodo:14919237/1-packets.zip";
pub const FLOW_ARCHIVE_LOGICAL_PATH: &str = "zenodo:14919237/2-flows.zip";

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ArtifactDigest {
    pub size_bytes: u64,
    pub md5: String,
    pub sha256: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MemberPair {
    pub schema_version: String,
    pub flow_member: String,
    pub packet_member: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct MemberAudit {
    pub binding_sha256: String,
    pub flow_member_size_bytes: u64,
    pub flow_member_sha256: String,
    pub packet_member_size_bytes: u64,
    pub packet_member_sha256: String,
    pub flow_rows_seen: u64,
    pub selected_flow_rows: u64,
    pub pcapng_interfaces: u64,
    pub pcapng_linktypes: Vec<u16>,
    pub packets_seen: u64,
    pub ip_packets_seen: u64,
    pub selected_packets: u64,
}

#[derive(Clone, Debug, Serialize)]
pub struct InputAudit {
    pub logical_path: String,
    pub size_bytes: u64,
    pub md5: String,
    pub sha256: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct PacketStatistics {
    pub packets_seen: u64,
    pub ip_packets_seen: u64,
    pub non_ip_packets_seen: u64,
    pub selected_packets: u64,
    pub ipv4_fragments_seen: u64,
    pub ipv6_fragments_seen: u64,
    pub unresolved_fragments: u64,
    pub structural_error_count: u64,
}

#[derive(Clone, Debug, Serialize)]
pub struct ComparisonRow {
    pub scope: &'static str,
    pub sample_id: Option<String>,
    pub group_id: String,
    pub flow_count: u64,
    pub csv_packet_count: u64,
    pub recomputed_packet_count: u64,
    pub csv_tot_bytes: u64,
    pub l2_wire_bytes: u64,
    pub l3_network_bytes: u64,
    pub l2_minus_csv: i64,
    pub l3_minus_csv: i64,
    pub l2_exact_match: bool,
    pub l3_exact_match: bool,
    pub match_status: &'static str,
    pub identity_status: &'static str,
    pub dur_inverse_count: u64,
    pub dur_interval_lower_ns: Option<i64>,
    pub dur_interval_upper_ns: Option<i64>,
    pub actual_duration_ns: Option<i64>,
    pub dur_interval_match: bool,
    pub source_binding_sha256: String,
    pub evidence_sha256: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct ScopeMatchSummary {
    pub compared_rows: u64,
    pub exact_integer_matches: u64,
    pub mismatches: u64,
}

#[derive(Clone, Debug, Serialize)]
pub struct LayerMatchSummary {
    pub flow: ScopeMatchSummary,
    pub group: ScopeMatchSummary,
    pub all_exact: bool,
}

#[derive(Clone, Debug, Serialize)]
pub struct Summary {
    pub schema_version: &'static str,
    pub status: &'static str,
    pub review_status: &'static str,
    pub decision: &'static str,
    pub decision_rule: &'static str,
    pub mapped_semantics: &'static str,
    pub expected_candidate_count: u64,
    pub compared_candidate_count: u64,
    pub compared_group_count: u64,
    pub all_rows_loaded: u64,
    pub candidate_identity_unique: u64,
    pub candidate_identity_missing: u64,
    pub candidate_identity_ambiguous: u64,
    pub dur_inverse_empty: u64,
    pub dur_interval_match: u64,
    pub dur_interval_mismatch: u64,
    pub repeated_flow_id_candidate_count: u64,
    pub l2_wire_match: LayerMatchSummary,
    pub l3_network_match: LayerMatchSummary,
    pub packet_count_matches: u64,
    pub packet_statistics: PacketStatistics,
    pub comparison_payload_sha256: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct ToolchainAudit {
    pub rustc_verbose_version: String,
    pub cargo_version: String,
    pub target_arch: &'static str,
    pub target_os: &'static str,
}

#[derive(Clone, Debug, Serialize)]
pub struct RunManifest {
    pub schema_version: &'static str,
    pub status: &'static str,
    pub review_status: &'static str,
    pub tool_name: &'static str,
    pub tool_version: &'static str,
    pub tool_revision: String,
    pub execution_code_lock_sha256: String,
    pub executable_size_bytes: u64,
    pub executable_sha256: String,
    pub toolchain: ToolchainAudit,
    pub inputs: Vec<InputAudit>,
    pub member_audits: Vec<MemberAudit>,
    pub expected_candidate_count: u64,
    pub all_rows_loaded: u64,
    pub candidate_identity_unique: u64,
    pub candidate_identity_missing: u64,
    pub candidate_identity_ambiguous: u64,
    pub dur_inverse_empty: u64,
    pub dur_interval_match: u64,
    pub dur_interval_mismatch: u64,
    pub repeated_flow_id_candidate_count: u64,
    pub time_tolerance_ns: u64,
    pub absolute_time_rounding_radius_ns: u64,
    pub max_pcapng_block_bytes: u64,
    pub max_flow_bindings: u64,
    pub max_fragment_contexts: u64,
    pub elapsed_milliseconds: u64,
    pub peak_rss_bytes: u64,
    pub packet_statistics: PacketStatistics,
    pub semantic_decision: &'static str,
    pub error_count: u64,
}

#[derive(Clone, Debug, Serialize)]
pub struct ArtifactEntry {
    pub relative_path: String,
    pub size_bytes: u64,
    pub sha256: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct ArtifactManifest {
    pub schema_version: &'static str,
    pub status: &'static str,
    pub review_status: &'static str,
    pub self_hash_excluded: bool,
    pub artifacts: Vec<ArtifactEntry>,
}
