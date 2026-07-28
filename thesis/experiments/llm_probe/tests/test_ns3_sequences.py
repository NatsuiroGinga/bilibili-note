import csv
import hashlib
import importlib
import json
import os
from pathlib import Path
from types import ModuleType

import pytest

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from flow_probe.ns3_field_roles import (
    load_ns3_field_roles,
    validate_group_disjoint_splits,
)
from flow_probe.ns3_truth import CSV_FIELDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIELD_ROLES_PATH = PROJECT_ROOT / "configs" / "ns3_queue_truth_field_roles.json"
SHELL_SCRIPT = PROJECT_ROOT / "scripts" / "build_ns3_sequences.sh"
REQUIRED_ARTIFACTS = {
    "train.jsonl",
    "validation.jsonl",
    "test.jsonl",
    "split_manifest.json",
    "field_roles_snapshot.json",
    "source_csv_sha256.json",
    "sample_statistics.json",
    "artifact_manifest.json",
    "console.log",
}


def _subject() -> ModuleType:
    return importlib.import_module("flow_probe.ns3_sequences")


def _rows(
    *,
    seed: int = 42,
    scenario: str = "benign-low",
) -> list[dict[str, object]]:
    capacity_shift = scenario in {"benign-capacity-shift", "dos-udp-capacity-shift"}
    is_dos = scenario.startswith("dos-")
    rows: list[dict[str, object]] = []
    for index in range(120):
        attack_active = is_dos and index >= 50
        transition = is_dos and index == 50
        attack_exposure = 0.5 if transition else int(is_dos and index >= 51)
        traffic_phase = "transition" if transition else "attack" if attack_active else "benign"
        queue_drop = (is_dos and index == 50) or (
            scenario == "benign-capacity-shift" and index == 60
        )
        random_loss = scenario == "benign-random-loss" and index == 10
        dropped_before_bytes = 100 if queue_drop else 0
        dropped_before_packets = 1 if queue_drop else 0
        received_bytes = 1000
        received_packets = 1 + dropped_before_packets
        enqueued_bytes = received_bytes - dropped_before_bytes
        enqueued_packets = 1
        queue_start_bytes = index * 100
        queue_end_bytes = (index + 1) * 100
        dequeued_bytes = received_bytes - dropped_before_bytes - 100

        if capacity_shift and index == 59:
            capacity_start = 5_000_000
            capacity_end = 2_500_000
            capacity_integral = 62_500
        elif capacity_shift and index >= 60:
            capacity_start = 2_500_000
            capacity_end = 2_500_000
            capacity_integral = 31_250
        else:
            capacity_start = 5_000_000
            capacity_end = 5_000_000
            capacity_integral = 62_500

        rows.append(
            {
                "schema_version": "flow_probe_ns3_queue_v4",
                "scenario_id": scenario,
                "topology_id": "star-bottleneck-v1",
                "queue_model": "fifo-queue-disc",
                "group_id": f"star-bottleneck-v1|{scenario}|seed{seed}|run1",
                "seed": seed,
                "run": 1,
                "jitter_stream_base": 100,
                "jitter_max_ms": 40,
                "error_stream": 500,
                "downstream_error_rate": 0.01 if random_loss else 0,
                "window_index": index,
                "window_start_s": f"{index / 10:.1f}",
                "window_end_s": f"{(index + 1) / 10:.1f}",
                "is_attack": int(attack_active),
                "attack_exposure_fraction": attack_exposure,
                "traffic_phase": traffic_phase,
                "label_primary": "malicious" if attack_active else "benign",
                "label_family": "dos" if attack_active else "benign",
                "label_subtype": "udp" if attack_active else "benign",
                "capacity_start_bps": capacity_start,
                "capacity_end_bps": capacity_end,
                "configured_capacity_integral_link_bytes": capacity_integral,
                "queue_limit_packets": 50,
                "queue_start_l3_bytes": queue_start_bytes,
                "queue_end_l3_bytes": queue_end_bytes,
                "qdisc_received_l3_bytes": received_bytes,
                "qdisc_enqueued_l3_bytes": enqueued_bytes,
                "qdisc_dequeued_l3_bytes": dequeued_bytes,
                "qdisc_dropped_before_enqueue_l3_bytes": dropped_before_bytes,
                "qdisc_dropped_after_dequeue_l3_bytes": 0,
                "device_tx_drop_ppp_frame_bytes": 0,
                "downstream_error_loss_ppp_frame_bytes": 100 if random_loss else 0,
                "sink_received_app_payload_bytes": 777 if random_loss else 800,
                "queue_start_packets": 0,
                "queue_end_packets": 0,
                "qdisc_received_packets": received_packets,
                "qdisc_enqueued_packets": enqueued_packets,
                "qdisc_dequeued_packets": enqueued_packets,
                "qdisc_dropped_before_enqueue_packets": dropped_before_packets,
                "qdisc_dropped_after_dequeue_packets": 0,
                "device_tx_drop_packets": 0,
                "downstream_error_loss_packets": 1 if random_loss else 0,
                "sink_received_packets": 0 if random_loss else enqueued_packets,
                "queue_balance_residual_l3_bytes": 0,
                "queue_balance_residual_packets": 0,
            }
        )
    return rows


