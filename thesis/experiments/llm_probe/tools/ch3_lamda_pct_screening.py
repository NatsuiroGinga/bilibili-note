#!/usr/bin/env python3
"""LAMDA PCT/Focal Distillation 与恶意漏判修复来源／开发期筛查。"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

import ch3_lamda_gap_repair_screening as gap


base = gap.base
RUN_YEARS = [2013, 2014, 2016, 2017]
SOURCE_YEARS = [2013, 2014]
DEVELOPMENT_YEARS = [2016, 2017]
SEALED_FINAL_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
ARMS = ["experience_replay", "pct", "gap_repair", "gap_repair_pct"]
THRESHOLD = 0.5


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    data = config.get("data", {})
    if config.get("arms") != ARMS:
        raise ValueError("PCT 筛查必须恰有四个预注册实验臂")
    if data.get("run_years") != RUN_YEARS or data.get("source_years") != SOURCE_YEARS or data.get("development_years") != DEVELOPMENT_YEARS or data.get("sealed_final_years") != SEALED_FINAL_YEARS:
        raise ValueError("年份角色不符合 LAMDA 数据清单")
    if data.get("published_feature_count") != 4561 or data.get("protocol") != "Domain-IL":
        raise ValueError("LAMDA 输入合同不匹配")
    identity = config.get("identity", {})
    if identity.get("run_tier") != "screening_only" or identity.get("published_feature_space_uses_future_covariates") is not True:
        raise ValueError("PCT 筛查只允许 screening_only 且必须披露未来协变量")
    training = config.get("training", {})
    if training.get("seed") != 42 or training.get("epochs_per_year") != 10 or training.get("batch_size") != 1024:
        raise ValueError("训练预算不符合既有公平合同")
    if config.get("replay", {}).get("capacity") != 200:
        raise ValueError("回放容量必须为 200")
    pct = config.get("pct", {})
    if pct.get("distance") != "logit_matching" or pct.get("alpha") != 1.0 or pct.get("beta") != 5.0 or pct.get("lambda") != 1.0:
        raise ValueError("PCT 论文起始配置不匹配")
    if config.get("evaluation", {}).get("development_current_years") != DEVELOPMENT_YEARS:
        raise ValueError("开发期评价年份未冻结")
    return config


def logit_scores(model: nn.Module, values: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    parts: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, len(values), base.SCANNER_BATCH_SIZE):
            inputs = torch.from_numpy(values[start : start + base.SCANNER_BATCH_SIZE]).to(device=device, dtype=torch.float32)
            logits = model.head[:-1](model.backbone(inputs)).squeeze(1)
            parts.append(logits.cpu().numpy())
    return np.concatenate(parts) if parts else np.empty((0,), dtype=np.float32)


def fpr_on_historical_benign(model: nn.Module, years: list[int], files: dict[int, dict[str, Path]], features: list[str], device: torch.device) -> float | None:
    false_positive = 0
    benign_total = 0
    for year in years:
        for values, labels, _, _ in base.iter_parquet(files[year]["test"], features):
            mask = labels == 0
            if not np.any(mask):
                continue
            scores = gap.teacher_scores(model, values[mask], device)
            false_positive += int(np.sum(scores >= THRESHOLD))
            benign_total += int(np.sum(mask))
    return float(false_positive / benign_total) if benign_total else None


def train_epoch(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    values: np.ndarray,
    labels: np.ndarray,
    repair_mask: np.ndarray,
    repair_weights: np.ndarray,
    pct_logits: np.ndarray,
    pct_known: np.ndarray,
    pct_correct: np.ndarray,
    device: torch.device,
    batch_size: int,
    shuffle_seed: int,
    use_gap_repair: bool,
    use_pct: bool,
    pct_alpha: float,
    pct_beta: float,
    lambda_repair: float,
    lambda_pct: float,
) -> tuple[float, int, dict[str, float | int]]:
    model.train()
    order = np.random.default_rng(shuffle_seed).permutation(len(labels))
    values, labels = values[order], labels[order]
    repair_mask, repair_weights = repair_mask[order], repair_weights[order]
    pct_logits, pct_known, pct_correct = pct_logits[order], pct_known[order], pct_correct[order]
    total_loss = 0.0
    repair_loss_total = 0.0
    pct_loss_total = 0.0
    total_samples = 0
    for start in range(0, len(labels), batch_size):
        batch_values = values[start : start + batch_size]
        batch_labels = labels[start : start + batch_size]
        batch_repair = repair_mask[start : start + batch_size]
        batch_weights = repair_weights[start : start + batch_size]
        batch_known = pct_known[start : start + batch_size]
        batch_correct = pct_correct[start : start + batch_size]
        batch_old_logits = pct_logits[start : start + batch_size]
        inputs = torch.from_numpy(batch_values).to(device=device, dtype=torch.float32)
        targets = torch.from_numpy(batch_labels.astype(np.float32, copy=False)).to(device=device)
        optimizer.zero_grad(set_to_none=True)
        probabilities = model(inputs)
        loss = criterion(probabilities, targets)
        repair_loss = torch.zeros((), device=device)
        pct_loss = torch.zeros((), device=device)
        if use_gap_repair and np.any(batch_repair):
            repair_inputs = inputs[torch.from_numpy(batch_repair).to(device=device)]
            repair_probabilities = model(repair_inputs)
            weights = torch.from_numpy(batch_weights[batch_repair]).to(device=device, dtype=torch.float32)
            repair_loss = gap.weighted_repair_loss(repair_probabilities, weights)
            loss = loss + lambda_repair * repair_loss
        if use_pct and np.any(batch_known):
            pct_inputs = inputs[torch.from_numpy(batch_known).to(device=device)]
            new_logits = model.head[:-1](model.backbone(pct_inputs)).squeeze(1)
            old_logits = torch.from_numpy(batch_old_logits[batch_known]).to(device=device, dtype=torch.float32)
            correct = torch.from_numpy(batch_correct[batch_known].astype(np.float32, copy=False)).to(device=device)
            weights = pct_alpha + pct_beta * correct
            pct_loss = (weights * 0.5 * (new_logits - old_logits).square()).sum() / torch.clamp(weights.sum(), min=torch.finfo(weights.dtype).eps)
            loss = loss + lambda_pct * pct_loss
        loss.backward()
        optimizer.step()
        count = len(batch_labels)
        total_loss += float(loss.item()) * count
        repair_loss_total += float(repair_loss.item()) * count
        pct_loss_total += float(pct_loss.item()) * count
        total_samples += count
    if total_samples == 0:
        raise RuntimeError("训练批次为空")
    return total_loss / total_samples, total_samples, {"repair_loss": repair_loss_total / total_samples, "pct_loss": pct_loss_total / total_samples, "repair_candidates": int(np.sum(repair_mask)), "pct_known": int(np.sum(pct_known))}


def checkpoint_payload(model: nn.Module, optimizer: torch.optim.Optimizer, memory: base.Reservoir, year_index: int, next_epoch: int, yearly: dict[str, Any], old_positive: dict[str, bool], context: dict[str, Any] | None) -> dict[str, Any]:
    return {"schema_version": "ch3-lamda-pct-screening-checkpoint-v1", "model": model.state_dict(), "optimizer": optimizer.state_dict(), "memory": memory.state_dict(), "year_index": year_index, "next_epoch": next_epoch, "yearly": yearly, "old_positive": old_positive, "context": context, "rng": base.rng_state(), "saved_at": base.now_utc()}


def execute_arm(arm: str, config: dict[str, Any], features: list[str], files: dict[int, dict[str, Path]], output_root: Path, device: torch.device, resume: bool, started_at: str) -> None:
    checkpoint_path = output_root / "checkpoints" / arm / "latest.pt"
    seed = int(config["training"]["seed"])
    use_gap_repair = arm in {"gap_repair", "gap_repair_pct"}
    use_pct = arm in {"pct", "gap_repair_pct"}
    pct_alpha = float(config["pct"]["alpha"])
    pct_beta = float(config["pct"]["beta"])
    lambda_repair = float(config["mechanism"]["lambda_repair"])
    lambda_pct = float(config["pct"]["lambda"])
    if resume and checkpoint_path.is_file():
        saved = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model = base.LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device)
        model.load_state_dict(saved["model"])
        optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"]))
        optimizer.load_state_dict(saved["optimizer"])
        memory = base.Reservoir.from_state(saved["memory"])
        year_index, next_epoch = int(saved["year_index"]), int(saved["next_epoch"])
        yearly, old_positive, context = dict(saved["yearly"]), dict(saved["old_positive"]), saved.get("context")
        base.restore_rng(saved["rng"])
    else:
        base.seed_everything(seed)
        model = base.LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device)
        optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"]))
        memory = base.Reservoir(int(config["replay"]["capacity"]), len(features), seed)
        year_index, next_epoch, yearly, old_positive, context = 0, 1, {}, {}, None
    criterion = nn.BCELoss()
    epochs = int(config["training"]["epochs_per_year"])
    batch_size = int(config["training"]["batch_size"])
    for index in range(year_index, len(RUN_YEARS)):
        year = RUN_YEARS[index]
        values, labels, hashes = gap.load_train(files[year]["train"], features)
        if index == year_index and next_epoch > 1 and context is not None:
            old_logits = np.asarray(context["old_logits"], dtype=np.float32)
            repair_mask = np.asarray(context["repair_mask"], dtype=bool)
            repair_weights = np.asarray(context["repair_weights"], dtype=np.float32)
            old_correct = np.asarray(context["old_correct"], dtype=bool)
            old_gate_fpr = context.get("old_gate_fpr")
        else:
            old_logits = logit_scores(model, values, device) if index else np.full(len(labels), np.nan, dtype=np.float32)
            old_probabilities = 1.0 / (1.0 + np.exp(-old_logits))
            repair_mask = (labels == 1) & np.isfinite(old_logits) & (old_probabilities < THRESHOLD)
            repair_weights = np.where(repair_mask, THRESHOLD - old_probabilities, 0.0).astype(np.float32)
            old_correct = (np.isfinite(old_logits) & (((old_probabilities >= THRESHOLD).astype(np.int64)) == labels))
            old_gate_fpr = fpr_on_historical_benign(model, RUN_YEARS[:index], files, features, device) if index else None
            context = {"year": year, "old_logits": old_logits, "repair_mask": repair_mask, "repair_weights": repair_weights, "old_correct": old_correct, "old_gate_fpr": old_gate_fpr}
        memory_logits = logit_scores(model, memory.values, device) if len(memory.labels) else np.empty((0,), dtype=np.float32)
        memory_known = np.isfinite(memory_logits)
        memory_correct = memory_known & ((((1.0 / (1.0 + np.exp(-memory_logits))) >= THRESHOLD).astype(np.int64)) == memory.labels)
        train_values, train_labels = values, labels
        train_repair, train_weights = repair_mask, repair_weights
        train_old_logits, train_known, train_correct = old_logits, np.isfinite(old_logits), old_correct
        if len(memory.labels):
            train_values = np.concatenate((train_values, memory.values), axis=0)
            train_labels = np.concatenate((train_labels, memory.labels), axis=0)
            train_repair = np.concatenate((train_repair, np.zeros(len(memory.labels), dtype=bool)))
            train_weights = np.concatenate((train_weights, np.zeros(len(memory.labels), dtype=np.float32)))
            train_old_logits = np.concatenate((train_old_logits, memory_logits), axis=0)
            train_known = np.concatenate((train_known, memory_known))
            train_correct = np.concatenate((train_correct, memory_correct))
        epoch_start = next_epoch if index == year_index else 1
        for epoch in range(epoch_start, epochs + 1):
            loss, samples, auxiliary = train_epoch(model, optimizer, criterion, train_values, train_labels, train_repair, train_weights, train_old_logits, train_known, train_correct, device, batch_size, seed + index * epochs + epoch, use_gap_repair, use_pct, pct_alpha, pct_beta, lambda_repair, lambda_pct)
            yearly.setdefault(str(year), {"epochs": []})["epochs"].append({"epoch": epoch, "loss": loss, "samples": samples, "auxiliary": auxiliary, "completed_at": base.now_utc()})
            snapshot = checkpoint_payload(model, optimizer, memory, index, epoch + 1, yearly, old_positive, context)
            base.atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / f"epoch-{epoch:02d}.pt", snapshot)
            base.atomic_torch(checkpoint_path, snapshot)
            base.write_status(output_root, "running", f"{arm} {year} 第 {epoch}/{epochs} 轮完成", started_at, {"arm": arm, "year": year, "epoch": epoch})
        surfaces: dict[str, Any] = {}
        surfaces["current_year"], current = base.evaluate_surface(model, arm, year, "current_year", [year], files, features, output_root, device, THRESHOLD, old_positive)
        next_years = [RUN_YEARS[index + 1]] if index + 1 < len(RUN_YEARS) else []
        surfaces["next_year"] = {"not_applicable": True} if not next_years else base.evaluate_surface(model, arm, year, "next_year", next_years, files, features, output_root, device, THRESHOLD, old_positive)[0]
        backward_years = RUN_YEARS[:index]
        surfaces["backward"], backward = ({"not_applicable": True}, {}) if not backward_years else base.evaluate_surface(model, arm, year, "backward", backward_years, files, features, output_root, device, THRESHOLD, old_positive)
        if old_gate_fpr is not None:
            new_gate_fpr = fpr_on_historical_benign(model, backward_years, files, features, device)
            surfaces["historical_benign_gate"] = {"old_fpr": old_gate_fpr, "new_fpr": new_gate_fpr, "not_increased": new_gate_fpr is not None and new_gate_fpr <= old_gate_fpr}
        yearly[str(year)]["evaluation"] = surfaces
        old_positive.update(current)
        old_positive.update(backward)
        for chunk_values, chunk_labels, chunk_hashes, _ in base.iter_parquet(files[year]["train"], features):
            memory.update(chunk_values, chunk_labels, [base.identity_pair(year, source_hash, row, int(label)) for row, label, source_hash in zip(chunk_values, chunk_labels, chunk_hashes, strict=True)])
        yearly[str(year)]["memory"] = {"capacity": memory.capacity, "size": int(len(memory.labels)), "seen_training_samples": memory.seen, "updated_after_training_and_evaluation": True}
        context = None
        snapshot = checkpoint_payload(model, optimizer, memory, index + 1, 1, yearly, old_positive, context)
        base.atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / "year-complete.pt", snapshot)
        base.atomic_torch(checkpoint_path, snapshot)
        base.atomic_json(output_root / "metrics" / arm / f"year-{year}.json", {"arm": arm, "trained_through_year": year, "evaluation": surfaces, "epochs": yearly[str(year)]["epochs"], "memory": yearly[str(year)]["memory"]})
        next_epoch = 1


def aggregate_development(output_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"development_years": DEVELOPMENT_YEARS, "arms": {}, "screening_only": True, "independent_final_test": False}
    for arm in ARMS:
        rows: list[dict[str, Any]] = []
        for year in DEVELOPMENT_YEARS:
            with (output_root / "predictions" / arm / f"trained-through-{year}" / "current_year.jsonl").open(encoding="utf-8") as handle:
                rows.extend(json.loads(line) for line in handle)
        identities = [row["sample_identity_sha256"] for row in rows]
        if len(identities) != len(set(identities)):
            raise ValueError(f"{arm} 开发期汇总存在重复身份")
        labels = np.asarray([row["label"] for row in rows], dtype=np.int64)
        scores = np.asarray([row["score"] for row in rows], dtype=np.float64)
        result["arms"][arm] = {"current_year_metrics": base.metrics(labels, scores, THRESHOLD), "prediction_count": len(rows), "prediction_sha256": hashlib.sha256("".join(identities).encode("ascii")).hexdigest()}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="LAMDA 来源／开发期 PCT 与恶意漏判修复筛查")
    parser.add_argument("--config", type=Path, required=True, help="冻结 JSON 配置")
    parser.add_argument("--resume", action="store_true", help="从同一身份最新断点恢复")
    parser.add_argument("--validate-config", action="store_true", help="只校验配置")
    args = parser.parse_args()
    config = load_config(args.config.resolve())
    if args.validate_config:
        print(json.dumps({"valid": True, "run_id": config["identity"]["run_id"], "run_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "screening_only": True}, ensure_ascii=False))
        return 0
    output_root = Path(config["paths"]["output_root"])
    data_root = Path(config["paths"]["data_root"])
    base.prepare_output(output_root, config, args.config.resolve(), args.resume)
    started_at = base.now_utc()
    started = time.monotonic()
    base.write_status(output_root, "running", "开始 LAMDA PCT 与恶意漏判修复筛查", started_at)
    try:
        features, files, manifest = gap.verify_input(data_root)
        base.atomic_json(output_root / "input-manifest.json", {"input_manifest_path": str(data_root / "manifest.json"), "input_manifest_sha256": base.sha256_file(data_root / "manifest.json"), "manifest": manifest, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "published_feature_space_uses_future_covariates": True, "screening_only": True})
        device = base.choose_device()
        torch.set_float32_matmul_precision(config["training"]["float32_matmul_precision"])
        base.atomic_json(output_root / "runtime-receipt.json", {"device": str(device), "torch": torch.__version__, "numpy": np.__version__, "platform": platform.platform(), "float32_matmul_precision": config["training"]["float32_matmul_precision"], "torch_compile": False, "screening_only": True, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "started_at": started_at})
        for arm in ARMS:
            execute_arm(arm, config, features, files, output_root, device, args.resume, started_at)
        base.atomic_json(output_root / "development-summary.json", aggregate_development(output_root, config))
        usage = resource.getrusage(resource.RUSAGE_SELF)
        base.atomic_json(output_root / "resource-receipt.json", {"device": str(device), "wall_seconds": time.monotonic() - started, "max_rss": usage.ru_maxrss, "max_rss_unit": "platform_dependent", "cuda_max_memory_allocated": int(torch.cuda.max_memory_allocated()) if device.type == "cuda" else None, "cuda_max_memory_reserved": int(torch.cuda.max_memory_reserved()) if device.type == "cuda" else None})
        base.atomic_json(output_root / "run-manifest.json", {"tool_sha256": base.sha256_file(Path(__file__).resolve()), "config_sha256": base.sha256_file(args.config.resolve()), "arms": ARMS, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "screening_only": True})
        base.write_status(output_root, "completed", "LAMDA PCT 与恶意漏判修复筛查完成", started_at)
        return 0
    except Exception as error:
        base.write_status(output_root, "failed", f"{type(error).__name__}: {error}", started_at)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
