use std::collections::{BTreeMap, BTreeSet};
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::net::IpAddr;
use std::path::Path;
use std::time::Instant;

use ahash::{AHashMap, AHashSet};
use anyhow::{Context, Result, bail, ensure};
use blake2::Blake2bVar;
use blake2::digest::{Update as BlakeUpdate, VariableOutput};
use csv::StringRecord;
use serde_json::Value;
use sha2::{Digest, Sha256};
use zip::ZipArchive;

use crate::archive::{
    DigestReader, OFFICIAL_FLOW_ARCHIVE_MD5, OFFICIAL_FLOW_ARCHIVE_SHA256,
    OFFICIAL_FLOW_ARCHIVE_SIZE, OFFICIAL_PACKET_ARCHIVE_MD5, OFFICIAL_PACKET_ARCHIVE_SIZE,
    ensure_regular_file, hash_file, sha256_bytes, validate_member_path, validate_revision,
    validate_sha256, verify_digest,
};
use crate::cli::Cli;
use crate::model::{
    ArtifactManifest, ComparisonRow, FLOW_ARCHIVE_LOGICAL_PATH, InputAudit, LayerMatchSummary,
    MEMBER_MAP_SCHEMA_VERSION, MemberAudit, MemberPair, PACKET_ARCHIVE_LOGICAL_PATH,
    PacketStatistics, RunManifest, SCHEMA_VERSION, ScopeMatchSummary, Summary, ToolchainAudit,
};
use crate::output::{
    OutputTransaction, artifact_entry, command_version, peak_rss_bytes, write_comparison_parquet,
    write_json,
};
use crate::packet::{
    ConnectionKey, Endpoint, FragmentCache, IpAddress, ParsedPacket, parse_packet,
};
use crate::pcapng::read_pcapng;

const CANDIDATE_NAMESPACE: &str = "dataset-candidate-genis-v0";
const CANDIDATE_LOGICAL_PATH: &str =
    "runs/data-frozen/dataset-v1/manifests/budgets/train_candidate_approx10000.jsonl";
const MEMBER_MAP_LOGICAL_PATH: &str = "r2-input:genis-member-map-v1.jsonl";
const MATCH_STATUS: &str = "matched_exact_packet_counts";
const ABSOLUTE_TIME_ROUNDING_RADIUS_NS: i64 = 500_000_000;

#[derive(Clone, Copy, Debug)]
struct RoundedSecond {
    center_ns: i64,
    lower_inclusive_ns: i64,
    upper_exclusive_ns: i64,
}

impl RoundedSecond {
    fn contains(self, timestamp_ns: i64) -> bool {
        timestamp_ns >= self.lower_inclusive_ns && timestamp_ns < self.upper_exclusive_ns
    }
}

#[derive(Clone, Debug)]
struct ResolvedMemberPair {
    flow_member: String,
    packet_member: String,
    binding_sha256: String,
}

#[derive(Debug)]
struct FlowBinding {
    sample_id: String,
    is_candidate: bool,
    flow_id: String,
    group_id: String,
    member_index: usize,
    csv_row_number: u64,
    source_binding_sha256: String,
    source: Endpoint,
    destination: Endpoint,
    key: ConnectionKey,
    start_time: RoundedSecond,
    end_time: RoundedSecond,
    duration_ns: i64,
    published_duration_seconds: f64,
    csv_tot_bytes: u64,
    csv_total_packets: u64,
    csv_source_packets: u64,
    csv_destination_packets: u64,
    recomputed_packets: u64,
    recomputed_source_packets: u64,
    recomputed_destination_packets: u64,
    l2_wire_bytes: u64,
    l3_network_bytes: u64,
    first_packet_timestamp_ns: Option<i64>,
    last_packet_timestamp_ns: Option<i64>,
    identity_status: IdentityStatus,
    duration_evidence: Option<DurationEvidence>,
}

#[derive(Clone, Copy, Debug)]
struct IdentityPacket {
    timestamp_ns: i64,
    parsed: ParsedPacket,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct FeasibleSegment {
    packet_start: usize,
    packet_end_exclusive: usize,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum IdentityStatus {
    Unresolved,
    Unique,
    Missing,
    Ambiguous,
}

impl IdentityStatus {
    fn as_str(self) -> &'static str {
        match self {
            Self::Unresolved => "unresolved",
            Self::Unique => "unique",
            Self::Missing => "missing",
            Self::Ambiguous => "ambiguous",
        }
    }
}

#[derive(Clone, Copy, Debug)]
struct DurationEvidence {
    inverse_count: u64,
    interval_lower_ns: Option<i64>,
    interval_upper_ns: Option<i64>,
    actual_duration_ns: i64,
    interval_match: bool,
}

#[derive(Debug, Default)]
struct ConnectionGroup {
    flow_indexes: Vec<usize>,
}

impl ConnectionGroup {
    fn sort_by_source_order(&mut self, flows: &[FlowBinding]) {
        self.flow_indexes
            .sort_by_key(|flow_index| flows[*flow_index].csv_row_number);
    }

    fn feasible_segments(
        &self,
        flow_index: usize,
        flows: &[FlowBinding],
        packets: &[IdentityPacket],
        low_to_high_prefix: &[u64],
        start_positions: &AHashMap<i64, Vec<usize>>,
    ) -> Result<Vec<FeasibleSegment>> {
        let flow = flows.get(flow_index).context("连接组引用不存在的流记录")?;
        let segment_length = usize::try_from(flow.csv_total_packets)
            .context("TotPkts 无法转换为内存索引")?;
        if segment_length == 0 || segment_length > packets.len() {
            return Ok(Vec::new());
        }

        ensure!(
            low_to_high_prefix.len() == packets.len() + 1,
            "方向前缀和长度与连接包序列不一致"
        );
        let last_start = packets.len() - segment_length;
        let Some(candidate_starts) = start_positions.get(&flow.start_time.center_ns) else {
            return Ok(Vec::new());
        };
        let mut feasible = Vec::new();
        for packet_start in candidate_starts.iter().copied() {
            if packet_start > last_start {
                continue;
            }
            let packet_end_exclusive = packet_start
                .checked_add(segment_length)
                .context("包分段终点溢出")?;
            let segment = &packets[packet_start..packet_end_exclusive];
            let first = segment.first().context("可行分段意外为空")?;
            let last = segment.last().context("可行分段意外为空")?;
            if !flow.start_time.contains(first.timestamp_ns)
                || !flow.end_time.contains(last.timestamp_ns)
            {
                continue;
            }

            let low_to_high = low_to_high_prefix[packet_end_exclusive]
                .checked_sub(low_to_high_prefix[packet_start])
                .context("方向前缀和逆序")?;
            let total_packets = u64::try_from(segment_length)
                .context("包分段长度无法转换为 u64")?;
            let high_to_low = total_packets
                .checked_sub(low_to_high)
                .context("方向包数超过总包数")?;
            let (source_packets, destination_packets) = if flow.source == flow.key.low {
                (low_to_high, high_to_low)
            } else {
                (high_to_low, low_to_high)
            };
            if source_packets == flow.csv_source_packets
                && destination_packets == flow.csv_destination_packets
            {
                feasible.push(FeasibleSegment {
                    packet_start,
                    packet_end_exclusive,
                });
            }
        }
        Ok(feasible)
    }
}

#[derive(Default)]
struct GroupAccumulator {
    flow_count: u64,
    csv_packet_count: u64,
    recomputed_packet_count: u64,
    csv_tot_bytes: u64,
    l2_wire_bytes: u64,
    l3_network_bytes: u64,
    source_bindings: BTreeSet<String>,
}

struct HeaderIndex {
    flow_id: usize,
    start_time: usize,
    last_time: usize,
    duration: usize,
    source_address: usize,
    destination_address: usize,
    protocol: usize,
    source_port: usize,
    destination_port: usize,
    total_bytes: usize,
    total_packets: usize,
    source_packets: usize,
    destination_packets: usize,
}

impl HeaderIndex {
    fn new(headers: &StringRecord) -> Result<Self> {
        let mut seen = AHashSet::with_capacity(headers.len());
        for (index, name) in headers.iter().enumerate() {
            let name = if index == 0 {
                name.strip_prefix('\u{feff}').unwrap_or(name)
            } else {
                name
            };
            ensure!(seen.insert(name), "GeNIS 流 CSV 表头含重复字段：{name}");
        }
        let required = |name: &str| {
            headers
                .iter()
                .enumerate()
                .position(|(index, candidate)| {
                    let candidate = if index == 0 {
                        candidate.strip_prefix('\u{feff}').unwrap_or(candidate)
                    } else {
                        candidate
                    };
                    candidate == name
                })
                .with_context(|| format!("GeNIS 流 CSV 缺少字段：{name}"))
        };
        Ok(Self {
            flow_id: required("FlowID")?,
            start_time: required("StartTime")?,
            last_time: required("LastTime")?,
            duration: required("Dur")?,
            source_address: required("SrcAddr")?,
            destination_address: required("DstAddr")?,
            protocol: required("Proto")?,
            source_port: required("Sport")?,
            destination_port: required("Dport")?,
            total_bytes: required("TotBytes")?,
            total_packets: required("TotPkts")?,
            source_packets: required("SrcPkts")?,
            destination_packets: required("DstPkts")?,
        })
    }

