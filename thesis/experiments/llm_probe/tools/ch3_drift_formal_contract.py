#!/usr/bin/env python3
"""第三章 DRIFT 正式评价的共享合同与统一机械门禁。

本模块只使用 Python 标准库，不导入 PyTorch、NumPy、PyArrow 或任何设备后端。
它负责配置严格读取、身份哈希、路径边界、原子 JSON 和运行状态迁移；原 Parquet
直读、成员选择、攻击生成、评分及比较器由后续独立模块实现。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "ch3_drift_formal_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[4]
LLM_PROBE_ROOT = REPO_ROOT / "thesis/experiments/llm_probe"
SHORT_PATH_PREFIXES = frozenset(("configs", "runs", "tools", "scripts"))
ALLOWED_ARMS = ("A", "B", "D", "F", "G")
ALLOWED_GATE_NAMES = ("inputs", "train", "evaluate", "compare")
ALLOWED_MODES = ("audit", "run", "resume", "summarize")
ALLOWED_STATUS = ("created", "running", "complete", "failed")
ALLOWED_TRANSITIONS = {
    "created": frozenset(("running", "failed")),
    "running": frozenset(("complete", "failed")),
    "failed": frozenset(("running",)),
    "complete": frozenset(),
}
DATA_REVISION = "3b31077020cd1c013d0a75cad51042a2327c4521"
EXPECTED_ROLE_COUNT = 30
EXPECTED_TARGET_YEARS = (20, 21, 22, 23, 24, 25)
EXPECTED_SOURCE_YEARS = (17, 18, 19)
EXPECTED_CLASSES = ("benign", "dga")
EXPECTED_TRAIN_SPLITS = ("train", "test")
EXPECTED_INPUT_ROOT = (
    "thesis/experiments/llm_probe/runs/data-raw/"
    "drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD"
)


class ContractError(ValueError):
    """合同校验失败。"""


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"JSON 存在重复键：{key}")
        result[key] = value
    return result


def _load_json(path: Path) -> Any:
    def reject_nonstandard_number(token: str) -> None:
        raise ContractError(f"JSON 不允许非标准数值：{token}")

    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=reject_nonstandard_number,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ContractError) as exc:
        raise ContractError(f"无法严格读取 JSON：{path}；{exc}") from exc


def canonical_json_bytes(value: Any) -> bytes:
    """返回规范 JSON 字节，用于配置、清单和状态身份哈希。"""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError(f"规范 JSON 序列化失败：{exc}") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """流式计算文件 SHA-256，不把文件整体读入内存。"""
    if chunk_size <= 0:
        raise ContractError("文件哈希块大小必须为正数")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(chunk_size):
                digest.update(chunk)
    except OSError as exc:
        raise ContractError(f"无法读取文件以计算 SHA-256：{path}；{exc}") from exc
    return digest.hexdigest()


def length_prefix_encode(*fields: str) -> bytes:
    """使用 8 字节大端 UTF-8 长度前缀编码字符串字段。"""
    encoded = bytearray()
    for field in fields:
        if not isinstance(field, str):
            raise ContractError(f"长度前缀字段必须是字符串，收到：{type(field).__name__}")
        raw = field.encode("utf-8")
        encoded.extend(len(raw).to_bytes(8, "big", signed=False))
        encoded.extend(raw)
    return bytes(encoded)


def member_hash(namespace: str, revision: str, panel_id: str, year: int, class_name: str, exact_esld: str) -> str:
    """计算正式成员身份摘要；不会清洗、转小写或依赖对象哈希。"""
    if not isinstance(year, int) or isinstance(year, bool):
        raise ContractError("成员年份必须是整数")
    return sha256_bytes(length_prefix_encode(namespace, revision, panel_id, str(year), class_name, exact_esld))


def attack_stream_id(attack_namespace: str, revision: str, exact_esld: str) -> str:
    """计算不含面板、年份、骨干和训练臂的共享编辑流身份。"""
    return sha256_bytes(length_prefix_encode(attack_namespace, revision, exact_esld))


def resolve_repo_relative(path_value: str | Path, *, must_exist: bool = False) -> Path:
    """按固定根解析路径；configs/runs/tools/scripts 短路径映射到 llm_probe。"""
    raw = Path(path_value)
    if raw.is_absolute():
        raise ContractError(f"只允许仓库相对路径：{path_value}")
    if any(part == ".." for part in raw.parts):
        raise ContractError(f"路径不得包含越界片段 '..'：{path_value}")
    base = LLM_PROBE_ROOT if raw.parts and raw.parts[0] in SHORT_PATH_PREFIXES else REPO_ROOT
    candidate = (base / raw).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ContractError(f"路径越出允许根目录：{path_value}") from exc
    if candidate.exists():
        return candidate
    if must_exist:
        raise ContractError(f"路径不存在或越出仓库根目录：{path_value}")
    return candidate


def resolve_run_dir(path_value: str | Path) -> Path:
    """解析运行目录并限制在 llm_probe/runs 下，避免把状态写到仓库根。"""
    path = resolve_repo_relative(path_value)
    try:
        path.relative_to(LLM_PROBE_ROOT / "runs")
    except ValueError as exc:
        raise ContractError(f"运行目录必须位于 llm_probe/runs 下：{path_value}") from exc
    return path


def _require_keys(value: Mapping[str, Any], expected: Iterable[str], where: str) -> None:
    if not isinstance(value, Mapping):
        raise ContractError(f"{where} 必须是 JSON 对象")
    expected_set = set(expected)
    actual_set = set(value)
    unknown = sorted(actual_set - expected_set)
    missing = sorted(expected_set - actual_set)
    if unknown:
        raise ContractError(f"{where} 含未知键：{unknown}")
    if missing:
        raise ContractError(f"{where} 缺少键：{missing}")


def _require_type(value: Any, expected_type: type | tuple[type, ...], where: str) -> None:
    if not isinstance(value, expected_type) or (expected_type is int and isinstance(value, bool)):
        raise ContractError(f"{where} 类型错误：期望 {expected_type}，实际 {type(value).__name__}")


def _require_string(value: Any, where: str, *, nonempty: bool = True) -> None:
    _require_type(value, str, where)
    if nonempty and not value:
        raise ContractError(f"{where} 不能为空")


def _require_string_list(value: Any, where: str) -> None:
    _require_type(value, list, where)
    for index, item in enumerate(value):
        _require_string(item, f"{where}[{index}]")


def _contains_key(value: Any, key_name: str) -> bool:
    if isinstance(value, dict):
        return key_name in value or any(_contains_key(child, key_name) for child in value.values())
    if isinstance(value, list):
        return any(_contains_key(child, key_name) for child in value)
    return False


def _validate_input_roles(config: Mapping[str, Any]) -> None:
    roles = config["input_roles"]
    _require_type(roles, list, "input_roles")
    if len(roles) != EXPECTED_ROLE_COUNT:
        raise ContractError(f"输入角色必须恰好为 30 个，实际 {len(roles)} 个")
    seen_role: set[str] = set()
    seen_path: set[str] = set()
    for index, role in enumerate(roles):
        where = f"input_roles[{index}]"
        _require_type(role, dict, where)
        _require_keys(role, ("role", "path", "year", "class", "split", "scope"), where)
        _require_string(role["role"], f"{where}.role")
        _require_string(role["path"], f"{where}.path")
        _require_type(role["year"], int, f"{where}.year")
        _require_string(role["class"], f"{where}.class")
        _require_string(role["split"], f"{where}.split")
        _require_string(role["scope"], f"{where}.scope")
        if role["role"] in seen_role:
            raise ContractError(f"输入角色重复：{role['role']}")
        if role["path"] in seen_path:
            raise ContractError(f"输入路径重复：{role['path']}")
        seen_role.add(role["role"])
        seen_path.add(role["path"])
        resolved = resolve_repo_relative(role["path"])
        if resolved.suffix != ".parquet":
            raise ContractError(f"输入文件必须是 Parquet：{role['path']}")
        if role["scope"] == "source":
            if role["year"] not in EXPECTED_SOURCE_YEARS:
                raise ContractError(f"源角色年份非法：{where}.year")
            if role["split"] not in (*EXPECTED_TRAIN_SPLITS, "val"):
                raise ContractError(f"源角色切分非法：{where}.split")
        elif role["scope"] == "target":
            if role["year"] not in EXPECTED_TARGET_YEARS or role["split"] != "target":
                raise ContractError(f"目标角色年份或切分非法：{where}")
        else:
            raise ContractError(f"角色范围只能是 source 或 target：{where}.scope")
        if role["class"] not in EXPECTED_CLASSES:
            raise ContractError(f"角色类别非法：{where}.class")
        expected_role = (
            f"T{role['year']}_{role['class']}_{role['split']}"
            if role["scope"] == "source"
            else f"T{role['year']}_{role['class']}"
        )
        expected_path = f"{config['input_root']}/{expected_role}.parquet"
        if role["role"] != expected_role:
            raise ContractError(f"{where} 的 role 与 year/class/split/scope 组合不一致：期望 {expected_role}")
        if role["path"] != expected_path:
            raise ContractError(f"{where} 的 path 未绑定冻结 input_root 和 role：期望 {expected_path}")
    expected_roles = {
        *(f"T{year}_{class_name}_{split}" for year in EXPECTED_SOURCE_YEARS for class_name in EXPECTED_CLASSES for split in (*EXPECTED_TRAIN_SPLITS, "val")),
        *(f"T{year}_{class_name}" for year in EXPECTED_TARGET_YEARS for class_name in EXPECTED_CLASSES),
    }
    if seen_role != expected_roles:
        missing = sorted(expected_roles - seen_role)
        extra = sorted(seen_role - expected_roles)
        raise ContractError(f"输入角色集合不符合 30 角色合同：缺少 {missing}；额外 {extra}")


def _validate_evaluation_config(config: Mapping[str, Any]) -> None:
    _require_keys(
        config,
        (
            "config_kind", "schema_version", "config_id", "contract_id", "data_revision", "input_root",
            "input_access", "input_roles", "approved_panels", "panels", "member_identity", "attacks",
            "thresholds", "result_contract", "allowed_modes", "forbidden_keys",
        ),
        "评价配置",
    )
    if config["schema_version"] != SCHEMA_VERSION or config["contract_id"] != SCHEMA_VERSION:
        raise ContractError("评价配置模式版本不匹配")
    _require_string(config["config_id"], "config_id")
    if config["data_revision"] != DATA_REVISION:
        raise ContractError(f"data_revision 必须为冻结值 {DATA_REVISION}")
    if config["input_root"] != EXPECTED_INPUT_ROOT:
        raise ContractError(f"input_root 必须为冻结路径：{EXPECTED_INPUT_ROOT}")
    input_access = config["input_access"]
    _require_keys(input_access, ("mode", "source_order", "deduplicate_by", "derived_data_written"), "input_access")
    if input_access != {
        "mode": "direct_parquet_read_only",
        "source_order": "input_role_order_then_row_first_occurrence",
        "deduplicate_by": "exact_esld",
        "derived_data_written": False,
    }:
        raise ContractError("input_access 必须冻结为原 Parquet 只读直读合同")
    _require_string_list(config["approved_panels"], "approved_panels")
    _require_type(config["allowed_modes"], list, "allowed_modes")
    if tuple(config["allowed_modes"]) != ALLOWED_MODES:
        raise ContractError("allowed_modes 必须完整且按合同顺序列出")
    _require_string_list(config["forbidden_keys"], "forbidden_keys")
    required_forbidden = {"member_seed", "krand", "maskdga", "target_limit", "threshold_override"}
    if not required_forbidden.issubset(config["forbidden_keys"]):
        raise ContractError("forbidden_keys 未完整声明禁止的成员、攻击、上限或阈值覆盖键")
    _validate_input_roles(config)

    member_identity = config["member_identity"]
    _require_keys(member_identity, ("namespace", "encoding", "selection", "max_entities_per_year_class"), "member_identity")
    _require_string(member_identity["namespace"], "member_identity.namespace")
    if member_identity["encoding"] != "utf8_length_prefix_u64_be":
        raise ContractError("成员编码必须是 UTF-8 8 字节大端长度前缀")
    _require_keys(member_identity["selection"], ("deduplicate_by", "sort_by", "take"), "member_identity.selection")
    if member_identity["selection"] != {
        "deduplicate_by": "exact_esld",
        "sort_by": "member_hash_ascending",
        "take": "min(200000, unique_count)",
    }:
        raise ContractError("成员选择规则与冻结合同不一致")
    if member_identity["max_entities_per_year_class"] != 200000:
        raise ContractError("每年每类成员上限必须固定为 200000")

    panels = config["panels"]
    _require_type(panels, list, "panels")
    panel_ids: set[str] = set()
    for index, panel in enumerate(panels):
        where = f"panels[{index}]"
        _require_type(panel, dict, where)
        _require_keys(panel, ("panel_id", "scope", "formal", "years", "classes", "selection", "qualification_receipt"), where)
        _require_string(panel["panel_id"], f"{where}.panel_id")
        if panel["panel_id"] in panel_ids:
            raise ContractError(f"面板重复：{panel['panel_id']}")
        panel_ids.add(panel["panel_id"])
        _require_type(panel["years"], list, f"{where}.years")
        _require_type(panel["classes"], list, f"{where}.classes")
        if panel["scope"] not in ("source", "target"):
            raise ContractError(f"{where}.scope 必须是 source 或 target")
        if panel["formal"] is not True and panel["formal"] is not False:
            raise ContractError(f"{where}.formal 必须是布尔值")
        if panel["panel_id"] == "target_official_annual_v1":
            if panel["formal"] is not True or tuple(panel["years"]) != EXPECTED_TARGET_YEARS or tuple(panel["classes"]) != EXPECTED_CLASSES:
                raise ContractError("官方年度目标面板必须覆盖 T20-T25 两类")
            _require_keys(panel["selection"], ("method", "max_entities_per_year_class"), f"{where}.selection")
            if panel["selection"] != {"method": "fixed_hash", "max_entities_per_year_class": 200000}:
                raise ContractError("官方年度目标面板选择规则不一致")
            if panel["qualification_receipt"] is not None:
                raise ContractError("官方批准面板不应伪造新实体资格收据")
        elif panel["panel_id"] == "source_validation_benign_v1":
            if panel["formal"] is not True or tuple(panel["years"]) != EXPECTED_SOURCE_YEARS or panel["classes"] != ["benign"]:
                raise ContractError("共同源验证良性面板定义不一致")
            _require_keys(panel["selection"], ("method",), f"{where}.selection")
            if panel["selection"] != {"method": "all_unique_exact_esld"}:
                raise ContractError("共同源验证良性面板选择规则不一致")
        elif panel["panel_id"] == "target_new_entity_annual_v1":
            if panel["formal"] is True or panel["qualification_receipt"] is not None:
                raise ContractError("未获资格收据的新实体面板不得标为正式或伪造收据")
            _require_keys(panel["selection"], ("method",), f"{where}.selection")
            if panel["selection"] != {"method": "qualification_receipt_driven"}:
                raise ContractError("新实体候选必须由资格收据驱动")
        else:
            raise ContractError(f"存在未批准的评价面板：{panel['panel_id']}")
    approved_panels = set(config["approved_panels"])
    if not approved_panels.issubset(panel_ids):
        raise ContractError(f"panels 未包含全部已批准面板：{sorted(approved_panels - panel_ids)}")
    if len(config["approved_panels"]) != 2 or approved_panels != {"target_official_annual_v1", "source_validation_benign_v1"}:
        raise ContractError("approved_panels 必须只含两个已批准面板")
    if "target_new_entity_annual_v1" in config["approved_panels"]:
        raise ContractError("新实体候选不得进入 approved_panels")

    attacks = config["attacks"]
    _require_keys(attacks, ("namespace", "algorithm_version", "alphabet", "tiers"), "attacks")
    _require_string(attacks["namespace"], "attacks.namespace")
    if attacks["alphabet"] != "abcdefghijklmnopqrstuvwxyz0123456789-":
        raise ContractError("攻击字符表不符合冻结合同")
    if attacks["algorithm_version"] != "shared_prefix_edit_v1":
        raise ContractError("攻击算子版本不符合冻结合同")
    tiers = attacks["tiers"]
    _require_type(tiers, list, "attacks.tiers")
    for index, tier in enumerate(tiers):
        _require_type(tier, dict, f"attacks.tiers[{index}]")
    if [tier.get("attack_tier") for tier in tiers] != ["k=1", "k=2", "random_half"]:
        raise ContractError("正式攻击档位必须严格为 k=1、k=2、random_half")
    for index, tier in enumerate(tiers):
        _require_keys(tier, ("attack_tier", "requested_budget"), f"attacks.tiers[{index}]")
        if tier["attack_tier"] == "k=1" and tier["requested_budget"] != "min(1, L)":
            raise ContractError("k=1 预算不一致")
        if tier["attack_tier"] == "k=2" and tier["requested_budget"] != "min(2, L)":
            raise ContractError("k=2 预算不一致")
        if tier["attack_tier"] == "random_half" and tier["requested_budget"] != "min(max(1, floor(L/2)), L)":
            raise ContractError("random_half 预算不一致")
    if any(term in json.dumps(attacks, ensure_ascii=False).lower() for term in ("krand", "maskdga")):
        raise ContractError("正式攻击配置不得包含历史攻击名称")

    thresholds = config["thresholds"]
    _require_keys(thresholds, ("source_panel", "workpoints", "decision_rule", "tie_group_policy"), "thresholds")
    if thresholds["source_panel"] != "source_validation_benign_v1":
        raise ContractError("阈值源面板必须是共同源验证良性清单")
    if thresholds["workpoints"] != [
        {"name": "tau_0p1", "alpha": 0.001},
        {"name": "tau_1p0", "alpha": 0.01},
    ]:
        raise ContractError("阈值工作点必须严格为 0.001 和 0.01")
    if thresholds["decision_rule"] != "score >= threshold":
        raise ContractError("恶意判定规则不一致")
    if thresholds["tie_group_policy"] != "whole_equal_score_groups":
        raise ContractError("阈值同分组策略不一致")
    result_contract = config["result_contract"]
    _require_keys(result_contract, ("clean_metrics", "pure_dga_metrics", "threshold_semantics", "t25_required"), "result_contract")
    _require_type(result_contract["clean_metrics"], list, "result_contract.clean_metrics")
    _require_type(result_contract["pure_dga_metrics"], list, "result_contract.pure_dga_metrics")
    _require_type(result_contract["threshold_semantics"], list, "result_contract.threshold_semantics")
    if result_contract["clean_metrics"] != ["accuracy", "precision", "recall", "f1", "ap", "roc_auc", "fpr", "fnr", "tpr"]:
        raise ContractError("clean_metrics 未完整声明冻结的干净混合指标")
    if result_contract["pure_dga_metrics"] != ["fnr", "tpr", "count", "clopper_pearson_95"]:
        raise ContractError("pure_dga_metrics 不得包含纯 DGA 面板非法混合指标")
    if result_contract["threshold_semantics"] != ["source_frozen", "target_informed_oracle_separate"]:
        raise ContractError("threshold_semantics 未分离源冻结与目标知情重标")
    if result_contract["t25_required"] is not True:
        raise ContractError("结果合同必须强制包含 T25")
    if _contains_key(config, "member_seed"):
        raise ContractError("配置文本不得出现 member_seed")


def _validate_training_config(config: Mapping[str, Any]) -> None:
    _require_keys(
        config,
        (
            "config_kind", "schema_version", "config_id", "contract_id", "data_revision", "evaluation_config",
            "backbone", "allowed_arms", "training", "checkpoint", "input_views",
            "output_layout", "allowed_modes", "forbidden_keys",
        ),
        "训练配置",
    )
    if config["schema_version"] != SCHEMA_VERSION or config["contract_id"] != SCHEMA_VERSION:
        raise ContractError("训练配置模式版本不匹配")
    if config["data_revision"] != DATA_REVISION:
        raise ContractError("训练配置 data_revision 不符合冻结值")
    if config["backbone"] not in ("drift", "bresnet"):
        raise ContractError("骨干只能是 drift 或 bresnet")
    if config["evaluation_config"] != "configs/ch3-drift-formal-evaluation-v1.json":
        raise ContractError("训练配置必须引用共享评价配置")
    if config["allowed_arms"] != list(ALLOWED_ARMS):
        raise ContractError("训练配置必须允许且只允许 A/B/D/F/G")
    _require_keys(config["training"], ("batch_size", "epochs", "seed", "optimizer", "learning_rate", "beta_benign", "online_augmentation_threshold"), "training")
    training = config["training"]
    for key in ("batch_size", "epochs", "seed"):
        _require_type(training[key], int, f"training.{key}")
        if training[key] <= 0:
            raise ContractError(f"training.{key} 必须为正数")
    if training["epochs"] != 3 or training["seed"] != 42:
        raise ContractError("正式训练 epochs 和 seed 必须冻结为 3 和 42")
    if training["optimizer"] != "Adam" or training["beta_benign"] != 3.0 or training["online_augmentation_threshold"] != 0.5:
        raise ContractError("训练优化器、良性权重或在线增强判定不符合冻结语义")
    if config["backbone"] == "drift":
        if training["batch_size"] != 1024 or training["learning_rate"] != {"backbone": 1e-6, "head": 1e-4}:
            raise ContractError("DRIFT 正式训练参数不符合已核对脚本")
    else:
        if training["batch_size"] != 128 or training["learning_rate"] != {"all_parameters": 1e-3}:
            raise ContractError("BResNet 正式训练参数不符合已核对协议")
    _require_keys(config["checkpoint"], ("schema_version", "save_every_batches", "save_at_epoch_end", "progress_semantics", "legacy_reuse"), "checkpoint")
    expected_checkpoint = "ch3_drift_official_p2p3_formal_checkpoint_v3" if config["backbone"] == "drift" else "ch3_drift_bresnet_p2p3_formal_checkpoint_v1"
    if config["checkpoint"]["schema_version"] != expected_checkpoint or config["checkpoint"]["save_every_batches"] != 2000 or config["checkpoint"]["save_at_epoch_end"] is not True or config["checkpoint"]["progress_semantics"] != "next_batch_to_process" or config["checkpoint"]["legacy_reuse"] is not False:
        raise ContractError("正式断点合同不一致或错误复用历史断点")
    _require_keys(config["input_views"], ("training", "validation"), "input_views")
    if config["input_views"] != {
        "training": "source_train_test_exact_unique_in_memory",
        "validation": "source_val_exact_unique_in_memory",
    }:
        raise ContractError("训练配置必须消费评价配置中的源角色直读唯一视图")
    _require_keys(config["output_layout"], ("run_root", "checkpoint", "model", "summary"), "output_layout")
    for value in config["output_layout"].values():
        _require_string(value, "output_layout 路径")
        resolve_repo_relative(value)
    if config["allowed_modes"] != list(ALLOWED_MODES):
        raise ContractError("训练配置 allowed_modes 不完整")
    _require_string_list(config["forbidden_keys"], "forbidden_keys")
    required_forbidden = {"member_seed", "target_limit", "attack_tier", "threshold_override", "arms"}
    if not required_forbidden.issubset(config["forbidden_keys"]):
        raise ContractError("训练配置未完整声明禁止的运行时覆盖键")
    if _contains_key(config, "member_seed"):
        raise ContractError("配置文本不得出现 member_seed")


def load_config(path_value: str | Path) -> tuple[dict[str, Any], str]:
    """严格读取并校验评价或训练配置，返回配置和规范哈希。"""
    path = resolve_repo_relative(path_value, must_exist=True)
    config = _load_json(path)
    _require_type(config, dict, "配置根")
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"配置 schema_version 必须为 {SCHEMA_VERSION}")
    if config.get("config_kind") == "evaluation":
        _validate_evaluation_config(config)
    elif config.get("config_kind") == "training":
        _validate_training_config(config)
    else:
        raise ContractError("config_kind 必须是 evaluation 或 training")
    return config, sha256_bytes(canonical_json_bytes(config))


def atomic_write_json(path_value: str | Path, payload: Mapping[str, Any]) -> str:
    """以同目录临时文件、同步和原子替换写入 JSON，返回规范哈希。"""
    path = resolve_repo_relative(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_json_bytes(dict(payload))
    digest = sha256_bytes(encoded)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".partial", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise ContractError(f"原子写入失败：{path}；{exc}") from exc
    return digest


def read_status(run_dir_value: str | Path) -> dict[str, Any] | None:
    run_dir = resolve_run_dir(run_dir_value)
    status_path = run_dir / "status.json"
    if not status_path.exists():
        return None
    status = _load_json(status_path)
    _require_type(status, dict, "status.json")
    _require_keys(status, ("status", "stage", "error_class", "recoverable"), "status.json")
    _require_string(status["stage"], "status.stage")
    if status["status"] not in ALLOWED_STATUS:
        raise ContractError(f"status.json 含未知状态：{status['status']}")
    if status["status"] == "failed":
        _require_string(status["error_class"], "status.error_class")
    elif status["error_class"] is not None:
        raise ContractError("非 failed 状态的 error_class 必须为 null")
    if not isinstance(status["recoverable"], bool):
        raise ContractError("status.recoverable 必须是布尔值")
    return status


def transition_status(run_dir_value: str | Path, new_status: str, *, stage: str, error_class: str | None = None, recoverable: bool = True) -> str:
    """执行受限状态迁移；不会为未实现下游创建虚假完成状态。"""
    if new_status not in ALLOWED_STATUS:
        raise ContractError(f"未知运行状态：{new_status}")
    _require_string(stage, "状态阶段")
    if not isinstance(recoverable, bool):
        raise ContractError("recoverable 必须是布尔值")
    run_dir = resolve_run_dir(run_dir_value)
    current = read_status(run_dir.relative_to(REPO_ROOT))
    if current is None:
        if new_status != "created":
            raise ContractError("新运行目录必须先创建为 created，不能跳过状态")
    elif new_status == "running" and current["status"] == "failed" and current["recoverable"] is False:
        raise ContractError("不可恢复的 failed 状态不得迁移回 running")
    elif new_status not in ALLOWED_TRANSITIONS[current["status"]]:
        raise ContractError(f"非法状态迁移：{current['status']} -> {new_status}")
    if new_status == "failed" and not error_class:
        raise ContractError("failed 状态必须记录错误类别")
    if new_status != "failed" and error_class is not None:
        raise ContractError("非 failed 状态不得记录错误类别")
    payload = {
        "status": new_status,
        "stage": stage,
        "error_class": error_class,
        "recoverable": recoverable,
    }
    return atomic_write_json(run_dir.relative_to(REPO_ROOT) / "status.json", payload)


def audit_input_roles(config: Mapping[str, Any]) -> dict[str, Any]:
    """只核对 30 个输入角色的仓库内路径和存在性，不扫描 Parquet 内容。"""
    _validate_input_roles(config)
    missing: list[str] = []
    files: list[dict[str, Any]] = []
    for role in config["input_roles"]:
        path = resolve_repo_relative(role["path"])
        if not path.is_file():
            missing.append(role["path"])
        else:
            files.append({"role": role["role"], "path": role["path"], "bytes": path.stat().st_size})
    return {"schema_version": SCHEMA_VERSION, "role_count": len(files), "missing": missing, "files": files, "complete": not missing}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DRIFT 正式评价共享合同与统一机械门禁")
    parser.add_argument("--gate", choices=ALLOWED_GATE_NAMES, required=True, help="门禁阶段")
    parser.add_argument("--config", required=True, help="仓库相对配置路径")
    parser.add_argument("--run-dir", required=True, help="仓库相对运行目录")
    parser.add_argument("--backbone", choices=("drift", "bresnet"), help="单臂评价或汇总使用的骨干")
    parser.add_argument("--arm", choices=ALLOWED_ARMS, help="单臂训练或评价使用的训练臂")
    mode = parser.add_mutually_exclusive_group()
    for name in ALLOWED_MODES:
        mode.add_argument(f"--{name}", dest="mode", action="store_const", const=name, help=f"请求 {name} 模式")
    mode.add_argument("--materialize", dest="mode", action="store_const", const="materialize", help=argparse.SUPPRESS)
    parser.set_defaults(mode="audit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        resolve_run_dir(args.run_dir)
        config, config_hash = load_config(args.config)
        if args.mode == "materialize":
            raise ContractError("--materialize 已废止；正式数据必须使用原 Parquet 只读直读")
        if args.gate == "inputs":
            if config.get("config_kind") != "evaluation":
                raise ContractError("inputs 门禁必须使用评价配置")
            audit = audit_input_roles(config)
            if not audit["complete"]:
                raise ContractError(f"真实输入角色缺失：{audit['missing']}")
            if args.mode != "audit":
                raise ContractError("inputs 门禁当前只实现 audit；直读下游由独立模块负责")
            print(json.dumps({"gate": args.gate, "mode": args.mode, "config_sha256": config_hash, "input_role_count": audit["role_count"], "audit_complete": True, "input_roles_complete": True, "assets_complete": False, "complete": False}, ensure_ascii=False, sort_keys=True))
            return 0
        if config.get("config_kind") != "training":
            raise ContractError(f"{args.gate} 门禁必须使用训练配置")
        if args.backbone and args.backbone != config["backbone"]:
            raise ContractError("命令行 backbone 与配置冲突")
        if args.gate in ("train", "evaluate") and args.arm is None:
            raise ContractError(f"{args.gate} 门禁必须明确一个训练臂，不接受 all")
        if args.gate == "compare" and args.arm is not None:
            raise ContractError("compare 门禁不得指定单个 arm")
        if args.mode != "audit":
            raise ContractError(f"{args.gate} 下游生产模块尚未实现；合同入口失败关闭，不创建虚假通过状态")
        print(json.dumps({"gate": args.gate, "mode": args.mode, "config_sha256": config_hash, "backbone": config["backbone"], "arm": args.arm, "contract_valid": True, "complete": False, "downstream_status": "未实现"}, ensure_ascii=False, sort_keys=True))
        return 0
    except ContractError as exc:
        print(f"合同门禁失败：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
