#!/usr/bin/env python3
"""只读绑定 GRANDE 已完成制品并修复 SwanLab 聚合指标发布。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from collections.abc import Mapping
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from flow_probe.tracking import (  # noqa: E402
    initialize_swanlab_run,
    load_swanlab_tag_aliases,
    validate_swanlab_contract,
    write_swanlab_tag_receipt,
)

SCHEMA_VERSION = "ch3-grande-swanlab-publish-repair-config-v1"
RUN_ID = "ch3-grande-swanlab-publish-repair-v1"
PARENT_RUN_ID = "ch3-grande-c00-protocolA-source-q0-seed42-v1-bf16-v1"
REPAIR_CONFIG_SHA256 = "f46528a644c9a7add2210187b2efd246f8213a9b4884fded05089553a270f46b"
TAG_ALIASES_SHA256 = "d2bf7212068e6d7ced2fa916cd327dd24fea26bbb3bd3cbd9fd241c77a3f7a16"
PARENT_MANIFEST_SHA256 = "b02ec174c7c107b232269b89038262ee7bd64b156967d25774bcabf212600d16"
PARENT_PRODUCTION_CONFIG_SHA256 = "af4b8cac2f4322498149d271ad8c93f3b118a31b718408038dfddef85c8d84a1"
PARENT_FROZEN_CONFIG_SHA256 = "11b2269788666060b42b1f37af1aaebb5c3a24ce03193ac1f77a2157c440193b"
CURRENT_SOURCE_RESULTS_SHA256 = "6dc3d8c06f42fb24d5429150f1ed0039a7bf7dd47df19bfbfa770d2220ff4e12"
MANIFEST_SOURCE_RESULTS_SHA256 = "13291c39ff551c99f75b40cfa9f88c7edeee98f6afd05c279f3cddc9a877fab7"
CURRENT_GRANDE_RESULTS_SHA256 = "13291c39ff551c99f75b40cfa9f88c7edeee98f6afd05c279f3cddc9a877fab7"
CURRENT_RESOURCE_RECEIPT_SHA256 = "fa0f8ccfa7206487d8f24e7802f124e23040167850f78c932876444c15113ff3"
CURRENT_STATUS_SHA256 = "6ab7b838966876fc3e232820235f2e80cc6d0f5fdfe9a7d772d62209f2ab5418"
REQUIRED_UNITS = ("G-A", "G-B")
ALLOWED_PARENT_MANIFEST_DRIFT = frozenset(
    ("source-screen-results.json", "resource-receipt.json", "status.json")
)
PROHIBITED_OPERATIONS = (
    "prepare",
    "resource-calibrate",
    "train-unit",
    "aggregate",
    "training-data-read",
    "gpu-read",
    "parent-artifact-write",
)
EXPECTED_SWANLAB_DESTINATION = {
    "workspace": "mortiswang",
    "project": "ns3-rwkv-lspr24",
    "name": "GRANDE协议A源年BF16零重训发布修复",
    "group": RUN_ID,
    "mode": "cloud",
    "tags": [
        "chapter3",
        "grande",
        "protocol-a",
        "source-q0",
        "seed42",
        "bf16",
        "fp32-sensitive",
        "same-precision-selection",
        "publish-repair",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GRANDE 零重训 SwanLab 发布修复")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--alias-config", type=Path)
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--verify-completed", action="store_true")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--attempt", type=int, choices=(1, 2), default=1)
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"无法读取 JSON：{path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON 顶层必须为对象：{path}")
    return value


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_alias_path(config: Mapping[str, Any], override: Path | None) -> Path:
    configured = config.get("paths", {}).get("tag_aliases")
    if configured != "configs/swanlab-tag-aliases-v1.json":
        raise ValueError("标签别名路径必须与发布修复身份精确冻结")
    expected = (PROJECT_ROOT / configured).resolve()
    if override is not None and override.resolve() != expected:
        raise ValueError("--alias-config 不得改变冻结的标签别名路径")
    if sha256_file(expected) != TAG_ALIASES_SHA256:
        raise ValueError("标签别名文件哈希与冻结值不一致")
    return expected


def expected_parent_artifacts() -> dict[str, str]:
    return {
        "frozen_config": "config.json",
        "source_screen_results": "source-screen-results.json",
        "grande_source_results": "grande-c00-source-results.json",
        "selection_seal": "backbone_selection_frozen.json",
        "aggregate_curves": "complete-alert-budget-curves.npz",
        "aggregate_curves_receipt": "complete-alert-budget-curves-receipt.json",
        "selection_g_a": "receipts/selection-G-A.json",
        "selection_g_b": "receipts/selection-G-B.json",
        "checkpoint_g_a": "checkpoints/selected-G-A.pt",
        "checkpoint_g_b": "checkpoints/selected-G-B.pt",
        "resource_receipt": "resource-receipt.json",
        "failed_status": "status.json",
        "parent_manifest": "manifest.json",
    }


def validate_config(
    config: dict[str, Any],
    *,
    config_path: Path,
    alias_path: Path,
    authorized_workspace: str | None,
    authorized_project: str | None,
) -> dict[str, object]:
    expected_config_path = (
        PROJECT_ROOT / "configs" / "ch3-grande-swanlab-publish-repair-v1.json"
    ).resolve()
    if config_path != expected_config_path:
        raise ValueError("发布修复配置路径与运行身份冻结值不一致")
    if sha256_file(config_path) != REPAIR_CONFIG_SHA256:
        raise ValueError("发布修复配置哈希与运行身份冻结值不一致")
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("发布修复配置模式或运行身份不符")
    if config.get("display_name") != EXPECTED_SWANLAB_DESTINATION["name"]:
        raise ValueError("发布修复展示身份不符")
    paths = config.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("paths 必须为对象")
    if Path(str(paths.get("output_root", ""))).name != RUN_ID:
        raise ValueError("发布修复输出根与运行身份不符")
    if Path(str(paths.get("parent_root", ""))).name != PARENT_RUN_ID:
        raise ValueError("父运行根与冻结身份不符")
    if paths.get("tag_aliases_sha256") != TAG_ALIASES_SHA256:
        raise ValueError("配置中的标签别名哈希不符")
    if alias_path != (PROJECT_ROOT / "configs/swanlab-tag-aliases-v1.json").resolve():
        raise ValueError("标签别名实际路径不符")
    parent = config.get("parent_binding")
    expected_parent_fields = {
        "run_id": PARENT_RUN_ID,
        "production_config_sha256": PARENT_PRODUCTION_CONFIG_SHA256,
        "frozen_config_sha256": PARENT_FROZEN_CONFIG_SHA256,
        "manifest_sha256": PARENT_MANIFEST_SHA256,
        "current_source_screen_results_sha256": CURRENT_SOURCE_RESULTS_SHA256,
        "manifest_source_screen_results_sha256": MANIFEST_SOURCE_RESULTS_SHA256,
        "current_grande_source_results_sha256": CURRENT_GRANDE_RESULTS_SHA256,
        "current_resource_receipt_sha256": CURRENT_RESOURCE_RECEIPT_SHA256,
        "current_status_sha256": CURRENT_STATUS_SHA256,
        "expected_status": {"state": "failed", "exit_code": 1},
        "required_units": list(REQUIRED_UNITS),
        "epochs_per_unit": 20,
        "optimizer_steps_per_unit": 20000,
        "expected_selected_epochs": {"G-B": 9},
        "required_artifacts": expected_parent_artifacts(),
    }
    if parent != expected_parent_fields:
        raise ValueError("父运行绑定合同不符")
    if config.get("swanlab") != EXPECTED_SWANLAB_DESTINATION:
        raise ValueError("SwanLab 目的地与发布修复身份不符")
    if config.get("allowed_operations") != [
        "swanlab-ping",
        "swanlab-verify",
        "parent-artifact-hash-verification",
        "aggregate-metric-upload",
    ]:
        raise ValueError("发布修复允许动作不符")
    if config.get("prohibited_operations") != list(PROHIBITED_OPERATIONS):
        raise ValueError("发布修复禁止动作不符")
    if (
        config.get("source_year_only") is not True
        or config.get("target_year_arrays_read") != 0
        or config.get("target_year_paths_enumerated") != 0
        or config.get("new_cells_trained") != []
        or config.get("parent_artifacts_mutated") is not False
        or config.get("formal_paper_evidence") is not False
        or config.get("independent_test") is not False
    ):
        raise ValueError("零重训与证据边界不符")
    aliases = load_swanlab_tag_aliases(alias_path)
    return validate_swanlab_contract(
        config["swanlab"],
        aliases=aliases,
        authorized_workspace=authorized_workspace,
        authorized_project=authorized_project,
    )


def artifact_record(path: Path, parent_root: Path) -> dict[str, object]:
    if not path.is_file():
        raise RuntimeError(f"父运行必需制品缺失：{path}")
    return {
        "relative_path": str(path.relative_to(parent_root)),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def validate_parent_manifest(parent_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = parent_root / "manifest.json"
    if sha256_file(manifest_path) != PARENT_MANIFEST_SHA256:
        raise RuntimeError("父 manifest 哈希与冻结值不一致")
    manifest = load_json(manifest_path)
    files = manifest.get("files")
    if (
        manifest.get("schema_version") != "ch3-grande-protocol-a-source-q0-manifest-v1"
        or manifest.get("run_id") != PARENT_RUN_ID
        or not isinstance(files, dict)
        or len(files) != 23
    ):
        raise RuntimeError("父 manifest 模式、运行身份或 23 项文件清单不符")
    current_records: dict[str, Any] = {}
    drifted: list[str] = []
    for relative, recorded in files.items():
        if not isinstance(relative, str) or not isinstance(recorded, dict):
            raise RuntimeError("父 manifest 文件条目类型不符")
        path = parent_root / relative
        current = artifact_record(path, parent_root)
        current_records[relative] = current
        if current["sha256"] != recorded.get("sha256") or current["bytes"] != recorded.get("bytes"):
            if relative not in ALLOWED_PARENT_MANIFEST_DRIFT:
                raise RuntimeError(f"父 manifest 非法漂移：{relative}")
            drifted.append(relative)
    if set(drifted) != ALLOWED_PARENT_MANIFEST_DRIFT:
        raise RuntimeError("父 manifest 合法后置漂移必须精确为结果、资源和状态三项")
    source_record = files.get("source-screen-results.json")
    if not isinstance(source_record, dict) or source_record.get("sha256") != MANIFEST_SOURCE_RESULTS_SHA256:
        raise RuntimeError("父 manifest 中旧源侧结果哈希不符")
    return manifest, current_records


def validate_parent_semantics(
    config: dict[str, Any], parent_root: Path, artifacts: Mapping[str, Mapping[str, object]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    production_config_path = Path(config["paths"]["parent_config"])
    frozen_config_path = parent_root / "config.json"
    if sha256_file(production_config_path) != PARENT_PRODUCTION_CONFIG_SHA256:
        raise RuntimeError("父生产配置哈希与冻结值不一致")
    if sha256_file(frozen_config_path) != PARENT_FROZEN_CONFIG_SHA256:
        raise RuntimeError("父运行冻结配置哈希与冻结值不一致")
    if load_json(production_config_path) != load_json(frozen_config_path):
        raise RuntimeError("父生产配置与运行冻结配置 JSON 语义不一致")
    exact_hashes = {
        "source_screen_results": CURRENT_SOURCE_RESULTS_SHA256,
        "grande_source_results": CURRENT_GRANDE_RESULTS_SHA256,
        "resource_receipt": CURRENT_RESOURCE_RECEIPT_SHA256,
        "failed_status": CURRENT_STATUS_SHA256,
        "parent_manifest": PARENT_MANIFEST_SHA256,
    }
    for key, expected in exact_hashes.items():
        if artifacts[key]["sha256"] != expected:
            raise RuntimeError(f"父运行当前制品哈希不符：{key}")
    manifest, manifest_current_records = validate_parent_manifest(parent_root)
    source_result = load_json(parent_root / "source-screen-results.json")
    grande_result = load_json(parent_root / "grande-c00-source-results.json")
    resource_receipt = load_json(parent_root / "resource-receipt.json")
    status = load_json(parent_root / "status.json")
    if status.get("state") != "failed" or status.get("exit_code") != 1:
        raise RuntimeError("父运行原失败状态不符，拒绝覆盖或猜测修复")
    source_without_admission = copy.deepcopy(source_result)
    resource = source_without_admission.get("resource")
    if not isinstance(resource, dict):
        raise RuntimeError("父源侧结果缺少资源对象")
    launcher_admission = resource.pop("launcher_admission_receipt", None)
    if not isinstance(launcher_admission, dict) or len(launcher_admission) != 7:
        raise RuntimeError("父源侧结果后置资源收据必须精确包含 7 个键")
    if launcher_admission != resource_receipt:
        raise RuntimeError("父源侧结果后置资源收据与当前资源收据不一致")
    if source_without_admission != grande_result:
        raise RuntimeError("父两个源侧结果除后置资源收据外存在差异")
    if source_result.get("target_year_arrays_read") != 0:
        raise RuntimeError("父结果违反目标年零读取合同")
    source_selection = source_result.get("source_selection")
    if not isinstance(source_selection, dict):
        raise RuntimeError("父结果缺少源侧选择")
    completed = source_selection.get("completed_structures")
    if not isinstance(completed, list):
        raise RuntimeError("父结果缺少已完成结构")
    by_unit = {item.get("unit_key"): item for item in completed if isinstance(item, dict)}
    if tuple(by_unit) != REQUIRED_UNITS or len(by_unit) != len(REQUIRED_UNITS):
        raise RuntimeError("父运行必须按 G-A、G-B 完整绑定")
    for unit in REQUIRED_UNITS:
        item = by_unit[unit]
        if len(item.get("history", [])) != 20 or item.get("optimizer_steps") != 20000:
            raise RuntimeError(f"父运行 {unit} 未满足 20 轮、20000 步完成条件")
        selection_receipt = load_json(parent_root / f"receipts/selection-{unit}.json")
        selection = selection_receipt.get("selection")
        if not isinstance(selection, dict) or selection.get("unit_key") != unit:
            raise RuntimeError(f"父运行 {unit} 选择收据不符")
        if selection.get("selected_epoch") != item.get("selected_epoch"):
            raise RuntimeError(f"父运行 {unit} 聚合结果与选择收据轮次不一致")
        checkpoint = selection.get("checkpoint")
        artifact_key = "checkpoint_g_a" if unit == "G-A" else "checkpoint_g_b"
        if not isinstance(checkpoint, dict) or checkpoint.get("sha256") != artifacts[artifact_key]["sha256"]:
            raise RuntimeError(f"父运行 {unit} 检查点哈希不一致")
    if by_unit["G-B"].get("selected_epoch") != 9:
        raise RuntimeError("父运行 G-B 选中轮次不是冻结的第 9 轮")
    curve_receipt = load_json(parent_root / "complete-alert-budget-curves-receipt.json")
    if curve_receipt.get("sha256") != artifacts["aggregate_curves"]["sha256"]:
        raise RuntimeError("父运行聚合曲线与曲线收据哈希不一致")
    verification = {
        "manifest_schema_version": manifest["schema_version"],
        "manifest_file_count": len(manifest["files"]),
        "allowed_post_manifest_drift": sorted(ALLOWED_PARENT_MANIFEST_DRIFT),
        "manifest_current_records": manifest_current_records,
        "production_and_frozen_config_json_equal": True,
        "source_results_only_added_launcher_admission_receipt": True,
        "launcher_admission_receipt_key_count": 7,
        "launcher_admission_receipt_equals_resource_receipt": True,
    }
    return source_result, verification


def build_parent_binding(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    parent_root = Path(config["paths"]["parent_root"])
    artifacts = {
        key: artifact_record(parent_root / relative, parent_root)
        for key, relative in expected_parent_artifacts().items()
    }
    result, verification = validate_parent_semantics(config, parent_root, artifacts)
    binding = {
        "schema_version": "ch3-grande-swanlab-parent-binding-v2",
        "parent_run_id": PARENT_RUN_ID,
        "parent_root": str(parent_root),
        "parent_config_path": str(config["paths"]["parent_config"]),
        "production_config_sha256": PARENT_PRODUCTION_CONFIG_SHA256,
        "frozen_config_sha256": PARENT_FROZEN_CONFIG_SHA256,
        "parent_manifest_sha256": PARENT_MANIFEST_SHA256,
        "artifacts": artifacts,
        "manifest_reverse_verification": verification,
        "required_units": list(REQUIRED_UNITS),
        "selection_complete": True,
        "parent_failed_evidence_preserved": True,
        "parent_artifacts_mutated": False,
        "new_cells_trained": [],
        "target_year_arrays_read": 0,
    }
    return binding, result


def verify_parent_unchanged(config: dict[str, Any], binding: Mapping[str, Any]) -> None:
    parent_root = Path(config["paths"]["parent_root"])
    records = binding["manifest_reverse_verification"]["manifest_current_records"]
    for record in records.values():
        path = parent_root / str(record["relative_path"])
        if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"父运行制品在发布期间发生漂移：{path}")
    production_config = Path(config["paths"]["parent_config"])
    if sha256_file(production_config) != PARENT_PRODUCTION_CONFIG_SHA256:
        raise RuntimeError("父生产配置在发布期间发生漂移")
    if sha256_file(parent_root / "manifest.json") != PARENT_MANIFEST_SHA256:
        raise RuntimeError("父 manifest 在发布期间发生漂移")


def build_metrics(result: Mapping[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for selection in result["source_selection"]["completed_structures"]:
        prefix = f"source/{selection['unit_key']}"
        metrics[f"{prefix}/selected_epoch"] = float(selection["selected_epoch"])
        metrics[f"{prefix}/validation_flow_ap"] = float(selection["validation_flow_ap"])
        metrics[f"{prefix}/diagnostic_entity_ap"] = float(
            selection["diagnostic_entity"]["entity_average_precision"]
        )
        metrics[f"{prefix}/parameter_count"] = float(selection["parameter_count_framework"])
        metrics[f"{prefix}/training_seconds"] = float(selection["training_seconds"])
        metrics[f"{prefix}/peak_gpu_allocated_mib"] = float(selection["peak_gpu_allocated_mib"])
        for key, value in selection["diagnostic_entity"]["dr_at_fpr"].items():
            metrics[f"{prefix}/diagnostic_dr_fpr_{key}"] = float(value)
    metrics["source/gate_passed"] = float(result["verdict"]["passed"])
    metrics["runtime/new_cells_trained"] = 0.0
    metrics["runtime/target_year_arrays_read"] = 0.0
    metrics["runtime/publish_repair_only"] = 1.0
    return metrics


def status_value(
    state: str,
    stage: str,
    exit_code: int | None,
    detail: str,
    attempt: int,
    retryable_401: bool,
) -> dict[str, Any]:
    return {
        "schema_version": "ch3-grande-swanlab-publish-repair-status-v2",
        "run_id": RUN_ID,
        "parent_run_id": PARENT_RUN_ID,
        "state": state,
        "stage": stage,
        "exit_code": exit_code,
        "detail": detail,
        "attempt": attempt,
        "retryable_zero_step_init_401": retryable_401,
        "updated_at_unix": time.time(),
        "new_cells_trained": [],
        "target_year_arrays_read": 0,
        "parent_artifacts_mutated": False,
    }


def write_status(
    output_root: Path,
    attempt_root: Path,
    state: str,
    stage: str,
    exit_code: int | None,
    detail: str,
    attempt: int,
    retryable_401: bool = False,
) -> None:
    value = status_value(state, stage, exit_code, detail, attempt, retryable_401)
    atomic_json(output_root / "status.json", value)
    atomic_json(attempt_root / "status.json", value)


def log(output_root: Path, attempt_root: Path, message: str) -> None:
    line = f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {message}"
    print(line, flush=True)
    for path in (output_root / "publish-repair.log", attempt_root / "publish-repair.log"):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def run_tracking_gate(attempt_root: Path) -> dict[str, Any]:
    gate_root = attempt_root / "tracking-gate"
    gate_root.mkdir(parents=True, exist_ok=True)
    commands = {
        "ping": ["uv", "run", "--no-sync", "swanlab", "ping"],
        "verify": ["uv", "run", "--no-sync", "swanlab", "verify"],
    }
    receipt: dict[str, Any] = {
        "schema_version": "ch3-grande-swanlab-publish-repair-tracking-gate-v2",
        "commands": {},
    }
    for name, command in commands.items():
        log_path = gate_root / f"swanlab-{name}.log"
        with log_path.open("wb") as handle:
            completed = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                stdout=handle,
                stderr=subprocess.STDOUT,
                check=False,
            )
        receipt["commands"][name] = {"exit_code": completed.returncode, "log": str(log_path)}
        if completed.returncode != 0:
            atomic_json(attempt_root / "tracking-gate-receipt.json", receipt)
            raise RuntimeError(f"SwanLab {name} 门失败，退出码 {completed.returncode}")
    receipt["passed"] = True
    atomic_json(attempt_root / "tracking-gate-receipt.json", receipt)
    return receipt


def identity_paths(config_path: Path, alias_path: Path) -> dict[str, Path]:
    return {
        "repair-config": config_path,
        "tag-aliases": alias_path,
        "repair-tool": Path(__file__).resolve(),
        "tracking-module": SRC_ROOT / "flow_probe" / "tracking.py",
        "launcher": PROJECT_ROOT
        / "scripts"
        / "remote_launchers"
        / "run_ch3_grande_swanlab_publish_repair_v1.sh",
    }


def build_manifest(
    output_root: Path,
    config_path: Path,
    alias_path: Path,
    *,
    publish_completed: bool,
    attempt: int,
) -> None:
    relative_files = [
        "parent-binding.json",
        "tag-receipt.json",
        "swanlab-receipt.json",
        "status.json",
        "publish-repair.log",
    ]
    for attempt_number in range(1, attempt + 1):
        prefix = f"attempts/attempt-{attempt_number}"
        relative_files.extend(
            (
                f"{prefix}/status.json",
                f"{prefix}/publish-repair.log",
                f"{prefix}/tag-receipt.json",
                f"{prefix}/tracking-gate-receipt.json",
                f"{prefix}/tracking-gate/swanlab-ping.log",
                f"{prefix}/tracking-gate/swanlab-verify.log",
            )
        )
    files: dict[str, Any] = {}
    for relative in relative_files:
        path = output_root / relative
        if path.is_file():
            files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    identities = {
        name: {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for name, path in identity_paths(config_path, alias_path).items()
    }
    atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-grande-swanlab-publish-repair-manifest-v2",
            "run_id": RUN_ID,
            "parent_run_id": PARENT_RUN_ID,
            "attempt": attempt,
            "publish_completed": publish_completed,
            "files": files,
            "identity_files": identities,
            "published_existing_aggregate_metrics_only": publish_completed,
            "new_cells_trained": [],
            "training_data_read": False,
            "gpu_read": False,
            "target_year_arrays_read": 0,
            "parent_artifacts_mutated": False,
        },
    )


def verify_file_records(root: Path, records: Mapping[str, Any]) -> None:
    for relative, record in records.items():
        if not isinstance(record, dict):
            raise RuntimeError(f"manifest 文件记录类型不符：{relative}")
        path = root / relative
        if (
            not path.is_file()
            or path.stat().st_size != record.get("bytes")
            or sha256_file(path) != record.get("sha256")
        ):
            raise RuntimeError(f"manifest 登记文件缺失或漂移：{relative}")


def verify_identity_records(
    manifest: Mapping[str, Any], config_path: Path, alias_path: Path
) -> None:
    records = manifest.get("identity_files")
    if not isinstance(records, dict) or set(records) != set(identity_paths(config_path, alias_path)):
        raise RuntimeError("发布修复生产身份文件清单不符")
    for name, path in identity_paths(config_path, alias_path).items():
        record = records[name]
        if (
            record.get("path") != str(path)
            or record.get("bytes") != path.stat().st_size
            or record.get("sha256") != sha256_file(path)
        ):
            raise RuntimeError(f"发布修复生产身份漂移：{name}")


def validate_completed_output(config: dict[str, Any], config_path: Path, alias_path: Path) -> None:
    output_root = Path(config["paths"]["output_root"])
    manifest = load_json(output_root / "manifest.json")
    status = load_json(output_root / "status.json")
    if (
        manifest.get("schema_version") != "ch3-grande-swanlab-publish-repair-manifest-v2"
        or manifest.get("run_id") != RUN_ID
        or manifest.get("parent_run_id") != PARENT_RUN_ID
        or manifest.get("publish_completed") is not True
        or manifest.get("published_existing_aggregate_metrics_only") is not True
    ):
        raise RuntimeError("完成 manifest 身份或 publish_completed 不符")
    attempt = manifest.get("attempt")
    if attempt not in (1, 2):
        raise RuntimeError("完成 manifest 尝试编号不符")
    if (
        status.get("state") != "complete"
        or status.get("stage") != "published"
        or status.get("exit_code") != 0
        or status.get("attempt") != attempt
        or status.get("retryable_zero_step_init_401") is not False
    ):
        raise RuntimeError("完成状态与 manifest 不一致")
    required = {
        "parent-binding.json",
        "tag-receipt.json",
        "swanlab-receipt.json",
        "status.json",
        "publish-repair.log",
    }
    for attempt_number in range(1, attempt + 1):
        prefix = f"attempts/attempt-{attempt_number}"
        required.update(
            (
                f"{prefix}/status.json",
                f"{prefix}/publish-repair.log",
                f"{prefix}/tag-receipt.json",
                f"{prefix}/tracking-gate-receipt.json",
                f"{prefix}/tracking-gate/swanlab-ping.log",
                f"{prefix}/tracking-gate/swanlab-verify.log",
            )
        )
    records = manifest.get("files")
    if not isinstance(records, dict) or not required.issubset(records):
        raise RuntimeError("完成 manifest 缺少必需登记文件")
    verify_file_records(output_root, records)
    verify_identity_records(manifest, config_path, alias_path)
    attempt_status = load_json(output_root / "attempts" / f"attempt-{attempt}" / "status.json")
    if attempt_status != status:
        raise RuntimeError("完成顶层状态与最终尝试状态不一致")
    binding = load_json(output_root / "parent-binding.json")
    verify_parent_unchanged(config, binding)
    tag_receipt = load_json(output_root / "tag-receipt.json")
    if (
        tag_receipt.get("expected_swanlab_version") != "0.9.0"
        or tag_receipt.get("actual_swanlab_version") != "0.9.0"
        or tag_receipt.get("alias_config_sha256") != TAG_ALIASES_SHA256
        or tag_receipt.get("requested_mode") != "cloud"
        or tag_receipt.get("effective_mode") != "online"
    ):
        raise RuntimeError("完成标签收据版本、别名或模式绑定不符")
    swanlab_receipt = load_json(output_root / "swanlab-receipt.json")
    if (
        swanlab_receipt.get("repair_run_id") != RUN_ID
        or swanlab_receipt.get("aggregate_only") is not True
        or swanlab_receipt.get("parent_artifacts_mutated") is not False
    ):
        raise RuntimeError("完成 SwanLab 收据身份或零重训边界不符")


def validate_retryable_attempt_one(
    config: dict[str, Any], config_path: Path, alias_path: Path
) -> None:
    output_root = Path(config["paths"]["output_root"])
    status = load_json(output_root / "status.json")
    attempt_status = load_json(output_root / "attempts" / "attempt-1" / "status.json")
    manifest = load_json(output_root / "manifest.json")
    if status != attempt_status:
        raise RuntimeError("首次 401 顶层状态与保留状态不一致")
    if (
        status.get("state") != "failed"
        or status.get("attempt") != 1
        or status.get("retryable_zero_step_init_401") is not True
        or manifest.get("publish_completed") is not False
        or manifest.get("attempt") != 1
    ):
        raise RuntimeError("输出根不是可重试的首次零步初始化 401")
    records = manifest.get("files")
    if not isinstance(records, dict):
        raise RuntimeError("首次失败 manifest 文件记录缺失")
    verify_file_records(output_root, records)
    verify_identity_records(manifest, config_path, alias_path)
    if (output_root / "attempts" / "attempt-2").exists():
        raise RuntimeError("第二次尝试目录已存在，禁止第三次初始化")


def is_zero_step_init_401(exc: BaseException, stage: str, attempt: int) -> bool:
    return attempt == 1 and stage == "swanlab-init" and "401" in str(exc)


def publish(
    config: dict[str, Any],
    config_path: Path,
    alias_path: Path,
    args: argparse.Namespace,
) -> None:
    output_root = Path(config["paths"]["output_root"])
    attempt = args.attempt
    if output_root.exists():
        try:
            validate_completed_output(config, config_path, alias_path)
        except BaseException:
            if attempt != 2:
                raise RuntimeError(f"发布修复输出根已存在且未通过完整完成复核：{output_root}")
            validate_retryable_attempt_one(config, config_path, alias_path)
        else:
            print(f"发布修复已完整复核，不重复创建 SwanLab 运行：{output_root}")
            return
    elif attempt != 1:
        raise RuntimeError("没有首次 401 失败证据，禁止直接执行第二次初始化")
    else:
        output_root.mkdir(parents=True)
    attempt_root = output_root / "attempts" / f"attempt-{attempt}"
    attempt_root.mkdir(parents=True, exist_ok=False)
    swanlab_module: object | None = None
    run_finished = False
    stage = "parent-binding"
    try:
        write_status(output_root, attempt_root, "running", stage, None, "开始只读绑定父运行制品", attempt)
        binding, result = build_parent_binding(config)
        atomic_json(output_root / "parent-binding.json", binding)
        log(output_root, attempt_root, "父运行 manifest、G-A/G-B 选择、曲线、检查点、资源与配置语义绑定通过")
        stage = "tracking-gate"
        write_status(output_root, attempt_root, "running", stage, None, "执行 SwanLab ping 与 verify", attempt)
        run_tracking_gate(attempt_root)
        metrics = build_metrics(result)
        stage = "swanlab-init"
        write_status(output_root, attempt_root, "running", stage, None, "创建独立聚合发布身份", attempt)
        swanlab_module, run, tag_receipt = initialize_swanlab_run(
            config["swanlab"],
            alias_config_path=alias_path,
            expected_alias_config_sha256=TAG_ALIASES_SHA256,
            config={
                "run_id": RUN_ID,
                "parent_run_id": PARENT_RUN_ID,
                "repair_config_sha256": REPAIR_CONFIG_SHA256,
                "parent_production_config_sha256": PARENT_PRODUCTION_CONFIG_SHA256,
                "parent_frozen_config_sha256": PARENT_FROZEN_CONFIG_SHA256,
                "published_existing_aggregate_metrics_only": True,
                "new_cells_trained": [],
                "target_year_arrays_read": 0,
            },
            log_dir=attempt_root / "swanlog",
            tag_receipt_path=attempt_root / "tag-receipt.json",
            authorized_workspace=args.authorized_swanlab_workspace,
            authorized_project=args.authorized_swanlab_project,
        )
        stage = "swanlab-log"
        swanlab_module.log(metrics, step=0)
        swanlab_module.finish()
        run_finished = True
        verify_parent_unchanged(config, binding)
        write_swanlab_tag_receipt(output_root / "tag-receipt.json", tag_receipt)
        atomic_json(
            output_root / "swanlab-receipt.json",
            {
                "schema_version": "ch3-grande-swanlab-publish-repair-receipt-v2",
                "repair_run_id": RUN_ID,
                "swanlab_run_id": str(run.id),
                "attempt": attempt,
                "workspace": config["swanlab"]["workspace"],
                "project": config["swanlab"]["project"],
                "name": config["swanlab"]["name"],
                "group": config["swanlab"]["group"],
                "requested_mode": tag_receipt["requested_mode"],
                "effective_mode": tag_receipt["effective_mode"],
                "effective_tags": tag_receipt["effective_tags"],
                "metric_count": len(metrics),
                "metric_keys": sorted(metrics),
                "aggregate_only": True,
                "published_existing_parent_metrics": True,
                "new_cells_trained": [],
                "target_year_arrays_read": 0,
                "parent_artifacts_mutated": False,
            },
        )
        log(output_root, attempt_root, "GRANDE SwanLab 零重训发布修复完成")
        write_status(
            output_root,
            attempt_root,
            "complete",
            "published",
            0,
            "既有聚合指标已通过独立身份发布",
            attempt,
        )
        build_manifest(output_root, config_path, alias_path, publish_completed=True, attempt=attempt)
    except BaseException as exc:
        if swanlab_module is not None and not run_finished:
            try:
                swanlab_module.finish(state="crashed", error=str(exc))
                run_finished = True
            except BaseException:
                pass
        retryable_401 = is_zero_step_init_401(exc, stage, attempt)
        log(output_root, attempt_root, f"发布修复第 {attempt} 次尝试失败：{exc}")
        write_status(
            output_root,
            attempt_root,
            "failed",
            stage,
            1,
            str(exc),
            attempt,
            retryable_401,
        )
        build_manifest(output_root, config_path, alias_path, publish_completed=False, attempt=attempt)
        raise


def main() -> int:
    args = parse_args()
    if sum((args.validate_config, args.verify_completed, args.publish)) != 1:
        raise SystemExit("必须且只能选择 --validate-config、--verify-completed 或 --publish")
    config_path = args.config.resolve()
    config = load_json(config_path)
    alias_path = resolve_alias_path(config, args.alias_config)
    validate_config(
        config,
        config_path=config_path,
        alias_path=alias_path,
        authorized_workspace=args.authorized_swanlab_workspace,
        authorized_project=args.authorized_swanlab_project,
    )
    if args.validate_config:
        print("GRANDE_SWANLAB_PUBLISH_REPAIR_CONFIG_VALID")
        return 0
    if args.verify_completed:
        validate_completed_output(config, config_path, alias_path)
        print("GRANDE_SWANLAB_PUBLISH_REPAIR_COMPLETED_OUTPUT_VALID")
        return 0
    if not args.authorized_swanlab_workspace or not args.authorized_swanlab_project:
        raise SystemExit("发布时必须显式提供 SwanLab 工作区与项目授权")
    try:
        publish(config, config_path, alias_path, args)
    except BaseException:
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
