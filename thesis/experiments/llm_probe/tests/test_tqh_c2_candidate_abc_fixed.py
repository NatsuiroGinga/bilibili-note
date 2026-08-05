"""TQH-C2 A/B/C 固定预算物化器测试。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml
from test_tqh_c2_candidate_abc import (
    APPROVED_CELL_COUNTS,
    APPROVED_SPLIT_FILES,
    APPROVED_SUITES,
    _artifact_bytes,
    _refresh_upstream_artifact_manifest,
    _write_abc_fixture,
)

from flow_probe.frozen_protocol import load_frozen_protocol
from flow_probe.tqh_c2_candidate import MODEL_FEATURE_FIELDS, _aggregate_features
from flow_probe.tqh_c2_candidate_abc import _build_base_groups
from flow_probe.tqh_c2_candidate_abc_fixed import (
    BUDGET_SAMPLING_ALGORITHM,
    CANDIDATE_ID,
    PROTOCOL_PHASE,
    PROTOCOL_STATUS,
    PROTOCOL_VERSION,
    TQHC2ABCFixedError,
    filter_and_aggregate_budget_packets,
    load_fixed_suite_groups,
    materialize_candidate_abc_budget,
    select_budget_samples,
)

CHECKED_IN_ASSIGNMENT = (
    Path(__file__).resolve().parents[1] / "configs" / "tqhc2_abc_fixed_assignment_v1.json"
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fixed_split(suite_id: str, profile: str, interval_s: int, jitter_pct: int) -> str:
    key = (profile, interval_s, jitter_pct)
    if suite_id == "tqhc2_cell_indomain":
        validation = {
            ("A", 30, 0),
            ("B", 300, 30),
            ("C", 1800, 70),
            ("A", 3600, 30),
        }
        test = {
            ("B", 30, 70),
            ("C", 300, 0),
            ("A", 1800, 30),
            ("B", 3600, 0),
        }
        return "validation" if key in validation else "test" if key in test else "train"
    held_out = suite_id.rsplit("_", 1)[-1]
    if profile == held_out:
        return "test"
    sources = sorted({"A", "B", "C"}.difference({held_out}))
    validation = {
        (sources[0], 30, 0),
        (sources[1], 300, 30),
        (sources[0], 1800, 70),
        (sources[1], 3600, 0),
    }
    return "validation" if key in validation else "train"


def _assignment_document(base_groups: pd.DataFrame) -> dict[str, object]:
    cell_fields = (
        "allocation_group_id",
        "capture_group_id",
        "profile",
        "interval_s",
        "jitter_pct",
        "source_capture_sha256",
        "mapped_count",
        "benign_count",
        "malicious_count",
    )
    cells = base_groups.loc[:, list(cell_fields)].sort_values("capture_group_id")
    suites = []
    for suite_id in APPROVED_SUITES:
        held_out = None if suite_id == "tqhc2_cell_indomain" else suite_id.rsplit("_", 1)[-1]
        assignments = []
        for row in cells.itertuples(index=False):
            split_id = _fixed_split(
                suite_id, str(row.profile), int(row.interval_s), int(row.jitter_pct)
            )
            assignments.append(
                {
                    "capture_group_id": str(row.capture_group_id),
                    "domain_role": (
                        "in_domain"
                        if held_out is None
                        else (
                            "held_out_profile" if str(row.profile) == held_out else "source_profile"
                        )
                    ),
                    "split_id": split_id,
                }
            )
        suites.append(
            {
                "assignments": assignments,
                "held_out_profile": held_out,
                "suite_id": suite_id,
            }
        )
    return {
        "budget": {
            "cap_per_cell": 1000,
            "expected_packet_count": None,
            "expected_sample_count": None,
            "sampling_algorithm": BUDGET_SAMPLING_ALGORITHM,
            "source_mapped_sample_count": int(cells["mapped_count"].sum()),
        },
        "cells": cells.to_dict(orient="records"),
        "generation": {
            "candidate_id": "dataset-candidate-tqhc2-abc-v0",
            "method": "一次受约束组合搜索后冻结",
        },
        "schema_version": "tqhc2-abc-fixed-assignment-v1",
        "suites": suites,
    }


def _write_assignment(path: Path, base_groups: pd.DataFrame) -> Path:
    path.write_text(
        json.dumps(_assignment_document(base_groups), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return path


def _grid_master(rows_per_label: int = 3) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for profile in ("A", "B", "C"):
        for interval_s in (30, 300, 1800, 3600):
            for jitter_pct in (0, 30, 70):
                cell = f"{profile}_i{interval_s}_j{jitter_pct}"
                for label in ("benign", "malicious"):
                    for index in range(rows_per_label):
                        sample_id = _digest(f"{cell}:{label}:{index}")
                        rows.append(
                            {
                                "allocation_group_id": _digest(f"allocation:{cell}"),
                                "binary_label": label,
                                "capture_group_id": cell,
                                "interval_s": interval_s,
                                "jitter_pct": jitter_pct,
                                "label_status": "mapped",
                                "packet_count_kept": index + 1,
                                "profile": profile,
                                "sample_id": sample_id,
                                "source_capture_sha256": _digest(f"pcap:{cell}"),
                            }
                        )
    return pd.DataFrame(rows)


def _base_groups(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cell, frame in master.groupby("capture_group_id", sort=True):
        counts = Counter(frame["binary_label"])
        rows.append(
            {
                "allocation_group_id": str(frame["allocation_group_id"].iloc[0]),
                "capture_group_id": str(cell),
                "profile": str(frame["profile"].iloc[0]),
                "interval_s": int(frame["interval_s"].iloc[0]),
                "jitter_pct": int(frame["jitter_pct"].iloc[0]),
                "source_capture_sha256": str(frame["source_capture_sha256"].iloc[0]),
                "record_count": len(frame),
                "mapped_count": len(frame),
                "auxiliary_count": 0,
                "unresolved_count": 0,
                "benign_count": counts["benign"],
                "malicious_count": counts["malicious"],
            }
        )
    return pd.DataFrame(rows)


def test_load_fixed_suite_groups_validates_all_four_suites(tmp_path: Path) -> None:
    base_groups = _base_groups(_grid_master())
    assignment = _write_assignment(tmp_path / "assignment.json", base_groups)

    groups, audits = load_fixed_suite_groups(assignment, base_groups)

    assert len(groups) == 144
    assert len(audits) == 4
    for suite_id, frame in groups.groupby("suite_id"):
        assert Counter(frame["split_id"]) == Counter(APPROVED_CELL_COUNTS[suite_id])
        assert frame["capture_group_id"].is_unique
    assert {audit["status"] for audit in audits} == {"pass"}


def test_checked_in_assignment_satisfies_real_coverage_contract() -> None:
    document = json.loads(CHECKED_IN_ASSIGNMENT.read_text(encoding="utf-8"))
    base_groups = pd.DataFrame(document["cells"])

    groups, audits = load_fixed_suite_groups(CHECKED_IN_ASSIGNMENT, base_groups)

    assert len(groups) == 144
    assert len(audits) == 4
    indomain = groups[groups["suite_id"].eq("tqhc2_cell_indomain")]
    for split_id in ("validation", "test"):
        split = indomain[indomain["split_id"].eq(split_id)]
        assert set(split["profile"]) == {"A", "B", "C"}
        assert set(split["interval_s"]) == {30, 300, 1800, 3600}
        assert set(split["jitter_pct"]) == {0, 30, 70}


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing", "cell 集合"),
        ("extra", "cell 集合"),
        ("duplicate", "重复"),
        ("wrong_held_out", "留出 profile"),
        ("coverage", "硬覆盖"),
    ],
)
def test_load_fixed_suite_groups_rejects_invalid_assignment(
    tmp_path: Path, mutation: str, message: str
) -> None:
    base_groups = _base_groups(_grid_master())
    document = _assignment_document(base_groups)
    cells = document["cells"]
    suites = document["suites"]
    if mutation == "missing":
        cells.pop()
    elif mutation == "extra":
        cells.append({**cells[0], "capture_group_id": "extra"})
    elif mutation == "duplicate":
        suites[0]["assignments"][-1] = dict(suites[0]["assignments"][0])
    elif mutation == "wrong_held_out":
        suites[1]["held_out_profile"] = "B"
    else:
        target = next(row for row in suites[0]["assignments"] if row["split_id"] == "validation")
        target["split_id"] = "train"
    path = tmp_path / "assignment.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(TQHC2ABCFixedError, match=message):
        load_fixed_suite_groups(path, base_groups)


def test_select_budget_samples_uses_largest_remainder_and_lexical_tie() -> None:
    master = _grid_master(rows_per_label=1).iloc[:0].copy()
    rows = []
    for label, count in (("benign", 3), ("malicious", 3)):
        for index in range(count):
            rows.append(
                {
                    "allocation_group_id": _digest("allocation:cell"),
                    "binary_label": label,
                    "capture_group_id": "cell",
                    "interval_s": 30,
                    "jitter_pct": 0,
                    "label_status": "mapped",
                    "packet_count_kept": 1,
                    "profile": "A",
                    "sample_id": _digest(f"{label}:{index}"),
                    "source_capture_sha256": _digest("pcap:cell"),
                }
            )
    master = pd.concat([master, pd.DataFrame(rows)], ignore_index=True)

    selected, audit = select_budget_samples(master, cap_per_cell=5)

    assert Counter(selected["binary_label"]) == Counter({"benign": 3, "malicious": 2})
    assert audit["cells"][0]["quotas"] == {"benign": 3, "malicious": 2}


def test_select_budget_samples_keeps_small_cells_and_is_reproducible() -> None:
    master = _grid_master(rows_per_label=3)

    first, first_audit = select_budget_samples(master, cap_per_cell=1000)
    second, second_audit = select_budget_samples(master.sample(frac=1, random_state=7), 1000)

    assert len(first) == len(master)
    assert first.to_json(orient="records") == second.to_json(orient="records")
    assert first_audit["sample_manifest_sha256"] == second_audit["sample_manifest_sha256"]
    assert first_audit["sampling_algorithm"] == BUDGET_SAMPLING_ALGORITHM


def _packet(sample_id: str, packet_index: int, *, cell: str) -> dict[str, object]:
    return {
        "sample_id": sample_id,
        "packet_index": packet_index,
        "relative_time_ns": packet_index * 10_000,
        "delta_time_us": 0 if packet_index == 0 else 10,
        "direction": 1 if packet_index % 2 == 0 else -1,
        "network_length_bytes": 100 + packet_index,
        "payload_length_bytes": 50 + packet_index,
        "transport_family": "TCP",
        "tcp_flags": 0x12,
        "burst_id": packet_index,
        "is_first_packet": packet_index == 0,
        "payload_length_observed": True,
        "tcp_flags_applicable": True,
        "truncation_mask": False,
        "capture_group_id": cell,
    }


def _write_packet_groups(path: Path, groups: list[list[dict[str, object]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {key: value for key, value in row.items() if key != "capture_group_id"} for row in groups[0]
    ]
    schema = pa.Table.from_pylist(rows).schema
    with pq.ParquetWriter(path, schema, compression="zstd") as writer:
        for group in groups:
            values = [
                {key: value for key, value in row.items() if key != "capture_group_id"}
                for row in group
            ]
            writer.write_table(pa.Table.from_pylist(values, schema=schema))


def _packet_fixture(
    root: Path,
    a_groups: list[list[dict[str, object]]],
) -> tuple[pd.DataFrame, dict[str, Path]]:
    profile_dirs: dict[str, Path] = {}
    budget_rows = []
    all_a = [row for group in a_groups for row in group]
    a_ids = sorted({str(row["sample_id"]) for row in all_a})
    for profile in ("A", "B", "C"):
        profile_dir = root / profile
        profile_dirs[profile] = profile_dir
        if profile == "A":
            groups = a_groups
            sample_ids = a_ids
            cell = str(a_groups[0][0]["capture_group_id"])
        else:
            cell = f"{profile}_cell"
            sample_ids = [_digest(f"{profile}:sample")]
            groups = [[_packet(sample_ids[0], 0, cell=cell)]]
        counts = Counter(str(row["sample_id"]) for group in groups for row in group)
        master_rows = []
        for sample_id in sample_ids:
            master_rows.append(
                {
                    "sample_id": sample_id,
                    "profile": profile,
                    "capture_group_id": cell,
                    "packet_count_kept": counts[sample_id],
                }
            )
            budget_rows.append(master_rows[-1])
        profile_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(master_rows).to_parquet(profile_dir / "master_records.parquet", index=False)
        _write_packet_groups(profile_dir / "views" / "packet_observations.parquet", groups)
    return pd.DataFrame(budget_rows), profile_dirs


def test_filter_packets_restores_interleaved_samples_and_adjacent_row_groups(
    tmp_path: Path,
) -> None:
    first = _digest("first")
    second = _digest("second")
    cell = "A_cell"
    groups = [
        [
            _packet(first, 0, cell=cell),
            _packet(second, 0, cell=cell),
            _packet(first, 1, cell=cell),
        ],
        [_packet(second, 1, cell=cell), _packet(first, 2, cell=cell)],
    ]
    master, profile_dirs = _packet_fixture(tmp_path, groups)

    features, hashes, audits = filter_and_aggregate_budget_packets(master, profile_dirs)

    expected_packets = pd.DataFrame([groups[0][0], groups[0][2], groups[1][1]]).drop(
        columns="capture_group_id"
    )
    expected = _aggregate_features(expected_packets).loc[first]
    pd.testing.assert_series_equal(features.loc[first], expected, check_names=False)
    assert set(hashes) == set(master["sample_id"])
    assert sum(audit["retained_row_count"] for audit in audits) == len(expected_packets) + 4
    assert all(audit["packet_table_loaded_whole"] is False for audit in audits)


@pytest.mark.parametrize(
    ("indexes", "message"),
    [
        ([0, 2], "缺口"),
        ([0, 1, 1], "重复"),
        ([0, 2, 1], "回退"),
    ],
)
def test_filter_packets_rejects_invalid_packet_indexes(
    tmp_path: Path, indexes: list[int], message: str
) -> None:
    sample_id = _digest(message)
    groups = [[_packet(sample_id, index, cell="A_cell") for index in indexes]]
    master, profile_dirs = _packet_fixture(tmp_path, groups)

    with pytest.raises(TQHC2ABCFixedError, match=message):
        filter_and_aggregate_budget_packets(master, profile_dirs)


def test_filter_packets_rejects_unknown_sample_and_count_mismatch(tmp_path: Path) -> None:
    sample_id = _digest("known")
    groups = [[_packet(sample_id, 0, cell="A_cell")]]
    master, profile_dirs = _packet_fixture(tmp_path, groups)
    packet_path = profile_dirs["A"] / "views" / "packet_observations.parquet"
    unknown = _packet(_digest("unknown"), 0, cell="A_cell")
    _write_packet_groups(packet_path, [[*groups[0], unknown]])

    with pytest.raises(TQHC2ABCFixedError, match="未知 sample_id"):
        filter_and_aggregate_budget_packets(master, profile_dirs)

    _write_packet_groups(packet_path, groups)
    full_master = pd.read_parquet(profile_dirs["A"] / "master_records.parquet")
    full_master.loc[0, "packet_count_kept"] = 2
    full_master.to_parquet(profile_dirs["A"] / "master_records.parquet", index=False)
    master.loc[master["profile"].eq("A"), "packet_count_kept"] = 2
    with pytest.raises(TQHC2ABCFixedError, match="主记录计数"):
        filter_and_aggregate_budget_packets(master, profile_dirs)


def test_filter_packets_rejects_cross_cell_order_fallback(tmp_path: Path) -> None:
    one = _digest("one")
    two = _digest("two")
    three = _digest("three")
    groups = [
        [_packet(one, 0, cell="cell-1")],
        [_packet(two, 0, cell="cell-2")],
        [_packet(three, 0, cell="cell-1")],
    ]
    master, profile_dirs = _packet_fixture(tmp_path, groups)
    a_master = pd.DataFrame(
        [
            {
                "sample_id": one,
                "profile": "A",
                "capture_group_id": "cell-1",
                "packet_count_kept": 1,
            },
            {
                "sample_id": two,
                "profile": "A",
                "capture_group_id": "cell-2",
                "packet_count_kept": 1,
            },
            {
                "sample_id": three,
                "profile": "A",
                "capture_group_id": "cell-1",
                "packet_count_kept": 1,
            },
        ]
    )
    a_master.to_parquet(profile_dirs["A"] / "master_records.parquet", index=False)
    master = pd.concat([a_master, master[~master["profile"].eq("A")]], ignore_index=True)

    with pytest.raises(TQHC2ABCFixedError, match="cell 顺序回退"):
        filter_and_aggregate_budget_packets(master, profile_dirs)


def test_materialize_budget_is_byte_reproducible_and_frozen_protocol_compatible(
    tmp_path: Path,
) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    masters = pd.concat(
        [pd.read_parquet(path / "master_records.parquet") for path in profile_dirs.values()],
        ignore_index=True,
    )
    assignment = _write_assignment(tmp_path / "assignment.json", _build_base_groups(masters))
    first = tmp_path / "first" / "protocol"
    second = tmp_path / "second" / "protocol"

    first_result = materialize_candidate_abc_budget(
        profile_dirs=profile_dirs,
        approved_inputs=approved_inputs,
        assignment_path=assignment,
        cap_per_cell=2,
        output_dir=first,
    )
    materialize_candidate_abc_budget(
        profile_dirs=profile_dirs,
        approved_inputs=approved_inputs,
        assignment_path=assignment,
        cap_per_cell=2,
        output_dir=second,
    )

    assert first_result["sample_count"] == 72
    assert _artifact_bytes(first) == _artifact_bytes(second)
    protocol = load_frozen_protocol(
        first,
        expected_protocol_version=PROTOCOL_VERSION,
        expected_status=PROTOCOL_STATUS,
        expected_phase=PROTOCOL_PHASE,
    )
    assert set(protocol.manifests) == APPROVED_SPLIT_FILES
    samples = pd.read_parquet(first / "samples.parquet")
    assert samples["sample_id"].is_unique
    assert set(samples["candidate_id"]) == {CANDIDATE_ID}
    assert np.isfinite(samples.loc[:, MODEL_FEATURE_FIELDS].to_numpy(dtype=float)).all()
    document = yaml.safe_load((first / "protocol.yaml").read_text(encoding="utf-8"))
    assert (
        document["fixed_assignment_sha256"] == hashlib.sha256(assignment.read_bytes()).hexdigest()
    )
    assert document["sampling_algorithm"] == BUDGET_SAMPLING_ALGORITHM

    with pytest.raises(TQHC2ABCFixedError, match="拒绝覆盖"):
        materialize_candidate_abc_budget(
            profile_dirs=profile_dirs,
            approved_inputs=approved_inputs,
            assignment_path=assignment,
            cap_per_cell=2,
            output_dir=first,
        )


def test_materialize_budget_preserves_incomplete_marker_on_failure(tmp_path: Path) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    masters = pd.concat(
        [pd.read_parquet(path / "master_records.parquet") for path in profile_dirs.values()],
        ignore_index=True,
    )
    assignment = _write_assignment(tmp_path / "assignment.json", _build_base_groups(masters))
    packet_path = profile_dirs["A"] / "views" / "packet_observations.parquet"
    packets = pd.read_parquet(packet_path)
    packets.loc[0, "packet_index"] = 9
    packets.to_parquet(packet_path, index=False)
    approved_inputs["A"]["artifact_checksums_sha256"] = _refresh_upstream_artifact_manifest(
        profile_dirs["A"]
    )
    output_dir = tmp_path / "failed" / "protocol"

    with pytest.raises(TQHC2ABCFixedError):
        materialize_candidate_abc_budget(
            profile_dirs=profile_dirs,
            approved_inputs=approved_inputs,
            assignment_path=assignment,
            cap_per_cell=2,
            output_dir=output_dir,
        )

    assert (output_dir / "_INCOMPLETE").is_file()


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "message"),
    [
        ("sampling_algorithm", "unexpected", "抽样算法"),
        ("source_mapped_sample_count", -1, "源样本总数"),
    ],
)
def test_materialize_budget_rejects_conflicting_budget_metadata(
    tmp_path: Path, field_name: str, invalid_value: object, message: str
) -> None:
    profile_dirs, approved_inputs = _write_abc_fixture(tmp_path / "inputs")
    masters = pd.concat(
        [pd.read_parquet(path / "master_records.parquet") for path in profile_dirs.values()],
        ignore_index=True,
    )
    document = _assignment_document(_build_base_groups(masters))
    document["budget"][field_name] = invalid_value
    assignment = tmp_path / "assignment.json"
    assignment.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(TQHC2ABCFixedError, match=message):
        materialize_candidate_abc_budget(
            profile_dirs=profile_dirs,
            approved_inputs=approved_inputs,
            assignment_path=assignment,
            cap_per_cell=2,
            output_dir=tmp_path / f"failed-{field_name}" / "protocol",
        )
