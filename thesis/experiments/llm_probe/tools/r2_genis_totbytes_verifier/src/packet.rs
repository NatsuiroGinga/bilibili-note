use ahash::AHashMap;
use anyhow::{Context, Result, bail, ensure};

use crate::model::PacketStatistics;
use crate::pcapng::{Endian, PcapPacket};

const LINKTYPE_NULL: u16 = 0;
const LINKTYPE_ETHERNET: u16 = 1;
const LINKTYPE_RAW: u16 = 101;
const LINKTYPE_LINUX_SLL: u16 = 113;
const LINKTYPE_IPV4: u16 = 228;
const LINKTYPE_IPV6: u16 = 229;
const LINKTYPE_LINUX_SLL2: u16 = 276;

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum IpAddress {
    V4([u8; 4]),
    V6([u8; 16]),
}

#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct Endpoint {
    pub address: IpAddress,
    pub port: u16,
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub struct ConnectionKey {
    pub protocol: u8,
    pub low: Endpoint,
    pub high: Endpoint,
}

impl ConnectionKey {
    pub fn new(protocol: u8, source: Endpoint, destination: Endpoint) -> Self {
        let (low, high) = if source <= destination {
            (source, destination)
        } else {
            (destination, source)
        };
        Self {
            protocol,
            low,
            high,
        }
    }
}

#[derive(Clone, Copy, Debug)]
pub struct ParsedPacket {
    pub source: Endpoint,
    pub destination: Endpoint,
    pub key: ConnectionKey,
    pub l2_wire_bytes: u64,
    pub l3_network_bytes: u64,
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
struct FragmentKey {
    source: IpAddress,
    destination: IpAddress,
    protocol: u8,
    identification: u32,
}

#[derive(Clone, Copy, Debug)]
struct FragmentPorts {
    source: u16,
    destination: u16,
}

pub struct FragmentCache {
    entries: AHashMap<FragmentKey, FragmentPorts>,
    maximum_entries: usize,
}

impl FragmentCache {
    pub fn new(maximum_entries: usize) -> Result<Self> {
        ensure!(maximum_entries > 0, "IP 分片上下文上限必须大于 0");
        Ok(Self {
            entries: AHashMap::with_capacity(maximum_entries.min(65_536)),
            maximum_entries,
        })
    }

    fn insert(&mut self, key: FragmentKey, ports: FragmentPorts) -> Result<()> {
        if !self.entries.contains_key(&key) {
            ensure!(
                self.entries.len() < self.maximum_entries,
                "IP 分片上下文超过有界内存上限"
            );
        }
        self.entries.insert(key, ports);
        Ok(())
    }

    fn resolve(&mut self, key: &FragmentKey, is_last: bool) -> Option<FragmentPorts> {
        if is_last {
            self.entries.remove(key)
        } else {
            self.entries.get(key).copied()
        }
    }

