import csv
import json
from pathlib import Path

import pytest

from flow_probe.ns3_truth import NS3TruthValidationError, main, validate_ns3_truth_paths

FIELDS = (
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
SCENARIOS = (
    "benign-low",
    "benign-high",
    "benign-capacity-shift",
    "benign-random-loss",
    "dos-udp-medium",
    "dos-udp-high",
    "dos-udp-capacity-shift",
)


def _rows(scenario: str = "benign-low") -> list[dict[str, object]]:
    capacity_shift = scenario in {"benign-capacity-shift", "dos-udp-capacity-shift"}
    is_dos = scenario.startswith("dos-")
    rows: list[dict[str, object]] = []
    for index in range(120):
        attack_active = is_dos and index >= 50
        transition = is_dos and index == 50
        attack_exposure = 0.5 if transition else int(is_dos and index >= 51)
        traffic_phase = "transition" if transition else "attack" if attack_active else "benign"
        queue_drop = (is_dos and index == 50) or (
            scenario == "benign-capacity-shift" and index == 60
        )
        random_loss = scenario == "benign-random-loss" and index == 10
        dropped_before_bytes = 100 if queue_drop else 0
        dropped_before_packets = 1 if queue_drop else 0
        enqueued_bytes = 1000 - dropped_before_bytes
        enqueued_packets = 1
        received_packets = enqueued_packets + dropped_before_packets

        if capacity_shift and index == 59:
            capacity_start = 5_000_000
            capacity_end = 2_500_000
            service_budget = 62_500
        elif capacity_shift and index >= 60:
            capacity_start = 2_500_000
            capacity_end = 2_500_000
            service_budget = 31_250
        else:
            capacity_start = 5_000_000
            capacity_end = 5_000_000
            service_budget = 62_500

        rows.append(
            {
                "schema_version": "flow_probe_ns3_queue_v4",
                "scenario_id": scenario,
                "topology_id": "star-bottleneck-v1",
                "queue_model": "fifo-queue-disc",
                "group_id": f"star-bottleneck-v1|{scenario}|seed42|run1",
                "seed": 42,
                "run": 1,
                "jitter_stream_base": 100,
                "jitter_max_ms": 40,
                "error_stream": 500,
                "downstream_error_rate": 0.01 if scenario == "benign-random-loss" else 0,
                "window_index": index,
                "window_start_s": index / 10,
                "window_end_s": (index + 1) / 10,
                "is_attack": int(attack_active),
                "attack_exposure_fraction": attack_exposure,
                "traffic_phase": traffic_phase,
                "label_primary": "malicious" if attack_active else "benign",
                "label_family": "dos" if attack_active else "benign",
                "label_subtype": "udp" if attack_active else "benign",
                "capacity_start_bps": capacity_start,
                "capacity_end_bps": capacity_end,
                "configured_capacity_integral_link_bytes": service_budget,
                "queue_limit_packets": 50,
                "queue_start_l3_bytes": 0,
                "queue_end_l3_bytes": 0,
                "qdisc_received_l3_bytes": 1000,
                "qdisc_enqueued_l3_bytes": enqueued_bytes,
                "qdisc_dequeued_l3_bytes": enqueued_bytes,
                "qdisc_dropped_before_enqueue_l3_bytes": dropped_before_bytes,
                "qdisc_dropped_after_dequeue_l3_bytes": 0,
                "device_tx_drop_ppp_frame_bytes": 0,
                "downstream_error_loss_ppp_frame_bytes": 100 if random_loss else 0,
                "sink_received_app_payload_bytes": 777 if random_loss else 800,
                "queue_start_packets": 0,
                "queue_end_packets": 0,
                "qdisc_received_packets": received_packets,
                "qdisc_enqueued_packets": enqueued_packets,
                "qdisc_dequeued_packets": enqueued_packets,
                "qdisc_dropped_before_enqueue_packets": dropped_before_packets,
                "qdisc_dropped_after_dequeue_packets": 0,
                "device_tx_drop_packets": 0,
                "downstream_error_loss_packets": 1 if random_loss else 0,
                "sink_received_packets": 0 if random_loss else enqueued_packets,
                "queue_balance_residual_l3_bytes": 0,
                "queue_balance_residual_packets": 0,
            }
        )
    return rows


def _write_rows(
    path: Path,
    rows: list[dict[str, object]],
    *,
    fieldnames: tuple[str, ...] = FIELDS,
) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_validate_ns3_truth_paths_accepts_minimal_complete_group(
    tmp_path: Path,
    scenario: str,
) -> None:
    source = tmp_path / f"{scenario}.csv"
    _write_rows(source, _rows(scenario))

    summary = validate_ns3_truth_paths([source])

    assert summary["validation_status"] == "passed"
    assert summary["file_count"] == 1
    assert summary["group_count"] == 1
    assert summary["total_window_count"] == 120
    assert summary["scenario_window_counts"][scenario] == 120
    expected_queue_drop = (
        100
        if scenario
        in {
            "benign-capacity-shift",
            "dos-udp-medium",
            "dos-udp-high",
            "dos-udp-capacity-shift",
        }
        else 0
    )
    expected_downstream_error = 100 if scenario == "benign-random-loss" else 0
    assert summary["qdisc_drop_l3_bytes"] == expected_queue_drop
    assert summary["downstream_error_loss_ppp_frame_bytes"] == expected_downstream_error
    assert summary["nonzero_l3_residual_count"] == 0
    assert summary["nonzero_packet_residual_count"] == 0
    assert summary["transition_window_count"] == int(scenario.startswith("dos-"))


def test_validate_ns3_truth_paths_rejects_broken_flow_decomposition(tmp_path: Path) -> None:
    source = tmp_path / "broken-decomposition.csv"
    rows = _rows()
    rows[5]["qdisc_received_l3_bytes"] = 1001
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="broken-decomposition.csv.*流量分解"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_broken_conservation(tmp_path: Path) -> None:
    source = tmp_path / "broken-conservation.csv"
    rows = _rows()
    rows[5]["qdisc_dequeued_l3_bytes"] = 999
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="broken-conservation.csv.*队列守恒"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_broken_packet_conservation(tmp_path: Path) -> None:
    source = tmp_path / "broken-packet-conservation.csv"
    rows = _rows()
    rows[5]["qdisc_dequeued_packets"] = 0
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="broken-packet-conservation.csv.*包级守恒"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_early_attack_label(tmp_path: Path) -> None:
    source = tmp_path / "bad-label.csv"
    rows = _rows("dos-udp-high")
    rows[49]["is_attack"] = 1
    rows[49]["label_primary"] = "malicious"
    rows[49]["label_family"] = "dos"
    rows[49]["label_subtype"] = "udp"
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="bad-label.csv.*标签时序"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_invalid_transition_exposure(tmp_path: Path) -> None:
    source = tmp_path / "bad-transition.csv"
    rows = _rows("dos-udp-medium")
    rows[50]["attack_exposure_fraction"] = 1
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="bad-transition.csv.*攻击暴露时序"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_full_attack_without_activity(tmp_path: Path) -> None:
    source = tmp_path / "empty-attack-tail.csv"
    rows = _rows("dos-udp-high")
    for row in rows[116:]:
        for field in (
            "qdisc_received_l3_bytes",
            "qdisc_enqueued_l3_bytes",
            "qdisc_dequeued_l3_bytes",
            "qdisc_dropped_before_enqueue_l3_bytes",
            "qdisc_dropped_after_dequeue_l3_bytes",
            "sink_received_app_payload_bytes",
            "qdisc_received_packets",
            "qdisc_enqueued_packets",
            "qdisc_dequeued_packets",
            "qdisc_dropped_before_enqueue_packets",
            "qdisc_dropped_after_dequeue_packets",
            "sink_received_packets",
        ):
            row[field] = 0
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="empty-attack-tail.csv.*攻击活动"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_attack_tail_without_qdisc_ingress(
    tmp_path: Path,
) -> None:
    source = tmp_path / "no-qdisc-ingress-tail.csv"
    rows = _rows("dos-udp-high")
    for field in (
        "qdisc_received_l3_bytes",
        "qdisc_enqueued_l3_bytes",
        "qdisc_dequeued_l3_bytes",
        "qdisc_received_packets",
        "qdisc_enqueued_packets",
        "qdisc_dequeued_packets",
    ):
        rows[-1][field] = 0
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="no-qdisc-ingress-tail.csv.*攻击入口活动"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_changed_jitter_config(tmp_path: Path) -> None:
    source = tmp_path / "bad-jitter.csv"
    rows = _rows()
    rows[80]["jitter_max_ms"] = 10
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="bad-jitter.csv.*组内常量"):
        validate_ns3_truth_paths([source])


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    (("jitter_stream_base", 101), ("jitter_max_ms", 41)),
)
def test_validate_ns3_truth_paths_rejects_wrong_fixed_jitter_config(
    tmp_path: Path,
    field: str,
    invalid_value: int,
) -> None:
    source = tmp_path / f"bad-fixed-{field}.csv"
    rows = _rows()
    for row in rows:
        row[field] = invalid_value
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match=f"bad-fixed-{field}.csv.*抖动配置"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_error_model_config(tmp_path: Path) -> None:
    source = tmp_path / "bad-error-model.csv"
    rows = _rows("benign-random-loss")
    rows[80]["downstream_error_rate"] = 0
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="bad-error-model.csv.*误码配置"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_capacity_budget_error(tmp_path: Path) -> None:
    source = tmp_path / "bad-capacity.csv"
    rows = _rows("benign-capacity-shift")
    rows[60]["configured_capacity_integral_link_bytes"] = 62_500
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="bad-capacity.csv.*容量预算"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_hidden_device_drop(tmp_path: Path) -> None:
    source = tmp_path / "hidden-drop.csv"
    rows = _rows()
    rows[70]["device_tx_drop_ppp_frame_bytes"] = 100
    rows[70]["device_tx_drop_packets"] = 1
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="hidden-drop.csv.*隐藏设备丢弃"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_required_drop_without_packet_count(
    tmp_path: Path,
) -> None:
    source = tmp_path / "drop-bytes-without-packets.csv"
    rows = _rows("dos-udp-high")
    rows[50]["qdisc_dropped_before_enqueue_packets"] = 0
    rows[50]["qdisc_received_packets"] = 1
    _write_rows(source, rows)

    with pytest.raises(
        NS3TruthValidationError, match="drop-bytes-without-packets.csv.*队列丢弃计量"
    ):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_random_loss_without_packet_count(
    tmp_path: Path,
) -> None:
    source = tmp_path / "loss-bytes-without-packets.csv"
    rows = _rows("benign-random-loss")
    rows[10]["downstream_error_loss_packets"] = 0
    _write_rows(source, rows)

    with pytest.raises(
        NS3TruthValidationError, match="loss-bytes-without-packets.csv.*误码丢弃计量"
    ):
        validate_ns3_truth_paths([source])


