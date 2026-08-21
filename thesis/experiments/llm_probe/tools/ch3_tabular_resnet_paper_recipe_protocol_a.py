# -*- coding: utf-8 -*-
"""全容量表格 ResNet（表格预归一化残差多层感知机）骨干专属论文配方协议 A 四格工具。

本工具实现 N-14 冻结实施计划
``.Codex/docs/RWKV/2026-08-21-全容量表格ResNet骨干协议A实施计划.md`` 的四个生产阶段：

- ``select-input``：在 LSPR23 C00 上比较冻结的两个输入候选，封印唯一输入接口。
- ``select-optimizer``：在已封印输入上比较两个优化器候选，封印唯一优化器。
- ``cells``：以封印的输入与优化器训练协议 A 四格 ``C00/C01/C10/C11`` 并写选择封印。
- ``evaluate``：四格全部封印后加载 LSPR24，每格恰好评价一次，合计恰好 4 次。

冻结结构（实施计划第四节，逐条照办，不得增改）：

    输入投影 Linear(83→192)
    两个残差块，每块 LayerNorm → Linear(192→384) → ReLU → Dropout(0.15)
                     → Linear(384→192) → Dropout(0) → 残差相加
    CPA 打开时拼接 192 维当前表示与 192 维因果上下文，
        经 Linear(384→192) → ReLU → Dropout(0.1)
    输出头 Linear(192→1)；ELP 分支含一个 FP32 p_log

可训练参数量恒为 ``387,074``，由闭式、冻结配置登记值与实际
``sum(p.numel() for p in model.parameters() if p.requires_grad)`` 三方比对，
任一不等立即抛错。禁止增加块数、宽度扫描、注意力、门控、多尺度、分段线性编码、
端口嵌入或额外归一化层。

``LayerNorm`` 替代 Gorishniy 2021 原论文的 ``BatchNorm``，是本课题因果序列与补零
安全的**任务适配**，不是论文原配方；该偏离在配置、封印与实施报告中均显式登记。

精度合同：本运行走 RTX 5090 神经训练默认配置 ``cuda-bf16-amp-fp32-sensitive-v1``
（BF16 autocast、参数与优化器状态保持 FP32、敏感计算进 FP32 岛、不用 GradScaler），
经 ``tools/neural_precision_runtime.py`` 接入，不自建第二套精度、累积或收据实现。

按仓库规则，numpy、scikit-learn 与 torch 的导入一律延迟到真正需要它们的函数内部：
``--validate-config`` 只做纯 Python 字典/字符串比对与纯标准库的精度合同校验，
不应因为本机 ``.venv`` 缺少这些依赖而失败。模块顶层因此只导入
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

# 允许以 `python tools/ch3_tabular_resnet_paper_recipe_protocol_a.py` 之外的方式调用时
# 仍能找到同目录的 neural_precision_runtime，与仓库既有工具同一写法。
TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

# ---------------------------------------------------------------------------
# 运行身份与协议 A 冻结常量
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "ch3-tabular-resnet-paper-recipe-protocol-a-config-v1"
RUN_ID = "ch3-tabular-resnet-paper-recipe-protocol-a-seed42-v1"
MODEL_KEY = "tabular-resnet-paper-recipe"
DISPLAY_NAME = "表格预归一化残差多层感知机骨干专属论文配方协议A四格"

# 冻结配方文件 `.Codex/docs/RWKV/2026-08-20-骨干专属论文配方冻结/骨干专属论文配方冻结.md`
# 的实测 SHA-256（2026-08-21 本机 `shasum -a 256` 实测）。本模块只做字符串比对，
# 不重新计算冻结配方文件本身的哈希——那是启动器与人工核验的职责。
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

# 命令行 --stage 的合法取值。四个阶段全部为生产实现：任一阶段都不得留成只抛「未实现」
# 的骨架，也不得以函数存在冒充实现完成。这里刻意不写出该异常类名，以免机械扫描把本行
# 注释误报成残留骨架。
STAGE_CHOICES: tuple[str, ...] = ("select-input", "select-optimizer", "cells", "evaluate")

# ---------------------------------------------------------------------------
# 输入接口候选（实施计划第三节冻结顺序）
# ---------------------------------------------------------------------------

# 候选一 `standardized-83`：直接复用冻结 83 字段的现有标准化数值视图。X23.npy 存的
# 是**标准化浮点**（不是原始端口号，七字段 integer_like 全为 False），因此本候选是
# 该视图的等值透传，只对缺失值按训练区口径补零并计数——补零后的 0 恰好是标准化后的
# 训练区均值，与「缺失补零只由 LSPR23 训练区拟合」一致。七字段的 missing_fraction
# 实测全为 0，故正常情况下补零计数恒为 0，透传与原视图逐位相同。
#
# 候选二 `source-quantile-83`：只对 76 个连续与计数字段在 LSPR23 训练区拟合分位数
# 规范化；端口、协议与二元粗拓扑七字段一律不参与拟合、原值透传。输出维仍为 83，
# 因此两候选的参数量同为 387,074，比较只反映数值变换差异，不混入容量差异。
#
# 候选二受「仅在有全文或官方依据支持时比较」的准入条件约束，其准入判定由
# `resolve_quantile_policy` 依据冻结配置中逐项可追溯的证据串机械裁定，
# 证据不全时该候选停用并写入原因，不得以任何猜测数值补齐。
INPUT_CANDIDATE_STANDARDIZED = "standardized-83"
INPUT_CANDIDATE_SOURCE_QUANTILE = "source-quantile-83"

INPUT_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "order": 1,
        "display_name": "表格ResNet-冻结83字段标准化数值输入",
        "key": INPUT_CANDIDATE_STANDARDIZED,
        "numeric_transform": "frozen_training_region_standardized_passthrough",
        "special_field_treatment": "ports_protocols_and_coarse_topology_keep_frozen_standardized_values",
        "missing_policy": "training_region_zero_fill_with_absorption_count",
        "input_dimension": 83,
        "parameter_count": 387074,
        "requires_admission_evidence": False,
    },
    {
        "order": 2,
        "display_name": "表格ResNet-训练区分位数规范化连续与计数字段输入",
        "key": INPUT_CANDIDATE_SOURCE_QUANTILE,
        "numeric_transform": "lspr23_training_region_quantile_normalization_on_continuous_and_count_fields_only",
        "special_field_treatment": "ports_protocols_and_coarse_topology_excluded_from_quantile_fit_and_passed_through",
        "missing_policy": "training_region_zero_fill_with_absorption_count",
        "input_dimension": 83,
        "parameter_count": 387074,
        "requires_admission_evidence": True,
    },
)

# ---------------------------------------------------------------------------
# 优化器候选（实施计划第五节 = 冻结配方 3.5 节，逐字复用内部短键）
# ---------------------------------------------------------------------------

OPTIMIZER_CANDIDATE_LOGMID = "resmlp-paper-logmid"
OPTIMIZER_CANDIDATE_LOGQ75 = "resmlp-paper-logq75"

OPTIMIZER_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "order": 1,
        "display_name": "表格残差多层感知机-论文对数中位学习率",
        "key": OPTIMIZER_CANDIDATE_LOGMID,
        "optimizer": "adamw",
        "learning_rate": 0.00031622776601683794,
        "weight_decay": 0.0,
    },
    {
        "order": 2,
        "display_name": "表格残差多层感知机-论文高四分位学习率",
        "key": OPTIMIZER_CANDIDATE_LOGQ75,
        "optimizer": "adamw",
        "learning_rate": 0.0017782794100389228,
        "weight_decay": 0.0,
    },
)

# ---------------------------------------------------------------------------
# 精度合同接入常量（2026-08-21 Codex 裁定的 RTX 5090 神经训练默认配置）
# ---------------------------------------------------------------------------

# 依据：thesis/experiments/llm_probe/AGENTS.md「PyTorch 训练与显存」条，
# 合同定义见 configs/neural-precision-profiles-v1.json，运行时实现见
# tools/neural_precision_runtime.py。本运行不走 FP32 或 FP16 例外。
PRECISION_PROFILE_ID = "cuda-bf16-amp-fp32-sensitive-v1"
PRECISION_CONTRACT_FILENAME = "neural-precision-profiles-v1.json"

# 有效批的对象单位是序列，损失归一化单位是流。
EFFECTIVE_BATCH_ITEM_UNIT = "sequence"
NORMALIZATION_UNIT = "flow"

# 各计算类型的元素字节数，用于按精度合同而不是写死 4 字节来预算展开张量。
PRECISION_DTYPE_BYTES: dict[str, int] = {"bfloat16": 2, "float16": 2, "float32": 4}

# 主机侧 InputTransform.apply 的输出恒为 float32，与设备端计算类型无关。
HOST_FEATURE_DTYPE_BYTES = 4

# 与既有协议 A 工具逐字一致的源年形状身份，供训练前机械断言。
LSPR23_SEQUENCE_COUNT = 271_815
LSPR23_FLOW_COUNT = 16_353_511
DIJK_FEATURE_COUNT = 83
PROTOCOL_A_SEQUENCE_LENGTH = 128
PROTOCOL_A_SPLIT_STATISTICS: dict[str, int] = {
    "entity_count": 150_680,
    "train_sequences": 208_598,
    "validation_sequences": 22_444,
    "train_validation_row_intersection": 0,
}

# ---------------------------------------------------------------------------
# 冻结结构常量（实施计划第四节）
# ---------------------------------------------------------------------------

MAIN_WIDTH = 192
HIDDEN_WIDTH = 384
HIDDEN_FACTOR = 2.0
RESIDUAL_BLOCK_COUNT = 2
HIDDEN_DROPOUT = 0.15
RESIDUAL_DROPOUT = 0.0
FUSION_DROPOUT = 0.1
EXPECTED_PARAMETER_COUNT = 387_074

# 实施计划第四节第 6 条逐项登记的参数量分解，供闭式与逐层展开互相核对。
EXPECTED_PARAMETER_DECOMPOSITION: dict[str, int] = {
    "input_projection": 16_128,
    "residual_blocks": 296_832,
    "causal_prefix_fusion": 73_920,
    "output_head_and_p_log": 194,
}

# 机制常量，与既有协议 A 四格工具逐字同值，保证跨骨干指标可并表。
MECHANISM_ELP_INITIAL_P = 2.0
MECHANISM_ELP_P_MINIMUM = 1e-3
MECHANISM_ELP_P_MAXIMUM = 1e3
MECHANISM_ELP_PROBABILITY_FLOOR = 1e-7
MECHANISM_ELP_POOLED_CLAMP = 1e-6

# 前向张量的轴约定：0 批、1 时间、2 特征。因果前缀聚合只沿时间轴累积。
BATCH_AXIS = 0
TIME_AXIS = 1
FEATURE_AXIS = 2

# ---------------------------------------------------------------------------
# 微批冻结（与 N-13 同一机械规则，不继承 N-12 的批量数值）
# ---------------------------------------------------------------------------

# 有效批 64 序列是协议 A 的跨骨干共同预算，由协议而非本工具决定，不参与搜索。
PROTOCOL_A_EFFECTIVE_BATCH_SEQUENCES = 64
# 微批只能取有效批的机械因子（精度合同 microbatch_factor_rule）。
# 选择规则：在全部因子中取「单微批前向保留激活的解析上界」不超过天花板的最大者。
# 天花板取 GPU 准入阈值的十分之一（20480 / 10 = 2048 MiB）。十分之一这个工程余量
# 的依据是本结构的三项同量级放大：LayerNorm 与因果前缀累积走 FP32 岛因而同时存在
# FP32 与计算类型两份张量、反向为每层保留与前向同量级的梯度缓冲、缓存分配器碎片。
# 该数值是工程资源余量而非科研阈值，服务器第一次真实 optimizer.step() 的显存收据
# 到手后必须复核并可修订。
MICROBATCH_CEILING_DIVISOR = 10

# Codex 先例裁定的 GPU 空闲显存准入阈值（MiB），与 N-12、N-13 同值。
GPU_FREE_MEMORY_MINIMUM_MIB = 20480

# ---------------------------------------------------------------------------
# 分位数候选的准入证据（实施计划第三节「仅在有全文或官方依据支持时比较」）
# ---------------------------------------------------------------------------

# 候选二必须逐项封印的分位数策略键。每一项在冻结配置的
# `quantile_policy` 下都必须同时给出 `value` 与非空 `source`；任一项 `value` 为
# null 或 `source` 为空即视为未封印，候选二停用并把缺项写进封印收据。
#
# 已核验证据（2026-08-21 本机 pdftotext 逐页核对原件
# raw/papers/methodology/2021-Gorishniy-Revisiting-Deep-Learning-Tabular-Data.pdf，
# SHA-256 f2faa32ffd8c15ed8534677f978dc02730fdbe1f94e9c9557ada6aa19163478d）：
#
# - 物理页 6，§4.3「Data preprocessing」：默认使用 scikit-learn 的分位数变换。
# - 物理页 14，附录 B.2：拟合分位数前对训练区数值特征叠加 N(0, 1e-3) 噪声，
#   作为「取值种类很少」的特征的变通，并注明精确实现见源码。
#
# 未核验项：`output_distribution`、`n_quantiles`、`subsample` 三个 scikit-learn
# 形参在论文正文与附录中都没有出现，只能取自官方 `lib/data.py`；本仓库归档的
# rtdl 快照（vendor/ft_transformer/）只含 `bin/ft_transformer.py`，不含预处理代码，
# 因此这三项当前无法封印。**不得**用同组作者后续 TabM 仓库的 NOISY_QUANTILE 数值
# （output_distribution="normal"、n // 30 地标、subsample=1e9、噪声 1e-5）顶替：
# 那是另一篇论文另一份源码的口径，噪声标准差与本论文的 1e-3 已经不同，
# 凭它推断本论文其余形参属于跨来源臆断。
QUANTILE_POLICY_KEYS: tuple[str, ...] = (
    "noise_standard_deviation",
    "output_distribution",
    "n_quantiles",
    "subsample",
)

# 分位数拟合时的单次噪声抽取元素数，只为把 float64 临时缓冲限制在 32 MiB 以内；
# 逐块抽取与一次性抽取的随机流分配方式相同，不改变每元素的分布。
QUANTILE_NOISE_CHUNK_ELEMENTS = 4_194_304

# 组装式变换器的实现漂移绊线，不是科学阈值。推导：地标数为 n 时中位数附近一格地标
# 的概率间距为 1/(n-1)；标准正态分位函数在 p=0.5 处斜率为 sqrt(2*pi)≈2.5066，
# 故 n=1000 时插值位移的解析上界约 2.5e-3。下列容差约为该上界的 40 倍，
# 只在 scikit-learn 行为实质改变时触发。该自检只在 output_distribution 为
# "normal" 时有意义，其他分布下跳过并记录。
QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE = 0.1

# 字段基数收据身份，与 tools/ch3_lspr23_field_cardinality_receipt.py 一致。
CARDINALITY_RECEIPT_SCHEMA_VERSION = "ch3-lspr23-field-cardinality-receipt-v1"
CARDINALITY_RECEIPT_RUN_ID = "ch3-lspr23-field-cardinality-receipt-v1"

# ---------------------------------------------------------------------------
# validate_config 内部使用的冻结期望值（不对外导出，只服务该函数）
# ---------------------------------------------------------------------------

# 字段分组与收据消费口径必须与 N-12/N-13 完全一致：它决定收据里有哪些字段、
# 以什么顺序出现。本骨干的扁平数值视图不对这七个字段做独热，但仍必须显式登记
# 分组，使「哪些字段不参与分位数拟合」可机械追溯（Codex 提交 956abcb 裁定）。
_EXPECTED_FIELD_GROUPS: dict[str, Any] = {
    "categorical": ["SrcPort", "DstPort", "Protocol", "L3/L4 Protocol", "Int/Ext Dst IP"],
    "boolean": ["External_src", "External_dst"],
    "numeric_count": 76,
    "total_count": 83,
}

_EXPECTED_ARCHITECTURE: dict[str, Any] = {
    "input_dimension": DIJK_FEATURE_COUNT,
    "main_width": MAIN_WIDTH,
    "hidden_width": HIDDEN_WIDTH,
    "hidden_factor": HIDDEN_FACTOR,
    "residual_blocks": RESIDUAL_BLOCK_COUNT,
    "block_order": "layer_norm_linear_relu_dropout_linear_dropout_add",
    "normalization": "per_token_layer_norm",
    "normalization_deviates_from_paper_batch_norm": True,
    "normalization_deviation_note": (
        "Gorishniy 2021 物理页3公式2 的残差块首层为 BatchNorm；本任务改用逐标记 LayerNorm，"
        "理由是批统计会让序列内某一标记依赖同批其他标记并可能混入当前时刻之后的输入，"
        "破坏前向因果与补零独立。该替换是本课题任务适配，不得写成论文原配方"
    ),
    "activation": "relu",
    "hidden_dropout": HIDDEN_DROPOUT,
    "residual_dropout": RESIDUAL_DROPOUT,
    "causal_prefix_fusion": "concat_hidden_and_causal_context_then_linear_2d_to_d_relu_dropout",
    "fusion_dropout": FUSION_DROPOUT,
    "output_head": "linear_d_to_1",
    "elp_exponent": "shared_scalar_fp32_p_log",
    "additional_normalization_layers": False,
    "attention": False,
    "gating": False,
    "multi_scale": False,
    "piecewise_linear_encoding": False,
    "port_embedding": False,
    "parameter_formula": (
        "d_in*d+d + B*(2*d + d*h+h + h*d+d) + (2*d*d+d) + (d+1) + 1"
    ),
    "parameter_count": EXPECTED_PARAMETER_COUNT,
}

_EXPECTED_TRAINING: dict[str, Any] = {
    "seed": 42,
    "sequence_length": PROTOCOL_A_SEQUENCE_LENGTH,
    "effective_batch_size": PROTOCOL_A_EFFECTIVE_BATCH_SEQUENCES,
    "micro_batch_sequences": 64,
    "gradient_accumulation_steps": 1,
    "microbatch_activation_ceiling_mib": GPU_FREE_MEMORY_MINIMUM_MIB // MICROBATCH_CEILING_DIVISOR,
    "effective_batch_item_unit": EFFECTIVE_BATCH_ITEM_UNIT,
    "normalization_unit": NORMALIZATION_UNIT,
    "epochs": 20,
    "steps_per_epoch": 1000,
    "gradient_clip_norm": 1.0,
    "auxiliary_loss_weight": 1.0,
    "validation_fraction": 0.1,
    "time_tail_fraction": 0.15,
    "learning_rate_schedule": "none",
    "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
    "selection_rule": "single_epoch_argmax_earliest_tie_no_early_stopping",
    "stopping_rule_deviates_from_frozen_recipe": True,
    "stopping_rule_deviation_note": (
        "冻结配方3.4节停止行为耐心16无轮数上限；本运行取协议A的20轮跑满不早停，"
        "以保持四格与跨骨干可比性"
    ),
}

_EXPECTED_SELECTION_STAGES: dict[str, Any] = {
    "stage_one_input_interface": [
        INPUT_CANDIDATE_STANDARDIZED,
        INPUT_CANDIDATE_SOURCE_QUANTILE,
    ],
    "stage_one_fixed_optimizer": OPTIMIZER_CANDIDATE_LOGMID,
    "stage_two_optimizer": [OPTIMIZER_CANDIDATE_LOGMID, OPTIMIZER_CANDIDATE_LOGQ75],
    "stage_two_uses_sealed_input": True,
    "tie_break": "fixed_table_order",
    "forbidden_tie_breakers": ["entity_ap", "alert_budget", "training_time", "gpu_memory", "lspr24"],
    "no_cartesian_expansion_of_input_and_optimizer": True,
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
    "report_realized_fpr_beside_every_nominal_working_point": True,
}

_EXPECTED_ARTIFACT_POLICY: dict[str, Any] = {
    "persist_selected_checkpoint_per_cell": True,
    "persist_inflight_epoch_checkpoint": True,
    "persist_per_flow_scores": False,
    "persist_per_entity_scores": False,
    "persist_complete_budget_curve_aggregate": True,
}

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
    "tags": [
        "chapter3",
        "tabular-resnet",
        "paper-recipe",
        "protocol-a",
        "2x2",
        "seed42",
        "single-run",
    ],
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
            f"精度合同默认配置为 {contract['default_profile']}，"
            f"与本运行冻结的 {PRECISION_PROFILE_ID} 不符"
        )
    return contract


def resolve_precision_profile(
    device_type: str, torch_module: Any, contract: dict[str, Any] | None = None
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """核验真实设备能力后返回 ``(合同, 精度配置, 配置标识)``。

    ``profile_for_device`` 只在非 CUDA 设备上返回回退标识；CUDA 无 BF16 时不静默降级，
    而是由 ``validate_runtime_profile`` 抛错，要求显式改走 FP16 回退并留硬件收据。
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


