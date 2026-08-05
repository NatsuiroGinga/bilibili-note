from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest
import yaml

from flow_probe.frozen_protocol import file_sha256
from flow_probe.unified_budget import (
    UnifiedBudgetError,
    _hamilton_allocate,
    materialize_unified_budget,
)


PROTOCOL_VERSION = "data-protocol-v1.0-rc1"
PROTOCOL_STATUS = "provisional"
PROTOCOL_PHASE = "theory_selection"


def test_checked_in_config_freezes_real_budget_contract() -> None:
    config_path = Path(__file__).resolve().parents[1] / "configs" / "unified_budget_v1.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["schema_version"] == "flow_probe_unified_budget_config_v1"
    assert config["determinism"]["quota_algorithm"] == (
        "proportional_largest_remainder_minimum_one_v1"
    )
    assert config["sources"]["genis"]["expected_sample_count"] == 1_372_690
    assert config["sources"]["genis"]["formal_train_pool"]["expected_joint_strata"] == 8
    assert config["sources"]["tqhc2"]["expected_sample_count"] == 35_235
    assert config["sources"]["tqhc2"]["formal_train_pool"]["expected_joint_strata"] == 56
    assert config["sources"]["ns3"]["identity"]["expected_unique_count"] == 2_421
    assert config["budgets"]["formal_training"]["source_counts"] == {
        "genis": 30_000,
        "tqhc2": 27_235,
        "ns3": 2_421,
    }
    assert config["budgets"]["formal_training"]["total_target_count"] == 59_656
    assert config["budgets"]["candidate_screening"]["source_counts"] == {
        "genis": 3_973,
        "tqhc2": 3_606,
        "ns3": 2_421,
    }
    assert config["budgets"]["candidate_screening"]["total_target_count"] == 10_000
    assert config["input_policy"]["allow_model_outputs"] is False
    assert config["outputs"]["budgets_dir"] == "manifests/budgets"
    assert config["publication"]["build_root"] == ("runs/data-candidate-builds/unified-budget-v1")
    assert config["publication"]["status_before_review"] == "review_pending"


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _write_yaml(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        yaml.safe_dump(value, allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )


def _write_protocol(
    root: Path,
    *,
    records: list[dict[str, object]],
    manifests: dict[str, tuple[str, str, list[str]]],
) -> None:
    root.mkdir(parents=True)
    (root / "splits").mkdir()
    samples = pd.DataFrame(records)
    samples.to_parquet(root / "samples.parquet", index=False)
    fields: dict[str, object] = {}
    for column in samples.columns:
        if column in {"binary_label", "family_label", "subtype_label"}:
            fields[column] = {"role": "label_target"}
        elif column == "feature":
            fields[column] = {"role": "model_input", "views": ["tree_flat_view"]}
        else:
            fields[column] = {"role": "audit_only"}
    _write_yaml(
        root / "field-roles.yaml",
        {
            "protocol_version": PROTOCOL_VERSION,
            "fields": fields,
            "views": {"tree_flat_view": {"feature_fields": ["feature"]}},
        },
    )
    samples_sha256 = file_sha256(root / "samples.parquet")
    for filename, (suite_id, split_id, sample_ids) in manifests.items():
        _write_jsonl(
            root / "splits" / filename,
            [
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "sample_id": sample_id,
                    "samples_sha256": samples_sha256,
                    "split_id": split_id,
                    "suite_id": suite_id,
                }
                for sample_id in sample_ids
            ],
        )
    artifacts = {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "protocol.yaml"
    }
    _write_yaml(
        root / "protocol.yaml",
        {
            "protocol_version": PROTOCOL_VERSION,
            "status": PROTOCOL_STATUS,
            "phase": PROTOCOL_PHASE,
            "artifacts": artifacts,
        },
    )


