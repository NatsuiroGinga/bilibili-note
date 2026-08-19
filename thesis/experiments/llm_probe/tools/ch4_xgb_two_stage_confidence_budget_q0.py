#!/usr/bin/env python3
"""冻结 XGBoost 基座上的双段先导置信预算告警零训练 Q0。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch4_xgb_pbc_q0 as base  # noqa: E402
from ch3_xgb_cpa_elp_eval_continuation import (  # noqa: E402
    CACHE,
    CONTINUATION_RUN_ID,
    EXPECTED_XGB_PARAMS,
    PARENT_RUN_ID,
    atomic_json,
    gpu_guard,
    predict_rows,
    sha256_file,
    validate_parent_inputs,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "ch4-xgb-two-stage-confidence-budget-q0-seed42-v1"
N_FLOW_23 = 16_353_511
N_ENTITY_23 = 150_680
N_POS_ENTITY_23 = 239
N_FLOW_24 = 20_227_356
N_ENTITY_24 = 47_115
N_FOLD = 3
N_TREE = 800
METHODS = (
    "source_frozen",
    "selection_empirical",
    "two_stage_confirmed",
    "evaluation_oracle",
)
METHOD_DISPLAY_NAMES = {
    "source_frozen": "源年度冻结阈值",
    "selection_empirical": "选择段经验阈值",
    "two_stage_confirmed": "双段先导置信预算阈值",
    "evaluation_oracle": "评价段标签阈值上界（仅诊断）",
}
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def ndarray_sha256(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode("ascii"))
    digest.update(json.dumps(list(contiguous.shape), separators=(",", ":")).encode("ascii"))
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="双段先导置信预算告警零训练 Q0")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/ch4-xgb-two-stage-confidence-budget-q0-seed42-v1.json",
    )
    parser.add_argument(
        "--parent-run-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / PARENT_RUN_ID,
    )
    parser.add_argument(
        "--parent-eval-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / CONTINUATION_RUN_ID,
    )
    parser.add_argument(
        "--parent-config",
        type=Path,
        default=ROOT / "configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json",
    )
    parser.add_argument(
        "--parent-recovery-proof",
        type=Path,
        default=(
            ROOT
            / "runs/recovery"
            / f"{PARENT_RUN_ID}-for-{RUN_ID}-v1"
            / base.PARENT_RECOVERY_PROOF_FILENAME
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "runs/candidates" / RUN_ID,
    )
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


def validate_config(config: dict[str, Any]) -> None:
    expected_exact = {
        "schema_version": "ch4-xgb-two-stage-confidence-budget-q0-v1",
        "run_id": RUN_ID,
        "display_name": "双段先导置信预算告警 Q0",
        "seed": 42,
        "screening_only": True,
        "formal": False,
        "formal_paper_evidence": False,
        "independent_test": False,
        "zero_training": True,
        "parent_run_id": PARENT_RUN_ID,
        "parent_eval_run_id": CONTINUATION_RUN_ID,
        "parent_recovery_proof": {
            "schema_version": base.PARENT_RECOVERY_PROOF_SCHEMA_VERSION,
            "requires_parent_incomplete": True,
            "original_manifest_expected": False,
        },
        "base_view": "semantic168",
        "power_mean_p": 1.0,
        "target_score_calls": 1,
        "segment_time_fractions": {
            "selection_end": 0.1,
            "confirmation_end": 0.2,
        },
        "candidate_fpr_grid": [0.001, 0.002, 0.005, 0.01, 0.02, 0.04, 0.08],
        "entity_fpr_budgets": [0.01, 0.02, 0.04],
        "familywise_alpha": 0.05,
        "multiple_candidate_correction": "bonferroni_within_budget",
        "fpr_upper_bound": "clopper_pearson_one_sided_exact",
        "alert_statistic": "max_running_entity_mean",
        "artifact_policy": {
            "persist_aggregate_json": True,
            "persist_status_log_manifest_resource": True,
            "persist_per_flow_scores": False,
            "persist_per_entity_scores": False,
            "persist_derived_matrices": False,
            "persist_label_details": False,
            "persist_new_models": False,
        },
    }
    for key, expected in expected_exact.items():
        if config.get(key) != expected:
            raise SystemExit(f"双段 Q0 配置字段不符：{key}")
    expected_provenance = {
        "0.01": "预注册保守敏感性，不是安全标准",
        "0.02": "预注册保守敏感性，不是安全标准",
        "0.04": "Gehri 同源经验工作点，不是安全标准",
    }
    if config.get("budget_provenance") != expected_provenance:
        raise SystemExit("预算来源说明与冻结合同不符")
    for key in (
        "time_unit_per_second",
        "predict_batch",
        "sequence_batch",
        "gpu_need_gib",
        "gpu_floor_gib",
        "estimated_peak_host_gib",
    ):
        if float(config.get(key, 0)) <= 0:
            raise SystemExit(f"双段 Q0 数值配置必须为正：{key}")
    if config.get("expected_time_span_hours") != [140.0, 144.0]:
        raise SystemExit("目标时间跨度门与冻结数据身份不符")
    if config.get("tracking") != {
        "workspace": "mortiswang",
        "project": "ns3-rwkv-lspr24",
        "mode": "online",
        "aggregate_only": True,
    }:
        raise SystemExit("SwanLab 目的地或聚合模式与授权合同不符")


def validate_inputs(args: argparse.Namespace, config: dict[str, Any]) -> dict[str, Any]:
    if args.out.resolve().name != RUN_ID:
        raise SystemExit(f"输出运行身份必须为 {RUN_ID}")
    parent_args = argparse.Namespace(
        parent_run_root=args.parent_run_root,
        parent_config=args.parent_config,
        out=args.out,
        bootstrap=1,
        predict_batch=int(config["predict_batch"]),
        sequence_batch=int(config["sequence_batch"]),
    )
    parent = validate_parent_inputs(parent_args)
    if parent["selected_adapter"] != "semantic168":
        raise SystemExit("父运行适配器不是 semantic168")
    if float(parent["p_selection"]["semantic168"]) != 1.0:
        raise SystemExit("父运行 semantic168 的 p 不是 1.0")

    parent_eval_root = args.parent_eval_root.resolve()
    if parent_eval_root.name != CONTINUATION_RUN_ID:
        raise SystemExit(f"父评价身份不符：{parent_eval_root.name}")
    expected_eval = {
        "xgb_cpa_elp_results.json": base.EXPECTED_PARENT_RESULT_SHA256,
        "manifest.json": base.EXPECTED_PARENT_EVAL_MANIFEST_SHA256,
    }
    eval_hashes: dict[str, str] = {}
    for name, expected in expected_eval.items():
        path = parent_eval_root / name
        if not path.is_file():
            raise SystemExit(f"父评价制品缺失：{path}")
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(f"父评价制品摘要不符：{name}")
        eval_hashes[name] = actual
    status = load_json(parent_eval_root / "status.json")
    if (
        status.get("state") != "finished"
        or status.get("stage") != "complete"
        or status.get("exit_code") != 0
    ):
        raise SystemExit("父评价未处于 finished/complete/exit=0")
    parent_result = load_json(parent_eval_root / "xgb_cpa_elp_results.json")
    if parent_result.get("isolation", {}).get("target_score_calls") != 2:
        raise SystemExit("父评价没有两次目标预测收据")
    if parent_result.get("isolation", {}).get("target_scores_persisted") is not False:
        raise SystemExit("父评价逐流分数持久化声明异常")

    proof_path = args.parent_recovery_proof.resolve()
    if proof_path.name != base.PARENT_RECOVERY_PROOF_FILENAME or not proof_path.is_file():
        raise SystemExit(f"父恢复证明缺失或文件名不符：{proof_path}")
    if args.parent_run_root.resolve() in proof_path.parents:
        raise SystemExit("父恢复证明不得位于父运行目录内")
    proof = load_json(proof_path)
    if proof.get("schema_version") != base.PARENT_RECOVERY_PROOF_SCHEMA_VERSION:
        raise SystemExit("父恢复证明模式版本不符")
    if proof.get("parent_run_id") != PARENT_RUN_ID:
        raise SystemExit("父恢复证明运行身份不符")
    if Path(str(proof.get("parent_run_root", ""))).resolve() != args.parent_run_root.resolve():
        raise SystemExit("父恢复证明中的父运行路径不符")
    if proof.get("does_not_assert_parent_completion") is not True:
        raise SystemExit("父恢复证明错误声明父运行已完成")
    parent_state = proof.get("parent_state", {})
    historical_status = parent_state.get("historical_status", {})
    if (
        parent_state.get("complete") is not False
        or historical_status.get("state") != "running"
        or historical_status.get("stage") != "source_selection"
        or historical_status.get("exit_code") is not None
        or parent_state.get("missing_completion_artifacts")
        != ["xgb_cpa_elp_results.json", "manifest.json"]
    ):
        raise SystemExit("父恢复证明未保留已核验的中断事实")
    parent_status_path = args.parent_run_root.resolve() / "status.json"
    if (
        not parent_status_path.is_file()
        or historical_status.get("filename") != parent_status_path.name
        or historical_status.get("sha256") != sha256_file(parent_status_path)
        or historical_status.get("bytes") != parent_status_path.stat().st_size
    ):
        raise SystemExit("父实际状态与恢复证明不符")
    for name in parent_state["missing_completion_artifacts"]:
        if (args.parent_run_root.resolve() / name).exists():
            raise SystemExit(f"父运行出现证明声明缺失的完成制品：{name}")
    proof_artifacts = proof.get("artifacts", {})
    artifact_hashes: dict[str, str] = {}
    for name in base.PARENT_RECOVERY_ARTIFACTS:
        path = args.parent_run_root.resolve() / name
        receipt = proof_artifacts.get(name, {})
        if not path.is_file() or not receipt:
            raise SystemExit(f"父恢复证明或实际制品缺失：{name}")
        actual = sha256_file(path)
        if actual != receipt.get("sha256") or path.stat().st_size != receipt.get("bytes"):
            raise SystemExit(f"父制品与恢复证明不符：{name}")
        if name.startswith("model_") and receipt.get("num_boosted_rounds") != N_TREE:
            raise SystemExit(f"父恢复证明中的模型树数不是 {N_TREE}：{name}")
        artifact_hashes[name] = actual
    effective_summary = proof.get("effective_config_receipts", {})
    if (
        effective_summary.get("receipt_count") != 11
        or effective_summary.get("all_passed") is not True
        or set(effective_summary.get("required_dependency_tags", []))
        != base.PARENT_RECOVERY_EFFECTIVE_TAGS
    ):
        raise SystemExit("父恢复证明中的有效配置收据摘要不符")

    for name in (
        "X23",
        "y23",
        "I23",
        "M23",
        "ent23",
        "t23_flow",
        "X24",
        "y24",
        "I24",
        "M24",
        "s24",
        "d24",
        "t24",
    ):
        path = CACHE / f"{name}.npy"
        if not path.is_file() or path.stat().st_size <= 0:
            raise SystemExit(f"共享缓存缺失或为空：{path}")

    parent["parent_eval_root"] = str(parent_eval_root)
    parent["parent_eval_sha256"] = eval_hashes
    parent["parent_recovery_proof_path"] = str(proof_path)
    parent["parent_recovery_proof_sha256"] = sha256_file(proof_path)
    parent["recovery_artifact_sha256"] = artifact_hashes
    return parent


def segment_entities(
    entity: np.ndarray,
    time_values: np.ndarray,
    time_min: float,
    time_max: float,
) -> dict[str, Any]:
    first_time = np.full(N_ENTITY_24, math.inf, np.float64)
    last_time = np.full(N_ENTITY_24, -math.inf, np.float64)
    np.minimum.at(first_time, entity, time_values)
    np.maximum.at(last_time, entity, time_values)
    selection_end = time_min + 0.1 * (time_max - time_min)
    confirmation_end = time_min + 0.2 * (time_max - time_min)
    selection = last_time <= selection_end
    confirmation = (first_time > selection_end) & (last_time <= confirmation_end)
    evaluation = first_time > confirmation_end
    if np.any(selection & confirmation) or np.any(selection & evaluation) or np.any(
        confirmation & evaluation
    ):
        raise SystemExit("选择、确认、评价实体集合发生交叉")
    boundary = ~(selection | confirmation | evaluation)
    return {
        "selection_end": selection_end,
        "confirmation_end": confirmation_end,
        "selection": selection,
        "confirmation": confirmation,
        "evaluation": evaluation,
        "boundary": boundary,
        "first_time": first_time,
        "last_time": last_time,
    }


def load_segment_entity_labels(
    entity: np.ndarray,
    segment: np.ndarray,
    tag: str,
) -> tuple[np.ndarray, np.ndarray, int]:
    entity_ids = np.flatnonzero(segment)
    if len(entity_ids) == 0:
        raise SystemExit(f"{tag}没有实体")
    row_ids = np.flatnonzero(segment[entity])
    label_file = np.load(CACHE / "y24.npy", mmap_mode="r")
    if label_file.shape != (N_FLOW_24,):
        raise SystemExit("LSPR24 标签长度不符")
    row_labels = np.asarray(label_file[row_ids], np.uint8)
    del label_file
    if np.any((row_labels != 0) & (row_labels != 1)):
        raise SystemExit(f"{tag}标签不是二元值")
    local_entity = np.searchsorted(entity_ids, entity[row_ids])
    labels = np.zeros(len(entity_ids), np.uint8)
    np.maximum.at(labels, local_entity, row_labels)
    del row_ids, row_labels, local_entity
    return entity_ids, labels, int(segment[entity].sum())


def log_binomial_cdf(k: int, n: int, probability: float) -> float:
    if k < 0:
        return -math.inf
    if k >= n or probability <= 0.0:
        return 0.0
    if probability >= 1.0:
        return -math.inf
    log_p = math.log(probability)
    log_q = math.log1p(-probability)
    terms = [
        math.lgamma(n + 1)
        - math.lgamma(index + 1)
        - math.lgamma(n - index + 1)
        + index * log_p
        + (n - index) * log_q
        for index in range(k + 1)
    ]
    maximum = max(terms)
    return maximum + math.log(math.fsum(math.exp(term - maximum) for term in terms))


def clopper_pearson_upper(k: int, n: int, alpha: float) -> float | None:
    if n <= 0 or k < 0 or k > n or not 0.0 < alpha < 1.0:
        return None
    if k == n:
        return 1.0
    if k == 0:
        return -math.expm1(math.log(alpha) / n)
    target = math.log(alpha)
    lower = k / n
    upper = 1.0
    for _ in range(100):
        middle = (lower + upper) / 2.0
        if log_binomial_cdf(k, n, middle) > target:
            lower = middle
        else:
            upper = middle
    value = (lower + upper) / 2.0
    return value if math.isfinite(value) else None


def build_candidates(
    selection_alert_scores: np.ndarray,
    selection_labels: np.ndarray,
    candidate_grid: list[float],
) -> list[dict[str, Any]]:
    negative_scores = selection_alert_scores[selection_labels == 0]
    if len(negative_scores) == 0:
        raise SystemExit("选择段没有良性实体，无法生成候选阈值")
    return [
        {
            "candidate_fpr": rate,
            **base.conservative_threshold(negative_scores, rate),
        }
        for rate in candidate_grid
    ]


def confirm_candidates_for_budget(
    candidates: list[dict[str, Any]],
    confirmation_alert_scores: np.ndarray,
    confirmation_labels: np.ndarray,
    source_receipt: dict[str, Any],
    budget: float,
    familywise_alpha: float,
) -> dict[str, Any]:
    negative_scores = confirmation_alert_scores[confirmation_labels == 0]
    negative_count = int(len(negative_scores))
    alpha_piece = familywise_alpha / len(candidates)
    zero_error_upper = clopper_pearson_upper(0, negative_count, alpha_piece)
    insufficient = zero_error_upper is None or zero_error_upper > budget
    checks: list[dict[str, Any]] = []
    upper_bound_failed = False
    for candidate in candidates:
        threshold = float(candidate["threshold"])
        false_positive = int((negative_scores >= threshold).sum())
        upper = clopper_pearson_upper(false_positive, negative_count, alpha_piece)
        if upper is None:
            upper_bound_failed = True
        checks.append(
            {
                "candidate_fpr": float(candidate["candidate_fpr"]),
                "threshold": threshold,
                "confirmation_negative_entities": negative_count,
                "confirmation_false_positive_entities": false_positive,
                "confirmation_empirical_fpr": (
                    false_positive / negative_count if negative_count else None
                ),
                "bonferroni_alpha": alpha_piece,
                "fpr_upper_bound": upper,
                "feasible": upper is not None and upper <= budget,
            }
        )
    feasible = [item for item in checks if item["feasible"]]
    fallback_reason: str | None = None
    selected: dict[str, Any] | None = None
    if insufficient:
        fallback_reason = "confirmation_negative_entities_insufficient"
    elif upper_bound_failed:
        fallback_reason = "confirmation_fpr_upper_bound_not_computable"
    elif not feasible:
        fallback_reason = "no_candidate_meets_confirmed_fpr_budget"
    else:
        selected = min(
            feasible,
            key=lambda item: (float(item["threshold"]), -float(item["candidate_fpr"])),
        )
    if selected is None:
        threshold = float(source_receipt["threshold"])
        source_fallback = True
    else:
        threshold = float(selected["threshold"])
        source_fallback = False
    if source_fallback and threshold != float(source_receipt["threshold"]):
        raise SystemExit("源阈值回退不是同预算精确回退")
    return {
        "budget": budget,
        "familywise_alpha": familywise_alpha,
        "candidate_count": len(candidates),
        "bonferroni_alpha": alpha_piece,
        "confirmation_negative_entities": negative_count,
        "zero_error_fpr_upper_bound": zero_error_upper,
        "confirmation_sample_sufficient": not insufficient,
        "candidate_checks": checks,
        "selected_candidate": selected,
        "source_fallback": source_fallback,
        "fallback_reason": fallback_reason,
        "threshold": threshold,
    }


def evaluate_alert_threshold(
    threshold: float,
    budget: float,
    evaluation: np.ndarray,
    labels: np.ndarray,
    final_entity_scores: np.ndarray,
    first_time: np.ndarray,
    online: dict[str, np.ndarray],
    time_unit_per_second: float,
) -> dict[str, Any]:
    first_position = np.full(N_ENTITY_24, len(online["entity"]), np.int64)
    crossing = evaluation[online["entity"]] & (online["mean"] >= threshold)
    np.minimum.at(first_position, online["entity"][crossing], online["position"][crossing])
    alerted = evaluation & (first_position < len(online["entity"]))
    first_flow_index = np.full(N_ENTITY_24, np.nan, np.float64)
    first_seconds = np.full(N_ENTITY_24, np.nan, np.float64)
    alerted_ids = np.flatnonzero(alerted)
    positions = first_position[alerted_ids]
    first_flow_index[alerted_ids] = online["rank"][positions].astype(np.float64)
    first_seconds[alerted_ids] = (
        online["time"][positions].astype(np.float64) - first_time[alerted_ids]
    ) / time_unit_per_second
    metrics = base.evaluate_subset(
        evaluation,
        labels,
        final_entity_scores,
        alerted,
        first_flow_index,
        first_seconds,
        budget,
    )
    metrics["latency_distribution_population"] = (
        "已告警正评价实体；流序号从实体首流起按 1 计数"
    )
    return {
        "threshold": threshold,
        "evaluation_entities": metrics,
        "alert_rule": "任一流更新后的累计 p=1 实体均分首次达到阈值即锁存告警",
    }


def peak_host_rss_gib() -> float:
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    byte_count = value if sys.platform == "darwin" else value * 1024.0
    return byte_count / 2**30


def segment_receipt(
    mask: np.ndarray,
    entity_ids: np.ndarray,
    labels: np.ndarray,
    entity: np.ndarray,
) -> dict[str, Any]:
    return {
        "n_flow": int(mask[entity].sum()),
        "n_entity": int(len(entity_ids)),
        "n_positive_entity": int(labels.sum()),
        "n_negative_entity": int(len(labels) - labels.sum()),
        "entity_id_set_sha256": ndarray_sha256(entity_ids.astype(np.int64, copy=False)),
    }


def main() -> None:
    args = parse_args()
    if not args.config.is_file():
        raise SystemExit(f"配置不存在：{args.config}")
    config = load_json(args.config)
    validate_config(config)
    if args.validate_config:
        print("TWO_STAGE_CONFIDENCE_BUDGET_CONFIG_VALID", flush=True)
        return
    parent = validate_inputs(args, config)
    if args.validate_inputs:
        print("TWO_STAGE_CONFIDENCE_BUDGET_INPUTS_VALID", flush=True)
        return

    protected = (
        args.out / "threshold-seal.json",
        args.out / "two-stage-confidence-budget-results.json",
        args.out / "manifest.json",
        args.out / "swanlab-receipt.json",
        args.out / "swanlog",
    )
    if any(path.exists() for path in protected):
        raise SystemExit(f"双段 Q0 聚合制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)

    import swanlab
    import torch
    import xgboost as xgb

    build_info = xgb.build_info()
    if xgb.__version__ != "3.2.0" or build_info.get("USE_CUDA") is not True:
        raise SystemExit(
            f"XGBoost 环境不符：version={xgb.__version__} "
            f"USE_CUDA={build_info.get('USE_CUDA')}"
        )
    if not torch.cuda.is_available():
        raise SystemExit("CUDA 不可用，拒绝以 CPU 冒充冻结模型推理")
    free, total = torch.cuda.mem_get_info()
    if free / 2**30 < float(config["gpu_need_gib"]):
        raise SystemExit("可用显存低于双段 Q0 启动门槛")
    torch.cuda.reset_peak_memory_stats()
    log(f"GPU 总显存 {total / 2**30:.2f} GiB，可用 {free / 2**30:.2f} GiB")

    script_sha = sha256_file(Path(__file__).resolve())
    config_sha = sha256_file(args.config.resolve())
    tracking = config["tracking"]
    swanlab.init(
        workspace=tracking["workspace"],
        project=tracking["project"],
        name=RUN_ID,
        config={
            "seed": 42,
            "screening_only": True,
            "formal": False,
            "zero_training": True,
            "parent_run_id": PARENT_RUN_ID,
            "base_view": "semantic168",
            "p": 1.0,
            "selection_end_fraction": 0.1,
            "confirmation_end_fraction": 0.2,
            "candidate_fpr_grid": config["candidate_fpr_grid"],
            "entity_fpr_budgets": config["entity_fpr_budgets"],
            "familywise_alpha": config["familywise_alpha"],
            "target_score_calls": 1,
            "script_sha256": script_sha,
            "config_sha256": config_sha,
        },
        mode=tracking["mode"],
        logdir=str(args.out / "swanlog"),
    )

    log("阶段一：只读 LSPR23，重建 semantic168 三折折外源阈值")
    source_labels = np.load(CACHE / "y23.npy")
    source_indices = np.load(CACHE / "I23.npy")
    source_mask = np.load(CACHE / "M23.npy")
    source_entity = np.load(CACHE / "ent23.npy")
    source_time = np.load(CACHE / "t23_flow.npy")
    if len(source_labels) != N_FLOW_23 or len(source_entity) != N_FLOW_23:
        raise SystemExit("LSPR23 流数或实体键长度不符")
    if int(source_entity.max()) + 1 != N_ENTITY_23:
        raise SystemExit("LSPR23 实体数不符")
    base.assert_sequence_time_monotonic(
        source_time,
        source_indices,
        source_mask,
        N_FLOW_23,
        "LSPR23",
    )
    del source_time
    fold_of_flow, _, source_entity_labels = base.reconstruct_source_folds(
        source_labels,
        source_entity,
        parent["selection"]["fold_stat"],
        int(config["seed"]),
    )
    source_semantic = base.build_semantic_matrix(
        CACHE / "X23.npy",
        N_FLOW_23,
        source_indices,
        source_mask,
        int(config["predict_batch"]),
        int(config["sequence_batch"]),
        "LSPR23",
    )
    del source_indices, source_mask
    source_oof = np.full(N_FLOW_23, np.nan, np.float32)
    source_model_receipts: list[dict[str, Any]] = []
    for fold in range(N_FOLD):
        rows = np.flatnonzero(fold_of_flow == fold)
        model_path = args.parent_run_root.resolve() / f"model_oof_semantic168_fold{fold}.json"
        booster, receipt = base.load_booster(xgb, model_path, f"semantic168/fold{fold}")
        gpu_guard(torch, float(config["gpu_floor_gib"]), f"semantic168/fold{fold}/推理前")
        source_oof[rows] = base.predict_selected_rows(
            booster,
            source_semantic,
            rows,
            int(config["predict_batch"]),
            f"semantic168/fold{fold}/OOF",
        )
        receipt["holdout_flow_count"] = int(len(rows))
        source_model_receipts.append(receipt)
        del booster, rows
        torch.cuda.empty_cache()
    if not np.isfinite(source_oof).all():
        raise SystemExit("源折外分数存在未覆盖流")
    del source_semantic, fold_of_flow
    source_entity_scores = base.mean_entity_scores(source_oof, source_entity, N_ENTITY_23)
    del source_oof, source_entity, source_labels
    if int(source_entity_labels.sum()) != N_POS_ENTITY_23:
        raise SystemExit("LSPR23 正实体数不符")
    source_budget_thresholds = {
        f"budget_{float(budget):g}": base.source_operating_point(
            source_entity_scores,
            source_entity_labels,
            float(budget),
        )
        for budget in config["entity_fpr_budgets"]
    }
    del source_entity_scores

    log("阶段二：只读目标特征与时间，最终 semantic168 模型只预测一次")
    target_indices = np.load(CACHE / "I24.npy")
    target_mask = np.load(CACHE / "M24.npy")
    source_address = np.load(CACHE / "s24.npy", allow_pickle=True)
    destination_address = np.load(CACHE / "d24.npy", allow_pickle=True)
    target_time = np.load(CACHE / "t24.npy")
    base.assert_sequence_time_monotonic(
        target_time,
        target_indices,
        target_mask,
        N_FLOW_24,
        "LSPR24",
    )
    entity_key = np.array(
        [
            left + "|" + right if left <= right else right + "|" + left
            for left, right in zip(source_address, destination_address, strict=True)
        ],
        object,
    )
    _, target_entity = np.unique(entity_key, return_inverse=True)
    if int(target_entity.max()) + 1 != N_ENTITY_24:
        raise SystemExit(f"LSPR24 实体数不符：{int(target_entity.max()) + 1:,}")
    del entity_key, source_address, destination_address
    target_semantic = base.build_semantic_matrix(
        CACHE / "X24.npy",
        N_FLOW_24,
        target_indices,
        target_mask,
        int(config["predict_batch"]),
        int(config["sequence_batch"]),
        "LSPR24",
    )
    del target_indices, target_mask
    final_model_path = args.parent_run_root.resolve() / "model_semantic168.json"
    final_booster, final_model_receipt = base.load_booster(
        xgb,
        final_model_path,
        "semantic168/final",
    )
    gpu_guard(torch, float(config["gpu_floor_gib"]), "semantic168/final/目标推理前")
    target_flow_scores = predict_rows(
        final_booster,
        target_semantic,
        int(config["predict_batch"]),
        "semantic168/final/LSPR24",
    )
    target_prediction_ledger = [
        {"call": 1, "view": "semantic168", "n_flow": N_FLOW_24, "p": 1.0}
    ]
    del target_semantic, final_booster
    torch.cuda.empty_cache()

    final_entity_scores = base.mean_entity_scores(
        target_flow_scores,
        target_entity,
        N_ENTITY_24,
    )
    time_min = float(np.min(target_time))
    time_max = float(np.max(target_time))
    time_span_hours = (
        (time_max - time_min) / float(config["time_unit_per_second"]) / 3600.0
    )
    span_low, span_high = [float(value) for value in config["expected_time_span_hours"]]
    if not span_low <= time_span_hours <= span_high:
        raise SystemExit(f"LSPR24 时间跨度 {time_span_hours:.3f} 小时超出冻结门")
    segments = segment_entities(target_entity, target_time, time_min, time_max)
    online = base.prepare_sorted_online_state(target_flow_scores, target_entity, target_time)
    alert_scores = np.full(N_ENTITY_24, -math.inf, np.float64)
    np.maximum.at(alert_scores, online["entity"], online["mean"])
    if not np.isfinite(alert_scores).all():
        raise SystemExit("目标实体在线告警统计量含非有限值")

    log("阶段三：只读取选择段和确认段完整实体标签，封印候选与回退")
    selection_ids, selection_labels, selection_label_rows = load_segment_entity_labels(
        target_entity,
        segments["selection"],
        "选择段",
    )
    confirmation_ids, confirmation_labels, confirmation_label_rows = load_segment_entity_labels(
        target_entity,
        segments["confirmation"],
        "确认段",
    )
    if np.intersect1d(selection_ids, confirmation_ids).size:
        raise SystemExit("选择段与确认段实体集合不独立")
    candidate_grid = [float(value) for value in config["candidate_fpr_grid"]]
    candidates = build_candidates(
        alert_scores[selection_ids],
        selection_labels,
        candidate_grid,
    )
    candidate_by_rate = {float(item["candidate_fpr"]): item for item in candidates}
    confirmations: dict[str, Any] = {}
    frozen_methods: dict[str, Any] = {}
    for budget_value in config["entity_fpr_budgets"]:
        budget = float(budget_value)
        budget_key = f"budget_{budget:g}"
        source_receipt = source_budget_thresholds[budget_key]
        confirmation = confirm_candidates_for_budget(
            candidates,
            alert_scores[confirmation_ids],
            confirmation_labels,
            source_receipt,
            budget,
            float(config["familywise_alpha"]),
        )
        confirmations[budget_key] = confirmation
        frozen_methods[budget_key] = {
            "source_frozen": {
                "threshold": float(source_receipt["threshold"]),
                "source_receipt": source_receipt,
            },
            "selection_empirical": {
                "threshold": float(candidate_by_rate[budget]["threshold"]),
                "selection_candidate": candidate_by_rate[budget],
                "uses_confirmation": False,
            },
            "two_stage_confirmed": {
                "threshold": float(confirmation["threshold"]),
                "source_fallback": confirmation["source_fallback"],
                "fallback_reason": confirmation["fallback_reason"],
                "selected_candidate": confirmation["selected_candidate"],
            },
        }

    selection_segment = segment_receipt(
        segments["selection"],
        selection_ids,
        selection_labels,
        target_entity,
    )
    confirmation_segment = segment_receipt(
        segments["confirmation"],
        confirmation_ids,
        confirmation_labels,
        target_entity,
    )
    evaluation_ids_before_seal = np.flatnonzero(segments["evaluation"])
    boundary_ids = np.flatnonzero(segments["boundary"])
    threshold_seal = {
        "schema_version": "ch4-xgb-two-stage-confidence-budget-threshold-seal-v1",
        "run_id": RUN_ID,
        "sealed_before_evaluation_label_load": True,
        "evaluation_label_rows_read_before_seal": 0,
        "selection_and_confirmation_labels_authorized": True,
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "selection_rule_sha256": canonical_sha256(
            {
                "segment_time_fractions": config["segment_time_fractions"],
                "candidate_fpr_grid": config["candidate_fpr_grid"],
                "entity_fpr_budgets": config["entity_fpr_budgets"],
                "familywise_alpha": config["familywise_alpha"],
                "multiple_candidate_correction": config["multiple_candidate_correction"],
                "fpr_upper_bound": config["fpr_upper_bound"],
                "alert_statistic": config["alert_statistic"],
            }
        ),
        "parent": {
            "run_id": PARENT_RUN_ID,
            "eval_run_id": CONTINUATION_RUN_ID,
            "selected_adapter": parent["selected_adapter"],
            "p": parent["p_selection"]["semantic168"],
            "parent_artifact_sha256": parent["artifact_sha256"],
            "parent_eval_sha256": parent["parent_eval_sha256"],
            "parent_recovery_proof_sha256": parent["parent_recovery_proof_sha256"],
            "source_oof_models": source_model_receipts,
            "target_final_model": final_model_receipt,
        },
        "source": {
            "n_flow": N_FLOW_23,
            "n_entity": N_ENTITY_23,
            "n_positive_entity": N_POS_ENTITY_23,
            "fold_stat": parent["selection"]["fold_stat"],
            "budget_thresholds": source_budget_thresholds,
            "source_year_retrained": False,
            "oof_scores_persisted": False,
        },
        "target_unlabeled": {
            "n_flow": N_FLOW_24,
            "n_entity": N_ENTITY_24,
            "time_min_raw": time_min,
            "time_max_raw": time_max,
            "time_span_hours": time_span_hours,
            "target_score_calls": 1,
            "prediction_ledger": target_prediction_ledger,
            "target_scores_persisted": False,
        },
        "segments": {
            "selection_end_time_raw": segments["selection_end"],
            "confirmation_end_time_raw": segments["confirmation_end"],
            "selection": selection_segment,
            "confirmation": confirmation_segment,
            "evaluation_before_label_load": {
                "n_flow": int(segments["evaluation"][target_entity].sum()),
                "n_entity": int(len(evaluation_ids_before_seal)),
                "entity_id_set_sha256": ndarray_sha256(
                    evaluation_ids_before_seal.astype(np.int64, copy=False)
                ),
            },
            "boundary_crossing": {
                "n_flow": int(segments["boundary"][target_entity].sum()),
                "n_entity": int(len(boundary_ids)),
                "entity_id_set_sha256": ndarray_sha256(
                    boundary_ids.astype(np.int64, copy=False)
                ),
            },
            "pairwise_disjoint": True,
        },
        "label_access": {
            "selection_label_rows": selection_label_rows,
            "confirmation_label_rows": confirmation_label_rows,
            "evaluation_label_rows": 0,
        },
        "alert_statistic": (
            "冻结 semantic168 逐流分数按 p=1 累计实体均分；实体告警统计量为历史最大累计均分"
        ),
        "candidate_thresholds": candidates,
        "confirmations": confirmations,
        "frozen_methods": frozen_methods,
        "budget_provenance": config["budget_provenance"],
        "forbidden_after_seal": [
            "用评价段标签改变候选、阈值、预算或时间边界",
            "评价段重新选择双段方法或回退状态",
            "评价段全体分数 top-k",
        ],
    }
    seal_path = args.out / "threshold-seal.json"
    atomic_json(seal_path, threshold_seal)
    seal_sha = sha256_file(seal_path) if seal_path.is_file() else None
    if seal_sha is None:
        raise SystemExit("阈值封印未成功原子落盘")
    log(f"阈值封印已原子落盘：{seal_path}")

    log("阶段四：封印后首次读取评价新实体标签，只作冻结评价")
    evaluation_ids, evaluation_labels, evaluation_label_rows = load_segment_entity_labels(
        target_entity,
        segments["evaluation"],
        "评价段",
    )
    if not np.array_equal(evaluation_ids, evaluation_ids_before_seal):
        raise SystemExit("封印前后评价实体集合发生变化")
    if np.intersect1d(selection_ids, evaluation_ids).size or np.intersect1d(
        confirmation_ids,
        evaluation_ids,
    ).size:
        raise SystemExit("评价实体与先导实体集合发生交叉")
    target_entity_labels = np.zeros(N_ENTITY_24, np.uint8)
    target_entity_labels[evaluation_ids] = evaluation_labels
    evaluation: dict[str, Any] = {}
    metric_payload: dict[str, int | float] = {
        "segments/selection/entities": int(len(selection_ids)),
        "segments/confirmation/entities": int(len(confirmation_ids)),
        "segments/evaluation/entities": int(len(evaluation_ids)),
        "segments/boundary/entities": int(len(boundary_ids)),
    }
    for budget_value in config["entity_fpr_budgets"]:
        budget = float(budget_value)
        budget_key = f"budget_{budget:g}"
        oracle_receipt = base.conservative_threshold(
            alert_scores[evaluation_ids][evaluation_labels == 0],
            budget,
        )
        method_receipts = {
            **frozen_methods[budget_key],
            "evaluation_oracle": {
                "threshold": float(oracle_receipt["threshold"]),
                "diagnostic_only": True,
                "uses_evaluation_labels_after_seal": True,
                "oracle_receipt": oracle_receipt,
            },
        }
        method_results: dict[str, Any] = {}
        for method in METHODS:
            threshold = float(method_receipts[method]["threshold"])
            metrics = evaluate_alert_threshold(
                threshold,
                budget,
                segments["evaluation"],
                target_entity_labels,
                final_entity_scores,
                segments["first_time"],
                online,
                float(config["time_unit_per_second"]),
            )
            method_results[method] = {
                "display_name": METHOD_DISPLAY_NAMES[method],
                "selection_receipt": method_receipts[method],
                **metrics,
            }
            aggregate = metrics["evaluation_entities"]
            for metric_name in (
                "actual_entity_fpr",
                "detection_rate",
                "false_positive_count",
                "budget_violation_fpr",
                "budget_violation_count",
                "entity_ap",
                "first_alert_flow_index_median",
                "first_alert_flow_index_p90",
                "unalerted_censor_rate",
            ):
                value = aggregate[metric_name]
                if value is not None and math.isfinite(float(value)):
                    metric_payload[f"{budget_key}/{method}/{metric_name}"] = value
        ap_values = {
            method_results[method]["evaluation_entities"]["entity_ap"] for method in METHODS
        }
        if len(ap_values) != 1:
            raise SystemExit(f"{budget_key} 的阈值层意外改变冻结实体 AP")
        evaluation[budget_key] = {
            "budget": budget,
            "provenance": config["budget_provenance"][f"{budget:g}"],
            "confirmation": confirmations[budget_key],
            "methods": method_results,
            "entity_ap_invariance": {
                "passed": True,
                "reason": "四种方法共享冻结最终实体均分及逐项相同排序，只改变告警阈值",
                "value": next(iter(ap_values)),
            },
        }

    resource_aggregate = {
        "host_peak_rss_gib": peak_host_rss_gib(),
        "gpu_peak_allocated_gib": torch.cuda.max_memory_allocated() / 2**30,
        "gpu_peak_reserved_gib": torch.cuda.max_memory_reserved() / 2**30,
        "runtime_seconds": time.time() - T0,
    }
    for key, value in resource_aggregate.items():
        metric_payload[f"resource/{key}"] = value
    result = {
        "schema_version": "ch4-xgb-two-stage-confidence-budget-q0-results-v1",
        "run_id": RUN_ID,
        "display_name": config["display_name"],
        "seed": 42,
        "screening_only": True,
        "formal": False,
        "formal_paper_evidence": False,
        "independent_test": False,
        "zero_training": True,
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "threshold_seal_sha256": seal_sha,
        "threshold_sealed_before_evaluation_label_load": True,
        "evaluation_labels_loaded_after_threshold_seal": True,
        "source_year_retrained": False,
        "base": {
            "parent_run_id": PARENT_RUN_ID,
            "parent_eval_run_id": CONTINUATION_RUN_ID,
            "view": "semantic168",
            "p": 1.0,
            "num_boost_round": N_TREE,
            "xgboost_version": xgb.__version__,
            "xgboost_params": EXPECTED_XGB_PARAMS,
        },
        "segments": {
            "selection": selection_segment,
            "confirmation": confirmation_segment,
            "evaluation": segment_receipt(
                segments["evaluation"],
                evaluation_ids,
                evaluation_labels,
                target_entity,
            ),
            "boundary_crossing": {
                "n_flow": int(segments["boundary"][target_entity].sum()),
                "n_entity": int(len(boundary_ids)),
                "entity_id_set_sha256": ndarray_sha256(
                    boundary_ids.astype(np.int64, copy=False)
                ),
            },
            "pairwise_disjoint": True,
        },
        "label_access": {
            "selection_label_rows_before_seal": selection_label_rows,
            "confirmation_label_rows_before_seal": confirmation_label_rows,
            "evaluation_label_rows_before_seal": 0,
            "evaluation_label_rows_after_seal": evaluation_label_rows,
        },
        "budget_provenance": config["budget_provenance"],
        "evaluation": evaluation,
        "resource_aggregate": resource_aggregate,
        "isolation": {
            "target_score_calls": 1,
            "prediction_ledger": target_prediction_ledger,
            "post_seal_threshold_reselection": False,
            "post_seal_method_reselection": False,
            "post_seal_top_k": False,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "derived_matrices_persisted": False,
            "label_details_persisted": False,
            "new_models_persisted": False,
            "swanlab_aggregate_only": True,
        },
        "metric_definitions": {
            "entity_ap": "冻结最终实体均分排序的平均精确率；四种阈值逐项相同",
            "fpr_upper_bound": (
                "确认段良性实体告警伯努利事件的 Bonferroni 校正单侧精确二项上界"
            ),
            "first_alert": "已告警正评价实体从实体首流起首次达到阈值的 1 基流序号",
            "censor_rate": "正评价实体中截至目标结束仍未告警的比例",
        },
    }
    result_path = args.out / "two-stage-confidence-budget-results.json"
    atomic_json(result_path, result)

    swanlab.log(metric_payload, step=0)
    swanlab.finish()
    swanlab_receipt = {
        "schema_version": "ch4-xgb-two-stage-confidence-budget-aggregate-swanlab-v1",
        "completed": True,
        "workspace": tracking["workspace"],
        "project": tracking["project"],
        "mode": tracking["mode"],
        "aggregate_only": True,
        "metric_keys": sorted(metric_payload),
    }
    atomic_json(args.out / "swanlab-receipt.json", swanlab_receipt)

    manifest = {
        "schema_version": "ch4-xgb-two-stage-confidence-budget-q0-manifest-v1",
        "run_id": RUN_ID,
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "screening_only": True,
        "formal": False,
        "per_sample_artifacts_persisted": False,
        "files": {},
    }
    for name in (
        "resource-receipt.json",
        "threshold-seal.json",
        "two-stage-confidence-budget-results.json",
        "swanlab-receipt.json",
    ):
        path = args.out / name
        if not path.is_file():
            raise SystemExit(f"必需聚合制品缺失：{path}")
        manifest["files"][name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    atomic_json(args.out / "manifest.json", manifest)
    log(f"双段先导置信预算告警聚合结果已保存：{result_path}")


if __name__ == "__main__":
    main()
