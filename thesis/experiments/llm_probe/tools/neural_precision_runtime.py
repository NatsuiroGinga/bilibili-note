# -*- coding: utf-8 -*-
"""单卡神经训练精度、等效微批量与资源收据共享脚手架。

本模块不修改任何现有训练入口，也不在顶层导入 PyTorch。接入方先加载并验证
`configs/neural-precision-profiles-v1.json`，再把真实运行环境中的 ``torch`` 模块
显式传给运行时辅助函数。

敏感计算示例：

    with autocast_context(profile, device.type, torch) as _:
        logits = model(inputs)
    with fp32_island(logits, device_type=device.type, torch_module=torch) as (logits32,):
        loss_sum = torch.nn.functional.binary_cross_entropy_with_logits(
            logits32, targets.float(), reduction="sum"
        )

等效微批示例：原始有效批先确定全部有效单位数，随后只清梯度一次、逐微批反向，
最后只裁剪和更新一次。模型必须显式声明归一化单位是 flow、sequence 或 entity。
"""

from __future__ import annotations

import argparse
import json
import math
import random
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, ContextManager, Iterable, Iterator, Mapping


SCHEMA_VERSION = "neural-precision-contract-v1"
DEFAULT_PROFILE_ID = "cuda-bf16-amp-fp32-sensitive-v1"
FP16_FALLBACK_PROFILE_ID = "cuda-fp16-amp-gradscaler-v1"
FP32_FALLBACK_PROFILE_ID = "cuda-fp32-numerical-fallback-v1"
CPU_PROFILE_ID = "cpu-fp32-v1"
MPS_PROFILE_ID = "mps-fp32-v1"
NORMALIZATION_UNITS = ("flow", "sequence", "entity")
SENSITIVE_COMPUTATIONS = (
    "softmax",
    "log",
    "probability_normalization",
    "loss",
    "reduction",
    "metrics",
    "model_declared_recursive_state",
    "model_declared_routing",
)
SAME_PROFILE_CLAIMS = (
    "structure_causal",
    "mechanism_causal",
    "same_family_selection",
)
CROSS_PROFILE_CLAIMS = ("complete_system_pareto", "engineering_observation")
CHECKPOINT_REQUIRED_FIELDS = (
    "precision_profile_id",
    "precision_profile",
    "scaler_state_dict",
    "effective_batch_items",
    "effective_batch_item_unit",
    "microbatch_items",
    "accumulation_steps",
    "normalization_unit",
    "is_tail_batch",
    "rng_state",
    "optimizer_step",
    "optimizer_step_boundary",
)
RESOURCE_REQUIRED_FIELDS = (
    "precision_profile_id",
    "device_type",
    "effective_batch_items",
    "microbatch_items",
    "accumulation_steps",
    "normalization_unit",
    "cuda_memory_allocated_bytes",
    "cuda_memory_reserved_bytes",
    "cuda_max_memory_allocated_bytes",
    "cuda_max_memory_reserved_bytes",
    "external_process_gpu_memory_mib",
    "external_measurement_source",
    "processed_valid_units",
    "elapsed_seconds",
    "valid_units_per_second",
)


class ContractValidationError(ValueError):
    """表示精度、累积、比较或收据合同不成立。"""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractValidationError(message)


def _require_exact_keys(value: Mapping[str, Any], required: Iterable[str], name: str) -> None:
    missing = sorted(set(required) - set(value))
    _require(not missing, f"{name} 缺少字段：{', '.join(missing)}")


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON 顶层必须是对象：{path}")
    return value


