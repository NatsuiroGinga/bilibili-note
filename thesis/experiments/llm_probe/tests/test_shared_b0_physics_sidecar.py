"""共享 B0 物理旁路的确定性物化与失败即停测试。"""

from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml


def _subject():
    return importlib.import_module("flow_probe.shared_b0_physics_sidecar")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
        newline="\n",
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _expected_mask(sample_id: str, seed: int = 42) -> list[bool]:
    digest = hashlib.sha256(f"{seed}:{sample_id}".encode("utf-8")).digest()
    second_anchor = int.from_bytes(digest, "big") % 4 + 1
    return [index in {0, second_anchor} for index in range(5)]


def _refresh_output_hash_bindings(output: Path) -> None:
    record_path = output / "candidate" / "ns3_physics_train.jsonl"
    dataset_path = output / "dataset_manifest.json"
    source_path = output / "source_manifest.json"
    join_path = output / "join_audit.json"
    materialization_path = output / "materialization_audit.json"

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    for relative, path in (
        ("candidate/ns3_physics_train.jsonl", record_path),
        ("source_manifest.json", source_path),
        ("join_audit.json", join_path),
    ):
        dataset["artifacts"][relative]["sha256"] = _sha256(path)
        dataset["artifacts"][relative]["size_bytes"] = path.stat().st_size
    _write_json(dataset_path, dataset)

    materialization = json.loads(materialization_path.read_text(encoding="utf-8"))
    for relative, path in (
        ("candidate/ns3_physics_train.jsonl", record_path),
        ("dataset_manifest.json", dataset_path),
        ("source_manifest.json", source_path),
        ("join_audit.json", join_path),
    ):
        materialization["artifacts"][relative]["sha256"] = _sha256(path)
        materialization["artifacts"][relative]["size_bytes"] = path.stat().st_size
    _write_json(materialization_path, materialization)


@dataclass(frozen=True)
class _Fixture:
    root: Path
    config_path: Path
    classification_path: Path
    source_paths: tuple[Path, Path, Path]
    sample_ids: tuple[str, ...]


def _source_record(index: int, sample_id: str, split: str) -> dict[str, object]:
    queue_start = float(index % 17)
    capacity = [12_500.0, 12_500.0, 12_500.0, 12_500.0]
    return {
        "sample_id": sample_id,
        "group_id": f"star-bottleneck-v1|scenario-{index % 11}|seed42|run1",
        "split": split,
        "model_inputs": {
            "configured_capacity_integral_link_bytes": capacity,
            "qdisc_received_l3_bytes": [100.0 + index % 7, 120.0, 140.0, 160.0],
            "qdisc_received_packets": [1.0, 2.0, 3.0, 4.0],
        },
        "queue_boundary_anchors_l3_bytes": [
            queue_start,
            queue_start + 1.0,
            queue_start + 2.0,
            queue_start + 3.0,
            queue_start + 4.0,
        ],
        "state_supervision": {
            "qdisc_dequeued_l3_bytes": [90.0, 110.0, 130.0, 150.0],
            "qdisc_dropped_before_enqueue_l3_bytes": [1.0, 0.0, 2.0, 0.0],
            "qdisc_dropped_after_dequeue_l3_bytes": [0.0, 1.0, 0.0, 2.0],
        },
        "normalization_scale_configured_capacity_integral_link_bytes": capacity,
        "metadata": {
            "window_start_s": [0.0, 0.1, 0.2, 0.3],
            "window_end_s": [0.1, 0.2, 0.3, 0.4],
        },
    }


def _write_config(
    fixture_root: Path,
    source_paths: tuple[Path, Path, Path],
    *,
    usage: str = "train_fit_diagnostic",
) -> Path:
    config_path = fixture_root / "configs" / "shared_b0_physics_sidecar_v1.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    sources = []
    for split, source_path in zip(
        ("train", "validation", "test"), source_paths, strict=True
    ):
        sources.append(
            {
                "split": split,
                "path": source_path.relative_to(fixture_root).as_posix(),
                "sha256": _sha256(source_path),
                "expected_count": 807,
            }
        )
    config = {
        "schema_version": "flow_probe_shared_b0_physics_sidecar_config_v1",
        "dataset_name": "dataset-v1-shared-b0-physics-v1",
        "stage": "theory_selection",
        "status": "review_pending",
        "classification": {
            "manifest": (
                "runs/data-frozen/dataset-v1-shared-b0/candidate/qwen_train.jsonl"
            ),
            "ns3_sample_id_prefix": "ns3-h4-",
        },
        "contract": {
            "record_count": 2_421,
            "anchor_count": 5,
            "usage": usage,
        },
        "state_mask": {"mode": "anchor0_plus_one", "seed": 42},
        "sources": sources,
        "publication": {
            "output": "runs/data-frozen/dataset-v1-shared-b0-physics-v1"
        },
    }
    config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )
    return config_path


