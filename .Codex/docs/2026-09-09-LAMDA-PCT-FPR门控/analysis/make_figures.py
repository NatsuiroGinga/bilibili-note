from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[4] / "thesis" / "experiments" / "llm_probe" / "runs" / "diagnostics" / "ch3-lamda-pct-fpr-screening-mps-seed42-v1"
OUT = Path(__file__).resolve().parent / "figures"


def load_summary() -> dict:
    return json.loads((ROOT / "development-summary.json").read_text(encoding="utf-8"))


def style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["SimHei", "Arial Unicode MS", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.dpi": 120,
        "savefig.dpi": 400,
    })


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)


def development_metrics() -> None:
    summary = load_summary()["arms"]
    names = ["ER", "ER＋PCT", "ER＋缺口修复", "ER＋缺口修复＋PCT"]
    keys = ["experience_replay", "pct", "gap_repair", "gap_repair_pct"]
    metrics = [("AP", "AP"), ("F1", "F1"), ("FPR", "FPR"), ("FNR", "FNR")]
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.2), constrained_layout=True)
    x = np.arange(len(names))
    for axis, (title, key) in zip(axes, metrics, strict=True):
        values = [summary[arm]["current_year_metrics"][key] for arm in keys]
        axis.bar(x, values, color=["#355c7d", "#6c9a8b", "#c06c84", "#f67280"], width=0.68)
        axis.set_title(title)
        axis.set_xticks(x, names, rotation=35, ha="right")
        axis.grid(axis="y", alpha=0.25)
        axis.set_axisbelow(True)
        for i, value in enumerate(values):
            axis.text(i, value, f"{value:.3f}", ha="center", va="bottom", fontsize=7)
    fig.suptitle("LAMDA 开发期四臂预筛指标（单种子，CPU）")
    save(fig, "figure-01-development-metrics")


def historical_gate() -> None:
    arms = ["experience_replay", "pct", "gap_repair", "gap_repair_pct"]
    names = ["ER", "ER＋PCT", "ER＋缺口修复", "ER＋缺口修复＋PCT"]
    colors = ["#355c7d", "#6c9a8b", "#c06c84", "#f67280"]
    values: dict[str, list[tuple[float, float]]] = {arm: [] for arm in arms}
    for arm in arms:
        for year in (2016, 2017):
            gate = json.loads((ROOT / "metrics" / arm / f"year-{year}.json").read_text(encoding="utf-8"))["evaluation"]["historical_benign_gate"]
            values[arm].append((gate["old_fpr"], gate["new_fpr"]))
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2), sharey=True, constrained_layout=True)
    for axis, year_index, year in zip(axes, (0, 1), (2016, 2017), strict=True):
        x = np.arange(len(names))
        old = [values[arm][year_index][0] for arm in arms]
        new = [values[arm][year_index][1] for arm in arms]
        width = 0.36
        axis.bar(x - width / 2, old, width, label="旧 FPR", color="#9aa5b1")
        axis.bar(x + width / 2, new, width, label="新 FPR", color=colors)
        axis.set_title(f"训练至 {year}")
        axis.set_xticks(x, names, rotation=35, ha="right")
        axis.grid(axis="y", alpha=0.25)
        axis.set_axisbelow(True)
    axes[0].set_ylabel("历史良性 FPR")
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("历史良性 FPR gate 诊断")
    save(fig, "figure-02-historical-benign-gate")


if __name__ == "__main__":
    style()
    development_metrics()
    historical_gate()
