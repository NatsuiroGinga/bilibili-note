"""重跑第三章四格并诊断第四章实体流数分桶。

该入口只读取冻结缓存和 LSPR23 原始归档，不持久化逐流分数。四格训练协议与
``ch3_full.py`` 保持一致，末五个检查点以 safetensors 归档，并对概率求平均后评价。
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import shutil
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
from sklearn.metrics import average_precision_score, roc_auc_score

STARTED_AT = time.time()
CACHE_NAMES = ("X23", "y23", "X24", "y24", "I23", "M23", "I24", "M24", "s24", "d24")
CELLS = (
    ("C00", False, False),
    ("C01", False, True),
    ("C10", True, False),
    ("C11", True, True),
)


def log(message: str) -> None:
    """输出带累计耗时的限频阶段日志。"""
    print(f"[{time.time() - STARTED_AT:8.1f}s] {message}", flush=True)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial")
    with partial.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    partial.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial")
    partial.write_text(value, encoding="utf-8")
    partial.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_config(config: dict[str, Any]) -> None:
    expected_scalars = {
        "schema_version": "ch4-entity-length-bucket-diagnostic-config-v1",
        "run_id": "ch4-entity-length-bucket-diagnostic-seed42-v1",
        "seed": 42,
        "hidden_size": 192,
        "sequence_length": 128,
        "batch_size": 64,
        "learning_rate": 0.002,
        "weight_decay": 0.01,
        "gradient_clip_norm": 1.0,
        "training_steps": 20000,
        "snapshot_interval_steps": 1000,
        "averaged_snapshot_count": 5,
        "auxiliary_loss_weight": 1.0,
        "target_fpr": 0.04,
        "global_metric_absolute_tolerance": 0.001,
        "normalization_sample_absolute_tolerance": 0.00001,
        "underpowered_positive_entity_threshold": 20,
        "screening_only": True,
        "formal_paper_evidence": False,
        "independent_test": False,
        "persist_per_flow_scores": False,
    }
    for key, expected in expected_scalars.items():
        if config.get(key) != expected:
            raise ValueError(f"配置 {key} 必须为冻结值 {expected!r}")
    if config.get("entity_length_buckets") != [
        {"name": "1-2", "minimum": 1, "maximum": 2},
        {"name": "3-10", "minimum": 3, "maximum": 10},
        {"name": "11-100", "minimum": 11, "maximum": 100},
        {"name": "101-1000", "minimum": 101, "maximum": 1000},
        {"name": "1001+", "minimum": 1001, "maximum": None},
    ]:
        raise ValueError("实体流数分桶必须与冻结五档完全一致")
    if config.get("normalization_sample_indices") != [
        0,
        1,
        2,
        127,
        128,
        1024,
        100000,
        1000000,
        16000000,
    ]:
        raise ValueError("归一化固定行索引与冻结配置不一致")
    dependencies = config.get("required_dependency_versions", {})
    if dependencies != {"safetensors": "0.8.0"}:
        raise ValueError("safetensors 必须精确锁定为 0.8.0")
    expected_excluded = {
        "Flow ID",
        "SrcIP",
        "DstIP",
        "mTimestampStart",
        "mTimestampLast",
        "SigID revision",
        "Category",
        "Severity",
        "Anomaly_event",
        "Conn_state",
        "Service",
        "Segment_src",
        "Segment_dst",
        "Expoid_src",
        "Expoid_dst",
        "Label_src",
        "Label_dst",
        "Label",
    }
    if set(config.get("excluded_feature_columns", [])) != expected_excluded:
        raise ValueError("冻结排除列必须与 ch3_full.py 的 18 列完全一致")


def resolve_paths(config: dict[str, Any]) -> dict[str, Path]:
    paths = config.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("配置缺少 paths 对象")
    required = (
        "cache_root",
        "lspr23_zip",
        "lspr24_schema_parquet",
        "frozen_results_json",
        "output_root",
    )
    resolved = {name: Path(paths[name]) for name in required if isinstance(paths.get(name), str)}
    if tuple(resolved) != required:
        raise ValueError("paths 缺少必需路径")
    return resolved


def require_clean_output(output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    protected = ("config.json", "aggregate-results.json", "model_package", "run-status.json")
    conflicts = [name for name in protected if (output_root / name).exists()]
    if conflicts:
        raise FileExistsError(f"输出根已有不可覆盖制品：{conflicts}")


def validate_dependencies(config: dict[str, Any]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for package, expected in config["required_dependency_versions"].items():
        actual = importlib.metadata.version(package)
        if actual != expected:
            raise RuntimeError(f"依赖 {package} 必须为 {expected}，实际为 {actual}")
        versions[package] = actual
    for package in ("numpy", "pyarrow", "scikit-learn", "torch"):
        versions[package] = importlib.metadata.version(package)
    return versions


def validate_inputs(paths: dict[str, Path]) -> dict[str, Any]:
    cache_root = paths["cache_root"]
    missing = [name for name in CACHE_NAMES if not (cache_root / f"{name}.npy").is_file()]
    if missing:
        raise FileNotFoundError(f"冻结缓存缺失且禁止补写：{missing}")
    for name in ("lspr23_zip", "lspr24_schema_parquet", "frozen_results_json"):
        if not paths[name].is_file():
            raise FileNotFoundError(f"必需输入不存在：{paths[name]}")
    return {
        "cache_fields": list(CACHE_NAMES),
        "cache_read_only": True,
        "lspr23_zip_bytes": paths["lspr23_zip"].stat().st_size,
        "frozen_results_sha256": sha256_file(paths["frozen_results_json"]),
    }


def feature_names(schema_path: Path, excluded: set[str]) -> list[str]:
    parquet = pq.ParquetFile(schema_path)
    features = [name for name in parquet.schema_arrow.names if name not in excluded]
    if len(features) != 83:
        raise RuntimeError(f"冻结字段数必须为 83，实际为 {len(features)}")
    return features


def recompute_normalization(
    zip_path: Path,
    features: list[str],
    cached_x23_path: Path,
    sample_indices: list[int],
    tolerance: float,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    log("开始从原始 LSPR23 ZIP 重算 83 字段均值与标准差")
    with zipfile.ZipFile(zip_path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise RuntimeError(f"LSPR23 ZIP 必须恰含一个 CSV，实际为 {members}")
        with archive.open(members[0]) as handle:
            table = pacsv.read_csv(
                handle,
                read_options=pacsv.ReadOptions(block_size=1 << 26),
                convert_options=pacsv.ConvertOptions(include_columns=features),
            )
    cached_x23 = np.load(cached_x23_path, mmap_mode="r", allow_pickle=False)
    if cached_x23.shape != (table.num_rows, len(features)):
        raise RuntimeError(
            f"原始与缓存 X23 形状不一致：raw={(table.num_rows, len(features))} "
            f"cache={cached_x23.shape}"
        )
    if max(sample_indices) >= table.num_rows:
        raise RuntimeError("归一化固定行索引超出 LSPR23 行数")
    raw = np.empty((table.num_rows, len(features)), dtype=np.float32)
    for column_index, name in enumerate(features):
        raw[:, column_index] = np.asarray(
            table.column(name).to_numpy(zero_copy_only=False), dtype=np.float32
        )
    del table
    raw[~np.isfinite(raw)] = 0.0
    mu = raw.mean(0, keepdims=True)
    sd = raw.std(0, keepdims=True)
    sd[sd < 1e-8] = 1.0
    sample = np.asarray(sample_indices, dtype=np.int64)
    transformed = np.clip((raw[sample] - mu) / sd, -10, 10)
    cached_sample = np.asarray(cached_x23[sample], dtype=np.float32)
    max_absolute_difference = float(np.max(np.abs(transformed - cached_sample)))
    receipt = {
        "source": str(zip_path),
        "row_count": int(raw.shape[0]),
        "feature_count": int(raw.shape[1]),
        "sample_indices": sample_indices,
        "sample_max_absolute_difference": max_absolute_difference,
        "sample_absolute_tolerance": tolerance,
        "passed": max_absolute_difference <= tolerance,
        "transform": "float32; non-finite->0; mean/std on LSPR23; sd<1e-8->1; clip[-10,10]",
    }
    del raw, cached_x23, cached_sample, transformed
    gc.collect()
    if not receipt["passed"]:
        raise RuntimeError(
            "重算归一化与冻结 X23 不一致："
            f"max_abs_diff={max_absolute_difference} tolerance={tolerance}"
        )
    log(f"归一化门禁通过：固定行最大绝对差={max_absolute_difference:.9g}")
    return mu, sd, receipt


@dataclass(frozen=True)
class RuntimeData:
    x23: np.ndarray
    y23: np.ndarray
    x24: np.ndarray
    y24: np.ndarray
    i23: np.ndarray
    m23: np.ndarray
    i24: np.ndarray
    m24: np.ndarray
    s24: np.ndarray
    d24: np.ndarray


def load_cache(cache_root: Path) -> RuntimeData:
    arrays: dict[str, np.ndarray] = {}
    for name in CACHE_NAMES:
        path = cache_root / f"{name}.npy"
        if name in {"s24", "d24"}:
            arrays[name] = np.load(path, allow_pickle=True)
        else:
            arrays[name] = np.load(path, mmap_mode="r", allow_pickle=False)
    data = RuntimeData(
        x23=arrays["X23"],
        y23=arrays["y23"],
        x24=arrays["X24"],
        y24=arrays["y24"],
        i23=arrays["I23"],
        m23=arrays["M23"],
        i24=arrays["I24"],
        m24=arrays["M24"],
        s24=arrays["s24"],
        d24=arrays["d24"],
    )
    if data.x23.shape[1] != 83 or data.x24.shape[1] != 83:
        raise RuntimeError("缓存输入特征数不是冻结的 83")
    if data.i23.shape[1] != 128 or data.i24.shape[1] != 128:
        raise RuntimeError("缓存序列长度不是冻结的 128")
    if len(data.x24) != len(data.y24) or len(data.s24) != len(data.y24):
        raise RuntimeError("LSPR24 缓存行数不一致")
    return data


def build_entities(
    sources: np.ndarray, destinations: np.ndarray, labels: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    keys = np.array(
        [
            f"{src}|{dst}" if src <= dst else f"{dst}|{src}"
            for src, dst in zip(sources, destinations, strict=True)
        ],
        dtype=object,
    )
    _, entity_index = np.unique(keys, return_inverse=True)
    entity_count = int(entity_index.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, entity_index, labels)
    flow_counts = np.bincount(entity_index, minlength=entity_count).astype(np.int64)
    return entity_index, entity_labels, flow_counts


def lp_pool(scores: Any, mask: Any, p_value: Any) -> Any:
    import torch

    log_scores = torch.log(scores.clamp(min=1e-7))
    counts = mask.sum(1).clamp(min=1.0)
    summed = torch.logsumexp(
        (p_value * log_scores).masked_fill(mask < 0.5, -1e30), dim=1
    )
    return torch.exp((summed - torch.log(counts)) / p_value)


def create_model(input_size: int, aggregate: bool, lp_enabled: bool, hidden_size: int) -> Any:
    import torch
    import torch.nn as nn

    class Model(nn.Module):
        """与第三章冻结四格完全相同的统一容量模型。"""

        def __init__(self) -> None:
            super().__init__()
            self.aggregate = aggregate
            self.lp_enabled = lp_enabled
            self.feature = nn.Sequential(
                nn.Linear(input_size, hidden_size), nn.ReLU(), nn.Dropout(0.1)
            )
            self.context = nn.Sequential(
                nn.Linear(hidden_size * 2, hidden_size), nn.ReLU(), nn.Dropout(0.1)
            )
            self.output = nn.Linear(hidden_size, 1)
            self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

        @property
        def p(self) -> Any:
            return torch.exp(self.p_log).clamp(1e-3, 1e3)

        def forward(self, inputs: Any, mask: Any) -> Any:
            hidden = self.feature(inputs) * mask.unsqueeze(-1)
            if self.aggregate:
                cumulative = torch.cumsum(hidden, dim=1)
                counts = torch.cumsum(mask, dim=1).clamp(min=1.0).unsqueeze(-1)
                context = cumulative / counts * mask.unsqueeze(-1)
            else:
                context = torch.zeros_like(hidden)
            combined = torch.cat([hidden, context], dim=-1)
            return self.output(self.context(combined)).squeeze(-1)

    return Model()


@dataclass(frozen=True)
class DeviceData:
    x23: Any
    y23: Any
    x24: Any
    i23: Any
    m23: Any
    i24: Any
    m24: Any


def move_to_device(data: RuntimeData, device: str) -> DeviceData:
    import torch

    log(f"开始把冻结矩阵移动到 {device}")
    moved = DeviceData(
        x23=torch.from_numpy(data.x23).to(device),
        y23=torch.from_numpy(data.y23).to(device),
        x24=torch.from_numpy(data.x24).to(device),
        i23=torch.from_numpy(data.i23).to(device),
        m23=torch.from_numpy(data.m23).to(device),
        i24=torch.from_numpy(data.i24).to(device),
        m24=torch.from_numpy(data.m24).to(device),
    )
    if device == "cuda":
        log(f"冻结矩阵已上卡，当前显存={torch.cuda.memory_allocated() / 2**30:.2f} GiB")
    return moved


def cpu_state_dict(model: Any) -> dict[str, Any]:
    return {name: value.detach().cpu().contiguous() for name, value in model.state_dict().items()}


def train_cell(
    cell: str,
    aggregate: bool,
    lp_enabled: bool,
    config: dict[str, Any],
    data: RuntimeData,
    tensors: DeviceData,
    checkpoint_root: Path,
) -> tuple[np.ndarray, np.ndarray, float, dict[str, Any]]:
    import torch
    import torch.nn as nn
    from safetensors.torch import load_file, save_file

    seed = int(config["seed"])
    steps = int(config["training_steps"])
    interval = int(config["snapshot_interval_steps"])
    averaged_count = int(config["averaged_snapshot_count"])
    batch_size = int(config["batch_size"])
    sequence_length = int(config["sequence_length"])
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = tensors.x23.device
    model = create_model(83, aggregate, lp_enabled, int(config["hidden_size"])).to(device)
    decay = [
        parameter
        for name, parameter in model.named_parameters()
        if not (name.endswith(".bias") or name == "p_log")
    ]
    no_decay = [
        parameter
        for name, parameter in model.named_parameters()
        if name.endswith(".bias") or name == "p_log"
    ]
    optimizer = torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": float(config["weight_decay"])},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=float(config["learning_rate"]),
    )
    sequence_labels = (
        data.y23[data.i23.reshape(-1)].reshape(data.i23.shape) * data.m23
    ).max(1) > 0
    sequence_positive_weight = float(
        (1 - sequence_labels.mean()) / max(sequence_labels.mean(), 1e-8)
    )
    flow_positive_weight = torch.tensor(
        [(1 - data.y23.mean()) / data.y23.mean()], device=device
    )
    flow_loss = nn.BCEWithLogitsLoss(reduction="none", pos_weight=flow_positive_weight)
    sequence_loss = nn.BCELoss(reduction="none")
    generator = torch.Generator().manual_seed(seed)
    checkpoint_dir = checkpoint_root / cell
    checkpoint_dir.mkdir(parents=True, exist_ok=False)
    checkpoint_steps: list[int] = []
    training_started = time.time()
    model.train()
    for step_index in range(steps):
        selected = torch.randint(0, len(data.i23), (batch_size,), generator=generator).to(device)
        indices = tensors.i23[selected][:, :sequence_length]
        mask = tensors.m23[selected][:, :sequence_length]
        inputs = tensors.x23[indices.reshape(-1)].reshape(batch_size, sequence_length, 83)
        labels = tensors.y23[indices.reshape(-1)].reshape(batch_size, sequence_length)
        logits = model(inputs, mask)
        loss = (flow_loss(logits, labels) * mask).sum() / mask.sum().clamp(min=1)
        if lp_enabled:
            sequence_scores = lp_pool(torch.sigmoid(logits), mask, model.p).clamp(1e-6, 1 - 1e-6)
            target = (labels * mask).amax(1)
            weights = 1.0 + (sequence_positive_weight - 1.0) * target
            auxiliary = (sequence_loss(sequence_scores, target) * weights).sum() / weights.sum()
            loss = loss + float(config["auxiliary_loss_weight"]) * auxiliary
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), float(config["gradient_clip_norm"]))
        optimizer.step()
        step = step_index + 1
        if steps - step_index <= averaged_count * interval and step % interval == 0:
            checkpoint_path = checkpoint_dir / f"step-{step}.safetensors"
            save_file(
                cpu_state_dict(model),
                checkpoint_path,
                metadata={"cell": cell, "step": str(step), "seed": str(seed)},
            )
            checkpoint_steps.append(step)
        if step % interval == 0:
            elapsed = time.time() - training_started
            throughput = step / max(elapsed, 1e-9)
            remaining = (steps - step) / max(throughput, 1e-9)
            log(
                f"{cell} 训练进度 {step}/{steps}，吞吐={throughput:.2f} 步/秒，"
                f"累计={elapsed:.1f}秒，预计剩余={remaining:.1f}秒"
            )
    expected_steps = list(range(steps - (averaged_count - 1) * interval, steps + 1, interval))
    if checkpoint_steps != expected_steps:
        raise RuntimeError(f"{cell} 末五快照步数错误：{checkpoint_steps}")
    training_seconds = time.time() - training_started
    probability_sum: np.ndarray | None = None
    seen_all: np.ndarray | None = None
    p_values: list[float] = []
    evaluation_started = time.time()
    for step in checkpoint_steps:
        checkpoint_path = checkpoint_dir / f"step-{step}.safetensors"
        model.load_state_dict(load_file(checkpoint_path, device=str(device)))
        model.eval()
        p_values.append(float(model.p.item()))
        scores = torch.zeros(len(data.y24), device=device)
        seen = torch.zeros(len(data.y24), dtype=torch.bool, device=device)
        with torch.no_grad():
            for start in range(0, len(data.i24), 2048):
                indices = tensors.i24[start : start + 2048, :sequence_length]
                mask = tensors.m24[start : start + 2048, :sequence_length]
                batch = indices.shape[0]
                inputs = tensors.x24[indices.reshape(-1)].reshape(batch, sequence_length, 83)
                probabilities = torch.sigmoid(model(inputs, mask))
                flat_indices = indices.reshape(-1)
                valid = mask.reshape(-1) > 0
                scores[flat_indices[valid]] = probabilities.reshape(-1)[valid]
                seen[flat_indices[valid]] = True
        scores_numpy = scores.cpu().numpy()
        seen_numpy = seen.cpu().numpy()
        probability_sum = (
            scores_numpy if probability_sum is None else probability_sum + scores_numpy
        )
        seen_all = seen_numpy if seen_all is None else seen_all | seen_numpy
    if probability_sum is None or seen_all is None:
        raise RuntimeError(f"{cell} 未产生评价概率")
    if not bool(seen_all.all()):
        raise RuntimeError(f"{cell} seen.all() 失败，覆盖={seen_all.mean():.10f}")
    evaluation_seconds = time.time() - evaluation_started
    mean_p = float(np.mean(p_values))
    receipt = {
        "cell": cell,
        "aggregate_enabled": aggregate,
        "lp_enabled": lp_enabled,
        "checkpoint_steps": checkpoint_steps,
        "checkpoint_count": len(checkpoint_steps),
        "probability_average_count": len(checkpoint_steps),
        "mean_learned_p": mean_p,
        "training_seconds": training_seconds,
        "evaluation_seconds": evaluation_seconds,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "seen_all": True,
        "flow_scores_persisted": False,
    }
    log(
        f"{cell} 完成：训练={training_seconds:.1f}秒，评价={evaluation_seconds:.1f}秒，"
        f"p={mean_p:.6f}"
    )
    return probability_sum / len(checkpoint_steps), seen_all, mean_p, receipt


def aggregate_entity_scores(
    flow_scores: np.ndarray,
    seen: np.ndarray,
    entity_index: np.ndarray,
    entity_count: int,
    p_value: float | None,
) -> np.ndarray:
    if p_value is None:
        entity_scores = np.full(entity_count, -np.inf, dtype=np.float32)
        np.maximum.at(entity_scores, entity_index[seen], flow_scores[seen])
        return entity_scores
    sums = np.zeros(entity_count, dtype=np.float64)
    counts = np.zeros(entity_count, dtype=np.float64)
    clipped = np.clip(flow_scores[seen], 1e-7, 1.0).astype(np.float64)
    np.add.at(sums, entity_index[seen], clipped**p_value)
    np.add.at(counts, entity_index[seen], 1.0)
    pooled = np.where(counts > 0, (sums / np.maximum(counts, 1.0)) ** (1.0 / p_value), -np.inf)
    return pooled.astype(np.float32)


def detection_rate_at_fpr(
    labels: np.ndarray, scores: np.ndarray, target_fpr: float
) -> float | None:
    negatives = np.sort(scores[labels == 0])[::-1]
    positives = scores[labels == 1]
    if len(negatives) == 0 or len(positives) == 0:
        return None
    threshold = negatives[min(int(len(negatives) * target_fpr), len(negatives) - 1)]
    return float((positives >= threshold).mean())


def safe_average_precision(labels: np.ndarray, scores: np.ndarray) -> float | None:
    if len(labels) == 0 or not bool(np.any(labels == 1)) or not bool(np.any(labels == 0)):
        return None
    return float(average_precision_score(labels, scores))


def evaluate_global(
    flow_scores: np.ndarray,
    seen: np.ndarray,
    y24: np.ndarray,
    entity_index: np.ndarray,
    entity_labels: np.ndarray,
    p_value: float | None,
    target_fpr: float,
) -> tuple[dict[str, Any], np.ndarray]:
    maximum_scores = aggregate_entity_scores(
        flow_scores, seen, entity_index, len(entity_labels), None
    )
    selected_scores = aggregate_entity_scores(
        flow_scores, seen, entity_index, len(entity_labels), p_value
    )
    valid_maximum = np.isfinite(maximum_scores)
    valid_selected = np.isfinite(selected_scores)
    metrics = {
        "flow_ap": float(average_precision_score(y24[seen], flow_scores[seen])),
        "flow_roc_auc": float(roc_auc_score(y24[seen], flow_scores[seen])),
        "entity_ap_max": float(
            average_precision_score(entity_labels[valid_maximum], maximum_scores[valid_maximum])
        ),
        "entity_ap_selected": float(
            average_precision_score(entity_labels[valid_selected], selected_scores[valid_selected])
        ),
        "dr_at_4pct_fpr": detection_rate_at_fpr(
            entity_labels[valid_selected], selected_scores[valid_selected], target_fpr
        ),
        "seen_all": bool(seen.all()),
    }
    return metrics, selected_scores


def compare_frozen(
    cell: str,
    metrics: dict[str, Any],
    frozen: dict[str, Any],
    tolerance: float,
) -> dict[str, Any]:
    frozen_cell = frozen["cells"][cell]
    comparisons = {
        "flow_ap": (metrics["flow_ap"], float(frozen_cell["fap"])),
        "entity_ap": (metrics["entity_ap_selected"], float(frozen_cell["e_lp"])),
        "dr_at_4pct_fpr": (metrics["dr_at_4pct_fpr"], float(frozen_cell["dr"])),
    }
    differences = {
        name: abs(float(actual) - expected) for name, (actual, expected) in comparisons.items()
    }
    passed = all(difference <= tolerance for difference in differences.values())
    return {
        "tolerance": tolerance,
        "absolute_differences": differences,
        "passed": passed,
    }


def bucket_metrics(
    entity_labels: np.ndarray,
    entity_scores: np.ndarray,
    flow_counts: np.ndarray,
    buckets: list[dict[str, Any]],
    target_fpr: float,
    underpowered_threshold: int,
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for bucket in buckets:
        minimum = int(bucket["minimum"])
        maximum = bucket["maximum"]
        selected = flow_counts >= minimum
        if maximum is not None:
            selected &= flow_counts <= int(maximum)
        selected &= np.isfinite(entity_scores)
        labels = entity_labels[selected]
        scores = entity_scores[selected]
        positive_count = int(labels.sum())
        count = int(len(labels))
        base_rate = float(labels.mean()) if count else None
        ap = safe_average_precision(labels, scores)
        lift = ap / base_rate if ap is not None and base_rate not in {None, 0.0} else None
        result[str(bucket["name"])] = {
            "entity_count": count,
            "positive_entity_count": positive_count,
            "base_rate": base_rate,
            "entity_ap": ap,
            "ap_over_base_rate": lift,
            "dr_at_4pct_fpr": detection_rate_at_fpr(labels, scores, target_fpr),
            "underpowered": positive_count < underpowered_threshold,
        }
    return result


def numeric_delta(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def bucket_deltas(cell_buckets: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for bucket_name in cell_buckets["C00"]:
        bucket_result: dict[str, Any] = {}
        for delta_name, left_cell, right_cell in (
            ("C10-C00", "C10", "C00"),
            ("C11-C00", "C11", "C00"),
            ("C11-C10", "C11", "C10"),
        ):
            left = cell_buckets[left_cell][bucket_name]
            right = cell_buckets[right_cell][bucket_name]
            bucket_result[delta_name] = {
                metric: numeric_delta(left[metric], right[metric])
                for metric in ("entity_ap", "ap_over_base_rate", "dr_at_4pct_fpr")
            }
        result[bucket_name] = bucket_result
    return result


INFERENCE_SOURCE = '''# -*- coding: utf-8 -*-
"""第四章归档模型的研究用途逐流推理入口。"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from safetensors.torch import load_file


