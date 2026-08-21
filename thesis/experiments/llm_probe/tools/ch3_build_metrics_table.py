# -*- coding: utf-8 -*-
"""从第三章原始运行制品机械生成统一指标总表。"""

import argparse
import ast
import csv
import hashlib
import json
import struct
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


FPR_BUDGETS = (
    ("fpr_0.001", "dr_fpr_0.001"),
    ("fpr_0.005", "dr_fpr_0.005"),
    ("fpr_0.01", "dr_fpr_0.01"),
    ("fpr_0.02", "dr_fpr_0.02"),
    ("fpr_0.04", "dr_fpr_0.04"),
    ("fpr_0.08", "dr_fpr_0.08"),
)

PERFORMANCE_SCALAR_COLUMNS = [
    "flow_ap",
    "entity_ap",
    "max_entity_ap",
    *(column for _, column in FPR_BUDGETS),
]

UNALERTED_RATE_COLUMNS = [
    f"unalerted_rate_{source_key}" for source_key, _ in FPR_BUDGETS
]

FIRST_ALERT_COLUMNS = [
    "first_alert_axis",
    "time_delay_available",
    *UNALERTED_RATE_COLUMNS,
    "timely_detection_curve_summary",
    "timely_detection_curve_artifact",
    "first_alert_delay_summary",
    "first_alert_definition",
]

RESOURCE_METRIC_COLUMNS = [
    "scale_value",
    "scale_unit",
    "model_weight_bytes",
    "training_seconds",
    "selection_seconds",
    "inference_seconds",
    "evaluation_seconds",
    "total_seconds",
    "gpu_hours",
    "training_throughput",
    "evaluation_throughput",
    "peak_gpu_mib",
    "peak_rss_mib",
    "checkpoint_bytes",
    "interruption_count",
    "recovery_count",
    "recomputed_units",
]

PARETO_COLUMNS = [
    "pareto_status",
    "dominated_by",
    "dominates",
    "pareto_missing_reasons",
]

CANONICAL_COLUMNS = [
    "display_name",
    "config_type",
    "differentiable",
    "run_id",
    "selection_pool",
    "evaluation_pool",
    "selection_metric",
    "selection_score",
    "selected_epoch",
    "validation_flow_ap",
    "selected_p",
    "selection_protocol",
    "flow_ap",
    "entity_ap",
    "max_entity_ap",
    *(column for _, column in FPR_BUDGETS),
    "dr_curve_summary",
    "dr_curve_artifact",
    *FIRST_ALERT_COLUMNS,
    "source_performance_pool",
    "source_flow_ap",
    "source_entity_ap",
    "source_max_entity_ap",
    *(f"source_{column}" for _, column in FPR_BUDGETS),
    "source_dr_curve_summary",
    "source_dr_curve_artifact",
    *(f"source_{column}" for column in FIRST_ALERT_COLUMNS),
    "model_scale",
    "parameter_count",
    *RESOURCE_METRIC_COLUMNS,
    "time_scope",
    "evidence_level",
    "source_path",
    "pending_reason",
    "missing_reasons",
]

LSPR23_PERFORMANCE_COLUMNS = [
    "display_name",
    "config_type",
    "differentiable",
    "run_id",
    "evaluation_pool",
    *PERFORMANCE_SCALAR_COLUMNS,
    "dr_curve_summary",
    "dr_curve_artifact",
    *FIRST_ALERT_COLUMNS,
    "evidence_level",
    "source_path",
    "pending_reason",
    "missing_reasons",
    "best_flags",
    *PARETO_COLUMNS,
]

LSPR23_COLUMNS = [
    "display_name",
    "config_type",
    "differentiable",
    "run_id",
    "selection_pool",
    "selection_metric",
    "selection_score",
    "selected_epoch",
    "validation_flow_ap",
    "selected_p",
    "selection_protocol",
    "evidence_level",
    "source_path",
    "pending_reason",
    "missing_reasons",
    "best_flags",
]

LSPR24_COLUMNS = [
    "display_name",
    "config_type",
    "differentiable",
    "run_id",
    "evaluation_pool",
    "flow_ap",
    "entity_ap",
    "max_entity_ap",
    *(column for _, column in FPR_BUDGETS),
    "dr_curve_summary",
    "dr_curve_artifact",
    *FIRST_ALERT_COLUMNS,
    "evidence_level",
    "source_path",
    "pending_reason",
    "missing_reasons",
    "best_flags",
    *PARETO_COLUMNS,
]

RESOURCE_COLUMNS = [
    "display_name",
    "config_type",
    "differentiable",
    "run_id",
    "model_scale",
    "parameter_count",
    *RESOURCE_METRIC_COLUMNS,
    "time_scope",
    "evidence_level",
    "source_path",
    "pending_reason",
    "missing_reasons",
    *PARETO_COLUMNS,
]

COLUMN_LABELS = {
    "display_name": "模型",
    "config_type": "配置类型",
    "differentiable": "可微",
    "run_id": "运行身份",
    "selection_pool": "选择池",
    "evaluation_pool": "评价池",
    "selection_metric": "选择指标",
    "selection_score": "选择分数",
    "selected_epoch": "选定轮次",
    "validation_flow_ap": "验证逐流AP",
    "selected_p": "选定幂指数",
    "selection_protocol": "选择口径",
    "flow_ap": "逐流AP",
    "entity_ap": "实体AP",
    "max_entity_ap": "最大实体AP",
    "dr_fpr_0.001": "DR@0.1%FPR",
    "dr_fpr_0.005": "DR@0.5%FPR",
    "dr_fpr_0.01": "DR@1%FPR",
    "dr_fpr_0.02": "DR@2%FPR",
    "dr_fpr_0.04": "DR@4%FPR",
    "dr_fpr_0.08": "DR@8%FPR",
    "dr_curve_summary": "完整曲线摘要",
    "dr_curve_artifact": "完整曲线制品",
    "unalerted_rate_fpr_0.001": "0.1%FPR未告警率",
    "unalerted_rate_fpr_0.005": "0.5%FPR未告警率",
    "unalerted_rate_fpr_0.01": "1%FPR未告警率",
    "unalerted_rate_fpr_0.02": "2%FPR未告警率",
    "unalerted_rate_fpr_0.04": "4%FPR未告警率",
    "unalerted_rate_fpr_0.08": "8%FPR未告警率",
    "timely_detection_curve_summary": "按时检出曲线摘要",
    "timely_detection_curve_artifact": "按时检出曲线制品",
    "first_alert_axis": "首次告警横轴",
    "time_delay_available": "真实秒时延可用",
    "first_alert_delay_summary": "首次告警延迟摘要",
    "first_alert_definition": "首次告警定义",
    "model_scale": "模型规模",
    "parameter_count": "参数量",
    "scale_value": "规模数值",
    "scale_unit": "规模单位",
    "model_weight_bytes": "模型权重字节",
    "training_seconds": "训练时间/秒",
    "selection_seconds": "选模时间/秒",
    "inference_seconds": "纯推理时间/秒",
    "evaluation_seconds": "评价时间/秒",
    "total_seconds": "总时间/秒",
    "gpu_hours": "GPU小时",
    "training_throughput": "训练吞吐/样本每秒",
    "evaluation_throughput": "评价吞吐/样本每秒",
    "peak_gpu_mib": "峰值显存/MiB",
    "peak_rss_mib": "峰值主存RSS/MiB",
    "checkpoint_bytes": "检查点字节",
    "interruption_count": "中断次数",
    "recovery_count": "恢复次数",
    "recomputed_units": "重复计算量",
    "time_scope": "时间口径",
    "evidence_level": "证据等级",
    "source_path": "原始路径",
    "pending_reason": "待补原因",
    "pareto_status": "帕累托状态",
    "dominated_by": "支配者",
    "dominates": "被其支配",
}

TABLE_TITLES = {
    "lspr23-selection": "LSPR23 源年选择表",
    "lspr23-performance": "LSPR23 源年完整性能表",
    "lspr24-evaluation": "LSPR24 已访问目标年描述性评价表",
    "resource": "资源开销表",
}


def _blank_result() -> dict[str, Any]:
    metadata = {
        "display_name",
        "config_type",
        "differentiable",
        "run_id",
        "evidence_level",
        "source_path",
        "pending_reason",
        "missing_reasons",
    }
    return {column: None for column in CANONICAL_COLUMNS if column not in metadata}