def validate_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    """使用标准库验证共享合同，不要求安装 PyTorch 或 jsonschema。"""

    top_level = (
        "schema_version",
        "default_profile",
        "device_fallbacks",
        "profiles",
        "runtime_defaults",
        "effective_batch_contract",
        "comparison_contract",
        "checkpoint_contract",
        "resource_receipt_contract",
        "integration_example",
    )
    _require_exact_keys(contract, top_level, "精度合同")
    _require(contract["schema_version"] == SCHEMA_VERSION, "精度合同 schema_version 不符")
    _require(contract["default_profile"] == DEFAULT_PROFILE_ID, "默认精度配置标识不符")

    profiles = contract["profiles"]
    _require(isinstance(profiles, dict), "profiles 必须是对象")
    required_profile_ids = (
        DEFAULT_PROFILE_ID,
        FP16_FALLBACK_PROFILE_ID,
        FP32_FALLBACK_PROFILE_ID,
        CPU_PROFILE_ID,
        MPS_PROFILE_ID,
    )
    _require_exact_keys(profiles, required_profile_ids, "profiles")
    for profile_id, raw_profile in profiles.items():
        _require(isinstance(raw_profile, dict), f"配置 {profile_id} 必须是对象")
        _validate_profile_definition(profile_id, raw_profile)

    fallbacks = contract["device_fallbacks"]
    _require(isinstance(fallbacks, dict), "device_fallbacks 必须是对象")
    _require(
        fallbacks
        == {
            "cuda_without_bf16": FP16_FALLBACK_PROFILE_ID,
            "cpu": CPU_PROFILE_ID,
            "mps": MPS_PROFILE_ID,
        },
        "设备回退映射不符，禁止静默选择未核验配置",
    )

    runtime = contract["runtime_defaults"]
    _require(isinstance(runtime, dict), "runtime_defaults 必须是对象")
    _require(runtime.get("activation_checkpointing") is False, "激活检查点必须默认关闭")
    _require(runtime.get("torch_compile") is False, "torch.compile 必须默认关闭")
    _require(runtime.get("tf32") is False, "TF32 必须默认关闭")
    _require(runtime.get("model_parameter_dtype") == "float32", "模型参数必须保持 FP32")
    _require(runtime.get("optimizer_state_dtype") == "float32", "优化器状态必须保持 FP32")
    _require(
        runtime.get("activation_checkpointing_enable_condition")
        == "explicit_after_bf16_and_equivalent_microbatch_are_insufficient",
        "激活检查点启用条件不符",
    )

    effective = contract["effective_batch_contract"]
    _require(isinstance(effective, dict), "effective_batch_contract 必须是对象")
    expected_effective = {
        "effective_batch_source": "experiment_contract",
        "microbatch_selection": "resource_only",
        "microbatch_factor_rule": "exact_mechanical_factor_of_effective_batch_items",
        "zero_grad_per_original_step": "exactly_once_set_to_none_true",
        "loss_semantics": "sum_each_microbatch_divide_by_total_valid_units",
        "clip_per_original_step": "at_most_once_after_all_microbatches",
        "optimizer_step_per_original_step": "exactly_once_after_all_microbatches",
        "tail_batch_policy": "keep_real_units_no_padding_no_drop",
        "normalization_units": list(NORMALIZATION_UNITS),
    }
    _require(effective == expected_effective, "有效批与梯度累积合同不符")

    comparison = contract["comparison_contract"]
    _require(isinstance(comparison, dict), "comparison_contract 必须是对象")
    _require(
        comparison.get("same_profile_required_for") == list(SAME_PROFILE_CLAIMS),
        "同精度比较类型不符",
    )
    _require(
        comparison.get("cross_profile_allowed_for") == list(CROSS_PROFILE_CLAIMS),
        "跨精度允许比较类型不符",
    )

    checkpoint = contract["checkpoint_contract"]
    resource = contract["resource_receipt_contract"]
    _require(isinstance(checkpoint, dict), "checkpoint_contract 必须是对象")
    _require(isinstance(resource, dict), "resource_receipt_contract 必须是对象")
    _require(
        checkpoint.get("required_fields") == list(CHECKPOINT_REQUIRED_FIELDS),
        "检查点必填字段不符",
    )
    _require(
        resource.get("required_fields") == list(RESOURCE_REQUIRED_FIELDS),
        "资源收据必填字段不符",
    )

    example = contract["integration_example"]
    _require(isinstance(example, dict), "integration_example 必须是对象")
    _require(example.get("example_only") is True, "接入示例必须声明仅为示例")
    _require(
        example.get("do_not_inherit_batch_values") is True,
        "接入示例必须禁止其他模型继承批量数值",
    )
    validate_microbatch_plan(
        effective_batch_items=example.get("effective_batch_items"),
        microbatch_items=example.get("microbatch_items"),
        accumulation_steps=example.get("accumulation_steps"),
        normalization_unit=example.get("normalization_unit"),
        is_tail_batch=False,
    )
    _require(example.get("profile_id") in profiles, "接入示例引用了未知精度配置")
    _require(
        example.get("effective_batch_item_unit") in NORMALIZATION_UNITS,
        "接入示例的有效批对象单位非法",
    )
    return dict(contract)


