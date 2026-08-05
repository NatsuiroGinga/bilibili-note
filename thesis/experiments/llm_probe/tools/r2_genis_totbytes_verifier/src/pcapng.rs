use std::collections::BTreeSet;
use std::io::{ErrorKind, Read};

use anyhow::{Context, Result, bail, ensure};

const SECTION_HEADER_BLOCK: [u8; 4] = [0x0a, 0x0d, 0x0d, 0x0a];
const INTERFACE_DESCRIPTION_BLOCK: u32 = 1;
const OBSOLETE_PACKET_BLOCK: u32 = 2;
const SIMPLE_PACKET_BLOCK: u32 = 3;
const ENHANCED_PACKET_BLOCK: u32 = 6;

#[derive(Clone, Copy, Debug)]
pub enum Endian {
    Little,
    Big,
}

#[derive(Clone, Copy, Debug)]
enum TimestampResolution {
    Decimal(u8),
    Binary(u8),
}

#[derive(Clone, Copy, Debug)]
struct Interface {
    linktype: u16,
    snaplen: u32,
    timestamp_resolution: TimestampResolution,
    timestamp_offset_seconds: i64,
}

#[derive(Clone, Copy, Debug)]
pub struct PcapPacket<'a> {
    pub timestamp_ns: i64,
    pub captured: &'a [u8],
    pub original_len: u32,
    pub linktype: u16,
    pub section_endian: Endian,
}

#[derive(Debug, Default)]
pub struct PcapNgStats {
    pub interface_count: u64,
    pub linktypes: BTreeSet<u16>,
    pub packet_count: u64,
}

fn read_u16(bytes: &[u8], endian: Endian) -> Result<u16> {
    let raw: [u8; 2] = bytes
        .get(..2)
        .context("PCAPNG u16 字段被截断")?
        .try_into()
        .context("PCAPNG u16 字段长度错误")?;
    Ok(match endian {
        Endian::Little => u16::from_le_bytes(raw),
        Endian::Big => u16::from_be_bytes(raw),
    })
}

fn read_u32(bytes: &[u8], endian: Endian) -> Result<u32> {
    let raw: [u8; 4] = bytes
        .get(..4)
        .context("PCAPNG u32 字段被截断")?
        .try_into()
        .context("PCAPNG u32 字段长度错误")?;
    Ok(match endian {
        Endian::Little => u32::from_le_bytes(raw),
        Endian::Big => u32::from_be_bytes(raw),
    })
}

fn read_i64(bytes: &[u8], endian: Endian) -> Result<i64> {
    let raw: [u8; 8] = bytes
        .get(..8)
        .context("PCAPNG i64 字段被截断")?
        .try_into()
        .context("PCAPNG i64 字段长度错误")?;
    Ok(match endian {
        Endian::Little => i64::from_le_bytes(raw),
        Endian::Big => i64::from_be_bytes(raw),
    })
}

fn read_exact_or_eof<R: Read>(reader: &mut R, buffer: &mut [u8]) -> Result<bool> {
    let mut offset = 0;
    while offset < buffer.len() {
        match reader.read(&mut buffer[offset..]) {
            Ok(0) if offset == 0 => return Ok(false),
            Ok(0) => bail!("PCAPNG 在块头中间提前结束"),
            Ok(read) => offset += read,
            Err(error) if error.kind() == ErrorKind::Interrupted => {}
            Err(error) => return Err(error).context("读取 PCAPNG 块头失败"),
        }
    }
    Ok(true)
}

fn section_endian(byte_order_magic: &[u8]) -> Result<Endian> {
    match byte_order_magic {
        [0x4d, 0x3c, 0x2b, 0x1a] => Ok(Endian::Little),
        [0x1a, 0x2b, 0x3c, 0x4d] => Ok(Endian::Big),
        _ => bail!("PCAPNG Section Header 的字节序魔数无效"),
    }
}

fn padded_length(length: usize) -> Result<usize> {
    length.checked_add(3).map(|value| value & !3).context("PCAPNG 选项长度溢出")
}

