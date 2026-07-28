import json
from pathlib import Path

import pytest

from flow_probe.ns3_field_roles import (
    NS3FieldRolesError,
    load_ns3_field_roles,
    validate_group_disjoint_splits,
)
from flow_probe.ns3_truth import CSV_FIELDS

CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "ns3_queue_truth_field_roles.json"

EXPECTED_ROLES = {
    "model_input_observable": (
        "capacity_start_bps",
        "capacity_end_bps",
        "configured_capacity_integral_link_bytes",
        "qdisc_received_l3_bytes",
        "qdisc_received_packets",
    ),
    "state_supervision": (
        "queue_start_l3_bytes",
        "queue_end_l3_bytes",
        "qdisc_enqueued_l3_bytes",
        "qdisc_dequeued_l3_bytes",
        "qdisc_dropped_before_enqueue_l3_bytes",
        "qdisc_dropped_after_dequeue_l3_bytes",
        "queue_start_packets",
        "queue_end_packets",
        "qdisc_enqueued_packets",
        "qdisc_dequeued_packets",
        "qdisc_dropped_before_enqueue_packets",
        "qdisc_dropped_after_dequeue_packets",
    ),
    "label_target": (
        "is_attack",
        "attack_exposure_fraction",
        "traffic_phase",
        "label_primary",
        "label_family",
        "label_subtype",
    ),
    "split_metadata": (
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
        "queue_limit_packets",
    ),
    "audit_only": (
        "device_tx_drop_ppp_frame_bytes",
        "downstream_error_loss_ppp_frame_bytes",
        "sink_received_app_payload_bytes",
        "device_tx_drop_packets",
        "downstream_error_loss_packets",
        "sink_received_packets",
        "queue_balance_residual_l3_bytes",
        "queue_balance_residual_packets",
    ),
}


def _mutable_roles() -> dict[str, list[object]]:
    return {role: list(fields) for role, fields in EXPECTED_ROLES.items()}


def _write_roles(path: Path, roles: object) -> None:
    path.write_text(json.dumps(roles, ensure_ascii=False), encoding="utf-8")


def test_load_ns3_field_roles_accepts_fixed_contract() -> None:
    roles = load_ns3_field_roles(CONFIG_PATH)

    assert roles == EXPECTED_ROLES
    assert all(isinstance(fields, tuple) for fields in roles.values())
    assigned_fields = [field for fields in roles.values() for field in fields]
    assert len(assigned_fields) == len(CSV_FIELDS) == 46
    assert set(assigned_fields) == set(CSV_FIELDS)


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_load_ns3_field_roles_rejects_wrong_role_names(
    tmp_path: Path,
    mutation: str,
) -> None:
    roles = _mutable_roles()
    if mutation == "missing":
        roles.pop("audit_only")
    else:
        roles["unexpected_role"] = []
    source = tmp_path / f"wrong-role-names-{mutation}.json"
    _write_roles(source, roles)

    with pytest.raises(ValueError, match="角色名"):
        load_ns3_field_roles(source)


def test_load_ns3_field_roles_rejects_non_object_root(tmp_path: Path) -> None:
    source = tmp_path / "non-object-root.json"
    _write_roles(source, [])

    with pytest.raises(ValueError, match="顶层.*对象"):
        load_ns3_field_roles(source)


@pytest.mark.parametrize(
    ("raw_content", "expected_context", "cause_type"),
    [
        (b"{", "JSON", json.JSONDecodeError),
        (b"\xff", "UTF-8", UnicodeDecodeError),
    ],
)
def test_load_ns3_field_roles_wraps_invalid_file_content(
    tmp_path: Path,
    raw_content: bytes,
    expected_context: str,
    cause_type: type[Exception],
) -> None:
    source = tmp_path / f"invalid-{expected_context}.json"
    source.write_bytes(raw_content)

    with pytest.raises(NS3FieldRolesError) as captured:
        load_ns3_field_roles(source)

    message = str(captured.value)
    assert str(source) in message
    assert expected_context in message
    assert isinstance(captured.value.__cause__, cause_type)


def test_load_ns3_field_roles_wraps_file_read_failure(tmp_path: Path) -> None:
    source = tmp_path / "missing-field-roles.json"

    with pytest.raises(NS3FieldRolesError) as captured:
        load_ns3_field_roles(source)

    message = str(captured.value)
    assert str(source) in message
    assert "读取" in message
    assert "失败" in message
    assert isinstance(captured.value.__cause__, FileNotFoundError)


