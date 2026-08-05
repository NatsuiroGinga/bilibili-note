"""共享 B0 视图的字段映射与无泄漏行为测试。"""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml


def _subject():
    return importlib.import_module("flow_probe.shared_b0_view")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_genis_direct_mapping_preserves_values_and_masks() -> None:
    subject = _subject()
    row = {
        "total_packets": 10.0,
        "total_bytes": 1000.0,
        "packet_length_mean": 100.0,
        "packet_length_min": None,
        "packet_length_max": 150.0,
        "iat_mean_ms": 2.5,
        "packet_rate": 400.0,
        "byte_rate": 40_000.0,
        "total_packets_missing": 0,
        "total_bytes_missing": 0,
        "packet_length_mean_missing": 0,
        "packet_length_min_missing": 1,
        "packet_length_max_missing": 0,
        "iat_mean_ms_missing": 0,
        "packet_rate_missing": 0,
        "byte_rate_missing": 0,
    }

    mapped = subject.map_genis_row(row)

    assert mapped == row


def test_genis_rejects_value_mask_disagreement() -> None:
    subject = _subject()
    row = {field: 1.0 for field in subject.COMMON_FIELDS} | {
        f"{field}_missing": 0 for field in subject.COMMON_FIELDS
    }
    row["packet_length_min_missing"] = 1

    with pytest.raises(subject.SharedB0ViewError, match="数值与缺失掩码不一致"):
        subject.map_genis_row(row)


def test_tqhc2_uses_fixed_unit_conversions_and_duration_rates() -> None:
    subject = _subject()
    mapped = subject.map_tqhc2_row(
        {
            "packet_count": 10,
            "flow_duration_us": 500_000,
            "network_bytes_total": 1000,
            "network_bytes_mean": 100,
            "network_bytes_min": 60,
            "network_bytes_max": 140,
            "delta_time_us_mean": 2500,
        }
    )

    assert mapped["iat_mean_ms"] == 2.5
    assert mapped["packet_rate"] == 20.0
    assert mapped["byte_rate"] == 2000.0
    assert all(mapped[f"{field}_missing"] == 0 for field in subject.COMMON_FIELDS)


def test_tqhc2_zero_duration_marks_only_rates_missing() -> None:
    subject = _subject()
    mapped = subject.map_tqhc2_row(
        {
            "packet_count": 1,
            "flow_duration_us": 0,
            "network_bytes_total": 64,
            "network_bytes_mean": 64,
            "network_bytes_min": 64,
            "network_bytes_max": 64,
            "delta_time_us_mean": 0,
        }
    )

    assert mapped["packet_rate"] is None
    assert mapped["byte_rate"] is None
    assert mapped["packet_rate_missing"] == 1
    assert mapped["byte_rate_missing"] == 1
    assert mapped["iat_mean_ms_missing"] == 0


def _ns3_record(*, is_attack: int = 0) -> dict[str, object]:
    return {
        "model_inputs": {
            "qdisc_received_packets": [1, 2, 3, 4],
            "qdisc_received_l3_bytes": [100, 200, 300, 400],
            "capacity_start_bps": [1_000_000] * 4,
            "capacity_end_bps": [1_000_000] * 4,
            "configured_capacity_integral_link_bytes": [12_500] * 4,
        },
        "metadata": {
            "scenario_id": "不得进入模型输入",
            "topology_id": "不得进入模型输入",
            "window_start_s": [0.0, 0.1, 0.2, 0.3],
            "window_end_s": [0.1, 0.2, 0.3, 0.4],
        },
        "label_targets": {"is_attack": [is_attack] * 4},
        "state_supervision": {"queue_start_l3_bytes": [0, 10, 20, 30]},
        "queue_boundary_anchors_l3_bytes": [0, 10, 20, 30, 40],
        "normalized_physics": {"queue_start_l3_bytes": [0.0, 0.1, 0.2, 0.3]},
    }


