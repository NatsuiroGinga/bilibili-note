# -*- coding: utf-8 -*-
"""第三章全模型统一指标总表构建工具——读取层与 schema 适配器（任务 2）。

本文件当前只实现读取层：把三套异构制品（`baselines_full`、`fairsel_2x2`、
`protocol_a_v1`、`xgb_cpa_elp` 四种 schema）归一化到统一字段字典，并提供
`--probe` 子命令对配置中每个 `available: true` 的模型条目做单点读取验证。

分表、判优（同一评价池内全精度自动判优）与最终输出层由后续任务（任务 3、
任务 4）实现，本文件不提前实现。

关键点——`cell` 字段的语义按 schema 不同：
  - `baselines_full`：`cell` 是从 JSON 根开始的点分路径（如
    `models.random_forest_dijk2024`），需逐段下钻。
  - 其余三种：`cell` 是短键（如 `C11`），由各自适配器自己加前缀。

四个运行根的绝对路径不写死在本文件内，一律由命令行 `--root name=path`
注入（可重复传入）。
"""

import argparse
import json
from pathlib import Path
from typing import Any, Callable

# 三表共用的列顺序来源：display_name 来自配置条目本身，其余键与
# read_source() 归一化后的统一字段字典键一致。分表、判优、渲染层的列顺序
# 均以此列表为准，避免三张表各自发明一套列名。
CANONICAL_COLUMNS: list[str] = [
    "display_name",
    "flow_ap",
    "entity_ap",
    "max_entity_ap",
    "dr_curve",
    "selected_epoch",
    "validation_flow_ap",
    "selected_p",
    "parameter_count",
    "training_seconds",
    "evaluation_seconds",
    "gpu_hours",
    "peak_gpu_mib",
    "peak_rss_mib",
]


def _adapt_baselines_full(doc: dict, cell: str) -> dict | None:
    """适配 `baselines_full` schema。

    `cell` 是从 JSON 根开始的点分路径（如 `models.random_forest_dijk2024`），
    需逐段下钻。该来源只持久化 4% FPR 单档检出率，其余五档检出率不可得。
    """
    node = doc
    for part in cell.split("."):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    if not node:
        return None
    return {
        "flow_ap": node.get("flow_ap"),
        "entity_ap": node.get("ent_ap_max"),
        "max_entity_ap": node.get("ent_ap_max"),
        "dr_curve": {"fpr_0.04": node.get("dr_at_fpr_max")},
        "dr_curve_note": "该来源只持久化 4% 单档，其余五档不可得",
        "selected_epoch": node.get("sel_epoch"),
        "validation_flow_ap": node.get("val_ap"),
        "selected_p": node.get("p"),
        "parameter_count": node.get("npar"),
        "training_seconds": node.get("tr"),
        "evaluation_seconds": node.get("ev"),
        "total_seconds": None,
        "gpu_hours": None,
        "peak_gpu_mib": None,
        "peak_rss_mib": None,
    }


def _adapt_fairsel_2x2(doc: dict, cell: str) -> dict | None:
    """适配 `fairsel_2x2` schema。

    `cell` 是短键（如 `C11`），取 `doc["cells"][cell]`。主口径实体 AP 在
    启用幂平均的格（`C01`、`C11`）取 `e_lp`，未启用的格（`C00`、`C10`）取
    `e_max`——同名不同义，不能一律取 `e_max`。该来源只持久化 4% FPR 单档
    检出率，其余五档不可得。
    """
    node = doc.get("cells", {}).get(cell)
    if not node:
        return None
    uses_lp = cell in ("C01", "C11")
    return {
        "flow_ap": node.get("fap"),
        "entity_ap": node.get("e_lp") if uses_lp else node.get("e_max"),
        "max_entity_ap": node.get("e_max"),
        "dr_curve": {"fpr_0.04": node.get("dr_main")},
        "dr_curve_note": "该来源只持久化 4% 单档，其余五档不可得",
        "selected_epoch": node.get("sel_epoch"),
        "validation_flow_ap": node.get("val_ap"),
        "selected_p": node.get("p"),
        "parameter_count": node.get("npar"),
        "training_seconds": node.get("tr"),
        "evaluation_seconds": node.get("ev"),
        "total_seconds": None,
        "gpu_hours": None,
        "peak_gpu_mib": None,
        "peak_rss_mib": None,
    }


def _adapt_protocol_a_v1(doc: dict, cell: str) -> dict | None:
    """适配 `protocol_a_v1` schema。

    `cell` 是短键，选择阶段取 `source_selection.cells[cell]`，评价阶段取
    `target_evaluation.cells[cell]["target"]`。六档检出率、资源与显存峰值
    均可得。
    """
    sel = doc.get("source_selection", {}).get("cells", {}).get(cell, {})
    tgt = doc.get("target_evaluation", {}).get("cells", {}).get(cell, {}).get("target", {})
    res = doc.get("resource", {})
    if not tgt:
        return None
    return {
        "flow_ap": tgt.get("flow_average_precision"),
        "entity_ap": tgt.get("entity_average_precision"),
        "max_entity_ap": tgt.get("maximum_entity_average_precision"),
        "dr_curve": dict(tgt.get("dr_at_fpr", {})),
        "dr_curve_note": "",
        "selected_epoch": sel.get("selected_epoch"),
        "validation_flow_ap": sel.get("validation_flow_ap"),
        "selected_p": sel.get("p_at_selection"),
        "parameter_count": res.get("parameter_count") or doc.get("model", {}).get("parameter_count"),
        "training_seconds": res.get("training_wall_seconds_sum"),
        "evaluation_seconds": res.get("evaluation_wall_seconds_sum"),
        "total_seconds": None,
        "gpu_hours": res.get("gpu_hours"),
        "peak_gpu_mib": res.get("peak_gpu_allocated_mib"),
        "peak_rss_mib": res.get("peak_process_rss_mib"),
    }


