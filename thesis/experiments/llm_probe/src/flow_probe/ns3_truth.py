"""验证 ns-3 队列真值 CSV 的字段、时序、标签与守恒关系。"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCHEMA_VERSION = "flow_probe_ns3_queue_v4"
SUMMARY_SCHEMA_VERSION = "flow_probe_ns3_truth_validation_v2"
DEFAULT_WINDOW_COUNT = 120
WINDOW_SECONDS = Decimal("0.1")
INITIAL_CAPACITY_BPS = Decimal("5000000")
SHIFTED_CAPACITY_BPS = Decimal("2500000")
INITIAL_SERVICE_BUDGET_BYTES = Decimal("62500")
SHIFTED_SERVICE_BUDGET_BYTES = Decimal("31250")
ERROR_STREAM = Decimal("500")
RANDOM_LOSS_ERROR_RATE = Decimal("0.01")
JITTER_STREAM_BASE = Decimal("100")
JITTER_MAX_MS = Decimal("40")

CSV_FIELDS = (
    "schema_version",
    "scenario_id",
    "topology_id",
    "queue_model",
    "group_id",
    "seed",
    "run",
    "jitter_stream_base",
    "jitter_max_ms",
    "error_stream",
    "downstream_error_rate",
    "window_index",
    "window_start_s",
    "window_end_s",
    "is_attack",
    "attack_exposure_fraction",
    "traffic_phase",
    "label_primary",
    "label_family",
    "label_subtype",
    "capacity_start_bps",
    "capacity_end_bps",
    "configured_capacity_integral_link_bytes",
    "queue_limit_packets",
    "queue_start_l3_bytes",
    "queue_end_l3_bytes",
    "qdisc_received_l3_bytes",
    "qdisc_enqueued_l3_bytes",
    "qdisc_dequeued_l3_bytes",
    "qdisc_dropped_before_enqueue_l3_bytes",
    "qdisc_dropped_after_dequeue_l3_bytes",
    "device_tx_drop_ppp_frame_bytes",
    "downstream_error_loss_ppp_frame_bytes",
    "sink_received_app_payload_bytes",
    "queue_start_packets",
    "queue_end_packets",
    "qdisc_received_packets",
    "qdisc_enqueued_packets",
    "qdisc_dequeued_packets",
    "qdisc_dropped_before_enqueue_packets",
    "qdisc_dropped_after_dequeue_packets",
    "device_tx_drop_packets",
    "downstream_error_loss_packets",
    "sink_received_packets",
    "queue_balance_residual_l3_bytes",
    "queue_balance_residual_packets",
)

TEXT_FIELDS = (
    "schema_version",
    "scenario_id",
    "topology_id",
    "queue_model",
    "group_id",
    "traffic_phase",
    "label_primary",
    "label_family",
    "label_subtype",
)

NUMERIC_FIELDS = tuple(field for field in CSV_FIELDS if field not in TEXT_FIELDS)
INTEGER_FIELDS = frozenset(
    {
        "seed",
        "run",
        "jitter_stream_base",
        "error_stream",
        "window_index",
        "is_attack",
        "capacity_start_bps",
        "capacity_end_bps",
        "queue_limit_packets",
        "queue_start_l3_bytes",
        "queue_end_l3_bytes",
        "qdisc_received_l3_bytes",
        "qdisc_enqueued_l3_bytes",
        "qdisc_dequeued_l3_bytes",
        "qdisc_dropped_before_enqueue_l3_bytes",
        "qdisc_dropped_after_dequeue_l3_bytes",
        "device_tx_drop_ppp_frame_bytes",
        "downstream_error_loss_ppp_frame_bytes",
        "sink_received_app_payload_bytes",
        "queue_start_packets",
        "queue_end_packets",
        "qdisc_received_packets",
        "qdisc_enqueued_packets",
        "qdisc_dequeued_packets",
        "qdisc_dropped_before_enqueue_packets",
        "qdisc_dropped_after_dequeue_packets",
        "device_tx_drop_packets",
        "downstream_error_loss_packets",
        "sink_received_packets",
        "queue_balance_residual_l3_bytes",
        "queue_balance_residual_packets",
    }
)

SCENARIOS = frozenset(
    {
        "benign-low",
        "benign-high",
        "benign-capacity-shift",
        "benign-random-loss",
        "dos-udp-medium",
        "dos-udp-high",
        "dos-udp-capacity-shift",
    }
)
DOS_SCENARIOS = frozenset({"dos-udp-medium", "dos-udp-high", "dos-udp-capacity-shift"})
CAPACITY_SHIFT_SCENARIOS = frozenset({"benign-capacity-shift", "dos-udp-capacity-shift"})
NO_QUEUE_DROP_SCENARIOS = frozenset({"benign-low", "benign-high", "benign-random-loss"})


class NS3TruthValidationError(ValueError):
    """ns-3 队列真值违反固定数据契约。"""


@dataclass(frozen=True, slots=True)
class _Window:
    path: Path
    row_number: int
    text: dict[str, str]
    numbers: dict[str, Decimal]

    @property
    def group_id(self) -> str:
        return self.text["group_id"]

    @property
    def scenario(self) -> str:
        return self.text["scenario_id"]

    @property
    def window_index(self) -> int:
        return int(self.numbers["window_index"])


def _error(
    path: Path | str,
    group_id: str,
    rule: str,
    detail: str,
) -> NS3TruthValidationError:
    group = group_id or "<未知>"
    return NS3TruthValidationError(f"文件 {path}，组 {group}，规则 {rule}：{detail}")


def _validate_header(path: Path, fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise _error(path, "<未读取>", "字段契约", "CSV 缺少表头")

    counts = Counter(fieldnames)
    missing = sorted(set(CSV_FIELDS).difference(fieldnames))
    extra = sorted(set(fieldnames).difference(CSV_FIELDS))
    duplicates = sorted(field for field, count in counts.items() if count > 1)
    if len(fieldnames) != len(CSV_FIELDS) or missing or extra or duplicates:
        details = [f"应有 {len(CSV_FIELDS)} 个命名字段，实际 {len(fieldnames)} 个"]
        if missing:
            details.append(f"缺少：{', '.join(missing)}")
        if extra:
            details.append(f"多出：{', '.join(extra)}")
        if duplicates:
            details.append(f"重复：{', '.join(duplicates)}")
        raise _error(path, "<未读取>", "字段契约", "；".join(details))


def _parse_number(path: Path, row_number: int, group_id: str, field: str, raw: str) -> Decimal:
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as error:
        raise _error(
            path,
            group_id,
            "有限数值",
            f"第 {row_number} 行字段 {field} 无法解析：{raw!r}",
        ) from error
    if not value.is_finite():
        raise _error(
            path,
            group_id,
            "有限数值",
            f"第 {row_number} 行字段 {field} 不是有限数",
        )
    if field in INTEGER_FIELDS and value != value.to_integral_value():
        raise _error(
            path,
            group_id,
            "计数字段",
            f"第 {row_number} 行字段 {field} 必须为整数，实际为 {raw!r}",
        )
    if value < 0:
        raise _error(
            path,
            group_id,
            "非负数值",
            f"第 {row_number} 行字段 {field} 为负数 {raw!r}",
        )
    return value


def _parse_window(path: Path, row_number: int, row: dict[str | None, str | None]) -> _Window:
    group_id = str(row.get("group_id") or "").strip()
    if None in row or any(row.get(field) is None for field in CSV_FIELDS):
        raise _error(
            path,
            group_id,
            "字段契约",
            f"第 {row_number} 行不是恰好 {len(CSV_FIELDS)} 列",
        )

    text = {field: str(row[field]).strip() for field in TEXT_FIELDS}
    for field, value in text.items():
        if not value:
            raise _error(path, group_id, "字段契约", f"第 {row_number} 行字段 {field} 不能为空")

    if text["schema_version"] != SCHEMA_VERSION:
        raise _error(
            path,
            group_id,
            "模式版本",
            f"第 {row_number} 行应为 {SCHEMA_VERSION}，实际为 {text['schema_version']}",
        )
    if text["scenario_id"] not in SCENARIOS:
        raise _error(
            path,
            group_id,
            "场景集合",
            f"第 {row_number} 行包含未知场景 {text['scenario_id']}",
        )

    numbers = {
        field: _parse_number(path, row_number, group_id, field, str(row[field]))
        for field in NUMERIC_FIELDS
    }
    return _Window(
        path=path,
        row_number=row_number,
        text=text,
        numbers=numbers,
    )


def _validate_row(window: _Window) -> None:
    number = window.numbers
    received_bytes = number["qdisc_received_l3_bytes"]
    decomposed_bytes = (
        number["qdisc_enqueued_l3_bytes"] + number["qdisc_dropped_before_enqueue_l3_bytes"]
    )
    if received_bytes != decomposed_bytes:
        raise _error(
            window.path,
            window.group_id,
            "流量分解",
            (
                f"第 {window.row_number} 行 qdisc_received_l3_bytes={received_bytes}，"
                f"复算值为 {decomposed_bytes}"
            ),
        )

    received_packets = number["qdisc_received_packets"]
    decomposed_packets = (
        number["qdisc_enqueued_packets"] + number["qdisc_dropped_before_enqueue_packets"]
    )
    if received_packets != decomposed_packets:
        raise _error(
            window.path,
            window.group_id,
            "包级流量分解",
            (
                f"第 {window.row_number} 行 qdisc_received_packets={received_packets}，"
                f"复算值为 {decomposed_packets}"
            ),
        )

    recomputed_l3_residual = (
        number["queue_end_l3_bytes"]
        - number["queue_start_l3_bytes"]
        - received_bytes
        + number["qdisc_dequeued_l3_bytes"]
        + number["qdisc_dropped_before_enqueue_l3_bytes"]
    )
    if recomputed_l3_residual != 0:
        raise _error(
            window.path,
            window.group_id,
            "队列守恒",
            f"第 {window.row_number} 行复算 L3 字节残差为 {recomputed_l3_residual}",
        )
    recomputed_packet_residual = (
        number["queue_end_packets"]
        - number["queue_start_packets"]
        - received_packets
        + number["qdisc_dequeued_packets"]
        + number["qdisc_dropped_before_enqueue_packets"]
    )
    if recomputed_packet_residual != 0:
        raise _error(
            window.path,
            window.group_id,
            "包级守恒",
            f"第 {window.row_number} 行复算包残差为 {recomputed_packet_residual}",
        )
    if (
        number["queue_balance_residual_l3_bytes"] != 0
        or number["queue_balance_residual_packets"] != 0
    ):
        raise _error(
            window.path,
            window.group_id,
            "保存残差",
            f"第 {window.row_number} 行保存的字节或包残差不为零",
        )
    if number["device_tx_drop_ppp_frame_bytes"] != 0 or number["device_tx_drop_packets"] != 0:
        raise _error(
            window.path,
            window.group_id,
            "隐藏设备丢弃",
            f"第 {window.row_number} 行设备发送队列仍有丢弃",
        )


def _validate_group_constants(windows: list[_Window]) -> None:
    first = windows[0]
    for field in ("scenario_id", "topology_id", "queue_model"):
        expected = first.text[field]
        for window in windows[1:]:
            if window.text[field] != expected:
                raise _error(
                    window.path,
                    window.group_id,
                    "组内常量",
                    f"第 {window.row_number} 行字段 {field} 发生变化",
                )
    for field in ("seed", "run", "jitter_stream_base", "jitter_max_ms"):
        expected_number = first.numbers[field]
        for window in windows[1:]:
            if window.numbers[field] != expected_number:
                raise _error(
                    window.path,
                    window.group_id,
                    "组内常量",
                    f"第 {window.row_number} 行字段 {field} 发生变化",
                )

    expected_jitter = {
        "jitter_stream_base": JITTER_STREAM_BASE,
        "jitter_max_ms": JITTER_MAX_MS,
    }
    for field, expected_number in expected_jitter.items():
        actual_number = first.numbers[field]
        if actual_number != expected_number:
            raise _error(
                first.path,
                first.group_id,
                "抖动配置",
                f"字段 {field} 应为 {expected_number}，实际为 {actual_number}",
            )


def _complete_windows(windows: list[_Window], expected_windows: int) -> list[_Window]:
    first = windows[0]
    if len(windows) != expected_windows:
        raise _error(
            first.path,
            first.group_id,
            "完整窗口",
            f"应有 {expected_windows} 个窗口，实际为 {len(windows)} 个",
        )
    actual_indices = [window.window_index for window in windows]
    expected_indices = list(range(expected_windows))
    if actual_indices != expected_indices:
        raise _error(
            first.path,
            first.group_id,
            "窗口索引",
            f"window_index 必须连续为 0 至 {expected_windows - 1}",
        )
    return windows


def _validate_timeline(windows: list[_Window]) -> None:
    for window in windows:
        duration = window.numbers["window_end_s"] - window.numbers["window_start_s"]
        if duration != WINDOW_SECONDS:
            raise _error(
                window.path,
                window.group_id,
                "窗口长度",
                f"第 {window.row_number} 行窗口长度为 {duration} 秒，应为 {WINDOW_SECONDS} 秒",
            )
    for previous, current in zip(windows, windows[1:], strict=False):
        if previous.numbers["window_end_s"] != current.numbers["window_start_s"]:
            raise _error(
                current.path,
                current.group_id,
                "窗口连续",
                f"窗口 {previous.window_index} 与 {current.window_index} 的时间边界不连续",
            )
        if previous.numbers["queue_end_bytes"] != current.numbers["queue_start_bytes"]:
            raise _error(
                current.path,
                current.group_id,
                "队列连续",
                f"窗口 {previous.window_index} 末队列与窗口 {current.window_index} 初队列不一致",
            )


def _validate_labels(windows: list[_Window]) -> None:
    scenario = windows[0].scenario
    for window in windows:
        attack_active = scenario in DOS_SCENARIOS and window.window_index >= 50
        expected = (
            (Decimal(1), "malicious", "dos", "udp")
            if attack_active
            else (Decimal(0), "benign", "benign", "benign")
        )
        actual = (
            window.numbers["is_attack"],
            window.text["label_primary"],
            window.text["label_family"],
            window.text["label_subtype"],
        )
        if actual != expected:
            raise _error(
                window.path,
                window.group_id,
                "标签时序",
                f"窗口 {window.window_index} 标签应为 {expected}，实际为 {actual}",
            )

        exposure = window.numbers["attack_exposure_fraction"]
        phase = window.text["traffic_phase"]
        if scenario not in DOS_SCENARIOS or window.window_index < 50:
            valid_exposure = exposure == 0 and phase == "benign"
            expected_exposure = "exposure=0、phase=benign"
        elif window.window_index == 50:
            valid_exposure = 0 < exposure < 1 and phase == "transition"
            expected_exposure = "exposure 位于 (0, 1)、phase=transition"
        else:
            valid_exposure = exposure == 1 and phase == "attack"
            expected_exposure = "exposure=1、phase=attack"
        if not valid_exposure:
            raise _error(
                window.path,
                window.group_id,
                "攻击暴露时序",
                (
                    f"窗口 {window.window_index} 应为 {expected_exposure}，"
                    f"实际为 exposure={exposure}、phase={phase}"
                ),
            )

        attack_activity = sum(
            (
                window.numbers[field]
                for field in (
                    "offered_bytes",
                    "queue_start_bytes",
                    "queue_end_bytes",
                    "departed_bytes",
                    "dropped_before_enqueue_bytes",
                    "dropped_after_dequeue_bytes",
                    "sink_received_bytes",
                )
            ),
            start=Decimal(0),
        )
        if exposure > 0 and attack_activity == 0:
            raise _error(
                window.path,
                window.group_id,
                "攻击活动",
                f"窗口 {window.window_index} 有攻击暴露标签，但所有流量与队列活动均为零",
            )


def _expected_capacity(scenario: str, window_index: int) -> tuple[Decimal, Decimal, Decimal]:
    if scenario not in CAPACITY_SHIFT_SCENARIOS or window_index < 59:
        return (
            INITIAL_CAPACITY_BPS,
            INITIAL_CAPACITY_BPS,
            INITIAL_SERVICE_BUDGET_BYTES,
        )
    if window_index == 59:
        return (
            INITIAL_CAPACITY_BPS,
            SHIFTED_CAPACITY_BPS,
            INITIAL_SERVICE_BUDGET_BYTES,
        )
    return (
        SHIFTED_CAPACITY_BPS,
        SHIFTED_CAPACITY_BPS,
        SHIFTED_SERVICE_BUDGET_BYTES,
    )


def _validate_capacity(windows: list[_Window]) -> None:
    scenario = windows[0].scenario
    for window in windows:
        expected = _expected_capacity(scenario, window.window_index)
        actual = (
            window.numbers["capacity_start_bps"],
            window.numbers["capacity_end_bps"],
            window.numbers["service_budget_bytes"],
        )
        if actual != expected:
            raise _error(
                window.path,
                window.group_id,
                "容量预算",
                f"窗口 {window.window_index} 应为 {expected}，实际为 {actual}",
            )


def _validate_error_model(windows: list[_Window]) -> None:
    scenario = windows[0].scenario
    expected_rate = RANDOM_LOSS_ERROR_RATE if scenario == "benign-random-loss" else Decimal(0)
    expected = (ERROR_STREAM, expected_rate)
    for window in windows:
        actual = (
            window.numbers["error_stream"],
            window.numbers["downstream_error_rate"],
        )
        if actual != expected:
            raise _error(
                window.path,
                window.group_id,
                "误码配置",
                f"窗口 {window.window_index} 应为 {expected}，实际为 {actual}",
            )


def _queue_drop_bytes(window: _Window) -> Decimal:
    return (
        window.numbers["dropped_before_enqueue_bytes"]
        + window.numbers["dropped_after_dequeue_bytes"]
    )


def _queue_drop_packets(window: _Window) -> Decimal:
    return (
        window.numbers["dropped_before_enqueue_packets"]
        + window.numbers["dropped_after_dequeue_packets"]
    )


def _validate_drop_rules(windows: list[_Window]) -> None:
    first = windows[0]
    scenario = first.scenario
    queue_drop_bytes = sum((_queue_drop_bytes(window) for window in windows), start=Decimal(0))
    queue_drop_packets = sum(
        (_queue_drop_packets(window) for window in windows),
        start=Decimal(0),
    )

    if scenario in NO_QUEUE_DROP_SCENARIOS and (queue_drop_bytes != 0 or queue_drop_packets != 0):
        raise _error(
            first.path,
            first.group_id,
            "队列规则丢弃",
            f"场景 {scenario} 不得出现队列规则丢弃",
        )
    if scenario == "benign-capacity-shift":
        post_shift_bytes = sum(
            (_queue_drop_bytes(window) for window in windows if window.window_index >= 60),
            start=Decimal(0),
        )
        if post_shift_bytes == 0:
            raise _error(
                first.path,
                first.group_id,
                "队列规则丢弃",
                "benign-capacity-shift 在容量下降后必须出现队列规则丢弃",
            )
    if scenario in DOS_SCENARIOS:
        attack_drop_bytes = sum(
            (_queue_drop_bytes(window) for window in windows if window.window_index >= 50),
            start=Decimal(0),
        )
        if attack_drop_bytes == 0:
            raise _error(
                first.path,
                first.group_id,
                "队列规则丢弃",
                f"场景 {scenario} 在攻击开始后必须出现队列规则丢弃",
            )

    downstream_bytes = sum(
        (window.numbers["downstream_error_loss_bytes"] for window in windows),
        start=Decimal(0),
    )
    downstream_packets = sum(
        (window.numbers["downstream_error_loss_packets"] for window in windows),
        start=Decimal(0),
    )
    if scenario == "benign-random-loss":
        if downstream_bytes == 0 and downstream_packets == 0:
            raise _error(
                first.path,
                first.group_id,
                "下游误码丢弃",
                "benign-random-loss 每组必须出现下游误码丢弃",
            )
    elif downstream_bytes != 0 or downstream_packets != 0:
        raise _error(
            first.path,
            first.group_id,
            "下游误码丢弃",
            f"场景 {scenario} 不得出现下游误码丢弃",
        )


def _validate_group(windows: list[_Window], expected_windows: int) -> list[_Window]:
    _validate_group_constants(windows)
    complete = _complete_windows(windows, expected_windows)
    _validate_timeline(complete)
    _validate_labels(complete)
    _validate_capacity(complete)
    _validate_error_model(complete)
    _validate_drop_rules(complete)
    return complete


def validate_ns3_truth_paths(
    input_paths: Sequence[Path],
    *,
    expected_windows: int = DEFAULT_WINDOW_COUNT,
) -> dict[str, object]:
    """验证一个或多个 ns-3 队列真值 CSV，并返回确定性摘要。"""
    paths = [Path(path) for path in input_paths]
    if not paths:
        raise _error("<输入>", "<未知>", "输入文件", "至少需要一个 CSV 路径")
    if expected_windows <= 0:
        raise ValueError("expected_windows 必须为正整数")

    groups: dict[str, list[_Window]] = {}
    group_sources: dict[str, Path] = {}
    for path in paths:
        file_row_count = 0
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            _validate_header(path, reader.fieldnames)
            for row in reader:
                file_row_count += 1
                window = _parse_window(path, reader.line_num, row)
                _validate_row(window)
                previous_source = group_sources.setdefault(window.group_id, path)
                if previous_source != path:
                    raise _error(
                        path,
                        window.group_id,
                        "组标识唯一",
                        f"同一 group_id 已在文件 {previous_source} 中使用",
                    )
                groups.setdefault(window.group_id, []).append(window)
        if file_row_count == 0:
            raise _error(path, "<未读取>", "完整窗口", "CSV 不包含数据行")

    ordered_groups = {
        group_id: _validate_group(windows, expected_windows)
        for group_id, windows in sorted(groups.items())
    }
    scenario_window_counts = Counter(
        window.scenario for windows in ordered_groups.values() for window in windows
    )
    queue_drop_bytes = sum(
        (_queue_drop_bytes(window) for windows in ordered_groups.values() for window in windows),
        start=Decimal(0),
    )
    downstream_error_loss_bytes = sum(
        (
            window.numbers["downstream_error_loss_bytes"]
            for windows in ordered_groups.values()
            for window in windows
        ),
        start=Decimal(0),
    )
    nonzero_residual_count = sum(
        window.numbers["queue_balance_residual_bytes"] != 0
        for windows in ordered_groups.values()
        for window in windows
    )
    transition_window_count = sum(
        window.text["traffic_phase"] == "transition"
        for windows in ordered_groups.values()
        for window in windows
    )
    total_window_count = sum(len(windows) for windows in ordered_groups.values())
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "validation_status": "passed",
        "file_count": len(paths),
        "group_count": len(ordered_groups),
        "total_window_count": total_window_count,
        "scenario_window_counts": {
            scenario: scenario_window_counts.get(scenario, 0) for scenario in sorted(SCENARIOS)
        },
        "queue_drop_bytes": int(queue_drop_bytes),
        "downstream_error_loss_bytes": int(downstream_error_loss_bytes),
        "nonzero_residual_count": nonzero_residual_count,
        "transition_window_count": transition_window_count,
    }


def validate_ns3_truth_file(
    input_path: Path,
    *,
    expected_windows: int = DEFAULT_WINDOW_COUNT,
) -> dict[str, object]:
    """验证单个 ns-3 队列真值 CSV。"""
    return validate_ns3_truth_paths([input_path], expected_windows=expected_windows)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 ns-3 队列真值 CSV")
    parser.add_argument("inputs", metavar="CSV", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, help="可选的 UTF-8 JSON 摘要路径")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        summary = validate_ns3_truth_paths(args.inputs)
        rendered = json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
    except (NS3TruthValidationError, OSError) as error:
        print(f"ns-3 真值验证失败：{error}", file=sys.stderr)
        return 1
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
