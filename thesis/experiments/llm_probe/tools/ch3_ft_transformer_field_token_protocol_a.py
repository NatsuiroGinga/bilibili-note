# -*- coding: utf-8 -*-
"""FT-Transformer 逐字段 Token 协议 A 四格实验工具（任务 1 至 3）。

本文件目前实现：

- 任务 1：运行身份与结构冻结常量、配置校验 ``validate_config``、命令行入口与四个
  阶段的分发骨架。
- 任务 2：字段基数收据消费 ``load_cardinality_receipt``、Token 布局与参数量闭式
  ``expected_parameter_count``，以及逐字段 Token 输入变换 ``fit_input_transform`` /
  ``FieldTokenTransform``（数值线性 Token 的分位数变换与二值直通、离散字段训练区词表
  加越界桶）。
- 任务 3：特征标记器 ``FeatureTokenizer``、多头注意力 ``MultiheadAttention``、
  Pre-Norm 块堆叠 ``TransformerBlocks``、FT-Transformer 主干 ``FTTransformerFieldToken``、
  整向量投影同参数对照 ``WholeVectorProjectionControl``，以及宽度对位搜索
  ``solve_control_token_width`` 与参数量三方比对 ``build_model`` / ``build_control_model``。

``select-input``、``select-optimizer``、``cells``、``evaluate`` 四个阶段的编排、训练
循环、断点恢复、选择封印与目标年评价由任务 4 与任务 5 继续叠加，本文件只为它们预留
分发位置，并在生产路径上显式抛错而不是静默通过。

结构依据：官方仓库 ``yandex-research/rtdl-revisiting-models`` 固定提交
``e3ed46cac38568785289d8fa16b8cfa585bde27e``（Apache-2.0）的 ``bin/ft_transformer.py``、
``lib/deep.py`` 与 ``lib/data.py``；默认配方取自同一提交的
``output/adult/ft_transformer/default/0.toml``，调参空间取自
``output/*/ft_transformer/tuning/0.toml``。逐条对应关系写在各常量与类的注释中。

精度合同：本运行走 RTX 5090 神经训练默认配置 ``cuda-bf16-amp-fp32-sensitive-v1``
（BF16 autocast、参数与优化器状态保持 FP32、敏感计算进 FP32 岛、不用 GradScaler），
经 ``tools/neural_precision_runtime.py`` 接入，不自建第二套精度、累积或收据实现。
注意力的 ``softmax`` 属精度合同登记的敏感计算，在本文件的注意力实现里进 FP32 岛。

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

# 允许以 `python tools/ch3_ft_transformer_field_token_protocol_a.py` 之外的方式调用时
# 仍能找到同目录的 neural_precision_runtime，与仓库既有工具同一写法。
TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

# ---------------------------------------------------------------------------
# 运行身份与协议 A 冻结常量
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "ch3-ft-transformer-field-token-protocol-a-config-v1"
RUN_ID = "ch3-ft-transformer-field-token-protocol-a-seed42-v1"
MODEL_KEY = "ft-transformer-field-token"
DISPLAY_NAME = "FT-Transformer逐字段Token协议A四格"

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

STAGE_CHOICES: tuple[str, ...] = ("select-input", "select-optimizer", "cells", "evaluate")

# ---------------------------------------------------------------------------
# 官方源码归档凭据（只登记可追溯凭据，本模块不读取也不执行上游源码）
# ---------------------------------------------------------------------------

OFFICIAL_REPOSITORY = "yandex-research/rtdl-revisiting-models"
OFFICIAL_COMMIT = "e3ed46cac38568785289d8fa16b8cfa585bde27e"
OFFICIAL_LICENSE = "Apache-2.0"
OFFICIAL_STRUCTURE_FILE = "bin/ft_transformer.py"
OFFICIAL_STRUCTURE_SHA256 = "2eddb24549aa322840f1e699b80b3ed9137bba2032592c333ad34998310326b3"
OFFICIAL_LICENSE_SHA256 = "bd39fcc730a79d256b14fcdccbfc8ac9f0c7fad4a2e8d01fc513def67980fe35"
OFFICIAL_DEFAULT_RECIPE_FILE = "output/adult/ft_transformer/default/0.toml"
OFFICIAL_TUNING_SPACE_FILE = "output/higgs_small/ft_transformer/tuning/0.toml"
OFFICIAL_VENDOR_DIRECTORY = "thesis/experiments/llm_probe/vendor/ft_transformer"

# ---------------------------------------------------------------------------
# 结构冻结常量（逐项对应官方默认配方 output/adult/ft_transformer/default/0.toml）
# ---------------------------------------------------------------------------

# 官方默认配方 [model] 段逐字：n_layers=3、d_token=192、n_heads=8、
# d_ffn_factor=1.333333333333333、activation='reglu'、attention_dropout=0.2、
# ffn_dropout=0.1、residual_dropout=0.0、initialization='kaiming'、prenormalization=true。
N_LAYERS = 3
D_TOKEN = 192
N_HEADS = 8
# 本运行按实施计划与看板裁决取精确的 4/3；官方 TOML 写的是十进制字面量
# 1.333333333333333（15 个 3），二者在 d_token=192 处的 int() 结果不同，
# 差异与证据见 OFFICIAL_LITERAL_D_FFN_FACTOR 与 ffn_factor_rounding_diagnostic。
D_FFN_FACTOR = 4 / 3
ACTIVATION = "reglu"
ATTENTION_DROPOUT = 0.2
FFN_DROPOUT = 0.1
RESIDUAL_DROPOUT = 0.0
INITIALIZATION = "kaiming"
PRENORMALIZATION = True
# 论文 PDF 第 4 至 5 页与附录 E.1 第 17 页：Pre-Norm 下首块去掉第一处归一化。
# 官方第 223 行 ``if not prenormalization or layer_idx:`` 只在 layer_idx>0 时建 norm0。
FIRST_BLOCK_SKIPS_FIRST_NORMALIZATION = True
# 官方第 42 至 43 行：weight 形状为 (d_numerical+1, d_token)，第 0 行即 [CLS]，
# 不单独设参数；bias 形状为 (d_numerical+len(categories), d_token)，[CLS] 无偏置。
TOKEN_BIAS = True
CLS_SHARES_TOKENIZER_WEIGHT_ROW_ZERO = True
# 官方第 89 至 92 行：W_q/W_k/W_v/W_out 均为 nn.Linear(d, d)，默认 bias=True。
ATTENTION_PROJECTION_BIAS = True
D_OUT = 1

# 官方 TOML 中 d_ffn_factor 的十进制字面量。int(192*1.333333333333333)==255，
# 而 int(192*(4/3))==256，两者相差一格前馈宽度、每层相差 (3d+2)=578 个参数。
OFFICIAL_LITERAL_D_FFN_FACTOR = 1.333333333333333

# 官方调参空间 output/*/ft_transformer/tuning/0.toml 的 d_token 上下界，
# 用作整向量投影对照的宽度搜索区间，避免自造搜索范围。
OFFICIAL_D_TOKEN_SEARCH_LOWER = 64
OFFICIAL_D_TOKEN_SEARCH_UPPER = 512

# ---------------------------------------------------------------------------
# 字段策略常量（Codex 2026-08-21 15:55 CST 看板裁决，已定死，不再是待裁开关）
# ---------------------------------------------------------------------------

# 裁决原文要点：SrcPort、DstPort 保持训练区数值表示；Protocol、L3/L4 Protocol 用
# 只由 LSPR23 训练区拟合的词表加越界桶；Int/Ext Dst IP、External_src、External_dst
# 依据 TabM 论文二值规则按 {0,1} 直通，不另建三行词表，并同样视为数值 Token。
# 三个二元字段仍各自形成一个 Token，只是数值化口径是 {0,1} 直通而不是分位数变换。
VOCABULARY_TOKEN_FIELDS: tuple[str, ...] = ("Protocol", "L3/L4 Protocol")
ZERO_ONE_PASSTHROUGH_FIELDS: tuple[str, ...] = (
    "Int/Ext Dst IP",
    "External_src",
    "External_dst",
)
# 收据里出现的七个字段中，走分位数变换的两个（其余 76 个数值字段不在收据里）。
RECEIPT_QUANTILE_TREATED_FIELDS: tuple[str, ...] = ("SrcPort", "DstPort")

DIJK_FEATURE_COUNT = 83
NUMERIC_TOKEN_FIELD_COUNT = 81
VOCABULARY_TOKEN_FIELD_COUNT = 2
TOKEN_COUNT_INCLUDING_CLS = 84

# 冻结缓存的形状身份，与既有协议 A 工具逐字一致。
LSPR23_FLOW_COUNT = 16_353_511
LSPR23_SEQUENCE_COUNT = 271_815
PROTOCOL_A_SEQUENCE_LENGTH = 128
PROTOCOL_A_SPLIT_STATISTICS: dict[str, int] = {
    "entity_count": 150_680,
    "train_sequences": 208_598,
    "validation_sequences": 22_444,
    "train_validation_row_intersection": 0,
}

# ---------------------------------------------------------------------------
# 官方数值预处理常量（lib/data.py 的 normalize 与 build_X，非 TabM 的 NOISY_QUANTILE）
# ---------------------------------------------------------------------------

# lib/data.py 第 26 至 38 行：output_distribution='normal'、
# n_quantiles=max(min(n//30, 1000), 10)、subsample=1e9、random_state=seed；
# 拟合前叠加相对噪声 noise_std = 1e-3 / max(列标准差, 1e-3)。
# 与 TabM 的 NOISY_QUANTILE（绝对噪声 1e-5）不同，本工具按 FT-Transformer 自己的配方。
QUANTILE_OUTPUT_DISTRIBUTION = "normal"
QUANTILE_SUBSAMPLE = 1_000_000_000
QUANTILE_ROWS_PER_LANDMARK = 30
QUANTILE_LANDMARK_MAXIMUM = 1000
QUANTILE_LANDMARK_MINIMUM = 10
QUANTILE_RELATIVE_NOISE = 1e-3
# lib/data.py 第 133 至 141 行：数值缺失按训练区 np.nanmean 填补，且在规范化之前。
NUMERIC_NAN_POLICY = "training_region_mean"
# 生成拟合噪声时的单次抽取元素数，只为限制 float64 临时缓冲，不改变分布。
QUANTILE_NOISE_CHUNK_ELEMENTS = 4_194_304
# 组装式变换器的实现漂移绊线，不是科学阈值：地标数 n 时中位数附近概率间距为 1/(n-1)，
# 标准正态分位函数在 p=0.5 处斜率 sqrt(2*pi)≈2.5066，n=1000 时插值位移解析上界约 2.5e-3；
# 下列容差约为该上界的 40 倍，只在 sklearn 私有属性语义实质改变时触发。
QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE = 0.1

# ---------------------------------------------------------------------------
# 输入候选与优化器候选
# ---------------------------------------------------------------------------

INPUT_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "order": 1,
        "display_name": "FT-Transformer-全字段数值Token输入",
        "key": "ft-transformer-input-all-numeric-token",
        "numeric_token_field_count": 83,
        "vocabulary_token_field_count": 0,
        "vocabulary_total_columns": 0,
        "token_count": TOKEN_COUNT_INCLUDING_CLS,
        # 参数量由运行时按闭式实算并与实际 sum(p.numel()) 三方比对，不在此写死。
        "parameter_count": None,
    },
    {
        "order": 2,
        "display_name": "FT-Transformer-协议字段词表Token输入",
        "key": "ft-transformer-input-protocol-vocabulary-token",
        "numeric_token_field_count": NUMERIC_TOKEN_FIELD_COUNT,
        "vocabulary_token_field_count": VOCABULARY_TOKEN_FIELD_COUNT,
        # 词表总列数由训练区实测基数决定（含越界桶），拟合前从收据预算。
        "vocabulary_total_columns": None,
        "token_count": TOKEN_COUNT_INCLUDING_CLS,
        "parameter_count": None,
    },
)

OPTIMIZER_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "order": 1,
        "display_name": "FT-Transformer-论文默认优化器",
        "key": "ft-transformer-official-default",
        "optimizer": "adamw",
        "learning_rate": 1e-4,
        "weight_decay": 1e-5,
    },
    {
        "order": 2,
        "display_name": "FT-Transformer-官方调参空间对数中位优化器",
        "key": "ft-transformer-tuning-space-logmid",
        "optimizer": "adamw",
        # sqrt(1e-05 * 1e-03) = 1e-04，与默认学习率重合（已知，不是笔误）。
        "learning_rate": 1e-4,
        # sqrt(1e-06 * 1e-03) = 3.1622776601683794e-05。
        "weight_decay": 3.1622776601683794e-05,
    },
)

# 权重衰减例外：论文表 12 明写特征标记器、LayerNorm 与偏置一律取 0.0。
WEIGHT_DECAY_EXCLUDED_ROLES: tuple[str, ...] = (
    "feature_tokenizer",
    "layer_normalization",
    "bias",
)
# 官方第 376 行的字符串规则；其对 last_normalization.weight 不生效（不含 '.norm'），
# 与论文正文不一致，本工具按论文正文语义实现并在优化器构造时记录差异清单。
OFFICIAL_WEIGHT_DECAY_STRING_RULE = "all(x not in name for x in ['tokenizer', '.norm', '.bias'])"

# ---------------------------------------------------------------------------
# 整向量投影同参数对照（对照，不是候选）
# ---------------------------------------------------------------------------

CONTROL_KEY = "whole-vector-projection-parameter-matched-control"
CONTROL_DISPLAY_NAME = "整向量投影同参数对照（非FT-Transformer）"
CONTROL_ROLE = "对照，不是候选"
CONTROL_IDENTITY_GATE_NOTE = (
    "统一合同第 111 行：把整条 83 维向量投影成单一 Token 的普通 Transformer 不能称为 "
    "FT-Transformer，其失败也不能否决该模型族"
)

# ---------------------------------------------------------------------------
# 精度合同接入常量
# ---------------------------------------------------------------------------

PRECISION_PROFILE_ID = "cuda-bf16-amp-fp32-sensitive-v1"
PRECISION_CONTRACT_FILENAME = "neural-precision-profiles-v1.json"
EFFECTIVE_BATCH_ITEM_UNIT = "sequence"
NORMALIZATION_UNIT = "flow"
PRECISION_DTYPE_BYTES: dict[str, int] = {"bfloat16": 2, "float16": 2, "float32": 4}
HOST_FEATURE_DTYPE_BYTES = 4

# Codex 2026-08-21 14:20 CST 为协议 A 神经骨干裁定的 GPU 空闲显存准入阈值（MiB）。
# 本模型的实测张量上界严格小于 TabM32，沿用同一保守下限只会更安全，不放宽。
GPU_FREE_MEMORY_MINIMUM_MIB = 20480

# ---------------------------------------------------------------------------
# validate_config 内部使用的冻结期望值
# ---------------------------------------------------------------------------

_EXPECTED_ARCHITECTURE: dict[str, Any] = {
    "n_layers": N_LAYERS,
    "d_token": D_TOKEN,
    "n_heads": N_HEADS,
    "d_ffn_factor": D_FFN_FACTOR,
    "d_ffn_hidden": 256,
    "activation": ACTIVATION,
    "attention_dropout": ATTENTION_DROPOUT,
    "ffn_dropout": FFN_DROPOUT,
    "residual_dropout": RESIDUAL_DROPOUT,
    "prenormalization": PRENORMALIZATION,
    "first_block_skips_first_normalization": FIRST_BLOCK_SKIPS_FIRST_NORMALIZATION,
    "token_bias": TOKEN_BIAS,
    "attention_projection_bias": ATTENTION_PROJECTION_BIAS,
    "initialization": INITIALIZATION,
    "d_out": D_OUT,
    "cls_shares_tokenizer_weight_row_zero": CLS_SHARES_TOKENIZER_WEIGHT_ROW_ZERO,
}

_EXPECTED_TRAINING: dict[str, Any] = {
    "seed": 42,
    "sequence_length": PROTOCOL_A_SEQUENCE_LENGTH,
    "effective_batch_size": 64,
    "effective_batch_item_unit": EFFECTIVE_BATCH_ITEM_UNIT,
    "normalization_unit": NORMALIZATION_UNIT,
    "micro_batch_sequences": 4,
    "gradient_accumulation_steps": 16,
    "epochs": 20,
    "steps_per_epoch": 1000,
    "gradient_clip_norm": None,
    "gradient_clip_policy": "official_ft_transformer_recipe_no_clipping",
    "validation_fraction": 0.1,
    "time_tail_fraction": 0.15,
    "learning_rate_schedule": "none",
    "official_recipe_patience": 16,
    "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
    "selection_rule": "single_epoch_argmax_earliest_tie_no_early_stopping",
    "stopping_rule_deviates_from_official_recipe": True,
    "stopping_rule_deviation_note": (
        "官方默认配方为耐心 16、无轮数上限；本运行取协议 A 的 20 轮跑满不早停"
        "以保持四格与跨骨干可比性"
    ),
}

_EXPECTED_SELECTION_STAGES: dict[str, Any] = {
    "stage_one_input_interface": [
        "ft-transformer-input-all-numeric-token",
        "ft-transformer-input-protocol-vocabulary-token",
    ],
    "stage_one_fixed_optimizer": "ft-transformer-official-default",
    "stage_two_optimizer": [
        "ft-transformer-official-default",
        "ft-transformer-tuning-space-logmid",
    ],
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

_EXPECTED_RESOURCE_CONTRACT: dict[str, Any] = {
    "measure_resident_bytes_after_upload": True,
    "assert_free_memory_before_model_allocation": True,
    "minimum_free_gpu_memory_mib": GPU_FREE_MEMORY_MINIMUM_MIB,
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
    "tags": ["chapter3", "ft-transformer", "field-token", "protocol-a", "2x2", "seed42", "single-run"],
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

    CUDA 无 BF16 时不静默降级，而是由 ``validate_runtime_profile`` 抛错，
    要求显式改走 FP16 回退并留硬件收据。本运行按合同只接受 CUDA BF16 默认配置。
    """
    module = _precision_module()
    resolved_contract = contract or load_precision_contract()
    profile_id = module.profile_for_device(resolved_contract, device_type)
    if profile_id != PRECISION_PROFILE_ID:
        raise RuntimeError(
            f"设备类型 {device_type} 解析出的精度配置为 {profile_id}，"
            f"本运行只接受 {PRECISION_PROFILE_ID}；非 CUDA 或无 BF16 的环境须先取得显式例外收据"
        )
    profile = module.validate_runtime_profile(resolved_contract, profile_id, device_type, torch_module)
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


