"""R1 源时间环境与上下文尾部风险 Q0 训练、封存和独立评价入口。"""

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
import scipy
import sklearn
import torch
from numpy.lib.format import open_memmap
from scipy.stats import binom, genpareto
from sklearn.metrics import average_precision_score, brier_score_loss
from torch import nn
from torch.nn import functional as F

from flow_probe.c12_crossyear_models import (
    C12ModelConfig,
    Rwkv7Kernel,
    trainable_parameter_count,
)
from flow_probe.c12_crossyear_train import (
    SequenceRole,
    _load_target_prefix_representation,
    load_cache,
)
from flow_probe.r1_source_environment import (
    EnvironmentBundle,
    R1Error,
    _append_jsonl,
    _environment,
    _load_environments as _load_legacy_environments,
    _load_frozen_representations,
    _probe_environment_auc,
    _row_environment,
    _seed_everything,
    _sequence_batch,
    _sha256,
    _write_json,
    _write_npy,
    _write_npz,
    prepare_environments as _prepare_legacy_environments,
)
from flow_probe.tracking import REQUIRED_SWANLAB_PROJECT, REQUIRED_SWANLAB_WORKSPACE


CONFIG_SCHEMA = "r1-tail-risk-q0-config-v1"
RUN_SCHEMA = "r1-tail-risk-q0-run-v1"
PREDICTION_SCHEMA = "r1-tail-risk-sealed-probabilities-v1"
RISK_SCHEMA = "r1-context-tail-risk-sealed-scores-v1"
EVALUATION_SCHEMA = "r1-tail-risk-q0-evaluation-v1"
VARIANTS = ("ERM", "GROUPDRO", "VREX", "CVAR", "TAILRISK")
DISPLAY_NAMES = {
    "ERM": "R1-ERM 共享状态评分基线",
    "GROUPDRO": "R1-GroupDRO 最坏源时间环境风险",
    "VREX": "R1-V-REx 源环境风险外推",
    "CVAR": "R1-CVaR 环境内样本尾部风险",
    "TAILRISK": "R1-双层尾部风险状态学习",
}


class TailRiskError(R1Error):
    """双层尾部风险实验合同被违反。"""


class SharedStateScorer(nn.Module):
    """五个目标完全共享的 RWKV-7 式逐流状态评分器。"""

    def __init__(self, config: C12ModelConfig) -> None:
        super().__init__()
        self.state = Rwkv7Kernel(config)
        self.classifier = nn.Sequential(
            nn.LayerNorm(config.hidden_size * 2),
            nn.Linear(config.hidden_size * 2, config.hidden_size),
            nn.GELU(),
            nn.Linear(config.hidden_size, 1),
        )

    def classify(
        self, values: torch.Tensor, valid: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        state = self.state(values, valid)
        logits = self.classifier(torch.cat((values, state), dim=-1)).squeeze(-1)
        return logits, state


class SwanTracker:
    """每个训练变体独占一个在线 SwanLab 运行。"""

    def __init__(
        self,
        output_dir: Path,
        run_name: str,
        variant: str,
        config: Mapping[str, Any],
    ) -> None:
        _assert_swanlab_destination(config)
        import swanlab

        self.client = swanlab
        self.run = swanlab.init(
            project=REQUIRED_SWANLAB_PROJECT,
            workspace=REQUIRED_SWANLAB_WORKSPACE,
            name=run_name,
            description="R1 源时间环境与上下文尾部风险 Q0 快速筛选",
            config={**dict(config), "variant": variant},
            mode="online",
            tags=["r1", "tail-risk", variant.lower(), "q0", "seed42"],
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
        raise TailRiskError(f"JSON 顶层必须是对象：{path}")
    return value


def _load_config(path: Path) -> dict[str, Any]:
    config = _read_json(path.resolve())
    if config.get("schema_version") != CONFIG_SCHEMA:
        raise TailRiskError("R1 双层尾部风险配置模式不匹配")
    fixed = {
        "seed": 42,
        "epochs": 4,
        "batch_size_sequences": 16,
        "maximum_sequence_length": 128,
        "hidden_size": 192,
        "steps_per_epoch": 183,
        "total_training_steps": 732,
        "maximum_concurrent_variants": 3,
    }
    for key, expected in fixed.items():
        if config.get(key) != expected:
            raise TailRiskError(f"Q0 冻结配置不匹配：{key} 必须为 {expected}")
    variant_keys = [item.get("key") for item in config.get("variants", [])]
    if variant_keys != list(VARIANTS):
        raise TailRiskError("训练变体必须按冻结顺序包含五种共同架构目标")
    if (
        config.get("screening_only") is not True
        or config.get("formal_paper_evidence") is not False
        or config.get("final_accessed") is not False
    ):
        raise TailRiskError("Q0 证据等级或最终区状态不合法")
    _assert_swanlab_destination(config)
    return config


def _assert_swanlab_destination(config: Mapping[str, Any]) -> None:
    swanlab_config = config.get("swanlab")
    if not isinstance(swanlab_config, Mapping):
        raise TailRiskError("SwanLab 冻结目的地缺失")
    if (
        swanlab_config.get("workspace") != REQUIRED_SWANLAB_WORKSPACE
        or swanlab_config.get("project") != REQUIRED_SWANLAB_PROJECT
        or swanlab_config.get("mode") != "online"
    ):
        raise TailRiskError("SwanLab 工作区、项目或模式与授权不一致")


def _identity_sha256(role: SequenceRole) -> str:
    digest = hashlib.sha256(b"r1-tail-risk-row-identity-v1\0")
    for array in (role.sample_id, role.sequence_id, role.position, role.valid_length):
        digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


def _environment_bundle(
    cache_root: Path,
    representation_root: Path,
    environment_root: Path,
    roles: Mapping[str, SequenceRole],
) -> EnvironmentBundle:
    receipt = _read_json(environment_root / "training-sampling-receipt.json")
    if (
        receipt.get("shared_by_variants") != list(VARIANTS)
        or receipt.get("fixed_budget_steps") != 732
        or receipt.get("batch_size_sequences") != 16
        or receipt.get("epochs") != 4
    ):
        raise TailRiskError("环境×标签共享训练顺序未绑定五变体或 732 步预算")
    return _load_legacy_environments(
        cache_root, representation_root, environment_root, roles
    )


def prepare_environments(
    cache_root: Path,
    representation_root: Path,
    output_dir: Path,
    config_path: Path,
) -> dict[str, Any]:
    """复用既有标签盲环境算法，并把共享顺序重新绑定到五个新目标。"""
    config = _load_config(config_path)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    compatibility_path = output_dir.parent / f".r1-tail-risk-env-config.{os.getpid()}.json"
    compatibility = dict(config)
    compatibility["schema_version"] = "r1-source-environment-q0-config-v1"
    try:
        _write_json(compatibility_path, compatibility)
        manifest = _prepare_legacy_environments(
            cache_root,
            representation_root,
            output_dir,
            compatibility_path,
        )
    finally:
        compatibility_path.unlink(missing_ok=True)
    sampling_path = output_dir / "training-sampling-receipt.json"
    sampling = _read_json(sampling_path)
    sampling["shared_by_variants"] = list(VARIANTS)
    sampling["shared_model_architecture"] = "SharedStateScorer"
    sampling["shared_parameter_count_required"] = True
    if sampling.get("fixed_budget_steps") != 732:
        raise TailRiskError("真实 Q0 缓存未形成冻结的 732 步预算")
    _write_json(sampling_path, sampling)
    manifest["sampling_receipt_sha256"] = _sha256(sampling_path)
    manifest["tail_risk_variants"] = list(VARIANTS)
    manifest["shared_model_architecture"] = "SharedStateScorer"
    _write_json(output_dir / "environment-manifest.json", manifest)
    return manifest


def _tail_mean(losses: torch.Tensor, rho: float) -> torch.Tensor:
    if losses.ndim != 1 or not len(losses):
        raise TailRiskError("CVaR 要求非空的一维逐样本损失")
    count = max(1, int(math.ceil(rho * len(losses))))
    return torch.topk(losses, count, largest=True, sorted=False).values.mean()


def _objective_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    valid: torch.Tensor,
    environments: torch.Tensor,
    variant: str,
    dro_weights: torch.Tensor,
    config: Mapping[str, Any],
) -> tuple[torch.Tensor, torch.Tensor, dict[str, float]]:
    row_losses = F.binary_cross_entropy_with_logits(logits, labels, reduction="none")
    risks: list[torch.Tensor] = []
    tails: list[torch.Tensor] = []
    active: list[int] = []
    rho = float(config["risk_objective"]["rho"])
    for environment in range(4):
        mask = valid & (environments == environment).unsqueeze(1)
        if torch.any(mask):
            losses = row_losses[mask].float()
            risks.append(losses.mean())
            tails.append(_tail_mean(losses, rho))
            active.append(environment)
    if not risks:
        raise TailRiskError("训练批次没有有效的源时间环境")
    risk_tensor = torch.stack(risks)
    tail_tensor = torch.stack(tails)
    updated = dro_weights.clone()
    if variant == "ERM":
        loss = row_losses[valid].float().mean()
    elif variant == "GROUPDRO":
        indices = torch.tensor(active, device=dro_weights.device, dtype=torch.long)
        updated[indices] *= torch.exp(
            float(config["risk_objective"]["groupdro_eta"])
            * risk_tensor.detach()
        )
        updated /= updated.sum()
        loss = torch.sum(updated[indices] * risk_tensor)
    elif variant == "VREX":
        beta = float(config["risk_objective"]["beta"])
        loss = risk_tensor.mean() + beta * risk_tensor.var(unbiased=False)
    elif variant == "CVAR":
        loss = tail_tensor.mean()
    elif variant == "TAILRISK":
        weight = float(config["risk_objective"]["lambda"])
        loss = torch.max((1.0 - weight) * risk_tensor + weight * tail_tensor)
    else:
        raise TailRiskError(f"未知训练变体：{variant}")
    metrics: dict[str, float] = {
        "loss": float(loss.detach().cpu()),
        "mean_environment_risk": float(risk_tensor.detach().mean().cpu()),
        "maximum_environment_risk": float(risk_tensor.detach().max().cpu()),
        "mean_environment_tail_risk": float(tail_tensor.detach().mean().cpu()),
        "maximum_environment_tail_risk": float(tail_tensor.detach().max().cpu()),
    }
    for environment, risk, tail in zip(active, risks, tails, strict=True):
        metrics[f"environment_{environment}_risk"] = float(risk.detach().cpu())
        metrics[f"environment_{environment}_tail_risk"] = float(tail.detach().cpu())
    return loss, updated.detach(), metrics


def _save_checkpoint(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    torch.save(dict(payload), partial)
    os.replace(partial, path)


def _checkpoint_payload(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    variant: str,
    binding: Mapping[str, object],
    next_epoch: int,
    next_batch: int,
    global_step: int,
    dro_weights: torch.Tensor,
    epoch_sums: Mapping[str, float],
    epoch_batches: int,
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": "r1-tail-risk-checkpoint-v1",
        "variant": variant,
        "binding": dict(binding),
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict(),
        "next_epoch": next_epoch,
        "next_batch": next_batch,
        "global_step": global_step,
        "dro_weights": dro_weights.detach().cpu(),
        "epoch_sums": dict(epoch_sums),
        "epoch_batches": epoch_batches,
        "python_random_state": random.getstate(),
        "numpy_random_state": np.random.get_state(),
        "torch_random_state": torch.random.get_rng_state(),
        "final_accessed": False,
    }
    if torch.cuda.is_available():
        result["cuda_random_states"] = torch.cuda.get_rng_state_all()
    return result


def _restore_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    variant: str,
    binding: Mapping[str, object],
    device: torch.device,
) -> tuple[int, int, int, torch.Tensor, dict[str, float], int]:
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    if (
        checkpoint.get("schema_version") != "r1-tail-risk-checkpoint-v1"
        or checkpoint.get("variant") != variant
        or checkpoint.get("binding") != dict(binding)
        or checkpoint.get("final_accessed") is not False
    ):
        raise TailRiskError("恢复检查点身份绑定不一致")
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
        checkpoint["dro_weights"].to(device=device, dtype=torch.float32),
        {str(key): float(value) for key, value in checkpoint["epoch_sums"].items()},
        int(checkpoint["epoch_batches"]),
    )


