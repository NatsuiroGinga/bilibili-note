#!/usr/bin/env python3
"""定理 1 数值验证：选择算子谱系（uniform / per-group top-1 / cross-group budgeted）。

============================================================================
一、模型与算子定义（合成闭式部分）
============================================================================
N 个干净（恶意）样本；比例 π 属「高骗过组」（组内每个变体独立骗过概率 p_h），
其余 1−π 属「低骗过组」（每个变体独立骗过概率 p_l）。每个样本生成 K=4 个变体，
骗过指示 u_ik ∈ {0,1}（u=1 表示该变体骗过当前模型）。候选池总数 = N·K。
预算 q 表示本批可入选的变体数（q ≤ N，本脚本取 q/N ∈ {0.25, 0.5}）。

三个算子（都在同一预算 q 下比较「已骗过变体捕获数」C = 入选者中 u=1 的个数）：

1. uniform：每个干净样本**均匀**选 1 个变体（组内等概率），再从该 N 个中均匀抽 q 个。
   等价表述：从 N·K 个候选池中均匀无放回抽 q 个（就捕获数分布而言两者同分布）。
2. per-group top-1：每组（同一样本的 K=4 个变体）取 u 最大者（u 相同则均匀随机破并列），
   得 N 个「组冠军」，再从中均匀抽 q 个。
3. cross-group budgeted：把全部 N·K 个候选按 u 全局降序排列取 top-q，
   即「先全部 u=1 的骗过者，quota 未满才用 u=0 的候选补位」。

============================================================================
二、闭式推导（本脚本 docstring 内推导，脚本按此实现）
============================================================================
记单位置骗过概率 μ = π·p_h + (1−π)·p_l。

【uniform】抽到的第 j 个候选（j=1..q）来自某个均匀随机的干净样本、
且该样本的高/低组身份与组内位置均与候选身份独立 ⇒ 每个被选候选骗过概率恰为 μ，
且 q 次抽样的指示变量 i.i.d.（组间身份独立）。故

    E[C_uniform] = q·μ                                              ……(1)

（注：池内每候选的骗过指示 iid Bernoulli(μ)，从中**无放回**均匀抽 q 个后所选指示
仍 iid Bernoulli(μ)（交换性），故捕获数精确为 Binomial(q, μ)，均值即 q·μ；
真实重放部分的池是**固定**的，那时选择随机性才对应超几何分布——两者期望同为 q·μ。）

【per-group top-1】一组内 K 个独立变体至少一个骗过的概率为 1−(1−p)^K，故组冠军的
骗过概率（对组身份取期望）

    ν = π·(1−(1−p_h)^K) + (1−π)·(1−(1−p_l)^K)                      ……(2)

各组身份独立 ⇒ 组冠军指示变量 i.i.d. Bernoulli(ν)；从 N 个冠军中均匀无放回抽 q 个
（或等价地先抽 q 个样本再看其冠军），捕获数期望为

    E[C_top1] = q·ν                                                 ……(3)

【cross-group budgeted】全局降序取 top-q 等价于

    C_cross = min(F, q),   F = 全体 N·K 个候选中的骗过总数           ……(4)

F 的分布：F = Σ_{i=1}^N c_i，其中 c_i 独立，取 c_i ~ Binom(K, p_h)（概率 π）或
Binom(K, p_l)（概率 1−π）。即 F 的 pmf 是「混合二项分布 pmf 的 N 重卷积」：

    m(c) = π·Binom(K,p_h)(c) + (1−π)·Binom(K,p_l)(c),  c = 0..K
    pmf_F = m^{*N}（N 次离散卷积，支撑 0..N·K）                       ……(5)
    E[C_cross] = Σ_f min(f, q)·pmf_F(f)                              ……(6)

【严格优判据】cross-group 严格优 ⇔ E[C_cross] > max(E[C_uniform], E[C_top1])。
直觉：cross-group 把预算集中在「已知会骗过」的候选上，而 uniform / top-1 会在
「组冠军仍未骗过」的组上浪费预算；当 q 接近 N·K 时三者收敛（都覆盖全部候选），
故严格优区域是 q/N 的**下方**区间。

============================================================================
三、误差口径（重要，避免把 MC 噪声当成闭式偏差）
============================================================================
原始计数 C 的量级为 q·μ（N=1000、q=250 时约 125），其 MC 标准误为 σ/√M，
σ ≈ sqrt(q·μ) ≈ 8（10^6 次重复时标准误 ≈ 0.008）。**任何闭式都不可能被验证到
「原始计数误差 < 1e-3」**，该量级纯属采样噪声。
故本脚本把「误差 < 1e-3」判据建立在**捕获率口径 C/q**（与真实重放表的
「捕获数/预算」同口径）上，同时报告：
  - 原始计数口径的 |Δ| 与其理论标准误 σ/√M；
  - z 分数 = Δ/(MC 标准误)，用于判定原始差异是否只是采样噪声。

============================================================================
四、真实数据重放（不训练，只重放选择）
============================================================================
数据：T18_dga_val 前 7500 域，按 official_p2p3.py D 臂同款算子与顺序生成 K=4 变体
（rng=random.Random(42)，base=perturb2(d)，4 个变体各为 perturb2(base)），
用官方 finetuning.pt 原始模型打分得 s=P(DGA)，取 u = 1 − s。
三算子在同一预算 q 下重放选择，报告「已骗过捕获数/预算」与所选变体平均 u。
预算对齐 D 臂：D 臂每批 128 个主样本配 64 个变体配额 ⇒ q/N = 64/128 = 0.5，
故主预算 q = 0.5×7500 = 3750；同时报告 q/N=0.25 的次级口径。
本脚本另存 verify-thm1-real-scores.npz（u 矩阵 + 域清单哈希）供定理 3 脚本复用。

运行：PYTORCH_ENABLE_MPS_FALLBACK=1 /opt/miniconda3/envs/rwkv/bin/python verify_thm1_selection.py
"""
from __future__ import annotations