def compute_torch_dtype(profile: dict[str, Any], torch_module: Any) -> Any:
    """把精度合同登记的 ``compute_dtype`` 字符串映射为 ``torch.dtype``。"""
    dtype_name = profile["compute_dtype"]
    if dtype_name not in PRECISION_DTYPE_BYTES:
        raise ValueError(f"精度配置登记了未核验的计算类型：{dtype_name}")
    return getattr(torch_module, dtype_name)


# ---------------------------------------------------------------------------
# 张量上界与微批冻结
# ---------------------------------------------------------------------------


def retained_activation_bytes(
    micro_batch: int, sequence_length: int, element_bytes: int
) -> int:
    """单微批训练前向为反向保留的激活字节数解析上界，按展开维度乘积逐项相加。

    逐项构成（``flows = micro_batch × sequence_length``，``d=192``，``h=384``）：

    - 输入投影输出并掩码：``flows × d`` 个计算类型元素；
    - 每个残差块四项：LayerNorm 输出走 FP32（见 ``TabularResNetBackbone.forward``
      的核验说明）故按 ``flows × d`` 个 FP32 元素记；首线性、ReLU 与隐藏随机失活
      各 ``flows × h`` 个计算类型元素；次线性、残差随机失活与残差相加各
      ``flows × d`` 个计算类型元素；
    - 因果前缀累积在 FP32 岛内完成，同时存在 ``hidden32`` 与 ``context32`` 两份
      ``flows × d`` 个 FP32 元素；
    - 拼接张量 ``flows × 2d``、融合线性、ReLU 与融合随机失活各 ``flows × d``，
      输出头 ``flows × 1``，均按计算类型记。

    这是**前向保留**的上界，不含反向自身的梯度缓冲与缓存分配器碎片；
    微批选择的天花板已按这些同量级放大留出余量。
    """
    flows = micro_batch * sequence_length
    per_block = (
        flows * MAIN_WIDTH * HOST_FEATURE_DTYPE_BYTES  # LayerNorm 输出（FP32）
        + 3 * flows * HIDDEN_WIDTH * element_bytes  # 首线性、ReLU、隐藏随机失活
        + 3 * flows * MAIN_WIDTH * element_bytes  # 次线性、残差随机失活、残差相加
    )
    return (
        flows * MAIN_WIDTH * element_bytes
        + RESIDUAL_BLOCK_COUNT * per_block
        + 2 * flows * MAIN_WIDTH * HOST_FEATURE_DTYPE_BYTES  # 因果前缀 FP32 岛两份
        + flows * 2 * MAIN_WIDTH * element_bytes  # 拼接
        + 3 * flows * MAIN_WIDTH * element_bytes  # 融合线性、ReLU、融合随机失活
        + flows * element_bytes  # 输出头
    )


def tensor_upper_bounds(config: dict[str, Any], profile: dict[str, Any]) -> dict[str, int]:
    """按真实展开维度乘积给出单微批张量上界，不按参数量估算。"""
    training = config["training"]
    micro_batch = training["micro_batch_sequences"]
    length = training["sequence_length"]
    element_bytes = compute_dtype_bytes(profile)
    flows = micro_batch * length
    return {
        "micro_batch_flows": flows,
        "micro_batch_host_dense_input_bytes": flows * DIJK_FEATURE_COUNT * HOST_FEATURE_DTYPE_BYTES,
        "hidden_tensor_bytes": flows * MAIN_WIDTH * element_bytes,
        "hidden_tensor_fp32_bytes": flows * MAIN_WIDTH * HOST_FEATURE_DTYPE_BYTES,
        "block_hidden_expansion_bytes": flows * HIDDEN_WIDTH * element_bytes,
        "causal_prefix_concat_bytes": flows * 2 * MAIN_WIDTH * element_bytes,
        "causal_prefix_fp32_island_bytes": 2 * flows * MAIN_WIDTH * HOST_FEATURE_DTYPE_BYTES,
        "retained_activation_bytes": retained_activation_bytes(micro_batch, length, element_bytes),
        "compute_dtype_bytes": element_bytes,
    }


def mechanical_factors(value: int) -> tuple[int, ...]:
    """返回 ``value`` 的全部正因子，升序；微批只能取有效批的机械因子。"""
    if value <= 0:
        raise ValueError(f"有效批必须为正整数，实际 {value}")
    return tuple(factor for factor in range(1, value + 1) if value % factor == 0)


