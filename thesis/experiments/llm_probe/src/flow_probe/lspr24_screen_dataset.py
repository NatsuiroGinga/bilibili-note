"""LSPR24 筛选宽表的统一消费端加载器。"""

from __future__ import annotations

import hashlib
import heapq
import json
import os
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow.dataset as pds


SCREEN_CONTRACT_VERSION = "lspr24-screen-6-2-2-v1"
SEQUENCE_CACHE_VERSION = "lspr24-rwkv-screen-cache-v1"
ALLOWED_SPLITS = frozenset(("train", "validation"))
ALLOWED_HISTORY_LENGTHS = frozenset((1, 4, 16, 32))
REQUIRED_ARTIFACTS = frozenset(("wide_table", "labels", "field_manifest", "temporal_relations"))
FORBIDDEN_FEATURES = frozenset(
    (
        "window_row_index",
        "window_start_ns",
        "window_end_ns",
        "protected_endpoint_sha256",
        "split_name",
        "label",
    )
)
SCAN_BATCH_SIZE = 65_536


class Lspr24ScreenDatasetError(ValueError):
    """数据清单、字段或历史关系不满足筛选合同。"""


@dataclass(frozen=True)
class Lspr24ScreenBatch:
    """一个任务投影、历史长度和切分对应的模型输入。"""

    sample_ids: tuple[str, ...]
    features: np.ndarray
    labels: np.ndarray
    feature_columns: tuple[str, ...]
    split_name: str
    history_length: int
    task: str


@dataclass(frozen=True)
class _SelectedTarget:
    target: int
    label: int
    history: tuple[int, ...]


def _read_json(path: Path, description: str) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Lspr24ScreenDatasetError(f"无法读取{description}：{path}") from error
    if not isinstance(value, Mapping):
        raise Lspr24ScreenDatasetError(f"{description}顶层必须是对象")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _experiment_root(manifest_path: Path) -> Path:
    for candidate in manifest_path.parents:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src" / "flow_probe").is_dir():
            return candidate
    raise Lspr24ScreenDatasetError(f"无法确定实验工程根目录：{manifest_path}")


def _checked_project_path(path: Path, project_root: Path, description: str) -> Path:
    if not path.is_absolute():
        raise Lspr24ScreenDatasetError(f"{description}必须为绝对路径：{path}")
    resolved = path.resolve()
    try:
        relative_path = resolved.relative_to(project_root)
    except ValueError as error:
        raise Lspr24ScreenDatasetError(f"{description}越出开发实验工程：{resolved}") from error
    if "final" in relative_path.parts:
        raise Lspr24ScreenDatasetError(f"{description}不得指向最终切分：{resolved}")
    return resolved


def _artifact_path(
    manifest_path: Path,
    project_root: Path,
    artifacts: Mapping[str, object],
    name: str,
) -> Path:
    entry = artifacts.get(name)
    if not isinstance(entry, Mapping):
        raise Lspr24ScreenDatasetError(f"清单缺少制品登记：{name}")
    raw_path = str(entry.get("path", "")).strip()
    if not raw_path:
        raise Lspr24ScreenDatasetError(f"制品 {name} 缺少路径")
    path = _checked_project_path(Path(raw_path), project_root, f"登记制品路径 {name}")
    if not path.is_file():
        raise Lspr24ScreenDatasetError(f"登记制品不存在：{name}={path}")
    return path


def _iter_parquet_rows(
    path: Path,
    columns: Sequence[str],
    *,
    filter_expression: pds.Expression | None = None,
) -> Iterator[tuple[object, ...]]:
    scanner = pds.dataset(path, format="parquet").scanner(
        columns=list(columns),
        filter=filter_expression,
        batch_size=SCAN_BATCH_SIZE,
        use_threads=False,
    )
    for batch in scanner.to_batches():
        values = batch.to_pydict()
        for row_index in range(batch.num_rows):
            yield tuple(values[column][row_index] for column in columns)


def _iter_sorted_unique_rows(
    path: Path,
    columns: Sequence[str],
    description: str,
) -> Iterator[tuple[object, ...]]:
    previous: int | None = None
    for row in _iter_parquet_rows(path, columns):
        key = int(row[0])
        if previous is not None and key <= previous:
            reason = "重复" if key == previous else "未按主键递增"
            raise Lspr24ScreenDatasetError(f"{description}主键{reason}：{key}")
        previous = key
        yield row


