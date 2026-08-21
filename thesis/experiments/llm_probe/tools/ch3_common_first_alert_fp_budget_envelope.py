#!/usr/bin/env python3
"""五个既有系统在 LSPR24 上的共同实际首次告警 FP 预算包络。

本入口不训练、不调参、不重选任何超参数，只对既有冻结系统做一次零训练的目标年
描述性评价：按良性 ``path_max`` 完整并列组生成各方法自身的全部可达阈值，以整数
假阳性实体预算 ``k`` 为公共横轴，各方法只取自身 ``FP<=k`` 的最后可达点。禁止拆
分同分并列组、禁止插值、禁止持久化逐流或逐实体分数与二维曝光矩阵。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import resource
import shutil
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = Path(__file__).resolve().parent

RUN_ID = "ch3-common-first-alert-fp-budget-envelope-v1"
DISPLAY_NAME = "五系统共同实际首次告警FP预算包络"
CONFIG_SCHEMA = "ch3-common-first-alert-fp-budget-envelope-config-v1"
RESULT_SCHEMA = "ch3-common-first-alert-fp-budget-envelope-results-v1"
PATH_CURVE_SCHEMA = "ch3-common-first-alert-path-budget-curves-v1"
TERMINAL_CURVE_SCHEMA = "ch3-common-first-alert-terminal-at-path-threshold-v1"
TIMELY_SCHEMA = "ch3-common-first-alert-timely-detection-v1"
MANIFEST_SCHEMA = "ch3-common-first-alert-fp-budget-envelope-manifest-v1"

N_FLOW = 20_227_356
N_ENTITY = 47_115
N_POSITIVE_ENTITY = 752
N_NEGATIVE_ENTITY = 46_363
FLOW_POSITIVE_RATE = 0.0257073138
N_SEQUENCE_WIDTH = 128

NOMINAL_BUDGETS: tuple[float, ...] = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)
COMMON_INTEGER_BUDGETS: tuple[int, ...] = (46, 231, 463, 927, 1854, 3709)
FIRST_ALERT_QUANTILES: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0)
QUANTILE_NAMES: tuple[str, ...] = (
    "minimum",
    "p25",
    "median",
    "p75",
    "p90",
    "p95",
    "p99",
    "maximum",
)

METHOD_KEYS: tuple[str, ...] = (
    "full_mlp_o11",
    "xgb_cpa_elp_c11",
    "cnn_published_max",
    "gru_published_max",
    "transformer_published_max",
)
PUBLISHED_METHOD_KEYS: tuple[str, ...] = (
    "cnn_published_max",
    "gru_published_max",
    "transformer_published_max",
)
STAGES: tuple[str, ...] = (
    "validate_shared_identity",
    "published_neural_aggregate",
    "xgb_rescore_and_aggregate",
    "mlp_infer_and_aggregate",
    "common_budget_projection",
    "finalize",
)
REQUIRED_METHOD_INPUTS: dict[str, set[str]] = {
    "cnn_published_max": {"flow_scores"},
    "gru_published_max": {"flow_scores"},
    "transformer_published_max": {"flow_scores"},
    "xgb_cpa_elp_c11": {
        "semantic168_model",
        "selection_seal",
        "effective_config_receipts",
        "parent_evaluation_result",
        "parent_evaluation_manifest",
        "target_features",
        "target_sequence_index",
        "target_sequence_mask",
    },
    "full_mlp_o11": {
        "selected_checkpoint",
        "selection_receipt",
        "frozen_run_config",
        "target_features",
        "target_sequence_index",
        "target_sequence_mask",
    },
}

PATH_CURVE_FIELDS: tuple[str, ...] = (
    "threshold",
    "tie_group_size",
    "tie_group_positive_entity_count",
    "tie_group_negative_entity_count",
    "path_true_positive_entity_count",
    "path_false_positive_entity_count",
    "path_false_positive_rate",
    "path_detection_rate",
    "last_reachable_index_by_integer_budget",
)
TERMINAL_CURVE_FIELDS: tuple[str, ...] = (
    "terminal_true_positive_entity_count",
    "terminal_false_positive_entity_count",
    "terminal_false_positive_rate",
    "terminal_detection_rate",
)

FORBIDDEN_NAME_FRAGMENTS: tuple[str, ...] = (
    "flow-score",
    "flow_score",
    "entity-score",
    "entity_score",
    "per-entity-first-alert",
    "per_entity_first_alert",
    "entity-mapping",
    "entity_mapping",
    "semantic168",
    "exposure-matrix",
    "exposure_matrix",
    "checkpoint",
    ".npy",
    ".pt",
    ".ubj",
)

T0 = time.time()
LAST_BEAT = [T0]
np: Any = None


# ----------------------------------------------------------------------------
# 基础设施
# ----------------------------------------------------------------------------


def load_numeric_dependencies() -> None:
    """静态入口只依赖标准库；正式阶段才加载冻结环境中的 NumPy。"""
    global np
    if np is not None:
        return
    try:
        import numpy as numpy_module
    except ModuleNotFoundError as error:  # pragma: no cover - 依赖缺失时的可操作提示
        raise SystemExit(
            "正式计算阶段需要 NumPy，当前解释器不可用："
            f"{error}。请在服务器冻结环境下先加载 tools/env/activate.sh，"
            "再用 uv run --no-sync python 执行本入口；本机静态检查只支持 --validate-config。"
        ) from error
    np = numpy_module


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def beat(stage: str, done: int, total: int, started: float, every: float = 30.0) -> None:
    """限频心跳，报告已处理量、总量、吞吐与可计算的剩余时间。"""
    now = time.time()
    if now - LAST_BEAT[0] < every and done < total:
        return
    LAST_BEAT[0] = now
    elapsed = now - started
    rate = done / max(elapsed, 1e-9)
    remaining = (total - done) / max(rate, 1e-9)
    log(
        f"[{stage}] {done:,}/{total:,} ({done / max(total, 1):.1%}) "
        f"吞吐 {rate:,.0f}/s 累计 {elapsed:.0f}s 预计剩余 {remaining:.0f}s"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def atomic_npz(path: Path, vectors: Mapping[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **vectors)
    os.replace(temporary, path)
    return artifact_receipt(path)


def artifact_receipt(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"制品缺失或为空：{path}")
    return {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def process_peak_rss_mib() -> float:
    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak / 1024.0 if sys.platform != "darwin" else peak / (1024.0 * 1024.0)


def read_cgroup_number(name: str) -> int | None:
    legacy_name = {
        "memory.current": "memory.usage_in_bytes",
        "memory.peak": "memory.max_usage_in_bytes",
    }.get(name, name)
    for candidate in (Path("/sys/fs/cgroup") / name, Path("/sys/fs/cgroup/memory") / legacy_name):
        if candidate.is_file():
            value = candidate.read_text(encoding="utf-8").strip()
            if value.isdigit():
                return int(value)
    return None


def write_status(
    output_root: Path,
    state: str,
    stage: str,
    detail: str,
    exit_code: int | None,
    unreachable: Mapping[str, str] | None = None,
) -> None:
    status_path = output_root / "status.json"
    recovery_count = 0
    if status_path.is_file():
        try:
            recovery_count = int(load_json(status_path).get("recovery_count", 0))
        except (OSError, ValueError, json.JSONDecodeError):
            recovery_count = 0
    atomic_json(
        status_path,
        {
            "schema_version": "ch3-common-first-alert-fp-budget-envelope-status-v1",
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "state": state,
            "stage": stage,
            "detail": detail,
            "exit_code": exit_code,
            "updated_at_unix": time.time(),
            "recovery_count": recovery_count,
            "unreachable_methods": dict(unreachable or {}),
            "training_runs": 0,
            "hyperparameter_selection_runs": 0,
            "persist_per_flow_scores": False,
            "persist_per_entity_scores": False,
            "persist_per_entity_first_alert": False,
            "persist_entity_mapping": False,
        },
    )


def bump_recovery_count(output_root: Path) -> int:
    status_path = output_root / "status.json"
    if not status_path.is_file():
        return 0
    status = load_json(status_path)
    count = int(status.get("recovery_count", 0)) + 1
    status["recovery_count"] = count
    status["updated_at_unix"] = time.time()
    atomic_json(status_path, status)
    return count


# ----------------------------------------------------------------------------
# 配置门
# ----------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DISPLAY_NAME)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/ch3-common-first-alert-fp-budget-envelope-v1.json",
        help="冻结配置路径",
    )
    parser.add_argument("--validate-config", action="store_true", help="只核验冻结配置，不触碰数据")
    parser.add_argument(
        "--stage",
        choices=(*STAGES, "compute"),
        help=(
            "执行单个原子阶段；compute 在同一进程内按序执行前五个计算阶段。"
            "finalize 必须单独进程执行，否则 run.log 会在封口后继续增长导致清单摘要失效"
        ),
    )
    parser.add_argument("--project-root", type=Path, help="llm_probe 生产根，正式阶段必填")
    parser.add_argument("--resume", action="store_true", help="幂等核验并跳过已原子发布的阶段")
    parser.add_argument(
        "--admission-receipt",
        type=Path,
        help="启动器写出的资源准入读数，finalize 阶段必填",
    )
    return parser.parse_args()


def require_equal(config: Mapping[str, Any], key: str, expected: Any) -> None:
    if config.get(key) != expected:
        raise SystemExit(f"配置字段不符：{key}")


def validate_method_contract(key: str, contract: Mapping[str, Any]) -> None:
    required = {
        "display_name",
        "source_kind",
        "online_score",
        "terminal_score",
        "probability_clip",
        "logical_training_runs",
        "logical_target_inference_calls",
        "logical_target_score_calls",
        "target_retrained",
        "inputs",
    }
    if set(contract) != required:
        raise SystemExit(f"方法合同字段集不符：{key}")
    if not isinstance(contract["display_name"], str) or not contract["display_name"].strip():
        raise SystemExit(f"方法缺少有意义的中文展示名：{key}")
    if contract["logical_training_runs"] != 0 or contract["target_retrained"] is not False:
        raise SystemExit(f"方法必须是零训练目标年评价：{key}")
    if key in PUBLISHED_METHOD_KEYS:
        expected = {
            "source_kind": "persisted_published_flow_scores",
            "online_score": "prefix_maximum",
            "terminal_score": "complete_entity_maximum",
            "probability_clip": None,
            "logical_target_inference_calls": 0,
            "logical_target_score_calls": 0,
        }
    elif key == "xgb_cpa_elp_c11":
        expected = {
            "source_kind": "frozen_semantic168_booster_single_logical_rescore",
            "online_score": "running_arithmetic_mean",
            "terminal_score": "complete_entity_arithmetic_mean",
            "probability_clip": [1e-7, 1.0],
            "logical_target_inference_calls": 0,
            "logical_target_score_calls": 1,
        }
    else:
        expected = {
            "source_kind": "frozen_o11_checkpoint_single_logical_inference",
            "online_score": "running_power_mean_p_from_selection_receipt",
            "terminal_score": "complete_entity_power_mean_p_from_selection_receipt",
            "probability_clip": [1e-7, 1.0],
            "logical_target_inference_calls": 1,
            "logical_target_score_calls": 0,
        }
    for field, value in expected.items():
        if contract.get(field) != value:
            raise SystemExit(f"方法在线口径或零训练次数不符：{key}.{field}")
    inputs = contract["inputs"]
    if not isinstance(inputs, dict) or not inputs:
        raise SystemExit(f"方法输入清单为空：{key}")
    if set(inputs) != REQUIRED_METHOD_INPUTS[key]:
        raise SystemExit(f"方法输入名称集不符：{key}")
    for name, item in inputs.items():
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("relative_path"), str)
            or not isinstance(item.get("sha256"), str)
            or len(item["sha256"]) != 64
        ):
            raise SystemExit(f"方法输入缺少路径或 SHA-256：{key}.{name}")


def validate_config(config: Mapping[str, Any]) -> None:
    """机械核验冻结配置；任一项不符立即失败，不静默修正。"""
    require_equal(config, "schema_version", CONFIG_SCHEMA)
    require_equal(config, "run_id", RUN_ID)
    require_equal(config, "display_name", DISPLAY_NAME)
    require_equal(config, "dataset", "LSPR24")
    require_equal(config, "target_previously_accessed", True)
    require_equal(config, "independent_test", False)
    require_equal(config, "formal_paper_evidence", False)
    require_equal(config, "screening_only", False)
    require_equal(config, "training_runs", 0)
    require_equal(config, "hyperparameter_selection_runs", 0)
    require_equal(config, "evidence_ceiling", "目标年描述性共同首次告警包络")

    identity = config.get("target_identity", {})
    if identity != {
        "flow_count": N_FLOW,
        "entity_count": N_ENTITY,
        "positive_entity_count": N_POSITIVE_ENTITY,
        "negative_entity_count": N_NEGATIVE_ENTITY,
        "flow_positive_rate": FLOW_POSITIVE_RATE,
        "sequence_width": N_SEQUENCE_WIDTH,
        "entity_key": "unordered_source_destination_address_pair",
        "entity_label": "maximum_flow_label",
        "exposure_order": "ascending_frozen_flow_array_index_within_entity",
        "exposure_index_base": 1,
        "timestamp_input_loaded": False,
        "time_delay_available": False,
    }:
        raise SystemExit("LSPR24 冻结身份、实体构造或曝光顺序合同不符")

    shared = config.get("shared_inputs", {})
    if set(shared) != {"flow_labels", "source_addresses", "destination_addresses"}:
        raise SystemExit("共享评价输入白名单必须严格为 y24/s24/d24")
    for name, item in shared.items():
        if (
            not isinstance(item.get("relative_path"), str)
            or not isinstance(item.get("sha256"), str)
            or len(item["sha256"]) != 64
        ):
            raise SystemExit(f"共享输入缺少路径或 SHA-256：{name}")

    methods = config.get("methods", {})
    if tuple(methods) != METHOD_KEYS:
        raise SystemExit("五个稳定方法键或顺序不符")
    for key, contract in methods.items():
        validate_method_contract(key, contract)

    budget = config.get("common_budget", {})
    if budget != {
        "axis": "integer_false_positive_entity_count",
        "axis_minimum": 0,
        "axis_maximum": N_NEGATIVE_ENTITY,
        "tie_group_rule": "complete_benign_path_max_tie_groups_never_split",
        "selection_rule": "last_reachable_threshold_with_path_fp_not_exceeding_k",
        "interpolation": False,
        "exact_fpr_intersection": False,
        "nominal_budgets": list(NOMINAL_BUDGETS),
        "common_integer_budgets": list(COMMON_INTEGER_BUDGETS),
        "integer_budget_formula": "floor(nominal_budget*negative_entity_count)",
        "nominal_4_percent_is_empirical_anchor_not_deployment_standard": True,
    }:
        raise SystemExit("公共整数 FP 预算轴、不拆同分或不插值合同不符")
    for nominal, integer_budget in zip(NOMINAL_BUDGETS, COMMON_INTEGER_BUDGETS, strict=True):
        if math.floor(nominal * N_NEGATIVE_ENTITY) != integer_budget:
            raise SystemExit(f"六档公共整数预算与向下取整公式不符：{nominal}")

    evaluation = config.get("evaluation", {})
    if evaluation != {
        "path_curve_threshold_source": "all_entity_path_max_descending_unique",
        "threshold_semantics": "online_score_greater_equal_threshold",
        "zero_false_positive_boundary": "nextafter_of_global_maximum_path_max",
        "terminal_curve_threshold_source": "identical_to_path_curve_thresholds",
        "first_alert_axis": "exposure_index",
        "exposure_index_base": 1,
        "first_alert_quantiles": list(FIRST_ALERT_QUANTILES),
        "timely_detection_denominator": N_POSITIVE_ENTITY,
        "timely_curve_encoding": "right_continuous_exact_first_crossing_breakpoints",
        "timely_detection_budget_count": len(COMMON_INTEGER_BUDGETS),
        "benign_first_alert_count_must_equal_path_false_positive": True,
        "time_delay_available": False,
        "time_delay_unavailable_reason": (
            "目标输入不含完整流available_ns，曝光序号不能解释为真实时间时延"
        ),
        "dominance_tolerance": 0.0,
        "dominance_requires_strict_improvement_somewhere": True,
        "synthetic_best_of_baselines_forbidden": True,
    }:
        raise SystemExit("完整路径曲线、同阈值终端曲线或及时检出评价合同不符")

    arrays = config.get("full_flow_array_budget", {})
    if arrays != {
        "entity_id_int32": 1,
        "stable_order_int64": 1,
        "exposure_index_int64": 1,
        "current_method_probability_float32": 1,
        "online_running_score_float64": 1,
        "transient_int64_first_alert_candidate": 1,
        "dense_entity_by_exposure_matrix": 0,
        "threshold_by_flow_matrix": 0,
        "note": (
            "在线运行分数与首次跨越候选是运行均值/幂平均无法避免的全流级工作区，"
            "已在实施报告登记为对计划第五节数组清单的显式增补"
        ),
    }:
        raise SystemExit("全流级数组种类或二维矩阵禁令不符")

    execution = config.get("execution", {})
    if execution != {
        "xgb_predict_batch": 2_000_000,
        "xgb_sequence_batch": 2048,
        "mlp_inference_batch_from_frozen_entry": 2048,
        "batching_is_engineering_detail_only": True,
        "reuses_frozen_production_entries": True,
    }:
        raise SystemExit("批处理明细或复用冻结生产入口合同不符")

    resources = config.get("resource_contract", {})
    if resources != {
        "authorized_server": "B76",
        "minimum_free_gpu_memory_mib": 12288,
        "minimum_cgroup_available_memory_gib": 48,
        "minimum_free_disk_gib": 10,
        "maximum_disk_used_percent": 79,
        "maximum_parallel_units": 1,
        "wall_clock_limit": None,
        "gpu_hour_limit": None,
        "stage_atomic_resume": True,
        "fair_efficiency_evidence": False,
    }:
        raise SystemExit("资源准入、并发或无时长上限合同不符")

    if config.get("tracking") != {
        "workspace": "mortiswang",
        "project": "ns3-rwkv-lspr24",
        "mode": "online",
        "aggregate_only": True,
    }:
        raise SystemExit("SwanLab 授权目的地或仅聚合上报合同不符")

    if config.get("artifact_policy") != {
        "output_root": f"runs/diagnostics/{RUN_ID}",
        "atomic_json_and_npz": True,
        "persist_aggregate_results": True,
        "persist_complete_path_budget_curves": True,
        "persist_terminal_at_path_threshold_curves": True,
        "persist_first_alert_timing_curves": True,
        "persist_method_level_aggregates_for_resume": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_per_entity_first_alert": False,
        "persist_entity_mapping": False,
        "persist_derived_matrices": False,
        "persist_models_or_checkpoints": False,
    }:
        raise SystemExit("原子制品或禁止持久化合同不符")

    schema_keys = config.get("schema_keys", {})
    if schema_keys != {
        "config": CONFIG_SCHEMA,
        "results": RESULT_SCHEMA,
        "path_budget_curves": PATH_CURVE_SCHEMA,
        "terminal_at_path_threshold": TERMINAL_CURVE_SCHEMA,
        "timely_detection": TIMELY_SCHEMA,
        "manifest": MANIFEST_SCHEMA,
    }:
        raise SystemExit("模式版本键不符")

    if tuple(config.get("stages", ())) != STAGES:
        raise SystemExit("原子阶段清单或顺序不符")


# ----------------------------------------------------------------------------
# 路径解析与输入身份
# ----------------------------------------------------------------------------


def resolve_within(project_root: Path, relative_path: str) -> Path:
    if Path(relative_path).is_absolute():
        raise SystemExit(f"配置路径必须相对项目根：{relative_path}")
    resolved = (project_root / relative_path).resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise SystemExit(f"配置路径越出项目根：{relative_path}") from error
    return resolved


def resolve_runtime_paths(config: Mapping[str, Any], project_root_arg: Path | None) -> tuple[Path, Path]:
    if project_root_arg is None:
        raise SystemExit("正式阶段必须显式传入 --project-root（llm_probe 生产根）")
    project_root = project_root_arg.resolve()
    if project_root.name != "llm_probe" or not (project_root / "pyproject.toml").is_file():
        raise SystemExit(f"显式项目根不是 llm_probe 生产根：{project_root}")
    output_root = resolve_within(project_root, str(config["artifact_policy"]["output_root"]))
    if output_root.name != RUN_ID:
        raise SystemExit("输出目录与运行身份不一致")
    return project_root, output_root


def probe_frozen_file(project_root: Path, item: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """返回 (收据, 缺失原因)。缺失记为不可达；存在但摘要不符即身份失败。"""
    path = resolve_within(project_root, str(item["relative_path"]))
    if not path.is_file() or path.stat().st_size <= 0:
        return None, f"冻结输入缺失或为空：{item['relative_path']}"
    actual_bytes = path.stat().st_size
    if "bytes" in item and actual_bytes != int(item["bytes"]):
        raise SystemExit(
            f"冻结输入字节数不符：{item['relative_path']} 期望 {item['bytes']} 实际 {actual_bytes}"
        )
    digest = sha256_file(path)
    if digest != item["sha256"]:
        raise SystemExit(f"冻结输入 SHA-256 不符：{item['relative_path']}")
    return {
        "relative_path": item["relative_path"],
        "bytes": actual_bytes,
        "sha256": digest,
    }, None


# ----------------------------------------------------------------------------
# 共享评价层
# ----------------------------------------------------------------------------


def build_shared_layer(project_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    """一次构造共享实体编号、稳定实体内流序、实体标签并复现共同分母。"""
    load_numeric_dependencies()
    shared = config["shared_inputs"]
    labels_path = resolve_within(project_root, str(shared["flow_labels"]["relative_path"]))
    source_path = resolve_within(project_root, str(shared["source_addresses"]["relative_path"]))
    destination_path = resolve_within(project_root, str(shared["destination_addresses"]["relative_path"]))

    started = time.time()
    flow_labels_raw = np.load(labels_path, mmap_mode="r", allow_pickle=False)
    if flow_labels_raw.shape != (N_FLOW,):
        raise SystemExit(f"冻结逐流标签形状不符：{flow_labels_raw.shape}")
    flow_labels = np.asarray(flow_labels_raw)
    if not np.isfinite(flow_labels).all() or not np.logical_or(flow_labels == 0, flow_labels == 1).all():
        raise SystemExit("冻结逐流标签不是有限二值数组")
    flow_positive_rate = float(np.mean(flow_labels, dtype=np.float64))
    if abs(flow_positive_rate - FLOW_POSITIVE_RATE) >= 1e-9:
        raise SystemExit(f"LSPR24 逐流正例率不符：{flow_positive_rate:.12f}")
    flow_labels = flow_labels.astype(np.int8, copy=False)

    source = np.load(source_path, allow_pickle=True)
    destination = np.load(destination_path, allow_pickle=True)
    if source.shape != (N_FLOW,) or destination.shape != (N_FLOW,):
        raise SystemExit("冻结源端或目的端地址数组形状不符")
    entity_keys = np.fromiter(
        (
            f"{left}|{right}" if left <= right else f"{right}|{left}"
            for left, right in zip(source, destination, strict=True)
        ),
        dtype=object,
        count=N_FLOW,
    )
    del source, destination
    _, entity = np.unique(entity_keys, return_inverse=True)
    del entity_keys
    entity = entity.astype(np.int32, copy=False)
    if int(entity.min()) != 0 or int(entity.max()) != N_ENTITY - 1:
        raise SystemExit(f"实体编号边界不符，实体数应为 {N_ENTITY:,}")
    entity_counts = np.bincount(entity, minlength=N_ENTITY).astype(np.int64)
    if len(entity_counts) != N_ENTITY or int(entity_counts.min()) <= 0:
        raise SystemExit("实体编号不连续或存在零曝光实体")
    if int(entity_counts.sum()) != N_FLOW:
        raise SystemExit("每条流未恰好属于一个实体")

    entity_labels = np.zeros(N_ENTITY, dtype=np.int8)
    np.maximum.at(entity_labels, entity, flow_labels)
    positive_count = int((entity_labels == 1).sum())
    negative_count = int((entity_labels == 0).sum())
    if positive_count != N_POSITIVE_ENTITY or negative_count != N_NEGATIVE_ENTITY:
        raise SystemExit(f"共同分母不符：正实体 {positive_count} 负实体 {negative_count}")

    order = np.argsort(entity, kind="stable").astype(np.int64, copy=False)
    ordered_entity = entity[order]
    starts = np.r_[0, np.flatnonzero(ordered_entity[1:] != ordered_entity[:-1]) + 1].astype(np.int64)
    if not np.array_equal(ordered_entity[starts], np.arange(N_ENTITY, dtype=np.int32)):
        raise SystemExit("稳定排序未覆盖连续实体编号，曝光顺序不可信")
    lengths = np.diff(np.r_[starts, N_FLOW]).astype(np.int64)
    if not np.array_equal(lengths, entity_counts):
        raise SystemExit("实体内曝光段长度与实体计数不一致")
    exposure_index = (
        np.arange(N_FLOW, dtype=np.int64) - np.repeat(starts, lengths) + 1
    ).astype(np.int64)
    if int(exposure_index.min()) != 1 or int(exposure_index.max()) != int(lengths.max()):
        raise SystemExit("1 基实体内曝光序号构造异常")
    del ordered_entity
    log(f"共享评价层构造完成，用时 {time.time() - started:.1f}s")

    return {
        "entity": entity,
        "entity_labels": entity_labels,
        "entity_counts": entity_counts,
        "order": order,
        "starts": starts,
        "lengths": lengths,
        "exposure_index": exposure_index,
        "flow_positive_rate": flow_positive_rate,
        "identity": {
            "flow_count": N_FLOW,
            "entity_count": N_ENTITY,
            "positive_entity_count": positive_count,
            "negative_entity_count": negative_count,
            "flow_positive_rate": flow_positive_rate,
            "maximum_entity_exposure_count": int(lengths.max()),
            "maximum_positive_entity_exposure_count": int(entity_counts[entity_labels == 1].max()),
            "each_flow_in_exactly_one_entity": True,
            "every_entity_has_at_least_one_flow": True,
            "exposure_order": "ascending_frozen_flow_array_index_within_entity",
            "exposure_index_base": 1,
            "entity_mapping_persisted": False,
        },
    }


# ----------------------------------------------------------------------------
# 在线分数、完整并列组曲线与公共整数预算
# ----------------------------------------------------------------------------


def ordered_probabilities(
    flow_probabilities: Any,
    shared: Mapping[str, Any],
    clip: Sequence[float] | None,
) -> tuple[Any, float, float]:
    if flow_probabilities.shape != (N_FLOW,):
        raise SystemExit(f"逐流概率形状不符：{flow_probabilities.shape}")
    if not np.isfinite(flow_probabilities).all():
        raise SystemExit("逐流概率含非有限值")
    minimum = float(flow_probabilities.min())
    maximum = float(flow_probabilities.max())
    if minimum < 0.0 or maximum > 1.0:
        raise SystemExit(f"逐流概率越出 [0,1]：min={minimum} max={maximum}")
    values = flow_probabilities[shared["order"]].astype(np.float64, copy=True)
    if clip is not None:
        np.clip(values, float(clip[0]), float(clip[1]), out=values)
    return values, minimum, maximum


def running_prefix_maximum(values: Any, starts: Any, lengths: Any) -> Any:
    """逐实体前缀最大值；并列组完整保留，不跨实体累计。"""
    running = values
    started = time.time()
    total = len(starts)
    for position, (start, length) in enumerate(
        zip(starts.tolist(), lengths.tolist(), strict=True), start=1
    ):
        stop = start + length
        np.maximum.accumulate(running[start:stop], out=running[start:stop])
        if position % 4096 == 0 or position == total:
            beat("在线前缀最大值", position, total, started)
    return running


def running_power_mean(values: Any, shared: Mapping[str, Any], exponent: float) -> Any:
    """逐实体运行 p 幂平均；p=1 即运行算术平均。全部累加保持 FP64。"""
    if not math.isfinite(exponent) or exponent <= 0.0:
        raise SystemExit(f"幂平均指数必须是有限正数：{exponent}")
    starts = shared["starts"]
    lengths = shared["lengths"]
    running = values
    if exponent != 1.0:
        np.power(running, exponent, out=running)
    np.cumsum(running, dtype=np.float64, out=running)
    previous = np.zeros(len(starts), dtype=np.float64)
    previous[1:] = running[starts[1:] - 1]
    running -= np.repeat(previous, lengths)
    running /= shared["exposure_index"]
    if exponent != 1.0:
        np.power(running, 1.0 / exponent, out=running)
    return running


def path_and_terminal(running: Any, shared: Mapping[str, Any]) -> tuple[Any, Any]:
    starts = shared["starts"]
    lengths = shared["lengths"]
    path_max = np.maximum.reduceat(running, starts).astype(np.float64, copy=False)
    terminal = running[starts + lengths - 1].astype(np.float64, copy=False)
    if not np.isfinite(path_max).all() or not np.isfinite(terminal).all():
        raise SystemExit("实体路径最大值或终端读数含非有限值")
    if not bool((terminal <= path_max).all()):
        raise SystemExit("终端读数超过路径最大值，在线聚合实现异常")
    return path_max, terminal


def complete_tie_group_curve(path_max: Any, terminal: Any, entity_labels: Any) -> dict[str, Any]:
    """按全部实体 path_max 的降序唯一值生成完整并列组曲线，绝不拆分同分组。"""
    order = np.argsort(path_max, kind="stable")[::-1]
    scores = path_max[order]
    labels = entity_labels[order].astype(np.int64, copy=False)
    group_starts = np.r_[0, np.flatnonzero(scores[1:] != scores[:-1]) + 1].astype(np.int64)
    group_size = np.diff(np.r_[group_starts, N_ENTITY]).astype(np.int64)
    group_positive = np.add.reduceat(labels, group_starts).astype(np.int64)
    group_negative = (group_size - group_positive).astype(np.int64)
    threshold = scores[group_starts].astype(np.float64)

    threshold = np.r_[np.nextafter(float(threshold[0]), math.inf), threshold].astype(np.float64)
    group_size = np.r_[0, group_size].astype(np.int64)
    group_positive = np.r_[0, group_positive].astype(np.int64)
    group_negative = np.r_[0, group_negative].astype(np.int64)
    path_tp = np.cumsum(group_positive, dtype=np.int64)
    path_fp = np.cumsum(group_negative, dtype=np.int64)

    positive_terminal = np.sort(terminal[entity_labels == 1])
    negative_terminal = np.sort(terminal[entity_labels == 0])
    terminal_tp = (
        N_POSITIVE_ENTITY - np.searchsorted(positive_terminal, threshold, side="left")
    ).astype(np.int64)
    terminal_fp = (
        N_NEGATIVE_ENTITY - np.searchsorted(negative_terminal, threshold, side="left")
    ).astype(np.int64)

    curve = {
        "threshold": threshold,
        "tie_group_size": group_size,
        "tie_group_positive_entity_count": group_positive,
        "tie_group_negative_entity_count": group_negative,
        "path_true_positive_entity_count": path_tp,
        "path_false_positive_entity_count": path_fp,
        "path_false_positive_rate": path_fp.astype(np.float64) / N_NEGATIVE_ENTITY,
        "path_detection_rate": path_tp.astype(np.float64) / N_POSITIVE_ENTITY,
        "terminal_true_positive_entity_count": terminal_tp,
        "terminal_false_positive_entity_count": terminal_fp,
        "terminal_false_positive_rate": terminal_fp.astype(np.float64) / N_NEGATIVE_ENTITY,
        "terminal_detection_rate": terminal_tp.astype(np.float64) / N_POSITIVE_ENTITY,
    }
    assert_curve_invariants(curve, path_max)
    return curve


def assert_curve_invariants(curve: Mapping[str, Any], path_max: Any) -> None:
    threshold = curve["threshold"]
    path_fp = curve["path_false_positive_entity_count"]
    path_tp = curve["path_true_positive_entity_count"]
    if not bool((np.diff(threshold) < 0).all()):
        raise SystemExit("完整曲线阈值不是严格单调下降")
    if int(path_fp[0]) != 0 or int(path_tp[0]) != 0:
        raise SystemExit("完整曲线缺少 TP=FP=0 的零误报边界")
    if int(path_fp[-1]) != N_NEGATIVE_ENTITY or int(path_tp[-1]) != N_POSITIVE_ENTITY:
        raise SystemExit("完整曲线缺少 TP=P、FP=B 的全量边界")
    if not bool((np.diff(path_fp) >= 0).all()) or not bool((np.diff(path_tp) >= 0).all()):
        raise SystemExit("完整曲线的假阳或真阳计数不是单调不减")
    if int(curve["tie_group_size"].sum()) != N_ENTITY:
        raise SystemExit("完整并列组未覆盖全部实体")
    ascending = np.sort(path_max)
    covered = (N_ENTITY - np.searchsorted(ascending, threshold, side="left")).astype(np.int64)
    reached = (path_fp + path_tp).astype(np.int64)
    if not np.array_equal(covered, reached):
        raise SystemExit("存在被拆分的同分并列组，阈值累计数与实际 path_max 计数不符")
    if not bool((curve["terminal_false_positive_entity_count"] <= path_fp).all()):
        raise SystemExit("同阈值终端假阳超过路径假阳，终端曲线口径异常")
    if not bool((curve["terminal_true_positive_entity_count"] <= path_tp).all()):
        raise SystemExit("同阈值终端真阳超过路径真阳，终端曲线口径异常")


def project_integer_budgets(path_fp: Any) -> Any:
    """对全部整数 k 取自身 FP<=k 的最后可达完整并列组索引；不插值、不拆同分。"""
    budgets = np.arange(0, N_NEGATIVE_ENTITY + 1, dtype=np.int64)
    index = (np.searchsorted(path_fp, budgets, side="right") - 1).astype(np.int64)
    if int(index.min()) < 0:
        raise SystemExit("整数预算投影缺少零误报可达点")
    if not bool((path_fp[index] <= budgets).all()):
        raise SystemExit("整数预算投影选中了超出预算的点")
    following = index + 1
    interior = following < len(path_fp)
    if not bool((path_fp[following[interior]] > budgets[interior]).all()):
        raise SystemExit("整数预算投影不是最后可达点")
    if not bool((np.diff(index) >= 0).all()):
        raise SystemExit("整数预算投影索引不是单调不减")
    return index.astype(np.int32, copy=False)


def curve_point(curve: Mapping[str, Any], index: int) -> dict[str, Any]:
    return {
        "curve_index": index,
        "threshold": float(curve["threshold"][index]),
        "threshold_semantics": "online_score_greater_equal_threshold",
        "complete_tie_group_size": int(curve["tie_group_size"][index]),
        "tie_group_positive_entity_count": int(curve["tie_group_positive_entity_count"][index]),
        "tie_group_negative_entity_count": int(curve["tie_group_negative_entity_count"][index]),
        "path_false_positive_entity_count": int(curve["path_false_positive_entity_count"][index]),
        "path_false_positive_rate": float(curve["path_false_positive_rate"][index]),
        "path_true_positive_entity_count": int(curve["path_true_positive_entity_count"][index]),
        "path_detection_rate": float(curve["path_detection_rate"][index]),
        "terminal_false_positive_entity_count": int(curve["terminal_false_positive_entity_count"][index]),
        "terminal_false_positive_rate": float(curve["terminal_false_positive_rate"][index]),
        "terminal_true_positive_entity_count": int(curve["terminal_true_positive_entity_count"][index]),
        "terminal_detection_rate": float(curve["terminal_detection_rate"][index]),
        "interpolated": False,
        "tie_group_split": False,
    }


def budget_readouts(curve: Mapping[str, Any], index_by_budget: Any) -> dict[str, dict[str, Any]]:
    readouts: dict[str, dict[str, Any]] = {}
    total_points = len(curve["threshold"])
    for nominal, integer_budget in zip(NOMINAL_BUDGETS, COMMON_INTEGER_BUDGETS, strict=True):
        index = int(index_by_budget[integer_budget])
        best = curve_point(curve, index)
        following = (
            curve_point(curve, index + 1) if index + 1 < total_points else None
        )
        readouts[f"k_{integer_budget}"] = {
            "nominal_budget": nominal,
            "common_integer_budget": integer_budget,
            "nominal_budget_is_label_only": True,
            "actual_reachable_point": best,
            "next_reachable_point": following,
            "next_point_exceeds_budget": (
                None
                if following is None
                else following["path_false_positive_entity_count"] > integer_budget
            ),
            "selection_rule": "last_reachable_threshold_with_path_fp_not_exceeding_k",
        }
    return readouts


def distribution(values: Any) -> dict[str, Any]:
    if not len(values):
        return {"count": 0, **{name: None for name in QUANTILE_NAMES}}
    points = np.quantile(values.astype(np.float64), FIRST_ALERT_QUANTILES)
    return {
        "count": int(len(values)),
        **dict(zip(QUANTILE_NAMES, (float(value) for value in points), strict=True)),
    }


def first_alert_timely(
    running: Any,
    shared: Mapping[str, Any],
    curve: Mapping[str, Any],
    readouts: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """六档公共预算的首次告警阶梯；固定 P=752 分母，未告警正实体保留为删失。"""
    entity_labels = shared["entity_labels"]
    entity_counts = shared["entity_counts"]
    starts = shared["starts"]
    exposure_index = shared["exposure_index"]
    positive = entity_labels == 1
    benign = entity_labels == 0
    sentinel = np.iinfo(np.int64).max
    summaries: dict[str, Any] = {}
    vectors: dict[str, Any] = {}

    for budget_key, readout in readouts.items():
        point = readout["actual_reachable_point"]
        threshold = float(point["threshold"])
        candidate = np.where(running >= threshold, exposure_index, sentinel)
        first_alert = np.minimum.reduceat(candidate, starts)
        del candidate
        first_alert[first_alert == sentinel] = 0

        alerted_positive = positive & (first_alert > 0)
        alerted_benign = benign & (first_alert > 0)
        benign_alert_count = int(alerted_benign.sum())
        if benign_alert_count != int(point["path_false_positive_entity_count"]):
            raise SystemExit(
                f"{budget_key} 良性首次告警数 {benign_alert_count} 与该阈值 path_fp "
                f"{point['path_false_positive_entity_count']} 不一致"
            )
        positive_positions = first_alert[alerted_positive]
        if len(positive_positions):
            breakpoints, counts = np.unique(positive_positions, return_counts=True)
            axis = np.r_[0, breakpoints].astype(np.int64)
            rate = np.r_[
                0.0, np.cumsum(counts, dtype=np.int64).astype(np.float64) / N_POSITIVE_ENTITY
            ].astype(np.float64)
        else:
            axis = np.zeros(1, dtype=np.int64)
            rate = np.zeros(1, dtype=np.float64)
        never_alerted = int((positive & (first_alert == 0)).sum())
        summaries[budget_key] = {
            "nominal_budget": readout["nominal_budget"],
            "common_integer_budget": readout["common_integer_budget"],
            "threshold": threshold,
            "threshold_semantics": "online_score_greater_equal_threshold",
            "complete_tie_group_kept": True,
            "axis": "exposure_index",
            "exposure_index_base": 1,
            "positive_entity_denominator": N_POSITIVE_ENTITY,
            "alerted_positive_entity_count": int(alerted_positive.sum()),
            "never_alerted_positive_entity_count": never_alerted,
            "positive_unalerted_rate": float(never_alerted / N_POSITIVE_ENTITY),
            "benign_entity_denominator": N_NEGATIVE_ENTITY,
            "alerted_benign_entity_count": benign_alert_count,
            "actual_first_alert_false_positive_rate": float(
                benign_alert_count / N_NEGATIVE_ENTITY
            ),
            "path_false_positive_entity_count": int(point["path_false_positive_entity_count"]),
            "first_alert_exposure_index": distribution(positive_positions),
            "maximum_positive_entity_exposure_count": int(entity_counts[positive].max()),
            "timely_curve_point_count": int(len(axis)),
            "timely_curve_final_rate": float(rate[-1]),
        }
        vectors[f"{budget_key}__exposure_index"] = axis
        vectors[f"{budget_key}__timely_detection_rate"] = rate
        del first_alert, positive_positions

    return (
        {
            "axis": "exposure_index",
            "exposure_index_base": 1,
            "curve_encoding": "right_continuous_exact_first_crossing_breakpoints",
            "timely_detection_denominator": N_POSITIVE_ENTITY,
            "time_delay_available": False,
            "budgets": summaries,
            "persisted_per_flow_scores": False,
            "persisted_per_entity_scores": False,
            "persisted_per_entity_first_alert": False,
        },
        vectors,
    )


# ----------------------------------------------------------------------------
# 方法级聚合与原子发布
# ----------------------------------------------------------------------------


def method_artifact_names(method_key: str) -> tuple[str, str, str]:
    return (
        f"method-aggregates/{method_key}.json",
        f"method-aggregates/{method_key}.npz",
        f"method-aggregates/{method_key}-receipt.json",
    )


def method_artifacts_complete(
    output_root: Path,
    method_key: str,
    identity: Mapping[str, Any],
    resume: bool,
) -> bool:
    """已原子发布且身份一致时返回 True；非恢复模式遇到历史制品直接拒绝覆盖。"""
    json_name, npz_name, receipt_name = method_artifact_names(method_key)
    receipt_path = output_root / receipt_name
    if not receipt_path.is_file():
        if not resume and any(
            (output_root / name).exists() for name in (json_name, npz_name)
        ):
            raise SystemExit(
                f"全新运行存在 {method_key} 的半程制品；仅允许用 --resume 幂等核验后续跑"
            )
        return False
    if not resume:
        raise SystemExit(
            f"{method_key} 聚合阶段已完成；仅允许用 --resume 幂等跳过，禁止覆盖旧目录"
        )
    receipt = load_json(receipt_path)
    if receipt.get("method_key") != method_key or receipt.get("identity") != dict(identity):
        raise SystemExit(f"既有方法聚合身份与当前工具/配置/输入不符，拒绝覆盖：{method_key}")
    for name in (json_name, npz_name):
        item = receipt.get("artifacts", {}).get(name, {})
        path = output_root / name
        if (
            not path.is_file()
            or path.stat().st_size != item.get("bytes")
            or sha256_file(path) != item.get("sha256")
        ):
            raise SystemExit(f"既有方法聚合制品与收据不符，拒绝覆盖：{method_key}")
    return True


def publish_method(
    output_root: Path,
    method_key: str,
    identity: Mapping[str, Any],
    aggregate: Mapping[str, Any],
    vectors: Mapping[str, Any],
) -> None:
    json_name, npz_name, receipt_name = method_artifact_names(method_key)
    atomic_json(output_root / json_name, aggregate)
    atomic_npz(output_root / npz_name, vectors)
    atomic_json(
        output_root / receipt_name,
        {
            "schema_version": "ch3-common-first-alert-method-aggregate-receipt-v1",
            "run_id": RUN_ID,
            "method_key": method_key,
            "identity": dict(identity),
            "artifacts": {
                json_name: artifact_receipt(output_root / json_name),
                npz_name: artifact_receipt(output_root / npz_name),
            },
            "published_at_unix": time.time(),
        },
    )


def aggregate_method(
    method_key: str,
    contract: Mapping[str, Any],
    shared: Mapping[str, Any],
    flow_probabilities: Any,
    source_receipt: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """单方法在线聚合：只在逐流概率驻留一份时完成两次稳定顺序扫描。"""
    clip = contract["probability_clip"]
    values, raw_minimum, raw_maximum = ordered_probabilities(flow_probabilities, shared, clip)
    online = contract["online_score"]
    if online == "prefix_maximum":
        running = running_prefix_maximum(values, shared["starts"], shared["lengths"])
        exponent: float | None = None
    elif online == "running_arithmetic_mean":
        exponent = 1.0
        running = running_power_mean(values, shared, exponent)
    else:
        exponent = float(source_receipt["power_mean_p"])
        running = running_power_mean(values, shared, exponent)

    path_max, terminal = path_and_terminal(running, shared)
    if online == "prefix_maximum" and not np.array_equal(path_max, terminal):
        raise SystemExit(f"{method_key} 前缀最大池化的路径与终端读数未逐位相等")
    curve = complete_tie_group_curve(path_max, terminal, shared["entity_labels"])
    index_by_budget = project_integer_budgets(curve["path_false_positive_entity_count"])
    readouts = budget_readouts(curve, index_by_budget)
    timely, timely_vectors = first_alert_timely(running, shared, curve, readouts)

    vectors = {name: curve[name] for name in PATH_CURVE_FIELDS if name in curve}
    vectors["last_reachable_index_by_integer_budget"] = index_by_budget
    vectors.update({name: curve[name] for name in TERMINAL_CURVE_FIELDS})
    vectors.update({f"first_alert__{name}": value for name, value in timely_vectors.items()})

    aggregate = {
        "schema_version": "ch3-common-first-alert-method-aggregate-v1",
        "run_id": RUN_ID,
        "method_key": method_key,
        "display_name": contract["display_name"],
        "online_score": online,
        "terminal_score": contract["terminal_score"],
        "power_mean_p": exponent,
        "probability_clip": None if clip is None else [float(clip[0]), float(clip[1])],
        "raw_probability_range": {"minimum": raw_minimum, "maximum": raw_maximum},
        "curve_point_count": int(len(curve["threshold"])),
        "path_max_equals_terminal": bool(np.array_equal(path_max, terminal)),
        "budget_readouts": readouts,
        "first_alert": timely,
        "score_source": dict(source_receipt),
        "persisted_per_flow_scores": False,
        "persisted_per_entity_scores": False,
        "persisted_per_entity_first_alert": False,
        "persisted_entity_mapping": False,
    }
    del values, running, path_max, terminal, curve, index_by_budget
    return aggregate, vectors


# ----------------------------------------------------------------------------
# 阶段一：共享身份与全部冻结输入
# ----------------------------------------------------------------------------


def stage_validate_shared_identity(context: dict[str, Any]) -> dict[str, Any]:
    config = context["config"]
    project_root = context["project_root"]
    output_root = context["output_root"]
    write_status(output_root, "running", "validate_shared_identity", "核验共享数组、实体与全部冻结输入", None)

    files: dict[str, Any] = {}
    for name, item in config["shared_inputs"].items():
        receipt, missing = probe_frozen_file(project_root, item)
        if missing is not None:
            raise SystemExit(f"共享评价输入不可缺失：{missing}")
        files[f"shared/{name}"] = receipt

    unreachable: dict[str, str] = {}
    for method_key, contract in config["methods"].items():
        reasons: list[str] = []
        for name, item in contract["inputs"].items():
            receipt, missing = probe_frozen_file(project_root, item)
            if missing is not None:
                reasons.append(missing)
            else:
                files[f"{method_key}/{name}"] = receipt
        if reasons:
            unreachable[method_key] = "；".join(reasons)
            log(f"方法不可达：{method_key}（{unreachable[method_key]}）")

    shared = build_shared_layer(project_root, config)
    context["shared"] = shared
    receipt = {
        "schema_version": "ch3-common-first-alert-input-validation-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "tool_sha256": context["tool_sha256"],
        "config_sha256": context["config_sha256"],
        "files": files,
        "files_canonical_sha256": canonical_sha256(files),
        "shared_identity": shared["identity"],
        "unreachable_methods": unreachable,
        "dataset": "LSPR24",
        "target_previously_accessed": True,
        "independent_test": False,
        "target_labels_used_for_evaluation_envelope": True,
        "target_labels_used_for_model_input_p_or_method_pool": False,
        "training_runs": 0,
        "hyperparameter_selection_runs": 0,
    }
    atomic_json(output_root / "input-validation-receipt.json", receipt)
    atomic_json(output_root / "config.json", config)
    context["unreachable"] = unreachable
    context["input_receipt"] = receipt
    return receipt


def ensure_input_receipt(context: dict[str, Any]) -> dict[str, Any]:
    """读取阶段一收据并核对工具与配置身份；后续阶段的不可达清单以它为准。"""
    if context.get("input_receipt") is not None:
        return context["input_receipt"]
    receipt_path = context["output_root"] / "input-validation-receipt.json"
    if not receipt_path.is_file():
        raise SystemExit(
            "尚未完成 validate_shared_identity 阶段，禁止直接进入后续阶段；"
            "请先执行 --stage validate_shared_identity 或使用 --stage compute"
        )
    receipt = load_json(receipt_path)
    if (
        receipt.get("tool_sha256") != context["tool_sha256"]
        or receipt.get("config_sha256") != context["config_sha256"]
    ):
        raise SystemExit("工具或配置身份自阶段一以来已变化，拒绝续跑")
    context["input_receipt"] = receipt
    context["unreachable"] = dict(receipt.get("unreachable_methods", {}))
    return receipt


def require_shared(context: dict[str, Any]) -> dict[str, Any]:
    """方法级阶段单独运行时重建共享层，并机械核对阶段一登记的身份。"""
    if context.get("shared") is not None:
        return context["shared"]
    receipt = ensure_input_receipt(context)
    shared = build_shared_layer(context["project_root"], context["config"])
    if shared["identity"] != receipt.get("shared_identity"):
        raise SystemExit("重建的共享实体身份与阶段一收据不符，拒绝按新分母静默重算")
    context["shared"] = shared
    return shared


def method_identity(context: dict[str, Any], method_key: str) -> dict[str, Any]:
    contract = context["config"]["methods"][method_key]
    return {
        "tool_sha256": context["tool_sha256"],
        "config_sha256": context["config_sha256"],
        "shared_identity_sha256": canonical_sha256(require_shared(context)["identity"]),
        "inputs_sha256": canonical_sha256(
            {name: item["sha256"] for name, item in contract["inputs"].items()}
        ),
        "online_score": contract["online_score"],
        "terminal_score": contract["terminal_score"],
    }


def skip_unreachable(context: dict[str, Any], method_key: str) -> bool:
    reason = context.get("unreachable", {}).get(method_key)
    if reason is None:
        return False
    log(f"跳过不可达方法 {method_key}：{reason}")
    return True


# ----------------------------------------------------------------------------
# 阶段二：三份已发表神经分数
# ----------------------------------------------------------------------------


def stage_published_neural_aggregate(context: dict[str, Any]) -> None:
    config = context["config"]
    output_root = context["output_root"]
    project_root = context["project_root"]
    ensure_input_receipt(context)
    pending = [key for key in PUBLISHED_METHOD_KEYS if not skip_unreachable(context, key)]
    if not pending:
        return
    shared = require_shared(context)
    for method_key in pending:
        contract = config["methods"][method_key]
        identity = method_identity(context, method_key)
        if method_artifacts_complete(output_root, method_key, identity, context["resume"]):
            log(f"{method_key} 聚合制品身份匹配，幂等跳过")
            continue
        write_status(
            output_root,
            "running",
            "published_neural_aggregate",
            f"逐模型处理 {contract['display_name']}",
            None,
            context.get("unreachable"),
        )
        score_path = resolve_within(
            project_root, str(contract["inputs"]["flow_scores"]["relative_path"])
        )
        started = time.time()
        scores = np.load(score_path, mmap_mode="r", allow_pickle=False)
        if scores.dtype != np.dtype("float32"):
            raise SystemExit(f"{method_key} 冻结分数类型不符：{scores.dtype}")
        flow_probabilities = np.asarray(scores)
        source_receipt = {
            "source_kind": contract["source_kind"],
            "relative_path": contract["inputs"]["flow_scores"]["relative_path"],
            "sha256": contract["inputs"]["flow_scores"]["sha256"],
            "logical_training_runs": 0,
            "logical_target_inference_calls": 0,
            "logical_target_score_calls": 0,
            "target_retrained": False,
            "model_loaded": False,
            "score_fusion_performed": False,
            "target_scores_persisted": False,
        }
        aggregate, vectors = aggregate_method(
            method_key, contract, shared, flow_probabilities, source_receipt
        )
        aggregate["stage_seconds"] = time.time() - started
        publish_method(output_root, method_key, identity, aggregate, vectors)
        del flow_probabilities, scores, vectors
        log(f"{method_key} 聚合完成，用时 {time.time() - started:.1f}s")


# ----------------------------------------------------------------------------
# 阶段三：XGBoost＋CPA-ELP C11 一次逻辑重打分
# ----------------------------------------------------------------------------


def stage_xgb_rescore_and_aggregate(context: dict[str, Any]) -> None:
    method_key = "xgb_cpa_elp_c11"
    config = context["config"]
    output_root = context["output_root"]
    project_root = context["project_root"]
    contract = config["methods"][method_key]
    ensure_input_receipt(context)
    if skip_unreachable(context, method_key):
        return
    shared = require_shared(context)
    identity = method_identity(context, method_key)
    if method_artifacts_complete(output_root, method_key, identity, context["resume"]):
        log(f"{method_key} 聚合制品身份匹配，幂等跳过")
        return
    write_status(
        output_root,
        "running",
        "xgb_rescore_and_aggregate",
        "同一冻结 semantic168 模型执行一次逻辑目标打分",
        None,
        context.get("unreachable"),
    )
    if str(TOOL_DIR) not in sys.path:
        sys.path.insert(0, str(TOOL_DIR))
    try:
        import ch3_xgb_cpa_elp_operational_backfill as xgb_backfill
    except ModuleNotFoundError as error:
        raise SystemExit(
            f"无法导入冻结 XGBoost 回填入口以复用 semantic168 与打分逻辑：{error}"
        ) from error
    xgb_backfill.load_numeric_dependencies()

    parent_root = resolve_within(
        project_root, str(contract["inputs"]["semantic168_model"]["relative_path"])
    ).parent
    booster, torch_module, xgboost_version = xgb_backfill.load_frozen_model(
        {"paths": {"parent_run_root": str(parent_root)}}
    )
    cache_root = resolve_within(project_root, str(contract["inputs"]["target_features"]["relative_path"])).parent
    started = time.time()
    features = np.load(cache_root / "X24.npy", mmap_mode="r", allow_pickle=False)
    sequence_index = np.load(cache_root / "I24.npy", mmap_mode="r", allow_pickle=False)
    sequence_mask = np.load(cache_root / "M24.npy", mmap_mode="r", allow_pickle=False)
    sequence_contract = xgb_backfill.validate_sequence_index_contract(sequence_index, sequence_mask)
    semantic = xgb_backfill.build_semantic_matrix(
        features,
        sequence_index,
        sequence_mask,
        int(config["execution"]["xgb_predict_batch"]),
        int(config["execution"]["xgb_sequence_batch"]),
    )
    del features, sequence_index, sequence_mask
    score_started = time.time()
    flow_probabilities, api_batches = xgb_backfill.predict_once(
        booster,
        semantic,
        int(config["execution"]["xgb_predict_batch"]),
        torch_module,
    )
    scoring_seconds = time.time() - score_started
    del semantic, booster
    torch_module.cuda.empty_cache()

    source_receipt = {
        "source_kind": contract["source_kind"],
        "relative_path": contract["inputs"]["semantic168_model"]["relative_path"],
        "sha256": contract["inputs"]["semantic168_model"]["sha256"],
        "xgboost_version": xgboost_version,
        "prediction_device": "cuda:0",
        "semantic168_build_count": 1,
        "sequence_index_contract": sequence_contract,
        "logical_training_runs": 0,
        "logical_target_inference_calls": 0,
        "logical_target_score_calls": 1,
        "predict_api_batches_within_single_logical_call": api_batches,
        "target_retrained": False,
        "raw83_branch_used": False,
        "single_logical_score_seconds": scoring_seconds,
        "target_scores_persisted": False,
    }
    aggregate, vectors = aggregate_method(
        method_key, contract, shared, flow_probabilities, source_receipt
    )
    aggregate["stage_seconds"] = time.time() - started
    publish_method(output_root, method_key, identity, aggregate, vectors)
    del flow_probabilities, vectors
    log(f"{method_key} 聚合完成，用时 {time.time() - started:.1f}s")


# ----------------------------------------------------------------------------
# 阶段四：全容量 MLP O11 一次逻辑推理
# ----------------------------------------------------------------------------


def read_o11_power_mean_p(project_root: Path, contract: Mapping[str, Any], torch_module: Any) -> dict[str, Any]:
    """从 O11 选择收据读取全精度 p，并用检查点 p_log 独立复算交叉核对。"""
    receipt_path = resolve_within(
        project_root, str(contract["inputs"]["selection_receipt"]["relative_path"])
    )
    selection = load_json(receipt_path)
    value = selection.get("selection", {}).get("p_at_selection")
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0.0:
        raise SystemExit("O11 选择收据缺少有限正的 p_at_selection")
    receipt_p = float(value)
    checkpoint_path = resolve_within(
        project_root, str(contract["inputs"]["selected_checkpoint"]["relative_path"])
    )
    payload = torch_module.load(checkpoint_path, map_location="cpu", weights_only=False)
    state = payload.get("model", {})
    if "p_log" not in state:
        raise SystemExit("O11 选中检查点缺少学习幂平均参数 p_log")
    checkpoint_p = float(
        torch_module.exp(state["p_log"].float()).clamp(1e-3, 1e3).item()
    )
    tolerance = 4.0 * sys.float_info.epsilon * max(1.0, abs(receipt_p))
    if abs(checkpoint_p - receipt_p) > tolerance:
        raise SystemExit(
            f"O11 检查点复算 p={checkpoint_p!r} 与选择收据 p={receipt_p!r} 不一致"
        )
    return {
        "power_mean_p": receipt_p,
        "power_mean_p_hex": float.hex(receipt_p),
        "power_mean_p_source": "receipts/selection-O11.json:selection.p_at_selection",
        "power_mean_p_checkpoint_recomputed": checkpoint_p,
        "power_mean_p_reselected": False,
        "power_mean_p_rounded_value_reconstructed": False,
        "state_dict": state,
        "payload": payload,
    }


def stage_mlp_infer_and_aggregate(context: dict[str, Any]) -> None:
    method_key = "full_mlp_o11"
    config = context["config"]
    output_root = context["output_root"]
    project_root = context["project_root"]
    contract = config["methods"][method_key]
    ensure_input_receipt(context)
    if skip_unreachable(context, method_key):
        return
    shared = require_shared(context)
    identity = method_identity(context, method_key)
    if method_artifacts_complete(output_root, method_key, identity, context["resume"]):
        log(f"{method_key} 聚合制品身份匹配，幂等跳过")
        return
    write_status(
        output_root,
        "running",
        "mlp_infer_and_aggregate",
        "O11 选中检查点执行一次逻辑目标推理",
        None,
        context.get("unreachable"),
    )
    if str(TOOL_DIR) not in sys.path:
        sys.path.insert(0, str(TOOL_DIR))
    try:
        import ch3_full_mlp_complete_entity_lp_protocol_a_q0_bf16 as mlp_bf16
    except ModuleNotFoundError as error:
        raise SystemExit(
            f"无法导入冻结全容量 MLP BF16 入口以复用模型与推理逻辑：{error}"
        ) from error
    torch_module = mlp_bf16.legacy.torch
    if torch_module is None or not torch_module.cuda.is_available():
        raise SystemExit("O11 目标推理要求可用 CUDA，拒绝以 CPU 冒充冻结推理路径")

    mlp_config_path = resolve_within(
        project_root, str(contract["inputs"]["frozen_run_config"]["relative_path"])
    )
    mlp_config = load_json(mlp_config_path)
    mlp_bf16.validate_config(mlp_config)
    mlp_bf16.install_runtime(mlp_config, argparse.Namespace(config=str(mlp_config_path)))

    power = read_o11_power_mean_p(project_root, contract, torch_module)
    started = time.time()
    model = mlp_bf16.build_model(mlp_config, "O11")
    model.load_state_dict(power.pop("state_dict"))
    device = torch_module.device("cuda:0")
    model = model.to(device)
    recomputed = float(model.p.detach().cpu().item())
    if abs(recomputed - power["power_mean_p"]) > 4.0 * sys.float_info.epsilon * max(
        1.0, abs(power["power_mean_p"])
    ):
        raise SystemExit("装载后的 O11 学习幂平均指数与选择收据不一致")
    power.pop("payload", None)

    cache_root = resolve_within(
        project_root, str(contract["inputs"]["target_features"]["relative_path"])
    ).parent
    target = {
        "X24": np.load(cache_root / "X24.npy", allow_pickle=False),
        "I24": np.load(cache_root / "I24.npy", allow_pickle=False),
        "M24": np.load(cache_root / "M24.npy", allow_pickle=False),
        "y24": np.load(cache_root / "y24.npy", allow_pickle=False),
    }
    if target["X24"].shape != (N_FLOW, 83):
        raise SystemExit(f"LSPR24 特征形状不符：{target['X24'].shape}")
    inference_started = time.time()
    flow_probabilities, seen = mlp_bf16.score_target(mlp_config, model, target, device)
    inference_seconds = time.time() - inference_started
    if not bool(seen.all()):
        raise SystemExit("O11 一次逻辑推理未覆盖全部合法流")
    peak_gpu_mib = float(torch_module.cuda.max_memory_reserved(device)) / 2**20
    del model, target, seen
    torch_module.cuda.empty_cache()

    source_receipt = {
        "source_kind": contract["source_kind"],
        "relative_path": contract["inputs"]["selected_checkpoint"]["relative_path"],
        "sha256": contract["inputs"]["selected_checkpoint"]["sha256"],
        "torch_version": str(torch_module.__version__),
        "precision_profile_id": mlp_bf16.PROFILE_ID,
        "probability_generated_in_fp32_island": True,
        "logical_training_runs": 0,
        "logical_target_inference_calls": 1,
        "logical_target_score_calls": 0,
        "target_retrained": False,
        "single_logical_inference_seconds": inference_seconds,
        "peak_gpu_reserved_mib": peak_gpu_mib,
        "target_scores_persisted": False,
        **power,
    }
    aggregate, vectors = aggregate_method(
        method_key, contract, shared, flow_probabilities, source_receipt
    )
    aggregate["stage_seconds"] = time.time() - started
    publish_method(output_root, method_key, identity, aggregate, vectors)
    del flow_probabilities, vectors
    log(f"{method_key} 聚合完成，用时 {time.time() - started:.1f}s")


# ----------------------------------------------------------------------------
# 阶段五：公共整数预算投影与子向量支配
# ----------------------------------------------------------------------------


def step_evaluate(axis: Any, rate: Any, queries: Any) -> Any:
    position = np.searchsorted(axis, queries, side="right") - 1
    if int(position.min()) < 0:
        raise SystemExit("及时检出阶梯查询点落在起点之前")
    return rate[position]


def dominance_between(
    first: Mapping[str, Any],
    second: Mapping[str, Any],
) -> dict[str, Any]:
    """共同首次告警子向量支配：全精度比较，不设容差、不计胜出项、不加权。"""
    strict = False
    path_ok = bool((first["path_dr_by_k"] >= second["path_dr_by_k"]).all())
    terminal_ok = bool((first["terminal_dr_by_k"] >= second["terminal_dr_by_k"]).all())
    strict = strict or bool((first["path_dr_by_k"] > second["path_dr_by_k"]).any())
    strict = strict or bool((first["terminal_dr_by_k"] > second["terminal_dr_by_k"]).any())
    unalerted_ok = True
    timely_ok = True
    for budget_key in first["budget_keys"]:
        if first["unalerted"][budget_key] > second["unalerted"][budget_key]:
            unalerted_ok = False
        if first["unalerted"][budget_key] < second["unalerted"][budget_key]:
            strict = True
        axis = np.union1d(first["timely_axis"][budget_key], second["timely_axis"][budget_key])
        left = step_evaluate(first["timely_axis"][budget_key], first["timely_rate"][budget_key], axis)
        right = step_evaluate(second["timely_axis"][budget_key], second["timely_rate"][budget_key], axis)
        if not bool((left >= right).all()):
            timely_ok = False
        if bool((left > right).any()):
            strict = True
    dominates = path_ok and terminal_ok and unalerted_ok and timely_ok and strict
    return {
        "dominates": bool(dominates),
        "path_detection_rate_never_lower": path_ok,
        "terminal_detection_rate_never_lower": terminal_ok,
        "positive_unalerted_rate_never_higher": unalerted_ok,
        "timely_detection_rate_never_lower": timely_ok,
        "strictly_better_somewhere": bool(strict),
    }


def load_method_vectors(output_root: Path, method_key: str) -> tuple[dict[str, Any], dict[str, Any]]:
    json_name, npz_name, _ = method_artifact_names(method_key)
    aggregate = load_json(output_root / json_name)
    with np.load(output_root / npz_name, allow_pickle=False) as payload:
        vectors = {name: payload[name] for name in payload.files}
    return aggregate, vectors


def stage_common_budget_projection(context: dict[str, Any]) -> None:
    config = context["config"]
    output_root = context["output_root"]
    input_receipt = ensure_input_receipt(context)
    unreachable = dict(context.get("unreachable", {}))
    write_status(
        output_root,
        "running",
        "common_budget_projection",
        "投影全部整数预算、生成六档及时曲线与支配矩阵",
        None,
        unreachable,
    )
    load_numeric_dependencies()
    available = [key for key in METHOD_KEYS if key not in unreachable]
    if not available:
        raise SystemExit("没有任何可达方法，无法生成共同预算包络")

    path_vectors: dict[str, Any] = {}
    terminal_vectors: dict[str, Any] = {}
    timely_vectors: dict[str, Any] = {}
    method_results: dict[str, Any] = {}
    score_sources: dict[str, Any] = {}
    comparison: dict[str, dict[str, Any]] = {}
    budget_keys = [f"k_{value}" for value in COMMON_INTEGER_BUDGETS]

    for method_key in available:
        aggregate, vectors = load_method_vectors(output_root, method_key)
        index = vectors["last_reachable_index_by_integer_budget"].astype(np.int64, copy=False)
        for name in PATH_CURVE_FIELDS:
            path_vectors[f"{method_key}__{name}"] = vectors[name]
        for name in TERMINAL_CURVE_FIELDS:
            terminal_vectors[f"{method_key}__{name}"] = vectors[name]
        axis_map: dict[str, Any] = {}
        rate_map: dict[str, Any] = {}
        for budget_key in budget_keys:
            axis = vectors[f"first_alert__{budget_key}__exposure_index"]
            rate = vectors[f"first_alert__{budget_key}__timely_detection_rate"]
            timely_vectors[f"{method_key}__{budget_key}__exposure_index"] = axis
            timely_vectors[f"{method_key}__{budget_key}__timely_detection_rate"] = rate
            axis_map[budget_key] = axis
            rate_map[budget_key] = rate
        comparison[method_key] = {
            "path_dr_by_k": vectors["path_detection_rate"][index],
            "terminal_dr_by_k": vectors["terminal_detection_rate"][index],
            "unalerted": {
                budget_key: float(
                    aggregate["first_alert"]["budgets"][budget_key]["positive_unalerted_rate"]
                )
                for budget_key in budget_keys
            },
            "timely_axis": axis_map,
            "timely_rate": rate_map,
            "budget_keys": budget_keys,
        }
        method_results[method_key] = {
            "display_name": aggregate["display_name"],
            "online_score": aggregate["online_score"],
            "terminal_score": aggregate["terminal_score"],
            "power_mean_p": aggregate["power_mean_p"],
            "curve_point_count": aggregate["curve_point_count"],
            "path_max_equals_terminal": aggregate["path_max_equals_terminal"],
            "budget_readouts": aggregate["budget_readouts"],
            "first_alert": aggregate["first_alert"],
        }
        score_sources[method_key] = aggregate["score_source"]

    dominance = {
        first: {
            second: dominance_between(comparison[first], comparison[second])
            for second in available
            if second != first
        }
        for first in available
    }

    curve_artifact = atomic_npz(output_root / "complete-path-budget-curves.npz", path_vectors)
    atomic_json(
        output_root / "complete-path-budget-curves-receipt.json",
        {
            "schema_version": PATH_CURVE_SCHEMA,
            "run_id": RUN_ID,
            "artifact": curve_artifact,
            "methods": available,
            "fields": list(PATH_CURVE_FIELDS),
            "field_shapes": {
                name: list(np.shape(value)) for name, value in path_vectors.items()
            },
            "field_dtypes": {name: str(value.dtype) for name, value in path_vectors.items()},
            "positive_entity_denominator": N_POSITIVE_ENTITY,
            "negative_entity_denominator": N_NEGATIVE_ENTITY,
            "threshold_semantics": "online_score_greater_equal_threshold",
            "threshold_source": "all_entity_path_max_descending_unique",
            "zero_false_positive_boundary_included": True,
            "complete_tie_groups_never_split": True,
            "interpolation": False,
            "integer_budget_axis": {
                "minimum": 0,
                "maximum": N_NEGATIVE_ENTITY,
                "field": "last_reachable_index_by_integer_budget",
                "selection_rule": "last_reachable_threshold_with_path_fp_not_exceeding_k",
            },
        },
    )
    terminal_artifact = atomic_npz(
        output_root / "terminal-at-path-threshold-curves.npz", terminal_vectors
    )
    atomic_json(
        output_root / "terminal-at-path-threshold-curves-receipt.json",
        {
            "schema_version": TERMINAL_CURVE_SCHEMA,
            "run_id": RUN_ID,
            "artifact": terminal_artifact,
            "methods": available,
            "fields": list(TERMINAL_CURVE_FIELDS),
            "field_shapes": {
                name: list(np.shape(value)) for name, value in terminal_vectors.items()
            },
            "field_dtypes": {name: str(value.dtype) for name, value in terminal_vectors.items()},
            "threshold_correspondence": (
                "与 complete-path-budget-curves.npz 的同方法 threshold 逐位一一对应"
            ),
            "path_curve_artifact_sha256": curve_artifact["sha256"],
            "is_independent_terminal_budget_axis": False,
            "terminal_fpr_must_not_be_read_as_path_budget": True,
        },
    )
    timely_artifact = atomic_npz(output_root / "first-alert-timing-curves.npz", timely_vectors)
    atomic_json(
        output_root / "first-alert-timing-curves-receipt.json",
        {
            "schema_version": TIMELY_SCHEMA,
            "run_id": RUN_ID,
            "artifact": timely_artifact,
            "methods": available,
            "axis": "exposure_index",
            "exposure_index_base": 1,
            "curve_encoding": "right_continuous_exact_first_crossing_breakpoints",
            "timely_detection_denominator": N_POSITIVE_ENTITY,
            "budget_to_threshold": {
                method_key: {
                    budget_key: method_results[method_key]["budget_readouts"][budget_key][
                        "actual_reachable_point"
                    ]["threshold"]
                    for budget_key in budget_keys
                }
                for method_key in available
            },
            "field_shapes": {
                name: list(np.shape(value)) for name, value in timely_vectors.items()
            },
            "field_dtypes": {name: str(value.dtype) for name, value in timely_vectors.items()},
            "time_delay_available": False,
            "time_delay_unavailable_reason": config["evaluation"]["time_delay_unavailable_reason"],
            "persisted_per_entity_first_alert": False,
        },
    )
    atomic_json(
        output_root / "score-source-receipt.json",
        {
            "schema_version": "ch3-common-first-alert-score-source-v1",
            "run_id": RUN_ID,
            "methods": score_sources,
            "training_runs": 0,
            "hyperparameter_selection_runs": 0,
            "target_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "per_entity_first_alert_persisted": False,
        },
    )

    envelope_closed = not unreachable
    if not envelope_closed:
        verdict = "共同五方法包络未闭合"
        verdict_detail = "只报告已完成方法的描述性曲线，不对全容量 MLP O11 作存废裁决"
    else:
        dominators = [
            key
            for key in available
            if key != "full_mlp_o11" and dominance[key]["full_mlp_o11"]["dominates"]
        ]
        if dominators:
            verdict = "当前全容量 MLP O11 不支持替代"
            verdict_detail = "被强基线在共同首次告警子向量上机械支配：" + "、".join(dominators)
        else:
            verdict = "全容量 MLP O11 在目标年共同首次告警子向量上保持非支配"
            verdict_detail = (
                "非支配只覆盖共同首次告警子向量，不覆盖逐流 AP、实体 AP、源年证据、"
                "灾备与工程公平性，也不自动完成第三章统一资格 Goal"
            )
    aggregate_results = {
        "schema_version": RESULT_SCHEMA,
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "complete": envelope_closed,
        "dataset": "LSPR24",
        "evaluation_role": "已访问目标年的描述性共同首次告警 FP 预算包络",
        "evidence_ceiling": config["evidence_ceiling"],
        "independent_test": False,
        "formal_paper_evidence": False,
        "target_previously_accessed": True,
        "shared_identity": input_receipt["shared_identity"],
        "common_integer_budgets": {
            f"k_{value}": {"nominal_budget": nominal, "common_integer_budget": value}
            for nominal, value in zip(NOMINAL_BUDGETS, COMMON_INTEGER_BUDGETS, strict=True)
        },
        "method_count": len(available),
        "methods": method_results,
        "unreachable_methods": unreachable,
        "dominance_matrix": dominance,
        "dominance_definition": (
            "对全部整数 k 的 path_dr 与同阈值 terminal_dr 均不低于，六档正实体未告警率均不高于，"
            "六档及时检出阶梯在断点并集上处处不低于，且至少一处严格更好"
        ),
        "synthetic_best_of_baselines_forbidden": True,
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "goal_completion_not_implied": True,
        "training_runs": 0,
        "hyperparameter_selection_runs": 0,
        "artifact_policy": config["artifact_policy"],
    }
    atomic_json(output_root / "aggregate-results.json", aggregate_results)
    log(f"共同预算投影完成，裁决：{verdict}")


# ----------------------------------------------------------------------------
# 阶段六：资源、跟踪、状态与清单
# ----------------------------------------------------------------------------


def write_stage_resource(context: dict[str, Any], stage: str, started: float) -> None:
    output_root = context["output_root"]
    atomic_json(
        output_root / f"stage-receipts/{stage}.json",
        {
            "schema_version": "ch3-common-first-alert-stage-resource-v1",
            "run_id": RUN_ID,
            "stage": stage,
            "wall_seconds": time.time() - started,
            "process_peak_rss_mib": process_peak_rss_mib(),
            "cgroup_current_bytes": read_cgroup_number("memory.current"),
            "cgroup_peak_bytes": read_cgroup_number("memory.peak"),
            "disk_free_bytes": shutil.disk_usage(context["project_root"]).free,
            "completed_at_unix": time.time(),
        },
    )


def collect_resource_receipt(context: dict[str, Any], admission: Mapping[str, Any]) -> dict[str, Any]:
    output_root = context["output_root"]
    stages: dict[str, Any] = {}
    stage_root = output_root / "stage-receipts"
    if stage_root.is_dir():
        for path in sorted(stage_root.glob("*.json")):
            stages[path.stem] = load_json(path)
    gpu_receipts: dict[str, Any] = {}
    for method_key in ("xgb_cpa_elp_c11", "full_mlp_o11"):
        json_name, _, _ = method_artifact_names(method_key)
        path = output_root / json_name
        if path.is_file():
            source = load_json(path).get("score_source", {})
            gpu_receipts[method_key] = {
                "peak_gpu_reserved_mib": source.get("peak_gpu_reserved_mib"),
                "single_logical_score_seconds": source.get("single_logical_score_seconds"),
                "single_logical_inference_seconds": source.get("single_logical_inference_seconds"),
            }
    return {
        "schema_version": "ch3-common-first-alert-resource-v1",
        "run_id": RUN_ID,
        "authorized_server": context["config"]["resource_contract"]["authorized_server"],
        "hostname": platform.node(),
        "admission": dict(admission),
        "stages": stages,
        "gpu": gpu_receipts,
        "process_peak_rss_mib": process_peak_rss_mib(),
        "cgroup_current_bytes_at_receipt": read_cgroup_number("memory.current"),
        "cgroup_peak_bytes_at_receipt": read_cgroup_number("memory.peak"),
        "disk_free_bytes_at_receipt": shutil.disk_usage(context["project_root"]).free,
        "wall_clock_limit": None,
        "gpu_hour_limit": None,
        "concurrency_contamination_possible": bool(
            admission.get("concurrency_contamination_possible", True)
        ),
        "fair_efficiency_evidence": False,
        "failed_stage": None,
        "measurement_note": (
            "控制组读数可能包含并发任务；本收据只作资源安全上界，不作公平效率证据"
        ),
    }


def publish_tracking(context: dict[str, Any]) -> dict[str, Any]:
    config = context["config"]
    output_root = context["output_root"]
    tracking = config["tracking"]
    aggregate = load_json(output_root / "aggregate-results.json")
    import swanlab

    swanlab.init(
        workspace=tracking["workspace"],
        project=tracking["project"],
        name=DISPLAY_NAME,
        config={
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "dataset": "LSPR24",
            "method_count": aggregate["method_count"],
            "verdict": aggregate["verdict"],
            "tool_sha256": context["tool_sha256"],
            "config_sha256": context["config_sha256"],
        },
        mode=tracking["mode"],
        logdir=str(output_root / "swanlog"),
    )
    log_values: dict[str, float] = {}
    for method_key, payload in aggregate["methods"].items():
        for budget_key, readout in payload["budget_readouts"].items():
            point = readout["actual_reachable_point"]
            log_values[f"path_dr/{method_key}_{budget_key}"] = point["path_detection_rate"]
            log_values[f"terminal_dr/{method_key}_{budget_key}"] = point["terminal_detection_rate"]
            log_values[f"actual_fpr/{method_key}_{budget_key}"] = point["path_false_positive_rate"]
        for budget_key, summary in payload["first_alert"]["budgets"].items():
            log_values[f"unalerted/{method_key}_{budget_key}"] = summary["positive_unalerted_rate"]
            log_values[f"first_alert_fpr/{method_key}_{budget_key}"] = summary[
                "actual_first_alert_false_positive_rate"
            ]
    swanlab.log(log_values, step=0)
    swanlab.finish()
    receipt = {
        "schema_version": "ch3-common-first-alert-swanlab-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "workspace": tracking["workspace"],
        "project": tracking["project"],
        "mode": tracking["mode"],
        "aggregate_only": True,
        "logged_scalar_count": len(log_values),
        "per_flow_scores_logged": False,
        "per_entity_scores_logged": False,
        "per_entity_first_alert_logged": False,
        "completed": True,
    }
    atomic_json(output_root / "swanlab-receipt.json", receipt)
    return receipt


def assert_no_forbidden_artifacts(output_root: Path) -> list[str]:
    names: list[str] = []
    for path in sorted(output_root.rglob("*")):
        if not path.is_file():
            continue
        relative = str(path.relative_to(output_root))
        if relative.startswith("swanlog/"):
            continue
        names.append(relative)
        lowered = relative.lower()
        if any(fragment in lowered for fragment in FORBIDDEN_NAME_FRAGMENTS):
            raise SystemExit(f"发现禁止持久化的分数、映射、派生矩阵或模型制品：{relative}")
        if lowered.endswith(".partial") or ".partial." in lowered:
            raise SystemExit(f"输出根存在未发布临时文件，拒绝宣称完成：{relative}")
    return names


def validate_existing_manifest(output_root: Path, context: Mapping[str, Any]) -> dict[str, Any]:
    manifest = load_json(output_root / "manifest.json")
    if (
        manifest.get("schema_version") != MANIFEST_SCHEMA
        or manifest.get("run_id") != RUN_ID
        or manifest.get("tool_sha256") != context["tool_sha256"]
        or manifest.get("config_sha256") != context["config_sha256"]
        or manifest.get("forbidden_artifacts_absent") is not True
        or manifest.get("per_flow_scores_persisted") is not False
        or manifest.get("per_entity_scores_persisted") is not False
        or manifest.get("per_entity_first_alert_persisted") is not False
        or manifest.get("entity_mapping_persisted") is not False
    ):
        raise SystemExit("已有最终清单的身份或零持久化合同不符，拒绝覆盖")
    for name, item in manifest.get("files", {}).items():
        path = output_root / name
        if (
            not path.is_file()
            or path.stat().st_size != item.get("bytes")
            or sha256_file(path) != item.get("sha256")
        ):
            raise SystemExit(f"已有最终制品与清单不符：{name}")
    return manifest


def stage_finalize(context: dict[str, Any]) -> None:
    output_root = context["output_root"]
    if (output_root / "manifest.json").is_file():
        if not context["resume"]:
            raise SystemExit("最终清单已存在；仅允许用 --resume 幂等核验，禁止重复上报跟踪运行")
        manifest = validate_existing_manifest(output_root, context)
        print(
            f"RUN_ALREADY_COMPLETE run={RUN_ID} verdict={manifest.get('verdict')}",
            flush=True,
        )
        return
    admission_path = context["admission_receipt"]
    if admission_path is None:
        raise SystemExit("finalize 阶段必须提供 --admission-receipt（启动器写出的资源准入读数）")
    if not admission_path.is_file():
        raise SystemExit(f"资源准入读数缺失：{admission_path}")
    admission = load_json(admission_path)
    for name in (
        "aggregate-results.json",
        "complete-path-budget-curves.npz",
        "complete-path-budget-curves-receipt.json",
        "terminal-at-path-threshold-curves.npz",
        "terminal-at-path-threshold-curves-receipt.json",
        "first-alert-timing-curves.npz",
        "first-alert-timing-curves-receipt.json",
        "input-validation-receipt.json",
        "score-source-receipt.json",
        "config.json",
    ):
        path = output_root / name
        if not path.is_file() or path.stat().st_size <= 0:
            raise SystemExit(f"前置阶段制品缺失或为空，禁止发布：{name}")
    run_log = output_root / "run.log"
    if not run_log.is_file() or run_log.stat().st_size <= 0:
        raise SystemExit("run.log 尚未封口或为空，禁止发布最终清单")

    atomic_json(output_root / "resource-receipt.json", collect_resource_receipt(context, admission))
    publish_tracking(context)
    aggregate = load_json(output_root / "aggregate-results.json")
    unreachable = aggregate.get("unreachable_methods", {})
    state = "complete" if aggregate.get("complete") else "incomplete"
    detail = (
        "五方法共同首次告警包络已完整发布"
        if aggregate.get("complete")
        else "存在不可达方法，只发布已完成方法的描述性曲线"
    )
    write_status(output_root, state, "complete", detail, 0, unreachable)

    names = assert_no_forbidden_artifacts(output_root)
    files = {name: artifact_receipt(output_root / name) for name in names if name != "manifest.json"}
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "complete": bool(aggregate.get("complete")),
        "verdict": aggregate.get("verdict"),
        "tool_sha256": context["tool_sha256"],
        "config_sha256": context["config_sha256"],
        "method_count": aggregate.get("method_count"),
        "unreachable_methods": unreachable,
        "training_runs": 0,
        "hyperparameter_selection_runs": 0,
        "per_flow_scores_persisted": False,
        "per_entity_scores_persisted": False,
        "per_entity_first_alert_persisted": False,
        "entity_mapping_persisted": False,
        "derived_matrices_persisted": False,
        "models_or_checkpoints_persisted": False,
        "forbidden_artifacts_absent": True,
        "files": files,
    }
    atomic_json(output_root / "manifest.json", manifest)
    for name, item in files.items():
        path = output_root / name
        if path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise SystemExit(f"最终制品与清单不符：{name}")
    print(f"COMMON_FIRST_ALERT_ENVELOPE_COMPLETE run={RUN_ID} verdict={aggregate.get('verdict')}", flush=True)


# ----------------------------------------------------------------------------
# 阶段调度
# ----------------------------------------------------------------------------


STAGE_FUNCTIONS = {
    "validate_shared_identity": stage_validate_shared_identity,
    "published_neural_aggregate": stage_published_neural_aggregate,
    "xgb_rescore_and_aggregate": stage_xgb_rescore_and_aggregate,
    "mlp_infer_and_aggregate": stage_mlp_infer_and_aggregate,
    "common_budget_projection": stage_common_budget_projection,
    "finalize": stage_finalize,
}


def run_stage(context: dict[str, Any], stage: str) -> None:
    log(f"阶段开始：{stage}")
    started = time.time()
    STAGE_FUNCTIONS[stage](context)
    if stage != "finalize":
        write_stage_resource(context, stage, started)
    log(f"阶段结束：{stage}，用时 {time.time() - started:.1f}s")


def execute(context: dict[str, Any], stage: str) -> None:
    output_root = context["output_root"]
    output_root.mkdir(parents=True, exist_ok=True)
    if not (output_root / "status.json").is_file():
        write_status(output_root, "pending", stage, "运行目录已建立，尚未进入首个阶段", None)
    elif context["resume"] and stage != "finalize":
        bump_recovery_count(output_root)
    if stage == "compute":
        for name in STAGES[:-1]:
            run_stage(context, name)
        return
    run_stage(context, stage)


def main() -> int:
    args = parse_args()
    if not args.config.is_file():
        raise SystemExit(f"配置文件缺失：{args.config}")
    config_path = args.config.resolve()
    config = load_json(config_path)
    validate_config(config)
    if args.validate_config:
        print("CONFIG_VALID", flush=True)
        return 0
    if args.stage is None:
        raise SystemExit("必须指定 --validate-config 或 --stage（单阶段名或 compute）")

    load_numeric_dependencies()
    project_root, output_root = resolve_runtime_paths(config, args.project_root)
    context: dict[str, Any] = {
        "config": config,
        "config_path": config_path,
        "config_sha256": sha256_file(config_path),
        "tool_sha256": sha256_file(Path(__file__).resolve()),
        "project_root": project_root,
        "output_root": output_root,
        "resume": bool(args.resume),
        "admission_receipt": args.admission_receipt.resolve() if args.admission_receipt else None,
        "shared": None,
        "input_receipt": None,
        "unreachable": {},
    }
    try:
        execute(context, args.stage)
    except BaseException as error:  # noqa: BLE001 - 失败必须保留状态与原退出码
        output_root.mkdir(parents=True, exist_ok=True)
        write_status(output_root, "failed", args.stage, f"{type(error).__name__}: {error}"[:1000], 1)
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
