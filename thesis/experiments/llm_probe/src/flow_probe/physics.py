"""用于恶意流量训练的可微队列守恒约束。"""

from __future__ import annotations

import math
from collections.abc import Sequence

import torch


class PhysicsConstraintError(ValueError):
    """物理约束输入的形状、量纲或时间跨度不合法。"""


def _validate_flow_tensor(
    name: str,
    value: torch.Tensor,
    expected_shape: torch.Size,
) -> None:
    if value.shape != expected_shape:
        raise PhysicsConstraintError(
            f"{name}形状必须为{tuple(expected_shape)}，实际为{tuple(value.shape)}"
        )
    if not torch.isfinite(value).all():
        raise PhysicsConstraintError(f"{name}必须全部为有限数")


def _capacity_column(capacity: torch.Tensor, batch_size: int) -> torch.Tensor:
    if not torch.isfinite(capacity).all() or torch.any(capacity <= 0):
        raise PhysicsConstraintError("链路容量必须全部为有限正数")
    if capacity.numel() == 1:
        return capacity.reshape(1, 1).expand(batch_size, 1)
    if capacity.shape == (batch_size,):
        return capacity.reshape(batch_size, 1)
    if capacity.shape == (batch_size, 1):
        return capacity
    raise PhysicsConstraintError("链路容量必须是标量、批大小向量或单列矩阵")


def multiscale_queue_balance_residual(
    *,
    predicted_queue: torch.Tensor,
    arrivals: torch.Tensor,
    departures: torch.Tensor,
    drops: torch.Tensor,
    consumed: torch.Tensor,
    capacity: torch.Tensor,
    delta_seconds: float,
    horizons: Sequence[int] = (1,),
    epsilon: float = 1e-8,
) -> dict[int, torch.Tensor]:
    """计算按容量预算归一的多尺度离散队列守恒残差。

    攻击流量仍应满足完整守恒式。该残差用于约束模型预测的连续队列状态，
    而不是把攻击定义成守恒律失效。
    """
    if predicted_queue.ndim != 2:
        raise PhysicsConstraintError("预测队列必须采用[批量, 时间点]二维形状")
    if not torch.isfinite(predicted_queue).all():
        raise PhysicsConstraintError("预测队列必须全部为有限数")
    batch_size, state_count = predicted_queue.shape
    transition_count = state_count - 1
    if batch_size <= 0 or transition_count <= 0:
        raise PhysicsConstraintError("预测队列至少需要一个样本和一个状态转移")
    expected_shape = torch.Size((batch_size, transition_count))
    for name, value in (
        ("到达量", arrivals),
        ("离开量", departures),
        ("丢弃量", drops),
        ("消费量", consumed),
    ):
        _validate_flow_tensor(name, value, expected_shape)
    if not math.isfinite(delta_seconds) or delta_seconds <= 0:
        raise PhysicsConstraintError("时间窗长度必须是有限正数")
    if not math.isfinite(epsilon) or epsilon <= 0:
        raise PhysicsConstraintError("归一化稳定项必须是有限正数")

    normalized_horizons: list[int] = []
    for horizon in horizons:
        if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon <= 0:
            raise PhysicsConstraintError("时间跨度必须是正整数")
        if horizon > transition_count:
            raise PhysicsConstraintError(f"时间跨度{horizon}超过可用状态转移数{transition_count}")
        if horizon in normalized_horizons:
            raise PhysicsConstraintError(f"时间跨度不得重复：{horizon}")
        normalized_horizons.append(horizon)
    if not normalized_horizons:
        raise PhysicsConstraintError("至少需要一个时间跨度")

    capacity_column = _capacity_column(capacity, batch_size).to(
        device=predicted_queue.device,
        dtype=predicted_queue.dtype,
    )
    net_input = arrivals - departures - drops - consumed
    residuals: dict[int, torch.Tensor] = {}
    for horizon in normalized_horizons:
        predicted_change = predicted_queue[:, horizon:] - predicted_queue[:, :-horizon]
        accumulated_input = net_input.unfold(1, horizon, 1).sum(dim=-1)
        capacity_budget = capacity_column * (float(delta_seconds) * horizon)
        residuals[horizon] = (predicted_change - accumulated_input) / (capacity_budget + epsilon)
    return residuals