@pytest.mark.parametrize(
    ("scenario", "byte_field", "packet_field", "first_index", "expected_rule"),
    (
        (
            "dos-udp-high",
            "qdisc_dropped_before_enqueue_l3_bytes",
            "qdisc_dropped_before_enqueue_packets",
            50,
            "队列丢弃计量",
        ),
        (
            "benign-random-loss",
            "downstream_error_loss_ppp_frame_bytes",
            "downstream_error_loss_packets",
            10,
            "误码丢弃计量",
        ),
    ),
)
def test_validate_ns3_truth_paths_rejects_cross_window_loss_measurement_splice(
    tmp_path: Path,
    scenario: str,
    byte_field: str,
    packet_field: str,
    first_index: int,
    expected_rule: str,
) -> None:
    source = tmp_path / f"cross-window-{scenario}.csv"
    rows = _rows(scenario)
    rows[first_index][packet_field] = 0
    rows[first_index + 1][packet_field] = 1
    if scenario == "dos-udp-high":
        rows[first_index]["qdisc_received_packets"] = 1
        rows[first_index + 1]["qdisc_received_packets"] = 2
    assert rows[first_index][byte_field] != 0
    assert rows[first_index + 1][byte_field] == 0
    _write_rows(source, rows)

    with pytest.raises(
        NS3TruthValidationError,
        match=f"cross-window-{scenario}.csv.*{expected_rule}",
    ):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_wrong_topology(tmp_path: Path) -> None:
    source = tmp_path / "wrong-topology.csv"
    rows = _rows()
    for row in rows:
        row["topology_id"] = "line-v1"
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="wrong-topology.csv.*拓扑配置"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_wrong_queue_model(tmp_path: Path) -> None:
    source = tmp_path / "wrong-queue-model.csv"
    rows = _rows()
    for row in rows:
        row["queue_model"] = "codel-queue-disc"
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="wrong-queue-model.csv.*队列模型"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_forged_group_id(tmp_path: Path) -> None:
    source = tmp_path / "forged-group-id.csv"
    rows = _rows()
    for row in rows:
        row["group_id"] = "star-bottleneck-v1|benign-high|seed7|run9"
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="forged-group-id.csv.*组标识组成"):
        validate_ns3_truth_paths([source])