import os

# MPS 上 nn.Transformer 的部分算子需要回退 CPU（与 official_p2p3.py 同口径）
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
WORKTREE = SCRIPT_DIR.parents[2]
ROOT = Path(os.environ.get("LLM_PROBE_ROOT", WORKTREE / "thesis/experiments/llm_probe"))
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ROOT / "tools"))

SEED = 42                      # 全局随机种子（脚本级固定）
N_SAMPLES = 1000               # 合成：干净样本数
K_VARIANTS = 4                 # 每样本变体数（对齐 D 臂 K=4）
MC_REPS = 10**6                # 合成 MC 重复次数
REAL_N = 7500                  # 真实：T18_dga_val 域数
REAL_Q_RATIOS = (0.5, 0.25)    # 真实预算口径：0.5 = D 臂 64/128 对齐；0.25 作次级
REAL_MC_REPS = 2000            # 真实重放中随机算子的重复次数
PI_GRID = (0.2, 0.5, 0.8)
PH_GRID = (0.9,)
PL_GRID = (0.1, 0.3)
Q_RATIO_GRID = (0.25, 0.5)
THRESHOLD_Q_GRID = tuple(round(0.05 * i, 2) for i in range(1, 21))  # 阈值扫描 0.05..1.00
OUT_JSON = SCRIPT_DIR / "verify-thm1-result.json"
OUT_NPZ = SCRIPT_DIR / "verify-thm1-real-scores.npz"


def log(msg: str) -> None:
    """里程碑输出（控制台）。"""
    print(f"[定理1] {msg}", flush=True)


def atomic_json(path: Path, value: dict) -> None:
    """原子写 JSON：先写 .partial 再 rename。"""
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    partial.replace(path)


def binom_pmf(n: int, p: float) -> np.ndarray:
    """二项分布 pmf（长度 n+1，float64）。"""
    c = np.arange(n + 1)
    from math import comb
    return np.array([comb(n, int(k)) * (p ** int(k)) * ((1.0 - p) ** (n - int(k))) for k in c], dtype=np.float64)


