"""Qwen3 生成式标签评估与推理效率测量。"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.efficiency import RunTimer
from flow_probe.evaluate import compute_detection_metrics
from flow_probe.output_parser import parse_prediction
from flow_probe.tracking import (
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)


@dataclass(frozen=True)
class GeneratedResult:
    """单条生成及其实际令牌和延迟统计。"""

    text: str
    input_tokens: int
    generated_tokens: int
    latency_ms: float


def evaluation_record_contract(record: Mapping[str, object]) -> tuple[str, str]:
    """从冻结记录中解析真实标签及其严格生成键。"""
    direct_label = record.get("binary_label")
    completion = record.get("completion")
    output_key = "label"
    completion_label = None
    if completion is not None:
        try:
            payload = json.loads(str(completion))
        except json.JSONDecodeError as error:
            raise ValueError(f"completion 不是合法 JSON：{error.msg}") from error
        if not isinstance(payload, dict) or len(payload) != 1:
            raise ValueError("completion 必须是单键 JSON 对象")
        output_key = next(iter(payload))
        if output_key not in {"label", "binary_label"}:
            raise ValueError(f"completion 使用了未知标签键：{output_key!r}")
        completion_label = payload[output_key]

    label = direct_label if direct_label is not None else completion_label
    label = str(label)
    if label not in {"benign", "malicious"}:
        raise ValueError(f"未知真实标签：{label!r}")
    if completion_label is not None and str(completion_label) != label:
        raise ValueError("binary_label 与 completion 标签不一致")
    return label, output_key


def validate_evaluation_records(records: Sequence[Mapping[str, object]]) -> None:
    """在加载模型前验证评测记录的提示与标签合同。"""
    if not records:
        raise ValueError("测试集不能为空")
    for index, record in enumerate(records):
        if not str(record.get("prompt", "")).strip():
            raise ValueError(f"第 {index + 1} 条测试记录缺少 prompt")
        try:
            evaluation_record_contract(record)
        except ValueError as error:
            raise ValueError(f"第 {index + 1} 条测试记录合同非法：{error}") from error


def format_generation_prompt(tokenizer, prompt: str) -> str:
    """使用 Qwen3 官方硬开关关闭思考模式。"""
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("分位数输入不能为空")
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def summarize_generated_results(
    records: Sequence[Mapping[str, object]], generated: Sequence[GeneratedResult]
) -> tuple[dict[str, float | int], list[dict[str, object]]]:
    """合并严格解析、检测指标、令牌数和延迟分位数。"""
    if len(records) != len(generated):
        raise ValueError("记录与生成结果长度必须一致")
    labels = []
    predictions = []
    valid_mask = []
    rows = []
    for record, result in zip(records, generated, strict=True):
        label, output_key = evaluation_record_contract(record)
        parsed = parse_prediction(result.text, label_key=output_key)
        labels.append(label)
        predictions.append(parsed.label)
        valid_mask.append(parsed.is_valid)
        rows.append(
            {
                "sample_id": record.get("sample_id"),
                "true_label": label,
                "generated_text": result.text,
                "parsed_label": parsed.label,
                "is_valid": parsed.is_valid,
                "parse_error": parsed.error,
                "expected_output_key": output_key,
                "input_tokens": result.input_tokens,
                "generated_tokens": result.generated_tokens,
                "latency_ms": result.latency_ms,
            }
        )

    metrics = compute_detection_metrics(labels, predictions, valid_mask)
    latencies = [result.latency_ms for result in generated]
    metrics.update(
        {
            "latency_p50_ms": _percentile(latencies, 0.50),
            "latency_p95_ms": _percentile(latencies, 0.95),
            "input_tokens": sum(result.input_tokens for result in generated),
            "generated_tokens": sum(result.generated_tokens for result in generated),
        }
    )
    return metrics, rows


def _load_records(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def build_evaluation_tracking_config(
    probe: ProbeConfig,
    test_file: Path | str,
    adapter_path: Path | str | None,
) -> dict[str, object]:
    """构造评估阶段的 SwanLab 复现配置。"""
    return {
        "model_id": probe.model_id,
        "feature_view": probe.feature_view,
        "seed": probe.seed,
        "max_input_length": probe.max_input_length,
        "max_new_tokens": probe.max_new_tokens,
        "test_file": str(test_file),
        "adapter_path": str(adapter_path) if adapter_path is not None else None,
        "quantization": "NF4",
        "compute_dtype": "BF16",
        "strict_json": True,
    }


def _evaluate_model_impl(
    probe: ProbeConfig,
    test_file: Path,
    output_dir: Path,
    adapter_path: Path | None = None,
) -> dict[str, object]:
    """在 CUDA 上执行零样本或 LoRA 适配后的生成式评估。"""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝启动大模型评估")
    records = _load_records(test_file)
    validate_evaluation_records(records)

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
    if adapter_path is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter_path))
    model.eval()

    def generate(record: Mapping[str, object]) -> GeneratedResult:
        prompt = format_generation_prompt(tokenizer, str(record["prompt"]))
        inputs = tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=probe.max_input_length
        )
        inputs = inputs.to(model.device)
        input_tokens = int(inputs["input_ids"].shape[-1])
        torch.cuda.synchronize()
        started_at = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(
                **inputs,
                max_new_tokens=probe.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - started_at) * 1000
        new_tokens = output[0, input_tokens:]
        return GeneratedResult(
            text=tokenizer.decode(new_tokens, skip_special_tokens=True),
            input_tokens=input_tokens,
            generated_tokens=int(new_tokens.numel()),
            latency_ms=latency_ms,
        )

    generate(records[0])
    generated = []
    with RunTimer(sample_count=len(records)) as timer:
        for record in records:
            result = generate(record)
            generated.append(result)
            timer.record_tokens(result.input_tokens, result.generated_tokens)
    metrics, rows = summarize_generated_results(records, generated)
    efficiency = timer.summary()
    summary: dict[str, object] = {
        "model_id": probe.model_id,
        "adapter_path": str(adapter_path) if adapter_path is not None else None,
        "seed": probe.seed,
        "metrics": metrics,
        "efficiency": efficiency,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "predictions.jsonl").open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (output_dir / "evaluation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def evaluate_model(
    probe: ProbeConfig,
    test_file: Path,
    output_dir: Path,
    adapter_path: Path | None = None,
    tracking: TrackingSettings | None = None,
) -> dict[str, object]:
    """执行评估，并把检测效果与效率写入 SwanLab。"""
    if tracking is None:
        with capture_console_log(output_dir / "console.log"):
            return _evaluate_model_impl(probe, test_file, output_dir, adapter_path)

    phase = "zero-shot" if adapter_path is None else "evaluation"
    tracking_config = build_evaluation_tracking_config(probe, test_file, adapter_path)
    tracked_metrics_path = output_dir / "swanlab_metrics.json"
    data_files = {
        "evaluation_summary": output_dir / "evaluation_summary.json",
        "predictions": output_dir / "predictions.jsonl",
        "swanlab_metrics": tracked_metrics_path,
        "test_file": test_file,
    }
    if adapter_path is not None:
        data_files["adapter_path"] = adapter_path
    with (
        capture_console_log(output_dir / "console.log"),
        swanlab_run(
            tracking,
            phase=phase,
            config=tracking_config,
            artifact_dir=output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        summary = _evaluate_model_impl(probe, test_file, output_dir, adapter_path)
        tracked_metrics = flatten_scalar_metrics(summary, prefix=phase)
        tracked_metrics_path.write_text(
            json.dumps(tracked_metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        swanlab.log(tracked_metrics)
        return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qwen3-1.7B 恶意流量生成式评估")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--adapter-path", type=Path)
    parser.add_argument("--model-path", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    probe = ProbeConfig.from_mapping(raw["probe"])
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    evaluation = raw["evaluation"]
    tracking = TrackingSettings.from_mapping(raw["tracking"])
    summary = evaluate_model(
        probe=probe,
        test_file=Path(evaluation["test_file"]),
        output_dir=Path(evaluation["output_dir"]),
        adapter_path=args.adapter_path,
        tracking=tracking,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
