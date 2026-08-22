"""独立 CUDA-RWKV Raw83 资格单入口。"""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

os.environ["OMP_NUM_THREADS"] = "1"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

SCHEMA_VERSION = "ch3-cuda-rwkv-raw83-qualification-v1"
RUN_ID = "ch3-cuda-rwkv-raw83-qualification-seed42-v1"
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / f"{RUN_ID}.json"
SOURCE_CELLS = ("C00", "C01", "C10", "C11")
EXPECTED_PARAMETER_COUNTS = {
    "small": {"R1": 104_274, "R2": 104_274},
    "large": {"R1": 8_977_842, "R2": 9_490_178},
}
SEMANTIC_GROUP_INDICES = (
    (0, 1, 2, 79, 80, 81, 82),
    tuple(range(3, 10)),
    tuple(range(10, 18)),
    tuple(range(18, 22)),
    tuple(range(22, 32)),
    tuple(range(32, 40)),
    (*range(40, 45), *range(53, 57)),
    tuple(range(45, 53)),
    tuple(range(57, 63)),
    tuple(range(63, 67)),
    tuple(range(67, 71)),
    tuple(range(71, 79)),
)


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON 顶层必须为对象：{path}")
    return value


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _static_backend_contract() -> dict[str, Any]:
    vendor_root = PROJECT_ROOT / "vendor" / "cuda_rwkv_official"
    manifest_path = vendor_root / "manifest.json"
    manifest = load_json(manifest_path)
    if manifest.get("upstream_commit") != "952102498e9ed367ea0a59ee64106916d474d30f":
        raise RuntimeError("CUDA-RWKV 官方提交身份不符")
    if manifest.get("license") != "Apache-2.0":
        raise RuntimeError("CUDA-RWKV 官方许可证身份不符")
    for item in [
        {"path": manifest["license_file"], "sha256": manifest["license_sha256"]},
        *manifest["upstream_files"],
        *manifest["derived_files"],
    ]:
        path = vendor_root / item["path"]
        if not path.is_file() or path.is_symlink() or sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"CUDA-RWKV 供应商文件身份不符：{item['path']}")
    return {
        "upstream_commit": manifest["upstream_commit"],
        "license": manifest["license"],
        "vendor_manifest_sha256": sha256_file(manifest_path),
    }


def _static_semantic_group_contract() -> dict[str, Any]:
    flattened = [index for group in SEMANTIC_GROUP_INDICES for index in group]
    if len(SEMANTIC_GROUP_INDICES) != 12 or sorted(flattened) != list(range(83)):
        raise RuntimeError("R1 语义组必须不重不漏覆盖 0..82")
    groups = [
        {"name": f"G{index:02d}", "indices": list(group)}
        for index, group in enumerate(SEMANTIC_GROUP_INDICES)
    ]
    return {"groups": groups, "groups_sha256": canonical_sha256(groups)}


def _static_parameter_counts(config: Mapping[str, Any]) -> dict[str, int]:
    capacities = config["model"]["capacities"]
    measured: dict[str, int] = {}
    for capacity, values in capacities.items():
        channels = int(values["channels"])
        head_size = int(values["head_size"])
        low_rank = int(values["low_rank"])
        layers = int(values["layers"])
        if channels % head_size != 0 or int(values["sequence_length"]) != 128:
            raise RuntimeError(f"{capacity} 容量通道、头或序列实参非法")
        if layers == 1:
            common = 6 * channels * channels + 6 * channels * low_rank + 15 * channels + 2
        elif layers == 3:
            common = 14 * channels * channels + 22 * channels * low_rank + 49 * channels + 2
        else:
            raise RuntimeError("CUDA-RWKV 容量层数未预注册")
        for adapter in ("R1", "R2"):
            if adapter == "R1":
                adapter_parameters = 97 * 15 + 12 * 15 * channels + 3 * channels + 1
            else:
                adapter_parameters = channels * channels + 84 * channels
            parameter_count = common + adapter_parameters
            if int(values[f"{adapter}_parameters"]) != parameter_count:
                raise RuntimeError(f"{capacity}/{adapter} 配置参数量与公式不符")
            measured[f"{capacity}/{adapter}"] = parameter_count
    return measured