def _write_group(
    directory: Path,
    *,
    seed: int = 42,
    scenario: str = "benign-low",
    rows: list[dict[str, object]] | None = None,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{scenario}-seed{seed}-run1.csv"
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows if rows is not None else _rows(seed=seed, scenario=scenario))
    return path


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_one_complete_group_produces_117_samples_and_all_artifacts(tmp_path: Path) -> None:
    source = _write_group(tmp_path / "input")
    output_dir = tmp_path / "sequences"

    summary = _subject().build_ns3_sequences([source], output_dir)

    assert summary["candidate_count"] == 117
    assert summary["sample_count"] == 117
    assert summary["excluded_transition_count"] == 0
    assert {path.name for path in output_dir.iterdir()} == REQUIRED_ARTIFACTS
    assert len(_read_jsonl(output_dir / "train.jsonl")) == 117
    assert _read_jsonl(output_dir / "validation.jsonl") == []
    assert _read_jsonl(output_dir / "test.jsonl") == []

    statistics = _read_json(output_dir / "sample_statistics.json")
    assert statistics["total"] == {
        "candidate_count": 117,
        "retained_count": 117,
        "excluded_transition_count": 0,
    }
    assert statistics["splits"]["train"]["scenarios"]["benign-low"] == {
        "candidate_count": 117,
        "retained_count": 117,
        "excluded_transition_count": 0,
    }


def test_sequence_preserves_five_anchors_roles_and_raw_supervision(tmp_path: Path) -> None:
    source = _write_group(tmp_path / "input")
    output_dir = tmp_path / "sequences"
    roles = load_ns3_field_roles(FIELD_ROLES_PATH)

    _subject().build_ns3_sequences([source], output_dir)

    sample = _read_jsonl(output_dir / "train.jsonl")[0]
    assert sample["queue_boundary_anchors_l3_bytes"] == [0, 100, 200, 300, 400]
    assert set(sample["model_inputs"]) == set(roles["model_input_observable"])
    assert list(sample["model_inputs"]) == list(roles["model_input_observable"])
    assert all(len(values) == 4 for values in sample["model_inputs"].values())

    forbidden_inputs = set(roles["label_target"])
    forbidden_inputs.update(roles["split_metadata"])
    forbidden_inputs.update(roles["audit_only"])
    assert forbidden_inputs.isdisjoint(sample["model_inputs"])
    assert set(sample["label_targets"]) == set(roles["label_target"])
    assert set(sample["state_supervision"]) == set(roles["state_supervision"])
    assert sample["state_supervision"]["queue_start_l3_bytes"] == [0, 100, 200, 300]
    assert sample["state_supervision"]["queue_end_l3_bytes"] == [100, 200, 300, 400]
    assert sample["state_supervision"]["qdisc_dequeued_l3_bytes"] == [900] * 4
    assert sample["metadata"]["window_indices"] == [0, 1, 2, 3]
    assert sample["metadata"]["window_start_s"] == [0.0, 0.1, 0.2, 0.3]
    assert sample["metadata"]["window_end_s"] == [0.1, 0.2, 0.3, 0.4]


