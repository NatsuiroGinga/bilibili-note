#!/usr/bin/env python3
"""第三章 DRIFT 正式评价共享编辑 v2（评价侧）合法算子。

规格来源：``thesis/methods/第三章-正式攻击与目标抽样合同裁决.md`` §十二。
实施计划：``.Codex/docs/2026-10-13-正式编辑预算科学筛选/implementation_plan.md``。

本模块在内存中为一个 exact eSLD 生成确定性编辑流，并提供冻结成员合法性审计。
顶层只依赖 Python 标准库；PyArrow 只在 ``--audit`` 入口内按需导入。

冻结语义（勿改）：

- 预算按**可编辑位** ``|E|`` 计：``b_h = max(1, |E|//2)``，实际 ``q_t = min(b_t, |E|)``；
- 点号位置冻结；``xn--`` 开头或标签第 3、4 位同时为连字符的标签整标签冻结；
- 标签首／尾位替换集仅 ``{a-z0-9}``；内部位 ``{a-z0-9-}`` 且第 3、4 位不新生成 ``-``；
  排除与原字符大小写不敏感相同的选项；
- 随机流由 ``(NAMESPACE, stream_id, x)`` 派生；三档共享同一位置排列与替换字符流的前缀；
- ``|E| == 0`` 时生成失败并计失败，绝不把干净原串静默计作攻击。
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Iterator

SCHEMA_VERSION = "ch3-drift-formal-edit-v2"
NAMESPACE = "shared_prefix_edit_v2"
TIERS = ("k1", "k2", "random_half")
NOMINAL_BUDGETS = {"k1": 1, "k2": 2}
DOT = "."
HYPHEN = "-"
ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"
ALPHABET = ALNUM + HYPHEN
RESERVED_LABEL_PREFIX = "xn--"
RESERVED_HYPHEN_OFFSETS = (2, 3)
LABEL_MIN_BYTES = 1
LABEL_MAX_BYTES = 63
ALLOWED_SYNTAX_CHARS = frozenset(ALPHABET + DOT)

COUNTER_BYTES = 8
WORD_BYTES = 8
WORD_BITS = WORD_BYTES * 8
WORD_SPACE = 1 << WORD_BITS

DEFAULT_SAMPLE_MAX_ROWS = 200_000
DEFAULT_PREFIX_SAMPLE = 1_000
MAX_FAILURE_DETAIL = 50
DATA_REVISION = "3b31077020cd1c013d0a75cad51042a2327c4521"
SOURCE_YEARS = (17, 18, 19)
SPLITS = ("train", "test", "val")
DEFAULT_DATA_DIR = (
    "thesis/experiments/llm_probe/runs/data-raw/"
    f"drift-dga-2026-rev-{DATA_REVISION}/DRIFT_input_eSLD"
)
DEFAULT_STREAM_ID = f"audit|{NAMESPACE}|{DATA_REVISION}"
DEFAULT_RECEIPT = (
    ".Codex/docs/2026-10-13-正式编辑预算科学筛选/edit-v2-audit-receipt.json"
)
DEFAULT_LOG = (
    ".Codex/docs/2026-10-13-正式编辑预算科学筛选/edit-v2-audit-console.log"
)
SAMPLE_SALT = f"{SCHEMA_VERSION}|deterministic-subset-v1"

REPO_ROOT = Path(__file__).resolve().parents[4]


class EditContractError(ValueError):
    """v2 编辑合同校验失败。"""


# ---------------------------------------------------------------- 基础工具


def _sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """流式计算文件 SHA-256，不把文件整体读入内存。"""
    if chunk_size <= 0:
        raise EditContractError("哈希块大小必须为正数")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _length_prefix_encode(*fields: str) -> bytes:
    encoded = bytearray()
    for field in fields:
        raw = field.encode("utf-8")
        encoded.extend(len(raw).to_bytes(8, "big", signed=False))
        encoded.extend(raw)
    return bytes(encoded)


class _CounterByteStream:
    """由 ``(NAMESPACE, stream_id, x)`` 派生的计数器模式 SHA-256 字节流。"""

    def __init__(self, prefix: bytes) -> None:
        self._prefix = prefix
        self._counter = 0
        self._block = b""
        self._offset = 0

    def read(self, size: int) -> bytes:
        if size < 0:
            raise EditContractError("随机字节读取长度不得为负数")
        output = bytearray()
        while len(output) < size:
            if self._offset == len(self._block):
                counter = self._counter.to_bytes(COUNTER_BYTES, "big", signed=False)
                self._block = hashlib.sha256(self._prefix + counter).digest()
                self._counter += 1
                self._offset = 0
            take = min(size - len(output), len(self._block) - self._offset)
            output.extend(self._block[self._offset : self._offset + take])
            self._offset += take
        return bytes(output)

    def read_word(self) -> int:
        return int.from_bytes(self.read(WORD_BYTES), "big", signed=False)

    def index(self, upper_bound: int) -> int:
        """用 64 位拒绝采样返回 ``[0, upper_bound)`` 的均匀整数。"""
        if upper_bound <= 0 or upper_bound >= WORD_SPACE:
            raise EditContractError("拒绝采样上界必须在 1 和 2^64-1 之间")
        remainder = WORD_SPACE % upper_bound
        limit = WORD_SPACE - remainder
        while True:
            value = self.read_word()
            if value < limit:
                return value % upper_bound


def _stream_identity(stream_id: str, x: str) -> tuple[str, _CounterByteStream]:
    prefix = _length_prefix_encode(NAMESPACE, stream_id, x)
    return _sha256_hex(prefix), _CounterByteStream(prefix)


# ---------------------------------------------------------------- 语法与可编辑位


def _label_records(x: str) -> list[dict[str, Any]]:
    """按点号切分标签，返回含冻结判据的记录（不做合法性判定）。"""
    records: list[dict[str, Any]] = []
    start = 0
    for index in range(len(x) + 1):
        if index == len(x) or x[index] == DOT:
            value = x[start:index]
            frozen_reason = None
            if value.startswith(RESERVED_LABEL_PREFIX):
                frozen_reason = "reserved_xn_prefix"
            elif (
                len(value) > RESERVED_HYPHEN_OFFSETS[1]
                and all(value[offset] == HYPHEN for offset in RESERVED_HYPHEN_OFFSETS)
            ):
                frozen_reason = "reserved_double_hyphen_at_3_4"
            records.append(
                {
                    "index": len(records),
                    "value": value,
                    "start": start,
                    "end": index,
                    "length": len(value),
                    "frozen": frozen_reason is not None,
                    "frozen_reason": frozen_reason,
                }
            )
            start = index + 1
    return records


def validate_basic_syntax(x: str) -> dict:
    """基础语法规格校验。

    合格条件：仅 ASCII 小写字母／数字／连字符／点；每个标签 1–63 字节；
    标签首尾为字母或数字；无空标签（无前导、尾随或连续点）。
    """
    if not isinstance(x, str):
        return {"ok": False, "reason": "not_a_string", "labels": []}
    if not x:
        return {"ok": False, "reason": "empty_input", "labels": []}
    for char in x:
        if char not in ALLOWED_SYNTAX_CHARS:
            return {
                "ok": False,
                "reason": f"illegal_character:U+{ord(char):04X}",
                "labels": [],
            }
    labels = _label_records(x)
    for record in labels:
        value = record["value"]
        if record["length"] < LABEL_MIN_BYTES:
            return {"ok": False, "reason": "empty_label", "labels": labels}
        if record["length"] > LABEL_MAX_BYTES:
            return {"ok": False, "reason": "label_too_long", "labels": labels}
        if value[0] not in ALNUM:
            return {"ok": False, "reason": "label_leading_not_alnum", "labels": labels}
        if value[-1] not in ALNUM:
            return {"ok": False, "reason": "label_trailing_not_alnum", "labels": labels}
    return {"ok": True, "reason": None, "labels": labels}


def _replacement_choices(value: str, offset: int) -> tuple[str, ...]:
    """标签内第 ``offset`` 位的合法非恒等替换字符（保持固定顺序）。"""
    last = len(value) - 1
    if offset == 0 or offset == last:
        base = ALNUM
    elif offset in RESERVED_HYPHEN_OFFSETS:
        base = ALNUM
    else:
        base = ALPHABET
    original = value[offset].lower()
    return tuple(char for char in base if char.lower() != original)


def _editable_detail(x: str) -> tuple[list[tuple[int, tuple[str, ...]]], int]:
    """返回 ``([(绝对位置, 合法替换字符元组)], 冻结标签数)``。"""
    detail: list[tuple[int, tuple[str, ...]]] = []
    frozen_labels = 0
    for record in _label_records(x):
        if record["frozen"]:
            frozen_labels += 1
            continue
        value = record["value"]
        for offset in range(record["length"]):
            choices = _replacement_choices(value, offset)
            if choices:
                detail.append((record["start"] + offset, choices))
    return detail, frozen_labels


def editable_positions(x: str) -> dict:
    """返回 ``{L, E_positions, n_e, frozen_labels}``（``E_positions`` 升序）。"""
    detail, frozen_labels = _editable_detail(x)
    return {
        "L": len(x) if isinstance(x, str) else 0,
        "E_positions": [position for position, _ in detail],
        "n_e": len(detail),
        "frozen_labels": frozen_labels,
    }


def _shared_edit_plan(
    x: str, stream_id: str, detail: list[tuple[int, tuple[str, ...]]]
) -> tuple[tuple[tuple[int, str], ...], str]:
    """对 ``E(x)`` 无放回洗牌并为每位置选一个替换字符。

    返回 ``(plan, stream_identity)``；``plan`` 按应用顺序排列，三档共享同一 plan 的前缀。
    """
    identity, stream = _stream_identity(stream_id, x)
    positions = [position for position, _ in detail]
    choices_by_position = {position: choices for position, choices in detail}
    for index in range(len(positions) - 1, 0, -1):
        swap_index = stream.index(index + 1)
        positions[index], positions[swap_index] = positions[swap_index], positions[index]
    plan: list[tuple[int, str]] = []
    for position in positions:
        choices = choices_by_position[position]
        plan.append((position, choices[stream.index(len(choices))]))
    return tuple(plan), identity


def _nominal_budget(tier: str, n_e: int) -> int:
    if tier in NOMINAL_BUDGETS:
        return NOMINAL_BUDGETS[tier]
    if tier == "random_half":
        return max(1, n_e // 2)
    raise EditContractError(f"未知攻击档位：{tier}")


def _apply_plan(x: str, plan: tuple[tuple[int, str], ...]) -> str:
    chars = list(x)
    for position, replacement in plan:
        chars[position] = replacement
    return "".join(chars)


def _failure_record(
    tier: str, reason: str, length: int, n_e: int, frozen_labels: int, b_nominal: int, identity: str
) -> dict:
    return {
        "ok": False,
        "tier": tier,
        "reason": reason,
        "output": None,
        "L": length,
        "n_e": n_e,
        "frozen_labels": frozen_labels,
        "b_nominal": b_nominal,
        "q_actual": 0,
        "hamming": 0,
        "changed_positions_digest": _sha256_hex(_canonical_json_bytes([])),
        "stream_identity": identity,
        "output_sha256": None,
    }


def _tier_result(
    x: str,
    tier: str,
    plan: tuple[tuple[int, str], ...],
    n_e: int,
    frozen_labels: int,
    b_nominal: int,
    identity: str,
) -> dict:
    """由共享 plan 的前 ``q_t`` 项生成单档结果（三档共用同一 plan 前缀）。"""
    q_actual = min(b_nominal, n_e)
    applied = plan[:q_actual]
    output = _apply_plan(x, applied)
    hamming = sum(1 for left, right in zip(x, output) if left != right)
    if hamming != q_actual:
        return _failure_record(
            tier, "hamming_budget_mismatch", len(x), n_e, frozen_labels, b_nominal, identity
        )
    return {
        "ok": True,
        "tier": tier,
        "reason": None,
        "output": output,
        "L": len(x),
        "n_e": n_e,
        "frozen_labels": frozen_labels,
        "b_nominal": b_nominal,
        "q_actual": q_actual,
        "hamming": hamming,
        "changed_positions_digest": _sha256_hex(
            _canonical_json_bytes([[position, replacement] for position, replacement in applied])
        ),
        "stream_identity": identity,
        "output_sha256": _sha256_hex(output.encode("utf-8")),
    }


def _generate_tiers(
    x: str, stream_id: str
) -> tuple[dict[str, dict], list[tuple[int, tuple[str, ...]]], tuple[tuple[int, str], ...]]:
    """一次计算共享 plan，返回三档结果、可编辑位明细与 plan（审计复用同一路径）。"""
    syntax = validate_basic_syntax(x)
    detail, frozen_labels = _editable_detail(x)
    n_e = len(detail)
    identity, _ = _stream_identity(stream_id, x)
    if not syntax["ok"] or n_e == 0:
        reason = "invalid_syntax" if not syntax["ok"] else "no_editable_position"
        results = {
            tier: _failure_record(
                tier, reason, len(x), n_e, frozen_labels, _nominal_budget(tier, n_e), identity
            )
            for tier in TIERS
        }
        return results, detail, ()
    plan, identity = _shared_edit_plan(x, stream_id, detail)
    results = {
        tier: _tier_result(
            x, tier, plan, n_e, frozen_labels, _nominal_budget(tier, n_e), identity
        )
        for tier in TIERS
    }
    return results, detail, plan


def generate(x: str, tier: str, stream_id: str) -> dict:
    """为一个 exact eSLD 生成指定档位的确定性编辑输出。

    名义预算 ``b``：``k1``→1，``k2``→2，``random_half``→``max(1, |E|//2)``；
    实际预算 ``q_t = min(b, |E|)``，只应用共享 plan 的前 ``q_t`` 项。
    ``|E| == 0`` 时返回失败，绝不把干净原串静默计作攻击。
    """
    if tier not in TIERS:
        raise EditContractError(f"未知攻击档位：{tier}")
    if not isinstance(x, str) or not isinstance(stream_id, str) or not stream_id:
        raise EditContractError("x 与 stream_id 必须是非空字符串")
    results, _, _ = _generate_tiers(x, stream_id)
    return results[tier]


# ---------------------------------------------------------------- 合法性审计


def _changed_pairs(original: str, output: str) -> dict[int, str]:
    return {
        index: char
        for index, (before, char) in enumerate(zip(original, output))
        if before != char
    }


def _check_outputs(
    domain: str,
    results: dict[str, dict],
    detail: list[tuple[int, tuple[str, ...]]],
    plan: tuple[tuple[int, str], ...],
) -> list[str]:
    """逐实体机械核五类约束；返回问题列表（空列表即合格）。

    1) 输出自身通过基础语法；2) 长度不变；3) 点号位置不变；
    4) ``Hamming == q_actual`` 且替换字符落在该位合法集合内；
    5) 输出等于共享 plan 前 ``q_t`` 项的应用结果，故 ``k1 ⊆ k2 ⊆ random_half``。
    """
    problems: list[str] = []
    choices_by_position = dict(detail)
    dot_positions = [index for index, char in enumerate(domain) if char == DOT]
    changed_by_tier: dict[str, dict[int, str]] = {}

    for tier in TIERS:
        result = results[tier]
        output = result["output"]
        if output is None:
            problems.append(f"{tier}:missing_output")
            continue
        if len(output) != len(domain):
            problems.append(f"{tier}:length_changed")
            continue
        syntax = validate_basic_syntax(output)
        if not syntax["ok"]:
            problems.append(f"{tier}:illegal_output_syntax:{syntax['reason']}")
        if any(output[index] != DOT for index in dot_positions):
            problems.append(f"{tier}:dot_positions_changed")
        changed = _changed_pairs(domain, output)
        if len(changed) != result["q_actual"] or result["hamming"] != result["q_actual"]:
            problems.append(f"{tier}:hamming_budget_mismatch")
        if result["q_actual"] < 1:
            problems.append(f"{tier}:clean_original_counted_as_attack")
        for position, char in changed.items():
            choices = choices_by_position.get(position)
            if choices is None:
                problems.append(f"{tier}:changed_frozen_or_dot_position:{position}")
            elif char not in choices:
                problems.append(f"{tier}:illegal_replacement:{position}")
        if dict(plan[: result["q_actual"]]) != changed:
            problems.append(f"{tier}:output_not_shared_plan_prefix")
        changed_by_tier[tier] = changed

    for left in TIERS:
        for right in TIERS:
            if left == right:
                continue
            if results[left]["q_actual"] > results[right]["q_actual"]:
                continue
            for position, char in changed_by_tier.get(left, {}).items():
                if changed_by_tier.get(right, {}).get(position) != char:
                    problems.append(f"prefix_nesting:{left}_not_in_{right}:{position}")
    return problems


def _empty_counts() -> dict[str, int]:
    return {
        "total": 0,
        "valid_input": 0,
        "invalid_syntax": 0,
        "legal": 0,
        "no_editable_position": 0,
        "illegal_output": 0,
        "error": 0,
    }


def audit_members(domains: Iterable[str], stream_id: str) -> dict:
    """对成员做合法性审计；任何非法输出计入失败计数并使审计失败。"""
    started = time.monotonic()
    counts = _empty_counts()
    invalid_reasons: dict[str, int] = {}
    failures: list[dict[str, Any]] = []
    tier_stats = {
        tier: {"generated": 0, "hamming_sum": 0, "q_min": None, "q_max": 0, "budget_truncated": 0}
        for tier in TIERS
    }

    for index, domain in enumerate(domains):
        counts["total"] += 1
        if not isinstance(domain, str):
            counts["invalid_syntax"] += 1
            invalid_reasons["not_a_string"] = invalid_reasons.get("not_a_string", 0) + 1
            continue
        syntax = validate_basic_syntax(domain)
        if not syntax["ok"]:
            counts["invalid_syntax"] += 1
            reason = str(syntax["reason"])
            invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1
            if len(failures) < MAX_FAILURE_DETAIL:
                failures.append(
                    {"index": index, "kind": "invalid_syntax", "domain": domain, "problems": [reason]}
                )
            continue

        counts["valid_input"] += 1
        try:
            results, detail, plan = _generate_tiers(domain, stream_id)
        except EditContractError as exc:
            counts["error"] += 1
            if len(failures) < MAX_FAILURE_DETAIL:
                failures.append(
                    {"index": index, "kind": "error", "domain": domain, "problems": [str(exc)]}
                )
            continue

        failed_tiers = [tier for tier in TIERS if not results[tier]["ok"]]
        if failed_tiers:
            if all(results[tier]["reason"] == "no_editable_position" for tier in TIERS):
                counts["no_editable_position"] += 1
                continue
            counts["illegal_output"] += 1
            if len(failures) < MAX_FAILURE_DETAIL:
                failures.append(
                    {
                        "index": index,
                        "kind": "illegal_output",
                        "domain": domain,
                        "problems": [
                            f"{tier}:{results[tier]['reason']}" for tier in failed_tiers
                        ],
                    }
                )
            continue

        problems = _check_outputs(domain, results, detail, plan)
        if problems:
            counts["illegal_output"] += 1
            if len(failures) < MAX_FAILURE_DETAIL:
                failures.append(
                    {
                        "index": index,
                        "kind": "illegal_output",
                        "domain": domain,
                        "problems": problems[:8],
                    }
                )
            continue

        counts["legal"] += 1
        for tier in TIERS:
            result = results[tier]
            stats = tier_stats[tier]
            stats["generated"] += 1
            stats["hamming_sum"] += result["hamming"]
            q_actual = result["q_actual"]
            stats["q_min"] = q_actual if stats["q_min"] is None else min(stats["q_min"], q_actual)
            stats["q_max"] = max(stats["q_max"], q_actual)
            if q_actual < result["b_nominal"]:
                stats["budget_truncated"] += 1

    return {
        "schema_version": SCHEMA_VERSION,
        "namespace": NAMESPACE,
        "stream_id": stream_id,
        "status": "complete" if counts["illegal_output"] == 0 and counts["error"] == 0 else "failed",
        "ok": counts["illegal_output"] == 0 and counts["error"] == 0,
        "counts": counts,
        "invalid_syntax_reasons": dict(sorted(invalid_reasons.items())),
        "tier_stats": tier_stats,
        "failures": failures,
        "failure_detail_truncated": counts["illegal_output"] + counts["invalid_syntax"] > MAX_FAILURE_DETAIL,
        "elapsed_seconds": time.monotonic() - started,
    }


def _prefix_nesting_check(domains: Iterable[str], stream_id: str) -> dict:
    """显式核验 ``k1 ⊆ k2 ⊆ random_half`` 且逐项等于共享 plan 的前 ``q`` 项。"""
    checked = 0
    passed = 0
    skipped = 0
    failures: list[dict[str, Any]] = []
    deterministic_passed = 0
    deterministic_failed: list[str] = []

    for domain in domains:
        if not isinstance(domain, str) or not validate_basic_syntax(domain)["ok"]:
            skipped += 1
            continue
        results = {tier: generate(domain, tier, stream_id) for tier in TIERS}
        if not all(results[tier]["ok"] for tier in TIERS):
            skipped += 1
            continue
        checked += 1

        detail, _ = _editable_detail(domain)
        plan, _ = _shared_edit_plan(domain, stream_id, detail)
        problems: list[str] = []
        for tier in TIERS:
            applied = plan[: results[tier]["q_actual"]]
            if _apply_plan(domain, applied) != results[tier]["output"]:
                problems.append(f"{tier}:plan_prefix_mismatch")
            changed = _changed_pairs(domain, results[tier]["output"])
            if changed != dict(applied):
                problems.append(f"{tier}:changed_set_not_plan_prefix")
        ordered = sorted(TIERS, key=lambda tier: results[tier]["q_actual"])
        for smaller, larger in zip(ordered, ordered[1:]):
            q_small = results[smaller]["q_actual"]
            if plan[:q_small] != plan[: results[larger]["q_actual"]][:q_small]:
                problems.append(f"{smaller}:not_prefix_of_{larger}")
        repeated = {tier: generate(domain, tier, stream_id) for tier in TIERS}
        if all(
            repeated[tier]["output"] == results[tier]["output"]
            and repeated[tier]["output_sha256"] == results[tier]["output_sha256"]
            for tier in TIERS
        ):
            deterministic_passed += 1
        else:
            deterministic_failed.append(domain)

        if problems:
            if len(failures) < MAX_FAILURE_DETAIL:
                failures.append({"domain": domain, "problems": problems[:8]})
        else:
            passed += 1

    return {
        "checked": checked,
        "passed": passed,
        "failed": checked - passed,
        "skipped": skipped,
        "deterministic_checked": checked,
        "deterministic_passed": deterministic_passed,
        "deterministic_failed": deterministic_failed[:MAX_FAILURE_DETAIL],
        "failures": failures,
    }


# ---------------------------------------------------------------- 审计入口


def _iter_domain_column(path: Path, batch_size: int) -> Iterator[Any]:
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:  # pragma: no cover - 环境缺 PyArrow 时给出明确失败
        raise EditContractError(f"审计入口需要 PyArrow：{exc}") from exc
    for batch in parquet.ParquetFile(path).iter_batches(batch_size=batch_size, columns=["domain"]):
        yield from batch.column(0).to_pylist()


def _parquet_row_count(path: Path) -> int:
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:  # pragma: no cover
        raise EditContractError(f"审计入口需要 PyArrow：{exc}") from exc
    metadata = parquet.ParquetFile(path).metadata
    if metadata is None:
        raise EditContractError(f"源 Parquet 缺少元数据：{path}")
    return int(metadata.num_rows)


def _sample_key(salt: str, value: Any) -> int:
    raw = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    digest = hashlib.sha256(salt.encode("utf-8") + raw.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _deterministic_subset(
    path: Path, max_rows: int, batch_size: int
) -> tuple[list[str], dict[str, Any]]:
    """按固定哈希键取每文件最小的 ``max_rows`` 行，结果与文件顺序无关。"""
    salt = f"{SAMPLE_SALT}|{path.name}"
    total = _parquet_row_count(path)
    if total <= max_rows:
        sampled = list(_iter_domain_column(path, batch_size))
        keys = {domain: _sample_key(salt, domain) for domain in sampled}
    else:
        smallest = heapq.nsmallest(
            max_rows,
            ((_sample_key(salt, value), value) for value in _iter_domain_column(path, batch_size)),
        )
        sampled = [value for _, value in smallest]
        keys = {domain: key for key, domain in smallest}
    digest = hashlib.sha256()
    for domain in sorted(sampled, key=lambda item: (keys[item], item)):
        digest.update(_length_prefix_encode(domain))
    return sampled, {
        "rows_total": total,
        "rows_sampled": len(sampled),
        "fully_sampled": total <= max_rows,
        "sample_salt": salt,
        "sample_sha256": digest.hexdigest(),
    }


def _discover_files(data_dir: Path) -> list[Path]:
    files: list[Path] = []
    for year in SOURCE_YEARS:
        for split in SPLITS:
            candidate = data_dir / f"T{year}_dga_{split}.parquet"
            if not candidate.is_file():
                raise EditContractError(f"缺少源 DGA 文件：{candidate}")
            files.append(candidate)
    return files


def _write_json_atomic(path: Path, payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    return _sha256_hex(encoded.encode("utf-8"))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="共享编辑 v2 真实成员合法性审计")
    parser.add_argument("--audit", action="store_true", help="执行真实成员审计")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="仓库相对数据目录")
    parser.add_argument("--stream-id", default=DEFAULT_STREAM_ID, help="攻击流身份")
    parser.add_argument("--max-rows-per-file", type=int, default=DEFAULT_SAMPLE_MAX_ROWS)
    parser.add_argument("--batch-size", type=int, default=65536)
    parser.add_argument("--prefix-sample", type=int, default=DEFAULT_PREFIX_SAMPLE)
    parser.add_argument("--receipt", default=DEFAULT_RECEIPT, help="仓库相对收据路径")
    parser.add_argument("--log", default=DEFAULT_LOG, help="仓库相对审计日志路径")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if not args.audit:
            raise EditContractError("必须显式指定 --audit")
        if args.max_rows_per_file <= 0 or args.batch_size <= 0 or args.prefix_sample <= 0:
            raise EditContractError("采样、批次与抽样规模必须为正数")

        data_dir = REPO_ROOT / args.data_dir
        log_path = REPO_ROOT / args.log
        receipt_path = REPO_ROOT / args.receipt
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_handle = log_path.open("w", encoding="utf-8")

        def emit(line: str) -> None:
            print(line, file=sys.stderr, flush=True)
            log_handle.write(line + "\n")
            log_handle.flush()

        started = time.monotonic()
        code_path = Path(__file__).resolve()
        code_hash = sha256_file(code_path)
        emit(
            f"[edit-v2-audit] start schema={SCHEMA_VERSION} namespace={NAMESPACE} "
            f"stream_id={args.stream_id} max_rows_per_file={args.max_rows_per_file}"
        )
        emit(f"[edit-v2-audit] code={code_path.name} sha256={code_hash}")

        file_receipts: list[dict[str, Any]] = []
        totals = _empty_counts()
        total_illegal = 0
        prefix_sample_domains: list[str] = []

        for path in _discover_files(data_dir):
            file_started = time.monotonic()
            emit(f"[edit-v2-audit] file-start file={path.name}")
            sampled, sample_meta = _deterministic_subset(
                path, args.max_rows_per_file, args.batch_size
            )
            data_hash = sha256_file(path)
            if not prefix_sample_domains:
                prefix_sample_domains = sampled[: args.prefix_sample]
            result = audit_members(sampled, args.stream_id)
            counts = result["counts"]
            for key, value in counts.items():
                totals[key] = totals.get(key, 0) + value
            total_illegal += counts["illegal_output"] + counts["error"]
            emit(
                f"[edit-v2-audit] file-done file={path.name} "
                f"rows_total={sample_meta['rows_total']} sampled={sample_meta['rows_sampled']} "
                f"legal={counts['legal']} invalid_syntax={counts['invalid_syntax']} "
                f"no_editable_position={counts['no_editable_position']} "
                f"illegal_output={counts['illegal_output']} error={counts['error']} "
                f"elapsed={time.monotonic() - file_started:.1f}s"
            )
            file_receipts.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "data_sha256": data_hash,
                    "sample": sample_meta,
                    "counts": counts,
                    "invalid_syntax_reasons": result["invalid_syntax_reasons"],
                    "tier_stats": result["tier_stats"],
                    "failures": result["failures"],
                    "elapsed_seconds": result["elapsed_seconds"],
                }
            )

        emit(
            f"[edit-v2-audit] prefix-sample-check n={len(prefix_sample_domains)} "
            f"source={_discover_files(data_dir)[0].name}"
        )
        prefix_check = _prefix_nesting_check(prefix_sample_domains, args.stream_id)
        emit(
            f"[edit-v2-audit] prefix-sample-done checked={prefix_check['checked']} "
            f"passed={prefix_check['passed']} failed={prefix_check['failed']} "
            f"deterministic_passed={prefix_check['deterministic_passed']}"
        )

        status = "complete" if total_illegal == 0 else "failed"
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "namespace": NAMESPACE,
            "stream_id": args.stream_id,
            "status": status,
            "code": {"path": str(code_path.relative_to(REPO_ROOT)), "sha256": code_hash},
            "data_dir": args.data_dir,
            "sampling": {
                "method": "sha256-rank-deterministic-subset",
                "max_rows_per_file": args.max_rows_per_file,
                "batch_size": args.batch_size,
                "salt": SAMPLE_SALT,
            },
            "totals": totals,
            "illegal_output_total": total_illegal,
            "files": file_receipts,
            "prefix_nesting_sample": prefix_check,
            "runtime": {
                "elapsed_seconds": time.monotonic() - started,
                "python_executable": sys.executable,
                "python_version": sys.version,
            },
        }
        receipt_hash = _write_json_atomic(receipt_path, receipt)
        emit(
            f"[edit-v2-audit] done status={status} illegal_output_total={total_illegal} "
            f"receipt={receipt_path.relative_to(REPO_ROOT)} receipt_sha256={receipt_hash}"
        )
        log_handle.close()
        print(
            json.dumps(
                {
                    "status": status,
                    "totals": totals,
                    "illegal_output_total": total_illegal,
                    "receipt": str(receipt_path.relative_to(REPO_ROOT)),
                    "receipt_sha256": receipt_hash,
                    "prefix_nesting_sample": {
                        "checked": prefix_check["checked"],
                        "passed": prefix_check["passed"],
                        "failed": prefix_check["failed"],
                        "deterministic_passed": prefix_check["deterministic_passed"],
                    },
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0 if status == "complete" else 2
    except (EditContractError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"共享编辑 v2 审计失败：{exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
