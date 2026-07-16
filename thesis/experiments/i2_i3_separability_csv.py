#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验：守恒不变量 I2（流双向守恒）/ I3-弱（单向 SYN）在 IDS2018 上的可分性
目的：验证方案 B 的守恒不变量能否在真实 IDS2018 数据上区分正常/攻击（开题可行性实证）
数据：CSE-CIC-IDS2018 Thursday-15-02-2018（DoS GoldenEye + Slowloris 日），CICFlowMeter 流级 CSV
依赖：仅 Python 标准库（csv/statistics），无第三方包

运行：
  python3 thesis/experiments/i2_i3_separability_csv.py
（默认数据路径 raw/datasets/CSE-CIC-IDS2018/Thursday-15-02-2018_TrafficForML_CICFlowMeter.csv，可改 DATA）

不变量定义（见 output/数据集构建章节设计_开题实施计划.md §5）：
  I2 流双向守恒：前向字节占比 i2 = TotLen Fwd / (TotLen Fwd + TotLen Bwd)
                  正常服务应双向均衡（有请求有响应）；单向洪泛/扫描 → i2 极端（近0或1）
  I3-弱 TCP 状态守恒（流级近似）：SYN>0 且反向包=0 → 半开/单向连接嫌疑
                  （严格 I3 需逐包未应答 SYN，见 i3_strict_pcap.py）
"""
import csv, collections, statistics, os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA = os.path.join(REPO, 'raw/datasets/CSE-CIC-IDS2018/Thursday-15-02-2018_TrafficForML_CICFlowMeter.csv')

def main():
    with open(DATA, newline='', encoding='utf-8', errors='replace') as fh:
        r = csv.reader(fh)
        hdr = next(r)
        idx = {c.strip(): i for i, c in enumerate(hdr)}
        rows = collections.defaultdict(list)
        n = 0
        for row in r:
            if len(row) < len(hdr):
                continue
            lab = row[idx['Label']].strip()
            if lab == 'Label':
                continue
            try:
                tf = int(float(row[idx['TotLen Fwd Pkts']] or 0))
                tb = int(float(row[idx['TotLen Bwd Pkts']] or 0))
                pb = int(float(row[idx['Tot Bwd Pkts']] or 0))
                syn = int(float(row[idx['SYN Flag Cnt']] or 0))
            except ValueError:
                continue
            i2 = tf / (tf + tb + 1)                 # 前向字节占比
            i3 = 1 if (syn > 0 and pb == 0) else 0  # 单向 SYN 嫌疑
            rows[lab].append((i2, syn, i3))
            n += 1

    print(f"总流数: {n}")
    print(f"\n{'标签':<28}{'流数':>8} {'I2均值':>8} {'I2_std':>8} {'I2极端%':>8} {'单向SYN%':>9} {'SYN均值':>8}")
    print('-' * 90)
    for lab, rs in rows.items():
        i2s = [x[0] for x in rs]
        syns = [x[1] for x in rs]
        i3s = [x[2] for x in rs]
        extreme = sum(1 for v in i2s if v > 0.95 or v < 0.05) / len(rs) * 100
        print(f"{lab:<28}{len(rs):>8} {statistics.mean(i2s):>8.3f} "
              f"{statistics.pstdev(i2s):>8.3f} {extreme:>7.1f}% "
              f"{sum(i3s)/len(rs)*100:>8.1f}% {statistics.mean(syns):>8.1f}")

    # 朴素判据可分性：I2极端 或 单向SYN → 判攻击
    print("\n=== 朴素判据可分性（I2极端 或 单向SYN → 攻击）===")
    benign = rows.get('Benign', [])
    for atk in ['DoS attacks-GoldenEye', 'DoS attacks-Slowloris']:
        if atk not in rows:
            continue
        is_pos = lambda x: x[0] > 0.95 or x[0] < 0.05 or x[2] == 1
        tp = sum(1 for x in rows[atk] if is_pos(x))
        fn = len(rows[atk]) - tp
        tn = sum(1 for x in benign if not is_pos(x))
        fp = len(benign) - tn
        acc = (tp + tn) / (len(rows[atk]) + len(benign)) * 100
        rec = tp / len(rows[atk]) * 100
        fpr = fp / max(tn + fp, 1) * 100
        print(f"{atk}: 召回{rec:.1f}% 误报率{fpr:.1f}% 准确率{acc:.1f}% (TP{tp} FN{fn} FP{fp} TN{tn})")

if __name__ == '__main__':
    main()
