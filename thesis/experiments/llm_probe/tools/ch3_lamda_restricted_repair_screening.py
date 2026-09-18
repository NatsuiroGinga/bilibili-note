#!/usr/bin/env python3
"""LAMDA 受限参数修复（head-only）与浅缺口优先课程化暴露的来源／开发期筛查。

四臂：experience_replay（锚点）、gap_repair（全参数修复历史对照）、
restricted_repair（head-only 修复）、restricted_repair_curriculum
（head-only + margin 缺口 d=0.5-old_score 按当年分位数 e/10 由浅到深逐
epoch 暴露）。本工具只产生 screening_only 制品；修复候选只取当前年度真实
恶意且上一冻结模型 score<0.5 的训练样本。运行年份含 2018（train 按到达使用，
test 只在训练后评价，与 2016/2017 同一到达语义）；2019-2023 封印与
2024/2025 探索年一律不读取。
"""

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


RUN_YEARS = [2013, 2014, 2016, 2017, 2018]
SOURCE_YEARS = [2013, 2014]
DEVELOPMENT_YEARS = [2016, 2017, 2018]
SEALED_FINAL_YEARS = [2019, 2020, 2021, 2022, 2023]
ADDITIONAL_UNREAD_YEARS = [2024, 2025]
ARMS = ["experience_replay", "gap_repair", "restricted_repair", "restricted_repair_curriculum"]
THRESHOLD = 0.5
CUR_EXPOSURE = "shallow_gap_first_decile_epochs"
REPAIR_SCOPE = {
    "experience_replay": "no_repair",
    "gap_repair": "full",
    "restricted_repair": "head_only",
    "restricted_repair_curriculum": "head_only",
}


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    data = config.get("data", {})
    if config.get("arms") != ARMS:
        raise ValueError("受限参数修复筛查必须恰有四个预注册实验臂")
    if (
        data.get("run_years") != RUN_YEARS
        or data.get("source_years") != SOURCE_YEARS
        or data.get("development_years") != DEVELOPMENT_YEARS
        or data.get("sealed_final_years") != SEALED_FINAL_YEARS
        or data.get("additional_unread_years") != ADDITIONAL_UNREAD_YEARS
    ):
        raise ValueError("年份角色不符合 D1 冻结数据清单")
    if data.get("published_feature_count") != 4561 or data.get("protocol") != "Domain-IL":
        raise ValueError("LAMDA 输入合同不匹配")
    identity = config.get("identity", {})
    if identity.get("run_tier") != "screening_only" or identity.get("published_feature_space_uses_future_covariates") is not True:
        raise ValueError("受限参数修复筛查只允许 screening_only 且必须披露未来协变量")
    training = config.get("training", {})
    if training.get("seed") != 42 or training.get("epochs_per_year") != 10 or training.get("batch_size") != 1024:
        raise ValueError("训练预算不符合既有公平合同")
    if config.get("replay", {}).get("capacity") != 200:
        raise ValueError("回放容量必须为 200")
    mechanism = config.get("mechanism", {})
    if mechanism.get("repair_weight") != "margin_deficit":
        raise ValueError("修复加权必须为 margin_deficit")
    if mechanism.get("repair_scope") != REPAIR_SCOPE:
        raise ValueError("修复参数作用域分派不匹配（full／head_only）")
    curriculum = mechanism.get("curriculum", {})
    if curriculum.get("arm") != "restricted_repair_curriculum" or curriculum.get("exposure") != CUR_EXPOSURE:
        raise ValueError("浅缺口课程化暴露定义不匹配")
    if config.get("evaluation", {}).get("development_current_years") != DEVELOPMENT_YEARS:
        raise ValueError("开发期评价年份未冻结")
    required_device = config.get("runtime", {}).get("required_device")
    if required_device not in {"mps", "cuda"}:
        raise ValueError("受限参数修复筛查必须显式要求 mps 或 cuda")
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


