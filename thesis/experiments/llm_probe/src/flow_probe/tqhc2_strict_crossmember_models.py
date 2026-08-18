"""TQH-C2 严格跨成员 Q0 的模型、训练目标与聚合指标。"""

from __future__ import annotations

import math
import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score

try:
    import torch
    from torch import nn
    from torch.nn import functional as functional
except ModuleNotFoundError:
    torch = None  # type: ignore[assignment]

    class _UnavailableModule:
        pass

    class _UnavailableNN:
        Module = _UnavailableModule

    nn = _UnavailableNN()  # type: ignore[assignment]
    functional = None  # type: ignore[assignment]


class StrictCrossMemberModelError(RuntimeError):
    """表示模型身份、训练目标或推理合同被破坏。"""


EPSILON = 1e-6
DELTA_BOUND = math.log(10.0)
SOURCE_MEMBER_SET = frozenset({"A", "B", "D"})
PAIRWISE_DISPLAY_NAME = "线性1%部分AUC成对排名近似"
PAIRWISE_FIDELITY = "pairwise_ranking_approximation"


def _require_torch() -> Any:
    if torch is None:
        raise StrictCrossMemberModelError("神经身份需要项目 gpu 可选组中的 PyTorch")
    return torch


def set_seed(seed: int) -> None:
    _require_torch()
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def device_from_config(value: str) -> torch.device:
    _require_torch()
    if value == "cuda":
        if not torch.cuda.is_available():
            raise StrictCrossMemberModelError("神经身份要求 CUDA，不得缩小容量或静默回退 CPU")
        return torch.device("cuda")
    if value == "cpu":
        return torch.device("cpu")
    raise StrictCrossMemberModelError(f"未知设备：{value}")


@dataclass(frozen=True)
class RobustScaler:
    median: np.ndarray
    iqr: np.ndarray

    @classmethod
    def fit(cls, values: np.ndarray) -> RobustScaler:
        transformed = np.log1p(np.asarray(values, dtype=np.float64))
        median = np.median(transformed, axis=0)
        q25, q75 = np.quantile(transformed, (0.25, 0.75), axis=0)
        iqr = q75 - q25
        iqr[iqr == 0.0] = 1.0
        return cls(median=median.astype(np.float32), iqr=iqr.astype(np.float32))

    def transform(self, values: np.ndarray) -> np.ndarray:
        transformed = np.log1p(np.asarray(values, dtype=np.float32))
        result = (transformed - self.median) / self.iqr
        if not np.isfinite(result).all():
            raise StrictCrossMemberModelError("稳健缩放产生非有限值")
        return result.astype(np.float32, copy=False)


def logit(probability: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(probability, dtype=np.float64), EPSILON, 1.0 - EPSILON)
    return np.log(clipped / (1.0 - clipped))


