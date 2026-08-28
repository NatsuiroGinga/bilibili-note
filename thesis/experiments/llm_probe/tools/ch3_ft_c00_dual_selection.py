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


SCHEMA_VERSION = "ch3-ft-c00-dual-selection-config-v1"
CHECKPOINT_SCHEMA_VERSION = "ch3-ft-candidate-unified-checkpoint-v1"
SOURCE_ARRAYS = ("X23", "y23", "I23", "M23", "E23", "T23")
EXIT_CONFIG = 2
EXIT_INPUT = 3
EXIT_RUNTIME = 4
LOGGER = logging.getLogger("ch3_ft_c00_dual_selection")


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
    require(identity.get("candidate_key") == "bare-ft-c00-dual-selection", "候选身份不符")
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
    require(config.get("model") == {
        "role": "bare_ft_transformer",
        "expected_parameter_count": 924283,
        "old_cpa_enabled": False,
        "old_elp_enabled": False,
        "old_mechanism_scaffold_present": False,
    }, "裸 FT 模型合同不符")
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


def build_model_optimizer(config: dict[str, Any], base_config: dict[str, Any], view: Any, torch_module: Any, device: Any) -> tuple[Any, Any, dict[str, Any]]:
    model = base.build_model(base_config, view.transform, input_key=config["data"]["input_candidate"])
    actual = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    require(actual == config["model"]["expected_parameter_count"], f"裸 FT 参数量不符：{actual}", EXIT_RUNTIME)
    names = tuple(name for name, _ in model.named_parameters())
    require(not any("fusion" in name or "p_log" in name for name in names), "裸 FT 含旧机制脚手架", EXIT_RUNTIME)
    model = model.to(device)
    optimizer, optimizer_receipt = base.make_optimizer(base_config, model, config["optimizer"]["candidate_key"])
    return model, optimizer, optimizer_receipt


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
    random.seed(config["training"]["seed"])
    np.random.seed(config["training"]["seed"])
    torch_module.manual_seed(config["training"]["seed"])
    if device.type == "cuda":
        torch_module.cuda.manual_seed_all(config["training"]["seed"])
        torch_module.cuda.reset_peak_memory_stats(device)
    generator = torch_module.Generator().manual_seed(config["training"]["seed"])
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
    step = training_step(
        config, base_config, model, optimizer, view, train_rows, generator, device,
        profile, precision, torch_module, positive_weight,
    )
    synchronize_device(torch_module, device)
    step_seconds = time.time() - step_started
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


def checkpoint_payload(
    config: dict[str, Any], science_receipt: dict[str, Any], runtime_receipt: dict[str, Any],
    model: Any, optimizer: Any, epoch: int, step_count: int, history: list[dict[str, Any]],
    best_flow: dict[str, Any], best_entity: dict[str, Any], generator: Any,
    torch_module: Any, device: Any, profile: dict[str, Any], input_transform_state_hash: str,
) -> dict[str, Any]:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
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
    random.seed(config["training"]["seed"])
    np.random.seed(config["training"]["seed"])
    torch_module.manual_seed(config["training"]["seed"])
    if device.type == "cuda":
        torch_module.cuda.manual_seed_all(config["training"]["seed"])
    generator = torch_module.Generator().manual_seed(config["training"]["seed"])
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
        for step_in_epoch in range(1, steps_per_epoch + 1):
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
        metrics = validation_metrics(
            config, model, view, arrays, validation_rows, device, profile, precision, torch_module
        )
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