def _iter_relation_groups(
    path: Path,
    history_length: int,
) -> Iterator[tuple[int, tuple[int, ...]]]:
    columns = ("target_window_row_index", "lag", "history_window_row_index")
    expression = pds.field("horizon") == history_length
    current_target: int | None = None
    previous_target: int | None = None
    lags: dict[int, int] = {}
    invalid = False
    for raw_target, raw_lag, raw_history in _iter_parquet_rows(
        path,
        columns,
        filter_expression=expression,
    ):
        target = int(raw_target)
        lag = int(raw_lag)
        history = int(raw_history)
        if previous_target is not None and target < previous_target:
            raise Lspr24ScreenDatasetError("历史关系目标主键未按递增顺序排列")
        previous_target = target
        if current_target is not None and target != current_target:
            if not invalid and set(lags) == set(range(1, history_length + 1)):
                yield current_target, tuple(lags[value] for value in range(history_length, 0, -1))
            lags = {}
            invalid = False
        current_target = target
        if lag in lags or lag < 1 or lag > history_length or len(lags) >= history_length:
            invalid = True
        else:
            lags[lag] = history
    if current_target is not None and not invalid and set(lags) == set(range(1, history_length + 1)):
        yield current_target, tuple(lags[value] for value in range(history_length, 0, -1))


def _advance_to(
    iterator: Iterator[tuple[object, ...]],
    current: tuple[object, ...] | None,
    target: int,
) -> tuple[object, ...] | None:
    while current is not None and int(current[0]) < target:
        current = next(iterator, None)
    return current


def _write_npy(path: Path, value: np.ndarray) -> None:
    with path.open("wb") as handle:
        np.save(handle, value, allow_pickle=False)


def _fixed_string_array(values: tuple[str, ...]) -> np.ndarray:
    width = max((len(value) for value in values), default=1)
    return np.asarray(values, dtype=f"<U{width}")