def _adapt_xgb_cpa_elp(doc: dict, cell: str) -> dict | None:
    """适配 `xgb_cpa_elp` schema。

    `cell` 是短键，取 `doc["cells"][cell]`。树集成不适用可训练参数量；
    该来源在启用幂平均（`p` 非空）时未单独持久化「取最大」聚合读数，此时
    `max_entity_ap` 置 `None` 并记原因。
    """
    node = doc.get("cells", {}).get(cell)
    if not node:
        return None
    return {
        "flow_ap": node.get("flow_ap"),
        "entity_ap": node.get("ent_ap"),
        "max_entity_ap": node.get("ent_ap") if node.get("p") is None else None,
        "max_entity_ap_note": "该来源未单独持久化取最大聚合读数" if node.get("p") is not None else "",
        "dr_curve": dict(node.get("dr_curve", {})),
        "dr_curve_note": "",
        "selected_epoch": None,
        "validation_flow_ap": None,
        "selected_p": node.get("p"),
        "parameter_count": None,
        "parameter_count_note": "树集成不适用可训练参数量",
        "training_seconds": None,
        "training_seconds_note": "该来源只持久化总耗时，未拆分训练与评价",
        "evaluation_seconds": None,
        "evaluation_seconds_note": "该来源只持久化总耗时，未拆分训练与评价",
        "total_seconds": doc.get("timing", {}).get("total_seconds"),
        "gpu_hours": None,
        "peak_gpu_mib": None,
        "peak_rss_mib": None,
    }


ADAPTERS: dict[str, Callable[[dict, str], dict | None]] = {
    "baselines_full": _adapt_baselines_full,
    "fairsel_2x2": _adapt_fairsel_2x2,
    "protocol_a_v1": _adapt_protocol_a_v1,
    "xgb_cpa_elp": _adapt_xgb_cpa_elp,
}


def read_source(root_path: str, model_entry: dict) -> dict | None:
    """读取单个模型的原始制品并归一化为统一字段字典。

    Args:
        root_path: 该模型条目所属 runs 根的绝对（或相对当前工作目录的）
            路径，由调用方按 `model_entry["root"]` 从 `--root name=path`
            映射中解析后传入；本函数不解析根名，也不写死任何绝对路径。
        model_entry: 来自 `configs/ch3-metrics-table-sources-v1.json` 的
            单条模型配置字典，须含 `relative_path`、`source_schema`、
            `cell`。

    Returns:
        统一字段字典（键见模块顶部 `CANONICAL_COLUMNS` 说明），或在制品
        文件缺失、JSON 解析失败、目标 schema 未知、目标 cell 取不到数据
        时返回 `None`。单个字段取不到时该字段置 `None`，本函数不抛异常。
    """
    relative_path = model_entry.get("relative_path")
    source_schema = model_entry.get("source_schema")
    cell = model_entry.get("cell")
    if not relative_path or not source_schema or cell is None:
        return None

    adapter = ADAPTERS.get(source_schema)
    if adapter is None:
        return None

    full_path = Path(root_path) / relative_path
    if full_path.suffix != ".json" or not full_path.is_file():
        return None

    try:
        with full_path.open("r", encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(doc, dict):
        return None

    return adapter(doc, cell)


def _parse_root_args(root_args: list[str]) -> dict[str, str]:
    """把重复传入的 `--root name=path` 解析为 {根名: 路径} 字典。"""
    roots: dict[str, str] = {}
    for item in root_args:
        if "=" not in item:
            raise ValueError(f"--root 参数格式必须为 name=path，收到：{item}")
        name, path = item.split("=", 1)
        roots[name] = path
    return roots


def _run_probe(config_path: str, root_args: list[str]) -> None:
    """对配置中每个模型条目做单点读取验证并打印结果。

    `available: true` 的条目：解析其 `root` 对应的根路径，调用
    `read_source` 后打印 `display_name`、`flow_ap`、`entity_ap`。
    `available: false` 的条目：不调用适配器，只打印 `display_name` 与
    `pending_reason`。
    """
    roots = _parse_root_args(root_args)
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    for entry in config.get("models", []):
        display_name = entry.get("display_name")

        if not entry.get("available"):
            print(f"{display_name}\tpending_reason={entry.get('pending_reason')}")
            continue

        root_name = entry.get("root")
        root_path = roots.get(root_name)
        if root_path is None:
            print(f"{display_name}\t错误：--root 未提供根 {root_name!r} 的路径映射")
            continue

        result = read_source(root_path, entry)
        if result is None:
            print(f"{display_name}\t错误：读取失败，或目标制品文件/字段缺失")
            continue

        print(f"{display_name}\tflow_ap={result.get('flow_ap')}\tentity_ap={result.get('entity_ap')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="第三章全模型统一指标总表构建工具")
    parser.add_argument("--probe", action="store_true", help="对配置中每个可用模型条目做单点读取验证")
    parser.add_argument("--config", type=str, default=None, help="模型来源配置文件路径")
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        metavar="name=path",
        help="运行根目录映射，可重复传入，例如 --root main=/abs/path/to/runs",
    )
    args = parser.parse_args()

    if args.probe:
        if not args.config:
            parser.error("--probe 需要同时提供 --config")
        _run_probe(args.config, args.root)
        return

    parser.error("当前仅实现 --probe 子命令；分表、判优、输出层由后续任务实现")


if __name__ == "__main__":
    main()
