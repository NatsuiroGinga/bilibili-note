#!/usr/bin/env python3
"""LAMDA 安全回归约束的独立消融筛查。

这是与阶段 A 分离的 screening_only 运行。安全记忆只从已经到达的年度训练样本中
构造，不读取未来年度样本；它不改变阶段 A 的 Naive/Replay 资格裁决。
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

import ch3_lamda_domain_il_replay_screening as base


YEAR_ORDER = [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
ARMS = ["naive_security_regression", "replay_security_regression"]
THRESHOLD = 0.5


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("arms") != ARMS:
        raise ValueError("安全回归消融必须恰有两个独立臂")
    if config.get("data", {}).get("year_order") != YEAR_ORDER:
        raise ValueError("年份顺序不符合 LAMDA Domain-IL 合同")
    if config.get("data", {}).get("published_feature_count") != 4561:
        raise ValueError("发布特征数必须为 4561")
    training = config.get("training", {})
    if training.get("seed") != 42 or training.get("epochs_per_year") != 10 or training.get("batch_size") != 1024:
        raise ValueError("训练预算不符合阶段 A 合同")
    replay = config.get("replay", {})
    if replay.get("capacity") != 200:
        raise ValueError("回放容量必须为 200")
    safety = config.get("security_regression", {})
    if safety.get("capacity") != 200 or safety.get("lambda") != 1.0:
        raise ValueError("安全记忆或约束系数不符合冻结消融")
    if config.get("identity", {}).get("published_feature_space_uses_future_covariates") is not True:
        raise ValueError("必须披露发布特征空间使用未来协变量")
    return config


class SafetyMemory(base.Reservoir):
    """只保存历史训练区内被上一模型正确判为恶意的样本。"""

    def update_from_predictions(self, values: np.ndarray, labels: np.ndarray, hashes: np.ndarray, scores: np.ndarray, year: int, threshold: float) -> int:
        eligible = (labels == 1) & (scores >= threshold)
        selected_values = values[eligible]
        selected_labels = labels[eligible]
        identities = [
            base.identity_pair(year, source_hash, row, int(label))
            for row, label, source_hash in zip(values[eligible], labels[eligible], hashes[eligible], strict=True)
        ]
        self.update(selected_values, selected_labels, identities)
        return int(np.sum(eligible))


def train_epoch(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    train_path: Path,
    features: list[str],
    replay_memory: base.Reservoir | None,
    safety_memory: SafetyMemory,
    device: torch.device,
    batch_size: int,
    shuffle_seed: int,
    safety_lambda: float,
) -> tuple[float, int, float]:
    model.train()
    value_chunks: list[np.ndarray] = []
    label_chunks: list[np.ndarray] = []
    for values, labels, _, _ in base.iter_parquet(train_path, features):
        value_chunks.append(values)
        label_chunks.append(labels)
    if not label_chunks:
        raise RuntimeError("年度训练未读取到任何样本")
    values = np.concatenate(value_chunks, axis=0)
    labels = np.concatenate(label_chunks, axis=0)
    if replay_memory is not None and len(replay_memory.labels):
        values = np.concatenate((values, replay_memory.values), axis=0)
        labels = np.concatenate((labels, replay_memory.labels), axis=0)
    order = np.random.default_rng(shuffle_seed).permutation(len(labels))
    values, labels = values[order], labels[order]
    total_loss, total_samples, safety_loss_total = 0.0, 0, 0.0
    safety_inputs = None
    safety_targets = None
    if len(safety_memory.labels):
        safety_inputs = torch.from_numpy(safety_memory.values).to(device=device, dtype=torch.float32)
        safety_targets = torch.ones(len(safety_memory.labels), device=device)
    for start in range(0, len(labels), batch_size):
        batch_values = values[start : start + batch_size]
        batch_labels = labels[start : start + batch_size]
        inputs = torch.from_numpy(batch_values).to(device=device, dtype=torch.float32)
        targets = torch.from_numpy(batch_labels.astype(np.float32, copy=False)).to(device=device)
        optimizer.zero_grad(set_to_none=True)
        probabilities = model(inputs)
        loss = criterion(probabilities, targets)
        safety_loss = torch.zeros((), device=device)
        if safety_inputs is not None and safety_targets is not None:
            safety_loss = criterion(model(safety_inputs), safety_targets)
            loss = loss + safety_lambda * safety_loss
        loss.backward()
        optimizer.step()
        total_loss += float(loss.item()) * len(batch_labels)
        safety_loss_total += float(safety_loss.item())
        total_samples += len(batch_labels)
    return total_loss / total_samples, total_samples, safety_loss_total / max(1, total_samples // batch_size + int(total_samples % batch_size != 0))


def collect_safety_memory(model: nn.Module, train_path: Path, features: list[str], memory: SafetyMemory, device: torch.device, year: int, threshold: float) -> int:
    model.eval()
    eligible_count = 0
    with torch.inference_mode():
        for values, labels, hashes, _ in base.iter_parquet(train_path, features):
            scores = model(torch.from_numpy(values).to(device=device, dtype=torch.float32)).cpu().numpy()
            eligible_count += memory.update_from_predictions(values, labels, hashes, scores, year, threshold)
    return eligible_count


def checkpoint_payload(model: nn.Module, optimizer: torch.optim.Optimizer, replay_memory: base.Reservoir | None, safety_memory: SafetyMemory, year_index: int, next_epoch: int, yearly: dict[str, Any], old_positive: dict[str, bool]) -> dict[str, Any]:
    return {
        "schema_version": "ch3-lamda-security-regression-checkpoint-v1",
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "replay_memory": None if replay_memory is None else replay_memory.state_dict(),
        "safety_memory": safety_memory.state_dict(),
        "year_index": year_index,
        "next_epoch": next_epoch,
        "yearly": yearly,
        "old_positive": old_positive,
        "rng": base.rng_state(),
        "saved_at": base.now_utc(),
    }


def execute_arm(arm: str, config: dict[str, Any], features: list[str], files: dict[int, dict[str, Path]], output_root: Path, device: torch.device, resume: bool, started_at: str) -> dict[str, Any]:
    checkpoint_path = output_root / "checkpoints" / arm / "latest.pt"
    seed = int(config["training"]["seed"])
    if resume and checkpoint_path.is_file():
        saved = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model = base.LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device)
        model.load_state_dict(saved["model"])
        optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"]))
        optimizer.load_state_dict(saved["optimizer"])
        replay_memory = None if saved["replay_memory"] is None else base.Reservoir.from_state(saved["replay_memory"])
        safety_memory = SafetyMemory.from_state(saved["safety_memory"])
        year_index, next_epoch = int(saved["year_index"]), int(saved["next_epoch"])
        yearly, old_positive = dict(saved["yearly"]), dict(saved["old_positive"])
        base.restore_rng(saved["rng"])
    else:
        base.seed_everything(seed)
        model = base.LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device)
        optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"]))
        replay_memory = base.Reservoir(int(config["replay"]["capacity"]), len(features), seed) if arm == "replay_security_regression" else None
        safety_memory = SafetyMemory(int(config["security_regression"]["capacity"]), len(features), seed + 1)
        year_index, next_epoch, yearly, old_positive = 0, 1, {}, {}
    criterion = nn.BCELoss()
    epochs = int(config["training"]["epochs_per_year"])
    batch_size = int(config["training"]["batch_size"])
    safety_lambda = float(config["security_regression"]["lambda"])
    for index in range(year_index, len(YEAR_ORDER)):
        year = YEAR_ORDER[index]
        epoch_start = next_epoch if index == year_index else 1
        for epoch in range(epoch_start, epochs + 1):
            shuffle_seed = seed + index * epochs + epoch
            loss, samples, safety_loss = train_epoch(model, optimizer, criterion, files[year]["train"], features, replay_memory, safety_memory, device, batch_size, shuffle_seed, safety_lambda)
            yearly.setdefault(str(year), {"epochs": []})["epochs"].append({"epoch": epoch, "loss": loss, "safety_loss": safety_loss, "samples": samples, "shuffle_seed": shuffle_seed, "completed_at": base.now_utc()})
            snapshot = checkpoint_payload(model, optimizer, replay_memory, safety_memory, index, epoch + 1, yearly, old_positive)
            base.atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / f"epoch-{epoch:02d}.pt", snapshot)
            base.atomic_torch(checkpoint_path, snapshot)
            base.write_status(output_root, "running", f"{arm} {year} 第 {epoch}/{epochs} 轮完成", started_at, {"arm": arm, "year": year, "epoch": epoch})
        surfaces: dict[str, Any] = {}
        surfaces["current_year"], current = base.evaluate_surface(model, arm, year, "current_year", [year], files, features, output_root, device, THRESHOLD, old_positive)
        next_years = [YEAR_ORDER[index + 1]] if index + 1 < len(YEAR_ORDER) else []
        surfaces["next_year"] = {"not_applicable": True} if not next_years else base.evaluate_surface(model, arm, year, "next_year", next_years, files, features, output_root, device, THRESHOLD, old_positive)[0]
        backward_years = YEAR_ORDER[:index]
        surfaces["backward"], backward = ({"not_applicable": True}, {}) if not backward_years else base.evaluate_surface(model, arm, year, "backward", backward_years, files, features, output_root, device, THRESHOLD, old_positive)
        yearly[str(year)]["evaluation"] = surfaces
        old_positive.update(current)
        old_positive.update(backward)
        eligible = collect_safety_memory(model, files[year]["train"], features, safety_memory, device, year, THRESHOLD)
        yearly[str(year)]["safety_memory"] = {"capacity": safety_memory.capacity, "size": int(len(safety_memory.labels)), "seen_correct_malicious_training_samples": safety_memory.seen, "eligible_in_current_training_year": eligible, "updated_after_training_and_evaluation": True}
        if replay_memory is not None:
            for values, labels, hashes, _ in base.iter_parquet(files[year]["train"], features):
                replay_memory.update(values, labels, [base.identity_pair(year, source_hash, row, int(label)) for row, label, source_hash in zip(values, labels, hashes, strict=True)])
            yearly[str(year)]["replay_memory"] = {"capacity": replay_memory.capacity, "size": int(len(replay_memory.labels)), "seen_training_samples": replay_memory.seen, "updated_after_training_and_evaluation": True}
        snapshot = checkpoint_payload(model, optimizer, replay_memory, safety_memory, index + 1, 1, yearly, old_positive)
        base.atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / "year-complete.pt", snapshot)
        base.atomic_torch(checkpoint_path, snapshot)
        base.atomic_json(output_root / "metrics" / arm / f"year-{year}.json", {"arm": arm, "trained_through_year": year, "evaluation": surfaces, "epochs": yearly[str(year)]["epochs"], "safety_memory": yearly[str(year)]["safety_memory"], "replay_memory": yearly[str(year)].get("replay_memory")})
        next_epoch = 1
    return yearly


def aggregate(output_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    years = list(config["evaluation"]["qualification_current_years"])
    result: dict[str, Any] = {"qualification_years": years, "arms": {}, "screening_only": True, "independent_final_test": False}
    for arm in ARMS:
        rows: list[dict[str, Any]] = []
        for year in years:
            path = output_root / "predictions" / arm / f"trained-through-{year}" / "current_year.jsonl"
            with path.open(encoding="utf-8") as handle:
                rows.extend(json.loads(line) for line in handle)
        identities = [row["sample_identity_sha256"] for row in rows]
        if len(identities) != len(set(identities)):
            raise ValueError(f"{arm} 晚期汇总存在重复身份")
        labels = np.asarray([row["label"] for row in rows], dtype=np.int64)
        scores = np.asarray([row["score"] for row in rows], dtype=np.float64)
        result["arms"][arm] = {"current_year_metrics": base.metrics(labels, scores, THRESHOLD), "prediction_count": len(rows), "prediction_sha256": base.hashlib.sha256("".join(identities).encode("ascii")).hexdigest()}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="LAMDA 安全回归约束消融筛查")
    parser.add_argument("--config", type=Path, required=True, help="冻结 JSON 配置")
    parser.add_argument("--resume", action="store_true", help="从同一身份断点恢复")
    parser.add_argument("--validate-config", action="store_true", help="只校验配置")
    args = parser.parse_args()
    config = load_config(args.config.resolve())
    if args.validate_config:
        print(json.dumps({"valid": True, "run_id": config["identity"]["run_id"], "screening_only": True}, ensure_ascii=False))
        return 0
    base_root = Path(config["paths"]["output_root"])
    data_root = Path(config["paths"]["data_root"])
    base.prepare_output(base_root, config, args.config.resolve(), args.resume)
    started_at = base.now_utc()
    started = time.monotonic()
    base.write_status(base_root, "running", "开始 LAMDA 安全回归约束消融", started_at)
    try:
        features, files, manifest = base.verify_input(data_root, config)
        base.atomic_json(base_root / "input-manifest.json", {"input_manifest_path": str(data_root / "manifest.json"), "input_manifest_sha256": base.sha256_file(data_root / "manifest.json"), "manifest": manifest, "published_feature_space_uses_future_covariates": True, "screening_only": True})
        device = base.choose_device()
        base.atomic_json(base_root / "runtime-receipt.json", {"device": str(device), "torch": torch.__version__, "numpy": np.__version__, "platform": platform.platform(), "float32_matmul_precision": config["training"]["float32_matmul_precision"], "torch_compile": False, "safety_lambda": config["security_regression"]["lambda"], "screening_only": True, "started_at": started_at})
        torch.set_float32_matmul_precision(config["training"]["float32_matmul_precision"])
        arm_metrics = {arm: execute_arm(arm, config, features, files, base_root, device, args.resume, started_at) for arm in ARMS}
        summary = aggregate(base_root, config)
        base.atomic_json(base_root / "qualification-summary.json", summary)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        base.atomic_json(base_root / "resource-receipt.json", {"device": str(device), "wall_seconds": time.monotonic() - started, "max_rss": usage.ru_maxrss, "max_rss_unit": "platform_dependent", "cuda_max_memory_allocated": int(torch.cuda.max_memory_allocated()) if device.type == "cuda" else None, "cuda_max_memory_reserved": int(torch.cuda.max_memory_reserved()) if device.type == "cuda" else None})
        base.atomic_json(base_root / "run-manifest.json", {"tool_sha256": base.sha256_file(Path(__file__).resolve()), "config_sha256": base.sha256_file(args.config.resolve()), "arms": ARMS, "screening_only": True})
        base.write_status(base_root, "completed", "安全回归消融完成", started_at)
        return 0
    except Exception as error:
        base.write_status(base_root, "failed", f"{type(error).__name__}: {error}", started_at)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
