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

# 输入接口候选（阶段一 select-input 的备选清单）。
#
# Codex 2026-08-21 14:20 CST 裁定（覆盖此前 WAITING_FOR_CODEX_CARDINALITY_RECEIPT
# 待定态）：否决 SrcPort/DstPort 全独热候选（缺少原始语义、产生 37.7× 容量混杂与
# 显存代价）。候选二改为：两端口继续数值，仅 Protocol、L3/L4 Protocol 与二元粗
# 拓扑字段（Int/Ext Dst IP、External_src、External_dst）采用训练区词表独热，其余
# 数值与候选一相同。候选二的 input_dimension 与 parameter_count 保持 None：
# 由运行时从字段基数收据实测推导（见 project_input_dimension/fit_input_transform
# 对 TYPE_PARTITIONED_* 三个字段角色常量的消费），不在此硬编码——这样代码对实测
# 基数如有出入会明确报错，而不是掩盖与预算不符的偏差。
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
        "display_name": "TabM32-协议与粗拓扑字段独热输入",
        "key": "tabm32-input-type-partitioned",
        "numeric_transform": "training_region_quantile_normalization",
        "categorical_treatment": (
            "srcport_dstport_remain_numeric_quantile_normalized；"
            "protocol_and_l34_training_region_one_hot_with_out_of_vocabulary_bucket；"
            "coarse_topology_binary_fields_zero_one_passthrough"
        ),
        "boolean_treatment": "zero_one_passthrough",
        "input_dimension": None,
        "parameter_count": None,
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

# resource_contract 中除 minimum_free_gpu_memory_mib 外的固定期望值。该字段本身
# 由 Codex 于 2026-08-21 14:20 CST 裁定为 20480（见看板 N-12 裁决第 4 条），
# 在 validate_config 中单独按等值校验。
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

# Codex 2026-08-21 14:20 CST 裁定的 GPU 空闲显存准入阈值（MiB）。
GPU_FREE_MEMORY_MINIMUM_MIB = 20480

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


# 精度配置登记的计算类型字符串到 torch.dtype 的映射；键集合与
# PRECISION_DTYPE_BYTES、neural_precision_runtime.autocast_context 内部映射一致。
_COMPUTE_DTYPE_NAMES: tuple[str, ...] = ("bfloat16", "float16", "float32")


