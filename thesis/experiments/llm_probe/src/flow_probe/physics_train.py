"""Qwen3-1.7B 的 M0、M1、M2 首轮物理一致性训练入口。"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import random
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import torch
import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.qwen_physics_gradient import select_last_token_hidden
from flow_probe.tracking import TrackingSettings, capture_console_log, swanlab_run

MODEL_INPUT_FIELDS = (
    "capacity_start_bps",
    "capacity_end_bps",
    "configured_capacity_integral_link_bytes",
    "qdisc_received_l3_bytes",
    "qdisc_received_packets",
)
AUDIT_RESIDUAL_FIELDS = (
    "queue_balance_residual_l3_bytes",
    "queue_balance_residual_packets",
)
STEP_METRIC_KEYS = (
    "train/total_loss",
    "train/generation_loss",
    "train/state_loss",
    "train/physics_loss",
    "train/lora_gradient_norm",
    "train/state_head_gradient_norm",
    "train/learning_rate",
    "train/throughput_samples_per_second",
    "train/peak_gpu_memory_mib",
)
VARIANTS = ("M0", "M1", "M2", "M2P")
STATE_SUPERVISION_MODES = ("dense", "anchor0_only", "anchor0_plus_one")


class PhysicsDataError(ValueError):
    """物理训练样本不满足字段或数值契约。"""


class PhysicsTrainingError(ValueError):
    """物理训练配置或运行状态不合法。"""


def resolve_lambda_physics(configured: float, override: float | None) -> float:
    """解析物理损失权重，并允许命令行执行单变量敏感性实验。"""
    value = float(configured if override is None else override)
    if not math.isfinite(value):
        raise PhysicsTrainingError("lambda_physics 必须为有限数")
    if value < 0:
        raise PhysicsTrainingError("lambda_physics 不得为负")
    return value


@dataclass(frozen=True)
class PhysicsGradientProjection:
    """物理梯度相对生成梯度的逐张量投影结果。"""

    gradients: tuple[torch.Tensor | None, ...]
    cosine_before: float
    cosine_after: float
    triggered: bool
    removed_component_ratio: float


@dataclass(frozen=True)
class M2PGradientDiagnostics:
    """M2P 梯度合成时的三个目标范数与投影信息。"""

    generation_norm: float
    state_norm: float
    physics_norm: float
    projection: PhysicsGradientProjection


def _gradient_sequence_stats(
    name: str, gradients: Sequence[torch.Tensor | None]
) -> tuple[float, float]:
    square_sum = 0.0
    present = False
    for gradient in gradients:
        if gradient is None:
            continue
        present = True
        value = gradient.detach().float()
        if not bool(torch.isfinite(value).all().item()):
            raise PhysicsTrainingError(f"{name}梯度包含非有限值")
        square_sum += float(value.square().sum().item())
    if not present or square_sum == 0.0:
        raise PhysicsTrainingError(f"{name}梯度严格为零")
    if not math.isfinite(square_sum):
        raise PhysicsTrainingError(f"{name}梯度范数非有限")
    return square_sum, math.sqrt(square_sum)


def _gradient_sequence_dot(
    left: Sequence[torch.Tensor | None],
    right: Sequence[torch.Tensor | None],
) -> float:
    if len(left) != len(right):
        raise PhysicsTrainingError("梯度参数张量数量不一致")
    total = 0.0
    for left_gradient, right_gradient in zip(left, right, strict=True):
        if left_gradient is None or right_gradient is None:
            continue
        if left_gradient.shape != right_gradient.shape:
            raise PhysicsTrainingError("梯度参数张量形状不一致")
        total += float(
            (left_gradient.detach().float() * right_gradient.detach().float()).sum().item()
        )
    if not math.isfinite(total):
        raise PhysicsTrainingError("梯度点积非有限")
    return total


def project_physics_gradients(
    generation_gradients: Sequence[torch.Tensor | None],
    physics_gradients: Sequence[torch.Tensor | None],
) -> PhysicsGradientProjection:
    """仅在负点积时移除物理梯度中损害生成目标的分量。"""
    generation_square, generation_norm = _gradient_sequence_stats("生成", generation_gradients)
    _, physics_norm = _gradient_sequence_stats("物理", physics_gradients)
    dot_before = _gradient_sequence_dot(generation_gradients, physics_gradients)
    cosine_before = dot_before / (generation_norm * physics_norm)
    triggered = dot_before < 0.0
    coefficient = dot_before / generation_square if triggered else 0.0
    projected: list[torch.Tensor | None] = []
    for generation, physics in zip(generation_gradients, physics_gradients, strict=True):
        if physics is None and generation is None:
            projected.append(None)
            continue
        if physics is None:
            projected.append(-coefficient * generation.detach().float())
            continue
        value = physics.detach().float().clone()
        if generation is not None and triggered:
            value = value - coefficient * generation.detach().float()
        projected.append(value)
    _, projected_norm = _gradient_sequence_stats("投影后物理", projected)
    dot_after = _gradient_sequence_dot(generation_gradients, projected)
    cosine_after = dot_after / (generation_norm * projected_norm)
    if triggered and cosine_after < -1e-6:
        raise PhysicsTrainingError("投影后物理梯度仍与生成梯度显著负相关")
    return PhysicsGradientProjection(
        gradients=tuple(projected),
        cosine_before=cosine_before,
        cosine_after=cosine_after,
        triggered=triggered,
        removed_component_ratio=abs(cosine_before) if triggered else 0.0,
    )


def _combine_gradient(
    parameter: torch.nn.Parameter,
    weighted_gradients: Sequence[tuple[float, torch.Tensor | None]],
) -> torch.Tensor | None:
    combined: torch.Tensor | None = None
    for weight, gradient in weighted_gradients:
        if gradient is None:
            continue
        value = float(weight) * gradient.detach().float()
        combined = value.clone() if combined is None else combined + value
    if combined is None:
        return None
    if combined.shape != parameter.shape or not bool(torch.isfinite(combined).all().item()):
        raise PhysicsTrainingError("合成梯度形状错误或包含非有限值")
    return combined.to(device=parameter.device, dtype=parameter.dtype)


def apply_m2p_gradients(
    lora_parameters: Sequence[torch.nn.Parameter],
    state_head_parameters: Sequence[torch.nn.Parameter],
    *,
    generation_gradients: Sequence[torch.Tensor | None],
    state_lora_gradients: Sequence[torch.Tensor | None],
    physics_lora_gradients: Sequence[torch.Tensor | None],
    state_head_state_gradients: Sequence[torch.Tensor | None],
    state_head_physics_gradients: Sequence[torch.Tensor | None],
    lambda_state: float,
    lambda_physics: float,
) -> M2PGradientDiagnostics:
    """为 LoRA 写入投影组合梯度，为状态头写入原始加权梯度。"""
    lora_count = len(lora_parameters)
    if not (
        len(generation_gradients)
        == len(state_lora_gradients)
        == len(physics_lora_gradients)
        == lora_count
    ):
        raise PhysicsTrainingError("LoRA 梯度参数数量不一致")
    if not (
        len(state_head_state_gradients)
        == len(state_head_physics_gradients)
        == len(state_head_parameters)
    ):
        raise PhysicsTrainingError("状态头梯度参数数量不一致")
    _, generation_norm = _gradient_sequence_stats("生成", generation_gradients)
    _, state_norm = _gradient_sequence_stats("状态", state_lora_gradients)
    _, physics_norm = _gradient_sequence_stats("物理", physics_lora_gradients)
    projection = project_physics_gradients(generation_gradients, physics_lora_gradients)
    for index, parameter in enumerate(lora_parameters):
        parameter.grad = _combine_gradient(
            parameter,
            (
                (1.0, generation_gradients[index]),
                (lambda_state, state_lora_gradients[index]),
                (lambda_physics, projection.gradients[index]),
            ),
        )
    for index, parameter in enumerate(state_head_parameters):
        parameter.grad = _combine_gradient(
            parameter,
            (
                (lambda_state, state_head_state_gradients[index]),
                (lambda_physics, state_head_physics_gradients[index]),
            ),
        )
    return M2PGradientDiagnostics(
        generation_norm=generation_norm,
        state_norm=state_norm,
        physics_norm=physics_norm,
        projection=projection,
    )


@dataclass(frozen=True)
class StateRecord:
    """状态监督所需的最小记录。"""

    sample_id: str
    prompt: str
    scale: float
    state_targets: tuple[float, ...]


@dataclass(frozen=True)
class PreparedPhysicsRecord(StateRecord):
    """M2 现场计算单窗口残差所需的训练期真值。"""

    capacity: tuple[float, ...]
    received: tuple[float, ...]
    dequeued: tuple[float, ...]
    dropped_before: tuple[float, ...]
    dropped_after: tuple[float, ...]


@dataclass(frozen=True)
class VariantContract:
    """三个变体除开关外共享的损失契约。"""

    name: str
    uses_state: bool
    uses_physics: bool
    uses_projection: bool
    state_head_outputs: int
    lambda_state: float
    lambda_physics: float


@dataclass(frozen=True)
class LossBreakdown:
    """一次联合目标的分项张量。"""

    total: torch.Tensor
    generation: torch.Tensor
    state: torch.Tensor | None
    physics: torch.Tensor | None


@dataclass(frozen=True)
class RunLayout:
    """单次运行必须生成的本地制品路径。"""

    output_dir: Path
    variant: str
    config_snapshot: Path
    environment: Path
    input_sha256: Path
    console_log: Path
    step_metrics: Path
    training_summary: Path
    final_adapter: Path
    state_head: Path
    physics_sample_order: Path
    artifact_manifest: Path

    @property
    def required_paths(self) -> tuple[Path, ...]:
        paths = [
            self.config_snapshot,
            self.environment,
            self.input_sha256,
            self.console_log,
            self.step_metrics,
            self.training_summary,
            self.final_adapter,
            self.artifact_manifest,
        ]
        if self.variant != "M0":
            paths.extend((self.state_head, self.physics_sample_order))
        return tuple(paths)


@dataclass(frozen=True)
class PhysicsTrainingSettings:
    """首轮训练使用的固定计算预算与数据路径。"""

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

    @property
    def effective_generation_batch_size(self) -> int:
        return self.generation_batch_size * self.gradient_accumulation_steps


class ContinuousQueueStateHead(torch.nn.Module):
    """从共享隐藏表示预测五个非负无量纲队列锚点。"""

    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(hidden_size, 5)
        self.activation = torch.nn.Softplus()

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        aligned_hidden = hidden.to(dtype=self.linear.weight.dtype)
        return self.activation(self.linear(aligned_hidden))


def _variant_name(value: str) -> str:
    normalized = str(value).upper()
    if normalized not in VARIANTS:
        raise PhysicsTrainingError(f"未知训练变体：{value}")
    return normalized


def build_variant_contract(
    variant: str,
    *,
    lambda_state: float,
    lambda_physics: float,
) -> VariantContract:
    """构造 M0、M1、M2、M2P 的唯一机制开关。"""
    name = _variant_name(variant)
    if lambda_state < 0 or lambda_physics < 0:
        raise PhysicsTrainingError("损失权重不得为负")
    return VariantContract(
        name=name,
        uses_state=name in {"M1", "M2", "M2P"},
        uses_physics=name in {"M2", "M2P"},
        uses_projection=name == "M2P",
        state_head_outputs=5,
        lambda_state=float(lambda_state),
        lambda_physics=float(lambda_physics),
    )


def compose_variant_loss(
    variant: str,
    generation_loss: torch.Tensor,
    state_loss_factory: Callable[[], torch.Tensor],
    physics_loss_factory: Callable[[], torch.Tensor],
    lambda_state: float,
    lambda_physics: float,
) -> LossBreakdown:
    """只调用当前变体声明的损失工厂，避免越界读取真值字段。"""
    contract = build_variant_contract(
        variant,
        lambda_state=lambda_state,
        lambda_physics=lambda_physics,
    )
    state_loss = None
    physics_loss = None
    total = generation_loss
    if contract.uses_state:
        state_loss = state_loss_factory()
        total = total + contract.lambda_state * state_loss
    if contract.uses_physics:
        physics_loss = physics_loss_factory()
        total = total + contract.lambda_physics * physics_loss
    return LossBreakdown(total, generation_loss, state_loss, physics_loss)


def _assert_no_audit_residual(value: object) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key) in AUDIT_RESIDUAL_FIELDS:
                raise PhysicsDataError("保存的审计残差不得进入训练数据接口")
            _assert_no_audit_residual(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_no_audit_residual(nested)


def _numeric_sequence(value: object, field: str, length: int) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise PhysicsDataError(f"{field} 必须包含 {length} 个数值")
    result = tuple(float(item) for item in value)
    if not all(math.isfinite(item) for item in result):
        raise PhysicsDataError(f"{field} 包含非有限数值")
    return result


def _model_inputs(sample: Mapping[str, object]) -> Mapping[str, object]:
    value = sample.get("model_inputs")
    if not isinstance(value, Mapping):
        raise PhysicsDataError("物理样本缺少 model_inputs")
    if set(value) != set(MODEL_INPUT_FIELDS):
        raise PhysicsDataError("model_inputs 必须且只能包含五个允许输入字段")
    return value


def build_physics_prompt(sample: Mapping[str, object]) -> str:
    """仅序列化四窗口五个可观测输入字段。"""
    inputs = _model_inputs(sample)
    columns = {field: _numeric_sequence(inputs[field], field, 4) for field in MODEL_INPUT_FIELDS}
    rows = []
    for index in range(4):
        values = ";".join(f"{field}={columns[field][index]:.12g}" for field in MODEL_INPUT_FIELDS)
        rows.append(f"窗口{index + 1}:{values}")
    return "四窗口队列观测\n" + "\n".join(rows)


def prepare_state_record(sample: Mapping[str, object]) -> StateRecord:
    """只读取 M1 所需的提示、公共尺度和五锚点真值。"""
    _assert_no_audit_residual(sample)
    inputs = _model_inputs(sample)
    capacity = _numeric_sequence(
        inputs["configured_capacity_integral_link_bytes"],
        "configured_capacity_integral_link_bytes",
        4,
    )
    if any(value <= 0 for value in capacity):
        raise PhysicsDataError("配置容量积分必须全部大于零")
    anchors = _numeric_sequence(
        sample.get("queue_boundary_anchors_l3_bytes"),
        "queue_boundary_anchors_l3_bytes",
        5,
    )
    scale = max(capacity)
    return StateRecord(
        sample_id=str(sample.get("sample_id", "")),
        prompt=build_physics_prompt(sample),
        scale=scale,
        state_targets=tuple(anchor / scale for anchor in anchors),
    )


def prepare_physics_record(sample: Mapping[str, object]) -> PreparedPhysicsRecord:
    """选择 M2 允许的 L3 通量，并拒绝保存的双零残差。"""
    state = prepare_state_record(sample)
    inputs = _model_inputs(sample)
    supervision = sample.get("state_supervision")
    if not isinstance(supervision, Mapping):
        raise PhysicsDataError("物理样本缺少 state_supervision")
    return PreparedPhysicsRecord(
        sample_id=state.sample_id,
        prompt=state.prompt,
        scale=state.scale,
        state_targets=state.state_targets,
        capacity=_numeric_sequence(
            inputs["configured_capacity_integral_link_bytes"],
            "configured_capacity_integral_link_bytes",
            4,
        ),
        received=_numeric_sequence(inputs["qdisc_received_l3_bytes"], "qdisc_received_l3_bytes", 4),
        dequeued=_numeric_sequence(
            supervision.get("qdisc_dequeued_l3_bytes"), "qdisc_dequeued_l3_bytes", 4
        ),
        dropped_before=_numeric_sequence(
            supervision.get("qdisc_dropped_before_enqueue_l3_bytes"),
            "qdisc_dropped_before_enqueue_l3_bytes",
            4,
        ),
        dropped_after=_numeric_sequence(
            supervision.get("qdisc_dropped_after_dequeue_l3_bytes"),
            "qdisc_dropped_after_dequeue_l3_bytes",
            4,
        ),
    )


def queue_balance_residual(
    predicted_queue: torch.Tensor,
    scale: torch.Tensor,
    capacity: torch.Tensor,
    received: torch.Tensor,
    dequeued: torch.Tensor,
    dropped_before: torch.Tensor,
    dropped_after: torch.Tensor,
) -> torch.Tensor:
    """现场计算四个无量纲单窗口 L3 字节守恒残差。"""
    if predicted_queue.ndim != 2 or predicted_queue.shape[1] != 5:
        raise PhysicsDataError("预测队列必须采用[批量, 5]形状")
    expected = (predicted_queue.shape[0], 4)
    fluxes = (capacity, received, dequeued, dropped_before, dropped_after)
    if any(value.shape != expected for value in fluxes):
        raise PhysicsDataError("容量和四类通量必须采用[批量, 4]形状")
    if scale.shape not in {(predicted_queue.shape[0],), (predicted_queue.shape[0], 1)}:
        raise PhysicsDataError("公共尺度必须按批量提供")
    predicted = predicted_queue.float()
    scale_f = scale.float().reshape(-1, 1)
    capacity_f = capacity.float()
    if torch.any(capacity_f <= 0):
        raise PhysicsDataError("配置容量积分必须严格大于零")
    numerator = (
        scale_f * (predicted[:, 1:] - predicted[:, :-1])
        - received.float()
        + dequeued.float()
        + dropped_before.float()
        + dropped_after.float()
    )
    return numerator / capacity_f


def state_target_loss(predicted: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """计算五锚点公共尺度状态均方误差。"""
    if predicted.shape != target.shape or predicted.ndim != 2 or predicted.shape[1] != 5:
        raise PhysicsDataError("状态预测与目标必须具有相同的[批量, 5]形状")
    return torch.nn.functional.mse_loss(predicted.float(), target.float())


def build_state_supervision_masks(
    records: Sequence[Mapping[str, object]], mode: str, seed: int
) -> dict[str, tuple[bool, bool, bool, bool, bool]]:
    """按唯一组确定性分配状态锚点，并以样本标识返回掩码。"""
    normalized_mode = str(mode).lower()
    if normalized_mode not in STATE_SUPERVISION_MODES:
        raise PhysicsTrainingError(f"未知状态监督模式：{mode}")
    samples: list[tuple[str, str]] = []
    sample_ids: set[str] = set()
    for record in records:
        sample_id = str(record.get("sample_id", "")).strip()
        group_id = str(record.get("group_id", "")).strip()
        if not sample_id or not group_id:
            raise PhysicsDataError("状态监督掩码要求非空 sample_id 和 group_id")
        if sample_id in sample_ids:
            raise PhysicsDataError(f"状态监督掩码发现重复 sample_id：{sample_id}")
        sample_ids.add(sample_id)
        samples.append((sample_id, group_id))

    group_masks: dict[str, tuple[bool, bool, bool, bool, bool]] = {}
    group_ids = sorted({group_id for _, group_id in samples})
    if normalized_mode == "dense":
        group_masks = {group_id: (True, True, True, True, True) for group_id in group_ids}
    elif normalized_mode == "anchor0_only":
        group_masks = {group_id: (True, False, False, False, False) for group_id in group_ids}
    else:
        ranked_groups = sorted(
            group_ids,
            key=lambda group_id: (
                hashlib.sha256(f"{int(seed)}:{group_id}".encode()).digest(),
                group_id,
            ),
        )
        for rank, group_id in enumerate(ranked_groups):
            internal_anchor = rank % 4 + 1
            group_masks[group_id] = tuple(index in {0, internal_anchor} for index in range(5))
    return {sample_id: group_masks[group_id] for sample_id, group_id in samples}


def masked_state_target_loss(
    predicted: torch.Tensor, target: torch.Tensor, mask: torch.Tensor
) -> torch.Tensor:
    """只对掩码标记的观测锚点计算均方误差。"""
    if predicted.shape != target.shape or predicted.ndim != 2 or predicted.shape[1] != 5:
        raise PhysicsDataError("状态预测与目标必须具有相同的[批量, 5]形状")
    if mask.shape != predicted.shape:
        raise PhysicsDataError("状态监督掩码必须与状态预测具有相同形状")
    selected = mask.to(device=predicted.device, dtype=torch.bool)
    if not bool(selected.any().item()):
        raise PhysicsDataError("状态监督掩码必须至少包含一个观测锚点")
    errors = (predicted.float() - target.float()).square()
    return errors.masked_select(selected).mean()


def _state_mask_sha256(
    masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> str:
    payload = [
        {"sample_id": sample_id, "mask": list(masks[sample_id])} for sample_id in sorted(masks)
    ]
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def physics_sample_schedule(
    sample_count: int,
    *,
    batch_size: int,
    steps: int,
    seed: int,
) -> tuple[tuple[int, ...], ...]:
    """生成与变体无关、每步等量的确定性样本顺序。"""
    if sample_count <= 0 or batch_size <= 0 or steps <= 0:
        raise PhysicsTrainingError("样本数、批量和步数必须大于零")
    generator = random.Random(seed)
    stream: list[int] = []
    required = batch_size * steps
    while len(stream) < required:
        epoch = list(range(sample_count))
        generator.shuffle(epoch)
        stream.extend(epoch)
    return tuple(
        tuple(stream[offset : offset + batch_size]) for offset in range(0, required, batch_size)
    )


def create_run_layout(output_dir: Path, variant: str) -> RunLayout:
    """原子创建不可复用的运行目录。"""
    name = _variant_name(variant)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    return RunLayout(
        output_dir=output_dir,
        variant=name,
        config_snapshot=output_dir / "config_snapshot.yaml",
        environment=output_dir / "environment.json",
        input_sha256=output_dir / "input_sha256.json",
        console_log=output_dir / "console.log",
        step_metrics=output_dir / "step_metrics.jsonl",
        training_summary=output_dir / "training_summary.json",
        final_adapter=output_dir / "final_adapter",
        state_head=output_dir / "state_head.pt",
        physics_sample_order=output_dir / "physics_sample_order.json",
        artifact_manifest=output_dir / "artifact_manifest.json",
    )


def validate_completed_artifacts(layout: RunLayout) -> None:
    """拒绝把缺少任一强制制品的运行标记为完成。"""
    missing = [str(path) for path in layout.required_paths if not path.exists()]
    if missing:
        raise PhysicsTrainingError("运行制品不完整：" + ", ".join(missing))


def record_step_metrics(
    path: Path,
    swanlab: object,
    *,
    step: int,
    metrics: Mapping[str, float],
) -> None:
    """同步持久化并在线记录一个优化步的全部强制指标。"""
    missing = sorted(set(STEP_METRIC_KEYS).difference(metrics))
    if missing:
        raise PhysicsTrainingError("逐步指标缺失：" + ", ".join(missing))
    normalized = {key: float(value) for key, value in metrics.items()}
    if not all(math.isfinite(value) for value in normalized.values()):
        raise PhysicsTrainingError("逐步指标必须全部为有限数值")
    with Path(path).open("a", encoding="utf-8") as target:
        target.write(json.dumps({"step": step, "metrics": normalized}, sort_keys=True) + "\n")
    swanlab.log(normalized, step=step)


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    with Path(path).open("r", encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "packages": {
            name: _package_version(name)
            for name in (
                "accelerate",
                "bitsandbytes",
                "peft",
                "swanlab",
                "transformers",
            )
        },
    }


def _input_manifest(settings: PhysicsTrainingSettings) -> dict[str, object]:
    files = {
        "generation_train": settings.generation_train_file,
        "generation_validation": settings.generation_validation_file,
        "physics_train": settings.physics_train_file,
        "physics_validation": settings.physics_validation_file,
        "physics_test": settings.physics_test_file,
    }
    result: dict[str, object] = {}
    for name, path in files.items():
        if not path.is_file():
            raise PhysicsTrainingError(f"输入文件不存在：{path}")
        with path.open("r", encoding="utf-8") as source:
            records = sum(1 for line in source if line.strip())
        result[name] = {
            "path": str(path),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "records": records,
        }
    return result


def _build_settings(
    raw: Mapping[str, object],
    *,
    variant: str,
    output_dir: Path,
    max_steps: int,
    validation_limit: int | None,
    lambda_physics_override: float | None = None,
    state_supervision_mode_override: str | None = None,
) -> PhysicsTrainingSettings:
    data = raw.get("training")
    if not isinstance(data, Mapping):
        raise PhysicsTrainingError("配置缺少 training")
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
        raise PhysicsTrainingError("缺少训练配置：" + ", ".join(missing))
    settings = PhysicsTrainingSettings(
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
        state_supervision_mode=str(
            state_supervision_mode_override
            if state_supervision_mode_override is not None
            else data.get("state_supervision_mode", "dense")
        ).lower(),
        lambda_state=float(data["lambda_state"]),
        lambda_physics=resolve_lambda_physics(
            float(data["lambda_physics"]), lambda_physics_override
        ),
        max_grad_norm=float(data["max_grad_norm"]),
        validation_limit=validation_limit,
    )
    positive = (
        settings.learning_rate,
        settings.generation_batch_size,
        settings.gradient_accumulation_steps,
        settings.physics_batch_size,
        settings.validation_batch_size,
        settings.max_steps,
        settings.max_grad_norm,
    )
    if any(value <= 0 for value in positive):
        raise PhysicsTrainingError("批量、步数、学习率和梯度上限必须大于零")
    if settings.effective_generation_batch_size != 16:
        raise PhysicsTrainingError("分类有效批量大小必须固定为 16")
    if settings.lambda_state != 1.0:
        raise PhysicsTrainingError("首轮状态损失权重必须固定为 lambda_state=1.0")
    if settings.state_supervision_mode not in STATE_SUPERVISION_MODES:
        raise PhysicsTrainingError(
            "state_supervision_mode 只允许 dense、anchor0_only、anchor0_plus_one"
        )
    if validation_limit is not None and validation_limit <= 0:
        raise PhysicsTrainingError("验证样本上限必须大于零")
    return settings


def _generation_batch(
    records: Sequence[Mapping[str, object]],
    tokenizer: object,
    max_length: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    sequences: list[list[int]] = []
    labels: list[list[int]] = []
    for record in records:
        prompt_text = tokenizer.apply_chat_template(
            [{"role": "user", "content": str(record["prompt"])}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        prompt_ids = tokenizer.encode(prompt_text, add_special_tokens=False)
        completion_ids = tokenizer.encode(
            str(record["completion"]) + tokenizer.eos_token,
            add_special_tokens=False,
        )
        completion_ids = completion_ids[:max_length]
        available_prompt = max(0, max_length - len(completion_ids))
        prompt_ids = prompt_ids[-available_prompt:] if available_prompt else []
        input_ids = prompt_ids + completion_ids
        if not completion_ids:
            raise PhysicsTrainingError("生成式样本缺少监督完成文本")
        sequences.append(input_ids)
        labels.append([-100] * len(prompt_ids) + completion_ids)
    width = max(len(value) for value in sequences)
    input_tensor = torch.full(
        (len(sequences), width), int(tokenizer.pad_token_id), dtype=torch.long
    )
    attention = torch.zeros((len(sequences), width), dtype=torch.long)
    label_tensor = torch.full((len(sequences), width), -100, dtype=torch.long)
    for row, (input_ids, target_ids) in enumerate(zip(sequences, labels, strict=True)):
        length = len(input_ids)
        input_tensor[row, :length] = torch.tensor(input_ids)
        attention[row, :length] = 1
        label_tensor[row, :length] = torch.tensor(target_ids)
    return {
        "input_ids": input_tensor.to(device),
        "attention_mask": attention.to(device),
        "labels": label_tensor.to(device),
    }


def _state_batch(
    records: Sequence[Mapping[str, object]],
    tokenizer: object,
    max_length: int,
    device: torch.device,
    *,
    include_fluxes: bool,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]] | None = None,
) -> dict[str, object]:
    prepared: list[StateRecord]
    if include_fluxes:
        prepared = [prepare_physics_record(record) for record in records]
    else:
        prepared = [prepare_state_record(record) for record in records]
    prompts = [item.prompt for item in prepared]
    chat_prompts = [
        tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        for prompt in prompts
    ]
    encoded = tokenizer(
        chat_prompts,
        padding=True,
        truncation=True,
        max_length=max_length,
        add_special_tokens=False,
        return_tensors="pt",
    )
    batch: dict[str, object] = {
        "input_ids": encoded["input_ids"].to(device),
        "attention_mask": encoded["attention_mask"].to(device),
        "state_targets": torch.tensor(
            [item.state_targets for item in prepared], dtype=torch.float32, device=device
        ),
    }
    if state_masks is not None:
        try:
            masks = [state_masks[str(record["sample_id"])] for record in records]
        except KeyError as error:
            raise PhysicsDataError(f"状态监督掩码缺少样本：{error.args[0]}") from error
        batch["state_mask"] = torch.tensor(masks, dtype=torch.bool, device=device)
    if include_fluxes:
        physics = [item for item in prepared if isinstance(item, PreparedPhysicsRecord)]
        for name in (
            "scale",
            "capacity",
            "received",
            "dequeued",
            "dropped_before",
            "dropped_after",
        ):
            batch[name] = torch.tensor(
                [getattr(item, name) for item in physics], dtype=torch.float32, device=device
            )
    return batch


def _gradient_norm(parameters: Sequence[torch.nn.Parameter]) -> float:
    total = 0.0
    for parameter in parameters:
        if parameter.grad is not None:
            total += float(parameter.grad.detach().float().square().sum().item())
    return math.sqrt(total)


def _load_model(probe: ProbeConfig) -> tuple[object, object]:
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝启动 Qwen 物理一致性训练")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("当前 GPU 不支持 BF16")
    tokenizer = AutoTokenizer.from_pretrained(probe.model_id, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        probe.model_id,
        quantization_config=quantization,
        dtype=torch.bfloat16,
        device_map="auto",
    )
    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )
    model = get_peft_model(
        model,
        LoraConfig(
            r=probe.lora_rank,
            lora_alpha=probe.lora_alpha,
            lora_dropout=probe.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules="all-linear",
        ),
    )
    model.config.use_cache = False
    model.train()
    return tokenizer, model


def _evaluate_generation(
    model: object,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
) -> float:
    losses = []
    model.eval()
    with torch.no_grad():
        for offset in range(0, len(records), batch_size):
            batch = _generation_batch(
                records[offset : offset + batch_size], tokenizer, max_length, device
            )
            losses.append(float(model(**batch, return_dict=True).loss.detach().float().item()))
    model.train()
    return sum(losses) / len(losses)


def _evaluate_state(
    model: object,
    state_head: ContinuousQueueStateHead,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> tuple[float, float, float, float | None]:
    state_values = []
    physics_values = []
    observed_error_sum = 0.0
    observed_count = 0
    unobserved_error_sum = 0.0
    unobserved_count = 0
    model.eval()
    state_head.eval()
    with torch.no_grad():
        for offset in range(0, len(records), batch_size):
            batch = _state_batch(
                records[offset : offset + batch_size],
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
            state_values.append(float(state_target_loss(predicted, batch["state_targets"]).item()))
            squared_error = (predicted.float() - batch["state_targets"].float()).square()
            observed = batch["state_mask"].bool()
            unobserved = ~observed
            observed_error_sum += float(squared_error.masked_select(observed).sum().item())
            observed_count += int(observed.sum().item())
            unobserved_error_sum += float(squared_error.masked_select(unobserved).sum().item())
            unobserved_count += int(unobserved.sum().item())
            residual = queue_balance_residual(
                predicted,
                batch["scale"],
                batch["capacity"],
                batch["received"],
                batch["dequeued"],
                batch["dropped_before"],
                batch["dropped_after"],
            )
            physics_values.append(float(residual.square().mean().item()))
    model.train()
    state_head.train()
    return (
        sum(state_values) / len(state_values),
        sum(physics_values) / len(physics_values),
        observed_error_sum / observed_count,
        unobserved_error_sum / unobserved_count if unobserved_count else None,
    )


def _tracking_settings(raw: Mapping[str, object], run_name: str) -> TrackingSettings:
    tracking = raw.get("tracking")
    if not isinstance(tracking, Mapping):
        raise PhysicsTrainingError("配置缺少 tracking")
    return TrackingSettings.from_mapping(
        {
            **tracking,
            "run_name": run_name,
        }
    )


def _training_snapshot(
    raw: Mapping[str, object],
    probe: ProbeConfig,
    settings: PhysicsTrainingSettings,
    run_name: str,
) -> dict[str, object]:
    return {
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
            "state_supervision_mode": settings.state_supervision_mode,
            "lambda_state": settings.lambda_state,
            "lambda_physics": settings.lambda_physics,
            "effective_generation_batch_size": settings.effective_generation_batch_size,
            "validation_limit": settings.validation_limit,
        },
        "tracking": {**dict(raw["tracking"]), "run_name": run_name},
    }


def train_physics_variant(
    probe: ProbeConfig,
    settings: PhysicsTrainingSettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
) -> dict[str, object]:
    """执行一个严格隔离的 M0、M1 或 M2 运行。"""
    contract = build_variant_contract(
        settings.variant,
        lambda_state=settings.lambda_state,
        lambda_physics=settings.lambda_physics,
    )
    layout = create_run_layout(settings.output_dir, settings.variant)
    snapshot = _training_snapshot(raw_config, probe, settings, tracking.run_name)
    layout.config_snapshot.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=True), encoding="utf-8"
    )
    _write_json(layout.environment, _environment_manifest())
    _write_json(layout.input_sha256, _input_manifest(settings))
    generation_train = _load_jsonl(settings.generation_train_file)
    generation_validation = _load_jsonl(settings.generation_validation_file)
    if settings.validation_limit is not None:
        generation_validation = generation_validation[: settings.validation_limit]
    physics_train: list[dict[str, object]] = []
    physics_validation: list[dict[str, object]] = []
    physics_schedule: tuple[tuple[int, ...], ...] = ()
    train_state_masks: dict[str, tuple[bool, bool, bool, bool, bool]] = {}
    validation_state_masks: dict[str, tuple[bool, bool, bool, bool, bool]] = {}
    observed_anchor_fraction: float | None = None
    state_mask_sha256: str | None = None
    if contract.uses_state:
        physics_train = _load_jsonl(settings.physics_train_file)
        physics_validation = _load_jsonl(settings.physics_validation_file)
        if settings.validation_limit is not None:
            physics_validation = physics_validation[: settings.validation_limit]
        train_state_masks = build_state_supervision_masks(
            physics_train, settings.state_supervision_mode, probe.seed
        )
        validation_state_masks = build_state_supervision_masks(
            physics_validation, settings.state_supervision_mode, probe.seed
        )
        observed_anchor_fraction = sum(sum(mask) for mask in train_state_masks.values()) / (
            5 * len(train_state_masks)
        )
        state_mask_sha256 = _state_mask_sha256(train_state_masks)
        physics_schedule = physics_sample_schedule(
            len(physics_train),
            batch_size=settings.physics_batch_size,
            steps=settings.max_steps,
            seed=probe.seed,
        )
        _write_json(
            layout.physics_sample_order,
            [
                {
                    "step": step,
                    "indices": list(indices),
                    "sample_ids": [physics_train[index]["sample_id"] for index in indices],
                }
                for step, indices in enumerate(physics_schedule, start=1)
            ],
        )
    generation_schedule = physics_sample_schedule(
        len(generation_train),
        batch_size=settings.generation_batch_size,
        steps=settings.max_steps * settings.gradient_accumulation_steps,
        seed=probe.seed,
    )
    data_files = {
        "config_snapshot": layout.config_snapshot,
        "environment": layout.environment,
        "input_sha256": layout.input_sha256,
        "step_metrics": layout.step_metrics,
        "training_summary": layout.training_summary,
        "final_adapter": layout.final_adapter,
    }
    if contract.uses_state:
        data_files.update(
            {
                "state_head": layout.state_head,
                "physics_sample_order": layout.physics_sample_order,
            }
        )
    started = time.perf_counter()
    with (
        capture_console_log(layout.console_log),
        swanlab_run(
            settings=tracking,
            phase="physics-train",
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
        state_head = None
        if contract.uses_state:
            state_head = ContinuousQueueStateHead(model.config.hidden_size).to(
                device=device, dtype=torch.bfloat16
            )
            state_head.train()
        lora_parameters = [
            parameter
            for name, parameter in model.named_parameters()
            if parameter.requires_grad and "lora_" in name
        ]
        if not lora_parameters:
            raise PhysicsTrainingError("未发现可训练 LoRA 参数")
        state_head_parameters = tuple(state_head.parameters()) if state_head is not None else ()
        trainable = list(lora_parameters)
        trainable.extend(state_head_parameters)
        optimizer = torch.optim.AdamW(trainable, lr=settings.learning_rate)
        projection_records: list[dict[str, float]] = []
        for step in range(1, settings.max_steps + 1):
            step_started = time.perf_counter()
            optimizer.zero_grad(set_to_none=True)
            generation_loss_value = 0.0
            micro_start = (step - 1) * settings.gradient_accumulation_steps
            for micro in range(settings.gradient_accumulation_steps):
                indices = generation_schedule[micro_start + micro]
                batch = _generation_batch(
                    [generation_train[index] for index in indices],
                    tokenizer,
                    probe.max_input_length,
                    device,
                )
                generation_loss = model(**batch, return_dict=True).loss.float()
                generation_loss_value += float(generation_loss.detach().item())
                (generation_loss / settings.gradient_accumulation_steps).backward()
            generation_loss_value /= settings.gradient_accumulation_steps
            generation_gradients = (
                tuple(
                    None if parameter.grad is None else parameter.grad.detach().float().clone()
                    for parameter in lora_parameters
                )
                if contract.uses_projection
                else ()
            )
            state_loss_value = 0.0
            physics_loss_value = 0.0
            projection_metrics: dict[str, float] = {}
            if state_head is not None:
                indices = physics_schedule[step - 1]
                state_batch = _state_batch(
                    [physics_train[index] for index in indices],
                    tokenizer,
                    probe.max_input_length,
                    device,
                    include_fluxes=contract.uses_physics,
                    state_masks=train_state_masks,
                )
                outputs = model(
                    input_ids=state_batch["input_ids"],
                    attention_mask=state_batch["attention_mask"],
                    output_hidden_states=True,
                    return_dict=True,
                )
                hidden = select_last_token_hidden(
                    outputs.hidden_states[-1], state_batch["attention_mask"]
                )
                predicted = state_head(hidden)
                state_loss = masked_state_target_loss(
                    predicted, state_batch["state_targets"], state_batch["state_mask"]
                )
                state_loss_value = float(state_loss.detach().item())
                auxiliary_loss = contract.lambda_state * state_loss
                physics_loss = None
                if contract.uses_physics:
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
                    physics_loss_value = float(physics_loss.detach().item())
                    auxiliary_loss = auxiliary_loss + contract.lambda_physics * physics_loss
                if contract.uses_projection:
                    if physics_loss is None:
                        raise PhysicsTrainingError("M2P 缺少物理损失")
                    auxiliary_parameters = tuple(lora_parameters) + state_head_parameters
                    state_gradients = torch.autograd.grad(
                        state_loss,
                        auxiliary_parameters,
                        retain_graph=True,
                        allow_unused=True,
                    )
                    physics_gradients = torch.autograd.grad(
                        physics_loss,
                        auxiliary_parameters,
                        allow_unused=True,
                    )
                    diagnostics = apply_m2p_gradients(
                        lora_parameters,
                        state_head_parameters,
                        generation_gradients=generation_gradients,
                        state_lora_gradients=state_gradients[: len(lora_parameters)],
                        physics_lora_gradients=physics_gradients[: len(lora_parameters)],
                        state_head_state_gradients=state_gradients[len(lora_parameters) :],
                        state_head_physics_gradients=physics_gradients[len(lora_parameters) :],
                        lambda_state=contract.lambda_state,
                        lambda_physics=contract.lambda_physics,
                    )
                    projection_metrics = {
                        "train/generation_gradient_norm": diagnostics.generation_norm,
                        "train/state_gradient_norm": diagnostics.state_norm,
                        "train/physics_gradient_norm": diagnostics.physics_norm,
                        "train/projection_cosine_before": diagnostics.projection.cosine_before,
                        "train/projection_cosine_after": diagnostics.projection.cosine_after,
                        "train/projection_triggered": float(diagnostics.projection.triggered),
                        "train/projection_removed_component_ratio": (
                            diagnostics.projection.removed_component_ratio
                        ),
                    }
                    projection_records.append(projection_metrics)
                else:
                    auxiliary_loss.backward()
            lora_gradient_norm = _gradient_norm(lora_parameters)
            state_head_gradient_norm = (
                _gradient_norm(list(state_head.parameters())) if state_head is not None else 0.0
            )
            torch.nn.utils.clip_grad_norm_(trainable, settings.max_grad_norm)
            optimizer.step()
            elapsed = time.perf_counter() - step_started
            metrics = {
                "train/total_loss": generation_loss_value
                + contract.lambda_state * state_loss_value
                + contract.lambda_physics * physics_loss_value,
                "train/generation_loss": generation_loss_value,
                "train/state_loss": state_loss_value,
                "train/physics_loss": physics_loss_value,
                "train/lora_gradient_norm": lora_gradient_norm,
                "train/state_head_gradient_norm": state_head_gradient_norm,
                "train/learning_rate": optimizer.param_groups[0]["lr"],
                "train/throughput_samples_per_second": (
                    settings.effective_generation_batch_size
                    + (settings.physics_batch_size if contract.uses_state else 0)
                )
                / elapsed,
                "train/peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            }
            metrics.update(projection_metrics)
            record_step_metrics(layout.step_metrics, swanlab, step=step, metrics=metrics)
            print(json.dumps({"step": step, **metrics}, ensure_ascii=False, sort_keys=True))
        model.save_pretrained(layout.final_adapter)
        tokenizer.save_pretrained(layout.final_adapter)
        if state_head is not None:
            torch.save(
                {name: value.detach().cpu() for name, value in state_head.state_dict().items()},
                layout.state_head,
            )
        generation_validation_loss = _evaluate_generation(
            model,
            tokenizer,
            generation_validation,
            batch_size=settings.validation_batch_size,
            max_length=probe.max_input_length,
            device=device,
        )
        validation_state_loss = None
        validation_physics_loss = None
        validation_state_observed_loss = None
        validation_state_unobserved_loss = None
        if state_head is not None:
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
        projection_summary: dict[str, object] = {"enabled": False}
        if contract.uses_projection:
            if len(projection_records) != settings.max_steps:
                raise PhysicsTrainingError("M2P 投影指标步数不完整")
            projection_summary = {
                "enabled": True,
                "triggered_steps": int(
                    sum(record["train/projection_triggered"] for record in projection_records)
                ),
                "mean_cosine_before": sum(
                    record["train/projection_cosine_before"] for record in projection_records
                )
                / len(projection_records),
                "mean_cosine_after": sum(
                    record["train/projection_cosine_after"] for record in projection_records
                )
                / len(projection_records),
                "mean_removed_component_ratio": sum(
                    record["train/projection_removed_component_ratio"]
                    for record in projection_records
                )
                / len(projection_records),
            }
        summary = {
            "schema_version": "flow_probe_physics_m012_v1",
            "status": "finished",
            "variant": settings.variant,
            "seed": probe.seed,
            "max_steps": settings.max_steps,
            "model_id": probe.model_id,
            "train_samples": len(generation_train),
            "physics_train_samples": len(physics_train),
            "generation_validation_samples": len(generation_validation),
            "physics_validation_samples": len(physics_validation),
            "effective_generation_batch_size": settings.effective_generation_batch_size,
            "state_supervision_mode": settings.state_supervision_mode,
            "observed_anchor_fraction": observed_anchor_fraction,
            "state_mask_sha256": state_mask_sha256,
            "lambda_state": settings.lambda_state,
            "lambda_physics": settings.lambda_physics,
            "residual_denominator": "strict_positive_configured_capacity_integral_link_bytes",
            "projection": projection_summary,
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
            "state_head_parameter_count": (
                sum(parameter.numel() for parameter in state_head.parameters())
                if state_head is not None
                else 0
            ),
        }
        _write_json(layout.training_summary, summary)
        validation_metrics = {
            "validation/generation_loss": generation_validation_loss,
        }
        if validation_state_loss is not None and validation_physics_loss is not None:
            validation_metrics.update(
                {
                    "validation/state_mse": validation_state_loss,
                    "validation/state_mse_observed": validation_state_observed_loss,
                    "validation/physics_residual_mse": validation_physics_loss,
                }
            )
            if validation_state_unobserved_loss is not None:
                validation_metrics["validation/state_mse_unobserved"] = (
                    validation_state_unobserved_loss
                )
        swanlab.log(validation_metrics, step=settings.max_steps + 1)
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    validate_completed_artifacts(layout)
    return json.loads(layout.artifact_manifest.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 Qwen3-1.7B M0/M1/M2 物理一致性训练")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--variant", choices=VARIANTS, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--max-steps", type=int, required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--validation-limit", type=int)
    parser.add_argument("--lambda-physics", type=float)
    parser.add_argument("--state-supervision-mode", choices=STATE_SUPERVISION_MODES)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise PhysicsTrainingError("配置根节点必须是映射")
    probe = ProbeConfig.from_mapping(raw["probe"])
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = _build_settings(
        raw,
        variant=args.variant,
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        validation_limit=args.validation_limit,
        lambda_physics_override=args.lambda_physics,
        state_supervision_mode_override=args.state_supervision_mode,
    )
    tracking = _tracking_settings(raw, args.run_name)
    manifest = train_physics_variant(probe, settings, tracking, raw)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
