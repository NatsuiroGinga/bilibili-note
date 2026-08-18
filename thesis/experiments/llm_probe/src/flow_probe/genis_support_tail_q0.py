"""GeNIS 60 秒十三类类别支持与固定预算尾部联合 Q0。"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import io
import json
import math
import os
import resource
import sys
import time
import warnings
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from numpy.lib.format import open_memmap


class GeNISQ0Error(RuntimeError):
    """表示冻结合同被破坏。"""


LABEL_COLUMNS = ("BinaryLabel", "CategoryLabel", "SubCategoryLabel")
SPLITS = ("fit", "calibration", "q0_eval")
VARIANTS = ("B0", "S1", "T1", "ST")
BENIGN_CLASS_COUNT = 3
EXPECTED_STATES = {"DATA_GATE_PASSED", "SELECTION_FROZEN", "FINISHED"}
BOOLEAN_ONE_HOT_FIELDS = (
    "Proto_arp",
    "Proto_icmp",
    "Proto_ipv6-icmp",
    "Proto_tcp",
    "Proto_udp",
    "Flgs_e",
    "Flgs_e *",
    "Flgs_e d",
    "Flgs_e g",
    "Flgs_e r",
    "Flgs_e s",
    "Flgs_eU",
    "State_CLO",
    "State_CON",
    "State_ECO",
    "State_FIN",
    "State_INT",
    "State_NRS",
    "State_REQ",
    "State_RST",
    "State_TST",
    "State_URH",
    "State_URHPRO",
)


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GeNISQ0Error(f"无法读取 JSON：{path}：{error}") from error
    if not isinstance(value, dict):
        raise GeNISQ0Error(f"JSON 顶层必须是对象：{path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    partial.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _md5(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - 官方归档合同使用 MD5 身份值。
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_save(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with partial.open("wb") as handle:
        np.save(handle, array, allow_pickle=False)
    partial.replace(path)


def _canonical_json_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_config(path: Path) -> dict[str, Any]:
    config = _json(path.resolve())
    required = {
        "schema_version",
        "contract_version",
        "seed",
        "data",
        "feature_budget",
        "classes",
        "split",
        "xgboost",
        "weighting",
        "variants",
        "gates",
        "paths",
        "evidence",
        "swanlab",
    }
    if set(config) < required:
        raise GeNISQ0Error(f"配置缺少字段：{sorted(required - set(config))}")
    if config["seed"] != 42 or config["evidence"] != {
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }:
        raise GeNISQ0Error("种子或证据标志不符合冻结合同")
    if tuple(config["classes"]) != tuple(config["data"]["class_order"]):
        raise GeNISQ0Error("十三类顺序配置不一致")
    if len(config["classes"]) != 13 or len(config["feature_budget"]["fields"]) != 76:
        raise GeNISQ0Error("类别数或特征数不符合冻结合同")
    if (
        config["xgboost"]["fixed"]["tree_method"] != "hist"
        or config["xgboost"]["fixed"]["device"] != "cuda"
    ):
        raise GeNISQ0Error("XGBoost 必须固定 hist/cuda")
    return config


def _resolve(config_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    project_root = config_path.resolve().parent.parent
    return (project_root / path).resolve()


def _output_root(config: Mapping[str, Any], config_path: Path, override: Path | None) -> Path:
    return (override or _resolve(config_path, str(config["paths"]["output_root"]))).resolve()


def _module_path() -> Path:
    return Path(__file__).resolve()


class _HashingReader(io.RawIOBase):
    def __init__(self, raw: Any, digest: Any) -> None:
        self.raw = raw
        self.digest = digest

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        size = self.raw.readinto(buffer)
        if size:
            self.digest.update(memoryview(buffer)[:size])
        return size


def _member_rows(archive_path: Path, member: str, digest: Any | None = None) -> Iterable[list[str]]:
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
        if member not in names:
            raise GeNISQ0Error(f"冻结成员不存在：{member}")
        with archive.open(member, "r") as raw:
            source: Any = raw
            if digest is not None:
                source = io.BufferedReader(_HashingReader(raw, digest), buffer_size=1024 * 1024)
            with io.TextIOWrapper(source, encoding="utf-8-sig", newline="") as text:
                yield from csv.reader(text)


def _observation_hash(names: Sequence[str], tokens: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for name, token in zip(names, tokens, strict=True):
        name_bytes = name.encode("utf-8")
        token_bytes = token.encode("utf-8")
        digest.update(name_bytes)
        digest.update(len(token_bytes).to_bytes(8, "big"))
        digest.update(token_bytes)
    return digest.hexdigest()


def _feature_values(
    feature_names: Sequence[str],
    positions: Sequence[int],
    row: Sequence[str],
    row_number: int,
) -> np.ndarray:
    values = np.empty(len(feature_names), dtype=np.float32)
    for index, (name, position) in enumerate(zip(feature_names, positions, strict=True)):
        token = row[position]
        if name in BOOLEAN_ONE_HOT_FIELDS:
            if token == "True":
                values[index] = 1.0
            elif token == "False":
                values[index] = 0.0
            else:
                raise GeNISQ0Error(f"第 {row_number} 行布尔独热字段 {name} 不是精确 True/False")
        else:
            try:
                values[index] = float(token)
            except ValueError as error:
                raise GeNISQ0Error(f"第 {row_number} 行连续数值字段 {name} 含不可解析值") from error
    if not np.isfinite(values).all():
        raise GeNISQ0Error(f"第 {row_number} 行含非有限数值")
    return values


def _split_groups(
    group_rows: Mapping[str, int], group_labels: Mapping[str, int], class_count: int, seed: int
) -> dict[str, str]:
    assignments: dict[str, str] = {}
    ratios = np.asarray([0.6, 0.2, 0.2], dtype=np.float64)
    for class_index in range(class_count):
        groups = [key for key, label in group_labels.items() if label == class_index]
        if len(groups) < 3:
            raise GeNISQ0Error(f"类别 {class_index} 的唯一观察组少于 3")
        groups.sort(
            key=lambda key: (
                -group_rows[key],
                hashlib.sha256(f"{seed}:{class_index}:{key}".encode()).hexdigest(),
            )
        )
        total = sum(group_rows[key] for key in groups)
        targets = ratios * total
        counts = np.zeros(3, dtype=np.int64)
        for position, key in enumerate(groups):
            remaining = len(groups) - position
            empty = [index for index, count in enumerate(counts) if count == 0]
            if empty and remaining <= len(empty):
                chosen = empty[0]
            else:
                deficits = targets - counts
                chosen = int(np.argmax(deficits / np.maximum(targets, 1.0)))
            assignments[key] = SPLITS[chosen]
            counts[chosen] += group_rows[key]
        if np.any(counts == 0):
            raise GeNISQ0Error(f"类别 {class_index} 的三分区非空门禁失败")
    return assignments


def _status(output_root: Path, state: str, stage: str, **extra: Any) -> None:
    if state not in EXPECTED_STATES | {"FAILED", "RUNNING"}:
        raise GeNISQ0Error(f"非法状态：{state}")
    _write_json(
        output_root / "status.json",
        {
            "schema_version": "genis-support-tail-q0-status-v1",
            "state": state,
            "stage": stage,
            "updated_at_epoch": time.time(),
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
            **extra,
        },
    )


def _heartbeat(stage: str, completed: int, total: int, started: float) -> None:
    elapsed = max(time.monotonic() - started, 1e-9)
    rate = completed / elapsed
    eta = (total - completed) / rate if rate > 0 else None
    print(
        json.dumps(
            {
                "event": "progress",
                "stage": stage,
                "completed": completed,
                "total": total,
                "elapsed_seconds": round(elapsed, 3),
                "throughput_per_second": round(rate, 3),
                "eta_seconds": None if eta is None else round(eta, 3),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def prepare(
    config_path: Path,
    output_override: Path | None,
    archive_override: Path | None,
) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = _load_config(config_path)
    output_root = _output_root(config, config_path, output_override)
    if output_root.exists():
        raise GeNISQ0Error(f"唯一运行目录已存在，拒绝覆盖或续写：{output_root}")
    output_root.mkdir(parents=True)
    _status(output_root, "RUNNING", "prepare")
    started = time.monotonic()
    archive_path = (
        archive_override.resolve()
        if archive_override is not None
        else _resolve(config_path, str(config["data"]["archive_path"]))
    )
    if _md5(archive_path) != config["data"]["archive_md5"]:
        raise GeNISQ0Error("GeNIS 归档 MD5 不匹配")
    member = str(config["data"]["allowed_member"])
    feature_names = list(config["feature_budget"]["fields"])
    class_names = list(config["classes"])
    class_to_index = {name: index for index, name in enumerate(class_names)}
    group_rows: Counter[str] = Counter()
    group_labels: dict[str, int] = {}
    group_label_triples: dict[str, tuple[str, str, str]] = {}
    digest = hashlib.sha256()
    iterator = iter(_member_rows(archive_path, member, digest))
    try:
        header = next(iterator)
    except StopIteration as error:
        raise GeNISQ0Error("冻结 CSV 为空") from error
    if len(header) != 87 or len(header) != len(set(header)):
        raise GeNISQ0Error("冻结 CSV 必须有 87 个不重复字段")
    if tuple(header[-3:]) != LABEL_COLUMNS:
        raise GeNISQ0Error("标签字段必须是最后三列")
    if hashlib.sha256(",".join(header).encode()).hexdigest() != config["data"]["header_sha256"]:
        raise GeNISQ0Error("60 秒原始表头 SHA-256 不匹配")
    if _canonical_json_sha(header) != config["data"]["ordered_fields_sha256"]:
        raise GeNISQ0Error("60 秒有序字段数组 SHA-256 不匹配")
    non_label_names = header[:-3]
    if [
        name for name in non_label_names if name not in config["feature_budget"]["excluded"]
    ] != feature_names:
        raise GeNISQ0Error("safe76-v1 字段顺序不匹配")
    if tuple(feature_names[-len(BOOLEAN_ONE_HOT_FIELDS) :]) != BOOLEAN_ONE_HOT_FIELDS:
        raise GeNISQ0Error("safe76-v1 的 23 个官方布尔独热字段顺序不匹配")
    label_position = header.index("SubCategoryLabel")
    feature_positions = [header.index(name) for name in feature_names]
    observed_classes: set[str] = set()
    row_count = 0
    for row_count, row in enumerate(iterator, start=1):
        if len(row) != len(header):
            raise GeNISQ0Error(f"第 {row_count} 行列数不是 87")
        label = row[label_position]
        if label not in class_to_index:
            raise GeNISQ0Error(f"发现冻结顺序外标签：{label}")
        observed_classes.add(label)
        group = _observation_hash(non_label_names, row[:-3])
        index = class_to_index[label]
        previous = group_labels.setdefault(group, index)
        if previous != index:
            raise GeNISQ0Error(f"观察哈希跨标签冲突：{group}")
        triple = tuple(row[header.index(name)] for name in LABEL_COLUMNS)
        previous_triple = group_label_triples.setdefault(group, triple)
        if previous_triple != triple:
            raise GeNISQ0Error(f"观察哈希跨三层标签冲突：{group}")
        group_rows[group] += 1
        if row_count % int(config["runtime"]["progress_rows"]) == 0:
            _heartbeat("prepare-pass-1", row_count, int(config["data"]["expected_rows"]), started)
    if row_count != int(config["data"]["expected_rows"]):
        raise GeNISQ0Error(f"行数不匹配：{row_count}")
    if digest.hexdigest() != config["data"]["member_sha256"]:
        raise GeNISQ0Error("冻结成员内容 SHA-256 不匹配")
    if observed_classes != set(class_names):
        raise GeNISQ0Error("十三类实际集合不完整")
    assignments = _split_groups(group_rows, group_labels, len(class_names), int(config["seed"]))
    split_rows = Counter()
    for group, count in group_rows.items():
        split_rows[assignments[group]] += count
    data_root = output_root / "data"
    arrays: dict[str, dict[str, Any]] = {}
    for split in SPLITS:
        split_root = data_root / split
        split_root.mkdir(parents=True)
        arrays[split] = {
            "x": open_memmap(
                split_root / "features.npy.partial",
                mode="w+",
                dtype=np.float32,
                shape=(split_rows[split], len(feature_names)),
            ),
            "hash": open_memmap(
                split_root / "observation_hash.npy.partial",
                mode="w+",
                dtype=np.uint8,
                shape=(split_rows[split], 32),
            ),
        }
        label_root = data_root / ("q0_eval_labels" if split == "q0_eval" else split)
        label_root.mkdir(parents=True, exist_ok=True)
        arrays[split]["y"] = open_memmap(
            label_root / "labels.npy.partial",
            mode="w+",
            dtype=np.uint8,
            shape=(split_rows[split],),
        )
    offsets = Counter()
    iterator = iter(_member_rows(archive_path, member))
    second_header = next(iterator)
    if second_header != header:
        raise GeNISQ0Error("两遍扫描期间表头发生变化")
    second_started = time.monotonic()
    for row_number, row in enumerate(iterator, start=1):
        group = _observation_hash(non_label_names, row[:-3])
        split = assignments[group]
        offset = offsets[split]
        values = _feature_values(feature_names, feature_positions, row, row_number)
        arrays[split]["x"][offset] = values
        arrays[split]["hash"][offset] = np.frombuffer(bytes.fromhex(group), dtype=np.uint8)
        arrays[split]["y"][offset] = class_to_index[row[label_position]]
        offsets[split] += 1
        if row_number % int(config["runtime"]["progress_rows"]) == 0:
            _heartbeat("prepare-pass-2", row_number, row_count, second_started)
    for split in SPLITS:
        if offsets[split] != split_rows[split]:
            raise GeNISQ0Error(f"{split} 写入行数不匹配")
        for name, array in arrays[split].items():
            array.flush()
            del array
            arrays[split][name] = None
        (data_root / split / "features.npy.partial").replace(data_root / split / "features.npy")
        (data_root / split / "observation_hash.npy.partial").replace(
            data_root / split / "observation_hash.npy"
        )
        label_root = data_root / ("q0_eval_labels" if split == "q0_eval" else split)
        (label_root / "labels.npy.partial").replace(label_root / "labels.npy")
    gc.collect()
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except (ImportError, OSError) as error:
        raise GeNISQ0Error("PyArrow 依赖不可用") from error
    manifest_rows = [
        {
            "observation_hash": group,
            "class_index": group_labels[group],
            "class_name": class_names[group_labels[group]],
            "split": assignments[group],
            "row_count": group_rows[group],
        }
        for group in sorted(group_rows)
    ]
    pq.write_table(pa.Table.from_pylist(manifest_rows), output_root / "split_manifest.parquet")
    per_class: dict[str, Any] = {}
    for class_index, class_name in enumerate(class_names):
        class_groups = [group for group, label in group_labels.items() if label == class_index]
        total = sum(group_rows[group] for group in class_groups)
        per_class[class_name] = {
            split: {
                "rows": sum(
                    group_rows[group] for group in class_groups if assignments[group] == split
                ),
                "groups": sum(assignments[group] == split for group in class_groups),
                "row_ratio": sum(
                    group_rows[group] for group in class_groups if assignments[group] == split
                )
                / total,
            }
            for split in SPLITS
        }
    split_hash_sets = {
        split: {group for group, assigned in assignments.items() if assigned == split}
        for split in SPLITS
    }
    intersections = {
        f"{left}__{right}": len(split_hash_sets[left] & split_hash_sets[right])
        for index, left in enumerate(SPLITS)
        for right in SPLITS[index + 1 :]
    }
    if any(intersections.values()):
        raise GeNISQ0Error("三分区观察哈希不互斥")
    feature_manifest = {
        "schema_version": "genis-safe76-feature-manifest-v1",
        "feature_budget_id": config["feature_budget"]["id"],
        "fields": feature_names,
        "fields_sha256": _canonical_json_sha(feature_names),
        "excluded": config["feature_budget"]["excluded"],
        "label_columns": list(LABEL_COLUMNS),
        "continuous_numeric_fields": feature_names[: -len(BOOLEAN_ONE_HOT_FIELDS)],
        "boolean_one_hot_fields": list(BOOLEAN_ONE_HOT_FIELDS),
        "boolean_mapping": {"False": 0.0, "True": 1.0},
        "finite_numeric_gate_passed": True,
    }
    _write_json(output_root / "feature_manifest.json", feature_manifest)
    split_audit = {
        "schema_version": "genis-q0-split-audit-v1",
        "seed": config["seed"],
        "ratios": config["split"]["ratios"],
        "rows": dict(split_rows),
        "unique_groups": len(group_rows),
        "duplicate_rows": row_count - len(group_rows),
        "label_conflicts": 0,
        "intersections": intersections,
        "per_class": per_class,
        "all_partitions_have_all_classes": True,
    }
    _write_json(output_root / "split_audit.json", split_audit)
    artifact_paths = (
        [
            output_root / "feature_manifest.json",
            output_root / "split_manifest.parquet",
            output_root / "split_audit.json",
        ]
        + [
            data_root / split / name
            for split in SPLITS
            for name in ("features.npy", "observation_hash.npy")
        ]
        + [data_root / split / "labels.npy" for split in ("fit", "calibration")]
        + [data_root / "q0_eval_labels" / "labels.npy"]
    )
    data_manifest = {
        "schema_version": "genis-support-tail-q0-data-manifest-v1",
        "dataset_version": config["data"]["version"],
        "archive_md5": config["data"]["archive_md5"],
        "allowed_member": member,
        "member_sha256": config["data"]["member_sha256"],
        "forbidden_members_opened": [],
        "rows": row_count,
        "columns": len(header),
        "split_rows": dict(split_rows),
        "artifacts": {str(path.relative_to(output_root)): _sha256(path) for path in artifact_paths},
        "q0_eval_label_sidecar": "data/q0_eval_labels/labels.npy",
        "q0_eval_labels_opened": False,
        **config["evidence"],
    }
    _write_json(output_root / "data_manifest.json", data_manifest)
    _write_json(
        output_root / "contract.json",
        {
            "schema_version": "genis-support-tail-q0-contract-receipt-v1",
            "contract_version": config["contract_version"],
            "config_sha256": _sha256(config_path),
            "code_sha256": _sha256(_module_path()),
            "data_manifest_sha256": _sha256(output_root / "data_manifest.json"),
            **config["evidence"],
        },
    )
    _status(output_root, "DATA_GATE_PASSED", "prepare", rows=row_count)
    result = {"state": "DATA_GATE_PASSED", "rows": row_count, "split_rows": dict(split_rows)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


def _load_development(output_root: Path, split: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if split not in {"fit", "calibration"}:
        raise GeNISQ0Error("选择阶段只允许读取 fit 与 calibration")
    root = output_root / "data" / split
    return (
        np.load(root / "features.npy", mmap_mode="r"),
        np.load(root / "labels.npy", mmap_mode="r"),
        np.load(root / "observation_hash.npy", mmap_mode="r"),
    )


def _verify_development_inputs(
    config_path: Path, output_root: Path, data_manifest: Mapping[str, Any]
) -> None:
    contract = _json(output_root / "contract.json")
    if (
        contract.get("config_sha256") != _sha256(config_path)
        or contract.get("code_sha256") != _sha256(_module_path())
        or contract.get("data_manifest_sha256") != _sha256(output_root / "data_manifest.json")
    ):
        raise GeNISQ0Error("选择阶段的代码、配置或数据清单绑定失效")
    allowed_prefixes = ("data/fit/", "data/calibration/")
    for relative, expected in data_manifest.get("artifacts", {}).items():
        if not relative.startswith(allowed_prefixes):
            continue
        path = output_root / relative
        if not path.is_file() or _sha256(path) != expected:
            raise GeNISQ0Error(f"选择阶段开发输入哈希不一致：{path}")


def _xgb_params(config: Mapping[str, Any], selected: Mapping[str, Any]) -> dict[str, Any]:
    params = dict(config["xgboost"]["fixed"])
    params.update(selected)
    params.pop("n_estimators")
    params.pop("random_state")
    params["seed"] = int(config["seed"])
    params["nthread"] = int(config["runtime"]["xgboost_threads"])
    return params


def _train_booster(
    x: np.ndarray,
    y: np.ndarray,
    params: Mapping[str, Any],
    rounds: int,
    weights: np.ndarray | None = None,
) -> tuple[Any, float, str]:
    try:
        import xgboost as xgb
    except (ImportError, OSError) as error:
        raise GeNISQ0Error("XGBoost 依赖不可用") from error
    matrix = xgb.DMatrix(x, label=y, weight=weights, nthread=int(params["nthread"]))
    started = time.monotonic()
    booster = xgb.train(dict(params), matrix, num_boost_round=rounds)
    elapsed = time.monotonic() - started
    saved = json.loads(booster.save_config())
    try:
        device = saved["learner"]["generic_param"]["device"]
    except (KeyError, TypeError) as error:
        raise GeNISQ0Error("Booster 配置缺少设备字段") from error
    if device != "cuda:0":
        raise GeNISQ0Error(f"XGBoost 静默回退，实际设备为 {device}")
    return booster, elapsed, device


def _predict(booster: Any, x: np.ndarray, threads: int) -> tuple[np.ndarray, float]:
    import xgboost as xgb

    started = time.monotonic()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        probability = np.asarray(booster.predict(xgb.DMatrix(x, nthread=threads)), dtype=np.float64)
    elapsed = time.monotonic() - started
    if "mismatched devices" in " ".join(str(item.message) for item in caught).lower():
        raise GeNISQ0Error("显式 DMatrix 预测仍出现设备不匹配")
    if probability.ndim != 2 or probability.shape[1] != 13:
        raise GeNISQ0Error(f"概率形状错误：{probability.shape}")
    if not np.isfinite(probability).all():
        raise GeNISQ0Error("预测概率含非有限值")
    maximum_error = float(np.max(np.abs(probability.sum(axis=1) - 1.0)))
    if maximum_error > 1e-5:
        raise GeNISQ0Error(f"概率行和误差超过 1e-5：{maximum_error}")
    return probability, elapsed


def _macro_f1(y: np.ndarray, probability: np.ndarray) -> float:
    from sklearn.metrics import f1_score

    return float(f1_score(y, probability.argmax(axis=1), labels=np.arange(13), average="macro"))


def _fold_assignments(hashes: np.ndarray, labels: np.ndarray, folds: int, seed: int) -> np.ndarray:
    group_to_rows: dict[bytes, list[int]] = defaultdict(list)
    for index, value in enumerate(hashes):
        group_to_rows[bytes(value)].append(index)
    assignments = np.empty(len(labels), dtype=np.uint8)
    for class_index in range(13):
        groups = [key for key, rows in group_to_rows.items() if int(labels[rows[0]]) == class_index]
        groups.sort(
            key=lambda key: (
                -len(group_to_rows[key]),
                hashlib.sha256(seed.to_bytes(8, "big") + key).digest(),
            )
        )
        counts = np.zeros(folds, dtype=np.int64)
        for key in groups:
            fold = int(np.argmin(counts))
            rows = group_to_rows[key]
            assignments[rows] = fold
            counts[fold] += len(rows)
        if np.any(counts == 0):
            raise GeNISQ0Error(f"类别 {class_index} 的交叉拟合折非空门禁失败")
    return assignments


def _malicious_score(probability: np.ndarray) -> np.ndarray:
    score = 1.0 - probability[:, :BENIGN_CLASS_COUNT].sum(axis=1)
    if not np.isfinite(score).all():
        raise GeNISQ0Error("恶意分数含非有限值")
    return score


def _threshold(scores: np.ndarray, labels: np.ndarray, alpha: float) -> tuple[float, int, int]:
    benign = np.sort(scores[labels < BENIGN_CLASS_COUNT], kind="stable")
    if len(benign) == 0:
        raise GeNISQ0Error("校准集没有良性样本")
    allowed = math.floor(alpha * len(benign))
    threshold = float(benign[len(benign) - allowed - 1]) if allowed < len(benign) else -math.inf
    actual = int(np.count_nonzero(benign > threshold))
    if actual > allowed:
        raise GeNISQ0Error("严格阈值仍超过校准误报预算")
    return threshold, allowed, actual


def _normalized(weights: np.ndarray, cap: float | None = None) -> np.ndarray:
    value = np.asarray(weights, dtype=np.float64)
    if cap is not None:
        value = np.minimum(value, cap)
    mean = float(value.mean())
    if not np.isfinite(value).all() or mean <= 0:
        raise GeNISQ0Error("样本权重非法")
    return np.asarray(value / mean, dtype=np.float32)


def select(config_path: Path, output_override: Path | None) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = _load_config(config_path)
    output_root = _output_root(config, config_path, output_override)
    status = _json(output_root / "status.json")
    if status.get("state") != "DATA_GATE_PASSED":
        raise GeNISQ0Error("select 只接受 DATA_GATE_PASSED 状态")
    data_manifest = _json(output_root / "data_manifest.json")
    if data_manifest.get("q0_eval_labels_opened") is not False:
        raise GeNISQ0Error("Q0 标签隔离收据无效")
    q0_label_path = output_root / str(data_manifest["q0_eval_label_sidecar"])
    if q0_label_path.name != "labels.npy" or q0_label_path.parent.name != "q0_eval_labels":
        raise GeNISQ0Error("Q0 标签侧车路径不符合隔离合同")
    _verify_development_inputs(config_path, output_root, data_manifest)
    _status(output_root, "RUNNING", "select")
    fit_x, fit_y, fit_hash = _load_development(output_root, "fit")
    calibration_x, calibration_y, _ = _load_development(output_root, "calibration")
    rounds = int(config["xgboost"]["fixed"]["n_estimators"])
    selected_params: dict[str, Any] | None = None
    grid_records: list[dict[str, Any]] = []
    started = time.monotonic()
    grid = [
        {"max_depth": depth, "colsample_bytree": colsample}
        for depth in config["xgboost"]["grid"]["max_depth"]
        for colsample in config["xgboost"]["grid"]["colsample_bytree"]
    ]
    for index, candidate in enumerate(grid, start=1):
        booster, train_seconds, device = _train_booster(
            fit_x, fit_y, _xgb_params(config, candidate), rounds
        )
        probability, predict_seconds = _predict(
            booster, calibration_x, int(config["runtime"]["xgboost_threads"])
        )
        record = {
            **candidate,
            "calibration_macro_f1": _macro_f1(calibration_y, probability),
            "train_seconds": train_seconds,
            "calibration_predict_seconds": predict_seconds,
            "booster_device": device,
        }
        grid_records.append(record)
        _heartbeat("select-grid", index, len(grid), started)
    best = sorted(
        grid_records,
        key=lambda item: (
            -item["calibration_macro_f1"],
            item["max_depth"],
            item["colsample_bytree"],
        ),
    )[0]
    selected_params = {
        "max_depth": int(best["max_depth"]),
        "colsample_bytree": float(best["colsample_bytree"]),
    }
    folds = int(config["split"]["crossfit_folds"])
    fold_id = _fold_assignments(fit_hash, fit_y, folds, int(config["seed"]))
    oof_probability = np.empty((len(fit_y), 13), dtype=np.float32)
    crossfit_records = []
    for fold in range(folds):
        train_mask = fold_id != fold
        held_mask = ~train_mask
        booster, train_seconds, device = _train_booster(
            fit_x[train_mask],
            fit_y[train_mask],
            _xgb_params(config, selected_params),
            rounds,
        )
        probability, predict_seconds = _predict(
            booster, fit_x[held_mask], int(config["runtime"]["xgboost_threads"])
        )
        oof_probability[held_mask] = probability
        crossfit_records.append(
            {
                "fold": fold,
                "train_rows": int(train_mask.sum()),
                "held_rows": int(held_mask.sum()),
                "train_seconds": train_seconds,
                "predict_seconds": predict_seconds,
                "booster_device": device,
            }
        )
        _heartbeat("select-crossfit", fold + 1, folds, started)
    if (
        not np.isfinite(oof_probability).all()
        or float(np.max(np.abs(oof_probability.sum(axis=1) - 1.0))) > 1e-5
    ):
        raise GeNISQ0Error("交叉拟合概率门禁失败")
    unique_support = Counter()
    seen_groups: set[bytes] = set()
    for group, label in zip(fit_hash, fit_y, strict=True):
        key = bytes(group)
        if key not in seen_groups:
            unique_support[int(label)] += 1
            seen_groups.add(key)
    total_unique = sum(unique_support.values())
    support_by_class = np.asarray(
        [
            min(
                float(config["weighting"]["class_weight_cap"]),
                total_unique / (13 * unique_support[index]),
            )
            for index in range(13)
        ],
        dtype=np.float64,
    )
    support_weight = _normalized(support_by_class[np.asarray(fit_y, dtype=np.int64)])
    oof_score = _malicious_score(oof_probability)
    benign_oof = oof_score[np.asarray(fit_y) < BENIGN_CLASS_COUNT]
    q_fit = float(np.quantile(benign_oof, 1.0 - float(config["weighting"]["alpha"])))
    tail_mask = np.where(
        np.asarray(fit_y) < BENIGN_CLASS_COUNT, oof_score >= q_fit, oof_score <= q_fit
    )
    tail_weight = np.where(tail_mask, float(config["weighting"]["tail_weight"]), 1.0)
    variant_weights = {
        "B0": np.ones(len(fit_y), dtype=np.float32),
        "S1": support_weight,
        "T1": _normalized(tail_weight),
        "ST": _normalized(
            support_weight * tail_weight,
            cap=float(config["weighting"]["combined_weight_cap"]),
        ),
    }
    model_root = output_root / "models"
    probability_root = output_root / "calibration_probabilities"
    model_root.mkdir()
    probability_root.mkdir()
    threshold_records: dict[str, Any] = {}
    variant_records: dict[str, Any] = {}
    for index, variant in enumerate(VARIANTS, start=1):
        booster, train_seconds, device = _train_booster(
            fit_x,
            fit_y,
            _xgb_params(config, selected_params),
            rounds,
            variant_weights[variant],
        )
        probability, predict_seconds = _predict(
            booster, calibration_x, int(config["runtime"]["xgboost_threads"])
        )
        model_path = model_root / f"{variant}.ubj"
        booster.save_model(model_path)
        probability_path = probability_root / f"{variant}.npy"
        _atomic_save(probability_path, probability.astype(np.float32))
        score = _malicious_score(probability)
        threshold, allowed, actual = _threshold(
            score, calibration_y, float(config["weighting"]["alpha"])
        )
        threshold_records[variant] = {
            "display_name": config["variants"][variant],
            "threshold": threshold,
            "comparison": "malicious_score > threshold",
            "calibration_benign_rows": int(np.count_nonzero(calibration_y < BENIGN_CLASS_COUNT)),
            "allowed_false_positives": allowed,
            "actual_false_positives": actual,
            "calibration_fpr": actual / int(np.count_nonzero(calibration_y < BENIGN_CLASS_COUNT)),
            "probability_path": str(probability_path.relative_to(output_root)),
            "sample_key_path": "data/calibration/observation_hash.npy",
            "row_position_contract": "zero_based_array_position",
        }
        variant_records[variant] = {
            "model": str(model_path.relative_to(output_root)),
            "model_sha256": _sha256(model_path),
            "calibration_probability": str(probability_path.relative_to(output_root)),
            "calibration_probability_sha256": _sha256(probability_path),
            "train_seconds": train_seconds,
            "calibration_predict_seconds": predict_seconds,
            "booster_device": device,
            "weight_min": float(variant_weights[variant].min()),
            "weight_max": float(variant_weights[variant].max()),
            "weight_mean": float(variant_weights[variant].mean()),
            "cumulative_process_peak_rss_bytes": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                * (1 if sys.platform == "darwin" else 1024)
            ),
        }
        _heartbeat("select-four-variants", index, len(VARIANTS), started)
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except (ImportError, OSError) as error:
        raise GeNISQ0Error("PyArrow 依赖不可用") from error
    audit_table = pa.table(
        {
            "observation_hash": [bytes(value).hex() for value in fit_hash],
            "class_index": np.asarray(fit_y, dtype=np.uint8),
            "fold": fold_id,
            "malicious_score": oof_score.astype(np.float32),
            "support_weight": support_weight,
            "tail_hard": tail_mask,
            "tail_weight": np.asarray(tail_weight, dtype=np.float32),
            "combined_weight": variant_weights["ST"],
        }
    )
    pq.write_table(audit_table, output_root / "oof_weight_audit.parquet")
    _write_json(
        output_root / "selected_xgb_params.json",
        {
            "schema_version": "genis-q0-selected-xgb-params-v1",
            "selection_metric": "calibration_macro_f1",
            "tie_break": ["shallower_max_depth", "smaller_colsample_bytree"],
            "selected": selected_params,
            "fixed": config["xgboost"]["fixed"],
            "grid": grid_records,
            "crossfit": crossfit_records,
        },
    )
    _write_json(
        output_root / "threshold_audit.json",
        {
            "schema_version": "genis-q0-threshold-audit-v1",
            "alpha": config["weighting"]["alpha"],
            "selection_complexity": "O(n log n) stable sort per variant",
            "strict_comparison": True,
            "variants": threshold_records,
        },
    )
    _write_json(
        output_root / "weight_freeze.json",
        {
            "schema_version": "genis-q0-weight-freeze-v1",
            "unique_hash_support": {
                config["classes"][index]: unique_support[index] for index in range(13)
            },
            "raw_support_weights": {
                config["classes"][index]: float(support_by_class[index]) for index in range(13)
            },
            "q_fit": q_fit,
            "tail_rows": int(tail_mask.sum()),
            "variant_training": variant_records,
        },
    )
    frozen_files = [
        output_root / "contract.json",
        output_root / "data_manifest.json",
        output_root / "feature_manifest.json",
        output_root / "split_manifest.parquet",
        output_root / "split_audit.json",
        output_root / "selected_xgb_params.json",
        output_root / "oof_weight_audit.parquet",
        output_root / "threshold_audit.json",
        output_root / "weight_freeze.json",
        config_path,
        _module_path(),
    ] + [model_root / f"{variant}.ubj" for variant in VARIANTS]
    freeze = {
        "schema_version": "genis-q0-evaluation-freeze-v1",
        "state": "SELECTION_FROZEN",
        "hashes": {str(path.resolve()): _sha256(path) for path in frozen_files},
        "models": variant_records,
        "thresholds": threshold_records,
        "q0_eval_label_sidecar": str(q0_label_path.resolve()),
        "q0_eval_labels_opened": False,
        "selection_used_splits": ["fit", "calibration"],
        "selection_used_q0_eval": False,
        **config["evidence"],
    }
    _write_json(output_root / "evaluation_freeze.json", freeze)
    _status(output_root, "SELECTION_FROZEN", "select", q0_eval_labels_opened=False)
    result = {"state": "SELECTION_FROZEN", "selected": selected_params}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


def _verify_freeze(config_path: Path, output_root: Path) -> dict[str, Any]:
    freeze = _json(output_root / "evaluation_freeze.json")
    if (
        freeze.get("state") != "SELECTION_FROZEN"
        or freeze.get("q0_eval_labels_opened") is not False
        or freeze.get("selection_used_q0_eval") is not False
        or freeze.get("final_accessed") is not False
    ):
        raise GeNISQ0Error("评价冻结收据无效")
    for raw_path, expected in freeze.get("hashes", {}).items():
        path = Path(raw_path)
        if not path.is_file() or _sha256(path) != expected:
            raise GeNISQ0Error(f"评价冻结哈希不一致：{path}")
    if (
        str(config_path.resolve()) not in freeze["hashes"]
        or str(_module_path()) not in freeze["hashes"]
    ):
        raise GeNISQ0Error("评价冻结未绑定当前配置或代码")
    manifest = _json(output_root / "data_manifest.json")
    label_sidecar = str(manifest["q0_eval_label_sidecar"])
    for relative, expected in manifest.get("artifacts", {}).items():
        if relative == label_sidecar:
            continue
        path = output_root / relative
        if not path.is_file() or _sha256(path) != expected:
            raise GeNISQ0Error(f"评价输入哈希不一致：{path}")
    return freeze


def _load_q0_labels_once(output_root: Path, freeze: Mapping[str, Any]) -> np.ndarray:
    manifest = _json(output_root / "data_manifest.json")
    label_path = Path(str(freeze["q0_eval_label_sidecar"]))
    relative = str(label_path.relative_to(output_root))
    expected = manifest.get("artifacts", {}).get(relative)
    if not isinstance(expected, str):
        raise GeNISQ0Error("Q0 标签侧车未绑定输入哈希")
    raw = label_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise GeNISQ0Error("Q0 标签侧车哈希不一致")
    labels = np.load(io.BytesIO(raw), allow_pickle=False)
    if labels.ndim != 1:
        raise GeNISQ0Error("Q0 标签侧车维度错误")
    return labels


def _metrics(
    y: np.ndarray, probability: np.ndarray, threshold: float
) -> tuple[dict[str, Any], np.ndarray, list[dict[str, Any]]]:
    from sklearn.metrics import (
        average_precision_score,
        confusion_matrix,
        log_loss,
        precision_recall_fscore_support,
    )

    prediction = probability.argmax(axis=1)
    precision, recall, f1, support = precision_recall_fscore_support(
        y, prediction, labels=np.arange(13), zero_division=0
    )
    score = _malicious_score(probability)
    binary_y = np.asarray(y >= BENIGN_CLASS_COUNT, dtype=np.uint8)
    alarm = score > threshold
    benign_count = int(np.count_nonzero(binary_y == 0))
    malicious_count = int(np.count_nonzero(binary_y == 1))
    false_positive = int(np.count_nonzero(alarm & (binary_y == 0)))
    true_positive = int(np.count_nonzero(alarm & (binary_y == 1)))
    supported = f1[np.asarray(support) >= 20]
    aggregate = {
        "recall_at_fpr_0.005": true_positive / malicious_count,
        "fpr_at_threshold": false_positive / benign_count,
        "false_alerts_per_10000_benign": false_positive * 10000.0 / benign_count,
        "macro_f1": float(np.mean(f1)),
        "macro_recall": float(np.mean(recall)),
        "min_supported_class_f1": float(np.min(supported)),
        "malicious_pr_auc": float(average_precision_score(binary_y, score)),
        "multiclass_log_loss": float(log_loss(y, probability, labels=np.arange(13))),
        "benign_rows": benign_count,
        "malicious_rows": malicious_count,
        "false_positives": false_positive,
        "true_positives": true_positive,
    }
    rows = [
        {
            "class_index": index,
            "support": int(support[index]),
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
        }
        for index in range(13)
    ]
    return aggregate, confusion_matrix(y, prediction, labels=np.arange(13)), rows


def evaluate(config_path: Path, output_override: Path | None) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = _load_config(config_path)
    output_root = _output_root(config, config_path, output_override)
    if _json(output_root / "status.json").get("state") != "SELECTION_FROZEN":
        raise GeNISQ0Error("evaluate 只接受 SELECTION_FROZEN 状态")
    freeze = _verify_freeze(config_path, output_root)
    q0_x = np.load(output_root / "data" / "q0_eval" / "features.npy", mmap_mode="r")
    # 只有以上全部冻结门禁通过后，才在此处首次连接 Q0 标签侧车。
    q0_y = _load_q0_labels_once(output_root, freeze)
    if len(q0_x) != len(q0_y) or set(np.unique(q0_y)) != set(range(13)):
        raise GeNISQ0Error("Q0 评价特征、标签或类别完整性门禁失败")
    _status(output_root, "RUNNING", "evaluate", q0_eval_labels_opened=True)
    import xgboost as xgb

    aggregate: dict[str, Any] = {}
    matrices: dict[str, Any] = {}
    per_class_rows: list[dict[str, Any]] = []
    runtime_variants: dict[str, Any] = {}
    started = time.monotonic()
    for index, variant in enumerate(VARIANTS, start=1):
        booster = xgb.Booster()
        booster.load_model(output_root / freeze["models"][variant]["model"])
        probability, predict_seconds = _predict(
            booster, q0_x, int(config["runtime"]["xgboost_threads"])
        )
        metrics, matrix, rows = _metrics(
            q0_y, probability, float(freeze["thresholds"][variant]["threshold"])
        )
        metrics["display_name"] = config["variants"][variant]
        aggregate[variant] = metrics
        matrices[variant] = matrix.tolist()
        for row in rows:
            per_class_rows.append(
                {
                    "variant": variant,
                    "display_name": config["variants"][variant],
                    "class_name": config["classes"][row["class_index"]],
                    **row,
                }
            )
        runtime_variants[variant] = {
            "train_seconds": freeze["models"][variant]["train_seconds"],
            "q0_eval_predict_seconds": predict_seconds,
            "inference_seconds_per_million_rows": predict_seconds * 1_000_000 / len(q0_y),
            "selection_cumulative_process_peak_rss_bytes": freeze["models"][variant][
                "cumulative_process_peak_rss_bytes"
            ],
            "evaluation_cumulative_process_peak_rss_bytes": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                * (1 if sys.platform == "darwin" else 1024)
            ),
        }
        _heartbeat("evaluate", index, len(VARIANTS), started)
    baseline = aggregate["B0"]
    for variant in VARIANTS:
        aggregate[variant]["delta_vs_B0"] = {
            key: aggregate[variant][key] - baseline[key]
            for key in (
                "recall_at_fpr_0.005",
                "fpr_at_threshold",
                "macro_f1",
                "macro_recall",
                "min_supported_class_f1",
                "malicious_pr_auc",
            )
        }
    gates = config["gates"]
    baseline_qualified = baseline["macro_f1"] >= gates["baseline_macro_f1_minimum"]
    near_saturation = (
        baseline["recall_at_fpr_0.005"] >= gates["near_saturation"]["recall_minimum"]
        and baseline["macro_f1"] >= gates["near_saturation"]["macro_f1_minimum"]
    )
    st = aggregate["ST"]
    promotion_gates = {
        "recall_gain_vs_B0": st["recall_at_fpr_0.005"] - baseline["recall_at_fpr_0.005"]
        >= gates["promotion"]["recall_gain_vs_B0_minimum"],
        "macro_f1_delta_vs_B0": st["macro_f1"] - baseline["macro_f1"]
        >= gates["promotion"]["macro_f1_delta_vs_B0_minimum"],
        "fpr_budget": st["fpr_at_threshold"] <= gates["promotion"]["fpr_maximum"],
        "recall_gain_vs_best_single": st["recall_at_fpr_0.005"]
        - max(aggregate["S1"]["recall_at_fpr_0.005"], aggregate["T1"]["recall_at_fpr_0.005"])
        >= gates["promotion"]["recall_gain_vs_best_single_minimum"],
    }
    single_signal = {}
    for variant in ("S1", "T1"):
        single_signal[variant] = (
            aggregate[variant]["recall_at_fpr_0.005"] - baseline["recall_at_fpr_0.005"]
            >= gates["single_mechanism"]["recall_gain_vs_B0_minimum"]
            and aggregate[variant]["macro_f1"] - baseline["macro_f1"]
            >= gates["single_mechanism"]["macro_f1_delta_vs_B0_minimum"]
            and aggregate[variant]["fpr_at_threshold"] <= gates["single_mechanism"]["fpr_maximum"]
        )
    promoted = baseline_qualified and not near_saturation and all(promotion_gates.values())
    if not baseline_qualified:
        decision = "INVALID_WEAK_BASELINE"
    elif near_saturation:
        decision = "STOP_NEAR_SATURATION"
    elif promoted:
        decision = "Q0_SUPPORTS_JOINT_CANDIDATE_PROMOTION"
    else:
        decision = "Q0_DOES_NOT_SUPPORT_JOINT_CANDIDATE_PROMOTION"
    metrics_document = {
        "schema_version": "genis-support-tail-q0-metrics-v1",
        "variants": aggregate,
        "baseline_qualified": baseline_qualified,
        "near_saturation": near_saturation,
        "promotion_gates": promotion_gates,
        "single_mechanism_signal": single_signal,
        "joint_candidate_promoted": promoted,
        "decision": decision,
        "single_seed_no_significance_claim": True,
        **config["evidence"],
    }
    _write_json(output_root / "metrics.json", metrics_document)
    _write_json(
        output_root / "confusion_matrices.json",
        {"class_order": config["classes"], "variants": matrices},
    )
    with (output_root / "per_class_metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_class_rows[0]))
        writer.writeheader()
        writer.writerows(per_class_rows)
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_bytes = int(peak_rss * (1 if sys.platform == "darwin" else 1024))
    _write_json(
        output_root / "runtime.json",
        {
            "schema_version": "genis-support-tail-q0-runtime-v1",
            "variants": runtime_variants,
            "evaluation_wall_seconds": time.monotonic() - started,
            "process_peak_rss_bytes": peak_rss_bytes,
            "prediction_interface": "Booster.predict(DMatrix)",
            "device_required": "cuda:0",
        },
    )
    _status(
        output_root,
        "FINISHED",
        "evaluate",
        q0_eval_labels_opened_after_freeze=True,
        baseline_qualified=baseline_qualified,
        near_saturation=near_saturation,
        promotion_gates=promotion_gates,
        single_mechanism_signal=single_signal,
        joint_candidate_promoted=promoted,
        decision=decision,
    )
    print(json.dumps(metrics_document, ensure_ascii=False, sort_keys=True))
    return metrics_document


def swanlab_publish(
    config_path: Path,
    output_override: Path | None,
    authorized_workspace: str,
    authorized_project: str,
) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = _load_config(config_path)
    target = config["swanlab"]
    if authorized_workspace != target["workspace"] or authorized_project != target["project"]:
        raise GeNISQ0Error("SwanLab 本轮授权目的地与冻结配置不一致")
    output_root = _output_root(config, config_path, output_override)
    status = _json(output_root / "status.json")
    if status.get("state") != "FINISHED" or status.get("final_accessed") is not False:
        raise GeNISQ0Error("SwanLab 上传前完成状态或最终测试隔离无效")
    metrics = _json(output_root / "metrics.json")
    allowed = set(target["allowed_upload_fields"])
    scalar_metrics: dict[str, float] = {}
    for variant in VARIANTS:
        for key in allowed:
            value = metrics["variants"][variant].get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                scalar_metrics[f"{variant}/{key}"] = float(value)
    try:
        import swanlab
    except ImportError as error:
        raise GeNISQ0Error("SwanLab 依赖不可用") from error
    run = swanlab.init(
        workspace=target["workspace"],
        project=target["project"],
        name=target["run_name"],
        mode=target["mode"],
        config={
            "contract_version": config["contract_version"],
            "seed": config["seed"],
            "dataset_version": config["data"]["version"],
            "feature_budget_id": config["feature_budget"]["id"],
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        },
    )
    swanlab.log(scalar_metrics)
    run.finish()
    receipt = {
        "schema_version": "genis-support-tail-q0-swanlab-receipt-v1",
        "workspace": target["workspace"],
        "project": target["project"],
        "run_name": target["run_name"],
        "uploaded_keys": sorted(scalar_metrics),
        "upload_policy": "aggregate_metrics_and_protocol_metadata_only",
        **config["evidence"],
    }
    _write_json(output_root / "swanlab_publish_receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare", help="流式物化冻结开发三分区")
    prepare_parser.add_argument("--config", type=Path, required=True)
    prepare_parser.add_argument("--output-root", type=Path)
    prepare_parser.add_argument(
        "--archive-path",
        type=Path,
        help="只覆盖 prepare 实际读取的归档路径，归档与成员摘要仍按配置校验",
    )
    for command, help_text in (
        ("select", "冻结强基线、交叉拟合权重、四格模型和阈值"),
        ("evaluate", "冻结一致后一次连接 Q0 标签并机械裁决"),
    ):
        child = subparsers.add_parser(command, help=help_text)
        child.add_argument("--config", type=Path, required=True)
        child.add_argument("--output-root", type=Path)
    publish = subparsers.add_parser("swanlab-publish", help="仅上传聚合指标与协议元数据")
    publish.add_argument("--config", type=Path, required=True)
    publish.add_argument("--output-root", type=Path)
    publish.add_argument("--authorized-workspace", required=True)
    publish.add_argument("--authorized-project", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "prepare":
            prepare(args.config, args.output_root, args.archive_path)
        elif args.command == "select":
            select(args.config, args.output_root)
        elif args.command == "evaluate":
            evaluate(args.config, args.output_root)
        elif args.command == "swanlab-publish":
            swanlab_publish(
                args.config,
                args.output_root,
                args.authorized_workspace,
                args.authorized_project,
            )
        else:
            raise GeNISQ0Error(f"未知命令：{args.command}")
    except GeNISQ0Error as error:
        try:
            config = _load_config(args.config)
            output_root = _output_root(config, args.config, args.output_root)
            if output_root.is_dir():
                _status(
                    output_root,
                    "FAILED",
                    args.command,
                    failure_type=type(error).__name__,
                    failure=str(error),
                )
        except (GeNISQ0Error, OSError, AttributeError):
            pass
        print(f"GeNIS Q0 失败：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
