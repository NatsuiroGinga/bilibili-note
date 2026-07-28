"""分层生成式评估的数据协议与执行入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import sys
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.generative_multiclass import (
    apply_unknown_rejection,
    calibrate_unknown_threshold,
    compute_open_set_metrics,
    normalize_candidate_scores,
    parse_label_prediction,
)
from flow_probe.tracking import (
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)

FAMILY_LABELS = ("benign", "bruteforce", "dos")
SUBTYPE_LABELS = ("benign", "ftp", "smb", "ssh", "hulk", "slowloris")
UNKNOWN_LABEL = "unknown_attack"


@dataclass(frozen=True)
class EvaluationSettings:
    """生成式分层评估所需的数据、批量与拒识设置。"""

    sample_dir: Path
    output_dir: Path
    samples_per_label: int
    generation_batch_size: int
    scoring_batch_size: int
    progress_every_batches: int
    max_known_rejection_rate: float
    seed: int

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> EvaluationSettings:
        required = {
            "sample_dir",
            "output_dir",
            "samples_per_label",
            "generation_batch_size",
            "scoring_batch_size",
            "progress_every_batches",
            "max_known_rejection_rate",
            "seed",
        }
        missing = sorted(required.difference(data))
        if missing:
            raise ValueError(f"缺少评估字段：{', '.join(missing)}")

        samples_per_label = int(data["samples_per_label"])
        generation_batch_size = int(data["generation_batch_size"])
        scoring_batch_size = int(data["scoring_batch_size"])
        progress_every_batches = int(data["progress_every_batches"])
        batch_values = (
            samples_per_label,
            generation_batch_size,
            scoring_batch_size,
            progress_every_batches,
        )
        if any(value <= 0 for value in batch_values):
            raise ValueError("样本数和批量设置必须大于 0")
        max_known_rejection_rate = float(data["max_known_rejection_rate"])
        if not 0 <= max_known_rejection_rate < 1:
            raise ValueError("最大已知类拒识率必须位于 [0, 1)")
        sample_dir = Path(str(data["sample_dir"]))
        output_dir = Path(str(data["output_dir"]))
        if sample_dir == output_dir:
            raise ValueError("样本目录与输出目录不能相同")
        return cls(
            sample_dir=sample_dir,
            output_dir=output_dir,
            samples_per_label=samples_per_label,
            generation_batch_size=generation_batch_size,
            scoring_batch_size=scoring_batch_size,
            progress_every_batches=progress_every_batches,
            max_known_rejection_rate=max_known_rejection_rate,
            seed=int(data["seed"]),
        )


@dataclass(frozen=True)
class EvaluationSplit:
    """一个评估分区及其生成、候选评分标签空间。"""

    name: str
    path: Path
    candidate_labels: tuple[str, ...]
    free_generation_labels: tuple[str, ...]
    calibrates_threshold: bool = False


@dataclass(frozen=True)
class CandidateSequence:
    """提示词与候选完成拼接后的令牌边界。"""

    input_ids: tuple[int, ...]
    completion_start: int

    @property
    def completion_token_ids(self) -> tuple[int, ...]:
        return self.input_ids[self.completion_start :]


@dataclass(frozen=True)
class CandidateDecision:
    """候选完成评分得到的标签、置信度和完整概率。"""

    label: str
    confidence: float
    probabilities: tuple[float, ...]


def build_evaluation_plan(settings: EvaluationSettings) -> tuple[EvaluationSplit, ...]:
    """建立固定分区顺序，并把拒识校准限定在域内子类验证集。"""
    sample_dir = settings.sample_dir
    open_labels = (*SUBTYPE_LABELS, UNKNOWN_LABEL)
    return (
        EvaluationSplit(
            name="family_test",
            path=sample_dir / "family" / "test.jsonl",
            candidate_labels=FAMILY_LABELS,
            free_generation_labels=FAMILY_LABELS,
        ),
        EvaluationSplit(
            name="subtype_validation",
            path=sample_dir / "subtype" / "validation.jsonl",
            candidate_labels=SUBTYPE_LABELS,
            free_generation_labels=SUBTYPE_LABELS,
            calibrates_threshold=True,
        ),
        EvaluationSplit(
            name="subtype_test",
            path=sample_dir / "subtype" / "test.jsonl",
            candidate_labels=SUBTYPE_LABELS,
            free_generation_labels=SUBTYPE_LABELS,
        ),
        EvaluationSplit(
            name="ood_dos_icmp",
            path=sample_dir / "subtype_ood" / "dos-icmp.jsonl",
            candidate_labels=SUBTYPE_LABELS,
            free_generation_labels=open_labels,
        ),
        EvaluationSplit(
            name="ood_dos_pushack",
            path=sample_dir / "subtype_ood" / "dos-pushack.jsonl",
            candidate_labels=SUBTYPE_LABELS,
            free_generation_labels=open_labels,
        ),
        EvaluationSplit(
            name="ood_dos_udp",
            path=sample_dir / "subtype_ood" / "dos-udp.jsonl",
            candidate_labels=SUBTYPE_LABELS,
            free_generation_labels=open_labels,
        ),
    )


def _derived_seed(seed: int, value: str) -> int:
    digest = hashlib.sha256(f"{seed}:{value}".encode()).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def select_stratified_records(
    records: Sequence[Mapping[str, object]],
    labels: Sequence[str],
    per_label: int,
    seed: int,
) -> list[dict[str, object]]:
    """按任务标签确定性抽样，避免探针子集改变类别比例。"""
    selected_labels = tuple(str(label).strip() for label in labels)
    if not selected_labels or any(not label for label in selected_labels):
        raise ValueError("分层标签不能为空")
    if len(set(selected_labels)) != len(selected_labels):
        raise ValueError("分层标签不能重复")
    if per_label <= 0:
        raise ValueError("每类样本数必须大于 0")

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    allowed = set(selected_labels)
    for record in records:
        label = str(record.get("task_label", "")).strip()
        if label not in allowed:
            raise ValueError(f"分层数据包含未知标签：{label!r}")
        grouped[label].append(dict(record))

    selected: list[dict[str, object]] = []
    for label in selected_labels:
        candidates = grouped[label]
        if len(candidates) < per_label:
            raise ValueError(f"标签 {label} 的样本不足：需要 {per_label}，实际 {len(candidates)}")
        random.Random(_derived_seed(seed, label)).shuffle(candidates)
        selected.extend(candidates[:per_label])
    random.Random(_derived_seed(seed, "combined")).shuffle(selected)
    return selected


def build_candidate_completion(label: str) -> str:
    """生成与监督训练完全一致的单键 JSON 候选完成。"""
    value = str(label).strip()
    if not value:
        raise ValueError("候选标签不能为空")
    return json.dumps({"label": value}, ensure_ascii=False, separators=(",", ":"))


def encode_candidate_sequence(
    tokenizer,
    formatted_prompt: str,
    label: str,
    max_length: int,
) -> CandidateSequence:
    """分别编码提示词和候选完成，显式保留条件似然的起点。"""
    if max_length <= 0:
        raise ValueError("最大长度必须大于 0")
    prompt_ids = tuple(
        int(token) for token in tokenizer.encode(formatted_prompt, add_special_tokens=False)
    )
    completion_ids = tuple(
        int(token)
        for token in tokenizer.encode(build_candidate_completion(label), add_special_tokens=False)
    )
    eos_token_id = tokenizer.eos_token_id
    if eos_token_id is None:
        raise ValueError("分词器缺少 EOS 令牌")
    if not prompt_ids or not completion_ids:
        raise ValueError("提示词与候选完成的令牌不能为空")
    input_ids = (*prompt_ids, *completion_ids, int(eos_token_id))
    if len(input_ids) > max_length:
        raise ValueError(f"候选序列超过最大长度：实际 {len(input_ids)}，上限 {max_length}")
    return CandidateSequence(input_ids=input_ids, completion_start=len(prompt_ids))


def decode_candidate_scores(
    flat_scores: Sequence[float], candidate_labels: Sequence[str]
) -> list[CandidateDecision]:
    """把按样本连续排列的候选分数转换为温度 1 的分类决策。"""
    labels = tuple(str(label).strip() for label in candidate_labels)
    if not labels or any(not label for label in labels) or len(set(labels)) != len(labels):
        raise ValueError("候选标签必须非空且不能重复")
    scores = tuple(float(score) for score in flat_scores)
    if not scores or len(scores) % len(labels) != 0:
        raise ValueError("候选分数数量必须能被标签数整除")
    rows = [scores[index : index + len(labels)] for index in range(0, len(scores), len(labels))]
    probabilities = normalize_candidate_scores(rows)
    decisions = []
    for row in probabilities:
        best_index = max(range(len(labels)), key=row.__getitem__)
        decisions.append(
            CandidateDecision(
                label=labels[best_index],
                confidence=row[best_index],
                probabilities=row,
            )
        )
    return decisions


def completion_mean_log_probability(logits, sequence: CandidateSequence) -> float:
    """只聚合完成令牌的移位条件对数概率。"""
    import torch

    if logits.ndim != 2:
        raise ValueError("单条候选输出必须是二维 logits")
    if logits.shape[0] != len(sequence.input_ids):
        raise ValueError("logits 序列长度与候选序列不一致")
    if sequence.completion_start <= 0:
        raise ValueError("候选完成之前必须存在提示词令牌")
    completion_ids = sequence.completion_token_ids
    if not completion_ids:
        raise ValueError("候选完成令牌不能为空")
    if max(completion_ids) >= logits.shape[1] or min(completion_ids) < 0:
        raise ValueError("候选完成令牌超出词表范围")

    positions = torch.arange(
        sequence.completion_start - 1,
        len(sequence.input_ids) - 1,
        device=logits.device,
    )
    targets = torch.tensor(completion_ids, dtype=torch.long, device=logits.device)
    log_probabilities = torch.log_softmax(logits[positions].float(), dim=-1)
    token_log_probabilities = log_probabilities.gather(1, targets.unsqueeze(1)).squeeze(1)
    return float(token_log_probabilities.mean().item())


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _percentile(values: Sequence[float], quantile: float) -> float:
    if not values:
        raise ValueError("延迟分位数输入不能为空")
    if not 0 <= quantile <= 1:
        raise ValueError("分位数必须位于 [0, 1]")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _load_records(path: Path, allowed_labels: Sequence[str]) -> list[dict[str, object]]:
    allowed = set(allowed_labels)
    records = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"评估记录必须是对象：{path}:{line_number}")
            sample_id = str(value.get("sample_id", "")).strip()
            prompt = str(value.get("prompt", "")).strip()
            label = str(value.get("task_label", "")).strip()
            if not sample_id or not prompt:
                raise ValueError(f"评估记录缺少样本标识或提示词：{path}:{line_number}")
            if label not in allowed:
                raise ValueError(f"评估记录含未知任务标签：{path}:{line_number}:{label}")
            records.append(value)
    if not records:
        raise ValueError(f"评估文件不能为空：{path}")
    sample_ids = [str(record["sample_id"]) for record in records]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError(f"评估文件含重复样本标识：{path}")
    return records


def _format_generation_prompt(tokenizer, prompt: str) -> str:
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


class _ProgressLogger:
    """同步记录每个评估批次的控制台、本地 JSONL 和 SwanLab 指标。"""

    def __init__(self, swanlab, path: Path) -> None:
        self.swanlab = swanlab
        self.path = path
        self.step = 0

    def log(self, prefix: str, metrics: Mapping[str, object]) -> None:
        scalar_metrics = flatten_scalar_metrics(metrics, prefix=prefix)
        self.swanlab.log(scalar_metrics, step=self.step)
        record = {"step": self.step, "prefix": prefix, "metrics": scalar_metrics}
        with self.path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        print(json.dumps(record, ensure_ascii=False, sort_keys=True), flush=True)
        self.step += 1


def _load_model_runtime(
    probe: ProbeConfig,
    adapter_path: Path,
    task_adapter_path: Path | None = None,
):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝启动分层生成式评估")
    if not adapter_path.is_dir():
        raise ValueError(f"LoRA 适配器目录不存在：{adapter_path}")
    tokenizer_source = (
        adapter_path if (adapter_path / "tokenizer_config.json").is_file() else probe.model_id
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
    if task_adapter_path is None:
        model = PeftModel.from_pretrained(base_model, str(adapter_path))
    else:
        if not task_adapter_path.is_dir():
            raise ValueError(f"任务私有 LoRA 目录不存在：{task_adapter_path}")
        model = PeftModel.from_pretrained(
            base_model,
            str(adapter_path),
            adapter_name="detection",
            is_trainable=False,
        )
        model.load_adapter(
            str(task_adapter_path),
            adapter_name="physics_private",
            is_trainable=False,
        )
        model.base_model.set_adapter("detection", inference_mode=True)
    model.eval()
    return torch, tokenizer, model


def _set_task_adapter_route(model: object, *, use_private: bool) -> tuple[str, ...]:
    """按评估分区启用冻结检测路径或检测与物理私有路径。"""
    route = ("detection", "physics_private") if use_private else ("detection",)
    model.base_model.set_adapter(list(route) if use_private else route[0], inference_mode=True)
    return route


def _free_generation_metrics(
    records: Sequence[Mapping[str, object]],
    generated_rows: Sequence[Mapping[str, object]],
    split: EvaluationSplit,
) -> dict[str, object]:
    truth = [str(record["task_label"]) for record in records[: len(generated_rows)]]
    predictions = [row.get("parsed_label") for row in generated_rows]
    unknown_label = UNKNOWN_LABEL if UNKNOWN_LABEL in split.free_generation_labels else None
    return compute_open_set_metrics(
        truth=truth,
        predictions=predictions,
        known_labels=split.candidate_labels,
        unknown_label=unknown_label,
    )


def _run_free_generation(
    torch,
    tokenizer,
    model,
    records: Sequence[Mapping[str, object]],
    split: EvaluationSplit,
    settings: EvaluationSettings,
    progress: _ProgressLogger,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    torch.cuda.reset_peak_memory_stats()
    rows: list[dict[str, object]] = []
    input_tokens_total = 0
    generated_tokens_total = 0
    amortized_latencies = []
    started_at = time.perf_counter()
    batch_count = math.ceil(len(records) / settings.generation_batch_size)
    device = next(model.parameters()).device

    for batch_index, start in enumerate(
        range(0, len(records), settings.generation_batch_size), start=1
    ):
        batch_records = records[start : start + settings.generation_batch_size]
        prompts = [
            _format_generation_prompt(tokenizer, str(record["prompt"])) for record in batch_records
        ]
        inputs = tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512,
        ).to(device)
        input_width = int(inputs["input_ids"].shape[1])
        input_counts = [int(value) for value in inputs["attention_mask"].sum(dim=1).tolist()]
        torch.cuda.synchronize()
        batch_started_at = time.perf_counter()
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=16,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        torch.cuda.synchronize()
        batch_seconds = time.perf_counter() - batch_started_at
        new_token_rows = outputs[:, input_width:]
        per_sample_latency_ms = batch_seconds * 1000 / len(batch_records)

        for record, input_count, new_tokens in zip(
            batch_records, input_counts, new_token_rows, strict=True
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
                    "sample_id": record["sample_id"],
                    "true_label": record["task_label"],
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

        should_log = (
            batch_index % settings.progress_every_batches == 0 or batch_index == batch_count
        )
        if should_log:
            elapsed = time.perf_counter() - started_at
            metrics = _free_generation_metrics(records, rows, split)
            metrics["progress"] = {
                "processed_samples": len(rows),
                "total_samples": len(records),
                "samples_per_second": len(rows) / elapsed,
                "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            }
            progress.log(f"evaluation/free/{split.name}", metrics)

    total_seconds = time.perf_counter() - started_at
    metrics = _free_generation_metrics(records, rows, split)
    return (
        {
            "metrics": metrics,
            "efficiency": {
                "total_seconds": total_seconds,
                "samples_per_second": len(records) / total_seconds,
                "input_tokens": input_tokens_total,
                "generated_tokens": generated_tokens_total,
                "amortized_latency_p50_ms": _percentile(amortized_latencies, 0.50),
                "amortized_latency_p95_ms": _percentile(amortized_latencies, 0.95),
                "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            },
        },
        rows,
    )


def _candidate_metrics(
    records: Sequence[Mapping[str, object]],
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
        truth=[str(record["task_label"]) for record in records[: len(decisions)]],
        predictions=predictions,
        known_labels=split.candidate_labels,
        unknown_label=unknown_label,
    )
    return metrics, predictions


def _run_candidate_scoring(
    torch,
    tokenizer,
    model,
    records: Sequence[Mapping[str, object]],
    split: EvaluationSplit,
    settings: EvaluationSettings,
    progress: _ProgressLogger,
    threshold: float | None,
) -> tuple[dict[str, object], list[dict[str, object]], list[CandidateDecision]]:
    label_count = len(split.candidate_labels)
    records_per_batch = settings.scoring_batch_size // label_count
    if records_per_batch <= 0:
        raise ValueError("候选评分批量必须不少于当前任务的候选标签数")
    torch.cuda.reset_peak_memory_stats()
    device = next(model.parameters()).device
    pad_token_id = int(tokenizer.pad_token_id)
    all_scores: list[float] = []
    all_decisions: list[CandidateDecision] = []
    all_rows: list[dict[str, object]] = []
    candidate_tokens = 0
    started_at = time.perf_counter()
    batch_count = math.ceil(len(records) / records_per_batch)

    for batch_index, start in enumerate(range(0, len(records), records_per_batch), start=1):
        batch_records = records[start : start + records_per_batch]
        sequences = []
        for record in batch_records:
            formatted_prompt = _format_generation_prompt(tokenizer, str(record["prompt"]))
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
        for row_index, sequence in enumerate(sequences):
            length = len(sequence.input_ids)
            input_ids[row_index, :length] = torch.tensor(
                sequence.input_ids, dtype=torch.long, device=device
            )
            attention_mask[row_index, :length] = 1
            candidate_tokens += length
        torch.cuda.synchronize()
        with torch.inference_mode():
            logits = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_cache=False,
            ).logits
        torch.cuda.synchronize()
        batch_scores = [
            completion_mean_log_probability(logits[index, : len(sequence.input_ids)], sequence)
            for index, sequence in enumerate(sequences)
        ]
        all_scores.extend(batch_scores)
        batch_decisions = decode_candidate_scores(batch_scores, split.candidate_labels)
        all_decisions.extend(batch_decisions)

        should_log = (
            batch_index % settings.progress_every_batches == 0 or batch_index == batch_count
        )
        if should_log:
            elapsed = time.perf_counter() - started_at
            metrics, _ = _candidate_metrics(
                records=records,
                decisions=all_decisions,
                split=split,
                threshold=threshold,
            )
            metrics["progress"] = {
                "processed_samples": len(all_decisions),
                "total_samples": len(records),
                "samples_per_second": len(all_decisions) / elapsed,
                "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            }
            progress.log(f"evaluation/candidate/{split.name}", metrics)

    total_seconds = time.perf_counter() - started_at
    metrics, predictions = _candidate_metrics(
        records=records,
        decisions=all_decisions,
        split=split,
        threshold=threshold,
    )
    width = len(split.candidate_labels)
    for index, (record, decision, prediction) in enumerate(
        zip(records, all_decisions, predictions, strict=True)
    ):
        score_row = all_scores[index * width : (index + 1) * width]
        all_rows.append(
            {
                "sample_id": record["sample_id"],
                "true_label": record["task_label"],
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
        )
    return (
        {
            "metrics": metrics,
            "efficiency": {
                "total_seconds": total_seconds,
                "samples_per_second": len(records) / total_seconds,
                "candidate_sequences": len(all_scores),
                "candidate_tokens": candidate_tokens,
                "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            },
        },
        all_rows,
        all_decisions,
    )


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run_hierarchical_evaluation(
    probe: ProbeConfig,
    settings: EvaluationSettings,
    adapter_path: Path,
    tracking: TrackingSettings,
    task_adapter_path: Path | None = None,
) -> dict[str, object]:
    """执行自由生成、候选完成评分与仅由域内验证集校准的开放集评估。"""
    import torch
    import transformers

    if settings.output_dir.exists():
        raise ValueError(f"评估输出目录已存在，拒绝复用：{settings.output_dir}")
    plan = build_evaluation_plan(settings)
    missing = [str(split.path) for split in plan if not split.path.is_file()]
    if missing:
        raise ValueError(f"评估数据文件缺失：{', '.join(missing)}")

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

    output_dir = settings.output_dir
    predictions_dir = output_dir / "predictions"
    summary_path = output_dir / "evaluation_summary.json"
    metrics_path = output_dir / "swanlab_metrics.json"
    history_path = output_dir / "metric_history.jsonl"
    threshold_path = output_dir / "threshold_calibration.json"
    config_path = output_dir / "config_snapshot.json"
    environment_path = output_dir / "environment.json"
    selected_manifest_path = output_dir / "selected_samples_manifest.json"
    config_snapshot = {
        "probe": {
            "model_id": probe.model_id,
            "feature_view": probe.feature_view,
            "seed": probe.seed,
            "max_input_length": probe.max_input_length,
            "max_new_tokens": probe.max_new_tokens,
        },
        "evaluation": {
            **asdict(settings),
            "sample_dir": str(settings.sample_dir),
            "output_dir": str(settings.output_dir),
        },
        "adapter_path": str(adapter_path),
        "task_adapter_path": str(task_adapter_path) if task_adapter_path is not None else None,
        "protocol": {
            "candidate_temperature": 1.0,
            "threshold_source": "subtype_validation_only",
            "threshold_comparator": "confidence < threshold",
            "candidate_score": "mean_completion_token_log_probability_with_eos",
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
        "predictions": predictions_dir,
        "adapter": adapter_path,
    }
    if task_adapter_path is not None:
        data_files["task_adapter"] = task_adapter_path

    with (
        capture_console_log(output_dir / "console.log"),
        swanlab_run(
            settings=tracking,
            phase="hierarchical-generative-evaluation",
            config=config_snapshot,
            artifact_dir=output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        predictions_dir.mkdir(parents=True, exist_ok=False)
        config_path.write_text(
            json.dumps(config_snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        selected_manifest_path.write_text(
            json.dumps(selected_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        environment_path.write_text(
            json.dumps(
                {
                    "python": sys.version,
                    "platform": platform.platform(),
                    "torch": torch.__version__,
                    "transformers": transformers.__version__,
                    "cuda": torch.version.cuda,
                    "gpu": torch.cuda.get_device_name(0),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        progress = _ProgressLogger(swanlab, history_path)
        runtime_torch, tokenizer, model = _load_model_runtime(
            probe, adapter_path, task_adapter_path
        )
        results: dict[str, object] = {}
        routes: dict[str, list[str]] = {}
        threshold_calibration = None

        for split in plan:
            if task_adapter_path is not None:
                route = _set_task_adapter_route(model, use_private=split.name != "family_test")
                routes[split.name] = list(route)
            records = selected_records[split.name]
            print(
                f"评估分区开始：{split.name}，样本数={len(records)}",
                flush=True,
            )
            free_summary, free_rows = _run_free_generation(
                runtime_torch,
                tokenizer,
                model,
                records,
                split,
                settings,
                progress,
            )
            _write_jsonl(predictions_dir / f"{split.name}_free.jsonl", free_rows)

            threshold = None
            if split.name not in {"family_test", "subtype_validation"}:
                if threshold_calibration is None:
                    raise AssertionError("子类测试开始前尚未完成验证集阈值校准")
                threshold = threshold_calibration.threshold
            candidate_summary, candidate_rows, decisions = _run_candidate_scoring(
                runtime_torch,
                tokenizer,
                model,
                records,
                split,
                settings,
                progress,
                threshold=threshold,
            )
            _write_jsonl(predictions_dir / f"{split.name}_candidate.jsonl", candidate_rows)
            if split.calibrates_threshold:
                threshold_calibration = calibrate_unknown_threshold(
                    [decision.confidence for decision in decisions],
                    settings.max_known_rejection_rate,
                )
                threshold_path.write_text(
                    json.dumps(
                        asdict(threshold_calibration),
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                progress.log(
                    "evaluation/candidate/calibration",
                    asdict(threshold_calibration),
                )
            results[split.name] = {
                "free_generation": free_summary,
                "candidate_scoring": candidate_summary,
            }
            print(f"评估分区完成：{split.name}", flush=True)

        if threshold_calibration is None:
            raise AssertionError("评估结束时缺少验证集阈值")
        summary = {
            "schema_version": "flow_probe_hierarchical_generative_evaluation_v1",
            "model_id": probe.model_id,
            "adapter_path": str(adapter_path),
            "task_adapter_path": (
                str(task_adapter_path) if task_adapter_path is not None else None
            ),
            "adapter_routes": routes,
            "seed": settings.seed,
            "samples_per_label": settings.samples_per_label,
            "threshold_calibration": asdict(threshold_calibration),
            "results": results,
        }
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        final_metrics = flatten_scalar_metrics(summary, prefix="evaluation/final")
        swanlab.log(final_metrics, step=progress.step)
        metrics_path.write_text(
            json.dumps(
                {"step": progress.step, "metrics": final_metrics},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    manifest = json.loads((output_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    with capture_console_log(output_dir / "console.log"):
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qwen 分层多分类与开放集生成式评估")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--adapter-path", type=Path, required=True)
    parser.add_argument("--task-adapter-path", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    probe = ProbeConfig.from_mapping(raw["probe"])
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = EvaluationSettings.from_mapping(raw["evaluation"])
    tracking = TrackingSettings.from_mapping(raw["tracking"])
    run_hierarchical_evaluation(
        probe=probe,
        settings=settings,
        adapter_path=args.adapter_path,
        tracking=tracking,
        task_adapter_path=args.task_adapter_path,
    )
