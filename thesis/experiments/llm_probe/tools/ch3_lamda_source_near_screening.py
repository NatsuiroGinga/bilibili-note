#!/usr/bin/env python3
"""LAMDA 来源期与近时段 screening_only 资格探针。

该工具只打开 2013、2014、2016、2017 年的行数据；2018--2025 年只能由输入
manifest 的文件级记录表示。发布的 4561 维特征空间已知使用未来协变量，因此
本工具绝不将结果称为严格来源期无泄漏评价。
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import os
import platform
import random
import resource
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pyarrow.dataset as ds
import sklearn
import torch
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    roc_auc_score,
)
from torch import nn


ALLOWED_YEARS = (2013, 2014, 2016, 2017)
SEALED_YEARS = tuple(range(2018, 2026))
SOURCE_YEARS = (2013, 2014)
IID_MONTHS = {"2013-12", "2014-08"}
METADATA_COLUMNS = ("hash", "label", "family", "vt_count", "year_month")
OFFICIAL_CODE_REVISION = "7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249"
FUTURE_COVARIATE_KEY = "published_feature_space_uses_future_covariates"
SEED = 42
BATCH_SIZE = 512
EPOCHS = 6
LEARNING_RATE = 0.001
SCANNER_BATCH_SIZE = 2048
MAX_SCREENING_PARAMETERS = 1_000_000
EXPECTED_PARAMETER_COUNTS = {"all_features": 594753, "without_url_domain": 415169}


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def common_metadata() -> dict[str, Any]:
    return {
        FUTURE_COVARIATE_KEY: True,
        "official_vectorization_code_revision": OFFICIAL_CODE_REVISION,
        "protocol": "screening_only",
        "strict_source_inductive_protocol": False,
    }


def require_unsealed_text(value: str, context: str) -> None:
    for year in SEALED_YEARS:
        if str(year) in value:
            raise ValueError(f"封印年份 {year} 出现在{context}；拒绝在读取行数据前继续")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def expected_data_root() -> Path:
    return repository_root() / "thesis/experiments/llm_probe/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767"


def load_and_verify_manifest(data_root: Path) -> dict[str, Any]:
    """核验冻结下载身份；不打开任何 Parquet 行数据。"""
    if data_root.resolve() != expected_data_root().resolve():
        raise ValueError("data-root 不等于冻结的 LAMDA Baseline 输入根")
    manifest_path = data_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    expected = {
        ("source", "repo_id"): "IQSeC-Lab/LAMDA",
        ("source", "revision"): "ad9614bdd5556767f97ced2fce797c2f06408ebf",
        ("download", "file_count"): 26,
        ("download", "total_bytes"): 232622050,
        ("download", "completion_status"): "complete",
        ("content", "parquet_files"): 24,
        ("content", "rows"): 1008381,
        ("verification", "official_lfs_sha256_checked"): 25,
        ("verification", "official_lfs_sha256_mismatches"): 0,
    }
    for (section, key), wanted in expected.items():
        if manifest.get(section, {}).get(key) != wanted:
            raise ValueError(f"manifest {section}.{key} 不匹配冻结值")
    if manifest.get("content", {}).get("columns") != [4566]:
        raise ValueError("manifest 列数不等于 4566")
    if len(manifest.get("files", [])) != 26:
        raise ValueError("manifest 文件条目数不等于 26")
    return manifest


def discover_allowed_files(data_root: Path) -> dict[int, list[Path]]:
    """只构造允许年份路径，避免枚举或打开封印年份 Parquet。"""
    files: dict[int, list[Path]] = {}
    for year in ALLOWED_YEARS:
        year_dir = data_root / "Baseline" / str(year)
        require_unsealed_text(str(year_dir), "允许数据目录")
        paths = [year_dir / f"{year}_train.parquet", year_dir / f"{year}_test.parquet"]
        if not all(path.is_file() for path in paths):
            raise FileNotFoundError(f"允许年份 {year} 的 train/test Parquet 不完整")
        for path in paths:
            require_unsealed_text(str(path), "允许数据文件")
        files[year] = paths
    return files


def load_feature_views(mapping_path: Path) -> dict[str, list[str]]:
    rows: list[dict[str, str]] = []
    with mapping_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    all_features = [row["mapped_name"] for row in rows]
    url_features = [row["mapped_name"] for row in rows if row["feature_name"].startswith("URLDomainList_")]
    without_url_domain = [name for name in all_features if name not in set(url_features)]
    if len(all_features) != 4561 or len(url_features) != 1403 or len(without_url_domain) != 3158:
        raise ValueError("特征映射计数不符合 4561/1403/3158 冻结合同")
    if len(set(all_features)) != len(all_features):
        raise ValueError("特征映射含重复列")
    return {"all_features": all_features, "without_url_domain": without_url_domain}


def set_seed() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)


def choose_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def route_rows(months: np.ndarray) -> np.ndarray:
    routes: list[str] = []
    for month in months.astype(str):
        year = int(month[:4])
        if year not in ALLOWED_YEARS:
            raise ValueError(f"行数据含不允许年份 {year}")
        if year in SOURCE_YEARS:
            routes.append("iid" if month in IID_MONTHS else "train")
        else:
            routes.append(f"dev_{year}")
    return np.asarray(routes, dtype=object)


def iter_record_batches(paths: list[Path], features: list[str], fingerprint_features: list[str] | None = None) -> Iterator[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    """分批读取当前视图，始终显式投影元数据而不将其作为模型输入。"""
    for path in paths:
        require_unsealed_text(str(path), "Parquet 扫描路径")
        fingerprint_features = fingerprint_features or features
        columns = list(dict.fromkeys([*features, *fingerprint_features, *METADATA_COLUMNS]))
        scanner = ds.dataset(path, format="parquet").scanner(columns=columns, batch_size=SCANNER_BATCH_SIZE)
        for batch in scanner.to_batches():
            frame = batch.to_pandas(split_blocks=True)
            features_np = frame.loc[:, features].to_numpy(dtype=np.float32, copy=True)
            fingerprint_np = frame.loc[:, fingerprint_features].to_numpy(dtype=np.float32, copy=True)
            labels = frame["label"].to_numpy(dtype=np.int64, copy=True)
            months = frame["year_month"].astype(str).to_numpy()
            families = frame["family"].fillna("").astype(str).to_numpy()
            yield features_np, fingerprint_np, labels, months, families


def iter_split_batches(paths: list[Path], features: list[str], wanted: str, shuffle_rng: np.random.Generator | None = None) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    for x, _, labels, months, _ in iter_record_batches(paths, features):
        mask = route_rows(months) == wanted
        selected_x, selected_y = x[mask], labels[mask]
        if shuffle_rng is not None and len(selected_y) > 1:
            order = shuffle_rng.permutation(len(selected_y))
            selected_x, selected_y = selected_x[order], selected_y[order]
        for start in range(0, len(selected_y), BATCH_SIZE):
            batch_x, batch_y = selected_x[start : start + BATCH_SIZE], selected_y[start : start + BATCH_SIZE]
            if len(batch_y) > 1:
                yield batch_x, batch_y


class LamdaMLP(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        width = input_dim
        for next_width in (128, 64, 32):
            layers.extend([nn.Linear(width, next_width), nn.BatchNorm1d(next_width), nn.ReLU(), nn.Dropout(0.5)])
            width = next_width
        layers.append(nn.Linear(width, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x).squeeze(1)


def predict(model: nn.Module, paths: list[Path], features: list[str], fingerprint_features: list[str], train_fingerprints: set[bytes], device: torch.device) -> dict[str, dict[str, np.ndarray]]:
    output: dict[str, dict[str, list[Any]]] = defaultdict(lambda: defaultdict(list))
    model.eval()
    with torch.inference_mode():
        for x, fingerprint_x, labels, months, families in iter_record_batches(paths, features, fingerprint_features):
            routes = route_rows(months)
            scores = torch.sigmoid(model(torch.from_numpy(x).to(device))).cpu().numpy()
            fingerprints = [hashlib.sha256(np.ascontiguousarray(row, dtype=np.uint8).tobytes()).digest() for row in fingerprint_x]
            for route in ("iid", "dev_2016", "dev_2017"):
                mask = routes == route
                if not np.any(mask):
                    continue
                output[route]["labels"].extend(labels[mask].tolist())
                output[route]["scores"].extend(scores[mask].tolist())
                output[route]["months"].extend(months[mask].tolist())
                output[route]["families"].extend(families[mask].tolist())
                output[route]["seen_training_vector"].extend(fingerprints[index] in train_fingerprints for index in np.flatnonzero(mask))
    return {route: {key: np.asarray(values) for key, values in values_by_key.items()} for route, values_by_key in output.items()}


def metric_values(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float | int | None]:
    predicted = scores >= threshold
    tp = int(np.sum((predicted == 1) & (labels == 1)))
    fp = int(np.sum((predicted == 1) & (labels == 0)))
    tn = int(np.sum((predicted == 0) & (labels == 0)))
    fn = int(np.sum((predicted == 0) & (labels == 1)))
    return {
        "n": int(len(labels)),
        "positive_rate": float(np.mean(labels)),
        "roc_auc": float(roc_auc_score(labels, scores)) if len(np.unique(labels)) == 2 else None,
        "average_precision": float(average_precision_score(labels, scores)) if len(np.unique(labels)) == 2 else None,
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "macro_f1": float(f1_score(labels, predicted, average="macro", zero_division=0)),
        "fpr": float(fp / (fp + tn)) if fp + tn else None,
        "fnr": float(fn / (fn + tp)) if fn + tp else None,
        "brier_score": float(brier_score_loss(labels, scores)),
        "threshold": float(threshold),
    }


def split_metrics(values: dict[str, np.ndarray], zero_fpr_threshold: float) -> dict[str, Any]:
    labels, scores = values["labels"].astype(int), values["scores"].astype(float)
    seen = values["seen_training_vector"].astype(bool)
    result: dict[str, Any] = {
        "training_vector_repeat_count": int(np.sum(seen)),
        "training_vector_repeat_rate": float(np.mean(seen)),
        "all": {
            "fixed_probability_0_5": metric_values(labels, scores, 0.5),
            "iid_zero_false_positive": metric_values(labels, scores, zero_fpr_threshold),
        },
    }
    if not np.all(seen):
        result["novel_without_source_feature_vector"] = {
            "fixed_probability_0_5": metric_values(labels[~seen], scores[~seen], 0.5),
            "iid_zero_false_positive": metric_values(labels[~seen], scores[~seen], zero_fpr_threshold),
        }
    month_recall: dict[str, Any] = {}
    family_recall: dict[str, Any] = {}
    months, families = values["months"].astype(str), values["families"].astype(str)
    for month in sorted(set(months)):
        mask = months == month
        positives = labels[mask] == 1
        month_recall[month] = {"n": int(np.sum(mask)), "positive_n": int(np.sum(positives)), "recall": float(np.mean((scores[mask] >= 0.5)[positives])) if np.any(positives) else None}
    for family in sorted(set(families[labels == 1])):
        mask = (families == family) & (labels == 1)
        family_recall[family] = {"n": int(np.sum(mask)), "recall": float(np.mean(scores[mask] >= 0.5))}
    if month_recall:
        result["month_recall_fixed_probability_0_5"] = month_recall
        eligible = [(name, item["recall"]) for name, item in month_recall.items() if item["recall"] is not None]
        result["worst_month_recall_fixed_probability_0_5"] = min(eligible, key=lambda item: item[1]) if eligible else None
    if family_recall:
        result["malicious_family_recall_fixed_probability_0_5"] = family_recall
        result["worst_family_recall_fixed_probability_0_5"] = min(family_recall.items(), key=lambda item: item[1]["recall"])
    return result


def collect_train_fingerprints(paths: list[Path], all_features: list[str]) -> set[bytes]:
    fingerprints: set[bytes] = set()
    for x, _, _, months, _ in iter_record_batches(paths, all_features):
        for row in x[route_rows(months) == "train"]:
            fingerprints.add(hashlib.sha256(np.ascontiguousarray(row, dtype=np.uint8).tobytes()).digest())
    return fingerprints


def train_view(name: str, features: list[str], fingerprint_features: list[str], source_paths: list[Path], all_paths: list[Path], train_fingerprints: set[bytes], device: torch.device, progress: Path, started: float) -> dict[str, Any]:
    set_seed()
    model = LamdaMLP(len(features)).to(device)
    parameter_count = int(sum(parameter.numel() for parameter in model.parameters()))
    if parameter_count > MAX_SCREENING_PARAMETERS:
        raise RuntimeError(f"模型 {name} 参数量 {parameter_count} 超过本机筛选上限 {MAX_SCREENING_PARAMETERS}")
    if parameter_count != EXPECTED_PARAMETER_COUNTS[name]:
        raise RuntimeError(f"模型 {name} 参数量 {parameter_count} 不等于冻结值 {EXPECTED_PARAMETER_COUNTS[name]}")
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.BCEWithLogitsLoss()
    best_ap, best_state, history = float("-inf"), None, []
    for epoch in range(1, EPOCHS + 1):
        model.train()
        rng = np.random.default_rng(SEED + epoch)
        losses: list[float] = []
        for x, labels in iter_split_batches(source_paths, features, "train", rng):
            optimizer.zero_grad(set_to_none=True)
            logits = model(torch.from_numpy(x).to(device))
            loss = loss_fn(logits, torch.from_numpy(labels.astype(np.float32)).to(device))
            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))
        iid = predict(model, source_paths, features, fingerprint_features, train_fingerprints, device)["iid"]
        iid_ap = float(average_precision_score(iid["labels"], iid["scores"]))
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "iid_average_precision": iid_ap})
        if iid_ap > best_ap:
            best_ap = iid_ap
            best_state = copy.deepcopy(model.state_dict())
        progress.open("a").write(json.dumps({**common_metadata(), "view": name, "epoch": epoch, "elapsed_seconds": time.monotonic() - started, "iid_average_precision": iid_ap}, ensure_ascii=False) + "\n")
        print(f"[{name}] epoch={epoch}/{EPOCHS} iid_ap={iid_ap:.6f} elapsed={time.monotonic() - started:.1f}s", flush=True)
    if best_state is None:
        raise RuntimeError("未保存 IID AP 最佳模型状态")
    model.load_state_dict(best_state)
    predictions = predict(model, all_paths, features, fingerprint_features, train_fingerprints, device)
    iid = predictions["iid"]
    benign_scores = iid["scores"][iid["labels"].astype(int) == 0]
    if not len(benign_scores):
        raise RuntimeError("IID 验证没有良性样本，无法冻结零假阳性阈值")
    threshold = float(np.nextafter(np.max(benign_scores), np.inf))
    return {
        "feature_count": len(features),
        "parameter_count": parameter_count,
        "best_iid_average_precision": best_ap,
        "epoch_history": history,
        "iid_zero_false_positive_threshold": threshold,
        "splits": {route: split_metrics(values, threshold) for route, values in predictions.items()},
    }


def numeric_deltas(full: Any, without: Any) -> Any:
    if isinstance(full, dict) and isinstance(without, dict):
        return {key: numeric_deltas(full[key], without[key]) for key in full.keys() & without.keys()}
    if isinstance(full, (int, float)) and isinstance(without, (int, float)) and not isinstance(full, bool) and not isinstance(without, bool):
        return full - without
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAMDA 来源期/近时段 screening_only 资格探针")
    parser.add_argument("--data-root", type=Path, required=True, help="冻结的 LAMDA Baseline 数据根")
    parser.add_argument("--output-dir", type=Path, required=True, help="唯一的新诊断制品目录")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_unsealed_text(str(args.data_root), "命令行 data-root")
    require_unsealed_text(str(args.output_dir), "命令行 output-dir")
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError("输出目录已存在；为保护唯一运行身份拒绝覆盖")
    output_dir.mkdir(parents=True)
    started = time.monotonic()
    started_at = now_utc()
    status_path = output_dir / "status.json"
    try:
        manifest = load_and_verify_manifest(args.data_root.resolve())
        allowed = discover_allowed_files(args.data_root.resolve())
        views = load_feature_views(args.data_root / "Baseline/feature_mapping.csv")
        device = choose_device()
        config = {**common_metadata(), "seed": SEED, "epochs": EPOCHS, "batch_size": BATCH_SIZE, "optimizer": "Adam", "learning_rate": LEARNING_RATE, "dtype": "float32", "device": str(device), "allowed_years": list(ALLOWED_YEARS), "sealed_years": list(SEALED_YEARS), "iid_months": sorted(IID_MONTHS), "feature_views": {name: len(features) for name, features in views.items()}, "max_screening_parameters": MAX_SCREENING_PARAMETERS, "expected_parameter_counts": EXPECTED_PARAMETER_COUNTS}
        json_dump(output_dir / "effective-config.json", config)
        json_dump(output_dir / "manifest.json", {**common_metadata(), "input_manifest_path": str((args.data_root / "manifest.json").resolve()), "input_manifest_sha256": sha256_file(args.data_root / "manifest.json"), "verified_manifest": manifest})
        json_dump(status_path, {**common_metadata(), "status": "running", "started_at": started_at})
        source_paths = [path for year in SOURCE_YEARS for path in allowed[year]]
        all_paths = [path for year in ALLOWED_YEARS for path in allowed[year]]
        fingerprints = collect_train_fingerprints(source_paths, views["all_features"])
        progress = output_dir / "progress.jsonl"
        full = train_view("all_features", views["all_features"], views["all_features"], source_paths, all_paths, fingerprints, device, progress, started)
        without = train_view("without_url_domain", views["without_url_domain"], views["all_features"], source_paths, all_paths, fingerprints, device, progress, started)
        metrics = {**common_metadata(), "training_feature_fingerprint_count": len(fingerprints), "views": {"all_features": full, "without_url_domain": without}, "all_features_minus_without_url_domain": numeric_deltas(full.get("splits"), without.get("splits")), "interpretation_boundary": "仅作 URLDomainList 特征捷径诊断和已发布特征空间中的错误余量观察；不可裁决无泄漏正式资格。"}
        json_dump(output_dir / "metrics.json", metrics)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        resource_data = {**common_metadata(), "device": str(device), "python": sys.version, "platform": platform.platform(), "torch": torch.__version__, "pyarrow": __import__("pyarrow").__version__, "sklearn": sklearn.__version__, "numpy": np.__version__, "wall_seconds": time.monotonic() - started, "peak_resident_set_size": usage.ru_maxrss, "peak_resident_set_size_unit": "bytes_on_macos", "mps_peak_memory_bytes": None, "mps_peak_memory_note": "MPS 无可靠通用峰值显存接口；当前实际设备已单独记录。", "tool_sha256": sha256_file(Path(__file__).resolve())}
        json_dump(output_dir / "resource.json", resource_data)
        json_dump(status_path, {**common_metadata(), "status": "completed", "started_at": started_at, "completed_at": now_utc(), "elapsed_seconds": time.monotonic() - started})
        output_files = {}
        for path in (output_dir / "effective-config.json", status_path, output_dir / "metrics.json", output_dir / "resource.json", output_dir / "progress.jsonl"):
            output_files[path.name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        run_manifest = json.loads((output_dir / "manifest.json").read_text())
        run_manifest["output_files"] = output_files
        run_manifest["manifest_self_hash_note"] = "manifest.json 不含自身 SHA256，避免自指哈希；其余全部输出文件均已列出。"
        json_dump(output_dir / "manifest.json", run_manifest)
        return 0
    except Exception as error:
        json_dump(status_path, {**common_metadata(), "status": "failed", "started_at": started_at, "failed_at": now_utc(), "error_type": type(error).__name__, "error": str(error)})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