def _validate_profile_definition(profile_id: str, profile: Mapping[str, Any]) -> None:
    required = (
        "device_type",
        "compute_dtype",
        "autocast",
        "grad_scaler",
        "parameter_dtype",
        "optimizer_state_dtype",
        "sensitive_computations",
        "fallback_requires_receipt",
        "scientific_status",
    )
    _require_exact_keys(profile, required, f"配置 {profile_id}")
    _require(profile["device_type"] in ("cuda", "cpu", "mps"), f"配置 {profile_id} 设备非法")
    _require(
        profile["compute_dtype"] in ("bfloat16", "float16", "float32"),
        f"配置 {profile_id} 计算类型非法",
    )
    _require(profile["parameter_dtype"] == "float32", f"配置 {profile_id} 参数必须为 FP32")
    _require(
        profile["optimizer_state_dtype"] == "float32",
        f"配置 {profile_id} 优化器状态必须为 FP32",
    )
    _require(
        profile["sensitive_computations"] == list(SENSITIVE_COMPUTATIONS),
        f"配置 {profile_id} 的 FP32 敏感计算清单不完整或顺序不符",
    )
    compute_dtype = profile["compute_dtype"]
    if compute_dtype == "bfloat16":
        _require(profile["device_type"] == "cuda", "BF16 默认配置只允许 CUDA")
        _require(profile["autocast"] is True, "CUDA BF16 必须启用 autocast")
        _require(profile["grad_scaler"] is False, "BF16 默认不得启用 GradScaler")
    elif compute_dtype == "float16":
        _require(profile["device_type"] == "cuda", "FP16 回退只允许 CUDA")
        _require(profile["autocast"] is True, "CUDA FP16 必须启用 autocast")
        _require(profile["grad_scaler"] is True, "FP16 回退必须启用 GradScaler")
        _require(profile["fallback_requires_receipt"] is True, "FP16 回退必须有硬件收据")
    else:
        _require(profile["autocast"] is False, f"配置 {profile_id} 的 FP32 不得启用 autocast")
        _require(profile["grad_scaler"] is False, f"配置 {profile_id} 的 FP32 不得启用 GradScaler")
    if profile_id == FP32_FALLBACK_PROFILE_ID:
        _require(profile["fallback_requires_receipt"] is True, "CUDA FP32 回退必须有数值异常收据")
    if profile["device_type"] in ("cpu", "mps"):
        _require(compute_dtype == "float32", "CPU/MPS 默认只允许 FP32")


def load_and_validate_contract(path: Path | str) -> dict[str, Any]:
    return validate_contract(load_json_object(Path(path)))


def get_profile(contract: Mapping[str, Any], profile_id: str | None = None) -> dict[str, Any]:
    resolved_id = profile_id or str(contract["default_profile"])
    profiles = contract["profiles"]
    _require(resolved_id in profiles, f"未知精度配置：{resolved_id}")
    return dict(profiles[resolved_id])


def profile_for_device(contract: Mapping[str, Any], device_type: str) -> str:
    """返回设备默认配置；CUDA 无 BF16 时不在此处静默降级。"""

    if device_type == "cuda":
        return str(contract["default_profile"])
    if device_type in ("cpu", "mps"):
        return str(contract["device_fallbacks"][device_type])
    raise ContractValidationError(f"未核验设备类型：{device_type}")