def _genis_records() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    records: list[dict[str, object]] = []
    assignments: list[dict[str, object]] = []
    specifications = [
        ("session-a", "2026-01-01", "benign", "benign", 3, "train"),
        ("session-b", "2026-01-01", "benign", "benign", 3, "train"),
        ("session-c", "2026-01-02", "dos", "udp_flood", 3, "train"),
        ("session-d", "2026-01-02", "dos", "udp_flood", 3, "train"),
        ("session-open-a", "2026-01-03", "dos", "novel_a", 2, "ood:dos-udp"),
        ("session-open-b", "2026-01-04", "dos", "novel_b", 2, "ood:dos-pushack"),
    ]
    for session_id, day, family, subtype, count, assignment in specifications:
        start_time = datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()
        assignments.append(
            {
                "assignment": assignment,
                "binary_label": "benign" if family == "benign" else "malicious",
                "last_time": start_time + 60,
                "row_count": count,
                "session_id": session_id,
                "start_time": start_time,
                "subtype": subtype,
            }
        )
        for index in range(count):
            records.append(
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "sample_id": f"genis-{session_id}-{index}",
                    "group_id": session_id,
                    "source_partition": assignment,
                    "binary_label": "benign" if family == "benign" else "malicious",
                    "family_label": family,
                    "subtype_label": subtype,
                    "feature": float(index),
                }
            )
    return records, assignments


def _tqh_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for index in range(6):
        profile = "A" if index < 3 else "B"
        records.append(
            {
                "protocol_version": PROTOCOL_VERSION,
                "sample_id": f"tqh-{index}",
                "split_id": "train",
                "allocation_group_id": f"cell-{index // 2}",
                "capture_group_id": f"capture-{index // 2}",
                "profile": profile,
                "interval_s": 30 if index % 2 == 0 else 60,
                "jitter_pct": 0 if index % 3 == 0 else 10,
                "binary_label": "benign" if index % 2 == 0 else "malicious",
                "feature": float(index),
            }
        )
    return records


def _ns3_records() -> dict[str, list[dict[str, object]]]:
    return {
        split: [
            {
                "sample_id": f"ns3-{split}",
                "group_id": f"topology-star-{split}",
                "label_targets": {"binary_label": "benign"},
                "model_inputs": {"packet_count": [1, 2, 3, 4]},
                "normalized_physics": {"queue_residual": [0.0, 0.0, 0.0, 0.0]},
                "state_supervision": {"queue_bytes": [0.0, 0.0, 0.0, 0.0]},
            }
        ]
        for split in ("train", "validation", "test")
    }