def tensor_upper_bounds(
    config: dict[str, Any], token_count: int, profile: dict[str, Any]
) -> dict[str, int]:
    """按真实展开维度乘积给出单微批张量上界，不按参数量估算。

    轴约定：单微批含 ``micro_batch × sequence_length`` 条流，逐流 ``token_count``
    个 Token，宽度 ``d_token``。注意力矩阵还要乘头数与 Token 数的平方。
    softmax 在 FP32 岛内完成，因此注意力矩阵按 FP32 记保守上界。
    """
    architecture = config["architecture"]
    training = config["training"]
    micro_batch = training["micro_batch_sequences"]
    length = training["sequence_length"]
    d_token = architecture["d_token"]
    n_heads = architecture["n_heads"]
    element_bytes = compute_dtype_bytes(profile)

    flows = micro_batch * length
    token_elements = flows * token_count * d_token
    attention_elements = flows * n_heads * token_count * token_count
    hidden = ffn_hidden_size(d_token, architecture["d_ffn_factor"])
    # ReGLU 首层输出宽度翻倍，是块内最宽的中间张量。
    ffn_elements = flows * token_count * 2 * hidden
    return {
        "micro_batch_flows": flows,
        "token_tensor_bytes": token_elements * element_bytes,
        "token_tensor_fp32_bytes": token_elements * HOST_FEATURE_DTYPE_BYTES,
        "attention_matrix_fp32_bytes": attention_elements * HOST_FEATURE_DTYPE_BYTES,
        "attention_matrix_compute_dtype_bytes": attention_elements * element_bytes,
        "ffn_expanded_bytes": ffn_elements * element_bytes,
        "host_dense_numeric_bytes": flows * DIJK_FEATURE_COUNT * HOST_FEATURE_DTYPE_BYTES,
        "compute_dtype_bytes": element_bytes,
    }


# ---------------------------------------------------------------------------
# 参数量闭式（任务 2 与任务 3 共用）
# ---------------------------------------------------------------------------


def ffn_hidden_size(d_token: int, ffn_factor: float) -> int:
    """官方第 208 行 ``d_hidden = int(d_token * d_ffn_factor)``，逐字复现取整口径。"""
    return int(d_token * ffn_factor)


def feature_tokenizer_parameter_count(
    numeric_field_count: int,
    categorical_field_count: int,
    vocabulary_total_columns: int,
    d_token: int,
    token_bias: bool,
) -> int:
    """特征标记器参数量 ``d*(2F + C + 1 + sum_v)``（``token_bias`` 为真时）。

    三项分别对应官方第 42 行的 ``weight``（``(F+1)*d``，第 0 行即共享的 [CLS]）、
    第 43 行的 ``bias``（``(F+C)*d``，[CLS] 不设偏置）与类别嵌入表 ``sum_v*d``。
    """
    weight = (numeric_field_count + 1) * d_token
    bias = (numeric_field_count + categorical_field_count) * d_token if token_bias else 0
    embeddings = vocabulary_total_columns * d_token
    return weight + bias + embeddings


def transformer_block_parameter_count(d_token: int, n_layers: int, ffn_factor: float) -> int:
    """``L * (4d^2 + 5d + h*(3d+2))``，其中 ``h = int(d * ffn_factor)``。

    逐项来源：注意力四个 ``nn.Linear(d, d)`` 带偏置得 ``4d^2 + 4d``（官方第 89 至 92 行）；
    ReGLU 前馈首层 ``nn.Linear(d, 2h)`` 得 ``2dh + 2h``、次层 ``nn.Linear(h, d)`` 得
    ``hd + d``（官方第 216 至 219 行），合并为 ``h*(3d+2) + d``。两者相加即上式。
    """
    hidden = ffn_hidden_size(d_token, ffn_factor)
    per_layer = 4 * d_token * d_token + 5 * d_token + hidden * (3 * d_token + 2)
    return n_layers * per_layer


def layer_normalization_parameter_count(d_token: int, n_layers: int) -> int:
    """全部 LayerNorm 的闭式合计 ``4*d*L``。

    Pre-Norm 下每层有 ``norm1``、除首层外每层有 ``norm0``，另有一处
    ``last_normalization``，共 ``L + (L-1) + 1 = 2L`` 个 LayerNorm，每个 ``2d`` 个参数。
    """
    return 4 * d_token * n_layers


def prediction_head_parameter_count(d_token: int, d_out: int) -> int:
    """预测头 ``nn.Linear(d, d_out)`` 的 ``d_out*(d+1)``。"""
    return d_out * (d_token + 1)


def expected_parameter_count(
    numeric_field_count: int,
    categorical_field_count: int,
    vocabulary_total_columns: int,
    *,
    d_token: int = D_TOKEN,
    n_layers: int = N_LAYERS,
    ffn_factor: float = D_FFN_FACTOR,
    d_out: int = D_OUT,
    token_bias: bool = TOKEN_BIAS,
) -> int:
    """FT-Transformer 主干（无机制外接）可训练参数量闭式。

    ``Total = d*(2F + C + 1 + sum_v) + L*(4d^2 + 5d + h*(3d+2)) + 4*d*L + d_out*(d+1)``
    """
    return (
        feature_tokenizer_parameter_count(
            numeric_field_count, categorical_field_count, vocabulary_total_columns, d_token, token_bias
        )
        + transformer_block_parameter_count(d_token, n_layers, ffn_factor)
        + layer_normalization_parameter_count(d_token, n_layers)
        + prediction_head_parameter_count(d_token, d_out)
    )


def parameter_count_decomposition(
    numeric_field_count: int,
    categorical_field_count: int,
    vocabulary_total_columns: int,
    *,
    d_token: int = D_TOKEN,
    n_layers: int = N_LAYERS,
    ffn_factor: float = D_FFN_FACTOR,
    d_out: int = D_OUT,
    token_bias: bool = TOKEN_BIAS,
) -> dict[str, int]:
    """返回闭式的分项，供日志、封印与三方比对逐项对表。"""
    tokenizer = feature_tokenizer_parameter_count(
        numeric_field_count, categorical_field_count, vocabulary_total_columns, d_token, token_bias
    )
    blocks = transformer_block_parameter_count(d_token, n_layers, ffn_factor)
    norms = layer_normalization_parameter_count(d_token, n_layers)
    head = prediction_head_parameter_count(d_token, d_out)
    return {
        "feature_tokenizer": tokenizer,
        "transformer_blocks": blocks,
        "layer_normalizations": norms,
        "prediction_head": head,
        "backbone_and_head": blocks + norms + head,
        "total": tokenizer + blocks + norms + head,
        "ffn_hidden_size": ffn_hidden_size(d_token, ffn_factor),
        "token_count": numeric_field_count + categorical_field_count + 1,
    }


def control_parameter_count(
    input_dimension: int,
    *,
    d_token: int,
    n_layers: int = N_LAYERS,
    ffn_factor: float = D_FFN_FACTOR,
    d_out: int = D_OUT,
) -> int:
    """整向量投影对照的参数量闭式。

    与 FT-Transformer 主干的差别只在第一项：对照没有逐字段权重、没有嵌入表、没有
    [CLS] 拼接，而是一个 ``nn.Linear(input_dimension, d_token)``（含偏置），
    把整条向量投影成序列长度为 1 的单一 Token。块、归一化与预测头逐项相同。
    """
    projection = input_dimension * d_token + d_token
    return (
        projection
        + transformer_block_parameter_count(d_token, n_layers, ffn_factor)
        + layer_normalization_parameter_count(d_token, n_layers)
        + prediction_head_parameter_count(d_token, d_out)
    )


