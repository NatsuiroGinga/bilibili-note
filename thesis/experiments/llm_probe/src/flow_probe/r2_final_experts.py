from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping, TypeVar


EXPERT_SHARED = "shared_conservation"
EXPERT_TCP = "tcp_dynamics"
EXPERT_UDP = "udp_dynamics"
EXPERT_QUIC = "quic_dynamics"
EXPERT_UNKNOWN = "unknown_fallback"
ROUTE_NAMES = ("TCP", "UDP", "QUIC", "UNKNOWN")
ROUTE_TO_INDEX = {name: index for index, name in enumerate(ROUTE_NAMES)}


class R2FinalExpertError(ValueError):
    """表示最终 R2 专家合同被违反。"""


@dataclass(frozen=True)
class ExpertConfig:
    """统一物理专家配置。"""

    name: str
    input_dimension: int
    hidden_dimension: int
    representation_dimension: int
    state_dimension: int
    residual_dimension: int
    layer_count: int
    dropout: float
    enabled: bool
    required_truth_fields: tuple[str, ...]


@dataclass(frozen=True)
class ExpertOutput:
    """所有专家共享的前向输出。"""

    representation: Any
    window_representation: Any
    predicted_state: Any
    physics_residual: Any
    valid_mask: Any
    active_mask: Any
    expert_name: str


@dataclass(frozen=True)
class RouteBatch:
    """停止梯度的协议路由输入。"""

    route_index: Any
    confidence: Any
    quic_applicable: Any


@dataclass(frozen=True)
class PhysicsSupervisionBatch:
    """训练期物理真值；不得进入推理路由或分类表示。"""

    truth_state: Any
    truth_mask: Any
    qlog_truth_available: Any


@dataclass(frozen=True)
class ResidualObservationContext:
    """只用于选择固定残差方程的停止梯度观测真值。"""

    observed_state: Any
    observed_mask: Any


@dataclass(frozen=True)
class RoutedPhysicsOutput:
    """共享守恒与唯一适用协议专家的组合输出。"""

    representation: Any
    sidecar_sequence: Any
    shared: ExpertOutput
    protocol_outputs: Mapping[str, ExpertOutput]
    effective_route_index: Any
    hard_masks: Any
    stopped_confidence: Any
    quic_structurally_closed_count: int
    routing_audit: Mapping[str, int]


def _tcp_phase_observation_availability(observed_mask: Any) -> tuple[Any, Any]:
    """分别给出增长方程与收缩方程所需真值是否可用。"""

    event_observed = observed_mask[..., 7] & observed_mask[..., 8]
    growth = (
        observed_mask[..., 0]
        & observed_mask[..., 1]
        & observed_mask[..., 2]
        & observed_mask[..., 6]
        & observed_mask[..., 9]
        & event_observed
    )
    contraction = (
        observed_mask[..., 1]
        & observed_mask[..., 3]
        & observed_mask[..., 4]
        & observed_mask[..., 5]
        & event_observed
    )
    return growth, contraction


TExpert = TypeVar("TExpert")
PHYSICS_EXPERT_REGISTRY: dict[str, type[Any]] = {}


def register_physics_expert(name: str) -> Callable[[TExpert], TExpert]:
    """注册唯一命名的物理专家实现。"""

    if not name or name.strip() != name:
        raise R2FinalExpertError("专家注册名不能为空或包含首尾空白")

    def decorator(expert_class: TExpert) -> TExpert:
        if name in PHYSICS_EXPERT_REGISTRY:
            raise R2FinalExpertError(f"物理专家重复注册：{name}")
        PHYSICS_EXPERT_REGISTRY[name] = expert_class  # type: ignore[assignment]
        return expert_class

    return decorator


def create_physics_expert(config: ExpertConfig) -> Any:
    """按冻结配置创建一个已注册专家。"""

    expert_class = PHYSICS_EXPERT_REGISTRY.get(config.name)
    if expert_class is None:
        available = ", ".join(sorted(PHYSICS_EXPERT_REGISTRY))
        raise R2FinalExpertError(f"未知物理专家 {config.name}；可用实现为：{available}")
    return expert_class(config)


def _load_torch() -> Any:
    try:
        import torch
    except ImportError as error:
        raise R2FinalExpertError("最终 R2 专家需要 PyTorch") from error
    return torch


def _validate_config(config: ExpertConfig) -> None:
    integer_fields = {
        "input_dimension": config.input_dimension,
        "hidden_dimension": config.hidden_dimension,
        "representation_dimension": config.representation_dimension,
        "state_dimension": config.state_dimension,
        "residual_dimension": config.residual_dimension,
        "layer_count": config.layer_count,
    }
    for name, value in integer_fields.items():
        if value <= 0:
            raise R2FinalExpertError(f"专家配置 {name} 必须为正整数")
    if not 0.0 <= config.dropout < 1.0:
        raise R2FinalExpertError("专家 dropout 必须位于 [0,1)")


