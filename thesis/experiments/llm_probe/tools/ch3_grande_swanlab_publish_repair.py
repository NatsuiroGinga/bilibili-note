#!/usr/bin/env python3
"""只读绑定 GRANDE 已完成制品并修复 SwanLab 聚合指标发布。"""

from __future__ import annotations

import argparse
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
)

SCHEMA_VERSION = "ch3-grande-swanlab-publish-repair-config-v1"
RUN_ID = "ch3-grande-swanlab-publish-repair-v1"
PARENT_RUN_ID = "ch3-grande-c00-protocolA-source-q0-seed42-v1-bf16-v1"
PARENT_CONFIG_SHA256 = "af4b8cac2f4322498149d271ad8c93f3b118a31b718408038dfddef85c8d84a1"
REQUIRED_UNITS = ("G-A", "G-B")
PROHIBITED_OPERATIONS = (
    "prepare",
    "resource-calibrate",
    "train-unit",
    "aggregate",
    "training-data-read",
    "gpu-read",
    "parent-artifact-write",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GRANDE 零重训 SwanLab 发布修复")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--alias-config", type=Path)
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--publish", action="store_true")
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
    if override is not None:
        return override.resolve()
    configured = Path(str(config["paths"]["tag_aliases"]))
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


def validate_config(
    config: dict[str, Any],
    *,
    alias_path: Path,
    authorized_workspace: str | None,
    authorized_project: str | None,
) -> dict[str, object]:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("发布修复配置模式或运行身份不符")
    if config.get("display_name") != "GRANDE协议A源年BF16零重训发布修复":
        raise ValueError("发布修复展示身份不符")
    paths = config.get("paths")
    if not isinstance(paths, dict):
        raise ValueError("paths 必须为对象")
    if Path(str(paths.get("output_root", ""))).name != RUN_ID:
        raise ValueError("发布修复输出根与运行身份不符")
    if Path(str(paths.get("parent_root", ""))).name != PARENT_RUN_ID:
        raise ValueError("父运行根与冻结身份不符")
    parent = config.get("parent_binding")
    if not isinstance(parent, dict) or parent.get("run_id") != PARENT_RUN_ID:
        raise ValueError("父运行绑定身份不符")
    if parent.get("config_sha256") != PARENT_CONFIG_SHA256:
        raise ValueError("父配置哈希不符")
    if parent.get("expected_status") != {"state": "failed", "exit_code": 1}:
        raise ValueError("父失败状态绑定不符")
    if parent.get("required_units") != list(REQUIRED_UNITS):
        raise ValueError("父运行结构绑定不符")
    if parent.get("epochs_per_unit") != 20 or parent.get("optimizer_steps_per_unit") != 20000:
        raise ValueError("父运行训练完成条件不符")
    if parent.get("expected_selected_epochs") != {"G-B": 9}:
        raise ValueError("父运行 G-B 选择轮次绑定不符")
    expected_artifacts = {
        "frozen_config": "config.json",
        "source_screen_results": "source-screen-results.json",
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
    if parent.get("required_artifacts") != expected_artifacts:
        raise ValueError("父运行制品清单不符")
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


def validate_parent_semantics(
    config: dict[str, Any], parent_root: Path, artifacts: Mapping[str, Mapping[str, object]]
) -> dict[str, Any]:
    parent_config_path = Path(config["paths"]["parent_config"])
    if sha256_file(parent_config_path) != PARENT_CONFIG_SHA256:
        raise RuntimeError("父生产配置哈希与冻结值不一致")
    if artifacts["frozen_config"]["sha256"] != PARENT_CONFIG_SHA256:
        raise RuntimeError("父运行冻结配置哈希与冻结值不一致")
    parent_config = load_json(parent_config_path)
    if parent_config.get("run_id") != PARENT_RUN_ID:
        raise RuntimeError("父生产配置运行身份不符")
    result = load_json(parent_root / "source-screen-results.json")
    status = load_json(parent_root / "status.json")
    if status.get("state") != "failed" or status.get("exit_code") != 1:
        raise RuntimeError("父运行原失败状态不符，拒绝覆盖或猜测修复")
    if result.get("target_year_arrays_read") != 0:
        raise RuntimeError("父结果违反目标年零读取合同")
    source_selection = result.get("source_selection")
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
        if not isinstance(checkpoint, dict):
            raise RuntimeError(f"父运行 {unit} 缺少检查点绑定")
        artifact_key = "checkpoint_g_a" if unit == "G-A" else "checkpoint_g_b"
        if checkpoint.get("sha256") != artifacts[artifact_key]["sha256"]:
            raise RuntimeError(f"父运行 {unit} 检查点哈希不一致")
    if by_unit["G-B"].get("selected_epoch") != 9:
        raise RuntimeError("父运行 G-B 选中轮次不是冻结的第 9 轮")
    curve_receipt = load_json(parent_root / "complete-alert-budget-curves-receipt.json")
    if curve_receipt.get("sha256") != artifacts["aggregate_curves"]["sha256"]:
        raise RuntimeError("父运行聚合曲线与曲线收据哈希不一致")
    return result


def build_parent_binding(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    parent_root = Path(config["paths"]["parent_root"])
    required = config["parent_binding"]["required_artifacts"]
    artifacts = {
        key: artifact_record(parent_root / relative, parent_root)
        for key, relative in required.items()
    }
    result = validate_parent_semantics(config, parent_root, artifacts)
    binding = {
        "schema_version": "ch3-grande-swanlab-parent-binding-v1",
        "parent_run_id": PARENT_RUN_ID,
        "parent_root": str(parent_root),
        "parent_config_path": str(config["paths"]["parent_config"]),
        "parent_config_sha256": PARENT_CONFIG_SHA256,
        "artifacts": artifacts,
        "required_units": list(REQUIRED_UNITS),
        "selection_complete": True,
        "source_screen_results_bound": True,
        "aggregate_curves_bound": True,
        "selected_checkpoints_bound": True,
        "resource_receipt_bound": True,
        "parent_failed_evidence_preserved": True,
        "parent_artifacts_mutated": False,
        "new_cells_trained": [],
        "target_year_arrays_read": 0,
    }
    return binding, result


def verify_parent_unchanged(config: dict[str, Any], binding: Mapping[str, Any]) -> None:
    parent_root = Path(config["paths"]["parent_root"])
    for record in binding["artifacts"].values():
        path = parent_root / str(record["relative_path"])
        if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
            raise RuntimeError(f"父运行制品在发布期间发生漂移：{path}")


def build_metrics(result: Mapping[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    completed = result["source_selection"]["completed_structures"]
    for selection in completed:
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


def write_status(output_root: Path, state: str, stage: str, exit_code: int | None, detail: str) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-grande-swanlab-publish-repair-status-v1",
            "run_id": RUN_ID,
            "parent_run_id": PARENT_RUN_ID,
            "state": state,
            "stage": stage,
            "exit_code": exit_code,
            "detail": detail,
            "updated_at_unix": time.time(),
            "new_cells_trained": [],
            "target_year_arrays_read": 0,
            "parent_artifacts_mutated": False,
        },
    )


def log(output_root: Path, message: str) -> None:
    line = f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}] {message}"
    print(line, flush=True)
    with (output_root / "publish-repair.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def run_tracking_gate(output_root: Path) -> dict[str, Any]:
    gate_root = output_root / "tracking-gate"
    gate_root.mkdir(parents=True, exist_ok=True)
    commands = {"ping": ["uv", "run", "--no-sync", "swanlab", "ping"], "verify": ["uv", "run", "--no-sync", "swanlab", "verify"]}
    receipt: dict[str, Any] = {
        "schema_version": "ch3-grande-swanlab-publish-repair-tracking-gate-v1",
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
            atomic_json(output_root / "tracking-gate-receipt.json", receipt)
            raise RuntimeError(f"SwanLab {name} 门失败，退出码 {completed.returncode}")
    receipt["passed"] = True
    atomic_json(output_root / "tracking-gate-receipt.json", receipt)
    return receipt


def build_manifest(output_root: Path, config_path: Path, alias_path: Path) -> None:
    expected = [
        "parent-binding.json",
        "tag-receipt.json",
        "tracking-gate-receipt.json",
        "tracking-gate/swanlab-ping.log",
        "tracking-gate/swanlab-verify.log",
        "swanlab-receipt.json",
        "status.json",
        "publish-repair.log",
    ]
    files: dict[str, Any] = {}
    for relative in expected:
        path = output_root / relative
        if path.is_file():
            files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    files["repair-config"] = {"path": str(config_path), "sha256": sha256_file(config_path)}
    files["tag-aliases"] = {"path": str(alias_path), "sha256": sha256_file(alias_path)}
    atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-grande-swanlab-publish-repair-manifest-v1",
            "run_id": RUN_ID,
            "parent_run_id": PARENT_RUN_ID,
            "files": files,
            "published_existing_aggregate_metrics_only": True,
            "new_cells_trained": [],
            "training_data_read": False,
            "gpu_read": False,
            "target_year_arrays_read": 0,
            "parent_artifacts_mutated": False,
        },
    )