def _build_fixture(project_root: Path) -> tuple[Path, dict[str, object]]:
    genis_records, assignments = _genis_records()
    genis_train_ids = [
        str(row["sample_id"]) for row in genis_records if row["source_partition"] == "train"
    ]
    genis_open_ids = [
        str(row["sample_id"]) for row in genis_records if row["source_partition"] != "train"
    ]
    genis_root = project_root / "inputs" / "genis"
    _write_protocol(
        genis_root,
        records=genis_records,
        manifests={
            "genis-family-development-train.jsonl": (
                "genis_family_development",
                "train",
                genis_train_ids,
            ),
            "genis-subtype-open-set-test.jsonl": (
                "genis_subtype_open",
                "test",
                genis_open_ids,
            ),
        },
    )
    assignments_path = project_root / "inputs" / "session_assignments.jsonl"
    _write_jsonl(assignments_path, assignments)

    tqh_records = _tqh_records()
    tqh_ids = [str(row["sample_id"]) for row in tqh_records]
    tqh_root = project_root / "inputs" / "tqh"
    _write_protocol(
        tqh_root,
        records=tqh_records,
        manifests={
            "tqhc2_cell_indomain-train.jsonl": (
                "tqhc2_cell_indomain",
                "train",
                tqh_ids,
            )
        },
    )

    ns3 = _ns3_records()
    ns3_specs: dict[str, dict[str, object]] = {}
    for split, rows in ns3.items():
        relative_path = f"inputs/ns3-{split}.jsonl"
        path = project_root / relative_path
        _write_jsonl(path, rows)
        ns3_specs[split] = {
            "path": relative_path,
            "sha256": file_sha256(path),
            "expected_count": len(rows),
        }

    config: dict[str, object] = {
        "schema_version": "flow_probe_unified_budget_config_v1",
        "config_id": "unified-budget-v1",
        "stage": PROTOCOL_PHASE,
        "status": "review_pending",
        "path_policy": {
            "base": "project_root",
            "require_project_relative_paths": True,
            "forbid_absolute_paths": True,
        },
        "protocol_contract": {
            "version": PROTOCOL_VERSION,
            "status": PROTOCOL_STATUS,
            "phase": PROTOCOL_PHASE,
        },
        "determinism": {
            "seed": 42,
            "hash_algorithm": "sha256",
            "separator": "\\0",
            "quota_algorithm": "proportional_largest_remainder_minimum_one_v1",
            "unified_order_algorithm": "global_sha256_ascending_v1",
            "require_input_order_independence": True,
            "require_unique_sample_ids": True,
            "require_byte_identical_rebuilds": True,
            "rank_key_fields": [
                "algorithm_namespace",
                "seed",
                "source_dataset",
                "sample_id",
            ],
            "algorithm_namespaces": {
                "genis_formal": "unified-budget-v1/genis-formal",
                "genis_candidate": "unified-budget-v1/genis-candidate",
                "genis_open_neural": "unified-budget-v1/genis-open-neural",
                "tqhc2_candidate": "unified-budget-v1/tqhc2-candidate",
                "unified_formal_order": "unified-budget-v1/unified-formal-order",
                "unified_candidate_order": "unified-budget-v1/unified-candidate-order",
            },
        },
        "input_policy": {
            "allow_raw_source_data": False,
            "allow_model_outputs": False,
            "preserve_source_sample_id": True,
            "rewrite_labels": False,
            "rewrite_source_roles": False,
            "cross_source_sample_id_collisions_expected": 0,
        },
        "sources": {
            "genis": {
                "source_dataset": "genis",
                "protocol_dir": "inputs/genis",
                "protocol_file": "inputs/genis/protocol.yaml",
                "protocol_sha256": file_sha256(genis_root / "protocol.yaml"),
                "samples_file": "inputs/genis/samples.parquet",
                "samples_sha256": file_sha256(genis_root / "samples.parquet"),
                "expected_sample_count": len(genis_records),
                "identity": {
                    "field": "sample_id",
                    "expected_unique_count": len(genis_records),
                },
                "session_assignments_file": "inputs/session_assignments.jsonl",
                "session_assignments_sha256": file_sha256(assignments_path),
                "session_join": {
                    "sample_field": "group_id",
                    "assignment_field": "session_id",
                    "require_complete_join": True,
                    "on_missing": "fail",
                },
                "time_stratum": {
                    "source_field": "start_time",
                    "source_unit": "unix_seconds",
                    "timezone": "UTC",
                    "derived_field": "utc_day",
                    "format": "%Y-%m-%d",
                    "allow_fabricated_fallback": False,
                },
                "formal_train_pool": {
                    "manifest": "inputs/genis/splits/genis-family-development-train.jsonl",
                    "manifest_sha256": file_sha256(
                        genis_root / "splits" / "genis-family-development-train.jsonl"
                    ),
                    "expected_count": len(genis_train_ids),
                    "required_source_partition": "train",
                    "required_split_id": "train",
                    "stratification_fields": ["utc_day", "family_label", "subtype_label"],
                    "session_spread_field": "group_id",
                    "within_stratum_algorithm": "group_round_robin_then_sha256_v1",
                    "expected_group_count": 4,
                    "expected_joint_strata": 2,
                    "formal_target_count": 8,
                    "candidate_target_count": 3,
                },
                "open_eval_pool": {
                    "manifest": "inputs/genis/splits/genis-subtype-open-set-test.jsonl",
                    "manifest_sha256": file_sha256(
                        genis_root / "splits" / "genis-subtype-open-set-test.jsonl"
                    ),
                    "expected_count": len(genis_open_ids),
                    "allowed_use": "evaluation_only",
                    "stratification_fields": ["utc_day", "family_label", "subtype_label"],
                    "session_spread_field": "group_id",
                    "within_stratum_algorithm": "group_round_robin_then_sha256_v1",
                    "neural_eval_target_count": 3,
                },
            },
            "tqhc2": {
                "source_dataset": "tqhc2",
                "protocol_dir": "inputs/tqh",
                "protocol_file": "inputs/tqh/protocol.yaml",
                "protocol_sha256": file_sha256(tqh_root / "protocol.yaml"),
                "samples_file": "inputs/tqh/samples.parquet",
                "samples_sha256": file_sha256(tqh_root / "samples.parquet"),
                "expected_sample_count": len(tqh_records),
                "identity": {
                    "field": "sample_id",
                    "expected_unique_count": len(tqh_records),
                },
                "formal_train_pool": {
                    "manifest": "inputs/tqh/splits/tqhc2_cell_indomain-train.jsonl",
                    "manifest_sha256": file_sha256(
                        tqh_root / "splits" / "tqhc2_cell_indomain-train.jsonl"
                    ),
                    "expected_count": len(tqh_ids),
                    "expected_allocation_group_count": 3,
                    "expected_joint_strata": 6,
                    "formal_selection_algorithm": "preserve_manifest_membership_and_order_v1",
                    "formal_target_count": 6,
                    "candidate_target_count": 3,
                    "candidate_stratification_fields": [
                        "allocation_group_id",
                        "profile",
                        "interval_s",
                        "jitter_pct",
                        "binary_label",
                    ],
                    "candidate_within_stratum_algorithm": "sha256_ascending_v1",
                },
            },
            "ns3": {
                "source_dataset": "ns3",
                "source_dir": "inputs",
                "files": ns3_specs,
                "identity": {"field": "sample_id", "expected_unique_count": 3},
                "expected_group_count": 3,
                "formal_target_count": 3,
                "candidate_target_count": 3,
                "allow_oversampling": False,
                "allow_duplicate_index_entries": False,
            },
        },
        "budgets": {
            "formal_training": {
                "total_target_count": 17,
                "source_counts": {"genis": 8, "tqhc2": 6, "ns3": 3},
                "output_manifest": "train_unified_formal.jsonl",
            },
            "candidate_screening": {
                "total_target_count": 9,
                "source_counts": {"genis": 3, "tqhc2": 3, "ns3": 3},
                "public_detection_allocation_basis": {
                    "remaining_after_ns3": 6,
                    "formal_weights": {"genis": 8, "tqhc2": 6},
                    "allocation_algorithm": "hamilton_largest_remainder_v1",
                },
                "require_subset_of_formal_training": True,
                "output_manifest": "train_candidate_approx10000.jsonl",
            },
            "genis_open_neural": {
                "total_target_count": 3,
                "output_manifest": "eval_genis_open_neural_30000.jsonl",
            },
            "genis_open_full": {
                "total_target_count": 4,
                "output_manifest": "eval_genis_open_full_1179168.jsonl",
            },
        },
        "outputs": {
            "master_records": "master_records.parquet",
            "master_records_expected_count": len(genis_records) + len(tqh_records) + 3,
            "budgets_dir": "manifests/budgets",
            "files": [
                "train_genis_30000.jsonl",
                "train_tqhc2_cell_cap1000.jsonl",
                "train_ns3_all2421.jsonl",
                "train_unified_formal.jsonl",
                "train_candidate_approx10000.jsonl",
                "eval_genis_open_neural_30000.jsonl",
                "eval_genis_open_full_1179168.jsonl",
                "budget_statistics.json",
                "budget_checksums.json",
                "budget_freeze_manifest.json",
            ],
            "required_record_fields": [
                "sample_id",
                "source_dataset",
                "source_split",
                "task_role",
                "stable_order",
            ],
        },
        "publication": {
            "build_root": "builds",
            "independent_builds": ["build-a", "build-b"],
            "partial_suffix": ".partial",
            "publish_target": "published/dataset-v1",
            "refuse_overwrite": True,
            "require_atomic_rename": True,
            "require_byte_identical_builds": True,
            "status_before_review": "review_pending",
        },
    }
    config_path = project_root / "config.yaml"
    _write_yaml(config_path, config)
    return config_path, config


