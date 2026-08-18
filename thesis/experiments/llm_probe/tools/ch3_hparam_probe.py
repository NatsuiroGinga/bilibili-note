# -*- coding: utf-8 -*-
"""超参搜索的规模探针：只读 LSPR23 侧，估算各 L 的序列数、切分规模与步数预算。

不训练、不评价、不创建运行身份、不触碰 LSPR24（本文件内不出现任何 24 侧数组名）。
用途：在启动 24 配置搜索前，先把 n_seq(L)、训练/验证序列数与按 n_seq 缩放后的步数量出来，
避免「L=32 步数暴涨导致总时长失控」这类只能事后发现的问题。
"""
import time

import numpy as np

T0 = time.time()
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


e23 = np.load(f"{CACHE}/ent23.npy")
t23 = np.load(f"{CACHE}/t23_flow.npy")
E23 = np.load(f"{CACHE}/E23.npy")
T23 = np.load(f"{CACHE}/T23.npy")
log(f"逐流 {len(e23):,}  L=128 缓存序列 {len(E23):,}")

cnt = np.bincount(e23)
cnt = cnt[cnt > 0]
log(f"实体 {len(cnt):,}  单实体流数 中位={np.median(cnt):.0f} 均值={cnt.mean():.1f} 最大={cnt.max():,}")

# 与 ch3_2x2_fairsel.py 第 80-84 行同一切分代码：val_ent 只依赖唯一实体集合与 RandomState(42)，
# 因此与 L 无关；随 L 变的只有每个 L 的序列数与时间尾部分位点。
SEED, VAL_FRAC, TIME_TAIL = 42, 0.10, 0.15
rs = np.random.RandomState(SEED)
uent = np.unique(E23)
perm = rs.permutation(len(uent))
val_ent = set(uent[perm[:max(1, int(len(uent) * VAL_FRAC))]].tolist())
log(f"验证实体 {len(val_ent):,} / 全部实体 {len(uent):,}（与 L 无关）")

order = np.lexsort((t23, e23))
iv = e23[order]
bnd = np.flatnonzero(np.r_[True, iv[1:] != iv[:-1], True])
seg_len = np.diff(bnd)

print(f"\n{'L':>5}{'n_seq':>10}{'训练序列':>10}{'验证序列':>10}{'填充率':>9}"
      f"{'步数∝n_tr':>11}{'epoch数':>8}{'真实流visits':>15}", flush=True)
BASE = {}
for Lu in (32, 64, 128):
    n_seq = int(np.ceil(seg_len / Lu).sum())
    # 每个 chunk 的实体与起始时间：chunk 内按 (ent, ts) 排序，首元素即代表
    starts = np.concatenate([bnd[i] + np.arange(0, seg_len[i], Lu) for i in range(len(seg_len))])
    assert len(starts) == n_seq
    first = order[starts]
    EL, TL = e23[first], t23[first]
    m_ent = np.isin(EL, list(val_ent))
    t_cut = np.quantile(TL, 1.0 - TIME_TAIL)
    m_time = TL >= t_cut
    n_tr = int((~(m_ent | m_time)).sum())
    n_val = int((m_ent & ~m_time).sum())
    fill = len(e23) / (n_seq * Lu)
    BASE[Lu] = (n_seq, n_tr, n_val, fill)

for Lu in (32, 64, 128):
    n_seq, n_tr, n_val, fill = BASE[Lu]
    steps = int(round(20000 * n_tr / BASE[128][1]))
    visits = steps * 64 * len(e23) / n_seq
    print(f"{Lu:>5}{n_seq:>10,}{n_tr:>10,}{n_val:>10,}{fill:>9.4f}"
          f"{steps:>11,}{steps/1000:>8.1f}{visits:>15,.0f}", flush=True)

tot = sum(int(round(20000 * BASE[L][1] / BASE[128][1])) for L in (32, 64, 128)) * 8
log(f"24 配置总步数 = {tot:,}（每 L 各 8 个配置）")
log("L=128 自检：n_seq 应为 271,815，训练 208,598，验证 22,444")
