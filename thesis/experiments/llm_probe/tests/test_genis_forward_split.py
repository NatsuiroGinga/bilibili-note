import csv
import json
from pathlib import Path

import pytest

import flow_probe.genis_forward_split as forward_split
from flow_probe.genis_forward_split import (
    GeNISForwardSplitError,
    GeNISSession,
    plan_hybrid_forward_split,
)

GENIS_METADATA_FIELDS = (
    "FlowID",
    "StartTime",
    "LastTime",
    "BinaryLabel",
    "CategoryLabel",
    "SubCategoryLabel",
)
GENIS_TRAINING_FIELDS = GENIS_METADATA_FIELDS + (
    "TotPkts",
    "SrcPkts",
    "DstPkts",
    "TotBytes",
    "sMinPktSz",
    "dMinPktSz",
    "sMaxPktSz",
    "dMaxPktSz",
    "SIntPkt",
    "DIntPkt",
    "Rate",
    "Load",
)


def session(
    session_id: str,
    subtype: str,
    start: float,
    last: float,
    row_count: int = 1,
) -> GeNISSession:
    return GeNISSession(
        session_id=session_id,
        subtype=subtype,
        binary_label="benign" if subtype.startswith("benign") else "malicious",
        start_time=start,
        last_time=last,
        row_count=row_count,
    )


def write_metadata_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=GENIS_METADATA_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_training_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=GENIS_TRAINING_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "TotPkts": 10,
                    "SrcPkts": 6,
                    "DstPkts": 4,
                    "TotBytes": 1000,
                    "sMinPktSz": 40,
                    "dMinPktSz": 50,
                    "sMaxPktSz": 200,
                    "dMaxPktSz": 300,
                    "SIntPkt": 2,
                    "DIntPkt": 4,
                    "Rate": 5,
                    "Load": 8000,
                }
            )


def test_hybrid_split_is_forward_and_keeps_same_start_group_together() -> None:
    sessions = [
        session("a", "bruteforce-ftp", 0, 1),
        session("b", "bruteforce-ftp", 0, 2),
        session("c", "bruteforce-ftp", 10, 11),
        session("d", "bruteforce-ftp", 20, 21),
        session("e", "bruteforce-ftp", 30, 31),
        session("f", "bruteforce-ftp", 40, 41),
    ]

    plan = plan_hybrid_forward_split(
        sessions,
        ratios=(0.5, 0.25, 0.25),
        ood_subtypes=frozenset(),
    )

    assert plan.assignments["a"] == plan.assignments["b"]
    assert plan.assignments["a"] == "train"
    assert max(item.last_time for item in plan.train) < min(
        item.start_time for item in plan.validation
    )
    assert max(item.last_time for item in plan.validation) < min(
        item.start_time for item in plan.test
    )


def test_hybrid_split_purges_sessions_crossing_a_time_boundary() -> None:
    sessions = [
        session("crossing", "bruteforce-ftp", 0, 25),
        session("early", "bruteforce-ftp", 10, 11),
        session("middle", "bruteforce-ftp", 20, 21),
        session("late", "bruteforce-ftp", 30, 31),
        session("latest", "bruteforce-ftp", 40, 41),
    ]

    plan = plan_hybrid_forward_split(
        sessions,
        ratios=(0.4, 0.2, 0.4),
        ood_subtypes=frozenset(),
    )

    assert plan.assignments["crossing"] == "purged"
    assert {item.session_id for item in plan.purged} == {"crossing"}


def test_hybrid_split_keeps_declared_ood_subtype_whole() -> None:
    sessions = [
        session("train-a", "bruteforce-ftp", 0, 1),
        session("train-b", "bruteforce-ftp", 10, 11),
        session("train-c", "bruteforce-ftp", 20, 21),
        session("ood-a", "dos-icmp", 5, 15, row_count=100),
        session("ood-b", "dos-icmp", 25, 35, row_count=200),
    ]

    plan = plan_hybrid_forward_split(
        sessions,
        ratios=(0.34, 0.33, 0.33),
        ood_subtypes=frozenset({"dos-icmp"}),
    )

    assert plan.assignments["ood-a"] == "ood:dos-icmp"
    assert plan.assignments["ood-b"] == "ood:dos-icmp"
    assert {item.session_id for item in plan.ood["dos-icmp"]} == {"ood-a", "ood-b"}


def test_hybrid_split_rejects_non_ood_subtype_with_fewer_than_three_start_groups() -> None:
    sessions = [
        session("a", "dos-udp", 0, 1),
        session("b", "dos-udp", 10, 11),
    ]

    with pytest.raises(GeNISForwardSplitError, match="至少 3 个会话起始时刻"):
        plan_hybrid_forward_split(
            sessions,
            ratios=(0.8, 0.1, 0.1),
            ood_subtypes=frozenset(),
        )


def test_load_genis_sessions_merges_repeated_windows_without_writing_flow_id(
    tmp_path: Path,
) -> None:
    assert hasattr(forward_split, "load_genis_sessions")
    source = tmp_path / "attack-bruteforce-ftp.csv"
    write_metadata_rows(
        source,
        [
            {
                "FlowID": "private-flow-a",
                "StartTime": 10,
                "LastTime": 15,
                "BinaryLabel": 1,
                "CategoryLabel": "bruteforce",
                "SubCategoryLabel": "bruteforce-ftp",
            },
            {
                "FlowID": "private-flow-a",
                "StartTime": 20,
                "LastTime": 25,
                "BinaryLabel": 1,
                "CategoryLabel": "bruteforce",
                "SubCategoryLabel": "bruteforce-ftp",
            },
        ],
    )

    sessions = forward_split.load_genis_sessions([source])

    assert len(sessions) == 1
    assert sessions[0].row_count == 2
    assert sessions[0].start_time == 10
    assert sessions[0].last_time == 25
    assert "private-flow-a" not in sessions[0].session_id