def _project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        remote_root = Path("/root/autodl-tmp/thesis/experiments/llm_probe")
        if path.is_relative_to(remote_root):
            return PROJECT_ROOT / path.relative_to(remote_root)
        return path
    return PROJECT_ROOT / path


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """静态验证不读取数据、CUDA 设备或 SwanLab。"""

    _require(config.get("schema_version") == SCHEMA_VERSION, "配置模式不符")
    _require(config.get("run_id") == RUN_ID, "配置运行身份不符")
    _require(config.get("seed") == 42, "资格种子必须为 42")
    data = config["data"]
    _require(data["source_year"] == "LSPR23", "源年必须为 LSPR23")
    _require(data["target_year"] == "LSPR24", "目标年必须为 LSPR24")
    _require(data["field_count"] == 83, "Raw83 字段数必须为 83")
    _require(data["sequence_length"] == 128, "序列长度必须为 128")
    _require(data["views"] == ["A", "B"], "共享视图必须严格为 A/B")
    _require(data["prohibit_direct_label_files"] is True, "必须禁止直接标签文件")
    _require(
        all(data[key] == 0 for key in ("persisted_score_rows", "persisted_label_rows", "persisted_member_rows")),
        "不得持久化分数、标签或成员行",
    )
    training = config["training"]
    expected_training = {
        "seed": 42,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "effective_batch_sequences": 64,
        "microbatch_sequences": 4,
        "accumulation_steps": 16,
        "checkpoint_interval_optimizer_steps": 20,
        "wall_clock_limit_seconds": None,
    }
    for key, expected in expected_training.items():
        _require(training.get(key) == expected, f"训练合同不符：{key}")
    _require(training["normalization_unit"] == "effective_valid_flow", "必须按有效流归一")
    _require(config["precision"]["profile_id"] == "cuda-bf16-amp-fp32-sensitive-v1", "精度配置不符")
    _require(config["precision"]["grad_scaler"] is None, "BF16 不得创建缩放器")
    cells = config["cells"]
    expected_cells = {
        "C00": (False, False),
        "C01": (False, True),
        "C10": (True, False),
        "C11": (True, True),
    }
    _require(set(cells) == set(expected_cells), "四格必须严格为 C00/C01/C10/C11")
    for cell, flags in expected_cells.items():
        observed = (
            cells[cell]["causal_prefix_module"],
            cells[cell]["learned_entity_pooling_module"],
        )
        _require(observed == flags, f"{cell} 模块位不符")
    selection = config["selection"]
    _require(selection["metric"] == "LSPR23_validation_flow_average_precision", "选择指标必须只是源年验证逐流 AP")
    _require(selection["maximum_new_selection_training_units"] == 4, "选择新训练单元上界必须为 4")
    _require(selection["cartesian_expansion_forbidden"] is True, "必须禁止笛卡尔展开")
    _require(selection["stages"]["S1"]["units"] == ["A-R2-small-C00", "B-R2-small-C00"], "S1 必须只选 A/B")
    _require(selection["stages"]["S2"]["reuse_winning_R2_small_C00"] is True, "S2 必须复用同身份 R2")
    _require(selection["stages"]["S3"]["reuse_winning_small_C00"] is True, "S3 必须复用同身份 small")
    _require(config["source_qualification"]["required_cells"] == list(SOURCE_CELLS), "源年必须封印全部四格")
    _require(config["source_qualification"]["new_cells_from_seed"] == ["C01", "C10", "C11"], "三个机制格必须独立初始化")
    for key in (
        "target_schema_reads_before_seal",
        "target_feature_rows_read_before_seal",
        "target_label_rows_read_before_seal",
    ):
        _require(config["source_qualification"][key] == 0, f"源年封印前目标读取必须为零：{key}")
    resources = config["resources"]
    _require(resources["minimum_free_gpu_memory_gib"] == 20, "GPU 显存启动门必须为 20 GiB")
    _require(resources["minimum_available_cgroup_memory_gib"] == 40, "cgroup 主存启动门必须为 40 GiB")
    _require(resources["minimum_free_disk_gib"] == 25, "磁盘启动门必须为 25 GiB")
    _require(resources["wall_clock_limit_seconds"] is None, "资源合同不得设墙钟上限")
    tracking = config["tracking"]
    _require(tracking["single_final_online_aggregate_run"] is True, "必须使用一个最终在线聚合运行")
    _require(tracking["maximum_attempts"] == 2 and tracking["retry_exit_code"] == 91, "SwanLab 尝试合同不符")
    _require(tracking["retry_only_first_zero_step_401"] is True, "只有首次零步 401 可重试")
    _require(tracking["lifecycle_reference_commits"] == ["89ddecf", "d6313ca", "70a8a2b"], "SwanLab 生命周期来源不符")
    semantic = _static_semantic_group_contract()
    _require(len(semantic["groups"]) == 12, "R1 必须含 12 语义组")
    backend = _static_backend_contract()
    _require(backend["upstream_commit"] == config["cuda"]["upstream_commit"], "CUDA 官方提交不符")
    _require(backend["license"] == "Apache-2.0", "CUDA 许可证不符")
    reference = config["cuda"]["small_kernel_qualification_input"]
    _require(reference == {"reference_commit": "703c3d3", "role": "implementation_qualification_only", "effect_evidence": False}, "small 自身门参考身份不符")
    precision_path = _project_path(config["precision"]["contract_path"])
    aliases_path = _project_path(tracking["alias_config_path"])
    _require(precision_path.is_file(), "统一精度合同缺失")
    _require(sha256_file(precision_path) == config["precision"]["contract_sha256"], "统一精度合同 SHA-256 不符")
    precision_contract = load_json(precision_path)
    profile_id = config["precision"]["profile_id"]
    profile = precision_contract.get("profiles", {}).get(profile_id)
    _require(precision_contract.get("default_profile") == profile_id, "统一默认精度配置不符")
    _require(
        isinstance(profile, dict)
        and profile.get("device_type") == "cuda"
        and profile.get("compute_dtype") == "bfloat16"
        and profile.get("autocast") is True
        and profile.get("grad_scaler") is False
        and profile.get("parameter_dtype") == "float32"
        and profile.get("optimizer_state_dtype") == "float32",
        "统一 BF16/FP32 精度区合同不符",
    )
    _require(aliases_path.is_file(), "SwanLab 别名合同缺失")
    _require(sha256_file(aliases_path) == tracking["alias_config_sha256"], "SwanLab 别名合同 SHA-256 不符")
    aliases_document = load_json(aliases_path)
    aliases = aliases_document.get("aliases")
    _require(isinstance(aliases, dict), "SwanLab 别名合同格式不符")
    _require(
        all(
            isinstance(tracking.get(key), str) and bool(tracking[key])
            for key in ("workspace", "project", "name", "group", "mode")
        ),
        "SwanLab 目的地文本字段不完整",
    )
    _require(tracking["mode"] in {"cloud", "online"}, "SwanLab 必须使用在线模式")
    tags = tracking.get("tags")
    _require(isinstance(tags, list) and 0 < len(tags) <= 20, "SwanLab 标签列表非法")
    effective_tags = [aliases.get(tag, tag) for tag in tags]
    _require(
        len(effective_tags) == len(set(effective_tags))
        and all(isinstance(tag, str) and 0 < len(tag) <= 20 for tag in effective_tags),
        "SwanLab 有效标签重复或超长",
    )
    parameter_counts = _static_parameter_counts(config)
    expected_counts = {
        f"{capacity}/{adapter}": EXPECTED_PARAMETER_COUNTS[capacity][adapter]
        for capacity in ("small", "large")
        for adapter in ("R1", "R2")
    }
    _require(parameter_counts == expected_counts, "CUDA-RWKV 参数公式与实参不符")
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "semantic_groups_sha256": semantic["groups_sha256"],
        "parameter_counts": parameter_counts,
        "vendor_manifest_sha256": backend["vendor_manifest_sha256"],
        "data_products_opened": 0,
        "cuda_initialized": False,
        "swanlab_initialized": False,
    }