    fn value<'a>(&self, row: &'a StringRecord, index: usize, field_name: &str) -> Result<&'a str> {
        row.get(index)
            .with_context(|| format!("GeNIS 流 CSV 行缺少字段：{field_name}"))
    }
}

fn checked_add(target: &mut u64, value: u64, field_name: &str) -> Result<()> {
    *target = target
        .checked_add(value)
        .with_context(|| format!("{field_name} 发生整数溢出"))?;
    Ok(())
}

fn usize_to_u64(value: usize, field_name: &str) -> Result<u64> {
    u64::try_from(value).with_context(|| format!("{field_name} 无法转换为 u64"))
}

fn parse_decimal_integer(value: &str, field_name: &str) -> Result<u64> {
    let value = value.trim();
    ensure!(!value.is_empty(), "{field_name} 为空");
    let value = value.strip_prefix('+').unwrap_or(value);
    ensure!(!value.starts_with('-'), "{field_name} 不能为负数");
    let mut pieces = value.split('.');
    let integer = pieces.next().context("整数解析失败")?;
    let fraction = pieces.next();
    ensure!(pieces.next().is_none(), "{field_name} 不是十进制整数");
    ensure!(!integer.is_empty() && integer.bytes().all(|byte| byte.is_ascii_digit()), "{field_name} 不是十进制整数");
    if let Some(fraction) = fraction {
        ensure!(fraction.bytes().all(|byte| byte == b'0'), "{field_name} 含非零小数部分");
    }
    integer
        .parse::<u64>()
        .with_context(|| format!("{field_name} 超出 u64 范围"))
}

fn parse_timestamp_ns(value: &str, field_name: &str) -> Result<i64> {
    let value = value.trim();
    ensure!(!value.is_empty(), "{field_name} 为空");
    let value = value.strip_prefix('+').unwrap_or(value);
    ensure!(!value.starts_with('-'), "{field_name} 不能为负数");
    let mut exponent_parts = value.split(['e', 'E']);
    let mantissa = exponent_parts.next().context("十进制尾数缺失")?;
    let exponent_text = exponent_parts.next();
    ensure!(exponent_parts.next().is_none(), "{field_name} 含多个十进制指数");
    let exponent = if let Some(exponent_text) = exponent_text {
        let digits = exponent_text
            .strip_prefix('+')
            .or_else(|| exponent_text.strip_prefix('-'))
            .unwrap_or(exponent_text);
        ensure!(!digits.is_empty() && digits.bytes().all(|byte| byte.is_ascii_digit()), "{field_name} 十进制指数无效");
        exponent_text
            .parse::<i32>()
            .with_context(|| format!("{field_name} 十进制指数超出 i32"))?
    } else {
        0
    };
    let mut mantissa_parts = mantissa.split('.');
    let integer = mantissa_parts.next().context("十进制整数部分缺失")?;
    let fraction = mantissa_parts.next().unwrap_or("");
    ensure!(mantissa_parts.next().is_none(), "{field_name} 含多个小数点");
    ensure!(!integer.is_empty() && integer.bytes().all(|byte| byte.is_ascii_digit()), "{field_name} 整数部分无效");
    ensure!(fraction.bytes().all(|byte| byte.is_ascii_digit()), "{field_name} 小数部分无效");
    let digits = format!("{integer}{fraction}");
    let significand = digits
        .parse::<u128>()
        .with_context(|| format!("{field_name} 十进制尾数超出 u128"))?;
    let fraction_digits = i32::try_from(fraction.len()).context("小数位数超出 i32")?;
    let nanosecond_power = exponent
        .checked_sub(fraction_digits)
        .and_then(|power| power.checked_add(9))
        .context("十进制纳秒指数溢出")?;
    let total = if nanosecond_power >= 0 {
        let factor = 10_u128
            .checked_pow(u32::try_from(nanosecond_power).context("正十进制指数转换失败")?)
            .context("十进制纳秒倍率溢出")?;
        significand
            .checked_mul(factor)
            .context("十进制纳秒值溢出")?
    } else {
        let divisor = 10_u128
            .checked_pow(nanosecond_power.unsigned_abs())
            .context("十进制纳秒除数溢出")?;
        ensure!(significand % divisor == 0, "{field_name} 无法精确换算为整数纳秒");
        significand / divisor
    };
    i64::try_from(total).with_context(|| format!("{field_name} 超出 i64 纳秒范围"))
}

fn parse_rounded_second(value: &str, field_name: &str) -> Result<RoundedSecond> {
    let seconds = parse_decimal_integer(value, field_name)?;
    let center = i128::from(seconds)
        .checked_mul(1_000_000_000)
        .context("整秒时间戳换算溢出")?;
    let lower = center
        .checked_sub(i128::from(ABSOLUTE_TIME_ROUNDING_RADIUS_NS))
        .context("整秒时间戳下界溢出")?;
    let upper = center
        .checked_add(i128::from(ABSOLUTE_TIME_ROUNDING_RADIUS_NS))
        .context("整秒时间戳上界溢出")?;
    Ok(RoundedSecond {
        center_ns: i64::try_from(center).with_context(|| format!("{field_name} 中心超出 i64"))?,
        lower_inclusive_ns: i64::try_from(lower)
            .with_context(|| format!("{field_name} 下界超出 i64"))?,
        upper_exclusive_ns: i64::try_from(upper)
            .with_context(|| format!("{field_name} 上界超出 i64"))?,
    })
}

fn parse_protocol(value: &str) -> Result<u8> {
    let normalised = value.trim().to_ascii_lowercase();
    let protocol = match normalised.as_str() {
        "tcp" | "6" => 6,
        "udp" | "17" => 17,
        "icmp" | "1" => 1,
        "icmpv6" | "ipv6-icmp" | "58" => 58,
        "sctp" | "132" => 132,
        "dccp" | "33" => 33,
        "esp" | "50" => 50,
        _ => bail!("GeNIS Proto 不在已声明的 IP 协议集合中：{normalised}"),
    };
    Ok(protocol)
}

fn parse_ip_address(value: &str, field_name: &str) -> Result<IpAddress> {
    match value
        .trim()
        .parse::<IpAddr>()
        .with_context(|| format!("{field_name} 不是合法 IP 地址"))?
    {
        IpAddr::V4(address) => Ok(IpAddress::V4(address.octets())),
        IpAddr::V6(address) => Ok(IpAddress::V6(address.octets())),
    }
}

fn parse_port(value: &str, protocol: u8, field_name: &str) -> Result<u16> {
    if matches!(protocol, 6 | 17 | 33 | 132) {
        let port = parse_decimal_integer(value, field_name)?;
        u16::try_from(port).with_context(|| format!("{field_name} 超出 u16 范围"))
    } else {
        Ok(0)
    }
}

fn candidate_sample_id(member_basename: &str, row_number: u64) -> String {
    let old_sample_id = format!("genis:{member_basename}:{row_number}");
    let mut hasher = Sha256::new();
    Digest::update(&mut hasher, CANDIDATE_NAMESPACE.as_bytes());
    Digest::update(&mut hasher, b"\0");
    Digest::update(&mut hasher, old_sample_id.as_bytes());
    format!("genis:{}", hex::encode(hasher.finalize()))
}

fn group_id(member_basename: &str, flow_id: &str) -> Result<String> {
    let flow_id = flow_id.trim();
    ensure!(!flow_id.is_empty() && !flow_id.contains('\0'), "GeNIS FlowID 为空或含 NUL");
    let mut hasher = Blake2bVar::new(16).context("无法创建 BLAKE2b-128")?;
    BlakeUpdate::update(&mut hasher, member_basename.as_bytes());
    BlakeUpdate::update(&mut hasher, b"\0");
    BlakeUpdate::update(&mut hasher, flow_id.as_bytes());
    let mut output = [0_u8; 16];
    hasher
        .finalize_variable(&mut output)
        .context("无法完成 BLAKE2b-128")?;
    Ok(hex::encode(output))
}