def verify_input(data_root: Path) -> tuple[list[str], dict[int, dict[str, Path]], dict[str, Any]]:
    """核验数据身份与运行年文件存在性。

    年份角色差异（manifest 曾把 2018 归入 sealed_final_years，本运行按冻结
    D1 合同将 2018 纳入运行/开发期）不在本函数阻断，由 main 原样登记到
    input-manifest.json。
    """
    manifest_path = data_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest.get("source", {})
    if source.get("repo_id") != "IQSeC-Lab/LAMDA" or source.get("revision") != "ad9614bdd5556767f97ced2fce797c2f06408ebf":
        raise ValueError("输入 manifest 的 LAMDA 身份不匹配")
    import csv

    mapping_lines = (data_root / "Baseline/feature_mapping.csv").read_text(encoding="utf-8").splitlines()
    features = [row["mapped_name"] for row in csv.DictReader(mapping_lines)]
    if len(features) != 4561 or len(features) != len(set(features)):
        raise ValueError("特征映射不是 4561 个唯一字段")
    files: dict[int, dict[str, Path]] = {}
    for year in RUN_YEARS:
        root = data_root / "Baseline" / str(year)
        train, test = root / f"{year}_train.parquet", root / f"{year}_test.parquet"
        if not train.is_file() or not test.is_file():
            raise FileNotFoundError(f"年度 train/test 不完整：{year}")
        files[year] = {"train": train, "test": test}
    return features, files, manifest


def old_model_probabilities(model: nn.Module, values: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    parts: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, len(values), base.SCANNER_BATCH_SIZE):
            inputs = torch.from_numpy(values[start : start + base.SCANNER_BATCH_SIZE]).to(device=device, dtype=torch.float32)
            parts.append(model(inputs).cpu().numpy())
    return np.concatenate(parts) if parts else np.empty((0,), dtype=np.float32)


def fpr_on_historical_benign(model: nn.Module, years: list[int], files: dict[int, dict[str, Path]], features: list[str], device: torch.device) -> float | None:
    false_positive = 0
    benign_total = 0
    for year in years:
        for values, labels, _, _ in base.iter_parquet(files[year]["test"], features):
            mask = labels == 0
            if not np.any(mask):
                continue
            probabilities = old_model_probabilities(model, values[mask], device)
            false_positive += int(np.sum(probabilities >= THRESHOLD))
            benign_total += int(np.sum(mask))
    return float(false_positive / benign_total) if benign_total else None