@pytest.mark.parametrize("drift_index", [None, 80])
def test_validate_ns3_truth_paths_rejects_wrong_queue_limit(
    tmp_path: Path,
    drift_index: int | None,
) -> None:
    source = tmp_path / f"wrong-queue-limit-{drift_index}.csv"
    rows = _rows()
    targets = rows if drift_index is None else [rows[drift_index]]
    for row in targets:
        row["queue_limit_packets"] = 49
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="wrong-queue-limit.*队列上限"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_shifted_absolute_timeline(tmp_path: Path) -> None:
    source = tmp_path / "shifted-timeline.csv"
    rows = _rows()
    for index, row in enumerate(rows):
        row["window_start_s"] = f"{(index + 1) / 10:.1f}"
        row["window_end_s"] = f"{(index + 2) / 10:.1f}"
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="shifted-timeline.csv.*绝对时间"):
        validate_ns3_truth_paths([source])


@pytest.mark.parametrize(
    ("start_field", "end_field", "value"),
    (
        ("queue_start_l3_bytes", "queue_end_l3_bytes", 100),
        ("queue_start_packets", "queue_end_packets", 1),
    ),
)
def test_validate_ns3_truth_paths_rejects_discontinuous_queue_state(
    tmp_path: Path,
    start_field: str,
    end_field: str,
    value: int,
) -> None:
    source = tmp_path / f"discontinuous-{start_field}.csv"
    rows = _rows()
    rows[5][start_field] = value
    rows[5][end_field] = value
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="discontinuous.*队列连续"):
        validate_ns3_truth_paths([source])