def _seal_predictions(
    output_dir: Path,
    role: SequenceRole,
    probabilities: np.ndarray,
) -> dict[str, Any]:
    if probabilities.shape != (role.row_count,) or not np.isfinite(probabilities).all():
        raise TailRiskError(f"{role.role} 概率形状不合法或包含非有限值")
    path = output_dir / "predictions" / f"{role.role}.npz"
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
        "path": str(path.resolve()),
        "sha256": _sha256(path),
        "identity_sha256": _identity_sha256(role),
        "row_count": role.row_count,
        "sequence_count": role.sequence_count,
        "labels_read": role.role in {"source-train", "source-validation"},
        "target_labels_read": False,
        "sealed_before_target_evaluation": True,
        "final_accessed": False,
    }
    _write_json(output_dir / "predictions" / f"{role.role}-receipt.json", receipt)
    return receipt


def _predict_role(
    model: SharedStateScorer,
    role: SequenceRole,
    representation: np.ndarray,
    output_dir: Path,
    batch_size: int,
    device: torch.device,
    save_state: bool,
    progress_interval_rows: int,
) -> tuple[dict[str, Any], dict[str, Any] | None, float]:
    model.eval()
    probabilities = np.empty(role.row_count, dtype=np.float32)
    state_path: Path | None = None
    state_output: np.memmap | None = None
    state_partial: Path | None = None
    if save_state:
        state_path = output_dir / "states" / f"{role.role}.npy"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_partial = state_path.with_suffix(f".npy.partial.{os.getpid()}")
        state_output = open_memmap(
            state_partial,
            mode="w+",
            dtype=np.float16,
            shape=(role.row_count, representation.shape[1]),
        )
    started = time.perf_counter()
    processed = 0
    next_progress = progress_interval_rows
    with torch.no_grad():
        for offset in range(0, role.sequence_count, batch_size):
            indices = np.arange(offset, min(offset + batch_size, role.sequence_count))
            values, valid, _, _ = _sequence_batch(role, representation, indices, None)
            values = values.to(device, non_blocking=True)
            valid_device = valid.to(device, non_blocking=True)
            with torch.autocast(
                device_type=device.type,
                dtype=torch.bfloat16,
                enabled=device.type == "cuda",
            ):
                logits, state = model.classify(values, valid_device)
            probability_np = torch.sigmoid(logits).float().cpu().numpy()
            state_np = state.float().cpu().numpy()
            valid_np = valid.numpy()
            for batch_index, sequence_index in enumerate(indices):
                start = int(role.starts[sequence_index])
                length = int(role.lengths[sequence_index])
                row_mask = valid_np[batch_index]
                probabilities[start : start + length] = probability_np[batch_index][row_mask]
                if state_output is not None:
                    state_output[start : start + length] = state_np[batch_index][row_mask].astype(
                        np.float16
                    )
                processed += length
            if processed >= next_progress or processed == role.row_count:
                elapsed = time.perf_counter() - started
                rate = processed / max(elapsed, 1e-9)
                remaining = (role.row_count - processed) / max(rate, 1e-9)
                print(
                    f"概率封存：角色={role.role} 已处理={processed}/{role.row_count} "
                    f"吞吐={rate:.1f}行/秒 预计剩余={remaining:.1f}秒",
                    flush=True,
                )
                next_progress += progress_interval_rows
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    if state_output is not None and state_partial is not None and state_path is not None:
        state_output.flush()
        del state_output
        os.replace(state_partial, state_path)
    prediction_receipt = _seal_predictions(output_dir, role, probabilities)
    state_receipt = None
    if state_path is not None:
        state_receipt = {
            "path": str(state_path.resolve()),
            "sha256": _sha256(state_path),
            "shape": [role.row_count, representation.shape[1]],
            "dtype": "float16",
            "identity_sha256": _identity_sha256(role),
        }
    return prediction_receipt, state_receipt, time.perf_counter() - started


