#!/usr/bin/env python3
"""第三章 DRIFT 正式评价的按需共享编辑算子。

本模块在内存中为一个 exact eSLD 生成一条确定性编辑流，并从同一条流
返回 ``k=1``、``k=2`` 和 ``random_half`` 三个前缀。模块顶层只依赖
Python 标准库和共享合同；PyArrow 仅在 ``--audit`` 入口内按需导入。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterator, Mapping

try:
    from ch3_drift_formal_contract import (
    REPO_ROOT,
        ContractError,
        atomic_write_json,
        attack_stream_id,
        canonical_json_bytes,
        length_prefix_encode,
        load_config,
        resolve_repo_relative,
        resolve_run_dir,
        sha256_bytes,
        sha256_file,
    )
except ImportError:
    from thesis.experiments.llm_probe.tools.ch3_drift_formal_contract import (
        REPO_ROOT,
        ContractError,
        atomic_write_json,
        attack_stream_id,
        canonical_json_bytes,
        length_prefix_encode,
        load_config,
        resolve_repo_relative,
        resolve_run_dir,
        sha256_bytes,
        sha256_file,
    )


SCHEMA_VERSION = "ch3_drift_formal_edit_v1"
ALGORITHM_VERSION = "shared_prefix_edit_v1"
DEFAULT_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789-"
TIER_ORDER = ("k=1", "k=2", "random_half")
DEFAULT_BATCH_SIZE = 8192
COUNTER_BYTES = 8
WORD_BYTES = 8
WORD_BITS = WORD_BYTES * 8
WORD_SPACE = 1 << WORD_BITS


class EditContractError(ValueError):
    """按需编辑合同校验失败。"""


class _CounterByteStream:
    """由流身份和大端计数器扩展 SHA-256 字节。"""

    def __init__(self, stream_id: str) -> None:
        self._prefix = length_prefix_encode(stream_id)
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


def _validate_text(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise EditContractError(f"{name} 必须是字符串")
    if not value:
        raise EditContractError(f"{name} 不能为空")
    return value


def _uniform_index(stream: _CounterByteStream, upper_bound: int) -> int:
    """用 64 位拒绝采样返回 ``[0, upper_bound)`` 的均匀整数。"""
    if upper_bound <= 0 or upper_bound >= WORD_SPACE:
        raise EditContractError("拒绝采样上界必须在 1 和 2^64-1 之间")
    remainder = WORD_SPACE % upper_bound
    limit = WORD_SPACE - remainder
    while True:
        value = stream.read_word()
        if value < limit:
            return value % upper_bound


def _budgets(length: int) -> dict[str, int]:
    if length <= 0:
        raise EditContractError("exact_esld 长度必须为正数")
    requested = {
        "k=1": 1,
        "k=2": 2,
        "random_half": max(1, length // 2),
    }
    return {tier: min(value, length) for tier, value in requested.items()}


def _requested_budgets(length: int) -> dict[str, int]:
    return {"k=1": 1, "k=2": 2, "random_half": max(1, length // 2)}


def _hamming_distance(left: str, right: str) -> int:
    if len(left) != len(right):
        raise EditContractError("编辑不得改变 exact_esld 长度")
    return sum(left_char != right_char for left_char, right_char in zip(left, right))


def _changed_positions(original: str, edited: str) -> set[int]:
    if len(original) != len(edited):
        raise EditContractError("编辑输出长度与 exact_esld 不一致")
    return {
        index
        for index, (original_char, edited_char) in enumerate(zip(original, edited))
        if original_char != edited_char
    }


def _validate_alphabet(alphabet: str) -> str:
    _validate_text(alphabet, "alphabet")
    if len(set(alphabet)) != len(alphabet):
        raise EditContractError("alphabet 不得包含重复字符")
    return alphabet


def generate_shared_edits(
    exact_esld: str,
    *,
    attack_namespace: str,
    revision: str,
    alphabet: str = DEFAULT_ALPHABET,
) -> dict[str, Any]:
    """为一个 exact eSLD 生成三档共享前缀编辑。

    ``output`` 字段只在调用方当前评价批的内存中存在；本模块不写出该字段。
    ``requested_budget`` 是名义预算，``actual_budget`` 是按字符串长度截断后
    的有效预算。三档共享同一个位置排列和替换字符流的前缀。
    """
    original = _validate_text(exact_esld, "exact_esld")
    namespace = _validate_text(attack_namespace, "attack_namespace")
    data_revision = _validate_text(revision, "revision")
    alphabet_value = _validate_alphabet(alphabet)
    length = len(original)
    requested = _requested_budgets(length)
    actual = _budgets(length)
    stream_id = attack_stream_id(namespace, data_revision, original)
    stream = _CounterByteStream(stream_id)

    positions = list(range(length))
    for index in range(length - 1, 0, -1):
        swap_index = _uniform_index(stream, index + 1)
        positions[index], positions[swap_index] = positions[swap_index], positions[index]

    replacements: list[str] = []
    for position in positions:
        original_char = original[position]
        choices = tuple(char for char in alphabet_value if char != original_char)
        if not choices:
            raise EditContractError("alphabet 排除原字符后为空")
        replacements.append(choices[_uniform_index(stream, len(choices))])

    edits = tuple(zip(positions, replacements))
    outputs: dict[str, str] = {}
    for tier in TIER_ORDER:
        output_chars = list(original)
        for position, replacement in edits[: actual[tier]]:
            output_chars[position] = replacement
        outputs[tier] = "".join(output_chars)

    degenerate = len(set(actual.values())) < len(TIER_ORDER)
    tiers: dict[str, dict[str, Any]] = {}
    for tier in TIER_ORDER:
        output = outputs[tier]
        distance = _hamming_distance(original, output)
        if distance != actual[tier]:
            raise EditContractError(f"{tier} 实际汉明距离不等于有效预算")
        tiers[tier] = {
            "output": output,
            "requested_budget": requested[tier],
            "actual_budget": actual[tier],
            "hamming_distance": distance,
            "output_sha256": sha256_bytes(output.encode("utf-8")),
            "degenerate_budget": degenerate,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "attack_stream_id": stream_id,
        "length": length,
        "requested_budgets": requested,
        "actual_budgets": actual,
        "degenerate_budget": degenerate,
        "half_weaker_than_k2": actual["random_half"] < actual["k=2"],
        "tiers": tiers,
    }


def generate_shared_edit_stream(
    exact_esld: str,
    *,
    attack_namespace: str,
    revision: str,
    alphabet: str = DEFAULT_ALPHABET,
) -> dict[str, Any]:
    """``generate_shared_edits`` 的语义别名，便于评价器按流调用。"""
    return generate_shared_edits(
        exact_esld,
        attack_namespace=attack_namespace,
        revision=revision,
        alphabet=alphabet,
    )


def _iter_domain_batches(path: Path, batch_size: int) -> Iterator[list[Any]]:
    """按批次读取域名列；PyArrow 只在真实审计入口中导入。"""
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise EditContractError(f"审计入口需要 PyArrow：{exc}") from exc
    if batch_size <= 0:
        raise EditContractError("batch_size 必须为正数")
    for batch in parquet.ParquetFile(path).iter_batches(
        batch_size=batch_size,
        columns=["domain"],
    ):
        yield batch.column(0).to_pylist()


def _parquet_row_count(path: Path) -> int:
    """读取源 Parquet 元数据行数，不加载数据列。"""
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise EditContractError(f"审计入口需要 PyArrow：{exc}") from exc
    metadata = parquet.ParquetFile(path).metadata
    if metadata is None:
        raise EditContractError("源 Parquet 缺少元数据")
    return int(metadata.num_rows)


def _audit_pair_prefix(original: str, result: Mapping[str, Any]) -> bool:
    tiers = result["tiers"]
    changed = {
        tier: _changed_positions(original, tiers[tier]["output"])
        for tier in TIER_ORDER
    }
    actual = result["actual_budgets"]
    for left in TIER_ORDER:
        for right in TIER_ORDER:
            if actual[left] <= actual[right] and not changed[left].issubset(changed[right]):
                return False
            if actual[left] <= actual[right]:
                for position in changed[left]:
                    if tiers[left]["output"][position] != tiers[right]["output"][position]:
                        return False
            if actual[left] == actual[right] and tiers[left]["output"] != tiers[right]["output"]:
                return False
    return True


def _record_digest(source_hash: str, result: Mapping[str, Any], tier: str) -> bytes:
    tier_result = result["tiers"][tier]
    record = {
        "source_sha256": source_hash,
        "attack_tier": tier,
        "attack_stream_id": result["attack_stream_id"],
        "requested_budget": tier_result["requested_budget"],
        "actual_budget": tier_result["actual_budget"],
        "hamming_distance": tier_result["hamming_distance"],
        "output_sha256": tier_result["output_sha256"],
        "degenerate_budget": tier_result["degenerate_budget"],
    }
    return hashlib.sha256(canonical_json_bytes(record)).digest()


def _new_summary() -> dict[str, Any]:
    return {
        "count": 0,
        "root_sha256": hashlib.sha256().hexdigest(),
        "xor_digest": "00" * 32,
        "output_sha256_unique_count": 0,
    }


def _audit_scope(
    config: Mapping[str, Any],
    config_hash: str,
    source_path: Path,
    code_hash: str,
    batch_size: int,
) -> dict[str, Any]:
    started = time.monotonic()
    attacks = config["attacks"]
    namespace = attacks["namespace"]
    revision = config["data_revision"]
    alphabet = attacks["alphabet"]
    summary = {tier: _new_summary() for tier in TIER_ORDER}
    roots = {tier: hashlib.sha256() for tier in TIER_ORDER}
    xor_values = {tier: 0 for tier in TIER_ORDER}
    output_sources: dict[str, dict[str, str]] = {tier: {} for tier in TIER_ORDER}
    collision_records: list[dict[str, str]] = []
    counts: dict[str, int] = {}
    input_count = 0
    valid_count = 0
    degenerate_count = 0
    prefix_pass_count = 0
    deterministic_pass_count = 0
    half_weaker_count = 0
    metadata_rows = _parquet_row_count(source_path)

    for values in _iter_domain_batches(source_path, batch_size):
        for value in values:
            input_count += 1
            if not isinstance(value, str):
                counts["non_string_domain"] = counts.get("non_string_domain", 0) + 1
                continue
            if not value:
                counts["empty_domain"] = counts.get("empty_domain", 0) + 1
                continue
            try:
                result = generate_shared_edits(
                    value,
                    attack_namespace=namespace,
                    revision=revision,
                    alphabet=alphabet,
                )
                repeated = generate_shared_edits(
                    value,
                    attack_namespace=namespace,
                    revision=revision,
                    alphabet=alphabet,
                )
            except EditContractError as exc:
                category = "edit_contract_error"
                if "alphabet" in str(exc):
                    category = "alphabet_error"
                counts[category] = counts.get(category, 0) + 1
                continue
            source_hash = sha256_bytes(value.encode("utf-8"))
            valid_count += 1
            deterministic_ok = (
                result["attack_stream_id"] == repeated["attack_stream_id"]
                and all(
                    result["tiers"][tier]["output_sha256"]
                    == repeated["tiers"][tier]["output_sha256"]
                    for tier in TIER_ORDER
                )
            )
            if deterministic_ok:
                deterministic_pass_count += 1
            else:
                counts["nondeterministic_output"] = counts.get("nondeterministic_output", 0) + 1
            prefix_ok = _audit_pair_prefix(value, result)
            if prefix_ok:
                prefix_pass_count += 1
            else:
                counts["prefix_or_budget_failure"] = counts.get("prefix_or_budget_failure", 0) + 1
            if result["degenerate_budget"]:
                degenerate_count += 1
            if result["half_weaker_than_k2"]:
                half_weaker_count += 1
            for tier in TIER_ORDER:
                tier_result = result["tiers"][tier]
                digest = tier_result["output_sha256"]
                previous_source = output_sources[tier].get(digest)
                if previous_source is None:
                    output_sources[tier][digest] = source_hash
                elif previous_source != source_hash:
                    collision_records.append(
                        {
                            "attack_tier": tier,
                            "output_sha256": digest,
                            "first_source_sha256": previous_source,
                            "second_source_sha256": source_hash,
                        }
                    )
                record_digest = _record_digest(source_hash, result, tier)
                roots[tier].update(record_digest)
                xor_values[tier] ^= int.from_bytes(record_digest, "big")
                summary[tier]["count"] += 1

    for tier in TIER_ORDER:
        summary[tier]["root_sha256"] = roots[tier].hexdigest()
        summary[tier]["xor_digest"] = xor_values[tier].to_bytes(32, "big").hex()
        summary[tier]["output_sha256_unique_count"] = len(output_sources[tier])
    if input_count != valid_count:
        counts["invalid_input_total"] = input_count - valid_count
    fully_processed = input_count == metadata_rows
    if not fully_processed:
        counts["source_row_count_mismatch"] = abs(metadata_rows - input_count)
    status = "complete" if not counts else "failed"
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "status": status,
        "scope": "t17-validation",
        "source": {
            "path": str(source_path.relative_to(REPO_ROOT)),
            "sha256": sha256_file(source_path),
            "rows_read": input_count,
            "valid_rows": valid_count,
            "metadata_rows": metadata_rows,
            "fully_processed": fully_processed,
        },
        "config_sha256": config_hash,
        "code_sha256": code_hash,
        "namespace": namespace,
        "revision": revision,
        "alphabet_sha256": sha256_bytes(alphabet.encode("utf-8")),
        "batch_size": batch_size,
        "verification": {
            "deterministic_rows_passed": deterministic_pass_count,
            "prefix_rows_passed": prefix_pass_count,
            "budget_degenerate_rows": degenerate_count,
            "half_weaker_than_k2_rows": half_weaker_count,
            "failure_counts": dict(sorted(counts.items())),
            "output_summary": summary,
        },
        "collision_audit": {
            "collision_count": len(collision_records),
            "records": collision_records,
        },
        "runtime": {
            "elapsed_seconds": time.monotonic() - started,
            "python_executable": sys.executable,
            "python_version": sys.version,
        },
        "materialization": {
            "attacked_esld_written": False,
            "member_dataset_written": False,
            "per_entity_list_written": False,
        },
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="仓库相对评价配置路径")
    parser.add_argument("--run-dir", required=True, help="仓库相对审计运行目录")
    parser.add_argument("--audit", action="store_true", help="执行真实输入审计")
    parser.add_argument("--scope", choices=("t17-validation",), help="审计作用域")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="只读批次大小")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if not args.audit or args.scope != "t17-validation":
            raise EditContractError("必须同时指定 --audit --scope t17-validation")
        if args.batch_size <= 0:
            raise EditContractError("batch-size 必须为正数")
        run_dir = resolve_run_dir(args.run_dir)
        config, config_hash = load_config(args.config)
        if config.get("config_kind") != "evaluation":
            raise EditContractError("按需编辑审计必须使用评价配置")
        roles = [role for role in config["input_roles"] if role["role"] == "T17_dga_val"]
        if len(roles) != 1:
            raise EditContractError("评价配置必须恰好包含 T17_dga_val")
        source_path = resolve_repo_relative(roles[0]["path"], must_exist=True)
        code_path = Path(__file__).resolve()
        receipt = _audit_scope(config, config_hash, source_path, sha256_file(code_path), args.batch_size)
        receipt_path = run_dir / "direct-edit-audit.json"
        receipt_hash = atomic_write_json(receipt_path.relative_to(REPO_ROOT), receipt)
        collision_path = run_dir / "attack-collision-audit.json"
        collision_payload = {
            "schema_version": SCHEMA_VERSION,
            "algorithm_version": ALGORITHM_VERSION,
            "scope": receipt["scope"],
            "source_path": receipt["source"]["path"],
            "source_sha256": receipt["source"]["sha256"],
            "collision_count": receipt["collision_audit"]["collision_count"],
            "records": receipt["collision_audit"]["records"],
        }
        collision_hash = atomic_write_json(collision_path.relative_to(REPO_ROOT), collision_payload)
        print(
            json.dumps(
                {
                    "status": receipt["status"],
                    "scope": receipt["scope"],
                    "rows_read": receipt["source"]["rows_read"],
                    "valid_rows": receipt["source"]["valid_rows"],
                    "failure_counts": receipt["verification"]["failure_counts"],
                    "receipt": str(receipt_path.relative_to(REPO_ROOT)),
                    "receipt_sha256": receipt_hash,
                    "collision_audit": str(collision_path.relative_to(REPO_ROOT)),
                    "collision_audit_sha256": collision_hash,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0 if receipt["status"] == "complete" else 2
    except (ContractError, EditContractError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"按需共享编辑审计失败：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