def test_normalization_uses_each_windows_own_capacity_integral(tmp_path: Path) -> None:
    source = _write_group(tmp_path / "input", scenario="benign-capacity-shift")
    output_dir = tmp_path / "sequences"

    _subject().build_ns3_sequences([source], output_dir)

    sample = next(
        item
        for item in _read_jsonl(output_dir / "train.jsonl")
        if item["metadata"]["window_indices"][0] == 58
    )
    assert sample["normalization_scale_configured_capacity_integral_link_bytes"] == [
        62_500,
        62_500,
        31_250,
        31_250,
    ]
    assert sample["normalized_physics"]["queue_start_l3_bytes"] == pytest.approx(
        [5800 / 62_500, 5900 / 62_500, 6000 / 31_250, 6100 / 31_250]
    )
    assert sample["normalized_physics"]["queue_end_l3_bytes"] == pytest.approx(
        [5900 / 62_500, 6000 / 62_500, 6100 / 31_250, 6200 / 31_250]
    )
    assert sample["normalized_physics"]["qdisc_received_l3_bytes"] == pytest.approx(
        [1000 / 62_500, 1000 / 62_500, 1000 / 31_250, 1000 / 31_250]
    )


def test_groups_never_cross_and_fixed_seed_splits_are_disjoint(tmp_path: Path) -> None:
    sources = [
        _write_group(tmp_path / "input", seed=seed)
        for seed in (42, 43, 44)
    ]
    output_dir = tmp_path / "sequences"

    summary = _subject().build_ns3_sequences(sources, output_dir)

    assert summary["sample_count"] == 351
    split_samples = {
        split: _read_jsonl(output_dir / f"{split}.jsonl")
        for split in ("train", "validation", "test")
    }
    expected_seed = {"train": 42, "validation": 43, "test": 44}
    for split, samples in split_samples.items():
        assert len(samples) == 117
        assert {sample["metadata"]["seed"] for sample in samples} == {expected_seed[split]}
        assert len({sample["group_id"] for sample in samples}) == 1
        assert all(
            end - start == 3
            for sample in samples
            for start, end in [
                (
                    sample["metadata"]["window_indices"][0],
                    sample["metadata"]["window_indices"][-1],
                )
            ]
        )

    split_manifest = _read_json(output_dir / "split_manifest.json")
    split_groups = {
        split: manifest["group_ids"]
        for split, manifest in split_manifest["splits"].items()
    }
    validate_group_disjoint_splits(split_groups)


def test_transition_window_excludes_all_four_overlapping_candidates(tmp_path: Path) -> None:
    source = _write_group(tmp_path / "input", scenario="dos-udp-high")
    output_dir = tmp_path / "sequences"

    summary = _subject().build_ns3_sequences([source], output_dir)

    samples = _read_jsonl(output_dir / "train.jsonl")
    assert summary["candidate_count"] == 117
    assert summary["excluded_transition_count"] == 4
    assert summary["sample_count"] == 113
    assert len(samples) == 113
    assert all("transition" not in sample["label_targets"]["traffic_phase"] for sample in samples)
    assert {47, 48, 49, 50}.isdisjoint(
        {sample["metadata"]["window_indices"][0] for sample in samples}
    )


@pytest.mark.parametrize(
    ("mutation", "expected_rule"),
    [
        (lambda rows: rows[5].update(window_index=7), "窗口索引"),
        (lambda rows: rows[5].update(window_start_s="0.51"), "绝对时间"),
    ],
)
def test_broken_index_or_time_fails_with_source_context(
    tmp_path: Path,
    mutation,
    expected_rule: str,
) -> None:
    rows = _rows()
    mutation(rows)
    source = _write_group(tmp_path / "input", rows=rows)
    output_dir = tmp_path / "sequences"
    subject = _subject()

    with pytest.raises(subject.NS3SequenceBuildError, match=expected_rule) as captured:
        subject.build_ns3_sequences([source], output_dir)

    assert str(source) in str(captured.value)
    assert captured.value.__cause__ is not None
    console_log = (output_dir / "console.log").read_text(encoding="utf-8")
    assert str(source) in console_log
    assert expected_rule in console_log


