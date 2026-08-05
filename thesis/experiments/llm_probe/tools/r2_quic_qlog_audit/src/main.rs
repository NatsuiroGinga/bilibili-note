use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, BufWriter, Read, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Instant;

use anyhow::{Context, Result, bail, ensure};
use clap::Parser;
use serde::de::{self, DeserializeSeed, IgnoredAny, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Serialize};
use serde_json::{Number, Value};
use sha2::{Digest, Sha256};

const DEFAULT_COMMIT: &str = "f237a20360b83868a197488c5b557f53e4b7e53c";
const DEFAULT_FILE_COUNT: usize = 200;
const DEFAULT_FILE_BYTES: u64 = 695_847_525;
const DEFAULT_QLOG_COUNT: usize = 89;
const DEFAULT_QLOG_BYTES: u64 = 630_227_334;
const EXPECTED_QLOG_VERSION: &str = "draft-02-wip";
const EMPTY_SHA256: &str = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

#[derive(Debug, Parser)]
#[command(version, about)]
struct Cli {
    /// 固定提交的 QUIC-MedNetCom 根目录。
    #[arg(long)]
    source_root: PathBuf,

    /// 覆盖 200 个上游普通文件的 SHA-256 清单。
    #[arg(long)]
    source_manifest: PathBuf,

    /// 本轮独立构建输出目录；已存在时拒绝覆盖。
    #[arg(long)]
    output: PathBuf,

    /// 预期上游提交。
    #[arg(long, default_value = DEFAULT_COMMIT)]
    expected_commit: String,

    /// 预期上游普通文件数。
    #[arg(long, default_value_t = DEFAULT_FILE_COUNT)]
    expected_file_count: usize,

    /// 预期上游普通文件总字节数。
    #[arg(long, default_value_t = DEFAULT_FILE_BYTES)]
    expected_file_bytes: u64,

    /// 预期 qlog 文件数。
    #[arg(long, default_value_t = DEFAULT_QLOG_COUNT)]
    expected_qlog_count: usize,

    /// 预期 qlog 文件总字节数。
    #[arg(long, default_value_t = DEFAULT_QLOG_BYTES)]
    expected_qlog_bytes: u64,

    /// 与模型结果和安全标签无关的确定性先导轨迹数。
    #[arg(long, default_value_t = 16)]
    pilot_count: usize,
}

#[derive(Debug, Clone)]
struct SourceEntry {
    relative_path: String,
    sha256: String,
    size_bytes: u64,
}

#[derive(Debug, Default)]
struct ParsedQlog {
    qlog_version: Option<String>,
    title: Option<String>,
    traces: Vec<TraceAudit>,
}

#[derive(Debug, Default)]
struct TraceAudit {
    vantage_point: Option<String>,
    group_id: Option<String>,
    original_connection_id: Option<String>,
    event_fields: Vec<String>,
    event_count: u64,
    first_time_ns: Option<u64>,
    last_time_ns: Option<u64>,
    time_is_monotonic: bool,
    invalid_event_count: u64,
    unknown_event_count: u64,
    packet_sent_count: u64,
    packet_received_count: u64,
    packet_number_count: u64,
    packet_size_count: u64,
    packet_number_spaces: BTreeSet<String>,
    ack_frame_count: u64,
    ack_range_count: u64,
    ack_delay_count: u64,
    metrics_count: u64,
    complete_rtt_count: u64,
    bytes_in_flight_count: u64,
    congestion_window_count: u64,
    packet_lost_count: u64,
    valid_ack_relation_count: u64,
    unresolved_ack_relation_count: u64,
    valid_packet_lost_relation_count: u64,
    unresolved_packet_lost_relation_count: u64,
    pto_event_count: u64,
    quic_versions: BTreeSet<String>,
    issues: BTreeSet<String>,
    local_sent_packets: BTreeMap<String, PacketHistory>,
    peer_sent_packets: BTreeMap<String, PacketHistory>,
    relations_by_packet_space: BTreeMap<String, RelationAudit>,
}

#[derive(Debug, Clone, Copy)]
struct PacketObservation {
    time_ns: u64,
    event_index: u64,
}

#[derive(Debug, Default)]
struct PacketHistory {
    observations: BTreeMap<u64, PacketObservation>,
    contiguous_intervals: BTreeMap<u64, u64>,
}

impl PacketHistory {
    fn insert(&mut self, packet_number: u64, observation: PacketObservation) {
        if self.observations.contains_key(&packet_number) {
            return;
        }
        self.observations.insert(packet_number, observation);

        let left = self
            .contiguous_intervals
            .range(..=packet_number)
            .next_back()
            .map(|(&start, &end)| (start, end));
        if left.is_some_and(|(_, end)| end >= packet_number) {
            return;
        }
        let right = packet_number.checked_add(1).and_then(|next| {
            self.contiguous_intervals
                .get_key_value(&next)
                .map(|(&start, &end)| (start, end))
        });
        let joins_left = left.is_some_and(|(_, end)| end.checked_add(1) == Some(packet_number));

        match (joins_left, right) {
            (true, Some((right_start, right_end))) => {
                let left_start = left.expect("左区间已经验证存在").0;
                self.contiguous_intervals.insert(left_start, right_end);
                self.contiguous_intervals.remove(&right_start);
            }
            (true, None) => {
                let left_start = left.expect("左区间已经验证存在").0;
                self.contiguous_intervals.insert(left_start, packet_number);
            }
            (false, Some((right_start, right_end))) => {
                self.contiguous_intervals.remove(&right_start);
                self.contiguous_intervals.insert(packet_number, right_end);
            }
            (false, None) => {
                self.contiguous_intervals.insert(packet_number, packet_number);
            }
        }
    }

    fn contains_prior_range(
        &self,
        start: u64,
        end: u64,
        relation_time_ns: u64,
        relation_event_index: u64,
    ) -> bool {
        let Some((_, &interval_end)) = self.contiguous_intervals.range(..=start).next_back() else {
            return false;
        };
        if interval_end < end {
            return false;
        }
        let Some(first) = self.observations.get(&start) else {
            return false;
        };
        let Some(last) = self.observations.get(&end) else {
            return false;
        };
        first.event_index < relation_event_index
            && last.event_index < relation_event_index
            && first.time_ns <= relation_time_ns
            && last.time_ns <= relation_time_ns
    }

    fn contains_prior_packet(
        &self,
        packet_number: u64,
        relation_time_ns: u64,
        relation_event_index: u64,
    ) -> bool {
        self.observations.get(&packet_number).is_some_and(|observation| {
            observation.event_index < relation_event_index && observation.time_ns <= relation_time_ns
        })
    }
}

#[derive(Debug, Clone, Default, Serialize)]
struct RelationAudit {
    valid_ack_ranges: u64,
    unresolved_ack_ranges: u64,
    valid_packet_losses: u64,
    unresolved_packet_losses: u64,
    first_valid_ack_time_ns: Option<u64>,
    first_valid_packet_loss_time_ns: Option<u64>,
}

impl TraceAudit {
    fn new() -> Self {
        Self {
            time_is_monotonic: true,
            ..Self::default()
        }
    }

