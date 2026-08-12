"""复用历史 C12-DREF 权重的非破坏性状态控制回放。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from flow_probe.c12_crossyear_models import (
    C12ModelConfig,
    ReceiverSourceScorer,
    build_phase_b_parameter_matched_models,
)
from flow_probe.c12_crossyear_train import (
    C12TrainError,
    ControlContract,
    SequenceRole,
    SwanTracker,
    _binary_metrics,
    _flush_reference_block,
    _iter_representation_batches,
    _load_representations,
    _load_target_prefix_representation,
    _new_reference_state,
    _sha256,
    _trusted_quality,
    _write_artifact_manifest,
    _write_json,
    load_cache,
)

SCHEMA = "c12-r-reference-replay-q0-v1"
VARIANTS = (
    "DREF",
    "DREF_QUALIFIED_GATE",
    "DREF_QUALIFIED_GATE_CLIP",
    "DREF_QUALIFIED_GATE_CLIP_BUDGET",
    "DREF_QUALIFIED_GATE_CLIP_BUDGET_ROLLBACK",
    "DREF_RANDOM_GATE_MATCHED_CLIP",
)
DISPLAY_NAMES = {
    "DREF": "原始双参照回放",
    "DREF_QUALIFIED_GATE": "双参照加源冻结资格门",
    "DREF_QUALIFIED_GATE_CLIP": "双参照资格门加单步裁剪",
    "DREF_QUALIFIED_GATE_CLIP_BUDGET": "双参照资格门加单步裁剪与累计预算",
    "DREF_QUALIFIED_GATE_CLIP_BUDGET_ROLLBACK": "双参照资格门加裁剪、累计预算与回退",
    "DREF_RANDOM_GATE_MATCHED_CLIP": "双参照逐序列更新数匹配随机门加单步裁剪",
}


class ReplayError(C12TrainError):
    """回放输入或动作违反冻结合同。"""


@dataclass(frozen=True)
class Inputs:
    cache_root: Path
    representation_root: Path
    target_prefix_representation_root: Path
    receiver_checkpoint: Path
    dref_run: Path


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ReplayError(f"JSON 顶层必须为对象：{path}")
    return value


def _contract_from_receipt(receipt: Mapping[str, Any]) -> ControlContract:
    if (
        receipt.get("schema_version") != "c12-phase-b-source-frozen-control-contract-v1"
        or receipt.get("selection_roles") != ["source-train", "source-validation"]
        or receipt.get("target_prefix_used_for_thresholds") is not False
        or receipt.get("target_development_label_used") is not False
        or receipt.get("final_accessed") is not False
    ):
        raise ReplayError("历史 DREF 源冻结控制合同不合法")
    raw = receipt.get("contract")
    if not isinstance(raw, dict):
        raise ReplayError("历史 DREF 控制合同缺少 contract")
    values = dict(raw)
    values["source_anchor"] = np.asarray(values["source_anchor"], dtype=np.float32)
    values["source_variance"] = np.asarray(values["source_variance"], dtype=np.float32)
    contract = ControlContract(**values)
    if contract.source_anchor.shape != (192,) or contract.source_variance.shape != (192,):
        raise ReplayError("历史 DREF 源锚或方差维度不合法")
    return contract


def _validate_inputs(inputs: Inputs) -> tuple[dict[str, Any], dict[str, Any], ControlContract]:
    checkpoint_path = inputs.dref_run / "checkpoints/best.pt"
    contract_path = inputs.dref_run / "source-frozen-control-contract.json"
    status = _load_json(inputs.dref_run / "status.json")
    config = _load_json(inputs.dref_run / "config.json")
    threshold = _load_json(inputs.dref_run / "threshold-receipt.json")
    if (
        status.get("variant") != "C12-DREF"
        or status.get("state") != "finished"
        or status.get("final_accessed") is not False
        or config.get("variant") != "C12-DREF"
        or config.get("target_prefix_labels_available") is not False
        or config.get("target_development_label_read_during_training") is not False
        or config.get("final_accessed") is not False
    ):
        raise ReplayError("历史运行不是完成且隔离有效的 C12-DREF")
    manifest, _ = load_cache(inputs.cache_root)
    representations, representation_receipt = _load_representations(
        inputs.cache_root, inputs.representation_root
    )
    del representations
    _, prefix_receipt = _load_target_prefix_representation(
        inputs.cache_root, inputs.target_prefix_representation_root
    )
    receiver_hash = _sha256(inputs.receiver_checkpoint)
    if (
        representation_receipt.get("receiver_checkpoint_sha256") != receiver_hash
        or prefix_receipt.get("receiver_checkpoint_sha256") != receiver_hash
        or config.get("representation_manifest_sha256")
        != _sha256(inputs.representation_root / "representation-manifest.json")
        or config.get("target_prefix_representation_manifest_sha256")
        != _sha256(
            inputs.target_prefix_representation_root / "target-prefix-representation-manifest.json"
        )
        or config.get("cache_manifest_sha256") != _sha256(inputs.cache_root / "cache-manifest.json")
        or manifest.get("final_accessed") is not False
    ):
        raise ReplayError("DREF 权重、冻结表示、接收器或缓存哈希链不一致")
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if payload.get("variant") != "C12-DREF":
        raise ReplayError("检查点 variant 不是 C12-DREF")
    contract = _contract_from_receipt(_load_json(contract_path))
    return payload, threshold, contract


def _random_mask(
    length: int,
    accepted: int,
    source_contract_sha256: str,
    checkpoint_sha256: str,
    seed: int,
    sequence_id: object,
) -> np.ndarray:
    if not 0 <= accepted <= length:
        raise ReplayError("随机匹配更新数超出序列长度")
    material = "\x1f".join(
        (source_contract_sha256, checkpoint_sha256, str(seed), str(sequence_id))
    ).encode("utf-8")
    digest = hashlib.sha256(material).digest()
    random_generator = np.random.default_rng(np.frombuffer(digest, dtype=np.uint64).tolist())
    mask = np.zeros(length, dtype=bool)
    if accepted:
        mask[random_generator.permutation(length)[:accepted]] = True
    return mask


def _qualification_masks(
    scorer: torch.nn.Module,
    role: SequenceRole,
    representation: np.ndarray,
    contract: ControlContract,
    batch_size: int,
    device: torch.device,
    initial_quality: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    qualified = np.zeros(role.row_count, dtype=bool)
    quality_values = np.empty(role.row_count, dtype=np.float32)
    drift_values = np.empty(role.row_count, dtype=np.float32)
    anchor = torch.from_numpy(contract.source_anchor).to(device)
    variance = torch.from_numpy(contract.source_variance).to(device)
    scorer.eval()
    with torch.no_grad():
        for _, indices, values, valid, _ in _iter_representation_batches(
            role, representation, np.arange(role.sequence_count), batch_size
        ):
            values = values.to(device)
            valid_device = valid.to(device)
            quality_sum = torch.full(
                (values.shape[0],), initial_quality * contract.quality_window, device=device
            )
            quality_count = torch.full(
                (values.shape[0],), float(contract.quality_window), device=device
            )
            for position in range(values.shape[1]):
                current = values[:, position]
                active = valid_device[:, position]
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    source_logits = scorer(current).squeeze(-1)
                probability = torch.sigmoid(source_logits.float()).clamp(1e-7, 1.0 - 1e-7)
                entropy = -(
                    probability * torch.log(probability)
                    + (1.0 - probability) * torch.log(1.0 - probability)
                )
                quality = (1.0 - probability) * torch.exp(-entropy)
                quality_sum += torch.where(active, quality, torch.zeros_like(quality))
                quality_count += active.float()
                rolling_quality = quality_sum / quality_count.clamp_min(1.0)
                raw_drift = torch.log1p(((current.float() - anchor) ** 2 / variance).sum(dim=1))
                drift = torch.clamp(
                    (raw_drift - contract.drift_median) / max(contract.drift_scale, 1e-6),
                    0.0,
                    contract.drift_maximum,
                )
                gate = (
                    active
                    & (drift >= contract.enter_threshold)
                    & (drift < contract.rollback_threshold)
                    & (rolling_quality >= contract.quality_threshold)
                )
                active_np = active.cpu().numpy()
                for batch_index in np.flatnonzero(active_np):
                    row = int(role.starts[indices[batch_index]]) + position
                    qualified[row] = bool(gate[batch_index].item())
                    quality_values[row] = float(rolling_quality[batch_index].item())
                    drift_values[row] = float(drift[batch_index].item())
    return qualified, quality_values, drift_values


def _variant_features(variant: str) -> tuple[bool, bool, bool, bool]:
    return (
        variant != "DREF",
        variant
        in (
            "DREF_QUALIFIED_GATE_CLIP",
            "DREF_QUALIFIED_GATE_CLIP_BUDGET",
            "DREF_QUALIFIED_GATE_CLIP_BUDGET_ROLLBACK",
            "DREF_RANDOM_GATE_MATCHED_CLIP",
        ),
        variant
        in (
            "DREF_QUALIFIED_GATE_CLIP_BUDGET",
            "DREF_QUALIFIED_GATE_CLIP_BUDGET_ROLLBACK",
        ),
        variant == "DREF_QUALIFIED_GATE_CLIP_BUDGET_ROLLBACK",
    )


def _replay_role(
    model: torch.nn.Module,
    scorer: torch.nn.Module,
    role: SequenceRole,
    representation: np.ndarray,
    contract: ControlContract,
    variant: str,
    batch_size: int,
    device: torch.device,
    initial_quality: float,
    reference: dict[str, Any],
    update_reference: bool,
    seed: int,
    contract_sha256: str,
    checkpoint_sha256: str,
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, Any]]:
    use_gate, use_clip, use_budget, use_rollback = _variant_features(variant)
    qualified, quality_values, drift_values = _qualification_masks(
        scorer, role, representation, contract, batch_size, device, initial_quality
    )
    selected = qualified.copy()
    if variant == "DREF_RANDOM_GATE_MATCHED_CLIP":
        selected.fill(False)
        for start, length in zip(role.starts, role.lengths, strict=True):
            start_int, length_int = int(start), int(length)
            count = int(qualified[start_int : start_int + length_int].sum())
            selected[start_int : start_int + length_int] = _random_mask(
                length_int,
                count,
                contract_sha256,
                checkpoint_sha256,
                seed,
                role.sequence_id[start_int],
            )
    probabilities = np.empty(role.row_count, dtype=np.float32)
    filled = np.zeros(role.row_count, dtype=bool)
    diagnostics = {
        name: np.empty(role.row_count, dtype=dtype)
        for name, dtype in (
            ("drift", np.float32),
            ("quality", np.float32),
            ("qualified", np.uint8),
            ("selected", np.uint8),
            ("proposal_norm", np.float32),
            ("applied_norm", np.float32),
            ("cumulative_impact", np.float32),
            ("action", np.uint8),
            ("reference_distance", np.float32),
            ("promotion_coefficient", np.float32),
        )
    }
    action_counts = {"接受": 0, "冻结": 0, "回退": 0}
    started = time.perf_counter()
    model.eval()
    scorer.eval()
    with torch.no_grad():
        for _, indices, values, valid, _ in _iter_representation_batches(
            role, representation, np.arange(role.sequence_count), batch_size
        ):
            values = values.to(device)
            valid_device = valid.to(device)
            state = model.empty_state(values)
            checkpoint = state.clone()
            cumulative = torch.zeros(values.shape[0], device=device)
            safe_steps = torch.zeros(values.shape[0], device=device, dtype=torch.int64)
            active_reference_np = reference["active"]
            active_reference = torch.from_numpy(active_reference_np).to(device)
            for position in range(values.shape[1]):
                current = values[:, position]
                active = valid_device[:, position]
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits, _ = model.predict_step(current, state, active_reference)
                    proposal = model.propose_step(current, state)
                    source_logits = scorer(current).squeeze(-1)
                delta = proposal - state
                proposal_norm = torch.linalg.vector_norm(delta.flatten(1), dim=1)
                proposal_state_norm = torch.linalg.vector_norm(proposal.flatten(1), dim=1)
                active_np = active.cpu().numpy()
                active_batch_indices = np.flatnonzero(active_np)
                active_rows = np.asarray(
                    [
                        int(role.starts[indices[batch_index]]) + position
                        for batch_index in active_batch_indices
                    ],
                    dtype=np.int64,
                )
                selected_batch = np.zeros(len(indices), dtype=bool)
                selected_batch[active_batch_indices] = selected[active_rows]
                selected_tensor = torch.from_numpy(selected_batch).to(device) & active
                drift_batch = np.zeros(len(indices), dtype=np.float32)
                drift_batch[active_batch_indices] = drift_values[active_rows]
                if not use_gate:
                    selected_tensor = active
                if use_clip:
                    scale = torch.minimum(
                        torch.ones_like(proposal_norm),
                        torch.full_like(proposal_norm, contract.step_budget)
                        / proposal_norm.clamp_min(1e-9),
                    )
                    bounded_delta = delta * scale.view(-1, 1, 1, 1)
                else:
                    bounded_delta = delta
                applied_norm = torch.linalg.vector_norm(bounded_delta.flatten(1), dim=1)
                proposed_cumulative = contract.cumulative_decay * cumulative + applied_norm
                finite = torch.isfinite(proposal.flatten(1)).all(dim=1)
                rollback = (
                    active
                    & use_rollback
                    & (
                        (~finite)
                        | (proposal_state_norm > contract.state_norm_maximum)
                        | torch.from_numpy(drift_batch).to(device).ge(contract.rollback_threshold)
                    )
                )
                accept = selected_tensor & (~rollback)
                if use_budget:
                    accept &= proposed_cumulative <= contract.cumulative_budget
                accepted_state = state + bounded_delta
                state = torch.where(
                    rollback.view(-1, 1, 1, 1),
                    checkpoint,
                    torch.where(accept.view(-1, 1, 1, 1), accepted_state, state),
                )
                decayed_cumulative = contract.cumulative_decay * cumulative
                if use_rollback:
                    decayed_cumulative = torch.where(
                        rollback, torch.zeros_like(cumulative), decayed_cumulative
                    )
                cumulative = torch.where(accept, proposed_cumulative, decayed_cumulative)
                safe_steps = torch.where(
                    accept & finite, safe_steps + 1, torch.zeros_like(safe_steps)
                )
                checkpoint = torch.where(
                    (safe_steps >= contract.checkpoint_steps).view(-1, 1, 1, 1),
                    state,
                    checkpoint,
                )
                action = torch.where(
                    rollback,
                    torch.full_like(safe_steps, 2, dtype=torch.uint8),
                    torch.where(
                        accept,
                        torch.ones_like(safe_steps, dtype=torch.uint8),
                        torch.zeros_like(safe_steps, dtype=torch.uint8),
                    ),
                )
                probability = torch.sigmoid(logits).float().cpu().numpy()[active_np]
                proposal_np = proposal_norm.float().cpu().numpy()[active_np]
                applied_np = (
                    torch.where(accept, applied_norm, torch.zeros_like(applied_norm))
                    .float()
                    .cpu()
                    .numpy()[active_np]
                )
                cumulative_np = cumulative.float().cpu().numpy()[active_np]
                action_np = action.cpu().numpy()[active_np]
                current_np = current.float().cpu().numpy()[active_np]
                probabilities[active_rows] = probability
                diagnostics["drift"][active_rows] = drift_values[active_rows]
                diagnostics["quality"][active_rows] = quality_values[active_rows]
                diagnostics["qualified"][active_rows] = qualified[active_rows]
                diagnostics["selected"][active_rows] = selected[active_rows] if use_gate else 1
                diagnostics["proposal_norm"][active_rows] = proposal_np
                diagnostics["applied_norm"][active_rows] = applied_np
                diagnostics["cumulative_impact"][active_rows] = cumulative_np
                diagnostics["action"][active_rows] = action_np
                diagnostics["reference_distance"][active_rows] = np.linalg.norm(
                    current_np - active_reference_np, axis=1
                )
                diagnostics["promotion_coefficient"][active_rows] = float(reference["pi"])
                filled[active_rows] = True
                action_counts["接受"] += int(np.sum(action_np == 1))
                action_counts["冻结"] += int(np.sum(action_np == 0))
                action_counts["回退"] += int(np.sum(action_np == 2))
                if update_reference:
                    attack_np = torch.sigmoid(source_logits.float()).cpu().numpy()[active_np]
                    entropy_np = -(
                        attack_np * np.log(np.clip(attack_np, 1e-7, 1.0))
                        + (1.0 - attack_np) * np.log(np.clip(1.0 - attack_np, 1e-7, 1.0))
                    )
                    source_quality = _trusted_quality(attack_np)
                    rescue = (
                        attack_np
                        * np.exp(-entropy_np)
                        * (drift_values[active_rows] >= contract.new_normal_threshold)
                    )
                    raw_weight = np.minimum(
                        contract.sample_weight_maximum,
                        source_quality + contract.rescue_weight * rescue,
                    )
                    distance = np.linalg.norm(current_np - reference["candidate"], axis=1)
                    influence = np.minimum(
                        1.0, contract.reference_step_budget / np.maximum(distance, 1e-9)
                    )
                    weight = raw_weight * influence
                    reference["block_weighted_sum"] += (weight[:, None] * current_np).sum(axis=0)
                    reference["block_raw_mass"] += float(raw_weight.sum())
                    reference["block_effective_mass"] += float(weight.sum())
                    reference["block_rows"] += len(active_rows)
                    reference["block_rollbacks"] += int(rollback[active].sum().item())
                    if reference["block_rows"] >= contract.block_rows:
                        _flush_reference_block(reference, contract)
                        active_reference_np = reference["active"]
                        active_reference = torch.from_numpy(active_reference_np).to(device)
    if update_reference:
        _flush_reference_block(reference, contract)
    if not filled.all() or not np.isfinite(probabilities).all():
        raise ReplayError(f"{role.role} 回放概率未完整封存")
    if variant == "DREF_RANDOM_GATE_MATCHED_CLIP":
        for start, length in zip(role.starts, role.lengths, strict=True):
            part = slice(int(start), int(start + length))
            if int(selected[part].sum()) != int(qualified[part].sum()):
                raise ReplayError("随机门没有逐 2-IP 序列精确匹配资格门更新数")
    summary = {
        "role": role.role,
        "rows": role.row_count,
        "sequences": role.sequence_count,
        "action_counts": action_counts,
        "qualified_count": int(qualified.sum()),
        "selected_count": int((selected if use_gate else np.ones_like(selected)).sum()),
        "reference_promotions": int(reference["promotions"]),
        "reference_retentions": int(reference["retentions"]),
        "reference_rejections": int(reference["rejections"]),
        "final_promotion_coefficient": float(reference["pi"]),
        "seconds": time.perf_counter() - started,
        "labels_read": False,
        "prediction_update_order": "当前位置概率先封存，再执行状态与参照更新",
        "final_accessed": False,
    }
    return probabilities, diagnostics, summary


def _seal_role(
    output_dir: Path,
    role: SequenceRole,
    probabilities: np.ndarray,
    diagnostics: Mapping[str, np.ndarray],
    summary: Mapping[str, Any],
    variant: str,
) -> tuple[Path, Path]:
    predictions_dir = output_dir / "predictions"
    diagnostics_dir = output_dir / "diagnostics"
    predictions_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = predictions_dir / f"{role.role}.npz"
    partial = prediction_path.with_suffix(f".npz.partial.{os.getpid()}")
    with partial.open("wb") as handle:
        np.savez_compressed(
            handle,
            probability=probabilities,
            sample_id=np.asarray(role.sample_id),
            sequence_id=np.asarray(role.sequence_id),
            position=np.asarray(role.position),
            valid_length=np.asarray(role.valid_length),
        )
    os.replace(partial, prediction_path)
    diagnostic_path = diagnostics_dir / f"{role.role}-state-control.npz"
    diagnostic_partial = diagnostic_path.with_suffix(f".npz.partial.{os.getpid()}")
    with diagnostic_partial.open("wb") as handle:
        np.savez_compressed(
            handle,
            np.asarray(role.sample_id),
            np.asarray(role.sequence_id),
            np.asarray(role.position),
            *[np.asarray(diagnostics[name]) for name in diagnostics],
        )
    os.replace(diagnostic_partial, diagnostic_path)
    _write_json(
        diagnostics_dir / f"{role.role}-state-control-layout.json",
        {
            "schema_version": "c12-r-state-control-layout-v1",
            "arrays": ["sample_id", "sequence_id", "position", *diagnostics.keys()],
            "storage_keys": [f"arr_{index}" for index in range(3 + len(diagnostics))],
            "diagnostic_sha256": _sha256(diagnostic_path),
            "final_accessed": False,
        },
    )
    receipt_path = predictions_dir / f"{role.role}-receipt.json"
    _write_json(
        receipt_path,
        {
            "schema_version": "c12-r-sealed-role-v1",
            "variant": variant,
            "role": role.role,
            "row_count": role.row_count,
            "sequence_count": role.sequence_count,
            "prediction_sha256": _sha256(prediction_path),
            "diagnostic_sha256": _sha256(diagnostic_path),
            "summary": dict(summary),
            "labels_connected": False,
            "final_accessed": False,
        },
    )
    return prediction_path, receipt_path


def replay(
    config_path: Path,
    output_dir: Path,
    variant: str,
    resource_measurement_mode: str,
) -> dict[str, Any]:
    if variant not in VARIANTS:
        raise ReplayError(f"未知 C12-R 变体：{variant}")
    if resource_measurement_mode not in {"isolated", "concurrent"}:
        raise ReplayError(f"未知资源测量模式：{resource_measurement_mode}")
    if output_dir.exists():
        raise ReplayError("C12-R 输出目录已存在，拒绝覆盖")
    config = _load_json(config_path)
    if config.get("schema_version") != SCHEMA or config.get("final_accessed") is not False:
        raise ReplayError("C12-R 配置模式或最终区隔离标志不合法")
    configured_variants = config.get("variants")
    if (
        int(config.get("seed", -1)) != 42
        or int(config.get("batch_size_sequences", -1)) != 16
        or not isinstance(configured_variants, list)
        or tuple(item.get("key") for item in configured_variants) != VARIANTS
    ):
        raise ReplayError("C12-R 冻结种子、批量或六级变体清单不一致")
    paths = config["paths"]
    inputs = Inputs(
        cache_root=Path(paths["cache_root"]),
        representation_root=Path(paths["representation_root"]),
        target_prefix_representation_root=Path(paths["target_prefix_representation_root"]),
        receiver_checkpoint=Path(paths["receiver_checkpoint"]),
        dref_run=Path(paths["dref_run"]),
    )
    batch_size = int(config["batch_size_sequences"])
    seed = int(config["seed"])
    payload, threshold, contract = _validate_inputs(inputs)
    output_dir.mkdir(parents=True)
    _, roles = load_cache(inputs.cache_root)
    representations, _ = _load_representations(inputs.cache_root, inputs.representation_root)
    prefix_representation, _ = _load_target_prefix_representation(
        inputs.cache_root, inputs.target_prefix_representation_root
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise ReplayError("C12-R 真实回放要求 CUDA")
    models, _, _ = build_phase_b_parameter_matched_models(C12ModelConfig(), seed)
    model = models["C12-DREF"].to(device)
    model.load_state_dict(payload["model"])
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    receiver = ReceiverSourceScorer(C12ModelConfig()).to(device)
    receiver_payload = torch.load(
        inputs.receiver_checkpoint, map_location="cpu", weights_only=False
    )
    receiver.load_state_dict(receiver_payload["model"])
    receiver.eval()
    scorer = receiver.classifier
    for parameter in scorer.parameters():
        parameter.requires_grad_(False)
    checkpoint_path = inputs.dref_run / "checkpoints/best.pt"
    contract_path = inputs.dref_run / "source-frozen-control-contract.json"
    checkpoint_hash = _sha256(checkpoint_path)
    contract_hash = _sha256(contract_path)
    run_config = {
        "schema_version": SCHEMA,
        "variant": variant,
        "display_name": DISPLAY_NAMES[variant],
        "seed": seed,
        "batch_size_sequences": batch_size,
        "historical_variant": "C12-DREF",
        "training_performed": False,
        "optimizer_created": False,
        "new_trainable_parameters": 0,
        "resource_measurement_mode": resource_measurement_mode,
        "single_process_efficiency_metrics_valid": resource_measurement_mode == "isolated",
        "source_contract_sha256": contract_hash,
        "dref_checkpoint_sha256": checkpoint_hash,
        "config_sha256": _sha256(config_path),
        "target_prefix_labels_used": False,
        "target_development_labels_connected_after_seal": True,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    _write_json(output_dir / "config.json", run_config)
    _write_json(
        output_dir / "input-receipt.json",
        {
            **run_config,
            "cache_manifest_sha256": _sha256(inputs.cache_root / "cache-manifest.json"),
            "representation_manifest_sha256": _sha256(
                inputs.representation_root / "representation-manifest.json"
            ),
            "target_prefix_representation_manifest_sha256": _sha256(
                inputs.target_prefix_representation_root
                / "target-prefix-representation-manifest.json"
            ),
            "receiver_checkpoint_sha256": _sha256(inputs.receiver_checkpoint),
        },
    )
    _write_json(
        output_dir / "status.json",
        {"state": "running", "variant": variant, "final_accessed": False},
    )
    tracker = SwanTracker(
        output_dir,
        f"c12-r-reference-replay-q0-seed42-v1-{variant.lower().replace('_', '-')}",
        run_config,
        phase="c12-r-replay",
    )
    try:
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        reference = _new_reference_state(contract)
        prefix_probability, prefix_diagnostics, prefix_summary = _replay_role(
            model,
            scorer,
            roles["target-prefix"],
            prefix_representation,
            contract,
            variant,
            batch_size,
            device,
            contract.quality_threshold,
            reference,
            True,
            seed,
            contract_hash,
            checkpoint_hash,
        )
        _, prefix_receipt = _seal_role(
            output_dir,
            roles["target-prefix"],
            prefix_probability,
            prefix_diagnostics,
            prefix_summary,
            variant,
        )
        frozen_reference = reference["active"].copy()
        target_probability, target_diagnostics, target_summary = _replay_role(
            model,
            scorer,
            roles["target-development"],
            representations["target-development"],
            contract,
            variant,
            batch_size,
            device,
            float(prefix_diagnostics["quality"].mean()),
            reference,
            False,
            seed,
            contract_hash,
            checkpoint_hash,
        )
        if not np.array_equal(frozen_reference, reference["active"]):
            raise ReplayError("目标开发回放改写了全局双参照")
        prediction_path, target_receipt = _seal_role(
            output_dir,
            roles["target-development"],
            target_probability,
            target_diagnostics,
            target_summary,
            variant,
        )
        _write_json(
            output_dir / "threshold-receipt.json",
            {
                **threshold,
                "reused_without_refit": True,
                "source": str(inputs.dref_run / "threshold-receipt.json"),
                "source_sha256": _sha256(inputs.dref_run / "threshold-receipt.json"),
                "target_prefix_used": False,
                "target_development_used": False,
                "final_accessed": False,
            },
        )
        _write_json(
            output_dir / "diagnostics/dual-reference.json",
            {
                "schema_version": "c12-r-dual-reference-v1",
                "variant": variant,
                "events": reference["events"],
                "promotions": reference["promotions"],
                "retentions": reference["retentions"],
                "rejections": reference["rejections"],
                "final_promotion_coefficient": reference["pi"],
                "source_anchor_unchanged": True,
                "target_prefix_labels_used": False,
                "final_accessed": False,
            },
        )
        tracker.log(
            {
                "replay/prefix_updates": prefix_summary["action_counts"]["接受"],
                "replay/target_updates": target_summary["action_counts"]["接受"],
                "runtime/peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            },
            step=1,
        )
        tracker.finish()
        summary = {
            **run_config,
            "state": "predictions_sealed_evaluation_pending",
            "prefix_summary": prefix_summary,
            "target_summary": target_summary,
            "prediction_path": str(prediction_path),
            "prefix_receipt_sha256": _sha256(prefix_receipt),
            "target_receipt_sha256": _sha256(target_receipt),
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "swanlab": tracker.status,
        }
        _write_json(
            output_dir / "resource-usage.json",
            {
                "schema_version": "c12-r-resource-usage-v1",
                "variant": variant,
                "prefix_replay_seconds": prefix_summary["seconds"],
                "target_replay_seconds": target_summary["seconds"],
                "total_replay_seconds": prefix_summary["seconds"] + target_summary["seconds"],
                "target_rows_per_second": roles["target-development"].row_count
                / max(float(target_summary["seconds"]), 1e-9),
                "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
                "resource_measurement_mode": resource_measurement_mode,
                "single_process_efficiency_metrics_valid": resource_measurement_mode == "isolated",
                "training_performed": False,
                "final_accessed": False,
            },
        )
        _write_json(output_dir / "summary.json", summary)
        _write_json(
            output_dir / "status.json",
            {
                "state": "predictions_sealed_evaluation_pending",
                "variant": variant,
                "target_prefix_labels_used": False,
                "final_accessed": False,
            },
        )
        _write_artifact_manifest(output_dir)
        return summary
    except BaseException as error:
        tracker.fail(error)
        _write_json(output_dir / "swanlab-status.json", tracker.status)
        _write_json(
            output_dir / "status.json",
            {
                "state": "failed",
                "variant": variant,
                "error_type": type(error).__name__,
                "error": str(error),
                "final_accessed": False,
            },
        )
        raise


def _fixed_alert_budget_recall(
    labels: np.ndarray, probabilities: np.ndarray, budgets_per_million: list[int]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    positives = int(labels.sum())
    order = np.argsort(-probabilities, kind="stable")
    for budget in budgets_per_million:
        count = min(len(labels), int(np.floor(len(labels) * budget / 1_000_000)))
        true_positives = int(labels[order[:count]].sum())
        result[str(budget)] = {
            "alert_count": count,
            "true_positives": true_positives,
            "recall": true_positives / max(positives, 1),
        }
    return result


def evaluate(config_path: Path, run_dir: Path) -> dict[str, Any]:
    config = _load_json(config_path)
    inputs = Inputs(
        cache_root=Path(config["paths"]["cache_root"]),
        representation_root=Path(config["paths"]["representation_root"]),
        target_prefix_representation_root=Path(
            config["paths"]["target_prefix_representation_root"]
        ),
        receiver_checkpoint=Path(config["paths"]["receiver_checkpoint"]),
        dref_run=Path(config["paths"]["dref_run"]),
    )
    _, roles = load_cache(inputs.cache_root)
    status = _load_json(run_dir / "status.json")
    if status.get("state") != "predictions_sealed_evaluation_pending":
        raise ReplayError("评价只能连接已封存且待评价的概率")
    prediction_path = run_dir / "predictions/target-development.npz"
    receipt = _load_json(run_dir / "predictions/target-development-receipt.json")
    if receipt.get("prediction_sha256") != _sha256(prediction_path):
        raise ReplayError("目标开发概率哈希不匹配")
    role = roles["target-development"]
    label_path = role.root / "labels.npy"
    labels = np.asarray(np.load(label_path, mmap_mode="r"), dtype=np.uint8)
    with np.load(prediction_path, allow_pickle=False) as sealed:
        probabilities = np.asarray(sealed["probability"], dtype=np.float64)
        if not np.array_equal(sealed["sample_id"], role.sample_id):
            raise ReplayError("目标开发概率无法按 sample_id 逐行连接标签")
        if not np.array_equal(sealed["sequence_id"], role.sequence_id):
            raise ReplayError("目标开发概率序列顺序漂移")
    threshold = float(_load_json(run_dir / "threshold-receipt.json")["threshold"])
    metrics = _binary_metrics(labels, probabilities, threshold)
    metrics.update(
        {
            "schema_version": "c12-r-target-development-metrics-v1",
            "variant": status["variant"],
            "fixed_alert_budget_recall_per_million": _fixed_alert_budget_recall(
                labels,
                probabilities,
                [int(value) for value in config["evaluation"]["alert_budgets_per_million"]],
            ),
            "evaluation_order": "概率与状态先封存，后由本入口连接标签",
            "prediction_sha256": _sha256(prediction_path),
            "label_sha256": _sha256(label_path),
            "target_prefix_labels_used": False,
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        }
    )
    _write_json(run_dir / "metrics/target-development.json", metrics)
    _write_json(
        run_dir / "status.json",
        {
            "state": "finished",
            "variant": status["variant"],
            "target_development_evaluated": True,
            "target_prefix_labels_used": False,
            "final_accessed": False,
        },
    )
    _write_artifact_manifest(run_dir)
    return metrics


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 C12-R 免重训双参照状态控制回放")
    subparsers = parser.add_subparsers(dest="command", required=True)
    replay_parser = subparsers.add_parser("replay", help="复用历史 DREF 权重封存回放概率")
    replay_parser.add_argument("--config", type=Path, required=True)
    replay_parser.add_argument("--output-dir", type=Path, required=True)
    replay_parser.add_argument("--variant", choices=VARIANTS, required=True)
    replay_parser.add_argument(
        "--resource-measurement-mode",
        choices=("isolated", "concurrent"),
        required=True,
    )
    evaluate_parser = subparsers.add_parser("evaluate", help="概率封存后连接目标开发标签")
    evaluate_parser.add_argument("--config", type=Path, required=True)
    evaluate_parser.add_argument("--run-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "replay":
        result = replay(
            args.config,
            args.output_dir,
            args.variant,
            args.resource_measurement_mode,
        )
    elif args.command == "evaluate":
        result = evaluate(args.config, args.run_dir)
    else:
        raise AssertionError(f"未处理命令：{args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