fn binding_hash(parts: &[&str]) -> String {
    let mut hasher = Sha256::new();
    for part in parts {
        Digest::update(&mut hasher, part.as_bytes());
        Digest::update(&mut hasher, b"\0");
    }
    hex::encode(hasher.finalize())
}

fn load_candidates(path: &Path, expected_count: usize) -> Result<AHashSet<String>> {
    ensure_regular_file(path, "候选清单")?;
    let source = File::open(path).context("无法打开冻结候选清单")?;
    let reader = BufReader::with_capacity(1024 * 1024, source);
    let mut candidates = AHashSet::with_capacity(expected_count);
    for (line_index, line) in reader.lines().enumerate() {
        let line = line.with_context(|| format!("读取候选清单第 {} 行失败", line_index + 1))?;
        ensure!(!line.trim().is_empty(), "候选清单第 {} 行为空", line_index + 1);
        let value: Value = serde_json::from_str(&line)
            .with_context(|| format!("候选清单第 {} 行不是合法 JSON", line_index + 1))?;
        let sample_id = value
            .get("sample_id")
            .and_then(Value::as_str)
            .with_context(|| format!("候选清单第 {} 行缺少字符串 sample_id", line_index + 1))?;
        if sample_id.starts_with("genis:") {
            ensure!(sample_id.len() == 70, "GeNIS 候选 sample_id 长度无效");
            ensure!(candidates.insert(sample_id.to_owned()), "GeNIS 候选 sample_id 重复");
        }
    }
    ensure!(
        candidates.len() == expected_count,
        "GeNIS 冻结候选数不一致：期望 {expected_count}，实际 {}",
        candidates.len()
    );
    Ok(candidates)
}

fn load_member_pairs(path: &Path, expected_count: usize) -> Result<Vec<ResolvedMemberPair>> {
    ensure_regular_file(path, "成员配对清单")?;
    let source = File::open(path).context("无法打开成员配对清单")?;
    let reader = BufReader::with_capacity(1024 * 1024, source);
    let mut pairs = Vec::with_capacity(expected_count);
    let mut flow_members = AHashSet::with_capacity(expected_count);
    let mut packet_members = AHashSet::with_capacity(expected_count);
    for (line_index, line) in reader.lines().enumerate() {
        let line = line.with_context(|| format!("读取成员配对清单第 {} 行失败", line_index + 1))?;
        ensure!(!line.trim().is_empty(), "成员配对清单第 {} 行为空", line_index + 1);
        let pair: MemberPair = serde_json::from_str(&line)
            .with_context(|| format!("成员配对清单第 {} 行结构错误", line_index + 1))?;
        ensure!(pair.schema_version == MEMBER_MAP_SCHEMA_VERSION, "成员配对清单模式版本错误");
        validate_member_path(&pair.flow_member, "流归档")?;
        validate_member_path(&pair.packet_member, "包归档")?;
        ensure!(
            pair.packet_member.to_ascii_lowercase().ends_with(".pcapng"),
            "包成员必须是 PCAPNG；经典 PCAP 不在本工具合同内"
        );
        ensure!(flow_members.insert(pair.flow_member.clone()), "流归档成员重复配对");
        ensure!(packet_members.insert(pair.packet_member.clone()), "包归档成员重复配对");
        let binding_sha256 = binding_hash(&[
            MEMBER_MAP_SCHEMA_VERSION,
            &pair.flow_member,
            &pair.packet_member,
        ]);
        pairs.push(ResolvedMemberPair {
            flow_member: pair.flow_member,
            packet_member: pair.packet_member,
            binding_sha256,
        });
    }
    ensure!(
        pairs.len() == expected_count,
        "成员配对数不一致：期望 {expected_count}，实际 {}",
        pairs.len()
    );
    pairs.sort_by(|left, right| left.flow_member.cmp(&right.flow_member));
    Ok(pairs)
}

fn zip_member_names(archive: &mut ZipArchive<File>, role: &str) -> Result<BTreeSet<String>> {
    let mut names = BTreeSet::new();
    for index in 0..archive.len() {
        let entry = archive
            .by_index(index)
            .with_context(|| format!("读取{role} ZIP 第 {index} 个成员失败"))?;
        let name = entry.name().to_owned();
        validate_member_path(name.trim_end_matches('/'), role)?;
        ensure!(names.insert(name.clone()), "{role} ZIP 含重复成员路径");
        if let Some(mode) = entry.unix_mode() {
            ensure!(mode & 0o170000 != 0o120000, "{role} ZIP 含符号链接成员");
        }
    }
    Ok(names)
}

fn validate_zip_members(
    flow_archive: &mut ZipArchive<File>,
    packet_archive: &mut ZipArchive<File>,
    pairs: &[ResolvedMemberPair],
) -> Result<()> {
    let flow_names = zip_member_names(flow_archive, "GeNIS 流归档")?;
    let packet_names = zip_member_names(packet_archive, "GeNIS 包归档")?;
    let mapped_flows: BTreeSet<&str> = pairs.iter().map(|pair| pair.flow_member.as_str()).collect();
    let mapped_packets: BTreeSet<&str> = pairs.iter().map(|pair| pair.packet_member.as_str()).collect();
    let ten_second_flows: BTreeSet<&str> = flow_names
        .iter()
        .filter(|name| name.contains("/flows-10-sec/") && name.to_ascii_lowercase().ends_with(".csv"))
        .map(String::as_str)
        .collect();
    let packet_captures: BTreeSet<&str> = packet_names
        .iter()
        .filter(|name| {
            let lower = name.to_ascii_lowercase();
            lower.ends_with(".pcapng") || lower.ends_with(".pcap")
        })
        .map(String::as_str)
        .collect();
    ensure!(ten_second_flows == mapped_flows, "成员配对清单未精确覆盖全部 10 秒流 CSV");
    ensure!(packet_captures == mapped_packets, "成员配对清单未精确覆盖全部原始包捕获成员");
    Ok(())
}

fn open_zip(path: &Path, role: &str) -> Result<ZipArchive<File>> {
    ensure_regular_file(path, role)?;
    let source = File::open(path).with_context(|| format!("无法打开{role}"))?;
    ZipArchive::new(source).with_context(|| format!("{role}不是完整 ZIP 归档"))
}

fn parse_flow_binding(
    headers: &HeaderIndex,
    row: &StringRecord,
    sample_id: String,
    is_candidate: bool,
    flow_id: String,
    group_id: String,
    member_index: usize,
    csv_row_number: u64,
) -> Result<FlowBinding> {
    let protocol = parse_protocol(headers.value(row, headers.protocol, "Proto")?)?;
    let source_address = parse_ip_address(
        headers.value(row, headers.source_address, "SrcAddr")?,
        "SrcAddr",
    )?;
    let destination_address = parse_ip_address(
        headers.value(row, headers.destination_address, "DstAddr")?,
        "DstAddr",
    )?;
    ensure!(
        matches!((source_address, destination_address), (IpAddress::V4(_), IpAddress::V4(_)) | (IpAddress::V6(_), IpAddress::V6(_))),
        "GeNIS 流的源和目的 IP 版本不一致"
    );
    let source_port = parse_port(
        headers.value(row, headers.source_port, "Sport")?,
        protocol,
        "Sport",
    )?;
    let destination_port = parse_port(
        headers.value(row, headers.destination_port, "Dport")?,
        protocol,
        "Dport",
    )?;
    let source = Endpoint {
        address: source_address,
        port: source_port,
    };
    let destination = Endpoint {
        address: destination_address,
        port: destination_port,
    };
    let start_time = parse_rounded_second(
        headers.value(row, headers.start_time, "StartTime")?,
        "StartTime",
    )?;
    let end_time = parse_rounded_second(
        headers.value(row, headers.last_time, "LastTime")?,
        "LastTime",
    )?;
    ensure!(end_time.center_ns >= start_time.center_ns, "GeNIS LastTime 早于 StartTime");
    let duration_ns = parse_timestamp_ns(
        headers.value(row, headers.duration, "Dur")?,
        "Dur",
    )?;
    let published_duration_seconds = headers
        .value(row, headers.duration, "Dur")?
        .trim()
        .parse::<f64>()
        .context("Dur 不是合法浮点数")?;
    ensure!(
        published_duration_seconds.is_finite() && published_duration_seconds >= 0.0,
        "Dur 必须是非负有限浮点数"
    );
    let csv_tot_bytes = parse_decimal_integer(
        headers.value(row, headers.total_bytes, "TotBytes")?,
        "TotBytes",
    )?;
    let csv_total_packets = parse_decimal_integer(
        headers.value(row, headers.total_packets, "TotPkts")?,
        "TotPkts",
    )?;
    let csv_source_packets = parse_decimal_integer(
        headers.value(row, headers.source_packets, "SrcPkts")?,
        "SrcPkts",
    )?;
    let csv_destination_packets = parse_decimal_integer(
        headers.value(row, headers.destination_packets, "DstPkts")?,
        "DstPkts",
    )?;
    ensure!(
        csv_source_packets.checked_add(csv_destination_packets) == Some(csv_total_packets),
        "GeNIS TotPkts 不等于 SrcPkts + DstPkts"
    );
    Ok(FlowBinding {
        sample_id,
        is_candidate,
        flow_id,
        group_id,
        member_index,
        csv_row_number,
        source_binding_sha256: String::new(),
        source,
        destination,
        key: ConnectionKey::new(protocol, source, destination),
        start_time,
        end_time,
        duration_ns,
        published_duration_seconds,
        csv_tot_bytes,
        csv_total_packets,
        csv_source_packets,
        csv_destination_packets,
        recomputed_packets: 0,
        recomputed_source_packets: 0,
        recomputed_destination_packets: 0,
        l2_wire_bytes: 0,
        l3_network_bytes: 0,
        first_packet_timestamp_ns: None,
        last_packet_timestamp_ns: None,
        identity_status: IdentityStatus::Unresolved,
        duration_evidence: None,
    })
}