def train_variant(
    cache_root: Path,
    representation_root: Path,
    target_prefix_representation_root: Path,
    environment_root: Path,
    output_dir: Path,
    config_path: Path,
    variant: str,
    run_name: str,
) -> dict[str, Any]:
    """用完全相同的状态评分模型与顺序训练一个风险目标。"""
    if variant not in VARIANTS:
        raise TailRiskError(f"未知训练变体：{variant}")
    config = _load_config(config_path)
    _assert_swanlab_destination(config)
    _seed_everything(int(config["seed"]))
    cache_manifest, roles = load_cache(cache_root)
    representations, representation_receipt = _load_frozen_representations(
        cache_root, representation_root
    )
    target_prefix_representation, target_prefix_receipt = _load_target_prefix_representation(
        cache_root, target_prefix_representation_root
    )
    if target_prefix_receipt.get("labels_read") is not False:
        raise TailRiskError("目标前缀冻结表示违反 labels_read=false")
    if len(target_prefix_representation) != roles["target-prefix"].row_count:
        raise TailRiskError("目标前缀冻结表示与缓存行数不一致")
    environments = _environment_bundle(
        cache_root, representation_root, environment_root, roles
    )
    order = environments.training_order
    expected_shape = (
        int(config["epochs"]),
        int(config["steps_per_epoch"]),
        int(config["batch_size_sequences"]),
    )
    if order.shape != expected_shape or int(np.prod(order.shape[:2])) != 732:
        raise TailRiskError("共享训练序列顺序不是冻结的 4 轮 732 步")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise TailRiskError("R1 Q0 真实训练要求 CUDA")
    model = SharedStateScorer(C12ModelConfig()).to(device)
    parameter_count = trainable_parameter_count(model)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=int(config["epochs"])
    )
    objective_binding = {
        key: config["risk_objective"][key]
        for key in ("beta", "rho", "lambda", "groupdro_eta")
    }
    binding = {
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "representation_manifest_sha256": _sha256(
            representation_root / "representation-manifest.json"
        ),
        "target_prefix_representation_manifest_sha256": _sha256(
            target_prefix_representation_root
            / "target-prefix-representation-manifest.json"
        ),
        "environment_manifest_sha256": _sha256(
            environment_root / "environment-manifest.json"
        ),
        "training_order_sha256": _sha256(
            environment_root / "training-sequence-order.npy"
        ),
        "config_sha256": _sha256(config_path),
        "variant": variant,
        "seed": int(config["seed"]),
        "objective_parameters": objective_binding,
    }
    snapshot = {
        "schema_version": RUN_SCHEMA,
        "variant": variant,
        "display_name": DISPLAY_NAMES[variant],
        "run_name": run_name,
        "binding": binding,
        "model_class": "SharedStateScorer",
        "trainable_parameter_count": parameter_count,
        "shared_architecture_for_all_variants": True,
        "shared_parameter_count_for_all_variants": True,
        "shared_training_order_for_all_variants": True,
        "model_inputs": ["frozen_receiver_representation"],
        "forbidden_model_inputs": [
            "environment",
            "group_key_ref",
            "sample_id",
            "sequence_id",
            "position",
            "valid_length",
            "year_role",
            "label",
        ],
        "environment_used_for": "共享采样与损失聚合，不进入状态评分模型输入",
        "target_prefix_labels_used": False,
        "target_development_labels_used": False,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
        "config": config,
        "cache_schema": cache_manifest["schema_version"],
        "receiver_checkpoint_sha256": representation_receipt.get(
            "receiver_checkpoint_sha256"
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = output_dir / "config.json"
    if snapshot_path.exists():
        existing = _read_json(snapshot_path)
        if existing.get("binding") != binding or existing.get("variant") != variant:
            raise TailRiskError("已有运行目录与当前冻结身份不一致")
    else:
        _write_json(snapshot_path, snapshot)
        environment_receipt = _environment(device)
        environment_receipt.update(
            {
                "scipy": scipy.__version__,
                "scikit_learn": sklearn.__version__,
            }
        )
        _write_json(output_dir / "environment-receipt.json", environment_receipt)
    _write_json(
        output_dir / "status.json",
        {
            "state": "running",
            "variant": variant,
            "target_prefix_labels_used": False,
            "target_development_labels_used": False,
            "final_accessed": False,
        },
    )
    checkpoint_path = output_dir / "checkpoints" / "latest.pt"
    dro_weights = torch.full((4,), 0.25, device=device, dtype=torch.float32)
    start_epoch = 0
    start_batch = 0
    global_step = 0
    epoch_sums: dict[str, float] = {}
    epoch_batches = 0
    resumed = False
    if checkpoint_path.is_file():
        (
            start_epoch,
            start_batch,
            global_step,
            dro_weights,
            epoch_sums,
            epoch_batches,
        ) = _restore_checkpoint(
            checkpoint_path,
            model,
            optimizer,
            scheduler,
            variant,
            binding,
            device,
        )
        resumed = True
    tracker: SwanTracker | None = None
    started = time.perf_counter()
    epoch_receipts: list[dict[str, Any]] = []
    metrics_path = output_dir / "metrics" / "epochs.jsonl"
    if metrics_path.is_file():
        for line in metrics_path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            if isinstance(value, dict):
                epoch_receipts.append(value)
    train_role = roles["source-train"]
    if train_role.labels is None:
        raise TailRiskError("源训练标签缺失")
    torch.cuda.reset_peak_memory_stats(device)
    try:
        tracker = SwanTracker(output_dir, run_name, variant, config)
        for epoch in range(start_epoch, int(config["epochs"])):
            model.train()
            if epoch != start_epoch:
                epoch_sums = {}
                epoch_batches = 0
            batch_begin = start_batch if epoch == start_epoch else 0
            for batch_index in range(batch_begin, int(config["steps_per_epoch"])):
                sequence_indices = np.asarray(order[epoch, batch_index])
                values, valid, labels, batch_environments = _sequence_batch(
                    train_role,
                    representations["source-train"],
                    sequence_indices,
                    environments.train_environment,
                )
                if labels is None or batch_environments is None:
                    raise TailRiskError("训练批次缺少源标签或环境")
                values = values.to(device, non_blocking=True)
                valid = valid.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                batch_environments = batch_environments.to(device, non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits, _ = model.classify(values, valid)
                    loss, dro_weights, scalars = _objective_loss(
                        logits,
                        labels,
                        valid,
                        batch_environments,
                        variant,
                        dro_weights,
                        config,
                    )
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), float(config["gradient_clip_norm"])
                )
                optimizer.step()
                global_step += 1
                epoch_batches += 1
                for name, value in scalars.items():
                    epoch_sums[name] = epoch_sums.get(name, 0.0) + value
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
                            dro_weights,
                            epoch_sums,
                            epoch_batches,
                        ),
                    )
                if global_step % int(config["progress_interval_steps"]) == 0:
                    elapsed = time.perf_counter() - started
                    processed = max(global_step - start_epoch * int(config["steps_per_epoch"]), 1)
                    rate = processed / max(elapsed, 1e-9)
                    remaining = (732 - global_step) / max(rate, 1e-9)
                    print(
                        f"R1双层风险训练：变体={variant} 步={global_step}/732 "
                        f"吞吐={rate:.2f}步/秒 预计剩余={remaining:.1f}秒",
                        flush=True,
                    )
                    tracker.log(
                        {
                            **{f"train/{key}": value for key, value in scalars.items()},
                            "train/learning_rate": float(optimizer.param_groups[0]["lr"]),
                        },
                        step=global_step,
                    )
            scheduler.step()
            mean_metrics = {
                name: value / max(epoch_batches, 1)
                for name, value in epoch_sums.items()
            }
            epoch_receipt = {
                "epoch": epoch + 1,
                "steps": epoch_batches,
                "mean_metrics": mean_metrics,
                "environment_risks_recorded": True,
                "environment_tail_risks_recorded": True,
                "groupdro_weights": dro_weights.detach().cpu().tolist(),
                "training_order_sha256": binding["training_order_sha256"],
            }
            epoch_receipts.append(epoch_receipt)
            _append_jsonl(metrics_path, epoch_receipt)
            tracker.log(
                {f"epoch/{name}": value for name, value in mean_metrics.items()},
                step=global_step,
            )
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
                    dro_weights,
                    {},
                    0,
                ),
            )
            start_batch = 0
            epoch_sums = {}
            epoch_batches = 0
        if global_step != 732:
            raise TailRiskError(f"实际训练步数不是冻结预算 732：{global_step}")
        final_checkpoint = output_dir / "checkpoints" / "final.pt"
        _save_checkpoint(
            final_checkpoint,
            _checkpoint_payload(
                model,
                optimizer,
                scheduler,
                variant,
                binding,
                int(config["epochs"]),
                0,
                global_step,
                dro_weights,
                {},
                0,
            ),
        )
        all_representations = {
            **representations,
            "target-prefix": target_prefix_representation,
        }
        prediction_receipts: dict[str, Any] = {}
        state_records: dict[str, Any] = {}
        prediction_seconds: dict[str, float] = {}
        for role_name in (
            "source-train",
            "source-validation",
            "target-prefix",
            "target-development",
        ):
            prediction_receipt, state_receipt, seconds = _predict_role(
                model,
                roles[role_name],
                all_representations[role_name],
                output_dir,
                int(config["batch_size_sequences"]),
                device,
                save_state=role_name in {"source-train", "source-validation"},
                progress_interval_rows=int(config["prediction_progress_interval_rows"]),
            )
            prediction_receipts[role_name] = prediction_receipt
            prediction_seconds[role_name] = seconds
            if state_receipt is not None:
                state_records[role_name] = state_receipt
        state_manifest = {
            "schema_version": "r1-tail-risk-state-representations-v1",
            "variant": variant,
            "records": state_records,
            "environment_or_identity_used_as_model_input": False,
            "target_state_persisted": False,
            "final_accessed": False,
        }
        _write_json(output_dir / "states" / "manifest.json", state_manifest)
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
            "checkpoint_interval_steps": int(config["checkpoint_interval_steps"]),
            "model_class": "SharedStateScorer",
            "trainable_parameter_count": parameter_count,
            "objective_parameters": objective_binding,
            "binding": binding,
            "epoch_receipts": epoch_receipts,
            "prediction_receipts": prediction_receipts,
            "state_manifest_sha256": _sha256(output_dir / "states" / "manifest.json"),
            "final_checkpoint_sha256": _sha256(final_checkpoint),
            "prediction_seconds": prediction_seconds,
            "training_seconds": training_seconds,
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "swanlab_run_id": tracker.run_id,
            "target_prefix_labels_used": False,
            "target_development_labels_used": False,
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
                "all_four_role_probabilities_sealed": True,
                "target_prefix_labels_used": False,
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
                "target_prefix_labels_used": False,
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
) -> tuple[np.ndarray, dict[str, Any]]:
    receipt = _read_json(run_dir / "predictions" / f"{role.role}-receipt.json")
    path = run_dir / "predictions" / f"{role.role}.npz"
    if (
        receipt.get("schema_version") != PREDICTION_SCHEMA
        or receipt.get("role") != role.role
        or receipt.get("sha256") != _sha256(path)
        or receipt.get("identity_sha256") != _identity_sha256(role)
        or receipt.get("target_labels_read") is not False
        or receipt.get("final_accessed") is not False
    ):
        raise TailRiskError(f"{run_dir.name}/{role.role} 概率封存收据不合法")
    with np.load(path, allow_pickle=False) as values:
        expected = {
            "sample_id": role.sample_id,
            "sequence_id": role.sequence_id,
            "position": role.position,
            "valid_length": role.valid_length,
        }
        for key, identity in expected.items():
            if not np.array_equal(values[key], identity):
                raise TailRiskError(f"{run_dir.name}/{role.role} 身份键不逐项一致：{key}")
        probability = np.asarray(values["probability"], dtype=np.float64)
    if probability.shape != (role.row_count,) or not np.isfinite(probability).all():
        raise TailRiskError(f"{run_dir.name}/{role.role} 概率数组不合法")
    return probability, receipt