    fn observe_event(&mut self, time: &Number, category: &str, name: &str, data: &Value) {
        self.event_count = self.event_count.saturating_add(1);
        let event_time_ns = match decimal_milliseconds_to_nanoseconds(&time.to_string()) {
            Ok(value) => value,
            Err(error) => {
                self.invalid_event_count = self.invalid_event_count.saturating_add(1);
                self.issues.insert(format!("事件时间无法解释：{error}"));
                return;
            }
        };
        if !(1_500_000_000_000_000_000..=2_000_000_000_000_000_000).contains(&event_time_ns) {
            self.issues.insert("事件时间不符合绝对 Unix 毫秒量级".to_owned());
        }
        if let Some(previous) = self.last_time_ns
            && event_time_ns < previous
        {
            self.time_is_monotonic = false;
            self.issues.insert("事件时间发生回退".to_owned());
        }
        self.first_time_ns.get_or_insert(event_time_ns);
        self.last_time_ns = Some(event_time_ns);

        let event_index = self.event_count;
        match (category, name) {
            ("transport", "packet_sent") => self.observe_packet(data, true, event_time_ns, event_index),
            ("transport", "packet_received") => {
                self.observe_packet(data, false, event_time_ns, event_index)
            }
            ("transport", "connection_started") => self.observe_connection_started(data),
            ("recovery", "metrics_updated") => self.observe_metrics(data),
            ("recovery", "packet_lost") => {
                self.observe_packet_lost(data, event_time_ns, event_index)
            }
            _ => {
                self.unknown_event_count = self.unknown_event_count.saturating_add(1);
                self.issues
                    .insert(format!("未映射事件：{category}:{name}"));
            }
        }
    }

    fn observe_packet(&mut self, data: &Value, is_sent: bool, event_time_ns: u64, event_index: u64) {
        if is_sent {
            self.packet_sent_count = self.packet_sent_count.saturating_add(1);
        } else {
            self.packet_received_count = self.packet_received_count.saturating_add(1);
        }
        let Some(object) = data.as_object() else {
            self.invalid_event_count = self.invalid_event_count.saturating_add(1);
            self.issues.insert("包事件 data 不是对象".to_owned());
            return;
        };
        let packet_space = object
            .get("packet_type")
            .and_then(Value::as_str)
            .and_then(normalize_packet_number_space);
        if let Some(space) = packet_space {
            self.packet_number_spaces.insert(space.to_owned());
        } else {
            self.issues.insert("包事件缺少可映射的包号空间".to_owned());
        }
        let header = object.get("header").and_then(Value::as_object);
        let packet_number = header
            .and_then(|value| value.get("packet_number"))
            .and_then(value_to_u64);
        if packet_number.is_some() {
            self.packet_number_count = self.packet_number_count.saturating_add(1);
        } else {
            self.issues.insert("包事件缺少合法 packet_number".to_owned());
        }
        if header
            .and_then(|value| value.get("packet_size"))
            .and_then(value_to_u64)
            .is_some()
        {
            self.packet_size_count = self.packet_size_count.saturating_add(1);
        } else {
            self.issues.insert("包事件缺少合法 packet_size".to_owned());
        }
        if let Some(version) = header
            .and_then(|value| value.get("version"))
            .and_then(Value::as_str)
        {
            self.quic_versions.insert(version.to_owned());
        }
        if let (Some(space), Some(number)) = (packet_space, packet_number) {
            let observation = PacketObservation {
                time_ns: event_time_ns,
                event_index,
            };
            let histories = if is_sent {
                &mut self.local_sent_packets
            } else {
                &mut self.peer_sent_packets
            };
            histories.entry(space.to_owned()).or_default().insert(number, observation);
        }
        if let Some(frames) = object.get("frames").and_then(Value::as_array) {
            for frame in frames {
                if frame.get("frame_type").and_then(Value::as_str) == Some("ack") {
                    self.observe_ack_frame(frame, packet_space, is_sent, event_time_ns, event_index);
                }
            }
        }
    }

    fn observe_ack_frame(
        &mut self,
        frame: &Value,
        packet_space: Option<&'static str>,
        carrier_is_sent: bool,
        event_time_ns: u64,
        event_index: u64,
    ) {
        self.ack_frame_count = self.ack_frame_count.saturating_add(1);
        if frame.get("ack_delay").and_then(value_to_u64).is_some() {
            self.ack_delay_count = self.ack_delay_count.saturating_add(1);
        }
        let Some(ranges) = frame.get("acked_ranges").and_then(Value::as_array) else {
            self.issues.insert("ACK 帧缺少 acked_ranges".to_owned());
            self.record_unresolved_ack(packet_space);
            return;
        };
        for range in ranges {
            let Some(values) = range.as_array() else {
                self.issues.insert("ACK 范围不是数组".to_owned());
                self.record_unresolved_ack(packet_space);
                continue;
            };
            if !(values.len() == 1 || values.len() == 2) {
                self.issues.insert("ACK 范围长度不是 1 或 2".to_owned());
                self.record_unresolved_ack(packet_space);
                continue;
            }
            let Some(start) = values.first().and_then(value_to_u64) else {
                self.issues.insert("ACK 范围起点不是非负整数".to_owned());
                self.record_unresolved_ack(packet_space);
                continue;
            };
            let end = values.get(1).and_then(value_to_u64).unwrap_or(start);
            if start > end {
                self.issues.insert("ACK 范围起点大于终点".to_owned());
                self.record_unresolved_ack(packet_space);
                continue;
            }
            self.ack_range_count = self.ack_range_count.saturating_add(1);
            let related = packet_space.is_some_and(|space| {
                let histories = if carrier_is_sent {
                    &self.peer_sent_packets
                } else {
                    &self.local_sent_packets
                };
                histories.get(space).is_some_and(|history| {
                    history.contains_prior_range(start, end, event_time_ns, event_index)
                })
            });
            if related {
                self.valid_ack_relation_count = self.valid_ack_relation_count.saturating_add(1);
                let relation = self
                    .relations_by_packet_space
                    .entry(packet_space.expect("有效 ACK 关系必须有包号空间").to_owned())
                    .or_default();
                relation.valid_ack_ranges = relation.valid_ack_ranges.saturating_add(1);
                relation.first_valid_ack_time_ns.get_or_insert(event_time_ns);
            } else {
                self.issues
                    .insert("ACK 范围无法关联同包号空间的对向先前发送包".to_owned());
                self.record_unresolved_ack(packet_space);
            }
        }
    }

    fn record_unresolved_ack(&mut self, packet_space: Option<&str>) {
        self.unresolved_ack_relation_count = self.unresolved_ack_relation_count.saturating_add(1);
        if let Some(space) = packet_space {
            let relation = self.relations_by_packet_space.entry(space.to_owned()).or_default();
            relation.unresolved_ack_ranges = relation.unresolved_ack_ranges.saturating_add(1);
        }
    }

    fn observe_connection_started(&mut self, data: &Value) {
        if let Some(version) = data.get("quic_version").and_then(Value::as_str) {
            self.quic_versions.insert(version.to_owned());
        }
    }

    fn observe_metrics(&mut self, data: &Value) {
        self.metrics_count = self.metrics_count.saturating_add(1);
        let latest = duration_field_to_nanoseconds(data, "latest_rtt", &mut self.issues);
        let minimum = duration_field_to_nanoseconds(data, "min_rtt", &mut self.issues);
        let smoothed = duration_field_to_nanoseconds(data, "smoothed_rtt", &mut self.issues);
        if latest.is_some() && minimum.is_some() && smoothed.is_some() {
            self.complete_rtt_count = self.complete_rtt_count.saturating_add(1);
        }
        if data.get("bytes_in_flight").and_then(value_to_u64).is_some() {
            self.bytes_in_flight_count = self.bytes_in_flight_count.saturating_add(1);
        } else {
            self.issues
                .insert("恢复指标缺少合法 bytes_in_flight".to_owned());
        }
        if data
            .get("congestion_window")
            .and_then(value_to_u64)
            .is_some_and(|value| value > 0)
        {
            self.congestion_window_count = self.congestion_window_count.saturating_add(1);
        } else {
            self.issues
                .insert("恢复指标缺少正数 congestion_window".to_owned());
        }
    }

