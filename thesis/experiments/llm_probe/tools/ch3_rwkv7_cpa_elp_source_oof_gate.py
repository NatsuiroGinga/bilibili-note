# -*- coding: utf-8 -*-
"""第三章 RWKV-7 与 CPA/ELP 源年实体三折折外资格门。"""

from __future__ import annotations

import argparse
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
F = torch.nn.functional if torch is not None else None

SCHEMA_VERSION = "ch3-rwkv7-source-oof-gate-config-v1"
RESULT_SCHEMA_VERSION = "ch3-rwkv7-source-oof-results-v1"
RUN_ID = "ch3-rwkv7-cpa-elp-source-oof-gate-seed42-v1"
MODEL_KEY = "rwkv7"
HIDDEN_SIZE = 112
HEAD_SIZE = 16
LORA_SIZE = 8
PARAMETER_COUNT = 91_730
OFFICIAL_COMMIT = "952102498e9ed367ea0a59ee64106916d474d30f"
DR_FPR_GRID = (0.01, 0.02, 0.04, 0.08)
ALERT_FPR_GRID = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)

_CAPTURE_ACTIVE = False
_CAPTURE_INDEX = 0
_CAPTURE_ORDER: list[tuple[str, int]] = []
_CAPTURE_FLOW_SCORES: dict[str, np.ndarray] = {}
_CAPTURE_SEEN: dict[str, np.ndarray] = {}
BASE_BUILD_MANIFEST = base.build_manifest


def rwkv7_parameter_count(
    feature_count: int, hidden_size: int, lora_size: int
) -> int:
    return (
        6 * hidden_size * hidden_size
        + 6 * hidden_size * lora_size
        + (feature_count + 16) * hidden_size
        + 2
    )


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置模式版本不符")
    if config.get("run_id") != RUN_ID or config.get("model_key") != MODEL_KEY:
        raise ValueError("RWKV-7 运行身份不符")
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
    expected_folds = {
        "count": 3,
        "assignment": "seeded-stratified-entity-round-robin",
        "map_to_sequences_via": "E23",
        "map_to_flows_via": ["I23", "M23"],
        "require_each_entity_once_oof": True,
        "require_train_holdout_entity_disjoint": True,
    }
    if config["fold_contract"] != expected_folds:
        raise ValueError("实体三折合同不符")
    if config["cells"] != {
        "C00": {"causal_prefix_aggregation": False, "learned_lp_pooling": False},
        "C11": {"causal_prefix_aggregation": True, "learned_lp_pooling": True},
    }:
        raise ValueError("仅允许 C00 与 C11 两格")
    candidate = config["candidate"]
    expected_candidate = {
        "residual_blocks": 0,
        "residual_affine_layers": 0,
        "hidden_size": HIDDEN_SIZE,
        "head_size": HEAD_SIZE,
        "lora_size": LORA_SIZE,
        "time_mix_blocks": 1,
        "state_scope": "within_sequence_only",
        "sequence_length": 128,
        "activation": "relu",
        "dropout": 0.1,
        "inference_batch_size": 512,
        "parameter_formula": "6C^2+6Cr+(D+16)C+2",
        "parameter_count": PARAMETER_COUNT,
        "reference_parameter_count": 90_242,
        "parameter_tolerance_fraction": 0.02,
        "official_repository": "BlinkDL/RWKV-LM",
        "official_source_commit": OFFICIAL_COMMIT,
        "official_license": "Apache-2.0",
        "operator_backend": "pytorch_recursive_reference",
        "official_cuda_kernel_used": False,
    }
    if candidate != expected_candidate:
        raise ValueError("RWKV-7 结构、源码身份或参数预算不是预注册值")
    actual = rwkv7_parameter_count(83, HIDDEN_SIZE, LORA_SIZE)
    if actual != PARAMETER_COUNT:
        raise ValueError("RWKV-7 参数公式计算值不符")
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
    expected_evaluation = {
        "c00_entity_aggregation": "maximum",
        "c11_entity_aggregation": "fold_learned_p",
        "p_diagnostic_grid": [0.5, 1.0, 2.0, 4.0, 8.0],
        "flow_average_precision": True,
        "entity_average_precision": True,
        "dr_fpr_grid": list(DR_FPR_GRID),
        "alert_budget_fpr_grid": list(ALERT_FPR_GRID),
        "mlp_reference_c00_pooled": 0.5109066464488172,
        "mlp_reference_c11_pooled": 0.5447784766847485,
        "qualification_primary_metric_only": "entity_average_precision",
        "qualification_rule": (
            "candidate_c11_gt_xgb_and_candidate_c11_gt_c00_and_"
            "all_fold_c11_gt_c00_and_at_least_two_fold_c11_gt_xgb"
        ),
    }
    if config["evaluation"] != expected_evaluation:
        raise ValueError("RWKV-7 多指标评价合同不符")
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
    if artifacts.get("persist_selected_checkpoint_per_cell_fold") is not True:
        raise ValueError("必须保存六个选定检查点")
    if config["resource_contract"] != {
        "serial_minimum_free_gpu_memory_gib": 12,
        "serial_minimum_cgroup_available_memory_gib": 40,
        "minimum_free_disk_gib": 10,
        "maximum_parallel_training_units": 1,
        "adaptive_parallelism": False,
        "parallelism_policy": "serial_only_for_pytorch_recursive_reference",
    }:
        raise ValueError("RWKV-7 纯 PyTorch 首次串行资源合同不符")
    if config.get("plan_deviation") != {
        "candidate_outside_original_whitelist": True,
        "multi_metric_continuation_added": True,
        "source_screening_only": True,
        "does_not_change_chapter3_body_verdict": True,
    }:
        raise ValueError("计划偏离声明缺失")
    if config.get("rwkv8_exclusion") != {
        "implemented": False,
        "reverse_operator_has_backward": False,
        "formal_paper_frozen": False,
        "stable_training_contract_frozen": False,
        "verdict": "excluded_from_this_round",
    }:
        raise ValueError("RWKV-8 排除合同不符")
    if not config.get("screening_only") or config.get("formal_paper_evidence"):
        raise ValueError("证据等级必须是快速筛选且非正式论文证据")
    if config.get("independent_test") or config.get("target_year_arrays_read") != 0:
        raise ValueError("本门禁不得访问独立测试或目标年数组")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="第三章 RWKV-7 与 CPA/ELP 源年实体三折折外资格门"
    )
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