def _with_target_fields(result: dict[str, Any], dr_curve: dict[str, Any]) -> dict[str, Any]:
    for source_key, column in FPR_BUDGETS:
        result[column] = dr_curve.get(source_key)
    return result


def _with_source_fields(result: dict[str, Any], dr_curve: dict[str, Any]) -> dict[str, Any]:
    for source_key, column in FPR_BUDGETS:
        result[f"source_{column}"] = dr_curve.get(source_key)
    return result


def _adapt_baselines_full(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    node: Any = doc
    for part in cell.split("."):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    if not node:
        return None
    validation_score = node.get("val_ap_pred_avg")
    is_neural = node.get("npar") is not None
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23实体不相交验证集" if validation_score is not None else "LSPR23固定配置训练集",
            "evaluation_pool": "LSPR24已访问目标年描述性评价池",
            "selection_metric": "前5名轮次预测平均的逐流AP" if validation_score is not None else None,
            "selection_score": validation_score,
            "selected_epoch": node.get("topk_epochs"),
            "validation_flow_ap": validation_score,
            "selection_protocol": doc.get("protocol"),
            "source_performance_pool": "LSPR23实体不相交验证集" if validation_score is not None else None,
            "source_flow_ap": validation_score,
            "flow_ap": node.get("flow_ap"),
            "entity_ap": node.get("ent_ap_max"),
            "max_entity_ap": node.get("ent_ap_max"),
            "dr_curve_summary": "仅持久化4% FPR单点；无完整告警预算曲线",
            "model_scale": node.get("scale"),
            "parameter_count": node.get("npar"),
            "scale_value": node.get("npar") or node.get("n_trees"),
            "scale_unit": "parameter" if node.get("npar") is not None else "tree",
            "training_seconds": node.get("train_seconds"),
            "time_scope": "训练墙钟；未拆分目标年纯推理与指标计算" if is_neural else "固定树配置训练墙钟；未拆分目标年纯推理与指标计算",
        }
    )
    return _with_target_fields(result, {"fpr_0.04": node.get("dr_at_fpr_max")})


def _adapt_fairsel_2x2(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    node = doc.get("cells", {}).get(cell)
    if not node:
        return None
    uses_lp = cell in {"C01", "C11"}
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23实体不相交验证集",
            "evaluation_pool": "LSPR24已访问目标年描述性评价池",
            "selection_metric": "单轮逐流AP",
            "selection_score": node.get("val_ap"),
            "selected_epoch": node.get("sel_epoch"),
            "validation_flow_ap": node.get("val_ap"),
            "selected_p": node.get("p"),
            "selection_protocol": doc.get("protocol"),
            "source_performance_pool": "LSPR23实体不相交验证集",
            "source_flow_ap": node.get("val_ap"),
            "flow_ap": node.get("fap"),
            "entity_ap": node.get("e_lp") if uses_lp else node.get("e_max"),
            "max_entity_ap": node.get("e_max"),
            "dr_curve_summary": "仅持久化4% FPR单点；无完整告警预算曲线",
            "model_scale": f"{node.get('npar'):,}个可训练参数" if isinstance(node.get("npar"), int) else None,
            "parameter_count": node.get("npar"),
            "scale_value": node.get("npar"),
            "scale_unit": "parameter" if node.get("npar") is not None else None,
            "training_seconds": node.get("tr"),
            "evaluation_seconds": node.get("ev"),
            "time_scope": "单格训练墙钟；评价时间含预测与指标计算，不等同纯推理",
        }
    )
    return _with_target_fields(result, {"fpr_0.04": node.get("dr_main")})


def _adapt_protocol_a_v1(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    selection_cells = doc.get("source_selection", {}).get("cells", {})
    selection = selection_cells.get(cell, {})
    target = doc.get("target_evaluation", {}).get("cells", {}).get(cell, {}).get("target", {})
    resource = doc.get("resource", {})
    if not target:
        return None
    parameter_count = resource.get("parameter_count") or doc.get("model", {}).get("parameter_count")
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23实体不相交验证集",
            "evaluation_pool": "LSPR24已访问目标年描述性评价池",
            "selection_metric": "单轮逐流AP",
            "selection_score": selection.get("validation_flow_ap"),
            "selected_epoch": selection.get("selected_epoch"),
            "validation_flow_ap": selection.get("validation_flow_ap"),
            "selected_p": selection.get("p_at_selection"),
            "selection_protocol": doc.get("source_selection", {}).get("protocol") or "协议A：源年验证集单轮逐流AP择优",
            "source_performance_pool": "LSPR23实体不相交验证集",
            "source_flow_ap": selection.get("validation_flow_ap"),
            "flow_ap": target.get("flow_average_precision"),
            "entity_ap": target.get("entity_average_precision"),
            "max_entity_ap": target.get("maximum_entity_average_precision"),
            "model_scale": f"{parameter_count:,}个可训练参数" if isinstance(parameter_count, int) else None,
            "parameter_count": parameter_count,
            "scale_value": parameter_count,
            "scale_unit": "parameter" if parameter_count is not None else None,
            "training_seconds": resource.get("training_wall_seconds_sum"),
            "evaluation_seconds": resource.get("evaluation_wall_seconds_sum"),
            "total_seconds": (
                resource.get("training_wall_seconds_sum", 0.0)
                + resource.get("target_stage_wall_seconds", 0.0)
            )
            if resource.get("training_wall_seconds_sum") is not None
            and resource.get("target_stage_wall_seconds") is not None
            else None,
            "gpu_hours": resource.get("gpu_hours"),
            "peak_gpu_mib": resource.get("peak_gpu_allocated_mib")
            or max(
                (item.get("peak_gpu_allocated_mib", 0.0) for item in selection_cells.values()),
                default=0.0,
            )
            or None,
            "peak_rss_mib": resource.get("peak_process_rss_mib")
            or max(
                (item.get("peak_process_rss_mib", 0.0) for item in selection_cells.values()),
                default=0.0,
            )
            or None,
            "checkpoint_bytes": sum(
                item.get("checkpoint", {}).get("bytes", 0)
                for item in selection_cells.values()
                if isinstance(item, dict)
            ) or None,
            "time_scope": "四格训练与评价墙钟之和；评价时间含预测与指标计算，不等同纯推理",
        }
    )
    return _with_target_fields(result, dict(target.get("dr_at_fpr", {})))


def _adapt_xgb_cpa_elp(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    node = doc.get("cells", {}).get(cell)
    if not node:
        return None
    input_view = node.get("input_view")
    p_selection = doc.get("p_selection", {}).get(input_view, {})
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23三折实体OOF",
            "evaluation_pool": "LSPR24已访问目标年描述性评价池",
            "selection_metric": "实体OOF AP",
            "selection_score": p_selection.get("oof_ent_ap_at_p"),
            "selected_p": node.get("p"),
            "selection_protocol": doc.get("adapter_selection", {}).get("criterion"),
            "source_performance_pool": "LSPR23三折实体OOF",
            "source_entity_ap": p_selection.get("oof_ent_ap_at_p"),
            "flow_ap": node.get("flow_ap"),
            "entity_ap": node.get("ent_ap"),
            "max_entity_ap": node.get("ent_ap") if node.get("p") is None else None,
            "dr_curve_summary": "持久化六个预设FPR工作点；无全可达预算曲线制品",
            "model_scale": f"{doc.get('num_boost_round')}棵提升树" if doc.get("num_boost_round") is not None else None,
            "scale_value": doc.get("num_boost_round"),
            "scale_unit": "tree" if doc.get("num_boost_round") is not None else None,
            "total_seconds": doc.get("timing", {}).get("total_seconds"),
            "time_scope": "源年拟合与目标年评价总墙钟；未拆分训练、纯推理和指标计算",
        }
    )
    return _with_target_fields(result, dict(node.get("dr_curve", {})))