    fn observe_packet_lost(&mut self, data: &Value, event_time_ns: u64, event_index: u64) {
        self.packet_lost_count = self.packet_lost_count.saturating_add(1);
        let packet_space = data
            .get("packet_type")
            .and_then(Value::as_str)
            .and_then(normalize_packet_number_space);
        let packet_number = data.get("packet_number").and_then(value_to_u64);
        let trigger = data.get("trigger").and_then(Value::as_str);
        if packet_space.is_none() || packet_number.is_none() || !trigger.is_some_and(|value| !value.is_empty()) {
            self.issues.insert("packet_lost 缺少包号空间、包号或触发原因".to_owned());
            self.record_unresolved_packet_loss(packet_space);
            return;
        }
        let space = packet_space.expect("packet_lost 包号空间已经验证存在");
        let number = packet_number.expect("packet_lost 包号已经验证存在");
        let related = self.local_sent_packets.get(space).is_some_and(|history| {
            history.contains_prior_packet(number, event_time_ns, event_index)
        });
        if related {
            self.valid_packet_lost_relation_count =
                self.valid_packet_lost_relation_count.saturating_add(1);
            let relation = self.relations_by_packet_space.entry(space.to_owned()).or_default();
            relation.valid_packet_losses = relation.valid_packet_losses.saturating_add(1);
            relation.first_valid_packet_loss_time_ns.get_or_insert(event_time_ns);
        } else {
            self.issues
                .insert("packet_lost 无法关联同包号空间的本端先前发送包".to_owned());
            self.record_unresolved_packet_loss(Some(space));
        }
    }

    fn record_unresolved_packet_loss(&mut self, packet_space: Option<&str>) {
        self.unresolved_packet_lost_relation_count =
            self.unresolved_packet_lost_relation_count.saturating_add(1);
        if let Some(space) = packet_space {
            let relation = self.relations_by_packet_space.entry(space.to_owned()).or_default();
            relation.unresolved_packet_losses = relation.unresolved_packet_losses.saturating_add(1);
        }
    }

    fn core_gate_failures(&self, qlog_version: Option<&str>) -> Vec<String> {
        let mut failures = Vec::new();
        if qlog_version != Some(EXPECTED_QLOG_VERSION) {
            failures.push("qlog_version_not_draft_02_wip".to_owned());
        }
        if self.vantage_point.as_deref() != Some("server") {
            failures.push("vantage_point_not_server".to_owned());
        }
        if self.event_fields != ["time", "category", "event", "data"] {
            failures.push("event_fields_contract_mismatch".to_owned());
        }
        if !self.time_is_monotonic || self.first_time_ns.is_none() || self.last_time_ns.is_none() {
            failures.push("event_time_not_interpretable".to_owned());
        }
        if self.invalid_event_count > 0 || self.unknown_event_count > 0 {
            failures.push("event_semantics_invalid_or_unknown".to_owned());
        }
        if self.packet_sent_count == 0 || self.packet_number_count == 0 {
            failures.push("sent_packet_number_missing".to_owned());
        }
        if self.packet_number_count != self.packet_sent_count.saturating_add(self.packet_received_count) {
            failures.push("packet_number_incomplete".to_owned());
        }
        if self.packet_size_count != self.packet_sent_count.saturating_add(self.packet_received_count) {
            failures.push("passive_packet_size_incomplete".to_owned());
        }
        for required in ["initial", "handshake", "application_data"] {
            if !self.packet_number_spaces.contains(required) {
                failures.push(format!("packet_number_space_missing_{required}"));
            }
        }
        if self.ack_frame_count == 0 || self.ack_range_count == 0 {
            failures.push("ack_ranges_missing".to_owned());
        }
        if self.valid_ack_relation_count == 0 {
            failures.push("valid_ack_relation_missing".to_owned());
        }
        if self
            .relations_by_packet_space
            .get("application_data")
            .map_or(0, |relation| relation.valid_ack_ranges)
            == 0
        {
            failures.push("application_data_ack_relation_missing".to_owned());
        }
        if self.unresolved_ack_relation_count > 0 {
            failures.push("unresolved_ack_relations_present".to_owned());
        }
        if self.complete_rtt_count == 0 {
            failures.push("complete_rtt_missing".to_owned());
        }
        if self.valid_packet_lost_relation_count == 0 {
            failures.push("endpoint_packet_loss_missing".to_owned());
        }
        if self.unresolved_packet_lost_relation_count > 0 {
            failures.push("unresolved_packet_loss_relations_present".to_owned());
        }
        if self.bytes_in_flight_count == 0 {
            failures.push("bytes_in_flight_missing".to_owned());
        }
        if self.congestion_window_count == 0 {
            failures.push("congestion_window_missing".to_owned());
        }
        if !self.issues.is_empty() {
            failures.push("hard_semantic_issues_present".to_owned());
            failures.extend(
                self.issues
                    .iter()
                    .map(|issue| format!("hard_semantic_issue:{issue}")),
            );
        }
        failures
    }

    fn relation_counts_by_packet_space(&self) -> BTreeMap<String, RelationAudit> {
        let mut relations = self.relations_by_packet_space.clone();
        for space in ["initial", "handshake", "application_data"] {
            relations.entry(space.to_owned()).or_default();
        }
        relations
    }

    fn allowed_missing_mask(&self) -> AllowedMissingMask {
        AllowedMissingMask {
            ack_delay_available: self.ack_delay_count > 0,
            ack_delay_complete: self.ack_delay_count == self.ack_frame_count,
            pto_event_available: self.pto_event_count > 0,
        }
    }

    fn allowed_missing_counts(&self) -> AllowedMissingCounts {
        AllowedMissingCounts {
            ack_delay_missing_frames: self.ack_frame_count.saturating_sub(self.ack_delay_count),
            pto_event_absent_trace: u64::from(self.pto_event_count == 0),
        }
    }
}

struct QlogSeed<'a>(&'a mut ParsedQlog);

impl<'de> DeserializeSeed<'de> for QlogSeed<'_> {
    type Value = ();

    fn deserialize<D>(self, deserializer: D) -> std::result::Result<Self::Value, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_map(QlogVisitor(self.0))
    }
}

struct QlogVisitor<'a>(&'a mut ParsedQlog);

impl<'de> Visitor<'de> for QlogVisitor<'_> {
    type Value = ();

    fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str("qlog 顶层对象")
    }

    fn visit_map<M>(self, mut map: M) -> std::result::Result<Self::Value, M::Error>
    where
        M: MapAccess<'de>,
    {
        while let Some(key) = map.next_key::<String>()? {
            match key.as_str() {
                "qlog_version" => self.0.qlog_version = Some(map.next_value()?),
                "title" => self.0.title = Some(map.next_value()?),
                "traces" => map.next_value_seed(TracesSeed(&mut self.0.traces))?,
                _ => {
                    map.next_value::<IgnoredAny>()?;
                }
            }
        }
        Ok(())
    }
}

struct TracesSeed<'a>(&'a mut Vec<TraceAudit>);

impl<'de> DeserializeSeed<'de> for TracesSeed<'_> {
    type Value = ();

    fn deserialize<D>(self, deserializer: D) -> std::result::Result<Self::Value, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_seq(TracesVisitor(self.0))
    }
}

struct TracesVisitor<'a>(&'a mut Vec<TraceAudit>);

impl<'de> Visitor<'de> for TracesVisitor<'_> {
    type Value = ();

    fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str("qlog traces 数组")
    }

    fn visit_seq<A>(self, mut sequence: A) -> std::result::Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        loop {
            let mut trace = TraceAudit::new();
            let Some(()) = sequence.next_element_seed(TraceSeed(&mut trace))? else {
                break;
            };
            self.0.push(trace);
        }
        Ok(())
    }
}