def validate_runtime_profile(
    contract: Mapping[str, Any],
    profile_id: str,
    device_type: str,
    torch_module: Any,
    fallback_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """核验真实设备能力与显式回退依据，不静默切换配置。"""

    profile = get_profile(contract, profile_id)
    _require(profile["device_type"] == device_type, "精度配置与真实设备类型不一致")
    if profile["fallback_requires_receipt"]:
        _require(bool(fallback_receipt), f"配置 {profile_id} 必须提供回退收据")
    if profile["compute_dtype"] == "bfloat16":
        _require(hasattr(torch_module, "amp"), "目标 PyTorch 缺少统一 torch.amp 入口")
        _require(torch_module.cuda.is_available(), "CUDA BF16 配置要求可用 CUDA")
        _require(
            bool(torch_module.cuda.is_bf16_supported()),
            f"当前 CUDA 不支持 BF16；须显式选择 {FP16_FALLBACK_PROFILE_ID} 并记录硬件收据",
        )
    if profile["compute_dtype"] == "float16":
        _require(hasattr(torch_module.amp, "GradScaler"), "目标 PyTorch 缺少 torch.amp.GradScaler")
    return profile


def validate_model_optimizer_fp32(model: Any, optimizer: Any, torch_module: Any) -> dict[str, int]:
    """检查模型浮点参数和已建立的优化器浮点状态均为 FP32。"""

    parameter_count = 0
    for name, parameter in model.named_parameters():
        if parameter.is_floating_point():
            parameter_count += 1
            _require(parameter.dtype == torch_module.float32, f"模型参数 {name} 不是 FP32")
    state_tensor_count = 0
    for state in optimizer.state.values():
        for key, value in state.items():
            if torch_module.is_tensor(value) and value.is_floating_point():
                state_tensor_count += 1
                _require(value.dtype == torch_module.float32, f"优化器状态 {key} 不是 FP32")
    return {
        "checked_floating_parameters": parameter_count,
        "checked_floating_optimizer_states": state_tensor_count,
    }


def autocast_context(
    profile: Mapping[str, Any],
    device_type: str,
    torch_module: Any,
) -> ContextManager[Any]:
    """按配置返回 autocast；CPU/MPS 与 FP32 配置返回空上下文。"""

    _require(profile["device_type"] == device_type, "autocast 设备与配置不一致")
    if not profile["autocast"]:
        return nullcontext()
    dtype = {
        "bfloat16": torch_module.bfloat16,
        "float16": torch_module.float16,
    }.get(profile["compute_dtype"])
    _require(dtype is not None, "启用 autocast 的配置必须是 BF16 或 FP16")
    return torch_module.amp.autocast(device_type, dtype=dtype)


@contextmanager
def fp32_island(
    *tensors: Any,
    device_type: str,
    torch_module: Any,
) -> Iterator[tuple[Any, ...]]:
    """禁用 CUDA autocast，并把 BF16/FP16 输入显式提升到 FP32。"""

    _require(device_type in ("cuda", "cpu", "mps"), f"未核验设备类型：{device_type}")
    low_precision = (torch_module.float16, torch_module.bfloat16)
    context = (
        torch_module.amp.autocast("cuda", enabled=False)
        if device_type == "cuda"
        else nullcontext()
    )
    with context:
        converted = tuple(
            tensor.float()
            if torch_module.is_tensor(tensor) and tensor.dtype in low_precision
            else tensor
            for tensor in tensors
        )
        yield converted


def create_grad_scaler(profile: Mapping[str, Any], torch_module: Any) -> Any | None:
    if not profile["grad_scaler"]:
        return None
    _require(profile["compute_dtype"] == "float16", "只有 FP16 回退可创建 GradScaler")
    return torch_module.amp.GradScaler("cuda")


def validate_microbatch_plan(
    effective_batch_items: Any,
    microbatch_items: Any,
    accumulation_steps: Any,
    normalization_unit: Any,
    is_tail_batch: bool,
) -> dict[str, int | str | bool]:
    """验证完整有效批的机械因子，或尾批的真实不补不丢切分。"""

    values = (effective_batch_items, microbatch_items, accumulation_steps)
    _require(all(isinstance(value, int) and not isinstance(value, bool) for value in values), "批量值必须是整数")
    _require(all(value > 0 for value in values), "批量值必须为正")
    _require(normalization_unit in NORMALIZATION_UNITS, "归一化单位必须是 flow、sequence 或 entity")
    if is_tail_batch:
        expected_steps = math.ceil(effective_batch_items / microbatch_items)
        _require(accumulation_steps == expected_steps, "尾批累积次数必须覆盖全部真实对象且不得补齐")
        final_microbatch_items = effective_batch_items - microbatch_items * (accumulation_steps - 1)
    else:
        _require(
            microbatch_items * accumulation_steps == effective_batch_items,
            "完整有效批必须满足 microbatch_items × accumulation_steps = effective_batch_items",
        )
        final_microbatch_items = microbatch_items
    _require(0 < final_microbatch_items <= microbatch_items, "末微批对象数非法")
    return {
        "effective_batch_items": effective_batch_items,
        "microbatch_items": microbatch_items,
        "accumulation_steps": accumulation_steps,
        "normalization_unit": normalization_unit,
        "is_tail_batch": is_tail_batch,
        "final_microbatch_items": final_microbatch_items,
    }


class EffectiveBatchAccumulator:
    """保证一个原始优化步只有一次清梯度、裁剪和参数更新。"""

    def __init__(
        self,
        total_valid_units: int,
        normalization_unit: str,
        torch_module: Any,
        expected_microbatches: int | None = None,
    ) -> None:
        _require(isinstance(total_valid_units, int) and total_valid_units > 0, "全部有效单位数必须为正整数")
        _require(normalization_unit in NORMALIZATION_UNITS, "归一化单位非法")
        if expected_microbatches is not None:
            _require(expected_microbatches > 0, "预期微批数必须为正")
        self.total_valid_units = total_valid_units
        self.normalization_unit = normalization_unit
        self.torch_module = torch_module
        self.expected_microbatches = expected_microbatches
        self.consumed_valid_units = 0
        self.microbatch_count = 0
        self._started = False
        self._finished = False

    def begin(self, optimizer: Any) -> None:
        _require(not self._started and not self._finished, "一个有效批只能开始一次")
        optimizer.zero_grad(set_to_none=True)
        self._started = True

    def backward(self, loss_sum: Any, valid_units: int, scaler: Any | None = None) -> Any:
        _require(self._started and not self._finished, "须先开始有效批且不得在完成后反向")
        _require(isinstance(valid_units, int) and valid_units > 0, "微批有效单位数必须为正整数")
        _require(self.consumed_valid_units + valid_units <= self.total_valid_units, "微批有效单位累计超过本步总数")
        if hasattr(loss_sum, "ndim"):
            _require(loss_sum.ndim == 0, "微批损失必须先按敏感 FP32 区域求和为标量")
        _require(
            getattr(loss_sum, "dtype", None) == self.torch_module.float32,
            "微批损失必须在禁用 autocast 的 FP32 敏感区计算",
        )
        normalized_loss = loss_sum / self.total_valid_units
        if scaler is None:
            normalized_loss.backward()
        else:
            scaler.scale(normalized_loss).backward()
        self.consumed_valid_units += valid_units
        self.microbatch_count += 1
        return normalized_loss

    def finish(
        self,
        model_parameters: Iterable[Any],
        optimizer: Any,
        torch_module: Any,
        max_grad_norm: float,
        scaler: Any | None = None,
    ) -> Any | None:
        _require(self._started and not self._finished, "有效批尚未开始或已经完成")
        _require(self.consumed_valid_units == self.total_valid_units, "有效单位尚未全部反向，禁止更新")
        if self.expected_microbatches is not None:
            _require(self.microbatch_count == self.expected_microbatches, "实际微批数与合同不符")
        if scaler is not None:
            scaler.unscale_(optimizer)
        _require(math.isfinite(max_grad_norm) and max_grad_norm > 0, "梯度裁剪阈值必须为有限正数")
        gradient_norm = torch_module.nn.utils.clip_grad_norm_(model_parameters, max_grad_norm)
        if scaler is None:
            optimizer.step()
        else:
            scaler.step(optimizer)
            scaler.update()
        self._finished = True
        return gradient_norm

    def receipt(self) -> dict[str, Any]:
        return {
            "normalization_unit": self.normalization_unit,
            "total_valid_units": self.total_valid_units,
            "consumed_valid_units": self.consumed_valid_units,
            "microbatch_count": self.microbatch_count,
            "optimizer_step_boundary": self._finished,
        }


def validate_comparison_profiles(
    left_profile_id: str,
    right_profile_id: str,
    claim_type: str,
) -> dict[str, Any]:
    if claim_type in SAME_PROFILE_CLAIMS:
        _require(
            left_profile_id == right_profile_id,
            f"{claim_type} 比较要求相同精度配置；跨配置不得作纯结构或机制因果主张",
        )
    elif claim_type in CROSS_PROFILE_CLAIMS:
        pass
    else:
        raise ContractValidationError(f"未知比较类型：{claim_type}")
    return {
        "left_profile_id": left_profile_id,
        "right_profile_id": right_profile_id,
        "claim_type": claim_type,
        "same_profile": left_profile_id == right_profile_id,
        "valid": True,
    }


def capture_rng_state(torch_module: Any) -> dict[str, Any]:
    state: dict[str, Any] = {
        "python_random": random.getstate(),
        "torch_cpu": torch_module.get_rng_state(),
        "torch_cuda_all": None,
        "numpy_random": None,
    }
    if torch_module.cuda.is_available():
        state["torch_cuda_all"] = torch_module.cuda.get_rng_state_all()
    try:
        import numpy as np
    except ModuleNotFoundError:
        pass
    else:
        state["numpy_random"] = np.random.get_state()
    return state


def build_checkpoint_runtime_state(
    *,
    profile_id: str,
    profile: Mapping[str, Any],
    scaler: Any | None,
    effective_batch_items: int,
    effective_batch_item_unit: str,
    microbatch_items: int,
    accumulation_steps: int,
    normalization_unit: str,
    is_tail_batch: bool,
    optimizer_step: int,
    optimizer_step_boundary: bool,
    torch_module: Any,
) -> dict[str, Any]:
    _require(optimizer_step_boundary is True, "检查点只能保存于完整 optimizer.step() 边界")
    _require(isinstance(optimizer_step, int) and optimizer_step >= 0, "optimizer_step 必须是非负整数")
    _require(effective_batch_item_unit in NORMALIZATION_UNITS, "有效批对象单位非法")
    validate_microbatch_plan(
        effective_batch_items,
        microbatch_items,
        accumulation_steps,
        normalization_unit,
        is_tail_batch=is_tail_batch,
    )
    _require((scaler is not None) == bool(profile["grad_scaler"]), "缩放器状态与精度配置不一致")
    state = {
        "precision_profile_id": profile_id,
        "precision_profile": dict(profile),
        "scaler_state_dict": scaler.state_dict() if scaler is not None else None,
        "effective_batch_items": effective_batch_items,
        "effective_batch_item_unit": effective_batch_item_unit,
        "microbatch_items": microbatch_items,
        "accumulation_steps": accumulation_steps,
        "normalization_unit": normalization_unit,
        "is_tail_batch": is_tail_batch,
        "rng_state": capture_rng_state(torch_module),
        "optimizer_step": optimizer_step,
        "optimizer_step_boundary": True,
    }
    validate_checkpoint_runtime_state(state)
    return state


def validate_checkpoint_runtime_state(state: Mapping[str, Any]) -> None:
    _require_exact_keys(state, CHECKPOINT_REQUIRED_FIELDS, "检查点运行时状态")
    _require(state["optimizer_step_boundary"] is True, "检查点不在完整优化器步边界")
    _require(state["normalization_unit"] in NORMALIZATION_UNITS, "检查点归一化单位非法")
    _require(isinstance(state["is_tail_batch"], bool), "检查点尾批标识必须是布尔值")
    profile = state["precision_profile"]
    _require(isinstance(profile, dict), "检查点精度配置必须是对象")
    _validate_profile_definition(str(state["precision_profile_id"]), profile)
    _require((state["scaler_state_dict"] is not None) == bool(profile["grad_scaler"]), "检查点缩放器状态不符")


def reset_cuda_peak_memory(torch_module: Any, device: Any = None) -> None:
    _require(torch_module.cuda.is_available(), "重置 CUDA 峰值前必须有可用 CUDA")
    torch_module.cuda.reset_peak_memory_stats(device)


def collect_resource_receipt(
    *,
    profile_id: str,
    device_type: str,
    effective_batch_items: int,
    microbatch_items: int,
    accumulation_steps: int,
    normalization_unit: str,
    processed_valid_units: int,
    elapsed_seconds: float,
    external_process_gpu_memory_mib: float | None,
    external_measurement_source: str,
    torch_module: Any | None = None,
    device: Any = None,
) -> dict[str, Any]:
    _require(isinstance(processed_valid_units, int) and processed_valid_units >= 0, "处理有效单位数非法")
    _require(math.isfinite(elapsed_seconds) and elapsed_seconds > 0, "资源收据耗时必须为有限正数")
    _require(bool(external_measurement_source), "资源收据必须声明外部测量来源")
    if device_type == "cuda":
        _require(torch_module is not None and torch_module.cuda.is_available(), "CUDA 收据要求可用 PyTorch CUDA")
        _require(
            external_process_gpu_memory_mib is not None
            and math.isfinite(external_process_gpu_memory_mib)
            and external_process_gpu_memory_mib >= 0,
            "CUDA 收据必须包含外部进程显存",
        )
        allocated = int(torch_module.cuda.memory_allocated(device))
        reserved = int(torch_module.cuda.memory_reserved(device))
        max_allocated = int(torch_module.cuda.max_memory_allocated(device))
        max_reserved = int(torch_module.cuda.max_memory_reserved(device))
    else:
        _require(device_type in ("cpu", "mps"), "资源收据设备类型非法")
        allocated = reserved = max_allocated = max_reserved = None
    receipt = {
        "precision_profile_id": profile_id,
        "device_type": device_type,
        "effective_batch_items": effective_batch_items,
        "microbatch_items": microbatch_items,
        "accumulation_steps": accumulation_steps,
        "normalization_unit": normalization_unit,
        "cuda_memory_allocated_bytes": allocated,
        "cuda_memory_reserved_bytes": reserved,
        "cuda_max_memory_allocated_bytes": max_allocated,
        "cuda_max_memory_reserved_bytes": max_reserved,
        "external_process_gpu_memory_mib": external_process_gpu_memory_mib,
        "external_measurement_source": external_measurement_source,
        "processed_valid_units": processed_valid_units,
        "elapsed_seconds": elapsed_seconds,
        "valid_units_per_second": processed_valid_units / elapsed_seconds,
    }
    validate_resource_receipt(receipt)
    return receipt


def validate_resource_receipt(receipt: Mapping[str, Any]) -> None:
    _require_exact_keys(receipt, RESOURCE_REQUIRED_FIELDS, "资源收据")
    _require(receipt["normalization_unit"] in NORMALIZATION_UNITS, "资源收据归一化单位非法")
    _require(bool(receipt["external_measurement_source"]), "资源收据缺少外部测量来源")
    if receipt["device_type"] == "cuda":
        for key in (
            "cuda_memory_allocated_bytes",
            "cuda_memory_reserved_bytes",
            "cuda_max_memory_allocated_bytes",
            "cuda_max_memory_reserved_bytes",
            "external_process_gpu_memory_mib",
        ):
            _require(isinstance(receipt[key], (int, float)) and receipt[key] >= 0, f"CUDA 资源字段 {key} 非法")


def contract_summary(contract: Mapping[str, Any], profile_id: str | None = None) -> dict[str, Any]:
    resolved_id = profile_id or str(contract["default_profile"])
    profile = get_profile(contract, resolved_id)
    return {
        "schema_version": contract["schema_version"],
        "profile_id": resolved_id,
        "device_type": profile["device_type"],
        "compute_dtype": profile["compute_dtype"],
        "autocast": profile["autocast"],
        "grad_scaler": profile["grad_scaler"],
        "parameter_dtype": profile["parameter_dtype"],
        "optimizer_state_dtype": profile["optimizer_state_dtype"],
        "scientific_status": profile["scientific_status"],
        "torch_required_for_validation": False,
    }


def run_self_check(contract_path: Path) -> dict[str, Any]:
    contract = load_and_validate_contract(contract_path)
    full = validate_microbatch_plan(64, 4, 16, "flow", is_tail_batch=False)
    tail = validate_microbatch_plan(10, 4, 3, "sequence", is_tail_batch=True)
    validate_comparison_profiles(DEFAULT_PROFILE_ID, DEFAULT_PROFILE_ID, "structure_causal")
    validate_comparison_profiles(DEFAULT_PROFILE_ID, FP16_FALLBACK_PROFILE_ID, "engineering_observation")
    blocked_cross_profile_causal = False
    try:
        validate_comparison_profiles(DEFAULT_PROFILE_ID, FP16_FALLBACK_PROFILE_ID, "mechanism_causal")
    except ContractValidationError:
        blocked_cross_profile_causal = True
    _require(blocked_cross_profile_causal, "跨配置机制因果比较未被阻止")
    return {
        "contract": contract_summary(contract),
        "full_batch_plan": full,
        "tail_batch_plan": tail,
        "cross_profile_causal_blocked": blocked_cross_profile_causal,
        "self_check": "passed",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="验证神经训练精度、等效微批量与资源收据合同")
    parser.add_argument("--validate-profile", type=Path, help="验证指定精度合同 JSON，不要求安装 PyTorch")
    parser.add_argument("--profile-id", help="随合同验证的配置标识；默认使用 default_profile")
    parser.add_argument("--self-check", action="store_true", help="对仓库默认合同执行无 PyTorch 自检")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.validate_profile and not args.self_check:
        parser.print_help()
        return 0
    default_contract = Path(__file__).resolve().parent.parent / "configs" / "neural-precision-profiles-v1.json"
    if args.self_check:
        result = run_self_check(args.validate_profile or default_contract)
    else:
        contract = load_and_validate_contract(args.validate_profile)
        result = contract_summary(contract, args.profile_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