def rwkv7_op(
    r: "torch.Tensor",
    w: "torch.Tensor",
    k: "torch.Tensor",
    v: "torch.Tensor",
    a: "torch.Tensor",
    b: "torch.Tensor",
    head_size: int,
) -> "torch.Tensor":
    batch, length, channels = r.size()
    heads = channels // head_size
    r = r.view(batch, length, heads, head_size).float()
    k = k.view(batch, length, heads, head_size).float()
    v = v.view(batch, length, heads, head_size).float()
    a = a.view(batch, length, heads, head_size).float()
    b = b.view(batch, length, heads, head_size).float()
    w = torch.exp(-torch.exp(w.view(batch, length, heads, head_size).float()))
    output = torch.zeros(
        (batch, length, heads, head_size), device=r.device, dtype=torch.float
    )
    state = torch.zeros(
        (batch, heads, head_size, head_size), device=r.device, dtype=torch.float
    )
    for position in range(length):
        kk = k[:, position, :].view(batch, heads, 1, head_size)
        rr = r[:, position, :].view(batch, heads, head_size, 1)
        vv = v[:, position, :].view(batch, heads, head_size, 1)
        aa = a[:, position, :].view(batch, heads, head_size, 1)
        bb = b[:, position, :].view(batch, heads, 1, head_size)
        state = state * w[:, position, :, None, :] + state @ aa @ bb + vv @ kk
        output[:, position, :] = (state @ rr).view(
            batch, heads, head_size
        )
    return output.view(batch, length, channels)


