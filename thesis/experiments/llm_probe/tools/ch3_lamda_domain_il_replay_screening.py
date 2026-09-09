#!/usr/bin/env python3
"""LAMDA Domain-IL 标准经验回放资格筛查。

发布 4561 维特征空间使用未来协变量；本工具只产生 screening_only 制品，不能作为
无泄漏正式基线或独立最终测试。Naive 与 Replay 使用同一初始化，Replay 仅在年度
训练和评价结束后，以总容量 200 的单样本水库接收该年度训练样本。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import resource
import shutil
import sys
import time
try:
    from datetime import UTC, datetime
except ImportError:
    from datetime import datetime, timezone

    UTC = timezone.utc
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pyarrow.dataset as ds
import sklearn
import torch
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, roc_auc_score
from torch import nn


OFFICIAL_REPOSITORY = "IQSeC-Lab/LAMDA"
OFFICIAL_REVISION = "ad9614bdd5556767f97ced2fce797c2f06408ebf"
METADATA_COLUMNS = ("hash", "label", "family", "vt_count", "year_month")
SCANNER_BATCH_SIZE = 2048


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def atomic_torch(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    torch.save(payload, temporary)
    os.replace(temporary, path)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def rng_state() -> dict[str, Any]:
    state: dict[str, Any] = {"python": random.getstate(), "numpy": np.random.get_state(), "torch": torch.get_rng_state()}
    if torch.cuda.is_available():
        state["cuda"] = torch.cuda.get_rng_state_all()
    return state


def restore_rng(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])
    if "cuda" in state and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(state["cuda"])


def load_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"identity", "paths", "data", "arms", "model", "training", "replay", "evaluation", "qualification_gate"}
    missing = required - set(payload)
    if missing:
        raise ValueError(f"冻结配置缺少字段：{sorted(missing)}")
    if payload["identity"].get("run_tier") != "screening_only":
        raise ValueError("仅允许 screening_only 运行身份")
    if payload["identity"].get("published_feature_space_uses_future_covariates") is not True:
        raise ValueError("必须披露 published_feature_space_uses_future_covariates=true")
    if payload["data"].get("protocol") != "Domain-IL":
        raise ValueError("持续学习协议必须是 Domain-IL")
    if payload["arms"] != ["naive", "replay"]:
        raise ValueError("比较臂必须恰为 naive/replay")
    if payload["data"].get("year_order") != [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]:
        raise ValueError("年份顺序不符合研究卡")
    if payload["data"].get("published_feature_count") != 4561:
        raise ValueError("发布特征数必须为 4561")
    if payload["training"].get("seed") != 42 or payload["training"].get("epochs_per_year") != 10:
        raise ValueError("种子或年度轮数不符合冻结合同")
    if payload["training"].get("batch_size") != 1024:
        raise ValueError("批量大小必须为冻结的 1024")
    if payload["replay"].get("capacity") != 200:
        raise ValueError("Replay 总容量必须为 200")
    if payload["model"].get("backbone") != [512, 384, 256, 128] or payload["model"].get("head") != [100, 100, 1]:
        raise ValueError("模型宽度不符合冻结合同")
    return payload


def verify_input(data_root: Path, config: dict[str, Any]) -> tuple[list[str], dict[int, dict[str, Path]], dict[str, Any]]:
    manifest_path = data_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source", {}).get("repo_id") != OFFICIAL_REPOSITORY or manifest.get("source", {}).get("revision") != OFFICIAL_REVISION:
        raise ValueError("输入 manifest 的 LAMDA 发布身份不匹配")
    if manifest.get("content", {}).get("columns") != [4566] or manifest.get("content", {}).get("rows") != 1008381:
        raise ValueError("输入 manifest 的发布模式不匹配")
    mapping_path = data_root / "Baseline/feature_mapping.csv"
    mapping_lines = mapping_path.read_text(encoding="utf-8").splitlines()
    if not mapping_lines or "mapped_name" not in mapping_lines[0]:
        raise ValueError("特征映射缺少 mapped_name")
    import csv
    features = [row["mapped_name"] for row in csv.DictReader(mapping_lines)]
    if len(features) != config["data"]["published_feature_count"] or len(features) != len(set(features)):
        raise ValueError("发布特征映射与冻结维度不一致")
    files: dict[int, dict[str, Path]] = {}
    for year in config["data"]["year_order"]:
        year_root = data_root / "Baseline" / str(year)
        train, test = year_root / f"{year}_train.parquet", year_root / f"{year}_test.parquet"
        if not train.is_file() or not test.is_file():
            raise FileNotFoundError(f"年份 {year} 的 train/test Parquet 不完整")
        files[year] = {"train": train, "test": test}
    return features, files, manifest


class LamdaDomainILMLP(nn.Module):
    def __init__(self, input_dim: int, dropout: float) -> None:
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, 512), nn.ReLU(), nn.Linear(512, 384), nn.ReLU(),
            nn.Linear(384, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU(),
        )
        self.head = nn.Sequential(
            nn.Linear(128, 100), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(100, 100), nn.ReLU(), nn.Dropout(dropout), nn.Linear(100, 1), nn.Sigmoid(),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return self.head(self.backbone(values)).squeeze(1)


def choose_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def identity_pair(year: int, source_hash: Any, values: np.ndarray, label: int) -> tuple[str, str]:
    source = str(source_hash).encode("utf-8", errors="replace")
    sample_identity = hashlib.sha256(str(year).encode("ascii") + b"\0" + source).hexdigest()
    feature_label = hashlib.sha256(np.ascontiguousarray(values, dtype=np.uint8).tobytes() + bytes([int(label)])).hexdigest()
    return sample_identity, feature_label


def iter_parquet(path: Path, features: list[str]) -> Iterator[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    columns = [*features, *METADATA_COLUMNS]
    scanner = ds.dataset(path, format="parquet").scanner(columns=columns, batch_size=SCANNER_BATCH_SIZE)
    for batch in scanner.to_batches():
        frame = batch.to_pandas(split_blocks=True)
        values = frame.loc[:, features].to_numpy(dtype=np.uint8, copy=True)
        labels = frame["label"].to_numpy(dtype=np.int64, copy=True)
        hashes = frame["hash"].astype(str).to_numpy()
        months = frame["year_month"].astype(str).to_numpy()
        yield values, labels, hashes, months


def iter_fixed_batches(values: np.ndarray, labels: np.ndarray, batch_size: int) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    for start in range(0, len(labels), batch_size):
        yield values[start : start + batch_size], labels[start : start + batch_size]


class Reservoir:
    def __init__(self, capacity: int, input_dim: int, seed: int) -> None:
        self.capacity, self.input_dim, self.seen = capacity, input_dim, 0
        self.values = np.empty((0, input_dim), dtype=np.uint8)
        self.labels = np.empty((0,), dtype=np.int64)
        self.identities: list[tuple[str, str]] = []
        self.rng = np.random.default_rng(seed)

    def state_dict(self) -> dict[str, Any]:
        return {"capacity": self.capacity, "input_dim": self.input_dim, "seen": self.seen, "values": self.values, "labels": self.labels, "identities": self.identities, "rng_state": self.rng.bit_generator.state}

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "Reservoir":
        result = cls(int(state["capacity"]), int(state["input_dim"]), 0)
        result.seen, result.values, result.labels = int(state["seen"]), state["values"], state["labels"]
        result.identities = list(state["identities"])
        result.rng.bit_generator.state = state["rng_state"]
        return result

    def update(self, values: np.ndarray, labels: np.ndarray, identities: list[tuple[str, str]]) -> None:
        for row, label, pair in zip(values, labels, identities, strict=True):
            self.seen += 1
            if len(self.labels) < self.capacity:
                self.values = np.vstack((self.values, row[np.newaxis, :]))
                self.labels = np.append(self.labels, label)
                self.identities.append(pair)
                continue
            slot = int(self.rng.integers(0, self.seen))
            if slot < self.capacity:
                self.values[slot] = row
                self.labels[slot] = label
                self.identities[slot] = pair


def train_epoch(model: nn.Module, optimizer: torch.optim.Optimizer, criterion: nn.Module, train_path: Path, features: list[str], reservoir: Reservoir | None, device: torch.device, batch_size: int, shuffle_seed: int) -> tuple[float, int]:
    model.train()
    total_loss, total_samples = 0.0, 0
    def consume(values: np.ndarray, labels: np.ndarray) -> None:
        nonlocal total_loss, total_samples
        for batch_values, batch_labels in iter_fixed_batches(values, labels, batch_size):
            inputs = torch.from_numpy(batch_values).to(device=device, dtype=torch.float32)
            targets = torch.from_numpy(batch_labels.astype(np.float32, copy=False)).to(device=device)
            optimizer.zero_grad(set_to_none=True)
            probabilities = model(inputs)
            loss = criterion(probabilities, targets)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(batch_labels)
            total_samples += len(batch_labels)
    current_values: list[np.ndarray] = []
    current_labels: list[np.ndarray] = []
    for values, labels, _, _ in iter_parquet(train_path, features):
        current_values.append(values)
        current_labels.append(labels)
    if not current_labels:
        raise RuntimeError("年度训练未读取到任何样本")
    values = np.concatenate(current_values, axis=0)
    labels = np.concatenate(current_labels, axis=0)
    if reservoir is not None and len(reservoir.labels):
        values = np.concatenate((values, reservoir.values), axis=0)
        labels = np.concatenate((labels, reservoir.labels), axis=0)
    order = np.random.default_rng(shuffle_seed).permutation(len(labels))
    consume(values[order], labels[order])
    if not total_samples:
        raise RuntimeError("年度训练未读取到任何样本")
    return total_loss / total_samples, total_samples


def metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float | int | None]:
    predicted = scores >= threshold
    tp = int(np.sum((predicted == 1) & (labels == 1)))
    fp = int(np.sum((predicted == 1) & (labels == 0)))
    tn = int(np.sum((predicted == 0) & (labels == 0)))
    fn = int(np.sum((predicted == 0) & (labels == 1)))
    binary = len(np.unique(labels)) == 2
    return {"n": int(len(labels)), "AP": float(average_precision_score(labels, scores)) if binary else None, "AUROC": float(roc_auc_score(labels, scores)) if binary else None, "F1": float(f1_score(labels, predicted, zero_division=0)), "FPR": float(fp / (fp + tn)) if fp + tn else None, "FNR": float(fn / (fn + tp)) if fn + tp else None, "Brier": float(brier_score_loss(labels, scores)), "threshold": threshold}


def evaluate_surface(model: nn.Module, arm: str, trained_year: int, surface: str, years: list[int], files: dict[int, dict[str, Path]], features: list[str], output_root: Path, device: torch.device, threshold: float, old_positive: dict[str, bool]) -> tuple[dict[str, Any], dict[str, bool]]:
    records: list[dict[str, Any]] = []
    model.eval()
    with torch.inference_mode():
        for year in years:
            for values, labels, hashes, _ in iter_parquet(files[year]["test"], features):
                scores = model(torch.from_numpy(values).to(device=device, dtype=torch.float32)).cpu().numpy()
                for row, label, source_hash, score in zip(values, labels, hashes, scores, strict=True):
                    sample_identity, feature_label = identity_pair(year, source_hash, row, int(label))
                    prediction = bool(float(score) >= threshold)
                    records.append({"arm": arm, "trained_through_year": trained_year, "evaluation_surface": surface, "evaluation_year": year, "sample_identity_sha256": sample_identity, "feature_label_sha256": feature_label, "label": int(label), "score": float(score), "predicted_malicious": prediction})
    prediction_root = output_root / "predictions" / arm / f"trained-through-{trained_year}"
    prediction_root.mkdir(parents=True, exist_ok=True)
    prediction_path = prediction_root / f"{surface}.jsonl"
    temporary = prediction_path.with_name(f".{prediction_path.name}.{os.getpid()}.partial")
    with temporary.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, prediction_path)
    labels = np.asarray([record["label"] for record in records], dtype=np.int64)
    scores = np.asarray([record["score"] for record in records], dtype=np.float64)
    flipped = [record for record in records if record["label"] == 1 and old_positive.get(record["sample_identity_sha256"]) is True and not record["predicted_malicious"]]
    eligible = [record for record in records if record["label"] == 1 and old_positive.get(record["sample_identity_sha256"]) is True]
    return {"years": years, "metrics": metrics(labels, scores, threshold), "old_malicious_negative_flip": {"eligible_n": len(eligible), "negative_flip_n": len(flipped), "rate": float(len(flipped) / len(eligible)) if eligible else None}, "prediction_path": str(prediction_path), "prediction_sha256": sha256_file(prediction_path)}, {record["sample_identity_sha256"]: bool(record["predicted_malicious"]) for record in records if record["label"] == 1}


def checkpoint_payload(model: nn.Module, optimizer: torch.optim.Optimizer, reservoir: Reservoir | None, year_index: int, next_epoch: int, yearly: dict[str, Any], old_positive: dict[str, bool]) -> dict[str, Any]:
    return {"schema_version": "ch3-lamda-domain-il-replay-checkpoint-v1", "model": model.state_dict(), "optimizer": optimizer.state_dict(), "reservoir": None if reservoir is None else reservoir.state_dict(), "year_index": year_index, "next_epoch": next_epoch, "yearly": yearly, "old_positive": old_positive, "rng": rng_state(), "saved_at": now_utc()}


def write_status(output_root: Path, state: str, detail: str, started_at: str, extra: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {"schema_version": "ch3-lamda-domain-il-replay-status-v1", "state": state, "detail": detail, "started_at": started_at, "updated_at": now_utc(), "screening_only": True, "published_feature_space_uses_future_covariates": True}
    if extra:
        payload.update(extra)
    atomic_json(output_root / "status.json", payload)


def prepare_output(output_root: Path, config: dict[str, Any], config_path: Path, resume: bool) -> None:
    if output_root.exists() and not resume:
        raise FileExistsError("输出目录已存在；只允许用 --resume 恢复同一运行身份")
    output_root.mkdir(parents=True, exist_ok=True)
    frozen = output_root / "effective-config.json"
    if frozen.is_file() and json.loads(frozen.read_text(encoding="utf-8")) != config:
        raise ValueError("同一输出身份的冻结配置不一致")
    if not frozen.is_file():
        shutil.copyfile(config_path, frozen)


def execute_arm(arm: str, config: dict[str, Any], features: list[str], files: dict[int, dict[str, Path]], output_root: Path, device: torch.device, resume: bool, started_at: str) -> dict[str, Any]:
    checkpoint_path = output_root / "checkpoints" / arm / "latest.pt"
    seed = int(config["training"]["seed"])
    if resume and checkpoint_path.is_file():
        saved = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model = LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device)
        model.load_state_dict(saved["model"])
        optimizer = torch.optim.SGD(model.parameters(), **config["training"]["optimizer"] | {"lr": float(config["training"]["optimizer"]["lr"])})
        optimizer.load_state_dict(saved["optimizer"])
        reservoir = Reservoir.from_state(saved["reservoir"]) if saved["reservoir"] is not None else None
        year_index, next_epoch, yearly, old_positive = int(saved["year_index"]), int(saved["next_epoch"]), dict(saved["yearly"]), dict(saved["old_positive"])
        restore_rng(saved["rng"])
    else:
        seed_everything(seed)
        model = LamdaDomainILMLP(len(features), float(config["model"]["head_dropout"])).to(device)
        optimizer = torch.optim.SGD(model.parameters(), lr=float(config["training"]["optimizer"]["lr"]), momentum=float(config["training"]["optimizer"]["momentum"]), weight_decay=float(config["training"]["optimizer"]["weight_decay"]))
        reservoir = Reservoir(int(config["replay"]["capacity"]), len(features), seed) if arm == "replay" else None
        year_index, next_epoch, yearly, old_positive = 0, 1, {}, {}
    criterion = nn.BCELoss()
    years = list(config["data"]["year_order"])
    batch_size, epochs, threshold = int(config["training"]["batch_size"]), int(config["training"]["epochs_per_year"]), float(config["evaluation"]["threshold"])
    for index in range(year_index, len(years)):
        year = years[index]
        epoch_start = next_epoch if index == year_index else 1
        for epoch in range(epoch_start, epochs + 1):
            shuffle_seed = seed + index * epochs + epoch
            loss, samples = train_epoch(model, optimizer, criterion, files[year]["train"], features, reservoir, device, batch_size, shuffle_seed)
            yearly.setdefault(str(year), {"epochs": []})["epochs"].append({"epoch": epoch, "loss": loss, "samples": samples, "shuffle_seed": shuffle_seed, "completed_at": now_utc()})
            snapshot = checkpoint_payload(model, optimizer, reservoir, index, epoch + 1, yearly, old_positive)
            atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / f"epoch-{epoch:02d}.pt", snapshot)
            atomic_torch(checkpoint_path, snapshot)
            write_status(output_root, "running", f"{arm} {year} 第 {epoch}/{epochs} 轮完成", started_at, {"arm": arm, "year": year, "epoch": epoch})
        surfaces: dict[str, Any] = {}
        surfaces["current_year"], current = evaluate_surface(model, arm, year, "current_year", [year], files, features, output_root, device, threshold, old_positive)
        next_years = [years[index + 1]] if index + 1 < len(years) else []
        surfaces["next_year"] = {"not_applicable": True} if not next_years else evaluate_surface(model, arm, year, "next_year", next_years, files, features, output_root, device, threshold, old_positive)[0]
        backward_years = years[:index]
        surfaces["backward"], backward = ( {"not_applicable": True}, {} ) if not backward_years else evaluate_surface(model, arm, year, "backward", backward_years, files, features, output_root, device, threshold, old_positive)
        yearly[str(year)]["evaluation"] = surfaces
        old_positive.update(current)
        old_positive.update(backward)
        if reservoir is not None:
            for values, labels, hashes, _ in iter_parquet(files[year]["train"], features):
                reservoir.update(values, labels, [identity_pair(year, source_hash, row, int(label)) for row, label, source_hash in zip(values, labels, hashes, strict=True)])
            yearly[str(year)]["reservoir"] = {"capacity": reservoir.capacity, "size": int(len(reservoir.labels)), "seen_training_samples": reservoir.seen, "updated_after_training_and_evaluation": True}
        snapshot = checkpoint_payload(model, optimizer, reservoir, index + 1, 1, yearly, old_positive)
        atomic_torch(output_root / "checkpoints" / arm / f"year-{year}" / "year-complete.pt", snapshot)
        atomic_torch(checkpoint_path, snapshot)
        atomic_json(output_root / "metrics" / arm / f"year-{year}.json", {"arm": arm, "trained_through_year": year, "evaluation": surfaces, "epochs": yearly[str(year)]["epochs"], "reservoir": yearly[str(year)].get("reservoir")})
        next_epoch = 1
    return yearly


def aggregate_qualification(output_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    years = config["evaluation"]["qualification_current_years"]
    aggregate: dict[str, Any] = {"qualification_years": years, "arms": {}}
    for arm in config["arms"]:
        rows: list[dict[str, Any]] = []
        for year in years:
            path = output_root / "predictions" / arm / f"trained-through-{year}" / "current_year.jsonl"
            with path.open(encoding="utf-8") as handle:
                rows.extend(json.loads(line) for line in handle)
        identities = [row["sample_identity_sha256"] for row in rows]
        if len(identities) != len(set(identities)):
            raise ValueError(f"{arm} 资格汇总存在重复样本身份")
        labels = np.asarray([row["label"] for row in rows], dtype=np.int64)
        scores = np.asarray([row["score"] for row in rows], dtype=np.float64)
        aggregate["arms"][arm] = {"current_year_metrics": metrics(labels, scores, float(config["evaluation"]["threshold"])), "prediction_count": len(rows), "prediction_sha256": hashlib.sha256("".join(identities).encode("ascii")).hexdigest()}
    naive, replay = aggregate["arms"]["naive"]["current_year_metrics"], aggregate["arms"]["replay"]["current_year_metrics"]
    fpr_ok = replay["FPR"] is not None and naive["FPR"] is not None and replay["FPR"] <= naive["FPR"]
    flip_totals: dict[str, dict[str, int]] = {}
    for arm in config["arms"]:
        eligible_n = negative_flip_n = 0
        for year in years:
            yearly_path = output_root / "metrics" / arm / f"year-{year}.json"
            yearly = json.loads(yearly_path.read_text(encoding="utf-8"))
            backward = yearly["evaluation"].get("backward", {})
            flip = backward.get("old_malicious_negative_flip", {})
            eligible_n += int(flip.get("eligible_n", 0))
            negative_flip_n += int(flip.get("negative_flip_n", 0))
        flip_totals[arm] = {"eligible_n": eligible_n, "negative_flip_n": negative_flip_n}
        flip_totals[arm]["rate"] = float(negative_flip_n / eligible_n) if eligible_n else None
    improvements = {
        "AP_higher": replay["AP"] is not None and naive["AP"] is not None and replay["AP"] > naive["AP"],
        "FNR_lower": replay["FNR"] is not None and naive["FNR"] is not None and replay["FNR"] < naive["FNR"],
        "old_malicious_negative_flip_rate_lower": flip_totals["replay"]["rate"] is not None and flip_totals["naive"]["rate"] is not None and flip_totals["replay"]["rate"] < flip_totals["naive"]["rate"],
    }
    aggregate["flip_totals"] = flip_totals
    aggregate["qualification"] = {"fpr_not_increased": fpr_ok, "strict_improvements": improvements, "decision": "经验回放获得资格" if fpr_ok and any(value is True for value in improvements.values()) else "经验回放不获资格；不得扩展安全回归约束", "screening_only": True, "independent_final_test": False}
    atomic_json(output_root / "qualification-summary.json", aggregate)
    return aggregate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAMDA Domain-IL Naive 对 Replay 的 screening_only 资格筛查")
    parser.add_argument("--config", type=Path, required=True, help="冻结 JSON 配置")
    parser.add_argument("--resume", action="store_true", help="从同一身份最新原子断点恢复")
    parser.add_argument("--validate-config", action="store_true", help="只校验冻结配置，不读取数据或创建运行目录")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(args.config.resolve())
    if args.validate_config:
        print(json.dumps({"valid": True, "run_id": config["identity"]["run_id"], "screening_only": True}, ensure_ascii=False))
        return 0
    torch.set_float32_matmul_precision(config["training"]["float32_matmul_precision"])
    output_root, data_root = Path(config["paths"]["output_root"]), Path(config["paths"]["data_root"])
    prepare_output(output_root, config, args.config.resolve(), args.resume)
    started_at = now_utc()
    started_monotonic = time.monotonic()
    write_status(output_root, "running", "开始 LAMDA Domain-IL Naive/Replay 资格筛查", started_at)
    try:
        features, files, manifest = verify_input(data_root, config)
        atomic_json(output_root / "input-manifest.json", {"input_manifest_path": str(data_root / "manifest.json"), "input_manifest_sha256": sha256_file(data_root / "manifest.json"), "manifest": manifest, "published_feature_space_uses_future_covariates": True, "screening_only": True})
        device = choose_device()
        receipt = {"device": str(device), "torch": torch.__version__, "numpy": np.__version__, "sklearn": sklearn.__version__, "platform": platform.platform(), "float32_matmul_precision": config["training"]["float32_matmul_precision"], "torch_compile": False, "cpu_feature_dtype": "uint8", "device_feature_dtype": "float32", "started_at": started_at}
        atomic_json(output_root / "runtime-receipt.json", receipt)
        arm_metrics = {arm: execute_arm(arm, config, features, files, output_root, device, args.resume, started_at) for arm in config["arms"]}
        qualification = aggregate_qualification(output_root, config)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        atomic_json(output_root / "resource-receipt.json", {**receipt, "completed_at": now_utc(), "wall_seconds": time.monotonic() - started_monotonic, "max_rss": usage.ru_maxrss, "max_rss_unit": "platform_dependent", "cuda_max_memory_allocated": int(torch.cuda.max_memory_allocated()) if device.type == "cuda" else None, "cuda_max_memory_reserved": int(torch.cuda.max_memory_reserved()) if device.type == "cuda" else None})
        atomic_json(output_root / "run-manifest.json", {"tool_sha256": sha256_file(Path(__file__).resolve()), "config_sha256": sha256_file(args.config.resolve()), "arms": list(arm_metrics), "qualification": qualification["qualification"], "screening_only": True})
        write_status(output_root, "completed", qualification["qualification"]["decision"], started_at)
        return 0
    except Exception as error:
        write_status(output_root, "failed", f"{type(error).__name__}: {error}", started_at)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