class _CausalExpertBase:
    """统一的因果专家实现骨架。"""

    def __new__(cls, *args: object, **kwargs: object) -> Any:
        torch = _load_torch()

        class TorchExpert(torch.nn.Module):
            def __init__(self, config: ExpertConfig) -> None:
                super().__init__()
                _validate_config(config)
                self.config = config
                self.input_projection = torch.nn.Linear(
                    config.input_dimension,
                    config.hidden_dimension,
                )
                self.encoder = torch.nn.GRU(
                    input_size=config.hidden_dimension,
                    hidden_size=config.hidden_dimension,
                    num_layers=config.layer_count,
                    dropout=config.dropout if config.layer_count > 1 else 0.0,
                    batch_first=True,
                )
                self.representation_head = torch.nn.Sequential(
                    torch.nn.LayerNorm(config.hidden_dimension),
                    torch.nn.Linear(
                        config.hidden_dimension,
                        config.representation_dimension,
                    ),
                )
                self.state_head = torch.nn.Linear(
                    config.hidden_dimension,
                    config.state_dimension,
                )

            def _validate_inputs(self, observations: Any, valid_mask: Any) -> None:
                if observations.ndim != 3:
                    raise R2FinalExpertError("专家观测必须为 [批量,窗口,字段]")
                if observations.shape[-1] != self.config.input_dimension:
                    raise R2FinalExpertError("专家观测字段维数与冻结配置不一致")
                if valid_mask.shape != observations.shape[:2]:
                    raise R2FinalExpertError("专家有效窗口掩码形状不一致")
                if valid_mask.dtype != torch.bool:
                    raise R2FinalExpertError("专家有效窗口掩码必须为布尔张量")
                if not bool(torch.isfinite(observations).all().item()):
                    raise R2FinalExpertError("专家观测包含非有限值")
                lengths = valid_mask.to(dtype=torch.int64).sum(dim=1)
                positions = torch.arange(valid_mask.shape[1], device=valid_mask.device).unsqueeze(0)
                expected = positions < lengths.unsqueeze(1)
                if not bool(torch.equal(valid_mask, expected)):
                    raise R2FinalExpertError("有效窗口必须构成非空前缀")

            def _encode(self, observations: Any, valid_mask: Any) -> tuple[Any, Any]:
                self._validate_inputs(observations, valid_mask)
                projected = torch.nn.functional.gelu(self.input_projection(observations))
                encoded, _ = self.encoder(projected)
                encoded = encoded * valid_mask.unsqueeze(-1).to(encoded.dtype)
                lengths = valid_mask.to(dtype=torch.int64).sum(dim=1)
                final_index = torch.clamp(lengths - 1, min=0)
                batch_index = torch.arange(encoded.shape[0], device=encoded.device)
                final_state = encoded[batch_index, final_index]
                return encoded, final_state

            def _physics_residual(
                self,
                observations: Any,
                encoded: Any,
                state: Any,
                valid_mask: Any,
                residual_context: ResidualObservationContext | None,
            ) -> Any:
                del observations, encoded, state, valid_mask, residual_context
                raise R2FinalExpertError(f"专家 {self.config.name} 尚未定义固定物理残差")

            def fixed_residual_from_state(
                self,
                state: Any,
                residual_context: ResidualObservationContext | None = None,
            ) -> Any:
                """仅供运行时收据直接审计固定残差算子。"""

                if state.ndim != 3 or state.shape[-1] != self.config.state_dimension:
                    raise R2FinalExpertError("固定残差审计状态形状不一致")
                valid = torch.ones(state.shape[:2], dtype=torch.bool, device=state.device)
                return self._physics_residual(None, None, state, valid, residual_context)

            def forward(
                self,
                observations: Any,
                valid_mask: Any,
                active_mask: Any | None = None,
                residual_context: ResidualObservationContext | None = None,
            ) -> ExpertOutput:
                if active_mask is None:
                    active_mask = torch.ones(
                        observations.shape[0],
                        dtype=torch.bool,
                        device=observations.device,
                    )
                if active_mask.shape != observations.shape[:1]:
                    raise R2FinalExpertError("专家激活掩码形状不一致")
                active = active_mask.detach().to(dtype=torch.bool)
                encoded, final_state = self._encode(observations, valid_mask)
                predicted_state = torch.nn.functional.softplus(self.state_head(encoded))
                if bool(active.any().item()):
                    residual = self._physics_residual(
                        observations,
                        encoded,
                        predicted_state,
                        valid_mask,
                        residual_context,
                    )
                else:
                    residual = torch.zeros(
                        *predicted_state.shape[:-1],
                        self.config.residual_dimension,
                        dtype=predicted_state.dtype,
                        device=predicted_state.device,
                    )
                window_active = valid_mask & active.unsqueeze(1)
                representation = self.representation_head(final_state)
                window_representation = self.representation_head(encoded)
                has_history = valid_mask.any(dim=1)
                representation = representation * has_history.unsqueeze(1).to(representation.dtype)
                representation = representation * active.unsqueeze(1).to(representation.dtype)
                window_representation = window_representation * window_active.unsqueeze(-1).to(
                    window_representation.dtype
                )
                predicted_state = predicted_state * window_active.unsqueeze(-1).to(
                    predicted_state.dtype
                )
                residual = residual * window_active.unsqueeze(-1).to(residual.dtype)
                return ExpertOutput(
                    representation=representation,
                    window_representation=window_representation,
                    predicted_state=predicted_state,
                    physics_residual=residual,
                    valid_mask=valid_mask,
                    active_mask=active,
                    expert_name=self.config.name,
                )

        return TorchExpert(*args, **kwargs)


