#!/usr/bin/env python3
"""N12 G1：全 T17 零更新的三任务下游梯度方向筛查。"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import pyarrow.parquet as pq
import torch
from tokenizers import Tokenizer
from torch import Tensor, nn

import ch3_drift_n10_conservative_fusion_pilot as pilot
import ch3_drift_t17_equal3_auxheads_gradient_base as g0
import neural_precision_runtime as precision


SCHEMA_VERSION = "ch3-drift-n12-g1-equal3-gradient-screen-v1"
TASKS = ("MTP", "TPP", "TOV")
RISKS = ("benign_bce", "dga_micro_bce", "dga_family_macro_bce")
BRANCHES = ("char", "subword")
FORBIDDEN_YEARS = tuple(f"T{year}" for year in range(18, 26))


@dataclass(frozen=True)
class InputSpec:
    label: int
    path: Path
    rows: int
    sha256: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    partial.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(partial, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_file(path: Path, expected: str, description: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{description}不存在：{path}")
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{description} SHA-256 不匹配")
    return actual


def reject_future_values(value: Any) -> None:
    if isinstance(value, str):
        if any(year in value for year in FORBIDDEN_YEARS):
            raise ValueError("G1 配置或路径含 T18--T25，入口机械拒绝")
    elif isinstance(value, Mapping):
        for child in value.values():
            reject_future_values(child)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for child in value:
            reject_future_values(child)


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置 schema_version 不匹配")
    if config.get("approved_scope") != "t17_g1_zero_update_equal3_gradient_screen_only":
        raise ValueError("G1 批准范围不匹配")
    if config.get("screening_only") is not True or config.get("seed") != 42:
        raise ValueError("G1 必须保持 screening_only 和种子 42")
    if config.get("dataset_revision") != "3b31077020cd1c013d0a75cad51042a2327c4521":
        raise ValueError("DRIFT 数据 revision 不匹配")
    reject_future_values(config["inputs"])
    probe = config["probe"]
    if probe != {
        "pooling": "p0_max_mean",
        "encoder_frozen": True,
        "classifier": "p0_static_classifier",
        "batch_size": 1024,
        "optimizer": "adam",
        "learning_rate": 0.0001,
        "member_passes": 1,
        "dropout": 0.1,
    }:
        raise ValueError("检测探针配方偏离 P0 一致解释")
    gradient = config["gradient"]
    if gradient != {
        "tasks": list(TASKS),
        "fit_mode": "train",
        "risk_mode": "eval",
        "normalization": "full_member_effective_supervision_mean",
        "risks": list(RISKS),
        "family_ambiguity": "exclude_from_macro_only",
    }:
        raise ValueError("G1 梯度定义偏离研究卡")
    runtime = config["runtime"]
    if (
        int(runtime["batch_size"]),
        int(runtime["raw_parquet_batch_rows"]),
        int(runtime["checkpoint_batches"]),
        str(runtime["precision_profile"]),
    ) != (1024, 32768, 32, "cuda-bf16-amp-fp32-sensitive-v1"):
        raise ValueError("G1 运行数值偏离冻结依据")
    return config


def load_spec(item: Mapping[str, Any], root: Path, description: str) -> InputSpec:
    path = (root / str(item["path"])).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"{description}路径必须位于项目根内")
    if not path.name.startswith("T17_"):
        raise ValueError(f"{description}只允许 T17 成员")
    spec = InputSpec(int(item["label"]), path, int(item["rows"]), str(item["sha256"]))
    parquet = pq.ParquetFile(spec.path)
    required = ["domain", "label"] if "raw" not in description else ["domain", "label", "family"]
    if parquet.schema_arrow.names != required:
        raise ValueError(f"{description}字段不匹配：{parquet.schema_arrow.names}")
    if int(parquet.metadata.num_rows) != spec.rows:
        raise ValueError(f"{description}行数不匹配")
    verify_file(spec.path, spec.sha256, description)
    return spec


def verify_inputs(config: Mapping[str, Any], root: Path) -> tuple[tuple[InputSpec, InputSpec], tuple[InputSpec, InputSpec], InputSpec, list[dict[str, Any]]]:
    fit = tuple(load_spec(item, root, "T17 fit 输入") for item in config["inputs"]["fit"])
    validation = tuple(load_spec(item, root, "T17 val 输入") for item in config["inputs"]["validation"])
    raw = load_spec(config["inputs"]["raw_dga_family"], root, "raw family 输入")
    if tuple(item.label for item in fit) != (0, 1) or tuple(item.label for item in validation) != (0, 1):
        raise ValueError("T17 fit/val 必须按 benign、DGA 顺序各含一份")
    if raw.label != 1:
        raise ValueError("raw family 输入必须为 DGA")
    receipts = [
        {"role": "fit", "label": item.label, "path": str(item.path), "rows": item.rows, "sha256": item.sha256}
        for item in fit
    ] + [
        {"role": "validation", "label": item.label, "path": str(item.path), "rows": item.rows, "sha256": item.sha256}
        for item in validation
    ] + [{"role": "raw_family", "label": raw.label, "path": str(raw.path), "rows": raw.rows, "sha256": raw.sha256}]
    return fit, validation, raw, receipts


def verify_p0(config: Mapping[str, Any], root: Path) -> tuple[dict[str, Any], Tokenizer, dict[str, Any]]:
    p0 = config["p0"]
    receipts: dict[str, Any] = {}
    for key, hash_key, description in (
        ("config", "config_sha256", "P0 配置"),
        ("source_code", "source_code_sha256", "P0 源代码"),
        ("tokenizer", "tokenizer_sha256", "P0 tokenizer"),
    ):
        path = root / str(p0[key])
        receipts[key] = {"path": str(path), "sha256": verify_file(path, str(p0[hash_key]), description)}
    p0_config = pilot.load_config(root / str(p0["config"]), root)
    tokenizer = Tokenizer.from_file(str(root / str(p0["tokenizer"])))
    if tokenizer.get_vocab_size() != int(p0_config["model"]["vocab_size_subword"]):
        raise ValueError("P0 tokenizer 词表大小不匹配")
    return p0_config, tokenizer, receipts


def verify_g0(config: Mapping[str, Any], root: Path) -> tuple[dict[str, Mapping[str, Any]], dict[str, Any]]:
    source = config["g0"]
    receipts: dict[str, Any] = {}
    for key, hash_key, description in (
        ("config", "config_sha256", "G0 配置"),
        ("source_code", "source_code_sha256", "G0 源代码"),
    ):
        path = root / str(source[key])
        receipts[key] = {"path": str(path), "sha256": verify_file(path, str(source[hash_key]), description)}
    states: dict[str, Mapping[str, Any]] = {}
    for arm in BRANCHES:
        item = source[arm]
        run_dir = root / str(item["run_dir"])
        result_path = run_dir / "result.json"
        checkpoint_path = run_dir / "checkpoint.pt"
        status_path = run_dir / "status.json"
        result_hash = verify_file(result_path, str(item["result_sha256"]), f"G0 {arm} 结果")
        checkpoint_hash = verify_file(checkpoint_path, str(item["checkpoint_sha256"]), f"G0 {arm} 检查点")
        if not status_path.is_file():
            raise FileNotFoundError(f"G0 {arm} 状态不存在")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        status = json.loads(status_path.read_text(encoding="utf-8"))
        state = pilot.load_checkpoint(checkpoint_path)
        if result.get("status") != "completed" or status.get("status") != "completed" or state.get("status") != "completed":
            raise ValueError(f"G0 {arm} 未完成")
        if status.get("result_sha256") != result_hash or status.get("checkpoint_sha256") != checkpoint_hash:
            raise ValueError(f"G0 {arm} 状态哈希不闭合")
        identity = state.get("identity")
        if not isinstance(identity, Mapping) or identity.get("arm") != arm:
            raise ValueError(f"G0 {arm} 检查点身份不匹配")
        if identity.get("config_sha256") != source["config_sha256"] or identity.get("script_sha256") != source["source_code_sha256"]:
            raise ValueError(f"G0 {arm} 配置或脚本身份不匹配")
        for task in TASKS:
            if int(state.get("valid_counts", {}).get(task, 0)) <= 0:
                raise ValueError(f"G0 {arm} 缺少 {task} 有效监督")
        if "optimizer" not in state or "rng_state" not in state or "branch" not in state:
            raise ValueError(f"G0 {arm} 缺少优化器、随机状态或分支状态")
        states[arm] = state
        receipts[arm] = {
            "run_dir": str(run_dir),
            "result_sha256": result_hash,
            "checkpoint_sha256": checkpoint_hash,
            "identity": dict(identity),
            "valid_counts": {task: int(state["valid_counts"][task]) for task in TASKS},
        }
    return states, receipts


def load_branches(p0_config: Mapping[str, Any], tokenizer: Tokenizer, states: Mapping[str, Mapping[str, Any]], device: torch.device) -> dict[str, pilot.PretrainedBranch]:
    model = pilot.build_static(dict(p0_config), tokenizer.get_vocab_size())
    branches = {"char": model.char, "subword": model.token}
    for name, branch in branches.items():
        branch.load_state_dict(states[name]["branch"], strict=True)
        branch.to(device)
    return branches


def build_probe(p0_config: Mapping[str, Any], branches: Mapping[str, pilot.PretrainedBranch], device: torch.device) -> pilot.StaticDual:
    pilot.set_seed(42)
    probe = pilot.StaticDual(
        pilot.EncoderBranch(branches["subword"]),
        pilot.EncoderBranch(branches["char"]),
        int(p0_config["model"]["d_model"]),
        float(p0_config["model"]["dropout"]),
    ).to(device)
    return probe


def shared_parameters(branch: pilot.PretrainedBranch) -> list[tuple[str, Tensor]]:
    parameters = [
        (name, parameter)
        for name, parameter in branch.named_parameters()
        if not name.startswith(("mtp_head", "tpp_head", "tov_head"))
    ]
    if not parameters:
        raise ValueError("共享编码器参数为空")
    return parameters


def set_encoder_requires_grad(probe: pilot.StaticDual, enabled: bool) -> None:
    for module in (probe.token, probe.char):
        for parameter in module.parameters():
            parameter.requires_grad = enabled


def set_probe_training_mode(probe: pilot.StaticDual) -> None:
    probe.classifier.train()
    probe.token.eval()
    probe.char.eval()


def set_risk_mode(probe: pilot.StaticDual) -> None:
    probe.eval()
    for parameter in probe.classifier.parameters():
        parameter.requires_grad = False


def save_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    torch.save(dict(value), partial)
    os.replace(partial, path)


def checkpoint_identity(config_hash: str, script_hash: str, inputs: list[dict[str, Any]], p0: Mapping[str, Any], g0_receipts: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "config_sha256": config_hash,
        "script_sha256": script_hash,
        "input_sha256": [item["sha256"] for item in inputs],
        "p0_config_sha256": p0["config"]["sha256"],
        "p0_source_code_sha256": p0["source_code"]["sha256"],
        "p0_tokenizer_sha256": p0["tokenizer"]["sha256"],
        "g0_config_sha256": g0_receipts["config"]["sha256"],
        "g0_source_code_sha256": g0_receipts["source_code"]["sha256"],
        "g0_char_checkpoint_sha256": g0_receipts["char"]["checkpoint_sha256"],
        "g0_subword_checkpoint_sha256": g0_receipts["subword"]["checkpoint_sha256"],
    }


def verify_checkpoint_identity(state: Mapping[str, Any], identity: Mapping[str, Any]) -> None:
    if state.get("identity") != identity:
        raise ValueError("G1 恢复检查点身份不匹配")


def iter_domains(spec: InputSpec, batch_size: int) -> Iterator[list[str]]:
    emitted = 0
    for batch in pq.ParquetFile(spec.path).iter_batches(batch_size=batch_size, columns=["domain", "label"]):
        domains = batch.column(0).to_pylist()
        labels = batch.column(1).to_pylist()
        if any(int(value) != spec.label for value in labels):
            raise ValueError(f"输入标签偏离合同：{spec.path}")
        values = [str(value) for value in domains]
        emitted += len(values)
        yield values
    if emitted != spec.rows:
        raise RuntimeError(f"输入未完整遍历：{spec.path}")


def encode_pair(domains: list[str], tokenizer: Tokenizer, p0_config: Mapping[str, Any], device: torch.device) -> tuple[Tensor, Tensor]:
    token = pilot.encode_subword_cpu(domains, tokenizer, int(p0_config["model"]["max_len_token"]))
    char = pilot.encode_char_cpu(domains, int(p0_config["model"]["max_len_char"]))
    if device.type == "cuda":
        token = token.pin_memory()
        char = char.pin_memory()
    return token.to(device, non_blocking=device.type == "cuda"), char.to(device, non_blocking=device.type == "cuda")


def fp32_cross_entropy(logits: Tensor, labels: Tensor, reduction: str) -> Tensor:
    return nn.functional.cross_entropy(logits.float(), labels, reduction=reduction)


def snapshot_probe_state(probe: pilot.StaticDual, optimizer: torch.optim.Optimizer, completed_batch: int, examples_seen: int, loss_sum: float, batches: int, identity: Mapping[str, Any], stage: str) -> dict[str, Any]:
    return {
        "identity": dict(identity),
        "stage": stage,
        "probe_classifier": probe.classifier.state_dict(),
        "probe_optimizer": optimizer.state_dict(),
        "completed_batch": completed_batch,
        "examples_seen": examples_seen,
        "loss_sum": loss_sum,
        "batches": batches,
        "probe_training": getattr(probe, "g1_training_receipt", None),
        "rng_state": pilot.capture_rng_state(),
    }


def train_probe(probe: pilot.StaticDual, tokenizer: Tokenizer, p0_config: Mapping[str, Any], fit: tuple[InputSpec, InputSpec], device: torch.device, profile: Mapping[str, Any], config: Mapping[str, Any], checkpoint_path: Path, identity: Mapping[str, Any], resume: Mapping[str, Any] | None) -> dict[str, Any]:
    set_encoder_requires_grad(probe, False)
    set_probe_training_mode(probe)
    optimizer = torch.optim.Adam(probe.classifier.parameters(), lr=float(config["probe"]["learning_rate"]))
    completed_batch = -1
    examples_seen = 0
    loss_sum = 0.0
    batches = 0
    if resume is not None and resume.get("stage") in {"probe", "probe_completed"}:
        verify_checkpoint_identity(resume, identity)
        probe.classifier.load_state_dict(resume["probe_classifier"], strict=True)
        optimizer.load_state_dict(resume["probe_optimizer"])
        completed_batch = int(resume["completed_batch"])
        examples_seen = int(resume["examples_seen"])
        loss_sum = float(resume["loss_sum"])
        batches = int(resume["batches"])
        pilot.restore_rng_state(resume["rng_state"])
        if resume.get("stage") == "probe_completed":
            return {"examples_seen": examples_seen, "batches": batches, "mean_loss": loss_sum / max(batches, 1), "resumed_completed": True}
    if resume is not None and resume.get("stage") in {"family", "family_completed", "task_gradients", "risk_gradients", "completed"}:
        receipt = resume.get("probe_training")
        if not isinstance(receipt, Mapping):
            raise ValueError("已进入 G1 后续阶段但缺少检测探针训练收据")
        return dict(receipt)
    parts = tuple(pilot.InputPart(item.path, item.label, item.rows, "fit") for item in fit)
    interval = int(config["runtime"]["checkpoint_batches"])
    start = time.monotonic()
    for index, (domains, labels_cpu) in enumerate(pilot.iter_labeled_batches(parts, int(config["probe"]["batch_size"]), 42)):
        if index <= completed_batch:
            continue
        token, char = encode_pair(domains, tokenizer, p0_config, device)
        labels = labels_cpu.to(device, non_blocking=device.type == "cuda")
        optimizer.zero_grad(set_to_none=True)
        with precision.autocast_context(profile, device.type, torch):
            logits = probe(token, char)
        loss = fp32_cross_entropy(logits, labels, reduction="mean")
        if not torch.isfinite(loss):
            raise FloatingPointError("检测探针损失非有限")
        loss.backward()
        optimizer.step()
        examples_seen += len(domains)
        batches += 1
        loss_sum += float(loss.detach().cpu())
        completed_batch = index
        if (index + 1) % interval == 0:
            save_checkpoint(checkpoint_path, snapshot_probe_state(probe, optimizer, completed_batch, examples_seen, loss_sum, batches, identity, "probe"))
            print(json.dumps({"stage": "probe", "batches": batches, "examples_seen": examples_seen, "elapsed_seconds": time.monotonic() - start}, ensure_ascii=False), flush=True)
    expected = sum(item.rows for item in fit)
    if examples_seen != expected:
        raise RuntimeError(f"检测探针未完整遍历 T17 fit：{examples_seen} != {expected}")
    final = snapshot_probe_state(probe, optimizer, completed_batch, examples_seen, loss_sum, batches, identity, "probe_completed")
    save_checkpoint(checkpoint_path, final)
    return {"examples_seen": examples_seen, "batches": batches, "mean_loss": loss_sum / max(batches, 1), "wall_seconds": time.monotonic() - start, "throughput_examples_per_second": expected / max(time.monotonic() - start, 1e-12)}


def domain_digest(value: str) -> bytes:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).digest()


def raw_to_esld(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().split(".", 1)[0]


def checkpoint_family_state(checkpoint_path: Path, identity: Mapping[str, Any], probe: pilot.StaticDual, family: Mapping[str, Any]) -> None:
    save_checkpoint(checkpoint_path, {"identity": dict(identity), "stage": "family", "probe_classifier": probe.classifier.state_dict(), "probe_training": getattr(probe, "g1_training_receipt", None), "family": dict(family), "rng_state": pilot.capture_rng_state()})


def prepare_family_mapping(validation_dga: InputSpec, raw: InputSpec, config: Mapping[str, Any], checkpoint_path: Path, identity: Mapping[str, Any], probe: pilot.StaticDual, resume: Mapping[str, Any] | None) -> dict[str, Any]:
    if resume is not None and resume.get("stage") in {"family_completed", "task_gradients", "risk_gradients", "completed"}:
        verify_checkpoint_identity(resume, identity)
        return dict(resume["family"])
    raw_batch_rows = int(config["runtime"]["raw_parquet_batch_rows"])
    interval = int(config["runtime"]["checkpoint_batches"])
    target_hashes: set[bytes]
    mapped: dict[bytes, set[bytes]]
    completed_raw_batches = -1
    if resume is not None and resume.get("stage") == "family":
        verify_checkpoint_identity(resume, identity)
        family = resume["family"]
        target_hashes = set(family["target_hashes"])
        mapped = {key: set(value) for key, value in family["mapped"].items()}
        completed_raw_batches = int(family["completed_raw_batches"])
        pilot.restore_rng_state(resume["rng_state"])
    else:
        target_hashes = set()
        for domains in iter_domains(validation_dga, int(config["runtime"]["batch_size"])):
            target_hashes.update(domain_digest(domain) for domain in domains)
        mapped = {key: set() for key in target_hashes}
    start = time.monotonic()
    processed = 0
    for index, batch in enumerate(pq.ParquetFile(raw.path).iter_batches(batch_size=raw_batch_rows, columns=["domain", "label", "family"])):
        processed += batch.num_rows
        if index <= completed_raw_batches:
            continue
        frame = batch.to_pydict()
        for domain, label, family_value in zip(frame["domain"], frame["label"], frame["family"], strict=True):
            if int(label) != 1:
                raise ValueError("raw DGA 文件含非恶意标签")
            key = raw_to_esld(domain)
            digest = domain_digest(key)
            if digest in mapped and isinstance(family_value, str) and (family := family_value.strip().lower()):
                mapped[digest].add(hashlib.sha256(family.encode("utf-8")).digest())
        completed_raw_batches = index
        if (index + 1) % interval == 0:
            checkpoint_family_state(checkpoint_path, identity, probe, {"target_hashes": target_hashes, "mapped": mapped, "completed_raw_batches": completed_raw_batches})
            print(json.dumps({"stage": "family_join", "raw_rows": processed, "total_raw_rows": raw.rows, "elapsed_seconds": time.monotonic() - start}, ensure_ascii=False), flush=True)
    if processed != raw.rows:
        raise RuntimeError("raw family 未完整扫描")
    supports: dict[bytes, int] = defaultdict(int)
    statuses: dict[bytes, str] = {}
    for key, values in mapped.items():
        statuses[key] = "unique" if len(values) == 1 else "ambiguous" if len(values) > 1 else "missing"
    selected_rows = 0
    for domains in iter_domains(validation_dga, int(config["runtime"]["batch_size"])):
        for domain in domains:
            values = mapped[domain_digest(domain)]
            if len(values) == 1:
                supports[next(iter(values))] += 1
                selected_rows += 1
    if not supports:
        raise ValueError("T17 val DGA 无可唯一映射 family")
    family = {
        "target_hashes": target_hashes,
        "mapped": mapped,
        "statuses": statuses,
        "supports": dict(supports),
        "completed_raw_batches": completed_raw_batches,
        "raw_rows": processed,
        "unique_esld_keys": sum(value == "unique" for value in statuses.values()),
        "ambiguous_esld_keys": sum(value == "ambiguous" for value in statuses.values()),
        "missing_esld_keys": sum(value == "missing" for value in statuses.values()),
        "family_count": len(supports),
        "family_macro_rows": selected_rows,
        "wall_seconds": time.monotonic() - start,
    }
    save_checkpoint(checkpoint_path, {"identity": dict(identity), "stage": "family_completed", "probe_classifier": probe.classifier.state_dict(), "probe_training": getattr(probe, "g1_training_receipt", None), "family": family, "rng_state": pilot.capture_rng_state()})
    return family


def cpu_zero_vectors(parameters: list[tuple[str, Tensor]]) -> dict[str, Tensor]:
    return {name: torch.zeros_like(parameter, dtype=torch.float32, device="cpu") for name, parameter in parameters}


def gpu_vectors(values: Mapping[str, Tensor], device: torch.device) -> dict[str, Tensor]:
    return {name: value.to(device=device, dtype=torch.float32) for name, value in values.items()}


def cpu_snapshot(values: Mapping[str, Tensor]) -> dict[str, Tensor]:
    return {name: value.detach().to(device="cpu", dtype=torch.float32) for name, value in values.items()}


def gradient_norm(values: Mapping[str, Tensor]) -> float:
    squared = sum(float(torch.sum(value.detach().double().square()).cpu()) for value in values.values())
    return math.sqrt(squared)


def vector_dot(left: Mapping[str, Tensor], right: Mapping[str, Tensor]) -> float:
    if set(left) != set(right):
        raise ValueError("梯度向量键不一致")
    return sum(float(torch.sum(left[name].detach().double() * right[name].detach().double()).cpu()) for name in left)


def finite_vectors(values: Mapping[str, Tensor]) -> bool:
    return all(bool(torch.isfinite(value).all()) for value in values.values())


def snapshot_gradient_state(identity: Mapping[str, Any], probe: pilot.StaticDual, family: Mapping[str, Any], task_gradients: Mapping[str, Any], risk_gradients: Mapping[str, Any], stage: str, work: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "identity": dict(identity),
        "stage": stage,
        "probe_classifier": probe.classifier.state_dict(),
        "probe_training": getattr(probe, "g1_training_receipt", None),
        "family": dict(family),
        "task_gradients": dict(task_gradients),
        "risk_gradients": dict(risk_gradients),
        "work": dict(work),
        "rng_state": pilot.capture_rng_state(),
    }


def compute_task_gradients(branch_name: str, branch: pilot.PretrainedBranch, tokenizer: Tokenizer, p0_config: Mapping[str, Any], fit: tuple[InputSpec, InputSpec], device: torch.device, profile: Mapping[str, Any], config: Mapping[str, Any], checkpoint_path: Path, identity: Mapping[str, Any], probe: pilot.StaticDual, family: Mapping[str, Any], all_tasks: dict[str, Any], all_risks: dict[str, Any], resume: Mapping[str, Any] | None) -> dict[str, Any]:
    if branch_name in all_tasks:
        return all_tasks[branch_name]
    parameters = shared_parameters(branch)
    branch.train()
    for parameter in branch.parameters():
        parameter.requires_grad = True
    completed_batch = -1
    examples_seen = 0
    valid_counts = {task: 0 for task in TASKS}
    accum = {task: cpu_zero_vectors(parameters) for task in TASKS}
    if resume is not None and resume.get("stage") == "task_gradients":
        work = resume.get("work", {})
        if work.get("branch") == branch_name:
            completed_batch = int(work["completed_batch"])
            examples_seen = int(work["examples_seen"])
            valid_counts = {task: int(work["valid_counts"][task]) for task in TASKS}
            accum = {task: dict(work["sums"][task]) for task in TASKS}
            pilot.restore_rng_state(resume["rng_state"])
    gpu_accum = {task: gpu_vectors(values, device) for task, values in accum.items()}
    parts = tuple(pilot.InputPart(item.path, item.label, item.rows, "fit") for item in fit)
    interval = int(config["runtime"]["checkpoint_batches"])
    start = time.monotonic()
    for index, domains in enumerate(pilot.iter_domain_batches(parts, int(config["runtime"]["batch_size"]), 42)):
        if index <= completed_batch:
            continue
        if branch_name == "char":
            ids = pilot.encode_char_cpu(domains, int(p0_config["model"]["max_len_char"]))
        else:
            ids = pilot.encode_subword_cpu(domains, tokenizer, int(p0_config["model"]["max_len_token"]))
        views_cpu = pilot.pretraining_views(ids, int(config["seed"]) + index, int(p0_config["pretraining"]["ignore_index"]), float(p0_config["pretraining"]["mask_ratio"]), float(p0_config["pretraining"]["shuffle_probability"]))
        views = tuple(value.to(device, non_blocking=device.type == "cuda") for value in views_cpu)
        with precision.autocast_context(profile, device.type, torch):
            _, losses, valid = g0.task_losses(branch, views, int(p0_config["pretraining"]["ignore_index"]))
        for task_index, task in enumerate(TASKS):
            if valid[task] <= 0:
                raise ValueError(f"{branch_name} {task} 出现零有效监督")
            loss = losses[task].float() * valid[task]
            if not torch.isfinite(loss):
                raise FloatingPointError(f"{branch_name} {task} 梯度损失非有限")
            gradients = torch.autograd.grad(loss, [parameter for _, parameter in parameters], retain_graph=task_index < len(TASKS) - 1, allow_unused=False)
            for (name, _), gradient in zip(parameters, gradients, strict=True):
                if not torch.isfinite(gradient).all():
                    raise FloatingPointError(f"{branch_name} {task} 梯度非有限")
                gpu_accum[task][name].add_(gradient.detach().float())
            valid_counts[task] += valid[task]
        examples_seen += len(domains)
        completed_batch = index
        if (index + 1) % interval == 0:
            work = {"branch": branch_name, "completed_batch": completed_batch, "examples_seen": examples_seen, "valid_counts": valid_counts, "sums": {task: cpu_snapshot(values) for task, values in gpu_accum.items()}}
            save_checkpoint(checkpoint_path, snapshot_gradient_state(identity, probe, family, all_tasks, all_risks, "task_gradients", work))
            print(json.dumps({"stage": "task_gradients", "branch": branch_name, "examples_seen": examples_seen, "elapsed_seconds": time.monotonic() - start}, ensure_ascii=False), flush=True)
    expected = sum(item.rows for item in fit)
    if examples_seen != expected:
        raise RuntimeError(f"{branch_name} 任务梯度未完整遍历 T17 fit")
    vectors = {task: {name: value / valid_counts[task] for name, value in cpu_snapshot(gpu_accum[task]).items()} for task in TASKS}
    if any(not finite_vectors(vector) or gradient_norm(vector) == 0.0 for vector in vectors.values()):
        raise FloatingPointError(f"{branch_name} 任务完整梯度非有限或为零")
    result = {"vectors": vectors, "valid_counts": valid_counts, "examples_seen": examples_seen, "mode": "train", "normalization": "effective_supervision_mean"}
    all_tasks[branch_name] = result
    save_checkpoint(checkpoint_path, snapshot_gradient_state(identity, probe, family, all_tasks, all_risks, "task_gradients", {"branch": branch_name, "completed": True}))
    return result


def risk_loss_sum(risk: str, logits: Tensor, family_values: list[bytes | None], family_supports: Mapping[bytes, int]) -> tuple[Tensor, int]:
    if risk == "benign_bce":
        labels = torch.zeros(logits.shape[0], dtype=torch.long, device=logits.device)
        return fp32_cross_entropy(logits, labels, reduction="sum"), logits.shape[0]
    labels = torch.ones(logits.shape[0], dtype=torch.long, device=logits.device)
    if risk == "dga_micro_bce":
        return fp32_cross_entropy(logits, labels, reduction="sum"), logits.shape[0]
    per_row = fp32_cross_entropy(logits, labels, reduction="none")
    weights = torch.tensor([0.0 if family is None else 1.0 / family_supports[family] for family in family_values], dtype=torch.float32, device=logits.device)
    return torch.sum(per_row * weights), len(family_supports)


def compute_risk_gradient(branch_name: str, risk: str, probe: pilot.StaticDual, branch: pilot.PretrainedBranch, tokenizer: Tokenizer, p0_config: Mapping[str, Any], spec: InputSpec, device: torch.device, profile: Mapping[str, Any], config: Mapping[str, Any], checkpoint_path: Path, identity: Mapping[str, Any], family: Mapping[str, Any], all_tasks: Mapping[str, Any], all_risks: dict[str, Any], resume: Mapping[str, Any] | None) -> dict[str, Any]:
    existing = all_risks.get(branch_name, {}).get(risk)
    if existing is not None:
        return existing
    parameters = shared_parameters(branch)
    set_risk_mode(probe)
    for name, other in (("char", probe.char), ("subword", probe.token)):
        for parameter in other.parameters():
            parameter.requires_grad = name == branch_name
    completed_batch = -1
    processed = 0
    denominator = 0
    accum = cpu_zero_vectors(parameters)
    if resume is not None and resume.get("stage") == "risk_gradients":
        work = resume.get("work", {})
        if work.get("branch") == branch_name and work.get("risk") == risk:
            completed_batch = int(work["completed_batch"])
            processed = int(work["processed"])
            denominator = int(work["denominator"])
            accum = dict(work["sum"])
            pilot.restore_rng_state(resume["rng_state"])
    gpu_accum = gpu_vectors(accum, device)
    supports = family["supports"]
    mapping = family["mapped"]
    interval = int(config["runtime"]["checkpoint_batches"])
    start = time.monotonic()
    for index, domains in enumerate(iter_domains(spec, int(config["runtime"]["batch_size"]))):
        if index <= completed_batch:
            continue
        token, char = encode_pair(domains, tokenizer, p0_config, device)
        family_values = []
        if risk == "dga_family_macro_bce":
            for domain in domains:
                values = mapping.get(domain_digest(domain), set())
                family_values.append(next(iter(values)) if len(values) == 1 else None)
        else:
            family_values = [None] * len(domains)
        with precision.autocast_context(profile, device.type, torch):
            logits = probe(token, char)
        loss_sum, units = risk_loss_sum(risk, logits, family_values, supports)
        if not torch.isfinite(loss_sum):
            raise FloatingPointError(f"{branch_name} {risk} 风险损失非有限")
        gradients = torch.autograd.grad(loss_sum, [parameter for _, parameter in parameters], allow_unused=False)
        for (name, _), gradient in zip(parameters, gradients, strict=True):
            if not torch.isfinite(gradient).all():
                raise FloatingPointError(f"{branch_name} {risk} 风险梯度非有限")
            gpu_accum[name].add_(gradient.detach().float())
        processed += len(domains)
        denominator = units if risk == "dga_family_macro_bce" else denominator + units
        completed_batch = index
        if (index + 1) % interval == 0:
            work = {"branch": branch_name, "risk": risk, "completed_batch": completed_batch, "processed": processed, "denominator": denominator, "sum": cpu_snapshot(gpu_accum)}
            save_checkpoint(checkpoint_path, snapshot_gradient_state(identity, probe, family, all_tasks, all_risks, "risk_gradients", work))
            print(json.dumps({"stage": "risk_gradients", "branch": branch_name, "risk": risk, "processed": processed, "elapsed_seconds": time.monotonic() - start}, ensure_ascii=False), flush=True)
    if processed != spec.rows or denominator <= 0:
        raise RuntimeError(f"{branch_name} {risk} 风险成员未完整遍历或归一化单位为空")
    vector = {name: value / denominator for name, value in cpu_snapshot(gpu_accum).items()}
    if not finite_vectors(vector) or gradient_norm(vector) == 0.0:
        raise FloatingPointError(f"{branch_name} {risk} 完整梯度非有限或为零")
    result = {"vector": vector, "processed_rows": processed, "normalization_units": denominator, "mode": "eval"}
    all_risks.setdefault(branch_name, {})[risk] = result
    save_checkpoint(checkpoint_path, snapshot_gradient_state(identity, probe, family, all_tasks, all_risks, "risk_gradients", {"branch": branch_name, "risk": risk, "completed": True}))
    return result


def pair_metrics(left: Mapping[str, Tensor], right: Mapping[str, Tensor]) -> dict[str, Any]:
    left_norm = gradient_norm(left)
    right_norm = gradient_norm(right)
    dot = vector_dot(left, right)
    cosine = dot / (left_norm * right_norm)
    return {
        "raw_dot": dot,
        "left_l2_norm": left_norm,
        "right_l2_norm": right_norm,
        "cosine": cosine,
        "unit_direction_dot": cosine,
        "unit_direction_storage": "checkpoint.pt 的 FP32 原始向量分别除以本字段范数",
    }


def summarize_gradients(task_gradients: Mapping[str, Any], risk_gradients: Mapping[str, Any], family: Mapping[str, Any]) -> dict[str, Any]:
    branches: dict[str, Any] = {}
    decision_cells: list[dict[str, str]] = []
    for branch in BRANCHES:
        task_vectors = task_gradients[branch]["vectors"]
        risk_vectors = {risk: risk_gradients[branch][risk]["vector"] for risk in RISKS}
        task_summary = {task: {"valid_supervision": int(task_gradients[branch]["valid_counts"][task]), "l2_norm": gradient_norm(task_vectors[task]), "finite": finite_vectors(task_vectors[task]), "unit_direction_storage": "checkpoint.pt"} for task in TASKS}
        pairs = {f"{left}__{right}": pair_metrics(task_vectors[left], task_vectors[right]) for left, right in itertools.combinations(TASKS, 2)}
        risks = {risk: {"processed_rows": int(risk_gradients[branch][risk]["processed_rows"]), "normalization_units": int(risk_gradients[branch][risk]["normalization_units"]), "l2_norm": gradient_norm(risk_vectors[risk]), "finite": finite_vectors(risk_vectors[risk]), "unit_direction_storage": "checkpoint.pt"} for risk in RISKS}
        alignment = {risk: {task: pair_metrics(risk_vectors[risk], task_vectors[task]) for task in TASKS} for risk in RISKS}
        for risk in RISKS:
            cosine = {task: alignment[risk][task]["cosine"] for task in TASKS}
            if any(value < 0.0 for value in cosine.values()) and any(value >= 0.0 for value in cosine.values()):
                decision_cells.append({"branch": branch, "risk": risk})
        branches[branch] = {"tasks": task_summary, "task_pairwise": pairs, "risks": risks, "risk_task_alignment": alignment}
    verdict = "eligible_for_g2_only" if decision_cells else "rejected_no_direction_difference"
    return {
        "branches": branches,
        "family_macro_receipt": {key: family[key] for key in ("unique_esld_keys", "ambiguous_esld_keys", "missing_esld_keys", "family_count", "family_macro_rows")},
        "g1_direction_difference_cells": decision_cells,
        "g1_verdict": verdict,
        "verdict_rule": "同一 branch x risk 至少一个任务 cosine<0 且另一个任务 cosine>=0；余弦是单位范数方向量，因此不以范数量级作裁决。",
    }


def resource_receipt(device: torch.device, checkpoint_path: Path, profile_id: str) -> dict[str, Any]:
    if device.type == "cuda":
        return {
            "device": torch.cuda.get_device_name(0),
            "device_type": "cuda",
            "precision_profile_id": profile_id,
            "float32_matmul_precision": torch.get_float32_matmul_precision(),
            "cuda_matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
            "cudnn_allow_tf32": bool(torch.backends.cudnn.allow_tf32),
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
            "checkpoint_bytes": checkpoint_path.stat().st_size if checkpoint_path.is_file() else 0,
        }
    return {"device": str(device), "device_type": device.type, "precision_profile_id": profile_id, "peak_allocated_bytes": None, "peak_reserved_bytes": None, "checkpoint_bytes": checkpoint_path.stat().st_size if checkpoint_path.is_file() else 0}


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    run_dir = args.run_dir.resolve()
    config_path = args.config.resolve()
    config = load_config(config_path)
    if run_dir.name != config["run_identity"]:
        raise ValueError("运行目录名与 G1 身份不一致")
    if run_dir.exists() and not args.resume:
        raise FileExistsError("G1 运行目录已存在；仅允许 --resume")
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path = run_dir / "status.json"
    checkpoint_path = run_dir / "checkpoint.pt"
    config_hash = sha256_file(config_path)
    script_hash = sha256_file(Path(__file__).resolve())
    started = time.monotonic()
    atomic_json(status_path, {"status": "running", "stage": "verify"})
    try:
        fit, validation, raw, input_receipts = verify_inputs(config, root)
        p0_config, tokenizer, p0_receipts = verify_p0(config, root)
        g0_states, g0_receipts = verify_g0(config, root)
        identity = checkpoint_identity(config_hash, script_hash, input_receipts, p0_receipts, g0_receipts)
        device = pilot.device_for_run()
        precision_contract_path = root / str(config["runtime"]["precision_contract"])
        verify_file(precision_contract_path, str(config["runtime"]["precision_contract_sha256"]), "精度合同")
        precision_contract = precision.load_and_validate_contract(precision_contract_path)
        profile_id = precision.profile_for_device(precision_contract, device.type)
        if device.type == "cuda" and profile_id != config["runtime"]["precision_profile"]:
            raise ValueError("CUDA 精度 profile 偏离冻结配置")
        profile = precision.validate_runtime_profile(precision_contract, profile_id, device.type, torch)
        pilot.set_seed(42)
        torch.set_float32_matmul_precision("high")
        branches = load_branches(p0_config, tokenizer, g0_states, device)
        probe = build_probe(p0_config, branches, device)
        resume = pilot.load_checkpoint(checkpoint_path) if args.resume and checkpoint_path.is_file() else None
        if resume is not None:
            verify_checkpoint_identity(resume, identity)
            if "probe_classifier" in resume:
                probe.classifier.load_state_dict(resume["probe_classifier"], strict=True)
            probe.g1_training_receipt = resume.get("probe_training")
        atomic_json(run_dir / "effective-config.json", {"config": config, "identity": identity, "inputs": input_receipts, "p0": p0_receipts, "g0": g0_receipts, "precision_profile": profile_id})
        training = train_probe(probe, tokenizer, p0_config, fit, device, profile, config, checkpoint_path, identity, resume)
        probe.g1_training_receipt = training
        resume = pilot.load_checkpoint(checkpoint_path)
        verify_checkpoint_identity(resume, identity)
        family = prepare_family_mapping(validation[1], raw, config, checkpoint_path, identity, probe, resume)
        resume = pilot.load_checkpoint(checkpoint_path)
        verify_checkpoint_identity(resume, identity)
        task_gradients: dict[str, Any] = dict(resume.get("task_gradients", {}))
        risk_gradients: dict[str, Any] = dict(resume.get("risk_gradients", {}))
        for branch_name in BRANCHES:
            compute_task_gradients(branch_name, branches[branch_name], tokenizer, p0_config, fit, device, profile, config, checkpoint_path, identity, probe, family, task_gradients, risk_gradients, resume)
            resume = pilot.load_checkpoint(checkpoint_path)
            verify_checkpoint_identity(resume, identity)
            task_gradients = dict(resume.get("task_gradients", task_gradients))
            risk_gradients = dict(resume.get("risk_gradients", risk_gradients))
        for branch_name in BRANCHES:
            for risk, spec in (("benign_bce", validation[0]), ("dga_micro_bce", validation[1]), ("dga_family_macro_bce", validation[1])):
                compute_risk_gradient(branch_name, risk, probe, branches[branch_name], tokenizer, p0_config, spec, device, profile, config, checkpoint_path, identity, family, task_gradients, risk_gradients, resume)
                resume = pilot.load_checkpoint(checkpoint_path)
                verify_checkpoint_identity(resume, identity)
                task_gradients = dict(resume.get("task_gradients", task_gradients))
                risk_gradients = dict(resume.get("risk_gradients", risk_gradients))
        summary = summarize_gradients(task_gradients, risk_gradients, family)
        result = {"schema_version": SCHEMA_VERSION, "status": "completed", "run_identity": config["run_identity"], "screening_only": True, "identity": identity, "probe_training": training, "gradient_summary": summary, "runtime": {"wall_seconds": time.monotonic() - started, "resources": resource_receipt(device, checkpoint_path, profile_id), "precision_profile": profile}, "interpretation_boundary": config["interpretation_boundary"]}
        atomic_json(run_dir / "result.json", result)
        save_checkpoint(checkpoint_path, snapshot_gradient_state(identity, probe, family, task_gradients, risk_gradients, "completed", {"result_sha256": sha256_file(run_dir / "result.json")}))
        atomic_json(status_path, {"status": "completed", "stage": "completed", "identity": identity, "result_sha256": sha256_file(run_dir / "result.json"), "checkpoint_sha256": sha256_file(checkpoint_path)})
        print(json.dumps({"status": "completed", "run_dir": str(run_dir)}, ensure_ascii=False))
        return 0
    except Exception as error:
        atomic_json(status_path, {"status": "failed", "error_type": type(error).__name__, "error": str(error)})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