def compute_torch_dtype(profile: dict[str, Any], torch_module: Any) -> Any:
    """把精度合同登记的 ``compute_dtype`` 字符串映射为 ``torch.dtype``。

    Codex 2026-08-21 14:20 CST 裁定：BatchEnsemble 入口须把激活显式转换为计算
    类型，避免 ``values * r`` 保留 FP32 后在矩阵乘前再复制一份 BF16
    （见 ``LinearBatchEnsemble.forward``）。该计算类型必须从本函数按
    profile 解析，不得在骨干代码中硬编码 ``torch.bfloat16``，使 FP32 例外
    profile（``compute_dtype=="float32"``）也能复用同一条代码路径。
    """
    dtype_name = profile["compute_dtype"]
    if dtype_name not in _COMPUTE_DTYPE_NAMES:
        raise ValueError(f"精度配置登记了未核验的计算类型：{dtype_name}")
    return getattr(torch_module, dtype_name)


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
    if resource_contract.get("minimum_free_gpu_memory_mib") != GPU_FREE_MEMORY_MINIMUM_MIB:
        raise ValueError(
            f"resource_contract.minimum_free_gpu_memory_mib 必须等于 Codex 裁定值 "
            f"{GPU_FREE_MEMORY_MINIMUM_MIB}"
        )
    if "pending_reason" in resource_contract:
        raise ValueError(
            "resource_contract.pending_reason 必须删除：GPU 显存准入阈值已由 Codex 裁定，"
            "配置中不得再保留待裁字段"
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

# 组装式变换器的实现漂移绊线，不是科学阈值。探针是变换器自身的地标：在 quantiles_
# 严格递增的位置上，transform(quantiles_[k, j]) 与 Phi^-1(references_[k]) 是同一个数的
# 两条计算路径，解析偏差为 0，实测在四列合成算例的 2905 个严格递增地标上最大绝对偏差
# 亦为 0.000e+00。下列容差只为容纳 float32 往返舍入，任何实质语义改变都会远超它。
QUANTILE_LANDMARK_SELF_CHECK_TOLERANCE = 1e-6


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


# 候选二（tabm32-input-type-partitioned）的字段角色划分，与 field_groups
# （用于消费字段基数收据的原始 7 字段清单与顺序，见 load_cardinality_receipt）
# 是两个不同用途的分组：field_groups 决定收据里有哪些字段、以什么顺序出现；
# 下列三个常量决定候选二对这些字段各自采用哪种数值/独热/直通处理。
#
# Codex 2026-08-21 14:20 CST 裁定：两端口继续数值（不独热，理由是缺少原始语义、
# 全独热会产生 37.7× 容量混杂与显存代价）；Protocol、L3/L4 Protocol 采用训练区
# 词表独热（真正多类别字段，含越界桶）；Int/Ext Dst IP、External_src、
# External_dst 是二元粗拓扑字段，按论文 §D.2 对二值特征的 {0,1} 直通处理
# ——与 External_src/External_dst 原有的 zero_one_passthrough 机制完全一致，
# 只是把 Int/Ext Dst IP 也纳入同一处理，不新增独立代码路径。
# 实测基数（field-cardinality-receipt-v1）：Protocol=7、L3/L4 Protocol=5、
# Int/Ext Dst IP=2、External_src=2、External_dst=2，七个字段 missing_fraction
# 全为 0。按此口径预算 d_in = 78(数值) + (7+1)+(5+1)(两个独热字段含越界桶)
# + 3(三个二元直通字段) = 95，参数量 = 544*95+950305 = 1,001,985；
# 该预算以运行时对真实收据的实测为准，此处不写死。
TYPE_PARTITIONED_NUMERIC_TREATED_FIELDS: tuple[str, ...] = ("SrcPort", "DstPort")
TYPE_PARTITIONED_ONE_HOT_FIELDS: tuple[str, ...] = ("Protocol", "L3/L4 Protocol")
TYPE_PARTITIONED_BOOLEAN_FIELDS: tuple[str, ...] = ("Int/Ext Dst IP", "External_src", "External_dst")


def project_input_dimension(candidate_key: str, receipt: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """拟合前用收据的 unique_count 预算输出维、参数量与稠密输入字节。

    先预算再扫描，避免全量拟合之后才发现输出维不可行。
    """
    groups = config["field_groups"]
    numeric_count = groups["numeric_count"]
    if candidate_key == "tabm32-input-all-numeric":
        output_dimension = groups["total_count"]
        vocabulary_widths: dict[str, int] = {}
    elif candidate_key == "tabm32-input-type-partitioned":
        one_hot_fields = list(TYPE_PARTITIONED_ONE_HOT_FIELDS)
        boolean_fields = list(TYPE_PARTITIONED_BOOLEAN_FIELDS)
        numeric_treated_fields = list(TYPE_PARTITIONED_NUMERIC_TREATED_FIELDS)
        # 每个独热字段占 词表长度 + 1 列，加一为固定越界桶；二元直通字段不设
        # 越界桶（论文 §D.2 对二值特征是 {0,1} 直通，训练区未见取值静默记 0）。
        vocabulary_widths = {
            name: receipt["fields"][name]["unique_count"] + 1 for name in one_hot_fields
        }
        output_dimension = (
            (numeric_count + len(numeric_treated_fields))
            + sum(vocabulary_widths.values())
            + len(boolean_fields)
        )
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
    # GPU 空闲显存准入阈值已由 Codex 裁定为 GPU_FREE_MEMORY_MINIMUM_MIB；实际准入判定
    # 由启动器门禁 9（gate_gpu_free_memory）在真实设备上比对，本函数只给出预算事实。
    logger.info(
        "输出维可行性预算事实（不构成准入判定，准入判定见启动器门禁 9）：GPU 空闲显存准入阈值=%d MiB",
        GPU_FREE_MEMORY_MINIMUM_MIB,
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
    from scipy.stats import norm as scipy_norm
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
    partitioned = candidate_key == "tabm32-input-type-partitioned"
    if partitioned:
        # 候选二字段角色：SrcPort/DstPort 继续数值（并入分位数规范化），
        # Protocol/L3-L4 Protocol 独热（真正多类别），Int/Ext Dst IP/
        # External_src/External_dst 二元直通——三者互斥地划分收据里的 7 个字段。
        categorical_names = tuple(TYPE_PARTITIONED_ONE_HOT_FIELDS)
        boolean_names = tuple(TYPE_PARTITIONED_BOOLEAN_FIELDS)
        reserved = {field_indices[name] for name in (*categorical_names, *boolean_names)}
        numeric_indices = tuple(i for i in range(DIJK_FEATURE_COUNT) if i not in reserved)
        expected_numeric_count = (
            config["field_groups"]["numeric_count"] + len(TYPE_PARTITIONED_NUMERIC_TREATED_FIELDS)
        )
        if len(numeric_indices) != expected_numeric_count:
            raise RuntimeError(
                f"候选二数值字段数 {len(numeric_indices)} 与预算 {expected_numeric_count} 不符"
            )
    else:
        # 候选一把 83 个字段全部声明为数值，统一施加同一分位数规范化。
        categorical_names = ()
        boolean_names = ()
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
    # 语义就会静默产出错误数值。自检用变换器自身的地标作探针：在 quantiles_ 严格递增的
    # 位置上，transform(quantiles_[k, j]) 必须精确等于 Phi^-1(references_[k])。该恒等式
    # 直接检验被写入的私有属性语义，且与字段的并列结构无关。
    #
    # 早期版本改用「训练区中位数应映射到约 0」作探针，在本数据上必然误报：中位数取自
    # 未加噪的干净列（NaN 填补需要它），而 quantiles_ 拟合在加噪列上。当某字段过半数行
    # 取同一值时，干净中位数落在加噪并列平台的正中，被映到平台的中点分位而非 0.5。
    # 合成算例复现：平台占 60% 时映射值 +0.522099，与真实运行报错的 0.521619 同量级；
    # 平台占 40%（中位数不在平台内）与几乎无并列的两个对照均映到约 0，证明变换本身正确。
    # 本数据 83 个字段中有 5 个最高频值占比超过 50%（如 External_src 占 0.7387、仅 2 个
    # 唯一值），故旧探针对本数据结构性不适用，属探针缺陷而非变换缺陷。
    landmark_grid = quantile_transformer.quantiles_
    landmark_response = quantile_transformer.transform(landmark_grid)
    bounds_threshold = float(np.finfo(np.float32).eps)
    landmark_expected = scipy_norm.ppf(
        np.clip(quantile_transformer.references_, bounds_threshold, 1.0 - bounds_threshold)
    )
    landmark_deviation = 0.0
    landmark_checked = 0
    for column_position in range(landmark_grid.shape[1]):
        column_grid = landmark_grid[:, column_position]
        ascending = np.diff(column_grid) > 0
        # 只检验严格递增的内部地标：并列位的正反向插值本就取平台中点，两端受
        # scikit-learn 的边界裁剪影响，二者都不构成组装语义的判据。
        strictly_increasing = np.r_[False, ascending] & np.r_[ascending, False]
        strictly_increasing[0] = False
        strictly_increasing[-1] = False
        selected = np.flatnonzero(strictly_increasing)
        if selected.size == 0:
            continue
        landmark_checked += int(selected.size)
        landmark_deviation = max(
            landmark_deviation,
            float(np.max(np.abs(
                landmark_response[selected, column_position] - landmark_expected[selected]
            ))),
        )
    if landmark_checked == 0:
        raise RuntimeError(
            "组装式分位数变换器自检无可检地标：全部字段的分位数网格均无严格递增位置，"
            "无法确认私有拟合属性语义，拒绝继续拟合"
        )
    if landmark_deviation > QUANTILE_LANDMARK_SELF_CHECK_TOLERANCE:
        raise RuntimeError(
            f"组装式分位数变换器自检失败：{landmark_checked} 个严格递增地标中，"
            f"transform 输出与 Phi^-1(references_) 的最大绝对偏差为 {landmark_deviation:.6g}，"
            f"超过绊线 {QUANTILE_LANDMARK_SELF_CHECK_TOLERANCE}；"
            f"scikit-learn {sklearn.__version__} 的私有拟合属性语义可能已改变，拒绝继续拟合"
        )
    logger.info(
        "组装式变换器自检通过：%d 个严格递增地标的最大绝对偏差=%.6g（绊线 %.3g），scikit-learn=%s",
        landmark_checked, landmark_deviation, QUANTILE_LANDMARK_SELF_CHECK_TOLERANCE,
        sklearn.__version__,
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
            "landmark_self_check_strictly_increasing_count": landmark_checked,
            "landmark_self_check_max_absolute_deviation": landmark_deviation,
            "landmark_self_check_tolerance": QUANTILE_LANDMARK_SELF_CHECK_TOLERANCE,
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
            compute_dtype: Any,
        ) -> None:
            super().__init__()
            self.input_size = input_size
            self.output_size = output_size
            self.members = members
            self.random_sign_input_scaling = random_sign_input_scaling
            # 计算类型只用于 forward 内的显式转型，不改变参数本身的存储 dtype：
            # weight/r/s/bias 仍按精度合同保持 FP32（见下方 nn.Parameter 构造）。
            self.compute_dtype = compute_dtype
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
            #
            # Codex 2026-08-21 14:20 CST 裁定：在 BatchEnsemble 入口把激活显式转换
            # 为计算类型，避免 ``values * r`` 先在 FP32 物化出展开张量、autocast
            # 又在 matmul 前另生一份计算类型副本（两份同时存在，实测峰值 1.50×）。
            # 这里连同 r/weight/s/bias 一并显式转型：mul/matmul 均不在 PyTorch AMP
            # 的隐式降精度列表之外，只显式转型激活而不转型参数会因 FP32×BF16 的
            # 类型提升规则被自动升回 FP32，起不到消除副本的作用；r/weight/s/bias
            # 参数本身（nn.Parameter 存储）与优化器状态仍保持 FP32，这里的 ``.to``
            # 只产生前向用的临时视图/副本，反向梯度经 ``.to`` 正常回传到 FP32 参数。
            if values.ndim != 4 or values.shape[MEMBER_AXIS] != self.members:
                raise RuntimeError(
                    f"BatchEnsemble 输入必须是 N×{self.members}×T×{self.input_size}，"
                    f"实际 {tuple(values.shape)}"
                )
            compute_values = values.to(self.compute_dtype)
            compute_r = self.r.to(self.compute_dtype)
            scaled = compute_values * compute_r.unsqueeze(0).unsqueeze(TIME_AXIS)
            projected = torch.matmul(scaled, self.weight.to(self.compute_dtype).t())
            return (
                projected * self.s.to(self.compute_dtype).unsqueeze(0).unsqueeze(TIME_AXIS)
                + self.bias.to(self.compute_dtype).unsqueeze(0).unsqueeze(TIME_AXIS)
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
            compute_dtype: Any,
        ) -> None:
            super().__init__()
            self.input_dimension = input_dimension
            self.hidden_size = hidden_size
            self.members = members
            self.aggregate = aggregate
            self.compute_dtype = compute_dtype
            self.input_layer = LinearBatchEnsemble(input_dimension, hidden_size, members, True, compute_dtype)
            self.hidden_layer = LinearBatchEnsemble(hidden_size, hidden_size, members, False, compute_dtype)
            self.fusion_layer = LinearBatchEnsemble(hidden_size * 2, hidden_size, members, False, compute_dtype)
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


def build_model(
    config: dict[str, Any], cell: str, input_key: str, input_dimension: int, profile: dict[str, Any]
) -> Any:
    """按格构造骨干并做参数量三方比对。

    三方为：闭式 ``expected_parameter_count(input_dimension)``、冻结配置中该输入候选
    登记的 ``parameter_count``、以及实际 ``sum(p.numel() ...)``。候选二的冻结值当前
    为 null（待收据裁定），此时只比对闭式与实际两方，并把实测值写进日志，不自行回填。

    ``profile`` 提供 BatchEnsemble 入口显式转型所需的计算类型（见
    ``LinearBatchEnsemble.forward`` 与 ``compute_torch_dtype``），从精度合同解析，
    不在本函数硬编码。
    """
    import torch

    if cell not in CELLS:
        raise ValueError(f"未知实验格：{cell}")
    candidate = config["candidate"]
    classes = backbone_classes()
    compute_dtype = compute_torch_dtype(profile, torch)
    model = classes["TabM32Backbone"](
        input_dimension=input_dimension,
        hidden_size=candidate["hidden_size"],
        members=candidate["ensemble_members"],
        dropout=config["training"]["dropout"],
        aggregate=CELLS[cell]["causal_prefix_aggregation"],
        compute_dtype=compute_dtype,
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
# 训练循环、梯度累积与协议 A 检查点选择（任务 4）
# ---------------------------------------------------------------------------


def _atomic_json(path: Path, value: Any) -> None:
    """先写同目录临时文件再原子替换，避免半写文件被当作完成制品。"""
    import os

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def _atomic_torch(path: Path, value: Any) -> None:
    """检查点的原子写；只应在完整 ``optimizer.step()`` 边界调用。"""
    import os

    import torch

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    torch.save(value, temporary)
    os.replace(temporary, path)


def _sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _process_peak_rss_mib() -> float:
    """进程峰值常驻内存；Linux 的 ru_maxrss 单位是 KiB，macOS 是字节。"""
    import resource

    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak / 1024.0 if sys.platform != "darwin" else peak / (1024.0 * 1024.0)


def external_process_gpu_memory_mib(torch_module: Any, device: Any) -> float:
    """同卡外部进程占用显存的估计值，用于判断测量是否被并发运行污染。

    以 ``torch.cuda.mem_get_info()`` 的 ``(free, total)`` 为准，减去本进程缓存分配器
    已保留的字节。本进程的 CUDA 上下文开销不计入 ``memory_reserved``，因此该估计会
    略微高估外部占用；它只作污染判据，不作准入阈值。这里使用与仓库既有工具一致的
    无参调用形式（资源合同 ``maximum_parallel_jobs`` 为 1，单卡）。
    """
    free_bytes, total_bytes = torch_module.cuda.mem_get_info()
    reserved = int(torch_module.cuda.memory_reserved(device))
    return max(int(total_bytes) - int(free_bytes) - reserved, 0) / 2**20


def gpu_memory_snapshot(torch_module: Any, device: Any) -> dict[str, float]:
    """四个本进程显存量加同卡外部进程占用，一律换算为 MiB。"""
    if device.type != "cuda":
        raise RuntimeError("显存快照只在 CUDA 设备上有意义")
    return {
        "memory_allocated_mib": int(torch_module.cuda.memory_allocated(device)) / 2**20,
        "memory_reserved_mib": int(torch_module.cuda.memory_reserved(device)) / 2**20,
        "max_memory_allocated_mib": int(torch_module.cuda.max_memory_allocated(device)) / 2**20,
        "max_memory_reserved_mib": int(torch_module.cuda.max_memory_reserved(device)) / 2**20,
        "external_process_gpu_mib": external_process_gpu_memory_mib(torch_module, device),
    }


def load_source_arrays(cache_root: str) -> dict[str, Any]:
    """加载协议 A 源年冻结数组并机械断言形状身份。"""
    import numpy as np

    root = Path(cache_root)
    arrays: dict[str, Any] = {}
    for name in SOURCE_ARRAYS:
        path = root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少冻结缓存：{path}")
        arrays[name] = np.load(path, allow_pickle=False)
    if arrays["X23"].shape != (LSPR23_FLOW_COUNT, DIJK_FEATURE_COUNT):
        raise RuntimeError(f"X23 形状不符：{arrays['X23'].shape}")
    if arrays["I23"].shape != (LSPR23_SEQUENCE_COUNT, PROTOCOL_A_SEQUENCE_LENGTH):
        raise RuntimeError(f"I23 形状不符：{arrays['I23'].shape}")
    if arrays["M23"].shape != arrays["I23"].shape:
        raise RuntimeError(f"M23 形状与 I23 不符：{arrays['M23'].shape}")
    if arrays["y23"].shape != (LSPR23_FLOW_COUNT,):
        raise RuntimeError(f"y23 形状不符：{arrays['y23'].shape}")
    for name in ("E23", "T23"):
        if arrays[name].shape != (LSPR23_SEQUENCE_COUNT,):
            raise RuntimeError(f"{name} 形状不符：{arrays[name].shape}")
    resident = {name: int(array.nbytes) for name, array in arrays.items()}
    logger.info(
        "源年数组已载入主机：总常驻 %.2f GiB，逐数组字节 %s",
        sum(resident.values()) / 2**30, resident,
    )
    return arrays


def source_split(arrays: dict[str, Any], config: dict[str, Any]) -> tuple[Any, Any, dict[str, int]]:
    """协议 A 源年切分：按实体随机留出验证集并切除时间尾部，逐字复用既有语义。"""
    import numpy as np

    training = config["training"]
    seed = training["seed"]
    entity = arrays["E23"]
    timestamp = arrays["T23"]
    unique_entity = np.unique(entity)
    permutation = np.random.RandomState(seed).permutation(len(unique_entity))
    count = max(1, int(len(unique_entity) * training["validation_fraction"]))
    validation_entities = set(unique_entity[permutation[:count]].tolist())
    entity_mask = np.fromiter((value in validation_entities for value in entity), bool, len(entity))
    time_cut = np.quantile(timestamp, 1.0 - training["time_tail_fraction"])
    time_mask = timestamp >= time_cut
    train_rows = np.flatnonzero(~(entity_mask | time_mask))
    validation_rows = np.flatnonzero(entity_mask & ~time_mask)
    statistics = {
        "entity_count": int(len(unique_entity)),
        "train_sequences": int(len(train_rows)),
        "validation_sequences": int(len(validation_rows)),
        "train_validation_row_intersection": int(np.intersect1d(train_rows, validation_rows).size),
    }
    if statistics != PROTOCOL_A_SPLIT_STATISTICS:
        raise RuntimeError(f"协议 A 源年切分统计不符：{statistics}")

    # 梯度累积按真实有效流归一化，任一微批的有效流数必须为正；这里提前把
    # 「存在整条全掩码序列」这一数据合同违例暴露成明确错误，而不是留到累积器内部。
    length = training["sequence_length"]
    for name, rows in (("训练", train_rows), ("验证", validation_rows)):
        per_row_valid = (arrays["M23"][rows][:, :length] > 0.5).sum(axis=1)
        if int(per_row_valid.min()) <= 0:
            raise RuntimeError(f"{name}集中存在有效流数为 0 的序列，违反逐流归一化前提")
    logger.info("协议 A 源年切分统计已核验：%s", statistics)
    return train_rows, validation_rows, statistics


class ProtocolASourceView:
    """协议 A 源年数据的主机侧视图，按已冻结的输入变换逐微批供给特征。

    两个输入候选共用同一条数据通路「主机取原值 → 冻结变换 → 逐微批上卡」。
    不做整表物化的理由是可核对的算术：候选二变换后的整表为
    ``16,353,511 × 67,195 × 4`` 字节约 ``4.0 TiB``，任何主机或设备都放不下；
    若只给候选一开整表模式，两个候选的数据通路就不再可比。
    """

    def __init__(self, arrays: dict[str, Any], transform: InputTransform) -> None:
        self.matrix = arrays["X23"]
        self.labels = arrays["y23"]
        self.indices = arrays["I23"]
        self.mask = arrays["M23"]
        self.transform = transform
        self._sequence_positive_weight: float | None = None

    @property
    def flow_positive_rate(self) -> float:
        return float(self.labels.mean())

    @property
    def sequence_positive_weight(self) -> float:
        """序列级正类权重，与既有协议 A 工具同口径，在全部序列上统计一次。"""
        if self._sequence_positive_weight is None:
            sequence_labels = (
                self.labels[self.indices.reshape(-1)].reshape(self.indices.shape) * self.mask
            ).max(1) > 0
            positive_rate = float(sequence_labels.mean())
            self._sequence_positive_weight = (1.0 - positive_rate) / max(positive_rate, 1e-8)
        return self._sequence_positive_weight

    def gather_sequences(self, rows: Any, length: int) -> tuple[Any, Any, Any]:
        """取出若干序列的流索引、有效掩码与逐流标签，形状均为 ``(len(rows), length)``。"""
        import numpy as np

        indices = np.ascontiguousarray(self.indices[rows][:, :length])
        valid = np.ascontiguousarray(self.mask[rows][:, :length] > 0.5)
        labels = np.ascontiguousarray(self.labels[indices].astype(np.float32, copy=False))
        return indices, valid, labels

    def features(self, indices: Any) -> Any:
        """把 ``(n, T)`` 流索引展成 ``(n, T, output_dimension)`` 的 float32 特征。

        无效位置的索引仍会被变换，其贡献随后由掩码清零；保持矩形形状换取批处理效率。
        """
        import numpy as np

        flat = np.asarray(indices).reshape(-1)
        raw = np.asarray(self.matrix[flat], dtype=np.float32)
        values = self.transform.apply(raw)
        return np.ascontiguousarray(
            values.reshape(indices.shape[0], indices.shape[1], self.transform.output_dimension)
        )


def sample_distinct_positions(size: int, count: int, generator: Any) -> Any:
    """在 ``[0, size)`` 内抽 ``count`` 个互不相同的位置，供有效批取不同序列。"""
    import torch

    if count > size:
        raise ValueError(f"要求 {count} 条不同序列，但可选池只有 {size} 条")
    positions: list[int] = []
    seen: set[int] = set()
    while len(positions) < count:
        candidates = torch.randint(
            0, size, ((count - len(positions)) * 2,), generator=generator
        ).tolist()
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                positions.append(candidate)
                if len(positions) == count:
                    break
    return torch.tensor(positions, dtype=torch.int64)


def make_optimizer(config: dict[str, Any], model: Any, optimizer_key: str) -> tuple[Any, dict[str, Any]]:
    """按优化器候选建 AdamW；权重衰减只施加于三层共享主权重与 32 个输出头权重。

    成员输入缩放、成员输出缩放、成员偏置、输出头偏置与共享标量 ``p_log`` 不衰减，
    与本仓库同族 TabM4 实现的分组一致。协议 A 无学习率调度，此处不建 scheduler。
    """
    import torch

    candidate = next(
        (entry for entry in OPTIMIZER_CANDIDATES if entry["key"] == optimizer_key), None
    )
    if candidate is None:
        raise ValueError(f"未知优化器候选：{optimizer_key}")
    decay_names = {
        "input_layer.weight",
        "hidden_layer.weight",
        "fusion_layer.weight",
        "output_weight",
    }
    decay = [parameter for name, parameter in model.named_parameters() if name in decay_names]
    no_decay = [parameter for name, parameter in model.named_parameters() if name not in decay_names]
    if len(decay) != len(decay_names):
        raise RuntimeError(
            f"权重衰减分组只匹配到 {len(decay)} 个参数，期望 {len(decay_names)} 个共享主权重"
        )
    optimizer = torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": candidate["weight_decay"]},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=candidate["learning_rate"],
    )
    logger.info(
        "优化器候选 %s：学习率=%s，权重衰减=%s，衰减组参数 %d 个、不衰减组 %d 个，无学习率调度",
        candidate["display_name"], candidate["learning_rate"], candidate["weight_decay"],
        len(decay), len(no_decay),
    )
    return optimizer, candidate


def evaluate_validation_flow_ap(
    config: dict[str, Any],
    model: Any,
    view: ProtocolASourceView,
    rows: Any,
    device: Any,
    profile: dict[str, Any],
) -> tuple[float, int]:
    """在 LSPR23 实体不相交验证集上计算逐流平均精度。

    推理批取有效批的序列数：同一批对象数下 ``no_grad`` 保留的显存严格低于训练步，
    因此不需要另立一个未经依据的推理批常数。
    """
    import numpy as np
    import torch
    from sklearn.metrics import average_precision_score

    precision = _precision_module()
    length = config["training"]["sequence_length"]
    batch_sequences = config["training"]["effective_batch_size"]
    predictions: list[Any] = []
    labels: list[Any] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(rows), batch_sequences):
            chunk = rows[start : start + batch_sequences]
            indices, valid, flow_labels = view.gather_sequences(chunk, length)
            values_t = torch.from_numpy(view.features(indices)).to(device)
            valid_t = torch.from_numpy(valid).to(device)
            with precision.autocast_context(profile, device.type, torch):
                probabilities = model.shared_batch_flow_probability(values_t, valid_t)
            flat_mask = valid.reshape(-1)
            predictions.append(probabilities.reshape(-1).float().cpu().numpy()[flat_mask])
            labels.append(flow_labels.reshape(-1)[flat_mask])
    model.train()
    scores = np.concatenate(predictions)
    targets = np.concatenate(labels)
    return float(average_precision_score(targets, scores)), int(len(scores))


def _move_optimizer_state(optimizer: Any, device: Any) -> None:
    """把 ``optimizer.load_state_dict`` 恢复后仍留在 CPU 的张量状态搬到目标设备。

    与既有同族工具 ``tools/ch3_resmlp2_tabm_protocol_a_2x2.py`` 的
    ``move_optimizer_state`` 同写法，供三层断点恢复的在途层调用。
    """
    import torch

    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                state[key] = value.to(device)


def train_cell(
    config: dict[str, Any],
    cell: str,
    input_key: str,
    optimizer_key: str,
    *,
    output_root: Path,
    identity: dict[str, Any],
    view: ProtocolASourceView,
    train_rows: Any,
    validation_rows: Any,
    device: Any,
    resume: bool = False,
    precision_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """训练一格并按协议 A 选择检查点，支持三层同身份断点恢复。

    梯度累积、精度与资源收据一律复用 ``tools/neural_precision_runtime.py``：
    有效批起点一次 ``zero_grad(set_to_none=True)``，每个微批把 FP32 岛内求和得到的
    标量损失交给 ``EffectiveBatchAccumulator.backward``（内部统一除以本步的全部有效流数），
    全部微批反向完成后只裁剪一次并只更新一次。

    选择规则：跑满 ``epochs`` 轮、每轮 ``steps_per_epoch`` 步，不早停、无学习率调度；
    每轮结束在实体不相交验证集上算逐流平均精度，用严格大于更新最优，因此并列保留最早轮次。

    三层断点恢复（任务 5）：

    - 完成层：``checkpoints/selected-{cell}.pt`` 与 ``receipts/selection-{cell}.json``
      同时存在时，只有传了 ``--resume`` 且收据 ``identity`` 等于本次调用的 ``identity``、
      且收据记录的检查点 ``sha256`` 等于实测哈希，才直接复用并跳过训练；否则拒绝。
    - 未传 ``--resume`` 时若任一历史制品（完成检查点、完成收据、在途检查点）已存在，
      直接拒绝，避免静默覆盖。
    - 在途层：每个 epoch 完整跑满（即 ``optimizer.step()`` 的完整边界）后原子写
      ``inflight/{cell}.pt``；恢复时先核验精度、微批量、累积步数与身份一致，
      再从 ``epoch+1`` 继续。半个有效批中断时该 epoch 从未落盘，恢复会整轮重放，
      不会出现"恢复部分累计梯度后跳过样本"的情形。
    """
    import random
    import time

    import numpy as np
    import torch

    checkpoint_path = output_root / "checkpoints" / f"selected-{cell}.pt"
    receipt_path = output_root / "receipts" / f"selection-{cell}.json"
    inflight_path = output_root / "inflight" / f"{cell}.pt"

    if checkpoint_path.is_file() and receipt_path.is_file():
        receipt = load_json(receipt_path)
        checkpoint_sha = receipt.get("selection", {}).get("checkpoint", {}).get("sha256")
        if not resume or receipt.get("identity") != identity or checkpoint_sha != _sha256_file(checkpoint_path):
            raise RuntimeError(
                f"{cell}（输入候选={input_key}，优化器候选={optimizer_key}）已有完成检查点，"
                "但未传 --resume、身份不符或摘要不符，拒绝覆盖或部分拼接"
            )
        logger.info("%s 完成层复用：身份与检查点摘要均匹配，跳过训练：%s", cell, receipt_path)
        return receipt["selection"]
    if not resume and (checkpoint_path.exists() or receipt_path.exists() or inflight_path.exists()):
        raise RuntimeError(f"全新运行（未传 --resume）已存在 {cell} 的历史制品，拒绝覆盖：{output_root}")

    precision = _precision_module()
    training = config["training"]
    candidate = config["candidate"]
    members = candidate["ensemble_members"]
    micro_batch = candidate["micro_batch_sequences"]
    accumulation_steps = candidate["gradient_accumulation_steps"]
    effective_batch = training["effective_batch_size"]
    length = training["sequence_length"]
    uses_lp = CELLS[cell]["learned_lp_pooling"]
    device_type = device.type

    # 精度合同：核验设备能力与配置一致，再核验批量因子自洽。
    contract, profile, profile_id = resolve_precision_profile(device_type, torch, precision_contract)
    plan = precision.validate_microbatch_plan(
        effective_batch, micro_batch, accumulation_steps, NORMALIZATION_UNIT, is_tail_batch=False
    )
    scaler = precision.create_grad_scaler(profile, torch)
    if scaler is not None:
        raise RuntimeError("BF16 默认精度配置不得创建 GradScaler，实际创建了缩放器")
    bounds = tensor_upper_bounds(config, view.transform.output_dimension, profile)
    logger.info(
        "%s 张量上界（按展开维度乘积，非参数量）：主机稠密输入=%.2f MiB，"
        "设备展开输入=%.2f MiB（%s）/%.2f MiB（FP32 保守口径），隐藏张量=%.2f MiB，因果前缀拼接=%.2f MiB",
        cell,
        bounds["micro_batch_host_dense_input_bytes"] / 2**20,
        bounds["micro_batch_device_expanded_input_bytes"] / 2**20,
        profile["compute_dtype"],
        bounds["micro_batch_device_expanded_input_fp32_bytes"] / 2**20,
        bounds["hidden_tensor_bytes"] / 2**20,
        bounds["causal_prefix_concat_bytes"] / 2**20,
    )

    random.seed(training["seed"])
    np.random.seed(training["seed"])
    torch.manual_seed(training["seed"])
    if device_type == "cuda":
        torch.cuda.manual_seed_all(training["seed"])

    model = build_model(config, cell, input_key, view.transform.output_dimension, profile).to(device)
    optimizer, optimizer_candidate = make_optimizer(config, model, optimizer_key)
    parameter_check = precision.validate_model_optimizer_fp32(model, optimizer, torch)
    logger.info(
        "%s 精度前置核验：FP32 浮点参数 %d 个，优化器浮点状态 %d 个（首次 step 前为 0）",
        cell, parameter_check["checked_floating_parameters"],
        parameter_check["checked_floating_optimizer_states"],
    )

    positive_weight = torch.tensor(
        [(1.0 - view.flow_positive_rate) / max(view.flow_positive_rate, 1e-8)],
        device=device,
        dtype=torch.float32,
    )
    flow_loss = torch.nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    sequence_loss = torch.nn.BCELoss(reduction="none")
    sequence_positive_weight = view.sequence_positive_weight

    if device_type == "cuda":
        precision.reset_cuda_peak_memory(torch, device)

    generator = torch.Generator().manual_seed(training["seed"])
    history: list[dict[str, Any]] = []
    best_ap = -1.0
    best_epoch = 0
    best_p = float("nan")
    best_state: dict[str, Any] | None = None
    first_step_memory: dict[str, Any] | None = None
    optimizer_step_count = 0
    processed_valid_flows = 0
    processed_sequences = 0
    total_steps = training["epochs"] * training["steps_per_epoch"]
    total_sequences = total_steps * effective_batch
    heartbeat_interval = max(1, training["steps_per_epoch"] // 4)
    elapsed_before = 0.0
    start_epoch = 1

    # 在途层恢复：只有传了 --resume 且在途检查点存在时才尝试恢复；身份、精度、
    # 微批量与累积步数任一不符都拒绝，不做部分拼接。
    if resume and inflight_path.is_file():
        inflight = torch.load(inflight_path, map_location="cpu", weights_only=False)
        if inflight.get("identity") != identity:
            raise RuntimeError(f"{cell} 在途检查点身份与本次运行不符，拒绝恢复")
        runtime_state = inflight["runtime_state"]
        precision.validate_checkpoint_runtime_state(runtime_state)
        if (
            runtime_state["precision_profile_id"] != profile_id
            or runtime_state["microbatch_items"] != micro_batch
            or runtime_state["accumulation_steps"] != accumulation_steps
        ):
            raise RuntimeError(f"{cell} 在途检查点的精度或批量合同与本次运行不符，拒绝恢复")
        model.load_state_dict(inflight["model_state_dict"])
        model.to(device)
        optimizer.load_state_dict(inflight["optimizer_state_dict"])
        _move_optimizer_state(optimizer, device)
        history = inflight["history"]
        best_ap = float(inflight["best_ap"])
        best_epoch = int(inflight["best_epoch"])
        best_p = float(inflight["best_p"])
        best_state = inflight["best_state"]
        elapsed_before = float(inflight["elapsed_seconds"])
        generator.set_state(inflight["generator_state"])
        rng_state = runtime_state["rng_state"]
        random.setstate(rng_state["python_random"])
        torch.set_rng_state(rng_state["torch_cpu"])
        if rng_state["torch_cuda_all"] is not None and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(rng_state["torch_cuda_all"])
        if rng_state["numpy_random"] is not None:
            np.random.set_state(rng_state["numpy_random"])
        start_epoch = int(inflight["epoch"]) + 1
        optimizer_step_count = int(inflight["epoch"]) * training["steps_per_epoch"]
        processed_sequences = optimizer_step_count * effective_batch
        logger.info(
            "%s 在途层恢复：身份、精度与批量合同均匹配，从第 %d 轮继续（已完成 %d 轮）",
            cell, start_epoch, int(inflight["epoch"]),
        )
    elif resume:
        logger.info("%s 未发现在途检查点，从第 1 轮开始（首次为本次运行的初次训练）", cell)

    started = time.time()
    model.train()
    # 若恢复自一个已跑满全部轮次但尚未落最终检查点的在途状态，下方轮次循环
    # 不会执行任何一次，accumulator 需要有定义的占位，避免收尾阶段引用未定义变量。
    accumulator: Any = None

    for epoch in range(start_epoch, training["epochs"] + 1):
        epoch_started = time.time()
        running_loss = 0.0
        for step in range(1, training["steps_per_epoch"] + 1):
            positions = sample_distinct_positions(len(train_rows), effective_batch, generator)
            rows = train_rows[positions.numpy()]
            indices, valid, flow_labels = view.gather_sequences(rows, length)
            total_valid_flows = int(valid.sum())
            sequence_labels = np.asarray(
                (flow_labels * valid).max(axis=1) > 0, dtype=np.float32
            )
            sequence_weights = (
                1.0 + (sequence_positive_weight - 1.0) * sequence_labels
            ).astype(np.float32)
            total_weight = float(sequence_weights.sum())
            # 辅助损失的自然分母是序列权重和，主损失的分母是全部有效流数；累积器只接受
            # 一个全局分母，因此把辅助项先乘 total_valid_flows/total_weight，
            # 除以 total_valid_flows 之后恰好还原为按序列权重的加权平均，数值完全等价。
            auxiliary_scale = (
                training["auxiliary_loss_weight"] * total_valid_flows / max(total_weight, 1e-8)
            )

            accumulator = precision.EffectiveBatchAccumulator(
                total_valid_units=total_valid_flows,
                normalization_unit=NORMALIZATION_UNIT,
                torch_module=torch,
                expected_microbatches=accumulation_steps,
            )
            accumulator.begin(optimizer)
            step_loss = 0.0
            for start in range(0, effective_batch, micro_batch):
                stop = min(start + micro_batch, effective_batch)
                micro_valid = valid[start:stop]
                micro_valid_flows = int(micro_valid.sum())
                values_t = torch.from_numpy(view.features(indices[start:stop])).to(device)
                valid_t = torch.from_numpy(micro_valid).to(device)
                labels_t = torch.from_numpy(flow_labels[start:stop]).to(device)
                mask32 = valid_t.to(torch.float32)
                labels32 = labels_t.to(torch.float32)
                with precision.autocast_context(profile, device_type, torch):
                    expanded_values, expanded_valid = model.expand_to_members(values_t, valid_t)
                    logits = model(expanded_values, expanded_valid)
                # 损失、概率归一化与掩码归约都是精度合同的敏感计算，进 FP32 岛。
                with precision.fp32_island(
                    logits, device_type=device_type, torch_module=torch
                ) as (logits32,):
                    member_labels = labels32.unsqueeze(MEMBER_AXIS).expand(-1, members, -1)
                    member_mask = mask32.unsqueeze(MEMBER_AXIS).expand(-1, members, -1)
                    # 32 个成员各自的二元交叉熵先求和再除以成员数，即成员损失均值；
                    # 禁止先平均概率再算训练损失。
                    loss_sum = (flow_loss(logits32, member_labels) * member_mask).sum() / members
                    if uses_lp:
                        # 先对 32 个成员概率做算术平均，再对唯一实体做 ELP。
                        flow_probability = model.member_mean_probability(logits32)
                        pooled = learned_lp_pool(flow_probability, mask32, model.p).clamp(
                            1e-6, 1.0 - 1e-6
                        )
                        auxiliary_labels = torch.from_numpy(sequence_labels[start:stop]).to(device)
                        auxiliary_weights = torch.from_numpy(sequence_weights[start:stop]).to(device)
                        auxiliary = (
                            sequence_loss(pooled, auxiliary_labels) * auxiliary_weights
                        ).sum()
                        loss_sum = loss_sum + auxiliary_scale * auxiliary
                normalized = accumulator.backward(loss_sum, micro_valid_flows, scaler=scaler)
                step_loss += float(normalized.detach())
            accumulator.finish(
                model.parameters(), optimizer, torch, training["gradient_clip_norm"], scaler=scaler
            )
            optimizer_step_count += 1
            processed_valid_flows += total_valid_flows
            processed_sequences += effective_batch
            running_loss += step_loss

            if optimizer_step_count == 1:
                state_check = precision.validate_model_optimizer_fp32(model, optimizer, torch)
                first_step_memory = {
                    "schema_version": "ch3-tabm32-first-step-memory-v1",
                    "identity": dict(identity),
                    "cell": cell,
                    "input_candidate": input_key,
                    "optimizer_candidate": optimizer_key,
                    "input_dimension": view.transform.output_dimension,
                    "precision_profile_id": profile_id,
                    "tensor_upper_bounds": bounds,
                    "accumulation_plan": plan,
                    "checked_floating_parameters": state_check["checked_floating_parameters"],
                    "checked_floating_optimizer_states": state_check[
                        "checked_floating_optimizer_states"
                    ],
                }
                if device_type == "cuda":
                    first_step_memory.update(gpu_memory_snapshot(torch, device))
                _atomic_json(
                    output_root
                    / "receipts"
                    / f"first-step-memory-{cell}-{input_key}-{optimizer_key}.json",
                    first_step_memory,
                )
                logger.info("%s 首次 optimizer.step() 后的显存快照：%s", cell, first_step_memory)

            if step % heartbeat_interval == 0 or step == training["steps_per_epoch"]:
                elapsed = time.time() - started
                throughput = processed_sequences / max(elapsed, 1e-9)
                remaining = (total_sequences - processed_sequences) / max(throughput, 1e-9)
                logger.info(
                    "%s 心跳 epoch=%d/%d step=%d/%d 已处理序列=%d/%d 有效流=%d "
                    "吞吐=%.1f 序列/秒 累计=%.1f 分 预计剩余=%.1f 分",
                    cell, epoch, training["epochs"], step, training["steps_per_epoch"],
                    processed_sequences, total_sequences, processed_valid_flows,
                    throughput, elapsed / 60.0, remaining / 60.0,
                )

        validation_ap, scored_flows = evaluate_validation_flow_ap(
            config, model, view, validation_rows, device, profile
        )
        p_value = float(model.p.detach())
        history.append(
            {
                "epoch": epoch,
                "validation_flow_ap": validation_ap,
                "p": p_value,
                "mean_training_loss": running_loss / training["steps_per_epoch"],
            }
        )
        # 严格大于：并列时保留最早轮次。不早停、不看目标年。
        if validation_ap > best_ap:
            best_ap = validation_ap
            best_epoch = epoch
            best_p = p_value
            best_state = {
                name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()
            }
        logger.info(
            "%s epoch=%d/%d 验证逐流AP=%.8f p=%.6f 平均训练损失=%.8f 计分流=%d",
            cell, epoch, training["epochs"], validation_ap, p_value,
            history[-1]["mean_training_loss"], scored_flows,
        )

        # 在途层落盘：写入点固定在本轮全部 optimizer.step() 完成之后，即完整边界。
        # 内容含身份、轮次、模型与优化器状态、历史、当前最优四元组、已耗时、
        # 采样器状态（generator_state）与由 neural_precision_runtime 构造的
        # 精度/批量/四路随机状态（runtime_state.rng_state）。
        epoch_elapsed_seconds = elapsed_before + (time.time() - started)
        inflight_runtime_state = precision.build_checkpoint_runtime_state(
            profile_id=profile_id,
            profile=profile,
            scaler=scaler,
            effective_batch_items=effective_batch,
            effective_batch_item_unit=EFFECTIVE_BATCH_ITEM_UNIT,
            microbatch_items=micro_batch,
            accumulation_steps=accumulation_steps,
            normalization_unit=NORMALIZATION_UNIT,
            is_tail_batch=False,
            optimizer_step=optimizer_step_count,
            optimizer_step_boundary=True,
            torch_module=torch,
        )
        _atomic_torch(
            inflight_path,
            {
                "schema_version": "ch3-tabm32-inflight-checkpoint-v1",
                "identity": dict(identity),
                "epoch": epoch,
                "model_state_dict": {
                    name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()
                },
                "optimizer_state_dict": optimizer.state_dict(),
                "history": history,
                "best_ap": best_ap,
                "best_epoch": best_epoch,
                "best_p": best_p,
                "best_state": best_state,
                "elapsed_seconds": epoch_elapsed_seconds,
                "generator_state": generator.get_state(),
                "runtime_state": inflight_runtime_state,
            },
        )

        if epoch == 1:
            epoch_seconds = time.time() - epoch_started
            logger.info(
                "%s 首轮实测 %.1f 分（%.4f 秒/优化步），按此换算全程 %d 轮预计 %.1f 小时；"
                "本运行不设人为墙钟或 GPU 小时上限，该数字只供判断是否继续",
                cell, epoch_seconds / 60.0, epoch_seconds / training["steps_per_epoch"],
                training["epochs"], epoch_seconds * training["epochs"] / 3600.0,
            )

    if best_state is None:
        raise RuntimeError(f"{cell} 未产生可选检查点")
    training_seconds = elapsed_before + (time.time() - started)

    runtime_state = precision.build_checkpoint_runtime_state(
        profile_id=profile_id,
        profile=profile,
        scaler=scaler,
        effective_batch_items=effective_batch,
        effective_batch_item_unit=EFFECTIVE_BATCH_ITEM_UNIT,
        microbatch_items=micro_batch,
        accumulation_steps=accumulation_steps,
        normalization_unit=NORMALIZATION_UNIT,
        is_tail_batch=False,
        optimizer_step=optimizer_step_count,
        optimizer_step_boundary=True,
        torch_module=torch,
    )
    precision.validate_checkpoint_runtime_state(runtime_state)
    checkpoint_path = output_root / "checkpoints" / f"selected-{cell}.pt"
    _atomic_torch(
        checkpoint_path,
        {
            "schema_version": "ch3-tabm32-protocol-a-selected-checkpoint-v1",
            "identity": dict(identity),
            "cell": cell,
            "input_candidate": input_key,
            "optimizer_candidate": optimizer_key,
            "input_dimension": view.transform.output_dimension,
            "input_transform_state_hash": view.transform.state_hash,
            "selected_epoch": best_epoch,
            "model": best_state,
            "runtime_state": runtime_state,
        },
    )

    external_mib = (
        external_process_gpu_memory_mib(torch, device) if device_type == "cuda" else None
    )
    resource_receipt = precision.collect_resource_receipt(
        profile_id=profile_id,
        device_type=device_type,
        effective_batch_items=effective_batch,
        microbatch_items=micro_batch,
        accumulation_steps=accumulation_steps,
        normalization_unit=NORMALIZATION_UNIT,
        processed_valid_units=processed_valid_flows,
        elapsed_seconds=training_seconds,
        external_process_gpu_memory_mib=external_mib,
        external_measurement_source=(
            "torch.cuda.mem_get_info 总量减空闲减本进程 memory_reserved" if device_type == "cuda" else "非 CUDA 设备"
        ),
        torch_module=torch,
        device=device,
    )
    precision.validate_resource_receipt(resource_receipt)

    selection = {
        "selected_epoch": best_epoch,
        "validation_flow_ap": best_ap,
        "p_at_selection": best_p,
        "history": history,
        "training_seconds": training_seconds,
        "checkpoint": {
            "filename": str(checkpoint_path.relative_to(output_root)),
            "bytes": checkpoint_path.stat().st_size,
            "sha256": _sha256_file(checkpoint_path),
        },
        "parameter_count": sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        ),
        "peak_gpu_allocated_mib": (
            int(torch.cuda.max_memory_allocated(device)) / 2**20 if device_type == "cuda" else None
        ),
        "peak_process_rss_mib": _process_peak_rss_mib(),
        "input_candidate": input_key,
        "optimizer_candidate": optimizer_key,
        "input_dimension": view.transform.output_dimension,
        "precision_profile_id": profile_id,
        "precision_contract_schema_version": contract["schema_version"],
        "precision_resource_receipt": resource_receipt,
        "accumulation_plan": plan,
        "accumulation_receipt": (
            accumulator.receipt()
            if accumulator is not None
            else {"reused_from_inflight_without_new_optimizer_steps": True}
        ),
        "optimizer_steps": optimizer_step_count,
        "tensor_upper_bounds": bounds,
        "first_step_memory": first_step_memory,
        "training_sequences_per_second": processed_sequences / max(training_seconds, 1e-9),
        "learning_rate": optimizer_candidate["learning_rate"],
        "weight_decay": optimizer_candidate["weight_decay"],
    }
    logger.info(
        "%s 训练完成：最优轮次=%d 验证逐流AP=%.8f p=%.6f 用时=%.1f 分 检查点=%s",
        cell, best_epoch, best_ap, best_p, training_seconds / 60.0, checkpoint_path,
    )

    # 完成层收据：与最终检查点一起构成可复用判据（身份 + 检查点摘要）。
    _atomic_json(receipt_path, {"identity": dict(identity), "selection": selection})
    inflight_path.unlink(missing_ok=True)
    return selection


# ---------------------------------------------------------------------------
# 运行身份、数据清单与训练有效流掩码（任务 5 支撑）
# ---------------------------------------------------------------------------


def _resolve_device() -> Any:
    """解析本次运行的计算设备；精度合同要求 CUDA BF16，无 CUDA 时不静默降级。"""
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    raise RuntimeError(
        "本运行的精度合同 cuda-bf16-amp-fp32-sensitive-v1 要求 CUDA，"
        "当前环境无可用 CUDA；非 CUDA 环境须先取得显式例外收据，本工具不静默降级"
    )


def data_inventory(cache_root: Path, names: tuple[str, ...]) -> dict[str, Any]:
    """对若干冻结缓存文件的字节数与 mtime 取规范化摘要，作为数据版本身份的一部分。"""
    files: list[dict[str, Any]] = []
    for name in names:
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少冻结缓存：{path}")
        stat = path.stat()
        files.append({"name": path.name, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    return {
        "schema_version": "ch3-tabm32-data-inventory-v1",
        "cache_root": str(cache_root),
        "files": files,
        "sha256": _canonical_sha256(files),
    }


def build_effective_flow_mask(
    indices: Any, mask: Any, train_rows: Any, flow_count: int
) -> tuple[Any, dict[str, Any]]:
    """训练有效流掩码：把训练区序列的有效位置映射到流索引，去重后置真。

    与诊断工具 ``tools/ch3_lspr23_field_cardinality_receipt.py`` 的
    ``build_effective_flow_mask``（第 182 至 205 行）逐字同算法（含分块行数
    4096），使本工具独立重算出的掩码哈希能够与收据登记的
    ``effective_flow_mask_sha256`` 相互核验，而不是单方面信任收据。
    """
    import hashlib

    import numpy as np

    if indices.shape != mask.shape or indices.ndim != 2:
        raise RuntimeError("I23/M23 形状不符")
    effective = np.zeros(flow_count, dtype=bool)
    valid_occurrences = 0
    for start in range(0, len(train_rows), 4096):
        rows = train_rows[start : start + 4096]
        current_mask = np.asarray(mask[rows], dtype=bool)
        current_indices = np.asarray(indices[rows])
        selected = current_indices[current_mask]
        if selected.size:
            if int(selected.min()) < 0 or int(selected.max()) >= flow_count:
                raise RuntimeError("I23 存在越界流索引")
            effective[selected] = True
            valid_occurrences += int(selected.size)
    digest = hashlib.sha256(effective.tobytes()).hexdigest()
    return effective, {
        "train_sequences": int(len(train_rows)),
        "sequence_length": int(indices.shape[1]),
        "valid_sequence_flow_occurrences": valid_occurrences,
        "effective_flows": int(effective.sum()),
        "deduplicated_flow_mapping": True,
        "effective_flow_mask_sha256": digest,
    }


def build_run_identity(
    config_path: Path, cache_root: Path, cardinality_receipt_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """本工具独立重算的运行身份：配置、代码、源数据与字段基数收据四路哈希。

    返回 ``(identity, source_data_inventory)``；identity 不含候选或 cell，
    候选与 cell 由 ``cell_identity`` 在其基础上补齐。
    """
    source_inventory = data_inventory(cache_root, SOURCE_ARRAYS)
    identity = {
        "schema_version": "ch3-tabm32-run-identity-v1",
        "config_sha256": _sha256_file(config_path),
        "code_sha256": _sha256_file(Path(__file__).resolve()),
        "source_data_inventory_sha256": source_inventory["sha256"],
        "cardinality_receipt_sha256": _sha256_file(cardinality_receipt_path),
    }
    return identity, source_inventory


def cell_identity(
    run_identity: dict[str, Any], *, input_candidate: str, optimizer_candidate: str, cell: str
) -> dict[str, Any]:
    """把运行身份补齐为某个 cell 训练调用的完整身份，供 train_cell 的三层恢复比对。"""
    return {
        "schema_version": "ch3-tabm32-cell-identity-v1",
        "run_id": RUN_ID,
        "model_key": MODEL_KEY,
        **run_identity,
        "input_candidate": input_candidate,
        "optimizer_candidate": optimizer_candidate,
        "cell": cell,
    }


def materialize_reused_cell(
    source_root: Path, target_root: Path, cell: str, identity: dict[str, Any]
) -> dict[str, Any]:
    """把选择阶段已完成、身份完全一致的 cell 检查点与收据复制到最终输出根。

    只在调用方已核验候选与优化器均为封印值时调用；这里再独立核对一次收据身份与
    检查点摘要，防止把不同配置/代码/数据下产出的制品部分拼接进最终四格。
    """
    import shutil

    source_checkpoint = source_root / "checkpoints" / f"selected-{cell}.pt"
    source_receipt = source_root / "receipts" / f"selection-{cell}.json"
    if not source_checkpoint.is_file() or not source_receipt.is_file():
        raise RuntimeError(f"待复用的 {cell} 选择运行制品不完整：{source_root}")
    receipt = load_json(source_receipt)
    if receipt.get("identity") != identity:
        raise RuntimeError(f"待复用的 {cell} 选择运行身份与目标身份不符，拒绝复用")
    if receipt["selection"]["checkpoint"]["sha256"] != _sha256_file(source_checkpoint):
        raise RuntimeError(f"待复用的 {cell} 选择运行检查点摘要不符，拒绝复用")
    target_checkpoint = target_root / "checkpoints" / f"selected-{cell}.pt"
    target_receipt = target_root / "receipts" / f"selection-{cell}.json"
    target_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    target_receipt.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_checkpoint, target_checkpoint)
    shutil.copy2(source_receipt, target_receipt)
    logger.info("%s 已从选择阶段完成运行复用（身份与检查点摘要均核验通过）：%s -> %s", cell, source_root, target_root)
    return receipt["selection"]


def save_input_transform(path: Path, transform: InputTransform) -> None:
    """把已在 LSPR23 训练区拟合完成的输入变换整体持久化，供 evaluate 阶段只应用不拟合。

    ``InputTransform`` 内部含 sklearn ``QuantileTransformer`` 与 numpy 数组，
    均为标准库 ``pickle`` 可序列化对象；先写临时文件再原子替换。
    """
    import os
    import pickle

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        pickle.dump(transform, handle, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(temporary, path)


def load_input_transform(path: Path) -> InputTransform:
    """加载 ``cells`` 阶段封印的输入变换；``evaluate`` 阶段只应用，绝不重新拟合。"""
    import pickle

    if not path.is_file():
        raise FileNotFoundError(f"缺少已封印的输入变换：{path}，须先完成 cells 阶段")
    with path.open("rb") as handle:
        transform = pickle.load(handle)
    if not isinstance(transform, InputTransform):
        raise RuntimeError(f"已封印的输入变换类型不符：{path}")
    return transform


def load_target_arrays(cache_root: str) -> dict[str, Any]:
    """加载协议 A 目标年（LSPR24）冻结数组；s24/d24 为对象数组，按需允许 pickle。"""
    import numpy as np

    root = Path(cache_root)
    arrays: dict[str, Any] = {}
    for name in TARGET_ARRAYS:
        path = root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少冻结缓存：{path}")
        arrays[name] = np.load(path, allow_pickle=name in {"s24", "d24"})
    if arrays["X24"].shape[1] != DIJK_FEATURE_COUNT:
        raise RuntimeError(f"X24 字段数不符：{arrays['X24'].shape}")
    logger.info("目标年数组已载入：X24=%s I24=%s", arrays["X24"].shape, arrays["I24"].shape)
    return arrays


def write_status(output_root: Path, state: str, stage: str, exit_code: int | None, detail: str) -> None:
    """原子写运行级状态文件，供人工与启动器只读核对进度。"""
    import time

    _atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-tabm32-paper-recipe-protocol-a-status-v1",
            "run_id": RUN_ID,
            "state": state,
            "stage": stage,
            "exit_code": exit_code,
            "detail": detail,
            "updated_at_unix": time.time(),
            "target_previously_accessed": True,
            "independent_test": False,
        },
    )


def build_manifest(output_root: Path, run_id: str) -> None:
    """重写运行根的制品清单：只登记确实存在的文件，逐个记录字节数与摘要。"""
    names = (
        "config.json",
        "input_selection_sealed.json",
        "optimizer_selection_sealed.json",
        "selection_frozen.json",
        "aggregate-results.json",
        "complete-alert-budget-curves.npz",
        "complete-alert-budget-curves-receipt.json",
        "resource-receipt.json",
        "swanlab-receipt.json",
        "status.json",
        "artifacts/sealed-input-transform.pkl",
    )
    files: dict[str, Any] = {}
    for name in names:
        path = output_root / name
        if path.is_file():
            files[name] = {"bytes": path.stat().st_size, "sha256": _sha256_file(path)}
    for cell in CELL_ORDER:
        for relative in (
            f"checkpoints/selected-{cell}.pt",
            f"receipts/selection-{cell}.json",
            f"receipts/target-evaluation-{cell}/receipt.json",
            f"receipts/target-evaluation-{cell}/complete-alert-budget-curve.npz",
        ):
            path = output_root / relative
            if path.is_file():
                files[relative] = {"bytes": path.stat().st_size, "sha256": _sha256_file(path)}
    _atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-tabm32-paper-recipe-protocol-a-manifest-v1",
            "run_id": run_id,
            "files": files,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "complete_budget_curve_persisted": "complete-alert-budget-curves.npz" in files,
        },
    )


# ---------------------------------------------------------------------------
# 选择封印、目标评价与制品清单（任务 6）
# ---------------------------------------------------------------------------


def entity_scores(flow_scores: Any, seen: Any, flow_entity: Any, entity_count: int, p_value: float | None) -> Any:
    """按实体聚合逐流分数：``p_value`` 为空取实体内最大值，否则做共享 p 的 ELP 池化。

    与既有同族工具 ``tools/ch3_resmlp2_tabm_protocol_a_2x2.py`` 的
    ``entity_scores`` 同公式，供 ``evaluate`` 阶段区分「主指标（学习池化格用 ELP，
    其余格用最大池化）」与「最大池化指标（全部格统一用最大池化）」。
    """
    import numpy as np

    if p_value is None:
        scores = np.full(entity_count, -np.inf, dtype=np.float32)
        np.maximum.at(scores, flow_entity[seen], flow_scores[seen])
        return scores
    numerator = np.zeros(entity_count, dtype=np.float64)
    count = np.zeros(entity_count, dtype=np.float64)
    np.add.at(numerator, flow_entity[seen], np.clip(flow_scores[seen], 1e-7, 1.0).astype(np.float64) ** p_value)
    np.add.at(count, flow_entity[seen], 1.0)
    return np.where(count > 0, (numerator / np.maximum(count, 1.0)) ** (1.0 / p_value), -np.inf).astype(np.float32)


def dr_at_fpr(scores: Any, labels: Any, target_fpr: float) -> float:
    """给定负类实体分数排序后，在最接近 ``target_fpr`` 的整数下标处取检测率。"""
    import numpy as np

    valid = np.isfinite(scores)
    values = scores[valid]
    target = labels[valid]
    negative = np.sort(values[target == 0])[::-1]
    positive = values[target == 1]
    if len(negative) == 0 or len(positive) == 0:
        raise RuntimeError("检测率计算缺少正类或负类实体")
    threshold = negative[min(int(len(negative) * target_fpr), len(negative) - 1)]
    return float((positive >= threshold).mean())


def complete_budget_curve(scores: Any, labels: Any) -> dict[str, Any]:
    """遍历全部可达负类实体预算，给出完整检测率-误报预算曲线。"""
    import numpy as np

    valid = np.isfinite(scores)
    values = scores[valid]
    target = labels[valid]
    positive = np.sort(values[target == 1])
    negative = np.sort(values[target == 0])[::-1]
    detection_rate = (len(positive) - np.searchsorted(positive, negative, side="left")) / len(positive)
    false_positive = len(negative) - np.searchsorted(negative[::-1], negative, side="left")
    return {
        "n_false_positive_entity": false_positive.astype(np.int64),
        "nominal_fpr": np.arange(len(negative), dtype=np.float64) / len(negative),
        "realized_fpr": false_positive.astype(np.float64) / len(negative),
        "detection_rate": detection_rate.astype(np.float64),
    }


def save_target_evaluation(
    output_root: Path, cell: str, identity: dict[str, Any], cell_result: dict[str, Any], curve: dict[str, Any]
) -> None:
    """原子写某格的目标评价完成收据与完整预算曲线，目录整体存在即视为完成。"""
    import os

    import numpy as np

    receipt_root = output_root / "receipts" / f"target-evaluation-{cell}"
    if receipt_root.exists():
        raise RuntimeError(f"{cell} 目标评价完成目录已存在，拒绝覆盖")
    temporary_root = receipt_root.with_name(f"{receipt_root.name}.partial.{os.getpid()}")
    temporary_root.mkdir(parents=True, exist_ok=False)
    curve_path = temporary_root / "complete-alert-budget-curve.npz"
    with curve_path.open("wb") as handle:
        np.savez_compressed(handle, **curve)
    _atomic_json(
        temporary_root / "receipt.json",
        {
            "schema_version": "ch3-tabm32-target-cell-receipt-v1",
            "identity": identity,
            "cell_result": cell_result,
            "curve": {
                "filename": curve_path.name,
                "bytes": curve_path.stat().st_size,
                "sha256": _sha256_file(curve_path),
                "fields": list(curve),
            },
            "complete": True,
        },
    )
    os.replace(temporary_root, receipt_root)


def load_target_evaluation(
    output_root: Path, cell: str, identity: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """复用已完成的目标评价收据；身份或摘要任一不符都拒绝伪装完成。"""
    import numpy as np

    receipt_root = output_root / "receipts" / f"target-evaluation-{cell}"
    if not receipt_root.exists():
        return None
    if not receipt_root.is_dir():
        raise RuntimeError(f"{cell} 目标评价收据路径类型不符")
    receipt_path = receipt_root / "receipt.json"
    curve_path = receipt_root / "complete-alert-budget-curve.npz"
    if not receipt_path.is_file() or not curve_path.is_file():
        raise RuntimeError(f"{cell} 目标评价只有部分写入，拒绝伪装完成")
    receipt = load_json(receipt_path)
    if (
        receipt.get("identity") != identity
        or receipt.get("complete") is not True
        or receipt.get("curve", {}).get("sha256") != _sha256_file(curve_path)
    ):
        raise RuntimeError(f"{cell} 目标评价收据身份或摘要不符")
    with np.load(curve_path, allow_pickle=False) as payload:
        curve = {name: payload[name] for name in payload.files}
    if set(curve) != {"n_false_positive_entity", "nominal_fpr", "realized_fpr", "detection_rate"}:
        raise RuntimeError(f"{cell} 目标评价预算曲线字段不完整")
    return receipt["cell_result"], curve


def score_target(
    config: dict[str, Any],
    model: Any,
    transform: InputTransform,
    target: dict[str, Any],
    device: Any,
    profile: dict[str, Any],
) -> tuple[Any, Any]:
    """对 LSPR24 全量序列打分；输入变换只 ``apply``，绝不在目标年上重新拟合。

    评价阶段不得训练、不得替换检查点、不得裁剪成员、不得搜索阈值、不得更新聚合
    指数或任何超参数，因此这里全程 ``torch.no_grad()``，且不调用
    ``optimizer``、不调用 ``model.train()``。
    """
    import numpy as np
    import torch

    precision = _precision_module()
    length = config["training"]["sequence_length"]
    X = target["X24"]
    I = target["I24"]
    M = target["M24"]
    y = target["y24"]
    scores = np.zeros(len(y), dtype=np.float32)
    seen = np.zeros(len(y), dtype=bool)
    batch_sequences = 2048
    model.eval()
    with torch.no_grad():
        for start in range(0, len(I), batch_sequences):
            stop = min(start + batch_sequences, len(I))
            indices = np.ascontiguousarray(I[start:stop, :length])
            valid = np.ascontiguousarray(M[start:stop, :length] > 0.5)
            raw = np.asarray(X[indices.reshape(-1)], dtype=np.float32)
            values = transform.apply(raw).reshape(indices.shape[0], indices.shape[1], transform.output_dimension)
            values_t = torch.from_numpy(values).to(device)
            valid_t = torch.from_numpy(valid).to(device)
            with precision.autocast_context(profile, device.type, torch):
                probabilities = model.shared_batch_flow_probability(values_t, valid_t)
            flat_indices = indices.reshape(-1)
            flat_valid = valid.reshape(-1)
            flat_probabilities = probabilities.reshape(-1).float().cpu().numpy()
            selected = flat_indices[flat_valid]
            scores[selected] = flat_probabilities[flat_valid]
            seen[selected] = True
    return scores, seen


def publish_swanlab(config: dict[str, Any], result: dict[str, Any], output_root: Path) -> None:
    """创建 SwanLab 运行并上报聚合指标；只使用已核验存在的 Run 公开属性。

    核验依据（2026-08-13 本仓库事故记录）：SwanLab 0.9.0 的 ``Run`` 对象只公开
    ``id``/``name``/``path``/``url``/``dir``/``config``/``log*`` 七类属性，没有
    ``public`` 属性；本函数只读取 ``name``/``id``/``url`` 三个已核验字段用于收据
    留痕，不访问 ``run.public``。上传前先机械核对目的地与冻结配置逐字相同。
    """
    destination = config["swanlab"]
    if destination != _EXPECTED_SWANLAB:
        raise RuntimeError("SwanLab 目的地与冻结配置不一致，拒绝创建运行或上传")

    import swanlab

    run = swanlab.init(
        workspace=destination["workspace"],
        project=destination["project"],
        name=RUN_ID,
        mode=destination["mode"],
        group=destination["group"],
        tags=destination["tags"],
        log_dir=str(output_root / "swanlog"),
        config={
            "run_id": RUN_ID,
            "model_key": MODEL_KEY,
            "seed": config["training"]["seed"],
            "protocol": "tabm32_paper_recipe_protocol_a",
            "target_previously_accessed": True,
            "independent_test": False,
        },
    )
    if run.name != RUN_ID:
        raise RuntimeError("SwanLab 运行名称与冻结身份不符，拒绝上报")

    metrics: dict[str, float] = {}
    for cell in CELL_ORDER:
        selection = result["source_selection"]["cells"][cell]
        cell_target = result["target_evaluation"]["cells"][cell]["target"]
        metrics[f"source/{cell}_selected_epoch"] = float(selection["selected_epoch"])
        metrics[f"source/{cell}_validation_flow_ap"] = float(selection["validation_flow_ap"])
        metrics[f"target/{cell}_flow_ap"] = cell_target["flow_average_precision"]
        metrics[f"target/{cell}_entity_ap"] = cell_target["entity_average_precision"]
        metrics[f"target/{cell}_maximum_entity_ap"] = cell_target["maximum_entity_average_precision"]
        for key, value in cell_target["dr_at_fpr"].items():
            metrics[f"target/{cell}_dr_{key}"] = value
    metrics["resource/training_wall_seconds"] = result["resource"]["training_wall_seconds_sum"]
    metrics["resource/evaluation_wall_seconds"] = result["resource"]["evaluation_wall_seconds_sum"]
    metrics["resource/peak_gpu_allocated_mib"] = result["resource"]["peak_gpu_allocated_mib"]
    metrics["resource/peak_process_rss_mib"] = result["resource"]["peak_process_rss_mib"]
    metrics["resource/gpu_hours"] = result["resource"]["gpu_hours"]
    swanlab.log(metrics, step=0)
    swanlab.finish()
    _atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-tabm32-paper-recipe-protocol-a-swanlab-receipt-v1",
            "completed": True,
            "workspace": destination["workspace"],
            "project": destination["project"],
            "run_name": run.name,
            "run_id_field": run.id,
            "run_url": run.url,
            "metric_count": len(metrics),
            "per_sample_values_uploaded": False,
        },
    )


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
        help="恢复同运行身份下的在途检查点或已封印选择；未传时任一历史制品存在都拒绝覆盖",
    )
    parser.add_argument(
        "--stage",
        choices=STAGE_CHOICES,
        help="要执行的实验阶段：select-input / select-optimizer / cells / evaluate",
    )
    parser.add_argument(
        "--resource-receipt",
        help="启动器写入的资源准入收据路径；evaluate 阶段原样并入聚合结果的 resource 字段",
    )
    return parser.parse_args()