def _adapt_rwkv7_protocol_a_v1(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    """适配 RWKV-7 协议 A 聚合结果及其专用资源键。"""
    result = _adapt_protocol_a_v1(doc, cell)
    if result is None:
        return None
    resource = doc.get("resource", {})
    result.update(
        {
            "training_seconds": resource.get("source_training_wall_seconds"),
            "evaluation_seconds": resource.get("target_stage_wall_seconds"),
            "total_seconds": (
                resource.get("source_training_wall_seconds", 0.0)
                + resource.get("target_stage_wall_seconds", 0.0)
            )
            if resource.get("source_training_wall_seconds") is not None
            and resource.get("target_stage_wall_seconds") is not None
            else None,
            "gpu_hours": resource.get("gpu_hours"),
            "peak_rss_mib": resource.get("peak_process_rss_mib"),
            "time_scope": "源年四格训练与目标年四格评价总墙钟；未拆分纯推理与指标计算",
        }
    )
    return result


def _adapt_grande_source_q0_v1(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    """适配 GRANDE 源年 complete_metrics，不假造目标年指标。"""
    selection_root = doc.get("source_selection", {})
    winner = selection_root.get("winner") or doc.get("selected_candidate")
    if cell == "selected":
        if not isinstance(winner, dict):
            return None
        selected_key = winner.get("unit_key")
    else:
        selected_key = cell
    metrics = doc.get("complete_metrics", {}).get(selected_key, {})
    if not selected_key or not metrics:
        return None
    completed = selection_root.get("completed_structures", [])
    selected = next(
        (item for item in completed if item.get("unit_key") == selected_key),
        winner if isinstance(winner, dict) else None,
    )
    if not isinstance(selected, dict):
        return None
    resource = doc.get("resource", {})
    parameter_count = selected.get("parameter_count_framework")
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23实体不相交验证集",
            "selection_metric": "单轮逐流AP",
            "selection_score": selected.get("validation_flow_ap"),
            "selected_epoch": selected.get("selected_epoch"),
            "validation_flow_ap": selected.get("validation_flow_ap"),
            "selection_protocol": "协议A：源年验证集单轮逐流AP择优",
            "source_performance_pool": "LSPR23实体不相交验证集",
            "source_flow_ap": metrics.get("flow_average_precision"),
            "source_entity_ap": metrics.get("entity_average_precision"),
            "source_max_entity_ap": metrics.get("maximum_entity_average_precision"),
            "model_scale": f"{parameter_count:,}个可训练参数" if isinstance(parameter_count, int) else None,
            "parameter_count": parameter_count,
            "scale_value": parameter_count,
            "scale_unit": "parameter" if parameter_count is not None else None,
            "model_weight_bytes": selected.get("model_weight_bytes"),
            "training_seconds": resource.get("training_wall_seconds_sum"),
            "selection_seconds": resource.get("diagnostic_wall_seconds_sum"),
            "gpu_hours": resource.get("cumulative_gpu_hours"),
            "training_throughput": selected.get("training_valid_flows_per_second"),
            "evaluation_throughput": selected.get("diagnostic_flows_per_second"),
            "peak_gpu_mib": resource.get("peak_gpu_allocated_mib"),
            "peak_rss_mib": resource.get("peak_process_rss_mib"),
            "checkpoint_bytes": selected.get("checkpoint", {}).get("bytes"),
            "recovery_count": selected.get("resume_count"),
            "time_scope": "源年G-A/G-B选择总墙钟；诊断时间与训练时间分列",
            "_curve_cell": selected_key,
        }
    )
    return _with_source_fields(result, dict(metrics.get("dr_at_fpr", {})))


def _adapt_tabm32_protocol_a_v1(doc: dict[str, Any], cell: str) -> dict[str, Any] | None:
    """TabM32 使用独立版本化入口，制品形成前由清单保持 pending。"""
    return _adapt_protocol_a_v1(doc, cell)


def _adapt_full_mlp_complete_entity_lp_v1(
    doc: dict[str, Any], cell: str
) -> dict[str, Any] | None:
    """适配全容量多层感知机 BF16 O11 完整系统及双年度完整指标。"""
    selection = doc.get("source_selection", {}).get("cells", {}).get(cell, {})
    source = doc.get("source_year_table", {}).get(cell, {})
    target = doc.get("target_year_table", {}).get(cell, {})
    resource = doc.get("resource", {})
    model = doc.get("model", {})
    if not selection or not source or not target:
        return None
    parameter_count = model.get("parameter_count") or resource.get("parameter_count")
    trained_cells = set(doc.get("source_selection", {}).get("cells", {}))
    evaluated_flows = sum(
        int(table.get(branch, {}).get("flows_scored", 0))
        for table in (doc.get("source_year_table", {}), doc.get("target_year_table", {}))
        for branch in trained_cells
    )
    pure_inference_seconds = resource.get("pure_inference_seconds_sum")
    result = _blank_result()
    result.update(
        {
            "selection_pool": "LSPR23实体不相交验证集",
            "evaluation_pool": "LSPR24已访问目标年描述性评价池",
            "selection_metric": "单轮逐流AP",
            "selection_score": selection.get("validation_flow_ap"),
            "selected_epoch": selection.get("selected_epoch"),
            "validation_flow_ap": selection.get("validation_flow_ap"),
            "selected_p": selection.get("p_at_selection"),
            "selection_protocol": "协议A：源年验证集单轮逐流AP择优；O11为完整系统",
            "source_performance_pool": "LSPR23实体不相交验证集",
            "source_flow_ap": source.get("flow_average_precision"),
            "source_entity_ap": source.get("entity_average_precision"),
            "source_max_entity_ap": source.get("maximum_entity_average_precision"),
            "flow_ap": target.get("flow_average_precision"),
            "entity_ap": target.get("entity_average_precision"),
            "max_entity_ap": target.get("maximum_entity_average_precision"),
            "model_scale": f"{parameter_count:,}个可训练参数" if isinstance(parameter_count, int) else None,
            "parameter_count": parameter_count,
            "scale_value": parameter_count,
            "scale_unit": "parameter" if parameter_count is not None else None,
            "model_weight_bytes": resource.get("model_weight_bytes_fp32"),
            "training_seconds": resource.get("training_wall_seconds_sum"),
            "selection_seconds": resource.get("selection_seconds_sum"),
            "inference_seconds": pure_inference_seconds,
            "evaluation_seconds": resource.get("evaluation_wall_seconds_sum"),
            "total_seconds": resource.get("total_process_seconds_before_publish"),
            "gpu_hours": resource.get("gpu_hours"),
            "training_throughput": resource.get("effective_training_flows_per_second"),
            "evaluation_throughput": (
                evaluated_flows / pure_inference_seconds
                if evaluated_flows and isinstance(pure_inference_seconds, (int, float)) and pure_inference_seconds > 0
                else None
            ),
            "peak_gpu_mib": resource.get("peak_gpu_allocated_mib"),
            "peak_rss_mib": resource.get("peak_process_rss_mib"),
            "checkpoint_bytes": resource.get("selected_checkpoint_bytes_sum"),
            "interruption_count": resource.get("recovery_count_sum"),
            "recovery_count": resource.get("recovery_count_sum"),
            "recomputed_units": resource.get("recomputed_optimizer_steps_upper_bound_sum"),
            "time_scope": (
                "四格源年训练、选择与双年度评价总收据；中断次数按完成运行的恢复计数记录；"
                "评价吞吐按四个真实前向分支的源年与目标年流数除以纯推理总墙钟"
            ),
            "_curve_cell": cell,
            "_derive_dr_from_complete_curve": True,
            "_source_first_alert_metadata": source.get("first_alert"),
            "_first_alert_metadata": target.get("first_alert"),
        }
    )
    return result


ADAPTERS: dict[str, Callable[[dict[str, Any], str], dict[str, Any] | None]] = {
    "baselines_full": _adapt_baselines_full,
    "fairsel_2x2": _adapt_fairsel_2x2,
    "protocol_a_v1": _adapt_protocol_a_v1,
    "rwkv7_protocol_a_v1": _adapt_rwkv7_protocol_a_v1,
    "grande_source_q0_v1": _adapt_grande_source_q0_v1,
    "tabm32_protocol_a_v1": _adapt_tabm32_protocol_a_v1,
    "full_mlp_complete_entity_lp_v1": _adapt_full_mlp_complete_entity_lp_v1,
    "xgb_cpa_elp": _adapt_xgb_cpa_elp,
}


