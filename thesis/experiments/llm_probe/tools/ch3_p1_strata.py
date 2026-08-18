# -*- coding: utf-8 -*-
"""P1 第 1 步：在 LSPR23 实体不相交验证集上统计实体流数分布，确认难分层是否可用。

难分层按**结构先验**定义，不看任何性能数字，也不接触 LSPR24：
  小实体 n<=2 —— 因果前缀均值在 t=1 时退化为 ctx=h_1，机制一不提供额外信息
  大实体 n>100 —— max 与 Lp 的顺序统计量随组内样本数膨胀

这样定义避免了「用 LSPR24 分箱结论反过来设计 LSPR23 验证指标」这一泄漏路径。

本脚本只回答：这两箱在验证集上各有多少实体、多少正例实体，够不够稳定地算 AP。
若某箱正例实体数过少（少于 20），该箱 AP 方差过大，不能作为选择信号。

划分构造逐字照抄 tools/ch3_2x2_fairsel.py 第 79-94 行（其本身照抄 select_signal.py）。
纯 CPU，不训练、不推理、不创建 SwanLab 运行身份。
"""
import json
import os

import numpy as np

R = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics"
CACHE = f"{R}/dijk-repro/cache"
OUT = f"{R}/ch3-p1-strata"
os.makedirs(OUT, exist_ok=True)
VAL_FRAC, TIME_TAIL = 0.10, 0.15          # 与既有脚本一致
SEED = 42

y23 = np.load(f"{CACHE}/y23.npy")
ent23 = np.load(f"{CACHE}/ent23.npy")       # 逐流实体 id
E23 = np.load(f"{CACHE}/E23.npy")           # 逐序列实体 id
T23 = np.load(f"{CACHE}/T23.npy")           # 逐序列起始时间
I23 = np.load(f"{CACHE}/I23.npy")           # 序列 -> 流索引
M23 = np.load(f"{CACHE}/M23.npy")
print(f"LSPR23 流 {len(y23):,}  序列 {len(E23):,}  逐流实体 id 长度 {len(ent23):,}", flush=True)

# ---- 划分：照抄 ch3_2x2_fairsel.py 第 79-94 行 ----
rs = np.random.RandomState(SEED)
uent = np.unique(E23)
perm = rs.permutation(len(uent))
val_ent = set(uent[perm[:max(1, int(len(uent) * VAL_FRAC))]].tolist())
m_ent = np.fromiter((e in val_ent for e in E23), bool, len(E23))
t_cut = np.quantile(T23, 1.0 - TIME_TAIL)
m_time = T23 >= t_cut
tr_mask = ~(m_ent | m_time)
tr_idx = np.flatnonzero(tr_mask)
val_idx = np.flatnonzero(m_ent & ~m_time)
print(f"LSPR23 实体 {len(uent):,} | 训练序列 {len(tr_idx):,} | 实体不相交验证 {len(val_idx):,}", flush=True)
assert len(uent) == 150680, f"实体数自检失败：{len(uent)}"
assert len(tr_idx) == 208598, f"训练序列数自检失败：{len(tr_idx)}"
assert len(val_idx) == 22444, f"验证序列数自检失败：{len(val_idx)}，应为 22444"

# ---- 验证集上的实体：流数与标签 ----
# 验证集的「实体」以序列所属实体为准；其流数按该实体在验证序列内实际覆盖的有效流计
vseq = val_idx
vent_of_seq = E23[vseq]
flat_idx = I23[vseq].reshape(-1)
flat_msk = M23[vseq].reshape(-1) > 0
flat_ent = np.repeat(vent_of_seq, I23.shape[1])[flat_msk]
flat_y = y23[flat_idx[flat_msk]]

uv, inv = np.unique(flat_ent, return_inverse=True)
NV = len(uv)
cnt = np.bincount(inv, minlength=NV).astype(np.int64)
lab = np.zeros(NV, np.float32); np.maximum.at(lab, inv, flat_y)
print(f"验证集实体 {NV:,}  正例实体 {int(lab.sum()):,}  先验 {lab.mean():.6f}", flush=True)
print(f"流数：中位 {np.median(cnt):.0f}  均值 {cnt.mean():.1f}  最大 {cnt.max():,}", flush=True)

BINS = [("n<=2 小实体（前缀均值退化）", cnt <= 2),
        ("3<=n<=10", (cnt >= 3) & (cnt <= 10)),
        ("11<=n<=100", (cnt >= 11) & (cnt <= 100)),
        ("n>100 大实体（顺序统计量膨胀）", cnt > 100)]

W = 92
print("\n" + "=" * W)
print("LSPR23 实体不相交验证集的实体流数分箱（难分层按结构先验定义，不看性能数字）")
print(f"{'分箱':<34}{'实体数':>10}{'占比':>9}{'正例实体':>10}{'箱内先验':>11}{'可算 AP':>10}")
ROWS = []
for name, m in BINS:
    n_e = int(m.sum()); n_p = int(lab[m].sum())
    ok = "可" if n_p >= 20 else ("勉强" if n_p >= 5 else "不可")
    ROWS.append({"bin": name, "n_entity": n_e, "n_pos": n_p,
                 "frac": n_e / NV, "prior": float(lab[m].mean()) if n_e else 0.0, "usable": ok})
    print(f"{name:<34}{n_e:>10,}{n_e/NV:>9.2%}{n_p:>10,}"
          f"{(lab[m].mean() if n_e else 0):>11.6f}{ok:>10}")

hard = (cnt <= 2) | (cnt > 100)
n_h, p_h = int(hard.sum()), int(lab[hard].sum())
print("-" * W)
print(f"难分层合并（n<=2 或 n>100）：实体 {n_h:,}（{n_h/NV:.2%}）  正例实体 {p_h:,}  "
      f"先验 {lab[hard].mean():.6f}")
print(f"其余（3<=n<=100）：实体 {NV-n_h:,}  正例实体 {int(lab.sum())-p_h:,}")

verdict = ("难分层正例实体 >= 20，可作为选择信号，P1 第 2 步可继续"
           if p_h >= 20 else
           "难分层正例实体过少，箱内 AP 方差过大，不能作为选择信号，P1 判死")
print(f"\n事前判据（难分层正例实体 >= 20）→ {verdict}")
print("=" * W)

json.dump({"val_seq": int(len(val_idx)), "val_entity": NV,
           "val_pos_entity": int(lab.sum()), "bins": ROWS,
           "hard_n_entity": n_h, "hard_n_pos": p_h, "verdict": verdict},
          open(f"{OUT}/p1_strata.json", "w"), ensure_ascii=False, indent=2)
print(f"结果已存 {OUT}/p1_strata.json")