def freeze_microbatch_plan(config: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """按解析张量上界在有效批的机械因子中冻结微批与累积步数。

    规则：取使 ``retained_activation_bytes`` 不超过
    ``minimum_free_gpu_memory_mib / MICROBATCH_CEILING_DIVISOR`` 的**最大**机械因子。
    有效批本身由协议 A 的跨骨干共同预算决定，不参与搜索。本函数不读数据、不建目录、
    不导入 numpy 或 torch，因此 ``--validate-config`` 也能复算并核对冻结值。
    """
    training = config["training"]
    effective_batch = training["effective_batch_size"]
    if effective_batch != PROTOCOL_A_EFFECTIVE_BATCH_SEQUENCES:
        raise ValueError(
            f"有效批必须为协议 A 的跨骨干共同预算 {PROTOCOL_A_EFFECTIVE_BATCH_SEQUENCES} 序列，"
            f"实际 {effective_batch}"
        )
    admission_mib = config["resource_contract"]["minimum_free_gpu_memory_mib"]
    ceiling_mib = admission_mib // MICROBATCH_CEILING_DIVISOR
    if ceiling_mib != training["microbatch_activation_ceiling_mib"]:
        raise ValueError(
            f"training.microbatch_activation_ceiling_mib 必须等于准入阈值 {admission_mib} "
            f"除以 {MICROBATCH_CEILING_DIVISOR} 得到的 {ceiling_mib}"
        )
    element_bytes = compute_dtype_bytes(profile)
    length = training["sequence_length"]
    trace: list[dict[str, Any]] = []
    chosen: int | None = None
    for factor in mechanical_factors(effective_batch):
        activation_mib = retained_activation_bytes(factor, length, element_bytes) / 2**20
        feasible = activation_mib <= ceiling_mib
        trace.append(
            {
                "micro_batch_sequences": factor,
                "retained_activation_mib": activation_mib,
                "feasible": feasible,
            }
        )
        if feasible:
            chosen = factor
    if chosen is None:
        raise RuntimeError(
            f"有效批 {effective_batch} 的任何机械因子都超过激活天花板 {ceiling_mib} MiB，"
            "须先重议准入阈值或结构，不得静默放宽"
        )
    return {
        "effective_batch_size": effective_batch,
        "effective_batch_item_unit": EFFECTIVE_BATCH_ITEM_UNIT,
        "normalization_unit": NORMALIZATION_UNIT,
        "micro_batch_sequences": chosen,
        "gradient_accumulation_steps": effective_batch // chosen,
        "activation_ceiling_mib": ceiling_mib,
        "gpu_admission_floor_mib": admission_mib,
        "ceiling_divisor": MICROBATCH_CEILING_DIVISOR,
        "selection_rule": "largest_mechanical_factor_within_analytic_activation_ceiling",
        "selection_trace": trace,
        "independently_frozen_by_this_tool": True,
        "inherits_other_backbone_values": False,
        "revisit_after_first_step_memory_receipt": True,
    }


# ---------------------------------------------------------------------------
# 参数量闭式与逐层展开
# ---------------------------------------------------------------------------


def input_projection_parameter_count(input_dimension: int, main_width: int) -> int:
    """输入投影 ``Linear(d_in, d)``：``d_in*d + d``。"""
    return input_dimension * main_width + main_width


def residual_block_parameter_count(main_width: int, hidden_width: int) -> int:
    """单个残差块：``LayerNorm(d)`` 加 ``Linear(d,h)`` 加 ``Linear(h,d)``。

    ``LayerNorm`` 含权重与偏置共 ``2d``；两个随机失活层无参数；残差相加无参数。
    """
    return (
        2 * main_width
        + main_width * hidden_width + hidden_width
        + hidden_width * main_width + main_width
    )


def causal_prefix_fusion_parameter_count(main_width: int) -> int:
    """因果前缀融合 ``Linear(2d, d)``：``2*d*d + d``。ReLU 与随机失活无参数。"""
    return 2 * main_width * main_width + main_width


def output_head_parameter_count(main_width: int) -> int:
    """输出头 ``Linear(d, 1)`` 加共享标量 ``p_log``：``d + 1 + 1``。"""
    return main_width + 1 + 1


def parameter_count_decomposition(
    input_dimension: int = DIJK_FEATURE_COUNT,
    main_width: int = MAIN_WIDTH,
    hidden_width: int = HIDDEN_WIDTH,
    residual_blocks: int = RESIDUAL_BLOCK_COUNT,
) -> dict[str, int]:
    """逐项展开的可训练参数量，键名与实施计划第四节第 6 条逐字对应。"""
    return {
        "input_projection": input_projection_parameter_count(input_dimension, main_width),
        "residual_blocks": residual_blocks
        * residual_block_parameter_count(main_width, hidden_width),
        "causal_prefix_fusion": causal_prefix_fusion_parameter_count(main_width),
        "output_head_and_p_log": output_head_parameter_count(main_width),
    }


def expected_parameter_count(
    input_dimension: int = DIJK_FEATURE_COUNT,
    main_width: int = MAIN_WIDTH,
    hidden_width: int = HIDDEN_WIDTH,
    residual_blocks: int = RESIDUAL_BLOCK_COUNT,
) -> int:
    """闭式可训练参数量：逐项分解之和。

    冻结配置下 ``d_in=83、d=192、h=384、B=2`` 时应恰为 ``387,074``；
    该值由 ``validate_config`` 与 ``build_model`` 分别机械核验。
    """
    return sum(
        parameter_count_decomposition(
            input_dimension, main_width, hidden_width, residual_blocks
        ).values()
    )


# ---------------------------------------------------------------------------
# 配置校验
# ---------------------------------------------------------------------------


def _validate_quantile_policy_shape(config: dict[str, Any]) -> None:
    """只核验 ``quantile_policy`` 的结构，不裁定候选二是否准入。

    准入裁定由 ``resolve_quantile_policy`` 在真正需要候选二时执行；本函数保证
    每个策略键都存在且形如 ``{"value": ..., "source": ...}``，使
    ``--validate-config`` 能在无依赖开发机上暴露结构性缺陷。
    """
    policy = config.get("quantile_policy")
    if not isinstance(policy, dict):
        raise ValueError("配置缺少 quantile_policy 对象（候选二的分位数策略台账）")
    if list(policy.keys()) != list(QUANTILE_POLICY_KEYS):
        raise ValueError(
            f"quantile_policy 的键集合或顺序不符，期望 {list(QUANTILE_POLICY_KEYS)}，"
            f"实际 {list(policy.keys())}"
        )
    for key in QUANTILE_POLICY_KEYS:
        entry = policy[key]
        if not isinstance(entry, dict) or set(entry.keys()) != {"value", "source"}:
            raise ValueError(
                f"quantile_policy.{key} 必须是恰含 value 与 source 两键的对象，"
                "缺证据的项把 value 与 source 一并置为 null"
            )
        has_value = entry["value"] is not None
        has_source = isinstance(entry["source"], str) and bool(entry["source"].strip())
        if has_value != has_source:
            raise ValueError(
                f"quantile_policy.{key} 的 value 与 source 必须同时存在或同时为 null："
                "有值无依据属于魔法数字，有依据无值属于登记不全"
            )


def validate_config(config: dict[str, Any]) -> None:
    """核验冻结 JSON 配置是否严格等于协议 A 的冻结身份与合同。

    只做纯 Python 字典/字符串比对与纯标准库的精度合同校验，不读取磁盘上的冻结配方
    文件、不联网、不建运行目录；每项不符都抛出带中文原因的 ``ValueError``。
    """
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version 与冻结模式版本不符")
    if config.get("model_key") != MODEL_KEY or config.get("run_id") != RUN_ID:
        raise ValueError("model_key 或 run_id 运行身份不符")
    if config.get("display_name") != DISPLAY_NAME:
        raise ValueError("display_name 与冻结展示名不符；纯字母数字代号不得作为唯一名称")
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
    if config.get("input_candidates") != [dict(entry) for entry in INPUT_CANDIDATES]:
        raise ValueError("input_candidates 与冻结输入候选定义不符")

    frozen_optimizers = [dict(entry) for entry in OPTIMIZER_CANDIDATES]
    configured_optimizers = config.get("optimizer_candidates")
    if not isinstance(configured_optimizers, list) or len(configured_optimizers) != len(
        frozen_optimizers
    ):
        raise ValueError("optimizer_candidates 数量与冻结优化器候选不符")
    for configured, frozen in zip(configured_optimizers, frozen_optimizers):
        for key, expected_value in frozen.items():
            if configured.get(key) != expected_value:
                raise ValueError(f"optimizer_candidates 的 {frozen['key']}.{key} 与冻结值不符")
        if not isinstance(configured.get("source"), str) or not configured["source"].strip():
            raise ValueError(f"optimizer_candidates 的 {frozen['key']} 缺少可追溯的 source 依据")

    architecture = config.get("architecture", {})
    if architecture != _EXPECTED_ARCHITECTURE:
        raise ValueError(
            "architecture 与冻结结构不符；禁止增加块数、宽度扫描、注意力、门控、多尺度、"
            "分段线性编码、端口嵌入或额外归一化层"
        )
    closed_form = expected_parameter_count()
    decomposition = parameter_count_decomposition()
    if decomposition != EXPECTED_PARAMETER_DECOMPOSITION:
        raise ValueError(
            f"参数量逐项分解 {decomposition} 与实施计划第四节第6条登记的 "
            f"{EXPECTED_PARAMETER_DECOMPOSITION} 不符"
        )
    if closed_form != EXPECTED_PARAMETER_COUNT:
        raise ValueError(f"参数量闭式 {closed_form} 与冻结值 {EXPECTED_PARAMETER_COUNT} 不符")
    if architecture["parameter_count"] != closed_form:
        raise ValueError("architecture.parameter_count 与闭式参数量不符")
    for candidate in INPUT_CANDIDATES:
        if candidate["parameter_count"] != closed_form:
            raise ValueError(
                f"输入候选 {candidate['key']} 登记的参数量与闭式 {closed_form} 不符；"
                "两个候选的输出维同为 83，参数量必须相等"
            )

    training = config.get("training", {})
    if training.get("hidden_dropout") != HIDDEN_DROPOUT:
        raise ValueError("training.hidden_dropout 隐藏随机失活必须为 0.15")
    if training.get("residual_dropout") != RESIDUAL_DROPOUT:
        raise ValueError("training.residual_dropout 残差随机失活必须为 0")
    if training.get("fusion_dropout") != FUSION_DROPOUT:
        raise ValueError("training.fusion_dropout 融合随机失活必须为 0.1")
    comparable_training = {
        key: value
        for key, value in training.items()
        if key not in {"hidden_dropout", "residual_dropout", "fusion_dropout"}
    }
    if comparable_training != _EXPECTED_TRAINING:
        raise ValueError("training 训练与选择合同不符（协议 A 冻结值）")
    for key in ("hidden_dropout", "residual_dropout", "fusion_dropout"):
        if training[key] != architecture[key]:
            raise ValueError(f"training.{key} 与 architecture.{key} 不一致")

    if config.get("selection_stages") != _EXPECTED_SELECTION_STAGES:
        raise ValueError("selection_stages 选择阶段合同不符")
    if config.get("evaluation") != _EXPECTED_EVALUATION:
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
            "resource_contract.minimum_free_gpu_memory_mib 必须等于同族先例值 "
            f"{GPU_FREE_MEMORY_MINIMUM_MIB}"
        )

    if config.get("precision_profile_id") != PRECISION_PROFILE_ID:
        raise ValueError(
            f"precision_profile_id 必须为 {PRECISION_PROFILE_ID}："
            "本运行按 RTX 5090 神经训练默认精度配置执行，FP32 与 FP16 只作有收据的显式例外"
        )
    _validate_quantile_policy_shape(config)

    # 只做纯标准库的合同校验，不导入 torch，保证 --validate-config 在无 GPU 开发机可跑。
    contract = load_precision_contract()
    profile = _precision_module().get_profile(contract, PRECISION_PROFILE_ID)
    if profile["compute_dtype"] != "bfloat16" or profile["grad_scaler"] is not False:
        raise ValueError("精度配置不是 BF16 且不使用 GradScaler 的默认配置")
    example = contract["integration_example"]
    # 精度合同自身写明 do_not_inherit_batch_values：示例里的批量是 N-12 的实验合同，
    # 本骨干的微批由 freeze_microbatch_plan 依自身解析张量上界独立冻结，不继承示例值。
    if example.get("example_only") is not True or example.get("do_not_inherit_batch_values") is not True:
        raise ValueError("精度合同的 integration_example 必须标记为示例且禁止继承批量值")

    plan = freeze_microbatch_plan(config, profile)
    if (
        plan["micro_batch_sequences"] != training["micro_batch_sequences"]
        or plan["gradient_accumulation_steps"] != training["gradient_accumulation_steps"]
    ):
        raise ValueError(
            "training 登记的微批与累积步数不等于本工具按解析激活上界复算的冻结值："
            f"复算 micro_batch_sequences={plan['micro_batch_sequences']}、"
            f"gradient_accumulation_steps={plan['gradient_accumulation_steps']}"
        )
    _precision_module().validate_microbatch_plan(
        training["effective_batch_size"],
        training["micro_batch_sequences"],
        training["gradient_accumulation_steps"],
        training["normalization_unit"],
        is_tail_batch=False,
    )

    if config.get("swanlab") != _EXPECTED_SWANLAB:
        raise ValueError("swanlab 上报身份合同不符")
    if config.get("single_run_directly_comparable") is not True:
        raise ValueError("single_run_directly_comparable 必须为真")
    if config.get("formal_paper_evidence") is not False or config.get("independent_test") is not False:
        raise ValueError("本次运行不能宣称正式论文证据或独立测试")


# ---------------------------------------------------------------------------
# 字段基数收据消费与输入接口构造
# ---------------------------------------------------------------------------