def read_source(root_path: str, model_entry: dict[str, Any]) -> dict[str, Any] | None:
    """读取单个JSON来源，并用配置指定的模式适配为统一字段。"""
    relative_path = model_entry.get("relative_path")
    adapter = ADAPTERS.get(model_entry.get("source_schema"))
    cell = model_entry.get("cell")
    if not relative_path or adapter is None or cell is None:
        return None
    source_path = Path(root_path) / relative_path
    if source_path.suffix != ".json" or not source_path.is_file():
        return None
    try:
        document = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return adapter(document, cell) if isinstance(document, dict) else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_provenance(path: Path, role: str, records: dict[str, dict[str, Any]]) -> None:
    absolute = path.resolve()
    key = str(absolute)
    if key not in records:
        records[key] = {
            "absolute_path": key,
            "sha256": _sha256(absolute),
            "bytes": absolute.stat().st_size,
            "read_at_utc": datetime.now(timezone.utc).isoformat(),
            "roles": [],
        }
    if role not in records[key]["roles"]:
        records[key]["roles"].append(role)


def _load_auxiliary_json(path: Path) -> dict[str, Any] | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return document if isinstance(document, dict) else None


def _npy_header(handle: Any) -> dict[str, Any]:
    if handle.read(6) != b"\x93NUMPY":
        raise ValueError("NPZ成员不是NPY数组")
    major, _minor = struct.unpack("BB", handle.read(2))
    length_size = 2 if major == 1 else 4
    length_format = "<H" if length_size == 2 else "<I"
    header_length = struct.unpack(length_format, handle.read(length_size))[0]
    header = ast.literal_eval(handle.read(header_length).decode("latin1").strip())
    if not isinstance(header, dict):
        raise ValueError("NPY头不是对象")
    return header


def _npy_shape(handle: Any) -> tuple[int, ...]:
    header = _npy_header(handle)
    shape = header.get("shape")
    if not isinstance(shape, tuple):
        raise ValueError("NPY头缺少shape")
    return shape


def _read_npy_vector(handle: Any) -> list[int | float]:
    """只读取帕累托比较需要的一维数值NPY，避免依赖NumPy。"""
    header = _npy_header(handle)
    shape = header.get("shape")
    if not isinstance(shape, tuple) or len(shape) != 1 or header.get("fortran_order") is not False:
        raise ValueError("帕累托曲线只接受C序一维NPY数组")
    formats = {
        "<f8": "<d",
        "<f4": "<f",
        "<i8": "<q",
        "<i4": "<i",
        "<u8": "<Q",
        "<u4": "<I",
    }
    item_format = formats.get(header.get("descr"))
    if item_format is None:
        raise ValueError(f"帕累托曲线NPY类型不受支持：{header.get('descr')}")
    item_size = struct.calcsize(item_format)
    payload = handle.read()
    expected = shape[0] * item_size
    if len(payload) != expected:
        raise ValueError(f"NPY载荷字节数不符：期望{expected}，实际{len(payload)}")
    return [item[0] for item in struct.iter_unpack(item_format, payload)]


def _npz_shapes(path: Path, prefix: str) -> dict[str, tuple[int, ...]]:
    shapes: dict[str, tuple[int, ...]] = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith(prefix) and name.endswith(".npy"):
                with archive.open(name) as handle:
                    shapes[name[:-4]] = _npy_shape(handle)
    return shapes


def _npz_vectors(path: Path, names: list[str]) -> dict[str, list[int | float]]:
    vectors: dict[str, list[int | float]] = {}
    with zipfile.ZipFile(path) as archive:
        available = set(archive.namelist())
        for name in names:
            member = f"{name}.npy"
            if member not in available:
                continue
            with archive.open(member) as handle:
                vectors[name] = _read_npy_vector(handle)
    return vectors


def _enrich_neural_resource(
    result: dict[str, Any],
    root: Path,
    entry: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
) -> None:
    relative = entry.get("selection_relative_path")
    if not relative:
        return
    path = root / relative
    if not path.is_file():
        return
    _record_provenance(path, f"{entry['display_name']}的选择与显存收据", provenance)
    document = _load_auxiliary_json(path)
    if document is None:
        return
    model_key = str(entry.get("cell", "")).split(".")[-1]
    architecture = document.get("architectures", {}).get(model_key, {})
    chosen_lr = architecture.get("chosen_lr")
    candidate = next(
        (item for item in architecture.get("candidates", []) if item.get("lr") == chosen_lr),
        None,
    )
    if candidate and candidate.get("peak_gib") is not None:
        result["peak_gpu_mib"] = candidate["peak_gib"] * 1024.0


def _apply_complete_curve(
    result: dict[str, Any],
    artifact_path: Path,
    member_prefix: str,
    fields: list[str],
    scope_prefix: str,
    derive_dr_from_curve: bool,
) -> None:
    expected_names = [f"{member_prefix}__{field}" for field in fields]
    shapes = _npz_shapes(artifact_path, f"{member_prefix}__")
    expected_shapes = [shapes.get(name) for name in expected_names]
    if any(shape is None or len(shape) != 1 for shape in expected_shapes):
        return
    point_counts = {shape[0] for shape in expected_shapes if shape is not None}
    if len(point_counts) != 1:
        return
    vector_names = [
        f"{member_prefix}__n_false_positive_entity",
        f"{member_prefix}__realized_fpr",
        f"{member_prefix}__detection_rate",
    ]
    vectors = _npz_vectors(artifact_path, vector_names)
    if any(name not in vectors for name in vector_names):
        return
    negative_budget, realized_fpr, detection_rate = (vectors[name] for name in vector_names)
    if not (len(negative_budget) == len(realized_fpr) == len(detection_rate)):
        return
    point_count = next(iter(point_counts))
    suffix = "；六档DR按realized_fpr不超过名义预算的最接近实际可达点重算" if derive_dr_from_curve else ""
    result[f"{scope_prefix}dr_curve_summary"] = (
        f"完整可达负实体预算曲线，共{point_count}个预算点；字段："
        + "、".join(fields)
        + suffix
    )
    result[f"{scope_prefix}dr_curve_artifact"] = f"{artifact_path.resolve()}#{member_prefix}"
    result[f"_{scope_prefix}dr_curve_points"] = {
        int(budget): float(rate)
        for budget, rate in zip(negative_budget, detection_rate, strict=True)
    }
    if not derive_dr_from_curve:
        return
    for source_key, column in FPR_BUDGETS:
        nominal_budget = float(source_key.removeprefix("fpr_"))
        eligible = [
            (float(actual_fpr), float(rate))
            for actual_fpr, rate in zip(realized_fpr, detection_rate, strict=True)
            if float(actual_fpr) <= nominal_budget
        ]
        if not eligible:
            continue
        closest_fpr = max(actual_fpr for actual_fpr, _rate in eligible)
        result[f"{scope_prefix}{column}"] = max(
            rate for actual_fpr, rate in eligible if actual_fpr == closest_fpr
        )


def _enrich_complete_curve(
    result: dict[str, Any],
    root: Path,
    entry: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
) -> None:
    receipt_relative = entry.get("curve_receipt_relative_path")
    artifact_relative = entry.get("curve_artifact_relative_path")
    if not receipt_relative or not artifact_relative:
        return
    receipt_path = root / receipt_relative
    artifact_path = root / artifact_relative
    if not receipt_path.is_file() or not artifact_path.is_file():
        return
    _record_provenance(receipt_path, f"{entry['display_name']}的完整曲线收据", provenance)
    _record_provenance(artifact_path, f"{entry['display_name']}的完整曲线NPZ", provenance)
    receipt = _load_auxiliary_json(receipt_path)
    if receipt is None:
        return
    declared = receipt.get("artifact", receipt)
    actual_hash = provenance[str(artifact_path.resolve())]["sha256"]
    if declared.get("sha256") and declared["sha256"] != actual_hash:
        raise ValueError(f"完整曲线制品哈希与收据不符：{artifact_path}")
    if declared.get("bytes") and declared["bytes"] != artifact_path.stat().st_size:
        raise ValueError(f"完整曲线制品字节数与收据不符：{artifact_path}")
    fields = receipt.get("fields") or [
        "n_false_positive_entity",
        "nominal_fpr",
        "realized_fpr",
        "detection_rate",
    ]
    schema = receipt.get("schema_version")
    complete = (
        receipt.get("curve_is_complete_over_all_reachable_negative_entity_budgets") is True
        or receipt.get("complete_over_all_reachable_negative_entity_budgets") is True
        or schema == "ch3-grande-complete-alert-budget-curves-v1"
    )
    if complete:
        cell = str(result.get("_curve_cell") or entry.get("cell"))
        member_prefix = f"{entry.get('curve_member_prefix', '')}{cell}"
        scope_prefix = "source_" if entry.get("curve_scope") == "source" else ""
        _apply_complete_curve(
            result,
            artifact_path,
            member_prefix,
            [str(field) for field in fields],
            scope_prefix,
            result.get("_derive_dr_from_complete_curve") is True,
        )


