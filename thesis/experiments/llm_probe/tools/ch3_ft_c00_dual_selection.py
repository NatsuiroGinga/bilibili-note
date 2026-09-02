#!/usr/bin/env python3
"""裸 FT C00 的跨设备双选轮训练与真实运行校准。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import logging
import math
import os
import platform
import random
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any


TOOL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_DIR.parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch3_ft_transformer_field_token_protocol_a as base

# 执行路径观测层。该模块顶层只导入标准库（torch 与 torch._dynamo 全部延迟到函数内），
# 因此可以无条件在此导入，不破坏 --validate-config 在缺 numpy/torch 的 .venv 上跑通的既有约束。
import ch3_ft_execution_path_receipt as execution_path

# ch3_ft_entity_memory_interface 在其模块顶层无条件 import numpy，本文件的
# --validate-config 路径必须在缺 numpy/torch 的 .venv 上也能跑通（既有约束，
# 2026-08-28 实测确认：项目 .venv 缺 numpy 与 torch），因此这里不在模块顶层
# import 它，只在真正需要机制一接口的函数内部延迟导入。


SCHEMA_VERSION = "ch3-ft-c00-dual-selection-config-v1"
CHECKPOINT_SCHEMA_VERSION = "ch3-ft-candidate-unified-checkpoint-v2"
SOURCE_ARRAYS = ("X23", "y23", "I23", "M23", "E23", "T23")
EXIT_CONFIG = 2
EXIT_INPUT = 3
EXIT_RUNTIME = 4
LOGGER = logging.getLogger("ch3_ft_c00_dual_selection")

# 裸 FT 骨干可训练参数量，两处校验（配置合同、模型实测）共用同一常量，避免字面量漂移。
BARE_FT_PARAMETER_COUNT = 924283

# ---------------------------------------------------------------------------
# 模型宽度档位（缩容代理模型实验用，2026-09-02 新增）。
#
# **不改 tools/ch3_ft_transformer_field_token_protocol_a.py**：该文件被 21 份配置以
# base.tool_sha256 逐字节哈希锁定（本机 2026-09-02 实测：除一份引用另一工具的配置外，
# 全部 20 份现有 ch3-ft-*.json 的 base.tool_sha256 都等于该文件当前哈希
# 1c8c0cd1ac162149363d13bbda6ca8ec9588424ec494a4c7861d7ce6c347e91b）；任何字节级改动都会
# 让 validate_config 第 507 行的「基础 FT 工具摘要漂移」门在全部既有配置上失败，而不只是
# 本任务关心的 C00/C01/C11 三份 v2。tools/ch3_ft_c00_dual_selection.py 本身不被任何配置
# 哈希锁定，故宽度档位逻辑全部落在本文件，只通过 base.expected_parameter_count（已支持
# 任意 d_token 关键字参数）与 base.build_model（已从 config["architecture"]["d_token"]
# 读取，不依赖模块级常量）复用协议 A 现成闭式，不新写公式。
# ---------------------------------------------------------------------------
WIDTH_PROFILE_FULL = "full"
WIDTH_PROFILE_HALF = "half"
WIDTH_PROFILES: tuple[str, ...] = (WIDTH_PROFILE_FULL, WIDTH_PROFILE_HALF)
# half 档 d_token：官方默认配方宽度对半，n_heads=8 仍整除（96/8=12），层数与头数不变。
HALF_WIDTH_D_TOKEN = base.D_TOKEN // 2
# 裸 FT 骨干词表总列数（Protocol + L3/L4 Protocol 两个词表字段，训练区基数各加一个越界
# 桶后的列数之和）。本机 2026-09-02 反解验证：
# base.expected_parameter_count(base.NUMERIC_TOKEN_FIELD_COUNT,
# base.VOCABULARY_TOKEN_FIELD_COUNT, 14, d_token=192) == 924283 == BARE_FT_PARAMETER_COUNT，
# 故取 14 为该列数，供 half 档复用同一闭式重算，不手填 half 档参数量。
BARE_FT_VOCABULARY_TOTAL_COLUMNS = 14


def bare_ft_expected_parameter_count(width_profile: str) -> int:
    """裸 FT 骨干在给定宽度档位下的期望可训练参数量。

    ``full`` 档直接返回既有冻结常量 ``BARE_FT_PARAMETER_COUNT``（不改变现状行为）；
    ``half`` 档复用 ``base.expected_parameter_count`` 同一闭式，只把 ``d_token`` 换成
    ``HALF_WIDTH_D_TOKEN``，不新写公式、不手填数字。
    """
    if width_profile == WIDTH_PROFILE_FULL:
        return BARE_FT_PARAMETER_COUNT
    if width_profile == WIDTH_PROFILE_HALF:
        return base.expected_parameter_count(
            base.NUMERIC_TOKEN_FIELD_COUNT,
            base.VOCABULARY_TOKEN_FIELD_COUNT,
            BARE_FT_VOCABULARY_TOTAL_COLUMNS,
            d_token=HALF_WIDTH_D_TOKEN,
        )
    raise ValueError(f"未知 model.width_profile：{width_profile}")

# mechanism 键在既有两份 C00 配置（cuda-formal / mps-screening）中不存在；缺省即
# 机制一、机制二均关闭，行为与这两份配置历史上的语义完全一致，因此不需要改动它们。
# entity_ranking 与 entity_memory 对称新增，机制二实现报告见
# .Codex/docs/RWKV/2026-08-28-机制二实现报告.md。
#
# **本字典不得再增键**（2026-08-31 实测确认）：``science_projection`` 对缺 mechanism 键的
# 配置回落到本字典，故给它加任何键都会改变这类配置的 science_identity_sha256。实测：
# 两份 C00 配置的科学身份现为 08dd9f1899972d1d…，加一个 entity_gated_ple 键后变成
# eb1d2370111dae47…，而 C10/C01/C11 因自带 mechanism 键不受影响。身份漂移会让既有
# C00 在途检查点在 ``run_training`` 的 ``require(checkpoint["science_identity"] == …)``
# 处被拒绝续训。因此 M-E（z1 = entity_gated_ple）改用
# ``mechanism.get("entity_gated_ple", {})`` 就地缺省，不进本字典。
DEFAULT_MECHANISM: dict[str, Any] = {
    "entity_memory": {"enabled": False, "slots": None},
    "entity_ranking": {
        "enabled": False,
        "budgets": None,
        "bag_policy": None,
        "n_pos": None,
        "n_neg": None,
        "truncate_length": None,
        "num_length_buckets": None,
        "xi_learning_rate": None,
    },
}

# 机制二袋处置策略枚举，与 ch3_ft_entity_ranking_loss.BagPolicyConfig 的
# _VALID_POLICIES 逐字一致；这里独立重复一份纯字符串常量，使
# --validate-config 路径不必导入 torch（该模块顶层无条件 import torch）。
ENTITY_RANKING_BAG_POLICIES = ("full", "causal_prefix_truncation", "stratified_weighting")

# 任务 1 接口约定的角色编码（与 ch3_ft_entity_memory_interface.load_role_ids 逐字一致）：
# 0＝训练实体，1＝验证实体；本任务只读 LSPR23，不存在第三档目标年角色。
ENTITY_MEMORY_ROLE_TRAIN = 0
ENTITY_MEMORY_ROLE_VALIDATION = 1

# ---------------------------------------------------------------------------
# M-E（实体门控的分段线性数值分词）的纯字符串与纯算术常量。
# 与 ch3_ft_entity_gated_ple.py 逐字一致的部分在此独立重复一份，理由与
# entity_memory_parameter_count 相同：--validate-config 路径必须能在缺 numpy/torch 的
# 项目 .venv 上跑通，而 ch3_ft_entity_gated_ple 模块顶层无条件 import torch。
# ---------------------------------------------------------------------------

# 门模式枚举，与 ch3_ft_entity_gated_ple.GATE_MODES 逐字一致。
ENTITY_GATED_PLE_GATE_MODES = ("entity_state", "constant", "binary_indicator")

# 三个门模式各自的候选身份键。三臂共用同一份机制实现、同一份预算，只有门不同，
# 因此身份键必须逐臂区分，否则完整 M-E 与两个消融臂会落在同一个科学身份上。
ENTITY_GATED_PLE_CANDIDATE_KEYS: dict[str, str] = {
    "entity_state": "entity-gated-ple-c10",
    "constant": "constant-gate-ple-e1",
    "binary_indicator": "binary-gate-ple-e2",
}

# 科学合同版本：M-E 三臂用自己的版本号，既有四格（C00/C01/C10/C11）不受影响。
SCIENCE_CONTRACT_DUAL_SELECTION = "ch3-ft-c00-dual-selection-science-v1"
SCIENCE_CONTRACT_ENTITY_GATED_PLE = "ch3-ft-entity-gated-ple-science-v1"

# ---------------------------------------------------------------------------
# 机制一第二候选：实体内尾部聚合（经验 CVaR_α 的 ATk 形式）的纯字符串与纯校验常量。
# 算术实现只有一份，在 ch3_ft_entity_ranking_loss.tail_aggregate；这里同样只放
# 不依赖 torch/numpy 的常量与校验，使 --validate-config 能在缺 numpy/torch 的
# 项目 .venv 上跑通（既有约束，理由与 entity_gated_ple 那一组常量相同）。
#
# 参数裁决：`.Codex/docs/RWKV/2026-09-01-尾部聚合参数裁决/裁决报告.md`。
# α = 0.5 由两条结构约束唯一确定，已随该报告冻结，**不得按任何实验读数回调**。
# ---------------------------------------------------------------------------

# 聚合算子枚举。当前只有一种；路径 C（LSE 软聚合）是预注册退路，未实现，
# 因此不在这里预留键——真要启用时按裁决报告第四节补登记 τ0 的尺度诊断依据。
ENTITY_TAIL_AGGREGATION_KINDS = ("atk_tail_mean",)

# 冻结的尾部水平。写成常量而不是只放在配置里，是为了让「配置写了别的值」这件事
# 可被机械发现：validate_config 断言配置值等于本常量。
ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA = 0.5

# 魔法数字登记表的必填字段，逐条对应根 AGENTS.md 的门禁项与裁决报告第三节。
ENTITY_TAIL_AGGREGATION_PROVENANCE_KEYS = (
    "purpose_and_value",
    "literature",
    "derivation",
    "real_data_diagnostic",
    "scope",
    "touches_target_labels",
    "verification_status",
)

# 配置块允许出现的键，白名单式校验。**不含任何截断长度键**：排序袋的 8192 上限
# 只能来自 mechanism.entity_ranking.truncate_length，另立一个就会出现两个可以
# 不一致的袋合同（裁决报告第五节第 4 条「沿用截断 8192」）。
ENTITY_TAIL_AGGREGATION_ALLOWED_KEYS = ("enabled", "kind", "alpha", "numeric_provenance")

# 评价侧实体聚合口径字符串。z1'=0 保持历史值不变，z1'=1 换成尾部聚合口径——
# 该字段进 science_projection，因此两臂的科学身份天然不同，不会撞车。
ENTITY_AGGREGATION_MAXIMUM = "maximum_over_validation_flows"
ENTITY_AGGREGATION_TAIL_MEAN = "entity_tail_mean_over_validation_flows"

# 候选身份键：尾部聚合 z1' 与 BER z2 组成新的一组四格，键必须与 CEM 那组区分，
# 否则两代机制一的运行会落在同一个科学身份上。
ENTITY_TAIL_AGGREGATION_CANDIDATE_KEYS: dict[bool, str] = {
    False: "entity-tail-aggregation-c10-dual-selection",
    True: "entity-tail-aggregation-ber-c11-dual-selection",
}
SCIENCE_CONTRACT_ENTITY_TAIL_AGGREGATION = "ch3-ft-entity-tail-aggregation-science-v1"

# 箱边界拟合的分块行数：与 base._gather_training_column 的分块读法同量级，
# 每块显式分配上界为 chunk × 83 × 4B（原值）加 chunk × F × 4B（变换后），
# 取 131,072 时约 43 MB + 42 MB，与冻结基数收据的 chunk_rows 同一量级。
ENTITY_GATED_PLE_FIT_CHUNK_ROWS = 131_072


def entity_gated_ple_parameter_count(
    numeric_field_count: int, bin_count: int, d_token: int, gate_hidden: int, gate_mode: str
) -> int:
    """M-E 专属参数量闭式，与 ``ch3_ft_entity_gated_ple.entity_gated_ple_parameter_count``
    逐字一致的纯算术副本。

    位移嵌入 ``F·T·d``；``entity_state`` 门是 ``Linear(2,h)`` 加 ``Linear(h,1)``，
    参数 ``4h + 1``；``constant`` 与 ``binary_indicator`` 门是单个可学标量，参数 ``1``。
    ``build_model_optimizer`` 在真正构造模型时交叉核验两处实现一致，防止静默漂移。
    """
    if gate_mode not in ENTITY_GATED_PLE_GATE_MODES:
        raise ValueError(f"未知门模式：{gate_mode}")
    displacement = numeric_field_count * bin_count * d_token
    gate = (4 * gate_hidden + 1) if gate_mode == "entity_state" else 1
    return displacement + gate


def entity_memory_parameter_count(width: int, slots: int) -> int:
    """机制一交叉注意力参数量闭式，与 ``ch3_ft_causal_entity_memory.

    causal_entity_memory_parameter_count`` 逐字一致——此处独立重复一份纯算术实现，
    使 ``--validate-config`` 路径不必导入 torch（该模块顶层无条件 ``import torch``）。
    ``build_model_optimizer`` 在真正构造模型时会交叉核验两处实现一致，防止静默漂移。
    """
    projections = 4 * (width * width + width)
    gate = 2 * width + 1
    norms = 2 * (2 * width)
    role_embedding = slots * width
    return projections + gate + norms + role_embedding


class ExperimentError(RuntimeError):
    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def require(condition: bool, message: str, exit_code: int = EXIT_CONFIG) -> None:
    if not condition:
        raise ExperimentError(message, exit_code)


def sha256_file(path: Path, block_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExperimentError(f"JSON 读取失败：{path}：{error}", EXIT_CONFIG) from error


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def atomic_torch(path: Path, value: Any, torch_module: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    torch_module.save(value, temporary)
    os.replace(temporary, path)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def validate_config(config: dict[str, Any]) -> None:
    require(config.get("schema_version") == SCHEMA_VERSION, "配置模式版本不符")
    identity = config.get("identity", {})
    # mechanism 键缺失（既有两份 C00 配置）即机制一关闭，语义与历史行为完全一致；
    # 提前解析出 entity_memory_enabled，供候选身份与模型合同两处共用同一判定。
    mechanism = config.get("mechanism", DEFAULT_MECHANISM)
    entity_memory = mechanism.get("entity_memory", {})
    entity_memory_enabled = entity_memory.get("enabled", False)
    require(isinstance(entity_memory_enabled, bool), "mechanism.entity_memory.enabled 必须是布尔值")
    # 对称新增：entity_ranking 缺省即机制二关闭，与 entity_memory 的缺省语义一致。
    entity_ranking = mechanism.get("entity_ranking", {})
    entity_ranking_enabled = entity_ranking.get("enabled", False)
    require(isinstance(entity_ranking_enabled, bool), "mechanism.entity_ranking.enabled 必须是布尔值")
    # M-E 就地缺省读取，不进 DEFAULT_MECHANISM（理由见该字典上方注释）。
    entity_gated_ple = mechanism.get("entity_gated_ple", {})
    entity_gated_ple_enabled = entity_gated_ple.get("enabled", False)
    require(isinstance(entity_gated_ple_enabled, bool), "mechanism.entity_gated_ple.enabled 必须是布尔值")
    # 实体内尾部聚合同样就地缺省读取，不进 DEFAULT_MECHANISM（理由见该字典上方注释：
    # 给它加键会改变缺 mechanism 键的 C00 配置的科学身份，拒掉既有在途检查点）。
    entity_tail_aggregation = mechanism.get("entity_aggregation", {})
    entity_tail_aggregation_enabled = entity_tail_aggregation.get("enabled", False)
    require(
        isinstance(entity_tail_aggregation_enabled, bool),
        "mechanism.entity_aggregation.enabled 必须是布尔值",
    )
    if entity_tail_aggregation_enabled:
        unknown = set(entity_tail_aggregation) - set(ENTITY_TAIL_AGGREGATION_ALLOWED_KEYS)
        require(
            not unknown,
            f"mechanism.entity_aggregation 含未登记键 {sorted(unknown)}；"
            "特别是不得另立截断长度键，排序袋上限只能来自 entity_ranking.truncate_length",
        )
        require(
            entity_tail_aggregation.get("kind") in ENTITY_TAIL_AGGREGATION_KINDS,
            "mechanism.entity_aggregation.kind 取值不合法",
        )
        alpha = entity_tail_aggregation.get("alpha")
        require(
            isinstance(alpha, float) and alpha == ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA,
            f"mechanism.entity_aggregation.alpha 必须是已冻结的 {ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA}"
            "（2026-09-01 尾部聚合参数裁决报告，两条结构约束唯一确定，不得按实验读数回调）",
        )
        provenance = entity_tail_aggregation.get("numeric_provenance")
        require(isinstance(provenance, dict), "mechanism.entity_aggregation.numeric_provenance 必须是对象")
        for key in ENTITY_TAIL_AGGREGATION_PROVENANCE_KEYS:
            value = provenance.get(key)
            require(
                (isinstance(value, str) and value.strip()) or isinstance(value, bool),
                f"numeric_provenance.{key} 缺失或为空——魔法数字门禁要求逐项登记",
            )
        require(
            provenance.get("touches_target_labels") is False,
            "numeric_provenance.touches_target_labels 必须为 false（α 的推导零接触 LSPR24 与 y23）",
        )
        # 三个机制一候选改的是同一个位置（实体分数），同开会得到一个从未设计过的
        # 模型，其读数无法解释。与 M-E 的互斥断言同型。
        require(
            not entity_memory_enabled and not entity_gated_ple_enabled,
            "尾部聚合臂必须 entity_memory=false 且 entity_gated_ple=false"
            "（三者都是机制一候选，改的是同一处实体分数）",
        )
    if entity_gated_ple_enabled:
        # M-E 改的是分词器本身，与机制一的交叉注意力、机制二的第二数据流互不兼容；
        # 三者同开会得到一个从未设计过的模型，其读数无法解释。
        require(
            not entity_memory_enabled and not entity_ranking_enabled,
            "M-E 臂必须 z1(entity_memory)=false 且 z2(entity_ranking)=false",
        )
        gate_mode = entity_gated_ple.get("gate_mode")
        require(gate_mode in ENTITY_GATED_PLE_GATE_MODES, "mechanism.entity_gated_ple.gate_mode 取值不合法")
        bin_count = entity_gated_ple.get("bin_count")
        require(
            isinstance(bin_count, int) and not isinstance(bin_count, bool) and bin_count >= 1,
            "mechanism.entity_gated_ple.bin_count(T) 必须是 ≥1 的整数",
        )
        gate_hidden = entity_gated_ple.get("gate_hidden")
        require(
            isinstance(gate_hidden, int) and not isinstance(gate_hidden, bool) and gate_hidden >= 1,
            "mechanism.entity_gated_ple.gate_hidden(h) 必须是 ≥1 的整数",
        )
        for key in ("c_scale_quantile", "gap_scale_quantile"):
            value = entity_gated_ple.get(key)
            require(
                isinstance(value, float) and 0.0 < value < 1.0,
                f"mechanism.entity_gated_ple.{key} 必须是 (0,1) 内的小数",
            )
        sample_cap = entity_gated_ple.get("bin_fit_sample_cap")
        require(
            isinstance(sample_cap, int) and not isinstance(sample_cap, bool) and sample_cap > 0,
            "mechanism.entity_gated_ple.bin_fit_sample_cap 必须是正整数",
        )
        expected_candidate_key = ENTITY_GATED_PLE_CANDIDATE_KEYS[gate_mode]
        expected_science_contract = SCIENCE_CONTRACT_ENTITY_GATED_PLE
    elif entity_tail_aggregation_enabled:
        expected_candidate_key = ENTITY_TAIL_AGGREGATION_CANDIDATE_KEYS[bool(entity_ranking_enabled)]
        expected_science_contract = SCIENCE_CONTRACT_ENTITY_TAIL_AGGREGATION
    else:
        expected_candidate_key = {
            (False, False): "bare-ft-c00-dual-selection",
            (True, False): "causal-entity-memory-c10-dual-selection",
            (False, True): "budget-aware-entity-ranking-c01-dual-selection",
            (True, True): "cem-ber-c11-dual-selection",
        }[(entity_memory_enabled, entity_ranking_enabled)]
        expected_science_contract = SCIENCE_CONTRACT_DUAL_SELECTION
    require(identity.get("candidate_key") == expected_candidate_key, "候选身份不符")
    require(identity.get("science_contract_version") == expected_science_contract, "科学合同版本不符")
    require(identity.get("run_tier") in {"screening_only", "formal"}, "运行级别不符")
    run_id = identity.get("run_id")
    require(isinstance(run_id, str) and run_id, "运行身份缺失")
    require(Path(config["paths"]["output_root"]).name == run_id, "输出根末级与运行身份不符")

    runtime = config.get("runtime", {})
    expected_profile = {
        "mps": "mps-fp32-v1",
        "cuda": "cuda-bf16-amp-fp32-sensitive-v1",
    }
    device_type = runtime.get("device_type")
    require(device_type in expected_profile, "设备类型只能是 mps 或 cuda")
    require(runtime.get("precision_profile_id") == expected_profile[device_type], "设备与精度 profile 不匹配")
    require(runtime.get("allow_device_fallback") is False, "禁止设备回退")
    require(runtime.get("allow_cpu_op_fallback") is False, "禁止算子回退 CPU")
    if identity["run_tier"] == "screening_only":
        # 2026-08-31 放宽：原断言为 device_type == "mps"，把「筛选」等同于「本机 MPS」。
        # 该等同是早期假设而非必然——根 AGENTS.md 规定 screening_only「可自选微批量、
        # 精度、容量、训练与评估预算和资源」，未限定设备；而本机 MPS 跑不动
        # 20 轮 × 1000 步的机制筛选臂，该门会拦下本可正常进行的实验。
        # 筛选与正式的隔离由下面两条保证，不依赖设备类型：
        # run_tier 字段本身，以及 formal_resume_eligible 必须为 False。
        # 实际设备写入运行收据，跨设备结果不得互相比较。
        require(device_type in {"mps", "cuda"}, "筛选运行的设备只能是 mps 或 cuda")
        require(config["checkpoint"]["formal_resume_eligible"] is False, "筛选检查点不得正式续训")
    else:
        require(device_type == "cuda", "正式运行必须使用 CUDA")
        require(config["checkpoint"]["formal_resume_eligible"] is True, "CUDA 正式检查点须允许同身份恢复")

    require(config.get("data", {}).get("source_arrays") == list(SOURCE_ARRAYS), "源年数组白名单不符")
    require(config["data"].get("target_reads") == 0, "目标读取必须为零")
    require(config["data"].get("input_candidate") == "ft-transformer-input-protocol-vocabulary-token", "输入候选不符")

    if entity_memory_enabled:
        slots = entity_memory.get("slots")
        require(
            isinstance(slots, int) and not isinstance(slots, bool) and slots >= 2,
            "z1=1 时 mechanism.entity_memory.slots(R) 必须是 ≥2 的整数",
        )
        require(config.get("model") == {
            "role": "causal_entity_memory_ft_transformer",
            "expected_parameter_count": BARE_FT_PARAMETER_COUNT + entity_memory_parameter_count(base.D_TOKEN, slots),
            "entity_memory_slots": slots,
            "old_cpa_enabled": False,
            "old_elp_enabled": False,
            "old_mechanism_scaffold_present": False,
        }, "机制一 FT 模型合同不符")
    elif entity_gated_ple_enabled:
        # 数值字段数取骨干冻结常量：M-E 的位移嵌入按 F×T×d 计，F 与骨干分词器同源。
        # build_model_optimizer 会用 view.transform.numeric_field_count 交叉核验实测值。
        own = entity_gated_ple_parameter_count(
            base.NUMERIC_TOKEN_FIELD_COUNT,
            entity_gated_ple["bin_count"],
            base.D_TOKEN,
            entity_gated_ple["gate_hidden"],
            entity_gated_ple["gate_mode"],
        )
        require(config.get("model") == {
            "role": "entity_gated_ple_ft_transformer",
            "expected_parameter_count": BARE_FT_PARAMETER_COUNT + own,
            "entity_gated_ple_bin_count": entity_gated_ple["bin_count"],
            "entity_gated_ple_gate_hidden": entity_gated_ple["gate_hidden"],
            "entity_gated_ple_gate_mode": entity_gated_ple["gate_mode"],
            "old_cpa_enabled": False,
            "old_elp_enabled": False,
            "old_mechanism_scaffold_present": False,
        }, "M-E FT 模型合同不符")
    else:
        slots = entity_memory.get("slots")
        require(slots is None or isinstance(slots, int), "z1=0 时 slots 只能是 null 或整数（不参与模型构造）")
        # width_profile 是可选字段，缺省即 full；缺省时期望字典完全不含该键，与改动前
        # 逐位一致，保证既有配置（无该字段）的 science_identity_sha256 不变。
        model_block = config.get("model")
        has_width_profile = isinstance(model_block, dict) and "width_profile" in model_block
        width_profile = model_block.get("width_profile", WIDTH_PROFILE_FULL) if isinstance(model_block, dict) else WIDTH_PROFILE_FULL
        require(width_profile in WIDTH_PROFILES, f"model.width_profile 只能是 {WIDTH_PROFILES} 之一")
        expected_model: dict[str, Any] = {
            "role": "bare_ft_transformer",
            "expected_parameter_count": bare_ft_expected_parameter_count(width_profile),
            "old_cpa_enabled": False,
            "old_elp_enabled": False,
            "old_mechanism_scaffold_present": False,
        }
        if has_width_profile:
            expected_model["width_profile"] = width_profile
        require(config.get("model") == expected_model, "裸 FT 模型合同不符")

    if entity_ranking_enabled:
        budgets = entity_ranking.get("budgets")
        require(
            isinstance(budgets, list) and len(budgets) > 0
            and all(isinstance(k, int) and not isinstance(k, bool) and k > 0 for k in budgets),
            "z2=1 时 mechanism.entity_ranking.budgets 必须是非空正整数列表",
        )
        require(entity_ranking.get("bag_policy") in ENTITY_RANKING_BAG_POLICIES, "mechanism.entity_ranking.bag_policy 取值不合法")
        n_pos = entity_ranking.get("n_pos")
        n_neg = entity_ranking.get("n_neg")
        require(isinstance(n_pos, int) and not isinstance(n_pos, bool) and n_pos >= 1, "n_pos 必须是 ≥1 的整数")
        require(isinstance(n_neg, int) and not isinstance(n_neg, bool) and n_neg >= 1, "n_neg 必须是 ≥1 的整数")
        truncate_length = entity_ranking.get("truncate_length")
        require(
            isinstance(truncate_length, int) and not isinstance(truncate_length, bool) and truncate_length > 0,
            "truncate_length 必须是正整数",
        )
        num_length_buckets = entity_ranking.get("num_length_buckets")
        require(
            isinstance(num_length_buckets, int) and not isinstance(num_length_buckets, bool) and num_length_buckets >= 1,
            "num_length_buckets 必须是 ≥1 的整数",
        )
        # xi_learning_rate 2026-08-31 曾短暂改为不驱动训练（xi 改由跨步水库直接取
        # 分位数）；该修法已于 2026-09-01 被预注册判据否决并回退（见
        # .Codex/docs/RWKV/2026-09-01-BER水库分位数修法裁决.md 的「回退实施」节）。
        # xi_learning_rate 现重新驱动训练：_ranking_phase 用它对 get()/commit() 取出
        # 的叶张量做子梯度 SGD 更新，与本字段引入时（2026-08-30 之前）的语义一致。
        xi_learning_rate = entity_ranking.get("xi_learning_rate")
        require(
            isinstance(xi_learning_rate, (int, float)) and not isinstance(xi_learning_rate, bool) and xi_learning_rate > 0,
            "xi_learning_rate 必须是正数",
        )
        reservoir_size = entity_ranking.get("reservoir_size", 4096)
        require(
            isinstance(reservoir_size, int) and not isinstance(reservoir_size, bool) and reservoir_size > 0,
            "reservoir_size 必须是正整数",
        )
    require(config.get("optimizer", {}).get("candidate_key") == "ft-transformer-official-default", "优化器候选不符")

    training = config.get("training", {})
    require(training.get("seed") == 42, "随机种子不符")
    require(training.get("effective_batch_size") == 64, "有效批必须是 64 个序列")
    micro = training.get("micro_batch_sequences")
    accumulation = training.get("gradient_accumulation_steps")
    require(isinstance(micro, int) and micro > 0 and isinstance(accumulation, int) and accumulation > 0, "微批或累积步数无效")
    require(micro * accumulation == training["effective_batch_size"], "微批乘累积步数不等于有效批")
    require(training.get("sequence_length") == 128, "序列长度不符")
    require(training.get("normalization_unit") == "valid_flow", "损失归一化单位不符")
    require(training.get("selection_metrics") == ["validation_flow_ap", "validation_entity_ap"], "双选轮指标不符")
    require(training.get("tie_rule") == "strict_argmax_earliest", "打平规则不符")
    validation_batch = training.get("validation_batch_sequences")
    require(isinstance(validation_batch, int) and validation_batch > 0, "验证序列批量无效")

    budget = config.get("budget", {})
    require(budget.get("state") in {"unmeasured", "frozen"}, "预算状态不符")
    require(budget.get("probe_optimizer_steps") == 1, "校准必须执行一个完整优化步")
    if budget["state"] == "unmeasured":
        require(budget.get("epochs") == 0 and budget.get("steps_per_epoch") == 0, "未测预算禁止填写训练轮数或步数")
    else:
        require(isinstance(budget.get("epochs"), int) and budget["epochs"] > 0, "冻结轮数无效")
        require(isinstance(budget.get("steps_per_epoch"), int) and budget["steps_per_epoch"] > 0, "冻结步数无效")

    checkpoint = config.get("checkpoint", {})
    require(checkpoint.get("schema_version") == CHECKPOINT_SCHEMA_VERSION, "检查点模式不符")
    require(checkpoint.get("cross_profile_resume_allowed") is False, "禁止跨 profile 恢复")
    # 评价侧聚合口径必须与机制开关一致：z1'=0 保持历史值，z1'=1 换成尾部聚合口径。
    # 两个方向都断言，防止「开了机制却仍按 max 评价」或「没开机制却写了尾部口径」。
    expected_entity_aggregation = (
        ENTITY_AGGREGATION_TAIL_MEAN if entity_tail_aggregation_enabled else ENTITY_AGGREGATION_MAXIMUM
    )
    require(
        config.get("evaluation", {}).get("entity_aggregation") == expected_entity_aggregation,
        f"实体聚合口径不符：机制开关要求 {expected_entity_aggregation}",
    )
    require(config["evaluation"].get("target_reads") == 0, "评价目标读取必须为零")

    base_config_path = resolve_project_path(config["base"]["config_path"])
    base_tool_path = resolve_project_path(config["base"]["tool_path"])
    require(base_config_path.is_file() and base_tool_path.is_file(), "基础 FT 配置或工具不存在")
    require(sha256_file(base_config_path) == config["base"]["config_sha256"], "基础 FT 配置摘要漂移")
    require(sha256_file(base_tool_path) == config["base"]["tool_sha256"], "基础 FT 工具摘要漂移")


def science_projection(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "science_contract_version": config["identity"]["science_contract_version"],
        "candidate_key": config["identity"]["candidate_key"],
        "base": config["base"],
        "data": {
            "source_arrays": config["data"]["source_arrays"],
            "target_reads": 0,
            "input_candidate": config["data"]["input_candidate"],
            "split": "protocol_a_entity_disjoint_with_time_tail_exclusion",
            "positive_weight_source": "training_effective_flows_only",
        },
        "model": config["model"],
        "mechanism": config.get("mechanism", DEFAULT_MECHANISM),
        "optimizer": config["optimizer"],
        "training": {
            "seed": config["training"]["seed"],
            "effective_batch_size": config["training"]["effective_batch_size"],
            "sequence_length": config["training"]["sequence_length"],
            "normalization_unit": config["training"]["normalization_unit"],
            "selection_metrics": config["training"]["selection_metrics"],
            "tie_rule": config["training"]["tie_rule"],
        },
        "checkpoint_schema": config["checkpoint"]["schema_version"],
        "evaluation": config["evaluation"],
    }


def runtime_projection(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": config["identity"]["run_id"],
        "run_tier": config["identity"]["run_tier"],
        "runtime": config["runtime"],
        "paths": config["paths"],
        "micro_batch_sequences": config["training"]["micro_batch_sequences"],
        "gradient_accumulation_steps": config["training"]["gradient_accumulation_steps"],
        "validation_batch_sequences": config["training"]["validation_batch_sequences"],
        "budget": config["budget"],
        "resource": config["resource"],
        "tracking": config["tracking"],
    }


def effective_base_config(config: dict[str, Any]) -> dict[str, Any]:
    base_config = load_json(resolve_project_path(config["base"]["config_path"]))
    base.validate_config(base_config)
    result = copy.deepcopy(base_config)
    result["paths"]["cache_root"] = config["paths"]["cache_root"]
    result["paths"]["field_cardinality_receipt"] = config["paths"]["cardinality_receipt"]
    result["training"]["seed"] = config["training"]["seed"]
    result["training"]["sequence_length"] = config["training"]["sequence_length"]
    result["training"]["effective_batch_size"] = config["training"]["effective_batch_size"]
    result["training"]["micro_batch_sequences"] = config["training"]["micro_batch_sequences"]
    result["training"]["gradient_accumulation_steps"] = config["training"]["gradient_accumulation_steps"]
    result["training"]["epochs"] = max(1, int(config["budget"]["epochs"] or 1))
    result["training"]["steps_per_epoch"] = max(1, int(config["budget"]["steps_per_epoch"] or 1))
    return result


def resolve_runtime(config: dict[str, Any]) -> tuple[Any, Any, dict[str, Any], Any]:
    import torch

    # float32 矩阵乘精度：恢复卡第 38 行把它列为「未冻结候选」，要求第一格启动前裁决并冻结。
    # 2026-09-01 裁决为**不启用**（取 "highest"，即不走 TF32 类快速路径）。理由：它会改变
    # 舍入与训练轨迹，而启用需要额外的构造等价性检查与吞吐实测；在四格已统一即时执行的
    # 前提下，保守取值与该方向一致。此处**显式设置**而非依赖 PyTorch 默认，因为默认值可能
    # 随版本变化，显式调用才能保证四格跨时间、跨机器取到同一条数值路径。
    # 实际生效值由执行路径收据的 float32_matmul_precision 字段记录。
    matmul_precision = config["runtime"].get("float32_matmul_precision", "highest")
    require(
        matmul_precision in ("highest", "high", "medium"),
        f"未知的 float32 矩阵乘精度：{matmul_precision}",
        EXIT_INPUT,
    )
    torch.set_float32_matmul_precision(matmul_precision)

    precision = base._precision_module()
    contract = precision.load_and_validate_contract(resolve_project_path(config["paths"]["precision_contract"]))
    device_type = config["runtime"]["device_type"]
    profile_id = config["runtime"]["precision_profile_id"]
    profile = precision.validate_runtime_profile(contract, profile_id, device_type, torch)
    if device_type == "mps":
        require(torch.backends.mps.is_available(), "当前进程没有可用 MPS", EXIT_RUNTIME)
        device = torch.device("mps")
    else:
        require(torch.cuda.is_available(), "当前进程没有可用 CUDA", EXIT_RUNTIME)
        require(torch.cuda.is_bf16_supported(), "当前 CUDA 设备不支持 BF16", EXIT_RUNTIME)
        device = torch.device("cuda")
    require(profile["parameter_dtype"] == "float32" and profile["optimizer_state_dtype"] == "float32", "参数或优化器状态不是 FP32")
    require(profile["grad_scaler"] is False, "本合同禁止 GradScaler")
    receipt = {
        "device_type": device_type,
        "precision_profile_id": profile_id,
        "torch_version": torch.__version__,
        "platform": platform.platform(),
        "mps_available": bool(torch.backends.mps.is_available()),
        "cuda_available": bool(torch.cuda.is_available()),
    }
    return torch, device, profile, precision


def synchronize_device(torch_module: Any, device: Any) -> None:
    if device.type == "mps":
        torch_module.mps.synchronize()
    else:
        torch_module.cuda.synchronize(device)


def accelerator_memory(torch_module: Any, device: Any) -> dict[str, Any]:
    if device.type == "mps":
        current = int(torch_module.mps.current_allocated_memory()) if hasattr(torch_module.mps, "current_allocated_memory") else None
        driver = int(torch_module.mps.driver_allocated_memory()) if hasattr(torch_module.mps, "driver_allocated_memory") else None
        recommended = int(torch_module.mps.recommended_max_memory()) if hasattr(torch_module.mps, "recommended_max_memory") else None
        return {
            "accelerator_memory_current_bytes": current,
            "accelerator_memory_reserved_or_driver_bytes": driver,
            "accelerator_memory_recommended_max_bytes": recommended,
            "measurement_available": current is not None,
            "measurement_source": "torch.mps",
        }
    return {
        "accelerator_memory_current_bytes": int(torch_module.cuda.memory_allocated(device)),
        "accelerator_memory_reserved_or_driver_bytes": int(torch_module.cuda.memory_reserved(device)),
        "accelerator_memory_peak_sampled_bytes": int(torch_module.cuda.max_memory_allocated(device)),
        "measurement_available": True,
        "measurement_source": "torch.cuda",
    }


def process_peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def capture_rng(torch_module: Any, device: Any) -> dict[str, Any]:
    accelerator_state = None
    if device.type == "mps" and hasattr(torch_module.mps, "get_rng_state"):
        accelerator_state = torch_module.mps.get_rng_state(device)
    elif device.type == "cuda":
        accelerator_state = torch_module.cuda.get_rng_state(device)
    return {
        "python_random": random.getstate(),
        "numpy_random": __import__("numpy").random.get_state(),
        "torch_cpu": torch_module.get_rng_state(),
        "accelerator_type": device.type,
        "accelerator_state": accelerator_state,
    }


def restore_rng(state: dict[str, Any], torch_module: Any, device: Any) -> None:
    require(state["accelerator_type"] == device.type, "检查点加速器类型与当前设备不符", EXIT_RUNTIME)
    random.setstate(state["python_random"])
    __import__("numpy").random.set_state(state["numpy_random"])
    torch_module.set_rng_state(state["torch_cpu"])
    if state["accelerator_state"] is not None:
        if device.type == "mps":
            torch_module.mps.set_rng_state(state["accelerator_state"], device)
        else:
            torch_module.cuda.set_rng_state(state["accelerator_state"], device)


def load_source_arrays_mmap(cache_root: str) -> dict[str, Any]:
    import numpy as np

    root = Path(cache_root)
    arrays = {
        name: np.load(root / f"{name}.npy", mmap_mode="r", allow_pickle=False)
        for name in SOURCE_ARRAYS
    }
    require(arrays["X23"].shape == (base.LSPR23_FLOW_COUNT, base.DIJK_FEATURE_COUNT), "X23 形状不符", EXIT_INPUT)
    require(arrays["I23"].shape == (base.LSPR23_SEQUENCE_COUNT, base.PROTOCOL_A_SEQUENCE_LENGTH), "I23 形状不符", EXIT_INPUT)
    require(arrays["M23"].shape == arrays["I23"].shape, "M23 形状不符", EXIT_INPUT)
    require(arrays["y23"].shape == (base.LSPR23_FLOW_COUNT,), "y23 形状不符", EXIT_INPUT)
    return arrays


def build_training_flow_mask(arrays: dict[str, Any], train_rows: Any, length: int) -> Any:
    import numpy as np

    mask = np.zeros(base.LSPR23_FLOW_COUNT, dtype=bool)
    for start in range(0, len(train_rows), 20_000):
        rows = train_rows[start : start + 20_000]
        indices = arrays["I23"][rows, :length]
        valid = arrays["M23"][rows, :length] > 0.5
        mask[indices[valid]] = True
    return mask


def prepare_data(config: dict[str, Any], base_config: dict[str, Any], output_root: Path) -> tuple[dict[str, Any], Any, Any, Any]:
    arrays = load_source_arrays_mmap(config["paths"]["cache_root"])
    train_rows, validation_rows, split_stats = base.source_split(arrays, base_config)
    transform_path = output_root / "artifacts" / "sealed-input-transform.pkl"
    receipt = base.load_cardinality_receipt(config["paths"]["cardinality_receipt"], base_config)
    if transform_path.is_file():
        transform = base.load_input_transform(transform_path)
    else:
        training_flow_mask = build_training_flow_mask(arrays, train_rows, config["training"]["sequence_length"])
        transform = base.fit_input_transform(
            config["data"]["input_candidate"],
            config["paths"]["cache_root"],
            training_flow_mask,
            receipt,
            config=base_config,
            seed=config["training"]["seed"],
        )
        base.save_input_transform(transform_path, transform)
    view = base.ProtocolASourceView(arrays, transform)
    atomic_json(output_root / "receipts" / "split.json", split_stats)
    atomic_json(output_root / "receipts" / "input-transform.json", transform.receipt())
    return arrays, train_rows, validation_rows, view


def entity_memory_enabled_from_config(config: dict[str, Any]) -> bool:
    """统一的 z1 读取入口，避免各处对 mechanism 缺省值的写法漂移。"""
    mechanism = config.get("mechanism", DEFAULT_MECHANISM)
    return bool(mechanism.get("entity_memory", {}).get("enabled", False))


def entity_gated_ple_enabled_from_config(config: dict[str, Any]) -> bool:
    """统一的 M-E 读取入口。缺省就地给出，不经 DEFAULT_MECHANISM（见该字典上方注释）。"""
    mechanism = config.get("mechanism", DEFAULT_MECHANISM)
    return bool(mechanism.get("entity_gated_ple", {}).get("enabled", False))


def entity_tail_aggregation_enabled_from_config(config: dict[str, Any]) -> bool:
    """统一的尾部聚合开关读取入口，缺省就地给出，不经 DEFAULT_MECHANISM。"""
    mechanism = config.get("mechanism", DEFAULT_MECHANISM)
    return bool(mechanism.get("entity_aggregation", {}).get("enabled", False))


def entity_tail_aggregation_alpha_from_config(config: dict[str, Any]) -> float | None:
    """尾部水平 α，未启用时为 ``None``。

    ``None`` 是训练侧与评价侧共同的「按 max 聚合」信号：``tail_aggregate`` 见到
    ``None`` 就取 `k ≡ 1`，宿主评价侧见到 ``None`` 就走原来的 ``np.maximum.at``。
    两处因此不需要各自记住「关掉时该怎么办」。
    """
    if not entity_tail_aggregation_enabled_from_config(config):
        return None
    mechanism = config.get("mechanism", DEFAULT_MECHANISM)
    return float(mechanism["entity_aggregation"]["alpha"])


def build_role_of_entity(interface: dict[str, Any], entity: Any, entity_count: int) -> Any:
    """从任务 1 接口的 ``is_entity_start`` 行取每个实体的角色，得到 ``(entity_count,)`` 数组。

    角色按实体恒定——同实体全部片段同角色，这正是任务 1 ``same_role`` 断言核验的
    不变量——故只需取每个实体链首片段（``is_entity_start`` 为真）的 ``role_id``
    即可代表整个实体，不需要遍历该实体的其余片段。
    """
    import numpy as np

    role_of_entity = np.full(entity_count, -1, dtype=np.int8)
    starts = interface["is_entity_start"]
    role_of_entity[entity[starts]] = interface["role_id"][starts]
    require(bool((role_of_entity >= 0).all()), "存在没有起始片段的实体，角色映射不完整", EXIT_INPUT)
    return role_of_entity


class EntityChainScheduler:
    """按实体链顺序推进的调度器：把"抽样"从随机片段行改为随机实体，再取该实体
    当前应处理的下一个片段。

    ``chain_rows`` 是按 ``(实体, segment_ordinal)`` 排序、只含本角色行集合的片段行
    数组（CSR 风格），``chain_offsets``/``chain_lengths`` 给出每个实体在其中的区间。
    因为同角色内一个实体的可用片段恒为其全局链的前缀（时间尾部裁剪只影响链尾，
    见机制设计与实验计划第 3.0 节的实测结论），直接复用任务 1 的
    ``previous_segment_row``/``segment_ordinal`` 即为本角色内正确的前驱关系，不需要
    按角色重新计算一份。
    """

    def __init__(self, rows: Any, entity_of_row: Any, segment_ordinal: Any) -> None:
        import numpy as np

        entity_ids = entity_of_row[rows]
        order = np.lexsort((segment_ordinal[rows], entity_ids))
        self.chain_rows = rows[order]
        sorted_entities = entity_ids[order]
        unique_entities, offsets, lengths = np.unique(sorted_entities, return_index=True, return_counts=True)
        self.entity_ids = unique_entities
        self.chain_offsets = offsets
        self.chain_lengths = lengths
        self.cursor = np.zeros(len(unique_entities), dtype=np.int64)

    @property
    def entity_count(self) -> int:
        return len(self.entity_ids)

    def state_dict(self) -> dict[str, Any]:
        """导出续训所需的可变游标。

        ``chain_rows``/``chain_offsets``/``chain_lengths``/``entity_ids`` 由冻结的
        ``rows``、``entity_of_row``、``segment_ordinal`` 确定性地重建，不需入检查点；
        唯一随训练推进而改变的是 ``cursor``（每个实体下一次应取的链内位置）。
        同时导出实体身份供恢复时机械核对，防止跨划分或跨角色错配游标。
        """
        import numpy as np

        return {
            "entity_count": int(self.entity_count),
            "entity_ids_sha256": canonical_sha256(np.asarray(self.entity_ids).tolist()),
            "cursor": np.asarray(self.cursor).astype(np.int64).tolist(),
        }

    def load_state_dict(self, payload: dict[str, Any]) -> None:
        """恢复游标；实体数与实体身份不符即拒绝，不静默按缺省值继续。"""
        import numpy as np

        require(
            int(payload["entity_count"]) == self.entity_count,
            f"调度器实体数不符：检查点 {payload['entity_count']}，当前 {self.entity_count}",
            EXIT_RUNTIME,
        )
        require(
            payload["entity_ids_sha256"] == canonical_sha256(np.asarray(self.entity_ids).tolist()),
            "调度器实体身份不符，拒绝恢复游标",
            EXIT_RUNTIME,
        )
        cursor = np.asarray(payload["cursor"], dtype=np.int64)
        require(
            bool((cursor >= 0).all() and (cursor < self.chain_lengths).all()),
            "调度器游标越出链长范围",
            EXIT_RUNTIME,
        )
        self.cursor = cursor

    def sample_rows(self, count: int, generator: Any) -> tuple[Any, Any]:
        """抽 ``count`` 个互不相同的实体，取各自当前应处理的片段行，并推进游标。

        游标回绕到 0 时即该实体本轮重新从链首（``is_entity_start``）开始；调用方
        通过 ``interface["is_entity_start"][rows]`` 判定是否需要先清零状态，不在
        本类内部重复该判断，保持单一事实来源。
        """
        positions = base.sample_distinct_positions(self.entity_count, count, generator).numpy()
        cursor = self.cursor[positions]
        rows = self.chain_rows[self.chain_offsets[positions] + cursor]
        entities = self.entity_ids[positions]
        self.cursor[positions] = (cursor + 1) % self.chain_lengths[positions]
        return rows, entities

    def validation_rounds(self) -> Any:
        """按链内位置从浅到深逐轮产出该轮仍有片段的实体所在行，覆盖每个实体的
        全部片段恰好一次；每轮内每个实体至多出现一次（不同实体，互不冲突）。
        """
        max_length = int(self.chain_lengths.max()) if self.entity_count else 0
        for position in range(max_length):
            active = self.chain_lengths > position
            if not bool(active.any()):
                continue
            yield self.chain_rows[self.chain_offsets[active] + position], self.entity_ids[active]


def assert_recovery_adjacency(rows: Any, interface: dict[str, Any], entity_of_row: Any) -> None:
    """恢复跨片段状态前核验：非起始片段的前驱与当前片段同实体、同角色、序号恰好相邻。

    对应设计规约第 4.3 节"恢复前同时断言实体、角色、片段序号...相邻"；直接复用
    任务 1 已核验的 ``previous_segment_row``/``role_id``/``segment_ordinal``，本函数
    只是在调度器实际抽到的行子集上重放同一组断言，防止调度器自身的 bug（例如
    误用了不属于本角色前缀的行）绕过任务 1 的全局核验。
    """
    import numpy as np

    is_start = interface["is_entity_start"][rows]
    linked_rows = rows[~is_start]
    if linked_rows.size == 0:
        return
    previous = interface["previous_segment_row"][linked_rows]
    require(bool(np.all(previous >= 0)), "非起始片段的前驱行缺失", EXIT_RUNTIME)
    require(bool(np.all(entity_of_row[previous] == entity_of_row[linked_rows])), "前驱片段实体不一致", EXIT_RUNTIME)
    require(bool(np.all(interface["role_id"][previous] == interface["role_id"][linked_rows])), "前驱片段角色不一致", EXIT_RUNTIME)
    require(
        bool(np.all(interface["segment_ordinal"][linked_rows] - interface["segment_ordinal"][previous] == 1)),
        "前驱片段序号不相邻",
        EXIT_RUNTIME,
    )


def prepare_entity_memory_context(config: dict[str, Any], arrays: dict[str, Any], train_rows: Any, validation_rows: Any, output_root: Path) -> dict[str, Any]:
    """构建机制一所需的严格过去接口、逐实体角色映射与训练/验证两个链式调度器。

    只在 ``z1=1`` 时被调用；``z1=0`` 的路径完全不触碰本函数，天然满足
    "z1=0 时不构造、不读取状态" 的硬约束。
    """
    import numpy as np

    import ch3_ft_entity_memory_interface as entity_interface

    entity = np.asarray(arrays["E23"])
    stamp = np.asarray(arrays["T23"])
    interface = entity_interface.build_interface(
        Path(config["paths"]["cache_root"]), resolve_project_path(config["base"]["config_path"])
    )
    checks = entity_interface.assert_causality(interface, entity, stamp)
    entity_count = int(entity.max()) + 1
    role_of_entity = build_role_of_entity(interface, entity, entity_count)
    train_scheduler = EntityChainScheduler(train_rows, entity, interface["segment_ordinal"])
    validation_scheduler = EntityChainScheduler(validation_rows, entity, interface["segment_ordinal"])
    atomic_json(output_root / "receipts" / "entity-memory-interface.json", {
        "schema_version": "ch3-ft-c10-entity-memory-context-receipt-v1",
        "target_reads": 0,
        "entity_count": entity_count,
        "train_entity_count": train_scheduler.entity_count,
        "validation_entity_count": validation_scheduler.entity_count,
        "causality_assertions": checks,
    })
    return {
        "interface": interface,
        "entity_of_row": entity,
        "role_of_entity": role_of_entity,
        "entity_count": entity_count,
        "train_scheduler": train_scheduler,
        "validation_scheduler": validation_scheduler,
    }


# M-E 的状态归一化尺度取训练区 p99，该 0.99 由 ch3_ft_entity_segment_state.
# fit_state_normalizers 写死实现；配置里的 c_scale_quantile/gap_scale_quantile 只是把它
# 显式登记出来，prepare_entity_gated_ple_context 会核对两者一致，防止配置写了别的分位数
# 却被实现静默忽略（那样运行收据会误述本次运行的口径）。
ENTITY_GATED_PLE_STATE_SCALE_QUANTILE = 0.99

# 门激活片段数的冻结值，来源 tools/ch3_ft_me_gate_scope_probe.py 的 FROZEN
# ["overall_gate_active_segments"]。正式入口在拟合状态后重放这一个数字，
# 确保训练时用的严格过去状态与门作用域文档量化的是同一口径。
ENTITY_GATED_PLE_FROZEN_GATE_ACTIVE_SEGMENTS = 121_135


def _gather_transformed_numeric(
    config: dict[str, Any], arrays: dict[str, Any], train_rows: Any, view: Any
) -> tuple[Any, dict[str, Any]]:
    """取训练区有效流经冻结输入变换后的数值矩阵，供 PLE 箱边界拟合。

    **只用训练区行**：训练区有效流掩码由 ``build_training_flow_mask`` 在同一段
    ``train_rows`` 上产出，与 ``prepare_data`` 拟合输入变换时用的是同一个函数、同一段
    行集合；验证区与目标年 LSPR24 零参与。

    箱边界必须在**分位数变换之后**的张量上拟合——骨干分词器吃的就是这份张量，
    位移通道与它同口径才有意义，因此这里过 ``view.transform.apply`` 而不是读原值。

    规模与内存（2026-08-31 本机实测）：训练区有效流 ``11,991,315`` 条，全量展开成
    ``(n, 81)`` float32 需 ``3.88 GB``，``np.quantile`` 的分区副本再需同量，峰值约
    ``8 GB``。故按冻结的 ``bin_fit_sample_cap`` 做一次确定性无放回抽样（种子取
    ``training.seed``），抽样下标升序排列以保持 mmap 读取的顺序局部性；分块读取，
    每块显式分配上界为 ``chunk × 83 × 4B`` 加 ``chunk × 81 × 4B``。

    ``transform.apply`` 会把本次读取的行数计入 ``source`` 分区的诊断计数器。这些行
    确实是源年训练区行，分区归属正确；计数被抬高的部分由收据的 ``bin_fit_rows``
    说明，冻结状态与 ``state_hash`` 完全不受影响（``apply`` 只读不写冻结状态）。
    """
    import numpy as np

    mechanism = config["mechanism"]["entity_gated_ple"]
    mask = build_training_flow_mask(arrays, train_rows, config["training"]["sequence_length"])
    flow_indices = np.flatnonzero(mask)
    total_rows = int(flow_indices.size)
    require(total_rows > 0, "训练区没有任何有效流，无法拟合 PLE 箱边界", EXIT_INPUT)
    sample_cap = int(mechanism["bin_fit_sample_cap"])
    if total_rows > sample_cap:
        # 用 legacy RandomState 而不是 default_rng：NEP 19 冻结了 RandomState 的流，
        # Generator 的分布方法允许跨 numpy 版本改变取值序列。箱边界是随运行冻结的制品，
        # 本机（numpy 2.4.6）与服务器必须抽到同一批行，故与 base.source_split 用同一种
        # 生成器。抽到的下标升序排列，使 mmap 读取保持顺序局部性。
        permutation = np.random.RandomState(config["training"]["seed"]).permutation(total_rows)
        flow_indices = np.sort(flow_indices[permutation[:sample_cap]])
    sampled_rows = int(flow_indices.size)
    field_count = view.transform.numeric_field_count
    values = np.empty((sampled_rows, field_count), dtype=np.float32)
    started = time.time()
    heartbeat = max(1, sampled_rows // 10)
    LOGGER.info(
        "开始取训练区数值用于 PLE 箱边界拟合：训练有效流=%d，本次取=%d，分块=%d",
        total_rows, sampled_rows, ENTITY_GATED_PLE_FIT_CHUNK_ROWS,
    )
    for start in range(0, sampled_rows, ENTITY_GATED_PLE_FIT_CHUNK_ROWS):
        stop = min(start + ENTITY_GATED_PLE_FIT_CHUNK_ROWS, sampled_rows)
        raw = np.asarray(view.matrix[flow_indices[start:stop]], dtype=np.float32)
        numeric, _categorical = view.transform.apply(raw)
        values[start:stop] = numeric
        if stop == sampled_rows or stop // heartbeat != start // heartbeat:
            elapsed = time.time() - started
            throughput = stop / max(elapsed, 1e-9)
            LOGGER.info(
                "PLE 箱边界取数进度=%d/%d，吞吐=%.0f流/秒，已用=%.1f秒，预计剩余=%.1f秒",
                stop, sampled_rows, throughput, elapsed,
                (sampled_rows - stop) / max(throughput, 1e-9),
            )
    return values, {
        "training_effective_flows": total_rows,
        "bin_fit_sample_cap": sample_cap,
        "bin_fit_rows": sampled_rows,
        "bin_fit_subsampled": sampled_rows < total_rows,
        "bin_fit_seed": config["training"]["seed"],
        "bin_fit_seconds": time.time() - started,
        "fitted_on": "lspr23_protocol_a_training_region_effective_flows_only",
    }


def prepare_entity_gated_ple_context(
    config: dict[str, Any], arrays: dict[str, Any], train_rows: Any, view: Any, output_root: Path
) -> dict[str, Any]:
    """拟合 PLE 箱边界与实体状态归一化常数，二者都只用训练区行。

    只在 M-E 开启时被调用；关闭时完全不触碰本函数，天然满足"不构造、不读取状态"。
    结果随运行收据落盘（含箱边界摘要），供复现与哈希核验。
    """
    import numpy as np

    import ch3_ft_entity_gated_ple as gated_ple
    import ch3_ft_entity_segment_state as segment_state

    mechanism = config["mechanism"]["entity_gated_ple"]
    require(
        mechanism["c_scale_quantile"] == ENTITY_GATED_PLE_STATE_SCALE_QUANTILE
        and mechanism["gap_scale_quantile"] == ENTITY_GATED_PLE_STATE_SCALE_QUANTILE,
        "配置登记的状态尺度分位数与 ch3_ft_entity_segment_state.fit_state_normalizers "
        f"实现的 {ENTITY_GATED_PLE_STATE_SCALE_QUANTILE} 不一致",
    )
    entity = np.asarray(arrays["E23"])
    stamp = np.asarray(arrays["T23"])
    prior_segments, gap = segment_state.compute_segment_state(entity, stamp)
    normalizers = segment_state.fit_state_normalizers(prior_segments, gap, train_rows)
    state_matrix = segment_state.normalize_state(prior_segments, gap, normalizers)
    require(
        state_matrix.shape == (base.LSPR23_SEQUENCE_COUNT, 2),
        f"实体状态矩阵形状不符：{state_matrix.shape}",
        EXIT_INPUT,
    )
    gate_active_segments = int((prior_segments >= 1).sum())
    require(
        gate_active_segments == ENTITY_GATED_PLE_FROZEN_GATE_ACTIVE_SEGMENTS,
        f"门激活片段数 {gate_active_segments} 与冻结值 "
        f"{ENTITY_GATED_PLE_FROZEN_GATE_ACTIVE_SEGMENTS} 不符，严格过去状态口径已漂移",
        EXIT_INPUT,
    )

    training_values, gather_receipt = _gather_transformed_numeric(config, arrays, train_rows, view)
    bin_edges = gated_ple.fit_quantile_bin_edges(training_values, mechanism["bin_count"])
    require(
        bin_edges.shape == (view.transform.numeric_field_count, mechanism["bin_count"] + 1),
        f"箱边界形状不符：{bin_edges.shape}",
        EXIT_RUNTIME,
    )

    receipt = {
        "schema_version": "ch3-ft-entity-gated-ple-context-receipt-v1",
        "target_reads": 0,
        "gate_mode": mechanism["gate_mode"],
        "bin_count": mechanism["bin_count"],
        "gate_hidden": mechanism["gate_hidden"],
        "numeric_field_count": int(view.transform.numeric_field_count),
        "normalizers": normalizers,
        "state_scale_quantile": ENTITY_GATED_PLE_STATE_SCALE_QUANTILE,
        "bin_edges_sha256": canonical_sha256(bin_edges.tolist()),
        # 状态矩阵有 271,815×2 个 float32，走 canonical_sha256 要先序列化成十几兆的 JSON；
        # 这里直接对缓冲区取摘要，语义同样是"逐位身份"，但常数时间内完成。
        "state_matrix_sha256": hashlib.sha256(
            np.ascontiguousarray(state_matrix).tobytes()
        ).hexdigest(),
        "state_rows": int(state_matrix.shape[0]),
        "gate_active_segments": gate_active_segments,
        "gate_inactive_segments": int(state_matrix.shape[0]) - gate_active_segments,
        **gather_receipt,
    }
    atomic_json(output_root / "receipts" / "entity-gated-ple-context.json", receipt)
    LOGGER.info(
        "M-E 上下文已就绪：门模式=%s，箱数=%d，箱边界拟合行=%d/%d，门激活片段=%d",
        mechanism["gate_mode"], mechanism["bin_count"], receipt["bin_fit_rows"],
        receipt["training_effective_flows"], gate_active_segments,
    )
    return {"bin_edges": bin_edges, "state_matrix": state_matrix, "receipt": receipt}


_ENTITY_MEMORY_MODEL_CACHE: dict[str, Any] = {}


def _causal_entity_memory_model_class() -> Any:
    """延迟构造依赖 torch 的整格模型包装类，与 base.transformer_classes 同一惰性缓存写法。

    参数名带 ``backbone.``/``memory.`` 前缀，与 ``base.resolve_weight_decay_groups``
    既有注释预期的挂载模式一致（该函数注释原文："机制外接后参数名带 backbone. 前缀"），
    使权重衰减分组、状态字典与优化器构造无需为本类特化。
    """
    if _ENTITY_MEMORY_MODEL_CACHE:
        return _ENTITY_MEMORY_MODEL_CACHE["CausalEntityMemoryFTModel"]

    from torch import nn

    class CausalEntityMemoryFTModel(nn.Module):
        """裸 FT 主干 + 因果实体记忆交叉注意力的整格包装，仅供 z1=1 使用。"""

        def __init__(self, backbone: Any, memory_attention: Any) -> None:
            super().__init__()
            self.backbone = backbone
            self.memory = memory_attention

        def encode(self, x_num: Any, x_cat: Any) -> Any:
            return self.backbone.encode(x_num, x_cat)

        def predict(self, representation: Any) -> Any:
            return self.backbone.predict(representation)

        def inject(self, representation: Any, memory: Any, memory_valid: Any) -> Any:
            return self.memory(representation, memory, memory_valid)

        def forward(
            self, x_num: Any, x_cat: Any, memory: Any, memory_valid: Any
        ) -> tuple[Any, Any]:
            """统一执行骨干编码、记忆注入和预测，确保 ``torch.compile`` 覆盖 CEM 路径。"""
            representation = self.backbone.encode(x_num, x_cat)
            injected = self.memory(representation, memory, memory_valid)
            return self.backbone.predict(injected), injected

    _ENTITY_MEMORY_MODEL_CACHE["CausalEntityMemoryFTModel"] = CausalEntityMemoryFTModel
    return CausalEntityMemoryFTModel


_ENTITY_GATED_PLE_MODEL_CACHE: dict[str, Any] = {}


def _entity_gated_ple_model_class() -> Any:
    """延迟构造 M-E 整格包装类，与 ``_causal_entity_memory_model_class`` 同一惰性缓存写法。

    M-E 替换的是**分词器**这一步，因此包装体绕过 ``backbone.tokenizer``，改用 M-E 分词器
    产出 Token 后直接进 ``backbone.blocks``；``predict`` 仍完全委派给骨干。
    ``ch3_ft_transformer_field_token_protocol_a.py`` 因此不需要任何改动。

    参数名带 ``backbone.``／``me_tokenizer.`` 前缀。``base.resolve_weight_decay_groups``
    按 ``"tokenizer." in name`` 判定特征标记器例外，``me_tokenizer.`` 命中该子串，
    故 M-E 的位移嵌入与门参数与骨干分词器一样不施加权重衰减——这正是论文表 12
    "特征标记器一律取 0.0" 的口径，不需要为本类特化。

    ``me_tokenizer.base`` 与 ``backbone.tokenizer`` 是同一个对象；PyTorch 的
    ``named_parameters()`` 默认去重，骨干分词器参数只会以 ``backbone.tokenizer.*``
    出现一次，不会被重复计入总量或重复交给优化器。
    """
    if _ENTITY_GATED_PLE_MODEL_CACHE:
        return _ENTITY_GATED_PLE_MODEL_CACHE["EntityGatedPLEFTModel"]

    from torch import nn

    class EntityGatedPLEFTModel(nn.Module):
        """裸 FT 主干 + 实体门控分段线性数值分词的整格包装，仅供 M-E 三臂使用。"""

        def __init__(self, backbone: Any, tokenizer: Any) -> None:
            super().__init__()
            self.backbone = backbone
            self.me_tokenizer = tokenizer

        def encode(self, x_num: Any, x_cat: Any, entity_state: Any) -> Any:
            return self.backbone.blocks(self.me_tokenizer(x_num, x_cat, entity_state))

        def predict(self, representation: Any) -> Any:
            return self.backbone.predict(representation)

        def forward(self, x_num: Any, x_cat: Any, entity_state: Any) -> Any:
            return self.backbone.predict(self.encode(x_num, x_cat, entity_state))

    _ENTITY_GATED_PLE_MODEL_CACHE["EntityGatedPLEFTModel"] = EntityGatedPLEFTModel
    return EntityGatedPLEFTModel


def build_model_optimizer(
    config: dict[str, Any], base_config: dict[str, Any], view: Any, torch_module: Any, device: Any,
    mechanism_context: dict[str, Any] | None = None,
) -> tuple[Any, Any, dict[str, Any]]:
    # mechanism_context 默认 None，使 z1=0、CEM 与 BER 三条既有路径的调用点一字不改；
    # 只有 M-E 需要在建模前拿到训练区拟合的箱边界，故由调用方显式传入。
    entity_memory_enabled = entity_memory_enabled_from_config(config)
    entity_gated_ple_enabled = entity_gated_ple_enabled_from_config(config)

    backbone = base.build_model(base_config, view.transform, input_key=config["data"]["input_candidate"])
    backbone_actual = sum(parameter.numel() for parameter in backbone.parameters() if parameter.requires_grad)
    require(backbone_actual == BARE_FT_PARAMETER_COUNT, f"裸 FT 骨干参数量不符：{backbone_actual}", EXIT_RUNTIME)
    names = tuple(name for name, _ in backbone.named_parameters())
    require(not any("fusion" in name or "p_log" in name for name in names), "裸 FT 含旧机制脚手架", EXIT_RUNTIME)

    if entity_memory_enabled:
        # 延迟导入：ch3_ft_causal_entity_memory 在其模块顶层无条件 import torch，
        # 只有真正启用机制一时才需要它，保持 z1=0 路径（含 --validate-config）不变。
        import ch3_ft_causal_entity_memory as entity_memory

        slots = config["mechanism"]["entity_memory"]["slots"]
        width = base_config["architecture"]["d_token"]
        heads = base_config["architecture"]["n_heads"]
        cross_checked = entity_memory.causal_entity_memory_parameter_count(width, slots)
        require(
            cross_checked == entity_memory_parameter_count(width, slots),
            "机制一参数量闭式两处实现不一致（ch3_ft_c00_dual_selection 与 ch3_ft_causal_entity_memory）",
            EXIT_RUNTIME,
        )
        attention = entity_memory.CausalEntityMemoryAttention(width=width, heads=heads, slots=slots)
        attention_actual = sum(parameter.numel() for parameter in attention.parameters() if parameter.requires_grad)
        require(attention_actual == cross_checked, f"机制一参数量不符：{attention_actual}", EXIT_RUNTIME)
        require(
            config["model"]["expected_parameter_count"] == backbone_actual + attention_actual,
            "冻结 expected_parameter_count 与实测不符",
            EXIT_RUNTIME,
        )
        model_class = _causal_entity_memory_model_class()
        model = model_class(backbone, attention)
    elif entity_gated_ple_enabled:
        # 延迟导入：ch3_ft_entity_gated_ple 在其模块顶层无条件 import torch，
        # 只有真正启用 M-E 时才需要它，保持 --validate-config 路径不变。
        import ch3_ft_entity_gated_ple as gated_ple

        require(
            mechanism_context is not None and "bin_edges" in mechanism_context,
            "M-E 需要在建模前拿到训练区拟合的箱边界，但 mechanism_context 缺失",
            EXIT_RUNTIME,
        )
        mechanism = config["mechanism"]["entity_gated_ple"]
        width = base_config["architecture"]["d_token"]
        field_count = view.transform.numeric_field_count
        cross_checked = gated_ple.entity_gated_ple_parameter_count(
            field_count, mechanism["bin_count"], width, mechanism["gate_hidden"],
            gate_mode=mechanism["gate_mode"],
        )
        require(
            cross_checked == entity_gated_ple_parameter_count(
                field_count, mechanism["bin_count"], width, mechanism["gate_hidden"],
                mechanism["gate_mode"],
            ),
            "M-E 参数量闭式两处实现不一致（ch3_ft_c00_dual_selection 与 ch3_ft_entity_gated_ple）",
            EXIT_RUNTIME,
        )
        tokenizer = gated_ple.EntityGatedPLETokenizer(
            base_tokenizer=backbone.tokenizer,
            bin_edges=torch_module.from_numpy(mechanism_context["bin_edges"]),
            d_token=width,
            gate_hidden=mechanism["gate_hidden"],
            gate_mode=mechanism["gate_mode"],
        )
        # base_tokenizer 以子模块持有，其参数会出现在 tokenizer.named_parameters() 里；
        # 不排除 base. 前缀就会把骨干分词器参数重复计入 M-E 专属量。
        own = sum(
            parameter.numel()
            for name, parameter in tokenizer.named_parameters()
            if parameter.requires_grad and not name.startswith("base.")
        )
        require(own == cross_checked, f"M-E 参数量不符：{own} 对 {cross_checked}", EXIT_RUNTIME)
        require(
            config["model"]["expected_parameter_count"] == backbone_actual + own,
            "冻结 expected_parameter_count 与实测不符",
            EXIT_RUNTIME,
        )
        model_class = _entity_gated_ple_model_class()
        model = model_class(backbone, tokenizer)
        # 去重后骨干分词器只算一次，整格实测参数量必须恰为骨干加 M-E 专属量。
        model_actual = sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        )
        require(
            model_actual == backbone_actual + own,
            f"M-E 整格参数量 {model_actual} 与骨干 {backbone_actual} 加专属 {own} 不符",
            EXIT_RUNTIME,
        )
    else:
        require(config["model"]["expected_parameter_count"] == backbone_actual, "裸 FT 参数量不符", EXIT_RUNTIME)
        model = backbone

    model = model.to(device)
    optimizer, optimizer_receipt = base.make_optimizer(base_config, model, config["optimizer"]["candidate_key"])
    model = maybe_compile(model, config, torch_module)
    return model, optimizer, optimizer_receipt


def maybe_compile(model: Any, config: dict[str, Any], torch_module: Any) -> Any:
    """按运行配置启用 torch.compile；未启用时原样返回。

    数值边界（2026-08-28 服务器实测，PyTorch 2.13.0+cu130 / sm_120）：编译前后 logits
    **非逐位相等**，最大绝对差 8.940697e-07；训练步提速 1.316 倍。因此 compile 属于
    改变数值路径的运行配置，**必须在比较集第一个臂启动前统一决定**——四格若混用编译与
    非编译，训练轨迹自第一步分叉，单种子下无法区分机制效应与轨迹噪声。

    用户 2026-08-28 裁决：四格统一启用 compile 并重跑 C00、C10。故本函数的开关值由
    各格配置的 ``runtime.torch_compile`` 给出，四格必须一致；不一致由 ``run_training``
    的收据比对暴露，本函数只负责按配置执行并把实际生效值写进运行收据。

    优化器在编译前创建（``build_model_optimizer`` 已保证该顺序），因为编译返回的包装体
    与原模块共享同一批 ``Parameter`` 对象，先建优化器可避免参数身份分叉。
    """
    settings = config["runtime"].get("torch_compile")
    # 2026-09-01 用户裁决：本仓库统一停用 torch.compile，不再逐配置开关。
    # 此处无条件早退，使所有运行走即时执行；下方编译分支保留但不可达，
    # 以便将来若要恢复只需删除这三行。已跑完运行的配置是冻结证据，不修改，
    # 因此对仍写着 enabled=true 的旧配置只做披露，不阻断——执行路径收据记录实际路径。
    if isinstance(settings, dict) and settings.get("enabled"):
        LOGGER.warning(
            "配置 runtime.torch_compile.enabled=true，但本仓库已统一停用 torch.compile；"
            "本次按即时执行运行，以执行路径收据的实际记录为准",
        )
    return model

    settings = config["runtime"].get("torch_compile")
    if not isinstance(settings, dict) or not settings.get("enabled"):
        return model
    mode = settings.get("mode", "default")
    require(
        mode in ("default", "reduce-overhead", "max-autotune"),
        f"未知的 torch.compile 模式：{mode}",
        EXIT_INPUT,
    )
    require(
        hasattr(torch_module, "compile"),
        f"当前 PyTorch {torch_module.__version__} 无 torch.compile",
        EXIT_RUNTIME,
    )
    compiled = torch_module.compile(model, mode=mode)
    # torch.compile 返回的 OptimizedModule 会给 state_dict 的每个键加 "_orig_mod." 前缀，
    # 使检查点键与非编译运行、以及零门核验用的裸模型不匹配。把 state_dict/load_state_dict
    # 委派回原模块，保证「编译只改执行路径，不改状态字典布局」——检查点因此在编译与
    # 非编译运行之间保持同一套键，续训与零门核验都不受影响。
    compiled.state_dict = model.state_dict
    compiled.load_state_dict = model.load_state_dict
    LOGGER.info("启用 torch.compile：mode=%s（数值路径与非编译运行不同，四格须一致）", mode)
    return compiled


def forward_bare(
    model: Any, numeric: Any, categorical: Any, valid: Any, device: Any, profile: dict[str, Any],
    precision: Any, torch_module: Any, *, site: str = "flow_forward_bare_train",
    entity_state: Any = None,
) -> Any:
    """统一的逐流前向入口。

    ``entity_state is None`` 时逐字保持既有行为：``z1=0``、CEM 与 BER 三条既有路径的
    数值路径一位不变。传入时走 M-E 分支——``entity_state`` 是**逐片段**的 ``(batch, 2)``，
    而前向是**逐流展平**的 ``(batch × length, F)``，故沿时间轴广播：同一片段内所有流
    共享该片段的实体状态，这与形式化第 3.2 节一致，``s_{e,t}`` 定义在片段上、不随
    片段内的流位置变化。
    """
    # site 只服务执行路径收据：同一个 forward_bare 被训练、验证、C01 逐流阶段与零门
    # 断言四处调用，收据必须能分辨它们各自实际进的是编译包装体还是原模块。
    execution_path.LEDGER.record(site, model, checkpointed=False)
    numeric_t = torch_module.from_numpy(numeric).to(device)
    categorical_t = torch_module.from_numpy(categorical).to(device) if categorical is not None else None
    valid_t = torch_module.from_numpy(valid).to(device)
    batch, length = valid.shape
    flat_num = numeric_t.reshape(batch * length, numeric_t.shape[-1])
    flat_cat = categorical_t.reshape(batch * length, categorical_t.shape[-1]) if categorical_t is not None else None
    with precision.autocast_context(profile, device.type, torch_module):
        if entity_state is None:
            logits = model(flat_num, flat_cat).reshape(batch, length)
        else:
            state_t = torch_module.from_numpy(entity_state).to(device)
            flat_state = state_t.unsqueeze(1).expand(batch, length, 2).reshape(batch * length, 2)
            logits = model(flat_num, flat_cat, flat_state).reshape(batch, length)
    return logits, valid_t


def training_step(
    config: dict[str, Any], base_config: dict[str, Any], model: Any, optimizer: Any,
    view: Any, train_rows: Any, generator: Any, device: Any, profile: dict[str, Any],
    precision: Any, torch_module: Any, positive_weight: Any,
    mechanism_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """裸 FT 逐流训练步。

    ``mechanism_context`` 默认 ``None``，此时行为与既有 ``z1=0`` 路径逐字一致。
    M-E 开启时传入含 ``state_matrix`` 的上下文，按本批片段行索引取实体状态；
    该矩阵在 ``prepare_entity_gated_ple_context`` 阶段算一次，不在每步重算。
    """
    import numpy as np

    effective = config["training"]["effective_batch_size"]
    micro = config["training"]["micro_batch_sequences"]
    positions = base.sample_distinct_positions(len(train_rows), effective, generator)
    rows = train_rows[positions.numpy()]
    state_matrix = mechanism_context["state_matrix"] if mechanism_context is not None else None
    indices, valid, labels = view.gather_sequences(rows, config["training"]["sequence_length"])
    total_valid = int(valid.sum())
    loss_fn = torch_module.nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    accumulator = base.no_clip_accumulator_class()(
        total_valid_units=total_valid,
        normalization_unit=base.NORMALIZATION_UNIT,
        torch_module=torch_module,
        expected_microbatches=config["training"]["gradient_accumulation_steps"],
    )
    accumulator.begin(optimizer)
    loss_total = 0.0
    model.train()
    for start in range(0, effective, micro):
        stop = start + micro
        numeric, categorical = view.features(indices[start:stop])
        logits, valid_t = forward_bare(
            model, numeric, categorical, valid[start:stop], device, profile, precision, torch_module,
            entity_state=None if state_matrix is None else state_matrix[rows[start:stop]],
        )
        labels_t = torch_module.from_numpy(labels[start:stop]).to(device)
        mask32 = valid_t.to(torch_module.float32)
        with precision.fp32_island(logits, device_type=device.type, torch_module=torch_module) as (logits32,):
            loss_sum = (loss_fn(logits32, labels_t.to(torch_module.float32)) * mask32).sum()
        normalized = accumulator.backward(loss_sum, int(valid[start:stop].sum()), scaler=None)
        loss_total += float(normalized.detach().cpu())
    gradient_norm = accumulator.finish(list(model.parameters()), optimizer, torch_module)
    return {
        "loss": loss_total,
        "gradient_norm": float(gradient_norm.detach().cpu()),
        "valid_flows": total_valid,
        "sampled_sequences": effective,
    }


def validation_metrics(
    config: dict[str, Any], model: Any, view: Any, arrays: dict[str, Any], validation_rows: Any,
    device: Any, profile: dict[str, Any], precision: Any, torch_module: Any,
    mechanism_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """完整源验证扫描。``mechanism_context`` 默认 ``None``，此时行为与既有路径逐字一致。

    M-E 开启时按验证片段行索引取同一份预计算实体状态矩阵——验证区实体的 `c`、`Δ`
    同样只由该实体的严格过去片段决定，与训练区共用一份计算，不需要第二套口径。

    实体聚合口径**恒算两条**，与 ``mechanism.entity_aggregation`` 的开关无关
    （2026-09-01 C10 路线裁决第〇节「不允许保守设定」的改正措施）：
    ``validation_entity_ap`` 恒为历史的 ``np.maximum.at`` 口径（max，语义与改造前
    逐位相同，不再由配置的 alpha 挑选分支）；``validation_entity_ap_tail`` 恒为冻结
    α=0.5 的 ``ch3_ft_entity_ranking_loss.tail_aggregate`` top-k 口径（与训练侧
    **同一份**算术实现，评价期用完整袋，不受排序袋 8192 截断偏差影响）。一次训练
    因此同时产出两种选轮依据：C00 用前者选轮，C10 用后者独立选出自己的最佳轮，
    两格共享同一份权重轨迹。
    """
    import numpy as np
    from sklearn.metrics import average_precision_score

    state_matrix = mechanism_context["state_matrix"] if mechanism_context is not None else None
    batch_sequences = config["training"]["validation_batch_sequences"]
    predictions: list[Any] = []
    targets: list[Any] = []
    entity_ids: list[Any] = []
    seen = np.zeros(base.LSPR23_FLOW_COUNT, dtype=bool)
    model.eval()
    started = time.time()
    heartbeat = max(1, len(validation_rows) // 10)
    LOGGER.info(
        "开始完整源验证：序列=%d，验证批=%d，设备=%s",
        len(validation_rows), batch_sequences, device.type,
    )
    with torch_module.no_grad():
        for start in range(0, len(validation_rows), batch_sequences):
            rows = validation_rows[start : start + batch_sequences]
            indices, valid, labels = view.gather_sequences(rows, config["training"]["sequence_length"])
            numeric, categorical = view.features(indices)
            logits, _ = forward_bare(
                model, numeric, categorical, valid, device, profile, precision, torch_module,
                site="flow_forward_bare_validation",
                entity_state=None if state_matrix is None else state_matrix[rows],
            )
            scores = torch_module.sigmoid(logits.to(torch_module.float32)).cpu().numpy()
            selected_indices = indices[valid]
            require(not bool(seen[selected_indices].any()), "验证流被重复计分", EXIT_INPUT)
            seen[selected_indices] = True
            predictions.append(scores[valid])
            targets.append(labels[valid])
            repeated_entities = np.broadcast_to(np.asarray(arrays["E23"][rows])[:, None], indices.shape)
            entity_ids.append(repeated_entities[valid])
            completed = min(start + len(rows), len(validation_rows))
            if completed == len(validation_rows) or completed // heartbeat != start // heartbeat:
                elapsed = time.time() - started
                throughput = completed / max(elapsed, 1e-9)
                remaining = (len(validation_rows) - completed) / max(throughput, 1e-9)
                LOGGER.info(
                    "源验证进度=%d/%d，吞吐=%.1f序列/秒，预计剩余=%.1f秒",
                    completed, len(validation_rows), throughput, remaining,
                )
    synchronize_device(torch_module, device)
    scores = np.concatenate(predictions).astype(np.float64, copy=False)
    labels = np.concatenate(targets).astype(np.float32, copy=False)
    entities = np.concatenate(entity_ids).astype(np.int64, copy=False)
    flow_ap = float(average_precision_score(labels, scores))
    entity_count = int(np.max(arrays["E23"])) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    # 实体标签恒取该实体全部流标签的最大值，与聚合口径无关，两条口径共用。
    np.maximum.at(entity_labels, entities, labels)

    # 口径一：max（历史实现，逐位不变；现在与配置的 alpha 无关地恒算——C00 的
    # 选轮口径不因某份配置自身是否启用尾部聚合而改变，backward-compat 由此保证）。
    max_entity_scores = np.full(entity_count, -np.inf, dtype=np.float64)
    np.maximum.at(max_entity_scores, entities, scores)
    scored_entities_max = np.isfinite(max_entity_scores)
    entity_ap_max = float(
        average_precision_score(entity_labels[scored_entities_max], max_entity_scores[scored_entities_max])
    )

    # 口径二：α=0.5 top-k（冻结常量 ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA，与配置的
    # alpha 无关地恒算）。评价侧挂载点：与训练侧调用**同一份** tail_aggregate，
    # 不另写一套重聚合。延迟导入：该模块顶层无条件 import torch，而本文件的
    # --validate-config 路径必须能在缺 torch 的项目 .venv 上跑通。
    import ch3_ft_entity_ranking_loss as ranking

    # 在 CPU、float64 上聚合：与被替换的 np.maximum.at 同精度，且 k≡1 时逐位相同
    # （本机已实测，见尾部聚合训练侧实现报告的验证 7）。
    aggregated = ranking.tail_aggregate(
        torch_module.from_numpy(scores),
        torch_module.ones(scores.shape[0], dtype=torch_module.bool),
        torch_module.from_numpy(entities),
        entity_count,
        ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA,
    )
    scored_entities_tail = (aggregated["m_per_entity"] > 0).numpy()
    tail_entity_scores = aggregated["entity_scores"].numpy()
    entity_ap_tail = float(
        average_precision_score(entity_labels[scored_entities_tail], tail_entity_scores[scored_entities_tail])
    )
    tail_receipt = ranking.tail_aggregation_receipt(
        aggregated["k_per_entity"], aggregated["m_per_entity"], ENTITY_TAIL_AGGREGATION_FROZEN_ALPHA
    )
    model.train()
    return {
        "validation_flow_ap": flow_ap,
        "validation_entity_ap": entity_ap_max,
        "validation_entity_ap_tail": entity_ap_tail,
        "scored_flows": int(len(scores)),
        "scored_entities": int(scored_entities_max.sum()),
        "positive_entities": int((entity_labels[scored_entities_max] == 1).sum()),
        # 评价侧的 inner_tail_frac 等聚合标量；现在恒算，不再由某份配置的开关
        # 决定是否计算——两种聚合口径逐轮同时评价（2026-09-01 C10 路线裁决）。
        "entity_tail_aggregation": tail_receipt,
        "seconds": time.time() - started,
    }


def _broadcast_segment_memory(segment_memory: Any, segment_valid: Any, batch: int, length: int) -> tuple[Any, Any]:
    """把每段一份的记忆读数广播到该段内全部 ``length`` 个流位置。

    机制一对 K/V（严格过去记忆）按片段读取一次，但交叉注意力的 query 与输出仍是
    逐流的（每个流有各自的 [CLS] 表示，因此各自的注意力权重与上下文），这正是设计
    规约第 4.5 节 FLOP 表"按有效批 64 序列（8,192 流）计"的来源——K/V 共享、query
    逐流。
    """
    slots, width = segment_memory.shape[1], segment_memory.shape[2]
    broadcast_memory = (
        segment_memory.unsqueeze(1).expand(batch, length, slots, width).reshape(batch * length, slots, width)
    )
    broadcast_valid = segment_valid.unsqueeze(1).expand(batch, length, slots).reshape(batch * length, slots)
    return broadcast_memory, broadcast_valid


def _segment_summary_from_injected(injected: Any, valid: Any, batch: int, length: int, width: int, torch_module: Any, device: Any) -> Any:
    """段级摘要＝该段最后一个有效流的注入后表示（严格过去记忆槽 0 保存的"最终表示"）。

    ``valid``（numpy，``(batch,length)``）在本数据集中恒为前缀掩码（已用本机真实
    ``M23`` 核验：抽样 5,000 段掩码全部是"先若干个真、后面全假"的前缀形态），故
    "最后一个有效流位置" 等于 ``valid.sum(axis=1) - 1``，不需要更通用但更贵的
    逐段扫描。``source_split`` 已断言每段至少一个有效流，因此该下标恒 ≥ 0。
    """
    import numpy as np

    last_valid_index = valid.sum(axis=1) - 1
    require(bool(np.all(last_valid_index >= 0)), "存在没有任何有效流的片段", EXIT_INPUT)
    reshaped = injected.reshape(batch, length, width)
    return reshaped[torch_module.arange(batch, device=device), torch_module.from_numpy(last_valid_index).to(device)]


def entity_memory_training_step(
    config: dict[str, Any], base_config: dict[str, Any], model: Any, optimizer: Any,
    view: Any, scheduler: "EntityChainScheduler", memory_state: Any, interface: dict[str, Any],
    entity_of_row: Any, generator: Any, device: Any, profile: dict[str, Any],
    precision: Any, torch_module: Any, positive_weight: Any,
) -> dict[str, Any]:
    """z1=1 的训练步：按实体链顺序推进（不使用随机片段采样器）。

    每个微批只在片段级别读一次严格过去记忆（广播到该段内全部流位置），预测完成后
    立即按段写回（段级摘要＝最后一个有效流的注入后表示），随后才计算损失并反传——
    写回只依赖前向的值，不依赖反传是否已发生，提前写入更简单也更不容易遗漏。
    """
    import numpy as np

    effective = config["training"]["effective_batch_size"]
    micro = config["training"]["micro_batch_sequences"]
    rows, entity_ids_np = scheduler.sample_rows(effective, generator)
    assert_recovery_adjacency(rows, interface, entity_of_row)

    indices, valid, labels = view.gather_sequences(rows, config["training"]["sequence_length"])
    is_start_np = interface["is_entity_start"][rows]
    total_valid = int(valid.sum())
    loss_fn = torch_module.nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    accumulator = base.no_clip_accumulator_class()(
        total_valid_units=total_valid,
        normalization_unit=base.NORMALIZATION_UNIT,
        torch_module=torch_module,
        expected_microbatches=config["training"]["gradient_accumulation_steps"],
    )
    accumulator.begin(optimizer)
    loss_total = 0.0
    reset_count = 0
    recovery_count = 0
    model.train()
    for start in range(0, effective, micro):
        stop = start + micro
        micro_rows = rows[start:stop]
        micro_entity_ids = torch_module.from_numpy(entity_ids_np[start:stop].astype(np.int64)).to(device)
        micro_is_start = torch_module.from_numpy(is_start_np[start:stop]).to(device)
        micro_valid = valid[start:stop]

        if bool(micro_is_start.any()):
            memory_state.reset_entities(micro_entity_ids[micro_is_start])
            reset_count += int(micro_is_start.sum().item())
        recovery_count += int(micro_rows.shape[0]) - int(micro_is_start.sum().item())

        segment_memory = memory_state.read(micro_entity_ids)
        segment_valid = memory_state.valid(micro_entity_ids)

        numeric, categorical = view.features(indices[start:stop])
        numeric_t = torch_module.from_numpy(numeric).to(device)
        categorical_t = torch_module.from_numpy(categorical).to(device) if categorical is not None else None
        valid_t = torch_module.from_numpy(micro_valid).to(device)
        batch, length = micro_valid.shape
        flat_num = numeric_t.reshape(batch * length, numeric_t.shape[-1])
        flat_cat = categorical_t.reshape(batch * length, categorical_t.shape[-1]) if categorical_t is not None else None

        execution_path.LEDGER.record("flow_forward_entity_memory_train", model, checkpointed=False)
        with precision.autocast_context(profile, device.type, torch_module):
            broadcast_memory, broadcast_valid = _broadcast_segment_memory(segment_memory, segment_valid, batch, length)
            logits_flat, injected = model(flat_num, flat_cat, broadcast_memory, broadcast_valid)
            logits = logits_flat.reshape(batch, length)

        width = injected.shape[-1]
        summary = _segment_summary_from_injected(injected, micro_valid, batch, length, width, torch_module, device)
        memory_state.write(micro_entity_ids, summary)

        labels_t = torch_module.from_numpy(labels[start:stop]).to(device)
        mask32 = valid_t.to(torch_module.float32)
        with precision.fp32_island(logits, device_type=device.type, torch_module=torch_module) as (logits32,):
            loss_sum = (loss_fn(logits32, labels_t.to(torch_module.float32)) * mask32).sum()
        normalized = accumulator.backward(loss_sum, int(micro_valid.sum()), scaler=None)
        loss_total += float(normalized.detach().cpu())

    gradient_norm = accumulator.finish(list(model.parameters()), optimizer, torch_module)
    return {
        "loss": loss_total,
        "gradient_norm": float(gradient_norm.detach().cpu()),
        "valid_flows": total_valid,
        "sampled_sequences": effective,
        "state_reset_count": reset_count,
        "cross_segment_recovery_count": recovery_count,
        "gate": model.memory.gate_statistics(),
    }


def entity_memory_validation_metrics(
    config: dict[str, Any], model: Any, view: Any, arrays: dict[str, Any], scheduler: "EntityChainScheduler",
    memory_state: Any, interface: dict[str, Any], entity_of_row: Any,
    device: Any, profile: dict[str, Any], precision: Any, torch_module: Any,
) -> dict[str, Any]:
    """z1=1 的完整确定性验证扫描：逐轮覆盖每个验证实体的全部片段恰好一次。

    每轮验证前先把验证角色的全部状态清零（``reset_role``），保证同一检查点在不同
    轮次重复评价时结果可复现，不携带上一次验证遗留的状态。
    """
    import numpy as np
    from sklearn.metrics import average_precision_score

    batch_sequences = config["training"]["validation_batch_sequences"]
    memory_state.reset_role(ENTITY_MEMORY_ROLE_VALIDATION)
    predictions: list[Any] = []
    targets: list[Any] = []
    entity_ids_scored: list[Any] = []
    gate_means: list[float] = []
    valid_slot_means: list[float] = []
    reset_count = 0
    recovery_count = 0
    no_history_flow_count = 0
    total_flow_count = 0
    seen = np.zeros(base.LSPR23_FLOW_COUNT, dtype=bool)
    model.eval()
    started = time.time()
    with torch_module.no_grad():
        for round_rows, round_entities in scheduler.validation_rounds():
            assert_recovery_adjacency(round_rows, interface, entity_of_row)
            is_start_np = interface["is_entity_start"][round_rows]
            for start in range(0, len(round_rows), batch_sequences):
                stop = start + batch_sequences
                micro_rows = round_rows[start:stop]
                micro_entity_ids = torch_module.from_numpy(round_entities[start:stop].astype(np.int64)).to(device)
                micro_is_start = torch_module.from_numpy(is_start_np[start:stop]).to(device)

                if bool(micro_is_start.any()):
                    memory_state.reset_entities(micro_entity_ids[micro_is_start])
                    reset_count += int(micro_is_start.sum().item())
                recovery_count += int(micro_rows.shape[0]) - int(micro_is_start.sum().item())

                segment_memory = memory_state.read(micro_entity_ids)
                segment_valid = memory_state.valid(micro_entity_ids)
                no_history_flow_count += int((~segment_valid.any(dim=1)).sum().item())

                indices, valid, labels = view.gather_sequences(micro_rows, config["training"]["sequence_length"])
                numeric, categorical = view.features(indices)
                numeric_t = torch_module.from_numpy(numeric).to(device)
                categorical_t = torch_module.from_numpy(categorical).to(device) if categorical is not None else None
                batch, length = valid.shape
                flat_num = numeric_t.reshape(batch * length, numeric_t.shape[-1])
                flat_cat = categorical_t.reshape(batch * length, categorical_t.shape[-1]) if categorical_t is not None else None

                execution_path.LEDGER.record("flow_forward_entity_memory_validation", model, checkpointed=False)
                broadcast_memory, broadcast_valid = _broadcast_segment_memory(segment_memory, segment_valid, batch, length)
                logits_flat, injected = model(flat_num, flat_cat, broadcast_memory, broadcast_valid)
                logits = logits_flat.reshape(batch, length)
                gate_means.append(model.memory.gate_statistics()["gate_mean"])
                valid_slot_means.append(float(segment_valid.sum(dim=1).to(torch_module.float32).mean().item()))

                width = injected.shape[-1]
                summary = _segment_summary_from_injected(injected, valid, batch, length, width, torch_module, device)
                memory_state.write(micro_entity_ids, summary)

                scores = torch_module.sigmoid(logits.to(torch_module.float32)).cpu().numpy()
                selected_indices = indices[valid]
                require(not bool(seen[selected_indices].any()), "验证流被重复计分", EXIT_INPUT)
                seen[selected_indices] = True
                predictions.append(scores[valid])
                targets.append(labels[valid])
                repeated_entities = np.broadcast_to(np.asarray(arrays["E23"][micro_rows])[:, None], indices.shape)
                entity_ids_scored.append(repeated_entities[valid])
                total_flow_count += int(valid.sum())

    synchronize_device(torch_module, device)
    expected_total_flows = int(np.asarray(arrays["M23"])[scheduler.chain_rows][:, : config["training"]["sequence_length"]].astype(bool).sum())
    require(total_flow_count == expected_total_flows, "验证扫描的流总数与独立统计不符", EXIT_INPUT)

    scores = np.concatenate(predictions).astype(np.float64, copy=False)
    labels_all = np.concatenate(targets).astype(np.float32, copy=False)
    entities = np.concatenate(entity_ids_scored).astype(np.int64, copy=False)
    flow_ap = float(average_precision_score(labels_all, scores))
    entity_count = int(np.max(arrays["E23"])) + 1
    entity_scores = np.full(entity_count, -np.inf, dtype=np.float64)
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_scores, entities, scores)
    np.maximum.at(entity_labels, entities, labels_all)
    scored_entities = np.isfinite(entity_scores)
    entity_ap = float(average_precision_score(entity_labels[scored_entities], entity_scores[scored_entities]))
    model.train()
    return {
        "validation_flow_ap": flow_ap,
        "validation_entity_ap": entity_ap,
        "scored_flows": int(len(scores)),
        "scored_entities": int(scored_entities.sum()),
        "positive_entities": int((entity_labels[scored_entities] == 1).sum()),
        "seconds": time.time() - started,
        "mechanism_diagnostics": {
            "gate_mean": float(np.mean(gate_means)) if gate_means else None,
            "mean_valid_memory_slots": float(np.mean(valid_slot_means)) if valid_slot_means else None,
            "state_reset_count": reset_count,
            "cross_segment_recovery_count": recovery_count,
            "no_history_flow_ratio": (no_history_flow_count / total_flow_count) if total_flow_count else None,
        },
    }


def assert_zero_gate_degeneracy(
    config: dict[str, Any], base_config: dict[str, Any], model: Any, memory_state: Any,
    view: Any, train_rows: Any, device: Any, profile: dict[str, Any], precision: Any, torch_module: Any,
) -> None:
    """z1=0 时机械核验两件事：不构造记忆状态；首批 logits 与新建裸模型逐位相等。

    第二项用 ``torch.equal``（不是 ``allclose``）：新建一个裸模型、把当前模型的
    权重原样加载进去，用相同的一小批真实数据各自前向一次，比较 logits。z1=0 时
    ``model`` 就是 ``base.build_model`` 的直接返回值（没有任何包装），这一断言把
    "z1=0 路径与裸 FT 逐位等价" 从"代码没有改动因而必然如此"变成一条可机械核验、
    可在未来重构后继续把关的运行时收据。
    """
    entity_memory_enabled = entity_memory_enabled_from_config(config)
    require(entity_memory_enabled or memory_state is None, "z1=0 时不得构造记忆状态", EXIT_RUNTIME)
    if entity_memory_enabled:
        return
    if entity_gated_ple_enabled_from_config(config):
        # M-E 的 model 是 EntityGatedPLEFTModel 包装体，state_dict 的键带 backbone./
        # me_tokenizer. 前缀，把它加载进一个裸 FT 会直接报键不匹配；而且 M-E 本来就
        # **不是**逐位等价于裸 FT 的路径，这条断言的前提不成立。M-E 的零门退化是
        # "同一组权重内、位移置零后逐位退化"，与本函数比较的"跨模型逐位相等"不是一回事，
        # 见 .Codex/docs/RWKV/2026-08-31-M-E门作用域源年量化.md 第 4.4 节的更正。
        LOGGER.info("M-E 臂跳过跨模型零门断言：其退化性是同权重内的位移置零，不是跨模型逐位相等")
        return

    reference = base.build_model(base_config, view.transform, input_key=config["data"]["input_candidate"])
    reference.load_state_dict(model.state_dict())
    reference = reference.to(device).eval()
    # 参照模型必须与被测模型走同一条数值路径，否则本断言测的是「编译 vs 未编译」的
    # 已知差异（服务器实测最大绝对差 8.94e-07），而不是「z1=0 是否改变输出」。
    # 编译只改执行路径，故对参照做同样处理后，两者仍应逐位相等。
    reference = maybe_compile(reference, config, torch_module)

    probe_rows = train_rows[: min(4, len(train_rows))]
    indices, valid, _ = view.gather_sequences(probe_rows, config["training"]["sequence_length"])
    numeric, categorical = view.features(indices)
    was_training = model.training
    model.eval()
    with torch_module.no_grad():
        logits_a, _ = forward_bare(
            model, numeric, categorical, valid, device, profile, precision, torch_module,
            site="flow_forward_bare_zero_gate_model",
        )
        logits_b, _ = forward_bare(
            reference, numeric, categorical, valid, device, profile, precision, torch_module,
            site="flow_forward_bare_zero_gate_reference",
        )
    if was_training:
        model.train()
    require(torch_module.equal(logits_a, logits_b), "z1=0 路径 logits 与新建裸模型不是逐位相等", EXIT_RUNTIME)
    LOGGER.info("零门退化断言通过：z1=0 路径与裸 FT 在 %d 个探测片段上 logits 逐位相等", len(probe_rows))


def assert_tail_aggregation_degeneracy(
    config: dict[str, Any], model: Any, view: Any, arrays: dict[str, Any], train_rows: Any,
    device: Any, profile: dict[str, Any], precision: Any, torch_module: Any, output_root: Path,
) -> None:
    """尾部聚合的 `k ≡ 1` 逐位自检，在真实数据的一小批上跑一次。

    与 ``assert_zero_gate_degeneracy`` 同一职责层：把「关掉机制就回到现状」从
    「代码没改因而必然如此」变成一条可机械核验的运行时收据。这里核验的是聚合算子
    本身——`α → 0` 极限（`k ≡ 1`）的 ``tail_scores`` 必须与 ``prefix_scores`` 的
    max 在同一批真实 logits 上 ``torch.equal`` 为真。不成立说明分组、排序或掩码有
    实现缺陷，四格 `z1=0` 臂的「等于现状」这句话随之失效，2×2 消融不可解释。

    只在尾部聚合开启时跑：关闭时聚合走的就是 ``prefix_scores`` 本身，没有可比对象。
    用真实片段而不是构造夹具，收据落 ``receipts/entity-tail-aggregation-self-check.json``。
    """
    if not entity_tail_aggregation_enabled_from_config(config):
        return

    import numpy as np

    import ch3_ft_entity_ranking_loss as ranking  # 延迟导入，模块顶层 import torch

    # 片段数取 8：与 assert_zero_gate_degeneracy 的 4 同量级。**不能取大**——本函数
    # 走的是不分微批的单次前向，2026-09-01 本机实测 256 个片段（32,768 条流）时
    # 逐字段注意力单次申请 6.89 GiB，直接 MPS OOM；训练路径之所以没事，是因为它按
    # micro_batch_sequences 分批。8 个片段约 1,024 条流，两端都安全。
    # 片段数小不影响自检强度：袋大小按**流**算，单个片段已可含 128 条流，
    # 下面的 max_bag_size >= 2 断言保证这一批不是「全是单流实体」的平凡情形。
    probe_rows = train_rows[: min(8, len(train_rows))]
    indices, valid, _ = view.gather_sequences(probe_rows, config["training"]["sequence_length"])
    numeric, categorical = view.features(indices)
    _unique, segment_owner_np = np.unique(arrays["E23"][probe_rows], return_inverse=True)
    segment_owner = torch_module.from_numpy(segment_owner_np.astype(np.int64)).to(device)
    was_training = model.training
    model.eval()
    with torch_module.no_grad():
        logits, valid_t = forward_bare(
            model, numeric, categorical, valid, device, profile, precision, torch_module,
            site="flow_forward_bare_tail_aggregation_self_check",
        )
    if was_training:
        model.train()
    with precision.fp32_island(logits, device_type=device.type, torch_module=torch_module) as (logits32,):
        receipt = ranking.assert_tail_aggregation_degenerates_to_max(logits32, valid_t, segment_owner)
    alpha = entity_tail_aggregation_alpha_from_config(config)
    _scores, k_per_entity, tail_receipt = ranking.tail_scores(logits32, valid_t, segment_owner, alpha)
    # 非平凡性：全是单流实体时 `k ≡ 1` 恒成立，自检退化成空断言，抓不到任何分组错位。
    # 这条不是新增的科学门，而是保证上面那条自检确实检查了东西。
    require(
        tail_receipt["max_bag_size"] >= 2.0,
        f"尾部聚合自检的探测批里最大袋只有 {tail_receipt['max_bag_size']} 条流，"
        "k≡1 断言平凡成立、检查不到分组错位；须增大 probe_rows",
        EXIT_RUNTIME,
    )
    receipt = {
        "schema_version": "ch3-ft-entity-tail-aggregation-self-check-v1",
        "alpha": alpha,
        "k_equals_one_versus_max": receipt,
        "frozen_alpha_receipt": tail_receipt,
        "probe_segment_count": int(len(probe_rows)),
        "target_reads": 0,
    }
    atomic_json(output_root / "receipts" / "entity-tail-aggregation-self-check.json", receipt)
    LOGGER.info(
        "尾部聚合自检通过：%d 个探测片段、%d 个实体上 k≡1 与 max 逐位相等；"
        "α=%s 的 inner_tail_frac=%r、mean_k=%r、k>1 实体数=%d",
        len(probe_rows), receipt["k_equals_one_versus_max"]["checked_entity_count"], alpha,
        tail_receipt["inner_tail_frac"], tail_receipt["mean_k"], tail_receipt["entities_with_k_gt_1"],
    )


def build_entity_memory_state(config: dict[str, Any], base_config: dict[str, Any], context: dict[str, Any], torch_module: Any, device: Any) -> Any:
    """按冻结的 ``slots`` 与骨干宽度构造全实体常驻的 ``EntityMemoryState``。"""
    import ch3_ft_causal_entity_memory as entity_memory  # 延迟导入，只在 z1=1 时需要 torch

    slots = config["mechanism"]["entity_memory"]["slots"]
    width = base_config["architecture"]["d_token"]
    role_of_entity = torch_module.from_numpy(context["role_of_entity"].astype("int64"))
    return entity_memory.EntityMemoryState(
        entity_count=context["entity_count"], slots=slots, width=width,
        device=device, role_of_entity=role_of_entity,
    )


# ---------------------------------------------------------------------------
# 机制二（预算感知实体排序，z2）宿主接线。
#
# 与机制一（z1）完全对称：统一读取入口 entity_ranking_enabled_from_config、
# mechanism.entity_ranking 配置段、z2=0 时下列函数全部不被调用（不构造采样器、
# 不计算排序损失）。三个独立模块（ch3_ft_entity_stratified_sampler、
# ch3_ft_entity_ranking_loss、ch3_ft_gradient_controller）本身不改动，只在此处
# 接线；引用的公开接口见各模块文档字符串与
# .Codex/docs/RWKV/2026-08-28-机制二实现报告.md。
# ---------------------------------------------------------------------------


def entity_ranking_enabled_from_config(config: dict[str, Any]) -> bool:
    """统一的 z2 读取入口，对称于 entity_memory_enabled_from_config。"""
    mechanism = config.get("mechanism", DEFAULT_MECHANISM)
    return bool(mechanism.get("entity_ranking", {}).get("enabled", False))


def prepare_entity_ranking_sampler(config: dict[str, Any], arrays: dict[str, Any], train_rows: Any) -> Any:
    """只在 z2=1 时被调用：构建实体分层采样器，限定在训练角色片段内。

    ``ch3_ft_entity_stratified_sampler.EntityStratifiedSampler`` 按其构造参数的
    行下标直接建立实体索引，不知道"训练/验证角色"这一概念；若直接传入全量
    E23/I23/M23/T23（如该模块自身诊断脚本 main() 的做法），正/负实体池会混入
    验证角色实体，构成训练-验证实体交叉污染。这里显式只切 ``train_rows`` 对应的
    片段行传入，``sample()`` 返回的 ``segment_rows`` 因此是相对于该切片的局部下标，
    调用方须用 ``train_rows[segment_rows]`` 换回全局片段行号（见 ``_ranking_phase``）。
    """
    import ch3_ft_entity_stratified_sampler as stratified  # 延迟导入，模块顶层 import numpy 但不 import torch

    ranking_cfg = config["mechanism"]["entity_ranking"]
    sampler_config = stratified.EntityStratifiedSamplerConfig(
        n_pos=ranking_cfg["n_pos"], n_neg=ranking_cfg["n_neg"], max_bag_flows=ranking_cfg["truncate_length"],
    )
    return stratified.EntityStratifiedSampler(
        entity_of_segment=arrays["E23"][train_rows],
        segment_flow_indices=arrays["I23"][train_rows],
        segment_valid_mask=arrays["M23"][train_rows],
        segment_timestamp=arrays["T23"][train_rows],
        flow_labels=arrays["y23"],
        config=sampler_config,
    )


def _cap_segments_per_entity_rows(sorted_rows: Any, entity_of_sorted_rows: Any, max_segments: int) -> Any:
    """按 (entity,T23) 升序输入的全局片段行数组，保留每实体因果最早 ``max_segments`` 段。

    ``ch3_ft_entity_ranking_loss.py``/``ch3_ft_gradient_controller.py`` 的诊断脚本
    main() 内各自独立实现了同名私有工具（用于避免诊断脚本吃到最大 2,475,228 条流
    的极端实体袋）；宿主接线面临同一问题的生产版本——``EntityStratifiedSampler``
    返回抽中实体的"完整"片段行清单，但完整袋对单步计算不可行（机制二实现报告
    第三节引用的实测：最大袋对单步 8,192 条流预算差 302 倍）。这里在宿主侧独立
    重复同一原理的实现（不依赖两个诊断脚本 main() 内的私有函数），把"编码哪些
    片段"这一步收敛到与 5.3.1 节生产 ``truncate_length`` 等价的规模，再交给
    ``bag_policy_diagnostics`` 内部的 ``_causal_truncate_valid`` 做逐流精确截断。
    """
    import numpy as np

    if sorted_rows.size == 0:
        return sorted_rows
    boundaries = np.flatnonzero(np.r_[True, entity_of_sorted_rows[1:] != entity_of_sorted_rows[:-1]])
    ends = np.r_[boundaries[1:], len(entity_of_sorted_rows)]
    parts = [sorted_rows[start : min(start + max_segments, end)] for start, end in zip(boundaries, ends)]
    return np.concatenate(parts) if parts else sorted_rows


def _shared_parameters(model: Any) -> list[Any]:
    """两个损失（逐流／排序）流经的共享参数清单，两阶段调用须用同一顺序。"""
    return [parameter for parameter in model.parameters() if parameter.requires_grad]


def _flat_grad_from_params(shared_params: list[Any], torch_module: Any) -> Any:
    """把当前 ``.grad``（若为 None 补零）展平拼接为一维 FP32 张量，不清空 ``.grad``。"""
    return torch_module.cat(
        [
            (parameter.grad.detach().clone() if parameter.grad is not None else torch_module.zeros_like(parameter)).reshape(-1)
            for parameter in shared_params
        ]
    ).to(torch_module.float32)


def _flow_phase_bare(
    config: dict[str, Any], model: Any, optimizer: Any, view: Any, train_rows: Any, generator: Any,
    device: Any, profile: dict[str, Any], precision: Any, torch_module: Any, positive_weight: Any,
) -> tuple[Any, dict[str, Any]]:
    """z2=1、z1=0（C01）的第一步：原有逐流批照常前向，得 L_flow 与 g_f。

    与既有 ``training_step`` 的采样、微批、损失计算逐字一致，唯一差异是不调用
    ``accumulator.finish()``（不在此处清空 ``.grad`` 或 ``optimizer.step()``）——
    调用方须在读出 ``g_flow`` 后自行合成梯度并更新，因此本函数独立实现而不是
    改造 ``training_step`` 本身：``training_step`` 是 z2=0 阻断条件的被保护对象，
    任何改造都有意外改变 z1=0/z2=0 既有路径的风险，重复少量代码换取零风险。
    """
    effective = config["training"]["effective_batch_size"]
    micro = config["training"]["micro_batch_sequences"]
    positions = base.sample_distinct_positions(len(train_rows), effective, generator)
    rows = train_rows[positions.numpy()]
    indices, valid, labels = view.gather_sequences(rows, config["training"]["sequence_length"])
    total_valid = int(valid.sum())
    loss_fn = torch_module.nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    accumulator = base.no_clip_accumulator_class()(
        total_valid_units=total_valid, normalization_unit=base.NORMALIZATION_UNIT,
        torch_module=torch_module, expected_microbatches=config["training"]["gradient_accumulation_steps"],
    )
    accumulator.begin(optimizer)
    loss_total = 0.0
    model.train()
    for start in range(0, effective, micro):
        stop = start + micro
        numeric, categorical = view.features(indices[start:stop])
        logits, valid_t = forward_bare(
            model, numeric, categorical, valid[start:stop], device, profile, precision, torch_module,
            site="flow_forward_bare_combined",
        )
        labels_t = torch_module.from_numpy(labels[start:stop]).to(device)
        mask32 = valid_t.to(torch_module.float32)
        with precision.fp32_island(logits, device_type=device.type, torch_module=torch_module) as (logits32,):
            loss_sum = (loss_fn(logits32, labels_t.to(torch_module.float32)) * mask32).sum()
        normalized = accumulator.backward(loss_sum, int(valid[start:stop].sum()), scaler=None)
        loss_total += float(normalized.detach().cpu())
    require(accumulator.consumed_valid_units == accumulator.total_valid_units, "逐流阶段未覆盖全部有效流", EXIT_RUNTIME)
    shared_params = _shared_parameters(model)
    g_flow = _flat_grad_from_params(shared_params, torch_module)
    require(bool(torch_module.isfinite(g_flow).all()), "逐流阶段梯度非有限", EXIT_RUNTIME)
    return g_flow, {"loss": loss_total, "valid_flows": total_valid, "sampled_sequences": effective}


def _flow_phase_entity_memory(
    config: dict[str, Any], model: Any, optimizer: Any, view: Any, scheduler: "EntityChainScheduler",
    memory_state: Any, interface: dict[str, Any], entity_of_row: Any, generator: Any, device: Any,
    profile: dict[str, Any], precision: Any, torch_module: Any, positive_weight: Any,
) -> tuple[Any, dict[str, Any]]:
    """z2=1、z1=1（C11）的第一步：与既有 ``entity_memory_training_step`` 逐字一致的
    实体链前向，唯一差异同样是不调用 ``accumulator.finish()``。理由与
    ``_flow_phase_bare`` 相同：``entity_memory_training_step`` 是 z1 零门核验保护
    的既有函数，不在此处改造。
    """
    import numpy as np

    effective = config["training"]["effective_batch_size"]
    micro = config["training"]["micro_batch_sequences"]
    rows, entity_ids_np = scheduler.sample_rows(effective, generator)
    assert_recovery_adjacency(rows, interface, entity_of_row)
    indices, valid, labels = view.gather_sequences(rows, config["training"]["sequence_length"])
    is_start_np = interface["is_entity_start"][rows]
    total_valid = int(valid.sum())
    loss_fn = torch_module.nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    accumulator = base.no_clip_accumulator_class()(
        total_valid_units=total_valid, normalization_unit=base.NORMALIZATION_UNIT,
        torch_module=torch_module, expected_microbatches=config["training"]["gradient_accumulation_steps"],
    )
    accumulator.begin(optimizer)
    loss_total = 0.0
    reset_count = 0
    recovery_count = 0
    model.train()
    for start in range(0, effective, micro):
        stop = start + micro
        micro_rows = rows[start:stop]
        micro_entity_ids = torch_module.from_numpy(entity_ids_np[start:stop].astype(np.int64)).to(device)
        micro_is_start = torch_module.from_numpy(is_start_np[start:stop]).to(device)
        micro_valid = valid[start:stop]
        if bool(micro_is_start.any()):
            memory_state.reset_entities(micro_entity_ids[micro_is_start])
            reset_count += int(micro_is_start.sum().item())
        recovery_count += int(micro_rows.shape[0]) - int(micro_is_start.sum().item())
        segment_memory = memory_state.read(micro_entity_ids)
        segment_valid = memory_state.valid(micro_entity_ids)
        numeric, categorical = view.features(indices[start:stop])
        numeric_t = torch_module.from_numpy(numeric).to(device)
        categorical_t = torch_module.from_numpy(categorical).to(device) if categorical is not None else None
        valid_t = torch_module.from_numpy(micro_valid).to(device)
        batch, length = micro_valid.shape
        flat_num = numeric_t.reshape(batch * length, numeric_t.shape[-1])
        flat_cat = categorical_t.reshape(batch * length, categorical_t.shape[-1]) if categorical_t is not None else None
        execution_path.LEDGER.record("flow_forward_entity_memory_combined", model, checkpointed=False)
        with precision.autocast_context(profile, device.type, torch_module):
            broadcast_memory, broadcast_valid = _broadcast_segment_memory(segment_memory, segment_valid, batch, length)
            logits_flat, injected = model(flat_num, flat_cat, broadcast_memory, broadcast_valid)
            logits = logits_flat.reshape(batch, length)
        width = injected.shape[-1]
        summary = _segment_summary_from_injected(injected, micro_valid, batch, length, width, torch_module, device)
        memory_state.write(micro_entity_ids, summary)
        labels_t = torch_module.from_numpy(labels[start:stop]).to(device)
        mask32 = valid_t.to(torch_module.float32)
        with precision.fp32_island(logits, device_type=device.type, torch_module=torch_module) as (logits32,):
            loss_sum = (loss_fn(logits32, labels_t.to(torch_module.float32)) * mask32).sum()
        normalized = accumulator.backward(loss_sum, int(micro_valid.sum()), scaler=None)
        loss_total += float(normalized.detach().cpu())
    require(accumulator.consumed_valid_units == accumulator.total_valid_units, "逐流阶段未覆盖全部有效流", EXIT_RUNTIME)
    shared_params = _shared_parameters(model)
    g_flow = _flat_grad_from_params(shared_params, torch_module)
    require(bool(torch_module.isfinite(g_flow).all()), "逐流阶段梯度非有限", EXIT_RUNTIME)
    return g_flow, {
        "loss": loss_total, "valid_flows": total_valid, "sampled_sequences": effective,
        "state_reset_count": reset_count, "cross_segment_recovery_count": recovery_count,
        "gate": model.memory.gate_statistics(),
    }


def _entity_ranking_bare_forward(
    config: dict[str, Any], model: Any, view: Any, indices: Any, valid: Any, device: Any,
    profile: dict[str, Any], precision: Any, torch_module: Any,
) -> tuple[Any, Any]:
    """z1=0：实体排序批各片段互不依赖（裸 FT 无跨片段状态），可分微批并行前向。

    2026-08-29 修复 CUDA 显存溢出：原实现虽已按 micro 分批前向，但把每个微批的
    输出连同其完整反向图一起累积到 ``logits_parts``，激活内存随微批数线性增长。
    实体排序批规模由 ``n_pos + n_neg = 66`` 个实体乘每实体至多
    ``ceil(truncate_length / sequence_length) = 64`` 段决定，实测达 6403 个序列、
    即 100 个微批；三层注意力的中间激活合计需 30.97 GiB，在 31.36 GiB 可用的
    RTX 5090 上首步即溢出（C01 实测 ``torch.OutOfMemoryError``，申请 394 MiB 时
    仅余 389 MiB）。

    CVaR-pAUC 排序损失要求全体实体分数同时在同一张图中，无法像主任务那样分微批
    反传后累加梯度，因此改用梯度检查点：前向只保留各微批的输出张量，反向时按需
    重算该微批的中间激活。这是纯工程修复——机制超参数、损失定义、采样口径和
    数值语义全部不变，只是用重算换显存。

    ``use_reentrant=False`` 为显式指定：目标机 PyTorch 2.13.0+cu130 的
    ``torch.utils.checkpoint.checkpoint`` 签名中该参数默认 ``None`` 并会告警，
    非重入实现对本处的多输出与 autocast 组合支持更完整（签名已在目标机实测核验）。

    2026-08-31 统一执行路径：检查点内的纯模型段固定走原模块（即时执行），与
    ``_entity_ranking_memory_forward`` 完全一致。此前本函数传入的是编译包装体，
    目标机实测（``.Codex/docs/RWKV/2026-08-31-四格编译路径统一/notes.md`` 第三节）
    该组合会真实进入 Dynamo（``frames total=3 ok=3``、``unique_graphs=2``）并因
    等长微批加尾部残批的两种形状生成**动态形状核**（``aten.addmm_s77_192_192``），
    正是提交 ``0a47546`` 记录的「前向与重算 FFN 宽度元数据 255/256 不一致」的成因；
    而传原模块时 ``counters`` 全空，即 Dynamo 完全不介入。因此本改动同时满足恢复卡
    门禁第 2 条「C01 与 C11 的实体排序检查点统一即时执行」并消除该类硬失败。
    逐流骨干阶段不受影响，仍走编译路径。
    """
    from torch.utils.checkpoint import checkpoint

    micro = config["training"]["micro_batch_sequences"]
    logits_parts = []
    valid_parts = []
    checkpoint_model = getattr(model, "_orig_mod", model)
    execution_path.LEDGER.record("ranking_forward_bare", checkpoint_model, checkpointed=True)
    for start in range(0, indices.shape[0], micro):
        stop = start + micro
        numeric, categorical = view.features(indices[start:stop])
        micro_valid = valid[start:stop]
        # 张量转换必须留在检查点外：checkpoint 只能追踪张量入参，
        # 且 numpy → GPU 的搬运不需要被重算。
        numeric_t = torch_module.from_numpy(numeric).to(device)
        categorical_t = torch_module.from_numpy(categorical).to(device) if categorical is not None else None
        valid_t = torch_module.from_numpy(micro_valid).to(device)
        batch, length = micro_valid.shape
        flat_num = numeric_t.reshape(batch * length, numeric_t.shape[-1])
        flat_cat = categorical_t.reshape(batch * length, categorical_t.shape[-1]) if categorical_t is not None else None

        def _bare_segment_forward(num_input: Any, cat_input: Any) -> Any:
            """被检查点包裹的纯计算段：无状态写入，重算安全。"""
            with precision.autocast_context(profile, device.type, torch_module):
                return checkpoint_model(num_input, cat_input).reshape(batch, length)

        logits = checkpoint(_bare_segment_forward, flat_num, flat_cat, use_reentrant=False)
        logits_parts.append(logits)
        valid_parts.append(valid_t)
    return torch_module.cat(logits_parts, dim=0), torch_module.cat(valid_parts, dim=0)


def _entity_ranking_memory_forward(
    config: dict[str, Any], model: Any, view: Any, indices: Any, valid: Any, entity_rows: Any,
    is_start_np: Any, entity_of_row: Any, scratch_memory_state: Any, device: Any,
    profile: dict[str, Any], precision: Any, torch_module: Any,
) -> tuple[Any, Any]:
    """z1=1：实体排序批复用严格过去记忆交叉注意力，须按段顺序读写状态，不能整体并行。

    只使用宿主专用的 scratch 记忆状态（与训练角色链式调度器持有的持久
    ``memory_state`` 完全隔离的第二个 ``EntityMemoryState`` 实例），不写回持久
    ``memory_state``。理由：``EntityStratifiedSampler`` 抽出的实体袋（经
    ``_cap_segments_per_entity_rows`` 截断后）总是从该实体因果最早的片段开始
    （任务 1 docstring："按 (entity, T23) 升序排列"，截断只保留最早若干段），
    这是一次独立的"从头重放"；若直接读写训练角色的持久 ``memory_state``，当
    同一实体在同一优化步内也被机制一的链式调度器（``EntityChainScheduler``）
    抽中时，两条独立的遍历会相互覆盖对方推进的状态——链式调度器凭
    ``self.cursor``（与 ``memory_state`` 张量本身无关）决定"下次该实体从哪段
    继续"，但排序批的重放会把该实体状态直接写到"重放末段之后"，链式调度器下次
    按游标读到的会是"未来"状态，违反设计规约第 4.3 节的严格过去约束、也违反
    8.5 节"硬失败：任何未来信息"的判据。scratch 状态按 ``is_entity_start`` 在
    每次经过实体首段时自动重置（``EntityMemoryState.reset_entities`` 语义），
    故不需要在此额外清零；这是宿主接线新增的隔离设计，机制一、机制二两个模块
    本身均未涉及这一问题（各自独立正确，只是从未被设计成共享同一状态实例）。
    """
    import numpy as np
    from torch.utils.checkpoint import checkpoint

    micro = config["training"]["micro_batch_sequences"]
    logits_parts = []
    valid_parts = []
    # 服务器真实首步显示：变长 depth 微批在 checkpoint 反向重算时，torch.compile
    # 可能从静态图切换到动态图，导致前向/重算的 FFN 宽度元数据 255/256 不一致。
    # 常规 CEM 逐流阶段继续使用编译模型；这里只把需要重算的纯模型段固定到原模块。
    # 2026-08-31：``_entity_ranking_bare_forward`` 已作同样处理，两条排序路径统一即时执行。
    checkpoint_model = getattr(model, "_orig_mod", model)
    execution_path.LEDGER.record("ranking_forward_entity_memory", checkpoint_model, checkpointed=True)

    # 输入按 (entity, T23) 分组；若直接按连续行切微批，同一实体的多个片段会在一次
    # read 之后并行前向，既看不到前一片段刚写入的状态，也会触发 EntityMemoryState
    # 对重复实体写入的拒绝。改为按实体内片段深度交错：每一层每个实体最多出现一次，
    # 层 k 完成写入后才进入层 k+1。最终再恢复到原分组顺序供袋级损失消费。
    entity_ids_np = entity_of_row[entity_rows].astype(np.int64, copy=False)
    boundaries = np.flatnonzero(np.r_[True, entity_ids_np[1:] != entity_ids_np[:-1]])
    ends = np.r_[boundaries[1:], entity_ids_np.size]
    max_depth = int((ends - boundaries).max()) if boundaries.size else 0
    depth_orders = []
    for depth in range(max_depth):
        positions = boundaries + depth
        depth_orders.append(positions[positions < ends])
    execution_order = np.concatenate(depth_orders) if depth_orders else np.empty(0, dtype=np.int64)
    require(
        execution_order.size == entity_rows.size
        and np.array_equal(np.sort(execution_order), np.arange(entity_rows.size)),
        "实体排序记忆执行序未精确覆盖全部片段",
        EXIT_RUNTIME,
    )

    for depth_positions in depth_orders:
        # 不能跨深度层切微批；否则层边界处可能把同一实体的相邻片段放进同一批，
        # 两段会读取同一旧状态并触发重复实体写入拒绝。
        for start in range(0, depth_positions.shape[0], micro):
            stop = start + micro
            micro_positions = depth_positions[start:stop]
            micro_rows = entity_rows[micro_positions]
            micro_entity_ids = torch_module.from_numpy(entity_of_row[micro_rows].astype(np.int64)).to(device)
            micro_is_start = torch_module.from_numpy(is_start_np[micro_positions]).to(device)
            micro_valid = valid[micro_positions]
            if bool(micro_is_start.any()):
                scratch_memory_state.reset_entities(micro_entity_ids[micro_is_start])
            segment_memory = scratch_memory_state.read(micro_entity_ids)
            segment_valid = scratch_memory_state.valid(micro_entity_ids)
            numeric, categorical = view.features(indices[micro_positions])
            numeric_t = torch_module.from_numpy(numeric).to(device)
            categorical_t = torch_module.from_numpy(categorical).to(device) if categorical is not None else None
            valid_t = torch_module.from_numpy(micro_valid).to(device)
            batch, length = micro_valid.shape
            flat_num = numeric_t.reshape(batch * length, numeric_t.shape[-1])
            flat_cat = categorical_t.reshape(batch * length, categorical_t.shape[-1]) if categorical_t is not None else None

            def _memory_segment_forward(
                num_input: Any,
                cat_input: Any,
                seg_mem: Any,
                seg_valid: Any,
                batch_size: int = batch,
                sequence_length: int = length,
            ) -> Any:
                """被检查点包裹的纯计算段，状态读写均留在检查点之外。"""
                with precision.autocast_context(profile, device.type, torch_module):
                    broadcast_memory, broadcast_valid = _broadcast_segment_memory(
                        seg_mem, seg_valid, batch_size, sequence_length
                    )
                    logits_flat, injected_local = checkpoint_model(
                        num_input, cat_input, broadcast_memory, broadcast_valid
                    )
                    return logits_flat.reshape(batch_size, sequence_length), injected_local

            # 实体排序损失需要整批实体分数同时存在；检查点只重算纯模型段，状态推进一次。
            logits, injected = checkpoint(
                _memory_segment_forward, flat_num, flat_cat, segment_memory, segment_valid,
                use_reentrant=False,
            )
            width = injected.shape[-1]
            summary = _segment_summary_from_injected(
                injected, micro_valid, batch, length, width, torch_module, device
            )
            scratch_memory_state.write(micro_entity_ids, summary)
            logits_parts.append(logits)
            valid_parts.append(valid_t)
    execution_logits = torch_module.cat(logits_parts, dim=0)
    execution_valid = torch_module.cat(valid_parts, dim=0)
    restore_order = np.empty_like(execution_order)
    restore_order[execution_order] = np.arange(execution_order.size)
    restore_order_t = torch_module.from_numpy(restore_order).to(device)
    return (
        execution_logits.index_select(0, restore_order_t),
        execution_valid.index_select(0, restore_order_t),
    )


def _ranking_phase(
    config: dict[str, Any], model: Any, optimizer: Any, view: Any, arrays: dict[str, Any], train_rows: Any,
    np_rng: Any, device: Any, profile: dict[str, Any], precision: Any, torch_module: Any, sampler: Any,
    xi_state: Any, entity_memory_enabled: bool, interface: dict[str, Any] | None, entity_of_row: Any,
    scratch_memory_state: Any,
) -> tuple[Any, dict[str, Any]]:
    """z2=1 的第二步：抽实体批、编码、算 CVaR-pAUC 排序损失，反传得 g_r。

    对应实施计划任务 1 步骤 2 的第 2～3 条：「用 EntityStratifiedSampler 抽实体批，
    编码其片段，得实体前缀分数」「cvar_pauc_loss(...) 得 L_rank 与 CVaR 活动率
    诊断」。调用方须先 ``optimizer.zero_grad(set_to_none=True)``（这里不重复做，
    因为 C11 路径下第一阶段的 accumulator 已在其自身 begin() 里清过一次，本函数
    自己的 zero_grad 放在最前，覆盖两种调用场景）。
    """
    import numpy as np

    import ch3_ft_entity_ranking_loss as ranking  # 延迟导入，模块顶层 import torch

    optimizer.zero_grad(set_to_none=True)
    ranking_cfg = config["mechanism"]["entity_ranking"]
    length = config["training"]["sequence_length"]
    max_segments = -(-int(ranking_cfg["truncate_length"]) // int(length))  # ceil(truncate_length/sequence_length)

    batch = sampler.sample(np_rng)
    rows_all = train_rows[batch["segment_rows"]]
    entity_raw_all = arrays["E23"][rows_all]
    entity_rows = _cap_segments_per_entity_rows(rows_all, entity_raw_all, max_segments)
    indices, valid, _labels = view.gather_sequences(entity_rows, length)
    entity_raw = arrays["E23"][entity_rows]
    unique_entities, segment_owner_np = np.unique(entity_raw, return_inverse=True)
    segment_owner = torch_module.from_numpy(segment_owner_np.astype(np.int64)).to(device)
    entity_is_positive = torch_module.from_numpy(np.isin(unique_entities, batch["positive_entities"])).to(device)
    entity_chain_length = torch_module.from_numpy(sampler.flows_per_entity[unique_entities].astype(np.int64)).to(device)

    if entity_memory_enabled:
        is_start_np = interface["is_entity_start"][entity_rows]
        assert_recovery_adjacency(entity_rows, interface, entity_of_row)
        entity_logits, entity_valid_t = _entity_ranking_memory_forward(
            config, model, view, indices, valid, entity_rows, is_start_np, entity_of_row,
            scratch_memory_state, device, profile, precision, torch_module,
        )
    else:
        entity_logits, entity_valid_t = _entity_ranking_bare_forward(
            config, model, view, indices, valid, device, profile, precision, torch_module,
        )

    positive_entity_ids = unique_entities[entity_is_positive.detach().cpu().numpy()]
    require(positive_entity_ids.size > 0, "实体排序批不含任何正实体", EXIT_RUNTIME)
    eff_budgets = [
        ranking.effective_budget(int(k), sampler.negative_pool_size, ranking_cfg["n_neg"]) for k in xi_state.budgets
    ]
    # 2026-09-01 回退：跨步水库分位数修法已被预注册判据正式否决（见
    # .Codex/docs/RWKV/2026-09-01-BER水库分位数修法裁决.md）——第 15-20 轮六档活动率
    # 均值对目标 β 的比值为 0/0/0/0.391/0.488/0.391，全部低于 0.5 下界，且源年最佳
    # 实体 AP 0.9295 低于子梯度 SGD 实现的 0.9537；根因是批内采样规模而非估计方法，
    # 换估计器修不好。故 xi 改回子梯度 SGD 追踪：get() 取出持久表中的当前值（严格
    # 来自过去步 commit() 的写入，本步样本尚未参与），作为 requires_grad=True 的叶
    # 张量参与 cvar_pauc_loss 的反传图，backward 后 xi.grad 即子梯度，见下方 commit()。
    # 水库实现（quantile()/observe()）保留在 CvarThresholdState 中不删——它是已执行
    # 筛选实验的证据，且旧检查点的 state_dict 仍可能引用其字段——只是本函数不再调用。
    xi = xi_state.get(positive_entity_ids).to(device)
    xi.retain_grad()

    with precision.fp32_island(entity_logits, device_type=device.type, torch_module=torch_module) as (entity_logits32,):
        bag_config = ranking.BagPolicyConfig(
            active_policy=ranking_cfg["bag_policy"],
            truncate_length=int(ranking_cfg["truncate_length"]),
            num_length_buckets=int(ranking_cfg["num_length_buckets"]),
            # 训练侧挂载点：α 非 None 时 S_e 改由 tail_scores 给出。袋上限仍只来自
            # 上面的 truncate_length，尾部聚合不另立截断。
            alpha=entity_tail_aggregation_alpha_from_config(config),
        )
        bag_result = ranking.bag_policy_diagnostics(
            entity_logits32, entity_valid_t, segment_owner, entity_is_positive,
            entity_chain_length, eff_budgets, xi, bag_config,
        )
        loss_rank = bag_result["loss"]
    # 观测量 nonargmax_grad_share 必须在 loss_rank.backward() **之前**取：backward()
    # 会释放计算图，之后再对 entity_scores 求梯度会报「图已释放」。这里只对实体分数
    # （长度 E 的向量）反传一次，不穿实体前向，代价与 pairwise 同量级。
    tail_observables: dict[str, Any] = {"nonargmax_grad_share": None}
    if bag_config.alpha is not None:
        grad_entity_scores = torch_module.autograd.grad(
            loss_rank, bag_result["active_entity_scores"], retain_graph=True
        )[0]
        tail_observables["nonargmax_grad_share"] = ranking.nonargmax_grad_energy_share(
            grad_entity_scores, bag_result["active_k_per_entity"]
        )
    loss_rank.backward()

    require(xi.grad is not None, "xi 未接收到梯度，检查是否进入了 cvar_pauc_loss 的反传图", EXIT_RUNTIME)
    xi_updated = (xi.detach() - float(ranking_cfg["xi_learning_rate"]) * xi.grad).cpu()
    xi_state.commit(positive_entity_ids, xi_updated)

    shared_params = _shared_parameters(model)
    g_rank = _flat_grad_from_params(shared_params, torch_module)
    require(bool(torch_module.isfinite(g_rank).all()), "排序阶段梯度非有限", EXIT_RUNTIME)

    diagnostics = {
        "batch_composition": sampler.batch_composition_receipt(batch),
        "capped_segment_count": int(entity_rows.shape[0]),
        "active_policy": bag_config.active_policy,
        "bag_policy_loss_values": {
            name: info["loss_value"] for name, info in bag_result["policies"].items()
        },
        "per_budget_active_rate": {
            name: info.get("per_budget_active_rate") for name, info in bag_result["policies"].items()
        },
        "per_budget_subunit": bag_result["policies"][bag_config.active_policy].get("per_budget_subunit"),
        "effective_budgets": eff_budgets,
        "sampled_negative_count": int(ranking_cfg["n_neg"]),
        # 2026-09-01 回退：xi_reservoir 诊断键已随水库估计器一并移除——本函数不再
        # 调用 observe()，水库永远空载，继续上报会是误导性的常零收据。水库实现本身
        # 仍保留在 CvarThresholdState 中（reservoir_diagnostics() 未删），只是不再
        # 被本函数调用。
        # 调研报告 2.4 节四个可证伪观测量的**逐步**来源，全部是标量：
        # pairwise_loss_mean 供轮内算 pair_loss_batch_var（观测量三）；
        # nonargmax_grad_share 是观测量一；entity_tail_aggregation.inner_tail_frac
        # 是观测量四；观测量二 per_budget_active_rate 已在上面。
        "pairwise_loss_mean": float(
            bag_result["policies"][bag_config.active_policy]["pairwise_loss_mean"]
        ),
        "nonargmax_grad_share": tail_observables["nonargmax_grad_share"],
        "entity_tail_aggregation": bag_result["policies"][bag_config.active_policy].get(
            "entity_tail_aggregation"
        ),
    }
    return g_rank, diagnostics


def summarize_falsifiable_observables(step_diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    """把一轮内逐步的排序诊断压成调研报告 2.4 节的四个可证伪观测量（全部标量）。

    | 观测量 | 本函数给出的口径 | 证伪判读 |
    | --- | --- | --- |
    | `nonargmax_grad_share` | 轮均值 | C11 中 ≈0 ⇒ 密度化通道（2.3-2）不成立 |
    | `per_budget_active_rate` | 逐档轮均值（现有诊断的轮内累计版本） | C11 低三档相对 C01 无回升 ⇒ 耦合主预测失败 |
    | `pair_loss_batch_var` | 轮内各步 `L_pn` 批均值的方差（总体方差，分母 n） | C11 不低于 C01 ⇒ 稳定性通道（2.3-3）不成立 |
    | `inner_tail_frac` | 轮均值 | 口径核对，防实现错位；不与 α 直接比大小（小袋结构性抬高它） |

    四项都不依赖尾部聚合是否开启：`z1'=0` 的臂里 `nonargmax_grad_share` 与
    `inner_tail_frac` 为 ``None``，另两项照常给出，C01 与 C11 因此可以逐项对比。
    输入是逐步诊断字典列表，输出只有标量与逐档标量字典，不含任何逐实体或逐流数组。
    """
    import numpy as np

    if not step_diagnostics:
        return {
            "step_count": 0,
            "nonargmax_grad_share_epoch_mean": None,
            "per_budget_active_rate_epoch_mean": None,
            "pair_loss_batch_var": None,
            "inner_tail_frac_epoch_mean": None,
        }

    def _mean(values: list[float]) -> float | None:
        return float(np.mean(values)) if values else None

    shares = [
        float(entry["nonargmax_grad_share"])
        for entry in step_diagnostics
        if entry.get("nonargmax_grad_share") is not None
    ]
    tail_fractions = [
        float(entry["entity_tail_aggregation"]["inner_tail_frac"])
        for entry in step_diagnostics
        if entry.get("entity_tail_aggregation")
        and entry["entity_tail_aggregation"].get("inner_tail_frac") is not None
    ]
    pair_means = [
        float(entry["pairwise_loss_mean"])
        for entry in step_diagnostics
        if entry.get("pairwise_loss_mean") is not None
    ]
    # 逐档活动率：取生效袋处置那一份，键是预算档的字符串形式。
    active_policy = step_diagnostics[-1].get("active_policy")
    per_budget: dict[str, list[float]] = {}
    for entry in step_diagnostics:
        rates = (entry.get("per_budget_active_rate") or {}).get(active_policy) or {}
        for budget_key, value in rates.items():
            per_budget.setdefault(budget_key, []).append(float(value))
    return {
        "step_count": len(step_diagnostics),
        "active_policy": active_policy,
        "nonargmax_grad_share_epoch_mean": _mean(shares),
        "nonargmax_grad_share_step_count": len(shares),
        "per_budget_active_rate_epoch_mean": {
            key: float(np.mean(values)) for key, values in sorted(per_budget.items())
        },
        # 总体方差（分母 n）：这是「这一轮里 L_pn 批均值抖得多厉害」的直接读数，
        # 不是对某个总体方差的无偏估计，故不用 ddof=1。
        "pair_loss_batch_var": float(np.var(pair_means)) if pair_means else None,
        "pair_loss_batch_mean": _mean(pair_means),
        "inner_tail_frac_epoch_mean": _mean(tail_fractions),
    }


def _combine_and_step(model: Any, optimizer: Any, g_flow: Any, g_rank: Any, torch_module: Any) -> dict[str, Any]:
    """把 g_f、g_r 交给梯度控制器合成，机械核验一阶不变量，写回 ``.grad`` 并
    ``optimizer.step()``。对应实施计划任务 1 步骤 2 的第 4～5 条。
    """
    import ch3_ft_gradient_controller as controller  # 延迟导入，模块顶层 import torch

    combined, diagnostics = controller.combine_gradients(g_flow, g_rank)
    require(bool(torch_module.isfinite(combined).all()), "合成梯度非有限", EXIT_RUNTIME)
    invariants = controller.verify_first_order_invariants(combined, g_flow, diagnostics)
    require(invariants["both_hold"], "梯度控制器一阶不变量在真实梯度上不成立", EXIT_RUNTIME)

    shared_params = _shared_parameters(model)
    optimizer.zero_grad(set_to_none=True)
    offset = 0
    with torch_module.no_grad():
        for parameter in shared_params:
            count = parameter.numel()
            parameter.grad = combined[offset : offset + count].reshape(parameter.shape).to(parameter.dtype).clone()
            offset += count
    optimizer.step()
    return {**diagnostics, "invariants": invariants}


def entity_ranking_training_step(
    config: dict[str, Any], model: Any, optimizer: Any, view: Any, arrays: dict[str, Any], train_rows: Any,
    generator: Any, np_rng: Any, device: Any, profile: dict[str, Any], precision: Any, torch_module: Any,
    positive_weight: Any, sampler: Any, xi_state: Any,
) -> dict[str, Any]:
    """C01（z1=0,z2=1）训练步：裸 FT 逐流批 + 独立实体排序批，梯度控制器合成后一次更新。"""
    g_flow, flow_diag = _flow_phase_bare(
        config, model, optimizer, view, train_rows, generator, device, profile, precision, torch_module, positive_weight,
    )
    g_rank, rank_diag = _ranking_phase(
        config, model, optimizer, view, arrays, train_rows, np_rng, device, profile, precision, torch_module,
        sampler, xi_state, entity_memory_enabled=False, interface=None, entity_of_row=None, scratch_memory_state=None,
    )
    combine_diag = _combine_and_step(model, optimizer, g_flow, g_rank, torch_module)
    return {**flow_diag, "entity_ranking": {**rank_diag, "gradient_control": combine_diag}}


def combined_mechanism_training_step(
    config: dict[str, Any], model: Any, optimizer: Any, view: Any, arrays: dict[str, Any], train_rows: Any,
    scheduler: "EntityChainScheduler", memory_state: Any, interface: dict[str, Any], entity_of_row: Any,
    generator: Any, np_rng: Any, device: Any, profile: dict[str, Any], precision: Any, torch_module: Any,
    positive_weight: Any, sampler: Any, xi_state: Any, scratch_memory_state: Any,
) -> dict[str, Any]:
    """C11（z1=1,z2=1）训练步：机制一实体链流批 + 机制二独立实体排序批（用 scratch
    记忆状态，见 ``_entity_ranking_memory_forward`` 文档字符串），梯度控制器合成后
    一次更新。排序分数当前不复用机制一链式调度器正在推进的持久状态——这是宿主
    接线阶段的简化版联合（对称遵循实施计划任务 1 的字面五步伪代码，未实现设计
    规约第六节"同一 M_(t-1) 同时产生流表示与排序分数"的完全共享状态联合算法，
    后者留待源年前缀分数曲线裁决袋处置方案后再设计，见任务 1 报告遗留风险）。
    """
    g_flow, flow_diag = _flow_phase_entity_memory(
        config, model, optimizer, view, scheduler, memory_state, interface, entity_of_row,
        generator, device, profile, precision, torch_module, positive_weight,
    )
    g_rank, rank_diag = _ranking_phase(
        config, model, optimizer, view, arrays, train_rows, np_rng, device, profile, precision, torch_module,
        sampler, xi_state, entity_memory_enabled=True, interface=interface, entity_of_row=entity_of_row,
        scratch_memory_state=scratch_memory_state,
    )
    combine_diag = _combine_and_step(model, optimizer, g_flow, g_rank, torch_module)
    return {**flow_diag, "entity_ranking": {**rank_diag, "gradient_control": combine_diag}}


def initialize_run(config: dict[str, Any], config_path: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    science = science_projection(config)
    runtime = runtime_projection(config)
    science_receipt = {"projection": science, "science_identity_sha256": canonical_sha256(science)}
    runtime_receipt = {"projection": runtime, "runtime_identity_sha256": canonical_sha256(runtime)}
    atomic_json(output_root / "config.json", config)
    atomic_json(output_root / "science-identity.json", science_receipt)
    atomic_json(output_root / "runtime-identity.json", runtime_receipt)
    atomic_json(output_root / "status.json", {
        "run_id": config["identity"]["run_id"], "state": "prepared", "stage": "identity",
        "exit_code": None, "target_reads": 0,
    })
    return output_root, science_receipt, runtime_receipt


def environment_receipt(config: dict[str, Any], torch_module: Any, device: Any, profile: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import sklearn

    receipt = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "torch": torch_module.__version__,
        "device_type": device.type,
        "precision_profile_id": config["runtime"]["precision_profile_id"],
        "profile": profile,
        "process_peak_rss_bytes": process_peak_rss_bytes(),
    }
    receipt.update(accelerator_memory(torch_module, device))
    return receipt


def probe_runtime(config: dict[str, Any], config_path: Path) -> None:
    import numpy as np

    output_root, science_receipt, runtime_receipt = initialize_run(config, config_path)
    execution_path.LEDGER.reset()
    LOGGER.info("启动真实运行校准：run_id=%s", config["identity"]["run_id"])
    atomic_json(output_root / "status.json", {
        "run_id": config["identity"]["run_id"], "state": "running", "stage": "probe-runtime",
        "exit_code": None, "target_reads": 0,
    })
    torch_module, device, profile, precision = resolve_runtime(config)
    base_config = effective_base_config(config)
    arrays, train_rows, validation_rows, view = prepare_data(config, base_config, output_root)
    # M-E 的箱边界与状态归一化尺度只能由训练区拟合，且必须在建模前就绪，
    # 因此上下文准备排在 build_model_optimizer 之前；未启用时恒为 None。
    entity_gated_ple_enabled = entity_gated_ple_enabled_from_config(config)
    entity_gated_ple_context = (
        prepare_entity_gated_ple_context(config, arrays, train_rows, view, output_root)
        if entity_gated_ple_enabled
        else None
    )
    model, optimizer, optimizer_receipt = build_model_optimizer(
        config, base_config, view, torch_module, device, entity_gated_ple_context
    )
    entity_memory_enabled = entity_memory_enabled_from_config(config)
    entity_memory_context = None
    memory_state = None
    if entity_memory_enabled:
        entity_memory_context = prepare_entity_memory_context(config, arrays, train_rows, validation_rows, output_root)
        memory_state = build_entity_memory_state(config, base_config, entity_memory_context, torch_module, device)
    entity_ranking_enabled = entity_ranking_enabled_from_config(config)
    sampler = None
    xi_state = None
    scratch_memory_state = None
    if entity_ranking_enabled:
        import ch3_ft_entity_ranking_loss as ranking  # 延迟导入，只在 z2=1 时需要 torch

        sampler = prepare_entity_ranking_sampler(config, arrays, train_rows)
        xi_state = ranking.CvarThresholdState(
            budgets=config["mechanism"]["entity_ranking"]["budgets"],
            reservoir_size=int(config["mechanism"]["entity_ranking"].get("reservoir_size", 4096)),
        )
        if entity_memory_enabled:
            scratch_memory_state = build_entity_memory_state(config, base_config, entity_memory_context, torch_module, device)
    require(
        entity_ranking_enabled or (sampler is None and xi_state is None and scratch_memory_state is None),
        "z2=0 时不得构造实体排序采样器或阈值状态", EXIT_RUNTIME,
    )
    assert_zero_gate_degeneracy(
        config, base_config, model, memory_state, view, train_rows, device, profile, precision, torch_module
    )
    assert_tail_aggregation_degeneracy(
        config, model, view, arrays, train_rows, device, profile, precision, torch_module, output_root
    )
    random.seed(config["training"]["seed"])
    np.random.seed(config["training"]["seed"])
    torch_module.manual_seed(config["training"]["seed"])
    if device.type == "cuda":
        torch_module.cuda.manual_seed_all(config["training"]["seed"])
        torch_module.cuda.reset_peak_memory_stats(device)
    generator = torch_module.Generator().manual_seed(config["training"]["seed"])
    entity_ranking_rng = np.random.default_rng(config["training"]["seed"])
    training_flow_mask = build_training_flow_mask(
        arrays, train_rows, config["training"]["sequence_length"]
    )
    train_positive_rate = float(np.asarray(arrays["y23"])[training_flow_mask].mean())
    positive_weight = torch_module.tensor(
        [(1.0 - train_positive_rate) / max(train_positive_rate, 1e-12)],
        dtype=torch_module.float32,
        device=device,
    )
    synchronize_device(torch_module, device)
    step_started = time.time()
    if entity_memory_enabled and entity_ranking_enabled:
        step = combined_mechanism_training_step(
            config, model, optimizer, view, arrays, train_rows, entity_memory_context["train_scheduler"],
            memory_state, entity_memory_context["interface"], entity_memory_context["entity_of_row"],
            generator, entity_ranking_rng, device, profile, precision, torch_module, positive_weight,
            sampler, xi_state, scratch_memory_state,
        )
    elif entity_memory_enabled:
        step = entity_memory_training_step(
            config, base_config, model, optimizer, view, entity_memory_context["train_scheduler"],
            memory_state, entity_memory_context["interface"], entity_memory_context["entity_of_row"],
            generator, device, profile, precision, torch_module, positive_weight,
        )
    elif entity_ranking_enabled:
        step = entity_ranking_training_step(
            config, model, optimizer, view, arrays, train_rows, generator, entity_ranking_rng,
            device, profile, precision, torch_module, positive_weight, sampler, xi_state,
        )
    else:
        step = training_step(
            config, base_config, model, optimizer, view, train_rows, generator, device,
            profile, precision, torch_module, positive_weight,
            mechanism_context=entity_gated_ple_context,
        )
    synchronize_device(torch_module, device)
    step_seconds = time.time() - step_started
    if entity_memory_enabled:
        validation = entity_memory_validation_metrics(
            config, model, view, arrays, entity_memory_context["validation_scheduler"], memory_state,
            entity_memory_context["interface"], entity_memory_context["entity_of_row"],
            device, profile, precision, torch_module,
        )
    else:
        validation = validation_metrics(
            config, model, view, arrays, validation_rows, device, profile, precision, torch_module,
            mechanism_context=entity_gated_ple_context,
        )
    full_budget = {
        "epochs": 20,
        "steps_per_epoch": 1000,
        "estimated_training_seconds": 20 * 1000 * step_seconds,
        "estimated_validation_seconds": 20 * validation["seconds"],
        "estimated_total_seconds": 20 * 1000 * step_seconds + 20 * validation["seconds"],
    }
    receipt = {
        "schema_version": "ch3-ft-c00-runtime-probe-v1",
        "run_id": config["identity"]["run_id"],
        "science_identity_sha256": science_receipt["science_identity_sha256"],
        "runtime_identity_sha256": runtime_receipt["runtime_identity_sha256"],
        "optimizer": optimizer_receipt,
        "train_positive_rate": train_positive_rate,
        "one_optimizer_step": {**step, "seconds": step_seconds},
        "full_validation": validation,
        "formal_budget_projection": full_budget,
        "resource": {
            "process_peak_rss_bytes": process_peak_rss_bytes(),
            **accelerator_memory(torch_module, device),
        },
        "target_reads": 0,
        "screening_result": False,
    }
    atomic_json(output_root / "environment-receipt.json", environment_receipt(config, torch_module, device, profile))
    atomic_json(output_root / "budget-receipt.json", receipt)
    execution_path.write_execution_path_receipt(
        output_root, config, stage="probe-runtime", project_root=str(PROJECT_ROOT),
        atomic_json=atomic_json, logger=LOGGER,
        extra={"one_optimizer_step_seconds": step_seconds, "full_validation_seconds": validation["seconds"]},
    )
    atomic_json(output_root / "status.json", {
        "run_id": config["identity"]["run_id"], "state": "finished", "stage": "probe-runtime",
        "exit_code": 0, "target_reads": 0,
    })
    print(json.dumps({
        "run_id": config["identity"]["run_id"],
        "step_seconds": step_seconds,
        "validation_seconds": validation["seconds"],
        "validation_flow_ap": validation["validation_flow_ap"],
        "validation_entity_ap": validation["validation_entity_ap"],
        "estimated_formal_hours": full_budget["estimated_total_seconds"] / 3600.0,
    }, ensure_ascii=False), flush=True)


def restore_mechanism_state(
    checkpoint: dict[str, Any], train_scheduler: Any, memory_state: Any, xi_state: Any,
    numpy_rng: Any, *, entity_memory_enabled: bool, entity_ranking_enabled: bool,
) -> None:
    """恢复机制侧状态；开关不一致或缺状态即拒绝，不静默按初值继续。

    拒绝而非降级的理由：若带 `z1` 的检查点在 `z1=0` 的运行里被加载，或反之，恢复出的
    训练轨迹与任一完整运行都不对应，产出的读数无法解释。这属于「原子断点恢复不能成立」，
    是根 AGENTS.md 允许阻断实验的硬门之一。
    """
    mechanism = checkpoint.get("mechanism_state")
    require(isinstance(mechanism, dict), "在途检查点缺 mechanism_state，无法安全续训", EXIT_INPUT)
    require(
        bool(mechanism["entity_memory_enabled"]) == entity_memory_enabled
        and bool(mechanism["entity_ranking_enabled"]) == entity_ranking_enabled,
        "在途检查点的机制开关与当前配置不一致，拒绝恢复",
        EXIT_INPUT,
    )
    if train_scheduler is not None and mechanism.get("train_scheduler") is not None:
        train_scheduler.load_state_dict(mechanism["train_scheduler"])
    if entity_memory_enabled:
        require(mechanism.get("entity_memory") is not None, "z1 检查点缺实体记忆状态", EXIT_INPUT)
        memory_state.load_state_dict(mechanism["entity_memory"])
    if entity_ranking_enabled:
        require(mechanism.get("cvar_threshold") is not None, "z2 检查点缺 CVaR 阈值状态", EXIT_INPUT)
        xi_state.load_state_dict(mechanism["cvar_threshold"])
        require(mechanism.get("numpy_rng_state") is not None, "z2 检查点缺采样 RNG 状态", EXIT_INPUT)
        numpy_rng.bit_generator.state = mechanism["numpy_rng_state"]
    LOGGER.info(
        "机制状态已恢复：z1=%s z2=%s 调度器游标=%s",
        entity_memory_enabled, entity_ranking_enabled,
        "已还原" if mechanism.get("train_scheduler") is not None else "无",
    )


def checkpoint_payload(
    config: dict[str, Any], science_receipt: dict[str, Any], runtime_receipt: dict[str, Any],
    model: Any, optimizer: Any, epoch: int, step_count: int, history: list[dict[str, Any]],
    best_flow: dict[str, Any], best_entity: dict[str, Any], generator: Any,
    torch_module: Any, device: Any, profile: dict[str, Any], input_transform_state_hash: str,
    train_scheduler: Any = None, memory_state: Any = None, xi_state: Any = None,
    numpy_rng: Any = None, best_entity_tail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构造检查点载荷。

    机制状态（2026-08-28 补齐）：`z1` 臂的实体链调度器游标与 ``EntityMemoryState``、
    `z2` 臂的 CVaR 阈值状态与 numpy 采样 RNG 一并入盘，使带机制的臂可原子续训。
    未启用对应机制时相应键为 ``None``，恢复端据此校验开关一致性。

    ``EntityMemoryState.state_dict`` 已是稀疏导出（只含 ``count > 0`` 的已激活实体），
    全量 150,680 实体 × R=8 × d=192 × 4B ≈ 0.93 GB，稀疏后随训练进度增长而远小于该上界。

    ``best_entity_tail``（2026-09-01 双聚合选轮改造新增）：α=0.5 top-k 口径独立追踪
    的最佳轮状态，与 ``best_flow``/``best_entity`` 同构地随每轮进度入盘，使 C10
    （乃至任何 z1'=0 的训练轨迹）在断点续训后仍能正确恢复它自己的选轮进度。
    CEM 分支（``entity_memory_enabled``）不追踪该口径，调用方传 ``None``。
    """
    mechanism_state: dict[str, Any] = {
        "entity_memory_enabled": memory_state is not None,
        "entity_ranking_enabled": xi_state is not None,
        "train_scheduler": train_scheduler.state_dict() if train_scheduler is not None else None,
        "entity_memory": memory_state.state_dict() if memory_state is not None else None,
        "cvar_threshold": xi_state.state_dict() if xi_state is not None else None,
        "numpy_rng_state": numpy_rng.bit_generator.state if numpy_rng is not None else None,
    }
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "mechanism_state": mechanism_state,
        "science_identity": science_receipt,
        "runtime_identity": runtime_receipt,
        "run_id": config["identity"]["run_id"],
        "run_tier": config["identity"]["run_tier"],
        "device_type": device.type,
        "precision_profile_id": config["runtime"]["precision_profile_id"],
        "profile": profile,
        "model_state_dict": {name: value.detach().cpu().clone() for name, value in model.state_dict().items()},
        "optimizer_state_dict": optimizer.state_dict(),
        "scaler_state_dict": None,
        "epoch": epoch,
        "optimizer_step": step_count,
        "history": history,
        "best_by_flow": best_flow,
        "best_by_entity": best_entity,
        "best_by_entity_tail": best_entity_tail,
        "input_transform_state_hash": input_transform_state_hash,
        "effective_batch_size": config["training"]["effective_batch_size"],
        "micro_batch_sequences": config["training"]["micro_batch_sequences"],
        "gradient_accumulation_steps": config["training"]["gradient_accumulation_steps"],
        "normalization_unit": config["training"]["normalization_unit"],
        "optimizer_step_boundary": True,
        "rng_state": {**capture_rng(torch_module, device), "sampler_state": generator.get_state()},
        "resume_scope": "same_run_same_profile_only",
        "formal_resume_eligible": config["checkpoint"]["formal_resume_eligible"],
    }