fn load_flows(
    archive: &mut ZipArchive<File>,
    pairs: &[ResolvedMemberPair],
    candidates: &AHashSet<String>,
    flow_archive_sha256: &str,
    maximum_flows: usize,
) -> Result<(Vec<FlowBinding>, Vec<MemberAudit>)> {
    let mut flows = Vec::with_capacity(candidates.len());
    let mut matched_candidates = AHashSet::with_capacity(candidates.len());
    let mut audits = Vec::with_capacity(pairs.len());

    for (member_index, pair) in pairs.iter().enumerate() {
        let member = archive
            .by_name(&pair.flow_member)
            .with_context(|| format!("流归档缺少配对成员：{}", pair.flow_member))?;
        ensure!(!member.is_dir(), "配对的流归档成员是目录");
        let mut digest_reader = DigestReader::new(member);
        let mut csv_reader = csv::ReaderBuilder::new()
            .flexible(false)
            .from_reader(&mut digest_reader);
        let headers = HeaderIndex::new(csv_reader.headers().context("读取 GeNIS 流 CSV 表头失败")?)?;
        let member_basename = pair
            .flow_member
            .rsplit('/')
            .next()
            .context("流成员缺少 basename")?
            .trim();
        ensure!(!member_basename.is_empty(), "流成员 basename 为空");
        let mut flow_rows_seen = 0_u64;
        let mut selected_indexes = Vec::new();
        let mut member_indexes = Vec::new();
        for (row_index, record) in csv_reader.records().enumerate() {
            let row = record.with_context(|| format!("读取 GeNIS 流 CSV 第 {} 条数据行失败", row_index + 1))?;
            let row_number = u64::try_from(row_index)
                .context("CSV 行号无法转换为 u64")?
                .checked_add(1)
                .context("CSV 一基行号溢出")?;
            checked_add(&mut flow_rows_seen, 1, "流 CSV 行数")?;
            let sample_id = candidate_sample_id(member_basename, row_number);
            let is_candidate = candidates.contains(&sample_id);
            if is_candidate {
                ensure!(matched_candidates.insert(sample_id.clone()), "冻结候选命中多条 GeNIS 流记录");
                ensure!(matched_candidates.len() <= maximum_flows, "冻结流绑定超过有界内存上限");
            }
            let protocol_text = headers
                .value(&row, headers.protocol, "Proto")?
                .trim()
                .to_ascii_lowercase();
            if protocol_text == "arp" {
                ensure!(!is_candidate, "GeNIS 冻结候选包含非 IP 的 ARP 流记录");
                continue;
            }
            let flow_id = headers.value(&row, headers.flow_id, "FlowID")?.trim().to_owned();
            let group_id = group_id(member_basename, &flow_id)?;
            let binding = parse_flow_binding(
                &headers,
                &row,
                sample_id,
                is_candidate,
                flow_id,
                group_id,
                member_index,
                row_number,
            )?;
            if is_candidate {
                selected_indexes.push(flows.len());
            }
            member_indexes.push(flows.len());
            flows.push(binding);
        }
        drop(csv_reader);
        let (member_size, member_sha256) = digest_reader.finish()?;
        for index in member_indexes.iter().copied() {
            let flow = &mut flows[index];
            let row_number = flow.csv_row_number.to_string();
            flow.source_binding_sha256 = binding_hash(&[
                SCHEMA_VERSION,
                flow_archive_sha256,
                &member_sha256,
                &pair.binding_sha256,
                &row_number,
                &flow.sample_id,
            ]);
        }
        audits.push(MemberAudit {
            binding_sha256: pair.binding_sha256.clone(),
            flow_member_size_bytes: member_size,
            flow_member_sha256: member_sha256,
            packet_member_size_bytes: 0,
            packet_member_sha256: String::new(),
            flow_rows_seen,
            selected_flow_rows: usize_to_u64(selected_indexes.len(), "成员候选流数")?,
            pcapng_interfaces: 0,
            pcapng_linktypes: Vec::new(),
            packets_seen: 0,
            ip_packets_seen: 0,
            selected_packets: 0,
        });
    }
    ensure!(matched_candidates.len() == candidates.len(), "存在未消费的 GeNIS 冻结候选");
    ensure!(flows.iter().filter(|flow| flow.is_candidate).count() == candidates.len(), "冻结候选与流绑定数不一致");
    Ok((flows, audits))
}

type MemberFlowIndex = AHashMap<ConnectionKey, ConnectionGroup>;

fn build_flow_indexes(
    flows: &[FlowBinding],
    member_count: usize,
) -> Result<Vec<MemberFlowIndex>> {
    let mut indexes: Vec<MemberFlowIndex> = (0..member_count).map(|_| AHashMap::new()).collect();
    for (index, flow) in flows.iter().enumerate() {
        indexes
            .get_mut(flow.member_index)
            .context("流绑定引用不存在的成员")?
            .entry(flow.key)
            .or_default()
            .flow_indexes
            .push(index);
    }
    for index in &mut indexes {
        for group in index.values_mut() {
            group.sort_by_source_order(flows);
        }
        index.retain(|_, group| {
            group
                .flow_indexes
                .iter()
                .any(|flow_index| flows[*flow_index].is_candidate)
        });
    }
    Ok(indexes)
}

fn capped_add(left: u8, right: u8) -> u8 {
    left.saturating_add(right).min(2)
}

fn direction_prefix(
    key: ConnectionKey,
    packets: &[IdentityPacket],
) -> Result<Vec<u64>> {
    let mut prefix = Vec::with_capacity(packets.len() + 1);
    prefix.push(0_u64);
    for packet in packets {
        ensure!(packet.parsed.key == key, "连接包序列含错误五元组");
        let low_to_high = if packet.parsed.source == key.low
            && packet.parsed.destination == key.high
        {
            1_u64
        } else if packet.parsed.source == key.high
            && packet.parsed.destination == key.low
        {
            0_u64
        } else {
            bail!("连接包序列端点与规范化五元组不一致")
        };
        let next = prefix
            .last()
            .copied()
            .context("方向前缀和为空")?
            .checked_add(low_to_high)
            .context("方向前缀和溢出")?;
        prefix.push(next);
    }
    Ok(prefix)
}

fn rounded_start_positions(packets: &[IdentityPacket]) -> Result<AHashMap<i64, Vec<usize>>> {
    let mut positions: AHashMap<i64, Vec<usize>> = AHashMap::new();
    for (packet_index, packet) in packets.iter().enumerate() {
        let shifted = packet
            .timestamp_ns
            .checked_add(ABSOLUTE_TIME_ROUNDING_RADIUS_NS)
            .context("包时间戳舍入平移溢出")?;
        let center_ns = shifted
            .div_euclid(1_000_000_000)
            .checked_mul(1_000_000_000)
            .context("包时间戳舍入中心溢出")?;
        positions.entry(center_ns).or_default().push(packet_index);
    }
    Ok(positions)
}

