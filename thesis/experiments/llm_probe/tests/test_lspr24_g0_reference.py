from __future__ import annotations

import json
from pathlib import Path

import pytest

from flow_probe.lspr24_g0_reference import compare_reference, materialize_reference


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "lspr24_g0" / "canonical_vectors.json"
DEVELOPMENT_SCOPE = "development-visible-first-80-percent"


def _row(
    payload: int,
    endpoint: int,
    last_ns: int,
    start_ns: int,
    raw_flow: int,
    role: str,
    source_row_index: int,
) -> dict[str, object]:
    return {
        "protected_endpoint_id": f"{endpoint:02x}" * 32,
        "last_ns": last_ns,
        "start_ns": start_ns,
        "raw_flow_id": f"{raw_flow:02x}" * 32,
        "endpoint_role_order": role,
        "source_row_index": source_row_index,
        "values": [{"type": "u8", "value": payload}],
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_reference_materialization_matches_frozen_vectors_and_rejects_soft_equivalence(
    tmp_path: Path,
) -> None:
    vectors = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    vector_input = tmp_path / "development-vectors.json"
    vector_output = tmp_path / "development-vectors-reference.json"
    _write_json(
        vector_input,
        {
            "schema_version": "lspr24-g0-development-reference-input-v1",
            "scope": DEVELOPMENT_SCOPE,
            "rows": [
                {
                    "protected_endpoint_id": "00" * 32,
                    "last_ns": 1,
                    "start_ns": 0,
                    "raw_flow_id": "10" * 32,
                    "endpoint_role_order": "source",
                    "source_row_index": 0,
                    "values": [
                        {"type": "null"},
                        {"type": "bool", "value": True},
                        {"type": "i64", "value": -2},
                        {"type": "u16", "value": 0x1234},
                        {"type": "utf8", "value": "Aé"},
                        {"type": "bytes", "value_hex": "00ff"},
                    ],
                },
                {
                    "protected_endpoint_id": "01" * 32,
                    "last_ns": 2,
                    "start_ns": 1,
                    "raw_flow_id": "20" * 32,
                    "endpoint_role_order": "destination",
                    "source_row_index": 1,
                    "values": [
                        {"type": "utf8", "value": ""},
                        {"type": "null"},
                        {"type": "bool", "value": False},
                        {"type": "u64", "value": 1},
                        {"type": "fixed_decimal_12", "value": "-0.000000000001"},
                    ],
                },
            ],
        },
    )

    materialized = materialize_reference(vector_input, vector_output)

    assert [row["canonical_hex"] for row in materialized["rows"]] == [
        vectors["mixed_tuple_hex"],
        vectors["second_row_hex"],
    ]
    assert [row["row_sha256"] for row in materialized["rows"]] == [
        vectors["mixed_tuple_sha256"],
        vectors["second_row_sha256"],
    ]
    assert materialized["dataset_semantic_sha256"] == vectors["ordered_dataset_sha256"]
    assert materialized["rows"][1]["values"][4] == {
        "type": "fixed_decimal_12",
        "quantized_integer": "-1",
    }
    assert compare_reference(vector_output, vector_output)["status"] == "PASS"

    original_bytes = vector_output.read_bytes()
    with pytest.raises(FileExistsError):
        materialize_reference(vector_input, vector_output)
    assert vector_output.read_bytes() == original_bytes

    mismatched_output = tmp_path / "mismatched-reference.json"
    mismatched = json.loads(vector_output.read_text(encoding="utf-8"))
    mismatched["rows"][1]["values"][4]["quantized_integer"] = "0"
    _write_json(mismatched_output, mismatched)
    with pytest.raises(ValueError, match="硬一致"):
        compare_reference(vector_output, mismatched_output)

    sort_input = tmp_path / "development-sort.json"
    sort_output = tmp_path / "development-sort-reference.json"
    rows = [
        _row(0x10, 0, 99, 1, 9, "destination", 9),
        _row(0x20, 1, 9, 1, 9, "destination", 9),
        _row(0x30, 1, 10, 0, 9, "destination", 9),
        _row(0x40, 1, 10, 1, 0, "destination", 9),
        _row(0x50, 1, 10, 1, 1, "source", 3),
        _row(0x60, 1, 10, 1, 1, "source", 4),
        _row(0x70, 1, 10, 1, 1, "destination", 1),
        _row(0x80, 2, -99, -100, 0, "source", 0),
    ]
    _write_json(
        sort_input,
        {
            "schema_version": "lspr24-g0-development-reference-input-v1",
            "scope": DEVELOPMENT_SCOPE,
            "rows": [rows[index] for index in [6, 2, 7, 4, 0, 5, 1, 3]],
        },
    )

    sorted_reference = materialize_reference(sort_input, sort_output)

    assert [row["values"][0]["value"] for row in sorted_reference["rows"]] == [
        0x10,
        0x20,
        0x30,
        0x40,
        0x50,
        0x60,
        0x70,
        0x80,
    ]
    assert [row["stable_key"]["source_row_index"] for row in sorted_reference["rows"]] == [
        9,
        9,
        9,
        9,
        3,
        4,
        1,
        0,
    ]

    final_input = tmp_path / "final-test.json"
    final_output = tmp_path / "forbidden-final-reference.json"
    _write_json(
        final_input,
        {
            "schema_version": "lspr24-g0-development-reference-input-v1",
            "scope": "final-test",
            "rows": [],
        },
    )
    with pytest.raises(ValueError, match="最终区"):
        materialize_reference(final_input, final_output)
    assert not final_output.exists()
