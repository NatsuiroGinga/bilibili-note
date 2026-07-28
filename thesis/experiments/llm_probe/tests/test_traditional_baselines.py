import gzip
import json
from pathlib import Path

import pytest

import flow_probe.traditional_baselines as traditional_baselines
from flow_probe.schemas import CANONICAL_CORE_FIELDS
from flow_probe.traditional_baselines import BaselineDataError, run_baseline_suite


def write_numeric_records(path: Path, values: list[tuple[str, float]]) -> None:
    with path.open("w", encoding="utf-8") as output:
        for index, (label, value) in enumerate(values):
            record = {
                "sample_id": f"sample-{index}",
                "group_id": f"group-{index}",
                "binary_label": label,
                "features": {field: value for field in CANONICAL_CORE_FIELDS},
            }
            output.write(json.dumps(record) + "\n")


def test_run_baseline_suite_compares_three_models_on_same_records(tmp_path: Path) -> None:
    train_path = tmp_path / "train.jsonl"
    test_path = tmp_path / "test.jsonl"
    write_numeric_records(
        train_path,
        [("benign", float(index)) for index in range(20)]
        + [("malicious", float(index + 100)) for index in range(20)],
    )
    write_numeric_records(
        test_path,
        [("benign", float(index)) for index in range(4)]
        + [("malicious", float(index + 100)) for index in range(4)],
    )

    summary = run_baseline_suite(
        train_path=train_path,
        evaluation_paths={"test": test_path},
        seed=42,
        predictions_path=tmp_path / "predictions.jsonl.gz",
    )

    assert set(summary["models"]) == {
        "majority",
        "logistic_regression",
        "hist_gradient_boosting",
    }
    for model in summary["models"].values():
        assert model["evaluations"]["test"]["metrics"]["sample_count"] == 8
        assert model["fit_seconds"] >= 0
    assert summary["models"]["logistic_regression"]["evaluations"]["test"]["metrics"][
        "macro_f1"
    ] == pytest.approx(1.0)
    assert summary["feature_fields"] == list(CANONICAL_CORE_FIELDS)
    with gzip.open(tmp_path / "predictions.jsonl.gz", "rt", encoding="utf-8") as source:
        predictions = [json.loads(line) for line in source]
    assert len(predictions) == 24
    assert {item["model"] for item in predictions} == set(summary["models"])


def test_run_baseline_suite_rejects_missing_numeric_features(tmp_path: Path) -> None:
    train_path = tmp_path / "train.jsonl"
    test_path = tmp_path / "test.jsonl"
    train_path.write_text(
        json.dumps(
            {
                "sample_id": "sample-1",
                "group_id": "group-1",
                "binary_label": "benign",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    write_numeric_records(test_path, [("benign", 1.0), ("malicious", 2.0)])

    with pytest.raises(BaselineDataError, match="features"):
        run_baseline_suite(
            train_path=train_path,
            evaluation_paths={"test": test_path},
            seed=42,
        )


def test_parse_evaluation_specs_rejects_duplicates_and_missing_separator(tmp_path: Path) -> None:
    assert hasattr(traditional_baselines, "parse_evaluation_specs")
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"

    assert traditional_baselines.parse_evaluation_specs([f"test={first}", f"ood={second}"]) == {
        "test": first,
        "ood": second,
    }
    with pytest.raises(BaselineDataError, match="重复"):
        traditional_baselines.parse_evaluation_specs([f"test={first}", f"test={second}"])
    with pytest.raises(BaselineDataError, match="名称=路径"):
        traditional_baselines.parse_evaluation_specs([str(first)])