def _build_materialization_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    subject = _subject()
    root = tmp_path / "project"
    root.mkdir()
    data = root / "data"
    data.mkdir()

    master_path = data / "master.parquet"
    pd.DataFrame(
        [
            {"sample_id": "g-train", "source_dataset": "genis"},
            {"sample_id": "t-train", "source_dataset": "tqhc2"},
            {"sample_id": "n-train", "source_dataset": "ns3"},
            {"sample_id": "g-validation", "source_dataset": "genis"},
            {"sample_id": "t-validation", "source_dataset": "tqhc2"},
        ]
    ).to_parquet(master_path, index=False)
    master_sha = _sha256(master_path)

    candidate_path = data / "candidate.jsonl"
    candidate_rows = [
        {
            "stable_order": order,
            "sample_id": sample_id,
            "source_dataset": source,
            "task_role": "candidate_screening",
            "master_records_sha256": master_sha,
        }
        for order, (sample_id, source) in enumerate(
            (("g-train", "genis"), ("t-train", "tqhc2"), ("n-train", "ns3"))
        )
    ]
    _write_jsonl(candidate_path, candidate_rows)

    genis_path = data / "genis.parquet"
    genis_rows = []
    for sample_id, group_id, label in (
        ("g-train", "genis-train-group", "benign"),
        ("g-validation", "genis-validation-group", "malicious"),
    ):
        values = {field: float(index + 1) for index, field in enumerate(subject.COMMON_FIELDS)}
        genis_rows.append(
            {
                "sample_id": sample_id,
                "group_id": group_id,
                "binary_label": label,
                **values,
                **{f"{field}_missing": 0 for field in subject.COMMON_FIELDS},
            }
        )
    pd.DataFrame(genis_rows).to_parquet(genis_path, index=False)
    genis_sha = _sha256(genis_path)

    tqh_path = data / "tqhc2.parquet"
    pd.DataFrame(
        [
            {
                "sample_id": sample_id,
                "capture_group_id": group_id,
                "binary_label": label,
                "packet_count": 10,
                "flow_duration_us": 500_000,
                "network_bytes_total": 1000,
                "network_bytes_mean": 100,
                "network_bytes_min": 60,
                "network_bytes_max": 140,
                "delta_time_us_mean": 2500,
            }
            for sample_id, group_id, label in (
                ("t-train", "tqh-train-group", "malicious"),
                ("t-validation", "tqh-validation-group", "benign"),
            )
        ]
    ).to_parquet(tqh_path, index=False)
    tqh_sha = _sha256(tqh_path)

    genis_validation_path = data / "genis-validation.jsonl"
    _write_jsonl(
        genis_validation_path,
        [
            {
                "sample_id": "g-validation",
                "samples_sha256": genis_sha,
                "suite_id": "genis-family-development",
                "split_id": "validation",
            }
        ],
    )
    tqh_validation_path = data / "tqh-validation.jsonl"
    _write_jsonl(
        tqh_validation_path,
        [
            {
                "sample_id": "t-validation",
                "samples_sha256": tqh_sha,
                "suite_id": "tqhc2-cell-indomain",
                "split_id": "validation",
            }
        ],
    )

    ns3_path = data / "ns3.jsonl"
    ns3_record = _ns3_record()
    ns3_record["sample_id"] = "n-train"
    _write_jsonl(ns3_path, [ns3_record])

    checksums_path = data / "budget-checksums.json"
    _write_json(
        checksums_path,
        {"artifacts": {"data/candidate.jsonl": {"sha256": _sha256(candidate_path)}}},
    )
    output_path = root / "derived" / "shared-b0"
    config_path = root / "shared-b0.yaml"
    config = {
        "schema_version": subject.CONFIG_SCHEMA_VERSION,
        "config_id": "test-shared-b0",
        "stage": "theory_selection",
        "status": "review_pending",
        "common_fields": list(subject.COMMON_FIELDS),
        "dataset": {
            "master_records": {"path": "data/master.parquet", "sha256": master_sha},
            "budget_checksums": {
                "path": "data/budget-checksums.json",
                "sha256": _sha256(checksums_path),
            },
            "candidate_manifest": {
                "path": "data/candidate.jsonl",
                "checksum_entry": "data/candidate.jsonl",
                "expected_count": 3,
                "source_counts": {"genis": 1, "tqhc2": 1, "ns3": 1},
            },
        },
        "sources": {
            "genis": {
                "samples_path": "data/genis.parquet",
                "samples_sha256": genis_sha,
                "validation_manifest": {
                    "path": "data/genis-validation.jsonl",
                    "sha256": _sha256(genis_validation_path),
                    "expected_count": 1,
                    "suite_id": "genis-family-development",
                    "split_id": "validation",
                    "group_field": "group_id",
                },
            },
            "tqhc2": {
                "samples_path": "data/tqhc2.parquet",
                "samples_sha256": tqh_sha,
                "validation_manifest": {
                    "path": "data/tqh-validation.jsonl",
                    "sha256": _sha256(tqh_validation_path),
                    "expected_count": 1,
                    "suite_id": "tqhc2-cell-indomain",
                    "split_id": "validation",
                    "group_field": "capture_group_id",
                },
            },
            "ns3": {"files": [{"path": "data/ns3.jsonl", "sha256": _sha256(ns3_path)}]},
        },
        "publication": {
            "output": "derived/shared-b0",
            "partial_suffix": ".partial",
            "refuse_overwrite": True,
            "require_atomic_rename": True,
        },
    }
    config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return root, config_path, output_path