@register_physics_expert(EXPERT_SHARED)
class SharedConservationExpert(_CausalExpertBase):
    """显式计算有限队列守恒残差的共享专家。"""

    def __new__(cls, config: ExpertConfig) -> Any:
        expert = super().__new__(cls, config)
        torch = _load_torch()

        def shared_residual(
            self: Any,
            observations: Any,
            encoded: Any,
            state: Any,
            valid_mask: Any,
            residual_context: ResidualObservationContext | None,
        ) -> Any:
            del observations, encoded, residual_context
            if state.shape[-1] < 5:
                raise R2FinalExpertError(
                    "共享守恒专家至少需要队列起点、终点、到达、服务和丢弃五个状态"
                )
            queue_start = state[..., 0]
            queue_end = state[..., 1]
            arrived = state[..., 2]
            served = state[..., 3]
            dropped = state[..., 4:].sum(dim=-1)
            balance = queue_end - queue_start - arrived + served + dropped
            balance = balance.unsqueeze(-1)
            if self.config.residual_dimension == 1:
                return balance
            padding = torch.zeros(
                *balance.shape[:-1],
                self.config.residual_dimension - 1,
                dtype=balance.dtype,
                device=balance.device,
            )
            return torch.cat((balance, padding), dim=-1)

        expert._physics_residual = shared_residual.__get__(expert, type(expert))
        expert.residual_contract = "finite_queue_l3_balance_v1"
        expert.formal_dynamics_ready = True
        return expert


@register_physics_expert(EXPERT_TCP)
class TcpDynamicsExpert(_CausalExpertBase):
    """使用公共窗口级有效 TCP 状态计算固定均场动力学残差。"""

    def __new__(cls, config: ExpertConfig) -> Any:
        expert = super().__new__(cls, config)
        torch = _load_torch()
        expected = (
            "truth_tcp_cwnd_start_bytes",
            "truth_tcp_cwnd_end_bytes",
            "truth_tcp_ssthresh_start_bytes",
            "truth_tcp_ssthresh_end_bytes",
            "truth_tcp_bytes_in_flight_start_bytes",
            "truth_tcp_bytes_in_flight_end_bytes",
            "truth_tcp_acked_bytes",
            "truth_tcp_loss_event_count",
            "truth_tcp_timeout_event_count",
            "truth_tcp_rtt_mean_ms",
        )
        if config.required_truth_fields != expected:
            raise R2FinalExpertError("TCP 网络级状态字段不符合冻结顺序")

        def tcp_phase_masks(
            self: Any,
            context: ResidualObservationContext,
            valid_mask: Any,
        ) -> Any:
            del self
            observed_state = context.observed_state.detach()
            observed_mask = context.observed_mask.detach().to(dtype=torch.bool)
            growth_observed, contraction_observed = _tcp_phase_observation_availability(
                observed_mask
            )
            loss_observed = observed_state[..., 7] > 0.0
            timeout_observed = observed_state[..., 8] > 0.0
            timeout_phase = contraction_observed & timeout_observed
            loss_phase = contraction_observed & loss_observed & ~timeout_observed
            growth_phase = growth_observed & ~loss_observed & ~timeout_observed
            slow_start_phase = growth_phase & (observed_state[..., 0] < observed_state[..., 2])
            congestion_avoidance_phase = growth_phase & ~slow_start_phase
            masks = torch.stack(
                (
                    slow_start_phase,
                    congestion_avoidance_phase,
                    loss_phase,
                    timeout_phase,
                ),
                dim=-1,
            )
            return masks & valid_mask.unsqueeze(-1)

        def tcp_residual(
            self: Any,
            observations: Any,
            encoded: Any,
            state: Any,
            valid_mask: Any,
            residual_context: ResidualObservationContext | None,
        ) -> Any:
            del observations, encoded
            if state.shape[-1] != 10:
                raise R2FinalExpertError("TCP v2 状态维数必须为 10")
            if self.config.residual_dimension != 4:
                raise R2FinalExpertError("TCP v3 固定残差维数必须为 4")
            if residual_context is None:
                return torch.zeros(
                    *state.shape[:-1],
                    4,
                    dtype=state.dtype,
                    device=state.device,
                )
            observed_state = residual_context.observed_state.detach()
            observed_mask = residual_context.observed_mask.detach().to(dtype=torch.bool)
            if observed_state.shape != state.shape or observed_mask.shape != state.shape:
                raise R2FinalExpertError("TCP 残差观测上下文形状与预测状态不一致")
            cwnd_start = state[..., 0]
            cwnd_end = state[..., 1]
            ssthresh_end = state[..., 3]
            bytes_in_flight_start = state[..., 4]
            bytes_in_flight_end = state[..., 5]
            acked_bytes = state[..., 6]
            # 所有字节状态已按 1e6 缩放；MSS 固定为场景合同中的 1448 字节。
            mss = 1448.0 / 1_000_000.0
            masks = tcp_phase_masks(self, residual_context, valid_mask)
            if bool((masks.to(dtype=torch.int64).sum(dim=-1) > 1).any().item()):
                raise R2FinalExpertError("TCP 四段残差掩码必须互斥")
            # RTT 仅作停止梯度的无量纲条件尺度，不改变残差零点。
            observed_rtt_s = torch.clamp(observed_state[..., 9], min=0.001, max=0.100)
            rtt_scale = (observed_rtt_s / 0.100).detach()
            slow_start_balance = rtt_scale * (cwnd_end - cwnd_start - acked_bytes)
            additive_growth = acked_bytes * mss / torch.clamp(cwnd_start, min=mss)
            congestion_avoidance_balance = rtt_scale * (cwnd_end - cwnd_start - additive_growth)
            loss_target = torch.maximum(
                bytes_in_flight_start * 0.5,
                torch.full_like(bytes_in_flight_start, 2.0 * mss),
            )
            loss_components = torch.stack(
                (
                    ssthresh_end - loss_target,
                    cwnd_end - ssthresh_end,
                    torch.relu(bytes_in_flight_end - cwnd_end),
                ),
                dim=-1,
            )
            timeout_components = torch.stack(
                (
                    ssthresh_end - loss_target,
                    cwnd_end - mss,
                    torch.relu(bytes_in_flight_end - cwnd_end),
                ),
                dim=-1,
            )
            epsilon = torch.finfo(state.dtype).eps
            loss_balance = torch.sqrt(
                torch.square(loss_components).sum(dim=-1) + epsilon
            ) - math.sqrt(epsilon)
            timeout_balance = torch.sqrt(
                torch.square(timeout_components).sum(dim=-1) + epsilon
            ) - math.sqrt(epsilon)
            phase_residuals = torch.stack(
                (
                    slow_start_balance,
                    congestion_avoidance_balance,
                    loss_balance,
                    timeout_balance,
                ),
                dim=-1,
            )
            return phase_residuals * masks.to(dtype=state.dtype)

        expert._physics_residual = tcp_residual.__get__(expert, type(expert))
        expert.residual_phase_masks = tcp_phase_masks.__get__(expert, type(expert))
        expert.residual_contract = (
            "tcp_network_aggregate_newreno_mean_field_mutually_exclusive_window_v4"
        )
        expert.formal_dynamics_ready = True
        expert.missing_dynamics_fields = tuple()
        return expert


