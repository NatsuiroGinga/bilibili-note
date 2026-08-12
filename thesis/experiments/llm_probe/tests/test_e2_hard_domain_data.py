"""E2 困难域冻结开发视图的最小合同测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest


FEATURE_FIELDS = (
    "duration",
    "orig_bytes",
    "resp_bytes",
    "orig_pkts",
    "resp_pkts",
    "orig_ip_bytes",
    "resp_ip_bytes",
)


def _data_api():
    try:
        from flow_probe.e2_hard_domain_data import (
            E2_FEATURE_FIELDS,
            E2HardDomainDataError,
            build_e2_panel,
            load_e2_development_view,
            samples_to_model_matrix,
        )
    except ModuleNotFoundError:
        pytest.fail("缺少 E2 困难域数据视图模块")
    return (
        E2_FEATURE_FIELDS,
        E2HardDomainDataError,
        build_e2_panel,
        load_e2_development_view,
        samples_to_model_matrix,
    )


def _write_manifest(path: Path, sample_ids: list[str], split_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps({"sample_id": sample_id, "split_id": split_id}, ensure_ascii=False)
        for sample_id in sample_ids
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_development_protocol(root: Path) -> None:
    rows = []
    for index, (sample_id, profile, split_id, label) in enumerate(
        (
            ("train-b", "B", "train", "non_c2"),
            ("train-a", "A", "train", "malicious_c2"),
            ("train-d", "D", "train", "non_c2"),
            ("cal-a", "A", "calibration", "malicious_c2"),
            ("valid-a", "A", "validation", "non_c2"),
            ("valid-b", "B", "validation", "malicious_c2"),
            ("valid-c2", "C", "validation", "non_c2"),
            ("valid-c1", "C", "validation", "malicious_c2"),
            ("valid-d", "D", "validation", "malicious_c2"),
        )
    ):
        row = {
            "sample_id": sample_id,
            "capture_id": f"capture-{profile}",
            "profile": profile,
            "development_split": split_id,
            "binary_label": label,
        }
        row.update({field: float(index + field_index + 1) for field_index, field in enumerate(FEATURE_FIELDS)})
        rows.append(row)
    pd.DataFrame(rows).to_parquet(root / "samples.parquet", index=False)
    _write_manifest(root / "splits/train.jsonl", ["train-b", "train-a", "train-d"], "train")
    _write_manifest(root / "splits/calibration.jsonl", ["cal-a"], "calibration")
    _write_manifest(root / "splits/validation_A.jsonl", ["valid-a"], "validation")
    _write_manifest(root / "splits/validation_B.jsonl", ["valid-b"], "validation")
    _write_manifest(root / "splits/validation_C.jsonl", ["valid-c2", "valid-c1"], "validation")
    _write_manifest(root / "splits/validation_D.jsonl", ["valid-d"], "validation")


def test_development_view_rejects_final_test_and_unknown_feature_request(tmp_path: Path) -> None:
    _, error_type, _, load_view, _ = _data_api()
    _write_development_protocol(tmp_path)
    _write_manifest(tmp_path / "splits/final_test.jsonl", ["held-out"], "test")

    with pytest.raises(error_type, match="最终测试"):
        load_view(tmp_path)

    (tmp_path / "splits/final_test.jsonl").unlink()
    with pytest.raises(error_type, match="七字段"):
        load_view(tmp_path, feature_fields=(*FEATURE_FIELDS, "profile"))


def test_panel_preserves_frozen_manifest_order_and_keeps_c_out_of_source(tmp_path: Path) -> None:
    fields, _, build_panel, load_view, to_matrix = _data_api()
    _write_development_protocol(tmp_path)

    parquet_columns = set(pd.read_parquet(tmp_path / "samples.parquet").columns)
    assert "development_split" in parquet_columns
    assert "split_id" not in parquet_columns
    samples = load_view(tmp_path)
    panel = build_panel(samples, panel="abd_to_c")
    labels_by_id = {sample.sample_id: sample.label for sample in samples}

    assert fields == FEATURE_FIELDS
    assert labels_by_id["train-b"] == 0
    assert labels_by_id["train-a"] == 1
    assert [sample.sample_id for sample in panel.train] == ["train-b", "train-a", "train-d"]
    assert [sample.sample_id for sample in panel.calibration] == ["cal-a"]
    assert [sample.sample_id for sample in panel.target] == ["valid-c2", "valid-c1"]
    assert {sample.profile for sample in panel.train} == {"A", "B", "D"}
    assert {sample.profile for sample in panel.target} == {"C"}
    assert {sample.sample_id for sample in panel.train}.isdisjoint(
        sample.sample_id for sample in panel.target
    )
    matrix = to_matrix(panel.train)
    assert matrix.shape == (3, 7)
    assert matrix[0].tolist() == [float(index + 1) for index in range(7)]


def test_development_view_rejects_unknown_binary_label(tmp_path: Path) -> None:
    _, error_type, _, load_view, _ = _data_api()
    _write_development_protocol(tmp_path)
    samples_path = tmp_path / "samples.parquet"
    frame = pd.read_parquet(samples_path)
    frame.loc[frame["sample_id"] == "train-b", "binary_label"] = "unknown_label"
    frame.to_parquet(samples_path, index=False)

    with pytest.raises(error_type, match="标签非法"):
        load_view(tmp_path)
