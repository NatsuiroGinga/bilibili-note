"""冻结 S3 并训练有界物理条件交叉注意力的 E1/E2 入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import torch
import yaml

from flow_probe.bounded_physics_conditioning import (
    ConditioningDiagnostics,
    ConditioningSpec,
    PhysicsConditionedRuntime,
)
from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.physics_train import (
    ContinuousQueueStateHead,
    PhysicsTrainingError,
    PhysicsTrainingSettings,
    _build_settings,
    _environment_manifest,
    _generation_batch,
    _gradient_norm,
    _input_manifest,
    _load_jsonl,
    _sha256,
    _state_batch,
    _state_mask_sha256,
    _tracking_settings,
    _write_json,
    build_state_supervision_masks,
    masked_state_target_loss,
    physics_sample_schedule,
    queue_balance_residual,
    record_step_metrics,
)
from flow_probe.tracking import TrackingSettings, capture_console_log, swanlab_run

FIXED_BASE_MODEL_ID = "/root/autodl-tmp/thesis/models/Qwen3-1.7B"
FIXED_DETECTION_ADAPTER = Path(
    "runs/physics-sparse/" "qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/final_adapter"
)
DETECTION_ADAPTER_NAME = "detection"
FORMAL_TRAINING_STEPS = 202
WARMUP_STEPS = 20
PEAK_LEARNING_RATE = 2e-4
MIN_LEARNING_RATE = 2e-5
STATE_LOSS_WEIGHT = 1.0
PHYSICS_LOSS_WEIGHT = 0.01
MAX_GRAD_NORM = 1.0
STRUCTURE_SCHEMA_VERSION = "bounded_physics_conditioning_v1"
TRACKING_ARTIFACT_SCHEMA_VERSION = "flow_probe_run_artifacts_v1"
BOUNDED_TRAINING_PHASE = "bounded-physics-train"
REQUIRED_TRACKING_DATA_FILES = frozenset(
    {
        "artifact_manifest",
        "console_log",
        "swanlab_log_dir",
        "config_snapshot",
        "environment",
        "input_sha256",
        "step_metrics",
        "training_summary",
        "structure_config",
        "structure_state",
        "base_binding",
        "gradient_path",
        "runtime_path_audit",
        "bypass_equivalence",
        "generation_sample_order",
        "physics_sample_order",
    }
)


@dataclass(frozen=True)
class ConditioningVariantContract:
    """E1/E2 除损失开关和状态语义外完全相同的契约。"""

    name: str
    state_loss_enabled: bool | None = None
    physics_loss_enabled: bool | None = None
    state_semantics: str | None = None
    lambda_state: float = STATE_LOSS_WEIGHT
    lambda_physics: float = PHYSICS_LOSS_WEIGHT

    def __post_init__(self) -> None:
        expected = {
            "structure_only": (False, False, "condition_latent"),
            "combined": (True, True, "predicted_queue_state"),
        }
        if self.name not in expected:
            raise PhysicsTrainingError(
                f"未知条件训练变体：{self.name}；只允许 structure_only、combined"
            )
        expected_state, expected_physics, expected_semantics = expected[self.name]
        supplied = (
            self.state_loss_enabled,
            self.physics_loss_enabled,
            self.state_semantics,
        )
        if supplied == (None, None, None):
            object.__setattr__(self, "state_loss_enabled", expected_state)
            object.__setattr__(self, "physics_loss_enabled", expected_physics)
            object.__setattr__(self, "state_semantics", expected_semantics)
        elif supplied != (expected_state, expected_physics, expected_semantics):
            raise PhysicsTrainingError("条件训练变体的损失开关或状态语义不得改写")
        if not math.isclose(self.lambda_state, STATE_LOSS_WEIGHT, rel_tol=0.0, abs_tol=0.0):
            raise PhysicsTrainingError("状态损失权重必须固定为 1.0")
        if not math.isclose(
            self.lambda_physics,
            PHYSICS_LOSS_WEIGHT,
            rel_tol=0.0,
            abs_tol=0.0,
        ):
            raise PhysicsTrainingError("物理损失权重必须固定为 0.01")


@dataclass(frozen=True)
class ConditioningLossBreakdown:
    """一次训练步的生成、状态和物理损失。"""

    total: torch.Tensor
    generation: torch.Tensor
    state: torch.Tensor
    physics: torch.Tensor


def resolve_conditioning_variant(name: str) -> ConditioningVariantContract:
    """只解析两个预注册变体。"""

    return ConditioningVariantContract(str(name))


def compose_conditioning_loss(
    variant: str | ConditioningVariantContract,
    generation_loss: torch.Tensor,
    state_loss_factory: Callable[[], torch.Tensor],
    physics_loss_factory: Callable[[], torch.Tensor],
) -> ConditioningLossBreakdown:
    """按变体构造联合目标，并把关闭项显式写成数值零张量。"""

    contract = resolve_conditioning_variant(variant) if isinstance(variant, str) else variant
    if not isinstance(contract, ConditioningVariantContract):
        raise PhysicsTrainingError("variant 必须是条件训练变体名称或契约")
    if not isinstance(generation_loss, torch.Tensor) or generation_loss.ndim != 0:
        raise PhysicsTrainingError("generation_loss 必须是标量张量")
    zero = generation_loss.new_zeros(())
    state = state_loss_factory() if contract.state_loss_enabled else zero
    physics = physics_loss_factory() if contract.physics_loss_enabled else zero
    for name, value in (("state", state), ("physics", physics)):
        if not isinstance(value, torch.Tensor) or value.ndim != 0:
            raise PhysicsTrainingError(f"{name}_loss 必须是标量张量")
    total = generation_loss + contract.lambda_state * state + contract.lambda_physics * physics
    return ConditioningLossBreakdown(total, generation_loss, state, physics)


def bounded_physics_learning_rate(step: int) -> float:
    """返回固定 202 步线性预热加余弦衰减轨迹。"""

    if isinstance(step, bool) or not isinstance(step, int):
        raise PhysicsTrainingError("学习率轨迹步数必须是整数")
    if step < 1 or step > FORMAL_TRAINING_STEPS:
        raise PhysicsTrainingError(f"学习率轨迹只定义于第 1 至 {FORMAL_TRAINING_STEPS} 步")
    if step <= WARMUP_STEPS:
        progress = (step - 1) / (WARMUP_STEPS - 1)
        return MIN_LEARNING_RATE + progress * (PEAK_LEARNING_RATE - MIN_LEARNING_RATE)
    decay_progress = (step - WARMUP_STEPS) / (FORMAL_TRAINING_STEPS - WARMUP_STEPS)
    return MIN_LEARNING_RATE + 0.5 * (PEAK_LEARNING_RATE - MIN_LEARNING_RATE) * (
        1.0 + math.cos(math.pi * decay_progress)
    )


@dataclass(frozen=True)
class BoundedRunLayout:
    """E1/E2 单次运行的完整制品布局。"""

    output_dir: Path
    config_snapshot: Path
    environment: Path
    input_sha256: Path
    console_log: Path
    step_metrics: Path
    training_summary: Path
    structure_config: Path
    structure_state: Path
    base_binding: Path
    gradient_path: Path
    runtime_path_audit: Path
    bypass_equivalence: Path
    generation_sample_order: Path
    physics_sample_order: Path
    artifact_manifest: Path

    @classmethod
    def create(cls, output_dir: Path) -> BoundedRunLayout:
        output_dir = Path(output_dir)
        return cls(
            output_dir=output_dir,
            config_snapshot=output_dir / "config_snapshot.yaml",
            environment=output_dir / "environment.json",
            input_sha256=output_dir / "input_sha256.json",
            console_log=output_dir / "console.log",
            step_metrics=output_dir / "step_metrics.jsonl",
            training_summary=output_dir / "training_summary.json",
            structure_config=output_dir / "structure_config.json",
            structure_state=output_dir / "structure_state.pt",
            base_binding=output_dir / "base_binding.json",
            gradient_path=output_dir / "gradient_path.json",
            runtime_path_audit=output_dir / "runtime_path_audit.json",
            bypass_equivalence=output_dir / "bypass_equivalence.json",
            generation_sample_order=output_dir / "generation_sample_order.json",
            physics_sample_order=output_dir / "physics_sample_order.json",
            artifact_manifest=output_dir / "artifact_manifest.json",
        )

    @property
    def required_paths(self) -> tuple[Path, ...]:
        return (
            self.config_snapshot,
            self.environment,
            self.input_sha256,
            self.console_log,
            self.step_metrics,
            self.training_summary,
            self.structure_config,
            self.structure_state,
            self.base_binding,
            self.gradient_path,
            self.runtime_path_audit,
            self.bypass_equivalence,
            self.generation_sample_order,
            self.physics_sample_order,
            self.artifact_manifest,
        )


def create_bounded_run_layout(output_dir: Path) -> BoundedRunLayout:
    """拒绝复用输出目录并建立运行布局。"""

    layout = BoundedRunLayout.create(output_dir)
    if layout.output_dir.exists():
        raise PhysicsTrainingError(f"输出目录已存在，拒绝复用：{layout.output_dir}")
    layout.output_dir.mkdir(parents=True, exist_ok=False)
    return layout


def validate_bounded_artifacts(layout: BoundedRunLayout) -> None:
    """拒绝把缺少强制制品的运行标记为完成。"""

    missing = [str(path) for path in layout.required_paths if not path.is_file()]
    if missing:
        raise PhysicsTrainingError("有界条件训练制品不完整：" + ", ".join(missing))


@dataclass(frozen=True)
class StructureParameterGroups:
    """严格白名单内的四类新增结构参数。"""

    state_head: tuple[torch.nn.Parameter, ...]
    condition_encoder: tuple[torch.nn.Parameter, ...]
    cross_attention: tuple[torch.nn.Parameter, ...]
    gates: tuple[torch.nn.Parameter, ...]
    names: tuple[str, ...]

    @property
    def injectors(self) -> tuple[torch.nn.Parameter, ...]:
        return self.condition_encoder + self.cross_attention + self.gates

    @property
    def all(self) -> tuple[torch.nn.Parameter, ...]:
        return self.state_head + self.condition_encoder + self.cross_attention + self.gates


def configure_structure_trainability(
    model: torch.nn.Module,
    runtime: PhysicsConditionedRuntime,
) -> StructureParameterGroups:
    """冻结 Qwen/S3，并只打开状态头、编码器、交叉注意力和四个门。"""

    for parameter in model.parameters():
        parameter.requires_grad_(False)
        parameter.grad = None
    for parameter in runtime.parameters():
        parameter.requires_grad_(True)
        parameter.grad = None

    state_head: list[torch.nn.Parameter] = []
    condition_encoder: list[torch.nn.Parameter] = []
    cross_attention: list[torch.nn.Parameter] = []
    gates: list[torch.nn.Parameter] = []
    names: list[str] = []
    gate_names: list[str] = []
    for name, parameter in runtime.named_parameters():
        names.append(name)
        if name.startswith("state_head."):
            state_head.append(parameter)
        elif name.startswith("condition_encoder."):
            condition_encoder.append(parameter)
        elif name.startswith("injectors.") and name.endswith(".alpha"):
            gates.append(parameter)
            gate_names.append(name)
        elif name.startswith("injectors."):
            cross_attention.append(parameter)
        else:
            raise PhysicsTrainingError(f"结构参数不在白名单中：{name}")

    expected_gate_names = [f"injectors.{index}.alpha" for index in range(4)]
    if sorted(gate_names) != expected_gate_names:
        raise PhysicsTrainingError("结构必须且只能包含四个逐层门参数")
    if not state_head or not condition_encoder or not cross_attention:
        raise PhysicsTrainingError("结构参数白名单缺少状态头、条件编码器或交叉注意力")
    if runtime.unexpected_base_parameter_names():
        raise PhysicsTrainingError("运行时结构意外注册了底层模型参数")
    leaked_base = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    if leaked_base:
        raise PhysicsTrainingError("检测到冻结 Qwen/S3 中的可训练参数：" + ", ".join(leaked_base))
    disabled_structure = [
        name for name, parameter in runtime.named_parameters() if not parameter.requires_grad
    ]
    if disabled_structure:
        raise PhysicsTrainingError("白名单结构参数未启用：" + ", ".join(disabled_structure))
    groups = StructureParameterGroups(
        state_head=tuple(state_head),
        condition_encoder=tuple(condition_encoder),
        cross_attention=tuple(cross_attention),
        gates=tuple(gates),
        names=tuple(names),
    )
    if len({id(parameter) for parameter in groups.all}) != len(groups.all):
        raise PhysicsTrainingError("结构参数白名单包含重复参数")
    return groups


def gradient_checkpointing_audit(model: torch.nn.Module) -> dict[str, object]:
    """检查模型及全部子模块均未开启梯度检查点。"""

    enabled_modules = []
    for name, module in model.named_modules():
        if getattr(module, "gradient_checkpointing", False) is True:
            enabled_modules.append(name or "<root>")
    model_flag = bool(getattr(model, "is_gradient_checkpointing", False))
    audit = {
        "use_gradient_checkpointing": False,
        "model_is_gradient_checkpointing": model_flag,
        "enabled_module_names": enabled_modules,
        "verified_disabled": not model_flag and not enabled_modules,
    }
    if not audit["verified_disabled"]:
        raise PhysicsTrainingError("梯度检查点仍处于启用状态")
    return audit


def prepare_base_for_bounded_training(
    base_model: torch.nn.Module,
    prepare_model_for_kbit_training: Callable[..., torch.nn.Module],
) -> tuple[torch.nn.Module, dict[str, object]]:
    """以显式关闭梯度检查点的方式准备 4 位基座并立即断言。"""

    prepared = prepare_model_for_kbit_training(
        base_model,
        use_gradient_checkpointing=False,
    )
    disable = getattr(prepared, "gradient_checkpointing_disable", None)
    if callable(disable):
        disable()
    return prepared, gradient_checkpointing_audit(prepared)


def _directory_manifest(path: Path) -> dict[str, object]:
    path = Path(path)
    if not path.is_dir():
        raise PhysicsTrainingError(f"S3 检测适配器目录不存在：{path}")
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise PhysicsTrainingError(f"S3 检测适配器目录为空：{path}")
    entries = [
        {
            "path": str(item.relative_to(path)),
            "bytes": item.stat().st_size,
            "sha256": _sha256(item),
        }
        for item in files
    ]
    digest = hashlib.sha256(
        json.dumps(entries, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"path": str(path), "sha256": digest, "files": entries}


def _adapter_parameter_digest(model: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    marker = f".{DETECTION_ADAPTER_NAME}."
    matched = 0
    for name, parameter in sorted(model.named_parameters()):
        if marker not in name:
            continue
        matched += 1
        digest.update(name.encode("utf-8"))
        raw = parameter.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()
        digest.update(raw)
    if matched == 0:
        raise PhysicsTrainingError("未找到冻结的 S3 检测 LoRA 参数")
    return digest.hexdigest()


def _load_state_head(path: Path, hidden_size: int) -> ContinuousQueueStateHead:
    path = Path(path)
    if not path.is_file():
        raise PhysicsTrainingError(f"S3 状态头不存在：{path}")
    state = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(state, Mapping):
        raise PhysicsTrainingError("S3 state_head.pt 必须包含状态字典")
    state_head = ContinuousQueueStateHead(hidden_size)
    state_head.load_state_dict(state, strict=True)
    return state_head


def load_frozen_s3_model(
    probe: ProbeConfig,
    detection_adapter_path: Path,
) -> tuple[object, torch.nn.Module, ContinuousQueueStateHead, dict[str, object]]:
    """加载 4 位 Qwen、冻结 S3 LoRA 和 S3 状态头，不创建第二个 LoRA。"""

    from peft import PeftModel, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if probe.model_id != FIXED_BASE_MODEL_ID:
        raise PhysicsTrainingError(f"基座路径必须固定为 {FIXED_BASE_MODEL_ID}")
    if Path(detection_adapter_path) != FIXED_DETECTION_ADAPTER:
        raise PhysicsTrainingError(f"S3 路径必须固定为 {FIXED_DETECTION_ADAPTER}")
    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝启动有界物理条件训练")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("当前 GPU 不支持 BF16")

    tokenizer_source = (
        detection_adapter_path
        if (detection_adapter_path / "tokenizer_config.json").is_file()
        else probe.model_id
    )
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        probe.model_id,
        quantization_config=quantization,
        dtype=torch.bfloat16,
        device_map="auto",
    )
    base_model, checkpoint_audit = prepare_base_for_bounded_training(
        base_model,
        prepare_model_for_kbit_training,
    )
    model = PeftModel.from_pretrained(
        base_model,
        str(detection_adapter_path),
        adapter_name=DETECTION_ADAPTER_NAME,
        is_trainable=False,
    )
    for parameter in model.parameters():
        parameter.requires_grad_(False)
        parameter.grad = None
    model.config.use_cache = False
    model.eval()
    checkpoint_audit = gradient_checkpointing_audit(model)
    state_head = _load_state_head(
        detection_adapter_path.parent / "state_head.pt",
        int(model.config.hidden_size),
    )
    return tokenizer, model, state_head, checkpoint_audit


def _gradient_sequence_norm(gradients: Sequence[torch.Tensor | None]) -> float:
    square_sum = 0.0
    for gradient in gradients:
        if gradient is None:
            continue
        value = gradient.detach().float()
        if not bool(torch.isfinite(value).all().item()):
            raise PhysicsTrainingError("梯度诊断包含非有限值")
        square_sum += float(value.square().sum().item())
    return math.sqrt(square_sum)


def generation_gradient_snapshot(groups: StructureParameterGroups) -> dict[str, float]:
    """读取当前仅由生成损失产生的四类结构梯度范数。"""

    return {
        "generation_to_state_head_gradient_norm": _gradient_norm(list(groups.state_head)),
        "generation_to_condition_encoder_gradient_norm": _gradient_norm(
            list(groups.condition_encoder)
        ),
        "generation_to_cross_attention_gradient_norm": _gradient_norm(list(groups.cross_attention)),
        "generation_to_gate_gradient_norm": _gradient_norm(list(groups.gates)),
    }


def validate_generation_gradient_step(step: int, snapshot: Mapping[str, float]) -> None:
    """强制首步仅门有生成梯度，次步生成梯度贯通全部新增结构。"""

    state = float(snapshot["generation_to_state_head_gradient_norm"])
    encoder = float(snapshot["generation_to_condition_encoder_gradient_norm"])
    attention = float(snapshot["generation_to_cross_attention_gradient_norm"])
    gates = float(snapshot["generation_to_gate_gradient_norm"])
    if step == 1:
        if gates <= 0.0 or any(value != 0.0 for value in (state, encoder, attention)):
            raise PhysicsTrainingError("第一步生成梯度必须只到达四个门")
    elif step == 2 and any(value <= 0.0 for value in (state, encoder, attention, gates)):
        raise PhysicsTrainingError("第二步生成梯度未贯通状态头、编码器、交叉注意力和门")


def physics_gradient_isolation(
    physics_loss: torch.Tensor,
    groups: StructureParameterGroups,
    model: torch.nn.Module,
) -> dict[str, float]:
    """证明物理损失只对状态头有梯度，不直达注入器或冻结基座。"""

    if any(parameter.requires_grad for parameter in model.parameters()):
        raise PhysicsTrainingError("物理梯度隔离检查发现可训练基座或 S3 参数")
    parameters = groups.state_head + groups.injectors
    gradients = torch.autograd.grad(
        physics_loss,
        parameters,
        retain_graph=True,
        allow_unused=True,
    )
    split = len(groups.state_head)
    state_norm = _gradient_sequence_norm(gradients[:split])
    injector_norm = _gradient_sequence_norm(gradients[split:])
    result = {
        "physics_to_state_head_gradient_norm": state_norm,
        "physics_to_injector_gradient_norm": injector_norm,
        "physics_to_base_gradient_norm": 0.0,
    }
    if state_norm <= 0.0:
        raise PhysicsTrainingError("物理损失未到达状态头")
    if injector_norm != 0.0:
        raise PhysicsTrainingError("物理损失越界到达条件注入器")
    return result


def _state_conditioning_batch(
    records: Sequence[Mapping[str, object]],
    tokenizer: object,
    max_length: int,
    device: torch.device,
    *,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> dict[str, object]:
    """在每条物理提示末端追加一个仅用于定位锚点的监督令牌。"""

    raw = _state_batch(
        records,
        tokenizer,
        max_length - 1,
        device,
        include_fluxes=True,
        state_masks=state_masks,
    )
    raw_ids = raw["input_ids"]
    raw_attention = raw["attention_mask"]
    if not isinstance(raw_ids, torch.Tensor) or not isinstance(raw_attention, torch.Tensor):
        raise PhysicsTrainingError("物理批次缺少输入张量")
    sequences = [raw_ids[row][raw_attention[row].bool()] for row in range(raw_ids.shape[0])]
    width = max(sequence.shape[0] for sequence in sequences) + 1
    if width > max_length:
        raise PhysicsTrainingError("追加状态锚点令牌后超过最大输入长度")
    input_ids = torch.full(
        (len(sequences), width),
        int(tokenizer.pad_token_id),
        dtype=raw_ids.dtype,
        device=device,
    )
    attention_mask = torch.zeros_like(input_ids)
    labels = torch.full_like(input_ids, -100)
    sentinel = int(tokenizer.eos_token_id)
    for row, sequence in enumerate(sequences):
        length = sequence.shape[0]
        input_ids[row, :length] = sequence
        input_ids[row, length] = sentinel
        attention_mask[row, : length + 1] = 1
        labels[row, length] = sentinel
    return {
        **raw,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


def _prompt_only_batch(
    batch: Mapping[str, torch.Tensor],
    pad_token_id: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    labels = batch["labels"]
    input_ids = batch["input_ids"]
    if bool(((labels != -100).sum(dim=1) == 0).any().item()):
        raise PhysicsTrainingError("生成式审计批次缺少完成文本")
    starts = (labels != -100).to(dtype=torch.int64).argmax(dim=1)
    width = int(starts.max().item())
    prompt_ids = torch.full(
        (input_ids.shape[0], width),
        int(pad_token_id),
        dtype=input_ids.dtype,
        device=input_ids.device,
    )
    attention = torch.zeros_like(prompt_ids)
    for row, start in enumerate(starts.tolist()):
        if start < 1:
            raise PhysicsTrainingError("生成式审计样本缺少提示令牌")
        prompt_ids[row, :start] = input_ids[row, :start]
        attention[row, :start] = 1
    return prompt_ids, attention


def _diagnostics_dict(diagnostics: ConditioningDiagnostics) -> dict[str, object]:
    return {
        "gate_values": list(diagnostics.gate_values),
        "attention_entropies": list(diagnostics.attention_entropies),
        "max_residual_ratio": diagnostics.max_residual_ratio,
        "source_hook_count": diagnostics.source_hook_count,
        "target_hook_counts": list(diagnostics.target_hook_counts),
        "prefill_count": diagnostics.prefill_count,
        "cached_decode_count": diagnostics.cached_decode_count,
    }


@torch.no_grad()
def audit_runtime_paths(
    runtime: PhysicsConditionedRuntime,
    tokenizer: object,
    batch: Mapping[str, torch.Tensor],
) -> dict[str, object]:
    """执行训练、自由生成和候选评分三条真实结构路径。"""

    runtime.eval()
    training = runtime(**batch, return_dict=True)
    starts = (batch["labels"] != -100).to(dtype=torch.int64).argmax(dim=1)
    candidate = runtime(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        completion_start=starts,
        return_dict=True,
    )
    prompt_ids, prompt_attention = _prompt_only_batch(batch, int(tokenizer.pad_token_id))
    old_use_cache = bool(getattr(runtime.model.config, "use_cache", False))
    runtime.model.config.use_cache = True
    try:
        generated = runtime.generate(
            prompt_ids,
            prompt_attention,
            max_new_tokens=2,
            min_new_tokens=2,
            do_sample=False,
            num_beams=1,
            use_cache=True,
            pad_token_id=int(tokenizer.pad_token_id),
            eos_token_id=int(tokenizer.eos_token_id),
        )
    finally:
        runtime.model.config.use_cache = old_use_cache
    audit = {
        "schema_version": STRUCTURE_SCHEMA_VERSION,
        "training": _diagnostics_dict(training.diagnostics),
        "generation": _diagnostics_dict(generated.diagnostics),
        "candidate_scoring": _diagnostics_dict(candidate.diagnostics),
    }
    for name in ("training", "generation", "candidate_scoring"):
        if int(audit[name]["source_hook_count"]) < 1:
            raise PhysicsTrainingError(f"{name} 路径未经过条件源挂钩")
        if any(int(value) < 1 for value in audit[name]["target_hook_counts"]):
            raise PhysicsTrainingError(f"{name} 路径未经过全部四个注入挂钩")
    if int(audit["generation"]["prefill_count"]) != 1:
        raise PhysicsTrainingError("自由生成路径必须恰好执行一次完整提示预填充")
    runtime.train()
    return audit


@torch.no_grad()
def initial_bypass_equivalence(
    runtime: PhysicsConditionedRuntime,
    batch: Mapping[str, torch.Tensor],
) -> dict[str, object]:
    """验证零门结构启用、显式旁路和冻结 S3 逻辑值等价。"""

    runtime.eval()
    direct = runtime.model(**batch, return_dict=True).logits.detach().float()
    bypass = runtime(**batch, bypass=True, return_dict=True).logits.detach().float()
    enabled = runtime(**batch, return_dict=True).logits.detach().float()
    direct_difference = float((direct - bypass).abs().max().item())
    enabled_difference = float((enabled - bypass).abs().max().item())
    result = {
        "initial_direct_vs_bypass_max_abs_diff": direct_difference,
        "initial_enabled_vs_bypass_max_abs_diff": enabled_difference,
        "tolerance": 1e-6,
        "initial_equivalent": direct_difference <= 1e-6 and enabled_difference <= 1e-6,
    }
    if not result["initial_equivalent"]:
        raise PhysicsTrainingError("零门初始化未保持 S3 旁路等价")
    runtime.train()
    return result


@torch.no_grad()
def final_bypass_equivalence(
    runtime: PhysicsConditionedRuntime,
    batch: Mapping[str, torch.Tensor],
) -> dict[str, object]:
    """训练后再次证明旁路仍严格恢复冻结 S3。"""

    runtime.eval()
    direct = runtime.model(**batch, return_dict=True).logits.detach().float()
    bypass = runtime(**batch, bypass=True, return_dict=True).logits.detach().float()
    difference = float((direct - bypass).abs().max().item())
    if difference > 1e-6:
        raise PhysicsTrainingError("训练后显式旁路未恢复冻结 S3")
    runtime.train()
    return {
        "final_direct_vs_bypass_max_abs_diff": difference,
        "final_equivalent": True,
    }


def _mean_diagnostics(
    diagnostics: Sequence[ConditioningDiagnostics],
) -> dict[str, float]:
    if not diagnostics:
        raise PhysicsTrainingError("训练步缺少结构运行诊断")
    count = len(diagnostics)
    metrics: dict[str, float] = {}
    for index, layer in enumerate((24, 25, 26, 27)):
        metrics[f"structure/gate_layer_{layer}"] = diagnostics[-1].gate_values[index]
        metrics[f"structure/attention_entropy_layer_{layer}"] = (
            sum(item.attention_entropies[index] for item in diagnostics) / count
        )
        metrics[f"runtime/target_layer_{layer}_hook_count"] = float(
            sum(item.target_hook_counts[index] for item in diagnostics)
        )
    metrics["structure/max_residual_ratio"] = max(item.max_residual_ratio for item in diagnostics)
    metrics["runtime/source_hook_count"] = float(
        sum(item.source_hook_count for item in diagnostics)
    )
    return metrics


@torch.no_grad()
def _evaluate_generation(
    runtime: PhysicsConditionedRuntime,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
) -> float:
    values = []
    runtime.eval()
    for offset in range(0, len(records), batch_size):
        batch = _generation_batch(
            records[offset : offset + batch_size], tokenizer, max_length, device
        )
        output = runtime(**batch, return_dict=True)
        values.append(float(output.loss.detach().float().item()))
    runtime.train()
    if not values:
        raise PhysicsTrainingError("生成验证集为空")
    return sum(values) / len(values)


@torch.no_grad()
def _evaluate_conditions(
    runtime: PhysicsConditionedRuntime,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> dict[str, float | None]:
    total_error = 0.0
    total_count = 0
    observed_error = 0.0
    observed_count = 0
    unobserved_error = 0.0
    unobserved_count = 0
    residual_error = 0.0
    residual_count = 0
    runtime.eval()
    for offset in range(0, len(records), batch_size):
        selected = records[offset : offset + batch_size]
        batch = _state_conditioning_batch(
            selected,
            tokenizer,
            max_length,
            device,
            state_masks=state_masks,
        )
        output = runtime(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"],
            return_dict=True,
        )
        if output.predicted_state is None:
            raise PhysicsTrainingError("状态验证路径未返回五维条件")
        squared = (output.predicted_state.float() - batch["state_targets"].float()).square()
        mask = batch["state_mask"].bool()
        total_error += float(squared.sum().item())
        total_count += squared.numel()
        observed_error += float(squared.masked_select(mask).sum().item())
        observed_count += int(mask.sum().item())
        unobserved_error += float(squared.masked_select(~mask).sum().item())
        unobserved_count += int((~mask).sum().item())
        residual = queue_balance_residual(
            output.predicted_state,
            batch["scale"],
            batch["capacity"],
            batch["received"],
            batch["dequeued"],
            batch["dropped_before"],
            batch["dropped_after"],
        )
        residual_error += float(residual.square().sum().item())
        residual_count += residual.numel()
    runtime.train()
    if not total_count or not observed_count or not residual_count:
        raise PhysicsTrainingError("物理验证集或状态掩码为空")
    return {
        "five_dimensional_reference_mse": total_error / total_count,
        "observed_reference_mse": observed_error / observed_count,
        "unobserved_reference_mse": (
            unobserved_error / unobserved_count if unobserved_count else None
        ),
        "queue_residual_reference_mse": residual_error / residual_count,
    }


def _normalized_json(value: object) -> object:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _read_json_mapping(path: Path, artifact_name: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PhysicsTrainingError(f"无法读取 {artifact_name}：{error}") from error
    if not isinstance(value, Mapping):
        raise PhysicsTrainingError(f"{artifact_name} 必须是 JSON 映射")
    return dict(value)


def _validate_completed_bounded_run(
    layout: BoundedRunLayout,
) -> tuple[dict[str, object], dict[str, object]]:
    validate_bounded_artifacts(layout)
    summary = _read_json_mapping(layout.training_summary, "training_summary.json")
    manifest = _read_json_mapping(layout.artifact_manifest, "artifact_manifest.json")
    if (
        summary.get("schema_version") != STRUCTURE_SCHEMA_VERSION
        or summary.get("status") != "finished"
    ):
        raise PhysicsTrainingError("training_summary.json 未记录完成的有界条件训练")
    if (
        manifest.get("schema_version") != TRACKING_ARTIFACT_SCHEMA_VERSION
        or manifest.get("status") != "finished"
        or manifest.get("phase") != BOUNDED_TRAINING_PHASE
    ):
        raise PhysicsTrainingError("artifact_manifest.json 未记录完成的有界条件训练")
    if not isinstance(manifest.get("run_id"), str) or not str(manifest["run_id"]).strip():
        raise PhysicsTrainingError("artifact_manifest.json 缺少 SwanLab 运行编号")
    data_files = manifest.get("data_files")
    if not isinstance(data_files, Mapping):
        raise PhysicsTrainingError("artifact_manifest.json 缺少制品路径清单")
    missing_keys = sorted(REQUIRED_TRACKING_DATA_FILES.difference(data_files))
    if missing_keys:
        raise PhysicsTrainingError(
            "artifact_manifest.json 制品路径不完整：" + ", ".join(missing_keys)
        )
    if any(
        not isinstance(data_files[name], str) or not str(data_files[name]).strip()
        for name in REQUIRED_TRACKING_DATA_FILES
    ):
        raise PhysicsTrainingError("artifact_manifest.json 包含无效制品路径")
    swanlog_dir = layout.output_dir / "swanlog" / BOUNDED_TRAINING_PHASE
    if not swanlog_dir.is_dir() or not any(path.is_file() for path in swanlog_dir.rglob("*")):
        raise PhysicsTrainingError("完成运行缺少 SwanLab 原始日志")
    return summary, manifest


def _validate_saved_s3_binding(
    runtime: PhysicsConditionedRuntime,
    binding: Mapping[str, object],
    detection_adapter_path: Path,
) -> None:
    saved_manifest = binding.get("detection_adapter_manifest")
    if not isinstance(saved_manifest, Mapping):
        raise PhysicsTrainingError("base_binding.json 缺少 S3 目录清单")
    current_manifest = _directory_manifest(detection_adapter_path)
    if _normalized_json(saved_manifest) != _normalized_json(current_manifest):
        raise PhysicsTrainingError("当前 S3 适配器目录与训练时绑定不一致")

    digest_before = binding.get("detection_adapter_parameter_sha256_before")
    digest_after = binding.get("detection_adapter_parameter_sha256_after")
    if (
        not isinstance(digest_before, str)
        or not digest_before
        or not isinstance(digest_after, str)
        or not digest_after
        or digest_before != digest_after
    ):
        raise PhysicsTrainingError("base_binding.json 缺少一致的 S3 参数摘要")
    current_digest = _adapter_parameter_digest(runtime.model)
    if current_digest != digest_after:
        raise PhysicsTrainingError("当前内存 S3 参数与训练时绑定不一致")


def load_bounded_structure_artifacts(
    runtime: PhysicsConditionedRuntime,
    artifact_dir: Path,
    *,
    expected_model_id: str,
    expected_detection_adapter_path: Path,
) -> dict[str, object]:
    """校验完成状态、结构与冻结 S3 内容绑定后严格加载结构状态。"""

    artifact_dir = Path(artifact_dir)
    layout = BoundedRunLayout.create(artifact_dir)
    summary, _manifest = _validate_completed_bounded_run(layout)
    config = _read_json_mapping(layout.structure_config, "structure_config.json")
    binding = _read_json_mapping(layout.base_binding, "base_binding.json")
    if config.get("schema_version") != STRUCTURE_SCHEMA_VERSION:
        raise PhysicsTrainingError("structure_config.json 架构版本不匹配")
    variant = resolve_conditioning_variant(str(config.get("variant")))
    if config.get("spec") != _normalized_json(asdict(runtime.spec)):
        raise PhysicsTrainingError("结构配置与运行时固定架构不匹配")
    if binding.get("schema_version") != STRUCTURE_SCHEMA_VERSION:
        raise PhysicsTrainingError("base_binding.json 架构版本不匹配")
    if binding.get("model_id") != expected_model_id:
        raise PhysicsTrainingError("结构制品绑定的基座路径不匹配")
    if binding.get("detection_adapter_path") != str(expected_detection_adapter_path):
        raise PhysicsTrainingError("结构制品绑定的 S3 路径不匹配")
    if (
        summary.get("variant") != variant.name
        or summary.get("model_id") != expected_model_id
        or summary.get("detection_adapter_path") != str(expected_detection_adapter_path)
        or summary.get("base_and_s3_trainable_parameter_count") != 0
    ):
        raise PhysicsTrainingError("training_summary.json 与结构或冻结基座绑定不一致")
    checkpoint = binding.get("gradient_checkpointing")
    if not isinstance(checkpoint, Mapping) or not bool(checkpoint.get("verified_disabled")):
        raise PhysicsTrainingError("结构制品没有可核验的梯度检查点关闭记录")
    _validate_saved_s3_binding(runtime, binding, expected_detection_adapter_path)
    state = torch.load(layout.structure_state, map_location="cpu", weights_only=True)
    if not isinstance(state, Mapping):
        raise PhysicsTrainingError("structure_state.pt 必须包含状态字典")
    runtime.load_structure_state_dict(state, strict=True)
    return {"structure_config": config, "base_binding": binding}


def _validate_settings(
    probe: ProbeConfig,
    settings: PhysicsTrainingSettings,
    contract: ConditioningVariantContract,
) -> None:
    if probe.model_id != FIXED_BASE_MODEL_ID:
        raise PhysicsTrainingError(f"基座路径必须固定为 {FIXED_BASE_MODEL_ID}")
    if probe.seed != 42:
        raise PhysicsTrainingError("E1/E2 当前只允许固定种子 42")
    if settings.variant != contract.name:
        raise PhysicsTrainingError("训练设置与条件变体不一致")
    if settings.max_steps < 2 or settings.max_steps > FORMAL_TRAINING_STEPS:
        raise PhysicsTrainingError("E1/E2 必须至少运行两步且不得超过 202 步")
    if settings.state_supervision_mode != "anchor0_plus_one":
        raise PhysicsTrainingError("E1/E2 状态监督必须固定为 anchor0_plus_one")
    if not math.isclose(settings.learning_rate, PEAK_LEARNING_RATE, rel_tol=0.0, abs_tol=0.0):
        raise PhysicsTrainingError("配置峰值学习率必须固定为 2e-4")
    if not math.isclose(settings.lambda_state, STATE_LOSS_WEIGHT, rel_tol=0.0, abs_tol=0.0):
        raise PhysicsTrainingError("状态损失权重必须固定为 1.0")
    if not math.isclose(settings.lambda_physics, PHYSICS_LOSS_WEIGHT, rel_tol=0.0, abs_tol=0.0):
        raise PhysicsTrainingError("物理损失权重必须固定为 0.01")
    if not math.isclose(settings.max_grad_norm, MAX_GRAD_NORM, rel_tol=0.0, abs_tol=0.0):
        raise PhysicsTrainingError("梯度裁剪必须固定为 1.0")


def _training_snapshot(
    raw: Mapping[str, object],
    probe: ProbeConfig,
    settings: PhysicsTrainingSettings,
    tracking: TrackingSettings,
    contract: ConditioningVariantContract,
    detection_adapter_path: Path,
) -> dict[str, object]:
    return {
        "probe": asdict(probe),
        "training": {
            **dict(raw["training"]),
            "variant": contract.name,
            "output_dir": str(settings.output_dir),
            "max_steps": settings.max_steps,
            "effective_generation_batch_size": settings.effective_generation_batch_size,
            "validation_limit": settings.validation_limit,
        },
        "conditioning": {
            "schema_version": STRUCTURE_SCHEMA_VERSION,
            "detection_adapter_path": str(detection_adapter_path),
            "spec": _normalized_json(asdict(ConditioningSpec())),
            "state_semantics": contract.state_semantics,
            "state_loss_enabled": contract.state_loss_enabled,
            "physics_loss_enabled": contract.physics_loss_enabled,
            "gradient_checkpointing": False,
            "learning_rate_schedule": "linear_warmup_cosine_decay",
            "warmup_steps": WARMUP_STEPS,
            "formal_steps": FORMAL_TRAINING_STEPS,
            "peak_learning_rate": PEAK_LEARNING_RATE,
            "minimum_learning_rate": MIN_LEARNING_RATE,
        },
        "tracking": {**dict(raw["tracking"]), "run_name": tracking.run_name},
    }


def _write_sample_orders(
    layout: BoundedRunLayout,
    generation_train: Sequence[Mapping[str, object]],
    physics_train: Sequence[Mapping[str, object]],
    generation_schedule: Sequence[Sequence[int]],
    physics_schedule: Sequence[Sequence[int]],
) -> None:
    _write_json(
        layout.generation_sample_order,
        [
            {
                "micro_step": index + 1,
                "indices": list(indices),
                "sample_ids": [generation_train[item]["sample_id"] for item in indices],
                "tasks": [generation_train[item].get("task") for item in indices],
            }
            for index, indices in enumerate(generation_schedule)
        ],
    )
    _write_json(
        layout.physics_sample_order,
        [
            {
                "step": index + 1,
                "indices": list(indices),
                "sample_ids": [physics_train[item]["sample_id"] for item in indices],
            }
            for index, indices in enumerate(physics_schedule)
        ],
    )


def train_bounded_physics_variant(
    probe: ProbeConfig,
    settings: PhysicsTrainingSettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
    detection_adapter_path: Path,
) -> dict[str, object]:
    """执行冻结 S3 的 E1 结构单支柱或 E2 PINN 组合训练。"""

    contract = resolve_conditioning_variant(settings.variant)
    _validate_settings(probe, settings, contract)
    if Path(detection_adapter_path) != FIXED_DETECTION_ADAPTER:
        raise PhysicsTrainingError(f"S3 路径必须固定为 {FIXED_DETECTION_ADAPTER}")
    layout = create_bounded_run_layout(settings.output_dir)
    snapshot = _training_snapshot(
        raw_config,
        probe,
        settings,
        tracking,
        contract,
        detection_adapter_path,
    )
    layout.config_snapshot.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=True), encoding="utf-8"
    )
    _write_json(layout.environment, _environment_manifest())
    input_manifest = _input_manifest(settings)
    input_manifest["detection_adapter"] = _directory_manifest(detection_adapter_path)
    state_head_path = detection_adapter_path.parent / "state_head.pt"
    if not state_head_path.is_file():
        raise PhysicsTrainingError(f"S3 状态头不存在：{state_head_path}")
    input_manifest["state_head"] = {
        "path": str(state_head_path),
        "bytes": state_head_path.stat().st_size,
        "sha256": _sha256(state_head_path),
    }
    _write_json(layout.input_sha256, input_manifest)

    generation_train = _load_jsonl(settings.generation_train_file)
    generation_validation = _load_jsonl(settings.generation_validation_file)
    physics_train = _load_jsonl(settings.physics_train_file)
    physics_validation = _load_jsonl(settings.physics_validation_file)
    if settings.validation_limit is not None:
        generation_validation = generation_validation[: settings.validation_limit]
        physics_validation = physics_validation[: settings.validation_limit]
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
    train_state_masks = build_state_supervision_masks(
        physics_train,
        settings.state_supervision_mode,
        probe.seed,
    )
    validation_state_masks = build_state_supervision_masks(
        physics_validation,
        settings.state_supervision_mode,
        probe.seed,
    )
    _write_sample_orders(
        layout,
        generation_train,
        physics_train,
        generation_schedule,
        physics_schedule,
    )

    data_files = {
        "config_snapshot": layout.config_snapshot,
        "environment": layout.environment,
        "input_sha256": layout.input_sha256,
        "step_metrics": layout.step_metrics,
        "training_summary": layout.training_summary,
        "structure_config": layout.structure_config,
        "structure_state": layout.structure_state,
        "base_binding": layout.base_binding,
        "gradient_path": layout.gradient_path,
        "runtime_path_audit": layout.runtime_path_audit,
        "bypass_equivalence": layout.bypass_equivalence,
        "generation_sample_order": layout.generation_sample_order,
        "physics_sample_order": layout.physics_sample_order,
    }
    started = time.perf_counter()
    with (
        capture_console_log(layout.console_log),
        swanlab_run(
            settings=tracking,
            phase="bounded-physics-train",
            config=snapshot,
            artifact_dir=layout.output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        torch.manual_seed(probe.seed)
        torch.cuda.manual_seed_all(probe.seed)
        torch.cuda.reset_peak_memory_stats()
        tokenizer, model, state_head, checkpoint_audit = load_frozen_s3_model(
            probe,
            detection_adapter_path,
        )
        device = next(model.parameters()).device
        torch.manual_seed(probe.seed)
        runtime = PhysicsConditionedRuntime(model, state_head).to(
            device=device,
            dtype=torch.bfloat16,
        )
        try:
            runtime.train()
            model.eval()
            groups = configure_structure_trainability(model, runtime)
            initial_adapter_digest = _adapter_parameter_digest(model)
            audit_batch = _generation_batch(
                generation_train[:1],
                tokenizer,
                probe.max_input_length,
                device,
            )
            bypass_record = initial_bypass_equivalence(runtime, audit_batch)
            runtime_path_audit = audit_runtime_paths(runtime, tokenizer, audit_batch)
            _write_json(layout.runtime_path_audit, runtime_path_audit)
            runtime.zero_grad(set_to_none=True)

            optimizer = torch.optim.AdamW(
                groups.all,
                lr=bounded_physics_learning_rate(1),
                weight_decay=0.0,
            )
            gradient_path: dict[str, object] = {
                "schema_version": STRUCTURE_SCHEMA_VERSION,
                "first_step": None,
                "second_step": None,
                "physics": {
                    "enabled": bool(contract.physics_loss_enabled),
                    "physics_to_state_head_gradient_norm": 0.0,
                    "physics_to_injector_gradient_norm": 0.0,
                    "physics_to_base_gradient_norm": 0.0,
                },
            }
            for step in range(1, settings.max_steps + 1):
                step_started = time.perf_counter()
                learning_rate = bounded_physics_learning_rate(step)
                for parameter_group in optimizer.param_groups:
                    parameter_group["lr"] = learning_rate
                optimizer.zero_grad(set_to_none=True)
                generation_loss_value = 0.0
                step_diagnostics: list[ConditioningDiagnostics] = []
                micro_start = (step - 1) * settings.gradient_accumulation_steps
                for micro in range(settings.gradient_accumulation_steps):
                    indices = generation_schedule[micro_start + micro]
                    batch = _generation_batch(
                        [generation_train[index] for index in indices],
                        tokenizer,
                        probe.max_input_length,
                        device,
                    )
                    output = runtime(**batch, return_dict=True)
                    generation_loss = output.loss.float()
                    generation_loss_value += float(generation_loss.detach().item())
                    (generation_loss / settings.gradient_accumulation_steps).backward()
                    step_diagnostics.append(output.diagnostics)
                generation_loss_value /= settings.gradient_accumulation_steps
                generation_gradients = generation_gradient_snapshot(groups)
                if step <= 2:
                    validate_generation_gradient_step(step, generation_gradients)
                    gradient_path["first_step" if step == 1 else "second_step"] = {
                        "step": step,
                        **generation_gradients,
                    }

                state_loss_value = 0.0
                physics_loss_value = 0.0
                physics_gradients = {
                    "physics_to_state_head_gradient_norm": 0.0,
                    "physics_to_injector_gradient_norm": 0.0,
                    "physics_to_base_gradient_norm": 0.0,
                }
                if contract.state_loss_enabled:
                    indices = physics_schedule[step - 1]
                    state_batch = _state_conditioning_batch(
                        [physics_train[index] for index in indices],
                        tokenizer,
                        probe.max_input_length,
                        device,
                        state_masks=train_state_masks,
                    )
                    state_output = runtime(
                        input_ids=state_batch["input_ids"],
                        attention_mask=state_batch["attention_mask"],
                        labels=state_batch["labels"],
                        return_dict=True,
                    )
                    step_diagnostics.append(state_output.diagnostics)
                    if state_output.predicted_state is None:
                        raise PhysicsTrainingError("E2 状态路径未返回预测队列状态")
                    state_loss = masked_state_target_loss(
                        state_output.predicted_state,
                        state_batch["state_targets"],
                        state_batch["state_mask"],
                    )
                    residual = queue_balance_residual(
                        state_output.predicted_state,
                        state_batch["scale"],
                        state_batch["capacity"],
                        state_batch["received"],
                        state_batch["dequeued"],
                        state_batch["dropped_before"],
                        state_batch["dropped_after"],
                    )
                    physics_loss = residual.square().mean()
                    state_loss_value = float(state_loss.detach().item())
                    physics_loss_value = float(physics_loss.detach().item())
                    physics_gradients = physics_gradient_isolation(
                        physics_loss,
                        groups,
                        model,
                    )
                    auxiliary = (
                        contract.lambda_state * state_loss + contract.lambda_physics * physics_loss
                    )
                    auxiliary.backward()
                    gradient_path["physics"] = {
                        "enabled": True,
                        "measured_step": step,
                        **physics_gradients,
                    }

                total_loss_value = (
                    generation_loss_value
                    + contract.lambda_state * state_loss_value
                    + contract.lambda_physics * physics_loss_value
                )
                state_head_gradient_norm = _gradient_norm(list(groups.state_head))
                condition_encoder_gradient_norm = _gradient_norm(list(groups.condition_encoder))
                cross_attention_gradient_norm = _gradient_norm(list(groups.cross_attention))
                gate_gradient_norm = _gradient_norm(list(groups.gates))
                torch.nn.utils.clip_grad_norm_(groups.all, settings.max_grad_norm)
                optimizer.step()
                elapsed = time.perf_counter() - step_started
                metrics = {
                    "train/total_loss": total_loss_value,
                    "train/generation_loss": generation_loss_value,
                    "train/state_loss": state_loss_value,
                    "train/physics_loss": physics_loss_value,
                    "train/lora_gradient_norm": 0.0,
                    "train/state_head_gradient_norm": state_head_gradient_norm,
                    "train/condition_encoder_gradient_norm": (condition_encoder_gradient_norm),
                    "train/cross_attention_gradient_norm": (cross_attention_gradient_norm),
                    "train/gate_gradient_norm": gate_gradient_norm,
                    "train/learning_rate": learning_rate,
                    "train/throughput_samples_per_second": (
                        settings.effective_generation_batch_size
                        + (settings.physics_batch_size if contract.state_loss_enabled else 0)
                    )
                    / elapsed,
                    "train/peak_gpu_memory_mib": (torch.cuda.max_memory_allocated() / (1024**2)),
                    **generation_gradients,
                    **physics_gradients,
                    **_mean_diagnostics(step_diagnostics),
                    "runtime/training_path_calls": float(len(step_diagnostics)),
                    "runtime/generation_path_calls": 1.0,
                    "runtime/candidate_scoring_path_calls": 1.0,
                }
                record_step_metrics(
                    layout.step_metrics,
                    swanlab,
                    step=step,
                    metrics=metrics,
                )
                print(json.dumps({"step": step, **metrics}, ensure_ascii=False, sort_keys=True))

            if gradient_path["first_step"] is None or gradient_path["second_step"] is None:
                raise PhysicsTrainingError("两步生成梯度路径证据不完整")
            final_adapter_digest = _adapter_parameter_digest(model)
            if final_adapter_digest != initial_adapter_digest:
                raise PhysicsTrainingError("冻结的 S3 检测 LoRA 在训练后发生变化")
            bypass_record.update(final_bypass_equivalence(runtime, audit_batch))
            _write_json(layout.bypass_equivalence, bypass_record)
            _write_json(layout.gradient_path, gradient_path)

            structure_config = {
                "schema_version": STRUCTURE_SCHEMA_VERSION,
                "variant": contract.name,
                "state_semantics": contract.state_semantics,
                "spec": _normalized_json(asdict(runtime.spec)),
                "trainable_parameter_names": list(groups.names),
                "trainable_parameter_count": sum(parameter.numel() for parameter in groups.all),
                "lambda_state": contract.lambda_state,
                "lambda_physics": contract.lambda_physics,
                "max_grad_norm": settings.max_grad_norm,
                "learning_rate_key_points": {
                    "1": bounded_physics_learning_rate(1),
                    "20": bounded_physics_learning_rate(20),
                    "21": bounded_physics_learning_rate(21),
                    "202": bounded_physics_learning_rate(202),
                },
                "gradient_checkpointing": False,
            }
            _write_json(layout.structure_config, structure_config)
            torch.save(
                {
                    name: value.detach().cpu()
                    for name, value in runtime.structure_state_dict().items()
                },
                layout.structure_state,
            )
            saved_state = torch.load(
                layout.structure_state,
                map_location="cpu",
                weights_only=True,
            )
            runtime.load_structure_state_dict(saved_state, strict=True)
            base_binding = {
                "schema_version": STRUCTURE_SCHEMA_VERSION,
                "model_id": probe.model_id,
                "detection_adapter_path": str(detection_adapter_path),
                "detection_adapter_name": DETECTION_ADAPTER_NAME,
                "detection_adapter_manifest": input_manifest["detection_adapter"],
                "detection_adapter_parameter_sha256_before": initial_adapter_digest,
                "detection_adapter_parameter_sha256_after": final_adapter_digest,
                "state_head_source": input_manifest["state_head"],
                "base_and_s3_trainable_parameter_count": sum(
                    parameter.numel() for parameter in model.parameters() if parameter.requires_grad
                ),
                "gradient_checkpointing": checkpoint_audit,
                "strict_structure_load_verified": True,
            }
            _write_json(layout.base_binding, base_binding)

            generation_validation_loss = _evaluate_generation(
                runtime,
                tokenizer,
                generation_validation,
                batch_size=settings.validation_batch_size,
                max_length=probe.max_input_length,
                device=device,
            )
            condition_validation = _evaluate_conditions(
                runtime,
                tokenizer,
                physics_validation,
                batch_size=settings.validation_batch_size,
                max_length=probe.max_input_length,
                device=device,
                state_masks=validation_state_masks,
            )
            torch.cuda.synchronize()
            summary = {
                "schema_version": STRUCTURE_SCHEMA_VERSION,
                "status": "finished",
                "variant": contract.name,
                "state_semantics": contract.state_semantics,
                "seed": probe.seed,
                "max_steps": settings.max_steps,
                "model_id": probe.model_id,
                "detection_adapter_path": str(detection_adapter_path),
                "generation_train_samples": len(generation_train),
                "physics_train_samples": len(physics_train),
                "generation_validation_samples": len(generation_validation),
                "physics_validation_samples": len(physics_validation),
                "effective_generation_batch_size": (settings.effective_generation_batch_size),
                "state_supervision_mode": settings.state_supervision_mode,
                "state_mask_sha256": _state_mask_sha256(train_state_masks),
                "lambda_state": contract.lambda_state,
                "lambda_physics": contract.lambda_physics,
                "gradient_checkpointing": checkpoint_audit,
                "gradient_path": gradient_path,
                "validation": {
                    "generation_loss": generation_validation_loss,
                    **condition_validation,
                },
                "runtime_seconds": time.perf_counter() - started,
                "peak_gpu_memory_mib": (torch.cuda.max_memory_allocated() / (1024**2)),
                "trainable_structure_parameter_count": sum(
                    parameter.numel() for parameter in groups.all
                ),
                "base_and_s3_trainable_parameter_count": 0,
            }
            _write_json(layout.training_summary, summary)
            swanlab.log(
                {
                    "validation/generation_loss": generation_validation_loss,
                    "validation/five_dimensional_reference_mse": float(
                        condition_validation["five_dimensional_reference_mse"]
                    ),
                    "validation/observed_reference_mse": float(
                        condition_validation["observed_reference_mse"]
                    ),
                    "validation/queue_residual_reference_mse": float(
                        condition_validation["queue_residual_reference_mse"]
                    ),
                },
                step=settings.max_steps + 1,
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        finally:
            runtime.close()
    validate_bounded_artifacts(layout)
    return json.loads(layout.artifact_manifest.read_text(encoding="utf-8"))


def _build_bounded_settings(
    raw: Mapping[str, object],
    *,
    variant: str,
    output_dir: Path,
    max_steps: int,
    validation_limit: int | None,
) -> PhysicsTrainingSettings:
    contract = resolve_conditioning_variant(variant)
    reused = _build_settings(
        raw,
        variant="M2",
        output_dir=output_dir,
        max_steps=max_steps,
        validation_limit=validation_limit,
        lambda_physics_override=None,
        state_supervision_mode_override="anchor0_plus_one",
    )
    return replace(reused, variant=contract.name)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行冻结 S3 的 E1/E2 有界物理条件训练")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--variant",
        choices=("structure_only", "combined"),
        required=True,
    )
    parser.add_argument("--detection-adapter-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--max-steps", type=int, required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--validation-limit", type=int)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise PhysicsTrainingError("配置根节点必须是映射")
    probe_data = raw.get("probe")
    if not isinstance(probe_data, Mapping):
        raise PhysicsTrainingError("配置缺少 probe")
    probe = ProbeConfig.from_mapping(probe_data)
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = _build_bounded_settings(
        raw,
        variant=args.variant,
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        validation_limit=args.validation_limit,
    )
    tracking = _tracking_settings(raw, args.run_name)
    manifest = train_bounded_physics_variant(
        probe,
        settings,
        tracking,
        raw,
        args.detection_adapter_path,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
