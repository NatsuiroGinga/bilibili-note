"""从分组切分结果中生成固定预算的平衡实验子集。"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path

SPLITS = ("train", "validation", "test")
LABELS = ("benign", "malicious")
REQUIRED_FIELDS = ("sample_id", "group_id", "binary_label", "prompt", "completion")


class SamplingError(ValueError):
    """采样输入无法满足平衡、无放回或无泄漏要求。"""


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise SamplingError(f"切分文件不存在：{path}")
    records = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise SamplingError(f"JSONL 行必须是对象：{path}:{line_number}")
            missing = [field for field in REQUIRED_FIELDS if field not in value]
            if missing:
                raise SamplingError(f"采样记录缺少字段：{path}:{line_number} {missing}")
            if value["binary_label"] not in LABELS:
                raise SamplingError(f"未知二分类标签：{path}:{line_number} {value['binary_label']}")
            records.append(value)
    if not records:
        raise SamplingError(f"切分文件不能为空：{path}")
    return records


def _assert_disjoint(records_by_split: Mapping[str, Sequence[Mapping[str, object]]]) -> None:
    sample_owners: dict[str, str] = {}
    group_owners: dict[str, str] = {}
    for split in SPLITS:
        for record in records_by_split[split]:
            sample_id = str(record["sample_id"])
            group_id = str(record["group_id"])
            previous_sample = sample_owners.setdefault(sample_id, split)
            if previous_sample != split:
                raise SamplingError(f"样本标识跨切分重复：{sample_id}")
            previous_group = group_owners.setdefault(group_id, split)
            if previous_group != split:
                raise SamplingError(f"分组交叉：{group_id} 同时位于多个切分")


def _sample_balanced(
    records: Sequence[dict[str, object]], target: int, seed: int
) -> list[dict[str, object]]:
    if target <= 0 or target % 2 != 0:
        raise SamplingError("平衡采样目标必须是大于 0 的偶数")
    per_label = target // 2
    selected: list[dict[str, object]] = []
    randomizer = random.Random(seed)
    for label in LABELS:
        candidates = sorted(
            (record for record in records if record["binary_label"] == label),
            key=lambda record: str(record["sample_id"]),
        )
        if len(candidates) < per_label:
            raise SamplingError(f"{label} 样本不足：需要 {per_label}，实际 {len(candidates)}")
        selected.extend(randomizer.sample(candidates, per_label))
    return sorted(selected, key=lambda record: str(record["sample_id"]))


def _write_jsonl(path: Path, records: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def sample_prepared_splits(
    source_dir: Path,
    output_dir: Path,
    targets: Mapping[str, int],
    seed: int,
) -> dict[str, object]:
    """按切分和类别无放回采样，并保存机器可读清单。"""
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)
    if set(targets) != set(SPLITS):
        raise SamplingError(f"采样目标必须包含且仅包含：{SPLITS}")

    source_paths = {split: source_dir / f"{split}.jsonl" for split in SPLITS}
    records_by_split = {split: _read_jsonl(source_paths[split]) for split in SPLITS}
    _assert_disjoint(records_by_split)

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_splits: dict[str, object] = {}
    for index, split in enumerate(SPLITS):
        target = int(targets[split])
        selected = _sample_balanced(records_by_split[split], target, seed + index)
        _write_jsonl(output_dir / f"{split}.jsonl", selected)
        manifest_splits[split] = {
            "target": target,
            "actual": len(selected),
            "label_distribution": dict(
                sorted(Counter(str(record["binary_label"]) for record in selected).items())
            ),
            "source_path": str(source_paths[split]),
            "source_sha256": _file_sha256(source_paths[split]),
        }

    manifest = {
        "schema_version": "flow_probe_sample_manifest_v1",
        "seed": seed,
        "sampling": "balanced_without_replacement_after_grouped_split",
        "splits": manifest_splits,
    }
    (output_dir / "sample_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成固定预算的平衡探针子集")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--train-size", type=int, required=True)
    parser.add_argument("--validation-size", type=int, required=True)
    parser.add_argument("--test-size", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = sample_prepared_splits(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        targets={
            "train": args.train_size,
            "validation": args.validation_size,
            "test": args.test_size,
        },
        seed=args.seed,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
