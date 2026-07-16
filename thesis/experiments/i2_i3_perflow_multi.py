#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 v3：跨攻击类型对比——守恒不变量 I2/I3-弱 对哪类攻击有效
动机：v1/v2 在 DoS GoldenEye/Slowloris（HTTP层洪水，双向）上无效。诊断：是攻击类型问题还是不变量整体问题？
方法：对多个 CSV 日，逐流算 I2（前向字节占比）+ I3-弱（单向SYN），按标签报均值 + 朴素判据召回/误报。
用法：python3 i2_i3_perflow_multi.py [csv路径...]
默认跑 Thursday-15-02(DoS) 与 Wednesday-21-02(DDoS HOIC)。
"""
import csv, collections, statistics, os, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
D = os.path.join(REPO, 'raw/datasets/CSE-CIC-IDS2018')
DEFAULTS = [
    f'{D}/Thursday-15-02-2018_TrafficForML_CICFlowMeter.csv',
    f'{D}/Wednesday-21-02-2018_TrafficForML_CICFlowMeter.csv',
    f'{D}/Wednesday-14-02-2018_TrafficForML_CICFlowMeter.csv',
]
FILES = sys.argv[1:] or DEFAULTS

def analyze(f):
    with open(f, newline='', encoding='utf-8', errors='replace') as fh:
        r = csv.reader(fh); hdr = next(r)
        idx = {c.strip(): i for i, c in enumerate(hdr)}
        rows = collections.defaultdict(list)
        for row in r:
            if len(row) < len(hdr): continue
            lab = row[idx['Label']].strip()
            if lab == 'Label': continue
            try:
                tf = int(float(row[idx['TotLen Fwd Pkts']] or 0))
                tb = int(float(row[idx['TotLen Bwd Pkts']] or 0))
                pb = int(float(row[idx['Tot Bwd Pkts']] or 0))
                syn = int(float(row[idx['SYN Flag Cnt']] or 0))
            except ValueError:
                continue
            i2 = tf / (tf + tb + 1)
            i3 = 1 if (syn > 0 and pb == 0) else 0
            rows[lab].append((i2, i3))
    day = os.path.basename(f).split('_')[0]
    print(f"\n##### {day} #####")
    print(f"{'标签':<32}{'流数':>9} {'I2均值':>8} {'I2极端%':>9} {'单向SYN%':>9}")
    print('-'*70)
    for lab, rs in sorted(rows.items(), key=lambda x:-len(x[1])):
        i2s=[x[0] for x in rs]; i3s=[x[1] for x in rs]
        ext=sum(1 for v in i2s if v>0.95 or v<0.05)/len(rs)*100
        print(f"{lab:<32}{len(rs):>9} {statistics.mean(i2s):>8.3f} {ext:>8.1f}% {sum(i3s)/len(rs)*100:>8.1f}%")
    # 朴素判据（I2极端 或 单向SYN）vs Benign
    benign = rows.get('Benign', [])
    if not benign: return
    print(f"  朴素判据(I2极端或单向SYN→攻击):")
    for lab, rs in rows.items():
        if lab == 'Benign': continue
        is_pos = lambda x: x[0]>0.95 or x[0]<0.05 or x[1]==1
        tp=sum(1 for x in rs if is_pos(x)); fn=len(rs)-tp
        fp=sum(1 for x in benign if is_pos(x)); tn=len(benign)-fp
        rec=tp/max(len(rs),1)*100; fpr=fp/max(tn+fp,1)*100
        print(f"    {lab[:30]:<30} 召回{rec:5.1f}% 误报{fpr:5.1f}%")

for f in FILES:
    if os.path.exists(f): analyze(f)
    else: print(f"缺失: {f}")
