#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验：严格 I3（TCP 状态守恒）在真实 IDS2018 pcap 上的逐包验证
目的：v1-v3 只跑流级 CSV；本脚本在 zip-FF 恢复的真实 pcap 上逐包算"未应答 SYN"。
方法：dpkt 解析 pcap（Ethernet→IPv4→TCP），按 5 元组跟踪 SYN/SYN-ACK，
      统计每 1 分钟窗口"未应答 SYN 流占比"（严格 I3 残差）。
      SYN flood / Slowloris 半开 → 未答 SYN 骤增 → I3 残差尖峰。
依赖：dpkt（uv 环境已装）。运行：uv run python i3_strict_pcap.py
数据：raw/datasets/CSE-CIC-IDS2018-PCAP/extracted/pcap/（Thursday-15-02 DoS GoldenEye+Slowloris 日）。
"""
import os, glob, collections, statistics, dpkt

PCAP_DIR = os.path.join(os.path.dirname(__file__), '..', '..',
                        'raw/datasets/CSE-CIC-IDS2018-PCAP/extracted/pcap')
WIN = 60  # 1 分钟窗

def iter_tcp(path):
    """yield (ts, src_ip, sport, dst_ip, dport, flags) for each TCP/IPv4 packet."""
    with open(path, 'rb') as f:
        try:
            rdr = dpkt.pcap.Reader(f)
        except ValueError:
            return
        for ts, buf in rdr:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
            except Exception:
                continue
            ip = getattr(eth, 'data', None)
            if not isinstance(ip, dpkt.ip.IP) or ip.p != dpkt.ip.IP_PROTO_TCP:
                continue
            tcp = getattr(ip, 'data', None)
            if not isinstance(tcp, dpkt.tcp.TCP):
                continue
            src_ip = '.'.join(str(b) for b in ip.src)
            dst_ip = '.'.join(str(b) for b in ip.dst)
            yield ts, src_ip, tcp.sport, dst_ip, tcp.dport, tcp.flags

def analyze(path):
    flow_firstwin = {}                       # fk -> 首个 SYN 所在窗口
    flow_answered = collections.defaultdict(int)  # fk -> 是否被 SYN-ACK 应答
    n = 0
    for ts, sip, sp, dip, dp, flags in iter_tcp(path):
        n += 1
        fk = (sip, sp, dip, dp)              # SYN 发起方向
        rev = (dip, dp, sip, sp)             # 对端反向
        w = int(ts) // WIN
        is_syn = bool(flags & dpkt.tcp.TH_SYN) and not (flags & dpkt.tcp.TH_ACK)
        is_synack = bool(flags & dpkt.tcp.TH_SYN) and (flags & dpkt.tcp.TH_ACK)
        if is_syn and fk not in flow_firstwin:
            flow_firstwin[fk] = w
        if is_synack:
            # 对端 rev 方向回了 SYN-ACK → rev 的 SYN 被应答
            flow_answered[rev] = 1
    win_total = collections.Counter()
    win_ans = collections.Counter()
    for fk, w in flow_firstwin.items():
        win_total[w] += 1
        if flow_answered.get(fk):
            win_ans[w] += 1
    return n, win_total, win_ans

def main():
    files = sorted(glob.glob(os.path.join(PCAP_DIR, '*')))
    if not files:
        print("未找到 pcap，先解压 extracted/pcap/"); return
    for path in files:
        n, wt, wa = analyze(path)
        if n == 0:
            print(f"{os.path.basename(path)}: 无 TCP 包"); continue
        print(f"\n##### {os.path.basename(path)} ({n} TCP 包) #####")
        i3s = []
        for w in sorted(set(wt) | set(wa)):
            tot = wt.get(w, 0)
            if tot == 0:
                continue
            un = tot - wa.get(w, 0)
            i3s.append((w, tot, un, un / tot))
        i3s.sort(key=lambda x: -x[3])
        print(f"{'窗口':>10} {'SYN流':>8} {'未答SYN':>8} {'I3残差':>8}")
        for w, tot, un, i3 in i3s[:15]:
            print(f"{w:>10} {tot:>8} {un:>8} {i3*100:>7.1f}%")
        if i3s:
            allv = [x[3] for x in i3s]
            print(f"  窗口数 {len(i3s)} | I3均值 {statistics.mean(allv)*100:.1f}% | "
                  f"I3max {max(allv)*100:.1f}% | I3>50%窗口 {sum(1 for v in allv if v>0.5)}/{len(i3s)}")

if __name__ == '__main__':
    main()