fn parse_interface_options(
    options: &[u8],
    endian: Endian,
) -> Result<(TimestampResolution, i64)> {
    let mut resolution = TimestampResolution::Decimal(6);
    let mut offset_seconds = 0_i64;
    let mut seen_resolution = false;
    let mut seen_offset = false;
    let mut cursor = 0_usize;
    while cursor < options.len() {
        ensure!(options.len() - cursor >= 4, "PCAPNG 接口选项头被截断");
        let code = read_u16(&options[cursor..], endian)?;
        let length = usize::from(read_u16(&options[cursor + 2..], endian)?);
        cursor += 4;
        if code == 0 {
            ensure!(length == 0, "PCAPNG 选项结束标记长度必须为 0");
            break;
        }
        let padded = padded_length(length)?;
        ensure!(cursor + padded <= options.len(), "PCAPNG 接口选项值被截断");
        let value = &options[cursor..cursor + length];
        match code {
            9 => {
                ensure!(!seen_resolution, "PCAPNG 接口重复声明 if_tsresol");
                ensure!(value.len() == 1, "PCAPNG if_tsresol 长度必须为 1");
                let raw = value[0];
                resolution = if raw & 0x80 == 0 {
                    TimestampResolution::Decimal(raw)
                } else {
                    TimestampResolution::Binary(raw & 0x7f)
                };
                seen_resolution = true;
            }
            14 => {
                ensure!(!seen_offset, "PCAPNG 接口重复声明 if_tsoffset");
                ensure!(value.len() == 8, "PCAPNG if_tsoffset 长度必须为 8");
                offset_seconds = read_i64(value, endian)?;
                seen_offset = true;
            }
            _ => {}
        }
        cursor += padded;
    }
    Ok((resolution, offset_seconds))
}

fn timestamp_ns(ticks: u64, interface: Interface) -> Result<i64> {
    let base_ns = match interface.timestamp_resolution {
        TimestampResolution::Decimal(exponent) if exponent <= 9 => {
            let factor = 10_u128
                .checked_pow(u32::from(9 - exponent))
                .context("PCAPNG 十进制时间分辨率溢出")?;
            u128::from(ticks)
                .checked_mul(factor)
                .context("PCAPNG 时间戳溢出")?
        }
        TimestampResolution::Decimal(exponent) => {
            let divisor = 10_u128
                .checked_pow(u32::from(exponent - 9))
                .context("PCAPNG 十进制时间分辨率溢出")?;
            ensure!(u128::from(ticks) % divisor == 0, "PCAPNG 时间戳含不可无损表示的亚纳秒部分");
            u128::from(ticks) / divisor
        }
        TimestampResolution::Binary(exponent) => {
            ensure!(exponent < 128, "PCAPNG 二进制时间分辨率超出支持范围");
            let numerator = u128::from(ticks)
                .checked_mul(1_000_000_000)
                .context("PCAPNG 时间戳溢出")?;
            let divisor = 1_u128 << exponent;
            ensure!(numerator % divisor == 0, "PCAPNG 时间戳含不可无损表示的亚纳秒部分");
            numerator / divisor
        }
    };
    let base = i128::try_from(base_ns).context("PCAPNG 时间戳超出 i128")?;
    let offset = i128::from(interface.timestamp_offset_seconds)
        .checked_mul(1_000_000_000)
        .context("PCAPNG 时间偏移溢出")?;
    let combined = base.checked_add(offset).context("PCAPNG 时间戳加偏移后溢出")?;
    i64::try_from(combined).context("PCAPNG 纳秒时间戳超出 i64")
}

fn packet_timestamp(body: &[u8], interface: Interface, endian: Endian) -> Result<i64> {
    let high = u64::from(read_u32(body, endian)?);
    let low = u64::from(read_u32(&body[4..], endian)?);
    timestamp_ns((high << 32) | low, interface)
}

