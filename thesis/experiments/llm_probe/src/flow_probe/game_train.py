"""G2-G5 三目标博弈协调与一次可微跟随响应的统一训练入口。"""

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
from torch.func import functional_call

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.game_coordination import (
    ASYMMETRIC_POWERS,
    GENERATION_FLOOR,
    CoordinationSolution,
    G5Coordinator,
    build_g5_diagnostics,
    coordinate_g5_response,
    g5_projection_jacobian_norm,
    solve_asymmetric_bargaining,
    solve_reliability_protected_available,
    solve_symmetric_bargaining,
)
from flow_probe.gradient_conflict import GradientTuple, _generation_gradients, _gradient_dot
from flow_probe.gradient_feasibility import (
    SIMPLEX_RESOLUTION,
    GramMatrix,
    ObjectiveVector,
    direction_margins,
    validate_gram_matrix,
)
from flow_probe.physics_train import (
    ContinuousQueueStateHead,
    _environment_manifest,
    _evaluate_generation,
    _evaluate_state,
    _generation_batch,
    _input_manifest,
    _load_jsonl,
    _load_model,
    _sha256,
    _state_batch,
    _state_mask_sha256,
    _write_json,
    build_state_supervision_masks,
    masked_state_target_loss,
    physics_sample_schedule,
    prepare_physics_record,
    prepare_state_record,
    queue_balance_residual,
)
from flow_probe.qwen_physics_gradient import select_last_token_hidden
from flow_probe.tracking import TrackingSettings, capture_console_log, swanlab_run

G5_VARIANTS = ("G5", "G5-STOP-RESPONSE")
GAME_VARIANTS = ("G2", "G3", "G4", "G4R", *G5_VARIANTS)
STATE_SUPERVISION_MODE = "anchor0_only"
PHASE = "game-train"
G5_COORDINATOR_LEARNING_RATE = 2e-4
G5_EXPECTED_LORA_PARAMETER_COUNT = 17_432_576
G5_GENERATION_VALIDATION_SEED_OFFSET = 100_003
G5_PHYSICS_VALIDATION_SEED_OFFSET = 200_003
GAME_STEP_METRIC_KEYS = (
    "train/total_loss",
    "train/generation_loss",
    "train/state_loss",
    "train/physics_loss",
    "train/generation_gradient_norm",
    "train/state_gradient_norm",
    "train/physics_gradient_norm",
    "train/lora_gradient_norm",
    "train/state_head_gradient_norm",
    "train/cosine_generation_state",
    "train/cosine_generation_physics",
    "train/cosine_state_physics",
    "coordination/objective",
    "coordination/weight_generation",
    "coordination/weight_state",
    "coordination/weight_physics",
    "coordination/margin_generation",
    "coordination/margin_state",
    "coordination/margin_physics",
    "coordination/physics_valid_fraction",
    "coordination/physics_reliability",
    "coordination/generation_veto",
    "coordination/state_rejected",
    "coordination/physics_rejected",
    "coordination/fallback_to_generation",
    "coordination/private_state_anchor_forced",
    "train/learning_rate",
    "train/optimizer_updates",
    "train/throughput_samples_per_second",
    "train/peak_gpu_memory_mib",
)
G5_STEP_METRIC_KEYS = (
    "g5/base_weight_generation",
    "g5/base_weight_state",
    "g5/base_weight_physics",
    "g5/response_state",
    "g5/response_physics",
    "g5/selected_state",
    "g5/selected_physics",
    "g5/projection_distance",
    "g5/projection_jacobian_norm",
    "g5/leader_cost",
    "g5/validation_generation_relative",
    "g5/validation_state_unobserved_relative",
    "g5/validation_physics_relative",
    "g5/direct_gradient_norm",
    "g5/reaction_gradient_norm",
    "g5/reaction_proxy_state",
    "g5/reaction_proxy_physics",
    "g5/reaction_gradient_finite",
    "g5/reaction_gate_failure",
    "g5/stop_response",
    "g5/model_optimizer_updates",
    "g5/state_head_updates",
    "g5/coordinator_optimizer_updates",
    "g5/virtual_response_evaluations",
    "g5/validation_forwards",
    "g5/extra_model_optimizer_steps",
)


class GameTrainingError(ValueError):
    """博弈协调训练配置、梯度或制品不满足固定协议。"""


@dataclass(frozen=True)
class GameTrainingSettings:
    """G2-G5 共享的训练预算、数据和协调参数。"""

    variant: str
    output_dir: Path
    generation_train_file: Path
    generation_validation_file: Path
    physics_train_file: Path
    physics_validation_file: Path
    physics_test_file: Path
    learning_rate: float
    generation_batch_size: int
    gradient_accumulation_steps: int
    physics_batch_size: int
    validation_batch_size: int
    max_steps: int
    state_supervision_mode: str
    lambda_state: float
    lambda_physics: float
    max_grad_norm: float
    validation_limit: int | None
    simplex_resolution: float = SIMPLEX_RESOLUTION
    generation_floor: float = GENERATION_FLOOR
    asymmetric_powers: ObjectiveVector = ASYMMETRIC_POWERS
    coordinator_learning_rate: float = G5_COORDINATOR_LEARNING_RATE

    @property
    def effective_generation_batch_size(self) -> int:
        return self.generation_batch_size * self.gradient_accumulation_steps

    @property
    def uses_g5_response(self) -> bool:
        return self.variant in G5_VARIANTS

    @property
    def stops_g5_response(self) -> bool:
        return self.variant == "G5-STOP-RESPONSE"


@dataclass(frozen=True)
class GameRunLayout:
    """一次协调训练必须完整保存的本地制品。"""

    output_dir: Path
    config_snapshot: Path
    environment: Path
    input_sha256: Path
    sample_order: Path
    state_mask: Path
    console_log: Path
    step_metrics: Path
    training_summary: Path
    final_adapter: Path
    state_head: Path
    coordinator: Path
    artifact_manifest: Path

    @property
    def required_paths(self) -> tuple[Path, ...]:
        return (
            self.config_snapshot,
            self.environment,
            self.input_sha256,
            self.sample_order,
            self.state_mask,
            self.console_log,
            self.step_metrics,
            self.training_summary,
            self.final_adapter,
            self.state_head,
            self.artifact_manifest,
            self.output_dir / "swanlog" / PHASE,
        )


@dataclass(frozen=True)
class GameGradientDiagnostics:
    """一次共享梯度协调的范数、Gram、可靠性和最终解。"""

    solution: CoordinationSolution
    gram: GramMatrix
    generation_norm: float
    state_norm: float
    physics_norm: float
    physics_valid_fraction: float
    physics_reliability: float


@dataclass(frozen=True)
class FunctionalAdamWStep:
    """不改写模型与优化器状态的一次 AdamW 响应。"""

    parameters: tuple[torch.Tensor, ...]
    exp_avgs: tuple[torch.Tensor | None, ...]
    exp_avg_sqs: tuple[torch.Tensor | None, ...]
    steps: tuple[int, ...]
    updated: tuple[bool, ...]


@dataclass(frozen=True)
class G5LeaderLosses:
    """独立验证批次上的三个主导方损失。"""

    generation: torch.Tensor
    state_unobserved: torch.Tensor
    physics: torch.Tensor


def _variant_name(value: str) -> str:
    name = str(value).upper()
    if name not in GAME_VARIANTS:
        raise GameTrainingError(f"未知博弈训练变体：{value}")
    return name