def _build_fixture(tmp_path: Path) -> _Fixture:
    root = tmp_path / "project"
    root.mkdir()
    sample_ids = tuple(f"ns3-h4-{index:064x}" for index in range(2_421))
    source_root = root / "runs" / "ns3-data" / "frozen-sequences"
    source_paths = tuple(
        source_root / f"{split}.jsonl" for split in ("train", "validation", "test")
    )
    for split_index, (split, path) in enumerate(
        zip(("train", "validation", "test"), source_paths, strict=True)
    ):
        start = split_index * 807
        _write_jsonl(
            path,
            [
                _source_record(index, sample_ids[index], split)
                for index in range(start, start + 807)
            ],
        )

    classification_path = (
        root
        / "runs"
        / "data-frozen"
        / "dataset-v1-shared-b0"
        / "candidate"
        / "qwen_train.jsonl"
    )
    classification_rows = [
        {
            "sample_id": "genis-control",
            "stable_order": 0,
            "prompt": "公开共同观测",
            "completion": '{"binary_label":"benign"}',
        }
    ]
    classification_rows.extend(
        {
            "sample_id": sample_id,
            "stable_order": stable_order,
            "prompt": "公开共同观测",
            "completion": '{"binary_label":"benign"}',
        }
        for stable_order, sample_id in enumerate(reversed(sample_ids), start=1)
    )
    classification_rows.append(
        {
            "sample_id": "tqhc2-control",
            "stable_order": len(classification_rows),
            "prompt": "公开共同观测",
            "completion": '{"binary_label":"malicious"}',
        }
    )
    _write_jsonl(classification_path, classification_rows)
    config_path = _write_config(root, source_paths)
    return _Fixture(
        root=root,
        config_path=config_path,
        classification_path=classification_path,
        source_paths=source_paths,
        sample_ids=sample_ids,
    )


def _refresh_source_hashes(fixture: _Fixture) -> None:
    config = yaml.safe_load(fixture.config_path.read_text(encoding="utf-8"))
    for source, path in zip(config["sources"], fixture.source_paths, strict=True):
        source["sha256"] = _sha256(path)
    fixture.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )


def test_production_config_freezes_paths_counts_usage_and_source_hashes() -> None:
    subject = _subject()
    config_path = (
        Path(__file__).parents[1] / "configs" / "shared_b0_physics_sidecar_v1.yaml"
    )

    config = subject.load_shared_b0_physics_sidecar_config(config_path)

    assert config.classification_manifest == subject.CLASSIFICATION_LOGICAL_PATH
    assert config.output_path == subject.OUTPUT_LOGICAL_PATH
    assert config.expected_record_count == 2_421
    assert config.anchor_count == 5
    assert config.usage == "train_fit_diagnostic"
    assert config.stage == "theory_selection"
    assert config.status == "review_pending"
    assert config.state_mask_mode == "anchor0_plus_one"
    assert config.state_mask_seed == 42
    assert [
        (
            source.source_split,
            source.path,
            source.sha256,
            source.expected_count,
        )
        for source in config.sources
    ] == [
        (
            "train",
            "runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/train.jsonl",
            "d6a6ca23a985223401e1d650d619c2a50b255d2066769e2478cef72cc6239fa0",
            807,
        ),
        (
            "validation",
            "runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/validation.jsonl",
            "0bbbb4ea483867561c329c896cb4e7745a102cb90024c464654e0b7d673c8723",
            807,
        ),
        (
            "test",
            "runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/test.jsonl",
            "6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94",
            807,
        ),
    ]


def test_config_requires_exactly_807_records_per_source(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    config = yaml.safe_load(fixture.config_path.read_text(encoding="utf-8"))
    config["sources"][0]["expected_count"] = 806
    config["sources"][2]["expected_count"] = 808
    fixture.config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="各登记 807 条"):
        subject.load_shared_b0_physics_sidecar_config(fixture.config_path)