def _canonical_sha256(value: Any) -> str:
    """对可 JSON 序列化对象取规范化 SHA-256，与收据工具同口径。"""
    import hashlib

    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_cardinality_receipt(path: str, config: dict[str, Any]) -> dict[str, Any]:
    """读取并机械校验 LSPR23 训练区字段基数收据。

    收据由独立诊断工具产出，本工具只消费不产出。本骨干的扁平数值视图不做独热，
    但仍必须消费收据：它提供七个特殊字段的 ``dijk_feature_index``（决定候选二哪些
    列不参与分位数拟合）、训练有效流数与有效流掩码哈希（决定拟合区身份）。
    """
    receipt_path = Path(path)
    if not receipt_path.exists():
        raise FileNotFoundError(
            f"缺少字段基数收据：{receipt_path}。"
            "输入适配封印前必须先取得该收据，本工具不自行产出，也不以默认字段索引替代"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not receipt.get("complete"):
        raise RuntimeError("字段基数收据未标记完成，拒绝消费")
    if receipt.get("schema_version") != CARDINALITY_RECEIPT_SCHEMA_VERSION:
        raise RuntimeError(f"收据模式版本不符：{receipt.get('schema_version')}")
    if receipt.get("run_id") != CARDINALITY_RECEIPT_RUN_ID:
        raise RuntimeError(f"收据运行身份不符：{receipt.get('run_id')}")
    if receipt["identity"].get("target_year_arrays_read") != 0:
        raise RuntimeError("收据声明读取过目标年数组，拒绝消费")

    expected_fields = (
        list(config["field_groups"]["categorical"]) + list(config["field_groups"]["boolean"])
    )
    if list(receipt["fields"].keys()) != expected_fields:
        raise RuntimeError(f"收据字段清单或顺序不符：{list(receipt['fields'].keys())}")
    split = receipt["protocol_a_source_split"]["statistics"]
    if (split["entity_count"], split["train_sequences"], split["validation_sequences"]) != (
        PROTOCOL_A_SPLIT_STATISTICS["entity_count"],
        PROTOCOL_A_SPLIT_STATISTICS["train_sequences"],
        PROTOCOL_A_SPLIT_STATISTICS["validation_sequences"],
    ):
        raise RuntimeError(f"收据的协议 A 切分身份与本运行不符：{split}")

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
        covered = entry["finite_count"] + entry["missing_count"]
        if covered != effective_flows:
            raise RuntimeError(
                f"字段 {name} 的 finite_count 加 missing_count 为 {covered}，"
                f"未覆盖训练有效流 {effective_flows}"
            )
        logger.info(
            "收据字段 %s：unique_count=%d，missing_fraction=%.6g，integer_like=%s，"
            "min=%s，max=%s，dijk_feature_index=%d",
            name, entry["unique_count"], entry["missing_fraction"], entry["integer_like"],
            entry["min"], entry["max"], index,
        )
    if len(seen_indices) != len(expected_fields):
        raise RuntimeError("收据的特殊字段索引数量与字段清单不符")
    return receipt


def resolve_missing_indicator_policy(receipt: dict[str, Any]) -> bool:
    """裁决是否引入缺失指示位，两个候选必须一致。

    七个字段的 ``missing_fraction`` 实测全为 0，故不引入指示位；两个候选的输入维
    因此同为 83，参数量同为 387,074。一旦收据显示存在缺失，输入维合同需要重新裁定，
    这里停止而不是自行加维。
    """
    nonzero = {
        name: entry["missing_fraction"]
        for name, entry in receipt["fields"].items()
        if entry["missing_fraction"] != 0
    }
    if nonzero:
        raise RuntimeError(
            f"收据显示以下字段存在缺失：{nonzero}。引入缺失指示位会改变输入维与参数量，"
            "而冻结配置把两个候选的 input_dimension 钉为 83、parameter_count 钉为 387074，"
            "属于合同冲突，须先重新裁定输入维合同再运行，本工具拒绝自行加维"
        )
    logger.info("七个特殊字段的 missing_fraction 全为 0，两个候选一致地不引入缺失指示位")
    return False


def resolve_quantile_policy(config: dict[str, Any]) -> dict[str, Any]:
    """裁定候选二 ``source-quantile-83`` 是否满足「有全文或官方依据支持」的准入条件。

    返回 ``{"admitted": bool, "values": {...}, "evidence": {...}, "missing": [...]}``。
    任一策略键的 ``value`` 为 null 或 ``source`` 为空即判定未准入；此时候选二在
    ``select-input`` 阶段被跳过并把缺项写进封印，**绝不**以任何猜测数值补齐，
    也不以另一篇论文另一份源码的口径顶替（见 ``QUANTILE_POLICY_KEYS`` 上方说明）。
    """
    policy = config["quantile_policy"]
    values: dict[str, Any] = {}
    evidence: dict[str, Any] = {}
    missing: list[str] = []
    for key in QUANTILE_POLICY_KEYS:
        entry = policy[key]
        values[key] = entry["value"]
        evidence[key] = entry["source"]
        if entry["value"] is None:
            missing.append(key)
    admitted = not missing
    resolution = {
        "candidate_key": INPUT_CANDIDATE_SOURCE_QUANTILE,
        "admitted": admitted,
        "values": values,
        "evidence": evidence,
        "missing_evidence_keys": missing,
        "admission_rule": (
            "实施计划第三节：候选二仅在有全文或官方依据支持时比较；"
            "四项分位数策略键必须逐项给出 value 与可追溯 source"
        ),
        "blocked_reason": (
            None
            if admitted
            else (
                f"分位数策略键 {missing} 缺少可追溯依据：论文正文与附录未给出这些 "
                "scikit-learn 形参，本仓库归档的 rtdl 快照只含 bin/ft_transformer.py、"
                "不含预处理源码；不得以同组作者后续 TabM 仓库的 NOISY_QUANTILE 数值顶替"
            )
        ),
    }
    if admitted:
        logger.info("候选二分位数策略已封印：%s", values)
    else:
        logger.warning(
            "候选二 %s 未准入，缺少依据的策略键：%s；本次输入选择只比较候选一，"
            "缺项与理由已写入阶段一封印",
            INPUT_CANDIDATE_SOURCE_QUANTILE, missing,
        )
    return resolution


def admitted_input_candidates(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """按冻结顺序返回本次实际参与比较的输入候选与分位数准入裁定。

    候选一无准入条件恒参与；候选二受 ``resolve_quantile_policy`` 裁定。
    准入清单为空是不可能的（候选一恒在），因此不会退化为「以默认输入替代」。
    """
    resolution = resolve_quantile_policy(config)
    admitted: list[dict[str, Any]] = []
    for candidate in sorted(INPUT_CANDIDATES, key=lambda item: item["order"]):
        if candidate["requires_admission_evidence"] and not resolution["admitted"]:
            continue
        admitted.append(dict(candidate))
    if not admitted:
        raise RuntimeError("输入候选准入清单为空，无法进入阶段一")
    logger.info(
        "本次参与阶段一比较的输入候选：%s", [candidate["key"] for candidate in admitted]
    )
    return admitted, resolution


# ---------------------------------------------------------------------------
# 输入变换：两个候选共用同一条「主机取原值 → 冻结变换 → 逐微批上卡」通路
# ---------------------------------------------------------------------------


class InputTransform:
    """在 LSPR23 协议 A 训练区拟合完成后冻结的输入变换。

    ``apply`` 只应用不重新拟合：验证区、时间尾部区与 LSPR24 共用同一份状态。
    两个候选的输出维恒为 83，因此参数量恒为 387,074，比较不混入容量差异。

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
        quantile_feature_indices: tuple[int, ...],
        passthrough_feature_indices: tuple[int, ...],
        quantile_fill_values: tuple[float, ...],
        quantile_transformer: Any,
        quantile_policy: dict[str, Any],
    ) -> None:
        self.candidate_key = candidate_key
        self.output_dimension = output_dimension
        self.state_hash = state_hash
        self.fitted_row_count = fitted_row_count
        self.quantile_feature_indices = quantile_feature_indices
        self.passthrough_feature_indices = passthrough_feature_indices
        # 训练区中位数只作拟合状态与组装式变换器自检的探针，不参与 ``apply``：
        # 两个候选共用同一条缺失策略 training_region_zero_fill_with_absorption_count，
        # X23 已是标准化浮点，补零后的 0 即标准化后的训练区均值。把该值一并冻结是为了
        # 让 quantile_fill_values_sha256 可追溯，不是为了在推理时二次填补。
        self.quantile_fill_values = quantile_fill_values
        self.quantile_transformer = quantile_transformer
        self.quantile_policy = quantile_policy
        # 诊断计数器，不属于冻结状态、不参与 state_hash：统计被按训练区口径补零
        # 吸收的缺失值个数。收据显示训练区七字段缺失率为 0，若目标年出现缺失，
        # 该计数会把分布漂移显式暴露出来而不是无声并入 0。
        self.missing_absorption_count = 0
        self._missing_absorption_warned = False

    def receipt(self) -> dict[str, Any]:
        """供封印与目标评价收据登记的可 JSON 序列化摘要。"""
        return {
            "candidate_key": self.candidate_key,
            "output_dimension": self.output_dimension,
            "state_hash": self.state_hash,
            "fitted_row_count": self.fitted_row_count,
            "quantile_feature_count": len(self.quantile_feature_indices),
            "passthrough_feature_count": len(self.passthrough_feature_indices),
            "quantile_policy": self.quantile_policy,
            "missing_absorption_count": self.missing_absorption_count,
        }

    def apply(self, values: Any) -> Any:
        """把 ``(n, 83)`` 的 float32 原值批变换为 ``(n, 83)`` 的 float32。

        候选一：全部 83 列按训练区口径补零后原样透传（X23 已是标准化浮点，
        补零后的 0 即标准化后的训练区均值）。
        候选二：``quantile_feature_indices`` 指向的 76 个连续与计数字段先按训练区
        中位数填补再做分位数变换；端口、协议与二元粗拓扑七字段仍按补零后透传。
        """
        import numpy as np

        array = np.asarray(values)
        if array.ndim != 2 or array.shape[1] != DIJK_FEATURE_COUNT:
            raise ValueError(f"输入批形状必须为 (n, {DIJK_FEATURE_COUNT})，实际 {array.shape}")
        output = array.astype(np.float32, copy=True)

        missing = ~np.isfinite(output)
        absorbed = int(missing.sum())
        if absorbed:
            self.missing_absorption_count += absorbed
            if not self._missing_absorption_warned:
                self._missing_absorption_warned = True
                logger.warning(
                    "输入批出现 %d 个非有限取值（NaN 或无穷），按训练区口径补零吸收；"
                    "累计次数见 missing_absorption_count",
                    absorbed,
                )
            output[missing] = 0.0

        if self.quantile_transformer is None:
            return np.ascontiguousarray(output)

        columns = list(self.quantile_feature_indices)
        selected = output[:, columns]
        # scikit-learn 对超出拟合范围的取值本身就截断到训练端点输出，无需另加裁剪。
        output[:, columns] = self.quantile_transformer.transform(selected).astype(
            np.float32, copy=False
        )
        return np.ascontiguousarray(output)


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
        raise RuntimeError(
            f"字段 {feature_index} 实际取出 {written} 行，与训练有效流 {row_count} 不符"
        )
    return selected


def _fit_quantile_column(
    values: Any, policy: dict[str, Any], seed: int
) -> tuple[Any, float]:
    """在单个字段上按已封印的分位数策略拟合网格，并返回训练区中位数。

    噪声标准差、输出分布、地标数与子采样上限全部取自 ``policy``，不在本函数写死；
    ``policy`` 的每一项都由 ``resolve_quantile_policy`` 核验过可追溯依据。
    """
    import numpy as np
    from sklearn.preprocessing import QuantileTransformer

    finite = np.isfinite(values)
    if int(finite.sum()) == 0:
        raise RuntimeError("字段在训练区全为缺失，无法拟合分位数规范化")
    median = float(np.nanmedian(values))

    noisy = values.copy()
    standard_deviation = float(policy["noise_standard_deviation"])
    state = np.random.RandomState(seed)
    for start in range(0, len(noisy), QUANTILE_NOISE_CHUNK_ELEMENTS):
        stop = min(start + QUANTILE_NOISE_CHUNK_ELEMENTS, len(noisy))
        noisy[start:stop] += state.normal(0.0, standard_deviation, stop - start).astype(
            np.float32
        )

    transformer = QuantileTransformer(
        n_quantiles=int(policy["n_quantiles"]),
        output_distribution=str(policy["output_distribution"]),
        subsample=int(policy["subsample"]),
        random_state=seed,
    )
    transformer.fit(noisy.reshape(-1, 1))
    return transformer, median


def fit_input_transform(
    candidate_key: str,
    cache_root: str,
    train_flow_mask: Any,
    receipt: dict[str, Any],
    *,
    config: dict[str, Any],
    quantile_resolution: dict[str, Any],
    seed: int = 42,
) -> InputTransform:
    """在 LSPR23 协议 A 训练区有效流上拟合指定候选的输入变换并冻结。

    ``X23`` 一律以 ``mmap_mode="r"`` 打开并逐字段分块处理；任一时刻的显式分配都有
    固定上界，与字段数无关。拟合状态全部并入 ``state_hash``，供选择封印追溯。
    LSPR24 对拟合零参与。
    """
    import hashlib

    import numpy as np

    known_keys = {candidate["key"] for candidate in INPUT_CANDIDATES}
    if candidate_key not in known_keys:
        raise ValueError(f"未知输入候选：{candidate_key}")
    resolve_missing_indicator_policy(receipt)

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

    field_indices = {name: entry["dijk_feature_index"] for name, entry in receipt["fields"].items()}
    special_indices = tuple(sorted(field_indices.values()))
    continuous_indices = tuple(
        index for index in range(DIJK_FEATURE_COUNT) if index not in set(special_indices)
    )
    expected_continuous = config["field_groups"]["numeric_count"]
    if len(continuous_indices) != expected_continuous:
        raise RuntimeError(
            f"连续与计数字段数 {len(continuous_indices)} 与冻结分组 {expected_continuous} 不符"
        )

    if candidate_key == INPUT_CANDIDATE_STANDARDIZED:
        state = {
            "candidate_key": candidate_key,
            "output_dimension": DIJK_FEATURE_COUNT,
            "fitted_row_count": row_count,
            "numeric_transform": "frozen_training_region_standardized_passthrough",
            "quantile_feature_indices": [],
            "passthrough_feature_indices": list(range(DIJK_FEATURE_COUNT)),
            "missing_policy": "training_region_zero_fill_with_absorption_count",
            "field_integer_like": {
                name: bool(entry["integer_like"]) for name, entry in receipt["fields"].items()
            },
            "cardinality_receipt_effective_flow_mask_sha256": flow_mapping[
                "effective_flow_mask_sha256"
            ],
        }
        state_hash = _canonical_sha256(state)
        logger.info(
            "输入变换 %s 已冻结（无需拟合）：输出维=%d，参数量=%d，state_hash=%s",
            candidate_key, DIJK_FEATURE_COUNT, expected_parameter_count(), state_hash,
        )
        return InputTransform(
            candidate_key=candidate_key,
            output_dimension=DIJK_FEATURE_COUNT,
            state_hash=state_hash,
            fitted_row_count=row_count,
            quantile_feature_indices=(),
            passthrough_feature_indices=tuple(range(DIJK_FEATURE_COUNT)),
            quantile_fill_values=(),
            quantile_transformer=None,
            quantile_policy={"applied": False, "reason": "候选一不拟合任何分位数状态"},
        )

    if not quantile_resolution["admitted"]:
        raise RuntimeError(
            f"候选二 {candidate_key} 未通过准入：{quantile_resolution['blocked_reason']}。"
            "本工具不以任何猜测数值补齐分位数策略"
        )
    import sklearn
    from sklearn.preprocessing import QuantileTransformer

    policy_values = quantile_resolution["values"]
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

    logger.info(
        "开始拟合输入变换 %s：训练有效流=%d，参与拟合的连续与计数字段=%d，"
        "排除的端口/协议/二元粗拓扑字段=%d，分块行数=%d，分位数策略=%s",
        candidate_key, row_count, len(continuous_indices), len(special_indices),
        chunk_rows, policy_values,
    )

    quantile_columns: list[Any] = []
    fill_values: list[float] = []
    references: Any = None
    landmark_actual: int | None = None
    for position, feature_index in enumerate(continuous_indices, start=1):
        column = _gather_training_column(matrix, feature_index, mask, row_count, chunk_rows)
        # 每个字段使用独立派生种子。官方对 (n, d) 训练矩阵一次性抽取噪声，逐字段处理
        # 无法复现同一随机流；此处每元素仍为独立同分布 N(0, sigma)，只是随机流分配
        # 方式不同，是显式记录的实现偏离。
        transformer, median = _fit_quantile_column(column, policy_values, seed + feature_index)
        quantile_columns.append(transformer.quantiles_[:, 0])
        fill_values.append(median)
        if references is None:
            references = transformer.references_.copy()
            landmark_actual = int(transformer.n_quantiles_)
        del column
        if position % 10 == 0 or position == len(continuous_indices):
            logger.info("分位数拟合进度 %d/%d", position, len(continuous_indices))

    quantile_transformer = QuantileTransformer(
        n_quantiles=int(policy_values["n_quantiles"]),
        output_distribution=str(policy_values["output_distribution"]),
        subsample=int(policy_values["subsample"]),
        random_state=seed,
    )
    quantile_transformer.n_quantiles_ = landmark_actual
    quantile_transformer.quantiles_ = np.stack(quantile_columns, axis=1)
    quantile_transformer.references_ = references
    quantile_transformer.n_features_in_ = len(continuous_indices)

    # 组装式变换器直接写入了 scikit-learn 的私有拟合属性，未来版本一旦改变这些属性
    # 的语义就会静默产出错误数值。这里加一条运行时自检：输出分布为 normal 时，
    # 训练区中位数应被映射到约 0；偏差超过绊线即停止。其他输出分布下跳过并记录。
    median_probe = np.asarray(fill_values, dtype=np.float32).reshape(1, -1)
    median_response = quantile_transformer.transform(median_probe)
    median_deviation = float(np.max(np.abs(median_response)))
    if str(policy_values["output_distribution"]) == "normal":
        if median_deviation > QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE:
            raise RuntimeError(
                f"组装式分位数变换器自检失败：训练区中位数映射后的最大绝对值为 "
                f"{median_deviation:.6g}，超过绊线 {QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE}；"
                f"scikit-learn {sklearn.__version__} 的私有拟合属性语义可能已改变"
            )
        logger.info(
            "组装式变换器自检通过：中位数映射最大绝对值=%.6g（绊线 %.3g），scikit-learn=%s",
            median_deviation, QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE, sklearn.__version__,
        )
    else:
        logger.warning(
            "输出分布为 %s 而非 normal，跳过中位数自检；只记录实测最大绝对值 %.6g",
            policy_values["output_distribution"], median_deviation,
        )

    state = {
        "candidate_key": candidate_key,
        "output_dimension": DIJK_FEATURE_COUNT,
        "fitted_row_count": row_count,
        "numeric_transform": (
            "lspr23_training_region_quantile_normalization_on_continuous_and_count_fields_only"
        ),
        "quantile_feature_indices": list(continuous_indices),
        "passthrough_feature_indices": list(special_indices),
        "quantile_policy_values": policy_values,
        "quantile_policy_evidence": quantile_resolution["evidence"],
        "quantile_landmark_count": landmark_actual,
        "noise_seed_derivation": "per_feature_seed_plus_dijk_feature_index",
        "scikit_learn_version": sklearn.__version__,
        "median_self_check_max_absolute_value": median_deviation,
        "median_self_check_tolerance": QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE,
        "quantile_fill_values_sha256": hashlib.sha256(
            np.asarray(fill_values, dtype=np.float64).tobytes()
        ).hexdigest(),
        "quantile_grid_sha256": hashlib.sha256(
            np.ascontiguousarray(quantile_transformer.quantiles_).tobytes()
        ).hexdigest(),
        "quantile_references_sha256": hashlib.sha256(
            np.ascontiguousarray(quantile_transformer.references_).tobytes()
        ).hexdigest(),
        "field_integer_like": {
            name: bool(entry["integer_like"]) for name, entry in receipt["fields"].items()
        },
        "cardinality_receipt_effective_flow_mask_sha256": flow_mapping[
            "effective_flow_mask_sha256"
        ],
    }
    state_hash = _canonical_sha256(state)
    logger.info(
        "输入变换 %s 拟合完成：输出维=%d，参数量=%d，state_hash=%s",
        candidate_key, DIJK_FEATURE_COUNT, expected_parameter_count(), state_hash,
    )
    return InputTransform(
        candidate_key=candidate_key,
        output_dimension=DIJK_FEATURE_COUNT,
        state_hash=state_hash,
        fitted_row_count=row_count,
        quantile_feature_indices=continuous_indices,
        passthrough_feature_indices=special_indices,
        quantile_fill_values=tuple(fill_values),
        quantile_transformer=quantile_transformer,
        quantile_policy={"applied": True, **policy_values},
    )


# ---------------------------------------------------------------------------
# 冻结骨干：表格预归一化残差多层感知机
# ---------------------------------------------------------------------------

_BACKBONE_CACHE: dict[str, Any] = {}


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

    class PreNormResidualBlock(nn.Module):
        """冻结残差块：``LayerNorm → Linear(d,h) → ReLU → Dropout(0.15)
        → Linear(h,d) → Dropout(0) → 残差相加``。

        这是 Gorishniy 2021 物理页 3 公式 2 表格残差块的**预归一化变体**：原文首层
        为 ``BatchNorm``，本任务改用逐标记 ``LayerNorm`` 以保持前向因果与补零独立。
        该替换是本课题任务适配，不得写成论文原配方。

        参数构成与 ``residual_block_parameter_count`` 逐项对应：``LayerNorm`` 的
        权重与偏置共 ``2d``，``linear1`` 为 ``d*h+h``，``linear2`` 为 ``h*d+d``；
        两个随机失活层与残差相加均无参数。
        """

        def __init__(
            self,
            main_width: int,
            hidden_width: int,
            hidden_dropout: float,
            residual_dropout: float,
        ) -> None:
            super().__init__()
            self.main_width = main_width
            self.hidden_width = hidden_width
            self.normalization = nn.LayerNorm(main_width)
            self.linear1 = nn.Linear(main_width, hidden_width)
            self.linear2 = nn.Linear(hidden_width, main_width)
            self.activation = nn.ReLU()
            self.hidden_dropout = nn.Dropout(hidden_dropout)
            self.residual_dropout = nn.Dropout(residual_dropout)

        def parameter_count(self) -> int:
            return residual_block_parameter_count(self.main_width, self.hidden_width)

        def forward(self, values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
            # values: (N, T, d) -> (N, T, d)
            #
            # ``nn.LayerNorm`` 在 BF16 autocast 下自动在 FP32 中计算：PyTorch 的
            # aten/src/ATen/autocast_mode.h 把 layer_norm 与 native_layer_norm 列入
            # AT_FORALL_FP32（2026-08-21 经 Context7 取 pytorch/pytorch 主干源码核验），
            # 即 autocast 无视输入类型强制以 FP32 执行。因此这里不需要额外的
            # fp32_island，也不得改用 in-place 或显式 .to(bfloat16) 绕过该策略。
            residual = self.normalization(values)
            residual = self.hidden_dropout(self.activation(self.linear1(residual)))
            residual = self.residual_dropout(self.linear2(residual))
            # out-of-place 相加，避免破坏自动求导图。
            return masked(values + residual, mask)

    class TabularResNetBackbone(nn.Module):
        """两块表格残差骨干，含因果前缀聚合与实体级可学幂平均池化两个开关。

        ``aggregate`` 为假时上下文置零后同样拼接成 ``2d`` 维，使两条路径的参数量与
        张量形状完全一致，机制差异只来自上下文是否携带信息。
        """

        def __init__(
            self,
            input_dimension: int,
            main_width: int,
            hidden_width: int,
            residual_blocks: int,
            hidden_dropout: float,
            residual_dropout: float,
            fusion_dropout: float,
            aggregate: bool,
        ) -> None:
            super().__init__()
            self.input_dimension = input_dimension
            self.main_width = main_width
            self.hidden_width = hidden_width
            self.aggregate = aggregate
            self.input_projection = nn.Linear(input_dimension, main_width)
            self.blocks = nn.ModuleList(
                PreNormResidualBlock(main_width, hidden_width, hidden_dropout, residual_dropout)
                for _ in range(residual_blocks)
            )
            self.fusion_linear = nn.Linear(main_width * 2, main_width)
            self.fusion_activation = nn.ReLU()
            self.fusion_dropout = nn.Dropout(fusion_dropout)
            self.output = nn.Linear(main_width, 1)
            self.p_log = nn.Parameter(torch.tensor(math.log(MECHANISM_ELP_INITIAL_P)))

        @property
        def p(self) -> torch.Tensor:
            return torch.exp(self.p_log).clamp(MECHANISM_ELP_P_MINIMUM, MECHANISM_ELP_P_MAXIMUM)

        def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
            # values: (N, T, F) 与 valid: (N, T) -> 逐流对数几率 (N, T)
            if values.ndim != 3 or values.shape[FEATURE_AXIS] != self.input_dimension:
                raise RuntimeError(
                    f"表格 ResNet 训练输入必须是 N×T×{self.input_dimension}，"
                    f"实际 {tuple(values.shape)}"
                )
            if valid.shape != values.shape[:FEATURE_AXIS]:
                raise RuntimeError(f"有效掩码必须是 N×T，实际 {tuple(valid.shape)}")
            device_type = values.device.type
            mask = valid.to(torch.float32)
            hidden = masked(self.input_projection(values), mask)
            for block in self.blocks:
                hidden = block(hidden, mask)

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

            # 机制边界：因果前缀聚合只沿时间轴累积，且严格只读当前及之前的位置。
            # 上下文张量必须与隐藏张量同形；任何跨序列聚合或形状变化都会在此立即失败。
            if context.shape != hidden.shape:
                raise RuntimeError(
                    "因果前缀聚合越出时间轴：上下文张量必须与隐藏张量同形，"
                    f"实际 {tuple(context.shape)} 对 {tuple(hidden.shape)}"
                )

            fused = masked(
                self.fusion_dropout(
                    self.fusion_activation(
                        self.fusion_linear(torch.cat((hidden, context), dim=-1))
                    )
                ),
                mask,
            )
            return self.output(fused).squeeze(-1)

        def flow_probability(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
            """推理路径：直接得到逐流概率；``sigmoid`` 在 FP32 岛内完成。"""
            logits = self.forward(values, valid)
            with precision.fp32_island(
                logits, device_type=logits.device.type, torch_module=torch
            ) as (logits32,):
                probabilities = torch.sigmoid(logits32)
            return probabilities

    _BACKBONE_CACHE.update(
        {
            "PreNormResidualBlock": PreNormResidualBlock,
            "TabularResNetBackbone": TabularResNetBackbone,
        }
    )
    return _BACKBONE_CACHE


def learned_lp_pool(scores: Any, valid: Any, p_value: Any) -> Any:
    """实体级可学幂平均池化。

    ``scores`` 必须是 ``N×T`` 的逐流概率与同形掩码。对数、幂与掩码归约都属精度合同
    的敏感计算，全部在 FP32 岛内完成。公式与既有协议 A 四格工具逐字同式。
    """
    import torch

    if scores.ndim != 2 or valid.ndim != 2 or scores.shape != valid.shape:
        raise RuntimeError(
            "ELP 池化输入必须是 N×T 概率与同形掩码，"
            f"实际 {tuple(scores.shape)} 与 {tuple(valid.shape)}"
        )
    precision = _precision_module()
    with precision.fp32_island(
        scores, valid, p_value, device_type=scores.device.type, torch_module=torch
    ) as (scores32, valid32, exponent):
        log_scores = torch.log(scores32.clamp(min=MECHANISM_ELP_PROBABILITY_FLOOR))
        count = valid32.sum(1).clamp(min=1.0)
        summed = torch.logsumexp((exponent * log_scores).masked_fill(valid32 < 0.5, -1e30), 1)
        pooled = torch.exp((summed - torch.log(count)) / exponent)
    return pooled


def resolve_weight_decay_groups(model: Any) -> dict[str, Any]:
    """按参数角色而非名称子串划分权重衰减分组。

    不衰减组：全部 ``LayerNorm`` 参数、全部偏置、共享标量 ``p_log``。
    衰减组：输入投影、两块残差分支与融合层的线性主权重，以及输出头权重。
    两个冻结优化器候选的权重衰减均为 0，因此本函数当前不改变数值结果；保留角色化
    分组是为了让非零权重衰减一旦被引入也不会误伤归一化与偏置参数。
    """
    from torch import nn

    normalization_parameters: set[str] = set()
    for module_name, module in model.named_modules():
        if isinstance(module, nn.LayerNorm):
            for parameter_name, _ in module.named_parameters(recurse=False):
                normalization_parameters.add(
                    f"{module_name}.{parameter_name}" if module_name else parameter_name
                )
    decay_names: list[str] = []
    no_decay_names: list[str] = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        if name in normalization_parameters or name.endswith(".bias") or name == "p_log":
            no_decay_names.append(name)
        else:
            decay_names.append(name)
    if not decay_names or not no_decay_names:
        raise RuntimeError(
            f"权重衰减分组退化：衰减组 {len(decay_names)} 个、不衰减组 {len(no_decay_names)} 个"
        )
    if "p_log" not in no_decay_names:
        raise RuntimeError("共享标量 p_log 必须在不衰减组")
    if not normalization_parameters.issubset(set(no_decay_names)):
        raise RuntimeError("存在 LayerNorm 参数落入衰减组")
    return {
        "decay": decay_names,
        "no_decay": no_decay_names,
        "excluded_parameter_roles": ["layer_normalization", "bias", "shared_scalar_p_log"],
        "excluded_weight_decay_value": 0.0,
    }


def build_model(
    config: dict[str, Any], cell: str, input_key: str, input_dimension: int
) -> Any:
    """按格构造骨干并做参数量三方比对。

    三方为：闭式 ``expected_parameter_count(...)``、冻结配置中登记的
    ``architecture.parameter_count`` 与该输入候选的 ``parameter_count``、
    以及实际 ``sum(p.numel() for p in model.parameters() if p.requires_grad)``。
    任一不等立即抛错，禁止先看指标再改结构。
    """
    import torch

    if cell not in CELLS:
        raise ValueError(f"未知实验格：{cell}")
    if input_dimension != DIJK_FEATURE_COUNT:
        raise RuntimeError(
            f"本骨干的两个输入候选输出维恒为 {DIJK_FEATURE_COUNT}，实际 {input_dimension}"
        )
    architecture = config["architecture"]
    training = config["training"]
    classes = backbone_classes()
    model = classes["TabularResNetBackbone"](
        input_dimension=input_dimension,
        main_width=architecture["main_width"],
        hidden_width=architecture["hidden_width"],
        residual_blocks=architecture["residual_blocks"],
        hidden_dropout=training["hidden_dropout"],
        residual_dropout=training["residual_dropout"],
        fusion_dropout=training["fusion_dropout"],
        aggregate=CELLS[cell]["causal_prefix_aggregation"],
    )
    closed_form = expected_parameter_count(
        input_dimension,
        architecture["main_width"],
        architecture["hidden_width"],
        architecture["residual_blocks"],
    )
    decomposition = parameter_count_decomposition(
        input_dimension,
        architecture["main_width"],
        architecture["hidden_width"],
        architecture["residual_blocks"],
    )
    actual = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    frozen_candidate = next(entry for entry in INPUT_CANDIDATES if entry["key"] == input_key)
    frozen_parameters = frozen_candidate["parameter_count"]
    if closed_form != architecture["parameter_count"]:
        raise RuntimeError(
            f"参数量闭式 {closed_form} 与冻结配置登记的 {architecture['parameter_count']} 不符"
        )
    if closed_form != frozen_parameters:
        raise RuntimeError(
            f"参数量闭式 {closed_form} 与输入候选 {input_key} 登记的 {frozen_parameters} 不符"
        )
    if actual != closed_form:
        raise RuntimeError(
            f"实际可训练参数量 {actual} 与闭式 {closed_form} 不符；"
            f"逐项分解={decomposition}"
        )
    if actual != EXPECTED_PARAMETER_COUNT:
        raise RuntimeError(
            f"实际可训练参数量 {actual} 与实施计划冻结值 {EXPECTED_PARAMETER_COUNT} 不符"
        )
    # 逐模块回读残差块参数，确认块数与宽度没有被结构改动悄悄改变。
    for index, block in enumerate(model.blocks):
        block_actual = sum(
            parameter.numel() for parameter in block.parameters() if parameter.requires_grad
        )
        if block_actual != block.parameter_count():
            raise RuntimeError(
                f"第 {index + 1} 个残差块实际参数量 {block_actual} 与闭式 "
                f"{block.parameter_count()} 不符"
            )
    # 参数必须保持 FP32：这里先核参数，优化器状态在第一次 step 之后再核。
    for name, parameter in model.named_parameters():
        if parameter.is_floating_point() and parameter.dtype != torch.float32:
            raise RuntimeError(f"模型参数 {name} 不是 FP32，与精度合同不符")
    if model.p_log.dtype != torch.float32:
        raise RuntimeError("共享标量 p_log 必须是 FP32")
    logger.info(
        "已构造 %s 骨干：输入候选=%s，输入维=%d，主宽度=%d，隐藏宽度=%d，残差块=%d，"
        "因果前缀聚合=%s，可训练参数量=%d（闭式、冻结登记值与实测三方一致），逐项分解=%s",
        cell, input_key, input_dimension, architecture["main_width"],
        architecture["hidden_width"], architecture["residual_blocks"],
        CELLS[cell]["causal_prefix_aggregation"], actual, decomposition,
    )
    return model


# ---------------------------------------------------------------------------
# 原子写、摘要与资源快照
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
    略微高估外部占用；它只作污染判据，不作准入阈值。
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


def _resolve_device() -> Any:
    """解析本次运行的计算设备；精度合同要求 CUDA BF16，无 CUDA 时不静默降级。"""
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    raise RuntimeError(
        f"本运行的精度合同 {PRECISION_PROFILE_ID} 要求 CUDA，当前环境无可用 CUDA；"
        "非 CUDA 环境须先取得显式例外收据，本工具不静默降级"
    )


# ---------------------------------------------------------------------------
# 源年数据加载、协议 A 切分与主机侧视图
# ---------------------------------------------------------------------------


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
    # 「存在整条全掩码序列」这一数据合同违例暴露成明确错误。
    length = training["sequence_length"]
    for name, rows in (("训练", train_rows), ("验证", validation_rows)):
        per_row_valid = (arrays["M23"][rows][:, :length] > 0.5).sum(axis=1)
        if int(per_row_valid.min()) <= 0:
            raise RuntimeError(f"{name}集中存在有效流数为 0 的序列，违反逐流归一化前提")
    logger.info("协议 A 源年切分统计已核验：%s", statistics)
    return train_rows, validation_rows, statistics


def build_effective_flow_mask(
    indices: Any, mask: Any, train_rows: Any, flow_count: int
) -> tuple[Any, dict[str, Any]]:
    """训练有效流掩码：把训练区序列的有效位置映射到流索引，去重后置真。

    与诊断工具 ``tools/ch3_lspr23_field_cardinality_receipt.py`` 的同名函数逐字同
    算法（含分块行数 4096），使本工具独立重算出的掩码哈希能够与收据登记的
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


class ProtocolASourceView:
    """协议 A 源年数据的主机侧视图，按已冻结的输入变换逐微批供给特征。

    两个输入候选共用同一条数据通路「主机取原值 → 冻结变换 → 逐微批上卡」，
    因此两者的数据通路开销可比，比较只反映数值变换差异。
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
        """把 ``(n, T)`` 流索引展成 ``(n, T, 83)`` 的 float32 特征。

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
    """按优化器候选建 AdamW，并按参数角色划分权重衰减分组。

    协议 A 无学习率调度，此处不建 scheduler（Gorishniy 2021 物理页 6 明确不使用）。
    """
    import torch

    candidate = next(
        (entry for entry in config["optimizer_candidates"] if entry["key"] == optimizer_key), None
    )
    if candidate is None:
        raise ValueError(f"未知优化器候选：{optimizer_key}")
    groups = resolve_weight_decay_groups(model)
    named = dict(model.named_parameters())
    decay = [named[name] for name in groups["decay"]]
    no_decay = [named[name] for name in groups["no_decay"]]
    optimizer = torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": candidate["weight_decay"]},
            {"params": no_decay, "weight_decay": groups["excluded_weight_decay_value"]},
        ],
        lr=candidate["learning_rate"],
    )
    logger.info(
        "优化器候选 %s：学习率=%s，权重衰减=%s，衰减组参数 %d 个、不衰减组 %d 个"
        "（不衰减角色=%s），无学习率调度",
        candidate["display_name"], candidate["learning_rate"], candidate["weight_decay"],
        len(decay), len(no_decay), groups["excluded_parameter_roles"],
    )
    return optimizer, {**candidate, "weight_decay_groups": groups}


