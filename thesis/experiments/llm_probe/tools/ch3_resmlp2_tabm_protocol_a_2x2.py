# -*- coding: utf-8 -*-
"""ResMLP2 与 TabM4 的第三章协议 A 四格直接重跑入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any

try:
    import numpy as np
    from sklearn.metrics import average_precision_score, roc_auc_score
except ModuleNotFoundError:
    np = None
    average_precision_score = None
    roc_auc_score = None

try:
    import torch
    import torch.nn as nn
except ModuleNotFoundError:
    torch = None
    nn = None


SCHEMA_VERSION = "ch3-protocol-a-backbone-2x2-config-v1"
RESULT_SCHEMA_VERSION = "ch3-protocol-a-backbone-2x2-results-v1"
CELL_ORDER = ("C00", "C01", "C10", "C11")
CELLS = {
    "C00": {"causal_prefix_aggregation": False, "learned_lp_pooling": False},
    "C01": {"causal_prefix_aggregation": False, "learned_lp_pooling": True},
    "C10": {"causal_prefix_aggregation": True, "learned_lp_pooling": False},
    "C11": {"causal_prefix_aggregation": True, "learned_lp_pooling": True},
}
RUN_IDS = {
    "resmlp2": "ch3-resmlp2-cpa-elp-protocol-a-2x2-seed42-v1",
    "tabm4": "ch3-tabm4-cpa-elp-protocol-a-2x2-seed42-v1",
}
PARAMETER_COUNTS = {"resmlp2": 89_796, "tabm4": 90_175}
DR_FPR_GRID = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)
SOURCE_ARRAYS = ("X23", "y23", "I23", "M23", "E23", "T23")
TARGET_ARRAYS = ("X24", "y24", "I24", "M24", "s24", "d24", "t24")
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def data_inventory(cache_root: Path, names: tuple[str, ...]) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for name in names:
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少冻结缓存：{path}")
        stat = path.stat()
        files.append(
            {
                "name": path.name,
                "bytes": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    return {
        "schema_version": "ch3-protocol-a-data-inventory-v1",
        "cache_root": str(cache_root),
        "files": files,
        "sha256": canonical_sha256(files),
    }


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def atomic_torch(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    torch.save(value, temporary)
    os.replace(temporary, path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def write_status(
    output_root: Path,
    state: str,
    stage: str,
    exit_code: int | None,
    detail: str,
) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-protocol-a-backbone-2x2-status-v1",
            "state": state,
            "stage": stage,
            "exit_code": exit_code,
            "detail": detail,
            "updated_at_unix": time.time(),
            "target_previously_accessed": True,
            "independent_test": False,
        },
    )


def process_peak_rss_mib() -> float:
    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak / 1024.0 if sys.platform != "darwin" else peak / (1024.0 * 1024.0)


def resmlp2_parameter_count(feature_count: int, hidden_size: int) -> int:
    input_projection = feature_count * hidden_size + hidden_size
    residual_block = 2 * hidden_size * hidden_size + 4 * hidden_size
    fusion = 2 * hidden_size * hidden_size + hidden_size
    output_and_p = hidden_size + 2
    return input_projection + residual_block + fusion + output_and_p


def tabm4_parameter_count(feature_count: int, hidden_size: int, members: int) -> int:
    return (
        2 * hidden_size * hidden_size
        + feature_count * hidden_size
        + members * (feature_count + 1 + 7 * hidden_size)
        + 1
    )


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置模式版本不符")
    model_key = config.get("model_key")
    if model_key not in RUN_IDS or config.get("run_id") != RUN_IDS[model_key]:
        raise ValueError("模型或运行身份不符")
    if config.get("cells") != CELLS:
        raise ValueError("必须严格运行协议 A 四格")
    if config.get("source_arrays") != list(SOURCE_ARRAYS):
        raise ValueError("源年数组合同不符")
    if config.get("target_arrays") != list(TARGET_ARRAYS):
        raise ValueError("目标年数组合同不符")
    training = config.get("training")
    expected_training = {
        "seed": 42,
        "sequence_length": 128,
        "batch_size": 64,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "learning_rate": 0.002,
        "weight_decay": 0.01,
        "dropout": 0.1,
        "gradient_clip_norm": 1.0,
        "auxiliary_loss_weight": 1.0,
        "validation_fraction": 0.1,
        "time_tail_fraction": 0.15,
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_rule": "single_epoch_argmax_earliest_tie_no_early_stopping",
    }
    if training != expected_training:
        raise ValueError("协议 A 训练与选择合同不符")
    evaluation = config.get("evaluation")
    if evaluation != {
        "target_year": "LSPR24",
        "target_previously_accessed": True,
        "independent_test": False,
        "target_load_after_all_selections_sealed": True,
        "target_evaluation_calls": 4,
        "flow_average_precision": True,
        "entity_average_precision": True,
        "maximum_entity_average_precision": True,
        "dr_fpr_grid": list(DR_FPR_GRID),
        "complete_reachable_alert_budget_curve": True,
    }:
        raise ValueError("目标评价合同不符")
    artifacts = config.get("artifact_policy")
    if artifacts != {
        "persist_selected_checkpoint_per_cell": True,
        "persist_inflight_epoch_checkpoint": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_complete_budget_curve_aggregate": True,
    }:
        raise ValueError("制品合同不符")
    if config.get("formal_paper_evidence") or config.get("independent_test"):
        raise ValueError("本次重跑不能宣称正式论文证据或独立测试")
    candidate = config.get("candidate")
    if model_key == "resmlp2":
        expected = {
            "hidden_size": 139,
            "residual_blocks": 1,
            "residual_affine_layers": 2,
            "pre_normalization": True,
            "activation": "relu",
            "parameter_formula": "4d^2+90d+2",
            "parameter_count": 89_796,
        }
        actual = resmlp2_parameter_count(83, 139)
    else:
        expected = {
            "hidden_size": 186,
            "ensemble_members": 4,
            "member_batch_sequences": 16,
            "member_probability_reduction": "arithmetic_mean",
            "elp_exponent": "shared_scalar",
            "activation": "relu",
            "parameter_formula": "2d^2+83d+k(84+7d)+1",
            "parameter_count": 90_175,
        }
        actual = tabm4_parameter_count(83, 186, 4)
    if candidate != expected or actual != PARAMETER_COUNTS[model_key]:
        raise ValueError("骨干结构或参数量不是冻结值")
    paths = config.get("paths", {})
    if Path(paths.get("output_root", "")).name != RUN_IDS[model_key]:
        raise ValueError("输出目录与运行身份不一致")
    if config.get("swanlab", {}).get("group") != RUN_IDS[model_key]:
        raise ValueError("SwanLab 分组与运行身份不一致")
    if config.get("resource_contract") != {
        "observed_tabm_single_job_peak_gpu_memory_mib": 8244,
        "minimum_free_gpu_memory_mib": 8244,
        "minimum_cgroup_available_memory_gib": 40,
        "minimum_free_disk_gib": 10,
        "maximum_parallel_jobs": 2,
        "maximum_parallel_cells_per_job": 1,
        "resource_sample_interval_seconds": 5,
        "concurrent_resource_measurement_is_fair_efficiency_evidence": False,
        "oom_fallback": "run_same_two_commands_serially",
    }:
        raise ValueError("资源与并发合同不符")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ResMLP2 与 TabM4 协议 A 四格重跑")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument("--validate-config", action="store_true", help="只核验配置")
    parser.add_argument("--resume", action="store_true", help="恢复同身份在途检查点")
    parser.add_argument("--publish-only", action="store_true", help="仅发布已有聚合指标")
    parser.add_argument("--resource-receipt", help="启动器资源准入收据")
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    return parser.parse_args()


if nn is not None:
    class PreNormFullWidthResidualBlock(nn.Module):
        """一个预归一化残差块，内部包含两个全宽仿射层。"""

        def __init__(self, hidden_size: int, dropout: float):
            super().__init__()
            self.normalization = nn.LayerNorm(hidden_size)
            self.linear1 = nn.Linear(hidden_size, hidden_size)
            self.linear2 = nn.Linear(hidden_size, hidden_size)
            self.activation = nn.ReLU()
            self.dropout1 = nn.Dropout(dropout)
            self.dropout2 = nn.Dropout(dropout)

        def forward(self, values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
            residual = self.normalization(values)
            residual = self.dropout1(self.activation(self.linear1(residual)))
            residual = self.dropout2(self.linear2(residual))
            return (values + residual) * mask.unsqueeze(-1)


    class ResMLP2Backbone(nn.Module):
        def __init__(self, feature_count: int, hidden_size: int, dropout: float, aggregate: bool):
            super().__init__()
            self.aggregate = aggregate
            self.input_projection = nn.Linear(feature_count, hidden_size)
            self.residual = PreNormFullWidthResidualBlock(hidden_size, dropout)
            self.fusion = nn.Sequential(
                nn.Linear(hidden_size * 2, hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout),
            )
            self.output = nn.Linear(hidden_size, 1)
            self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

        @property
        def p(self) -> torch.Tensor:
            return torch.exp(self.p_log).clamp(1e-3, 1e3)

        def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
            mask = valid.to(values.dtype)
            hidden = self.input_projection(values) * mask.unsqueeze(-1)
            hidden = self.residual(hidden, mask)
            if self.aggregate:
                context = torch.cumsum(hidden, 1) / torch.cumsum(mask, 1).clamp(min=1.0).unsqueeze(-1)
                context = context * mask.unsqueeze(-1)
            else:
                context = torch.zeros_like(hidden)
            return self.output(self.fusion(torch.cat((hidden, context), dim=-1))).squeeze(-1)


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
            return projected * self.s.unsqueeze(0).unsqueeze(2) + self.bias.unsqueeze(0).unsqueeze(2)


    class TabM4Backbone(nn.Module):
        def __init__(self, feature_count: int, hidden_size: int, members: int, dropout: float, aggregate: bool):
            super().__init__()
            self.members = members
            self.aggregate = aggregate
            self.input_layer = LinearBatchEnsemble(feature_count, hidden_size, members, True)
            self.fusion_layer = LinearBatchEnsemble(hidden_size * 2, hidden_size, members, False)
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
                raise RuntimeError("TabM4 训练输入必须是 N×4×T×F")
            mask = valid.to(values.dtype)
            hidden = self.dropout(self.activation(self.input_layer(values))) * mask.unsqueeze(-1)
            if self.aggregate:
                context = torch.cumsum(hidden, 2) / torch.cumsum(mask, 2).clamp(min=1.0).unsqueeze(-1)
                context = context * mask.unsqueeze(-1)
            else:
                context = torch.zeros_like(hidden)
            fused = self.dropout(self.activation(self.fusion_layer(torch.cat((hidden, context), dim=-1))))
            fused = fused * mask.unsqueeze(-1)
            return (fused * self.output_weight.unsqueeze(0).unsqueeze(2)).sum(-1) + self.output_bias.unsqueeze(0).unsqueeze(2)

        def mean_member_probability(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
            expanded_values = values.unsqueeze(1).expand(-1, self.members, -1, -1)
            expanded_valid = valid.unsqueeze(1).expand(-1, self.members, -1)
            return torch.sigmoid(self.forward(expanded_values, expanded_valid)).mean(1)
else:
    class ResMLP2Backbone:
        pass


    class TabM4Backbone:
        pass


def build_model(config: dict[str, Any], cell: str) -> Any:
    if torch is None or nn is None:
        raise RuntimeError("正式计算缺少 PyTorch GPU 依赖")
    aggregate = config["cells"][cell]["causal_prefix_aggregation"]
    candidate = config["candidate"]
    if config["model_key"] == "resmlp2":
        model = ResMLP2Backbone(83, candidate["hidden_size"], config["training"]["dropout"], aggregate)
    else:
        model = TabM4Backbone(83, candidate["hidden_size"], candidate["ensemble_members"], config["training"]["dropout"], aggregate)
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != candidate["parameter_count"]:
        raise RuntimeError(f"模型参数量不符：{actual}")
    return model


def lp_pool(scores: torch.Tensor, valid: torch.Tensor, p_value: torch.Tensor) -> torch.Tensor:
    log_scores = torch.log(scores.clamp(min=1e-7))
    count = valid.sum(1).clamp(min=1.0)
    summed = torch.logsumexp((p_value * log_scores).masked_fill(valid < 0.5, -1e30), 1)
    return torch.exp((summed - torch.log(count)) / p_value)


def move_optimizer_state(optimizer: torch.optim.Optimizer, device: torch.device) -> None:
    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                state[key] = value.to(device)


def make_optimizer(config: dict[str, Any], model: Any) -> torch.optim.Optimizer:
    if config["model_key"] == "tabm4":
        decay_names = {"input_layer.weight", "fusion_layer.weight", "output_weight"}
        decay = [parameter for name, parameter in model.named_parameters() if name in decay_names]
        no_decay = [parameter for name, parameter in model.named_parameters() if name not in decay_names]
    else:
        decay = [parameter for name, parameter in model.named_parameters() if not (name.endswith(".bias") or name == "p_log")]
        no_decay = [parameter for name, parameter in model.named_parameters() if name.endswith(".bias") or name == "p_log"]
    return torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": config["training"]["weight_decay"]},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=config["training"]["learning_rate"],
    )


def sample_distinct_positions(size: int, count: int, generator: torch.Generator) -> torch.Tensor:
    positions: list[int] = []
    seen: set[int] = set()
    while len(positions) < count:
        candidates = torch.randint(0, size, ((count - len(positions)) * 2,), generator=generator).tolist()
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                positions.append(candidate)
                if len(positions) == count:
                    break
    return torch.tensor(positions, dtype=torch.int64)


@torch.no_grad() if torch is not None else (lambda function: function)
def predict_sequences(
    config: dict[str, Any],
    model: Any,
    rows: np.ndarray,
    gX: torch.Tensor,
    gy: torch.Tensor,
    gI: torch.Tensor,
    gM: torch.Tensor,
    batch_size: int = 2048,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    model.eval()
    predictions: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    flow_ids: list[np.ndarray] = []
    length = config["training"]["sequence_length"]
    for start in range(0, len(rows), batch_size):
        selected = torch.from_numpy(rows[start : start + batch_size]).to(gX.device)
        indices = gI[selected][:, :length]
        valid = gM[selected][:, :length] > 0.5
        batch = indices.shape[0]
        values = gX[indices.reshape(-1)].reshape(batch, length, gX.shape[1])
        if config["model_key"] == "tabm4":
            probabilities = model.mean_member_probability(values, valid)
        else:
            probabilities = torch.sigmoid(model(values, valid))
        mask = valid.reshape(-1)
        predictions.append(probabilities.reshape(-1)[mask].float().cpu().numpy())
        labels.append(gy[indices.reshape(-1)].reshape(-1)[mask].float().cpu().numpy())
        flow_ids.append(indices.reshape(-1)[mask].cpu().numpy())
    model.train()
    return np.concatenate(predictions), np.concatenate(labels), np.concatenate(flow_ids)


def train_cell(
    config: dict[str, Any],
    cell: str,
    output_root: Path,
    run_identity: dict[str, Any],
    source: dict[str, np.ndarray],
    train_rows: np.ndarray,
    validation_rows: np.ndarray,
    device: torch.device,
    resume: bool,
) -> dict[str, Any]:
    checkpoint_path = output_root / "checkpoints" / f"selected-{cell}.pt"
    receipt_path = output_root / "receipts" / f"selection-{cell}.json"
    inflight_path = output_root / "inflight" / f"{cell}.pt"
    identity = {
        "schema_version": "ch3-protocol-a-cell-identity-v1",
        "run_id": config["run_id"],
        "model_key": config["model_key"],
        "cell": cell,
        **run_identity,
    }
    if checkpoint_path.is_file() and receipt_path.is_file():
        receipt = load_json(receipt_path)
        if not resume or receipt.get("identity") != identity or receipt.get("checkpoint", {}).get("sha256") != sha256_file(checkpoint_path):
            raise RuntimeError(f"{cell} 已有检查点但不可合法复用")
        log(f"{cell} 复用已封印检查点")
        return receipt["selection"]
    if not resume and (checkpoint_path.exists() or receipt_path.exists() or inflight_path.exists()):
        raise RuntimeError(f"全新运行存在 {cell} 历史制品")

    training = config["training"]
    torch.manual_seed(training["seed"])
    torch.cuda.manual_seed_all(training["seed"])
    np.random.seed(training["seed"])
    model = build_model(config, cell).to(device)
    optimizer = make_optimizer(config, model)
    generator = torch.Generator().manual_seed(training["seed"])
    history: list[dict[str, Any]] = []
    best_ap = -1.0
    best_epoch = 0
    best_p = float("nan")
    best_state: dict[str, torch.Tensor] | None = None
    elapsed_before = 0.0
    start_epoch = 1
    if resume and inflight_path.is_file():
        inflight = torch.load(inflight_path, map_location="cpu", weights_only=False)
        if inflight.get("identity") != identity:
            raise RuntimeError(f"{cell} 在途检查点身份不符")
        model.load_state_dict(inflight["model"])
        optimizer.load_state_dict(inflight["optimizer"])
        move_optimizer_state(optimizer, device)
        history = inflight["history"]
        best_ap = float(inflight["best_ap"])
        best_epoch = int(inflight["best_epoch"])
        best_p = float(inflight["best_p"])
        best_state = inflight["best_state"]
        elapsed_before = float(inflight["elapsed_seconds"])
        generator.set_state(inflight["generator_state"])
        torch.set_rng_state(inflight["torch_rng_state"])
        torch.cuda.set_rng_state_all(inflight["cuda_rng_state_all"])
        np.random.set_state(inflight["numpy_rng_state"])
        start_epoch = int(inflight["epoch"]) + 1

    X = source["X23"]
    y = source["y23"]
    I = source["I23"]
    M = source["M23"]
    gX = torch.from_numpy(X).to(device)
    gy = torch.from_numpy(y).to(device)
    gI = torch.from_numpy(I).to(device)
    gM = torch.from_numpy(M).to(device)
    sequence_labels = (y[I.reshape(-1)].reshape(I.shape) * M).max(1) > 0
    sequence_positive_weight = float((1 - sequence_labels.mean()) / max(sequence_labels.mean(), 1e-8))
    positive_weight = torch.tensor([(1 - y.mean()) / y.mean()], device=device)
    flow_loss = nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    sequence_loss = nn.BCELoss(reduction="none")
    uses_lp = config["cells"][cell]["learned_lp_pooling"]
    length = training["sequence_length"]
    torch.cuda.reset_peak_memory_stats(device)
    started = time.time()
    model.train()
    for epoch in range(start_epoch, training["epochs"] + 1):
        running_loss = 0.0
        for step in range(1, training["steps_per_epoch"] + 1):
            if config["model_key"] == "tabm4":
                positions = sample_distinct_positions(len(train_rows), training["batch_size"], generator)
                selected_rows = torch.from_numpy(train_rows[positions.numpy()]).reshape(16, 4).to(device)
                indices = gI[selected_rows][:, :, :length]
                valid = gM[selected_rows][:, :, :length] > 0.5
                values = gX[indices.reshape(-1)].reshape(16, 4, length, gX.shape[1])
                labels = gy[indices.reshape(-1)].reshape(indices.shape)
                logits = model(values, valid)
                mask = valid.to(logits.dtype)
                auxiliary_scores = torch.sigmoid(logits).reshape(-1, length)
                auxiliary_mask = mask.reshape(-1, length)
                auxiliary_labels = (labels * mask).amax(-1).reshape(-1)
            else:
                positions = torch.randint(0, len(train_rows), (training["batch_size"],), generator=generator)
                selected_rows = torch.from_numpy(train_rows[positions.numpy()]).to(device)
                indices = gI[selected_rows][:, :length]
                valid = gM[selected_rows][:, :length] > 0.5
                values = gX[indices.reshape(-1)].reshape(training["batch_size"], length, gX.shape[1])
                labels = gy[indices.reshape(-1)].reshape(indices.shape)
                logits = model(values, valid)
                mask = valid.to(logits.dtype)
                auxiliary_scores = torch.sigmoid(logits)
                auxiliary_mask = mask
                auxiliary_labels = (labels * mask).amax(-1)
            loss = (flow_loss(logits, labels) * mask).sum() / mask.sum().clamp(min=1.0)
            if uses_lp:
                pooled = lp_pool(auxiliary_scores, auxiliary_mask, model.p).clamp(1e-6, 1 - 1e-6)
                weights = 1.0 + (sequence_positive_weight - 1.0) * auxiliary_labels
                loss = loss + training["auxiliary_loss_weight"] * ((sequence_loss(pooled, auxiliary_labels) * weights).sum() / weights.sum())
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), training["gradient_clip_norm"])
            optimizer.step()
            running_loss += float(loss.detach())
            if step % 250 == 0:
                elapsed = elapsed_before + time.time() - started
                completed = (epoch - 1) * training["steps_per_epoch"] + step
                total = training["epochs"] * training["steps_per_epoch"]
                eta = elapsed * max(total - completed, 0) / max(completed, 1)
                log(f"{cell} 心跳 epoch={epoch}/{training['epochs']} step={step}/{training['steps_per_epoch']} 累计={elapsed/60:.1f}分 预计剩余={eta/60:.1f}分")
        predictions, labels_np, _ = predict_sequences(config, model, validation_rows, gX, gy, gI, gM)
        validation_ap = float(average_precision_score(labels_np, predictions))
        p_value = float(model.p.detach())
        history.append(
            {
                "epoch": epoch,
                "validation_flow_ap": validation_ap,
                "p": p_value,
                "mean_training_loss": running_loss / training["steps_per_epoch"],
            }
        )
        if validation_ap > best_ap:
            best_ap = validation_ap
            best_epoch = epoch
            best_p = p_value
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
        elapsed = elapsed_before + time.time() - started
        atomic_torch(
            inflight_path,
            {
                "identity": identity,
                "epoch": epoch,
                "model": {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()},
                "optimizer": optimizer.state_dict(),
                "history": history,
                "best_ap": best_ap,
                "best_epoch": best_epoch,
                "best_p": best_p,
                "current_p": float(model.p.detach()),
                "best_state": best_state,
                "elapsed_seconds": elapsed,
                "generator_state": generator.get_state(),
                "torch_rng_state": torch.get_rng_state(),
                "cuda_rng_state_all": torch.cuda.get_rng_state_all(),
                "numpy_rng_state": np.random.get_state(),
            },
        )
        log(f"{cell} epoch={epoch}/{training['epochs']} 验证逐流AP={validation_ap:.8f} p={p_value:.6f}")
    if best_state is None:
        raise RuntimeError(f"{cell} 未产生可选检查点")
    training_seconds = elapsed_before + time.time() - started
    atomic_torch(
        checkpoint_path,
        {
            "schema_version": "ch3-protocol-a-selected-checkpoint-v1",
            "identity": identity,
            "model": best_state,
        },
    )
    selection = {
        "selected_epoch": best_epoch,
        "validation_flow_ap": best_ap,
        "p_at_selection": best_p,
        "history": history,
        "training_seconds": training_seconds,
        "checkpoint": {
            "filename": str(checkpoint_path.relative_to(output_root)),
            "bytes": checkpoint_path.stat().st_size,
            "sha256": sha256_file(checkpoint_path),
        },
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_process_rss_mib": process_peak_rss_mib(),
    }
    atomic_json(receipt_path, {"identity": identity, "selection": selection, "checkpoint": selection["checkpoint"]})
    inflight_path.unlink(missing_ok=True)
    del model, optimizer, gX, gy, gI, gM
    torch.cuda.empty_cache()
    return selection


def entity_scores(
    flow_scores: np.ndarray,
    seen: np.ndarray,
    flow_entity: np.ndarray,
    entity_count: int,
    p_value: float | None,
) -> np.ndarray:
    if p_value is None:
        scores = np.full(entity_count, -np.inf, dtype=np.float32)
        np.maximum.at(scores, flow_entity[seen], flow_scores[seen])
        return scores
    numerator = np.zeros(entity_count, dtype=np.float64)
    count = np.zeros(entity_count, dtype=np.float64)
    np.add.at(numerator, flow_entity[seen], np.clip(flow_scores[seen], 1e-7, 1.0).astype(np.float64) ** p_value)
    np.add.at(count, flow_entity[seen], 1.0)
    return np.where(count > 0, (numerator / np.maximum(count, 1.0)) ** (1.0 / p_value), -np.inf).astype(np.float32)


def dr_at_fpr(scores: np.ndarray, labels: np.ndarray, target_fpr: float) -> float:
    valid = np.isfinite(scores)
    values = scores[valid]
    target = labels[valid]
    negative = np.sort(values[target == 0])[::-1]
    positive = values[target == 1]
    if len(negative) == 0 or len(positive) == 0:
        raise RuntimeError("检测率计算缺少正类或负类实体")
    threshold = negative[min(int(len(negative) * target_fpr), len(negative) - 1)]
    return float((positive >= threshold).mean())


def complete_budget_curve(scores: np.ndarray, labels: np.ndarray) -> dict[str, np.ndarray]:
    valid = np.isfinite(scores)
    values = scores[valid]
    target = labels[valid]
    positive = np.sort(values[target == 1])
    negative = np.sort(values[target == 0])[::-1]
    detection_rate = (len(positive) - np.searchsorted(positive, negative, side="left")) / len(positive)
    false_positive = len(negative) - np.searchsorted(negative[::-1], negative, side="left")
    return {
        "n_false_positive_entity": false_positive.astype(np.int64),
        "nominal_fpr": np.arange(len(negative), dtype=np.float64) / len(negative),
        "realized_fpr": false_positive.astype(np.float64) / len(negative),
        "detection_rate": detection_rate.astype(np.float64),
    }


def save_target_evaluation(
    output_root: Path,
    cell: str,
    identity: dict[str, Any],
    cell_result: dict[str, Any],
    curve: dict[str, np.ndarray],
) -> None:
    receipt_root = output_root / "receipts" / f"target-evaluation-{cell}"
    if receipt_root.exists():
        raise RuntimeError(f"{cell} 目标评价完成目录已存在，拒绝覆盖")
    temporary_root = receipt_root.with_name(f"{receipt_root.name}.partial.{os.getpid()}")
    temporary_root.mkdir(parents=True, exist_ok=False)
    curve_path = temporary_root / "complete-alert-budget-curve.npz"
    with curve_path.open("wb") as handle:
        np.savez_compressed(handle, **curve)
    atomic_json(
        temporary_root / "receipt.json",
        {
            "schema_version": "ch3-protocol-a-target-cell-receipt-v1",
            "identity": identity,
            "cell_result": cell_result,
            "curve": {
                "filename": curve_path.name,
                "bytes": curve_path.stat().st_size,
                "sha256": sha256_file(curve_path),
                "fields": list(curve),
            },
            "complete": True,
        },
    )
    os.replace(temporary_root, receipt_root)


def load_target_evaluation(
    output_root: Path,
    cell: str,
    identity: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, np.ndarray]] | None:
    receipt_root = output_root / "receipts" / f"target-evaluation-{cell}"
    if not receipt_root.exists():
        return None
    if not receipt_root.is_dir():
        raise RuntimeError(f"{cell} 目标评价收据路径类型不符")
    receipt_path = receipt_root / "receipt.json"
    curve_path = receipt_root / "complete-alert-budget-curve.npz"
    if not receipt_path.is_file() or not curve_path.is_file():
        raise RuntimeError(f"{cell} 目标评价只有部分写入，拒绝伪装完成")
    receipt = load_json(receipt_path)
    if (
        receipt.get("identity") != identity
        or receipt.get("complete") is not True
        or receipt.get("curve", {}).get("sha256") != sha256_file(curve_path)
    ):
        raise RuntimeError(f"{cell} 目标评价收据身份或摘要不符")
    with np.load(curve_path, allow_pickle=False) as payload:
        curve = {name: payload[name] for name in payload.files}
    if set(curve) != {
        "n_false_positive_entity",
        "nominal_fpr",
        "realized_fpr",
        "detection_rate",
    }:
        raise RuntimeError(f"{cell} 目标评价预算曲线字段不完整")
    return receipt["cell_result"], curve


def load_arrays(cache_root: Path, names: tuple[str, ...]) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for name in names:
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少冻结缓存：{path}")
        arrays[name] = np.load(path, allow_pickle=name in {"s24", "d24"})
    return arrays


def source_split(source: dict[str, np.ndarray], config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    seed = config["training"]["seed"]
    entity = source["E23"]
    timestamp = source["T23"]
    unique_entity = np.unique(entity)
    permutation = np.random.RandomState(seed).permutation(len(unique_entity))
    count = max(1, int(len(unique_entity) * config["training"]["validation_fraction"]))
    validation_entities = set(unique_entity[permutation[:count]].tolist())
    entity_mask = np.fromiter((value in validation_entities for value in entity), bool, len(entity))
    time_cut = np.quantile(timestamp, 1.0 - config["training"]["time_tail_fraction"])
    time_mask = timestamp >= time_cut
    train_rows = np.flatnonzero(~(entity_mask | time_mask))
    validation_rows = np.flatnonzero(entity_mask & ~time_mask)
    stats = {
        "entity_count": int(len(unique_entity)),
        "train_sequences": int(len(train_rows)),
        "validation_sequences": int(len(validation_rows)),
        "train_validation_row_intersection": int(np.intersect1d(train_rows, validation_rows).size),
    }
    if stats != {
        "entity_count": 150_680,
        "train_sequences": 208_598,
        "validation_sequences": 22_444,
        "train_validation_row_intersection": 0,
    }:
        raise RuntimeError(f"协议 A 源年切分统计不符：{stats}")
    return train_rows, validation_rows, stats


@torch.no_grad() if torch is not None else (lambda function: function)
def score_target(
    config: dict[str, Any],
    model: Any,
    target: dict[str, np.ndarray],
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    X = target["X24"]
    I = target["I24"]
    M = target["M24"]
    gX = torch.from_numpy(X).to(device)
    gI = torch.from_numpy(I).to(device)
    gM = torch.from_numpy(M).to(device)
    scores = torch.zeros(len(target["y24"]), device=device)
    seen = torch.zeros(len(target["y24"]), dtype=torch.bool, device=device)
    length = config["training"]["sequence_length"]
    model.eval()
    for start in range(0, len(I), 2048):
        indices = gI[start : start + 2048][:, :length]
        valid = gM[start : start + 2048][:, :length] > 0.5
        batch = indices.shape[0]
        values = gX[indices.reshape(-1)].reshape(batch, length, gX.shape[1])
        if config["model_key"] == "tabm4":
            probabilities = model.mean_member_probability(values, valid)
        else:
            probabilities = torch.sigmoid(model(values, valid))
        flow_ids = indices.reshape(-1)
        mask = valid.reshape(-1)
        scores[flow_ids[mask]] = probabilities.reshape(-1)[mask]
        seen[flow_ids[mask]] = True
    result = scores.cpu().numpy(), seen.cpu().numpy()
    del gX, gI, gM, scores, seen
    torch.cuda.empty_cache()
    return result


def build_manifest(output_root: Path, run_id: str) -> None:
    names = (
        "config.json",
        "selection_frozen.json",
        "aggregate-results.json",
        "complete-alert-budget-curves.npz",
        "complete-alert-budget-curves-receipt.json",
        "resource-receipt.json",
        "swanlab-receipt.json",
        "status.json",
    )
    files: dict[str, Any] = {}
    for name in names:
        path = output_root / name
        if path.is_file():
            files[name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    for cell in CELL_ORDER:
        for relative in (
            f"checkpoints/selected-{cell}.pt",
            f"receipts/selection-{cell}.json",
            f"receipts/target-evaluation-{cell}/receipt.json",
            f"receipts/target-evaluation-{cell}/complete-alert-budget-curve.npz",
        ):
            path = output_root / relative
            if path.is_file():
                files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-protocol-a-backbone-2x2-manifest-v1",
            "run_id": run_id,
            "files": files,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "complete_budget_curve_persisted": "complete-alert-budget-curves.npz" in files,
        },
    )


def run_experiment(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    if (
        np is None
        or average_precision_score is None
        or roc_auc_score is None
        or torch is None
        or nn is None
        or not torch.cuda.is_available()
    ):
        raise RuntimeError("协议 A 四格真实重跑要求完整 GPU 可选依赖与可用 CUDA")
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    config_sha = sha256_file(config_path)
    code_sha = sha256_file(Path(__file__).resolve())
    cache_root = Path(config["paths"]["cache_root"])
    source_inventory = data_inventory(cache_root, SOURCE_ARRAYS)
    run_identity = {
        "config_sha256": config_sha,
        "code_sha256": code_sha,
        "source_data_inventory_sha256": source_inventory["sha256"],
    }
    frozen_config_path = output_root / "config.json"
    if frozen_config_path.is_file():
        if not args.resume or load_json(frozen_config_path) != config:
            raise RuntimeError("输出根已有不兼容冻结配置")
    else:
        atomic_json(frozen_config_path, config)
    write_status(output_root, "running", "source-selection", None, "只加载 LSPR23 并冻结四格选择")
    selection_path = output_root / "selection_frozen.json"
    selections: dict[str, Any]
    split_stats: dict[str, int]
    if selection_path.is_file():
        if not args.resume:
            raise RuntimeError("全新运行已存在选择封印")
        seal = load_json(selection_path)
        if seal.get("identity") != run_identity or set(seal.get("cells", {})) != set(CELL_ORDER):
            raise RuntimeError("选择封印身份不符")
        selections = seal["cells"]
        split_stats = seal["source_split"]
    else:
        source = load_arrays(cache_root, SOURCE_ARRAYS)
        if source["X23"].shape != (16_353_511, 83) or source["I23"].shape != (271_815, 128):
            raise RuntimeError("LSPR23 冻结缓存形状不符")
        train_rows, validation_rows, split_stats = source_split(source, config)
        device = torch.device("cuda")
        selections = {}
        for cell in CELL_ORDER:
            log(f"开始 {cell} 协议 A 训练与选择")
            selections[cell] = train_cell(
                config,
                cell,
                output_root,
                run_identity,
                source,
                train_rows,
                validation_rows,
                device,
                args.resume,
            )
        seal = {
            "schema_version": "ch3-protocol-a-selection-frozen-v1",
            "run_id": config["run_id"],
            "config_sha256": config_sha,
            "identity": run_identity,
            "source_data_inventory": source_inventory,
            "protocol": "LSPR23实体不相交验证逐流AP最早最大轮次，20轮跑满且不早停",
            "source_split": split_stats,
            "cells": selections,
            "all_four_cells_sealed": True,
            "target_arrays_loaded_before_seal": 0,
            "sealed_at_unix": time.time(),
        }
        atomic_json(selection_path, seal)
        del source, train_rows, validation_rows
        torch.cuda.empty_cache()
    if not load_json(selection_path).get("all_four_cells_sealed"):
        raise RuntimeError("四格选择未全部封印，禁止加载 LSPR24")

    write_status(output_root, "running", "target-evaluation", None, "选择封印后首次加载 LSPR24，每格评价一次")
    target_inventory = data_inventory(cache_root, TARGET_ARRAYS)
    target = load_arrays(cache_root, TARGET_ARRAYS)
    target_load_count = 1
    if target["X24"].shape != (20_227_356, 83):
        raise RuntimeError("LSPR24 冻结缓存形状不符")
    key = np.array(
        [left + "|" + right if left <= right else right + "|" + left for left, right in zip(target["s24"], target["d24"])],
        dtype=object,
    )
    _, flow_entity = np.unique(key, return_inverse=True)
    entity_count = int(flow_entity.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, target["y24"])
    flow_positive_rate = float(target["y24"].astype(np.float64).mean())
    if entity_count != 47_115 or int(entity_labels.sum()) != 752 or abs(flow_positive_rate - 0.0257073138) >= 1e-9:
        raise RuntimeError("LSPR24 实体与标签自检失败")
    del key

    cells: dict[str, Any] = {}
    curve_arrays: dict[str, np.ndarray] = {}
    evaluation_calls_this_process = 0
    evaluation_receipts_reused = 0
    evaluation_started = time.time()
    evaluation_peak_gpu_mib = 0.0
    for cell in CELL_ORDER:
        checkpoint_path = output_root / selections[cell]["checkpoint"]["filename"]
        if selections[cell]["checkpoint"]["sha256"] != sha256_file(checkpoint_path):
            raise RuntimeError(f"{cell} 选择检查点摘要不符")
        target_identity = {
            **run_identity,
            "target_data_inventory_sha256": target_inventory["sha256"],
            "cell": cell,
            "checkpoint_sha256": selections[cell]["checkpoint"]["sha256"],
        }
        restored = load_target_evaluation(output_root, cell, target_identity)
        if restored is not None:
            cell_result, curve = restored
            cells[cell] = cell_result
            for field, values in curve.items():
                curve_arrays[f"{cell}__{field}"] = values
            evaluation_receipts_reused += 1
            log(f"{cell} 复用身份与摘要匹配的目标评价完成收据")
            continue
        model = build_model(config, cell).to("cuda")
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model.load_state_dict(checkpoint["model"])
        selected_p = float(model.p.detach())
        if abs(selected_p - float(selections[cell]["p_at_selection"])) > 1e-9:
            raise RuntimeError(f"{cell} 回载后的共享 p 与选择封印不符")
        torch.cuda.reset_peak_memory_stats()
        started = time.time()
        flow_scores, seen = score_target(config, model, target, torch.device("cuda"))
        evaluation_calls_this_process += 1
        evaluation_seconds = time.time() - started
        evaluation_peak_gpu_mib = max(evaluation_peak_gpu_mib, torch.cuda.max_memory_allocated() / 2**20)
        main_p = selected_p if config["cells"][cell]["learned_lp_pooling"] else None
        main_entity_scores = entity_scores(flow_scores, seen, flow_entity, entity_count, main_p)
        maximum_entity_scores = entity_scores(flow_scores, seen, flow_entity, entity_count, None)
        valid_entity = np.isfinite(main_entity_scores)
        valid_maximum = np.isfinite(maximum_entity_scores)
        metrics = {
            "flow_average_precision": float(average_precision_score(target["y24"][seen], flow_scores[seen])),
            "flow_roc_auc": float(roc_auc_score(target["y24"][seen], flow_scores[seen])),
            "entity_average_precision": float(average_precision_score(entity_labels[valid_entity], main_entity_scores[valid_entity])),
            "maximum_entity_average_precision": float(average_precision_score(entity_labels[valid_maximum], maximum_entity_scores[valid_maximum])),
            "dr_at_fpr": {f"fpr_{value:g}": dr_at_fpr(main_entity_scores, entity_labels, value) for value in DR_FPR_GRID},
            "maximum_dr_at_fpr": {f"fpr_{value:g}": dr_at_fpr(maximum_entity_scores, entity_labels, value) for value in DR_FPR_GRID},
            "flows_scored": int(seen.sum()),
            "entities_scored": int(valid_entity.sum()),
            "evaluation_seconds": evaluation_seconds,
            "target_evaluation_call": CELL_ORDER.index(cell) + 1,
        }
        curve = complete_budget_curve(main_entity_scores, entity_labels)
        for field, values in curve.items():
            curve_arrays[f"{cell}__{field}"] = values
        cell_result = {
            "mechanisms": config["cells"][cell],
            "selection": selections[cell],
            "selected_p": selected_p,
            "target": metrics,
        }
        save_target_evaluation(output_root, cell, target_identity, cell_result, curve)
        cells[cell] = cell_result
        log(f"{cell} 目标评价：逐流AP={metrics['flow_average_precision']:.8f} 实体AP={metrics['entity_average_precision']:.8f}")
        del model, checkpoint, flow_scores, seen, main_entity_scores, maximum_entity_scores
        torch.cuda.empty_cache()
    if len(cells) != 4 or evaluation_calls_this_process + evaluation_receipts_reused != 4 or target_load_count != 1:
        raise RuntimeError("目标年加载或四格评价次数不符")
    curve_path = output_root / "complete-alert-budget-curves.npz"
    temporary_curve = curve_path.with_name(f"{curve_path.name}.partial.{os.getpid()}")
    with temporary_curve.open("wb") as handle:
        np.savez_compressed(handle, **curve_arrays)
    os.replace(temporary_curve, curve_path)
    curve_receipt = {
        "schema_version": "ch3-protocol-a-complete-alert-budget-curves-v1",
        "artifact": {"filename": curve_path.name, "bytes": curve_path.stat().st_size, "sha256": sha256_file(curve_path)},
        "cells": list(CELL_ORDER),
        "fields": ["n_false_positive_entity", "nominal_fpr", "realized_fpr", "detection_rate"],
        "curve_is_complete_over_all_reachable_negative_entity_budgets": True,
        "per_flow_scores_persisted": False,
        "per_entity_scores_persisted": False,
    }
    atomic_json(output_root / "complete-alert-budget-curves-receipt.json", curve_receipt)

    interaction: dict[str, Any] = {}
    for name in ("flow_average_precision", "entity_average_precision", "maximum_entity_average_precision"):
        values = {cell: cells[cell]["target"][name] for cell in CELL_ORDER}
        interaction[name] = {
            **values,
            "causal_prefix_effect": values["C10"] - values["C00"],
            "elp_effect": values["C01"] - values["C00"],
            "combined_effect": values["C11"] - values["C00"],
            "interaction": values["C11"] - values["C10"] - values["C01"] + values["C00"],
        }
    training_seconds = sum(float(selections[cell]["training_seconds"]) for cell in CELL_ORDER)
    evaluation_seconds = sum(float(cells[cell]["target"]["evaluation_seconds"]) for cell in CELL_ORDER)
    launcher_resource = load_json(Path(args.resource_receipt)) if args.resource_receipt else None
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": config["run_id"],
        "model": {
            "model_key": config["model_key"],
            "display_name": config["display_name"],
            **config["candidate"],
            "pytorch_version": torch.__version__,
        },
        "evidence": {
            "single_run_directly_comparable": True,
            "formal_paper_evidence": False,
            "target_previously_accessed": True,
            "independent_test": False,
            "target_metrics_used_for_selection_or_tuning": False,
        },
        "source_selection": {"split": split_stats, "cells": selections},
        "target_evaluation": {
            "dataset": "LSPR24",
            "flow_count": int(len(target["y24"])),
            "entity_count": entity_count,
            "positive_entity_count": int(entity_labels.sum()),
            "flow_positive_rate": flow_positive_rate,
            "cells": cells,
            "data_inventory": target_inventory,
        },
        "interaction": interaction,
        "isolation": {
            "all_four_selections_sealed_before_target_load": True,
            "target_disk_loads": target_load_count,
            "target_evaluation_calls": 4,
            "target_evaluation_calls_this_process": evaluation_calls_this_process,
            "target_evaluation_receipts_reused": evaluation_receipts_reused,
            "one_call_per_cell": True,
        },
        "artifact_policy": {
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "selected_checkpoints_persisted": 4,
            "complete_alert_budget_curve": curve_receipt,
        },
        "resource": {
            "parameter_count": config["candidate"]["parameter_count"],
            "training_wall_seconds_sum": training_seconds,
            "evaluation_wall_seconds_sum": evaluation_seconds,
            "target_stage_wall_seconds": time.time() - evaluation_started,
            "peak_gpu_allocated_mib": max([evaluation_peak_gpu_mib, *[float(selections[cell]["peak_gpu_allocated_mib"]) for cell in CELL_ORDER]]),
            "peak_process_rss_mib": process_peak_rss_mib(),
            "gpu_hours": (training_seconds + evaluation_seconds) / 3600.0,
            "launcher_admission_receipt": launcher_resource,
        },
    }
    atomic_json(output_root / "aggregate-results.json", result)
    write_status(output_root, "computed", "publish-pending", 0, "四格选择与目标评价完成，等待聚合发布")
    build_manifest(output_root, config["run_id"])
    log(f"协议 A 四格完成，总耗时 {(time.time() - T0) / 60:.1f} 分")


def publish_aggregate(config: dict[str, Any], args: argparse.Namespace) -> None:
    destination = config["swanlab"]
    if (
        args.authorized_swanlab_workspace != destination["workspace"]
        or args.authorized_swanlab_project != destination["project"]
    ):
        raise RuntimeError("SwanLab 授权目的地与冻结配置不一致")
    output_root = Path(config["paths"]["output_root"])
    result = load_json(output_root / "aggregate-results.json")
    import swanlab

    swanlab.init(
        workspace=destination["workspace"],
        project=destination["project"],
        name=config["run_id"],
        mode=destination["mode"],
        group=destination["group"],
        tags=destination["tags"],
        log_dir=str(output_root / "swanlog"),
        config={
            "run_id": config["run_id"],
            "model_key": config["model_key"],
            "seed": config["training"]["seed"],
            "protocol": "protocol_a_2x2",
            "target_previously_accessed": True,
            "independent_test": False,
        },
    )
    metrics: dict[str, float] = {}
    for cell in CELL_ORDER:
        selection = result["source_selection"]["cells"][cell]
        target = result["target_evaluation"]["cells"][cell]["target"]
        metrics[f"source/{cell}_selected_epoch"] = float(selection["selected_epoch"])
        metrics[f"source/{cell}_validation_flow_ap"] = float(selection["validation_flow_ap"])
        metrics[f"target/{cell}_flow_ap"] = target["flow_average_precision"]
        metrics[f"target/{cell}_entity_ap"] = target["entity_average_precision"]
        metrics[f"target/{cell}_maximum_entity_ap"] = target["maximum_entity_average_precision"]
        for key, value in target["dr_at_fpr"].items():
            metrics[f"target/{cell}_dr_{key}"] = value
    metrics["resource/training_wall_seconds"] = result["resource"]["training_wall_seconds_sum"]
    metrics["resource/evaluation_wall_seconds"] = result["resource"]["evaluation_wall_seconds_sum"]
    metrics["resource/peak_gpu_allocated_mib"] = result["resource"]["peak_gpu_allocated_mib"]
    metrics["resource/peak_process_rss_mib"] = result["resource"]["peak_process_rss_mib"]
    metrics["resource/gpu_hours"] = result["resource"]["gpu_hours"]
    swanlab.log(metrics, step=0)
    swanlab.finish()
    atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-protocol-a-backbone-2x2-swanlab-receipt-v1",
            "completed": True,
            "workspace": destination["workspace"],
            "project": destination["project"],
            "metric_count": len(metrics),
            "per_sample_values_uploaded": False,
        },
    )
    write_status(output_root, "complete", "finished", 0, "四格结果与聚合指标已完成")
    build_manifest(output_root, config["run_id"])


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    validate_config(config)
    if args.validate_config:
        print("配置核验通过")
        return 0
    try:
        if args.publish_only:
            publish_aggregate(config, args)
        else:
            run_experiment(config, args, config_path)
    except Exception as error:
        output_root = Path(config["paths"]["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        write_status(output_root, "failed", "runtime", 1, f"{type(error).__name__}: {error}"[:1000])
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
