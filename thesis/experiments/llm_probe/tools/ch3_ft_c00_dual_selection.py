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

# mechanism 键在既有两份 C00 配置（cuda-formal / mps-screening）中不存在；缺省即
# 机制一、机制二均关闭，行为与这两份配置历史上的语义完全一致，因此不需要改动它们。
# entity_ranking 与 entity_memory 对称新增，机制二实现报告见
# .Codex/docs/RWKV/2026-08-28-机制二实现报告.md。
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
    expected_candidate_key = {
        (False, False): "bare-ft-c00-dual-selection",
        (True, False): "causal-entity-memory-c10-dual-selection",
        (False, True): "budget-aware-entity-ranking-c01-dual-selection",
        (True, True): "cem-ber-c11-dual-selection",
    }[(entity_memory_enabled, entity_ranking_enabled)]
    require(identity.get("candidate_key") == expected_candidate_key, "候选身份不符")
    require(identity.get("science_contract_version") == "ch3-ft-c00-dual-selection-science-v1", "科学合同版本不符")
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
        require(device_type == "mps", "本机筛选必须使用 MPS")
        require(config["checkpoint"]["formal_resume_eligible"] is False, "MPS 检查点不得正式续训")
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
    else:
        slots = entity_memory.get("slots")
        require(slots is None or isinstance(slots, int), "z1=0 时 slots 只能是 null 或整数（不参与模型构造）")
        require(config.get("model") == {
            "role": "bare_ft_transformer",
            "expected_parameter_count": BARE_FT_PARAMETER_COUNT,
            "old_cpa_enabled": False,
            "old_elp_enabled": False,
            "old_mechanism_scaffold_present": False,
        }, "裸 FT 模型合同不符")

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
        xi_learning_rate = entity_ranking.get("xi_learning_rate")
        require(
            isinstance(xi_learning_rate, (int, float)) and not isinstance(xi_learning_rate, bool) and xi_learning_rate > 0,
            "xi_learning_rate 必须是正数",
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
    require(config.get("evaluation", {}).get("entity_aggregation") == "maximum_over_validation_flows", "实体聚合口径不符")
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

    _ENTITY_MEMORY_MODEL_CACHE["CausalEntityMemoryFTModel"] = CausalEntityMemoryFTModel
    return CausalEntityMemoryFTModel


def build_model_optimizer(config: dict[str, Any], base_config: dict[str, Any], view: Any, torch_module: Any, device: Any) -> tuple[Any, Any, dict[str, Any]]:
    entity_memory_enabled = entity_memory_enabled_from_config(config)

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


def forward_bare(model: Any, numeric: Any, categorical: Any, valid: Any, device: Any, profile: dict[str, Any], precision: Any, torch_module: Any) -> Any:
    numeric_t = torch_module.from_numpy(numeric).to(device)
    categorical_t = torch_module.from_numpy(categorical).to(device) if categorical is not None else None
    valid_t = torch_module.from_numpy(valid).to(device)
    batch, length = valid.shape
    flat_num = numeric_t.reshape(batch * length, numeric_t.shape[-1])
    flat_cat = categorical_t.reshape(batch * length, categorical_t.shape[-1]) if categorical_t is not None else None
    with precision.autocast_context(profile, device.type, torch_module):
        logits = model(flat_num, flat_cat).reshape(batch, length)
    return logits, valid_t


def training_step(
    config: dict[str, Any], base_config: dict[str, Any], model: Any, optimizer: Any,
    view: Any, train_rows: Any, generator: Any, device: Any, profile: dict[str, Any],
    precision: Any, torch_module: Any, positive_weight: Any,
) -> dict[str, Any]:
    import numpy as np

    effective = config["training"]["effective_batch_size"]
    micro = config["training"]["micro_batch_sequences"]
    positions = base.sample_distinct_positions(len(train_rows), effective, generator)
    rows = train_rows[positions.numpy()]
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
            model, numeric, categorical, valid[start:stop], device, profile, precision, torch_module
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
) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import average_precision_score

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
            logits, _ = forward_bare(model, numeric, categorical, valid, device, profile, precision, torch_module)
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
    entity_scores = np.full(entity_count, -np.inf, dtype=np.float64)
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_scores, entities, scores)
    np.maximum.at(entity_labels, entities, labels)
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

        with precision.autocast_context(profile, device.type, torch_module):
            representation = model.encode(flat_num, flat_cat)
            width = representation.shape[-1]
            broadcast_memory, broadcast_valid = _broadcast_segment_memory(segment_memory, segment_valid, batch, length)
            injected = model.inject(representation, broadcast_memory, broadcast_valid)
            logits = model.predict(injected).reshape(batch, length)

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

                representation = model.encode(flat_num, flat_cat)
                width = representation.shape[-1]
                broadcast_memory, broadcast_valid = _broadcast_segment_memory(segment_memory, segment_valid, batch, length)
                injected = model.inject(representation, broadcast_memory, broadcast_valid)
                logits = model.predict(injected).reshape(batch, length)
                gate_means.append(model.memory.gate_statistics()["gate_mean"])
                valid_slot_means.append(float(segment_valid.sum(dim=1).to(torch_module.float32).mean().item()))

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
        logits_a, _ = forward_bare(model, numeric, categorical, valid, device, profile, precision, torch_module)
        logits_b, _ = forward_bare(reference, numeric, categorical, valid, device, profile, precision, torch_module)
    if was_training:
        model.train()
    require(torch_module.equal(logits_a, logits_b), "z1=0 路径 logits 与新建裸模型不是逐位相等", EXIT_RUNTIME)
    LOGGER.info("零门退化断言通过：z1=0 路径与裸 FT 在 %d 个探测片段上 logits 逐位相等", len(probe_rows))


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
        logits, valid_t = forward_bare(model, numeric, categorical, valid[start:stop], device, profile, precision, torch_module)
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
        with precision.autocast_context(profile, device.type, torch_module):
            representation = model.encode(flat_num, flat_cat)
            width = representation.shape[-1]
            broadcast_memory, broadcast_valid = _broadcast_segment_memory(segment_memory, segment_valid, batch, length)
            injected = model.inject(representation, broadcast_memory, broadcast_valid)
            logits = model.predict(injected).reshape(batch, length)
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
    """z1=0：实体排序批各片段互不依赖（裸 FT 无跨片段状态），可分微批并行前向。"""
    micro = config["training"]["micro_batch_sequences"]
    logits_parts = []
    valid_parts = []
    for start in range(0, indices.shape[0], micro):
        stop = start + micro
        numeric, categorical = view.features(indices[start:stop])
        logits, valid_t = forward_bare(model, numeric, categorical, valid[start:stop], device, profile, precision, torch_module)
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

    micro = config["training"]["micro_batch_sequences"]
    logits_parts = []
    valid_parts = []
    for start in range(0, indices.shape[0], micro):
        stop = start + micro
        micro_rows = entity_rows[start:stop]
        micro_entity_ids = torch_module.from_numpy(entity_of_row[micro_rows].astype(np.int64)).to(device)
        micro_is_start = torch_module.from_numpy(is_start_np[start:stop]).to(device)
        micro_valid = valid[start:stop]
        if bool(micro_is_start.any()):
            scratch_memory_state.reset_entities(micro_entity_ids[micro_is_start])
        segment_memory = scratch_memory_state.read(micro_entity_ids)
        segment_valid = scratch_memory_state.valid(micro_entity_ids)
        numeric, categorical = view.features(indices[start:stop])
        numeric_t = torch_module.from_numpy(numeric).to(device)
        categorical_t = torch_module.from_numpy(categorical).to(device) if categorical is not None else None
        valid_t = torch_module.from_numpy(micro_valid).to(device)
        batch, length = micro_valid.shape
        flat_num = numeric_t.reshape(batch * length, numeric_t.shape[-1])
        flat_cat = categorical_t.reshape(batch * length, categorical_t.shape[-1]) if categorical_t is not None else None
        with precision.autocast_context(profile, device.type, torch_module):
            representation = model.encode(flat_num, flat_cat)
            width = representation.shape[-1]
            broadcast_memory, broadcast_valid = _broadcast_segment_memory(segment_memory, segment_valid, batch, length)
            injected = model.inject(representation, broadcast_memory, broadcast_valid)
            logits = model.predict(injected).reshape(batch, length)
        summary = _segment_summary_from_injected(injected, micro_valid, batch, length, width, torch_module, device)
        scratch_memory_state.write(micro_entity_ids, summary)
        logits_parts.append(logits)
        valid_parts.append(valid_t)
    return torch_module.cat(logits_parts, dim=0), torch_module.cat(valid_parts, dim=0)


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
    xi = xi_state.get(positive_entity_ids).to(device)
    xi.retain_grad()

    with precision.fp32_island(entity_logits, device_type=device.type, torch_module=torch_module) as (entity_logits32,):
        bag_config = ranking.BagPolicyConfig(
            active_policy=ranking_cfg["bag_policy"],
            truncate_length=int(ranking_cfg["truncate_length"]),
            num_length_buckets=int(ranking_cfg["num_length_buckets"]),
        )
        bag_result = ranking.bag_policy_diagnostics(
            entity_logits32, entity_valid_t, segment_owner, entity_is_positive,
            entity_chain_length, eff_budgets, xi, bag_config,
        )
        loss_rank = bag_result["loss"]
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
    }
    return g_rank, diagnostics


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
    LOGGER.info("启动真实运行校准：run_id=%s", config["identity"]["run_id"])
    atomic_json(output_root / "status.json", {
        "run_id": config["identity"]["run_id"], "state": "running", "stage": "probe-runtime",
        "exit_code": None, "target_reads": 0,
    })
    torch_module, device, profile, precision = resolve_runtime(config)
    base_config = effective_base_config(config)
    arrays, train_rows, validation_rows, view = prepare_data(config, base_config, output_root)
    model, optimizer, optimizer_receipt = build_model_optimizer(
        config, base_config, view, torch_module, device
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
        xi_state = ranking.CvarThresholdState(budgets=config["mechanism"]["entity_ranking"]["budgets"])
        if entity_memory_enabled:
            scratch_memory_state = build_entity_memory_state(config, base_config, entity_memory_context, torch_module, device)
    require(
        entity_ranking_enabled or (sampler is None and xi_state is None and scratch_memory_state is None),
        "z2=0 时不得构造实体排序采样器或阈值状态", EXIT_RUNTIME,
    )
    assert_zero_gate_degeneracy(
        config, base_config, model, memory_state, view, train_rows, device, profile, precision, torch_module
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
            config, model, view, arrays, validation_rows, device, profile, precision, torch_module
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
    numpy_rng: Any = None,
) -> dict[str, Any]:
    """构造检查点载荷。

    机制状态（2026-08-28 补齐）：`z1` 臂的实体链调度器游标与 ``EntityMemoryState``、
    `z2` 臂的 CVaR 阈值状态与 numpy 采样 RNG 一并入盘，使带机制的臂可原子续训。
    未启用对应机制时相应键为 ``None``，恢复端据此校验开关一致性。

    ``EntityMemoryState.state_dict`` 已是稀疏导出（只含 ``count > 0`` 的已激活实体），
    全量 150,680 实体 × R=8 × d=192 × 4B ≈ 0.93 GB，稀疏后随训练进度增长而远小于该上界。
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
    torch_module, device, profile, precision = resolve_runtime(config)
    base_config = effective_base_config(config)
    arrays, train_rows, validation_rows, view = prepare_data(config, base_config, output_root)
    model, optimizer, optimizer_receipt = build_model_optimizer(config, base_config, view, torch_module, device)
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
        xi_state = ranking.CvarThresholdState(budgets=config["mechanism"]["entity_ranking"]["budgets"])
        if entity_memory_enabled:
            scratch_memory_state = build_entity_memory_state(config, base_config, entity_memory_context, torch_module, device)
    require(
        entity_ranking_enabled or (sampler is None and xi_state is None and scratch_memory_state is None),
        "z2=0 时不得构造实体排序采样器或阈值状态", EXIT_RUNTIME,
    )
    assert_zero_gate_degeneracy(
        config, base_config, model, memory_state, view, train_rows, device, profile, precision, torch_module
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
        restore_rng(checkpoint["rng_state"], torch_module, device)
        generator.set_state(checkpoint["rng_state"]["sampler_state"])
        start_epoch = int(checkpoint["epoch"]) + 1
        step_count = int(checkpoint["optimizer_step"])
        restore_mechanism_state(
            checkpoint, train_scheduler,
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
                config, model, view, arrays, validation_rows, device, profile, precision, torch_module
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
                "gradient_control": {
                    "c_scaling_median": float(np.median(c_values)) if c_values else None,
                    "c_equal_one_step_count": int(sum(1 for c in c_values if c >= 1.0 - 1e-9)),
                    "grad_norm_flow_median": float(np.median(grad_norm_flow_values)) if grad_norm_flow_values else None,
                    "grad_norm_rank_median": float(np.median(grad_norm_rank_values)) if grad_norm_rank_values else None,
                    "projection_triggered_step_count": projection_triggered_count,
                },
                "last_step_snapshot": epoch_ranking_diagnostics[-1] if epoch_ranking_diagnostics else None,
            })
        entry = {
            "epoch": epoch,
            "mean_training_loss": float(np.mean(losses)),
            "validation_flow_ap": metrics["validation_flow_ap"],
            "validation_entity_ap": metrics["validation_entity_ap"],
            "validation_seconds": metrics["seconds"],
        }
        history.append(entry)
        state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
        if metrics["validation_flow_ap"] > best_flow["metric"]:
            best_flow = {"metric": metrics["validation_flow_ap"], "epoch": epoch, "state": state}
        if metrics["validation_entity_ap"] > best_entity["metric"]:
            best_entity = {"metric": metrics["validation_entity_ap"], "epoch": epoch, "state": state}
        payload = checkpoint_payload(
            config, science_receipt, runtime_receipt, model, optimizer, epoch, step_count,
            history, best_flow, best_entity, generator, torch_module, device, profile,
            view.transform.state_hash,
            train_scheduler=train_scheduler,
            memory_state=memory_state if entity_memory_enabled else None,
            xi_state=xi_state if entity_ranking_enabled else None,
            numpy_rng=entity_ranking_rng,
        )
        atomic_torch(inflight_path, payload, torch_module)
        print(json.dumps({
            "epoch": epoch,
            "flow_ap": metrics["validation_flow_ap"],
            "entity_ap": metrics["validation_entity_ap"],
            "best_flow_epoch": best_flow["epoch"],
            "best_entity_epoch": best_entity["epoch"],
        }, ensure_ascii=False), flush=True)
    require(best_flow["state"] is not None and best_entity["state"] is not None, "训练结束但双选轮状态为空", EXIT_RUNTIME)
    for role, selected in (("flow", best_flow), ("entity", best_entity)):
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
        "optimizer": optimizer_receipt,
        "train_positive_rate": train_positive_rate,
        "wall_seconds": time.time() - started,
        "resource": {"process_peak_rss_bytes": process_peak_rss_bytes(), **accelerator_memory(torch_module, device)},
        "target_reads": 0,
    }
    atomic_json(output_root / "receipts" / "selection.json", receipt)
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
