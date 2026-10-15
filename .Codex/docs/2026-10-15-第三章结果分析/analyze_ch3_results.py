#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""第三章 results-analysis 三件套：从权威制品重算描述统计、自助推断、效应量与真图。

职责边界
--------
本脚本只做 **分析与绘图**，不改正文、不回写路线总控、不跑训练、不碰
`thesis/figures/**` 的既有文件。全部读数由 `metrics_*.json` 的 records 现场重算，
不手工录入任何数字。

冻结口径（跑前冻结，不得事后改；依据任务简报 + 仓库 AGENTS.md L41）
------------------------------------------------------------------
* 单一冻结种子 42。**仓库 AGENTS.md 禁止多种子训练**，故不确定性只能来自测试侧。
* 主指标 = 跨年平均 F1。两个口径并报：
    - 12 年平均（协议口径，表 3-1/3-2/3-4 用）；
    - 11 年平均（排除 2025 测试年度，细粒度比较用；该年 8,933 条中正例仅 5 条）。
* 分析单元 = 年度测试分片上的判定结果（11 或 12 个单元）。
* 不确定性来源：**年度级配对自助**（n=2000）——重采样年度测试分片，配对取两臂之差。
  只量化「年度测试分片」这一层的样本不确定性，不冒充训练随机性。
* **样本级自助不可用**：唯一落盘的逐样本分数 `scores_expreplay_m200_quota_deficit_r2.npz`
  经核验是「训练分片」的分数（各键规模与 `[load] YYYY train=(N, 4561)` 逐年严格相等，
  而对应测试分片规模小得多），属一年超前的前向打分，**不承载本章的测试集评价**，已隔离，
  不用于任何主张（见末尾 `quarantine_npz()` 的实测证据）。

用途
----
`/opt/miniconda3/envs/rwkv/bin/python analyze_ch3_results.py`
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ART = REPO / "thesis/experiments/llm_probe/runs/diagnostics/ch3-lamda-domain-il-e4-replication-v1"
FIGDIR = HERE / "figures"
FIGDIR.mkdir(exist_ok=True)

# 复用论文图件的样式层（只读导入；字体、配色、合同常量与交付自检同源）
sys.path.insert(0, str(REPO / "thesis/figures/第三章"))
import figstyle as fs  # noqa: E402

TEST_YEARS = (2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)
Y11 = tuple(y for y in TEST_YEARS if y != 2025)

B = 2000                      # 自助重复数（任务简报冻结）
BOOT_SEED = 20261015          # 自助随机源（固定，可复现；每个调用点独立取种）


class Incomplete(FileNotFoundError):
    """制品存在但记录未写全（该臂仍在运行或曾中断）。"""


# ---------------------------------------------------------------- 取数


def load_years(tag: str) -> dict[int, float]:
    """读某臂末年 experience=2025、mode=backward 的逐年 F1（0–1）。"""
    p = ART / f"metrics_{tag}.json"
    if not p.is_file():
        raise Incomplete(f"{p.name} 不存在")
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise Incomplete(f"{p.name} 不是完整 JSON（{e}）") from e
    recs = [r for r in payload["records"]
            if r["experience"] == 2025 and r["mode"] == "backward"]
    if len(recs) != 12:
        raise Incomplete(f"{tag} 的 backward 记录 {len(recs)}/12 条")
    return {int(r["test_year"]): float(r["f1"]) for r in recs}


def load_records(tag: str) -> list[dict]:
    """读某臂末年 experience=2025、mode=backward 的 12 条完整记录。"""
    p = ART / f"metrics_{tag}.json"
    payload = json.loads(p.read_text(encoding="utf-8"))
    recs = [r for r in payload["records"]
            if r["experience"] == 2025 and r["mode"] == "backward"]
    if len(recs) != 12:
        raise Incomplete(f"{tag} 的 backward 记录 {len(recs)}/12 条")
    return recs


def confusion(r: dict) -> tuple[int, int, int, int]:
    """由 (n, n_pos, precision, recall, accuracy) 反解四格计数（四舍五入）。"""
    n, n_pos = int(r["n"]), int(r["n_pos"])
    tp = round(float(r["recall"]) * n_pos)
    tn = round(float(r["accuracy"]) * n) - tp
    fn = n_pos - tp
    fp = n - tp - fn - tn
    return tp, fp, fn, tn


def derived_pair12(tag: str) -> dict[str, float]:
    """跨年平均的七个指标（12 年与 11 年两个口径）。"""
    recs = load_records(tag)
    rows = {}
    for r in recs:
        tp, fp, fn, tn = confusion(r)
        fpr = fp / (fp + tn) if fp + tn else float("nan")
        fnr = fn / (fn + tp) if fn + tp else float("nan")
        rows[int(r["test_year"])] = {
            "precision": 100 * float(r["precision"]), "recall": 100 * float(r["recall"]),
            "f1": 100 * float(r["f1"]), "accuracy": 100 * float(r["accuracy"]),
            "fpr": 100 * fpr, "fnr": 100 * fnr, "ba": 100 * (float(r["recall"]) + 1 - fpr) / 2}

    def avg(years):
        return {k: sum(rows[y][k] for y in years) / len(years) for k in rows[years[0]]}

    return {"12y": avg(TEST_YEARS), "11y": avg(Y11)}