def _enrich_manifest_source_curve(
    result: dict[str, Any],
    root: Path,
    entry: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
) -> None:
    artifact_relative = entry.get("source_curve_artifact_relative_path")
    manifest_relative = entry.get("manifest_relative_path")
    if not artifact_relative or not manifest_relative:
        return
    artifact_path = root / artifact_relative
    manifest_path = root / manifest_relative
    if not artifact_path.is_file() or not manifest_path.is_file():
        return
    _record_provenance(manifest_path, f"{entry['display_name']}的运行清单", provenance)
    _record_provenance(artifact_path, f"{entry['display_name']}的源年完整曲线NPZ", provenance)
    manifest = _load_auxiliary_json(manifest_path)
    if manifest is None:
        return
    declared = manifest.get("files", {}).get(artifact_path.name, {})
    actual_hash = provenance[str(artifact_path.resolve())]["sha256"]
    if declared.get("sha256") != actual_hash or declared.get("bytes") != artifact_path.stat().st_size:
        raise ValueError(f"源年完整曲线制品与运行清单不符：{artifact_path}")
    cell = str(result.get("_curve_cell") or entry.get("cell"))
    member_prefix = f"{entry.get('source_curve_member_prefix', '')}{cell}"
    _apply_complete_curve(
        result,
        artifact_path,
        member_prefix,
        ["n_false_positive_entity", "nominal_fpr", "realized_fpr", "detection_rate"],
        "source_",
        result.get("_derive_dr_from_complete_curve") is True,
    )


def _apply_first_alert(
    result: dict[str, Any],
    artifact_path: Path,
    member_prefix: str,
    axis: str,
    time_delay_available: bool,
    metadata: dict[str, Any],
    scope_prefix: str,
    key_style: str,
) -> None:
    unalerted: dict[str, float] = {}
    delay_summary: dict[str, Any] = {}
    actual_fpr_by_budget: dict[str, float] = {}
    curves_by_actual_fpr: dict[float, dict[float, float]] = {}
    unalerted_by_actual_fpr: dict[float, float] = {}
    for source_key, _column in FPR_BUDGETS:
        item = metadata.get(source_key, {})
        if (
            item.get("axis") != axis
            or item.get("time_delay_available") is not time_delay_available
            or not isinstance(item.get("positive_unalerted_rate"), (int, float))
            or not isinstance(item.get("realized_first_alert_fpr"), (int, float))
        ):
            return
        actual_fpr = float(item["realized_first_alert_fpr"])
        if key_style == "branch_first_alert_v1":
            axis_name = f"{member_prefix}__first_alert__{source_key}__{axis}"
            rate_name = f"{member_prefix}__first_alert__{source_key}__on_time_detection_rate"
        else:
            axis_name = f"{member_prefix}__{source_key}__{axis}"
            rate_name = f"{member_prefix}__{source_key}__timely_detection_rate"
        vectors = _npz_vectors(artifact_path, [axis_name, rate_name])
        axis_values = vectors.get(axis_name)
        rates = vectors.get(rate_name)
        if axis_values is None or rates is None or len(axis_values) != len(rates) or not axis_values:
            return
        curve = {
            float(axis_value): float(rate)
            for axis_value, rate in zip(axis_values, rates, strict=True)
        }
        unalerted[source_key] = float(item["positive_unalerted_rate"])
        actual_fpr_by_budget[source_key] = actual_fpr
        unalerted_by_actual_fpr[actual_fpr] = unalerted[source_key]
        curves_by_actual_fpr[actual_fpr] = curve
        delay_summary[source_key] = {
            "nominal_fpr": float(source_key.removeprefix("fpr_")),
            "realized_first_alert_fpr": actual_fpr,
            "positive_unalerted_rate": unalerted[source_key],
            "first_alert_delay_quantiles": item.get("first_alert_exposure_quantiles")
            or item.get("first_alert_delay_quantiles"),
            "time_delay_available": time_delay_available,
        }
    result[f"{scope_prefix}first_alert_axis"] = axis
    result[f"{scope_prefix}time_delay_available"] = time_delay_available
    for source_key, _column in FPR_BUDGETS:
        result[f"{scope_prefix}unalerted_rate_{source_key}"] = unalerted[source_key]
    result[f"{scope_prefix}timely_detection_curve_summary"] = (
        f"六档名义预算均保留实际可达FPR与按时检出累计曲线；横轴={axis}；各档均含未告警实体"
    )
    result[f"{scope_prefix}timely_detection_curve_artifact"] = (
        f"{artifact_path.resolve()}#{member_prefix}"
    )
    result[f"{scope_prefix}first_alert_delay_summary"] = delay_summary
    result[f"{scope_prefix}first_alert_definition"] = (
        "从实体首条合法可观测流起计算1基实体内曝光序号；每档同时保留实际可达FPR；"
        f"axis={axis}；time_delay_available={str(time_delay_available).lower()}"
    )
    result[f"_{scope_prefix}first_alert_actual_fpr"] = actual_fpr_by_budget
    result[f"_{scope_prefix}unalerted_by_actual_fpr"] = unalerted_by_actual_fpr
    result[f"_{scope_prefix}timely_detection_curves"] = curves_by_actual_fpr


def _enrich_first_alert(
    result: dict[str, Any],
    root: Path,
    entry: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
) -> None:
    """读取版本化首次告警制品；缺失时保持空值，不从其他指标推导。"""
    receipt_relative = entry.get("first_alert_receipt_relative_path")
    artifact_relative = entry.get("first_alert_artifact_relative_path")
    if not receipt_relative or not artifact_relative:
        return
    receipt_path = root / receipt_relative
    artifact_path = root / artifact_relative
    if not receipt_path.is_file() or not artifact_path.is_file():
        return
    _record_provenance(receipt_path, f"{entry['display_name']}的首次告警收据", provenance)
    _record_provenance(artifact_path, f"{entry['display_name']}的按时检出曲线NPZ", provenance)
    receipt = _load_auxiliary_json(receipt_path)
    if receipt is None:
        return
    axis = receipt.get("axis")
    time_delay_available = receipt.get("time_delay_available")
    if axis not in {"exposure_index", "elapsed_seconds"}:
        return
    if not isinstance(time_delay_available, bool):
        return
    if axis == "elapsed_seconds" and not time_delay_available:
        return
    declared = receipt.get("artifact", {})
    actual_hash = provenance[str(artifact_path.resolve())]["sha256"]
    if declared.get("sha256") != actual_hash or declared.get("bytes") != artifact_path.stat().st_size:
        raise ValueError(f"首次告警制品与收据不符：{artifact_path}")
    scope_prefix = "source_" if entry.get("first_alert_scope") == "source" else ""
    metadata = result.get(f"_{scope_prefix}first_alert_metadata")
    cell = str(result.get("_curve_cell") or entry.get("cell"))
    if not isinstance(metadata, dict):
        cell_receipt = receipt.get("cells", {}).get(cell, {})
        unalerted = cell_receipt.get("unalerted_rate_at_fpr", {})
        realized = cell_receipt.get("realized_fpr_at_fpr", {})
        delay = cell_receipt.get("delay_summary_at_fpr", {})
        if all(
            isinstance(unalerted.get(source_key), (int, float))
            and isinstance(realized.get(source_key), (int, float))
            for source_key, _column in FPR_BUDGETS
        ):
            metadata = {
                source_key: {
                    "axis": axis,
                    "time_delay_available": time_delay_available,
                    "positive_unalerted_rate": unalerted[source_key],
                    "realized_first_alert_fpr": realized[source_key],
                    "first_alert_delay_quantiles": delay.get(source_key),
                }
                for source_key, _column in FPR_BUDGETS
            }
    if not isinstance(metadata, dict):
        return
    member_prefix = f"{entry.get('first_alert_member_prefix', '')}{cell}"
    _apply_first_alert(
        result,
        artifact_path,
        member_prefix,
        axis,
        time_delay_available,
        metadata,
        scope_prefix,
        str(entry.get("first_alert_key_style", "timely_detection_v1")),
    )


