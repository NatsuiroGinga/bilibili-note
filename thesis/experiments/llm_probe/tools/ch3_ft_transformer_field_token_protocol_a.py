# -*- coding: utf-8 -*-
"""FT-Transformer 逐字段 Token 协议 A 四格实验工具（任务 1 至 5）。

本文件实现：

- 任务 1：运行身份与结构冻结常量、配置校验 ``validate_config``、命令行入口与四个
  阶段的分发。
- 任务 2：字段基数收据消费 ``load_cardinality_receipt``、Token 布局与参数量闭式
  ``expected_parameter_count``，以及逐字段 Token 输入变换 ``fit_input_transform`` /
  ``FieldTokenTransform``（数值线性 Token 的分位数变换与二值直通、离散字段训练区词表
  加越界桶）。
- 任务 3：特征标记器 ``FeatureTokenizer``、多头注意力 ``MultiheadAttention``、
  Pre-Norm 块堆叠 ``TransformerBlocks``、FT-Transformer 主干 ``FTTransformerFieldToken``、
  整向量投影同结构近参数对照 ``WholeVectorProjectionControl``，以及宽度对位搜索
  ``solve_control_token_width`` 与参数量三方比对 ``build_model`` / ``build_control_model``。
- 任务 4：协议 A 机制外接模型 ``ProtocolACellModel``、等效微批冻结
  ``freeze_microbatch_plan``、无裁剪累积器 ``NoClipEffectiveBatchAccumulator``、
  训练与逐轮选择 ``train_cell``。
- 任务 5：三层同身份断点恢复、两阶段选择封印、四格 LSPR24 单次评价与聚合上报，
  即 ``run_select_input_stage``、``run_select_optimizer_stage``、``run_cells_stage``、
  ``run_evaluate_stage`` 四个生产阶段。

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
# Codex 2026-08-21 17:05 CST 裁决一：「后续严格采用……十进制 ffn_factor=1.333333333333333
# 经截断的口径」。该裁决是对前一轮实现代理「请裁决是否改判字面量口径」的直接回答，
# 故本运行按官方 TOML 的十进制字面量冻结，得 int(192*1.333333333333333)=255。
# 精确 4/3 得 h=256，只保留在 ffn_factor_rounding_diagnostic 里作对照事实，不参与冻结。
D_FFN_FACTOR = 1.333333333333333
# 精确 4/3（论文正文写法）。仅供取整口径诊断，改判口径时把 D_FFN_FACTOR 换成它即可。
EXACT_FOUR_THIRDS_D_FFN_FACTOR = 4 / 3
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

# 官方 TOML 中 d_ffn_factor 的十进制字面量，与上方冻结值同值，另立常量只为在
# ffn_factor_rounding_diagnostic 中显式表达「本运行取的就是官方字面量」。
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
# 目标年冻结缓存的流数身份；只在选择全部封印之后的评价阶段用于形状断言。
LSPR24_FLOW_COUNT = 20_227_356
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

CONTROL_KEY = "whole-vector-projection-structure-matched-control"
CONTROL_DISPLAY_NAME = "整向量投影同结构近参数对照（非FT-Transformer）"
CONTROL_ROLE = "对照，不是候选"
# Codex 2026-08-21 17:05 CST 裁决二：对照固定 d=192、L=3、n_heads=8，与主口径同宽、
# 同深、同头数；参数差 -18240 属既定事实，定位为「同结构近参数对照」而非精确同参数。
# 该措辞在日志、配置与封印中一律逐字使用，不得含糊为「同参数对照」。
CONTROL_PARAMETER_MATCH_SEMANTICS = "同结构近参数对照"
CONTROL_WIDTH_RULING = "codex_2026_08_21_17_05_cst_fixed_d192_l3_h8"
CONTROL_D_TOKEN = 192
CONTROL_IDENTITY_GATE_NOTE = (
    "统一合同第 111 行：把整条 83 维向量投影成单一 Token 的普通 Transformer 不能称为 "
    "FT-Transformer，其失败也不能否决该模型族"
)
# 对照没有嵌入表，只能消费整条 83 维数值向量，因此无论阶段一封印哪个输入候选，
# 对照一律使用「全字段数值 Token」候选的变换产出的 (n, 83) 数值矩阵。
CONTROL_INPUT_CANDIDATE_KEY = "ft-transformer-input-all-numeric-token"
# 对照只在 C00 结构（无因果前缀聚合、无 ELP）下训练与评价，其指标单列，不混入四格。
CONTROL_CELL = "C00"

# ---------------------------------------------------------------------------
# 机制外接常量（统一合同第 111 行的拟议接口：[CLS] 之后接 CPA、分类概率之后接 ELP）
# ---------------------------------------------------------------------------

# 因果前缀聚合的融合层：把 [CLS] 表示与因果前缀上下文拼接成 2d 再投影回 d。
# 与本仓库同族协议 A 工具（ch3_resmlp2_tabm_protocol_a_2x2.py 第 147 行、
# ch3_tabm32_paper_recipe_protocol_a.py 的 fusion_layer）同一机制形状，
# 使跨骨干的机制语义一致、四格之间参数量恒等。
MECHANISM_FUSION_INPUT_MULTIPLIER = 2
# ELP 的共享标量以 log(2) 初始化，即初值 p=2（同族工具第 306 与 367 行）。
MECHANISM_ELP_INITIAL_P = 2.0
# ELP 幂指数的数值安全区间与概率下限，沿用同族工具，属实现数值稳定常量而非科研阈值。
MECHANISM_ELP_P_MINIMUM = 1e-3
MECHANISM_ELP_P_MAXIMUM = 1e3
MECHANISM_ELP_PROBABILITY_FLOOR = 1e-7
MECHANISM_ELP_POOLED_CLAMP = 1e-6

# 时间轴（序列内逐流）与特征轴的轴约定；因果前缀聚合只沿时间轴累积。
SEQUENCE_BATCH_AXIS = 0
SEQUENCE_TIME_AXIS = 1
SEQUENCE_FEATURE_AXIS = 2

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
# 等效微批冻结（本任务独立冻结，不继承 TabM32 的 4×16）
# ---------------------------------------------------------------------------

# 有效批 64 序列是协议 A 的跨骨干共同预算，由协议而非本工具决定，不参与下面的搜索。
PROTOCOL_A_EFFECTIVE_BATCH_SEQUENCES = 64
# 微批只能取有效批的机械因子（精度合同 microbatch_factor_rule）。
# 选择规则：在全部因子中取「单微批前向保留激活的解析上界」不超过下方天花板的最大者。
# 天花板取 GPU 准入阈值的十分之一（20480 / 10 = 2048 MiB）。十分之一这个工程余量
# 的依据是本结构的三项同量级放大：注意力 softmax 走 FP32 岛因而同时存在 FP32 与
# 计算类型两份注意力矩阵、反向为每层保留与前向同量级的梯度缓冲、缓存分配器碎片，
# 三者叠加使真实峰值可达解析前向上界的数倍。该数值是工程资源余量而非科研阈值，
# 服务器第一次真实 optimizer.step() 的显存收据到手后必须复核并可修订。
MICROBATCH_ACTIVATION_CEILING_MIB = 2048
MICROBATCH_CEILING_DIVISOR = 10

# ---------------------------------------------------------------------------
# validate_config 内部使用的冻结期望值
# ---------------------------------------------------------------------------

_EXPECTED_ARCHITECTURE: dict[str, Any] = {
    "n_layers": N_LAYERS,
    "d_token": D_TOKEN,
    "n_heads": N_HEADS,
    "d_ffn_factor": D_FFN_FACTOR,
    # int(192 * 1.333333333333333) == 255（官方 TOML 十进制字面量经截断），
    # 与精确 4/3 的 256 相差一格前馈宽度、每层 (3d+2)=578 个参数。
    "d_ffn_hidden": 255,
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
    "effective_batch_size": PROTOCOL_A_EFFECTIVE_BATCH_SEQUENCES,
    "effective_batch_item_unit": EFFECTIVE_BATCH_ITEM_UNIT,
    "normalization_unit": NORMALIZATION_UNIT,
    # 本任务独立冻结：由 freeze_microbatch_plan 按解析张量上界在 64 的机械因子中
    # 选出的最大可行值，实算得 8×8；与 TabM32 的 4×16 无关，不继承。
    "micro_batch_sequences": 8,
    "gradient_accumulation_steps": 8,
    "microbatch_activation_ceiling_mib": MICROBATCH_ACTIVATION_CEILING_MIB,
    "microbatch_selection_rule": "largest_mechanical_factor_within_analytic_activation_ceiling",
    "epochs": 20,
    "steps_per_epoch": 1000,
    "gradient_clip_norm": None,
    "gradient_clip_policy": "official_ft_transformer_recipe_no_clipping",
    "non_finite_gradient_policy": "fail_immediately_no_silent_skip",
    # ELP 的训练信号权重是协议 A 的 2×2 机制定义的一部分，ResMLP2 与 TabM32 两条
    # 既有骨干均取 1.0；跨骨干比较要求机制定义一致，故此处沿用协议常量而非新设值。
    "auxiliary_loss_weight": 1.0,
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
    # 整向量投影对照的目标年评价单列计数，不并入四格的 4 次。
    "control_target_evaluation_calls": 1,
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
    bounds = {
        "micro_batch_flows": flows,
        "token_tensor_bytes": token_elements * element_bytes,
        "token_tensor_fp32_bytes": token_elements * HOST_FEATURE_DTYPE_BYTES,
        "attention_matrix_fp32_bytes": attention_elements * HOST_FEATURE_DTYPE_BYTES,
        "attention_matrix_compute_dtype_bytes": attention_elements * element_bytes,
        "ffn_expanded_bytes": ffn_elements * element_bytes,
        "host_dense_numeric_bytes": flows * DIJK_FEATURE_COUNT * HOST_FEATURE_DTYPE_BYTES,
        "compute_dtype_bytes": element_bytes,
    }
    bounds["retained_activation_bytes"] = retained_activation_bytes(
        micro_batch, length, token_count, architecture, element_bytes
    )
    return bounds


def retained_activation_bytes(
    micro_batch: int,
    sequence_length: int,
    token_count: int,
    architecture: dict[str, Any],
    element_bytes: int,
) -> int:
    """单微批训练前向为反向保留的激活字节数解析上界，按展开维度乘积逐项相加。

    逐项构成（每层，``flows = micro_batch × sequence_length``）：

    - 注意力矩阵两份：``softmax`` 走 FP32 岛，故同时存在 FP32 与计算类型两份
      ``flows × heads × T × T``；
    - 查询、键、值三份 ``flows × T × d``；
    - ReGLU 首层展开 ``flows × T × 2h``。

    再加上进入首块前的一份 Token 张量。这是**前向保留**的上界，不含反向自身的
    梯度缓冲与缓存分配器碎片；微批选择的天花板已按这些同量级放大留出余量。
    """
    d_token = architecture["d_token"]
    n_heads = architecture["n_heads"]
    n_layers = architecture["n_layers"]
    hidden = ffn_hidden_size(d_token, architecture["d_ffn_factor"])
    flows = micro_batch * sequence_length
    attention = flows * n_heads * token_count * token_count
    per_layer = (
        attention * HOST_FEATURE_DTYPE_BYTES
        + attention * element_bytes
        + 3 * flows * token_count * d_token * element_bytes
        + flows * token_count * 2 * hidden * element_bytes
    )
    return n_layers * per_layer + flows * token_count * d_token * element_bytes


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
    architecture = config["architecture"]
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
        activation = retained_activation_bytes(
            factor, length, TOKEN_COUNT_INCLUDING_CLS, architecture, element_bytes
        )
        activation_mib = activation / 2**20
        feasible = activation_mib <= ceiling_mib
        trace.append(
            {"micro_batch_sequences": factor, "retained_activation_mib": activation_mib, "feasible": feasible}
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
        "inherits_tabm32_values": False,
        "revisit_after_first_step_memory_receipt": True,
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

    这是任务 1 至 3 实测发现、Codex 2026-08-21 17:05 CST 裁决一定案的口径分歧：
    ``int(192*(4/3)) == 256`` 而 ``int(192*1.333333333333333) == 255``，
    每层前馈相差 ``(3d+2)`` 个参数。以论文表 12 的自检基准（100 个数值特征、
    0 个类别特征）代入，前者得 930241、后者得 928507；论文自报 ``929K``，
    按四舍五入命中后者，这正是裁决一采用官方十进制字面量的依据。
    本函数只报告两种口径的事实，冻结值由 ``D_FFN_FACTOR`` 决定。
    """
    reference_numeric_fields = 100
    exact = {
        "d_ffn_factor": EXACT_FOUR_THIRDS_D_FFN_FACTOR,
        "ffn_hidden_size": ffn_hidden_size(d_token, EXACT_FOUR_THIRDS_D_FFN_FACTOR),
        "paper_reference_total": expected_parameter_count(
            reference_numeric_fields, 0, 0, d_token=d_token,
            ffn_factor=EXACT_FOUR_THIRDS_D_FFN_FACTOR,
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
        "frozen_choice": "official_toml_literal",
        "frozen_choice_reason": (
            "Codex 2026-08-21 17:05 CST 裁决一：后续严格采用十进制 "
            "ffn_factor=1.333333333333333 经截断的口径；论文自报 929K 按四舍五入命中该口径的 928507"
        ),
        "superseded_choice": "exact_four_thirds",
        "ruling_two_quoted_totals_use_superseded_choice": {
            "note": (
                "裁决二引用的 926017（主口径）与 907777（对照）来自裁决前按 4/3 计算的汇报，"
                "在裁决一口径下分别为 924283 与 906043；两者之差 -18240 与口径无关，恒定不变"
            ),
            "control_minus_main_parameter_difference_is_invariant": -18240,
        },
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
            "Codex 裁定对照匹配总参数量，禁止改成只匹配主干"
        )
    if control.get("parameter_match_semantics") != CONTROL_PARAMETER_MATCH_SEMANTICS:
        raise ValueError(
            f"control_branch.parameter_match_semantics 必须逐字为「{CONTROL_PARAMETER_MATCH_SEMANTICS}」："
            "Codex 2026-08-21 17:05 CST 裁决二要求该措辞在配置、日志与封印中一律不得含糊为「同参数对照」"
        )
    if control.get("d_token") != CONTROL_D_TOKEN:
        raise ValueError(
            f"control_branch.d_token 必须为 {CONTROL_D_TOKEN}："
            "Codex 裁决二已固定对照与主口径同宽、同深、同头数，宽度不再由搜索决定"
        )
    if control.get("n_layers") != N_LAYERS or control.get("n_heads") != N_HEADS:
        raise ValueError("control_branch 的层数与头数必须与 FT-T 主口径相同（裁决二：同深、同头数）")
    if control.get("width_ruling") != CONTROL_WIDTH_RULING:
        raise ValueError("control_branch.width_ruling 未登记 Codex 固定宽度的裁决来源")
    if control.get("input_candidate_key") != CONTROL_INPUT_CANDIDATE_KEY:
        raise ValueError(
            f"control_branch.input_candidate_key 必须为 {CONTROL_INPUT_CANDIDATE_KEY}："
            "对照没有嵌入表，只能消费全字段数值 Token 候选产出的 83 维数值向量"
        )
    if control.get("cell") != CONTROL_CELL:
        raise ValueError(f"control_branch.cell 必须为 {CONTROL_CELL}：对照只在无机制结构下训练与评价")
    if control.get("metrics_reported_separately_from_four_cells") is not True:
        raise ValueError("control_branch.metrics_reported_separately_from_four_cells 必须为真：对照指标单列")
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
            "architecture.d_ffn_factor 必须为官方 TOML 的十进制字面量 1.333333333333333"
            "（Codex 2026-08-21 17:05 CST 裁决一）；精确 4/3 在 d_token=192 处取整为 256 "
            "而不是 255，两者不可混用"
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
    # 微批不是抄来的数：这里用与运行时同一函数重新推导一次，冻结值必须与推导一致，
    # 否则任何人手改配置里的微批都会在 --validate-config 阶段被拦下。
    derived = freeze_microbatch_plan(config, profile)
    if derived["micro_batch_sequences"] != micro_batch or derived["gradient_accumulation_steps"] != accumulation:
        raise ValueError(
            f"training 冻结的微批 {micro_batch}×{accumulation} 与按解析张量上界重新推导的 "
            f"{derived['micro_batch_sequences']}×{derived['gradient_accumulation_steps']} 不一致；"
            f"推导依据：{derived['selection_trace']}"
        )

    if config.get("swanlab") != _EXPECTED_SWANLAB:
        raise ValueError("swanlab 上报身份合同不符")

    if config.get("single_run_directly_comparable") is not True:
        raise ValueError("single_run_directly_comparable 必须为真")
    if config.get("formal_paper_evidence") is not False or config.get("independent_test") is not False:
        raise ValueError("本次运行不能宣称正式论文证据或独立测试")

    diagnostic = ffn_factor_rounding_diagnostic(architecture["d_token"])
    logger.info(
        "前馈宽度取整口径事实：官方 TOML 字面量 %.15f 得 h=%d、论文自检基准总参数 %d（论文自报 929K）；"
        "精确 4/3 得 h=%d、总参数 %d。Codex 裁决一：本运行按官方十进制字面量冻结。",
        OFFICIAL_LITERAL_D_FFN_FACTOR,
        diagnostic["official_toml_literal"]["ffn_hidden_size"],
        diagnostic["official_toml_literal"]["paper_reference_total"],
        diagnostic["exact_four_thirds"]["ffn_hidden_size"],
        diagnostic["exact_four_thirds"]["paper_reference_total"],
    )
    logger.warning(
        "裁决内部数字冲突已按裁决一处置：裁决二引用的主口径 926017 与对照 907777 是裁决前按 4/3 "
        "计算的汇报值，在本运行冻结的字面量口径下分别为 %d 与 %d；两者之差 %d 与口径无关、恒定不变，"
        "裁决二的结构规定（d=192、L=3、n_heads=8、同结构近参数对照、否决 d=168/L=4）已全部照办。",
        expected_parameter_count(
            NUMERIC_TOKEN_FIELD_COUNT, VOCABULARY_TOKEN_FIELD_COUNT, 14, d_token=architecture["d_token"]
        ),
        control_parameter_count(DIJK_FEATURE_COUNT, d_token=CONTROL_D_TOKEN),
        diagnostic["ruling_two_quoted_totals_use_superseded_choice"][
            "control_minus_main_parameter_difference_is_invariant"
        ],
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
        frozen_state: dict[str, Any],
    ) -> None:
        self.candidate_key = candidate_key
        self.state_hash = state_hash
        # Codex 裁决六：全部变换状态、词表、OOV 率与变换哈希写入收据。
        # 这里保留拟合时构造的完整状态字典，供选择封印逐字登记。
        self.frozen_state = frozen_state
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
        # 诊断计数器，不属于冻结状态，也不参与 state_hash。按数据分区分别累计，
        # 以便封印里分开登记源年与目标年的越界率（Codex 裁决六）。
        self.regions: tuple[str, ...] = ("source", "target")
        self.zero_one_absorption_counts: dict[str, dict[str, int]] = {
            region: {numeric_field_names[slot]: 0 for slot in zero_one_slots}
            for region in self.regions
        }
        self.out_of_vocabulary_counts: dict[str, dict[str, int]] = {
            region: {name: 0 for name in vocabulary_field_names} for region in self.regions
        }
        self.applied_row_counts: dict[str, int] = {region: 0 for region in self.regions}
        self._applied_region = "source"
        self._absorption_warned: set[str] = set()

    def switch_region(self, region: str) -> None:
        """切换 ``apply`` 的计数分区；只影响诊断计数，绝不改变任何冻结状态。"""
        if region not in self.applied_row_counts:
            raise ValueError(f"未知计数分区：{region}")
        self._applied_region = region

    def receipt(self) -> dict[str, Any]:
        """变换收据：冻结状态、词表、越界率与哈希，供选择封印与目标年评价逐项登记。"""
        rows = dict(self.applied_row_counts)
        return {
            "candidate_key": self.candidate_key,
            "state_hash": self.state_hash,
            "fitted_row_count": self.fitted_row_count,
            "quantile_landmark_count": self.quantile_landmark_count,
            "numeric_field_count": self.numeric_field_count,
            "vocabulary_field_count": self.vocabulary_field_count,
            "categories": list(self.categories),
            "frozen_state": self.frozen_state,
            "applied_row_counts": rows,
            "out_of_vocabulary_counts": {
                region: dict(counts) for region, counts in self.out_of_vocabulary_counts.items()
            },
            "out_of_vocabulary_rate": {
                region: {
                    name: (count / rows[region] if rows[region] else None)
                    for name, count in counts.items()
                }
                for region, counts in self.out_of_vocabulary_counts.items()
            },
            "zero_one_absorption_counts": {
                region: dict(counts) for region, counts in self.zero_one_absorption_counts.items()
            },
            "fitted_on": "lspr23_protocol_a_training_region_effective_flows_only",
            "applied_only_never_refitted_on_target": True,
        }

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
        region = self._applied_region
        self.applied_row_counts[region] += row_count
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
                self.zero_one_absorption_counts[region][name] += absorbed
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
                self.out_of_vocabulary_counts[region][name] += missed
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
        frozen_state=state,
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

    class ProtocolACellModel(nn.Module):
        """协议 A 单格模型：骨干加两个机制开关，四格共用同一结构与同一参数量。

        机制位置取统一合同第 111 行记载的拟议接口（采用而非强制）：

        - **因果前缀聚合（CPA）接在 ``[CLS]`` 之后**。骨干逐流给出 ``(N,T,d)`` 的
          ``[CLS]`` 表示，沿序列时间轴做掩码因果前缀均值得到上下文，再与表示拼接成
          ``2d`` 经一层融合投影回 ``d``。``aggregate`` 为假时上下文置零后**仍然拼接**，
          因此四格的参数量与张量形状完全一致，机制差异只来自上下文是否携带信息。
        - **可学幂平均池化（ELP）接在分类概率之后**，由共享标量 ``p_log`` 参数化。
          四格都持有该标量（与同族协议 A 工具一致），只有 ``learned_lp`` 为真的格
          在训练目标里使用它，从而使四格参数量恒等。

        字段内注意力只在同一条流的 ``83+1`` 个 Token 之间进行，绝不跨流；跨流关系
        全部由沿时间轴的因果前缀聚合承担，且只读取当前及严格过去时刻。
        """

        def __init__(self, backbone: nn.Module, d_token: int, aggregate: bool, learned_lp: bool) -> None:
            super().__init__()
            self.backbone = backbone
            self.aggregate = aggregate
            self.learned_lp = learned_lp
            self.d_token = d_token
            self.fusion = nn.Linear(MECHANISM_FUSION_INPUT_MULTIPLIER * d_token, d_token)
            self.p_log = nn.Parameter(torch.tensor(math.log(MECHANISM_ELP_INITIAL_P)))

        @property
        def p(self) -> torch.Tensor:
            return torch.exp(self.p_log).clamp(MECHANISM_ELP_P_MINIMUM, MECHANISM_ELP_P_MAXIMUM)

        def flow_representation(
            self, x_num: torch.Tensor, x_cat: torch.Tensor | None, valid: torch.Tensor
        ) -> torch.Tensor:
            """``(N,T,F)``（可选 ``(N,T,C)``）与 ``(N,T)`` 进，``(N,T,d)`` 的融合表示出。"""
            if x_num.ndim != 3 or valid.ndim != 2 or valid.shape != x_num.shape[:2]:
                raise RuntimeError(
                    f"协议 A 输入必须是 N×T×F 与 N×T，实际 {tuple(x_num.shape)} 与 {tuple(valid.shape)}"
                )
            batch, length = valid.shape
            flat_num = x_num.reshape(batch * length, x_num.shape[SEQUENCE_FEATURE_AXIS])
            flat_cat = (
                x_cat.reshape(batch * length, x_cat.shape[SEQUENCE_FEATURE_AXIS])
                if x_cat is not None
                else None
            )
            # 逐流独立走特征标记器与块堆叠：注意力只在一条流的 Token 之间进行。
            representation = self.backbone.encode(flat_num, flat_cat).reshape(batch, length, self.d_token)
            mask = valid.to(torch.float32)
            representation = representation * mask.unsqueeze(-1).to(representation.dtype)

            if self.aggregate:
                # 因果前缀累积属精度合同的 reduction 敏感计算，进 FP32 岛：
                # 长度 128 的前缀和在 BF16 下会累积可观舍入误差。
                with precision.fp32_island(
                    representation, mask, device_type=representation.device.type, torch_module=torch
                ) as (representation32, mask32):
                    counts = torch.cumsum(mask32, SEQUENCE_TIME_AXIS).clamp(min=1.0).unsqueeze(-1)
                    context32 = torch.cumsum(representation32, SEQUENCE_TIME_AXIS) / counts
                    context32 = context32 * mask32.unsqueeze(-1)
                context = context32.to(representation.dtype)
            else:
                context = torch.zeros_like(representation)

            # 机制边界：因果前缀聚合只沿时间轴，上下文必须与表示同形；
            # 任何跨序列的求和、拼接或注意力都会改变形状，从而在此立即失败。
            if context.shape != representation.shape:
                raise RuntimeError(
                    "因果前缀聚合越出时间轴：上下文张量必须与表示同形，"
                    f"实际 {tuple(context.shape)} 对 {tuple(representation.shape)}"
                )
            return self.fusion(torch.cat((representation, context), dim=-1))

        def forward(
            self, x_num: torch.Tensor, x_cat: torch.Tensor | None, valid: torch.Tensor
        ) -> torch.Tensor:
            """返回逐流对数几率 ``(N,T)``。"""
            return self.backbone.predict(self.flow_representation(x_num, x_cat, valid))

        def flow_probability(self, logits: torch.Tensor) -> torch.Tensor:
            """概率归一化属敏感计算，在 FP32 岛内完成。"""
            with precision.fp32_island(
                logits, device_type=logits.device.type, torch_module=torch
            ) as (logits32,):
                probabilities = torch.sigmoid(logits32)
            return probabilities

    _MODULE_CACHE.update(
        {
            "reglu": reglu,
            "FeatureTokenizer": FeatureTokenizer,
            "MultiheadAttention": MultiheadAttention,
            "TransformerBlocks": TransformerBlocks,
            "PredictionHead": PredictionHead,
            "FTTransformerFieldToken": FTTransformerFieldToken,
            "WholeVectorProjectionControl": WholeVectorProjectionControl,
            "ProtocolACellModel": ProtocolACellModel,
        }
    )
    return _MODULE_CACHE


def mechanism_parameter_count(d_token: int) -> int:
    """机制外接的可训练参数量闭式 ``2d^2 + d + 1``。

    ``2d^2 + d`` 是把 ``[CLS]`` 表示与因果前缀上下文拼接后的融合层
    ``nn.Linear(2d, d)``，``+1`` 是 ELP 的共享标量 ``p_log``。四格都持有这两项，
    因此四格参数量恒等；对照分支同样外接同一机制，故对照与主口径的参数差
    与机制无关，恒等于骨干之差。
    """
    return MECHANISM_FUSION_INPUT_MULTIPLIER * d_token * d_token + d_token + 1


def learned_lp_pool(scores: Any, valid: Any, p_value: Any) -> Any:
    """实体级可学幂平均池化，公式与同族协议 A 工具逐字一致。

    ``scores`` 必须是逐流概率 ``N×T``、``valid`` 是同形掩码。对数、幂与掩码归约
    都属精度合同登记的敏感计算，全部在 FP32 岛内完成。
    """
    import torch

    if scores.ndim != 2 or valid.ndim != 2 or scores.shape != valid.shape:
        raise RuntimeError(
            f"ELP 池化输入必须是 N×T 概率与同形掩码，实际 {tuple(scores.shape)} 与 {tuple(valid.shape)}"
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
        # 机制外接后参数名带 backbone. 前缀，故用子串而不是前缀判断特征标记器；
        # ELP 的共享标量 p_log 是机制指数不是权重矩阵，与同族协议 A 工具一致地不衰减。
        excluded = (
            "tokenizer." in name
            or name in normalization_parameters
            or name.endswith(".bias")
            or name == "bias"
            or name.split(".")[-1] == "p_log"
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

    宽度由 Codex 2026-08-21 17:05 CST 裁决二**固定**为 ``d=192``，与 FT-T 主口径
    同宽、同深、同头数；``solve_control_token_width`` 只作对位事实登记，不再决定宽度。
    该裁决同时否决了能把差压到 ``-0.08%`` 的 ``d=168, L=4``，理由是不得以改变深度
    混入额外变量。因此本对照定位为**同结构近参数对照**，不是精确同参数对照。
    返回 ``(模型, 搜索与比对记录)``。
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
    # 裁定宽度优先于搜索结果；两者不一致时如实记录，不静默改用搜索解。
    ruled_width = control["d_token"]
    chosen = next(
        (entry for entry in [search["buildable"], *search["head_divisible_neighbours"]]
         if entry["d_token"] == ruled_width),
        None,
    )
    if chosen is None:
        chosen = {
            "d_token": ruled_width,
            "parameter_count": control_parameter_count(
                control["input_dimension"], d_token=ruled_width,
                n_layers=architecture["n_layers"], ffn_factor=architecture["d_ffn_factor"],
                d_out=architecture["d_out"],
            ),
            "head_divisible": ruled_width % architecture["n_heads"] == 0,
        }
        chosen["parameter_difference"] = chosen["parameter_count"] - target_total
        chosen["parameter_relative_difference"] = chosen["parameter_difference"] / target_total
    if chosen["d_token"] != search["buildable"]["d_token"]:
        logger.warning(
            "裁定的对照宽度 d=%d 与机械搜索的最优可构造宽度 d=%d 不同；按裁决二采用裁定宽度，"
            "搜索结果只作事实登记",
            ruled_width, search["buildable"]["d_token"],
        )
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
    frozen_parameters = control.get("parameter_count")
    if frozen_parameters is not None and actual != frozen_parameters:
        raise RuntimeError(f"对照实际参数量 {actual} 与冻结值 {frozen_parameters} 不符")
    _assert_parameter_dtypes(model)
    logger.info(
        "已构造%s：角色=%s，对位语义=%s，输入维=%d，Token 数=1，宽度=%d，层数=%d，头数=%d，"
        "可训练参数量=%d，对位目标=%d，差 %+d（%+.4f%%）。%s",
        CONTROL_DISPLAY_NAME, CONTROL_ROLE, CONTROL_PARAMETER_MATCH_SEMANTICS,
        control["input_dimension"], chosen["d_token"], architecture["n_layers"],
        architecture["n_heads"], actual, target_total, chosen["parameter_difference"],
        chosen["parameter_relative_difference"] * 100, CONTROL_IDENTITY_GATE_NOTE,
    )
    record = dict(search)
    record.update(
        {
            "key": CONTROL_KEY,
            "display_name": CONTROL_DISPLAY_NAME,
            "role": CONTROL_ROLE,
            "parameter_match_semantics": CONTROL_PARAMETER_MATCH_SEMANTICS,
            "width_ruling": CONTROL_WIDTH_RULING,
            "is_candidate": False,
            "ruled": chosen,
            "closed_form_parameter_count": closed_form,
            "actual_parameter_count": actual,
        }
    )
    return model, record


# ---------------------------------------------------------------------------
# 机制外接后的整格模型构造（任务 4）
# ---------------------------------------------------------------------------


def cell_parameter_count(
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
    """单格总参数量 = 骨干闭式 + 机制闭式；四格取值恒等。"""
    return (
        expected_parameter_count(
            numeric_field_count, categorical_field_count, vocabulary_total_columns,
            d_token=d_token, n_layers=n_layers, ffn_factor=ffn_factor, d_out=d_out,
            token_bias=token_bias,
        )
        + mechanism_parameter_count(d_token)
    )


def build_cell_model(
    config: dict[str, Any], cell: str, transform_or_projection: Any, *, input_key: str
) -> Any:
    """构造某一格的完整模型（骨干加机制），并做骨干与整格两级参数量比对。"""
    if cell not in CELLS:
        raise ValueError(f"未知实验格：{cell}")
    architecture = config["architecture"]
    backbone = build_model(config, transform_or_projection, input_key=input_key)
    classes = transformer_classes()
    model = classes["ProtocolACellModel"](
        backbone=backbone,
        d_token=architecture["d_token"],
        aggregate=CELLS[cell]["causal_prefix_aggregation"],
        learned_lp=CELLS[cell]["learned_lp_pooling"],
    )
    backbone_total = sum(p.numel() for p in backbone.parameters() if p.requires_grad)
    actual = sum(p.numel() for p in model.parameters() if p.requires_grad)
    expected_mechanism = mechanism_parameter_count(architecture["d_token"])
    if actual - backbone_total != expected_mechanism:
        raise RuntimeError(
            f"{cell} 机制参数量实测 {actual - backbone_total} 与闭式 {expected_mechanism} 不符"
        )
    _assert_parameter_dtypes(model)
    logger.info(
        "已构造 %s 整格模型：因果前缀聚合=%s，可学幂平均池化=%s，骨干参数=%d，机制参数=%d，"
        "整格可训练参数量=%d（四格恒等）",
        cell, CELLS[cell]["causal_prefix_aggregation"], CELLS[cell]["learned_lp_pooling"],
        backbone_total, expected_mechanism, actual,
    )
    return model


def build_control_cell_model(config: dict[str, Any], target_total: int) -> tuple[Any, dict[str, Any]]:
    """构造整向量投影对照的整格模型（同一 C00 结构与同一机制外接）。

    对照与主口径外接**同一份**机制，因此两者的整格参数差恒等于骨干之差，
    机制不参与对位。返回 ``(模型, 对位记录)``。
    """
    architecture = config["architecture"]
    backbone, record = build_control_model(config, target_total)
    classes = transformer_classes()
    model = classes["ProtocolACellModel"](
        backbone=backbone,
        d_token=record["ruled"]["d_token"],
        aggregate=CELLS[CONTROL_CELL]["causal_prefix_aggregation"],
        learned_lp=CELLS[CONTROL_CELL]["learned_lp_pooling"],
    )
    backbone_total = sum(p.numel() for p in backbone.parameters() if p.requires_grad)
    actual = sum(p.numel() for p in model.parameters() if p.requires_grad)
    expected_mechanism = mechanism_parameter_count(record["ruled"]["d_token"])
    if actual - backbone_total != expected_mechanism:
        raise RuntimeError(
            f"对照机制参数量实测 {actual - backbone_total} 与闭式 {expected_mechanism} 不符"
        )
    if record["ruled"]["d_token"] != architecture["d_token"]:
        raise RuntimeError(
            f"对照宽度 {record['ruled']['d_token']} 与主口径 {architecture['d_token']} 不同，"
            "违反裁决二的同宽要求"
        )
    _assert_parameter_dtypes(model)
    record["cell"] = CONTROL_CELL
    record["backbone_parameter_count"] = backbone_total
    record["mechanism_parameter_count"] = expected_mechanism
    record["cell_parameter_count"] = actual
    return model, record


# ---------------------------------------------------------------------------
# 运行制品原子写、哈希与资源采集（任务 4）
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
        "本运行的精度合同 cuda-bf16-amp-fp32-sensitive-v1 要求 CUDA，"
        "当前环境无可用 CUDA；非 CUDA 环境须先取得显式例外收据，本工具不静默降级"
    )


# ---------------------------------------------------------------------------
# 源年数组、协议 A 切分与主机侧视图（任务 4）
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
    """协议 A 源年切分：按实体随机留出验证集并切除时间尾部，逐字复用既有语义。

    切分统计必须与冻结身份逐项相等：实体 150680、训练序列 208598、验证序列 22444、
    训练与验证行交集 0。
    """
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


class ProtocolASourceView:
    """协议 A 源年数据的主机侧视图，按已冻结的输入变换逐微批供给逐字段 Token 特征。

    与整表物化不同，本视图逐微批取原值再过冻结变换：候选二变换后需要同时给出
    ``(n, F)`` 数值矩阵与 ``(n, C)`` 类别索引矩阵，两者按逐流展平的顺序对应。
    """

    def __init__(self, arrays: dict[str, Any], transform: FieldTokenTransform) -> None:
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

    def features(self, indices: Any) -> tuple[Any, Any]:
        """把 ``(n, T)`` 流索引展成 ``((n,T,F) float32, (n,T,C) int64 或 None)``。

        无效位置的索引仍会被变换，其贡献随后由掩码清零；保持矩形形状换取批处理效率。
        """
        import numpy as np

        flat = np.asarray(indices).reshape(-1)
        raw = np.asarray(self.matrix[flat], dtype=np.float32)
        numeric, categorical = self.transform.apply(raw)
        numeric = np.ascontiguousarray(
            numeric.reshape(indices.shape[0], indices.shape[1], self.transform.numeric_field_count)
        )
        if categorical is None:
            return numeric, None
        categorical = np.ascontiguousarray(
            categorical.reshape(
                indices.shape[0], indices.shape[1], self.transform.vocabulary_field_count
            )
        )
        return numeric, categorical


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
    """按优化器候选建 AdamW；权重衰减例外按论文表 12 的参数角色划分。

    协议 A 无学习率调度，此处不建 scheduler；官方 FT-T 配方无梯度裁剪，
    因此也不在此处准备任何裁剪阈值。
    """
    import torch

    candidate = next((entry for entry in OPTIMIZER_CANDIDATES if entry["key"] == optimizer_key), None)
    if candidate is None:
        raise ValueError(f"未知优化器候选：{optimizer_key}")
    groups = resolve_weight_decay_groups(model)
    optimizer = torch.optim.AdamW(
        [
            {"params": groups["parameters_with_weight_decay"], "weight_decay": candidate["weight_decay"]},
            {"params": groups["parameters_without_weight_decay"], "weight_decay": 0.0},
        ],
        lr=candidate["learning_rate"],
    )
    logger.info(
        "优化器候选 %s：学习率=%s，权重衰减=%s，衰减组 %d 个参数张量、例外组 %d 个，"
        "无学习率调度、无梯度裁剪",
        candidate["display_name"], candidate["learning_rate"], candidate["weight_decay"],
        len(groups["names_with_weight_decay"]), len(groups["names_without_weight_decay"]),
    )
    return optimizer, {
        **candidate,
        "weight_decay_groups": {
            "names_with_weight_decay": groups["names_with_weight_decay"],
            "names_without_weight_decay": groups["names_without_weight_decay"],
            "official_string_rule": groups["official_string_rule"],
            "divergence_from_official_string_rule": groups["divergence_from_official_string_rule"],
        },
    }


def _move_optimizer_state(optimizer: Any, device: Any) -> None:
    """把 ``optimizer.load_state_dict`` 恢复后仍留在 CPU 的张量状态搬到目标设备。"""
    import torch

    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                state[key] = value.to(device)


def evaluate_validation_flow_ap(
    config: dict[str, Any], model: Any, view: ProtocolASourceView, rows: Any, device: Any,
    profile: dict[str, Any],
) -> tuple[float, int]:
    """在 LSPR23 实体不相交验证集上计算逐流平均精度。

    推理批取训练微批的序列数。理由是可证的显存关系：同一批对象数下，``no_grad``
    不为反向保留任何逐层激活，峰值严格低于训练步；因此复用微批数不需要另立一个
    未经依据的推理批常数，也不会超过已经冻结的激活天花板。
    """
    import numpy as np
    import torch
    from sklearn.metrics import average_precision_score

    precision = _precision_module()
    length = config["training"]["sequence_length"]
    batch_sequences = config["training"]["micro_batch_sequences"]
    predictions: list[Any] = []
    labels: list[Any] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(rows), batch_sequences):
            chunk = rows[start : start + batch_sequences]
            indices, valid, flow_labels = view.gather_sequences(chunk, length)
            numeric, categorical = view.features(indices)
            numeric_t = torch.from_numpy(numeric).to(device)
            categorical_t = torch.from_numpy(categorical).to(device) if categorical is not None else None
            valid_t = torch.from_numpy(valid).to(device)
            with precision.autocast_context(profile, device.type, torch):
                logits = model(numeric_t, categorical_t, valid_t)
            probabilities = model.flow_probability(logits)
            flat_mask = valid.reshape(-1)
            predictions.append(probabilities.reshape(-1).float().cpu().numpy()[flat_mask])
            labels.append(flow_labels.reshape(-1)[flat_mask])
    model.train()
    scores = np.concatenate(predictions)
    targets = np.concatenate(labels)
    return float(average_precision_score(targets, scores)), int(len(scores))


# ---------------------------------------------------------------------------
# 无裁剪等效批累积器与训练循环（任务 4）
# ---------------------------------------------------------------------------


def no_clip_accumulator_class() -> Any:
    """返回 ``EffectiveBatchAccumulator`` 的无裁剪子类，延迟构造以免顶层导入 torch。

    共享精度运行时的 ``finish`` 硬性要求一个有限正的裁剪阈值并总是调用
    ``clip_grad_norm_``；而 Codex 2026-08-21 17:05 CST 裁决五明令**不启用梯度裁剪**，
    遵循 FT-Transformer 官方配方（``lib/deep.py`` 的训练循环没有任何 ``clip_grad``），
    并要求**非有限梯度直接失败**而不是静默跳过。

    这里用子类而不是改共享框架：``begin``/``backward``/``receipt`` 完全继承，
    一次清梯度、按 ``sum`` 累加再除以全部有效单位、一步一更新的语义逐字保留；
    只有 ``finish`` 改为「校验同样的不变量 → 计算真实梯度范数并断言有限 → 直接
    ``optimizer.step()``」。梯度范数只作诊断记录，不用于缩放或裁剪。
    """
    import torch

    from neural_precision_runtime import ContractValidationError, EffectiveBatchAccumulator

    if not hasattr(torch.nn.utils, "get_total_norm"):
        raise RuntimeError(
            "目标 PyTorch 缺少 torch.nn.utils.get_total_norm（PyTorch 2.6 起提供）；"
            "本工具用它在不裁剪的前提下计算梯度范数并断言有限，须升级或显式改判裁剪策略"
        )

    class NoClipEffectiveBatchAccumulator(EffectiveBatchAccumulator):
        """按官方 FT-Transformer 配方在完整有效批边界只更新一次、不裁剪梯度。"""

        def finish(  # type: ignore[override]
            self,
            model_parameters: Any,
            optimizer: Any,
            torch_module: Any,
            max_grad_norm: float | None = None,
            scaler: Any | None = None,
        ) -> Any:
            if not self._started or self._finished:
                raise ContractValidationError("有效批尚未开始或已经完成")
            if self.consumed_valid_units != self.total_valid_units:
                raise ContractValidationError("有效单位尚未全部反向，禁止更新")
            if self.expected_microbatches is not None and self.microbatch_count != self.expected_microbatches:
                raise ContractValidationError("实际微批数与合同不符")
            if scaler is not None:
                raise ContractValidationError("BF16 默认精度配置不得使用 GradScaler")
            if max_grad_norm is not None:
                raise ContractValidationError(
                    "本运行按官方 FT-Transformer 配方不裁剪梯度，禁止传入裁剪阈值"
                )
            gradients = [
                parameter.grad for parameter in model_parameters if parameter.grad is not None
            ]
            if not gradients:
                raise ContractValidationError("完整有效批反向后没有任何梯度，训练图已断开")
            # error_if_nonfinite=True 直接实现「非有限梯度立即失败」，不静默跳过该步。
            gradient_norm = torch_module.nn.utils.get_total_norm(
                gradients, norm_type=2.0, error_if_nonfinite=True
            )
            optimizer.step()
            self._finished = True
            return gradient_norm

    return NoClipEffectiveBatchAccumulator


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
    control_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """训练一格并按协议 A 选择检查点，支持三层同身份断点恢复。

    梯度累积、精度与资源收据复用 ``tools/neural_precision_runtime.py``：有效批起点
    一次 ``zero_grad(set_to_none=True)``，每个微批把 FP32 岛内求和得到的标量损失交给
    累积器（内部统一除以本步的全部有效流数），全部微批反向完成后**不裁剪**、
    只更新一次；梯度非有限即失败。

    选择规则：跑满 ``epochs`` 轮、每轮 ``steps_per_epoch`` 步，不早停、无学习率调度；
    每轮结束在实体不相交验证集上算逐流平均精度，用**严格大于**更新最优，
    因此并列保留最早轮次。

    三层同身份断点恢复：

    - **完成层**：``checkpoints/selected-{cell}.pt`` 与 ``receipts/selection-{cell}.json``
      同时存在时，只有传了 ``--resume``、收据 ``identity`` 等于本次调用的 ``identity``、
      且收据登记的检查点 ``sha256`` 等于实测哈希，才直接复用并跳过训练；否则抛错拒绝。
    - **在途层**：每轮全部 ``optimizer.step()`` 完成后原子写 ``inflight/{cell}.pt``，
      内容含精度配置、微批量、累积步数、采样器状态与四路随机状态（由
      ``build_checkpoint_runtime_state`` 构造、``validate_checkpoint_runtime_state`` 校验）。
      半个有效批中断时该轮从未落盘，恢复会整轮重放，不会出现「恢复部分累计梯度后跳过样本」。
    - **封印层**：由调用方的阶段函数负责，见 ``run_cells_stage``。

    ``control_record`` 非空时训练的是整向量投影对照而不是 FT-T 候选，其结果单列。
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
    micro_batch = training["micro_batch_sequences"]
    accumulation_steps = training["gradient_accumulation_steps"]
    effective_batch = training["effective_batch_size"]
    length = training["sequence_length"]
    device_type = device.type
    is_control = control_record is not None
    # 对照分支的 cell 名是运行身份键而不是四格之一，其机制开关按 C00 结构取。
    mechanism_cell = CONTROL_CELL if is_control else cell
    if mechanism_cell not in CELLS:
        raise ValueError(f"未知实验格：{cell}")
    uses_lp = CELLS[mechanism_cell]["learned_lp_pooling"]
    branch_name = CONTROL_DISPLAY_NAME if is_control else DISPLAY_NAME
    label = f"{cell}{'（对照）' if is_control else ''}"

    # 精度合同：核验设备能力与配置一致，再核验批量因子自洽。
    contract, profile, profile_id = resolve_precision_profile(device_type, torch, precision_contract)
    plan = precision.validate_microbatch_plan(
        effective_batch, micro_batch, accumulation_steps, NORMALIZATION_UNIT, is_tail_batch=False
    )
    frozen_plan = freeze_microbatch_plan(config, profile)
    if (
        frozen_plan["micro_batch_sequences"] != micro_batch
        or frozen_plan["gradient_accumulation_steps"] != accumulation_steps
    ):
        raise RuntimeError(f"运行时重新推导的等效微批与配置不符：{frozen_plan}")
    scaler = precision.create_grad_scaler(profile, torch)
    if scaler is not None:
        raise RuntimeError("BF16 默认精度配置不得创建 GradScaler，实际创建了缩放器")
    # 对照把整条向量投影成单一 Token，其序列长度恒为 1，张量上界按 1 个 Token 计。
    bounds = tensor_upper_bounds(config, 1 if is_control else TOKEN_COUNT_INCLUDING_CLS, profile)
    logger.info(
        "%s 张量上界（按展开维度乘积，非参数量）：单微批流数=%d，Token 张量=%.2f MiB（%s）/"
        "%.2f MiB（FP32 保守口径），注意力矩阵=%.2f MiB（FP32 岛口径），ReGLU 展开=%.2f MiB，"
        "为反向保留的激活合计=%.2f MiB（天花板 %d MiB）",
        label, bounds["micro_batch_flows"],
        bounds["token_tensor_bytes"] / 2**20, profile["compute_dtype"],
        bounds["token_tensor_fp32_bytes"] / 2**20,
        bounds["attention_matrix_fp32_bytes"] / 2**20,
        bounds["ffn_expanded_bytes"] / 2**20,
        bounds["retained_activation_bytes"] / 2**20,
        frozen_plan["activation_ceiling_mib"],
    )

    random.seed(training["seed"])
    np.random.seed(training["seed"])
    torch.manual_seed(training["seed"])
    if device_type == "cuda":
        torch.cuda.manual_seed_all(training["seed"])

    if is_control:
        model, _ = build_control_cell_model(config, control_record["target_total"])
    else:
        model = build_cell_model(config, cell, view.transform, input_key=input_key)
    model = model.to(device)
    optimizer, optimizer_candidate = make_optimizer(config, model, optimizer_key)
    parameter_check = precision.validate_model_optimizer_fp32(model, optimizer, torch)
    logger.info(
        "%s 精度前置核验：FP32 浮点参数 %d 个，优化器浮点状态 %d 个（首次 step 前为 0）",
        label, parameter_check["checked_floating_parameters"],
        parameter_check["checked_floating_optimizer_states"],
    )

    positive_weight = torch.tensor(
        [(1.0 - view.flow_positive_rate) / max(view.flow_positive_rate, 1e-8)],
        device=device, dtype=torch.float32,
    )
    flow_loss = torch.nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    sequence_loss = torch.nn.BCELoss(reduction="none")
    sequence_positive_weight = view.sequence_positive_weight
    accumulator_class = no_clip_accumulator_class()

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

    # 在途层恢复：只有传了 --resume 且在途检查点存在时才尝试；身份、精度、
    # 微批量与累积步数任一不符都拒绝，不做部分拼接。
    if resume and inflight_path.is_file():
        inflight = torch.load(inflight_path, map_location="cpu", weights_only=False)
        if inflight.get("identity") != identity:
            raise RuntimeError(f"{label} 在途检查点身份与本次运行不符，拒绝恢复")
        runtime_state = inflight["runtime_state"]
        precision.validate_checkpoint_runtime_state(runtime_state)
        if (
            runtime_state["precision_profile_id"] != profile_id
            or runtime_state["microbatch_items"] != micro_batch
            or runtime_state["accumulation_steps"] != accumulation_steps
        ):
            raise RuntimeError(f"{label} 在途检查点的精度或批量合同与本次运行不符，拒绝恢复")
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
            label, start_epoch, int(inflight["epoch"]),
        )
    elif resume:
        logger.info("%s 未发现在途检查点，从第 1 轮开始（首次为本次运行的初次训练）", label)

    started = time.time()
    model.train()
    # 若恢复自一个已跑满全部轮次但尚未落最终检查点的在途状态，下方轮次循环
    # 不会执行任何一次，accumulator 需要有定义的占位。
    accumulator: Any = None
    last_gradient_norm = float("nan")

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

            accumulator = accumulator_class(
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
                numeric, categorical = view.features(indices[start:stop])
                numeric_t = torch.from_numpy(numeric).to(device)
                categorical_t = (
                    torch.from_numpy(categorical).to(device) if categorical is not None else None
                )
                valid_t = torch.from_numpy(micro_valid).to(device)
                labels_t = torch.from_numpy(flow_labels[start:stop]).to(device)
                mask32 = valid_t.to(torch.float32)
                labels32 = labels_t.to(torch.float32)
                with precision.autocast_context(profile, device_type, torch):
                    logits = model(numeric_t, categorical_t, valid_t)
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
            # 官方 FT-Transformer 配方不裁剪梯度；非有限梯度由累积器直接抛错。
            last_gradient_norm = float(accumulator.finish(list(model.parameters()), optimizer, torch))
            optimizer_step_count += 1
            processed_valid_flows += total_valid_flows
            processed_sequences += effective_batch
            running_loss += step_loss

            if optimizer_step_count == 1:
                state_check = precision.validate_model_optimizer_fp32(model, optimizer, torch)
                first_step_memory = {
                    "schema_version": "ch3-ft-transformer-first-step-memory-v1",
                    "identity": dict(identity),
                    "cell": cell,
                    "branch": branch_name,
                    "is_control": is_control,
                    "input_candidate": input_key,
                    "optimizer_candidate": optimizer_key,
                    "precision_profile_id": profile_id,
                    "tensor_upper_bounds": bounds,
                    "accumulation_plan": plan,
                    "frozen_microbatch_plan": frozen_plan,
                    "first_step_gradient_norm": last_gradient_norm,
                    "checked_floating_parameters": state_check["checked_floating_parameters"],
                    "checked_floating_optimizer_states": state_check["checked_floating_optimizer_states"],
                }
                if device_type == "cuda":
                    first_step_memory.update(gpu_memory_snapshot(torch, device))
                _atomic_json(
                    output_root / "receipts" / f"first-step-memory-{cell}-{input_key}-{optimizer_key}.json",
                    first_step_memory,
                )
                logger.info("%s 首次 optimizer.step() 后的显存快照：%s", label, first_step_memory)

            if step % heartbeat_interval == 0 or step == training["steps_per_epoch"]:
                elapsed = time.time() - started
                throughput = processed_sequences / max(elapsed, 1e-9)
                remaining = (total_sequences - processed_sequences) / max(throughput, 1e-9)
                logger.info(
                    "%s 心跳 epoch=%d/%d step=%d/%d 已处理序列=%d/%d 有效流=%d "
                    "梯度范数=%.6g 吞吐=%.1f 序列/秒 累计=%.1f 分 预计剩余=%.1f 分",
                    label, epoch, training["epochs"], step, training["steps_per_epoch"],
                    processed_sequences, total_sequences, processed_valid_flows,
                    last_gradient_norm, throughput, elapsed / 60.0, remaining / 60.0,
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
            label, epoch, training["epochs"], validation_ap, p_value,
            history[-1]["mean_training_loss"], scored_flows,
        )

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
                "schema_version": "ch3-ft-transformer-inflight-checkpoint-v1",
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
                label, epoch_seconds / 60.0, epoch_seconds / training["steps_per_epoch"],
                training["epochs"], epoch_seconds * training["epochs"] / 3600.0,
            )

    if best_state is None:
        raise RuntimeError(f"{label} 未产生可选检查点")
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
            "schema_version": "ch3-ft-transformer-protocol-a-selected-checkpoint-v1",
            "identity": dict(identity),
            "cell": cell,
            "branch": branch_name,
            "is_control": is_control,
            "input_candidate": input_key,
            "optimizer_candidate": optimizer_key,
            "numeric_field_count": view.transform.numeric_field_count,
            "vocabulary_field_count": view.transform.vocabulary_field_count,
            "input_transform_state_hash": view.transform.state_hash,
            "selected_epoch": best_epoch,
            "model": best_state,
            "runtime_state": runtime_state,
        },
    )

    external_mib = external_process_gpu_memory_mib(torch, device) if device_type == "cuda" else None
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
        "cell": cell,
        "branch": branch_name,
        "is_control": is_control,
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
        "parameter_count": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "backbone_parameter_count": sum(
            p.numel() for p in model.backbone.parameters() if p.requires_grad
        ),
        "mechanism_parameter_count": mechanism_parameter_count(model.d_token),
        "peak_gpu_allocated_mib": (
            int(torch.cuda.max_memory_allocated(device)) / 2**20 if device_type == "cuda" else None
        ),
        "peak_process_rss_mib": _process_peak_rss_mib(),
        "input_candidate": input_key,
        "optimizer_candidate": optimizer_key,
        "numeric_field_count": view.transform.numeric_field_count,
        "vocabulary_field_count": view.transform.vocabulary_field_count,
        "input_transform_state_hash": view.transform.state_hash,
        "precision_profile_id": profile_id,
        "precision_contract_schema_version": contract["schema_version"],
        "precision_resource_receipt": resource_receipt,
        "accumulation_plan": plan,
        "frozen_microbatch_plan": frozen_plan,
        "accumulation_receipt": (
            accumulator.receipt()
            if accumulator is not None
            else {"reused_from_inflight_without_new_optimizer_steps": True}
        ),
        "gradient_clip_norm": None,
        "gradient_clip_policy": config["training"]["gradient_clip_policy"],
        "last_gradient_norm": last_gradient_norm,
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
        label, best_epoch, best_ap, best_p, training_seconds / 60.0, checkpoint_path,
    )

    _atomic_json(receipt_path, {"identity": dict(identity), "selection": selection})
    inflight_path.unlink(missing_ok=True)
    return selection


# ---------------------------------------------------------------------------
# 运行身份、数据清单与制品持久化（任务 5）
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
        "schema_version": "ch3-ft-transformer-data-inventory-v1",
        "cache_root": str(cache_root),
        "files": files,
        "sha256": _canonical_sha256(files),
    }


def build_effective_flow_mask(
    indices: Any, mask: Any, train_rows: Any, flow_count: int
) -> tuple[Any, dict[str, Any]]:
    """训练有效流掩码：把训练区序列的有效位置映射到流索引，去重后置真。

    与诊断工具 ``tools/ch3_lspr23_field_cardinality_receipt.py`` 的
    ``build_effective_flow_mask`` 逐字同算法（含分块行数 4096），使本工具独立重算出的
    掩码哈希能够与收据登记的 ``effective_flow_mask_sha256`` 相互核验，
    而不是单方面信任收据。
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
    """本工具独立重算的运行身份：配置、代码、源数据与字段基数收据四路哈希。"""
    source_inventory = data_inventory(cache_root, SOURCE_ARRAYS)
    identity = {
        "schema_version": "ch3-ft-transformer-run-identity-v1",
        "config_sha256": _sha256_file(config_path),
        "code_sha256": _sha256_file(Path(__file__).resolve()),
        "source_data_inventory_sha256": source_inventory["sha256"],
        "cardinality_receipt_sha256": _sha256_file(cardinality_receipt_path),
    }
    return identity, source_inventory


def cell_identity(
    run_identity: dict[str, Any], *, input_candidate: str, optimizer_candidate: str, cell: str,
    branch: str = MODEL_KEY,
) -> dict[str, Any]:
    """把运行身份补齐为某次训练调用的完整身份，供 ``train_cell`` 的三层恢复比对。"""
    return {
        "schema_version": "ch3-ft-transformer-cell-identity-v1",
        "run_id": RUN_ID,
        "model_key": MODEL_KEY,
        **run_identity,
        "branch": branch,
        "input_candidate": input_candidate,
        "optimizer_candidate": optimizer_candidate,
        "cell": cell,
    }


def materialize_reused_cell(
    source_root: Path, target_root: Path, cell: str, identity: dict[str, Any]
) -> dict[str, Any]:
    """把选择阶段已完成、身份完全一致的格检查点与收据复制到最终输出根。

    这里再独立核对一次收据身份与检查点摘要，防止把不同配置、代码或数据版本下
    产出的制品部分拼接进最终四格。
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


def save_input_transform(path: Path, transform: FieldTokenTransform) -> None:
    """把已在 LSPR23 训练区拟合完成的输入变换整体持久化，供评价阶段只应用不拟合。"""
    import os
    import pickle

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        pickle.dump(transform, handle, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(temporary, path)


def load_input_transform(path: Path) -> FieldTokenTransform:
    """加载 ``cells`` 阶段封印的输入变换；``evaluate`` 阶段只应用，绝不重新拟合。"""
    import pickle

    if not path.is_file():
        raise FileNotFoundError(f"缺少已封印的输入变换：{path}，须先完成 cells 阶段")
    with path.open("rb") as handle:
        transform = pickle.load(handle)
    if not isinstance(transform, FieldTokenTransform):
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
    if arrays["X24"].shape[0] != LSPR24_FLOW_COUNT:
        raise RuntimeError(f"X24 流数不符：{arrays['X24'].shape}")
    logger.info("目标年数组已载入：X24=%s I24=%s", arrays["X24"].shape, arrays["I24"].shape)
    return arrays


def write_status(output_root: Path, state: str, stage: str, exit_code: int | None, detail: str) -> None:
    """原子写运行级状态文件，供人工与启动器只读核对进度。"""
    import time

    _atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-ft-transformer-field-token-protocol-a-status-v1",
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
        "artifacts/sealed-control-input-transform.pkl",
    )
    files: dict[str, Any] = {}
    for name in names:
        path = output_root / name
        if path.is_file():
            files[name] = {"bytes": path.stat().st_size, "sha256": _sha256_file(path)}
    for cell in (*CELL_ORDER, CONTROL_KEY):
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
            "schema_version": "ch3-ft-transformer-field-token-protocol-a-manifest-v1",
            "run_id": run_id,
            "files": files,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "complete_budget_curve_persisted": "complete-alert-budget-curves.npz" in files,
        },
    )


# ---------------------------------------------------------------------------
# 目标年指标与完整告警预算曲线（任务 5）
# ---------------------------------------------------------------------------


def entity_scores(
    flow_scores: Any, seen: Any, flow_entity: Any, entity_count: int, p_value: float | None
) -> Any:
    """按实体聚合逐流分数：``p_value`` 为空取实体内最大值，否则做共享 p 的 ELP 池化。

    与既有同族协议 A 工具同公式，供评价阶段区分「主指标（学习池化格用 ELP，其余格
    用最大池化）」与「最大池化指标（全部格统一用最大池化）」。
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
        np.clip(flow_scores[seen], MECHANISM_ELP_PROBABILITY_FLOOR, 1.0).astype(np.float64) ** p_value,
    )
    np.add.at(count, flow_entity[seen], 1.0)
    return np.where(
        count > 0, (numerator / np.maximum(count, 1.0)) ** (1.0 / p_value), -np.inf
    ).astype(np.float32)


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
    output_root: Path, cell: str, identity: dict[str, Any], cell_result: dict[str, Any],
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
            "schema_version": "ch3-ft-transformer-target-cell-receipt-v1",
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
    config: dict[str, Any], model: Any, transform: FieldTokenTransform, target: dict[str, Any],
    device: Any, profile: dict[str, Any],
) -> tuple[Any, Any]:
    """对 LSPR24 全量序列打分；输入变换只 ``apply``，绝不在目标年上重新拟合。

    评价阶段不训练、不替换检查点、不搜索阈值、不更新聚合指数或任何超参数，
    因此全程 ``torch.no_grad()``，不调用优化器也不调用 ``model.train()``。
    目标年出现的词表外取值一律落入训练区已冻结的越界桶，词表不扩充。
    """
    import numpy as np
    import torch

    precision = _precision_module()
    length = config["training"]["sequence_length"]
    batch_sequences = config["training"]["micro_batch_sequences"]
    indices_all = target["I24"]
    mask_all = target["M24"]
    labels = target["y24"]
    matrix = target["X24"]
    scores = np.zeros(len(labels), dtype=np.float32)
    seen = np.zeros(len(labels), dtype=bool)
    transform.switch_region("target")
    model.eval()
    try:
        with torch.no_grad():
            for start in range(0, len(indices_all), batch_sequences):
                stop = min(start + batch_sequences, len(indices_all))
                indices = np.ascontiguousarray(indices_all[start:stop, :length])
                valid = np.ascontiguousarray(mask_all[start:stop, :length] > 0.5)
                raw = np.asarray(matrix[indices.reshape(-1)], dtype=np.float32)
                numeric, categorical = transform.apply(raw)
                numeric = np.ascontiguousarray(
                    numeric.reshape(indices.shape[0], indices.shape[1], transform.numeric_field_count)
                )
                numeric_t = torch.from_numpy(numeric).to(device)
                categorical_t = None
                if categorical is not None:
                    categorical = np.ascontiguousarray(
                        categorical.reshape(
                            indices.shape[0], indices.shape[1], transform.vocabulary_field_count
                        )
                    )
                    categorical_t = torch.from_numpy(categorical).to(device)
                valid_t = torch.from_numpy(valid).to(device)
                with precision.autocast_context(profile, device.type, torch):
                    logits = model(numeric_t, categorical_t, valid_t)
                probabilities = model.flow_probability(logits)
                flat_indices = indices.reshape(-1)
                flat_valid = valid.reshape(-1)
                flat_probabilities = probabilities.reshape(-1).float().cpu().numpy()
                selected = flat_indices[flat_valid]
                scores[selected] = flat_probabilities[flat_valid]
                seen[selected] = True
    finally:
        transform.switch_region("source")
    return scores, seen


