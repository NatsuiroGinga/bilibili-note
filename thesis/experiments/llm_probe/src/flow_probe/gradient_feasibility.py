"""诊断生成、稀疏状态与物理目标的共享 LoRA 梯度可行性。"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import torch
import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.gradient_conflict import (
    GradientDiagnosticError,
    _generation_gradients,
    _gradient_dot,
    _gradient_norm,
    _sample_id,
    _state_and_physics_gradients,
)
from flow_probe.physics_train import (
    ContinuousQueueStateHead,
    _environment_manifest,
    _load_jsonl,
    _load_model,
    _sha256,
    _write_json,
    build_state_supervision_masks,
    physics_sample_schedule,
)
from flow_probe.tracking import TrackingSettings, capture_console_log, swanlab_run

OBJECTIVE_NAMES = ("generation", "state", "physics")
STATE_SUPERVISION_MODE = "anchor0_only"
SIMPLEX_RESOLUTION = 0.02
GENERATION_FLOOR = 0.95
COMMON_DESCENT_TOLERANCE = 1e-8
RESPONSE_TOLERANCE = 1e-6
PHASE = "gradient-feasibility"
TRAIN_STREAM_SEED_OFFSET = 0
VALIDATION_STREAM_SEED_OFFSET = 100_003
PHYSICS_STREAM_SEED_OFFSET = 200_003

GramMatrix = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]
ObjectiveVector = tuple[float, float, float]


class GradientFeasibilityError(GradientDiagnosticError):
    """梯度可行性输入、数值或制品不满足固定协议。"""


@dataclass(frozen=True)
class DirectionSolution:
    """单纯形方向的三目标权重、一阶边际与优化目标。"""

    weights: ObjectiveVector
    margins: ObjectiveVector
    objective: float


@dataclass(frozen=True)
class FeasibilityBatch:
    """一个诊断步使用的三套互相独立的样本顺序。"""

    step: int
    generation_train_microbatches: tuple[tuple[int, ...], ...]
    generation_validation_microbatches: tuple[tuple[int, ...], ...]
    physics_indices: tuple[int, ...]


@dataclass(frozen=True)
class FeasibilitySettings:
    """真实批次梯度可行性诊断的固定协议。"""

    output_dir: Path
    generation_train_file: Path
    generation_validation_file: Path
    physics_train_file: Path
    generation_batch_size: int
    generation_accumulation_steps: int
    physics_batch_size: int
    paired_batches: int
    simplex_resolution: float = SIMPLEX_RESOLUTION
    generation_floor: float = GENERATION_FLOOR
    state_supervision_mode: str = STATE_SUPERVISION_MODE


@dataclass(frozen=True)
class FeasibilityLayout:
    """诊断必须完整写出的十类制品。"""

    output_dir: Path
    config_snapshot: Path
    environment: Path
    input_sha256: Path
    sample_order: Path
    state_mask: Path
    step_metrics: Path
    summary: Path
    console_log: Path
    artifact_manifest: Path

    @property
    def required_paths(self) -> tuple[Path, ...]:
        return (
            self.config_snapshot,
            self.environment,
            self.input_sha256,
            self.sample_order,
            self.state_mask,
            self.step_metrics,
            self.summary,
            self.console_log,
            self.output_dir / "swanlog" / PHASE,
            self.artifact_manifest,
        )


def validate_gram_matrix(gram: Sequence[Sequence[float]], *, tolerance: float = 1e-7) -> GramMatrix:
    """校验三单位梯度的对称半正定 Gram 矩阵。"""
    if len(gram) != 3 or any(len(row) != 3 for row in gram):
        raise GradientFeasibilityError("Gram 矩阵必须为 3x3")
    if not math.isfinite(tolerance) or tolerance <= 0:
        raise GradientFeasibilityError("Gram 校验容差必须为有限正数")
    values = tuple(tuple(float(value) for value in row) for row in gram)
    if not all(math.isfinite(value) for row in values for value in row):
        raise GradientFeasibilityError("Gram 矩阵包含非有限值")
    for row in range(3):
        if abs(values[row][row] - 1.0) > tolerance:
            raise GradientFeasibilityError("单位梯度 Gram 矩阵的对角线必须为 1")
        for column in range(3):
            if abs(values[row][column] - values[column][row]) > tolerance:
                raise GradientFeasibilityError("Gram 矩阵必须对称")
            if values[row][column] < -1.0 - tolerance or values[row][column] > 1.0 + tolerance:
                raise GradientFeasibilityError("Gram 矩阵元素必须位于 [-1, 1]")
    for left, right in ((0, 1), (0, 2), (1, 2)):
        minor = values[left][left] * values[right][right] - values[left][right] ** 2
        if minor < -tolerance:
            raise GradientFeasibilityError("Gram 矩阵不是半正定矩阵")
    determinant = (
        values[0][0] * (values[1][1] * values[2][2] - values[1][2] * values[2][1])
        - values[0][1] * (values[1][0] * values[2][2] - values[1][2] * values[2][0])
        + values[0][2] * (values[1][0] * values[2][1] - values[1][1] * values[2][0])
    )
    if determinant < -tolerance:
        raise GradientFeasibilityError("Gram 矩阵不是半正定矩阵")
    return values  # type: ignore[return-value]


def direction_margins(gram: Sequence[Sequence[float]], weights: Sequence[float]) -> ObjectiveVector:
    """计算聚合单位梯度方向对三个目标的一阶下降边际。"""
    matrix = validate_gram_matrix(gram)
    if len(weights) != 3:
        raise GradientFeasibilityError("方向权重必须包含三个分量")
    normalized = tuple(float(value) for value in weights)
    if not all(math.isfinite(value) and value >= 0 for value in normalized):
        raise GradientFeasibilityError("方向权重必须为有限非负数")
    if abs(sum(normalized) - 1.0) > 1e-12:
        raise GradientFeasibilityError("方向权重必须位于单位单纯形")
    return tuple(
        sum(matrix[row][column] * normalized[column] for column in range(3)) for row in range(3)
    )  # type: ignore[return-value]


def _resolution_units(resolution: float) -> int:
    value = float(resolution)
    if not math.isfinite(value) or value <= 0 or value > 1:
        raise GradientFeasibilityError("单纯形分辨率必须位于 (0, 1]")
    units = round(1.0 / value)
    if units <= 0 or abs(value * units - 1.0) > 1e-12:
        raise GradientFeasibilityError("单纯形分辨率必须能够整数划分 1")
    return units


def _simplex_weights(resolution: float) -> tuple[ObjectiveVector, ...]:
    units = _resolution_units(resolution)
    result: list[ObjectiveVector] = []
    for generation_units in range(units, -1, -1):
        remaining = units - generation_units
        for state_units in range(remaining, -1, -1):
            physics_units = remaining - state_units
            result.append(
                (
                    generation_units / units,
                    state_units / units,
                    physics_units / units,
                )
            )
    return tuple(result)


def _solution_key(solution: DirectionSolution) -> tuple[float, ...]:
    return (
        solution.objective,
        solution.margins[0],
        solution.margins[1],
        solution.margins[2],
        solution.weights[0],
        solution.weights[1],
        solution.weights[2],
    )


def solve_common_descent(
    gram: Sequence[Sequence[float]], *, resolution: float = SIMPLEX_RESOLUTION
) -> DirectionSolution:
    """在确定性整数单纯形网格上最大化三个下降边际的最小值。"""
    matrix = validate_gram_matrix(gram)
    candidates = []
    for weights in _simplex_weights(resolution):
        margins = direction_margins(matrix, weights)
        candidates.append(
            DirectionSolution(weights=weights, margins=margins, objective=min(margins))
        )
    if not candidates:
        raise GradientFeasibilityError("单纯形网格没有候选方向")
    return max(candidates, key=_solution_key)


def solve_generation_protected_direction(
    gram: Sequence[Sequence[float]],
    *,
    generation_floor: float = GENERATION_FLOOR,
    resolution: float = SIMPLEX_RESOLUTION,
) -> DirectionSolution:
    """在生成边际下界内最大化状态与物理边际的最小值。"""
    matrix = validate_gram_matrix(gram)
    floor = float(generation_floor)
    if not math.isfinite(floor) or floor < 0 or floor > 1:
        raise GradientFeasibilityError("生成保护底线必须位于 [0, 1]")
    candidates = []
    for weights in _simplex_weights(resolution):
        margins = direction_margins(matrix, weights)
        if margins[0] + 1e-12 < floor:
            continue
        candidates.append(
            DirectionSolution(
                weights=weights,
                margins=margins,
                objective=min(margins[1], margins[2]),
            )
        )
    if not candidates:
        raise GradientFeasibilityError("没有满足生成保护底线的单纯形方向")
    return max(candidates, key=_solution_key)


def has_strict_common_descent(
    solution: DirectionSolution, *, tolerance: float = COMMON_DESCENT_TOLERANCE
) -> bool:
    """判断最优共同方向是否严格改善三个目标的一阶代理。"""
    if not math.isfinite(tolerance) or tolerance < 0:
        raise GradientFeasibilityError("共同下降容差必须为有限非负数")
    return solution.objective > tolerance


def is_generation_vetoed(
    solution: DirectionSolution, *, generation_floor: float = GENERATION_FLOOR
) -> bool:
    """判断无保护共同方向是否违反生成边际底线。"""
    floor = float(generation_floor)
    if not math.isfinite(floor) or floor < 0 or floor > 1:
        raise GradientFeasibilityError("生成保护底线必须位于 [0, 1]")
    return solution.margins[0] + 1e-12 < floor


def has_dual_auxiliary_participation(
    solution: DirectionSolution, *, tolerance: float = 0.0
) -> bool:
    """判断保护解中状态与物理目标是否同时有效参与。"""
    if not math.isfinite(tolerance) or tolerance < 0:
        raise GradientFeasibilityError("辅助参与容差必须为有限非负数")
    return (
        solution.weights[1] > 0
        and solution.weights[2] > 0
        and solution.margins[1] > tolerance
        and solution.margins[2] > tolerance
    )


def gradient_gram_matrix(
    generation_gradients: Sequence[torch.Tensor | None],
    state_gradients: Sequence[torch.Tensor | None],
    physics_gradients: Sequence[torch.Tensor | None],
) -> GramMatrix:
    """逐参数张量累计三个非零梯度的单位 Gram 矩阵。"""
    if not (len(generation_gradients) == len(state_gradients) == len(physics_gradients)):
        raise GradientFeasibilityError("三个目标的梯度参数张量数量不一致")
    gradients = (generation_gradients, state_gradients, physics_gradients)
    norms = tuple(
        _gradient_norm(name, values)
        for name, values in zip(("生成", "状态", "物理"), gradients, strict=True)
    )
    rows: list[tuple[float, float, float]] = []
    for row in range(3):
        values = []
        for column in range(3):
            if row == column:
                values.append(1.0)
            else:
                cosine = _gradient_dot(gradients[row], gradients[column]) / (
                    norms[row] * norms[column]
                )
                values.append(max(-1.0, min(1.0, cosine)))
        rows.append(tuple(values))  # type: ignore[arg-type]
    return validate_gram_matrix(tuple(rows))


def g5_response_proxy(
    validation_generation_gradients: Sequence[torch.Tensor | None],
    follower_gradients: Sequence[torch.Tensor | None],
) -> float:
    """计算独立验证生成梯度对跟随目标更新的归一化一阶反应。"""
    if len(validation_generation_gradients) != len(follower_gradients):
        raise GradientFeasibilityError("G5 反应代理的梯度参数张量数量不一致")
    validation_norm = _gradient_norm("验证生成", validation_generation_gradients)
    follower_norm = _gradient_norm("跟随目标", follower_gradients)
    value = _gradient_dot(validation_generation_gradients, follower_gradients) / (
        validation_norm * follower_norm
    )
    if not math.isfinite(value):
        raise GradientFeasibilityError("G5 反应代理非有限")
    return max(-1.0, min(1.0, value))


def build_feasibility_schedule(
    *,
    generation_train_sample_count: int,
    generation_validation_sample_count: int,
    physics_sample_count: int,
    paired_batches: int,
    generation_batch_size: int,
    generation_accumulation_steps: int,
    physics_batch_size: int,
    seed: int,
) -> tuple[FeasibilityBatch, ...]:
    """以三个独立确定性随机流构造真实批次诊断顺序。"""
    if paired_batches <= 0 or generation_accumulation_steps <= 0:
        raise GradientFeasibilityError("配对批次数和生成累积步数必须大于零")
    train = physics_sample_schedule(
        generation_train_sample_count,
        batch_size=generation_batch_size,
        steps=paired_batches * generation_accumulation_steps,
        seed=seed + TRAIN_STREAM_SEED_OFFSET,
    )
    validation = physics_sample_schedule(
        generation_validation_sample_count,
        batch_size=generation_batch_size,
        steps=paired_batches * generation_accumulation_steps,
        seed=seed + VALIDATION_STREAM_SEED_OFFSET,
    )
    physics = physics_sample_schedule(
        physics_sample_count,
        batch_size=physics_batch_size,
        steps=paired_batches,
        seed=seed + PHYSICS_STREAM_SEED_OFFSET,
    )
    return tuple(
        FeasibilityBatch(
            step=step,
            generation_train_microbatches=tuple(
                train[
                    (step - 1)
                    * generation_accumulation_steps : step
                    * generation_accumulation_steps
                ]
            ),
            generation_validation_microbatches=tuple(
                validation[
                    (step - 1)
                    * generation_accumulation_steps : step
                    * generation_accumulation_steps
                ]
            ),
            physics_indices=physics[step - 1],
        )
        for step in range(1, paired_batches + 1)
    )


def _build_settings(
    raw: Mapping[str, object], output_dir: Path, paired_batches: int
) -> FeasibilitySettings:
    training = raw.get("training")
    if not isinstance(training, Mapping):
        raise GradientFeasibilityError("配置缺少 training")
    required = (
        "generation_train_file",
        "generation_validation_file",
        "physics_train_file",
        "generation_batch_size",
        "gradient_accumulation_steps",
        "physics_batch_size",
        "state_supervision_mode",
    )
    missing = [name for name in required if name not in training]
    if missing:
        raise GradientFeasibilityError("缺少诊断配置：" + ", ".join(missing))
    settings = FeasibilitySettings(
        output_dir=Path(output_dir),
        generation_train_file=Path(str(training["generation_train_file"])),
        generation_validation_file=Path(str(training["generation_validation_file"])),
        physics_train_file=Path(str(training["physics_train_file"])),
        generation_batch_size=int(training["generation_batch_size"]),
        generation_accumulation_steps=int(training["gradient_accumulation_steps"]),
        physics_batch_size=int(training["physics_batch_size"]),
        paired_batches=int(paired_batches),
        state_supervision_mode=str(training["state_supervision_mode"]).lower(),
    )
    if (
        settings.generation_batch_size,
        settings.generation_accumulation_steps,
        settings.physics_batch_size,
    ) != (4, 4, 4):
        raise GradientFeasibilityError("梯度可行性诊断必须固定为生成4x4和物理4")
    if settings.paired_batches not in {2, 20}:
        raise GradientFeasibilityError("梯度可行性诊断只允许 2 或 20 个配对批次")
    if settings.state_supervision_mode != STATE_SUPERVISION_MODE:
        raise GradientFeasibilityError("梯度可行性诊断必须使用 anchor0_only 状态监督")
    for path in (
        settings.generation_train_file,
        settings.generation_validation_file,
        settings.physics_train_file,
    ):
        if not path.is_file():
            raise GradientFeasibilityError(f"诊断输入不存在：{path}")
    return settings


def _create_layout(output_dir: Path) -> FeasibilityLayout:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    return FeasibilityLayout(
        output_dir=output_dir,
        config_snapshot=output_dir / "config.snapshot.yaml",
        environment=output_dir / "environment.json",
        input_sha256=output_dir / "input_sha256.json",
        sample_order=output_dir / "sample_order.json",
        state_mask=output_dir / "state_mask.json",
        step_metrics=output_dir / "step_metrics.jsonl",
        summary=output_dir / "summary.json",
        console_log=output_dir / "console.log",
        artifact_manifest=output_dir / "artifact_manifest.json",
    )


def _input_manifest(settings: FeasibilitySettings) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, path in (
        ("generation_train", settings.generation_train_file),
        ("generation_validation", settings.generation_validation_file),
        ("physics_train", settings.physics_train_file),
    ):
        with path.open("r", encoding="utf-8") as source:
            records = sum(1 for line in source if line.strip())
        result[name] = {
            "path": str(path),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "records": records,
        }
    return result


def _write_sample_order(
    path: Path,
    schedule: Sequence[FeasibilityBatch],
    generation_train_records: Sequence[Mapping[str, object]],
    generation_validation_records: Sequence[Mapping[str, object]],
    physics_records: Sequence[Mapping[str, object]],
    *,
    seed: int,
) -> None:
    def generation_batches(
        batches: Sequence[Sequence[int]], records: Sequence[Mapping[str, object]]
    ) -> list[dict[str, object]]:
        return [
            {
                "indices": list(indices),
                "sample_ids": [_sample_id(records[index], index) for index in indices],
            }
            for indices in batches
        ]

    _write_json(
        path,
        {
            "schema_version": "flow_probe_gradient_feasibility_order_v1",
            "stream_seeds": {
                "generation_train": seed + TRAIN_STREAM_SEED_OFFSET,
                "generation_validation": seed + VALIDATION_STREAM_SEED_OFFSET,
                "physics_train": seed + PHYSICS_STREAM_SEED_OFFSET,
            },
            "steps": [
                {
                    "step": batch.step,
                    "generation_train_microbatches": generation_batches(
                        batch.generation_train_microbatches,
                        generation_train_records,
                    ),
                    "generation_validation_microbatches": generation_batches(
                        batch.generation_validation_microbatches,
                        generation_validation_records,
                    ),
                    "physics": {
                        "indices": list(batch.physics_indices),
                        "sample_ids": [
                            _sample_id(physics_records[index], index)
                            for index in batch.physics_indices
                        ],
                    },
                }
                for batch in schedule
            ],
        },
    )


def _write_state_mask(
    path: Path,
    masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> None:
    _write_json(
        path,
        {
            "schema_version": "flow_probe_state_mask_v1",
            "mode": STATE_SUPERVISION_MODE,
            "observed_anchor_fraction": sum(sum(mask) for mask in masks.values())
            / (5 * len(masks)),
            "samples": [
                {"sample_id": sample_id, "mask": list(masks[sample_id])}
                for sample_id in sorted(masks)
            ],
        },
    )


def _solution_metrics(prefix: str, solution: DirectionSolution) -> dict[str, float]:
    metrics = {f"{prefix}/objective": solution.objective}
    for index, name in enumerate(OBJECTIVE_NAMES):
        metrics[f"{prefix}/weight_{name}"] = solution.weights[index]
        metrics[f"{prefix}/margin_{name}"] = solution.margins[index]
    return metrics


def _step_metrics(
    *,
    generation_train_loss: float,
    generation_validation_loss: float,
    state_loss: float,
    physics_loss: float,
    gram: GramMatrix,
    common: DirectionSolution,
    protected: DirectionSolution,
    state_response_proxy: float,
    physics_response_proxy: float,
    generation_floor: float,
    elapsed_seconds: float,
) -> dict[str, float]:
    metrics = {
        "feasibility/generation_train_loss": generation_train_loss,
        "feasibility/generation_validation_loss": generation_validation_loss,
        "feasibility/state_loss": state_loss,
        "feasibility/physics_loss": physics_loss,
        "feasibility/cosine_generation_state": gram[0][1],
        "feasibility/cosine_generation_physics": gram[0][2],
        "feasibility/cosine_state_physics": gram[1][2],
        "feasibility/strict_common_descent": float(has_strict_common_descent(common)),
        "feasibility/generation_veto": float(
            is_generation_vetoed(common, generation_floor=generation_floor)
        ),
        "feasibility/dual_auxiliary_participation": float(
            has_dual_auxiliary_participation(protected)
        ),
        "feasibility/g5_state_response_proxy": state_response_proxy,
        "feasibility/g5_physics_response_proxy": physics_response_proxy,
        "feasibility/g5_state_response_nonzero": float(
            abs(state_response_proxy) > RESPONSE_TOLERANCE
        ),
        "feasibility/g5_physics_response_nonzero": float(
            abs(physics_response_proxy) > RESPONSE_TOLERANCE
        ),
        "feasibility/optimizer_updates": 0.0,
        "feasibility/elapsed_seconds": elapsed_seconds,
        "feasibility/peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
    }
    metrics.update(_solution_metrics("feasibility/common", common))
    metrics.update(_solution_metrics("feasibility/protected", protected))
    if not all(math.isfinite(value) for value in metrics.values()):
        raise GradientFeasibilityError("逐步可行性指标包含非有限值")
    return metrics


def _record_metrics(path: Path, swanlab: object, step: int, metrics: Mapping[str, float]) -> None:
    normalized = {key: float(value) for key, value in metrics.items()}
    with Path(path).open("a", encoding="utf-8") as target:
        target.write(json.dumps({"step": step, "metrics": normalized}, sort_keys=True) + "\n")
    swanlab.log(normalized, step=step)


def _aggregate(step_records: Sequence[Mapping[str, float]]) -> dict[str, object]:
    if not step_records:
        raise GradientFeasibilityError("没有可汇总的诊断步骤")

    def mean(key: str) -> float:
        return sum(float(record[key]) for record in step_records) / len(step_records)

    count = len(step_records)
    return {
        "strict_common_descent": {
            "count": int(
                sum(record["feasibility/strict_common_descent"] for record in step_records)
            ),
            "rate": mean("feasibility/strict_common_descent"),
        },
        "generation_veto": {
            "count": int(sum(record["feasibility/generation_veto"] for record in step_records)),
            "rate": mean("feasibility/generation_veto"),
        },
        "dual_auxiliary_participation": {
            "count": int(
                sum(record["feasibility/dual_auxiliary_participation"] for record in step_records)
            ),
            "rate": mean("feasibility/dual_auxiliary_participation"),
        },
        "g5_response": {
            "state": {
                "mean_proxy": mean("feasibility/g5_state_response_proxy"),
                "nonzero_count": int(
                    sum(record["feasibility/g5_state_response_nonzero"] for record in step_records)
                ),
                "nonzero_rate": mean("feasibility/g5_state_response_nonzero"),
            },
            "physics": {
                "mean_proxy": mean("feasibility/g5_physics_response_proxy"),
                "nonzero_count": int(
                    sum(
                        record["feasibility/g5_physics_response_nonzero"] for record in step_records
                    )
                ),
                "nonzero_rate": mean("feasibility/g5_physics_response_nonzero"),
            },
        },
        "mean_common_weights": {
            name: mean(f"feasibility/common/weight_{name}") for name in OBJECTIVE_NAMES
        },
        "mean_common_margins": {
            name: mean(f"feasibility/common/margin_{name}") for name in OBJECTIVE_NAMES
        },
        "mean_protected_weights": {
            name: mean(f"feasibility/protected/weight_{name}") for name in OBJECTIVE_NAMES
        },
        "mean_protected_margins": {
            name: mean(f"feasibility/protected/margin_{name}") for name in OBJECTIVE_NAMES
        },
        "mean_step_seconds": mean("feasibility/elapsed_seconds"),
        "paired_batches": count,
    }


def _tracking_settings(raw: Mapping[str, object], run_name: str) -> TrackingSettings:
    tracking = raw.get("tracking")
    if not isinstance(tracking, Mapping):
        raise GradientFeasibilityError("配置缺少 tracking")
    tags = list(tracking.get("tags", ()))
    for tag in ("gradient-feasibility", STATE_SUPERVISION_MODE):
        if tag not in tags:
            tags.append(tag)
    settings = TrackingSettings.from_mapping(
        {
            **tracking,
            "run_name": run_name,
            "description": "Qwen3-1.7B 三目标共享 LoRA 梯度可行性诊断",
            "tags": tags,
        }
    )
    if (
        settings.workspace,
        settings.project,
        settings.mode,
    ) != ("mortiswang", "malicious-traffic-llm", "online"):
        raise GradientFeasibilityError("正式诊断必须使用固定 SwanLab 在线项目")
    return settings


def run_gradient_feasibility_diagnostic(
    probe: ProbeConfig,
    settings: FeasibilitySettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
) -> dict[str, object]:
    """运行不更新参数的三目标真实批次梯度可行性诊断。"""
    layout = _create_layout(settings.output_dir)
    generation_train_records = _load_jsonl(settings.generation_train_file)
    generation_validation_records = _load_jsonl(settings.generation_validation_file)
    physics_records = _load_jsonl(settings.physics_train_file)
    state_masks = build_state_supervision_masks(
        physics_records,
        settings.state_supervision_mode,
        probe.seed,
    )
    schedule = build_feasibility_schedule(
        generation_train_sample_count=len(generation_train_records),
        generation_validation_sample_count=len(generation_validation_records),
        physics_sample_count=len(physics_records),
        paired_batches=settings.paired_batches,
        generation_batch_size=settings.generation_batch_size,
        generation_accumulation_steps=settings.generation_accumulation_steps,
        physics_batch_size=settings.physics_batch_size,
        seed=probe.seed,
    )
    snapshot = {
        "schema_version": "flow_probe_gradient_feasibility_v1",
        "probe": {
            "model_id": probe.model_id,
            "seed": probe.seed,
            "max_input_length": probe.max_input_length,
            "lora_rank": probe.lora_rank,
            "lora_alpha": probe.lora_alpha,
            "lora_dropout": probe.lora_dropout,
        },
        "diagnostic": {
            "paired_batches": settings.paired_batches,
            "generation_batch_size": settings.generation_batch_size,
            "generation_accumulation_steps": settings.generation_accumulation_steps,
            "physics_batch_size": settings.physics_batch_size,
            "state_supervision_mode": settings.state_supervision_mode,
            "simplex_resolution": settings.simplex_resolution,
            "generation_floor": settings.generation_floor,
            "common_descent_tolerance": COMMON_DESCENT_TOLERANCE,
            "response_tolerance": RESPONSE_TOLERANCE,
            "optimizer_updates": 0,
            "residual_denominator": "strict_positive_configured_capacity_integral_link_bytes",
            "stream_seed_offsets": {
                "generation_train": TRAIN_STREAM_SEED_OFFSET,
                "generation_validation": VALIDATION_STREAM_SEED_OFFSET,
                "physics_train": PHYSICS_STREAM_SEED_OFFSET,
            },
        },
        "tracking": {
            "workspace": tracking.workspace,
            "project": tracking.project,
            "run_name": tracking.run_name,
            "mode": tracking.mode,
        },
        "source_training_config": dict(raw_config["training"]),
    }
    layout.config_snapshot.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    _write_json(layout.environment, _environment_manifest())
    _write_json(layout.input_sha256, _input_manifest(settings))
    _write_sample_order(
        layout.sample_order,
        schedule,
        generation_train_records,
        generation_validation_records,
        physics_records,
        seed=probe.seed,
    )
    _write_state_mask(layout.state_mask, state_masks)
    data_files = {
        "config_snapshot": layout.config_snapshot,
        "environment": layout.environment,
        "input_sha256": layout.input_sha256,
        "sample_order": layout.sample_order,
        "state_mask": layout.state_mask,
        "step_metrics": layout.step_metrics,
        "summary": layout.summary,
    }
    started = time.perf_counter()
    with (
        capture_console_log(layout.console_log),
        swanlab_run(
            settings=tracking,
            phase=PHASE,
            config=snapshot,
            artifact_dir=layout.output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        torch.manual_seed(probe.seed)
        torch.cuda.manual_seed_all(probe.seed)
        torch.cuda.reset_peak_memory_stats()
        tokenizer, model = _load_model(probe)
        device = next(model.parameters()).device
        state_head = ContinuousQueueStateHead(model.config.hidden_size).to(
            device=device, dtype=torch.bfloat16
        )
        state_head.train()
        lora_parameters = tuple(
            parameter
            for name, parameter in model.named_parameters()
            if parameter.requires_grad and "lora_" in name
        )
        if not lora_parameters:
            raise GradientFeasibilityError("未发现可训练 LoRA 参数")
        if any(parameter.grad is not None for parameter in lora_parameters):
            raise GradientFeasibilityError("诊断开始前 LoRA 参数已有持久梯度")
        step_records: list[dict[str, float]] = []
        for paired in schedule:
            step_started = time.perf_counter()
            generation_train_loss, generation_train_gradients = _generation_gradients(
                model,
                tokenizer,
                lora_parameters,
                generation_train_records,
                paired.generation_train_microbatches,
                max_length=probe.max_input_length,
                device=device,
            )
            generation_validation_loss, generation_validation_gradients = _generation_gradients(
                model,
                tokenizer,
                lora_parameters,
                generation_validation_records,
                paired.generation_validation_microbatches,
                max_length=probe.max_input_length,
                device=device,
            )
            state_loss, physics_loss, state_gradients, physics_gradients = (
                _state_and_physics_gradients(
                    model,
                    state_head,
                    tokenizer,
                    lora_parameters,
                    physics_records,
                    paired.physics_indices,
                    max_length=probe.max_input_length,
                    device=device,
                    state_masks=state_masks,
                )
            )
            gram = gradient_gram_matrix(
                generation_train_gradients,
                state_gradients,
                physics_gradients,
            )
            common = solve_common_descent(gram, resolution=settings.simplex_resolution)
            protected = solve_generation_protected_direction(
                gram,
                generation_floor=settings.generation_floor,
                resolution=settings.simplex_resolution,
            )
            state_response = g5_response_proxy(
                generation_validation_gradients,
                state_gradients,
            )
            physics_response = g5_response_proxy(
                generation_validation_gradients,
                physics_gradients,
            )
            metrics = _step_metrics(
                generation_train_loss=generation_train_loss,
                generation_validation_loss=generation_validation_loss,
                state_loss=state_loss,
                physics_loss=physics_loss,
                gram=gram,
                common=common,
                protected=protected,
                state_response_proxy=state_response,
                physics_response_proxy=physics_response,
                generation_floor=settings.generation_floor,
                elapsed_seconds=time.perf_counter() - step_started,
            )
            _record_metrics(layout.step_metrics, swanlab, paired.step, metrics)
            step_records.append(metrics)
            print(
                json.dumps(
                    {"step": paired.step, **metrics},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            if any(parameter.grad is not None for parameter in lora_parameters):
                raise GradientFeasibilityError("诊断期间意外写入了 LoRA 参数梯度")
        torch.cuda.synchronize()
        persistent_grad_count = sum(parameter.grad is not None for parameter in lora_parameters)
        summary = {
            "schema_version": "flow_probe_gradient_feasibility_v1",
            "status": "finished",
            "model_id": probe.model_id,
            "seed": probe.seed,
            "paired_batches": settings.paired_batches,
            "optimizer_updates": 0,
            "persistent_lora_grad_count": persistent_grad_count,
            "state_supervision_mode": settings.state_supervision_mode,
            "simplex_resolution": settings.simplex_resolution,
            "generation_floor": settings.generation_floor,
            "trainable_lora_parameter_count": sum(
                parameter.numel() for parameter in lora_parameters
            ),
            "input_sha256": _sha256(layout.input_sha256),
            "sample_order_sha256": _sha256(layout.sample_order),
            "state_mask_sha256": _sha256(layout.state_mask),
            "runtime_seconds": time.perf_counter() - started,
            "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            **_aggregate(step_records),
        }
        if persistent_grad_count != 0:
            raise GradientFeasibilityError("诊断完成后 LoRA 参数仍有持久梯度")
        _write_json(layout.summary, summary)
        swanlab.log(
            {
                "summary/runtime_seconds": summary["runtime_seconds"],
                "summary/peak_gpu_memory_mib": summary["peak_gpu_memory_mib"],
                "summary/strict_common_descent_rate": summary["strict_common_descent"]["rate"],
                "summary/generation_veto_rate": summary["generation_veto"]["rate"],
                "summary/dual_auxiliary_participation_rate": summary[
                    "dual_auxiliary_participation"
                ]["rate"],
                "summary/g5_state_nonzero_rate": summary["g5_response"]["state"]["nonzero_rate"],
                "summary/g5_physics_nonzero_rate": summary["g5_response"]["physics"][
                    "nonzero_rate"
                ],
            },
            step=settings.paired_batches + 1,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    missing = [str(path) for path in layout.required_paths if not path.exists()]
    if missing:
        raise GradientFeasibilityError("诊断制品不完整：" + ", ".join(missing))
    return json.loads(layout.artifact_manifest.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行三目标共享 LoRA 梯度可行性诊断")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--paired-batches", type=int, choices=(2, 20), default=20)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise GradientFeasibilityError("配置根节点必须是映射")
    probe = ProbeConfig.from_mapping(raw["probe"])
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = _build_settings(raw, args.output_dir, args.paired_batches)
    tracking = _tracking_settings(raw, args.run_name)
    manifest = run_gradient_feasibility_diagnostic(probe, settings, tracking, raw)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