def test_split_summary_counts_rows_and_excludes_raw_identifiers(tmp_path: Path) -> None:
    assert hasattr(forward_split, "summarize_hybrid_plan")
    sessions = [
        session("a", "bruteforce-ftp", 0, 1, row_count=2),
        session("b", "bruteforce-ftp", 10, 11, row_count=3),
        session("c", "bruteforce-ftp", 20, 21, row_count=5),
        session("private-flow", "dos-icmp", 0, 10, row_count=100),
    ]
    plan = plan_hybrid_forward_split(
        sessions,
        ratios=(0.34, 0.33, 0.33),
        ood_subtypes=frozenset({"dos-icmp"}),
    )

    summary = forward_split.summarize_hybrid_plan(
        plan,
        ratios=(0.34, 0.33, 0.33),
        ood_subtypes=frozenset({"dos-icmp"}),
    )

    assert summary["partitions"]["train"]["row_count"] == 2
    assert summary["partitions"]["validation"]["row_count"] == 3
    assert summary["partitions"]["test"]["row_count"] == 5
    assert summary["ood"]["dos-icmp"]["row_count"] == 100
    assert summary["privacy"]["raw_flow_ids_written"] is False
    assert summary["domain_row_count"] == 10
    assert summary["kept_row_count"] == 10
    assert summary["purged_row_rate"] == 0
    assert summary["kept_ratios"] == {
        "test": 0.5,
        "train": 0.2,
        "validation": 0.3,
    }
    assert summary["temporal_order_verified"] is True
    assert "private-flow" not in json.dumps(summary)


def test_create_hybrid_forward_split_writes_reproducible_private_artifacts(
    tmp_path: Path,
) -> None:
    assert hasattr(forward_split, "create_hybrid_forward_split")
    source = tmp_path / "mixed.csv"
    rows = []
    for index, start in enumerate((0, 10, 20, 30)):
        rows.append(
            {
                "FlowID": f"private-train-{index}",
                "StartTime": start,
                "LastTime": start + 1,
                "BinaryLabel": 1,
                "CategoryLabel": "bruteforce",
                "SubCategoryLabel": "bruteforce-ftp",
            }
        )
    rows.append(
        {
            "FlowID": "private-ood",
            "StartTime": 5,
            "LastTime": 15,
            "BinaryLabel": 1,
            "CategoryLabel": "dos",
            "SubCategoryLabel": "dos-icmp",
        }
    )
    write_metadata_rows(source, rows)
    output_dir = tmp_path / "plan"

    summary = forward_split.create_hybrid_forward_split(
        input_paths=[source],
        output_dir=output_dir,
        ratios=(0.5, 0.25, 0.25),
        ood_subtypes=frozenset({"dos-icmp"}),
    )

    summary_path = output_dir / "plan_summary.json"
    assignments_path = output_dir / "session_assignments.jsonl"
    assert summary_path.is_file()
    assert assignments_path.is_file()
    assert summary["source_files"][0]["sha256"]
    combined = summary_path.read_text() + assignments_path.read_text()
    assert "private-train" not in combined
    assert "private-ood" not in combined
    assert len(assignments_path.read_text().splitlines()) == 5


def test_materialize_genis_split_writes_domain_and_separate_ood_jsonl(
    tmp_path: Path,
) -> None:
    assert hasattr(forward_split, "materialize_genis_split")
    source = tmp_path / "mixed.csv"
    rows = []
    for index, start in enumerate((0, 10, 20, 30)):
        rows.append(
            {
                "FlowID": f"private-train-{index}",
                "StartTime": start,
                "LastTime": start + 1,
                "BinaryLabel": 1,
                "CategoryLabel": "bruteforce",
                "SubCategoryLabel": "bruteforce-ftp",
            }
        )
    rows.append(
        {
            "FlowID": "private-ood",
            "StartTime": 5,
            "LastTime": 15,
            "BinaryLabel": 1,
            "CategoryLabel": "dos",
            "SubCategoryLabel": "dos-icmp",
        }
    )
    write_training_rows(source, rows)
    plan_dir = tmp_path / "plan"
    forward_split.create_hybrid_forward_split(
        input_paths=[source],
        output_dir=plan_dir,
        ratios=(0.5, 0.25, 0.25),
        ood_subtypes=frozenset({"dos-icmp"}),
    )
    output_dir = tmp_path / "materialized"

    summary = forward_split.materialize_genis_split(
        input_paths=[source],
        assignments_path=plan_dir / "session_assignments.jsonl",
        output_dir=output_dir,
    )

    output_paths = [
        output_dir / "train.jsonl",
        output_dir / "validation.jsonl",
        output_dir / "test.jsonl",
        output_dir / "ood_dos-icmp.jsonl",
    ]
    assert all(path.is_file() for path in output_paths)
    records = [
        json.loads(line)
        for path in output_paths
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 5
    assert summary["schema_version"] == "genis_materialized_split_v2"
    assert summary["written_row_count"] == 5
    assert summary["purged_row_count"] == 0
    assert all(len(record["group_id"]) == 32 for record in records)
    assert all(
        set(record["features"])
        == {
            "total_packets",
            "total_bytes",
            "packet_length_mean",
            "packet_length_min",
            "packet_length_max",
            "iat_mean_ms",
            "packet_rate",
            "byte_rate",
        }
        for record in records
    )
    assert {record["attack_subtype"] for record in records} == {
        "bruteforce-ftp",
        "dos-icmp",
    }
    assert all(record["attack_subtype"] not in record["prompt"] for record in records)
    assert "private-train" not in json.dumps(records)
    assert "private-ood" not in json.dumps(records)