pub fn read_pcapng<R, F>(
    reader: &mut R,
    max_block_bytes: usize,
    mut on_packet: F,
) -> Result<PcapNgStats>
where
    R: Read,
    F: FnMut(PcapPacket<'_>) -> Result<()>,
{
    ensure!(max_block_bytes >= 28, "PCAPNG 最大块大小不能小于 28 字节");
    let mut current_endian: Option<Endian> = None;
    let mut interfaces: Vec<Interface> = Vec::new();
    let mut stats = PcapNgStats::default();
    let mut header = [0_u8; 8];
    let mut remaining = Vec::new();

    while read_exact_or_eof(reader, &mut header)? {
        if header[..4] == SECTION_HEADER_BLOCK {
            let mut magic = [0_u8; 4];
            reader.read_exact(&mut magic).context("读取 PCAPNG 字节序魔数失败")?;
            let endian = section_endian(&magic)?;
            let total_length = usize::try_from(read_u32(&header[4..], endian)?)
                .context("PCAPNG 块长度无法转换为 usize")?;
            ensure!(
                total_length >= 28 && total_length % 4 == 0,
                "PCAPNG Section Header 块长度无效"
            );
            ensure!(total_length <= max_block_bytes, "PCAPNG 块超过配置上限");
            let remaining_length = total_length - 12;
            remaining.resize(remaining_length, 0);
            reader.read_exact(&mut remaining).context("读取 PCAPNG Section Header 失败")?;
            let trailing = read_u32(&remaining[remaining_length - 4..], endian)?;
            ensure!(usize::try_from(trailing).ok() == Some(total_length), "PCAPNG 块首尾长度不一致");
            ensure!(read_u16(&remaining[..2], endian)? == 1, "仅支持 PCAPNG 主版本 1");
            current_endian = Some(endian);
            interfaces.clear();
            continue;
        }

        let endian = current_endian.context("PCAPNG 首个块不是 Section Header")?;
        let block_type = read_u32(&header[..4], endian)?;
        let total_length = usize::try_from(read_u32(&header[4..], endian)?)
            .context("PCAPNG 块长度无法转换为 usize")?;
        ensure!(total_length >= 12 && total_length % 4 == 0, "PCAPNG 块长度无效");
        ensure!(total_length <= max_block_bytes, "PCAPNG 块超过配置上限");
        remaining.resize(total_length - 8, 0);
        reader.read_exact(&mut remaining).context("读取 PCAPNG 块体失败")?;
        let trailing = read_u32(&remaining[remaining.len() - 4..], endian)?;
        ensure!(usize::try_from(trailing).ok() == Some(total_length), "PCAPNG 块首尾长度不一致");
        let body = &remaining[..remaining.len() - 4];

        match block_type {
            INTERFACE_DESCRIPTION_BLOCK => {
                ensure!(body.len() >= 8, "PCAPNG 接口描述块被截断");
                let linktype = read_u16(body, endian)?;
                let snaplen = read_u32(&body[4..], endian)?;
                let (timestamp_resolution, timestamp_offset_seconds) =
                    parse_interface_options(&body[8..], endian)?;
                interfaces.push(Interface {
                    linktype,
                    snaplen,
                    timestamp_resolution,
                    timestamp_offset_seconds,
                });
                stats.interface_count = stats.interface_count.checked_add(1).context("接口计数溢出")?;
                stats.linktypes.insert(linktype);
            }
            ENHANCED_PACKET_BLOCK => {
                ensure!(body.len() >= 20, "PCAPNG 增强包块被截断");
                let interface_id = usize::try_from(read_u32(body, endian)?)
                    .context("PCAPNG 接口编号无法转换为 usize")?;
                let interface = *interfaces.get(interface_id).context("PCAPNG 包引用不存在的接口")?;
                let timestamp = packet_timestamp(&body[4..12], interface, endian)?;
                let captured_len = usize::try_from(read_u32(&body[12..], endian)?)
                    .context("PCAPNG 捕获长度无法转换为 usize")?;
                let original_len = read_u32(&body[16..], endian)?;
                ensure!(u64::try_from(captured_len).ok().is_some_and(|value| value <= u64::from(original_len)), "PCAPNG 捕获长度大于线上长度");
                if interface.snaplen != 0 {
                    ensure!(u64::try_from(captured_len).ok().is_some_and(|value| value <= u64::from(interface.snaplen)), "PCAPNG 捕获长度大于接口 snaplen");
                }
                let data_end = 20_usize.checked_add(captured_len).context("PCAPNG 包数据长度溢出")?;
                ensure!(data_end <= body.len(), "PCAPNG 增强包数据被截断");
                on_packet(PcapPacket {
                    timestamp_ns: timestamp,
                    captured: &body[20..data_end],
                    original_len,
                    linktype: interface.linktype,
                    section_endian: endian,
                })?;
                stats.packet_count = stats.packet_count.checked_add(1).context("包计数溢出")?;
            }
            OBSOLETE_PACKET_BLOCK => {
                ensure!(body.len() >= 20, "PCAPNG 旧包块被截断");
                let interface_id = usize::from(read_u16(body, endian)?);
                let interface = *interfaces.get(interface_id).context("PCAPNG 旧包块引用不存在的接口")?;
                let timestamp = packet_timestamp(&body[4..12], interface, endian)?;
                let captured_len = usize::try_from(read_u32(&body[12..], endian)?)
                    .context("PCAPNG 捕获长度无法转换为 usize")?;
                let original_len = read_u32(&body[16..], endian)?;
                ensure!(u64::try_from(captured_len).ok().is_some_and(|value| value <= u64::from(original_len)), "PCAPNG 捕获长度大于线上长度");
                let data_end = 20_usize.checked_add(captured_len).context("PCAPNG 包数据长度溢出")?;
                ensure!(data_end <= body.len(), "PCAPNG 旧包块数据被截断");
                on_packet(PcapPacket {
                    timestamp_ns: timestamp,
                    captured: &body[20..data_end],
                    original_len,
                    linktype: interface.linktype,
                    section_endian: endian,
                })?;
                stats.packet_count = stats.packet_count.checked_add(1).context("包计数溢出")?;
            }
            SIMPLE_PACKET_BLOCK => {
                bail!("PCAPNG Simple Packet Block 没有可用于精确流连接的时间戳")
            }
            _ => {}
        }
    }

    ensure!(current_endian.is_some(), "PCAPNG 文件为空或缺少 Section Header");
    ensure!(stats.interface_count > 0, "PCAPNG 没有接口描述块");
    Ok(stats)
}
