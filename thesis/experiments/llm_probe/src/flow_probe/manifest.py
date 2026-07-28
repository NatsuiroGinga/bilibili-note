"""数据来源、字段和划分的机器可读清单。"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path

from flow_probe.schemas import CANONICAL_CORE_FIELDS, FlowSample


class ManifestError(ValueError):
    """数据清单缺少复现实验所需信息。"""


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    samples: Sequence[FlowSample],
    source_paths: Sequence[Path],
    split_summary: Mapping[str, object],
) -> dict[str, object]:
    """生成包含哈希、分布、缺失率和证据等级的数据清单。"""
    for field in ("group_basis", "evidence_level"):
        if not str(split_summary.get(field, "")).strip():
            raise ManifestError(f"split_summary 缺少 {field}")
    if not samples:
        raise ManifestError("数据清单不能基于空样本集")

    sample_ids = [sample.sample_id for sample in samples]
    if len(sample_ids) != len(set(sample_ids)):
        raise ManifestError("样本标识重复")

    sources = []
    for path in sorted((Path(path) for path in source_paths), key=lambda item: str(item)):
        if not path.is_file():
            raise ManifestError(f"来源文件不存在：{path}")
        sources.append(
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": _file_sha256(path),
            }
        )

    missing_rate = {
        field: sum(sample.features[field] is None for sample in samples) / len(samples)
        for field in CANONICAL_CORE_FIELDS
    }
    return {
        "schema_version": "flow_probe_manifest_v1",
        "sample_count": len(samples),
        "source_datasets": sorted({sample.source_dataset for sample in samples}),
        "feature_views": sorted({sample.feature_view for sample in samples}),
        "label_distribution": dict(
            sorted(Counter(sample.binary_label for sample in samples).items())
        ),
        "field_missing_rate": missing_rate,
        "sources": sources,
        "split_summary": dict(split_summary),
    }