def test_load_ns3_field_roles_rejects_non_array_role(tmp_path: Path) -> None:
    roles: dict[str, object] = _mutable_roles()
    roles["label_target"] = "is_attack"
    source = tmp_path / "non-array-role.json"
    _write_roles(source, roles)

    with pytest.raises(ValueError, match="label_target.*数组"):
        load_ns3_field_roles(source)


def test_load_ns3_field_roles_rejects_non_string_member(tmp_path: Path) -> None:
    roles = _mutable_roles()
    roles["audit_only"][0] = 42
    source = tmp_path / "non-string-member.json"
    _write_roles(source, roles)

    with pytest.raises(ValueError, match="audit_only.*字符串"):
        load_ns3_field_roles(source)


def test_load_ns3_field_roles_rejects_missing_field(tmp_path: Path) -> None:
    roles = _mutable_roles()
    roles["state_supervision"].remove("queue_end_l3_bytes")
    source = tmp_path / "missing-field.json"
    _write_roles(source, roles)

    with pytest.raises(ValueError, match="缺少.*queue_end_l3_bytes"):
        load_ns3_field_roles(source)


def test_load_ns3_field_roles_rejects_unknown_field(tmp_path: Path) -> None:
    roles = _mutable_roles()
    roles["audit_only"].append("not_an_ns3_truth_field")
    source = tmp_path / "unknown-field.json"
    _write_roles(source, roles)

    with pytest.raises(ValueError, match="未知.*not_an_ns3_truth_field"):
        load_ns3_field_roles(source)


def test_load_ns3_field_roles_rejects_duplicate_within_role(tmp_path: Path) -> None:
    roles = _mutable_roles()
    roles["state_supervision"].append("queue_end_l3_bytes")
    source = tmp_path / "duplicate-within-role.json"
    _write_roles(source, roles)

    with pytest.raises(ValueError, match="角色内重复.*queue_end_l3_bytes"):
        load_ns3_field_roles(source)


def test_load_ns3_field_roles_rejects_duplicate_across_roles(tmp_path: Path) -> None:
    roles = _mutable_roles()
    roles["audit_only"].append("queue_end_l3_bytes")
    source = tmp_path / "duplicate-across-roles.json"
    _write_roles(source, roles)

    with pytest.raises(ValueError, match="跨角色重复.*queue_end_l3_bytes"):
        load_ns3_field_roles(source)


@pytest.mark.parametrize("mutation", ["forbidden", "missing_allowed"])
def test_load_ns3_field_roles_rejects_wrong_model_inputs(
    tmp_path: Path,
    mutation: str,
) -> None:
    roles = _mutable_roles()
    if mutation == "forbidden":
        roles["state_supervision"].remove("queue_start_l3_bytes")
        roles["model_input_observable"].append("queue_start_l3_bytes")
    else:
        roles["model_input_observable"].remove("capacity_start_bps")
        roles["audit_only"].append("capacity_start_bps")
    source = tmp_path / f"wrong-model-inputs-{mutation}.json"
    _write_roles(source, roles)

    with pytest.raises(ValueError, match="模型输入"):
        load_ns3_field_roles(source)


def test_validate_group_disjoint_splits_accepts_disjoint_groups() -> None:
    result = validate_group_disjoint_splits(
        {
            "train": {"train-group-1", "train-group-2"},
            "validation": ["validation-group-1"],
            "test": ("test-group-1",),
        }
    )

    assert result is None


@pytest.mark.parametrize("group_ids", ["group-a", b"group-a"])
def test_validate_group_disjoint_splits_rejects_scalar_string_collections(
    group_ids: str | bytes,
) -> None:
    with pytest.raises(NS3FieldRolesError, match="切分.*train.*group_id.*集合"):
        validate_group_disjoint_splits({"train": group_ids})


def test_validate_group_disjoint_splits_rejects_non_string_member() -> None:
    with pytest.raises(NS3FieldRolesError, match="切分.*train.*group_id.*字符串"):
        validate_group_disjoint_splits({"train": ["group-a", 42]})


def test_validate_group_disjoint_splits_rejects_shared_group() -> None:
    with pytest.raises(ValueError) as captured:
        validate_group_disjoint_splits(
            {
                "train": {"shared-group", "train-only"},
                "validation": ["validation-only", "shared-group"],
            }
        )

    message = str(captured.value)
    assert "train" in message
    assert "validation" in message
    assert "shared-group" in message
