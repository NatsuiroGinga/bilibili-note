"""对 M1 与 M2 检查点执行只读的逐样本物理误差诊断。"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import math
import platform
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import torch
import yaml

from flow_probe.physics_train import (
    ContinuousQueueStateHead,
    PhysicsDataError,
    _state_batch,
    prepare_physics_record,
)
from flow_probe.qwen_physics_gradient import select_last_token_hidden
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    swanlab_run,
)

MODEL_LABELS = ("M1", "M2")
RESIDUAL_COMPONENTS = (
    "storage",
    "received",
    "dequeued",
    "dropped_before",
    "dropped_after",
)
SUMMARY_DIMENSIONS = (
    "scenario_id",
    "received_activity",
    "target_queue_activity",
    "capacity_shift",
    "attack_status",
    "group_id",
)


class PhysicsErrorAnalysisError(RuntimeError):
    """诊断输入、检查点或输出制品不满足预注册契约。"""


@dataclass(frozen=True)
class AnalysisLayout:
    """一次诊断运行的完整制品路径。"""

    output_dir: Path
    config_snapshot: Path
    environment: Path
    input_sha256: Path
    sample_metrics: Path
    group_summary: Path
    comparison: Path
    console_log: Path
    artifact_manifest: Path

    @property
    def required_paths(self) -> tuple[Path, ...]:
        return (
            self.config_snapshot,
            self.environment,
            self.input_sha256,
            self.sample_metrics,
            self.group_summary,
            self.comparison,
            self.console_log,
            self.artifact_manifest,
        )


def decompose_queue_balance(
    predicted: torch.Tensor,
    scale: torch.Tensor,
    capacity: torch.Tensor,
    received: torch.Tensor,
    dequeued: torch.Tensor,
    dropped_before: torch.Tensor,
    dropped_after: torch.Tensor,
) -> dict[str, torch.Tensor]:
    """把四窗口队列守恒残差分解为五个有符号组成项。"""
    if predicted.ndim != 2 or predicted.shape[1] != 5:
        raise PhysicsDataError("预测队列必须采用[批量, 5]形状")
    expected = (predicted.shape[0], 4)
    values = (capacity, received, dequeued, dropped_before, dropped_after)
    if any(value.shape != expected for value in values):
        raise PhysicsDataError("容量和四类通量必须采用[批量, 4]形状")
    if scale.shape not in {(predicted.shape[0],), (predicted.shape[0], 1)}:
        raise PhysicsDataError("公共尺度必须按批量提供")
    if not all(torch.isfinite(value).all() for value in (predicted, scale, *values)):
        raise PhysicsDataError("队列、尺度、容量和通量必须全部为有限数")

    predicted_f = predicted.float()
    scale_f = scale.float().reshape(-1, 1)
    capacity_f = capacity.float()
    if torch.any(capacity_f <= 0):
        raise PhysicsDataError("配置容量积分必须严格大于零")
    parts = {
        "storage": scale_f * (predicted_f[:, 1:] - predicted_f[:, :-1]) / capacity_f,
        "received": -received.float() / capacity_f,
        "dequeued": dequeued.float() / capacity_f,
        "dropped_before": dropped_before.float() / capacity_f,
        "dropped_after": dropped_after.float() / capacity_f,
    }
    parts["residual"] = (
        parts["storage"]
        + parts["received"]
        + parts["dequeued"]
        + parts["dropped_before"]
        + parts["dropped_after"]
    )
    return parts


def _numeric_list(value: object, field: str, length: int) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != length:
        raise PhysicsErrorAnalysisError(f"{field} 必须包含 {length} 个数值")
    values = [float(item) for item in value]
    if not all(math.isfinite(item) for item in values):
        raise PhysicsErrorAnalysisError(f"{field} 包含非有限数值")
    return values


def _activity_bin(value: float) -> str:
    if value <= 1e-12:
        return "zero"
    if value <= 0.25:
        return "low"
    if value <= 0.75:
        return "medium"
    return "high"


def classify_physics_regime(record: Mapping[str, object]) -> dict[str, str | int | float]:
    """按场景、攻击、容量变化、接收负载和目标队列水平标记样本。"""
    metadata = record.get("metadata")
    inputs = record.get("model_inputs")
    labels = record.get("label_targets")
    if not isinstance(metadata, Mapping):
        raise PhysicsErrorAnalysisError("样本缺少 metadata")
    if not isinstance(inputs, Mapping):
        raise PhysicsErrorAnalysisError("样本缺少 model_inputs")
    if not isinstance(labels, Mapping):
        raise PhysicsErrorAnalysisError("样本缺少 label_targets")

    scenario_id = str(metadata.get("scenario_id", "")).strip()
    if not scenario_id:
        raise PhysicsErrorAnalysisError("scenario_id 不能为空")
    capacities = _numeric_list(
        inputs.get("configured_capacity_integral_link_bytes"),
        "configured_capacity_integral_link_bytes",
        4,
    )
    if any(value <= 0 for value in capacities):
        raise PhysicsErrorAnalysisError("配置容量积分必须严格大于零")
    received = _numeric_list(inputs.get("qdisc_received_l3_bytes"), "qdisc_received_l3_bytes", 4)
    anchors = _numeric_list(
        record.get("queue_boundary_anchors_l3_bytes"),
        "queue_boundary_anchors_l3_bytes",
        5,
    )
    attack_values = _numeric_list(labels.get("is_attack"), "is_attack", 4)
    if not all(value in {0.0, 1.0} for value in attack_values):
        raise PhysicsErrorAnalysisError("is_attack 只能包含 0 或 1")
    if all(value == 0.0 for value in attack_values):
        is_attack = 0
        attack_status = "benign"
    elif all(value == 1.0 for value in attack_values):
        is_attack = 1
        attack_status = "attack"
    else:
        is_attack = -1
        attack_status = "mixed"

    capacity_shift = int(
        any(
            not math.isclose(value, capacities[0], rel_tol=1e-12, abs_tol=1e-9)
            for value in capacities[1:]
        )
    )
    received_load_ratio = sum(abs(value) for value in received) / sum(capacities)
    target_queue_level_ratio = max(abs(value) for value in anchors) / max(capacities)
    received_activity = _activity_bin(received_load_ratio)
    target_queue_activity = _activity_bin(target_queue_level_ratio)
    group_id = (
        f"scenario={scenario_id}|attack={attack_status}|capacity_shift={capacity_shift}"
        f"|received={received_activity}|queue={target_queue_activity}"
    )
    return {
        "scenario_id": scenario_id,
        "is_attack": is_attack,
        "attack_status": attack_status,
        "capacity_shift": capacity_shift,
        "received_activity": received_activity,
        "received_load_ratio": received_load_ratio,
        "target_queue_activity": target_queue_activity,
        "target_queue_level_ratio": target_queue_level_ratio,
        "group_id": group_id,
    }


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise PhysicsErrorAnalysisError("无法汇总空指标序列")
    return math.fsum(values) / len(values)


def _mean_vectors(rows: Sequence[Mapping[str, object]], field: str, width: int) -> list[float]:
    vectors = [_numeric_list(row.get(field), field, width) for row in rows]
    return [_mean([vector[index] for vector in vectors]) for index in range(width)]


def _aggregate_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not rows:
        raise PhysicsErrorAnalysisError("无法汇总空样本组")
    residual_term_abs_mean = {}
    for name in RESIDUAL_COMPONENTS:
        values: list[float] = []
        for row in rows:
            terms = row.get("residual_terms")
            if not isinstance(terms, Mapping):
                raise PhysicsErrorAnalysisError("逐样本记录缺少 residual_terms")
            values.extend(abs(item) for item in _numeric_list(terms.get(name), name, 4))
        residual_term_abs_mean[name] = _mean(values)
    residuals = [
        value for row in rows for value in _numeric_list(row.get("residuals"), "residuals", 4)
    ]
    return {
        "sample_count": len(rows),
        "state_mse": _mean([float(row["state_mse"]) for row in rows]),
        "anchor_mse": _mean_vectors(rows, "anchor_squared_errors", 5),
        "physics_residual_mse": _mean([float(row["physics_residual_mse"]) for row in rows]),
        "residual_window_mse": _mean_vectors(rows, "residual_squared_errors", 4),
        "residual_abs_mean": _mean([abs(value) for value in residuals]),
        "residual_term_abs_mean": residual_term_abs_mean,
        "truth_residual_abs_max": max(float(row["truth_residual_abs_max"]) for row in rows),
    }


def _group_rows(rows: Sequence[Mapping[str, object]], field: str) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row[field]), []).append(row)
    return {key: _aggregate_rows(grouped[key]) for key in sorted(grouped)}


def summarize_rows(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """分别汇总各模型的总体、场景和五类工况指标。"""
    if not rows:
        raise PhysicsErrorAnalysisError("逐样本记录不能为空")
    models: dict[str, object] = {}
    labels = sorted({str(row.get("model", "")) for row in rows})
    if any(not label for label in labels):
        raise PhysicsErrorAnalysisError("逐样本记录的 model 不能为空")
    for label in labels:
        model_rows = [row for row in rows if str(row["model"]) == label]
        models[label] = {
            "overall": _aggregate_rows(model_rows),
            "scenarios": _group_rows(model_rows, "scenario_id"),
            "received_activity": _group_rows(model_rows, "received_activity"),
            "target_queue_activity": _group_rows(model_rows, "target_queue_activity"),
            "capacity_shift": _group_rows(model_rows, "capacity_shift"),
            "attack_status": _group_rows(model_rows, "attack_status"),
            "regimes": _group_rows(model_rows, "group_id"),
        }
    return {
        "schema_version": "flow_probe_physics_error_group_summary_v1",
        "models": models,
    }


def _summary_delta(m2: Mapping[str, object], m1: Mapping[str, object]) -> dict[str, object]:
    m2_terms = m2["residual_term_abs_mean"]
    m1_terms = m1["residual_term_abs_mean"]
    if not isinstance(m2_terms, Mapping) or not isinstance(m1_terms, Mapping):
        raise PhysicsErrorAnalysisError("分组摘要缺少残差组成项")
    return {
        "sample_count": int(m2["sample_count"]),
        "state_mse_delta_m2_minus_m1": float(m2["state_mse"]) - float(m1["state_mse"]),
        "anchor_mse_delta_m2_minus_m1": [
            right - left
            for right, left in zip(
                _numeric_list(m2["anchor_mse"], "anchor_mse", 5),
                _numeric_list(m1["anchor_mse"], "anchor_mse", 5),
                strict=True,
            )
        ],
        "physics_residual_mse_delta_m2_minus_m1": float(m2["physics_residual_mse"])
        - float(m1["physics_residual_mse"]),
        "residual_window_mse_delta_m2_minus_m1": [
            right - left
            for right, left in zip(
                _numeric_list(m2["residual_window_mse"], "residual_window_mse", 4),
                _numeric_list(m1["residual_window_mse"], "residual_window_mse", 4),
                strict=True,
            )
        ],
        "residual_term_abs_mean_delta_m2_minus_m1": {
            name: float(m2_terms[name]) - float(m1_terms[name]) for name in RESIDUAL_COMPONENTS
        },
    }


def _comparison_groups(
    m1: Mapping[str, object], m2: Mapping[str, object], dimension: str
) -> dict[str, object]:
    left = m1[dimension]
    right = m2[dimension]
    if not isinstance(left, Mapping) or not isinstance(right, Mapping):
        raise PhysicsErrorAnalysisError(f"摘要维度 {dimension} 不是映射")
    if set(left) != set(right):
        raise PhysicsErrorAnalysisError(f"M1 与 M2 的 {dimension} 分组不一致")
    return {
        key: _summary_delta(right[key], left[key])
        for key in sorted(left)
        if isinstance(left[key], Mapping) and isinstance(right[key], Mapping)
    }


def build_comparison(
    rows: Sequence[Mapping[str, object]], summary: Mapping[str, object]
) -> dict[str, object]:
    """生成严格配对的 M2 减 M1 总体与分组比较。"""
    by_model = {
        label: [row for row in rows if str(row["model"]) == label] for label in MODEL_LABELS
    }
    left_ids = [str(row["sample_id"]) for row in by_model["M1"]]
    right_ids = [str(row["sample_id"]) for row in by_model["M2"]]
    if left_ids != right_ids:
        raise PhysicsErrorAnalysisError("M1 与 M2 的样本顺序不一致")
    models = summary.get("models")
    if not isinstance(models, Mapping):
        raise PhysicsErrorAnalysisError("分组摘要缺少 models")
    m1 = models.get("M1")
    m2 = models.get("M2")
    if not isinstance(m1, Mapping) or not isinstance(m2, Mapping):
        raise PhysicsErrorAnalysisError("比较必须同时包含 M1 与 M2")
    m1_overall = m1.get("overall")
    m2_overall = m2.get("overall")
    if not isinstance(m1_overall, Mapping) or not isinstance(m2_overall, Mapping):
        raise PhysicsErrorAnalysisError("模型摘要缺少 overall")

    state_improvements = 0
    residual_improvements = 0
    joint_improvements = 0
    for left, right in zip(by_model["M1"], by_model["M2"], strict=True):
        state_better = float(right["state_mse"]) < float(left["state_mse"])
        residual_better = float(right["physics_residual_mse"]) < float(left["physics_residual_mse"])
        state_improvements += int(state_better)
        residual_improvements += int(residual_better)
        joint_improvements += int(state_better and residual_better)
    return {
        "schema_version": "flow_probe_physics_error_comparison_v1",
        "delta_definition": "M2_minus_M1",
        "paired_sample_count": len(left_ids),
        "sample_order_sha256": _sample_order_sha256(left_ids),
        "overall": {
            **_summary_delta(m2_overall, m1_overall),
            "m2_state_improved_sample_count": state_improvements,
            "m2_physics_improved_sample_count": residual_improvements,
            "m2_joint_improved_sample_count": joint_improvements,
        },
        "scenarios": _comparison_groups(m1, m2, "scenarios"),
        "received_activity": _comparison_groups(m1, m2, "received_activity"),
        "target_queue_activity": _comparison_groups(m1, m2, "target_queue_activity"),
        "capacity_shift": _comparison_groups(m1, m2, "capacity_shift"),
        "attack_status": _comparison_groups(m1, m2, "attack_status"),
        "regimes": _comparison_groups(m1, m2, "regimes"),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _directory_sha256(path: Path) -> tuple[str, int]:
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise PhysicsErrorAnalysisError(f"检查点目录为空：{path}")
    digest = hashlib.sha256()
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256(item).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest(), len(files)


def _sample_order_sha256(sample_ids: Sequence[str]) -> str:
    return hashlib.sha256(("\n".join(sample_ids) + "\n").encode("utf-8")).hexdigest()


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as source:
        rows = [json.loads(line) for line in source if line.strip()]
    if not all(isinstance(row, dict) for row in rows):
        raise PhysicsErrorAnalysisError("诊断数据每行必须是 JSON 对象")
    return rows


def _load_json_mapping(path: Path) -> Mapping[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise PhysicsErrorAnalysisError(f"JSON 根节点必须是映射：{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.write_text(
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
            for name in ("accelerate", "bitsandbytes", "peft", "swanlab", "transformers")
        },
    }


def _verify_run_inputs(
    label: str,
    run_dir: Path,
    *,
    data_sha256: str,
    data_records: int,
) -> dict[str, object]:
    if not run_dir.is_dir():
        raise PhysicsErrorAnalysisError(f"{label} 运行目录不存在：{run_dir}")
    adapter = run_dir / "final_adapter"
    state_head = run_dir / "state_head.pt"
    input_manifest_path = run_dir / "input_sha256.json"
    training_summary_path = run_dir / "training_summary.json"
    for path in (state_head, input_manifest_path, training_summary_path):
        if not path.is_file():
            raise PhysicsErrorAnalysisError(f"{label} 缺少只读制品：{path}")
    if not adapter.is_dir():
        raise PhysicsErrorAnalysisError(f"{label} 缺少 LoRA 适配器：{adapter}")

    input_manifest = _load_json_mapping(input_manifest_path)
    validation = input_manifest.get("physics_validation")
    if not isinstance(validation, Mapping):
        raise PhysicsErrorAnalysisError(f"{label} 输入清单缺少 physics_validation")
    if str(validation.get("sha256", "")) != data_sha256:
        raise PhysicsErrorAnalysisError(f"{label} 物理验证集哈希与诊断输入不一致")
    if int(validation.get("records", -1)) != data_records:
        raise PhysicsErrorAnalysisError(f"{label} 物理验证集记录数与诊断输入不一致")

    training_summary = _load_json_mapping(training_summary_path)
    if training_summary.get("status") != "finished":
        raise PhysicsErrorAnalysisError(f"{label} 训练运行状态不是 finished")
    if str(training_summary.get("variant", "")) != label:
        raise PhysicsErrorAnalysisError(f"{label} 运行目录内的变体标识不匹配")
    adapter_sha256, adapter_files = _directory_sha256(adapter)
    return {
        "path": str(run_dir),
        "input_manifest": {
            "path": str(input_manifest_path),
            "sha256": _sha256(input_manifest_path),
        },
        "training_summary": {
            "path": str(training_summary_path),
            "sha256": _sha256(training_summary_path),
        },
        "final_adapter": {
            "path": str(adapter),
            "tree_sha256": adapter_sha256,
            "file_count": adapter_files,
        },
        "state_head": {
            "path": str(state_head),
            "sha256": _sha256(state_head),
        },
    }


def _validate_inputs(
    data_path: Path,
    run_dirs: Mapping[str, Path],
    *,
    expected_samples: int,
    truth_tolerance: float,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if not data_path.is_file():
        raise PhysicsErrorAnalysisError(f"诊断数据不存在：{data_path}")
    records = _load_jsonl(data_path)
    if len(records) != expected_samples:
        raise PhysicsErrorAnalysisError(
            f"诊断数据必须包含 {expected_samples} 条，实际为 {len(records)} 条"
        )
    sample_ids = [str(record.get("sample_id", "")).strip() for record in records]
    if any(not sample_id for sample_id in sample_ids):
        raise PhysicsErrorAnalysisError("诊断数据包含空 sample_id")
    if len(set(sample_ids)) != len(sample_ids):
        raise PhysicsErrorAnalysisError("诊断数据包含重复 sample_id")

    prepared = [prepare_physics_record(record) for record in records]
    target = torch.tensor([item.state_targets for item in prepared], dtype=torch.float32)
    tensors = {
        name: torch.tensor([getattr(item, name) for item in prepared], dtype=torch.float32)
        for name in (
            "scale",
            "capacity",
            "received",
            "dequeued",
            "dropped_before",
            "dropped_after",
        )
    }
    truth_parts = decompose_queue_balance(target, **tensors)
    truth_max = float(truth_parts["residual"].abs().max().item())
    if truth_max > truth_tolerance:
        raise PhysicsErrorAnalysisError(
            f"真值零残差门禁失败：最大绝对值 {truth_max:.12g} > {truth_tolerance:.12g}"
        )

    data_sha256 = _sha256(data_path)
    run_manifests = {
        label: _verify_run_inputs(
            label,
            run_dirs[label],
            data_sha256=data_sha256,
            data_records=len(records),
        )
        for label in MODEL_LABELS
    }
    return records, {
        "schema_version": "flow_probe_physics_error_inputs_v1",
        "data": {
            "path": str(data_path),
            "sha256": data_sha256,
            "bytes": data_path.stat().st_size,
            "records": len(records),
        },
        "sample_order_sha256": _sample_order_sha256(sample_ids),
        "unique_sample_count": len(set(sample_ids)),
        "truth_residual_abs_max": truth_max,
        "truth_residual_tolerance": truth_tolerance,
        "runs": run_manifests,
    }


def _load_checkpoint(base_model_path: Path, run_dir: Path) -> tuple[object, object, object]:
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise PhysicsErrorAnalysisError("未检测到 CUDA，拒绝启动检查点诊断")
    if not torch.cuda.is_bf16_supported():
        raise PhysicsErrorAnalysisError("当前 GPU 不支持 BF16")
    adapter_path = run_dir / "final_adapter"
    tokenizer = AutoTokenizer.from_pretrained(str(adapter_path), use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    base_model = AutoModelForCausalLM.from_pretrained(
        str(base_model_path),
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        ),
        dtype=torch.bfloat16,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base_model, str(adapter_path), is_trainable=False)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    device = model.get_input_embeddings().weight.device
    state_head = ContinuousQueueStateHead(model.config.hidden_size).to(
        device=device, dtype=torch.bfloat16
    )
    state = torch.load(run_dir / "state_head.pt", map_location="cpu", weights_only=True)
    if not isinstance(state, Mapping):
        raise PhysicsErrorAnalysisError("state_head.pt 必须包含状态字典")
    state_head.load_state_dict(state, strict=True)
    state_head.eval()
    for parameter in state_head.parameters():
        parameter.requires_grad_(False)
    return tokenizer, model, state_head


def _tensor(batch: Mapping[str, object], name: str) -> torch.Tensor:
    value = batch.get(name)
    if not isinstance(value, torch.Tensor):
        raise PhysicsErrorAnalysisError(f"批量字段 {name} 不是张量")
    return value


def _evaluate_checkpoint(
    label: str,
    base_model_path: Path,
    run_dir: Path,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_input_length: int,
) -> list[dict[str, object]]:
    tokenizer, model, state_head = _load_checkpoint(base_model_path, run_dir)
    device = model.get_input_embeddings().weight.device
    rows: list[dict[str, object]] = []
    try:
        with torch.inference_mode():
            for offset in range(0, len(records), batch_size):
                raw_batch = records[offset : offset + batch_size]
                batch = _state_batch(
                    raw_batch,
                    tokenizer,
                    max_input_length,
                    device,
                    include_fluxes=True,
                )
                outputs = model(
                    input_ids=_tensor(batch, "input_ids"),
                    attention_mask=_tensor(batch, "attention_mask"),
                    output_hidden_states=True,
                    return_dict=True,
                )
                hidden = select_last_token_hidden(
                    outputs.hidden_states[-1], _tensor(batch, "attention_mask")
                )
                predicted = state_head(hidden).float()
                target = _tensor(batch, "state_targets").float()
                physics_tensors = {
                    name: _tensor(batch, name).float()
                    for name in (
                        "scale",
                        "capacity",
                        "received",
                        "dequeued",
                        "dropped_before",
                        "dropped_after",
                    )
                }
                parts = decompose_queue_balance(predicted, **physics_tensors)
                truth_parts = decompose_queue_balance(target, **physics_tensors)
                for index, record in enumerate(raw_batch):
                    regime = classify_physics_regime(record)
                    anchor_errors = (predicted[index] - target[index]).square()
                    residual_errors = parts["residual"][index].square()
                    scale = float(physics_tensors["scale"][index].item())
                    rows.append(
                        {
                            "schema_version": "flow_probe_physics_error_sample_v1",
                            "model": label,
                            "sample_index": offset + index,
                            "sample_id": str(record["sample_id"]),
                            "source_group_id": str(record.get("group_id", "")),
                            **regime,
                            "normalization_scale": scale,
                            "target_queue_anchors_normalized": target[index].cpu().tolist(),
                            "predicted_queue_anchors_normalized": predicted[index].cpu().tolist(),
                            "target_queue_anchors_l3_bytes": (target[index] * scale).cpu().tolist(),
                            "predicted_queue_anchors_l3_bytes": (predicted[index] * scale)
                            .cpu()
                            .tolist(),
                            "anchor_squared_errors": anchor_errors.cpu().tolist(),
                            "state_mse": float(anchor_errors.mean().item()),
                            "residual_terms": {
                                name: parts[name][index].cpu().tolist()
                                for name in RESIDUAL_COMPONENTS
                            },
                            "residuals": parts["residual"][index].cpu().tolist(),
                            "residual_squared_errors": residual_errors.cpu().tolist(),
                            "physics_residual_mse": float(residual_errors.mean().item()),
                            "truth_residuals": truth_parts["residual"][index].cpu().tolist(),
                            "truth_residual_abs_max": float(
                                truth_parts["residual"][index].abs().max().item()
                            ),
                        }
                    )
    finally:
        del state_head
        del model
        del tokenizer
        gc.collect()
        torch.cuda.empty_cache()
    return rows


def _create_layout(output_dir: Path) -> AnalysisLayout:
    output_dir.mkdir(parents=True, exist_ok=False)
    return AnalysisLayout(
        output_dir=output_dir,
        config_snapshot=output_dir / "config_snapshot.yaml",
        environment=output_dir / "environment.json",
        input_sha256=output_dir / "input_sha256.json",
        sample_metrics=output_dir / "sample_metrics.jsonl",
        group_summary=output_dir / "group_summary.json",
        comparison=output_dir / "comparison.json",
        console_log=output_dir / "console.log",
        artifact_manifest=output_dir / "artifact_manifest.json",
    )


def _validate_completed_artifacts(layout: AnalysisLayout, expected_rows: int) -> None:
    missing = [str(path) for path in layout.required_paths if not path.exists()]
    if missing:
        raise PhysicsErrorAnalysisError("诊断制品不完整：" + ", ".join(missing))
    empty = [
        str(path) for path in layout.required_paths if path.is_file() and path.stat().st_size == 0
    ]
    if empty:
        raise PhysicsErrorAnalysisError("诊断制品为空：" + ", ".join(empty))
    with layout.sample_metrics.open("r", encoding="utf-8") as source:
        actual_rows = sum(1 for line in source if line.strip())
    if actual_rows != expected_rows:
        raise PhysicsErrorAnalysisError(
            f"逐样本制品应有 {expected_rows} 行，实际为 {actual_rows} 行"
        )
    swanlog = layout.output_dir / "swanlog" / "physics-error-analysis"
    if not swanlog.is_dir() or not any(swanlog.rglob("*")):
        raise PhysicsErrorAnalysisError("SwanLab 原始日志目录缺失或为空")
    manifest = _load_json_mapping(layout.artifact_manifest)
    if manifest.get("status") != "finished" or not str(manifest.get("run_id", "")).strip():
        raise PhysicsErrorAnalysisError("制品清单缺少 finished 状态或 SwanLab 运行编号")


def _tracking_metrics(
    summary: Mapping[str, object], comparison: Mapping[str, object]
) -> dict[str, float | int]:
    models = summary["models"]
    if not isinstance(models, Mapping):
        raise PhysicsErrorAnalysisError("摘要缺少模型指标")
    metrics: dict[str, float | int] = {}
    for label in MODEL_LABELS:
        model = models[label]
        if not isinstance(model, Mapping) or not isinstance(model.get("overall"), Mapping):
            raise PhysicsErrorAnalysisError(f"摘要缺少 {label} 总体指标")
        overall = model["overall"]
        metrics[f"summary/{label.lower()}/sample_count"] = int(overall["sample_count"])
        metrics[f"summary/{label.lower()}/state_mse"] = float(overall["state_mse"])
        metrics[f"summary/{label.lower()}/physics_residual_mse"] = float(
            overall["physics_residual_mse"]
        )
    overall_comparison = comparison.get("overall")
    if not isinstance(overall_comparison, Mapping):
        raise PhysicsErrorAnalysisError("比较结果缺少 overall")
    for name in (
        "state_mse_delta_m2_minus_m1",
        "physics_residual_mse_delta_m2_minus_m1",
        "m2_state_improved_sample_count",
        "m2_physics_improved_sample_count",
        "m2_joint_improved_sample_count",
    ):
        metrics[f"comparison/{name}"] = float(overall_comparison[name])
    return metrics


def run_physics_error_analysis(
    *,
    base_model_path: Path,
    run_dirs: Mapping[str, Path],
    data_path: Path,
    output_dir: Path,
    tracking_mode: str,
    batch_size: int,
    max_input_length: int,
    expected_samples: int,
    truth_tolerance: float,
    limit: int | None = None,
) -> dict[str, object]:
    """执行两个检查点的顺序只读诊断并返回最终制品清单。"""
    if set(run_dirs) != set(MODEL_LABELS):
        raise PhysicsErrorAnalysisError("--run 必须且只能提供 M1 与 M2")
    if not base_model_path.is_absolute() or not base_model_path.is_dir():
        raise PhysicsErrorAnalysisError("基座模型必须是存在的绝对目录")
    if output_dir.exists():
        raise PhysicsErrorAnalysisError(f"输出路径已存在，不得覆盖：{output_dir}")
    if batch_size <= 0 or max_input_length <= 0 or expected_samples <= 0:
        raise PhysicsErrorAnalysisError("批量、最大输入长度和预期样本数必须大于零")
    if truth_tolerance <= 0 or not math.isfinite(truth_tolerance):
        raise PhysicsErrorAnalysisError("真值残差容差必须是有限正数")
    if limit is not None and limit <= 0:
        raise PhysicsErrorAnalysisError("诊断样本上限必须大于零")

    records, input_manifest = _validate_inputs(
        data_path,
        run_dirs,
        expected_samples=expected_samples,
        truth_tolerance=truth_tolerance,
    )
    evaluation_records = records[:limit] if limit is not None else records
    layout = _create_layout(output_dir)
    snapshot = {
        "schema_version": "flow_probe_physics_error_analysis_config_v1",
        "base_model": str(base_model_path),
        "runs": {label: str(run_dirs[label]) for label in MODEL_LABELS},
        "data": str(data_path),
        "output": str(output_dir),
        "tracking_mode": tracking_mode,
        "batch_size": batch_size,
        "max_input_length": max_input_length,
        "expected_samples": expected_samples,
        "evaluated_samples": len(evaluation_records),
        "truth_tolerance": truth_tolerance,
        "read_only": True,
        "optimizer_updates": 0,
        "activity_thresholds": {
            "zero_max": 1e-12,
            "low_max": 0.25,
            "medium_max": 0.75,
            "high_min_exclusive": 0.75,
        },
    }
    layout.config_snapshot.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=True), encoding="utf-8"
    )
    _write_json(layout.environment, _environment_manifest())
    _write_json(layout.input_sha256, input_manifest)
    layout.sample_metrics.touch()
    tracking = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": output_dir.name,
            "description": "M1 与 M2 逐样本物理误差和工况分布诊断",
            "mode": tracking_mode,
            "tags": ["llm-probe", "pinn", "task10", "diagnostic", "seed42"],
        }
    )
    data_files = {
        "config_snapshot": layout.config_snapshot,
        "environment": layout.environment,
        "input_sha256": layout.input_sha256,
        "sample_metrics": layout.sample_metrics,
        "group_summary": layout.group_summary,
        "comparison": layout.comparison,
    }
    started = time.perf_counter()
    all_rows: list[dict[str, object]] = []
    model_orders: dict[str, list[str]] = {}
    torch.cuda.reset_peak_memory_stats()
    with (
        capture_console_log(layout.console_log),
        swanlab_run(
            settings=tracking,
            phase="physics-error-analysis",
            config=snapshot,
            artifact_dir=layout.output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        print(
            json.dumps(
                {
                    "gate": "passed",
                    "records": len(records),
                    "evaluated_records": len(evaluation_records),
                    "sample_order_sha256": input_manifest["sample_order_sha256"],
                    "truth_residual_abs_max": input_manifest["truth_residual_abs_max"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        for step, label in enumerate(MODEL_LABELS, start=1):
            model_rows = _evaluate_checkpoint(
                label,
                base_model_path,
                run_dirs[label],
                evaluation_records,
                batch_size=batch_size,
                max_input_length=max_input_length,
            )
            model_orders[label] = [str(row["sample_id"]) for row in model_rows]
            all_rows.extend(model_rows)
            with layout.sample_metrics.open("a", encoding="utf-8") as target:
                for row in model_rows:
                    target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            partial = _aggregate_rows(model_rows)
            swanlab.log(
                {
                    f"summary/{label.lower()}/state_mse": partial["state_mse"],
                    f"summary/{label.lower()}/physics_residual_mse": partial[
                        "physics_residual_mse"
                    ],
                    f"summary/{label.lower()}/sample_count": partial["sample_count"],
                },
                step=step,
            )
            print(json.dumps({"model": label, **partial}, ensure_ascii=False, sort_keys=True))
        if model_orders["M1"] != model_orders["M2"]:
            raise PhysicsErrorAnalysisError("M1 与 M2 的样本顺序不一致")
        summary = summarize_rows(all_rows)
        comparison = build_comparison(all_rows, summary)
        summary["runtime_seconds"] = time.perf_counter() - started
        summary["peak_gpu_memory_mib"] = torch.cuda.max_memory_allocated() / (1024**2)
        summary["evaluated_sample_count_per_model"] = len(evaluation_records)
        summary["optimizer_updates"] = 0
        _write_json(layout.group_summary, summary)
        _write_json(layout.comparison, comparison)
        swanlab.log(_tracking_metrics(summary, comparison), step=3)
        print(json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True))

    _validate_completed_artifacts(layout, len(evaluation_records) * len(MODEL_LABELS))
    return dict(_load_json_mapping(layout.artifact_manifest))


def _parse_run_specs(values: Sequence[str]) -> dict[str, Path]:
    runs: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise PhysicsErrorAnalysisError("--run 必须采用 M1=路径 或 M2=路径")
        label, raw_path = value.split("=", 1)
        label = label.strip().upper()
        if label not in MODEL_LABELS or label in runs or not raw_path.strip():
            raise PhysicsErrorAnalysisError("--run 必须且只能各提供一次 M1 与 M2")
        runs[label] = Path(raw_path.strip())
    if set(runs) != set(MODEL_LABELS):
        raise PhysicsErrorAnalysisError("--run 必须且只能提供 M1 与 M2")
    return runs


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="诊断 M1 与 M2 的物理误差和样本分布")
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--run", action="append", required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tracking-mode", choices=("online",), default="online")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-input-length", type=int, default=512)
    parser.add_argument("--expected-samples", type=int, default=807)
    parser.add_argument("--truth-tolerance", type=float, default=1e-6)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = run_physics_error_analysis(
        base_model_path=args.base_model,
        run_dirs=_parse_run_specs(args.run),
        data_path=args.data,
        output_dir=args.output,
        tracking_mode=args.tracking_mode,
        batch_size=args.batch_size,
        max_input_length=args.max_input_length,
        expected_samples=args.expected_samples,
        truth_tolerance=args.truth_tolerance,
        limit=args.limit,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