def _rewrite_config(config_path: Path, config: dict[str, object]) -> None:
    _write_yaml(config_path, config)


def _refresh_genis_protocol_bindings(
    config_path: Path,
    config: dict[str, object],
) -> None:
    project_root = config_path.parent
    genis_config = config["sources"]["genis"]
    protocol_root = project_root / genis_config["protocol_dir"]
    samples_path = protocol_root / "samples.parquet"
    samples_sha256 = file_sha256(samples_path)
    split_specs = (
        ("formal_train_pool", "genis-family-development-train.jsonl"),
        ("open_eval_pool", "genis-subtype-open-set-test.jsonl"),
    )
    protocol = yaml.safe_load((protocol_root / "protocol.yaml").read_text(encoding="utf-8"))
    protocol["artifacts"]["samples.parquet"] = samples_sha256
    for pool_name, filename in split_specs:
        manifest_path = protocol_root / "splits" / filename
        rows = _read_budget(manifest_path)
        for row in rows:
            row["samples_sha256"] = samples_sha256
        _write_jsonl(manifest_path, rows)
        digest = file_sha256(manifest_path)
        protocol["artifacts"][f"splits/{filename}"] = digest
        genis_config[pool_name]["manifest_sha256"] = digest
    _write_yaml(protocol_root / "protocol.yaml", protocol)
    genis_config["samples_sha256"] = samples_sha256
    genis_config["protocol_sha256"] = file_sha256(protocol_root / "protocol.yaml")
    _rewrite_config(config_path, config)