struct TraceSeed<'a>(&'a mut TraceAudit);

impl<'de> DeserializeSeed<'de> for TraceSeed<'_> {
    type Value = ();

    fn deserialize<D>(self, deserializer: D) -> std::result::Result<Self::Value, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_map(TraceVisitor(self.0))
    }
}

struct TraceVisitor<'a>(&'a mut TraceAudit);

impl<'de> Visitor<'de> for TraceVisitor<'_> {
    type Value = ();

    fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str("qlog trace 对象")
    }

    fn visit_map<M>(self, mut map: M) -> std::result::Result<Self::Value, M::Error>
    where
        M: MapAccess<'de>,
    {
        while let Some(key) = map.next_key::<String>()? {
            match key.as_str() {
                "vantage_point" => {
                    let value: Value = map.next_value()?;
                    self.0.vantage_point = value
                        .get("type")
                        .and_then(Value::as_str)
                        .map(str::to_owned);
                }
                "common_fields" => {
                    let value: Value = map.next_value()?;
                    self.0.group_id = value
                        .get("group_id")
                        .and_then(Value::as_str)
                        .map(str::to_owned);
                    self.0.original_connection_id = value
                        .get("ODCID")
                        .and_then(Value::as_str)
                        .map(str::to_owned);
                }
                "event_fields" => self.0.event_fields = map.next_value()?,
                "events" => map.next_value_seed(EventsSeed(self.0))?,
                _ => {
                    map.next_value::<IgnoredAny>()?;
                }
            }
        }
        Ok(())
    }
}

struct EventsSeed<'a>(&'a mut TraceAudit);

impl<'de> DeserializeSeed<'de> for EventsSeed<'_> {
    type Value = ();

    fn deserialize<D>(self, deserializer: D) -> std::result::Result<Self::Value, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_seq(EventsVisitor(self.0))
    }
}

struct EventsVisitor<'a>(&'a mut TraceAudit);

impl<'de> Visitor<'de> for EventsVisitor<'_> {
    type Value = ();

    fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str("qlog events 数组")
    }

    fn visit_seq<A>(self, mut sequence: A) -> std::result::Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        while let Some(()) = sequence.next_element_seed(EventSeed(self.0))? {}
        Ok(())
    }
}

struct EventSeed<'a>(&'a mut TraceAudit);

impl<'de> DeserializeSeed<'de> for EventSeed<'_> {
    type Value = ();

    fn deserialize<D>(self, deserializer: D) -> std::result::Result<Self::Value, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_seq(EventVisitor(self.0))
    }
}

struct EventVisitor<'a>(&'a mut TraceAudit);

impl<'de> Visitor<'de> for EventVisitor<'_> {
    type Value = ();

    fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str("[time, category, event, data] qlog 事件")
    }

    fn visit_seq<A>(self, mut sequence: A) -> std::result::Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        let time: Number = required_element(&mut sequence, "time")?;
        let category: String = required_element(&mut sequence, "category")?;
        let name: String = required_element(&mut sequence, "event")?;
        let data: Value = required_element(&mut sequence, "data")?;
        if sequence.next_element::<IgnoredAny>()?.is_some() {
            return Err(de::Error::custom("qlog 事件包含超过 4 个字段"));
        }
        self.0.observe_event(&time, &category, &name, &data);
        Ok(())
    }
}

fn required_element<'de, A, T>(sequence: &mut A, name: &str) -> std::result::Result<T, A::Error>
where
    A: SeqAccess<'de>,
    T: Deserialize<'de>,
{
    sequence
        .next_element()?
        .ok_or_else(|| de::Error::custom(format!("qlog 事件缺少 {name}")))
}

#[derive(Debug, Serialize)]
struct SourceLock {
    dataset: &'static str,
    source_root: &'static str,
    upstream_commit: String,
    manifest_sha256: String,
    regular_file_count: usize,
    regular_file_bytes: u64,
    git_tree_symlink_count: usize,
    git_tree_symlink_bytes: u64,
    qlog_file_count: usize,
    qlog_file_bytes: u64,
    empty_qlog_count: usize,
    raw_data_redistribution: &'static str,
    malicious_labels: &'static str,
}

#[derive(Debug, Clone, Copy, Serialize)]
struct CoverageMask {
    sent_packet_number: bool,
    ack_ranges: bool,
    latest_min_smoothed_rtt: bool,
    endpoint_packet_loss: bool,
    bytes_in_flight: bool,
    congestion_window: bool,
    pto_event: bool,
}

#[derive(Debug, Clone, Copy, Serialize)]
struct AllowedMissingMask {
    ack_delay_available: bool,
    ack_delay_complete: bool,
    pto_event_available: bool,
}

#[derive(Debug, Clone, Copy, Serialize)]
struct AllowedMissingCounts {
    ack_delay_missing_frames: u64,
    pto_event_absent_trace: u64,
}

#[derive(Debug, Serialize)]
struct EventCounts {
    total: u64,
    packet_sent: u64,
    packet_received: u64,
    ack_frames: u64,
    ack_ranges: u64,
    valid_ack_relations: u64,
    unresolved_ack_relations: u64,
    metrics_updated: u64,
    complete_rtt: u64,
    bytes_in_flight: u64,
    congestion_window: u64,
    packet_lost: u64,
    valid_packet_lost_relations: u64,
    unresolved_packet_lost_relations: u64,
    pto_events: u64,
}

#[derive(Debug, Serialize)]
struct TraceManifestRow {
    trace_id: String,
    canonical_path: String,
    content_sha256: String,
    size_bytes: u64,
    duplicate_alias_paths: Vec<String>,
    qlog_version: String,
    observer_vantage_point: String,
    observer_role: &'static str,
    group_id_sha256: Option<String>,
    original_connection_id_sha256: Option<String>,
    first_event_time_ns: u64,
    last_event_time_ns: u64,
    duration_ns: u64,
    time_is_monotonic: bool,
    packet_number_spaces: Vec<String>,
    quic_versions: Vec<String>,
    event_counts: EventCounts,
    relation_counts_by_packet_space: BTreeMap<String, RelationAudit>,
    deployment_observable_mask: BTreeMap<&'static str, bool>,
    privileged_truth_mask: CoverageMask,
    allowed_missing_mask: AllowedMissingMask,
    allowed_missing_counts: AllowedMissingCounts,
    hard_issue_count: usize,
    hard_issues: Vec<String>,
    malicious_label: Option<String>,
}

#[derive(Debug, Serialize)]
struct ExcludedTraceRow {
    source_path: String,
    content_sha256: String,
    size_bytes: u64,
    exclusion_reasons: Vec<String>,
    source_kind: &'static str,
    canonical_trace_path: Option<String>,
    relation_counts_by_packet_space: BTreeMap<String, RelationAudit>,
    allowed_missing_mask: Option<AllowedMissingMask>,
    allowed_missing_counts: Option<AllowedMissingCounts>,
    hard_issue_count: usize,
    hard_issues: Vec<String>,
}

#[derive(Debug, Serialize)]
struct PilotRow {
    pilot_rank: usize,
    selection_rule: &'static str,
    trace_id: String,
    canonical_path: String,
    content_sha256: String,
    size_bytes: u64,
    field_coverage: CoverageMask,
    relation_counts_by_packet_space: BTreeMap<String, RelationAudit>,
    allowed_missing_mask: AllowedMissingMask,
    allowed_missing_counts: AllowedMissingCounts,
    hard_issue_count: usize,
    event_time_unit: &'static str,
    rtt_unit: &'static str,
    byte_unit: &'static str,
    use_boundary: &'static str,
}

