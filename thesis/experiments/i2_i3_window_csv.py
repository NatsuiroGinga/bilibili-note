#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 v2：守恒不变量按时间窗聚合的可分性（改进 v1 的逐流朴素阈值）
动机：v1 逐流阈值弱（Benign 也有 35% 单向流，误报高）。攻击是突发——窗口内单向/极端流
      密度应骤增，与正常窗口可分。
方法：按 Timestamp 分 1 分钟窗口，每窗口算：极端I2流占比、单向SYN流占比、流总数；
      窗口含任一攻击流 → 标 attack。比较 attack vs benign 窗口的指标分布。
"""
import csv, collections, statistics, os
from datetime import datetime

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA = os.path.join(REPO, 'raw/datasets/CSE-CIC-IDS2018/Thursday-15-02-2018_TrafficForML_CICFlowMeter.csv')

def main():
    win = collections.defaultdict(lambda: {'n':0, 'extreme':0, 'oneway':0, 'atk':0})
    n = 0
    with open(DATA, newline='', encoding='utf-8', errors='replace') as fh:
        r = csv.reader(fh); hdr = next(r)
        idx = {c.strip(): i for i, c in enumerate(hdr)}
        for row in r:
            if len(row) < len(hdr): continue
            lab = row[idx['Label']].strip()
            if lab == 'Label': continue
            ts = row[idx['Timestamp']].strip()  # 02/15/2018 08:47:38
            try:
                t = datetime.strptime(ts, '%d/%m/%Y %H:%M:%S')
                wkey = t.replace(second=0)  # 1 分钟窗
            except ValueError:
                continue
            try:
                tf = int(float(row[idx['TotLen Fwd Pkts']] or 0))
                tb = int(float(row[idx['TotLen Bwd Pkts']] or 0))
                pb = int(float(row[idx['Tot Bwd Pkts']] or 0))
                syn = int(float(row[idx['SYN Flag Cnt']] or 0))
            except ValueError:
                continue
            i2 = tf / (tf + tb + 1)
            w = win[wkey]
            w['n'] += 1
            if i2 > 0.95 or i2 < 0.05: w['extreme'] += 1
            if syn > 0 and pb == 0: w['oneway'] += 1
            if lab != 'Benign': w['atk'] += 1
            n += 1

    atk_w = [v for v in win.values() if v['atk'] > 0]
    ben_w = [v for v in win.values() if v['atk'] == 0]
    print(f"总流数 {n} | 窗口数 {len(win)} | 攻击窗口 {len(atk_w)} | 正常窗口 {len(ben_w)}")

    def stats(ws, key):
        if not ws: return (0,0,0)
        vals = [v[key]/max(v['n'],1) for v in ws] if key in ('extreme','oneway') else [v[key] for v in ws]
        return (statistics.mean(vals), statistics.pstdev(vals), max(vals))

    print(f"\n{'指标':<22}{'攻击窗口均值':>12}{'正常窗口均值':>14}{'攻击max':>10}")
    print('-'*60)
    for key,label in [('extreme','极端I2流占比'),('oneway','单向SYN流占比'),('n','窗口流总数')]:
        am,asx,amx = stats(atk_w,key); bm,bsx,bmx = stats(ben_w,key)
        if key in ('extreme','oneway'):
            am*=100; bm*=100; amx*=100
            print(f"{label:<22}{am:>11.1f}%{bm:>13.1f}%{amx:>9.1f}%")
        else:
            print(f"{label:<22}{am:>12.0f}{bm:>14.0f}{amx:>10.0f}")

    # 窗口级可分性：用单向SYN流占比 阈值判攻击窗口
    print("\n=== 窗口级判据（单向SYN流占比 > θ → 攻击窗口）===")
    oneway_atk = [v['oneway']/max(v['n'],1) for v in atk_w]
    oneway_ben = [v['oneway']/max(v['n'],1) for v in ben_w]
    best=None
    for theta_x10 in range(0,101,5):
        theta=theta_x10/1000
        tp=sum(1 for v in oneway_atk if v>theta); fn=len(oneway_atk)-tp
        fp=sum(1 for v in oneway_ben if v>theta); tn=len(oneway_ben)-fp
        if tp+fp==0: continue
        f1=2*tp/(2*tp+fn+fp)*100 if (2*tp+fn+fp) else 0
        if best is None or f1>best[0]: best=(f1,theta,tp,fn,fp,tn)
    f1,theta,tp,fn,fp,tn=best
    print(f"最优θ={theta:.3f}: 窗口召回{tp/max(tp+fn,1)*100:.1f}% 窗口误报{fp/max(tn+fp,1)*100:.1f}% F1={f1:.1f}% (TP{tp} FN{fn} FP{fp} TN{tn})")

if __name__ == '__main__':
    main()
