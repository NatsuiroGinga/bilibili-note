"""Qwen3 生成式标签评估、断点续评与推理效率测量。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TypeVar

import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.evaluate import compute_detection_metrics
from flow_probe.output_parser import parse_prediction
from flow_probe.tracking import (
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)

_EVALUATION_BINDING_SCHEMA_VERSION = "qwen_evaluation_binding_v1"
_EVALUATION_PROGRESS_SCHEMA_VERSION = "qwen_evaluation_progress_v1"
_ATTENTION_BACKENDS = frozenset({"auto", "sdpa", "flash_attention_2"})
_JOURNAL_FIELDS = frozenset(
    {
        "_journal_batch",
        "_journal_batch_size",
        "_journal_batch_elapsed_seconds",
        "_journal_batch_peak_gpu_memory_bytes",
    }
)
_ResultT = TypeVar("_ResultT")


@dataclass(frozen=True)
class EvaluationSettings:
    """不改变科学协议的评测运行参数。"""

    batch_size: int = 1
    length_bucket: bool = False
    flush_every_batches: int = 1
    resume: bool = False
    attention_backend: str = "auto"


@dataclass(frozen=True)
class GeneratedResult:
    """单条生成及其实际令牌和延迟统计。"""

    text: str
    input_tokens: int
    generated_tokens: int
    latency_ms: float


def _positive_integer(data: Mapping[str, object], field: str, default: int) -> int:
    value = data.get(field, default)
    if type(value) is not int or value <= 0:
        raise ValueError(f"{field} 必须是正整数")
    return value


def _strict_boolean(data: Mapping[str, object], field: str, default: bool) -> bool:
    value = data.get(field, default)
    if type(value) is not bool:
        raise ValueError(f"{field} 必须是布尔值")
    return value


def _validate_attention_backend(value: object) -> str:
    if not isinstance(value, str) or value not in _ATTENTION_BACKENDS:
        allowed = "、".join(sorted(_ATTENTION_BACKENDS))
        raise ValueError(f"attention_backend 只允许 {allowed}")
    return value


def build_evaluation_settings(data: Mapping[str, object]) -> EvaluationSettings:
    """解析并严格校验评测运行参数。"""
    return EvaluationSettings(
        batch_size=_positive_integer(data, "batch_size", 1),
        length_bucket=_strict_boolean(data, "length_bucket", False),
        flush_every_batches=_positive_integer(data, "flush_every_batches", 1),
        resume=_strict_boolean(data, "resume", False),
        attention_backend=_validate_attention_backend(data.get("attention_backend", "auto")),
    )


def plan_length_bucketed_batches(
    lengths: Sequence[int],
    batch_size: int,
    enabled: bool,
) -> tuple[tuple[int, ...], ...]:
    """确定性规划批次，并用原始索引表示每个样本。"""
    if type(batch_size) is not int or batch_size <= 0:
        raise ValueError("batch_size 必须是正整数")
    if type(enabled) is not bool:
        raise ValueError("enabled 必须是布尔值")
    for length in lengths:
        if type(length) is not int or length < 0:
            raise ValueError("输入长度必须是非负整数")
    indices = list(range(len(lengths)))
    if enabled:
        indices.sort(key=lambda index: (lengths[index], index))
    return tuple(
        tuple(indices[start : start + batch_size]) for start in range(0, len(indices), batch_size)
    )


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


def _record_sample_ids(records: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    sample_ids: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        sample_id = record.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError(f"第 {index + 1} 条测试记录缺少非空 sample_id")
        if sample_id in seen:
            raise ValueError(f"测试记录包含重复 sample_id：{sample_id}")
        sample_ids.append(sample_id)
        seen.add(sample_id)
    return tuple(sample_ids)


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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def evaluation_binding_sha256(binding: Mapping[str, object]) -> str:
    """计算与键顺序无关的评测绑定摘要。"""
    return hashlib.sha256(_canonical_json_bytes(dict(binding))).hexdigest()


def build_evaluation_binding(
    probe: ProbeConfig,
    settings: EvaluationSettings,
    test_file: Path | str,
    records: Sequence[Mapping[str, object]],
    adapter_path: Path | str | None,
) -> dict[str, object]:
    """绑定恢复评测时不得变化的数据、模型、标签与运行参数。"""
    validate_evaluation_records(records)
    sample_ids = _record_sample_ids(records)
    label_contract = []
    for sample_id, record in zip(sample_ids, records, strict=True):
        label, output_key = evaluation_record_contract(record)
        label_contract.append(
            {"sample_id": sample_id, "true_label": label, "output_key": output_key}
        )
    resolved_test_file = Path(test_file).expanduser().resolve()
    resolved_adapter = (
        str(Path(adapter_path).expanduser().resolve()) if adapter_path is not None else None
    )
    return {
        "schema_version": _EVALUATION_BINDING_SCHEMA_VERSION,
        "test_file": str(resolved_test_file),
        "test_file_sha256": _sha256_file(resolved_test_file),
        "record_count": len(records),
        "sample_order_sha256": hashlib.sha256(_canonical_json_bytes(sample_ids)).hexdigest(),
        "label_contract_sha256": hashlib.sha256(_canonical_json_bytes(label_contract)).hexdigest(),
        "model_id": probe.model_id,
        "adapter_path": resolved_adapter,
        "feature_view": probe.feature_view,
        "seed": probe.seed,
        "max_input_length": probe.max_input_length,
        "max_new_tokens": probe.max_new_tokens,
        "evaluation_settings": asdict(settings),
        "evaluation_code_sha256": _sha256_file(Path(__file__)),
    }


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary_path.open("x", encoding="utf-8", newline="\n") as target:
            json.dump(
                value,
                target,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _atomic_write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary_path.open("x", encoding="utf-8", newline="\n") as target:
            for row in rows:
                target.write(
                    json.dumps(
                        dict(row),
                        ensure_ascii=False,
                        sort_keys=True,
                        allow_nan=False,
                    )
                    + "\n"
                )
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"无法读取合法 JSON：{path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def _binding_differences(stored: Mapping[str, object], expected: Mapping[str, object]) -> list[str]:
    keys = sorted(set(stored) | set(expected))
    return [key for key in keys if stored.get(key) != expected.get(key)]


class EvaluationJournal:
    """以部分预测为事实来源，逐批持久化并支持严格恢复。"""

    def __init__(
        self,
        output_dir: Path | str,
        binding: Mapping[str, object],
        records: Sequence[Mapping[str, object]],
        *,
        resume: bool,
        flush_every_batches: int | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.binding = dict(binding)
        self.binding_sha256 = evaluation_binding_sha256(binding)
        self.records = tuple(records)
        self.sample_ids = _record_sample_ids(records)
        runtime = binding.get("evaluation_settings")
        if not isinstance(runtime, dict):
            raise ValueError("评测绑定缺少 evaluation_settings")
        self.batch_size = _positive_integer(runtime, "batch_size", 1)
        configured_flush = _positive_integer(runtime, "flush_every_batches", 1)
        self.flush_every_batches = (
            configured_flush
            if flush_every_batches is None
            else _positive_integer(
                {"flush_every_batches": flush_every_batches},
                "flush_every_batches",
                configured_flush,
            )
        )
        self.total_batches = math.ceil(len(records) / self.batch_size)
        self.binding_path = self.output_dir / "evaluation_binding.json"
        self.partial_path = self.output_dir / "predictions.partial.jsonl"
        self.progress_path = self.output_dir / "evaluation_progress.json"
        self.final_path = self.output_dir / "predictions.jsonl"
        self._rows_by_index: dict[int, dict[str, object]] = {}
        self._batch_runtime: dict[int, tuple[float, int]] = {}

        self.output_dir.mkdir(parents=True, exist_ok=True)
        artifacts_exist = self.binding_path.exists() or self.partial_path.exists()
        if resume and artifacts_exist:
            self._restore()
        else:
            self._initialize_fresh()
        self._write_progress("running" if self._rows_by_index else "prepared")

    @property
    def pending_indices(self) -> tuple[int, ...]:
        return tuple(
            index for index in range(len(self.records)) if index not in self._rows_by_index
        )

    @property
    def elapsed_seconds(self) -> float:
        return sum(runtime[0] for runtime in self._batch_runtime.values())

    @property
    def peak_gpu_memory_bytes(self) -> int:
        return max((runtime[1] for runtime in self._batch_runtime.values()), default=0)

    def _initialize_fresh(self) -> None:
        for path in (
            self.binding_path,
            self.partial_path,
            self.progress_path,
            self.final_path,
            self.output_dir / "evaluation_summary.json",
        ):
            path.unlink(missing_ok=True)
        _atomic_write_json(self.binding_path, self.binding)
        with self.partial_path.open("w", encoding="utf-8", newline="\n") as target:
            target.flush()
            os.fsync(target.fileno())

    def _restore(self) -> None:
        if not self.binding_path.is_file():
            raise ValueError("已有部分预测但缺少 evaluation_binding.json")
        if not self.partial_path.is_file():
            raise ValueError("已有评测绑定但缺少 predictions.partial.jsonl")
        stored_binding = _read_json_object(self.binding_path)
        differences = _binding_differences(stored_binding, self.binding)
        if differences:
            raise ValueError(f"评测绑定不一致：{', '.join(differences)}")
        parsed_rows, has_unterminated_tail = self._read_complete_partial_rows()
        committed_rows, needs_truncation = self._committed_partial_rows(parsed_rows)
        for line_number, row in committed_rows:
            self._register_restored_row(row, line_number)
        if has_unterminated_tail or needs_truncation:
            _atomic_write_jsonl(self.partial_path, [row for _, row in committed_rows])

    def _read_complete_partial_rows(self) -> tuple[list[tuple[int, dict[str, object]]], bool]:
        try:
            content = self.partial_path.read_bytes()
        except OSError as error:
            raise ValueError("无法读取部分预测日志") from error
        final_newline = content.rfind(b"\n")
        if final_newline < 0:
            complete_content = b""
            has_unterminated_tail = bool(content)
        else:
            complete_content = content[: final_newline + 1]
            has_unterminated_tail = final_newline != len(content) - 1
        try:
            lines = complete_content.decode("utf-8").splitlines()
        except UnicodeDecodeError as error:
            raise ValueError("部分预测已提交区域不是合法 UTF-8") from error

        parsed_rows: list[tuple[int, dict[str, object]]] = []
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"部分预测第 {line_number} 行损坏") from error
            if not isinstance(row, dict):
                raise ValueError(f"部分预测第 {line_number} 行不是对象")
            parsed_rows.append((line_number, row))
        return parsed_rows, has_unterminated_tail

    def _committed_partial_rows(
        self,
        parsed_rows: Sequence[tuple[int, dict[str, object]]],
    ) -> tuple[list[tuple[int, dict[str, object]]], bool]:
        groups: list[list[tuple[int, dict[str, object]]]] = []
        expected_sizes: list[int] = []
        for line_number, row in parsed_rows:
            batch_number = row.get("_journal_batch")
            batch_size = row.get("_journal_batch_size")
            if type(batch_number) is not int or batch_number <= 0:
                raise ValueError(f"部分预测第 {line_number} 行缺少批次元数据")
            if type(batch_size) is not int or not 0 < batch_size <= self.batch_size:
                raise ValueError(f"部分预测第 {line_number} 行批次大小非法")
            if not groups or batch_number != len(groups):
                if groups and len(groups[-1]) != expected_sizes[-1]:
                    raise ValueError("部分预测包含非尾部的不完整批次")
                expected_batch_number = len(groups) + 1
                if batch_number != expected_batch_number:
                    raise ValueError(f"部分预测第 {line_number} 行批次编号不连续")
                groups.append([])
                expected_sizes.append(batch_size)
            elif batch_size != expected_sizes[-1]:
                raise ValueError(f"部分预测第 {line_number} 行批次大小不一致")
            groups[-1].append((line_number, row))
            if len(groups[-1]) > expected_sizes[-1]:
                raise ValueError(f"部分预测第 {line_number} 行批次行数超出声明")

        needs_truncation = bool(groups and len(groups[-1]) < expected_sizes[-1])
        if needs_truncation:
            groups.pop()
        committed_rows = [item for group in groups for item in group]
        return committed_rows, needs_truncation

    def _validate_prediction_semantics(
        self,
        row: Mapping[str, object],
        *,
        location: str,
        output_key: str,
    ) -> None:
        required_fields = (
            "generated_text",
            "parsed_label",
            "is_valid",
            "parse_error",
            "input_tokens",
            "generated_tokens",
            "latency_ms",
        )
        for field in required_fields:
            if field not in row:
                raise ValueError(f"{location} 缺少 {field}")

        generated_text = row["generated_text"]
        if not isinstance(generated_text, str):
            raise ValueError(f"{location} generated_text 类型非法")
        parsed_label = row["parsed_label"]
        if parsed_label is not None and (
            not isinstance(parsed_label, str) or parsed_label not in {"benign", "malicious"}
        ):
            raise ValueError(f"{location} parsed_label 非法")
        is_valid = row["is_valid"]
        if type(is_valid) is not bool:
            raise ValueError(f"{location} is_valid 类型非法")
        parse_error = row["parse_error"]
        if parse_error is not None and not isinstance(parse_error, str):
            raise ValueError(f"{location} parse_error 类型非法")
        for field in ("input_tokens", "generated_tokens"):
            value = row[field]
            if type(value) is not int or value < 0:
                raise ValueError(f"{location} {field} 必须是非负整数")
        latency_ms = row["latency_ms"]
        if (
            not isinstance(latency_ms, (int, float))
            or isinstance(latency_ms, bool)
            or not math.isfinite(latency_ms)
            or latency_ms < 0
        ):
            raise ValueError(f"{location} latency_ms 必须是有限非负数")

        reparsed = parse_prediction(generated_text, label_key=output_key)
        if reparsed.label != parsed_label:
            raise ValueError(f"{location} parsed_label 与 generated_text 不一致")
        if reparsed.is_valid is not is_valid:
            raise ValueError(f"{location} is_valid 与 generated_text 不一致")
        if reparsed.error != parse_error:
            raise ValueError(f"{location} parse_error 与 generated_text 不一致")

    def _register_restored_row(self, row: dict[str, object], line_number: int) -> None:
        index = row.get("record_index")
        if type(index) is not int or not 0 <= index < len(self.records):
            raise ValueError(f"部分预测第 {line_number} 行 record_index 非法")
        sample_id = row.get("sample_id")
        if sample_id != self.sample_ids[index]:
            raise ValueError(f"部分预测第 {line_number} 行 sample_id 与冻结顺序不一致")
        if index in self._rows_by_index:
            raise ValueError(f"部分预测包含重复 record_index：{index}")
        if any(existing.get("sample_id") == sample_id for existing in self._rows_by_index.values()):
            raise ValueError(f"部分预测包含重复 sample_id：{sample_id}")
        label, output_key = evaluation_record_contract(self.records[index])
        if row.get("true_label") != label or row.get("expected_output_key") != output_key:
            raise ValueError(f"部分预测第 {line_number} 行标签合同不一致")
        self._validate_prediction_semantics(
            row,
            location=f"部分预测第 {line_number} 行",
            output_key=output_key,
        )
        batch_number = row.get("_journal_batch")
        batch_size = row.get("_journal_batch_size")
        elapsed = row.get("_journal_batch_elapsed_seconds")
        peak = row.get("_journal_batch_peak_gpu_memory_bytes")
        if type(batch_number) is not int or batch_number <= 0:
            raise ValueError(f"部分预测第 {line_number} 行缺少批次元数据")
        if type(batch_size) is not int or not 0 < batch_size <= self.batch_size:
            raise ValueError(f"部分预测第 {line_number} 行批次大小非法")
        if (
            not isinstance(elapsed, (int, float))
            or isinstance(elapsed, bool)
            or not math.isfinite(elapsed)
            or elapsed < 0
        ):
            raise ValueError(f"部分预测第 {line_number} 行批次耗时非法")
        if type(peak) is not int or peak < 0:
            raise ValueError(f"部分预测第 {line_number} 行峰值显存非法")
        runtime = (float(elapsed), peak)
        previous_runtime = self._batch_runtime.get(batch_number)
        if previous_runtime is not None and previous_runtime != runtime:
            raise ValueError(f"部分预测第 {line_number} 行批次元数据不一致")
        self._batch_runtime[batch_number] = runtime
        self._rows_by_index[index] = row

    def _progress(self, status: str) -> dict[str, object]:
        completed = len(self._rows_by_index)
        elapsed = self.elapsed_seconds
        throughput = completed / elapsed if elapsed > 0 else 0.0
        remaining = len(self.records) - completed
        eta = remaining / throughput if throughput > 0 else 0.0
        latest_batch_peak = (
            self._batch_runtime[max(self._batch_runtime)][1] if self._batch_runtime else 0
        )
        return {
            "schema_version": _EVALUATION_PROGRESS_SCHEMA_VERSION,
            "binding_sha256": self.binding_sha256,
            "status": status,
            "completed_samples": completed,
            "total_samples": len(self.records),
            "completed_batches": len(self._batch_runtime),
            "total_batches": self.total_batches,
            "samples_per_second": throughput,
            "elapsed_seconds": elapsed,
            "eta_seconds": eta,
            "gpu_peak_mib": self.peak_gpu_memory_bytes / (1024 * 1024),
            "batch_gpu_peak_mib": latest_batch_peak / (1024 * 1024),
        }

    def _write_progress(self, status: str) -> dict[str, object]:
        progress = self._progress(status)
        _atomic_write_json(self.progress_path, progress)
        return progress

    def append_batch(
        self,
        rows: Sequence[Mapping[str, object]],
        *,
        batch_elapsed_seconds: float,
        batch_peak_gpu_memory_bytes: int,
    ) -> dict[str, object]:
        """一次追加完整批次；部分预测先于进度落盘。"""
        if not rows:
            raise ValueError("不能追加空批次")
        if (
            not isinstance(batch_elapsed_seconds, (int, float))
            or isinstance(batch_elapsed_seconds, bool)
            or not math.isfinite(batch_elapsed_seconds)
            or batch_elapsed_seconds < 0
        ):
            raise ValueError("批次耗时必须是非负数")
        if type(batch_peak_gpu_memory_bytes) is not int or batch_peak_gpu_memory_bytes < 0:
            raise ValueError("批次峰值显存必须是非负整数")
        batch_number = max(self._batch_runtime, default=0) + 1
        if batch_number > self.total_batches:
            raise ValueError("预测批次数超过评测绑定声明")
        if len(rows) > self.batch_size:
            raise ValueError("预测批次行数超过 batch_size")
        decorated: list[dict[str, object]] = []
        batch_indices: set[int] = set()
        batch_sample_ids: set[str] = set()
        for raw_row in rows:
            row = dict(raw_row)
            index = row.get("record_index")
            if type(index) is not int or not 0 <= index < len(self.records):
                raise ValueError("预测行 record_index 非法")
            sample_id = row.get("sample_id")
            if sample_id != self.sample_ids[index]:
                raise ValueError("预测行 sample_id 与冻结顺序不一致")
            if index in self._rows_by_index or index in batch_indices:
                raise ValueError(f"预测批次包含重复 record_index：{index}")
            if (
                any(
                    existing.get("sample_id") == sample_id
                    for existing in self._rows_by_index.values()
                )
                or sample_id in batch_sample_ids
            ):
                raise ValueError(f"预测批次包含重复 sample_id：{sample_id}")
            label, output_key = evaluation_record_contract(self.records[index])
            if row.get("true_label") != label or row.get("expected_output_key") != output_key:
                raise ValueError("预测行标签合同不一致")
            row.update(
                {
                    "_journal_batch": batch_number,
                    "_journal_batch_size": len(rows),
                    "_journal_batch_elapsed_seconds": float(batch_elapsed_seconds),
                    "_journal_batch_peak_gpu_memory_bytes": batch_peak_gpu_memory_bytes,
                }
            )
            self._validate_prediction_semantics(
                row,
                location="预测行",
                output_key=output_key,
            )
            decorated.append(row)
            batch_indices.add(index)
            batch_sample_ids.add(str(sample_id))

        _atomic_write_jsonl(
            self.partial_path,
            [*self._rows_by_index.values(), *decorated],
        )
        for row in decorated:
            self._rows_by_index[int(row["record_index"])] = row
        self._batch_runtime[batch_number] = (
            float(batch_elapsed_seconds),
            batch_peak_gpu_memory_bytes,
        )
        return self._write_progress("running")

    def finalize(
        self,
        summary_builder: Callable[[Sequence[Mapping[str, object]]], Mapping[str, object]],
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        """先完成验证与汇总，再按冻结顺序发布最终制品。"""
        if self.pending_indices:
            raise ValueError(f"仍有 {len(self.pending_indices)} 条样本未完成")
        rows: list[dict[str, object]] = []
        for index in range(len(self.records)):
            stored_row = self._rows_by_index[index]
            _, output_key = evaluation_record_contract(self.records[index])
            self._validate_prediction_semantics(
                stored_row,
                location=f"最终预测第 {index + 1} 行",
                output_key=output_key,
            )
            row = {
                key: value
                for key, value in stored_row.items()
                if key != "record_index" and key not in _JOURNAL_FIELDS
            }
            _canonical_json_bytes(row)
            rows.append(row)
        summary = dict(summary_builder(rows))
        _atomic_write_json(self.output_dir / "evaluation_summary.json", summary)
        _atomic_write_jsonl(self.final_path, rows)
        self._write_progress("finished")
        return rows, summary


def build_evaluation_tracking_config(
    probe: ProbeConfig,
    test_file: Path | str,
    adapter_path: Path | str | None,
    settings: EvaluationSettings | None = None,
) -> dict[str, object]:
    """构造评估阶段的 SwanLab 复现配置。"""
    runtime = settings or EvaluationSettings()
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
        **asdict(runtime),
    }


def build_evaluation_progress_metrics(
    progress: Mapping[str, object],
    *,
    batch_latency_ms: float,
) -> dict[str, float | int]:
    """把本地进度转换为稳定的 SwanLab 逐批标量键。"""
    completed = int(progress["completed_samples"])
    total = int(progress["total_samples"])
    if total <= 0:
        raise ValueError("评测总样本数必须大于 0")
    return {
        "progress/completed": completed,
        "progress/ratio": completed / total,
        "throughput/samples_per_second": float(progress["samples_per_second"]),
        "runtime/eta_seconds": float(progress["eta_seconds"]),
        "runtime/batch_latency_ms": batch_latency_ms,
        "memory/gpu_peak_mib": float(progress["batch_gpu_peak_mib"]),
    }


def _run_with_fresh_cuda_peak(
    operation: Callable[[], _ResultT],
    cuda,
) -> tuple[_ResultT, int]:
    """重置统计后执行单批操作，并返回该批自身的 CUDA 峰值。"""
    cuda.reset_peak_memory_stats()
    result = operation()
    return result, int(cuda.max_memory_allocated())


def evaluation_tracking_artifact_dir(
    output_dir: Path | str,
    *,
    resume: bool,
) -> Path:
    """为续评保留既有 SwanLab 清单，并选择新的跟踪尝试目录。"""
    output_path = Path(output_dir)
    if not resume or not (output_path / "artifact_manifest.json").exists():
        return output_path
    attempts_dir = output_path / "tracking-attempts"
    attempt = 1
    while (attempts_dir / f"attempt-{attempt:04d}" / "artifact_manifest.json").exists():
        attempt += 1
    return attempts_dir / f"attempt-{attempt:04d}"


def _generate_batch(
    model,
    tokenizer,
    prompts: Sequence[str],
    *,
    max_input_length: int,
    max_new_tokens: int,
    synchronize: Callable[[], None] | None = None,
) -> list[GeneratedResult]:
    """用一次贪心生成处理一个左填充批次。"""
    if not prompts:
        raise ValueError("生成批次不能为空")
    import torch

    inputs = tokenizer(
        list(prompts),
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_input_length,
    )
    inputs = inputs.to(model.device)
    if "attention_mask" not in inputs:
        raise ValueError("批量生成要求分词器返回 attention_mask")
    input_token_counts = [int(value) for value in inputs["attention_mask"].sum(dim=1)]
    padded_input_width = int(inputs["input_ids"].shape[-1])
    sync = synchronize or (lambda: None)
    sync()
    started_at = time.perf_counter()
    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    sync()
    latency_ms = (time.perf_counter() - started_at) * 1000
    new_tokens = output[:, padded_input_width:]
    texts = tokenizer.batch_decode(new_tokens, skip_special_tokens=True)
    pad_token_id = tokenizer.pad_token_id
    results = []
    for text, input_tokens, token_row in zip(texts, input_token_counts, new_tokens, strict=True):
        generated_tokens = (
            int(token_row.numel())
            if pad_token_id is None
            else int((token_row != pad_token_id).sum().item())
        )
        results.append(
            GeneratedResult(
                text=text,
                input_tokens=input_tokens,
                generated_tokens=generated_tokens,
                latency_ms=latency_ms,
            )
        )
    return results


def _prediction_row(
    index: int,
    record: Mapping[str, object],
    result: GeneratedResult,
) -> dict[str, object]:
    label, output_key = evaluation_record_contract(record)
    parsed = parse_prediction(result.text, label_key=output_key)
    return {
        "record_index": index,
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


def _summary_from_rows(
    probe: ProbeConfig,
    adapter_path: Path | None,
    settings: EvaluationSettings,
    binding_sha256: str,
    records: Sequence[Mapping[str, object]],
    rows: Sequence[Mapping[str, object]],
    journal: EvaluationJournal,
) -> dict[str, object]:
    generated = [
        GeneratedResult(
            text=str(row["generated_text"]),
            input_tokens=int(row["input_tokens"]),
            generated_tokens=int(row["generated_tokens"]),
            latency_ms=float(row["latency_ms"]),
        )
        for row in rows
    ]
    metrics, _ = summarize_generated_results(records, generated)
    elapsed = max(journal.elapsed_seconds, 1e-12)
    input_tokens = sum(result.input_tokens for result in generated)
    generated_tokens = sum(result.generated_tokens for result in generated)
    efficiency = {
        "sample_count": len(records),
        "input_tokens": input_tokens,
        "generated_tokens": generated_tokens,
        "wall_seconds": elapsed,
        "samples_per_second": len(records) / elapsed,
        "tokens_per_second": (input_tokens + generated_tokens) / elapsed,
        "peak_gpu_memory_bytes": journal.peak_gpu_memory_bytes,
    }
    return {
        "model_id": probe.model_id,
        "adapter_path": str(adapter_path) if adapter_path is not None else None,
        "seed": probe.seed,
        "evaluation_settings": asdict(settings),
        "binding_sha256": binding_sha256,
        "metrics": metrics,
        "efficiency": efficiency,
    }


def _evaluate_model_impl(
    probe: ProbeConfig,
    test_file: Path,
    output_dir: Path,
    adapter_path: Path | None = None,
    settings: EvaluationSettings | None = None,
    progress_callback: Callable[[Mapping[str, float | int]], None] | None = None,
) -> dict[str, object]:
    """在 CUDA 上执行可恢复的零样本或 LoRA 批量评估。"""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    runtime = settings or EvaluationSettings()
    records = _load_records(test_file)
    validate_evaluation_records(records)
    binding = build_evaluation_binding(
        probe, runtime, test_file, records, adapter_path=adapter_path
    )
    journal = EvaluationJournal(
        output_dir,
        binding,
        records,
        resume=runtime.resume,
        flush_every_batches=runtime.flush_every_batches,
    )

    if journal.pending_indices:
        if not torch.cuda.is_available():
            raise RuntimeError("未检测到 CUDA，拒绝启动大模型评估")
        tokenizer = AutoTokenizer.from_pretrained(probe.model_id, use_fast=True)
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        quantization = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        model_kwargs: dict[str, object] = {
            "quantization_config": quantization,
            "dtype": torch.bfloat16,
            "device_map": "auto",
        }
        if runtime.attention_backend != "auto":
            model_kwargs["attn_implementation"] = runtime.attention_backend
        model = AutoModelForCausalLM.from_pretrained(probe.model_id, **model_kwargs)
        if adapter_path is not None:
            from peft import PeftModel

            model = PeftModel.from_pretrained(model, str(adapter_path))
        model.eval()

        pending_indices = journal.pending_indices
        prompts = [
            format_generation_prompt(tokenizer, str(records[index]["prompt"]))
            for index in pending_indices
        ]
        length_encoding = tokenizer(
            prompts,
            padding=False,
            truncation=True,
            max_length=probe.max_input_length,
        )
        lengths = [len(token_ids) for token_ids in length_encoding["input_ids"]]
        relative_batches = plan_length_bucketed_batches(
            lengths,
            runtime.batch_size,
            runtime.length_bucket,
        )
        batches = tuple(
            tuple(pending_indices[relative_index] for relative_index in batch)
            for batch in relative_batches
        )
        prompt_by_index = dict(zip(pending_indices, prompts, strict=True))
        synchronize = torch.cuda.synchronize

        warmup_index = pending_indices[0]
        _generate_batch(
            model,
            tokenizer,
            [prompt_by_index[warmup_index]],
            max_input_length=probe.max_input_length,
            max_new_tokens=probe.max_new_tokens,
            synchronize=synchronize,
        )
        for batch in batches:
            batch_started_at = time.perf_counter()
            batch_prompts = [prompt_by_index[index] for index in batch]
            batch_results, peak_gpu_memory_bytes = _run_with_fresh_cuda_peak(
                lambda prompts=batch_prompts: _generate_batch(
                    model,
                    tokenizer,
                    prompts,
                    max_input_length=probe.max_input_length,
                    max_new_tokens=probe.max_new_tokens,
                    synchronize=synchronize,
                ),
                torch.cuda,
            )
            rows = [
                _prediction_row(index, records[index], result)
                for index, result in zip(batch, batch_results, strict=True)
            ]
            batch_elapsed_seconds = time.perf_counter() - batch_started_at
            progress = journal.append_batch(
                rows,
                batch_elapsed_seconds=batch_elapsed_seconds,
                batch_peak_gpu_memory_bytes=peak_gpu_memory_bytes,
            )
            if progress_callback is not None:
                progress_callback(
                    build_evaluation_progress_metrics(
                        progress,
                        batch_latency_ms=batch_elapsed_seconds * 1000,
                    )
                )

    _, summary = journal.finalize(
        lambda final_rows: _summary_from_rows(
            probe,
            adapter_path,
            runtime,
            journal.binding_sha256,
            records,
            final_rows,
            journal,
        )
    )
    return summary


def evaluate_model(
    probe: ProbeConfig,
    test_file: Path,
    output_dir: Path,
    adapter_path: Path | None = None,
    tracking: TrackingSettings | None = None,
    settings: EvaluationSettings | None = None,
) -> dict[str, object]:
    """执行评估，并把检测效果、效率和逐批进度写入 SwanLab。"""
    runtime = settings or EvaluationSettings()
    if tracking is None:
        with capture_console_log(output_dir / "console.log"):
            return _evaluate_model_impl(
                probe,
                test_file,
                output_dir,
                adapter_path,
                runtime,
            )

    phase = "zero-shot" if adapter_path is None else "evaluation"
    tracking_config = build_evaluation_tracking_config(probe, test_file, adapter_path, runtime)
    tracked_metrics_path = output_dir / "swanlab_metrics.json"
    data_files = {
        "evaluation_binding": output_dir / "evaluation_binding.json",
        "evaluation_progress": output_dir / "evaluation_progress.json",
        "evaluation_summary": output_dir / "evaluation_summary.json",
        "partial_predictions": output_dir / "predictions.partial.jsonl",
        "predictions": output_dir / "predictions.jsonl",
        "swanlab_metrics": tracked_metrics_path,
        "test_file": test_file,
    }
    if adapter_path is not None:
        data_files["adapter_path"] = adapter_path
    tracking_artifact_dir = evaluation_tracking_artifact_dir(output_dir, resume=runtime.resume)
    with (
        capture_console_log(tracking_artifact_dir / "console.log"),
        swanlab_run(
            tracking,
            phase=phase,
            config=tracking_config,
            artifact_dir=tracking_artifact_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        summary = _evaluate_model_impl(
            probe,
            test_file,
            output_dir,
            adapter_path,
            runtime,
            progress_callback=swanlab.log,
        )
        tracked_metrics = flatten_scalar_metrics(summary, prefix=phase)
        _atomic_write_json(tracked_metrics_path, tracked_metrics)
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
    settings = build_evaluation_settings(evaluation)
    tracking = TrackingSettings.from_mapping(raw["tracking"])
    summary = evaluate_model(
        probe=probe,
        test_file=Path(evaluation["test_file"]),
        output_dir=Path(evaluation["output_dir"]),
        adapter_path=args.adapter_path,
        tracking=tracking,
        settings=settings,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