@pytest.mark.parametrize("invalid_capacity", [0, -1])
def test_nonpositive_capacity_integral_fails_without_silent_drop(
    tmp_path: Path,
    invalid_capacity: int,
) -> None:
    rows = _rows()
    rows[5]["configured_capacity_integral_link_bytes"] = invalid_capacity
    source = _write_group(tmp_path / "input", rows=rows)
    output_dir = tmp_path / "sequences"
    subject = _subject()

    with pytest.raises(subject.NS3SequenceBuildError, match="容量"):
        subject.build_ns3_sequences([source], output_dir)

    assert "容量" in (output_dir / "console.log").read_text(encoding="utf-8")


def test_source_hash_manifest_mismatch_fails_with_context(tmp_path: Path) -> None:
    input_root = tmp_path / "input"
    source = _write_group(input_root / "csv")
    manifest = {
        "schema_version": "flow_probe_ns3_csv_sha256_v1",
        "files": [
            {
                "group_id": "star-bottleneck-v1|benign-low|seed42|run1",
                "path": f"/remote/input/csv/{source.name}",
                "sha256": "0" * 64,
            }
        ],
    }
    (input_root / "csv_sha256.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
    )
    output_dir = tmp_path / "sequences"
    subject = _subject()

    with pytest.raises(subject.NS3SequenceBuildError, match="SHA-256") as captured:
        subject.build_ns3_sequences([source], output_dir)

    assert source.name in str(captured.value)
    assert "SHA-256" in (output_dir / "console.log").read_text(encoding="utf-8")


def test_source_hash_and_artifact_manifests_are_traceable(tmp_path: Path) -> None:
    source = _write_group(tmp_path / "input")
    output_dir = tmp_path / "sequences"

    _subject().build_ns3_sequences([source], output_dir)

    expected_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    source_manifest = _read_json(output_dir / "source_csv_sha256.json")
    assert source_manifest["files"] == [
        {
            "group_id": "star-bottleneck-v1|benign-low|seed42|run1",
            "path": str(source.resolve()),
            "sha256": expected_sha256,
        }
    ]
    samples = _read_jsonl(output_dir / "train.jsonl")
    assert {sample["source_csv_sha256"] for sample in samples} == {expected_sha256}

    artifact_manifest = _read_json(output_dir / "artifact_manifest.json")
    artifact_entries = {entry["path"]: entry for entry in artifact_manifest["artifacts"]}
    assert REQUIRED_ARTIFACTS - {"artifact_manifest.json"} == set(artifact_entries)
    for relative_path, entry in artifact_entries.items():
        artifact_path = output_dir / relative_path
        assert entry["sha256"] == hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        assert entry["size_bytes"] == artifact_path.stat().st_size


def test_output_directory_cannot_be_reused(tmp_path: Path) -> None:
    source = _write_group(tmp_path / "input")
    output_dir = tmp_path / "sequences"
    output_dir.mkdir()
    sentinel = output_dir / "sentinel.txt"
    sentinel.write_text("不得覆盖", encoding="utf-8")
    subject = _subject()

    with pytest.raises(subject.NS3SequenceBuildError, match="输出目录.*已存在"):
        subject.build_ns3_sequences([source], output_dir)

    assert sentinel.read_text(encoding="utf-8") == "不得覆盖"


def test_horizon_is_fixed_at_four(tmp_path: Path) -> None:
    source = _write_group(tmp_path / "input")
    subject = _subject()

    with pytest.raises(subject.NS3SequenceBuildError, match="horizon.*4"):
        subject.build_ns3_sequences([source], tmp_path / "sequences", horizon=3)


def test_fixed_command_entry_and_executable_shell_wrapper() -> None:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert (
        project["project"]["scripts"]["flow-probe-build-ns3-sequences"]
        == "flow_probe.ns3_sequences:main"
    )
    assert SHELL_SCRIPT.is_file()
    assert os.access(SHELL_SCRIPT, os.X_OK)