@pytest.mark.parametrize(
    ("start_field", "end_field", "value"),
    (
        ("queue_start_l3_bytes", "queue_end_l3_bytes", 100),
        ("queue_start_packets", "queue_end_packets", 1),
    ),
)
def test_validate_ns3_truth_paths_rejects_nonzero_initial_queue_state(
    tmp_path: Path,
    start_field: str,
    end_field: str,
    value: int,
) -> None:
    source = tmp_path / f"nonzero-initial-{start_field}.csv"
    rows = _rows()
    for row in rows:
        row[start_field] = value
        row[end_field] = value
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="nonzero-initial.*初始队列"):
        validate_ns3_truth_paths([source])


@pytest.mark.parametrize("boundary", ("start", "end"))
def test_validate_ns3_truth_paths_rejects_queue_packet_state_above_limit(
    tmp_path: Path,
    boundary: str,
) -> None:
    source = tmp_path / f"queue-{boundary}-packets-above-limit.csv"
    rows = _rows()
    grow_index = 118 if boundary == "start" else 119
    rows[grow_index].update(
        {
            "queue_end_packets": 51,
            "qdisc_received_packets": 52,
            "qdisc_enqueued_packets": 52,
        }
    )
    if boundary == "start":
        rows[119].update(
            {
                "queue_start_packets": 51,
                "qdisc_dequeued_packets": 52,
            }
        )
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="above-limit.csv.*队列包状态上限"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_missing_field(tmp_path: Path) -> None:
    source = tmp_path / "missing-field.csv"
    _write_rows(source, _rows(), fieldnames=FIELDS[:-1])

    with pytest.raises(NS3TruthValidationError, match="missing-field.csv.*字段契约"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_reordered_fields(tmp_path: Path) -> None:
    source = tmp_path / "reordered-fields.csv"
    reordered = list(FIELDS)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    _write_rows(source, _rows(), fieldnames=tuple(reordered))

    with pytest.raises(NS3TruthValidationError, match="reordered-fields.csv.*字段顺序"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_fewer_than_120_windows(tmp_path: Path) -> None:
    source = tmp_path / "short-group.csv"
    _write_rows(source, _rows()[:-1])

    with pytest.raises(NS3TruthValidationError, match="short-group.csv.*完整窗口"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_scrambled_window_indices(tmp_path: Path) -> None:
    source = tmp_path / "scrambled-indices.csv"
    rows = _rows()
    rows[10], rows[11] = rows[11], rows[10]
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="scrambled-indices.csv.*窗口索引"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_discontinuous_time(tmp_path: Path) -> None:
    source = tmp_path / "discontinuous-time.csv"
    rows = _rows()
    rows[5]["window_start_s"] = "0.6"
    rows[5]["window_end_s"] = "0.7"
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="discontinuous-time.csv.*绝对时间"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_missing_required_queue_drop(tmp_path: Path) -> None:
    source = tmp_path / "missing-required-drop.csv"
    rows = _rows("dos-udp-high")
    rows[50].update(
        {
            "qdisc_enqueued_l3_bytes": 1000,
            "qdisc_dequeued_l3_bytes": 1000,
            "qdisc_dropped_before_enqueue_l3_bytes": 0,
            "qdisc_received_packets": 1,
            "qdisc_dropped_before_enqueue_packets": 0,
        }
    )
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="missing-required-drop.csv.*队列规则丢弃"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_error_loss_in_nonrandom_scenario(
    tmp_path: Path,
) -> None:
    source = tmp_path / "unexpected-error-loss.csv"
    rows = _rows()
    rows[10]["downstream_error_loss_ppp_frame_bytes"] = 100
    rows[10]["downstream_error_loss_packets"] = 1
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="unexpected-error-loss.csv.*下游误码丢弃"):
        validate_ns3_truth_paths([source])


def test_validate_ns3_truth_paths_rejects_saved_packet_residual(tmp_path: Path) -> None:
    source = tmp_path / "saved-packet-residual.csv"
    rows = _rows()
    rows[5]["queue_balance_residual_packets"] = 1
    _write_rows(source, rows)

    with pytest.raises(NS3TruthValidationError, match="saved-packet-residual.csv.*保存残差"):
        validate_ns3_truth_paths([source])


def test_main_writes_json_and_returns_nonzero_for_invalid_input(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    valid_source = tmp_path / "valid.csv"
    output = tmp_path / "summary.json"
    _write_rows(valid_source, _rows())

    assert main([str(valid_source), "--output", str(output)]) == 0
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["validation_status"] == "passed"

    invalid_source = tmp_path / "invalid.csv"
    rows = _rows()
    rows[0]["device_tx_drop_packets"] = 1
    _write_rows(invalid_source, rows)

    assert main([str(invalid_source)]) == 1
    assert "invalid.csv" in capsys.readouterr().err