def run_select_input_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段一：训练两个输入候选各自的 C00（固定阶段一优化器候选），封印胜出输入接口。

    并列裁决固定为「候选一（table order 第一个）」；只用
    ``lspr23_entity_disjoint_validation_flow_ap`` 决策，不看实体 AP、告警预算、
    训练时间、显存或 LSPR24（``selection_stages.forbidden_tie_breakers``）。
    """
    import time

    config_path = Path(args.config).resolve()
    cache_root = Path(config["paths"]["cache_root"])
    output_root = Path(config["paths"]["output_root"])
    receipt_path = Path(config["paths"]["field_cardinality_receipt"])
    seal_path = output_root / "input_selection_sealed.json"

    if seal_path.is_file():
        if not args.resume:
            raise RuntimeError(f"全新运行（未传 --resume）已存在输入接口封印，拒绝覆盖：{seal_path}")
        logger.info("阶段一封印已存在且传了 --resume，直接复用：%s", seal_path)
        return

    # 先做纯标准库的收据存在性与内容核验，再写运行状态：避免在收据缺失时
    # 仍尝试建立运行输出目录（本地无网络盘挂载时会报误导性的目录创建失败）。
    receipt = load_cardinality_receipt(str(receipt_path), config)
    write_status(output_root, "running", "select-input", None, "训练两个输入候选各自的 C00 以选择输入接口")

    run_identity, source_inventory = build_run_identity(config_path, cache_root, receipt_path)
    arrays = load_source_arrays(str(cache_root))
    train_rows, validation_rows, split_stats = source_split(arrays, config)
    train_flow_mask, flow_mapping = build_effective_flow_mask(
        arrays["I23"], arrays["M23"], train_rows, LSPR23_FLOW_COUNT
    )
    if flow_mapping["effective_flow_mask_sha256"] != receipt["training_effective_flows"]["effective_flow_mask_sha256"]:
        raise RuntimeError("本工具独立重算的训练有效流掩码与收据登记的哈希不一致，拒绝继续")

    fixed_optimizer = config["selection_stages"]["stage_one_fixed_optimizer"]
    device = _resolve_device()
    runs: dict[str, Any] = {}
    for candidate in sorted(INPUT_CANDIDATES, key=lambda item: item["order"]):
        key = candidate["key"]
        run_root = output_root / "selection-runs" / "select-input" / key
        transform = fit_input_transform(
            key, str(cache_root), train_flow_mask, receipt, config=config, seed=config["training"]["seed"]
        )
        view = ProtocolASourceView(arrays, transform)
        identity = cell_identity(run_identity, input_candidate=key, optimizer_candidate=fixed_optimizer, cell="C00")
        selection = train_cell(
            config, "C00", key, fixed_optimizer,
            output_root=run_root, identity=identity, view=view,
            train_rows=train_rows, validation_rows=validation_rows, device=device, resume=args.resume,
        )
        runs[key] = {
            "identity": identity,
            "input_dimension": transform.output_dimension,
            "parameter_count": expected_parameter_count(transform.output_dimension),
            "selection": selection,
        }
        logger.info("阶段一 %s（%s）训练完成：验证逐流AP=%.8f", key, candidate["display_name"], selection["validation_flow_ap"])

    key_a, key_b = (c["key"] for c in sorted(INPUT_CANDIDATES, key=lambda item: item["order"]))
    ap_a = runs[key_a]["selection"]["validation_flow_ap"]
    ap_b = runs[key_b]["selection"]["validation_flow_ap"]
    if ap_b > ap_a:
        best_key = key_b
        reason = f"候选二验证逐流AP={ap_b!r}严格高于候选一{ap_a!r}"
    elif ap_a == ap_b:
        best_key = key_a
        reason = f"两候选验证逐流AP并列={ap_a!r}，按冻结候选表固定顺序取候选一"
    else:
        best_key = key_a
        reason = f"候选一验证逐流AP={ap_a!r}高于候选二{ap_b!r}"

    seal = {
        "schema_version": "ch3-tabm32-input-selection-sealed-v1",
        "run_id": RUN_ID,
        "identity": run_identity,
        "source_data_inventory": source_inventory,
        "source_split": split_stats,
        "cardinality_receipt_flow_mapping": flow_mapping,
        "fixed_optimizer_candidate": fixed_optimizer,
        "runs": runs,
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_metric_full_precision": {key_a: ap_a, key_b: ap_b},
        "tie_break_rule": "fixed_table_order",
        "forbidden_tie_breakers": list(config["selection_stages"]["forbidden_tie_breakers"]),
        "selected_candidate": best_key,
        "selection_reason": reason,
        "sealed_at_unix": time.time(),
    }
    _atomic_json(seal_path, seal)
    write_status(output_root, "running", "select-input", 0, f"输入接口已封印：{best_key}")
    logger.info("阶段一封印完成：胜出输入候选=%s（%s）", best_key, reason)


def run_select_optimizer_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段二：在已封印输入上训练优化器候选二的 C00，与阶段一对应结果比较。

    不重训优化器候选一：阶段一固定用它训练过 C00，这里直接复用阶段一该结果做比较。
    完全相等或候选一更高时取 ``tabm32-official-default``（冻结配方第 181 行）。
    """
    import time

    config_path = Path(args.config).resolve()
    cache_root = Path(config["paths"]["cache_root"])
    output_root = Path(config["paths"]["output_root"])
    receipt_path = Path(config["paths"]["field_cardinality_receipt"])
    input_seal_path = output_root / "input_selection_sealed.json"
    seal_path = output_root / "optimizer_selection_sealed.json"

    if not input_seal_path.is_file():
        raise RuntimeError(f"尚未完成阶段一输入接口封印，禁止进入阶段二：{input_seal_path}")
    input_seal = load_json(input_seal_path)
    sealed_input_candidate = input_seal["selected_candidate"]
    fixed_optimizer_key = input_seal["fixed_optimizer_candidate"]

    if seal_path.is_file():
        if not args.resume:
            raise RuntimeError(f"全新运行（未传 --resume）已存在优化器封印，拒绝覆盖：{seal_path}")
        logger.info("阶段二封印已存在且传了 --resume，直接复用：%s", seal_path)
        return

    # 先做纯标准库的收据核验，再写运行状态，理由同 select-input 阶段。
    receipt = load_cardinality_receipt(str(receipt_path), config)
    write_status(output_root, "running", "select-optimizer", None, "在已封印输入上训练优化器候选二的 C00")

    run_identity, source_inventory = build_run_identity(config_path, cache_root, receipt_path)
    if run_identity != input_seal["identity"]:
        raise RuntimeError("阶段二独立重算的运行身份与阶段一封印不符，拒绝在不同配置/代码/数据版本间比较")

    arrays = load_source_arrays(str(cache_root))
    train_rows, validation_rows, split_stats = source_split(arrays, config)
    train_flow_mask, flow_mapping = build_effective_flow_mask(
        arrays["I23"], arrays["M23"], train_rows, LSPR23_FLOW_COUNT
    )
    if flow_mapping["effective_flow_mask_sha256"] != receipt["training_effective_flows"]["effective_flow_mask_sha256"]:
        raise RuntimeError("本工具独立重算的训练有效流掩码与收据登记的哈希不一致，拒绝继续")

    stage_two_keys = list(config["selection_stages"]["stage_two_optimizer"])
    challenger_candidates = [c["key"] for c in OPTIMIZER_CANDIDATES if c["key"] != fixed_optimizer_key]
    if stage_two_keys != [fixed_optimizer_key, *challenger_candidates]:
        raise RuntimeError("selection_stages.stage_two_optimizer 顺序与阶段一固定优化器候选不符")
    challenger_key = challenger_candidates[0]

    device = _resolve_device()
    transform = fit_input_transform(
        sealed_input_candidate, str(cache_root), train_flow_mask, receipt,
        config=config, seed=config["training"]["seed"],
    )
    view = ProtocolASourceView(arrays, transform)
    challenger_identity = cell_identity(
        run_identity, input_candidate=sealed_input_candidate, optimizer_candidate=challenger_key, cell="C00"
    )
    challenger_run_root = output_root / "selection-runs" / "select-optimizer" / challenger_key
    challenger_selection = train_cell(
        config, "C00", sealed_input_candidate, challenger_key,
        output_root=challenger_run_root, identity=challenger_identity, view=view,
        train_rows=train_rows, validation_rows=validation_rows, device=device, resume=args.resume,
    )

    incumbent_run = input_seal["runs"][sealed_input_candidate]
    incumbent_ap = float(incumbent_run["selection"]["validation_flow_ap"])
    challenger_ap = float(challenger_selection["validation_flow_ap"])
    if challenger_ap > incumbent_ap:
        best_key = challenger_key
        reason = f"候选二（{challenger_key}）验证逐流AP={challenger_ap!r}严格高于候选一{incumbent_ap!r}"
    elif challenger_ap == incumbent_ap:
        best_key = fixed_optimizer_key
        reason = f"两优化器候选验证逐流AP并列={incumbent_ap!r}，按冻结配方第181行取 tabm32-official-default"
    else:
        best_key = fixed_optimizer_key
        reason = f"候选一（{fixed_optimizer_key}）验证逐流AP={incumbent_ap!r}高于候选二{challenger_ap!r}"

    seal = {
        "schema_version": "ch3-tabm32-optimizer-selection-sealed-v1",
        "run_id": RUN_ID,
        "identity": run_identity,
        "sealed_input_candidate": sealed_input_candidate,
        "runs": {
            fixed_optimizer_key: incumbent_run,
            challenger_key: {"identity": challenger_identity, "selection": challenger_selection},
        },
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_metric_full_precision": {fixed_optimizer_key: incumbent_ap, challenger_key: challenger_ap},
        "tie_break_rule": "frozen_recipe_line_181_tabm32_official_default_on_tie_or_loss",
        "forbidden_tie_breakers": list(config["selection_stages"]["forbidden_tie_breakers"]),
        "selected_candidate": best_key,
        "selection_reason": reason,
        "sealed_at_unix": time.time(),
    }
    _atomic_json(seal_path, seal)
    write_status(output_root, "running", "select-optimizer", 0, f"优化器已封印：{best_key}")
    logger.info("阶段二封印完成：胜出优化器候选=%s（%s）", best_key, reason)


