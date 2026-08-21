# -*- coding: utf-8 -*-
"""TabM32 骨干专属论文配方协议 A 四格实验工具（任务 1：配置与运行身份骨架）。

本文件目前只实现：模块级冻结常量、配置校验 ``validate_config`` 与命令行入口的
阶段分发骨架。``select-input``、``select-optimizer``、``cells``、``evaluate``
四个阶段的真实计算逻辑将由后续任务（输入变换、骨干、训练循环、断点恢复、封印
与评价、启动器）继续在本文件上叠加，本任务只为它们预留分发位置，不预先实现。

按仓库规则，numpy 与 torch 的导入延迟到真正需要它们的函数内部：本任务的
``--validate-config`` 只做纯 Python 字典/字符串比对，不应因为本机 ``.venv``
缺少 numpy/torch 而失败。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 运行身份与协议 A 冻结常量
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "ch3-tabm32-paper-recipe-protocol-a-config-v1"
RUN_ID = "ch3-tabm32-paper-recipe-protocol-a-seed42-v1"
MODEL_KEY = "tabm32-paper-recipe"

# 冻结配方文件的实测 SHA-256（本模块只做字符串比对，不重新计算冻结配方文件
# 本身的哈希——那是启动器任务的职责）。
FROZEN_RECIPE_SHA256 = "3b1e3103c9a8d37afe55c5e055cfcc4b84c72af3054b4cd20ec1dc4e5554d359"

CELL_ORDER: tuple[str, ...] = ("C00", "C01", "C10", "C11")
CELLS: dict[str, dict[str, bool]] = {
    "C00": {"causal_prefix_aggregation": False, "learned_lp_pooling": False},
    "C01": {"causal_prefix_aggregation": False, "learned_lp_pooling": True},
    "C10": {"causal_prefix_aggregation": True, "learned_lp_pooling": False},
    "C11": {"causal_prefix_aggregation": True, "learned_lp_pooling": True},
}

DR_FPR_GRID: tuple[float, ...] = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)

SOURCE_ARRAYS: tuple[str, ...] = ("X23", "y23", "I23", "M23", "E23", "T23")
TARGET_ARRAYS: tuple[str, ...] = ("X24", "y24", "I24", "M24", "s24", "d24", "t24")

# 输入接口候选（阶段一 select-input 的备选清单）。候选二的 input_dimension 与
# parameter_count 故意为 None：它们由运行时从字段基数收据推导，在
# WAITING_FOR_CODEX_CARDINALITY_RECEIPT 解除前保持未知。
INPUT_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "order": 1,
        "display_name": "TabM32-官方全数值扁平输入",
        "key": "tabm32-input-all-numeric",
        "numeric_transform": "training_region_quantile_normalization",
        "categorical_treatment": "as_numeric",
        "boolean_treatment": "as_numeric",
        "input_dimension": 83,
        "parameter_count": 995457,
    },
    {
        "order": 2,
        "display_name": "TabM32-官方字段类型分治输入",
        "key": "tabm32-input-type-partitioned",
        "numeric_transform": "training_region_quantile_normalization",
        "categorical_treatment": "training_region_one_hot_with_out_of_vocabulary_bucket",
        "boolean_treatment": "zero_one_passthrough",
        "input_dimension": None,
        "parameter_count": None,
        "pending_reason": "WAITING_FOR_CODEX_CARDINALITY_RECEIPT",
    },
)

# 优化器候选（阶段二 select-optimizer 的备选清单）。
OPTIMIZER_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "order": 1,
        "display_name": "TabM32-官方默认优化器",
        "key": "tabm32-official-default",
        "learning_rate": 0.002,
        "weight_decay": 0.0003,
    },
    {
        "order": 2,
        "display_name": "TabM32-论文对数中位优化器",
        "key": "tabm32-paper-logmid",
        "learning_rate": 0.0007071067811865476,
        "weight_decay": 0.0,
    },
)

# 命令行 --stage 的合法取值，对应后续任务要补全的四个执行阶段。
STAGE_CHOICES: tuple[str, ...] = ("select-input", "select-optimizer", "cells", "evaluate")

# ---------------------------------------------------------------------------
# validate_config 内部使用的冻结期望值（不对外导出，只服务本函数）
# ---------------------------------------------------------------------------

_EXPECTED_FIELD_GROUPS: dict[str, Any] = {
    "categorical": ["SrcPort", "DstPort", "Protocol", "L3/L4 Protocol", "Int/Ext Dst IP"],
    "boolean": ["External_src", "External_dst"],
    "numeric_count": 76,
    "total_count": 83,
}

_EXPECTED_CANDIDATE: dict[str, Any] = {
    "hidden_size": 512,
    "layer_count": 3,
    "ensemble_members": 32,
    "member_batch_sharing": True,
    "shared_training_batches": True,
    "micro_batch_sequences": 4,
    "gradient_accumulation_steps": 16,
    "member_probability_reduction": "arithmetic_mean",
    "member_loss_reduction": "mean_of_member_binary_cross_entropy",
    "elp_exponent": "shared_scalar",
    "activation": "relu",
    "numerical_embedding": False,
    "additional_normalization_layers": False,
    "parameter_formula": "544*d_in+950305",
    "batch_ensemble_formula": "BE(a,b,k)=a*b+k*a+k*b+k*b",
}

_EXPECTED_TRAINING: dict[str, Any] = {
    "seed": 42,
    "sequence_length": 128,
    "effective_batch_size": 64,
    "epochs": 20,
    "steps_per_epoch": 1000,
    "dropout": 0.1,
    "gradient_clip_norm": 1.0,
    "auxiliary_loss_weight": 1.0,
    "validation_fraction": 0.1,
    "time_tail_fraction": 0.15,
    "learning_rate_schedule": "none",
    "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
    "selection_rule": "single_epoch_argmax_earliest_tie_no_early_stopping",
    "stopping_rule_deviates_from_frozen_recipe": True,
    "stopping_rule_deviation_note": (
        "冻结配方第155行为耐心16无轮数上限；本运行取协议A的20轮跑满不早停"
        "以保持四格与跨骨干可比性，见实施计划冲突一"
    ),
}

_EXPECTED_SELECTION_STAGES: dict[str, Any] = {
    "stage_one_input_interface": ["tabm32-input-all-numeric", "tabm32-input-type-partitioned"],
    "stage_one_fixed_optimizer": "tabm32-official-default",
    "stage_two_optimizer": ["tabm32-official-default", "tabm32-paper-logmid"],
    "stage_two_uses_sealed_input": True,
    "tie_break": "fixed_table_order",
    "forbidden_tie_breakers": ["entity_ap", "alert_budget", "training_time", "gpu_memory", "lspr24"],
}

_EXPECTED_EVALUATION: dict[str, Any] = {
    "target_year": "LSPR24",
    "target_previously_accessed": True,
    "independent_test": False,
    "target_load_after_all_selections_sealed": True,
    "target_evaluation_calls": 4,
    "flow_average_precision": True,
    "entity_average_precision": True,
    "maximum_entity_average_precision": True,
    "dr_fpr_grid": list(DR_FPR_GRID),
    "complete_reachable_alert_budget_curve": True,
}

_EXPECTED_ARTIFACT_POLICY: dict[str, Any] = {
    "persist_selected_checkpoint_per_cell": True,
    "persist_inflight_epoch_checkpoint": True,
    "persist_per_flow_scores": False,
    "persist_per_entity_scores": False,
    "persist_complete_budget_curve_aggregate": True,
}

# resource_contract 中除 minimum_free_gpu_memory_mib 外的固定期望值；该字段
# 目前故意为 null，待 Codex 依实施计划冲突四重新裁定后才回填，见 validate_config。
_EXPECTED_RESOURCE_CONTRACT_FIXED: dict[str, Any] = {
    "measure_resident_bytes_after_upload": True,
    "assert_free_memory_before_model_allocation": True,
    "minimum_cgroup_available_memory_gib": 40,
    "minimum_free_disk_gib": 10,
    "maximum_parallel_jobs": 1,
    "maximum_parallel_cells_per_job": 1,
    "resource_sample_interval_seconds": 5,
    "concurrent_resource_measurement_is_fair_efficiency_evidence": False,
}

_EXPECTED_SWANLAB: dict[str, Any] = {
    "workspace": "mortiswang",
    "project": "ns3-rwkv-lspr24",
    "group": RUN_ID,
    "mode": "cloud",
    "tags": ["chapter3", "tabm32", "paper-recipe", "protocol-a", "2x2", "seed42", "single-run"],
}


# ---------------------------------------------------------------------------
# 配置校验
# ---------------------------------------------------------------------------


def validate_config(config: dict[str, Any]) -> None:
    """核验冻结 JSON 配置是否严格等于协议 A 的冻结身份与合同。

    只做纯 Python 字典/字符串比对，不读取磁盘上的冻结配方文件、不联网、
    不建运行目录；每项不符都抛出带中文原因的 ``ValueError``。
    """
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version 与冻结模式版本不符")
    if config.get("model_key") != MODEL_KEY or config.get("run_id") != RUN_ID:
        raise ValueError("model_key 或 run_id 运行身份不符")
    if config.get("frozen_recipe_sha256") != FROZEN_RECIPE_SHA256:
        raise ValueError("frozen_recipe_sha256 与冻结配方常量不符（本函数只做字符串比对）")
    if config.get("cells") != CELLS:
        raise ValueError("cells 必须严格等于协议 A 四格 C00/C01/C10/C11 的冻结定义")
    if config.get("source_arrays") != list(SOURCE_ARRAYS):
        raise ValueError("source_arrays 源年数组合同不符")
    if config.get("target_arrays") != list(TARGET_ARRAYS):
        raise ValueError("target_arrays 目标年数组合同不符")
    if config.get("field_groups") != _EXPECTED_FIELD_GROUPS:
        raise ValueError("field_groups 字段分组合同不符")
    if config.get("input_candidates") != list(INPUT_CANDIDATES):
        raise ValueError("input_candidates 与冻结输入候选定义不符")
    if config.get("optimizer_candidates") != list(OPTIMIZER_CANDIDATES):
        raise ValueError("optimizer_candidates 与冻结优化器候选定义不符")

    candidate = config.get("candidate", {})
    training = config.get("training", {})
    if candidate.get("ensemble_members") != 32:
        raise ValueError("candidate.ensemble_members 成员数必须为 32")
    if candidate.get("layer_count") != 3:
        raise ValueError("candidate.layer_count 层数必须为 3")
    if candidate.get("hidden_size") != 512:
        raise ValueError("candidate.hidden_size 宽度必须为 512")
    if candidate.get("numerical_embedding") is not False:
        raise ValueError("candidate.numerical_embedding 必须为假，TabM32 官方配方不使用数值嵌入")
    if candidate.get("additional_normalization_layers") is not False:
        raise ValueError("candidate.additional_normalization_layers 必须为假，不追加归一化层")
    micro_batch = candidate.get("micro_batch_sequences")
    accumulation = candidate.get("gradient_accumulation_steps")
    effective_batch = training.get("effective_batch_size")
    if not isinstance(micro_batch, int) or not isinstance(accumulation, int) or micro_batch * accumulation != effective_batch:
        raise ValueError("micro_batch_sequences 乘以 gradient_accumulation_steps 必须等于 effective_batch_size")
    if candidate != _EXPECTED_CANDIDATE:
        raise ValueError("candidate 配方其余字段与冻结协议 A 配方不符")

    if training.get("dropout") != 0.1:
        raise ValueError("training.dropout 随机失活必须为 0.1")
    if training != _EXPECTED_TRAINING:
        raise ValueError("training 训练与选择合同不符（协议 A 冻结值）")

    if config.get("selection_stages", {}).get("forbidden_tie_breakers") != _EXPECTED_SELECTION_STAGES["forbidden_tie_breakers"]:
        raise ValueError("selection_stages.forbidden_tie_breakers 禁用打平依据清单缺项或不符")
    if config.get("selection_stages") != _EXPECTED_SELECTION_STAGES:
        raise ValueError("selection_stages 选择阶段合同不符")

    evaluation = config.get("evaluation", {})
    if evaluation.get("target_evaluation_calls") != 4:
        raise ValueError("evaluation.target_evaluation_calls 目标评价调用次数必须为 4")
    if evaluation != _EXPECTED_EVALUATION:
        raise ValueError("evaluation 目标评价合同不符")

    if config.get("artifact_policy") != _EXPECTED_ARTIFACT_POLICY:
        raise ValueError("artifact_policy 制品持久化合同不符")

    paths = config.get("paths", {})
    for key in ("cache_root", "output_root", "field_cardinality_receipt"):
        if not isinstance(paths.get(key), str) or not paths.get(key):
            raise ValueError(f"paths.{key} 缺失或类型不符")
    if Path(paths["output_root"]).name != RUN_ID:
        raise ValueError("paths.output_root 末级目录必须等于运行身份 run_id")

    resource_contract = config.get("resource_contract", {})
    for key, expected_value in _EXPECTED_RESOURCE_CONTRACT_FIXED.items():
        if resource_contract.get(key) != expected_value:
            raise ValueError(f"resource_contract.{key} 与冻结值不符")
    if resource_contract.get("minimum_free_gpu_memory_mib") is not None:
        raise ValueError(
            "resource_contract.minimum_free_gpu_memory_mib 当前必须为待定的 null，"
            "须先由 Codex 依实施计划冲突四重新裁定后再回填"
        )
    if not resource_contract.get("pending_reason"):
        raise ValueError("resource_contract 缺少 pending_reason 待定说明")
    logger.warning(
        "resource_contract.minimum_free_gpu_memory_mib 待定（%s），GPU 显存准入阈值尚未确定",
        resource_contract.get("pending_reason"),
    )

    if config.get("swanlab") != _EXPECTED_SWANLAB:
        raise ValueError("swanlab 上报身份合同不符")

    if config.get("single_run_directly_comparable") is not True:
        raise ValueError("single_run_directly_comparable 必须为真")
    if config.get("formal_paper_evidence") is not False or config.get("independent_test") is not False:
        raise ValueError("本次重跑不能宣称正式论文证据或独立测试")


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------


def load_json(path: Path) -> dict[str, Any]:
    """读取 JSON 文件并要求顶层是对象。"""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TabM32 骨干专属论文配方协议 A 四格实验入口")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置路径")
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="只核验配置后退出，不触碰数据、不建运行目录、不连接 SwanLab",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="恢复同运行身份下的在途检查点或已封印选择（预留，由后续任务实现）",
    )
    parser.add_argument(
        "--stage",
        choices=STAGE_CHOICES,
        help="要执行的实验阶段：select-input / select-optimizer / cells / evaluate",
    )
    parser.add_argument(
        "--resource-receipt",
        help="启动器写入的资源准入收据路径（预留，由后续任务实现）",
    )
    return parser.parse_args()


def run_select_input_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段一：在 INPUT_CANDIDATES 中筛选输入接口（骨架占位，尚未实现）。"""
    raise NotImplementedError("select-input 阶段尚未实现，将由后续任务补全输入变换与筛选逻辑")