def _local_module_map() -> dict[str, Path]:
    return {
        "flow_probe": SRC_ROOT / "flow_probe" / "__init__.py",
        "flow_probe.cuda_rwkv_evaluation": SRC_ROOT / "flow_probe" / "cuda_rwkv_evaluation.py",
        "flow_probe.cuda_rwkv_model": SRC_ROOT / "flow_probe" / "cuda_rwkv_model.py",
        "flow_probe.cuda_rwkv_training": SRC_ROOT / "flow_probe" / "cuda_rwkv_training.py",
        "flow_probe.protocol_a_preprocessing": SRC_ROOT / "flow_probe" / "protocol_a_preprocessing.py",
        "flow_probe.protocol_a_raw83": SRC_ROOT / "flow_probe" / "protocol_a_raw83.py",
        "flow_probe.tracking": SRC_ROOT / "flow_probe" / "tracking.py",
        "ch3_cuda_rwkv_raw83_qualification": Path(__file__).resolve(),
        "cuda_rwkv_official_backend": PROJECT_ROOT / "tools" / "cuda_rwkv_official_backend.py",
        "neural_precision_runtime": PROJECT_ROOT / "tools" / "neural_precision_runtime.py",
    }


def dependency_closure(config: Mapping[str, Any]) -> dict[str, Any]:
    module_map = _local_module_map()
    allowed = set(config["dependencies"]["allowed_local_imports"])
    observed_paths = {
        str(path.resolve(strict=True).relative_to(PROJECT_ROOT))
        for path in module_map.values()
    }
    if observed_paths != allowed:
        raise RuntimeError(
            f"本地依赖闭包与配置白名单不等："
            f"extra={sorted(observed_paths - allowed)} missing={sorted(allowed - observed_paths)}"
        )
    local_roots = {name.split(".")[0] for name in module_map}
    imports: dict[str, list[str]] = {}
    for module_name, path in module_map.items():
        if path.is_symlink():
            raise RuntimeError(f"本地依赖不得为符号链接：{path}")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        local_imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                names = [base]
                if base == "flow_probe":
                    names.extend(f"flow_probe.{alias.name}" for alias in node.names)
            else:
                continue
            for imported in names:
                if imported.split(".")[0] in local_roots:
                    if imported not in module_map:
                        raise RuntimeError(f"发现未登记本地导入：{module_name} -> {imported}")
                    local_imports.add(imported)
        imports[module_name] = sorted(local_imports)
    files = [
        {
            "path": relative,
            "bytes": (PROJECT_ROOT / relative).stat().st_size,
            "sha256": sha256_file(PROJECT_ROOT / relative),
        }
        for relative in sorted(observed_paths)
    ]
    result = {
        "schema_version": "cuda-rwkv-dependency-closure-v1",
        "run_id": RUN_ID,
        "files": files,
        "local_import_graph": imports,
        "absolute_path_escape": False,
        "symbolic_links": 0,
    }
    result["closure_sha256"] = canonical_sha256(result)
    return result


def write_dependency_closure(config: Mapping[str, Any], output_path: Path) -> dict[str, Any]:
    result = dependency_closure(config)
    atomic_write_json(output_path, result)
    return result