def _np_threshold(scores: np.ndarray, alpha: float, delta: float) -> dict[str, Any]:
    if scores.ndim != 1 or not len(scores) or not np.isfinite(scores).all():
        raise TailRiskError("NP 阈值要求非空有限源良性校准分数")
    ordered = np.sort(scores, kind="stable")
    low = 1
    high = len(ordered)
    while low < high:
        middle = (low + high) // 2
        violation = float(binom.sf(middle - 1, len(ordered), 1.0 - alpha))
        if violation <= delta:
            high = middle
        else:
            low = middle + 1
    order_threshold = float(ordered[low - 1])
    allowed = int(math.floor(alpha * len(ordered)))
    unique, group_counts = np.unique(ordered, return_counts=True)
    descending = unique[::-1]
    cumulative = np.cumsum(group_counts[::-1])
    valid = np.flatnonzero(cumulative <= allowed)
    tie_threshold = (
        float(descending[valid[-1]])
        if len(valid)
        else float(np.nextafter(ordered.max(), np.inf))
    )
    threshold = max(order_threshold, tie_threshold)
    actual = int(np.sum(ordered >= threshold))
    return {
        "alpha": alpha,
        "delta": delta,
        "source_benign_count": int(len(ordered)),
        "order_statistic_k_one_based": low,
        "order_statistic_threshold": order_threshold,
        "tie_safe_threshold": threshold,
        "allowed_false_positives": allowed,
        "actual_false_positives": actual,
        "violation_bound": float(binom.sf(low - 1, len(ordered), 1.0 - alpha)),
        "source_only": True,
    }


def _context_ids(
    position: np.ndarray,
    valid_length: np.ndarray,
    position_boundaries: list[int],
    length_boundaries: list[int],
) -> tuple[np.ndarray, int, int]:
    position_bucket = np.searchsorted(
        np.asarray(position_boundaries), position, side="right"
    )
    length_bucket = np.searchsorted(
        np.asarray(length_boundaries), valid_length, side="right"
    )
    position_count = len(position_boundaries) + 1
    length_count = len(length_boundaries) + 1
    return (
        (length_bucket * position_count + position_bucket).astype(np.int16),
        position_count,
        length_count,
    )


def _capped_prefix(
    source: np.ndarray,
    prefix: np.ndarray,
    maximum_weight: float,
) -> np.ndarray:
    maximum = min(len(prefix), int(math.floor(len(source) * maximum_weight)))
    if maximum <= 0:
        return np.empty(0, dtype=np.float64)
    indices = np.linspace(0, len(prefix) - 1, maximum, dtype=np.int64)
    return np.asarray(prefix[indices], dtype=np.float64)


def _empirical_risk(
    reference: np.ndarray,
    scores: np.ndarray,
    smoothing: float,
    survival_floor: float,
) -> np.ndarray:
    ordered = np.sort(np.asarray(reference, dtype=np.float64), kind="stable")
    ranks = np.searchsorted(ordered, scores, side="left")
    survival = (len(ordered) - ranks + smoothing) / (len(ordered) + smoothing)
    return -np.log(np.clip(survival, survival_floor, 1.0))


