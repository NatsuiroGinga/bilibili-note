"""E2 困难域共同预算的冻结开发数据视图。"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

E2_FEATURE_FIELDS = (
    "duration",
    "orig_bytes",
    "resp_bytes",
    "orig_pkts",
    "resp_pkts",
    "orig_ip_bytes",
    "resp_ip_bytes",
)

_REQUIRED_MANIFESTS = (
    ("train.jsonl", "train", None),
    ("calibration.jsonl", "calibration", None),
    ("validation_A.jsonl", "validation", "A"),
    ("validation_B.jsonl", "validation", "B"),
    ("validation_C.jsonl", "validation", "C"),
    ("validation_D.jsonl", "validation", "D"),
)
_SAMPLE_COLUMNS = (
    "sample_id",
    "capture_id",
    "profile",
    "development_split",
    "binary_label",
    *E2_FEATURE_FIELDS,
)
_BINARY_LABEL_TO_ID = {"non_c2": 0, "malicious_c2": 1}
_PANELS = {"abd_to_c": ("A", "B", "D"), "ab_to_c": ("A", "B")}


class E2HardDomainDataError(ValueError):
    """E2 冻结数据合同不满足时抛出。"""


@dataclass(frozen=True)
class E2Sample:
    """一条 E2 样本；模型只能消费 features 中的共同七字段。"""

    sample_id: str
    capture_id: str
    profile: str
    split_id: str
    label: int
    features: tuple[float, ...]
    stable_order: int


@dataclass(frozen=True)
class E2Panel:
    """一个固定困难域面板的源域训练、校准与 C 域目标记录。"""

    panel: str
    train: tuple[E2Sample, ...]
    calibration: tuple[E2Sample, ...]
    target: tuple[E2Sample, ...]


def _validate_feature_fields(feature_fields: Sequence[str]) -> None:
    if tuple(feature_fields) != E2_FEATURE_FIELDS:
        raise E2HardDomainDataError("模型输入必须精确使用共同七字段，禁止未知字段")


def _read_manifest(path: Path, expected_split: str, expected_profile: str | None) -> list[str]:
    if not path.is_file():
        raise E2HardDomainDataError(f"缺少 E1 冻结开发清单：{path.name}")
    sample_ids: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise E2HardDomainDataError(f"清单包含空行：{path.name}:{line_number}")
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise E2HardDomainDataError(f"清单不是合法 JSON：{path.name}:{line_number}") from error
        if not isinstance(record, dict):
            raise E2HardDomainDataError(f"清单记录必须是对象：{path.name}:{line_number}")
        sample_id = record.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id:
            raise E2HardDomainDataError(f"清单缺少 sample_id：{path.name}:{line_number}")
        if record.get("split_id") != expected_split:
            raise E2HardDomainDataError(f"清单 split_id 不匹配：{path.name}:{line_number}")
        profile = record.get("profile")
        if expected_profile is not None and profile not in (None, expected_profile):
            raise E2HardDomainDataError(f"清单 profile 不匹配：{path.name}:{line_number}")
        sample_ids.append(sample_id)
    if not sample_ids or len(sample_ids) != len(set(sample_ids)):
        raise E2HardDomainDataError(f"清单样本为空或重复：{path.name}")
    return sample_ids


def _reject_forbidden_manifests(splits_dir: Path) -> None:
    if not splits_dir.is_dir():
        raise E2HardDomainDataError("缺少 E1 冻结开发 splits 目录")
    forbidden = [
        path.name
        for path in splits_dir.glob("*.jsonl")
        if "test" in path.stem.lower() or "unassigned" in path.stem.lower()
    ]
    if forbidden:
        raise E2HardDomainDataError(f"E2 禁止读取最终测试或未分配组清单：{sorted(forbidden)}")


def load_e2_development_view(
    protocol_dir: Path,
    *,
    feature_fields: Sequence[str] = E2_FEATURE_FIELDS,
) -> tuple[E2Sample, ...]:
    """从 E1 冻结开发制品构建稳定顺序的 E2 样本，不重新拆分。"""
    _validate_feature_fields(feature_fields)
    root = Path(protocol_dir)
    splits_dir = root / "splits"
    _reject_forbidden_manifests(splits_dir)
    manifest_ids: list[tuple[str, str, str | None, str]] = []
    for name, expected_split, expected_profile in _REQUIRED_MANIFESTS:
        for sample_id in _read_manifest(splits_dir / name, expected_split, expected_profile):
            manifest_ids.append((sample_id, expected_split, expected_profile, name))
    ordered_ids = [sample_id for sample_id, _, _, _ in manifest_ids]
    if len(ordered_ids) != len(set(ordered_ids)):
        raise E2HardDomainDataError("E1 开发清单之间存在重复 sample_id")

    samples_path = root / "samples.parquet"
    if not samples_path.is_file():
        raise E2HardDomainDataError("缺少 E1 冻结 samples.parquet")
    try:
        frame = pd.read_parquet(samples_path, columns=list(_SAMPLE_COLUMNS))
    except (KeyError, ValueError) as error:
        raise E2HardDomainDataError("E1 样本缺少 E2 所需字段") from error
    if frame["sample_id"].duplicated().any():
        raise E2HardDomainDataError("E1 样本存在重复 sample_id")
    frame["sample_id"] = frame["sample_id"].astype(str)
    indexed = frame.set_index("sample_id", drop=False)
    missing = [sample_id for sample_id in ordered_ids if sample_id not in indexed.index]
    extra = sorted(set(indexed.index).difference(ordered_ids))
    if missing or extra:
        raise E2HardDomainDataError("E1 视图含未分配组或清单与样本不一致")

    samples: list[E2Sample] = []
    for stable_order, (sample_id, expected_split, expected_profile, manifest_name) in enumerate(
        manifest_ids
    ):
        row = indexed.loc[sample_id]
        profile = str(row["profile"])
        if profile not in {"A", "B", "C", "D"}:
            raise E2HardDomainDataError(f"样本 profile 非 E1 开发域：{sample_id}")
        if expected_profile is not None and profile != expected_profile:
            raise E2HardDomainDataError(f"验证清单与样本 profile 不一致：{manifest_name}:{sample_id}")
        if str(row["development_split"]) != expected_split:
            raise E2HardDomainDataError(
                f"验证清单与样本 development_split 不一致：{manifest_name}:{sample_id}"
            )
        try:
            label = _BINARY_LABEL_TO_ID[row["binary_label"]]
        except (KeyError, TypeError) as error:
            raise E2HardDomainDataError(f"样本标签非法：{sample_id}") from error
        features = tuple(float(row[field]) for field in E2_FEATURE_FIELDS)
        if not all(math.isfinite(value) for value in features):
            raise E2HardDomainDataError(f"样本七字段含非有限值：{sample_id}")
        capture_id = str(row["capture_id"])
        if not capture_id:
            raise E2HardDomainDataError(f"样本缺少 capture_id：{sample_id}")
        samples.append(
            E2Sample(
                sample_id=sample_id,
                capture_id=capture_id,
                profile=profile,
                split_id=expected_split,
                label=label,
                features=features,
                stable_order=stable_order,
            )
        )
    return tuple(samples)


def build_e2_panel(samples: Sequence[E2Sample], *, panel: str) -> E2Panel:
    """按冻结 profile 分组建立 A+B+D→C 或 A+B→C 面板。"""
    source_profiles = _PANELS.get(panel)
    if source_profiles is None:
        raise E2HardDomainDataError("E2 面板只允许 abd_to_c 或 ab_to_c")
    ordered = tuple(sorted(samples, key=lambda sample: sample.stable_order))
    sample_ids = [sample.sample_id for sample in ordered]
    if not ordered or len(sample_ids) != len(set(sample_ids)):
        raise E2HardDomainDataError("E2 面板样本为空或重复")
    train = tuple(
        sample
        for sample in ordered
        if sample.split_id == "train" and sample.profile in source_profiles
    )
    calibration = tuple(
        sample
        for sample in ordered
        if sample.split_id == "calibration" and sample.profile in source_profiles
    )
    target = tuple(
        sample for sample in ordered if sample.split_id == "validation" and sample.profile == "C"
    )
    if not train or not target:
        raise E2HardDomainDataError("E2 面板训练集或 C 困难域目标集为空")
    source_ids = {sample.sample_id for sample in (*train, *calibration)}
    target_ids = {sample.sample_id for sample in target}
    if source_ids.intersection(target_ids):
        raise E2HardDomainDataError("E2 源域与 C 困难域目标样本不互斥")
    return E2Panel(panel=panel, train=train, calibration=calibration, target=target)


def samples_to_model_matrix(samples: Sequence[E2Sample]) -> np.ndarray:
    """唯一允许进入模型的矩阵，列顺序固定为 E2 共同七字段。"""
    matrix = np.asarray([sample.features for sample in samples], dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1:] != (len(E2_FEATURE_FIELDS),):
        raise E2HardDomainDataError("模型矩阵必须是非空的七字段二维矩阵")
    return matrix