def check_dependency_closure(config: Mapping[str, Any], path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError("CUDA-RWKV 正式运行缺少依赖闭包收据")
    expected = dependency_closure(config)
    actual = load_json(path)
    if actual != expected:
        raise RuntimeError("CUDA-RWKV 依赖闭包与当前生产文件漂移")
    return actual


def check_target_isolation(config: Mapping[str, Any]) -> dict[str, Any]:
    source = inspect.getsource(run_source)
    forbidden = ("target_dataset_manifest", "target_materialization_config", "target-evaluate")
    hits = [value for value in forbidden if value in source]
    if hits:
        raise RuntimeError(f"源年入口静态引用了目标能力：{hits}")
    counters = config["source_qualification"]
    if any(
        counters[key] != 0
        for key in (
            "target_schema_reads_before_seal",
            "target_feature_rows_read_before_seal",
            "target_label_rows_read_before_seal",
        )
    ):
        raise RuntimeError("源年目标读取冻结计数非零")
    return {
        "schema_version": "cuda-rwkv-target-isolation-static-v1",
        "source_entry_target_references": [],
        "target_schema_reads": 0,
        "target_feature_rows_read": 0,
        "target_label_rows_read": 0,
        "status": "isolated",
    }


def check_source_product_gate(config: Mapping[str, Any]) -> dict[str, Any]:
    manifest_path = Path(config["data"]["source_dataset_manifest"])
    receipt_path = Path(config["data"]["source_product_validation_receipt"])
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RuntimeError("CUDA-RWKV 源年运行需要合法 dataset-manifest.json")
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise RuntimeError("CUDA-RWKV 源年运行需要 validate-product 成功收据")
    manifest_sha256 = sha256_file(manifest_path)
    expected_sha256 = config["data"]["expected_source_manifest_sha256"]
    if manifest_sha256 != expected_sha256:
        raise RuntimeError("CUDA-RWKV 源年清单 SHA-256 与冻结生产身份不符")
    receipt = load_json(receipt_path)
    manifest = load_json(manifest_path)
    expected_content_sha256 = config["data"]["expected_source_manifest_content_sha256"]
    if (
        not str(receipt.get("schema_version", "")).endswith(
            "-published-product-validation-v1"
        )
        or receipt.get("manifest_file_sha256") != manifest_sha256
        or receipt.get("manifest_content_sha256") != expected_content_sha256
        or manifest.get("manifest_content_sha256") != expected_content_sha256
        or not isinstance(receipt.get("verified_artifact_sha256"), dict)
        or not receipt["verified_artifact_sha256"]
    ):
        raise RuntimeError("CUDA-RWKV validate-product 收据与当前源产品不符")
    output_root = manifest_path.parents[2]
    status = load_json(output_root / "status.json")
    pointer = load_json(output_root / "current-source.json")
    if status.get("state") != "finished" or status.get("sealed_through_stage") != "P5":
        raise RuntimeError("CUDA-RWKV 源产品完成状态未封印到 P5")
    if pointer.get("manifest_sha256") != manifest_sha256:
        raise RuntimeError("CUDA-RWKV current-source 指针与源清单不符")
    unsigned_pointer = {
        key: value for key, value in pointer.items() if key != "pointer_content_sha256"
    }
    if pointer.get("pointer_content_sha256") != canonical_sha256(unsigned_pointer):
        raise RuntimeError("CUDA-RWKV current-source 指针内容 SHA-256 无效")
    return {
        "schema_version": "cuda-rwkv-source-product-gate-v1",
        "manifest_sha256": manifest_sha256,
        "validation_receipt_sha256": sha256_file(receipt_path),
        "verified_artifact_count": len(receipt["verified_artifact_sha256"]),
        "status": "admitted",
    }


def check_storage_gate(config: Mapping[str, Any]) -> dict[str, Any]:
    resources = config["resources"]
    bound = resources["checkpoint_storage_bound"]
    large_parameters = max(EXPECTED_PARAMETER_COUNTS["large"].values())
    small_parameters = max(EXPECTED_PARAMETER_COUNTS["small"].values())
    large_units = int(bound["maximum_large_training_units"])
    all_units = int(bound["maximum_unique_training_units"])
    small_units = all_units - large_units
    retained = int(bound["retained_checkpoints_per_unit"])
    bytes_per_parameter = int(bound["parameter_and_optimizer_bytes_per_parameter"])
    safety = float(bound["serialization_safety_factor"])
    retained_bytes = int(
        (large_units * large_parameters + small_units * small_parameters)
        * retained
        * bytes_per_parameter
        * safety
    )
    atomic_temporary_bytes = int(
        large_parameters
        * bytes_per_parameter
        * safety
        * int(bound["maximum_atomic_temporary_files"])
    )
    fixed_headroom_bytes = int(
        (
            float(bound["extension_and_logs_upper_bound_gib"])
            + float(bound["additional_free_space_headroom_gib"])
        )
        * 1024**3
    )
    calculated_required_bytes = (
        retained_bytes + atomic_temporary_bytes + fixed_headroom_bytes
    )
    configured_minimum_bytes = int(resources["minimum_free_disk_gib"] * 1024**3)
    required_bytes = max(calculated_required_bytes, configured_minimum_bytes)
    run_root = Path(config["paths"]["run_root"])
    probe = run_root
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    usage = shutil.disk_usage(probe)
    used_fraction = (usage.total - usage.free) / usage.total
    if usage.free < required_bytes:
        raise RuntimeError(
            f"CUDA-RWKV 磁盘可用空间不足："
            f"free={usage.free} required={required_bytes}"
        )
    if used_fraction >= float(resources["maximum_disk_used_percent_at_start"]) / 100.0:
        raise RuntimeError(
            f"CUDA-RWKV 磁盘使用率不得达到或超过 "
            f"{resources['maximum_disk_used_percent_at_start']}%"
        )
    return {
        "schema_version": "cuda-rwkv-storage-admission-v1",
        "probe_path": str(probe),
        "free_bytes": usage.free,
        "used_fraction": used_fraction,
        "retained_checkpoint_upper_bound_bytes": retained_bytes,
        "maximum_atomic_temporary_bytes": atomic_temporary_bytes,
        "fixed_extension_logs_and_headroom_bytes": fixed_headroom_bytes,
        "calculated_required_bytes": calculated_required_bytes,
        "configured_minimum_bytes": configured_minimum_bytes,
        "required_free_bytes": required_bytes,
        "status": "admitted",
    }


def _secret_from_environment(config: Mapping[str, Any], purpose: str) -> str:
    variable = config["data"]["label_stage_token_environment"][purpose]
    value = os.environ.get(variable)
    if not value:
        raise RuntimeError(f"标签阶段令牌环境变量缺失：{variable}")
    return value


def _unit_result_payload(result: TrainingUnitResult) -> dict[str, Any]:
    return {
        "unit": result.spec.key,
        "arm": result.spec.arm,
        "adapter": result.spec.adapter,
        "capacity": result.spec.capacity,
        "cell": result.spec.cell,
        "best_checkpoint": str(result.best_checkpoint),
        "best_checkpoint_sha256": result.best_checkpoint_sha256,
        "best_epoch": result.best_epoch,
        "validation_flow_average_precision": result.validation_flow_average_precision,
        "model_spec_sha256": result.model_spec_sha256,
        "cuda_execution_identity_sha256": result.cuda_execution_identity_sha256,
        "source_metrics_path": str(result.source_metrics_path),
        "source_metrics_sha256": result.source_metrics_sha256,
    }


def _write_stage_seal(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = {"schema_version": "cuda-rwkv-source-selection-seal-v1", **dict(payload)}
    seal = {**unsigned, "seal_sha256": canonical_sha256(unsigned)}
    atomic_write_json(path, seal)
    return seal


def _run_training_unit(
    *,
    config: Mapping[str, Any],
    config_path: Path,
    dependency_path: Path,
    train_dataset: Any,
    validation_dataset: Any,
    train_token: str,
    validate_token: str,
    spec: TrainingUnitSpec,
    run_root: Path,
    resume: bool,
) -> TrainingUnitResult:
    from flow_probe.cuda_rwkv_training import train_unit

    return train_unit(
        config=config,
        config_path=config_path,
        dependency_closure_path=dependency_path,
        train_dataset=train_dataset,
        validation_dataset=validation_dataset,
        train_label_stage_token=train_token,
        validation_label_stage_token=validate_token,
        spec=spec,
        run_root=run_root,
        resume=resume,
    )


def run_source(config: Mapping[str, Any], config_path: Path, *, resume: bool) -> dict[str, Any]:
    """严格只执行源年选择和四格封印。"""

    source_product_gate = check_source_product_gate(config)
    manifest_path = Path(config["data"]["source_dataset_manifest"])
    run_root = Path(config["paths"]["run_root"])
    dependency_path = Path(config["paths"]["dependency_closure"])
    check_dependency_closure(config, dependency_path)
    isolation = check_target_isolation(config)
    atomic_write_json(run_root / "target-read-audit.json", isolation)
    atomic_write_json(run_root / "source-product-gate.json", source_product_gate)
    from cuda_rwkv_official_backend import run_kernel_self_gate
    from flow_probe import protocol_a_preprocessing as _shared_preprocessing
    from flow_probe.cuda_rwkv_training import (
        TrainingUnitSpec,
        choose_by_flow_ap,
        reuse_training_unit,
    )
    from flow_probe.protocol_a_raw83 import (
        open_protocol_a_dataset,
        validate_source_qualification_seal,
    )

    _ = _shared_preprocessing

    train_dataset = open_protocol_a_dataset(manifest_path, "LSPR23", "train", arm="A")
    validation_dataset = open_protocol_a_dataset(manifest_path, "LSPR23", "validate", arm="A")
    datasets = {
        "A": (train_dataset, validation_dataset),
        "B": (
            open_protocol_a_dataset(manifest_path, "LSPR23", "train", arm="B"),
            open_protocol_a_dataset(manifest_path, "LSPR23", "validate", arm="B"),
        ),
    }
    train_token = _secret_from_environment(config, "train")
    validate_token = _secret_from_environment(config, "validate")
    small_gate_path = run_root / "cuda-gates" / "small-self-gate.json"
    small_gate = run_kernel_self_gate(
        "small",
        build_root=run_root / "build" / "small",
        expected_environment=config["cuda"]["environment"],
        reference_input_commit=config["cuda"]["small_kernel_qualification_input"]["reference_commit"],
    )
    atomic_write_json(small_gate_path, small_gate)
    unit_results: dict[str, TrainingUnitResult] = {}

    def execute(spec: TrainingUnitSpec) -> TrainingUnitResult:
        train_view, validate_view = datasets[spec.arm]
        result = _run_training_unit(
            config=config,
            config_path=config_path,
            dependency_path=dependency_path,
            train_dataset=train_view,
            validation_dataset=validate_view,
            train_token=train_token,
            validate_token=validate_token,
            spec=spec,
            run_root=run_root,
            resume=resume,
        )
        unit_results[spec.key] = result
        return result

    s1_candidates = [
        execute(TrainingUnitSpec(arm, "R2", "small", "C00"))
        for arm in ("A", "B")
    ]
    s1_winner = choose_by_flow_ap(
        s1_candidates,
        tie_order=[result.spec.key for result in s1_candidates],
    )
    manifest = train_dataset.manifest
    arm_payload = {
        "winning_arm": s1_winner.spec.arm,
        "source_manifest_sha256": sha256_file(manifest_path),
        "transform_state_sha256": manifest["transform_state_hashes"][s1_winner.spec.arm],
        "view_content_sha256": manifest["view_content_sha256"][s1_winner.spec.arm],
    }
    arm_payload["source_input_arm_sha256"] = canonical_sha256(arm_payload)
    s1_seal = _write_stage_seal(
        run_root / "seals" / "source-transform-selection.json",
        {
            "stage": "S1",
            **arm_payload,
            "candidates": [_unit_result_payload(value) for value in s1_candidates],
            "selection_metric": "validation_flow_average_precision",
            "target_schema_reads": 0,
            "target_feature_rows_read": 0,
            "target_label_rows_read": 0,
        },
    )
    reused_r2 = reuse_training_unit(
        s1_winner,
        TrainingUnitSpec(s1_winner.spec.arm, "R2", "small", "C00"),
    )
    r1_result = execute(
        TrainingUnitSpec(s1_winner.spec.arm, "R1", "small", "C00")
    )
    s2_candidates = [reused_r2, r1_result]
    s2_winner = choose_by_flow_ap(
        s2_candidates, tie_order=[reused_r2.spec.key, r1_result.spec.key]
    )
    s2_seal = _write_stage_seal(
        run_root / "seals" / "source-adapter-selection.json",
        {
            "stage": "S2",
            "winning_arm": s1_winner.spec.arm,
            "winning_adapter": s2_winner.spec.adapter,
            "reused_unit": reused_r2.spec.key,
            "new_unit": r1_result.spec.key,
            "candidates": [_unit_result_payload(value) for value in s2_candidates],
            "target_schema_reads": 0,
            "target_feature_rows_read": 0,
            "target_label_rows_read": 0,
        },
    )
    reused_small = reuse_training_unit(
        s2_winner,
        TrainingUnitSpec(
            s1_winner.spec.arm, s2_winner.spec.adapter, "small", "C00"
        ),
    )
    large_gate = run_kernel_self_gate(
        "large",
        build_root=run_root / "build" / "large",
        expected_environment=config["cuda"]["environment"],
    )
    atomic_write_json(run_root / "cuda-gates" / "large-self-gate.json", large_gate)
    large_result = execute(
        TrainingUnitSpec(
            s1_winner.spec.arm, s2_winner.spec.adapter, "large", "C00"
        )
    )
    s3_candidates = [reused_small, large_result]
    s3_winner = choose_by_flow_ap(
        s3_candidates, tie_order=[reused_small.spec.key, large_result.spec.key]
    )
    s3_seal = _write_stage_seal(
        run_root / "seals" / "source-capacity-selection.json",
        {
            "stage": "S3",
            "winning_arm": s1_winner.spec.arm,
            "winning_adapter": s2_winner.spec.adapter,
            "winning_capacity": s3_winner.spec.capacity,
            "reused_unit": reused_small.spec.key,
            "new_unit": large_result.spec.key,
            "candidates": [_unit_result_payload(value) for value in s3_candidates],
            "target_schema_reads": 0,
            "target_feature_rows_read": 0,
            "target_label_rows_read": 0,
        },
    )
    final_c00 = reuse_training_unit(
        s3_winner,
        TrainingUnitSpec(
            s1_winner.spec.arm,
            s2_winner.spec.adapter,
            s3_winner.spec.capacity,
            "C00",
        ),
    )
    final_cells = {"C00": final_c00}
    for cell in ("C01", "C10", "C11"):
        final_cells[cell] = execute(
            TrainingUnitSpec(
                s1_winner.spec.arm,
                s2_winner.spec.adapter,
                s3_winner.spec.capacity,
                cell,
            )
        )
    checkpoint_hashes = {
        cell: result.best_checkpoint_sha256 for cell, result in final_cells.items()
    }
    model_specs = {cell: result.model_spec_sha256 for cell, result in final_cells.items()}
    mechanism = {
        cell: dict(config["cells"][cell]) for cell in SOURCE_CELLS
    }
    seal_unsigned = {
        "schema_version": "cuda-rwkv-source-qualification-seal-v1",
        "run_id": RUN_ID,
        "winning_arm": s1_winner.spec.arm,
        "winning_adapter": s2_winner.spec.adapter,
        "winning_capacity": s3_winner.spec.capacity,
        "source_input_arm_sha256": s1_seal["source_input_arm_sha256"],
        "recipe_sha256": canonical_sha256(
            {"S1": s1_seal["seal_sha256"], "S2": s2_seal["seal_sha256"], "S3": s3_seal["seal_sha256"]}
        ),
        "capacity_sha256": canonical_sha256(model_specs),
        "checkpoint_sha256": canonical_sha256(checkpoint_hashes),
        "mechanism_sha256": canonical_sha256(mechanism),
        "evaluation_code_sha256": sha256_file(
            _project_path(config["dependencies"]["evaluation_code_path"])
        ),
        "source_manifest_sha256": sha256_file(manifest_path),
        "dependency_closure_sha256": sha256_file(dependency_path),
        "small_self_gate_sha256": sha256_file(small_gate_path),
        "large_self_gate_sha256": sha256_file(run_root / "cuda-gates" / "large-self-gate.json"),
        "cells": {cell: _unit_result_payload(result) for cell, result in final_cells.items()},
        "target_schema_reads": 0,
        "target_feature_rows_read": 0,
        "target_label_rows_read": 0,
        "persisted_score_rows": 0,
        "persisted_label_rows": 0,
        "persisted_member_rows": 0,
    }
    source_seal = {**seal_unsigned, "seal_sha256": canonical_sha256(seal_unsigned)}
    source_seal_path = Path(config["paths"]["source_seal"])
    atomic_write_json(source_seal_path, source_seal)
    validate_source_qualification_seal(
        source_seal_path,
        expected_input_arm_sha256=source_seal["source_input_arm_sha256"],
    )
    summary = {
        "schema_version": "cuda-rwkv-source-qualification-summary-v1",
        "status": "source_qualified",
        "source_seal_path": str(source_seal_path),
        "source_seal_sha256": sha256_file(source_seal_path),
        "S1_seal_sha256": s1_seal["seal_sha256"],
        "S2_seal_sha256": s2_seal["seal_sha256"],
        "S3_seal_sha256": s3_seal["seal_sha256"],
        "cells": {cell: _unit_result_payload(result) for cell, result in final_cells.items()},
        "target_reads": {"schema": 0, "features": 0, "labels": 0},
    }
    atomic_write_json(run_root / "source-summary.json", summary)
    return summary


def _load_frozen_cell_model(
    config: Mapping[str, Any], cell_payload: Mapping[str, Any], source_seal: Mapping[str, Any]
) -> Any:
    import torch

    from cuda_rwkv_official_backend import load_extension
    from flow_probe.cuda_rwkv_model import build_model

    run_root = Path(config["paths"]["run_root"])
    capacity = str(source_seal["winning_capacity"])
    adapter = str(source_seal["winning_adapter"])
    extension = load_extension(
        capacity,
        build_root=run_root / "build" / capacity,
        expected_environment=config["cuda"]["environment"],
    )
    if extension.identity["cuda_execution_identity_sha256"] != cell_payload["cuda_execution_identity_sha256"]:
        raise RuntimeError(f"{cell_payload['cell']} 目标评价 CUDA 身份漂移")
    model, model_identity = build_model(
        config,
        adapter_key=adapter,
        capacity_key=capacity,
        cell=str(cell_payload["cell"]),
        build_root=run_root / "build",
    )
    model_spec = {**model_identity.spec, "view": source_seal["winning_arm"]}
    if canonical_sha256(model_spec) != cell_payload["model_spec_sha256"]:
        raise RuntimeError(f"{cell_payload['cell']} 目标评价模型规格漂移")
    checkpoint_path = Path(cell_payload["best_checkpoint"])
    if sha256_file(checkpoint_path) != cell_payload["best_checkpoint_sha256"]:
        raise RuntimeError(f"{cell_payload['cell']} 目标评价检查点漂移")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    return model.to(torch.device("cuda"))


def run_target(config: Mapping[str, Any]) -> dict[str, Any]:
    source_seal_path = Path(config["paths"]["source_seal"])
    if not source_seal_path.is_file() or source_seal_path.is_symlink():
        raise RuntimeError("CUDA-RWKV 目标评价需要完整源年资格封印")
    source_seal = load_json(source_seal_path)
    dependency_path = Path(config["paths"]["dependency_closure"])
    check_dependency_closure(config, dependency_path)
    from flow_probe.protocol_a_raw83 import validate_source_qualification_seal

    validate_source_qualification_seal(
        source_seal_path,
        expected_input_arm_sha256=source_seal["source_input_arm_sha256"],
    )
    target_manifest = Path(config["data"]["target_dataset_manifest"])
    if not target_manifest.is_file() or target_manifest.is_symlink():
        raise RuntimeError("CUDA-RWKV 目标评价需要源封印后 P6 dataset-manifest.json")
    import torch

    from flow_probe.cuda_rwkv_evaluation import evaluate_dataset
    from flow_probe.protocol_a_raw83 import open_protocol_a_dataset

    target_dataset = open_protocol_a_dataset(
        target_manifest,
        "LSPR24",
        "target-evaluate",
        arm=None,
        source_qualification_seal=source_seal_path,
    )
    target_token = _secret_from_environment(config, "target-evaluate")
    cell_results: dict[str, Any] = {}
    source_seal_sha256 = sha256_file(source_seal_path)
    for cell in SOURCE_CELLS:
        cell_payload = source_seal["cells"][cell]
        cell_path = Path(config["paths"]["run_root"]) / "target-cells" / f"{cell}.json"
        if cell_path.is_file():
            metrics = load_json(cell_path)
            if (
                metrics.get("source_seal_sha256") != source_seal_sha256
                or metrics.get("checkpoint_sha256")
                != cell_payload["best_checkpoint_sha256"]
                or metrics.get("evaluation_call") != 1
            ):
                raise RuntimeError(f"{cell} 目标年完成收据身份漂移")
        else:
            model = _load_frozen_cell_model(config, cell_payload, source_seal)
            metrics = evaluate_dataset(
                model=model,
                dataset=target_dataset,
                purpose="target-evaluate",
                label_stage_token=target_token,
                batch_sequences=int(config["evaluation"]["batch_sequences"]),
                device=torch.device("cuda"),
            )
            metrics.update(
                {
                    "cell": cell,
                    "independent_test": False,
                    "target_previously_accessed": True,
                    "evaluation_call": 1,
                    "checkpoint_sha256": cell_payload["best_checkpoint_sha256"],
                    "source_seal_sha256": source_seal_sha256,
                }
            )
            atomic_write_json(cell_path, metrics)
        cell_results[cell] = metrics
    result = {
        "schema_version": "cuda-rwkv-target-descriptive-evaluation-v1",
        "run_id": RUN_ID,
        "source_seal_sha256": source_seal_sha256,
        "target_manifest_sha256": sha256_file(target_manifest),
        "independent_test": False,
        "target_previously_accessed": True,
        "cells": cell_results,
        "persisted_score_rows": 0,
        "persisted_label_rows": 0,
        "persisted_member_rows": 0,
    }
    result["result_sha256"] = canonical_sha256(result)
    atomic_write_json(Path(config["paths"]["target_results"]), result)
    return result


def _tracking_metrics(config: Mapping[str, Any]) -> dict[str, float | int]:
    source = load_json(Path(config["paths"]["run_root"]) / "source-summary.json")
    target = load_json(Path(config["paths"]["target_results"]))
    metrics: dict[str, float | int] = {}
    for year, payload in (("source", source), ("target", target)):
        cells = payload["cells"]
        for cell, item in cells.items():
            if year == "source":
                item = load_json(Path(item["source_metrics_path"]))
            scalar = {
                key: item[key]
                for key in (
                    "flow_average_precision",
                    "entity_average_precision",
                    "maximum_entity_average_precision",
                )
            }
            metrics.update(
                {
                    f"{year}/{cell}/{key}": value
                    for key, value in scalar.items()
                    if isinstance(value, (int, float)) and not isinstance(value, bool)
                }
            )
    return metrics


def publish_attempt(
    config: Mapping[str, Any],
    *,
    attempt: int,
    authorized_workspace: str,
    authorized_project: str,
) -> int:
    if attempt not in (1, 2):
        raise ValueError("SwanLab 发布尝试只能为 1 或 2")
    source_seal = Path(config["paths"]["source_seal"])
    target_results = Path(config["paths"]["target_results"])
    if not source_seal.is_file() or not target_results.is_file():
        raise RuntimeError("SwanLab 最终聚合发布需要源封印和目标聚合结果")
    attempts_root = Path(config["paths"]["tracking_attempts"])
    top_manifest = attempts_root.parent / "tracking-manifest.json"
    for number in (1, 2):
        root = attempts_root / f"attempt-{number}"
        success = root / "success-receipt.json"
        if success.is_file():
            receipt = load_json(success)
            if not top_manifest.is_file():
                atomic_write_json(top_manifest, receipt)
            return 0
        if (root / "inflight-receipt.json").is_file():
            raise RuntimeError("SwanLab 存在无成功收据的在途运行，禁止重复初始化")
    if attempt == 2:
        first_failure = attempts_root / "attempt-1" / "failure-receipt.json"
        if not first_failure.is_file() or load_json(first_failure).get("retry_exit_code") != 91:
            raise RuntimeError("第二次 SwanLab 尝试缺少首次零步 401 收据")
    attempt_root = attempts_root / f"attempt-{attempt}"
    for gate in ("swanlab-ping.log", "swanlab-verify.log"):
        gate_path = attempt_root / gate
        if not gate_path.is_file() or gate_path.stat().st_size == 0:
            raise RuntimeError(f"SwanLab 尝试缺少健康门日志：{gate}")
    from flow_probe.tracking import initialize_swanlab_run

    try:
        swanlab_module, run, tag_receipt = initialize_swanlab_run(
            config["tracking"],
            alias_config_path=_project_path(config["tracking"]["alias_config_path"]),
            expected_alias_config_sha256=config["tracking"]["alias_config_sha256"],
            config={
                "run_id": RUN_ID,
                "source_seal_sha256": sha256_file(source_seal),
                "target_results_sha256": sha256_file(target_results),
                "dependency_closure_sha256": sha256_file(Path(config["paths"]["dependency_closure"])),
            },
            log_dir=attempt_root / "swanlog",
            tag_receipt_path=attempt_root / "swanlab-tag-receipt.json",
            authorized_workspace=authorized_workspace,
            authorized_project=authorized_project,
        )
    except Exception as error:
        retryable = attempt == 1 and "401" in str(error)
        failure = {
            "schema_version": "cuda-rwkv-swanlab-failure-receipt-v1",
            "attempt": attempt,
            "zero_step": True,
            "http_401": retryable,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "retry_exit_code": 91 if retryable else None,
        }
        atomic_write_json(attempt_root / "failure-receipt.json", failure)
        if retryable:
            return 91
        raise
    run_id = getattr(run, "id", None)
    if not isinstance(run_id, str) or not run_id:
        raise RuntimeError("SwanLab init 返回后缺少云端运行 ID")
    inflight = {
        "schema_version": "cuda-rwkv-swanlab-inflight-receipt-v1",
        "attempt": attempt,
        "cloud_run_id": run_id,
        "logged_steps": 0,
        "source_seal_sha256": sha256_file(source_seal),
        "target_results_sha256": sha256_file(target_results),
    }
    atomic_write_json(attempt_root / "inflight-receipt.json", inflight)
    metrics = _tracking_metrics(config)
    swanlab_module.log(metrics, step=0)
    inflight["logged_steps"] = 1
    atomic_write_json(attempt_root / "inflight-receipt.json", inflight)
    swanlab_module.finish()
    tag_receipt_path = attempt_root / "swanlab-tag-receipt.json"
    success = {
        "schema_version": "cuda-rwkv-swanlab-success-receipt-v1",
        "attempt": attempt,
        "cloud_run_id": run_id,
        "logged_steps": 1,
        "metric_count": len(metrics),
        "tag_receipt_sha256": sha256_file(tag_receipt_path),
        "source_seal_sha256": sha256_file(source_seal),
        "target_results_sha256": sha256_file(target_results),
        "status": "finished",
    }
    atomic_write_json(attempt_root / "success-receipt.json", success)
    atomic_write_json(top_manifest, success)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="独立 CUDA-RWKV Raw83 分阶段资格与四格入口"
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--validate-config", action="store_true")
    action.add_argument("--write-dependency-closure", action="store_true")
    action.add_argument("--check-dependency-closure", action="store_true")
    action.add_argument("--check-target-isolation", action="store_true")
    action.add_argument("--check-source-product", action="store_true")
    action.add_argument("--check-storage-gate", action="store_true")
    action.add_argument("--run-source", action="store_true")
    action.add_argument("--run-target", action="store_true")
    action.add_argument("--publish-attempt", type=int, choices=(1, 2))
    parser.add_argument("--dependency-closure-path", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = args.config.resolve(strict=True)
    config = load_json(config_path)
    validation = validate_config(config)
    dependency_path = args.dependency_closure_path or Path(
        config["paths"]["dependency_closure"]
    )
    if args.validate_config:
        result: Any = validation
    elif args.write_dependency_closure:
        result = write_dependency_closure(config, dependency_path)
    elif args.check_dependency_closure:
        result = check_dependency_closure(config, dependency_path)
    elif args.check_target_isolation:
        result = check_target_isolation(config)
    elif args.check_source_product:
        result = check_source_product_gate(config)
    elif args.check_storage_gate:
        result = check_storage_gate(config)
    elif args.run_source:
        result = run_source(config, config_path, resume=args.resume)
    elif args.run_target:
        result = run_target(config)
    elif args.publish_attempt is not None:
        if not args.authorized_swanlab_workspace or not args.authorized_swanlab_project:
            parser.error("--publish-attempt 需要本轮授权的 SwanLab workspace/project")
        return publish_attempt(
            config,
            attempt=args.publish_attempt,
            authorized_workspace=args.authorized_swanlab_workspace,
            authorized_project=args.authorized_swanlab_project,
        )
    else:
        parser.print_help()
        return 0
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