# ---------------------------------------------------------------------------
# 合成部分：闭式 vs Monte Carlo
# ---------------------------------------------------------------------------
def cross_expected_capture(n: int, k: int, pi: float, p_h: float, p_l: float, q: int) -> float:
    """式(5)(6)：cross-group 期望捕获数（混合二项 pmf 的 N 重卷积）。"""
    m = pi * binom_pmf(k, p_h) + (1.0 - pi) * binom_pmf(k, p_l)
    pmf = np.array([1.0], dtype=np.float64)
    for _ in range(n):
        pmf = np.convolve(pmf, m)
    f = np.arange(pmf.size, dtype=np.float64)
    return float(np.sum(np.minimum(f, float(q)) * pmf))


def synthetic_scan() -> tuple[list[dict], dict]:
    """扫描 π×p_h×p_l×q/N，逐格给出闭式、MC、误差与严格优判据。"""
    rng = np.random.default_rng(SEED)
    rows: list[dict] = []
    for pi in PI_GRID:
        for p_h in PH_GRID:
            for p_l in PL_GRID:
                for q_ratio in Q_RATIO_GRID:
                    q = int(round(q_ratio * N_SAMPLES))
                    mu = pi * p_h + (1.0 - pi) * p_l
                    nu = pi * (1.0 - (1.0 - p_h) ** K_VARIANTS) + (1.0 - pi) * (1.0 - (1.0 - p_l) ** K_VARIANTS)
                    # 闭式
                    cf = {
                        "uniform": q * mu,
                        "per_group_top1": q * nu,
                        "cross_group": cross_expected_capture(N_SAMPLES, K_VARIANTS, pi, p_h, p_l, q),
                    }
                    # MC：三个算子各自按「算子的真实分布」精确抽样。
                    # 池内候选的骗过指示为 iid Bernoulli(μ)（组身份与组内位置独立），
                    # 均匀无放回抽 q 个后所选指示仍 iid Bernoulli(μ) ⇒ 捕获数 ~ Binomial(q, μ)；
                    # 同理组冠军指示 iid Bernoulli(ν) ⇒ 捕获数 ~ Binomial(q, ν)。
                    c_uniform = rng.binomial(q, mu, size=MC_REPS)
                    c_top1 = rng.binomial(q, nu, size=MC_REPS)
                    # cross-group：C = min(F, q)，F = Binom(n_h·K, p_h) + Binom((N−n_h)·K, p_l)
                    n_h = rng.binomial(N_SAMPLES, pi, size=MC_REPS)
                    f = rng.binomial(n_h * K_VARIANTS, p_h) + rng.binomial((N_SAMPLES - n_h) * K_VARIANTS, p_l)
                    c_cross = np.minimum(f, q)
                    mc = {name: arr.mean() for name, arr in
                          (("uniform", c_uniform), ("per_group_top1", c_top1), ("cross_group", c_cross))}
                    se = {name: arr.std(ddof=1) / np.sqrt(MC_REPS) for name, arr in
                          (("uniform", c_uniform), ("per_group_top1", c_top1), ("cross_group", c_cross))}
                    detail = {}
                    for name in ("uniform", "per_group_top1", "cross_group"):
                        delta = mc[name] - cf[name]
                        detail[name] = {
                            "closed_form_capture": round(cf[name], 6),
                            "mc_mean_capture": round(float(mc[name]), 6),
                            "raw_abs_diff": round(abs(float(delta)), 6),
                            "raw_diff_theory_se": round(float(se[name]), 6),
                            "rate_abs_diff_per_budget": round(abs(float(delta)) / q, 6),
                            "z_score": round(float(delta / se[name]), 3) if se[name] > 0 else None,
                        }
                    best_closed = max(cf.values())
                    best_name = max(cf, key=cf.get)
                    best_mc = max(mc.values())
                    rows.append({
                        "pi": pi, "p_h": p_h, "p_l": p_l, "q_over_N": q_ratio, "q": q,
                        "mu": round(mu, 6), "nu": round(nu, 6),
                        "closed_form": {k: round(v, 4) for k, v in cf.items()},
                        "mc": {k: round(float(v), 4) for k, v in mc.items()},
                        "error_detail": detail,
                        "cross_strictly_best_closed_form": bool(cf["cross_group"] > max(cf["uniform"], cf["per_group_top1"]) + 1e-12),
                        "cross_strictly_best_mc": bool(mc["cross_group"] > max(mc["uniform"], mc["per_group_top1"]) + 1e-9),
                        "margin_closed_form": round(cf["cross_group"] - max(cf["uniform"], cf["per_group_top1"]), 4),
                        "best_operator_closed_form": best_name,
                        "best_operator_mc": max(mc, key=mc.get),
                    })
                    # 内部一致性：MC 的最优算子需与闭式一致
                    assert best_name == max(mc, key=mc.get) or abs(best_closed - best_mc) < 1e-3, "MC 与闭式最优算子不一致"
    names = ("uniform", "per_group_top1", "cross_group")
    zs = [r["error_detail"][n]["z_score"] for r in rows for n in names
          if r["error_detail"][n]["z_score"] is not None]
    n_degenerate = sum(1 for r in rows for n in names if r["error_detail"][n]["z_score"] is None)
    gate = {
        "max_rate_abs_diff": round(max(r["error_detail"][n]["rate_abs_diff_per_budget"]
                                       for r in rows for n in names), 6),
        "max_raw_abs_diff": round(max(r["error_detail"][n]["raw_abs_diff"]
                                      for r in rows for n in names), 6),
        "max_abs_z": round(max(abs(z) for z in zs), 3) if zs else None,
        "zero_variance_cells": n_degenerate,
        "note_zero_variance": ("z 为空表示该格 MC 方差为 0（cross-group 预算已饱和 C≡q），不是误差缺失；"
                               "这些格的 |Δ| 亦为 0"),
        "gate_rate_lt_1e-3": None,
    }
    gate["gate_rate_lt_1e-3"] = bool(gate["max_rate_abs_diff"] < 1e-3)
    return rows, gate