def publish(config: dict[str, Any], config_path: Path, alias_path: Path, args: argparse.Namespace) -> None:
    output_root = Path(config["paths"]["output_root"])
    if output_root.exists():
        status_path = output_root / "status.json"
        if status_path.is_file() and load_json(status_path).get("state") == "complete":
            print(f"发布修复已完成，不重复创建 SwanLab 运行：{output_root}")
            return
        raise RuntimeError(f"发布修复输出根已存在，拒绝覆盖：{output_root}")
    output_root.mkdir(parents=True)
    swanlab_module: object | None = None
    try:
        write_status(output_root, "running", "parent-binding", None, "开始只读绑定父运行制品")
        binding, result = build_parent_binding(config)
        atomic_json(output_root / "parent-binding.json", binding)
        log(output_root, "父运行 G-A/G-B 选择、聚合曲线、检查点、资源与配置哈希绑定通过")
        write_status(output_root, "running", "tracking-gate", None, "执行 SwanLab ping 与 verify")
        run_tracking_gate(output_root)
        aliases = load_swanlab_tag_aliases(alias_path)
        metrics = build_metrics(result)
        write_status(output_root, "running", "publish-existing-aggregate", None, "只上传父运行既有聚合指标")
        swanlab_module, run, tag_receipt = initialize_swanlab_run(
            config["swanlab"],
            aliases=aliases,
            config={
                "run_id": RUN_ID,
                "parent_run_id": PARENT_RUN_ID,
                "parent_config_sha256": PARENT_CONFIG_SHA256,
                "published_existing_aggregate_metrics_only": True,
                "new_cells_trained": [],
                "target_year_arrays_read": 0,
            },
            log_dir=output_root / "swanlog",
            tag_receipt_path=output_root / "tag-receipt.json",
            authorized_workspace=args.authorized_swanlab_workspace,
            authorized_project=args.authorized_swanlab_project,
        )
        swanlab_module.log(metrics, step=0)
        swanlab_module.finish()
        verify_parent_unchanged(config, binding)
        atomic_json(
            output_root / "swanlab-receipt.json",
            {
                "schema_version": "ch3-grande-swanlab-publish-repair-receipt-v1",
                "run_id": str(run.id),
                "workspace": config["swanlab"]["workspace"],
                "project": config["swanlab"]["project"],
                "name": config["swanlab"]["name"],
                "group": config["swanlab"]["group"],
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
        log(output_root, "GRANDE SwanLab 零重训发布修复完成")
        write_status(output_root, "complete", "published", 0, "既有聚合指标已通过独立身份发布")
        build_manifest(output_root, config_path, alias_path)
    except BaseException as exc:
        if swanlab_module is not None:
            try:
                swanlab_module.finish(state="crashed", error=str(exc))
            except BaseException:
                pass
        log(output_root, f"发布修复失败：{exc}")
        write_status(output_root, "failed", "publish-repair", 1, str(exc))
        build_manifest(output_root, config_path, alias_path)
        raise


def main() -> int:
    args = parse_args()
    if args.validate_config == args.publish:
        raise SystemExit("必须且只能选择 --validate-config 或 --publish")
    config_path = args.config.resolve()
    config = load_json(config_path)
    alias_path = resolve_alias_path(config, args.alias_config)
    validate_config(
        config,
        alias_path=alias_path,
        authorized_workspace=args.authorized_swanlab_workspace,
        authorized_project=args.authorized_swanlab_project,
    )
    if args.validate_config:
        print("GRANDE_SWANLAB_PUBLISH_REPAIR_CONFIG_VALID")
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
