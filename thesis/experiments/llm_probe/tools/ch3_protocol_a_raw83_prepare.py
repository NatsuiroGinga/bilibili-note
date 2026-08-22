#!/usr/bin/env python3
"""Protocol A Raw83 共享预处理 P0–P5 幂等阶段入口。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import io
import json
import os
import platform
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Callable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(PROJECT_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from flow_probe.protocol_a_preprocessing import (  # noqa: E402
    fit_candidate_a,
    fit_candidate_b,
    materialize_source_views,
)
from flow_probe.protocol_a_raw83 import (  # noqa: E402
    DIJK_FEATURES,
    SCHEMA_VERSION,
    SOURCE_ROW_COUNT,
    YEAR_CONFIG_SCHEMA_VERSION,
    YearProtocolADataset,
    ProtocolARaw83Error,
    atomic_write_json,
    bind_protocol_a_split,
    canonical_sha256,
    load_json,
    materialize_source_raw83,
    materialize_qualified_year_product,
    publish_dataset_manifest,
    sha256_file,
    source_data_root,
    source_generation_roots,
    validate_config,
    validate_year_config,
)

SOURCE_STAGES = ("P0", "P1", "P2", "P3", "P4", "P5")
STAGES = SOURCE_STAGES + ("P6",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从 LSPR23 原始 ZIP 物化 Protocol A Raw83 与 A/B 共享视图。"
    )
    parser.add_argument("--config", type=Path, required=True, help="冻结 JSON 配置")
    parser.add_argument(
        "--through-stage",
        choices=STAGES,
        default="P5",
        help="从 P0 连续执行到指定阶段，默认 P5",
    )
    parser.add_argument("--validate-config", action="store_true", help="只校验配置与代码合同")
    parser.add_argument(
        "--validate-product",
        action="store_true",
        help="只校验已发布清单与全部登记制品哈希",
    )
    parser.add_argument(
        "--print-resource-requirements",
        action="store_true",
        help="只输出磁盘与内存资源公式结果",
    )
    return parser.parse_args()


def _load_config(path: Path) -> dict[str, Any]:
    config = load_json(path)
    if config.get("schema_version") == YEAR_CONFIG_SCHEMA_VERSION:
        validate_year_config(config)
    else:
        validate_config(config)
    configured_path = Path(config["paths"]["config_path"])
    if configured_path.exists():
        path_matches = path.resolve(strict=True) == configured_path.resolve(strict=True)
    else:
        path_matches = path.name == configured_path.name and path.parent.name == "configs"
    if not path_matches:
        raise ProtocolARaw83Error("命令行配置与冻结 config_path 不同一")
    return config


def _localize_project_path(path: Path, configured_root: Path) -> Path:
    if path.exists():
        return path
    try:
        relative = path.relative_to(configured_root)
    except ValueError:
        return path
    return PROJECT_ROOT / relative


def _validate_vendor(config: Mapping[str, Any]) -> None:
    vendor = config["vendor"]
    configured_root = Path(config["paths"]["project_root"])
    for item in vendor["files"]:
        path = _localize_project_path(Path(item["path"]), configured_root)
        if not path.is_file() or path.is_symlink():
            raise ProtocolARaw83Error(f"官方快照缺失或为符号链接：{path}")
        if path.stat().st_size != int(item["bytes"]) or sha256_file(path) != item["sha256"]:
            raise ProtocolARaw83Error(f"官方快照哈希不匹配：{path}")
    manifest_path = _localize_project_path(Path(vendor["manifest_path"]), configured_root)
    manifest = load_json(manifest_path)
    if manifest["commit"] != vendor["commit"] or manifest["license"] != "Apache-2.0":
        raise ProtocolARaw83Error("官方快照提交或许可证不匹配")


def validate_static_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    _validate_vendor(config)
    dependencies = _dependency_receipt()
    observed_dependencies = {
        "numpy": dependencies["numpy"],
        "pyarrow": dependencies["pyarrow"],
        "sklearn": dependencies["sklearn"],
    }
    if observed_dependencies != config["dependencies"]:
        raise ProtocolARaw83Error(
            f"实际依赖版本与冻结配置不匹配：{observed_dependencies}"
        )
    vendor_manifest_path = _localize_project_path(
        Path(config["vendor"]["manifest_path"]),
        Path(config["paths"]["project_root"]),
    )
    source = config["source"]
    if source["expected_bytes"] != 1_925_103_715:
        raise ProtocolARaw83Error("LSPR23 冻结字节数不匹配")
    if source["expected_md5"] != "f3f5bf9f7cecf2186511eabb38f7accc":
        raise ProtocolARaw83Error("LSPR23 官方 MD5 不匹配")
    if source["expected_sha256"] != "4c39f29a2e99ec58f6c167863d49d944ab5e46dc78a28afe78cc57ba85cd2885":
        raise ProtocolARaw83Error("LSPR23 冻结 SHA-256 不匹配")
    preprocessing = config["preprocessing"]
    if preprocessing["candidate_a"] != {
        "imputation": "training-valid-flow-mean",
        "variance_ddof": 0,
        "constant_scale": 1.0,
        "clip": [-10.0, 10.0],
    }:
        raise ProtocolARaw83Error("候选 A 配置不等于冻结合同")
    candidate_b = preprocessing["candidate_b"]
    required_b = {
        "quantile_indices": list(range(3, 79)),
        "special_indices_copied_from_a": [0, 1, 2, 79, 80, 81, 82],
        "imputation": "training-valid-flow-mean",
        "noise": 0.001,
        "random_state": 42,
        "random_stream": "single-default_rng-42-standard_normal-C-row-major-float64-out-v1",
        "output_distribution": "normal",
        "subsample": 1_000_000_000,
        "n_quantiles_formula": "max(min(n_train//30,1000),10)",
        "expected_n_quantiles": 1_000,
    }
    if candidate_b != required_b:
        raise ProtocolARaw83Error("候选 B 配置不等于官方参数任务适配合同")
    return {
        "schema_version": f"{SCHEMA_VERSION}-static-validation-v1",
        "config_sha256": canonical_sha256(config),
        "vendor_manifest_sha256": sha256_file(vendor_manifest_path),
        "default_stages": list(SOURCE_STAGES),
        "dependencies": observed_dependencies,
    }


def validate_year_static_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    validate_year_config(config)
    dependencies = _dependency_receipt()
    observed = {key: dependencies[key] for key in ("numpy", "pyarrow", "sklearn")}
    if observed != config["dependencies"]:
        raise ProtocolARaw83Error(f"年度产品依赖版本不匹配：{observed}")
    return {
        "schema_version": f"{YEAR_CONFIG_SCHEMA_VERSION}-static-validation-v1",
        "config_sha256": canonical_sha256(config),
        "qualification_status": config["qualification_status"],
        "winning_arm": config["winning_arm"],
        "dependencies": observed,
        "runtime_admitted": config["qualification_status"] == "qualified-source-arm-sealed",
    }


def _read_cgroup_limit() -> tuple[int | None, int]:
    maximum_path = Path("/sys/fs/cgroup/memory.max")
    current_path = Path("/sys/fs/cgroup/memory.current")
    maximum: int | None = None
    current = 0
    if maximum_path.is_file():
        text = maximum_path.read_text(encoding="utf-8").strip()
        if text != "max":
            maximum = int(text)
    if current_path.is_file():
        current = int(current_path.read_text(encoding="utf-8").strip())
    if maximum is None:
        try:
            maximum = int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
        except (ValueError, OSError):
            maximum = None
    return maximum, current


def runtime_resource_plan(config: Mapping[str, Any]) -> dict[str, Any]:
    resources = config["resources"]
    maximum, current = _read_cgroup_limit()
    if maximum is None:
        raise ProtocolARaw83Error("无法获得 cgroup 或物理内存上界")
    available = max(0, maximum - current)
    per_row_working_set = len(config["protocol_a"]["feature_names"]) * (8 + 4 + 8 + 4 + 1)
    safety_divisor = int(resources["batch_memory_safety_divisor"])
    minimum_required_memory = (
        per_row_working_set * int(resources["minimum_batch_rows"]) * safety_divisor
    )
    if available < minimum_required_memory:
        raise ProtocolARaw83Error(
            f"cgroup 可用内存不足：{available} < {minimum_required_memory}"
        )
    batch_rows = available // max(1, per_row_working_set * safety_divisor)
    batch_rows = max(
        int(resources["minimum_batch_rows"]),
        min(int(resources["maximum_batch_rows"]), int(batch_rows)),
    )
    arrow_block_size = available // int(resources["arrow_block_memory_divisor"])
    arrow_block_size = max(
        int(resources["minimum_arrow_block_bytes"]),
        min(int(resources["maximum_arrow_block_bytes"]), int(arrow_block_size)),
    )
    feature_bytes = SOURCE_ROW_COUNT * len(config["protocol_a"]["feature_names"]) * 4
    sidecar_bytes = SOURCE_ROW_COUNT * (4 + 8)
    _, partial_generation, final_generation = source_generation_roots(config)
    output_root = final_generation if final_generation.exists() else partial_generation
    final_specs = (
        (output_root / "raw" / "lspr23-raw83.npy", feature_bytes),
        (output_root / "sidecars" / "lspr23-flow-entity-id.npy", SOURCE_ROW_COUNT * 4),
        (output_root / "sidecars" / "lspr23-start-time-ns.npy", SOURCE_ROW_COUNT * 8),
        (output_root / "views" / "lspr23-candidate-a-standard.npy", feature_bytes),
        (output_root / "views" / "lspr23-candidate-b-quantile.npy", feature_bytes),
    )
    final_bytes = 0
    for final_path, expected_bytes in final_specs:
        partial_path = final_path.with_name(f"{final_path.name}.partial.{config['run_id']}")
        if not final_path.exists() and not partial_path.exists():
            final_bytes += expected_bytes
    noise_bytes = SOURCE_ROW_COUNT * 76 * 8
    noisy_bytes = SOURCE_ROW_COUNT * 76 * 4
    temporary_root = Path(config["paths"]["output_root"]) / "temporary" / "candidate-b"
    noise_path = temporary_root / f"official-row-major-noise.f8.partial.{config['run_id']}.npy"
    noisy_path = temporary_root / f"filled-noisy-training.f4.partial.{config['run_id']}.npy"
    quantile_temporary_bytes = (0 if noise_path.exists() else noise_bytes) + (
        0 if noisy_path.exists() else noisy_bytes
    )
    largest_atomic_bytes = feature_bytes
    low_water_bytes = int(resources["minimum_free_disk_gib"]) * 1024**3
    required_free_bytes = final_bytes + quantile_temporary_bytes + largest_atomic_bytes + low_water_bytes
    return {
        "schema_version": f"{SCHEMA_VERSION}-runtime-resource-plan-v1",
        "cgroup_limit_bytes": maximum,
        "cgroup_current_bytes": current,
        "cgroup_available_bytes": available,
        "minimum_required_memory_bytes": minimum_required_memory,
        "per_row_working_set_upper_bound_bytes": per_row_working_set,
        "batch_memory_safety_divisor": safety_divisor,
        "batch_rows": batch_rows,
        "arrow_block_size": arrow_block_size,
        "missing_final_artifact_upper_bound_bytes": final_bytes,
        "maximum_quantile_temporary_bytes": quantile_temporary_bytes,
        "largest_atomic_publish_bytes": largest_atomic_bytes,
        "disk_low_water_bytes": low_water_bytes,
        "required_free_bytes": required_free_bytes,
    }


def _stage_identity(
    config: Mapping[str, Any],
    stage: str,
    upstream_receipts: list[Path],
) -> dict[str, Any]:
    code_paths = [
        Path(__file__),
        PROJECT_ROOT / "src" / "flow_probe" / "protocol_a_raw83.py",
        PROJECT_ROOT / "src" / "flow_probe" / "protocol_a_preprocessing.py",
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}-stage-identity-v1",
        "stage": stage,
        "logical_config_sha256": canonical_sha256(_logical_config_identity(config)),
        "code_sha256": {str(path.relative_to(PROJECT_ROOT)): sha256_file(path) for path in code_paths},
        "upstream_receipt_sha256": {
            str(path.relative_to(Path(config["paths"]["output_root"]))): sha256_file(path)
            for path in upstream_receipts
        },
    }


def _logical_config_identity(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": config["schema_version"],
        "run_id": config["run_id"],
        "dependencies": config["dependencies"],
        "source": {
            key: config["source"][key]
            for key in (
                "year",
                "expected_bytes",
                "expected_md5",
                "expected_sha256",
                "expected_rows",
                "inner_csv",
                "inner_csv_uncompressed_bytes",
            )
        },
        "protocol_a": config["protocol_a"],
        "preprocessing": config["preprocessing"],
        "resources": config["resources"],
        "vendor": {
            "commit": config["vendor"]["commit"],
            "files": [
                {key: item[key] for key in ("bytes", "sha256")}
                for item in config["vendor"]["files"]
            ],
        },
        "path_roles": sorted(config["paths"]),
    }


def _run_stage(
    config: Mapping[str, Any],
    stage: str,
    upstream_receipts: list[Path],
    action: Callable[[], Mapping[str, Any]],
) -> Mapping[str, Any]:
    output_root = Path(config["paths"]["output_root"])
    state_path = output_root / "states" / "pipeline" / f"{stage.lower()}.json"
    identity = _stage_identity(config, stage, upstream_receipts)
    identity_sha = canonical_sha256(identity)
    if state_path.exists():
        previous = load_json(state_path)
        if (
            stage != "P0"
            and previous.get("state") == "sealed"
            and previous.get("identity_sha256") == identity_sha
        ):
            receipt_path = Path(previous["receipt_path"])
            if receipt_path.is_file() and sha256_file(receipt_path) == previous["receipt_sha256"]:
                print(f"{stage} 已封印，同身份跳过。", flush=True)
                return load_json(receipt_path)
        if previous.get("identity_sha256") != identity_sha:
            raise ProtocolARaw83Error(f"{stage} 存在不同身份状态，拒绝拼接")
    atomic_write_json(
        state_path,
        {
            "schema_version": f"{SCHEMA_VERSION}-stage-state-v1",
            "stage": stage,
            "state": "running",
            "identity": identity,
            "identity_sha256": identity_sha,
            "started_at_unix": time.time(),
            "exit_code": None,
        },
    )
    print(f"{stage} 开始执行。", flush=True)
    try:
        receipt = dict(action())
        receipt_path = output_root / "receipts" / f"{stage.lower()}-stage-result.json"
        atomic_write_json(receipt_path, receipt)
        atomic_write_json(
            state_path,
            {
                "schema_version": f"{SCHEMA_VERSION}-stage-state-v1",
                "stage": stage,
                "state": "sealed",
                "identity": identity,
                "identity_sha256": identity_sha,
                "receipt_path": str(receipt_path.resolve(strict=True)),
                "receipt_sha256": sha256_file(receipt_path),
                "finished_at_unix": time.time(),
                "exit_code": 0,
            },
        )
        print(f"{stage} 已封印。", flush=True)
        return receipt
    except BaseException as error:
        atomic_write_json(
            state_path,
            {
                "schema_version": f"{SCHEMA_VERSION}-stage-state-v1",
                "stage": stage,
                "state": "failed",
                "identity": identity,
                "identity_sha256": identity_sha,
                "failed_at_unix": time.time(),
                "error_type": type(error).__name__,
                "error": str(error),
                "exit_code": 1,
            },
        )
        raise


def _p0(config: Mapping[str, Any]) -> dict[str, Any]:
    source_path = Path(config["source"]["zip_path"])
    if not source_path.is_file() or source_path.is_symlink():
        raise ProtocolARaw83Error(f"LSPR23 源 ZIP 缺失或为符号链接：{source_path}")
    if source_path.stat().st_size != int(config["source"]["expected_bytes"]):
        raise ProtocolARaw83Error("LSPR23 ZIP 字节数不匹配")
    md5_digest = hashlib.md5(usedforsecurity=False)
    sha256_digest = hashlib.sha256()
    with source_path.open("rb") as source_stream:
        while block := source_stream.read(8 * 1024 * 1024):
            md5_digest.update(block)
            sha256_digest.update(block)
    observed_md5 = md5_digest.hexdigest()
    observed_sha256 = sha256_digest.hexdigest()
    if observed_md5 != config["source"]["expected_md5"]:
        raise ProtocolARaw83Error("LSPR23 ZIP MD5 不匹配")
    if observed_sha256 != config["source"]["expected_sha256"]:
        raise ProtocolARaw83Error("LSPR23 ZIP SHA-256 不匹配")
    with zipfile.ZipFile(source_path) as archive:
        csv_members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if csv_members != [config["source"]["inner_csv"]]:
            raise ProtocolARaw83Error(f"LSPR23 ZIP 内部 CSV 不匹配：{csv_members}")
        member = archive.getinfo(csv_members[0])
        if member.file_size != int(config["source"]["inner_csv_uncompressed_bytes"]):
            raise ProtocolARaw83Error("LSPR23 CSV 解压字节数不匹配")
        with archive.open(member, "r") as binary_stream:
            with io.TextIOWrapper(binary_stream, encoding="utf-8", newline="") as text_stream:
                header = next(csv.reader(text_stream))
        required_columns = set(DIJK_FEATURES) | {
            "SrcIP",
            "DstIP",
            "mTimestampStart",
            "Label",
        }
        if len(header) != len(set(header)) or not required_columns.issubset(header):
            missing = sorted(required_columns - set(header))
            raise ProtocolARaw83Error(f"LSPR23 CSV 表头缺失或重复：{missing}")
    return {
        "schema_version": f"{SCHEMA_VERSION}-p0-source-preflight-v1",
        "source_path": str(source_path.resolve(strict=True)),
        "source_bytes": source_path.stat().st_size,
        "source_md5": observed_md5,
        "source_sha256": observed_sha256,
        "inner_csv": member.filename,
        "inner_csv_uncompressed_bytes": member.file_size,
        "header_column_count": len(header),
        "header_sha256": canonical_sha256(header),
    }


def _dependency_receipt() -> dict[str, Any]:
    result: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    for module_name in ("numpy", "pyarrow", "sklearn"):
        module = importlib.import_module(module_name)
        result[module_name] = module.__version__
    return result


def validate_published_product(config: Mapping[str, Any]) -> dict[str, Any]:
    manifest_path = Path(config["paths"]["dataset_manifest"])
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ProtocolARaw83Error("已发布清单缺失或为符号链接")
    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ProtocolARaw83Error("已发布清单模式不匹配")
    content_hash = manifest.get("manifest_content_sha256")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_content_sha256"}
    if content_hash != canonical_sha256(unsigned):
        raise ProtocolARaw83Error("已发布清单内容哈希不匹配")
    output_root = Path(config["paths"]["output_root"]).resolve(strict=True)
    verified: dict[str, str] = {}
    generation_root = manifest_path.parent.resolve(strict=True)
    expected_files = {"dataset-manifest.json"}
    for key, item in manifest["artifacts"].items():
        path = Path(item["path"])
        resolved = path.resolve(strict=True)
        if path.is_symlink() or not resolved.is_relative_to(output_root):
            raise ProtocolARaw83Error(f"已发布制品越界：{key}")
        if resolved.stat().st_size != int(item["bytes"]):
            raise ProtocolARaw83Error(f"已发布制品字节数不匹配：{key}")
        observed = sha256_file(resolved)
        if observed != item["sha256"]:
            raise ProtocolARaw83Error(f"已发布制品 SHA-256 不匹配：{key}")
        verified[key] = observed
        expected_files.add(str(resolved.relative_to(generation_root)))
    observed_files = {
        str(path.resolve(strict=True).relative_to(generation_root))
        for path in generation_root.rglob("*")
        if path.is_file()
    }
    if observed_files != expected_files:
        raise ProtocolARaw83Error("已发布世代不等于清单严格制品集")
    return {
        "schema_version": f"{SCHEMA_VERSION}-published-product-validation-v1",
        "manifest_file_sha256": sha256_file(manifest_path),
        "manifest_content_sha256": content_hash,
        "verified_artifact_sha256": verified,
    }


def run(config: Mapping[str, Any], through_stage: str) -> None:
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    _, _, final_generation = source_generation_roots(config)
    if final_generation.exists():
        validate_published_product(config)
        temporary_root = output_root / "temporary" / "candidate-b"
        for name in (
            f"official-row-major-noise.f8.partial.{config['run_id']}.npy",
            f"filled-noisy-training.f4.partial.{config['run_id']}.npy",
            f"quantiles.f8.partial.{config['run_id']}.npy",
            f"references.f8.partial.{config['run_id']}.npy",
        ):
            cleanup_path = temporary_root / name
            if cleanup_path.exists():
                cleanup_path.unlink()
        if temporary_root.exists() and not any(temporary_root.iterdir()):
            temporary_root.rmdir()
        atomic_write_json(
            output_root / "status.json",
            {
                "schema_version": f"{SCHEMA_VERSION}-status-v1",
                "run_id": config["run_id"],
                "state": "finished",
                "sealed_through_stage": "P5",
                "updated_at_unix": time.time(),
            },
        )
        return
    resource_plan = runtime_resource_plan(config)
    disk = shutil.disk_usage(output_root)
    used_percent = 100.0 * disk.used / disk.total
    if disk.free < int(resource_plan["required_free_bytes"]):
        raise ProtocolARaw83Error(
            f"可用磁盘不足：{disk.free} < {resource_plan['required_free_bytes']}"
        )
    if used_percent >= float(config["resources"]["maximum_disk_used_percent"]):
        raise ProtocolARaw83Error(
            f"磁盘使用率超过门限：{used_percent:.3f}%"
        )
    resource_plan["disk_free_bytes"] = disk.free
    resource_plan["disk_used_percent"] = used_percent
    atomic_write_json(output_root / "receipts" / "runtime-resource-plan.json", resource_plan)
    if through_stage not in SOURCE_STAGES:
        raise ProtocolARaw83Error("源年入口只允许 P0-P5")
    stages_to_run = SOURCE_STAGES[: SOURCE_STAGES.index(through_stage) + 1]
    receipts: dict[str, Mapping[str, Any]] = {}
    p0_stage_path = output_root / "receipts" / "p0-stage-result.json"
    if "P0" in stages_to_run:
        receipts["P0"] = _run_stage(config, "P0", [], lambda: _p0(config))
    if "P1" in stages_to_run:
        def p1_action() -> Mapping[str, Any]:
            receipt = materialize_source_raw83(
                config,
                block_size=int(resource_plan["arrow_block_size"]),
            )
            p0 = receipts.get("P0") or load_json(p0_stage_path)
            receipt["source_sha256"] = p0["source_sha256"]
            receipt["source_md5"] = p0["source_md5"]
            atomic_write_json(output_root / "receipts" / "p1-source-raw83.json", receipt)
            return receipt

        receipts["P1"] = _run_stage(config, "P1", [p0_stage_path], p1_action)
    p1_stage_path = output_root / "receipts" / "p1-stage-result.json"
    if "P2" in stages_to_run:
        receipts["P2"] = _run_stage(
            config,
            "P2",
            [p1_stage_path],
            lambda: bind_protocol_a_split(config),
        )
    p2_stage_path = output_root / "receipts" / "p2-stage-result.json"
    if "P3" in stages_to_run:
        receipts["P3"] = _run_stage(
            config,
            "P3",
            [p2_stage_path],
            lambda: fit_candidate_a(config, batch_rows=int(resource_plan["batch_rows"])),
        )
    p3_stage_path = output_root / "receipts" / "p3-stage-result.json"
    if "P4" in stages_to_run:
        receipts["P4"] = _run_stage(
            config,
            "P4",
            [p3_stage_path],
            lambda: fit_candidate_b(config, batch_rows=int(resource_plan["batch_rows"])),
        )
    p4_stage_path = output_root / "receipts" / "p4-stage-result.json"
    if "P5" in stages_to_run:
        def p5_action() -> Mapping[str, Any]:
            run_root, partial_root, final_root = source_generation_roots(config)
            if final_root.exists():
                validation = validate_published_product(config)
                temporary_root = run_root / "temporary" / "candidate-b"
                for name in (
                    f"official-row-major-noise.f8.partial.{config['run_id']}.npy",
                    f"filled-noisy-training.f4.partial.{config['run_id']}.npy",
                    f"quantiles.f8.partial.{config['run_id']}.npy",
                    f"references.f8.partial.{config['run_id']}.npy",
                ):
                    cleanup_path = temporary_root / name
                    if cleanup_path.exists():
                        cleanup_path.unlink()
                if temporary_root.exists() and not any(temporary_root.iterdir()):
                    temporary_root.rmdir()
                return {
                    "schema_version": f"{SCHEMA_VERSION}-p5-existing-generation-v1",
                    "dataset_manifest_path": str(Path(config["paths"]["dataset_manifest"])),
                    "dataset_manifest_sha256": validation["manifest_file_sha256"],
                    "generation_reused": True,
                }
            views = materialize_source_views(
                config,
                batch_rows=int(resource_plan["batch_rows"]),
            )
            p1 = receipts.get("P1") or load_json(p1_stage_path)
            p2 = receipts.get("P2") or load_json(p2_stage_path)
            manifest = publish_dataset_manifest(
                config,
                p1_receipt=p1,
                p2_receipt=p2,
                preprocessing_receipt=views,
                runtime={**resource_plan, "dependencies": _dependency_receipt()},
            )
            temporary_root = run_root / "temporary" / "candidate-b"
            cleanup_paths = [
                temporary_root / f"official-row-major-noise.f8.partial.{config['run_id']}.npy",
                temporary_root / f"filled-noisy-training.f4.partial.{config['run_id']}.npy",
                temporary_root / f"quantiles.f8.partial.{config['run_id']}.npy",
                temporary_root / f"references.f8.partial.{config['run_id']}.npy",
            ]
            if final_root.exists() or not partial_root.is_dir():
                raise ProtocolARaw83Error("源世代原子发布前目录状态非法")
            os.replace(partial_root, final_root)
            final_manifest = final_root / "dataset-manifest.json"
            pointer = {
                "schema_version": f"{SCHEMA_VERSION}-current-source-pointer-v1",
                "generation": "source-v1",
                "manifest_path": str(final_manifest.resolve(strict=True)),
                "manifest_sha256": sha256_file(final_manifest),
            }
            pointer["pointer_content_sha256"] = canonical_sha256(pointer)
            atomic_write_json(run_root / "current-source.json", pointer)
            for cleanup_path in cleanup_paths:
                if cleanup_path.exists():
                    cleanup_path.unlink()
            if temporary_root.exists() and not any(temporary_root.iterdir()):
                temporary_root.rmdir()
            published_views = dict(views)
            published_views["artifacts"] = {
                key: {
                    **item,
                    "path": str(
                        final_root
                        / Path(item["path"]).resolve(strict=False).relative_to(partial_root)
                    ),
                }
                for key, item in views["artifacts"].items()
            }
            return {
                **published_views,
                "dataset_manifest_path": str(final_manifest.resolve(strict=True)),
                "dataset_manifest_sha256": sha256_file(final_manifest),
                "manifest_content_sha256": manifest["manifest_content_sha256"],
                "generation_reused": False,
                "temporary_files_removed": [str(path) for path in cleanup_paths],
            }

        receipts["P5"] = _run_stage(
            config,
            "P5",
            [p1_stage_path, p2_stage_path, p3_stage_path, p4_stage_path],
            p5_action,
        )
    atomic_write_json(
        output_root / "status.json",
        {
            "schema_version": f"{SCHEMA_VERSION}-status-v1",
            "run_id": config["run_id"],
            "state": "finished",
            "sealed_through_stage": through_stage,
            "updated_at_unix": time.time(),
        },
    )


def main() -> int:
    args = parse_args()
    config = _load_config(args.config)
    is_year_product = config["schema_version"] == YEAR_CONFIG_SCHEMA_VERSION
    static_receipt = (
        validate_year_static_contract(config)
        if is_year_product
        else validate_static_contract(config)
    )
    if args.validate_config:
        print(json.dumps(static_receipt, ensure_ascii=False, sort_keys=True))
        return 0
    if is_year_product:
        if args.print_resource_requirements:
            row_count = int(config["year_product"]["expected_rows"])
            payload_bytes = row_count * (len(DIJK_FEATURES) * 8 + 12)
            required = payload_bytes + row_count * len(DIJK_FEATURES) * 4 + int(
                config["resources"]["minimum_free_disk_gib"]
            ) * 1024**3
            print(
                json.dumps(
                    {
                        "schema_version": f"{YEAR_CONFIG_SCHEMA_VERSION}-resource-plan-v1",
                        "required_free_bytes": required,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        if args.validate_product:
            dataset = YearProtocolADataset(
                Path(config["paths"]["dataset_manifest"]),
                Path(config["source_product"]["qualification_seal"]),
            )
            print(
                json.dumps(
                    {
                        "schema_version": f"{YEAR_CONFIG_SCHEMA_VERSION}-product-validation-v1",
                        "manifest_sha256": sha256_file(dataset.manifest_path),
                        "artifact_count": len(dataset.artifact_paths),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        if config["qualification_status"] != "qualified-source-arm-sealed":
            raise ProtocolARaw83Error("源输入臂尚未封印，P6 在打开任何数据前硬失败")
        run_root = Path(config["paths"]["output_root"])
        run_root.mkdir(parents=True, exist_ok=True)
        year_manifest = Path(config["paths"]["dataset_manifest"])
        if year_manifest.is_file():
            dataset = YearProtocolADataset(
                year_manifest,
                Path(config["source_product"]["qualification_seal"]),
            )
            atomic_write_json(
                run_root / "status.json",
                {
                    "schema_version": f"{YEAR_CONFIG_SCHEMA_VERSION}-status-v1",
                    "state": "finished",
                    "sealed_through_stage": "P6",
                    "exit_code": 0,
                    "manifest_sha256": sha256_file(dataset.manifest_path),
                },
            )
            return 0
        maximum, current = _read_cgroup_limit()
        if maximum is None:
            raise ProtocolARaw83Error("无法获得 P6 cgroup 内存上界")
        available = maximum - current
        per_row = len(DIJK_FEATURES) * (8 + 4 + 8 + 4 + 1)
        divisor = int(config["resources"]["batch_memory_safety_divisor"])
        computed_batch_rows = available // (per_row * divisor)
        if computed_batch_rows < int(config["resources"]["minimum_batch_rows"]):
            raise ProtocolARaw83Error("P6 cgroup 可用内存不足")
        batch_rows = min(
            int(config["resources"]["maximum_batch_rows"]), computed_batch_rows
        )
        row_count = int(config["year_product"]["expected_rows"])
        required_free = (
            row_count * (len(DIJK_FEATURES) * 8 + 12)
            + row_count * len(DIJK_FEATURES) * 4
            + int(config["resources"]["minimum_free_disk_gib"]) * 1024**3
        )
        disk = shutil.disk_usage(run_root)
        used_percent = 100.0 * disk.used / disk.total
        if disk.free < required_free or used_percent >= float(
            config["resources"]["maximum_disk_used_percent"]
        ):
            raise ProtocolARaw83Error("P6 磁盘资源门失败")
        receipt = materialize_qualified_year_product(
            config,
            batch_rows=int(batch_rows),
        )
        atomic_write_json(run_root / "receipts" / "p6-stage-result.json", receipt)
        atomic_write_json(
            run_root / "status.json",
            {
                "schema_version": f"{YEAR_CONFIG_SCHEMA_VERSION}-status-v1",
                "state": "finished",
                "sealed_through_stage": "P6",
                "exit_code": 0,
            },
        )
        return 0
    if args.validate_product:
        print(json.dumps(validate_published_product(config), ensure_ascii=False, sort_keys=True))
        return 0
    resource_plan = runtime_resource_plan(config)
    if args.print_resource_requirements:
        print(json.dumps(resource_plan, ensure_ascii=False, sort_keys=True))
        return 0
    run(config, args.through_stage)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProtocolARaw83Error as error:
        print(f"协议 A Raw83 合同失败：{error}", file=sys.stderr, flush=True)
        raise SystemExit(78) from error
