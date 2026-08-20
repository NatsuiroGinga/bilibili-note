# -*- coding: utf-8 -*-
"""第三章 TabM 式骨干源年实体三折折外资格门。"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score

import ch3_neural_backbone_source_oof_gate as base

torch = base.torch
nn = base.nn

SCHEMA_VERSION = "ch3-tabm-source-oof-gate-config-v1"
RUN_ID = "ch3-tabm4-cpa-elp-source-oof-gate-seed42-v1"
MODEL_KEY = "tabm4"
MEMBER_COUNT = 4
HIDDEN_SIZE = 186
PARAMETER_COUNT = 90_175


def tabm_parameter_count(feature_count: int, hidden_size: int, members: int) -> int:
    return (
        2 * hidden_size * hidden_size
        + feature_count * hidden_size
        + members * (feature_count + 1 + 7 * hidden_size)
        + 1
    )


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置模式版本不符")
    if config.get("run_id") != RUN_ID or config.get("model_key") != MODEL_KEY:
        raise ValueError("TabM 运行身份不符")
    input_contract = config["input_contract"]
    if tuple(input_contract["allowed_arrays"]) != base.ALLOWED_ARRAYS:
        raise ValueError("输入必须严格锁定为五个源年数组")
    if tuple(config.get("allowed_arrays", ())) != base.ALLOWED_ARRAYS:
        raise ValueError("顶层输入白名单与源年合同不符")
    expected_input = {
        "flow_count": 16_353_511,
        "sequence_count": 271_815,
        "entity_count": 150_680,
        "positive_entity_count": 239,
        "feature_count": 83,
        "sequence_length": 128,
        "entity_code_minimum": 0,
        "entity_code_maximum": 150_679,
    }
    if any(input_contract.get(key) != value for key, value in expected_input.items()):
        raise ValueError("源年输入规模合同不符")
    if config["fold_contract"] != {
        "count": 3,
        "assignment": "seeded-stratified-entity-round-robin",
        "map_to_sequences_via": "E23",
        "map_to_flows_via": ["I23", "M23"],
        "require_each_entity_once_oof": True,
        "require_train_holdout_entity_disjoint": True,
    }:
        raise ValueError("实体三折合同不符")
    if config["cells"] != {
        "C00": {"causal_prefix_aggregation": False, "learned_lp_pooling": False},
        "C11": {"causal_prefix_aggregation": True, "learned_lp_pooling": True},
    }:
        raise ValueError("仅允许 C00 与 C11 两格")
    candidate = config["candidate"]
    expected_candidate = {
        "ensemble_members": MEMBER_COUNT,
        "hidden_size": HIDDEN_SIZE,
        "share_training_batches": False,
        "member_batch_sequences": 16,
        "activation": "relu",
        "dropout": 0.1,
        "first_layer_r_initialization": "random_sign",
        "later_scaling_initialization": "ones",
        "member_bias_initialization": "shared_initial_value",
        "output_heads": "independent_linear",
        "inference_member_reduction": "mean_sigmoid_probability",
        "parameter_formula": "2d^2+83d+k(84+7d)+1",
        "parameter_count": PARAMETER_COUNT,
        "reference_parameter_count": 90_242,
        "parameter_tolerance_fraction": 0.01,
        "official_source_commit": "28e47ae301c92ec37787dde1ce923a0793f405b4",
        "residual_blocks": 0,
        "residual_affine_layers": 0,
    }
    if candidate != expected_candidate:
        raise ValueError("TabM4 结构或参数预算不是预注册值")
    actual = tabm_parameter_count(83, HIDDEN_SIZE, MEMBER_COUNT)
    if actual != PARAMETER_COUNT:
        raise ValueError("TabM4 参数公式计算值不符")
    training = config["training"]
    expected_training = {
        "seed": 42,
        "hidden_size": HIDDEN_SIZE,
        "dropout": 0.1,
        "parameter_count": PARAMETER_COUNT,
        "batch_size": 64,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "learning_rate": 0.002,
        "weight_decay": 0.01,
        "weight_decay_policy": "shared_and_output_weights_only",
        "gradient_clip_norm": 1.0,
        "auxiliary_loss_weight": 1.0,
        "positive_weight_scope": "train_rows_reachable_labels_only",
        "selection_metric": "holdout_flow_average_precision",
        "selection_rule": "single_epoch_argmax_earliest_tie",
        "selection_evidence_scope": "source_screening_not_independent_oof",
    }
    if training != expected_training:
        raise ValueError("训练预算或选择规则不是冻结值")
    mirrors = {
        "seed": 42,
        "fold_count": 3,
        "batch_size": 64,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "learning_rate": 0.002,
        "weight_decay": 0.01,
        "gradient_clip_norm": 1.0,
        "auxiliary_loss_weight": 1.0,
    }
    if any(config.get(key) != value for key, value in mirrors.items()):
        raise ValueError("顶层预注册训练镜像字段不符")
    evaluation = config["evaluation"]
    if evaluation != {
        "c00_entity_aggregation": "maximum_after_member_probability_mean",
        "c11_entity_aggregation": "fold_learned_p_after_member_probability_mean",
        "p_diagnostic_grid": [0.5, 1.0, 2.0, 4.0, 8.0],
        "mlp_reference_c00_pooled": 0.5109066464488172,
        "mlp_reference_c11_pooled": 0.5447784766847485,
        "qualification_rule": (
            "candidate_c11_gt_xgb_and_candidate_c11_gt_c00_and_"
            "all_fold_c11_gt_c00_and_at_least_two_fold_c11_gt_xgb"
        ),
    }:
        raise ValueError("TabM4 评价合同不符")
    if config["parent_contract"] != {
        "mlp_run_id": "ch4-e1-source-entity-oof-gate-seed42-v1",
        "xgb_run_id": "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1",
        "xgb_adapter": "semantic168",
        "xgb_p": 1.0,
        "xgb_recovery_proof_schema": "ch3-xgb-parent-recovery-proof-v1",
        "historical_xgb_per_array_hash_persisted": False,
    }:
        raise ValueError("父基线身份合同不符")
    artifacts = config["artifact_policy"]
    if any(
        artifacts[key]
        for key in (
            "persist_per_flow_scores",
            "persist_per_entity_scores",
            "persist_fold_membership",
        )
    ):
        raise ValueError("禁止持久化逐流、逐实体分数或折成员")
    resources = config["resource_contract"]
    if resources != {
        "serial_minimum_free_gpu_memory_gib": 12,
        "serial_minimum_cgroup_available_memory_gib": 40,
        "minimum_free_disk_gib": 10,
        "maximum_parallel_training_units": 1,
        "initial_run_parallelism": 1,
        "parallel_resume_requires_first_unit_resource_receipt": True,
    }:
        raise ValueError("TabM4 首次串行资源合同不符")
    if not config.get("screening_only") or config.get("formal_paper_evidence"):
        raise ValueError("证据等级必须是快速筛选且非正式论文证据")
    if config.get("independent_test") or config.get("target_year_arrays_read") != 0:
        raise ValueError("本门禁不得访问独立测试或目标年数组")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="第三章 TabM4 源年实体三折折外资格门")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument(
        "--phase",
        choices=("prepare", "train-unit", "aggregate", "publish-aggregate"),
        default="prepare",
    )
    parser.add_argument("--resume", action="store_true", help="显式恢复合法检查点")
    parser.add_argument("--validate-config", action="store_true", help="只解析并核验配置")
    parser.add_argument("--cell", choices=base.CELL_ORDER)
    parser.add_argument("--fold", type=int, choices=(0, 1, 2))
    parser.add_argument("--actual-parallelism", type=int, choices=(1,))
    parser.add_argument("--resource-receipt")
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    parser.add_argument("--tracking-attempt", type=int, choices=(1, 2), default=1)
    return parser.parse_args()


if nn is not None:
    class LinearBatchEnsemble(nn.Module):
        def __init__(
            self,
            input_size: int,
            output_size: int,
            members: int,
            random_sign_input_scaling: bool,
        ):
            super().__init__()
            self.weight = nn.Parameter(torch.empty(output_size, input_size))
            self.r = nn.Parameter(torch.empty(members, input_size))
            self.s = nn.Parameter(torch.ones(members, output_size))
            self.bias = nn.Parameter(torch.empty(members, output_size))
            nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
            if random_sign_input_scaling:
                signs = torch.randint(0, 2, self.r.shape, dtype=torch.int64)
                self.r.data.copy_(signs.to(self.r.dtype).mul_(2).sub_(1))
            else:
                nn.init.ones_(self.r)
            bound = 1 / math.sqrt(input_size)
            shared_bias = torch.empty(output_size).uniform_(-bound, bound)
            self.bias.data.copy_(shared_bias.unsqueeze(0).expand_as(self.bias))

        def forward(self, values: torch.Tensor) -> torch.Tensor:
            scaled = values * self.r.unsqueeze(0).unsqueeze(2)
            projected = torch.matmul(scaled, self.weight.t())
            return (
                projected * self.s.unsqueeze(0).unsqueeze(2)
                + self.bias.unsqueeze(0).unsqueeze(2)
            )


    class TabM4Backbone(nn.Module):
        def __init__(
            self,
            feature_count: int,
            hidden_size: int,
            members: int,
            dropout: float,
            aggregate: bool,
        ):
            super().__init__()
            self.members = members
            self.aggregate = aggregate
            self.input_layer = LinearBatchEnsemble(
                feature_count, hidden_size, members, random_sign_input_scaling=True
            )
            self.fusion_layer = LinearBatchEnsemble(
                hidden_size * 2,
                hidden_size,
                members,
                random_sign_input_scaling=False,
            )
            self.activation = nn.ReLU()
            self.dropout = nn.Dropout(dropout)
            self.output_weight = nn.Parameter(torch.empty(members, hidden_size))
            self.output_bias = nn.Parameter(torch.empty(members))
            nn.init.kaiming_uniform_(self.output_weight, a=math.sqrt(5))
            bound = 1 / math.sqrt(hidden_size)
            nn.init.uniform_(self.output_bias, -bound, bound)
            self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

        @property
        def p(self) -> torch.Tensor:
            return torch.exp(self.p_log).clamp(1e-3, 1e3)

        def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
            if values.ndim != 4 or values.shape[1] != self.members:
                raise RuntimeError("TabM 训练输入必须是 N×4×T×F")
            mask = valid.to(values.dtype)
            hidden = self.dropout(self.activation(self.input_layer(values)))
            hidden = hidden * mask.unsqueeze(-1)
            if self.aggregate:
                context = torch.cumsum(hidden, dim=2) / torch.cumsum(
                    mask, dim=2
                ).clamp(min=1.0).unsqueeze(-1)
                context = context * mask.unsqueeze(-1)
            else:
                context = torch.zeros_like(hidden)
            fused = self.dropout(
                self.activation(self.fusion_layer(torch.cat((hidden, context), dim=-1)))
            )
            fused = fused * mask.unsqueeze(-1)
            return (
                (fused * self.output_weight.unsqueeze(0).unsqueeze(2)).sum(dim=-1)
                + self.output_bias.unsqueeze(0).unsqueeze(2)
            )

        def mean_member_probability(
            self, values: torch.Tensor, valid: torch.Tensor
        ) -> torch.Tensor:
            expanded_values = values.unsqueeze(1).expand(-1, self.members, -1, -1)
            expanded_valid = valid.unsqueeze(1).expand(-1, self.members, -1)
            return torch.sigmoid(self.forward(expanded_values, expanded_valid)).mean(dim=1)
else:
    class LinearBatchEnsemble:
        pass


    class TabM4Backbone:
        pass


def build_model(config: dict[str, Any], cell: str) -> TabM4Backbone:
    if torch is None or nn is None:
        raise RuntimeError("正式计算缺少 torch；请加载项目 GPU 可选依赖")
    model = TabM4Backbone(
        config["input_contract"]["feature_count"],
        config["candidate"]["hidden_size"],
        config["candidate"]["ensemble_members"],
        config["training"]["dropout"],
        config["cells"][cell]["causal_prefix_aggregation"],
    )
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != config["candidate"]["parameter_count"]:
        raise RuntimeError(f"TabM4 模型参数量不符：{actual}")
    reference = config["candidate"]["reference_parameter_count"]
    tolerance = config["candidate"]["parameter_tolerance_fraction"]
    if abs(actual - reference) / reference > tolerance:
        raise RuntimeError("TabM4 参数量超出百分之一预算")
    return model


def sample_distinct_train_rows(
    train_rows: np.ndarray, batch_size: int, generator: torch.Generator
) -> torch.Tensor:
    positions: list[int] = []
    seen: set[int] = set()
    while len(positions) < batch_size:
        needed = batch_size - len(positions)
        candidates = torch.randint(
            0, len(train_rows), (needed * 2,), generator=generator
        ).tolist()
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                positions.append(candidate)
                if len(positions) == batch_size:
                    break
    return torch.from_numpy(train_rows[np.asarray(positions, dtype=np.int64)])


@base.no_grad_if_available
def holdout_predictions(
    model: TabM4Backbone,
    rows: np.ndarray,
    gX: torch.Tensor,
    gy: torch.Tensor,
    gI: torch.Tensor,
    gM: torch.Tensor,
    inference_batch_size: int = 512,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    model.eval()
    predictions: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    flow_ids: list[np.ndarray] = []
    device = gX.device
    for start in range(0, len(rows), inference_batch_size):
        selected = torch.from_numpy(rows[start : start + inference_batch_size]).to(device)
        indices = gI[selected]
        valid = gM[selected] > 0.5
        batch = indices.shape[0]
        values = gX[indices.reshape(-1)].reshape(
            batch, indices.shape[1], gX.shape[1]
        )
        probabilities = model.mean_member_probability(values, valid)
        mask = valid.reshape(-1)
        predictions.append(probabilities.reshape(-1)[mask].float().cpu().numpy())
        labels.append(gy[indices.reshape(-1)].reshape(-1)[mask].float().cpu().numpy())
        flow_ids.append(indices.reshape(-1)[mask].cpu().numpy())
    model.train()
    return np.concatenate(predictions), np.concatenate(labels), np.concatenate(flow_ids)


def train_or_resume_unit(
    config: dict[str, Any],
    output_root: Path,
    identity: dict[str, Any],
    cell: str,
    fold: int,
    train_rows: np.ndarray,
    holdout_rows: np.ndarray,
    gX: torch.Tensor,
    gy: torch.Tensor,
    gI: torch.Tensor,
    gM: torch.Tensor,
    positive_weight: torch.Tensor,
    sequence_positive_weight: float,
    label_balance: dict[str, Any],
    resume: bool,
) -> tuple[TabM4Backbone, dict[str, Any], str]:
    checkpoint_path, inflight_path, receipt_path = base.unit_paths(output_root, cell, fold)
    identity = {
        **identity,
        "schema_version": "ch3-neural-backbone-source-unit-identity-v1",
    }
    selected = base.validate_selected_checkpoint(checkpoint_path, receipt_path, identity)
    if selected is not None:
        if not resume:
            raise RuntimeError(f"全新运行已有完成单元：{cell}/fold{fold}")
        model = build_model(config, cell).to(gX.device)
        model.load_state_dict(selected["model"])
        base.log(f"{cell}/fold{fold} 合法检查点复用")
        return model, selected["selection"], "reused"
    if (inflight_path.exists() or receipt_path.exists()) and not resume:
        raise RuntimeError(f"全新运行已有单元制品：{cell}/fold{fold}")

    training = config["training"]
    seed = training["seed"]
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    model = build_model(config, cell).to(gX.device)
    decay_names = {"input_layer.weight", "fusion_layer.weight", "output_weight"}
    decay = [parameter for name, parameter in model.named_parameters() if name in decay_names]
    no_decay = [
        parameter for name, parameter in model.named_parameters() if name not in decay_names
    ]
    optimizer = torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": training["weight_decay"]},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=training["learning_rate"],
    )
    generator = torch.Generator().manual_seed(seed)
    history: list[dict[str, Any]] = []
    best_ap = -1.0
    best_epoch = 0
    best_p = float("nan")
    best_state: dict[str, torch.Tensor] | None = None
    elapsed_before = 0.0
    encoded_sequences = 0
    encoded_effective_flows = 0
    selection_inference_seconds = 0.0
    start_epoch = 1
    if resume and inflight_path.is_file():
        inflight = torch.load(inflight_path, map_location="cpu", weights_only=False)
        if (
            inflight.get("schema_version") != base.INFLIGHT_SCHEMA
            or inflight.get("identity") != identity
        ):
            raise RuntimeError(f"在途检查点身份不符：{inflight_path}")
        model.load_state_dict(inflight["model"])
        optimizer.load_state_dict(inflight["optimizer"])
        base.move_optimizer_state(optimizer, gX.device)
        history = inflight["history"]
        best_ap = float(inflight["best_ap"])
        best_epoch = int(inflight["best_epoch"])
        best_p = float(inflight["best_p"])
        best_state = inflight["best_state"]
        elapsed_before = float(inflight["elapsed_seconds"])
        encoded_sequences = int(inflight["encoded_sequences"])
        encoded_effective_flows = int(inflight["encoded_effective_flows"])
        selection_inference_seconds = float(inflight["selection_inference_seconds"])
        base.restore_rng(inflight["rng"], generator)
        start_epoch = int(inflight["epoch"]) + 1

    flow_loss = nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    sequence_loss = nn.BCELoss(reduction="none")
    uses_lp = config["cells"][cell]["learned_lp_pooling"]
    members = config["candidate"]["ensemble_members"]
    member_batch = config["candidate"]["member_batch_sequences"]
    device = gX.device
    effective_flow_counter = torch.tensor(
        encoded_effective_flows, dtype=torch.int64, device=device
    )
    unit_started = time.time()
    total_steps = training["epochs"] * training["steps_per_epoch"]
    completed_before = (start_epoch - 1) * training["steps_per_epoch"]
    model.train()
    for epoch in range(start_epoch, training["epochs"] + 1):
        epoch_started = time.time()
        running_loss = 0.0
        for step in range(1, training["steps_per_epoch"] + 1):
            selected_rows = sample_distinct_train_rows(
                train_rows, training["batch_size"], generator
            ).reshape(member_batch, members).to(device)
            indices = gI[selected_rows]
            valid = gM[selected_rows] > 0.5
            values = gX[indices.reshape(-1)].reshape(
                member_batch, members, indices.shape[2], gX.shape[1]
            )
            labels = gy[indices.reshape(-1)].reshape(indices.shape)
            logits = model(values, valid)
            mask = valid.to(logits.dtype)
            encoded_sequences += training["batch_size"]
            effective_flow_counter += valid.sum()
            loss = (flow_loss(logits, labels) * mask).sum() / mask.sum().clamp(min=1.0)
            if uses_lp:
                sequence_scores = base.lp_pool(
                    torch.sigmoid(logits).reshape(-1, logits.shape[-1]),
                    mask.reshape(-1, mask.shape[-1]),
                    model.p,
                ).clamp(1e-6, 1 - 1e-6)
                sequence_labels = (labels * mask).amax(dim=-1).reshape(-1)
                weights = 1.0 + (
                    sequence_positive_weight - 1.0
                ) * sequence_labels
                loss = loss + training["auxiliary_loss_weight"] * (
                    (sequence_loss(sequence_scores, sequence_labels) * weights).sum()
                    / weights.sum()
                )
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), training["gradient_clip_norm"]
            )
            optimizer.step()
            running_loss += float(loss.detach())
            if step % 250 == 0:
                completed = (
                    completed_before
                    + (epoch - start_epoch) * training["steps_per_epoch"]
                    + step
                )
                elapsed = elapsed_before + time.time() - unit_started
                rate = completed / max(elapsed, 1e-9)
                eta = (total_steps - completed) / max(rate, 1e-9)
                base.log(
                    f"{cell}/fold{fold} 心跳 epoch={epoch}/{training['epochs']} "
                    f"step={step}/{training['steps_per_epoch']} "
                    f"累计={elapsed/60:.1f}分 预计剩余={eta/60:.1f}分"
                )
        inference_started = time.time()
        predictions, labels, _ = holdout_predictions(
            model, holdout_rows, gX, gy, gI, gM
        )
        inference_seconds = time.time() - inference_started
        selection_inference_seconds += inference_seconds
        if labels.max() <= 0:
            raise RuntimeError(f"{cell}/fold{fold} 留出逐流标签无正例")
        validation_ap = float(average_precision_score(labels, predictions))
        p_value = float(model.p.detach())
        history.append(
            {
                "epoch": epoch,
                "holdout_flow_ap": validation_ap,
                "p": p_value if uses_lp else None,
                "mean_training_loss": running_loss / training["steps_per_epoch"],
                "holdout_inference_seconds": inference_seconds,
                "epoch_seconds": time.time() - epoch_started,
            }
        )
        if validation_ap > best_ap:
            best_ap = validation_ap
            best_epoch = epoch
            best_p = p_value
            best_state = {
                name: tensor.detach().cpu().clone()
                for name, tensor in model.state_dict().items()
            }
        elapsed = elapsed_before + time.time() - unit_started
        encoded_effective_flows = int(effective_flow_counter.detach())
        base.atomic_torch(
            inflight_path,
            {
                "schema_version": base.INFLIGHT_SCHEMA,
                "identity": identity,
                "epoch": epoch,
                "model": {
                    name: tensor.detach().cpu().clone()
                    for name, tensor in model.state_dict().items()
                },
                "optimizer": optimizer.state_dict(),
                "history": history,
                "best_ap": best_ap,
                "best_epoch": best_epoch,
                "best_p": best_p,
                "best_state": best_state,
                "elapsed_seconds": elapsed,
                "encoded_sequences": encoded_sequences,
                "encoded_effective_flows": encoded_effective_flows,
                "selection_inference_seconds": selection_inference_seconds,
                "rng": base.capture_rng(generator),
            },
        )
        base.append_jsonl(
            output_root / "units" / f"{cell}-fold{fold}" / "progress.jsonl",
            {
                "cell": cell,
                "fold": fold,
                "epoch": epoch,
                "holdout_flow_ap": validation_ap,
                "p": p_value if uses_lp else None,
                "elapsed_seconds": elapsed,
            },
        )
        base.log(
            f"{cell}/fold{fold} epoch {epoch}/{training['epochs']} "
            f"留出逐流AP={validation_ap:.8f} p={p_value:.6f}"
        )

    if best_state is None or best_epoch <= 0:
        raise RuntimeError(f"{cell}/fold{fold} 未产生可选检查点")
    model.load_state_dict(best_state)
    selection = {
        "selected_epoch": best_epoch,
        "holdout_flow_ap": best_ap,
        "p": best_p if uses_lp else None,
        "history": history,
        "training_seconds": elapsed_before + time.time() - unit_started,
        "selection_inference_seconds": selection_inference_seconds,
        "encoded_sequences": encoded_sequences,
        "encoded_effective_flows": encoded_effective_flows,
        "optimizer_steps": training["epochs"] * training["steps_per_epoch"],
        "sequences_per_step": training["batch_size"],
        "share_training_batches": False,
        "member_count": members,
        "training_label_balance": label_balance,
    }
    base.atomic_torch(
        checkpoint_path,
        {
            "schema_version": base.CHECKPOINT_SCHEMA,
            "identity": identity,
            "model": best_state,
            "selection": selection,
        },
    )
    checkpoint_sha = base.sha256_file(checkpoint_path)
    base.atomic_json(
        receipt_path,
        {
            "schema_version": base.RECEIPT_SCHEMA,
            "identity": identity,
            "checkpoint": {
                "filename": checkpoint_path.name,
                "bytes": checkpoint_path.stat().st_size,
                "sha256": checkpoint_sha,
            },
            "selection": selection,
            "completed": True,
        },
    )
    inflight_path.unlink(missing_ok=True)
    return model, selection, "trained"


def aggregate(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    base.aggregate(config, args, config_path)
    output_root = Path(config["paths"]["output_root"])
    result_path = output_root / "aggregate-results.json"
    result = base.load_json(result_path)
    result["schema_version"] = "ch3-tabm-source-oof-results-v1"
    result["model"] = {
        "model_key": MODEL_KEY,
        "display_name": config["display_name"],
        "ensemble_members": MEMBER_COUNT,
        "hidden_size": HIDDEN_SIZE,
        "share_training_batches": False,
        "inference_member_reduction": "mean_sigmoid_probability",
        "cpa_scope": "within_member_along_time",
        "elp_shared_p_count": 1,
        "parameter_count": PARAMETER_COUNT,
        "parameter_formula": config["candidate"]["parameter_formula"],
        "official_source_commit": config["candidate"]["official_source_commit"],
        "pytorch_version": torch.__version__,
    }
    verdict = result["mechanical_verdict"]
    verdict.pop("depth_signal", None)
    verdict["candidate_family"] = MODEL_KEY
    verdict["depth_escalation_not_applicable"] = True
    for cell_units in result["cells"].values():
        for unit in cell_units:
            unit["share_training_batches"] = False
            unit["member_count"] = MEMBER_COUNT
            unit["inference_member_reduction"] = "mean_sigmoid_probability"
    result["artifact_policy"]["member_level_predictions_persisted"] = False
    base.atomic_json(result_path, result)
    base.build_manifest(output_root, config["run_id"])


def install_base_overrides() -> None:
    base.validate_config = validate_config
    base.build_model = build_model
    base.holdout_predictions = holdout_predictions
    base.train_or_resume_unit = train_or_resume_unit


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = base.load_json(config_path)
    validate_config(config)
    if args.validate_config:
        print("配置核验通过")
        return 0
    install_base_overrides()
    try:
        if args.phase == "prepare":
            base.prepare(config, args, config_path)
        elif args.phase == "train-unit":
            base.train_unit(config, args, config_path)
        elif args.phase == "aggregate":
            aggregate(config, args, config_path)
        else:
            base.publish_aggregate(config, args)
    except SystemExit:
        raise
    except Exception as error:
        output_root = Path(config["paths"]["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        detail = f"{type(error).__name__}: {error}"[:1000]
        if args.phase == "train-unit" and args.cell is not None and args.fold is not None:
            base.write_unit_status(
                output_root,
                args.cell,
                args.fold,
                "failed",
                args.phase,
                1,
                detail,
                resource=(
                    base.resource_snapshot()
                    if torch is not None and torch.cuda.is_available()
                    else {}
                ),
            )
        else:
            base.write_status(output_root, "failed", args.phase, 1, detail)
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