#[derive(Debug, Serialize)]
struct FieldCoverage {
    candidate_trace_count: usize,
    excluded_qlog_count: usize,
    excluded_non_qlog_alias_count: usize,
    candidate_event_count: u64,
    candidate_packet_sent_count: u64,
    candidate_packet_received_count: u64,
    candidate_ack_frame_count: u64,
    candidate_ack_range_count: u64,
    candidate_valid_ack_relation_count: u64,
    candidate_unresolved_ack_relation_count: u64,
    candidate_complete_rtt_count: u64,
    candidate_packet_lost_count: u64,
    candidate_valid_packet_lost_relation_count: u64,
    candidate_unresolved_packet_lost_relation_count: u64,
    candidate_metrics_count: u64,
    candidate_bytes_in_flight_count: u64,
    candidate_congestion_window_count: u64,
    candidate_pto_event_count: u64,
    traces_with_pto: usize,
    candidate_hard_issue_count: usize,
    pto_interpretation: &'static str,
}

#[derive(Debug, Serialize)]
struct UnitContract {
    qlog_schema: &'static str,
    event_time: UnitField,
    rtt_metrics: UnitField,
    ack_delay: UnitField,
    packet_and_state_bytes: UnitField,
    direction: DirectionContract,
    packet_number_spaces: BTreeMap<&'static str, &'static str>,
    deployment_observable_fields: Vec<&'static str>,
    training_only_privileged_truth: Vec<&'static str>,
    forbidden_deployment_fields: Vec<&'static str>,
    missing_value_policy: &'static str,
}

#[derive(Debug, Serialize)]
struct UnitField {
    source_unit: &'static str,
    normalized_unit: &'static str,
    conversion: &'static str,
    evidence: &'static str,
}

#[derive(Debug, Serialize)]
struct DirectionContract {
    source: &'static str,
    normalized: &'static str,
    observer: &'static str,
}

#[derive(Debug, Serialize)]
struct AuditSummary {
    status: &'static str,
    dataset: &'static str,
    qlog_files_seen: usize,
    qlog_files_parsed: usize,
    upstream_empty_placeholders: usize,
    candidate_traces: usize,
    excluded_qlogs: usize,
    duplicate_non_qlog_aliases: usize,
    pilot_traces: usize,
    candidate_total_events: u64,
    hard_gate: &'static str,
    pto_status: &'static str,
    label_status: &'static str,
    release_scope: &'static str,
}

fn main() {
    let cli = Cli::parse();
    if let Err(error) = run(cli) {
        eprintln!("错误：{error:#}");
        std::process::exit(1);
    }
}

