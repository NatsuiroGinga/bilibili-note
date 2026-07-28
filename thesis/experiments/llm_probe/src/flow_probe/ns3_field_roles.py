"""加载 ns-3 字段角色并验证按完整运行分组的防泄漏切分。"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Collection, Mapping
from pathlib import Path

from flow_probe.ns3_truth import CSV_FIELDS

ROLE_NAMES = (
    "model_input_observable",
    "state_supervision",
    "label_target",
    "split_metadata",
    "audit_only",
)
ALLOWED_MODEL_INPUTS = (
    "capacity_start_bps",
    "capacity_end_bps",
    "configured_capacity_integral_link_bytes",
    "qdisc_received_l3_bytes",
    "qdisc_received_packets",
)


class NS3FieldRolesError(ValueError):
    """ns-3 字段角色或运行切分违反防泄漏契约。"""


def _format_difference(prefix: str, values: Collection[str]) -> str | None:
    if not values:
        return None
    return f"{prefix}：{', '.join(sorted(values))}"


def load_ns3_field_roles(path: Path) -> dict[str, tuple[str, ...]]:
    """加载并验证 ns-3 队列真值字段的唯一角色映射。"""
    source_path = Path(path)
    try:
        raw_config = source_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise NS3FieldRolesError(
            f"读取字段角色配置 {source_path} 时 UTF-8 解码失败：{exc}"
        ) from exc
    except OSError as exc:
        raise NS3FieldRolesError(f"读取字段角色配置 {source_path} 失败：{exc}") from exc

    try:
        loaded = json.loads(raw_config)
    except json.JSONDecodeError as exc:
        raise NS3FieldRolesError(f"解析字段角色配置 {source_path} 的 JSON 失败：{exc}") from exc
    if not isinstance(loaded, dict):
        raise NS3FieldRolesError(f"字段角色配置 {source_path} 的顶层必须是对象")

    expected_role_names = set(ROLE_NAMES)
    actual_role_names = set(loaded)
    if actual_role_names != expected_role_names:
        details = [
            detail
            for detail in (
                _format_difference("缺少角色名", expected_role_names - actual_role_names),
                _format_difference("未知角色名", actual_role_names - expected_role_names),
            )
            if detail is not None
        ]
        raise NS3FieldRolesError(f"字段角色配置的角色名集合不正确；{'；'.join(details)}")

    roles: dict[str, tuple[str, ...]] = {}
    for role_name in ROLE_NAMES:
        raw_fields = loaded[role_name]
        if not isinstance(raw_fields, list):
            raise NS3FieldRolesError(f"角色 {role_name} 的成员必须使用 JSON 数组")
        if any(not isinstance(field, str) for field in raw_fields):
            raise NS3FieldRolesError(f"角色 {role_name} 的每个成员都必须是字符串")
        duplicates = sorted(field for field, count in Counter(raw_fields).items() if count > 1)
        if duplicates:
            raise NS3FieldRolesError(
                f"角色内重复：角色 {role_name} 重复包含 {', '.join(duplicates)}"
            )
        roles[role_name] = tuple(raw_fields)

    field_owners: dict[str, list[str]] = {}
    for role_name, fields in roles.items():
        for field in fields:
            field_owners.setdefault(field, []).append(role_name)
    cross_role_duplicates = sorted(
        field for field, owners in field_owners.items() if len(owners) > 1
    )
    if cross_role_duplicates:
        raise NS3FieldRolesError(f"跨角色重复字段：{', '.join(cross_role_duplicates)}")

    expected_fields = set(CSV_FIELDS)
    actual_fields = set(field_owners)
    missing_fields = expected_fields - actual_fields
    unknown_fields = actual_fields - expected_fields
    if missing_fields or unknown_fields:
        details = [
            detail
            for detail in (
                _format_difference("缺少字段", missing_fields),
                _format_difference("未知字段", unknown_fields),
            )
            if detail is not None
        ]
        raise NS3FieldRolesError(f"字段角色未精确覆盖 CSV_FIELDS；{'；'.join(details)}")

    if roles["model_input_observable"] != ALLOWED_MODEL_INPUTS:
        actual_inputs = set(roles["model_input_observable"])
        allowed_inputs = set(ALLOWED_MODEL_INPUTS)
        details = [
            detail
            for detail in (
                _format_difference("缺少允许字段", allowed_inputs - actual_inputs),
                _format_difference("包含禁止字段", actual_inputs - allowed_inputs),
            )
            if detail is not None
        ]
        if not details:
            details.append("字段顺序与固定允许列表不一致")
        raise NS3FieldRolesError(f"模型输入字段必须精确等于固定允许列表；{'；'.join(details)}")

    return roles


def validate_group_disjoint_splits(
    split_groups: Mapping[str, Collection[str]],
) -> None:
    """确保任意两个命名切分不共享完整运行的 group_id。"""
    group_owners: dict[str, str] = {}
    for split_name, group_ids in split_groups.items():
        if isinstance(group_ids, (str, bytes)):
            raise NS3FieldRolesError(f"切分 {split_name!r} 的 group_id 集合不能是 str 或 bytes")
        for group_id in group_ids:
            if not isinstance(group_id, str):
                raise NS3FieldRolesError(f"切分 {split_name!r} 的 group_id 集合成员都必须是字符串")
            previous_split = group_owners.get(group_id)
            if previous_split is not None and previous_split != split_name:
                raise NS3FieldRolesError(
                    f"group_id {group_id!r} 同时出现在切分 {previous_split!r} "
                    f"与 {split_name!r} 中"
                )
            group_owners[group_id] = split_name