fn forward_path_counts(segments: &[Vec<FeasibleSegment>]) -> Vec<Vec<u8>> {
    let mut counts = Vec::with_capacity(segments.len());
    for (record_index, current) in segments.iter().enumerate() {
        if record_index == 0 {
            counts.push(vec![1; current.len()]);
            continue;
        }
        let previous_segments = &segments[record_index - 1];
        let previous_counts = &counts[record_index - 1];
        let mut prefix_counts = Vec::with_capacity(previous_counts.len() + 1);
        prefix_counts.push(0_u8);
        for count in previous_counts {
            let next = capped_add(*prefix_counts.last().unwrap_or(&0), *count);
            prefix_counts.push(next);
        }
        let current_counts = current
            .iter()
            .map(|segment| {
                let compatible = previous_segments.partition_point(|previous| {
                    previous.packet_end_exclusive <= segment.packet_start
                });
                prefix_counts[compatible]
            })
            .collect();
        counts.push(current_counts);
    }
    counts
}

fn backward_path_counts(segments: &[Vec<FeasibleSegment>]) -> Vec<Vec<u8>> {
    let mut counts: Vec<Vec<u8>> = segments
        .iter()
        .map(|record_segments| vec![0; record_segments.len()])
        .collect();
    let Some(last) = counts.last_mut() else {
        return counts;
    };
    last.fill(1);
    for record_index in (0..segments.len().saturating_sub(1)).rev() {
        let next_segments = &segments[record_index + 1];
        let next_counts = &counts[record_index + 1];
        let mut suffix_counts = vec![0_u8; next_counts.len() + 1];
        for index in (0..next_counts.len()).rev() {
            suffix_counts[index] = capped_add(suffix_counts[index + 1], next_counts[index]);
        }
        counts[record_index] = segments[record_index]
            .iter()
            .map(|segment| {
                let compatible = next_segments.partition_point(|next| {
                    next.packet_start < segment.packet_end_exclusive
                });
                suffix_counts[compatible]
            })
            .collect();
    }
    counts
}

fn formatted_duration_seconds(duration_us: u64) -> Result<f64> {
    ensure!(duration_us <= u64::from(u32::MAX), "Dur 逆像搜索范围超过 f32 安全输入上限");
    let seconds = (duration_us as f32) / 1_000_000.0_f32;
    format!("{seconds:.6}")
        .parse::<f64>()
        .context("无法解析 f32 六位 Dur 表示")
}

fn duration_search_upper_us(flow: &FlowBinding) -> Result<u64> {
    let latest_end_ns = flow
        .end_time
        .upper_exclusive_ns
        .checked_sub(1)
        .context("LastTime 粗窗上界下溢")?;
    let earliest_start_us = flow.start_time.lower_inclusive_ns.div_euclid(1_000);
    let latest_end_us = latest_end_ns.div_euclid(1_000);
    if latest_end_us < earliest_start_us {
        return Ok(0);
    }
    u64::try_from(latest_end_us - earliest_start_us).context("Dur 逆像上界无法转换为 u64")
}

fn duration_lower_bound(
    target: f64,
    maximum_us: u64,
    strictly_greater: bool,
) -> Result<u64> {
    let mut lower = 0_u64;
    let mut upper = maximum_us.checked_add(1).context("Dur 逆像二分上界溢出")?;
    while lower < upper {
        let middle = lower + (upper - lower) / 2;
        let value = formatted_duration_seconds(middle)?;
        let before_boundary = if strictly_greater {
            value <= target
        } else {
            value < target
        };
        if before_boundary {
            lower = middle.checked_add(1).context("Dur 逆像二分下界溢出")?;
        } else {
            upper = middle;
        }
    }
    Ok(lower)
}

fn duration_evidence(flow: &FlowBinding) -> Result<DurationEvidence> {
    let first_timestamp = flow
        .first_packet_timestamp_ns
        .context("唯一身份缺少首包时间戳")?;
    let last_timestamp = flow
        .last_packet_timestamp_ns
        .context("唯一身份缺少末包时间戳")?;
    let actual_duration_ns = last_timestamp
        .checked_sub(first_timestamp)
        .context("逐流首末包时间跨度溢出")?;
    ensure!(actual_duration_ns >= 0, "逐流首末包时间跨度为负数");

    let maximum_us = duration_search_upper_us(flow)?;
    let inverse_lower = duration_lower_bound(
        flow.published_duration_seconds,
        maximum_us,
        false,
    )?;
    let inverse_upper = duration_lower_bound(
        flow.published_duration_seconds,
        maximum_us,
        true,
    )?;
    let inverse_count = inverse_upper.saturating_sub(inverse_lower);
    if inverse_count == 0
        || inverse_lower > maximum_us
        || formatted_duration_seconds(inverse_lower)? != flow.published_duration_seconds
    {
        return Ok(DurationEvidence {
            inverse_count: 0,
            interval_lower_ns: None,
            interval_upper_ns: None,
            actual_duration_ns,
            interval_match: false,
        });
    }

    let last_inverse_us = inverse_upper.checked_sub(1).context("Dur 逆像上界为空")?;
    let interval_lower = i128::from(inverse_lower)
        .checked_mul(1_000)
        .and_then(|value| value.checked_sub(999))
        .context("Dur 逆像区间下界溢出")?
        .max(0);
    let interval_upper = i128::from(last_inverse_us)
        .checked_mul(1_000)
        .and_then(|value| value.checked_add(999))
        .context("Dur 逆像区间上界溢出")?;
    let interval_lower_ns = i64::try_from(interval_lower).context("Dur 逆像区间下界超出 i64")?;
    let interval_upper_ns = i64::try_from(interval_upper).context("Dur 逆像区间上界超出 i64")?;
    Ok(DurationEvidence {
        inverse_count,
        interval_lower_ns: Some(interval_lower_ns),
        interval_upper_ns: Some(interval_upper_ns),
        actual_duration_ns,
        interval_match: actual_duration_ns >= interval_lower_ns
            && actual_duration_ns <= interval_upper_ns,
    })
}

fn update_flow(flow: &mut FlowBinding, packet: ParsedPacket, timestamp_ns: i64) -> Result<()> {
    checked_add(&mut flow.recomputed_packets, 1, "逐流包数")?;
    checked_add(&mut flow.l2_wire_bytes, packet.l2_wire_bytes, "逐流 L2 字节")?;
    checked_add(&mut flow.l3_network_bytes, packet.l3_network_bytes, "逐流 L3 字节")?;
    flow.first_packet_timestamp_ns = Some(
        flow.first_packet_timestamp_ns
            .map_or(timestamp_ns, |current| current.min(timestamp_ns)),
    );
    flow.last_packet_timestamp_ns = Some(
        flow.last_packet_timestamp_ns
            .map_or(timestamp_ns, |current| current.max(timestamp_ns)),
    );
    if packet.source == flow.source && packet.destination == flow.destination {
        checked_add(&mut flow.recomputed_source_packets, 1, "逐流源方向包数")?;
    } else if packet.source == flow.destination && packet.destination == flow.source {
        checked_add(&mut flow.recomputed_destination_packets, 1, "逐流目的方向包数")?;
    } else {
        bail!("规范连接键命中后方向端点仍不一致")
    }
    Ok(())
}

fn mark_group_identity(
    group: &ConnectionGroup,
    flows: &mut [FlowBinding],
    status: IdentityStatus,
) -> Result<()> {
    for flow_index in &group.flow_indexes {
        let flow = flows
            .get_mut(*flow_index)
            .context("连接组引用不存在的流记录")?;
        if flow.is_candidate {
            flow.identity_status = status;
        }
    }
    Ok(())
}

fn solve_connection_group(
    key: ConnectionKey,
    group: &ConnectionGroup,
    packets: &[IdentityPacket],
    flows: &mut [FlowBinding],
) -> Result<u64> {
    let prefix = direction_prefix(key, packets)?;
    let start_positions = rounded_start_positions(packets)?;
    let segments: Vec<Vec<FeasibleSegment>> = group
        .flow_indexes
        .iter()
        .map(|flow_index| {
            group.feasible_segments(
                *flow_index,
                flows,
                packets,
                &prefix,
                &start_positions,
            )
        })
        .collect::<Result<_>>()?;
    let forward = forward_path_counts(&segments);
    let total_paths = forward
        .last()
        .map(|counts| counts.iter().copied().fold(0_u8, capped_add))
        .unwrap_or(0);
    if total_paths == 0 {
        mark_group_identity(group, flows, IdentityStatus::Missing)?;
        return Ok(0);
    }
    if total_paths > 1 {
        mark_group_identity(group, flows, IdentityStatus::Ambiguous)?;
        return Ok(0);
    }

    let backward = backward_path_counts(&segments);
    let mut assignments = Vec::with_capacity(group.flow_indexes.len());
    for record_index in 0..group.flow_indexes.len() {
        let complete_segments: Vec<FeasibleSegment> = segments[record_index]
            .iter()
            .copied()
            .enumerate()
            .filter(|(segment_index, _)| {
                forward[record_index][*segment_index] > 0
                    && backward[record_index][*segment_index] > 0
            })
            .map(|(_, segment)| segment)
            .collect();
        ensure!(
            complete_segments.len() == 1,
            "唯一全局路径未能还原为逐记录唯一分段"
        );
        assignments.push((group.flow_indexes[record_index], complete_segments[0]));
    }

    let mut selected_candidate_packets = 0_u64;
    for (flow_index, segment) in assignments {
        let flow = flows
            .get_mut(flow_index)
            .context("唯一分段引用不存在的流记录")?;
        if !flow.is_candidate {
            continue;
        }
        for packet in &packets[segment.packet_start..segment.packet_end_exclusive] {
            update_flow(flow, packet.parsed, packet.timestamp_ns)?;
        }
        flow.identity_status = IdentityStatus::Unique;
        flow.duration_evidence = Some(duration_evidence(flow)?);
        checked_add(
            &mut selected_candidate_packets,
            flow.csv_total_packets,
            "唯一候选包数",
        )?;
    }
    Ok(selected_candidate_packets)
}