def publish_swanlab(config: dict[str, Any], result: dict[str, Any], output_root: Path) -> None:
    """创建 SwanLab 运行并上报聚合指标；只使用已核验存在的 ``Run`` 公开属性。

    核验依据（2026-08-13 本仓库事故记录）：SwanLab 0.9.0 的 ``Run`` 对象只公开
    ``id``/``name``/``path``/``url``/``dir``/``config``/``log*`` 七类属性，**没有
    ``public`` 属性**；本函数只读取 ``name``/``id``/``url`` 三个已核验字段用于收据
    留痕。创建运行前先机械断言工作区与项目名逐字等于冻结配置，不一致即退出且不上传。
    """
    destination = config["swanlab"]
    if destination != _EXPECTED_SWANLAB:
        raise RuntimeError("SwanLab 目的地与冻结配置不一致，拒绝创建运行或上传")
    if destination["workspace"] != _EXPECTED_SWANLAB["workspace"]:
        raise RuntimeError("SwanLab 工作区与本轮授权不符，拒绝创建运行")
    if destination["project"] != _EXPECTED_SWANLAB["project"]:
        raise RuntimeError("SwanLab 项目与本轮授权不符，拒绝创建运行")

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
            "protocol": "ft_transformer_field_token_protocol_a",
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
        metrics[f"target/{cell}_maximum_entity_ap"] = cell_target["maximum_entity_average_precision"]
        for key, value in cell_target["dr_at_fpr"].items():
            metrics[f"target/{cell}_dr_{key}"] = value
    control = result.get("control_branch")
    if control is not None and control.get("target") is not None:
        # 对照指标单列在 control/ 前缀下，不与四格的 target/ 前缀混写。
        metrics["control/source_validation_flow_ap"] = float(
            control["selection"]["validation_flow_ap"]
        )
        metrics["control/target_flow_ap"] = control["target"]["flow_average_precision"]
        metrics["control/target_entity_ap"] = control["target"]["entity_average_precision"]
        metrics["control/target_maximum_entity_ap"] = control["target"][
            "maximum_entity_average_precision"
        ]
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
            "schema_version": "ch3-ft-transformer-field-token-protocol-a-swanlab-receipt-v1",
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
# 命令行入口与阶段分发
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