class Lspr24ScreenDataset:
    """只通过 ``dataset-manifest.json`` 发现筛选宽表全部制品。"""

    def __init__(self, manifest_path: Path) -> None:
        self.manifest_path = Path(manifest_path).resolve()
        if self.manifest_path.name != "dataset-manifest.json":
            raise Lspr24ScreenDatasetError("统一加载器只接受 dataset-manifest.json")
        self.project_root = _experiment_root(self.manifest_path)
        manifest = _read_json(self.manifest_path, "数据清单")
        if manifest.get("contract_version") != SCREEN_CONTRACT_VERSION:
            raise Lspr24ScreenDatasetError("数据清单筛选合同版本不匹配")
        if manifest.get("training_split") != "train" or manifest.get("validation_split") != "validation":
            raise Lspr24ScreenDatasetError("数据清单必须登记 train/validation 切分")
        if not str(manifest.get("final_split", "")).startswith("final"):
            raise Lspr24ScreenDatasetError("数据清单必须显式保留最终切分名称")
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, Mapping):
            raise Lspr24ScreenDatasetError("数据清单 artifacts 必须是对象")
        missing = REQUIRED_ARTIFACTS.difference(artifacts)
        if missing:
            raise Lspr24ScreenDatasetError(f"数据清单缺少必要制品：{', '.join(sorted(missing))}")
        self.manifest = manifest
        self.wide_path = _artifact_path(self.manifest_path, self.project_root, artifacts, "wide_table")
        self.labels_path = _artifact_path(self.manifest_path, self.project_root, artifacts, "labels")
        self.field_manifest_path = _artifact_path(
            self.manifest_path, self.project_root, artifacts, "field_manifest"
        )
        self.history_path = _artifact_path(
            self.manifest_path, self.project_root, artifacts, "temporal_relations"
        )
        self.allowed_fields, self.field_groups = self._load_field_manifest()
        registered_fields = manifest.get("model_feature_columns")
        if not isinstance(registered_fields, list) or tuple(registered_fields) != self.allowed_fields:
            raise Lspr24ScreenDatasetError("数据清单模型字段与字段清单不一致")

    def _load_field_manifest(self) -> tuple[tuple[str, ...], Mapping[str, tuple[str, ...]]]:
        document = _read_json(self.field_manifest_path, "字段清单")
        entries = document.get("entries")
        if not isinstance(entries, list) or not entries:
            raise Lspr24ScreenDatasetError("字段清单 entries 必须为非空数组")
        fields: list[str] = []
        groups: dict[str, list[str]] = {}
        for index, raw_entry in enumerate(entries):
            if not isinstance(raw_entry, Mapping):
                raise Lspr24ScreenDatasetError(f"字段清单 entries[{index}] 必须是对象")
            name = str(raw_entry.get("output_name", "")).strip()
            group = str(raw_entry.get("semantic_group", "")).strip()
            allowed_models = raw_entry.get("allowed_models")
            if not name or name in FORBIDDEN_FEATURES:
                raise Lspr24ScreenDatasetError(f"字段清单包含禁入字段：{name or index}")
            if not isinstance(allowed_models, list) or not allowed_models:
                raise Lspr24ScreenDatasetError(f"字段 {name} 未登记允许消费模型")
            if name in fields:
                raise Lspr24ScreenDatasetError(f"字段清单 output_name 重复：{name}")
            fields.append(name)
            groups.setdefault(group, []).append(name)
        return tuple(fields), {key: tuple(value) for key, value in groups.items()}

    def select_fields(
        self,
        *,
        field_names: Sequence[str] | None = None,
        field_groups: Sequence[str] | None = None,
    ) -> tuple[str, ...]:
        if field_names is None and field_groups is None:
            return self.allowed_fields
        selected: list[str] = []
        if field_groups is not None:
            for group in field_groups:
                name = str(group).strip()
                if name not in self.field_groups:
                    raise Lspr24ScreenDatasetError(f"未知字段组：{name}")
                selected.extend(self.field_groups[name])
        if field_names is not None:
            selected.extend(str(field).strip() for field in field_names)
        selected = list(dict.fromkeys(selected))
        unknown = sorted(set(selected).difference(self.allowed_fields))
        if not selected or unknown:
            raise Lspr24ScreenDatasetError(f"字段选择不合法：{', '.join(unknown) or '空选择'}")
        return tuple(selected)

    def _select_targets(
        self,
        split_name: str,
        history_length: int,
        sample_limit: int,
    ) -> tuple[_SelectedTarget, ...]:
        wide_rows = _iter_sorted_unique_rows(
            self.wide_path,
            ("window_row_index", "split_name"),
            "宽表",
        )
        label_rows = _iter_sorted_unique_rows(
            self.labels_path,
            ("window_row_index", "label"),
            "标签旁车",
        )
        current_wide = next(wide_rows, None)
        current_label = next(label_rows, None)
        selected: list[tuple[int, int, _SelectedTarget]] = []
        relation_count = 0
        for target, history in _iter_relation_groups(self.history_path, history_length):
            relation_count += 1
            current_wide = _advance_to(wide_rows, current_wide, target)
            current_label = _advance_to(label_rows, current_label, target)
            if (
                current_wide is None
                or int(current_wide[0]) != target
                or str(current_wide[1]) != split_name
                or current_label is None
                or int(current_label[0]) != target
            ):
                continue
            digest = int.from_bytes(hashlib.sha256(str(target).encode("utf-8")).digest(), "big")
            item = _SelectedTarget(
                target=target,
                label=int(int(current_label[1]) != 0),
                history=history,
            )
            heap_item = (-digest, -target, item)
            if len(selected) < sample_limit:
                heapq.heappush(selected, heap_item)
            elif heap_item > selected[0]:
                heapq.heapreplace(selected, heap_item)
        if relation_count == 0:
            raise Lspr24ScreenDatasetError(f"历史关系表没有 H={history_length}")
        for _ in wide_rows:
            pass
        for _ in label_rows:
            pass
        if not selected:
            raise Lspr24ScreenDatasetError("同切分内没有完整历史的目标窗口")
        return tuple(sorted((entry[2] for entry in selected), key=lambda item: item.target))

    def _load_features(
        self,
        selected: Sequence[_SelectedTarget],
        fields: tuple[str, ...],
        history_length: int,
    ) -> np.ndarray:
        field_count = len(fields)
        features = np.empty(
            (len(selected), (history_length + 1) * field_count),
            dtype=np.float64,
        )
        destinations: dict[int, list[tuple[int, int]]] = {}
        for sample_index, item in enumerate(selected):
            for time_index, window_index in enumerate((*item.history, item.target)):
                destinations.setdefault(window_index, []).append((sample_index, time_index))
        needed_ids = sorted(destinations)
        expression = pds.field("window_row_index").isin(needed_ids)
        columns = ("window_row_index", *fields)
        scanner = pds.dataset(self.wide_path, format="parquet").scanner(
            columns=list(columns),
            filter=expression,
            batch_size=SCAN_BATCH_SIZE,
            use_threads=False,
        )
        filled: set[int] = set()
        for batch in scanner.to_batches():
            identifiers = batch.column(0).to_numpy(zero_copy_only=False)
            values = np.column_stack(
                [batch.column(index).to_numpy(zero_copy_only=False) for index in range(1, len(columns))]
            ).astype(np.float64, copy=False)
            for batch_index, raw_identifier in enumerate(identifiers):
                identifier = int(raw_identifier)
                if identifier in filled:
                    raise Lspr24ScreenDatasetError(f"宽表命中主键重复：{identifier}")
                positions = destinations.pop(identifier, None)
                if positions is None:
                    continue
                for sample_index, time_index in positions:
                    start = time_index * field_count
                    features[sample_index, start : start + field_count] = values[batch_index]
                filled.add(identifier)
        if destinations:
            first_missing = min(destinations)
            raise Lspr24ScreenDatasetError(f"历史关系引用的宽表窗口不存在：{first_missing}")
        return features

    def load(
        self,
        *,
        split_name: str,
        history_length: int,
        task: str = "binary_detection",
        field_names: Sequence[str] | None = None,
        field_groups: Sequence[str] | None = None,
        sample_limit: int | None = None,
    ) -> Lspr24ScreenBatch:
        """按主键流式稳定选样，再只读取目标窗口及其历史。"""
        if split_name not in ALLOWED_SPLITS:
            raise Lspr24ScreenDatasetError("加载器只允许 train 或 validation，最终测试不可见")
        if history_length not in ALLOWED_HISTORY_LENGTHS:
            raise Lspr24ScreenDatasetError(f"不支持的历史长度：{history_length}")
        if task != "binary_detection":
            raise Lspr24ScreenDatasetError(f"当前表格基线不支持任务投影：{task}")
        if sample_limit is None or sample_limit <= 0:
            raise Lspr24ScreenDatasetError("有界加载必须提供正整数样本上限")
        fields = self.select_fields(field_names=field_names, field_groups=field_groups)
        selected = self._select_targets(split_name, history_length, sample_limit)
        features = self._load_features(selected, fields, history_length)
        feature_columns = tuple(
            [f"lag{lag}_{field}" for lag in range(history_length, 0, -1) for field in fields]
            + [f"current_{field}" for field in fields]
        )
        return Lspr24ScreenBatch(
            sample_ids=tuple(str(item.target) for item in selected),
            features=features,
            labels=np.asarray([item.label for item in selected], dtype=np.int64),
            feature_columns=feature_columns,
            split_name=split_name,
            history_length=history_length,
            task=task,
        )

    def prepare_sequence_cache(
        self,
        *,
        cache_dir: Path,
        history_length: int = 4,
        train_limit: int = 100_000,
        validation_limit: int = 20_000,
        seed: int = 42,
    ) -> Mapping[str, object]:
        """生成基线和隔离训练进程可共同内存映射的只读数组。"""
        cache_dir = _checked_project_path(Path(cache_dir), self.project_root, "共享缓存目录")
        if cache_dir.exists():
            raise Lspr24ScreenDatasetError(f"共享缓存目录已存在，不得复用：{cache_dir}")
        if history_length != 4:
            raise Lspr24ScreenDatasetError("四进程共享序列缓存固定使用 H=4")
        if train_limit <= 0 or validation_limit <= 0:
            raise Lspr24ScreenDatasetError("训练与验证样本上限必须为正整数")
        staging = cache_dir.with_name(cache_dir.name + f".partial.{os.getpid()}")
        if staging.exists():
            raise Lspr24ScreenDatasetError(f"共享缓存暂存目录已存在：{staging}")
        staging.parent.mkdir(parents=True, exist_ok=True)
        staging.mkdir()
        started = time.perf_counter()

        train = self.load(
            split_name="train",
            history_length=history_length,
            sample_limit=train_limit,
        )
        validation = self.load(
            split_name="validation",
            history_length=history_length,
            sample_limit=validation_limit,
        )
        field_count = len(self.allowed_fields)
        train_raw = train.features.reshape(len(train.labels), history_length + 1, field_count)
        validation_raw = validation.features.reshape(
            len(validation.labels), history_length + 1, field_count
        )
        flattened = train_raw.reshape(-1, field_count)
        replacement = np.empty(field_count, dtype=np.float64)
        for index in range(field_count):
            finite = flattened[np.isfinite(flattened[:, index]), index]
            if finite.size == 0:
                raise Lspr24ScreenDatasetError(f"训练字段 {index} 没有有限值")
            replacement[index] = float(np.median(finite))
        filled_train = np.where(np.isfinite(flattened), flattened, replacement)
        mean = filled_train.mean(axis=0, dtype=np.float64)
        std = filled_train.std(axis=0, dtype=np.float64)
        std = np.where(np.isfinite(std) & (std >= 1e-6), std, 1.0)
        del filled_train, flattened

        def normalize(sequence: np.ndarray) -> np.ndarray:
            filled = np.where(np.isfinite(sequence), sequence, replacement)
            normalized = np.clip((filled - mean) / std, -10.0, 10.0).astype(
                np.float32,
                copy=False,
            )
            if not np.isfinite(normalized).all():
                raise Lspr24ScreenDatasetError("标准化后仍包含非有限值")
            return normalized

        group_names = tuple(self.field_groups)
        group_by_field = {
            field: group_index
            for group_index, group_name in enumerate(group_names)
            for field in self.field_groups[group_name]
        }
        try:
            group_ids = tuple(group_by_field[field] for field in self.allowed_fields)
        except KeyError as error:
            raise Lspr24ScreenDatasetError(f"字段缺少语义组：{error.args[0]}") from error
        from flow_probe.lspr24_rwkv_screen_models import ScreenModelConfig, parameter_budget

        model_config = ScreenModelConfig()
        parameter_counts = parameter_budget(field_count, group_ids, model_config)
        arrays = {
            "train_sequence.npy": normalize(train_raw),
            "train_labels.npy": train.labels.astype(np.int64, copy=False),
            "train_sample_ids.npy": _fixed_string_array(train.sample_ids),
            "validation_sequence.npy": normalize(validation_raw),
            "validation_labels.npy": validation.labels.astype(np.int64, copy=False),
            "validation_sample_ids.npy": _fixed_string_array(validation.sample_ids),
            "normalizer_replacement.npy": replacement,
            "normalizer_mean.npy": mean,
            "normalizer_std.npy": std,
        }
        for file_name, value in arrays.items():
            _write_npy(staging / file_name, value)
        manifest_hash = _sha256(self.manifest_path)
        metadata: dict[str, object] = {
            "schema_version": SEQUENCE_CACHE_VERSION,
            "dataset_manifest": str(self.manifest_path),
            "dataset_manifest_sha256": manifest_hash,
            "history_length": history_length,
            "time_steps": history_length + 1,
            "seed": seed,
            "train_limit": train_limit,
            "validation_limit": validation_limit,
            "train_sample_count": len(train.labels),
            "validation_sample_count": len(validation.labels),
            "feature_count": field_count,
            "feature_names": list(self.allowed_fields),
            "flattened_feature_columns": list(train.feature_columns),
            "field_group_names": list(group_names),
            "field_group_ids": list(group_ids),
            "model_config": model_config.to_dict(),
            "parameter_counts": parameter_counts,
            "parameter_ratio": max(parameter_counts.values()) / min(parameter_counts.values()),
            "normalizer": {
                "source_split": "train",
                "non_finite_replacement": "per-field-train-median",
                "clip_range": [-10.0, 10.0],
                "median_file": "normalizer_replacement.npy",
                "mean_file": "normalizer_mean.npy",
                "std_file": "normalizer_std.npy",
            },
            "array_files": {
                file_name: {
                    "shape": list(value.shape),
                    "dtype": str(value.dtype),
                    "sha256": _sha256(staging / file_name),
                }
                for file_name, value in arrays.items()
            },
            "cache_manifest": str(cache_dir / "cache-manifest.json"),
            "preparation_seconds": time.perf_counter() - started,
            "immutable_read_only": True,
            "labels_separate_from_features": True,
        }
        manifest_path = staging / "cache-manifest.json"
        manifest_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        cache_manifest_sha256 = _sha256(manifest_path)
        os.replace(staging, cache_dir)
        for path in cache_dir.iterdir():
            path.chmod(0o444)
        cache_dir.chmod(0o555)
        return {**metadata, "cache_manifest_sha256": cache_manifest_sha256}