def _refresh_candidate_hash_binding(root: Path, config_path: Path) -> None:
    candidate_path = root / "data" / "candidate.jsonl"
    checksums_path = root / "data" / "budget-checksums.json"
    _write_json(
        checksums_path,
        {"artifacts": {"data/candidate.jsonl": {"sha256": _sha256(candidate_path)}}},
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["dataset"]["budget_checksums"]["sha256"] = _sha256(checksums_path)
    config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )


def test_ns3_aggregates_only_observable_fields_without_fabricating_values() -> None:
    subject = _subject()

    mapped = subject.map_ns3_record(_ns3_record())

    assert mapped["total_packets"] == 10.0
    assert mapped["total_bytes"] == 1000.0
    assert mapped["packet_length_mean"] == 100.0
    assert mapped["packet_rate"] == 25.0
    assert mapped["byte_rate"] == 2500.0
    for field in ("packet_length_min", "packet_length_max", "iat_mean_ms"):
        assert mapped[field] is None
        assert mapped[f"{field}_missing"] == 1


def test_ns3_rejects_mixed_window_labels() -> None:
    subject = _subject()
    record = _ns3_record()
    record["label_targets"]["is_attack"] = [0, 0, 1, 1]

    with pytest.raises(subject.SharedB0ViewError, match="不得跨越攻击标签变化"):
        subject._ns3_binary_label(record)


def test_rendered_input_excludes_source_label_and_physics_truth() -> None:
    subject = _subject()
    common = subject.map_ns3_record(_ns3_record(is_attack=1))

    text = subject.render_input_text(common)

    assert "scenario" not in text.lower()
    assert "topology" not in text.lower()
    assert "label" not in text.lower()
    assert "capacity" not in text.lower()
    assert "queue" not in text.lower()
    assert "malicious" not in text.lower()
    assert "benign" not in text.lower()


def test_candidate_contract_preserves_exact_order_and_source_quota() -> None:
    subject = _subject()
    master_sha = "a" * 64
    rows = [
        {
            "stable_order": 0,
            "sample_id": "g-1",
            "source_dataset": "genis",
            "task_role": "candidate_screening",
            "master_records_sha256": master_sha,
        },
        {
            "stable_order": 1,
            "sample_id": "t-1",
            "source_dataset": "tqhc2",
            "task_role": "candidate_screening",
            "master_records_sha256": master_sha,
        },
        {
            "stable_order": 2,
            "sample_id": "n-1",
            "source_dataset": "ns3",
            "task_role": "candidate_screening",
            "master_records_sha256": master_sha,
        },
    ]
    config = {
        "expected_count": 3,
        "source_counts": {"genis": 1, "tqhc2": 1, "ns3": 1},
    }

    sample_ids, sources = subject._candidate_contract(rows, config, master_sha)

    assert sample_ids == ["g-1", "t-1", "n-1"]
    assert sources == {"g-1": "genis", "t-1": "tqhc2", "n-1": "ns3"}