def _enrich_manifest_source_first_alert(
    result: dict[str, Any],
    root: Path,
    entry: dict[str, Any],
) -> None:
    artifact_relative = entry.get("source_curve_artifact_relative_path")
    receipt_relative = entry.get("first_alert_receipt_relative_path")
    if not artifact_relative or not receipt_relative:
        return
    artifact_path = root / artifact_relative
    receipt = _load_auxiliary_json(root / receipt_relative)
    metadata = result.get("_source_first_alert_metadata")
    if not artifact_path.is_file() or receipt is None or not isinstance(metadata, dict):
        return
    axis = receipt.get("axis")
    time_delay_available = receipt.get("time_delay_available")
    if axis not in {"exposure_index", "elapsed_seconds"} or not isinstance(time_delay_available, bool):
        return
    if axis == "elapsed_seconds" and not time_delay_available:
        return
    cell = str(result.get("_curve_cell") or entry.get("cell"))
    member_prefix = f"{entry.get('source_curve_member_prefix', '')}{cell}"
    _apply_first_alert(
        result,
        artifact_path,
        member_prefix,
        axis,
        time_delay_available,
        metadata,
        "source_",
        str(entry.get("first_alert_key_style", "timely_detection_v1")),
    )


def _enrich_run_receipts(
    root: Path,
    entry: dict[str, Any],
    provenance: dict[str, dict[str, Any]],
) -> None:
    status_relative = entry.get("status_relative_path")
    if status_relative:
        status_path = root / status_relative
        if not status_path.is_file():
            raise ValueError(f"配置声明的完成状态收据不存在：{status_path}")
        _record_provenance(status_path, f"{entry['display_name']}的完成状态", provenance)
        status = _load_auxiliary_json(status_path)
        if status is None or (
            status.get("state"), status.get("stage"), status.get("exit_code")
        ) != ("complete", "finished", 0):
            raise ValueError(f"运行尚未达到complete/finished/0：{status_path}")
    resource_relative = entry.get("resource_receipt_relative_path")
    if resource_relative:
        resource_path = root / resource_relative
        if not resource_path.is_file():
            raise ValueError(f"配置声明的资源收据不存在：{resource_path}")
        _record_provenance(resource_path, f"{entry['display_name']}的资源收据", provenance)
        resource = _load_auxiliary_json(resource_path)
        if resource is None or resource.get("finished_at_unix") is None:
            raise ValueError(f"资源收据没有完成时间：{resource_path}")


def _default_missing_reason(column: str, row: dict[str, Any]) -> str:
    if row.get("pending_reason"):
        return str(row["pending_reason"])
    reasons = {
        "selected_epoch": "该来源没有单轮检查点选择，或未持久化选定轮次",
        "validation_flow_ap": "该来源未持久化可比较的源年验证逐流AP",
        "selected_p": "该模型或选择规则不使用幂平均指数",
        "selection_protocol": "原始来源未持久化选择协议说明",
        "selection_score": "固定配置直接训练，或原始制品未持久化选择分数",
        "selection_metric": "固定配置直接训练，不执行开发集择优",
        "parameter_count": "树集成不适用神经网络可训练参数量，规模见模型规模列",
        "scale_value": "原始来源未持久化可比较的模型规模数值",
        "scale_unit": "原始来源未持久化模型规模单位",
        "model_weight_bytes": "原始来源未持久化模型权重字节数",
        "inference_seconds": "所有现有来源均未单独持久化纯模型推理墙钟",
        "selection_seconds": "原始来源未拆分选模墙钟",
        "evaluation_seconds": "原始来源未拆分目标年评价墙钟",
        "training_seconds": "原始来源未拆分训练墙钟",
        "total_seconds": "原始来源未持久化端到端总墙钟",
        "gpu_hours": "原始来源未持久化GPU小时",
        "training_throughput": "原始来源未持久化有效训练样本吞吐",
        "evaluation_throughput": "原始来源未持久化评价样本吞吐",
        "peak_gpu_mib": "原始来源未持久化峰值显存",
        "peak_rss_mib": "原始来源未持久化峰值进程RSS",
        "checkpoint_bytes": "原始来源未持久化检查点字节数",
        "interruption_count": "原始来源未持久化中断次数",
        "recovery_count": "原始来源未持久化恢复次数",
        "recomputed_units": "原始来源未持久化重复计算量",
        "max_entity_ap": "原始来源未单独持久化最大池化实体AP",
        "dr_curve_summary": "原始来源未持久化完整曲线或曲线摘要",
        "dr_curve_artifact": "原始来源未持久化完整告警预算曲线制品",
        "timely_detection_curve_summary": "原始来源未持久化按时检出累计曲线摘要",
        "timely_detection_curve_artifact": "原始来源未持久化按时检出累计曲线制品",
        "first_alert_axis": "原始来源未声明首次告警横轴，曝光序号与真实秒不得混比",
        "time_delay_available": "原始来源未声明真实秒时延是否可用",
        "first_alert_delay_summary": "原始来源未持久化首次告警延迟或曝光摘要，禁止由AP或DR推导",
        "first_alert_definition": "原始来源未持久化首次告警起点与阈值定义，禁止推导",
        "model_scale": "原始来源未持久化模型规模描述",
        "time_scope": "原始来源未持久化时间统计口径",
    }
    if column.startswith("dr_fpr_"):
        return "原始来源未持久化该FPR工作点"
    if column.startswith("unalerted_rate_fpr_"):
        return "原始来源未持久化该预算的未告警率，禁止从DR反推"
    return reasons.get(column, "原始来源未持久化该字段")


def _fill_missing_reasons(row: dict[str, Any]) -> None:
    fields = {
        "selection_metric",
        "selection_score",
        "selected_epoch",
        "validation_flow_ap",
        "selected_p",
        "selection_protocol",
        "flow_ap",
        "entity_ap",
        "max_entity_ap",
        *(column for _, column in FPR_BUDGETS),
        "dr_curve_summary",
        "dr_curve_artifact",
        *FIRST_ALERT_COLUMNS,
        "model_scale",
        "parameter_count",
        *RESOURCE_METRIC_COLUMNS,
        "time_scope",
    }
    row["missing_reasons"] = {
        column: _default_missing_reason(column, row)
        for column in sorted(fields)
        if row.get(column) is None
    }
    source_fields = [
        *PERFORMANCE_SCALAR_COLUMNS,
        "dr_curve_summary",
        "dr_curve_artifact",
        *FIRST_ALERT_COLUMNS,
    ]
    row["source_performance_missing_reasons"] = {
        column: _default_missing_reason(column, row)
        for column in source_fields
        if row.get(f"source_{column}") is None
    }


def _parse_root_args(root_args: list[str]) -> dict[str, str]:
    roots: dict[str, str] = {}
    for item in root_args:
        if "=" not in item:
            raise ValueError(f"--root参数必须为name=path，收到：{item}")
        name, path = item.split("=", 1)
        if not name or not path:
            raise ValueError(f"--root参数必须同时含名称和路径，收到：{item}")
        roots[name] = str(Path(path).resolve())
    return roots