fn run(cli: Cli) -> Result<()> {
    let started = Instant::now();
    ensure!(!cli.output.exists(), "输出目录已存在，拒绝覆盖");
    ensure!(cli.pilot_count > 0, "先导轨迹数必须为正数");
    let entries = verify_source_lock(&cli)?;
    let manifest_sha256 = hash_file(&cli.source_manifest)?.0;
    let commit = git_stdout(&cli.source_root, &["rev-parse", "HEAD"])?;
    ensure!(commit == cli.expected_commit, "上游提交不匹配");
    run_git_fsck(&cli.source_root)?;

    let mut by_digest: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for entry in &entries {
        by_digest
            .entry(entry.sha256.clone())
            .or_default()
            .push(entry.relative_path.clone());
    }
    for paths in by_digest.values_mut() {
        paths.sort();
    }

    let mut qlogs: Vec<&SourceEntry> = entries
        .iter()
        .filter(|entry| entry.relative_path.ends_with(".qlog"))
        .collect();
    qlogs.sort_by(|left, right| left.relative_path.cmp(&right.relative_path));

    let mut rows = Vec::new();
    let mut excluded = Vec::new();
    let mut parsed_count = 0usize;
    let mut empty_count = 0usize;
    let mut non_qlog_alias_count = 0usize;

    for entry in qlogs {
        if entry.size_bytes == 0 {
            ensure!(entry.sha256 == EMPTY_SHA256, "零字节 qlog 的摘要不是空内容摘要");
            empty_count += 1;
            excluded.push(ExcludedTraceRow {
                source_path: entry.relative_path.clone(),
                content_sha256: entry.sha256.clone(),
                size_bytes: 0,
                exclusion_reasons: vec!["upstream_zero_byte_placeholder".to_owned()],
                source_kind: "qlog",
                canonical_trace_path: None,
                relation_counts_by_packet_space: BTreeMap::new(),
                allowed_missing_mask: None,
                allowed_missing_counts: None,
                hard_issue_count: 0,
                hard_issues: Vec::new(),
            });
            continue;
        }

        let parsed = scan_qlog(&cli.source_root.join(&entry.relative_path))
            .with_context(|| format!("解析 qlog 失败：{}", entry.relative_path))?;
        parsed_count += 1;
        let mut reasons = Vec::new();
        if parsed.traces.len() != 1 {
            reasons.push(format!("trace_count_not_one:{}", parsed.traces.len()));
        }
        if parsed.traces.len() == 1 {
            reasons.extend(parsed.traces[0].core_gate_failures(parsed.qlog_version.as_deref()));
        }
        if !reasons.is_empty() {
            reasons.sort();
            reasons.dedup();
            let trace = parsed.traces.first().filter(|_| parsed.traces.len() == 1);
            excluded.push(ExcludedTraceRow {
                source_path: entry.relative_path.clone(),
                content_sha256: entry.sha256.clone(),
                size_bytes: entry.size_bytes,
                exclusion_reasons: reasons,
                source_kind: "qlog",
                canonical_trace_path: None,
                relation_counts_by_packet_space: trace
                    .map(TraceAudit::relation_counts_by_packet_space)
                    .unwrap_or_default(),
                allowed_missing_mask: trace.map(TraceAudit::allowed_missing_mask),
                allowed_missing_counts: trace.map(TraceAudit::allowed_missing_counts),
                hard_issue_count: trace.map_or(0, |audit| audit.issues.len()),
                hard_issues: trace
                    .map(|audit| audit.issues.iter().cloned().collect())
                    .unwrap_or_default(),
            });
            continue;
        }

        let trace = &parsed.traces[0];
        let aliases = by_digest
            .get(&entry.sha256)
            .cloned()
            .unwrap_or_default()
            .into_iter()
            .filter(|path| path != &entry.relative_path)
            .collect::<Vec<_>>();
        for alias in &aliases {
            if !alias.ends_with(".qlog") {
                non_qlog_alias_count += 1;
                let alias_entry = entries
                    .iter()
                    .find(|candidate| candidate.relative_path == *alias)
                    .context("重复别名未出现在源清单")?;
                excluded.push(ExcludedTraceRow {
                    source_path: alias.clone(),
                    content_sha256: alias_entry.sha256.clone(),
                    size_bytes: alias_entry.size_bytes,
                    exclusion_reasons: vec!["content_alias_duplicate".to_owned()],
                    source_kind: "non_qlog_alias",
                    canonical_trace_path: Some(entry.relative_path.clone()),
                    relation_counts_by_packet_space: BTreeMap::new(),
                    allowed_missing_mask: None,
                    allowed_missing_counts: None,
                    hard_issue_count: 0,
                    hard_issues: Vec::new(),
                });
            }
        }
        let first = trace.first_time_ns.context("候选轨迹缺少首事件时间")?;
        let last = trace.last_time_ns.context("候选轨迹缺少末事件时间")?;
        let trace_id = format!("quic-mednetcom-{}", &entry.sha256[..20]);
        let mut deployment = BTreeMap::new();
        deployment.insert("relative_arrival_time", true);
        deployment.insert("packet_interarrival", true);
        deployment.insert("direction", true);
        deployment.insert("packet_length", true);
        deployment.insert("window_packet_count", true);
        deployment.insert("window_byte_count", true);
        deployment.insert("window_rate", true);
        deployment.insert("transport_family_applicability", true);
        rows.push(TraceManifestRow {
            trace_id,
            canonical_path: entry.relative_path.clone(),
            content_sha256: entry.sha256.clone(),
            size_bytes: entry.size_bytes,
            duplicate_alias_paths: aliases,
            qlog_version: parsed.qlog_version.clone().context("候选缺少 qlog_version")?,
            observer_vantage_point: trace.vantage_point.clone().context("候选缺少观察点")?,
            observer_role: "server_endpoint",
            group_id_sha256: trace.group_id.as_deref().map(hash_text),
            original_connection_id_sha256: trace.original_connection_id.as_deref().map(hash_text),
            first_event_time_ns: first,
            last_event_time_ns: last,
            duration_ns: last.checked_sub(first).context("候选轨迹持续时间下溢")?,
            time_is_monotonic: trace.time_is_monotonic,
            packet_number_spaces: trace.packet_number_spaces.iter().cloned().collect(),
            quic_versions: trace.quic_versions.iter().cloned().collect(),
            event_counts: EventCounts {
                total: trace.event_count,
                packet_sent: trace.packet_sent_count,
                packet_received: trace.packet_received_count,
                ack_frames: trace.ack_frame_count,
                ack_ranges: trace.ack_range_count,
                valid_ack_relations: trace.valid_ack_relation_count,
                unresolved_ack_relations: trace.unresolved_ack_relation_count,
                metrics_updated: trace.metrics_count,
                complete_rtt: trace.complete_rtt_count,
                bytes_in_flight: trace.bytes_in_flight_count,
                congestion_window: trace.congestion_window_count,
                packet_lost: trace.packet_lost_count,
                valid_packet_lost_relations: trace.valid_packet_lost_relation_count,
                unresolved_packet_lost_relations: trace.unresolved_packet_lost_relation_count,
                pto_events: trace.pto_event_count,
            },
            relation_counts_by_packet_space: trace.relation_counts_by_packet_space(),
            deployment_observable_mask: deployment,
            privileged_truth_mask: CoverageMask {
                sent_packet_number: true,
                ack_ranges: trace.valid_ack_relation_count > 0,
                latest_min_smoothed_rtt: true,
                endpoint_packet_loss: trace.valid_packet_lost_relation_count > 0,
                bytes_in_flight: true,
                congestion_window: true,
                pto_event: trace.pto_event_count > 0,
            },
            allowed_missing_mask: trace.allowed_missing_mask(),
            allowed_missing_counts: trace.allowed_missing_counts(),
            hard_issue_count: trace.issues.len(),
            hard_issues: trace.issues.iter().cloned().collect(),
            malicious_label: None,
        });
    }

    ensure!(empty_count == 8, "上游零字节 qlog 数量不是 8");
    ensure!(parsed_count == 81, "非空可解析 qlog 数量不是 81");
    ensure!(!rows.is_empty(), "没有轨迹通过核心物理字段门禁");
    ensure!(rows.len() >= cli.pilot_count, "通过门禁的轨迹不足以冻结先导子集");
    rows.sort_by(|left, right| {
        left.content_sha256
            .cmp(&right.content_sha256)
            .then_with(|| left.canonical_path.cmp(&right.canonical_path))
    });
    excluded.sort_by(|left, right| {
        left.source_path
            .cmp(&right.source_path)
            .then_with(|| left.exclusion_reasons.cmp(&right.exclusion_reasons))
    });

    fs::create_dir_all(&cli.output)
        .with_context(|| format!("无法创建输出目录：{}", cli.output.display()))?;
    let source_lock = SourceLock {
        dataset: "QUIC-MedNetCom",
        source_root: "raw/datasets/QUIC-MedNetCom",
        upstream_commit: commit,
        manifest_sha256,
        regular_file_count: entries.len(),
        regular_file_bytes: entries.iter().map(|entry| entry.size_bytes).sum(),
        git_tree_symlink_count: 1,
        git_tree_symlink_bytes: 27,
        qlog_file_count: entries
            .iter()
            .filter(|entry| entry.relative_path.ends_with(".qlog"))
            .count(),
        qlog_file_bytes: entries
            .iter()
            .filter(|entry| entry.relative_path.ends_with(".qlog"))
            .map(|entry| entry.size_bytes)
            .sum(),
        empty_qlog_count: empty_count,
        raw_data_redistribution: "许可尚不明确，仅限本课题内部实验，不公开镜像原始数据",
        malicious_labels: "数据不含恶意或良性标签，禁止推测或补造",
    };
    write_json(&cli.output.join("source-lock.json"), &source_lock)?;
    write_jsonl(&cli.output.join("trace-manifest.jsonl"), &rows)?;
    write_jsonl(&cli.output.join("excluded-traces.jsonl"), &excluded)?;

    let coverage = build_field_coverage(&rows, &excluded, non_qlog_alias_count);
    write_json(&cli.output.join("field-coverage.json"), &coverage)?;
    write_json(&cli.output.join("unit-contract.json"), &unit_contract())?;

    let pilots = rows
        .iter()
        .take(cli.pilot_count)
        .enumerate()
        .map(|(index, row)| PilotRow {
            pilot_rank: index + 1,
            selection_rule: "通过全部核心字段、单位、时序及同包号空间ACK/丢包关系门禁后，按规范内容 SHA-256 升序取前 16 条；与标签、模型结果、路径场景名无关",
            trace_id: row.trace_id.clone(),
            canonical_path: row.canonical_path.clone(),
            content_sha256: row.content_sha256.clone(),
            size_bytes: row.size_bytes,
            field_coverage: CoverageMask {
                sent_packet_number: true,
                ack_ranges: row.privileged_truth_mask.ack_ranges,
                latest_min_smoothed_rtt: true,
                endpoint_packet_loss: row.privileged_truth_mask.endpoint_packet_loss,
                bytes_in_flight: true,
                congestion_window: true,
                pto_event: row.privileged_truth_mask.pto_event,
            },
            relation_counts_by_packet_space: row.relation_counts_by_packet_space.clone(),
            allowed_missing_mask: row.allowed_missing_mask,
            allowed_missing_counts: row.allowed_missing_counts,
            hard_issue_count: row.hard_issue_count,
            event_time_unit: "nanosecond",
            rtt_unit: "nanosecond",
            byte_unit: "byte",
            use_boundary: "仅供开发集物理旁路先导，不是最终 QUIC 物理辅助池",
        })
        .collect::<Vec<_>>();
    write_jsonl(&cli.output.join("pilot-traces.jsonl"), &pilots)?;

    let excluded_qlogs = excluded
        .iter()
        .filter(|row| row.source_kind == "qlog")
        .count();
    let summary = AuditSummary {
        status: "GO",
        dataset: "QUIC-MedNetCom",
        qlog_files_seen: cli.expected_qlog_count,
        qlog_files_parsed: parsed_count,
        upstream_empty_placeholders: empty_count,
        candidate_traces: rows.len(),
        excluded_qlogs,
        duplicate_non_qlog_aliases: non_qlog_alias_count,
        pilot_traces: pilots.len(),
        candidate_total_events: rows.iter().map(|row| row.event_counts.total).sum(),
        hard_gate: "候选逐条具备发送包号、同包号空间且先于关系事件的有效ACK/丢包关系、应用数据有效ACK、最新/最小/平滑RTT、在途字节、拥塞窗口及零核心语义异常",
        pto_status: "源数据没有显式PTO事件；PTO掩码保持false，不做后验推测",
        label_status: "无攻击标签，仅进入训练期物理辅助池",
        release_scope: "仅表示QUIC物理辅助池候选GO，不表示检测数据或R2整体冻结",
    };
    write_json(&cli.output.join("audit-summary.json"), &summary)?;
    sync_directory(&cli.output)?;

    println!(
        "状态=GO 候选轨迹={} 排除qlog={} 先导轨迹={} 事件={} 耗时毫秒={} 峰值内存字节={}",
        rows.len(),
        excluded_qlogs,
        pilots.len(),
        summary.candidate_total_events,
        started.elapsed().as_millis(),
        peak_rss_bytes()?
    );
    Ok(())
}

