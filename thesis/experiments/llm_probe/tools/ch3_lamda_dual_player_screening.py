#!/usr/bin/env python3
"""LAMDA 双玩家速率约束回放的来源／开发期筛选。"""

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

import ch3_lamda_domain_il_replay_screening as base
import ch3_lamda_gap_repair_screening as gap


RUN_YEARS = [2013, 2014, 2016, 2017]
SOURCE_YEARS = [2013, 2014]
DEVELOPMENT_YEARS = [2016, 2017]
SEALED_FINAL_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
ARMS = ["experience_replay", "gap_repair", "dual_player", "gap_repair_dual_player"]
THRESHOLD = 0.5


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    data = config.get("data", {})
    if config.get("arms") != ARMS:
        raise ValueError("双玩家筛查必须恰有四个预注册实验臂")
    if data.get("run_years") != RUN_YEARS or data.get("source_years") != SOURCE_YEARS or data.get("development_years") != DEVELOPMENT_YEARS or data.get("sealed_final_years") != SEALED_FINAL_YEARS:
        raise ValueError("年份角色不符合 LAMDA 数据清单")
    if data.get("published_feature_count") != 4561 or data.get("protocol") != "Domain-IL":
        raise ValueError("LAMDA 输入合同不匹配")
    identity = config.get("identity", {})
    if identity.get("run_tier") != "screening_only" or identity.get("published_feature_space_uses_future_covariates") is not True:
        raise ValueError("双玩家筛查只允许 screening_only 且必须披露未来协变量")
    training = config.get("training", {})
    if training.get("seed") != 42 or training.get("epochs_per_year") != 10 or training.get("batch_size") != 1024:
        raise ValueError("训练预算不符合既有公平合同")
    if config.get("replay", {}).get("capacity") != 200:
        raise ValueError("回放容量必须为 200")
    mechanism = config.get("mechanism", {})
    if mechanism.get("repair_weight") != "margin_deficit" or mechanism.get("risk_constraint") != "dual_player_proxy_lagrangian":
        raise ValueError("双玩家机制定义不匹配")
    dual = config.get("dual_player", {})
    if dual.get("lambda_lr") != 1.0 or dual.get("initial_lambda") != 0.0:
        raise ValueError("双玩家乘子起始配置不匹配")
    if config.get("evaluation", {}).get("development_current_years") != DEVELOPMENT_YEARS:
        raise ValueError("开发期评价年份未冻结")
    required_device = config.get("runtime", {}).get("required_device")
    if required_device not in {"mps", "cuda"}:
        raise ValueError("双玩家筛查必须显式要求 mps 或 cuda")
    return config


