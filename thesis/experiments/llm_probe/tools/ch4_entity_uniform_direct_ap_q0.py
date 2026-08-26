"""第四章实体均匀训练与直接实体 AP 优化的冻结 Q0 入口。

入口从 LSPR23 原始 ZIP 流式构建只驻内存的无向 2-IP 实体索引，先执行
随机 Lp 袋源侧误差门，再按门禁结果运行严格四格或仅 M 两格。目标年度标签只在
选择封存后载入；逐流分数、实体键、实体索引和抽样成员均不持久化。
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import resource
import shutil
import sys
import time
import traceback
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score

STARTED_AT = time.time()
CELLS = (
    ("M0R0", "C11 流均匀训练与原目标", False, False),
    ("M1R0", "C11 实体均匀训练与原目标", True, False),
    ("M0R1", "C11 流均匀训练与直接实体 AP", False, True),
    ("M1R1", "C11 实体均匀训练与直接实体 AP", True, True),
)
SOURCE_CACHE_NAMES = ("X23", "y23", "I23", "M23")
TARGET_CACHE_NAMES = ("X24", "y24", "I24", "M24", "s24", "d24")


class Q0Failure(RuntimeError):
    """携带持久状态名和稳定退出码的运行失败。"""

    def __init__(self, state: str, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.state = state
        self.exit_code = exit_code


def log(message: str) -> None:
    print(f"[{time.time() - STARTED_AT:9.1f}s] {message}", flush=True)


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须为对象：{path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial")
    with partial.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    partial.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_seed(*parts: object) -> int:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def peak_rss_mib() -> float:
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value / 1024.0 if sys.platform != "darwin" else value / (1024.0 * 1024.0)


def validate_config(config: dict[str, Any]) -> None:
    frozen = {
        "schema_version": "ch4-entity-uniform-direct-ap-q0-config-v1",
        "run_id": "ch4-entity-uniform-direct-ap-q0-seed42-v1-rerun2",
        "seed": 42,
        "feature_count": 83,
        "hidden_size": 192,
        "dropout": 0.1,
        "parameter_count": 90242,
        "sequence_length": 128,
        "entity_batch_size": 64,
        "positive_entities_per_batch": 32,
        "negative_entities_per_batch": 32,
        "entity_flow_budget": 128,
        "physical_entity_microbatch": 8,
        "training_steps": 20000,
        "snapshot_steps": [16000, 17000, 18000, 19000, 20000],
        "learning_rate": 0.002,
        "weight_decay": 0.01,
        "gradient_clip_norm": 1.0,
        "flow_positive_weight": 8.9438,
        "entity_positive_weight": 19.8687,
        "auxiliary_loss_weight": 1.0,
        "screening_only": True,
        "formal_paper_evidence": False,
        "independent_test": False,
        "persist_per_flow_scores": False,
        "automatic_mixed_precision": False,
        "hyperparameter_search_count": 0,
    }
    for key, expected in frozen.items():
        if config.get(key) != expected:
            raise ValueError(f"配置 {key} 必须为冻结值 {expected!r}")
    contract = config.get("input_contract", {})
    expected_contract = {
        "lspr23_zip_sha256": "4c39f29a2e99ec58f6c167863d49d944ab5e46dc78a28afe78cc57ba85cd2885",
        "lspr23_zip_bytes": 1925103715,
        "lspr23_csv_uncompressed_bytes": 10588252004,
        "lspr23_flow_count": 16353511,
        "lspr23_entity_count": 150680,
        "lspr23_positive_entity_count": 239,
        "lspr24_flow_count": 20227356,
        "lspr24_entity_count": 47115,
        "lspr24_positive_entity_count": 752,
        "source_columns": ["SrcIP", "DstIP", "Label"],
        "entity_definition": "unordered-2-ip",
    }
    if contract != expected_contract:
        raise ValueError("输入合同不是冻结的 LSPR23/LSPR24 无向 2-IP 合同")
    paths = config.get("paths", {})
    required_paths = {
        "cache_root",
        "lspr23_zip",
        "lspr23_zip_member",
        "archived_c11_checkpoint",
        "diagnostic_results",
        "output_root",
    }
    if set(paths) != required_paths or paths["lspr23_zip_member"] != "ls23pr_v1.csv":
        raise ValueError("paths 必须完整显式冻结且 ZIP 成员必须为 ls23pr_v1.csv")
    if any(not isinstance(paths[key], str) for key in required_paths):
        raise ValueError("全部冻结路径必须为字符串")
    if config.get("required_dependency_versions") != {"safetensors": "0.8.0"}:
        raise ValueError("safetensors 必须精确为 0.8.0")
    if config.get("soap") != {
        "moving_rate": 0.9,
        "margin": 1.0,
        "denominator_floor": 0.000001,
        "loss_weight": 1.0,
        "zero_gradient_failure_steps": 100,
        "denominator_floor_failure_fraction": 0.05,
    }:
        raise ValueError("SOAP 合同不是冻结值")
    gate = config.get("lp_gate", {})
    if gate.get("p_values") != [0.5, 1.0, 1.223554, 2.0]:
        raise ValueError("Lp 门 p 值不一致")
    if gate.get("k_values") != [32, 64, 128] or gate.get("repetitions") != 32:
        raise ValueError("Lp 门 K 或重复数不一致")
    if config.get("entity_length_buckets") != [
        {"name": "1-2", "minimum": 1, "maximum": 2},
        {"name": "3-10", "minimum": 3, "maximum": 10},
        {"name": "11-100", "minimum": 11, "maximum": 100},
        {"name": "101-1000", "minimum": 101, "maximum": 1000},
        {"name": "1001+", "minimum": 1001, "maximum": None},
    ]:
        raise ValueError("实体长度桶不是冻结五档")
    destination = config.get("swanlab", {})
    if destination.get("project") != "ns3-rwkv-lspr24" or destination.get("mode") != "cloud":
        raise ValueError("SwanLab 项目或模式不是冻结值")
    if not isinstance(destination.get("workspace"), str) or not destination["workspace"]:
        raise ValueError("SwanLab 工作区必须显式给出")
    if (
        destination.get("group")
        != "ch4-entity-uniform-direct-ap-q0-seed42-v1-rerun2"
        or destination.get("lifecycle")
        != "independent-process-per-cell-and-aggregate"
        or destination.get("orchestrator_imports_swanlab") is not False
        or destination.get("preinit_commands")
        != ["swanlab ping", "swanlab verify"]
        or destination.get("init_401_retry")
        != {"maximum_retries": 1, "requires_new_process": True}
        or destination.get("tags")
        != [
            "chapter4",
            "entity-ap",
            "q0",
            "seed42",
            "strict-2x2",
            "rerun2",
        ]
    ):
        raise ValueError("SwanLab rerun2 独立进程生命周期合同不一致")
    if config.get("failed_run_provenance") != {
        "run_id": "ch4-entity-uniform-direct-ap-q0-seed42-v1-rerun1",
        "output_root": "/root/autodl-tmp/thesis/experiments/llm_probe/runs/candidates/ch4-entity-uniform-direct-ap-q0-seed42-v1-rerun1",
        "failure_state": "TRAINING_FAILED_M0R1",
        "actual_failure_stage": "training-M0R1-soap-state-index",
        "completed_cells": ["M0R0", "M1R0"],
        "target_labels_read": False,
        "reuse_artifacts": False,
        "reuse_blocked_reason": "rerun1 缺少四格完成汇总、选择封存与目标评估，不能满足完整恢复合同",
    }:
        raise ValueError("首次失败谱系或禁止复用合同不一致")


def resolved_paths(config: dict[str, Any]) -> dict[str, Path]:
    return {
        key: Path(value)
        for key, value in config["paths"].items()
        if key != "lspr23_zip_member"
    }


def write_status(output_root: Path, state: str, stage: str, exit_code: int | None, **extra: Any) -> None:
    write_json(
        output_root / "status.json",
        {
            "schema_version": "ch4-entity-uniform-direct-ap-q0-status-v1",
            "run_id": "ch4-entity-uniform-direct-ap-q0-seed42-v1-rerun2",
            "state": state,
            "stage": stage,
            "exit_code": exit_code,
            "updated_at_unix": time.time(),
            "screening_only": True,
            "formal_paper_evidence": False,
            "independent_test": False,
            "flow_scores_persisted": False,
            **extra,
        },
    )


def validate_dependencies(config: dict[str, Any]) -> dict[str, str]:
    versions = {}
    for package in ("numpy", "pyarrow", "scikit-learn", "torch", "safetensors", "swanlab"):
        versions[package] = importlib.metadata.version(package)
    if versions["safetensors"] != config["required_dependency_versions"]["safetensors"]:
        raise Q0Failure("PRECHECK_FAILED", "safetensors 版本与冻结配置不一致", 69)
    return versions


def validate_inputs(config: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    missing = [name for name in SOURCE_CACHE_NAMES + TARGET_CACHE_NAMES if not (paths["cache_root"] / f"{name}.npy").is_file()]
    required = [paths["lspr23_zip"], paths["archived_c11_checkpoint"], paths["diagnostic_results"]]
    if missing or any(not path.is_file() for path in required):
        raise Q0Failure("PRECHECK_FAILED", f"冻结输入缺失：cache={missing}", 66)
    contract = config["input_contract"]
    zip_path = paths["lspr23_zip"]
    if zip_path.stat().st_size != contract["lspr23_zip_bytes"]:
        raise Q0Failure("PRECHECK_FAILED", "LSPR23 ZIP 字节数不一致", 65)
    zip_hash = sha256_file(zip_path)
    if zip_hash != contract["lspr23_zip_sha256"]:
        raise Q0Failure("PRECHECK_FAILED", "LSPR23 ZIP SHA-256 不一致", 65)
    input_hashes = {
        "lspr23_zip": {"sha256": zip_hash, "bytes": zip_path.stat().st_size, "member": config["paths"]["lspr23_zip_member"]},
        "archived_c11_checkpoint": {"sha256": sha256_file(paths["archived_c11_checkpoint"]), "bytes": paths["archived_c11_checkpoint"].stat().st_size},
        "diagnostic_results": {"sha256": sha256_file(paths["diagnostic_results"]), "bytes": paths["diagnostic_results"].stat().st_size},
        "cache": {name: {"sha256": sha256_file(paths["cache_root"] / f"{name}.npy"), "bytes": (paths["cache_root"] / f"{name}.npy").stat().st_size} for name in SOURCE_CACHE_NAMES + TARGET_CACHE_NAMES},
    }
    return input_hashes


@dataclass(frozen=True)
class SourceData:
    x: np.ndarray
    y: np.ndarray
    sequences: np.ndarray
    sequence_mask: np.ndarray


@dataclass(frozen=True)
class EntityIndex:
    ent: np.ndarray
    labels: np.ndarray
    counts: np.ndarray
    sequence_counts: np.ndarray
    offsets: np.ndarray
    flow_order: np.ndarray
    sequence_entity: np.ndarray


def load_source_cache(cache_root: Path, config: dict[str, Any]) -> SourceData:
    # 数据身份：X23 是 dijk 复现管线标准化后的特征矩阵（非有限值置 0 → 按 LSPR23 逐列均值和标准差
    # 标准化 → 裁剪 [-10, 10]），不是 raw83 原值；形状与文件字节数和 raw83 产品相同但内容不同。
    # 只有训练侧同样消费这份缓存的模型才可直接读它。见该缓存目录的 README.md。
    x = np.load(cache_root / "X23.npy", mmap_mode="r", allow_pickle=False)
    y = np.load(cache_root / "y23.npy", mmap_mode="r", allow_pickle=False)
    sequences = np.load(cache_root / "I23.npy", mmap_mode="r", allow_pickle=False)
    mask = np.load(cache_root / "M23.npy", mmap_mode="r", allow_pickle=False)
    if x.shape != (config["input_contract"]["lspr23_flow_count"], 83):
        raise Q0Failure("PRECHECK_FAILED", f"X23 形状错误：{x.shape}", 65)
    if y.shape != (len(x),) or sequences.shape != mask.shape or sequences.shape[1] != 128:
        raise Q0Failure("PRECHECK_FAILED", "源缓存形状不一致", 65)
    if not np.isin(np.asarray(y), (0, 1)).all():
        raise Q0Failure("PRECHECK_FAILED", "源标签不是二值", 65)
    return SourceData(x=x, y=y, sequences=sequences, sequence_mask=mask)


def normalize_ip(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def build_source_entity_index(config: dict[str, Any], paths: dict[str, Path], source: SourceData) -> tuple[EntityIndex, dict[str, Any]]:
    import pyarrow.csv as pacsv

    started = time.time()
    flow_count = int(config["input_contract"]["lspr23_flow_count"])
    ent = np.empty(flow_count, dtype=np.int32)
    entity_by_key: dict[tuple[str, str], int] = {}
    labels: list[int] = []
    counts: list[int] = []
    offset = 0
    member = config["paths"]["lspr23_zip_member"]
    log("阶段 P2 开始：流式构建 LSPR23 无向 2-IP 内存实体索引")
    with zipfile.ZipFile(paths["lspr23_zip"]) as archive:
        info = archive.getinfo(member)
        if info.file_size != config["input_contract"]["lspr23_csv_uncompressed_bytes"]:
            raise Q0Failure("FAILED_SOURCE_ENTITY_INDEX", "ZIP 成员未压缩字节数不一致", 65)
        with archive.open(member) as handle:
            reader = pacsv.open_csv(
                handle,
                read_options=pacsv.ReadOptions(block_size=1 << 24),
                convert_options=pacsv.ConvertOptions(include_columns=["SrcIP", "DstIP", "Label"]),
            )
            for batch in reader:
                src_values = batch.column(0).to_pylist()
                dst_values = batch.column(1).to_pylist()
                batch_labels = np.asarray(batch.column(2).to_numpy(zero_copy_only=False), dtype=np.int8)
                if offset + len(batch_labels) > flow_count:
                    raise Q0Failure("FAILED_SOURCE_ENTITY_INDEX", "ZIP 有效行超过冻结流数", 65)
                for local, (src, dst, label) in enumerate(zip(src_values, dst_values, batch_labels, strict=True)):
                    left = normalize_ip(src)
                    right = normalize_ip(dst)
                    key = (left, right) if left <= right else (right, left)
                    entity = entity_by_key.get(key)
                    if entity is None:
                        entity = len(labels)
                        entity_by_key[key] = entity
                        labels.append(int(label))
                        counts.append(0)
                    else:
                        labels[entity] = max(labels[entity], int(label))
                    ent[offset + local] = entity
                    counts[entity] += 1
                offset += len(batch_labels)
                if offset % 1000000 < len(batch_labels):
                    elapsed = time.time() - started
                    log(f"源实体索引进度 {offset:,}/{flow_count:,}，吞吐={offset / max(elapsed, 1e-9):,.0f} 流/秒，峰值 RSS={peak_rss_mib():.1f} MiB")
    del entity_by_key
    gc.collect()
    label_array = np.asarray(labels, dtype=np.int8)
    count_array = np.asarray(counts, dtype=np.int64)
    if offset != flow_count or len(label_array) != config["input_contract"]["lspr23_entity_count"]:
        raise Q0Failure("FAILED_SOURCE_ENTITY_INDEX", f"源流/实体数错误：flows={offset} entities={len(label_array)}", 65)
    if int(label_array.sum()) != config["input_contract"]["lspr23_positive_entity_count"]:
        raise Q0Failure("FAILED_SOURCE_ENTITY_INDEX", "源正实体数不一致", 65)
    if np.any(label_array[ent] < np.asarray(source.y, dtype=np.int8)):
        raise Q0Failure("FAILED_SOURCE_ENTITY_INDEX", "源正流未连接到正实体", 65)
    valid = np.asarray(source.sequence_mask) > 0
    sequence_entity = np.empty(len(source.sequences), dtype=np.int32)
    for start in range(0, len(source.sequences), 200000):
        stop = min(start + 200000, len(source.sequences))
        indices = np.asarray(source.sequences[start:stop])
        masks = valid[start:stop]
        owners = ent[indices]
        first = owners[:, 0]
        if np.any((owners != first[:, None]) & masks):
            raise Q0Failure("FAILED_SOURCE_ENTITY_INDEX", "I23 序列跨越真实实体", 65)
        sequence_entity[start:stop] = first
    sequence_counts = np.bincount(sequence_entity, minlength=len(label_array)).astype(np.int64)
    if np.any(sequence_counts == 0):
        raise Q0Failure("FAILED_SOURCE_ENTITY_INDEX", "存在未被 I23 覆盖的实体", 65)
    flow_order = np.argsort(ent, kind="stable").astype(np.int32, copy=False)
    offsets = np.empty(len(label_array) + 1, dtype=np.int64)
    offsets[0] = 0
    np.cumsum(count_array, out=offsets[1:])
    receipt = {
        "schema_version": "ch4-source-entity-index-receipt-v1",
        "zip_sha256": config["input_contract"]["lspr23_zip_sha256"],
        "zip_member": member,
        "flow_count": offset,
        "entity_count": len(label_array),
        "positive_entity_count": int(label_array.sum()),
        "sequence_count": int(len(sequence_entity)),
        "all_flows_assigned_once": bool(int(count_array.sum()) == flow_count),
        "entity_labels_equal_maximum_flow_label": True,
        "sequences_single_entity": True,
        "derived_index_persisted": False,
        "raw_ip_persisted": False,
        "elapsed_seconds": time.time() - started,
        "peak_rss_mib": peak_rss_mib(),
    }
    log(f"源实体索引完成：{offset:,} 流、{len(label_array):,} 实体、{int(label_array.sum())} 正实体")
    return EntityIndex(ent, label_array, count_array, sequence_counts, offsets, flow_order, sequence_entity), receipt


def create_model(config: dict[str, Any]) -> Any:
    import torch
    import torch.nn as nn

    class C11(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            hidden = int(config["hidden_size"])
            self.feature = nn.Sequential(nn.Linear(83, hidden), nn.ReLU(), nn.Dropout(float(config["dropout"])))
            self.context = nn.Sequential(nn.Linear(hidden * 2, hidden), nn.ReLU(), nn.Dropout(float(config["dropout"])))
            self.output = nn.Linear(hidden, 1)
            self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

        @property
        def p(self) -> Any:
            return torch.exp(self.p_log).clamp(1e-3, 1e3)

        def forward(self, inputs: Any, mask: Any) -> Any:
            hidden = self.feature(inputs) * mask.unsqueeze(-1)
            cumulative = torch.cumsum(hidden, dim=1)
            counts = torch.cumsum(mask, dim=1).clamp(min=1.0).unsqueeze(-1)
            context = cumulative / counts * mask.unsqueeze(-1)
            return self.output(self.context(torch.cat([hidden, context], dim=-1))).squeeze(-1)

    model = C11()
    if sum(parameter.numel() for parameter in model.parameters()) != config["parameter_count"]:
        raise Q0Failure("PRECHECK_FAILED", "C11 参数量不是 90242", 65)
    return model


def lp_pool(probabilities: Any, mask: Any, p_value: Any) -> Any:
    import torch

    log_scores = torch.log(probabilities.clamp(min=1e-7))
    counts = mask.sum(1).clamp(min=1.0)
    summed = torch.logsumexp((p_value * log_scores).masked_fill(mask < 0.5, -1e30), dim=1)
    return torch.exp((summed - torch.log(counts)) / p_value)


def entity_rows(index: EntityIndex, entity: int) -> np.ndarray:
    return index.flow_order[index.offsets[entity] : index.offsets[entity + 1]]


def sampled_rows(index: EntityIndex, entity: int, k: int, *seed_parts: object) -> np.ndarray:
    rows = entity_rows(index, entity)
    if len(rows) <= k:
        return rows
    rng = np.random.default_rng(stable_seed(*seed_parts, entity, k))
    return np.sort(rng.choice(rows, size=k, replace=False))


def pad_entity_batch(
    source: SourceData,
    rows_by_entity: list[np.ndarray],
    device: str,
    fixed_width: int | None = None,
) -> tuple[Any, Any, Any]:
    import torch

    width = fixed_width if fixed_width is not None else max(len(rows) for rows in rows_by_entity)
    if any(len(rows) > width for rows in rows_by_entity):
        raise ValueError("实体流数超过固定批宽")
    indices = np.zeros((len(rows_by_entity), width), dtype=np.int64)
    mask = np.zeros((len(rows_by_entity), width), dtype=np.float32)
    for row, values in enumerate(rows_by_entity):
        indices[row, : len(values)] = values
        mask[row, : len(values)] = 1.0
    inputs = torch.from_numpy(np.asarray(source.x[indices], dtype=np.float32)).to(device)
    labels = torch.from_numpy(np.asarray(source.y[indices], dtype=np.float32)).to(device)
    return inputs, labels, torch.from_numpy(mask).to(device)


def model_gradient_vector(model: Any) -> np.ndarray:
    parts = []
    for parameter in model.parameters():
        gradient = parameter.grad
        parts.append(np.zeros(parameter.numel(), np.float32) if gradient is None else gradient.detach().cpu().float().numpy().reshape(-1))
    return np.concatenate(parts)


def cosine_and_relative_l2(estimated: np.ndarray, reference: np.ndarray) -> tuple[float, float]:
    denominator = float(np.linalg.norm(estimated) * np.linalg.norm(reference))
    cosine = float(np.dot(estimated, reference) / denominator) if denominator > 0 else 0.0
    relative = float(np.linalg.norm(estimated - reference) / max(np.linalg.norm(reference), 1e-12))
    return cosine, relative


def rankdata(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=np.float64)
    start = 0
    while start < len(values):
        stop = start + 1
        while stop < len(values) and values[order[stop]] == values[order[start]]:
            stop += 1
        ranks[order[start:stop]] = (start + stop - 1) / 2.0
        start = stop
    return ranks


def spearman(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.corrcoef(rankdata(left), rankdata(right))[0, 1])


def ap_surrogate(scores: Any, labels: Any, weights: Any, margin: float, floor: float) -> Any:
    import torch

    logits = torch.logit(scores.clamp(1e-6, 1 - 1e-6))
    positive = labels > 0.5
    positive_logits = logits[positive]
    losses = torch.relu(margin - (positive_logits[:, None] - logits[None, :])).square()
    inner = weights[None, :]
    g1 = (losses * inner * labels[None, :]).sum(1)
    g2 = (losses * inner).sum(1).clamp(min=floor)
    outer = weights[positive]
    return -((outer * g1 / g2).sum() / outer.sum().clamp(min=floor))


def choose_gate_queue(index: EntityIndex, config: dict[str, Any]) -> np.ndarray:
    buckets = config["entity_length_buckets"]
    chosen: list[int] = []
    for label, total in ((1, 32), (0, 32)):
        candidates = np.flatnonzero(index.labels == label)
        ranked = sorted(candidates.tolist(), key=lambda entity: stable_seed("lp-gate", config["seed"], entity))
        per_bucket: list[list[int]] = []
        for bucket in buckets:
            maximum = bucket["maximum"]
            per_bucket.append([entity for entity in ranked if index.counts[entity] >= bucket["minimum"] and (maximum is None or index.counts[entity] <= maximum)])
        selected: list[int] = []
        for group in per_bucket:
            if group:
                selected.append(group[0])
        selected.extend(entity for entity in ranked if entity not in selected)
        chosen.extend(selected[:total])
    queue = np.asarray(chosen, dtype=np.int32)
    if len(queue) != 64 or int(index.labels[queue].sum()) != 32:
        raise Q0Failure("R1_DISABLED_BY_LP_GATE", "无法构造固定 32/32 源实体队列", 3)
    return queue


def scores_and_gradient(model: Any, source: SourceData, index: EntityIndex, queue: np.ndarray, p_value: float, k: int | None, repetition: int, bag: str, device: str, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    import torch

    if k is None:
        return complete_entity_scores_and_gradient(
            model, source, index, queue, p_value, device, config
        )
    rows = [sampled_rows(index, int(entity), k, "lp-gate", config["seed"], p_value, repetition, bag) for entity in queue]
    inputs, _, mask = pad_entity_batch(source, rows, device)
    model.zero_grad(set_to_none=True)
    probabilities = torch.sigmoid(model(inputs, mask))
    p_tensor = torch.tensor(p_value, dtype=torch.float32, device=device)
    scores = lp_pool(probabilities, mask, p_tensor)
    labels = torch.from_numpy(index.labels[queue].astype(np.float32)).to(device)
    weights = torch.full_like(labels, 1.0 / len(labels))
    loss = ap_surrogate(scores, labels, weights, config["soap"]["margin"], config["soap"]["denominator_floor"])
    loss.backward()
    gradient = model_gradient_vector(model)
    return scores.detach().cpu().numpy(), gradient


def complete_entity_scores_and_gradient(
    model: Any,
    source: SourceData,
    index: EntityIndex,
    queue: np.ndarray,
    p_value: float,
    device: str,
    config: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    """以两遍重计算获得完整实体分数和端到端参数梯度。"""
    import torch

    complete_scores: list[float] = []
    with torch.no_grad():
        for entity in queue:
            rows = entity_rows(index, int(entity))
            inputs, _, mask = pad_entity_batch(source, [rows], device)
            probabilities = torch.sigmoid(model(inputs, mask))
            score = lp_pool(
                probabilities,
                mask,
                torch.tensor(p_value, dtype=torch.float32, device=device),
            )
            complete_scores.append(float(score.item()))
            del inputs, mask, probabilities, score
    score_leaf = torch.tensor(
        complete_scores, dtype=torch.float32, device=device, requires_grad=True
    )
    labels = torch.from_numpy(index.labels[queue].astype(np.float32)).to(device)
    weights = torch.full_like(labels, 1.0 / len(labels))
    loss = ap_surrogate(
        score_leaf,
        labels,
        weights,
        config["soap"]["margin"],
        config["soap"]["denominator_floor"],
    )
    score_derivatives = torch.autograd.grad(loss, score_leaf)[0].detach()
    model.zero_grad(set_to_none=True)
    for queue_index, entity in enumerate(queue):
        rows = entity_rows(index, int(entity))
        inputs, _, mask = pad_entity_batch(source, [rows], device)
        probabilities = torch.sigmoid(model(inputs, mask))
        score = lp_pool(
            probabilities,
            mask,
            torch.tensor(p_value, dtype=torch.float32, device=device),
        )[0]
        score.backward(score_derivatives[queue_index])
        del inputs, mask, probabilities, score
    return np.asarray(complete_scores, dtype=np.float32), model_gradient_vector(model)


def execute_lp_gate(model: Any, source: SourceData, index: EntityIndex, config: dict[str, Any], device: str) -> dict[str, Any]:
    gate = config["lp_gate"]
    queue = choose_gate_queue(index, config)
    records: dict[str, Any] = {}
    all_passed = True
    log("阶段 P2：执行源侧随机 Lp 分数、双袋与完整端到端梯度门")
    for p_value in gate["p_values"]:
        full_scores, full_gradient = scores_and_gradient(model, source, index, queue, p_value, None, 0, "full", device, config)
        full_ap = float(average_precision_score(index.labels[queue], full_scores))
        by_k: dict[str, Any] = {}
        gradients: dict[int, list[np.ndarray]] = {32: [], 64: [], 128: []}
        independent_cosines: list[float] = []
        for k in gate["k_values"]:
            score_spearman: list[float] = []
            ap_differences: list[float] = []
            score_p95: list[float] = []
            cosine_values: list[float] = []
            relative_values: list[float] = []
            bucket_errors: dict[str, list[float]] = {bucket["name"]: [] for bucket in config["entity_length_buckets"]}
            for repetition in range(gate["repetitions"]):
                scores_a, gradient_a = scores_and_gradient(model, source, index, queue, p_value, k, repetition, "A", device, config)
                gradients[k].append(gradient_a)
                cosine, relative = cosine_and_relative_l2(gradient_a, full_gradient)
                cosine_values.append(cosine)
                relative_values.append(relative)
                score_spearman.append(spearman(full_scores, scores_a))
                ap_differences.append(abs(float(average_precision_score(index.labels[queue], scores_a)) - full_ap))
                score_p95.append(float(np.quantile(np.abs(scores_a - full_scores), 0.95)))
                for bucket in config["entity_length_buckets"]:
                    maximum = bucket["maximum"]
                    selected = (index.counts[queue] >= bucket["minimum"]) & (True if maximum is None else index.counts[queue] <= maximum)
                    if np.any(selected):
                        bucket_errors[bucket["name"]].append(float(np.quantile(np.abs(scores_a[selected] - full_scores[selected]), 0.95)))
                if k == 128:
                    _, gradient_b = scores_and_gradient(model, source, index, queue, p_value, k, repetition, "B", device, config)
                    cosine_b, relative_b = cosine_and_relative_l2(gradient_b, full_gradient)
                    cosine_values.append(cosine_b)
                    relative_values.append(relative_b)
                    independent_cosines.append(cosine_and_relative_l2(gradient_a, gradient_b)[0])
            by_k[str(k)] = {
                "score_spearman_median": float(np.median(score_spearman)),
                "score_spearman_minimum": float(np.min(score_spearman)),
                "entity_ap_max_absolute_difference": float(np.max(ap_differences)),
                "score_absolute_error_p95_maximum": float(np.max(score_p95)),
                "gradient_cosine_median": float(np.median(cosine_values)),
                "gradient_cosine_minimum": float(np.min(cosine_values)),
                "gradient_relative_l2_median": float(np.median(relative_values)),
                "bucket_score_error_p95": {name: (float(np.median(values)) if values else None) for name, values in bucket_errors.items()},
            }
        k128 = by_k["128"]
        relative_by_k = {k: by_k[str(k)]["gradient_relative_l2_median"] for k in gate["k_values"]}
        passed = (
            k128["score_spearman_median"] >= gate["spearman_median_minimum"]
            and k128["score_spearman_minimum"] >= gate["spearman_minimum"]
            and k128["entity_ap_max_absolute_difference"] <= gate["entity_ap_max_absolute_difference"]
            and k128["score_absolute_error_p95_maximum"] <= gate["score_absolute_error_p95_maximum"]
            and k128["gradient_cosine_median"] >= gate["gradient_cosine_median_minimum"]
            and k128["gradient_cosine_minimum"] >= gate["gradient_cosine_minimum"]
            and k128["gradient_relative_l2_median"] <= gate["gradient_relative_l2_median_maximum"]
            and float(np.median(independent_cosines)) >= gate["independent_bag_cosine_median_minimum"]
            and relative_by_k[128] <= relative_by_k[64] + gate["k_monotonic_slack"]
            and relative_by_k[64] <= relative_by_k[32] + gate["k_monotonic_slack"]
        )
        records[str(p_value)] = {"full_entity_ap": full_ap, "by_k": by_k, "independent_k128_bag_gradient_cosine_median": float(np.median(independent_cosines)), "passed": passed}
        all_passed = all_passed and passed
        log(f"Lp 门 p={p_value:g}：{'通过' if passed else '失败'}")
    return {
        "schema_version": "ch4-random-lp-estimator-gate-v1",
        "status": "PASSED" if all_passed else "R1_DISABLED_BY_LP_GATE",
        "passed": all_passed,
        "queue_entity_count": 64,
        "positive_entity_count": 32,
        "negative_entity_count": 32,
        "queue_members_persisted": False,
        "full_entity_end_to_end_gradient_reference": True,
        "k128_independent_bags": 2,
        "random_p_moment_unbiasedness_claimed": False,
        "soap_composite_gradient_unbiasedness_claimed": False,
        "r1_description": "过门后的随机袋插值估计",
        "results": records,
    }


def initial_state(config: dict[str, Any]) -> dict[str, Any]:
    import torch

    torch.manual_seed(config["seed"])
    np.random.seed(config["seed"])
    model = create_model(config)
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def state_dict_sha256(state: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        tensor = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(json.dumps(list(tensor.shape)).encode("ascii"))
        digest.update(tensor.numpy().tobytes(order="C"))
    return digest.hexdigest()


def shared_entity_batch(index: EntityIndex, step: int, config: dict[str, Any]) -> np.ndarray:
    positive = np.flatnonzero(index.labels == 1)
    negative = np.flatnonzero(index.labels == 0)
    rng = np.random.default_rng(stable_seed("training-entities", config["seed"], step))
    return np.concatenate(
        [
            rng.choice(positive, 32, replace=False),
            rng.choice(negative, 32, replace=False),
        ]
    ).astype(np.int32)


def target_weights(index: EntityIndex, entities: np.ndarray, entity_uniform: bool, device: str) -> Any:
    import torch

    labels = index.labels
    if entity_uniform:
        target = np.full(len(labels), 1.0 / len(labels), dtype=np.float64)
    else:
        target = index.sequence_counts.astype(np.float64) / index.sequence_counts.sum()
    positive_count = int(labels.sum())
    negative_count = len(labels) - positive_count
    rho = np.where(labels == 1, 1.0 / (2 * positive_count), 1.0 / (2 * negative_count))
    importance = target[entities] / rho[entities]
    result = np.empty(len(entities), dtype=np.float32)
    for label in (0, 1):
        selected = labels[entities] == label
        target_mass = float(target[labels == label].sum())
        result[selected] = (importance[selected] / importance[selected].sum() * target_mass).astype(np.float32)
    return torch.from_numpy(result).to(device)


def soap_state_loss(scores: Any, labels: Any, weights: Any, entities: np.ndarray, positive_lookup: np.ndarray, state: Any, config: dict[str, Any]) -> tuple[Any, dict[str, float]]:
    import torch

    settings = config["soap"]
    logits = torch.logit(scores.clamp(1e-6, 1 - 1e-6))
    positive = labels > 0.5
    losses = torch.relu(settings["margin"] - (logits[positive, None] - logits[None, :])).square()
    current_g1 = (losses * weights[None, :] * labels[None, :]).sum(1)
    current_g2 = (losses * weights[None, :]).sum(1)
    positive_numpy = positive.detach().cpu().numpy()
    state_indices = torch.from_numpy(positive_lookup[entities[positive_numpy]]).to(scores.device)
    old = state[state_indices].detach()
    rate = settings["moving_rate"]
    updated_g1 = rate * old[:, 0] + (1 - rate) * current_g1.detach()
    updated_g2 = rate * old[:, 1] + (1 - rate) * current_g2.detach()
    state[state_indices, 0] = updated_g1
    state[state_indices, 1] = updated_g2
    denominator = updated_g2.clamp(min=settings["denominator_floor"])
    surrogate = current_g1 / denominator - updated_g1 * current_g2 / denominator.square()
    outer = weights[positive]
    loss = -(outer * surrogate).sum() / outer.sum().clamp(min=settings["denominator_floor"])
    return loss, {
        "denominator_floor_fraction": float((updated_g2 <= settings["denominator_floor"]).float().mean().item()),
        "state_u1_minimum": float(updated_g1.min().item()),
        "state_u1_maximum": float(updated_g1.max().item()),
        "state_u2_minimum": float(updated_g2.min().item()),
        "state_u2_maximum": float(updated_g2.max().item()),
    }


def validate_tracking_gate(
    output_root: Path, role: str, tracking_attempt: int
) -> dict[str, Any]:
    if tracking_attempt not in {1, 2}:
        raise Q0Failure("TRAINING_TRACKING_FAILED", "跟踪尝试编号只能为 1 或 2", 82)
    gate_root = (
        output_root / "tracking-gates" / role / f"attempt-{tracking_attempt}"
    )
    paths = {
        "ping_log": gate_root / "swanlab-ping.log",
        "ping_exit": gate_root / "swanlab-ping.exit-code.txt",
        "verify_log": gate_root / "swanlab-verify.log",
        "verify_exit": gate_root / "swanlab-verify.exit-code.txt",
    }
    if any(not path.is_file() for path in paths.values()):
        raise Q0Failure(
            "TRAINING_TRACKING_FAILED",
            f"{role} 第 {tracking_attempt} 次初始化缺少 ping/verify 门禁制品",
            82,
        )
    try:
        ping_exit = int(paths["ping_exit"].read_text(encoding="utf-8").strip())
        verify_exit = int(paths["verify_exit"].read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as error:
        raise Q0Failure(
            "TRAINING_TRACKING_FAILED", "ping/verify 退出码收据无效", 82
        ) from error
    receipt = {
        "schema_version": "ch4-swanlab-preinit-gate-v1",
        "role": role,
        "attempt": tracking_attempt,
        "ping_exit_code": ping_exit,
        "verify_exit_code": verify_exit,
        "ping_log_sha256": sha256_file(paths["ping_log"]),
        "verify_log_sha256": sha256_file(paths["verify_log"]),
        "passed": ping_exit == 0 and verify_exit == 0,
        "commands": ["swanlab ping", "swanlab verify"],
    }
    write_json(gate_root / "receipt.json", receipt)
    if not receipt["passed"]:
        raise Q0Failure(
            "TRAINING_TRACKING_FAILED",
            f"{role} 第 {tracking_attempt} 次初始化前 ping/verify 门失败",
            82,
        )
    return receipt


def is_swanlab_init_401(error: BaseException) -> bool:
    messages: list[str] = []
    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        messages.append(f"{type(current).__name__}: {current}")
        current = current.__cause__ or current.__context__
    message = "\n".join(messages).lower()
    return "401" in message and (
        "unauthorized" in message or "/api/projects/" in message
    )


def swanlab_start(
    config: dict[str, Any],
    role: str,
    display_name: str,
    output_root: Path,
    tracking_attempt: int,
    authorized_workspace: str,
    authorized_project: str,
    aggregate: bool = False,
) -> tuple[Any, Any]:
    destination = config["swanlab"]
    if authorized_workspace != destination["workspace"] or authorized_project != destination["project"]:
        raise Q0Failure(
            "TRAINING_TRACKING_FAILED", "SwanLab 授权目的地与冻结配置不一致", 78
        )
    validate_tracking_gate(output_root, role, tracking_attempt)
    import swanlab

    try:
        run = swanlab.init(
            workspace=authorized_workspace,
            project=authorized_project,
            name=display_name,
            mode=destination["mode"],
            group=destination["group"],
            tags=[*destination["tags"], "aggregate"] if aggregate else destination["tags"],
            log_dir=str(
                output_root
                / "swanlog"
                / role
                / f"attempt-{tracking_attempt}"
            ),
            config={
                "run_id": config["run_id"],
                "role": role,
                "seed": config["seed"],
                "tracking_attempt": tracking_attempt,
                "screening_only": True,
                "formal_paper_evidence": False,
                "independent_test": False,
            },
        )
    except Exception as error:
        retryable = is_swanlab_init_401(error) and tracking_attempt == 1
        write_json(
            output_root
            / "tracking-attempts"
            / role
            / f"attempt-{tracking_attempt}-init-failure.json",
            {
                "schema_version": "ch4-swanlab-init-failure-v1",
                "role": role,
                "attempt": tracking_attempt,
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
                "http_401_unauthorized": is_swanlab_init_401(error),
                "bounded_retry_allowed": retryable,
                "requires_new_process": True,
            },
        )
        raise Q0Failure(
            "TRAINING_TRACKING_FAILED",
            f"{role} SwanLab 在线运行初始化失败：{type(error).__name__}: {error}",
            81 if retryable else 82,
        ) from error
    return swanlab, run


def train_cell(cell: str, display_name: str, entity_uniform: bool, direct_ap: bool, initial: dict[str, Any], source: SourceData, index: EntityIndex, config: dict[str, Any], output_root: Path, device: str, tracking_attempt: int, authorized_workspace: str, authorized_project: str) -> dict[str, Any]:
    import torch
    import torch.nn.functional as functional
    from safetensors.torch import save_file

    torch.manual_seed(config["seed"])
    np.random.seed(config["seed"])
    if device == "cuda":
        torch.cuda.manual_seed_all(config["seed"])
        torch.cuda.reset_peak_memory_stats()
    model = create_model(config).to(device)
    model.load_state_dict(initial)
    decay = [parameter for name, parameter in model.named_parameters() if not (name.endswith(".bias") or name == "p_log")]
    no_decay = [parameter for name, parameter in model.named_parameters() if name.endswith(".bias") or name == "p_log"]
    optimizer = torch.optim.AdamW([{"params": decay, "weight_decay": config["weight_decay"]}, {"params": no_decay, "weight_decay": 0.0}], lr=config["learning_rate"])
    positive_entities = np.flatnonzero(index.labels == 1)
    positive_lookup = np.full(len(index.labels), -1, dtype=np.int32)
    positive_lookup[positive_entities] = np.arange(len(positive_entities), dtype=np.int32)
    soap_state = torch.zeros((len(positive_entities), 2), dtype=torch.float32, device=device)
    soap_state_updates = np.zeros(len(positive_entities), dtype=np.int32)
    checkpoint_dir = output_root / "cells" / cell / "checkpoints"
    swanlab, run = swanlab_start(
        config,
        cell,
        f"{display_name}（{cell}）",
        output_root,
        tracking_attempt,
        authorized_workspace,
        authorized_project,
    )
    torch.manual_seed(config["seed"])
    if device == "cuda":
        torch.cuda.manual_seed_all(config["seed"])
    started = time.time()
    encoded_flows = 0
    requested_flows = 0
    entity_draws = np.zeros(len(index.labels), dtype=np.int32)
    entity_score_gradient_mass = np.zeros(len(index.labels), dtype=np.float64)
    zero_ap_gradient_steps = 0
    positive_coverage_step: int | None = None
    last_soap = {}
    exposure = {bucket["name"]: 0 for bucket in config["entity_length_buckets"]}
    try:
        checkpoint_dir.mkdir(parents=True, exist_ok=False)
        model.train()
        for step in range(1, config["training_steps"] + 1):
            entities = shared_entity_batch(index, step, config)
            rows = [sampled_rows(index, int(entity), config["entity_flow_budget"], "training-flows", config["seed"], step) for entity in entities]
            requested_flows += len(entities) * config["entity_flow_budget"]
            encoded_flows += sum(len(value) for value in rows)
            np.add.at(entity_draws, entities, 1)
            if (
                positive_coverage_step is None
                and np.all(entity_draws[index.labels == 1] > 0)
            ):
                positive_coverage_step = step
            for bucket in config["entity_length_buckets"]:
                maximum = bucket["maximum"]
                selected = (index.counts[entities] >= bucket["minimum"]) & (True if maximum is None else index.counts[entities] <= maximum)
                exposure[bucket["name"]] += int(selected.sum())
            logits_parts = []
            label_parts = []
            mask_parts = []
            microbatch = int(config["physical_entity_microbatch"])
            for start in range(0, len(rows), microbatch):
                inputs_part, labels_part, mask_part = pad_entity_batch(
                    source,
                    rows[start : start + microbatch],
                    device,
                    fixed_width=config["entity_flow_budget"],
                )
                logits_parts.append(model(inputs_part, mask_part))
                label_parts.append(labels_part)
                mask_parts.append(mask_part)
            logits = torch.cat(logits_parts, dim=0)
            flow_labels = torch.cat(label_parts, dim=0)
            mask = torch.cat(mask_parts, dim=0)
            flow_loss = functional.binary_cross_entropy_with_logits(logits, flow_labels, reduction="none", pos_weight=torch.tensor(config["flow_positive_weight"], device=device))
            entity_flow_loss = (flow_loss * mask).sum(1) / mask.sum(1).clamp(min=1)
            scores = lp_pool(torch.sigmoid(logits), mask, model.p).clamp(1e-6, 1 - 1e-6)
            labels = torch.from_numpy(index.labels[entities].astype(np.float32)).to(device)
            entity_bce = functional.binary_cross_entropy(scores, labels, reduction="none") * (1 + (config["entity_positive_weight"] - 1) * labels)
            weights = target_weights(index, entities, entity_uniform, device)
            base_loss = (weights * (entity_flow_loss + config["auxiliary_loss_weight"] * entity_bce)).sum()
            loss = base_loss
            ap_loss = torch.zeros((), device=device)
            if direct_ap:
                ap_loss, last_soap = soap_state_loss(scores, labels, weights, entities, positive_lookup, soap_state, config)
                positive_batch_entities = entities[index.labels[entities] == 1]
                np.add.at(
                    soap_state_updates,
                    positive_lookup[positive_batch_entities],
                    1,
                )
                if last_soap["denominator_floor_fraction"] > config["soap"]["denominator_floor_failure_fraction"]:
                    raise Q0Failure(f"TRAINING_FAILED_{cell}", "SOAP 分母触底比例超过 5%", 4)
                loss = loss + config["soap"]["loss_weight"] * ap_loss
            if not torch.isfinite(loss):
                raise Q0Failure(f"TRAINING_FAILED_{cell}", "训练损失非有限", 4)
            if direct_ap:
                ap_score_gradient = torch.autograd.grad(
                    ap_loss, scores, retain_graph=True, allow_unused=False
                )[0]
                ap_gradient_norm = float(ap_score_gradient.norm().item())
                zero_ap_gradient_steps = (
                    zero_ap_gradient_steps + 1 if ap_gradient_norm == 0 else 0
                )
                if zero_ap_gradient_steps >= config["soap"]["zero_gradient_failure_steps"]:
                    raise Q0Failure(
                        f"TRAINING_FAILED_{cell}", "AP 梯度连续 100 步为零", 4
                    )
            score_gradient = torch.autograd.grad(
                loss, scores, retain_graph=True, allow_unused=False
            )[0]
            np.add.at(
                entity_score_gradient_mass,
                entities,
                score_gradient.detach().abs().cpu().numpy().astype(np.float64),
            )
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            gradient_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config["gradient_clip_norm"])
            if not torch.isfinite(gradient_norm):
                raise Q0Failure(f"TRAINING_FAILED_{cell}", "梯度非有限", 4)
            optimizer.step()
            if step in config["snapshot_steps"]:
                save_file({name: value.detach().cpu().contiguous() for name, value in model.state_dict().items()}, checkpoint_dir / f"step-{step}.safetensors", metadata={"cell": cell, "step": str(step), "seed": str(config["seed"])})
            if step % 1000 == 0:
                elapsed = time.time() - started
                if direct_ap:
                    last_soap["state_coverage_fraction"] = float(
                        np.count_nonzero(soap_state_updates) / len(soap_state_updates)
                    )
                    last_soap["state_update_count"] = int(soap_state_updates.sum())
                metrics = {"training/loss": float(loss.detach().item()), "training/base_loss": float(base_loss.detach().item()), "training/ap_loss": float(ap_loss.detach().item()), "training/learned_p": float(model.p.detach().item()), "training/encoded_flows": encoded_flows, "training/throughput_steps_per_second": step / max(elapsed, 1e-9), "training/peak_rss_mib": peak_rss_mib(), **{f"soap/{key}": value for key, value in last_soap.items()}}
                try:
                    swanlab.log(metrics, step=step)
                except Exception as error:
                    raise Q0Failure(
                        "TRAINING_TRACKING_FAILED",
                        f"{cell} SwanLab 指标写入失败：{type(error).__name__}: {error}",
                        82,
                    ) from error
                log(f"{cell} 训练 {step}/{config['training_steps']}，吞吐={metrics['training/throughput_steps_per_second']:.3f} 步/秒，累计编码流={encoded_flows:,}")
        try:
            run.finish()
        except Exception as error:
            raise Q0Failure(
                "TRAINING_TRACKING_FAILED",
                f"{cell} SwanLab 正式运行结束失败：{type(error).__name__}: {error}",
                82,
            ) from error
    except Exception as error:
        if not (
            isinstance(error, Q0Failure)
            and error.state == "TRAINING_TRACKING_FAILED"
        ):
            try:
                run.finish()
            except Exception:
                log(f"{cell} 失败运行的 SwanLab 结束调用也失败")
        raise
    checkpoint_hashes = {str(step): sha256_file(checkpoint_dir / f"step-{step}.safetensors") for step in config["snapshot_steps"]}
    importance = (index.sequence_counts / index.sequence_counts.sum()) if not entity_uniform else np.full(len(index.labels), 1 / len(index.labels))
    rho = np.where(index.labels == 1, 1 / (2 * int(index.labels.sum())), 1 / (2 * int((index.labels == 0).sum())))
    raw_weights = importance / rho
    receipt = {
        "schema_version": "ch4-entity-ap-cell-training-v1",
        "cell": cell,
        "display_name": display_name,
        "entity_uniform": entity_uniform,
        "direct_entity_ap": direct_ap,
        "common_initial_state_sha256": state_dict_sha256(initial),
        "swanlab_tracking_attempt": tracking_attempt,
        "independent_python_process": True,
        "swanlab_online_run_finished": True,
        "training_steps": config["training_steps"],
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "encoded_flow_count": encoded_flows,
        "requested_flow_count": requested_flows,
        "positive_entity_proposals": config["training_steps"] * 32,
        "negative_entity_proposals": config["training_steps"] * 32,
        "unique_entity_count": int(np.count_nonzero(entity_draws)),
        "repeated_entity_draw_count": int(entity_draws.sum() - np.count_nonzero(entity_draws)),
        "within_step_duplicate_entity_count": 0,
        "positive_entity_coverage": float(np.count_nonzero(entity_draws[index.labels == 1]) / int(index.labels.sum())),
        "positive_entity_full_coverage_step": positive_coverage_step,
        "weight_minimum": float(raw_weights.min()),
        "weight_median": float(np.median(raw_weights)),
        "weight_p95": float(np.quantile(raw_weights, 0.95)),
        "weight_maximum": float(raw_weights.max()),
        "weight_effective_sample_size": float(raw_weights.sum() ** 2 / np.square(raw_weights).sum()),
        "length_bucket_entity_exposure": exposure,
        "length_bucket_entity_score_gradient_mass": {
            bucket["name"]: float(
                entity_score_gradient_mass[
                    (index.counts >= bucket["minimum"])
                    & (
                        True
                        if bucket["maximum"] is None
                        else index.counts <= bucket["maximum"]
                    )
                ].sum()
            )
            for bucket in config["entity_length_buckets"]
        },
        "maximum_single_entity_score_gradient_fraction": float(
            entity_score_gradient_mass.max()
            / max(entity_score_gradient_mass.sum(), 1e-12)
        ),
        "checkpoint_hashes": checkpoint_hashes,
        "selection_rule": "冻结末五步 16000/17000/18000/19000/20000 概率算术平均",
        "training_seconds": time.time() - started,
        "peak_rss_mib": peak_rss_mib(),
        "peak_gpu_memory_mib": float(torch.cuda.max_memory_allocated() / 2**20) if device == "cuda" else 0.0,
        "soap_state_bytes": int(soap_state.numel() * soap_state.element_size()) if direct_ap else 0,
        "soap_state_coverage_fraction": (
            float(np.count_nonzero(soap_state_updates) / len(soap_state_updates))
            if direct_ap
            else 0.0
        ),
        "soap_state_update_count": int(soap_state_updates.sum()),
        "flow_scores_persisted": False,
        "sampling_members_persisted": False,
    }
    write_json(output_root / "cells" / cell / "train-metrics.json", receipt)
    del model, optimizer, soap_state, logits, scores
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    return receipt


def build_target_entities(sources: np.ndarray, destinations: np.ndarray, labels: np.ndarray, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    key_to_entity: dict[tuple[str, str], int] = {}
    entity_index = np.empty(len(labels), dtype=np.int32)
    entity_labels: list[int] = []
    counts: list[int] = []
    for row, (source, destination, label) in enumerate(zip(sources, destinations, labels, strict=True)):
        left, right = normalize_ip(source), normalize_ip(destination)
        key = (left, right) if left <= right else (right, left)
        entity = key_to_entity.get(key)
        if entity is None:
            entity = len(entity_labels)
            key_to_entity[key] = entity
            entity_labels.append(int(label))
            counts.append(0)
        else:
            entity_labels[entity] = max(entity_labels[entity], int(label))
        entity_index[row] = entity
        counts[entity] += 1
    del key_to_entity
    labels_array = np.asarray(entity_labels, dtype=np.int8)
    counts_array = np.asarray(counts, dtype=np.int64)
    if len(labels_array) != config["input_contract"]["lspr24_entity_count"] or int(labels_array.sum()) != config["input_contract"]["lspr24_positive_entity_count"]:
        raise Q0Failure("EVALUATION_FAILED", "目标实体计数不一致", 6)
    return entity_index, labels_array, counts_array


def aggregate_entity_scores(flow_scores: np.ndarray, entity_index: np.ndarray, entity_count: int, p_value: float) -> np.ndarray:
    sums = np.zeros(entity_count, dtype=np.float64)
    counts = np.bincount(entity_index, minlength=entity_count).astype(np.float64)
    np.add.at(sums, entity_index, np.clip(flow_scores, 1e-7, 1.0).astype(np.float64) ** p_value)
    return (sums / counts).astype(np.float64) ** (1.0 / p_value)


def detection_rate_at_fpr(labels: np.ndarray, scores: np.ndarray, target_fpr: float) -> float:
    negatives = np.sort(scores[labels == 0])[::-1]
    threshold = negatives[min(int(len(negatives) * target_fpr), len(negatives) - 1)]
    return float((scores[labels == 1] >= threshold).mean())


def evaluate_cell(cell: str, config: dict[str, Any], output_root: Path, target: dict[str, np.ndarray], entity_index: np.ndarray, entity_labels: np.ndarray, flow_counts: np.ndarray, device: str) -> dict[str, Any]:
    import torch
    from safetensors.torch import load_file

    probability_sum = np.zeros(len(target["y"]), dtype=np.float64)
    seen_all: np.ndarray | None = None
    p_values: list[float] = []
    started = time.time()
    model = create_model(config).to(device)
    for step in config["snapshot_steps"]:
        model.load_state_dict(load_file(output_root / "cells" / cell / "checkpoints" / f"step-{step}.safetensors", device=device))
        model.eval()
        p_values.append(float(model.p.detach().item()))
        scores = torch.zeros(len(target["y"]), dtype=torch.float32, device=device)
        seen = torch.zeros(len(target["y"]), dtype=torch.bool, device=device)
        with torch.no_grad():
            for start in range(0, len(target["i"]), 2048):
                index_numpy = np.asarray(
                    target["i"][start : start + 2048], dtype=np.int64
                )
                indices = torch.from_numpy(index_numpy).to(device)
                mask = torch.from_numpy(np.asarray(target["m"][start : start + 2048], dtype=np.float32)).to(device)
                inputs = torch.from_numpy(
                    np.asarray(
                        target["x"][index_numpy.reshape(-1)].reshape(
                            len(index_numpy), 128, 83
                        ),
                        dtype=np.float32,
                    )
                ).to(device)
                probabilities = torch.sigmoid(model(inputs, mask))
                flat_indices = indices.reshape(-1)
                valid = mask.reshape(-1) > 0
                scores[flat_indices[valid]] = probabilities.reshape(-1)[valid]
                seen[flat_indices[valid]] = True
        probability_sum += scores.cpu().numpy()
        seen_numpy = seen.cpu().numpy()
        seen_all = seen_numpy if seen_all is None else seen_all | seen_numpy
    if seen_all is None or not bool(seen_all.all()):
        raise Q0Failure("EVALUATION_FAILED", f"{cell} 目标 seen.all() 失败", 6)
    flow_scores = (probability_sum / len(config["snapshot_steps"])).astype(np.float32)
    p_value = float(np.mean(p_values))
    entity_scores = aggregate_entity_scores(flow_scores, entity_index, len(entity_labels), p_value)
    buckets = {}
    for bucket in config["entity_length_buckets"]:
        maximum = bucket["maximum"]
        selected = (flow_counts >= bucket["minimum"]) & (True if maximum is None else flow_counts <= maximum)
        labels = entity_labels[selected]
        scores = entity_scores[selected]
        base_rate = float(labels.mean())
        ap = float(average_precision_score(labels, scores))
        buckets[bucket["name"]] = {"entity_count": int(len(labels)), "positive_entity_count": int(labels.sum()), "base_rate": base_rate, "entity_ap": ap, "ap_over_base_rate": ap / base_rate, "dr_at_4pct_fpr": detection_rate_at_fpr(labels, scores, config["target_fpr"])}
    result = {
        "schema_version": "ch4-entity-ap-cell-evaluation-v1",
        "cell": cell,
        "flow_ap": float(average_precision_score(target["y"], flow_scores)),
        "entity_ap": float(average_precision_score(entity_labels, entity_scores)),
        "entity_dr_at_4pct_fpr": detection_rate_at_fpr(entity_labels, entity_scores, config["target_fpr"]),
        "learned_p": p_value,
        "seen_all": True,
        "entity_count": int(len(entity_labels)),
        "positive_entity_count": int(entity_labels.sum()),
        "length_buckets": buckets,
        "evaluation_seconds": time.time() - started,
        "flow_scores_persisted": False,
        "entity_scores_persisted": False,
    }
    write_json(output_root / "cells" / cell / "evaluation.json", result)
    del flow_scores, entity_scores, model
    gc.collect()
    return result


def determine_decision(config: dict[str, Any], evaluations: dict[str, Any], training: dict[str, Any], gate_passed: bool) -> dict[str, Any]:
    flow_counts = [receipt["encoded_flow_count"] for receipt in training.values()]
    unfair_fraction = (max(flow_counts) - min(flow_counts)) / min(flow_counts)
    if unfair_fraction > 0.01:
        raise Q0Failure("INVALID_UNFAIR_FLOW_BUDGET", f"有效编码流预算差={unfair_fraction:.6f}", 5)
    if not gate_passed:
        return {
            "status": "COMPLETED_M_ONLY_DIAGNOSTIC",
            "candidate_advanced": False,
            "strict_2x2_complete": False,
            "reason": "R1_DISABLED_BY_LP_GATE",
            "entity_uniform_measure_entity_ap_delta": (
                evaluations["M1R0"]["entity_ap"]
                - evaluations["M0R0"]["entity_ap"]
            ),
            "direct_entity_ap_conclusion_allowed": False,
            "joint_candidate_conclusion_allowed": False,
            "flow_budget_relative_range": unfair_fraction,
        }
    ap = {cell: value["entity_ap"] for cell, value in evaluations.items()}
    interaction = (ap["M1R1"] - ap["M1R0"]) - (ap["M0R1"] - ap["M0R0"])
    bucket_names = [bucket["name"] for bucket in config["entity_length_buckets"]]
    front_guard = all(evaluations["M1R1"]["length_buckets"][name]["entity_ap"] >= evaluations["M0R0"]["length_buckets"][name]["entity_ap"] - 0.02 for name in bucket_names[:3])
    tail_deltas = [evaluations["M1R1"]["length_buckets"][name]["entity_ap"] - evaluations["M0R0"]["length_buckets"][name]["entity_ap"] for name in bucket_names[-2:]]
    passed = (
        ap["M1R1"] - ap["M0R0"] >= 0.02
        and ap["M1R1"] - max(ap["M1R0"], ap["M0R1"]) >= 0.005
        and ap["M1R1"] - ap["M0R1"] >= 0.005
        and ap["M1R1"] - ap["M1R0"] >= 0.005
        and interaction >= 0
        and ap["M1R1"] >= config["xgboost_n1_entity_ap_anchor"]
        and evaluations["M1R1"]["flow_ap"] >= evaluations["M0R0"]["flow_ap"] - 0.02
        and evaluations["M1R1"]["entity_dr_at_4pct_fpr"] >= evaluations["M0R0"]["entity_dr_at_4pct_fpr"] - 0.02
        and front_guard
        and all(delta > 0 for delta in tail_deltas)
        and float(np.mean(tail_deltas)) >= 0.05
    )
    return {
        "status": "COMPLETED_Q0_SUPPORTED" if passed else "COMPLETED_Q0_REJECTED",
        "candidate_advanced": passed,
        "strict_2x2_complete": True,
        "entity_uniform_measure_supported": (
            ap["M1R0"] - ap["M0R0"] >= 0.005
            and ap["M1R1"] - ap["M0R1"] >= 0.005
        ),
        "direct_entity_ap_supported": (
            ap["M0R1"] - ap["M0R0"] >= 0.005
            and ap["M1R1"] - ap["M1R0"] >= 0.005
        ),
        "interaction": interaction,
        "flow_budget_relative_range": unfair_fraction,
        "tail_entity_ap_deltas": tail_deltas,
        "historical_m0r0_absolute_difference": abs(
            ap["M0R0"] - config["historical_c11_entity_ap"]
        ),
    }


def write_manifest(output_root: Path) -> None:
    forbidden = {"ent23.npy", "entity-index.npy", "flow-scores.npy", "entity-scores.npy", "labels.npy", "sampling-members.json"}
    files = []
    for path in sorted(output_root.rglob("*")):
        if not path.is_file() or path.name.endswith(".partial") or path.name == "manifest.json":
            continue
        if path.name in forbidden:
            raise Q0Failure("EVALUATION_FAILED", f"发现禁止制品：{path.name}", 7)
        files.append({"path": path.relative_to(output_root).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(output_root / "manifest.json", {"schema_version": "ch4-entity-ap-manifest-v1", "file_count": len(files), "files": files, "forbidden_per_sample_artifacts_absent": True})


def publish_aggregate_swanlab(
    config: dict[str, Any],
    aggregate: dict[str, Any],
    output_root: Path,
    tracking_attempt: int,
    authorized_workspace: str,
    authorized_project: str,
) -> dict[str, Any]:
    destination = config["swanlab"]
    if (
        authorized_workspace != destination["workspace"]
        or authorized_project != destination["project"]
    ):
        raise Q0Failure(
            "TRAINING_TRACKING_FAILED", "聚合 SwanLab 目的地不一致", 78
        )
    swanlab, run = swanlab_start(
        config,
        "aggregate",
        f"{destination['group']} 聚合收据",
        output_root,
        tracking_attempt,
        authorized_workspace,
        authorized_project,
        aggregate=True,
    )
    metrics: dict[str, float] = {}
    for cell, result in aggregate["evaluations"].items():
        for name in ("flow_ap", "entity_ap", "entity_dr_at_4pct_fpr", "learned_p"):
            metrics[f"evaluation/{cell}/{name}"] = float(result[name])
    metrics["decision/candidate_advanced"] = float(aggregate["candidate_advanced"])
    metrics["decision/strict_2x2_complete"] = float(aggregate["strict_2x2_complete"])
    try:
        swanlab.log(metrics, step=0)
        run.finish()
    except Exception as error:
        raise Q0Failure(
            "TRAINING_TRACKING_FAILED",
            f"聚合 SwanLab 指标发布或结束失败：{type(error).__name__}: {error}",
            82,
        ) from error
    return {
        "schema_version": "ch4-entity-ap-swanlab-receipt-v1",
        "workspace": authorized_workspace,
        "project": authorized_project,
        "group": destination["group"],
        "active_cells": list(aggregate["evaluations"]),
        "per_cell_online_runs_finished": True,
        "aggregate_online_run_finished": True,
        "aggregate_independent_python_process": True,
        "aggregate_tracking_attempt": tracking_attempt,
        "aggregate_metric_count": len(metrics),
        "aggregate_metrics_source": "aggregate-results.json",
        "credentials_persisted": False,
    }


def validate_authorized_destination(
    config: dict[str, Any], authorized_workspace: str, authorized_project: str
) -> None:
    if (
        authorized_workspace != config["swanlab"]["workspace"]
        or authorized_project != config["swanlab"]["project"]
    ):
        raise Q0Failure("PRECHECK_FAILED", "授权 SwanLab 目的地不一致", 78)


def load_execution_plan(
    config_path: Path, config: dict[str, Any], output_root: Path
) -> dict[str, Any]:
    plan_path = output_root / "execution-plan.json"
    run_config_path = output_root / "config.json"
    if not plan_path.is_file() or not run_config_path.is_file():
        raise Q0Failure("PRECHECK_FAILED", "独立进程执行计划或运行配置缺失", 67)
    plan = read_json(plan_path)
    expected = {
        "run_id": config["run_id"],
        "code_sha256": sha256_file(Path(__file__)),
        "production_config_sha256": sha256_file(config_path),
        "run_config_sha256": sha256_file(run_config_path),
    }
    if any(plan.get(key) != value for key, value in expected.items()):
        raise Q0Failure("PRECHECK_FAILED", "执行计划与当前代码或配置绑定不一致", 65)
    if plan.get("failed_run_artifacts_reused") is not False:
        raise Q0Failure("PRECHECK_FAILED", "rerun2 禁止复用 rerun1 失败制品", 65)
    return plan


def prepare_run(
    config_path: Path, authorized_workspace: str, authorized_project: str
) -> None:
    import torch
    from safetensors.torch import load_file

    config = read_json(config_path)
    validate_config(config)
    validate_authorized_destination(config, authorized_workspace, authorized_project)
    paths = resolved_paths(config)
    output_root = paths["output_root"]
    allowed_launcher_files = {"run.log"}
    existing = (
        {path.name for path in output_root.iterdir()}
        if output_root.exists()
        else set()
    )
    if existing - allowed_launcher_files:
        raise Q0Failure(
            "PRECHECK_FAILED",
            f"rerun2 运行根已有不可覆盖制品：{sorted(existing - allowed_launcher_files)}",
            73,
        )
    output_root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_path, output_root / "config.json")
    write_status(
        output_root,
        "RUNNING",
        "P0_PRECHECK",
        None,
        target_labels_read=False,
        failed_run_artifacts_reused=False,
    )
    dependencies = validate_dependencies(config)
    input_hashes = validate_inputs(config, paths)
    write_json(output_root / "input-hashes.json", input_hashes)
    source = load_source_cache(paths["cache_root"], config)
    index, index_receipt = build_source_entity_index(config, paths, source)
    write_json(output_root / "source-index-receipt.json", index_receipt)
    if not torch.cuda.is_available():
        raise Q0Failure("PRECHECK_FAILED", "正式 Q0 必须使用 CUDA", 69)
    gate_model = create_model(config).to("cuda")
    gate_model.load_state_dict(
        load_file(paths["archived_c11_checkpoint"], device="cuda")
    )
    gate_model.eval()
    gate_result = execute_lp_gate(gate_model, source, index, config, "cuda")
    write_json(output_root / "lp-estimator-gate.json", gate_result)
    initial = initial_state(config)
    active_cells = CELLS if gate_result["passed"] else CELLS[:2]
    plan = {
        "schema_version": "ch4-entity-ap-independent-process-plan-v1",
        "run_id": config["run_id"],
        "code_sha256": sha256_file(Path(__file__)),
        "production_config_sha256": sha256_file(config_path),
        "run_config_sha256": sha256_file(output_root / "config.json"),
        "input_hashes_sha256": sha256_file(output_root / "input-hashes.json"),
        "source_index_receipt_sha256": sha256_file(
            output_root / "source-index-receipt.json"
        ),
        "lp_gate_receipt_sha256": sha256_file(output_root / "lp-estimator-gate.json"),
        "lp_gate_passed": gate_result["passed"],
        "active_cells": [cell[0] for cell in active_cells],
        "common_initial_state_sha256": state_dict_sha256(initial),
        "dependencies": dependencies,
        "orchestrator_imports_swanlab": False,
        "cell_process_contract": "one-cell-one-python-process-one-online-run",
        "aggregate_process_contract": "one-python-process-one-online-run",
        "failed_run_artifacts_reused": False,
        "target_labels_read": False,
        "prepare_peak_rss_mib": peak_rss_mib(),
        "prepare_peak_gpu_memory_mib": float(
            torch.cuda.max_memory_allocated() / 2**20
        ),
    }
    write_json(output_root / "execution-plan.json", plan)
    state = "PREPARED" if gate_result["passed"] else "R1_DISABLED_BY_LP_GATE"
    write_status(
        output_root,
        state,
        "P2_LP_GATE",
        None,
        target_labels_read=False,
        active_cells=plan["active_cells"],
        common_initial_state_sha256=plan["common_initial_state_sha256"],
        failed_run_artifacts_reused=False,
    )
    del gate_model, initial, source, index
    torch.cuda.empty_cache()
    gc.collect()


def execute_cell_worker(
    config_path: Path,
    cell: str,
    tracking_attempt: int,
    authorized_workspace: str,
    authorized_project: str,
) -> None:
    import torch

    config = read_json(config_path)
    validate_config(config)
    validate_authorized_destination(config, authorized_workspace, authorized_project)
    paths = resolved_paths(config)
    output_root = paths["output_root"]
    plan = load_execution_plan(config_path, config, output_root)
    specification = next((value for value in CELLS if value[0] == cell), None)
    if specification is None or cell not in plan["active_cells"]:
        raise Q0Failure("PRECHECK_FAILED", f"单格进程收到非活动格：{cell}", 64)
    if (output_root / "cells" / cell).exists():
        raise Q0Failure(
            f"TRAINING_FAILED_{cell}", f"{cell} 已有训练制品，禁止覆盖或猜测恢复", 73
        )
    validate_tracking_gate(output_root, cell, tracking_attempt)
    write_status(
        output_root,
        "RUNNING",
        f"P3_TRAINING_{cell}",
        None,
        target_labels_read=False,
        active_cell=cell,
        tracking_attempt=tracking_attempt,
        independent_python_process=True,
    )
    source = load_source_cache(paths["cache_root"], config)
    index, rebuilt_receipt = build_source_entity_index(config, paths, source)
    prepared_receipt = read_json(output_root / "source-index-receipt.json")
    stable_keys = (
        "zip_sha256",
        "zip_member",
        "flow_count",
        "entity_count",
        "positive_entity_count",
        "sequence_count",
        "all_flows_assigned_once",
        "sequences_single_entity",
        "derived_index_persisted",
    )
    if any(rebuilt_receipt.get(key) != prepared_receipt.get(key) for key in stable_keys):
        raise Q0Failure(
            f"TRAINING_FAILED_{cell}", "单格重建的源实体索引与准备阶段不一致", 65
        )
    initial = initial_state(config)
    initial_hash = state_dict_sha256(initial)
    if initial_hash != plan["common_initial_state_sha256"]:
        raise Q0Failure(
            f"TRAINING_FAILED_{cell}", "单格共同初始化哈希不一致", 65
        )
    if not torch.cuda.is_available():
        raise Q0Failure(f"TRAINING_FAILED_{cell}", "单格训练必须使用 CUDA", 69)
    _, display_name, entity_uniform, direct_ap = specification
    receipt = train_cell(
        cell,
        display_name,
        entity_uniform,
        direct_ap,
        initial,
        source,
        index,
        config,
        output_root,
        "cuda",
        tracking_attempt,
        authorized_workspace,
        authorized_project,
    )
    write_status(
        output_root,
        "CELL_COMPLETED",
        f"P3_TRAINING_{cell}_COMPLETE",
        None,
        target_labels_read=False,
        active_cell=cell,
        tracking_attempt=tracking_attempt,
        training_receipt_sha256=sha256_file(
            output_root / "cells" / cell / "train-metrics.json"
        ),
        checkpoint_hashes=receipt["checkpoint_hashes"],
    )


def load_training_receipts(
    config: dict[str, Any], output_root: Path, plan: dict[str, Any]
) -> dict[str, Any]:
    training: dict[str, Any] = {}
    expected_steps = {str(step) for step in config["snapshot_steps"]}
    for cell in plan["active_cells"]:
        receipt_path = output_root / "cells" / cell / "train-metrics.json"
        if not receipt_path.is_file():
            raise Q0Failure("SELECTION_SEAL_FAILED", f"{cell} 训练收据缺失", 5)
        receipt = read_json(receipt_path)
        valid = (
            receipt.get("cell") == cell
            and receipt.get("training_steps") == config["training_steps"]
            and receipt.get("common_initial_state_sha256")
            == plan["common_initial_state_sha256"]
            and receipt.get("independent_python_process") is True
            and receipt.get("swanlab_online_run_finished") is True
            and set(receipt.get("checkpoint_hashes", {})) == expected_steps
        )
        if not valid:
            raise Q0Failure(
                "SELECTION_SEAL_FAILED", f"{cell} 训练恢复合同不完整", 5
            )
        for step, expected_hash in receipt["checkpoint_hashes"].items():
            checkpoint = (
                output_root
                / "cells"
                / cell
                / "checkpoints"
                / f"step-{step}.safetensors"
            )
            if not checkpoint.is_file() or sha256_file(checkpoint) != expected_hash:
                raise Q0Failure(
                    "SELECTION_SEAL_FAILED", f"{cell} 检查点 {step} 哈希不一致", 5
                )
        training[cell] = receipt
    return training


def finalize_run(
    config_path: Path, authorized_workspace: str, authorized_project: str
) -> None:
    import torch

    config = read_json(config_path)
    validate_config(config)
    validate_authorized_destination(config, authorized_workspace, authorized_project)
    paths = resolved_paths(config)
    output_root = paths["output_root"]
    plan = load_execution_plan(config_path, config, output_root)
    gate_result = read_json(output_root / "lp-estimator-gate.json")
    training = load_training_receipts(config, output_root, plan)
    encoded_counts = [receipt["encoded_flow_count"] for receipt in training.values()]
    fairness = (max(encoded_counts) - min(encoded_counts)) / min(encoded_counts)
    if fairness > 0.01:
        raise Q0Failure(
            "INVALID_UNFAIR_FLOW_BUDGET", f"有效编码流预算差={fairness:.6f}", 5
        )
    sampling_receipt = {
        "schema_version": "ch4-shared-sampling-receipt-v1",
        "seed": config["seed"],
        "entity_sampler": "sha256(seed,step) stratified 32 positive + 32 negative without replacement within step",
        "flow_sampler": "sha256(seed,step,entity,K) uniform without replacement; stable row order",
        "sampling_list_shared_by_all_cells": True,
        "sampling_members_persisted": False,
        "encoded_flow_counts": {
            cell: receipt["encoded_flow_count"] for cell, receipt in training.items()
        },
        "relative_range": fairness,
        "passed": True,
    }
    write_json(output_root / "sampling-receipt.json", sampling_receipt)
    seal = {
        "schema_version": "ch4-entity-ap-selection-seal-v1",
        "run_id": config["run_id"],
        "code_sha256": plan["code_sha256"],
        "config_sha256": plan["production_config_sha256"],
        "input_hashes_sha256": plan["input_hashes_sha256"],
        "active_cells": plan["active_cells"],
        "common_initial_state_sha256": plan["common_initial_state_sha256"],
        "checkpoint_hashes": {
            cell: receipt["checkpoint_hashes"] for cell, receipt in training.items()
        },
        "selection_basis": "source-only frozen final-five snapshots",
        "selection_steps": config["snapshot_steps"],
        "sampling_receipt_sha256": sha256_file(
            output_root / "sampling-receipt.json"
        ),
        "lp_gate_status": gate_result["status"],
        "entity_batch_size": config["entity_batch_size"],
        "entity_flow_budget": config["entity_flow_budget"],
        "failed_run_artifacts_reused": False,
        "target_labels_read": False,
        "sealed_at_unix": time.time(),
    }
    write_json(output_root / "selection-seal.json", seal)
    if not (output_root / "selection-seal.json").is_file():
        raise Q0Failure("SELECTION_SEAL_FAILED", "选择封存写入失败", 5)
    write_status(
        output_root,
        "RUNNING",
        "P5_TARGET_EVALUATION",
        None,
        target_labels_read=True,
        selection_seal_sha256=sha256_file(output_root / "selection-seal.json"),
    )
    target = {
        key: np.load(
            paths["cache_root"] / f"{name}.npy",
            mmap_mode=None if name in {"s24", "d24"} else "r",
            allow_pickle=name in {"s24", "d24"},
        )
        for key, name in (
            ("x", "X24"),
            ("y", "y24"),
            ("i", "I24"),
            ("m", "M24"),
            ("s", "s24"),
            ("d", "d24"),
        )
    }
    if len(target["y"]) != config["input_contract"]["lspr24_flow_count"]:
        raise Q0Failure("EVALUATION_FAILED", "目标流数不一致", 6)
    if (
        target["x"].shape != (len(target["y"]), config["feature_count"])
        or target["i"].shape != target["m"].shape
        or target["i"].shape[1] != config["sequence_length"]
        or len(target["s"]) != len(target["y"])
        or len(target["d"]) != len(target["y"])
    ):
        raise Q0Failure("EVALUATION_FAILED", "目标缓存形状不一致", 6)
    entity24, labels24, counts24 = build_target_entities(
        target["s"], target["d"], target["y"], config
    )
    evaluations = {
        cell: evaluate_cell(
            cell,
            config,
            output_root,
            target,
            entity24,
            labels24,
            counts24,
            "cuda",
        )
        for cell in plan["active_cells"]
    }
    decision = determine_decision(
        config, evaluations, training, gate_result["passed"]
    )
    if (
        gate_result["passed"]
        and decision["historical_m0r0_absolute_difference"]
        > config["historical_reproduction_tolerance"]
    ):
        raise Q0Failure(
            "EVALUATION_FAILED", "M0R0 与历史 C11 实体 AP 偏差超过 0.020", 6
        )
    aggregate = {
        "schema_version": "ch4-entity-uniform-direct-ap-q0-results-v1",
        "run_id": config["run_id"],
        "status": decision["status"],
        "candidate_advanced": decision["candidate_advanced"],
        "strict_2x2_complete": decision["strict_2x2_complete"],
        "screening_only": True,
        "formal_paper_evidence": False,
        "independent_test": False,
        "target_labels_read_after_selection_seal": True,
        "flow_scores_persisted": False,
        "entity_scores_persisted": False,
        "source_entity_index_persisted": False,
        "failed_run_artifacts_reused": False,
        "random_lp_gate": gate_result["status"],
        "training_receipts": training,
        "evaluations": evaluations,
        "decision": decision,
        "dependencies": plan["dependencies"],
        "limitation": "LSPR24 已被反复观察，本 Q0 不是独立测试或无偏泛化估计，仅用于候选筛选。",
    }
    write_json(output_root / "aggregate-results.json", aggregate)
    write_json(
        output_root / "resource-usage.json",
        {
            "schema_version": "ch4-entity-ap-resource-usage-v1",
            "peak_rss_mib": max(
                peak_rss_mib(),
                plan["prepare_peak_rss_mib"],
                *(receipt["peak_rss_mib"] for receipt in training.values()),
            ),
            "peak_gpu_memory_mib": max(
                float(torch.cuda.max_memory_allocated() / 2**20),
                plan["prepare_peak_gpu_memory_mib"],
                *(receipt["peak_gpu_memory_mib"] for receipt in training.values()),
            ),
            "estimated_peak_rss_gib": config["resource_contract"][
                "estimated_peak_rss_gib"
            ],
            "cells_serial": True,
            "cells_use_independent_python_processes": True,
        },
    )
    write_status(
        output_root,
        "EVALUATION_COMPLETE_PENDING_AGGREGATE_TRACKING",
        "P6_AGGREGATE_TRACKING_PENDING",
        None,
        target_labels_read=True,
        candidate_advanced=decision["candidate_advanced"],
        strict_2x2_complete=decision["strict_2x2_complete"],
    )


def publish_aggregate_phase(
    config_path: Path,
    tracking_attempt: int,
    authorized_workspace: str,
    authorized_project: str,
) -> None:
    config = read_json(config_path)
    validate_config(config)
    validate_authorized_destination(config, authorized_workspace, authorized_project)
    output_root = Path(config["paths"]["output_root"])
    plan = load_execution_plan(config_path, config, output_root)
    load_training_receipts(config, output_root, plan)
    aggregate_path = output_root / "aggregate-results.json"
    if not aggregate_path.is_file():
        raise Q0Failure(
            "TRAINING_TRACKING_FAILED", "聚合发布前缺少评估汇总", 67
        )
    aggregate = read_json(aggregate_path)
    if aggregate.get("run_id") != config["run_id"]:
        raise Q0Failure(
            "TRAINING_TRACKING_FAILED", "聚合汇总运行身份不一致", 65
        )
    receipt = publish_aggregate_swanlab(
        config,
        aggregate,
        output_root,
        tracking_attempt,
        authorized_workspace,
        authorized_project,
    )
    write_json(output_root / "swanlab-receipt.json", receipt)
    write_status(
        output_root,
        aggregate["status"],
        "COMPLETE",
        0,
        target_labels_read=True,
        candidate_advanced=aggregate["candidate_advanced"],
        strict_2x2_complete=aggregate["strict_2x2_complete"],
        aggregate_tracking_attempt=tracking_attempt,
    )
    write_manifest(output_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行第四章实体均匀训练与直接实体 AP 严格 2×2 Q0")
    parser.add_argument("--config", type=Path, help="冻结配置 JSON")
    parser.add_argument("--validate-config", action="store_true", help="仅确定性校验配置，不读取数据、不创建运行、不接触 SwanLab")
    parser.add_argument(
        "--phase",
        choices=("prepare", "cell", "finalize", "publish-aggregate"),
        help="正式包装器调用的独立进程阶段",
    )
    parser.add_argument("--cell", choices=tuple(cell[0] for cell in CELLS))
    parser.add_argument("--tracking-attempt", type=int, choices=(1, 2))
    parser.add_argument("--authorized-swanlab-workspace", help="用户本轮明确授权的 SwanLab 工作区")
    parser.add_argument("--authorized-swanlab-project", help="用户本轮明确授权的 SwanLab 项目")
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    if arguments.config is None:
        raise SystemExit("必须提供 --config")
    if arguments.validate_config:
        validate_config(read_json(arguments.config))
        print("CONFIG_VALID")
        return
    if arguments.phase is None:
        raise SystemExit("正式运行必须由包装器显式提供 --phase")
    if arguments.phase == "cell" and (
        arguments.cell is None or arguments.tracking_attempt is None
    ):
        raise SystemExit("cell 阶段必须提供 --cell 与 --tracking-attempt")
    if arguments.phase == "publish-aggregate" and arguments.tracking_attempt is None:
        raise SystemExit("publish-aggregate 阶段必须提供 --tracking-attempt")
    if arguments.phase in {"prepare", "finalize"} and (
        arguments.cell is not None or arguments.tracking_attempt is not None
    ):
        raise SystemExit("prepare/finalize 阶段不得携带单格跟踪参数")
    if not arguments.authorized_swanlab_workspace or not arguments.authorized_swanlab_project:
        raise SystemExit("正式运行必须显式提供两个 SwanLab 授权参数")
    config: dict[str, Any] | None = None
    output_root: Path | None = None
    try:
        config = read_json(arguments.config)
        validate_config(config)
        output_root = Path(config["paths"]["output_root"])
        if arguments.phase == "prepare":
            prepare_run(
                arguments.config,
                arguments.authorized_swanlab_workspace,
                arguments.authorized_swanlab_project,
            )
        elif arguments.phase == "cell":
            execute_cell_worker(
                arguments.config,
                arguments.cell,
                arguments.tracking_attempt,
                arguments.authorized_swanlab_workspace,
                arguments.authorized_swanlab_project,
            )
        elif arguments.phase == "finalize":
            finalize_run(
                arguments.config,
                arguments.authorized_swanlab_workspace,
                arguments.authorized_swanlab_project,
            )
        else:
            publish_aggregate_phase(
                arguments.config,
                arguments.tracking_attempt,
                arguments.authorized_swanlab_workspace,
                arguments.authorized_swanlab_project,
            )
    except Q0Failure as error:
        if output_root is not None:
            output_root.mkdir(parents=True, exist_ok=True)
            target_labels_read = False
            status_path = output_root / "status.json"
            if status_path.is_file():
                try:
                    target_labels_read = bool(
                        read_json(status_path).get("target_labels_read", False)
                    )
                except (OSError, ValueError, json.JSONDecodeError):
                    target_labels_read = False
            write_status(
                output_root,
                error.state,
                f"{arguments.phase.upper().replace('-', '_')}_FAILED",
                error.exit_code,
                target_labels_read=target_labels_read,
                error_type=type(error).__name__,
                error=str(error),
                traceback=traceback.format_exc(limit=20),
                research_decision_emitted=False,
                tracking_attempt=arguments.tracking_attempt,
                active_cell=arguments.cell,
            )
        log(f"失败状态={error.state}：{error}")
        raise SystemExit(error.exit_code) from error
    except Exception as error:
        state = {
            "prepare": "PRECHECK_FAILED",
            "cell": f"TRAINING_FAILED_{arguments.cell}",
            "finalize": "EVALUATION_FAILED",
            "publish-aggregate": "TRAINING_TRACKING_FAILED",
        }[arguments.phase]
        if output_root is not None:
            output_root.mkdir(parents=True, exist_ok=True)
            target_labels_read = False
            status_path = output_root / "status.json"
            if status_path.is_file():
                try:
                    target_labels_read = bool(
                        read_json(status_path).get("target_labels_read", False)
                    )
                except (OSError, ValueError, json.JSONDecodeError):
                    target_labels_read = False
            write_status(
                output_root,
                state,
                f"{arguments.phase.upper().replace('-', '_')}_FAILED",
                1,
                target_labels_read=target_labels_read,
                error_type=type(error).__name__,
                error=str(error),
                traceback=traceback.format_exc(limit=20),
                research_decision_emitted=False,
                tracking_attempt=arguments.tracking_attempt,
                active_cell=arguments.cell,
            )
        log(f"失败状态={state}：{type(error).__name__}: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