def _fit_and_score_contexts(
    source_scores: np.ndarray,
    source_context: np.ndarray,
    prefix_scores: np.ndarray,
    prefix_context: np.ndarray,
    target_scores: np.ndarray,
    target_context: np.ndarray,
    config: Mapping[str, Any],
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    risk_config = config["context_tail_risk"]
    minimum_source = int(risk_config["minimum_source_benign_per_context"])
    minimum_exceedances = int(risk_config["minimum_gpd_exceedances"])
    maximum_weight = float(risk_config["target_prefix_maximum_weight"])
    quantile = float(risk_config["tail_start_quantile"])
    smoothing = float(risk_config["empirical_smoothing"])
    survival_floor = float(risk_config["survival_floor"])
    empirical = np.empty(len(target_scores), dtype=np.float64)
    gpd = np.empty(len(target_scores), dtype=np.float64)
    global_source = np.asarray(source_scores, dtype=np.float64)
    global_prefix = _capped_prefix(global_source, prefix_scores, maximum_weight)
    context_receipts: dict[str, Any] = {}
    for context in sorted(set(target_context.tolist())):
        target_mask = target_context == context
        source_local = np.asarray(source_scores[source_context == context], dtype=np.float64)
        prefix_local = np.asarray(prefix_scores[prefix_context == context], dtype=np.float64)
        fallback_reason: str | None = None
        if len(source_local) < minimum_source:
            source_reference = global_source
            prefix_reference = global_prefix
            fallback_reason = "源上下文良性样本不足，回退全局源锚"
        else:
            source_reference = source_local
            prefix_reference = _capped_prefix(
                source_reference, prefix_local, maximum_weight
            )
        combined = np.concatenate((source_reference, prefix_reference))
        empirical[target_mask] = _empirical_risk(
            combined, target_scores[target_mask], smoothing, survival_floor
        )
        threshold = float(np.quantile(combined, quantile, method="higher"))
        exceedances = combined[combined > threshold] - threshold
        fit_status = "fitted"
        fit_reason = fallback_reason
        shape: float | None = None
        scale: float | None = None
        if len(exceedances) >= minimum_exceedances:
            try:
                fitted_shape, fitted_loc, fitted_scale = genpareto.fit(
                    exceedances, floc=0.0
                )
                if (
                    not np.isfinite((fitted_shape, fitted_loc, fitted_scale)).all()
                    or fitted_loc != 0.0
                    or fitted_scale <= 0.0
                ):
                    raise ValueError("广义帕累托参数非有限、位置非零或尺度非正")
                shape = float(fitted_shape)
                scale = float(fitted_scale)
                selected = target_scores[target_mask]
                base = _empirical_risk(combined, selected, smoothing, survival_floor)
                above = selected > threshold
                if np.any(above):
                    tail_fraction = len(exceedances) / len(combined)
                    survival = tail_fraction * genpareto.sf(
                        selected[above] - threshold,
                        shape,
                        loc=0.0,
                        scale=scale,
                    )
                    base[above] = -np.log(
                        np.clip(survival, survival_floor, 1.0)
                    )
                gpd[target_mask] = base
            except (ValueError, RuntimeError, FloatingPointError) as error:
                fit_status = "fallback_source_empirical"
                fit_reason = f"{type(error).__name__}: {error}"
                gpd[target_mask] = _empirical_risk(
                    source_reference,
                    target_scores[target_mask],
                    smoothing,
                    survival_floor,
                )
        else:
            fit_status = "fallback_source_empirical"
            fit_reason = (
                f"超阈样本不足：{len(exceedances)} < {minimum_exceedances}"
            )
            gpd[target_mask] = _empirical_risk(
                source_reference,
                target_scores[target_mask],
                smoothing,
                survival_floor,
            )
        context_receipts[str(context)] = {
            "source_anchor_count": int(len(source_reference)),
            "target_prefix_available_count": int(len(prefix_local)),
            "target_prefix_used_count": int(len(prefix_reference)),
            "target_prefix_effective_weight": float(
                len(prefix_reference) / max(len(source_reference), 1)
            ),
            "target_prefix_maximum_weight": maximum_weight,
            "tail_start_quantile": quantile,
            "tail_threshold": threshold,
            "exceedance_count": int(len(exceedances)),
            "gpd_shape": shape,
            "gpd_scale": scale,
            "gpd_status": fit_status,
            "fallback_reason": fit_reason,
            "target_score_count": int(target_mask.sum()),
        }
    if not np.isfinite(empirical).all() or not np.isfinite(gpd).all():
        raise TailRiskError("上下文尾部风险分数包含非有限值")
    return empirical, gpd, context_receipts


def _stable_perturbation(
    probabilities: np.ndarray,
    sample_id: np.ndarray,
    epsilon: float,
) -> np.ndarray:
    flat = np.ascontiguousarray(sample_id).view(np.uint8).reshape(len(sample_id), -1)
    signs = np.where(np.bitwise_xor.reduce(flat, axis=1) % 2 == 0, -1.0, 1.0)
    return np.clip(probabilities + epsilon * signs, 0.0, 1.0)


def fit_risk(
    cache_root: Path,
    representation_root: Path,
    environment_root: Path,
    run_dir: Path,
    output_dir: Path,
    config_path: Path,
) -> dict[str, Any]:
    """只用源校准标签、源概率和无标签目标前缀拟合冻结风险映射。"""
    if output_dir.exists():
        raise TailRiskError("风险拟合输出目录已存在，拒绝覆盖")
    config = _load_config(config_path)
    _, roles = load_cache(cache_root)
    environments = _environment_bundle(
        cache_root, representation_root, environment_root, roles
    )
    status = _read_json(run_dir / "status.json")
    if (
        status.get("state") != "probabilities_sealed_evaluation_pending"
        or status.get("all_four_role_probabilities_sealed") is not True
        or status.get("target_prefix_labels_used") is not False
        or status.get("target_development_labels_used") is not False
    ):
        raise TailRiskError("训练变体尚未完成四角色概率封存")
    source_probability, source_receipt = _load_sealed_probability(
        run_dir, roles["source-validation"]
    )
    prefix_probability, prefix_receipt = _load_sealed_probability(
        run_dir, roles["target-prefix"]
    )
    target_probability, target_receipt = _load_sealed_probability(
        run_dir, roles["target-development"]
    )
    source_role = roles["source-validation"]
    if source_role.labels is None:
        raise TailRiskError("源验证校准标签缺失")
    row_partition = _row_environment(source_role, environments.validation_partition)
    calibration_benign = (row_partition == 1) & (np.asarray(source_role.labels) == 0)
    source_scores = source_probability[calibration_benign]
    risk_config = config["context_tail_risk"]
    position_boundaries = [int(value) for value in risk_config["position_boundaries"]]
    length_boundaries = [int(value) for value in risk_config["valid_length_boundaries"]]
    source_context_all, position_count, length_count = _context_ids(
        np.asarray(source_role.position),
        np.asarray(source_role.valid_length),
        position_boundaries,
        length_boundaries,
    )
    prefix_context, _, _ = _context_ids(
        np.asarray(roles["target-prefix"].position),
        np.asarray(roles["target-prefix"].valid_length),
        position_boundaries,
        length_boundaries,
    )
    target_context, _, _ = _context_ids(
        np.asarray(roles["target-development"].position),
        np.asarray(roles["target-development"].valid_length),
        position_boundaries,
        length_boundaries,
    )
    empirical, gpd, model_receipts = _fit_and_score_contexts(
        source_scores,
        source_context_all[calibration_benign],
        prefix_probability,
        prefix_context,
        target_probability,
        target_context,
        config,
    )
    np_receipt = _np_threshold(
        source_scores,
        float(risk_config["np_alpha"]),
        float(risk_config["np_delta"]),
    )
    np_indicator = target_probability >= float(np_receipt["tie_safe_threshold"])
    epsilon = float(risk_config["stability_perturbation_epsilon"])
    perturbed_prefix = _stable_perturbation(
        prefix_probability,
        np.asarray(roles["target-prefix"].sample_id),
        epsilon,
    )
    empirical_perturbed, gpd_perturbed, _ = _fit_and_score_contexts(
        source_scores,
        source_context_all[calibration_benign],
        perturbed_prefix,
        prefix_context,
        target_probability,
        target_context,
        config,
    )
    primary_budget = int(config["evaluation"]["primary_alert_budget_per_million"])
    top_k = max(1, int(math.floor(len(target_probability) * primary_budget / 1_000_000)))

    def top_indices(values: np.ndarray) -> np.ndarray:
        return np.argsort(-values, kind="stable")[:top_k]

    empirical_overlap = len(
        np.intersect1d(top_indices(empirical), top_indices(empirical_perturbed))
    ) / top_k
    gpd_overlap = len(np.intersect1d(top_indices(gpd), top_indices(gpd_perturbed))) / top_k
    output_dir.mkdir(parents=True)
    score_path = output_dir / "risk-score.npz"
    target_role = roles["target-development"]
    _write_npz(
        score_path,
        raw_probability=np.asarray(target_probability, dtype=np.float32),
        np_indicator=np.asarray(np_indicator, dtype=np.uint8),
        empirical_risk=np.asarray(empirical, dtype=np.float64),
        gpd_risk=np.asarray(gpd, dtype=np.float64),
        context_id=np.asarray(target_context, dtype=np.int16),
        sample_id=np.asarray(target_role.sample_id),
        sequence_id=np.asarray(target_role.sequence_id),
        position=np.asarray(target_role.position),
        valid_length=np.asarray(target_role.valid_length),
    )
    context_receipt = {
        "schema_version": "r1-tail-risk-context-buckets-v1",
        "position_boundaries": position_boundaries,
        "valid_length_boundaries": length_boundaries,
        "position_bucket_count": position_count,
        "valid_length_bucket_count": length_count,
        "context_count": position_count * length_count,
        "source_calibration_benign_counts": {
            str(context): int(
                np.sum(source_context_all[calibration_benign] == context)
            )
            for context in range(position_count * length_count)
        },
        "target_prefix_counts": {
            str(context): int(np.sum(prefix_context == context))
            for context in range(position_count * length_count)
        },
        "target_development_counts_without_labels": {
            str(context): int(np.sum(target_context == context))
            for context in range(position_count * length_count)
        },
        "bucket_parameters_selected_from_target_labels": False,
        "final_accessed": False,
    }
    _write_json(output_dir / "context-bucket-receipt.json", context_receipt)
    stability = {
        "schema_version": "r1-tail-risk-prefix-stability-v1",
        "perturbation": "按 sample_id 固定奇偶符号加减 epsilon 后截断到 [0,1]",
        "epsilon": epsilon,
        "primary_top_k": top_k,
        "empirical_top_k_overlap": empirical_overlap,
        "gpd_top_k_overlap": gpd_overlap,
        "empirical_maximum_absolute_score_change": float(
            np.max(np.abs(empirical - empirical_perturbed))
        ),
        "gpd_maximum_absolute_score_change": float(
            np.max(np.abs(gpd - gpd_perturbed))
        ),
        "target_labels_read": False,
        "final_accessed": False,
    }
    _write_json(output_dir / "stability-diagnostic.json", stability)
    risk_receipt = {
        "schema_version": RISK_SCHEMA,
        "state": "risk_scores_sealed_evaluation_pending",
        "variant": status["variant"],
        "risk_score_path": str(score_path.resolve()),
        "risk_score_sha256": _sha256(score_path),
        "target_identity_sha256": _identity_sha256(target_role),
        "source_validation_probability_sha256": source_receipt["sha256"],
        "target_prefix_probability_sha256": prefix_receipt["sha256"],
        "target_development_probability_sha256": target_receipt["sha256"],
        "np_source_anchor": np_receipt,
        "context_models": model_receipts,
        "context_bucket_receipt_sha256": _sha256(
            output_dir / "context-bucket-receipt.json"
        ),
        "stability_diagnostic_sha256": _sha256(
            output_dir / "stability-diagnostic.json"
        ),
        "source_anchor_labels_read": True,
        "target_prefix_labels_read": False,
        "target_development_labels_read": False,
        "risk_parameters_selected_from_target_labels": False,
        "scores_sealed_before_target_label_connection": True,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    _write_json(output_dir / "risk-model-receipt.json", risk_receipt)
    _write_json(
        output_dir / "status.json",
        {
            "state": "risk_scores_sealed_evaluation_pending",
            "variant": status["variant"],
            "target_prefix_labels_read": False,
            "target_development_labels_read": False,
            "final_accessed": False,
        },
    )
    return risk_receipt


def _load_risk_scores(
    risk_dir: Path,
    role: SequenceRole,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    receipt = _read_json(risk_dir / "risk-model-receipt.json")
    status = _read_json(risk_dir / "status.json")
    path = risk_dir / "risk-score.npz"
    if (
        receipt.get("schema_version") != RISK_SCHEMA
        or receipt.get("state") != "risk_scores_sealed_evaluation_pending"
        or status.get("state") != "risk_scores_sealed_evaluation_pending"
        or receipt.get("risk_score_sha256") != _sha256(path)
        or receipt.get("target_identity_sha256") != _identity_sha256(role)
        or receipt.get("target_development_labels_read") is not False
        or receipt.get("final_accessed") is not False
    ):
        raise TailRiskError(f"{risk_dir.name} 风险分数封存收据不合法")
    with np.load(path, allow_pickle=False) as values:
        for key, expected in (
            ("sample_id", role.sample_id),
            ("sequence_id", role.sequence_id),
            ("position", role.position),
            ("valid_length", role.valid_length),
        ):
            if not np.array_equal(values[key], expected):
                raise TailRiskError(f"{risk_dir.name} 风险身份键不逐项一致：{key}")
        result = {
            key: np.asarray(values[key])
            for key in (
                "raw_probability",
                "np_indicator",
                "empirical_risk",
                "gpd_risk",
                "context_id",
            )
        }
    return result, receipt


def _ece(labels: np.ndarray, probabilities: np.ndarray, bins: int = 15) -> float:
    order = np.argsort(probabilities, kind="stable")
    error = 0.0
    for indices in np.array_split(order, bins):
        if len(indices):
            error += len(indices) / len(order) * abs(
                float(labels[indices].mean())
                - float(probabilities[indices].mean())
            )
    return float(error)


def _strict_top_k_recall(
    labels: np.ndarray,
    scores: np.ndarray,
    budgets: list[int],
) -> dict[str, Any]:
    order = np.argsort(-scores, kind="stable")
    malicious = int(np.sum(labels == 1))
    result: dict[str, Any] = {}
    for budget in budgets:
        count = int(math.floor(len(labels) * budget / 1_000_000))
        selected = order[:count]
        true_positives = int(np.sum(labels[selected] == 1))
        result[str(budget)] = {
            "top_k": count,
            "true_positives": true_positives,
            "recall": float(true_positives / max(malicious, 1)),
        }
    return result


def _fixed_recall_false_positives(
    labels: np.ndarray,
    scores: np.ndarray,
    recalls: list[float],
) -> dict[str, Any]:
    order = np.argsort(-scores, kind="stable")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    group_ends = np.r_[
        np.flatnonzero(sorted_scores[1:] != sorted_scores[:-1]), len(labels) - 1
    ]
    cumulative_tp = np.cumsum(sorted_labels == 1)[group_ends]
    cumulative_fp = np.cumsum(sorted_labels == 0)[group_ends]
    malicious = int(np.sum(labels == 1))
    result: dict[str, Any] = {}
    for recall in recalls:
        required = int(math.ceil(recall * malicious))
        valid = np.flatnonzero(cumulative_tp >= required)
        result[str(recall)] = (
            {
                "false_positives": int(cumulative_fp[valid[0]]),
                "achieved_recall": float(cumulative_tp[valid[0]] / max(malicious, 1)),
            }
            if len(valid)
            else {"false_positives": None, "achieved_recall": 0.0}
        )
    return result


def _score_metrics(
    labels: np.ndarray,
    scores: np.ndarray,
    calibration_probability: np.ndarray,
    recalls: list[float],
    budgets: list[int],
) -> dict[str, Any]:
    if not np.isfinite(scores).all() or not np.isfinite(calibration_probability).all():
        raise TailRiskError("评价分数或校准概率包含非有限值")
    prevalence = float(labels.mean())
    average_precision = float(average_precision_score(labels, scores))
    return {
        "average_precision": average_precision,
        "average_precision_over_prevalence": average_precision / max(prevalence, 1e-12),
        "prevalence": prevalence,
        "strict_global_top_k_recall": _strict_top_k_recall(labels, scores, budgets),
        "fixed_recall_false_positives": _fixed_recall_false_positives(
            labels, scores, recalls
        ),
        "brier": float(brier_score_loss(labels, calibration_probability)),
        "ece_15_equal_frequency": _ece(labels, calibration_probability),
    }


def _source_environment_risks(
    labels: np.ndarray,
    probabilities: np.ndarray,
    environments: np.ndarray,
    mask: np.ndarray,
) -> dict[str, Any]:
    clipped = np.clip(probabilities, 1e-7, 1.0 - 1e-7)
    losses = -(labels * np.log(clipped) + (1 - labels) * np.log1p(-clipped))
    result: dict[str, float] = {}
    for environment in range(4):
        selected = mask & (environments == environment)
        if not np.any(selected):
            raise TailRiskError(f"源验证环境 {environment} 没有有效风险样本")
        result[str(environment)] = float(losses[selected].mean())
    return {
        "per_environment": result,
        "mean": float(np.mean(list(result.values()))),
        "maximum": float(np.max(list(result.values()))),
    }


def evaluate(
    cache_root: Path,
    representation_root: Path,
    environment_root: Path,
    run_root: Path,
    output_dir: Path,
    config_path: Path,
) -> dict[str, Any]:
    """先验证全部原始概率和风险封存，再连接目标开发标签。"""
    if output_dir.exists():
        raise TailRiskError("评价输出目录已存在，拒绝覆盖")
    config = _load_config(config_path)
    _, roles = load_cache(cache_root)
    environments = _environment_bundle(
        cache_root, representation_root, environment_root, roles
    )
    target_role = roles["target-development"]
    raw_probabilities: dict[str, np.ndarray] = {}
    risk_scores: dict[str, dict[str, np.ndarray]] = {}
    seals: dict[str, Any] = {}
    training_contracts: dict[str, Any] = {}
    for variant in VARIANTS:
        slug = variant.lower()
        variant_dir = run_root / "variants" / slug
        status = _read_json(variant_dir / "status.json")
        training_receipt = _read_json(variant_dir / "training-receipt.json")
        if (
            status.get("state") != "probabilities_sealed_evaluation_pending"
            or status.get("target_development_labels_used") is not False
            or status.get("final_accessed") is not False
        ):
            raise TailRiskError(f"{variant} 原始概率尚未封存")
        raw_probability, raw_receipt = _load_sealed_probability(
            variant_dir, target_role
        )
        scores, risk_receipt = _load_risk_scores(
            run_root / "risks" / slug, target_role
        )
        if not np.array_equal(
            np.asarray(scores["raw_probability"], dtype=np.float64), raw_probability
        ):
            raise TailRiskError(f"{variant} 风险制品中的原始概率与封存概率不一致")
        raw_probabilities[variant] = raw_probability
        risk_scores[variant] = scores
        training_contracts[variant] = {
            "model_class": training_receipt.get("model_class"),
            "trainable_parameter_count": training_receipt.get(
                "trainable_parameter_count"
            ),
            "planned_steps": training_receipt.get("planned_steps"),
            "actual_steps": training_receipt.get("actual_steps"),
            "training_order_sha256": training_receipt.get("binding", {}).get(
                "training_order_sha256"
            ),
        }
        seals[variant] = {
            "raw_probability_sha256": raw_receipt["sha256"],
            "risk_score_sha256": risk_receipt["risk_score_sha256"],
        }
    shared_contract_values = list(training_contracts.values())
    if (
        len({item["model_class"] for item in shared_contract_values}) != 1
        or len({item["trainable_parameter_count"] for item in shared_contract_values}) != 1
        or len({item["training_order_sha256"] for item in shared_contract_values}) != 1
        or any(
            item["planned_steps"] != 732 or item["actual_steps"] != 732
            for item in shared_contract_values
        )
    ):
        raise TailRiskError("五变体模型、参数量、训练顺序或 732 步预算不完全一致")
    target_label_path = target_role.root / "labels.npy"
    if not target_label_path.is_file():
        raise TailRiskError("全部分数封存后无法连接目标开发标签")
    target_labels = np.load(target_label_path, mmap_mode="r")
    if target_labels.shape != (target_role.row_count,) or not np.isin(
        target_labels, (0, 1)
    ).all():
        raise TailRiskError("目标开发标签数组不合法")
    labels = np.asarray(target_labels, dtype=np.uint8)
    budgets = [int(value) for value in config["evaluation"]["alert_budgets_per_million"]]
    recalls = [float(value) for value in config["evaluation"]["fixed_recall_grid"]]
    results: dict[str, Any] = {}
    sentinel_assertions: dict[str, Any] = {}
    for variant in VARIANTS:
        raw = raw_probabilities[variant]
        empirical = np.asarray(risk_scores[variant]["empirical_risk"], dtype=np.float64)
        gpd = np.asarray(risk_scores[variant]["gpd_risk"], dtype=np.float64)
        raw_metrics = _score_metrics(labels, raw, raw, recalls, budgets)
        np_metrics = _score_metrics(labels, raw, raw, recalls, budgets)
        empirical_probability = 1.0 - np.exp(-empirical)
        gpd_probability = 1.0 - np.exp(-gpd)
        empirical_metrics = _score_metrics(
            labels, empirical, empirical_probability, recalls, budgets
        )
        gpd_metrics = _score_metrics(labels, gpd, gpd_probability, recalls, budgets)
        if (
            raw_metrics["average_precision"] != np_metrics["average_precision"]
            or raw_metrics["strict_global_top_k_recall"]
            != np_metrics["strict_global_top_k_recall"]
        ):
            raise TailRiskError(f"{variant} NP 纯阈值哨兵改变了排序指标")
        np_receipt = _read_json(
            run_root / "risks" / variant.lower() / "risk-model-receipt.json"
        )["np_source_anchor"]
        threshold = float(np_receipt["tie_safe_threshold"])
        predictions = raw >= threshold
        results[variant] = {
            "display_name": DISPLAY_NAMES[variant],
            "raw": raw_metrics,
            "np_operating_point": {
                "ranking_metrics": np_metrics,
                "threshold": threshold,
                "true_positives": int(np.sum(predictions & (labels == 1))),
                "false_positives": int(np.sum(predictions & (labels == 0))),
                "malicious_recall": float(
                    np.sum(predictions & (labels == 1)) / max(np.sum(labels == 1), 1)
                ),
            },
            "empirical_context_tail_risk": empirical_metrics,
            "gpd_context_tail_risk": gpd_metrics,
            "risk_calibration_probability_transform": "1-exp(-risk_score)",
        }
        sentinel_assertions[variant] = {
            "raw_and_np_average_precision_identical": True,
            "raw_and_np_strict_global_top_k_recall_identical": True,
            "np_only_changes_operating_point": True,
        }
    source_role = roles["source-validation"]
    if source_role.labels is None:
        raise TailRiskError("源验证标签缺失")
    row_partition = _row_environment(source_role, environments.validation_partition)
    row_environment = _row_environment(source_role, environments.validation_environment)
    validation_mask = row_partition == 0
    source_risks: dict[str, Any] = {}
    environment_probes: dict[str, Any] = {}
    train_row_environment = _row_environment(
        roles["source-train"], environments.train_environment
    )
    for variant in VARIANTS:
        variant_dir = run_root / "variants" / variant.lower()
        source_probability, _ = _load_sealed_probability(variant_dir, source_role)
        source_risks[variant] = _source_environment_risks(
            np.asarray(source_role.labels),
            source_probability,
            row_environment,
            validation_mask,
        )
        state_manifest = _read_json(variant_dir / "states" / "manifest.json")
        records = state_manifest.get("records")
        if not isinstance(records, Mapping):
            raise TailRiskError(f"{variant} 状态表示清单不合法")
        train_path = Path(str(records["source-train"]["path"])).resolve()
        validation_path = Path(str(records["source-validation"]["path"])).resolve()
        if (
            records["source-train"].get("sha256") != _sha256(train_path)
            or records["source-validation"].get("sha256") != _sha256(validation_path)
        ):
            raise TailRiskError(f"{variant} 状态表示哈希不一致")
        environment_probes[variant] = _probe_environment_auc(
            np.load(train_path, mmap_mode="r"),
            train_row_environment,
            np.load(validation_path, mmap_mode="r")[validation_mask],
            row_environment[validation_mask],
            int(config["seed"]),
            int(config["evaluation"]["environment_probe_max_rows"]),
        )
    non_erm = [variant for variant in VARIANTS if variant != "ERM"]
    best_m1 = max(
        non_erm,
        key=lambda variant: results[variant]["raw"]["average_precision"],
    )
    baseline_threshold = float(config["comparison_baselines"]["promotion_ap_threshold"])
    m1_pass = (
        results[best_m1]["raw"]["average_precision"] > baseline_threshold
        and results[best_m1]["raw"]["average_precision"]
        > results["ERM"]["raw"]["average_precision"]
        and source_risks[best_m1]["maximum"] <= source_risks["ERM"]["maximum"]
        and environment_probes[best_m1]["macro_ovr_auc"]
        < environment_probes["ERM"]["macro_ovr_auc"]
    )
    primary_budget = str(config["evaluation"]["primary_alert_budget_per_million"])

    def budget_vector(metrics: Mapping[str, Any]) -> np.ndarray:
        return np.asarray(
            [
                metrics["strict_global_top_k_recall"][str(budget)]["recall"]
                for budget in budgets
            ],
            dtype=np.float64,
        )

    erm_raw_vector = budget_vector(results["ERM"]["raw"])
    erm_m2_options = {
        "EMPIRICAL": results["ERM"]["empirical_context_tail_risk"],
        "GPD": results["ERM"]["gpd_context_tail_risk"],
    }
    best_erm_m2 = max(
        erm_m2_options,
        key=lambda key: erm_m2_options[key]["strict_global_top_k_recall"][primary_budget][
            "recall"
        ],
    )
    erm_m2_vector = budget_vector(erm_m2_options[best_erm_m2])
    m2_gains = erm_m2_vector - erm_raw_vector
    m2_pass = bool(np.any(m2_gains > 0.0) and np.sum(m2_gains) >= 0.0)
    full_options = {
        "EMPIRICAL": results[best_m1]["empirical_context_tail_risk"],
        "GPD": results[best_m1]["gpd_context_tail_risk"],
    }
    best_full = max(
        full_options,
        key=lambda key: full_options[key]["strict_global_top_k_recall"][primary_budget][
            "recall"
        ],
    )
    full_primary = full_options[best_full]["strict_global_top_k_recall"][primary_budget][
        "recall"
    ]
    best_single_primary = max(
        results[best_m1]["raw"]["strict_global_top_k_recall"][primary_budget][
            "recall"
        ],
        erm_m2_options[best_erm_m2]["strict_global_top_k_recall"][primary_budget][
            "recall"
        ],
    )
    combination_pass = full_primary > best_single_primary
    promoted = bool(m1_pass and m2_pass and combination_pass)
    comparison = {
        "strongest_shared_q0_baseline": {
            "name": "共享表格基线 XGBoost",
            "average_precision": baseline_threshold,
            "promotion_threshold": True,
        },
        "shared_hgb": config["comparison_baselines"]["shared_hgb"],
        "shared_random_forest": config["comparison_baselines"]["shared_random_forest"],
        "published_protocol_reference": config["comparison_baselines"][
            "dijk_2026_xgboost"
        ],
        "other_legal_q0_references": config["comparison_baselines"][
            "other_legal_q0_references"
        ],
        "excluded": config["comparison_baselines"]["excluded"],
    }
    decision = {
        "best_m1_variant": best_m1,
        "m1_passed": m1_pass,
        "m1_average_precision": results[best_m1]["raw"]["average_precision"],
        "erm_average_precision": results["ERM"]["raw"]["average_precision"],
        "promotion_average_precision_threshold": baseline_threshold,
        "m1_worst_source_environment_risk_not_worse": source_risks[best_m1][
            "maximum"
        ]
        <= source_risks["ERM"]["maximum"],
        "m1_environment_probe_auc_declined": environment_probes[best_m1][
            "macro_ovr_auc"
        ]
        < environment_probes["ERM"]["macro_ovr_auc"],
        "best_erm_m2": best_erm_m2,
        "m2_budget_recall_gains": {
            str(budget): float(gain)
            for budget, gain in zip(budgets, m2_gains, strict=True)
        },
        "m2_passed": m2_pass,
        "best_full_combination": f"{best_m1}+{best_full}",
        "full_primary_budget_recall": full_primary,
        "best_single_primary_budget_recall": best_single_primary,
        "full_combination_exceeds_best_single": combination_pass,
        "promoted": promoted,
        "verdict": "R1 Q0晋级" if promoted else "R1 Q0不晋级并转向候选B",
        "evidence_level": "Q0单种子快速筛选",
        "formal_paper_evidence": False,
        "not_formal_disproof": True,
    }
    output_dir.mkdir(parents=True)
    result = {
        "schema_version": EVALUATION_SCHEMA,
        "evaluation_order": "五组原始概率与十五组 NP/经验/GPD 风险制品先封存，后连接目标开发标签",
        "seals": seals,
        "shared_training_contracts": training_contracts,
        "identity_keys_checked_item_by_item": [
            "sample_id",
            "sequence_id",
            "position",
            "valid_length",
        ],
        "np_sentinel_assertions": sentinel_assertions,
        "variant_results": results,
        "source_validation_environment_risks": source_risks,
        "environment_probes": environment_probes,
        "comparison": comparison,
        "decision": decision,
        "target_label_sha256": _sha256(target_label_path),
        "target_label_connected_after_all_probability_and_risk_seals": True,
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
            "verdict": decision["verdict"],
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        },
    )
    for variant in VARIANTS:
        path = run_root / "variants" / variant.lower() / "status.json"
        status = _read_json(path)
        status.update(
            {
                "state": "finished",
                "evaluation_result": str((output_dir / "results.json").resolve()),
                "target_development_labels_used_during_training": False,
                "target_development_labels_used_during_independent_evaluation": True,
            }
        )
        _write_json(path, status)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser(
        "prepare-environments", help="生成标签盲环境与五变体共享训练顺序"
    )
    prepare.add_argument("--cache-root", type=Path, required=True)
    prepare.add_argument("--representation-root", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path, required=True)
    prepare.add_argument("--config", type=Path, required=True)
    train = subparsers.add_parser("train", help="训练一个共同架构风险目标并封存概率")
    train.add_argument("--cache-root", type=Path, required=True)
    train.add_argument("--representation-root", type=Path, required=True)
    train.add_argument(
        "--target-prefix-representation-root", type=Path, required=True
    )
    train.add_argument("--environment-root", type=Path, required=True)
    train.add_argument("--output-dir", type=Path, required=True)
    train.add_argument("--config", type=Path, required=True)
    train.add_argument("--variant", choices=VARIANTS, required=True)
    train.add_argument("--run-name", required=True)
    fit = subparsers.add_parser(
        "fit-risk", help="拟合源锚 NP 与无标签上下文经验/GPD 风险"
    )
    fit.add_argument("--cache-root", type=Path, required=True)
    fit.add_argument("--representation-root", type=Path, required=True)
    fit.add_argument("--environment-root", type=Path, required=True)
    fit.add_argument("--run-dir", type=Path, required=True)
    fit.add_argument("--output-dir", type=Path, required=True)
    fit.add_argument("--config", type=Path, required=True)
    evaluate_parser = subparsers.add_parser(
        "evaluate", help="全部分数封存后独立连接目标开发标签"
    )
    evaluate_parser.add_argument("--cache-root", type=Path, required=True)
    evaluate_parser.add_argument("--representation-root", type=Path, required=True)
    evaluate_parser.add_argument("--environment-root", type=Path, required=True)
    evaluate_parser.add_argument("--run-root", type=Path, required=True)
    evaluate_parser.add_argument("--output-dir", type=Path, required=True)
    evaluate_parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "prepare-environments":
        result = prepare_environments(
            args.cache_root,
            args.representation_root,
            args.output_dir,
            args.config,
        )
    elif args.command == "train":
        result = train_variant(
            args.cache_root,
            args.representation_root,
            args.target_prefix_representation_root,
            args.environment_root,
            args.output_dir,
            args.config,
            args.variant,
            args.run_name,
        )
    elif args.command == "fit-risk":
        result = fit_risk(
            args.cache_root,
            args.representation_root,
            args.environment_root,
            args.run_dir,
            args.output_dir,
            args.config,
        )
    elif args.command == "evaluate":
        result = evaluate(
            args.cache_root,
            args.representation_root,
            args.environment_root,
            args.run_root,
            args.output_dir,
            args.config,
        )
    else:
        raise TailRiskError(f"未处理命令：{args.command}")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