def test_mask_depends_only_on_sample_id_and_seed() -> None:
    subject = _subject()
    first_id = "ns3-h4-" + "a" * 64
    second_id = "ns3-h4-" + "b" * 64
    first_records = {
        first_id: subject._SourceRecord(
            value={
                "group_id": "scenario-benign",
                "label": "benign",
                "prompt": "first prompt",
                "scenario_name": "first-scene",
            },
            source_split="train",
            source_file_sha256="1" * 64,
        ),
        second_id: subject._SourceRecord(
            value={
                "group_id": "scenario-malicious",
                "label": "malicious",
                "prompt": "second prompt",
                "scenario_name": "second-scene",
            },
            source_split="test",
            source_file_sha256="2" * 64,
        ),
    }
    changed_and_reordered_records = {
        second_id: subject._SourceRecord(
            value={
                "group_id": "changed-group-b",
                "label": "changed-label-b",
                "prompt": "changed prompt b",
                "scenario_name": "changed-scene-b",
            },
            source_split="validation",
            source_file_sha256="3" * 64,
        ),
        first_id: subject._SourceRecord(
            value={
                "group_id": "changed-group-a",
                "label": "changed-label-a",
                "prompt": "changed prompt a",
                "scenario_name": "changed-scene-a",
            },
            source_split="test",
            source_file_sha256="4" * 64,
        ),
    }

    first_masks = subject._build_state_masks(first_records, 42)
    changed_masks = subject._build_state_masks(changed_and_reordered_records, 42)

    assert first_masks == changed_masks
    assert first_masks == {
        first_id: tuple(_expected_mask(first_id)),
        second_id: tuple(_expected_mask(second_id)),
    }
    assert all(mask[0] is True and sum(mask) == 2 for mask in first_masks.values())


def test_materializes_exact_sidecar_by_sample_id_and_preserves_classification(
    tmp_path: Path,
) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    classification_sha256 = _sha256(fixture.classification_path)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)
    output = tmp_path / "sidecar"

    manifest = subject.materialize_shared_b0_physics_sidecar(config, output)
    audit = subject.validate_shared_b0_physics_sidecar(
        output, fixture.classification_path
    )

    assert manifest.record_count == 2_421
    assert audit.status == "passed"
    assert audit.classification_record_count == 2_423
    assert audit.classification_ns3_count == 2_421
    assert _sha256(fixture.classification_path) == classification_sha256
    assert all((output / relative).is_file() for relative in subject.REQUIRED_OUTPUT_FILES)
    rows = _read_jsonl(output / "candidate" / "ns3_physics_train.jsonl")
    first = rows[0]
    assert first["sample_id"] == fixture.sample_ids[-1]
    assert first["source_record_id"] == fixture.sample_ids[-1]
    assert first["source_split"] == "test"
    assert first["stable_order"] == 1
    assert first == {
        "schema_version": "flow_probe_shared_b0_physics_sidecar_v1",
        "sample_id": fixture.sample_ids[-1],
        "group_id": "star-bottleneck-v1|scenario-0|seed42|run1",
        "stable_order": 1,
        "source_split": "test",
        "usage": "train_fit_diagnostic",
        "anchor_times": [0.0, 0.1, 0.2, 0.3, 0.4],
        "state_targets": [
            6.0 / 12_500.0,
            7.0 / 12_500.0,
            8.0 / 12_500.0,
            9.0 / 12_500.0,
            10.0 / 12_500.0,
        ],
        "state_mask_inputs": _expected_mask(fixture.sample_ids[-1]),
        "capacity_by_anchor": [0.0, 12_500.0, 25_000.0, 37_500.0, 50_000.0],
        "received_bytes_by_anchor": [0.0, 105.0, 225.0, 365.0, 525.0],
        "received_packets_by_anchor": [0.0, 1.0, 3.0, 6.0, 10.0],
        "dequeued_bytes_by_anchor": [0.0, 90.0, 200.0, 330.0, 480.0],
        "dropped_bytes_by_anchor": [0.0, 1.0, 2.0, 4.0, 6.0],
        "normalization_scale": 12_500.0,
        "source_record_id": fixture.sample_ids[-1],
        "source_file_sha256": _sha256(fixture.source_paths[2]),
    }
    assert not (output / "candidate" / "qwen_train.jsonl").exists()


def test_rejects_classification_missing_ns3_identifier(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    rows = _read_jsonl(fixture.classification_path)
    rows[1]["sample_id"] = "genis-replaced-ns3"
    _write_jsonl(fixture.classification_path, rows)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="ns-3 标识数必须为 2421"):
        subject.materialize_shared_b0_physics_sidecar(config, tmp_path / "sidecar")