def _read_budget(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _build_dir(project_root: Path, name: str = "build-a") -> Path:
    return project_root / "builds" / name


def _budget_dir(output_dir: Path) -> Path:
    return output_dir / "manifests" / "budgets"


def test_hamilton_allocation_is_exact_and_preserves_nonempty_strata() -> None:
    allocation = _hamilton_allocate({"a": 8, "b": 3, "c": 1}, target=7)

    assert allocation == {"a": 4, "b": 2, "c": 1}
    assert sum(allocation.values()) == 7
    assert all(allocation[key] >= 1 for key in ("a", "b", "c"))


def test_materialize_builds_deterministic_budgets_and_reference_only_master(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, _ = _build_fixture(project_root)
    first = _build_dir(project_root, "build-a")
    second = _build_dir(project_root, "build-b")

    first_result = materialize_unified_budget(
        project_root=project_root,
        config_path=config_path,
        output_dir=first,
    )
    second_result = materialize_unified_budget(
        project_root=project_root,
        config_path=config_path,
        output_dir=second,
    )

    budget_names = {
        "train_genis_30000.jsonl",
        "train_tqhc2_cell_cap1000.jsonl",
        "train_ns3_all2421.jsonl",
        "train_unified_formal.jsonl",
        "train_candidate_approx10000.jsonl",
        "eval_genis_open_neural_30000.jsonl",
        "eval_genis_open_full_1179168.jsonl",
        "budget_statistics.json",
        "budget_checksums.json",
        "budget_freeze_manifest.json",
    }
    expected_paths = {"master_records.parquet"} | {
        f"manifests/budgets/{name}" for name in budget_names
    }
    first_paths = {
        path.relative_to(first).as_posix() for path in first.rglob("*") if path.is_file()
    }
    assert first_paths == expected_paths
    assert first_result == second_result
    assert all(
        (first / path).read_bytes() == (second / path).read_bytes() for path in expected_paths
    )

    master = pd.read_parquet(first / "master_records.parquet")
    budgets = _budget_dir(first)
    assert set(master.columns) == {
        "sample_id",
        "source_dataset",
        "source_artifact",
        "source_record_ordinal",
        "source_split",
        "group_id",
        "task_role",
        "tree_view_available",
        "sequence_view_available",
        "physics_view_available",
        "source_binary_label",
        "source_family_label",
        "source_subtype_label",
    }
    assert "feature" not in master.columns
    assert not master["source_artifact"].str.startswith("/").any()

    tqh_budget = _read_budget(budgets / "train_tqhc2_cell_cap1000.jsonl")
    assert [row["sample_id"] for row in tqh_budget] == [f"tqh-{index}" for index in range(6)]
    formal = _read_budget(budgets / "train_unified_formal.jsonl")
    candidate = _read_budget(budgets / "train_candidate_approx10000.jsonl")
    formal_ids = {str(row["sample_id"]) for row in formal}
    candidate_ids = {str(row["sample_id"]) for row in candidate}
    assert len(formal) == 17
    assert len(candidate) == 9
    assert candidate_ids < formal_ids
    assert {"ns3-train", "ns3-validation", "ns3-test"} <= candidate_ids

    statistics = json.loads((budgets / "budget_statistics.json").read_text(encoding="utf-8"))
    assert statistics["counts"]["train_unified_formal"] == 17
    assert statistics["counts"]["train_candidate_approx10000"] == 9
    assert set(statistics["strata"]["genis_formal"]) == {
        "2026-01-01|benign|benign",
        "2026-01-02|dos|udp_flood",
    }
    selected_genis = _read_budget(budgets / "train_genis_30000.jsonl")
    selected_groups = master.set_index("sample_id").loc[
        [row["sample_id"] for row in selected_genis], "group_id"
    ]
    assert set(selected_groups) == {"session-a", "session-b", "session-c", "session-d"}
    open_full = _read_budget(budgets / "eval_genis_open_full_1179168.jsonl")
    master_split_by_id = master.set_index("sample_id")["source_split"].astype(str).to_dict()
    assert {row["source_split"] for row in open_full} == {
        "ood:dos-udp",
        "ood:dos-pushack",
    }
    assert all(row["source_split"] == master_split_by_id[row["sample_id"]] for row in open_full)
    checksums = json.loads((budgets / "budget_checksums.json").read_text(encoding="utf-8"))
    assert "materialization_state.json" not in checksums["artifacts"]
    for relative_path, artifact in checksums["artifacts"].items():
        artifact_path = first / relative_path
        assert artifact_path.is_file()
        assert file_sha256(artifact_path) == artifact["sha256"]

    persisted_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in first.rglob("*")
        if path.suffix in {".json", ".jsonl"}
    )
    assert str(tmp_path) not in persisted_text
    assert "generated_at" not in persisted_text
    assert "timestamp" not in persisted_text


def test_materialize_rejects_invalid_source_hash(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, config = _build_fixture(project_root)
    config["sources"]["genis"]["protocol_sha256"] = "0" * 64
    _rewrite_config(config_path, config)

    with pytest.raises(UnifiedBudgetError, match="哈希"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=_build_dir(project_root),
        )


def test_materialize_rejects_cross_source_identity_collision(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, config = _build_fixture(project_root)
    ns3_path = project_root / config["sources"]["ns3"]["files"]["train"]["path"]
    row = _read_budget(ns3_path)[0]
    row["sample_id"] = "genis-session-a-0"
    _write_jsonl(ns3_path, [row])
    config["sources"]["ns3"]["files"]["train"]["sha256"] = file_sha256(ns3_path)
    _rewrite_config(config_path, config)

    with pytest.raises(UnifiedBudgetError, match="跨来源.*sample_id"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=_build_dir(project_root),
        )


def test_materialize_rejects_train_open_leakage(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, config = _build_fixture(project_root)
    protocol_root = project_root / "inputs" / "genis"
    manifest_path = protocol_root / "splits" / "genis-subtype-open-set-test.jsonl"
    rows = _read_budget(manifest_path)
    rows[0]["sample_id"] = "genis-session-a-0"
    _write_jsonl(manifest_path, rows)
    protocol = yaml.safe_load((protocol_root / "protocol.yaml").read_text(encoding="utf-8"))
    protocol["artifacts"]["splits/genis-subtype-open-set-test.jsonl"] = file_sha256(manifest_path)
    _write_yaml(protocol_root / "protocol.yaml", protocol)
    config["sources"]["genis"]["open_eval_pool"]["manifest_sha256"] = file_sha256(manifest_path)
    config["sources"]["genis"]["protocol_sha256"] = file_sha256(protocol_root / "protocol.yaml")
    _rewrite_config(config_path, config)

    with pytest.raises(UnifiedBudgetError, match="训练.*开放集.*泄漏"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=_build_dir(project_root),
        )


def test_materialize_rejects_train_open_group_leakage(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, config = _build_fixture(project_root)
    samples_path = project_root / "inputs" / "genis" / "samples.parquet"
    samples = pd.read_parquet(samples_path)
    samples.loc[
        samples["sample_id"] == "genis-session-open-a-0",
        "group_id",
    ] = "session-a"
    samples.to_parquet(samples_path, index=False)
    _refresh_genis_protocol_bindings(config_path, config)

    with pytest.raises(UnifiedBudgetError, match="会话级.*泄漏"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=_build_dir(project_root),
        )


def test_materialize_rejects_duplicate_ns3_sample(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, config = _build_fixture(project_root)
    ns3_path = project_root / config["sources"]["ns3"]["files"]["train"]["path"]
    row = _read_budget(ns3_path)[0]
    _write_jsonl(ns3_path, [row, row])
    split_config = config["sources"]["ns3"]["files"]["train"]
    split_config["sha256"] = file_sha256(ns3_path)
    split_config["expected_count"] = 2
    config["sources"]["ns3"]["identity"]["expected_unique_count"] = 4
    config["sources"]["ns3"]["formal_target_count"] = 4
    config["sources"]["ns3"]["candidate_target_count"] = 4
    config["budgets"]["formal_training"]["source_counts"]["ns3"] = 4
    config["budgets"]["formal_training"]["total_target_count"] = 18
    config["budgets"]["candidate_screening"]["source_counts"]["ns3"] = 4
    config["budgets"]["candidate_screening"]["total_target_count"] = 10
    config["outputs"]["master_records_expected_count"] += 1
    _rewrite_config(config_path, config)

    with pytest.raises(UnifiedBudgetError, match="重复.*sample_id"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=_build_dir(project_root),
        )


def test_materialize_rejects_insufficient_target(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, config = _build_fixture(project_root)
    config["sources"]["genis"]["formal_train_pool"]["formal_target_count"] = 13
    config["sources"]["genis"]["formal_train_pool"]["candidate_target_count"] = 4
    config["sources"]["tqhc2"]["formal_train_pool"]["candidate_target_count"] = 2
    config["budgets"]["formal_training"]["source_counts"]["genis"] = 13
    config["budgets"]["formal_training"]["total_target_count"] = 22
    config["budgets"]["candidate_screening"]["source_counts"] = {
        "genis": 4,
        "tqhc2": 2,
        "ns3": 3,
    }
    config["budgets"]["candidate_screening"]["public_detection_allocation_basis"][
        "formal_weights"
    ] = {"genis": 13, "tqhc2": 6}
    _rewrite_config(config_path, config)

    with pytest.raises(UnifiedBudgetError, match="目标.*超过"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=_build_dir(project_root),
        )


def test_materialize_rejects_existing_output_without_modifying_it(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, _ = _build_fixture(project_root)
    output_dir = _build_dir(project_root)
    output_dir.mkdir(parents=True)
    sentinel = output_dir / "keep.txt"
    sentinel.write_text("keep\n", encoding="utf-8")

    with pytest.raises(UnifiedBudgetError, match="拒绝覆盖"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=output_dir,
        )

    assert sentinel.read_text(encoding="utf-8") == "keep\n"


def test_materialize_rejects_unapproved_output_path(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, _ = _build_fixture(project_root)

    with pytest.raises(UnifiedBudgetError, match="固定构建目录"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=project_root / "outside-build-root",
        )


def test_materialize_rejects_changed_algorithm_contract(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, config = _build_fixture(project_root)
    config["determinism"]["quota_algorithm"] = "unregistered_quota"
    _rewrite_config(config_path, config)

    with pytest.raises(UnifiedBudgetError, match="配额算法"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=_build_dir(project_root),
        )


def test_materialize_preserves_partial_state_after_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path, _ = _build_fixture(project_root)
    output_dir = _build_dir(project_root)

    def fail_to_parquet(*args: object, **kwargs: object) -> None:
        raise RuntimeError("injected parquet failure")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fail_to_parquet)
    with pytest.raises(RuntimeError, match="injected parquet failure"):
        materialize_unified_budget(
            project_root=project_root,
            config_path=config_path,
            output_dir=output_dir,
        )

    partial_dir = output_dir.with_name(output_dir.name + ".partial")
    state = json.loads((partial_dir / "materialization_state.json").read_text(encoding="utf-8"))
    assert (partial_dir / "_INCOMPLETE").read_text(encoding="ascii") == "incomplete\n"
    assert state["status"] == "failed"
    assert state["error_type"] == "RuntimeError"
    assert not output_dir.exists()
