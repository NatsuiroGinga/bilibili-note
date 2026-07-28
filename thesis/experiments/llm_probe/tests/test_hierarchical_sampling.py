import importlib
import importlib.util
import json
from pathlib import Path

from flow_probe.schemas import CANONICAL_CORE_FIELDS

DOMAIN_SPLITS = ("train", "validation", "test")
KNOWN_SUBTYPES = (
    ("benign", "benign-admin"),
    ("bruteforce", "bruteforce-ftp"),
    ("bruteforce", "bruteforce-smb"),
    ("bruteforce", "bruteforce-ssh"),
    ("dos", "dos-hulk"),
    ("dos", "dos-slowloris"),
)
OOD_SUBTYPES = ("dos-icmp", "dos-pushack", "dos-udp")


def _record(split: str, family: str, subtype: str, index: int) -> dict[str, object]:
    binary_label = "benign" if family == "benign" else "malicious"
    sample_id = f"{split}-{subtype}-{index}"
    features = {field: None for field in CANONICAL_CORE_FIELDS}
    features["total_packets"] = float(index + 1)
    return {
        "sample_id": sample_id,
        "group_id": f"{split}-group-{subtype}-{index}",
        "source_dataset": "genis",
        "binary_label": binary_label,
        "attack_family": family,
        "attack_subtype": subtype,
        "features": features,
        "prompt": f"流量记录：{sample_id}",
        "completion": json.dumps({"label": binary_label}, separators=(",", ":")),
    }


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _build_source(source_dir: Path) -> None:
    source_dir.mkdir()
    for split in DOMAIN_SPLITS:
        records = [
            _record(split, family, subtype, index)
            for family, subtype in KNOWN_SUBTYPES
            for index in range(4)
        ]
        _write_jsonl(source_dir / f"{split}.jsonl", records)
    for subtype in OOD_SUBTYPES:
        records = [_record("ood", "dos", subtype, index) for index in range(4)]
        _write_jsonl(source_dir / f"ood_{subtype}.jsonl", records)


def test_hierarchical_sampling_is_balanced_deterministic_and_keeps_ood_out_of_training(
    tmp_path: Path,
) -> None:
    assert importlib.util.find_spec("flow_probe.hierarchical_sampling") is not None
    module = importlib.import_module("flow_probe.hierarchical_sampling")
    source_dir = tmp_path / "source"
    _build_source(source_dir)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    kwargs = {
        "family_per_label": {split: 2 for split in DOMAIN_SPLITS},
        "subtype_per_label": {split: 2 for split in DOMAIN_SPLITS},
        "ood_attack_per_scenario": 2,
        "ood_benign_count": 2,
        "seed": 42,
    }

    first = module.sample_hierarchical_splits(source_dir, first_dir, **kwargs)
    second = module.sample_hierarchical_splits(source_dir, second_dir, **kwargs)

    assert first == second
    assert first["schema_version"] == "flow_probe_hierarchical_sample_v2"
    for split in DOMAIN_SPLITS:
        family_records = _read_jsonl(first_dir / "family" / f"{split}.jsonl")
        subtype_records = _read_jsonl(first_dir / "subtype" / f"{split}.jsonl")
        assert len(family_records) == 6
        assert len(subtype_records) == 12
        assert {record["task_label"] for record in family_records} == {
            "benign",
            "bruteforce",
            "dos",
        }
        assert {record["task_label"] for record in subtype_records} == {
            "benign",
            "ftp",
            "smb",
            "ssh",
            "hulk",
            "slowloris",
        }
        assert all("benign、bruteforce、dos" in record["prompt"] for record in family_records)
        assert all(
            "benign、ftp、smb、ssh、hulk、slowloris" in record["prompt"]
            for record in subtype_records
        )
        assert all("total_packets=" in record["prompt"] for record in family_records)
        assert all(record["sample_id"] not in record["prompt"] for record in family_records)
        assert all(record["attack_subtype"] not in record["prompt"] for record in family_records)
        assert all('{"label":"malicious"}' not in record["prompt"] for record in family_records)
        assert all("unknown_attack" not in record["completion"] for record in subtype_records)
    shared_benign_ids = None
    for subtype in OOD_SUBTYPES:
        records = _read_jsonl(first_dir / "subtype_ood" / f"{subtype}.jsonl")
        assert len(records) == 4
        assert {record["task_label"] for record in records} == {
            "benign",
            "unknown_attack",
        }
        assert all("unknown_attack" in record["prompt"] for record in records)
        assert all(record["sample_id"] not in record["prompt"] for record in records)
        assert all(record["attack_subtype"] not in record["prompt"] for record in records)
        benign_ids = {record["sample_id"] for record in records if record["task_label"] == "benign"}
        if shared_benign_ids is None:
            shared_benign_ids = benign_ids
        else:
            assert benign_ids == shared_benign_ids
    assert first["ood_protocol"] == {
        "ood_subtypes_absent_from_domain_training": True,
        "shared_benign_control_across_scenarios": True,
        "threshold_calibration_uses_ood_labels": False,
    }