fn process_packets(
    archive: &mut ZipArchive<File>,
    pairs: &[ResolvedMemberPair],
    indexes: &[MemberFlowIndex],
    flows: &mut [FlowBinding],
    audits: &mut [MemberAudit],
    cli: &Cli,
) -> Result<PacketStatistics> {
    let mut statistics = PacketStatistics {
        packets_seen: 0,
        ip_packets_seen: 0,
        non_ip_packets_seen: 0,
        selected_packets: 0,
        ipv4_fragments_seen: 0,
        ipv6_fragments_seen: 0,
        unresolved_fragments: 0,
        structural_error_count: 0,
    };
    for (member_index, pair) in pairs.iter().enumerate() {
        let member = archive
            .by_name(&pair.packet_member)
            .with_context(|| format!("包归档缺少配对成员：{}", pair.packet_member))?;
        ensure!(!member.is_dir(), "配对的包归档成员是目录");
        let mut digest_reader = DigestReader::new(member);
        let mut fragments = FragmentCache::new(cli.max_fragment_contexts)?;
        let mut member_packets = 0_u64;
        let mut member_ip_packets = 0_u64;
        let member_index_groups = indexes
            .get(member_index)
            .context("包成员缺少流索引")?;
        let mut connection_packets: AHashMap<ConnectionKey, Vec<IdentityPacket>> =
            AHashMap::with_capacity(member_index_groups.len());
        for key in member_index_groups.keys() {
            connection_packets.insert(*key, Vec::new());
        }
        let pcap_stats = read_pcapng(
            &mut digest_reader,
            cli.max_pcapng_block_bytes,
            |packet| {
                checked_add(&mut statistics.packets_seen, 1, "总包数")?;
                checked_add(&mut member_packets, 1, "成员包数")?;
                let parsed = parse_packet(packet, &mut fragments, &mut statistics)?;
                let Some(parsed) = parsed else {
                    checked_add(&mut statistics.non_ip_packets_seen, 1, "非 IP 包数")?;
                    return Ok(());
                };
                checked_add(&mut statistics.ip_packets_seen, 1, "IP 包数")?;
                checked_add(&mut member_ip_packets, 1, "成员 IP 包数")?;
                let Some(selected) = connection_packets.get_mut(&parsed.key) else {
                    return Ok(());
                };
                selected.push(IdentityPacket {
                    timestamp_ns: packet.timestamp_ns,
                    parsed,
                });
                Ok(())
            },
        )?;
        ensure!(pcap_stats.packet_count == member_packets, "PCAPNG 解析器与回调包数不一致");
        ensure!(fragments.remaining() == 0, "包成员结束时仍有未闭合 IP 分片上下文");
        let mut member_selected_packets = 0_u64;
        for (key, group) in member_index_groups {
            let packets = connection_packets
                .remove(key)
                .context("连接组缺少已初始化包序列")?;
            let selected = solve_connection_group(*key, group, &packets, flows)?;
            checked_add(&mut member_selected_packets, selected, "成员候选包数")?;
        }
        checked_add(
            &mut statistics.selected_packets,
            member_selected_packets,
            "候选包数",
        )?;
        let (member_size, member_sha256) = digest_reader.finish()?;
        let audit = audits.get_mut(member_index).context("包成员缺少审计记录")?;
        audit.packet_member_size_bytes = member_size;
        audit.packet_member_sha256 = member_sha256;
        audit.pcapng_interfaces = pcap_stats.interface_count;
        audit.pcapng_linktypes = pcap_stats.linktypes.into_iter().collect();
        audit.packets_seen = member_packets;
        audit.ip_packets_seen = member_ip_packets;
        audit.selected_packets = member_selected_packets;
    }
    Ok(statistics)
}

fn validate_resolved_bindings(flows: &[FlowBinding]) -> Result<()> {
    for flow in flows.iter().filter(|flow| flow.is_candidate) {
        if flow.identity_status != IdentityStatus::Unique {
            continue;
        }
        ensure!(flow.recomputed_packets == flow.csv_total_packets, "唯一候选的 TotPkts 不一致");
        ensure!(flow.recomputed_source_packets == flow.csv_source_packets, "唯一候选的 SrcPkts 不一致");
        ensure!(flow.recomputed_destination_packets == flow.csv_destination_packets, "唯一候选的 DstPkts 不一致");
        ensure!(flow.duration_evidence.is_some(), "唯一候选缺少 Dur 逆像证据");
    }
    Ok(())
}

fn signed_difference(value: u64, baseline: u64, field_name: &str) -> Result<i64> {
    let difference = i128::from(value) - i128::from(baseline);
    i64::try_from(difference).with_context(|| format!("{field_name} 差值超出 i64"))
}

fn row_evidence_sha256(row: &ComparisonRow) -> Result<String> {
    let payload = serde_json::to_vec(row).context("序列化逐行证据失败")?;
    Ok(sha256_bytes(&payload))
}

fn comparison_row_for_flow(flow: &FlowBinding) -> Result<ComparisonRow> {
    let duration = flow.duration_evidence;
    let match_status = match (flow.identity_status, duration) {
        (IdentityStatus::Unique, Some(evidence)) if evidence.interval_match => MATCH_STATUS,
        (IdentityStatus::Unique, Some(_)) => "duration_interval_mismatch",
        (IdentityStatus::Unique, None) => "duration_evidence_missing",
        (status, _) => status.as_str(),
    };
    let mut row = ComparisonRow {
        scope: "flow",
        sample_id: Some(flow.sample_id.clone()),
        group_id: flow.group_id.clone(),
        flow_count: 1,
        csv_packet_count: flow.csv_total_packets,
        recomputed_packet_count: flow.recomputed_packets,
        csv_tot_bytes: flow.csv_tot_bytes,
        l2_wire_bytes: flow.l2_wire_bytes,
        l3_network_bytes: flow.l3_network_bytes,
        l2_minus_csv: signed_difference(flow.l2_wire_bytes, flow.csv_tot_bytes, "逐流 L2")?,
        l3_minus_csv: signed_difference(flow.l3_network_bytes, flow.csv_tot_bytes, "逐流 L3")?,
        l2_exact_match: flow.l2_wire_bytes == flow.csv_tot_bytes,
        l3_exact_match: flow.l3_network_bytes == flow.csv_tot_bytes,
        match_status,
        identity_status: flow.identity_status.as_str(),
        dur_inverse_count: duration.map_or(0, |evidence| evidence.inverse_count),
        dur_interval_lower_ns: duration.and_then(|evidence| evidence.interval_lower_ns),
        dur_interval_upper_ns: duration.and_then(|evidence| evidence.interval_upper_ns),
        actual_duration_ns: duration.map(|evidence| evidence.actual_duration_ns),
        dur_interval_match: duration.is_some_and(|evidence| evidence.interval_match),
        source_binding_sha256: flow.source_binding_sha256.clone(),
        evidence_sha256: String::new(),
    };
    row.evidence_sha256 = row_evidence_sha256(&row)?;
    Ok(row)
}

fn add_group_flow(group: &mut GroupAccumulator, flow: &FlowBinding) -> Result<()> {
    checked_add(&mut group.flow_count, 1, "组流数")?;
    checked_add(&mut group.csv_packet_count, flow.csv_total_packets, "组 CSV 包数")?;
    checked_add(
        &mut group.recomputed_packet_count,
        flow.recomputed_packets,
        "组复算包数",
    )?;
    checked_add(&mut group.csv_tot_bytes, flow.csv_tot_bytes, "组 CSV 字节")?;
    checked_add(&mut group.l2_wire_bytes, flow.l2_wire_bytes, "组 L2 字节")?;
    checked_add(&mut group.l3_network_bytes, flow.l3_network_bytes, "组 L3 字节")?;
    group.source_bindings.insert(flow.source_binding_sha256.clone());
    Ok(())
}