def collect_rows(
    config_path: str,
    roots: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """读取全部配置项，返回统一行及去重后的来源溯源。"""
    config_file = Path(config_path)
    config = json.loads(config_file.read_text(encoding="utf-8"))
    if config.get("schema_version") != "ch3-metrics-table-sources-v1":
        raise ValueError("来源配置schema_version不受支持")
    provenance_records: dict[str, dict[str, Any]] = {}
    _record_provenance(config_file, "来源配置", provenance_records)
    rows: list[dict[str, Any]] = []
    for entry in config.get("models", []):
        root_name = entry.get("root")
        root_value = roots.get(root_name)
        relative_path = entry.get("relative_path")
        source_path = Path(root_value) / relative_path if root_value and relative_path else None
        row = _blank_result()
        row.update(
            {
                "display_name": entry.get("display_name"),
                "config_type": entry.get("config_type"),
                "differentiable": entry.get("differentiable"),
                "run_id": entry.get("run_id"),
                "selection_pool": None,
                "evaluation_pool": None,
                "evidence_level": entry.get("evidence_level"),
                "source_path": str(source_path.resolve()) if source_path else None,
                "pending_reason": entry.get("pending_reason"),
                "_include_in_lspr24": entry.get("include_in_lspr24", True),
            }
        )
        if source_path and source_path.is_file():
            _record_provenance(source_path, f"{entry['display_name']}的主结果", provenance_records)
            normalized = read_source(str(Path(root_value)), entry)
            if normalized is None:
                row["pending_reason"] = "主结果存在，但JSON或目标模式/单元不可解析"
            else:
                row.update(normalized)
                row["pending_reason"] = None
                root = Path(root_value)
                _enrich_neural_resource(row, root, entry, provenance_records)
                _enrich_complete_curve(row, root, entry, provenance_records)
                _enrich_manifest_source_curve(row, root, entry, provenance_records)
                _enrich_first_alert(row, root, entry, provenance_records)
                _enrich_manifest_source_first_alert(row, root, entry)
                _enrich_run_receipts(root, entry, provenance_records)
        elif entry.get("available"):
            row["pending_reason"] = "配置标记为可用，但指定本地原始制品不存在"
        elif not row.get("pending_reason"):
            row["pending_reason"] = "尚无本地原始制品"
        _fill_missing_reasons(row)
        rows.append(row)
    provenance = {
        "schema_version": "ch3-metrics-table-provenance-v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_file.resolve()),
        "roots": roots,
        "source_file_count": len(provenance_records),
        "sha256_count": len(provenance_records),
        "files": sorted(provenance_records.values(), key=lambda item: item["absolute_path"]),
    }
    return rows, provenance


def _project_row(row: dict[str, Any], columns: list[str]) -> dict[str, Any]:
    projected = {column: row.get(column) for column in columns}
    if "missing_reasons" in projected:
        projected["missing_reasons"] = {
            column: reason
            for column, reason in row.get("missing_reasons", {}).items()
            if column in columns
        }
    return projected


def _source_performance_row(row: dict[str, Any]) -> dict[str, Any]:
    projected = {
        column: row.get(column)
        for column in (
            "display_name",
            "config_type",
            "differentiable",
            "run_id",
            "evidence_level",
            "source_path",
            "pending_reason",
        )
    }
    projected["evaluation_pool"] = row.get("source_performance_pool")
    for column in [
        *PERFORMANCE_SCALAR_COLUMNS,
        "dr_curve_summary",
        "dr_curve_artifact",
        *FIRST_ALERT_COLUMNS,
    ]:
        projected[column] = row.get(f"source_{column}")
    projected["missing_reasons"] = dict(row.get("source_performance_missing_reasons", {}))
    projected["_dr_curve_points"] = row.get("_source_dr_curve_points")
    projected["_first_alert_actual_fpr"] = row.get("_source_first_alert_actual_fpr")
    projected["_unalerted_by_actual_fpr"] = row.get("_source_unalerted_by_actual_fpr")
    projected["_timely_detection_curves"] = row.get("_source_timely_detection_curves")
    return projected


def _performance_pareto_missing(row: dict[str, Any]) -> dict[str, str]:
    missing = {
        column: _default_missing_reason(column, row)
        for column in [*PERFORMANCE_SCALAR_COLUMNS, *FIRST_ALERT_COLUMNS]
        if row.get(column) is None
    }
    if not row.get("_dr_curve_points"):
        missing["dr_curve_artifact"] = "缺少可读取的完整告警预算曲线数组，不能仅凭路径或摘要判定"
    if not row.get("_timely_detection_curves"):
        missing["timely_detection_curve_artifact"] = "缺少可读取的六档按时检出累计曲线数组"
    if not row.get("_first_alert_actual_fpr") or not row.get("_unalerted_by_actual_fpr"):
        missing["first_alert_delay_summary"] = "缺少名义预算到实际可达FPR的首次告警映射"
    return missing


def _resource_pareto_missing(row: dict[str, Any]) -> dict[str, str]:
    required = [column for column in RESOURCE_METRIC_COLUMNS if column != "scale_unit"]
    missing = {
        column: _default_missing_reason(column, row)
        for column in required
        if not isinstance(row.get(column), (int, float)) or isinstance(row.get(column), bool)
    }
    if not row.get("scale_unit"):
        missing["scale_unit"] = _default_missing_reason("scale_unit", row)
    return missing


def _compare_high_vectors(
    left: dict[Any, float], right: dict[Any, float]
) -> tuple[bool, bool]:
    common = sorted(set(left).intersection(right))
    if not common:
        return False, False
    no_worse = all(float(left[key]) >= float(right[key]) for key in common)
    strictly_better = any(float(left[key]) > float(right[key]) for key in common)
    return no_worse, strictly_better


def _performance_dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get("first_alert_axis") != right.get("first_alert_axis"):
        return False
    no_worse = all(float(left[column]) >= float(right[column]) for column in PERFORMANCE_SCALAR_COLUMNS)
    strict = any(float(left[column]) > float(right[column]) for column in PERFORMANCE_SCALAR_COLUMNS)
    if not no_worse:
        return False
    curve_no_worse, curve_strict = _compare_high_vectors(
        left["_dr_curve_points"], right["_dr_curve_points"]
    )
    if not curve_no_worse:
        return False
    strict = strict or curve_strict
    common_first_alert_fpr = sorted(
        set(left["_unalerted_by_actual_fpr"]).intersection(right["_unalerted_by_actual_fpr"])
    )
    if not common_first_alert_fpr:
        return False
    for actual_fpr in common_first_alert_fpr:
        if float(left["_unalerted_by_actual_fpr"][actual_fpr]) > float(
            right["_unalerted_by_actual_fpr"][actual_fpr]
        ):
            return False
        strict = strict or float(left["_unalerted_by_actual_fpr"][actual_fpr]) < float(
            right["_unalerted_by_actual_fpr"][actual_fpr]
        )
        timely_no_worse, timely_strict = _compare_high_vectors(
            left["_timely_detection_curves"][actual_fpr],
            right["_timely_detection_curves"][actual_fpr],
        )
        if not timely_no_worse:
            return False
        strict = strict or timely_strict
    return strict


def _resource_dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if left.get("scale_unit") != right.get("scale_unit"):
        return False
    lower_is_better = [
        "scale_value",
        "model_weight_bytes",
        "training_seconds",
        "selection_seconds",
        "inference_seconds",
        "evaluation_seconds",
        "total_seconds",
        "gpu_hours",
        "peak_gpu_mib",
        "peak_rss_mib",
        "checkpoint_bytes",
        "interruption_count",
        "recovery_count",
        "recomputed_units",
    ]
    higher_is_better = ["training_throughput", "evaluation_throughput"]
    if any(float(left[column]) > float(right[column]) for column in lower_is_better):
        return False
    if any(float(left[column]) < float(right[column]) for column in higher_is_better):
        return False
    return any(float(left[column]) < float(right[column]) for column in lower_is_better) or any(
        float(left[column]) > float(right[column]) for column in higher_is_better
    )


def mark_pareto(table: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    """按完整同池向量标记帕累托状态；缺项行不参加支配。"""
    if kind not in {"performance", "resource"}:
        raise ValueError(f"未知帕累托类型：{kind}")
    missing_builder = _performance_pareto_missing if kind == "performance" else _resource_pareto_missing
    dominates = _performance_dominates if kind == "performance" else _resource_dominates
    group_keys = ("evaluation_pool", "first_alert_axis") if kind == "performance" else ("scale_unit",)
    complete: list[dict[str, Any]] = []
    for row in table:
        row["dominated_by"] = []
        row["dominates"] = []
        row["pareto_missing_reasons"] = missing_builder(row)
        group = tuple(row.get(key) for key in group_keys)
        row["_pareto_group"] = group
        if row["pareto_missing_reasons"] or any(part is None for part in group):
            for key, part in zip(group_keys, group, strict=True):
                if part is None:
                    row["pareto_missing_reasons"][key] = (
                        "缺少可比较池或首次告警横轴"
                        if kind == "performance"
                        else "缺少可比较池或规模单位"
                    )
            row["pareto_status"] = "证据不完整"
        else:
            complete.append(row)
    for left in complete:
        for right in complete:
            if left is right or left["_pareto_group"] != right["_pareto_group"]:
                continue
            if dominates(left, right):
                left["dominates"].append(str(right["display_name"]))
                right["dominated_by"].append(str(left["display_name"]))
    for row in complete:
        row["pareto_status"] = "被支配" if row["dominated_by"] else "帕累托前沿"
        row["dominated_by"].sort()
        row["dominates"].sort()
    return table


def mark_best(
    table: list[dict[str, Any]],
    columns: list[str],
    group_columns: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """在同一评价池中按全精度标记最大值；单行组不标最强。"""
    for row in table:
        row["best_flags"] = {}
    for column in columns:
        groups: dict[tuple[Any, ...], list[tuple[int, float]]] = {}
        for index, row in enumerate(table):
            value = row.get(column)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            group = tuple(row.get(key) for key in group_columns)
            if any(part is None for part in group):
                continue
            groups.setdefault(group, []).append((index, float(value)))
        for values in groups.values():
            if len(values) < 2:
                continue
            top = max(value for _, value in values)
            winners = [index for index, value in values if value == top]
            flag = "best" if len(winners) == 1 else "tied_best"
            for index in winners:
                table[index]["best_flags"][column] = flag
    return table


def build_tables(rows: list[dict[str, Any]]) -> dict[str, tuple[list[dict[str, Any]], list[str]]]:
    """把统一行投影为选择、年度性能与资源互不混排的四张表。"""
    source_table = [_project_row(row, LSPR23_COLUMNS) for row in rows]
    source_performance_rows = [_source_performance_row(row) for row in rows]
    target_rows = [dict(row) for row in rows if row.get("_include_in_lspr24")]
    resource_rows = [dict(row) for row in rows]
    mark_best(source_table, ["selection_score"], ("selection_pool", "selection_metric"))
    mark_best(source_performance_rows, PERFORMANCE_SCALAR_COLUMNS, ("evaluation_pool",))
    mark_best(
        target_rows,
        PERFORMANCE_SCALAR_COLUMNS,
        ("evaluation_pool",),
    )
    mark_pareto(source_performance_rows, "performance")
    mark_pareto(target_rows, "performance")
    mark_pareto(resource_rows, "resource")
    source_performance_table = [
        _project_row(row, LSPR23_PERFORMANCE_COLUMNS) for row in source_performance_rows
    ]
    target_table = [_project_row(row, LSPR24_COLUMNS) for row in target_rows]
    resource_table = [_project_row(row, RESOURCE_COLUMNS) for row in resource_rows]
    return {
        "lspr23-selection": (source_table, LSPR23_COLUMNS),
        "lspr23-performance": (source_performance_table, LSPR23_PERFORMANCE_COLUMNS),
        "lspr24-evaluation": (target_table, LSPR24_COLUMNS),
        "resource": (resource_table, RESOURCE_COLUMNS),
    }


def _serialize_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".15g")
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value)


def _markdown_cell(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, float):
        return format(value, ".12g")
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value).replace("|", "\\|").replace("\n", " ")