fn verify_source_lock(cli: &Cli) -> Result<Vec<SourceEntry>> {
    let manifest = File::open(&cli.source_manifest)
        .with_context(|| format!("无法打开源哈希清单：{}", cli.source_manifest.display()))?;
    let mut entries = Vec::with_capacity(cli.expected_file_count);
    let mut total_bytes = 0u64;
    for (line_number, line) in BufReader::new(manifest).lines().enumerate() {
        let line = line.with_context(|| format!("读取源清单第 {} 行失败", line_number + 1))?;
        let (expected_sha, relative) = line
            .split_once("  ")
            .with_context(|| format!("源清单第 {} 行格式错误", line_number + 1))?;
        ensure!(expected_sha.len() == 64, "源清单 SHA-256 长度错误");
        let normalized = relative.strip_prefix("./").unwrap_or(relative).to_owned();
        ensure!(!normalized.starts_with('/') && !normalized.contains("../"), "源清单路径越界");
        let path = cli.source_root.join(&normalized);
        let metadata = fs::metadata(&path)
            .with_context(|| format!("无法读取源文件元数据：{}", path.display()))?;
        ensure!(metadata.is_file(), "源清单对象不是普通文件：{}", normalized);
        let (actual_sha, actual_bytes) = hash_file(&path)?;
        ensure!(actual_sha == expected_sha, "源文件 SHA-256 不匹配：{}", normalized);
        ensure!(actual_bytes == metadata.len(), "源文件哈希字节数与元数据不一致");
        total_bytes = total_bytes.checked_add(actual_bytes).context("源文件总字节数溢出")?;
        entries.push(SourceEntry {
            relative_path: normalized,
            sha256: actual_sha,
            size_bytes: actual_bytes,
        });
    }
    ensure!(entries.len() == cli.expected_file_count, "上游普通文件数不匹配");
    ensure!(total_bytes == cli.expected_file_bytes, "上游普通文件总字节数不匹配");
    let qlog_count = entries
        .iter()
        .filter(|entry| entry.relative_path.ends_with(".qlog"))
        .count();
    let qlog_bytes: u64 = entries
        .iter()
        .filter(|entry| entry.relative_path.ends_with(".qlog"))
        .map(|entry| entry.size_bytes)
        .sum();
    ensure!(qlog_count == cli.expected_qlog_count, "qlog 文件数不匹配");
    ensure!(qlog_bytes == cli.expected_qlog_bytes, "qlog 文件总字节数不匹配");
    Ok(entries)
}

fn scan_qlog(path: &Path) -> Result<ParsedQlog> {
    let file = File::open(path).with_context(|| format!("无法打开 qlog：{}", path.display()))?;
    let reader = BufReader::with_capacity(1024 * 1024, file);
    let mut deserializer = serde_json::Deserializer::from_reader(reader);
    let mut parsed = ParsedQlog::default();
    QlogSeed(&mut parsed)
        .deserialize(&mut deserializer)
        .with_context(|| format!("流式解析 qlog 失败：{}", path.display()))?;
    deserializer.end().context("qlog 顶层对象后存在多余 JSON")?;
    Ok(parsed)
}

fn normalize_packet_number_space(packet_type: &str) -> Option<&'static str> {
    match packet_type {
        "initial" => Some("initial"),
        "handshake" => Some("handshake"),
        "1RTT" => Some("application_data"),
        _ => None,
    }
}

fn decimal_milliseconds_to_nanoseconds(raw: &str) -> Result<u64> {
    ensure!(!raw.starts_with('-'), "时间不能为负数");
    ensure!(!raw.contains(['e', 'E']), "不接受科学计数法时间");
    let (whole, fractional) = raw.split_once('.').unwrap_or((raw, ""));
    ensure!(!whole.is_empty() && whole.bytes().all(|value| value.is_ascii_digit()), "整数部分非法");
    ensure!(fractional.bytes().all(|value| value.is_ascii_digit()), "小数部分非法");
    ensure!(fractional.len() <= 6, "毫秒精度超过可无损转换的纳秒精度");
    let whole_ms = whole.parse::<u64>().context("毫秒整数部分溢出")?;
    let mut fractional_ns = fractional.to_owned();
    fractional_ns.extend(std::iter::repeat_n('0', 6usize.saturating_sub(fractional_ns.len())));
    let fractional_ns = if fractional_ns.is_empty() {
        0
    } else {
        fractional_ns.parse::<u64>().context("毫秒小数部分溢出")?
    };
    whole_ms
        .checked_mul(1_000_000)
        .and_then(|value| value.checked_add(fractional_ns))
        .context("毫秒转纳秒溢出")
}

fn duration_field_to_nanoseconds(
    data: &Value,
    field: &str,
    issues: &mut BTreeSet<String>,
) -> Option<u64> {
    let Some(value) = data.get(field) else {
        issues.insert(format!("恢复指标缺少 {field}"));
        return None;
    };
    let Some(number) = value.as_number() else {
        issues.insert(format!("恢复指标 {field} 不是数值"));
        return None;
    };
    match decimal_milliseconds_to_nanoseconds(&number.to_string()) {
        Ok(value) if value > 0 => Some(value),
        Ok(_) => {
            issues.insert(format!("恢复指标 {field} 不是正数"));
            None
        }
        Err(error) => {
            issues.insert(format!("恢复指标 {field} 单位无法解释：{error}"));
            None
        }
    }
}

fn value_to_u64(value: &Value) -> Option<u64> {
    match value {
        Value::String(raw) => raw.parse().ok(),
        Value::Number(number) => number.as_u64(),
        _ => None,
    }
}

fn hash_text(value: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(value.as_bytes());
    hex::encode(hasher.finalize())
}

fn hash_file(path: &Path) -> Result<(String, u64)> {
    let file = File::open(path).with_context(|| format!("无法打开待哈希文件：{}", path.display()))?;
    let mut reader = BufReader::with_capacity(1024 * 1024, file);
    let mut hasher = Sha256::new();
    let mut buffer = vec![0u8; 1024 * 1024];
    let mut size = 0u64;
    loop {
        let count = reader.read(&mut buffer).context("读取待哈希文件失败")?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
        size = size
            .checked_add(u64::try_from(count).context("哈希块长度转换失败")?)
            .context("文件大小累计溢出")?;
    }
    Ok((hex::encode(hasher.finalize()), size))
}

fn git_stdout(root: &Path, arguments: &[&str]) -> Result<String> {
    let output = Command::new("git")
        .arg("-C")
        .arg(root)
        .args(arguments)
        .output()
        .context("执行 Git 输入锁命令失败")?;
    ensure!(output.status.success(), "Git 输入锁命令失败");
    String::from_utf8(output.stdout)
        .context("Git 输出不是 UTF-8")
        .map(|value| value.trim().to_owned())
}

fn run_git_fsck(root: &Path) -> Result<()> {
    let status = Command::new("git")
        .arg("-C")
        .arg(root)
        .args(["fsck", "--full"])
        .status()
        .context("执行 git fsck 失败")?;
    ensure!(status.success(), "git fsck 未通过");
    Ok(())
}