fn comparison_row_for_group(group_id: &str, group: &GroupAccumulator) -> Result<ComparisonRow> {
    let source_payload = serde_json::to_vec(&group.source_bindings).context("序列化组来源绑定失败")?;
    let mut row = ComparisonRow {
        scope: "group",
        sample_id: None,
        group_id: group_id.to_owned(),
        flow_count: group.flow_count,
        csv_packet_count: group.csv_packet_count,
        recomputed_packet_count: group.recomputed_packet_count,
        csv_tot_bytes: group.csv_tot_bytes,
        l2_wire_bytes: group.l2_wire_bytes,
        l3_network_bytes: group.l3_network_bytes,
        l2_minus_csv: signed_difference(group.l2_wire_bytes, group.csv_tot_bytes, "逐组 L2")?,
        l3_minus_csv: signed_difference(group.l3_network_bytes, group.csv_tot_bytes, "逐组 L3")?,
        l2_exact_match: group.l2_wire_bytes == group.csv_tot_bytes,
        l3_exact_match: group.l3_network_bytes == group.csv_tot_bytes,
        match_status: MATCH_STATUS,
        identity_status: "group_aggregate",
        dur_inverse_count: 0,
        dur_interval_lower_ns: None,
        dur_interval_upper_ns: None,
        actual_duration_ns: None,
        dur_interval_match: false,
        source_binding_sha256: sha256_bytes(&source_payload),
        evidence_sha256: String::new(),
    };
    row.evidence_sha256 = row_evidence_sha256(&row)?;
    Ok(row)
}

fn build_comparison_rows(flows: &[FlowBinding]) -> Result<Vec<ComparisonRow>> {
    let mut ordered_flows: Vec<&FlowBinding> =
        flows.iter().filter(|flow| flow.is_candidate).collect();
    ordered_flows.sort_by(|left, right| left.sample_id.cmp(&right.sample_id));
    let mut groups: BTreeMap<String, GroupAccumulator> = BTreeMap::new();
    let mut rows = Vec::with_capacity(ordered_flows.len() + 64);
    for flow in ordered_flows {
        add_group_flow(groups.entry(flow.group_id.clone()).or_default(), flow)?;
        rows.push(comparison_row_for_flow(flow)?);
    }
    for (group_id, group) in groups {
        rows.push(comparison_row_for_group(&group_id, &group)?);
    }
    Ok(rows)
}

fn scope_summary<'a>(
    rows: impl Iterator<Item = &'a ComparisonRow>,
    layer: &str,
) -> Result<ScopeMatchSummary> {
    let mut compared_rows = 0_u64;
    let mut exact_integer_matches = 0_u64;
    for row in rows {
        checked_add(&mut compared_rows, 1, "比较行数")?;
        let matched = match layer {
            "l2" => row.l2_exact_match,
            "l3" => row.l3_exact_match,
            _ => bail!("未知字节层级摘要"),
        };
        if matched {
            checked_add(&mut exact_integer_matches, 1, "精确匹配行数")?;
        }
    }
    Ok(ScopeMatchSummary {
        compared_rows,
        exact_integer_matches,
        mismatches: compared_rows - exact_integer_matches,
    })
}

fn layer_summary(rows: &[ComparisonRow], layer: &str) -> Result<LayerMatchSummary> {
    let flow = scope_summary(rows.iter().filter(|row| row.scope == "flow"), layer)?;
    let group = scope_summary(rows.iter().filter(|row| row.scope == "group"), layer)?;
    let all_exact = flow.compared_rows > 0
        && group.compared_rows > 0
        && flow.mismatches == 0
        && group.mismatches == 0;
    Ok(LayerMatchSummary {
        flow,
        group,
        all_exact,
    })
}

fn build_summary(
    rows: &[ComparisonRow],
    flows: &[FlowBinding],
    all_rows_loaded: u64,
    expected_candidates: usize,
    statistics: PacketStatistics,
) -> Result<Summary> {
    let l2 = layer_summary(rows, "l2")?;
    let l3 = layer_summary(rows, "l3")?;
    let compared_candidates = rows.iter().filter(|row| row.scope == "flow").count();
    let compared_groups = rows.iter().filter(|row| row.scope == "group").count();
    ensure!(compared_candidates == expected_candidates, "比较流行数不等于冻结候选数");
    let candidates: Vec<&FlowBinding> = flows.iter().filter(|flow| flow.is_candidate).collect();
    ensure!(candidates.len() == expected_candidates, "候选绑定数不等于冻结候选数");
    let candidate_identity_unique = candidates
        .iter()
        .filter(|flow| flow.identity_status == IdentityStatus::Unique)
        .count();
    let candidate_identity_missing = candidates
        .iter()
        .filter(|flow| flow.identity_status == IdentityStatus::Missing)
        .count();
    let candidate_identity_ambiguous = candidates
        .iter()
        .filter(|flow| flow.identity_status == IdentityStatus::Ambiguous)
        .count();
    let dur_inverse_empty = candidates
        .iter()
        .filter(|flow| {
            flow
                .duration_evidence
                .is_some_and(|evidence| evidence.inverse_count == 0)
        })
        .count();
    let dur_interval_match = candidates
        .iter()
        .filter(|flow| {
            flow
                .duration_evidence
                .is_some_and(|evidence| evidence.interval_match)
        })
        .count();
    let dur_interval_mismatch = candidates
        .iter()
        .filter(|flow| {
            flow.duration_evidence.is_some_and(|evidence| {
                evidence.inverse_count > 0 && !evidence.interval_match
            })
        })
        .count();
    let mut flow_id_counts: AHashMap<(usize, &str), u64> = AHashMap::new();
    for flow in flows {
        let count = flow_id_counts
            .entry((flow.member_index, flow.flow_id.as_str()))
            .or_default();
        checked_add(count, 1, "FlowID 重复计数")?;
    }
    let repeated_flow_id_candidate_count = candidates
        .iter()
        .filter(|flow| {
            flow_id_counts
                .get(&(flow.member_index, flow.flow_id.as_str()))
                .is_some_and(|count| *count > 1)
        })
        .count();
    let identity_duration_pass = candidate_identity_unique == expected_candidates
        && candidate_identity_missing == 0
        && candidate_identity_ambiguous == 0
        && dur_inverse_empty == 0
        && dur_interval_match == expected_candidates
        && dur_interval_mismatch == 0;
    let decision = if identity_duration_pass && l3.all_exact {
        "GO"
    } else {
        "NO-GO"
    };
    let mapped_semantics = if l3.all_exact {
        "network_layer_bytes"
    } else if l2.all_exact {
        "pcap_original_length_l2"
    } else {
        "neither_exactly"
    };
    let comparison_payload = serde_json::to_vec(rows).context("序列化比较载荷失败")?;
    Ok(Summary {
        schema_version: SCHEMA_VERSION,
        status: "completed",
        review_status: "review_pending",
        decision,
        decision_rule: "仅当全部候选具有全记录全局唯一包身份、Dur 逆像区间匹配，且流与派生组在零整数容差下精确匹配网络层字节时判定 GO",
        mapped_semantics,
        expected_candidate_count: usize_to_u64(expected_candidates, "预期候选数")?,
        compared_candidate_count: usize_to_u64(compared_candidates, "比较候选数")?,
        compared_group_count: usize_to_u64(compared_groups, "比较组数")?,
        all_rows_loaded,
        candidate_identity_unique: usize_to_u64(candidate_identity_unique, "唯一候选数")?,
        candidate_identity_missing: usize_to_u64(candidate_identity_missing, "缺失候选数")?,
        candidate_identity_ambiguous: usize_to_u64(candidate_identity_ambiguous, "多义候选数")?,
        dur_inverse_empty: usize_to_u64(dur_inverse_empty, "Dur 逆像为空数")?,
        dur_interval_match: usize_to_u64(dur_interval_match, "Dur 区间匹配数")?,
        dur_interval_mismatch: usize_to_u64(dur_interval_mismatch, "Dur 区间失配数")?,
        repeated_flow_id_candidate_count: usize_to_u64(
            repeated_flow_id_candidate_count,
            "重复 FlowID 候选数",
        )?,
        l2_wire_match: l2,
        l3_network_match: l3,
        packet_count_matches: usize_to_u64(
            candidates
                .iter()
                .filter(|flow| {
                    flow.identity_status == IdentityStatus::Unique
                        && flow.recomputed_packets == flow.csv_total_packets
                        && flow.recomputed_source_packets == flow.csv_source_packets
                        && flow.recomputed_destination_packets == flow.csv_destination_packets
                })
                .count(),
            "包数匹配数",
        )?,
        packet_statistics: statistics,
        comparison_payload_sha256: sha256_bytes(&comparison_payload),
    })
}

