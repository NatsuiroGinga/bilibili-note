# -*- coding: utf-8 -*-
"""第四章 D1/D2 本机筛选：MLP 底座曝光病灶与长度桶条件风险再确认。

输入：D0-local 三折折外检查点 + LSPR23 冻结缓存。每个实体只由未见过它的
折外模型打分（OOF），随后全程 NumPy 决策层计算：

D1 曝光病灶（复刻 XGB 链口径）：
  在良性实体的首次曝光分数上把阈值校准到实体 FPR=4%（B0），
  再在全部曝光（路径最大 ≥ 同一阈值，B1）下测 FPR/DR。
  病灶门：FPR(B1) > 0.04 且 迟到检出实体数 > 0。

D2 长度桶条件风险：
  把路径最大分数按池化 4% 实体 FPR 重新校准阈值（M0'，无证书），
  按实体最终观测流数分五桶测逐桶 FPR。
  病灶门：存在 101-1000 或 1001+ 桶 FPR > 0.04。
  （在线因果分层留给 S_a 合同；诊断沿用既有事后口径以便与 XGB 链对照。）

证据边界：``screening_only=true``，fp32 折外模型（本机），结果不进论文；
正式再确认在服务器资源恢复后按冻结合同重跑。LSPR24 零读取。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch4_mlp_o11_oof_fold_models as d0
from ch4_mlp_o11_oof_fold_models_local_screen import LocalFullMLP, prepare, atomic_json

RUN_ID = "ch4-mlp-o11-pathology-diagnostics-local-screen-v1"
D0_RUN_ID = "ch4-mlp-o11-oof-fold-models-local-screen-v1"
SEQ_LEN = 128
BUDGET_FPR = 0.04
LENGTH_BUCKETS = ((1, 2), (3, 10), (11, 100), (101, 1000), (1001, None))
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def oof_flow_scores(
    context: dict[str, Any],
    X: np.ndarray,
    d0_root: Path,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """每个实体由其折外模型打分；返回逐流分数与 seen 掩码。"""
    source = context["source"]
    I23, M23, E23 = source["I23"], source["M23"], source["E23"]
    fold_of_entity = context["fold_of_entity"]
    flow_count = len(source["y23"])
    scores = np.zeros(flow_count, dtype=np.float32)
    seen = np.zeros(flow_count, dtype=bool)
    for fold in range(3):
        checkpoint_path = d0_root / "checkpoints" / f"selected-O11-fold{fold}.pt"
        payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if payload.get("run_id") != D0_RUN_ID or payload.get("fold") != fold:
            raise RuntimeError(f"fold{fold} 检查点身份不符")
        model = LocalFullMLP(aggregate=True).to(device)
        model.load_state_dict(payload["model"])
        model.eval()
        rows = np.flatnonzero(fold_of_entity[E23] == fold)
        log(f"fold{fold} 折外打分：{len(rows):,} 序列")
        with torch.no_grad():
            for start in range(0, len(rows), 1024):
                chunk = rows[start : start + 1024]
                indices = I23[chunk][:, :SEQ_LEN]
                valid_np = M23[chunk][:, :SEQ_LEN] > 0
                values = torch.from_numpy(X[indices.reshape(-1)]).reshape(len(chunk), SEQ_LEN, 83).to(device)
                valid = torch.from_numpy(valid_np).to(device)
                probabilities = torch.sigmoid(model(values, valid)).cpu().numpy()
                flat_ids = indices.reshape(-1)[valid_np.reshape(-1)]
                scores[flat_ids] = probabilities.reshape(-1)[valid_np.reshape(-1)]
                seen[flat_ids] = True
        del model
    if not seen.all():
        log(f"披露：{int((~seen).sum()):,} 条流未被任何序列覆盖（按未见处理）")
    return scores, seen


def build_flow_entity(source: dict[str, Any]) -> np.ndarray:
    I23, M23, E23 = source["I23"], source["M23"], source["E23"]
    flow_count = len(source["y23"])
    flow_entity = np.full(flow_count, -1, dtype=np.int64)
    valid = M23 > 0
    owners = np.broadcast_to(E23[:, None], I23.shape)
    flow_entity[I23[valid]] = owners[valid]
    if (flow_entity < 0).any():
        log(f"披露：{int((flow_entity < 0).sum()):,} 条流不在任何序列内")
    return flow_entity


def entity_tables(
    scores: np.ndarray,
    seen: np.ndarray,
    flow_entity: np.ndarray,
    entity_labels: np.ndarray,
) -> dict[str, np.ndarray]:
    """按（实体，冻结流索引升序）排序，产出首曝分数、路径最大、长度。"""
    flow_ids = np.flatnonzero(seen & (flow_entity >= 0))
    entities = flow_entity[flow_ids]
    order = np.lexsort((flow_ids, entities))
    ordered_flow = flow_ids[order]
    ordered_entity = entities[order]
    starts = np.flatnonzero(np.r_[True, ordered_entity[1:] != ordered_entity[:-1]])
    lengths = np.diff(np.r_[starts, len(ordered_entity)]).astype(np.int64)
    entity_ids = ordered_entity[starts]
    ordered_scores = scores[ordered_flow]
    first_scores = np.zeros(len(entity_labels), dtype=np.float32)
    path_max = np.zeros(len(entity_labels), dtype=np.float32)
    entity_length = np.zeros(len(entity_labels), dtype=np.int64)
    first_scores[entity_ids] = ordered_scores[starts]
    path_max[entity_ids] = np.maximum.reduceat(ordered_scores, starts)
    entity_length[entity_ids] = lengths
    covered = np.zeros(len(entity_labels), dtype=bool)
    covered[entity_ids] = True
    if not covered.all():
        raise RuntimeError(f"{int((~covered).sum())} 个实体无任何被打分流")
    return {"first": first_scores, "path_max": path_max, "length": entity_length}


def calibrate_threshold(benign_scores: np.ndarray, budget: float) -> float:
    """良性实体分数上取实体 FPR≤budget 的最小可达阈值（并列组整体处理）。"""
    ordered = np.sort(benign_scores)[::-1]
    allowed = int(len(ordered) * budget)
    candidates = np.unique(ordered)[::-1]
    for threshold in candidates:
        if int((ordered >= threshold).sum()) <= allowed:
            return float(threshold)
    return float(np.nextafter(ordered[0], np.inf))


def rates(entity_scores: np.ndarray, labels: np.ndarray, threshold: float) -> dict[str, Any]:
    alerts = entity_scores >= threshold
    benign = labels == 0
    positive = labels == 1
    return {
        "threshold": threshold,
        "entity_fpr": float((alerts & benign).sum() / max(int(benign.sum()), 1)),
        "entity_dr": float((alerts & positive).sum() / max(int(positive.sum()), 1)),
        "false_positive_entities": int((alerts & benign).sum()),
        "true_positive_entities": int((alerts & positive).sum()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章 D1/D2 本机病灶诊断（MLP 底座，筛选级）")
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--d0-root", default=f"runs/diagnostics/{D0_RUN_ID}")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    args = parser.parse_args()
    cache_root = Path(args.cache_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    context = prepare(cache_root)
    X = np.load(cache_root / "X23.npy")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    log(f"设备 {device.type}；折哈希 {context['fold_sha'][:16]}…")
    scores, seen = oof_flow_scores(context, X, Path(args.d0_root), device)
    flow_entity = build_flow_entity(context["source"])
    labels = context["entity_labels"]
    tables = entity_tables(scores, seen, flow_entity, labels)
    benign = labels == 0
    positive = labels == 1

    # D1 曝光病灶：首曝校准 → 全曝光复用同一阈值
    tau_first = calibrate_threshold(tables["first"][benign], BUDGET_FPR)
    b0 = rates(tables["first"], labels, tau_first)
    b1 = rates(tables["path_max"], labels, tau_first)
    late_positive = int(((tables["path_max"] >= tau_first) & (tables["first"] < tau_first) & positive).sum())
    d1_gate = b1["entity_fpr"] > BUDGET_FPR and late_positive > 0

    # D2 长度桶：池化路径最大校准 → 逐桶 FPR
    tau_pooled = calibrate_threshold(tables["path_max"][benign], BUDGET_FPR)
    m0 = rates(tables["path_max"], labels, tau_pooled)
    buckets: dict[str, Any] = {}
    long_bucket_violation = False
    for low, high in LENGTH_BUCKETS:
        key = f"{low}-{high if high else '+'}"
        in_bucket = (tables["length"] >= low) & (tables["length"] <= (high or np.iinfo(np.int64).max))
        bucket_labels = labels[in_bucket]
        bucket_scores = tables["path_max"][in_bucket]
        stats = rates(bucket_scores, bucket_labels, tau_pooled)
        stats.update({
            "entities": int(in_bucket.sum()),
            "benign_entities": int((bucket_labels == 0).sum()),
            "positive_entities": int((bucket_labels == 1).sum()),
        })
        buckets[key] = stats
        if low >= 101 and stats["entity_fpr"] > BUDGET_FPR:
            long_bucket_violation = True

    result = {
        "schema_version": "ch4-mlp-o11-pathology-local-screen-v1",
        "run_id": RUN_ID,
        "screening_only": True,
        "formal_paper_evidence": False,
        "target_year_arrays_read": 0,
        "precision": "fp32",
        "device_type": device.type,
        "fold_assignment_sha256": context["fold_sha"],
        "budget_entity_fpr": BUDGET_FPR,
        "d1_exposure_pathology": {
            "first_exposure_calibrated": b0,
            "all_exposure_same_threshold": b1,
            "late_detected_positive_entities": late_positive,
            "gate_fpr_all_gt_budget_and_late_gt_0": bool(d1_gate),
        },
        "d2_length_bucket_conditional_risk": {
            "pooled_path_max_calibrated": m0,
            "buckets": buckets,
            "gate_some_long_bucket_fpr_gt_budget": bool(long_bucket_violation),
        },
    }
    atomic_json(output_root / "pathology-results.json", result)
    log(f"D1 门={'过' if d1_gate else '不过'}：FPR(B1)={b1['entity_fpr']:.6f} 迟到TP={late_positive}")
    log(f"D2 门={'过' if long_bucket_violation else '不过'}：各桶 FPR=" + " ".join(
        f"{key}:{value['entity_fpr']:.4f}" for key, value in buckets.items()))
    print("LOCAL_SCREEN_D1D2_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