def ffn_factor_rounding_diagnostic(d_token: int = D_TOKEN) -> dict[str, Any]:
    """比较精确 ``4/3`` 与官方 TOML 十进制字面量在 ``int()`` 取整上的差异。

    这是本任务实测发现的口径分歧：``int(192*(4/3)) == 256`` 而
    ``int(192*1.333333333333333) == 255``，每层前馈相差 ``(3d+2)`` 个参数。
    以论文表 12 的自检基准（100 个数值特征、0 个类别特征）代入，前者得 930241、
    后者得 928507；论文自报 ``929K``，按四舍五入更接近后者。本函数只报告事实，
    不改变本运行冻结的 ``D_FFN_FACTOR``，口径改动须由 Codex 裁定。
    """
    reference_numeric_fields = 100
    exact = {
        "d_ffn_factor": D_FFN_FACTOR,
        "ffn_hidden_size": ffn_hidden_size(d_token, D_FFN_FACTOR),
        "paper_reference_total": expected_parameter_count(
            reference_numeric_fields, 0, 0, d_token=d_token, ffn_factor=D_FFN_FACTOR
        ),
    }
    literal = {
        "d_ffn_factor": OFFICIAL_LITERAL_D_FFN_FACTOR,
        "ffn_hidden_size": ffn_hidden_size(d_token, OFFICIAL_LITERAL_D_FFN_FACTOR),
        "paper_reference_total": expected_parameter_count(
            reference_numeric_fields, 0, 0, d_token=d_token, ffn_factor=OFFICIAL_LITERAL_D_FFN_FACTOR
        ),
    }
    return {
        "d_token": d_token,
        "paper_reference_numeric_field_count": reference_numeric_fields,
        "paper_self_reported_thousands": 929,
        "exact_four_thirds": exact,
        "official_toml_literal": literal,
        "frozen_choice": "exact_four_thirds",
        "frozen_choice_reason": "实施计划与看板裁决均按 4/3 冻结；字面量口径差异只作事实登记",
    }