def sigmoid(score: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(score, dtype=np.float64), -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def normalized_partial_auc(y: np.ndarray, score: np.ndarray, max_fpr: float = 0.01) -> float:
    labels = np.asarray(y, dtype=np.uint8)
    scores = np.asarray(score, dtype=np.float64)
    if labels.shape != scores.shape or set(np.unique(labels)) != {0, 1}:
        raise StrictCrossMemberModelError("部分曲线下面积要求同形且同时含正负类")
    order = np.argsort(-scores, kind="stable")
    labels = labels[order]
    scores = scores[order]
    positives = int(np.count_nonzero(labels == 1))
    negatives = int(np.count_nonzero(labels == 0))
    distinct_end = np.r_[np.flatnonzero(np.diff(scores)), len(scores) - 1]
    true_positive = np.cumsum(labels == 1)[distinct_end] / positives
    false_positive = np.cumsum(labels == 0)[distinct_end] / negatives
    fpr = np.r_[0.0, false_positive]
    tpr = np.r_[0.0, true_positive]
    if fpr[-1] < max_fpr:
        raise StrictCrossMemberModelError("ROC 未覆盖预注册低误报区间")
    cut = int(np.searchsorted(fpr, max_fpr, side="right"))
    clipped_fpr = fpr[:cut]
    clipped_tpr = tpr[:cut]
    if clipped_fpr[-1] < max_fpr:
        right = cut
        left = right - 1
        slope = (tpr[right] - tpr[left]) / (fpr[right] - fpr[left])
        clipped_tpr = np.r_[clipped_tpr, tpr[left] + slope * (max_fpr - fpr[left])]
        clipped_fpr = np.r_[clipped_fpr, max_fpr]
    return float(np.trapezoid(clipped_tpr, clipped_fpr) / max_fpr)


def recall_at_fpr(y: np.ndarray, score: np.ndarray, max_fpr: float = 0.01) -> float:
    labels = np.asarray(y, dtype=np.uint8)
    scores = np.asarray(score, dtype=np.float64)
    negatives = np.sort(scores[labels == 0])[::-1]
    positives = scores[labels == 1]
    if len(negatives) == 0 or len(positives) == 0:
        raise StrictCrossMemberModelError("低误报召回要求同时含正负类")
    maximum_false_positives = int(math.floor(max_fpr * len(negatives)))
    if maximum_false_positives == 0:
        threshold = float(np.nextafter(negatives[0], math.inf))
    else:
        threshold = float(negatives[maximum_false_positives - 1])
    return float(np.mean(positives >= threshold))


def aggregate_metrics(
    y: np.ndarray, score: np.ndarray, source_threshold: float | None = None
) -> dict[str, float]:
    labels = np.asarray(y, dtype=np.uint8)
    scores = np.asarray(score, dtype=np.float64)
    probabilities = sigmoid(scores)
    result = {
        "npauc_0_01": normalized_partial_auc(labels, scores),
        "recall_at_fpr_0_01": recall_at_fpr(labels, scores),
        "roc_auc": float(roc_auc_score(labels, scores)),
        "pr_auc": float(average_precision_score(labels, scores)),
        "negative_log_likelihood": float(log_loss(labels, probabilities, labels=[0, 1])),
        "brier": float(np.mean(np.square(probabilities - labels))),
    }
    if source_threshold is not None:
        predicted = scores >= source_threshold
        true_positive = int(np.count_nonzero(predicted & (labels == 1)))
        false_positive = int(np.count_nonzero(predicted & (labels == 0)))
        true_negative = int(np.count_nonzero(~predicted & (labels == 0)))
        false_negative = int(np.count_nonzero(~predicted & (labels == 1)))
        recall = true_positive / max(true_positive + false_negative, 1)
        precision = true_positive / max(true_positive + false_positive, 1)
        negative_precision = true_negative / max(true_negative + false_negative, 1)
        negative_recall = true_negative / max(true_negative + false_positive, 1)
        negative_f1 = 2 * negative_precision * negative_recall / max(
            negative_precision + negative_recall, 1e-12
        )
        positive_f1 = 2 * precision * recall / max(precision + recall, 1e-12)
        result.update(
            {
                "source_threshold": float(source_threshold),
                "false_positive_rate": false_positive / max(false_positive + true_negative, 1),
                "alerts_per_10000_negative": 10_000
                * false_positive
                / max(false_positive + true_negative, 1),
                "c2_recall": recall,
                "precision": precision,
                "macro_f1": (positive_f1 + negative_f1) / 2.0,
            }
        )
    return result


def capture_class_weights(captures: np.ndarray, labels: np.ndarray) -> np.ndarray:
    capture_values = np.asarray(captures, dtype=object)
    y = np.asarray(labels, dtype=np.uint8)
    weights = np.zeros(len(y), dtype=np.float64)
    unique_captures = sorted(str(value) for value in np.unique(capture_values))
    for capture in unique_captures:
        capture_mask = capture_values == capture
        for label in (0, 1):
            mask = capture_mask & (y == label)
            count = int(np.count_nonzero(mask))
            if count:
                weights[mask] = 1.0 / (len(unique_captures) * 2.0 * count)
    if np.any(weights <= 0.0) or not np.isfinite(weights).all():
        raise StrictCrossMemberModelError("捕获等质量、捕获内类别平衡权重无效")
    weights *= len(weights) / weights.sum()
    return weights.astype(np.float32)


class ResidualNetwork(nn.Module):
    """固定 7→32→16→1 的受界残差专家。"""

    def __init__(self) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(7, 32), nn.ReLU(), nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1)
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        raw = self.layers(values).squeeze(-1)
        return DELTA_BOUND * torch.tanh(raw / DELTA_BOUND)


