"""TQH-C2 A/B/C 统一候选协议的隔离夹具测试。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml

from flow_probe.frozen_protocol import load_frozen_protocol
from flow_probe.tqh_c2_candidate import MODEL_FEATURE_FIELDS
from flow_probe.tqh_c2_candidate_abc import (
    DATASET_VERSION,
    PROTOCOL_PHASE,
    PROTOCOL_STATUS,
    PROTOCOL_VERSION,
    TQHC2ABCCandidateError,
    materialize_candidate_abc,
)

PROFILES = ("A", "B", "C")
INTERVALS = (30, 300, 1800, 3600)
JITTERS = (0, 30, 70)
APPROVED_INPUT_IDS = {
    "A": "tqh-c2-A-20260728-v1",
    "B": "tqh-c2-B-20260728-v1",
    "C": "tqh-c2-C-20260724-v8",
}
APPROVED_SUITES = (
    "tqhc2_cell_indomain",
    "tqhc2_leave_one_profile_out_A",
    "tqhc2_leave_one_profile_out_B",
    "tqhc2_leave_one_profile_out_C",
)
APPROVED_CELL_COUNTS = {
    "tqhc2_cell_indomain": {"train": 28, "validation": 4, "test": 4},
    "tqhc2_leave_one_profile_out_A": {"train": 20, "validation": 4, "test": 12},
    "tqhc2_leave_one_profile_out_B": {"train": 20, "validation": 4, "test": 12},
    "tqhc2_leave_one_profile_out_C": {"train": 20, "validation": 4, "test": 12},
}
APPROVED_SPLIT_FILES = {
    f"splits/{suite_id}-{split_id}.jsonl"
    for suite_id in APPROVED_SUITES
    for split_id in ("train", "validation", "test")
}
UPSTREAM_ARTIFACTS = (
    "master_records.parquet",
    "views/packet_observations.parquet",
    "source_checksums.json",
    "run_manifest.provisional.json",
    "schema.provisional.json",
    "audit/cell-audit.json",
    "audit/label-coverage.json",
    "audit/leakage-audit.json",
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _profile_rows(profile: str) -> tuple[list[dict[str, object]], list[list[dict[str, object]]]]:
    master_rows: list[dict[str, object]] = []
    packet_cells: list[list[dict[str, object]]] = []
    sequence = 0
    for interval_s in INTERVALS:
        for jitter_pct in JITTERS:
            capture_group_id = f"{profile}_i{interval_s}_j{jitter_pct}"
            source_capture_sha256 = _digest(f"pcap:{capture_group_id}")
            allocation_group_id = _digest(f"allocation:{capture_group_id}")
            labels: tuple[tuple[str, str | None, str], ...] = (
                ("benign", "benign", "mapped"),
                ("malicious_c2", "malicious", "mapped"),
                ("unknown", None, "unresolved"),
            )
            cell_packets: list[dict[str, object]] = []
            for local_index, (native_label, binary_label, label_status) in enumerate(labels):
                sample_id = _digest(f"sample:{capture_group_id}:{local_index}")
                start_ns = 1_000_000_000 + sequence * 1_000_000
                master_rows.append(
                    {
                        "sample_id": sample_id,
                        "record_sha256": _digest(f"record:{sample_id}"),
                        "dataset_id": "TQH-C2",
                        "dataset_version": DATASET_VERSION,
                        "source_artifact_id": _digest(f"source:{capture_group_id}"),
                        "source_capture_sha256": source_capture_sha256,
                        "extractor_contract_sha256": _digest("extractor"),
                        "allocation_group_id": allocation_group_id,
                        "parent_session_id": f"uid-{profile}-{sequence}",
                        "capture_group_id": capture_group_id,
                        "sample_unit": "full_flow",
                        "window_start_ns": start_ns,
                        "window_end_ns": start_ns + 2_000_000,
                        "window_ordinal": 0,
                        "packet_count_raw": 2,
                        "packet_count_kept": 2,
                        "native_label": native_label,
                        "binary_label": binary_label,
                        "family_label": "c2" if native_label == "malicious_c2" else None,
                        "subtype_label": (
                            f"profile_{profile.lower()}" if native_label == "malicious_c2" else None
                        ),
                        "label_status": label_status,
                        "unknown_role": "unresolved" if native_label == "unknown" else None,
                        "profile": profile,
                        "interval_s": interval_s,
                        "jitter_pct": jitter_pct,
                        "capture_id": f"capture-{capture_group_id}",
                        "join_status": "matched_packets",
                    }
                )
                for packet_index in range(2):
                    is_tcp = local_index % 2 == 0
                    cell_packets.append(
                        {
                            "sample_id": sample_id,
                            "packet_index": packet_index,
                            "relative_time_ns": packet_index * (10_000 + sequence),
                            "delta_time_us": packet_index * (10 + sequence),
                            "direction": 1 if packet_index == 0 else -1,
                            "network_length_bytes": 100 + sequence + packet_index,
                            "payload_length_bytes": 40 + local_index + packet_index,
                            "transport_family": "TCP" if is_tcp else "UDP",
                            "tcp_flags": 0x12 if is_tcp else None,
                            "burst_id": packet_index,
                            "is_first_packet": packet_index == 0,
                            "payload_length_observed": True,
                            "tcp_flags_applicable": is_tcp,
                            "truncation_mask": False,
                        }
                    )
                sequence += 1
            packet_cells.append(cell_packets)
    return master_rows, packet_cells


def _write_packet_row_groups(path: Path, packet_cells: list[list[dict[str, object]]]) -> None:
    all_rows = [row for cell in packet_cells for row in cell]
    schema = pa.Table.from_pylist(all_rows).schema
    with pq.ParquetWriter(path, schema, compression="zstd") as writer:
        for cell in packet_cells:
            writer.write_table(pa.Table.from_pylist(cell, schema=schema))


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _refresh_upstream_artifact_manifest(root: Path) -> str:
    document = {
        "files": [
            {
                "path": relative_path,
                "sha256": _file_digest(root / relative_path),
                "size_bytes": (root / relative_path).stat().st_size,
            }
            for relative_path in UPSTREAM_ARTIFACTS
        ],
        "status": "provisional",
    }
    path = root / "artifact_checksums.provisional.json"
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
    return _file_digest(path)


def _write_profile_fixture(root: Path, profile: str) -> dict[str, object]:
    (root / "views").mkdir(parents=True)
    (root / "audit").mkdir()
    master_rows, packet_cells = _profile_rows(profile)
    packet_count = sum(len(cell) for cell in packet_cells)
    extractor_sha256 = _digest("extractor")
    pd.DataFrame(master_rows).to_parquet(root / "master_records.parquet", index=False)
    _write_packet_row_groups(root / "views" / "packet_observations.parquet", packet_cells)
    (root / "run_manifest.provisional.json").write_text(
        json.dumps(
            {
                "cell_count": 12,
                "dataset_id": "TQH-C2",
                "dataset_version": DATASET_VERSION,
                "extractor_contract_sha256": extractor_sha256,
                "master_record_count": len(master_rows),
                "packet_record_count": packet_count,
                "profile": profile,
                "status": "provisional",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "source_checksums.json").write_text(
        json.dumps({"files": []}, sort_keys=True) + "\n", encoding="utf-8"
    )
    (root / "schema.provisional.json").write_text(
        json.dumps({"status": "provisional"}, sort_keys=True) + "\n", encoding="utf-8"
    )
    capture_groups = sorted({str(row["capture_group_id"]) for row in master_rows})
    (root / "audit" / "cell-audit.json").write_text(
        json.dumps(
            {
                "cells": [
                    {"capture_group_id": capture_group_id} for capture_group_id in capture_groups
                ],
                "profile": profile,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "audit" / "label-coverage.json").write_text(
        json.dumps({"record_count": len(master_rows)}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "audit" / "leakage-audit.json").write_text(
        json.dumps({"status": "pass"}, sort_keys=True) + "\n", encoding="utf-8"
    )
    artifact_sha256 = _refresh_upstream_artifact_manifest(root)
    return {
        "input_id": APPROVED_INPUT_IDS[profile],
        "artifact_checksums_sha256": artifact_sha256,
        "extractor_contract_sha256": extractor_sha256,
        "master_record_count": len(master_rows),
        "packet_record_count": packet_count,
    }


def _write_abc_fixture(
    root: Path,
) -> tuple[dict[str, Path], dict[str, dict[str, object]]]:
    profile_dirs = {profile: root / f"profile-{profile}" for profile in PROFILES}
    approved_inputs: dict[str, dict[str, object]] = {}
    for profile, profile_dir in profile_dirs.items():
        approved_inputs[profile] = _write_profile_fixture(profile_dir, profile)
    return profile_dirs, approved_inputs


def _artifact_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _materialize(
    profile_dirs: dict[str, Path],
    approved_inputs: dict[str, dict[str, object]],
    output_dir: Path,
) -> dict[str, object]:
    return materialize_candidate_abc(
        profile_dirs=profile_dirs,
        approved_inputs=approved_inputs,
        output_dir=output_dir,
    )


def _reapprove_artifacts(
    profile_dirs: dict[str, Path],
    approved_inputs: dict[str, dict[str, object]],
    profile: str,
) -> None:
    approved_inputs[profile]["artifact_checksums_sha256"] = _refresh_upstream_artifact_manifest(
        profile_dirs[profile]
    )


def test_materialize_abc_builds_approved_hard_coverage_suites(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    output_dir = tmp_path / "candidate" / "protocol"

    result = _materialize(profile_dirs, approved_inputs, output_dir)

    assert result["sample_count"] == 72
    assert result["cell_count"] == 36
    assert result["suite_count"] == 4
    assert result["manifest_count"] == 12
    assert result["row_group_count"] == 36
    assert not (output_dir / "_INCOMPLETE").exists()
    document = yaml.safe_load((output_dir / "protocol.yaml").read_text(encoding="utf-8"))
    assert document["status"] == PROTOCOL_STATUS
    assert document["phase"] == PROTOCOL_PHASE
    assert document["review_status"] == "review_pending"
    assert document["suite_ids"] == list(APPROVED_SUITES)

    protocol = load_frozen_protocol(
        output_dir,
        expected_protocol_version=PROTOCOL_VERSION,
        expected_status=PROTOCOL_STATUS,
        expected_phase=PROTOCOL_PHASE,
    )
    assert tuple(protocol.model_views["tree_flat_view"].feature_fields) == MODEL_FEATURE_FIELDS
    assert set(protocol.manifests) == APPROVED_SPLIT_FILES
    for suite_id in APPROVED_SUITES:
        suite_manifests = [
            manifest for manifest in protocol.manifests.values() if manifest.suite_id == suite_id
        ]
        assert len(suite_manifests) == 3
        sample_ids = [
            sample_id for manifest in suite_manifests for sample_id in manifest.sample_ids
        ]
        assert len(sample_ids) == 72
        assert len(set(sample_ids)) == 72
        for manifest in suite_manifests:
            split = protocol.load_tabular_split(manifest.relative_path)
            assert split.features.shape[1] == 37
            assert set(split.labels) == {"benign", "malicious"}

    samples = pd.read_parquet(output_dir / "samples.parquet")
    groups = pd.read_parquet(output_dir / "groups.parquet")
    assert samples["sample_id"].is_unique
    assert set(samples["native_label"]) == {"benign", "malicious_c2"}
    assert len(groups) == 144
    for suite_id, frame in groups.groupby("suite_id"):
        assert Counter(frame["split_id"]) == Counter(APPROVED_CELL_COUNTS[suite_id])
        assert frame["capture_group_id"].is_unique

    suite_audits = json.loads((output_dir / "audit" / "suite-audits.json").read_text())
    for suite_id, audit in suite_audits.items():
        assert audit["status"] == "pass"
        assert set(audit["target_sample_fractions"]) == {"train", "validation", "test"}
        assert audit["l1_sample_fraction_deviation"] >= 0
        conditions = audit["split_conditions"]
        if suite_id == "tqhc2_cell_indomain":
            for split_id in ("validation", "test"):
                assert conditions[split_id]["profiles"] == ["A", "B", "C"]
                assert conditions[split_id]["intervals"] == [30, 300, 1800, 3600]
        else:
            held_out = suite_id[-1]
            assert conditions["validation"]["profiles"] == sorted(
                {"A", "B", "C"}.difference({held_out})
            )
            assert conditions["validation"]["intervals"] == [30, 300, 1800, 3600]
            assert conditions["test"]["profiles"] == [held_out]
            assert conditions["test"]["cell_count"] == 12

    samples_sha256 = protocol.samples_sha256
    for relative_path in APPROVED_SPLIT_FILES:
        rows = [
            json.loads(line)
            for line in (output_dir / relative_path).read_text(encoding="utf-8").splitlines()
        ]
        assert {row["samples_sha256"] for row in rows} == {samples_sha256}
    streaming = json.loads((output_dir / "audit" / "streaming-audit.json").read_text())
    assert streaming["packet_table_loaded_whole"] is False
    assert streaming["all_row_groups_single_cell"] is True
    assert streaming["all_cell_row_groups_contiguous"] is True
    assert streaming["cell_order_fallback_detected"] is False


def test_materialize_abc_is_byte_reproducible_and_refuses_overwrite(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    first = tmp_path / "first" / "protocol"
    second = tmp_path / "second" / "protocol"

    _materialize(profile_dirs, approved_inputs, first)
    _materialize(profile_dirs, approved_inputs, second)

    assert _artifact_bytes(first) == _artifact_bytes(second)
    with pytest.raises(TQHC2ABCCandidateError, match="拒绝覆盖"):
        _materialize(profile_dirs, approved_inputs, first)


def test_materialize_abc_rejects_unregistered_upstream_change(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    master_path = profile_dirs["A"] / "master_records.parquet"
    master = pd.read_parquet(master_path)
    master.loc[0, "binary_label"] = "malicious"
    master.to_parquet(master_path, index=False)

    with pytest.raises(TQHC2ABCCandidateError, match="大小或 SHA-256 不一致"):
        _materialize(profile_dirs, approved_inputs, tmp_path / "candidate" / "protocol")


def test_materialize_abc_rejects_manifest_count_not_bound_to_approval(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    path = profile_dirs["B"] / "run_manifest.provisional.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["master_record_count"] += 1
    path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    _reapprove_artifacts(profile_dirs, approved_inputs, "B")

    with pytest.raises(TQHC2ABCCandidateError, match="主记录数未绑定批准配置"):
        _materialize(profile_dirs, approved_inputs, tmp_path / "candidate" / "protocol")


def test_materialize_abc_rejects_extractor_mismatch(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    master_path = profile_dirs["C"] / "master_records.parquet"
    master = pd.read_parquet(master_path)
    master.loc[0, "extractor_contract_sha256"] = _digest("wrong-extractor")
    master.to_parquet(master_path, index=False)
    _reapprove_artifacts(profile_dirs, approved_inputs, "C")

    with pytest.raises(TQHC2ABCCandidateError, match="主记录提取器哈希"):
        _materialize(profile_dirs, approved_inputs, tmp_path / "candidate" / "protocol")


def test_materialize_abc_rejects_incomplete_four_by_three_grid(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    master_path = profile_dirs["A"] / "master_records.parquet"
    master = pd.read_parquet(master_path)
    target_cell = master["capture_group_id"].eq("A_i30_j0")
    master.loc[target_cell, "jitter_pct"] = 30
    master.to_parquet(master_path, index=False)
    _reapprove_artifacts(profile_dirs, approved_inputs, "A")

    with pytest.raises(TQHC2ABCCandidateError, match="固定 4×3 cell 网格"):
        _materialize(profile_dirs, approved_inputs, tmp_path / "candidate" / "protocol")


def test_materialize_abc_rejects_row_group_with_multiple_cells(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    packet_path = profile_dirs["A"] / "views" / "packet_observations.parquet"
    packets = pd.read_parquet(packet_path)
    packets.to_parquet(packet_path, index=False)
    _reapprove_artifacts(profile_dirs, approved_inputs, "A")
    output_dir = tmp_path / "candidate" / "protocol"

    with pytest.raises(TQHC2ABCCandidateError, match="行组混入多个 cell"):
        _materialize(profile_dirs, approved_inputs, output_dir)
    assert (output_dir / "_INCOMPLETE").is_file()


def test_materialize_abc_rejects_cell_order_fallback(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    _, cells = _profile_rows("A")
    reordered = [cells[0][:2], cells[1], cells[0][2:], *cells[2:]]
    packet_path = profile_dirs["A"] / "views" / "packet_observations.parquet"
    _write_packet_row_groups(packet_path, reordered)
    _reapprove_artifacts(profile_dirs, approved_inputs, "A")
    output_dir = tmp_path / "candidate" / "protocol"

    with pytest.raises(TQHC2ABCCandidateError, match="cell_order_fallback"):
        _materialize(profile_dirs, approved_inputs, output_dir)
    assert (output_dir / "_INCOMPLETE").is_file()


def test_materialize_abc_accepts_sample_across_adjacent_row_groups(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    _, cells = _profile_rows("A")
    adjacent = [cells[0][:1], cells[0][1:], *cells[1:]]
    packet_path = profile_dirs["A"] / "views" / "packet_observations.parquet"
    _write_packet_row_groups(packet_path, adjacent)
    _reapprove_artifacts(profile_dirs, approved_inputs, "A")

    result = _materialize(profile_dirs, approved_inputs, tmp_path / "candidate" / "protocol")

    assert result["row_group_count"] == 37


def test_materialize_abc_rejects_noncontiguous_sample_reappearance(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    _, cells = _profile_rows("A")
    noncontiguous = [cells[0][:2], cells[0][2:4], cells[0][:1], cells[0][4:], *cells[1:]]
    packet_path = profile_dirs["A"] / "views" / "packet_observations.parquet"
    _write_packet_row_groups(packet_path, noncontiguous)
    manifest_path = profile_dirs["A"] / "run_manifest.provisional.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["packet_record_count"] += 1
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    approved_inputs["A"]["packet_record_count"] += 1
    _reapprove_artifacts(profile_dirs, approved_inputs, "A")
    output_dir = tmp_path / "candidate" / "protocol"

    with pytest.raises(TQHC2ABCCandidateError, match="sample_id 在包表中非连续重现"):
        _materialize(profile_dirs, approved_inputs, output_dir)
    assert (output_dir / "_INCOMPLETE").is_file()


def test_materialize_abc_rejects_cross_profile_sample_id_collision(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    a_master = pd.read_parquet(profile_dirs["A"] / "master_records.parquet")
    b_master_path = profile_dirs["B"] / "master_records.parquet"
    b_master = pd.read_parquet(b_master_path)
    b_master.loc[0, "sample_id"] = a_master.loc[0, "sample_id"]
    b_master.to_parquet(b_master_path, index=False)
    _reapprove_artifacts(profile_dirs, approved_inputs, "B")

    with pytest.raises(TQHC2ABCCandidateError, match="sample_id 冲突"):
        _materialize(profile_dirs, approved_inputs, tmp_path / "candidate" / "protocol")


def test_materialize_abc_rejects_invalid_label_contract(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    master_path = profile_dirs["C"] / "master_records.parquet"
    master = pd.read_parquet(master_path)
    benign_index = master.index[master["native_label"].eq("benign")][0]
    master.loc[benign_index, "binary_label"] = "malicious"
    master.to_parquet(master_path, index=False)
    _reapprove_artifacts(profile_dirs, approved_inputs, "C")

    with pytest.raises(TQHC2ABCCandidateError, match="标签映射不符合固定契约"):
        _materialize(profile_dirs, approved_inputs, tmp_path / "candidate" / "protocol")


def test_materialize_abc_rejects_packet_count_mismatch(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    master_path = profile_dirs["B"] / "master_records.parquet"
    master = pd.read_parquet(master_path)
    master.loc[0, "packet_count_kept"] = 3
    master.to_parquet(master_path, index=False)
    _reapprove_artifacts(profile_dirs, approved_inputs, "B")

    with pytest.raises(TQHC2ABCCandidateError, match="包观测计数或序号"):
        _materialize(profile_dirs, approved_inputs, tmp_path / "candidate" / "protocol")


def test_materialize_abc_rejects_wrong_dataset_version(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    manifest_path = profile_dirs["A"] / "run_manifest.provisional.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["dataset_version"] = "1.0.0"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    _reapprove_artifacts(profile_dirs, approved_inputs, "A")

    with pytest.raises(TQHC2ABCCandidateError, match="运行清单.*合同不一致"):
        _materialize(profile_dirs, approved_inputs, tmp_path / "candidate" / "protocol")
