"""第三章结果分析：从权威制品重算描述统计、配对检验与效应量，并出图。

口径（与正文 3.6.1 一致）：
  - 报告 experience = 2025，mode = backward。
  - 12 年口径 = 12 个测试年度 F1 的算术平均（协议口径，表 3-1 至表 3-5 用）。
  - 11 年口径 = 排除 2025 测试年度后的 11 年平均（细粒度比较用；该年 8,933 条中正例仅 5 条）。
本脚本不手工录入任何读数，全部由 metrics_*.json 的 records 现场重算。
"""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ART = REPO / "thesis/experiments/llm_probe/runs/diagnostics/ch3-lamda-domain-il-e4-replication-v1"
FIGDIR = HERE / "figures"
FIGDIR.mkdir(exist_ok=True)

# 复用论文图件的字体解析（Office 随附 SimHei，逐字核验可用性）
sys.path.insert(0, str(REPO / "thesis/figures/第三章"))
import figstyle as fs  # noqa: E402

TEST_YEARS = (2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025)
Y11 = tuple(y for y in TEST_YEARS if y != 2025)


class Incomplete(FileNotFoundError):
    """制品存在但记录未写全（该臂仍在运行或曾中断）。"""


def read(tag: str) -> tuple[float, float]:
    """返回 (12 年平均, 11 年平均)，单位百分点。

    记录不足 12 条时抛 `Incomplete`——运行中的臂会留下半成品 JSON，此处不静默取部分记录。
    """
    p = ART / f"metrics_{tag}.json"
    if not p.is_file():
        raise Incomplete(f"{p} 不存在")
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise Incomplete(f"{p} 不是完整 JSON（{e}）") from e
    recs = [
        r
        for r in payload["records"]
        if r["experience"] == 2025 and r["mode"] == "backward"
    ]
    if len(recs) != 12:
        raise Incomplete(f"{tag} 的 backward 记录 {len(recs)}/12 条")
    by = {int(r["test_year"]): float(r["f1"]) for r in recs}
    a12 = 100.0 * sum(by[y] for y in TEST_YEARS) / 12
    a11 = 100.0 * sum(by[y] for y in Y11) / 11
    return round(a12, 2), round(a11, 2)


def desc(xs: list[float]) -> str:
    if len(xs) == 1:
        return f"{xs[0]:.2f} (n=1)"
    return f"{st.mean(xs):.2f} ± {st.stdev(xs):.2f} (n={len(xs)})"


def paired_tbl(name: str, a: dict[str, float], b: dict[str, float]) -> None:
    """同名种子的配对差。"""
    common = sorted(set(a) & set(b))
    print(f"\n[{name}] 配对（可用种子 {common}）")
    if not common:
        print("  无同名种子 ⇒ 配对检验被阻断")
        return
    d = [b[s] - a[s] for s in common]
    print(f"  逐对差：{['%+0.2f' % x for x in d]}")
    print(f"  均值 {st.mean(d):+.2f}" + (f"，标准差 {st.stdev(d):.2f}" if len(d) > 1 else ""))
    print(f"  全部同号：{'是' if all(x > 0 for x in d) or all(x < 0 for x in d) else '否'}")


# ---------------------------------------------------------------- 数据
print("=" * 78)
print("第三章结果分析 · 描述统计（单位：百分点）")
print("=" * 78)

CAPS = (50, 200, 400, 800, 1600, 18854)
res12, res11, met12, met11 = {}, {}, {}, {}
for c in CAPS:
    rt = "expreplay" if c == 200 else f"expreplay_m{c}"
    mt = f"expreplay_m{c}_quota_deficit_r2"
    try:
        res12[c], res11[c] = read(rt)
        met12[c], met11[c] = read(mt)
    except FileNotFoundError as e:
        print(f"[缺] {e.name}")

