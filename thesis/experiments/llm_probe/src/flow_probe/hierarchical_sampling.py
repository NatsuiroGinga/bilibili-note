"""生成 GeNIS 分层多分类与未知攻击固定实验集。"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path

from flow_probe.serialize import serialize_label_task

DOMAIN_SPLITS = ("train", "validation", "test")
FAMILY_LABELS = ("benign", "bruteforce", "dos")
SUBTYPE_LABELS = ("benign", "ftp", "smb", "ssh", "hulk", "slowloris")
SUBTYPE_MAP = {
    "benign-admin": "benign",
    "benign-background": "benign",
    "benign-user": "benign",
    "bruteforce-ftp": "ftp",
    "bruteforce-smb": "smb",
    "bruteforce-ssh": "ssh",
    "dos-hulk": "hulk",
    "dos-slowloris": "slowloris",
}
OOD_SUBTYPES = ("dos-icmp", "dos-pushack", "dos-udp")
REQUIRED_FIELDS = (
    "sample_id",
    "group_id",
    "binary_label",
    "attack_family",
    "attack_subtype",
    "features",
    "prompt",
    "completion",
)

TASK_PROMPT_SPECS = {
    "attack_family": (
        "判断以下网络流属于良性流量、暴力破解还是拒绝服务攻击",
        FAMILY_LABELS,
    ),
    "attack_subtype": (
        "判断以下网络流的已见攻击子类",
        SUBTYPE_LABELS,
    ),
    "attack_subtype_open_set": (
        "判断以下网络流的攻击子类，并拒识不属于已见子类的攻击",
        (*SUBTYPE_LABELS, "unknown_attack"),
    ),
}


class HierarchicalSamplingError(ValueError):
    """输入数据不能满足分层采样或防泄漏要求。"""


@dataclass
class _Reservoir:
    target: int
    randomizer: random.Random
    seen: int = 0
    records: list[dict[str, object]] = field(default_factory=list)

    def consider(self, record: dict[str, object]) -> None:
        self.seen += 1
        if len(self.records) < self.target:
            self.records.append(record)
            return
        replacement = self.randomizer.randrange(self.seen)
        if replacement < self.target:
            self.records[replacement] = record

    def finish(self, label: str, split: str) -> list[dict[str, object]]:
        if len(self.records) != self.target:
            raise HierarchicalSamplingError(
                f"{split} 的 {label} 样本不足：需要 {self.target}，实际 {self.seen}"
            )
        return sorted(self.records, key=lambda record: str(record["sample_id"]))


def _derived_seed(seed: int, *parts: str) -> int:
    digest = sha256()
    digest.update(str(seed).encode("ascii"))
    for part in parts:
        digest.update(b"\0")
        digest.update(part.encode("utf-8"))
    return int.from_bytes(digest.digest()[:8], "big")


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_jsonl(path: Path) -> Iterator[dict[str, object]]:
    if not path.is_file():
        raise HierarchicalSamplingError(f"实验源文件不存在：{path}")
    seen = False
    with path.open("rb") as source:
        for line_number, raw_line in enumerate(source, start=1):
            if not raw_line.strip():
                continue
            seen = True
            try:
                value = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise HierarchicalSamplingError(f"JSONL 无法解析：{path}:{line_number}") from error
            if not isinstance(value, dict):
                raise HierarchicalSamplingError(f"JSONL 行必须是对象：{path}:{line_number}")
            missing = [field_name for field_name in REQUIRED_FIELDS if field_name not in value]
            if missing:
                raise HierarchicalSamplingError(
                    f"记录缺少字段：{path}:{line_number} {', '.join(missing)}"
                )
            yield value
    if not seen:
        raise HierarchicalSamplingError(f"实验源文件不能为空：{path}")


def _family_label(record: Mapping[str, object]) -> str:
    label = str(record["attack_family"]).strip().lower()
    if label not in FAMILY_LABELS:
        raise HierarchicalSamplingError(f"未知攻击家族：{label}")
    binary_label = str(record["binary_label"])
    expected_binary = "benign" if label == "benign" else "malicious"
    if binary_label != expected_binary:
        raise HierarchicalSamplingError(f"二分类标签与攻击家族冲突：{binary_label}/{label}")
    return label


def _known_subtype_label(record: Mapping[str, object]) -> str:
    raw_subtype = str(record["attack_subtype"]).strip().lower()
    try:
        return SUBTYPE_MAP[raw_subtype]
    except KeyError as error:
        raise HierarchicalSamplingError(f"域内出现未知攻击子类：{raw_subtype}") from error


def _task_record(record: Mapping[str, object], task: str, task_label: str) -> dict[str, object]:
    try:
        instruction, allowed_labels = TASK_PROMPT_SPECS[task]
    except KeyError as error:
        raise HierarchicalSamplingError(f"未知分层任务：{task}") from error
    features = record["features"]
    if not isinstance(features, Mapping):
        raise HierarchicalSamplingError("流量特征必须是映射")
    result = dict(record)
    result["task"] = task
    result["task_label"] = task_label
    result["prompt"] = serialize_label_task(
        features,
        instruction=instruction,
        allowed_labels=allowed_labels,
    )
    result["completion"] = json.dumps(
        {"label": task_label}, ensure_ascii=False, separators=(",", ":")
    )
    return result


def _register_owner(
    record: Mapping[str, object],
    owner: str,
    sample_owners: dict[str, str],
    group_owners: dict[str, str],
) -> None:
    sample_id = str(record["sample_id"])
    group_id = str(record["group_id"])
    if not sample_id or not group_id:
        raise HierarchicalSamplingError("样本标识和分组标识不能为空")
    previous_sample = sample_owners.setdefault(sample_id, owner)
    if previous_sample != owner:
        raise HierarchicalSamplingError(f"样本跨集合重复：{sample_id}")
    previous_group = group_owners.setdefault(group_id, owner)
    if previous_group != owner:
        raise HierarchicalSamplingError(f"分组跨集合重复：{group_id}")


def _reservoirs(labels: Sequence[str], target: int, seed: int, scope: str) -> dict[str, _Reservoir]:
    if target <= 0:
        raise HierarchicalSamplingError(f"{scope} 的每类采样数必须为正数")
    return {
        label: _Reservoir(
            target=target,
            randomizer=random.Random(_derived_seed(seed, scope, label)),
        )
        for label in labels
    }


def _write_jsonl(path: Path, records: Sequence[Mapping[str, object]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return _file_sha256(path)


def _distribution(records: Sequence[Mapping[str, object]]) -> dict[str, int]:
    return dict(sorted(Counter(str(record["task_label"]) for record in records).items()))


def _validate_budgets(name: str, values: Mapping[str, int]) -> dict[str, int]:
    if set(values) != set(DOMAIN_SPLITS):
        raise HierarchicalSamplingError(f"{name} 必须包含 train、validation、test")
    result = {split: int(values[split]) for split in DOMAIN_SPLITS}
    if any(value <= 0 for value in result.values()):
        raise HierarchicalSamplingError(f"{name} 的每类采样数必须为正数")
    return result


def sample_hierarchical_splits(
    source_dir: Path,
    output_dir: Path,
    family_per_label: Mapping[str, int],
    subtype_per_label: Mapping[str, int],
    ood_attack_per_scenario: int,
    ood_benign_count: int,
    seed: int,
) -> dict[str, object]:
    """流式生成家族、已见子类和混合未知攻击实验集。"""
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)
    family_budget = _validate_budgets("family_per_label", family_per_label)
    subtype_budget = _validate_budgets("subtype_per_label", subtype_per_label)
    if ood_attack_per_scenario <= 0 or ood_benign_count <= 0:
        raise HierarchicalSamplingError("域外攻击和良性对照采样数必须为正数")
    output_dir.mkdir(parents=True, exist_ok=False)

    sample_owners: dict[str, str] = {}
    group_owners: dict[str, str] = {}
    source_hashes: dict[str, str] = {}
    set_manifest: dict[str, object] = {"family": {}, "subtype": {}, "subtype_ood": {}}
    benign_control = _Reservoir(
        target=ood_benign_count,
        randomizer=random.Random(_derived_seed(seed, "ood", "benign-control")),
    )

    for split in DOMAIN_SPLITS:
        source_path = source_dir / f"{split}.jsonl"
        family_reservoirs = _reservoirs(
            FAMILY_LABELS, family_budget[split], seed, f"family:{split}"
        )
        subtype_reservoirs = _reservoirs(
            SUBTYPE_LABELS, subtype_budget[split], seed, f"subtype:{split}"
        )
        for record in _iter_jsonl(source_path):
            _register_owner(record, split, sample_owners, group_owners)
            family_label = _family_label(record)
            subtype_label = _known_subtype_label(record)
            family_reservoirs[family_label].consider(record)
            subtype_reservoirs[subtype_label].consider(record)
            if split == "test" and family_label == "benign":
                benign_control.consider(record)
        source_hashes[source_path.name] = _file_sha256(source_path)

        family_records = [
            _task_record(record, "attack_family", label)
            for label in FAMILY_LABELS
            for record in family_reservoirs[label].finish(label, split)
        ]
        subtype_records = [
            _task_record(record, "attack_subtype", label)
            for label in SUBTYPE_LABELS
            for record in subtype_reservoirs[label].finish(label, split)
        ]
        family_records.sort(key=lambda record: str(record["sample_id"]))
        subtype_records.sort(key=lambda record: str(record["sample_id"]))
        family_path = output_dir / "family" / f"{split}.jsonl"
        subtype_path = output_dir / "subtype" / f"{split}.jsonl"
        set_manifest["family"][split] = {
            "row_count": len(family_records),
            "label_distribution": _distribution(family_records),
            "sha256": _write_jsonl(family_path, family_records),
        }
        set_manifest["subtype"][split] = {
            "row_count": len(subtype_records),
            "label_distribution": _distribution(subtype_records),
            "sha256": _write_jsonl(subtype_path, subtype_records),
        }

    shared_benign = benign_control.finish("benign", "test-control")
    for ood_subtype in OOD_SUBTYPES:
        source_path = source_dir / f"ood_{ood_subtype}.jsonl"
        attack_reservoir = _Reservoir(
            target=ood_attack_per_scenario,
            randomizer=random.Random(_derived_seed(seed, "ood", ood_subtype)),
        )
        owner = f"ood:{ood_subtype}"
        for record in _iter_jsonl(source_path):
            _register_owner(record, owner, sample_owners, group_owners)
            raw_subtype = str(record["attack_subtype"]).strip().lower()
            if raw_subtype != ood_subtype or str(record["binary_label"]) != "malicious":
                raise HierarchicalSamplingError(
                    f"域外文件标签不一致：{source_path.name}/{raw_subtype}"
                )
            attack_reservoir.consider(record)
        source_hashes[source_path.name] = _file_sha256(source_path)
        mixed_records = [
            *(
                _task_record(record, "attack_subtype_open_set", "benign")
                for record in shared_benign
            ),
            *(
                _task_record(record, "attack_subtype_open_set", "unknown_attack")
                for record in attack_reservoir.finish(ood_subtype, owner)
            ),
        ]
        mixed_records.sort(key=lambda record: str(record["sample_id"]))
        output_path = output_dir / "subtype_ood" / f"{ood_subtype}.jsonl"
        set_manifest["subtype_ood"][ood_subtype] = {
            "row_count": len(mixed_records),
            "label_distribution": _distribution(mixed_records),
            "sha256": _write_jsonl(output_path, mixed_records),
        }

    manifest = {
        "schema_version": "flow_probe_hierarchical_sample_v2",
        "seed": seed,
        "sampling": "streaming_stratified_reservoir_without_replacement",
        "task_labels": {
            "family": list(FAMILY_LABELS),
            "known_subtype": list(SUBTYPE_LABELS),
            "open_set_subtype": [*SUBTYPE_LABELS, "unknown_attack"],
        },
        "prompt_contract": {
            "task_specific_label_space": True,
            "uses_only_canonical_numeric_features": True,
            "sample_or_source_metadata_in_prompt": False,
        },
        "budgets_per_label": {
            "family": family_budget,
            "subtype": subtype_budget,
            "ood_attack_per_scenario": ood_attack_per_scenario,
            "ood_benign_count": ood_benign_count,
        },
        "source_sha256": dict(sorted(source_hashes.items())),
        "sets": set_manifest,
        "ood_protocol": {
            "ood_subtypes_absent_from_domain_training": True,
            "shared_benign_control_across_scenarios": True,
            "threshold_calibration_uses_ood_labels": False,
        },
    }
    (output_dir / "sample_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 GeNIS 分层多分类固定实验集")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--family-train-per-label", type=int, default=2000)
    parser.add_argument("--family-validation-per-label", type=int, default=300)
    parser.add_argument("--family-test-per-label", type=int, default=1000)
    parser.add_argument("--subtype-train-per-label", type=int, default=1500)
    parser.add_argument("--subtype-validation-per-label", type=int, default=300)
    parser.add_argument("--subtype-test-per-label", type=int, default=300)
    parser.add_argument("--ood-attack-per-scenario", type=int, default=1000)
    parser.add_argument("--ood-benign-count", type=int, default=1000)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = sample_hierarchical_splits(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        family_per_label={
            "train": args.family_train_per_label,
            "validation": args.family_validation_per_label,
            "test": args.family_test_per_label,
        },
        subtype_per_label={
            "train": args.subtype_train_per_label,
            "validation": args.subtype_validation_per_label,
            "test": args.subtype_test_per_label,
        },
        ood_attack_per_scenario=args.ood_attack_per_scenario,
        ood_benign_count=args.ood_benign_count,
        seed=args.seed,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
