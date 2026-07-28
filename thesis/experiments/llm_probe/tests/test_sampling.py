import json

import pytest

from flow_probe.sampling import SamplingError, sample_prepared_splits

SPLITS = ("train", "validation", "test")


def write_split(path, split: str, count_per_label: int) -> None:
    records = []
    for label in ("benign", "malicious"):
        for index in range(count_per_label):
            sample_id = f"{split}-{label}-{index:03d}"
            records.append(
                {
                    "sample_id": sample_id,
                    "group_id": f"{split}-group-{label}-{index:03d}",
                    "source_dataset": "hikari",
                    "binary_label": label,
                    "attack_family": label,
                    "prompt": f"流量记录：{sample_id}",
                    "completion": json.dumps(
                        {"label": label}, ensure_ascii=False, separators=(",", ":")
                    ),
                }
            )
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def read_jsonl(path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_sample_prepared_splits_is_balanced_deterministic_and_auditable(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    for split in SPLITS:
        write_split(source_dir / f"{split}.jsonl", split, count_per_label=8)

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    targets = {"train": 8, "validation": 4, "test": 6}
    first = sample_prepared_splits(source_dir, first_dir, targets=targets, seed=42)
    second = sample_prepared_splits(source_dir, second_dir, targets=targets, seed=42)

    assert first == second
    assert first["schema_version"] == "flow_probe_sample_manifest_v1"
    assert first["seed"] == 42
    for split, target in targets.items():
        first_records = read_jsonl(first_dir / f"{split}.jsonl")
        second_records = read_jsonl(second_dir / f"{split}.jsonl")
        assert first_records == second_records
        assert len(first_records) == target
        assert first["splits"][split]["label_distribution"] == {
            "benign": target // 2,
            "malicious": target // 2,
        }
        assert len(first["splits"][split]["source_sha256"]) == 64
    assert (first_dir / "sample_manifest.json").is_file()


def test_sample_prepared_splits_rejects_insufficient_class(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    for split in SPLITS:
        write_split(source_dir / f"{split}.jsonl", split, count_per_label=1)

    with pytest.raises(SamplingError, match="样本不足"):
        sample_prepared_splits(
            source_dir,
            tmp_path / "sampled",
            targets={"train": 4, "validation": 2, "test": 2},
            seed=42,
        )


def test_sample_prepared_splits_rejects_cross_split_group(tmp_path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    for split in SPLITS:
        write_split(source_dir / f"{split}.jsonl", split, count_per_label=2)
    validation_path = source_dir / "validation.jsonl"
    validation_records = read_jsonl(validation_path)
    validation_records[0]["group_id"] = "train-group-benign-000"
    validation_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in validation_records),
        encoding="utf-8",
    )

    with pytest.raises(SamplingError, match="分组交叉"):
        sample_prepared_splits(
            source_dir,
            tmp_path / "sampled",
            targets={"train": 2, "validation": 2, "test": 2},
            seed=42,
        )