print("\n容量曲线（12 年口径 / 11 年口径）")
print(f"{'容量':>6} {'官方回放 12y':>12} {'本章方法 12y':>12} {'差':>7} | {'官方回放 11y':>12} {'本章方法 11y':>12} {'差':>7}")
for c in CAPS:
    if c not in res12:
        continue
    print(
        f"{c:>6} {res12[c]:>12.2f} {met12[c]:>12.2f} {met12[c]-res12[c]:>+7.2f} | "
        f"{res11[c]:>12.2f} {met11[c]:>12.2f} {met11[c]-res11[c]:>+7.2f}"
    )

# 主对照（多种子）
BASE = {42: "expreplay_m200", 43: "expreplay_m200_s43", 44: "expreplay_m200_s44", 45: "expreplay_m200_s45", 46: "expreplay_m200_s46"}
METH = {42: "expreplay_m200_quota_deficit_r2", 43: "expreplay_m200_quota_deficit_r2_s43",
        44: "expreplay_m200_quota_deficit_r2_s44", 45: "expreplay_m200_quota_deficit_r2_s45",
        46: "expreplay_m200_quota_deficit_r2_s46"}
b11, m11 = {}, {}
print("\n主对照：官方回放（容量 200，复用 1）vs 本章方法（按年度配额 + 复用分配，复用 2）")
for s, t in BASE.items():
    try:
        _, v = read(t)
        b11[s] = v
        print(f"  基线 seed {s}: 11y = {v:.2f}")
    except FileNotFoundError:
        print(f"  基线 seed {s}: 缺")
for s, t in METH.items():
    try:
        _, v = read(t)
        m11[s] = v
        print(f"  本章 seed {s}: 11y = {v:.2f}")
    except FileNotFoundError:
        print(f"  本章 seed {s}: 缺")
print(f"\n  基线   {desc(list(b11.values()))}")
print(f"  本章   {desc(list(m11.values()))}")
paired_tbl("主对照", b11, m11)

# 2×2（全部 m=1）
CELL = {
    "按样本量比例·不分层": {"42": "expreplay"},
    "按样本量比例·分层": {"42": "expreplay_m200_prop_strat", "43": "expreplay_m200_prop_strat_s43",
                          "44": "expreplay_m200_prop_strat_s44", "45": "expreplay_m200_prop_strat_s45"},
    "年度间等额·不分层": {"42": "expreplay_m200_equal_unstrat", "43": "expreplay_m200_equal_unstrat_s43",
                          "44": "expreplay_m200_equal_unstrat_s44"},
    "年度间等额·分层": {"42": "expreplay_m200_quota", "43": "expreplay_m200_quota_s43",
                        "44": "expreplay_m200_quota_s44"},
}
print("\n双机制 2×2（全部复用倍数 1，11 年口径）")
cells: dict[str, list[float]] = {}
for name, tags in CELL.items():
    vs = []
    for s, t in tags.items():
        try:
            _, v = read(t)
            vs.append(v)
        except FileNotFoundError:
            pass
    cells[name] = vs
    print(f"  {name:<20} {desc(vs)}  逐种子 {['%.2f' % v for v in vs]}")

# m_max 扫描
print("\n配额臂复用上限扫描（容量 200，复用分配，seed 42，11 年口径）")
for mm in (1, 2, 4, 8, 16, 32, 64):
    t = f"expreplay_m200_quota_deficit_r{mm}" if mm != 1 else None
    if t is None:
        print(f"  m_max={mm:<3} （未跑）")
        continue
    try:
        _, v = read(t)
        print(f"  m_max={mm:<3} {v:.2f}")
    except FileNotFoundError:
        print(f"  m_max={mm:<3} 缺")

# 年内正例比例
print("\n年内正例比例扫描（11 年口径）")
for lbl, t in (("0.25", "expreplay_m200_quota_pr25_deficit_r2"), ("0.40", "expreplay_m200_quota_pr40_deficit_r2"),
               ("0.50", "expreplay_m200_quota_deficit_r2"), ("0.60", "expreplay_m200_quota_pr60_deficit_r2"),
               ("0.75", "expreplay_m200_quota_pr75_deficit_r2")):
    try:
        _, v = read(t)
        print(f"  {lbl}  {v:.2f}")
    except FileNotFoundError:
        print(f"  {lbl}  缺")