def _render_markdown(name: str, rows: list[dict[str, Any]], columns: list[str]) -> str:
    visible = [
        column
        for column in columns
        if column not in {"missing_reasons", "best_flags", "pareto_missing_reasons"}
    ]
    lines = [
        f"# {TABLE_TITLES[name]}",
        "",
        "本表由原始运行制品机械生成；粗体表示同一评价池、同一指标的全精度最强值。",
        "",
    ]
    lines.append("| " + " | ".join(COLUMN_LABELS.get(column, column) for column in visible) + " |")
    lines.append("| " + " | ".join("---" for _ in visible) + " |")
    for row in rows:
        cells = []
        for column in visible:
            value = _markdown_cell(row.get(column))
            if row.get("best_flags", {}).get(column):
                value = f"**{value}**"
            cells.append(value)
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(["", "## 缺失值说明", ""])
    for row in rows:
        reasons = row.get("missing_reasons", {})
        if not reasons:
            continue
        details = "；".join(f"{COLUMN_LABELS.get(column, column)}：{reason}" for column, reason in reasons.items())
        lines.append(f"- {row['display_name']}：{details}。")
    if "pareto_status" in columns:
        lines.extend(["", "## 帕累托证据缺口", ""])
        for row in rows:
            reasons = row.get("pareto_missing_reasons", {})
            if not reasons:
                continue
            details = "；".join(
                f"{COLUMN_LABELS.get(column, column)}：{reason}"
                for column, reason in reasons.items()
            )
            lines.append(f"- {row['display_name']}：{details}。")
    axis_notes = []
    if name in {"lspr23-performance", "lspr24-evaluation"}:
        axis_notes = [
            "- 首次告警帕累托只在相同横轴内比较；实体内曝光序号与真实秒时延不得混排。",
            "- 曝光序号轴可在真实秒时延不可用时参与同轴比较，但必须明确保留真实秒时延不可用。",
        ]
    lines.extend(
        [
            "",
            "## 评价口径",
            "",
            "- LSPR23 选择表只记录选模证据，LSPR23 性能表只记录源年开发性能；LSPR24 表只记录已访问目标年的描述性评价，三者不混排。",
            "- 实体 AP 为各运行预先注册的主聚合口径；最大实体 AP 单列，缺失时不反推。",
            "- 性能帕累托要求标量、实际完整预算曲线、六档未告警率和按时检出曲线全部齐全；缺项行标为证据不完整。",
            *axis_notes,
            "- 首次告警缺失时不由AP、DR或离线实体分数反推。",
            "- 评价时间含预测与指标计算时会在时间口径列明示，不能替代纯模型推理时间。",
            "- 工程帕累托独立计算；树数与神经参数量按不同规模单位分池，不机械折算。",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(
    tables: dict[str, tuple[list[dict[str, Any]], list[str]]],
    out_dir: str,
    provenance: dict[str, Any],
) -> list[str]:
    """以JSON、CSV、Markdown写出四表，并落盘唯一溯源清单。"""
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, (rows, columns) in tables.items():
        json_path = output / f"{name}.json"
        csv_path = output / f"{name}.csv"
        markdown_path = output / f"{name}.md"
        json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=columns,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({column: _serialize_cell(row.get(column)) for column in columns})
        markdown_path.write_text(_render_markdown(name, rows, columns), encoding="utf-8")
        written.extend(str(path) for path in (json_path, csv_path, markdown_path))
    provenance_path = output / "provenance.json"
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    written.append(str(provenance_path))
    return written


def _run_probe(config_path: str, root_args: list[str]) -> None:
    rows, provenance = collect_rows(config_path, _parse_root_args(root_args))
    for row in rows:
        print(
            f"{row['display_name']}\tflow_ap={row.get('flow_ap')}\t"
            f"entity_ap={row.get('entity_ap')}\tpending_reason={row.get('pending_reason')}"
        )
    print(f"来源文件={provenance['source_file_count']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="第三章全模型统一指标总表构建工具")
    parser.add_argument("--probe", action="store_true", help="只读探测每个来源，不写总表")
    parser.add_argument("--config", required=True, help="来源配置JSON路径")
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        metavar="name=path",
        help="运行根映射，可重复传入",
    )
    parser.add_argument("--out", help="十三个总表与溯源产物的输出目录")
    args = parser.parse_args()
    if args.probe:
        _run_probe(args.config, args.root)
        return
    if not args.out:
        parser.error("完整生成需要--out")
    roots = _parse_root_args(args.root)
    rows, provenance = collect_rows(args.config, roots)
    written = write_outputs(build_tables(rows), args.out, provenance)
    available = sum(row.get("pending_reason") is None for row in rows)
    pending = [row for row in rows if row.get("pending_reason")]
    print(f"模型总数={len(rows)} 可用={available} pending={len(pending)} 来源文件={provenance['source_file_count']}")
    for row in pending:
        print(f"pending\t{row['display_name']}\t{row['pending_reason']}")
    for path in written:
        print(f"写出\t{path}")


if __name__ == "__main__":
    main()