class Model(nn.Module):
    def __init__(self, input_size, hidden_size, aggregate):
        super().__init__()
        self.aggregate = aggregate
        self.feature = nn.Sequential(nn.Linear(input_size, hidden_size), nn.ReLU(), nn.Dropout(0.1))
        self.context = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size), nn.ReLU(), nn.Dropout(0.1)
        )
        self.output = nn.Linear(hidden_size, 1)
        self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

    def forward(self, inputs, mask):
        hidden = self.feature(inputs) * mask.unsqueeze(-1)
        if self.aggregate:
            cumulative = torch.cumsum(hidden, dim=1)
            counts = torch.cumsum(mask, dim=1).clamp(min=1.0).unsqueeze(-1)
            context = cumulative / counts * mask.unsqueeze(-1)
        else:
            context = torch.zeros_like(hidden)
        return self.output(self.context(torch.cat([hidden, context], dim=-1))).squeeze(-1)


def main():
    parser = argparse.ArgumentParser(description="加载单个归档检查点并输出逐流概率")
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--cell", choices=("C00", "C01", "C10", "C11"), required=True)
    parser.add_argument("--checkpoint-step", type=int, required=True)
    parser.add_argument("--features-npy", type=Path, required=True)
    parser.add_argument("--mask-npy", type=Path, required=True)
    parser.add_argument("--output-npy", type=Path, required=True)
    args = parser.parse_args()
    package_config = json.loads((args.package_root / "config.json").read_text(encoding="utf-8"))
    normalization = json.loads(
        (args.package_root / "normalization.json").read_text(encoding="utf-8")
    )
    inputs = np.load(args.features_npy, allow_pickle=False).astype(np.float32, copy=False)
    mask = np.load(args.mask_npy, allow_pickle=False).astype(np.float32, copy=False)
    mean = np.asarray(normalization["mean"], dtype=np.float32)
    std = np.asarray(normalization["std"], dtype=np.float32)
    inputs[~np.isfinite(inputs)] = 0.0
    inputs = np.clip((inputs - mean) / std, -10, 10)
    cell = package_config["cells"][args.cell]
    model = Model(83, package_config["hidden_size"], cell["aggregate_enabled"])
    checkpoint = args.package_root / "checkpoints" / args.cell / (
        f"step-{args.checkpoint_step}.safetensors"
    )
    model.load_state_dict(load_file(checkpoint, device="cpu"))
    model.eval()
    with torch.no_grad():
        probabilities = torch.sigmoid(
            model(torch.from_numpy(inputs), torch.from_numpy(mask))
        ).numpy()
    np.save(args.output_npy, probabilities)