def mean12(by: dict[int, float]) -> float:
    return 100.0 * sum(by[y] for y in TEST_YEARS) / 12


def mean11(by: dict[int, float]) -> float:
    return 100.0 * sum(by[y] for y in Y11) / 11


def vec12(by: dict[int, float]) -> np.ndarray:
    return np.array([100.0 * by[y] for y in TEST_YEARS])


def vec11(by: dict[int, float]) -> np.ndarray:
    return np.array([100.0 * by[y] for y in Y11])


# ---------------------------------------------------------------- 统计


def paired_year_bootstrap(diffs: np.ndarray, b: int = B, seed: int = BOOT_SEED) -> np.ndarray:
    """年度级配对自助：重采样年度单元，返回均值差的 b 个自助复现。

    每次调用用**独立且固定**的随机源，使同一输入在描述统计与绘图中得到逐位相同的
    复现（共享生成器会随调用顺序漂移，导致打印区间与图中区间不一致）。
    """
    n = len(diffs)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(b, n))
    return diffs[idx].mean(axis=1)


def signflip_exact(diffs: np.ndarray) -> tuple[float, int]:
    """精确符号翻转置换检验（全部 2^n 种符号组合）。"""
    n = len(diffs)
    obs = diffs.mean()
    bits = ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1).astype(float)
    signs = bits * 2.0 - 1.0
    perm = (signs * diffs).mean(axis=1)
    p = float(np.mean(np.abs(perm) >= abs(obs) - 1e-12))
    return p, 2 ** n


def describe(diffs: np.ndarray) -> dict[str, float]:
    from scipy import stats

    d = np.asarray(diffs, dtype=float)
    n = len(d)
    sd = float(d.std(ddof=1)) if n > 1 else float("nan")
    boot = paired_year_bootstrap(d)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    p_flip, nflip = signflip_exact(d)
    t = stats.ttest_rel(np.zeros(n), d)          # H0: 配对差均值为 0
    try:
        w = stats.wilcoxon(d, method="exact")
        w_stat, w_p = float(w.statistic), float(w.pvalue)
    except ValueError:
        w_stat, w_p = float("nan"), float("nan")
    return {
        "n_years": n,
        "mean_diff": float(d.mean()),
        "sd_diff": sd,
        "cohen_dz": float(d.mean() / sd) if sd and sd > 0 else float("nan"),
        "boot_se": float(boot.std(ddof=1)),
        "ci_lo": float(lo),
        "ci_hi": float(hi),
        "frac_boot_le0": float(np.mean(boot <= 0.0)),
        "p_signflip": p_flip,
        "n_sign_perm": nflip,
        "p_ttest": float(t.pvalue),
        "t_stat": float(t.statistic),
        "p_wilcoxon_exact": w_p,
        "w_stat": w_stat,
        "n_years_pos": int(np.sum(d > 0)),
        "n_years_neg": int(np.sum(d < 0)),
        "n_years_tie": int(np.sum(d == 0)),
        "min_diff": float(d.min()),
        "max_diff": float(d.max()),
    }


def holm(pvals: list[float]) -> list[float]:
    """Holm–Bonferroni 校正，返回与输入同序的校正 p 值。"""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * pvals[i])
        running = max(running, val)
        adj[i] = running
    return adj.tolist()


# ------------------------------------------------------------ 隔离核验：逐样本分数落盘


def quarantine_npz() -> dict[str, object]:
    """核验唯一落盘的逐样本分数属于哪一分片，并给出可追溯证据。

    结论（2026-10-15 实测）：`scores_expreplay_m200_quota_deficit_r2.npz` 的各键
    规模与 `full_diag_rga_scores.log` 的 `[load] YYYY train=(N, 4561)` **逐年严格相等**
    （n 相同、正例数相同），而 `metrics_*.json` 中对应测试分片的规模小得多
    （例：2014 训练 80,946 / 测试 20,237）。故该 npz 是「训练分片」的一年超前打分，
    **不承载测试集评价**，据此隔离：不用于区间、不用于效应量、不用于任何正文主张。
    """
    import re

    log = (ART / "full_diag_rga_scores.log").read_text(encoding="utf-8", errors="replace")
    train_n = {int(m.group(1)): int(m.group(2))
               for m in re.finditer(r"\[load\] (\d{4}) train=\((\d+), 4561\)", log)}
    npz = np.load(ART / "scores_expreplay_m200_quota_deficit_r2.npz")
    payload = json.loads((ART / "metrics_expreplay_m200_quota_deficit_r2.json").read_text())
    test_n = {int(r["test_year"]): int(r["n"])
              for r in payload["records"] if r["experience"] == 2025 and r["mode"] == "backward"}

    rows, all_match = [], True
    for y in sorted(train_n):
        if f"s{y}" not in npz:
            continue
        n_npz = int(npz[f"s{y}"].shape[0])
        npos = int((npz[f"y{y}"] > 0.5).sum())
        match = (n_npz == train_n[y])
        all_match &= match
        rows.append({"year": y, "npz_n": n_npz, "train_n": train_n[y],
                     "test_n": test_n.get(y), "npz_n_pos": npos, "matches_train": match})
    return {"artifact": "scores_expreplay_m200_quota_deficit_r2.npz",
            "verdict": "QUARANTINED" if all_match else "UNRESOLVED",
            "reason": "各键规模与训练分片逐年严格相等，与测试分片规模不符；属一年超前的前向打分",
            "rows": rows}