class ClassifierNetwork(nn.Module):
    """与残差单专家容量同阶的普通分类网络。"""

    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(7, 32), nn.ReLU(), nn.Linear(32, 16), nn.ReLU())
        self.head = nn.Linear(16, 1)

    def encode(self, values: torch.Tensor) -> torch.Tensor:
        return self.encoder(values)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.head(self.encode(values)).squeeze(-1)


class SelectiveNetwork(nn.Module):
    """具有真实预测头、选择头和辅助预测头的 SelectiveNet。"""

    def __init__(self) -> None:
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(7, 32), nn.ReLU(), nn.Linear(32, 16), nn.ReLU())
        self.prediction_head = nn.Linear(16, 1)
        self.selection_head = nn.Linear(16, 1)
        self.auxiliary_head = nn.Linear(16, 1)

    def forward(self, values: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        encoded = self.encoder(values)
        return (
            self.prediction_head(encoded).squeeze(-1),
            torch.sigmoid(self.selection_head(encoded).squeeze(-1)),
            self.auxiliary_head(encoded).squeeze(-1),
        )


class DomainClassifier(nn.Module):
    def __init__(self, domain_count: int) -> None:
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(16, 16), nn.ReLU(), nn.Linear(16, domain_count))

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.layers(values)


_GradientBase = torch.autograd.Function if torch is not None else object


class _GradientReverse(_GradientBase):
    @staticmethod
    def forward(ctx: Any, values: torch.Tensor, weight: float) -> torch.Tensor:
        ctx.weight = weight
        return values.view_as(values)

    @staticmethod
    def backward(ctx: Any, gradient: torch.Tensor) -> tuple[torch.Tensor, None]:
        return -ctx.weight * gradient, None


def _state_to_numpy(model: nn.Module) -> dict[str, np.ndarray]:
    return {name: tensor.detach().cpu().numpy() for name, tensor in model.state_dict().items()}


def _load_state(model: nn.Module, state: Mapping[str, np.ndarray]) -> nn.Module:
    model.load_state_dict(
        {name: torch.from_numpy(np.asarray(value)) for name, value in state.items()}
    )
    return model


def _batch_indices(length: int, batch_size: int, seed: int, epoch: int) -> list[np.ndarray]:
    order = np.random.default_rng(seed + epoch * 1009).permutation(length)
    return [order[start : start + batch_size] for start in range(0, length, batch_size)]


