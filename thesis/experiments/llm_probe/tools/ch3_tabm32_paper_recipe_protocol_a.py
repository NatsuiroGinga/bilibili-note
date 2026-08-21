# -*- coding: utf-8 -*-
"""TabM32 骨干专属论文配方协议 A 四格实验工具（任务 1 至 4）。

本文件目前实现：

- 任务 1：模块级冻结常量、配置校验 ``validate_config`` 与命令行入口的阶段分发骨架。
- 任务 2：字段基数收据消费 ``load_cardinality_receipt``、参数量闭式
  ``expected_parameter_count``，以及两个输入接口候选的拟合与应用
  ``fit_input_transform`` / ``InputTransform``。
- 任务 3：三层 BatchEnsemble 骨干 ``LinearBatchEnsemble`` / ``TabM32Backbone``
  与两个机制开关（因果前缀聚合、实体级可学幂平均池化）的边界断言。
- 任务 4：梯度累积训练循环 ``train_cell``、协议 A 源年切分 ``source_split``
  与逐轮最早最大验证逐流 AP 的检查点选择。

``select-input``、``select-optimizer``、``cells``、``evaluate`` 四个阶段的编排、
断点恢复、选择封印与目标年评价由后续任务继续叠加，本文件只为它们预留分发位置。

精度合同：本运行走 RTX 5090 神经训练默认配置 ``cuda-bf16-amp-fp32-sensitive-v1``
（BF16 autocast、参数与优化器状态保持 FP32、敏感计算进 FP32 岛、不用 GradScaler），
经 ``tools/neural_precision_runtime.py`` 接入，不自建第二套精度、累积或收据实现。

按仓库规则，numpy、scikit-learn 与 torch 的导入一律延迟到真正需要它们的函数内部：
``--validate-config`` 只做纯 Python 字典/字符串比对与纯标准库的精度合同校验，
不应因为本机 ``.venv`` 缺少这些依赖而失败。模块顶层因此只导入
``argparse``、``json``、``logging``、``sys``、``pathlib``、``typing``。
``neural_precision_runtime`` 只依赖标准库，但仍按同一纪律延迟导入。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 允许以 `python tools/ch3_tabm32_paper_recipe_protocol_a.py` 之外的方式调用时
# 仍能找到同目录的 neural_precision_runtime，与仓库既有工具同一写法。
TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

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
# 精度合同接入常量（2026-08-21 Codex 裁定的 RTX 5090 神经训练默认配置）
# ---------------------------------------------------------------------------

# 依据：thesis/experiments/llm_probe/AGENTS.md「PyTorch 训练与显存」条，
# 合同定义见 configs/neural-precision-profiles-v1.json，运行时实现见
# tools/neural_precision_runtime.py。本运行不走 FP32 或 FP16 例外。
PRECISION_PROFILE_ID = "cuda-bf16-amp-fp32-sensitive-v1"
PRECISION_CONTRACT_FILENAME = "neural-precision-profiles-v1.json"

# 有效批的对象单位是序列，损失归一化单位是流；与精度合同 integration_example
# 中登记的 N-12 数值（有效批 64 序列、微批 4 序列、累积 16、按流归一化）一致。
EFFECTIVE_BATCH_ITEM_UNIT = "sequence"
NORMALIZATION_UNIT = "flow"

# 各计算类型的元素字节数，用于按精度合同而不是写死 4 字节来预算展开张量。
PRECISION_DTYPE_BYTES: dict[str, int] = {"bfloat16": 2, "float16": 2, "float32": 4}

# 主机侧 InputTransform.apply 的输出恒为 float32，与设备端计算类型无关。
HOST_FEATURE_DTYPE_BYTES = 4

# 与既有协议 A 工具逐字一致的源年形状身份，供训练前机械断言。
LSPR23_SEQUENCE_COUNT = 271_815
PROTOCOL_A_SEQUENCE_LENGTH = 128
PROTOCOL_A_SPLIT_STATISTICS: dict[str, int] = {
    "entity_count": 150_680,
    "train_sequences": 208_598,
    "validation_sequences": 22_444,
    "train_validation_row_intersection": 0,
}

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
# 精度合同接入（复用 tools/neural_precision_runtime.py，不另写一套）
# ---------------------------------------------------------------------------


def _precision_module() -> Any:
    """延迟导入共享精度脚手架。

    该模块只依赖标准库，本函数仍延迟导入以保持模块顶层导入清单稳定。
    """
    import neural_precision_runtime

    return neural_precision_runtime


def precision_contract_path() -> Path:
    """默认精度合同路径：与本工具同仓库的 ``configs/neural-precision-profiles-v1.json``。"""
    return TOOL_DIR.parent / "configs" / PRECISION_CONTRACT_FILENAME


def load_precision_contract(path: Path | None = None) -> dict[str, Any]:
    """加载并校验精度合同；不需要安装 PyTorch。"""
    module = _precision_module()
    resolved = path or precision_contract_path()
    contract = module.load_and_validate_contract(resolved)
    if contract["default_profile"] != PRECISION_PROFILE_ID:
        raise ValueError(
            f"精度合同默认配置为 {contract['default_profile']}，与本运行冻结的 {PRECISION_PROFILE_ID} 不符"
        )
    return contract


def resolve_precision_profile(
    device_type: str, torch_module: Any, contract: dict[str, Any] | None = None
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """核验真实设备能力后返回 ``(合同, 精度配置, 配置标识)``。

    ``profile_for_device`` 只在非 CUDA 设备上返回回退标识；CUDA 无 BF16 时不静默降级，
    而是由 ``validate_runtime_profile`` 抛错，要求显式改走 FP16 回退并留硬件收据。
    本运行按合同只接受 CUDA BF16 默认配置。
    """
    module = _precision_module()
    resolved_contract = contract or load_precision_contract()
    profile_id = module.profile_for_device(resolved_contract, device_type)
    if profile_id != PRECISION_PROFILE_ID:
        raise RuntimeError(
            f"设备类型 {device_type} 解析出的精度配置为 {profile_id}，"
            f"本运行只接受 {PRECISION_PROFILE_ID}；非 CUDA 或无 BF16 的环境须先取得显式例外收据"
        )
    profile = module.validate_runtime_profile(
        resolved_contract, profile_id, device_type, torch_module
    )
    logger.info(
        "精度配置已核验：%s（计算类型=%s，autocast=%s，GradScaler=%s，参数=%s，优化器状态=%s）",
        profile_id, profile["compute_dtype"], profile["autocast"], profile["grad_scaler"],
        profile["parameter_dtype"], profile["optimizer_state_dtype"],
    )
    return resolved_contract, profile, profile_id


def compute_dtype_bytes(profile: dict[str, Any]) -> int:
    """按精度配置登记的计算类型返回元素字节数，不写死 4 字节。"""
    dtype_name = profile["compute_dtype"]
    if dtype_name not in PRECISION_DTYPE_BYTES:
        raise ValueError(f"精度配置登记了未核验的计算类型：{dtype_name}")
    return PRECISION_DTYPE_BYTES[dtype_name]


def tensor_upper_bounds(config: dict[str, Any], output_dimension: int, profile: dict[str, Any]) -> dict[str, int]:
    """按真实展开维度乘积给出单微批张量上界，不按参数量估算。

    冻结配方第 150 行登记的两个量在此重算：隐藏张量 ``4×128×32×512×4 = 32 MiB``、
    因果前缀拼接 ``64 MiB``。这两个量按 FP32 登记（配方冻结时的口径），
    autocast 只把矩阵乘输入下转为计算类型，逐元素缩放与 FP32 岛内的归约仍是 FP32，
    因此 FP32 口径是保守上界，计算类型口径是矩阵乘输入的实际副本大小，两者都记录。
    """
    candidate = config["candidate"]
    training = config["training"]
    micro_batch = candidate["micro_batch_sequences"]
    members = candidate["ensemble_members"]
    hidden_size = candidate["hidden_size"]
    length = training["sequence_length"]
    element_bytes = compute_dtype_bytes(profile)

    host_dense_bytes = micro_batch * length * output_dimension * HOST_FEATURE_DTYPE_BYTES
    expanded_elements = micro_batch * members * length * output_dimension
    hidden_elements = micro_batch * members * length * hidden_size
    return {
        "micro_batch_host_dense_input_bytes": host_dense_bytes,
        "micro_batch_device_expanded_input_bytes": expanded_elements * element_bytes,
        "micro_batch_device_expanded_input_fp32_bytes": expanded_elements * HOST_FEATURE_DTYPE_BYTES,
        "hidden_tensor_bytes": hidden_elements * HOST_FEATURE_DTYPE_BYTES,
        "hidden_tensor_compute_dtype_bytes": hidden_elements * element_bytes,
        "causal_prefix_concat_bytes": 2 * hidden_elements * HOST_FEATURE_DTYPE_BYTES,
        "compute_dtype_bytes": element_bytes,
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

    if config.get("precision_profile_id") != PRECISION_PROFILE_ID:
        raise ValueError(
            f"precision_profile_id 必须为 {PRECISION_PROFILE_ID}："
            "本运行按 RTX 5090 神经训练默认精度配置执行，FP32 与 FP16 只作有收据的显式例外"
        )
    if "precision_pending_ruling" in config:
        raise ValueError(
            "precision_pending_ruling 必须删除：精度冲突已由 Codex 裁定为 BF16 默认配置，"
            "配置中不得再保留待裁字段"
        )
    # 只做纯标准库的合同校验，不导入 torch，保证 --validate-config 在无 GPU 开发机可跑。
    contract = load_precision_contract()
    profile = _precision_module().get_profile(contract, PRECISION_PROFILE_ID)
    if profile["compute_dtype"] != "bfloat16" or profile["grad_scaler"] is not False:
        raise ValueError("精度配置不是 BF16 且不使用 GradScaler 的默认配置")
    example = contract["integration_example"]
    if (
        example["effective_batch_items"] != training["effective_batch_size"]
        or example["microbatch_items"] != candidate["micro_batch_sequences"]
        or example["accumulation_steps"] != candidate["gradient_accumulation_steps"]
    ):
        raise ValueError(
            "精度合同 integration_example 登记的 N-12 批量与本配置不符；"
            "有效批、微批与累积次数以本配置为准，须先修正合同再运行"
        )

    if config.get("swanlab") != _EXPECTED_SWANLAB:
        raise ValueError("swanlab 上报身份合同不符")

    if config.get("single_run_directly_comparable") is not True:
        raise ValueError("single_run_directly_comparable 必须为真")
    if config.get("formal_paper_evidence") is not False or config.get("independent_test") is not False:
        raise ValueError("本次重跑不能宣称正式论文证据或独立测试")


# ---------------------------------------------------------------------------
# 字段基数收据消费与输入接口构造（任务 2）
# ---------------------------------------------------------------------------

CARDINALITY_RECEIPT_SCHEMA_VERSION = "ch3-lspr23-field-cardinality-receipt-v1"
CARDINALITY_RECEIPT_RUN_ID = "ch3-lspr23-field-cardinality-receipt-v1"

# 冻结缓存 X23 的形状身份，与 tools/ch3_lspr23_field_cardinality_receipt.py 第 292 行一致。
DIJK_FEATURE_COUNT = 83
LSPR23_FLOW_COUNT = 16_353_511

# TabM 官方数值预处理策略 NOISY_QUANTILE 的逐字常量。
#
# 论文依据：Gorishniy 等《TabM: Advancing Tabular Deep Learning with Parameter-Efficient
#   Ensembling》ICLR 2025 附录 D.2「Data preprocessing」。原件
#   raw/papers/methodology/2025-Gorishniy-TabM-Parameter-Efficient-Ensembling.pdf，
#   SHA-256 a6988aa10d726e99c706dc92856c5a07f4e3f9fa854d08c8f854f06dc83ea34f。原文为
#   "we used a slightly modified version of the quantile normalization from the
#   Scikit-learn package (Pedregosa et al., 2011) (see the source code)"，即论文本身
#   不写具体改动，把改动交给官方源码；因此下列常量不能由论文正文推出，只能取自源码。
# 源码依据：yandex-research/tabm 固定提交 28e47ae301c92ec37787dde1ce923a0793f405b4
#   （Apache-2.0）的 paper/lib/data.py，函数 transform_num 的 NumPolicy.NOISY_QUANTILE
#   分支。该分支相对 scikit-learn 默认值的四处改动即为论文所称的「slightly modified」：
#   输出分布改为 normal、关闭子采样、按训练行数推导地标数、拟合前叠加 1e-5 高斯噪声。
# 适用边界：这些是官方跨数据集的预处理协议，不是本课题实测最优值；它们只固定预处理口径，
#   不接触 LSPR24，也不参与任何依据指标的调整。
QUANTILE_OUTPUT_DISTRIBUTION = "normal"
QUANTILE_SUBSAMPLE = 1_000_000_000
QUANTILE_NOISE_STANDARD_DEVIATION = 1e-5
QUANTILE_ROWS_PER_LANDMARK = 30
QUANTILE_LANDMARK_MAXIMUM = 1000
QUANTILE_LANDMARK_MINIMUM = 10

# 生成拟合噪声时的单次抽取元素数，只为把 float64 临时缓冲限制在 32 MiB 以内；
# 已实测分块抽取与一次性抽取的随机流逐位相同，因此不改变数值结果。
QUANTILE_NOISE_CHUNK_ELEMENTS = 4_194_304

# 组装式变换器的实现漂移绊线，不是科学阈值。推导：地标数为 n 时中位数附近一格地标的
# 概率间距为 1/(n-1)；标准正态分位函数在 p=0.5 处斜率为 sqrt(2*pi)≈2.5066，
# 故 n=1000 时插值位移的解析上界约 2.5e-3。下列容差约为该上界的 40 倍，
# 只在 sklearn 行为实质改变（输出分布变更、网格转置、私有属性语义变化）时触发。
QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE = 0.1


def expected_parameter_count(input_dimension: int) -> int:
    """按冻结配方 ``BE(a,b,k)=a*b+k*a+k*b+k*b`` 解出的闭式。

    冻结配方（`.Codex/docs/RWKV/2026-08-20-骨干专属论文配方冻结/骨干专属论文配方冻结.md`，
    SHA-256 ``3b1e3103...``）第 160 至 170 行给出逐层式：

        P = BE(d_in, d, k) + BE(d, d, k) + BE(2d, d, k) + k*Linear(d,1) + p_log

    代入 ``d=512``、``k=32`` 后 ``BE(d_in,512,32) = 544*d_in + 32768``，其余三项为常数，
    合并得 ``544*d_in + 950305``。``d_in=83`` 时恰为冻结值 995,457。
    """
    return 544 * input_dimension + 950_305


def _canonical_sha256(value: Any) -> str:
    """对可 JSON 序列化对象取规范化 SHA-256，与收据工具第 51 至 53 行同口径。"""
    import hashlib

    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_cardinality_receipt(path: str, config: dict[str, Any]) -> dict[str, Any]:
    """读取并机械校验 LSPR23 训练区字段基数收据。

    收据由 Codex 的独立诊断工具产出，本工具只消费不产出。
    """
    receipt_path = Path(path)
    if not receipt_path.exists():
        raise FileNotFoundError(
            f"缺少字段基数收据：{receipt_path}。"
            "输入适配封印前必须等待 Codex 产出该收据，见看板 N-12 的 "
            "WAITING_FOR_CODEX_CARDINALITY_RECEIPT"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not receipt.get("complete"):
        raise RuntimeError("字段基数收据未标记完成，拒绝消费")
    expected_fields = (
        list(config["field_groups"]["categorical"])
        + list(config["field_groups"]["boolean"])
    )
    if list(receipt["fields"].keys()) != expected_fields:
        raise RuntimeError(f"收据字段清单或顺序不符：{list(receipt['fields'].keys())}")
    split = receipt["protocol_a_source_split"]["statistics"]
    if (split["entity_count"], split["train_sequences"], split["validation_sequences"]) != (
        150_680, 208_598, 22_444
    ):
        raise RuntimeError(f"收据的协议 A 切分身份与本运行不符：{split}")

    # 以下为消费端追加的机械校验，收据自身不保证消费者按同一身份读取。
    if receipt.get("schema_version") != CARDINALITY_RECEIPT_SCHEMA_VERSION:
        raise RuntimeError(f"收据模式版本不符：{receipt.get('schema_version')}")
    if receipt.get("run_id") != CARDINALITY_RECEIPT_RUN_ID:
        raise RuntimeError(f"收据运行身份不符：{receipt.get('run_id')}")
    if receipt["identity"].get("target_year_arrays_read") != 0:
        raise RuntimeError("收据声明读取过目标年数组，拒绝消费")

    effective_flows = receipt["training_effective_flows"]["effective_flows"]
    if not isinstance(effective_flows, int) or not 0 < effective_flows <= LSPR23_FLOW_COUNT:
        raise RuntimeError(f"收据训练有效流数不合法：{effective_flows}")

    seen_indices: set[int] = set()
    for name, entry in receipt["fields"].items():
        index = entry.get("dijk_feature_index")
        if not isinstance(index, int) or not 0 <= index < DIJK_FEATURE_COUNT:
            raise RuntimeError(f"字段 {name} 的 dijk_feature_index 越界：{index}")
        if index in seen_indices:
            raise RuntimeError(f"字段 {name} 的 dijk_feature_index 与其他字段重复：{index}")
        seen_indices.add(index)
        # 与 training_effective_flows 交叉校验拟合覆盖的行数。收据第 247 行已有等价断言，
        # 这里重算一次，防止收据与本运行的有效流口径不一致。
        covered = entry["finite_count"] + entry["missing_count"]
        if covered != effective_flows:
            raise RuntimeError(
                f"字段 {name} 的 finite_count 加 missing_count 为 {covered}，"
                f"未覆盖训练有效流 {effective_flows}"
            )
        # integer_like 只作事实记录写入封印，不参与任何分支：独热只要求同一原值映射到同一列，
        # 该性质由 float32 取值相等判定，与这些浮点数是否可解释为原始端口号无关。
        logger.info(
            "收据字段 %s：unique_count=%d，missing_fraction=%.6g，integer_like=%s，"
            "min=%s，max=%s，dijk_feature_index=%d",
            name, entry["unique_count"], entry["missing_fraction"], entry["integer_like"],
            entry["min"], entry["max"], index,
        )
    return receipt


def resolve_quantile_landmark_count(row_count: int) -> int:
    """按官方 NOISY_QUANTILE 的 ``max(min(n // 30, 1000), 10)`` 推导分位数地标数。"""
    return max(
        min(row_count // QUANTILE_ROWS_PER_LANDMARK, QUANTILE_LANDMARK_MAXIMUM),
        QUANTILE_LANDMARK_MINIMUM,
    )


def resolve_missing_indicator_policy(receipt: dict[str, Any]) -> bool:
    """裁决是否引入缺失指示位，两个候选必须一致。

    实施计划第 75 行规定：若七个字段的 ``missing_fraction`` 全为 0 则不引入指示位。
    冻结配置把候选一的输入维钉为 83、参数量钉为 995,457，二者只在无指示位时成立；
    因此一旦收据显示存在缺失，输入维合同需要重新裁定，这里停止而不是自行加维。
    """
    nonzero = {
        name: entry["missing_fraction"]
        for name, entry in receipt["fields"].items()
        if entry["missing_fraction"] != 0
    }
    if nonzero:
        raise RuntimeError(
            f"收据显示以下字段存在缺失：{nonzero}。按实施计划第 75 行需引入缺失指示位，"
            "但冻结配置的 input_dimension=83 与 parameter_count=995457 不含指示位维度，"
            "属于合同冲突，须先重新裁定输入维合同再运行，本工具拒绝自行加维"
        )
    logger.info("七个字段的 missing_fraction 全为 0，两个候选一致地不引入缺失指示位")
    return False


def project_input_dimension(candidate_key: str, receipt: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """拟合前用收据的 unique_count 预算输出维、参数量与稠密输入字节。

    先预算再扫描，避免全量拟合之后才发现输出维不可行。
    """
    groups = config["field_groups"]
    numeric_count = groups["numeric_count"]
    categorical = list(groups["categorical"])
    boolean = list(groups["boolean"])
    if candidate_key == "tabm32-input-all-numeric":
        output_dimension = groups["total_count"]
        vocabulary_widths: dict[str, int] = {}
    elif candidate_key == "tabm32-input-type-partitioned":
        # 每个离散字段占 词表长度 + 1 列，加一为固定越界桶。
        vocabulary_widths = {
            name: receipt["fields"][name]["unique_count"] + 1 for name in categorical
        }
        output_dimension = numeric_count + sum(vocabulary_widths.values()) + len(boolean)
    else:
        raise ValueError(f"未知输入候选：{candidate_key}")

    # 张量上界必须区分两个量，不能合并成一个含糊的「稠密输入」：
    #   1) 主机侧 InputTransform.apply 产出的单微批矩阵是 (micro_batch*T, d)，不含成员维；
    #   2) 进第一层 BatchEnsemble 之前必须按成员数复制成 N×k×T×d，成员维在第 1 轴
    #      （LinearBatchEnsemble.forward 的 values * r.unsqueeze(0).unsqueeze(2) 要求如此）。
    # 此前只算第 1 个量并当作显存可行性依据，对 32 成员低估 32 倍，属实测确认的缺陷。
    profile = _precision_module().get_profile(load_precision_contract(), PRECISION_PROFILE_ID)
    bounds = tensor_upper_bounds(config, output_dimension, profile)
    projection = {
        "candidate_key": candidate_key,
        "output_dimension": output_dimension,
        "vocabulary_widths": vocabulary_widths,
        "parameter_count": expected_parameter_count(output_dimension),
        "ensemble_members": config["candidate"]["ensemble_members"],
        "precision_profile_id": PRECISION_PROFILE_ID,
        "tensor_upper_bounds": bounds,
        # 保留两个显式键名，便于收据与日志逐字对表。
        "micro_batch_host_dense_input_bytes": bounds["micro_batch_host_dense_input_bytes"],
        "micro_batch_device_expanded_input_bytes": bounds["micro_batch_device_expanded_input_bytes"],
    }
    logger.info(
        "输入维预算 %s：输出维=%d，参数量=%d，成员数=%d",
        candidate_key, output_dimension, projection["parameter_count"],
        projection["ensemble_members"],
    )
    logger.info(
        "单微批主机稠密输入（无成员维，float32）=%.2f MiB；"
        "单微批设备展开输入（含成员维，%s）=%.2f MiB，FP32 保守口径=%.2f MiB",
        bounds["micro_batch_host_dense_input_bytes"] / 1024 / 1024,
        profile["compute_dtype"],
        bounds["micro_batch_device_expanded_input_bytes"] / 1024 / 1024,
        bounds["micro_batch_device_expanded_input_fp32_bytes"] / 1024 / 1024,
    )
    logger.info(
        "隐藏张量上界=%.2f MiB，因果前缀拼接上界=%.2f MiB（均按 FP32 保守口径）",
        bounds["hidden_tensor_bytes"] / 1024 / 1024,
        bounds["causal_prefix_concat_bytes"] / 1024 / 1024,
    )
    if vocabulary_widths:
        logger.info("各离散字段独热块宽度（含越界桶）：%s", vocabulary_widths)
    # GPU 显存准入阈值仍为待定（配置 resource_contract.minimum_free_gpu_memory_mib 为 null），
    # 因此这里只给出可核对的预算事实，不设置未经依据的硬阈值。
    logger.warning(
        "输出维可行性硬阈值待定：resource_contract.minimum_free_gpu_memory_mib 仍为 null，"
        "本预算只提供事实，不构成准入判定"
    )
    return projection


class InputTransform:
    """在 LSPR23 协议 A 训练区拟合完成后冻结的输入变换。

    ``apply`` 只应用不重新拟合：验证区、时间尾部区与 LSPR24 共用同一份状态，
    目标年出现的词表外取值一律落入既有越界桶。

    本类刻意不使用 ``dataclasses``，以保持本模块顶层只导入
    ``argparse/json/logging/sys/pathlib/typing``；全部属性在构造后不再改写。
    """

    def __init__(
        self,
        *,
        candidate_key: str,
        output_dimension: int,
        state_hash: str,
        fitted_row_count: int,
        quantile_landmark_count: int,
        numeric_feature_indices: tuple[int, ...],
        numeric_fill_values: tuple[float, ...],
        quantile_transformer: Any,
        categorical_field_names: tuple[str, ...],
        categorical_feature_indices: tuple[int, ...],
        categorical_vocabularies: tuple[tuple[float, ...], ...],
        boolean_field_names: tuple[str, ...],
        boolean_feature_indices: tuple[int, ...],
        boolean_true_values: tuple[float, ...],
        boolean_false_values: tuple[float, ...],
    ) -> None:
        self.candidate_key = candidate_key
        self.output_dimension = output_dimension
        self.state_hash = state_hash
        self.fitted_row_count = fitted_row_count
        self.quantile_landmark_count = quantile_landmark_count
        self.numeric_feature_indices = numeric_feature_indices
        self.numeric_fill_values = numeric_fill_values
        self.quantile_transformer = quantile_transformer
        self.categorical_field_names = categorical_field_names
        self.categorical_feature_indices = categorical_feature_indices
        self.categorical_vocabularies = categorical_vocabularies
        self.boolean_field_names = boolean_field_names
        self.boolean_feature_indices = boolean_feature_indices
        self.boolean_true_values = boolean_true_values
        self.boolean_false_values = boolean_false_values
        # 诊断计数器，不属于冻结状态，也不参与 state_hash：布尔列只有 2 列冻结维、
        # 没有越界桶，训练区未见的第三取值与 NaN 都会被静默记 0。这里累计吸收次数，
        # 使目标年分布漂移可被发现而不是无声并入「假」类。
        self.boolean_absorption_counts: dict[str, int] = {name: 0 for name in boolean_field_names}
        self._boolean_absorption_warned: set[str] = set()

    def apply(self, values: Any) -> Any:
        """把 ``(n, 83)`` 的 float32 原值批变换为 ``(n, output_dimension)`` 的 float32。

        缺失值先按训练区中位数填补再做分位数变换，保证不会有 ``NaN`` 进入矩阵乘法。
        """
        import numpy as np

        array = np.asarray(values)
        if array.ndim != 2 or array.shape[1] != DIJK_FEATURE_COUNT:
            raise ValueError(f"输入批形状必须为 (n, {DIJK_FEATURE_COUNT})，实际 {array.shape}")
        row_count = array.shape[0]
        output = np.zeros((row_count, self.output_dimension), dtype=np.float32)

        numeric_width = len(self.numeric_feature_indices)
        numeric = array[:, list(self.numeric_feature_indices)].astype(np.float32, copy=True)
        missing = np.isnan(numeric)
        if missing.any():
            fill = np.asarray(self.numeric_fill_values, dtype=np.float32)
            numeric[missing] = np.broadcast_to(fill, numeric.shape)[missing]
        # scikit-learn 对超出拟合范围的取值本身就截断到训练端点输出，无需另加裁剪。
        output[:, :numeric_width] = self.quantile_transformer.transform(numeric)

        offset = numeric_width
        rows = np.arange(row_count)
        for index, vocabulary in zip(self.categorical_feature_indices, self.categorical_vocabularies, strict=True):
            width = len(vocabulary) + 1
            # 加 +0.0 把 -0.0 规范化为 +0.0，与收据 np.unique 的折叠口径一致。
            column = array[:, index].astype(np.float32, copy=True) + np.float32(0.0)
            table = np.asarray(vocabulary, dtype=np.float32)
            position = np.searchsorted(table, column)
            np.clip(position, 0, len(table) - 1, out=position)
            hit = table[position] == column  # NaN 与词表外取值都判否，落入越界桶
            output[rows, offset + np.where(hit, position, width - 1)] = 1.0
            offset += width

        for slot, index in enumerate(self.boolean_feature_indices):
            column = array[:, index].astype(np.float32, copy=False)
            true_value = np.float32(self.boolean_true_values[slot])
            false_value = np.float32(self.boolean_false_values[slot])
            is_true = column == true_value
            output[:, offset + slot] = is_true.astype(np.float32)
            # 训练区只见过 {false_value, true_value} 两个取值；其余取值与 NaN 都会落到 0。
            absorbed = int((~(is_true | (column == false_value))).sum())
            if absorbed:
                name = self.boolean_field_names[slot]
                self.boolean_absorption_counts[name] += absorbed
                if name not in self._boolean_absorption_warned:
                    self._boolean_absorption_warned.add(name)
                    logger.warning(
                        "布尔字段 %s 出现训练区未见取值（含 NaN）%d 个，按 0 静默吸收；"
                        "该列冻结维只有 2 列、无越界桶，累计次数见 boolean_absorption_counts",
                        name, absorbed,
                    )
        return output


def _gather_training_column(
    matrix: Any, feature_index: int, train_flow_mask: Any, row_count: int, chunk_rows: int
) -> Any:
    """按行分块从 mmap 的 X23 中取出某字段在训练区有效流上的取值。

    固定上界：返回缓冲为 ``row_count × 4`` 字节；每块临时列切片为 ``chunk_rows × 4`` 字节。
    全程不把 ``(16353511, 83)`` 的整矩阵读入内存。
    """
    import numpy as np

    selected = np.empty(row_count, dtype=np.float32)
    written = 0
    for start in range(0, len(train_flow_mask), chunk_rows):
        stop = min(start + chunk_rows, len(train_flow_mask))
        local_mask = train_flow_mask[start:stop]
        taken = int(local_mask.sum())
        if taken == 0:
            continue
        block = np.asarray(matrix[start:stop, feature_index], dtype=np.float32)
        selected[written : written + taken] = block[local_mask]
        written += taken
    if written != row_count:
        raise RuntimeError(f"字段 {feature_index} 实际取出 {written} 行，与训练有效流 {row_count} 不符")
    return selected


def _fit_quantile_column(values: Any, landmark_count: int, seed: int) -> tuple[Any, float]:
    """在单个字段上拟合官方 NOISY_QUANTILE 分位数网格，并返回训练区中位数。

    返回的是该字段的 ``quantiles_`` 列与中位数；调用方把各列堆叠为联合变换器。
    已实测逐列拟合堆叠所得网格与整体拟合逐位相同，故此处的分列拟合不改变数值结果。
    """
    import numpy as np
    from sklearn.preprocessing import QuantileTransformer

    finite = np.isfinite(values)
    finite_count = int(finite.sum())
    if finite_count == 0:
        raise RuntimeError("字段在训练区全为缺失，无法拟合分位数规范化")
    # 中位数在 NaN 填补时使用；np.nanmedian 忽略 NaN，与「NaN 不参与估计」一致。
    median = float(np.nanmedian(values))

    # 官方做法：拟合前给训练数据叠加 1e-5 高斯噪声，打散重复值以免分位数地标退化。
    # 分块抽取只为限制 float64 临时缓冲，随机流与一次性抽取逐位相同。
    noisy = values.copy()
    state = np.random.RandomState(seed)
    for start in range(0, len(noisy), QUANTILE_NOISE_CHUNK_ELEMENTS):
        stop = min(start + QUANTILE_NOISE_CHUNK_ELEMENTS, len(noisy))
        noisy[start:stop] += state.normal(
            0.0, QUANTILE_NOISE_STANDARD_DEVIATION, stop - start
        ).astype(np.float32)

    transformer = QuantileTransformer(
        n_quantiles=landmark_count,
        output_distribution=QUANTILE_OUTPUT_DISTRIBUTION,
        subsample=QUANTILE_SUBSAMPLE,
        random_state=seed,
    )
    transformer.fit(noisy.reshape(-1, 1))
    return transformer, median


def _fit_categorical_vocabulary(
    matrix: Any, feature_index: int, train_flow_mask: Any, chunk_rows: int
) -> tuple[float, ...]:
    """在训练区有效流上建立某离散字段的完整词表，返回升序排列的 float32 取值。

    词表来源必须是训练区数据本身：收据的 ``top_values`` 只含前二十个取值，
    而 ``unique_count`` 可能远大于二十，靠收据建不出完整词表。
    固定上界：只保留去重后的取值集合，不保留任何逐行历史。
    """
    import numpy as np

    vocabulary: Any = np.empty(0, dtype=np.float32)
    for start in range(0, len(train_flow_mask), chunk_rows):
        stop = min(start + chunk_rows, len(train_flow_mask))
        local_mask = train_flow_mask[start:stop]
        if not local_mask.any():
            continue
        block = np.asarray(matrix[start:stop, feature_index], dtype=np.float32)[local_mask]
        block = block[np.isfinite(block)] + np.float32(0.0)  # NaN 不进词表；-0.0 归一为 +0.0
        vocabulary = np.union1d(vocabulary, np.unique(block))
    return tuple(float(value) for value in vocabulary)


def fit_input_transform(
    candidate_key: str,
    cache_root: str,
    train_flow_mask: Any,
    receipt: dict[str, Any],
    *,
    config: dict[str, Any],
    seed: int = 42,
) -> InputTransform:
    """在 LSPR23 协议 A 训练区有效流上拟合指定候选的输入变换并冻结。

    ``X23`` 一律以 ``mmap_mode="r"`` 打开并逐字段分块处理；任一时刻的显式分配都有固定
    上界，与字段数无关。拟合状态（分位数网格、词表、越界桶位置、缺失填充值）全部并入
    ``state_hash``，供选择封印追溯。
    """
    import hashlib

    import numpy as np
    import sklearn
    from sklearn.preprocessing import QuantileTransformer

    if candidate_key not in {candidate["key"] for candidate in INPUT_CANDIDATES}:
        raise ValueError(f"未知输入候选：{candidate_key}")
    resolve_missing_indicator_policy(receipt)
    projection = project_input_dimension(candidate_key, receipt, config)

    flow_mapping = receipt["training_effective_flows"]
    row_count = flow_mapping["effective_flows"]
    mask = np.asarray(train_flow_mask)
    if mask.dtype != np.bool_ or mask.shape != (LSPR23_FLOW_COUNT,):
        raise RuntimeError(f"训练有效流掩码类型或形状不符：dtype={mask.dtype}，shape={mask.shape}")
    if int(mask.sum()) != row_count:
        raise RuntimeError(f"掩码有效流数 {int(mask.sum())} 与收据 {row_count} 不符")
    mask_digest = hashlib.sha256(mask.tobytes()).hexdigest()
    if mask_digest != flow_mapping["effective_flow_mask_sha256"]:
        raise RuntimeError("训练有效流掩码哈希与收据不符，拟合区身份不一致")

    chunk_rows = receipt["resource"]["chunk_rows"]
    if not isinstance(chunk_rows, int) or chunk_rows <= 0:
        raise RuntimeError(f"收据的分块行数不合法：{chunk_rows}")

    matrix_path = Path(cache_root) / "X23.npy"
    if not matrix_path.is_file():
        raise FileNotFoundError(f"缺少冻结数组：{matrix_path}")
    matrix = np.load(matrix_path, mmap_mode="r", allow_pickle=False)
    if matrix.shape != (LSPR23_FLOW_COUNT, DIJK_FEATURE_COUNT):
        raise RuntimeError(f"X23 形状不符：{matrix.shape}")
    if matrix.dtype != np.float32:
        raise RuntimeError(f"X23 类型不符：{matrix.dtype}")

    field_indices = {name: entry["dijk_feature_index"] for name, entry in receipt["fields"].items()}
    categorical_names = tuple(config["field_groups"]["categorical"])
    boolean_names = tuple(config["field_groups"]["boolean"])
    partitioned = candidate_key == "tabm32-input-type-partitioned"
    if partitioned:
        reserved = set(field_indices.values())
        numeric_indices = tuple(i for i in range(DIJK_FEATURE_COUNT) if i not in reserved)
        if len(numeric_indices) != config["field_groups"]["numeric_count"]:
            raise RuntimeError(
                f"数值字段数 {len(numeric_indices)} 与合同 {config['field_groups']['numeric_count']} 不符"
            )
    else:
        # 候选一把 83 个字段全部声明为数值，统一施加同一分位数规范化。
        numeric_indices = tuple(range(DIJK_FEATURE_COUNT))

    landmark_count = resolve_quantile_landmark_count(row_count)
    logger.info(
        "开始拟合输入变换 %s：训练有效流=%d，分位数地标=%d，数值字段=%d，分块行数=%d",
        candidate_key, row_count, landmark_count, len(numeric_indices), chunk_rows,
    )

    quantile_columns: list[Any] = []
    fill_values: list[float] = []
    references: Any = None
    landmark_actual: int | None = None
    for position, feature_index in enumerate(numeric_indices, start=1):
        column = _gather_training_column(matrix, feature_index, mask, row_count, chunk_rows)
        # 每个字段使用独立派生种子。官方对 (n, d) 训练矩阵一次性抽取噪声，逐字段处理无法
        # 复现同一随机流（复现需一次生成 n×d 个 float64，约 10 GiB）；此处每元素仍为
        # 独立同分布 N(0, 1e-5)，只是随机流分配方式不同，是显式记录的实现偏离。
        transformer, median = _fit_quantile_column(column, landmark_count, seed + feature_index)
        quantile_columns.append(transformer.quantiles_[:, 0])
        fill_values.append(median)
        if references is None:
            references = transformer.references_.copy()
            landmark_actual = int(transformer.n_quantiles_)
        del column
        if position % 10 == 0 or position == len(numeric_indices):
            logger.info("分位数拟合进度 %d/%d", position, len(numeric_indices))

    # 把逐列网格堆叠为单个联合变换器：实测逐列拟合与整体拟合的 quantiles_ 逐位相同，
    # 且有限元素上的 transform 输出最大绝对差为 0.0，故组装不改变数值语义，只减少调用开销。
    quantile_transformer = QuantileTransformer(
        n_quantiles=landmark_count,
        output_distribution=QUANTILE_OUTPUT_DISTRIBUTION,
        subsample=QUANTILE_SUBSAMPLE,
        random_state=seed,
    )
    quantile_transformer.n_quantiles_ = landmark_actual
    quantile_transformer.quantiles_ = np.stack(quantile_columns, axis=1)
    quantile_transformer.references_ = references
    quantile_transformer.n_features_in_ = len(numeric_indices)

    # 组装式变换器直接写入了 scikit-learn 的私有拟合属性，未来版本一旦改变这些属性的
    # 语义就会静默产出错误数值。这里加一条运行时自检：把各字段的训练区中位数送进
    # transform，output_distribution="normal" 应把中位数映射到约 0；偏差超过绊线即停止。
    median_probe = np.asarray(fill_values, dtype=np.float32).reshape(1, -1)
    median_response = quantile_transformer.transform(median_probe)
    median_deviation = float(np.max(np.abs(median_response)))
    if median_deviation > QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE:
        raise RuntimeError(
            f"组装式分位数变换器自检失败：训练区中位数映射后的最大绝对值为 {median_deviation:.6g}，"
            f"超过绊线 {QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE}；"
            f"scikit-learn {sklearn.__version__} 的私有拟合属性语义可能已改变，拒绝继续拟合"
        )
    logger.info(
        "组装式变换器自检通过：中位数映射最大绝对值=%.6g（绊线 %.3g），scikit-learn=%s",
        median_deviation, QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE, sklearn.__version__,
    )

    vocabularies: list[tuple[float, ...]] = []
    categorical_indices: list[int] = []
    boolean_indices: list[int] = []
    boolean_true_values: list[float] = []
    boolean_false_values: list[float] = []
    if partitioned:
        for name in categorical_names:
            feature_index = field_indices[name]
            vocabulary = _fit_categorical_vocabulary(matrix, feature_index, mask, chunk_rows)
            declared = receipt["fields"][name]["unique_count"]
            if len(vocabulary) != declared:
                raise RuntimeError(
                    f"字段 {name} 训练区词表长度 {len(vocabulary)} 与收据 unique_count {declared} 不符，"
                    "说明拟合区与收据的切分身份不一致"
                )
            vocabularies.append(vocabulary)
            categorical_indices.append(feature_index)
            logger.info("离散字段 %s 词表长度 %d，独热块宽度 %d（末列为越界桶）", name, len(vocabulary), len(vocabulary) + 1)
        for name in boolean_names:
            entry = receipt["fields"][name]
            if entry["unique_count"] > 2:
                raise RuntimeError(
                    f"布尔字段 {name} 的 unique_count 为 {entry['unique_count']}，超过两个取值，"
                    "不满足论文 D.2 的二值特征定义"
                )
            if entry["unique_count"] == 1:
                logger.warning("布尔字段 %s 在训练区只有一个取值，该列在训练区恒为 1", name)
            boolean_indices.append(field_indices[name])
            boolean_true_values.append(float(entry["max"]))
            boolean_false_values.append(float(entry["min"]))
            logger.info(
                "布尔字段 %s 映射：max=%s 记为 1，min=%s 记为 0，其余取值与 NaN 静默记 0 并计数",
                name, entry["max"], entry["min"],
            )

    output_dimension = len(numeric_indices) + sum(len(v) + 1 for v in vocabularies) + len(boolean_indices)
    if output_dimension != projection["output_dimension"]:
        raise RuntimeError(
            f"实测输出维 {output_dimension} 与收据预算 {projection['output_dimension']} 不符"
        )
    # 上一条只是把实测值与本函数自己推出的预算相比，等于自己跟自己比。这里再与
    # 冻结配置登记的候选值做二方比对；候选二的冻结值当前为 null（待收据裁定），
    # 为 null 时跳过比较并把实测值记入日志，不自行回填冻结配置。
    frozen_candidate = next(
        candidate for candidate in INPUT_CANDIDATES if candidate["key"] == candidate_key
    )
    frozen_dimension = frozen_candidate["input_dimension"]
    frozen_parameters = frozen_candidate["parameter_count"]
    if frozen_dimension is not None and output_dimension != frozen_dimension:
        raise RuntimeError(
            f"候选 {candidate_key} 实测输出维 {output_dimension} 与冻结值 {frozen_dimension} 不符"
        )
    if frozen_parameters is not None and expected_parameter_count(output_dimension) != frozen_parameters:
        raise RuntimeError(
            f"候选 {candidate_key} 闭式参数量 {expected_parameter_count(output_dimension)} "
            f"与冻结值 {frozen_parameters} 不符"
        )
    if frozen_dimension is None or frozen_parameters is None:
        logger.warning(
            "候选 %s 的冻结 input_dimension/parameter_count 仍为 null，"
            "本次实测为 %d / %d，只记录不回填冻结配置",
            candidate_key, output_dimension, expected_parameter_count(output_dimension),
        )

    state = {
        "candidate_key": candidate_key,
        "output_dimension": output_dimension,
        "fitted_row_count": row_count,
        "quantile_landmark_count": landmark_actual,
        "quantile_policy": {
            "output_distribution": QUANTILE_OUTPUT_DISTRIBUTION,
            "subsample": QUANTILE_SUBSAMPLE,
            "noise_standard_deviation": QUANTILE_NOISE_STANDARD_DEVIATION,
            "seed": seed,
            # 逐字段派生种子是相对官方一次性抽取 n×d 噪声的显式实现偏离，
            # 必须进封印制品而不是只留在注释里。
            "noise_seed_derivation": "per_feature_seed_plus_dijk_feature_index",
            "scikit_learn_version": sklearn.__version__,
            "median_self_check_max_absolute_value": median_deviation,
            "median_self_check_tolerance": QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE,
        },
        # integer_like 只作事实记录、不参与任何分支，但必须随封印可追溯。
        "field_integer_like": {
            name: bool(entry["integer_like"]) for name, entry in receipt["fields"].items()
        },
        "numeric_feature_indices": list(numeric_indices),
        "numeric_fill_values_sha256": hashlib.sha256(
            np.asarray(fill_values, dtype=np.float64).tobytes()
        ).hexdigest(),
        "quantile_grid_sha256": hashlib.sha256(
            np.ascontiguousarray(quantile_transformer.quantiles_).tobytes()
        ).hexdigest(),
        "quantile_references_sha256": hashlib.sha256(
            np.ascontiguousarray(quantile_transformer.references_).tobytes()
        ).hexdigest(),
        # 词表以 float32 位模式记录，避免十进制往返带来的比较歧义。
        "categorical_vocabularies": {
            name: {
                "dijk_feature_index": index,
                "size": len(vocabulary),
                "out_of_vocabulary_column": len(vocabulary),
                "bit_patterns_sha256": hashlib.sha256(
                    np.asarray(vocabulary, dtype=np.float32).view(np.uint32).tobytes()
                ).hexdigest(),
            }
            for name, index, vocabulary in zip(categorical_names, categorical_indices, vocabularies, strict=True)
        } if partitioned else {},
        "boolean_fields": {
            name: {"dijk_feature_index": index, "true_value": true_value, "false_value": false_value}
            for name, index, true_value, false_value in zip(
                boolean_names, boolean_indices, boolean_true_values, boolean_false_values, strict=True
            )
        } if partitioned else {},
        "cardinality_receipt_effective_flow_mask_sha256": flow_mapping["effective_flow_mask_sha256"],
    }
    state_hash = _canonical_sha256(state)
    logger.info(
        "输入变换 %s 拟合完成：输出维=%d，参数量=%d，state_hash=%s",
        candidate_key, output_dimension, expected_parameter_count(output_dimension), state_hash,
    )
    return InputTransform(
        candidate_key=candidate_key,
        output_dimension=output_dimension,
        state_hash=state_hash,
        fitted_row_count=row_count,
        quantile_landmark_count=int(landmark_actual or landmark_count),
        numeric_feature_indices=numeric_indices,
        numeric_fill_values=tuple(fill_values),
        quantile_transformer=quantile_transformer,
        categorical_field_names=categorical_names if partitioned else (),
        categorical_feature_indices=tuple(categorical_indices),
        categorical_vocabularies=tuple(vocabularies),
        boolean_field_names=boolean_names if partitioned else (),
        boolean_feature_indices=tuple(boolean_indices),
        boolean_true_values=tuple(boolean_true_values),
        boolean_false_values=tuple(boolean_false_values),
    )


# ---------------------------------------------------------------------------
# 三层 BatchEnsemble 骨干（任务 3）
# ---------------------------------------------------------------------------

# 前向张量的轴约定：0 批、1 成员、2 时间、3 特征。
# 因果前缀聚合只沿时间轴累积，成员轴自始至终只作批维的一部分；
# 任何跨成员的求和、拼接或注意力都是机制越界，由下列常量与断言共同钉死。
BATCH_AXIS = 0
MEMBER_AXIS = 1
TIME_AXIS = 2
FEATURE_AXIS = 3

_BACKBONE_CACHE: dict[str, Any] = {}


def batch_ensemble_parameter_count(input_size: int, output_size: int, members: int) -> int:
    """冻结配方第 170 行的 ``BE(a,b,k)=a*b+k*a+k*b+k*b``。

    四项依次对应共享主权重 ``weight``、成员输入缩放 ``r``、成员输出缩放 ``s``
    与成员偏置 ``bias``，与 ``LinearBatchEnsemble`` 的参数逐项一一对应。
    """
    return input_size * output_size + members * input_size + 2 * members * output_size


def backbone_parameter_count(input_dimension: int, hidden_size: int, members: int) -> int:
    """逐层展开的可训练参数量，用于与闭式 ``expected_parameter_count`` 交叉核对。

    ``BE(d_in,d,k) + BE(d,d,k) + BE(2d,d,k) + k*Linear(d,1) + p_log``。
    """
    return (
        batch_ensemble_parameter_count(input_dimension, hidden_size, members)
        + batch_ensemble_parameter_count(hidden_size, hidden_size, members)
        + batch_ensemble_parameter_count(2 * hidden_size, hidden_size, members)
        + members * (hidden_size + 1)
        + 1
    )


def backbone_classes() -> dict[str, Any]:
    """延迟构造依赖 PyTorch 的骨干类并缓存。

    模块顶层不导入 torch，``--validate-config`` 因此可以在没有 GPU 与 PyTorch 的
    开发机上跑通；只有真正要建模型时才触发导入。
    """
    if _BACKBONE_CACHE:
        return _BACKBONE_CACHE

    import math

    import torch
    from torch import nn

    precision = _precision_module()

    def masked(tensor: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """按时间掩码清零无效位置，并保持与被乘张量同一计算类型。"""
        return tensor * mask.unsqueeze(-1).to(tensor.dtype)

    class LinearBatchEnsemble(nn.Module):
        """BatchEnsemble 线性层：一份共享主权重加三组成员参数。

        参数构成与 ``BE(a,b,k)=a*b+k*a+k*b+k*b`` 逐项对应：
        ``weight`` 为 ``a*b`` 的共享主权重，``r`` 为 ``k*a`` 的成员输入缩放，
        ``s`` 为 ``k*b`` 的成员输出缩放，``bias`` 为 ``k*b`` 的成员偏置。

        初始化按冻结配方第 147 行：第一组输入缩放用随机符号，使 32 个成员在第一次
        特征混合前就产生不同表示；其余乘性缩放初始化为 1；成员偏置按官方语义初始化，
        即先按 ``nn.Linear`` 的默认界 ``U(-1/sqrt(a), 1/sqrt(a))`` 抽一份共享偏置，
        再复制到每个成员。该语义沿用本仓库同族 TabM4 实现
        （tools/ch3_resmlp2_tabm_protocol_a_2x2.py 第 343 至 345 行）。
        """

        def __init__(
            self,
            input_size: int,
            output_size: int,
            members: int,
            random_sign_input_scaling: bool,
        ) -> None:
            super().__init__()
            self.input_size = input_size
            self.output_size = output_size
            self.members = members
            self.random_sign_input_scaling = random_sign_input_scaling
            self.weight = nn.Parameter(torch.empty(output_size, input_size))
            self.r = nn.Parameter(torch.empty(members, input_size))
            self.s = nn.Parameter(torch.ones(members, output_size))
            self.bias = nn.Parameter(torch.empty(members, output_size))
            nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
            if random_sign_input_scaling:
                signs = torch.randint(0, 2, self.r.shape, dtype=torch.int64)
                self.r.data.copy_(signs.to(self.r.dtype).mul_(2).sub_(1))
            else:
                nn.init.ones_(self.r)
            bound = 1.0 / math.sqrt(input_size)
            shared_bias = torch.empty(output_size).uniform_(-bound, bound)
            self.bias.data.copy_(shared_bias.unsqueeze(0).expand_as(self.bias))

        def parameter_count(self) -> int:
            return batch_ensemble_parameter_count(self.input_size, self.output_size, self.members)

        def forward(self, values: torch.Tensor) -> torch.Tensor:
            # values: (N, k, T, a) -> (N, k, T, b)
            if values.ndim != 4 or values.shape[MEMBER_AXIS] != self.members:
                raise RuntimeError(
                    f"BatchEnsemble 输入必须是 N×{self.members}×T×{self.input_size}，"
                    f"实际 {tuple(values.shape)}"
                )
            scaled = values * self.r.unsqueeze(0).unsqueeze(TIME_AXIS)
            projected = torch.matmul(scaled, self.weight.t())
            return (
                projected * self.s.unsqueeze(0).unsqueeze(TIME_AXIS)
                + self.bias.unsqueeze(0).unsqueeze(TIME_AXIS)
            )

    class TabM32Backbone(nn.Module):
        """三层 BatchEnsemble 骨干，含因果前缀聚合与实体级可学幂平均池化两个开关。

        第一层 ``input_dimension→512``（随机符号输入缩放为真），第二层 ``512→512``，
        第三层是因果前缀聚合感知的 ``1024→512`` 融合。三层随机失活一致、激活为 ReLU、
        不追加任何归一化层。输出头是 32 个独立的 ``Linear(512,1)``，向量化为
        ``output_weight``（k×d）与 ``output_bias``（k），初始化与 32 个独立
        ``nn.Linear(512,1)`` 的默认初始化逐项一致；另有共享标量 ``p_log``。

        ``aggregate`` 为假时上下文置零后同样拼接成 1024 维，使两条路径的参数量与
        张量形状完全一致，机制差异只来自上下文是否携带信息。
        """

        def __init__(
            self,
            input_dimension: int,
            hidden_size: int,
            members: int,
            dropout: float,
            aggregate: bool,
        ) -> None:
            super().__init__()
            self.input_dimension = input_dimension
            self.hidden_size = hidden_size
            self.members = members
            self.aggregate = aggregate
            self.input_layer = LinearBatchEnsemble(input_dimension, hidden_size, members, True)
            self.hidden_layer = LinearBatchEnsemble(hidden_size, hidden_size, members, False)
            self.fusion_layer = LinearBatchEnsemble(hidden_size * 2, hidden_size, members, False)
            self.activation = nn.ReLU()
            self.dropout = nn.Dropout(dropout)
            self.output_weight = nn.Parameter(torch.empty(members, hidden_size))
            self.output_bias = nn.Parameter(torch.empty(members))
            nn.init.kaiming_uniform_(self.output_weight, a=math.sqrt(5))
            bound = 1.0 / math.sqrt(hidden_size)
            nn.init.uniform_(self.output_bias, -bound, bound)
            self.p_log = nn.Parameter(torch.tensor(math.log(2.0)))

        @property
        def p(self) -> torch.Tensor:
            return torch.exp(self.p_log).clamp(1e-3, 1e3)

        def expand_to_members(
            self, values: torch.Tensor, valid: torch.Tensor
        ) -> tuple[torch.Tensor, torch.Tensor]:
            """把 32 个成员共享的同一批序列扩成 N×32×T×F 与 N×32×T 的视图。

            冻结配方第 148 行规定 32 个成员共享同一批对象；``expand`` 只产生视图，
            真正的物化发生在第一层的成员输入缩放处。
            """
            if values.ndim != 3 or valid.ndim != 2 or valid.shape != values.shape[:2]:
                raise RuntimeError(
                    f"共享批输入必须是 N×T×F 与 N×T，实际 {tuple(values.shape)} 与 {tuple(valid.shape)}"
                )
            return (
                values.unsqueeze(MEMBER_AXIS).expand(-1, self.members, -1, -1),
                valid.unsqueeze(MEMBER_AXIS).expand(-1, self.members, -1),
            )

        def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
            if values.ndim != 4 or values.shape[MEMBER_AXIS] != self.members:
                raise RuntimeError(
                    f"TabM32 训练输入必须是 N×{self.members}×T×F，实际 {tuple(values.shape)}"
                )
            if valid.shape != values.shape[:FEATURE_AXIS]:
                raise RuntimeError(
                    f"有效掩码必须是 N×{self.members}×T，实际 {tuple(valid.shape)}"
                )
            device_type = values.device.type
            mask = valid.to(torch.float32)
            hidden = masked(self.dropout(self.activation(self.input_layer(values))), mask)
            hidden = masked(self.dropout(self.activation(self.hidden_layer(hidden))), mask)

            if self.aggregate:
                # 因果前缀累积属精度合同的 reduction 敏感计算，放进 FP32 岛：
                # 长度 128 的前缀和在 BF16 下会累积可观舍入误差。
                with precision.fp32_island(
                    hidden, mask, device_type=device_type, torch_module=torch
                ) as (hidden32, mask32):
                    counts = torch.cumsum(mask32, TIME_AXIS).clamp(min=1.0).unsqueeze(-1)
                    context32 = torch.cumsum(hidden32, TIME_AXIS) / counts
                    context32 = context32 * mask32.unsqueeze(-1)
                context = context32.to(hidden.dtype)
            else:
                context = torch.zeros_like(hidden)

            # 机制边界一：因果前缀聚合只沿时间轴、在成员维之内独立进行。
            # 上下文张量必须与隐藏张量同形且成员维仍为 members；任何跨成员求和、
            # 拼接或注意力都会改变这两项之一，从而在此立即失败。
            if context.shape != hidden.shape or context.shape[MEMBER_AXIS] != self.members:
                raise RuntimeError(
                    "因果前缀聚合越出成员维：上下文张量必须与隐藏张量同形且成员维不变，"
                    f"实际 {tuple(context.shape)} 对 {tuple(hidden.shape)}"
                )

            fused = masked(
                self.dropout(self.activation(self.fusion_layer(torch.cat((hidden, context), dim=-1)))),
                mask,
            )
            # 32 个独立 Linear(512,1) 的向量化写法：每个成员只用自己的头权重。
            logits = torch.einsum("nkth,kh->nkt", fused, self.output_weight)
            return logits + self.output_bias.view(1, self.members, 1)

        def member_mean_probability(self, logits: torch.Tensor) -> torch.Tensor:
            """32 个 sigmoid 概率算术平均，禁止平均对数几率。

            概率归一化属精度合同的敏感计算，在 FP32 岛内完成。
            """
            if logits.ndim != 3 or logits.shape[MEMBER_AXIS] != self.members:
                raise RuntimeError(
                    f"成员概率平均的输入必须是 N×{self.members}×T，实际 {tuple(logits.shape)}"
                )
            with precision.fp32_island(
                logits, device_type=logits.device.type, torch_module=torch
            ) as (logits32,):
                probabilities = torch.sigmoid(logits32).mean(dim=MEMBER_AXIS)
            return probabilities

        def shared_batch_flow_probability(
            self, values: torch.Tensor, valid: torch.Tensor
        ) -> torch.Tensor:
            """共享批推理：``(N,T,F)`` 与 ``(N,T)`` 直接得到成员平均后的逐流概率。"""
            expanded_values, expanded_valid = self.expand_to_members(values, valid)
            return self.member_mean_probability(self.forward(expanded_values, expanded_valid))

    _BACKBONE_CACHE.update(
        {
            "LinearBatchEnsemble": LinearBatchEnsemble,
            "TabM32Backbone": TabM32Backbone,
        }
    )
    return _BACKBONE_CACHE


def learned_lp_pool(scores: Any, valid: Any, p_value: Any) -> Any:
    """实体级可学幂平均池化。

    机制边界二：``scores`` 必须是已经完成成员维归约的 ``N×T``，即先对 32 个成员概率
    做算术平均，再对唯一实体做 ELP；禁止先逐成员池化再平均。下面的维度断言使违反
    该顺序时立即失败。对数、幂与掩码归约都属精度合同的敏感计算，全部在 FP32 岛内完成。
    """
    import torch

    if scores.ndim != 2 or valid.ndim != 2 or scores.shape != valid.shape:
        raise RuntimeError(
            "ELP 池化输入必须是已完成成员归约的 N×T 概率与同形掩码，"
            f"实际 {tuple(scores.shape)} 与 {tuple(valid.shape)}；禁止先逐成员池化再平均"
        )
    precision = _precision_module()
    with precision.fp32_island(
        scores, valid, p_value, device_type=scores.device.type, torch_module=torch
    ) as (scores32, valid32, exponent):
        log_scores = torch.log(scores32.clamp(min=1e-7))
        count = valid32.sum(1).clamp(min=1.0)
        summed = torch.logsumexp((exponent * log_scores).masked_fill(valid32 < 0.5, -1e30), 1)
        pooled = torch.exp((summed - torch.log(count)) / exponent)
    return pooled


def build_model(config: dict[str, Any], cell: str, input_key: str, input_dimension: int) -> Any:
    """按格构造骨干并做参数量三方比对。

    三方为：闭式 ``expected_parameter_count(input_dimension)``、冻结配置中该输入候选
    登记的 ``parameter_count``、以及实际 ``sum(p.numel() ...)``。候选二的冻结值当前
    为 null（待收据裁定），此时只比对闭式与实际两方，并把实测值写进日志，不自行回填。
    """
    import torch

    if cell not in CELLS:
        raise ValueError(f"未知实验格：{cell}")
    candidate = config["candidate"]
    classes = backbone_classes()
    model = classes["TabM32Backbone"](
        input_dimension=input_dimension,
        hidden_size=candidate["hidden_size"],
        members=candidate["ensemble_members"],
        dropout=config["training"]["dropout"],
        aggregate=CELLS[cell]["causal_prefix_aggregation"],
    )
    closed_form = expected_parameter_count(input_dimension)
    layer_wise = backbone_parameter_count(
        input_dimension, candidate["hidden_size"], candidate["ensemble_members"]
    )
    actual = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    if closed_form != layer_wise:
        raise RuntimeError(
            f"参数量闭式 {closed_form} 与逐层展开 {layer_wise} 不符，冻结配方的参数式已被破坏"
        )
    if actual != closed_form:
        raise RuntimeError(f"实际可训练参数量 {actual} 与闭式 {closed_form} 不符")
    frozen_candidate = next(
        entry for entry in INPUT_CANDIDATES if entry["key"] == input_key
    )
    frozen_parameters = frozen_candidate["parameter_count"]
    if frozen_parameters is not None and actual != frozen_parameters:
        raise RuntimeError(
            f"实际可训练参数量 {actual} 与冻结配置登记的 {frozen_parameters} 不符"
        )
    if frozen_parameters is None:
        logger.warning(
            "输入候选 %s 的冻结 parameter_count 仍为 null，本次实测为 %d，只记录不回填",
            input_key, actual,
        )
    # 参数与优化器状态必须保持 FP32：这里先核参数，优化器状态在第一次 step 之后再核。
    for name, parameter in model.named_parameters():
        if parameter.is_floating_point() and parameter.dtype != torch.float32:
            raise RuntimeError(f"模型参数 {name} 不是 FP32，与精度合同不符")
    logger.info(
        "已构造 %s 骨干：输入候选=%s，输入维=%d，宽度=%d，成员=%d，因果前缀聚合=%s，"
        "可训练参数量=%d（闭式与逐层展开一致）",
        cell, input_key, input_dimension, candidate["hidden_size"],
        candidate["ensemble_members"], CELLS[cell]["causal_prefix_aggregation"], actual,
    )
    return model


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