def solve_control_token_width(
    target_total: int,
    input_dimension: int,
    *,
    n_layers: int = N_LAYERS,
    ffn_factor: float = D_FFN_FACTOR,
    d_out: int = D_OUT,
    n_heads: int = N_HEADS,
    lower_bound: int = OFFICIAL_D_TOKEN_SEARCH_LOWER,
    upper_bound: int = OFFICIAL_D_TOKEN_SEARCH_UPPER,
) -> dict[str, Any]:
    """在官方 ``d_token`` 调参区间内机械搜索使对照总参数量最接近目标的宽度。

    搜索区间取官方 ``output/*/ft_transformer/tuning/0.toml`` 的
    ``d_token = ['$d_token', 64, 512]``，不自造范围。

    同时给出两个解：

    - ``unconstrained``：只按参数量最接近选，不管头数整除；
    - ``head_divisible``：额外要求 ``d % n_heads == 0``。

    官方第 84 至 85 行在 ``n_heads > 1`` 时断言 ``d % n_heads == 0``，且 ``_reshape``
    按 ``d // n_heads`` 切头，宽度不能被头数整除时会在前向直接报形状错误。因此
    只有 ``head_divisible`` 解是可构造的；``unconstrained`` 解只作对比事实登记。
    """
    if target_total <= 0:
        raise ValueError(f"对位目标参数量必须为正，实际 {target_total}")
    if lower_bound < 1 or upper_bound < lower_bound:
        raise ValueError(f"宽度搜索区间非法：[{lower_bound}, {upper_bound}]")

    scanned: list[dict[str, Any]] = []
    for width in range(lower_bound, upper_bound + 1):
        total = control_parameter_count(
            input_dimension, d_token=width, n_layers=n_layers, ffn_factor=ffn_factor, d_out=d_out
        )
        scanned.append(
            {
                "d_token": width,
                "parameter_count": total,
                "parameter_difference": total - target_total,
                "parameter_relative_difference": (total - target_total) / target_total,
                "head_divisible": width % n_heads == 0,
            }
        )

    def _closest(entries: list[dict[str, Any]]) -> dict[str, Any]:
        if not entries:
            raise RuntimeError("宽度搜索区间内没有可行解")
        # 并列时取较小宽度，规则固定且与指标无关。
        return min(entries, key=lambda item: (abs(item["parameter_difference"]), item["d_token"]))

    unconstrained = _closest(scanned)
    divisible_entries = [item for item in scanned if item["head_divisible"]]
    head_divisible = _closest(divisible_entries)

    def _neighbours(chosen: dict[str, Any], entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ordered = sorted(entries, key=lambda item: item["d_token"])
        position = next(i for i, item in enumerate(ordered) if item["d_token"] == chosen["d_token"])
        window = ordered[max(0, position - 1) : position + 2]
        return window

    result = {
        "target_total": target_total,
        "input_dimension": input_dimension,
        "n_heads": n_heads,
        "search_lower_bound": lower_bound,
        "search_upper_bound": upper_bound,
        "search_bound_source": OFFICIAL_TUNING_SPACE_FILE,
        "unconstrained": unconstrained,
        "unconstrained_neighbours": _neighbours(unconstrained, scanned),
        "head_divisible": head_divisible,
        "head_divisible_neighbours": _neighbours(head_divisible, divisible_entries),
        "buildable": head_divisible,
        "buildable_rule": "官方第 84 至 85 行断言 d % n_heads == 0，只有满足该条件的宽度可构造",
    }
    logger.info(
        "对照宽度对位搜索：目标=%d，区间=[%d, %d]，输入维=%d；"
        "不受整除约束最优 d=%d（参数=%d，差 %+d，%+.4f%%）；"
        "受头数整除约束最优 d=%d（参数=%d，差 %+d，%+.4f%%，可构造）",
        target_total, lower_bound, upper_bound, input_dimension,
        unconstrained["d_token"], unconstrained["parameter_count"],
        unconstrained["parameter_difference"], unconstrained["parameter_relative_difference"] * 100,
        head_divisible["d_token"], head_divisible["parameter_count"],
        head_divisible["parameter_difference"], head_divisible["parameter_relative_difference"] * 100,
    )
    if not unconstrained["head_divisible"]:
        logger.warning(
            "不受约束的最优宽度 d=%d 不能被头数 %d 整除，按官方结构无法构造；"
            "对照实际采用 d=%d",
            unconstrained["d_token"], n_heads, head_divisible["d_token"],
        )
    return result


# ---------------------------------------------------------------------------
# 配置校验（任务 1）
# ---------------------------------------------------------------------------


def _validate_field_policy(config: dict[str, Any]) -> None:
    """机械核验三组字段常量覆盖全部 83 字段且互不相交。"""
    order = config.get("field_order")
    if not isinstance(order, list) or len(order) != DIJK_FEATURE_COUNT:
        raise ValueError(f"field_order 必须是长度 {DIJK_FEATURE_COUNT} 的字段顺序清单")
    if len(set(order)) != DIJK_FEATURE_COUNT:
        raise ValueError("field_order 存在重名字段，无法与张量列一一对应")

    policy = config.get("field_policy", {})
    numeric = policy.get("numeric_token_fields")
    vocabulary = policy.get("vocabulary_token_fields")
    passthrough = policy.get("binary_passthrough_fields")
    for name, value in (
        ("numeric_token_fields", numeric),
        ("vocabulary_token_fields", vocabulary),
        ("binary_passthrough_fields", passthrough),
    ):
        if not isinstance(value, list):
            raise ValueError(f"field_policy.{name} 必须是清单")
        if len(set(value)) != len(value):
            raise ValueError(f"field_policy.{name} 内部存在重复字段")

    groups = (numeric, vocabulary, passthrough)
    union: set[str] = set()
    total = 0
    for group in groups:
        if union & set(group):
            raise ValueError("字段策略三组之间存在交集，必须互不相交")
        union |= set(group)
        total += len(group)
    if total != DIJK_FEATURE_COUNT or union != set(order):
        raise ValueError(
            f"字段策略三组合计 {total} 个字段、并集 {len(union)} 个，"
            f"未恰好覆盖 field_order 的 {DIJK_FEATURE_COUNT} 个字段"
        )

    if list(vocabulary) != list(VOCABULARY_TOKEN_FIELDS):
        raise ValueError(
            f"field_policy.vocabulary_token_fields 必须严格等于 Codex 裁定的 "
            f"{list(VOCABULARY_TOKEN_FIELDS)}"
        )
    if passthrough:
        raise ValueError(
            "field_policy.binary_passthrough_fields 必须为空："
            "Codex 已裁定三个二元粗拓扑字段并入数值 Token，不再单列第三类角色"
        )
    if len(numeric) != NUMERIC_TOKEN_FIELD_COUNT:
        raise ValueError(
            f"field_policy.numeric_token_fields 必须恰好 {NUMERIC_TOKEN_FIELD_COUNT} 个，"
            f"实际 {len(numeric)}"
        )
    if "pending_ruling" in policy:
        raise ValueError(
            "field_policy.pending_ruling 必须删除：词表策略已由 Codex 2026-08-21 15:55 CST 裁定，"
            "配置中不得再保留待裁字段"
        )

    preprocessing = policy.get("numeric_preprocessing", {})
    quantile = preprocessing.get("quantile_normalized_fields")
    zero_one = preprocessing.get("zero_one_passthrough_fields")
    if not isinstance(quantile, list) or not isinstance(zero_one, list):
        raise ValueError("field_policy.numeric_preprocessing 的两组字段清单缺失或类型不符")
    if set(quantile) & set(zero_one):
        raise ValueError("数值 Token 的两种数值化口径存在交集，必须互不相交")
    if set(quantile) | set(zero_one) != set(numeric):
        raise ValueError("数值 Token 的两种数值化口径并集不等于 numeric_token_fields")
    if list(zero_one) != list(ZERO_ONE_PASSTHROUGH_FIELDS):
        raise ValueError(
            f"zero_one_passthrough_fields 必须严格等于 Codex 裁定的 {list(ZERO_ONE_PASSTHROUGH_FIELDS)}"
        )
    for group_name, group in (("numeric_token_fields", numeric), ("quantile_normalized_fields", quantile)):
        expected = [field for field in order if field in set(group)]
        if list(group) != expected:
            raise ValueError(f"field_policy.{group_name} 必须按 field_order 的张量列顺序排列")

    counts = {
        "numeric_token_field_count": NUMERIC_TOKEN_FIELD_COUNT,
        "vocabulary_token_field_count": VOCABULARY_TOKEN_FIELD_COUNT,
        "binary_passthrough_field_count": 0,
        "total_field_count": DIJK_FEATURE_COUNT,
        "token_count_including_cls": TOKEN_COUNT_INCLUDING_CLS,
    }
    for key, expected_value in counts.items():
        if policy.get(key) != expected_value:
            raise ValueError(f"field_policy.{key} 必须为 {expected_value}")
    if policy.get("vocabulary_out_of_range_bucket") is not True:
        raise ValueError("field_policy.vocabulary_out_of_range_bucket 必须为真，词表须含固定越界桶")
    if policy.get("vocabulary_key_representation") != "float32_bit_pattern_after_plus_zero_normalization":
        raise ValueError(
            "field_policy.vocabulary_key_representation 必须登记为 float32 位模式且先经 +0.0 规范化："
            "裸位模式会把 ±0.0 算成两个键"
        )


def _validate_control_branch(config: dict[str, Any]) -> None:
    """核验整向量投影对照的身份门禁与搜索合同。"""
    control = config.get("control_branch", {})
    if control.get("is_candidate") is not False:
        raise ValueError("control_branch.is_candidate 必须为假：整向量投影只作对照，不作候选")
    if control.get("key") != CONTROL_KEY or control.get("display_name") != CONTROL_DISPLAY_NAME:
        raise ValueError("control_branch 的运行身份或展示名不符；展示名必须直接表明它不是 FT-Transformer")
    if control.get("role") != CONTROL_ROLE:
        raise ValueError(f"control_branch.role 必须逐字为「{CONTROL_ROLE}」")
    if control.get("identity_gate_note") != CONTROL_IDENTITY_GATE_NOTE:
        raise ValueError("control_branch.identity_gate_note 与统一合同第 111 行的身份门禁原文不符")
    if control.get("input_dimension") != DIJK_FEATURE_COUNT:
        raise ValueError(f"control_branch.input_dimension 必须为 {DIJK_FEATURE_COUNT}")
    if control.get("token_count") != 1:
        raise ValueError("control_branch.token_count 必须为 1：整条向量只投影成单一 Token")
    if control.get("has_feature_tokenizer") is not False or control.get("has_embedding_table") is not False:
        raise ValueError("control_branch 不得有逐字段特征标记器或嵌入表")
    if control.get("has_cls_token") is not False:
        raise ValueError("control_branch 不得拼接 [CLS]，序列长度恒为 1")
    if control.get("parameter_match_target") != "total_parameter_count":
        raise ValueError(
            "control_branch.parameter_match_target 必须为 total_parameter_count："
            "Codex 裁定同参数对照匹配总参数量，禁止改成只匹配主干"
        )
    if control.get("width_search_lower_bound") != OFFICIAL_D_TOKEN_SEARCH_LOWER:
        raise ValueError(f"control_branch.width_search_lower_bound 必须为 {OFFICIAL_D_TOKEN_SEARCH_LOWER}")
    if control.get("width_search_upper_bound") != OFFICIAL_D_TOKEN_SEARCH_UPPER:
        raise ValueError(f"control_branch.width_search_upper_bound 必须为 {OFFICIAL_D_TOKEN_SEARCH_UPPER}")
    if control.get("width_must_be_divisible_by_n_heads") is not True:
        raise ValueError(
            "control_branch.width_must_be_divisible_by_n_heads 必须为真："
            "官方第 84 至 85 行断言 d % n_heads == 0，否则前向按 d//n_heads 切头即报形状错误"
        )


def validate_config(config: dict[str, Any]) -> None:
    """核验冻结 JSON 配置是否严格等于协议 A 的冻结身份与合同。

    只做纯 Python 字典/字符串比对与纯标准库的精度合同校验，不读取数据、不建运行目录、
    不联网；每项不符都抛出带中文原因的 ``ValueError``。
    """
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version 与冻结模式版本不符")
    if config.get("model_key") != MODEL_KEY or config.get("run_id") != RUN_ID:
        raise ValueError("model_key 或 run_id 运行身份不符")
    if config.get("display_name") != DISPLAY_NAME:
        raise ValueError("display_name 必须直接表达机制与实验目的，不得只用字母数字代号")
    if config.get("cells") != CELLS:
        raise ValueError("cells 必须严格等于协议 A 四格 C00/C01/C10/C11 的冻结定义")
    if config.get("source_arrays") != list(SOURCE_ARRAYS):
        raise ValueError("source_arrays 源年数组合同不符")
    if config.get("target_arrays") != list(TARGET_ARRAYS):
        raise ValueError("target_arrays 目标年数组合同不符")

    official = config.get("official_source", {})
    expected_official = {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "license": OFFICIAL_LICENSE,
        "structure_reference_file": OFFICIAL_STRUCTURE_FILE,
        "structure_reference_sha256": OFFICIAL_STRUCTURE_SHA256,
        "license_sha256": OFFICIAL_LICENSE_SHA256,
        "default_recipe_reference_file": OFFICIAL_DEFAULT_RECIPE_FILE,
        "tuning_space_reference_file": OFFICIAL_TUNING_SPACE_FILE,
        "vendor_directory": OFFICIAL_VENDOR_DIRECTORY,
    }
    for key, expected_value in expected_official.items():
        if official.get(key) != expected_value:
            raise ValueError(f"official_source.{key} 与官方源码归档凭据不符")

    _validate_field_policy(config)

    architecture = config.get("architecture", {})
    if architecture.get("n_heads") != N_HEADS:
        raise ValueError(f"architecture.n_heads 必须为 {N_HEADS}（论文明写不调头数）")
    if architecture.get("d_ffn_factor") != D_FFN_FACTOR:
        raise ValueError(
            "architecture.d_ffn_factor 必须为精确的 4/3；官方 TOML 的十进制字面量 "
            "1.333333333333333 在 d_token=192 处取整为 255 而不是 256，两者不可混用"
        )
    if architecture.get("first_block_skips_first_normalization") is not True:
        raise ValueError("architecture.first_block_skips_first_normalization 必须为真（Pre-Norm 首块去归一化）")
    if architecture.get("token_bias") is not True:
        raise ValueError("architecture.token_bias 必须为真（官方第 43 行的逐字段偏置）")
    for key, expected_value in _EXPECTED_ARCHITECTURE.items():
        if architecture.get(key) != expected_value:
            raise ValueError(f"architecture.{key} 与官方默认配方冻结值不符")
    expected_hidden = ffn_hidden_size(architecture["d_token"], architecture["d_ffn_factor"])
    if architecture.get("d_ffn_hidden") != expected_hidden:
        raise ValueError(
            f"architecture.d_ffn_hidden 必须等于 int(d_token*d_ffn_factor)={expected_hidden}"
        )
    if architecture["d_token"] % architecture["n_heads"] != 0:
        raise ValueError("architecture.d_token 必须能被 n_heads 整除，否则注意力无法按头切分")
    reference = architecture.get("paper_self_reported_reference", {})
    reference_numeric = reference.get("numeric_field_count")
    reference_categorical = reference.get("categorical_field_count")
    if not isinstance(reference_numeric, int) or not isinstance(reference_categorical, int):
        raise ValueError("architecture.paper_self_reported_reference 缺少论文自检基准的字段数")
    expected_reference_total = expected_parameter_count(reference_numeric, reference_categorical, 0)
    if reference.get("closed_form_total") != expected_reference_total:
        raise ValueError(
            f"architecture.paper_self_reported_reference.closed_form_total 与闭式实算 "
            f"{expected_reference_total} 不符"
        )

    if config.get("input_candidates") != [dict(candidate) for candidate in INPUT_CANDIDATES]:
        raise ValueError("input_candidates 与冻结输入候选定义不符")
    frozen_optimizers = [dict(candidate) for candidate in OPTIMIZER_CANDIDATES]
    configured_optimizers = config.get("optimizer_candidates")
    if not isinstance(configured_optimizers, list) or len(configured_optimizers) != len(frozen_optimizers):
        raise ValueError("optimizer_candidates 数量与冻结优化器候选不符")
    for configured, frozen in zip(configured_optimizers, frozen_optimizers):
        for key, expected_value in frozen.items():
            if configured.get(key) != expected_value:
                raise ValueError(f"optimizer_candidates 的 {frozen['key']}.{key} 与冻结值不符")
        if not isinstance(configured.get("source"), str) or not configured["source"]:
            raise ValueError(f"optimizer_candidates 的 {frozen['key']} 缺少可追溯的 source 依据")

    policy = config.get("weight_decay_policy", {})
    if list(policy.get("excluded_parameter_roles", [])) != list(WEIGHT_DECAY_EXCLUDED_ROLES):
        raise ValueError("weight_decay_policy.excluded_parameter_roles 与论文表 12 的例外清单不符")
    if policy.get("excluded_weight_decay_value") != 0.0:
        raise ValueError("weight_decay_policy.excluded_weight_decay_value 必须为 0.0")
    if policy.get("official_string_rule") != OFFICIAL_WEIGHT_DECAY_STRING_RULE:
        raise ValueError("weight_decay_policy.official_string_rule 与官方第 376 行逐字不符")
    if not isinstance(policy.get("official_string_rule_divergence"), str):
        raise ValueError("weight_decay_policy 必须登记与官方字符串规则的差异说明")

    _validate_control_branch(config)

    training = config.get("training", {})
    micro_batch = training.get("micro_batch_sequences")
    accumulation = training.get("gradient_accumulation_steps")
    effective_batch = training.get("effective_batch_size")
    if (
        not isinstance(micro_batch, int)
        or not isinstance(accumulation, int)
        or not isinstance(effective_batch, int)
        or micro_batch * accumulation != effective_batch
    ):
        raise ValueError("micro_batch_sequences 乘以 gradient_accumulation_steps 必须等于 effective_batch_size")
    for key, expected_value in _EXPECTED_TRAINING.items():
        if training.get(key) != expected_value:
            raise ValueError(f"training.{key} 与协议 A 冻结值不符")
    if "gradient_clip_norm" not in training:
        raise ValueError("training.gradient_clip_norm 必须显式登记（本配方为不裁剪，取 null）")

    if config.get("selection_stages", {}).get("forbidden_tie_breakers") != _EXPECTED_SELECTION_STAGES[
        "forbidden_tie_breakers"
    ]:
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
    for key, expected_value in _EXPECTED_RESOURCE_CONTRACT.items():
        if resource_contract.get(key) != expected_value:
            raise ValueError(f"resource_contract.{key} 与冻结值不符")

    if config.get("precision_profile_id") != PRECISION_PROFILE_ID:
        raise ValueError(
            f"precision_profile_id 必须为 {PRECISION_PROFILE_ID}："
            "本运行按 RTX 5090 神经训练默认精度配置执行，FP32 与 FP16 只作有收据的显式例外"
        )
    # 只做纯标准库的合同校验，不导入 torch，保证 --validate-config 在无 GPU 开发机可跑。
    contract = load_precision_contract()
    profile = _precision_module().get_profile(contract, PRECISION_PROFILE_ID)
    if profile["compute_dtype"] != "bfloat16" or profile["grad_scaler"] is not False:
        raise ValueError("精度配置不是 BF16 且不使用 GradScaler 的默认配置")
    example = contract["integration_example"]
    # 合同第 183 行写明 do_not_inherit_batch_values，示例值是 N-12 的实验合同。
    # 本运行的有效批、微批与累积步数由本工具独立冻结，只校验示例被正确标记为示例。
    if example.get("example_only") is not True or example.get("do_not_inherit_batch_values") is not True:
        raise ValueError("精度合同的 integration_example 必须标记为示例且禁止继承批量值")
    _precision_module().validate_microbatch_plan(
        effective_batch, micro_batch, accumulation, training["normalization_unit"], False
    )

    if config.get("swanlab") != _EXPECTED_SWANLAB:
        raise ValueError("swanlab 上报身份合同不符")

    if config.get("single_run_directly_comparable") is not True:
        raise ValueError("single_run_directly_comparable 必须为真")
    if config.get("formal_paper_evidence") is not False or config.get("independent_test") is not False:
        raise ValueError("本次运行不能宣称正式论文证据或独立测试")

    diagnostic = ffn_factor_rounding_diagnostic(architecture["d_token"])
    logger.info(
        "前馈宽度取整口径事实：精确 4/3 得 h=%d、论文自检基准总参数 %d；"
        "官方 TOML 字面量 %.15f 得 h=%d、总参数 %d；论文自报 929K。本运行按 4/3 冻结。",
        diagnostic["exact_four_thirds"]["ffn_hidden_size"],
        diagnostic["exact_four_thirds"]["paper_reference_total"],
        OFFICIAL_LITERAL_D_FFN_FACTOR,
        diagnostic["official_toml_literal"]["ffn_hidden_size"],
        diagnostic["official_toml_literal"]["paper_reference_total"],
    )


# ---------------------------------------------------------------------------
# 字段基数收据消费与 Token 布局预算（任务 2）
# ---------------------------------------------------------------------------

CARDINALITY_RECEIPT_SCHEMA_VERSION = "ch3-lspr23-field-cardinality-receipt-v1"
CARDINALITY_RECEIPT_RUN_ID = "ch3-lspr23-field-cardinality-receipt-v1"
# 收据里出现的七个字段清单与顺序，与产出工具一致。
RECEIPT_FIELDS: tuple[str, ...] = (
    "SrcPort",
    "DstPort",
    "Protocol",
    "L3/L4 Protocol",
    "Int/Ext Dst IP",
    "External_src",
    "External_dst",
)


def _canonical_sha256(value: Any) -> str:
    """对可 JSON 序列化对象取规范化 SHA-256。"""
    import hashlib

    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_cardinality_receipt(path: str, config: dict[str, Any]) -> dict[str, Any]:
    """读取并机械校验 LSPR23 训练区字段基数收据。

    收据由 Codex 的独立诊断工具产出，本工具只消费不产出。除收据自带断言外，
    这里追加消费端校验：模式版本、运行身份、目标年读取计数、切分身份、
    ``dijk_feature_index`` 与本配置 ``field_order`` 的一致性。
    """
    receipt_path = Path(path)
    if not receipt_path.exists():
        raise FileNotFoundError(f"缺少字段基数收据：{receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not receipt.get("complete"):
        raise RuntimeError("字段基数收据未标记完成，拒绝消费")
    if receipt.get("schema_version") != CARDINALITY_RECEIPT_SCHEMA_VERSION:
        raise RuntimeError(f"收据模式版本不符：{receipt.get('schema_version')}")
    if receipt.get("run_id") != CARDINALITY_RECEIPT_RUN_ID:
        raise RuntimeError(f"收据运行身份不符：{receipt.get('run_id')}")
    if receipt["identity"].get("target_year_arrays_read") != 0:
        raise RuntimeError("收据声明读取过目标年数组，拒绝消费")
    if list(receipt["fields"].keys()) != list(RECEIPT_FIELDS):
        raise RuntimeError(f"收据字段清单或顺序不符：{list(receipt['fields'].keys())}")

    split = receipt["protocol_a_source_split"]["statistics"]
    expected_split = PROTOCOL_A_SPLIT_STATISTICS
    if (
        split["entity_count"],
        split["train_sequences"],
        split["validation_sequences"],
    ) != (
        expected_split["entity_count"],
        expected_split["train_sequences"],
        expected_split["validation_sequences"],
    ):
        raise RuntimeError(f"收据的协议 A 切分身份与本运行不符：{split}")

    effective_flows = receipt["training_effective_flows"]["effective_flows"]
    if not isinstance(effective_flows, int) or not 0 < effective_flows <= LSPR23_FLOW_COUNT:
        raise RuntimeError(f"收据训练有效流数不合法：{effective_flows}")

    order = config["field_order"]
    seen_indices: set[int] = set()
    for name, entry in receipt["fields"].items():
        index = entry.get("dijk_feature_index")
        if not isinstance(index, int) or not 0 <= index < DIJK_FEATURE_COUNT:
            raise RuntimeError(f"字段 {name} 的 dijk_feature_index 越界：{index}")
        if index in seen_indices:
            raise RuntimeError(f"字段 {name} 的 dijk_feature_index 与其他字段重复：{index}")
        seen_indices.add(index)
        if order[index] != name:
            raise RuntimeError(
                f"收据字段 {name} 的列号 {index} 在本配置 field_order 上是 {order[index]}，"
                "字段清单与冻结张量列不一致"
            )
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
    return receipt


def resolve_quantile_landmark_count(row_count: int) -> int:
    """官方 ``max(min(n // 30, 1000), 10)``（lib/data.py 第 29 行）。"""
    return max(min(row_count // QUANTILE_ROWS_PER_LANDMARK, QUANTILE_LANDMARK_MAXIMUM), QUANTILE_LANDMARK_MINIMUM)


def resolve_missing_indicator_policy(receipt: dict[str, Any]) -> bool:
    """裁决是否引入缺失指示位；两个输入候选必须一致。

    七个字段的 ``missing_fraction`` 全为 0 时不引入指示位。逐字段 Token 下引入指示位
    会改变 Token 数与参数量闭式，属于合同变更，因此发现缺失时停止而不是自行加位。
    """
    nonzero = {
        name: entry["missing_fraction"]
        for name, entry in receipt["fields"].items()
        if entry["missing_fraction"] != 0
    }
    if nonzero:
        raise RuntimeError(
            f"收据显示以下字段存在缺失：{nonzero}。逐字段 Token 下引入缺失指示位会改变"
            "Token 数与参数量闭式，属合同变更，须先重新裁定再运行，本工具拒绝自行加位"
        )
    logger.info("七个字段的 missing_fraction 全为 0，两个输入候选一致地不引入缺失指示位")
    return False


def resolve_field_roles(candidate_key: str, config: dict[str, Any]) -> dict[str, Any]:
    """按输入候选把 83 个字段划分为数值 Token 与词表 Token 两类角色。

    候选一把 83 个字段全部作数值线性 Token；候选二按 Codex 裁定的字段策略，
    只对 ``Protocol`` 与 ``L3/L4 Protocol`` 建训练区词表，其余 81 个走数值线性 Token。
    两个候选的 Token 数都是 ``83 + 1``（含共享权重矩阵第 0 行的 [CLS]）。
    """
    order = list(config["field_order"])
    policy = config["field_policy"]
    if candidate_key == "ft-transformer-input-all-numeric-token":
        numeric_fields = list(order)
        vocabulary_fields: list[str] = []
    elif candidate_key == "ft-transformer-input-protocol-vocabulary-token":
        numeric_fields = list(policy["numeric_token_fields"])
        vocabulary_fields = list(policy["vocabulary_token_fields"])
    else:
        raise ValueError(f"未知输入候选：{candidate_key}")

    zero_one_fields = [field for field in numeric_fields if field in set(ZERO_ONE_PASSTHROUGH_FIELDS)]
    quantile_fields = [field for field in numeric_fields if field not in set(ZERO_ONE_PASSTHROUGH_FIELDS)]
    if len(numeric_fields) + len(vocabulary_fields) != DIJK_FEATURE_COUNT:
        raise RuntimeError(
            f"候选 {candidate_key} 的字段角色划分合计 "
            f"{len(numeric_fields) + len(vocabulary_fields)} 个，未覆盖 {DIJK_FEATURE_COUNT} 个字段"
        )
    if set(numeric_fields) & set(vocabulary_fields):
        raise RuntimeError(f"候选 {candidate_key} 的数值 Token 与词表 Token 存在交集")
    return {
        "candidate_key": candidate_key,
        "numeric_fields": numeric_fields,
        "vocabulary_fields": vocabulary_fields,
        "quantile_fields": quantile_fields,
        "zero_one_fields": zero_one_fields,
        "numeric_feature_indices": tuple(order.index(field) for field in numeric_fields),
        "vocabulary_feature_indices": tuple(order.index(field) for field in vocabulary_fields),
        "quantile_slots": tuple(numeric_fields.index(field) for field in quantile_fields),
        "zero_one_slots": tuple(numeric_fields.index(field) for field in zero_one_fields),
        "token_count": len(numeric_fields) + len(vocabulary_fields) + 1,
    }


def project_token_layout(candidate_key: str, receipt: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """拟合前用收据的 ``unique_count`` 预算 Token 布局、参数量与张量上界。

    先预算再扫描，避免全量拟合之后才发现布局不可行。
    """
    roles = resolve_field_roles(candidate_key, config)
    architecture = config["architecture"]
    # 每个词表字段的类别数为 词表长度 + 1，加一为固定越界桶。
    vocabulary_sizes = {
        name: receipt["fields"][name]["unique_count"] + 1 for name in roles["vocabulary_fields"]
    }
    vocabulary_total = sum(vocabulary_sizes.values())
    decomposition = parameter_count_decomposition(
        len(roles["numeric_fields"]),
        len(roles["vocabulary_fields"]),
        vocabulary_total,
        d_token=architecture["d_token"],
        n_layers=architecture["n_layers"],
        ffn_factor=architecture["d_ffn_factor"],
        d_out=architecture["d_out"],
        token_bias=architecture["token_bias"],
    )
    if decomposition["token_count"] != TOKEN_COUNT_INCLUDING_CLS:
        raise RuntimeError(
            f"候选 {candidate_key} 的 Token 数为 {decomposition['token_count']}，"
            f"与身份门禁要求的 {TOKEN_COUNT_INCLUDING_CLS} 不符"
        )

    profile = _precision_module().get_profile(load_precision_contract(), PRECISION_PROFILE_ID)
    bounds = tensor_upper_bounds(config, decomposition["token_count"], profile)
    projection = {
        "candidate_key": candidate_key,
        "numeric_token_field_count": len(roles["numeric_fields"]),
        "vocabulary_token_field_count": len(roles["vocabulary_fields"]),
        "vocabulary_sizes": vocabulary_sizes,
        "vocabulary_total_columns": vocabulary_total,
        "token_count": decomposition["token_count"],
        "parameter_count": decomposition["total"],
        "parameter_decomposition": decomposition,
        "precision_profile_id": PRECISION_PROFILE_ID,
        "tensor_upper_bounds": bounds,
    }
    logger.info(
        "Token 布局预算 %s：数值 Token=%d，词表 Token=%d，词表总列数=%d，Token 数=%d，参数量=%d",
        candidate_key, projection["numeric_token_field_count"],
        projection["vocabulary_token_field_count"], vocabulary_total,
        projection["token_count"], projection["parameter_count"],
    )
    logger.info(
        "参数量分项：标记器=%d（占 %.2f%%），块=%d，归一化=%d，预测头=%d，主干加头=%d，前馈宽度 h=%d",
        decomposition["feature_tokenizer"],
        decomposition["feature_tokenizer"] / decomposition["total"] * 100,
        decomposition["transformer_blocks"], decomposition["layer_normalizations"],
        decomposition["prediction_head"], decomposition["backbone_and_head"],
        decomposition["ffn_hidden_size"],
    )
    logger.info(
        "单微批张量上界：流数=%d，Token 张量=%.2f MiB（FP32 保守口径 %.2f MiB），"
        "注意力矩阵=%.2f MiB（FP32 岛口径），ReGLU 展开=%.2f MiB",
        bounds["micro_batch_flows"],
        bounds["token_tensor_bytes"] / 1024 / 1024,
        bounds["token_tensor_fp32_bytes"] / 1024 / 1024,
        bounds["attention_matrix_fp32_bytes"] / 1024 / 1024,
        bounds["ffn_expanded_bytes"] / 1024 / 1024,
    )
    if vocabulary_sizes:
        logger.info("各词表字段类别数（含越界桶）：%s", vocabulary_sizes)
    return projection


# ---------------------------------------------------------------------------
# 逐字段 Token 输入变换（任务 2）
# ---------------------------------------------------------------------------


class FieldTokenTransform:
    """在 LSPR23 协议 A 训练区拟合完成后冻结的逐字段 Token 输入变换。

    ``apply`` 只应用不重新拟合：验证区、时间尾部区与 LSPR24 共用同一份状态，
    目标年出现的词表外取值一律落入既有越界桶。

    输出两个数组：``(n, F)`` 的 float32 数值矩阵与 ``(n, C)`` 的 int64 类别索引矩阵
    （``C`` 为 0 时返回 ``None``），恰好对应官方 ``Tokenizer.forward(x_num, x_cat)``
    的两个入参。

    本类刻意不使用 ``dataclasses``，以保持模块顶层只导入
    ``argparse/json/logging/sys/pathlib/typing``；全部属性在构造后不再改写。
    """

    def __init__(
        self,
        *,
        candidate_key: str,
        state_hash: str,
        fitted_row_count: int,
        quantile_landmark_count: int,
        numeric_field_names: tuple[str, ...],
        numeric_feature_indices: tuple[int, ...],
        quantile_slots: tuple[int, ...],
        quantile_feature_indices: tuple[int, ...],
        quantile_fill_values: tuple[float, ...],
        quantile_transformer: Any,
        zero_one_slots: tuple[int, ...],
        zero_one_feature_indices: tuple[int, ...],
        zero_one_true_values: tuple[float, ...],
        zero_one_false_values: tuple[float, ...],
        vocabulary_field_names: tuple[str, ...],
        vocabulary_feature_indices: tuple[int, ...],
        vocabularies: tuple[tuple[float, ...], ...],
    ) -> None:
        self.candidate_key = candidate_key
        self.state_hash = state_hash
        self.fitted_row_count = fitted_row_count
        self.quantile_landmark_count = quantile_landmark_count
        self.numeric_field_names = numeric_field_names
        self.numeric_feature_indices = numeric_feature_indices
        self.quantile_slots = quantile_slots
        self.quantile_feature_indices = quantile_feature_indices
        self.quantile_fill_values = quantile_fill_values
        self.quantile_transformer = quantile_transformer
        self.zero_one_slots = zero_one_slots
        self.zero_one_feature_indices = zero_one_feature_indices
        self.zero_one_true_values = zero_one_true_values
        self.zero_one_false_values = zero_one_false_values
        self.vocabulary_field_names = vocabulary_field_names
        self.vocabulary_feature_indices = vocabulary_feature_indices
        self.vocabularies = vocabularies
        # 诊断计数器，不属于冻结状态，也不参与 state_hash。
        self.zero_one_absorption_counts: dict[str, int] = {
            numeric_field_names[slot]: 0 for slot in zero_one_slots
        }
        self.out_of_vocabulary_counts: dict[str, int] = {name: 0 for name in vocabulary_field_names}
        self._absorption_warned: set[str] = set()

    @property
    def numeric_field_count(self) -> int:
        return len(self.numeric_feature_indices)

    @property
    def vocabulary_field_count(self) -> int:
        return len(self.vocabulary_feature_indices)

    @property
    def categories(self) -> tuple[int, ...]:
        """每个词表字段的类别数（含越界桶），即官方 ``Tokenizer`` 的 ``categories``。"""
        return tuple(len(vocabulary) + 1 for vocabulary in self.vocabularies)

    def apply(self, values: Any) -> tuple[Any, Any]:
        """把 ``(n, 83)`` 的 float32 原值批变换为 ``((n, F) float32, (n, C) int64)``。

        数值列的缺失先按训练区均值填补（官方 ``num_nan_policy='mean'``）再做分位数变换；
        二值列按训练区最大值记 1、最小值记 0，其余取值与 ``NaN`` 静默记 0 并计数；
        词表列命中训练区取值时取其位置，未命中与 ``NaN`` 一律落入末位越界桶并计数。
        """
        import numpy as np

        array = np.asarray(values)
        if array.ndim != 2 or array.shape[1] != DIJK_FEATURE_COUNT:
            raise ValueError(f"输入批形状必须为 (n, {DIJK_FEATURE_COUNT})，实际 {array.shape}")
        row_count = array.shape[0]
        numeric = np.zeros((row_count, self.numeric_field_count), dtype=np.float32)

        if self.quantile_slots:
            block = array[:, list(self.quantile_feature_indices)].astype(np.float32, copy=True)
            missing = np.isnan(block)
            if missing.any():
                fill = np.asarray(self.quantile_fill_values, dtype=np.float32)
                block[missing] = np.broadcast_to(fill, block.shape)[missing]
            # scikit-learn 对超出拟合范围的取值本身就截断到训练端点输出，无需另加裁剪。
            numeric[:, list(self.quantile_slots)] = self.quantile_transformer.transform(block).astype(
                np.float32, copy=False
            )

        for position, slot in enumerate(self.zero_one_slots):
            index = self.zero_one_feature_indices[position]
            column = array[:, index].astype(np.float32, copy=False)
            true_value = np.float32(self.zero_one_true_values[position])
            false_value = np.float32(self.zero_one_false_values[position])
            is_true = column == true_value
            numeric[:, slot] = is_true.astype(np.float32)
            absorbed = int((~(is_true | (column == false_value))).sum())
            if absorbed:
                name = self.numeric_field_names[slot]
                self.zero_one_absorption_counts[name] += absorbed
                if name not in self._absorption_warned:
                    self._absorption_warned.add(name)
                    logger.warning(
                        "二值字段 %s 出现训练区未见取值（含 NaN）%d 个，按 0 静默吸收；"
                        "该列按论文二值规则直通、无越界桶，累计次数见 zero_one_absorption_counts",
                        name, absorbed,
                    )

        if not self.vocabulary_field_count:
            return numeric, None

        categorical = np.zeros((row_count, self.vocabulary_field_count), dtype=np.int64)
        for position, index in enumerate(self.vocabulary_feature_indices):
            vocabulary = self.vocabularies[position]
            # 加 +0.0 把 -0.0 规范化为 +0.0，与词表拟合口径一致；否则 ±0.0 会算成两个键。
            column = array[:, index].astype(np.float32, copy=True) + np.float32(0.0)
            table = np.asarray(vocabulary, dtype=np.float32)
            location = np.searchsorted(table, column)
            np.clip(location, 0, len(table) - 1, out=location)
            hit = table[location] == column  # NaN 与词表外取值都判否，落入越界桶
            categorical[:, position] = np.where(hit, location, len(table)).astype(np.int64)
            missed = int((~hit).sum())
            if missed:
                name = self.vocabulary_field_names[position]
                self.out_of_vocabulary_counts[name] += missed
        return numeric, categorical


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
    """在单个字段上拟合官方分位数规范化网格，并返回训练区均值填补值。

    官方 lib/data.py 的口径：缺失先按训练区 ``np.nanmean`` 填补，再按
    ``noise_std = 1e-3 / max(列标准差, 1e-3)`` 叠加高斯噪声，最后拟合
    ``QuantileTransformer(output_distribution='normal', subsample=1e9)``。
    """
    import numpy as np
    from sklearn.preprocessing import QuantileTransformer

    finite = np.isfinite(values)
    if not bool(finite.any()):
        raise RuntimeError("字段在训练区全为缺失，无法拟合分位数规范化")
    fill_value = float(np.nanmean(values))
    filled = values.copy()
    missing = ~finite
    if bool(missing.any()):
        filled[missing] = np.float32(fill_value)

    # 官方在填补后的训练矩阵上算列标准差，再按相对噪声打散重复值。
    column_std = float(np.std(filled))
    noise_std = QUANTILE_RELATIVE_NOISE / max(column_std, QUANTILE_RELATIVE_NOISE)
    generator = np.random.default_rng(seed)
    for start in range(0, len(filled), QUANTILE_NOISE_CHUNK_ELEMENTS):
        stop = min(start + QUANTILE_NOISE_CHUNK_ELEMENTS, len(filled))
        filled[start:stop] += (noise_std * generator.standard_normal(stop - start)).astype(np.float32)

    transformer = QuantileTransformer(
        n_quantiles=landmark_count,
        output_distribution=QUANTILE_OUTPUT_DISTRIBUTION,
        subsample=QUANTILE_SUBSAMPLE,
        random_state=seed,
    )
    transformer.fit(filled.reshape(-1, 1))
    return transformer, fill_value


def _fit_vocabulary(matrix: Any, feature_index: int, train_flow_mask: Any, chunk_rows: int) -> tuple[float, ...]:
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
        # NaN 不进词表；-0.0 先经 +0.0 归一，否则裸位模式会把 ±0.0 算成两个键。
        block = block[np.isfinite(block)] + np.float32(0.0)
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
) -> FieldTokenTransform:
    """在 LSPR23 协议 A 训练区有效流上拟合指定候选的输入变换并冻结。

    ``X23`` 一律以 ``mmap_mode="r"`` 打开并逐字段分块处理；任一时刻的显式分配都有固定
    上界，与字段数无关。拟合状态（分位数网格、词表、越界桶位置、缺失填充值、二值映射）
    全部并入 ``state_hash``，供选择封印追溯。
    """
    import hashlib

    import numpy as np
    import sklearn
    from sklearn.preprocessing import QuantileTransformer

    if candidate_key not in {candidate["key"] for candidate in INPUT_CANDIDATES}:
        raise ValueError(f"未知输入候选：{candidate_key}")
    resolve_missing_indicator_policy(receipt)
    projection = project_token_layout(candidate_key, receipt, config)
    roles = resolve_field_roles(candidate_key, config)

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

    landmark_count = resolve_quantile_landmark_count(row_count)
    quantile_indices = tuple(
        roles["numeric_feature_indices"][slot] for slot in roles["quantile_slots"]
    )
    logger.info(
        "开始拟合输入变换 %s：训练有效流=%d，分位数地标=%d，分位数字段=%d，二值直通字段=%d，"
        "词表字段=%d，分块行数=%d",
        candidate_key, row_count, landmark_count, len(quantile_indices),
        len(roles["zero_one_slots"]), len(roles["vocabulary_fields"]), chunk_rows,
    )

    quantile_columns: list[Any] = []
    fill_values: list[float] = []
    references: Any = None
    landmark_actual: int | None = None
    for position, feature_index in enumerate(quantile_indices, start=1):
        column = _gather_training_column(matrix, feature_index, mask, row_count, chunk_rows)
        # 每个字段使用独立派生种子。官方对 (n, d) 训练矩阵一次性抽取噪声，逐字段处理无法
        # 复现同一随机流（复现需一次生成 n×d 个 float64）；此处每元素仍为独立同分布
        # N(0, noise_std^2)，只是随机流分配方式不同，是显式记录的实现偏离。
        transformer, fill_value = _fit_quantile_column(column, landmark_count, seed + feature_index)
        quantile_columns.append(transformer.quantiles_[:, 0])
        fill_values.append(fill_value)
        if references is None:
            references = transformer.references_.copy()
            landmark_actual = int(transformer.n_quantiles_)
        del column
        if position % 10 == 0 or position == len(quantile_indices):
            logger.info("分位数拟合进度 %d/%d", position, len(quantile_indices))

    # 把逐列网格堆叠为单个联合变换器，减少调用开销；数值语义与逐列调用一致。
    quantile_transformer = QuantileTransformer(
        n_quantiles=landmark_count,
        output_distribution=QUANTILE_OUTPUT_DISTRIBUTION,
        subsample=QUANTILE_SUBSAMPLE,
        random_state=seed,
    )
    quantile_transformer.n_quantiles_ = landmark_actual
    quantile_transformer.quantiles_ = np.stack(quantile_columns, axis=1)
    quantile_transformer.references_ = references
    quantile_transformer.n_features_in_ = len(quantile_indices)

    # 组装式变换器直接写入了 scikit-learn 的私有拟合属性，未来版本一旦改变这些属性的
    # 语义就会静默产出错误数值。这里加一条运行时自检：把各字段的训练区中位数送进
    # transform，output_distribution="normal" 应把中位数映射到约 0；偏差超过绊线即停止。
    median_probe = np.asarray(
        [float(np.median(quantile_transformer.quantiles_[:, i])) for i in range(len(quantile_indices))],
        dtype=np.float32,
    ).reshape(1, -1)
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

    zero_one_true: list[float] = []
    zero_one_false: list[float] = []
    for slot in roles["zero_one_slots"]:
        name = roles["numeric_fields"][slot]
        entry = receipt["fields"][name]
        if entry["unique_count"] > 2:
            raise RuntimeError(
                f"二值字段 {name} 的 unique_count 为 {entry['unique_count']}，超过两个取值，"
                "不满足论文对二值特征的定义"
            )
        if entry["unique_count"] == 1:
            logger.warning("二值字段 %s 在训练区只有一个取值，该列在训练区恒为 1", name)
        zero_one_true.append(float(entry["max"]))
        zero_one_false.append(float(entry["min"]))
        logger.info(
            "二值字段 %s 映射：max=%s 记为 1，min=%s 记为 0，其余取值与 NaN 静默记 0 并计数",
            name, entry["max"], entry["min"],
        )

    vocabularies: list[tuple[float, ...]] = []
    for name, feature_index in zip(
        roles["vocabulary_fields"], roles["vocabulary_feature_indices"], strict=True
    ):
        vocabulary = _fit_vocabulary(matrix, feature_index, mask, chunk_rows)
        declared = receipt["fields"][name]["unique_count"]
        if len(vocabulary) != declared:
            raise RuntimeError(
                f"字段 {name} 训练区词表长度 {len(vocabulary)} 与收据 unique_count {declared} 不符，"
                "说明拟合区与收据的切分身份不一致"
            )
        vocabularies.append(vocabulary)
        logger.info("词表字段 %s 词表长度 %d，类别数 %d（末位为越界桶）", name, len(vocabulary), len(vocabulary) + 1)

    vocabulary_total = sum(len(vocabulary) + 1 for vocabulary in vocabularies)
    if vocabulary_total != projection["vocabulary_total_columns"]:
        raise RuntimeError(
            f"实测词表总列数 {vocabulary_total} 与收据预算 {projection['vocabulary_total_columns']} 不符"
        )

    state = {
        "candidate_key": candidate_key,
        "numeric_field_count": len(roles["numeric_fields"]),
        "vocabulary_field_count": len(roles["vocabulary_fields"]),
        "vocabulary_total_columns": vocabulary_total,
        "token_count": projection["token_count"],
        "fitted_row_count": row_count,
        "quantile_landmark_count": landmark_actual,
        "quantile_policy": {
            "output_distribution": QUANTILE_OUTPUT_DISTRIBUTION,
            "subsample": QUANTILE_SUBSAMPLE,
            "relative_noise": QUANTILE_RELATIVE_NOISE,
            "numeric_nan_policy": NUMERIC_NAN_POLICY,
            "seed": seed,
            "noise_seed_derivation": "per_feature_seed_plus_dijk_feature_index",
            "scikit_learn_version": sklearn.__version__,
            "median_self_check_max_absolute_value": median_deviation,
            "median_self_check_tolerance": QUANTILE_MEDIAN_SELF_CHECK_TOLERANCE,
        },
        "field_integer_like": {
            name: bool(entry["integer_like"]) for name, entry in receipt["fields"].items()
        },
        "numeric_feature_indices": list(roles["numeric_feature_indices"]),
        "quantile_slots": list(roles["quantile_slots"]),
        "zero_one_slots": list(roles["zero_one_slots"]),
        "quantile_fill_values_sha256": hashlib.sha256(
            np.asarray(fill_values, dtype=np.float64).tobytes()
        ).hexdigest(),
        "quantile_grid_sha256": hashlib.sha256(
            np.ascontiguousarray(quantile_transformer.quantiles_).tobytes()
        ).hexdigest(),
        "quantile_references_sha256": hashlib.sha256(
            np.ascontiguousarray(quantile_transformer.references_).tobytes()
        ).hexdigest(),
        "zero_one_fields": {
            roles["numeric_fields"][slot]: {
                "numeric_slot": slot,
                "dijk_feature_index": roles["numeric_feature_indices"][slot],
                "true_value": true_value,
                "false_value": false_value,
            }
            for slot, true_value, false_value in zip(
                roles["zero_one_slots"], zero_one_true, zero_one_false, strict=True
            )
        },
        # 词表以 float32 位模式记录，避免十进制往返带来的比较歧义。
        "vocabularies": {
            name: {
                "dijk_feature_index": index,
                "size": len(vocabulary),
                "out_of_vocabulary_index": len(vocabulary),
                "categories": len(vocabulary) + 1,
                "bit_patterns_sha256": hashlib.sha256(
                    np.asarray(vocabulary, dtype=np.float32).view(np.uint32).tobytes()
                ).hexdigest(),
            }
            for name, index, vocabulary in zip(
                roles["vocabulary_fields"], roles["vocabulary_feature_indices"], vocabularies, strict=True
            )
        },
        "cardinality_receipt_effective_flow_mask_sha256": flow_mapping["effective_flow_mask_sha256"],
    }
    state_hash = _canonical_sha256(state)
    logger.info(
        "输入变换 %s 拟合完成：数值 Token=%d，词表 Token=%d，Token 数=%d，参数量=%d，state_hash=%s",
        candidate_key, len(roles["numeric_fields"]), len(roles["vocabulary_fields"]),
        projection["token_count"], projection["parameter_count"], state_hash,
    )
    return FieldTokenTransform(
        candidate_key=candidate_key,
        state_hash=state_hash,
        fitted_row_count=row_count,
        quantile_landmark_count=int(landmark_actual or landmark_count),
        numeric_field_names=tuple(roles["numeric_fields"]),
        numeric_feature_indices=tuple(roles["numeric_feature_indices"]),
        quantile_slots=tuple(roles["quantile_slots"]),
        quantile_feature_indices=quantile_indices,
        quantile_fill_values=tuple(fill_values),
        quantile_transformer=quantile_transformer,
        zero_one_slots=tuple(roles["zero_one_slots"]),
        zero_one_feature_indices=tuple(
            roles["numeric_feature_indices"][slot] for slot in roles["zero_one_slots"]
        ),
        zero_one_true_values=tuple(zero_one_true),
        zero_one_false_values=tuple(zero_one_false),
        vocabulary_field_names=tuple(roles["vocabulary_fields"]),
        vocabulary_feature_indices=tuple(roles["vocabulary_feature_indices"]),
        vocabularies=tuple(vocabularies),
    )


# ---------------------------------------------------------------------------
# Transformer 块与整向量投影对照（任务 3）
# ---------------------------------------------------------------------------

_MODULE_CACHE: dict[str, Any] = {}


def transformer_classes() -> dict[str, Any]:
    """延迟构造依赖 PyTorch 的模块类并缓存。

    模块顶层不导入 torch，``--validate-config`` 因此可以在没有 GPU 与 PyTorch 的
    开发机上跑通；只有真正要建模型时才触发导入。
    """
    if _MODULE_CACHE:
        return _MODULE_CACHE

    import math

    import torch
    from torch import nn
    from torch.nn import functional as F
    from torch.nn import init as nn_init

    precision = _precision_module()

    def reglu(values: torch.Tensor) -> torch.Tensor:
        """官方 lib/deep.py 第 109 至 111 行：``a, b = x.chunk(2, -1); return a * relu(b)``。"""
        first, second = values.chunk(2, dim=-1)
        return first * F.relu(second)

    class FeatureTokenizer(nn.Module):
        """逐字段特征标记器，逐项对应官方第 18 至 77 行。

        - ``weight`` 形状 ``(F+1, d)``：第 0 行是 [CLS]，与数值字段共享同一张矩阵，
          **[CLS] 不单独设参数**；数值 Token 为 ``T_j = b_j + x_j * W_j``。
        - ``bias`` 形状 ``(F+C, d)``：[CLS] 无偏置，前向时在最前面补一行零。
        - ``category_embeddings``：每个词表字段一段独立查找表，用 ``category_offsets``
          把逐字段局部索引平移到全局行号。
        """

        category_offsets: torch.Tensor | None

        def __init__(
            self,
            numeric_field_count: int,
            categories: tuple[int, ...],
            d_token: int,
            token_bias: bool,
        ) -> None:
            super().__init__()
            self.numeric_field_count = numeric_field_count
            self.categories = tuple(categories)
            self.d_token = d_token
            if self.categories:
                offsets = torch.tensor([0] + list(self.categories[:-1])).cumsum(0)
                self.register_buffer("category_offsets", offsets)
                self.category_embeddings = nn.Embedding(sum(self.categories), d_token)
                nn_init.kaiming_uniform_(self.category_embeddings.weight, a=math.sqrt(5))
            else:
                self.register_buffer("category_offsets", None)
                self.category_embeddings = None
            bias_rows = numeric_field_count + len(self.categories)
            self.weight = nn.Parameter(torch.empty(numeric_field_count + 1, d_token))
            self.bias = nn.Parameter(torch.empty(bias_rows, d_token)) if token_bias else None
            # 官方第 44 至 47 行：初始化按 nn.Linear 的 Kaiming 均匀分布。
            nn_init.kaiming_uniform_(self.weight, a=math.sqrt(5))
            if self.bias is not None:
                nn_init.kaiming_uniform_(self.bias, a=math.sqrt(5))

        @property
        def token_count(self) -> int:
            return self.numeric_field_count + 1 + len(self.categories)

        def forward(self, x_num: torch.Tensor, x_cat: torch.Tensor | None) -> torch.Tensor:
            # x_num: (n, F) -> 前置 [CLS] 常数 1 得 (n, F+1)，再逐字段缩放共享权重行。
            if x_num.ndim != 2 or x_num.shape[1] != self.numeric_field_count:
                raise RuntimeError(
                    f"数值输入必须是 n×{self.numeric_field_count}，实际 {tuple(x_num.shape)}"
                )
            ones = torch.ones(len(x_num), 1, device=x_num.device, dtype=x_num.dtype)
            with_cls = torch.cat([ones, x_num], dim=1)
            tokens = self.weight[None] * with_cls[:, :, None]
            if self.category_embeddings is not None:
                if x_cat is None or x_cat.shape[1] != len(self.categories):
                    raise RuntimeError(
                        f"类别输入必须是 n×{len(self.categories)}，实际 "
                        f"{None if x_cat is None else tuple(x_cat.shape)}"
                    )
                tokens = torch.cat(
                    [tokens, self.category_embeddings(x_cat + self.category_offsets[None])], dim=1
                )
            elif x_cat is not None:
                raise RuntimeError("本候选没有词表字段，不应传入类别输入")
            if self.bias is not None:
                zero_row = torch.zeros(1, self.bias.shape[1], device=tokens.device, dtype=self.bias.dtype)
                full_bias = torch.cat([zero_row, self.bias])
                tokens = tokens + full_bias[None]
            return tokens

    class MultiheadAttention(nn.Module):
        """多头注意力，逐项对应官方第 80 至 148 行（不含 Linformer 压缩）。

        四个投影都是 ``nn.Linear(d, d)`` 且默认带偏置；``W_out`` 只在 ``n_heads > 1``
        时存在。``softmax`` 属精度合同登记的敏感计算，在 FP32 岛内完成。
        """

        def __init__(self, d_token: int, n_heads: int, dropout: float, initialization: str) -> None:
            super().__init__()
            if n_heads > 1 and d_token % n_heads != 0:
                raise ValueError(
                    f"宽度 {d_token} 不能被头数 {n_heads} 整除，注意力无法按 d//n_heads 切头"
                )
            if initialization not in ("xavier", "kaiming"):
                raise ValueError(f"未核验的初始化方式：{initialization}")
            self.W_q = nn.Linear(d_token, d_token)
            self.W_k = nn.Linear(d_token, d_token)
            self.W_v = nn.Linear(d_token, d_token)
            self.W_out = nn.Linear(d_token, d_token) if n_heads > 1 else None
            self.n_heads = n_heads
            self.dropout = nn.Dropout(dropout) if dropout else None
            # 官方第 96 至 102 行：kaiming 时只把偏置清零，权重沿用 nn.Linear 默认初始化。
            for module in (self.W_q, self.W_k, self.W_v):
                if initialization == "xavier" and (n_heads > 1 or module is not self.W_v):
                    nn_init.xavier_uniform_(module.weight, gain=1 / math.sqrt(2))
                nn_init.zeros_(module.bias)
            if self.W_out is not None:
                nn_init.zeros_(self.W_out.bias)

        def _reshape(self, values: torch.Tensor) -> torch.Tensor:
            batch_size, token_count, width = values.shape
            head_width = width // self.n_heads
            return (
                values.reshape(batch_size, token_count, self.n_heads, head_width)
                .transpose(1, 2)
                .reshape(batch_size * self.n_heads, token_count, head_width)
            )

        def forward(self, x_query: torch.Tensor, x_key_value: torch.Tensor) -> torch.Tensor:
            query = self.W_q(x_query)
            key = self.W_k(x_key_value)
            value = self.W_v(x_key_value)
            batch_size = len(query)
            key_head_width = key.shape[-1] // self.n_heads
            value_head_width = value.shape[-1] // self.n_heads
            query_token_count = query.shape[1]

            logits = self._reshape(query) @ self._reshape(key).transpose(1, 2) / math.sqrt(key_head_width)
            with precision.fp32_island(
                logits, device_type=logits.device.type, torch_module=torch
            ) as (logits32,):
                attention = F.softmax(logits32, dim=-1)
            attention = attention.to(logits.dtype)
            if self.dropout is not None:
                attention = self.dropout(attention)
            mixed = attention @ self._reshape(value)
            mixed = (
                mixed.reshape(batch_size, self.n_heads, query_token_count, value_head_width)
                .transpose(1, 2)
                .reshape(batch_size, query_token_count, self.n_heads * value_head_width)
            )
            if self.W_out is not None:
                mixed = self.W_out(mixed)
            return mixed

    class TransformerBlocks(nn.Module):
        """Pre-Norm 块堆叠，FT-Transformer 主干与整向量投影对照共用同一实现。

        ``Block(x) = ResidualPreNorm(FFN, ResidualPreNorm(MHSA, x))``，其中
        ``ResidualPreNorm(M, x) = x + Dropout(M(Norm(x)))``；**首块去掉第一处归一化**
        （官方第 223 行只在 ``layer_idx > 0`` 时建 ``norm0``）。最后一块的注意力只以
        第 0 个 Token 作查询（官方第 277 至 283 行），对序列长度为 1 的对照是恒等操作。
        """

        def __init__(
            self,
            d_token: int,
            n_layers: int,
            n_heads: int,
            ffn_factor: float,
            attention_dropout: float,
            ffn_dropout: float,
            residual_dropout: float,
            initialization: str,
            first_block_skips_first_normalization: bool,
        ) -> None:
            super().__init__()
            self.d_token = d_token
            self.n_layers = n_layers
            self.ffn_dropout = ffn_dropout
            self.residual_dropout = residual_dropout
            hidden = ffn_hidden_size(d_token, ffn_factor)
            self.d_hidden = hidden
            self.layers = nn.ModuleList([])
            for layer_index in range(n_layers):
                layer = nn.ModuleDict(
                    {
                        "attention": MultiheadAttention(d_token, n_heads, attention_dropout, initialization),
                        # ReGLU 让首层输出宽度翻倍（官方第 216 至 217 行）。
                        "linear0": nn.Linear(d_token, hidden * 2),
                        "linear1": nn.Linear(hidden, d_token),
                        "norm1": nn.LayerNorm(d_token),
                    }
                )
                if layer_index or not first_block_skips_first_normalization:
                    layer["norm0"] = nn.LayerNorm(d_token)
                self.layers.append(layer)
            self.last_normalization = nn.LayerNorm(d_token)

        def _start_residual(self, values: torch.Tensor, layer: Any, norm_index: int) -> torch.Tensor:
            key = f"norm{norm_index}"
            return layer[key](values) if key in layer else values

        def _end_residual(self, values: torch.Tensor, branch: torch.Tensor) -> torch.Tensor:
            if self.residual_dropout:
                branch = F.dropout(branch, self.residual_dropout, self.training)
            return values + branch

        def forward(self, tokens: torch.Tensor) -> torch.Tensor:
            """``(n, T, d)`` 的 Token 序列进，``(n, d)`` 的第 0 个 Token 表示出。"""
            if tokens.ndim != 3 or tokens.shape[2] != self.d_token:
                raise RuntimeError(f"Token 张量必须是 n×T×{self.d_token}，实际 {tuple(tokens.shape)}")
            values = tokens
            for layer_index, layer in enumerate(self.layers):
                is_last_layer = layer_index + 1 == self.n_layers
                branch = self._start_residual(values, layer, 0)
                # 最后一块只需处理第 0 个 Token（[CLS]），其余位置的输出不参与预测。
                branch = layer["attention"](branch[:, :1] if is_last_layer else branch, branch)
                if is_last_layer:
                    values = values[:, : branch.shape[1]]
                values = self._end_residual(values, branch)

                branch = self._start_residual(values, layer, 1)
                branch = reglu(layer["linear0"](branch))
                if self.ffn_dropout:
                    branch = F.dropout(branch, self.ffn_dropout, self.training)
                branch = layer["linear1"](branch)
                values = self._end_residual(values, branch)
            if values.shape[1] != 1:
                raise RuntimeError(f"末块后应只剩 1 个 Token，实际 {values.shape[1]}")
            return values[:, 0]

    class PredictionHead(nn.Module):
        """预测头 ``Linear(ReLU(LayerNorm(T_L^[CLS])))``。

        ``LayerNorm`` 由 ``TransformerBlocks.last_normalization`` 提供，本模块只做
        ``ReLU`` 与线性映射（官方第 296 至 300 行的 ``last_activation`` 对 ReGLU 是 ReLU）。
        """

        def __init__(self, d_token: int, d_out: int) -> None:
            super().__init__()
            self.head = nn.Linear(d_token, d_out)
            self.d_out = d_out

        def forward(self, representation: torch.Tensor) -> torch.Tensor:
            return self.head(F.relu(representation))

    class FTTransformerFieldToken(nn.Module):
        """FT-Transformer 逐字段 Token 主干（机制外接前的骨干）。

        ``encode`` 返回末块输出的 ``T_L^[CLS]``（未过最后一处归一化），
        供因果前缀聚合在其后外接；``predict`` 完成 ``Linear(ReLU(LayerNorm(·)))``。
        ``forward`` 是两者的直接复合，与官方前向逐步等价。
        """

        def __init__(
            self,
            numeric_field_count: int,
            categories: tuple[int, ...],
            d_token: int,
            n_layers: int,
            n_heads: int,
            ffn_factor: float,
            attention_dropout: float,
            ffn_dropout: float,
            residual_dropout: float,
            initialization: str,
            token_bias: bool,
            first_block_skips_first_normalization: bool,
            d_out: int,
        ) -> None:
            super().__init__()
            self.tokenizer = FeatureTokenizer(numeric_field_count, categories, d_token, token_bias)
            self.blocks = TransformerBlocks(
                d_token, n_layers, n_heads, ffn_factor, attention_dropout, ffn_dropout,
                residual_dropout, initialization, first_block_skips_first_normalization,
            )
            self.prediction = PredictionHead(d_token, d_out)
            self.d_token = d_token
            self.d_out = d_out

        @property
        def token_count(self) -> int:
            return self.tokenizer.token_count

        def encode(self, x_num: torch.Tensor, x_cat: torch.Tensor | None) -> torch.Tensor:
            """返回 ``(n, d)`` 的末块 [CLS] 表示，机制在此之后外接。"""
            return self.blocks(self.tokenizer(x_num, x_cat))

        def predict(self, representation: torch.Tensor) -> torch.Tensor:
            return self.prediction(self.blocks.last_normalization(representation)).squeeze(-1)

        def forward(self, x_num: torch.Tensor, x_cat: torch.Tensor | None) -> torch.Tensor:
            return self.predict(self.encode(x_num, x_cat))

    class WholeVectorProjectionControl(nn.Module):
        """整向量投影同参数对照——对照，不是候选。

        把整条 ``input_dimension`` 维向量用一个 ``nn.Linear`` 投影成**单一 Token**，
        再过与 FT-Transformer 完全相同的块堆叠与预测头。**没有逐字段权重、没有嵌入表、
        没有 [CLS] 拼接**，序列长度恒为 1。

        统一合同第 111 行明写：这样的普通 Transformer 不能称为 FT-Transformer，
        其失败也不能否决该模型族。本类只用于证明收益来自字段身份而非容量。

        序列长度为 1 时自注意力退化为逐位置线性映射（softmax 只有一个元素恒为 1），
        这是整向量投影这一设定的固有结果，也正是它只能作容量对照的原因。
        """

        is_candidate = False
        role = CONTROL_ROLE

        def __init__(
            self,
            input_dimension: int,
            d_token: int,
            n_layers: int,
            n_heads: int,
            ffn_factor: float,
            attention_dropout: float,
            ffn_dropout: float,
            residual_dropout: float,
            initialization: str,
            first_block_skips_first_normalization: bool,
            d_out: int,
        ) -> None:
            super().__init__()
            self.input_projection = nn.Linear(input_dimension, d_token)
            self.blocks = TransformerBlocks(
                d_token, n_layers, n_heads, ffn_factor, attention_dropout, ffn_dropout,
                residual_dropout, initialization, first_block_skips_first_normalization,
            )
            self.prediction = PredictionHead(d_token, d_out)
            self.input_dimension = input_dimension
            self.d_token = d_token
            self.d_out = d_out

        @property
        def token_count(self) -> int:
            return 1

        def encode(self, x_num: torch.Tensor, x_cat: torch.Tensor | None = None) -> torch.Tensor:
            if x_cat is not None:
                raise RuntimeError("整向量投影对照没有嵌入表，不接受类别索引输入")
            if x_num.ndim != 2 or x_num.shape[1] != self.input_dimension:
                raise RuntimeError(
                    f"对照输入必须是 n×{self.input_dimension}，实际 {tuple(x_num.shape)}"
                )
            return self.blocks(self.input_projection(x_num).unsqueeze(1))

        def predict(self, representation: torch.Tensor) -> torch.Tensor:
            return self.prediction(self.blocks.last_normalization(representation)).squeeze(-1)

        def forward(self, x_num: torch.Tensor, x_cat: torch.Tensor | None = None) -> torch.Tensor:
            return self.predict(self.encode(x_num, x_cat))

    _MODULE_CACHE.update(
        {
            "reglu": reglu,
            "FeatureTokenizer": FeatureTokenizer,
            "MultiheadAttention": MultiheadAttention,
            "TransformerBlocks": TransformerBlocks,
            "PredictionHead": PredictionHead,
            "FTTransformerFieldToken": FTTransformerFieldToken,
            "WholeVectorProjectionControl": WholeVectorProjectionControl,
        }
    )
    return _MODULE_CACHE


def resolve_weight_decay_groups(model: Any) -> dict[str, Any]:
    """按论文表 12 的例外清单把参数分成施加与不施加权重衰减两组。

    论文表 12 明写「特征标记器、LayerNorm 与偏置一律取 0.0」。本函数按参数角色判断，
    不按参数名子串判断，因此覆盖官方字符串规则漏掉的 ``last_normalization.weight``。
    返回值同时给出官方字符串规则的判定结果与两者的差异清单，便于在封印中留证。
    """
    from torch import nn

    normalization_parameters: set[str] = set()
    for module_name, module in model.named_modules():
        if isinstance(module, nn.LayerNorm):
            for parameter_name, _ in module.named_parameters(recurse=False):
                normalization_parameters.add(f"{module_name}.{parameter_name}" if module_name else parameter_name)

    with_decay: list[Any] = []
    without_decay: list[Any] = []
    with_decay_names: list[str] = []
    without_decay_names: list[str] = []
    official_rule_names: list[str] = []
    for name, parameter in model.named_parameters():
        excluded = (
            name.startswith("tokenizer.")
            or name in normalization_parameters
            or name.endswith(".bias")
            or name == "bias"
        )
        if excluded:
            without_decay.append(parameter)
            without_decay_names.append(name)
        else:
            with_decay.append(parameter)
            with_decay_names.append(name)
        if all(pattern not in name for pattern in ("tokenizer", ".norm", ".bias")):
            official_rule_names.append(name)

    divergence = sorted(set(official_rule_names) - set(with_decay_names))
    if divergence:
        logger.warning(
            "官方字符串规则会对以下参数施加权重衰减，本实现按论文表 12 正文排除：%s",
            divergence,
        )
    logger.info(
        "权重衰减分组：施加 %d 个参数张量，例外 %d 个参数张量（特征标记器、LayerNorm、偏置）",
        len(with_decay_names), len(without_decay_names),
    )
    return {
        "parameters_with_weight_decay": with_decay,
        "parameters_without_weight_decay": without_decay,
        "names_with_weight_decay": with_decay_names,
        "names_without_weight_decay": without_decay_names,
        "official_string_rule": OFFICIAL_WEIGHT_DECAY_STRING_RULE,
        "official_string_rule_would_decay": official_rule_names,
        "divergence_from_official_string_rule": divergence,
    }


def _assert_parameter_dtypes(model: Any) -> None:
    """参数必须保持 FP32；优化器状态在第一次 step 之后由任务 4 再核。"""
    import torch

    for name, parameter in model.named_parameters():
        if parameter.is_floating_point() and parameter.dtype != torch.float32:
            raise RuntimeError(f"模型参数 {name} 不是 FP32，与精度合同不符")


def build_model(
    config: dict[str, Any], transform_or_projection: Any, *, input_key: str
) -> Any:
    """构造 FT-Transformer 主干并做参数量三方比对。

    三方为：闭式 ``expected_parameter_count``、冻结配置中该输入候选登记的
    ``parameter_count``、以及实际 ``sum(p.numel())``。冻结值为 ``null`` 时只比对
    闭式与实际两方，并把实测值写进日志，不自行回填冻结配置。

    ``transform_or_projection`` 接受 ``FieldTokenTransform`` 或
    ``project_token_layout`` 的预算字典，二者都能给出 Token 布局。
    """
    architecture = config["architecture"]
    if isinstance(transform_or_projection, FieldTokenTransform):
        numeric_count = transform_or_projection.numeric_field_count
        categories = transform_or_projection.categories
    else:
        numeric_count = transform_or_projection["numeric_token_field_count"]
        # vocabulary_sizes 由 project_token_layout 按 vocabulary_fields 的顺序构造，
        # 与 FieldTokenTransform.categories 的字段顺序一致。
        categories = tuple(transform_or_projection["vocabulary_sizes"].values())
    vocabulary_total = sum(categories)

    classes = transformer_classes()
    model = classes["FTTransformerFieldToken"](
        numeric_field_count=numeric_count,
        categories=categories,
        d_token=architecture["d_token"],
        n_layers=architecture["n_layers"],
        n_heads=architecture["n_heads"],
        ffn_factor=architecture["d_ffn_factor"],
        attention_dropout=architecture["attention_dropout"],
        ffn_dropout=architecture["ffn_dropout"],
        residual_dropout=architecture["residual_dropout"],
        initialization=architecture["initialization"],
        token_bias=architecture["token_bias"],
        first_block_skips_first_normalization=architecture["first_block_skips_first_normalization"],
        d_out=architecture["d_out"],
    )
    decomposition = parameter_count_decomposition(
        numeric_count, len(categories), vocabulary_total,
        d_token=architecture["d_token"], n_layers=architecture["n_layers"],
        ffn_factor=architecture["d_ffn_factor"], d_out=architecture["d_out"],
        token_bias=architecture["token_bias"],
    )
    actual = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    if actual != decomposition["total"]:
        raise RuntimeError(
            f"实际可训练参数量 {actual} 与闭式 {decomposition['total']} 不符；分项：{decomposition}"
        )
    if model.token_count != TOKEN_COUNT_INCLUDING_CLS:
        raise RuntimeError(
            f"模型 Token 数 {model.token_count} 与身份门禁要求的 {TOKEN_COUNT_INCLUDING_CLS} 不符"
        )
    frozen = next(entry for entry in INPUT_CANDIDATES if entry["key"] == input_key)
    if frozen["parameter_count"] is not None and actual != frozen["parameter_count"]:
        raise RuntimeError(f"实际可训练参数量 {actual} 与冻结配置登记的 {frozen['parameter_count']} 不符")
    if frozen["parameter_count"] is None:
        logger.warning(
            "输入候选 %s 的冻结 parameter_count 仍为 null，本次实测为 %d，只记录不回填",
            input_key, actual,
        )
    _assert_parameter_dtypes(model)
    logger.info(
        "已构造 FT-Transformer 主干：输入候选=%s，数值 Token=%d，词表 Token=%d，词表总列数=%d，"
        "Token 数=%d，宽度=%d，层数=%d，头数=%d，可训练参数量=%d（闭式与实际一致）",
        input_key, numeric_count, len(categories), vocabulary_total, model.token_count,
        architecture["d_token"], architecture["n_layers"], architecture["n_heads"], actual,
    )
    return model


def build_control_model(config: dict[str, Any], target_total: int) -> tuple[Any, dict[str, Any]]:
    """构造整向量投影对照并做参数量三方比对。

    宽度由 ``solve_control_token_width`` 在官方 ``d_token`` 调参区间内机械搜索确定，
    取受头数整除约束的最优解（只有它可构造）。返回 ``(模型, 搜索与比对记录)``。
    """
    architecture = config["architecture"]
    control = config["control_branch"]
    if control.get("is_candidate") is not False:
        raise RuntimeError("整向量投影分支被标为候选，违反统一合同第 111 行的身份门禁")
    search = solve_control_token_width(
        target_total,
        control["input_dimension"],
        n_layers=architecture["n_layers"],
        ffn_factor=architecture["d_ffn_factor"],
        d_out=architecture["d_out"],
        n_heads=architecture["n_heads"],
        lower_bound=control["width_search_lower_bound"],
        upper_bound=control["width_search_upper_bound"],
    )
    chosen = search["buildable"]
    classes = transformer_classes()
    model = classes["WholeVectorProjectionControl"](
        input_dimension=control["input_dimension"],
        d_token=chosen["d_token"],
        n_layers=architecture["n_layers"],
        n_heads=architecture["n_heads"],
        ffn_factor=architecture["d_ffn_factor"],
        attention_dropout=architecture["attention_dropout"],
        ffn_dropout=architecture["ffn_dropout"],
        residual_dropout=architecture["residual_dropout"],
        initialization=architecture["initialization"],
        first_block_skips_first_normalization=architecture["first_block_skips_first_normalization"],
        d_out=architecture["d_out"],
    )
    closed_form = control_parameter_count(
        control["input_dimension"], d_token=chosen["d_token"], n_layers=architecture["n_layers"],
        ffn_factor=architecture["d_ffn_factor"], d_out=architecture["d_out"],
    )
    actual = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    if closed_form != chosen["parameter_count"]:
        raise RuntimeError(
            f"对照闭式 {closed_form} 与搜索记录 {chosen['parameter_count']} 不符，搜索实现已被破坏"
        )
    if actual != closed_form:
        raise RuntimeError(f"对照实际可训练参数量 {actual} 与闭式 {closed_form} 不符")
    if model.token_count != 1:
        raise RuntimeError(f"对照 Token 数必须为 1，实际 {model.token_count}")
    frozen_width = control.get("d_token")
    if frozen_width is not None and frozen_width != chosen["d_token"]:
        raise RuntimeError(f"对照实测宽度 {chosen['d_token']} 与冻结值 {frozen_width} 不符")
    frozen_parameters = control.get("parameter_count")
    if frozen_parameters is not None and actual != frozen_parameters:
        raise RuntimeError(f"对照实际参数量 {actual} 与冻结值 {frozen_parameters} 不符")
    _assert_parameter_dtypes(model)
    logger.info(
        "已构造%s：角色=%s，输入维=%d，Token 数=1，宽度=%d，可训练参数量=%d，"
        "对位目标=%d，差 %+d（%+.4f%%）。%s",
        CONTROL_DISPLAY_NAME, CONTROL_ROLE, control["input_dimension"], chosen["d_token"],
        actual, target_total, chosen["parameter_difference"],
        chosen["parameter_relative_difference"] * 100, CONTROL_IDENTITY_GATE_NOTE,
    )
    record = dict(search)
    record.update(
        {
            "key": CONTROL_KEY,
            "display_name": CONTROL_DISPLAY_NAME,
            "role": CONTROL_ROLE,
            "is_candidate": False,
            "closed_form_parameter_count": closed_form,
            "actual_parameter_count": actual,
        }
    )
    return model, record


# ---------------------------------------------------------------------------
# 命令行入口与阶段分发（任务 1；四个阶段的实现由任务 4 与任务 5 叠加）
# ---------------------------------------------------------------------------


def load_json(path: Path) -> dict[str, Any]:
    """读取 JSON 文件并要求顶层是对象。"""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FT-Transformer 逐字段 Token 协议 A 四格实验入口")
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


def _stage_not_implemented(stage: str, owner: str) -> None:
    """统一的未实现阶段出口：显式抛错并写明由哪个任务补全，不静默通过。"""
    raise NotImplementedError(
        f"阶段 {stage} 尚未实现，由{owner}补全。当前文件只交付任务 1 至 3："
        "配置与运行身份骨架、特征标记器与输入变换、Transformer 块与整向量投影对照。"
    )


def run_select_input_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段一：训练两个输入候选各自的 C00（固定阶段一优化器候选），封印胜出输入接口。"""
    _stage_not_implemented("select-input", "任务 4（训练循环与协议 A 选择）与任务 5（封印）")


def run_select_optimizer_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段二：在已封印输入接口上训练两个优化器候选的 C00，封印胜出优化器配方。"""
    _stage_not_implemented("select-optimizer", "任务 4（训练循环与协议 A 选择）与任务 5（封印）")


def run_cells_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段三：在已封印输入接口与优化器上执行 C00/C01/C10/C11 四格。"""
    _stage_not_implemented("cells", "任务 4（训练循环与协议 A 选择）与任务 5（三层断点恢复）")


def run_evaluate_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段四：全部选择封印后对 LSPR24 各评价一次，四格合计恰好 4 次。"""
    _stage_not_implemented("evaluate", "任务 5（封印与 LSPR24 评价）")


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