@register_physics_expert(EXPERT_UDP)
class UdpDynamicsExpert(_CausalExpertBase):
    """使用计划、发送与应用丢弃量计算固定 UDP 守恒残差。"""

    def __new__(cls, config: ExpertConfig) -> Any:
        expert = super().__new__(cls, config)
        torch = _load_torch()
        expected = (
            "truth_udp_planned_app_payload_packets",
            "truth_udp_planned_app_payload_bytes",
            "truth_udp_actual_send_packets",
            "truth_udp_actual_send_bytes",
            "truth_udp_app_drop_packets",
            "truth_udp_app_drop_bytes",
        )
        if config.required_truth_fields != expected:
            raise R2FinalExpertError("UDP 状态字段不符合 v2 冻结顺序")

        def udp_residual(
            self: Any,
            observations: Any,
            encoded: Any,
            state: Any,
            valid_mask: Any,
            residual_context: ResidualObservationContext | None,
        ) -> Any:
            del observations, encoded, valid_mask, residual_context
            if state.shape[-1] != 6:
                raise R2FinalExpertError("UDP v2 状态维数必须为 6")
            packet_balance = state[..., 0] - state[..., 2] - state[..., 4]
            byte_balance = state[..., 1] - state[..., 3] - state[..., 5]
            residual = torch.stack((packet_balance, byte_balance), dim=-1)
            if self.config.residual_dimension != 2:
                raise R2FinalExpertError("UDP v2 固定残差维数必须为 2")
            return residual

        expert._physics_residual = udp_residual.__get__(expert, type(expert))
        expert.residual_contract = "udp_application_send_conservation_v2"
        expert.formal_dynamics_ready = True
        expert.missing_dynamics_fields = tuple()
        return expert


@register_physics_expert(EXPERT_QUIC)
class QuicDynamicsExpert(_CausalExpertBase):
    """仅在 qlog 同等级真值可用时启用的 QUIC 专家。"""

    def __new__(cls, config: ExpertConfig) -> Any:
        expert = super().__new__(cls, config)
        expert.residual_contract = "quic_not_ready_v1"
        expert.formal_dynamics_ready = False
        return expert