def _sample_capture_equal(
    pool: np.ndarray,
    captures: np.ndarray,
    limit: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if len(pool) <= limit:
        return pool.copy()
    capture_values = sorted(str(value) for value in np.unique(captures[pool]))
    selected = []
    shuffled_captures = rng.permutation(capture_values)
    while len(selected) < limit:
        progressed = False
        for capture in shuffled_captures:
            candidates = np.setdiff1d(
                pool[captures[pool] == capture], np.asarray(selected, dtype=np.int64)
            )
            if len(candidates):
                selected.append(int(rng.choice(candidates)))
                progressed = True
                if len(selected) == limit:
                    break
        if not progressed:
            break
    return np.asarray(selected, dtype=np.int64)


def _hard_negative_masks(
    labels: np.ndarray, members: np.ndarray, anchor: np.ndarray, visible: Sequence[str]
) -> dict[str, np.ndarray]:
    result: dict[str, np.ndarray] = {}
    for member in visible:
        negative = (members == member) & (labels == 0)
        if int(np.count_nonzero(negative)) < 5_000:
            raise StrictCrossMemberModelError(f"{member} 的 M1 负类支持不足")
        threshold = float(np.quantile(anchor[negative], 0.99))
        hard = negative & (anchor >= threshold)
        if int(np.count_nonzero(hard)) < 50:
            raise StrictCrossMemberModelError(f"{member} 的冻结 1% 锚带少于 50 个负类")
        result[member] = hard
    return result


def train_residual_expert(
    x: np.ndarray,
    y: np.ndarray,
    members: np.ndarray,
    captures: np.ndarray,
    anchor_score: np.ndarray,
    *,
    visible_members: Sequence[str],
    use_m1: bool,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    seed: int,
    device: torch.device,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    visible = tuple(visible_members)
    if not visible or any(member not in SOURCE_MEMBER_SET for member in visible):
        raise StrictCrossMemberModelError("残差专家只允许源成员 A、B、D")
    mask = np.isin(members, visible)
    values = np.asarray(x[mask], dtype=np.float32)
    labels = np.asarray(y[mask], dtype=np.float32)
    source_members = np.asarray(members[mask], dtype=object)
    source_captures = np.asarray(captures[mask], dtype=object)
    anchors = np.asarray(anchor_score[mask], dtype=np.float32)
    weights = capture_class_weights(source_captures, labels.astype(np.uint8))
    hard_masks = (
        _hard_negative_masks(labels, source_members, anchors, visible) if use_m1 else {}
    )
    set_seed(seed)
    model = ResidualNetwork().to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=learning_rate, weight_decay=weight_decay
    )
    pair_count = 0
    started = time.perf_counter()
    for epoch in range(epochs):
        model.train()
        for batch_number, indices in enumerate(
            _batch_indices(len(labels), batch_size, seed, epoch)
        ):
            batch_x = torch.from_numpy(values[indices]).to(device)
            batch_y = torch.from_numpy(labels[indices]).to(device)
            batch_anchor = torch.from_numpy(anchors[indices]).to(device)
            batch_weight = torch.from_numpy(weights[indices]).to(device)
            delta = model(batch_x)
            loss = functional.binary_cross_entropy_with_logits(
                batch_anchor + delta, batch_y, weight=batch_weight
            ) + 1e-3 * torch.mean(delta.square())
            if use_m1:
                rng = np.random.default_rng(seed + epoch * 10_007 + batch_number)
                per_member_limit = max(1, 64 // len(visible))
                rank_losses = []
                current_pairs = 0
                for member in visible:
                    positive_pool = np.flatnonzero((source_members == member) & (labels == 1))
                    negative_pool = np.flatnonzero(hard_masks[member])
                    positive_index = _sample_capture_equal(
                        positive_pool,
                        source_captures,
                        min(per_member_limit, len(positive_pool)),
                        rng,
                    )
                    negative_index = _sample_capture_equal(
                        negative_pool,
                        source_captures,
                        min(per_member_limit, len(negative_pool)),
                        rng,
                    )
                    positive_score = torch.from_numpy(anchors[positive_index]).to(device) + model(
                        torch.from_numpy(values[positive_index]).to(device)
                    )
                    negative_score = torch.from_numpy(anchors[negative_index]).to(device) + model(
                        torch.from_numpy(values[negative_index]).to(device)
                    )
                    pairs = positive_score[:, None] - negative_score[None, :]
                    current_pairs += pairs.numel()
                    rank_losses.append(functional.softplus(-pairs).mean())
                if current_pairs > 4096:
                    raise StrictCrossMemberModelError("M1 单批在线成对数超过 4096")
                pair_count += current_pairs
                loss = loss + torch.stack(rank_losses).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
    state = _state_to_numpy(model)
    model.eval()
    with torch.no_grad():
        delta_all = model(torch.from_numpy(values).to(device)).cpu().numpy()
    return state, {
        "visible_members": list(visible),
        "use_m1": use_m1,
        "epochs": epochs,
        "online_pair_count": pair_count,
        "maximum_pairs_per_batch": 4096,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "residual_saturation_rate": float(np.mean(np.abs(delta_all) > 0.95 * DELTA_BOUND)),
        "training_seconds": time.perf_counter() - started,
    }


def predict_residual(
    state: Mapping[str, np.ndarray], values: np.ndarray, device: torch.device
) -> np.ndarray:
    model = _load_state(ResidualNetwork(), state).to(device).eval()
    with torch.no_grad():
        result = model(torch.from_numpy(np.asarray(values, dtype=np.float32)).to(device))
    return result.cpu().numpy().astype(np.float64)


def _coral_loss(first: torch.Tensor, second: torch.Tensor) -> torch.Tensor:
    if first.shape[0] < 2 or second.shape[0] < 2:
        return first.new_zeros(())
    first_centered = first - first.mean(dim=0, keepdim=True)
    second_centered = second - second.mean(dim=0, keepdim=True)
    first_cov = first_centered.T @ first_centered / (first.shape[0] - 1)
    second_cov = second_centered.T @ second_centered / (second.shape[0] - 1)
    return torch.mean((first_cov - second_cov).square())


def train_classifier(
    x: np.ndarray,
    y: np.ndarray,
    members: np.ndarray,
    captures: np.ndarray,
    *,
    objective: str,
    objective_weight: float,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    weight_decay: float,
    seed: int,
    device: torch.device,
    selective_auxiliary_weight: float = 0.5,
    dann_schedule: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_members = tuple(sorted(str(value) for value in np.unique(members)))
    if not source_members or any(member not in SOURCE_MEMBER_SET for member in source_members):
        raise StrictCrossMemberModelError("神经基线只能看源成员，硬拒绝 C")
    if objective in {"coral", "dann", "groupdro", "vrex"} and len(source_members) < 2:
        raise StrictCrossMemberModelError(f"{objective} 至少需要两个源成员")
    set_seed(seed)
    selective = objective == "selective"
    model: nn.Module = SelectiveNetwork() if selective else ClassifierNetwork()
    model = model.to(device)
    domain_model = DomainClassifier(len(source_members)).to(device) if objective == "dann" else None
    parameters = list(model.parameters())
    if domain_model is not None:
        parameters.extend(domain_model.parameters())
    optimizer = torch.optim.AdamW(parameters, lr=learning_rate, weight_decay=weight_decay)
    values = np.asarray(x, dtype=np.float32)
    labels = np.asarray(y, dtype=np.float32)
    weights = capture_class_weights(captures, y)
    domain_lookup = {member: index for index, member in enumerate(source_members)}
    domains = np.asarray([domain_lookup[str(member)] for member in members], dtype=np.int64)
    group_weights = torch.ones(len(source_members), device=device) / len(source_members)
    started = time.perf_counter()
    for epoch in range(epochs):
        model.train()
        for batch_number, indices in enumerate(
            _batch_indices(len(labels), batch_size, seed, epoch)
        ):
            batch_x = torch.from_numpy(values[indices]).to(device)
            batch_y = torch.from_numpy(labels[indices]).to(device)
            batch_w = torch.from_numpy(weights[indices]).to(device)
            batch_domain = torch.from_numpy(domains[indices]).to(device)
            if selective:
                prediction, selection, auxiliary = model(batch_x)
                per_sample = functional.binary_cross_entropy_with_logits(
                    prediction, batch_y, reduction="none"
                )
                selective_risk = torch.sum(selection * per_sample) / torch.clamp(
                    selection.sum(), min=1e-6
                )
                coverage_penalty = torch.relu(0.75 - selection.mean()).square()
                auxiliary_loss = functional.binary_cross_entropy_with_logits(auxiliary, batch_y)
                loss = (
                    selective_risk
                    + 32.0 * coverage_penalty
                    + selective_auxiliary_weight * auxiliary_loss
                )
            else:
                encoded = model.encode(batch_x)
                logits = model.head(encoded).squeeze(-1)
                per_sample = functional.binary_cross_entropy_with_logits(
                    logits, batch_y, reduction="none"
                )
                if objective == "coral":
                    pair_losses = []
                    for left in range(len(source_members)):
                        for right in range(left + 1, len(source_members)):
                            pair_losses.append(
                                _coral_loss(
                                    encoded[batch_domain == left], encoded[batch_domain == right]
                                )
                            )
                    loss = torch.mean(per_sample * batch_w) + objective_weight * torch.stack(
                        pair_losses
                    ).mean()
                elif objective == "dann":
                    if domain_model is None:
                        raise StrictCrossMemberModelError("DANN 域分类器缺失")
                    progress = (epoch * math.ceil(len(labels) / batch_size) + batch_number) / max(
                        epochs * math.ceil(len(labels) / batch_size) - 1, 1
                    )
                    schedule = (
                        2.0 / (1.0 + math.exp(-10.0 * progress)) - 1.0
                        if dann_schedule
                        else 1.0
                    )
                    domain_logits = domain_model(
                        _GradientReverse.apply(encoded, objective_weight * schedule)
                    )
                    loss = torch.mean(per_sample * batch_w) + functional.cross_entropy(
                        domain_logits, batch_domain
                    )
                elif objective in {"groupdro", "vrex"}:
                    risks = torch.stack(
                        [
                            per_sample[batch_domain == group].mean()
                            for group in range(len(source_members))
                        ]
                    )
                    if objective == "groupdro":
                        with torch.no_grad():
                            group_weights *= torch.exp(objective_weight * risks.detach())
                            group_weights /= group_weights.sum()
                        loss = torch.sum(group_weights * risks)
                    else:
                        loss = risks.mean() + objective_weight * risks.var(unbiased=False)
                elif objective == "cvar":
                    tail_size = max(1, int(math.ceil(0.10 * len(per_sample))))
                    loss = torch.topk(per_sample, tail_size).values.mean()
                elif objective == "erm":
                    loss = torch.mean(per_sample * batch_w)
                else:
                    raise StrictCrossMemberModelError(f"未知神经目标：{objective}")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
    payload: dict[str, Any] = {"objective": objective, "model": _state_to_numpy(model)}
    if domain_model is not None:
        payload["domain_model"] = _state_to_numpy(domain_model)
    return payload, {
        "objective": objective,
        "objective_weight": objective_weight,
        "source_members": list(source_members),
        "target_member_seen": False,
        "epochs": epochs,
        "parameter_count": sum(parameter.numel() for parameter in parameters),
        "training_seconds": time.perf_counter() - started,
        "selective_has_prediction_selection_auxiliary_heads": selective,
        "dann_progressive_schedule": dann_schedule if objective == "dann" else None,
        "cvar_tail_fraction": 0.10 if objective == "cvar" else None,
        "group_definition": "source_member" if objective in {"groupdro", "vrex"} else None,
    }


def predict_classifier(
    payload: Mapping[str, Any], values: np.ndarray, device: torch.device
) -> tuple[np.ndarray, np.ndarray | None]:
    objective = str(payload["objective"])
    model: nn.Module = SelectiveNetwork() if objective == "selective" else ClassifierNetwork()
    model = _load_state(model, payload["model"]).to(device).eval()
    with torch.no_grad():
        tensor = torch.from_numpy(np.asarray(values, dtype=np.float32)).to(device)
        if objective == "selective":
            score, selection, _auxiliary = model(tensor)
            return (
                score.cpu().numpy().astype(np.float64),
                selection.cpu().numpy().astype(np.float64),
            )
        return model(tensor).cpu().numpy().astype(np.float64), None


def train_pairwise_linear(
    x: np.ndarray,
    y: np.ndarray,
    members: np.ndarray,
    *,
    c_value: float,
    epochs: int,
    seed: int,
    device: torch.device,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if any(str(member) not in SOURCE_MEMBER_SET for member in np.unique(members)):
        raise StrictCrossMemberModelError("线性部分AUC成对排名近似只能读取源成员")
    set_seed(seed)
    model = nn.Linear(7, 1).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1.0 / c_value)
    rng = np.random.default_rng(seed)
    pair_count = 0
    for _epoch in range(epochs):
        losses = []
        remaining = 4096
        for member in sorted(str(value) for value in np.unique(members)):
            positive = np.flatnonzero((members == member) & (y == 1))
            negative = np.flatnonzero((members == member) & (y == 0))
            with torch.no_grad():
                negative_scores = (
                    model(torch.from_numpy(np.asarray(x[negative], dtype=np.float32)).to(device))
                    .squeeze(-1)
                    .cpu()
                    .numpy()
                )
            threshold = np.quantile(negative_scores, 0.99)
            hard_negative = negative[negative_scores >= threshold]
            side = min(int(math.sqrt(max(remaining // max(len(np.unique(members)), 1), 1))), 64)
            selected_positive = rng.choice(positive, min(side, len(positive)), replace=False)
            selected_negative = rng.choice(
                hard_negative, min(side, len(hard_negative)), replace=False
            )
            positive_score = model(torch.from_numpy(x[selected_positive]).to(device)).squeeze(-1)
            negative_score = model(torch.from_numpy(x[selected_negative]).to(device)).squeeze(-1)
            pairs = positive_score[:, None] - negative_score[None, :]
            pair_count += pairs.numel()
            remaining -= pairs.numel()
            losses.append(functional.softplus(-pairs).mean())
        if remaining < 0:
            raise StrictCrossMemberModelError("线性成对排名单批超过 4096 对")
        loss = torch.stack(losses).mean()
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    return {
        "objective": "pairwise_pauc_0_01_approximation",
        "model": _state_to_numpy(model),
    }, {
        "display_name": PAIRWISE_DISPLAY_NAME,
        "implementation_fidelity": PAIRWISE_FIDELITY,
        "beta": 0.01,
        "c_value": c_value,
        "online_pair_count": pair_count,
        "maximum_pairs_per_batch": 4096,
    }


def predict_pairwise(
    payload: Mapping[str, Any], values: np.ndarray, device: torch.device
) -> np.ndarray:
    model = _load_state(nn.Linear(7, 1), payload["model"]).to(device).eval()
    with torch.no_grad():
        return (
            model(torch.from_numpy(np.asarray(values, dtype=np.float32)).to(device))
            .squeeze(-1)
            .cpu()
            .numpy()
            .astype(np.float64)
        )


def fit_xgboost(x: np.ndarray, y: np.ndarray, params: Mapping[str, Any], seed: int) -> Any:
    import xgboost as xgb

    model = xgb.XGBClassifier(
        n_estimators=int(params["n_estimators"]),
        max_depth=int(params["max_depth"]),
        min_child_weight=float(params["min_child_weight"]),
        learning_rate=float(params["learning_rate"]),
        subsample=float(params["subsample"]),
        colsample_bytree=float(params["colsample_bytree"]),
        reg_lambda=float(params["reg_lambda"]),
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        random_state=seed,
        n_jobs=int(params["n_jobs"]),
    )
    model.fit(x, y)
    return model


def fit_hist_gradient_boosting(
    x: np.ndarray, y: np.ndarray, params: Mapping[str, Any], seed: int
) -> HistGradientBoostingClassifier:
    model = HistGradientBoostingClassifier(
        max_iter=int(params["max_iter"]),
        max_leaf_nodes=int(params["max_leaf_nodes"]),
        l2_regularization=float(params["l2_regularization"]),
        learning_rate=float(params["learning_rate"]),
        random_state=seed,
    )
    model.fit(x, y)
    return model


def predict_tree_score(model: Any, values: np.ndarray) -> np.ndarray:
    probability = np.asarray(model.predict_proba(values)[:, 1], dtype=np.float64)
    if not np.isfinite(probability).all():
        raise StrictCrossMemberModelError("树模型概率含非有限值")
    return logit(probability)


def gate_from_experts(
    anchor_score: np.ndarray,
    expert_deltas: np.ndarray,
    *,
    global_gate: bool,
    kappa: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if expert_deltas.ndim != 2 or expert_deltas.shape[1] < 2:
        raise StrictCrossMemberModelError("M2 至少需要两个留一成员专家")
    mean_delta = expert_deltas.mean(axis=1)
    disagreement = np.sqrt(np.mean(np.square(expert_deltas - mean_delta[:, None]), axis=1))
    direction = np.abs(np.mean(np.sign(expert_deltas), axis=1))
    admission = global_gate & (disagreement <= kappa) & (direction == 1.0)
    score = np.asarray(anchor_score, dtype=np.float64).copy()
    score[admission] += mean_delta[admission]
    if not np.array_equal(score[~admission], np.asarray(anchor_score)[~admission]):
        raise StrictCrossMemberModelError("M2 关闭门的输出未逐元素精确等于强树锚")
    return score, admission, disagreement


def fit_m2_gate(
    member_labels: np.ndarray,
    labels: np.ndarray,
    anchor_score: np.ndarray,
    expert_deltas: np.ndarray,
    source_members: Sequence[str],
) -> dict[str, Any]:
    deltas: dict[str, float] = {}
    for index, member in enumerate(source_members):
        mask = member_labels == member
        anchor_risk = 1.0 - normalized_partial_auc(labels[mask], anchor_score[mask])
        expert_risk = 1.0 - normalized_partial_auc(
            labels[mask], anchor_score[mask] + expert_deltas[mask, index]
        )
        deltas[member] = expert_risk - anchor_risk
    member_count = len(source_members)
    lambda_min = -1.0 / member_count
    values = np.asarray(list(deltas.values()), dtype=np.float64)
    u_ext = (1.0 - member_count * lambda_min) * float(values.max()) + lambda_min * float(
        values.sum()
    )
    mean_delta = expert_deltas.mean(axis=1)
    disagreement = np.sqrt(np.mean(np.square(expert_deltas - mean_delta[:, None]), axis=1))
    kappa = float(np.quantile(disagreement, 0.75))
    global_gate = u_ext <= 0.005 and float(values.max()) <= 0.005
    return {
        "delta_e": deltas,
        "lambda_min": lambda_min,
        "u_ext": u_ext,
        "maximum_delta_e": float(values.max()),
        "u_ext_limit": 0.005,
        "maximum_delta_e_limit": 0.005,
        "kappa": kappa,
        "kappa_quantile": 0.75,
        "global_gate": global_gate,
    }


def deterministic_random_admission(
    uids: np.ndarray, capture_key: str, admission_count: int, seed: int
) -> np.ndarray:
    import hashlib

    if admission_count < 0 or admission_count > len(uids):
        raise StrictCrossMemberModelError("RND 准入数越界")
    hashes = np.asarray(
        [
            hashlib.sha256(
                f"tqhc2-rnd-v1|{seed}|{capture_key}|{str(uid)}".encode()
            ).digest()
            for uid in uids
        ],
        dtype="S32",
    )
    order = np.argsort(hashes, kind="stable")
    admission = np.zeros(len(uids), dtype=bool)
    admission[order[:admission_count]] = True
    return admission


def save_artifact(path: Path, artifact: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    joblib.dump(dict(artifact), partial, compress=3)
    os.replace(partial, path)


def load_artifact(path: Path) -> dict[str, Any]:
    value = joblib.load(path)
    if not isinstance(value, dict):
        raise StrictCrossMemberModelError("模型制品顶层必须是对象")
    return value