def test_rejects_duplicate_classification_identifier(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    rows = _read_jsonl(fixture.classification_path)
    rows[2]["sample_id"] = rows[1]["sample_id"]
    _write_jsonl(fixture.classification_path, rows)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="sample_id 重复"):
        subject.materialize_shared_b0_physics_sidecar(config, tmp_path / "sidecar")


def test_rejects_duplicate_source_identifier(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    rows = _read_jsonl(fixture.source_paths[0])
    rows[-1]["sample_id"] = rows[0]["sample_id"]
    _write_jsonl(fixture.source_paths[0], rows)
    _refresh_source_hashes(fixture)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="sample_id 重复"):
        subject.materialize_shared_b0_physics_sidecar(config, tmp_path / "sidecar")


def test_rejects_extra_and_mismatched_source_identifier(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    rows = _read_jsonl(fixture.source_paths[2])
    rows[-1]["sample_id"] = "ns3-h4-" + "f" * 64
    _write_jsonl(fixture.source_paths[2], rows)
    _refresh_source_hashes(fixture)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="sample_id 集合错配"):
        subject.materialize_shared_b0_physics_sidecar(config, tmp_path / "sidecar")


def test_rejects_non_increasing_anchor_times(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    rows = _read_jsonl(fixture.source_paths[0])
    rows[0]["metadata"]["window_end_s"][1] = 0.1
    _write_jsonl(fixture.source_paths[0], rows)
    _refresh_source_hashes(fixture)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="非法锚点|未严格递增"):
        subject.materialize_shared_b0_physics_sidecar(config, tmp_path / "sidecar")


def test_rejects_non_finite_physics_value(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    rows = _read_jsonl(fixture.source_paths[1])
    rows[0]["model_inputs"]["qdisc_received_l3_bytes"][0] = float("nan")
    _write_jsonl(fixture.source_paths[1], rows)
    _refresh_source_hashes(fixture)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="非有限数值"):
        subject.materialize_shared_b0_physics_sidecar(config, tmp_path / "sidecar")


def test_rejects_non_positive_normalization_scale(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    rows = _read_jsonl(fixture.source_paths[1])
    rows[0]["normalization_scale_configured_capacity_integral_link_bytes"] = [
        0.0,
        0.0,
        0.0,
        0.0,
    ]
    _write_jsonl(fixture.source_paths[1], rows)
    _refresh_source_hashes(fixture)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="归一化尺度必须严格为正"):
        subject.materialize_shared_b0_physics_sidecar(config, tmp_path / "sidecar")


def test_rejects_usage_other_than_train_fit_diagnostic(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    _write_config(fixture.root, fixture.source_paths, usage="external_test")

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="usage 必须固定"):
        subject.load_shared_b0_physics_sidecar_config(fixture.config_path)


def test_rejects_source_hash_change_before_materialization(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)
    fixture.source_paths[0].write_text(
        fixture.source_paths[0].read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="冻结来源哈希变化"):
        subject.materialize_shared_b0_physics_sidecar(config, tmp_path / "sidecar")


@pytest.mark.parametrize("tamper_kind", ["cumulative", "source_split", "mask"])
def test_validator_rebuilds_source_semantics_after_outer_hashes_are_refreshed(
    tmp_path: Path,
    tamper_kind: str,
) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)
    output = tmp_path / "sidecar"
    subject.materialize_shared_b0_physics_sidecar(config, output)
    record_path = output / "candidate" / "ns3_physics_train.jsonl"
    rows = _read_jsonl(record_path)

    if tamper_kind == "cumulative":
        rows[0]["received_bytes_by_anchor"][2] += 1.0
    elif tamper_kind == "source_split":
        source_manifest = json.loads(
            (output / "source_manifest.json").read_text(encoding="utf-8")
        )
        rows[0]["source_split"] = "train"
        rows[0]["source_file_sha256"] = source_manifest["sources"][0]["sha256"]
    else:
        rows[0]["state_mask_inputs"] = [True, True, True, True, True]
    _write_jsonl(record_path, rows)
    _refresh_output_hash_bindings(output)

    with pytest.raises(
        subject.SharedB0PhysicsSidecarError,
        match="冻结来源语义错配|严格为锚点 0 加一个其他锚点",
    ):
        subject.validate_shared_b0_physics_sidecar(
            output, fixture.classification_path
        )