def run_cells_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """协议 A 四格：用已封印的输入与优化器训练 C00/C01/C10/C11，全部完成后写选择封印。

    C00 只有在配置、代码、数据、字段基数收据与检查点身份完全一致时才复用阶段一或
    阶段二的完成运行；任一不符都以新运行身份在最终输出根重训，不做部分拼接。
    """
    import time

    config_path = Path(args.config).resolve()
    cache_root = Path(config["paths"]["cache_root"])
    output_root = Path(config["paths"]["output_root"])
    receipt_path = Path(config["paths"]["field_cardinality_receipt"])
    input_seal_path = output_root / "input_selection_sealed.json"
    optimizer_seal_path = output_root / "optimizer_selection_sealed.json"
    selection_frozen_path = output_root / "selection_frozen.json"

    if not input_seal_path.is_file() or not optimizer_seal_path.is_file():
        raise RuntimeError(
            "尚未完成阶段一/阶段二封印，禁止进入 cells 阶段："
            f"输入封印存在={input_seal_path.is_file()}，优化器封印存在={optimizer_seal_path.is_file()}"
        )
    input_seal = load_json(input_seal_path)
    optimizer_seal = load_json(optimizer_seal_path)
    sealed_input_candidate = input_seal["selected_candidate"]
    sealed_optimizer_candidate = optimizer_seal["selected_candidate"]

    if selection_frozen_path.is_file():
        if not args.resume:
            raise RuntimeError(f"全新运行（未传 --resume）已存在选择封印，拒绝覆盖：{selection_frozen_path}")
        seal = load_json(selection_frozen_path)
        if set(seal.get("cells", {})) != set(CELL_ORDER) or seal.get("all_four_cells_sealed") is not True:
            raise RuntimeError("既有选择封印不完整，拒绝在其上继续")
        logger.info("四格选择封印已存在且传了 --resume，直接复用：%s", selection_frozen_path)
        return

    # 先做纯标准库的收据核验，再写运行状态，理由同 select-input 阶段。
    receipt = load_cardinality_receipt(str(receipt_path), config)
    write_status(output_root, "running", "cells", None, "训练协议 A 四格并封印选择")

    run_identity, source_inventory = build_run_identity(config_path, cache_root, receipt_path)
    if run_identity != input_seal["identity"] or run_identity != optimizer_seal["identity"]:
        raise RuntimeError("cells 阶段独立重算的运行身份与阶段一/阶段二封印不符")
    arrays = load_source_arrays(str(cache_root))
    train_rows, validation_rows, split_stats = source_split(arrays, config)
    train_flow_mask, flow_mapping = build_effective_flow_mask(
        arrays["I23"], arrays["M23"], train_rows, LSPR23_FLOW_COUNT
    )
    if flow_mapping["effective_flow_mask_sha256"] != receipt["training_effective_flows"]["effective_flow_mask_sha256"]:
        raise RuntimeError("cells 阶段独立重算的训练有效流掩码与收据登记的哈希不一致，拒绝继续")

    device = _resolve_device()
    transform = fit_input_transform(
        sealed_input_candidate, str(cache_root), train_flow_mask, receipt,
        config=config, seed=config["training"]["seed"],
    )
    view = ProtocolASourceView(arrays, transform)
    save_input_transform(output_root / "artifacts" / "sealed-input-transform.pkl", transform)

    reused_c00_source = optimizer_seal["runs"].get(sealed_optimizer_candidate)
    selections: dict[str, Any] = {}
    for cell in CELL_ORDER:
        identity = cell_identity(
            run_identity, input_candidate=sealed_input_candidate,
            optimizer_candidate=sealed_optimizer_candidate, cell=cell,
        )
        if cell == "C00" and reused_c00_source is not None and reused_c00_source.get("identity") == identity:
            source_root = (
                output_root / "selection-runs" / "select-input" / sealed_input_candidate
                if sealed_optimizer_candidate == input_seal["fixed_optimizer_candidate"]
                else output_root / "selection-runs" / "select-optimizer" / sealed_optimizer_candidate
            )
            selections[cell] = materialize_reused_cell(source_root, output_root, cell, identity)
            continue
        logger.info("开始 %s 协议 A 训练与选择（输入=%s，优化器=%s）", cell, sealed_input_candidate, sealed_optimizer_candidate)
        selections[cell] = train_cell(
            config, cell, sealed_input_candidate, sealed_optimizer_candidate,
            output_root=output_root, identity=identity, view=view,
            train_rows=train_rows, validation_rows=validation_rows, device=device, resume=args.resume,
        )

    cell_hashes: dict[str, Any] = {}
    optimizer_candidate_record = next(c for c in OPTIMIZER_CANDIDATES if c["key"] == sealed_optimizer_candidate)
    for cell in CELL_ORDER:
        selection = selections[cell]
        cell_hashes[cell] = {
            "checkpoint_sha256": selection["checkpoint"]["sha256"],
            "config_sha256": run_identity["config_sha256"],
            "code_sha256": run_identity["code_sha256"],
            "optimizer_candidate_sha256": _canonical_sha256(optimizer_candidate_record),
            "random_state": {"seed": config["training"]["seed"]},
            "elp_parameter_p_at_selection": selection["p_at_selection"],
            "aggregation_rule": (
                "32个成员sigmoid概率算术平均"
                + ("，再对唯一实体做共享标量p的可学幂平均池化(ELP)" if CELLS[cell]["learned_lp_pooling"] else "")
            ),
        }

    sample_order_sha256 = _canonical_sha256(
        {"train_rows": train_rows.tolist(), "validation_rows": validation_rows.tolist()}
    )
    seal = {
        "schema_version": "ch3-tabm32-selection-frozen-v1",
        "run_id": RUN_ID,
        "frozen_recipe_sha256": FROZEN_RECIPE_SHA256,
        "identity": run_identity,
        "input_candidates": list(INPUT_CANDIDATES),
        "optimizer_candidates": list(OPTIMIZER_CANDIDATES),
        "field_groups": config["field_groups"],
        "dijk_feature_count": DIJK_FEATURE_COUNT,
        "lspr23_flow_count": LSPR23_FLOW_COUNT,
        "source_data_inventory": source_inventory,
        "source_split": split_stats,
        "sample_order_sha256": sample_order_sha256,
        "cardinality_receipt_sha256": run_identity["cardinality_receipt_sha256"],
        "input_selection": input_seal,
        "optimizer_selection": optimizer_seal,
        "sealed_input_candidate": sealed_input_candidate,
        "sealed_optimizer_candidate": sealed_optimizer_candidate,
        "input_dimension": view.transform.output_dimension,
        "parameter_count": expected_parameter_count(view.transform.output_dimension),
        "cells": selections,
        "cell_hashes": cell_hashes,
        "all_four_cells_sealed": True,
        "target_year_arrays_read": 0,
        "target_evaluation_calls": 0,
        "sealed_at_unix": time.time(),
    }
    _atomic_json(selection_frozen_path, seal)
    write_status(output_root, "computed", "cells", 0, "四格训练与选择封印完成，等待目标年评价")
    logger.info("四格选择封印完成：%s", selection_frozen_path)


