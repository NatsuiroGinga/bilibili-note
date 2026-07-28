import csv
from pathlib import Path

import pytest

from flow_probe.genis_audit import GeNISAuditError, audit_genis_paths

FIELDS = (
    "FlowID",
    "StartTime",
    "LastTime",
    "BinaryLabel",
    "CategoryLabel",
    "SubCategoryLabel",
)


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_audit_genis_paths_reports_sessions_time_and_subtypes(tmp_path: Path) -> None:
    source = tmp_path / "attack.csv"
    write_rows(
        source,
        [
            {
                "FlowID": "flow-a",
                "StartTime": "1000",
                "LastTime": "1005",
                "BinaryLabel": "1",
                "CategoryLabel": "dos",
                "SubCategoryLabel": "udp-flood",
            },
            {
                "FlowID": "flow-a",
                "StartTime": "1010",
                "LastTime": "1015",
                "BinaryLabel": "1",
                "CategoryLabel": "dos",
                "SubCategoryLabel": "udp-flood",
            },
            {
                "FlowID": "flow-b",
                "StartTime": "1020",
                "LastTime": "1025",
                "BinaryLabel": "0",
                "CategoryLabel": "benign",
                "SubCategoryLabel": "benign",
            },
        ],
    )

    audit = audit_genis_paths([source])

    assert audit["row_count"] == 3
    assert audit["session_count"] == 2
    assert audit["repeated_window_count"] == 1
    assert audit["binary_label_rows"] == {"0": 1, "1": 2}
    assert audit["subtype_rows"] == {"benign": 1, "udp-flood": 2}
    assert audit["subtype_sessions"] == {"benign": 1, "udp-flood": 1}
    assert audit["time_range"] == {
        "last_max": 1025.0,
        "last_min": 1005.0,
        "start_max": 1020.0,
        "start_min": 1000.0,
    }
    assert audit["session_window_count"]["max"] == 2
    assert audit["session_window_count"]["mean"] == pytest.approx(1.5)
    assert audit["session_label_conflicts"] == 0
    assert audit["session_subtype_conflicts"] == 0
    assert audit["input_files"][0]["start_time_count"] == 3
    assert audit["input_files"][0]["session_start_time_count"] == 2
    assert audit["input_files"][0]["session_last_time_count"] == 2
    assert audit["input_files"][0]["rows_per_start_time_mean"] == pytest.approx(1.0)
    assert audit["input_files"][0]["start_gap_seconds"] == {
        "max": 10.0,
        "min": 10.0,
        "p50": 10.0,
        "p95": 10.0,
    }
    assert "flow-a" not in str(audit)


def test_audit_genis_paths_counts_inconsistent_sessions(tmp_path: Path) -> None:
    source = tmp_path / "conflict.csv"
    write_rows(
        source,
        [
            {
                "FlowID": "flow-conflict",
                "StartTime": "1000",
                "LastTime": "1001",
                "BinaryLabel": "0",
                "CategoryLabel": "benign",
                "SubCategoryLabel": "benign",
            },
            {
                "FlowID": "flow-conflict",
                "StartTime": "1002",
                "LastTime": "1003",
                "BinaryLabel": "1",
                "CategoryLabel": "dos",
                "SubCategoryLabel": "udp-flood",
            },
        ],
    )

    audit = audit_genis_paths([source])

    assert audit["session_label_conflicts"] == 1
    assert audit["session_subtype_conflicts"] == 1
    assert audit["subtype_sessions"] == {"benign|udp-flood": 1}


def test_audit_genis_paths_rejects_missing_required_columns(tmp_path: Path) -> None:
    source = tmp_path / "missing.csv"
    source.write_text("FlowID,StartTime\nflow-a,1000\n", encoding="utf-8")

    with pytest.raises(GeNISAuditError, match="缺少审计字段"):
        audit_genis_paths([source])


def test_audit_genis_paths_rejects_invalid_timestamp(tmp_path: Path) -> None:
    source = tmp_path / "invalid-time.csv"
    write_rows(
        source,
        [
            {
                "FlowID": "flow-a",
                "StartTime": "not-a-time",
                "LastTime": "1001",
                "BinaryLabel": "0",
                "CategoryLabel": "benign",
                "SubCategoryLabel": "benign",
            }
        ],
    )

    with pytest.raises(GeNISAuditError, match="时间戳"):
        audit_genis_paths([source])
