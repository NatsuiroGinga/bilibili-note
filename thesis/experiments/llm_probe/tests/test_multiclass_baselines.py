import gzip
import importlib
import importlib.util
import json
from pathlib import Path

from flow_probe.schemas import CANONICAL_CORE_FIELDS

KNOWN_LABELS = ("benign", "ftp", "hulk")


def _record(split: str, label: str, index: int) -> dict[str, object]:
    centers = {"benign": 0.0, "ftp": 10.0, "hulk": 20.0, "unknown_attack": 30.0}
    center = centers[label]
    return {
        "sample_id": f"{split}-{label}-{index}",
        "task_label": label,
        "features": {field: center + index / 100 for field in CANONICAL_CORE_FIELDS},
    }


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def test_multiclass_baselines_calibrate_unknown_only_on_known_validation(
    tmp_path: Path,
) -> None:
    assert importlib.util.find_spec("flow_probe.multiclass_baselines") is not None
    module = importlib.import_module("flow_probe.multiclass_baselines")
    train_path = tmp_path / "train.jsonl"
    validation_path = tmp_path / "validation.jsonl"
    test_path = tmp_path / "test.jsonl"
    ood_path = tmp_path / "ood.jsonl"
    _write_jsonl(
        train_path,
        [_record("train", label, index) for label in KNOWN_LABELS for index in range(20)],
    )
    _write_jsonl(
        validation_path,
        [_record("validation", label, index) for label in KNOWN_LABELS for index in range(10)],
    )
    _write_jsonl(
        test_path,
        [_record("test", label, index) for label in KNOWN_LABELS for index in range(10)],
    )
    _write_jsonl(
        ood_path,
        [
            *(_record("ood", "benign", index) for index in range(5)),
            *(_record("ood", "unknown_attack", index) for index in range(5)),
        ],
    )
    predictions_path = tmp_path / "predictions.jsonl.gz"

    summary = module.run_multiclass_baseline_suite(
        train_path=train_path,
        validation_path=validation_path,
        evaluation_paths={"test": test_path, "ood": ood_path},
        known_labels=KNOWN_LABELS,
        unknown_label="unknown_attack",
        max_known_rejection_rate=0.1,
        seed=42,
        predictions_path=predictions_path,
    )

    assert summary["schema_version"] == "flow_probe_multiclass_baselines_v1"
    assert summary["known_labels"] == list(KNOWN_LABELS)
    assert summary["unknown_label"] == "unknown_attack"
    assert set(summary["models"]) == {
        "majority",
        "logistic_regression",
        "hist_gradient_boosting",
    }
    for result in summary["models"].values():
        assert result["calibration"]["uses_ood_labels"] is False
        assert result["calibration"]["known_rejection_rate"] <= 0.1
        assert 0 <= result["evaluations"]["ood"]["metrics"]["unknown_recall"] <= 1
        assert 0 <= result["evaluations"]["ood"]["metrics"]["benign_false_positive_rate"] <= 1
    with gzip.open(predictions_path, "rt", encoding="utf-8") as source:
        prediction_rows = [json.loads(line) for line in source]
    assert prediction_rows
    assert {row["evaluation"] for row in prediction_rows} == {"test", "ood"}