if nn is not None:
    class RWKV7TimeMix(nn.Module):
        """固定官方提交的单个 RWKV-7 时间混合块纯 PyTorch 路径。"""

        def __init__(self, channels: int, head_size: int, lora_size: int):
            super().__init__()
            if channels % head_size != 0:
                raise ValueError("RWKV-7 通道数必须能被头大小整除")
            heads = channels // head_size
            self.channels = channels
            self.head_size = head_size
            self.heads = heads
            with torch.no_grad():
                ddd = torch.arange(channels, dtype=torch.float32).reshape(
                    1, 1, channels
                ) / channels
                self.x_r = nn.Parameter(1.0 - torch.pow(ddd, 0.2))
                self.x_w = nn.Parameter(1.0 - torch.pow(ddd, 0.9))
                self.x_k = nn.Parameter(1.0 - torch.pow(ddd, 0.7))
                self.x_v = nn.Parameter(1.0 - torch.pow(ddd, 0.7))
                self.x_a = nn.Parameter(1.0 - torch.pow(ddd, 0.9))
                self.x_g = nn.Parameter(1.0 - torch.pow(ddd, 0.2))
                www = torch.zeros(channels)
                zigzag = torch.zeros(channels)
                linear = torch.zeros(channels)
                for index in range(channels):
                    linear[index] = index / (channels - 1) - 0.5
                    zigzag[index] = (
                        (index % head_size) - ((head_size - 1) / 2)
                    ) / ((head_size - 1) / 2)
                    zigzag[index] = zigzag[index] * abs(zigzag[index])
                    www[index] = -6 + 6 * (index / (channels - 1))

                def ortho_init(value: "torch.Tensor", scale: float) -> "torch.Tensor":
                    gain = math.sqrt(value.shape[0] / value.shape[1]) if value.shape[0] > value.shape[1] else 1.0
                    nn.init.orthogonal_(value, gain=gain * scale)
                    return value

                self.w1 = nn.Parameter(torch.zeros(channels, lora_size))
                self.w2 = nn.Parameter(ortho_init(torch.zeros(lora_size, channels), 0.1))
                self.w0 = nn.Parameter(
                    www.reshape(1, 1, channels) + 0.5 + zigzag * 2.5
                )
                self.a1 = nn.Parameter(torch.zeros(channels, lora_size))
                self.a2 = nn.Parameter(ortho_init(torch.zeros(lora_size, channels), 0.1))
                self.a0 = nn.Parameter(
                    torch.zeros(1, 1, channels) - 0.19 + zigzag * 0.3 + linear * 0.4
                )
                self.g1 = nn.Parameter(torch.zeros(channels, lora_size))
                self.g2 = nn.Parameter(ortho_init(torch.zeros(lora_size, channels), 0.1))
                self.k_k = nn.Parameter(
                    torch.zeros(1, 1, channels) + 0.71 - linear * 0.1
                )
                self.k_a = nn.Parameter(torch.zeros(1, 1, channels) + 1.02)
                self.r_k = nn.Parameter(torch.zeros(heads, head_size) - 0.04)
                self.time_shift = nn.ZeroPad2d((0, 0, 1, -1))
                self.receptance = nn.Linear(channels, channels, bias=False)
                self.key = nn.Linear(channels, channels, bias=False)
                self.value = nn.Linear(channels, channels, bias=False)
                self.output = nn.Linear(channels, channels, bias=False)
                self.ln_x = nn.GroupNorm(heads, channels, eps=64e-5)
                self.receptance.weight.data.uniform_(
                    -0.5 / math.sqrt(channels), 0.5 / math.sqrt(channels)
                )
                self.key.weight.data.uniform_(
                    -0.05 / math.sqrt(channels), 0.05 / math.sqrt(channels)
                )
                self.value.weight.data.uniform_(
                    -0.5 / math.sqrt(channels), 0.5 / math.sqrt(channels)
                )
                self.output.weight.data.zero_()

        def forward(self, values: "torch.Tensor") -> "torch.Tensor":
            batch, length, channels = values.size()
            shifted = self.time_shift(values) - values
            xr = values + shifted * self.x_r
            xw = values + shifted * self.x_w
            xk = values + shifted * self.x_k
            xv = values + shifted * self.x_v
            xa = values + shifted * self.x_a
            xg = values + shifted * self.x_g
            r = self.receptance(xr)
            w = -F.softplus(-(self.w0 + torch.tanh(xw @ self.w1) @ self.w2)) - 0.5
            k = self.key(xk)
            v = self.value(xv)
            a = torch.sigmoid(self.a0 + (xa @ self.a1) @ self.a2)
            g = torch.sigmoid(xg @ self.g1) @ self.g2
            kk = k * self.k_k
            kk = F.normalize(
                kk.view(batch, length, self.heads, -1), dim=-1, p=2.0
            ).view(batch, length, channels)
            k = k * (1 + (a - 1) * self.k_a)
            output = rwkv7_op(r, w, k, v, -kk, kk * a, self.head_size)
            output = self.ln_x(output.view(batch * length, channels)).view(
                batch, length, channels
            )
            bonus = (
                (
                    r.view(batch, length, self.heads, -1)
                    * k.view(batch, length, self.heads, -1)
                    * self.r_k
                ).sum(dim=-1, keepdim=True)
                * v.view(batch, length, self.heads, -1)
            ).view(batch, length, channels)
            return self.output((output + bonus) * g)


    class RWKV7Backbone(nn.Module):
        def __init__(
            self,
            feature_count: int,
            hidden_size: int,
            head_size: int,
            lora_size: int,
            dropout: float,
            aggregate: bool,
        ):
            super().__init__()
            self.aggregate = aggregate
            self.input_layer = nn.Linear(feature_count, hidden_size)
            self.time_mix = RWKV7TimeMix(hidden_size, head_size, lora_size)
            self.fusion_layer = nn.Sequential(
                nn.Linear(hidden_size * 2, hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout),
            )
            self.output_layer = nn.Linear(hidden_size, 1)
            self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

        @property
        def p(self) -> "torch.Tensor":
            return torch.exp(self.p_log).clamp(1e-3, 1e3)

        def forward(
            self, values: "torch.Tensor", valid: "torch.Tensor"
        ) -> "torch.Tensor":
            mask = valid.to(values.dtype)
            hidden = self.input_layer(values * mask.unsqueeze(-1))
            hidden = self.time_mix(hidden * mask.unsqueeze(-1))
            hidden = hidden * mask.unsqueeze(-1)
            if self.aggregate:
                context = torch.cumsum(hidden, dim=1) / torch.cumsum(
                    mask, dim=1
                ).clamp(min=1.0).unsqueeze(-1)
                context = context * mask.unsqueeze(-1)
            else:
                context = torch.zeros_like(hidden)
            fused = self.fusion_layer(torch.cat((hidden, context), dim=-1))
            fused = fused * mask.unsqueeze(-1)
            return self.output_layer(fused).squeeze(-1)
