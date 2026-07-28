"""GeNIS 理论筛选候选协议的隔离夹具测试。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path

import pandas as pd
import pytest
import yaml

from flow_probe.frozen_protocol import load_frozen_protocol
from flow_probe.genis_candidate import (
    FAMILY_SUITE_ID,
    INPUT_FILES,
    KNOWN_SUBTYPES,
    MODEL_FEATURE_FIELDS,
    OBSERVATION_FIELDS,
    OPEN_SET_SUITE_ID,
    PROTOCOL_PHASE,
    PROTOCOL_STATUS,
    PROTOCOL_VERSION,
    SPLIT_SPECS,
    SUBTYPE_SUITE_ID,
    UNKNOWN_SUBTYPES,
    GeNISCandidateError,
    materialize_candidate,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _family_for_subtype(subtype: str) -> str:
    return subtype.split("-", maxsplit=1)[0]


def _binary_for_subtype(subtype: str) -> str:
    return "benign" if subtype.startswith("benign-") else "malicious"


def _features(index: int) -> dict[str, float | None]:
    base = float(index + 1)
    return {
        "total_packets": base + 1.0,
        "total_bytes": base * 100.0 + 20.0,
        "packet_length_mean": base + 20.0,
        "packet_length_min": base + 10.0,
        "packet_length_max": base + 30.0,
        "iat_mean_ms": None if index == 9 else base / 10.0,
        "packet_rate": base * 2.0,
        "byte_rate": base * 8.0,
    }


def _partition_summary(assignments: list[dict[str, object]], assignment: str) -> dict[str, object]:
    selected = [row for row in assignments if row["assignment"] == assignment]
    binary_rows: Counter[str] = Counter()
    subtype_rows: Counter[str] = Counter()
    for row in selected:
        binary_rows[str(row["binary_label"])] += int(row["row_count"])
        subtype_rows[str(row["subtype"])] += int(row["row_count"])
    return {
        "row_count": sum(int(row["row_count"]) for row in selected),
        "session_count": len(selected),
        "binary_label_rows": dict(sorted(binary_rows.items())),
        "subtype_rows": dict(sorted(subtype_rows.items())),
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: list[Mapping[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_fixture(root: Path) -> dict[str, object]:
    prepared_dir = root / "prepared"
    split_dir = root / "split"
    prepared_dir.mkdir(parents=True)
    split_dir.mkdir()
    records_by_assignment: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    assignments: list[dict[str, object]] = []
    session_ids: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    old_sample_ids: list[str] = []
    record_index = 0

    for subtype_index, subtype in enumerate(sorted(KNOWN_SUBTYPES)):
        train_features: dict[str, float | None] | None = None
        for assignment, times in (
            ("train", (10.0,)),
            ("validation", (20.0, 21.0)),
            ("test", (30.0,)),
        ):
            for local_index, start_time in enumerate(times):
                session_id = hashlib.md5(
                    f"{subtype}:{assignment}:{local_index}".encode("utf-8"),
                    usedforsecurity=False,
                ).hexdigest()
                session_ids[(subtype, assignment)].append(session_id)
                assignments.append(
                    {
                        "assignment": assignment,
                        "binary_label": _binary_for_subtype(subtype),
                        "last_time": start_time + 0.25,
                        "row_count": 1,
                        "session_id": session_id,
                        "start_time": start_time,
                        "subtype": subtype,
                    }
                )
                current_features = _features(record_index)
                if assignment == "train":
                    train_features = current_features
                if subtype_index == 0 and assignment == "validation" and local_index == 0:
                    assert train_features is not None
                    current_features = dict(train_features)
                old_sample_id = f"genis:attack-{subtype}.csv:{record_index + 1}"
                old_sample_ids.append(old_sample_id)
                records_by_assignment[assignment].append(
                    {
                        "sample_id": old_sample_id,
                        "group_id": session_id,
                        "source_dataset": "genis",
                        "binary_label": _binary_for_subtype(subtype),
                        "attack_family": _family_for_subtype(subtype),
                        "features": current_features,
                        "prompt": f"fixture prompt {subtype}",
                        "completion": json.dumps(
                            {"label": _binary_for_subtype(subtype)}, sort_keys=True
                        ),
                    }
                )
                record_index += 1

    for subtype in sorted(UNKNOWN_SUBTYPES):
        assignment = f"ood:{subtype}"
        session_id = hashlib.md5(
            f"{subtype}:ood".encode("utf-8"), usedforsecurity=False
        ).hexdigest()
        session_ids[(subtype, assignment)].append(session_id)
        assignments.append(
            {
                "assignment": assignment,
                "binary_label": "malicious",
                "last_time": 40.25,
                "row_count": 1,
                "session_id": session_id,
                "start_time": 40.0,
                "subtype": subtype,
            }
        )
        old_sample_id = f"genis:attack-{subtype}.csv:{record_index + 1}"
        old_sample_ids.append(old_sample_id)
        records_by_assignment[assignment].append(
            {
                "sample_id": old_sample_id,
                "group_id": session_id,
                "source_dataset": "genis",
                "binary_label": "malicious",
                "attack_family": "dos",
                "features": _features(record_index),
                "prompt": f"fixture prompt {subtype}",
                "completion": '{"label":"malicious"}',
            }
        )
        record_index += 1

    assignments.sort(key=lambda row: (str(row["subtype"]), str(row["session_id"])))
    assignments_path = split_dir / "session_assignments.jsonl"
    _write_jsonl(assignments_path, assignments)
    for assignment, filename, _, _ in INPUT_FILES:
        _write_jsonl(prepared_dir / filename, records_by_assignment[assignment])

    source_files = [
        {
            "name": "source-fixture.csv",
            "sha256": _digest("source-fixture"),
            "size_bytes": 123,
        }
    ]
    output_rows = {
        assignment: len(records_by_assignment[assignment]) for assignment, _, _, _ in INPUT_FILES
    }
    material_summary = {
        "schema_version": "genis_materialized_split_v1",
        "assignment_sha256": hashlib.sha256(assignments_path.read_bytes()).hexdigest(),
        "output_rows": output_rows,
        "written_row_count": sum(output_rows.values()),
        "purged_row_count": 0,
        "source_files": source_files,
        "privacy": {
            "raw_flow_ids_written": False,
            "addresses_written": False,
            "ports_written": False,
        },
    }
    _write_json(prepared_dir / "materialization_summary.json", material_summary)
    plan_summary = {
        "schema_version": "genis_hybrid_forward_split_v1",
        "ratios": [0.8, 0.1, 0.1],
        "temporal_order_verified": True,
        "ood_subtypes": sorted(UNKNOWN_SUBTYPES),
        "partitions": {
            partition: _partition_summary(assignments, partition)
            for partition in ("train", "validation", "test", "purged")
        },
        "ood": {
            subtype: _partition_summary(assignments, f"ood:{subtype}")
            for subtype in sorted(UNKNOWN_SUBTYPES)
        },
        "source_files": source_files,
    }
    plan_summary_path = split_dir / "plan_summary.json"
    _write_json(plan_summary_path, plan_summary)
    return {
        "prepared_dir": prepared_dir,
        "assignments_path": assignments_path,
        "plan_summary_path": plan_summary_path,
        "old_sample_ids": old_sample_ids,
        "session_ids": session_ids,
        "source_name": "source-fixture.csv",
    }


def _materialize(fixture: Mapping[str, object], output_dir: Path) -> dict[str, object]:
    return materialize_candidate(
        prepared_dir=Path(fixture["prepared_dir"]),
        assignments_path=Path(fixture["assignments_path"]),
        plan_summary_path=Path(fixture["plan_summary_path"]),
        output_dir=output_dir,
    )


def _artifact_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _refresh_assignment_hash(fixture: Mapping[str, object]) -> None:
    assignments_path = Path(fixture["assignments_path"])
    summary_path = Path(fixture["prepared_dir"]) / "materialization_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["assignment_sha256"] = hashlib.sha256(assignments_path.read_bytes()).hexdigest()
    _write_json(summary_path, summary)


def test_materialize_candidate_restores_labels_and_builds_loadable_protocol(
    tmp_path: Path,
) -> None:
    fixture = _write_fixture(tmp_path / "fixture")
    output_dir = tmp_path / "candidate" / "protocol"

    result = _materialize(fixture, output_dir)

    assert result["sample_count"] == 35
    assert result["excluded_validation_count"] == 1
    assert result["development_eligible_count"] == 23
    assert not (output_dir / "_INCOMPLETE").exists()
    protocol_document = yaml.safe_load((output_dir / "protocol.yaml").read_text(encoding="utf-8"))
    assert protocol_document["protocol_version"] == PROTOCOL_VERSION
    assert protocol_document["status"] == PROTOCOL_STATUS
    assert protocol_document["phase"] == PROTOCOL_PHASE
    assert protocol_document["final_tuning_allowed"] is False
    assert protocol_document["final_test_claim_allowed"] is False

    protocol = load_frozen_protocol(
        output_dir,
        expected_protocol_version=PROTOCOL_VERSION,
        expected_status=PROTOCOL_STATUS,
        expected_phase=PROTOCOL_PHASE,
    )
    assert tuple(protocol.model_views["tree_flat_view"].feature_fields) == (MODEL_FEATURE_FIELDS)
    assert set(protocol.manifests) == {relative_path for relative_path, _, _, _ in SPLIT_SPECS}
    family_train = protocol.load_tabular_split(
        "splits/genis-family-development-train.jsonl", label_field="family_label"
    )
    family_validation = protocol.load_tabular_split(
        "splits/genis-family-development-validation.jsonl", label_field="family_label"
    )
    subtype_train = protocol.load_tabular_split(
        "splits/genis-subtype-development-train.jsonl", label_field="subtype_label"
    )
    subtype_validation = protocol.load_tabular_split(
        "splits/genis-subtype-development-validation.jsonl", label_field="subtype_label"
    )
    open_set = protocol.load_tabular_split(
        "splits/genis-subtype-open-set-test.jsonl", label_field="subtype_label"
    )
    assert family_train.sample_ids == subtype_train.sample_ids
    assert family_validation.sample_ids == subtype_validation.sample_ids
    assert set(family_train.labels) == {"benign", "bruteforce", "dos"}
    assert set(subtype_train.labels) == KNOWN_SUBTYPES
    assert set(subtype_validation.labels) == KNOWN_SUBTYPES
    assert set(open_set.labels) == UNKNOWN_SUBTYPES
    assert open_set.manifest.suite_id == OPEN_SET_SUITE_ID
    assert family_train.manifest.suite_id == FAMILY_SUITE_ID
    assert subtype_train.manifest.suite_id == SUBTYPE_SUITE_ID

    samples = pd.read_parquet(output_dir / "samples.parquet")
    roles = yaml.safe_load((output_dir / "field-roles.yaml").read_text(encoding="utf-8"))
    assert set(samples.columns) == set(roles["fields"])
    assert all(roles["fields"][field]["role"] == "model_input" for field in MODEL_FEATURE_FIELDS)
    missing_row = samples[samples["iat_mean_ms"].isna()].iloc[0]
    assert missing_row["iat_mean_ms_missing"] == 1
    leakage = json.loads((output_dir / "audit" / "leakage-audit.json").read_text())
    assert leakage["strict_train_validation_exact_observation"] == {
        "cross_split_hash_count": 0,
        "excluded_validation_counts_by_subtype": {sorted(KNOWN_SUBTYPES)[0]: 1},
        "excluded_validation_record_count": 1,
        "status": "pass",
    }
    label_contract = json.loads((output_dir / "label-contract.json").read_text())
    assert set(label_contract["open_set"]["unknown_labels"]) == UNKNOWN_SUBTYPES
    assert set(label_contract["open_set"]["family_mapping"].values()) == {"dos"}

    for old_sample_id in fixture["old_sample_ids"]:
        encoded = str(old_sample_id).encode("utf-8")
        assert all(encoded not in payload for payload in _artifact_bytes(output_dir).values())
    source_name = str(fixture["source_name"]).encode("utf-8")
    allowed_lineage_paths = {
        "source-artifacts.jsonl",
        "audit/input-lineage.json",
        "audit/artifact-sha256.txt",
        "protocol.yaml",
    }
    for relative_path, payload in _artifact_bytes(output_dir).items():
        if relative_path not in allowed_lineage_paths:
            assert source_name not in payload


def test_materialize_candidate_excludes_exact_validation_duplicate_and_is_reproducible(
    tmp_path: Path,
) -> None:
    fixture = _write_fixture(tmp_path / "fixture")
    first = tmp_path / "first"
    second = tmp_path / "second"

    _materialize(fixture, first)
    _materialize(fixture, second)

    assert _artifact_bytes(first) == _artifact_bytes(second)
    samples = pd.read_parquet(first / "samples.parquet")
    excluded = samples[~samples["development_eligible"]]
    duplicate_exclusions = excluded[
        excluded["exclusion_reason"].eq("exact_observation_seen_in_train")
    ]
    assert len(duplicate_exclusions) == 1
    validation_manifest = _read_jsonl(
        first / "splits" / "genis-family-development-validation.jsonl"
    )
    validation_ids = {str(row["sample_id"]) for row in validation_manifest}
    assert str(duplicate_exclusions.iloc[0]["sample_id"]) not in validation_ids
    with pytest.raises(GeNISCandidateError, match="拒绝覆盖"):
        _materialize(fixture, first)


def test_materialize_candidate_rejects_assignment_hash_and_source_summary_mismatch(
    tmp_path: Path,
) -> None:
    hash_fixture = _write_fixture(tmp_path / "hash-fixture")
    summary_path = Path(hash_fixture["prepared_dir"]) / "materialization_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["assignment_sha256"] = "0" * 64
    _write_json(summary_path, summary)
    with pytest.raises(GeNISCandidateError, match="会话分配 SHA-256"):
        _materialize(hash_fixture, tmp_path / "hash-output")

    source_fixture = _write_fixture(tmp_path / "source-fixture")
    plan_path = Path(source_fixture["plan_summary_path"])
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["source_files"][0]["sha256"] = "1" * 64
    _write_json(plan_path, plan)
    with pytest.raises(GeNISCandidateError, match="原始来源清单不一致"):
        _materialize(source_fixture, tmp_path / "source-output")


@pytest.mark.parametrize(
    ("mutator", "message"),
    (
        ("unknown_session", "未分配会话"),
        ("session_row_count", "会话行数不一致"),
        ("file_assignment", "所在文件与 assignment 不一致"),
        ("nonfinite_feature", "有限数或 null"),
    ),
)
def test_materialize_candidate_rejects_invalid_record_binding(
    tmp_path: Path,
    mutator: str,
    message: str,
) -> None:
    fixture = _write_fixture(tmp_path / mutator)
    prepared_dir = Path(fixture["prepared_dir"])
    if mutator == "unknown_session":
        path = prepared_dir / "train.jsonl"
        rows = _read_jsonl(path)
        rows[0]["group_id"] = "f" * 32
        _write_jsonl(path, rows)
    elif mutator == "session_row_count":
        path = prepared_dir / "validation.jsonl"
        rows = _read_jsonl(path)
        rows[1]["group_id"] = rows[0]["group_id"]
        _write_jsonl(path, rows)
    elif mutator == "file_assignment":
        path = prepared_dir / "train.jsonl"
        rows = _read_jsonl(path)
        subtype = str(rows[0]["attack_family"])
        matching = next(
            key
            for key in fixture["session_ids"]
            if key[0].startswith(f"{subtype}-") and key[1] == "validation"
        )
        rows[0]["group_id"] = fixture["session_ids"][matching][0]
        _write_jsonl(path, rows)
    else:
        path = prepared_dir / "train.jsonl"
        rows = _read_jsonl(path)
        rows[0]["features"][OBSERVATION_FIELDS[0]] = float("inf")
        _write_jsonl(path, rows)

    with pytest.raises(GeNISCandidateError, match=message):
        _materialize(fixture, tmp_path / f"{mutator}-output")


def test_materialize_candidate_rejects_temporal_overlap(
    tmp_path: Path,
) -> None:
    fixture = _write_fixture(tmp_path / "fixture")
    assignments_path = Path(fixture["assignments_path"])
    assignments = _read_jsonl(assignments_path)
    subtype = sorted(KNOWN_SUBTYPES)[0]
    validation_start = next(
        float(row["start_time"])
        for row in assignments
        if row["subtype"] == subtype and row["assignment"] == "validation"
    )
    train = next(
        row for row in assignments if row["subtype"] == subtype and row["assignment"] == "train"
    )
    train["last_time"] = validation_start
    _write_jsonl(assignments_path, assignments)
    _refresh_assignment_hash(fixture)

    with pytest.raises(GeNISCandidateError, match="训练与验证时间交叉"):
        _materialize(fixture, tmp_path / "output")
