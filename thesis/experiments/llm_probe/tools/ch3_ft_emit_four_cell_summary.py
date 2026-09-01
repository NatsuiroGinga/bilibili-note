#!/usr/bin/env python3
"""第三章 FT 四格读数汇总：把四个格的选轮收据压成一份可随时回传的小 JSON。

存在理由（2026-08-29）：compile 路径重跑的 C00 已完成，但主代理只把「最佳轮 = 第 17 轮」
写进文档、漏掉了实体 AP 数值本身，服务器关机后该数值取不到。根因是「记录关键读数」
一直是人工转录动作，而不是程序动作。本脚本把它变成程序动作。

只读、只披露、不阻断：任一格缺失或未完成都照常输出，用 available 标记状态。
按仓库规则，门禁只用于会使结果无效的失败，读数汇总不是门禁。

新四格适配（2026-09-01，依据 `.Codex/docs/RWKV/2026-09-01-C10路线裁决.md` 第三节）：
旧 CEM-BER 四格已被否决（`RWKV第三章恢复卡.md` 第 9 行），当前活动候选是「实体内尾部
聚合（`z1`，α=0.5 top-k）× 预算感知实体排序（`z2`，BER）」。与旧四格的关键差异——

1. 每轮训练收据（`selection.json` 的 `history`）新增 `validation_entity_ap_tail`，
   与既有 `validation_entity_ap`（max 口径）并列，双口径逐轮同时评价。
2. 每个非 CEM 运行目录新增第三份选轮检查点 `selected-by-entity-tail.pt`，与既有
   `selected-by-flow.pt` / `selected-by-entity.pt` 并列；`selection.json` 顶层对应新增
   `best_by_entity_tail`。
3. C10 不再是独立训练：`z2=0` 时尾部聚合不进训练图，C10 = C00 同一次训练的
   `selected-by-entity-tail.pt`（tail 口径选轮），与 C00 共享 `run_id`／运行目录，只是
   读取角色（`metric_role`）不同。四格因此只需三次独立训练（C00、C01、C11）。

向后兼容硬约束：旧 CEM-BER 四格的 `selection.json` 没有 `best_by_entity_tail` 顶层键、
`history` 条目也没有 `validation_entity_ap_tail` 键；全部读取一律用 `.get()`，缺键返回
`None` 而不是抛异常或误判。`--cell-set legacy` 保留旧四格的运行身份与判据读法，确保历史
制品仍可被正确解析、汇总与出表。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# 每种读数角色对应 selection.json 里的最佳轮字段、逐轮历史里的 AP 字段、以及要
# 读取的选轮检查点文件名。max 口径是历史实现（C00/C01 的选轮依据），tail 口径是
# 2026-09-01 双聚合选轮改造新增（C10/C11 的选轮依据）。
ROLE_CONFIG: Dict[str, Dict[str, str]] = {
    "max": {
        "best_key": "best_by_entity",
        "ap_field": "validation_entity_ap",
        "checkpoint_name": "selected-by-entity.pt",
    },
    "tail": {
        "best_key": "best_by_entity_tail",
        "ap_field": "validation_entity_ap_tail",
        "checkpoint_name": "selected-by-entity-tail.pt",
    },
}

# 四格的运行身份、展示名与读数角色。顺序即报告顺序。
#
# "new"：当前活动候选（尾部聚合 × BER）。C10 与 C00 共享 run_id——同一次训练，
# 只是分别按 max／tail 两种口径各自独立选轮（`shares_training_with` 仅作报告标注，
# 不参与目录查找）。C11 的 run_id 取自冻结配置 `configs/ch3-ft-c11-tail-aggregation-
# ber-eager-formal-v2.json` 的 `identity.run_id` 字段实测值——与本任务简报里给出的
# `ch3-ft-c11-tail-ranking-eager-formal-v2` 不一致，以冻结配置文件的实测值为准。
#
# "legacy"：已否决的旧 CEM-BER 四格（`RWKV第三章恢复卡.md` 第 9 行「CEM 正式候选已
# 否决」），四格各自独立训练，全部使用 max 口径选轮，历史上从未有 tail 口径。保留
# 该集合只为让本工具仍能正确读取历史制品，不代表候选复活。
CELL_SETS: Dict[str, List[Dict[str, Any]]] = {
    "new": [
        {
            "cell": "C00", "run_id": "ch3-ft-c00-bare-eager-formal-v2",
            "display": "裸 FT（max 口径选轮）", "z1": 0, "z2": 0,
            "metric_role": "max", "shares_training_with": None,
        },
        {
            "cell": "C10", "run_id": "ch3-ft-c00-bare-eager-formal-v2",
            "display": "＋实体内尾部聚合（tail 口径选轮，复用 C00 权重）", "z1": 1, "z2": 0,
            "metric_role": "tail", "shares_training_with": "C00",
        },
        {
            "cell": "C01", "run_id": "ch3-ft-c01-ranking-eager-formal-v2",
            "display": "＋预算感知实体排序（max 口径选轮）", "z1": 0, "z2": 1,
            "metric_role": "max", "shares_training_with": None,
        },
        {
            "cell": "C11", "run_id": "ch3-ft-c11-tail-aggregation-ber-eager-formal-v2",
            "display": "尾部聚合＋预算感知实体排序（tail 口径选轮）", "z1": 1, "z2": 1,
            "metric_role": "tail", "shares_training_with": None,
        },
    ],
    "legacy": [
        {
            "cell": "C00", "run_id": "ch3-ft-c00-dual-selection-cuda-formal-v1",
            "display": "裸 FT", "z1": 0, "z2": 0,
            "metric_role": "max", "shares_training_with": None,
        },
        {
            "cell": "C10", "run_id": "ch3-ft-c10-entity-memory-cuda-formal-v1",
            "display": "＋因果实体记忆（已否决）", "z1": 1, "z2": 0,
            "metric_role": "max", "shares_training_with": None,
        },
        {
            "cell": "C01", "run_id": "ch3-ft-c01-entity-ranking-cuda-formal-v1",
            "display": "＋预算感知实体排序", "z1": 0, "z2": 1,
            "metric_role": "max", "shares_training_with": None,
        },
        {
            "cell": "C11", "run_id": "ch3-ft-c11-cem-ber-cuda-formal-v1",
            "display": "因果状态共享（已否决）", "z1": 1, "z2": 1,
            "metric_role": "max", "shares_training_with": None,
        },
    ],
}

CELL_SET_LEGEND: Dict[str, Dict[str, str]] = {
    "new": {"z1": "entity_tail_aggregation(alpha=0.5, atk_tail_mean)", "z2": "entity_ranking(BER/CVaR-pAUC)"},
    "legacy": {"z1": "causal_entity_memory(CEM，已否决)", "z2": "entity_ranking(BER/CVaR-pAUC)"},
}


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
    """汇总单格：状态、本格自身读数角色下的最佳轮、选中轮次的三项指标、检查点路径。

    ``metric_role`` 决定读哪一套字段：
    - ``max``：``best_by_entity`` / ``validation_entity_ap`` / ``selected-by-entity.pt``
    - ``tail``：``best_by_entity_tail`` / ``validation_entity_ap_tail`` /
      ``selected-by-entity-tail.pt``

    旧格式（无 tail 口径）与「CEM 分支不产出 tail 口径」两种情况下，``best_by_entity_tail``
    在 ``selection.json`` 里要么整个顶层键不存在、要么值为 ``None``；两种情况 ``.get()``
    都返回 ``None``，这里统一按「本格不可用」处理，不抛异常、不误报数值。
    """
    run_dir = runs_root / spec["run_id"]
    status = read_json(run_dir / "status.json")
    selection = read_json(run_dir / "receipts" / "selection.json")
    role = spec.get("metric_role", "max")
    role_config = ROLE_CONFIG[role]
    checkpoints_dir = run_dir / "checkpoints"
    checkpoint_path = checkpoints_dir / role_config["checkpoint_name"]

    record: Dict[str, Any] = {
        "cell": spec["cell"],
        "display_name": spec["display"],
        "run_id": spec["run_id"],
        "metric_role": role,
        "shares_training_with": spec.get("shares_training_with"),
        "z1": spec["z1"],
        "z2": spec["z2"],
        "run_dir_exists": run_dir.is_dir(),
        "state": status.get("state") if status else None,
        "exit_code": status.get("exit_code") if status else None,
        "available": False,
    }

    # inflight.pt 的存在说明该格可续训；这是判断「中断是否有损失」的直接依据。
    record["has_inflight_checkpoint"] = (checkpoints_dir / "inflight.pt").is_file()
    record["selected_checkpoints"] = sorted(
        path.name for path in checkpoints_dir.glob("selected-by-*.pt")
    ) if checkpoints_dir.is_dir() else []
    record["selected_checkpoint_path"] = str(checkpoint_path)
    record["selected_checkpoint_exists"] = checkpoint_path.is_file()

    if selection is None:
        record["missing_reason"] = "无 receipts/selection.json（训练未完成或未开始）"
        return record

    history = selection.get("history") or []
    record["epochs_completed"] = len(history)

    best_role = selection.get(role_config["best_key"])
    if not best_role:
        record["missing_reason"] = (
            f"selection.json 缺 {role_config['best_key']}"
            "（旧格式无该键，或该运行走 CEM 分支不产出 tail 口径）"
        )
        return record

    selected_epoch = best_role.get("epoch")
    selected_metric = best_role.get("metric")
    epoch_entry = next((item for item in history if item.get("epoch") == selected_epoch), None)
    best_flow = selection.get("best_by_flow") or {}

    record.update({
        "available": True,
        "selected_epoch": selected_epoch,
        # 本格自身读数角色下的最佳实体 AP：C00/C01 是 max 口径，C10/C11 是 tail 口径。
        # 交互项与四格判据只用这个值，不跨口径混用。
        "best_entity_ap": selected_metric,
        # 选中轮次上的三项指标，供出表直接引用；max/tail 两个字段哪个缺失取决于该轮
        # 历史条目本身有没有算过（旧格式条目没有 validation_entity_ap_tail 键）。
        "validation_entity_ap": epoch_entry.get("validation_entity_ap") if epoch_entry else None,
        "validation_entity_ap_tail": epoch_entry.get("validation_entity_ap_tail") if epoch_entry else None,
        "validation_flow_ap": epoch_entry.get("validation_flow_ap") if epoch_entry else None,
        "best_flow_ap": best_flow.get("metric"),
        "best_flow_epoch": best_flow.get("epoch"),
        "selection_rules_agree": selected_epoch == best_flow.get("epoch"),
        "wall_seconds": selection.get("wall_seconds"),
        "target_reads": selection.get("target_reads"),
        "resource": selection.get("resource"),
        "entity_ap_by_epoch": [
            {
                "epoch": item.get("epoch"),
                "entity_ap": item.get("validation_entity_ap"),
                "entity_ap_tail": item.get("validation_entity_ap_tail"),
                "flow_ap": item.get("validation_flow_ap"),
            }
            for item in history
        ],
    })
    return record


def evaluate_criteria(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """四格判据：两单机制均严格超 C00，C11 取最大，交互 I 为正。

    判据阈值与朱焱雷学位论文对标裁决冻结时（`RWKV第三章恢复卡.md` 第 29 行）一致，
    未做任何改动：`C10 > C00`、`C01 > C00`、`C11 >= max(C10, C01)`、`I = C11-C10-C01+C00 > 0`。
    每格用的是它自己读数角色下的实体 AP（``collect_cell`` 已按 ``metric_role`` 选好），
    不跨口径比较。任一格读数缺失时只报告 ``complete=False``，不猜测、不外推、不用其他
    口径的数值代入缺格。
    """
    readings = {
        item["cell"]: item.get("best_entity_ap")
        for item in cells
        if item.get("available") and item.get("best_entity_ap") is not None
    }
    metric_roles = {item["cell"]: item.get("metric_role") for item in cells}
    missing = [item["cell"] for item in cells if item["cell"] not in readings]
    verdict: Dict[str, Any] = {
        "metric": "own_metric_role_validation_entity_ap（C00/C01 为 max 口径，C10/C11 为 tail 口径，见 metric_roles）",
        "metric_roles": metric_roles,
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
    parser = argparse.ArgumentParser(description="第三章 FT 四格读数汇总（只读、只披露）")
    parser.add_argument("--runs-root", required=True, help="诊断运行根目录，通常是 runs/diagnostics")
    parser.add_argument("--output", default=None, help="汇总落盘路径；缺省写入 runs-root/ch3-ft-four-cell-summary.json")
    parser.add_argument("--stdout", action="store_true", help="同时把汇总打印到标准输出")
    parser.add_argument(
        "--cell-set", choices=sorted(CELL_SETS), default="new",
        help="四格运行身份集合：new=当前活动候选（尾部聚合×BER，默认），"
             "legacy=已否决的旧 CEM-BER 四格（只用于读取历史制品）",
    )
    args = parser.parse_args()

    runs_root = Path(args.runs_root).expanduser().resolve()
    if not runs_root.is_dir():
        print(f"[错误] 运行根目录不存在：{runs_root}", file=sys.stderr)
        return 2

    cell_specs = CELL_SETS[args.cell_set]
    cells = [collect_cell(runs_root, spec) for spec in cell_specs]
    summary = {
        "schema_version": "ch3-ft-four-cell-summary-v2",
        "cell_set": args.cell_set,
        "cell_set_legend": CELL_SET_LEGEND[args.cell_set],
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
                f"{item['cell']} {item['display_name']}（{item['metric_role']} 口径）："
                f"实体 AP {item['best_entity_ap']}（第 {item['selected_epoch']} 轮／共 "
                f"{item['epochs_completed']} 轮），逐流 AP {item['validation_flow_ap']}，"
                f"检查点 {item['selected_checkpoint_path']}"
                f"{'' if item['selected_checkpoint_exists'] else '（文件缺失）'}，"
                f"state={item['state']} exit={item['exit_code']}",
                file=sys.stderr,
            )
        else:
            reason = item.get("missing_reason", "未知原因")
            print(
                f"{item['cell']} {item['display_name']}（{item['metric_role']} 口径）：不可用——{reason}，"
                f"state={item['state']} inflight={item['has_inflight_checkpoint']}",
                file=sys.stderr,
            )
    print(f"汇总已写入 {output}（cell_set={args.cell_set}）", file=sys.stderr)

    if args.stdout:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
