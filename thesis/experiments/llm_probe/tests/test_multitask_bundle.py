import hashlib
import importlib
import importlib.util
import json
from pathlib import Path


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> str:
    content = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _record(task: str, label: str, index: int) -> dict[str, object]:
    return {
        "sample_id": f"{task}-{label}-{index}",
        "group_id": f"group-{task}-{label}-{index}",
        "task": task,
        "task_label": label,
        "prompt": f"任务提示-{task}-{index}",
        "completion": json.dumps({"label": label}, separators=(",", ":")),
    }


def _build_sample_dir(sample_dir: Path, seed: int = 42) -> None:
    sets: dict[str, dict[str, object]] = {"family": {}, "subtype": {}}
    task_specs = {
        "family": ("attack_family", ("benign", "bruteforce", "dos")),
        "subtype": (
            "attack_subtype",
            ("benign", "ftp", "smb", "ssh", "hulk", "slowloris"),
        ),
    }
    for scope, (task, labels) in task_specs.items():
        for split in ("train", "validation"):
            records = [_record(task, label, index) for label in labels for index in range(2)]
            path = sample_dir / scope / f"{split}.jsonl"
            sets[scope][split] = {
                "row_count": len(records),
                "sha256": _write_jsonl(path, records),
            }
    manifest = {
        "schema_version": "flow_probe_hierarchical_sample_v2",
        "seed": seed,
        "sets": sets,
        "task_labels": {
            "family": ["benign", "bruteforce", "dos"],
            "known_subtype": ["benign", "ftp", "smb", "ssh", "hulk", "slowloris"],
            "open_set_subtype": [
                "benign",
                "ftp",
                "smb",
                "ssh",
                "hulk",
                "slowloris",
                "unknown_attack",
            ],
        },
    }
    (sample_dir / "sample_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_multitask_bundle_is_deterministic_and_excludes_unknown_attacks(tmp_path: Path) -> None:
    assert importlib.util.find_spec("flow_probe.multitask_bundle") is not None
    module = importlib.import_module("flow_probe.multitask_bundle")
    sample_dir = tmp_path / "sample"
    _build_sample_dir(sample_dir)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first = module.build_multitask_bundle(sample_dir, first_dir, seed=42)
    second = module.build_multitask_bundle(sample_dir, second_dir, seed=42)

    assert first == second
    assert first["schema_version"] == "flow_probe_multitask_bundle_v1"
    assert first["sets"]["train"]["row_count"] == 18
    assert first["sets"]["validation"]["row_count"] == 18
    assert first["sets"]["train"]["task_distribution"] == {
        "attack_family": 6,
        "attack_subtype": 12,
    }
    assert (first_dir / "train.jsonl").read_bytes() == (second_dir / "train.jsonl").read_bytes()
    records = _read_jsonl(first_dir / "train.jsonl")
    assert {record["task"] for record in records} == {"attack_family", "attack_subtype"}
    assert all(record["task_label"] != "unknown_attack" for record in records)


def test_multitask_bundle_rejects_v1_or_tampered_source(tmp_path: Path) -> None:
    assert importlib.util.find_spec("flow_probe.multitask_bundle") is not None
    module = importlib.import_module("flow_probe.multitask_bundle")
    sample_dir = tmp_path / "sample"
    _build_sample_dir(sample_dir)
    manifest_path = sample_dir / "sample_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "flow_probe_hierarchical_sample_v1"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    try:
        module.build_multitask_bundle(sample_dir, tmp_path / "v1-output", seed=42)
    except module.MultitaskBundleError as error:
        assert "v2" in str(error)
    else:
        raise AssertionError("v1 清单必须被拒绝")

    _build_sample_dir(sample_dir)
    with (sample_dir / "family" / "train.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(_record("attack_family", "benign", 99)) + "\n")
    try:
        module.build_multitask_bundle(sample_dir, tmp_path / "tampered-output", seed=42)
    except module.MultitaskBundleError as error:
        assert "SHA-256" in str(error)
    else:
        raise AssertionError("被篡改的源文件必须被拒绝")