def create_game_run_layout(output_dir: Path) -> GameRunLayout:
    """原子创建不可复用的协调训练目录。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    return GameRunLayout(
        output_dir=output_dir,
        config_snapshot=output_dir / "config_snapshot.yaml",
        environment=output_dir / "environment.json",
        input_sha256=output_dir / "input_sha256.json",
        sample_order=output_dir / "sample_order.json",
        state_mask=output_dir / "state_mask.json",
        console_log=output_dir / "console.log",
        step_metrics=output_dir / "step_metrics.jsonl",
        training_summary=output_dir / "training_summary.json",
        final_adapter=output_dir / "final_adapter",
        state_head=output_dir / "state_head.pt",
        coordinator=output_dir / "coordinator.pt",
        artifact_manifest=output_dir / "artifact_manifest.json",
    )


def validate_game_artifacts(layout: GameRunLayout, *, require_coordinator: bool = False) -> None:
    """拒绝把缺少任一强制制品的协调训练标记为完成。"""
    required = layout.required_paths + ((layout.coordinator,) if require_coordinator else ())
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise GameTrainingError("协调训练制品不完整：" + ", ".join(missing))


def _optional_gradient_norm(name: str, gradients: Sequence[torch.Tensor | None]) -> float:
    total = 0.0
    for gradient in gradients:
        if gradient is None:
            continue
        value = gradient.detach().float()
        if not bool(torch.isfinite(value).all().item()):
            raise GameTrainingError(f"{name}梯度包含非有限值")
        total += float(value.square().sum().item())
    if not math.isfinite(total):
        raise GameTrainingError(f"{name}梯度范数非有限")
    return math.sqrt(total)


def _available_gram(
    generation_gradients: Sequence[torch.Tensor | None],
    state_gradients: Sequence[torch.Tensor | None],
    physics_gradients: Sequence[torch.Tensor | None],
    norms: ObjectiveVector,
) -> GramMatrix:
    gradients = (generation_gradients, state_gradients, physics_gradients)
    if not (len(generation_gradients) == len(state_gradients) == len(physics_gradients)):
        raise GameTrainingError("三个目标的共享梯度参数数量不一致")
    rows: list[tuple[float, float, float]] = []
    for row in range(3):
        values = []
        for column in range(3):
            if row == column:
                values.append(1.0)
            elif norms[row] == 0.0 or norms[column] == 0.0:
                values.append(0.0)
            else:
                cosine = _gradient_dot(gradients[row], gradients[column]) / (
                    norms[row] * norms[column]
                )
                values.append(max(-1.0, min(1.0, cosine)))
        rows.append(tuple(values))  # type: ignore[arg-type]
    return validate_gram_matrix(tuple(rows))


def _pure_generation_solution(gram: GramMatrix) -> CoordinationSolution:
    weights: ObjectiveVector = (1.0, 0.0, 0.0)
    return CoordinationSolution(
        weights=weights,
        margins=direction_margins(gram, weights),
        objective=0.0,
        active_auxiliaries=(),
        fallback_to_generation=True,
    )


def _select_solution(
    variant: str,
    gram: GramMatrix,
    *,
    state_available: bool,
    physics_available: bool,
    reliability: float,
    resolution: float,
    generation_floor: float,
    asymmetric_powers: ObjectiveVector,
) -> CoordinationSolution:
    name = _variant_name(variant)
    if name in {"G2", "G3"} and not (state_available and physics_available):
        return _pure_generation_solution(gram)
    if name == "G2":
        return solve_symmetric_bargaining(gram, resolution)
    if name == "G3":
        return solve_asymmetric_bargaining(gram, asymmetric_powers, resolution)
    return solve_reliability_protected_available(
        gram,
        reliability,
        generation_floor,
        resolution,
        state_available=state_available,
        physics_available=physics_available,
    )


def _normalized_component(gradient: torch.Tensor | None, norm: float) -> torch.Tensor | None:
    if gradient is None or norm == 0.0:
        return None
    return gradient.detach().float() / norm


def apply_coordinated_lora_gradients(
    lora_parameters: Sequence[torch.nn.Parameter],
    *,
    generation_gradients: Sequence[torch.Tensor | None],
    state_gradients: Sequence[torch.Tensor | None],
    physics_gradients: Sequence[torch.Tensor | None],
    variant: str,
    physics_valid_fraction: float,
    resolution: float = SIMPLEX_RESOLUTION,
    generation_floor: float = GENERATION_FLOOR,
    asymmetric_powers: ObjectiveVector = ASYMMETRIC_POWERS,
) -> GameGradientDiagnostics:
    """写入生成尺度恢复后的协调 LoRA 梯度，并返回逐步诊断。"""
    count = len(lora_parameters)
    if not (len(generation_gradients) == len(state_gradients) == len(physics_gradients) == count):
        raise GameTrainingError("LoRA 参数与三个目标梯度数量不一致")
    valid_fraction = float(physics_valid_fraction)
    if not math.isfinite(valid_fraction) or valid_fraction < 0 or valid_fraction > 1:
        raise GameTrainingError("物理有效样本比例必须位于 [0, 1]")
    norms: ObjectiveVector = (
        _optional_gradient_norm("生成", generation_gradients),
        _optional_gradient_norm("状态", state_gradients),
        _optional_gradient_norm("物理", physics_gradients),
    )
    if norms[0] == 0.0:
        raise GameTrainingError("生成梯度严格为零，无法恢复共享更新尺度")
    gram = _available_gram(generation_gradients, state_gradients, physics_gradients, norms)
    state_available = norms[1] > 0.0
    physics_available = norms[2] > 0.0
    state_physics_cosine = gram[1][2] if state_available and physics_available else -1.0
    reliability = (
        valid_fraction * (1.0 + state_physics_cosine) / 2.0
        if state_available and physics_available
        else 0.0
    )
    reliability = max(0.0, min(1.0, reliability))
    solution = _select_solution(
        variant,
        gram,
        state_available=state_available,
        physics_available=physics_available,
        reliability=reliability,
        resolution=resolution,
        generation_floor=generation_floor,
        asymmetric_powers=asymmetric_powers,
    )
    gradients = (generation_gradients, state_gradients, physics_gradients)
    for index, parameter in enumerate(lora_parameters):
        combined: torch.Tensor | None = None
        for weight, objective_gradients, norm in zip(
            solution.weights, gradients, norms, strict=True
        ):
            component = _normalized_component(objective_gradients[index], norm)
            if component is None or weight == 0.0:
                continue
            value = float(weight) * component
            combined = value.clone() if combined is None else combined + value
        if combined is None:
            parameter.grad = None
            continue
        restored = norms[0] * combined
        if restored.shape != parameter.shape or not bool(torch.isfinite(restored).all().item()):
            raise GameTrainingError("协调 LoRA 梯度形状错误或包含非有限值")
        parameter.grad = restored.to(device=parameter.device, dtype=parameter.dtype)
    return GameGradientDiagnostics(
        solution=solution,
        gram=gram,
        generation_norm=norms[0],
        state_norm=norms[1],
        physics_norm=norms[2],
        physics_valid_fraction=valid_fraction,
        physics_reliability=reliability,
    )


def apply_private_state_head_gradients(
    state_head_parameters: Sequence[torch.nn.Parameter],
    *,
    state_gradients: Sequence[torch.Tensor | None],
    physics_gradients: Sequence[torch.Tensor | None],
    solution: CoordinationSolution,
    lambda_state: float,
    lambda_physics: float,
    physics_reliability: float,
    variant: str,
) -> None:
    """按变体契约累加状态头的状态与物理私有梯度。"""
    name = _variant_name(variant)
    if not (len(state_head_parameters) == len(state_gradients) == len(physics_gradients)):
        raise GameTrainingError("状态头参数与辅助目标梯度数量不一致")
    physics_scale = lambda_physics * (physics_reliability if name in {"G4", "G4R"} else 1.0)
    force_state_anchor = (
        name == "G4R" and _optional_gradient_norm("状态头状态", state_gradients) > 0.0
    )
    for index, parameter in enumerate(state_head_parameters):
        combined: torch.Tensor | None = None
        state_gradient = state_gradients[index]
        if (solution.accepts_state or force_state_anchor) and state_gradient is not None:
            combined = lambda_state * state_gradient.detach().float()
        if solution.accepts_physics and physics_gradients[index] is not None:
            value = physics_scale * physics_gradients[index].detach().float()
            combined = value.clone() if combined is None else combined + value
        if combined is None:
            parameter.grad = None
        else:
            if combined.shape != parameter.shape or not bool(torch.isfinite(combined).all().item()):
                raise GameTrainingError("状态头私有梯度形状错误或包含非有限值")
            parameter.grad = combined.to(device=parameter.device, dtype=parameter.dtype)


def _g5_anchored_private_component(
    gradient: torch.Tensor | None,
    *,
    weight: torch.Tensor,
    base_weight: float,
    normalized_scale: float,
    base_scale: float,
) -> torch.Tensor | None:
    if gradient is None or normalized_scale == 0.0:
        return None
    value = gradient.detach().float()
    current_weight = weight.to(device=value.device, dtype=value.dtype)
    component = current_weight * normalized_scale * value
    if base_weight <= 0.0 or base_scale == 0.0:
        return component
    ratio = torch.clamp(current_weight / base_weight, min=0.0, max=1.0)
    anchor = ratio.square() * (3.0 - 2.0 * ratio)
    correction_scale = base_scale - base_weight * normalized_scale
    return component + anchor * correction_scale * value


def build_g5_follower_gradients(
    lora_parameters: Sequence[torch.nn.Parameter],
    state_head_parameters: Sequence[torch.nn.Parameter],
    *,
    generation_gradients: Sequence[torch.Tensor | None],
    state_lora_gradients: Sequence[torch.Tensor | None],
    physics_lora_gradients: Sequence[torch.Tensor | None],
    state_head_state_gradients: Sequence[torch.Tensor | None],
    state_head_physics_gradients: Sequence[torch.Tensor | None],
    base_lora_gradients: Sequence[torch.Tensor | None],
    base_state_head_gradients: Sequence[torch.Tensor | None],
    base_diagnostics: GameGradientDiagnostics,
    coordinated_weights: torch.Tensor,
    lambda_state: float,
    lambda_physics: float,
    stop_response: bool,
) -> tuple[GradientTuple, GradientTuple]:
    """构造以 G4 为前向零点、对协调权重可微的跟随梯度。"""
    if coordinated_weights.shape != (3,) or not bool(
        torch.isfinite(coordinated_weights).all().item()
    ):
        raise GameTrainingError("G5 协调权重必须为有限三维张量")
    lora_count = len(lora_parameters)
    if not (
        len(generation_gradients)
        == len(state_lora_gradients)
        == len(physics_lora_gradients)
        == len(base_lora_gradients)
        == lora_count
    ):
        raise GameTrainingError("G5 LoRA 参数与梯度数量不一致")
    head_count = len(state_head_parameters)
    if not (
        len(state_head_state_gradients)
        == len(state_head_physics_gradients)
        == len(base_state_head_gradients)
        == head_count
    ):
        raise GameTrainingError("G5 状态头参数与梯度数量不一致")
    if stop_response:
        return (
            tuple(
                None if value is None else value.detach().float().clone()
                for value in base_lora_gradients
            ),
            tuple(
                None if value is None else value.detach().float().clone()
                for value in base_state_head_gradients
            ),
        )

    norms = (
        base_diagnostics.generation_norm,
        base_diagnostics.state_norm,
        base_diagnostics.physics_norm,
    )
    normalized_scales = (
        1.0,
        norms[0] / norms[1] if norms[1] > 0.0 else 0.0,
        norms[0] / norms[2] if norms[2] > 0.0 else 0.0,
    )
    objective_gradients = (
        generation_gradients,
        state_lora_gradients,
        physics_lora_gradients,
    )
    lora_result: list[torch.Tensor | None] = []
    for index in range(lora_count):
        combined: torch.Tensor | None = None
        for objective_index, gradients in enumerate(objective_gradients):
            component = _normalized_component(gradients[index], norms[objective_index])
            if component is None:
                continue
            weight = coordinated_weights[objective_index].to(
                device=component.device, dtype=component.dtype
            )
            value = norms[0] * weight * component
            combined = value if combined is None else combined + value
        base_gradient = base_lora_gradients[index]
        if (
            combined is not None
            and base_gradient is not None
            and bool(
                torch.equal(
                    coordinated_weights.detach().cpu(),
                    torch.tensor(
                        base_diagnostics.solution.weights, dtype=coordinated_weights.dtype
                    ),
                )
            )
        ):
            base_value = base_gradient.detach().float().to(combined.device)
            combined = combined + (base_value - combined).detach()
        lora_result.append(combined)

    base_solution = base_diagnostics.solution
    state_base_scale = lambda_state if base_solution.accepts_state else 0.0
    physics_base_scale = (
        lambda_physics * base_diagnostics.physics_reliability
        if base_solution.accepts_physics
        else 0.0
    )
    head_result: list[torch.Tensor | None] = []
    at_base = bool(
        torch.equal(
            coordinated_weights.detach().cpu(),
            torch.tensor(base_solution.weights, dtype=coordinated_weights.dtype),
        )
    )
    for index in range(head_count):
        state_component = _g5_anchored_private_component(
            state_head_state_gradients[index],
            weight=coordinated_weights[1],
            base_weight=base_solution.weights[1],
            normalized_scale=normalized_scales[1],
            base_scale=state_base_scale,
        )
        physics_component = _g5_anchored_private_component(
            state_head_physics_gradients[index],
            weight=coordinated_weights[2],
            base_weight=base_solution.weights[2],
            normalized_scale=normalized_scales[2],
            base_scale=physics_base_scale,
        )
        combined = state_component
        if physics_component is not None:
            combined = physics_component if combined is None else combined + physics_component
        base_gradient = base_state_head_gradients[index]
        if combined is not None and base_gradient is not None and at_base:
            base_value = base_gradient.detach().float().to(combined.device)
            combined = combined + (base_value - combined).detach()
        head_result.append(combined)
    return tuple(lora_result), tuple(head_result)


def differentiable_clip_grad_norm(
    parameters: Sequence[torch.nn.Parameter],
    gradients: Sequence[torch.Tensor | None],
    max_norm: float,
) -> tuple[GradientTuple, torch.Tensor, torch.Tensor]:
    """按真实全局二范数语义裁剪梯度，但保留对协调权重的导数。"""
    if len(parameters) != len(gradients):
        raise GameTrainingError("参数与待裁剪梯度数量不一致")
    if not math.isfinite(max_norm) or max_norm <= 0.0:
        raise GameTrainingError("梯度裁剪上限必须为有限正数")
    cast_gradients: list[torch.Tensor | None] = []
    norms = []
    for parameter, gradient in zip(parameters, gradients, strict=True):
        if gradient is None:
            cast_gradients.append(None)
            continue
        if gradient.shape != parameter.shape or not bool(torch.isfinite(gradient).all().item()):
            raise GameTrainingError("G5 跟随梯度形状错误或包含非有限值")
        value = gradient.to(device=parameter.device, dtype=parameter.dtype)
        cast_gradients.append(value)
        norm_value = value if value.dtype == torch.float64 else value.float()
        norms.append(torch.linalg.vector_norm(norm_value, 2.0))
    if not norms:
        raise GameTrainingError("G5 跟随响应没有可更新梯度")
    reference_device = norms[0].device
    total_norm = torch.linalg.vector_norm(
        torch.stack([value.to(reference_device) for value in norms]), 2.0
    )
    clip_coefficient = max_norm / (total_norm + 1e-6)
    clipped_coefficient = torch.clamp(clip_coefficient, max=1.0)
    clipped = tuple(
        (
            None
            if value is None
            else value * clipped_coefficient.to(device=value.device, dtype=value.dtype)
        )
        for value in cast_gradients
    )
    return clipped, total_norm, clipped_coefficient


def _optimizer_parameter_groups(
    optimizer: torch.optim.Optimizer,
) -> dict[int, Mapping[str, object]]:
    groups: dict[int, Mapping[str, object]] = {}
    for group in optimizer.param_groups:
        for parameter in group["params"]:
            identifier = id(parameter)
            if identifier in groups:
                raise GameTrainingError("同一参数重复出现在 AdamW 参数组中")
            groups[identifier] = group
    return groups


def _optimizer_step_value(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, torch.Tensor):
        return int(value.detach().item())
    return int(value)


def functional_adamw_step(
    parameters: Sequence[torch.nn.Parameter],
    gradients: Sequence[torch.Tensor | None],
    optimizer: torch.optim.Optimizer,
) -> FunctionalAdamWStep:
    """从正式优化器参数组和状态计算一次无副作用 AdamW 响应。"""
    if len(parameters) != len(gradients):
        raise GameTrainingError("函数式 AdamW 的参数与梯度数量不一致")
    groups = _optimizer_parameter_groups(optimizer)
    next_parameters: list[torch.Tensor] = []
    next_exp_avgs: list[torch.Tensor | None] = []
    next_exp_avg_sqs: list[torch.Tensor | None] = []
    next_steps: list[int] = []
    updated: list[bool] = []
    for parameter, gradient in zip(parameters, gradients, strict=True):
        group = groups.get(id(parameter))
        if group is None:
            raise GameTrainingError("函数式 AdamW 参数不属于正式优化器")
        if bool(group.get("amsgrad", False)) or bool(group.get("maximize", False)):
            raise GameTrainingError("G5 只支持标准非 AMSGrad、非 maximize 的 AdamW")
        state = optimizer.state.get(parameter, {})
        current_step = _optimizer_step_value(state.get("step"))
        if gradient is None:
            next_parameters.append(parameter)
            next_exp_avgs.append(None)
            next_exp_avg_sqs.append(None)
            next_steps.append(current_step)
            updated.append(False)
            continue
        if gradient.shape != parameter.shape or gradient.dtype != parameter.dtype:
            raise GameTrainingError("函数式 AdamW 梯度必须与参数同形同精度")
        beta1, beta2 = (float(value) for value in group["betas"])
        learning_rate = float(group["lr"])
        epsilon = float(group["eps"])
        weight_decay = float(group["weight_decay"])
        step = current_step + 1
        exp_avg = state.get("exp_avg")
        exp_avg_sq = state.get("exp_avg_sq")
        if exp_avg is None:
            exp_avg = torch.zeros_like(parameter)
        if exp_avg_sq is None:
            exp_avg_sq = torch.zeros_like(parameter)
        next_exp_avg = exp_avg.lerp(gradient, 1.0 - beta1)
        next_exp_avg_sq = exp_avg_sq.mul(beta2).addcmul(
            gradient,
            gradient,
            value=1.0 - beta2,
        )
        bias_correction1 = 1.0 - beta1**step
        bias_correction2_sqrt = math.sqrt(1.0 - beta2**step)
        exact_square_root = next_exp_avg_sq.sqrt()
        finite_derivative_square_root = next_exp_avg_sq.clamp_min(
            torch.finfo(next_exp_avg_sq.dtype).tiny
        ).sqrt()
        square_root = (
            finite_derivative_square_root
            + (exact_square_root - finite_derivative_square_root).detach()
        )
        denominator = square_root / bias_correction2_sqrt + epsilon
        next_parameter = (
            parameter * (1.0 - learning_rate * weight_decay)
            - (learning_rate / bias_correction1) * next_exp_avg / denominator
        )
        if not bool(torch.isfinite(next_parameter).all().item()):
            raise GameTrainingError("函数式 AdamW 响应包含非有限参数")
        next_parameters.append(next_parameter)
        next_exp_avgs.append(next_exp_avg)
        next_exp_avg_sqs.append(next_exp_avg_sq)
        next_steps.append(step)
        updated.append(True)
    return FunctionalAdamWStep(
        parameters=tuple(next_parameters),
        exp_avgs=tuple(next_exp_avgs),
        exp_avg_sqs=tuple(next_exp_avg_sqs),
        steps=tuple(next_steps),
        updated=tuple(updated),
    )


def commit_functional_adamw_step(
    parameters: Sequence[torch.nn.Parameter],
    optimizer: torch.optim.Optimizer,
    response: FunctionalAdamWStep,
) -> None:
    """原子提交已用于主导方评价的同一组参数与 AdamW 状态。"""
    if not (
        len(parameters)
        == len(response.parameters)
        == len(response.exp_avgs)
        == len(response.exp_avg_sqs)
        == len(response.steps)
        == len(response.updated)
    ):
        raise GameTrainingError("函数式 AdamW 提交载体长度不一致")
    groups = _optimizer_parameter_groups(optimizer)
    with torch.no_grad():
        for parameter, value, exp_avg, exp_avg_sq, step, updated in zip(
            parameters,
            response.parameters,
            response.exp_avgs,
            response.exp_avg_sqs,
            response.steps,
            response.updated,
            strict=True,
        ):
            if not updated:
                parameter.grad = None
                continue
            if exp_avg is None or exp_avg_sq is None:
                raise GameTrainingError("函数式 AdamW 更新缺少动量状态")
            parameter.copy_(value.detach())
            state = optimizer.state[parameter]
            previous_step = state.get("step")
            if isinstance(previous_step, torch.Tensor):
                state["step"] = torch.tensor(
                    float(step),
                    dtype=previous_step.dtype,
                    device=previous_step.device,
                )
            else:
                group = groups[id(parameter)]
                step_device = (
                    parameter.device
                    if bool(group.get("capturable", False)) or bool(group.get("fused", False))
                    else torch.device("cpu")
                )
                state["step"] = torch.tensor(float(step), dtype=torch.float32, device=step_device)
            state["exp_avg"] = exp_avg.detach().clone()
            state["exp_avg_sq"] = exp_avg_sq.detach().clone()
            parameter.grad = None


def physics_batch_valid_fraction(records: Sequence[Mapping[str, object]]) -> float:
    """计算容量严格为正、输入有限且边界锚点有效的样本比例。"""
    if not records:
        raise GameTrainingError("物理批次不得为空")
    valid = 0
    for record in records:
        try:
            prepare_state_record(record)
        except (TypeError, ValueError):
            continue
        valid += 1
    return valid / len(records)


def _state_and_physics_gradients(
    model: object,
    state_head: ContinuousQueueStateHead,
    tokenizer: object,
    lora_parameters: Sequence[torch.nn.Parameter],
    state_head_parameters: Sequence[torch.nn.Parameter],
    records: Sequence[Mapping[str, object]],
    *,
    max_length: int,
    device: torch.device,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> tuple[float, float, GradientTuple, GradientTuple, GradientTuple, GradientTuple]:
    if not records:
        empty_lora = tuple(None for _ in lora_parameters)
        empty_head = tuple(None for _ in state_head_parameters)
        return 0.0, 0.0, empty_lora, empty_lora, empty_head, empty_head
    batch = _state_batch(
        records,
        tokenizer,
        max_length,
        device,
        include_fluxes=True,
        state_masks=state_masks,
    )
    outputs = model(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        output_hidden_states=True,
        return_dict=True,
    )
    hidden = select_last_token_hidden(outputs.hidden_states[-1], batch["attention_mask"])
    predicted = state_head(hidden)
    state_loss = masked_state_target_loss(
        predicted,
        batch["state_targets"],
        batch["state_mask"],
    )
    residual = queue_balance_residual(
        predicted,
        batch["scale"],
        batch["capacity"],
        batch["received"],
        batch["dequeued"],
        batch["dropped_before"],
        batch["dropped_after"],
    )
    physics_loss = residual.square().mean()
    parameters = tuple(lora_parameters) + tuple(state_head_parameters)
    state_gradients = torch.autograd.grad(
        state_loss,
        parameters,
        retain_graph=True,
        allow_unused=True,
    )
    physics_gradients = torch.autograd.grad(
        physics_loss,
        parameters,
        allow_unused=True,
    )
    boundary = len(lora_parameters)
    return (
        float(state_loss.detach().item()),
        float(physics_loss.detach().item()),
        tuple(
            None if value is None else value.detach().float()
            for value in state_gradients[:boundary]
        ),
        tuple(
            None if value is None else value.detach().float()
            for value in physics_gradients[:boundary]
        ),
        tuple(
            None if value is None else value.detach().float()
            for value in state_gradients[boundary:]
        ),
        tuple(
            None if value is None else value.detach().float()
            for value in physics_gradients[boundary:]
        ),
    )


def _assert_g5_split_independence(
    training_records: Sequence[Mapping[str, object]],
    validation_records: Sequence[Mapping[str, object]],
    *,
    name: str,
) -> None:
    training_ids = {
        str(record["sample_id"]) for record in training_records if "sample_id" in record
    }
    validation_ids = {
        str(record["sample_id"]) for record in validation_records if "sample_id" in record
    }
    overlap = sorted(training_ids.intersection(validation_ids))
    if overlap:
        raise GameTrainingError(f"G5 {name}训练与验证样本重叠：{overlap[0]}")


def _g5_module_call(
    module: torch.nn.Module,
    parameters: Mapping[str, torch.Tensor] | None,
    args: tuple[object, ...],
    kwargs: Mapping[str, object] | None = None,
) -> object:
    if parameters is None:
        return module(*args, **dict(kwargs or {}))
    return functional_call(
        module,
        dict(parameters),
        args,
        dict(kwargs or {}),
        strict=False,
    )


def _g5_leader_losses(
    model: torch.nn.Module,
    state_head: ContinuousQueueStateHead,
    *,
    generation_batch: Mapping[str, torch.Tensor],
    state_batch: Mapping[str, torch.Tensor],
    model_parameters: Mapping[str, torch.Tensor] | None = None,
    state_head_parameters: Mapping[str, torch.Tensor] | None = None,
) -> G5LeaderLosses:
    generation_outputs = _g5_module_call(
        model,
        model_parameters,
        (),
        {**generation_batch, "return_dict": True},
    )
    generation_loss = generation_outputs.loss.float()
    state_outputs = _g5_module_call(
        model,
        model_parameters,
        (),
        {
            "input_ids": state_batch["input_ids"],
            "attention_mask": state_batch["attention_mask"],
            "output_hidden_states": True,
            "return_dict": True,
        },
    )
    hidden = select_last_token_hidden(
        state_outputs.hidden_states[-1], state_batch["attention_mask"]
    )
    predicted = _g5_module_call(
        state_head,
        state_head_parameters,
        (hidden,),
    )
    if (
        not isinstance(predicted, torch.Tensor)
        or predicted.shape != state_batch["state_targets"].shape
    ):
        raise GameTrainingError("G5 虚拟状态预测形状错误")
    unobserved = ~state_batch["state_mask"].bool()
    expected = torch.ones_like(unobserved)
    expected[:, 0] = False
    if not bool(torch.equal(unobserved, expected)):
        raise GameTrainingError("G5 验证状态掩码必须只选择第 1 至第 4 个锚点")
    state_unobserved = (
        (predicted.float() - state_batch["state_targets"].float())
        .square()
        .masked_select(unobserved)
        .mean()
    )
    residual = queue_balance_residual(
        predicted,
        state_batch["scale"],
        state_batch["capacity"],
        state_batch["received"],
        state_batch["dequeued"],
        state_batch["dropped_before"],
        state_batch["dropped_after"],
    )
    physics_loss = residual.square().mean()
    losses = (generation_loss, state_unobserved, physics_loss)
    if not all(bool(torch.isfinite(value).item()) for value in losses):
        raise GameTrainingError("G5 主导方验证损失包含非有限值")
    return G5LeaderLosses(*losses)


def _gradient_cosine_proxy(
    validation_gradients: Sequence[torch.Tensor | None],
    training_gradients: Sequence[torch.Tensor | None],
) -> float:
    validation_norm = _optional_gradient_norm("验证生成", validation_gradients)
    training_norm = _optional_gradient_norm("辅助训练", training_gradients)
    if validation_norm == 0.0 or training_norm == 0.0:
        return 0.0
    value = _gradient_dot(validation_gradients, training_gradients) / (
        validation_norm * training_norm
    )
    return max(-1.0, min(1.0, float(value)))


def _gradient_sequence_norm(gradients: Sequence[torch.Tensor | None]) -> float:
    return _optional_gradient_norm("协调器反应", gradients)


def record_game_step_metrics(
    path: Path,
    swanlab: object,
    *,
    step: int,
    metrics: Mapping[str, float],
) -> None:
    """同步写入本地 JSONL 并调用 SwanLab 在线记录。"""
    missing = sorted(set(GAME_STEP_METRIC_KEYS).difference(metrics))
    if missing:
        raise GameTrainingError("协调训练逐步指标缺失：" + ", ".join(missing))
    if any(key in metrics for key in G5_STEP_METRIC_KEYS):
        missing_g5 = sorted(set(G5_STEP_METRIC_KEYS).difference(metrics))
        if missing_g5:
            raise GameTrainingError("G5 逐步指标缺失：" + ", ".join(missing_g5))
    normalized = {key: float(value) for key, value in metrics.items()}
    if not all(math.isfinite(value) for value in normalized.values()):
        raise GameTrainingError("协调训练逐步指标必须全部为有限数值")
    with Path(path).open("a", encoding="utf-8") as target:
        target.write(json.dumps({"step": step, "metrics": normalized}, sort_keys=True) + "\n")
    swanlab.log(normalized, step=step)


def _build_settings(
    raw: Mapping[str, object],
    *,
    variant: str,
    output_dir: Path,
    max_steps: int,
    validation_limit: int | None,
    simplex_resolution: float = SIMPLEX_RESOLUTION,
    generation_floor: float = GENERATION_FLOOR,
) -> GameTrainingSettings:
    data = raw.get("training")
    if not isinstance(data, Mapping):
        raise GameTrainingError("配置缺少 training")
    required = (
        "generation_train_file",
        "generation_validation_file",
        "physics_train_file",
        "physics_validation_file",
        "physics_test_file",
        "learning_rate",
        "generation_batch_size",
        "gradient_accumulation_steps",
        "physics_batch_size",
        "validation_batch_size",
        "lambda_state",
        "lambda_physics",
        "max_grad_norm",
    )
    missing = [name for name in required if name not in data]
    if missing:
        raise GameTrainingError("缺少协调训练配置：" + ", ".join(missing))
    settings = GameTrainingSettings(
        variant=_variant_name(variant),
        output_dir=Path(output_dir),
        generation_train_file=Path(str(data["generation_train_file"])),
        generation_validation_file=Path(str(data["generation_validation_file"])),
        physics_train_file=Path(str(data["physics_train_file"])),
        physics_validation_file=Path(str(data["physics_validation_file"])),
        physics_test_file=Path(str(data["physics_test_file"])),
        learning_rate=float(data["learning_rate"]),
        generation_batch_size=int(data["generation_batch_size"]),
        gradient_accumulation_steps=int(data["gradient_accumulation_steps"]),
        physics_batch_size=int(data["physics_batch_size"]),
        validation_batch_size=int(data["validation_batch_size"]),
        max_steps=int(max_steps),
        state_supervision_mode=str(data.get("state_supervision_mode", "dense")).lower(),
        lambda_state=float(data["lambda_state"]),
        lambda_physics=float(data["lambda_physics"]),
        max_grad_norm=float(data["max_grad_norm"]),
        validation_limit=validation_limit,
        simplex_resolution=float(simplex_resolution),
        generation_floor=float(generation_floor),
    )
    positive = (
        settings.learning_rate,
        settings.generation_batch_size,
        settings.gradient_accumulation_steps,
        settings.physics_batch_size,
        settings.validation_batch_size,
        settings.max_steps,
        settings.max_grad_norm,
        settings.simplex_resolution,
    )
    if any(not math.isfinite(float(value)) or value <= 0 for value in positive):
        raise GameTrainingError("批量、步数、学习率、梯度上限和网格分辨率必须为有限正数")
    if settings.effective_generation_batch_size != 16:
        raise GameTrainingError("生成有效批量大小必须固定为 16")
    if settings.physics_batch_size != 4:
        raise GameTrainingError("物理批量大小必须固定为 4")
    if settings.max_steps not in {2, 202}:
        raise GameTrainingError("协调训练只允许 2 步冒烟或 202 步正式预算")
    allowed_state_supervision_modes = (
        {STATE_SUPERVISION_MODE, "anchor0_plus_one"}
        if settings.variant == "G4R"
        else {STATE_SUPERVISION_MODE}
    )
    if settings.state_supervision_mode not in allowed_state_supervision_modes:
        if settings.variant == "G4R":
            raise GameTrainingError("G4R 只允许 anchor0_only 或 anchor0_plus_one 状态监督")
        raise GameTrainingError("G2/G3/G4/G5/G5-STOP-RESPONSE 必须使用 anchor0_only 状态监督")
    if settings.lambda_state != 1.0 or settings.lambda_physics != 0.01:
        raise GameTrainingError("状态头私有目标权重必须沿用 lambda_state=1.0、lambda_physics=0.01")
    if settings.simplex_resolution != SIMPLEX_RESOLUTION:
        raise GameTrainingError("G2-G5 单纯形分辨率必须固定为 0.02")
    if settings.generation_floor != GENERATION_FLOOR:
        raise GameTrainingError("G4 生成边际底线必须固定为 0.95")
    if validation_limit is not None and validation_limit <= 0:
        raise GameTrainingError("验证样本上限必须大于零")
    return settings


def _tracking_settings(raw: Mapping[str, object], run_name: str, variant: str) -> TrackingSettings:
    tracking = raw.get("tracking")
    if not isinstance(tracking, Mapping):
        raise GameTrainingError("配置缺少 tracking")
    tags = list(tracking.get("tags", ()))
    for tag in ("game-coordination", variant.lower()):
        if tag not in tags:
            tags.append(tag)
    return TrackingSettings.from_mapping(
        {
            **tracking,
            "run_name": run_name,
            "description": f"Qwen3-1.7B {variant} 三目标博弈协调训练",
            "tags": tags,
        }
    )


def _write_state_mask(
    path: Path,
    masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
    *,
    mode: str,
) -> None:
    _write_json(
        path,
        {
            "schema_version": "flow_probe_state_mask_v1",
            "mode": mode,
            "samples": [
                {"sample_id": sample_id, "mask": list(masks[sample_id])}
                for sample_id in sorted(masks)
            ],
        },
    )


def _write_sample_order(
    path: Path,
    generation_schedule: Sequence[Sequence[int]],
    physics_schedule: Sequence[Sequence[int]],
    generation_records: Sequence[Mapping[str, object]],
    physics_records: Sequence[Mapping[str, object]],
    *,
    accumulation_steps: int,
    generation_validation_schedule: Sequence[Sequence[int]] | None = None,
    physics_validation_schedule: Sequence[Sequence[int]] | None = None,
    generation_validation_records: Sequence[Mapping[str, object]] | None = None,
    physics_validation_records: Sequence[Mapping[str, object]] | None = None,
) -> None:
    validation_values = (
        generation_validation_schedule,
        physics_validation_schedule,
        generation_validation_records,
        physics_validation_records,
    )
    includes_validation = all(value is not None for value in validation_values)
    if any(value is not None for value in validation_values) and not includes_validation:
        raise GameTrainingError("G5 验证样本顺序参数必须同时提供")
    if includes_validation and (
        len(generation_validation_schedule) != len(physics_schedule)  # type: ignore[arg-type]
        or len(physics_validation_schedule) != len(physics_schedule)  # type: ignore[arg-type]
    ):
        raise GameTrainingError("G5 训练与验证样本顺序步数不一致")

    steps = []
    for step in range(1, len(physics_schedule) + 1):
        record: dict[str, object] = {
            "step": step,
            "generation_microbatches": [
                {
                    "indices": list(indices),
                    "sample_ids": [
                        str(generation_records[index].get("sample_id", f"index:{index}"))
                        for index in indices
                    ],
                }
                for indices in generation_schedule[
                    (step - 1) * accumulation_steps : step * accumulation_steps
                ]
            ],
            "physics": {
                "indices": list(physics_schedule[step - 1]),
                "sample_ids": [
                    str(physics_records[index].get("sample_id", f"index:{index}"))
                    for index in physics_schedule[step - 1]
                ],
            },
        }
        if includes_validation:
            generation_indices = generation_validation_schedule[step - 1]  # type: ignore[index]
            physics_indices = physics_validation_schedule[step - 1]  # type: ignore[index]
            record["generation_validation"] = {
                "indices": list(generation_indices),
                "sample_ids": [
                    str(
                        generation_validation_records[index].get(  # type: ignore[index]
                            "sample_id", f"index:{index}"
                        )
                    )
                    for index in generation_indices
                ],
            }
            record["physics_validation"] = {
                "indices": list(physics_indices),
                "sample_ids": [
                    str(
                        physics_validation_records[index].get(  # type: ignore[index]
                            "sample_id", f"index:{index}"
                        )
                    )
                    for index in physics_indices
                ],
            }
        steps.append(record)
    _write_json(
        path,
        {
            "schema_version": (
                "flow_probe_game_sample_order_g5_v1"
                if includes_validation
                else "flow_probe_game_sample_order_v1"
            ),
            "steps": steps,
        },
    )


def _training_snapshot(
    raw: Mapping[str, object],
    probe: ProbeConfig,
    settings: GameTrainingSettings,
    tracking: TrackingSettings,
) -> dict[str, object]:
    snapshot = {
        "schema_version": (
            "flow_probe_game_coordination_g5_v1"
            if settings.uses_g5_response
            else "flow_probe_game_coordination_v1"
        ),
        "probe": {
            "model_id": probe.model_id,
            "feature_view": probe.feature_view,
            "seed": probe.seed,
            "max_input_length": probe.max_input_length,
            "max_new_tokens": probe.max_new_tokens,
            "lora_rank": probe.lora_rank,
            "lora_alpha": probe.lora_alpha,
            "lora_dropout": probe.lora_dropout,
        },
        "training": {
            **dict(raw["training"]),
            "variant": settings.variant,
            "output_dir": str(settings.output_dir),
            "max_steps": settings.max_steps,
            "effective_generation_batch_size": settings.effective_generation_batch_size,
            "validation_limit": settings.validation_limit,
            "simplex_resolution": settings.simplex_resolution,
            "generation_floor": settings.generation_floor,
            "asymmetric_powers": list(settings.asymmetric_powers),
            "shared_gradient_scale": "generation_gradient_norm",
        },
        "tracking": {
            "workspace": tracking.workspace,
            "project": tracking.project,
            "run_name": tracking.run_name,
            "mode": tracking.mode,
            "tags": list(tracking.tags),
        },
    }
    if settings.uses_g5_response:
        snapshot["g5"] = {
            "coordinator_weight_shape": [2, 7],
            "coordinator_bias_shape": [2],
            "coordinator_learning_rate": settings.coordinator_learning_rate,
            "coordinator_weight_decay": 0.0,
            "coordinator_betas": [0.9, 0.999],
            "coordinator_epsilon": 1e-8,
            "response_unroll_steps": 1,
            "response_optimizer": "AdamW",
            "stop_response": settings.stops_g5_response,
            "generation_validation_seed_offset": G5_GENERATION_VALIDATION_SEED_OFFSET,
            "physics_validation_seed_offset": G5_PHYSICS_VALIDATION_SEED_OFFSET,
        }
    return snapshot


def _step_metrics(
    *,
    variant: str,
    generation_loss: float,
    state_loss: float,
    physics_loss: float,
    diagnostics: GameGradientDiagnostics,
    lora_gradient_norm: float,
    state_head_gradient_norm: float,
    learning_rate: float,
    throughput: float,
    peak_memory_mib: float,
) -> dict[str, float]:
    solution = diagnostics.solution
    total_loss = generation_loss
    if solution.accepts_state:
        total_loss += state_loss
    if solution.accepts_physics:
        total_loss += 0.01 * physics_loss
    return {
        "train/total_loss": total_loss,
        "train/generation_loss": generation_loss,
        "train/state_loss": state_loss,
        "train/physics_loss": physics_loss,
        "train/generation_gradient_norm": diagnostics.generation_norm,
        "train/state_gradient_norm": diagnostics.state_norm,
        "train/physics_gradient_norm": diagnostics.physics_norm,
        "train/lora_gradient_norm": lora_gradient_norm,
        "train/state_head_gradient_norm": state_head_gradient_norm,
        "train/cosine_generation_state": diagnostics.gram[0][1],
        "train/cosine_generation_physics": diagnostics.gram[0][2],
        "train/cosine_state_physics": diagnostics.gram[1][2],
        "coordination/objective": solution.objective,
        "coordination/weight_generation": solution.weights[0],
        "coordination/weight_state": solution.weights[1],
        "coordination/weight_physics": solution.weights[2],
        "coordination/margin_generation": solution.margins[0],
        "coordination/margin_state": solution.margins[1],
        "coordination/margin_physics": solution.margins[2],
        "coordination/physics_valid_fraction": diagnostics.physics_valid_fraction,
        "coordination/physics_reliability": diagnostics.physics_reliability,
        "coordination/generation_veto": float(solution.generation_vetoed),
        "coordination/state_rejected": float(not solution.accepts_state),
        "coordination/physics_rejected": float(not solution.accepts_physics),
        "coordination/fallback_to_generation": float(solution.fallback_to_generation),
        "coordination/private_state_anchor_forced": float(_variant_name(variant) == "G4R"),
        "train/learning_rate": learning_rate,
        "train/optimizer_updates": 1.0,
        "train/throughput_samples_per_second": throughput,
        "train/peak_gpu_memory_mib": peak_memory_mib,
    }


def _finite_gradient_norm(
    gradients: Sequence[torch.Tensor | None],
) -> tuple[bool, float]:
    total = 0.0
    for gradient in gradients:
        if gradient is None:
            continue
        value = gradient.detach().float()
        if not bool(torch.isfinite(value).all().item()):
            return False, 0.0
        total += float(value.square().sum().item())
    return math.isfinite(total), math.sqrt(total) if math.isfinite(total) else 0.0


def _run_g5_response_step(
    *,
    model: torch.nn.Module,
    state_head: ContinuousQueueStateHead,
    tokenizer: object,
    lora_named_parameters: Sequence[tuple[str, torch.nn.Parameter]],
    state_head_named_parameters: Sequence[tuple[str, torch.nn.Parameter]],
    model_optimizer: torch.optim.Optimizer,
    coordinator: G5Coordinator,
    coordinator_optimizer: torch.optim.Optimizer,
    generation_gradients: Sequence[torch.Tensor | None],
    state_lora_gradients: Sequence[torch.Tensor | None],
    physics_lora_gradients: Sequence[torch.Tensor | None],
    state_head_state_gradients: Sequence[torch.Tensor | None],
    state_head_physics_gradients: Sequence[torch.Tensor | None],
    base_diagnostics: GameGradientDiagnostics,
    base_lora_gradients: Sequence[torch.Tensor | None],
    base_state_head_gradients: Sequence[torch.Tensor | None],
    generation_validation_records: Sequence[Mapping[str, object]],
    generation_validation_indices: Sequence[int],
    physics_validation_records: Sequence[Mapping[str, object]],
    physics_validation_indices: Sequence[int],
    validation_state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
    generation_loss: float,
    state_loss: float,
    physics_loss: float,
    settings: GameTrainingSettings,
    max_input_length: int,
    device: torch.device,
    step_started: float,
    valid_training_records: int,
    coordinator_updates_before: int,
    model_updates_before: int,
) -> tuple[dict[str, float], int]:
    lora_parameters = tuple(parameter for _, parameter in lora_named_parameters)
    state_head_parameters = tuple(parameter for _, parameter in state_head_named_parameters)
    diagnostics = build_g5_diagnostics(
        base_diagnostics.gram,
        physics_valid_fraction=base_diagnostics.physics_valid_fraction,
        physics_reliability=base_diagnostics.physics_reliability,
        base_solution=base_diagnostics.solution,
        device=device,
    )
    response = coordinator(diagnostics)
    coordination = coordinate_g5_response(
        base_diagnostics.gram,
        physics_reliability=base_diagnostics.physics_reliability,
        base_solution=base_diagnostics.solution,
        diagnostics=diagnostics,
        response=response,
        generation_floor=settings.generation_floor,
        stop_response=settings.stops_g5_response,
    )
    projection_jacobian_norm = g5_projection_jacobian_norm(coordination)
    lora_gradients, state_head_gradients = build_g5_follower_gradients(
        lora_parameters,
        state_head_parameters,
        generation_gradients=generation_gradients,
        state_lora_gradients=state_lora_gradients,
        physics_lora_gradients=physics_lora_gradients,
        state_head_state_gradients=state_head_state_gradients,
        state_head_physics_gradients=state_head_physics_gradients,
        base_lora_gradients=base_lora_gradients,
        base_state_head_gradients=base_state_head_gradients,
        base_diagnostics=base_diagnostics,
        coordinated_weights=coordination.coordinated_weights,
        lambda_state=settings.lambda_state,
        lambda_physics=settings.lambda_physics,
        stop_response=settings.stops_g5_response,
    )
    lora_gradient_norm = _optional_gradient_norm("G5 LoRA", lora_gradients)
    state_head_gradient_norm = _optional_gradient_norm("G5 状态头", state_head_gradients)
    trainable = tuple(lora_parameters) + tuple(state_head_parameters)
    follower_gradients = tuple(lora_gradients) + tuple(state_head_gradients)
    clipped_gradients, _, _ = differentiable_clip_grad_norm(
        trainable,
        follower_gradients,
        settings.max_grad_norm,
    )
    virtual_response = functional_adamw_step(
        trainable,
        clipped_gradients,
        model_optimizer,
    )

    generation_batch = _generation_batch(
        [generation_validation_records[index] for index in generation_validation_indices],
        tokenizer,
        max_input_length,
        device,
    )
    selected_validation_records = [
        physics_validation_records[index] for index in physics_validation_indices
    ]
    valid_validation_records = []
    for record in selected_validation_records:
        try:
            prepare_physics_record(record)
        except (TypeError, ValueError):
            continue
        valid_validation_records.append(record)
    if not valid_validation_records:
        raise GameTrainingError("G5 物理验证批次没有有效样本")
    state_batch = _state_batch(
        valid_validation_records,
        tokenizer,
        max_input_length,
        device,
        include_fluxes=True,
        state_masks=validation_state_masks,
    )
    virtual_lora = {
        name: virtual_response.parameters[index]
        for index, (name, _) in enumerate(lora_named_parameters)
    }
    head_boundary = len(lora_named_parameters)
    virtual_state_head = {
        name: virtual_response.parameters[head_boundary + index]
        for index, (name, _) in enumerate(state_head_named_parameters)
    }
    model_was_training = model.training
    state_head_was_training = state_head.training
    model.eval()
    state_head.eval()
    try:
        current_losses = _g5_leader_losses(
            model,
            state_head,
            generation_batch=generation_batch,
            state_batch=state_batch,
        )
        generation_denominator = current_losses.generation.detach().clamp_min(1e-12)
        state_denominator = current_losses.state_unobserved.detach().clamp_min(1e-12)
        physics_denominator = current_losses.physics.detach().clamp_min(1e-12)
        validation_generation_gradients = torch.autograd.grad(
            current_losses.generation,
            lora_parameters,
            allow_unused=True,
        )
        del current_losses
        virtual_losses = _g5_leader_losses(
            model,
            state_head,
            generation_batch=generation_batch,
            state_batch=state_batch,
            model_parameters=virtual_lora,
            state_head_parameters=virtual_state_head,
        )
    finally:
        model.train(model_was_training)
        state_head.train(state_head_was_training)

    generation_relative = virtual_losses.generation / generation_denominator
    state_relative = virtual_losses.state_unobserved / state_denominator
    physics_relative = virtual_losses.physics / physics_denominator
    leader_cost = (
        generation_relative
        + 0.5 * state_relative
        + (0.5 * base_diagnostics.physics_reliability * physics_relative)
    )
    if not bool(torch.isfinite(leader_cost).item()):
        raise GameTrainingError("G5 主导方代价非有限")
    proxy_state = _gradient_cosine_proxy(validation_generation_gradients, state_lora_gradients)
    proxy_physics = _gradient_cosine_proxy(validation_generation_gradients, physics_lora_gradients)

    coordinator_parameters = tuple(coordinator.parameters())
    coordinator_optimizer.zero_grad(set_to_none=True)
    auxiliary_active = bool(base_diagnostics.solution.active_auxiliaries)
    if settings.stops_g5_response or not auxiliary_active or not leader_cost.requires_grad:
        reaction_gradients: tuple[torch.Tensor | None, ...] = tuple(
            torch.zeros_like(parameter) for parameter in coordinator_parameters
        )
    else:
        reaction_gradients = torch.autograd.grad(
            leader_cost,
            coordinator_parameters,
            allow_unused=True,
        )
    reaction_finite, reaction_gradient_norm = _finite_gradient_norm(reaction_gradients)
    reaction_gate_failure = (
        auxiliary_active
        and not settings.stops_g5_response
        and (
            not reaction_finite or reaction_gradient_norm == 0.0 or projection_jacobian_norm == 0.0
        )
    )
    coordinator_updated = 0
    if (
        not settings.stops_g5_response
        and reaction_finite
        and reaction_gradient_norm > 0.0
        and projection_jacobian_norm > 0.0
    ):
        for parameter, gradient in zip(coordinator_parameters, reaction_gradients, strict=True):
            parameter.grad = (
                torch.zeros_like(parameter) if gradient is None else gradient.detach().to(parameter)
            )
        coordinator_optimizer.step()
        coordinator_updated = 1
    if settings.stops_g5_response and any(
        bool((parameter.detach() != 0).any().item()) for parameter in coordinator_parameters
    ):
        raise GameTrainingError("停止反应梯度时协调器参数必须保持逐位为零")

    commit_functional_adamw_step(trainable, model_optimizer, virtual_response)
    cumulative_model_updates = model_updates_before + 1
    cumulative_coordinator_updates = coordinator_updates_before + coordinator_updated
    effective_diagnostics = GameGradientDiagnostics(
        solution=coordination.solution,
        gram=base_diagnostics.gram,
        generation_norm=base_diagnostics.generation_norm,
        state_norm=base_diagnostics.state_norm,
        physics_norm=base_diagnostics.physics_norm,
        physics_valid_fraction=base_diagnostics.physics_valid_fraction,
        physics_reliability=base_diagnostics.physics_reliability,
    )
    metrics = _step_metrics(
        variant=settings.variant,
        generation_loss=generation_loss,
        state_loss=state_loss,
        physics_loss=physics_loss,
        diagnostics=effective_diagnostics,
        lora_gradient_norm=lora_gradient_norm,
        state_head_gradient_norm=state_head_gradient_norm,
        learning_rate=float(model_optimizer.param_groups[0]["lr"]),
        throughput=(settings.effective_generation_batch_size + valid_training_records)
        / (time.perf_counter() - step_started),
        peak_memory_mib=torch.cuda.max_memory_allocated() / (1024**2),
    )
    metrics.update(
        {
            "g5/base_weight_generation": base_diagnostics.solution.weights[0],
            "g5/base_weight_state": base_diagnostics.solution.weights[1],
            "g5/base_weight_physics": base_diagnostics.solution.weights[2],
            "g5/response_state": float(coordination.response[0].detach().item()),
            "g5/response_physics": float(coordination.response[1].detach().item()),
            "g5/selected_state": float(1 in coordination.selected_auxiliary_subset),
            "g5/selected_physics": float(2 in coordination.selected_auxiliary_subset),
            "g5/projection_distance": coordination.projection_distance,
            "g5/projection_jacobian_norm": projection_jacobian_norm,
            "g5/leader_cost": float(leader_cost.detach().item()),
            "g5/validation_generation_relative": float(generation_relative.detach().item()),
            "g5/validation_state_unobserved_relative": float(state_relative.detach().item()),
            "g5/validation_physics_relative": float(physics_relative.detach().item()),
            "g5/direct_gradient_norm": 0.0,
            "g5/reaction_gradient_norm": reaction_gradient_norm,
            "g5/reaction_proxy_state": proxy_state,
            "g5/reaction_proxy_physics": proxy_physics,
            "g5/reaction_gradient_finite": float(reaction_finite),
            "g5/reaction_gate_failure": float(reaction_gate_failure),
            "g5/stop_response": float(settings.stops_g5_response),
            "g5/model_optimizer_updates": float(cumulative_model_updates),
            "g5/state_head_updates": float(cumulative_model_updates),
            "g5/coordinator_optimizer_updates": float(cumulative_coordinator_updates),
            "g5/virtual_response_evaluations": float(cumulative_model_updates),
            "g5/validation_forwards": float(cumulative_model_updates),
            "g5/extra_model_optimizer_steps": 0.0,
        }
    )
    return metrics, coordinator_updated


def _mean(records: Sequence[Mapping[str, float]], key: str) -> float:
    return sum(float(record[key]) for record in records) / len(records)


def train_game_variant(
    probe: ProbeConfig,
    settings: GameTrainingSettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
) -> dict[str, object]:
    """执行一个隔离的 G2-G5 真实反向与优化器更新运行。"""
    variant = _variant_name(settings.variant)
    layout = create_game_run_layout(settings.output_dir)
    snapshot = _training_snapshot(raw_config, probe, settings, tracking)
    layout.config_snapshot.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=True), encoding="utf-8"
    )
    _write_json(layout.environment, _environment_manifest())
    _write_json(layout.input_sha256, _input_manifest(settings))  # type: ignore[arg-type]
    generation_train = _load_jsonl(settings.generation_train_file)
    generation_validation = _load_jsonl(settings.generation_validation_file)
    physics_train = _load_jsonl(settings.physics_train_file)
    physics_validation = _load_jsonl(settings.physics_validation_file)
    if settings.validation_limit is not None:
        generation_validation = generation_validation[: settings.validation_limit]
        physics_validation = physics_validation[: settings.validation_limit]
    train_state_masks = build_state_supervision_masks(
        physics_train, settings.state_supervision_mode, probe.seed
    )
    validation_state_masks = build_state_supervision_masks(
        physics_validation, settings.state_supervision_mode, probe.seed
    )
    generation_schedule = physics_sample_schedule(
        len(generation_train),
        batch_size=settings.generation_batch_size,
        steps=settings.max_steps * settings.gradient_accumulation_steps,
        seed=probe.seed,
    )
    physics_schedule = physics_sample_schedule(
        len(physics_train),
        batch_size=settings.physics_batch_size,
        steps=settings.max_steps,
        seed=probe.seed,
    )
    generation_validation_schedule = None
    physics_validation_schedule = None
    if settings.uses_g5_response:
        _assert_g5_split_independence(
            generation_train,
            generation_validation,
            name="生成",
        )
        _assert_g5_split_independence(
            physics_train,
            physics_validation,
            name="物理",
        )
        generation_validation_schedule = physics_sample_schedule(
            len(generation_validation),
            batch_size=settings.validation_batch_size,
            steps=settings.max_steps,
            seed=probe.seed + G5_GENERATION_VALIDATION_SEED_OFFSET,
        )
        physics_validation_schedule = physics_sample_schedule(
            len(physics_validation),
            batch_size=settings.validation_batch_size,
            steps=settings.max_steps,
            seed=probe.seed + G5_PHYSICS_VALIDATION_SEED_OFFSET,
        )
        _write_sample_order(
            layout.sample_order,
            generation_schedule,
            physics_schedule,
            generation_train,
            physics_train,
            accumulation_steps=settings.gradient_accumulation_steps,
            generation_validation_schedule=generation_validation_schedule,
            physics_validation_schedule=physics_validation_schedule,
            generation_validation_records=generation_validation,
            physics_validation_records=physics_validation,
        )
    else:
        _write_sample_order(
            layout.sample_order,
            generation_schedule,
            physics_schedule,
            generation_train,
            physics_train,
            accumulation_steps=settings.gradient_accumulation_steps,
        )
    _write_state_mask(
        layout.state_mask,
        train_state_masks,
        mode=settings.state_supervision_mode,
    )
    data_files = {
        "config_snapshot": layout.config_snapshot,
        "environment": layout.environment,
        "input_sha256": layout.input_sha256,
        "sample_order": layout.sample_order,
        "state_mask": layout.state_mask,
        "step_metrics": layout.step_metrics,
        "training_summary": layout.training_summary,
        "final_adapter": layout.final_adapter,
        "state_head": layout.state_head,
    }
    if settings.uses_g5_response:
        data_files["coordinator"] = layout.coordinator
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
        lora_named_parameters = tuple(
            (name, parameter)
            for name, parameter in model.named_parameters()
            if parameter.requires_grad and "lora_" in name
        )
        lora_parameters = tuple(parameter for _, parameter in lora_named_parameters)
        if not lora_parameters:
            raise GameTrainingError("未发现可训练 LoRA 参数")
        state_head_named_parameters = tuple(state_head.named_parameters())
        state_head_parameters = tuple(parameter for _, parameter in state_head_named_parameters)
        if settings.uses_g5_response:
            lora_parameter_count = sum(parameter.numel() for parameter in lora_parameters)
            if lora_parameter_count != G5_EXPECTED_LORA_PARAMETER_COUNT:
                raise GameTrainingError("G5 LoRA 参数元素数不满足 Qwen3-1.7B 固定契约")
            state_shapes = tuple(tuple(parameter.shape) for parameter in state_head_parameters)
            expected_state_shapes = ((5, model.config.hidden_size), (5,))
            if state_shapes != expected_state_shapes:
                raise GameTrainingError("G5 状态头必须严格包含 [5, d] 权重和 [5] 偏置")
        trainable = list(lora_parameters) + list(state_head_parameters)
        optimizer = torch.optim.AdamW(trainable, lr=settings.learning_rate)
        coordinator = None
        coordinator_optimizer = None
        if settings.uses_g5_response:
            coordinator = G5Coordinator().to(device=device)
            coordinator_optimizer = torch.optim.AdamW(
                coordinator.parameters(),
                lr=settings.coordinator_learning_rate,
                weight_decay=0.0,
            )
        model_optimizer_updates = 0
        coordinator_optimizer_updates = 0
        step_records: list[dict[str, float]] = []
        for step in range(1, settings.max_steps + 1):
            step_started = time.perf_counter()
            optimizer.zero_grad(set_to_none=True)
            micro_start = (step - 1) * settings.gradient_accumulation_steps
            generation_loss, generation_gradients = _generation_gradients(
                model,
                tokenizer,
                lora_parameters,
                generation_train,
                generation_schedule[
                    micro_start : micro_start + settings.gradient_accumulation_steps
                ],
                max_length=probe.max_input_length,
                device=device,
            )
            selected_records = [physics_train[index] for index in physics_schedule[step - 1]]
            valid_fraction = physics_batch_valid_fraction(selected_records)
            valid_records = []
            for record in selected_records:
                try:
                    prepare_physics_record(record)
                except (TypeError, ValueError):
                    continue
                valid_records.append(record)
            (
                state_loss,
                physics_loss,
                state_lora_gradients,
                physics_lora_gradients,
                state_head_state_gradients,
                state_head_physics_gradients,
            ) = _state_and_physics_gradients(
                model,
                state_head,
                tokenizer,
                lora_parameters,
                state_head_parameters,
                valid_records,
                max_length=probe.max_input_length,
                device=device,
                state_masks=train_state_masks,
            )
            if settings.uses_g5_response:
                if (
                    coordinator is None
                    or coordinator_optimizer is None
                    or generation_validation_schedule is None
                    or physics_validation_schedule is None
                ):
                    raise GameTrainingError("G5 协调器或验证样本顺序未初始化")
                base_diagnostics = apply_coordinated_lora_gradients(
                    lora_parameters,
                    generation_gradients=generation_gradients,
                    state_gradients=state_lora_gradients,
                    physics_gradients=physics_lora_gradients,
                    variant="G4",
                    physics_valid_fraction=valid_fraction,
                    resolution=settings.simplex_resolution,
                    generation_floor=settings.generation_floor,
                    asymmetric_powers=settings.asymmetric_powers,
                )
                apply_private_state_head_gradients(
                    state_head_parameters,
                    state_gradients=state_head_state_gradients,
                    physics_gradients=state_head_physics_gradients,
                    solution=base_diagnostics.solution,
                    lambda_state=settings.lambda_state,
                    lambda_physics=settings.lambda_physics,
                    physics_reliability=base_diagnostics.physics_reliability,
                    variant="G4",
                )
                base_lora_gradients = tuple(
                    None if parameter.grad is None else parameter.grad.detach().float().clone()
                    for parameter in lora_parameters
                )
                base_state_head_gradients = tuple(
                    None if parameter.grad is None else parameter.grad.detach().float().clone()
                    for parameter in state_head_parameters
                )
                metrics, coordinator_updates = _run_g5_response_step(
                    model=model,
                    state_head=state_head,
                    tokenizer=tokenizer,
                    lora_named_parameters=lora_named_parameters,
                    state_head_named_parameters=state_head_named_parameters,
                    model_optimizer=optimizer,
                    coordinator=coordinator,
                    coordinator_optimizer=coordinator_optimizer,
                    generation_gradients=generation_gradients,
                    state_lora_gradients=state_lora_gradients,
                    physics_lora_gradients=physics_lora_gradients,
                    state_head_state_gradients=state_head_state_gradients,
                    state_head_physics_gradients=state_head_physics_gradients,
                    base_diagnostics=base_diagnostics,
                    base_lora_gradients=base_lora_gradients,
                    base_state_head_gradients=base_state_head_gradients,
                    generation_validation_records=generation_validation,
                    generation_validation_indices=generation_validation_schedule[step - 1],
                    physics_validation_records=physics_validation,
                    physics_validation_indices=physics_validation_schedule[step - 1],
                    validation_state_masks=validation_state_masks,
                    generation_loss=generation_loss,
                    state_loss=state_loss,
                    physics_loss=physics_loss,
                    settings=settings,
                    max_input_length=probe.max_input_length,
                    device=device,
                    step_started=step_started,
                    valid_training_records=len(valid_records),
                    coordinator_updates_before=coordinator_optimizer_updates,
                    model_updates_before=model_optimizer_updates,
                )
                model_optimizer_updates += 1
                coordinator_optimizer_updates += coordinator_updates
            else:
                diagnostics = apply_coordinated_lora_gradients(
                    lora_parameters,
                    generation_gradients=generation_gradients,
                    state_gradients=state_lora_gradients,
                    physics_gradients=physics_lora_gradients,
                    variant=variant,
                    physics_valid_fraction=valid_fraction,
                    resolution=settings.simplex_resolution,
                    generation_floor=settings.generation_floor,
                    asymmetric_powers=settings.asymmetric_powers,
                )
                apply_private_state_head_gradients(
                    state_head_parameters,
                    state_gradients=state_head_state_gradients,
                    physics_gradients=state_head_physics_gradients,
                    solution=diagnostics.solution,
                    lambda_state=settings.lambda_state,
                    lambda_physics=settings.lambda_physics,
                    physics_reliability=diagnostics.physics_reliability,
                    variant=variant,
                )
                lora_gradient_norm = math.sqrt(
                    sum(
                        float(parameter.grad.detach().float().square().sum().item())
                        for parameter in lora_parameters
                        if parameter.grad is not None
                    )
                )
                state_head_gradient_norm = math.sqrt(
                    sum(
                        float(parameter.grad.detach().float().square().sum().item())
                        for parameter in state_head_parameters
                        if parameter.grad is not None
                    )
                )
                torch.nn.utils.clip_grad_norm_(trainable, settings.max_grad_norm)
                optimizer.step()
                model_optimizer_updates += 1
                elapsed = time.perf_counter() - step_started
                metrics = _step_metrics(
                    variant=variant,
                    generation_loss=generation_loss,
                    state_loss=state_loss,
                    physics_loss=physics_loss,
                    diagnostics=diagnostics,
                    lora_gradient_norm=lora_gradient_norm,
                    state_head_gradient_norm=state_head_gradient_norm,
                    learning_rate=float(optimizer.param_groups[0]["lr"]),
                    throughput=(settings.effective_generation_batch_size + len(valid_records))
                    / elapsed,
                    peak_memory_mib=torch.cuda.max_memory_allocated() / (1024**2),
                )
            record_game_step_metrics(layout.step_metrics, swanlab, step=step, metrics=metrics)
            step_records.append(metrics)
            print(json.dumps({"step": step, **metrics}, ensure_ascii=False, sort_keys=True))
        model.save_pretrained(layout.final_adapter)
        tokenizer.save_pretrained(layout.final_adapter)
        torch.save(
            {name: value.detach().cpu() for name, value in state_head.state_dict().items()},
            layout.state_head,
        )
        if model_optimizer_updates != settings.max_steps:
            raise GameTrainingError("模型有效更新次数与固定预算不一致")
        if settings.uses_g5_response:
            if coordinator is None or coordinator_optimizer is None:
                raise GameTrainingError("G5 协调器制品无法保存")
            torch.save(
                {
                    "schema_version": "flow_probe_g5_coordinator_v1",
                    "state_dict": {
                        name: value.detach().cpu()
                        for name, value in coordinator.state_dict().items()
                    },
                    "optimizer_state_dict": coordinator_optimizer.state_dict(),
                },
                layout.coordinator,
            )
        generation_validation_loss = _evaluate_generation(
            model,
            tokenizer,
            generation_validation,
            batch_size=settings.validation_batch_size,
            max_length=probe.max_input_length,
            device=device,
        )
        (
            validation_state_loss,
            validation_physics_loss,
            validation_state_observed_loss,
            validation_state_unobserved_loss,
        ) = _evaluate_state(
            model,
            state_head,
            tokenizer,
            physics_validation,
            batch_size=settings.validation_batch_size,
            max_length=probe.max_input_length,
            device=device,
            state_masks=validation_state_masks,
        )
        torch.cuda.synchronize()
        summary = {
            "schema_version": (
                "flow_probe_game_coordination_g5_v1"
                if settings.uses_g5_response
                else "flow_probe_game_coordination_v1"
            ),
            "status": "finished",
            "variant": variant,
            "seed": probe.seed,
            "max_steps": settings.max_steps,
            "model_id": probe.model_id,
            "optimizer_updates": model_optimizer_updates,
            "train_samples": len(generation_train),
            "physics_train_samples": len(physics_train),
            "generation_validation_samples": len(generation_validation),
            "physics_validation_samples": len(physics_validation),
            "effective_generation_batch_size": settings.effective_generation_batch_size,
            "state_supervision_mode": settings.state_supervision_mode,
            "state_mask_sha256": _state_mask_sha256(train_state_masks),
            "sample_order_sha256": _sha256(layout.sample_order),
            "simplex_resolution": settings.simplex_resolution,
            "generation_floor": settings.generation_floor,
            "asymmetric_powers": list(settings.asymmetric_powers),
            "coordination": {
                "fallback_steps": int(
                    sum(record["coordination/fallback_to_generation"] for record in step_records)
                ),
                "generation_veto_steps": int(
                    sum(record["coordination/generation_veto"] for record in step_records)
                ),
                "state_rejected_steps": int(
                    sum(record["coordination/state_rejected"] for record in step_records)
                ),
                "physics_rejected_steps": int(
                    sum(record["coordination/physics_rejected"] for record in step_records)
                ),
                "mean_physics_reliability": _mean(step_records, "coordination/physics_reliability"),
                "mean_weights": {
                    name: _mean(step_records, f"coordination/weight_{name}")
                    for name in ("generation", "state", "physics")
                },
                "mean_margins": {
                    name: _mean(step_records, f"coordination/margin_{name}")
                    for name in ("generation", "state", "physics")
                },
            },
            "validation": {
                "generation_loss": generation_validation_loss,
                "state_mse": validation_state_loss,
                "state_mse_observed": validation_state_observed_loss,
                "state_mse_unobserved": validation_state_unobserved_loss,
                "physics_residual_mse": validation_physics_loss,
            },
            "runtime_seconds": time.perf_counter() - started,
            "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            "trainable_lora_parameter_count": sum(
                parameter.numel() for parameter in lora_parameters
            ),
            "state_head_parameter_count": sum(
                parameter.numel() for parameter in state_head_parameters
            ),
        }
        if settings.uses_g5_response:
            summary["g5"] = {
                "coordinator_weight_shape": [2, 7],
                "coordinator_bias_shape": [2],
                "coordinator_learning_rate": settings.coordinator_learning_rate,
                "coordinator_weight_decay": 0.0,
                "coordinator_betas": [0.9, 0.999],
                "coordinator_epsilon": 1e-8,
                "stop_response": settings.stops_g5_response,
                "model_optimizer_updates": model_optimizer_updates,
                "state_head_updates": model_optimizer_updates,
                "coordinator_optimizer_updates": coordinator_optimizer_updates,
                "virtual_response_evaluations": settings.max_steps,
                "validation_forwards": settings.max_steps,
                "extra_model_optimizer_steps": 0,
                "reaction_gate_failure_steps": int(
                    sum(record["g5/reaction_gate_failure"] for record in step_records)
                ),
                "reaction_nonzero_steps": int(
                    sum(record["g5/reaction_gradient_norm"] > 0.0 for record in step_records)
                ),
                "mean_reaction_gradient_norm": _mean(step_records, "g5/reaction_gradient_norm"),
                "mean_projection_jacobian_norm": _mean(step_records, "g5/projection_jacobian_norm"),
                "mean_validation_relative": {
                    "generation": _mean(step_records, "g5/validation_generation_relative"),
                    "state_unobserved": _mean(
                        step_records, "g5/validation_state_unobserved_relative"
                    ),
                    "physics": _mean(step_records, "g5/validation_physics_relative"),
                },
            }
        _write_json(layout.training_summary, summary)
        swanlab.log(
            {
                "validation/generation_loss": generation_validation_loss,
                "validation/state_mse": validation_state_loss,
                "validation/state_mse_observed": validation_state_observed_loss,
                "validation/state_mse_unobserved": validation_state_unobserved_loss,
                "validation/physics_residual_mse": validation_physics_loss,
            },
            step=settings.max_steps + 1,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    validate_game_artifacts(layout, require_coordinator=settings.uses_g5_response)
    return json.loads(layout.artifact_manifest.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 G2-G5 三目标博弈协调训练")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--variant", choices=GAME_VARIANTS, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--max-steps", type=int, required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--validation-limit", type=int)
    parser.add_argument("--simplex-resolution", type=float, default=SIMPLEX_RESOLUTION)
    parser.add_argument("--generation-floor", type=float, default=GENERATION_FLOOR)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise GameTrainingError("配置根节点必须是映射")
    probe = ProbeConfig.from_mapping(raw["probe"])
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = _build_settings(
        raw,
        variant=args.variant,
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        validation_limit=args.validation_limit,
        simplex_resolution=args.simplex_resolution,
        generation_floor=args.generation_floor,
    )
    tracking = _tracking_settings(raw, args.run_name, settings.variant)
    manifest = train_game_variant(probe, settings, tracking, raw)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
