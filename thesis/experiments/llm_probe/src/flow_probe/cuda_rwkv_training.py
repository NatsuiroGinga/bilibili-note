"""CUDA-RWKV Raw83 训练、首步门与同身份断点。"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch
import torch.nn.functional as F

from cuda_rwkv_official_backend import LoadedExtension, load_extension, sha256_file
from flow_probe.cuda_rwkv_evaluation import evaluate_dataset
from flow_probe.cuda_rwkv_model import ModelIdentity, build_model, canonical_sha256
from flow_probe.protocol_a_raw83 import sha256_file as raw83_sha256_file
from neural_precision_runtime import (
    EffectiveBatchAccumulator,
    autocast_context,
    build_checkpoint_runtime_state,
    collect_resource_receipt,
    get_profile,
    load_and_validate_contract,
    reset_cuda_peak_memory,
    validate_microbatch_plan,
    validate_model_optimizer_fp32,
    validate_runtime_profile,
)


@dataclass(frozen=True)
class TrainingUnitSpec:
    arm: str
    adapter: str
    capacity: str
    cell: str

    @property
    def key(self) -> str:
        return f"{self.arm}-{self.adapter}-{self.capacity}-{self.cell}"


@dataclass(frozen=True)
class TrainingUnitResult:
    spec: TrainingUnitSpec
    unit_root: Path
    best_checkpoint: Path
    best_checkpoint_sha256: str
    best_epoch: int
    validation_flow_average_precision: float
    model_spec_sha256: str
    cuda_execution_identity_sha256: str
    source_metrics_path: Path
    source_metrics_sha256: str
    unit_manifest_path: Path
    unit_manifest_sha256: str


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON 顶层必须为对象：{path}")
    return value


def _artifact_entry(path: Path, root: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    root_resolved = root.resolve(strict=True)
    if path.is_symlink() or not resolved.is_relative_to(root_resolved):
        raise RuntimeError(f"单元制品路径越界或为符号链接：{path}")
    return {
        "path": str(resolved.relative_to(root_resolved)),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def _resource_samples_summary(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("CUDA-RWKV 单元缺少全程资源采样")
    gpu_values: list[float] = []
    memory_values: list[int] = []
    disk_values: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) != 4:
            continue
        try:
            gpu_values.append(float(fields[1]))
            memory_values.append(int(fields[2]))
            disk_values.append(int(fields[3]))
        except ValueError:
            continue
    if not gpu_values or not memory_values or not disk_values:
        raise RuntimeError("CUDA-RWKV 全程资源采样不含完整数值行")
    if min(gpu_values) < 0 or min(memory_values) < 0 or min(disk_values) <= 0:
        raise RuntimeError("CUDA-RWKV 全程资源采样包含非法负值或零磁盘余量")
    return {
        "sample_count": len(gpu_values),
        "gpu_process_memory_peak_mib": max(gpu_values),
        "cgroup_memory_peak_bytes": max(memory_values),
        "disk_available_minimum_kib": min(disk_values),
        "samples_file_sha256": sha256_file(path),
    }


def _write_unit_manifest(
    *,
    unit_root: Path,
    spec: TrainingUnitSpec,
    identities: Mapping[str, Any],
) -> tuple[Path, str]:
    manifest_path = unit_root / "unit-manifest.json"
    required = {
        "training-identities.json",
        "model-spec.json",
        "optimizer-groups.json",
        "first-complete-step-receipt.json",
        "checkpoints/latest.pt",
        "checkpoints/best.pt",
        "validation-history.json",
        "source-metrics.json",
        "resource-summary.json",
        "completed.json",
        "status.json",
    }
    files = sorted(
        path
        for path in unit_root.rglob("*")
        if path.is_file()
        and path != manifest_path
        and ".partial." not in path.name
    )
    observed = {str(path.relative_to(unit_root)) for path in files}
    missing = sorted(required - observed)
    if missing:
        raise RuntimeError(f"{spec.key} 单元清单缺少必需制品：{missing}")
    artifacts = [_artifact_entry(path, unit_root) for path in files]
    unsigned = {
        "schema_version": "cuda-rwkv-source-unit-manifest-v1",
        "unit": spec.key,
        "training_identity_sha256": canonical_sha256(identities),
        "required_artifacts": sorted(required),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    manifest = {**unsigned, "manifest_content_sha256": canonical_sha256(unsigned)}
    atomic_write_json(manifest_path, manifest)
    return manifest_path, sha256_file(manifest_path)


def _validate_unit_manifest(
    *,
    unit_root: Path,
    spec: TrainingUnitSpec,
    expected_identities: Mapping[str, Any],
) -> tuple[Path, str]:
    manifest_path = unit_root / "unit-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RuntimeError(f"{spec.key} 完成快路径缺少单元清单")
    manifest = load_json(manifest_path)
    unsigned = {
        key: value for key, value in manifest.items() if key != "manifest_content_sha256"
    }
    if manifest.get("manifest_content_sha256") != canonical_sha256(unsigned):
        raise RuntimeError(f"{spec.key} 单元清单内容 SHA-256 无效")
    if (
        manifest.get("unit") != spec.key
        or manifest.get("training_identity_sha256")
        != canonical_sha256(expected_identities)
    ):
        raise RuntimeError(f"{spec.key} 单元清单训练身份漂移")
    listed = set()
    for item in manifest.get("artifacts", []):
        relative = str(item["path"])
        path = unit_root / relative
        if relative in listed or not path.is_file() or path.is_symlink():
            raise RuntimeError(f"{spec.key} 单元清单制品缺失、重复或为链接：{relative}")
        listed.add(relative)
        if path.stat().st_size != int(item["bytes"]) or sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"{spec.key} 单元制品身份漂移：{relative}")
    observed = {
        str(path.relative_to(unit_root))
        for path in unit_root.rglob("*")
        if path.is_file()
        and path != manifest_path
        and ".partial." not in path.name
    }
    if listed != observed or int(manifest.get("artifact_count", -1)) != len(listed):
        raise RuntimeError(f"{spec.key} 单元制品集与清单不等")
    expected_required = {
        "training-identities.json",
        "model-spec.json",
        "optimizer-groups.json",
        "first-complete-step-receipt.json",
        "checkpoints/latest.pt",
        "checkpoints/best.pt",
        "validation-history.json",
        "source-metrics.json",
        "resource-summary.json",
        "completed.json",
        "status.json",
    }
    required = set(manifest.get("required_artifacts", []))
    if required != expected_required or not required.issubset(listed):
        raise RuntimeError(f"{spec.key} 单元清单必需制品不齐")
    if load_json(unit_root / "training-identities.json") != dict(expected_identities):
        raise RuntimeError(f"{spec.key} 训练身份文件漂移")
    first_step = load_json(unit_root / "first-complete-step-receipt.json")
    if (
        first_step.get("training_identity_sha256") != canonical_sha256(expected_identities)
        or not first_step.get("six_gradients")
        or any(
            item.get("finite") is not True or int(item.get("nonzero", 0)) <= 0
            for item in first_step.get("six_gradients", [])
        )
    ):
        raise RuntimeError(f"{spec.key} 首步六梯度收据无效")
    resource_summary = load_json(unit_root / "resource-summary.json")
    if resource_summary.get("fair_evidence") is not True:
        raise RuntimeError(f"{spec.key} 缺少完整公平资源证据")
    completed = load_json(unit_root / "completed.json")
    status = load_json(unit_root / "status.json")
    if completed.get("state") != "finished" or status.get("state") != "finished":
        raise RuntimeError(f"{spec.key} 完成收据或状态未封口")
    return manifest_path, sha256_file(manifest_path)


def _atomic_torch_save(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    torch.save(dict(payload), temporary)
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _verified_artifact_path(dataset: Any, key: str) -> Path:
    item = dataset.manifest.get("artifacts", {}).get(key)
    if not isinstance(item, dict):
        raise RuntimeError(f"Raw83 数据清单缺少训练制品：{key}")
    root = Path(dataset.manifest_path).resolve(strict=True).parent
    path = Path(item["path"])
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_relative_to(root):
        raise RuntimeError(f"Raw83 训练制品路径越界或为符号链接：{key}")
    if resolved.stat().st_size != int(item["bytes"]):
        raise RuntimeError(f"Raw83 训练制品字节数不符：{key}")
    if raw83_sha256_file(resolved) != item["sha256"]:
        raise RuntimeError(f"Raw83 训练制品 SHA-256 不符：{key}")
    return resolved


def set_random_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def make_optimizer(
    config: Mapping[str, Any], model: torch.nn.Module
) -> tuple[torch.optim.Optimizer, list[dict[str, Any]]]:
    training = config["training"]
    grouped: dict[str, list[tuple[str, torch.nn.Parameter]]] = {
        "no_decay_1x": [],
        "decay_raw_2x": [],
        "matrix_decay_1x": [],
    }
    for name, parameter in model.named_parameters():
        if name == "fusion.0.weight":
            grouped["no_decay_1x"].append((name, parameter))
        elif name.endswith(".time_mix.w0"):
            grouped["decay_raw_2x"].append((name, parameter))
        elif parameter.squeeze().ndim >= 2 and ".weight" in name:
            grouped["matrix_decay_1x"].append((name, parameter))
        else:
            grouped["no_decay_1x"].append((name, parameter))
    optimizer_groups: list[dict[str, Any]] = []
    receipt: list[dict[str, Any]] = []
    for group_name, learning_rate, weight_decay in (
        ("no_decay_1x", float(training["learning_rate"]), 0.0),
        (
            "decay_raw_2x",
            float(training["learning_rate"])
            * float(training["decay_learning_rate_scale"]),
            0.0,
        ),
        (
            "matrix_decay_1x",
            float(training["learning_rate"]),
            float(training["weight_decay"]),
        ),
    ):
        items = grouped[group_name]
        if not items:
            raise RuntimeError(f"CUDA-RWKV 优化器参数组为空：{group_name}")
        optimizer_groups.append(
            {
                "params": [parameter for _, parameter in items],
                "lr": learning_rate,
                "weight_decay": weight_decay,
            }
        )
        receipt.append(
            {
                "name": group_name,
                "parameter_names": [name for name, _ in items],
                "parameter_count": sum(value.numel() for _, value in items),
                "learning_rate": learning_rate,
                "weight_decay": weight_decay,
            }
        )
    optimizer = torch.optim.AdamW(
        optimizer_groups,
        betas=tuple(float(value) for value in training["betas"]),
        eps=float(training["epsilon"]),
    )
    return optimizer, receipt


def _external_gpu_peak_mib(path: Path) -> float:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("CUDA-RWKV 首步门缺少外部 GPU 进程显存采样")
    values: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) >= 2:
            try:
                values.append(float(fields[1]))
            except ValueError:
                continue
    if not values:
        raise RuntimeError("CUDA-RWKV 外部 GPU 显存采样不含有效数值")
    return max(values)


def _runtime_resource_check(config: Mapping[str, Any], run_root: Path) -> dict[str, Any]:
    resources = config["resources"]
    disk = shutil.disk_usage(run_root)
    disk_used_percent = (disk.total - disk.free) * 100.0 / disk.total
    free_disk_gib = disk.free / 1024**3
    if Path("/sys/fs/cgroup/memory.max").is_file():
        raw_limit = Path("/sys/fs/cgroup/memory.max").read_text(encoding="utf-8").strip()
        if raw_limit == "max":
            raise RuntimeError("CUDA-RWKV 运行门无法读取 cgroup 主存上限")
        memory_limit = int(raw_limit)
        memory_current = int(
            Path("/sys/fs/cgroup/memory.current").read_text(encoding="utf-8").strip()
        )
    elif Path("/sys/fs/cgroup/memory/memory.limit_in_bytes").is_file():
        memory_limit = int(
            Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")
            .read_text(encoding="utf-8")
            .strip()
        )
        memory_current = int(
            Path("/sys/fs/cgroup/memory/memory.usage_in_bytes")
            .read_text(encoding="utf-8")
            .strip()
        )
    else:
        raise RuntimeError("CUDA-RWKV 运行门缺少 cgroup 主存计量")
    available_memory_gib = max(memory_limit - memory_current, 0) / 1024**3
    receipt = {
        "schema_version": "cuda-rwkv-runtime-resource-gate-v1",
        "disk_used_percent": disk_used_percent,
        "free_disk_gib": free_disk_gib,
        "cgroup_memory_limit_bytes": memory_limit,
        "cgroup_memory_current_bytes": memory_current,
        "cgroup_available_memory_gib": available_memory_gib,
    }
    stop = (
        disk_used_percent >= float(resources["stop_disk_used_percent"])
        or free_disk_gib < float(resources["stop_free_disk_gib"])
        or available_memory_gib
        < float(resources["stop_available_cgroup_memory_gib"])
    )
    warning = (
        disk_used_percent >= float(resources["notify_disk_used_percent"])
        or free_disk_gib < float(resources["notify_free_disk_gib"])
    )
    receipt["warning"] = warning
    receipt["stop_after_complete_checkpoint"] = stop
    return receipt


def _parameter_snapshots(model: Any) -> dict[str, Any]:
    snapshots: dict[str, Any] = {}
    groups = model.module_parameter_groups()
    for name, parameters in groups.items():
        if parameters:
            snapshots[name] = [value.detach().clone() for value in parameters]
    channels = model.fusion[0].weight.shape[1] // 2
    snapshots["causal_prefix_slice"] = model.fusion[0].weight[
        :, channels:
    ].detach().clone()
    snapshots["entity_pooling_scalar"] = model.p_log.detach().clone()
    return snapshots


def _parameter_update_receipt(model: Any, before: Mapping[str, Any]) -> dict[str, Any]:
    receipt: dict[str, Any] = {}
    groups = model.module_parameter_groups()
    for name, previous_values in before.items():
        if name in {"causal_prefix_slice", "entity_pooling_scalar"}:
            continue
        parameters = groups[name]
        maximum = max(
            float((current.detach() - previous).abs().max().item())
            for current, previous in zip(parameters, previous_values, strict=True)
        )
        finite = all(bool(torch.isfinite(current).all().item()) for current in parameters)
        receipt[name] = {"finite": finite, "maximum_absolute_update": maximum}
        if not finite or maximum == 0.0:
            raise RuntimeError(f"CUDA-RWKV 首步模块未发生有限更新：{name}")
    channels = model.fusion[0].weight.shape[1] // 2
    causal_update = float(
        (
            model.fusion[0].weight[:, channels:].detach()
            - before["causal_prefix_slice"]
        )
        .abs()
        .max()
        .item()
    )
    pooling_update = float(
        (model.p_log.detach() - before["entity_pooling_scalar"]).abs().item()
    )
    receipt["causal_prefix_module"] = {
        "enabled": model.use_causal_prefix,
        "maximum_absolute_update": causal_update,
    }
    receipt["learned_entity_pooling_module"] = {
        "enabled": model.use_learned_entity_pooling,
        "maximum_absolute_update": pooling_update,
    }
    if model.use_causal_prefix != (causal_update > 0.0):
        raise RuntimeError("CUDA-RWKV 因果前缀模块首步更新与四格位不符")
    if model.use_learned_entity_pooling != (pooling_update > 0.0):
        raise RuntimeError("CUDA-RWKV 实体池化模块首步更新与四格位不符")
    return receipt


def _six_gradient_receipt(model: Any) -> list[dict[str, Any]]:
    if not model.last_kernel_inputs:
        raise RuntimeError("CUDA-RWKV 首步门未捕获核输入")
    receipt: list[dict[str, Any]] = []
    names = ("r", "w", "k", "v", "a", "b")
    for layer_index, tensors in enumerate(model.last_kernel_inputs):
        if len(tensors) != 6:
            raise RuntimeError("CUDA-RWKV 块未返回六个核输入")
        for name, tensor in zip(names, tensors, strict=True):
            gradient = tensor.grad
            if gradient is None:
                raise RuntimeError(f"CUDA-RWKV 第 {layer_index} 层 {name} 梯度缺失")
            finite = bool(torch.isfinite(gradient).all().item())
            nonzero = int(torch.count_nonzero(gradient).item())
            if gradient.dtype != torch.bfloat16 or not finite or nonzero == 0:
                raise RuntimeError(
                    f"CUDA-RWKV 第 {layer_index} 层 {name} 梯度精度、有限性或非零门失败"
                )
            receipt.append(
                {
                    "layer": layer_index,
                    "input": name,
                    "dtype": str(gradient.dtype),
                    "shape": list(gradient.shape),
                    "finite": finite,
                    "nonzero": nonzero,
                    "maximum_absolute": float(gradient.float().abs().max().item()),
                }
            )
    return receipt


def _restore_rng_state(state: Mapping[str, Any]) -> None:
    random.setstate(state["python_random"])
    torch.set_rng_state(state["torch_cpu"])
    if state.get("torch_cuda_all") is not None:
        torch.cuda.set_rng_state_all(state["torch_cuda_all"])
    if state.get("numpy_random") is not None:
        np.random.set_state(state["numpy_random"])


def _checkpoint_payload(
    *,
    model: Any,
    optimizer: Any,
    scheduler: Any,
    runtime_state: Mapping[str, Any],
    sampler_state: Mapping[str, Any],
    identities: Mapping[str, Any],
    epoch: int,
    optimizer_step: int,
    step_in_epoch: int,
    validation_history: Sequence[Mapping[str, Any]],
    best_epoch: int | None,
    best_flow_ap: float | None,
    resource_state: Mapping[str, Any],
    completed_unit_keys: Sequence[str],
    progress: Mapping[str, Any],
    first_step_receipt_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "cuda-rwkv-complete-step-checkpoint-v1",
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "runtime_state": dict(runtime_state),
        "sampler_state": dict(sampler_state),
        "identities": dict(identities),
        "epoch": epoch,
        "optimizer_step": optimizer_step,
        "step_in_epoch": step_in_epoch,
        "validation_history": list(validation_history),
        "best_epoch": best_epoch,
        "best_flow_average_precision": best_flow_ap,
        "resource_state": dict(resource_state),
        "swanlab_publish_state": "not_initialized_until_final_aggregate",
        "failure_count": 0,
        "completed_unit_keys": list(completed_unit_keys),
        "progress": dict(progress),
        "first_step_receipt_sha256": first_step_receipt_sha256,
        "optimizer_step_boundary": True,
    }


def _load_checkpoint(
    path: Path,
    *,
    model: Any,
    optimizer: Any,
    scheduler: Any,
    expected_identities: Mapping[str, Any],
    sampler: np.random.Generator,
) -> dict[str, Any]:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if checkpoint.get("schema_version") != "cuda-rwkv-complete-step-checkpoint-v1":
        raise RuntimeError("CUDA-RWKV 断点模式不符")
    if checkpoint.get("optimizer_step_boundary") is not True:
        raise RuntimeError("CUDA-RWKV 断点不在完整优化步边界")
    if checkpoint.get("identities") != dict(expected_identities):
        raise RuntimeError("CUDA-RWKV 断点的 CUDA、数据、模型、配置或精度身份漂移")
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
    _restore_rng_state(checkpoint["runtime_state"]["rng_state"])
    sampler.bit_generator.state = checkpoint["sampler_state"]
    return checkpoint


def _flow_validation_average_precision(
    *,
    model: Any,
    dataset: Any,
    label_stage_token: str,
    batch_sequences: int,
    device: torch.device,
) -> float:
    rows = np.asarray(
        np.load(
            _verified_artifact_path(dataset, "validation_rows"),
            mmap_mode="r",
            allow_pickle=False,
        ),
        dtype=np.int64,
    )
    resolver = dataset.open_label_resolver(label_stage_token)
    labels: list[np.ndarray] = []
    probabilities: list[np.ndarray] = []
    model.eval()
    with torch.inference_mode():
        for start in range(0, rows.size, batch_sequences):
            batch = dataset.gather_sequences(rows[start : start + batch_sequences])
            features = torch.as_tensor(
                batch["features"], dtype=torch.float32, device=device
            )
            valid = torch.as_tensor(
                batch["valid_mask"], dtype=torch.bool, device=device
            )
            logits = model(features, valid)
            mask = np.asarray(batch["valid_mask"], dtype=bool)
            probabilities.append(torch.sigmoid(logits.float()).cpu().numpy()[mask])
            labels.append(
                resolver.resolve(np.asarray(batch["raw_row_indices"])[mask])
            )
    from sklearn.metrics import average_precision_score

    return float(
        average_precision_score(np.concatenate(labels), np.concatenate(probabilities))
    )


def _identity_bundle(
    *,
    config: Mapping[str, Any],
    config_path: Path,
    dependency_closure_path: Path,
    dataset: Any,
    model_identity: ModelIdentity,
    unit_spec: TrainingUnitSpec,
    extension: LoadedExtension,
) -> dict[str, Any]:
    model_spec = {**model_identity.spec, "view": unit_spec.arm}
    model_spec_sha256 = canonical_sha256(model_spec)
    return {
        "schema_version": "cuda-rwkv-training-identity-bundle-v1",
        "config_sha256": sha256_file(config_path),
        "dependency_closure_sha256": sha256_file(dependency_closure_path),
        "dataset_manifest_sha256": raw83_sha256_file(Path(dataset.manifest_path)),
        "dataset_receipt_sha256": canonical_sha256(dataset.receipt()),
        "field_list_sha256": dataset.manifest["field_list_sha256"],
        "sequence_split_state_hash": dataset.manifest["sequence_split_state_hash"],
        "transform_state_hash": dataset.manifest["transform_state_hashes"][unit_spec.arm],
        "view_content_sha256": dataset.manifest["view_content_sha256"][unit_spec.arm],
        "model_spec": model_spec,
        "model_spec_sha256": model_spec_sha256,
        "precision_profile_id": config["precision"]["profile_id"],
        "precision_contract_sha256": sha256_file(Path(config["precision"]["contract_path"])),
        "evaluation_code_sha256": sha256_file(
            Path(config["dependencies"]["evaluation_code_path"])
        ),
        "cuda_execution_identity_sha256": extension.identity[
            "cuda_execution_identity_sha256"
        ],
        "cuda_execution_identity": extension.identity,
        "unit": {
            "arm": unit_spec.arm,
            "adapter": unit_spec.adapter,
            "capacity": unit_spec.capacity,
            "cell": unit_spec.cell,
        },
    }


def train_unit(
    *,
    config: Mapping[str, Any],
    config_path: Path,
    dependency_closure_path: Path,
    train_dataset: Any,
    validation_dataset: Any,
    train_label_stage_token: str,
    validation_label_stage_token: str,
    spec: TrainingUnitSpec,
    run_root: Path,
    resume: bool,
) -> TrainingUnitResult:
    """从随机初始化训练一个源年单元，或从同 CUDA 身份断点恢复。"""

    training = config["training"]
    unit_root = Path(run_root) / "source-units" / spec.key
    latest_checkpoint = unit_root / "checkpoints" / "latest.pt"
    best_checkpoint = unit_root / "checkpoints" / "best.pt"
    completed_path = unit_root / "completed.json"
    identities_path = unit_root / "training-identities.json"
    model_spec_path = unit_root / "model-spec.json"
    optimizer_groups_path = unit_root / "optimizer-groups.json"
    first_step_receipt_path = unit_root / "first-complete-step-receipt.json"
    volatile_progress_path = unit_root / "volatile-progress.json"
    completed = load_json(completed_path) if completed_path.is_file() else None
    if unit_root.exists() and not resume and completed is None:
        existing = [path for path in unit_root.rglob("*") if path.is_file()]
        if existing:
            raise RuntimeError(f"{spec.key} 已有未完成制品，必须显式续训")
    unit_root.mkdir(parents=True, exist_ok=True)
    set_random_seed(int(training["seed"]))
    device = torch.device("cuda")
    extension = load_extension(
        spec.capacity,
        build_root=Path(run_root) / "build" / spec.capacity,
        expected_environment=config["cuda"]["environment"],
    )
    model, model_identity = build_model(
        config,
        adapter_key=spec.adapter,
        capacity_key=spec.capacity,
        cell=spec.cell,
        build_root=Path(run_root) / "build",
    )
    model.to(device)
    optimizer, optimizer_group_receipt = make_optimizer(config, model)
    total_steps = int(training["epochs"]) * int(training["steps_per_epoch"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=total_steps, eta_min=float(training["minimum_learning_rate"])
    )
    precision_contract = load_and_validate_contract(
        Path(config["precision"]["contract_path"])
    )
    profile_id = str(config["precision"]["profile_id"])
    profile = validate_runtime_profile(
        precision_contract, profile_id, "cuda", torch
    )
    if get_profile(precision_contract, profile_id) != profile or profile["grad_scaler"]:
        raise RuntimeError("CUDA-RWKV 只允许冻结 BF16 且不创建缩放器")
    validate_model_optimizer_fp32(model, optimizer, torch)
    effective_batch = int(training["effective_batch_sequences"])
    microbatch = int(training["microbatch_sequences"])
    accumulation = int(training["accumulation_steps"])
    validate_microbatch_plan(
        effective_batch,
        microbatch,
        accumulation,
        "flow",
        is_tail_batch=False,
    )
    identities = _identity_bundle(
        config=config,
        config_path=config_path,
        dependency_closure_path=dependency_closure_path,
        dataset=train_dataset,
        model_identity=model_identity,
        unit_spec=spec,
        extension=extension,
    )
    training_identity_sha256 = canonical_sha256(identities)
    existing_files = [path for path in unit_root.rglob("*") if path.is_file()]
    if identities_path.is_file():
        if load_json(identities_path) != identities:
            raise RuntimeError(f"{spec.key} 现有单元与当前 CUDA 或训练身份漂移")
    elif existing_files:
        raise RuntimeError(f"{spec.key} 存在制品但缺少可先验的训练身份")
    else:
        atomic_write_json(identities_path, identities)
    expected_model_spec = identities["model_spec"]
    expected_optimizer_groups = {"groups": optimizer_group_receipt}
    for path, expected, name in (
        (model_spec_path, expected_model_spec, "模型规格"),
        (optimizer_groups_path, expected_optimizer_groups, "优化器分组"),
    ):
        if path.is_file():
            if load_json(path) != expected:
                raise RuntimeError(f"{spec.key} 现有{name}与当前身份漂移")
        else:
            atomic_write_json(path, expected)
    if completed is not None:
        if not identities_path.is_file():
            raise RuntimeError(f"{spec.key} 完成收据缺少训练身份")
        source_metrics_path = unit_root / "source-metrics.json"
        if not best_checkpoint.is_file() or not source_metrics_path.is_file():
            raise RuntimeError(f"{spec.key} 完成收据存在但检查点或源指标缺失")
        if sha256_file(best_checkpoint) != completed["best_checkpoint_sha256"]:
            raise RuntimeError(f"{spec.key} 已完成检查点 SHA-256 漂移")
        if sha256_file(source_metrics_path) != completed["source_metrics_sha256"]:
            raise RuntimeError(f"{spec.key} 已完成源指标 SHA-256 漂移")
        unit_manifest_path, unit_manifest_sha256 = _validate_unit_manifest(
            unit_root=unit_root,
            spec=spec,
            expected_identities=identities,
        )
        return TrainingUnitResult(
            spec=spec,
            unit_root=unit_root,
            best_checkpoint=best_checkpoint,
            best_checkpoint_sha256=str(completed["best_checkpoint_sha256"]),
            best_epoch=int(completed["best_epoch"]),
            validation_flow_average_precision=float(
                completed["validation_flow_average_precision"]
            ),
            model_spec_sha256=str(completed["model_spec_sha256"]),
            cuda_execution_identity_sha256=str(
                completed["cuda_execution_identity_sha256"]
            ),
            source_metrics_path=source_metrics_path,
            source_metrics_sha256=str(completed["source_metrics_sha256"]),
            unit_manifest_path=unit_manifest_path,
            unit_manifest_sha256=unit_manifest_sha256,
        )
    train_rows = np.asarray(
        np.load(
            _verified_artifact_path(train_dataset, "train_rows"),
            mmap_mode="r",
            allow_pickle=False,
        ),
        dtype=np.int64,
    )
    weight_aggregate = train_dataset.training_weight_aggregate()
    flow_positive_weight = float(weight_aggregate["train_flow_positive_weight"])
    sequence_positive_weight = float(
        weight_aggregate["train_sequence_positive_weight"]
    )
    resolver = train_dataset.open_label_resolver(train_label_stage_token)
    sampler = np.random.default_rng(int(training["seed"]))
    start_epoch = 1
    step_in_epoch = 0
    optimizer_step = 0
    validation_history: list[dict[str, Any]] = []
    best_epoch: int | None = None
    best_flow_ap: float | None = None
    progress: dict[str, Any] = {
        "training_seconds_total": 0.0,
        "selection_validation_seconds": 0.0,
        "source_evaluation_seconds": 0.0,
        "checkpoint_io_seconds": 0.0,
        "processed_valid_flows_total": 0,
        "effective_processed_valid_flows": 0,
        "resume_count": 0,
        "repeated_optimizer_steps": 0,
    }
    prior_volatile = (
        load_json(volatile_progress_path) if volatile_progress_path.is_file() else None
    )
    if prior_volatile is not None and prior_volatile.get(
        "training_identity_sha256"
    ) != training_identity_sha256:
        raise RuntimeError(f"{spec.key} 断点前进度收据身份漂移")
    if first_step_receipt_path.is_file():
        existing_first_step = load_json(first_step_receipt_path)
        if existing_first_step.get("training_identity_sha256") != training_identity_sha256:
            raise RuntimeError(f"{spec.key} 旧首步六梯度收据身份漂移")
    if latest_checkpoint.is_file():
        if not resume:
            raise RuntimeError(f"{spec.key} 发现断点但未显式启用续训")
        if not first_step_receipt_path.is_file():
            raise RuntimeError(f"{spec.key} 有断点但缺少首步六梯度收据")
        checkpoint = _load_checkpoint(
            latest_checkpoint,
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            expected_identities=identities,
            sampler=sampler,
        )
        optimizer_step = int(checkpoint["optimizer_step"])
        completed_epoch = int(checkpoint["epoch"])
        step_in_epoch = int(checkpoint["step_in_epoch"])
        validation_history = list(checkpoint["validation_history"])
        best_epoch = checkpoint["best_epoch"]
        best_flow_ap = checkpoint["best_flow_average_precision"]
        if checkpoint.get("first_step_receipt_sha256") != sha256_file(
            first_step_receipt_path
        ):
            raise RuntimeError(f"{spec.key} 断点未绑定当前首步六梯度收据")
        checkpoint_progress = checkpoint.get("progress")
        if not isinstance(checkpoint_progress, dict):
            raise RuntimeError(f"{spec.key} 断点缺少累计进度")
        progress.update(checkpoint_progress)
        progress["resume_count"] = int(progress["resume_count"]) + 1
        if prior_volatile is not None:
            repeated = max(
                int(prior_volatile.get("optimizer_step", optimizer_step))
                - optimizer_step,
                0,
            )
            progress["repeated_optimizer_steps"] = int(
                progress["repeated_optimizer_steps"]
            ) + repeated
            progress["training_seconds_total"] = max(
                float(progress["training_seconds_total"]),
                float(prior_volatile.get("training_seconds_total", 0.0)),
            )
            progress["processed_valid_flows_total"] = max(
                int(progress["processed_valid_flows_total"]),
                int(prior_volatile.get("processed_valid_flows_total", 0)),
            )
        epoch_already_validated = bool(
            validation_history
            and int(validation_history[-1].get("epoch", -1)) == completed_epoch
        )
        if step_in_epoch == int(training["steps_per_epoch"]) and epoch_already_validated:
            start_epoch = completed_epoch + 1
            step_in_epoch = 0
        else:
            start_epoch = completed_epoch
    elif resume:
        if first_step_receipt_path.is_file():
            old_first_step_sha256 = sha256_file(first_step_receipt_path)
            first_step_receipt_path.unlink()
            atomic_write_json(
                unit_root / "precheckpoint-first-step-replay.json",
                {
                    "schema_version": "cuda-rwkv-precheckpoint-first-step-replay-v1",
                    "unit": spec.key,
                    "training_identity_sha256": training_identity_sha256,
                    "removed_first_step_receipt_sha256": old_first_step_sha256,
                    "reason": "no_complete_twenty_step_checkpoint",
                },
            )
        if prior_volatile is not None:
            progress["training_seconds_total"] = float(
                prior_volatile.get("training_seconds_total", 0.0)
            )
            progress["processed_valid_flows_total"] = int(
                prior_volatile.get("processed_valid_flows_total", 0)
            )
            progress["repeated_optimizer_steps"] = int(
                prior_volatile.get("optimizer_step", 0)
            )
        progress["resume_count"] = int(progress["resume_count"]) + 1
        atomic_write_json(
            unit_root / "resume-from-random-initialization.json",
            {
                "schema_version": "cuda-rwkv-resume-before-first-checkpoint-v1",
                "unit": spec.key,
                "reason": "no_complete_twenty_step_checkpoint",
                "replayed_optimizer_steps_from": int(
                    progress["repeated_optimizer_steps"]
                ),
                "training_identity_sha256": training_identity_sha256,
            },
        )
    reset_cuda_peak_memory(torch, device)
    atomic_write_json(
        unit_root / "status.json",
        {"state": "running", "unit": spec.key, "optimizer_step": optimizer_step},
    )
    start_time = time.monotonic()
    for epoch in range(start_epoch, int(training["epochs"]) + 1):
        model.train()
        epoch_step_start = step_in_epoch if epoch == start_epoch else 0
        for local_step in range(epoch_step_start, int(training["steps_per_epoch"])):
            step_started = time.monotonic()
            batch_rows = sampler.choice(
                train_rows, size=effective_batch, replace=False
            ).astype(np.int64, copy=False)
            batch = train_dataset.gather_sequences(batch_rows)
            mask_numpy = np.asarray(batch["valid_mask"], dtype=bool)
            valid_flow_count = int(np.count_nonzero(mask_numpy))
            if valid_flow_count <= 0:
                raise RuntimeError("CUDA-RWKV 有效批不含有效流")
            accumulator = EffectiveBatchAccumulator(
                valid_flow_count,
                "flow",
                torch,
                expected_microbatches=accumulation,
            )
            accumulator.begin(optimizer)
            first_step = optimizer_step == 0 and not first_step_receipt_path.exists()
            before_parameters = _parameter_snapshots(model) if first_step else None
            loss_sum_value = 0.0
            for micro_index in range(accumulation):
                micro_start = micro_index * microbatch
                micro_stop = micro_start + microbatch
                micro_features = torch.as_tensor(
                    batch["features"][micro_start:micro_stop],
                    dtype=torch.float32,
                    device=device,
                )
                micro_valid = torch.as_tensor(
                    mask_numpy[micro_start:micro_stop],
                    dtype=torch.bool,
                    device=device,
                )
                micro_raw_rows = np.asarray(
                    batch["raw_row_indices"][micro_start:micro_stop]
                )
                micro_labels_numpy = np.zeros(micro_valid.shape, dtype=np.float32)
                micro_labels_numpy[mask_numpy[micro_start:micro_stop]] = resolver.resolve(
                    micro_raw_rows[mask_numpy[micro_start:micro_stop]]
                )
                micro_labels = torch.as_tensor(
                    micro_labels_numpy, dtype=torch.float32, device=device
                )
                capture = first_step and micro_index == accumulation - 1
                with autocast_context(profile, "cuda", torch):
                    logits = model(
                        micro_features,
                        micro_valid,
                        capture_kernel_inputs=capture,
                    )
                with torch.amp.autocast("cuda", enabled=False):
                    flow_losses = F.binary_cross_entropy_with_logits(
                        logits.float(),
                        micro_labels,
                        pos_weight=torch.tensor(
                            flow_positive_weight, device=device, dtype=torch.float32
                        ),
                        reduction="none",
                    )
                    loss_sum = flow_losses[micro_valid].sum()
                    if model.use_learned_entity_pooling:
                        probabilities = torch.sigmoid(logits.float())
                        entity_probabilities = model.pool_entity_probabilities(
                            probabilities, micro_valid
                        )
                        sequence_labels = (
                            micro_labels.masked_fill(~micro_valid, 0.0).amax(dim=1)
                        )
                        entity_loss = F.binary_cross_entropy(
                            entity_probabilities.clamp(1e-7, 1.0 - 1e-7),
                            sequence_labels,
                            weight=torch.where(
                                sequence_labels > 0,
                                torch.tensor(sequence_positive_weight, device=device),
                                torch.tensor(1.0, device=device),
                            ),
                            reduction="sum",
                        )
                        loss_sum = loss_sum + float(
                            training["entity_loss_weight"]
                        ) * entity_loss
                valid_in_micro = int(micro_valid.sum().item())
                accumulator.backward(loss_sum.float(), valid_in_micro, scaler=None)
                loss_sum_value += float(loss_sum.detach().item())
            gradient_norm = accumulator.finish(
                model.parameters(),
                optimizer,
                torch,
                max_grad_norm=float(training["gradient_clip_norm"]),
                scaler=None,
            )
            optimizer_step += 1
            scheduler.step()
            validate_model_optimizer_fp32(model, optimizer, torch)
            step_seconds = max(time.monotonic() - step_started, 0.0)
            progress["training_seconds_total"] = float(
                progress["training_seconds_total"]
            ) + step_seconds
            progress["processed_valid_flows_total"] = int(
                progress["processed_valid_flows_total"]
            ) + valid_flow_count
            progress["effective_processed_valid_flows"] = int(
                progress["effective_processed_valid_flows"]
            ) + valid_flow_count
            if first_step:
                if before_parameters is None:
                    raise AssertionError("CUDA-RWKV 首步参数快照缺失")
                six_gradients = _six_gradient_receipt(model)
                updates = _parameter_update_receipt(model, before_parameters)
                elapsed = max(time.monotonic() - start_time, 1e-9)
                resource_receipt = collect_resource_receipt(
                    profile_id=profile_id,
                    device_type="cuda",
                    effective_batch_items=effective_batch,
                    microbatch_items=microbatch,
                    accumulation_steps=accumulation,
                    normalization_unit="flow",
                    processed_valid_units=valid_flow_count,
                    elapsed_seconds=elapsed,
                    external_process_gpu_memory_mib=_external_gpu_peak_mib(
                        Path(config["paths"]["resource_samples"])
                    ),
                    external_measurement_source=str(
                        config["paths"]["resource_samples"]
                    ),
                    torch_module=torch,
                    device=device,
                )
                atomic_write_json(
                    first_step_receipt_path,
                    {
                        "schema_version": "cuda-rwkv-first-complete-step-receipt-v1",
                        "unit": spec.key,
                        "training_identity_sha256": training_identity_sha256,
                        "optimizer_step": optimizer_step,
                        "loss_sum": loss_sum_value,
                        "normalized_loss": loss_sum_value / valid_flow_count,
                        "gradient_norm_before_clip": float(gradient_norm.item()),
                        "gradient_clip_norm": float(training["gradient_clip_norm"]),
                        "gradient_norm_after_clip_upper_bound": min(
                            float(gradient_norm.item()),
                            float(training["gradient_clip_norm"]),
                        ),
                        "six_gradients": six_gradients,
                        "parameter_updates": updates,
                        "precision_profile_id": profile_id,
                        "parameter_dtype": "float32",
                        "optimizer_state_dtype": "float32",
                        "kernel_input_output_gradient_dtype": "bfloat16",
                        "kernel_state_dtype": "float32",
                        "effective_batch_receipt": accumulator.receipt(),
                        "resource_receipt": resource_receipt,
                    },
                )
            atomic_write_json(
                volatile_progress_path,
                {
                    "schema_version": "cuda-rwkv-volatile-progress-v1",
                    "unit": spec.key,
                    "training_identity_sha256": training_identity_sha256,
                    "epoch": epoch,
                    "step_in_epoch": local_step + 1,
                    "optimizer_step": optimizer_step,
                    **progress,
                },
            )
            checkpoint_due = optimizer_step % int(
                training["checkpoint_interval_optimizer_steps"]
            ) == 0
            if checkpoint_due:
                resource_gate = _runtime_resource_check(config, unit_root)
                runtime_state = build_checkpoint_runtime_state(
                    profile_id=profile_id,
                    profile=profile,
                    scaler=None,
                    effective_batch_items=effective_batch,
                    effective_batch_item_unit="sequence",
                    microbatch_items=microbatch,
                    accumulation_steps=accumulation,
                    normalization_unit="flow",
                    is_tail_batch=False,
                    optimizer_step=optimizer_step,
                    optimizer_step_boundary=True,
                    torch_module=torch,
                )
                payload = _checkpoint_payload(
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    runtime_state=runtime_state,
                    sampler_state=sampler.bit_generator.state,
                    identities=identities,
                    epoch=epoch,
                    optimizer_step=optimizer_step,
                    step_in_epoch=local_step + 1,
                    validation_history=validation_history,
                    best_epoch=best_epoch,
                    best_flow_ap=best_flow_ap,
                    resource_state=resource_gate,
                    completed_unit_keys=sorted(
                        path.parent.name
                        for path in unit_root.parent.glob("*/completed.json")
                    ),
                    progress=progress,
                    first_step_receipt_sha256=sha256_file(
                        first_step_receipt_path
                    ),
                )
                checkpoint_started = time.monotonic()
                _atomic_torch_save(latest_checkpoint, payload)
                progress["checkpoint_io_seconds"] = float(
                    progress["checkpoint_io_seconds"]
                ) + max(time.monotonic() - checkpoint_started, 0.0)
                atomic_write_json(
                    unit_root / "status.json",
                    {
                        "state": "running",
                        "unit": spec.key,
                        "epoch": epoch,
                        "step_in_epoch": local_step + 1,
                        "optimizer_step": optimizer_step,
                        "latest_checkpoint_sha256": sha256_file(latest_checkpoint),
                    },
                )
                if resource_gate["warning"]:
                    atomic_write_json(
                        unit_root / "resource-warning.json", resource_gate
                    )
                if resource_gate["stop_after_complete_checkpoint"]:
                    atomic_write_json(
                        unit_root / "status.json",
                        {
                            "state": "interrupted-resource-gate",
                            "unit": spec.key,
                            "epoch": epoch,
                            "step_in_epoch": local_step + 1,
                            "optimizer_step": optimizer_step,
                            "latest_checkpoint_sha256": sha256_file(
                                latest_checkpoint
                            ),
                            "resource_gate": resource_gate,
                        },
                    )
                    raise RuntimeError(
                        "CUDA-RWKV 已在最近完整断点后因资源门停止"
                    )
        validation_started = time.monotonic()
        validation_flow_ap = _flow_validation_average_precision(
            model=model,
            dataset=validation_dataset,
            label_stage_token=validation_label_stage_token,
            batch_sequences=int(config["evaluation"]["batch_sequences"]),
            device=device,
        )
        progress["selection_validation_seconds"] = float(
            progress["selection_validation_seconds"]
        ) + max(time.monotonic() - validation_started, 0.0)
        history_item = {
            "epoch": epoch,
            "optimizer_step": optimizer_step,
            "flow_average_precision": validation_flow_ap,
        }
        validation_history.append(history_item)
        if best_flow_ap is None or validation_flow_ap > best_flow_ap:
            best_flow_ap = validation_flow_ap
            best_epoch = epoch
        runtime_state = build_checkpoint_runtime_state(
            profile_id=profile_id,
            profile=profile,
            scaler=None,
            effective_batch_items=effective_batch,
            effective_batch_item_unit="sequence",
            microbatch_items=microbatch,
            accumulation_steps=accumulation,
            normalization_unit="flow",
            is_tail_batch=False,
            optimizer_step=optimizer_step,
            optimizer_step_boundary=True,
            torch_module=torch,
        )
        resource_gate = _runtime_resource_check(config, unit_root)
        payload = _checkpoint_payload(
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            runtime_state=runtime_state,
            sampler_state=sampler.bit_generator.state,
            identities=identities,
            epoch=epoch,
            optimizer_step=optimizer_step,
            step_in_epoch=int(training["steps_per_epoch"]),
            validation_history=validation_history,
            best_epoch=best_epoch,
            best_flow_ap=best_flow_ap,
            resource_state=resource_gate,
            completed_unit_keys=sorted(
                path.parent.name
                for path in unit_root.parent.glob("*/completed.json")
            ),
            progress=progress,
            first_step_receipt_sha256=sha256_file(first_step_receipt_path),
        )
        checkpoint_started = time.monotonic()
        _atomic_torch_save(latest_checkpoint, payload)
        if best_epoch == epoch:
            _atomic_torch_save(best_checkpoint, payload)
        progress["checkpoint_io_seconds"] = float(
            progress["checkpoint_io_seconds"]
        ) + max(time.monotonic() - checkpoint_started, 0.0)
        atomic_write_json(unit_root / "validation-history.json", {"history": validation_history})
        atomic_write_json(
            volatile_progress_path,
            {
                "schema_version": "cuda-rwkv-volatile-progress-v1",
                "unit": spec.key,
                "training_identity_sha256": training_identity_sha256,
                "epoch": epoch,
                "step_in_epoch": int(training["steps_per_epoch"]),
                "optimizer_step": optimizer_step,
                **progress,
            },
        )
        if resource_gate["warning"]:
            atomic_write_json(unit_root / "resource-warning.json", resource_gate)
        if resource_gate["stop_after_complete_checkpoint"]:
            atomic_write_json(
                unit_root / "status.json",
                {
                    "state": "interrupted-resource-gate",
                    "unit": spec.key,
                    "epoch": epoch,
                    "step_in_epoch": int(training["steps_per_epoch"]),
                    "optimizer_step": optimizer_step,
                    "latest_checkpoint_sha256": sha256_file(latest_checkpoint),
                    "resource_gate": resource_gate,
                },
            )
            raise RuntimeError(
                "CUDA-RWKV 已在轮末完整断点后因资源门停止"
            )
        step_in_epoch = 0
    if best_epoch is None or best_flow_ap is None or not best_checkpoint.is_file():
        raise RuntimeError(f"{spec.key} 训练完成但未封印验证最佳轮次")
    _load_checkpoint(
        best_checkpoint,
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        expected_identities=identities,
        sampler=sampler,
    )
    source_evaluation_started = time.monotonic()
    source_metrics = evaluate_dataset(
        model=model,
        dataset=validation_dataset,
        purpose="validate",
        label_stage_token=validation_label_stage_token,
        batch_sequences=int(config["evaluation"]["batch_sequences"]),
        device=device,
    )
    source_evaluation_seconds = max(
        time.monotonic() - source_evaluation_started, 0.0
    )
    progress["source_evaluation_seconds"] = float(
        progress["source_evaluation_seconds"]
    ) + source_evaluation_seconds
    first_step_receipt = load_json(first_step_receipt_path)
    sampled_resources = _resource_samples_summary(
        Path(config["paths"]["resource_samples"])
    )
    training_seconds = float(progress["training_seconds_total"])
    resource_summary = {
        "schema_version": "cuda-rwkv-source-unit-resource-summary-v1",
        "unit": spec.key,
        "training_identity_sha256": training_identity_sha256,
        "training_seconds": training_seconds,
        "selection_validation_seconds": float(
            progress["selection_validation_seconds"]
        ),
        "source_evaluation_seconds": float(
            progress["source_evaluation_seconds"]
        ),
        "pure_inference_seconds": float(progress["source_evaluation_seconds"]),
        "checkpoint_io_seconds": float(progress["checkpoint_io_seconds"]),
        "processed_valid_flows_total": int(
            progress["processed_valid_flows_total"]
        ),
        "effective_processed_valid_flows": int(
            progress["effective_processed_valid_flows"]
        ),
        "effective_training_flow_throughput_per_second": (
            None
            if training_seconds <= 0
            else int(progress["effective_processed_valid_flows"])
            / training_seconds
        ),
        "resume_count": int(progress["resume_count"]),
        "repeated_optimizer_steps": int(progress["repeated_optimizer_steps"]),
        "optimizer_steps": optimizer_step,
        "checkpoint_interval_optimizer_steps": int(
            training["checkpoint_interval_optimizer_steps"]
        ),
        "latest_checkpoint_bytes": latest_checkpoint.stat().st_size,
        "best_checkpoint_bytes": best_checkpoint.stat().st_size,
        "retained_checkpoint_count": 2,
        "first_step_cuda_resource_receipt": first_step_receipt[
            "resource_receipt"
        ],
        "full_run_samples": sampled_resources,
        "fair_evidence": True,
        "fair_evidence_boundary": (
            "engineering-resource-completeness-only-not-effect-evidence"
        ),
    }
    resource_summary_path = unit_root / "resource-summary.json"
    atomic_write_json(resource_summary_path, resource_summary)
    atomic_write_json(
        volatile_progress_path,
        {
            "schema_version": "cuda-rwkv-volatile-progress-v1",
            "unit": spec.key,
            "training_identity_sha256": training_identity_sha256,
            "epoch": int(training["epochs"]),
            "step_in_epoch": int(training["steps_per_epoch"]),
            "optimizer_step": optimizer_step,
            "state": "finished",
            **progress,
        },
    )
    source_metrics.update(
        {
            "unit": spec.key,
            "selected_epoch": best_epoch,
            "selection_metric": "validation_flow_average_precision",
            "selection_value": best_flow_ap,
            "model_spec_sha256": identities["model_spec_sha256"],
            "cuda_execution_identity_sha256": identities[
                "cuda_execution_identity_sha256"
            ],
            "resource_summary_sha256": sha256_file(resource_summary_path),
        }
    )
    source_metrics["result_sha256"] = canonical_sha256(
        {key: value for key, value in source_metrics.items() if key != "result_sha256"}
    )
    source_metrics_path = unit_root / "source-metrics.json"
    atomic_write_json(source_metrics_path, source_metrics)
    completed = {
        "schema_version": "cuda-rwkv-source-unit-complete-v1",
        "state": "finished",
        "unit": spec.key,
        "best_epoch": best_epoch,
        "validation_flow_average_precision": best_flow_ap,
        "best_checkpoint_sha256": sha256_file(best_checkpoint),
        "model_spec_sha256": identities["model_spec_sha256"],
        "cuda_execution_identity_sha256": identities[
            "cuda_execution_identity_sha256"
        ],
        "source_metrics_sha256": sha256_file(source_metrics_path),
        "resource_summary_sha256": sha256_file(resource_summary_path),
        "persisted_score_rows": 0,
        "persisted_label_rows": 0,
        "persisted_member_rows": 0,
    }
    atomic_write_json(completed_path, completed)
    atomic_write_json(
        unit_root / "status.json",
        {"state": "finished", "unit": spec.key, **completed},
    )
    unit_manifest_path, unit_manifest_sha256 = _write_unit_manifest(
        unit_root=unit_root,
        spec=spec,
        identities=identities,
    )
    _validate_unit_manifest(
        unit_root=unit_root,
        spec=spec,
        expected_identities=identities,
    )
    return TrainingUnitResult(
        spec=spec,
        unit_root=unit_root,
        best_checkpoint=best_checkpoint,
        best_checkpoint_sha256=completed["best_checkpoint_sha256"],
        best_epoch=best_epoch,
        validation_flow_average_precision=best_flow_ap,
        model_spec_sha256=identities["model_spec_sha256"],
        cuda_execution_identity_sha256=identities[
            "cuda_execution_identity_sha256"
        ],
        source_metrics_path=source_metrics_path,
        source_metrics_sha256=completed["source_metrics_sha256"],
        unit_manifest_path=unit_manifest_path,
        unit_manifest_sha256=unit_manifest_sha256,
    )


def reuse_training_unit(
    result: TrainingUnitResult, expected_spec: TrainingUnitSpec
) -> TrainingUnitResult:
    """只有四个科学维度完全相同时才返回原检查点。"""

    if result.spec != expected_spec:
        raise RuntimeError(
            f"训练单元身份不同，拒绝复用：{result.spec.key} != {expected_spec.key}"
        )
    if sha256_file(result.best_checkpoint) != result.best_checkpoint_sha256:
        raise RuntimeError("复用训练单元的检查点 SHA-256 漂移")
    if sha256_file(result.source_metrics_path) != result.source_metrics_sha256:
        raise RuntimeError("复用训练单元的源年指标 SHA-256 漂移")
    if (
        not result.unit_manifest_path.is_file()
        or sha256_file(result.unit_manifest_path) != result.unit_manifest_sha256
    ):
        raise RuntimeError("复用训练单元的完整清单 SHA-256 漂移")
    return result


def choose_by_flow_ap(
    candidates: Sequence[TrainingUnitResult],
    *,
    tie_order: Sequence[str],
) -> TrainingUnitResult:
    if not candidates:
        raise ValueError("源年选择候选不得为空")
    rank = {key: index for index, key in enumerate(tie_order)}
    unknown = [result.spec.key for result in candidates if result.spec.key not in rank]
    if unknown:
        raise RuntimeError(f"源年选择并列顺序缺少候选：{unknown}")
    return sorted(
        candidates,
        key=lambda result: (
            -result.validation_flow_average_precision,
            rank[result.spec.key],
        ),
    )[0]
