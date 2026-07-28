"""有界物理条件结构的固定六分区评估入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import torch
import yaml

from flow_probe.bounded_physics_conditioning import (
    ConditioningDiagnostics,
    PhysicsConditionedRuntime,
)
from flow_probe.bounded_physics_train import (
    DETECTION_ADAPTER_NAME,
    FIXED_BASE_MODEL_ID,
    FIXED_DETECTION_ADAPTER,
    _evaluate_conditions,
    _load_state_head,
    load_bounded_structure_artifacts,
)
from flow_probe.config import ProbeConfig
from flow_probe.generative_multiclass import (
    apply_unknown_rejection,
    calibrate_unknown_threshold,
    compute_open_set_metrics,
    parse_label_prediction,
)
from flow_probe.hierarchical_evaluation import (
    UNKNOWN_LABEL,
    CandidateDecision,
    EvaluationSettings,
    EvaluationSplit,
    _ProgressLogger,
    _derived_seed,
    _file_sha256,
    _format_generation_prompt,
    _load_records,
    _percentile,
    _write_jsonl,
    build_evaluation_plan,
    completion_mean_log_probability,
    decode_candidate_scores,
    encode_candidate_sequence,
    select_stratified_records,
)
from flow_probe.physics_train import _load_jsonl, build_state_supervision_masks
from flow_probe.tracking import (
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)

EVALUATION_SCHEMA_VERSION = "flow_probe_bounded_physics_evaluation_v1"
EVALUATION_PHASE = "bounded-physics-evaluation"
FIXED_SAMPLE_DIR = Path("runs/data-sampled/genis-hierarchical-v2-seed42")
FIXED_S3_EVALUATION_DIR = Path(
    "runs/physics-detection-evaluation/" "qwen3-1.7b-seed42-s3-anchor0-plus-one-eval300-v1"
)
FIXED_PHYSICS_TEST_FILE = Path(
    "runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/test.jsonl"
)
FIXED_SPLITS = (
    "family_test",
    "subtype_validation",
    "subtype_test",
    "ood_dos_icmp",
    "ood_dos_pushack",
    "ood_dos_udp",
)
CANDIDATE_CONDITION_TOLERANCE = 1e-6
SAMPLES_PER_LABEL = 300
GENERATION_BATCH_SIZE = 16
SCORING_BATCH_SIZE = 24
PROGRESS_EVERY_BATCHES = 25
MAX_KNOWN_REJECTION_RATE = 0.05
PHYSICS_TEST_SAMPLES = 807
PHYSICS_TEST_BATCH_SIZE = 8
STATE_SUPERVISION_MODE = "anchor0_plus_one"


class BoundedPhysicsEvaluationError(ValueError):
    """固定评估协议、推理边界或制品不满足要求。"""


@dataclass(frozen=True)
class BoundedEvaluationVariant:
    """一个固定 E1/E2 正式评估绑定。"""

    short_name: str
    training_variant: str
    training_dir: Path
    output_dir: Path
    run_name: str


_VARIANTS = {
    "e1": BoundedEvaluationVariant(
        short_name="e1",
        training_variant="structure_only",
        training_dir=Path(
            "runs/bounded-physics-conditioning/" "qwen3-1.7b-seed42-e1-structure-only-full202-v1"
        ),
        output_dir=Path(
            "runs/bounded-physics-conditioning-evaluation/"
            "qwen3-1.7b-seed42-e1-structure-only-eval300-v1"
        ),
        run_name="qwen3-1.7b-seed42-e1-structure-only-eval300-v1",
    ),
    "e2": BoundedEvaluationVariant(
        short_name="e2",
        training_variant="combined",
        training_dir=Path(
            "runs/bounded-physics-conditioning/" "qwen3-1.7b-seed42-e2-pinn-combined-full202-v1"
        ),
        output_dir=Path(
            "runs/bounded-physics-conditioning-evaluation/"
            "qwen3-1.7b-seed42-e2-pinn-combined-eval300-v1"
        ),
        run_name="qwen3-1.7b-seed42-e2-pinn-combined-eval300-v1",
    ),
}

_FORBIDDEN_PUBLIC_INFERENCE_FIELDS = frozenset(
    {
        "task_label",
        "true_label",
        "label",
        "attack_label",
        "attack_truth",
        "is_unknown",
        "unknown_attack",
        "unknown_attack_marker",
        "state_target",
        "state_targets",
        "queue_state",
        "queue_truth",
        "scenario",
        "scenario_id",
        "ns3_scenario",
        "ns3_scenario_id",
    }
)


@dataclass(frozen=True)
class PublicInferenceRequest:
    """公开推理只携带样本标识与提示词，不接收任何真值。"""

    sample_id: str
    prompt: str

    def __post_init__(self) -> None:
        if not isinstance(self.sample_id, str) or not self.sample_id.strip():
            raise BoundedPhysicsEvaluationError("公开推理的 sample_id 不能为空")
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise BoundedPhysicsEvaluationError("公开推理的 prompt 不能为空")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> PublicInferenceRequest:
        """严格拒绝队列、场景、攻击标签或未知攻击真值。"""

        if not isinstance(payload, Mapping):
            raise BoundedPhysicsEvaluationError("公开推理请求必须是映射")
        supplied = set(payload)
        forbidden = sorted(supplied.intersection(_FORBIDDEN_PUBLIC_INFERENCE_FIELDS))
        if forbidden:
            raise BoundedPhysicsEvaluationError("公开推理拒绝真值字段：" + ", ".join(forbidden))
        unexpected = sorted(supplied.difference({"sample_id", "prompt"}))
        if unexpected:
            raise BoundedPhysicsEvaluationError(
                "公开推理只允许 sample_id 和 prompt，收到：" + ", ".join(unexpected)
            )
        if supplied != {"sample_id", "prompt"}:
            raise BoundedPhysicsEvaluationError("公开推理必须同时提供 sample_id 和 prompt")
        return cls(sample_id=str(payload["sample_id"]), prompt=str(payload["prompt"]))


@dataclass(frozen=True)
class FreeGenerationResult:
    """一次自由生成路径的摘要、预测与结构诊断。"""

    summary: dict[str, object]
    rows: list[dict[str, object]]
    diagnostics: tuple[ConditioningDiagnostics, ...]


@dataclass(frozen=True)
class CandidateScoringResult:
    """一次候选评分路径的摘要、预测、决策与结构诊断。"""

    summary: dict[str, object]
    rows: list[dict[str, object]]
    decisions: list[CandidateDecision]
    diagnostics: tuple[ConditioningDiagnostics, ...]
    candidate_condition_repeat_max_diff: float


def resolve_evaluation_variant(name: str, training_seed: int = 42) -> BoundedEvaluationVariant:
    """只接受固定的 E1 与 E2 正式评估。"""

    if training_seed == 42 and name in _VARIANTS:
        return _VARIANTS[name]
    if name != "e2" or training_seed not in {43, 44}:
        raise BoundedPhysicsEvaluationError("评估变体只允许 e1 或 e2")
    return BoundedEvaluationVariant(
        short_name="e2",
        training_variant="combined",
        training_dir=Path(
            "runs/bounded-physics-conditioning/"
            f"qwen3-1.7b-seed{training_seed}-e2-pinn-combined-full202-v1"
        ),
        output_dir=Path(
            "runs/bounded-physics-conditioning-evaluation/"
            f"qwen3-1.7b-seed{training_seed}-e2-pinn-combined-eval300-v1"
        ),
        run_name=f"qwen3-1.7b-seed{training_seed}-e2-pinn-combined-eval300-v1",
    )


def expected_prediction_files(directory: Path) -> tuple[Path, ...]:
    """返回六分区自由生成与候选评分共十二个预测文件。"""

    return tuple(
        Path(directory) / f"{split}_{mode}.jsonl"
        for split in FIXED_SPLITS
        for mode in ("free", "candidate")
    )


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise BoundedPhysicsEvaluationError(f"配置缺少映射：{name}")
    return dict(value)


def load_fixed_evaluation_configuration(
    raw: Mapping[str, object],
    variant_name: str,
) -> tuple[
    ProbeConfig,
    EvaluationSettings,
    TrackingSettings,
    BoundedEvaluationVariant,
    Path,
    Path,
    Path,
]:
    """解析配置并拒绝任何会改变固定评估协议的字段。"""

    if not isinstance(raw, Mapping):
        raise BoundedPhysicsEvaluationError("配置根节点必须是映射")
    probe = ProbeConfig.from_mapping(_mapping(raw.get("probe"), "probe"))
    variant = resolve_evaluation_variant(variant_name, probe.seed)
    if (
        probe.model_id != FIXED_BASE_MODEL_ID
        or probe.seed not in {42, 43, 44}
        or probe.max_input_length != 512
        or probe.max_new_tokens != 16
    ):
        raise BoundedPhysicsEvaluationError("基座、种子或令牌上限偏离固定评估协议")

    evaluation_data = _mapping(raw.get("evaluation"), "evaluation")
    if "output_dir" in evaluation_data:
        raise BoundedPhysicsEvaluationError("评估输出目录必须由固定 E1/E2 绑定提供")
    evaluation_data["output_dir"] = str(variant.output_dir)
    settings = EvaluationSettings.from_mapping(evaluation_data)
    expected_values = {
        "sample_dir": FIXED_SAMPLE_DIR,
        "samples_per_label": SAMPLES_PER_LABEL,
        "generation_batch_size": GENERATION_BATCH_SIZE,
        "scoring_batch_size": SCORING_BATCH_SIZE,
        "progress_every_batches": PROGRESS_EVERY_BATCHES,
        "max_known_rejection_rate": MAX_KNOWN_REJECTION_RATE,
        "seed": 42,
    }
    for field, expected in expected_values.items():
        if getattr(settings, field) != expected:
            raise BoundedPhysicsEvaluationError(f"evaluation.{field} 必须固定为 {expected}")
    plan = build_evaluation_plan(settings)
    if tuple(split.name for split in plan) != FIXED_SPLITS:
        raise BoundedPhysicsEvaluationError("评估分区必须固定为六分区协议")
    if tuple(split.name for split in plan if split.calibrates_threshold) != ("subtype_validation",):
        raise BoundedPhysicsEvaluationError("阈值只能由 subtype_validation 校准")

    bounded = _mapping(raw.get("bounded_evaluation"), "bounded_evaluation")
    detection_adapter = Path(str(bounded.get("detection_adapter_path", "")))
    s3_evaluation_dir = Path(str(bounded.get("s3_evaluation_dir", "")))
    tolerance = float(bounded.get("candidate_condition_tolerance", math.nan))
    if detection_adapter != FIXED_DETECTION_ADAPTER:
        raise BoundedPhysicsEvaluationError("S3 检测适配器路径偏离固定协议")
    if s3_evaluation_dir != FIXED_S3_EVALUATION_DIR:
        raise BoundedPhysicsEvaluationError("S3 评估参照路径偏离固定协议")
    physics_test_file = Path(str(bounded.get("physics_test_file", "")))
    if physics_test_file != FIXED_PHYSICS_TEST_FILE:
        raise BoundedPhysicsEvaluationError("ns-3 物理测试路径偏离固定 seed44 协议")
    if int(bounded.get("physics_test_samples", 0)) != PHYSICS_TEST_SAMPLES:
        raise BoundedPhysicsEvaluationError("ns-3 物理测试样本数必须固定为 807")
    if int(bounded.get("physics_test_batch_size", 0)) != PHYSICS_TEST_BATCH_SIZE:
        raise BoundedPhysicsEvaluationError("ns-3 物理测试批量必须固定为 8")
    if bounded.get("state_supervision_mode") != STATE_SUPERVISION_MODE:
        raise BoundedPhysicsEvaluationError("物理测试状态掩码必须固定为 anchor0_plus_one")
    if not math.isclose(
        tolerance,
        CANDIDATE_CONDITION_TOLERANCE,
        rel_tol=0.0,
        abs_tol=0.0,
    ):
        raise BoundedPhysicsEvaluationError("候选条件重复容差必须固定为 1e-6")
    variants = _mapping(bounded.get("variants"), "bounded_evaluation.variants")
    configured = _mapping(variants.get(variant.short_name), f"variants.{variant.short_name}")
    expected_variant = {
        "training_variant": variant.training_variant,
        "training_dir": str(variant.training_dir),
        "output_dir": str(variant.output_dir),
        "run_name": variant.run_name,
    }
    if configured != expected_variant:
        raise BoundedPhysicsEvaluationError(f"{variant.short_name} 的固定路径或变体绑定被改写")

    tracking = TrackingSettings.from_mapping(_mapping(raw.get("tracking"), "tracking"))
    tracking = replace(tracking, run_name=variant.run_name)
    return (
        probe,
        settings,
        tracking,
        variant,
        detection_adapter,
        s3_evaluation_dir,
        physics_test_file,
    )


def _validate_requests(requests: Sequence[PublicInferenceRequest]) -> None:
    if not requests or any(not isinstance(item, PublicInferenceRequest) for item in requests):
        raise BoundedPhysicsEvaluationError("公开推理请求必须是非空 PublicInferenceRequest 序列")
    sample_ids = [request.sample_id for request in requests]
    if len(sample_ids) != len(set(sample_ids)):
        raise BoundedPhysicsEvaluationError("公开推理请求包含重复 sample_id")


def _project_public_requests(
    records: Sequence[Mapping[str, object]],
) -> list[PublicInferenceRequest]:
    return [
        PublicInferenceRequest(
            sample_id=str(record["sample_id"]),
            prompt=str(record["prompt"]),
        )
        for record in records
    ]


def _runtime_device(runtime: PhysicsConditionedRuntime) -> torch.device:
    try:
        return next(runtime.model.parameters()).device
    except StopIteration as error:
        raise BoundedPhysicsEvaluationError("底层模型没有可定位设备的参数") from error


def _load_frozen_evaluation_model(
    probe: ProbeConfig,
    detection_adapter_path: Path,
) -> tuple[object, torch.nn.Module, torch.nn.Module]:
    """按既有 S3 评估加载方式构造冻结模型，并补载状态头。"""

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if probe.model_id != FIXED_BASE_MODEL_ID:
        raise BoundedPhysicsEvaluationError(f"基座路径必须固定为 {FIXED_BASE_MODEL_ID}")
    if detection_adapter_path != FIXED_DETECTION_ADAPTER:
        raise BoundedPhysicsEvaluationError(f"S3 路径必须固定为 {FIXED_DETECTION_ADAPTER}")
    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝启动有界物理条件评估")
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
    tokenizer.padding_side = "left"
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
    model = PeftModel.from_pretrained(
        base_model,
        str(detection_adapter_path),
        adapter_name=DETECTION_ADAPTER_NAME,
        is_trainable=False,
    )
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    model.config.use_cache = True
    model.eval()
    state_head = _load_state_head(
        detection_adapter_path.parent / "state_head.pt",
        int(model.config.hidden_size),
    )
    return tokenizer, model, state_head


def _move_inputs(inputs: object, device: torch.device) -> dict[str, torch.Tensor]:
    if hasattr(inputs, "to"):
        inputs = inputs.to(device)
    if not isinstance(inputs, Mapping):
        raise BoundedPhysicsEvaluationError("分词器批量输出必须是映射")
    moved = {}
    for name in ("input_ids", "attention_mask"):
        value = inputs.get(name)
        if not isinstance(value, torch.Tensor):
            raise BoundedPhysicsEvaluationError(f"分词器输出缺少张量 {name}")
        moved[name] = value.to(device)
    return moved


def _cuda_synchronize() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def _cuda_reset_peak_memory() -> None:
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def _cuda_peak_memory_mib() -> float:
    if not torch.cuda.is_available():
        return 0.0
    return float(torch.cuda.max_memory_allocated() / (1024**2))


def _validate_enabled_diagnostics(
    diagnostics: ConditioningDiagnostics,
    *,
    path: str,
) -> None:
    if diagnostics.source_hook_count < 1 or any(
        count < 1 for count in diagnostics.target_hook_counts
    ):
        raise BoundedPhysicsEvaluationError(f"{path} 未经过条件源与四个注入层")
    if diagnostics.target_hook_counts != (diagnostics.source_hook_count,) * 4:
        raise BoundedPhysicsEvaluationError(f"{path} 的源层与目标层挂钩次数不一致")
    if path == "generation" and diagnostics.prefill_count != 1:
        raise BoundedPhysicsEvaluationError("自由生成必须恰好执行一次完整提示预填充")


def _validate_bypass_diagnostics(diagnostics: ConditioningDiagnostics) -> None:
    if (
        diagnostics.source_hook_count != 0
        or diagnostics.target_hook_counts != (0, 0, 0, 0)
        or diagnostics.prefill_count != 0
        or diagnostics.cached_decode_count != 0
    ):
        raise BoundedPhysicsEvaluationError("显式旁路不得捕获状态或执行条件注入")


def _free_metrics(
    truth_records: Sequence[Mapping[str, object]],
    rows: Sequence[Mapping[str, object]],
    split: EvaluationSplit,
) -> dict[str, object]:
    return compute_open_set_metrics(
        truth=[str(record["task_label"]) for record in truth_records[: len(rows)]],
        predictions=[row.get("parsed_label") for row in rows],
        known_labels=split.candidate_labels,
        unknown_label=UNKNOWN_LABEL if UNKNOWN_LABEL in split.free_generation_labels else None,
    )


def _attach_evaluation_truth(
    rows: Sequence[Mapping[str, object]],
    truth_records: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """推理完成后再附加真值，确保真值从未进入公开推理调用。"""

    if len(rows) != len(truth_records):
        raise BoundedPhysicsEvaluationError("推理预测与评估真值数量不一致")
    attached = []
    for index, (row, truth) in enumerate(zip(rows, truth_records, strict=True)):
        if row.get("sample_id") != truth.get("sample_id"):
            raise BoundedPhysicsEvaluationError(f"第 {index} 个推理预测与真值样本不一致")
        attached.append({**dict(row), "true_label": truth["task_label"]})
    return attached


def run_public_free_generation(
    runtime: PhysicsConditionedRuntime,
    tokenizer: object,
    requests: Sequence[PublicInferenceRequest],
    split: EvaluationSplit,
    settings: EvaluationSettings,
    progress: _ProgressLogger | None,
    *,
    bypass: bool,
    max_new_tokens: int,
) -> FreeGenerationResult:
    """只用公开提示执行缓存式生成，并把真值留在推理调用之外。"""

    _validate_requests(requests)
    _cuda_reset_peak_memory()
    rows: list[dict[str, object]] = []
    diagnostics: list[ConditioningDiagnostics] = []
    input_tokens_total = 0
    generated_tokens_total = 0
    amortized_latencies: list[float] = []
    started_at = time.perf_counter()
    batch_count = math.ceil(len(requests) / settings.generation_batch_size)
    device = _runtime_device(runtime)

    for batch_index, start in enumerate(
        range(0, len(requests), settings.generation_batch_size), start=1
    ):
        batch_requests = requests[start : start + settings.generation_batch_size]
        formatted_prompts = [
            _format_generation_prompt(tokenizer, request.prompt) for request in batch_requests
        ]
        inputs = _move_inputs(
            tokenizer(
                formatted_prompts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ),
            device,
        )
        input_width = int(inputs["input_ids"].shape[1])
        input_counts = [int(value) for value in inputs["attention_mask"].sum(dim=1).tolist()]
        _cuda_synchronize()
        batch_started_at = time.perf_counter()
        with torch.inference_mode():
            generated = runtime.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                bypass=bypass,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                num_beams=1,
                use_cache=True,
                pad_token_id=int(tokenizer.pad_token_id),
                eos_token_id=int(tokenizer.eos_token_id),
            )
        _cuda_synchronize()
        batch_seconds = time.perf_counter() - batch_started_at
        if bypass:
            _validate_bypass_diagnostics(generated.diagnostics)
        else:
            _validate_enabled_diagnostics(generated.diagnostics, path="generation")
            diagnostics.append(generated.diagnostics)
        output_ids = generated.model_output
        if not isinstance(output_ids, torch.Tensor) or output_ids.ndim != 2:
            raise BoundedPhysicsEvaluationError("缓存生成必须返回二维令牌张量")
        new_token_rows = output_ids[:, input_width:]
        per_sample_latency_ms = batch_seconds * 1000 / len(batch_requests)

        for request, input_count, new_tokens in zip(
            batch_requests,
            input_counts,
            new_token_rows,
            strict=True,
        ):
            token_ids = [int(token) for token in new_tokens.tolist()]
            if tokenizer.eos_token_id in token_ids:
                generated_count = token_ids.index(tokenizer.eos_token_id) + 1
            else:
                generated_count = len(token_ids)
            text = tokenizer.decode(token_ids[:generated_count], skip_special_tokens=True)
            parsed = parse_label_prediction(text, split.free_generation_labels)
            rows.append(
                {
                    "sample_id": request.sample_id,
                    "generated_text": text,
                    "parsed_label": parsed.label,
                    "is_valid": parsed.is_valid,
                    "parse_error": parsed.error,
                    "input_tokens": input_count,
                    "generated_tokens": generated_count,
                    "amortized_latency_ms": per_sample_latency_ms,
                }
            )
            input_tokens_total += input_count
            generated_tokens_total += generated_count
            amortized_latencies.append(per_sample_latency_ms)

        if progress is not None and (
            batch_index % settings.progress_every_batches == 0 or batch_index == batch_count
        ):
            elapsed = time.perf_counter() - started_at
            metrics = {
                "progress": {
                    "processed_samples": len(rows),
                    "total_samples": len(requests),
                    "samples_per_second": len(rows) / elapsed,
                    "peak_gpu_memory_mib": _cuda_peak_memory_mib(),
                }
            }
            route = "bypass" if bypass else "enabled"
            progress.log(f"evaluation/{route}/free/{split.name}", metrics)

    total_seconds = time.perf_counter() - started_at
    summary = {
        "efficiency": {
            "total_seconds": total_seconds,
            "samples_per_second": len(requests) / total_seconds,
            "input_tokens": input_tokens_total,
            "generated_tokens": generated_tokens_total,
            "amortized_latency_p50_ms": _percentile(amortized_latencies, 0.50),
            "amortized_latency_p95_ms": _percentile(amortized_latencies, 0.95),
            "peak_gpu_memory_mib": _cuda_peak_memory_mib(),
        },
    }
    return FreeGenerationResult(summary, rows, tuple(diagnostics))


def _candidate_metrics(
    truth_records: Sequence[Mapping[str, object]],
    decisions: Sequence[CandidateDecision],
    split: EvaluationSplit,
    threshold: float | None,
) -> tuple[dict[str, object], list[str]]:
    raw_predictions = [decision.label for decision in decisions]
    if threshold is None:
        predictions = raw_predictions
        unknown_label = None
    else:
        predictions = apply_unknown_rejection(
            raw_predictions,
            [decision.confidence for decision in decisions],
            threshold,
            UNKNOWN_LABEL,
        )
        unknown_label = UNKNOWN_LABEL
    metrics = compute_open_set_metrics(
        truth=[str(record["task_label"]) for record in truth_records[: len(decisions)]],
        predictions=predictions,
        known_labels=split.candidate_labels,
        unknown_label=unknown_label,
    )
    return metrics, predictions


def candidate_condition_repeat_max_diff(
    predicted_state: torch.Tensor,
    condition_tokens: torch.Tensor,
    candidates_per_prompt: int,
) -> tuple[float, list[float]]:
    """核对同一提示的全部候选共享完全相同的条件。"""

    if isinstance(candidates_per_prompt, bool) or candidates_per_prompt < 2:
        raise BoundedPhysicsEvaluationError("每个提示必须至少包含两个候选")
    if (
        not isinstance(predicted_state, torch.Tensor)
        or predicted_state.ndim != 2
        or predicted_state.shape[1] != 5
    ):
        raise BoundedPhysicsEvaluationError("候选评分必须返回 [N,5] 预测状态")
    if (
        not isinstance(condition_tokens, torch.Tensor)
        or condition_tokens.ndim != 3
        or condition_tokens.shape[1:] != (9, 256)
        or condition_tokens.shape[0] != predicted_state.shape[0]
    ):
        raise BoundedPhysicsEvaluationError("候选评分必须返回 [N,9,256] 条件词元")
    if predicted_state.shape[0] % candidates_per_prompt != 0:
        raise BoundedPhysicsEvaluationError("候选条件数量不能按提示完整分组")
    if not bool(torch.isfinite(predicted_state).all().item()) or not bool(
        torch.isfinite(condition_tokens).all().item()
    ):
        raise BoundedPhysicsEvaluationError("候选条件包含非有限值")

    prompt_count = predicted_state.shape[0] // candidates_per_prompt
    states = predicted_state.float().reshape(prompt_count, candidates_per_prompt, 5)
    tokens = condition_tokens.float().reshape(prompt_count, candidates_per_prompt, 9, 256)
    state_differences = (states - states[:, :1]).abs().flatten(start_dim=1).amax(dim=1)
    token_differences = (tokens - tokens[:, :1]).abs().flatten(start_dim=1).amax(dim=1)
    per_prompt = torch.maximum(state_differences, token_differences)
    values = [float(value) for value in per_prompt.tolist()]
    return max(values, default=0.0), values


def run_public_candidate_scoring(
    runtime: PhysicsConditionedRuntime,
    tokenizer: object,
    requests: Sequence[PublicInferenceRequest],
    split: EvaluationSplit,
    settings: EvaluationSettings,
    progress: _ProgressLogger | None,
    *,
    threshold: float | None,
    bypass: bool,
) -> CandidateScoringResult:
    """显式传递 completion_start，通过同一运行时执行候选完成评分。"""

    _validate_requests(requests)
    label_count = len(split.candidate_labels)
    records_per_batch = settings.scoring_batch_size // label_count
    if records_per_batch <= 0:
        raise BoundedPhysicsEvaluationError("候选评分批量小于候选标签数")
    _cuda_reset_peak_memory()
    device = _runtime_device(runtime)
    pad_token_id = int(tokenizer.pad_token_id)
    all_scores: list[float] = []
    all_decisions: list[CandidateDecision] = []
    all_diagnostics: list[ConditioningDiagnostics] = []
    per_record_condition_differences: list[float] = []
    amortized_latencies: list[float] = []
    candidate_tokens = 0
    started_at = time.perf_counter()
    batch_count = math.ceil(len(requests) / records_per_batch)

    for batch_index, start in enumerate(range(0, len(requests), records_per_batch), start=1):
        batch_requests = requests[start : start + records_per_batch]
        sequences = []
        for request in batch_requests:
            formatted_prompt = _format_generation_prompt(tokenizer, request.prompt)
            for label in split.candidate_labels:
                sequences.append(
                    encode_candidate_sequence(
                        tokenizer,
                        formatted_prompt=formatted_prompt,
                        label=label,
                        max_length=512,
                    )
                )
        max_length = max(len(sequence.input_ids) for sequence in sequences)
        input_ids = torch.full(
            (len(sequences), max_length),
            pad_token_id,
            dtype=torch.long,
            device=device,
        )
        attention_mask = torch.zeros_like(input_ids)
        completion_starts = torch.empty(len(sequences), dtype=torch.long, device=device)
        for row_index, sequence in enumerate(sequences):
            length = len(sequence.input_ids)
            input_ids[row_index, :length] = torch.tensor(
                sequence.input_ids,
                dtype=torch.long,
                device=device,
            )
            attention_mask[row_index, :length] = 1
            completion_starts[row_index] = sequence.completion_start
            candidate_tokens += length

        _cuda_synchronize()
        batch_started_at = time.perf_counter()
        with torch.inference_mode():
            output = runtime(
                input_ids=input_ids,
                attention_mask=attention_mask,
                completion_start=completion_starts,
                bypass=bypass,
                use_cache=False,
                return_dict=True,
            )
        _cuda_synchronize()
        batch_seconds = time.perf_counter() - batch_started_at
        if bypass:
            _validate_bypass_diagnostics(output.diagnostics)
            batch_condition_differences = [0.0] * len(batch_requests)
        else:
            _validate_enabled_diagnostics(output.diagnostics, path="candidate_scoring")
            all_diagnostics.append(output.diagnostics)
            if output.predicted_state is None or output.condition_tokens is None:
                raise BoundedPhysicsEvaluationError("候选评分结构路径未返回条件")
            batch_maximum, batch_condition_differences = candidate_condition_repeat_max_diff(
                output.predicted_state,
                output.condition_tokens,
                label_count,
            )
            if batch_maximum > CANDIDATE_CONDITION_TOLERANCE:
                raise BoundedPhysicsEvaluationError(
                    "同一提示的候选条件差超过 1e-6，评估无效：" f"{batch_maximum:.9g}"
                )
        per_record_condition_differences.extend(batch_condition_differences)
        per_sample_latency_ms = batch_seconds * 1000 / len(batch_requests)
        amortized_latencies.extend([per_sample_latency_ms] * len(batch_requests))
        logits = output.logits
        batch_scores = [
            completion_mean_log_probability(logits[index, : len(sequence.input_ids)], sequence)
            for index, sequence in enumerate(sequences)
        ]
        all_scores.extend(batch_scores)
        all_decisions.extend(decode_candidate_scores(batch_scores, split.candidate_labels))

        if progress is not None and (
            batch_index % settings.progress_every_batches == 0 or batch_index == batch_count
        ):
            elapsed = time.perf_counter() - started_at
            metrics = {
                "progress": {
                    "processed_samples": len(all_decisions),
                    "total_samples": len(requests),
                    "samples_per_second": len(all_decisions) / elapsed,
                    "peak_gpu_memory_mib": _cuda_peak_memory_mib(),
                }
            }
            route = "bypass" if bypass else "enabled"
            progress.log(f"evaluation/{route}/candidate/{split.name}", metrics)

    total_seconds = time.perf_counter() - started_at
    raw_predictions = [decision.label for decision in all_decisions]
    predictions = (
        raw_predictions
        if threshold is None
        else apply_unknown_rejection(
            raw_predictions,
            [decision.confidence for decision in all_decisions],
            threshold,
            UNKNOWN_LABEL,
        )
    )
    rows = []
    for index, (request, decision, prediction, condition_difference) in enumerate(
        zip(
            requests,
            all_decisions,
            predictions,
            per_record_condition_differences,
            strict=True,
        )
    ):
        score_row = all_scores[index * label_count : (index + 1) * label_count]
        row = {
            "sample_id": request.sample_id,
            "raw_prediction": decision.label,
            "prediction": prediction,
            "confidence": decision.confidence,
            "threshold": threshold,
            "candidate_probabilities": dict(
                zip(split.candidate_labels, decision.probabilities, strict=True)
            ),
            "candidate_mean_log_probabilities": dict(
                zip(split.candidate_labels, score_row, strict=True)
            ),
        }
        if not bypass:
            row["candidate_condition_repeat_max_diff"] = condition_difference
        rows.append(row)

    maximum_difference = max(per_record_condition_differences, default=0.0)
    summary = {
        "candidate_condition_repeat_max_diff": maximum_difference if not bypass else None,
        "efficiency": {
            "total_seconds": total_seconds,
            "samples_per_second": len(requests) / total_seconds,
            "candidate_sequences": len(all_scores),
            "candidate_tokens": candidate_tokens,
            "amortized_latency_p50_ms": _percentile(amortized_latencies, 0.50),
            "amortized_latency_p95_ms": _percentile(amortized_latencies, 0.95),
            "peak_gpu_memory_mib": _cuda_peak_memory_mib(),
        },
    }
    return CandidateScoringResult(
        summary,
        rows,
        all_decisions,
        tuple(all_diagnostics),
        maximum_difference,
    )


def _read_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BoundedPhysicsEvaluationError(f"无法读取 JSON：{path}：{error}") from error
    if not isinstance(payload, dict):
        raise BoundedPhysicsEvaluationError(f"JSON 顶层必须是对象：{path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows = []
    try:
        with path.open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise BoundedPhysicsEvaluationError(f"预测第 {line_number} 行不是对象：{path}")
                rows.append(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise BoundedPhysicsEvaluationError(f"无法读取预测文件：{path}：{error}") from error
    if not rows:
        raise BoundedPhysicsEvaluationError(f"预测文件为空：{path}")
    return rows


def _numeric_difference(reference: object, candidate: object) -> float:
    if isinstance(reference, bool) or isinstance(candidate, bool):
        if reference != candidate:
            raise BoundedPhysicsEvaluationError("旁路布尔预测字段与 S3 不一致")
        return 0.0
    if isinstance(reference, (int, float)) and isinstance(candidate, (int, float)):
        difference = abs(float(reference) - float(candidate))
        if not math.isfinite(difference):
            raise BoundedPhysicsEvaluationError("旁路预测数值差为非有限值")
        return difference
    if isinstance(reference, Mapping) and isinstance(candidate, Mapping):
        if set(reference) != set(candidate):
            raise BoundedPhysicsEvaluationError("旁路预测映射键与 S3 不一致")
        return max(
            (_numeric_difference(reference[key], candidate[key]) for key in reference),
            default=0.0,
        )
    if reference != candidate:
        raise BoundedPhysicsEvaluationError(
            f"旁路预测字段与 S3 不一致：{reference!r} != {candidate!r}"
        )
    return 0.0


def assert_bypass_matches_s3(
    s3_prediction_path: Path,
    bypass_rows: Sequence[Mapping[str, object]],
    *,
    mode: str,
) -> dict[str, object]:
    """逐样本核对旁路与固定 S3 预测，排除仅时延字段。"""

    if mode == "free":
        fields = (
            "sample_id",
            "true_label",
            "generated_text",
            "parsed_label",
            "is_valid",
            "parse_error",
            "input_tokens",
            "generated_tokens",
        )
    elif mode == "candidate":
        fields = (
            "sample_id",
            "true_label",
            "raw_prediction",
            "prediction",
            "confidence",
            "threshold",
            "candidate_probabilities",
            "candidate_mean_log_probabilities",
        )
    else:
        raise BoundedPhysicsEvaluationError("预测模式只允许 free 或 candidate")

    s3_rows = _read_jsonl(Path(s3_prediction_path))
    if len(s3_rows) != len(bypass_rows):
        raise BoundedPhysicsEvaluationError("旁路与 S3 预测行数不一致")
    maximum_difference = 0.0
    for index, (reference, candidate) in enumerate(zip(s3_rows, bypass_rows, strict=True)):
        for field in fields:
            if field not in reference or field not in candidate:
                raise BoundedPhysicsEvaluationError(f"第 {index} 行缺少旁路核对字段：{field}")
            try:
                maximum_difference = max(
                    maximum_difference,
                    _numeric_difference(reference[field], candidate[field]),
                )
            except BoundedPhysicsEvaluationError as error:
                raise BoundedPhysicsEvaluationError(
                    f"第 {index} 行字段 {field} 未恢复 S3：{error}"
                ) from error
    if maximum_difference > 1e-6:
        raise BoundedPhysicsEvaluationError(
            f"旁路与 S3 的逐样本数值差超过 1e-6：{maximum_difference:.9g}"
        )
    return {
        "s3_prediction_path": str(s3_prediction_path),
        "rows": len(s3_rows),
        "compared_fields": list(fields),
        "max_abs_numeric_diff": maximum_difference,
        "equivalent": True,
    }


def aggregate_conditioning_diagnostics(
    diagnostics: Sequence[ConditioningDiagnostics],
    *,
    path: str,
) -> dict[str, object]:
    """聚合正式评估中结构启用路径的挂钩和幅值证据。"""

    if not diagnostics:
        raise BoundedPhysicsEvaluationError(f"{path} 路径没有结构诊断")
    return {
        "calls": len(diagnostics),
        "gate_values": list(diagnostics[-1].gate_values),
        "mean_attention_entropies": [
            sum(item.attention_entropies[index] for item in diagnostics) / len(diagnostics)
            for index in range(4)
        ],
        "max_residual_ratio": max(item.max_residual_ratio for item in diagnostics),
        "source_hook_count": sum(item.source_hook_count for item in diagnostics),
        "target_hook_counts": [
            sum(item.target_hook_counts[index] for item in diagnostics) for index in range(4)
        ],
        "prefill_count": sum(item.prefill_count for item in diagnostics),
        "cached_decode_count": sum(item.cached_decode_count for item in diagnostics),
    }


def build_analysis_training_summary(
    summary: Mapping[str, object],
    physics_test_summary: Mapping[str, object],
) -> dict[str, object]:
    """为既有 S3/S4 分析器提供不改语义的指标键兼容视图。"""

    normalized = json.loads(json.dumps(summary, ensure_ascii=False))
    validation = normalized.get("validation")
    if not isinstance(validation, dict):
        raise BoundedPhysicsEvaluationError("有界训练摘要缺少 validation")
    test_metrics = physics_test_summary.get("metrics")
    if not isinstance(test_metrics, Mapping):
        raise BoundedPhysicsEvaluationError("物理测试摘要缺少 metrics")
    aliases = {
        "state_mse_unobserved": "unobserved_reference_mse",
        "physics_residual_mse": "queue_residual_reference_mse",
    }
    for target, source in aliases.items():
        value = test_metrics.get(source)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0
        ):
            raise BoundedPhysicsEvaluationError(f"有界训练摘要缺少有限非负指标：{source}")
        validation[target] = value
    normalized["analysis_compatibility"] = {
        "consumer": "flow_probe.s3_s4_detection_analysis.analyze",
        "key_mapping": aliases,
        "mechanism_metric_source": "physics_test_summary.json",
        "historical_s4_means_current_candidate": True,
    }
    normalized["physics_test"] = json.loads(json.dumps(physics_test_summary, ensure_ascii=False))
    return normalized


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _prepare_selected_records(
    settings: EvaluationSettings,
) -> tuple[
    tuple[EvaluationSplit, ...],
    dict[str, list[dict[str, object]]],
    dict[str, object],
]:
    plan = build_evaluation_plan(settings)
    missing = [str(split.path) for split in plan if not split.path.is_file()]
    if missing:
        raise BoundedPhysicsEvaluationError("评估数据文件缺失：" + ", ".join(missing))
    selected_records: dict[str, list[dict[str, object]]] = {}
    selected_manifest: dict[str, object] = {}
    for split in plan:
        records = _load_records(split.path, split.free_generation_labels)
        present_labels = tuple(
            label
            for label in split.free_generation_labels
            if any(str(record["task_label"]) == label for record in records)
        )
        selected = select_stratified_records(
            records,
            labels=present_labels,
            per_label=settings.samples_per_label,
            seed=_derived_seed(settings.seed, split.name),
        )
        selected_records[split.name] = selected
        selected_id_digest = hashlib.sha256(
            "\n".join(str(record["sample_id"]) for record in selected).encode()
        ).hexdigest()
        selected_manifest[split.name] = {
            "source_path": str(split.path),
            "source_sha256": _file_sha256(split.path),
            "source_count": len(records),
            "selected_count": len(selected),
            "selected_sample_ids_sha256": selected_id_digest,
            "selected_label_distribution": {
                label: sum(str(record["task_label"]) == label for record in selected)
                for label in present_labels
            },
        }
    return plan, selected_records, selected_manifest


def run_bounded_physics_evaluation(
    probe: ProbeConfig,
    settings: EvaluationSettings,
    tracking: TrackingSettings,
    variant: BoundedEvaluationVariant,
    detection_adapter_path: Path,
    s3_evaluation_dir: Path,
    physics_test_file: Path,
) -> dict[str, object]:
    """执行结构启用、显式旁路、S3 恢复核对和固定阈值评估。"""

    if settings.output_dir.exists():
        raise BoundedPhysicsEvaluationError(f"评估输出目录已存在，拒绝复用：{settings.output_dir}")
    if settings.output_dir != variant.output_dir:
        raise BoundedPhysicsEvaluationError("评估输出目录与固定变体绑定不一致")
    if detection_adapter_path != FIXED_DETECTION_ADAPTER:
        raise BoundedPhysicsEvaluationError("S3 检测适配器路径偏离固定协议")
    if s3_evaluation_dir != FIXED_S3_EVALUATION_DIR:
        raise BoundedPhysicsEvaluationError("S3 评估参照路径偏离固定协议")
    if physics_test_file != FIXED_PHYSICS_TEST_FILE:
        raise BoundedPhysicsEvaluationError("ns-3 物理测试路径偏离固定 seed44 协议")
    reference_manifest_path = s3_evaluation_dir / "selected_samples_manifest.json"
    reference_prediction_dir = s3_evaluation_dir / "predictions"
    required_reference_files = expected_prediction_files(reference_prediction_dir)
    missing_reference = [
        str(path)
        for path in (reference_manifest_path, *required_reference_files)
        if not path.is_file()
    ]
    if missing_reference:
        raise BoundedPhysicsEvaluationError(
            "S3 正式评估参照不完整：" + ", ".join(missing_reference)
        )

    plan, selected_records, selected_manifest = _prepare_selected_records(settings)
    reference_manifest = _read_json(reference_manifest_path)
    if selected_manifest != reference_manifest:
        raise BoundedPhysicsEvaluationError("当前选择样本清单与 S3 不完全一致")

    output_dir = settings.output_dir
    predictions_dir = output_dir / "predictions"
    bypass_predictions_dir = output_dir / "bypass_predictions"
    summary_path = output_dir / "evaluation_summary.json"
    metrics_path = output_dir / "swanlab_metrics.json"
    history_path = output_dir / "metric_history.jsonl"
    threshold_path = output_dir / "threshold_calibration.json"
    config_path = output_dir / "config_snapshot.json"
    environment_path = output_dir / "environment.json"
    selected_manifest_path = output_dir / "selected_samples_manifest.json"
    runtime_audit_path = output_dir / "runtime_path_audit.json"
    bypass_audit_path = output_dir / "bypass_equivalence.json"
    input_manifest_path = output_dir / "input_sha256.json"
    analysis_view_dir = output_dir / "analysis_training_view"
    analysis_training_summary_path = analysis_view_dir / "training_summary.json"
    physics_test_summary_path = output_dir / "physics_test_summary.json"

    config_snapshot = {
        "schema_version": EVALUATION_SCHEMA_VERSION,
        "probe": asdict(probe),
        "evaluation": {
            **asdict(settings),
            "sample_dir": str(settings.sample_dir),
            "output_dir": str(settings.output_dir),
        },
        "variant": {
            **asdict(variant),
            "training_dir": str(variant.training_dir),
            "output_dir": str(variant.output_dir),
        },
        "detection_adapter_path": str(detection_adapter_path),
        "s3_evaluation_dir": str(s3_evaluation_dir),
        "physics_test": {
            "path": str(physics_test_file),
            "expected_samples": PHYSICS_TEST_SAMPLES,
            "batch_size": PHYSICS_TEST_BATCH_SIZE,
            "state_supervision_mode": STATE_SUPERVISION_MODE,
            "calibration": "none",
            "parameter_tuning": "none",
        },
        "protocol": {
            "threshold_source": "subtype_validation_only",
            "candidate_condition_tolerance": CANDIDATE_CONDITION_TOLERANCE,
            "public_inference_fields": ["sample_id", "prompt"],
            "generation": "PhysicsConditionedRuntime.generate",
            "candidate_scoring": "PhysicsConditionedRuntime.forward(completion_start=...)",
            "bypass": "PhysicsConditionedRuntime explicit bypass",
        },
    }
    data_files = {
        "evaluation_summary": summary_path,
        "swanlab_metrics": metrics_path,
        "metric_history": history_path,
        "threshold_calibration": threshold_path,
        "config_snapshot": config_path,
        "environment": environment_path,
        "selected_samples_manifest": selected_manifest_path,
        "runtime_path_audit": runtime_audit_path,
        "bypass_equivalence": bypass_audit_path,
        "input_sha256": input_manifest_path,
        "analysis_training_summary": analysis_training_summary_path,
        "physics_test_summary": physics_test_summary_path,
        "predictions": predictions_dir,
        "bypass_predictions": bypass_predictions_dir,
        "structure_artifacts": variant.training_dir,
        "s3_evaluation_reference": s3_evaluation_dir,
    }

    with (
        capture_console_log(output_dir / "console.log"),
        swanlab_run(
            settings=tracking,
            phase=EVALUATION_PHASE,
            config=config_snapshot,
            artifact_dir=output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        predictions_dir.mkdir(parents=True, exist_ok=False)
        bypass_predictions_dir.mkdir(parents=True, exist_ok=False)
        _write_json(config_path, config_snapshot)
        _write_json(selected_manifest_path, selected_manifest)
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
        input_files = (
            variant.training_dir / "structure_config.json",
            variant.training_dir / "structure_state.pt",
            variant.training_dir / "base_binding.json",
            variant.training_dir / "training_summary.json",
            variant.training_dir / "runtime_path_audit.json",
            physics_test_file,
            reference_manifest_path,
            *required_reference_files,
        )
        missing_inputs = [str(path) for path in input_files if not path.is_file()]
        if missing_inputs:
            raise BoundedPhysicsEvaluationError(
                "有界结构或 S3 输入制品不完整：" + ", ".join(missing_inputs)
            )
        training_summary = _read_json(variant.training_dir / "training_summary.json")
        if int(training_summary.get("seed", -1)) != probe.seed:
            raise BoundedPhysicsEvaluationError("训练制品种子与评估绑定不一致")
        _write_json(
            input_manifest_path,
            {
                "schema_version": EVALUATION_SCHEMA_VERSION,
                "selected_samples_identical_to_s3": True,
                "files": {str(path): _file_sha256(path) for path in input_files},
            },
        )

        tokenizer, model, state_head = _load_frozen_evaluation_model(
            probe,
            detection_adapter_path,
        )
        try:
            device = next(model.parameters()).device
        except StopIteration as error:
            raise BoundedPhysicsEvaluationError("底层模型没有可定位设备的参数") from error
        runtime = PhysicsConditionedRuntime(model, state_head).to(
            device=device,
            dtype=torch.bfloat16,
        )
        try:
            metadata = load_bounded_structure_artifacts(
                runtime,
                variant.training_dir,
                expected_model_id=probe.model_id,
                expected_detection_adapter_path=detection_adapter_path,
            )
            structure_config = metadata["structure_config"]
            if structure_config.get("variant") != variant.training_variant:
                raise BoundedPhysicsEvaluationError("结构制品训练变体与 E1/E2 绑定不一致")
            runtime.eval()
            model.eval()
            model.config.use_cache = True
            for parameter in runtime.parameters():
                parameter.requires_grad_(False)
            if any(parameter.requires_grad for parameter in model.parameters()):
                raise BoundedPhysicsEvaluationError("正式评估发现冻结 Qwen/S3 可训练参数")

            training_runtime_audit = _read_json(variant.training_dir / "runtime_path_audit.json")
            training_path = training_runtime_audit.get("training")
            if not isinstance(training_path, Mapping):
                raise BoundedPhysicsEvaluationError("训练制品缺少结构训练前向审计")
            training_target_counts = training_path.get("target_hook_counts")
            if (
                not isinstance(training_target_counts, list)
                or len(training_target_counts) != 4
                or int(training_path.get("source_hook_count", 0)) < 1
                or any(int(value) < 1 for value in training_target_counts)
            ):
                raise BoundedPhysicsEvaluationError("训练制品未证明训练前向经过四层结构")

            physics_test_records = _load_jsonl(physics_test_file)
            if len(physics_test_records) != PHYSICS_TEST_SAMPLES:
                raise BoundedPhysicsEvaluationError(
                    "ns-3 物理测试集必须恰好包含 807 条记录：" f"实际 {len(physics_test_records)}"
                )
            physics_test_masks = build_state_supervision_masks(
                physics_test_records,
                STATE_SUPERVISION_MODE,
                probe.seed,
            )
            physics_test_metrics = _evaluate_conditions(
                runtime,
                tokenizer,
                physics_test_records,
                batch_size=PHYSICS_TEST_BATCH_SIZE,
                max_length=probe.max_input_length,
                device=device,
                state_masks=physics_test_masks,
            )
            runtime.eval()
            model.eval()
            physics_test_summary = {
                "schema_version": EVALUATION_SCHEMA_VERSION,
                "variant": variant.short_name,
                "training_variant": variant.training_variant,
                "source_path": str(physics_test_file),
                "source_sha256": _file_sha256(physics_test_file),
                "sample_count": len(physics_test_records),
                "split_seed": 44,
                "state_mask_seed": probe.seed,
                "state_supervision_mode": STATE_SUPERVISION_MODE,
                "calibration": None,
                "parameter_tuning": False,
                "metrics": physics_test_metrics,
            }
            _write_json(physics_test_summary_path, physics_test_summary)

            progress = _ProgressLogger(swanlab, history_path)
            results: dict[str, object] = {}
            bypass_results: dict[str, object] = {}
            bypass_files: dict[str, object] = {}
            generation_diagnostics: list[ConditioningDiagnostics] = []
            candidate_diagnostics: list[ConditioningDiagnostics] = []
            enabled_threshold_calibration = None
            bypass_threshold_calibration = None
            maximum_condition_difference = 0.0

            for split in plan:
                records = selected_records[split.name]
                requests = _project_public_requests(records)
                print(f"评估分区开始：{split.name}，样本数={len(records)}", flush=True)

                enabled_free = run_public_free_generation(
                    runtime,
                    tokenizer,
                    requests,
                    split,
                    settings,
                    progress,
                    bypass=False,
                    max_new_tokens=probe.max_new_tokens,
                )
                bypass_free = run_public_free_generation(
                    runtime,
                    tokenizer,
                    requests,
                    split,
                    settings,
                    progress,
                    bypass=True,
                    max_new_tokens=probe.max_new_tokens,
                )
                enabled_free_path = predictions_dir / f"{split.name}_free.jsonl"
                bypass_free_path = bypass_predictions_dir / f"{split.name}_free.jsonl"
                enabled_free_rows = _attach_evaluation_truth(enabled_free.rows, records)
                bypass_free_rows = _attach_evaluation_truth(bypass_free.rows, records)
                enabled_free_summary = {
                    **enabled_free.summary,
                    "metrics": _free_metrics(records, enabled_free_rows, split),
                }
                bypass_free_summary = {
                    **bypass_free.summary,
                    "metrics": _free_metrics(records, bypass_free_rows, split),
                }
                _write_jsonl(enabled_free_path, enabled_free_rows)
                _write_jsonl(bypass_free_path, bypass_free_rows)
                bypass_files[f"{split.name}_free"] = assert_bypass_matches_s3(
                    reference_prediction_dir / f"{split.name}_free.jsonl",
                    bypass_free_rows,
                    mode="free",
                )
                generation_diagnostics.extend(enabled_free.diagnostics)

                enabled_threshold = None
                bypass_threshold = None
                if split.name not in {"family_test", "subtype_validation"}:
                    if (
                        enabled_threshold_calibration is None
                        or bypass_threshold_calibration is None
                    ):
                        raise BoundedPhysicsEvaluationError(
                            "子类测试开始前缺少 subtype_validation 阈值"
                        )
                    enabled_threshold = enabled_threshold_calibration.threshold
                    bypass_threshold = bypass_threshold_calibration.threshold

                enabled_candidate = run_public_candidate_scoring(
                    runtime,
                    tokenizer,
                    requests,
                    split,
                    settings,
                    progress,
                    threshold=enabled_threshold,
                    bypass=False,
                )
                bypass_candidate = run_public_candidate_scoring(
                    runtime,
                    tokenizer,
                    requests,
                    split,
                    settings,
                    progress,
                    threshold=bypass_threshold,
                    bypass=True,
                )
                enabled_candidate_path = predictions_dir / f"{split.name}_candidate.jsonl"
                bypass_candidate_path = bypass_predictions_dir / f"{split.name}_candidate.jsonl"
                enabled_candidate_rows = _attach_evaluation_truth(
                    enabled_candidate.rows,
                    records,
                )
                bypass_candidate_rows = _attach_evaluation_truth(
                    bypass_candidate.rows,
                    records,
                )
                enabled_candidate_metrics, _ = _candidate_metrics(
                    records,
                    enabled_candidate.decisions,
                    split,
                    enabled_threshold,
                )
                bypass_candidate_metrics, _ = _candidate_metrics(
                    records,
                    bypass_candidate.decisions,
                    split,
                    bypass_threshold,
                )
                enabled_candidate_summary = {
                    **enabled_candidate.summary,
                    "metrics": enabled_candidate_metrics,
                }
                bypass_candidate_summary = {
                    **bypass_candidate.summary,
                    "metrics": bypass_candidate_metrics,
                }
                _write_jsonl(enabled_candidate_path, enabled_candidate_rows)
                _write_jsonl(bypass_candidate_path, bypass_candidate_rows)
                bypass_files[f"{split.name}_candidate"] = assert_bypass_matches_s3(
                    reference_prediction_dir / f"{split.name}_candidate.jsonl",
                    bypass_candidate_rows,
                    mode="candidate",
                )
                candidate_diagnostics.extend(enabled_candidate.diagnostics)
                maximum_condition_difference = max(
                    maximum_condition_difference,
                    enabled_candidate.candidate_condition_repeat_max_diff,
                )

                if split.calibrates_threshold:
                    enabled_threshold_calibration = calibrate_unknown_threshold(
                        [decision.confidence for decision in enabled_candidate.decisions],
                        settings.max_known_rejection_rate,
                    )
                    bypass_threshold_calibration = calibrate_unknown_threshold(
                        [decision.confidence for decision in bypass_candidate.decisions],
                        settings.max_known_rejection_rate,
                    )
                    _write_json(
                        threshold_path,
                        {
                            "source_split": "subtype_validation",
                            "enabled": asdict(enabled_threshold_calibration),
                            "bypass": asdict(bypass_threshold_calibration),
                        },
                    )
                    progress.log(
                        "evaluation/candidate/calibration/enabled",
                        asdict(enabled_threshold_calibration),
                    )
                    progress.log(
                        "evaluation/candidate/calibration/bypass",
                        asdict(bypass_threshold_calibration),
                    )

                results[split.name] = {
                    "free_generation": enabled_free_summary,
                    "candidate_scoring": enabled_candidate_summary,
                }
                bypass_results[split.name] = {
                    "free_generation": bypass_free_summary,
                    "candidate_scoring": bypass_candidate_summary,
                }
                print(f"评估分区完成：{split.name}", flush=True)

            if enabled_threshold_calibration is None or bypass_threshold_calibration is None:
                raise BoundedPhysicsEvaluationError("评估结束时缺少 subtype_validation 阈值")
            if maximum_condition_difference > CANDIDATE_CONDITION_TOLERANCE:
                raise BoundedPhysicsEvaluationError("候选条件重复差超过固定容差")

            runtime_audit = {
                "schema_version": EVALUATION_SCHEMA_VERSION,
                "training": dict(training_path),
                "generation": aggregate_conditioning_diagnostics(
                    generation_diagnostics,
                    path="generation",
                ),
                "candidate_scoring": aggregate_conditioning_diagnostics(
                    candidate_diagnostics,
                    path="candidate_scoring",
                ),
                "candidate_condition_repeat_max_diff": maximum_condition_difference,
                "candidate_condition_tolerance": CANDIDATE_CONDITION_TOLERANCE,
            }
            bypass_audit = {
                "schema_version": EVALUATION_SCHEMA_VERSION,
                "selected_samples_manifest_identical": True,
                "reference_prediction_file_count": len(required_reference_files),
                "checked_prediction_file_count": len(bypass_files),
                "files": bypass_files,
                "all_equivalent": len(bypass_files) == 12
                and all(bool(item["equivalent"]) for item in bypass_files.values()),
            }
            if not bypass_audit["all_equivalent"]:
                raise BoundedPhysicsEvaluationError("旁路未逐样本恢复全部十二个 S3 预测文件")
            _write_json(runtime_audit_path, runtime_audit)
            _write_json(bypass_audit_path, bypass_audit)

            training_summary = _read_json(variant.training_dir / "training_summary.json")
            _write_json(
                analysis_training_summary_path,
                build_analysis_training_summary(training_summary, physics_test_summary),
            )
            summary = {
                "schema_version": EVALUATION_SCHEMA_VERSION,
                "model_id": probe.model_id,
                "variant": variant.short_name,
                "training_variant": variant.training_variant,
                "training_dir": str(variant.training_dir),
                "adapter_path": str(detection_adapter_path),
                "seed": settings.seed,
                "samples_per_label": settings.samples_per_label,
                "threshold_calibration": asdict(enabled_threshold_calibration),
                "bypass_threshold_calibration": asdict(bypass_threshold_calibration),
                "candidate_condition_repeat_max_diff": maximum_condition_difference,
                "physics_test": physics_test_summary,
                "results": results,
                "bypass_results": bypass_results,
                "runtime_path_audit": runtime_audit,
                "bypass_equivalence": bypass_audit,
            }
            _write_json(summary_path, summary)
            final_metrics = flatten_scalar_metrics(summary, prefix="evaluation/final")
            swanlab.log(final_metrics, step=progress.step)
            _write_json(metrics_path, {"step": progress.step, "metrics": final_metrics})
        finally:
            runtime.close()

    manifest = _read_json(output_dir / "artifact_manifest.json")
    with capture_console_log(output_dir / "console.log"):
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 E1/E2 有界物理条件固定六分区评估")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--variant", choices=("e1", "e2"), required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    (
        probe,
        settings,
        tracking,
        variant,
        detection_adapter,
        s3_evaluation_dir,
        physics_test_file,
    ) = load_fixed_evaluation_configuration(raw, args.variant)
    manifest = run_bounded_physics_evaluation(
        probe,
        settings,
        tracking,
        variant,
        detection_adapter,
        s3_evaluation_dir,
        physics_test_file,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
