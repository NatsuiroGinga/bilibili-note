"""数据集适配器共享的严格转换工具。"""

from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path


class DatasetSchemaError(ValueError):
    """原始数据集字段或标签不满足已核验契约。"""


def source_name(source_file: str) -> str:
    """返回稳定且不含本机目录的源文件名。"""
    name = Path(source_file).name.strip()
    if not name:
        raise DatasetSchemaError("源文件名不能为空")
    return name


def sample_id(dataset: str, source_file: str, row_number: int) -> str:
    """构造不包含标签的稳定样本标识。"""
    if row_number < 0:
        raise DatasetSchemaError("row_number 不能为负数")
    return f"{dataset}:{source_name(source_file)}:{row_number}"


def parse_binary_label(dataset: str, value: object) -> str:
    """只接受数据发布方定义的二元数值标签。"""
    normalized = str(int(value)) if isinstance(value, bool) else str(value).strip().lower()
    mapping = {"0": "benign", "0.0": "benign", "1": "malicious", "1.0": "malicious"}
    try:
        return mapping[normalized]
    except KeyError as error:
        raise DatasetSchemaError(f"{dataset} 出现未知标签：{value!r}") from error


def require_columns(dataset: str, row: Mapping[str, object], columns: tuple[str, ...]) -> None:
    """确认真实表头包含适配器依赖的全部列。"""
    missing = [column for column in columns if column not in row]
    if missing:
        raise DatasetSchemaError(f"{dataset} 缺少必需列：{', '.join(missing)}")


def number(dataset: str, row: Mapping[str, object], column: str) -> float | None:
    """将数值列转换为有限浮点数，空值保持为 None。"""
    value = row[column]
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise DatasetSchemaError(f"{dataset} 列 {column} 含非数值：{value!r}") from error
    if not math.isfinite(result):
        return None
    return result


def add_if_complete(*values: float | None) -> float | None:
    """只在所有分量可观测时求和，避免把未知值当零。"""
    if any(value is None for value in values):
        return None
    return float(sum(value for value in values if value is not None))


def mean_if_present(*values: float | None) -> float | None:
    """计算可观测值均值；全部缺失时返回 None。"""
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def min_if_present(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    return min(present) if present else None


def max_if_present(*values: float | None) -> float | None:
    present = [value for value in values if value is not None]
    return max(present) if present else None
