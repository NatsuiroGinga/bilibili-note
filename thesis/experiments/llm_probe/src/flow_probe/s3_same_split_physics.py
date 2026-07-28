"""在固定 seed44 测试分区上评估冻结 S3 的物理状态与队列残差。"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path

import torch
import yaml

from flow_probe.bounded_physics_evaluation import (
    FIXED_PHYSICS_TEST_FILE,
    PHYSICS_TEST_BATCH_SIZE,
    PHYSICS_TEST_SAMPLES,
    STATE_SUPERVISION_MODE,
    _load_frozen_evaluation_model,
)
from flow_probe.bounded_physics_train import FIXED_BASE_MODEL_ID, FIXED_DETECTION_ADAPTER
from flow_probe.config import ProbeConfig
from flow_probe.hierarchical_evaluation import _file_sha256
from flow_probe.physics_train import (
    _load_jsonl,
    _state_mask_sha256,
    build_state_supervision_masks,
)
from flow_probe.representation_train import _evaluate_physics
from flow_probe.tracking import (
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)

SCHEMA_VERSION = "flow_probe_s3_same_split_physics_v1"
PHASE = "s3-same-split-physics"
MASK_SEEDS = (42, 43, 44)
EXPECTED_TEST_SHA256 = "6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94"
FIXED_S3_TRAINING_DIR = FIXED_DETECTION_ADAPTER.parent
FIXED_STATE_HEAD = FIXED_S3_TRAINING_DIR / "state_head.pt"
FIXED_OUTPUT_DIR = Path(
    "runs/bounded-physics-conditioning-evaluation/" "qwen3-1.7b-s3-same-split-physics-test-v1"
)
FIXED_RUN_NAME = "qwen3-1.7b-s3-same-split-physics-test-v1"


class S3SameSplitPhysicsError(ValueError):
    """S3 同分区评估协议或输入制品不满足固定要求。"""


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise S3SameSplitPhysicsError(f"配置缺少映射：{name}")
    return dict(value)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as target:
        for row in rows:
            target.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise S3SameSplitPhysicsError(f"JSON 根节点必须是映射：{path}")
    return dict(payload)


def _append_history(path: Path, step: int, metrics: Mapping[str, int | float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as target:
        target.write(json.dumps({"step": step, "metrics": dict(metrics)}, sort_keys=True) + "\n")


def load_fixed_configuration(
    raw: Mapping[str, object],
) -> tuple[ProbeConfig, TrackingSettings]:
    """解析并验证不允许调参的 S3 同分区评估配置。"""

    probe = ProbeConfig.from_mapping(_mapping(raw.get("probe"), "probe"))
    if (
        probe.model_id != FIXED_BASE_MODEL_ID
        or probe.seed != 42
        or probe.max_input_length != 512
        or probe.max_new_tokens != 16
    ):
        raise S3SameSplitPhysicsError("基座、随机种子或令牌上限偏离固定 S3 协议")

    evaluation = _mapping(raw.get("s3_same_split_evaluation"), "s3_same_split_evaluation")
    expected = {
        "training_dir": str(FIXED_S3_TRAINING_DIR),
        "detection_adapter_path": str(FIXED_DETECTION_ADAPTER),
        "state_head_path": str(FIXED_STATE_HEAD),
        "physics_test_file": str(FIXED_PHYSICS_TEST_FILE),
        "physics_test_sha256": EXPECTED_TEST_SHA256,
        "physics_test_samples": PHYSICS_TEST_SAMPLES,
        "physics_test_batch_size": PHYSICS_TEST_BATCH_SIZE,
        "state_supervision_mode": STATE_SUPERVISION_MODE,
        "state_mask_seeds": list(MASK_SEEDS),
        "output_dir": str(FIXED_OUTPUT_DIR),
        "calibration": "none",
        "parameter_tuning": "none",
    }
    if evaluation != expected:
        raise S3SameSplitPhysicsError("S3 同分区评估配置偏离固定协议")

    tracking = TrackingSettings.from_mapping(_mapping(raw.get("tracking"), "tracking"))
    if tracking.run_name != FIXED_RUN_NAME:
        raise S3SameSplitPhysicsError(f"SwanLab 运行名必须固定为 {FIXED_RUN_NAME}")
    return probe, tracking


def _normalized_metrics(metrics: Mapping[str, float]) -> dict[str, float]:
    return {
        "five_dimensional_reference_mse": float(metrics["state_mse"]),
        "observed_reference_mse": float(metrics["state_mse_observed"]),
        "unobserved_reference_mse": float(metrics["state_mse_unobserved"]),
        "queue_residual_reference_mse": float(metrics["physics_residual_mse"]),
    }


def _analysis_training_view(
    original: Mapping[str, object],
    physics_summary: Mapping[str, object],
) -> dict[str, object]:
    """保留 S3 训练元数据，只把物理比较键映射到固定测试分区。"""

    normalized = json.loads(json.dumps(dict(original), ensure_ascii=False))
    if not isinstance(normalized, dict):
        raise S3SameSplitPhysicsError("S3 训练摘要无法规范化")
    metrics = physics_summary.get("metrics")
    if not isinstance(metrics, Mapping):
        raise S3SameSplitPhysicsError("S3 物理摘要缺少 metrics")
    validation = normalized.get("validation")
    if not isinstance(validation, dict):
        raise S3SameSplitPhysicsError("S3 训练摘要缺少 validation")
    validation.update(
        {
            "state_mse": float(metrics["five_dimensional_reference_mse"]),
            "state_mse_observed": float(metrics["observed_reference_mse"]),
            "state_mse_unobserved": float(metrics["unobserved_reference_mse"]),
            "physics_residual_mse": float(metrics["queue_residual_reference_mse"]),
        }
    )
    normalized["analysis_compatibility"] = {
        "consumer": "flow_probe.s3_s4_detection_analysis.analyze",
        "mechanism_metric_source": "physics_test_summary.json",
        "key_mapping": {
            "state_mse_unobserved": "unobserved_reference_mse",
            "physics_residual_mse": "queue_residual_reference_mse",
        },
        "same_split_reference": True,
    }
    normalized["physics_test"] = json.loads(json.dumps(dict(physics_summary), ensure_ascii=False))
    return normalized


def run_s3_same_split_physics(
    probe: ProbeConfig,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
    config_path: Path,
) -> dict[str, object]:
    """单次加载冻结 S3，完成三种状态掩码的固定测试评估。"""

    if FIXED_OUTPUT_DIR.exists():
        raise S3SameSplitPhysicsError(f"输出目录已存在，拒绝复用：{FIXED_OUTPUT_DIR}")
    required_inputs = (
        config_path,
        FIXED_PHYSICS_TEST_FILE,
        FIXED_DETECTION_ADAPTER / "adapter_config.json",
        FIXED_DETECTION_ADAPTER / "adapter_model.safetensors",
        FIXED_STATE_HEAD,
        FIXED_S3_TRAINING_DIR / "training_summary.json",
    )
    missing = [str(path) for path in required_inputs if not path.is_file()]
    if missing:
        raise S3SameSplitPhysicsError("S3 同分区评估输入不完整：" + ", ".join(missing))
    test_sha256 = _file_sha256(FIXED_PHYSICS_TEST_FILE)
    if test_sha256 != EXPECTED_TEST_SHA256:
        raise S3SameSplitPhysicsError(f"固定 seed44 测试集哈希不一致：{test_sha256}")
    records = _load_jsonl(FIXED_PHYSICS_TEST_FILE)
    if len(records) != PHYSICS_TEST_SAMPLES:
        raise S3SameSplitPhysicsError(f"固定 seed44 测试集必须为 807 条，实际 {len(records)}")

    console_path = FIXED_OUTPUT_DIR / "console.log"
    config_snapshot_path = FIXED_OUTPUT_DIR / "config_snapshot.json"
    environment_path = FIXED_OUTPUT_DIR / "environment.json"
    input_manifest_path = FIXED_OUTPUT_DIR / "input_sha256.json"
    history_path = FIXED_OUTPUT_DIR / "metric_history.jsonl"
    metrics_path = FIXED_OUTPUT_DIR / "swanlab_metrics.json"
    combined_summary_path = FIXED_OUTPUT_DIR / "physics_test_summary.json"
    data_files: dict[str, Path] = {
        "config_snapshot": config_snapshot_path,
        "environment": environment_path,
        "input_manifest": input_manifest_path,
        "metric_history": history_path,
        "swanlab_metrics": metrics_path,
        "physics_test_summary": combined_summary_path,
    }
    for mask_seed in MASK_SEEDS:
        data_files[f"physics_summary_seed{mask_seed}"] = (
            FIXED_OUTPUT_DIR / f"mask-seed{mask_seed}" / "physics_test_summary.json"
        )
        data_files[f"physics_predictions_seed{mask_seed}"] = (
            FIXED_OUTPUT_DIR / f"mask-seed{mask_seed}" / "physics_predictions.jsonl"
        )
        data_files[f"analysis_training_seed{mask_seed}"] = (
            FIXED_OUTPUT_DIR
            / f"mask-seed{mask_seed}"
            / "analysis_training_view"
            / "training_summary.json"
        )

    fixed_config = {
        "schema_version": SCHEMA_VERSION,
        "probe": asdict(probe),
        "s3_same_split_evaluation": _mapping(
            raw_config.get("s3_same_split_evaluation"), "s3_same_split_evaluation"
        ),
        "tracking": asdict(tracking),
    }
    input_hashes_before = {str(path): _file_sha256(path) for path in required_inputs}
    immutable_model_files = (
        FIXED_DETECTION_ADAPTER / "adapter_model.safetensors",
        FIXED_STATE_HEAD,
    )
    immutable_hashes_before = {
        str(path): input_hashes_before[str(path)] for path in immutable_model_files
    }

    with (
        capture_console_log(console_path),
        swanlab_run(
            settings=tracking,
            phase=PHASE,
            config=fixed_config,
            artifact_dir=FIXED_OUTPUT_DIR,
            data_files=data_files,
        ) as swanlab,
    ):
        _write_json(config_snapshot_path, fixed_config)
        import transformers

        _write_json(
            environment_path,
            {
                "python": sys.version,
                "platform": platform.platform(),
                "torch": torch.__version__,
                "transformers": transformers.__version__,
                "cuda": torch.version.cuda,
                "gpu": torch.cuda.get_device_name(0),
            },
        )
        _write_json(
            input_manifest_path,
            {
                "schema_version": SCHEMA_VERSION,
                "files": input_hashes_before,
                "physics_test_records": len(records),
                "physics_test_split_seed": 44,
                "state_mask_seeds": list(MASK_SEEDS),
            },
        )

        torch.manual_seed(probe.seed)
        torch.cuda.manual_seed_all(probe.seed)
        tokenizer, model, state_head = _load_frozen_evaluation_model(
            probe,
            FIXED_DETECTION_ADAPTER,
        )
        try:
            device = next(model.parameters()).device
        except StopIteration as error:
            raise S3SameSplitPhysicsError("冻结 S3 模型没有可定位设备的参数") from error
        state_head = state_head.to(device=device, dtype=torch.bfloat16)
        state_head.eval()
        model.eval()
        if any(parameter.requires_grad for parameter in model.parameters()):
            raise S3SameSplitPhysicsError("只读评估发现 S3 模型仍有可训练参数")
        for parameter in state_head.parameters():
            parameter.requires_grad_(False)

        original_training_summary = _read_json(FIXED_S3_TRAINING_DIR / "training_summary.json")
        summaries: dict[str, object] = {}
        final_tracking_metrics: dict[str, int | float] = {}
        for step, mask_seed in enumerate(MASK_SEEDS, start=1):
            print(f"S3 同分区物理评估开始：state_mask_seed={mask_seed}", flush=True)
            state_masks = build_state_supervision_masks(
                records,
                STATE_SUPERVISION_MODE,
                mask_seed,
            )
            torch.cuda.reset_peak_memory_stats()
            started = time.perf_counter()
            raw_metrics, predictions = _evaluate_physics(
                model,
                state_head,
                tokenizer,
                records,
                state_masks=state_masks,
                batch_size=PHYSICS_TEST_BATCH_SIZE,
                max_length=probe.max_input_length,
                device=device,
            )
            runtime_seconds = time.perf_counter() - started
            metrics = _normalized_metrics(raw_metrics)
            summary = {
                "schema_version": SCHEMA_VERSION,
                "variant": "s3",
                "training_variant": "anchor0_plus_one_no_physics",
                "source_path": str(FIXED_PHYSICS_TEST_FILE),
                "source_sha256": test_sha256,
                "sample_count": len(records),
                "split_seed": 44,
                "state_mask_seed": mask_seed,
                "state_mask_sha256": _state_mask_sha256(state_masks),
                "state_supervision_mode": STATE_SUPERVISION_MODE,
                "calibration": None,
                "parameter_tuning": False,
                "runtime_seconds": runtime_seconds,
                "peak_gpu_memory_mib": float(torch.cuda.max_memory_allocated() / (1024**2)),
                "metrics": metrics,
            }
            mask_dir = FIXED_OUTPUT_DIR / f"mask-seed{mask_seed}"
            _write_json(mask_dir / "physics_test_summary.json", summary)
            _write_jsonl(mask_dir / "physics_predictions.jsonl", predictions)
            _write_json(
                mask_dir / "analysis_training_view" / "training_summary.json",
                _analysis_training_view(original_training_summary, summary),
            )
            summaries[str(mask_seed)] = summary
            tracked = flatten_scalar_metrics(
                {
                    "metrics": metrics,
                    "runtime_seconds": runtime_seconds,
                    "peak_gpu_memory_mib": summary["peak_gpu_memory_mib"],
                },
                prefix=f"evaluation/mask_seed_{mask_seed}",
            )
            swanlab.log(tracked, step=step)
            _append_history(history_path, step, tracked)
            final_tracking_metrics.update(tracked)
            print(json.dumps(summary, ensure_ascii=False, sort_keys=True), flush=True)
            print(f"S3 同分区物理评估完成：state_mask_seed={mask_seed}", flush=True)

        immutable_hashes_after = {str(path): _file_sha256(path) for path in immutable_model_files}
        if immutable_hashes_after != immutable_hashes_before:
            raise S3SameSplitPhysicsError("只读评估前后 S3 权重或状态头哈希发生变化")
        combined = {
            "schema_version": SCHEMA_VERSION,
            "status": "finished",
            "model_id": probe.model_id,
            "s3_training_dir": str(FIXED_S3_TRAINING_DIR),
            "detection_adapter_path": str(FIXED_DETECTION_ADAPTER),
            "state_head_path": str(FIXED_STATE_HEAD),
            "source_path": str(FIXED_PHYSICS_TEST_FILE),
            "source_sha256": test_sha256,
            "sample_count": len(records),
            "split_seed": 44,
            "state_mask_seeds": list(MASK_SEEDS),
            "immutable_hashes_before": immutable_hashes_before,
            "immutable_hashes_after": immutable_hashes_after,
            "summaries": summaries,
        }
        _write_json(combined_summary_path, combined)
        _write_json(metrics_path, {"step": len(MASK_SEEDS), "metrics": final_tracking_metrics})
        swanlab.log(final_tracking_metrics, step=len(MASK_SEEDS) + 1)

    return _read_json(FIXED_OUTPUT_DIR / "artifact_manifest.json")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行冻结 S3 的 seed44 同分区物理评估")
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise S3SameSplitPhysicsError("配置根节点必须是映射")
    probe, tracking = load_fixed_configuration(raw)
    manifest = run_s3_same_split_physics(probe, tracking, raw, args.config)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
