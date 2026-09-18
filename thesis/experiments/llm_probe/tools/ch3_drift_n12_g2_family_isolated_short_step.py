#!/usr/bin/env python3
"""N12 G2：严格 family 隔离端点、梯度与同预算短步筛查。"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import math
import os
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
import pyarrow.parquet as pq
import torch
from sklearn.metrics import average_precision_score, roc_auc_score
from tokenizers import Tokenizer, models, normalizers, processors, trainers
from torch import Tensor, nn

import ch3_drift_n10_conservative_fusion_pilot as pilot
import ch3_drift_n12_g1_equal3_gradient_screen as g1
import ch3_drift_t17_equal3_auxheads_gradient_base as g0
import neural_precision_runtime as precision


SCHEMA_VERSION = "ch3-drift-n12-g2-family-isolated-short-step-v1"
TASKS = ("MTP", "TPP", "TOV")
BRANCHES = ("char", "subword")
FORBIDDEN_YEARS = tuple(f"T{year}" for year in range(18, 26))


@dataclass(frozen=True)
class InputSpec:
    label: int
    path: Path
    rows: int
    sha256: str


@dataclass(frozen=True)
class FamilyMapping:
    esld_family: Mapping[str, str]
    train_members: Mapping[str, str]
    val_members: Mapping[str, str]
    ambiguous: frozenset[str]
    missing: frozenset[str]


@dataclass(frozen=True)
class FoldSpec:
    index: int
    fit_families: frozenset[str]
    meta_families: frozenset[str]
    train_only_families: frozenset[str]
    val_only_families: frozenset[str]
    fit_train_digests: frozenset[str]
    meta_val_digests: frozenset[str]
    fit_digest: str
    meta_digest: str


@dataclass(frozen=True)
class ShuffledLabels:
    labels: Mapping[str, str]
    offset: int
    digest: str


@dataclass(frozen=True)
class BlockSpec:
    domains: tuple[str, ...]
    digest: str
    batches: int


@dataclass(frozen=True)
class EndpointReceipt:
    tokenizer: Tokenizer
    branches: Mapping[str, pilot.PretrainedBranch]
    optimizers: Mapping[str, Mapping[str, Any]]
    rng_state: Mapping[str, Any]
    receipt: Mapping[str, Any]


@dataclass(frozen=True)
class ProbeReceipt:
    probe: pilot.StaticDual
    receipt: Mapping[str, Any]


@dataclass(frozen=True)
class GradientReceipt:
    values: Mapping[str, Any]
    vectors: Mapping[str, Any]


@dataclass(frozen=True)
class ArmReceipt:
    arm: str
    branch: str
    model_state: Mapping[str, Any]
    receipt: Mapping[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def atomic_torch(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    torch.save(dict(value), partial)
    os.replace(partial, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def state_hash(state: Mapping[str, Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        value = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(np.asarray(value.shape, dtype=np.int64).tobytes())
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def domain_digest(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def raw_to_esld(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().split(".", 1)[0]


def reject_future_values(value: Any) -> None:
    if isinstance(value, str):
        upper = value.upper()
        if any(year in upper for year in FORBIDDEN_YEARS):
            raise ValueError("配置包含禁止的未来年份")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            reject_future_values(str(key))
            reject_future_values(item)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for item in value:
            reject_future_values(item)


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION or config.get("approved_scope") != "t17_strict_family_isolated_short_step_only":
        raise ValueError("G2 配置身份或范围不匹配")
    if config.get("screening_only") is not True or config.get("seed") != 42:
        raise ValueError("G2 必须保持 screening_only 和种子 42")
    if config.get("dataset_revision") != "3b31077020cd1c013d0a75cad51042a2327c4521":
        raise ValueError("数据 revision 不匹配")
    reject_future_values(config)
    if tuple(config["training"]["tasks"]) != TASKS or tuple(config["arms"]) != ("no_update", "mtp_only", "tpp_only", "tov_only", "mtp_tov_equal", "all_equal", "all_unit_norm"):
        raise ValueError("任务或短步臂偏离冻结合同")
    if int(config["training"]["batch_size"]) != 1024 or int(config["training"]["checkpoint_batches"]) != 32:
        raise ValueError("G2 必须使用冻结 1024 批与 32 批块")
    return config


def load_spec(item: Mapping[str, Any], root: Path, description: str) -> InputSpec:
    path = (root / str(item["path"])).resolve()
    if not path.is_file() or sha256_file(path) != str(item["sha256"]):
        raise ValueError(f"{description} 不存在或 SHA-256 不匹配")
    parquet = pq.ParquetFile(path)
    if int(parquet.metadata.num_rows) != int(item["rows"]):
        raise ValueError(f"{description} 行数不匹配")
    return InputSpec(int(item["label"]), path, int(item["rows"]), str(item["sha256"]))


def verify_predecessors(config: Mapping[str, Any], root: Path) -> dict[str, Any]:
    receipts: dict[str, Any] = {}
    for group in ("p0", "g0"):
        for key, hash_key in (("config", "config_sha256"), ("source_code", "source_code_sha256")):
            path = root / str(config[group][key])
            if not path.is_file() or sha256_file(path) != str(config[group][hash_key]):
                raise ValueError(f"{group} {key} 身份不匹配")
            receipts[f"{group}_{key}"] = {"path": str(path), "sha256": str(config[group][hash_key])}
    for branch in BRANCHES:
        item = config["g0"][branch]
        run_dir = root / str(item["run_dir"])
        for name, expected in (("result.json", item["result_sha256"]), ("checkpoint.pt", item["checkpoint_sha256"])):
            path = run_dir / name
            if not path.is_file() or sha256_file(path) != str(expected):
                raise ValueError(f"G0 {branch} {name} 身份不匹配")
        status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
        if status.get("status") != "completed":
            raise ValueError(f"G0 {branch} 未完成")
    g1_config = config["g1"]
    run_dir = root / str(g1_config["run_dir"])
    for key, name in (("config_sha256", "config"), ("script_sha256", "script")):
        path = root / str(g1_config[name])
        if not path.is_file() or sha256_file(path) != str(g1_config[key]):
            raise ValueError(f"G1 {name} 身份不匹配")
    for name, key in (("result.json", "result_sha256"), ("checkpoint.pt", "checkpoint_sha256"), ("status.json", "status_sha256")):
        path = run_dir / name
        if not path.is_file() or sha256_file(path) != str(g1_config[key]):
            raise ValueError(f"G1 {name} 身份不匹配")
    result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    if status.get("status") != "completed" or result.get("gradient_summary", {}).get("g1_verdict") != "eligible_for_g2_only":
        raise ValueError("G1 未提供仅 G2 准入资格")
    receipts["g1"] = {"run_dir": str(run_dir), "result_sha256": g1_config["result_sha256"], "checkpoint_sha256": g1_config["checkpoint_sha256"]}
    return receipts


def iter_domains(spec: InputSpec, allowed: frozenset[str] | None = None) -> Iterator[str]:
    for batch in pq.ParquetFile(spec.path).iter_batches(batch_size=32768, columns=["domain", "label"]):
        frame = batch.to_pydict()
        for domain, label in zip(frame["domain"], frame["label"], strict=True):
            if int(label) != spec.label:
                raise ValueError("输入标签不符合冻结成员")
            value = str(domain).strip().lower()
            if allowed is None or domain_digest(value) in allowed:
                yield value


def build_family_mapping(config: Mapping[str, Any], root: Path) -> FamilyMapping:
    inputs = config["inputs"]
    train_dga = load_spec(inputs["fit"][1], root, "T17 训练 DGA")
    val_dga = load_spec(inputs["validation"][1], root, "T17 验证 DGA")
    raw = load_spec(inputs["raw_dga_family"], root, "T17 raw family")
    train_keys = {domain_digest(value) for value in iter_domains(train_dga)}
    val_keys = {domain_digest(value) for value in iter_domains(val_dga)}
    target = train_keys | val_keys
    mapped: dict[str, set[str]] = {key: set() for key in target}
    seen = 0
    for batch in pq.ParquetFile(raw.path).iter_batches(batch_size=int(config["runtime"]["raw_parquet_batch_rows"]), columns=["domain", "label", "family"]):
        frame = batch.to_pydict()
        seen += batch.num_rows
        for domain, label, family in zip(frame["domain"], frame["label"], frame["family"], strict=True):
            if int(label) != 1:
                raise ValueError("raw family 输入含非 DGA 标签")
            key = domain_digest(raw_to_esld(domain))
            if key in mapped and isinstance(family, str) and family.strip():
                mapped[key].add(family.strip().lower())
    if seen != raw.rows:
        raise RuntimeError("raw family 未完整扫描")
    unique = {key: next(iter(values)) for key, values in mapped.items() if len(values) == 1}
    missing = frozenset(key for key, values in mapped.items() if not values)
    ambiguous = frozenset(key for key, values in mapped.items() if len(values) > 1)
    if missing:
        raise ValueError("family 映射存在缺失 eSLD")
    return FamilyMapping(unique, {key: unique[key] for key in train_keys if key in unique}, {key: unique[key] for key in val_keys if key in unique}, ambiguous, missing)


def build_complementary_folds(mapping: FamilyMapping) -> tuple[FoldSpec, FoldSpec]:
    train_support = Counter(mapping.train_members.values())
    val_support = Counter(mapping.val_members.values())
    shared = sorted(set(train_support) & set(val_support), key=lambda family: (-train_support[family], family.encode("utf-8")))
    if len(shared) < 4:
        raise ValueError("共同 family 少于严格互补折所需最小数量")
    groups = [set(), set()]
    totals = [0, 0]
    for family in shared:
        target = 0 if totals[0] <= totals[1] else 1
        groups[target].add(family)
        totals[target] += train_support[family]
    train_only = frozenset(set(train_support) - set(val_support))
    val_only = frozenset(set(val_support) - set(train_support))
    folds: list[FoldSpec] = []
    for index in range(2):
        fit = frozenset(groups[index]) | train_only
        meta = frozenset(groups[1 - index]) | val_only
        fit_keys = frozenset(key for key, family in mapping.train_members.items() if family in fit)
        meta_keys = frozenset(key for key, family in mapping.val_members.items() if family in meta)
        if not fit_keys or not meta_keys or len(groups[index]) < 2 or fit_keys & meta_keys:
            raise ValueError("严格 family 折为空、共享 family 不足或 eSLD 重叠")
        folds.append(FoldSpec(index, fit, meta, train_only, val_only, fit_keys, meta_keys, canonical_hash(sorted(fit_keys)), canonical_hash(sorted(meta_keys))))
    return tuple(folds)  # type: ignore[return-value]


def build_shuffled_labels(rows: Sequence[tuple[str, str]], config_sha256: str) -> ShuffledLabels:
    ordered = sorted(rows, key=lambda item: item[0])
    if len(ordered) < 2:
        raise ValueError("family 打乱要求至少两个元验证 eSLD")
    offset = 1 + int(config_sha256[:8], 16) % (len(ordered) - 1)
    labels = {key: ordered[(index + offset) % len(ordered)][1] for index, (key, _) in enumerate(ordered)}
    if Counter(labels.values()) != Counter(value for _, value in ordered) or all(labels[key] == value for key, value in ordered):
        raise ValueError("family 打乱未保持频数或未改变对应")
    return ShuffledLabels(labels, offset, canonical_hash({"offset": offset, "labels": labels}))


def iter_fit_batches(benign: InputSpec, dga: InputSpec, allowed: frozenset[str], batch_size: int) -> Iterator[list[str]]:
    benign_stream, dga_stream = iter_domains(benign), iter_domains(dga, allowed)
    while True:
        left = [value for _, value in zip(range(batch_size // 2), benign_stream)]
        right = [value for _, value in zip(range(batch_size // 2), dga_stream)]
        if not left and not right:
            return
        values = left + right
        if not values:
            return
        yield values


def train_tokenizer(fold: FoldSpec, benign: InputSpec, dga: InputSpec, path: Path, config: Mapping[str, Any]) -> Tokenizer:
    if path.is_file():
        return Tokenizer.from_file(str(path))
    tokenizer = Tokenizer(models.WordPiece(unk_token="[UNK]"))
    tokenizer.normalizer = normalizers.Sequence([normalizers.NFD(), normalizers.Lowercase(), normalizers.StripAccents()])
    trainer = trainers.WordPieceTrainer(vocab_size=int(config["pretraining"]["vocab_size_subword_max"]), min_frequency=0, special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"])
    tokenizer.train_from_iterator(iter_fit_batches(benign, dga, fold.fit_train_digests, 8192), trainer=trainer)
    tokenizer.post_processor = processors.TemplateProcessing(single="[CLS]:0 $A:0 [SEP]:0", special_tokens=[("[CLS]", tokenizer.token_to_id("[CLS]")), ("[SEP]", tokenizer.token_to_id("[SEP]"))])
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    tokenizer.save(str(partial))
    os.replace(partial, path)
    return tokenizer


def encode_branch(branch: str, values: list[str], tokenizer: Tokenizer, config: Mapping[str, Any], device: torch.device) -> Tensor:
    if branch == "char":
        return pilot.encode_char_cpu(values, int(config["pretraining"]["max_len_char"])).to(device, non_blocking=device.type == "cuda")
    return pilot.encode_subword_cpu(values, tokenizer, int(config["pretraining"]["max_len_subword"])).to(device, non_blocking=device.type == "cuda")


def train_branch(branch_name: str, branch: pilot.PretrainedBranch, tokenizer: Tokenizer, fold: FoldSpec, benign: InputSpec, dga: InputSpec, config: Mapping[str, Any], profile: Mapping[str, Any], device: torch.device, checkpoint_path: Path, identity: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    optimizer = torch.optim.Adam(branch.parameters(), lr=float(config["training"]["learning_rate"]))
    counts, losses, examples, batches, completed_batches = {task: 0 for task in TASKS}, {task: 0.0 for task in TASKS}, 0, 0, -1
    if checkpoint_path.is_file():
        state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if state.get("identity") != identity or state.get("fold") != fold.index or state.get("branch") != branch_name:
            raise ValueError("折内分支恢复身份不匹配")
        branch.load_state_dict(state["branch_state"], strict=True)
        optimizer.load_state_dict(state["optimizer"])
        counts = {task: int(state["counts"][task]) for task in TASKS}
        losses = {task: float(state["loss_sums"][task]) for task in TASKS}
        examples, batches, completed_batches = int(state["examples"]), int(state["batches"]), int(state["completed_batches"])
        pilot.restore_rng_state(state["rng_state"])
        if state.get("stage") == "completed":
            return optimizer.state_dict(), {"examples": examples, "batches": batches, "valid_supervision": counts, "mean_batch_loss": {task: losses[task] / max(batches, 1) for task in TASKS}, "resumed_completed": True}
    for index, values in enumerate(iter_fit_batches(benign, dga, fold.fit_train_digests, int(config["training"]["batch_size"]))):
        if index <= completed_batches:
            continue
        ids = encode_branch(branch_name, values, tokenizer, config, device)
        views = tuple(value.to(device, non_blocking=device.type == "cuda") for value in pilot.pretraining_views(ids.detach().cpu(), 42 + index, int(config["pretraining"]["ignore_index"]), float(config["pretraining"]["mask_ratio"]), float(config["pretraining"]["shuffle_probability"])))
        optimizer.zero_grad(set_to_none=True)
        with precision.autocast_context(profile, device.type, torch):
            total, task_losses, valid = g0.task_losses(branch, views, int(config["pretraining"]["ignore_index"]))
        if not torch.isfinite(total) or any(valid[task] <= 0 for task in TASKS):
            raise FloatingPointError("折内预训练损失或有效监督无效")
        total.float().backward()
        norm = torch.nn.utils.clip_grad_norm_(branch.parameters(), float(config["training"]["gradient_clip_norm"]))
        if not torch.isfinite(norm):
            raise FloatingPointError("折内预训练梯度非有限")
        optimizer.step()
        examples += len(values)
        batches += 1
        completed_batches = index
        for task in TASKS:
            counts[task] += valid[task]
            losses[task] += float(task_losses[task].detach().float().cpu())
        if (index + 1) % int(config["training"]["checkpoint_batches"]) == 0:
            atomic_torch(checkpoint_path, {"identity": dict(identity), "stage": "running", "fold": fold.index, "branch": branch_name, "branch_state": branch.state_dict(), "optimizer": optimizer.state_dict(), "rng_state": pilot.capture_rng_state(), "examples": examples, "batches": batches, "completed_batches": completed_batches, "counts": counts, "loss_sums": losses})
    if any(counts[task] <= 0 for task in TASKS):
        raise ValueError("折内预训练缺少任务有效监督")
    atomic_torch(checkpoint_path, {"identity": dict(identity), "stage": "completed", "fold": fold.index, "branch": branch_name, "branch_state": branch.state_dict(), "optimizer": optimizer.state_dict(), "rng_state": pilot.capture_rng_state(), "examples": examples, "batches": batches, "completed_batches": completed_batches, "counts": counts, "loss_sums": losses})
    return optimizer.state_dict(), {"examples": examples, "batches": batches, "valid_supervision": counts, "mean_batch_loss": {task: losses[task] / max(batches, 1) for task in TASKS}}


def train_fold_endpoint(fold: FoldSpec, branch: str | None, root: Path, run_dir: Path, config: Mapping[str, Any], p0_config: Mapping[str, Any], inputs: Mapping[str, InputSpec], device: torch.device, profile: Mapping[str, Any], checkpoint_path: Path, identity: Mapping[str, Any]) -> EndpointReceipt:
    del branch
    tokenizer = train_tokenizer(fold, inputs["fit_benign"], inputs["fit_dga"], run_dir / f"fold-{fold.index}" / "tokenizer.json", config)
    pilot.set_seed(42)
    model = pilot.build_static(dict(p0_config), tokenizer.get_vocab_size()).to(device)
    char_optimizer, char_receipt = train_branch("char", model.char, tokenizer, fold, inputs["fit_benign"], inputs["fit_dga"], config, profile, device, run_dir / f"fold-{fold.index}-char-pretrain.pt", identity)
    after_char = pilot.capture_rng_state()
    pilot.restore_rng_state(after_char)
    token_optimizer, token_receipt = train_branch("subword", model.token, tokenizer, fold, inputs["fit_benign"], inputs["fit_dga"], config, profile, device, run_dir / f"fold-{fold.index}-subword-pretrain.pt", identity)
    return EndpointReceipt(tokenizer, {"char": model.char, "subword": model.token}, {"char": char_optimizer, "subword": token_optimizer}, pilot.capture_rng_state(), {"fold": fold.index, "char": char_receipt, "subword": token_receipt, "tokenizer_sha256": sha256_file(run_dir / f"fold-{fold.index}" / "tokenizer.json")})


def load_endpoint(path: Path, fold: FoldSpec, run_dir: Path, p0_config: Mapping[str, Any], identity: Mapping[str, Any], device: torch.device) -> EndpointReceipt:
    state = torch.load(path, map_location="cpu", weights_only=False)
    if state.get("identity") != identity or state.get("fold") != fold.index:
        raise ValueError("折端点恢复身份不匹配")
    tokenizer = Tokenizer.from_file(str(run_dir / f"fold-{fold.index}" / "tokenizer.json"))
    model = pilot.build_static(dict(p0_config), tokenizer.get_vocab_size()).to(device)
    model.char.load_state_dict(state["branches"]["char"], strict=True)
    model.token.load_state_dict(state["branches"]["subword"], strict=True)
    return EndpointReceipt(tokenizer, {"char": model.char, "subword": model.token}, state["optimizers"], state["rng_state"], state["receipt"])


def build_probe(endpoint: EndpointReceipt, p0_config: Mapping[str, Any], device: torch.device) -> pilot.StaticDual:
    pilot.set_seed(42)
    return pilot.StaticDual(pilot.EncoderBranch(endpoint.branches["subword"]), pilot.EncoderBranch(endpoint.branches["char"]), int(p0_config["model"]["d_model"]), float(p0_config["model"]["dropout"])).to(device)


def train_frozen_encoder_probe(fold: FoldSpec, endpoint: EndpointReceipt, p0_config: Mapping[str, Any], inputs: Mapping[str, InputSpec], config: Mapping[str, Any], device: torch.device, profile: Mapping[str, Any]) -> ProbeReceipt:
    probe = build_probe(endpoint, p0_config, device)
    g1.set_encoder_requires_grad(probe, False)
    g1.set_probe_training_mode(probe)
    optimizer = torch.optim.Adam(probe.classifier.parameters(), lr=float(config["probe"]["learning_rate"]))
    seen, losses = 0, 0.0
    for values in iter_fit_batches(inputs["fit_benign"], inputs["fit_dga"], fold.fit_train_digests, int(config["probe"]["batch_size"])):
        labels = torch.tensor([0] * min(len(values), int(config["probe"]["batch_size"]) // 2) + [1] * max(0, len(values) - int(config["probe"]["batch_size"]) // 2), dtype=torch.long, device=device)
        token = encode_branch("subword", values, endpoint.tokenizer, config, device)
        char = encode_branch("char", values, endpoint.tokenizer, config, device)
        optimizer.zero_grad(set_to_none=True)
        with precision.autocast_context(profile, device.type, torch):
            loss = nn.functional.cross_entropy(probe(token, char).float(), labels)
        if not torch.isfinite(loss):
            raise FloatingPointError("折内检测探针损失非有限")
        loss.backward()
        optimizer.step()
        seen += len(values)
        losses += float(loss.detach().cpu())
    return ProbeReceipt(probe, {"examples": seen, "mean_loss": losses / max(seen, 1)})


def vector_ops(values: Mapping[str, Tensor]) -> dict[str, float]:
    norm = math.sqrt(sum(float(torch.sum(value.detach().double().square()).cpu()) for value in values.values()))
    return {"l2_norm": norm, "finite": all(bool(torch.isfinite(value).all()) for value in values.values())}


def vector_dot(left: Mapping[str, Tensor], right: Mapping[str, Tensor]) -> float:
    return sum(float(torch.sum(left[key].detach().double() * right[key].detach().double()).cpu()) for key in left)


def pair_metrics(left: Mapping[str, Tensor], right: Mapping[str, Tensor]) -> dict[str, float]:
    left_norm, right_norm = vector_ops(left)["l2_norm"], vector_ops(right)["l2_norm"]
    dot = vector_dot(left, right)
    return {"raw_dot": dot, "left_l2_norm": left_norm, "right_l2_norm": right_norm, "cosine": dot / max(left_norm * right_norm, 1e-30)}


def shared_parameters(branch: pilot.PretrainedBranch) -> list[tuple[str, Tensor]]:
    values = [(name, parameter) for name, parameter in branch.named_parameters() if not name.startswith(("mtp_head", "tpp_head", "tov_head"))]
    if not values:
        raise ValueError("共享编码器参数为空")
    return values


def compute_fold_gradients(fold: FoldSpec, branch: str, endpoint: EndpointReceipt, probe_receipt: ProbeReceipt, inputs: Mapping[str, InputSpec], mapping: FamilyMapping, config: Mapping[str, Any], device: torch.device, profile: Mapping[str, Any]) -> GradientReceipt:
    encoder = endpoint.branches[branch]
    encoder.train()
    for parameter in encoder.parameters():
        parameter.requires_grad_(True)
    parameters = shared_parameters(encoder)
    tasks = {task: {name: torch.zeros_like(parameter, dtype=torch.float32, device="cpu") for name, parameter in parameters} for task in TASKS}
    counts = {task: 0 for task in TASKS}
    for index, values in enumerate(iter_fit_batches(inputs["fit_benign"], inputs["fit_dga"], fold.fit_train_digests, int(config["training"]["batch_size"]))):
        ids = encode_branch(branch, values, endpoint.tokenizer, config, device)
        views = tuple(value.to(device) for value in pilot.pretraining_views(ids.detach().cpu(), 42 + index, int(config["pretraining"]["ignore_index"]), float(config["pretraining"]["mask_ratio"]), float(config["pretraining"]["shuffle_probability"])))
        with precision.autocast_context(profile, device.type, torch):
            _, losses, valid = g0.task_losses(encoder, views, int(config["pretraining"]["ignore_index"]))
        for position, task in enumerate(TASKS):
            gradients = torch.autograd.grad(losses[task].float() * valid[task], [parameter for _, parameter in parameters], retain_graph=position < len(TASKS) - 1)
            for (name, _), value in zip(parameters, gradients, strict=True):
                tasks[task][name].add_(value.detach().float().cpu())
            counts[task] += valid[task]
    task_vectors = {task: {name: value / counts[task] for name, value in vector.items()} for task, vector in tasks.items()}
    risk_vectors: dict[str, dict[str, Tensor]] = {}
    probe = probe_receipt.probe
    probe.eval()
    for parameter in probe.classifier.parameters():
        parameter.requires_grad_(False)
    for name, module in (("char", probe.char), ("subword", probe.token)):
        for parameter in module.parameters():
            parameter.requires_grad_(name == branch)
    for risk in ("benign_bce", "dga_micro_bce", "dga_family_macro_bce"):
        sums = {name: torch.zeros_like(parameter, dtype=torch.float32, device="cpu") for name, parameter in parameters}
        units = 0
        allowed = None if risk == "benign_bce" else fold.meta_val_digests
        spec = inputs["val_benign"] if risk == "benign_bce" else inputs["val_dga"]
        supports = Counter(mapping.val_members[key] for key in fold.meta_val_digests)
        for values in [list(chunk) for chunk in _chunks(iter_domains(spec, allowed), int(config["training"]["batch_size"]))]:
            if not values:
                continue
            token, char = encode_branch("subword", values, endpoint.tokenizer, config, device), encode_branch("char", values, endpoint.tokenizer, config, device)
            logits = probe(token, char).float()
            label = 0 if risk == "benign_bce" else 1
            losses = nn.functional.cross_entropy(logits, torch.full((len(values),), label, dtype=torch.long, device=device), reduction="none")
            if risk == "dga_family_macro_bce":
                weights = torch.tensor([1.0 / supports[mapping.val_members[domain_digest(value)]] for value in values], device=device)
                total, units = torch.sum(losses * weights), len(supports)
            else:
                total, units = torch.sum(losses), units + len(values)
            gradients = torch.autograd.grad(total, [parameter for _, parameter in parameters])
            for (name, _), value in zip(parameters, gradients, strict=True):
                sums[name].add_(value.detach().float().cpu())
        risk_vectors[risk] = {name: value / max(units, 1) for name, value in sums.items()}
    summary = {"tasks": {task: {"metrics": vector_ops(value), "valid_supervision": counts[task]} for task, value in task_vectors.items()}, "risks": {risk: vector_ops(value) for risk, value in risk_vectors.items()}, "alignment": {risk: {task: pair_metrics(risk_vectors[risk], task_vectors[task]) for task in TASKS} for risk in risk_vectors}, "pairwise": {f"{left}__{right}": pair_metrics(task_vectors[left], task_vectors[right]) for left, right in (("MTP", "TPP"), ("MTP", "TOV"), ("TPP", "TOV"))}}
    return GradientReceipt(summary, {"tasks": task_vectors, "risks": risk_vectors})


def _chunks(values: Iterator[str], size: int) -> Iterator[tuple[str, ...]]:
    pending: list[str] = []
    for value in values:
        pending.append(value)
        if len(pending) == size:
            yield tuple(pending)
            pending = []
    if pending:
        yield tuple(pending)


def fixed_block(fold: FoldSpec, inputs: Mapping[str, InputSpec], config: Mapping[str, Any]) -> BlockSpec:
    batches = tuple(itertools.islice(iter_fit_batches(inputs["fit_benign"], inputs["fit_dga"], fold.fit_train_digests, int(config["training"]["batch_size"])), int(config["training"]["checkpoint_batches"])))
    if len(batches) != int(config["training"]["checkpoint_batches"]) or any(len(batch) != int(config["training"]["batch_size"]) for batch in batches):
        raise ValueError("严格短步未取得 32 个完整冻结批")
    domains = tuple(value for batch in batches for value in batch)
    return BlockSpec(domains, canonical_hash([domain_digest(value) for value in domains]), len(batches))


def run_short_step_arm(fold: FoldSpec, branch: str, arm: str, endpoint: EndpointReceipt, block: BlockSpec, config: Mapping[str, Any], device: torch.device, profile: Mapping[str, Any]) -> ArmReceipt:
    model = copy.deepcopy(endpoint.branches[branch]).to(device)
    model.train()
    for name, parameter in model.named_parameters():
        parameter.requires_grad_(not name.startswith(("mtp_head", "tpp_head", "tov_head")))
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config["training"]["learning_rate"]))
    optimizer.load_state_dict(copy.deepcopy(endpoint.optimizers[branch]))
    pilot.restore_rng_state(dict(endpoint.rng_state))
    start_hash = state_hash(model.state_dict())
    step_receipts: list[dict[str, Any]] = []
    for index in range(block.batches):
        values = list(block.domains[index * 1024 : (index + 1) * 1024])
        ids = encode_branch(branch, values, endpoint.tokenizer, config, device)
        views = tuple(value.to(device) for value in pilot.pretraining_views(ids.detach().cpu(), 42 + index, int(config["pretraining"]["ignore_index"]), float(config["pretraining"]["mask_ratio"]), float(config["pretraining"]["shuffle_probability"])))
        optimizer.zero_grad(set_to_none=True)
        with precision.autocast_context(profile, device.type, torch):
            _, losses, valid = g0.task_losses(model, views, int(config["pretraining"]["ignore_index"]))
        if arm == "no_update":
            step_receipts.append({"valid": valid, "optimizer_step": False})
            continue
        if arm == "all_unit_norm":
            parameters = [parameter for _, parameter in shared_parameters(model)]
            accumulated = [torch.zeros_like(parameter) for parameter in parameters]
            for position, task in enumerate(TASKS):
                gradients = torch.autograd.grad(losses[task].float(), parameters, retain_graph=position < 2)
                norm = math.sqrt(sum(float(value.detach().double().square().sum().cpu()) for value in gradients))
                for target, value in zip(accumulated, gradients, strict=True):
                    target.add_(value / max(norm, 1e-30))
            for parameter, value in zip(parameters, accumulated, strict=True):
                parameter.grad = value
        else:
            selected = {"mtp_only": ("MTP",), "tpp_only": ("TPP",), "tov_only": ("TOV",), "mtp_tov_equal": ("MTP", "TOV"), "all_equal": TASKS}[arm]
            sum(losses[task].float() for task in selected).backward()
        before = float(torch.nn.utils.clip_grad_norm_(model.parameters(), float(config["training"]["gradient_clip_norm"])))
        if not math.isfinite(before):
            raise FloatingPointError("短步梯度非有限")
        optimizer.step()
        step_receipts.append({"valid": valid, "optimizer_step": True, "pre_clip_norm": before})
    end_hash = state_hash(model.state_dict())
    return ArmReceipt(arm, branch, model.state_dict(), {"fold": fold.index, "branch": branch, "arm": arm, "batches": block.batches, "samples": len(block.domains), "block_sha256": block.digest, "start_model_sha256": start_hash, "end_model_sha256": end_hash, "steps": step_receipts})


def frozen_fit_threshold(endpoint: EndpointReceipt, probe_receipt: ProbeReceipt, fold: FoldSpec, inputs: Mapping[str, InputSpec], config: Mapping[str, Any], device: torch.device) -> float:
    probe = probe_receipt.probe.eval()
    scores: list[float] = []
    for values in _chunks(iter_domains(inputs["fit_benign"]), int(config["probe"]["batch_size"])):
        with torch.no_grad():
            token = encode_branch("subword", list(values), endpoint.tokenizer, config, device)
            char = encode_branch("char", list(values), endpoint.tokenizer, config, device)
            scores.extend(torch.softmax(probe(token, char).float(), dim=1)[:, 1].cpu().tolist())
    if not scores:
        raise ValueError("拟合侧良性阈值成员为空")
    permitted = int(math.floor(len(scores) * float(config["evaluation"]["source_fpr"])))
    raw = np.sort(np.asarray(scores, dtype=np.float64))[::-1][max(permitted - 1, 0)]
    return float(np.nextafter(raw, np.inf))


def evaluate_arm(arm: ArmReceipt, endpoint: EndpointReceipt, base_probe: ProbeReceipt, fold: FoldSpec, inputs: Mapping[str, InputSpec], mapping: FamilyMapping, shuffled: ShuffledLabels, p0_config: Mapping[str, Any], config: Mapping[str, Any], device: torch.device, profile: Mapping[str, Any], threshold: float, refit: bool) -> dict[str, Any]:
    branches = {name: copy.deepcopy(value).to(device) for name, value in endpoint.branches.items()}
    branches[arm.branch].load_state_dict(arm.model_state, strict=True)
    armed_endpoint = EndpointReceipt(endpoint.tokenizer, branches, endpoint.optimizers, endpoint.rng_state, endpoint.receipt)
    probe = build_probe(armed_endpoint, p0_config, device)
    probe.classifier.load_state_dict(base_probe.probe.classifier.state_dict(), strict=True)
    if refit:
        receipt = train_frozen_encoder_probe(fold, armed_endpoint, p0_config, inputs, config, device, profile)
        probe = receipt.probe
    probe.eval()
    records: list[tuple[float, int, str | None, str]] = []
    for spec, allowed, family_mode in ((inputs["val_benign"], None, None), (inputs["val_dga"], fold.meta_val_digests, "real")):
        for values in _chunks(iter_domains(spec, allowed), int(config["probe"]["batch_size"])):
            with torch.no_grad():
                token, char = encode_branch("subword", list(values), endpoint.tokenizer, config, device), encode_branch("char", list(values), endpoint.tokenizer, config, device)
                probability = torch.softmax(probe(token, char).float(), dim=1)[:, 1].cpu().numpy()
            for value, score in zip(values, probability, strict=True):
                key = domain_digest(value)
                records.append((float(score), spec.label, mapping.val_members.get(key) if family_mode else None, key))
    scores = np.asarray([item[0] for item in records], dtype=np.float64)
    labels = np.asarray([item[1] for item in records], dtype=np.int64)
    predicted = scores >= threshold
    probability_default = scores >= 0.5
    negative, positive = labels == 0, labels == 1
    family_losses: dict[str, list[float]] = defaultdict(list)
    shuffled_losses: dict[str, list[float]] = defaultdict(list)
    for score, label, family, key in records:
        if label == 1 and family is not None:
            value = -math.log(max(score, 1e-12))
            family_losses[family].append(value)
            shuffled_losses[shuffled.labels[key]].append(value)
    macro = float(np.mean([np.mean(values) for values in family_losses.values()]))
    shuffled_macro = float(np.mean([np.mean(values) for values in shuffled_losses.values()]))
    boundaries = np.linspace(0.0, 1.0, int(config["evaluation"]["ece_bins"]) + 1)
    ece = sum(float(np.mean((scores >= lower) & ((scores <= upper) if index == len(boundaries) - 2 else (scores < upper))) * abs(scores[((scores >= lower) & ((scores <= upper) if index == len(boundaries) - 2 else (scores < upper)))].mean() - labels[((scores >= lower) & ((scores <= upper) if index == len(boundaries) - 2 else (scores < upper)))].mean())) for index, (lower, upper) in enumerate(zip(boundaries[:-1], boundaries[1:], strict=True)) if np.any((scores >= lower) & ((scores <= upper) if index == len(boundaries) - 2 else (scores < upper))))
    return {"probe_mode": "refit_probe_attachment" if refit else "frozen_probe", "threshold": threshold, "benign_bce": float(np.mean([-math.log(max(1.0 - score, 1e-12)) for score, label, _, _ in records if label == 0])), "dga_micro_bce": float(np.mean([-math.log(max(score, 1e-12)) for score, label, _, _ in records if label == 1])), "dga_family_macro_bce": macro, "dga_family_macro_bce_shuffled": shuffled_macro, "default": {"fpr": float(probability_default[negative].mean()), "fnr": float((~probability_default[positive]).mean()), "tpr": float(probability_default[positive].mean()), "precision": float(labels[probability_default].mean()) if probability_default.any() else 0.0, "recall": float(probability_default[positive].mean())}, "source_fpr": {"fpr": float(predicted[negative].mean()), "tpr": float(predicted[positive].mean())}, "average_precision": float(average_precision_score(labels, scores)), "auroc": float(roc_auc_score(labels, scores)), "brier": float(np.mean((scores - labels) ** 2)), "ece": {"bins": int(config["evaluation"]["ece_bins"]), "value": float(ece)}, "prediction_rows": len(records)}


def _strict_order(values: Mapping[str, float]) -> tuple[str, ...] | None:
    if any(not math.isfinite(value) for value in values.values()) or len(set(values.values())) != len(values):
        return None
    return tuple(sorted(values, key=lambda key: values[key]))


def _metric_complete(metric: Mapping[str, Any]) -> bool:
    required = ("benign_bce", "dga_micro_bce", "dga_family_macro_bce", "dga_family_macro_bce_shuffled", "average_precision", "auroc", "brier")
    return all(isinstance(metric.get(key), (int, float)) and math.isfinite(float(metric[key])) for key in required) and all(isinstance(metric.get(section, {}).get(key), (int, float)) and math.isfinite(float(metric[section][key])) for section, key in (("default", "fpr"), ("default", "fnr"), ("default", "recall"), ("default", "precision"), ("source_fpr", "fpr"), ("source_fpr", "tpr"), ("ece", "value")))


def adjudicate_g2(result: Mapping[str, Any]) -> str:
    folds = result.get("folds_results", {})
    evidence: dict[str, Any] = {"task_direction": {}, "local_harm": {}, "family_specificity": {}, "equal_improvable": {}, "operational_complete": True}
    if set(folds) != {"0", "1"}:
        evidence["operational_complete"] = False
        if isinstance(result, dict):
            result["adjudication"] = evidence
        return "invalid_g2_metrics"
    for fold in folds.values():
        for branch in BRANCHES:
            for arm in fold["branches"][branch]["arms"].values():
                if not _metric_complete(arm["frozen_probe"]):
                    evidence["operational_complete"] = False
    if not evidence["operational_complete"]:
        if isinstance(result, dict):
            result["adjudication"] = evidence
        return "invalid_g2_metrics"
    harmful: list[tuple[str, str, str]] = []
    for branch in BRANCHES:
        for risk in ("benign_bce", "dga_micro_bce", "dga_family_macro_bce"):
            by_task = {task: [float(folds[str(index)]["branches"][branch]["gradients"]["alignment"][risk][task]["cosine"]) for index in range(2)] for task in TASKS}
            negative = [task for task, values in by_task.items() if all(value < 0.0 for value in values)]
            nonnegative = [task for task, values in by_task.items() if all(value >= 0.0 for value in values)]
            passed = bool(negative and nonnegative)
            evidence["task_direction"][f"{branch}:{risk}"] = {"cosines": by_task, "passed": passed}
            harmful.extend((branch, task, risk) for task in negative if passed)
    if not harmful:
        if isinstance(result, dict):
            result["adjudication"] = evidence
        return "rejected_after_g2_no_stable_direction"
    local_pass = False
    relevant_branches: set[str] = set()
    for branch, task, risk in harmful:
        deltas = []
        for index in range(2):
            arms = folds[str(index)]["branches"][branch]["arms"]
            current, baseline = arms[task.lower() + "_only"]["frozen_probe"], arms["no_update"]["frozen_probe"]
            other = "dga_family_macro_bce" if risk == "benign_bce" else "benign_bce"
            deltas.append({"risk": float(current[risk] - baseline[risk]), "other": float(current[other] - baseline[other])})
        passed = all(item["risk"] > 0.0 and item["other"] >= 0.0 for item in deltas)
        evidence["local_harm"][f"{branch}:{task}:{risk}"] = {"deltas": deltas, "passed": passed}
        local_pass = local_pass or passed
        if passed:
            relevant_branches.add(branch)
    if not local_pass:
        if isinstance(result, dict):
            result["adjudication"] = evidence
        return "rejected_after_g2_no_local_harm"
    evidence["family_specificity"]["relevant_branches"] = sorted(relevant_branches)
    family_pass = False
    for branch in sorted(relevant_branches):
        real_orders, shuffled_orders = [], []
        for index in range(2):
            arms = folds[str(index)]["branches"][branch]["arms"]
            baseline = arms["no_update"]["frozen_probe"]
            real = {task: float(arms[task.lower() + "_only"]["frozen_probe"]["dga_family_macro_bce"] - baseline["dga_family_macro_bce"]) for task in TASKS}
            shuffled = {task: float(arms[task.lower() + "_only"]["frozen_probe"]["dga_family_macro_bce_shuffled"] - baseline["dga_family_macro_bce_shuffled"]) for task in TASKS}
            real_orders.append(_strict_order(real))
            shuffled_orders.append(_strict_order(shuffled))
        passed = real_orders[0] is not None and real_orders[0] == real_orders[1] and not (shuffled_orders[0] == real_orders[0] and shuffled_orders[1] == real_orders[0])
        evidence["family_specificity"][branch] = {"real_orders": real_orders, "shuffled_orders": shuffled_orders, "passed": passed}
        family_pass = family_pass or passed
    if not family_pass:
        if isinstance(result, dict):
            result["adjudication"] = evidence
        return "rejected_after_g2_no_family_specificity"
    equal_pass = False
    for branch in BRANCHES:
        comparisons = {}
        for arm_name in ("mtp_only", "tpp_only", "tov_only", "mtp_tov_equal", "all_unit_norm"):
            fold_passes = []
            for index in range(2):
                arms = folds[str(index)]["branches"][branch]["arms"]
                candidate, equal = arms[arm_name]["frozen_probe"], arms["all_equal"]["frozen_probe"]
                fold_passes.append(candidate["dga_family_macro_bce"] <= equal["dga_family_macro_bce"] and candidate["benign_bce"] <= equal["benign_bce"] and (candidate["dga_family_macro_bce"] < equal["dga_family_macro_bce"] or candidate["benign_bce"] < equal["benign_bce"]))
            comparisons[arm_name] = fold_passes
            equal_pass = equal_pass or all(fold_passes)
        evidence["equal_improvable"][branch] = comparisons
    if isinstance(result, dict):
        result["adjudication"] = evidence
    return "eligible_for_two_block_activity_probe_only" if equal_pass else "rejected_after_g2_equal_not_improvable"


def manifest(run_dir: Path, root: Path, config_path: Path) -> dict[str, Any]:
    paths = [config_path, Path(__file__).resolve(), root / "scripts/remote_launchers/run_ch3_drift_n12_g2_family_isolated_short_step_v1.sh"]
    entries = [{"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size} for path in paths if path.is_file()]
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "status.json"}:
            entries.append({"path": str(path.relative_to(run_dir)), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    return {"schema_version": SCHEMA_VERSION, "files": entries}


def main() -> int:
    args = parse_args()
    root, run_dir, config_path = args.project_root.resolve(), args.run_dir.resolve(), args.config.resolve()
    config = load_config(config_path)
    if run_dir.name != config["run_identity"]:
        raise ValueError("运行目录与 G2 身份不一致")
    if run_dir.exists() and not args.resume:
        raise FileExistsError("运行目录已存在；只允许 --resume")
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path, checkpoint_path = run_dir / "status.json", run_dir / "checkpoint.pt"
    started = time.monotonic()
    atomic_json(status_path, {"status": "running", "stage": "verify"})
    try:
        predecessors = verify_predecessors(config, root)
        inputs = {"fit_benign": load_spec(config["inputs"]["fit"][0], root, "fit benign"), "fit_dga": load_spec(config["inputs"]["fit"][1], root, "fit dga"), "val_benign": load_spec(config["inputs"]["validation"][0], root, "val benign"), "val_dga": load_spec(config["inputs"]["validation"][1], root, "val dga")}
        p0_config = pilot.load_config(root / str(config["p0"]["config"]), root)
        device = pilot.device_for_run()
        contract_path = root / str(config["runtime"]["precision_contract"])
        if sha256_file(contract_path) != str(config["runtime"]["precision_contract_sha256"]):
            raise ValueError("精度合同哈希不匹配")
        contract = precision.load_and_validate_contract(contract_path)
        profile_id = precision.profile_for_device(contract, device.type)
        if device.type == "cuda" and profile_id != config["runtime"]["precision_profile"]:
            raise ValueError("实际精度 profile 偏离冻结配置")
        profile = precision.validate_runtime_profile(contract, profile_id, device.type, torch)
        torch.set_float32_matmul_precision("high")
        mapping = build_family_mapping(config, root)
        folds = build_complementary_folds(mapping)
        config_hash = sha256_file(config_path)
        fold_manifest = {"folds": [{"index": fold.index, "fit_families": sorted(fold.fit_families), "meta_families": sorted(fold.meta_families), "train_only_families": sorted(fold.train_only_families), "val_only_families": sorted(fold.val_only_families), "fit_digest": fold.fit_digest, "meta_digest": fold.meta_digest, "fit_meta_overlap": len(fold.fit_train_digests & fold.meta_val_digests)} for fold in folds], "ambiguous_esld_keys": len(mapping.ambiguous), "missing_esld_keys": len(mapping.missing)}
        atomic_json(run_dir / "fold-manifest.json", fold_manifest)
        identity = {"config_sha256": config_hash, "script_sha256": sha256_file(Path(__file__).resolve()), "inputs": [item.sha256 for item in inputs.values()], "predecessors": predecessors}
        atomic_json(run_dir / "effective-config.json", {"config": config, "identity": identity, "precision_profile": profile_id})
        all_results: dict[str, Any] = {}
        for fold in folds:
            endpoint_path = run_dir / f"fold-{fold.index}-endpoint.pt"
            if args.resume and endpoint_path.is_file():
                endpoint = load_endpoint(endpoint_path, fold, run_dir, p0_config, identity, device)
            else:
                endpoint = train_fold_endpoint(fold, None, root, run_dir, config, p0_config, inputs, device, profile, checkpoint_path, identity)
                atomic_torch(endpoint_path, {"identity": identity, "fold": fold.index, "branches": {name: value.state_dict() for name, value in endpoint.branches.items()}, "optimizers": endpoint.optimizers, "rng_state": endpoint.rng_state, "receipt": endpoint.receipt})
            probe_path = run_dir / f"fold-{fold.index}-probe.pt"
            if args.resume and probe_path.is_file():
                probe_state = torch.load(probe_path, map_location="cpu", weights_only=False)
                if probe_state.get("identity") != identity:
                    raise ValueError("检测探针恢复身份不匹配")
                restored = build_probe(endpoint, p0_config, device)
                restored.classifier.load_state_dict(probe_state["classifier"], strict=True)
                probe = ProbeReceipt(restored, probe_state["receipt"])
            else:
                probe = train_frozen_encoder_probe(fold, endpoint, p0_config, inputs, config, device, profile)
                atomic_torch(probe_path, {"identity": identity, "classifier": probe.probe.classifier.state_dict(), "receipt": probe.receipt})
            val_rows = [(key, family) for key, family in mapping.val_members.items() if key in fold.meta_val_digests]
            shuffled = build_shuffled_labels(val_rows, config_hash)
            block = fixed_block(fold, inputs, config)
            threshold = frozen_fit_threshold(endpoint, probe, fold, inputs, config, device)
            branch_results: dict[str, Any] = {}
            for branch in BRANCHES:
                gradient_path = run_dir / f"fold-{fold.index}-{branch}-gradients.pt"
                if args.resume and gradient_path.is_file():
                    gradient_state = torch.load(gradient_path, map_location="cpu", weights_only=False)
                    if gradient_state.get("identity") != identity:
                        raise ValueError("梯度恢复身份不匹配")
                    gradients = GradientReceipt(gradient_state["summary"], gradient_state["vectors"])
                else:
                    gradients = compute_fold_gradients(fold, branch, endpoint, probe, inputs, mapping, config, device, profile)
                    atomic_torch(gradient_path, {"identity": identity, "fold": fold.index, "branch": branch, "summary": gradients.values, "vectors": gradients.vectors})
                arm_results: dict[str, Any] = {}
                for arm in config["arms"]:
                    receipt_path = run_dir / "arms" / f"fold-{fold.index}-{branch}-{arm}.json"
                    endpoint_hash = state_hash(endpoint.branches[branch].state_dict())
                    if args.resume and receipt_path.is_file():
                        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
                        if existing.get("identity") != identity or existing.get("config_sha256") != identity["config_sha256"] or existing.get("script_sha256") != identity["script_sha256"] or existing.get("endpoint_sha256") != endpoint_hash or existing.get("block_sha256") != block.digest or existing.get("start_model_sha256") != endpoint_hash:
                            raise ValueError("短步 arm 收据恢复身份不匹配")
                        arm_results[arm] = existing
                        continue
                    arm_receipt = run_short_step_arm(fold, branch, arm, endpoint, block, config, device, profile)
                    metrics = evaluate_arm(arm_receipt, endpoint, probe, fold, inputs, mapping, shuffled, p0_config, config, device, profile, threshold, False)
                    attachment = evaluate_arm(arm_receipt, endpoint, probe, fold, inputs, mapping, shuffled, p0_config, config, device, profile, threshold, True)
                    arm_results[arm] = {"identity": identity, "config_sha256": identity["config_sha256"], "script_sha256": identity["script_sha256"], "endpoint_sha256": endpoint_hash, "block_sha256": block.digest, "start_model_sha256": arm_receipt.receipt["start_model_sha256"], "receipt": arm_receipt.receipt, "frozen_probe": metrics, "refit_probe_attachment": attachment}
                    atomic_json(receipt_path, arm_results[arm])
                    atomic_torch(checkpoint_path, {"identity": identity, "stage": "arms", "fold": fold.index, "branch": branch, "arm": arm, "completed_arms": sorted(arm_results), "rng_state": pilot.capture_rng_state()})
                branch_results[branch] = {"gradients": gradients.values, "arms": arm_results}
            all_results[str(fold.index)] = {"endpoint": endpoint.receipt, "probe": probe.receipt, "frozen_fit_threshold": threshold, "shuffle": {"offset": shuffled.offset, "digest": shuffled.digest}, "block": {"samples": len(block.domains), "batches": block.batches, "sha256": block.digest}, "branches": branch_results}
        resources = {"device": torch.cuda.get_device_name(0) if device.type == "cuda" else str(device), "device_type": device.type, "precision_profile": profile_id, "float32_matmul_precision": torch.get_float32_matmul_precision(), "tf32_matmul": bool(torch.backends.cuda.matmul.allow_tf32) if device.type == "cuda" else None, "tf32_cudnn": bool(torch.backends.cudnn.allow_tf32) if device.type == "cuda" else None, "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()) if device.type == "cuda" else None, "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()) if device.type == "cuda" else None, "checkpoint_bytes": checkpoint_path.stat().st_size if checkpoint_path.is_file() else 0}
        result = {"schema_version": SCHEMA_VERSION, "status": "completed", "screening_only": True, "run_identity": config["run_identity"], "identity": identity, "forbidden_years_accessed": [], "folds": fold_manifest["folds"], "folds_results": all_results, "short_step": {"samples": 32768, "batches": 32}, "runtime": {"wall_seconds": time.monotonic() - started, "resources": resources, "precision_profile": profile}, "interpretation_boundary": config["interpretation_boundary"]}
        result["g2_verdict"] = adjudicate_g2(result)
        atomic_json(run_dir / "result.json", result)
        atomic_torch(checkpoint_path, {"identity": identity, "stage": "completed", "result_sha256": sha256_file(run_dir / "result.json"), "rng_state": pilot.capture_rng_state()})
        manifest_value = manifest(run_dir, root, config_path)
        atomic_json(run_dir / "manifest.json", manifest_value)
        atomic_json(status_path, {"status": "completed", "stage": "completed", "result_sha256": sha256_file(run_dir / "result.json"), "checkpoint_sha256": sha256_file(checkpoint_path), "manifest_sha256": sha256_file(run_dir / "manifest.json")})
        return 0
    except Exception as error:
        atomic_json(status_path, {"status": "failed", "error_type": type(error).__name__, "error": str(error)})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
