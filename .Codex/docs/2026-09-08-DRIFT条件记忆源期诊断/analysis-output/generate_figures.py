#!/usr/bin/env python3
"""从冻结结果 JSON 生成条件记忆资格分析图。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


SIGNALS = (
    "char2_s",
    "char2_a",
    "char2_c",
    "char3_s",
    "char3_a",
    "char3_c",
)
YEARS = ("T17", "T18", "T19")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def configure() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["SimHei", "Songti SC", "Arial Unicode MS"],
            "axes.unicode_minus": False,
            "figure.dpi": 160,
            "savefig.bbox": "tight",
        }
    )


def plot_logloss(result: dict, output_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    colors = {"de": "#2B6F8A", "engram": "#C4552D"}
    names = {"de": "DeepEmbed", "engram": "Engram"}
    for axis, label, title in zip(axes, ("0", "1"), ("良性", "DGA"), strict=True):
        x = np.arange(2)
        for offset, candidate in ((-0.12, "de"), (0.12, "engram")):
            values = []
            low = []
            high = []
            for year in ("T18", "T19"):
                row = result["analysis"]["by_label"][label]["years"][year][candidate][
                    "comparisons"
                ]["versus_d0"]
                values.append(row["mean_log_loss_difference"])
                low.append(row["mean_log_loss_difference"] - row["ci_lower"])
                high.append(row["ci_upper"] - row["mean_log_loss_difference"])
            axis.errorbar(
                x + offset,
                values,
                yerr=np.asarray([low, high]),
                marker="o",
                linewidth=1.6,
                capsize=4,
                color=colors[candidate],
                label=names[candidate],
            )
        axis.axhline(0.0, color="#333333", linewidth=0.9)
        axis.set_xticks(x, ("T18", "T19"))
        axis.set_title(title)
        axis.set_ylabel("相对 D0 的成对对数损失差")
        axis.grid(axis="y", alpha=0.2)
    axes[0].legend(frameon=False)
    fig.suptitle("条件记忆键特征的错误预测增量（95% 区间）")
    fig.savefig(output_dir / "figure-01-logloss-difference.pdf")
    fig.savefig(output_dir / "figure-01-logloss-difference.png")
    plt.close(fig)


def heatmap(axis, matrix: np.ndarray, title: str, limit: float):
    image = axis.imshow(matrix, cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto")
    axis.set_xticks(np.arange(len(YEARS)), YEARS)
    axis.set_yticks(np.arange(len(SIGNALS)), SIGNALS)
    axis.set_title(title)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            axis.text(column, row, f"{value:+.3f}", ha="center", va="center", fontsize=7)
    return image


def plot_direction(result: dict, output_dir: Path) -> None:
    partial = result["analysis"]["partial_rank"]["1"]["engram"]["by_year"]
    centered = result["analysis"]["family_centered"]
    partial_matrix = np.asarray([[partial[year][signal] for year in YEARS] for signal in SIGNALS])
    centered_matrix = np.asarray(
        [[centered[year]["engram"][signal]["correlation"] for year in YEARS] for signal in SIGNALS]
    )
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0))
    limit = max(float(np.max(np.abs(partial_matrix))), float(np.max(np.abs(centered_matrix))), 1e-6)
    heatmap(axes[0], partial_matrix, "DGA 偏秩相关", limit)
    image = heatmap(
        axes[1], centered_matrix, "family 内中心化相关（描述）", limit
    )
    fig.colorbar(image, ax=axes, shrink=0.75, label="相关系数")
    fig.suptitle("Engram 键信号的预注册方向检查")
    fig.savefig(output_dir / "figure-02-engram-direction.pdf")
    fig.savefig(output_dir / "figure-02-engram-direction.png")
    plt.close(fig)


def main() -> int:
    args = parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    configure()
    plot_logloss(result, args.output_dir)
    plot_direction(result, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