    pub fn remaining(&self) -> usize {
        self.entries.len()
    }
}

fn read_be_u16(bytes: &[u8]) -> Result<u16> {
    let raw: [u8; 2] = bytes
        .get(..2)
        .context("网络报头 u16 字段被截断")?
        .try_into()
        .context("网络报头 u16 字段长度错误")?;
    Ok(u16::from_be_bytes(raw))
}

fn read_be_u32(bytes: &[u8]) -> Result<u32> {
    let raw: [u8; 4] = bytes
        .get(..4)
        .context("网络报头 u32 字段被截断")?
        .try_into()
        .context("网络报头 u32 字段长度错误")?;
    Ok(u32::from_be_bytes(raw))
}

fn network_offset(captured: &[u8], linktype: u16, endian: Endian) -> Result<Option<usize>> {
    match linktype {
        LINKTYPE_ETHERNET => {
            ensure!(captured.len() >= 14, "以太网帧头被截断");
            let mut offset = 14_usize;
            let mut ether_type = read_be_u16(&captured[12..14])?;
            let mut vlan_depth = 0_u8;
            while matches!(ether_type, 0x8100 | 0x88a8 | 0x9100) {
                vlan_depth = vlan_depth.checked_add(1).context("VLAN 层数溢出")?;
                ensure!(vlan_depth <= 4, "以太网 VLAN 封装超过四层上限");
                ensure!(captured.len() >= offset + 4, "VLAN 报头被截断");
                ether_type = read_be_u16(&captured[offset + 2..offset + 4])?;
                offset += 4;
            }
            if matches!(ether_type, 0x8847 | 0x8848) {
                let mut label_count = 0_u8;
                loop {
                    ensure!(captured.len() >= offset + 4, "MPLS 标签被截断");
                    label_count = label_count.checked_add(1).context("MPLS 标签计数溢出")?;
                    ensure!(label_count <= 16, "MPLS 标签栈超过十六层上限");
                    let is_bottom = captured[offset + 2] & 0x01 != 0;
                    offset += 4;
                    if is_bottom {
                        break;
                    }
                }
                let version = captured.get(offset).context("MPLS 后网络报头被截断")? >> 4;
                return match version {
                    4 | 6 => Ok(Some(offset)),
                    _ => Ok(None),
                };
            }
            match ether_type {
                0x0800 | 0x86dd => Ok(Some(offset)),
                _ => Ok(None),
            }
        }
        LINKTYPE_RAW => {
            let version = captured.first().context("RAW 链路包为空")? >> 4;
            match version {
                4 | 6 => Ok(Some(0)),
                _ => Ok(None),
            }
        }
        LINKTYPE_IPV4 => Ok(Some(0)),
        LINKTYPE_IPV6 => Ok(Some(0)),
        LINKTYPE_LINUX_SLL => {
            ensure!(captured.len() >= 16, "Linux SLL 报头被截断");
            match read_be_u16(&captured[14..16])? {
                0x0800 | 0x86dd => Ok(Some(16)),
                _ => Ok(None),
            }
        }
        LINKTYPE_LINUX_SLL2 => {
            ensure!(captured.len() >= 20, "Linux SLL2 报头被截断");
            match read_be_u16(&captured[..2])? {
                0x0800 | 0x86dd => Ok(Some(20)),
                _ => Ok(None),
            }
        }
        LINKTYPE_NULL => {
            ensure!(captured.len() >= 5, "NULL 链路报头被截断");
            let family_raw: [u8; 4] = captured[..4].try_into().context("NULL 地址族长度错误")?;
            let family = match endian {
                Endian::Little => u32::from_le_bytes(family_raw),
                Endian::Big => u32::from_be_bytes(family_raw),
            };
            let version = captured[4] >> 4;
            ensure!(
                (family == 2 && version == 4)
                    || (matches!(family, 10 | 24 | 28 | 30) && version == 6),
                "NULL 链路地址族与 IP 版本不一致"
            );
            Ok(Some(4))
        }
        _ => bail!("PCAPNG 出现未支持的链路类型：{linktype}"),
    }
}

fn transport_ports(protocol: u8, bytes: &[u8]) -> Result<FragmentPorts> {
    if matches!(protocol, 6 | 17 | 33 | 132) {
        ensure!(bytes.len() >= 4, "传输层端口字段被截断");
        Ok(FragmentPorts {
            source: read_be_u16(bytes)?,
            destination: read_be_u16(&bytes[2..])?,
        })
    } else {
        Ok(FragmentPorts {
            source: 0,
            destination: 0,
        })
    }
}

fn ensure_l3_fits_wire(original_len: u32, network_offset: usize, network_len: u64) -> Result<()> {
    let required = u64::try_from(network_offset)
        .context("网络层偏移无法转换为 u64")?
        .checked_add(network_len)
        .context("网络层线上长度溢出")?;
    ensure!(required <= u64::from(original_len), "IP 报头声明长度超过 PCAP 线上长度");
    Ok(())
}

fn endpoints(
    source_address: IpAddress,
    destination_address: IpAddress,
    protocol: u8,
    ports: FragmentPorts,
) -> ParsedPacketEndpoints {
    let source = Endpoint {
        address: source_address,
        port: ports.source,
    };
    let destination = Endpoint {
        address: destination_address,
        port: ports.destination,
    };
    ParsedPacketEndpoints {
        source,
        destination,
        key: ConnectionKey::new(protocol, source, destination),
    }
}

struct ParsedPacketEndpoints {
    source: Endpoint,
    destination: Endpoint,
    key: ConnectionKey,
}

fn parse_ipv4(
    packet: PcapPacket<'_>,
    offset: usize,
    fragments: &mut FragmentCache,
    statistics: &mut PacketStatistics,
) -> Result<ParsedPacket> {
    let ip = packet.captured.get(offset..).context("IPv4 报头偏移超出捕获长度")?;
    ensure!(ip.len() >= 20, "IPv4 基础报头被截断");
    ensure!(ip[0] >> 4 == 4, "链路类型指向的报头不是 IPv4");
    let header_len = usize::from(ip[0] & 0x0f)
        .checked_mul(4)
        .context("IPv4 报头长度溢出")?;
    ensure!(header_len >= 20 && ip.len() >= header_len, "IPv4 报头长度无效或被截断");
    let network_len = u64::from(read_be_u16(&ip[2..4])?);
    ensure!(network_len >= u64::try_from(header_len).context("IPv4 报头长度转换失败")?, "IPv4 total_length 小于报头长度");
    ensure_l3_fits_wire(packet.original_len, offset, network_len)?;
    let protocol = ip[9];
    let source_address = IpAddress::V4(ip[12..16].try_into().context("IPv4 源地址被截断")?);
    let destination_address = IpAddress::V4(ip[16..20].try_into().context("IPv4 目的地址被截断")?);
    let fragment_field = read_be_u16(&ip[6..8])?;
    let fragment_offset = fragment_field & 0x1fff;
    let more_fragments = fragment_field & 0x2000 != 0;
    let identification = u32::from(read_be_u16(&ip[4..6])?);
    let fragment_key = FragmentKey {
        source: source_address,
        destination: destination_address,
        protocol,
        identification,
    };
    let declared_len = usize::try_from(network_len).context("IPv4 total_length 无法转换为 usize")?;
    let transport_end = declared_len.min(ip.len());
    let ports = if fragment_offset == 0 {
        let value = transport_ports(protocol, &ip[header_len..transport_end])?;
        if more_fragments {
            statistics.ipv4_fragments_seen = statistics.ipv4_fragments_seen.checked_add(1).context("IPv4 分片计数溢出")?;
            fragments.insert(fragment_key, value)?;
        }
        value
    } else {
        statistics.ipv4_fragments_seen = statistics.ipv4_fragments_seen.checked_add(1).context("IPv4 分片计数溢出")?;
        match fragments.resolve(&fragment_key, !more_fragments) {
            Some(value) => value,
            None => {
                statistics.unresolved_fragments = statistics.unresolved_fragments.checked_add(1).context("未解析分片计数溢出")?;
                bail!("IPv4 非首分片缺少首分片连接上下文")
            }
        }
    };
    let parsed = endpoints(source_address, destination_address, protocol, ports);
    Ok(ParsedPacket {
        source: parsed.source,
        destination: parsed.destination,
        key: parsed.key,
        l2_wire_bytes: u64::from(packet.original_len),
        l3_network_bytes: network_len,
    })
}

fn parse_ipv6(
    packet: PcapPacket<'_>,
    offset: usize,
    fragments: &mut FragmentCache,
    statistics: &mut PacketStatistics,
) -> Result<ParsedPacket> {
    let ip = packet.captured.get(offset..).context("IPv6 报头偏移超出捕获长度")?;
    ensure!(ip.len() >= 40, "IPv6 基础报头被截断");
    ensure!(ip[0] >> 4 == 6, "链路类型指向的报头不是 IPv6");
    let payload_len = u64::from(read_be_u16(&ip[4..6])?);
    if payload_len == 0 && ip[6] == 0 {
        bail!("IPv6 payload_length 为 0 且含载荷，疑似巨型载荷；当前合同拒绝猜测")
    }
    let network_len = 40_u64.checked_add(payload_len).context("IPv6 网络层长度溢出")?;
    ensure_l3_fits_wire(packet.original_len, offset, network_len)?;
    let source_address = IpAddress::V6(ip[8..24].try_into().context("IPv6 源地址被截断")?);
    let destination_address = IpAddress::V6(ip[24..40].try_into().context("IPv6 目的地址被截断")?);
    let captured_network_end = usize::try_from(network_len)
        .ok()
        .map(|length| length.min(ip.len()))
        .context("IPv6 网络层长度无法转换为 usize")?;
    let mut next_header = ip[6];
    let mut cursor = 40_usize;
    let mut extension_count = 0_u8;
    let mut fragment: Option<(FragmentKey, bool)> = None;

    loop {
        extension_count = extension_count.checked_add(1).context("IPv6 扩展头计数溢出")?;
        ensure!(extension_count <= 16, "IPv6 扩展头超过十六层上限");
        match next_header {
            0 | 43 | 60 => {
                ensure!(cursor + 2 <= captured_network_end, "IPv6 扩展头被截断");
                let following = ip[cursor];
                let length = usize::from(ip[cursor + 1])
                    .checked_add(1)
                    .and_then(|value| value.checked_mul(8))
                    .context("IPv6 扩展头长度溢出")?;
                ensure!(cursor + length <= captured_network_end, "IPv6 扩展头超出声明长度或被截断");
                cursor += length;
                next_header = following;
            }
            51 => {
                ensure!(cursor + 2 <= captured_network_end, "IPv6 AH 报头被截断");
                let following = ip[cursor];
                let length = usize::from(ip[cursor + 1])
                    .checked_add(2)
                    .and_then(|value| value.checked_mul(4))
                    .context("IPv6 AH 长度溢出")?;
                ensure!(cursor + length <= captured_network_end, "IPv6 AH 超出声明长度或被截断");
                cursor += length;
                next_header = following;
            }
            44 => {
                ensure!(fragment.is_none(), "IPv6 包含重复 Fragment Header");
                ensure!(cursor + 8 <= captured_network_end, "IPv6 Fragment Header 被截断");
                let following = ip[cursor];
                ensure!(
                    !matches!(following, 0 | 43 | 44 | 51 | 60),
                    "IPv6 Fragment Header 后仍有扩展头，当前合同拒绝歧义连接键"
                );
                let field = read_be_u16(&ip[cursor + 2..cursor + 4])?;
                let fragment_offset = (field & 0xfff8) >> 3;
                let more_fragments = field & 0x0001 != 0;
                let identification = read_be_u32(&ip[cursor + 4..cursor + 8])?;
                let key = FragmentKey {
                    source: source_address,
                    destination: destination_address,
                    protocol: following,
                    identification,
                };
                statistics.ipv6_fragments_seen = statistics.ipv6_fragments_seen.checked_add(1).context("IPv6 分片计数溢出")?;
                cursor += 8;
                next_header = following;
                if fragment_offset != 0 {
                    let ports = match fragments.resolve(&key, !more_fragments) {
                        Some(value) => value,
                        None => {
                            statistics.unresolved_fragments = statistics.unresolved_fragments.checked_add(1).context("未解析分片计数溢出")?;
                            bail!("IPv6 非首分片缺少首分片连接上下文")
                        }
                    };
                    let parsed = endpoints(source_address, destination_address, following, ports);
                    return Ok(ParsedPacket {
                        source: parsed.source,
                        destination: parsed.destination,
                        key: parsed.key,
                        l2_wire_bytes: u64::from(packet.original_len),
                        l3_network_bytes: network_len,
                    });
                }
                fragment = Some((key, more_fragments));
            }
            _ => break,
        }
    }

    ensure!(cursor <= captured_network_end, "IPv6 传输层偏移超出捕获长度");
    let ports = transport_ports(next_header, &ip[cursor..captured_network_end])?;
    if let Some((key, more_fragments)) = fragment {
        if more_fragments {
            fragments.insert(key, ports)?;
        }
    }
    let parsed = endpoints(source_address, destination_address, next_header, ports);
    Ok(ParsedPacket {
        source: parsed.source,
        destination: parsed.destination,
        key: parsed.key,
        l2_wire_bytes: u64::from(packet.original_len),
        l3_network_bytes: network_len,
    })
}

pub fn parse_packet(
    packet: PcapPacket<'_>,
    fragments: &mut FragmentCache,
    statistics: &mut PacketStatistics,
) -> Result<Option<ParsedPacket>> {
    let Some(offset) = network_offset(packet.captured, packet.linktype, packet.section_endian)? else {
        return Ok(None);
    };
    let version = packet
        .captured
        .get(offset)
        .context("网络层报头在捕获数据中缺失")?
        >> 4;
    match version {
        4 => parse_ipv4(packet, offset, fragments, statistics).map(Some),
        6 => parse_ipv6(packet, offset, fragments, statistics).map(Some),
        _ => bail!("链路层声明为 IP，但网络层版本不是 IPv4 或 IPv6"),
    }
}