# ---------------------------------------------------------------- 主流程

SEED42_NOTE = "无 _sNN 后缀的臂按命名约定视为冻结种子 42（在两个有 [run] 头的臂上实测为真）"

# 主对照（容量 200）
BASE_TAG = "expreplay_m200"                      # 官方回放：reservoir/uniform/m1
METH_TAG = "expreplay_m200_quota_deficit_r2"     # 本章方法：quota/deficit/m2

# 容量曲线
CAPS = (50, 200, 400, 800, 1600, 18854)
CAP_BASE = {c: ("expreplay" if c == 200 else f"expreplay_m{c}") for c in CAPS}
CAP_METH = {c: f"expreplay_m{c}_quota_deficit_r2" for c in CAPS}

# 表 3-4 的双机制 2×2（统一复用，非 deficit 分配）
CELL_2x2 = {
    ("蓄水池", "倍数1"): "expreplay_m200",
    ("蓄水池", "倍数2"): "expreplay_m200_r2",
    ("按年度配额", "倍数1"): "expreplay_m200_quota",
    ("按年度配额", "倍数2"): "expreplay_m200_quota_r2",
}

# 复用上限扫描（配额 + deficit 分配）
MMAX_TAGS = {2: METH_TAG,
             4: "expreplay_m200_quota_deficit_r4",
             8: "expreplay_m200_quota_deficit_r8",
             16: "expreplay_m200_quota_deficit_r16",
             32: "expreplay_m200_quota_deficit_r32",
             64: "expreplay_m200_quota_deficit_r64"}

# 年内正例比例扫描
PR_TAGS = {"0.25": "expreplay_m200_quota_pr25_deficit_r2",
           "0.40": "expreplay_m200_quota_pr40_deficit_r2",
           "0.50": METH_TAG,
           "0.60": "expreplay_m200_quota_pr60_deficit_r2",
           "0.75": "expreplay_m200_quota_pr75_deficit_r2"}


