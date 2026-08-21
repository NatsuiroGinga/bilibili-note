# -*- coding: utf-8 -*-
"""TabM32 骨干专属论文配方协议 A 四格实验工具（任务 1 至 2）。

本文件目前实现：

- 任务 1：模块级冻结常量、配置校验 ``validate_config`` 与命令行入口的阶段分发骨架。
- 任务 2：字段基数收据消费 ``load_cardinality_receipt``、参数量闭式
  ``expected_parameter_count``，以及两个输入接口候选的拟合与应用
  ``fit_input_transform`` / ``InputTransform``。

``select-input``、``select-optimizer``、``cells``、``evaluate`` 四个阶段的训练与
评价逻辑将由后续任务（骨干、训练循环、断点恢复、封印与评价、启动器）继续叠加，
本文件只为它们预留分发位置，不预先实现。

按仓库规则，numpy、scikit-learn 与 torch 的导入一律延迟到真正需要它们的函数内部：
``--validate-config`` 只做纯 Python 字典/字符串比对，不应因为本机 ``.venv`` 缺少
这些依赖而失败。模块顶层因此只导入
``argparse``、``json``、``logging``、``sys``、``pathlib``、``typing``。
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

    training = config["training"]
    micro_batch = config["candidate"]["micro_batch_sequences"]
    dense_bytes = micro_batch * training["sequence_length"] * output_dimension * 4
    projection = {
        "candidate_key": candidate_key,
        "output_dimension": output_dimension,
        "vocabulary_widths": vocabulary_widths,
        "parameter_count": expected_parameter_count(output_dimension),
        "micro_batch_dense_input_bytes": dense_bytes,
    }
    logger.info(
        "输入维预算 %s：输出维=%d，参数量=%d，单微批稠密输入=%.2f MiB",
        candidate_key, output_dimension, projection["parameter_count"], dense_bytes / 1024 / 1024,
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
            output[:, offset + slot] = (column == np.float32(self.boolean_true_values[slot])).astype(np.float32)
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

    vocabularies: list[tuple[float, ...]] = []
    categorical_indices: list[int] = []
    boolean_indices: list[int] = []
    boolean_true_values: list[float] = []
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
            logger.info("布尔字段 %s 映射：max=%s 记为 1，其余记为 0", name, entry["max"])

    output_dimension = len(numeric_indices) + sum(len(v) + 1 for v in vocabularies) + len(boolean_indices)
    if output_dimension != projection["output_dimension"]:
        raise RuntimeError(
            f"实测输出维 {output_dimension} 与收据预算 {projection['output_dimension']} 不符"
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
            name: {"dijk_feature_index": index, "true_value": value}
            for name, index, value in zip(boolean_names, boolean_indices, boolean_true_values, strict=True)
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