if __name__ == "__main__":
    main()
'''


def write_model_manifest(package_root: Path) -> None:
    manifest_files = []
    for path in sorted(package_root.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            relative = path.relative_to(package_root).as_posix()
            manifest_files.append(
                {"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            )
    write_json(
        package_root / "manifest.json",
        {
            "schema_version": "ch4-four-cell-model-package-manifest-v1",
            "self_excluded": True,
            "file_count": len(manifest_files),
            "files": manifest_files,
            "forbidden_content_absent": [
                "data",
                "cache",
                "raw_ip_values",
                "labels",
                "entity_identifiers",
                "per_sample_predictions",
            ],
        },
    )


def build_model_package(
    package_root: Path,
    config: dict[str, Any],
    features: list[str],
    mu: np.ndarray,
    sd: np.ndarray,
    normalization_receipt: dict[str, Any],
    aggregate_results: dict[str, Any],
    dependencies: dict[str, str],
) -> None:
    package_config = {
        "schema_version": "ch4-four-cell-model-package-config-v1",
        "run_id": config["run_id"],
        "seed": config["seed"],
        "input_size": 83,
        "hidden_size": config["hidden_size"],
        "sequence_length": config["sequence_length"],
        "dropout": 0.1,
        "cells": {
            cell: {"aggregate_enabled": aggregate, "lp_enabled": lp_enabled}
            for cell, aggregate, lp_enabled in CELLS
        },
        "snapshot_steps": aggregate_results["snapshot_steps"],
        "probability_ensemble": "末五检查点逐流概率算术平均",
        "dependencies": dependencies,
        "research_only": True,
    }
    write_json(package_root / "config.json", package_config)
    write_json(
        package_root / "features.json",
        {"schema_version": "ch4-model-features-v1", "count": len(features), "names": features},
    )
    write_json(
        package_root / "normalization.json",
        {
            "schema_version": "ch4-model-normalization-v1",
            "dtype": "float32",
            "mean": mu.reshape(-1).astype(float).tolist(),
            "std": sd.reshape(-1).astype(float).tolist(),
            "non_finite_replacement": 0.0,
            "clip_minimum": -10.0,
            "clip_maximum": 10.0,
            "verification": normalization_receipt,
        },
    )
    write_json(package_root / "metrics.json", aggregate_results)
    write_text(package_root / "inference.py", INFERENCE_SOURCE)
    readme = """# 四格模型研究归档

本模型包保存第三章四格 `C00/C01/C10/C11` 在种子 42 下的末五个检查点。

## 数据与适用边界

- 模型使用 LSPR23 全量训练。
- LSPR24 已在多轮人机循环中反复用于探索性评价，不是独立测试集。
- 指标只供研究复核，不得解释为独立测试性能。
- 模型只供研究，不得直接用于生产告警或安全处置。
- 包内不含数据、缓存、IP、标签、实体标识或逐样本预测。

## 推理

`inference.py` 接收按 `features.json` 顺序组织的原始 `float32` 序列特征和掩码，
使用 `normalization.json` 变换后加载指定检查点，输出逐流概率。四格正式指标使用末五
检查点概率平均；单检查点输出不能直接替代归档指标。
"""
    write_text(package_root / "README.md", readme)
    write_model_manifest(package_root)


def verify_model_manifest(package_root: Path) -> None:
    manifest_path = package_root / "manifest.json"
    manifest = read_json(manifest_path)
    if manifest.get("schema_version") != "ch4-four-cell-model-package-manifest-v1":
        raise RuntimeError("模型包 manifest schema 不合法，拒绝刷新")
    entries = manifest.get("files")
    if not isinstance(entries, list) or manifest.get("file_count") != len(entries):
        raise RuntimeError("模型包 manifest 文件计数不合法，拒绝刷新")
    recorded: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise RuntimeError("模型包 manifest 条目不合法，拒绝刷新")
        relative = entry["path"]
        path = package_root / relative
        if not path.is_file() or relative in recorded:
            raise RuntimeError(f"模型包 manifest 路径缺失或重复：{relative}")
        if path.stat().st_size != entry.get("bytes") or sha256_file(path) != entry.get("sha256"):
            raise RuntimeError(f"模型包文件与 manifest 不一致：{relative}")
        recorded.add(relative)
    actual = {
        path.relative_to(package_root).as_posix()
        for path in package_root.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if recorded != actual:
        raise RuntimeError("模型包实际文件集合与 manifest 不一致，拒绝刷新")


def expected_checkpoint_paths(package_root: Path, config: dict[str, Any]) -> list[Path]:
    steps = list(
        range(
            int(config["training_steps"])
            - (int(config["averaged_snapshot_count"]) - 1)
            * int(config["snapshot_interval_steps"]),
            int(config["training_steps"]) + 1,
            int(config["snapshot_interval_steps"]),
        )
    )
    return [
        package_root / "checkpoints" / cell / f"step-{step}.safetensors"
        for cell, _, _ in CELLS
        for step in steps
    ]


def refresh_model_package_inference(config_path: Path) -> None:
    config = read_json(config_path)
    validate_config(config)
    paths = resolve_paths(config)
    output_root = paths["output_root"]
    package_root = output_root / "model_package"
    status = read_json(output_root / "status.json")
    run_status = read_json(output_root / "run-status.json")
    aggregate_path = output_root / "aggregate-results.json"
    aggregate = read_json(aggregate_path)
    metrics_path = package_root / "metrics.json"
    metrics = read_json(metrics_path)
    normalization_path = package_root / "normalization.json"
    normalization = read_json(normalization_path)
    checkpoints = expected_checkpoint_paths(package_root, config)
    checkpoint_actual = sorted((package_root / "checkpoints").glob("*/*.safetensors"))
    expected_resolved = sorted(checkpoints)
    complete = (
        status.get("state") == "finished"
        and status.get("stage") == "complete"
        and status.get("exit_code") == 0
        and run_status.get("state") == "finished"
        and run_status.get("stage") == "complete"
        and run_status.get("exit_code") == 0
        and aggregate.get("status") == "passed"
        and aggregate.get("research_decision_emitted") is True
        and aggregate.get("seen_all") is True
        and aggregate.get("model_checkpoint_count") == 20
        and aggregate.get("flow_scores_persisted") is False
        and metrics == aggregate
        and normalization.get("schema_version") == "ch4-model-normalization-v1"
        and normalization.get("dtype") == "float32"
        and normalization.get("non_finite_replacement") == 0.0
        and len(normalization.get("mean", [])) == 83
        and len(normalization.get("std", [])) == 83
        and bool(np.isfinite(np.asarray(normalization.get("mean"), dtype=np.float32)).all())
        and bool(np.isfinite(np.asarray(normalization.get("std"), dtype=np.float32)).all())
        and bool((np.asarray(normalization.get("std"), dtype=np.float32) > 0).all())
        and checkpoint_actual == expected_resolved
        and all(path.is_file() and path.stat().st_size > 0 for path in checkpoints)
    )
    if not complete:
        raise RuntimeError("既有输出未通过状态、聚合指标、归一化或 20 检查点完整性门禁")
    verify_model_manifest(package_root)
    protected_paths = [aggregate_path, metrics_path, normalization_path, *checkpoints]
    protected_hashes = {str(path): sha256_file(path) for path in protected_paths}
    write_text(package_root / "inference.py", INFERENCE_SOURCE)
    write_model_manifest(package_root)
    write_json(
        output_root / "output-hashes.json",
        {
            "aggregate_results_sha256": sha256_file(aggregate_path),
            "model_manifest_sha256": sha256_file(package_root / "manifest.json"),
            "inference_sha256": sha256_file(package_root / "inference.py"),
            "package_refresh_only": True,
        },
    )
    changed = [
        path for path in protected_paths if sha256_file(path) != protected_hashes[str(path)]
    ]
    if changed:
        raise RuntimeError(f"刷新越界修改了受保护制品：{changed}")
    verify_model_manifest(package_root)
    log(
        "PACKAGE_REFRESH_COMPLETE：仅重写 model_package/inference.py、manifest.json "
        "与 output-hashes.json"
    )


def execute(config_path: Path) -> None:
    import torch

    config = read_json(config_path)
    validate_config(config)
    paths = resolve_paths(config)
    require_clean_output(paths["output_root"])
    shutil.copyfile(config_path, paths["output_root"] / "config.json")
    status_path = paths["output_root"] / "run-status.json"
    write_json(
        status_path,
        {"state": "running", "stage": "preflight", "run_id": config["run_id"]},
    )
    try:
        dependencies = validate_dependencies(config)
        input_receipt = validate_inputs(paths)
        excluded = set(config["excluded_feature_columns"])
        features = feature_names(paths["lspr24_schema_parquet"], excluded)
        mu, sd, normalization_receipt = recompute_normalization(
            paths["lspr23_zip"],
            features,
            paths["cache_root"] / "X23.npy",
            [int(value) for value in config["normalization_sample_indices"]],
            float(config["normalization_sample_absolute_tolerance"]),
        )
        data = load_cache(paths["cache_root"])
        entity_index, entity_labels, flow_counts = build_entities(data.s24, data.d24, data.y24)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device != "cuda":
            raise RuntimeError("正式四格重跑必须使用 CUDA GPU")
        tensors = move_to_device(data, device)
        frozen = read_json(paths["frozen_results_json"])
        package_root = paths["output_root"] / "model_package"
        checkpoint_root = package_root / "checkpoints"
        checkpoint_root.mkdir(parents=True, exist_ok=False)
        global_results: dict[str, Any] = {}
        cell_buckets: dict[str, dict[str, dict[str, Any]]] = {}
        receipts: dict[str, Any] = {}
        reproduction_passed = True
        for cell, aggregate, lp_enabled in CELLS:
            scores, seen, learned_p, receipt = train_cell(
                cell,
                aggregate,
                lp_enabled,
                config,
                data,
                tensors,
                checkpoint_root,
            )
            selected_p = learned_p if lp_enabled else None
            metrics, entity_scores = evaluate_global(
                scores,
                seen,
                data.y24,
                entity_index,
                entity_labels,
                selected_p,
                float(config["target_fpr"]),
            )
            comparison = compare_frozen(
                cell,
                metrics,
                frozen,
                float(config["global_metric_absolute_tolerance"]),
            )
            metrics["frozen_reproduction"] = comparison
            metrics["learned_p"] = learned_p
            global_results[cell] = metrics
            receipts[cell] = receipt
            reproduction_passed = reproduction_passed and bool(comparison["passed"])
            if cell in {"C00", "C10", "C11"}:
                cell_buckets[cell] = bucket_metrics(
                    entity_labels,
                    entity_scores,
                    flow_counts,
                    config["entity_length_buckets"],
                    float(config["target_fpr"]),
                    int(config["underpowered_positive_entity_threshold"]),
                )
            del scores, seen, entity_scores
            gc.collect()
        result = {
            "schema_version": "ch4-entity-length-bucket-diagnostic-results-v1",
            "run_id": config["run_id"],
            "status": "passed" if reproduction_passed else "failed",
            "research_decision_emitted": reproduction_passed,
            "screening_only": True,
            "formal_paper_evidence": False,
            "independent_test": False,
            "input_receipt": input_receipt,
            "normalization_receipt": normalization_receipt,
            "feature_count": len(features),
            "entity_definition": "无向 2-IP",
            "entity_count": int(len(entity_labels)),
            "positive_entity_count": int(entity_labels.sum()),
            "entity_base_rate": float(entity_labels.mean()),
            "seen_all": all(value["seen_all"] for value in global_results.values()),
            "global_metrics": global_results,
            "bucket_metrics": cell_buckets,
            "bucket_deltas": bucket_deltas(cell_buckets),
            "training_receipts": receipts,
            "snapshot_steps": list(
                range(
                    int(config["training_steps"])
                    - (int(config["averaged_snapshot_count"]) - 1)
                    * int(config["snapshot_interval_steps"]),
                    int(config["training_steps"]) + 1,
                    int(config["snapshot_interval_steps"]),
                )
            ),
            "model_checkpoint_count": sum(
                len(value["checkpoint_steps"]) for value in receipts.values()
            ),
            "flow_scores_persisted": False,
            "dependencies": dependencies,
        }
        if not result["seen_all"]:
            raise RuntimeError("全局 seen.all() 合同失败")
        if result["model_checkpoint_count"] != 20:
            raise RuntimeError("模型检查点总数不是 20")
        if not reproduction_passed:
            result.pop("bucket_deltas", None)
            result["bucket_metrics"] = {}
        aggregate_path = paths["output_root"] / "aggregate-results.json"
        write_json(aggregate_path, result)
        build_model_package(
            package_root,
            config,
            features,
            mu,
            sd,
            normalization_receipt,
            result,
            dependencies,
        )
        write_json(
            paths["output_root"] / "output-hashes.json",
            {
                "aggregate_results_sha256": sha256_file(aggregate_path),
                "model_manifest_sha256": sha256_file(package_root / "manifest.json"),
            },
        )
        write_json(
            status_path,
            {
                "state": "finished" if reproduction_passed else "failed",
                "stage": "complete" if reproduction_passed else "frozen-reproduction",
                "run_id": config["run_id"],
                "exit_code": 0 if reproduction_passed else 2,
                "research_decision_emitted": reproduction_passed,
                "flow_scores_persisted": False,
            },
        )
        if not reproduction_passed:
            raise RuntimeError("四格全局指标未通过冻结复现容差，禁止输出研究裁决")
    except Exception as error:
        write_json(
            status_path,
            {
                "state": "failed",
                "stage": "exception",
                "run_id": config.get("run_id"),
                "exit_code": 1,
                "error_type": type(error).__name__,
                "error": str(error),
                "research_decision_emitted": False,
            },
        )
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="重跑第三章四格、归档末五模型并执行第四章实体流数分桶诊断"
    )
    parser.add_argument("--config", type=Path, help="冻结配置 JSON")
    parser.add_argument(
        "--refresh-model-package-inference",
        action="store_true",
        help="在既有完整输出上仅刷新推理源码及模型包哈希，不重训",
    )
    return parser


def main() -> None:
    parser = build_parser()
    arguments = parser.parse_args()
    if arguments.config is None:
        parser.error("运行或模型包刷新必须提供 --config")
    if arguments.refresh_model_package_inference:
        refresh_model_package_inference(arguments.config)
    else:
        execute(arguments.config)


if __name__ == "__main__":
    main()
