"""共享低秩基底的物理状态编码专家与运行时。"""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

import torch
from torch.utils.hooks import RemovableHandle

from flow_probe.bounded_physics_conditioning import (
    build_candidate_injection_mask,
    build_training_injection_mask,
)

__all__ = [
    "EXPERT_NAMES",
    "PhysicsRoutedExpertGeneration",
    "PhysicsRoutedExpertOutput",
    "PhysicsRoutedExpertRuntime",
    "RouteThresholds",
    "RoutingDiagnostics",
    "SharedBasisStateExpert",
    "calibrate_route_thresholds",
    "hadamard_expert_codes",
    "route_predicted_state",
]

EXPERT_NAMES = ("steady", "accumulating", "saturated")
TARGET_LAYERS = (24, 25, 26, 27)
ROUTER_SOURCE_LAYER = 13
SUPPORTED_VARIANTS = ("single", "routed")


def _validate_predicted_state(predicted_state: torch.Tensor, *, allow_empty: bool = False) -> None:
    if (
        not isinstance(predicted_state, torch.Tensor)
        or predicted_state.ndim != 2
        or predicted_state.shape[1] != 5
        or (not allow_empty and predicted_state.shape[0] < 1)
    ):
        raise ValueError("predicted_state 必须是非空的 [N,5] 张量")
    if not torch.is_floating_point(predicted_state) or torch.is_complex(predicted_state):
        raise ValueError("predicted_state 必须是实数浮点张量")
    if not bool(torch.isfinite(predicted_state).all().item()):
        raise ValueError("predicted_state 必须只包含有限值")
    if bool((predicted_state < 0).any().item()):
        raise ValueError("predicted_state 不得包含负值")


@dataclass(frozen=True)
class RouteThresholds:
    """冻结预测状态路由使用的两个标量阈值。"""

    growth: float
    pressure: float

    def __post_init__(self) -> None:
        for name, value in (("growth", self.growth), ("pressure", self.pressure)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} 阈值必须是数值")
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} 阈值必须是有限值")


def calibrate_route_thresholds(predicted_state: torch.Tensor) -> RouteThresholds:
    """仅从冻结模型的五维预测状态计算固定三分之二分位数阈值。"""

    _validate_predicted_state(predicted_state)
    state = predicted_state.detach().to(dtype=torch.float32)
    growth = state[:, 4] - state[:, 0]
    pressure = state.mean(dim=1)
    quantile = 2.0 / 3.0
    return RouteThresholds(
        growth=float(torch.quantile(growth, quantile).item()),
        pressure=float(torch.quantile(pressure, quantile).item()),
    )


def route_predicted_state(
    predicted_state: torch.Tensor,
    thresholds: RouteThresholds,
) -> torch.Tensor:
    """按高增长优先、高压力其次的固定规则返回 0/1/2 路由。"""

    _validate_predicted_state(predicted_state)
    if not isinstance(thresholds, RouteThresholds):
        raise ValueError("thresholds 必须是 RouteThresholds")
    state = predicted_state.to(dtype=torch.float32)
    growth = state[:, 4] - state[:, 0]
    pressure = state.mean(dim=1)
    routes = torch.zeros(state.shape[0], dtype=torch.long, device=state.device)
    high_growth = growth >= thresholds.growth
    high_pressure = pressure >= thresholds.pressure
    routes = torch.where(high_pressure, torch.full_like(routes, 2), routes)
    routes = torch.where(high_growth, torch.full_like(routes, 1), routes)
    return routes


def _sylvester_hadamard(order: int) -> torch.Tensor:
    matrix = torch.ones((1, 1), dtype=torch.float32)
    while matrix.shape[0] < order:
        matrix = torch.cat(
            (
                torch.cat((matrix, matrix), dim=1),
                torch.cat((matrix, -matrix), dim=1),
            ),
            dim=0,
        )
    return matrix


def hadamard_expert_codes(rank: int = 16) -> torch.Tensor:
    """返回三条固定、满支持、两两正交的 16 维非平凡 Hadamard 行码。"""

    if isinstance(rank, bool) or not isinstance(rank, int) or rank != 16:
        raise ValueError("共享低秩专家的 rank 必须固定为 16")
    matrix = _sylvester_hadamard(rank)
    codes = matrix.index_select(0, torch.tensor((1, 2, 4), dtype=torch.long)).clone()
    gram = codes @ codes.transpose(0, 1)
    if not torch.equal(gram, torch.eye(3, dtype=codes.dtype) * rank):
        raise RuntimeError("固定 Hadamard 专家码未通过正交性检查")
    if not bool((codes != 0).all().item()):
        raise RuntimeError("固定 Hadamard 专家码必须满支持")
    return codes