else:
    class RWKV7TimeMix:
        pass


    class RWKV7Backbone:
        pass


def build_model(config: dict[str, Any], cell: str) -> RWKV7Backbone:
    if torch is None or nn is None:
        raise RuntimeError("正式计算缺少 torch；请加载项目 GPU 可选依赖")
    candidate = config["candidate"]
    model = RWKV7Backbone(
        config["input_contract"]["feature_count"],
        candidate["hidden_size"],
        candidate["head_size"],
        candidate["lora_size"],
        config["training"]["dropout"],
        config["cells"][cell]["causal_prefix_aggregation"],
    )
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != candidate["parameter_count"]:
        raise RuntimeError(f"RWKV-7 模型参数量不符：{actual}")
    reference = candidate["reference_parameter_count"]
    if abs(actual - reference) / reference > candidate["parameter_tolerance_fraction"]:
        raise RuntimeError("RWKV-7 参数量超出百分之二预算")
    return model


@base.no_grad_if_available
def holdout_predictions(
    model: RWKV7Backbone,
    rows: np.ndarray,
    gX: "torch.Tensor",
    gy: "torch.Tensor",
    gI: "torch.Tensor",
    gM: "torch.Tensor",
    inference_batch_size: int = 512,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    global _CAPTURE_INDEX
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
        logits = model(values, valid)
        mask = valid.reshape(-1)
        predictions.append(
            torch.sigmoid(logits).reshape(-1)[mask].float().cpu().numpy()
        )
        labels.append(
            gy[indices.reshape(-1)].reshape(-1)[mask].float().cpu().numpy()
        )
        flow_ids.append(indices.reshape(-1)[mask].cpu().numpy())
    model.train()
    prediction = np.concatenate(predictions)
    label = np.concatenate(labels)
    flow_id = np.concatenate(flow_ids)
    if _CAPTURE_ACTIVE:
        if _CAPTURE_INDEX >= len(_CAPTURE_ORDER):
            raise RuntimeError("聚合预测捕获次数超过六单元合同")
        cell, _ = _CAPTURE_ORDER[_CAPTURE_INDEX]
        _CAPTURE_FLOW_SCORES[cell][flow_id] = prediction
        _CAPTURE_SEEN[cell][flow_id] = True
        _CAPTURE_INDEX += 1
    return prediction, label, flow_id


def dr_at_fpr(
    entity_scores: np.ndarray,
    entity_labels: np.ndarray,
    target_fpr: float,
    mask: np.ndarray | None = None,
) -> float:
    valid = np.isfinite(entity_scores)
    if mask is not None:
        valid &= mask
    values = entity_scores[valid]
    labels = entity_labels[valid]
    negative = np.sort(values[labels == 0])[::-1]
    positive = values[labels == 1]
    if len(negative) == 0 or len(positive) == 0:
        raise RuntimeError("检测率子集缺少正类或负类实体")
    threshold = negative[min(int(len(negative) * target_fpr), len(negative) - 1)]
    return float((positive >= threshold).mean())


def metric_bundle(
    flow_scores: np.ndarray,
    flow_labels: np.ndarray,
    flow_entity: np.ndarray,
    entity_scores: np.ndarray,
    entity_labels: np.ndarray,
    flow_mask: np.ndarray | None = None,
    entity_mask: np.ndarray | None = None,
) -> dict[str, Any]:
    valid_flow = np.isfinite(flow_scores)
    if flow_mask is not None:
        valid_flow &= flow_mask
    if flow_labels[valid_flow].max() <= 0 or flow_labels[valid_flow].min() >= 1:
        raise RuntimeError("逐流 AP 子集缺少正类或负类")
    valid_entity = np.isfinite(entity_scores)
    if entity_mask is not None:
        valid_entity &= entity_mask
    return {
        "flow_average_precision": float(
            average_precision_score(flow_labels[valid_flow], flow_scores[valid_flow])
        ),
        "entity_average_precision": float(
            average_precision_score(
                entity_labels[valid_entity], entity_scores[valid_entity]
            )
        ),
        "dr_at_fpr": {
            f"fpr_{value:g}": dr_at_fpr(
                entity_scores, entity_labels, value, entity_mask
            )
            for value in DR_FPR_GRID
        },
        "alert_budget_anchor_points": {
            f"fpr_{value:g}": dr_at_fpr(
                entity_scores, entity_labels, value, entity_mask
            )
            for value in ALERT_FPR_GRID
        },
        "flow_count": int(valid_flow.sum()),
        "entity_count": int(valid_entity.sum()),
        "per_sample_values_persisted": False,
    }


def complete_budget_curve(
    entity_scores: np.ndarray,
    entity_labels: np.ndarray,
    mask: np.ndarray | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    """按既有告警预算语义返回全部可达负实体预算点。"""
    valid = np.isfinite(entity_scores)
    if mask is not None:
        valid &= mask
    values = entity_scores[valid]
    labels = entity_labels[valid]
    positive = np.sort(values[labels == 1])
    negative = np.sort(values[labels == 0])[::-1]
    if len(positive) == 0 or len(negative) == 0:
        raise RuntimeError("完整告警预算曲线子集缺少正类或负类")
    detection_rate = (
        len(positive) - np.searchsorted(positive, negative, side="left")
    ) / len(positive)
    negative_ascending = negative[::-1]
    false_positive = len(negative) - np.searchsorted(
        negative_ascending, negative, side="left"
    )
    return (
        {
            "n_false_positive_entity": false_positive.astype(np.int64),
            "nominal_fpr": np.arange(len(negative), dtype=np.float64)
            / len(negative),
            "realized_fpr": false_positive.astype(np.float64) / len(negative),
            "detection_rate": detection_rate.astype(np.float64),
        },
        {
            "n_positive_entity": int(len(positive)),
            "n_negative_entity": int(len(negative)),
            "n_scored_entity": int(valid.sum()),
            "point_count": int(len(negative)),
        },
    )


def write_complete_budget_curves(
    output_root: Path,
    entity_results: dict[str, np.ndarray],
    entity_labels: np.ndarray,
    fold_of_entity: np.ndarray,
) -> dict[str, Any]:
    artifact_path = output_root / "complete-alert-budget-curves.npz"
    temporary_path = artifact_path.with_name(f"{artifact_path.name}.partial")
    arrays: dict[str, np.ndarray] = {}
    scopes: dict[str, dict[str, int]] = {}
    for cell in base.CELL_ORDER:
        scope_masks: list[tuple[str, np.ndarray | None]] = [("pooled", None)]
        scope_masks.extend(
            (f"fold{fold}", fold_of_entity == fold) for fold in range(3)
        )
        for scope, mask in scope_masks:
            curve, metadata = complete_budget_curve(
                entity_results[cell], entity_labels, mask
            )
            key = f"{cell}__{scope}"
            scopes[key] = metadata
            for field, values in curve.items():
                arrays[f"{key}__{field}"] = values
    with temporary_path.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    temporary_path.replace(artifact_path)
    receipt = {
        "schema_version": "ch3-rwkv7-complete-alert-budget-curves-v1",
        "artifact": {
            "filename": artifact_path.name,
            "bytes": artifact_path.stat().st_size,
            "sha256": base.sha256_file(artifact_path),
            "format": "npz",
        },
        "fields": [
            "n_false_positive_entity",
            "nominal_fpr",
            "realized_fpr",
            "detection_rate",
        ],
        "scope_count": len(scopes),
        "scopes": scopes,
        "thresholds_persisted": False,
        "per_flow_scores_persisted": False,
        "per_entity_scores_persisted": False,
        "curve_is_complete_over_all_reachable_negative_entity_budgets": True,
    }
    receipt_path = output_root / "complete-alert-budget-curves-receipt.json"
    base.atomic_json(receipt_path, receipt)
    return receipt


def build_manifest(output_root: Path, run_id: str) -> None:
    BASE_BUILD_MANIFEST(output_root, run_id)
    curve_path = output_root / "complete-alert-budget-curves.npz"
    receipt_path = output_root / "complete-alert-budget-curves-receipt.json"
    if curve_path.is_file() != receipt_path.is_file():
        raise RuntimeError("完整告警预算曲线与收据不成对")
    if not curve_path.is_file():
        return
    manifest_path = output_root / "manifest.json"
    manifest = base.load_json(manifest_path)
    manifest["schema_version"] = "ch3-rwkv7-source-oof-manifest-v1"
    for path in (curve_path, receipt_path):
        manifest["files"][path.name] = {
            "bytes": path.stat().st_size,
            "sha256": base.sha256_file(path),
        }
    manifest["complete_alert_budget_curve_persisted"] = True
    manifest["per_flow_scores_persisted"] = False
    manifest["per_entity_scores_persisted"] = False
    base.atomic_json(manifest_path, manifest)


def build_entity_results(
    result: dict[str, Any],
    flow_scores: dict[str, np.ndarray],
    flow_entity: np.ndarray,
    entity_count: int,
    fold_of_flow: np.ndarray,
    fold_of_entity: np.ndarray,
) -> dict[str, np.ndarray]:
    c00 = base.entity_scores(flow_scores["C00"], flow_entity, entity_count, None)
    c11 = np.full(entity_count, -np.inf, dtype=np.float32)
    for fold in range(3):
        p_value = float(result["folds"][fold]["C11_learned_p"])
        fold_scores = base.entity_scores(
            flow_scores["C11"],
            flow_entity,
            entity_count,
            p_value,
            fold_of_flow == fold,
        )
        entity_mask = fold_of_entity == fold
        c11[entity_mask] = fold_scores[entity_mask]
    if not np.isfinite(c00).all() or not np.isfinite(c11).all():
        raise RuntimeError("RWKV-7 多指标实体分数未完整覆盖")
    return {"C00": c00, "C11": c11}


def enrich_aggregate_metrics(
    config: dict[str, Any], args: argparse.Namespace
) -> None:
    output_root = Path(config["paths"]["output_root"])
    result_path = output_root / "aggregate-results.json"
    result = base.load_json(result_path)
    y = np.asarray(base.guarded_load(config, "y23"))
    I = base.guarded_load(config, "I23")
    M = base.guarded_load(config, "M23")
    E = base.guarded_load(config, "E23")
    contract = config["input_contract"]
    flow_entity = base.build_flow_entity(
        I, M, E, contract["flow_count"], contract["entity_count"]
    )
    entity_labels = np.zeros(contract["entity_count"], dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, y)
    fold_of_entity = base.make_entity_folds(
        entity_labels, config["training"]["seed"], 3
    )
    fold_of_flow = fold_of_entity[flow_entity]
    if _CAPTURE_INDEX != 6:
        raise RuntimeError(f"聚合预测捕获应为六次，实际为 {_CAPTURE_INDEX}")
    for cell in base.CELL_ORDER:
        if not _CAPTURE_SEEN[cell].all() or not np.isfinite(
            _CAPTURE_FLOW_SCORES[cell]
        ).all():
            raise RuntimeError(f"{cell} 多指标逐流 OOF 未完整覆盖")
    entity_results = build_entity_results(
        result,
        _CAPTURE_FLOW_SCORES,
        flow_entity,
        contract["entity_count"],
        fold_of_flow,
        fold_of_entity,
    )
    complete_curve_receipt = write_complete_budget_curves(
        output_root, entity_results, entity_labels, fold_of_entity
    )
    continuation: dict[str, Any] = {
        "schema_version": "ch3-rwkv7-source-oof-multi-metrics-v1",
        "participates_in_primary_qualification": False,
        "primary_qualification_metric": "entity_average_precision",
        "dr_fpr_grid": list(DR_FPR_GRID),
        "alert_budget_anchor_fpr_grid": list(ALERT_FPR_GRID),
        "complete_curve_artifact": complete_curve_receipt["artifact"],
        "complete_curve_scope_count": complete_curve_receipt["scope_count"],
        "complete_curve_is_all_reachable_negative_entity_budgets": True,
        "cells": {},
        "per_sample_values_persisted": False,
    }
    for cell in base.CELL_ORDER:
        folds = []
        for fold in range(3):
            folds.append(
                {
                    "fold": fold,
                    **metric_bundle(
                        _CAPTURE_FLOW_SCORES[cell],
                        y,
                        flow_entity,
                        entity_results[cell],
                        entity_labels,
                        flow_mask=fold_of_flow == fold,
                        entity_mask=fold_of_entity == fold,
                    ),
                }
            )
        pooled = metric_bundle(
            _CAPTURE_FLOW_SCORES[cell],
            y,
            flow_entity,
            entity_results[cell],
            entity_labels,
        )
        continuation["cells"][cell] = {"pooled_oof": pooled, "folds": folds}
        result["pooled_oof"][f"{cell}_flow_ap"] = pooled[
            "flow_average_precision"
        ]
        result["pooled_oof"][f"{cell}_dr_at_fpr"] = pooled["dr_at_fpr"]
        result["pooled_oof"][f"{cell}_alert_budget_anchor_points"] = pooled[
            "alert_budget_anchor_points"
        ]
        for fold in range(3):
            result["folds"][fold][f"{cell}_flow_ap"] = folds[fold][
                "flow_average_precision"
            ]
            result["folds"][fold][f"{cell}_dr_at_fpr"] = folds[fold][
                "dr_at_fpr"
            ]
            result["folds"][fold][f"{cell}_alert_budget_anchor_points"] = folds[fold][
                "alert_budget_anchor_points"
            ]
    checkpoint_bytes_total = 0
    unit_throughputs: list[float] = []
    inference_throughputs: list[float] = []
    for cell in base.CELL_ORDER:
        for fold, unit in enumerate(result["cells"][cell]):
            checkpoint_path, _, receipt_path = base.unit_paths(
                output_root, cell, fold
            )
            receipt = base.load_json(receipt_path)
            checkpoint_bytes = int(receipt["checkpoint"]["bytes"])
            if checkpoint_bytes != checkpoint_path.stat().st_size:
                raise RuntimeError(f"{cell}/fold{fold} 检查点字节数收据不符")
            train_seconds = float(unit["training_seconds"])
            infer_seconds = float(unit["aggregate_inference_seconds"])
            train_throughput = float(unit["encoded_effective_flows"]) / max(
                train_seconds, 1e-9
            )
            infer_throughput = float(unit["holdout_prediction_occurrences"]) / max(
                infer_seconds, 1e-9
            )
            unit["checkpoint_bytes"] = checkpoint_bytes
            unit["training_effective_flows_per_second"] = train_throughput
            unit["aggregate_inference_flows_per_second"] = infer_throughput
            checkpoint_bytes_total += checkpoint_bytes
            unit_throughputs.append(train_throughput)
            inference_throughputs.append(infer_throughput)
    result["schema_version"] = RESULT_SCHEMA_VERSION
    result["evidence"]["original_plan_candidate_whitelist_extended"] = True
    result["evidence"]["chapter3_body_verdict_changed"] = False
    result["evidence"]["rwkv8_implemented"] = False
    result["evidence"]["rwkv8_exclusion"] = config["rwkv8_exclusion"]
    result["model"] = {
        "model_key": MODEL_KEY,
        "display_name": config["display_name"],
        "hidden_size": HIDDEN_SIZE,
        "head_size": HEAD_SIZE,
        "lora_size": LORA_SIZE,
        "time_mix_blocks": 1,
        "state_scope": "within_sequence_only",
        "parameter_count": PARAMETER_COUNT,
        "parameter_formula": config["candidate"]["parameter_formula"],
        "official_repository": config["candidate"]["official_repository"],
        "official_source_commit": OFFICIAL_COMMIT,
        "official_license": "Apache-2.0",
        "operator_backend": "pytorch_recursive_reference",
        "official_cuda_kernel_used": False,
        "pytorch_version": torch.__version__,
    }
    verdict = result["mechanical_verdict"]
    verdict.pop("depth_signal", None)
    verdict["candidate_family"] = MODEL_KEY
    verdict["depth_escalation_not_applicable"] = True
    result["multi_metric_continuation"] = continuation
    result["artifact_policy"]["complete_alert_budget_curve_persisted"] = True
    result["artifact_policy"]["complete_alert_budget_curve_is_aggregate"] = True
    result["artifact_policy"]["alert_budget_thresholds_persisted"] = False
    result["resource"]["checkpoint_bytes_total"] = checkpoint_bytes_total
    result["resource"]["adaptive_parallelism"] = False
    result["resource"]["training_effective_flows_per_second_range"] = [
        min(unit_throughputs),
        max(unit_throughputs),
    ]
    result["resource"]["aggregate_inference_flows_per_second_range"] = [
        min(inference_throughputs),
        max(inference_throughputs),
    ]
    result["resource"]["efficiency_scope"] = (
        "pytorch_recursive_reference_not_official_cuda_kernel"
    )
    base.atomic_json(result_path, result)
    base.atomic_json(output_root / "fold-results.json", {"folds": result["folds"]})
    base.build_manifest(output_root, config["run_id"])


def aggregate(
    config: dict[str, Any], args: argparse.Namespace, config_path: Path
) -> None:
    global _CAPTURE_ACTIVE, _CAPTURE_INDEX
    global _CAPTURE_ORDER, _CAPTURE_FLOW_SCORES, _CAPTURE_SEEN
    flow_count = config["input_contract"]["flow_count"]
    _CAPTURE_INDEX = 0
    _CAPTURE_ORDER = [
        (cell, fold) for cell in base.CELL_ORDER for fold in range(3)
    ]
    _CAPTURE_FLOW_SCORES = {
        cell: np.full(flow_count, np.nan, dtype=np.float32)
        for cell in base.CELL_ORDER
    }
    _CAPTURE_SEEN = {
        cell: np.zeros(flow_count, dtype=np.bool_) for cell in base.CELL_ORDER
    }
    _CAPTURE_ACTIVE = True
    try:
        base.aggregate(config, args, config_path)
        _CAPTURE_ACTIVE = False
        enrich_aggregate_metrics(config, args)
    finally:
        _CAPTURE_ACTIVE = False
        _CAPTURE_ORDER = []
        _CAPTURE_FLOW_SCORES = {}
        _CAPTURE_SEEN = {}


def publish_aggregate(config: dict[str, Any], args: argparse.Namespace) -> None:
    base.validate_destination(config, args)
    output_root = Path(config["paths"]["output_root"])
    result_path = output_root / "aggregate-results.json"
    if not result_path.is_file():
        raise RuntimeError("聚合结果不存在，禁止创建 SwanLab 运行")
    result = base.load_json(result_path)
    if (
        result["input"]["arrays"] != list(base.ALLOWED_ARRAYS)
        or result["input"]["target_year_arrays_read"] != 0
    ):
        raise RuntimeError("聚合结果不能证明源年隔离")
    base.validate_tracking_gate(output_root, args.tracking_attempt)
    import swanlab

    destination = config["swanlab"]
    try:
        swanlab.init(
            workspace=args.authorized_swanlab_workspace,
            project=args.authorized_swanlab_project,
            name=config["run_id"],
            mode=destination["mode"],
            group=destination["group"],
            tags=[*destination["tags"], "aggregate-only"],
            log_dir=str(
                output_root
                / "swanlog"
                / "aggregate"
                / f"attempt-{args.tracking_attempt}"
            ),
            config={
                "run_id": config["run_id"],
                "seed": config["training"]["seed"],
                "fits": 6,
                "folds": 3,
                "screening_only": True,
                "formal_paper_evidence": False,
                "aggregate_only": True,
                "rwkv8_implemented": False,
            },
        )
    except Exception as error:
        retryable = base.is_swanlab_init_401(error) and args.tracking_attempt == 1
        base.atomic_json(
            output_root
            / "tracking-attempts"
            / f"attempt-{args.tracking_attempt}-failure.json",
            {
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
                "http_401_unauthorized": base.is_swanlab_init_401(error),
                "bounded_retry_allowed": retryable,
                "requires_new_process": True,
            },
        )
        raise SystemExit(81 if retryable else 82) from error
    pooled = result["pooled_oof"]
    metrics: dict[str, float] = {
        "source_oof/C00_entity_ap": pooled["C00_entity_ap"],
        "source_oof/C11_entity_ap": pooled["C11_entity_ap"],
        "source_oof/C00_flow_ap": pooled["C00_flow_ap"],
        "source_oof/C11_flow_ap": pooled["C11_flow_ap"],
        "source_oof/delta_C11_minus_C00": pooled["delta_C11_minus_C00"],
        "source_oof/C11_minus_mlp_C11": result["comparisons"][
            "candidate_C11_minus_mlp_C11"
        ],
        "source_oof/C11_minus_xgb_C11": result["comparisons"][
            "candidate_C11_minus_xgb_C11"
        ],
        "source_oof/source_qualified": float(
            result["mechanical_verdict"]["source_qualified"]
        ),
        "runtime/total_seconds": result["resource"]["launcher_receipt"][
            "overall_wall_seconds_through_aggregate"
        ],
        "runtime/checkpoint_bytes_total": float(
            result["resource"]["checkpoint_bytes_total"]
        ),
    }
    for cell in base.CELL_ORDER:
        cell_metrics = result["multi_metric_continuation"]["cells"][cell]
        for key, value in cell_metrics["pooled_oof"]["dr_at_fpr"].items():
            metrics[f"source_oof/{cell}_dr_{key}"] = value
        for key, value in cell_metrics["pooled_oof"]["alert_budget_anchor_points"].items():
            metrics[f"alert_budget/{cell}_{key}"] = value
        for fold in cell_metrics["folds"]:
            index = fold["fold"]
            metrics[f"fold{index}/{cell}_flow_ap"] = fold[
                "flow_average_precision"
            ]
            metrics[f"fold{index}/{cell}_entity_ap"] = fold[
                "entity_average_precision"
            ]
            for key, value in fold["dr_at_fpr"].items():
                metrics[f"fold{index}/{cell}_dr_{key}"] = value
    swanlab.log(metrics, step=0)
    swanlab.finish()
    base.atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-rwkv7-source-oof-swanlab-receipt-v1",
            "completed": True,
            "aggregate_only": True,
            "attempt": args.tracking_attempt,
            "workspace": destination["workspace"],
            "project": destination["project"],
            "metric_count": len(metrics),
            "per_sample_values_uploaded": False,
        },
    )
    base.write_status(output_root, "complete", "finished", 0, "计算与聚合上报完成")
    base.build_manifest(output_root, config["run_id"])
    base.log("RWKV-7 多指标聚合上报完成")


def install_base_overrides() -> None:
    base.validate_config = validate_config
    base.build_model = build_model
    base.holdout_predictions = holdout_predictions
    base.build_manifest = build_manifest


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
            publish_aggregate(config, args)
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
