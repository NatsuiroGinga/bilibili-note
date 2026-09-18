#!/usr/bin/env python3
"""零训练诊断实体重复曝光是否同时造成误报突破与迟到正检出。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from ch3_xgb_cpa_elp_eval_continuation import (  # noqa: E402
    BOOLEAN_IDX,
    CATEGORICAL_IDX,
    D_RAW,
    EXPECTED_CONFIG,
    EXPECTED_SHA256,
    EXPECTED_XGB_PARAMS,
    NUMERIC_IDX,
    PARENT_RUN_ID,
    configure_prediction_device,
    gpu_guard,
)

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "runs/diagnostics/dijk-repro/cache"
RUN_ID = "ch4-xgb-entity-repeated-exposure-pathology-lspr23-q0-seed42-v1-rerun1"
DISPLAY_NAME = "实体重复曝光误报时延病灶源年诊断"
SCHEMA_VERSION = "ch4-xgb-entity-exposure-lesion-source-diagnostic-v1"
PARENT_RECOVERY_SCHEMA = "ch3-xgb-parent-recovery-proof-v1"
PARENT_RECOVERY_FILENAME = "parent-recovery-proof.json"
ALLOWED_ARRAYS = ("X23", "y23", "I23", "M23", "E23", "ent23", "t23_flow")
N_FLOW = 16_353_511
N_SEQUENCE = 271_815
N_ENTITY = 150_680
N_POS_ENTITY = 239
N_NEG_ENTITY = 150_441
N_FOLD = 3
N_TREE = 800
SEQUENCE_LENGTH = 128
SEMANTIC_DIMENSION = 168
EXPECTED_FOLD_COUNTS = (50_227, 50_227, 50_226)
EXPECTED_FOLD_POSITIVE_COUNTS = (80, 80, 79)
EXPECTED_PARENT_ARTIFACTS = (
    "selection_frozen_xgb2x2.json",
    "effective_config_receipts.json",
    "model_oof_semantic168_fold0.json",
    "model_oof_semantic168_fold1.json",
    "model_oof_semantic168_fold2.json",
)
T0 = time.time()
LAST_BEAT = [T0]
TARGET_YEAR_ARRAYS_READ = 0
NEW_MODELS_TRAINED = 0


class InputContractError(RuntimeError):
    """输入身份、隔离或因果顺序不符合冻结合同时使用。"""


def invalid(message: str) -> None:
    raise InputContractError(message)


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def beat(stage: str, done: int, total: int, started: float, every: float = 30.0) -> None:
    now = time.time()
    if now - LAST_BEAT[0] < every and done < total:
        return
    LAST_BEAT[0] = now
    elapsed = now - started
    rate = done / max(elapsed, 1e-9)
    eta = (total - done) / max(rate, 1e-9)
    log(
        f"  [{stage}] {done:,}/{total:,} ({done / max(total, 1):.1%}) "
        f"吞吐 {rate:,.0f}/s 累计 {elapsed:.0f}s 预计剩余 {eta:.0f}s"
    )


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_array(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(json.dumps(array.shape, separators=(",", ":")).encode("ascii"))
    digest.update(memoryview(array).cast("B"))
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(partial, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DISPLAY_NAME)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT
        / "configs/ch4-xgb-entity-exposure-lesion-source-diagnostic-seed42-v1.json",
    )
    parser.add_argument(
        "--parent-run-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / PARENT_RUN_ID,
    )
    parser.add_argument(
        "--parent-config",
        type=Path,
        default=ROOT / "configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json",
    )
    parser.add_argument("--threshold-seal", type=Path)
    parser.add_argument("--parent-recovery-proof", type=Path)
    parser.add_argument(
        "--out", type=Path, default=ROOT / "runs/diagnostics" / RUN_ID
    )
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


def validate_config(config: dict[str, Any]) -> None:
    expected = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "seed": 42,
        "screening_only": True,
        "formal": False,
        "formal_paper_evidence": False,
        "independent_test": False,
        "source_year": "LSPR23",
        "source_year_only": True,
        "zero_training": True,
        "parent_run_id": PARENT_RUN_ID,
        "base_adapter": "semantic168",
        "power_mean_p": 1.0,
        "comparison_operator": "strict_greater_than",
        "entity_fpr_budget": 0.04,
        "pathology_rule": "FPR(all)>0.04 AND N_late_positive>0",
        "exposure_cutoff": None,
        "allowed_arrays": list(ALLOWED_ARRAYS),
        "target_year_arrays_read": 0,
        "new_models_trained": 0,
        "oof_models_loaded": 3,
        "predict_batch": 2_000_000,
        "sequence_batch": 2_048,
        "curve_write_batch": 250_000,
    }
    for key, expected_value in expected.items():
        if config.get(key) != expected_value:
            invalid(f"配置字段不符：{key}")
    if config.get("parent_recovery_proof") != {
        "schema_version": PARENT_RECOVERY_SCHEMA,
        "requires_parent_incomplete": True,
        "original_manifest_expected": False,
        "relative_path": (
            "runs/recovery/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-for-"
            "ch4-xgb-pbc-q0-seed42-v1-rerun2-v1/parent-recovery-proof.json"
        ),
    }:
        invalid("父恢复证明合同不符")
    if config.get("input_contract") != {
        "flow_count": N_FLOW,
        "sequence_count": N_SEQUENCE,
        "entity_count": N_ENTITY,
        "positive_entity_count": N_POS_ENTITY,
        "negative_entity_count": N_NEG_ENTITY,
        "feature_count": D_RAW,
        "semantic_feature_count": SEMANTIC_DIMENSION,
        "sequence_length": SEQUENCE_LENGTH,
        "fold_entity_counts": list(EXPECTED_FOLD_COUNTS),
        "fold_positive_entity_counts": list(EXPECTED_FOLD_POSITIVE_COUNTS),
    }:
        invalid("输入规模合同不符")
    threshold = config.get("source_threshold_contract", {})
    expected_threshold = {
        "file_sha256": "f70cb08c5e40413934b9a812debf98da47d6034940196348a808f8377dbe9334",
        "receipt_sha256": "5693e44838514200bbe15ce61b01d06cffbfc3a4dc3b74b80c347378970dfb23",
        "threshold": 3.660049696918577e-05,
        "population": N_NEG_ENTITY,
        "strictly_above_count": 6_017,
        "empirical_fpr": 0.03999574584056208,
        "boundary_tie_count": 1,
        "comparison_operator": ">",
        "tie_policy": "阈值同分实体全部不告警，不拆并列组",
        "entity_key_sha256": "40bdaf3e6a28b2a67e06754b8d5538edbc68cc8cc434d236e1643fba1ba314c6",
        "first_exposure_score_sha256": "ab1ff9c89cfdce9f13c551ef907d3561847492ee5873e7bd54618f43a41a76c2",
        "negative_first_exposure_score_sha256": "99bba9ff64bd0344f639a4306e1dc3c44e7cb0322f8261b036a682b777fcd5d7",
        "fold_assignment_sha256": "a206048274edd5bb20c8e92874c0c2c1853009ebbd5ea1533940f2ab34fd5aa5",
        "score_preprocessing": {
            "threshold_reproduction": "raw_float32_xgboost_score",
            "streaming_power_mean": (
                "clip_[1e-7,1]_then_float64_cumulative_sum_then_float32_readout"
            ),
            "power": 1.0,
        },
    }
    if threshold.get("relative_path") != (
        "runs/candidates/ch4-xgb-confidence-fallback-source-q0-seed42-v1/"
        "source-threshold-seal.json"
    ):
        invalid("源阈值收据路径不符")
    for key, expected_value in expected_threshold.items():
        if threshold.get(key) != expected_value:
            invalid(f"源阈值冻结配置不符：{key}")
    artifact_policy = config.get("artifact_policy", {})
    if artifact_policy != {
        "persist_diagnostic_summary": True,
        "persist_full_exposure_support_curve": True,
        "persist_input_resource_status_log_manifest": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_fold_membership": False,
        "persist_entity_ids": False,
        "persist_new_models": False,
    }:
        invalid("制品白名单合同不符")


def resolve_paths(args: argparse.Namespace, config: dict[str, Any]) -> None:
    if args.threshold_seal is None:
        args.threshold_seal = ROOT / config["source_threshold_contract"]["relative_path"]
    if args.parent_recovery_proof is None:
        args.parent_recovery_proof = ROOT / config["parent_recovery_proof"]["relative_path"]


def validate_threshold_seal(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        invalid(f"源阈值收据缺失：{path}")
    contract = config["source_threshold_contract"]
    if sha256_file(path) != contract["file_sha256"]:
        invalid("源阈值收据文件 SHA-256 不符")
    seal = load_json(path)
    receipt_sha = seal.get("receipt_sha256")
    unsigned = dict(seal)
    unsigned.pop("receipt_sha256", None)
    if receipt_sha != canonical_sha256(unsigned) or receipt_sha != contract["receipt_sha256"]:
        invalid("源阈值内部收据 SHA-256 不符")
    source = seal.get("source_threshold", {})
    exact = {
        "threshold": contract["threshold"],
        "population": contract["population"],
        "rate_requested": config["entity_fpr_budget"],
        "count_cap": 6_017,
        "strictly_above_count": contract["strictly_above_count"],
        "empirical_fpr": contract["empirical_fpr"],
        "order_statistic_index_zero_based": 144_423,
        "boundary_tie_count": contract["boundary_tie_count"],
        "comparison_operator": contract["comparison_operator"],
        "tie_policy": contract["tie_policy"],
    }
    if source != exact:
        invalid("源阈值数值、比较符或并列策略不符")
    if (
        seal.get("schema_version")
        != "ch4-xgb-confidence-fallback-source-threshold-seal-v1"
        or seal.get("run_id") != "ch4-xgb-confidence-fallback-source-q0-seed42-v1"
        or seal.get("sealed_before_development_selection") is not True
        or seal.get("entity_count") != N_ENTITY
        or seal.get("negative_entity_count") != N_NEG_ENTITY
        or seal.get("target_year_arrays_read") != 0
        or seal.get("new_models_trained") != 0
    ):
        invalid("源阈值收据身份或隔离字段不符")
    return seal


def validate_parent(
    args: argparse.Namespace, config: dict[str, Any], seal: dict[str, Any]
) -> dict[str, Any]:
    parent_root = args.parent_run_root.resolve()
    if parent_root.name != PARENT_RUN_ID or args.out.resolve() == parent_root:
        invalid("父运行或独立输出身份不符")
    if args.out.resolve().name != RUN_ID:
        invalid("本诊断运行目录身份不符")
    if not args.parent_config.is_file():
        invalid(f"父配置缺失：{args.parent_config}")
    parent_config = load_json(args.parent_config)
    for key, expected in EXPECTED_CONFIG.items():
        if parent_config.get(key) != expected:
            invalid(f"父配置字段不符：{key}")

    proof_path = args.parent_recovery_proof.resolve()
    if proof_path.name != PARENT_RECOVERY_FILENAME or not proof_path.is_file():
        invalid(f"父恢复证明缺失：{proof_path}")
    if parent_root in proof_path.parents:
        invalid("父恢复证明不得位于未完成父运行目录")
    proof = load_json(proof_path)
    parent_state = proof.get("parent_state", {})
    historical_status = parent_state.get("historical_status", {})
    if (
        proof.get("schema_version") != PARENT_RECOVERY_SCHEMA
        or proof.get("parent_run_id") != PARENT_RUN_ID
        or Path(str(proof.get("parent_run_root", ""))).resolve() != parent_root
        or proof.get("does_not_assert_parent_completion") is not True
        or parent_state.get("complete") is not False
        or historical_status.get("state") != "running"
        or historical_status.get("stage") != "source_selection"
        or historical_status.get("exit_code") is not None
        or parent_state.get("missing_completion_artifacts")
        != ["xgb_cpa_elp_results.json", "manifest.json"]
    ):
        invalid("父恢复证明未保持既有中断事实")
    parent_status = parent_root / "status.json"
    if (
        not parent_status.is_file()
        or historical_status.get("filename") != parent_status.name
        or historical_status.get("sha256") != sha256_file(parent_status)
        or historical_status.get("bytes") != parent_status.stat().st_size
    ):
        invalid("父实际状态与恢复证明不符")
    for name in parent_state["missing_completion_artifacts"]:
        if (parent_root / name).exists():
            invalid(f"父运行出现恢复证明声明缺失的制品：{name}")

    proof_artifacts = proof.get("artifacts", {})
    artifact_hashes: dict[str, str] = {}
    seal_models = {
        item.get("filename"): item for item in seal.get("source_model_receipts", [])
    }
    for name in EXPECTED_PARENT_ARTIFACTS:
        path = parent_root / name
        receipt = proof_artifacts.get(name, {})
        if not path.is_file() or not receipt:
            invalid(f"父恢复证明或父制品缺失：{name}")
        actual = sha256_file(path)
        if actual != receipt.get("sha256") or path.stat().st_size != receipt.get("bytes"):
            invalid(f"父制品与恢复证明不符：{name}")
        if name.startswith("model_oof_"):
            if (
                receipt.get("num_boosted_rounds") != N_TREE
                or seal_models.get(name, {}).get("sha256") != actual
                or seal_models.get(name, {}).get("num_boosted_rounds") != N_TREE
            ):
                invalid(f"父折模型与阈值收据不符：{name}")
        artifact_hashes[name] = actual
    for name in ("selection_frozen_xgb2x2.json", "effective_config_receipts.json"):
        if artifact_hashes[name] != EXPECTED_SHA256[name]:
            invalid(f"父固定收据摘要不符：{name}")
    selection = load_json(parent_root / "selection_frozen_xgb2x2.json")
    if (
        selection.get("run_name") != PARENT_RUN_ID
        or selection.get("seed") != 42
        or selection.get("n_fold") != N_FOLD
        or selection.get("xgb_params") != EXPECTED_XGB_PARAMS
        or selection.get("adapter_selection", {}).get("selected") != "semantic168"
        or float(
            selection.get("p_selection", {})
            .get("semantic168", {})
            .get("p_selected", math.nan)
        )
        != 1.0
        or selection.get("lspr23")
        != {"n_flow": N_FLOW, "n_entity": N_ENTITY, "n_pos_entity": N_POS_ENTITY}
    ):
        invalid("父选择收据未冻结 semantic168、p=1 或 LSPR23 身份")
    return {
        "root": str(parent_root),
        "config_path": str(args.parent_config.resolve()),
        "config_sha256": sha256_file(args.parent_config),
        "recovery_proof_path": str(proof_path),
        "recovery_proof_sha256": sha256_file(proof_path),
        "artifact_sha256": artifact_hashes,
        "selection": selection,
    }


def hash_allowed_arrays() -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for name in ALLOWED_ARRAYS:
        if "24" in name:
            invalid(f"数组白名单含目标年或非源年成员：{name}")
        path = CACHE / f"{name}.npy"
        if not path.is_file() or path.stat().st_size <= 0:
            invalid(f"源年数组缺失或为空：{path}")
        log(f"哈希源年数组：{path.name}")
        receipts[name] = {
            "filename": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return receipts


def guarded_source_load(name: str) -> np.ndarray:
    global TARGET_YEAR_ARRAYS_READ
    if "24" in name:
        TARGET_YEAR_ARRAYS_READ += 1
        invalid(f"拒绝读取目标年数组：{name}")
    if name not in ALLOWED_ARRAYS:
        invalid(f"拒绝读取源年白名单外数组：{name}")
    return np.load(CACHE / f"{name}.npy", mmap_mode="r", allow_pickle=False)


def scan_source_structure(
    labels: np.ndarray,
    indices: np.ndarray,
    masks: np.ndarray,
    sequence_entities: np.ndarray,
    flow_entities: np.ndarray,
    flow_times: np.ndarray,
) -> dict[str, np.ndarray | int]:
    if (
        labels.shape != (N_FLOW,)
        or flow_entities.shape != (N_FLOW,)
        or flow_times.shape != (N_FLOW,)
        or indices.shape != (N_SEQUENCE, SEQUENCE_LENGTH)
        or masks.shape != indices.shape
        or sequence_entities.shape != (N_SEQUENCE,)
    ):
        invalid("LSPR23 数组形状不符合冻结合同")
    if int(sequence_entities.min()) != 0 or int(sequence_entities.max()) != N_ENTITY - 1:
        invalid("E23 实体编号范围不符")
    entity_ids = np.unique(sequence_entities)
    if not np.array_equal(entity_ids, np.arange(N_ENTITY)):
        invalid("E23 未恰好覆盖全部实体")
    if not np.isfinite(np.asarray(flow_times)).all():
        invalid("t23_flow 含非有限时间")

    entity_labels = np.zeros(N_ENTITY, np.int8)
    entity_flow_counts = np.zeros(N_ENTITY, np.int64)
    entity_positive_flow_counts = np.zeros(N_ENTITY, np.int64)
    first_time = np.full(N_ENTITY, np.nan, np.float64)
    last_time = np.full(N_ENTITY, np.nan, np.float64)
    flow_seen = np.zeros(N_FLOW, np.bool_)
    within_reversals = 0
    cross_reversals = 0
    started = time.time()
    for start in range(0, N_SEQUENCE, 20_000):
        stop = min(start + 20_000, N_SEQUENCE)
        block_indices = np.asarray(indices[start:stop])
        block_valid = np.asarray(masks[start:stop]) > 0
        block_entities = np.asarray(sequence_entities[start:stop], np.int64)
        for local in range(stop - start):
            valid = block_valid[local]
            rows = np.asarray(block_indices[local, valid], np.int64)
            if len(rows) == 0:
                invalid(f"序列 {start + local} 没有有效流")
            if int(rows.min()) < 0 or int(rows.max()) >= N_FLOW:
                invalid(f"序列 {start + local} 含越界流索引")
            if flow_seen[rows].any() or len(rows) != len(np.unique(rows)):
                invalid(f"序列 {start + local} 重复覆盖流")
            flow_seen[rows] = True
            entity = int(block_entities[local])
            row_entities = np.asarray(flow_entities[rows], np.int64)
            if not np.all(row_entities == entity):
                invalid(f"序列 {start + local} 的 ent23 与 E23 不一致")
            times = np.asarray(flow_times[rows], np.float64)
            within_reversals += int(np.count_nonzero(times[1:] < times[:-1]))
            if math.isfinite(last_time[entity]) and times[0] < last_time[entity]:
                cross_reversals += 1
            if not math.isfinite(first_time[entity]):
                first_time[entity] = times[0]
            last_time[entity] = times[-1]
            row_labels = np.asarray(labels[rows])
            if not np.isin(row_labels, (0.0, 1.0)).all():
                invalid("y23 包含非二元标签")
            entity_labels[entity] = max(entity_labels[entity], int(row_labels.max()))
            entity_flow_counts[entity] += len(rows)
            entity_positive_flow_counts[entity] += int(row_labels.sum())
        beat("源年覆盖与时间门", stop, N_SEQUENCE, started)
    if not flow_seen.all():
        invalid(f"I23/M23 未覆盖全部流：缺少 {int((~flow_seen).sum()):,} 条")
    if within_reversals != 0 or cross_reversals != 0:
        invalid(
            f"因果时间门失败：段内逆序={within_reversals} 跨段逆序={cross_reversals}"
        )
    if (
        int(entity_flow_counts.sum()) != N_FLOW
        or int(entity_labels.sum()) != N_POS_ENTITY
        or np.any(entity_flow_counts <= 0)
    ):
        invalid("LSPR23 覆盖数、实体数或正实体数不符")
    return {
        "entity_ids": entity_ids.astype(np.int64, copy=False),
        "entity_labels": entity_labels,
        "entity_flow_counts": entity_flow_counts,
        "entity_positive_flow_counts": entity_positive_flow_counts,
        "first_time": first_time,
        "flow_coverage_count": int(flow_seen.sum()),
        "duplicate_flow_coverage_count": 0,
        "within_segment_time_reversals": within_reversals,
        "cross_segment_time_reversals": cross_reversals,
    }


def make_folds(entity_labels: np.ndarray, seed: int) -> np.ndarray:
    random_state = np.random.RandomState(seed)
    fold_of_entity = np.empty(N_ENTITY, np.int8)
    for label in (0, 1):
        entity_ids = np.flatnonzero(entity_labels == label)
        entity_ids = entity_ids[random_state.permutation(len(entity_ids))]
        fold_of_entity[entity_ids] = np.arange(len(entity_ids)) % N_FOLD
    counts = tuple(int((fold_of_entity == fold).sum()) for fold in range(N_FOLD))
    positives = tuple(
        int(entity_labels[fold_of_entity == fold].sum()) for fold in range(N_FOLD)
    )
    if counts != EXPECTED_FOLD_COUNTS or positives != EXPECTED_FOLD_POSITIVE_COUNTS:
        invalid(f"实体三折规模不符：counts={counts} positives={positives}")
    return fold_of_entity


def fold_statistics(
    fold_of_entity: np.ndarray,
    entity_labels: np.ndarray,
    entity_flow_counts: np.ndarray,
    entity_positive_flow_counts: np.ndarray,
) -> list[dict[str, int]]:
    result: list[dict[str, int]] = []
    for fold in range(N_FOLD):
        mask = fold_of_entity == fold
        result.append(
            {
                "fold": fold,
                "n_entity": int(mask.sum()),
                "n_pos_entity": int(entity_labels[mask].sum()),
                "n_flow": int(entity_flow_counts[mask].sum()),
                "n_pos_flow": int(entity_positive_flow_counts[mask].sum()),
            }
        )
    return result


def build_semantic_matrix(
    x_path: Path, indices: np.ndarray, masks: np.ndarray
) -> np.ndarray:
    """逐字保持第三章 semantic168 的段内因果特征语义。"""
    if indices.shape != (N_SEQUENCE, SEQUENCE_LENGTH) or masks.shape != indices.shape:
        invalid("semantic168 的 I23/M23 形状不符")
    n_valid = int((masks > 0).sum())
    if n_valid != N_FLOW:
        invalid("semantic168 的掩码覆盖数不符")
    dimension = D_RAW + len(NUMERIC_IDX) + len(CATEGORICAL_IDX) + len(BOOLEAN_IDX) + 2
    if dimension != SEMANTIC_DIMENSION:
        invalid("semantic168 维数推导不符")
    out = np.empty((N_FLOW, dimension), np.float32)
    source = np.load(x_path, mmap_mode="r", allow_pickle=False)
    if source.shape != (N_FLOW, D_RAW):
        invalid(f"X23 形状不符：{source.shape}")
    started = time.time()
    for start in range(0, N_FLOW, 2_000_000):
        stop = min(start + 2_000_000, N_FLOW)
        out[start:stop, :D_RAW] = source[start:stop]
        beat("semantic168/原始特征", stop, N_FLOW, started)
    del source

    cover = np.zeros(N_FLOW, np.bool_)
    lower = np.tri(SEQUENCE_LENGTH, SEQUENCE_LENGTH, dtype=bool)
    started = time.time()
    for start in range(0, N_SEQUENCE, 2_048):
        stop = min(start + 2_048, N_SEQUENCE)
        index_block = np.asarray(indices[start:stop])
        mask = np.asarray(masks[start:stop]) > 0
        batch, width = index_block.shape
        flat = index_block.reshape(-1)
        current = out[flat, :D_RAW].reshape(batch, width, D_RAW)
        count = np.cumsum(mask, axis=1, dtype=np.int32)
        denominator = np.maximum(count, 1).astype(np.float32)
        target = flat[mask.reshape(-1)]

        numeric = current[:, :, NUMERIC_IDX]
        numeric_sum = np.cumsum(
            numeric * mask[:, :, None], axis=1, dtype=np.float64
        )
        residual = numeric - numeric_sum / denominator[:, :, None]
        cursor = D_RAW
        out[target, cursor : cursor + len(NUMERIC_IDX)] = residual.reshape(
            -1, len(NUMERIC_IDX)
        )[mask.reshape(-1)]
        cursor += len(NUMERIC_IDX)

        prefix_mask = lower[None, :, :] & mask[:, None, :]
        for feature_idx in CATEGORICAL_IDX:
            value = current[:, :, feature_idx]
            equal = value[:, :, None] == value[:, None, :]
            frequency = (equal & prefix_mask).sum(axis=2) / denominator
            out[target, cursor] = frequency.reshape(-1)[mask.reshape(-1)]
            cursor += 1
        for feature_idx in BOOLEAN_IDX:
            truth = (current[:, :, feature_idx] > 0) & mask
            truth_rate = np.cumsum(truth, axis=1) / denominator
            out[target, cursor] = truth_rate.reshape(-1)[mask.reshape(-1)]
            cursor += 1
        out[target, cursor] = np.log1p(count).reshape(-1)[mask.reshape(-1)]
        cursor += 1
        out[target, cursor] = (count == 1).reshape(-1)[mask.reshape(-1)]
        cursor += 1
        if cursor != dimension:
            invalid("semantic168 写入列数不完整")
        cover[target] = True
        beat("semantic168/段内语义前缀", stop, N_SEQUENCE, started)
    if not cover.all() or not np.isfinite(out).all():
        invalid("semantic168 覆盖不完整或含非有限值")
    return out


def load_booster(
    xgb_module: Any, path: Path, fold: int, expected_sha: str
) -> tuple[Any, dict[str, Any]]:
    actual_sha = sha256_file(path)
    if actual_sha != expected_sha:
        invalid(f"折 {fold} 模型 SHA-256 与阈值收据不符")
    booster = xgb_module.Booster()
    booster.load_model(path)
    if int(booster.num_boosted_rounds()) != N_TREE:
        invalid(f"折 {fold} 模型树数不是 {N_TREE}")
    device = configure_prediction_device(booster, f"semantic168/fold{fold}")
    return booster, {
        "fold": fold,
        "filename": path.name,
        "sha256": actual_sha,
        "num_boosted_rounds": N_TREE,
        "prediction_device": device,
    }


def update_entity_states(
    entities: np.ndarray,
    times: np.ndarray,
    raw_scores: np.ndarray,
    threshold: float,
    cumulative_sum: np.ndarray,
    exposure_count: np.ndarray,
    first_scores: np.ndarray,
    first_alert_exposure: np.ndarray,
    first_alert_time: np.ndarray,
) -> None:
    boundaries = np.flatnonzero(np.r_[True, entities[1:] != entities[:-1], True])
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        entity = int(entities[left])
        prior_count = int(exposure_count[entity])
        scores = np.asarray(raw_scores[left:right], np.float32)
        clipped = np.clip(scores, 1e-7, 1.0).astype(np.float64)
        cumulative = np.cumsum(clipped, dtype=np.float64) + cumulative_sum[entity]
        denominators = np.arange(
            prior_count + 1, prior_count + len(scores) + 1, dtype=np.float64
        )
        running_scores = (cumulative / denominators).astype(np.float32)
        if prior_count == 0:
            first_scores[entity] = scores[0]
        if first_alert_exposure[entity] == 0:
            crossing = np.flatnonzero(running_scores > threshold)
            if len(crossing):
                offset = int(crossing[0])
                first_alert_exposure[entity] = prior_count + offset + 1
                first_alert_time[entity] = float(times[left + offset])
        cumulative_sum[entity] = cumulative[-1]
        exposure_count[entity] = prior_count + len(scores)


def score_all_exposures(
    xgb_module: Any,
    torch_module: Any,
    matrix: np.ndarray,
    indices: np.ndarray,
    masks: np.ndarray,
    sequence_entities: np.ndarray,
    flow_times: np.ndarray,
    fold_of_entity: np.ndarray,
    parent_root: Path,
    seal: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    threshold = float(config["source_threshold_contract"]["threshold"])
    cumulative_sum = np.zeros(N_ENTITY, np.float64)
    exposure_count = np.zeros(N_ENTITY, np.int64)
    first_scores = np.full(N_ENTITY, np.nan, np.float32)
    first_alert_exposure = np.zeros(N_ENTITY, np.int64)
    first_alert_time = np.full(N_ENTITY, np.nan, np.float64)
    scored_flow = np.zeros(N_FLOW, np.bool_)
    receipts: list[dict[str, Any]] = []
    seal_models = {
        item["filename"]: item for item in seal["source_model_receipts"]
    }
    sequence_batch = int(config["sequence_batch"])
    for fold in range(N_FOLD):
        name = f"model_oof_semantic168_fold{fold}.json"
        booster, receipt = load_booster(
            xgb_module, parent_root / name, fold, seal_models[name]["sha256"]
        )
        gpu_guard(
            torch_module,
            float(config["resource_contract"]["runtime_gpu_floor_gib"]),
            f"semantic168/fold{fold}/全曝光推理前",
        )
        sequence_rows = np.flatnonzero(fold_of_entity[sequence_entities] == fold)
        predicted_count = 0
        started = time.time()
        for start in range(0, len(sequence_rows), sequence_batch):
            selected = sequence_rows[start : start + sequence_batch]
            index_block = np.asarray(indices[selected])
            valid = np.asarray(masks[selected]) > 0
            rows = np.asarray(index_block[valid], np.int64)
            entities = np.broadcast_to(
                np.asarray(sequence_entities[selected], np.int64)[:, None],
                valid.shape,
            )[valid]
            if scored_flow[rows].any():
                invalid(f"折 {fold} 推理出现重复流")
            scored_flow[rows] = True
            raw_scores = np.asarray(booster.inplace_predict(matrix[rows]), np.float32)
            if raw_scores.shape != (len(rows),) or not np.isfinite(raw_scores).all():
                invalid(f"折 {fold} 逐流分数形状异常或含非有限值")
            update_entity_states(
                entities,
                np.asarray(flow_times[rows], np.float64),
                raw_scores,
                threshold,
                cumulative_sum,
                exposure_count,
                first_scores,
                first_alert_exposure,
                first_alert_time,
            )
            predicted_count += len(rows)
            beat(
                f"semantic168/fold{fold}/全曝光OOF",
                min(start + sequence_batch, len(sequence_rows)),
                len(sequence_rows),
                started,
            )
        receipt["holdout_entity_count"] = int((fold_of_entity == fold).sum())
        receipt["predicted_flow_count"] = predicted_count
        receipts.append(receipt)
        del booster, sequence_rows
        torch_module.cuda.empty_cache()
    if not scored_flow.all() or int(exposure_count.sum()) != N_FLOW:
        invalid("三折 OOF 推理未恰好覆盖全部 LSPR23 流")
    if not np.isfinite(first_scores).all():
        invalid("首曝分数存在未覆盖实体")
    return {
        "first_scores": first_scores,
        "first_alert_exposure": first_alert_exposure,
        "first_alert_time": first_alert_time,
        "exposure_count": exposure_count,
        "model_receipts": receipts,
        "scored_flow_count": int(scored_flow.sum()),
    }


def distribution(values: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(values, np.float64)
    finite = finite[np.isfinite(finite)]
    if len(finite) == 0:
        return {"count": 0, "min": None, "median": None, "mean": None, "p95": None, "max": None}
    return {
        "count": int(len(finite)),
        "min": float(finite.min()),
        "median": float(np.median(finite)),
        "mean": float(finite.mean()),
        "p95": float(np.percentile(finite, 95)),
        "max": float(finite.max()),
    }


def late_event_summary(
    mask: np.ndarray,
    first_alert_exposure: np.ndarray,
    first_alert_time: np.ndarray,
    first_time: np.ndarray,
) -> dict[str, Any]:
    entity_ids = np.flatnonzero(mask).astype(np.int64, copy=False)
    delays = first_alert_exposure[mask] - 1
    elapsed = first_alert_time[mask] - first_time[mask]
    unique, counts = np.unique(first_alert_exposure[mask], return_counts=True)
    return {
        "entity_count": int(mask.sum()),
        "entity_set_sha256": sha256_array(entity_ids),
        "exposure_delay": distribution(delays),
        "time_delay": distribution(elapsed),
        "first_alert_exposure_histogram": [
            {"exposure_index": int(index), "entity_count": int(count)}
            for index, count in zip(unique, counts)
        ],
    }


def write_support_curve(
    path: Path,
    entity_labels: np.ndarray,
    exposure_count: np.ndarray,
    first_alert_exposure: np.ndarray,
    write_batch: int,
) -> int:
    import pyarrow as pa
    import pyarrow.parquet as pq

    maximum = int(exposure_count.max())
    benign = entity_labels == 0
    positive = entity_labels == 1
    support_all = np.bincount(exposure_count, minlength=maximum + 1).astype(np.int64)
    support_benign = np.bincount(
        exposure_count[benign], minlength=maximum + 1
    ).astype(np.int64)
    support_positive = np.bincount(
        exposure_count[positive], minlength=maximum + 1
    ).astype(np.int64)
    new_false = np.bincount(
        first_alert_exposure[benign & (first_alert_exposure > 0)],
        minlength=maximum + 1,
    ).astype(np.int64)
    new_true = np.bincount(
        first_alert_exposure[positive & (first_alert_exposure > 0)],
        minlength=maximum + 1,
    ).astype(np.int64)
    at_risk = np.cumsum(support_all[::-1], dtype=np.int64)[::-1]
    benign_at_risk = np.cumsum(support_benign[::-1], dtype=np.int64)[::-1]
    positive_at_risk = np.cumsum(support_positive[::-1], dtype=np.int64)[::-1]
    cumulative_false = np.cumsum(new_false, dtype=np.int64)
    cumulative_true = np.cumsum(new_true, dtype=np.int64)

    schema = pa.schema(
        [
            ("exposure_index", pa.int64()),
            ("entities_at_risk", pa.int64()),
            ("benign_at_risk", pa.int64()),
            ("positive_at_risk", pa.int64()),
            ("new_false_alerts", pa.int64()),
            ("new_true_alerts", pa.int64()),
            ("cum_false_entities", pa.int64()),
            ("cum_true_entities", pa.int64()),
            ("fpr_all_through_j", pa.float64()),
            ("dr_all_through_j", pa.float64()),
        ]
    )
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    writer = pq.ParquetWriter(partial, schema, compression="zstd")
    try:
        started = time.time()
        for start in range(1, maximum + 1, write_batch):
            stop = min(start + write_batch, maximum + 1)
            table = pa.table(
                {
                    "exposure_index": np.arange(start, stop, dtype=np.int64),
                    "entities_at_risk": at_risk[start:stop],
                    "benign_at_risk": benign_at_risk[start:stop],
                    "positive_at_risk": positive_at_risk[start:stop],
                    "new_false_alerts": new_false[start:stop],
                    "new_true_alerts": new_true[start:stop],
                    "cum_false_entities": cumulative_false[start:stop],
                    "cum_true_entities": cumulative_true[start:stop],
                    "fpr_all_through_j": cumulative_false[start:stop] / N_NEG_ENTITY,
                    "dr_all_through_j": cumulative_true[start:stop] / N_POS_ENTITY,
                },
                schema=schema,
            )
            writer.write_table(table)
            beat("完整曝光支持曲线", stop - 1, maximum, started)
    finally:
        writer.close()
    os.replace(partial, path)
    return maximum


def resource_receipt(torch_module: Any, started: float) -> dict[str, Any]:
    maximum_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_host_bytes = int(maximum_rss * (1 if sys.platform == "darwin" else 1024))
    return {
        "schema_version": "ch4-xgb-entity-exposure-lesion-resource-v1",
        "run_id": RUN_ID,
        "wall_seconds": time.time() - started,
        "peak_host_rss_bytes": peak_host_bytes,
        "cuda_device": torch_module.cuda.get_device_name(0),
        "cuda_peak_allocated_bytes": int(torch_module.cuda.max_memory_allocated(0)),
        "cuda_peak_reserved_bytes": int(torch_module.cuda.max_memory_reserved(0)),
        "new_models_trained": NEW_MODELS_TRAINED,
    }


def run(args: argparse.Namespace, config: dict[str, Any]) -> None:
    resolve_paths(args, config)
    seal = validate_threshold_seal(args.threshold_seal.resolve(), config)
    parent = validate_parent(args, config, seal)
    array_receipts = hash_allowed_arrays()
    if args.validate_inputs:
        print("CH4_ENTITY_EXPOSURE_LESION_INPUTS_VALID", flush=True)
        return

    protected = (
        "diagnostic_summary.json",
        "full_exposure_support_curve.parquet",
        "input_receipt.json",
        "resource_receipt.json",
        "manifest.json",
    )
    if any((args.out / name).exists() for name in protected):
        invalid(f"同名诊断制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    script_sha = sha256_file(Path(__file__).resolve())
    config_sha = sha256_file(args.config.resolve())

    log("阶段一：只读加载七个 LSPR23 数组并执行覆盖、实体和时间硬门")
    raw_values = guarded_source_load("X23")
    labels = guarded_source_load("y23")
    indices = guarded_source_load("I23")
    masks = guarded_source_load("M23")
    sequence_entities = guarded_source_load("E23")
    flow_entities = guarded_source_load("ent23")
    flow_times = guarded_source_load("t23_flow")
    structure = scan_source_structure(
        labels, indices, masks, sequence_entities, flow_entities, flow_times
    )
    entity_labels = structure["entity_labels"]
    entity_flow_counts = structure["entity_flow_counts"]
    fold_of_entity = make_folds(entity_labels, int(config["seed"]))
    fold_sha = sha256_array(fold_of_entity)
    if fold_sha != config["source_threshold_contract"]["fold_assignment_sha256"]:
        invalid("实体折号哈希与源阈值收据不符")
    fold_stats = fold_statistics(
        fold_of_entity,
        entity_labels,
        entity_flow_counts,
        structure["entity_positive_flow_counts"],
    )
    if fold_stats != parent["selection"].get("fold_stat"):
        invalid("实体三折统计与父选择收据不符")
    entity_key_sha = sha256_array(structure["entity_ids"])
    if (
        entity_key_sha != seal.get("entity_key_sha256")
        or entity_key_sha != config["source_threshold_contract"]["entity_key_sha256"]
        or fold_sha != seal.get("fold_assignment_sha256")
    ):
        invalid("实体集合或折号哈希与源阈值封印不符")

    log("阶段二：按第三章段内语义构造 semantic168；128 只作特征边界")
    semantic = build_semantic_matrix(CACHE / "X23.npy", indices, masks)
    del raw_values

    log("阶段三：三个父折模型各自只推理原 OOF 折，并跨段连续累计全部曝光")
    import torch
    import xgboost as xgb

    if xgb.__version__ != "3.2.0" or xgb.build_info().get("USE_CUDA") is not True:
        invalid(
            f"XGBoost 环境不符：version={xgb.__version__} "
            f"USE_CUDA={xgb.build_info().get('USE_CUDA')}"
        )
    if not torch.cuda.is_available():
        invalid("CUDA 不可用，拒绝以 CPU 冒充父折模型推理")
    scored = score_all_exposures(
        xgb,
        torch,
        semantic,
        indices,
        masks,
        sequence_entities,
        flow_times,
        fold_of_entity,
        args.parent_run_root.resolve(),
        seal,
        config,
    )
    del semantic, indices, masks, sequence_entities, flow_entities, labels
    torch.cuda.empty_cache()

    first_scores = scored["first_scores"]
    first_score_sha = sha256_array(first_scores)
    negative_first_score_sha = sha256_array(first_scores[entity_labels == 0])
    contract = config["source_threshold_contract"]
    if (
        first_score_sha != seal.get("score_sha256")
        or first_score_sha != contract["first_exposure_score_sha256"]
        or negative_first_score_sha != seal.get("negative_score_sha256")
        or negative_first_score_sha != contract["negative_first_exposure_score_sha256"]
    ):
        invalid("首曝分数预处理或父模型接口未逐位复现源阈值收据")
    threshold = float(contract["threshold"])
    raw_first_false = int(((first_scores > threshold) & (entity_labels == 0)).sum())
    if raw_first_false != contract["strictly_above_count"]:
        invalid("严格大于阈值的首曝良性实体数与封印不符")
    del first_scores

    first_alert = scored["first_alert_exposure"]
    first_alert_time = scored["first_alert_time"]
    benign = entity_labels == 0
    positive = entity_labels == 1
    false_first = int((benign & (first_alert == 1)).sum())
    false_all = int((benign & (first_alert > 0)).sum())
    true_first = int((positive & (first_alert == 1)).sum())
    true_all = int((positive & (first_alert > 0)).sum())
    late_positive = positive & (first_alert > 1)
    late_benign = benign & (first_alert > 1)
    fpr_first = false_first / N_NEG_ENTITY
    fpr_all = false_all / N_NEG_ENTITY
    dr_first = true_first / N_POS_ENTITY
    dr_all = true_all / N_POS_ENTITY
    if false_first != contract["strictly_above_count"] or fpr_first > 0.04:
        invalid("FPR(1) 未复现封印值或源阈值自身已违约")
    pathology_pass = fpr_all > 0.04 and int(late_positive.sum()) > 0

    log("阶段四：写出每个真实曝光序号的完整聚合支持曲线")
    curve_path = args.out / "full_exposure_support_curve.parquet"
    curve_rows = write_support_curve(
        curve_path,
        entity_labels,
        entity_flow_counts,
        first_alert,
        int(config["curve_write_batch"]),
    )
    if curve_rows != int(entity_flow_counts.max()):
        invalid("曝光曲线行数不等于最大实体实际曝光数")

    summary = {
        "schema_version": "ch4-xgb-entity-exposure-lesion-diagnostic-summary-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "source_year": "LSPR23",
        "evidence": {
            "screening_only": True,
            "formal": False,
            "formal_paper_evidence": False,
            "independent_test": False,
            "zero_training": True,
        },
        "threshold": {
            "value": threshold,
            "comparison_operator": ">",
            "source_threshold_file_sha256": contract["file_sha256"],
            "source_threshold_receipt_sha256": contract["receipt_sha256"],
            "score_preprocessing": contract["score_preprocessing"],
        },
        "metrics": {
            "FPR(1)": fpr_first,
            "FPR(all)": fpr_all,
            "DR(1)": dr_first,
            "DR(all)": dr_all,
            "false_entities_first_exposure": false_first,
            "false_entities_all_exposures": false_all,
            "true_entities_first_exposure": true_first,
            "true_entities_all_exposures": true_all,
            "N_late_positive": int(late_positive.sum()),
            "N_late_benign_false_alert": int(late_benign.sum()),
            "positive_entities_never_detected": int((positive & (first_alert == 0)).sum()),
            "benign_entities_never_alerted": int((benign & (first_alert == 0)).sum()),
        },
        "late_positive_detection": late_event_summary(
            late_positive,
            first_alert,
            first_alert_time,
            structure["first_time"],
        ),
        "late_benign_false_alert": late_event_summary(
            late_benign,
            first_alert,
            first_alert_time,
            structure["first_time"],
        ),
        "support_curve": {
            "filename": curve_path.name,
            "rows": curve_rows,
            "max_observed_entity_exposures": int(entity_flow_counts.max()),
            "exposure_cutoff": None,
            "denominator_policy": "全体同标签实体固定分母",
            "capture_scope": "LSPR23 冻结捕获内全部已记录曝光",
        },
        "integrity_assertions": {
            "target_year_arrays_read": TARGET_YEAR_ARRAYS_READ,
            "new_models_trained": NEW_MODELS_TRAINED,
            "oof_models_loaded": len(scored["model_receipts"]),
            "per_flow_scores_persisted": 0,
            "per_entity_scores_persisted": 0,
            "fold_membership_persisted": 0,
            "flow_coverage_count": structure["flow_coverage_count"],
            "duplicate_flow_coverage_count": structure[
                "duplicate_flow_coverage_count"
            ],
            "scored_flow_count": scored["scored_flow_count"],
            "within_segment_time_reversals": structure[
                "within_segment_time_reversals"
            ],
            "cross_segment_time_reversals": structure[
                "cross_segment_time_reversals"
            ],
            "exposure_curve_rows": curve_rows,
            "max_observed_entity_exposures": int(entity_flow_counts.max()),
            "source_threshold_match": True,
            "first_exposure_fpr_le_0_04": fpr_first <= 0.04,
        },
        "mechanical_verdict": {
            "qualified": pathology_pass,
            "rule": "(FPR(all) > 0.04) AND (N_late_positive > 0)",
            "verdict": (
                "MECHANISM1_PATHOLOGY_QUALIFIED"
                if pathology_pass
                else "MECHANISM1_REJECTED_NO_JOINT_PATHOLOGY"
            ),
            "fpr_all_strictly_above_budget": fpr_all > 0.04,
            "late_positive_exists": int(late_positive.sum()) > 0,
            "claim_boundary": "只裁决 LSPR23 源年联合病灶，不证明任何控制方法有效",
        },
    }
    summary_path = args.out / "diagnostic_summary.json"
    atomic_json(summary_path, summary)

    input_receipt = {
        "schema_version": "ch4-xgb-entity-exposure-lesion-input-receipt-v1",
        "run_id": RUN_ID,
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "parent": parent,
        "threshold_seal": {
            "path": str(args.threshold_seal.resolve()),
            "file_sha256": contract["file_sha256"],
            "receipt_sha256": contract["receipt_sha256"],
        },
        "arrays": array_receipts,
        "fold_assignment_sha256": fold_sha,
        "entity_key_sha256": entity_key_sha,
        "first_exposure_score_sha256": first_score_sha,
        "negative_first_exposure_score_sha256": negative_first_score_sha,
        "source_model_receipts": scored["model_receipts"],
        "source_year": "LSPR23",
        "target_year_arrays_read": TARGET_YEAR_ARRAYS_READ,
        "new_models_trained": NEW_MODELS_TRAINED,
        "oof_models_loaded": len(scored["model_receipts"]),
        "per_flow_scores_persisted": 0,
        "exposure_cutoff": None,
    }
    input_path = args.out / "input_receipt.json"
    atomic_json(input_path, input_receipt)
    resource_path = args.out / "resource_receipt.json"
    atomic_json(resource_path, resource_receipt(torch, started))

    manifest_names = (
        "diagnostic_summary.json",
        "full_exposure_support_curve.parquet",
        "input_receipt.json",
        "resource_receipt.json",
    )
    manifest = {
        "schema_version": "ch4-xgb-entity-exposure-lesion-manifest-v1",
        "run_id": RUN_ID,
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "target_year_arrays_read": TARGET_YEAR_ARRAYS_READ,
        "new_models_trained": NEW_MODELS_TRAINED,
        "per_flow_scores_persisted": 0,
        "per_entity_scores_persisted": 0,
        "fold_membership_persisted": 0,
        "files": {},
    }
    for name in manifest_names:
        path = args.out / name
        if not path.is_file() or path.stat().st_size <= 0:
            invalid(f"必需诊断制品缺失：{path}")
        manifest["files"][name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    atomic_json(args.out / "manifest.json", manifest)
    log(
        f"诊断完成：FPR(1)={fpr_first:.10f} FPR(all)={fpr_all:.10f} "
        f"DR(1)={dr_first:.10f} DR(all)={dr_all:.10f} "
        f"N_late_positive={int(late_positive.sum())} verdict={summary['mechanical_verdict']['verdict']}"
    )


def main() -> int:
    args = parse_args()
    try:
        if not args.config.is_file():
            invalid(f"配置缺失：{args.config}")
        config = load_json(args.config)
        validate_config(config)
        if args.validate_config:
            print("CH4_ENTITY_EXPOSURE_LESION_CONFIG_VALID", flush=True)
            return 0
        run(args, config)
        return 0
    except InputContractError as error:
        print(f"INVALID_INPUT_CONTRACT: {error}", file=sys.stderr, flush=True)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
