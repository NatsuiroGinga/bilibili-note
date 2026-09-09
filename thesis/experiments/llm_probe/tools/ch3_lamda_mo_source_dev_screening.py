#!/usr/bin/env python3
"""LAMDA 来源／开发期 M/O 候选筛查。

该入口只读取 2013、2014 来源年和 2016、2017 开发年，封印年不会被枚举。
M 是总容量 200 的决策角色条件记忆，O 是基于上一年度教师与当前训练标签的
双侧风险修复目标。结果始终是 screening_only，不得当作正式目标期结论。
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


RUN_YEARS = [2013, 2014, 2016, 2017]
SOURCE_YEARS = [2013, 2014]
DEVELOPMENT_YEARS = [2016, 2017]
SEALED_FINAL_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
ARMS = [
    "experience_replay",
    "role_conditioned_memory",
    "risk_repair_update",
    "role_conditioned_memory_risk_repair",
]
ROLE_ORDER = ("protect", "repair", "fp_control", "coverage")
THRESHOLD = 0.5


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("arms") != ARMS:
        raise ValueError("M/O 筛查必须恰有四个具名实验臂")
    data = config.get("data", {})
    if data.get("run_years") != RUN_YEARS or data.get("source_years") != SOURCE_YEARS or data.get("development_years") != DEVELOPMENT_YEARS:
        raise ValueError("来源／开发年份不符合数据清单")
    if data.get("sealed_final_years") != SEALED_FINAL_YEARS:
        raise ValueError("封印年份登记不符合数据清单")
    if data.get("published_feature_count") != 4561 or data.get("protocol") != "Domain-IL":
        raise ValueError("LAMDA 输入合同不匹配")
    identity = config.get("identity", {})
    if identity.get("run_tier") != "screening_only" or identity.get("published_feature_space_uses_future_covariates") is not True:
        raise ValueError("M/O 入口只允许披露未来协变量的 screening_only 身份")
    training = config.get("training", {})
    if training.get("seed") != 42 or training.get("epochs_per_year") != 10 or training.get("batch_size") != 1024:
        raise ValueError("训练预算不符合既有公平比较合同")
    if config.get("replay", {}).get("capacity") != 200 or config.get("mechanism", {}).get("capacity") != 200:
        raise ValueError("两种记忆容量必须均为全程总容量 200")
    if config.get("mechanism", {}).get("role_order") != list(ROLE_ORDER):
        raise ValueError("角色顺序未冻结")
    risk = config.get("risk_repair", {})
    if risk.get("lambda_protect") != 1.0 or risk.get("lambda_repair") != 1.0 or risk.get("lambda_fp_control") != 1.0:
        raise ValueError("筛查阶段风险项必须使用等单位权重")
    if config.get("evaluation", {}).get("development_current_years") != DEVELOPMENT_YEARS:
        raise ValueError("开发期评价年份未冻结")
    return config


def load_train(path: Path, features: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values, labels, hashes = [], [], []
    for batch_values, batch_labels, batch_hashes, _ in base.iter_parquet(path, features):
        values.append(batch_values)
        labels.append(batch_labels)
        hashes.append(batch_hashes)
    if not labels:
        raise RuntimeError(f"年度训练未读取到样本：{path}")
    return np.concatenate(values), np.concatenate(labels), np.concatenate(hashes)


def verify_input(data_root: Path, config: dict[str, Any]) -> tuple[list[str], dict[int, dict[str, Path]], dict[str, Any]]:
    manifest = json.loads((data_root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("source", {}).get("repo_id") != "IQSeC-Lab/LAMDA" or manifest.get("source", {}).get("revision") != "ad9614bdd5556767f97ced2fce797c2f06408ebf":
        raise ValueError("输入 manifest 的 LAMDA 身份不匹配")
    roles = manifest.get("data_roles", {})
    if roles.get("source_years") != SOURCE_YEARS or roles.get("development_years") != DEVELOPMENT_YEARS or roles.get("sealed_final_years") != SEALED_FINAL_YEARS:
        raise ValueError("输入 manifest 的来源／开发／封印角色不匹配")
    mapping_lines = (data_root / "Baseline/feature_mapping.csv").read_text(encoding="utf-8").splitlines()
    if not mapping_lines or "mapped_name" not in mapping_lines[0]:
        raise ValueError("特征映射缺少 mapped_name")
    import csv

    features = [row["mapped_name"] for row in csv.DictReader(mapping_lines)]
    if len(features) != 4561 or len(features) != len(set(features)):
        raise ValueError("发布特征映射不是 4561 个唯一字段")
    files: dict[int, dict[str, Path]] = {}
    for year in RUN_YEARS:
        year_root = data_root / "Baseline" / str(year)
        train = year_root / f"{year}_train.parquet"
        test = year_root / f"{year}_test.parquet"
        if not train.is_file() or not test.is_file():
            raise FileNotFoundError(f"年度 train/test 不完整：{year}")
        files[year] = {"train": train, "test": test}
    return features, files, manifest


class RoleMemory:
    """总容量 200 的角色记忆；角色内按紧迫度排序，角色间轮转取样。"""

    def __init__(self, capacity: int, input_dim: int, seed: int) -> None:
        self.capacity = capacity
        self.input_dim = input_dim
        self.seen = 0
        self.values = np.empty((0, input_dim), dtype=np.uint8)
        self.labels = np.empty((0,), dtype=np.int64)
        self.identities: list[tuple[str, str]] = []
        self.roles: list[str] = []
        self.urgencies = np.empty((0,), dtype=np.float32)
        self.rng = np.random.default_rng(seed)

    def state_dict(self) -> dict[str, Any]:
        return {
            "capacity": self.capacity,
            "input_dim": self.input_dim,
            "seen": self.seen,
            "values": self.values,
            "labels": self.labels,
            "identities": self.identities,
            "roles": self.roles,
            "urgencies": self.urgencies,
            "rng_state": self.rng.bit_generator.state,
        }

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "RoleMemory":
        result = cls(int(state["capacity"]), int(state["input_dim"]), 0)
        result.seen = int(state["seen"])
        result.values = state["values"]
        result.labels = state["labels"]
        result.identities = list(state["identities"])
        result.roles = list(state["roles"])
        result.urgencies = state["urgencies"]
        result.rng.bit_generator.state = state["rng_state"]
        return result

    @staticmethod
    def role_for(label: int, score: float) -> tuple[str, float]:
        if label == 1 and score < THRESHOLD:
            return "repair", float(THRESHOLD - score)
        if label == 1:
            return "protect", float(max(0.0, 1.0 - score))
        if label == 0 and score >= THRESHOLD:
            return "fp_control", float(score - THRESHOLD)
        return "coverage", 0.0

    def replace_from_candidates(
        self,
        values: np.ndarray,
        labels: np.ndarray,
        identities: list[tuple[str, str]],
        roles: list[str],
        urgencies: np.ndarray,
        seen_increment: int,
    ) -> None:
        if len(labels) != len(identities) or len(labels) != len(roles) or len(labels) != len(urgencies):
            raise ValueError("角色记忆候选长度不一致")
        unique: dict[str, int] = {}
        for index, pair in enumerate(identities):
            unique.setdefault(pair[0], index)
        indices_by_role: dict[str, list[int]] = {role: [] for role in ROLE_ORDER}
        for index, pair in enumerate(identities):
            if unique[pair[0]] != index:
                continue
            indices_by_role[roles[index]].append(index)
        for role in ROLE_ORDER:
            indices_by_role[role].sort(key=lambda idx: (-float(urgencies[idx]), identities[idx][0]))
        selected: list[int] = []
        positions = {role: 0 for role in ROLE_ORDER}
        while len(selected) < self.capacity:
            added = False
            for role in ROLE_ORDER:
                position = positions[role]
                candidates = indices_by_role[role]
                if position < len(candidates):
                    selected.append(candidates[position])
                    positions[role] = position + 1
                    added = True
                    if len(selected) >= self.capacity:
                        break
            if not added:
                break
        self.values = values[selected].copy() if selected else np.empty((0, self.input_dim), dtype=np.uint8)
        self.labels = labels[selected].copy() if selected else np.empty((0,), dtype=np.int64)
        self.identities = [identities[index] for index in selected]
        self.roles = [roles[index] for index in selected]
        self.urgencies = urgencies[selected].astype(np.float32, copy=True) if selected else np.empty((0,), dtype=np.float32)
        self.seen += int(seen_increment)

    def update_after_year(self, model: nn.Module, current_values: np.ndarray, current_labels: np.ndarray, current_hashes: np.ndarray, year: int, device: torch.device) -> int:
        model.eval()
        with torch.inference_mode():
            current_scores = model(torch.from_numpy(current_values).to(device=device, dtype=torch.float32)).cpu().numpy()
            if len(self.labels):
                memory_scores = model(torch.from_numpy(self.values).to(device=device, dtype=torch.float32)).cpu().numpy()
            else:
                memory_scores = np.empty((0,), dtype=np.float32)
        candidate_values = np.concatenate((self.values, current_values), axis=0)
        candidate_labels = np.concatenate((self.labels, current_labels), axis=0)
        candidate_ids = list(self.identities) + [base.identity_pair(year, source_hash, row, int(label)) for row, label, source_hash in zip(current_values, current_labels, current_hashes, strict=True)]
        candidate_scores = np.concatenate((memory_scores, current_scores), axis=0)
        role_pairs = [self.role_for(int(label), float(score)) for label, score in zip(candidate_labels, candidate_scores, strict=True)]
        candidate_roles = [pair[0] for pair in role_pairs]
        candidate_urgencies = np.asarray([pair[1] for pair in role_pairs], dtype=np.float32)
        self.replace_from_candidates(candidate_values, candidate_labels, candidate_ids, candidate_roles, candidate_urgencies, len(current_labels))
        return int(sum(role == "repair" for role in candidate_roles[-len(current_labels) :])) if len(current_labels) else 0


def role_memory_protect_values(memory: RoleMemory) -> np.ndarray:
    if not len(memory.labels):
        return np.empty((0, memory.input_dim), dtype=np.uint8)
    mask = np.asarray([role == "protect" and int(label) == 1 for role, label in zip(memory.roles, memory.labels, strict=True)])
    return memory.values[mask]


def reservoir_protect_values(model: nn.Module, memory: base.Reservoir | None, device: torch.device) -> np.ndarray:
    if memory is None or not len(memory.labels):
        return np.empty((0, 0), dtype=np.uint8)
    model.eval()
    with torch.inference_mode():
        scores = model(torch.from_numpy(memory.values).to(device=device, dtype=torch.float32)).cpu().numpy()
    return memory.values[(memory.labels == 1) & (scores >= THRESHOLD)]


def teacher_scores(model: nn.Module, values: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    chunks: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, len(values), base.SCANNER_BATCH_SIZE):
            batch = torch.from_numpy(values[start : start + base.SCANNER_BATCH_SIZE]).to(device=device, dtype=torch.float32)
            chunks.append(model(batch).cpu().numpy())
    return np.concatenate(chunks) if chunks else np.empty((0,), dtype=np.float32)


def train_epoch(model: nn.Module, optimizer: torch.optim.Optimizer, criterion: nn.Module, values: np.ndarray, labels: np.ndarray, repair_mask: np.ndarray, benign_mask: np.ndarray, replay_values: np.ndarray | None, replay_labels: np.ndarray | None, protect_values: np.ndarray, device: torch.device, batch_size: int, shuffle_seed: int, use_risk_repair: bool, risk_config: dict[str, Any]) -> tuple[float, int, dict[str, float]]:
    model.train()
    current_values = values
    current_labels = labels
    current_repair = repair_mask
    current_benign = benign_mask
    if replay_values is not None and replay_labels is not None and len(replay_labels):
        current_values = np.concatenate((current_values, replay_values), axis=0)
        current_labels = np.concatenate((current_labels, replay_labels), axis=0)
        current_repair = np.concatenate((current_repair, np.zeros(len(replay_labels), dtype=bool)))
        current_benign = np.concatenate((current_benign, np.zeros(len(replay_labels), dtype=bool)))
    order = np.random.default_rng(shuffle_seed).permutation(len(current_labels))
    current_values, current_labels = current_values[order], current_labels[order]
    current_repair, current_benign = current_repair[order], current_benign[order]
    total_loss = total_samples = 0.0
    repair_loss_total = benign_loss_total = protect_loss_total = 0.0
    protect_tensor = torch.from_numpy(protect_values).to(device=device, dtype=torch.float32) if len(protect_values) else None
    ones = None
    zeros = None
    for start in range(0, len(current_labels), batch_size):
        batch_values = current_values[start : start + batch_size]
        batch_labels = current_labels[start : start + batch_size]
        batch_repair = current_repair[start : start + batch_size]
        batch_benign = current_benign[start : start + batch_size]
        inputs = torch.from_numpy(batch_values).to(device=device, dtype=torch.float32)
        targets = torch.from_numpy(batch_labels.astype(np.float32, copy=False)).to(device=device)
        optimizer.zero_grad(set_to_none=True)
        probabilities = model(inputs)
        loss = criterion(probabilities, targets)
        repair_loss = torch.zeros((), device=device)
        benign_loss = torch.zeros((), device=device)
        protect_loss = torch.zeros((), device=device)
        if use_risk_repair and np.any(batch_repair):
            repair_probabilities = model(inputs[torch.from_numpy(batch_repair).to(device=device)])
            ones = torch.ones_like(repair_probabilities)
            repair_loss = criterion(repair_probabilities, ones)
            loss = loss + float(risk_config["lambda_repair"]) * repair_loss
        if use_risk_repair and np.any(batch_benign):
            benign_probabilities = model(inputs[torch.from_numpy(batch_benign).to(device=device)])
            zeros = torch.zeros_like(benign_probabilities)
            benign_loss = criterion(benign_probabilities, zeros)
            loss = loss + float(risk_config["lambda_fp_control"]) * benign_loss
        if use_risk_repair and protect_tensor is not None:
            protect_probabilities = model(protect_tensor)
            protect_loss = torch.relu(torch.as_tensor(THRESHOLD, device=device) - protect_probabilities).mean()
            loss = loss + float(risk_config["lambda_protect"]) * protect_loss
        loss.backward()
        optimizer.step()
        count = len(batch_labels)
        total_loss += float(loss.item()) * count
        repair_loss_total += float(repair_loss.item()) * count
        benign_loss_total += float(benign_loss.item()) * count
        protect_loss_total += float(protect_loss.item()) * count
        total_samples += count
    if total_samples == 0:
        raise RuntimeError("训练批次为空")
    return total_loss / total_samples, int(total_samples), {"repair": repair_loss_total / total_samples, "fp_control": benign_loss_total / total_samples, "protect": protect_loss_total / total_samples}


def checkpoint_payload(model: nn.Module, optimizer: torch.optim.Optimizer, replay_memory: base.Reservoir | None, role_memory: RoleMemory | None, year_index: int, next_epoch: int, yearly: dict[str, Any], old_positive: dict[str, bool], active_context: dict[str, Any] | None) -> dict[str, Any]:
    return {"schema_version": "ch3-lamda-mo-source-dev-checkpoint-v1", "model": model.state_dict(), "optimizer": optimizer.state_dict(), "replay_memory": None if replay_memory is None else replay_memory.state_dict(), "role_memory": None if role_memory is None else role_memory.state_dict(), "year_index": year_index, "next_epoch": next_epoch, "yearly": yearly, "old_positive": old_positive, "active_context": active_context, "rng": base.rng_state(), "saved_at": base.now_utc()}


def execute_arm(arm: str, config: dict[str, Any], features: list[str], files: dict[int, dict[str, Path]], output_root: Path, device: torch.device, resume: bool, started_at: str) -> dict[str, Any]:
    checkpoint_path = output_root / "checkpoints" / arm / "latest.pt"
    seed = int(config["training"]["seed"])
    risk_enabled = arm in {"risk_repair_update", "role_conditioned_memory_risk_repair"}
    role_enabled = arm in {"role_conditioned_memory", "role_conditioned_memory_risk_repair"}
    if resume and checkpoint_path.is_file():
        saved = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model = base.LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device)
        model.load_state_dict(saved["model"])
        optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"]))
        optimizer.load_state_dict(saved["optimizer"])
        replay_memory = None if saved["replay_memory"] is None else base.Reservoir.from_state(saved["replay_memory"])
        role_memory = None if saved["role_memory"] is None else RoleMemory.from_state(saved["role_memory"])
        year_index, next_epoch = int(saved["year_index"]), int(saved["next_epoch"])
        yearly, old_positive, active_context = dict(saved["yearly"]), dict(saved["old_positive"]), saved.get("active_context")
        base.restore_rng(saved["rng"])
    else:
        base.seed_everything(seed)
        model = base.LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device)
        optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"]))
        replay_memory = base.Reservoir(int(config["replay"]["capacity"]), len(features), seed) if not role_enabled else None
        role_memory = RoleMemory(int(config["mechanism"]["capacity"]), len(features), seed + 1) if role_enabled else None
        year_index, next_epoch, yearly, old_positive, active_context = 0, 1, {}, {}, None
    criterion = nn.BCELoss()
    epochs = int(config["training"]["epochs_per_year"])
    batch_size = int(config["training"]["batch_size"])
    for index in range(year_index, len(RUN_YEARS)):
        year = RUN_YEARS[index]
        values, labels, hashes = load_train(files[year]["train"], features)
        if index == year_index and next_epoch > 1 and active_context is not None:
            teacher_scores_array = np.asarray(active_context["teacher_scores"], dtype=np.float32)
            repair_mask = np.asarray(active_context["repair_mask"], dtype=bool)
            benign_mask = np.asarray(active_context["benign_mask"], dtype=bool)
        else:
            teacher_scores_array = teacher_scores(model, values, device) if index > 0 else np.full(len(labels), np.nan, dtype=np.float32)
            repair_mask = (labels == 1) & np.isfinite(teacher_scores_array) & (teacher_scores_array < THRESHOLD)
            benign_mask = (labels == 0) & np.isfinite(teacher_scores_array) & (teacher_scores_array >= THRESHOLD)
            active_context = {"year": year, "teacher_scores": teacher_scores_array, "repair_mask": repair_mask, "benign_mask": benign_mask}
        if role_enabled:
            protect_values = role_memory_protect_values(role_memory)
            replay_values = role_memory.values if role_memory is not None and len(role_memory.labels) else None
            replay_labels = role_memory.labels if role_memory is not None and len(role_memory.labels) else None
        else:
            protect_values = reservoir_protect_values(model, replay_memory, device)
            replay_values = replay_memory.values if replay_memory is not None and len(replay_memory.labels) else None
            replay_labels = replay_memory.labels if replay_memory is not None and len(replay_memory.labels) else None
        epoch_start = next_epoch if index == year_index else 1
        for epoch in range(epoch_start, epochs + 1):
            loss, samples, auxiliary = train_epoch(model, optimizer, criterion, values, labels, repair_mask, benign_mask, replay_values, replay_labels, protect_values, device, batch_size, seed + index * epochs + epoch, risk_enabled, config["risk_repair"])
            yearly.setdefault(str(year), {"epochs": []})["epochs"].append({"epoch": epoch, "loss": loss, "samples": samples, "auxiliary": auxiliary, "repair_candidates": int(np.sum(repair_mask)), "fp_control_candidates": int(np.sum(benign_mask)), "protect_candidates": int(len(protect_values)), "completed_at": base.now_utc()})
            snapshot = checkpoint_payload(model, optimizer, replay_memory, role_memory, index, epoch + 1, yearly, old_positive, active_context)
            base.atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / f"epoch-{epoch:02d}.pt", snapshot)
            base.atomic_torch(checkpoint_path, snapshot)
            base.write_status(output_root, "running", f"{arm} {year} 第 {epoch}/{epochs} 轮完成", started_at, {"arm": arm, "year": year, "epoch": epoch})
        surfaces: dict[str, Any] = {}
        surfaces["current_year"], current = base.evaluate_surface(model, arm, year, "current_year", [year], files, features, output_root, device, THRESHOLD, old_positive)
        next_years = [RUN_YEARS[index + 1]] if index + 1 < len(RUN_YEARS) else []
        surfaces["next_year"] = {"not_applicable": True} if not next_years else base.evaluate_surface(model, arm, year, "next_year", next_years, files, features, output_root, device, THRESHOLD, old_positive)[0]
        backward_years = RUN_YEARS[:index]
        surfaces["backward"], backward = ({"not_applicable": True}, {}) if not backward_years else base.evaluate_surface(model, arm, year, "backward", backward_years, files, features, output_root, device, THRESHOLD, old_positive)
        yearly[str(year)]["evaluation"] = surfaces
        old_positive.update(current)
        old_positive.update(backward)
        if role_enabled:
            repair_count = role_memory.update_after_year(model, values, labels, hashes, year, device)
            yearly[str(year)]["role_memory"] = {"capacity": role_memory.capacity, "size": int(len(role_memory.labels)), "seen_training_samples": role_memory.seen, "role_counts": {role: int(sum(1 for value in role_memory.roles if value == role)) for role in ROLE_ORDER}, "repair_candidates_selected": repair_count, "updated_after_training_and_evaluation": True}
        elif replay_memory is not None:
            for chunk_values, chunk_labels, chunk_hashes, _ in base.iter_parquet(files[year]["train"], features):
                replay_memory.update(chunk_values, chunk_labels, [base.identity_pair(year, source_hash, row, int(label)) for row, label, source_hash in zip(chunk_values, chunk_labels, chunk_hashes, strict=True)])
            yearly[str(year)]["replay_memory"] = {"capacity": replay_memory.capacity, "size": int(len(replay_memory.labels)), "seen_training_samples": replay_memory.seen, "updated_after_training_and_evaluation": True}
        active_context = None
        snapshot = checkpoint_payload(model, optimizer, replay_memory, role_memory, index + 1, 1, yearly, old_positive, active_context)
        base.atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / "year-complete.pt", snapshot)
        base.atomic_torch(checkpoint_path, snapshot)
        base.atomic_json(output_root / "metrics" / arm / f"year-{year}.json", {"arm": arm, "trained_through_year": year, "evaluation": surfaces, "epochs": yearly[str(year)]["epochs"], "replay_memory": yearly[str(year)].get("replay_memory"), "role_memory": yearly[str(year)].get("role_memory")})
        next_epoch = 1
    return yearly


def aggregate_development(output_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"development_years": DEVELOPMENT_YEARS, "arms": {}, "screening_only": True, "independent_final_test": False}
    for arm in ARMS:
        rows: list[dict[str, Any]] = []
        for year in DEVELOPMENT_YEARS:
            path = output_root / "predictions" / arm / f"trained-through-{year}" / "current_year.jsonl"
            with path.open(encoding="utf-8") as handle:
                rows.extend(json.loads(line) for line in handle)
        identities = [row["sample_identity_sha256"] for row in rows]
        if len(identities) != len(set(identities)):
            raise ValueError(f"{arm} 开发期汇总存在重复样本身份")
        labels = np.asarray([row["label"] for row in rows], dtype=np.int64)
        scores = np.asarray([row["score"] for row in rows], dtype=np.float64)
        result["arms"][arm] = {"current_year_metrics": base.metrics(labels, scores, THRESHOLD), "prediction_count": len(rows), "prediction_sha256": base.hashlib.sha256("".join(identities).encode("ascii")).hexdigest()}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="LAMDA 来源／开发期决策角色记忆与双侧风险修复筛查")
    parser.add_argument("--config", type=Path, required=True, help="冻结 JSON 配置")
    parser.add_argument("--run", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--resume", action="store_true", help="从同一身份最新断点恢复")
    parser.add_argument("--validate-config", action="store_true", help="只校验配置")
    args = parser.parse_args()
    config = load_config(args.config.resolve())
    if args.validate_config:
        print(json.dumps({"valid": True, "run_id": config["identity"]["run_id"], "run_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "screening_only": True}, ensure_ascii=False))
        return 0
    base_root = Path(config["paths"]["output_root"])
    data_root = Path(config["paths"]["data_root"])
    base.prepare_output(base_root, config, args.config.resolve(), args.resume)
    started_at = base.now_utc()
    started = time.monotonic()
    base.write_status(base_root, "running", "开始 LAMDA 来源／开发期 M/O 筛查", started_at)
    try:
        features, files, manifest = verify_input(data_root, config)
        base.atomic_json(base_root / "input-manifest.json", {"input_manifest_path": str(data_root / "manifest.json"), "input_manifest_sha256": base.sha256_file(data_root / "manifest.json"), "manifest": manifest, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "published_feature_space_uses_future_covariates": True, "screening_only": True})
        device = base.choose_device()
        torch.set_float32_matmul_precision(config["training"]["float32_matmul_precision"])
        base.atomic_json(base_root / "runtime-receipt.json", {"device": str(device), "torch": torch.__version__, "numpy": np.__version__, "platform": platform.platform(), "float32_matmul_precision": config["training"]["float32_matmul_precision"], "torch_compile": False, "screening_only": True, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "started_at": started_at})
        for arm in ARMS:
            execute_arm(arm, config, features, files, base_root, device, args.resume, started_at)
        summary = aggregate_development(base_root, config)
        base.atomic_json(base_root / "development-summary.json", summary)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        base.atomic_json(base_root / "resource-receipt.json", {"device": str(device), "wall_seconds": time.monotonic() - started, "max_rss": usage.ru_maxrss, "max_rss_unit": "platform_dependent", "cuda_max_memory_allocated": int(torch.cuda.max_memory_allocated()) if device.type == "cuda" else None, "cuda_max_memory_reserved": int(torch.cuda.max_memory_reserved()) if device.type == "cuda" else None})
        base.atomic_json(base_root / "run-manifest.json", {"tool_sha256": base.sha256_file(Path(__file__).resolve()), "config_sha256": base.sha256_file(args.config.resolve()), "arms": ARMS, "enumerated_years": RUN_YEARS, "sealed_final_years_not_read": SEALED_FINAL_YEARS, "screening_only": True})
        base.write_status(base_root, "completed", "LAMDA 来源／开发期 M/O 筛查完成", started_at)
        return 0
    except Exception as error:
        base.write_status(base_root, "failed", f"{type(error).__name__}: {error}", started_at)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