fn input_audit(logical_path: &str, digest: &crate::model::ArtifactDigest) -> InputAudit {
    InputAudit {
        logical_path: logical_path.to_owned(),
        size_bytes: digest.size_bytes,
        md5: digest.md5.clone(),
        sha256: digest.sha256.clone(),
    }
}

fn validate_cli(cli: &Cli) -> Result<()> {
    validate_sha256(&cli.packet_archive_sha256, "packet_archive_sha256")?;
    validate_sha256(&cli.candidate_manifest_sha256, "candidate_manifest_sha256")?;
    validate_sha256(&cli.member_map_sha256, "member_map_sha256")?;
    validate_sha256(
        &cli.execution_code_lock_sha256,
        "execution_code_lock_sha256",
    )?;
    validate_revision(&cli.tool_revision)?;
    ensure!(cli.expected_candidate_count > 0, "预期候选数必须大于 0");
    ensure!(cli.expected_member_count > 0, "预期成员数必须大于 0");
    ensure!(cli.max_flow_bindings >= cli.expected_candidate_count, "流绑定内存上限小于预期候选数");
    ensure!(cli.max_pcapng_block_bytes >= 28, "PCAPNG 块上限不能小于 28 字节");
    ensure!(cli.max_fragment_contexts > 0, "IP 分片上下文上限必须大于 0");
    ensure!(cli.time_tolerance_ns == 0, "任务 02R 正式合同固定要求 time_tolerance_ns=0");
    ensure!(!cli.output.as_os_str().is_empty(), "正式输出路径不能为空");
    Ok(())
}

pub fn run_verification(cli: Cli) -> Result<()> {
    let started = Instant::now();
    validate_cli(&cli)?;
    let executable_path = std::env::current_exe().context("无法解析当前可执行文件路径")?;
    let executable_digest = hash_file(&executable_path)?;

    let packet_digest = hash_file(&cli.packet_archive)?;
    verify_digest(
        &packet_digest,
        Some(OFFICIAL_PACKET_ARCHIVE_SIZE),
        Some(OFFICIAL_PACKET_ARCHIVE_MD5),
        &cli.packet_archive_sha256,
        "GeNIS 官方包归档",
    )?;
    let flow_digest = hash_file(&cli.flow_archive)?;
    verify_digest(
        &flow_digest,
        Some(OFFICIAL_FLOW_ARCHIVE_SIZE),
        Some(OFFICIAL_FLOW_ARCHIVE_MD5),
        OFFICIAL_FLOW_ARCHIVE_SHA256,
        "GeNIS 官方流归档",
    )?;
    let candidate_digest = hash_file(&cli.candidate_manifest)?;
    verify_digest(
        &candidate_digest,
        None,
        None,
        &cli.candidate_manifest_sha256,
        "冻结候选清单",
    )?;
    let member_map_digest = hash_file(&cli.member_map)?;
    verify_digest(
        &member_map_digest,
        None,
        None,
        &cli.member_map_sha256,
        "成员配对清单",
    )?;

    let candidates = load_candidates(&cli.candidate_manifest, cli.expected_candidate_count)?;
    let pairs = load_member_pairs(&cli.member_map, cli.expected_member_count)?;
    let mut flow_archive = open_zip(&cli.flow_archive, "GeNIS 官方流归档")?;
    let mut packet_archive = open_zip(&cli.packet_archive, "GeNIS 官方包归档")?;
    validate_zip_members(&mut flow_archive, &mut packet_archive, &pairs)?;
    let (mut flows, mut member_audits) = load_flows(
        &mut flow_archive,
        &pairs,
        &candidates,
        &flow_digest.sha256,
        cli.max_flow_bindings,
    )?;
    drop(flow_archive);
    let indexes = build_flow_indexes(&flows, pairs.len())?;
    let packet_statistics = process_packets(
        &mut packet_archive,
        &pairs,
        &indexes,
        &mut flows,
        &mut member_audits,
        &cli,
    )?;
    drop(packet_archive);
    validate_resolved_bindings(&flows)?;
    let mut all_rows_loaded = 0_u64;
    for audit in &member_audits {
        checked_add(
            &mut all_rows_loaded,
            audit.flow_rows_seen,
            "全部流记录数",
        )?;
    }

    let comparison_rows = build_comparison_rows(&flows)?;
    let summary = build_summary(
        &comparison_rows,
        &flows,
        all_rows_loaded,
        cli.expected_candidate_count,
        packet_statistics.clone(),
    )?;
    let transaction = OutputTransaction::new(&cli.output)?;
    write_comparison_parquet(
        &transaction.path("flow_byte_comparison.parquet"),
        &comparison_rows,
    )?;
    write_json(&transaction.path("summary.json"), &summary)?;

    let elapsed_milliseconds = u64::try_from(started.elapsed().as_millis())
        .context("运行耗时毫秒数超出 u64")?;
    let toolchain = ToolchainAudit {
        rustc_verbose_version: command_version("rustc", &["-vV"])?,
        cargo_version: command_version("cargo", &["--version"])?,
        target_arch: std::env::consts::ARCH,
        target_os: std::env::consts::OS,
    };
    let run_manifest = RunManifest {
        schema_version: SCHEMA_VERSION,
        status: "completed",
        review_status: "review_pending",
        tool_name: env!("CARGO_PKG_NAME"),
        tool_version: env!("CARGO_PKG_VERSION"),
        tool_revision: cli.tool_revision,
        execution_code_lock_sha256: cli.execution_code_lock_sha256,
        executable_size_bytes: executable_digest.size_bytes,
        executable_sha256: executable_digest.sha256,
        toolchain,
        inputs: vec![
            input_audit(PACKET_ARCHIVE_LOGICAL_PATH, &packet_digest),
            input_audit(FLOW_ARCHIVE_LOGICAL_PATH, &flow_digest),
            input_audit(CANDIDATE_LOGICAL_PATH, &candidate_digest),
            input_audit(MEMBER_MAP_LOGICAL_PATH, &member_map_digest),
        ],
        member_audits,
        expected_candidate_count: usize_to_u64(cli.expected_candidate_count, "预期候选数")?,
        all_rows_loaded: summary.all_rows_loaded,
        candidate_identity_unique: summary.candidate_identity_unique,
        candidate_identity_missing: summary.candidate_identity_missing,
        candidate_identity_ambiguous: summary.candidate_identity_ambiguous,
        dur_inverse_empty: summary.dur_inverse_empty,
        dur_interval_match: summary.dur_interval_match,
        dur_interval_mismatch: summary.dur_interval_mismatch,
        repeated_flow_id_candidate_count: summary.repeated_flow_id_candidate_count,
        time_tolerance_ns: cli.time_tolerance_ns,
        absolute_time_rounding_radius_ns: u64::try_from(ABSOLUTE_TIME_ROUNDING_RADIUS_NS)
            .context("绝对时间舍入半径无法转换为 u64")?,
        max_pcapng_block_bytes: usize_to_u64(cli.max_pcapng_block_bytes, "PCAPNG 块上限")?,
        max_flow_bindings: usize_to_u64(cli.max_flow_bindings, "流绑定上限")?,
        max_fragment_contexts: usize_to_u64(cli.max_fragment_contexts, "分片上下文上限")?,
        elapsed_milliseconds,
        peak_rss_bytes: peak_rss_bytes()?,
        packet_statistics,
        semantic_decision: summary.decision,
        error_count: 0,
    };
    write_json(&transaction.path("run_manifest.json"), &run_manifest)?;

    let root = transaction.path("");
    let mut artifacts = vec![
        artifact_entry(&root, "flow_byte_comparison.parquet")?,
        artifact_entry(&root, "run_manifest.json")?,
        artifact_entry(&root, "summary.json")?,
    ];
    artifacts.sort_by(|left, right| left.relative_path.cmp(&right.relative_path));
    let artifact_manifest = ArtifactManifest {
        schema_version: SCHEMA_VERSION,
        status: "completed",
        review_status: "review_pending",
        self_hash_excluded: true,
        artifacts,
    };
    write_json(
        &transaction.path("artifact_manifest.json"),
        &artifact_manifest,
    )?;
    transaction.publish()?;
    Ok(())
}