def test_production_config_freezes_exact_candidate_counts() -> None:
    subject = _subject()
    config_path = subject.Path(__file__).resolve().parents[1] / "configs" / "shared_b0_view_v1.yaml"

    config = subject._read_yaml(config_path)
    candidate = config["dataset"]["candidate_manifest"]

    assert candidate["expected_count"] == 10_000
    assert candidate["source_counts"] == {"genis": 3973, "tqhc2": 3606, "ns3": 2421}


def test_materialize_publishes_candidate_and_isolated_validation_views(tmp_path: Path) -> None:
    subject = _subject()
    root, config_path, output_path = _build_materialization_fixture(tmp_path)

    result = subject.materialize_shared_b0_view(root, config_path, output_path)

    assert result["candidate_count"] == 3
    assert result["validation_counts"] == {"genis": 1, "tqhc2": 1}
    assert output_path.is_dir()
    assert not output_path.with_name(output_path.name + ".partial").exists()
    assert len((output_path / "candidate" / "qwen_train.jsonl").read_text().splitlines()) == 3
    assert len((output_path / "validation" / "genis_qwen.jsonl").read_text().splitlines()) == 1
    assert len((output_path / "validation" / "tqhc2_qwen.jsonl").read_text().splitlines()) == 1
    statistics = json.loads((output_path / "manifests" / "statistics.json").read_text())
    assert statistics["validation"]["genis"]["sample_overlap_count"] == 0
    assert statistics["validation"]["tqhc2"]["group_overlap_count"] == 0


def test_materialize_hash_mismatch_leaves_failed_partial(tmp_path: Path) -> None:
    subject = _subject()
    root, config_path, output_path = _build_materialization_fixture(tmp_path)
    master_path = root / "data" / "master.parquet"
    master_path.write_bytes(master_path.read_bytes() + b"corrupt")

    with pytest.raises(subject.SharedB0ViewError, match="哈希不一致"):
        subject.materialize_shared_b0_view(root, config_path, output_path)

    partial = output_path.with_name(output_path.name + ".partial")
    state = json.loads((partial / "materialization_state.json").read_text())
    assert state["status"] == "failed"
    assert (partial / "_INCOMPLETE").is_file()


def test_materialize_rejects_duplicate_candidate_sample(tmp_path: Path) -> None:
    subject = _subject()
    root, config_path, output_path = _build_materialization_fixture(tmp_path)
    candidate_path = root / "data" / "candidate.jsonl"
    rows = [json.loads(line) for line in candidate_path.read_text().splitlines()]
    rows[-1]["sample_id"] = rows[0]["sample_id"]
    _write_jsonl(candidate_path, rows)
    _refresh_candidate_hash_binding(root, config_path)

    with pytest.raises(subject.SharedB0ViewError, match="sample_id 重复"):
        subject.materialize_shared_b0_view(root, config_path, output_path)


def test_materialize_rejects_existing_output_without_overwrite(tmp_path: Path) -> None:
    subject = _subject()
    root, config_path, output_path = _build_materialization_fixture(tmp_path)
    subject.materialize_shared_b0_view(root, config_path, output_path)

    with pytest.raises(subject.SharedB0ViewError, match="拒绝覆盖"):
        subject.materialize_shared_b0_view(root, config_path, output_path)


def test_materialize_rejects_cli_output_different_from_publication(tmp_path: Path) -> None:
    subject = _subject()
    root, config_path, _ = _build_materialization_fixture(tmp_path)

    with pytest.raises(subject.SharedB0ViewError, match="publication.output 一致"):
        subject.materialize_shared_b0_view(root, config_path, root / "derived" / "other")
