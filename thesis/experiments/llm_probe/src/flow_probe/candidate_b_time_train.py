"""候选 B 角色分离物理时间 RWKV Q0 的准备、训练、封存与评价入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import sklearn
import torch
from sklearn.metrics import average_precision_score, brier_score_loss
from torch import nn

from flow_probe.c12_crossyear_train import (
    SequenceRole,
    _balanced_sequence_order,
    _load_target_prefix_representation,
    load_cache,
)
from flow_probe.candidate_b_time_state import (
    DISPLAY_NAMES,
    TIME_CONTROL_VARIANTS,
    VARIANTS,
    CandidateBModelConfig,
    CandidateBTimeModel,
    TimeTransform,
    build_parameter_matched_models,
    trainable_parameter_count,
)
from flow_probe.r1_source_environment import (
    _environment,
    _load_frozen_representations,
    _seed_everything,
    _sha256,
    _write_json,
    _write_npy,
    _write_npz,
)
from flow_probe.tracking import REQUIRED_SWANLAB_PROJECT, REQUIRED_SWANLAB_WORKSPACE


CONFIG_SCHEMA = "candidate-b-physical-time-rwkv-q0-config-v1"
PREPARE_SCHEMA = "candidate-b-physical-time-rwkv-q0-preparation-v1"
RUN_SCHEMA = "candidate-b-physical-time-rwkv-q0-run-v1"
PREDICTION_SCHEMA = "candidate-b-physical-time-sealed-probabilities-v1"
EVALUATION_SCHEMA = "candidate-b-physical-time-rwkv-q0-evaluation-v1"
DIAGNOSTICS = ("stable-time-shuffle", "fixed-source-median-time")


class CandidateBTrainError(ValueError):
    """训练、概率封存或独立评价违反冻结合同。"""


class SwanTracker:
    """每个训练变体独占在线运行，只记录聚合指标和协议元数据。"""

    def __init__(
        self,
        output_dir: Path,
        run_name: str,
        variant: str,
        config: Mapping[str, Any],
        parameter_count: int,
    ) -> None:
        _assert_swanlab_destination(config)
        import swanlab

        self.client = swanlab
        self.run = swanlab.init(
            project=REQUIRED_SWANLAB_PROJECT,
            workspace=REQUIRED_SWANLAB_WORKSPACE,
            name=run_name,
            description="候选 B 角色分离物理时间 RWKV Q0 快速筛选",
            config={
                "variant": variant,
                "display_name": DISPLAY_NAMES[variant],
                "seed": int(config["seed"]),
                "epochs": int(config["epochs"]),
                "total_training_steps": int(config["total_training_steps"]),
                "trainable_parameter_count": parameter_count,
                "screening_only": True,
                "formal_paper_evidence": False,
                "final_accessed": False,
            },
            mode="online",
            tags=["candidate-b", "physical-time", variant.lower(), "q0", "seed42"],
            log_dir=str(output_dir / "swanlog"),
        )
        self.run_id = str(self.run.id)
        _write_json(
            output_dir / "swanlab-status.json",
            {"status": "running", "run_id": self.run_id},
        )

    def log(self, values: Mapping[str, int | float], step: int) -> None:
        self.client.log(dict(values), step=step)

    def finish(self, output_dir: Path) -> None:
        self.client.finish()
        _write_json(
            output_dir / "swanlab-status.json",
            {"status": "finished", "run_id": self.run_id},
        )

    def fail(self, output_dir: Path, error: BaseException) -> None:
        try:
            self.client.finish(state="crashed", error=str(error))
        finally:
            _write_json(
                output_dir / "swanlab-status.json",
                {
                    "status": "failed",
                    "run_id": self.run_id,
                    "error_type": type(error).__name__,
                },
            )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CandidateBTrainError(f"JSON 顶层必须是对象：{path}")
    return value


def _append_jsonl(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n")


def _load_config(path: Path) -> dict[str, Any]:
    config = _read_json(path.resolve())
    fixed = {
        "schema_version": CONFIG_SCHEMA,
        "seed": 42,
        "epochs": 4,
        "batch_size_sequences": 16,
        "maximum_sequence_length": 128,
        "hidden_size": 192,
        "steps_per_epoch": 183,
        "total_training_steps": 732,
        "maximum_concurrent_variants": 3,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    for key, expected in fixed.items():
        if config.get(key) != expected:
            raise CandidateBTrainError(f"冻结配置不匹配：{key} 必须为 {expected}")
    if [item.get("key") for item in config.get("variants", [])] != list(VARIANTS):
        raise CandidateBTrainError("五变体键或冻结顺序不一致")
    _assert_swanlab_destination(config)
    return config


def _assert_swanlab_destination(config: Mapping[str, Any]) -> None:
    value = config.get("swanlab")
    if not isinstance(value, Mapping) or (
        value.get("workspace") != REQUIRED_SWANLAB_WORKSPACE
        or value.get("project") != REQUIRED_SWANLAB_PROJECT
        or value.get("mode") != "online"
        or value.get("upload_policy") != "aggregate_metrics_and_protocol_metadata_only"
    ):
        raise CandidateBTrainError("SwanLab 目的地或上传边界与授权不一致")


def _identity_sha256(role: SequenceRole) -> str:
    digest = hashlib.sha256(b"candidate-b-row-identity-v1\0")
    for value in (role.sample_id, role.sequence_id, role.position, role.valid_length):
        digest.update(np.ascontiguousarray(value).view(np.uint8))
    return digest.hexdigest()


def _fit_time_transform(role: SequenceRole, quantile: float) -> TimeTransform:
    if not 0.5 < quantile < 1.0:
        raise CandidateBTrainError("时间裁剪分位必须位于 (0.5,1)")
    delta = np.maximum(np.asarray(role.delta_t_us, dtype=np.int64), 0)
    clip = max(1, int(np.quantile(delta, quantile, method="higher")))
    clipped = np.minimum(delta, clip)
    logged = np.log1p(clipped.astype(np.float64) / 1_000_000.0)
    std = max(float(logged.std()), 1.0e-6)
    spans = np.asarray(
        [
            int(delta[int(start) : int(start + length)].sum(dtype=np.int64))
            for start, length in zip(role.starts, role.lengths, strict=True)
        ],
        dtype=np.int64,
    )

    def quartiles(value: np.ndarray) -> tuple[int, int, int]:
        return tuple(int(item) for item in np.quantile(value, [0.25, 0.5, 0.75], method="higher"))

    return TimeTransform(
        unit="microseconds",
        clip_delta_t_us=clip,
        median_delta_t_us=int(np.quantile(delta, 0.5, method="higher")),
        log1p_mean=float(logged.mean()),
        log1p_std=std,
        quartile_delta_t_us=quartiles(delta),
        quartile_sequence_span_us=quartiles(spans),
    )


def _time_transform(preparation_root: Path) -> TimeTransform:
    manifest = _read_json(preparation_root / "preparation-manifest.json")
    if (
        manifest.get("schema_version") != PREPARE_SCHEMA
        or manifest.get("source_train_statistics_only") is not True
        or manifest.get("target_statistics_used") is not False
        or manifest.get("final_accessed") is not False
    ):
        raise CandidateBTrainError("候选 B 准备清单不合法")
    value = manifest.get("time_transform")
    if not isinstance(value, Mapping):
        raise CandidateBTrainError("候选 B 时间变换缺失")
    return TimeTransform.from_mapping(value)


def prepare(
    cache_root: Path,
    representation_root: Path,
    target_prefix_representation_root: Path,
    output_dir: Path,
    config_path: Path,
) -> dict[str, Any]:
    """只从源训练拟合时间变换，并发布五变体唯一共同训练顺序。"""
    if output_dir.exists():
        raise CandidateBTrainError("准备输出目录已存在，拒绝覆盖")
    config = _load_config(config_path)
    cache_manifest, roles = load_cache(cache_root)
    representations, representation_manifest = _load_frozen_representations(
        cache_root, representation_root
    )
    target_prefix_phi, target_prefix_manifest = _load_target_prefix_representation(
        cache_root, target_prefix_representation_root
    )
    if len(target_prefix_phi) != roles["target-prefix"].row_count:
        raise CandidateBTrainError("目标前缀冻结表示行数不一致")
    if target_prefix_manifest.get("labels_read") is not False:
        raise CandidateBTrainError("目标前缀冻结表示必须保持 labels_read=false")
    for role_name in ("source-train", "source-validation", "target-development"):
        if representations[role_name].shape != (roles[role_name].row_count, 192):
            raise CandidateBTrainError(f"冻结 phi 形状不合法：{role_name}")
    time_transform = _fit_time_transform(
        roles["source-train"], float(config["time_transform"]["source_clip_quantile"])
    )
    order = np.empty(
        (
            int(config["epochs"]),
            int(config["steps_per_epoch"]),
            int(config["batch_size_sequences"]),
        ),
        dtype=np.int64,
    )
    pool_receipts: list[dict[str, object]] = []
    for epoch in range(1, int(config["epochs"]) + 1):
        epoch_order, receipt = _balanced_sequence_order(
            roles["source-train"],
            int(config["seed"]),
            epoch,
            int(config["batch_size_sequences"]),
        )
        expected = int(config["steps_per_epoch"]) * int(config["batch_size_sequences"])
        if len(epoch_order) != expected or receipt.get("every_batch_equal_pool_counts") is not True:
            raise CandidateBTrainError("真实 Q0 缓存未形成冻结的双池 183 步顺序")
        order[epoch - 1] = epoch_order.reshape(
            int(config["steps_per_epoch"]), int(config["batch_size_sequences"])
        )
        pool_receipts.append({"epoch": epoch, **receipt})
    output_dir.mkdir(parents=True)
    order_path = output_dir / "training-sequence-order.npy"
    _write_npy(order_path, order)
    manifest = {
        "schema_version": PREPARE_SCHEMA,
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "representation_manifest_sha256": _sha256(
            representation_root / "representation-manifest.json"
        ),
        "target_prefix_representation_manifest_sha256": _sha256(
            target_prefix_representation_root / "target-prefix-representation-manifest.json"
        ),
        "receiver_checkpoint_sha256": representation_manifest.get("receiver_checkpoint_sha256"),
        "cache_schema": cache_manifest.get("schema_version"),
        "role_rows": {name: role.row_count for name, role in roles.items()},
        "role_sequences": {name: role.sequence_count for name, role in roles.items()},
        "time_transform": time_transform.to_dict(),
        "source_train_statistics_only": True,
        "target_statistics_used": False,
        "training_order_path": str(order_path.resolve()),
        "training_order_sha256": _sha256(order_path),
        "training_order_shape": list(order.shape),
        "fixed_budget_steps": int(np.prod(order.shape[:2])),
        "pool_receipts": pool_receipts,
        "shared_by_variants": list(VARIANTS),
        "identity_fields_used_as_model_input": False,
        "model_inputs": ["frozen_phi", "exact_delta_t_us_by_variant_contract"],
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    _write_json(output_dir / "preparation-manifest.json", manifest)
    print(
        "候选B准备完成：共同顺序=4轮×183步，时间统计仅来自source-train，" "final_accessed=false",
        flush=True,
    )
    return manifest


def _load_preparation(
    preparation_root: Path, roles: Mapping[str, SequenceRole]
) -> tuple[dict[str, Any], np.ndarray, TimeTransform]:
    manifest = _read_json(preparation_root / "preparation-manifest.json")
    order_path = preparation_root / "training-sequence-order.npy"
    if (
        manifest.get("schema_version") != PREPARE_SCHEMA
        or manifest.get("training_order_sha256") != _sha256(order_path)
        or manifest.get("fixed_budget_steps") != 732
        or manifest.get("shared_by_variants") != list(VARIANTS)
        or manifest.get("final_accessed") is not False
    ):
        raise CandidateBTrainError("准备制品哈希、预算或共享合同不合法")
    if manifest.get("role_rows") != {name: role.row_count for name, role in roles.items()}:
        raise CandidateBTrainError("准备清单与当前缓存角色行数不一致")
    order = np.load(order_path, mmap_mode="r")
    if order.shape != (4, 183, 16):
        raise CandidateBTrainError("共同训练顺序必须为 [4,183,16]")
    return manifest, order, _time_transform(preparation_root)


def _sequence_batch(
    role: SequenceRole,
    representation: np.ndarray,
    sequence_indices: np.ndarray,
    delta_override: str | None = None,
    median_delta_t_us: int | None = None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor | None]:
    lengths = role.lengths[sequence_indices]
    maximum = int(lengths.max())
    values = np.zeros((len(sequence_indices), maximum, 192), dtype=np.float32)
    delta = np.zeros((len(sequence_indices), maximum), dtype=np.int64)
    valid = np.zeros((len(sequence_indices), maximum), dtype=bool)
    labels = (
        np.zeros((len(sequence_indices), maximum), dtype=np.float32)
        if role.labels is not None
        else None
    )
    for batch_index, sequence_index in enumerate(sequence_indices):
        start = int(role.starts[sequence_index])
        length = int(role.lengths[sequence_index])
        row_slice = slice(start, start + length)
        values[batch_index, :length] = representation[row_slice]
        exact = np.asarray(role.delta_t_us[row_slice], dtype=np.int64)
        if delta_override == "stable-time-shuffle":
            generator = np.random.default_rng(
                int.from_bytes(np.asarray(role.sequence_id[start]).tobytes()[:8], "little") ^ 42
            )
            exact = exact[generator.permutation(length)]
        elif delta_override == "fixed-source-median-time":
            if median_delta_t_us is None:
                raise CandidateBTrainError("固定中位时间诊断缺少源中位数")
            exact = np.full(length, median_delta_t_us, dtype=np.int64)
        elif delta_override is not None:
            raise CandidateBTrainError(f"未知时间诊断：{delta_override}")
        delta[batch_index, :length] = exact
        valid[batch_index, :length] = True
        if labels is not None and role.labels is not None:
            labels[batch_index, :length] = role.labels[row_slice]
    return (
        torch.from_numpy(values),
        torch.from_numpy(delta),
        torch.from_numpy(valid),
        torch.from_numpy(labels) if labels is not None else None,
    )


def _checkpoint_payload(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    variant: str,
    binding: Mapping[str, object],
    next_epoch: int,
    next_batch: int,
    global_step: int,
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": "candidate-b-physical-time-checkpoint-v1",
        "variant": variant,
        "binding": dict(binding),
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict(),
        "next_epoch": next_epoch,
        "next_batch": next_batch,
        "global_step": global_step,
        "python_random_state": random.getstate(),
        "numpy_random_state": np.random.get_state(),
        "torch_random_state": torch.random.get_rng_state(),
        "final_accessed": False,
    }
    if torch.cuda.is_available():
        result["cuda_random_states"] = torch.cuda.get_rng_state_all()
    return result


def _save_checkpoint(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    torch.save(dict(payload), partial)
    os.replace(partial, path)


def _restore_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    variant: str,
    binding: Mapping[str, object],
    device: torch.device,
) -> tuple[int, int, int]:
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    if (
        checkpoint.get("schema_version") != "candidate-b-physical-time-checkpoint-v1"
        or checkpoint.get("variant") != variant
        or checkpoint.get("binding") != dict(binding)
        or checkpoint.get("final_accessed") is not False
    ):
        raise CandidateBTrainError("恢复检查点身份绑定不一致")
    model.load_state_dict(checkpoint["model"])
    optimizer.load_state_dict(checkpoint["optimizer"])
    scheduler.load_state_dict(checkpoint["scheduler"])
    random.setstate(checkpoint["python_random_state"])
    np.random.set_state(checkpoint["numpy_random_state"])
    torch.random.set_rng_state(checkpoint["torch_random_state"])
    if "cuda_random_states" in checkpoint:
        torch.cuda.set_rng_state_all(checkpoint["cuda_random_states"])
    return (
        int(checkpoint["next_epoch"]),
        int(checkpoint["next_batch"]),
        int(checkpoint["global_step"]),
    )


def _seal_predictions(
    output_dir: Path,
    role: SequenceRole,
    probabilities: np.ndarray,
    diagnostic: str | None,
) -> dict[str, Any]:
    if probabilities.shape != (role.row_count,) or not np.isfinite(probabilities).all():
        raise CandidateBTrainError(f"{role.role} 概率形状不合法或包含非有限值")
    stem = role.role if diagnostic is None else f"{role.role}--{diagnostic}"
    path = output_dir / "predictions" / f"{stem}.npz"
    _write_npz(
        path,
        probability=np.asarray(probabilities, dtype=np.float32),
        sample_id=np.asarray(role.sample_id),
        sequence_id=np.asarray(role.sequence_id),
        position=np.asarray(role.position),
        valid_length=np.asarray(role.valid_length),
    )
    receipt = {
        "schema_version": PREDICTION_SCHEMA,
        "role": role.role,
        "diagnostic": diagnostic,
        "path": str(path.resolve()),
        "sha256": _sha256(path),
        "identity_sha256": _identity_sha256(role),
        "row_count": role.row_count,
        "target_labels_read": False,
        "model_retrained_for_diagnostic": False if diagnostic else None,
        "sealed_before_target_evaluation": True,
        "final_accessed": False,
    }
    _write_json(output_dir / "predictions" / f"{stem}-receipt.json", receipt)
    print(
        f"概率封存完成：角色={role.role} 诊断={diagnostic or '原始'} "
        f"行数={role.row_count} sha256={receipt['sha256']}",
        flush=True,
    )
    return receipt


def _predict_role(
    model: CandidateBTimeModel,
    role: SequenceRole,
    representation: np.ndarray,
    output_dir: Path,
    batch_size: int,
    device: torch.device,
    progress_interval_rows: int,
    time_transform: TimeTransform,
    diagnostic: str | None = None,
) -> tuple[dict[str, Any], dict[str, float], float]:
    model.eval()
    probabilities = np.empty(role.row_count, dtype=np.float32)
    processed = 0
    next_progress = progress_interval_rows
    norm_sum = 0.0
    retention_sum = 0.0
    valid_count = 0.0
    started = time.perf_counter()
    with torch.no_grad():
        for offset in range(0, role.sequence_count, batch_size):
            indices = np.arange(offset, min(offset + batch_size, role.sequence_count))
            values, delta, valid, _ = _sequence_batch(
                role,
                representation,
                indices,
                delta_override=diagnostic,
                median_delta_t_us=time_transform.median_delta_t_us,
            )
            values = values.to(device, non_blocking=True)
            delta = delta.to(device, non_blocking=True)
            valid_device = valid.to(device, non_blocking=True)
            with torch.autocast(
                device_type=device.type,
                dtype=torch.bfloat16,
                enabled=device.type == "cuda",
            ):
                logits, diagnostics = model(values, delta, valid_device)
            probability = torch.sigmoid(logits).float().cpu().numpy()
            valid_np = valid.numpy()
            for batch_index, sequence_index in enumerate(indices):
                start = int(role.starts[sequence_index])
                length = int(role.lengths[sequence_index])
                probabilities[start : start + length] = probability[batch_index][
                    valid_np[batch_index]
                ]
                processed += length
            norm_sum += float(diagnostics.state_norm_sum.cpu())
            retention_sum += float(diagnostics.retention_sum.cpu())
            valid_count += float(diagnostics.valid_count.cpu())
            if processed >= next_progress or processed == role.row_count:
                elapsed = time.perf_counter() - started
                rate = processed / max(elapsed, 1e-9)
                remaining = (role.row_count - processed) / max(rate, 1e-9)
                print(
                    f"概率封存进度：角色={role.role} 诊断={diagnostic or '原始'} "
                    f"已处理={processed}/{role.row_count} 吞吐={rate:.1f}行/秒 "
                    f"预计剩余={remaining:.1f}秒",
                    flush=True,
                )
                next_progress += progress_interval_rows
    receipt = _seal_predictions(output_dir, role, probabilities, diagnostic)
    return (
        receipt,
        {
            "mean_state_norm": norm_sum / max(valid_count, 1.0),
            "mean_retention": retention_sum / max(valid_count, 1.0),
            "valid_rows": valid_count,
        },
        time.perf_counter() - started,
    )


def train_variant(
    cache_root: Path,
    representation_root: Path,
    target_prefix_representation_root: Path,
    preparation_root: Path,
    output_dir: Path,
    config_path: Path,
    variant: str,
    run_name: str,
) -> dict[str, Any]:
    """按共同 732 步预算训练一个变体，并在无目标标签条件下封存概率。"""
    if variant not in VARIANTS:
        raise CandidateBTrainError(f"未知候选 B 变体：{variant}")
    config = _load_config(config_path)
    _seed_everything(int(config["seed"]))
    cache_manifest, roles = load_cache(cache_root)
    representations, representation_manifest = _load_frozen_representations(
        cache_root, representation_root
    )
    target_prefix_phi, target_prefix_manifest = _load_target_prefix_representation(
        cache_root, target_prefix_representation_root
    )
    preparation, order, time_transform = _load_preparation(preparation_root, roles)
    if target_prefix_manifest.get("labels_read") is not False:
        raise CandidateBTrainError("训练拒绝目标前缀标签")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise CandidateBTrainError("候选 B Q0 真实训练要求 CUDA")
    models, raw_counts, matched_counts = build_parameter_matched_models(
        CandidateBModelConfig(), time_transform, int(config["seed"])
    )
    if len(set(matched_counts.values())) != 1:
        raise CandidateBTrainError("五变体参数量必须完全一致")
    model = models[variant].to(device)
    del models
    parameter_count = trainable_parameter_count(model)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=int(config["epochs"]))
    binding = {
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "representation_manifest_sha256": _sha256(
            representation_root / "representation-manifest.json"
        ),
        "target_prefix_representation_manifest_sha256": _sha256(
            target_prefix_representation_root / "target-prefix-representation-manifest.json"
        ),
        "preparation_manifest_sha256": _sha256(preparation_root / "preparation-manifest.json"),
        "training_order_sha256": preparation["training_order_sha256"],
        "config_sha256": _sha256(config_path),
        "variant": variant,
        "seed": int(config["seed"]),
    }
    snapshot = {
        "schema_version": RUN_SCHEMA,
        "variant": variant,
        "display_name": DISPLAY_NAMES[variant],
        "run_name": run_name,
        "binding": binding,
        "raw_trainable_parameter_counts": raw_counts,
        "matched_trainable_parameter_counts": matched_counts,
        "trainable_parameter_count": parameter_count,
        "shared_training_order": True,
        "shared_optimizer_and_scheduler": True,
        "model_inputs": ["frozen_phi", "exact_delta_t_us_by_variant_contract"],
        "forbidden_model_inputs": [
            "sample_id",
            "sequence_id",
            "position",
            "valid_length",
            "year_role",
            "label",
        ],
        "target_prefix_labels_used": False,
        "target_development_labels_used": False,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
        "cache_schema": cache_manifest["schema_version"],
        "receiver_checkpoint_sha256": representation_manifest.get("receiver_checkpoint_sha256"),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = output_dir / "config.json"
    if snapshot_path.exists():
        existing = _read_json(snapshot_path)
        if existing.get("binding") != binding:
            raise CandidateBTrainError("已有运行目录与当前冻结身份不一致")
    else:
        _write_json(snapshot_path, snapshot)
        environment = _environment(device)
        environment["scikit_learn"] = sklearn.__version__
        _write_json(output_dir / "environment-receipt.json", environment)
    _write_json(
        output_dir / "status.json",
        {
            "state": "running",
            "variant": variant,
            "target_development_labels_used": False,
            "final_accessed": False,
        },
    )
    print(
        f"候选B训练启动：变体={variant} 展示名称={DISPLAY_NAMES[variant]} "
        "预算=732步 目标标签未读取 final_accessed=false",
        flush=True,
    )
    checkpoint_path = output_dir / "checkpoints" / "latest.pt"
    start_epoch = 0
    start_batch = 0
    global_step = 0
    resumed = False
    if checkpoint_path.is_file():
        start_epoch, start_batch, global_step = _restore_checkpoint(
            checkpoint_path, model, optimizer, scheduler, variant, binding, device
        )
        resumed = True
    tracker: SwanTracker | None = None
    started = time.perf_counter()
    epoch_receipts: list[dict[str, Any]] = []
    metrics_path = output_dir / "metrics" / "epochs.jsonl"
    if metrics_path.is_file():
        epoch_receipts = [
            json.loads(line)
            for line in metrics_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
    train_role = roles["source-train"]
    if train_role.labels is None:
        raise CandidateBTrainError("源训练标签缺失")
    torch.cuda.reset_peak_memory_stats(device)
    try:
        tracker = SwanTracker(output_dir, run_name, variant, config, parameter_count)
        for epoch in range(start_epoch, int(config["epochs"])):
            model.train()
            loss_sum = 0.0
            norm_sum = 0.0
            retention_sum = 0.0
            rows_sum = 0.0
            batch_begin = start_batch if epoch == start_epoch else 0
            for batch_index in range(batch_begin, int(config["steps_per_epoch"])):
                sequence_indices = np.asarray(order[epoch, batch_index])
                values, delta, valid, labels = _sequence_batch(
                    train_role, representations["source-train"], sequence_indices
                )
                if labels is None:
                    raise CandidateBTrainError("训练批次缺少源标签")
                values = values.to(device, non_blocking=True)
                delta = delta.to(device, non_blocking=True)
                valid = valid.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits, diagnostics = model(values, delta, valid)
                    loss = nn.functional.binary_cross_entropy_with_logits(
                        logits[valid], labels[valid]
                    )
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), float(config["gradient_clip_norm"]))
                optimizer.step()
                global_step += 1
                rows = float(diagnostics.valid_count.detach().cpu())
                mean_norm, mean_retention = diagnostics.means()
                loss_sum += float(loss.detach().cpu())
                norm_sum += float(mean_norm.detach().cpu())
                retention_sum += float(mean_retention.detach().cpu())
                rows_sum += rows
                if global_step % int(config["checkpoint_interval_steps"]) == 0:
                    _save_checkpoint(
                        checkpoint_path,
                        _checkpoint_payload(
                            model,
                            optimizer,
                            scheduler,
                            variant,
                            binding,
                            epoch,
                            batch_index + 1,
                            global_step,
                        ),
                    )
                if global_step == 1 or global_step % int(config["progress_interval_steps"]) == 0:
                    elapsed = time.perf_counter() - started
                    rate = global_step / max(elapsed, 1e-9)
                    remaining = (732 - global_step) / max(rate, 1e-9)
                    scalars = {
                        "train/loss": float(loss.detach().cpu()),
                        "train/mean_state_norm": float(mean_norm.detach().cpu()),
                        "train/mean_retention": float(mean_retention.detach().cpu()),
                        "train/learning_rate": float(optimizer.param_groups[0]["lr"]),
                        "runtime/peak_gpu_memory_bytes": int(
                            torch.cuda.max_memory_allocated(device)
                        ),
                    }
                    print(
                        f"候选B训练进度：变体={variant} 步={global_step}/732 "
                        f"损失={scalars['train/loss']:.6f} 吞吐={rate:.2f}步/秒 "
                        f"预计剩余={remaining:.1f}秒",
                        flush=True,
                    )
                    tracker.log(scalars, step=global_step)
            scheduler.step()
            completed_batches = int(config["steps_per_epoch"]) - batch_begin
            receipt = {
                "epoch": epoch + 1,
                "steps": completed_batches,
                "mean_loss": loss_sum / max(completed_batches, 1),
                "mean_state_norm": norm_sum / max(completed_batches, 1),
                "mean_retention": retention_sum / max(completed_batches, 1),
                "valid_rows": rows_sum,
                "training_order_sha256": binding["training_order_sha256"],
            }
            epoch_receipts.append(receipt)
            _append_jsonl(metrics_path, receipt)
            _save_checkpoint(
                checkpoint_path,
                _checkpoint_payload(
                    model,
                    optimizer,
                    scheduler,
                    variant,
                    binding,
                    epoch + 1,
                    0,
                    global_step,
                ),
            )
            start_batch = 0
        if global_step != 732:
            raise CandidateBTrainError(f"实际训练步数不是冻结预算 732：{global_step}")
        final_checkpoint = output_dir / "checkpoints" / "final.pt"
        _save_checkpoint(
            final_checkpoint,
            _checkpoint_payload(
                model,
                optimizer,
                scheduler,
                variant,
                binding,
                4,
                0,
                global_step,
            ),
        )
        all_representations = {
            **representations,
            "target-prefix": target_prefix_phi,
        }
        probability_receipts: dict[str, Any] = {}
        runtime_receipts: dict[str, Any] = {}
        for role_name in (
            "source-train",
            "source-validation",
            "target-prefix",
            "target-development",
        ):
            prediction, diagnostics, seconds = _predict_role(
                model,
                roles[role_name],
                all_representations[role_name],
                output_dir,
                int(config["batch_size_sequences"]),
                device,
                int(config["prediction_progress_interval_rows"]),
                time_transform,
            )
            probability_receipts[role_name] = prediction
            runtime_receipts[role_name] = {"seconds": seconds, **diagnostics}
        diagnostic_receipts: dict[str, Any] = {}
        if variant in TIME_CONTROL_VARIANTS:
            for diagnostic in DIAGNOSTICS:
                prediction, diagnostics, seconds = _predict_role(
                    model,
                    roles["target-development"],
                    all_representations["target-development"],
                    output_dir,
                    int(config["batch_size_sequences"]),
                    device,
                    int(config["prediction_progress_interval_rows"]),
                    time_transform,
                    diagnostic=diagnostic,
                )
                diagnostic_receipts[diagnostic] = {
                    "prediction": prediction,
                    "runtime_seconds": seconds,
                    "state_diagnostics": diagnostics,
                    "model_retrained": False,
                }
        training_seconds = time.perf_counter() - started
        receipt = {
            "schema_version": RUN_SCHEMA,
            "state": "probabilities_sealed_evaluation_pending",
            "variant": variant,
            "display_name": DISPLAY_NAMES[variant],
            "planned_epochs": 4,
            "actual_epochs": 4,
            "planned_steps": 732,
            "actual_steps": global_step,
            "resumed_from_checkpoint": resumed,
            "trainable_parameter_count": parameter_count,
            "raw_trainable_parameter_counts": raw_counts,
            "matched_trainable_parameter_counts": matched_counts,
            "binding": binding,
            "epoch_receipts": epoch_receipts,
            "probability_receipts": probability_receipts,
            "time_diagnostic_receipts": diagnostic_receipts,
            "time_diagnostics_retrained": False,
            "runtime_receipts": runtime_receipts,
            "training_seconds": training_seconds,
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "swanlab_run_id": tracker.run_id,
            "target_prefix_labels_used": False,
            "target_development_labels_used": False,
            "all_required_probabilities_sealed": True,
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        }
        _write_json(output_dir / "training-receipt.json", receipt)
        _write_json(
            output_dir / "status.json",
            {
                "state": "probabilities_sealed_evaluation_pending",
                "variant": variant,
                "actual_steps": global_step,
                "all_required_probabilities_sealed": True,
                "target_development_labels_used": False,
                "final_accessed": False,
            },
        )
        tracker.finish(output_dir)
        return receipt
    except BaseException as error:
        _write_json(
            output_dir / "status.json",
            {
                "state": "failed",
                "variant": variant,
                "error_type": type(error).__name__,
                "checkpoint_available": checkpoint_path.is_file(),
                "recovery_action": "保持冻结绑定后重新运行同一变体命令",
                "target_development_labels_used": False,
                "final_accessed": False,
            },
        )
        if tracker is not None:
            tracker.fail(output_dir, error)
        raise


def _load_sealed_probability(
    run_dir: Path,
    role: SequenceRole,
    diagnostic: str | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    stem = role.role if diagnostic is None else f"{role.role}--{diagnostic}"
    receipt = _read_json(run_dir / "predictions" / f"{stem}-receipt.json")
    path = run_dir / "predictions" / f"{stem}.npz"
    if (
        receipt.get("schema_version") != PREDICTION_SCHEMA
        or receipt.get("role") != role.role
        or receipt.get("diagnostic") != diagnostic
        or receipt.get("sha256") != _sha256(path)
        or receipt.get("identity_sha256") != _identity_sha256(role)
        or receipt.get("target_labels_read") is not False
        or receipt.get("final_accessed") is not False
    ):
        raise CandidateBTrainError(f"{run_dir.name}/{stem} 概率封存收据不合法")
    with np.load(path, allow_pickle=False) as values:
        for key, expected in (
            ("sample_id", role.sample_id),
            ("sequence_id", role.sequence_id),
            ("position", role.position),
            ("valid_length", role.valid_length),
        ):
            if not np.array_equal(values[key], expected):
                raise CandidateBTrainError(f"{run_dir.name}/{stem} 身份键不一致：{key}")
        probabilities = np.asarray(values["probability"], dtype=np.float64)
    if probabilities.shape != (role.row_count,) or not np.isfinite(probabilities).all():
        raise CandidateBTrainError(f"{run_dir.name}/{stem} 概率数组不合法")
    return probabilities, receipt


def _ece(labels: np.ndarray, probabilities: np.ndarray, bins: int = 15) -> float:
    order = np.argsort(probabilities, kind="stable")
    error = 0.0
    for indices in np.array_split(order, bins):
        if len(indices):
            error += (
                len(indices)
                / len(order)
                * abs(float(labels[indices].mean()) - float(probabilities[indices].mean()))
            )
    return float(error)


def _alert_budget_recall(
    labels: np.ndarray, scores: np.ndarray, budgets: list[int]
) -> dict[str, Any]:
    order = np.argsort(-scores, kind="stable")
    positives = max(int(np.sum(labels == 1)), 1)
    result: dict[str, Any] = {}
    for budget in budgets:
        count = int(math.floor(len(labels) * budget / 1_000_000))
        true_positives = int(np.sum(labels[order[:count]] == 1))
        result[str(budget)] = {
            "top_k": count,
            "true_positives": true_positives,
            "recall": true_positives / positives,
        }
    return result


def _fixed_recall_false_positives(
    labels: np.ndarray, scores: np.ndarray, recalls: list[float]
) -> dict[str, Any]:
    order = np.argsort(-scores, kind="stable")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    ends = np.r_[np.flatnonzero(sorted_scores[1:] != sorted_scores[:-1]), len(labels) - 1]
    cumulative_tp = np.cumsum(sorted_labels == 1)[ends]
    cumulative_fp = np.cumsum(sorted_labels == 0)[ends]
    positives = max(int(np.sum(labels == 1)), 1)
    result: dict[str, Any] = {}
    for recall in recalls:
        valid = np.flatnonzero(cumulative_tp >= math.ceil(recall * positives))
        result[str(recall)] = (
            {
                "false_positives": int(cumulative_fp[valid[0]]),
                "achieved_recall": float(cumulative_tp[valid[0]] / positives),
            }
            if len(valid)
            else {"false_positives": None, "achieved_recall": 0.0}
        )
    return result


def _metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    budgets: list[int],
    recalls: list[float],
) -> dict[str, Any]:
    prevalence = float(labels.mean())
    average_precision = float(average_precision_score(labels, probabilities))
    return {
        "average_precision": average_precision,
        "average_precision_over_prevalence": average_precision / max(prevalence, 1e-12),
        "prevalence": prevalence,
        "brier": float(brier_score_loss(labels, probabilities)),
        "ece_15_equal_frequency": _ece(labels, probabilities),
        "alert_budget_recall_per_million": _alert_budget_recall(labels, probabilities, budgets),
        "fixed_recall_false_positives": _fixed_recall_false_positives(
            labels, probabilities, recalls
        ),
    }


def _facet_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    values: np.ndarray,
    boundaries: tuple[int, int, int],
    prefix: str,
    budgets: list[int],
    recalls: list[float],
) -> dict[str, Any]:
    buckets = np.searchsorted(np.asarray(boundaries), values, side="right")
    result: dict[str, Any] = {}
    for bucket in range(4):
        selected = buckets == bucket
        name = f"{prefix}-q{bucket + 1}"
        if not np.any(selected) or len(np.unique(labels[selected])) < 2:
            result[name] = {
                "row_count": int(selected.sum()),
                "status": "insufficient_both_classes",
            }
        else:
            result[name] = {
                "row_count": int(selected.sum()),
                "status": "evaluated",
                "metrics": _metrics(labels[selected], probabilities[selected], budgets, recalls),
            }
    return result


def _sequence_span_rows(role: SequenceRole) -> np.ndarray:
    result = np.empty(role.row_count, dtype=np.int64)
    delta = np.maximum(np.asarray(role.delta_t_us, dtype=np.int64), 0)
    for start, length in zip(role.starts, role.lengths, strict=True):
        start_value = int(start)
        length_value = int(length)
        result[start_value : start_value + length_value] = delta[
            start_value : start_value + length_value
        ].sum(dtype=np.int64)
    return result


def evaluate(
    cache_root: Path,
    preparation_root: Path,
    run_root: Path,
    output_dir: Path,
    config_path: Path,
) -> dict[str, Any]:
    """先核验全部原始及时间诊断概率封存，再连接目标开发标签。"""
    if output_dir.exists():
        raise CandidateBTrainError("评价输出目录已存在，拒绝覆盖")
    config = _load_config(config_path)
    _, roles = load_cache(cache_root)
    _, _, time_transform = _load_preparation(preparation_root, roles)
    target_role = roles["target-development"]
    probabilities: dict[str, np.ndarray] = {}
    diagnostics: dict[str, dict[str, np.ndarray]] = {}
    seals: dict[str, Any] = {}
    contracts: dict[str, Any] = {}
    print("候选B独立评价启动：先核验全部概率封存，尚未连接目标标签", flush=True)
    for variant in VARIANTS:
        run_dir = run_root / "variants" / variant.lower()
        status = _read_json(run_dir / "status.json")
        receipt = _read_json(run_dir / "training-receipt.json")
        if (
            status.get("state") != "probabilities_sealed_evaluation_pending"
            or status.get("all_required_probabilities_sealed") is not True
            or status.get("target_development_labels_used") is not False
            or status.get("final_accessed") is not False
        ):
            raise CandidateBTrainError(f"{variant} 尚未完成无标签概率封存")
        role_seals: dict[str, str] = {}
        for role_name in (
            "source-train",
            "source-validation",
            "target-prefix",
            "target-development",
        ):
            sealed_values, sealed_receipt = _load_sealed_probability(run_dir, roles[role_name])
            role_seals[role_name] = str(sealed_receipt["sha256"])
            if role_name == "target-development":
                probabilities[variant] = sealed_values
        diagnostics[variant] = {}
        diagnostic_seals: dict[str, str] = {}
        if variant in TIME_CONTROL_VARIANTS:
            for diagnostic in DIAGNOSTICS:
                values, diagnostic_receipt = _load_sealed_probability(
                    run_dir, target_role, diagnostic
                )
                if diagnostic_receipt.get("model_retrained_for_diagnostic") is not False:
                    raise CandidateBTrainError(f"{variant} 时间诊断发生了禁止的重训练")
                diagnostics[variant][diagnostic] = values
                diagnostic_seals[diagnostic] = str(diagnostic_receipt["sha256"])
        elif receipt.get("time_diagnostic_receipts") != {}:
            raise CandidateBTrainError(f"{variant} 不应产生时间控制诊断")
        contracts[variant] = {
            "trainable_parameter_count": receipt.get("trainable_parameter_count"),
            "actual_steps": receipt.get("actual_steps"),
            "training_order_sha256": receipt.get("binding", {}).get("training_order_sha256"),
            "target_development_labels_used": receipt.get("target_development_labels_used"),
        }
        seals[variant] = {
            "raw_probability_sha256_by_role": role_seals,
            "diagnostic_probability_sha256": diagnostic_seals,
        }
    values = list(contracts.values())
    if (
        len({item["trainable_parameter_count"] for item in values}) != 1
        or len({item["training_order_sha256"] for item in values}) != 1
        or any(item["actual_steps"] != 732 for item in values)
        or any(item["target_development_labels_used"] is not False for item in values)
    ):
        raise CandidateBTrainError("五变体参数量、顺序、732 步预算或标签权限不一致")
    label_path = target_role.root / "labels.npy"
    if not label_path.is_file():
        raise CandidateBTrainError("全部概率封存后无法连接目标开发标签")
    labels = np.load(label_path, mmap_mode="r")
    if labels.shape != (target_role.row_count,) or not np.isin(labels, (0, 1)).all():
        raise CandidateBTrainError("目标开发标签旁车不合法")
    labels_value = np.asarray(labels, dtype=np.uint8)
    budgets = [int(value) for value in config["evaluation"]["alert_budgets_per_million"]]
    recalls = [float(value) for value in config["evaluation"]["fixed_recall_grid"]]
    delta = np.maximum(np.asarray(target_role.delta_t_us, dtype=np.int64), 0)
    spans = _sequence_span_rows(target_role)
    results: dict[str, Any] = {}
    use_assertions: dict[str, Any] = {}
    for variant in VARIANTS:
        raw_metrics = _metrics(labels_value, probabilities[variant], budgets, recalls)
        result: dict[str, Any] = {
            "display_name": DISPLAY_NAMES[variant],
            "raw": raw_metrics,
            "delta_t_quartile_facets": _facet_metrics(
                labels_value,
                probabilities[variant],
                delta,
                time_transform.quartile_delta_t_us,
                "delta-t",
                budgets,
                recalls,
            ),
            "sequence_span_quartile_facets": _facet_metrics(
                labels_value,
                probabilities[variant],
                spans,
                time_transform.quartile_sequence_span_us,
                "sequence-span",
                budgets,
                recalls,
            ),
        }
        diagnostic_results: dict[str, Any] = {}
        for diagnostic, values_array in diagnostics[variant].items():
            diagnostic_metrics = _metrics(labels_value, values_array, budgets, recalls)
            maximum_probability_change = float(
                np.max(np.abs(probabilities[variant] - values_array))
            )
            diagnostic_results[diagnostic] = {
                "metrics": diagnostic_metrics,
                "maximum_absolute_probability_change": maximum_probability_change,
                "probabilities_identical": bool(maximum_probability_change == 0.0),
                "model_retrained": False,
            }
        result["time_diagnostics"] = diagnostic_results
        results[variant] = result
        if variant in TIME_CONTROL_VARIANTS:
            shuffle = diagnostic_results["stable-time-shuffle"]
            high_facet = result["delta_t_quartile_facets"]["delta-t-q4"]
            high_original = (
                high_facet.get("metrics", {}).get("average_precision")
                if high_facet.get("status") == "evaluated"
                else None
            )
            shuffled_facets = _facet_metrics(
                labels_value,
                diagnostics[variant]["stable-time-shuffle"],
                delta,
                time_transform.quartile_delta_t_us,
                "delta-t",
                budgets,
                recalls,
            )
            shuffled_high = shuffled_facets["delta-t-q4"]
            high_shuffled = (
                shuffled_high.get("metrics", {}).get("average_precision")
                if shuffled_high.get("status") == "evaluated"
                else None
            )
            ap_decline = raw_metrics["average_precision"] - shuffle["metrics"]["average_precision"]
            facet_decline = (
                float(high_original - high_shuffled)
                if high_original is not None and high_shuffled is not None
                else None
            )
            use_assertions[variant] = {
                "probabilities_changed": shuffle["probabilities_identical"] is False,
                "overall_ap_decline": ap_decline,
                "high_time_facet_ap_decline": facet_decline,
                "explicit_time_mechanism_used": bool(
                    shuffle["probabilities_identical"] is False
                    and (ap_decline > 0.0 or (facet_decline is not None and facet_decline > 0.0))
                ),
                "mechanical_failure_if_unchanged": shuffle["probabilities_identical"],
            }
    role_ap = results["B-ROLE-SEPARATED"]["raw"]["average_precision"]
    discrete_ap = results["B-DISCRETE-RWKV"]["raw"]["average_precision"]
    other_ap = {
        variant: results[variant]["raw"]["average_precision"]
        for variant in (
            "B-DELTA-FEATURE",
            "B-DYG-SPAN",
            "B-LINEAR-CLIPPED",
        )
    }
    high_role = results["B-ROLE-SEPARATED"]["delta_t_quartile_facets"]["delta-t-q4"]
    high_discrete = results["B-DISCRETE-RWKV"]["delta_t_quartile_facets"]["delta-t-q4"]
    high_direction_consistent = bool(
        high_role.get("status") == "evaluated"
        and high_discrete.get("status") == "evaluated"
        and high_role["metrics"]["average_precision"]
        > high_discrete["metrics"]["average_precision"]
    )
    thresholds = config["comparison_thresholds"]
    mechanism_signal = bool(
        role_ap - discrete_ap >= float(thresholds["minimum_ap_gain_over_discrete"])
        and all(role_ap > value for value in other_ap.values())
        and high_direction_consistent
    )
    time_used = bool(use_assertions["B-ROLE-SEPARATED"]["explicit_time_mechanism_used"])
    xgboost_ap = float(thresholds["shared_xgboost_ap"])
    promoted = bool(mechanism_signal and time_used and role_ap > xgboost_ap)
    if role_ap <= max(other_ap["B-DELTA-FEATURE"], other_ap["B-DYG-SPAN"]):
        verdict = "候选B立即停止，不追加频谱支路"
    elif mechanism_signal and not promoted:
        verdict = "候选B仅允许有限重构，不晋级第三章主线"
    elif promoted:
        verdict = "候选B Q0机制信号通过，可申请后续正式验证"
    else:
        verdict = "候选B Q0不晋级"
    decision = {
        "role_separated_ap": role_ap,
        "discrete_ap": discrete_ap,
        "ap_gain_over_discrete": role_ap - discrete_ap,
        "other_control_ap": other_ap,
        "high_time_drift_direction_consistent": high_direction_consistent,
        "mechanism_signal_passed": mechanism_signal,
        "role_separated_time_use_passed": time_used,
        "shared_xgboost_ap": xgboost_ap,
        "candidate_promotion_passed": promoted,
        "verdict": verdict,
        "frequency_branch_tested": False,
        "screening_only": True,
        "formal_paper_evidence": False,
    }
    output_dir.mkdir(parents=True)
    result = {
        "schema_version": EVALUATION_SCHEMA,
        "evaluation_order": "五组原始概率以及全部稳定时间打乱/固定源中位时间诊断先封存并哈希，后连接目标开发标签",
        "seals": seals,
        "shared_training_contracts": contracts,
        "identity_keys_checked_item_by_item": [
            "sample_id",
            "sequence_id",
            "position",
            "valid_length",
        ],
        "variant_results": results,
        "time_use_assertions": use_assertions,
        "decision": decision,
        "target_label_sha256": _sha256(label_path),
        "target_label_connected_after_all_probability_seals": True,
        "target_prefix_labels_used": False,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    _write_json(output_dir / "results.json", result)
    _write_json(
        output_dir / "status.json",
        {
            "state": "finished",
            "verdict": verdict,
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        },
    )
    print(
        f"候选B评价完成：裁决={verdict} 角色分离AP={role_ap:.9f} "
        f"离散AP={discrete_ap:.9f} final_accessed=false",
        flush=True,
    )
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser(
        "prepare", help="拟合源训练时间变换并发布五变体共同训练顺序"
    )
    prepare_parser.add_argument("--cache-root", type=Path, required=True)
    prepare_parser.add_argument("--representation-root", type=Path, required=True)
    prepare_parser.add_argument("--target-prefix-representation-root", type=Path, required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)
    prepare_parser.add_argument("--config", type=Path, required=True)
    train_parser = subparsers.add_parser(
        "train", help="训练一个候选 B 变体并封存原始及时间诊断概率"
    )
    train_parser.add_argument("--cache-root", type=Path, required=True)
    train_parser.add_argument("--representation-root", type=Path, required=True)
    train_parser.add_argument("--target-prefix-representation-root", type=Path, required=True)
    train_parser.add_argument("--preparation-root", type=Path, required=True)
    train_parser.add_argument("--output-dir", type=Path, required=True)
    train_parser.add_argument("--config", type=Path, required=True)
    train_parser.add_argument("--variant", choices=VARIANTS, required=True)
    train_parser.add_argument("--run-name", required=True)
    evaluate_parser = subparsers.add_parser(
        "evaluate", help="在全部概率封存后连接目标标签并独立评价"
    )
    evaluate_parser.add_argument("--cache-root", type=Path, required=True)
    evaluate_parser.add_argument("--preparation-root", type=Path, required=True)
    evaluate_parser.add_argument("--run-root", type=Path, required=True)
    evaluate_parser.add_argument("--output-dir", type=Path, required=True)
    evaluate_parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "prepare":
        result = prepare(
            args.cache_root,
            args.representation_root,
            args.target_prefix_representation_root,
            args.output_dir,
            args.config,
        )
    elif args.command == "train":
        result = train_variant(
            args.cache_root,
            args.representation_root,
            args.target_prefix_representation_root,
            args.preparation_root,
            args.output_dir,
            args.config,
            args.variant,
            args.run_name,
        )
    elif args.command == "evaluate":
        result = evaluate(
            args.cache_root,
            args.preparation_root,
            args.run_root,
            args.output_dir,
            args.config,
        )
    else:
        raise CandidateBTrainError(f"未知命令：{args.command}")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