def _move_optimizer_state(optimizer: Any, device: Any) -> None:
    """把 ``optimizer.load_state_dict`` 恢复后仍留在 CPU 的张量状态搬到目标设备。"""
    import torch

    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                state[key] = value.to(device)


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
                probabilities = model.flow_probability(values_t, valid_t)
            flat_mask = valid.reshape(-1)
            predictions.append(probabilities.reshape(-1).float().cpu().numpy()[flat_mask])
            labels.append(flow_labels.reshape(-1)[flat_mask])
    model.train()
    scores = np.concatenate(predictions)
    targets = np.concatenate(labels)
    return float(average_precision_score(targets, scores)), int(len(scores))


# ---------------------------------------------------------------------------
# 训练循环、梯度累积与协议 A 检查点选择
# ---------------------------------------------------------------------------


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
    标量损失交给 ``EffectiveBatchAccumulator.backward``（内部统一除以本步的全部有效
    流数），全部微批反向完成后只裁剪一次并只更新一次。

    选择规则：跑满 ``epochs`` 轮、每轮 ``steps_per_epoch`` 步，不早停、无学习率调度；
    每轮结束在实体不相交验证集上算逐流平均精度，用严格大于更新最优，因此并列保留
    最早轮次。

    三层断点恢复：

    - 完成层：``checkpoints/selected-{cell}.pt`` 与 ``receipts/selection-{cell}.json``
      同时存在时，只有传了 ``--resume`` 且收据 ``identity`` 等于本次调用的
      ``identity``、且收据记录的检查点 ``sha256`` 等于实测哈希，才直接复用并跳过训练。
    - 未传 ``--resume`` 时若任一历史制品已存在，直接拒绝，避免静默覆盖。
    - 在途层：每个 epoch 完整跑满（即 ``optimizer.step()`` 的完整边界）后原子写
      ``inflight/{cell}.pt``；恢复时先核验精度、微批量、累积步数与身份一致，
      再从 ``epoch+1`` 继续。半个有效批中断时该 epoch 从未落盘，恢复会整轮重放。
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
        if not resume or receipt.get("identity") != identity or checkpoint_sha != _sha256_file(
            checkpoint_path
        ):
            raise RuntimeError(
                f"{cell}（输入候选={input_key}，优化器候选={optimizer_key}）已有完成检查点，"
                "但未传 --resume、身份不符或摘要不符，拒绝覆盖或部分拼接"
            )
        logger.info("%s 完成层复用：身份与检查点摘要均匹配，跳过训练：%s", cell, receipt_path)
        return receipt["selection"]
    if not resume and (
        checkpoint_path.exists() or receipt_path.exists() or inflight_path.exists()
    ):
        raise RuntimeError(f"全新运行（未传 --resume）已存在 {cell} 的历史制品，拒绝覆盖：{output_root}")

    precision = _precision_module()
    training = config["training"]
    micro_batch = training["micro_batch_sequences"]
    accumulation_steps = training["gradient_accumulation_steps"]
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
    bounds = tensor_upper_bounds(config, profile)
    logger.info(
        "%s 张量上界（按展开维度乘积，非参数量）：单微批有效流位=%d，主机稠密输入=%.2f MiB，"
        "隐藏张量=%.2f MiB（%s）/%.2f MiB（FP32 口径），块内展开=%.2f MiB，"
        "因果前缀拼接=%.2f MiB，因果前缀 FP32 岛=%.2f MiB，前向保留激活解析上界=%.2f MiB",
        cell, bounds["micro_batch_flows"],
        bounds["micro_batch_host_dense_input_bytes"] / 2**20,
        bounds["hidden_tensor_bytes"] / 2**20, profile["compute_dtype"],
        bounds["hidden_tensor_fp32_bytes"] / 2**20,
        bounds["block_hidden_expansion_bytes"] / 2**20,
        bounds["causal_prefix_concat_bytes"] / 2**20,
        bounds["causal_prefix_fp32_island_bytes"] / 2**20,
        bounds["retained_activation_bytes"] / 2**20,
    )

    random.seed(training["seed"])
    np.random.seed(training["seed"])
    torch.manual_seed(training["seed"])
    if device_type == "cuda":
        torch.cuda.manual_seed_all(training["seed"])

    model = build_model(config, cell, input_key, view.transform.output_dimension).to(device)
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
    # 若恢复自一个已跑满全部轮次但尚未落最终检查点的在途状态，下方轮次循环不会执行
    # 任何一次，accumulator 需要有定义的占位，避免收尾阶段引用未定义变量。
    accumulator: Any = None

    for epoch in range(start_epoch, training["epochs"] + 1):
        epoch_started = time.time()
        running_loss = 0.0
        for step in range(1, training["steps_per_epoch"] + 1):
            positions = sample_distinct_positions(len(train_rows), effective_batch, generator)
            rows = train_rows[positions.numpy()]
            indices, valid, flow_labels = view.gather_sequences(rows, length)
            total_valid_flows = int(valid.sum())
            sequence_labels = np.asarray((flow_labels * valid).max(axis=1) > 0, dtype=np.float32)
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
                    logits = model(values_t, valid_t)
                # 损失、概率归一化与掩码归约都是精度合同的敏感计算，进 FP32 岛。
                with precision.fp32_island(
                    logits, device_type=device_type, torch_module=torch
                ) as (logits32,):
                    loss_sum = (flow_loss(logits32, labels32) * mask32).sum()
                    if uses_lp:
                        flow_probability = torch.sigmoid(logits32)
                        pooled = learned_lp_pool(flow_probability, mask32, model.p).clamp(
                            MECHANISM_ELP_POOLED_CLAMP, 1.0 - MECHANISM_ELP_POOLED_CLAMP
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
                    "schema_version": "ch3-tabular-resnet-first-step-memory-v1",
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
                "schema_version": "ch3-tabular-resnet-inflight-checkpoint-v1",
                "identity": dict(identity),
                "epoch": epoch,
                "model_state_dict": {
                    name: tensor.detach().cpu().clone()
                    for name, tensor in model.state_dict().items()
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
    _atomic_torch(
        checkpoint_path,
        {
            "schema_version": "ch3-tabular-resnet-protocol-a-selected-checkpoint-v1",
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
            "torch.cuda.mem_get_info 总量减空闲减本进程 memory_reserved"
            if device_type == "cuda"
            else "非 CUDA 设备"
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
        "input_transform_receipt": view.transform.receipt(),
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
        "weight_decay_groups": optimizer_candidate["weight_decay_groups"],
    }
    logger.info(
        "%s 训练完成：最优轮次=%d 验证逐流AP=%.8f p=%.6f 用时=%.1f 分 检查点=%s",
        cell, best_epoch, best_ap, best_p, training_seconds / 60.0, checkpoint_path,
    )

    _atomic_json(receipt_path, {"identity": dict(identity), "selection": selection})
    inflight_path.unlink(missing_ok=True)
    return selection


# ---------------------------------------------------------------------------
# 运行身份、数据清单与制品状态
# ---------------------------------------------------------------------------


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
        "schema_version": "ch3-tabular-resnet-data-inventory-v1",
        "cache_root": str(cache_root),
        "files": files,
        "sha256": _canonical_sha256(files),
    }


def build_run_identity(
    config_path: Path, cache_root: Path, cardinality_receipt_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """本工具独立重算的运行身份：配置、代码、源数据与字段基数收据四路哈希。"""
    source_inventory = data_inventory(cache_root, SOURCE_ARRAYS)
    identity = {
        "schema_version": "ch3-tabular-resnet-run-identity-v1",
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
        "schema_version": "ch3-tabular-resnet-cell-identity-v1",
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
    logger.info(
        "%s 已从选择阶段完成运行复用（身份与检查点摘要均核验通过）：%s -> %s",
        cell, source_root, target_root,
    )
    return receipt["selection"]


def save_input_transform(path: Path, transform: InputTransform) -> None:
    """把已在 LSPR23 训练区拟合完成的输入变换整体持久化，供 evaluate 阶段只应用不拟合。"""
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
            "schema_version": "ch3-tabular-resnet-paper-recipe-protocol-a-status-v1",
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
            "schema_version": "ch3-tabular-resnet-paper-recipe-protocol-a-manifest-v1",
            "run_id": run_id,
            "files": files,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "complete_budget_curve_persisted": "complete-alert-budget-curves.npz" in files,
        },
    )


# ---------------------------------------------------------------------------
# 目标年评价：实体聚合、实际可达 FPR 检出率与完整告警预算曲线
# ---------------------------------------------------------------------------


def entity_scores(
    flow_scores: Any, seen: Any, flow_entity: Any, entity_count: int, p_value: float | None
) -> Any:
    """按实体聚合逐流分数：``p_value`` 为空取实体内最大值，否则做共享 p 的 ELP 池化。

    与既有协议 A 四格工具同公式，供 ``evaluate`` 阶段区分「主指标（学习池化格用
    ELP，其余格用最大池化）」与「最大池化指标（全部格统一用最大池化）」。
    """
    import numpy as np

    if p_value is None:
        scores = np.full(entity_count, -np.inf, dtype=np.float32)
        np.maximum.at(scores, flow_entity[seen], flow_scores[seen])
        return scores
    numerator = np.zeros(entity_count, dtype=np.float64)
    count = np.zeros(entity_count, dtype=np.float64)
    np.add.at(
        numerator, flow_entity[seen],
        np.clip(flow_scores[seen], MECHANISM_ELP_PROBABILITY_FLOOR, 1.0).astype(np.float64)
        ** p_value,
    )
    np.add.at(count, flow_entity[seen], 1.0)
    return np.where(
        count > 0, (numerator / np.maximum(count, 1.0)) ** (1.0 / p_value), -np.inf
    ).astype(np.float32)


def dr_at_fpr(scores: Any, labels: Any, target_fpr: float) -> dict[str, Any]:
    """在名义误报预算处取检测率，同时回报该工作点的**实际可达** FPR。

    工作点规则与既有协议 A 四格工具逐字相同：负类实体分数降序排列后取下标
    ``min(int(len(negative) * target_fpr), len(negative) - 1)`` 处的分数作阈值。
    保持同一规则是为了让本骨干的六档检出率能与既有四格工具并入同一张第三章总表。

    在此基础上补两件既有工具没有做的事，以满足实施计划第八节
    「六档必须使用实际可达 FPR、名义工作点越出预算时须报告真实 FPR」：

    1. ``realized_fpr`` 按该阈值实际判正的负类实体比例重新计数，而不是沿用名义值。
       并列分数会把多个负类实体一起带过阈值，此时实际值高于名义值。
    2. ``within_nominal_budget`` 标出实际值是否仍在名义预算内；越出时写日志警告。
       禁止把名义 ``4%`` 当作真实值写进任何结果表。
    """
    import numpy as np

    valid = np.isfinite(scores)
    values = scores[valid]
    target = labels[valid]
    negative = np.sort(values[target == 0])[::-1]
    positive = values[target == 1]
    if len(negative) == 0 or len(positive) == 0:
        raise RuntimeError("检测率计算缺少正类或负类实体")
    index = min(int(len(negative) * target_fpr), len(negative) - 1)
    threshold = negative[index]
    false_positive = int((negative >= threshold).sum())
    realized_fpr = false_positive / len(negative)
    return {
        "detection_rate": float((positive >= threshold).mean()),
        "nominal_fpr": float(target_fpr),
        "realized_fpr": float(realized_fpr),
        "nominal_index": int(index),
        "n_false_positive_entity": false_positive,
        "n_negative_entity": int(len(negative)),
        "within_nominal_budget": bool(realized_fpr <= target_fpr),
        "threshold_is_a_reachable_negative_entity_score": True,
    }


def dr_at_fpr_table(scores: Any, labels: Any, prefix: str) -> dict[str, Any]:
    """把六档工作点展开为「与既有工具逐字同名的检出率」加「实际可达 FPR 明细」。

    返回三个字典：``<prefix>``（键名与既有四格工具逐字相同，值为检出率）、
    ``<prefix>_realized``（同键名，值为该工作点的实际可达 FPR）与
    ``<prefix>_detail``（同键名，值为完整工作点明细）。
    """
    detection: dict[str, float] = {}
    realized: dict[str, float] = {}
    detail: dict[str, Any] = {}
    for value in DR_FPR_GRID:
        key = f"fpr_{value:g}"
        point = dr_at_fpr(scores, labels, value)
        detection[key] = point["detection_rate"]
        realized[key] = point["realized_fpr"]
        detail[key] = point
        if not point["within_nominal_budget"]:
            logger.warning(
                "%s 的名义工作点 %s 因并列分数越出预算：实际可达 FPR=%.8g（名义 %.8g），"
                "误报实体数=%d/%d；结果表必须写实际值",
                prefix, key, point["realized_fpr"], point["nominal_fpr"],
                point["n_false_positive_entity"], point["n_negative_entity"],
            )
    return {prefix: detection, f"{prefix}_realized": realized, f"{prefix}_detail": detail}


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
    output_root: Path,
    cell: str,
    identity: dict[str, Any],
    cell_result: dict[str, Any],
    curve: dict[str, Any],
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
            "schema_version": "ch3-tabular-resnet-target-cell-receipt-v1",
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

    评价阶段不得训练、不得替换检查点、不得搜索阈值、不得更新聚合指数或任何超参数，
    因此这里全程 ``torch.no_grad()``，且不调用 ``optimizer``、不调用 ``model.train()``。
    """
    import numpy as np
    import torch

    precision = _precision_module()
    length = config["training"]["sequence_length"]
    matrix = target["X24"]
    indices_all = target["I24"]
    mask_all = target["M24"]
    labels_all = target["y24"]
    scores = np.zeros(len(labels_all), dtype=np.float32)
    seen = np.zeros(len(labels_all), dtype=bool)
    batch_sequences = 2048
    model.eval()
    with torch.no_grad():
        for start in range(0, len(indices_all), batch_sequences):
            stop = min(start + batch_sequences, len(indices_all))
            indices = np.ascontiguousarray(indices_all[start:stop, :length])
            valid = np.ascontiguousarray(mask_all[start:stop, :length] > 0.5)
            raw = np.asarray(matrix[indices.reshape(-1)], dtype=np.float32)
            values = transform.apply(raw).reshape(
                indices.shape[0], indices.shape[1], transform.output_dimension
            )
            values_t = torch.from_numpy(values).to(device)
            valid_t = torch.from_numpy(valid).to(device)
            with precision.autocast_context(profile, device.type, torch):
                probabilities = model.flow_probability(values_t, valid_t)
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
    留痕。上传前先机械核对目的地与冻结配置逐字相同。
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
            "protocol": "tabular_resnet_paper_recipe_protocol_a",
            "parameter_count": EXPECTED_PARAMETER_COUNT,
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
        metrics[f"target/{cell}_flow_roc_auc"] = cell_target["flow_roc_auc"]
        metrics[f"target/{cell}_entity_ap"] = cell_target["entity_average_precision"]
        metrics[f"target/{cell}_maximum_entity_ap"] = cell_target[
            "maximum_entity_average_precision"
        ]
        for key, value in cell_target["dr_at_fpr"].items():
            metrics[f"target/{cell}_dr_{key}"] = value
        for key, value in cell_target["dr_at_fpr_realized"].items():
            metrics[f"target/{cell}_realized_{key}"] = value
    metrics["resource/training_wall_seconds"] = result["resource"]["training_wall_seconds_sum"]
    metrics["resource/evaluation_wall_seconds"] = result["resource"]["evaluation_wall_seconds_sum"]
    metrics["resource/peak_gpu_allocated_mib"] = result["resource"]["peak_gpu_allocated_mib"]
    metrics["resource/peak_process_rss_mib"] = result["resource"]["peak_process_rss_mib"]
    metrics["resource/gpu_hours"] = result["resource"]["gpu_hours"]
    metrics["resource/parameter_count"] = float(result["resource"]["parameter_count"])
    swanlab.log(metrics, step=0)
    swanlab.finish()
    _atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-tabular-resnet-paper-recipe-protocol-a-swanlab-receipt-v1",
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
# 命令行入口与四个生产阶段
# ---------------------------------------------------------------------------


def load_json(path: Path) -> dict[str, Any]:
    """读取 JSON 文件并要求顶层是对象。"""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="全容量表格 ResNet 骨干专属论文配方协议 A 四格实验入口"
    )
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


def _prepare_source_stage(
    config: dict[str, Any],
    args: argparse.Namespace,
    on_receipt_verified: Any = None,
) -> dict[str, Any]:
    """三个源年阶段共用的前置：收据核验、运行身份、数组、切分与有效流掩码。

    只读取 LSPR23；不触碰任何 LSPR24 数组。

    收据核验放在最前，且在其通过之后才调用 ``on_receipt_verified``（各阶段用它写
    运行状态）：这样收据缺失时不会先建出运行输出目录，本机无网络盘挂载时也不会
    报出误导性的目录创建失败；同时状态文件仍然早于数分钟的数组加载与切分落盘。
    """
    config_path = Path(args.config).resolve()
    cache_root = Path(config["paths"]["cache_root"])
    receipt_path = Path(config["paths"]["field_cardinality_receipt"])

    receipt = load_cardinality_receipt(str(receipt_path), config)
    if on_receipt_verified is not None:
        on_receipt_verified()
    run_identity, source_inventory = build_run_identity(config_path, cache_root, receipt_path)
    arrays = load_source_arrays(str(cache_root))
    train_rows, validation_rows, split_statistics = source_split(arrays, config)
    train_flow_mask, flow_mapping = build_effective_flow_mask(
        arrays["I23"], arrays["M23"], train_rows, LSPR23_FLOW_COUNT
    )
    if (
        flow_mapping["effective_flow_mask_sha256"]
        != receipt["training_effective_flows"]["effective_flow_mask_sha256"]
    ):
        raise RuntimeError("本工具独立重算的训练有效流掩码与收据登记的哈希不一致，拒绝继续")
    return {
        "config_path": config_path,
        "cache_root": cache_root,
        "receipt_path": receipt_path,
        "receipt": receipt,
        "run_identity": run_identity,
        "source_inventory": source_inventory,
        "arrays": arrays,
        "train_rows": train_rows,
        "validation_rows": validation_rows,
        "split_statistics": split_statistics,
        "train_flow_mask": train_flow_mask,
        "flow_mapping": flow_mapping,
    }


def run_select_input_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段一：训练每个已准入输入候选各自的 C00（固定阶段一优化器），封印胜出输入接口。

    并列裁决固定为冻结候选表的第一个；只用
    ``lspr23_entity_disjoint_validation_flow_ap`` 决策，不看实体 AP、告警预算、
    训练时间、显存或 LSPR24（``selection_stages.forbidden_tie_breakers``）。

    候选二 ``source-quantile-83`` 受「仅在有全文或官方依据支持时比较」的准入条件
    约束：证据不全时该候选被跳过，缺项与理由写进封印，**不以任何猜测数值补齐**。
    候选一无准入条件恒参与，因此准入清单不会为空，也不存在「以默认输入替代」。
    """
    import time

    output_root = Path(config["paths"]["output_root"])
    seal_path = output_root / "input_selection_sealed.json"

    if seal_path.is_file():
        if not args.resume:
            raise RuntimeError(f"全新运行（未传 --resume）已存在输入接口封印，拒绝覆盖：{seal_path}")
        logger.info("阶段一封印已存在且传了 --resume，直接复用：%s", seal_path)
        return

    # 先做纯标准库的候选准入裁定与收据核验，再写运行状态：避免在证据或收据缺失时
    # 仍尝试建立运行输出目录。
    admitted, quantile_resolution = admitted_input_candidates(config)
    prepared = _prepare_source_stage(
        config, args,
        lambda: write_status(
            output_root, "running", "select-input", None,
            f"训练 {len(admitted)} 个已准入输入候选各自的 C00 以选择输入接口",
        ),
    )

    fixed_optimizer = config["selection_stages"]["stage_one_fixed_optimizer"]
    if fixed_optimizer != OPTIMIZER_CANDIDATES[0]["key"]:
        raise RuntimeError(
            f"阶段一固定优化器必须是冻结候选表第一个 {OPTIMIZER_CANDIDATES[0]['key']}，"
            f"实际 {fixed_optimizer}"
        )
    device = _resolve_device()
    runs: dict[str, Any] = {}
    for candidate in admitted:
        key = candidate["key"]
        run_root = output_root / "selection-runs" / "select-input" / key
        transform = fit_input_transform(
            key, str(prepared["cache_root"]), prepared["train_flow_mask"], prepared["receipt"],
            config=config, quantile_resolution=quantile_resolution,
            seed=config["training"]["seed"],
        )
        view = ProtocolASourceView(prepared["arrays"], transform)
        identity = cell_identity(
            prepared["run_identity"], input_candidate=key,
            optimizer_candidate=fixed_optimizer, cell="C00",
        )
        selection = train_cell(
            config, "C00", key, fixed_optimizer,
            output_root=run_root, identity=identity, view=view,
            train_rows=prepared["train_rows"], validation_rows=prepared["validation_rows"],
            device=device, resume=args.resume,
        )
        runs[key] = {
            "identity": identity,
            "display_name": candidate["display_name"],
            "input_dimension": transform.output_dimension,
            "parameter_count": expected_parameter_count(),
            "input_transform_receipt": transform.receipt(),
            "selection": selection,
        }
        logger.info(
            "阶段一 %s（%s）训练完成：验证逐流AP=%.8f",
            key, candidate["display_name"], selection["validation_flow_ap"],
        )

    ordered_keys = [candidate["key"] for candidate in admitted]
    metric_values = {
        key: float(runs[key]["selection"]["validation_flow_ap"]) for key in ordered_keys
    }
    best_key = ordered_keys[0]
    for key in ordered_keys[1:]:
        if metric_values[key] > metric_values[best_key]:
            best_key = key
    if len(ordered_keys) == 1:
        reason = (
            f"仅候选 {best_key} 通过准入并有效（验证逐流AP={metric_values[best_key]!r}），"
            f"候选二未准入原因：{quantile_resolution['blocked_reason']}"
        )
    elif sum(1 for key in ordered_keys if metric_values[key] == metric_values[best_key]) > 1:
        reason = (
            f"多个候选验证逐流AP并列={metric_values[best_key]!r}，"
            f"按冻结候选表固定顺序取 {best_key}"
        )
    else:
        reason = (
            f"候选 {best_key} 验证逐流AP={metric_values[best_key]!r} 严格高于其余候选："
            f"{ {key: metric_values[key] for key in ordered_keys if key != best_key} }"
        )

    seal = {
        "schema_version": "ch3-tabular-resnet-input-selection-sealed-v1",
        "run_id": RUN_ID,
        "identity": prepared["run_identity"],
        "source_data_inventory": prepared["source_inventory"],
        "source_split": prepared["split_statistics"],
        "cardinality_receipt_flow_mapping": prepared["flow_mapping"],
        "fixed_optimizer_candidate": fixed_optimizer,
        "frozen_input_candidates": [dict(entry) for entry in INPUT_CANDIDATES],
        "quantile_candidate_admission": quantile_resolution,
        "admitted_candidate_keys": ordered_keys,
        "skipped_candidate_keys": [
            candidate["key"] for candidate in INPUT_CANDIDATES if candidate["key"] not in ordered_keys
        ],
        "runs": runs,
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_metric_full_precision": metric_values,
        "tie_break_rule": "fixed_table_order",
        "forbidden_tie_breakers": list(config["selection_stages"]["forbidden_tie_breakers"]),
        "selected_candidate": best_key,
        "selection_reason": reason,
        "target_year_arrays_read": 0,
        "sealed_at_unix": time.time(),
    }
    _atomic_json(seal_path, seal)
    write_status(output_root, "running", "select-input", 0, f"输入接口已封印：{best_key}")
    logger.info("阶段一封印完成：胜出输入候选=%s（%s）", best_key, reason)


def run_select_optimizer_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段二：在已封印输入上训练挑战者优化器的 C00，与阶段一对应结果比较。

    不重训阶段一固定优化器：阶段一已用它在封印输入上训练过 C00，这里直接复用该
    结果做比较。完全相等或挑战者更低时取冻结候选表第一个（``resmlp-paper-logmid``，
    冻结配方 3.5 节「两者验证逐流 AP 完全相等时选择 resmlp-paper-logmid」）。
    """
    import time

    output_root = Path(config["paths"]["output_root"])
    input_seal_path = output_root / "input_selection_sealed.json"
    seal_path = output_root / "optimizer_selection_sealed.json"

    if not input_seal_path.is_file():
        raise RuntimeError(
            f"尚未完成阶段一输入接口封印，禁止进入阶段二：{input_seal_path}；"
            "请先执行 --stage select-input"
        )
    input_seal = load_json(input_seal_path)
    sealed_input_candidate = input_seal["selected_candidate"]
    fixed_optimizer_key = input_seal["fixed_optimizer_candidate"]

    if seal_path.is_file():
        if not args.resume:
            raise RuntimeError(f"全新运行（未传 --resume）已存在优化器封印，拒绝覆盖：{seal_path}")
        logger.info("阶段二封印已存在且传了 --resume，直接复用：%s", seal_path)
        return

    quantile_resolution = resolve_quantile_policy(config)
    prepared = _prepare_source_stage(
        config, args,
        lambda: write_status(
            output_root, "running", "select-optimizer", None, "在已封印输入上训练挑战者优化器的 C00"
        ),
    )
    if prepared["run_identity"] != input_seal["identity"]:
        raise RuntimeError("阶段二独立重算的运行身份与阶段一封印不符，拒绝在不同配置/代码/数据版本间比较")

    stage_two_keys = list(config["selection_stages"]["stage_two_optimizer"])
    challenger_candidates = [
        entry["key"] for entry in OPTIMIZER_CANDIDATES if entry["key"] != fixed_optimizer_key
    ]
    if stage_two_keys != [fixed_optimizer_key, *challenger_candidates]:
        raise RuntimeError("selection_stages.stage_two_optimizer 顺序与阶段一固定优化器候选不符")
    challenger_key = challenger_candidates[0]

    device = _resolve_device()
    transform = fit_input_transform(
        sealed_input_candidate, str(prepared["cache_root"]), prepared["train_flow_mask"],
        prepared["receipt"], config=config, quantile_resolution=quantile_resolution,
        seed=config["training"]["seed"],
    )
    view = ProtocolASourceView(prepared["arrays"], transform)
    challenger_identity = cell_identity(
        prepared["run_identity"], input_candidate=sealed_input_candidate,
        optimizer_candidate=challenger_key, cell="C00",
    )
    challenger_run_root = output_root / "selection-runs" / "select-optimizer" / challenger_key
    challenger_selection = train_cell(
        config, "C00", sealed_input_candidate, challenger_key,
        output_root=challenger_run_root, identity=challenger_identity, view=view,
        train_rows=prepared["train_rows"], validation_rows=prepared["validation_rows"],
        device=device, resume=args.resume,
    )

    incumbent_run = input_seal["runs"][sealed_input_candidate]
    incumbent_ap = float(incumbent_run["selection"]["validation_flow_ap"])
    challenger_ap = float(challenger_selection["validation_flow_ap"])
    if challenger_ap > incumbent_ap:
        best_key = challenger_key
        reason = f"挑战者（{challenger_key}）验证逐流AP={challenger_ap!r} 严格高于 {incumbent_ap!r}"
    elif challenger_ap == incumbent_ap:
        best_key = fixed_optimizer_key
        reason = (
            f"两优化器候选验证逐流AP并列={incumbent_ap!r}，"
            f"按冻结配方3.5节取候选表第一个 {fixed_optimizer_key}"
        )
    else:
        best_key = fixed_optimizer_key
        reason = f"候选一（{fixed_optimizer_key}）验证逐流AP={incumbent_ap!r} 高于挑战者 {challenger_ap!r}"

    seal = {
        "schema_version": "ch3-tabular-resnet-optimizer-selection-sealed-v1",
        "run_id": RUN_ID,
        "identity": prepared["run_identity"],
        "sealed_input_candidate": sealed_input_candidate,
        "frozen_optimizer_candidates": list(config["optimizer_candidates"]),
        "runs": {
            fixed_optimizer_key: incumbent_run,
            challenger_key: {"identity": challenger_identity, "selection": challenger_selection},
        },
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_metric_full_precision": {
            fixed_optimizer_key: incumbent_ap,
            challenger_key: challenger_ap,
        },
        "tie_break_rule": "frozen_recipe_section_3_5_first_table_row_on_tie_or_loss",
        "forbidden_tie_breakers": list(config["selection_stages"]["forbidden_tie_breakers"]),
        "selected_candidate": best_key,
        "selection_reason": reason,
        "target_year_arrays_read": 0,
        "sealed_at_unix": time.time(),
    }
    _atomic_json(seal_path, seal)
    write_status(output_root, "running", "select-optimizer", 0, f"优化器已封印：{best_key}")
    logger.info("阶段二封印完成：胜出优化器候选=%s（%s）", best_key, reason)


def run_cells_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段三：用已封印的输入与优化器训练 C00/C01/C10/C11，全部完成后写选择封印。

    C00 只有在配置、代码、数据、字段基数收据与检查点身份完全一致时才复用阶段一或
    阶段二的完成运行；任一不符都以新运行身份在最终输出根重训，不做部分拼接。
    """
    import time

    output_root = Path(config["paths"]["output_root"])
    input_seal_path = output_root / "input_selection_sealed.json"
    optimizer_seal_path = output_root / "optimizer_selection_sealed.json"
    selection_frozen_path = output_root / "selection_frozen.json"

    if not input_seal_path.is_file() or not optimizer_seal_path.is_file():
        raise RuntimeError(
            "尚未完成阶段一与阶段二封印，禁止进入 cells 阶段："
            f"输入封印存在={input_seal_path.is_file()}，优化器封印存在={optimizer_seal_path.is_file()}；"
            "请先依次执行 --stage select-input 与 --stage select-optimizer"
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

    quantile_resolution = resolve_quantile_policy(config)
    prepared = _prepare_source_stage(
        config, args,
        lambda: write_status(output_root, "running", "cells", None, "训练协议 A 四格并封印选择"),
    )
    if (
        prepared["run_identity"] != input_seal["identity"]
        or prepared["run_identity"] != optimizer_seal["identity"]
    ):
        raise RuntimeError("cells 阶段独立重算的运行身份与阶段一或阶段二封印不符")

    device = _resolve_device()
    transform = fit_input_transform(
        sealed_input_candidate, str(prepared["cache_root"]), prepared["train_flow_mask"],
        prepared["receipt"], config=config, quantile_resolution=quantile_resolution,
        seed=config["training"]["seed"],
    )
    view = ProtocolASourceView(prepared["arrays"], transform)
    save_input_transform(output_root / "artifacts" / "sealed-input-transform.pkl", transform)

    reused_c00_source = optimizer_seal["runs"].get(sealed_optimizer_candidate)
    selections: dict[str, Any] = {}
    for cell in CELL_ORDER:
        identity = cell_identity(
            prepared["run_identity"], input_candidate=sealed_input_candidate,
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
        logger.info(
            "开始 %s 协议 A 训练与选择（输入=%s，优化器=%s）",
            cell, sealed_input_candidate, sealed_optimizer_candidate,
        )
        selections[cell] = train_cell(
            config, cell, sealed_input_candidate, sealed_optimizer_candidate,
            output_root=output_root, identity=identity, view=view,
            train_rows=prepared["train_rows"], validation_rows=prepared["validation_rows"],
            device=device, resume=args.resume,
        )

    optimizer_candidate_record = next(
        entry for entry in config["optimizer_candidates"] if entry["key"] == sealed_optimizer_candidate
    )
    cell_hashes: dict[str, Any] = {}
    for cell in CELL_ORDER:
        selection = selections[cell]
        cell_hashes[cell] = {
            "checkpoint_sha256": selection["checkpoint"]["sha256"],
            "config_sha256": prepared["run_identity"]["config_sha256"],
            "code_sha256": prepared["run_identity"]["code_sha256"],
            "optimizer_candidate_sha256": _canonical_sha256(optimizer_candidate_record),
            "random_state": {"seed": config["training"]["seed"]},
            "elp_parameter_p_at_selection": selection["p_at_selection"],
            "aggregation_rule": (
                "逐流 sigmoid 概率"
                + ("，再对唯一实体做共享标量p的可学幂平均池化(ELP)" if CELLS[cell]["learned_lp_pooling"] else "，实体聚合取最大池化")
            ),
        }

    sample_order_sha256 = _canonical_sha256(
        {
            "train_rows": prepared["train_rows"].tolist(),
            "validation_rows": prepared["validation_rows"].tolist(),
        }
    )
    seal = {
        "schema_version": "ch3-tabular-resnet-selection-frozen-v1",
        "run_id": RUN_ID,
        "model_key": MODEL_KEY,
        "display_name": config["display_name"],
        "frozen_recipe_sha256": FROZEN_RECIPE_SHA256,
        "identity": prepared["run_identity"],
        "architecture": config["architecture"],
        "input_candidates": [dict(entry) for entry in INPUT_CANDIDATES],
        "optimizer_candidates": list(config["optimizer_candidates"]),
        "field_groups": config["field_groups"],
        "dijk_feature_count": DIJK_FEATURE_COUNT,
        "lspr23_flow_count": LSPR23_FLOW_COUNT,
        "source_data_inventory": prepared["source_inventory"],
        "source_split": prepared["split_statistics"],
        "sample_order_sha256": sample_order_sha256,
        "cardinality_receipt_sha256": prepared["run_identity"]["cardinality_receipt_sha256"],
        "input_selection": input_seal,
        "optimizer_selection": optimizer_seal,
        "sealed_input_candidate": sealed_input_candidate,
        "sealed_optimizer_candidate": sealed_optimizer_candidate,
        "sealed_input_transform_receipt": transform.receipt(),
        "input_dimension": transform.output_dimension,
        "parameter_count": expected_parameter_count(),
        "parameter_count_decomposition": parameter_count_decomposition(),
        "cells": selections,
        "cell_hashes": cell_hashes,
        "all_four_cells_sealed": True,
        "target_year_arrays_read": 0,
        "target_evaluation_calls": 0,
        "sealed_at_unix": time.time(),
    }
    _atomic_json(selection_frozen_path, seal)
    write_status(output_root, "computed", "cells", 0, "四格训练与选择封印完成，等待目标年评价")
    build_manifest(output_root, RUN_ID)
    logger.info("四格选择封印完成：%s", selection_frozen_path)


def run_evaluate_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段四：四格全部封印后的目标年评价，每格恰好评价一次，四格合计恰好 4 次。

    输入变换只应用已封印的训练区状态，绝不在 LSPR24 上重新拟合；评价阶段全程
    ``torch.no_grad()``，不训练、不替换检查点、不搜索阈值、不更新聚合指数或任何
    超参数。六档检出率同时给出实际可达 FPR，名义工作点越出预算时写警告并记录真实值。
    """
    output_root = Path(config["paths"]["output_root"])
    cache_root = Path(config["paths"]["cache_root"])
    selection_frozen_path = output_root / "selection_frozen.json"

    # 先做纯标准库的封印存在性核验，numpy/torch/sklearn 延后到确认要做真实评价工作
    # 之后才导入，使本阶段在缺依赖或尚未完成上游阶段的开发机上也能给出清晰的中文错误。
    if not selection_frozen_path.is_file():
        raise RuntimeError(
            f"四格选择尚未封印，禁止加载 LSPR24：{selection_frozen_path}；"
            "请先依次执行 --stage select-input、--stage select-optimizer 与 --stage cells"
        )
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
    if transform.candidate_key != seal["sealed_input_candidate"]:
        raise RuntimeError("已封印输入变换的候选身份与选择封印不符")
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

        model = build_model(
            config, cell, seal["sealed_input_candidate"], seal["input_dimension"]
        ).to(device)
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
            evaluation_peak_gpu_mib = max(
                evaluation_peak_gpu_mib, torch.cuda.max_memory_allocated(device) / 2**20
            )

        main_p = selected_p if CELLS[cell]["learned_lp_pooling"] else None
        main_entity_scores = entity_scores(flow_scores, seen, flow_entity, entity_count, main_p)
        maximum_entity_scores = entity_scores(flow_scores, seen, flow_entity, entity_count, None)
        valid_entity = np.isfinite(main_entity_scores)
        valid_maximum = np.isfinite(maximum_entity_scores)
        main_table = dr_at_fpr_table(main_entity_scores, entity_labels, "dr_at_fpr")
        maximum_table = dr_at_fpr_table(
            maximum_entity_scores, entity_labels, "maximum_dr_at_fpr"
        )
        metrics = {
            "flow_average_precision": float(
                average_precision_score(target["y24"][seen], flow_scores[seen])
            ),
            "flow_roc_auc": float(roc_auc_score(target["y24"][seen], flow_scores[seen])),
            "entity_average_precision": float(
                average_precision_score(entity_labels[valid_entity], main_entity_scores[valid_entity])
            ),
            "maximum_entity_average_precision": float(
                average_precision_score(
                    entity_labels[valid_maximum], maximum_entity_scores[valid_maximum]
                )
            ),
            **main_table,
            **maximum_table,
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
            "input_transform_receipt": transform.receipt(),
        }
        save_target_evaluation(output_root, cell, target_identity, cell_result, curve)
        cells[cell] = cell_result
        logger.info(
            "%s 目标评价（第 %d 次调用）：逐流AP=%.8f 实体AP=%.8f 计分流=%d 用时=%.1f 分",
            cell, metrics["target_evaluation_call"], metrics["flow_average_precision"],
            metrics["entity_average_precision"], metrics["flows_scored"],
            evaluation_seconds / 60.0,
        )
        del model, checkpoint, flow_scores, seen, main_entity_scores, maximum_entity_scores
        if device.type == "cuda":
            torch.cuda.empty_cache()

    total_calls = evaluation_calls_this_process + evaluation_receipts_reused
    if len(cells) != 4 or total_calls != 4 or target_load_count != 1:
        raise RuntimeError(
            f"目标年加载或四格评价次数不符：cells={len(cells)} calls={total_calls} loads={target_load_count}"
        )

    curve_path = output_root / "complete-alert-budget-curves.npz"
    temporary_curve = curve_path.with_name(f"{curve_path.name}.partial.{os.getpid()}")
    with temporary_curve.open("wb") as handle:
        np.savez_compressed(handle, **curve_arrays)
    os.replace(temporary_curve, curve_path)
    curve_receipt = {
        "schema_version": "ch3-tabular-resnet-complete-alert-budget-curves-v1",
        "artifact": {
            "filename": curve_path.name,
            "bytes": curve_path.stat().st_size,
            "sha256": _sha256_file(curve_path),
        },
        "cells": list(CELL_ORDER),
        "fields": ["n_false_positive_entity", "nominal_fpr", "realized_fpr", "detection_rate"],
        "curve_is_complete_over_all_reachable_negative_entity_budgets": True,
        "per_flow_scores_persisted": False,
        "per_entity_scores_persisted": False,
    }
    _atomic_json(output_root / "complete-alert-budget-curves-receipt.json", curve_receipt)

    interaction: dict[str, Any] = {}
    for name in (
        "flow_average_precision",
        "entity_average_precision",
        "maximum_entity_average_precision",
    ):
        values = {cell: cells[cell]["target"][name] for cell in CELL_ORDER}
        interaction[name] = {
            **values,
            "causal_prefix_effect": values["C10"] - values["C00"],
            "elp_effect": values["C01"] - values["C00"],
            "combined_effect": values["C11"] - values["C00"],
            "interaction": values["C11"] - values["C10"] - values["C01"] + values["C00"],
        }
    for grid_key in (f"fpr_{value:g}" for value in DR_FPR_GRID):
        values = {cell: cells[cell]["target"]["dr_at_fpr"][grid_key] for cell in CELL_ORDER}
        interaction[f"dr_at_fpr.{grid_key}"] = {
            **values,
            "causal_prefix_effect": values["C10"] - values["C00"],
            "elp_effect": values["C01"] - values["C00"],
            "combined_effect": values["C11"] - values["C00"],
            "interaction": values["C11"] - values["C10"] - values["C01"] + values["C00"],
        }

    training_seconds_sum = sum(float(seal["cells"][cell]["training_seconds"]) for cell in CELL_ORDER)
    evaluation_seconds_sum = sum(
        float(cells[cell]["target"]["evaluation_seconds"]) for cell in CELL_ORDER
    )
    launcher_resource = load_json(Path(args.resource_receipt)) if args.resource_receipt else None
    peak_gpu_candidates = [evaluation_peak_gpu_mib] + [
        float(seal["cells"][cell]["peak_gpu_allocated_mib"] or 0.0) for cell in CELL_ORDER
    ]
    result = {
        "schema_version": "ch3-tabular-resnet-paper-recipe-protocol-a-results-v1",
        "run_id": RUN_ID,
        "model": {
            "model_key": MODEL_KEY,
            "display_name": config["display_name"],
            **config["architecture"],
            "sealed_input_candidate": seal["sealed_input_candidate"],
            "sealed_optimizer_candidate": seal["sealed_optimizer_candidate"],
            "input_dimension": seal["input_dimension"],
            "parameter_count": seal["parameter_count"],
            "parameter_count_decomposition": seal["parameter_count_decomposition"],
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
    except Exception:
        logger.exception("阶段执行失败：%s", args.stage)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