def run_select_optimizer_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段二：在已封印输入接口上筛选 OPTIMIZER_CANDIDATES（骨架占位，尚未实现）。"""
    raise NotImplementedError("select-optimizer 阶段尚未实现，将由后续任务补全优化器筛选逻辑")


def run_cells_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """协议 A 四格（CELL_ORDER）训练与选择（骨架占位，尚未实现）。"""
    raise NotImplementedError("cells 阶段尚未实现，将由后续任务补全骨干、训练循环与断点恢复")


def run_evaluate_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """四格全部封印后的目标年评价（骨架占位，尚未实现）。"""
    raise NotImplementedError("evaluate 阶段尚未实现，将由后续任务补全封印与评价逻辑")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    validate_config(config)
    if args.validate_config:
        print("配置核验通过")
        return 0
    if args.stage is None:
        print("必须指定 --stage 以进入对应实验阶段", file=sys.stderr)
        return 2
    dispatch = {
        "select-input": run_select_input_stage,
        "select-optimizer": run_select_optimizer_stage,
        "cells": run_cells_stage,
        "evaluate": run_evaluate_stage,
    }
    try:
        dispatch[args.stage](config, args)
    except NotImplementedError as error:
        logger.error("阶段未实现：%s", error)
        return 3
    except Exception:
        logger.exception("阶段执行失败：%s", args.stage)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