def run_evaluate_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """四格全部封印后的目标年评价：每格恰好评价一次，四格合计恰好 4 次。

    输入变换只应用已封印的训练区状态，绝不在 LSPR24 上重新拟合；评价阶段全程
    ``torch.no_grad()``，不训练、不替换检查点、不裁剪成员、不搜索阈值、
    不更新聚合指数或任何超参数。
    """
    output_root = Path(config["paths"]["output_root"])
    cache_root = Path(config["paths"]["cache_root"])
    selection_frozen_path = output_root / "selection_frozen.json"

    # 先做纯标准库的封印存在性核验，numpy/torch/sklearn 延后到确认要做真实评价
    # 工作之后才导入，使本阶段在缺依赖或尚未完成上游阶段的开发机上也能给出
    # 清晰的中文错误，而不是被导入失败掩盖真实原因。
    if not selection_frozen_path.is_file():
        raise RuntimeError(f"四格选择尚未封印，禁止加载 LSPR24：{selection_frozen_path}")
    seal = load_json(selection_frozen_path)
    if seal.get("all_four_cells_sealed") is not True or set(seal.get("cells", {})) != set(CELL_ORDER):
        raise RuntimeError("既有选择封印不完整，拒绝评价")

    aggregate_path = output_root / "aggregate-results.json"
    if aggregate_path.is_file():
        if not args.resume:
            raise RuntimeError(f"全新运行（未传 --resume）已存在聚合结果，拒绝覆盖：{aggregate_path}")
        logger.info("聚合结果已存在且传了 --resume，直接复用（不重新评价、不重新上报）：%s", aggregate_path)
        return

    import os
    import time

    import numpy as np
    import torch
    from sklearn.metrics import average_precision_score, roc_auc_score

    write_status(output_root, "running", "evaluate", None, "选择封印后首次加载 LSPR24，每格评价一次")

    device = _resolve_device()
    transform = load_input_transform(output_root / "artifacts" / "sealed-input-transform.pkl")
    _, profile, _ = resolve_precision_profile(device.type, torch)

    target_inventory = data_inventory(cache_root, TARGET_ARRAYS)
    target = load_target_arrays(str(cache_root))
    target_load_count = 1

    key = np.array(
        [
            left + "|" + right if left <= right else right + "|" + left
            for left, right in zip(target["s24"], target["d24"])
        ],
        dtype=object,
    )
    _, flow_entity = np.unique(key, return_inverse=True)
    entity_count = int(flow_entity.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, target["y24"])
    flow_positive_rate = float(target["y24"].astype(np.float64).mean())
    del key

    cells: dict[str, Any] = {}
    curve_arrays: dict[str, Any] = {}
    evaluation_calls_this_process = 0
    evaluation_receipts_reused = 0
    evaluation_started = time.time()
    evaluation_peak_gpu_mib = 0.0
    for cell in CELL_ORDER:
        checkpoint_path = output_root / seal["cells"][cell]["checkpoint"]["filename"]
        if seal["cells"][cell]["checkpoint"]["sha256"] != _sha256_file(checkpoint_path):
            raise RuntimeError(f"{cell} 选择检查点摘要与封印不符")
        target_identity = {
            **seal["identity"],
            "target_data_inventory_sha256": target_inventory["sha256"],
            "cell": cell,
            "checkpoint_sha256": seal["cells"][cell]["checkpoint"]["sha256"],
        }
        restored = load_target_evaluation(output_root, cell, target_identity)
        if restored is not None:
            cell_result, curve = restored
            cells[cell] = cell_result
            for field, values in curve.items():
                curve_arrays[f"{cell}__{field}"] = values
            evaluation_receipts_reused += 1
            logger.info("%s 复用身份与摘要匹配的目标评价完成收据", cell)
            continue

        model = build_model(config, cell, seal["sealed_input_candidate"], seal["input_dimension"], profile).to(device)
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model.load_state_dict(checkpoint["model"])
        model.to(device)
        selected_p = float(model.p.detach())
        if abs(selected_p - float(seal["cells"][cell]["p_at_selection"])) > 1e-9:
            raise RuntimeError(f"{cell} 回载后的共享 p 与选择封印不符")

        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        started = time.time()
        flow_scores, seen = score_target(config, model, transform, target, device, profile)
        evaluation_calls_this_process += 1
        evaluation_seconds = time.time() - started
        if device.type == "cuda":
            evaluation_peak_gpu_mib = max(evaluation_peak_gpu_mib, torch.cuda.max_memory_allocated(device) / 2**20)

        main_p = selected_p if CELLS[cell]["learned_lp_pooling"] else None
        main_entity_scores = entity_scores(flow_scores, seen, flow_entity, entity_count, main_p)
        maximum_entity_scores = entity_scores(flow_scores, seen, flow_entity, entity_count, None)
        valid_entity = np.isfinite(main_entity_scores)
        valid_maximum = np.isfinite(maximum_entity_scores)
        metrics = {
            "flow_average_precision": float(average_precision_score(target["y24"][seen], flow_scores[seen])),
            "flow_roc_auc": float(roc_auc_score(target["y24"][seen], flow_scores[seen])),
            "entity_average_precision": float(
                average_precision_score(entity_labels[valid_entity], main_entity_scores[valid_entity])
            ),
            "maximum_entity_average_precision": float(
                average_precision_score(entity_labels[valid_maximum], maximum_entity_scores[valid_maximum])
            ),
            "dr_at_fpr": {f"fpr_{value:g}": dr_at_fpr(main_entity_scores, entity_labels, value) for value in DR_FPR_GRID},
            "maximum_dr_at_fpr": {
                f"fpr_{value:g}": dr_at_fpr(maximum_entity_scores, entity_labels, value) for value in DR_FPR_GRID
            },
            "flows_scored": int(seen.sum()),
            "entities_scored": int(valid_entity.sum()),
            "evaluation_seconds": evaluation_seconds,
            "target_evaluation_call": CELL_ORDER.index(cell) + 1,
        }
        curve = complete_budget_curve(main_entity_scores, entity_labels)
        for field, values in curve.items():
            curve_arrays[f"{cell}__{field}"] = values
        cell_result = {
            "mechanisms": CELLS[cell],
            "selection": seal["cells"][cell],
            "selected_p": selected_p,
            "target": metrics,
        }
        save_target_evaluation(output_root, cell, target_identity, cell_result, curve)
        cells[cell] = cell_result
        logger.info(
            "%s 目标评价：逐流AP=%.8f 实体AP=%.8f",
            cell, metrics["flow_average_precision"], metrics["entity_average_precision"],
        )
        del model, checkpoint, flow_scores, seen, main_entity_scores, maximum_entity_scores
        if device.type == "cuda":
            torch.cuda.empty_cache()

    total_calls = evaluation_calls_this_process + evaluation_receipts_reused
    if len(cells) != 4 or total_calls != 4 or target_load_count != 1:
        raise RuntimeError(f"目标年加载或四格评价次数不符：cells={len(cells)} calls={total_calls} loads={target_load_count}")

    curve_path = output_root / "complete-alert-budget-curves.npz"
    temporary_curve = curve_path.with_name(f"{curve_path.name}.partial.{os.getpid()}")
    with temporary_curve.open("wb") as handle:
        np.savez_compressed(handle, **curve_arrays)
    os.replace(temporary_curve, curve_path)
    curve_receipt = {
        "schema_version": "ch3-tabm32-complete-alert-budget-curves-v1",
        "artifact": {"filename": curve_path.name, "bytes": curve_path.stat().st_size, "sha256": _sha256_file(curve_path)},
        "cells": list(CELL_ORDER),
        "fields": ["n_false_positive_entity", "nominal_fpr", "realized_fpr", "detection_rate"],
        "curve_is_complete_over_all_reachable_negative_entity_budgets": True,
        "per_flow_scores_persisted": False,
        "per_entity_scores_persisted": False,
    }
    _atomic_json(output_root / "complete-alert-budget-curves-receipt.json", curve_receipt)

    interaction: dict[str, Any] = {}
    for name in ("flow_average_precision", "entity_average_precision", "maximum_entity_average_precision"):
        values = {cell: cells[cell]["target"][name] for cell in CELL_ORDER}
        interaction[name] = {
            **values,
            "causal_prefix_effect": values["C10"] - values["C00"],
            "elp_effect": values["C01"] - values["C00"],
            "combined_effect": values["C11"] - values["C00"],
            "interaction": values["C11"] - values["C10"] - values["C01"] + values["C00"],
        }

    training_seconds_sum = sum(float(seal["cells"][cell]["training_seconds"]) for cell in CELL_ORDER)
    evaluation_seconds_sum = sum(float(cells[cell]["target"]["evaluation_seconds"]) for cell in CELL_ORDER)
    launcher_resource = load_json(Path(args.resource_receipt)) if args.resource_receipt else None
    peak_gpu_candidates = [evaluation_peak_gpu_mib] + [
        float(seal["cells"][cell]["peak_gpu_allocated_mib"] or 0.0) for cell in CELL_ORDER
    ]
    result = {
        "schema_version": "ch3-tabm32-paper-recipe-protocol-a-results-v1",
        "run_id": RUN_ID,
        "model": {
            "model_key": MODEL_KEY,
            "display_name": config["display_name"],
            **config["candidate"],
            "sealed_input_candidate": seal["sealed_input_candidate"],
            "sealed_optimizer_candidate": seal["sealed_optimizer_candidate"],
            "input_dimension": seal["input_dimension"],
            "parameter_count": seal["parameter_count"],
            "pytorch_version": torch.__version__,
        },
        "evidence": {
            "single_run_directly_comparable": True,
            "formal_paper_evidence": False,
            "target_previously_accessed": True,
            "independent_test": False,
            "target_metrics_used_for_selection_or_tuning": False,
        },
        "source_selection": {
            "split": seal["source_split"],
            "input_selection": seal["input_selection"],
            "optimizer_selection": seal["optimizer_selection"],
            "cells": seal["cells"],
        },
        "target_evaluation": {
            "dataset": "LSPR24",
            "flow_count": int(len(target["y24"])),
            "entity_count": entity_count,
            "positive_entity_count": int(entity_labels.sum()),
            "flow_positive_rate": flow_positive_rate,
            "cells": cells,
            "data_inventory": target_inventory,
        },
        "interaction": interaction,
        "isolation": {
            "all_four_selections_sealed_before_target_load": True,
            "target_disk_loads": target_load_count,
            "target_evaluation_calls": 4,
            "target_evaluation_calls_this_process": evaluation_calls_this_process,
            "target_evaluation_receipts_reused": evaluation_receipts_reused,
            "one_call_per_cell": True,
        },
        "artifact_policy": {
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "selected_checkpoints_persisted": 4,
            "complete_alert_budget_curve": curve_receipt,
        },
        "resource": {
            "parameter_count": seal["parameter_count"],
            "training_wall_seconds_sum": training_seconds_sum,
            "evaluation_wall_seconds_sum": evaluation_seconds_sum,
            "target_stage_wall_seconds": time.time() - evaluation_started,
            "peak_gpu_allocated_mib": max(peak_gpu_candidates),
            "peak_process_rss_mib": _process_peak_rss_mib(),
            "gpu_hours": (training_seconds_sum + evaluation_seconds_sum) / 3600.0,
            "launcher_admission_receipt": launcher_resource,
        },
    }
    _atomic_json(aggregate_path, result)
    write_status(output_root, "computed", "evaluate", 0, "四格目标评价完成，等待 SwanLab 上报")
    build_manifest(output_root, RUN_ID)
    publish_swanlab(config, result, output_root)
    write_status(output_root, "complete", "evaluate", 0, "四格结果、聚合指标与 SwanLab 上报均已完成")
    build_manifest(output_root, RUN_ID)
    logger.info("目标年评价与聚合完成：%s", aggregate_path)


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
