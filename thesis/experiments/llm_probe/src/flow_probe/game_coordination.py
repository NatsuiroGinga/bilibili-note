"""G2-G5 三目标梯度博弈的确定性协调器。"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations

import torch

from flow_probe.gradient_feasibility import (
    SIMPLEX_RESOLUTION,
    ObjectiveVector,
    _simplex_weights,
    direction_margins,
    validate_gram_matrix,
)

OBJECTIVE_NAMES = ("generation", "state", "physics")
ASYMMETRIC_POWERS: ObjectiveVector = (0.6, 0.2, 0.2)
GENERATION_FLOOR = 0.95
STRICT_MARGIN_TOLERANCE = 1e-12
G5_DIAGNOSTIC_SIZE = 7
G5_RESPONSE_SIZE = 2
G5_PROJECTION_TOLERANCE = 1e-9


class GameCoordinationError(ValueError):
    """协调输入或候选方向不满足数学契约。"""


@dataclass(frozen=True)
class CoordinationSolution:
    """协调方向、边际、效用及辅助目标接受状态。"""

    weights: ObjectiveVector
    margins: ObjectiveVector
    objective: float
    active_auxiliaries: tuple[str, ...]
    fallback_to_generation: bool
    generation_vetoed: bool = False

    @property
    def accepts_state(self) -> bool:
        return "state" in self.active_auxiliaries

    @property
    def accepts_physics(self) -> bool:
        return "physics" in self.active_auxiliaries


class G5Coordinator(torch.nn.Module):
    """以 G4 安全方向为零点的独立两输出协调器。"""

    def __init__(self) -> None:
        super().__init__()
        self.A = torch.nn.Parameter(torch.zeros((2, 7), dtype=torch.float32))
        self.b = torch.nn.Parameter(torch.zeros(2, dtype=torch.float32))

    def forward(self, diagnostics: torch.Tensor) -> torch.Tensor:
        if diagnostics.shape != (G5_DIAGNOSTIC_SIZE,):
            raise GameCoordinationError("G5 协调诊断必须为 float32[7]")
        if diagnostics.dtype != torch.float32:
            raise GameCoordinationError("G5 协调诊断必须使用 float32")
        if diagnostics.requires_grad:
            raise GameCoordinationError("G5 协调诊断必须停止梯度")
        if not bool(torch.isfinite(diagnostics).all().item()):
            raise GameCoordinationError("G5 协调诊断包含非有限值")
        response = self.A @ diagnostics + self.b
        if response.shape != (G5_RESPONSE_SIZE,) or not bool(torch.isfinite(response).all().item()):
            raise GameCoordinationError("G5 协调响应形状错误或包含非有限值")
        return response


@dataclass(frozen=True)
class G5CoordinationResult:
    """G5 的可微权重、离散选支和用于记录的协调解。"""

    base_solution: CoordinationSolution
    solution: CoordinationSolution
    diagnostics: torch.Tensor
    response: torch.Tensor
    base_weights: torch.Tensor
    coordinated_weights: torch.Tensor
    coordinated_margins: torch.Tensor
    selected_auxiliary_subset: tuple[int, ...]
    projection_distance: float


def _pure_generation_solution(
    gram: Sequence[Sequence[float]], *, generation_vetoed: bool = False
) -> CoordinationSolution:
    matrix = validate_gram_matrix(gram)
    weights: ObjectiveVector = (1.0, 0.0, 0.0)
    return CoordinationSolution(
        weights=weights,
        margins=direction_margins(matrix, weights),
        objective=0.0,
        active_auxiliaries=(),
        fallback_to_generation=True,
        generation_vetoed=generation_vetoed,
    )


def _validate_powers(powers: Sequence[float]) -> ObjectiveVector:
    if len(powers) != 3:
        raise GameCoordinationError("议价权必须包含生成、状态和物理三个分量")
    values = tuple(float(value) for value in powers)
    if not all(math.isfinite(value) and value > 0 for value in values):
        raise GameCoordinationError("议价权必须为有限正数")
    if abs(sum(values) - 1.0) > 1e-12:
        raise GameCoordinationError("议价权之和必须为 1")
    return values  # type: ignore[return-value]


def _stable_key_value(value: float) -> int:
    """按严格边际容差量化浮点键，归并数学等价候选的舍入噪声。"""
    return round(float(value) / STRICT_MARGIN_TOLERANCE)


def _bargaining_key(solution: CoordinationSolution) -> tuple[float, ...]:
    return (
        _stable_key_value(solution.objective),
        _stable_key_value(solution.margins[0]),
        _stable_key_value(solution.margins[1]),
        _stable_key_value(solution.margins[2]),
        solution.weights[0],
        solution.weights[1],
        solution.weights[2],
    )


def _solve_full_bargaining(
    gram: Sequence[Sequence[float]],
    powers: ObjectiveVector,
    resolution: float,
) -> CoordinationSolution:
    matrix = validate_gram_matrix(gram)
    candidates: list[CoordinationSolution] = []
    for weights in _simplex_weights(resolution):
        margins = direction_margins(matrix, weights)
        if any(margin <= STRICT_MARGIN_TOLERANCE for margin in margins):
            continue
        objective = sum(
            power * math.log(margin) for power, margin in zip(powers, margins, strict=True)
        )
        candidates.append(
            CoordinationSolution(
                weights=weights,
                margins=margins,
                objective=objective,
                active_auxiliaries=("state", "physics"),
                fallback_to_generation=False,
            )
        )
    if not candidates:
        return _pure_generation_solution(matrix)
    return max(candidates, key=_bargaining_key)


def solve_symmetric_bargaining(
    gram: Sequence[Sequence[float]], resolution: float = SIMPLEX_RESOLUTION
) -> CoordinationSolution:
    """G2：最大化三个严格正边际的等权对数和。"""
    return _solve_full_bargaining(gram, (1.0, 1.0, 1.0), resolution)


def solve_asymmetric_bargaining(
    gram: Sequence[Sequence[float]],
    powers: Sequence[float] = ASYMMETRIC_POWERS,
    resolution: float = SIMPLEX_RESOLUTION,
) -> CoordinationSolution:
    """G3：按固定议价权最大化三个严格正边际的加权对数和。"""
    return _solve_full_bargaining(gram, _validate_powers(powers), resolution)


def _active_sets(
    reliability: float, *, state_available: bool, physics_available: bool
) -> tuple[tuple[int, ...], ...]:
    result: list[tuple[int, ...]] = []
    if state_available and physics_available and reliability > STRICT_MARGIN_TOLERANCE:
        result.append((1, 2))
    if state_available:
        result.append((1,))
    if physics_available and reliability > STRICT_MARGIN_TOLERANCE:
        result.append((2,))
    return tuple(result)


def _protected_utility(
    margins: ObjectiveVector, active: tuple[int, ...], reliability: float
) -> float:
    powers = [1.0]
    values = [margins[0]]
    if 1 in active:
        powers.append(1.0)
        values.append(margins[1])
    if 2 in active:
        powers.append(reliability)
        values.append(margins[2])
    total_power = sum(powers)
    # 总议价权归一化后，不同辅助活跃集合的效用处于同一尺度。
    return (
        sum(power * math.log(value) for power, value in zip(powers, values, strict=True))
        / total_power
    )


def _protected_key(solution: CoordinationSolution) -> tuple[float, ...]:
    return (
        _stable_key_value(solution.objective),
        float(len(solution.active_auxiliaries)),
        _stable_key_value(solution.margins[0]),
        _stable_key_value(solution.margins[1]),
        _stable_key_value(solution.margins[2]),
        solution.weights[0],
        solution.weights[1],
        solution.weights[2],
    )


def solve_reliability_protected(
    gram: Sequence[Sequence[float]],
    reliability: float,
    generation_floor: float = GENERATION_FLOOR,
    resolution: float = SIMPLEX_RESOLUTION,
) -> CoordinationSolution:
    """G4：在生成边际底线内选择可靠性加权的辅助活跃集合。"""
    return solve_reliability_protected_available(
        gram,
        reliability,
        generation_floor,
        resolution,
        state_available=True,
        physics_available=True,
    )


def solve_reliability_protected_available(
    gram: Sequence[Sequence[float]],
    reliability: float,
    generation_floor: float = GENERATION_FLOOR,
    resolution: float = SIMPLEX_RESOLUTION,
    *,
    state_available: bool,
    physics_available: bool,
) -> CoordinationSolution:
    """在零梯度目标被拒绝后求解 G4，缺失方向绝不参与候选。"""
    matrix = validate_gram_matrix(gram)
    rho = float(reliability)
    floor = float(generation_floor)
    if not math.isfinite(rho) or rho < 0 or rho > 1:
        raise GameCoordinationError("物理可靠性必须位于 [0, 1]")
    if not math.isfinite(floor) or floor < 0 or floor > 1:
        raise GameCoordinationError("生成边际底线必须位于 [0, 1]")

    candidates: list[CoordinationSolution] = []
    unconstrained: list[CoordinationSolution] = []
    for active in _active_sets(
        rho,
        state_available=state_available,
        physics_available=physics_available,
    ):
        active_names = tuple(OBJECTIVE_NAMES[index] for index in active)
        for weights in _simplex_weights(resolution):
            if any(weights[index] <= 0 for index in active):
                continue
            if any(weights[index] != 0 for index in (1, 2) if index not in active):
                continue
            margins = direction_margins(matrix, weights)
            if margins[0] <= STRICT_MARGIN_TOLERANCE:
                continue
            if any(margins[index] <= STRICT_MARGIN_TOLERANCE for index in active):
                continue
            objective = _protected_utility(margins, active, rho)
            solution = CoordinationSolution(
                weights=weights,
                margins=margins,
                objective=objective,
                active_auxiliaries=active_names,
                fallback_to_generation=False,
            )
            unconstrained.append(solution)
            if margins[0] + STRICT_MARGIN_TOLERANCE >= floor:
                candidates.append(solution)

    generation_vetoed = (
        bool(unconstrained)
        and max(unconstrained, key=_protected_key).margins[0] + STRICT_MARGIN_TOLERANCE < floor
    )
    if not candidates:
        return _pure_generation_solution(matrix, generation_vetoed=generation_vetoed)
    selected = max(candidates, key=_protected_key)
    return CoordinationSolution(
        weights=selected.weights,
        margins=selected.margins,
        objective=selected.objective,
        active_auxiliaries=selected.active_auxiliaries,
        fallback_to_generation=False,
        generation_vetoed=generation_vetoed,
    )


def build_g5_diagnostics(
    gram: Sequence[Sequence[float]],
    *,
    physics_valid_fraction: float,
    physics_reliability: float,
    base_solution: CoordinationSolution,
    device: torch.device,
) -> torch.Tensor:
    """构造停止梯度的七维 G5 协调诊断。"""
    matrix = validate_gram_matrix(gram)
    valid_fraction = float(physics_valid_fraction)
    reliability = float(physics_reliability)
    if not math.isfinite(valid_fraction) or not 0.0 <= valid_fraction <= 1.0:
        raise GameCoordinationError("物理有效样本比例必须位于 [0, 1]")
    if not math.isfinite(reliability) or not 0.0 <= reliability <= 1.0:
        raise GameCoordinationError("物理可靠性必须位于 [0, 1]")
    values = (
        matrix[0][1],
        matrix[0][2],
        matrix[1][2],
        valid_fraction,
        reliability,
        base_solution.weights[1],
        base_solution.weights[2],
    )
    diagnostics = torch.tensor(values, dtype=torch.float32, device=device).detach()
    if diagnostics.shape != (G5_DIAGNOSTIC_SIZE,) or not bool(
        torch.isfinite(diagnostics).all().item()
    ):
        raise GameCoordinationError("G5 协调诊断形状错误或包含非有限值")
    return diagnostics


def _projection_candidate_key(
    candidate: tuple[torch.Tensor, torch.Tensor, tuple[int, ...]],
    reliability: float,
) -> tuple[object, ...]:
    weights, distance, subset = candidate
    values = weights.detach().cpu().tolist()
    return (
        float(distance.detach().item()),
        -float(values[0]),
        -reliability * float(values[2]),
        -float(values[1]),
        subset,
    )


def _project_g5_subset(
    q: torch.Tensor,
    gram: torch.Tensor,
    active_auxiliaries: tuple[int, ...],
    generation_floor: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """枚举活跃约束，解析投影到一个固定辅助子集的凸安全集。"""
    allowed = (0, *active_auxiliaries)
    q_allowed = q[list(allowed)]
    dimension = len(allowed)
    inequalities: list[tuple[torch.Tensor, float]] = []
    for position in range(dimension):
        coefficient = torch.zeros(dimension, dtype=q.dtype, device=q.device)
        coefficient[position] = 1.0
        inequalities.append((coefficient, 0.0))
    inequalities.append((gram[0, list(allowed)], generation_floor))
    for index in active_auxiliaries:
        inequalities.append((gram[index, list(allowed)], 0.0))

    candidates: list[tuple[torch.Tensor, torch.Tensor, tuple[int, ...]]] = []
    # 和约束已占一个自由度；凸投影总能由至多 dimension-1 个
    # 独立活跃不等式表征。
    for count in range(min(len(inequalities), dimension - 1) + 1):
        for active_constraints in combinations(range(len(inequalities)), count):
            rows = [torch.ones(dimension, dtype=q.dtype, device=q.device)]
            bounds = [1.0]
            for constraint_index in active_constraints:
                coefficient, bound = inequalities[constraint_index]
                rows.append(coefficient)
                bounds.append(bound)
            equality = torch.stack(rows)
            target = torch.tensor(bounds, dtype=q.dtype, device=q.device)
            residual = equality @ q_allowed - target
            multiplier = torch.linalg.pinv(equality @ equality.T) @ residual
            projected_allowed = q_allowed - equality.T @ multiplier
            if not bool(torch.isfinite(projected_allowed.detach()).all().item()):
                continue
            equality_error = (equality @ projected_allowed - target).detach().abs().max()
            if float(equality_error.item()) > G5_PROJECTION_TOLERANCE:
                continue
            feasible = True
            for coefficient, bound in inequalities:
                value = float((coefficient @ projected_allowed).detach().item())
                if value + G5_PROJECTION_TOLERANCE < bound:
                    feasible = False
                    break
            if not feasible:
                continue
            zero = q.sum() * 0.0
            positions = {index: position for position, index in enumerate(allowed)}
            projected = torch.stack(
                [
                    projected_allowed[positions[index]] if index in positions else zero
                    for index in range(3)
                ]
            )
            distance = (projected - q).square().sum()
            candidates.append((projected, distance, active_constraints))

    if not candidates:
        raise GameCoordinationError("G5 安全投影未找到可行候选")
    selected = min(
        candidates,
        key=lambda item: (
            float(item[1].detach().item()),
            item[2],
        ),
    )
    return selected[0], selected[1]


def coordinate_g5_response(
    gram: Sequence[Sequence[float]],
    *,
    physics_reliability: float,
    base_solution: CoordinationSolution,
    diagnostics: torch.Tensor,
    response: torch.Tensor,
    generation_floor: float = GENERATION_FLOOR,
    stop_response: bool = False,
) -> G5CoordinationResult:
    """在 G4 接受集合的全部子集上选择可微安全投影。"""
    matrix_values = validate_gram_matrix(gram)
    reliability = float(physics_reliability)
    floor = float(generation_floor)
    if not math.isfinite(reliability) or not 0.0 <= reliability <= 1.0:
        raise GameCoordinationError("物理可靠性必须位于 [0, 1]")
    if not math.isfinite(floor) or not 0.0 <= floor <= 1.0:
        raise GameCoordinationError("生成边际底线必须位于 [0, 1]")
    if diagnostics.shape != (G5_DIAGNOSTIC_SIZE,) or diagnostics.requires_grad:
        raise GameCoordinationError("G5 协调诊断必须为停止梯度的七维张量")
    if response.shape != (G5_RESPONSE_SIZE,) or not bool(torch.isfinite(response).all().item()):
        raise GameCoordinationError("G5 协调响应必须为有限二维张量")

    matrix = torch.tensor(matrix_values, dtype=torch.float64, device=response.device)
    base_weights = torch.tensor(
        base_solution.weights,
        dtype=torch.float64,
        device=response.device,
    )
    base_margins = matrix @ base_weights
    if (
        not bool(torch.isfinite(base_weights).all().item())
        or abs(float(base_weights.sum().item()) - 1.0) > G5_PROJECTION_TOLERANCE
        or bool((base_weights < 0).any().item())
        or float(base_margins[0].item()) + G5_PROJECTION_TOLERANCE < floor
    ):
        raise GameCoordinationError("G4 基线权重不属于 G5 安全可行域")

    if stop_response:
        coordinated_weights = base_weights
        coordinated_margins = base_margins
        selected_subset = tuple(
            index
            for index, name in ((1, "state"), (2, "physics"))
            if name in base_solution.active_auxiliaries
        )
        projection_distance = 0.0
        effective_response = torch.zeros_like(response).detach()
    else:
        effective_response = response
        delta = 1.0 - floor
        q_state = base_weights[1] + delta * torch.tanh(response[0].to(torch.float64))
        q_physics = base_weights[2] + (
            delta * reliability * torch.tanh(response[1].to(torch.float64))
        )
        q = torch.stack((1.0 - q_state - q_physics, q_state, q_physics))
        accepted = tuple(
            index
            for index, name in ((1, "state"), (2, "physics"))
            if name in base_solution.active_auxiliaries
            and base_solution.weights[index] > STRICT_MARGIN_TOLERANCE
            and base_solution.margins[index] > STRICT_MARGIN_TOLERANCE
        )
        candidates: list[tuple[torch.Tensor, torch.Tensor, tuple[int, ...]]] = []
        for count in range(len(accepted) + 1):
            for subset in combinations(accepted, count):
                projected, distance = _project_g5_subset(q, matrix, subset, floor)
                candidates.append((projected, distance, subset))
        selected_weights, selected_distance, selected_subset = min(
            candidates,
            key=lambda item: _projection_candidate_key(item, reliability),
        )
        # 零初始化时保留投影雅可比，同时把前向值逐位锚定到 G4。
        if bool((response.detach() == 0).all().item()):
            selected_weights = selected_weights + (base_weights - selected_weights).detach()
        coordinated_weights = selected_weights
        coordinated_margins = matrix @ coordinated_weights
        projection_distance = float(selected_distance.detach().item())

    if (
        not bool(torch.isfinite(coordinated_weights).all().item())
        or bool((coordinated_weights < -G5_PROJECTION_TOLERANCE).any().item())
        or abs(float(coordinated_weights.detach().sum().item()) - 1.0) > G5_PROJECTION_TOLERANCE
        or float(coordinated_margins[0].detach().item()) + G5_PROJECTION_TOLERANCE < floor
    ):
        raise GameCoordinationError("G5 协调权重违反生成保护或单纯形约束")
    for index in selected_subset:
        if float(coordinated_margins[index].detach().item()) < -G5_PROJECTION_TOLERANCE:
            raise GameCoordinationError("G5 协调权重违反辅助目标非负边际")

    active_names = tuple(OBJECTIVE_NAMES[index] for index in selected_subset)
    weights_tuple: ObjectiveVector = tuple(
        float(value) for value in coordinated_weights.detach().cpu().tolist()
    )  # type: ignore[assignment]
    margins_tuple: ObjectiveVector = tuple(
        float(value) for value in coordinated_margins.detach().cpu().tolist()
    )  # type: ignore[assignment]
    solution = CoordinationSolution(
        weights=weights_tuple,
        margins=margins_tuple,
        objective=base_solution.objective,
        active_auxiliaries=active_names,
        fallback_to_generation=not active_names,
        generation_vetoed=base_solution.generation_vetoed,
    )
    return G5CoordinationResult(
        base_solution=base_solution,
        solution=solution,
        diagnostics=diagnostics,
        response=effective_response,
        base_weights=base_weights,
        coordinated_weights=coordinated_weights,
        coordinated_margins=coordinated_margins,
        selected_auxiliary_subset=selected_subset,
        projection_distance=projection_distance,
    )


def g5_projection_jacobian_norm(result: G5CoordinationResult) -> float:
    """计算选中投影分支对协调响应的雅可比弗罗贝尼乌斯范数。"""
    if not result.response.requires_grad or not result.coordinated_weights.requires_grad:
        return 0.0
    rows = []
    for index in range(3):
        gradient = torch.autograd.grad(
            result.coordinated_weights[index],
            result.response,
            retain_graph=True,
            allow_unused=True,
        )[0]
        rows.append(torch.zeros_like(result.response) if gradient is None else gradient)
    jacobian = torch.stack(rows).detach().float()
    if not bool(torch.isfinite(jacobian).all().item()):
        raise GameCoordinationError("G5 安全投影雅可比包含非有限值")
    return float(torch.linalg.vector_norm(jacobian).item())