class SharedBasisStateExpert(torch.nn.Module):
    """使用固定通道码调制同一组秩 16 下投影与上投影。"""

    def __init__(
        self,
        hidden_size: int = 2048,
        rank: int = 16,
        residual_ratio_cap: float = 0.1,
    ) -> None:
        super().__init__()
        if isinstance(hidden_size, bool) or not isinstance(hidden_size, int) or hidden_size != 2048:
            raise ValueError("hidden_size 必须固定为 2048")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank != 16:
            raise ValueError("rank 必须固定为 16")
        if (
            isinstance(residual_ratio_cap, bool)
            or not isinstance(residual_ratio_cap, (int, float))
            or float(residual_ratio_cap) != 0.1
        ):
            raise ValueError("residual_ratio_cap 必须固定为 0.1")
        self.hidden_size = hidden_size
        self.rank = rank
        self.residual_ratio_cap = float(residual_ratio_cap)
        self.norm_epsilon = 1e-6
        self.down = torch.nn.Linear(hidden_size, rank, bias=False)
        self.up = torch.nn.Linear(rank, hidden_size, bias=False)
        self.alpha = torch.nn.Parameter(torch.zeros(()))
        self.reset_deterministic(42)

    def reset_deterministic(self, seed: int) -> None:
        """使用局部生成器初始化共享基底，不改变全局随机状态。"""

        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("初始化种子必须是整数")
        generator = torch.Generator(device="cpu")
        generator.manual_seed(seed)
        down = torch.randn(self.down.weight.shape, generator=generator, dtype=torch.float32)
        up = torch.randn(self.up.weight.shape, generator=generator, dtype=torch.float32)
        with torch.no_grad():
            self.down.weight.copy_(down * (1.0 / math.sqrt(self.hidden_size)))
            self.up.weight.copy_(up * (1.0 / math.sqrt(self.rank)))
            self.alpha.zero_()

    def forward(
        self,
        hidden: torch.Tensor,
        channel_codes: torch.Tensor,
        injection_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """计算全秩调制残差，并返回修正隐藏状态与最大相对范数。"""

        if (
            not isinstance(hidden, torch.Tensor)
            or hidden.ndim != 3
            or hidden.shape[0] < 1
            or hidden.shape[1] < 1
            or hidden.shape[2] != self.hidden_size
            or not torch.is_floating_point(hidden)
        ):
            raise ValueError("hidden 必须是非空的 [B,T,2048] 浮点张量")
        if (
            not isinstance(channel_codes, torch.Tensor)
            or channel_codes.shape != (hidden.shape[0], self.rank)
            or not torch.is_floating_point(channel_codes)
        ):
            raise ValueError("channel_codes 必须是与 hidden 同批次的 [B,16] 浮点张量")
        if (
            not isinstance(injection_mask, torch.Tensor)
            or injection_mask.dtype != torch.bool
            or injection_mask.shape != hidden.shape[:2]
        ):
            raise ValueError("injection_mask 必须是与 hidden 前两维相同的布尔张量")
        if hidden.device != channel_codes.device or hidden.device != injection_mask.device:
            raise ValueError("hidden、channel_codes 与 injection_mask 必须位于同一设备")
        if hidden.device != self.down.weight.device:
            raise ValueError("输入与共享低秩专家必须位于同一设备")
        if not bool(torch.isfinite(hidden).all().item()):
            raise ValueError("hidden 包含非有限值")
        if not bool(torch.isfinite(channel_codes).all().item()):
            raise ValueError("channel_codes 包含非有限值")
        if not bool(injection_mask.any().item()):
            return hidden, hidden.new_zeros((), dtype=torch.float32)

        aligned_hidden = hidden.to(dtype=self.down.weight.dtype)
        bottleneck = self.down(aligned_hidden)
        modulated = bottleneck * channel_codes.to(dtype=bottleneck.dtype).unsqueeze(1)
        raw_residual = self.up(modulated)
        calculation_dtype = (
            torch.float32
            if hidden.dtype in {torch.float16, torch.bfloat16}
            or raw_residual.dtype in {torch.float16, torch.bfloat16}
            else torch.promote_types(hidden.dtype, raw_residual.dtype)
        )
        hidden_float = hidden.to(dtype=calculation_dtype)
        residual_float = raw_residual.to(dtype=calculation_dtype)
        hidden_norm = torch.linalg.vector_norm(hidden_float, dim=-1, keepdim=True).detach()
        residual_norm = torch.linalg.vector_norm(residual_float, dim=-1, keepdim=True)
        gate = self.residual_ratio_cap * torch.tanh(self.alpha.to(dtype=calculation_dtype))
        bounded = gate * hidden_norm * residual_float / (residual_norm + self.norm_epsilon)
        masked = torch.where(injection_mask.unsqueeze(-1), bounded, torch.zeros_like(bounded))
        corrected = hidden + masked.to(dtype=hidden.dtype)
        ratios = torch.linalg.vector_norm(masked, dim=-1) / (
            hidden_norm.squeeze(-1) + self.norm_epsilon
        )
        maximum_ratio = ratios.amax()
        if not bool(torch.isfinite(corrected).all().item()):
            raise ValueError("共享低秩专家输出包含非有限值")
        if float(maximum_ratio.detach().item()) > self.residual_ratio_cap + 1e-6:
            raise RuntimeError("共享低秩专家超过相对残差范数上界")
        return corrected, maximum_ratio


def _read_named_output(model_output: object, name: str) -> object:
    if isinstance(model_output, Mapping) and name in model_output:
        return model_output[name]
    try:
        return getattr(model_output, name)
    except AttributeError as error:
        raise AttributeError(f"底层模型输出不包含 {name!r}") from error


@dataclass(frozen=True)
class RoutingDiagnostics:
    """一次共享基底专家运行的路由与有界残差诊断。"""

    gate_values: tuple[float, float, float, float]
    max_residual_ratio: float
    source_hook_count: int
    target_hook_counts: tuple[int, int, int, int]
    active_route_counts: tuple[int, int, int]
    active_rows: int
    prefill_count: int
    cached_decode_count: int


@dataclass(frozen=True)
class PhysicsRoutedExpertOutput:
    """普通前向的底层输出、双状态预测与路由诊断。"""

    model_output: object
    predicted_router_state: torch.Tensor | None
    predicted_outcome_state: torch.Tensor | None
    route_ids: torch.Tensor | None
    diagnostics: RoutingDiagnostics

    @property
    def loss(self) -> object:
        return _read_named_output(self.model_output, "loss")

    @property
    def logits(self) -> object:
        return _read_named_output(self.model_output, "logits")

    def __getitem__(self, name: str) -> object:
        if not isinstance(name, str):
            raise TypeError("PhysicsRoutedExpertOutput 只支持按名称读取")
        return _read_named_output(self.model_output, name)

    def __getattr__(self, name: str) -> object:
        model_output = object.__getattribute__(self, "model_output")
        return _read_named_output(model_output, name)


@dataclass(frozen=True)
class PhysicsRoutedExpertGeneration:
    """自由生成结果及其冻结路由状态与诊断。"""

    model_output: object
    predicted_router_state: torch.Tensor | None
    route_ids: torch.Tensor | None
    diagnostics: RoutingDiagnostics

    def __getitem__(self, name: str) -> object:
        if not isinstance(name, str):
            raise TypeError("PhysicsRoutedExpertGeneration 只支持按名称读取")
        return _read_named_output(self.model_output, name)

    def __getattr__(self, name: str) -> object:
        model_output = object.__getattribute__(self, "model_output")
        return _read_named_output(model_output, name)


@dataclass
class _RoutingSession:
    mode: str
    anchor_positions: torch.Tensor | None
    injection_mask: torch.Tensor | None
    expert_row_mask: torch.Tensor | None
    fixed_expert: int | None
    removed_expert: int | None
    predicted_router_state: torch.Tensor | None = None
    predicted_outcome_state: torch.Tensor | None = None
    route_ids: torch.Tensor | None = None
    channel_codes: torch.Tensor | None = None
    active_rows: torch.Tensor | None = None
    current_injection_mask: torch.Tensor | None = None
    source_hook_count: int = 0
    target_hook_counts: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    target_seen_in_step: list[bool] = field(default_factory=lambda: [False, False, False, False])
    max_residual_ratio: float = 0.0
    prefill_count: int = 0
    cached_decode_count: int = 0


class PhysicsRoutedExpertRuntime(torch.nn.Module):
    """在冻结 Qwen/S3 上执行共享基底状态专家路由。"""

    _STRUCTURE_PREFIXES = (
        "router_state_head.",
        "outcome_state_head.",
        "experts.",
        "expert_codes",
        "single_code",
    )

    def __init__(
        self,
        model: torch.nn.Module,
        s3_state_head: torch.nn.Module,
        thresholds: RouteThresholds,
        *,
        variant: Literal["single", "routed"],
        hidden_size: int = 2048,
        rank: int = 16,
        residual_ratio_cap: float = 0.1,
    ) -> None:
        super().__init__()
        if not isinstance(model, torch.nn.Module):
            raise ValueError("model 必须是 torch.nn.Module")
        if not isinstance(s3_state_head, torch.nn.Module):
            raise ValueError("s3_state_head 必须是 torch.nn.Module")
        if variant not in SUPPORTED_VARIANTS:
            raise ValueError("variant 只允许 single 或 routed")
        if not isinstance(thresholds, RouteThresholds):
            raise ValueError("thresholds 必须是 RouteThresholds")
        if hidden_size != 2048 or rank != 16 or residual_ratio_cap != 0.1:
            raise ValueError("共享基底运行时必须固定 hidden_size=2048、rank=16、上界=0.1")

        layers = self._resolve_decoder_layers(model)
        self.variant = variant
        self.thresholds = thresholds
        self.hidden_size = hidden_size
        self.rank = rank
        self.router_state_head = copy.deepcopy(s3_state_head)
        self.outcome_state_head = copy.deepcopy(s3_state_head)
        for parameter in self.router_state_head.parameters():
            parameter.requires_grad_(False)
            parameter.grad = None
        for parameter in self.outcome_state_head.parameters():
            parameter.requires_grad_(True)
        self.experts = torch.nn.ModuleList(
            SharedBasisStateExpert(hidden_size, rank, residual_ratio_cap) for _ in TARGET_LAYERS
        )
        for index, expert in enumerate(self.experts):
            expert.reset_deterministic(4200 + index)
        self.register_buffer("expert_codes", hadamard_expert_codes(rank), persistent=True)
        self.register_buffer("single_code", torch.ones(rank, dtype=torch.float32), persistent=True)

        object.__setattr__(self, "_model", model)
        object.__setattr__(self, "_active_session", None)
        object.__setattr__(self, "_closed", False)
        object.__setattr__(self, "_hook_handles", [])
        handles: list[RemovableHandle] = []
        try:
            handles.append(layers[ROUTER_SOURCE_LAYER].register_forward_hook(self._source_hook))
            for target_index, layer_index in enumerate(TARGET_LAYERS):
                handles.append(
                    layers[layer_index].register_forward_pre_hook(
                        self._make_target_hook(target_index),
                        with_kwargs=True,
                    )
                )
            handles.append(layers[TARGET_LAYERS[-1]].register_forward_hook(self._outcome_hook))
        except Exception:
            for handle in handles:
                handle.remove()
            raise
        object.__setattr__(self, "_hook_handles", handles)

    @property
    def model(self) -> torch.nn.Module:
        return object.__getattribute__(self, "_model")

    @staticmethod
    def _resolve_decoder_layers(model: torch.nn.Module) -> torch.nn.ModuleList:
        config = getattr(model, "config", None)
        if config is None:
            raise ValueError("model 必须公开 Qwen 配置")
        if getattr(config, "num_hidden_layers", None) != 28:
            raise ValueError("model.config.num_hidden_layers 必须固定为 28")
        if getattr(config, "hidden_size", None) != 2048:
            raise ValueError("model.config.hidden_size 必须固定为 2048")
        candidates = (
            ("model", "layers"),
            ("base_model", "model", "model", "layers"),
        )
        resolved: list[object] = []
        for path in candidates:
            current: object = model
            for name in path:
                try:
                    current = getattr(current, name)
                except AttributeError:
                    break
            else:
                resolved.append(current)
        if len(resolved) != 1 or not isinstance(resolved[0], torch.nn.ModuleList):
            raise ValueError("无法唯一解析受支持的 Qwen/PeftModel 解码层路径")
        layers = resolved[0]
        if len(layers) != 28:
            raise ValueError("Qwen 解码层数量必须固定为 28")
        return layers

    @staticmethod
    def _validate_attention_mask(
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        if (
            not isinstance(input_ids, torch.Tensor)
            or input_ids.ndim != 2
            or input_ids.shape[0] < 1
            or input_ids.shape[1] < 2
        ):
            raise ValueError("input_ids 必须是形状为 [B,T] 且 T 至少为 2 的张量")
        if not isinstance(attention_mask, torch.Tensor) or attention_mask.shape != input_ids.shape:
            raise ValueError("attention_mask 必须与 input_ids 形状相同")
        if attention_mask.dtype == torch.bool:
            valid = attention_mask
        elif attention_mask.dtype in {
            torch.uint8,
            torch.int8,
            torch.int16,
            torch.int32,
            torch.int64,
        }:
            if not bool(((attention_mask == 0) | (attention_mask == 1)).all().item()):
                raise ValueError("attention_mask 只能包含 0/1")
            valid = attention_mask.to(dtype=torch.bool)
        else:
            raise ValueError("attention_mask 必须是布尔或整数 0/1 张量")
        if bool((valid.sum(dim=1) < 2).any().item()):
            raise ValueError("每条输入必须至少包含两个有效令牌")
        return valid

    @staticmethod
    def _validate_expert_index(value: int | None, name: str) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int) or value not in {0, 1, 2}:
            raise ValueError(f"{name} 只允许 0、1、2 或 None")
        return value

    @staticmethod
    def _normalize_row_mask(
        mask: torch.Tensor | None,
        *,
        batch_size: int,
        device: torch.device,
    ) -> torch.Tensor:
        if mask is None:
            return torch.ones(batch_size, dtype=torch.bool, device=device)
        if not isinstance(mask, torch.Tensor) or mask.dtype != torch.bool:
            raise ValueError("expert_row_mask 必须是布尔张量")
        if mask.shape != (batch_size,) or mask.device != device:
            raise ValueError("expert_row_mask 必须是与输入同设备的 [B] 张量")
        return mask

    @staticmethod
    def _anchor_positions(
        value: int | Sequence[int] | torch.Tensor,
        *,
        batch_size: int,
        sequence_length: int,
        device: torch.device,
    ) -> torch.Tensor:
        if isinstance(value, bool):
            raise ValueError("锚点位置必须是整数或整数序列")
        if isinstance(value, int):
            positions = torch.full((batch_size,), value, dtype=torch.long, device=device)
        elif isinstance(value, torch.Tensor):
            positions = value.to(device=device, dtype=torch.long)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            positions = torch.tensor(tuple(value), dtype=torch.long, device=device)
        else:
            raise ValueError("锚点位置必须是整数或整数序列")
        if positions.shape != (batch_size,):
            raise ValueError("逐样本锚点位置必须是 [B]")
        if bool(((positions < 0) | (positions >= sequence_length)).any().item()):
            raise ValueError("锚点位置越界")
        return positions

    @staticmethod
    def _hidden(output: object, location: str) -> torch.Tensor:
        if isinstance(output, torch.Tensor):
            hidden = output
        elif isinstance(output, tuple) and output and isinstance(output[0], torch.Tensor):
            hidden = output[0]
        else:
            raise RuntimeError(f"{location} 输出必须是 Tensor 或首元素为 Tensor 的 tuple")
        if hidden.ndim != 3 or hidden.shape[2] != 2048:
            raise RuntimeError(f"{location} 隐藏状态必须是 [B,T,2048]")
        return hidden

    @staticmethod
    def _select_hidden(hidden: torch.Tensor, positions: torch.Tensor) -> torch.Tensor:
        rows = torch.arange(hidden.shape[0], device=hidden.device)
        return hidden[rows, positions]

    def _ensure_available(self) -> None:
        if object.__getattribute__(self, "_closed"):
            raise RuntimeError("PhysicsRoutedExpertRuntime 已关闭")
        if object.__getattribute__(self, "_active_session") is not None:
            raise RuntimeError("不允许嵌套或并发调用 PhysicsRoutedExpertRuntime")

    def _source_hook(
        self,
        _module: torch.nn.Module,
        _args: tuple[object, ...],
        output: object,
    ) -> None:
        session = object.__getattribute__(self, "_active_session")
        if session is None or session.mode == "bypass":
            return
        hidden = self._hidden(output, "第 13 层")
        if session.source_hook_count > 0 and not all(session.target_seen_in_step):
            raise RuntimeError("新的源层调用早于上一轮四个目标层完成")
        if session.mode in {"training", "candidate"}:
            if session.source_hook_count != 0:
                raise RuntimeError("普通前向的第 13 层只能调用一次")
            if session.anchor_positions is None or session.injection_mask is None:
                raise RuntimeError("普通前向缺少锚点或令牌掩码")
            self._compute_routes(session, hidden, session.anchor_positions)
            session.current_injection_mask = session.injection_mask
        elif session.mode == "generate":
            if session.source_hook_count == 0:
                if session.anchor_positions is None or session.injection_mask is None:
                    raise RuntimeError("生成预填充缺少锚点或令牌掩码")
                if hidden.shape[1] <= 1:
                    raise RuntimeError("生成预填充必须包含至少两个令牌")
                self._compute_routes(session, hidden, session.anchor_positions)
                session.current_injection_mask = session.injection_mask
                session.prefill_count = 1
            else:
                if session.channel_codes is None or session.active_rows is None:
                    raise RuntimeError("缓存解码发生在路由预填充之前")
                if hidden.shape[1] != 1:
                    raise RuntimeError("后续缓存解码必须逐令牌执行")
                session.current_injection_mask = session.active_rows.unsqueeze(1)
                session.cached_decode_count += 1
        else:
            raise RuntimeError(f"未知路由会话模式：{session.mode}")
        session.source_hook_count += 1
        session.target_seen_in_step = [False, False, False, False]

    def _compute_routes(
        self,
        session: _RoutingSession,
        hidden: torch.Tensor,
        anchor_positions: torch.Tensor,
    ) -> None:
        selected = self._select_hidden(hidden, anchor_positions)
        with torch.no_grad():
            router_input = selected.detach().to(
                dtype=next(self.router_state_head.parameters()).dtype
            )
            predicted = self.router_state_head(router_input)
        _validate_predicted_state(predicted)
        if session.fixed_expert is None:
            routes = route_predicted_state(predicted, self.thresholds)
        else:
            routes = torch.full(
                (hidden.shape[0],),
                session.fixed_expert,
                dtype=torch.long,
                device=hidden.device,
            )
        if session.expert_row_mask is None:
            raise RuntimeError("路由会话缺少专家行掩码")
        active_rows = session.expert_row_mask
        if session.removed_expert is not None:
            active_rows = active_rows & routes.ne(session.removed_expert)
        if self.variant == "single":
            codes = self.single_code.unsqueeze(0).expand(hidden.shape[0], -1)
        else:
            codes = self.expert_codes.index_select(0, routes)
        session.predicted_router_state = predicted.detach()
        session.route_ids = routes
        session.channel_codes = codes
        session.active_rows = active_rows

    @staticmethod
    def _target_hidden(
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> tuple[torch.Tensor, bool]:
        if "hidden_states" in kwargs:
            hidden = kwargs["hidden_states"]
            from_kwargs = True
        elif args:
            hidden = args[0]
            from_kwargs = False
        else:
            raise RuntimeError("目标层调用缺少 hidden_states")
        if not isinstance(hidden, torch.Tensor):
            raise RuntimeError("目标层 hidden_states 必须是 Tensor")
        return hidden, from_kwargs

    def _make_target_hook(self, target_index: int):
        def hook(
            _module: torch.nn.Module,
            args: tuple[object, ...],
            kwargs: dict[str, object],
        ) -> tuple[tuple[object, ...], dict[str, object]] | None:
            session = object.__getattribute__(self, "_active_session")
            if session is None or session.mode == "bypass":
                return None
            if session.channel_codes is None or session.current_injection_mask is None:
                raise RuntimeError("目标层调用早于第 13 层路由")
            next_target = next(
                (index for index, seen in enumerate(session.target_seen_in_step) if not seen),
                None,
            )
            if next_target != target_index:
                raise RuntimeError("目标层必须按 24、25、26、27 顺序各调用一次")
            hidden, from_kwargs = self._target_hidden(args, kwargs)
            if hidden.shape[:2] != session.current_injection_mask.shape:
                raise RuntimeError("目标层隐藏状态与注入掩码形状不一致")
            corrected, ratio = self.experts[target_index](
                hidden,
                session.channel_codes,
                session.current_injection_mask,
            )
            session.target_seen_in_step[target_index] = True
            session.target_hook_counts[target_index] += 1
            session.max_residual_ratio = max(
                session.max_residual_ratio,
                float(ratio.detach().item()),
            )
            if from_kwargs:
                updated_kwargs = dict(kwargs)
                updated_kwargs["hidden_states"] = corrected
                return args, updated_kwargs
            return (corrected, *args[1:]), kwargs

        return hook

    def _outcome_hook(
        self,
        _module: torch.nn.Module,
        _args: tuple[object, ...],
        output: object,
    ) -> None:
        session = object.__getattribute__(self, "_active_session")
        if (
            session is None
            or session.mode == "bypass"
            or session.predicted_outcome_state is not None
        ):
            return
        if session.anchor_positions is None:
            raise RuntimeError("结果状态头缺少提示锚点")
        hidden = self._hidden(output, "第 27 层")
        if bool((session.anchor_positions >= hidden.shape[1]).any().item()):
            raise RuntimeError("结果状态头锚点超出第 27 层序列长度")
        selected = self._select_hidden(hidden, session.anchor_positions)
        outcome_input = selected.to(dtype=next(self.outcome_state_head.parameters()).dtype)
        predicted = self.outcome_state_head(outcome_input)
        _validate_predicted_state(predicted)
        session.predicted_outcome_state = predicted

    def _validate_complete(self, session: _RoutingSession) -> None:
        if session.mode == "bypass":
            return
        if (
            session.predicted_router_state is None
            or session.predicted_outcome_state is None
            or session.route_ids is None
        ):
            raise RuntimeError("运行时未生成完整路由与结果状态")
        if not all(session.target_seen_in_step):
            raise RuntimeError("底层模型未完成四层专家注入")
        if tuple(session.target_hook_counts) != (session.source_hook_count,) * 4:
            raise RuntimeError("源层与目标层挂钩次数不一致")
        if session.mode == "generate" and session.prefill_count != 1:
            raise RuntimeError("自由生成必须恰好完成一次预填充")
        if session.mode != "generate" and session.source_hook_count != 1:
            raise RuntimeError("普通前向必须恰好调用一次路由源")

    def _diagnostics(self, session: _RoutingSession) -> RoutingDiagnostics:
        route_counts = [0, 0, 0]
        active_count = 0
        if session.route_ids is not None and session.active_rows is not None:
            active_count = int(session.active_rows.sum().item())
            for expert in range(3):
                route_counts[expert] = int(
                    ((session.route_ids == expert) & session.active_rows).sum().item()
                )
        gates = tuple(
            float(
                (
                    expert.residual_ratio_cap
                    * torch.tanh(expert.alpha.detach().to(dtype=torch.float32))
                ).item()
            )
            for expert in self.experts
        )
        return RoutingDiagnostics(
            gate_values=gates,
            max_residual_ratio=session.max_residual_ratio,
            source_hook_count=session.source_hook_count,
            target_hook_counts=tuple(session.target_hook_counts),
            active_route_counts=tuple(route_counts),
            active_rows=active_count,
            prefill_count=session.prefill_count,
            cached_decode_count=session.cached_decode_count,
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
        completion_start: int | Sequence[int] | torch.Tensor | None = None,
        *,
        expert_row_mask: torch.Tensor | None = None,
        bypass: bool = False,
        fixed_expert: int | None = None,
        removed_expert: int | None = None,
        **kwargs: object,
    ) -> PhysicsRoutedExpertOutput:
        """执行训练前向、候选评分或显式旁路。"""

        self._ensure_available()
        if type(bypass) is not bool:
            raise ValueError("bypass 必须是布尔值")
        fixed = self._validate_expert_index(fixed_expert, "fixed_expert")
        removed = self._validate_expert_index(removed_expert, "removed_expert")
        if bypass and any(value is not None for value in (fixed, removed, expert_row_mask)):
            raise ValueError("显式旁路不得同时设置专家掩码、覆盖或移除")
        if bypass:
            session = _RoutingSession("bypass", None, None, None, None, None)
        else:
            valid = self._validate_attention_mask(input_ids, attention_mask)
            row_mask = self._normalize_row_mask(
                expert_row_mask,
                batch_size=input_ids.shape[0],
                device=input_ids.device,
            )
            if labels is not None and completion_start is None:
                if labels.shape != input_ids.shape or labels.device != input_ids.device:
                    raise ValueError("labels 必须与 input_ids 形状和设备相同")
                supervised = labels != -100
                if bool((supervised.sum(dim=1) == 0).any().item()):
                    raise ValueError("labels 每行必须至少含一个监督令牌")
                starts = supervised.to(dtype=torch.int64).argmax(dim=1)
                if bool((starts < 1).any().item()):
                    raise ValueError("首个监督令牌之前必须存在提示锚点")
                session = _RoutingSession(
                    "training",
                    starts - 1,
                    build_training_injection_mask(labels),
                    row_mask,
                    fixed,
                    removed,
                )
            elif completion_start is not None and labels is None:
                mask = build_candidate_injection_mask(completion_start, attention_mask)
                starts = self._anchor_positions(
                    completion_start,
                    batch_size=input_ids.shape[0],
                    sequence_length=input_ids.shape[1],
                    device=input_ids.device,
                )
                session = _RoutingSession(
                    "candidate",
                    starts - 1,
                    mask,
                    row_mask,
                    fixed,
                    removed,
                )
            else:
                raise ValueError("非旁路前向必须且只能提供 labels 或 completion_start")
            if valid.shape != session.injection_mask.shape:
                raise RuntimeError("内部令牌掩码形状错误")

        object.__setattr__(self, "_active_session", session)
        model_kwargs = dict(kwargs)
        if labels is not None:
            model_kwargs["labels"] = labels
        try:
            model_output = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **model_kwargs,
            )
            self._validate_complete(session)
            return PhysicsRoutedExpertOutput(
                model_output=model_output,
                predicted_router_state=session.predicted_router_state,
                predicted_outcome_state=session.predicted_outcome_state,
                route_ids=session.route_ids,
                diagnostics=self._diagnostics(session),
            )
        finally:
            object.__setattr__(self, "_active_session", None)

    def score_candidates(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        completion_start: int | Sequence[int] | torch.Tensor,
        **kwargs: object,
    ) -> PhysicsRoutedExpertOutput:
        """以显式补全起点执行候选评分路径。"""

        return self(
            input_ids,
            attention_mask,
            completion_start=completion_start,
            **kwargs,
        )

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        *,
        expert_row_mask: torch.Tensor | None = None,
        bypass: bool = False,
        fixed_expert: int | None = None,
        removed_expert: int | None = None,
        **kwargs: object,
    ) -> PhysicsRoutedExpertGeneration:
        """执行一次提示预填充并在缓存解码中复用冻结路由。"""

        self._ensure_available()
        if type(bypass) is not bool:
            raise ValueError("bypass 必须是布尔值")
        fixed = self._validate_expert_index(fixed_expert, "fixed_expert")
        removed = self._validate_expert_index(removed_expert, "removed_expert")
        num_beams = kwargs.get("num_beams", 1)
        if isinstance(num_beams, bool) or not isinstance(num_beams, int) or num_beams != 1:
            raise ValueError("共享基底专家自由生成只支持 num_beams=1")
        if bypass and any(value is not None for value in (fixed, removed, expert_row_mask)):
            raise ValueError("显式旁路不得同时设置专家掩码、覆盖或移除")
        if bypass:
            session = _RoutingSession("bypass", None, None, None, None, None)
        else:
            valid = self._validate_attention_mask(input_ids, attention_mask)
            positions = torch.arange(input_ids.shape[1], device=input_ids.device).expand_as(
                input_ids
            )
            anchors = positions.masked_fill(~valid, -1).amax(dim=1)
            prefill_mask = torch.zeros_like(valid)
            prefill_mask.scatter_(1, anchors.unsqueeze(1), True)
            row_mask = self._normalize_row_mask(
                expert_row_mask,
                batch_size=input_ids.shape[0],
                device=input_ids.device,
            )
            session = _RoutingSession(
                "generate",
                anchors,
                prefill_mask,
                row_mask,
                fixed,
                removed,
            )
        object.__setattr__(self, "_active_session", session)
        try:
            model_output = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **kwargs,
            )
            self._validate_complete(session)
            return PhysicsRoutedExpertGeneration(
                model_output=model_output,
                predicted_router_state=session.predicted_router_state,
                route_ids=session.route_ids,
                diagnostics=self._diagnostics(session),
            )
        finally:
            object.__setattr__(self, "_active_session", None)

    def trainable_parameter_names(self) -> tuple[str, ...]:
        """返回候选和对照必须完全一致的可训练结构参数名。"""

        return tuple(name for name, parameter in self.named_parameters() if parameter.requires_grad)

    def shared_basis_parameters(self) -> tuple[torch.nn.Parameter, ...]:
        """返回四层共享 A/B，不包含门或状态头。"""

        parameters: list[torch.nn.Parameter] = []
        for expert in self.experts:
            parameters.extend((expert.down.weight, expert.up.weight))
        return tuple(parameters)

    def trainable_parameters(self) -> tuple[torch.nn.Parameter, ...]:
        return tuple(parameter for parameter in self.parameters() if parameter.requires_grad)

    def unexpected_base_parameter_names(self) -> tuple[str, ...]:
        base_ids = {id(parameter) for parameter in self.model.parameters()}
        return tuple(
            name for name, parameter in self.named_parameters() if id(parameter) in base_ids
        )

    def structure_state_dict(self) -> dict[str, torch.Tensor]:
        state = self.state_dict()
        unexpected = tuple(name for name in state if not name.startswith(self._STRUCTURE_PREFIXES))
        if unexpected:
            raise RuntimeError(f"运行时状态字典包含意外字段：{unexpected}")
        if self.unexpected_base_parameter_names():
            raise RuntimeError("运行时意外注册了冻结基座参数")
        return {name: value.detach().clone() for name, value in state.items()}

    def load_structure_state_dict(
        self,
        state: Mapping[str, torch.Tensor],
        *,
        strict: bool = True,
    ) -> object:
        if not isinstance(state, Mapping):
            raise ValueError("state 必须是参数名到张量的映射")
        expected = self.state_dict()
        supplied = set(state)
        missing = tuple(sorted(set(expected) - supplied))
        unexpected = tuple(sorted(supplied - set(expected)))
        if strict and (missing or unexpected):
            raise ValueError(f"结构状态键不匹配：缺失={missing}，多余={unexpected}")
        compatible: dict[str, torch.Tensor] = {}
        for name in sorted(set(expected) & supplied):
            value = state[name]
            if not isinstance(value, torch.Tensor) or value.shape != expected[name].shape:
                raise ValueError(f"结构状态 {name} 的类型或形状不匹配")
            compatible[name] = value
        return super().load_state_dict(compatible, strict=strict)

    def close(self) -> None:
        """移除全部挂钩；关闭后不再允许执行。"""

        if object.__getattribute__(self, "_active_session") is not None:
            raise RuntimeError("活动会话期间不得关闭运行时")
        if object.__getattribute__(self, "_closed"):
            return
        handles = object.__getattribute__(self, "_hook_handles")
        for handle in handles:
            handle.remove()
        handles.clear()
        object.__setattr__(self, "_closed", True)