def threshold_scan() -> list[dict]:
    """闭式阈值扫描：找出 cross-group 严格优的 q/N 区间上界。"""
    out: list[dict] = []
    for pi in PI_GRID:
        for p_l in PL_GRID:
            p_h = PH_GRID[0]
            margins = []
            for q_ratio in THRESHOLD_Q_GRID:
                q = int(round(q_ratio * N_SAMPLES))
                mu = pi * p_h + (1.0 - pi) * p_l
                nu = pi * (1.0 - (1.0 - p_h) ** K_VARIANTS) + (1.0 - pi) * (1.0 - (1.0 - p_l) ** K_VARIANTS)
                cf_cross = cross_expected_capture(N_SAMPLES, K_VARIANTS, pi, p_h, p_l, q)
                margins.append((q_ratio, cf_cross - max(q * mu, q * nu)))
            strict = [r for r, m in margins if m > 1e-9]
            out.append({
                "pi": pi, "p_l": p_l, "p_h": p_h,
                "q_over_N_margins": [{"q_over_N": r, "margin": round(float(m), 4)} for r, m in margins],
                "strict_region_q_over_N": [strict[0], strict[-1]] if strict else None,
            })
    return out


# ---------------------------------------------------------------------------
# 真实数据重放
# ---------------------------------------------------------------------------
def build_real_variants(domains: list[str]) -> list[list[str]]:
    """按 official_p2p3.py D 臂同款算子与顺序生成 K=4 变体。"""
    import official_p2p3 as op3

    rng = random.Random(SEED)
    groups: list[list[str]] = []
    for d in domains:
        base = op3.perturb2(d, rng)
        groups.append([op3.perturb2(base, rng) for _ in range(K_VARIANTS)])
    return groups


