"""LSPR24 G0 人工开发样本的确定性 Python 参考实现。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import string
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from pathlib import Path


INPUT_SCHEMA_VERSION = "lspr24-g0-development-reference-input-v1"
OUTPUT_SCHEMA_VERSION = "lspr24-g0-python-reference-output-v1"
CANONICAL_VERSION = "lspr24-canonical-v1"
DEVELOPMENT_SCOPE = "development-visible-first-80-percent"

_TYPE_TAGS = {
    "null": 0x00,
    "bool": 0x01,
    "i64": 0x02,
    "u8": 0x03,
    "u16": 0x04,
    "u64": 0x05,
    "utf8": 0x06,
    "bytes": 0x07,
    "ip16": 0x08,
    "sha256": 0x09,
    "fixed_decimal_12": 0x0A,
}
_ROLE_ORDERS = {"source": 0, "destination": 1}
_I64_MIN = -(1 << 63)
_I64_MAX = (1 << 63) - 1
_U64_MAX = (1 << 64) - 1
_I128_MIN = -(1 << 127)
_I128_MAX = (1 << 127) - 1
_DECIMAL_QUANTUM = Decimal("0.000000000001")
_DECIMAL_SCALE = Decimal(1_000_000_000_000)


@dataclass(frozen=True)
class _PreparedRow:
    sort_key: tuple[bytes, int, int, bytes, int, int]
    output: dict[str, object]


def materialize_reference(
    input_path: str | Path,
    output_path: str | Path,
) -> dict[str, object]:
    """物化显式人工开发样本，并以排他创建写出参考 JSON。"""

    source = Path(input_path)
    destination = Path(output_path)
    if destination.exists():
        raise FileExistsError(f"参考输出已存在，拒绝覆盖：{destination}")

    document = _load_json_object(source)
    _require_exact_keys(document, {"schema_version", "scope", "rows"}, "输入根对象")
    if document["schema_version"] != INPUT_SCHEMA_VERSION:
        raise ValueError(f"输入 schema_version 必须为 {INPUT_SCHEMA_VERSION}")
    if document["scope"] != DEVELOPMENT_SCOPE:
        raise ValueError("Python 参考禁止访问最终区，scope 必须是显式开发可见范围")

    raw_rows = document["rows"]
    if not isinstance(raw_rows, list):
        raise ValueError("输入 rows 必须是数组")
    prepared = [_prepare_row(value, index) for index, value in enumerate(raw_rows)]
    prepared.sort(key=lambda row: row.sort_key)
    for previous, current in zip(prepared, prepared[1:]):
        if previous.sort_key == current.sort_key:
            raise ValueError("输入包含重复完整稳定键")

    output_rows = [row.output for row in prepared]
    row_hashes = [bytes.fromhex(_require_string(row["row_sha256"], "row_sha256")) for row in output_rows]
    result: dict[str, object] = {
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "canonical_version": CANONICAL_VERSION,
        "scope": DEVELOPMENT_SCOPE,
        "row_count": len(output_rows),
        "rows": output_rows,
        "dataset_semantic_sha256": _dataset_semantic_hash(row_hashes).hex(),
    }
    _write_json_exclusive(destination, result)
    return result


def compare_reference(
    expected_path: str | Path,
    actual_path: str | Path,
) -> dict[str, object]:
    """逐类型、逐字段硬比较两个参考输出，不使用浮点容差。"""

    try:
        expected = _load_json_object(Path(expected_path))
        actual = _load_json_object(Path(actual_path))
        _validate_reference_output(expected, "expected")
        _validate_reference_output(actual, "actual")
        if _canonical_json_bytes(expected) != _canonical_json_bytes(actual):
            raise ValueError("参考 JSON 字段或类型不同")
    except (OSError, ValueError) as error:
        raise ValueError(f"Python 参考硬一致比较失败：{error}") from error

    return {
        "schema_version": "lspr24-g0-python-reference-comparison-v1",
        "status": "PASS",
        "row_count": expected["row_count"],
        "dataset_semantic_sha256": expected["dataset_semantic_sha256"],
    }


def _prepare_row(value: object, input_index: int) -> _PreparedRow:
    row = _require_object(value, f"rows[{input_index}]")
    _require_exact_keys(
        row,
        {
            "protected_endpoint_id",
            "last_ns",
            "start_ns",
            "raw_flow_id",
            "endpoint_role_order",
            "source_row_index",
            "values",
        },
        f"rows[{input_index}]",
    )
    endpoint = _decode_hex(row["protected_endpoint_id"], 32, "protected_endpoint_id")
    raw_flow = _decode_hex(row["raw_flow_id"], 32, "raw_flow_id")
    last_ns = _require_bounded_int(row["last_ns"], _I64_MIN, _I64_MAX, "last_ns")
    start_ns = _require_bounded_int(row["start_ns"], _I64_MIN, _I64_MAX, "start_ns")
    if start_ns > last_ns:
        raise ValueError(f"rows[{input_index}] 的 start_ns 不能晚于 last_ns")
    role = _require_string(row["endpoint_role_order"], "endpoint_role_order")
    if role not in _ROLE_ORDERS:
        raise ValueError("endpoint_role_order 只能为 source 或 destination")
    source_row_index = _require_bounded_int(
        row["source_row_index"], 0, _U64_MAX, "source_row_index"
    )

    raw_values = row["values"]
    if not isinstance(raw_values, list):
        raise ValueError(f"rows[{input_index}].values 必须是数组")
    encoded_parts: list[bytes] = []
    normalized_values: list[dict[str, object]] = []
    for value_index, raw_value in enumerate(raw_values):
        encoded, normalized = _encode_input_value(
            raw_value, f"rows[{input_index}].values[{value_index}]"
        )
        encoded_parts.append(encoded)
        normalized_values.append(normalized)
    canonical = b"".join(encoded_parts)
    row_hash = hashlib.sha256(canonical).hexdigest()
    stable_key = {
        "protected_endpoint_id": endpoint.hex(),
        "last_ns": last_ns,
        "start_ns": start_ns,
        "raw_flow_id": raw_flow.hex(),
        "endpoint_role_order": role,
        "source_row_index": source_row_index,
    }
    return _PreparedRow(
        sort_key=(
            endpoint,
            last_ns,
            start_ns,
            raw_flow,
            _ROLE_ORDERS[role],
            source_row_index,
        ),
        output={
            "stable_key": stable_key,
            "values": normalized_values,
            "canonical_hex": canonical.hex(),
            "row_sha256": row_hash,
        },
    )


def _encode_input_value(value: object, context: str) -> tuple[bytes, dict[str, object]]:
    field = _require_object(value, context)
    field_type = _require_string(field.get("type"), f"{context}.type")
    if field_type not in _TYPE_TAGS:
        raise ValueError(f"{context}.type 不是冻结规范类型")

    if field_type == "null":
        _require_exact_keys(field, {"type"}, context)
        raw = b""
        normalized: dict[str, object] = {"type": field_type}
    elif field_type == "bool":
        _require_exact_keys(field, {"type", "value"}, context)
        if not isinstance(field["value"], bool):
            raise ValueError(f"{context}.value 必须是布尔值")
        raw = bytes([int(field["value"])])
        normalized = {"type": field_type, "value": field["value"]}
    elif field_type in {"i64", "u8", "u16", "u64"}:
        _require_exact_keys(field, {"type", "value"}, context)
        bounds = {
            "i64": (_I64_MIN, _I64_MAX, 8, True),
            "u8": (0, 0xFF, 1, False),
            "u16": (0, 0xFFFF, 2, False),
            "u64": (0, _U64_MAX, 8, False),
        }
        minimum, maximum, width, signed = bounds[field_type]
        integer = _require_bounded_int(field["value"], minimum, maximum, f"{context}.value")
        raw = integer.to_bytes(width, "big", signed=signed)
        normalized = {"type": field_type, "value": integer}
    elif field_type == "utf8":
        _require_exact_keys(field, {"type", "value"}, context)
        text = _require_string(field["value"], f"{context}.value")
        try:
            raw = text.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ValueError(f"{context}.value 不是有效 UTF-8") from error
        normalized = {"type": field_type, "value": text}
    elif field_type in {"bytes", "ip16", "sha256"}:
        _require_exact_keys(field, {"type", "value_hex"}, context)
        required_length = {"bytes": None, "ip16": 16, "sha256": 32}[field_type]
        raw = _decode_hex(field["value_hex"], required_length, f"{context}.value_hex")
        normalized = {"type": field_type, "value_hex": raw.hex()}
    else:
        _require_exact_keys(field, {"type", "value"}, context)
        decimal_text = _require_string(field["value"], f"{context}.value")
        quantized_integer = _quantize_decimal_12(decimal_text, context)
        raw = quantized_integer.to_bytes(16, "big", signed=True)
        normalized = {
            "type": field_type,
            "quantized_integer": str(quantized_integer),
        }

    if len(raw) > 0xFFFF_FFFF:
        raise ValueError(f"{context} 的规范值长度超过 u32")
    encoded = bytes([_TYPE_TAGS[field_type]]) + len(raw).to_bytes(4, "big") + raw
    return encoded, normalized


def _encode_normalized_value(value: object, context: str) -> bytes:
    field = _require_object(value, context)
    if field.get("type") != "fixed_decimal_12":
        encoded, _ = _encode_input_value(field, context)
        return encoded

    _require_exact_keys(field, {"type", "quantized_integer"}, context)
    integer_text = _require_string(field["quantized_integer"], f"{context}.quantized_integer")
    try:
        integer = int(integer_text, 10)
    except ValueError as error:
        raise ValueError(f"{context}.quantized_integer 必须是十进制整数字符串") from error
    if str(integer) != integer_text or not _I128_MIN <= integer <= _I128_MAX:
        raise ValueError(f"{context}.quantized_integer 不是规范 i128 字符串")
    raw = integer.to_bytes(16, "big", signed=True)
    return bytes([_TYPE_TAGS["fixed_decimal_12"]]) + len(raw).to_bytes(4, "big") + raw


def _quantize_decimal_12(value: str, context: str) -> int:
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"{context}.value 不是十进制定点字符串") from error
    if not decimal_value.is_finite():
        raise ValueError(f"{context}.value 不能是 NaN 或无穷")

    digits = len(decimal_value.as_tuple().digits)
    try:
        with localcontext() as decimal_context:
            decimal_context.prec = max(50, digits + abs(decimal_value.as_tuple().exponent) + 20)
            quantized = decimal_value.quantize(_DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)
            integer = int(quantized * _DECIMAL_SCALE)
    except InvalidOperation as error:
        raise ValueError(f"{context}.value 无法量化为十二位小数") from error
    if quantized.is_zero():
        integer = 0
    if not _I128_MIN <= integer <= _I128_MAX:
        raise ValueError(f"{context}.value 的定点整数超过 i128")
    return integer


def _validate_reference_output(document: dict[str, object], context: str) -> None:
    _require_exact_keys(
        document,
        {
            "schema_version",
            "canonical_version",
            "scope",
            "row_count",
            "rows",
            "dataset_semantic_sha256",
        },
        context,
    )
    if document["schema_version"] != OUTPUT_SCHEMA_VERSION:
        raise ValueError(f"{context}.schema_version 不匹配")
    if document["canonical_version"] != CANONICAL_VERSION:
        raise ValueError(f"{context}.canonical_version 不匹配")
    if document["scope"] != DEVELOPMENT_SCOPE:
        raise ValueError(f"{context} 不是开发可见范围")
    rows = document["rows"]
    if not isinstance(rows, list):
        raise ValueError(f"{context}.rows 必须是数组")
    row_count = _require_bounded_int(document["row_count"], 0, _U64_MAX, f"{context}.row_count")
    if row_count != len(rows):
        raise ValueError(f"{context}.row_count 与 rows 长度不一致")

    row_hashes: list[bytes] = []
    previous_key: tuple[bytes, int, int, bytes, int, int] | None = None
    for index, raw_row in enumerate(rows):
        row_context = f"{context}.rows[{index}]"
        row = _require_object(raw_row, row_context)
        _require_exact_keys(row, {"stable_key", "values", "canonical_hex", "row_sha256"}, row_context)
        stable_key = _parse_output_stable_key(row["stable_key"], row_context)
        if previous_key is not None and stable_key <= previous_key:
            raise ValueError(f"{row_context} 未按完整稳定键严格升序排列")
        previous_key = stable_key

        values = row["values"]
        if not isinstance(values, list):
            raise ValueError(f"{row_context}.values 必须是数组")
        reconstructed = b"".join(
            _encode_normalized_value(value, f"{row_context}.values[{value_index}]")
            for value_index, value in enumerate(values)
        )
        canonical = _decode_hex(row["canonical_hex"], None, f"{row_context}.canonical_hex")
        if canonical != reconstructed:
            raise ValueError(f"{row_context}.canonical_hex 与规范值不一致")
        row_hash = _decode_hex(row["row_sha256"], 32, f"{row_context}.row_sha256")
        if row_hash != hashlib.sha256(canonical).digest():
            raise ValueError(f"{row_context}.row_sha256 无法复算")
        row_hashes.append(row_hash)

    dataset_hash = _decode_hex(
        document["dataset_semantic_sha256"],
        32,
        f"{context}.dataset_semantic_sha256",
    )
    if dataset_hash != _dataset_semantic_hash(row_hashes):
        raise ValueError(f"{context}.dataset_semantic_sha256 无法复算")


def _parse_output_stable_key(
    value: object, context: str
) -> tuple[bytes, int, int, bytes, int, int]:
    key = _require_object(value, f"{context}.stable_key")
    _require_exact_keys(
        key,
        {
            "protected_endpoint_id",
            "last_ns",
            "start_ns",
            "raw_flow_id",
            "endpoint_role_order",
            "source_row_index",
        },
        f"{context}.stable_key",
    )
    endpoint = _decode_hex(key["protected_endpoint_id"], 32, "protected_endpoint_id")
    raw_flow = _decode_hex(key["raw_flow_id"], 32, "raw_flow_id")
    last_ns = _require_bounded_int(key["last_ns"], _I64_MIN, _I64_MAX, "last_ns")
    start_ns = _require_bounded_int(key["start_ns"], _I64_MIN, _I64_MAX, "start_ns")
    role = _require_string(key["endpoint_role_order"], "endpoint_role_order")
    if role not in _ROLE_ORDERS:
        raise ValueError("endpoint_role_order 不是冻结枚举")
    source_row_index = _require_bounded_int(
        key["source_row_index"], 0, _U64_MAX, "source_row_index"
    )
    return endpoint, last_ns, start_ns, raw_flow, _ROLE_ORDERS[role], source_row_index


def _dataset_semantic_hash(row_hashes: list[bytes]) -> bytes:
    digest = hashlib.sha256()
    for row_hash in row_hashes:
        digest.update((32).to_bytes(4, "big"))
        digest.update(row_hash)
    return digest.digest()


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"JSON 输入无效：{path}") from error
    return _require_object(value, str(path))


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"JSON 不允许非有限常量 {value}")


def _write_json_exclusive(path: Path, value: dict[str, object]) -> None:
    payload = _canonical_json_bytes(value) + b"\n"
    try:
        with path.open("xb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError as error:
        raise FileExistsError(f"参考输出已存在，拒绝覆盖：{path}") from error


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _require_object(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} 必须是 JSON 对象")
    return value


def _require_exact_keys(value: dict[str, object], expected: set[str], context: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(str(key) for key in actual - expected)
        raise ValueError(f"{context} 字段集合不完整：缺少 {missing}，未知 {unknown}")


def _require_string(value: object, context: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{context} 必须是字符串")
    return value


def _require_bounded_int(value: object, minimum: int, maximum: int, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context} 必须是整数")
    if not minimum <= value <= maximum:
        raise ValueError(f"{context} 超出冻结整数范围")
    return value


def _decode_hex(value: object, length: int | None, context: str) -> bytes:
    text = _require_string(value, context)
    if len(text) % 2 != 0 or any(character not in string.hexdigits for character in text):
        raise ValueError(f"{context} 必须是偶数字符十六进制字符串")
    decoded = bytes.fromhex(text)
    if length is not None and len(decoded) != length:
        raise ValueError(f"{context} 必须解码为 {length} 字节")
    return decoded


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LSPR24 G0 人工开发样本 Python 参考")
    subparsers = parser.add_subparsers(dest="command", required=True)

    materialize_parser = subparsers.add_parser("materialize", help="物化显式开发样本")
    materialize_parser.add_argument("--input", required=True, type=Path)
    materialize_parser.add_argument("--output", required=True, type=Path)

    compare_parser = subparsers.add_parser("compare", help="执行无容差硬一致比较")
    compare_parser.add_argument("--expected", required=True, type=Path)
    compare_parser.add_argument("--actual", required=True, type=Path)
    return parser


def main() -> int:
    """运行单一开发参考命令入口。"""

    parser = _build_parser()
    arguments = parser.parse_args()
    try:
        if arguments.command == "materialize":
            materialized = materialize_reference(arguments.input, arguments.output)
            result = {
                "status": "PASS",
                "row_count": materialized["row_count"],
                "dataset_semantic_sha256": materialized["dataset_semantic_sha256"],
            }
        else:
            result = compare_reference(arguments.expected, arguments.actual)
    except (OSError, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