def build_model_and_optimizer(
    features: list[str],
    config: dict[str, Any],
    device: torch.device,
    use_restricted: bool,
) -> tuple[nn.Module, torch.optim.Optimizer]:
    model = base.LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device)
    if use_restricted:
        # 受限修复：骨干冻结，仅头部接收梯度；跨年份骨干保持冻结，不回拷头权重。
        for parameter in model.backbone.parameters():
            parameter.requires_grad = False
        parameters = model.head.parameters()
    else:
        parameters = model.parameters()
    optimizer = torch.optim.SGD(parameters, lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"]))
    return model, optimizer


def margin_and_candidates(
    labels: np.ndarray,
    probabilities: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """margin 缺口 d=0.5-old_score 与候选掩码（真实恶意且旧模型 score<0.5）。"""
    candidates = (labels == 1) & np.isfinite(probabilities) & (probabilities < THRESHOLD)
    margin = np.where(candidates, THRESHOLD - probabilities, 0.0).astype(np.float32)
    return candidates, margin


def curriculum_exposure(
    candidates: np.ndarray,
    margin: np.ndarray,
    epoch: int,
    epochs: int,
) -> tuple[np.ndarray, float | None]:
    """epoch e 只把 margin 缺口 d 落在当年候选 d 的 e/10 分位以内的样本计入。"""
    if not np.any(candidates):
        return np.zeros(len(candidates), dtype=bool), None
    quantile = float(np.quantile(margin[candidates], epoch / epochs))
    return candidates & (margin <= quantile), quantile


def train_epoch(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    values: np.ndarray,
    labels: np.ndarray,
    repair_mask: np.ndarray,
    repair_weights: np.ndarray,
    replay_values: np.ndarray,
    replay_labels: np.ndarray,
    device: torch.device,
    batch_size: int,
    shuffle_seed: int,
    use_repair: bool,
) -> tuple[float, int, dict[str, float | int]]:
    model.train()
    train_values, train_labels = values, labels
    train_repair, train_weights = repair_mask, repair_weights
    if len(replay_labels):
        train_values = np.concatenate((train_values, replay_values), axis=0)
        train_labels = np.concatenate((train_labels, replay_labels), axis=0)
        train_repair = np.concatenate((train_repair, np.zeros(len(replay_labels), dtype=bool)), axis=0)
        train_weights = np.concatenate((train_weights, np.zeros(len(replay_labels), dtype=np.float32)), axis=0)
    order = np.random.default_rng(shuffle_seed).permutation(len(train_labels))
    train_values, train_labels = train_values[order], train_labels[order]
    train_repair, train_weights = train_repair[order], train_weights[order]
    total_loss = 0.0
    repair_total = 0.0
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
        if use_repair and np.any(batch_repair):
            repair_inputs = inputs[torch.from_numpy(batch_repair).to(device=device)]
            repair_probabilities = model(repair_inputs)
            weights = torch.from_numpy(batch_weights[batch_repair]).to(device=device, dtype=torch.float32)
            repair_loss = gap.weighted_repair_loss(repair_probabilities, weights)
            loss = loss + repair_loss
        loss.backward()
        optimizer.step()
        count = len(batch_labels)
        total_loss += float(loss.detach().item()) * count
        repair_total += float(repair_loss.detach().item()) * count
        total_samples += count
    if total_samples == 0:
        raise RuntimeError("训练批次为空")
    return (
        total_loss / total_samples,
        total_samples,
        {
            "repair_loss": repair_total / total_samples,
            "repair_candidates_in_training": int(np.sum(train_repair)),
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
        "schema_version": "ch3-lamda-restricted-repair-screening-checkpoint-v1",
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
    use_repair = arm in {"gap_repair", "restricted_repair", "restricted_repair_curriculum"}
    use_restricted = arm in {"restricted_repair", "restricted_repair_curriculum"}
    use_curriculum = arm == "restricted_repair_curriculum"
    if resume and checkpoint_path.is_file():
        saved = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model, optimizer = build_model_and_optimizer(features, config, device, use_restricted)
        model.load_state_dict(saved["model"])
        optimizer.load_state_dict(saved["optimizer"])
        memory = base.Reservoir.from_state(saved["memory"])
        year_index, next_epoch = int(saved["year_index"]), int(saved["next_epoch"])
        yearly, old_positive, context = dict(saved["yearly"]), dict(saved["old_positive"]), saved.get("context")
        base.restore_rng(saved["rng"])
    else:
        base.seed_everything(seed)
        model, optimizer = build_model_and_optimizer(features, config, device, use_restricted)
        memory = base.Reservoir(int(config["replay"]["capacity"]), len(features), seed)
        year_index, next_epoch, yearly, old_positive, context = 0, 1, {}, {}, None
    criterion = nn.BCELoss()
    epochs = int(config["training"]["epochs_per_year"])
    batch_size = int(config["training"]["batch_size"])
    for index in range(year_index, len(RUN_YEARS)):
        year = RUN_YEARS[index]
        values, labels, hashes = load_train(files[year]["train"], features)
        if index == year_index and next_epoch > 1 and context is not None:
            probabilities = np.asarray(context["probabilities"], dtype=np.float32)
        else:
            # 只对到达年份的第 2 年起产生旧模型教师；首年无修复候选。
            probabilities = old_model_probabilities(model, values, device) if index else np.full(len(labels), np.nan, dtype=np.float32)
            context = {"year": year, "probabilities": probabilities}
        candidates, margin = margin_and_candidates(labels, probabilities)
        replay_values = memory.values.copy() if len(memory.labels) else np.empty((0, len(features)), dtype=np.uint8)
        replay_labels = memory.labels.copy() if len(memory.labels) else np.empty((0,), dtype=np.int64)
        epoch_start = next_epoch if index == year_index else 1
        for epoch in range(epoch_start, epochs + 1):
            if use_curriculum:
                exposed, decile_quantile = curriculum_exposure(candidates, margin, epoch, epochs)
            else:
                exposed, decile_quantile = candidates, None
            exposed_weights = np.where(exposed, margin, 0.0).astype(np.float32)
            loss, samples, auxiliary = train_epoch(model, optimizer, criterion, values, labels, exposed, exposed_weights, replay_values, replay_labels, device, batch_size, seed + index * epochs + epoch, use_repair)
            entry: dict[str, Any] = {"epoch": epoch, "loss": loss, "samples": samples, "auxiliary": auxiliary, "repair_candidates": int(np.sum(candidates)), "exposed_repair_candidates": int(np.sum(exposed)), "completed_at": base.now_utc()}
            if decile_quantile is not None:
                entry["curriculum_exposure_quantile"] = decile_quantile
            yearly.setdefault(str(year), {"epochs": []})["epochs"].append(entry)
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
    parser = argparse.ArgumentParser(description="LAMDA 受限参数修复（head-only）与浅缺口课程化暴露筛查")
    parser.add_argument("--config", type=Path, required=True, help="冻结 JSON 配置")
    parser.add_argument("--resume", action="store_true", help="从同一身份最新断点恢复")
    parser.add_argument("--validate-config", action="store_true", help="只校验配置")
    args = parser.parse_args()
    config = load_config(args.config.resolve())
    if args.validate_config:
        print(json.dumps({"valid": True, "run_id": config["identity"]["run_id"], "run_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "additional_unread_years": ADDITIONAL_UNREAD_YEARS, "screening_only": True}, ensure_ascii=False))
        return 0
    output_root = Path(config["paths"]["output_root"])
    data_root = Path(config["paths"]["data_root"])
    base.prepare_output(output_root, config, args.config.resolve(), args.resume)
    started_at = base.now_utc()
    started = time.monotonic()
    base.write_status(output_root, "running", "开始 LAMDA 受限参数修复（head-only）筛查", started_at)
    try:
        features, files, manifest = verify_input(data_root)
        manifest_roles = manifest.get("data_roles", {})
        role_difference_note = (
            "manifest 将 2018 归入 sealed_final_years；本运行按冻结 D1 合同以工具常量为准："
            "RUN_YEARS=[2013,2014,2016,2017,2018]、DEVELOPMENT_YEARS=[2016,2017,2018]、"
            "SEALED_FINAL_YEARS=[2019,2020,2021,2022,2023]；2018 train 标签按到达使用、"
            "2018 test 只在训练后评价；2019-2023 封印与 2024/2025 探索年一律不读取。"
            "未修改任何数据文件。"
        )
        base.atomic_json(output_root / "input-manifest.json", {"input_manifest_path": str(data_root / "manifest.json"), "input_manifest_sha256": base.sha256_file(data_root / "manifest.json"), "manifest": manifest, "tool_year_roles": {"run_years": RUN_YEARS, "source_years": SOURCE_YEARS, "development_years": DEVELOPMENT_YEARS, "sealed_final_years": SEALED_FINAL_YEARS, "additional_unread_years": ADDITIONAL_UNREAD_YEARS}, "manifest_data_roles": manifest_roles, "role_difference_note": role_difference_note, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "additional_unread_years_not_read": ADDITIONAL_UNREAD_YEARS, "published_feature_space_uses_future_covariates": True, "screening_only": True})
        device = base.choose_device()
        required_device = config["runtime"]["required_device"]
        if device.type != required_device:
            raise RuntimeError(f"配置要求 {required_device}，但设备探测为 {device.type}；禁止静默回退")
        torch.set_float32_matmul_precision(config["training"]["float32_matmul_precision"])
        base.atomic_json(output_root / "runtime-receipt.json", {"device": str(device), "required_device": required_device, "mps_built": bool(torch.backends.mps.is_built()), "mps_available": bool(torch.backends.mps.is_available()), "torch": torch.__version__, "numpy": np.__version__, "platform": platform.platform(), "float32_matmul_precision": config["training"]["float32_matmul_precision"], "torch_compile": False, "screening_only": True, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "additional_unread_years_not_read": ADDITIONAL_UNREAD_YEARS, "started_at": started_at})
        for arm in ARMS:
            execute_arm(arm, config, features, files, output_root, device, args.resume, started_at)
        base.atomic_json(output_root / "development-summary.json", aggregate_development(output_root))
        usage = resource.getrusage(resource.RUSAGE_SELF)
        base.atomic_json(output_root / "resource-receipt.json", {"device": str(device), "required_device": required_device, "wall_seconds": time.monotonic() - started, "max_rss": usage.ru_maxrss, "max_rss_unit": "platform_dependent", "cuda_max_memory_allocated": int(torch.cuda.max_memory_allocated()) if device.type == "cuda" else None, "cuda_max_memory_reserved": int(torch.cuda.max_memory_reserved()) if device.type == "cuda" else None})
        base.atomic_json(output_root / "run-manifest.json", {"tool_sha256": base.sha256_file(Path(__file__).resolve()), "config_sha256": base.sha256_file(args.config.resolve()), "arms": ARMS, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "additional_unread_years_not_read": ADDITIONAL_UNREAD_YEARS, "screening_only": True})
        base.write_status(output_root, "completed", "LAMDA 受限参数修复（head-only）筛查完成", started_at)
        return 0
    except Exception as error:
        base.write_status(output_root, "failed", f"{type(error).__name__}: {error}", started_at)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
