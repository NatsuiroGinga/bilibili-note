"""共享 B0 状态监督与标准 PINN 的可恢复训练入口。"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import random
import sys
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, cast

import numpy as np
import torch
import yaml

from flow_probe.config import ProbeConfig
from flow_probe.physics_train import (
    ContinuousQueueStateHead,
    masked_state_target_loss,
    queue_balance_residual,
)
from flow_probe.qwen_physics_gradient import select_last_token_hidden
from flow_probe.shared_b0_physics_sidecar import validate_shared_b0_physics_sidecar
from flow_probe.train_sft import (
    TrainingSettings,
    build_chat_dataset,
    build_chat_training_records,
    build_optimizer_scheduler_kwargs,
    build_qwen_model_and_tokenizer,
    build_sft_trainer,
    build_training_binding,
    build_training_settings,
    load_training_records,
    training_binding_sha256,
)
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    build_init_kwargs,
    capture_console_log,
)

CONFIG_SCHEMA_VERSION = "flow_probe_shared_b0_physics_baselines_config_v1"
SCHEDULE_SCHEMA_VERSION = "flow_probe_shared_b0_schedule_v1"
BINDING_SCHEMA_VERSION = "flow_probe_shared_b0_physics_binding_v1"
RUN_STATE_SCHEMA_VERSION = "flow_probe_shared_b0_physics_run_state_v1"
CHECKPOINT_SCHEMA_VERSION = "flow_probe_shared_b0_physics_checkpoint_v1"
BASELINES = ("state_supervision", "standard_pinn")
EXPECTED_SEED = 42
EXPECTED_MAX_STEPS = 200
EXPECTED_SAVE_STEPS = 20
EXPECTED_EFFECTIVE_BATCH_SIZE = 4
EXPECTED_GENERATION_RECORDS = 800
EXPECTED_PHYSICS_RECORDS = 2421
EXPECTED_PHYSICS_MICRO_STEPS = 400
EXPECTED_PHYSICS_BATCHES_OF_SEVEN = 21
EXPECTED_PHYSICS_BATCHES_OF_SIX = 379
EXPECTED_PHYSICS_MICRO_STEPS_PER_OPTIMIZATION = 2
EXPECTED_STATE_ANCHORS = 5
EXPECTED_OBSERVED_ANCHORS = 2
EXPECTED_STATE_MASK = "anchor0_plus_one"
EXPECTED_PHYSICS_USAGE = "train_fit_diagnostic"
SWANLAB_PHASE = "train"
EXPECTED_VISIBLE_FIELDS = (
    "total_packets",
    "total_bytes",
    "packet_length_mean",
    "packet_length_min",
    "packet_length_max",
    "iat_mean_ms",
    "packet_rate",
    "byte_rate",
)
EXPECTED_CLASSIFICATION_TRAIN_FILE = (
    "runs/data-frozen/dataset-v1-shared-b0/candidate/qwen_train.jsonl"
)
EXPECTED_PHYSICS_SIDECAR_FILE = (
    "runs/data-frozen/dataset-v1-shared-b0-physics-v1/"
    "candidate/ns3_physics_train.jsonl"
)
PHYSICS_COEFFICIENT_FIELDS = frozenset(
    {
        "capacity_by_anchor",
        "received_bytes_by_anchor",
        "received_packets_by_anchor",
        "dequeued_bytes_by_anchor",
        "dropped_bytes_by_anchor",
        "normalization_scale",
    }
)
PROHIBITED_CLASSIFICATION_FIELDS = PHYSICS_COEFFICIENT_FIELDS | {
    "anchor_times",
    "state_targets",
    "state_mask_inputs",
    "source_file_sha256",
}
_CHECKPOINT_REQUIRED_FILES = frozenset(
    {
        "checkpoint_binding.json",
        "gradient_scaler.pt",
        "lora_trainable.pt",
        "metrics.json",
        "optimizer.pt",
        "rng_state.pt",
        "scheduler.pt",
        "state_head.pt",
        "trainer_state.json",
    }
)


class SharedB0PhysicsTrainingError(ValueError):
    """共享 B0 物理训练合同或恢复状态不合法。"""


class MetricLogger(Protocol):
    """训练期间可选的步级指标记录器。"""

    def log(self, metrics: Mapping[str, float], step: int) -> None: ...


@dataclass
class SwanLabStepLogger:
    """把训练器的完整步级标量写入 SwanLab 在线运行。"""

    client: Any
    last_step: int = 0

    def log(self, metrics: Mapping[str, float], step: int) -> None:
        required = {
            "optimization_step",
            "generation_loss",
            "state_loss",
            "physics_loss",
            "total_loss",
            "gradient_norm",
            "nonfinite_count",
        }
        missing = sorted(required - set(metrics))
        if missing:
            raise SharedB0PhysicsTrainingError(
                f"SwanLab 步级指标缺少字段：{', '.join(missing)}"
            )
        if int(metrics["optimization_step"]) != step or step <= self.last_step:
            raise SharedB0PhysicsTrainingError("SwanLab 步数必须严格递增并等于优化步")
        payload = {f"train/{key}": float(value) for key, value in metrics.items()}
        self.client.log(payload, step=step)
        self.last_step = step


@dataclass(frozen=True)
class CompositeMetricLogger:
    """让在线跟踪和调用方附加记录器消费同一份步级指标。"""

    loggers: tuple[MetricLogger, ...]

    def log(self, metrics: Mapping[str, float], step: int) -> None:
        for logger in self.loggers:
            logger.log(metrics, step)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SharedB0PhysicsTrainingError(f"{description}必须是映射")
    return value


def _string(mapping: Mapping[str, object], key: str, description: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SharedB0PhysicsTrainingError(f"{description}.{key} 必须是非空字符串")
    return value.strip()


def _integer(mapping: Mapping[str, object], key: str, description: str) -> int:
    value = mapping.get(key)
    if type(value) is not int:
        raise SharedB0PhysicsTrainingError(f"{description}.{key} 必须是整数")
    return value


def _number(mapping: Mapping[str, object], key: str, description: str) -> float:
    value = mapping.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise SharedB0PhysicsTrainingError(f"{description}.{key} 必须是数值")
    result = float(value)
    if not math.isfinite(result):
        raise SharedB0PhysicsTrainingError(f"{description}.{key} 必须是有限数")
    return result


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _atomic_write_json(path: Path, value: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as target:
            json.dump(
                value,
                target,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as target:
            for row in rows:
                target.write(
                    json.dumps(
                        dict(row),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    )
                    + "\n"
                )
            target.flush()
            os.fsync(target.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_json(path: Path, description: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SharedB0PhysicsTrainingError(
            f"无法读取有效{description}：{path}：{error}"
        ) from error
    if not isinstance(value, dict):
        raise SharedB0PhysicsTrainingError(f"{description}顶层必须是对象：{path}")
    return value


def _read_jsonl(path: Path, description: str) -> list[dict[str, object]]:
    rows = []
    try:
        with Path(path).open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise SharedB0PhysicsTrainingError(
                        f"{description}第 {line_number} 行必须是对象"
                    )
                rows.append(value)
    except json.JSONDecodeError as error:
        raise SharedB0PhysicsTrainingError(
            f"{description}包含非法 JSON：{path}：{error}"
        ) from error
    return rows


def build_swanlab_tracking_settings(
    baseline: str,
    output_dir: Path,
) -> TrackingSettings:
    """构造固定工作区、固定项目和可区分运行目录的在线跟踪配置。"""
    contract = build_baseline_contract(baseline)
    resolved_output_dir = Path(output_dir).expanduser().resolve()
    return TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": f"{resolved_output_dir.name}-{contract.name}",
            "description": "共享 B0 状态监督与标准 PINN 正式训练",
            "mode": "online",
            "tags": [
                "shared-b0",
                "physics",
                "seed-42",
                contract.name,
                "run-formal",
                "review-pending",
            ],
        }
    )


def _swanlab_run_record(
    *,
    settings: TrackingSettings,
    output_dir: Path,
    run_id: str,
    status: str,
    last_step: int,
    failure: str | None,
    finish_error: str | None,
) -> dict[str, object]:
    return {
        "schema_version": "flow_probe_shared_b0_swanlab_run_v1",
        "status": status,
        "tracking_mode": settings.mode,
        "workspace": settings.workspace,
        "project": settings.project,
        "run_name": f"{settings.run_name}-{SWANLAB_PHASE}",
        "run_id": run_id,
        "run_url": (
            f"https://swanlab.cn/@{settings.workspace}/{settings.project}"
            f"/runs/{run_id}/chart"
            if run_id
            else None
        ),
        "log_dir": str(Path(output_dir) / "swanlog" / SWANLAB_PHASE),
        "last_completed_step": last_step,
        "failure": failure,
        "finish_error": finish_error,
        "updated_at": _utc_now(),
    }


@contextmanager
def swanlab_online_training_run(
    config: SharedB0PhysicsConfig,
    baseline: str,
    output_dir: Path,
    binding: Mapping[str, object],
    *,
    swanlab_module: Any | None = None,
) -> Iterator[SwanLabStepLogger]:
    """启动在线跟踪，并保证训练成功或失败后都调用结束接口。"""
    resolved_output_dir = Path(output_dir).expanduser().resolve()
    log_dir = resolved_output_dir / "swanlog" / SWANLAB_PHASE
    log_dir.mkdir(parents=True, exist_ok=True)
    record_path = resolved_output_dir / "swanlab_run.json"
    settings = build_swanlab_tracking_settings(baseline, resolved_output_dir)
    tracking_config = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "baseline": build_baseline_contract(baseline).name,
        "seed": config.probe.seed,
        "max_steps": config.max_steps,
        "lambda_state": binding["lambda_state"],
        "lambda_physics": binding["lambda_physics"],
        "binding_sha256": binding["binding_sha256"],
        "output_dir": str(resolved_output_dir),
    }
    client = swanlab_module if swanlab_module is not None else __import__("swanlab")
    run_id = ""
    status = "initializing"
    failure: str | None = None
    finish_error: str | None = None
    try:
        run = client.init(
            **build_init_kwargs(
                settings,
                SWANLAB_PHASE,
                tracking_config,
                log_dir=log_dir,
            )
        )
    except BaseException as error:
        failure = f"{type(error).__name__}: {error}"
        _atomic_write_json(
            record_path,
            _swanlab_run_record(
                settings=settings,
                output_dir=resolved_output_dir,
                run_id=run_id,
                status="initialization_failed",
                last_step=0,
                failure=failure,
                finish_error=None,
            ),
        )
        raise
    run_id = str(getattr(run, "id", "")).strip()
    if not run_id:
        error = SharedB0PhysicsTrainingError("SwanLab 在线运行没有返回 run_id")
        failure = f"{type(error).__name__}: {error}"
        try:
            client.finish(state="crashed", error=str(error))
        except BaseException as error_during_finish:
            finish_error = (
                f"{type(error_during_finish).__name__}: {error_during_finish}"
            )
        _atomic_write_json(
            record_path,
            _swanlab_run_record(
                settings=settings,
                output_dir=resolved_output_dir,
                run_id=run_id,
                status="initialization_failed",
                last_step=0,
                failure=failure,
                finish_error=finish_error,
            ),
        )
        raise error

    logger = SwanLabStepLogger(client)
    status = "running"
    _atomic_write_json(
        record_path,
        _swanlab_run_record(
            settings=settings,
            output_dir=resolved_output_dir,
            run_id=run_id,
            status=status,
            last_step=0,
            failure=None,
            finish_error=None,
        ),
    )
    try:
        yield logger
    except BaseException as error:
        status = "crashed"
        failure = f"{type(error).__name__}: {error}"
        try:
            client.log(
                {
                    "run/failed": 1.0,
                    "run/last_completed_step": float(logger.last_step),
                    "run/nonfinite_count": (
                        1.0 if isinstance(error, FloatingPointError) else 0.0
                    ),
                },
                step=logger.last_step,
            )
        except BaseException:
            pass
        try:
            client.finish(state="crashed", error=str(error))
        except BaseException as error_during_finish:
            finish_error = (
                f"{type(error_during_finish).__name__}: {error_during_finish}"
            )
        raise
    else:
        try:
            client.finish()
        except BaseException as error:
            status = "crashed"
            failure = f"{type(error).__name__}: {error}"
            raise
        status = "finished"
    finally:
        _atomic_write_json(
            record_path,
            _swanlab_run_record(
                settings=settings,
                output_dir=resolved_output_dir,
                run_id=run_id,
                status=status,
                last_step=logger.last_step,
                failure=failure,
                finish_error=finish_error,
            ),
        )


@dataclass(frozen=True)
class BaselineContract:
    """两条基线唯一允许不同的损失开关。"""

    name: str
    lambda_state: float
    lambda_physics: float
    reads_physics_coefficients: bool


def build_baseline_contract(name: str) -> BaselineContract:
    normalized = str(name).strip().lower()
    if normalized not in BASELINES:
        raise SharedB0PhysicsTrainingError(f"未知共享 B0 物理基线：{name}")
    return BaselineContract(
        name=normalized,
        lambda_state=1.0,
        lambda_physics=0.0 if normalized == "state_supervision" else 0.01,
        reads_physics_coefficients=normalized == "standard_pinn",
    )


def validate_generation_batch_contract(
    micro_batch_size: int, gradient_accumulation_steps: int
) -> None:
    pair = (micro_batch_size, gradient_accumulation_steps)
    if pair not in {(2, 2), (1, 4)}:
        raise SharedB0PhysicsTrainingError("生成批量只允许主档 2x2 或硬件回退档 1x4")
    if micro_batch_size * gradient_accumulation_steps != EXPECTED_EFFECTIVE_BATCH_SIZE:
        raise SharedB0PhysicsTrainingError("有效生成批量必须严格为 4")


@dataclass(frozen=True)
class SharedB0PhysicsConfig:
    """两条基线共同使用的已冻结配置。"""

    config_path: Path
    config_sha256: str
    probe: ProbeConfig
    classification_train_file: Path
    classification_validation_file: Path
    physics_sidecar_root: Path
    physics_sidecar_file: Path
    physics_dataset_manifest: Path
    visible_observation_fields: tuple[str, ...]
    generation_records_per_run: int
    physics_records: int
    physics_micro_steps: int
    physics_usage: str
    state_mask: str
    state_anchor_count: int
    state_observed_anchors: int
    learning_rate: float
    generation_micro_batch_size: int
    generation_gradient_accumulation_steps: int
    fallback_generation_micro_batch_size: int
    fallback_generation_gradient_accumulation_steps: int
    num_train_epochs: float
    max_steps: int
    save_steps: int
    max_grad_norm: float
    attention_backend: str
    group_by_length: bool
    lambda_state: float
    lambda_physics_by_baseline: tuple[tuple[str, float], ...]
    output_dirs: tuple[tuple[str, Path], ...]
    raw: Mapping[str, object]

    def output_dir(self, baseline: str) -> Path:
        contract = build_baseline_contract(baseline)
        return dict(self.output_dirs)[contract.name]

    def loss_weights(self, baseline: str) -> tuple[float, float]:
        contract = build_baseline_contract(baseline)
        return self.lambda_state, dict(self.lambda_physics_by_baseline)[contract.name]

    def generation_batch(self, use_hardware_fallback: bool) -> tuple[int, int]:
        if use_hardware_fallback:
            return (
                self.fallback_generation_micro_batch_size,
                self.fallback_generation_gradient_accumulation_steps,
            )
        return (
            self.generation_micro_batch_size,
            self.generation_gradient_accumulation_steps,
        )

    def training_settings(
        self,
        baseline: str,
        use_hardware_fallback: bool = False,
        *,
        output_dir: Path | None = None,
    ) -> TrainingSettings:
        micro_batch_size, accumulation = self.generation_batch(use_hardware_fallback)
        resolved_output_dir = (
            self.output_dir(baseline) if output_dir is None else Path(output_dir)
        )
        settings = build_training_settings(
            self.probe,
            {
                "train_file": str(self.classification_train_file),
                "validation_file": str(self.classification_validation_file),
                "output_dir": str(resolved_output_dir),
                "learning_rate": self.learning_rate,
                "per_device_train_batch_size": micro_batch_size,
                "gradient_accumulation_steps": accumulation,
                "num_train_epochs": self.num_train_epochs,
                "max_steps": self.max_steps,
                "save_steps": self.save_steps,
                "resume_from_checkpoint": "never",
                "attention_backend": self.attention_backend,
                "group_by_length": self.group_by_length,
            },
        )
        validate_generation_batch_contract(
            settings.per_device_train_batch_size,
            settings.gradient_accumulation_steps,
        )
        return settings


def load_shared_b0_physics_training_config(path: Path) -> SharedB0PhysicsConfig:
    """读取并冻结任务 03 的全部科学参数。"""
    path = Path(path)
    try:
        raw_value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise SharedB0PhysicsTrainingError(
            f"无法读取训练配置：{path}：{error}"
        ) from error
    raw = _mapping(raw_value, "训练配置")
    if raw.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise SharedB0PhysicsTrainingError("训练配置 schema_version 不匹配")
    probe = ProbeConfig.from_mapping(_mapping(raw.get("probe"), "probe"))
    if probe.seed != EXPECTED_SEED:
        raise SharedB0PhysicsTrainingError("共享 B0 物理基线种子必须固定为 42")
    if probe.feature_view != "shared_b0_common_v1":
        raise SharedB0PhysicsTrainingError("字段视图必须固定为 shared_b0_common_v1")

    data = _mapping(raw.get("data"), "data")
    classification_train = _string(data, "classification_train_file", "data")
    if classification_train != EXPECTED_CLASSIFICATION_TRAIN_FILE:
        raise SharedB0PhysicsTrainingError("分类训练文件必须绑定冻结 shared B0 清单")
    physics_sidecar_file = _string(data, "physics_sidecar_file", "data")
    if physics_sidecar_file != EXPECTED_PHYSICS_SIDECAR_FILE:
        raise SharedB0PhysicsTrainingError("物理旁路文件必须绑定冻结 shared B0 旁路")
    visible_fields_value = data.get("visible_observation_fields")
    if not isinstance(visible_fields_value, list) or any(
        not isinstance(value, str) for value in visible_fields_value
    ):
        raise SharedB0PhysicsTrainingError(
            "visible_observation_fields 必须是字符串列表"
        )
    visible_fields = tuple(visible_fields_value)
    if visible_fields != EXPECTED_VISIBLE_FIELDS:
        raise SharedB0PhysicsTrainingError(
            "普通 Qwen 可见字段必须严格为已发布的八个共同字段"
        )

    protocol = _mapping(raw.get("protocol"), "protocol")
    expected_integers = {
        "generation_records_per_run": EXPECTED_GENERATION_RECORDS,
        "physics_records": EXPECTED_PHYSICS_RECORDS,
        "physics_micro_steps": EXPECTED_PHYSICS_MICRO_STEPS,
        "state_anchor_count": EXPECTED_STATE_ANCHORS,
        "state_observed_anchors": EXPECTED_OBSERVED_ANCHORS,
    }
    for key, expected in expected_integers.items():
        if _integer(protocol, key, "protocol") != expected:
            raise SharedB0PhysicsTrainingError(f"protocol.{key} 必须固定为 {expected}")
    if _string(protocol, "physics_usage", "protocol") != EXPECTED_PHYSICS_USAGE:
        raise SharedB0PhysicsTrainingError("物理用途必须固定为 train_fit_diagnostic")
    if _string(protocol, "state_mask", "protocol") != EXPECTED_STATE_MASK:
        raise SharedB0PhysicsTrainingError("状态掩码必须固定为 anchor0_plus_one")

    training = _mapping(raw.get("training"), "training")
    micro_batch = _integer(training, "generation_micro_batch_size", "training")
    accumulation = _integer(
        training, "generation_gradient_accumulation_steps", "training"
    )
    validate_generation_batch_contract(micro_batch, accumulation)
    if _integer(training, "effective_generation_batch_size", "training") != 4:
        raise SharedB0PhysicsTrainingError("配置声明的有效生成批量必须为 4")
    fallback = _mapping(training.get("hardware_fallback"), "training.hardware_fallback")
    fallback_micro = _integer(
        fallback, "generation_micro_batch_size", "training.hardware_fallback"
    )
    fallback_accumulation = _integer(
        fallback,
        "generation_gradient_accumulation_steps",
        "training.hardware_fallback",
    )
    validate_generation_batch_contract(fallback_micro, fallback_accumulation)
    if (micro_batch, accumulation) != (2, 2) or (
        fallback_micro,
        fallback_accumulation,
    ) != (1, 4):
        raise SharedB0PhysicsTrainingError("主档和回退档必须分别固定为 2x2 与 1x4")
    if _integer(training, "max_steps", "training") != EXPECTED_MAX_STEPS:
        raise SharedB0PhysicsTrainingError("优化步数必须固定为 200")
    if _integer(training, "save_steps", "training") != EXPECTED_SAVE_STEPS:
        raise SharedB0PhysicsTrainingError("检查点间隔必须固定为 20")
    if _number(training, "lambda_state", "training") != 1.0:
        raise SharedB0PhysicsTrainingError("lambda_state 必须固定为 1.0")
    lambda_physics = _mapping(training.get("lambda_physics"), "training.lambda_physics")
    lambda_pairs = tuple(
        (baseline, _number(lambda_physics, baseline, "training.lambda_physics"))
        for baseline in BASELINES
    )
    if dict(lambda_pairs) != {"state_supervision": 0.0, "standard_pinn": 0.01}:
        raise SharedB0PhysicsTrainingError(
            "两条基线的 lambda_physics 必须固定为 0 与 0.01"
        )
    group_by_length = training.get("group_by_length")
    if type(group_by_length) is not bool or group_by_length:
        raise SharedB0PhysicsTrainingError("共享 B0 训练必须关闭长度分组")

    outputs = _mapping(raw.get("outputs"), "outputs")
    output_pairs = tuple(
        (baseline, Path(_string(outputs, baseline, "outputs")))
        for baseline in BASELINES
    )
    config = SharedB0PhysicsConfig(
        config_path=path,
        config_sha256=_file_sha256(path),
        probe=probe,
        classification_train_file=Path(classification_train),
        classification_validation_file=Path(
            _string(data, "classification_validation_file", "data")
        ),
        physics_sidecar_root=Path(_string(data, "physics_sidecar_root", "data")),
        physics_sidecar_file=Path(physics_sidecar_file),
        physics_dataset_manifest=Path(
            _string(data, "physics_dataset_manifest", "data")
        ),
        visible_observation_fields=visible_fields,
        generation_records_per_run=EXPECTED_GENERATION_RECORDS,
        physics_records=EXPECTED_PHYSICS_RECORDS,
        physics_micro_steps=EXPECTED_PHYSICS_MICRO_STEPS,
        physics_usage=EXPECTED_PHYSICS_USAGE,
        state_mask=EXPECTED_STATE_MASK,
        state_anchor_count=EXPECTED_STATE_ANCHORS,
        state_observed_anchors=EXPECTED_OBSERVED_ANCHORS,
        learning_rate=_number(training, "learning_rate", "training"),
        generation_micro_batch_size=micro_batch,
        generation_gradient_accumulation_steps=accumulation,
        fallback_generation_micro_batch_size=fallback_micro,
        fallback_generation_gradient_accumulation_steps=fallback_accumulation,
        num_train_epochs=_number(training, "num_train_epochs", "training"),
        max_steps=EXPECTED_MAX_STEPS,
        save_steps=EXPECTED_SAVE_STEPS,
        max_grad_norm=_number(training, "max_grad_norm", "training"),
        attention_backend=_string(training, "attention_backend", "training"),
        group_by_length=False,
        lambda_state=1.0,
        lambda_physics_by_baseline=lambda_pairs,
        output_dirs=output_pairs,
        raw=dict(raw),
    )
    if config.learning_rate <= 0 or config.max_grad_norm <= 0:
        raise SharedB0PhysicsTrainingError("学习率和梯度裁剪上限必须大于零")
    if config.num_train_epochs != 1.0:
        raise SharedB0PhysicsTrainingError("共享 B0 训练轮数合同必须固定为 1")
    if config.max_grad_norm != 1.0:
        raise SharedB0PhysicsTrainingError("梯度裁剪上限必须固定为 1.0")
    expected_optimizer = {
        "learning_rate": config.learning_rate,
        "optim": "paged_adamw_8bit",
        "lr_scheduler_type": "linear",
        "warmup_ratio": 0.0,
        "warmup_steps": 0,
        "max_grad_norm": 1.0,
    }
    if build_optimizer_scheduler_kwargs(config.training_settings(BASELINES[0])) != (
        expected_optimizer
    ):
        raise SharedB0PhysicsTrainingError("普通 Qwen 优化器或调度器合同发生漂移")
    return config


@dataclass(frozen=True)
class FrozenSchedule:
    """包含完整顺序、批边界和三类哈希的冻结调度。"""

    kind: str
    batches: tuple[tuple[str, ...], ...]
    order_sha256: str
    batch_boundaries_sha256: str
    schedule_sha256: str

    @property
    def sample_ids(self) -> tuple[str, ...]:
        return tuple(sample_id for batch in self.batches for sample_id in batch)

    @property
    def batch_sizes(self) -> tuple[int, ...]:
        return tuple(len(batch) for batch in self.batches)

    def to_mapping(self) -> dict[str, object]:
        boundaries = []
        cursor = 0
        for batch in self.batches:
            boundaries.append([cursor, cursor + len(batch)])
            cursor += len(batch)
        value = {
            "schema_version": SCHEDULE_SCHEMA_VERSION,
            "kind": self.kind,
            "sample_ids": list(self.sample_ids),
            "batch_boundaries": boundaries,
            "order_sha256": self.order_sha256,
            "batch_boundaries_sha256": self.batch_boundaries_sha256,
        }
        if _canonical_sha256(value) != self.schedule_sha256:
            raise SharedB0PhysicsTrainingError("冻结调度自身哈希不一致")
        return {**value, "schedule_sha256": self.schedule_sha256}


def _freeze_schedule(kind: str, batches: Sequence[Sequence[str]]) -> FrozenSchedule:
    frozen = tuple(tuple(batch) for batch in batches)
    sample_ids = [sample_id for batch in frozen for sample_id in batch]
    boundaries = []
    cursor = 0
    for batch in frozen:
        boundaries.append((cursor, cursor + len(batch)))
        cursor += len(batch)
    order_sha256 = _canonical_sha256(sample_ids)
    boundaries_sha256 = _canonical_sha256(boundaries)
    value = {
        "schema_version": SCHEDULE_SCHEMA_VERSION,
        "kind": kind,
        "sample_ids": sample_ids,
        "batch_boundaries": boundaries,
        "order_sha256": order_sha256,
        "batch_boundaries_sha256": boundaries_sha256,
    }
    return FrozenSchedule(
        kind=kind,
        batches=frozen,
        order_sha256=order_sha256,
        batch_boundaries_sha256=boundaries_sha256,
        schedule_sha256=_canonical_sha256(value),
    )


def _unique_sample_ids(
    records: Sequence[Mapping[str, object]], description: str
) -> list[str]:
    sample_ids = []
    seen = set()
    for index, record in enumerate(records):
        sample_id = str(record.get("sample_id", "")).strip()
        if not sample_id:
            raise SharedB0PhysicsTrainingError(
                f"{description}第 {index} 条缺少 sample_id"
            )
        if sample_id in seen:
            raise SharedB0PhysicsTrainingError(
                f"{description}发现重复 sample_id：{sample_id}"
            )
        seen.add(sample_id)
        sample_ids.append(sample_id)
    return sample_ids


def build_generation_schedule(
    records: Sequence[Mapping[str, object]],
    *,
    micro_batch_size: int,
    gradient_accumulation_steps: int,
    max_steps: int = EXPECTED_MAX_STEPS,
    seed: int = EXPECTED_SEED,
) -> FrozenSchedule:
    """冻结 800 个生成位置，并按硬件档位切分固定微批边界。"""
    validate_generation_batch_contract(micro_batch_size, gradient_accumulation_steps)
    required = max_steps * micro_batch_size * gradient_accumulation_steps
    if required != EXPECTED_GENERATION_RECORDS:
        raise SharedB0PhysicsTrainingError("生成位置必须严格为 800")
    sample_ids = _unique_sample_ids(records, "分类训练清单")
    if len(sample_ids) < required:
        raise SharedB0PhysicsTrainingError("分类训练清单不足 800 条，禁止过采样")
    shuffled = list(sample_ids)
    random.Random(seed).shuffle(shuffled)
    order = shuffled[:required]
    batches = [
        order[offset : offset + micro_batch_size]
        for offset in range(0, required, micro_batch_size)
    ]
    expected_micro_steps = max_steps * gradient_accumulation_steps
    if len(batches) != expected_micro_steps:
        raise SharedB0PhysicsTrainingError("生成微步数与梯度累积不一致")
    return _freeze_schedule("generation", batches)


def build_physics_schedule(
    records: Sequence[Mapping[str, object]],
    *,
    seed: int = EXPECTED_SEED,
) -> FrozenSchedule:
    """冻结 21 个七样本批和 379 个六样本批，记录各出现一次。"""
    if len(records) != EXPECTED_PHYSICS_RECORDS:
        raise SharedB0PhysicsTrainingError("物理旁路记录数必须严格为 2421")
    sample_ids = _unique_sample_ids(records, "物理旁路")
    ordered = sorted(
        zip(sample_ids, records, strict=True),
        key=lambda item: (_integer(item[1], "stable_order", "物理旁路记录"), item[0]),
    )
    shuffled = [sample_id for sample_id, _ in ordered]
    random.Random(seed).shuffle(shuffled)
    sizes = [7] * EXPECTED_PHYSICS_BATCHES_OF_SEVEN + [
        6
    ] * EXPECTED_PHYSICS_BATCHES_OF_SIX
    batches = []
    cursor = 0
    for size in sizes:
        batches.append(shuffled[cursor : cursor + size])
        cursor += size
    if (
        cursor != EXPECTED_PHYSICS_RECORDS
        or len(batches) != EXPECTED_PHYSICS_MICRO_STEPS
    ):
        raise SharedB0PhysicsTrainingError(
            "物理调度没有精确覆盖 2421 条记录和 400 微步"
        )
    schedule = _freeze_schedule("physics", batches)
    if len(set(schedule.sample_ids)) != EXPECTED_PHYSICS_RECORDS:
        raise SharedB0PhysicsTrainingError("物理调度存在重复或遗漏样本")
    return schedule


@dataclass(frozen=True)
class StateSidecarRecord:
    """状态监督分支唯一允许读取的旁路视图。"""

    sample_id: str
    state_targets: tuple[float, float, float, float, float]
    state_mask: tuple[bool, bool, bool, bool, bool]


@dataclass(frozen=True)
class PhysicsSidecarRecord(StateSidecarRecord):
    """标准 PINN 分支在状态视图外延迟读取的物理系数。"""

    scale: float
    capacity: tuple[float, float, float, float]
    received: tuple[float, float, float, float]
    dequeued: tuple[float, float, float, float]
    dropped_before: tuple[float, float, float, float]
    dropped_after: tuple[float, float, float, float]


def _finite_sequence(value: object, length: int, description: str) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise SharedB0PhysicsTrainingError(f"{description}必须包含 {length} 个数值")
    result = []
    for item in value:
        if not isinstance(item, (int, float)) or isinstance(item, bool):
            raise SharedB0PhysicsTrainingError(f"{description}必须只包含数值")
        number = float(item)
        if not math.isfinite(number):
            raise SharedB0PhysicsTrainingError(f"{description}包含非有限数")
        result.append(number)
    return tuple(result)


def parse_state_sidecar_record(record: Mapping[str, object]) -> StateSidecarRecord:
    """只读取已验签掩码和状态目标，不触碰任何物理系数字段。"""
    sample_id_value = record.get("sample_id")
    if not isinstance(sample_id_value, str) or not sample_id_value.strip():
        raise SharedB0PhysicsTrainingError("状态旁路记录缺少 sample_id")
    if record.get("usage") != EXPECTED_PHYSICS_USAGE:
        raise SharedB0PhysicsTrainingError(
            "状态旁路记录用途必须为 train_fit_diagnostic"
        )
    targets = _finite_sequence(record.get("state_targets"), 5, "state_targets")
    raw_mask = record.get("state_mask_inputs")
    if (
        not isinstance(raw_mask, (list, tuple))
        or len(raw_mask) != EXPECTED_STATE_ANCHORS
    ):
        raise SharedB0PhysicsTrainingError("state_mask_inputs 必须包含五个布尔值")
    if any(type(value) is not bool for value in raw_mask):
        raise SharedB0PhysicsTrainingError("state_mask_inputs 必须只包含布尔值")
    mask = tuple(raw_mask)
    if not mask[0] or sum(mask) != EXPECTED_OBSERVED_ANCHORS:
        raise SharedB0PhysicsTrainingError(
            "state_mask_inputs 必须包含 anchor0 且恰有两个真值"
        )
    return StateSidecarRecord(
        sample_id=sample_id_value.strip(),
        state_targets=targets,  # type: ignore[arg-type]
        state_mask=mask,  # type: ignore[arg-type]
    )


def _cumulative_differences(value: object, description: str) -> tuple[float, ...]:
    cumulative = _finite_sequence(value, 5, description)
    if not math.isclose(cumulative[0], 0.0, abs_tol=1e-12):
        raise SharedB0PhysicsTrainingError(f"{description}必须从零开始")
    differences = tuple(
        following - current
        for current, following in zip(cumulative, cumulative[1:], strict=False)
    )
    if any(number < 0 for number in differences):
        raise SharedB0PhysicsTrainingError(f"{description}必须单调不减")
    return differences


def parse_physics_sidecar_record(record: Mapping[str, object]) -> PhysicsSidecarRecord:
    """仅标准 PINN 分支调用，累计量在此恢复为四窗口系数。"""
    state = parse_state_sidecar_record(record)
    scale_value = record.get("normalization_scale")
    if not isinstance(scale_value, (int, float)) or isinstance(scale_value, bool):
        raise SharedB0PhysicsTrainingError("normalization_scale 必须是数值")
    scale = float(scale_value)
    if not math.isfinite(scale) or scale <= 0:
        raise SharedB0PhysicsTrainingError("normalization_scale 必须是有限正数")
    capacity = _cumulative_differences(
        record.get("capacity_by_anchor"), "capacity_by_anchor"
    )
    if any(value <= 0 for value in capacity):
        raise SharedB0PhysicsTrainingError("每个窗口的容量积分必须严格为正")
    received = _cumulative_differences(
        record.get("received_bytes_by_anchor"), "received_bytes_by_anchor"
    )
    dequeued = _cumulative_differences(
        record.get("dequeued_bytes_by_anchor"), "dequeued_bytes_by_anchor"
    )
    dropped = _cumulative_differences(
        record.get("dropped_bytes_by_anchor"), "dropped_bytes_by_anchor"
    )
    return PhysicsSidecarRecord(
        sample_id=state.sample_id,
        state_targets=state.state_targets,
        state_mask=state.state_mask,
        scale=scale,
        capacity=capacity,  # type: ignore[arg-type]
        received=received,  # type: ignore[arg-type]
        dequeued=dequeued,  # type: ignore[arg-type]
        dropped_before=dropped,  # type: ignore[arg-type]
        dropped_after=(0.0, 0.0, 0.0, 0.0),
    )


def state_mask_sha256(records: Sequence[StateSidecarRecord]) -> str:
    return _canonical_sha256(
        [
            {
                "sample_id": record.sample_id,
                "state_mask_inputs": list(record.state_mask),
            }
            for record in sorted(records, key=lambda item: item.sample_id)
        ]
    )


@dataclass(frozen=True)
class AuxiliaryTensorBatch:
    """状态张量与按基线延迟构造的物理张量。"""

    state_targets: torch.Tensor
    state_mask: torch.Tensor
    scale: torch.Tensor | None = None
    capacity: torch.Tensor | None = None
    received: torch.Tensor | None = None
    dequeued: torch.Tensor | None = None
    dropped_before: torch.Tensor | None = None
    dropped_after: torch.Tensor | None = None


def build_auxiliary_tensor_batch(
    records: Sequence[Mapping[str, object]],
    baseline: str,
    device: torch.device | str,
) -> AuxiliaryTensorBatch:
    """状态分支不构造物理记录，从字段访问层保证隔离。"""
    contract = build_baseline_contract(baseline)
    if contract.reads_physics_coefficients:
        prepared = [parse_physics_sidecar_record(record) for record in records]
    else:
        prepared = [parse_state_sidecar_record(record) for record in records]
    common = {
        "state_targets": torch.tensor(
            [record.state_targets for record in prepared],
            dtype=torch.float32,
            device=device,
        ),
        "state_mask": torch.tensor(
            [record.state_mask for record in prepared],
            dtype=torch.bool,
            device=device,
        ),
    }
    if not contract.reads_physics_coefficients:
        return AuxiliaryTensorBatch(**common)
    physics = [
        record for record in prepared if isinstance(record, PhysicsSidecarRecord)
    ]
    if len(physics) != len(prepared):
        raise SharedB0PhysicsTrainingError("标准 PINN 物理张量构造不完整")
    return AuxiliaryTensorBatch(
        **common,
        scale=torch.tensor(
            [record.scale for record in physics], dtype=torch.float32, device=device
        ),
        capacity=torch.tensor(
            [record.capacity for record in physics], dtype=torch.float32, device=device
        ),
        received=torch.tensor(
            [record.received for record in physics], dtype=torch.float32, device=device
        ),
        dequeued=torch.tensor(
            [record.dequeued for record in physics], dtype=torch.float32, device=device
        ),
        dropped_before=torch.tensor(
            [record.dropped_before for record in physics],
            dtype=torch.float32,
            device=device,
        ),
        dropped_after=torch.tensor(
            [record.dropped_after for record in physics],
            dtype=torch.float32,
            device=device,
        ),
    )


@dataclass(frozen=True)
class AuxiliaryLoss:
    """状态和物理损失的公共归约结果。"""

    total: torch.Tensor
    state: torch.Tensor
    physics: torch.Tensor | None
    valid_state_elements: int
    physics_coefficients_accessed: bool


def compute_auxiliary_loss(
    predicted_state: torch.Tensor,
    tensors: AuxiliaryTensorBatch,
    baseline: str,
) -> AuxiliaryLoss:
    """复用既有掩码均方误差和队列平衡残差，不复制公式。"""
    contract = build_baseline_contract(baseline)
    state_loss = masked_state_target_loss(
        predicted_state,
        tensors.state_targets,
        tensors.state_mask,
    )
    valid_elements = int(tensors.state_mask.sum().item())
    physics_loss = None
    total = contract.lambda_state * state_loss
    if contract.reads_physics_coefficients:
        coefficients = (
            tensors.scale,
            tensors.capacity,
            tensors.received,
            tensors.dequeued,
            tensors.dropped_before,
            tensors.dropped_after,
        )
        if any(value is None for value in coefficients):
            raise SharedB0PhysicsTrainingError("标准 PINN 缺少队列平衡残差系数")
        residual = queue_balance_residual(
            predicted_state,
            tensors.scale,  # type: ignore[arg-type]
            tensors.capacity,  # type: ignore[arg-type]
            tensors.received,  # type: ignore[arg-type]
            tensors.dequeued,  # type: ignore[arg-type]
            tensors.dropped_before,  # type: ignore[arg-type]
            tensors.dropped_after,  # type: ignore[arg-type]
        )
        physics_loss = residual.square().mean()
        total = total + contract.lambda_physics * physics_loss
    return AuxiliaryLoss(
        total=total,
        state=state_loss,
        physics=physics_loss,
        valid_state_elements=valid_elements,
        physics_coefficients_accessed=contract.reads_physics_coefficients,
    )


def physics_batch_weight(actual_batch_size: int) -> float:
    """把变批批均值换算为 2,421 条记录逐样本等权。"""
    if actual_batch_size not in {6, 7}:
        raise SharedB0PhysicsTrainingError("物理微批量只允许 6 或 7")
    return actual_batch_size / (EXPECTED_PHYSICS_RECORDS / EXPECTED_PHYSICS_MICRO_STEPS)


def ensure_finite_losses(**losses: torch.Tensor | None) -> None:
    nonfinite = [
        name
        for name, value in losses.items()
        if value is not None and not bool(torch.isfinite(value.detach()).all().item())
    ]
    if nonfinite:
        raise FloatingPointError(f"损失包含非有限数：{', '.join(sorted(nonfinite))}")


def finite_gradient_norm(parameters: Sequence[torch.nn.Parameter]) -> float:
    """在裁剪前检查全部梯度，并返回联合二范数。"""
    total = 0.0
    nonfinite_count = 0
    for parameter in parameters:
        if parameter.grad is None:
            continue
        gradient = parameter.grad.detach().float()
        nonfinite_count += int((~torch.isfinite(gradient)).sum().item())
        total += float(gradient.square().sum().item())
    if nonfinite_count:
        raise FloatingPointError(f"梯度包含 {nonfinite_count} 个非有限数")
    norm = math.sqrt(total)
    if not math.isfinite(norm):
        raise FloatingPointError("梯度范数不是有限数")
    return norm


def parameter_tree_sha256(module: torch.nn.Module) -> str:
    """对参数名、形状、数据类型和原始字节计算稳定摘要。"""
    digest = hashlib.sha256()
    state = module.state_dict()
    for name in sorted(state):
        tensor = state[name].detach().cpu().contiguous()
        metadata = {
            "name": name,
            "shape": list(tensor.shape),
            "dtype": str(tensor.dtype),
        }
        digest.update(_canonical_json_bytes(metadata))
        digest.update(tensor.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def trainable_model_parameter_sha256(
    model: torch.nn.Module, state_head: torch.nn.Module
) -> str:
    """计算 LoRA 可训练参数初始树摘要，并排除独立状态头。"""
    state_head_parameter_ids = {id(parameter) for parameter in state_head.parameters()}
    values = [
        (name, parameter)
        for name, parameter in model.named_parameters()
        if parameter.requires_grad and id(parameter) not in state_head_parameter_ids
    ]
    if not values:
        raise SharedB0PhysicsTrainingError("模型没有可哈希的 LoRA 参数")
    digest = hashlib.sha256()
    for name, parameter in sorted(values, key=lambda item: item[0]):
        tensor = parameter.detach().cpu().contiguous()
        digest.update(
            _canonical_json_bytes(
                {"name": name, "shape": list(tensor.shape), "dtype": str(tensor.dtype)}
            )
        )
        digest.update(tensor.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def initialize_state_head(
    hidden_size: int,
    seed: int = EXPECTED_SEED,
) -> tuple[ContinuousQueueStateHead, str]:
    """用独立 CPU 随机状态生成两条基线完全相同的状态头。"""
    if hidden_size <= 0:
        raise SharedB0PhysicsTrainingError("状态头隐藏维度必须大于零")
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        state_head = ContinuousQueueStateHead(hidden_size)
    return state_head, parameter_tree_sha256(state_head)


def build_state_prompt_texts(
    classification_records: Sequence[Mapping[str, object]], tokenizer: object
) -> list[str]:
    """只用任务 02 普通聊天构建接口生成状态前向提示词。"""
    formatted = build_chat_training_records(classification_records, tokenizer)
    prompts = []
    for record in formatted:
        prompt = record.get("prompt")
        if not isinstance(prompt, str):
            raise SharedB0PhysicsTrainingError("普通聊天构建结果缺少 prompt")
        prompts.append(prompt)
    return prompts


@dataclass(frozen=True)
class PreparedInputs:
    """模型加载前完成的分类、旁路、连接和调度门禁。"""

    classification_records: tuple[Mapping[str, object], ...]
    validation_records: tuple[Mapping[str, object], ...]
    classification_by_id: Mapping[str, Mapping[str, object]]
    sidecar_records: tuple[Mapping[str, object], ...]
    sidecar_by_id: Mapping[str, Mapping[str, object]]
    generation_schedule: FrozenSchedule
    physics_schedule: FrozenSchedule
    state_mask_sha256: str
    hashes: Mapping[str, str]
    audit: Mapping[str, object]

    def summary(
        self,
        config: SharedB0PhysicsConfig,
        baseline: str,
        *,
        output_dir: Path | None = None,
    ) -> dict[str, object]:
        contract = build_baseline_contract(baseline)
        settings = config.training_settings(contract.name, output_dir=output_dir)
        sizes = self.physics_schedule.batch_sizes
        return {
            "status": "passed",
            "baseline": contract.name,
            "classification_train_file": str(config.classification_train_file),
            "classification_records": len(self.classification_records),
            "classification_sha256": self.hashes["classification_train_file"],
            "physics_sidecar_file": str(config.physics_sidecar_file),
            "physics_records": len(self.sidecar_records),
            "physics_sidecar_sha256": self.hashes["physics_sidecar_file"],
            "effective_generation_batch_size": settings.effective_batch_size,
            "optimization_steps": config.max_steps,
            "generation_micro_steps": len(self.generation_schedule.batches),
            "generation_positions": len(self.generation_schedule.sample_ids),
            "physics_micro_steps": len(self.physics_schedule.batches),
            "physics_batches_of_seven": sizes.count(7),
            "physics_batches_of_six": sizes.count(6),
            "visible_observation_fields": list(config.visible_observation_fields),
            "lambda_state": contract.lambda_state,
            "lambda_physics": contract.lambda_physics,
            "output_dir": str(settings.output_dir),
        }


def prepare_training_inputs(
    config: SharedB0PhysicsConfig,
    baseline: str,
    *,
    use_hardware_fallback: bool = False,
    sidecar_validator: Callable[
        [Path, Path], object
    ] = validate_shared_b0_physics_sidecar,
) -> PreparedInputs:
    """验签数据后冻结两条基线共同的顺序与批边界。"""
    contract = build_baseline_contract(baseline)
    required_files = (
        config.classification_train_file,
        config.classification_validation_file,
        config.physics_sidecar_file,
        config.physics_dataset_manifest,
    )
    missing = [str(path) for path in required_files if not path.is_file()]
    if missing:
        raise SharedB0PhysicsTrainingError(f"训练输入不存在：{', '.join(missing)}")
    sidecar_validator(config.physics_sidecar_root, config.classification_train_file)
    classification = load_training_records(config.classification_train_file)
    validation = load_training_records(config.classification_validation_file)
    sidecar = _read_jsonl(config.physics_sidecar_file, "物理旁路")
    classification_ids = _unique_sample_ids(classification, "分类训练清单")
    sidecar_ids = _unique_sample_ids(sidecar, "物理旁路")
    if len(sidecar) != config.physics_records:
        raise SharedB0PhysicsTrainingError("物理旁路必须严格包含 2421 条记录")
    classification_by_id = dict(zip(classification_ids, classification, strict=True))
    sidecar_by_id = dict(zip(sidecar_ids, sidecar, strict=True))
    missing_join = sorted(set(sidecar_ids) - set(classification_ids))
    if missing_join:
        raise SharedB0PhysicsTrainingError(
            f"分类训练清单缺少物理旁路 sample_id：{missing_join[0]}"
        )
    for record in classification:
        prohibited = sorted(set(record) & PROHIBITED_CLASSIFICATION_FIELDS)
        if prohibited:
            raise SharedB0PhysicsTrainingError(
                f"分类记录包含禁止的物理字段：{', '.join(prohibited)}"
            )

    state_records = [parse_state_sidecar_record(record) for record in sidecar]
    if contract.reads_physics_coefficients:
        for record in sidecar:
            parse_physics_sidecar_record(record)
    micro_batch_size, accumulation = config.generation_batch(use_hardware_fallback)
    generation_schedule = build_generation_schedule(
        classification,
        micro_batch_size=micro_batch_size,
        gradient_accumulation_steps=accumulation,
        max_steps=config.max_steps,
        seed=config.probe.seed,
    )
    physics_schedule = build_physics_schedule(sidecar, seed=config.probe.seed)
    hashes = {
        "config": config.config_sha256,
        "classification_train_file": _file_sha256(config.classification_train_file),
        "classification_validation_file": _file_sha256(
            config.classification_validation_file
        ),
        "physics_sidecar_file": _file_sha256(config.physics_sidecar_file),
        "physics_dataset_manifest": _file_sha256(config.physics_dataset_manifest),
        "generation_order": generation_schedule.order_sha256,
        "generation_batch_boundaries": generation_schedule.batch_boundaries_sha256,
        "generation_schedule": generation_schedule.schedule_sha256,
        "physics_order": physics_schedule.order_sha256,
        "physics_batch_boundaries": physics_schedule.batch_boundaries_sha256,
        "physics_schedule": physics_schedule.schedule_sha256,
        "state_mask": state_mask_sha256(state_records),
    }
    audit = {
        "classification_record_count": len(classification),
        "sidecar_record_count": len(sidecar),
        "joined_record_count": len(sidecar_ids),
        "missing_join_count": 0,
        "state_mask_mode": config.state_mask,
        "state_mask_source": "signed_sidecar_state_mask_inputs",
        "state_mask_sha256": hashes["state_mask"],
        "physics_usage": config.physics_usage,
    }
    return PreparedInputs(
        classification_records=tuple(classification),
        validation_records=tuple(validation),
        classification_by_id=classification_by_id,
        sidecar_records=tuple(sidecar),
        sidecar_by_id=sidecar_by_id,
        generation_schedule=generation_schedule,
        physics_schedule=physics_schedule,
        state_mask_sha256=hashes["state_mask"],
        hashes=hashes,
        audit=audit,
    )


def compose_run_binding(
    base_training_binding: Mapping[str, object],
    config: SharedB0PhysicsConfig,
    prepared: PreparedInputs,
    baseline: str,
    state_head_initialization_sha256: str,
    lora_initialization_sha256: str,
    *,
    use_hardware_fallback: bool,
    output_dir: Path,
) -> dict[str, object]:
    """将普通 Qwen 绑定扩展为包含双顺序、初始化和基线身份的绑定。"""
    contract = build_baseline_contract(baseline)
    micro_batch_size, accumulation = config.generation_batch(use_hardware_fallback)
    value = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "base_training_binding": dict(base_training_binding),
        "base_training_binding_sha256": training_binding_sha256(base_training_binding),
        "config_sha256": config.config_sha256,
        "classification_train_sha256": prepared.hashes["classification_train_file"],
        "classification_validation_sha256": prepared.hashes[
            "classification_validation_file"
        ],
        "physics_sidecar_sha256": prepared.hashes["physics_sidecar_file"],
        "physics_dataset_manifest_sha256": prepared.hashes["physics_dataset_manifest"],
        "generation_order_sha256": prepared.generation_schedule.order_sha256,
        "generation_batch_boundaries_sha256": (
            prepared.generation_schedule.batch_boundaries_sha256
        ),
        "generation_schedule_sha256": prepared.generation_schedule.schedule_sha256,
        "physics_order_sha256": prepared.physics_schedule.order_sha256,
        "physics_batch_boundaries_sha256": (
            prepared.physics_schedule.batch_boundaries_sha256
        ),
        "physics_schedule_sha256": prepared.physics_schedule.schedule_sha256,
        "state_mask_sha256": prepared.state_mask_sha256,
        "state_head_initialization_sha256": state_head_initialization_sha256,
        "lora_initialization_sha256": lora_initialization_sha256,
        "visible_observation_fields_sha256": _canonical_sha256(
            list(config.visible_observation_fields)
        ),
        "trainer_code_sha256": _file_sha256(Path(__file__)),
        "baseline": contract.name,
        "lambda_state": contract.lambda_state,
        "lambda_physics": contract.lambda_physics,
        "generation_micro_batch_size": micro_batch_size,
        "generation_gradient_accumulation_steps": accumulation,
        "effective_generation_batch_size": EXPECTED_EFFECTIVE_BATCH_SIZE,
        "max_steps": config.max_steps,
        "save_steps": config.save_steps,
        "physics_records": config.physics_records,
        "physics_micro_steps": config.physics_micro_steps,
        "physics_usage": config.physics_usage,
        "output_dir": str(Path(output_dir).expanduser().resolve()),
    }
    return {**value, "binding_sha256": _canonical_sha256(value)}


def build_run_binding(
    config: SharedB0PhysicsConfig,
    prepared: PreparedInputs,
    baseline: str,
    state_head_initialization_sha256: str,
    lora_initialization_sha256: str,
    *,
    use_hardware_fallback: bool = False,
    output_dir: Path,
) -> dict[str, object]:
    settings = config.training_settings(
        baseline,
        use_hardware_fallback,
        output_dir=output_dir,
    )
    base = build_training_binding(config.probe, settings, Path(config.probe.model_id))
    return compose_run_binding(
        base,
        config,
        prepared,
        baseline,
        state_head_initialization_sha256,
        lora_initialization_sha256,
        use_hardware_fallback=use_hardware_fallback,
        output_dir=output_dir,
    )


@dataclass(frozen=True)
class TrainingProgress:
    """检查点恢复所需的优化步和两个独立微步游标。"""

    optimization_step: int = 0
    generation_micro_step: int = 0
    generation_cursor: int = 0
    physics_micro_step: int = 0
    physics_cursor: int = 0

    def to_mapping(self) -> dict[str, int]:
        return {
            "optimization_step": self.optimization_step,
            "generation_micro_step": self.generation_micro_step,
            "generation_cursor": self.generation_cursor,
            "physics_micro_step": self.physics_micro_step,
            "physics_cursor": self.physics_cursor,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> TrainingProgress:
        fields = (
            "optimization_step",
            "generation_micro_step",
            "generation_cursor",
            "physics_micro_step",
            "physics_cursor",
        )
        parsed = {}
        for field in fields:
            item = value.get(field)
            if type(item) is not int or item < 0:
                raise SharedB0PhysicsTrainingError(f"训练进度 {field} 必须是非负整数")
            parsed[field] = item
        return cls(**parsed)


def progress_for_step(
    optimization_step: int,
    generation_schedule: FrozenSchedule,
    physics_schedule: FrozenSchedule,
    gradient_accumulation_steps: int,
) -> TrainingProgress:
    if not 0 <= optimization_step <= EXPECTED_MAX_STEPS:
        raise SharedB0PhysicsTrainingError("优化步游标超出范围")
    generation_micro_step = optimization_step * gradient_accumulation_steps
    physics_micro_step = (
        optimization_step * EXPECTED_PHYSICS_MICRO_STEPS_PER_OPTIMIZATION
    )
    return TrainingProgress(
        optimization_step=optimization_step,
        generation_micro_step=generation_micro_step,
        generation_cursor=sum(
            len(batch) for batch in generation_schedule.batches[:generation_micro_step]
        ),
        physics_micro_step=physics_micro_step,
        physics_cursor=sum(
            len(batch) for batch in physics_schedule.batches[:physics_micro_step]
        ),
    )


def capture_rng_state() -> dict[str, object]:
    """保存 Python、NumPy、PyTorch 与全部 CUDA 随机数状态。"""
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
    }


def restore_rng_state(value: Mapping[str, object]) -> None:
    required = {"python", "numpy", "torch", "cuda"}
    if set(value) != required:
        raise SharedB0PhysicsTrainingError("随机数状态字段不完整")
    random.setstate(value["python"])  # type: ignore[arg-type]
    np.random.set_state(value["numpy"])  # type: ignore[arg-type]
    torch.set_rng_state(value["torch"])  # type: ignore[arg-type]
    cuda_state = value["cuda"]
    if cuda_state is not None:
        if not torch.cuda.is_available():
            raise SharedB0PhysicsTrainingError(
                "检查点包含 CUDA 随机状态，但当前 CUDA 不可用"
            )
        torch.cuda.set_rng_state_all(cuda_state)  # type: ignore[arg-type]


def _trainable_model_state(
    model: torch.nn.Module, state_head: torch.nn.Module
) -> dict[str, torch.Tensor]:
    state_head_parameter_ids = {id(parameter) for parameter in state_head.parameters()}
    result = {
        name: parameter.detach().cpu().clone()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad and id(parameter) not in state_head_parameter_ids
    }
    if not result:
        raise SharedB0PhysicsTrainingError("模型没有可保存的 LoRA 可训练参数")
    return result


def _load_trainable_model_state(
    model: torch.nn.Module,
    state_head: torch.nn.Module,
    value: Mapping[str, torch.Tensor],
) -> None:
    state_head_parameter_ids = {id(parameter) for parameter in state_head.parameters()}
    parameters = {
        name: parameter
        for name, parameter in model.named_parameters()
        if parameter.requires_grad and id(parameter) not in state_head_parameter_ids
    }
    if set(parameters) != set(value):
        missing = sorted(set(parameters) - set(value))
        unexpected = sorted(set(value) - set(parameters))
        raise SharedB0PhysicsTrainingError(
            "LoRA 参数树不一致："
            f"缺少={','.join(missing)}；多余={','.join(unexpected)}"
        )
    with torch.no_grad():
        for name, parameter in parameters.items():
            stored = value[name]
            if tuple(stored.shape) != tuple(parameter.shape):
                raise SharedB0PhysicsTrainingError(f"LoRA 参数形状不一致：{name}")
            parameter.copy_(stored.to(device=parameter.device, dtype=parameter.dtype))


def _save_adapter(model: torch.nn.Module, path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)
    save_pretrained = getattr(model, "save_pretrained", None)
    if callable(save_pretrained):
        save_pretrained(str(path))
    else:
        torch.save(model.state_dict(), path / "adapter_model.pt")
    if not any(item.is_file() for item in path.rglob("*")):
        raise SharedB0PhysicsTrainingError("LoRA 适配器目录为空")


def save_training_checkpoint(
    checkpoint: Path,
    *,
    model: torch.nn.Module,
    state_head: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: object,
    gradient_scaler: object | None,
    progress: TrainingProgress,
    binding: Mapping[str, object],
    metrics: Sequence[Mapping[str, object]],
) -> Path:
    """原子保存 LoRA、状态头、优化状态、双游标、指标和全部随机状态。"""
    checkpoint = Path(checkpoint)
    if checkpoint.exists():
        raise SharedB0PhysicsTrainingError(f"检查点已存在，拒绝覆盖：{checkpoint}")
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    partial = checkpoint.with_name(f".{checkpoint.name}.{uuid.uuid4().hex}.partial")
    partial.mkdir(parents=False, exist_ok=False)
    _save_adapter(model, partial / "adapter")
    trainable_state = _trainable_model_state(model, state_head)
    torch.save(trainable_state, partial / "lora_trainable.pt")
    torch.save(state_head.state_dict(), partial / "state_head.pt")
    torch.save(optimizer.state_dict(), partial / "optimizer.pt")
    state_dict = getattr(scheduler, "state_dict", None)
    if not callable(state_dict):
        raise SharedB0PhysicsTrainingError("调度器不支持 state_dict")
    torch.save(state_dict(), partial / "scheduler.pt")
    scaler_state = None
    if gradient_scaler is not None:
        scaler_state_dict = getattr(gradient_scaler, "state_dict", None)
        if not callable(scaler_state_dict):
            raise SharedB0PhysicsTrainingError("梯度缩放器不支持 state_dict")
        scaler_state = scaler_state_dict()
    torch.save(scaler_state, partial / "gradient_scaler.pt")
    torch.save(capture_rng_state(), partial / "rng_state.pt")
    metrics_value = [dict(metric) for metric in metrics]
    _atomic_write_json(partial / "metrics.json", metrics_value)
    binding_sha256 = str(binding.get("binding_sha256", ""))
    if binding_sha256 != _canonical_sha256(
        {key: value for key, value in binding.items() if key != "binding_sha256"}
    ):
        raise SharedB0PhysicsTrainingError("运行绑定自身哈希不一致")
    trainer_state = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        **progress.to_mapping(),
        "metrics_count": len(metrics_value),
        "metrics_sha256": _canonical_sha256(metrics_value),
    }
    checkpoint_binding = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "binding": dict(binding),
        "binding_sha256": binding_sha256,
        "baseline": binding.get("baseline"),
        "lambda_state": binding.get("lambda_state"),
        "lambda_physics": binding.get("lambda_physics"),
        "progress": progress.to_mapping(),
    }
    _atomic_write_json(partial / "trainer_state.json", trainer_state)
    _atomic_write_json(partial / "checkpoint_binding.json", checkpoint_binding)
    partial.replace(checkpoint)
    return checkpoint


def _validate_checkpoint_files(checkpoint: Path) -> None:
    if not checkpoint.is_dir():
        raise SharedB0PhysicsTrainingError(f"检查点不是目录：{checkpoint}")
    missing = sorted(
        filename
        for filename in _CHECKPOINT_REQUIRED_FILES
        if not (checkpoint / filename).is_file()
    )
    if missing:
        raise SharedB0PhysicsTrainingError(f"检查点缺少文件：{', '.join(missing)}")
    adapter = checkpoint / "adapter"
    if not adapter.is_dir() or not any(item.is_file() for item in adapter.rglob("*")):
        raise SharedB0PhysicsTrainingError("检查点缺少完整 LoRA 适配器")


def load_training_checkpoint(
    checkpoint: Path,
    *,
    model: torch.nn.Module,
    state_head: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: object,
    gradient_scaler: object | None,
    expected_binding: Mapping[str, object],
) -> tuple[TrainingProgress, list[dict[str, object]]]:
    """在修改参数前拒绝任一绑定不一致，再完整恢复训练状态。"""
    checkpoint = Path(checkpoint)
    _validate_checkpoint_files(checkpoint)
    checkpoint_binding = _read_json(
        checkpoint / "checkpoint_binding.json", "检查点绑定"
    )
    stored_binding = _mapping(checkpoint_binding.get("binding"), "检查点绑定.binding")
    if dict(stored_binding) != dict(expected_binding):
        fields = sorted(
            key
            for key in set(stored_binding) | set(expected_binding)
            if stored_binding.get(key) != expected_binding.get(key)
        )
        raise SharedB0PhysicsTrainingError(
            f"检查点绑定不一致，字段：{', '.join(fields)}"
        )
    trainer_state = _read_json(checkpoint / "trainer_state.json", "训练器状态")
    if trainer_state.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise SharedB0PhysicsTrainingError("训练器状态 schema_version 不匹配")
    progress = TrainingProgress.from_mapping(trainer_state)
    checkpoint_progress = TrainingProgress.from_mapping(
        _mapping(checkpoint_binding.get("progress"), "检查点进度")
    )
    if progress != checkpoint_progress:
        raise SharedB0PhysicsTrainingError("检查点双游标自报值不一致")
    metrics_value = json.loads(
        (checkpoint / "metrics.json").read_text(encoding="utf-8")
    )
    if not isinstance(metrics_value, list) or any(
        not isinstance(value, dict) for value in metrics_value
    ):
        raise SharedB0PhysicsTrainingError("检查点指标必须是对象列表")
    if trainer_state.get("metrics_count") != len(metrics_value) or trainer_state.get(
        "metrics_sha256"
    ) != _canonical_sha256(metrics_value):
        raise SharedB0PhysicsTrainingError("检查点指标计数或哈希不一致")

    trainable_state = torch.load(
        checkpoint / "lora_trainable.pt", map_location="cpu", weights_only=True
    )
    if not isinstance(trainable_state, Mapping):
        raise SharedB0PhysicsTrainingError("LoRA 参数检查点不是映射")
    state_head_state = torch.load(
        checkpoint / "state_head.pt", map_location="cpu", weights_only=True
    )
    optimizer_state = torch.load(
        checkpoint / "optimizer.pt", map_location="cpu", weights_only=False
    )
    scheduler_state = torch.load(
        checkpoint / "scheduler.pt", map_location="cpu", weights_only=False
    )
    scaler_state = torch.load(
        checkpoint / "gradient_scaler.pt", map_location="cpu", weights_only=False
    )
    rng_state = torch.load(
        checkpoint / "rng_state.pt", map_location="cpu", weights_only=False
    )
    if not isinstance(rng_state, Mapping):
        raise SharedB0PhysicsTrainingError("随机数检查点不是映射")

    _load_trainable_model_state(model, state_head, trainable_state)
    state_head.load_state_dict(state_head_state, strict=True)
    optimizer.load_state_dict(optimizer_state)
    load_scheduler = getattr(scheduler, "load_state_dict", None)
    if not callable(load_scheduler):
        raise SharedB0PhysicsTrainingError("调度器不支持 load_state_dict")
    load_scheduler(scheduler_state)
    if gradient_scaler is None:
        if scaler_state is not None:
            raise SharedB0PhysicsTrainingError("当前无梯度缩放器，但检查点包含缩放状态")
    else:
        load_scaler = getattr(gradient_scaler, "load_state_dict", None)
        if not callable(load_scaler):
            raise SharedB0PhysicsTrainingError("梯度缩放器不支持 load_state_dict")
        load_scaler(scaler_state)
    restore_rng_state(rng_state)
    return progress, [dict(value) for value in metrics_value]


@dataclass(frozen=True)
class RunLayout:
    """单条基线运行的固定制品路径。"""

    output_dir: Path
    resolved_config: Path
    environment: Path
    capabilities: Path
    training_binding: Path
    run_state: Path
    generation_order: Path
    physics_schedule: Path
    state_mask_audit: Path
    step_metrics: Path
    checkpoints: Path
    final_adapter: Path
    final_state_head: Path
    train_summary: Path
    artifact_manifest: Path
    console_log: Path


def build_run_layout(output_dir: Path) -> RunLayout:
    output_dir = Path(output_dir)
    return RunLayout(
        output_dir=output_dir,
        resolved_config=output_dir / "resolved_config.yaml",
        environment=output_dir / "environment.json",
        capabilities=output_dir / "capabilities.json",
        training_binding=output_dir / "training_binding.json",
        run_state=output_dir / "run_state.json",
        generation_order=output_dir / "generation_order.json",
        physics_schedule=output_dir / "physics_schedule.json",
        state_mask_audit=output_dir / "state_mask_audit.json",
        step_metrics=output_dir / "step_metrics.jsonl",
        checkpoints=output_dir / "checkpoints",
        final_adapter=output_dir / "adapter",
        final_state_head=output_dir / "state_head",
        train_summary=output_dir / "train_summary.json",
        artifact_manifest=output_dir / "artifact_manifest.json",
        console_log=output_dir / "console.log",
    )


def _atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as target:
            target.write(text)
            target.flush()
            os.fsync(target.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def _environment_manifest() -> dict[str, object]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": (
            torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        ),
        "cpu": platform.processor() or platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "packages": {
            name: _package_version(name)
            for name in (
                "accelerate",
                "bitsandbytes",
                "datasets",
                "peft",
                "swanlab",
                "transformers",
                "trl",
            )
        },
    }


def _capabilities_manifest(
    config: SharedB0PhysicsConfig,
    use_hardware_fallback: bool,
) -> dict[str, object]:
    micro_batch_size, accumulation = config.generation_batch(use_hardware_fallback)
    return {
        "device_policy": "cuda_bf16_qlora",
        "cuda_available": torch.cuda.is_available(),
        "bf16_supported": (
            torch.cuda.is_available() and torch.cuda.is_bf16_supported()
        ),
        "generation_micro_batch_size": micro_batch_size,
        "generation_gradient_accumulation_steps": accumulation,
        "effective_generation_batch_size": micro_batch_size * accumulation,
        "hardware_fallback": use_hardware_fallback,
        "precision": "bfloat16",
        "quantization": "NF4",
    }


def _new_run_state(binding_sha256: str) -> dict[str, object]:
    timestamp = _utc_now()
    return {
        "schema_version": RUN_STATE_SCHEMA_VERSION,
        "run_id": uuid.uuid4().hex,
        "status": "prepared",
        "binding_sha256": binding_sha256,
        **TrainingProgress().to_mapping(),
        "latest_checkpoint": None,
        "started_at": timestamp,
        "updated_at": timestamp,
        "failure": None,
    }


def _update_run_state(
    layout: RunLayout,
    state: Mapping[str, object],
    *,
    status: str,
    progress: TrainingProgress,
    latest_checkpoint: Path | None = None,
    failure: str | None = None,
) -> dict[str, object]:
    if status not in {"prepared", "running", "interrupted", "failed", "completed"}:
        raise SharedB0PhysicsTrainingError(f"非法运行状态：{status}")
    value = {
        **dict(state),
        "status": status,
        **progress.to_mapping(),
        "latest_checkpoint": (
            str(latest_checkpoint)
            if latest_checkpoint is not None
            else state.get("latest_checkpoint")
        ),
        "updated_at": _utc_now(),
        "failure": failure,
    }
    _atomic_write_json(layout.run_state, value)
    return value


def _checkpoint_step(path: Path) -> int | None:
    prefix = "checkpoint-"
    if not path.is_dir() or not path.name.startswith(prefix):
        return None
    suffix = path.name[len(prefix) :]
    if len(suffix) != 6 or not suffix.isdigit():
        return None
    return int(suffix)


def _checkpoint_candidates(layout: RunLayout) -> list[tuple[int, Path]]:
    if not layout.checkpoints.is_dir():
        return []
    candidates = []
    for path in layout.checkpoints.iterdir():
        step = _checkpoint_step(path)
        if step is not None:
            candidates.append((step, path))
    return sorted(candidates, reverse=True)


def resolve_training_checkpoint(
    layout: RunLayout,
    resume: str,
    expected_binding: Mapping[str, object],
) -> Path | None:
    """选择同一运行目录中的最新完整检查点，或严格验证显式路径。"""
    if resume not in {"auto", "never"}:
        candidate = Path(resume).expanduser().resolve()
        expected_parent = layout.checkpoints.expanduser().resolve()
        if candidate.parent != expected_parent:
            raise SharedB0PhysicsTrainingError(
                "显式检查点必须位于当前运行的 checkpoints 目录"
            )
        _validate_checkpoint_files(candidate)
        binding_value = _read_json(candidate / "checkpoint_binding.json", "检查点绑定")
        if (
            _mapping(binding_value.get("binding"), "检查点绑定.binding")
            != expected_binding
        ):
            raise SharedB0PhysicsTrainingError("显式检查点绑定不一致")
        return candidate
    if resume == "never":
        return None
    for _, candidate in _checkpoint_candidates(layout):
        try:
            _validate_checkpoint_files(candidate)
            binding_value = _read_json(
                candidate / "checkpoint_binding.json", "检查点绑定"
            )
            if dict(
                _mapping(binding_value.get("binding"), "检查点绑定.binding")
            ) == dict(expected_binding):
                return candidate
        except SharedB0PhysicsTrainingError:
            continue
    return None


@dataclass(frozen=True)
class PreparedRun:
    """新运行或已通过绑定门禁的恢复运行。"""

    layout: RunLayout
    run_state: Mapping[str, object]
    resume_checkpoint: Path | None


def prepare_training_run(
    config: SharedB0PhysicsConfig,
    prepared_inputs: PreparedInputs,
    binding: Mapping[str, object],
    baseline: str,
    resume: str,
    *,
    use_hardware_fallback: bool,
    output_dir: Path,
) -> PreparedRun:
    """先拒绝完成运行和绑定漂移，再创建或恢复制品目录。"""
    layout = build_run_layout(Path(output_dir).expanduser().resolve())
    binding_sha256 = str(binding.get("binding_sha256", ""))
    binding_exists = layout.training_binding.is_file()
    state_exists = layout.run_state.is_file()
    if not binding_exists and not state_exists:
        if resume not in {"auto", "never"}:
            raise SharedB0PhysicsTrainingError(
                "新运行不能从当前运行目录外的显式检查点启动"
            )
        if layout.output_dir.exists():
            if not layout.output_dir.is_dir():
                raise SharedB0PhysicsTrainingError("训练输出路径不是目录")
            existing = sorted(item.name for item in layout.output_dir.iterdir())
            if existing:
                raise SharedB0PhysicsTrainingError(
                    f"输出目录非空且缺少恢复元数据：{', '.join(existing)}"
                )
        layout.output_dir.mkdir(parents=True, exist_ok=True)
        layout.checkpoints.mkdir(parents=True, exist_ok=False)
        resolved = {
            **dict(config.raw),
            "resolved": {
                "baseline": baseline,
                "lambda_state": binding["lambda_state"],
                "lambda_physics": binding["lambda_physics"],
                "hardware_fallback": use_hardware_fallback,
                "binding_sha256": binding_sha256,
                "output_dir": str(layout.output_dir),
            },
        }
        _atomic_write_text(
            layout.resolved_config,
            yaml.safe_dump(resolved, allow_unicode=True, sort_keys=False),
        )
        _atomic_write_json(layout.environment, _environment_manifest())
        _atomic_write_json(
            layout.capabilities,
            _capabilities_manifest(config, use_hardware_fallback),
        )
        _atomic_write_json(layout.training_binding, binding)
        _atomic_write_json(
            layout.generation_order,
            prepared_inputs.generation_schedule.to_mapping(),
        )
        _atomic_write_json(
            layout.physics_schedule,
            prepared_inputs.physics_schedule.to_mapping(),
        )
        _atomic_write_json(layout.state_mask_audit, prepared_inputs.audit)
        run_state = _new_run_state(binding_sha256)
        _atomic_write_json(layout.run_state, run_state)
        _atomic_write_jsonl(layout.step_metrics, [])
        return PreparedRun(layout, run_state, None)

    if not binding_exists or not state_exists:
        missing = (
            layout.training_binding.name
            if not binding_exists
            else layout.run_state.name
        )
        raise SharedB0PhysicsTrainingError(f"已有运行缺少 {missing}，拒绝覆盖或恢复")
    if resume == "never":
        raise SharedB0PhysicsTrainingError("输出目录已存在且 resume=never，拒绝覆盖")
    stored_binding = _read_json(layout.training_binding, "训练绑定")
    if stored_binding != dict(binding):
        fields = sorted(
            key
            for key in set(stored_binding) | set(binding)
            if stored_binding.get(key) != binding.get(key)
        )
        raise SharedB0PhysicsTrainingError(f"训练绑定不一致，字段：{', '.join(fields)}")
    run_state = _read_json(layout.run_state, "运行状态")
    if run_state.get("schema_version") != RUN_STATE_SCHEMA_VERSION:
        raise SharedB0PhysicsTrainingError("运行状态 schema_version 不匹配")
    if run_state.get("binding_sha256") != binding_sha256:
        raise SharedB0PhysicsTrainingError("运行状态绑定哈希不一致")
    if run_state.get("status") == "completed":
        raise SharedB0PhysicsTrainingError("运行已经完成，拒绝覆盖")
    checkpoint = resolve_training_checkpoint(layout, resume, binding)
    if checkpoint is None:
        raise SharedB0PhysicsTrainingError("已有运行没有绑定一致的完整检查点")
    return PreparedRun(layout, run_state, checkpoint)


@dataclass
class TrainingRuntime:
    """由任务 02 公共构建接口创建的真实 Qwen 训练对象。"""

    trainer: Any
    model: torch.nn.Module
    tokenizer: Any
    state_head: ContinuousQueueStateHead
    state_head_initialization_sha256: str
    lora_initialization_sha256: str
    optimizer: torch.optim.Optimizer
    scheduler: Any
    gradient_scaler: Any | None
    device: torch.device
    trainable_parameters: tuple[torch.nn.Parameter, ...]


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _model_device(model: torch.nn.Module) -> torch.device:
    for parameter in model.parameters():
        if parameter.device.type != "meta":
            return parameter.device
    raise SharedB0PhysicsTrainingError("模型没有可用设备参数")


def build_training_runtime(
    config: SharedB0PhysicsConfig,
    prepared: PreparedInputs,
    baseline: str,
    *,
    use_hardware_fallback: bool,
    output_dir: Path,
) -> TrainingRuntime:
    """复用任务 02 的模型、LoRA、聊天数据集、训练器、优化器和调度器路径。"""
    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝启动共享 B0 大模型训练")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("当前 GPU 不支持 BF16")
    settings = config.training_settings(
        baseline,
        use_hardware_fallback,
        output_dir=output_dir,
    )
    _seed_everything(config.probe.seed)
    model_value, tokenizer = build_qwen_model_and_tokenizer(
        config.probe, settings, torch
    )
    scheduled_records = [
        prepared.classification_by_id[sample_id]
        for sample_id in prepared.generation_schedule.sample_ids
    ]
    train_dataset = build_chat_dataset(scheduled_records, tokenizer)
    validation_dataset = build_chat_dataset(prepared.validation_records, tokenizer)
    trainer = build_sft_trainer(
        config.probe,
        settings,
        model=model_value,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        validation_dataset=validation_dataset,
        tracking_enabled=False,
        callbacks=[],
    )
    model_candidate = getattr(trainer, "model", None)
    if not isinstance(model_candidate, torch.nn.Module):
        raise SharedB0PhysicsTrainingError("普通 SFTTrainer 没有返回 PyTorch 模型")
    model = cast(torch.nn.Module, model_candidate)
    hidden_size = int(getattr(model.config, "hidden_size", 0))
    state_head, initialization_sha256 = initialize_state_head(
        hidden_size,
        config.probe.seed,
    )
    device = _model_device(model)
    state_head = state_head.to(device=device, dtype=torch.bfloat16)
    if hasattr(model, "_shared_b0_state_head"):
        raise SharedB0PhysicsTrainingError("模型已包含共享 B0 状态头")
    model.add_module("_shared_b0_state_head", state_head)
    lora_initialization_sha256 = trainable_model_parameter_sha256(model, state_head)
    create_optimizer_and_scheduler = getattr(
        trainer, "create_optimizer_and_scheduler", None
    )
    if not callable(create_optimizer_and_scheduler):
        raise SharedB0PhysicsTrainingError("普通 SFTTrainer 缺少优化器调度器构建接口")
    create_optimizer_and_scheduler(num_training_steps=config.max_steps)
    optimizer_candidate = getattr(trainer, "optimizer", None)
    scheduler = getattr(trainer, "lr_scheduler", None)
    if not isinstance(optimizer_candidate, torch.optim.Optimizer) or scheduler is None:
        raise SharedB0PhysicsTrainingError("普通 SFTTrainer 未创建完整优化状态")
    optimizer = cast(torch.optim.Optimizer, optimizer_candidate)
    state_head_parameter_ids = {id(parameter) for parameter in state_head.parameters()}
    optimizer_parameter_ids = {
        id(parameter)
        for group in optimizer.param_groups
        for parameter in group["params"]
    }
    if not state_head_parameter_ids.issubset(optimizer_parameter_ids):
        raise SharedB0PhysicsTrainingError("状态头参数没有进入公共优化器")
    trainable = tuple(
        parameter for parameter in model.parameters() if parameter.requires_grad
    )
    if not trainable or not any(
        "lora_" in name for name, _ in model.named_parameters()
    ):
        raise SharedB0PhysicsTrainingError("公共训练器没有挂载可训练 LoRA")
    accelerator = getattr(trainer, "accelerator", None)
    gradient_scaler = getattr(accelerator, "scaler", None)
    model.config.use_cache = False
    model.train()
    state_head.train()
    return TrainingRuntime(
        trainer=trainer,
        model=model,
        tokenizer=tokenizer,
        state_head=state_head,
        state_head_initialization_sha256=initialization_sha256,
        lora_initialization_sha256=lora_initialization_sha256,
        optimizer=optimizer,
        scheduler=scheduler,
        gradient_scaler=gradient_scaler,
        device=device,
        trainable_parameters=trainable,
    )


def _generation_batch(
    runtime: TrainingRuntime,
    prepared: PreparedInputs,
    micro_step: int,
) -> dict[str, torch.Tensor]:
    dataset = getattr(runtime.trainer, "train_dataset", None)
    collator = getattr(runtime.trainer, "data_collator", None)
    if dataset is None or not callable(collator):
        raise SharedB0PhysicsTrainingError("公共训练器缺少训练数据集或整理器")
    start = sum(
        len(batch) for batch in prepared.generation_schedule.batches[:micro_step]
    )
    size = len(prepared.generation_schedule.batches[micro_step])
    features = [dataset[index] for index in range(start, start + size)]
    expected_ids = list(prepared.generation_schedule.batches[micro_step])
    actual_ids = [str(feature.get("sample_id", "")) for feature in features]
    if all(actual_ids) and actual_ids != expected_ids:
        raise SharedB0PhysicsTrainingError("TRL 数据集顺序与冻结生成批边界不一致")
    batch_value = collator(features)
    if not isinstance(batch_value, Mapping):
        raise SharedB0PhysicsTrainingError("普通训练整理器没有返回映射")
    batch = {
        key: value.to(runtime.device)
        for key, value in batch_value.items()
        if isinstance(value, torch.Tensor) and key != "sample_id"
    }
    if not {"input_ids", "attention_mask", "labels"}.issubset(batch):
        raise SharedB0PhysicsTrainingError("普通生成微批缺少输入、注意力或标签")
    return batch


def _state_predictions(
    runtime: TrainingRuntime,
    classification_records: Sequence[Mapping[str, object]],
    max_length: int,
) -> torch.Tensor:
    prompts = build_state_prompt_texts(classification_records, runtime.tokenizer)
    for prompt in prompts:
        leaked = sorted(
            field for field in PROHIBITED_CLASSIFICATION_FIELDS if field in prompt
        )
        if leaked:
            raise SharedB0PhysicsTrainingError(
                f"普通 Qwen 提示词包含物理旁路字段：{', '.join(leaked)}"
            )
    encoded = runtime.tokenizer(
        prompts,
        padding=True,
        truncation=True,
        max_length=max_length,
        add_special_tokens=False,
        return_tensors="pt",
    )
    input_ids = encoded["input_ids"].to(runtime.device)
    attention_mask = encoded["attention_mask"].to(runtime.device)
    outputs = runtime.model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        output_hidden_states=True,
        return_dict=True,
    )
    hidden_states = getattr(outputs, "hidden_states", None)
    if not hidden_states:
        raise SharedB0PhysicsTrainingError("普通 Qwen 前向没有返回隐藏状态")
    hidden = select_last_token_hidden(hidden_states[-1], attention_mask)
    return runtime.state_head(hidden)


def _backward(runtime: TrainingRuntime, loss: torch.Tensor) -> None:
    if runtime.gradient_scaler is None:
        loss.backward()
    else:
        runtime.gradient_scaler.scale(loss).backward()


def _optimizer_step(runtime: TrainingRuntime, max_grad_norm: float) -> float:
    if runtime.gradient_scaler is not None:
        runtime.gradient_scaler.unscale_(runtime.optimizer)
    gradient_norm = finite_gradient_norm(runtime.trainable_parameters)
    clipped = torch.nn.utils.clip_grad_norm_(
        runtime.trainable_parameters, max_grad_norm
    )
    if not bool(torch.isfinite(torch.as_tensor(clipped)).all().item()):
        raise FloatingPointError("裁剪后的梯度范数不是有限数")
    if runtime.gradient_scaler is None:
        runtime.optimizer.step()
    else:
        runtime.gradient_scaler.step(runtime.optimizer)
        runtime.gradient_scaler.update()
    step_scheduler = getattr(runtime.scheduler, "step", None)
    if not callable(step_scheduler):
        raise SharedB0PhysicsTrainingError("调度器不支持 step")
    step_scheduler()
    return gradient_norm


def _current_learning_rate(optimizer: torch.optim.Optimizer) -> float:
    if not optimizer.param_groups:
        raise SharedB0PhysicsTrainingError("优化器没有参数组")
    return float(optimizer.param_groups[0]["lr"])


def _checkpoint_path(layout: RunLayout, step: int) -> Path:
    return layout.checkpoints / f"checkpoint-{step:06d}"


def _artifact_entry(path: Path, root: Path) -> dict[str, object]:
    return {
        "path": str(path.relative_to(root)),
        "bytes": path.stat().st_size,
        "sha256": _file_sha256(path),
    }


def _write_artifact_manifest(
    layout: RunLayout,
    binding: Mapping[str, object],
    *,
    status: str,
) -> None:
    """在控制台和 SwanLab 日志关闭后冻结完整制品清单。"""
    files = sorted(
        path
        for path in layout.output_dir.rglob("*")
        if path.is_file() and path != layout.artifact_manifest
    )
    manifest = {
        "schema_version": "flow_probe_shared_b0_physics_artifact_manifest_v1",
        "status": status,
        "binding_sha256": binding["binding_sha256"],
        "artifacts": [_artifact_entry(path, layout.output_dir) for path in files],
    }
    _atomic_write_json(layout.artifact_manifest, manifest)


def _write_final_artifacts(
    runtime: TrainingRuntime,
    prepared_run: PreparedRun,
    config: SharedB0PhysicsConfig,
    baseline: str,
    progress: TrainingProgress,
    metrics: Sequence[Mapping[str, object]],
    binding: Mapping[str, object],
    run_state: Mapping[str, object],
    latest_checkpoint: Path | None,
) -> dict[str, object]:
    layout = prepared_run.layout
    if layout.final_adapter.exists() or layout.final_state_head.exists():
        raise SharedB0PhysicsTrainingError("最终模型制品已存在，拒绝覆盖")
    _save_adapter(runtime.model, layout.final_adapter)
    save_tokenizer = getattr(runtime.tokenizer, "save_pretrained", None)
    if callable(save_tokenizer):
        save_tokenizer(str(layout.final_adapter))
    layout.final_state_head.mkdir(parents=True, exist_ok=False)
    torch.save(
        runtime.state_head.state_dict(), layout.final_state_head / "state_head.pt"
    )
    _atomic_write_json(
        layout.final_state_head / "metadata.json",
        {
            "schema_version": BINDING_SCHEMA_VERSION,
            "initialization_sha256": binding["state_head_initialization_sha256"],
            "final_parameter_tree_sha256": parameter_tree_sha256(runtime.state_head),
            "binding_sha256": binding["binding_sha256"],
        },
    )
    summary = {
        "schema_version": "flow_probe_shared_b0_physics_train_summary_v1",
        "status": "completed",
        "baseline": baseline,
        "seed": config.probe.seed,
        "max_steps": config.max_steps,
        **progress.to_mapping(),
        "generation_records": progress.generation_cursor,
        "physics_records": progress.physics_cursor,
        "metrics_count": len(metrics),
        "binding_sha256": binding["binding_sha256"],
        "lambda_state": binding["lambda_state"],
        "lambda_physics": binding["lambda_physics"],
        "nonfinite_count": sum(
            _integer(metric, "nonfinite_count", "步级指标") for metric in metrics
        ),
    }
    _atomic_write_json(layout.train_summary, summary)
    _update_run_state(
        layout,
        run_state,
        status="completed",
        progress=progress,
        latest_checkpoint=latest_checkpoint,
    )
    return summary


def _execute_training_loop(
    runtime: TrainingRuntime,
    config: SharedB0PhysicsConfig,
    prepared_inputs: PreparedInputs,
    prepared_run: PreparedRun,
    binding: Mapping[str, object],
    baseline: str,
    *,
    use_hardware_fallback: bool,
    metric_logger: MetricLogger | None,
    stop_after_optimization_step: int | None,
) -> dict[str, object]:
    settings = config.training_settings(
        baseline,
        use_hardware_fallback,
        output_dir=prepared_run.layout.output_dir,
    )
    progress = TrainingProgress()
    metrics: list[dict[str, object]] = []
    run_state = dict(prepared_run.run_state)
    if prepared_run.resume_checkpoint is not None:
        progress, metrics = load_training_checkpoint(
            prepared_run.resume_checkpoint,
            model=runtime.model,
            state_head=runtime.state_head,
            optimizer=runtime.optimizer,
            scheduler=runtime.scheduler,
            gradient_scaler=runtime.gradient_scaler,
            expected_binding=binding,
        )
        expected_progress = progress_for_step(
            progress.optimization_step,
            prepared_inputs.generation_schedule,
            prepared_inputs.physics_schedule,
            settings.gradient_accumulation_steps,
        )
        if progress != expected_progress:
            raise SharedB0PhysicsTrainingError("检查点双游标与冻结批边界不一致")
        _atomic_write_jsonl(prepared_run.layout.step_metrics, metrics)
        run_state = _update_run_state(
            prepared_run.layout,
            run_state,
            status="prepared",
            progress=progress,
            latest_checkpoint=prepared_run.resume_checkpoint,
        )
    target_step = config.max_steps
    if stop_after_optimization_step is not None:
        if (
            not progress.optimization_step
            < stop_after_optimization_step
            <= config.max_steps
        ):
            raise SharedB0PhysicsTrainingError("停止步必须大于恢复步且不超过 200")
        target_step = stop_after_optimization_step
    run_state = _update_run_state(
        prepared_run.layout,
        run_state,
        status="running",
        progress=progress,
    )
    latest_checkpoint = prepared_run.resume_checkpoint
    try:
        for step in range(progress.optimization_step + 1, target_step + 1):
            runtime.optimizer.zero_grad(set_to_none=True)
            generation_loss_value = 0.0
            state_loss_value = 0.0
            physics_loss_value = 0.0
            valid_state_elements = 0
            physics_coefficients_accessed = False

            generation_start = (step - 1) * settings.gradient_accumulation_steps
            for offset in range(settings.gradient_accumulation_steps):
                micro_step = generation_start + offset
                batch = _generation_batch(runtime, prepared_inputs, micro_step)
                output = runtime.model(**batch, return_dict=True)
                generation_loss = output.loss.float()
                ensure_finite_losses(generation=generation_loss)
                generation_loss_value += float(generation_loss.detach().item())
                _backward(
                    runtime,
                    generation_loss / settings.gradient_accumulation_steps,
                )
            generation_loss_value /= settings.gradient_accumulation_steps

            physics_start = (step - 1) * EXPECTED_PHYSICS_MICRO_STEPS_PER_OPTIMIZATION
            for offset in range(EXPECTED_PHYSICS_MICRO_STEPS_PER_OPTIMIZATION):
                micro_step = physics_start + offset
                sample_ids = prepared_inputs.physics_schedule.batches[micro_step]
                raw_sidecar = [
                    prepared_inputs.sidecar_by_id[value] for value in sample_ids
                ]
                classification = [
                    prepared_inputs.classification_by_id[value] for value in sample_ids
                ]
                predicted = _state_predictions(
                    runtime,
                    classification,
                    config.probe.max_input_length,
                )
                tensors = build_auxiliary_tensor_batch(
                    raw_sidecar,
                    baseline,
                    runtime.device,
                )
                auxiliary = compute_auxiliary_loss(predicted, tensors, baseline)
                ensure_finite_losses(
                    state=auxiliary.state,
                    physics=auxiliary.physics,
                    auxiliary=auxiliary.total,
                )
                weight = physics_batch_weight(len(sample_ids))
                scaled = (
                    weight
                    * auxiliary.total
                    / EXPECTED_PHYSICS_MICRO_STEPS_PER_OPTIMIZATION
                )
                _backward(runtime, scaled)
                state_loss_value += (
                    weight
                    * float(auxiliary.state.detach().item())
                    / EXPECTED_PHYSICS_MICRO_STEPS_PER_OPTIMIZATION
                )
                if auxiliary.physics is not None:
                    physics_loss_value += (
                        weight
                        * float(auxiliary.physics.detach().item())
                        / EXPECTED_PHYSICS_MICRO_STEPS_PER_OPTIMIZATION
                    )
                valid_state_elements += auxiliary.valid_state_elements
                physics_coefficients_accessed = (
                    physics_coefficients_accessed
                    or auxiliary.physics_coefficients_accessed
                )

            gradient_norm = _optimizer_step(runtime, config.max_grad_norm)
            progress = progress_for_step(
                step,
                prepared_inputs.generation_schedule,
                prepared_inputs.physics_schedule,
                settings.gradient_accumulation_steps,
            )
            contract = build_baseline_contract(baseline)
            metric = {
                "optimization_step": step,
                "generation_micro_step": progress.generation_micro_step,
                "physics_micro_step": progress.physics_micro_step,
                "generation_cursor": progress.generation_cursor,
                "physics_cursor": progress.physics_cursor,
                "generation_loss": generation_loss_value,
                "state_loss": state_loss_value,
                "physics_loss": physics_loss_value,
                "total_loss": generation_loss_value
                + contract.lambda_state * state_loss_value
                + contract.lambda_physics * physics_loss_value,
                "valid_state_elements": valid_state_elements,
                "gradient_norm": gradient_norm,
                "learning_rate": _current_learning_rate(runtime.optimizer),
                "physics_coefficients_accessed": physics_coefficients_accessed,
                "nonfinite_count": 0,
            }
            metrics.append(metric)
            _atomic_write_jsonl(prepared_run.layout.step_metrics, metrics)
            if metric_logger is not None:
                metric_logger.log(
                    {
                        key: float(value)
                        for key, value in metric.items()
                        if isinstance(value, (int, float, bool))
                    },
                    step,
                )
            print(json.dumps(metric, ensure_ascii=False, sort_keys=True))
            run_state = _update_run_state(
                prepared_run.layout,
                run_state,
                status="running",
                progress=progress,
                latest_checkpoint=latest_checkpoint,
            )
            should_save = step % config.save_steps == 0 or step == target_step
            if should_save:
                latest_checkpoint = save_training_checkpoint(
                    _checkpoint_path(prepared_run.layout, step),
                    model=runtime.model,
                    state_head=runtime.state_head,
                    optimizer=runtime.optimizer,
                    scheduler=runtime.scheduler,
                    gradient_scaler=runtime.gradient_scaler,
                    progress=progress,
                    binding=binding,
                    metrics=metrics,
                )
                run_state = _update_run_state(
                    prepared_run.layout,
                    run_state,
                    status="running",
                    progress=progress,
                    latest_checkpoint=latest_checkpoint,
                )
    except KeyboardInterrupt as error:
        _update_run_state(
            prepared_run.layout,
            run_state,
            status="interrupted",
            progress=progress,
            latest_checkpoint=latest_checkpoint,
            failure=f"{type(error).__name__}: {error}",
        )
        raise
    except Exception as error:
        _update_run_state(
            prepared_run.layout,
            run_state,
            status="failed",
            progress=progress,
            latest_checkpoint=latest_checkpoint,
            failure=f"{type(error).__name__}: {error}",
        )
        raise

    if target_step != config.max_steps:
        _update_run_state(
            prepared_run.layout,
            run_state,
            status="interrupted",
            progress=progress,
            latest_checkpoint=latest_checkpoint,
            failure="受控短运行在目标步停止",
        )
        return {
            "status": "interrupted",
            "baseline": baseline,
            **progress.to_mapping(),
            "latest_checkpoint": str(latest_checkpoint),
            "binding_sha256": binding["binding_sha256"],
        }

    if progress.generation_cursor != EXPECTED_GENERATION_RECORDS:
        raise SharedB0PhysicsTrainingError("完成运行的生成样本位置不是 800")
    if progress.physics_cursor != EXPECTED_PHYSICS_RECORDS:
        raise SharedB0PhysicsTrainingError("完成运行的物理样本消费数不是 2421")
    return _write_final_artifacts(
        runtime,
        prepared_run,
        config,
        baseline,
        progress,
        metrics,
        binding,
        run_state,
        latest_checkpoint,
    )


def train_shared_b0_physics(
    config: SharedB0PhysicsConfig,
    baseline: str,
    *,
    output_dir: Path,
    resume: str = "auto",
    use_hardware_fallback: bool = False,
    metric_logger: MetricLogger | None = None,
    stop_after_optimization_step: int | None = None,
    swanlab_module: Any | None = None,
) -> dict[str, object]:
    """执行一条共享 B0 基线；短运行参数只供门禁与恢复等价检查使用。"""
    contract = build_baseline_contract(baseline)
    resolved_output_dir = Path(output_dir).expanduser().resolve()
    existing_state = resolved_output_dir / "run_state.json"
    if existing_state.is_file():
        state = _read_json(existing_state, "运行状态")
        if state.get("status") == "completed":
            raise SharedB0PhysicsTrainingError("运行已经完成，拒绝覆盖")
    prepared_inputs = prepare_training_inputs(
        config,
        contract.name,
        use_hardware_fallback=use_hardware_fallback,
    )
    runtime = build_training_runtime(
        config,
        prepared_inputs,
        contract.name,
        use_hardware_fallback=use_hardware_fallback,
        output_dir=resolved_output_dir,
    )
    binding = build_run_binding(
        config,
        prepared_inputs,
        contract.name,
        runtime.state_head_initialization_sha256,
        runtime.lora_initialization_sha256,
        use_hardware_fallback=use_hardware_fallback,
        output_dir=resolved_output_dir,
    )
    prepared_run = prepare_training_run(
        config,
        prepared_inputs,
        binding,
        contract.name,
        resume,
        use_hardware_fallback=use_hardware_fallback,
        output_dir=resolved_output_dir,
    )
    try:
        with capture_console_log(prepared_run.layout.console_log):
            with swanlab_online_training_run(
                config,
                contract.name,
                resolved_output_dir,
                binding,
                swanlab_module=swanlab_module,
            ) as online_logger:
                active_logger: MetricLogger = online_logger
                if metric_logger is not None:
                    active_logger = CompositeMetricLogger(
                        (online_logger, metric_logger)
                    )
                result = _execute_training_loop(
                    runtime,
                    config,
                    prepared_inputs,
                    prepared_run,
                    binding,
                    contract.name,
                    use_hardware_fallback=use_hardware_fallback,
                    metric_logger=active_logger,
                    stop_after_optimization_step=stop_after_optimization_step,
                )
    except BaseException as error:
        if prepared_run.layout.run_state.is_file():
            state = _read_json(prepared_run.layout.run_state, "运行状态")
            if state.get("status") not in {"failed", "interrupted"}:
                _update_run_state(
                    prepared_run.layout,
                    state,
                    status="failed",
                    progress=TrainingProgress.from_mapping(state),
                    failure=f"{type(error).__name__}: {error}",
                )
        _write_artifact_manifest(
            prepared_run.layout,
            binding,
            status="failed",
        )
        raise
    _write_artifact_manifest(
        prepared_run.layout,
        binding,
        status=str(result.get("status", "completed")),
    )
    return result


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="共享 B0 状态监督与标准 PINN 可恢复 Qwen 训练"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--baseline", choices=BASELINES, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--resume", default="auto")
    parser.add_argument("--hardware-fallback", action="store_true")
    args = parser.parse_args(argv)
    if not args.preflight_only and args.output_dir is None:
        parser.error("正式训练必须显式提供唯一的 --output-dir")
    return args


def main() -> None:
    args = _parse_args()
    config = load_shared_b0_physics_training_config(args.config)
    if args.preflight_only:
        prepared = prepare_training_inputs(
            config,
            args.baseline,
            use_hardware_fallback=args.hardware_fallback,
        )
        result = prepared.summary(
            config,
            args.baseline,
            output_dir=args.output_dir,
        )
    else:
        if args.output_dir is None:
            raise SharedB0PhysicsTrainingError("正式训练缺少 --output-dir")
        result = train_shared_b0_physics(
            config,
            args.baseline,
            output_dir=args.output_dir,
            resume=args.resume,
            use_hardware_fallback=args.hardware_fallback,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