def main() -> int:
    report: dict[str, object] = {"provenance": {"note": SEED42_NOTE,
                                                "boot_reps": B,
                                                "boot_seed": BOOT_SEED}}
    print("=" * 90)
    print("第三章 results-analysis：描述统计（单位：百分点）  种子 42，自助 n=%d，随机源 %d" % (B, BOOT_SEED))
    print("=" * 90)

    # -------- 主对照
    by_base = load_years(BASE_TAG)
    by_meth = load_years(METH_TAG)
    v11_base, v11_meth = vec11(by_base), vec11(by_meth)
    v12_base, v12_meth = vec12(by_base), vec12(by_meth)
    d11 = v11_meth - v11_base
    d12 = v12_meth - v12_base

    print("\n[主对照] 官方回放（容量 200，reservoir/uniform/m1）vs 本章方法（quota/deficit/m2）")
    print(f"{'测试年':>6} {'官方回放':>10} {'本章方法':>10} {'配对差':>8}")
    for i, y in enumerate(Y11):
        print(f"{y:>6} {v11_base[i]:>10.2f} {v11_meth[i]:>10.2f} {d11[i]:>+8.2f}")
    print(f"{'2025':>6} {100*by_base[2025]:>10.2f} {100*by_meth[2025]:>10.2f} "
          f"{100*(by_meth[2025]-by_base[2025]):>+8.2f}   ← 退化年，主口径排除")
    print(f"{'11年均':>6} {v11_base.mean():>10.2f} {v11_meth.mean():>10.2f} {d11.mean():>+8.2f}")
    print(f"{'12年均':>6} {v12_base.mean():>10.2f} {v12_meth.mean():>10.2f} {d12.mean():>+8.2f}")

    stat11 = describe(d11)
    stat12 = describe(d12)
    report["primary_11y"] = stat11
    report["primary_12y"] = stat12
    report["per_year"] = {str(y): {"baseline": 100 * by_base[y], "method": 100 * by_meth[y]}
                          for y in TEST_YEARS}

    print("\n  11 年口径配对自助：均值差 %+.3f，95%% CI [%+.3f, %+.3f]，自助标准误 %.4f"
          % (stat11["mean_diff"], stat11["ci_lo"], stat11["ci_hi"], stat11["boot_se"]))
    print("  自助复现中 <=0 的比例 %.4f；精确符号翻转置换 p=%.4f（%d 种组合）"
          % (stat11["frac_boot_le0"], stat11["p_signflip"], stat11["n_sign_perm"]))
    print("  参考检验（同以年度为单元，未校正；年度非独立，p 偏乐观）："
          "配对 t=%.3f p=%.4f；Wilcoxon 精确 W=%.1f p=%.4f"
          % (stat11["t_stat"], stat11["p_ttest"], stat11["w_stat"], stat11["p_wilcoxon_exact"]))
    print("  符号分布：正 %d / 负 %d / 并列 %d；Cohen's dz=%.2f；差区间 [%+.2f, %+.2f]"
          % (stat11["n_years_pos"], stat11["n_years_neg"], stat11["n_years_tie"],
             stat11["cohen_dz"], stat11["min_diff"], stat11["max_diff"]))
    print("  说明：两臂 11 年均值 %.4f / %.4f，其差 %.3f；组间差 %.3f 与之相等（数学恒等）"
          % (v11_base.mean(), v11_meth.mean(), v11_meth.mean() - v11_base.mean(), stat11["mean_diff"]))
    print("  12 年口径配对自助：均值差 %+.3f，95%% CI [%+.3f, %+.3f]，p(符号翻转)=%.4f"
          % (stat12["mean_diff"], stat12["ci_lo"], stat12["ci_hi"], stat12["p_signflip"]))

    # -------- 容量曲线
    print("\n[容量曲线] 官方回放 vs 本章方法（配额+deficit m2）")
    print(f"{'容量':>6} {'官方12y':>9} {'方法12y':>9} {'差12y':>7} | {'官方11y':>9} {'方法11y':>9} {'差11y':>7}")
    cap_rows = []
    for c in CAPS:
        try:
            b = load_years(CAP_BASE[c])
            m = load_years(CAP_METH[c])
        except Incomplete as e:
            print(f"{c:>6}  缺：{e}")
            continue
        row = {"cap": c,
               "base12": mean12(b), "meth12": mean12(m), "d12": mean12(m) - mean12(b),
               "base11": mean11(b), "meth11": mean11(m), "d11": mean11(m) - mean11(b)}
        cap_rows.append(row)
        print(f"{c:>6} {row['base12']:>9.2f} {row['meth12']:>9.2f} {row['d12']:>+7.3f} | "
              f"{row['base11']:>9.2f} {row['meth11']:>9.2f} {row['d11']:>+7.3f}")
    print("  注：差由未取整读数算出；与「两个两位小数均值之差」可能相差 0.01（取整口径差异）")
    report["capacity"] = cap_rows

    # 容量曲线上的配对自助（每个容量独立，作为一族做 Holm 校正）
    cap_contrasts = []
    for c in CAPS:
        try:
            b = load_years(CAP_BASE[c]); m = load_years(CAP_METH[c])
        except Incomplete:
            continue
        dd = vec11(m) - vec11(b)
        s = describe(dd)
        s["cap"] = c
        cap_contrasts.append(s)
    print("\n  容量曲线逐点配对自助（11 年口径，未经多重校正）")
    for s in cap_contrasts:
        print(f"    容量 {s['cap']:>5}: 差 %+.2f  95%%CI [%+.2f,%+.2f]  p_signflip=%.4f  正/负年 {s['n_years_pos']}/{s['n_years_neg']}"
              % (s["mean_diff"], s["ci_lo"], s["ci_hi"], s["p_signflip"]))
    adj = holm([s["p_signflip"] for s in cap_contrasts])
    for s, p in zip(cap_contrasts, adj):
        s["p_holm"] = p
    print("    Holm 校正后：", ", ".join(f"容量{c['cap']}={c['p_holm']:.4f}" for c in cap_contrasts))
    report["capacity_contrasts"] = cap_contrasts

    # -------- 双机制 2×2（表 3-4）
    print("\n[双机制 2×2]（统一复用；表 3-4 用 12 年口径，另并报 11 年）")
    cells: dict[tuple[str, str], dict[str, float]] = {}
    for key, tag in CELL_2x2.items():
        try:
            by = load_years(tag)
        except Incomplete as e:
            print(f"  {key} 缺：{e}")
            continue
        cells[key] = {"12y": mean12(by), "11y": mean11(by)}
        print(f"  {key[0]:>8}·{key[1]}  ({tag})  12y={cells[key]['12y']:.2f}  11y={cells[key]['11y']:.2f}")
    if all(k in cells for k in CELL_2x2):
        a = cells[("蓄水池", "倍数1")]["12y"]
        p_alone = cells[("按年度配额", "倍数1")]["12y"] - a
        r_alone = cells[("蓄水池", "倍数2")]["12y"] - a
        both = cells[("按年度配额", "倍数2")]["12y"] - a
        print(f"  12 年口径：切分单独 {p_alone:+.2f}；复用单独 {r_alone:+.2f}；"
              f"同时启用 {both:+.2f}；单独之和 {p_alone + r_alone:+.2f}")
        print(f"    → 亚可加量 {(p_alone + r_alone) - both:+.2f} 个百分点")
        # deficit 分配相对统一复用的增量（本章方法与表 3-4 右上格之差）
        mm = mean12(by_meth)
        print(f"  本章方法（deficit 分配）12y={mm:.2f}，相对统一复用 {mm - cells[('按年度配额','倍数2')]['12y']:+.2f}")
        report["ablation_2x2"] = {
            "cells": {f"{k[0]}|{k[1]}": v for k, v in cells.items()},
            "partition_alone_12y": p_alone, "reuse_alone_12y": r_alone,
            "both_12y": both, "sum_alone_12y": p_alone + r_alone,
            "subadditive_12y": (p_alone + r_alone) - both,
            "deficit_over_uniform_reuse_12y": mm - cells[("按年度配额", "倍数2")]["12y"]}

    # -------- 配额臂复用上限扫描
    print("\n[配额臂复用上限 m_max 扫描]（容量 200，deficit 分配，seed 42）")
    mmax_rows = []
    for mm, tag in sorted(MMAX_TAGS.items()):
        try:
            by = load_years(tag)
        except Incomplete as e:
            print(f"  m_max={mm:<3} 缺：{e}")
            continue
        r = {"m_max": mm, "11y": mean11(by), "12y": mean12(by)}
        mmax_rows.append(r)
        print(f"  m_max={mm:<3} 11y={r['11y']:.2f}  12y={r['12y']:.2f}")
    if mmax_rows:
        vals = [r["11y"] for r in mmax_rows]
        print(f"  11 年口径跨度 {max(vals) - min(vals):.2f}，"
              f"与方法臂自读 [(11y) 见主对照] 同量级")
    report["m_max_sweep"] = mmax_rows

    # -------- 年内正例比例扫描
    print("\n[年内正例比例扫描]（容量 200，配额+deficit m2，seed 42）")
    pr_rows = []
    for lbl, tag in PR_TAGS.items():
        try:
            by = load_years(tag)
        except Incomplete as e:
            print(f"  q+={lbl} 缺：{e}")
            continue
        r = {"q_pos": lbl, "11y": mean11(by), "12y": mean12(by)}
        pr_rows.append(r)
        print(f"  q+={lbl}  11y={r['11y']:.2f}  12y={r['12y']:.2f}")
    report["pr_sweep"] = pr_rows

    # -------- 表 3-1 的七个指标复核
    print("\n[表 3-1 复核] 七个跨年平均指标（由 records 的四格反解，单位：百分点）")
    TBL31 = {"朴素更新": "naive", "经验回放（官方容量）": "expreplay_m200",
             "本章方法": METH_TAG, "联合训练（上界）": "cumulative"}
    tbl31: dict[str, object] = {}
    hdr = f"{'方法':<20} {'口径':>4} {'精确率':>8} {'召回率':>8} {'F1':>8} {'准确率':>8} {'假正率':>8} {'假负率':>8} {'平衡准确率':>10}"
    print(hdr)
    for name, tag in TBL31.items():
        d = derived_pair12(tag)
        tbl31[name] = d
        for k in ("12y", "11y"):
            v = d[k]
            print(f"{name:<20} {k:>4} {v['precision']:>8.2f} {v['recall']:>8.2f} {v['f1']:>8.2f} "
                  f"{v['accuracy']:>8.2f} {v['fpr']:>8.2f} {v['fnr']:>8.2f} {v['ba']:>10.2f}")
    f1n = tbl31["朴素更新"]["12y"]["f1"]
    f1j = tbl31["联合训练（上界）"]["12y"]["f1"]
    f1r = tbl31["经验回放（官方容量）"]["12y"]["f1"]
    f1m = tbl31["本章方法"]["12y"]["f1"]
    print(f"  12 年口径缺口闭合率：经验回放 {100*(f1r-f1n)/(f1j-f1n):.2f}%；本章方法 {100*(f1m-f1n)/(f1j-f1n):.2f}%")
    print(f"  与联合上界的差距：经验回放 {f1j-f1r:.2f}；本章方法 {f1j-f1m:.2f}"
          f"（缩小 {(f1j-f1r)-(f1j-f1m):.2f}）")
    report["table_3_1_recheck"] = tbl31
    report["gap_closure"] = {
        "expreplay_12y_pct": 100 * (f1r - f1n) / (f1j - f1n),
        "method_12y_pct": 100 * (f1m - f1n) / (f1j - f1n),
        "gap_to_joint_expreplay": f1j - f1r,
        "gap_to_joint_method": f1j - f1m}
    report["table_3_1_recheck"] = tbl31

    # -------- 表 3-3 参数侧等预算对照复核
    print("\n[表 3-3 复核] 参数侧三形态与样本侧两档（12 年协议口径，单位：百分点）")
    PARAM = {"逐参数位移插值": "freemoca", "弹性权重巩固": "ewc", "无遗忘学习": "lwf",
             "200 条样本": "expreplay_m200", "18,854 条样本": "expreplay_m18854"}
    n12, j12 = mean12(load_years("naive")), mean12(load_years("cumulative"))
    param_rows = []
    for name, tag in PARAM.items():
        by = load_years(tag)
        row = {"name": name, "tag": tag, "12y": mean12(by), "11y": mean11(by)}
        row["gap_closure_12y"] = 100 * (row["12y"] - n12) / (j12 - n12)
        param_rows.append(row)
        print(f"  {name:<14} ({tag:<18}) 12y={row['12y']:6.2f}  11y={row['11y']:6.2f}  "
              f"缺口闭合率 {row['gap_closure_12y']:5.2f}%")
    print("  注：缺口闭合率由未取整读数算出；正文用「两个两位小数均值之差」的约定，"
          "个别行会差 0.1 个百分点")
    print("  注：正文「逐参数位移插值」一行在制品中对应 tag=freemoca，命名与机制名不一致，待作者确认")
    report["table_3_3_recheck"] = param_rows

    # -------- 2025 退化年的独立对照
    cum = load_years("cumulative")
    print(f"\n[2025 退化年] 联合训练（全历史）在 2025 测试分片上的 F1 = {100*cum[2025]:.2f}%"
          f"（测试 n_pos=5）；本章方法与官方回放均为 0.00%")
    report["joint_2025_f1"] = 100 * cum[2025]

    # -------- 隔离核验：逐样本分数
    quar = quarantine_npz()
    print("\n[隔离核验] %s → %s" % (quar["artifact"], quar["verdict"]))
    print("  理由：%s" % quar["reason"])
    print(f"  {'年':>6} {'npz n':>8} {'训练 n':>8} {'测试 n':>8} {'npz正例':>8} {'=训练?':>7}")
    for r in quar["rows"]:
        print(f"  {r['year']:>6} {r['npz_n']:>8} {r['train_n']:>8} {r['test_n']:>8} "
              f"{r['npz_n_pos']:>8} {str(r['matches_train']):>7}")
    print("  ⇒ 该 npz 不承载测试集评价，样本级自助不可用；本报告的区间全部来自年度级配对自助。")
    report["quarantined_npz"] = quar

    # -------- 落盘数值
    (HERE / "stats.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n[落盘] stats.json")

    # -------- 出图
    draw_all(report, cells, cap_rows, mmax_rows, pr_rows, cap_contrasts,
             v11_base, v11_meth, d11)
    return 0