# ---------------------------------------------------------------- 图
fs.apply_rcparams() if hasattr(fs, "apply_rcparams") else None
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [fs.CJK_FONT.name]
plt.rcParams["axes.unicode_minus"] = False

# 图 A：主对照的种子分布
fig, ax = plt.subplots(figsize=(5.9, 3.6), dpi=200)
seeds = sorted(set(b11) | set(m11))
x = range(len(seeds))
ax.plot(x, [b11.get(s, float("nan")) for s in seeds], "o-", color=fs.M1_EDGE, label="官方回放（容量 200）")
ax.plot(x, [m11.get(s, float("nan")) for s in seeds], "s--", color=fs.M2_EDGE, mfc="white", label="本章方法")
for i, s in enumerate(seeds):
    if s in b11 and s in m11:
        ax.annotate(f"{m11[s]-b11[s]:+.2f}", (i, (b11[s] + m11[s]) / 2), fontsize=7,
                    ha="left", va="center", color="0.35")
ax.set_xticks(list(x))
ax.set_xticklabels([f"seed {s}" for s in seeds])
ax.set_ylabel("11 年平均 F1（%）")
ax.set_title("主对照的种子分布与配对差")
ax.legend(fontsize=7, frameon=False)
ax.grid(axis="y", color="0.9", lw=0.6)
fig.tight_layout()
fig.savefig(FIGDIR / "fig-A-主对照种子分布.pdf")
fig.savefig(FIGDIR / "fig-A-主对照种子分布.png", dpi=200)
plt.close(fig)

# 图 B：容量曲线 + 2×2 分解
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.5), dpi=200)
ax = axes[0]
cc = [c for c in CAPS if c in res11]
ax.plot([c for c in cc], [res11[c] for c in cc], "o-", color=fs.M1_EDGE, label="官方回放")
ax.plot([c for c in cc], [met11[c] for c in cc], "s--", color=fs.M2_EDGE, mfc="white", label="本章方法")
ax.set_xscale("log")
ax.set_xlabel("缓冲容量（条，对数刻度）")
ax.set_ylabel("11 年平均 F1（%）")
ax.set_title("容量曲线：相对优势在 200 条上最大")
ax.legend(fontsize=7, frameon=False)
ax.grid(color="0.9", lw=0.6)
for c in cc:
    ax.annotate(f"{met11[c]-res11[c]:+.2f}", (c, met11[c]), fontsize=6.5, ha="center", va="bottom", color="0.35")

ax = axes[1]
order = ["按样本量比例·不分层", "按样本量比例·分层", "年度间等额·不分层", "年度间等额·分层"]
vals = [st.mean(cells[n]) for n in order]
cols = [fs.M1_EDGE, fs.M2_EDGE, fs.M1_EDGE, fs.M2_EDGE]
hatch = ["", "", "///", "\\\\\\"]
bars = ax.bar(range(4), vals, color="white", edgecolor=cols, linewidth=1.2)
for b, h in zip(bars, hatch):
    b.set_hatch(h)
for i, n in enumerate(order):
    ax.annotate(f"{vals[i]:.2f}", (i, vals[i]), fontsize=7, ha="center", va="bottom")
ax.set_xticks(range(4))
ax.set_xticklabels(["比例\n不分层", "比例\n分层", "等额\n不分层", "等额\n分层"], fontsize=7)
ax.set_ylim(min(vals) - 1.5, max(vals) + 1.2)
ax.set_ylabel("11 年平均 F1（%）")
ax.set_title("双机制 2×2（全部复用倍数 1）")
ax.axhline(st.mean(cells[order[0]]), color="0.6", ls=":", lw=0.8)
ax.grid(axis="y", color="0.9", lw=0.6)
fig.tight_layout()
fig.savefig(FIGDIR / "fig-B-容量曲线与2x2分解.pdf")
fig.savefig(FIGDIR / "fig-B-容量曲线与2x2分解.png", dpi=200)
plt.close(fig)

print("\n图已写出：", ", ".join(sorted(p.name for p in FIGDIR.glob("*.pdf"))))