def run_training(config: dict[str, Any], config_path: Path, resume: bool) -> None:
    import numpy as np

    require(config["budget"]["state"] == "frozen", "筛选预算尚未冻结，只允许 probe-runtime", EXIT_CONFIG)
    output_root, science_receipt, runtime_receipt = initialize_run(config, config_path)
    # 执行路径台账按进程重置：断点续训会重新起进程，收据因此记录的是「本次进程段」的
    # 调用路径，而不是跨中断累积值。这与 Dynamo counters 的进程内累积语义一致。
    execution_path.LEDGER.reset()
    torch_module, device, profile, precision = resolve_runtime(config)
    base_config = effective_base_config(config)
    arrays, train_rows, validation_rows, view = prepare_data(config, base_config, output_root)
    # 与 probe_runtime 同序：M-E 上下文（训练区拟合的箱边界与状态尺度）先于建模就绪。
    # 该上下文由冻结数据、冻结切分与冻结种子确定性地重建，因此断点续训时重算即可，
    # 不需要入检查点；模型侧的 bin_edges 缓冲区随 model_state_dict 一起恢复。
    entity_gated_ple_enabled = entity_gated_ple_enabled_from_config(config)
    entity_gated_ple_context = (
        prepare_entity_gated_ple_context(config, arrays, train_rows, view, output_root)
        if entity_gated_ple_enabled
        else None
    )
    model, optimizer, optimizer_receipt = build_model_optimizer(
        config, base_config, view, torch_module, device, entity_gated_ple_context
    )
    entity_memory_enabled = entity_memory_enabled_from_config(config)
    entity_memory_context = None
    memory_state = None
    if entity_memory_enabled:
        # 2026-08-28：调度器游标与 EntityMemoryState 已纳入检查点（见 checkpoint_payload
        # 的 mechanism_state 与 restore_mechanism_state），z1=1 支持原子续训。
        entity_memory_context = prepare_entity_memory_context(config, arrays, train_rows, validation_rows, output_root)
        memory_state = build_entity_memory_state(config, base_config, entity_memory_context, torch_module, device)
    entity_ranking_enabled = entity_ranking_enabled_from_config(config)
    sampler = None
    xi_state = None
    scratch_memory_state = None
    if entity_ranking_enabled:
        # 2026-08-28：CvarThresholdState 与 numpy 采样 RNG 已纳入检查点；采样器本身无可变
        # 游标（正负实体轮转由传入的 numpy RNG 决定），还原 RNG 即还原抽样序列。
        import ch3_ft_entity_ranking_loss as ranking  # 延迟导入，只在 z2=1 时需要 torch

        sampler = prepare_entity_ranking_sampler(config, arrays, train_rows)
        xi_state = ranking.CvarThresholdState(
            budgets=config["mechanism"]["entity_ranking"]["budgets"],
            reservoir_size=int(config["mechanism"]["entity_ranking"].get("reservoir_size", 4096)),
        )
        if entity_memory_enabled:
            scratch_memory_state = build_entity_memory_state(config, base_config, entity_memory_context, torch_module, device)
    require(
        entity_ranking_enabled or (sampler is None and xi_state is None and scratch_memory_state is None),
        "z2=0 时不得构造实体排序采样器或阈值状态", EXIT_RUNTIME,
    )
    assert_zero_gate_degeneracy(
        config, base_config, model, memory_state, view, train_rows, device, profile, precision, torch_module
    )
    assert_tail_aggregation_degeneracy(
        config, model, view, arrays, train_rows, device, profile, precision, torch_module, output_root
    )
    random.seed(config["training"]["seed"])
    np.random.seed(config["training"]["seed"])
    torch_module.manual_seed(config["training"]["seed"])
    if device.type == "cuda":
        torch_module.cuda.manual_seed_all(config["training"]["seed"])
    generator = torch_module.Generator().manual_seed(config["training"]["seed"])
    entity_ranking_rng = np.random.default_rng(config["training"]["seed"])
    training_flow_mask = build_training_flow_mask(arrays, train_rows, config["training"]["sequence_length"])
    train_positive_rate = float(np.asarray(arrays["y23"])[training_flow_mask].mean())
    positive_weight = torch_module.tensor(
        [(1.0 - train_positive_rate) / max(train_positive_rate, 1e-12)],
        dtype=torch_module.float32, device=device,
    )
    inflight_path = output_root / "checkpoints" / "inflight.pt"
    history: list[dict[str, Any]] = []
    best_flow = {"metric": -1.0, "epoch": 0, "state": None}
    best_entity = {"metric": -1.0, "epoch": 0, "state": None}
    # α=0.5 top-k 口径独立追踪的最佳轮（2026-09-01 双聚合选轮改造）；CEM 分支
    # （entity_memory_enabled）不更新它，保持 -1.0/0/None 的哨兵值。
    best_entity_tail = {"metric": -1.0, "epoch": 0, "state": None}
    start_epoch = 1
    step_count = 0
    if resume and inflight_path.is_file():
        checkpoint = torch_module.load(inflight_path, map_location="cpu", weights_only=False)
        require(checkpoint["schema_version"] == CHECKPOINT_SCHEMA_VERSION, "在途检查点模式不符", EXIT_INPUT)
        require(checkpoint["science_identity"] == science_receipt, "在途科学身份漂移", EXIT_INPUT)
        require(checkpoint["runtime_identity"] == runtime_receipt, "在途运行身份漂移", EXIT_INPUT)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(device)
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        base._move_optimizer_state(optimizer, device)
        history = checkpoint["history"]
        best_flow = checkpoint["best_by_flow"]
        best_entity = checkpoint["best_by_entity"]
        # .get 而非下标：本改造之前落盘的在途检查点没有这个键，视为「尚无 tail 口径
        # 最佳轮记录」而不是一种应拒绝续训的漂移。
        best_entity_tail = checkpoint.get("best_by_entity_tail") or {
            "metric": -1.0, "epoch": 0, "state": None,
        }
        restore_rng(checkpoint["rng_state"], torch_module, device)
        generator.set_state(checkpoint["rng_state"]["sampler_state"])
        start_epoch = int(checkpoint["epoch"]) + 1
        step_count = int(checkpoint["optimizer_step"])
        restore_mechanism_state(
            checkpoint,
            entity_memory_context["train_scheduler"] if entity_memory_context is not None else None,
            memory_state if entity_memory_enabled else None,
            xi_state if entity_ranking_enabled else None,
            entity_ranking_rng,
            entity_memory_enabled=entity_memory_enabled,
            entity_ranking_enabled=entity_ranking_enabled,
        )
    atomic_json(output_root / "environment-receipt.json", environment_receipt(config, torch_module, device, profile))
    atomic_json(output_root / "status.json", {
        "run_id": config["identity"]["run_id"], "state": "running", "stage": "train",
        "exit_code": None, "target_reads": 0,
    })
    started = time.time()
    for epoch in range(start_epoch, config["budget"]["epochs"] + 1):
        losses = []
        steps_per_epoch = config["budget"]["steps_per_epoch"]
        heartbeat = max(1, steps_per_epoch // 4)
        epoch_started = time.time()
        epoch_reset_count = 0
        epoch_recovery_count = 0
        epoch_gate_means: list[float] = []
        epoch_ranking_diagnostics: list[dict[str, Any]] = []
        for step_in_epoch in range(1, steps_per_epoch + 1):
            if entity_memory_enabled and entity_ranking_enabled:
                result = combined_mechanism_training_step(
                    config, model, optimizer, view, arrays, train_rows, entity_memory_context["train_scheduler"],
                    memory_state, entity_memory_context["interface"], entity_memory_context["entity_of_row"],
                    generator, entity_ranking_rng, device, profile, precision, torch_module, positive_weight,
                    sampler, xi_state, scratch_memory_state,
                )
                epoch_reset_count += result["state_reset_count"]
                epoch_recovery_count += result["cross_segment_recovery_count"]
                epoch_gate_means.append(result["gate"]["gate_mean"])
                epoch_ranking_diagnostics.append(result["entity_ranking"])
            elif entity_memory_enabled:
                result = entity_memory_training_step(
                    config, base_config, model, optimizer, view, entity_memory_context["train_scheduler"],
                    memory_state, entity_memory_context["interface"], entity_memory_context["entity_of_row"],
                    generator, device, profile, precision, torch_module, positive_weight,
                )
                epoch_reset_count += result["state_reset_count"]
                epoch_recovery_count += result["cross_segment_recovery_count"]
                epoch_gate_means.append(result["gate"]["gate_mean"])
            elif entity_ranking_enabled:
                result = entity_ranking_training_step(
                    config, model, optimizer, view, arrays, train_rows, generator, entity_ranking_rng,
                    device, profile, precision, torch_module, positive_weight, sampler, xi_state,
                )
                epoch_ranking_diagnostics.append(result["entity_ranking"])
            else:
                result = training_step(
                    config, base_config, model, optimizer, view, train_rows, generator, device,
                    profile, precision, torch_module, positive_weight,
                    mechanism_context=entity_gated_ple_context,
                )
            losses.append(result["loss"])
            step_count += 1
            if step_in_epoch % heartbeat == 0 or step_in_epoch == steps_per_epoch:
                elapsed = time.time() - epoch_started
                throughput = step_in_epoch / max(elapsed, 1e-9)
                remaining = (steps_per_epoch - step_in_epoch) / max(throughput, 1e-9)
                LOGGER.info(
                    "训练进度 epoch=%d/%d step=%d/%d，%.3f步/秒，预计本轮训练剩余=%.1f秒",
                    epoch, config["budget"]["epochs"], step_in_epoch, steps_per_epoch,
                    throughput, remaining,
                )
        if entity_memory_enabled:
            metrics = entity_memory_validation_metrics(
                config, model, view, arrays, entity_memory_context["validation_scheduler"], memory_state,
                entity_memory_context["interface"], entity_memory_context["entity_of_row"],
                device, profile, precision, torch_module,
            )
            atomic_json(output_root / "receipts" / f"mechanism-diagnostics-{epoch}.json", {
                "schema_version": "ch3-ft-c10-mechanism-diagnostics-receipt-v1",
                "epoch": epoch,
                "target_reads": 0,
                "training": {
                    "state_reset_count": epoch_reset_count,
                    "cross_segment_recovery_count": epoch_recovery_count,
                    "gate_mean": float(np.mean(epoch_gate_means)) if epoch_gate_means else None,
                },
                "validation": metrics["mechanism_diagnostics"],
            })
        else:
            metrics = validation_metrics(
                config, model, view, arrays, validation_rows, device, profile, precision, torch_module,
                mechanism_context=entity_gated_ple_context,
            )
        if entity_ranking_enabled:
            # 对应实施计划任务 1 步骤 4：批构成、CVaR 活动率、梯度范数/夹角/投影触发率/
            # 上限触发率、三种袋处置的并行数值。每轮落盘一次，取本轮全部步的中位数与
            # 末步快照，避免每步逐条写盘。
            # _combine_and_step 返回 {**combine_gradients 的诊断字典（扁平）, "invariants": {...}}，
            # 键直接是 grad_norm_flow/grad_norm_rank/c_scaling/projection_triggered 等，无嵌套。
            gradient_controls = [entry["gradient_control"] for entry in epoch_ranking_diagnostics]
            c_values = [float(g["c_scaling"]) for g in gradient_controls]
            grad_norm_flow_values = [float(g["grad_norm_flow"]) for g in gradient_controls]
            grad_norm_rank_values = [float(g["grad_norm_rank"]) for g in gradient_controls]
            projection_triggered_count = sum(1 for g in gradient_controls if bool(g["projection_triggered"]))
            atomic_json(output_root / "receipts" / f"entity-ranking-diagnostics-{epoch}.json", {
                "schema_version": "ch3-ft-c01-entity-ranking-diagnostics-receipt-v1",
                "epoch": epoch,
                "target_reads": 0,
                "step_count": len(epoch_ranking_diagnostics),
                "falsifiable_observables": summarize_falsifiable_observables(epoch_ranking_diagnostics),
                "gradient_control": {
                    "c_scaling_median": float(np.median(c_values)) if c_values else None,
                    "c_equal_one_step_count": int(sum(1 for c in c_values if c >= 1.0 - 1e-9)),
                    "grad_norm_flow_median": float(np.median(grad_norm_flow_values)) if grad_norm_flow_values else None,
                    "grad_norm_rank_median": float(np.median(grad_norm_rank_values)) if grad_norm_rank_values else None,
                    "projection_triggered_step_count": projection_triggered_count,
                },
                "last_step_snapshot": epoch_ranking_diagnostics[-1] if epoch_ranking_diagnostics else None,
            })
        # entity_memory_enabled 分支（CEM）走 entity_memory_validation_metrics，不产出
        # validation_entity_ap_tail；用 .get 而不是下标，使该分支的收据形状保持完全
        # 不变（不新增字段、不因缺键抛 KeyError）。
        entity_ap_tail = metrics.get("validation_entity_ap_tail")
        entry = {
            "epoch": epoch,
            "mean_training_loss": float(np.mean(losses)),
            "validation_flow_ap": metrics["validation_flow_ap"],
            "validation_entity_ap": metrics["validation_entity_ap"],
            "validation_entity_ap_tail": entity_ap_tail,
            "validation_seconds": metrics["seconds"],
        }
        history.append(entry)
        state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
        if metrics["validation_flow_ap"] > best_flow["metric"]:
            best_flow = {"metric": metrics["validation_flow_ap"], "epoch": epoch, "state": state}
        if metrics["validation_entity_ap"] > best_entity["metric"]:
            best_entity = {"metric": metrics["validation_entity_ap"], "epoch": epoch, "state": state}
        # 双聚合选轮（2026-09-01 C10 路线裁决第〇节）：只在 validation_metrics 分支
        # （非 CEM）追踪 tail 口径的最佳轮，同构的 `>` 比较即 tie_rule 要求的
        # strict_argmax_earliest（打平不更新，保留先出现的轮次）。
        if not entity_memory_enabled and entity_ap_tail > best_entity_tail["metric"]:
            best_entity_tail = {"metric": entity_ap_tail, "epoch": epoch, "state": state}
        payload = checkpoint_payload(
            config, science_receipt, runtime_receipt, model, optimizer, epoch, step_count,
            history, best_flow, best_entity, generator, torch_module, device, profile,
            view.transform.state_hash,
            train_scheduler=(
                entity_memory_context["train_scheduler"] if entity_memory_context is not None else None
            ),
            memory_state=memory_state if entity_memory_enabled else None,
            xi_state=xi_state if entity_ranking_enabled else None,
            numpy_rng=entity_ranking_rng,
            best_entity_tail=best_entity_tail if not entity_memory_enabled else None,
        )
        atomic_torch(inflight_path, payload, torch_module)
        # 每轮落一次：运行被中断时收据仍反映已发生的实际调用路径与图断裂，
        # 不必等到全部轮次跑完。
        execution_path.write_execution_path_receipt(
            output_root, config, stage="train", project_root=str(PROJECT_ROOT),
            atomic_json=atomic_json, logger=LOGGER, extra={"epoch": epoch},
        )
        print(json.dumps({
            "epoch": epoch,
            "flow_ap": metrics["validation_flow_ap"],
            "entity_ap": metrics["validation_entity_ap"],
            "entity_ap_tail": entity_ap_tail,
            "best_flow_epoch": best_flow["epoch"],
            "best_entity_epoch": best_entity["epoch"],
            "best_entity_tail_epoch": best_entity_tail["epoch"] if not entity_memory_enabled else None,
        }, ensure_ascii=False), flush=True)
    require(best_flow["state"] is not None and best_entity["state"] is not None, "训练结束但双选轮状态为空", EXIT_RUNTIME)
    # entity-tail 检查点只在 validation_metrics 分支（非 CEM）产出：CEM 走另一套
    # 评价函数，从未计算 tail 口径，本就不该有第三份检查点。
    require(
        entity_memory_enabled or best_entity_tail["state"] is not None,
        "训练结束但 tail 口径选轮状态为空", EXIT_RUNTIME,
    )
    selection_roles: list[tuple[str, dict[str, Any]]] = [("flow", best_flow), ("entity", best_entity)]
    if not entity_memory_enabled:
        selection_roles.append(("entity-tail", best_entity_tail))
    for role, selected in selection_roles:
        payload = {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "science_identity": science_receipt,
            "runtime_identity": runtime_receipt,
            "run_id": config["identity"]["run_id"],
            "selection_role": role,
            "selected_epoch": selected["epoch"],
            "selected_metric": selected["metric"],
            "model_state_dict": selected["state"],
            "formal_resume_eligible": config["checkpoint"]["formal_resume_eligible"],
        }
        atomic_torch(output_root / "checkpoints" / f"selected-by-{role}.pt", payload, torch_module)
    receipt = {
        "schema_version": "ch3-ft-c00-dual-selection-receipt-v1",
        "run_id": config["identity"]["run_id"],
        "history": history,
        "best_by_flow": {"epoch": best_flow["epoch"], "metric": best_flow["metric"]},
        "best_by_entity": {"epoch": best_entity["epoch"], "metric": best_entity["metric"]},
        "best_by_entity_tail": (
            {"epoch": best_entity_tail["epoch"], "metric": best_entity_tail["metric"]}
            if not entity_memory_enabled else None
        ),
        "optimizer": optimizer_receipt,
        "train_positive_rate": train_positive_rate,
        "wall_seconds": time.time() - started,
        "resource": {"process_peak_rss_bytes": process_peak_rss_bytes(), **accelerator_memory(torch_module, device)},
        "target_reads": 0,
    }
    atomic_json(output_root / "receipts" / "selection.json", receipt)
    execution_path.write_execution_path_receipt(
        output_root, config, stage="train-finished", project_root=str(PROJECT_ROOT),
        atomic_json=atomic_json, logger=LOGGER,
        extra={"epochs_completed": config["budget"]["epochs"], "wall_seconds": receipt["wall_seconds"]},
    )
    atomic_json(output_root / "status.json", {
        "run_id": config["identity"]["run_id"], "state": "finished", "stage": "train",
        "exit_code": 0, "target_reads": 0,
    })


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="裸 FT C00 跨设备双选轮训练")
    parser.add_argument("--config", required=True, help="冻结配置")
    parser.add_argument("--validate-config", action="store_true", help="仅核验配置")
    parser.add_argument("--calibrate-runtime", action="store_true", help="真实执行一个完整优化步和一次源验证")
    parser.add_argument("--run", action="store_true", help="按冻结预算训练")
    parser.add_argument("--resume", action="store_true", help="从同身份完整轮边界恢复")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    args = parse_args()
    config_path = Path(args.config).resolve()
    try:
        config = load_json(config_path)
        validate_config(config)
        if args.validate_config:
            print(json.dumps({
                "config_valid": True,
                "science_identity_sha256": canonical_sha256(science_projection(config)),
                "runtime_identity_sha256": canonical_sha256(runtime_projection(config)),
            }, ensure_ascii=False))
            return 0
        require(args.calibrate_runtime ^ args.run, "必须且只能指定 --calibrate-runtime 或 --run")
        if args.calibrate_runtime:
            probe_runtime(config, config_path)
        else:
            run_training(config, config_path, args.resume)
        return 0
    except ExperimentError as error:
        print(str(error), file=sys.stderr, flush=True)
        return error.exit_code
    except Exception as error:  # noqa: BLE001
        traceback.print_exc()
        print(f"未预期错误：{error}", file=sys.stderr, flush=True)
        return EXIT_RUNTIME


if __name__ == "__main__":
    sys.exit(main())
