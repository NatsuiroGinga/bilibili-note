"""生成式标签的严格解析。"""

from __future__ import annotations

import json
from dataclasses import dataclass

from flow_probe.schemas import BinaryLabel


@dataclass(frozen=True)
class ParsedPrediction:
    """一次生成的解析结果。"""

    label: BinaryLabel | None
    is_valid: bool
    error: str | None


def parse_prediction(text: str) -> ParsedPrediction:
    """只接受单个、单键且标签值合法的 JSON 对象。"""
    try:
        payload = json.loads(text.strip())
    except (json.JSONDecodeError, TypeError) as error:
        return ParsedPrediction(
            None, False, f"JSON 解析失败：{error.msg if hasattr(error, 'msg') else error}"
        )

    if not isinstance(payload, dict):
        return ParsedPrediction(None, False, "输出必须是 JSON 对象")
    if set(payload) != {"label"}:
        return ParsedPrediction(None, False, "JSON 对象只能包含 label 键")
    label = payload["label"]
    if label not in {"benign", "malicious"}:
        return ParsedPrediction(None, False, f"未知标签：{label!r}")
    return ParsedPrediction(label, True, None)
