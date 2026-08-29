#!/usr/bin/env python3
"""CEM-BER 四格读数汇总：把四个运行目录的选轮收据压成一份可随时回传的小 JSON。

存在理由（2026-08-29）：compile 路径重跑的 C00 已完成，但主代理只把「最佳轮 = 第 17 轮」
写进文档、漏掉了实体 AP 数值本身，服务器关机后该数值取不到。根因是「记录关键读数」
一直是人工转录动作，而不是程序动作。本脚本把它变成程序动作。

只读、只披露、不阻断：任一臂缺失或未完成都照常输出，用 available 标记状态。
按仓库规则，门禁只用于会使结果无效的失败，读数汇总不是门禁。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 四格的运行身份与展示名。顺序即报告顺序，与守护脚本一致。
CELLS: List[Dict[str, Any]] = [
    {"cell": "C00", "run_id": "ch3-ft-c00-dual-selection-cuda-formal-v1", "display": "裸 FT", "z1": 0, "z2": 0},
    {"cell": "C10", "run_id": "ch3-ft-c10-entity-memory-cuda-formal-v1", "display": "＋因果实体记忆", "z1": 1, "z2": 0},
    {"cell": "C01", "run_id": "ch3-ft-c01-entity-ranking-cuda-formal-v1", "display": "＋预算感知实体排序", "z1": 0, "z2": 1},
    {"cell": "C11", "run_id": "ch3-ft-c11-cem-ber-cuda-formal-v1", "display": "因果状态共享", "z1": 1, "z2": 1},
]


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    """读取 JSON，缺失或损坏都返回 None，不抛异常。"""
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, NotADirectoryError):
        return None
    except (json.JSONDecodeError, OSError) as error:
        print(f"[警告] 无法解析 {path}：{error}", file=sys.stderr)
        return None


def collect_cell(runs_root: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    """汇总单臂：状态、双选轮最佳读数、逐轮历史长度、耗时与峰值资源。"""
    run_dir = runs_root / spec["run_id"]
    status = read_json(run_dir / "status.json")
    selection = read_json(run_dir / "receipts" / "selection.json")

    record: Dict[str, Any] = {
        "cell": spec["cell"],
        "display_name": spec["display"],
        "run_id": spec["run_id"],
        "z1_entity_memory": spec["z1"],
        "z2_entity_ranking": spec["z2"],
        "run_dir_exists": run_dir.is_dir(),
        "state": status.get("state") if status else None,
        "exit_code": status.get("exit_code") if status else None,
        "available": False,
    }

    # inflight.pt 的存在说明该臂可续训；这是判断「中断是否有损失」的直接依据。
    record["has_inflight_checkpoint"] = (run_dir / "checkpoints" / "inflight.pt").is_file()
    record["selected_checkpoints"] = sorted(
        path.name for path in (run_dir / "checkpoints").glob("selected-by-*.pt")
    ) if (run_dir / "checkpoints").is_dir() else []

    if selection is None:
        return record

    history = selection.get("history") or []
    best_entity = selection.get("best_by_entity") or {}
    best_flow = selection.get("best_by_flow") or {}

    record.update({
        "available": True,
        "epochs_completed": len(history),
        "best_entity_ap": best_entity.get("metric"),
        "best_entity_epoch": best_entity.get("epoch"),
        "best_flow_ap": best_flow.get("metric"),
        "best_flow_epoch": best_flow.get("epoch"),
        "selection_rules_agree": best_entity.get("epoch") == best_flow.get("epoch"),
        "wall_seconds": selection.get("wall_seconds"),
        "target_reads": selection.get("target_reads"),
        "resource": selection.get("resource"),
        "entity_ap_by_epoch": [
            {"epoch": item.get("epoch"), "entity_ap": item.get("validation_entity_ap"),
             "flow_ap": item.get("validation_flow_ap")}
            for item in history
        ],
    })
    return record


def evaluate_criteria(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """四格判据：两单机制均严格超 C00，C11 取最大，交互 I 为正。

    任一臂读数缺失时只报告 complete=False，不猜测、不外推。
    """
    readings = {
        item["cell"]: item.get("best_entity_ap")
        for item in cells
        if item.get("available") and item.get("best_entity_ap") is not None
    }
    missing = [spec["cell"] for spec in CELLS if spec["cell"] not in readings]
    verdict: Dict[str, Any] = {
        "metric": "source_year_validation_entity_ap",
        "target_reads": 0,
        "complete": not missing,
        "missing_cells": missing,
        "readings": readings,
    }
    if missing:
        verdict["note"] = "四格未齐，判据不可评估；缺失格不得用其他口径的数值代入"
        return verdict

    c00, c10, c01, c11 = readings["C00"], readings["C10"], readings["C01"], readings["C11"]
    interaction = c11 - c10 - c01 + c00
    verdict.update({
        "c10_beats_c00": c10 > c00,
        "c01_beats_c00": c01 > c00,
        "c11_is_max": c11 >= max(c00, c10, c01),
        "single_effect_c10": c10 - c00,
        "single_effect_c01": c01 - c00,
        "interaction": interaction,
        "interaction_positive": interaction > 0,
    })
    verdict["all_criteria_met"] = bool(
        verdict["c10_beats_c00"] and verdict["c01_beats_c00"]
        and verdict["c11_is_max"] and verdict["interaction_positive"]
    )
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser(description="CEM-BER 四格读数汇总（只读、只披露）")
    parser.add_argument("--runs-root", required=True, help="诊断运行根目录，通常是 runs/diagnostics")
    parser.add_argument("--output", default=None, help="汇总落盘路径；缺省写入 runs-root/ch3-ft-four-cell-summary.json")
    parser.add_argument("--stdout", action="store_true", help="同时把汇总打印到标准输出")
    args = parser.parse_args()

    runs_root = Path(args.runs_root).expanduser().resolve()
    if not runs_root.is_dir():
        print(f"[错误] 运行根目录不存在：{runs_root}", file=sys.stderr)
        return 2

    cells = [collect_cell(runs_root, spec) for spec in CELLS]
    summary = {
        "schema_version": "ch3-ft-four-cell-summary-v1",
        "runs_root": str(runs_root),
        "hostname": os.uname().nodename,
        "cells": cells,
        "criteria": evaluate_criteria(cells),
    }

    output = Path(args.output) if args.output else runs_root / "ch3-ft-four-cell-summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    # 原子写：先写临时文件再替换，避免读到半截 JSON。
    staging = output.with_suffix(output.suffix + ".partial")
    with staging.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    staging.replace(output)

    for item in cells:
        if item["available"]:
            print(
                f"{item['cell']} {item['display_name']}：实体 AP {item['best_entity_ap']} "
                f"（第 {item['best_entity_epoch']} 轮／共 {item['epochs_completed']} 轮），"
                f"state={item['state']} exit={item['exit_code']}",
                file=sys.stderr,
            )
        else:
            print(
                f"{item['cell']} {item['display_name']}：无选轮收据，"
                f"state={item['state']} inflight={item['has_inflight_checkpoint']}",
                file=sys.stderr,
            )
    print(f"汇总已写入 {output}", file=sys.stderr)

    if args.stdout:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