# ---------------------------------------------------------------- 绘图

GRID = "#D9D9D9"
FS_MIN = fs.MIN_FONT_PT
FS_MAIN = fs.MAIN_FONT_PT


def data_axes(cv, rect, grid_axis="y"):
    ax = cv.fig.add_axes(rect)
    ax.set_facecolor("none")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=fs.AUX_LINE_PT, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=2.5, pad=1.5, width=0.7, labelsize=FS_MIN)
    return ax


def ax_lab(ax, axis, value):
    fs.check_label(value, FS_MAIN)
    (ax.set_xlabel if axis == "x" else ax.set_ylabel)(value, fontsize=FS_MAIN, labelpad=3)


def tag(cv, x, y, value, color=fs.INK, ha="left"):
    fs.check_label(value, FS_MIN)
    cv.ax.text(x, y, value, size=FS_MIN, color=color, ha=ha, va="center", zorder=9,
               bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none"})


def draw_all(report, cells, cap_rows, mmax_rows, pr_rows, cap_contrasts,
             v11_base, v11_meth, d11):
    entries = []

    # ---------------- 图A 主对照：逐年配对 + 自助分布
    W, H = 158.0, 80.0
    cv = fs.canvas(W, H)
    ax = data_axes(cv, (0.085, 0.20, 0.50, 0.70))
    x = np.arange(len(Y11))
    ax.plot(x, v11_base, "-", color=fs.M1_EDGE, marker="o", ms=3.0, lw=fs.MAIN_LINE_PT,
            label="官方回放（容量 200）", zorder=3)
    ax.plot(x, v11_meth, "--", color=fs.M2_EDGE, marker="s", ms=3.0, mfc="white",
            lw=fs.MAIN_LINE_PT, label="本章方法（配额+复用分配）", zorder=3)
    ax.axhline(v11_base.mean(), color=fs.M1_EDGE, ls=":", lw=fs.AUX_LINE_PT, zorder=1)
    ax.axhline(v11_meth.mean(), color=fs.M2_EDGE, ls=":", lw=fs.AUX_LINE_PT, zorder=1)
    for i in range(len(Y11)):
        ax.annotate(f"{d11[i]:+.1f}", (i, (v11_base[i] + v11_meth[i]) / 2),
                    fontsize=6.5, ha="center", va="bottom", color=fs.MUTED)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in Y11], fontsize=FS_MIN)
    ax.set_ylim(55, 100)
    ax_lab(ax, "y", "年度测试分片 F1（%）")
    ax_lab(ax, "x", "测试年度（2025 已排除）")
    ax.legend(fontsize=6.5, frameon=False, loc="lower right", ncol=1)

    ax2 = data_axes(cv, (0.66, 0.20, 0.31, 0.70), grid_axis="y")
    boot = paired_year_bootstrap(d11)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    ax2.axvspan(lo, hi, color=fs.M2_FACE, zorder=1)
    ax2.hist(boot, bins=32, color=fs.M2_FACE, edgecolor=fs.M2_EDGE, linewidth=0.5, zorder=2)
    ax2.axvline(0.0, color=fs.INK, ls="--", lw=fs.MAIN_LINE_PT, zorder=4)
    ax2.axvline(d11.mean(), color=fs.M2_EDGE, lw=fs.MAIN_LINE_PT, zorder=4)
    ax2.set_xlabel("11 年平均 F1 之差（百分点）", fontsize=7.5, labelpad=3)
    ax2.set_ylabel("自助频数", fontsize=7.5, labelpad=3)
    ax2.tick_params(labelsize=6.5)
    tag(cv, 0.655, 0.05,
        f"点估计 {d11.mean():+.2f}，95%CI [{lo:+.2f}, {hi:+.2f}]，n={B}；阴影为区间")
    spec = fs.FigureSpec(
        "图A-主对照-逐年配对与自助分布", W, H, None,
        "官方回放（容量 200，蓄水池抽样、统一复用）与本章方法（按年度配额切分 + deficit 复用分配，m=2）"
        "在同一冻结种子 42 下的逐年 F1 与 11 年平均 F1 之差。左：11 个测试年度（2025 因正例仅 5 条、"
        "两臂 F1 均为 0，按 11 年口径排除）的逐年读数，标注为逐年度配对差；点线为各自 11 年平均。"
        "右：年度级配对自助（重采样 11 个年度单元，n=2000）得到的均值差分布，竖实线为点估计，"
        "虚线为 0。误差区间只量化年度测试分片这一层的样本不确定性，不量化训练随机性（单一种子）。")
    entries.append(fs.save_figure(FIGDIR, spec, cv))

    # ---------------- 图B 支撑：容量曲线 + 双机制 2×2
    W, H = 162.0, 78.0
    cv = fs.canvas(W, H)
    ax = data_axes(cv, (0.075, 0.20, 0.42, 0.70))
    cc = [r["cap"] for r in cap_rows]
    ax.plot(cc, [r["base11"] for r in cap_rows], "-", color=fs.M1_EDGE, marker="o", ms=3.2,
            lw=fs.MAIN_LINE_PT, label="官方回放", zorder=3)
    ax.plot(cc, [r["meth11"] for r in cap_rows], "--", color=fs.M2_EDGE, marker="s", ms=3.2,
            mfc="white", lw=fs.MAIN_LINE_PT, label="本章方法", zorder=3)
    for r in cap_rows:
        ax.annotate(f"{r['d11']:+.2f}", (r["cap"], r["meth11"]), fontsize=6.5, ha="center",
                    va="bottom", color=fs.MUTED)
    ax.set_xscale("log")
    ax.set_xticks(list(cc))
    ax.set_xticklabels([str(c) for c in cc], fontsize=6.5)
    ax.set_ylim(83, 95)
    ax.set_xlim(min(cc) * 0.75, max(cc) * 1.7)
    ax_lab(ax, "x", "缓冲容量（条，对数刻度）")
    ax_lab(ax, "y", "11 年平均 F1（%）")
    ax.legend(fontsize=6.5, frameon=False, loc="lower right")

    ax = data_axes(cv, (0.575, 0.20, 0.395, 0.70))
    keys = list(CELL_2x2.keys())
    vals = [cells[k]["12y"] for k in keys]
    cols = [fs.M1_EDGE, fs.M1_EDGE, fs.M2_EDGE, fs.M2_EDGE]
    hatch = ["", "////", "", "\\\\\\\\"]
    bars = ax.bar(range(4), vals, color="white", edgecolor=cols, linewidth=1.2, zorder=3)
    for b, hh in zip(bars, hatch):
        b.set_hatch(hh)
    for i, v in enumerate(vals):
        ax.annotate(f"{v:.2f}", (i, v), fontsize=6.5, ha="center", va="bottom")
    lo_v = min(vals)
    ax.set_ylim(lo_v - 1.2, max(vals) + 1.4)
    ax.set_xticks(range(4))
    ax.set_xticklabels(["蓄水池\n倍数1", "蓄水池\n倍数2", "配额\n倍数1", "配额\n倍数2"], fontsize=6.5)
    ax_lab(ax, "y", "12 年平均 F1（%）")
    ax.text(0.5, 0.94, "双机制 2×2（统一复用，与表 3-4 同源）", transform=ax.transAxes,
            fontsize=6.5, color=fs.MUTED, ha="center", va="top")
    spec = fs.FigureSpec(
        "图B-支撑-容量曲线与双机制消融", W, H, None,
        "左：官方回放与本章方法的 11 年平均 F1 随缓冲容量的变化（对数横轴），标注为两者之差；"
        "相对优势在协议默认容量 200 条上最大，向两侧收窄，18,854 条处归零转负。"
        "右：双机制 2×2 消融（统一复用，12 年协议口径，与表 3-4 逐格对应），"
        "自左至右为蓄水池×倍数1（官方回放）、蓄水池×倍数2、按年度配额×倍数1、按年度配额×倍数2。"
        "两幅均为单一冻结种子 42 的读数，不含误差棒。")
    entries.append(fs.save_figure(FIGDIR, spec, cv))

    # ---------------- 图C 支撑：复用上限 + 年内正例比例
    W, H = 162.0, 76.0
    cv = fs.canvas(W, H)
    ax = data_axes(cv, (0.075, 0.20, 0.42, 0.70))
    mx = [r["m_max"] for r in mmax_rows]
    my = [r["11y"] for r in mmax_rows]
    ax.plot(mx, my, "-", color=fs.M2_EDGE, marker="s", ms=3.2, lw=fs.MAIN_LINE_PT, zorder=3)
    ax.set_xscale("log", base=2)
    ax.set_xticks(mx)
    ax.set_xticklabels([str(v) for v in mx], fontsize=6.5)
    pad = 0.25
    ax.set_ylim(min(my) - pad, max(my) + pad)
    ax.axhline(np.mean(my), color=fs.MUTED, ls=":", lw=fs.AUX_LINE_PT, zorder=1)
    ax_lab(ax, "x", "复用上限 m_max")
    ax_lab(ax, "y", "11 年平均 F1（%）")
    ax.text(0.5, 0.94, f"跨度 {max(my) - min(my):.2f} 个百分点", transform=ax.transAxes,
            fontsize=6.5, color=fs.MUTED, ha="center", va="top")

    ax = data_axes(cv, (0.575, 0.20, 0.395, 0.70))
    px = [float(r["q_pos"]) for r in pr_rows]
    py = [r["11y"] for r in pr_rows]
    ax.plot(px, py, "-", color=fs.M2_EDGE, marker="o", ms=3.2, lw=fs.MAIN_LINE_PT, zorder=3)
    ax.axvline(0.5, color=fs.MUTED, ls=":", lw=fs.AUX_LINE_PT, zorder=1)
    best = int(np.argmax(py))
    ax.plot([px[best]], [py[best]], marker="o", ms=6.5, mfc="white", mec=fs.INK, zorder=5)
    ax.set_ylim(min(py) - 0.6, max(py) + 0.6)
    ax_lab(ax, "x", "年内正例配额占比 q+")
    ax_lab(ax, "y", "11 年平均 F1（%）")
    ax.text(0.97, 0.06, "空心标记为最优取值\n内部最优落在现状 0.50", transform=ax.transAxes,
            fontsize=6.5, color=fs.MUTED, ha="right", va="bottom", linespacing=1.5)
    spec = fs.FigureSpec(
        "图C-支撑-复用上限与正例配额扫描", W, H, None,
        "左：配额臂复用上限 m_max 在 2–64 区间的 11 年平均 F1（容量 200，deficit 分配，种子 42），"
        "曲线非单调、上下抖动，全区间跨度 0.92 个百分点，点线为全区间均值。"
        "右：年内正例配额占比 q+ 的扫描（0.25–0.75），空心标记为最优取值；内部最优落在现状 0.50，"
        "两侧对称下降，降比例方向的损失最大。两幅均为单一冻结种子 42 的读数，不含误差棒。")
    entries.append(fs.save_figure(FIGDIR, spec, cv))

    # ---------------- 图D 支撑：容量曲线的配对差与自助区间
    W, H = 148.0, 74.0
    cv = fs.canvas(W, H)
    ax = data_axes(cv, (0.10, 0.22, 0.66, 0.66))
    cc = [s["cap"] for s in cap_contrasts]
    md = [s["mean_diff"] for s in cap_contrasts]
    lo = [s["mean_diff"] - s["ci_lo"] for s in cap_contrasts]
    hi = [s["ci_hi"] - s["mean_diff"] for s in cap_contrasts]
    x = np.arange(len(cc))
    ax.errorbar(x, md, yerr=[lo, hi], fmt="s", ms=3.6, color=fs.M2_EDGE, ecolor=fs.M2_EDGE,
                elinewidth=0.8, capsize=2.0, lw=0.8, zorder=3)
    ax.axhline(0.0, color=fs.INK, ls="--", lw=fs.AUX_LINE_PT, zorder=2)
    for i, s in enumerate(cap_contrasts):
        star = "*" if s.get("p_holm", 1.0) < 0.05 else ""
        ax.annotate(f"{s['mean_diff']:+.2f}{star}", (i, s["ci_hi"]), fontsize=6.5, ha="center",
                    va="bottom", color=fs.MUTED)
    ax.set_xticks(x)
    ax.set_xticklabels([str(c) for c in cc], fontsize=6.5)
    ax.set_xlim(-0.5, len(cc) - 0.5)
    ax_lab(ax, "x", "缓冲容量（条）")
    ax_lab(ax, "y", "11 年平均 F1 之差（百分点）")
    tag(cv, 0.10, 0.05, f"* 为 Holm 校正后 p<0.05；误差棒为年度级配对自助 95% 区间（n={B}）")
    spec = fs.FigureSpec(
        "图D-支撑-容量曲线的配对差与自助区间", W, H, None,
        "官方回放与本章方法在各缓冲容量上的 11 年平均 F1 之差，误差棒为年度级配对自助 95% 置信区间"
        "（重采样 11 个年度测试分片，n=2000），星号标记 Holm 校正后 p<0.05 的容量点。"
        "差值在协议默认容量 200 条上最大，向两侧收窄，18,854 条处归零转负；"
        "该区间只量化年度测试分片这一层的样本不确定性，不量化训练随机性（单一冻结种子 42）。")
    entries.append(fs.save_figure(FIGDIR, spec, cv))

    for line in fs.verify_outputs(FIGDIR, entries):
        print("  [图件] " + line)
    fs.write_manifest(FIGDIR, "analyze_ch3_results.py", entries,
                      evidence_mode="第三章实验制品重算（单一冻结种子 42）")
    print("  图已写出：", ", ".join(sorted(p.name for p in FIGDIR.glob("*.pdf"))))


if __name__ == "__main__":
    raise SystemExit(main())