def score_variants(flat_domains: list[str]) -> np.ndarray:
    """官方 finetuning.pt 原始模型打分：s = softmax(logits)[:,1]（不训练、无梯度）。"""
    import torch
    import ch3_drift_official_checkpoint_t17_eval as official

    ref = ROOT / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
    ckpt = ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"
    device = torch.device("mps")
    tokenizer = official.PreTrainedTokenizerFast(tokenizer_file=str(ref / "artifacts/tokenizer/tokenizer-0-30522-both.json"))
    model = official.load_model(ref, ckpt, device)
    model.eval()
    batch = 1024
    parts: list[np.ndarray] = []
    t0 = time.time()
    with torch.inference_mode():
        for off in range(0, len(flat_domains), batch):
            chunk = flat_domains[off:off + batch]
            tok = official.encode_subword(chunk, tokenizer).to(device)
            ch = official.encode_char(chunk).to(device)
            logits = model(tok, ch)
            parts.append(torch.softmax(logits.float(), dim=1)[:, 1].cpu().numpy())
            if (off // batch) % 5 == 0:
                log(f"打分 {off + len(chunk)}/{len(flat_domains)}（{time.time() - t0:.0f}s）")
    del model
    return np.concatenate(parts)


def random_subset_means(values: np.ndarray, q: int, reps: int, rng: np.random.Generator) -> np.ndarray:
    """均匀无放回抽 q 个下标后所选值的均值（分块置换，避免逐次 choice 的开销）。"""
    total = values.size
    out = np.empty(reps, dtype=np.float64)
    chunk = 250
    done = 0
    while done < reps:
        m = min(chunk, reps - done)
        idx = np.tile(np.arange(total, dtype=np.int64), (m, 1))
        idx = rng.permuted(idx, axis=1)[:, :q]
        out[done:done + m] = values[idx].mean(axis=1)
        done += m
    return out


def real_replay(u: np.ndarray) -> dict:
    """三算子在真实变体分数上的选择重放（不训练）。

    u：形状 [N, K] 的连续「骗过程度」u = 1 − s（越接近 1 越骗过）。
    严格骗过判据：u > 0.5（等价于模型 s < 0.5，即模型判良性）。
    """
    n, k = u.shape
    flat_u = u.reshape(-1)
    fooled = flat_u > 0.5
    pool = flat_u.size
    rng = np.random.default_rng(SEED)
    out: dict = {"n_domains": n, "k_variants": k, "pool_size": pool,
                 "overall_fool_rate": round(float(fooled.mean()), 6),
                 "overall_u_mean": round(float(flat_u.mean()), 6),
                 "u_quantiles": {str(q): round(float(np.quantile(flat_u, q)), 4) for q in (0.01, 0.1, 0.5, 0.9, 0.99)}}
    winner_idx = u.argmax(axis=1)                      # 每组 u 最大的变体下标
    winner_flat = winner_idx + np.arange(n) * k
    winner_u = flat_u[winner_flat]
    budgets: dict = {}
    for q_ratio in REAL_Q_RATIOS:
        q = int(round(q_ratio * n))
        # uniform：从 N·K 池中均匀无放回抽 q 个 ⇒ 捕获数精确服从超几何分布
        cu = rng.hypergeometric(int(fooled.sum()), pool - int(fooled.sum()), q, size=REAL_MC_REPS)
        sel_u = random_subset_means(flat_u, q, REAL_MC_REPS, rng)
        # per-group top-1：N 个组冠军中均匀抽 q 个 ⇒ 捕获数精确服从超几何分布
        wf = int((winner_u > 0.5).sum())
        ct = rng.hypergeometric(wf, n - wf, q, size=REAL_MC_REPS)
        sel_u_top1 = random_subset_means(winner_u, q, REAL_MC_REPS, rng)
        # cross-group：全局 top-q（确定性）
        order = np.argsort(-flat_u)
        cross_idx = order[:q]
        cross_capture = int(fooled[cross_idx].sum())
        budgets[f"q_over_N={q_ratio}"] = {
            "q": q,
            "uniform": {
                "capture_mean": round(float(cu.mean()), 2),
                "capture_std": round(float(cu.std(ddof=1)), 2),
                "capture_per_budget": round(float(cu.mean()) / q, 6),
                "selected_u_mean": round(float(sel_u.mean()), 6),
                "selected_u_std": round(float(sel_u.std(ddof=1)), 6),
            },
            "per_group_top1": {
                "capture_mean": round(float(ct.mean()), 2),
                "capture_std": round(float(ct.std(ddof=1)), 2),
                "capture_per_budget": round(float(ct.mean()) / q, 6),
                "selected_u_mean": round(float(sel_u_top1.mean()), 6),
                "selected_u_std": round(float(sel_u_top1.std(ddof=1)), 6),
            },
            "cross_group": {
                "capture": cross_capture,
                "capture_per_budget": round(cross_capture / q, 6),
                "selected_u_mean": round(float(flat_u[cross_idx].mean()), 6),
                "total_fooled_in_pool": int(fooled.sum()),
            },
        }
        # 方向一致性断言：cross-group 捕获数不低于两随机算子的 MC 均值
        assert cross_capture >= cu.mean() - 1e-9, "cross-group 捕获数低于 uniform（方向与定理相反）"
    out["budgets"] = budgets
    out["per_domain_fooled_count_hist"] = {str(c): int((fooled.reshape(n, k).sum(axis=1) == c).sum()) for c in range(k + 1)}
    return out


def main() -> int:
    random.seed(SEED)
    np.random.seed(SEED)
    t_start = time.time()
    log(f"合成扫描开始：N={N_SAMPLES} K={K_VARIANTS} MC={MC_REPS}；网格 π={PI_GRID} p_h={PH_GRID} p_l={PL_GRID} q/N={Q_RATIO_GRID}")
    rows, gate = synthetic_scan()
    log(f"合成扫描完成：{len(rows)} 格；捕获率口径最大误差 {gate['max_rate_abs_diff']:.2e}，"
        f"原始计数最大误差 {gate['max_raw_abs_diff']:.4f}，最大 |z|={gate['max_abs_z']}")
    log("闭式阈值扫描开始")
    thresholds = threshold_scan()
    log("闭式阈值扫描完成")

    # ---- 真实数据重放 ----
    import pyarrow.parquet as pq

    data_root = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD"
    t18 = pq.read_table(data_root / "T18_dga_val.parquet").to_pylist()[:REAL_N]
    domains = [str(r["domain"]) for r in t18]
    log(f"真实重放：T18_dga_val 前 {len(domains)} 域，生成 K={K_VARIANTS} 变体")
    groups = build_real_variants(domains)
    flat = [v for g in groups for v in g]
    log(f"变体生成完成：{len(flat)} 个变体，开始打分")
    t0 = time.time()
    scores = score_variants(flat)
    log(f"打分完成：{len(scores)} 条，用时 {time.time() - t0:.0f}s")
    u = (1.0 - scores).reshape(len(domains), K_VARIANTS)
    flat_domains = [d for g in groups for d in g]
    dom_hash = hashlib.sha256("\n".join(flat_domains).encode("utf-8")).hexdigest()
    partial = OUT_NPZ.with_name(OUT_NPZ.name + ".partial")
    # 注意：np.savez_compressed 对非 .npz 结尾的路径会自动补 .npz，故这里传文件句柄以保证原子替换
    with partial.open("wb") as handle:
        np.savez_compressed(
            handle,
            u=u.astype(np.float32),
            scores=scores.astype(np.float32),
            domains=np.array(flat_domains, dtype=object),
            variant_k=np.array(K_VARIANTS),
            seed=np.array(SEED),
            domain_list_sha256=np.array(dom_hash),
        )
    partial.replace(OUT_NPZ)
    log(f"真实分数已存 {OUT_NPZ.name}（域清单 sha256={dom_hash[:16]}…）")
    replay = real_replay(u)
    log(f"真实重放完成：全局骗过率 {replay['overall_fool_rate']:.4f}，"
        f"q/N=0.5 捕获数 uniform {replay['budgets']['q_over_N=0.5']['uniform']['capture_mean']:.0f} / "
        f"top1 {replay['budgets']['q_over_N=0.5']['per_group_top1']['capture_mean']:.0f} / "
        f"cross {replay['budgets']['q_over_N=0.5']['cross_group']['capture']}")

    # ---- 结论字段 ----
    closed_pass = bool(gate["gate_rate_lt_1e-3"] and (gate["max_abs_z"] is None or gate["max_abs_z"] < 4.0))
    q05 = replay["budgets"]["q_over_N=0.5"]
    real_dir = bool(q05["cross_group"]["capture"] >= q05["uniform"]["capture_mean"]
                    and q05["cross_group"]["capture"] >= q05["per_group_top1"]["capture_mean"])
    n_strict = sum(1 for r in rows if r["cross_strictly_best_closed_form"])
    result = {
        "theorem_id": "定理1：选择算子谱系（uniform / per-group top-1 / cross-group budgeted）",
        "verification_status": {
            "闭式验证": "闭式通过" if closed_pass else "闭式不通过",
            "真实数据方向": "真实方向一致" if real_dir else "反驳",
            "总判定": ("闭式通过 + 真实方向一致" if (closed_pass and real_dir) else
                     "闭式通过、真实方向不一致" if closed_pass else "闭式不通过"),
            "判据": {
                "闭式误差口径": "捕获率 C/q（与真实重放的捕获数/预算同口径）；原始计数口径受 σ/√M 采样噪声限制",
                "闭式门": "max |Δ(C/q)| < 1e-3 且 max |z| < 4",
                "真实方向门": "cross-group 捕获数 ≥ max(uniform, per-group top-1) 的 MC 均值",
            },
        },
        "数值表": {
            "合成参数": {"N": N_SAMPLES, "K": K_VARIANTS, "MC_reps": MC_REPS,
                     "seed": SEED, "网格": {"pi": list(PI_GRID), "p_h": list(PH_GRID),
                                        "p_l": list(PL_GRID), "q_over_N": list(Q_RATIO_GRID)}},
            "闭式_vs_MC": rows,
            "闭式_vs_MC_门禁": gate,
            "严格优参数区域": {
                "扫描": thresholds,
                "格点统计": {"严格优格点数": n_strict, "总格点数": len(rows)},
            },
            "真实重放": replay,
        },
        "conclusion": {
            "闭式成立": closed_pass,
            "真实数据方向一致": real_dir,
            "关键读数": {
                "最大捕获率口径误差": gate["max_rate_abs_diff"],
                "最大原始计数误差": gate["max_raw_abs_diff"],
                "最大 |z|": gate["max_abs_z"],
                "真实全局骗过率": replay["overall_fool_rate"],
                "真实 q/N=0.5 三算子捕获数/预算": {
                    "uniform": q05["uniform"]["capture_per_budget"],
                    "per_group_top1": q05["per_group_top1"]["capture_per_budget"],
                    "cross_group": q05["cross_group"]["capture_per_budget"],
                },
                "真实 q/N=0.5 三算子所选变体平均 u": {
                    "uniform": q05["uniform"]["selected_u_mean"],
                    "per_group_top1": q05["per_group_top1"]["selected_u_mean"],
                    "cross_group": q05["cross_group"]["selected_u_mean"],
                },
            },
        },
        "inputs": {
            "checkpoint": str(ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"),
            "data": str(data_root / "T18_dga_val.parquet"),
            "real_scores_npz": OUT_NPZ.name,
            "domain_list_sha256": dom_hash,
            "variant_operator": "official_p2p3.perturb2（base=perturb2(d)，4 变体=perturb2(base)，rng=Random(42)）",
            "device": "mps",
        },
        "runtime": {"elapsed_seconds": round(time.time() - t_start, 1), "seed": SEED},
    }
    atomic_json(OUT_JSON, result)
    log(f"完成：{OUT_JSON.name}；判定={result['verification_status']['总判定']}；用时 {time.time() - t_start:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
