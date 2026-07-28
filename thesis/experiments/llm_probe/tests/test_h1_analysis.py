import json
from pathlib import Path

import pytest

from flow_probe.h1_analysis import H1AnalysisError, aggregate_h1_files, main, summarize_values


def _write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _qwen_summary(seed: int, offset: float = 0.0) -> dict[str, object]:
    def result(macro_f1: float, unknown_recall: float | None, false_positive_rate: float):
        return {
            "candidate_scoring": {
                "metrics": {
                    "macro_f1": macro_f1 + offset,
                    "known_rejection_rate": 0.05 + offset,
                    "unknown_recall": unknown_recall,
                    "benign_false_positive_rate": false_positive_rate + offset,
                },
                "efficiency": {
                    "samples_per_second": 30.0 + offset,
                    "peak_gpu_memory_mib": 3400.0 + offset,
                },
            },
            "free_generation": {
                "metrics": {"macro_f1": macro_f1 + 0.01 + offset},
                "efficiency": {"samples_per_second": 20.0 + offset},
            },
        }

    return {
        "seed": seed,
        "threshold_calibration": {"threshold": 0.4 + offset},
        "results": {
            "family_test": result(0.90, None, 0.01),
            "subtype_test": result(0.80, None, 0.02),
            "ood_dos_icmp": result(0.50, 0.60, 0.10),
            "ood_dos_pushack": result(0.40, 0.50, 0.08),
            "ood_dos_udp": result(0.30, 0.40, 0.06),
        },
    }


def _training_summary(seed: int, offset: float = 0.0) -> dict[str, object]:
    return {
        "seed": seed,
        "metrics": {
            "train_runtime": 100.0 + offset,
            "train_samples_per_second": 10.0 + offset,
        },
    }


def _baseline_summary(seed: int, offset: float = 0.0) -> dict[str, object]:
    def evaluation(macro_f1: float, unknown_recall: float | None, false_positive_rate: float):
        return {
            "metrics": {
                "macro_f1": macro_f1 + offset,
                "known_rejection_rate": 0.04 + offset,
                "unknown_recall": unknown_recall,
                "benign_false_positive_rate": false_positive_rate + offset,
            }
        }

    model = {
        "fit_seconds": 2.0 + offset,
        "evaluations": {
            "test": evaluation(0.75, None, 0.03),
            "ood-dos-icmp": evaluation(0.50, 0.70, 0.12),
            "ood-dos-pushack": evaluation(0.40, 0.60, 0.10),
            "ood-dos-udp": evaluation(0.30, 0.50, 0.08),
        },
    }
    return {
        "seed": seed,
        "family": {
            "models": {
                "hist_gradient_boosting": {
                    "fit_seconds": 1.0 + offset,
                    "evaluations": {"test": evaluation(0.85, None, 0.01)},
                }
            }
        },
        "subtype": {"models": {"hist_gradient_boosting": model}},
    }


def test_summarize_values_reports_sample_statistics() -> None:
    summary = summarize_values([1.0, 2.0, 3.0])

    assert summary["n"] == 3
    assert summary["mean"] == pytest.approx(2.0)
    assert summary["sample_std"] == pytest.approx(1.0)
    assert summary["ci95_low"] < summary["mean"] < summary["ci95_high"]


def test_aggregate_h1_files_pairs_seeds_and_open_set_metrics(tmp_path: Path) -> None:
    qwen_paths = []
    training_paths = []
    baseline_paths = []
    for seed, offset in ((42, 0.00), (43, 0.01), (44, 0.02)):
        qwen_paths.append(_write_json(tmp_path / f"qwen-{seed}.json", _qwen_summary(seed, offset)))
        training_paths.append(
            _write_json(tmp_path / f"train-{seed}.json", _training_summary(seed, offset))
        )
        baseline_paths.append(
            _write_json(tmp_path / f"baseline-{seed}.json", _baseline_summary(seed, offset))
        )

    result = aggregate_h1_files(qwen_paths, training_paths, baseline_paths)

    assert result["seeds"] == [42, 43, 44]
    assert result["per_seed"][0]["qwen"]["ood_unknown_recall_mean"] == pytest.approx(0.5)
    assert result["per_seed"][0]["baseline"]["ood_unknown_recall_mean"] == pytest.approx(0.6)
    assert result["per_seed"][0]["paired_difference"][
        "subtype_candidate_macro_f1"
    ] == pytest.approx(0.05)
    assert result["aggregate"]["qwen"]["family_macro_f1"]["n"] == 3


def test_aggregate_h1_files_rejects_unpaired_seeds(tmp_path: Path) -> None:
    qwen = [_write_json(tmp_path / "qwen.json", _qwen_summary(42))]
    training = [_write_json(tmp_path / "train.json", _training_summary(42))]
    baseline = [_write_json(tmp_path / "baseline.json", _baseline_summary(43))]

    with pytest.raises(H1AnalysisError, match="随机种子不一致"):
        aggregate_h1_files(qwen, training, baseline)


def test_main_writes_reproducible_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    qwen = _write_json(tmp_path / "qwen.json", _qwen_summary(42))
    training = _write_json(tmp_path / "train.json", _training_summary(42))
    baseline = _write_json(tmp_path / "baseline.json", _baseline_summary(42))
    output = tmp_path / "summary.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "flow-probe-analyze-h1",
            "--qwen-evaluation",
            str(qwen),
            "--qwen-training",
            str(training),
            "--baseline",
            str(baseline),
            "--output",
            str(output),
        ],
    )

    main()

    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["schema_version"] == "flow_probe_h1_analysis_v1"
    assert written["seeds"] == [42]