fn write_json<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .with_context(|| format!("无法创建 JSON 制品：{}", path.display()))?;
    let mut writer = BufWriter::with_capacity(1024 * 1024, file);
    serde_json::to_writer_pretty(&mut writer, value).context("写入 JSON 制品失败")?;
    writer.write_all(b"\n").context("写入 JSON 换行失败")?;
    writer.flush().context("刷新 JSON 制品失败")?;
    writer.get_ref().sync_all().context("同步 JSON 制品失败")?;
    Ok(())
}

fn write_jsonl<T: Serialize>(path: &Path, rows: &[T]) -> Result<()> {
    let file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .with_context(|| format!("无法创建 JSONL 制品：{}", path.display()))?;
    let mut writer = BufWriter::with_capacity(1024 * 1024, file);
    for row in rows {
        serde_json::to_writer(&mut writer, row).context("写入 JSONL 行失败")?;
        writer.write_all(b"\n").context("写入 JSONL 换行失败")?;
    }
    writer.flush().context("刷新 JSONL 制品失败")?;
    writer.get_ref().sync_all().context("同步 JSONL 制品失败")?;
    Ok(())
}

fn sync_directory(path: &Path) -> Result<()> {
    File::open(path)
        .with_context(|| format!("无法打开输出目录进行同步：{}", path.display()))?
        .sync_all()
        .context("同步输出目录失败")
}

fn build_field_coverage(
    rows: &[TraceManifestRow],
    excluded: &[ExcludedTraceRow],
    non_qlog_alias_count: usize,
) -> FieldCoverage {
    FieldCoverage {
        candidate_trace_count: rows.len(),
        excluded_qlog_count: excluded.iter().filter(|row| row.source_kind == "qlog").count(),
        excluded_non_qlog_alias_count: non_qlog_alias_count,
        candidate_event_count: rows.iter().map(|row| row.event_counts.total).sum(),
        candidate_packet_sent_count: rows.iter().map(|row| row.event_counts.packet_sent).sum(),
        candidate_packet_received_count: rows.iter().map(|row| row.event_counts.packet_received).sum(),
        candidate_ack_frame_count: rows.iter().map(|row| row.event_counts.ack_frames).sum(),
        candidate_ack_range_count: rows.iter().map(|row| row.event_counts.ack_ranges).sum(),
        candidate_valid_ack_relation_count: rows
            .iter()
            .map(|row| row.event_counts.valid_ack_relations)
            .sum(),
        candidate_unresolved_ack_relation_count: rows
            .iter()
            .map(|row| row.event_counts.unresolved_ack_relations)
            .sum(),
        candidate_complete_rtt_count: rows.iter().map(|row| row.event_counts.complete_rtt).sum(),
        candidate_packet_lost_count: rows.iter().map(|row| row.event_counts.packet_lost).sum(),
        candidate_valid_packet_lost_relation_count: rows
            .iter()
            .map(|row| row.event_counts.valid_packet_lost_relations)
            .sum(),
        candidate_unresolved_packet_lost_relation_count: rows
            .iter()
            .map(|row| row.event_counts.unresolved_packet_lost_relations)
            .sum(),
        candidate_metrics_count: rows.iter().map(|row| row.event_counts.metrics_updated).sum(),
        candidate_bytes_in_flight_count: rows.iter().map(|row| row.event_counts.bytes_in_flight).sum(),
        candidate_congestion_window_count: rows.iter().map(|row| row.event_counts.congestion_window).sum(),
        candidate_pto_event_count: rows.iter().map(|row| row.event_counts.pto_events).sum(),
        traces_with_pto: rows
            .iter()
            .filter(|row| row.privileged_truth_mask.pto_event)
            .count(),
        candidate_hard_issue_count: rows.iter().map(|row| row.hard_issue_count).sum(),
        pto_interpretation: "源日志不存在显式PTO事件，保持缺失掩码，不从packet_lost或时间间隔反推",
    }
}

fn unit_contract() -> UnitContract {
    let mut spaces = BTreeMap::new();
    spaces.insert("initial", "Initial 包号空间");
    spaces.insert("handshake", "Handshake 包号空间");
    spaces.insert("1RTT", "应用数据包号空间");
    UnitContract {
        qlog_schema: "draft-02-wip；事件数组字段顺序固定为 time/category/event/data",
        event_time: UnitField {
            source_unit: "绝对Unix毫秒，最多6位毫秒小数",
            normalized_unit: "整数纳秒",
            conversion: "十进制定点值乘1,000,000；禁止经过二进制浮点",
            evidence: "事件时间约1.58e12且单调，对应2020年采集时期；全部原始值可无损转整数纳秒",
        },
        rtt_metrics: UnitField {
            source_unit: "毫秒",
            normalized_unit: "整数纳秒",
            conversion: "latest_rtt/min_rtt/smoothed_rtt十进制定点值乘1,000,000",
            evidence: "quic-go draft-02 recovery:metrics_updated；值域与事件往返间隔一致",
        },
        ack_delay: UnitField {
            source_unit: "旧qlog中的整数编码值，缺少可独立验证的ACK延迟指数",
            normalized_unit: "不转换，仅登记存在性",
            conversion: "禁止推测或作为核心RTT真值",
            evidence: "部分ACK帧缺少ack_delay；核心RTT采用端点恢复指标",
        },
        packet_and_state_bytes: UnitField {
            source_unit: "字节",
            normalized_unit: "非负整数字节",
            conversion: "恒等转换",
            evidence: "packet_size/bytes_in_flight/congestion_window由端点qlog直接记录",
        },
        direction: DirectionContract {
            source: "transport:packet_sent 与 transport:packet_received",
            normalized: "相对观察端点的 send/receive",
            observer: "全部候选要求 vantage_point.type=server",
        },
        packet_number_spaces: spaces,
        deployment_observable_fields: vec![
            "relative_arrival_time",
            "packet_interarrival",
            "direction",
            "packet_length",
            "window_packet_count",
            "window_byte_count",
            "window_rate",
            "transport_family_applicability",
        ],
        training_only_privileged_truth: vec![
            "packet_number_space",
            "packet_number",
            "ack_ranges",
            "latest_rtt",
            "min_rtt",
            "smoothed_rtt",
            "endpoint_packet_lost",
            "bytes_in_flight",
            "congestion_window",
            "pto_event_if_explicitly_available",
        ],
        forbidden_deployment_fields: vec![
            "endpoint_qlog",
            "tls_keys",
            "attack_label",
            "server_name",
            "source_dataset_id",
            "capture_scenario_id",
            "group_id",
            "original_connection_id",
        ],
        missing_value_policy: "显式布尔掩码；不插值、不零填充、不后验猜测",
    }
}

fn peak_rss_bytes() -> Result<u64> {
    let mut usage = std::mem::MaybeUninit::<libc::rusage>::uninit();
    // SAFETY: 系统调用成功时会完整初始化有效指针所指向的 rusage。
    let status = unsafe { libc::getrusage(libc::RUSAGE_SELF, usage.as_mut_ptr()) };
    ensure!(status == 0, "getrusage 无法取得峰值内存");
    // SAFETY: 上一条系统调用已经成功，结构体已完整初始化。
    let usage = unsafe { usage.assume_init() };
    let raw = u64::try_from(usage.ru_maxrss).context("峰值内存为负数")?;
    #[cfg(target_os = "linux")]
    {
        raw.checked_mul(1024).context("Linux 峰值内存换算溢出")
    }
    #[cfg(target_os = "macos")]
    {
        Ok(raw)
    }
    #[cfg(not(any(target_os = "linux", target_os = "macos")))]
    {
        bail!("当前平台未定义ru_maxrss字节换算")
    }
}