def _prepare_source_stage(
    config: dict[str, Any], args: argparse.Namespace, stage: str
) -> dict[str, Any]:
    """四个源年阶段共用的准备工作：收据核验、身份重算、数组载入、切分与掩码对表。

    收据核验用纯标准库先做，随后才建立运行输出目录与载入数组；这样收据缺失时给出的
    是明确的中文原因，而不是误导性的目录创建或依赖导入失败。
    """
    config_path = Path(args.config).resolve()
    cache_root = Path(config["paths"]["cache_root"])
    output_root = Path(config["paths"]["output_root"])
    receipt_path = Path(config["paths"]["field_cardinality_receipt"])

    receipt = load_cardinality_receipt(str(receipt_path), config)
    write_status(output_root, "running", stage, None, f"阶段 {stage} 已通过收据核验，开始准备源年数据")

    run_identity, source_inventory = build_run_identity(config_path, cache_root, receipt_path)
    arrays = load_source_arrays(str(cache_root))
    train_rows, validation_rows, split_statistics = source_split(arrays, config)
    train_flow_mask, flow_mapping = build_effective_flow_mask(
        arrays["I23"], arrays["M23"], train_rows, LSPR23_FLOW_COUNT
    )
    if flow_mapping["effective_flow_mask_sha256"] != receipt["training_effective_flows"][
        "effective_flow_mask_sha256"
    ]:
        raise RuntimeError("本工具独立重算的训练有效流掩码与收据登记的哈希不一致，拒绝继续")
    return {
        "config_path": config_path,
        "cache_root": cache_root,
        "output_root": output_root,
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


def _field_manifest_hashes(config: dict[str, Any]) -> dict[str, str]:
    """字段清单与字段策略的规范化哈希，写入两级封印以固定输入合同。"""
    return {
        "field_order_sha256": _canonical_sha256(config["field_order"]),
        "field_policy_sha256": _canonical_sha256(config["field_policy"]),
        "architecture_sha256": _canonical_sha256(config["architecture"]),
    }


def run_select_input_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段一：训练两个输入候选各自的 C00（固定阶段一优化器候选），封印胜出输入接口。

    两个候选（全字段数值 Token 与仅两个协议字段词表 Token）是 Codex 2026-08-21
    17:05 CST 裁决三保留的**数据适配消融**，只由 LSPR23 选择。并列时按冻结候选表的
    固定顺序取候选一；只用 ``lspr23_entity_disjoint_validation_flow_ap`` 决策，
    不看实体 AP、告警预算、训练时间、显存或 LSPR24。
    """
    import time

    output_root = Path(config["paths"]["output_root"])
    seal_path = output_root / "input_selection_sealed.json"
    if seal_path.is_file():
        if not args.resume:
            raise RuntimeError(f"全新运行（未传 --resume）已存在输入接口封印，拒绝覆盖：{seal_path}")
        logger.info("阶段一封印已存在且传了 --resume，直接复用：%s", seal_path)
        return

    prepared = _prepare_source_stage(config, args, "select-input")
    run_identity = prepared["run_identity"]
    cache_root = prepared["cache_root"]
    fixed_optimizer = config["selection_stages"]["stage_one_fixed_optimizer"]
    device = _resolve_device()

    runs: dict[str, Any] = {}
    for candidate in sorted(INPUT_CANDIDATES, key=lambda item: item["order"]):
        key = candidate["key"]
        run_root = output_root / "selection-runs" / "select-input" / key
        transform = fit_input_transform(
            key, str(cache_root), prepared["train_flow_mask"], prepared["receipt"],
            config=config, seed=config["training"]["seed"],
        )
        view = ProtocolASourceView(prepared["arrays"], transform)
        identity = cell_identity(
            run_identity, input_candidate=key, optimizer_candidate=fixed_optimizer, cell="C00"
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
            "numeric_token_field_count": transform.numeric_field_count,
            "vocabulary_token_field_count": transform.vocabulary_field_count,
            "vocabulary_total_columns": sum(transform.categories),
            "token_count": transform.numeric_field_count + transform.vocabulary_field_count + 1,
            "backbone_parameter_count": expected_parameter_count(
                transform.numeric_field_count, transform.vocabulary_field_count,
                sum(transform.categories), d_token=config["architecture"]["d_token"],
            ),
            "cell_parameter_count": selection["parameter_count"],
            "input_transform_receipt": transform.receipt(),
            "selection": selection,
        }
        logger.info(
            "阶段一 %s（%s）训练完成：验证逐流AP=%.8f",
            key, candidate["display_name"], selection["validation_flow_ap"],
        )

    key_a, key_b = (entry["key"] for entry in sorted(INPUT_CANDIDATES, key=lambda item: item["order"]))
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
        "schema_version": "ch3-ft-transformer-input-selection-sealed-v1",
        "run_id": RUN_ID,
        "identity": run_identity,
        **_field_manifest_hashes(config),
        "source_data_inventory": prepared["source_inventory"],
        "source_split": prepared["split_statistics"],
        "cardinality_receipt_sha256": run_identity["cardinality_receipt_sha256"],
        "cardinality_receipt_flow_mapping": prepared["flow_mapping"],
        "candidate_order": [entry["key"] for entry in sorted(INPUT_CANDIDATES, key=lambda i: i["order"])],
        "candidates": [dict(entry) for entry in INPUT_CANDIDATES],
        "fixed_optimizer_candidate": fixed_optimizer,
        "runs": runs,
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_metric_full_precision": {key_a: ap_a, key_b: ap_b},
        "tie_break_rule": "fixed_table_order",
        "forbidden_tie_breakers": list(config["selection_stages"]["forbidden_tie_breakers"]),
        "selected_candidate": best_key,
        "selection_reason": reason,
        "target_year_arrays_read": 0,
        "target_evaluation_calls": 0,
        "sealed_at_unix": time.time(),
    }
    _atomic_json(seal_path, seal)
    write_status(output_root, "running", "select-input", 0, f"输入接口已封印：{best_key}")
    logger.info("阶段一封印完成：胜出输入候选=%s（%s）", best_key, reason)


def run_select_optimizer_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段二：在已封印输入接口上训练挑战者优化器的 C00，与阶段一结果比较后封印。

    两个 AdamW 候选学习率同为 ``1e-4``，只有权重衰减不同（``1e-5`` 与
    ``3.1622776601683794e-5``），是 Codex 裁决四保留的**官方范围内单变量源年选择**。
    不重训候选一：阶段一已用它训练过同一格，直接复用该结果比较。并列或候选一更高
    时取官方默认配方。
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

    prepared = _prepare_source_stage(config, args, "select-optimizer")
    run_identity = prepared["run_identity"]
    if run_identity != input_seal["identity"]:
        raise RuntimeError("阶段二独立重算的运行身份与阶段一封印不符，拒绝在不同配置/代码/数据版本间比较")

    stage_two_keys = list(config["selection_stages"]["stage_two_optimizer"])
    challengers = [entry["key"] for entry in OPTIMIZER_CANDIDATES if entry["key"] != fixed_optimizer_key]
    if stage_two_keys != [fixed_optimizer_key, *challengers]:
        raise RuntimeError("selection_stages.stage_two_optimizer 顺序与阶段一固定优化器候选不符")
    challenger_key = challengers[0]

    device = _resolve_device()
    transform = fit_input_transform(
        sealed_input_candidate, str(prepared["cache_root"]), prepared["train_flow_mask"],
        prepared["receipt"], config=config, seed=config["training"]["seed"],
    )
    view = ProtocolASourceView(prepared["arrays"], transform)
    challenger_identity = cell_identity(
        run_identity, input_candidate=sealed_input_candidate,
        optimizer_candidate=challenger_key, cell="C00",
    )
    challenger_selection = train_cell(
        config, "C00", sealed_input_candidate, challenger_key,
        output_root=output_root / "selection-runs" / "select-optimizer" / challenger_key,
        identity=challenger_identity, view=view,
        train_rows=prepared["train_rows"], validation_rows=prepared["validation_rows"],
        device=device, resume=args.resume,
    )

    incumbent_run = input_seal["runs"][sealed_input_candidate]
    incumbent_ap = float(incumbent_run["selection"]["validation_flow_ap"])
    challenger_ap = float(challenger_selection["validation_flow_ap"])
    if challenger_ap > incumbent_ap:
        best_key = challenger_key
        reason = f"挑战者（{challenger_key}）验证逐流AP={challenger_ap!r}严格高于官方默认{incumbent_ap!r}"
    elif challenger_ap == incumbent_ap:
        best_key = fixed_optimizer_key
        reason = f"两优化器候选验证逐流AP并列={incumbent_ap!r}，按论文默认配方取 {fixed_optimizer_key}"
    else:
        best_key = fixed_optimizer_key
        reason = f"官方默认（{fixed_optimizer_key}）验证逐流AP={incumbent_ap!r}高于挑战者{challenger_ap!r}"

    seal = {
        "schema_version": "ch3-ft-transformer-optimizer-selection-sealed-v1",
        "run_id": RUN_ID,
        "identity": run_identity,
        **_field_manifest_hashes(config),
        "sealed_input_candidate": sealed_input_candidate,
        "candidate_order": stage_two_keys,
        "candidates": [dict(entry) for entry in OPTIMIZER_CANDIDATES],
        "runs": {
            fixed_optimizer_key: incumbent_run,
            challenger_key: {
                "identity": challenger_identity,
                "display_name": next(
                    entry["display_name"] for entry in OPTIMIZER_CANDIDATES if entry["key"] == challenger_key
                ),
                "input_transform_receipt": transform.receipt(),
                "selection": challenger_selection,
            },
        },
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_metric_full_precision": {
            fixed_optimizer_key: incumbent_ap, challenger_key: challenger_ap
        },
        "tie_break_rule": "official_default_recipe_on_tie_or_loss",
        "forbidden_tie_breakers": list(config["selection_stages"]["forbidden_tie_breakers"]),
        "selected_candidate": best_key,
        "selection_reason": reason,
        "target_year_arrays_read": 0,
        "target_evaluation_calls": 0,
        "sealed_at_unix": time.time(),
    }
    _atomic_json(seal_path, seal)
    write_status(output_root, "running", "select-optimizer", 0, f"优化器已封印：{best_key}")
    logger.info("阶段二封印完成：胜出优化器候选=%s（%s）", best_key, reason)


def run_cells_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段三：用已封印的输入与优化器训练四格与整向量投影对照，全部完成后写选择封印。

    C00 只有在配置、代码、数据、字段基数收据与检查点身份完全一致时才复用阶段一或
    阶段二的完成运行；任一不符都以新运行身份在最终输出根重训，不做部分拼接。
    对照分支单列训练，其结果不进入四格，也不参与任何交互项。
    """
    import time

    output_root = Path(config["paths"]["output_root"])
    input_seal_path = output_root / "input_selection_sealed.json"
    optimizer_seal_path = output_root / "optimizer_selection_sealed.json"
    selection_frozen_path = output_root / "selection_frozen.json"

    if not input_seal_path.is_file() or not optimizer_seal_path.is_file():
        raise RuntimeError(
            "尚未完成阶段一或阶段二封印，禁止进入 cells 阶段："
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

    prepared = _prepare_source_stage(config, args, "cells")
    run_identity = prepared["run_identity"]
    if run_identity != input_seal["identity"] or run_identity != optimizer_seal["identity"]:
        raise RuntimeError("cells 阶段独立重算的运行身份与阶段一/阶段二封印不符")

    device = _resolve_device()
    transform = fit_input_transform(
        sealed_input_candidate, str(prepared["cache_root"]), prepared["train_flow_mask"],
        prepared["receipt"], config=config, seed=config["training"]["seed"],
    )
    view = ProtocolASourceView(prepared["arrays"], transform)
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

    cell_parameters = {cell: selections[cell]["parameter_count"] for cell in CELL_ORDER}
    if len(set(cell_parameters.values())) != 1:
        raise RuntimeError(f"四格参数量不相等，机制外接口径被破坏：{cell_parameters}")

    # 整向量投影对照：与主口径同宽、同深、同头数，外接同一份机制，只在 C00 结构下训练。
    # 它消费的是「全字段数值 Token」候选的 83 维数值向量，因为它没有嵌入表。
    control_transform = fit_input_transform(
        CONTROL_INPUT_CANDIDATE_KEY, str(prepared["cache_root"]), prepared["train_flow_mask"],
        prepared["receipt"], config=config, seed=config["training"]["seed"],
    )
    save_input_transform(
        output_root / "artifacts" / "sealed-control-input-transform.pkl", control_transform
    )
    control_view = ProtocolASourceView(prepared["arrays"], control_transform)
    control_target_total = cell_parameters[CONTROL_CELL] - mechanism_parameter_count(
        config["architecture"]["d_token"]
    )
    control_identity = cell_identity(
        run_identity, input_candidate=CONTROL_INPUT_CANDIDATE_KEY,
        optimizer_candidate=sealed_optimizer_candidate, cell=CONTROL_KEY, branch=CONTROL_KEY,
    )
    logger.info(
        "开始%s训练（%s；对位目标骨干参数=%d，宽度=%d、层数=%d、头数=%d 与主口径相同）",
        CONTROL_DISPLAY_NAME, CONTROL_PARAMETER_MATCH_SEMANTICS, control_target_total,
        CONTROL_D_TOKEN, config["architecture"]["n_layers"], config["architecture"]["n_heads"],
    )
    control_selection = train_cell(
        config, CONTROL_KEY, CONTROL_INPUT_CANDIDATE_KEY, sealed_optimizer_candidate,
        output_root=output_root, identity=control_identity, view=control_view,
        train_rows=prepared["train_rows"], validation_rows=prepared["validation_rows"],
        device=device, resume=args.resume,
        control_record={"target_total": control_target_total},
    )

    optimizer_record = next(
        entry for entry in OPTIMIZER_CANDIDATES if entry["key"] == sealed_optimizer_candidate
    )
    cell_hashes = {
        cell: {
            "checkpoint_sha256": selections[cell]["checkpoint"]["sha256"],
            "config_sha256": run_identity["config_sha256"],
            "code_sha256": run_identity["code_sha256"],
            "optimizer_candidate_sha256": _canonical_sha256(optimizer_record),
            "input_transform_state_hash": transform.state_hash,
            "random_state": {"seed": config["training"]["seed"]},
            "elp_parameter_p_at_selection": selections[cell]["p_at_selection"],
            "aggregation_rule": (
                "逐流 sigmoid 概率"
                + ("，再对唯一实体做共享标量 p 的可学幂平均池化(ELP)" if CELLS[cell]["learned_lp_pooling"] else "，实体级取最大池化")
            ),
        }
        for cell in CELL_ORDER
    }

    architecture = config["architecture"]
    seal = {
        "schema_version": "ch3-ft-transformer-selection-frozen-v1",
        "run_id": RUN_ID,
        "model_key": MODEL_KEY,
        "display_name": DISPLAY_NAME,
        "identity": run_identity,
        **_field_manifest_hashes(config),
        "official_source": config["official_source"],
        "d_ffn_factor_rounding": ffn_factor_rounding_diagnostic(architecture["d_token"]),
        "input_candidates": [dict(entry) for entry in INPUT_CANDIDATES],
        "optimizer_candidates": [dict(entry) for entry in OPTIMIZER_CANDIDATES],
        "field_policy": config["field_policy"],
        "dijk_feature_count": DIJK_FEATURE_COUNT,
        "lspr23_flow_count": LSPR23_FLOW_COUNT,
        "source_data_inventory": prepared["source_inventory"],
        "source_split": prepared["split_statistics"],
        "sample_order_sha256": _canonical_sha256(
            {
                "train_rows": prepared["train_rows"].tolist(),
                "validation_rows": prepared["validation_rows"].tolist(),
            }
        ),
        "cardinality_receipt_sha256": run_identity["cardinality_receipt_sha256"],
        "input_selection": input_seal,
        "optimizer_selection": optimizer_seal,
        "sealed_input_candidate": sealed_input_candidate,
        "sealed_optimizer_candidate": sealed_optimizer_candidate,
        "input_dimension": transform.numeric_field_count,
        "input_dimension_note": (
            "input_dimension 指 x_num 的列数，即数值线性 Token 的字段数；"
            "词表 Token 另由 vocabulary_token_field_count 与 vocabulary_total_columns 描述"
        ),
        "vocabulary_token_field_count": transform.vocabulary_field_count,
        "vocabulary_total_columns": sum(transform.categories),
        "token_count": transform.numeric_field_count + transform.vocabulary_field_count + 1,
        "backbone_parameter_count": expected_parameter_count(
            transform.numeric_field_count, transform.vocabulary_field_count,
            sum(transform.categories), d_token=architecture["d_token"],
        ),
        "mechanism_parameter_count": mechanism_parameter_count(architecture["d_token"]),
        "parameter_count": cell_parameters[CELL_ORDER[0]],
        "per_cell_parameter_count": cell_parameters,
        "all_cells_have_equal_parameter_count": True,
        "input_transform_receipt": transform.receipt(),
        "control_input_transform_receipt": control_transform.receipt(),
        "control_branch": {
            "key": CONTROL_KEY,
            "display_name": CONTROL_DISPLAY_NAME,
            "role": CONTROL_ROLE,
            "parameter_match_semantics": CONTROL_PARAMETER_MATCH_SEMANTICS,
            "width_ruling": CONTROL_WIDTH_RULING,
            "identity_gate_note": CONTROL_IDENTITY_GATE_NOTE,
            "is_candidate": False,
            "cell": CONTROL_CELL,
            "identity": control_identity,
            "input_candidate": CONTROL_INPUT_CANDIDATE_KEY,
            "d_token": CONTROL_D_TOKEN,
            "n_layers": architecture["n_layers"],
            "n_heads": architecture["n_heads"],
            "parameter_match_target_total": control_target_total,
            "backbone_parameter_count": control_selection["backbone_parameter_count"],
            "mechanism_parameter_count": control_selection["mechanism_parameter_count"],
            "cell_parameter_count": control_selection["parameter_count"],
            "parameter_difference_against_main": (
                control_selection["parameter_count"] - cell_parameters[CONTROL_CELL]
            ),
            "selection": control_selection,
            "metrics_reported_separately_from_four_cells": True,
        },
        "cells": selections,
        "cell_hashes": cell_hashes,
        "all_four_cells_sealed": True,
        "target_year_arrays_read": 0,
        "target_evaluation_calls": 0,
        "sealed_at_unix": time.time(),
    }
    _atomic_json(selection_frozen_path, seal)
    write_status(output_root, "computed", "cells", 0, "四格与对照训练完成、选择已封印，等待目标年评价")
    build_manifest(output_root, RUN_ID)
    logger.info(
        "四格选择封印完成：%s（每格参数量=%d，对照参数量=%d，差 %+d）",
        selection_frozen_path, cell_parameters[CELL_ORDER[0]],
        control_selection["parameter_count"],
        control_selection["parameter_count"] - cell_parameters[CONTROL_CELL],
    )


def _score_one_branch(
    config: dict[str, Any], seal: dict[str, Any], branch_key: str, checkpoint_relative: str,
    checkpoint_sha256: str, uses_lp: bool, transform: FieldTokenTransform, target: dict[str, Any],
    flow_entity: Any, entity_labels: Any, entity_count: int, device: Any, profile: dict[str, Any],
    output_root: Path, is_control: bool, call_index: int,
) -> tuple[dict[str, Any], dict[str, Any], float]:
    """对一个分支做一次且仅一次的目标年打分，返回 ``(格结果, 预算曲线, 峰值显存)``。"""
    import time

    import numpy as np
    import torch
    from sklearn.metrics import average_precision_score, roc_auc_score

    checkpoint_path = output_root / checkpoint_relative
    if checkpoint_sha256 != _sha256_file(checkpoint_path):
        raise RuntimeError(f"{branch_key} 选择检查点摘要与封印不符")
    if is_control:
        # 对位目标是**主口径骨干**的参数量，由 cells 阶段写入封印；这里只读不重算。
        model, _ = build_control_cell_model(config, seal["control_branch"]["parameter_match_target_total"])
    else:
        model = build_cell_model(config, branch_key, transform, input_key=seal["sealed_input_candidate"])
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"])
    model = model.to(device)
    selected_p = float(model.p.detach())

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    started = time.time()
    flow_scores, seen = score_target(config, model, transform, target, device, profile)
    evaluation_seconds = time.time() - started
    peak = torch.cuda.max_memory_allocated(device) / 2**20 if device.type == "cuda" else 0.0

    main_p = selected_p if uses_lp else None
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
        "dr_at_fpr": {
            f"fpr_{value:g}": dr_at_fpr(main_entity_scores, entity_labels, value) for value in DR_FPR_GRID
        },
        "maximum_dr_at_fpr": {
            f"fpr_{value:g}": dr_at_fpr(maximum_entity_scores, entity_labels, value) for value in DR_FPR_GRID
        },
        "flows_scored": int(seen.sum()),
        "entities_scored": int(valid_entity.sum()),
        "evaluation_seconds": evaluation_seconds,
        "target_evaluation_call": call_index,
    }
    curve = complete_budget_curve(main_entity_scores, entity_labels)
    cell_result = {
        "mechanisms": CELLS[CONTROL_CELL] if is_control else CELLS[branch_key],
        "is_control": is_control,
        "selection": (
            seal["control_branch"]["selection"] if is_control else seal["cells"][branch_key]
        ),
        "selected_p": selected_p,
        "target": metrics,
        "input_transform_receipt": transform.receipt(),
    }
    logger.info(
        "%s 目标评价（第 %d 次调用）：逐流AP=%.8f 实体AP=%.8f 计分流=%d 用时=%.1f 分",
        branch_key, call_index, metrics["flow_average_precision"],
        metrics["entity_average_precision"], metrics["flows_scored"], evaluation_seconds / 60.0,
    )
    del model, checkpoint, flow_scores, seen, main_entity_scores, maximum_entity_scores
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return cell_result, curve, peak


def run_evaluate_stage(config: dict[str, Any], args: argparse.Namespace) -> None:
    """阶段四：四格全部封印后加载 LSPR24，每格恰好评价一次，四格合计恰好 4 次。

    输入变换只应用已封印的训练区状态，绝不在 LSPR24 上重新拟合；目标年出现的词表外
    取值落既有越界桶，词表不扩充。评价阶段全程 ``torch.no_grad()``，不训练、不替换
    检查点、不搜索阈值、不更新聚合指数或任何超参数。

    整向量投影对照另有恰好 1 次评价，用**独立计数器**记录并单列在
    ``control_branch`` 下，绝不并入四格的 4 次。
    """
    output_root = Path(config["paths"]["output_root"])
    cache_root = Path(config["paths"]["cache_root"])
    selection_frozen_path = output_root / "selection_frozen.json"

    # 先做纯标准库的封印存在性核验，numpy/torch/sklearn 延后到确认要做真实评价之后
    # 才导入，使本阶段在缺依赖或尚未完成上游阶段的开发机上也能给出清晰的中文错误。
    if not selection_frozen_path.is_file():
        raise RuntimeError(
            f"四格选择尚未封印，禁止加载 LSPR24：{selection_frozen_path}；"
            "请先依次执行 --stage select-input、--stage select-optimizer 与 --stage cells"
        )
    seal = load_json(selection_frozen_path)
    if seal.get("all_four_cells_sealed") is not True or set(seal.get("cells", {})) != set(CELL_ORDER):
        raise RuntimeError("既有选择封印不完整，拒绝评价")
    if seal.get("target_year_arrays_read") != 0 or seal.get("target_evaluation_calls") != 0:
        raise RuntimeError("选择封印声明其间读取过目标年数组，最终测试隔离已被破坏，拒绝评价")

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

    write_status(output_root, "running", "evaluate", None, "选择封印后首次加载 LSPR24，每格评价一次")

    device = _resolve_device()
    transform = load_input_transform(output_root / "artifacts" / "sealed-input-transform.pkl")
    if transform.state_hash != seal["input_transform_receipt"]["state_hash"]:
        raise RuntimeError("已封印输入变换的 state_hash 与选择封印不符，拒绝评价")
    control_transform = load_input_transform(
        output_root / "artifacts" / "sealed-control-input-transform.pkl"
    )
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
    control_calls_this_process = 0
    control_receipts_reused = 0
    evaluation_started = time.time()
    evaluation_peak_gpu_mib = 0.0

    for cell in CELL_ORDER:
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
        cell_result, curve, peak = _score_one_branch(
            config, seal, cell, seal["cells"][cell]["checkpoint"]["filename"],
            seal["cells"][cell]["checkpoint"]["sha256"], CELLS[cell]["learned_lp_pooling"],
            transform, target, flow_entity, entity_labels, entity_count, device, profile,
            output_root, False, CELL_ORDER.index(cell) + 1,
        )
        evaluation_calls_this_process += 1
        evaluation_peak_gpu_mib = max(evaluation_peak_gpu_mib, peak)
        save_target_evaluation(output_root, cell, target_identity, cell_result, curve)
        cells[cell] = cell_result
        for field, values in curve.items():
            curve_arrays[f"{cell}__{field}"] = values

    total_calls = evaluation_calls_this_process + evaluation_receipts_reused
    if len(cells) != 4 or total_calls != 4 or target_load_count != 1:
        raise RuntimeError(
            f"目标年加载或四格评价次数不符：cells={len(cells)} calls={total_calls} loads={target_load_count}"
        )

    # 对照分支：独立计数、独立收据目录，指标单列，绝不并入上面的 4 次。
    control_seal = seal["control_branch"]
    control_identity = {
        **seal["identity"],
        "target_data_inventory_sha256": target_inventory["sha256"],
        "cell": CONTROL_KEY,
        "checkpoint_sha256": control_seal["selection"]["checkpoint"]["sha256"],
    }
    restored_control = load_target_evaluation(output_root, CONTROL_KEY, control_identity)
    if restored_control is not None:
        control_result, control_curve = restored_control
        control_receipts_reused += 1
        logger.info("对照分支复用身份与摘要匹配的目标评价完成收据")
    else:
        control_result, control_curve, control_peak = _score_one_branch(
            config, seal, CONTROL_KEY, control_seal["selection"]["checkpoint"]["filename"],
            control_seal["selection"]["checkpoint"]["sha256"], False, control_transform, target,
            flow_entity, entity_labels, entity_count, device, profile, output_root, True, 1,
        )
        control_calls_this_process += 1
        evaluation_peak_gpu_mib = max(evaluation_peak_gpu_mib, control_peak)
        save_target_evaluation(output_root, CONTROL_KEY, control_identity, control_result, control_curve)
    for field, values in control_curve.items():
        curve_arrays[f"{CONTROL_KEY}__{field}"] = values
    control_total_calls = control_calls_this_process + control_receipts_reused
    if control_total_calls != config["evaluation"]["control_target_evaluation_calls"]:
        raise RuntimeError(f"对照分支目标评价次数不符：{control_total_calls}")

    curve_path = output_root / "complete-alert-budget-curves.npz"
    temporary_curve = curve_path.with_name(f"{curve_path.name}.partial.{os.getpid()}")
    with temporary_curve.open("wb") as handle:
        np.savez_compressed(handle, **curve_arrays)
    os.replace(temporary_curve, curve_path)
    curve_receipt = {
        "schema_version": "ch3-ft-transformer-complete-alert-budget-curves-v1",
        "artifact": {
            "filename": curve_path.name,
            "bytes": curve_path.stat().st_size,
            "sha256": _sha256_file(curve_path),
        },
        "cells": list(CELL_ORDER),
        "control_branch": CONTROL_KEY,
        "fields": ["n_false_positive_entity", "nominal_fpr", "realized_fpr", "detection_rate"],
        "curve_is_complete_over_all_reachable_negative_entity_budgets": True,
        "per_flow_scores_persisted": False,
        "per_entity_scores_persisted": False,
    }
    _atomic_json(output_root / "complete-alert-budget-curves-receipt.json", curve_receipt)

    interaction: dict[str, Any] = {}
    for name in (
        "flow_average_precision", "flow_roc_auc", "entity_average_precision",
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

    training_seconds_sum = sum(float(seal["cells"][cell]["training_seconds"]) for cell in CELL_ORDER)
    evaluation_seconds_sum = sum(float(cells[cell]["target"]["evaluation_seconds"]) for cell in CELL_ORDER)
    launcher_resource = load_json(Path(args.resource_receipt)) if args.resource_receipt else None
    peak_candidates = [evaluation_peak_gpu_mib] + [
        float(seal["cells"][cell]["peak_gpu_allocated_mib"] or 0.0) for cell in CELL_ORDER
    ]
    architecture = config["architecture"]
    result = {
        "schema_version": "ch3-ft-transformer-field-token-protocol-a-results-v1",
        "run_id": RUN_ID,
        "model": {
            "model_key": MODEL_KEY,
            "display_name": config["display_name"],
            "n_layers": architecture["n_layers"],
            "d_token": architecture["d_token"],
            "n_heads": architecture["n_heads"],
            "d_ffn_factor": architecture["d_ffn_factor"],
            "d_ffn_hidden": architecture["d_ffn_hidden"],
            "sealed_input_candidate": seal["sealed_input_candidate"],
            "sealed_optimizer_candidate": seal["sealed_optimizer_candidate"],
            "input_dimension": seal["input_dimension"],
            "vocabulary_total_columns": seal["vocabulary_total_columns"],
            "token_count": seal["token_count"],
            "backbone_parameter_count": seal["backbone_parameter_count"],
            "mechanism_parameter_count": seal["mechanism_parameter_count"],
            "parameter_count": seal["parameter_count"],
            "per_cell_parameter_count": seal["per_cell_parameter_count"],
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
        "control_branch": {
            **{k: v for k, v in control_seal.items() if k != "selection"},
            "selection": control_seal["selection"],
            "target": control_result["target"],
            "reported_separately_from_four_cells": True,
            "identity_gate_note": CONTROL_IDENTITY_GATE_NOTE,
            "not_usable_to_refute_ft_transformer_family": True,
        },
        "isolation": {
            "all_four_selections_sealed_before_target_load": True,
            "target_disk_loads": target_load_count,
            "target_evaluation_calls": 4,
            "target_evaluation_calls_this_process": evaluation_calls_this_process,
            "target_evaluation_receipts_reused": evaluation_receipts_reused,
            "one_call_per_cell": True,
            "control_target_evaluation_calls": control_total_calls,
            "control_calls_counted_separately": True,
            "input_transform_applied_only_never_refitted_on_target": True,
        },
        "artifact_policy": {
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "selected_checkpoints_persisted": len(CELL_ORDER) + 1,
            "complete_alert_budget_curve": curve_receipt,
        },
        "resource": {
            "parameter_count": seal["parameter_count"],
            "training_wall_seconds_sum": training_seconds_sum,
            "evaluation_wall_seconds_sum": evaluation_seconds_sum,
            "target_stage_wall_seconds": time.time() - evaluation_started,
            "peak_gpu_allocated_mib": max(peak_candidates),
            "peak_process_rss_mib": _process_peak_rss_mib(),
            "gpu_hours": (training_seconds_sum + evaluation_seconds_sum) / 3600.0,
            "control_training_wall_seconds": float(control_seal["selection"]["training_seconds"]),
            "control_evaluation_wall_seconds": float(control_result["target"]["evaluation_seconds"]),
            "launcher_admission_receipt": launcher_resource,
        },
    }
    _atomic_json(aggregate_path, result)
    write_status(output_root, "computed", "evaluate", 0, "四格与对照的目标评价完成，等待 SwanLab 上报")
    build_manifest(output_root, RUN_ID)
    publish_swanlab(config, result, output_root)
    write_status(output_root, "complete", "evaluate", 0, "四格结果、对照结果、聚合指标与 SwanLab 上报均已完成")
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
        # 四个阶段均已接通，生产路径不再有未实现出口；这里保留统一的失败出口，
        # 保留脱敏堆栈与非零退出码，供启动器按原退出码判定。
        logger.exception("阶段执行失败：%s", args.stage)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
