"""汇总 R2 DistilBERT 物理旁路探针的三种子开发集结果。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


SEEDS = (42, 43, 44)
VARIANTS = ("T-A", "T-P", "T-S", "T-R")
VARIANT_SLUGS = {"T-A": "t-a", "T-P": "t-p", "T-S": "t-s", "T-R": "t-r"}
COMPARATORS = ("T-A", "T-S", "T-R")
COMPARISON_NAMES = {"T-A": "P-A", "T-S": "P-S", "T-R": "P-R"}
METRICS = (
    "macro_f1",
    "benign_false_positive_rate",
    "brier_score",
    "expected_calibration_error",
)
EXPECTED_SAMPLE_COUNT = 512
EXPECTED_STAGE = "theory_selection"
EXPECTED_PROTOCOL_STATUS = "review_pending"
EXPECTED_SELECTION_SPLIT = "validation"
EXPECTED_OPTIMIZER_STEPS = 192
CALIBRATION_BINS = 15
THRESHOLD = 0.5
INPUT_BINDING_SCHEMA = "flow_probe_r2_distilbert_sidecar_input_v1"
RUN_BINDING_SCHEMA = "flow_probe_r2_distilbert_sidecar_run_binding_v2"
ARTIFACT_SCHEMA = "flow_probe_r2_distilbert_sidecar_artifacts_v1"
PREDICTION_FIELDS = frozenset(
    {
        "sample_id",
        "stable_order",
        "probability_malicious",
        "prediction",
        "prediction_label",
        "label",
        "label_name",
    }
)
SEMANTIC_DEPENDENCIES = frozenset(
    {
        "r2_physics_sidecar_signal.py",
        "r2_protocol_contract.py",
        "shared_b0_view.py",
        "shared_b0_distilbert_baseline.py",
        "tracking.py",
    }
)
EXPECTED_INPUT_DIGESTS = {
    "input_summary": "028d18d41d5703b3792f6440948716edea43b6f45ddf1ebb427f816ebd829462",
    "detection_view": "6d8019dc15f2cd11abc2b4aa8a92ca81608b8000ef0c39eb83aae04607d9a126",
    "sidecar": "56658ea8886a57cdefe1dba2268e658f9072e24a94b93d5bf7a3711db9de2553",
}
REQUIRED_MANIFEST_ARTIFACTS = (
    "config_snapshot.json",
    "finalization_receipt.json",
    "best_model_receipt.json",
    "input_binding.json",
    "model_binding.json",
    "run_binding.json",
    "summary.json",
    "metrics/validation_metrics.json",
    "predictions/validation_predictions.jsonl",
)


class R2DistilBertMultiseedAnalysisError(ValueError):
    """三种子制品不符合冻结开发集分析合同。"""


@dataclass(frozen=True)
class VariantArtifacts:
    seed: int
    variant: str
    root: Path
    metrics_path: Path
    predictions_path: Path
    artifact_manifest_path: Path
    run_binding_path: Path
    input_binding_path: Path
    metrics: Mapping[str, float | int]
    predictions: tuple[Mapping[str, object], ...]
    artifact_manifest: Mapping[str, object]
    run_binding: Mapping[str, object]
    input_binding: Mapping[str, object]


def _read_json(path: Path, description: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise R2DistilBertMultiseedAnalysisError(
            f"无法读取{description}：{path}"
        ) from error
    if not isinstance(value, dict):
        raise R2DistilBertMultiseedAnalysisError(f"{description}顶层必须是对象：{path}")
    return value


def _read_jsonl(path: Path, description: str) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    try:
        with path.open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise R2DistilBertMultiseedAnalysisError(
                        f"{description}第 {line_number} 行必须是对象：{path}"
                    )
                rows.append(value)
    except (OSError, json.JSONDecodeError) as error:
        raise R2DistilBertMultiseedAnalysisError(
            f"无法读取{description}：{path}"
        ) from error
    if not rows:
        raise R2DistilBertMultiseedAnalysisError(f"{description}不能为空：{path}")
    return tuple(rows)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise R2DistilBertMultiseedAnalysisError(f"{description}必须是对象")
    return value


def _integer(value: object, description: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise R2DistilBertMultiseedAnalysisError(f"{description}必须是整数")
    return value


def _number(value: object, description: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise R2DistilBertMultiseedAnalysisError(f"{description}必须是数值")
    result = float(value)
    if not math.isfinite(result):
        raise R2DistilBertMultiseedAnalysisError(f"{description}必须是有限数")
    return result


def _expected_sha256(value: object, description: str) -> str:
    digest = str(value)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise R2DistilBertMultiseedAnalysisError(f"{description}必须是小写 SHA-256")
    return digest


def _regular_file(path: Path, description: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise R2DistilBertMultiseedAnalysisError(f"{description}不是普通文件：{path}")
    return path


def _record_input_file(
    path: Path,
    description: str,
    consumed: dict[Path, dict[str, object]],
) -> dict[str, object]:
    _regular_file(path, description)
    resolved = path.resolve()
    record = consumed.get(resolved)
    if record is None:
        record = {"sha256": _sha256_file(path), "size_bytes": path.stat().st_size}
        consumed[resolved] = record
    return record


def _validate_artifact_manifest(
    root: Path,
    manifest: Mapping[str, object],
    consumed: dict[Path, dict[str, object]],
) -> Mapping[str, object]:
    records = _mapping(manifest.get("artifacts"), f"{root} 制品记录")
    if _integer(manifest.get("artifact_count"), f"{root} artifact_count") != len(records):
        raise R2DistilBertMultiseedAnalysisError(f"制品清单计数不一致：{root}")
    recorded_paths: set[str] = set()
    for raw_relative, raw_record in records.items():
        relative = str(raw_relative)
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise R2DistilBertMultiseedAnalysisError(f"制品清单含越界路径：{relative}")
        if relative.startswith("checkpoint-") or "/checkpoint-" in relative:
            raise R2DistilBertMultiseedAnalysisError(f"完成组仍登记训练检查点：{root / relative}")
        lowered = relative.lower()
        if any(
            token in lowered
            for token in (
                "final-test",
                "final_test",
                "test_predictions",
                "predictions/test",
                "metrics/test",
            )
        ):
            raise R2DistilBertMultiseedAnalysisError(f"完成组登记了疑似最终测试制品：{relative}")
        record = _mapping(raw_record, f"制品记录 {relative}")
        expected_size = _integer(record.get("size_bytes"), f"制品 {relative} 大小")
        _expected_sha256(record.get("sha256"), f"制品 {relative} 哈希")
        path = root / relative_path
        _regular_file(path, f"登记制品 {relative}")
        if path.stat().st_size != expected_size:
            raise R2DistilBertMultiseedAnalysisError(f"登记制品大小不一致：{path}")
        recorded_paths.add(relative_path.as_posix())
    actual_paths: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise R2DistilBertMultiseedAnalysisError(f"组目录含符号链接：{path}")
        if path.is_file() and path != root / "artifact_manifest.json" and path != root / "run_state.json":
            actual_paths.add(path.relative_to(root).as_posix())
    if actual_paths != recorded_paths:
        missing = sorted(recorded_paths.difference(actual_paths))
        extra = sorted(actual_paths.difference(recorded_paths))
        raise R2DistilBertMultiseedAnalysisError(
            f"制品清单与组目录不一致：缺失={missing}，未登记={extra}"
        )
    for relative in REQUIRED_MANIFEST_ARTIFACTS:
        if relative not in records:
            raise R2DistilBertMultiseedAnalysisError(f"制品清单缺少必要文件：{root / relative}")
        path = root / relative
        actual = _record_input_file(path, f"分析输入 {relative}", consumed)
        record = _mapping(records[relative], f"必要制品记录 {relative}")
        if actual["sha256"] != record.get("sha256") or actual["size_bytes"] != record.get(
            "size_bytes"
        ):
            raise R2DistilBertMultiseedAnalysisError(f"必要制品哈希或大小不一致：{path}")
    model_selection = root / "model-selection"
    selected = (
        [path for path in model_selection.iterdir() if path.is_dir() and not path.is_symlink()]
        if model_selection.is_dir() and not model_selection.is_symlink()
        else []
    )
    if len(selected) != 1:
        raise R2DistilBertMultiseedAnalysisError(f"完成组必须只保留一个最佳模型：{root}")
    if any(path.is_dir() and path.name.startswith("checkpoint-") for path in root.iterdir()):
        raise R2DistilBertMultiseedAnalysisError(f"完成组仍保留训练检查点目录：{root}")
    return records


def _split_binding(
    input_binding: Mapping[str, object], variant: str, split: str
) -> Mapping[str, object]:
    variants = _mapping(input_binding.get("variants"), "输入绑定 variants")
    if set(variants) != set(VARIANTS):
        raise R2DistilBertMultiseedAnalysisError("输入绑定必须精确包含 T-A/T-P/T-S/T-R")
    variant_binding = _mapping(variants.get(variant), f"输入绑定 {variant}")
    splits = _mapping(variant_binding.get("splits"), f"输入绑定 {variant}.splits")
    if set(splits) != {"train-fit", "validation"}:
        raise R2DistilBertMultiseedAnalysisError(f"{variant} 输入绑定划分非法")
    return _mapping(splits.get(split), f"输入绑定 {variant}.{split}")


def _validate_input_binding(
    input_binding: Mapping[str, object], seed: int, variant: str
) -> None:
    if input_binding.get("schema_version") != INPUT_BINDING_SCHEMA:
        raise R2DistilBertMultiseedAnalysisError("输入绑定模式版本不一致")
    if (
        input_binding.get("stage") != EXPECTED_STAGE
        or input_binding.get("status") != EXPECTED_PROTOCOL_STATUS
        or input_binding.get("final_test_visible") is not False
        or input_binding.get("source_dataset") != "TQH-C2"
    ):
        raise R2DistilBertMultiseedAnalysisError("输入绑定不是冻结 TQH-C2 开发验证合同")
    for name, expected_digest in EXPECTED_INPUT_DIGESTS.items():
        artifact = _mapping(input_binding.get(name), f"输入绑定 {name}")
        if artifact.get("sha256") != expected_digest:
            raise R2DistilBertMultiseedAnalysisError(f"输入绑定 {name} 摘要不符合冻结合同")
    variants = _mapping(input_binding.get("variants"), "输入绑定 variants")
    for expected_variant in VARIANTS:
        bound = _mapping(variants.get(expected_variant), f"输入绑定 {expected_variant}")
        if bound.get("variant") != expected_variant or bound.get("seed") != seed:
            raise R2DistilBertMultiseedAnalysisError(
                f"种子 {seed} 的 {expected_variant} 输入身份不一致"
            )
        if bound.get("label_used_for_transformation") is not False:
            raise R2DistilBertMultiseedAnalysisError(f"{expected_variant} 负对照错误使用标签")
        for split, expected_count in (("train-fit", 2048), ("validation", 512)):
            split_values = _split_binding(input_binding, expected_variant, split)
            if split_values.get("sample_count") != expected_count:
                raise R2DistilBertMultiseedAnalysisError(
                    f"{expected_variant} 的 {split} 样本数不一致"
                )
            for field in ("sample_order_sha256", "text_sha256", "label_sha256"):
                _expected_sha256(split_values.get(field), f"{expected_variant}.{split}.{field}")
            expected_active = 0 if expected_variant == "T-A" else expected_count
            if split_values.get("sidecar_mask_active_count") != expected_active:
                raise R2DistilBertMultiseedAnalysisError(
                    f"{expected_variant} 的 {split} 旁路启用计数不一致"
                )
    _split_binding(input_binding, variant, "validation")


def _compute_metrics(rows: Sequence[Mapping[str, object]]) -> dict[str, float | int]:
    labels = [int(row["label"]) for row in rows]
    probabilities = [float(row["probability_malicious"]) for row in rows]
    predictions = [int(probability >= THRESHOLD) for probability in probabilities]
    counts: dict[str, int] = {}
    counts["true_positive"] = sum(
        label == 1 and prediction == 1
        for label, prediction in zip(labels, predictions, strict=True)
    )
    counts["true_negative"] = sum(
        label == 0 and prediction == 0
        for label, prediction in zip(labels, predictions, strict=True)
    )
    counts["false_positive"] = sum(
        label == 0 and prediction == 1
        for label, prediction in zip(labels, predictions, strict=True)
    )
    counts["false_negative"] = sum(
        label == 1 and prediction == 0
        for label, prediction in zip(labels, predictions, strict=True)
    )

    def divide(numerator: int | float, denominator: int | float) -> float:
        return float(numerator / denominator) if denominator else 0.0

    class_f1: list[float] = []
    for label in (0, 1):
        true_positive = sum(
            actual == label and predicted == label
            for actual, predicted in zip(labels, predictions, strict=True)
        )
        false_positive = sum(
            actual != label and predicted == label
            for actual, predicted in zip(labels, predictions, strict=True)
        )
        false_negative = sum(
            actual == label and predicted != label
            for actual, predicted in zip(labels, predictions, strict=True)
        )
        denominator = 2 * true_positive + false_positive + false_negative
        class_f1.append(divide(2 * true_positive, denominator))

    confidences = [max(probability, 1.0 - probability) for probability in probabilities]
    correctness = [
        float(label == prediction)
        for label, prediction in zip(labels, predictions, strict=True)
    ]
    calibration_error = 0.0
    for index in range(CALIBRATION_BINS):
        lower = index / CALIBRATION_BINS
        upper = (index + 1) / CALIBRATION_BINS
        members = [
            position
            for position, confidence in enumerate(confidences)
            if (confidence >= lower if index == 0 else confidence > lower)
            and confidence <= upper
        ]
        if members:
            calibration_error += len(members) / len(rows) * abs(
                statistics.fmean(correctness[position] for position in members)
                - statistics.fmean(confidences[position] for position in members)
            )
    return {
        "sample_count": len(rows),
        "macro_f1": statistics.fmean(class_f1),
        "benign_false_positive_rate": divide(
            counts["false_positive"], counts["true_negative"] + counts["false_positive"]
        ),
        "brier_score": statistics.fmean(
            (probability - label) ** 2
            for probability, label in zip(probabilities, labels, strict=True)
        ),
        "expected_calibration_error": calibration_error,
        **counts,
    }


def _validate_predictions(
    rows: Sequence[Mapping[str, object]],
    split_binding: Mapping[str, object],
    description: str,
) -> dict[str, float | int]:
    if len(rows) != EXPECTED_SAMPLE_COUNT:
        raise R2DistilBertMultiseedAnalysisError(
            f"{description}预测数必须为 {EXPECTED_SAMPLE_COUNT}"
        )
    sample_ids: list[str] = []
    stable_orders: list[int] = []
    labels: list[int] = []
    for index, row in enumerate(rows):
        if set(row) != PREDICTION_FIELDS:
            raise R2DistilBertMultiseedAnalysisError(f"{description}第 {index} 行字段不一致")
        sample_id = row.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id:
            raise R2DistilBertMultiseedAnalysisError(f"{description}第 {index} 行 sample_id 非法")
        stable_order = _integer(row.get("stable_order"), f"{description}第 {index} 行 stable_order")
        label = _integer(row.get("label"), f"{description}第 {index} 行 label")
        prediction = _integer(row.get("prediction"), f"{description}第 {index} 行 prediction")
        probability = _number(
            row.get("probability_malicious"), f"{description}第 {index} 行恶意概率"
        )
        if label not in (0, 1) or prediction not in (0, 1) or not 0.0 <= probability <= 1.0:
            raise R2DistilBertMultiseedAnalysisError(f"{description}第 {index} 行二分类值非法")
        expected_prediction = int(probability >= THRESHOLD)
        label_name = "benign" if label == 0 else "malicious"
        prediction_name = "benign" if prediction == 0 else "malicious"
        if (
            prediction != expected_prediction
            or row.get("label_name") != label_name
            or row.get("prediction_label") != prediction_name
        ):
            raise R2DistilBertMultiseedAnalysisError(f"{description}第 {index} 行预测合同不一致")
        sample_ids.append(sample_id)
        stable_orders.append(stable_order)
        labels.append(label)
    if len(set(sample_ids)) != len(sample_ids):
        raise R2DistilBertMultiseedAnalysisError(f"{description}含重复 sample_id")
    if len(set(stable_orders)) != len(stable_orders):
        raise R2DistilBertMultiseedAnalysisError(f"{description}含重复 stable_order")
    sample_digest = hashlib.sha256("\n".join(sample_ids).encode("utf-8")).hexdigest()
    label_digest = hashlib.sha256(bytes(labels)).hexdigest()
    if sample_digest != split_binding.get("sample_order_sha256"):
        raise R2DistilBertMultiseedAnalysisError(f"{description}样本顺序与输入绑定不一致")
    if label_digest != split_binding.get("label_sha256"):
        raise R2DistilBertMultiseedAnalysisError(f"{description}标签与输入绑定不一致")
    return _compute_metrics(rows)


def _validate_run_binding(
    run_binding: Mapping[str, object],
    input_binding: Mapping[str, object],
    model_binding: Mapping[str, object],
    seed: int,
    variant: str,
) -> None:
    if run_binding.get("schema_version") != RUN_BINDING_SCHEMA:
        raise R2DistilBertMultiseedAnalysisError("运行绑定模式版本不一致")
    if (
        run_binding.get("seed") != seed
        or run_binding.get("variant") != variant
        or run_binding.get("final_test_visible") is not False
    ):
        raise R2DistilBertMultiseedAnalysisError(f"种子 {seed} 的 {variant} 运行身份不一致")
    sample_counts = _mapping(run_binding.get("sample_counts"), "运行绑定 sample_counts")
    if sample_counts != {"train-fit": 2048, "validation": 512}:
        raise R2DistilBertMultiseedAnalysisError("运行绑定样本数不符合冻结合同")
    if run_binding.get("expected_optimizer_steps") != EXPECTED_OPTIMIZER_STEPS:
        raise R2DistilBertMultiseedAnalysisError("运行绑定优化步预算不一致")
    _expected_sha256(run_binding.get("implementation_sha256"), "实现摘要")
    _expected_sha256(run_binding.get("config_file_sha256"), "配置文件摘要")
    dependencies = _mapping(
        run_binding.get("semantic_dependency_sha256"), "运行绑定语义依赖摘要"
    )
    if set(dependencies) != SEMANTIC_DEPENDENCIES:
        raise R2DistilBertMultiseedAnalysisError("运行绑定没有精确覆盖五项语义依赖")
    for filename, digest in dependencies.items():
        _expected_sha256(digest, f"语义依赖 {filename}")
    if run_binding.get("input_binding_sha256") != _canonical_sha256(input_binding):
        raise R2DistilBertMultiseedAnalysisError("运行绑定与输入绑定摘要不一致")
    variants = _mapping(input_binding.get("variants"), "输入绑定 variants")
    if run_binding.get("variant_binding_sha256") != _canonical_sha256(variants[variant]):
        raise R2DistilBertMultiseedAnalysisError("运行绑定与组输入摘要不一致")
    if run_binding.get("model_binding_sha256") != _canonical_sha256(model_binding):
        raise R2DistilBertMultiseedAnalysisError("运行绑定与模型绑定摘要不一致")
    config = _mapping(run_binding.get("config"), "运行绑定 config")
    if config.get("schema_version") != "flow_probe_r2_distilbert_sidecar_probe_config_v2":
        raise R2DistilBertMultiseedAnalysisError("运行配置快照版本不一致")
    dataset = _mapping(config.get("dataset"), "运行配置 dataset")
    for name, expected_digest in EXPECTED_INPUT_DIGESTS.items():
        configured = _mapping(dataset.get(name), f"运行配置 dataset.{name}")
        if configured.get("sha256") != expected_digest:
            raise R2DistilBertMultiseedAnalysisError(f"运行配置 {name} 摘要漂移")
    run = _mapping(config.get("run"), "运行配置 run")
    if (
        run.get("seed") != seed
        or run.get("stage") != EXPECTED_STAGE
        or run.get("status") != EXPECTED_PROTOCOL_STATUS
    ):
        raise R2DistilBertMultiseedAnalysisError("运行配置身份或协议状态不一致")
    storage = _mapping(config.get("storage"), "运行配置 storage")
    if storage.get("seed_execution") != "serial":
        raise R2DistilBertMultiseedAnalysisError("三种子执行合同必须为串行")
    training = _mapping(config.get("training"), "运行配置 training")
    if training.get("save_total_limit") != 1:
        raise R2DistilBertMultiseedAnalysisError("检查点保留上限必须为 1")
    evaluation = _mapping(config.get("evaluation"), "运行配置 evaluation")
    if evaluation.get("threshold") != THRESHOLD or evaluation.get(
        "calibration_bins"
    ) != CALIBRATION_BINS:
        raise R2DistilBertMultiseedAnalysisError("评价阈值或校准分箱数不一致")


def _load_variant(
    root: Path,
    seed: int,
    variant: str,
    consumed: dict[Path, dict[str, object]],
) -> VariantArtifacts:
    manifest_path = root / "artifact_manifest.json"
    _record_input_file(manifest_path, "组制品清单", consumed)
    manifest = _read_json(manifest_path, "组制品清单")
    if (
        manifest.get("schema_version") != ARTIFACT_SCHEMA
        or manifest.get("status") != "finished"
        or manifest.get("stage") != EXPECTED_STAGE
        or manifest.get("protocol_status") != EXPECTED_PROTOCOL_STATUS
        or manifest.get("seed") != seed
        or manifest.get("variant") != variant
        or manifest.get("selection_split") != EXPECTED_SELECTION_SPLIT
        or manifest.get("final_test_visible") is not False
    ):
        raise R2DistilBertMultiseedAnalysisError(f"组制品清单身份不一致：{root}")
    _validate_artifact_manifest(root, manifest, consumed)
    metrics_path = root / "metrics" / "validation_metrics.json"
    predictions_path = root / "predictions" / "validation_predictions.jsonl"
    run_binding_path = root / "run_binding.json"
    input_binding_path = root / "input_binding.json"
    model_binding_path = root / "model_binding.json"
    summary_path = root / "summary.json"
    state_path = root / "run_state.json"
    finalization_path = root / "finalization_receipt.json"
    best_model_receipt_path = root / "best_model_receipt.json"
    _record_input_file(state_path, "最终运行状态", consumed)
    metrics_raw = _read_json(metrics_path, "开发验证指标")
    predictions = _read_jsonl(predictions_path, "开发验证预测")
    run_binding = _read_json(run_binding_path, "运行绑定")
    input_binding = _read_json(input_binding_path, "输入绑定")
    model_binding = _read_json(model_binding_path, "模型绑定")
    summary = _read_json(summary_path, "组汇总")
    state = _read_json(state_path, "运行状态")
    finalization = _read_json(finalization_path, "收尾收据")
    best_model_receipt = _read_json(best_model_receipt_path, "最佳模型收据")
    _validate_input_binding(input_binding, seed, variant)
    _validate_run_binding(run_binding, input_binding, model_binding, seed, variant)
    binding_sha256 = _canonical_sha256(run_binding)
    if manifest.get("binding_sha256") != binding_sha256:
        raise R2DistilBertMultiseedAnalysisError(f"组清单与运行绑定不一致：{root}")
    if (
        state.get("schema_version") != "flow_probe_r2_distilbert_sidecar_run_state_v1"
        or manifest.get("run_id") != state.get("run_id")
        or state.get("status") != "finished"
        or state.get("binding_sha256") != binding_sha256
        or state.get("latest_checkpoint") is not None
        or state.get("failure") is not None
    ):
        raise R2DistilBertMultiseedAnalysisError(f"完成组运行状态非法：{root}")
    selected_directories = [
        path
        for path in (root / "model-selection").iterdir()
        if path.is_dir() and not path.is_symlink()
    ]
    if len(selected_directories) != 1:
        raise R2DistilBertMultiseedAnalysisError(f"完成组最佳模型数量不为一：{root}")
    selected_relative = selected_directories[0].relative_to(root).as_posix()
    if (
        finalization.get("schema_version")
        != "flow_probe_r2_distilbert_sidecar_finalization_v1"
        or finalization.get("status") != "finalizing"
        or finalization.get("binding_sha256") != binding_sha256
        or finalization.get("run_id") != state.get("run_id")
        or finalization.get("best_model") != selected_relative
        or finalization.get("parameter_contract") != manifest.get("parameter_contract")
    ):
        raise R2DistilBertMultiseedAnalysisError(f"收尾收据与完成组不一致：{root}")
    if (
        best_model_receipt.get("schema_version")
        != "flow_probe_r2_distilbert_best_model_receipt_v1"
        or best_model_receipt.get("binding_sha256") != binding_sha256
        or best_model_receipt.get("best_model") != selected_relative
    ):
        raise R2DistilBertMultiseedAnalysisError(f"最佳模型收据与完成组不一致：{root}")
    selection_manifest_path = selected_directories[0] / "selection_manifest.json"
    if _sha256_file(selection_manifest_path) != best_model_receipt.get(
        "selection_manifest_sha256"
    ):
        raise R2DistilBertMultiseedAnalysisError(f"最佳模型选模清单摘要不一致：{root}")
    if (
        summary.get("schema_version")
        != "flow_probe_r2_distilbert_sidecar_variant_summary_v1"
        or summary.get("stage") != EXPECTED_STAGE
        or summary.get("status") != EXPECTED_PROTOCOL_STATUS
        or summary.get("seed") != seed
        or summary.get("variant") != variant
        or summary.get("final_test_visible") is not False
    ):
        raise R2DistilBertMultiseedAnalysisError(f"组汇总身份不一致：{root}")
    summary_counts = _mapping(summary.get("sample_counts"), "组汇总 sample_counts")
    if summary_counts != {"train-fit": 2048, "validation": 512}:
        raise R2DistilBertMultiseedAnalysisError(f"组汇总样本数不一致：{root}")
    training = _mapping(summary.get("training"), "组训练汇总")
    if (
        training.get("global_step") != EXPECTED_OPTIMIZER_STEPS
        or training.get("total_optimizer_steps") != EXPECTED_OPTIMIZER_STEPS
    ):
        raise R2DistilBertMultiseedAnalysisError(f"组训练没有完成固定步数：{root}")
    if summary.get("parameter_contract") != manifest.get("parameter_contract"):
        raise R2DistilBertMultiseedAnalysisError(f"组汇总参数合同不一致：{root}")
    computed = _validate_predictions(
        predictions,
        _split_binding(input_binding, variant, "validation"),
        f"种子 {seed} {variant}",
    )
    summary_metrics = _mapping(summary.get("validation_metrics"), "组汇总验证指标")
    for metric in ("sample_count", *METRICS, "true_positive", "true_negative", "false_positive", "false_negative"):
        actual = _number(metrics_raw.get(metric), f"开发验证指标 {metric}")
        from_summary = _number(summary_metrics.get(metric), f"组汇总指标 {metric}")
        recalculated = float(computed[metric])
        if not math.isclose(actual, recalculated, rel_tol=1e-10, abs_tol=1e-12):
            raise R2DistilBertMultiseedAnalysisError(
                f"种子 {seed} {variant} 的 {metric} 与预测重算不一致"
            )
        if not math.isclose(from_summary, actual, rel_tol=1e-12, abs_tol=1e-12):
            raise R2DistilBertMultiseedAnalysisError(
                f"种子 {seed} {variant} 的 {metric} 在指标与汇总间不一致"
            )
    return VariantArtifacts(
        seed=seed,
        variant=variant,
        root=root,
        metrics_path=metrics_path,
        predictions_path=predictions_path,
        artifact_manifest_path=manifest_path,
        run_binding_path=run_binding_path,
        input_binding_path=input_binding_path,
        metrics={metric: computed[metric] for metric in ("sample_count", *METRICS)},
        predictions=predictions,
        artifact_manifest=manifest,
        run_binding=run_binding,
        input_binding=input_binding,
    )


def _validate_seed_summary(
    seed_root: Path,
    seed: int,
    artifacts: Mapping[str, VariantArtifacts],
    consumed: dict[Path, dict[str, object]],
) -> None:
    path = seed_root / "seed_summary.json"
    _record_input_file(path, "种子汇总", consumed)
    summary = _read_json(path, "种子汇总")
    if (
        summary.get("schema_version")
        != "flow_probe_r2_distilbert_sidecar_seed_summary_v1"
        or summary.get("stage") != EXPECTED_STAGE
        or summary.get("status") != EXPECTED_PROTOCOL_STATUS
        or summary.get("seed") != seed
        or summary.get("variant_order") != list(VARIANTS)
        or summary.get("same_model_structure") is not True
        or summary.get("same_optimizer") is not True
        or summary.get("same_samples_and_budget") is not True
        or summary.get("final_test_visible") is not False
    ):
        raise R2DistilBertMultiseedAnalysisError(f"种子 {seed} 汇总合同不一致")
    variants = _mapping(summary.get("variants"), "种子汇总 variants")
    if set(variants) != set(VARIANTS):
        raise R2DistilBertMultiseedAnalysisError(f"种子 {seed} 汇总缺少冻结组")
    if summary.get("parameter_contract") != artifacts["T-A"].artifact_manifest.get(
        "parameter_contract"
    ):
        raise R2DistilBertMultiseedAnalysisError(f"种子 {seed} 汇总参数合同不一致")
    for variant in VARIANTS:
        values = _mapping(variants[variant], f"种子汇总 {variant}")
        metrics = _mapping(values.get("validation_metrics"), f"种子汇总 {variant} 指标")
        for metric in METRICS:
            if not math.isclose(
                _number(metrics.get(metric), f"种子汇总 {variant}.{metric}"),
                float(artifacts[variant].metrics[metric]),
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise R2DistilBertMultiseedAnalysisError(
                    f"种子 {seed} 汇总中的 {variant}.{metric} 不一致"
                )


def _load_all(
    run_root: Path,
) -> tuple[dict[int, dict[str, VariantArtifacts]], dict[Path, dict[str, object]]]:
    if run_root.is_symlink() or not run_root.is_dir():
        raise R2DistilBertMultiseedAnalysisError(f"运行根目录不存在或为符号链接：{run_root}")
    expected_seed_names = {f"seed-{seed}" for seed in SEEDS}
    actual_seed_names = {
        path.name for path in run_root.iterdir() if path.name.startswith("seed-")
    }
    if actual_seed_names != expected_seed_names:
        raise R2DistilBertMultiseedAnalysisError(
            f"运行根必须精确包含种子 42/43/44：实际={sorted(actual_seed_names)}"
        )
    consumed: dict[Path, dict[str, object]] = {}
    loaded: dict[int, dict[str, VariantArtifacts]] = {}
    expected_variant_names = set(VARIANT_SLUGS.values())
    for seed in SEEDS:
        seed_root = run_root / f"seed-{seed}"
        if seed_root.is_symlink() or not seed_root.is_dir():
            raise R2DistilBertMultiseedAnalysisError(f"种子目录非法：{seed_root}")
        actual_variant_names = {
            path.name for path in seed_root.iterdir() if path.name.startswith("t-")
        }
        if actual_variant_names != expected_variant_names:
            raise R2DistilBertMultiseedAnalysisError(
                f"种子 {seed} 必须精确包含四个冻结组：实际={sorted(actual_variant_names)}"
            )
        loaded[seed] = {
            variant: _load_variant(seed_root / VARIANT_SLUGS[variant], seed, variant, consumed)
            for variant in VARIANTS
        }
        _validate_seed_summary(seed_root, seed, loaded[seed], consumed)
    return loaded, consumed


def _common_split_signature(
    artifact: VariantArtifacts, variant: str, split: str
) -> tuple[object, ...]:
    binding = _split_binding(artifact.input_binding, variant, split)
    return tuple(
        binding.get(field)
        for field in ("sample_count", "sample_order_sha256", "text_sha256", "label_sha256")
    )


def _validate_cross_run_consistency(
    loaded: Mapping[int, Mapping[str, VariantArtifacts]],
) -> dict[str, object]:
    first = loaded[SEEDS[0]][VARIANTS[0]]
    reference_rows = tuple(
        (row["sample_id"], row["stable_order"], row["label"])
        for row in first.predictions
    )
    reference_code = (
        first.run_binding["implementation_sha256"],
        first.run_binding["semantic_dependency_sha256"],
    )
    reference_model = first.run_binding["model_binding_sha256"]
    reference_structure = first.run_binding["model_structure"]
    reference_optimizer = first.run_binding["optimizer"]
    reference_budget = first.run_binding["training_budget"]
    reference_parameter_contract = first.artifact_manifest["parameter_contract"]
    reference_common = {
        split: _common_split_signature(first, "T-A", split)
        for split in ("train-fit", "validation")
    }
    per_seed_input_sha256: dict[str, str] = {}
    t_a_sidecar: dict[str, set[object]] = {"train-fit": set(), "validation": set()}
    t_p_sidecar: dict[str, set[object]] = {"train-fit": set(), "validation": set()}
    for seed in SEEDS:
        seed_bindings = {_canonical_sha256(item.input_binding) for item in loaded[seed].values()}
        if len(seed_bindings) != 1:
            raise R2DistilBertMultiseedAnalysisError(f"种子 {seed} 四组输入绑定不一致")
        per_seed_input_sha256[str(seed)] = next(iter(seed_bindings))
        for variant in VARIANTS:
            artifact = loaded[seed][variant]
            rows = tuple(
                (row["sample_id"], row["stable_order"], row["label"])
                for row in artifact.predictions
            )
            if rows != reference_rows:
                raise R2DistilBertMultiseedAnalysisError(
                    f"种子 {seed} {variant} 的预测样本顺序或标签不一致"
                )
            current_code = (
                artifact.run_binding["implementation_sha256"],
                artifact.run_binding["semantic_dependency_sha256"],
            )
            if current_code != reference_code:
                raise R2DistilBertMultiseedAnalysisError("十二组实现或语义依赖摘要不一致")
            if artifact.run_binding["model_binding_sha256"] != reference_model:
                raise R2DistilBertMultiseedAnalysisError("十二组模型绑定摘要不一致")
            if (
                artifact.run_binding["model_structure"] != reference_structure
                or artifact.run_binding["optimizer"] != reference_optimizer
                or artifact.run_binding["training_budget"] != reference_budget
                or artifact.artifact_manifest["parameter_contract"]
                != reference_parameter_contract
            ):
                raise R2DistilBertMultiseedAnalysisError(
                    "十二组模型结构、参数、优化器或训练预算不一致"
                )
            for bound_variant in VARIANTS:
                for split in ("train-fit", "validation"):
                    if _common_split_signature(artifact, bound_variant, split) != reference_common[
                        split
                    ]:
                        raise R2DistilBertMultiseedAnalysisError(
                            "十二组训练/验证样本、文本或标签摘要不一致"
                        )
            for split in ("train-fit", "validation"):
                if variant == "T-A":
                    t_a_sidecar[split].add(
                        _split_binding(artifact.input_binding, variant, split).get(
                            "sidecar_sha256"
                        )
                    )
                if variant == "T-P":
                    t_p_sidecar[split].add(
                        _split_binding(artifact.input_binding, variant, split).get(
                            "sidecar_sha256"
                        )
                    )
    if any(len(values) != 1 for values in (*t_a_sidecar.values(), *t_p_sidecar.values())):
        raise R2DistilBertMultiseedAnalysisError("T-A 或 T-P 的固定旁路摘要在种子间漂移")
    module_root = Path(__file__).resolve().parent
    implementation_path = module_root / "r2_distilbert_sidecar_probe.py"
    if _sha256_file(implementation_path) != reference_code[0]:
        raise R2DistilBertMultiseedAnalysisError("运行绑定的探针实现摘要与当前分析环境不一致")
    for filename, expected_digest in _mapping(reference_code[1], "语义依赖摘要").items():
        if _sha256_file(module_root / str(filename)) != expected_digest:
            raise R2DistilBertMultiseedAnalysisError(
                f"运行绑定的语义依赖摘要与当前分析环境不一致：{filename}"
            )
    return {
        "three_seeds_exact": True,
        "four_variants_per_seed_exact": True,
        "sample_order_labels_identical": True,
        "common_text_digest_identical": True,
        "frozen_input_artifact_digests": dict(EXPECTED_INPUT_DIGESTS),
        "per_seed_input_binding_sha256": per_seed_input_sha256,
        "implementation_sha256": reference_code[0],
        "semantic_dependency_sha256": reference_code[1],
        "current_code_files_match_run_binding": True,
        "model_binding_sha256": reference_model,
        "same_model_structure_parameters_optimizer_budget": True,
        "final_test_visible": False,
        "seed_selection_performed": False,
    }


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _comparison_seed(base_seed: int, seed: int, comparison: str) -> int:
    payload = f"{base_seed}:{seed}:{comparison}".encode("ascii")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _bootstrap_comparison(
    physical_rows: Sequence[Mapping[str, object]],
    comparator_rows: Sequence[Mapping[str, object]],
    *,
    repetitions: int,
    seed: int,
) -> dict[str, object]:
    physical_signature = tuple(
        (row["sample_id"], row["stable_order"], row["label"]) for row in physical_rows
    )
    comparator_signature = tuple(
        (row["sample_id"], row["stable_order"], row["label"])
        for row in comparator_rows
    )
    if physical_signature != comparator_signature:
        raise R2DistilBertMultiseedAnalysisError("配对自助法输入的样本顺序或标签不一致")
    strata: dict[int, list[int]] = defaultdict(list)
    for index, row in enumerate(physical_rows):
        strata[int(row["label"])].append(index)
    if set(strata) != {0, 1}:
        raise R2DistilBertMultiseedAnalysisError("配对自助法要求良性和恶意两类样本")
    point_physical = _compute_metrics(physical_rows)
    point_comparator = _compute_metrics(comparator_rows)
    distributions: dict[str, list[float]] = {metric: [] for metric in METRICS}
    rng = random.Random(seed)
    for _ in range(repetitions):
        indices: list[int] = []
        for label in sorted(strata):
            pool = strata[label]
            indices.extend(rng.choice(pool) for _ in pool)
        sampled_physical = [physical_rows[index] for index in indices]
        sampled_comparator = [comparator_rows[index] for index in indices]
        physical_metrics = _compute_metrics(sampled_physical)
        comparator_metrics = _compute_metrics(sampled_comparator)
        for metric in METRICS:
            distributions[metric].append(
                float(physical_metrics[metric]) - float(comparator_metrics[metric])
            )
    metrics: dict[str, object] = {}
    for metric in METRICS:
        point_delta = float(point_physical[metric]) - float(point_comparator[metric])
        lower = _quantile(distributions[metric], 0.025)
        upper = _quantile(distributions[metric], 0.975)
        higher_is_better = metric == "macro_f1"
        metrics[metric] = {
            "point_delta": point_delta,
            "ci95": [lower, upper],
            "bootstrap_mean_delta": statistics.fmean(distributions[metric]),
            "beneficial_direction": "positive" if higher_is_better else "negative",
            "point_beneficial": point_delta > 0.0 if higher_is_better else point_delta < 0.0,
            "ci95_supports_benefit": lower > 0.0 if higher_is_better else upper < 0.0,
        }
    return {
        "sampling": "paired_stratified_by_binary_label",
        "repetitions": repetitions,
        "seed": seed,
        "metrics": metrics,
    }


def _build_results(
    loaded: Mapping[int, Mapping[str, VariantArtifacts]],
    *,
    repetitions: int,
    bootstrap_seed: int,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    per_seed: dict[str, object] = {}
    for seed in SEEDS:
        variants = {
            variant: {metric: float(loaded[seed][variant].metrics[metric]) for metric in METRICS}
            for variant in VARIANTS
        }
        comparisons: dict[str, object] = {}
        for comparator in COMPARATORS:
            name = COMPARISON_NAMES[comparator]
            comparisons[name] = _bootstrap_comparison(
                loaded[seed]["T-P"].predictions,
                loaded[seed][comparator].predictions,
                repetitions=repetitions,
                seed=_comparison_seed(bootstrap_seed, seed, name),
            )
        per_seed[str(seed)] = {"variants": variants, "comparisons": comparisons}

    aggregate_variants: dict[str, object] = {}
    for variant in VARIANTS:
        aggregate_variants[variant] = {}
        for metric in METRICS:
            values = [
                float(_mapping(per_seed[str(seed)], "种子结果")["variants"][variant][metric])
                for seed in SEEDS
            ]
            aggregate_variants[variant][metric] = {
                "mean": statistics.fmean(values),
                "sample_standard_deviation": statistics.stdev(values),
                "values_by_seed": {str(seed): value for seed, value in zip(SEEDS, values, strict=True)},
            }
    aggregate_deltas: dict[str, object] = {}
    for comparison in COMPARISON_NAMES.values():
        aggregate_deltas[comparison] = {}
        for metric in METRICS:
            values = [
                float(
                    _mapping(
                        _mapping(per_seed[str(seed)], "种子结果")["comparisons"][comparison],
                        "种子比较",
                    )["metrics"][metric]["point_delta"]
                )
                for seed in SEEDS
            ]
            aggregate_deltas[comparison][metric] = {
                "mean": statistics.fmean(values),
                "sample_standard_deviation": statistics.stdev(values),
                "values_by_seed": {str(seed): value for seed, value in zip(SEEDS, values, strict=True)},
            }
    aggregate = {
        "standard_deviation_definition": "sample_standard_deviation_ddof_1",
        "variants": aggregate_variants,
        "deltas": aggregate_deltas,
    }

    failure_reasons: list[str] = []
    statistical_warnings: list[str] = []
    calibration_diagnostics: list[str] = []
    per_seed_decisions: dict[str, object] = {}
    for seed in SEEDS:
        seed_values = _mapping(per_seed[str(seed)], "种子结果")
        comparisons = _mapping(seed_values["comparisons"], "种子比较")
        point_checks: dict[str, bool] = {}
        ci_checks: dict[str, bool] = {}
        for comparison in COMPARISON_NAMES.values():
            metrics = _mapping(_mapping(comparisons[comparison], "比较结果")["metrics"], "比较指标")
            macro = _mapping(metrics["macro_f1"], "宏平均 F1 差值")
            point_checks[comparison] = bool(macro["point_beneficial"])
            ci_checks[comparison] = bool(macro["ci95_supports_benefit"])
            if not point_checks[comparison]:
                failure_reasons.append(
                    f"种子 {seed} 的 {comparison} 宏平均 F1 差值不为正："
                    f"{float(macro['point_delta']):.12f}"
                )
            if not ci_checks[comparison]:
                ci = list(macro["ci95"])
                statistical_warnings.append(
                    f"种子 {seed} 的 {comparison} 宏平均 F1 配对 95% 置信区间未完全高于 0："
                    f"[{float(ci[0]):.12f}, {float(ci[1]):.12f}]"
                )
            for metric in METRICS[1:]:
                diagnostic = _mapping(metrics[metric], f"{comparison}.{metric}")
                if not bool(diagnostic["point_beneficial"]):
                    calibration_diagnostics.append(
                        f"种子 {seed} 的 {comparison} 在 {metric} 上未改善："
                        f"P-对照={float(diagnostic['point_delta']):.12f}"
                    )
        per_seed_decisions[str(seed)] = {
            "t_p_macro_f1_strictly_exceeds_a_s_r": all(point_checks.values()),
            "paired_ci95_all_above_zero": all(ci_checks.values()),
            "point_checks": point_checks,
            "ci95_checks": ci_checks,
        }
    primary_pass = all(
        bool(_mapping(per_seed_decisions[str(seed)], "种子裁决")["t_p_macro_f1_strictly_exceeds_a_s_r"])
        for seed in SEEDS
    )
    all_ci_support = all(
        bool(_mapping(per_seed_decisions[str(seed)], "种子裁决")["paired_ci95_all_above_zero"])
        for seed in SEEDS
    )
    decision = {
        "contract": "T-P 在种子 42/43/44 上逐一严格超过 T-A、T-S、T-R 的宏平均 F1",
        "outcome": "GO_TO_QWEN" if primary_pass else "NO_GO",
        "primary_contract_pass": primary_pass,
        "paired_ci95_support_all_comparisons": all_ci_support,
        "evidence_strength": (
            "point_superiority_with_paired_ci95_support"
            if primary_pass and all_ci_support
            else "point_superiority_without_full_ci95_support"
            if primary_pass
            else "primary_contract_failed"
        ),
        "per_seed": per_seed_decisions,
        "failure_reasons": failure_reasons,
        "statistical_warnings": statistical_warnings,
        "calibration_diagnostics": calibration_diagnostics,
        "best_seed_selected": False,
        "final_test_read": False,
    }
    return per_seed, aggregate, decision


def _physical_metric_gate() -> dict[str, object]:
    return {
        "status": "not_evaluable_on_current_public_tqhc2_development_validation",
        "blocking_for_distilbert_probe_decision": False,
        "formal_r2_thresholds": {
            "unobserved_state_mse_relative_improvement_minimum": 0.10,
            "physics_residual_mse_relative_improvement_minimum": 0.10,
            "required_for_each_seed": True,
        },
        "available_background_binding": {
            "input_summary_sha256": EXPECTED_INPUT_DIGESTS["input_summary"],
            "sidecar_sha256": EXPECTED_INPUT_DIGESTS["sidecar"],
            "role": "旁路就绪背景，不计入 T-P 相对 T-A 的增益",
        },
        "reason": (
            "当前公开 TQH-C2 开发验证没有隐藏队列真值，T-A 也没有对应状态头；"
            "因此本探针不能计算状态误差或物理残差相对改善，不得用 ns-3 状态估计器"
            "就绪指标替代组间物理增益。"
        ),
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    per_seed: Mapping[str, object],
    aggregate: Mapping[str, object],
) -> None:
    fieldnames = (
        "record_type",
        "seed",
        "variant",
        "comparison",
        "metric",
        "value",
        "mean",
        "sample_standard_deviation",
        "ci95_lower",
        "ci95_upper",
        "beneficial_direction",
        "point_beneficial",
        "ci95_supports_benefit",
    )
    rows: list[dict[str, object]] = []
    for seed in SEEDS:
        seed_values = _mapping(per_seed[str(seed)], "种子结果")
        variants = _mapping(seed_values["variants"], "种子组指标")
        for variant in VARIANTS:
            metrics = _mapping(variants[variant], "组指标")
            for metric in METRICS:
                rows.append(
                    {
                        "record_type": "seed_variant_metric",
                        "seed": seed,
                        "variant": variant,
                        "comparison": "",
                        "metric": metric,
                        "value": metrics[metric],
                    }
                )
        comparisons = _mapping(seed_values["comparisons"], "种子比较")
        for comparison in COMPARISON_NAMES.values():
            metrics = _mapping(_mapping(comparisons[comparison], "比较结果")["metrics"], "比较指标")
            for metric in METRICS:
                values = _mapping(metrics[metric], "差值指标")
                ci = list(values["ci95"])
                rows.append(
                    {
                        "record_type": "seed_paired_delta",
                        "seed": seed,
                        "variant": "T-P",
                        "comparison": comparison,
                        "metric": metric,
                        "value": values["point_delta"],
                        "ci95_lower": ci[0],
                        "ci95_upper": ci[1],
                        "beneficial_direction": values["beneficial_direction"],
                        "point_beneficial": values["point_beneficial"],
                        "ci95_supports_benefit": values["ci95_supports_benefit"],
                    }
                )
    aggregate_variants = _mapping(aggregate["variants"], "聚合组指标")
    for variant in VARIANTS:
        metrics = _mapping(aggregate_variants[variant], "聚合组指标")
        for metric in METRICS:
            values = _mapping(metrics[metric], "聚合指标")
            rows.append(
                {
                    "record_type": "aggregate_variant_metric",
                    "seed": "42/43/44",
                    "variant": variant,
                    "comparison": "",
                    "metric": metric,
                    "mean": values["mean"],
                    "sample_standard_deviation": values["sample_standard_deviation"],
                }
            )
    aggregate_deltas = _mapping(aggregate["deltas"], "聚合差值")
    for comparison in COMPARISON_NAMES.values():
        metrics = _mapping(aggregate_deltas[comparison], "聚合比较")
        for metric in METRICS:
            values = _mapping(metrics[metric], "聚合差值指标")
            rows.append(
                {
                    "record_type": "aggregate_delta",
                    "seed": "42/43/44",
                    "variant": "T-P",
                    "comparison": comparison,
                    "metric": metric,
                    "mean": values["mean"],
                    "sample_standard_deviation": values["sample_standard_deviation"],
                }
            )
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _render_markdown(
    per_seed: Mapping[str, object],
    aggregate: Mapping[str, object],
    decision: Mapping[str, object],
    physical_gate: Mapping[str, object],
) -> str:
    lines = [
        "# R2 DistilBERT 物理旁路三种子汇总",
        "",
        "## 裁决",
        "",
        f"- 自动裁决：`{decision['outcome']}`。",
        f"- 三种子逐一严格超过三类对照：`{str(decision['primary_contract_pass']).lower()}`。",
        f"- 全部宏平均 F1 配对置信区间支持正差值：`{str(decision['paired_ci95_support_all_comparisons']).lower()}`。",
        "- 未选择最好种子，未读取最终测试。",
        "",
        "## 逐种子指标",
        "",
        "| 种子 | 组别 | 宏平均 F1 | 良性误报率 | Brier 分数 | 期望校准误差 |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for seed in SEEDS:
        variants = _mapping(_mapping(per_seed[str(seed)], "种子结果")["variants"], "组指标")
        for variant in VARIANTS:
            metrics = _mapping(variants[variant], "组指标")
            lines.append(
                f"| {seed} | {variant} | {float(metrics['macro_f1']):.6f} | "
                f"{float(metrics['benign_false_positive_rate']):.6f} | "
                f"{float(metrics['brier_score']):.6f} | "
                f"{float(metrics['expected_calibration_error']):.6f} |"
            )
    lines.extend(
        [
            "",
            "## P 与对照的配对差值",
            "",
            "差值统一为 `T-P - 对照`；宏平均 F1 越大越好，其余三项越小越好。",
            "",
            "| 种子 | 比较 | 指标 | 点差值 | 配对 95% 置信区间 |",
            "| ---: | --- | --- | ---: | --- |",
        ]
    )
    for seed in SEEDS:
        comparisons = _mapping(
            _mapping(per_seed[str(seed)], "种子结果")["comparisons"], "种子比较"
        )
        for comparison in COMPARISON_NAMES.values():
            metrics = _mapping(_mapping(comparisons[comparison], "比较结果")["metrics"], "比较指标")
            for metric in METRICS:
                values = _mapping(metrics[metric], "差值指标")
                ci = list(values["ci95"])
                lines.append(
                    f"| {seed} | {comparison} | {metric} | "
                    f"{float(values['point_delta']):.6f} | "
                    f"[{float(ci[0]):.6f}, {float(ci[1]):.6f}] |"
                )
    lines.extend(
        [
            "",
            "## 三种子均值与标准差",
            "",
            "标准差为样本标准差，分母使用 `n-1`。",
            "",
            "| 组别 | 指标 | 均值 | 标准差 |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    aggregate_variants = _mapping(aggregate["variants"], "聚合组指标")
    for variant in VARIANTS:
        metrics = _mapping(aggregate_variants[variant], "聚合组指标")
        for metric in METRICS:
            values = _mapping(metrics[metric], "聚合指标")
            lines.append(
                f"| {variant} | {metric} | {float(values['mean']):.6f} | "
                f"{float(values['sample_standard_deviation']):.6f} |"
            )
    lines.extend(
        [
            "",
            "| 比较 | 指标 | 差值均值 | 差值标准差 |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    aggregate_deltas = _mapping(aggregate["deltas"], "聚合差值")
    for comparison in COMPARISON_NAMES.values():
        metrics = _mapping(aggregate_deltas[comparison], "聚合比较")
        for metric in METRICS:
            values = _mapping(metrics[metric], "聚合差值指标")
            lines.append(
                f"| {comparison} | {metric} | {float(values['mean']):.6f} | "
                f"{float(values['sample_standard_deviation']):.6f} |"
            )
    lines.extend(
        [
            "",
            "## 物理指标边界",
            "",
            f"- 状态：`{physical_gate['status']}`。",
            f"- 原因：{physical_gate['reason']}",
            "- 正式 R2 仍要求每个种子的未观测状态误差和物理残差相对同分区基线均改善至少 `10%`。",
            "",
            "## 失败与警告",
            "",
        ]
    )
    failures = list(decision["failure_reasons"])
    warnings = list(decision["statistical_warnings"])
    diagnostics = list(decision["calibration_diagnostics"])
    if not failures and not warnings and not diagnostics:
        lines.append("- 无。")
    else:
        lines.extend(f"- 主裁决失败：{reason}" for reason in failures)
        lines.extend(f"- 统计警告：{reason}" for reason in warnings)
        lines.extend(f"- 校准诊断：{reason}" for reason in diagnostics)
    return "\n".join(lines) + "\n"


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="汇总 R2 DistilBERT 物理旁路探针的三种子开发集结果"
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-repetitions", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260803)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.bootstrap_repetitions <= 0:
            raise R2DistilBertMultiseedAnalysisError("配对自助法重复次数必须为正整数")
        result = analyze(
            run_root=args.run_root,
            output=args.output,
            bootstrap_repetitions=args.bootstrap_repetitions,
            bootstrap_seed=args.bootstrap_seed,
        )
        print(json.dumps(result["decision"], ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except R2DistilBertMultiseedAnalysisError as error:
        print(
            json.dumps(
                {"status": "failed", "reason": str(error)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


def analyze(
    *,
    run_root: Path,
    output: Path,
    bootstrap_repetitions: int,
    bootstrap_seed: int,
) -> dict[str, object]:
    """严格核验十二组开发集制品并生成确定性汇总。"""
    if bootstrap_repetitions <= 0:
        raise R2DistilBertMultiseedAnalysisError("配对自助法重复次数必须为正整数")
    if run_root.is_symlink():
        raise R2DistilBertMultiseedAnalysisError(f"运行根目录不得为符号链接：{run_root}")
    if output.exists() or output.is_symlink():
        raise R2DistilBertMultiseedAnalysisError(f"输出路径已存在，拒绝覆盖：{output}")
    run_root = run_root.resolve()
    output = output.resolve()
    loaded, consumed = _load_all(run_root)
    integrity = _validate_cross_run_consistency(loaded)
    per_seed, aggregate, decision = _build_results(
        loaded,
        repetitions=bootstrap_repetitions,
        bootstrap_seed=bootstrap_seed,
    )
    physical_gate = _physical_metric_gate()
    analysis_config = {
        "schema_version": "flow_probe_r2_distilbert_multiseed_analysis_config_v1",
        "run_root": str(run_root),
        "output": str(output),
        "seeds": list(SEEDS),
        "variants": list(VARIANTS),
        "comparisons": list(COMPARISON_NAMES.values()),
        "metrics": list(METRICS),
        "bootstrap_repetitions": bootstrap_repetitions,
        "bootstrap_seed": bootstrap_seed,
        "bootstrap_sampling": "paired_stratified_by_binary_label",
        "final_test_visible": False,
        "swanlab_registration_performed": False,
    }
    input_manifest = {
        "schema_version": "flow_probe_r2_distilbert_multiseed_analysis_inputs_v1",
        "run_root": str(run_root),
        "files": {
            str(path): record for path, record in sorted(consumed.items(), key=lambda item: str(item[0]))
        },
        "analysis_implementation_sha256": _sha256_file(Path(__file__)),
        "integrity": integrity,
    }
    summary = {
        "schema_version": "flow_probe_r2_distilbert_multiseed_analysis_v1",
        "stage": EXPECTED_STAGE,
        "protocol_status": EXPECTED_PROTOCOL_STATUS,
        "status": "finished",
        "scope": "frozen_tqhc2_development_validation_only",
        "protocol": {
            "seeds": list(SEEDS),
            "variants": list(VARIANTS),
            "comparisons": list(COMPARISON_NAMES.values()),
            "metrics": list(METRICS),
            "delta_direction": "T-P_minus_comparator",
            "bootstrap_repetitions": bootstrap_repetitions,
            "bootstrap_seed": bootstrap_seed,
            "bootstrap_sampling": "paired_stratified_by_binary_label",
        },
        "integrity": integrity,
        "per_seed": per_seed,
        "aggregate": aggregate,
        "physical_metric_gate": physical_gate,
        "decision": decision,
        "final_test_visible": False,
        "best_seed_selected": False,
        "swanlab_registration_performed": False,
    }
    output.mkdir(parents=True)
    _write_json(output / "analysis_config.json", analysis_config)
    _write_json(output / "input_manifest.json", input_manifest)
    _write_json(output / "analysis_summary.json", summary)
    _write_csv(output / "metrics.csv", per_seed, aggregate)
    (output / "summary.md").write_text(
        _render_markdown(per_seed, aggregate, decision, physical_gate),
        encoding="utf-8",
    )
    artifact_paths = [
        output / "analysis_config.json",
        output / "input_manifest.json",
        output / "analysis_summary.json",
        output / "metrics.csv",
        output / "summary.md",
    ]
    artifact_manifest = {
        "schema_version": "flow_probe_r2_distilbert_multiseed_analysis_artifacts_v1",
        "status": "finished",
        "final_test_visible": False,
        "files": {
            path.name: {"sha256": _sha256_file(path), "size_bytes": path.stat().st_size}
            for path in artifact_paths
        },
    }
    _write_json(output / "artifact_manifest.json", artifact_manifest)
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
