#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CEM-BER 四格在 LSPR24 上的封印后零物化描述性评价。

本入口**不训练、不选择、不改阈值、不碰源年封印**：四格的检查点与选轮结果在源年
已经冻结，本步只把它们各自跑一遍目标年，产出跨年度描述性读数。

**为什么不能读 `runs/diagnostics/dijk-repro/cache/X24.npy`**：实测该数组不是 Dijk 83
字段原值，而是 dijk 复现管线自己标准化后的特征矩阵（LSPR23 对照实测：与协议 A 冻结
raw83 有 1,224,589,881 个有限值单元不同，前 20 万行最大绝对差 251799984.0）。把它送进
按 raw83 拟合分位数变换的 FT，等于给模型从未见过的输入分布，读数无效。本工具沿用
`ch3_tabular_resnet_lspr24_inmemory_descriptive_eval` 的正确路径：目标年 83 字段原值
从冻结 Parquet 流式读入，序列结构用配置以 SHA-256 登记的 `I24.npy` / `M24.npy`。

选轮口径：四格统一取源年实体 AP 择优的 `selected-by-entity.pt`（2026-08-28 冻结裁决）；
`selected-by-flow.pt` 一并评价，作协议敏感性对照，不作主口径。

输入变换：复用源年封印的 `sealed-input-transform.pkl`——目标年**不重新拟合**，
否则等于让模型见到目标年分布，破坏封印。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

RUN_ID = "ch3-ft-lspr24-descriptive-eval-v1"
SCHEMA_VERSION = "ch3-ft-lspr24-descriptive-eval-receipt-v1"
CELLS = ("c00", "c10", "c01", "c11")
SELECTION_ROLES = ("entity", "flow")
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def resolve_cell_runs(runs_root: Path) -> dict[str, Path]:
    """把四格短键映射到各自的正式运行目录；缺任一格即报错，不做部分评价。

    部分评价没有意义：四格判据要求同时比较 C00/C10/C01/C11，缺一格则交互项无法计算。
    """
    mapping = {
        "c00": "ch3-ft-c00-dual-selection-cuda-formal-v1",
        "c10": "ch3-ft-c10-entity-memory-cuda-formal-v1",
        "c01": "ch3-ft-c01-entity-ranking-cuda-formal-v1",
        "c11": "ch3-ft-c11-cem-ber-cuda-formal-v1",
    }
    resolved: dict[str, Path] = {}
    missing: list[str] = []
    for cell, run_id in mapping.items():
        root = runs_root / run_id
        selection = root / "receipts" / "selection.json"
        if not selection.is_file():
            missing.append(f"{cell}({run_id})")
            continue
        resolved[cell] = root
    if missing:
        raise SystemExit(f"四格未齐备，缺：{', '.join(missing)}；不做部分评价")
    return resolved


def load_sealed_selection(run_root: Path) -> dict[str, Any]:
    """读取源年封印的选轮收据，确认其为已完成运行。"""
    receipt = json.loads((run_root / "receipts" / "selection.json").read_text(encoding="utf-8"))
    status = json.loads((run_root / "status.json").read_text(encoding="utf-8"))
    if status.get("state") != "finished" or status.get("exit_code") != 0:
        raise SystemExit(f"{run_root.name} 未正常完成，拒绝评价：{status}")
    if int(status.get("target_reads", -1)) != 0:
        raise SystemExit(f"{run_root.name} 源年运行的 target_reads 非零，封印已破")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", default="runs/diagnostics")
    parser.add_argument("--target-config", default="configs/ch3-protocol-a-raw83-target-v1.json")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    parser.add_argument("--dry-run", action="store_true",
                        help="只核验四格齐备与封印状态，不做前向；用于四格跑完前的预检")
    args = parser.parse_args()

    runs_root = Path(args.runs_root).resolve()
    output_root = Path(args.output_root).resolve()

    log("核验四格齐备与源年封印状态")
    cell_runs = resolve_cell_runs(runs_root)
    sealed: dict[str, dict[str, Any]] = {}
    for cell, root in cell_runs.items():
        receipt = load_sealed_selection(root)
        best_entity = receipt["best_by_entity"]
        best_flow = receipt["best_by_flow"]
        sealed[cell] = {
            "run_id": receipt["run_id"],
            "source_entity_ap": best_entity["metric"],
            "source_entity_epoch": best_entity["epoch"],
            "source_flow_ap": best_flow["metric"],
            "source_flow_epoch": best_flow["epoch"],
            "epochs": len(receipt["history"]),
        }
        for role in SELECTION_ROLES:
            checkpoint = root / "checkpoints" / f"selected-by-{role}.pt"
            if not checkpoint.is_file():
                raise SystemExit(f"{cell} 缺 selected-by-{role}.pt，无法评价")
        log(f"  {cell}: 源年实体AP={best_entity['metric']:.6f}（轮{best_entity['epoch']}）"
            f" 逐流AP={best_flow['metric']:.6f}（轮{best_flow['epoch']}）")

    interaction = (
        sealed["c11"]["source_entity_ap"] - sealed["c10"]["source_entity_ap"]
        - sealed["c01"]["source_entity_ap"] + sealed["c00"]["source_entity_ap"]
    )
    baseline = sealed["c00"]["source_entity_ap"]
    verdict = {
        "c10_over_c00": sealed["c10"]["source_entity_ap"] - baseline,
        "c01_over_c00": sealed["c01"]["source_entity_ap"] - baseline,
        "c11_is_best": sealed["c11"]["source_entity_ap"] >= max(
            sealed[c]["source_entity_ap"] for c in ("c00", "c10", "c01")
        ),
        "interaction": interaction,
        "note": "以上为源年读数，仅用于确认四格结构；目标年读数在下方 target 段",
    }
    log(f"源年四格判据：C10−C00={verdict['c10_over_c00']:+.6f} "
        f"C01−C00={verdict['c01_over_c00']:+.6f} "
        f"C11最佳={verdict['c11_is_best']} 交互={interaction:+.6f}")

    if args.dry_run:
        atomic_json(output_root / "preflight.json", {
            "schema_version": SCHEMA_VERSION, "run_id": RUN_ID, "stage": "preflight",
            "source_sealed": sealed, "source_verdict": verdict, "target_reads": 0,
        })
        log("预检完成（--dry-run），未做目标年前向")
        return 0

    # 目标年前向沿用 ch3_tabular_resnet_lspr24_inmemory_descriptive_eval 的零物化路径：
    # 从冻结 Parquet 流式读 83 字段原值，用源年封印的变换在内存中复算，绝不读 X24.npy。
    log("目标年前向尚未接线：需复用零物化 Parquet 读取器")
    raise SystemExit(
        "目标年前向未实现——请先用 --dry-run 完成四格齐备与封印预检；"
        "前向部分待四格跑完后按零物化路径接线"
    )


if __name__ == "__main__":
    sys.exit(main())