def test_validator_compares_source_manifest_with_real_config(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)
    output = tmp_path / "sidecar"
    subject.materialize_shared_b0_physics_sidecar(config, output)
    source_manifest_path = output / "source_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest["sources"][0]["selected_record_count"] = 806
    _write_json(source_manifest_path, source_manifest)
    _refresh_output_hash_bindings(output)

    with pytest.raises(
        subject.SharedB0PhysicsSidecarError,
        match="来源登记与真实配置不一致",
    ):
        subject.validate_shared_b0_physics_sidecar(
            output, fixture.classification_path
        )


def test_publish_failure_preserves_precreated_empty_directory_and_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)
    output = tmp_path / "sidecar"
    partial = tmp_path / "sidecar.partial"
    output.mkdir()
    original_replace = Path.replace

    def fail_publish(path: Path, target: Path) -> Path:
        if path == partial and Path(target) == output:
            raise OSError("注入发布重命名失败")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_publish)

    with pytest.raises(OSError, match="注入发布重命名失败"):
        subject.materialize_shared_b0_physics_sidecar(config, output)

    assert output.is_dir()
    assert list(output.iterdir()) == []
    assert not partial.exists()

    sentinel = output / "sentinel.txt"
    sentinel.write_bytes(b"keep-existing-content")
    with pytest.raises(subject.SharedB0PhysicsSidecarError, match="拒绝覆盖"):
        subject.materialize_shared_b0_physics_sidecar(config, output)
    assert sentinel.read_bytes() == b"keep-existing-content"
    assert not partial.exists()


@pytest.mark.parametrize(
    "invalid_kind",
    [
        "output_root_symlink",
        "extra_file",
        "renamed_classification_copy",
        "required_file_symlink",
        "non_empty_directory",
        "leftover_partial",
    ],
)
def test_validator_rejects_non_exact_or_linked_output_tree(
    tmp_path: Path,
    invalid_kind: str,
) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)
    output = tmp_path / "sidecar"
    subject.materialize_shared_b0_physics_sidecar(config, output)
    validation_root = output

    if invalid_kind == "output_root_symlink":
        validation_root = tmp_path / "sidecar-link"
        validation_root.symlink_to(output, target_is_directory=True)
    elif invalid_kind == "extra_file":
        (output / "extra.json").write_text("{}\n", encoding="utf-8")
    elif invalid_kind == "renamed_classification_copy":
        (output / "candidate" / "classification-copy.jsonl").write_bytes(
            fixture.classification_path.read_bytes()
        )
    elif invalid_kind == "required_file_symlink":
        record_path = output / "candidate" / "ns3_physics_train.jsonl"
        record_path.unlink()
        record_path.symlink_to(fixture.classification_path)
    elif invalid_kind == "non_empty_directory":
        unexpected = output / "unexpected"
        unexpected.mkdir()
        (unexpected / "data.json").write_text("{}\n", encoding="utf-8")
    else:
        output.with_name(output.name + ".partial").mkdir()

    with pytest.raises(subject.SharedB0PhysicsSidecarError):
        subject.validate_shared_b0_physics_sidecar(
            validation_root, fixture.classification_path
        )


def test_validator_requires_exact_materialization_file_set(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)
    output = tmp_path / "sidecar"
    subject.materialize_shared_b0_physics_sidecar(config, output)
    audit_path = output / "materialization_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["required_files"].append("candidate/renamed-copy.jsonl")
    _write_json(audit_path, audit)

    with pytest.raises(
        subject.SharedB0PhysicsSidecarError,
        match="必要文件集合不合法",
    ):
        subject.validate_shared_b0_physics_sidecar(
            output, fixture.classification_path
        )


def test_two_independent_materializations_are_byte_identical(tmp_path: Path) -> None:
    subject = _subject()
    fixture = _build_fixture(tmp_path)
    config = subject.load_shared_b0_physics_sidecar_config(fixture.config_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    subject.materialize_shared_b0_physics_sidecar(config, first)
    subject.materialize_shared_b0_physics_sidecar(config, second)

    first_files = sorted(
        path.relative_to(first).as_posix() for path in first.rglob("*") if path.is_file()
    )
    second_files = sorted(
        path.relative_to(second).as_posix() for path in second.rglob("*") if path.is_file()
    )
    assert first_files == sorted(subject.REQUIRED_OUTPUT_FILES)
    assert second_files == sorted(subject.REQUIRED_OUTPUT_FILES)
    assert all((first / relative).read_bytes() == (second / relative).read_bytes() for relative in first_files)