@register_physics_expert(EXPERT_UNKNOWN)
class UnknownFallbackExpert(_CausalExpertBase):
    """未知协议回退表示；不声明专属物理残差。"""

    def __new__(cls, config: ExpertConfig) -> Any:
        torch = _load_torch()

        class TorchUnknownFallback(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                _validate_config(config)
                self.config = config

            def forward(
                self,
                observations: Any,
                valid_mask: Any,
                active_mask: Any | None = None,
                residual_context: ResidualObservationContext | None = None,
            ) -> ExpertOutput:
                del residual_context
                if observations.ndim != 3 or observations.shape[-1] != config.input_dimension:
                    raise R2FinalExpertError("UNKNOWN 观测形状与冻结配置不一致")
                if valid_mask.shape != observations.shape[:2] or valid_mask.dtype != torch.bool:
                    raise R2FinalExpertError("UNKNOWN 有效窗口掩码非法")
                if active_mask is None:
                    active_mask = torch.ones(
                        observations.shape[0], dtype=torch.bool, device=observations.device
                    )
                if active_mask.shape != observations.shape[:1]:
                    raise R2FinalExpertError("UNKNOWN 激活掩码形状不一致")
                active = active_mask.detach().to(dtype=torch.bool)
                window_active = valid_mask & active.unsqueeze(1)
                zeros = observations.sum(dim=-1, keepdim=True) * 0.0
                return ExpertOutput(
                    representation=torch.zeros(
                        observations.shape[0],
                        config.representation_dimension,
                        dtype=observations.dtype,
                        device=observations.device,
                    ),
                    window_representation=torch.zeros(
                        observations.shape[0],
                        observations.shape[1],
                        config.representation_dimension,
                        dtype=observations.dtype,
                        device=observations.device,
                    ),
                    predicted_state=zeros.expand(-1, -1, config.state_dimension),
                    physics_residual=zeros.expand(-1, -1, config.residual_dimension),
                    valid_mask=valid_mask,
                    active_mask=active,
                    expert_name=config.name,
                )

        return TorchUnknownFallback()


class UnifiedPhysicsControlSystem:
    """不使用协议路由、但与正式 TCP/UDP 支路等容量的训练控制支路。"""

    def __new__(
        cls,
        *,
        shared: ExpertConfig,
        tcp_shape: ExpertConfig,
        udp_shape: ExpertConfig,
    ) -> Any:
        torch = _load_torch()

        class TorchUnifiedControl(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                if shared.name != EXPERT_SHARED:
                    raise R2FinalExpertError("统一控制支路共享专家配置名称错误")
                if tcp_shape.name != EXPERT_TCP or udp_shape.name != EXPERT_UDP:
                    raise R2FinalExpertError("统一控制支路动态组件配置名称错误")
                dimensions = {
                    shared.input_dimension,
                    tcp_shape.input_dimension,
                    udp_shape.input_dimension,
                }
                representations = {
                    shared.representation_dimension,
                    tcp_shape.representation_dimension,
                    udp_shape.representation_dimension,
                }
                if len(dimensions) != 1 or len(representations) != 1:
                    raise R2FinalExpertError("统一控制支路输入或表示维数不一致")
                self.shared = create_physics_expert(shared)
                self.components = torch.nn.ModuleDict(
                    {
                        "tcp_shape": create_physics_expert(tcp_shape),
                        "udp_shape": create_physics_expert(udp_shape),
                    }
                )
                self.representation_dimension = shared.representation_dimension

            def forward(
                self,
                observations: Any,
                valid_mask: Any,
                residual_contexts: Mapping[str, ResidualObservationContext] | None = None,
            ) -> RoutedPhysicsOutput:
                contexts = residual_contexts or {}
                shared_output = self.shared(observations, valid_mask)
                tcp_output = self.components["tcp_shape"](
                    observations,
                    valid_mask,
                    residual_context=contexts.get(EXPERT_TCP),
                )
                udp_output = self.components["udp_shape"](observations, valid_mask)
                representation = shared_output.representation + 0.5 * (
                    tcp_output.representation + udp_output.representation
                )
                sidecar_sequence = shared_output.window_representation + 0.5 * (
                    tcp_output.window_representation + udp_output.window_representation
                )
                batch_size = observations.shape[0]
                hard_masks = torch.zeros(
                    batch_size,
                    len(ROUTE_NAMES),
                    dtype=torch.bool,
                    device=observations.device,
                )
                hard_masks[:, ROUTE_TO_INDEX["UNKNOWN"]] = True
                return RoutedPhysicsOutput(
                    representation=representation,
                    sidecar_sequence=sidecar_sequence,
                    shared=shared_output,
                    protocol_outputs={"TCP": tcp_output, "UDP": udp_output},
                    effective_route_index=torch.full(
                        (batch_size,),
                        ROUTE_TO_INDEX["UNKNOWN"],
                        dtype=torch.int64,
                        device=observations.device,
                    ),
                    hard_masks=hard_masks,
                    stopped_confidence=torch.ones(
                        batch_size, dtype=observations.dtype, device=observations.device
                    ),
                    quic_structurally_closed_count=0,
                    routing_audit={"UNIFIED": batch_size},
                )

            def freeze_for_classification(self) -> None:
                for parameter in self.parameters():
                    parameter.requires_grad_(False)
                self.eval()

            def assert_classification_isolation(self) -> None:
                trainable = [
                    name for name, parameter in self.named_parameters() if parameter.requires_grad
                ]
                if trainable:
                    raise R2FinalExpertError(
                        "分类阶段统一控制支路仍有可训练参数：" + ",".join(trainable)
                    )

        return TorchUnifiedControl()


class ProtocolAdaptivePhysicsSystem:
    """组合共享守恒、协议动力学和 UNKNOWN 回退的统一系统。"""

    def __new__(
        cls,
        *,
        shared: ExpertConfig,
        tcp: ExpertConfig,
        udp: ExpertConfig,
        quic: ExpertConfig,
        unknown: ExpertConfig,
        quic_expert_ready: bool,
    ) -> Any:
        torch = _load_torch()

        class TorchSystem(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                configs = {
                    EXPERT_SHARED: shared,
                    EXPERT_TCP: tcp,
                    EXPERT_UDP: udp,
                    EXPERT_QUIC: quic,
                    EXPERT_UNKNOWN: unknown,
                }
                representation_dimensions = {
                    item.representation_dimension for item in configs.values()
                }
                input_dimensions = {item.input_dimension for item in configs.values()}
                if len(representation_dimensions) != 1 or len(input_dimensions) != 1:
                    raise R2FinalExpertError("所有专家必须共享输入维数和表示维数")
                if shared.name != EXPERT_SHARED:
                    raise R2FinalExpertError("共享专家配置名称错误")
                expected = {
                    EXPERT_TCP: tcp,
                    EXPERT_UDP: udp,
                    EXPERT_QUIC: quic,
                    EXPERT_UNKNOWN: unknown,
                }
                for expected_name, item in expected.items():
                    if item.name != expected_name:
                        raise R2FinalExpertError(f"协议专家配置名称错误：预期 {expected_name}")
                self.shared = create_physics_expert(shared)
                self.protocol_experts = torch.nn.ModuleDict(
                    {
                        "TCP": create_physics_expert(tcp),
                        "UDP": create_physics_expert(udp),
                        "QUIC": create_physics_expert(quic),
                        "UNKNOWN": create_physics_expert(unknown),
                    }
                )
                # 模块可训练不等于检查点可参与正式推理路由。
                self.quic_expert_ready = bool(quic_expert_ready)
                self.representation_dimension = shared.representation_dimension

            def _effective_routes(self, route: RouteBatch) -> tuple[Any, Any, int]:
                route_index = route.route_index.detach().to(dtype=torch.int64)
                confidence = route.confidence.detach()
                quic_applicable = route.quic_applicable.detach().to(dtype=torch.bool)
                if route_index.ndim != 1:
                    raise R2FinalExpertError("协议路由索引必须为一维")
                if confidence.shape != route_index.shape:
                    raise R2FinalExpertError("协议置信度形状不一致")
                if quic_applicable.shape != route_index.shape:
                    raise R2FinalExpertError("QUIC 推理适用掩码形状不一致")
                if bool(((route_index < 0) | (route_index >= len(ROUTE_NAMES))).any().item()):
                    raise R2FinalExpertError("协议路由索引超出冻结枚举")
                if not bool(torch.isfinite(confidence).all().item()):
                    raise R2FinalExpertError("协议置信度包含非有限值")
                if bool(((confidence < 0) | (confidence > 1)).any().item()):
                    raise R2FinalExpertError("协议置信度必须位于 [0,1]")
                effective = route_index.clone()
                quic_requested = route_index == ROUTE_TO_INDEX["QUIC"]
                quic_closed = quic_requested & ((~quic_applicable) | (not self.quic_expert_ready))
                effective[quic_closed] = ROUTE_TO_INDEX["UNKNOWN"]
                return effective, confidence, int(quic_closed.sum().item())

            def forward(
                self,
                observations: Any,
                valid_mask: Any,
                route: RouteBatch,
                residual_contexts: Mapping[str, ResidualObservationContext] | None = None,
            ) -> RoutedPhysicsOutput:
                contexts = residual_contexts or {}
                effective, confidence, quic_closed_count = self._effective_routes(route)
                hard_masks = torch.nn.functional.one_hot(
                    effective,
                    num_classes=len(ROUTE_NAMES),
                ).to(dtype=torch.bool)
                if bool((hard_masks.sum(dim=1) != 1).any().item()):
                    raise R2FinalExpertError("每个样本必须恰好激活一个协议路由")
                shared_output = self.shared(observations, valid_mask)
                combined = shared_output.representation
                sidecar_sequence = shared_output.window_representation
                protocol_outputs: dict[str, ExpertOutput] = {}
                routing_audit: dict[str, int] = {}
                for index, route_name in enumerate(ROUTE_NAMES):
                    active = hard_masks[:, index]
                    output = self.protocol_experts[route_name](
                        observations,
                        valid_mask,
                        active,
                        residual_context=contexts.get(
                            {
                                "TCP": EXPERT_TCP,
                                "UDP": EXPERT_UDP,
                                "QUIC": EXPERT_QUIC,
                                "UNKNOWN": EXPERT_UNKNOWN,
                            }[route_name]
                        ),
                    )
                    protocol_outputs[route_name] = output
                    strength = active.to(combined.dtype) * confidence
                    combined = combined + output.representation * strength.unsqueeze(1)
                    sidecar_sequence = sidecar_sequence + output.window_representation * (
                        strength.unsqueeze(1).unsqueeze(2)
                    )
                    routing_audit[route_name] = int(active.sum().item())
                if bool(
                    (
                        hard_masks[:, ROUTE_TO_INDEX["UDP"]]
                        & (route.route_index.detach() == ROUTE_TO_INDEX["QUIC"])
                    )
                    .any()
                    .item()
                ):
                    raise R2FinalExpertError("QUIC 样本不得回退到 UDP 专家")
                return RoutedPhysicsOutput(
                    representation=combined,
                    sidecar_sequence=sidecar_sequence,
                    shared=shared_output,
                    protocol_outputs=protocol_outputs,
                    effective_route_index=effective,
                    hard_masks=hard_masks,
                    stopped_confidence=confidence,
                    quic_structurally_closed_count=quic_closed_count,
                    routing_audit=routing_audit,
                )

            def freeze_for_classification(self) -> None:
                """冻结全部物理参数，隔离攻击分类梯度。"""

                for parameter in self.parameters():
                    parameter.requires_grad_(False)
                self.eval()

            def assert_classification_isolation(self) -> None:
                """确认分类阶段没有可训练物理或路由参数。"""

                trainable = [
                    name for name, parameter in self.named_parameters() if parameter.requires_grad
                ]
                if trainable:
                    raise R2FinalExpertError("分类阶段仍存在可训练物理参数：" + ",".join(trainable))

        return TorchSystem()


def fixed_residual_zero_collapse_receipt(system: Any) -> Mapping[str, object]:
    """逐方程证明固定残差不可由预测事件门控坍缩。"""

    torch = _load_torch()
    cases = {
        EXPERT_SHARED: (
            system.shared,
            [[[0.10, 0.70, 0.80, 0.10, 0.00, 0.00]]],
        ),
        EXPERT_UDP: (
            system.protocol_experts["UDP"],
            [[[10.0, 0.012, 8.0, 0.009, 1.0, 0.001]]],
        ),
    }
    experts: dict[str, Mapping[str, object]] = {}
    for name, (expert, values) in cases.items():
        legacy_parameters = [
            parameter_name
            for parameter_name, _ in expert.named_parameters()
            if parameter_name.startswith("transition_head")
            or parameter_name.startswith("residual_projection")
        ]
        if legacy_parameters:
            raise R2FinalExpertError(f"固定残差仍含旧可训练投影：{name}={legacy_parameters}")
        state = torch.tensor(values, dtype=torch.float32, requires_grad=True)
        residual_before = expert.fixed_residual_from_state(state)
        squared = torch.square(residual_before).sum()
        gradient = torch.autograd.grad(squared, state, retain_graph=True)[0]
        residual_after = expert.fixed_residual_from_state(state)
        residual_norm = float(torch.linalg.vector_norm(residual_before).item())
        gradient_norm = float(torch.linalg.vector_norm(gradient).item())
        invariance_difference = float(torch.max(torch.abs(residual_before - residual_after)).item())
        if residual_norm <= 0.0:
            raise R2FinalExpertError(f"固定残差非平凡输入仍为零：{name}")
        if gradient_norm <= 0.0:
            raise R2FinalExpertError(f"固定残差未向预测状态传递梯度：{name}")
        if invariance_difference != 0.0:
            raise R2FinalExpertError(f"固定残差重复计算不一致：{name}")
        experts[name] = {
            "residual_contract": str(expert.residual_contract),
            "residual_operator_trainable_parameter_count": 0,
            "legacy_projection_parameter_count": 0,
            "legacy_projection_removed": True,
            "legacy_projection_zero_invariance_max_abs_difference": invariance_difference,
            "constructed_residual_l2": residual_norm,
            "predicted_state_gradient_l2": gradient_norm,
            "formal_dynamics_ready": bool(expert.formal_dynamics_ready),
        }
    tcp = system.protocol_experts["TCP"]
    tcp_legacy_parameters = [
        parameter_name
        for parameter_name, _ in tcp.named_parameters()
        if parameter_name.startswith("transition_head")
        or parameter_name.startswith("residual_projection")
    ]
    if tcp_legacy_parameters:
        raise R2FinalExpertError(f"TCP 固定残差仍含旧可训练投影：{tcp_legacy_parameters}")
    tcp_values = [
        [
            [0.010, 0.020, 0.020, 0.018, 0.012, 0.008, 0.004, 0.0, 0.0, 0.025],
            [0.020, 0.025, 0.015, 0.015, 0.022, 0.018, 0.010, 0.0, 0.0, 0.030],
            [0.020, 0.012, 0.015, 0.010, 0.030, 0.020, 0.004, 0.0, 0.0, 0.025],
            [0.020, 0.004, 0.015, 0.008, 0.040, 0.012, 0.002, 0.0, 0.0, 0.040],
        ]
    ]
    observed_values = [
        [
            [0.010, 0.020, 0.020, 0.018, 0.012, 0.008, 0.004, 0.0, 0.0, 0.025],
            [0.020, 0.025, 0.015, 0.015, 0.022, 0.018, 0.010, 0.0, 0.0, 0.030],
            [0.020, 0.012, 0.015, 0.010, 0.030, 0.020, 0.004, 1.0, 0.0, 0.025],
            [0.020, 0.004, 0.015, 0.008, 0.040, 0.012, 0.002, 1.0, 1.0, 0.040],
        ]
    ]
    tcp_state = torch.tensor(tcp_values, dtype=torch.float32, requires_grad=True)
    observed_state = torch.tensor(observed_values, dtype=torch.float32, requires_grad=True)
    observed_mask = torch.ones_like(observed_state, dtype=torch.bool)
    context = ResidualObservationContext(observed_state, observed_mask)
    tcp_residual = tcp.fixed_residual_from_state(tcp_state, context)
    phase_masks = tcp.residual_phase_masks(
        context,
        torch.ones(tcp_state.shape[:2], dtype=torch.bool),
    )
    expected_masks = torch.eye(4, dtype=torch.bool).unsqueeze(0)
    if not bool(torch.equal(phase_masks, expected_masks)):
        raise R2FinalExpertError("TCP 慢启动、拥塞避免、损失与 RTO 掩码不互斥")
    equation_values = tcp_residual[0].diagonal()
    equation_names = ("slow_start", "congestion_avoidance", "loss", "rto")
    equation_receipts: dict[str, Mapping[str, object]] = {}
    for index, equation_name in enumerate(equation_names):
        value = equation_values[index]
        gradient = torch.autograd.grad(torch.square(value), tcp_state, retain_graph=True)[0]
        gradient_norm = float(torch.linalg.vector_norm(gradient).item())
        residual_abs = float(torch.abs(value).item())
        if residual_abs <= 0.0 or gradient_norm <= 0.0:
            raise R2FinalExpertError(f"TCP 方程缺少非平凡残差或梯度：{equation_name}")
        equation_receipts[equation_name] = {
            "constructed_residual_abs": residual_abs,
            "predicted_state_gradient_l2": gradient_norm,
            "observed_phase_mask": True,
        }
    total_tcp_loss = torch.square(equation_values).sum()
    total_tcp_gradient = torch.autograd.grad(total_tcp_loss, tcp_state, retain_graph=True)[0]
    critical_endpoint_gradients = {
        "cwnd_end": float(torch.linalg.vector_norm(total_tcp_gradient[..., 1]).item()),
        "ssthresh_end": float(torch.linalg.vector_norm(total_tcp_gradient[..., 3]).item()),
        "bytes_in_flight_end": float(torch.linalg.vector_norm(total_tcp_gradient[..., 5]).item()),
    }
    if any(value <= 0.0 for value in critical_endpoint_gradients.values()):
        raise R2FinalExpertError("TCP 关键终点预测状态未获得非零梯度")
    perturbed_state = tcp_state.detach().clone()
    perturbed_state[..., 7] = 100.0
    perturbed_state[..., 8] = 100.0
    perturbed_state.requires_grad_(True)
    perturbed_residual = tcp.fixed_residual_from_state(perturbed_state, context)
    prediction_gate_difference = float(
        torch.max(torch.abs(tcp_residual - perturbed_residual)).item()
    )
    if prediction_gate_difference != 0.0:
        raise R2FinalExpertError("TCP 事件方程仍可被预测 loss/timeout 状态门控")
    observed_gradient = torch.autograd.grad(
        total_tcp_loss,
        observed_state,
        allow_unused=True,
    )[0]
    if observed_gradient is not None:
        raise R2FinalExpertError("TCP 观测阶段门未停止梯度")
    experts[EXPERT_TCP] = {
        "residual_contract": str(tcp.residual_contract),
        "residual_operator_trainable_parameter_count": 0,
        "legacy_projection_parameter_count": 0,
        "legacy_projection_removed": True,
        "equations": equation_receipts,
        "phase_masks_mutually_exclusive": True,
        "phase_mask_active_counts": [int(value) for value in phase_masks.sum(dim=(0, 1)).tolist()],
        "predicted_event_gate_max_abs_difference": prediction_gate_difference,
        "observed_event_phase_gate_stopped_gradient": True,
        "critical_endpoint_gradient_l2": critical_endpoint_gradients,
        "formal_dynamics_ready": bool(tcp.formal_dynamics_ready),
    }
    formal_ready = all(
        bool(experts[name]["formal_dynamics_ready"]) for name in (EXPERT_TCP, EXPERT_UDP)
    )
    return {
        "schema_version": "r2_fixed_residual_zero_collapse_receipt_v2",
        "experts": experts,
        "protocol_residual_operator_trainable_parameter_count": 0,
        "nontrivial_residual_positive": True,
        "predicted_state_gradient_nonzero": True,
        "per_equation_nontrivial_gradient": True,
        "predicted_event_gate_invariant": True,
        "critical_tcp_endpoint_gradient_nonzero": True,
        "formal_tcp_udp_dynamics_ready": formal_ready,
        "blocking_reason": ("" if formal_ready else "TCP 或 UDP 固定动力学残差未通过运行时门禁"),
    }


def count_parameters(module: Any, *, trainable_only: bool = False) -> int:
    """计算模块参数量，用于 F-A/F-P 容量门禁。"""

    return sum(
        int(parameter.numel())
        for parameter in module.parameters()
        if not trainable_only or parameter.requires_grad
    )


def expert_registry_snapshot() -> dict[str, str]:
    """返回稳定的专家注册表摘要载荷。"""

    return {
        name: f"{expert_class.__module__}.{expert_class.__qualname__}"
        for name, expert_class in sorted(PHYSICS_EXPERT_REGISTRY.items())
    }


def expert_state_supervision_loss(
    output: ExpertOutput,
    supervision: PhysicsSupervisionBatch,
    *,
    expert_name: str,
) -> Any:
    """计算受适用真值掩码约束的状态监督损失。"""

    torch = _load_torch()
    if expert_name != output.expert_name:
        raise R2FinalExpertError(
            f"监督损失专家身份不一致：参数 {expert_name}，输出 {output.expert_name}"
        )
    truth = supervision.truth_state
    mask = supervision.truth_mask.detach().to(dtype=torch.bool)
    if truth.shape != output.predicted_state.shape or mask.shape != truth.shape:
        raise R2FinalExpertError("物理状态真值、预测和监督掩码形状不一致")
    if output.expert_name == EXPERT_QUIC:
        qlog_available = supervision.qlog_truth_available.detach().to(dtype=torch.bool)
        if qlog_available.shape != truth.shape[:1]:
            raise R2FinalExpertError("QUIC qlog 真值掩码形状不一致")
        mask = mask & qlog_available[:, None, None]
    active = mask & output.valid_mask[:, :, None] & output.active_mask[:, None, None]
    if not bool(active.any().item()):
        return output.predicted_state.sum() * 0.0
    absolute_error = torch.abs(output.predicted_state - truth)
    return absolute_error[active].mean()
