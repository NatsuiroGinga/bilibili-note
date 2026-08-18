"""跨年度实体级评价 Q0：运行入口与协议对齐门。

阶段：
- `preflight`  只读核验冻结缓存、哈希、最终区隔离与内存，不训练。
- `alignment-gate`  只跑 `B0`（逐流 XGBoost，复现 Dijk 2026 §5.6 配置），
  立即判定协议对齐门；不通过即写阻断收据并停止，不跑后续变体。
- `full`  阶段二（`B1`/`B2`/`M1`/`M1+B1`/`M3-*`）。只有协议对齐门通过后才允许实现与运行。

纪律：逐流分数先封存再连接目标开发标签；实体键只用于分组；最终封存区断言写入代码。
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import sys
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from flow_probe.crossyear_entity_eval_contract import (
    DIJK_LSPR24_OP_POSITIVE_RATE,
    DIJK_XGBOOST_PARAMS,
    ENTITY_KEY_NAME,
    EntityEvalError,
    PREREGISTERED,
    RUN_NAME,
    alignment_gate_decision,
    assert_no_final_region,
    describe_variants,
    frozen_config,
    memory_snapshot,
    read_json,
    seal_array,
    variant_slug,
    write_json,
)
from flow_probe.crossyear_entity_eval_data import (
    dataset_receipts,
    input_receipt,
    load_role,
    open_deferred_labels,
    verify_artifact_hashes,
)

logger = logging.getLogger("crossyear_entity_eval")

STAGES: tuple[str, ...] = ("preflight", "alignment-gate", "full")

CONSUMED_ARTIFACTS = (
    "source-train:cache",
    "source-train:labels",
    "source-validation:cache",
    "source-validation:labels",
    "target-prefix:cache",
    "target-development:cache",
    "target-development:labels",
)


def _configure_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for handler in list(root.handlers):
        root.removeHandler(handler)
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root.addHandler(stream)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def _write_status(output_root: Path, state: str, detail: Mapping[str, Any]) -> None:
    write_json(
        output_root / "status.json",
        {
            "run_name": RUN_NAME,
            "state": state,
            "final_accessed": False,
            "screening_only": True,
            "formal_paper_evidence": False,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            **dict(detail),
        },
    )


def _average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    """平均精确率（与 sklearn `average_precision_score` 同口径）。"""
    from sklearn.metrics import average_precision_score

    return float(average_precision_score(np.asarray(labels, dtype=np.uint8), np.asarray(scores, dtype=np.float64)))


def _build_b0(seed: int) -> Any:
    try:
        from xgboost import XGBClassifier
    except (ImportError, OSError) as error:  # 依赖缺失必须显式失败，不静默降级
        raise EntityEvalError(f"XGBoost 不可用：{error}") from error
    params = dict(DIJK_XGBOOST_PARAMS)
    return XGBClassifier(
        n_estimators=int(params["n_estimators"]),
        max_depth=int(params["max_depth"]),
        learning_rate=float(params["learning_rate"]),
        subsample=float(params["subsample"]),
        colsample_bytree=float(params["colsample_bytree"]),
        reg_lambda=float(params["reg_lambda"]),
        min_child_weight=float(params["min_child_weight"]),
        max_bin=int(params["max_bin"]),
        objective=str(params["objective"]),
        eval_metric=str(params["eval_metric"]),
        tree_method=str(params["tree_method"]),
        device="cpu",
        n_jobs=8,
        random_state=seed,
        verbosity=1,
    )


def run(*, dataset_root: Path, output_root: Path, stage: str, seed: int) -> Mapping[str, Any]:
    """执行指定阶段并返回摘要。"""
    if stage not in STAGES:
        raise EntityEvalError(f"未知阶段：{stage}")
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    _configure_logging(output_root / "logs" / f"{stage}.log")
    started = time.perf_counter()
    logger.info("[阶段] 开始 stage=%s seed=%d 运行根=%s", stage, seed, output_root)
    _write_status(output_root, "running", {"stage": stage, "seed": seed})
    snapshots = [memory_snapshot("start")]

    # ---- 1. 收据、哈希与最终区隔离 ----
    dataset_manifest, experiment_manifest, cache_root = dataset_receipts(dataset_root)
    logger.info("[门禁] 冻结缓存根=%s", cache_root)
    verified = verify_artifact_hashes(dataset_manifest, CONSUMED_ARTIFACTS)
    logger.info("[门禁] %d 个消费制品 SHA-256 全部匹配", len(verified))

    splits = dataset_manifest.get("splits")
    if not isinstance(splits, dict) or "target_final_cut_ns" not in splits:
        raise EntityEvalError("数据集收据缺少切分收据")
    final_cut_ns = int(splits["target_final_cut_ns"])

    # ---- 2. 分批装载 ----
    roles = {
        "source-train": load_role(cache_root, "source-train", label_mode="load"),
        "source-validation": load_role(cache_root, "source-validation", label_mode="load"),
        "target-development": load_role(cache_root, "target-development", label_mode="defer"),
    }
    snapshots.append(memory_snapshot("loaded"))

    max_available_ns = max(int(data.available_ns.max()) for data in roles.values())
    isolation = assert_no_final_region(
        consumed_paths=[Path(p) for data in roles.values() for p in data.feature_paths],
        max_available_ns=max_available_ns,
        target_final_cut_ns=final_cut_ns,
        dataset_manifest=dataset_manifest,
    )
    logger.info(
        "[门禁] 最终封存区隔离通过：最大 available_ns 距最终切点 %.3f 秒", isolation["margin_seconds"]
    )

    config = frozen_config(
        {
            "seed": seed,
            "stage": stage,
            "dataset_root": str(dataset_root),
            "cache_root": str(cache_root),
            "consumed_artifacts": list(CONSUMED_ARTIFACTS),
            "variant_catalog": [dict(item) for item in describe_variants()],
            "training_role": "source-train",
            "evaluation_role": "target-development",
            "platform": platform.platform(),
        }
    )
    config_path = output_root / "config.json"
    if config_path.is_file():
        existing = read_json(config_path)
        frozen_existing = existing.get("preregistered")
        if frozen_existing != dict(PREREGISTERED):
            raise EntityEvalError("已存在的 config.json 预注册判据与合同不一致，拒绝覆盖")
    write_json(config_path, config)
    write_json(
        output_root / "input-receipt.json",
        input_receipt(dataset_manifest, roles, verified),
    )
    write_json(
        output_root / "split-receipt.json",
        {
            "splits": splits,
            "role_rows": dataset_manifest.get("role_rows"),
            "role_sequences": dataset_manifest.get("role_sequences"),
            "role_row_limits": dataset_manifest.get("role_row_limits"),
            "isolation": isolation,
            "entity_key": ENTITY_KEY_NAME,
            "entity_counts": {role: data.entity_unique_count for role, data in roles.items()},
            "final_accessed": False,
        },
    )

    if stage == "preflight":
        _write_status(
            output_root,
            "preflight_passed",
            {"stage": stage, "seed": seed, "memory": snapshots, "elapsed_seconds": time.perf_counter() - started},
        )
        logger.info("[阶段] preflight 通过，耗时 %.1f 秒", time.perf_counter() - started)
        return {"stage": stage, "passed": True}

    # ---- 3. B0：逐流 XGBoost，复现 Dijk 2026 配置 ----
    train = roles["source-train"]
    validation = roles["source-validation"]
    target = roles["target-development"]
    if train.labels is None or validation.labels is None:
        raise EntityEvalError("源年度标签缺失")
    if set(np.unique(train.labels).tolist()) != {0, 1}:
        raise EntityEvalError("source-train 必须同时含良性与恶意标签")

    model = _build_b0(seed)
    logger.info(
        "[B0] 开始训练：训练行=%d 特征维=%d 树=%d 深度=%d 学习率=%.3f",
        train.features.shape[0],
        train.features.shape[1],
        DIJK_XGBOOST_PARAMS["n_estimators"],
        DIJK_XGBOOST_PARAMS["max_depth"],
        DIJK_XGBOOST_PARAMS["learning_rate"],
    )
    fit_started = time.perf_counter()
    model.fit(train.features, train.labels)
    fit_seconds = time.perf_counter() - fit_started
    logger.info("[B0] 训练完成，耗时 %.1f 秒", fit_seconds)
    snapshots.append(memory_snapshot("b0-fitted"))

    validation_scores = model.predict_proba(validation.features)[:, 1].astype(np.float64)
    source_validation_ap = _average_precision(validation.labels, validation_scores)
    logger.info("[B0] 源年度验证逐流 AP=%.6f（诊断用）", source_validation_ap)

    infer_started = time.perf_counter()
    target_scores = model.predict_proba(target.features)[:, 1].astype(np.float32)
    infer_seconds = time.perf_counter() - infer_started
    logger.info("[B0] 目标开发区打分完成，行=%d 耗时 %.1f 秒", target_scores.shape[0], infer_seconds)

    # ---- 4. 先封存逐流分数，再打开目标标签 ----
    prediction_dir = output_root / "predictions" / variant_slug("B0")
    seal = seal_array(prediction_dir / "flow-scores.npy", target_scores, kind="flow_scores")
    seal_record = {
        "variant": "B0",
        "display_name": "逐流XGBoost-Dijk配置复现",
        "flow_scores": seal,
        "target_sample_id_sha256": target.sample_id_sha256,
        "sealed_before_label_join": True,
        "entity_scores": None,
        "note": "阶段一只产出逐流分数；实体聚合属于阶段二。",
    }
    write_json(prediction_dir / "seal.json", seal_record)
    logger.info("[封存] B0 逐流分数已封存 sha256=%s", seal["array_sha256"])

    labels, keep, dropped = open_deferred_labels(cache_root, target)
    evaluated_labels = labels[keep].astype(np.uint8)
    evaluated_scores = target_scores[keep].astype(np.float64)
    positives = int((evaluated_labels == 1).sum())
    prevalence = positives / max(evaluated_labels.shape[0], 1)
    flow_ap = _average_precision(evaluated_labels, evaluated_scores)
    logger.info("[B0] 跨年度目标开发区逐流 AP=%.6f 阳性率=%.6f", flow_ap, prevalence)
    snapshots.append(memory_snapshot("b0-evaluated"))

    gate = alignment_gate_decision(flow_ap)
    diagnostics = {
        "target_development_positive_flow_count": positives,
        "target_development_flow_count": int(evaluated_labels.shape[0]),
        "target_development_prevalence": prevalence,
        "ap_over_prevalence_lift": flow_ap / prevalence if prevalence > 0 else None,
        "dijk2026_reference": {
            "flow_ap": PREREGISTERED["alignment_gate"]["flow_ap_target"],
            "lspr24_op_positive_rate": DIJK_LSPR24_OP_POSITIVE_RATE,
            "ap_over_prevalence_lift": PREREGISTERED["alignment_gate"]["flow_ap_target"] / DIJK_LSPR24_OP_POSITIVE_RATE,
            "source": "Dijk 2026 表 5（AP）与表 8（OP 诱导阳性率）",
        },
        "source_validation_flow_ap": source_validation_ap,
        "dropped_non_binary_label_rows": dropped,
        "training_rows": int(train.features.shape[0]),
        "training_positive_rows": int((train.labels == 1).sum()),
        "feature_dimension": int(train.features.shape[1]),
        "pair_hash_keep_thresholds": dataset_manifest.get("pair_hash_keep_thresholds"),
        "prescreen_excluded_rows": dataset_manifest.get("isolated_rows"),
        "role_row_limits": dataset_manifest.get("role_row_limits"),
    }
    write_json(
        output_root / "alignment-gate.json",
        {"gate": gate, "diagnostics": diagnostics, "seal": seal_record, "final_accessed": False},
    )
    write_json(
        output_root / "metrics" / "B0.json",
        {
            "variant": "B0",
            "display_name": "逐流XGBoost-Dijk配置复现",
            "seed": seed,
            "xgboost_params": dict(DIJK_XGBOOST_PARAMS),
            "target_development_flow_ap": flow_ap,
            "source_validation_flow_ap": source_validation_ap,
            "diagnostics": diagnostics,
            "resource": {
                "fit_seconds": fit_seconds,
                "inference_seconds": infer_seconds,
                "memory_snapshots": snapshots,
            },
            "final_accessed": False,
        },
    )

    decision = {
        "stage": stage,
        "alignment_gate": gate,
        "main_gate": "未评估：协议对齐门未通过" if not gate["passed"] else "待阶段二评估",
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    write_json(output_root / "decision.json", decision)

    if not gate["passed"]:
        _write_status(
            output_root,
            "blocked_alignment_gate",
            {
                "stage": stage,
                "seed": seed,
                "flow_ap": flow_ap,
                "required_interval": gate["interval"],
                "action": gate["action"],
                "memory": snapshots,
                "elapsed_seconds": time.perf_counter() - started,
            },
        )
        logger.error(
            "[门禁] 协议对齐门不通过：逐流 AP=%.6f 不在 [%.4f, %.4f]，停止，不进入 M1/M2/M3",
            flow_ap,
            gate["interval"][0],
            gate["interval"][1],
        )
        return {"stage": stage, "passed": False, "flow_ap": flow_ap, "gate": gate, "diagnostics": diagnostics}

    if stage == "alignment-gate":
        _write_status(
            output_root,
            "alignment_gate_passed",
            {"stage": stage, "seed": seed, "flow_ap": flow_ap, "memory": snapshots, "elapsed_seconds": time.perf_counter() - started},
        )
        return {"stage": stage, "passed": True, "flow_ap": flow_ap, "gate": gate, "diagnostics": diagnostics}

    raise EntityEvalError(
        "阶段二（B1/B2/M1/M1+B1/M3-同期/M3-冻结）尚未实现：按实施计划 §7，"
        "只有协议对齐门通过后才允许实现并运行实体级评价变体。"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="跨年度实体级评价与决策层适应 Q0")
    parser.add_argument("--dataset-root", type=Path, required=True, help="冻结跨年度有界缓存根")
    parser.add_argument("--output-root", type=Path, required=True, help="运行根")
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        result = run(dataset_root=args.dataset_root, output_root=args.output_root, stage=args.stage, seed=args.seed)
    except EntityEvalError as error:
        logger.error("运行失败：%s", error)
        _write_status(Path(args.output_root), "failed", {"stage": args.stage, "reason": str(error)})
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if result.get("passed") else 3


if __name__ == "__main__":
    raise SystemExit(main())