def load_train(path: Path, features: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values, labels, hashes = [], [], []
    for batch_values, batch_labels, batch_hashes, _ in gap.base.iter_parquet(path, features):
        values.append(batch_values)
        labels.append(batch_labels)
        hashes.append(batch_hashes)
    if not labels:
        raise RuntimeError(f"年度训练未读取到样本：{path}")
    return np.concatenate(values), np.concatenate(labels), np.concatenate(hashes)


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
            logits = logit_scores(model, values[mask], device)
            false_positive += int(np.sum((1.0 / (1.0 + np.exp(-logits))) >= THRESHOLD))
            benign_total += int(np.sum(mask))
    return float(false_positive / benign_total) if benign_total else None


def risk_proxies(model: nn.Module, benign_values: np.ndarray, protect_values: np.ndarray, device: torch.device) -> tuple[float, float]:
    model.eval()
    with torch.inference_mode():
        if len(benign_values):
            benign = torch.from_numpy(benign_values).to(device=device, dtype=torch.float32)
            benign_risk = float(model(benign).mean().item())
        else:
            benign_risk = 0.0
        if len(protect_values):
            protect = torch.from_numpy(protect_values).to(device=device, dtype=torch.float32)
            logits = model.head[:-1](model.backbone(protect)).squeeze(1)
            malicious_risk = float(torch.nn.functional.softplus(-logits).mean().item())
        else:
            malicious_risk = 0.0
    return benign_risk, malicious_risk


def hard_risk_rates(model: nn.Module, benign_values: np.ndarray, protect_values: np.ndarray, device: torch.device) -> tuple[float, float]:
    model.eval()
    with torch.inference_mode():
        if len(benign_values):
            benign = torch.from_numpy(benign_values).to(device=device, dtype=torch.float32)
            benign_rate = float(torch.mean((model(benign) >= THRESHOLD).to(torch.float32)).item())
        else:
            benign_rate = 0.0
        if len(protect_values):
            protect = torch.from_numpy(protect_values).to(device=device, dtype=torch.float32)
            logits = model.head[:-1](model.backbone(protect)).squeeze(1)
            malicious_rate = float(torch.mean((logits < 0.0).to(torch.float32)).item())
        else:
            malicious_rate = 0.0
    return benign_rate, malicious_rate


def train_epoch(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    values: np.ndarray,
    labels: np.ndarray,
    repair_mask: np.ndarray,
    repair_weights: np.ndarray,
    benign_values: np.ndarray,
    protect_values: np.ndarray,
    rho_benign: float,
    rho_malicious: float,
    hard_rho_benign: float,
    hard_rho_malicious: float,
    lambda_benign: float,
    lambda_malicious: float,
    lambda_lr: float,
    device: torch.device,
    batch_size: int,
    shuffle_seed: int,
    use_gap_repair: bool,
    use_dual_player: bool,
) -> tuple[float, int, float, float, dict[str, float | int]]:
    model.train()
    train_values, train_labels = values, labels
    train_repair, train_weights = repair_mask, repair_weights
    order = np.random.default_rng(shuffle_seed).permutation(len(train_labels))
    train_values, train_labels = train_values[order], train_labels[order]
    train_repair, train_weights = train_repair[order], train_weights[order]
    benign_tensor = torch.from_numpy(benign_values).to(device=device, dtype=torch.float32) if len(benign_values) else None
    protect_tensor = torch.from_numpy(protect_values).to(device=device, dtype=torch.float32) if len(protect_values) else None
    total_loss = 0.0
    repair_total = 0.0
    benign_residual_total = 0.0
    malicious_residual_total = 0.0
    total_samples = 0
    for start in range(0, len(train_labels), batch_size):
        batch_values = train_values[start : start + batch_size]
        batch_labels = train_labels[start : start + batch_size]
        batch_repair = train_repair[start : start + batch_size]
        batch_weights = train_weights[start : start + batch_size]
        inputs = torch.from_numpy(batch_values).to(device=device, dtype=torch.float32)
        targets = torch.from_numpy(batch_labels.astype(np.float32, copy=False)).to(device=device)
        optimizer.zero_grad(set_to_none=True)
        probabilities = model(inputs)
        loss = criterion(probabilities, targets)
        repair_loss = torch.zeros((), device=device)
        if use_gap_repair and np.any(batch_repair):
            repair_inputs = inputs[torch.from_numpy(batch_repair).to(device=device)]
            repair_probabilities = model(repair_inputs)
            weights = torch.from_numpy(batch_weights[batch_repair]).to(device=device, dtype=torch.float32)
            repair_loss = gap.weighted_repair_loss(repair_probabilities, weights)
            loss = loss + repair_loss
        benign_residual = torch.zeros((), device=device)
        malicious_residual = torch.zeros((), device=device)
        if use_dual_player and (benign_tensor is not None or protect_tensor is not None):
            # 安全代理关闭 dropout，避免同一 reference 在批次间产生随机约束梯度。
            model.eval()
            if benign_tensor is not None:
                benign_residual = torch.nn.functional.softplus(model.head[:-1](model.backbone(benign_tensor)).squeeze(1)).mean() - rho_benign
                loss = loss + lambda_benign * benign_residual
            if protect_tensor is not None:
                protect_logits = model.head[:-1](model.backbone(protect_tensor)).squeeze(1)
                malicious_residual = torch.nn.functional.softplus(-protect_logits).mean() - rho_malicious
                loss = loss + lambda_malicious * malicious_residual
            model.train()
        loss.backward()
        optimizer.step()
        count = len(batch_labels)
        total_loss += float(loss.detach().item()) * count
        repair_total += float(repair_loss.detach().item()) * count
        benign_residual_total += float(benign_residual.detach().item()) * count
        malicious_residual_total += float(malicious_residual.detach().item()) * count
        total_samples += count
    if total_samples == 0:
        raise RuntimeError("训练批次为空")
    hard_benign, hard_malicious = hard_risk_rates(model, benign_values, protect_values, device) if use_dual_player else (0.0, 0.0)
    hard_benign_residual = hard_benign - hard_rho_benign if use_dual_player and len(benign_values) else 0.0
    hard_malicious_residual = hard_malicious - hard_rho_malicious if use_dual_player and len(protect_values) else 0.0
    if use_dual_player:
        # 约束玩家每个 epoch 只依据一次 hard rate 更新，避免逐批次累加造成乘子爆炸。
        lambda_benign = max(0.0, lambda_benign + lambda_lr * hard_benign_residual)
        lambda_malicious = max(0.0, lambda_malicious + lambda_lr * hard_malicious_residual)
    return (
        total_loss / total_samples,
        total_samples,
        lambda_benign,
        lambda_malicious,
        {
            "repair_loss": repair_total / total_samples,
            "benign_proxy_residual": benign_residual_total / total_samples,
            "malicious_proxy_residual": malicious_residual_total / total_samples,
            "repair_candidates": int(np.sum(repair_mask)),
            "dual_updates": int(hard_benign_residual > 0.0) + int(hard_malicious_residual > 0.0),
            "hard_benign_rate": hard_benign,
            "hard_malicious_regression_rate": hard_malicious,
            "hard_benign_residual": hard_benign_residual,
            "hard_malicious_residual": hard_malicious_residual,
        },
    )


def checkpoint_payload(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    memory: base.Reservoir,
    year_index: int,
    next_epoch: int,
    yearly: dict[str, Any],
    old_positive: dict[str, bool],
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": "ch3-lamda-dual-player-screening-checkpoint-v1",
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "memory": memory.state_dict(),
        "year_index": year_index,
        "next_epoch": next_epoch,
        "yearly": yearly,
        "old_positive": old_positive,
        "context": context,
        "rng": base.rng_state(),
        "saved_at": base.now_utc(),
    }


def execute_arm(
    arm: str,
    config: dict[str, Any],
    features: list[str],
    files: dict[int, dict[str, Path]],
    output_root: Path,
    device: torch.device,
    resume: bool,
    started_at: str,
) -> None:
    checkpoint_path = output_root / "checkpoints" / arm / "latest.pt"
    seed = int(config["training"]["seed"])
    use_gap_repair = arm in {"gap_repair", "gap_repair_dual_player"}
    use_dual_player = arm in {"dual_player", "gap_repair_dual_player"}
    lambda_lr = float(config["dual_player"]["lambda_lr"])
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
        values, labels, hashes = load_train(files[year]["train"], features)
        if index == year_index and next_epoch > 1 and context is not None:
            teacher = np.asarray(context["teacher"], dtype=np.float32)
            repair_mask = np.asarray(context["repair_mask"], dtype=bool)
            repair_weights = np.asarray(context["repair_weights"], dtype=np.float32)
            benign_values = np.asarray(context["benign_values"], dtype=np.uint8)
            protect_values = np.asarray(context["protect_values"], dtype=np.uint8)
            rho_benign = float(context["rho_benign"])
            rho_malicious = float(context["rho_malicious"])
            hard_rho_benign = float(context["hard_rho_benign"])
            hard_rho_malicious = float(context["hard_rho_malicious"])
            lambda_benign = float(context["lambda_benign"])
            lambda_malicious = float(context["lambda_malicious"])
        else:
            teacher = logit_scores(model, values, device) if index else np.full(len(labels), np.nan, dtype=np.float32)
            old_probabilities = 1.0 / (1.0 + np.exp(-teacher))
            repair_mask = (labels == 1) & np.isfinite(teacher) & (old_probabilities < THRESHOLD) if use_gap_repair else np.zeros(len(labels), dtype=bool)
            repair_weights = np.where(repair_mask, THRESHOLD - old_probabilities, 0.0).astype(np.float32)
            memory_logits = logit_scores(model, memory.values, device) if len(memory.labels) else np.empty((0,), dtype=np.float32)
            benign_values = memory.values[memory.labels == 0].copy() if len(memory.labels) else np.empty((0, len(features)), dtype=np.uint8)
            protect_values = memory.values[(memory.labels == 1) & (memory_logits >= 0.0)].copy() if len(memory.labels) else np.empty((0, len(features)), dtype=np.uint8)
            rho_benign, rho_malicious = risk_proxies(model, benign_values, protect_values, device) if use_dual_player else (0.0, 0.0)
            hard_rho_benign, hard_rho_malicious = hard_risk_rates(model, benign_values, protect_values, device) if use_dual_player else (0.0, 0.0)
            lambda_benign = float(config["dual_player"]["initial_lambda"])
            lambda_malicious = float(config["dual_player"]["initial_lambda"])
            context = {"year": year, "teacher": teacher, "repair_mask": repair_mask, "repair_weights": repair_weights, "benign_values": benign_values, "protect_values": protect_values, "rho_benign": rho_benign, "rho_malicious": rho_malicious, "hard_rho_benign": hard_rho_benign, "hard_rho_malicious": hard_rho_malicious, "lambda_benign": lambda_benign, "lambda_malicious": lambda_malicious}
        replay_values = memory.values.copy() if len(memory.labels) else np.empty((0, len(features)), dtype=np.uint8)
        replay_labels = memory.labels.copy() if len(memory.labels) else np.empty((0,), dtype=np.int64)
        train_values = np.concatenate((values, replay_values), axis=0) if len(replay_labels) else values
        train_labels = np.concatenate((labels, replay_labels), axis=0) if len(replay_labels) else labels
        train_repair = np.concatenate((repair_mask, np.zeros(len(replay_labels), dtype=bool)), axis=0) if len(replay_labels) else repair_mask
        train_weights = np.concatenate((repair_weights, np.zeros(len(replay_labels), dtype=np.float32)), axis=0) if len(replay_labels) else repair_weights
        epoch_start = next_epoch if index == year_index else 1
        for epoch in range(epoch_start, epochs + 1):
            loss, samples, lambda_benign, lambda_malicious, auxiliary = train_epoch(model, optimizer, criterion, train_values, train_labels, train_repair, train_weights, benign_values, protect_values, rho_benign, rho_malicious, hard_rho_benign, hard_rho_malicious, lambda_benign, lambda_malicious, lambda_lr, device, batch_size, seed + index * epochs + epoch, use_gap_repair, use_dual_player)
            context["lambda_benign"], context["lambda_malicious"] = lambda_benign, lambda_malicious
            yearly.setdefault(str(year), {"epochs": []})["epochs"].append({"epoch": epoch, "loss": loss, "samples": samples, "auxiliary": auxiliary, "lambda_benign": lambda_benign, "lambda_malicious": lambda_malicious, "repair_candidates": int(np.sum(repair_mask)), "protect_candidates": int(len(protect_values)), "benign_reference": int(len(benign_values)), "completed_at": base.now_utc()})
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
        if backward_years:
            old_gate_fpr = fpr_on_historical_benign(model, backward_years, files, features, device)
            surfaces["historical_benign_gate"] = {"new_fpr": old_gate_fpr, "screening_only": True}
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


def aggregate_development(output_root: Path) -> dict[str, Any]:
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
    parser = argparse.ArgumentParser(description="LAMDA 双玩家速率约束来源／开发期筛查")
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
    base.write_status(output_root, "running", "开始 LAMDA 双玩家速率约束筛查", started_at)
    try:
        features, files, manifest = gap.verify_input(data_root)
        base.atomic_json(output_root / "input-manifest.json", {"input_manifest_path": str(data_root / "manifest.json"), "input_manifest_sha256": base.sha256_file(data_root / "manifest.json"), "manifest": manifest, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "published_feature_space_uses_future_covariates": True, "screening_only": True})
        device = base.choose_device()
        required_device = config["runtime"]["required_device"]
        if device.type != required_device:
            raise RuntimeError(f"配置要求 {required_device}，但设备探测为 {device.type}；禁止静默回退")
        torch.set_float32_matmul_precision(config["training"]["float32_matmul_precision"])
        base.atomic_json(output_root / "runtime-receipt.json", {"device": str(device), "required_device": required_device, "mps_built": bool(torch.backends.mps.is_built()), "mps_available": bool(torch.backends.mps.is_available()), "torch": torch.__version__, "numpy": np.__version__, "platform": platform.platform(), "float32_matmul_precision": config["training"]["float32_matmul_precision"], "torch_compile": False, "screening_only": True, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "started_at": started_at})
        for arm in ARMS:
            execute_arm(arm, config, features, files, output_root, device, args.resume, started_at)
        base.atomic_json(output_root / "development-summary.json", aggregate_development(output_root))
        usage = resource.getrusage(resource.RUSAGE_SELF)
        base.atomic_json(output_root / "resource-receipt.json", {"device": str(device), "required_device": required_device, "wall_seconds": time.monotonic() - started, "max_rss": usage.ru_maxrss, "max_rss_unit": "platform_dependent", "cuda_max_memory_allocated": int(torch.cuda.max_memory_allocated()) if device.type == "cuda" else None, "cuda_max_memory_reserved": int(torch.cuda.max_memory_reserved()) if device.type == "cuda" else None})
        base.atomic_json(output_root / "run-manifest.json", {"tool_sha256": base.sha256_file(Path(__file__).resolve()), "config_sha256": base.sha256_file(args.config.resolve()), "arms": ARMS, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "screening_only": True})
        base.write_status(output_root, "completed", "LAMDA 双玩家速率约束筛查完成", started_at)
        return 0
    except Exception as error:
        base.write_status(output_root, "failed", f"{type(error).__name__}: {error}", started_at)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
