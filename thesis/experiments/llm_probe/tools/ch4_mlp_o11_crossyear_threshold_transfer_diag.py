# -*- coding: utf-8 -*-
"""第四章跨年阈值迁移诊断：MLP O11 底座源年校准阈值搬到 LSPR24 的失配幅度存在性诊断。

研究问题（一句话）：源年校准的告警阈值搬到目标年后，实际误报率与检出率偏离多少？
这是第四章"跨年度阈值失配"维度在 MLP 底座上的存在性诊断——XGB 底座既有诊断
（ch4-drift-v2）显示源阈值只用掉 38% 误报预算、检出率少 6.5 点，MLP 底座此前未测过。

协议（对齐任务简报与恢复卡 §5.1"校准与评价须用同一模型"教训）：
1. 模型：第三章胜出 O11 冻结检查点（bf16 schema，state dict = encoder/fusion/output/p_log），
   校准与评价用同一个模型对象，不跨模型、不跨检查点。
2. 源年校准（部署现实口径）：只用协议 A 冻结切分的源年验证区序列（LSPR23 validation_rows，
   与训练区实体不相交），logit 空间路径最大分数上把阈值校准到实体 FPR=4%（并列组整体处理）。
   跳过 sigmoid 直接用原始 logit，避免 float32 sigmoid 在高置信区间饱和压缩次序统计的假象
   （单调变换不改变实体排序，只影响阈值的数值单位）。
3. 目标年评价：LSPR24 全量单次前向（bf16 autocast，逐流 logit）→ 实体路径最大聚合
   （实体键：s24|d24 无向对，与 ch3 bf16 工具的目标年口径一致）→ 在迁移阈值（步骤 2 产出，
   零目标年参与选择）下测实际实体 FPR/DR。
4. 对照点：目标年事后 4% 参考阈值（用目标标签重新校准，只作病灶存在性证明，明确不可部署）
   下的 FPR/DR；两者差即失配幅度。

证据边界：screening_only=true（本运行不进入论文正式结果或路线总控"已完成事实"）；
target_informed=true（读取目标年标签用于评价与事后参考阈值校准，但迁移阈值本身零目标年
参与）；formal_paper_evidence=false；LSPR24 数组只加载一次，一次前向覆盖全部评价。
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch3_full_mlp_complete_entity_lp_protocol_a_q0 as legacy
import ch3_full_mlp_complete_entity_lp_protocol_a_q0_bf16 as bf16
import neural_precision_runtime as precision

RUN_ID = "ch4-mlp-o11-crossyear-threshold-transfer-diag-v1"
CELL = "O11"
CHECKPOINT_SCHEMA = "ch3-full-mlp-bf16-selected-checkpoint-v1"
SOURCE_RUN_ID = bf16.RUN_ID
SEQ_LEN = 128
BUDGET_FPR = 0.04
EXPECTED_SOURCE_SPLIT = {
    "entity_count": 150_680,
    "train_sequences": 208_598,
    "validation_sequences": 22_444,
    "train_validation_row_intersection": 0,
}
EXPECTED_TARGET_ENTITY_COUNT = 47_115
EXPECTED_TARGET_POSITIVE_ENTITIES = 752
# 复刻 precision.autocast_context 所需的最小 profile 字典：本工具是 screening_only 诊断，
# 不引入完整精度合同文件加载，只保留与冻结 bf16 训练身份一致的三个字段。
_PROFILE = {"device_type": "cuda", "autocast": True, "compute_dtype": "bfloat16"}
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def load_checkpoint(path: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if payload.get("schema_version") != CHECKPOINT_SCHEMA:
        raise RuntimeError(f"检查点 schema 不符：{path}")
    identity = payload.get("identity", {})
    if identity.get("run_id") != SOURCE_RUN_ID or identity.get("cell") != CELL:
        raise RuntimeError(f"检查点身份不符（期望 run_id={SOURCE_RUN_ID} cell={CELL}）：{identity}")
    return payload["model"], identity, legacy.sha256_file(path)


def build_model(device: torch.device) -> torch.nn.Module:
    model = bf16.FullCapacityMLPBF16(83, 8, 512, 0.1, True)
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != 2_144_258:
        raise RuntimeError(f"框架实测参数量不符：{actual}")
    return model.to(device)


def score_rows_logit(
    model: torch.nn.Module,
    rows: np.ndarray,
    gX: torch.Tensor,
    gI: torch.Tensor,
    gM: torch.Tensor,
    device: torch.device,
    batch_size: int = 2048,
) -> tuple[np.ndarray, np.ndarray]:
    """给定源年序列行号，前向计算逐流 logit（跳过 sigmoid）。"""
    predictions: list[np.ndarray] = []
    flow_ids_all: list[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(rows), batch_size):
            selected = torch.from_numpy(rows[start : start + batch_size]).to(device)
            indices = gI[selected][:, :SEQ_LEN]
            valid = gM[selected][:, :SEQ_LEN] > 0.5
            batch = indices.shape[0]
            values = gX[indices.reshape(-1)].reshape(batch, SEQ_LEN, gX.shape[1])
            with precision.autocast_context(_PROFILE, device.type, torch):
                logits = model(values, valid)
            logits32 = logits.float()
            mask = valid.reshape(-1)
            predictions.append(logits32.reshape(-1)[mask].cpu().numpy())
            flow_ids_all.append(indices.reshape(-1)[mask].cpu().numpy())
    return np.concatenate(predictions), np.concatenate(flow_ids_all)


def score_target_logit(
    model: torch.nn.Module,
    X: np.ndarray,
    I: np.ndarray,
    M: np.ndarray,
    flow_count: int,
    device: torch.device,
    batch_size: int = 2048,
) -> tuple[np.ndarray, np.ndarray]:
    """LSPR24 全量单次前向：逐流 logit（跳过 sigmoid），覆盖 I/M 的全部行。"""
    gX = torch.from_numpy(X).to(device)
    gI = torch.from_numpy(I).to(device)
    gM = torch.from_numpy(M).to(device)
    scores = torch.zeros(flow_count, dtype=torch.float32, device=device)
    seen = torch.zeros(flow_count, dtype=torch.bool, device=device)
    model.eval()
    heartbeat_stride = batch_size * 1000
    with torch.no_grad():
        for start in range(0, len(gI), batch_size):
            indices = gI[start : start + batch_size][:, :SEQ_LEN]
            valid = gM[start : start + batch_size][:, :SEQ_LEN] > 0.5
            batch = indices.shape[0]
            values = gX[indices.reshape(-1)].reshape(batch, SEQ_LEN, gX.shape[1])
            with precision.autocast_context(_PROFILE, device.type, torch):
                logits = model(values, valid)
            logits32 = logits.float()
            flow_ids = indices.reshape(-1)
            mask = valid.reshape(-1)
            scores[flow_ids[mask]] = logits32.reshape(-1)[mask]
            seen[flow_ids[mask]] = True
            if start % heartbeat_stride == 0:
                log(f"目标年前向进度：{start:,}/{len(gI):,}")
    result = scores.cpu().numpy(), seen.cpu().numpy()
    del gX, gI, gM, scores, seen
    torch.cuda.empty_cache()
    return result


def calibrate_threshold(benign_scores: np.ndarray, budget: float) -> float:
    """良性实体分数上取实体 FPR<=budget 的最小可达阈值（并列组整体处理，即在预算内尽量压低阈值）。

    实现说明（2026-08-27 修复）：候选阈值按降序遍历，只要 count(scores>=threshold)<=allowed
    就持续下调阈值并记录为当前最优解，直到下一个候选会突破预算才停止，返回停止前的最优解。
    参照实现 ``tools/ch4_mlp_o11_pathology_diagnostics_local_screen.py`` 的同名函数在“遇到第一个
    满足条件的候选就立即返回”，由于最高候选恒满足 count=1<=allowed，会直接返回全局最高良性分数，
    实际 FPR far below 预算（本工具用纯 Python 合成数据验证：10 元素、budget=0.4、allowed=4 时，
    旧实现返回 threshold=10/realized_fpr=0.1，未用满 4 个允许假阳性名额；本实现返回
    threshold=7/realized_fpr=0.4，与预算目标一致）。本函数是独立修复实现，不复用旧版逐候选提前
    return 的控制流。
    """
    ordered = np.sort(benign_scores)[::-1]
    allowed = int(len(ordered) * budget)
    candidates = np.unique(ordered)[::-1]
    best = float(np.nextafter(ordered[0], np.inf))
    for threshold in candidates:
        count = int((ordered >= threshold).sum())
        if count <= allowed:
            best = float(threshold)
        else:
            break
    return best


def rates(entity_scores_arr: np.ndarray, labels: np.ndarray, threshold: float) -> dict[str, Any]:
    alerts = entity_scores_arr >= threshold
    benign = labels == 0
    positive = labels == 1
    benign_n = max(int(benign.sum()), 1)
    positive_n = max(int(positive.sum()), 1)
    return {
        "threshold": float(threshold),
        "entity_fpr": float((alerts & benign).sum() / benign_n),
        "entity_dr": float((alerts & positive).sum() / positive_n),
        "false_positive_entities": int((alerts & benign).sum()),
        "true_positive_entities": int((alerts & positive).sum()),
        "benign_entities": int(benign.sum()),
        "positive_entities": int(positive.sum()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章跨年阈值迁移诊断（MLP O11 底座，logit 空间路径最大）")
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument(
        "--checkpoint",
        default=f"runs/diagnostics/{SOURCE_RUN_ID}/checkpoints/selected-{CELL}.pt",
    )
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    args = parser.parse_args()
    cache_root = Path(args.cache_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    if not torch.cuda.is_available():
        raise RuntimeError("需要 CUDA 设备")
    device = torch.device("cuda")

    log("加载 O11 冻结检查点")
    state_dict, identity, checkpoint_sha256 = load_checkpoint(Path(args.checkpoint))
    model = build_model(device)
    model.load_state_dict(state_dict)
    log(f"检查点身份核验通过：run_id={identity.get('run_id')} cell={identity.get('cell')}")

    # ---- 源年（LSPR23）验证区校准 ----
    log("加载源年冻结缓存（LSPR23）")
    source = legacy.load_arrays(cache_root, legacy.SOURCE_ARRAYS)
    split_config = {"training": {"seed": 42, "validation_fraction": 0.1, "time_tail_fraction": 0.15}}
    train_rows, validation_rows, split_stats = legacy.source_split(source, split_config)
    if split_stats != EXPECTED_SOURCE_SPLIT:
        raise RuntimeError(f"源年协议 A 切分统计不符：{split_stats}")
    log(f"源年切分核验通过：{split_stats}")
    del train_rows

    gX23 = torch.from_numpy(source["X23"]).to(device)
    gI23 = torch.from_numpy(source["I23"]).to(device)
    gM23 = torch.from_numpy(source["M23"]).to(device)
    log(f"源年验证区前向（logit）：{len(validation_rows):,} 序列")
    val_scores_flow, val_flow_ids = score_rows_logit(model, validation_rows, gX23, gI23, gM23, device)
    del gX23, gI23, gM23
    torch.cuda.empty_cache()

    flow_count_23 = len(source["y23"])
    flow_logit_23 = np.full(flow_count_23, np.nan, dtype=np.float32)
    seen_23 = np.zeros(flow_count_23, dtype=bool)
    flow_logit_23[val_flow_ids] = val_scores_flow
    seen_23[val_flow_ids] = True

    flow_entity_23 = legacy.build_flow_entity(source["I23"], source["M23"], source["E23"], flow_count_23)
    entity_count_23 = int(flow_entity_23.max()) + 1
    entity_labels_23 = np.zeros(entity_count_23, dtype=np.float32)
    np.maximum.at(entity_labels_23, flow_entity_23, source["y23"])

    path_max_23 = legacy.entity_scores(flow_logit_23, seen_23, flow_entity_23, entity_count_23, None)
    valid_23 = np.isfinite(path_max_23)
    scores_23 = path_max_23[valid_23]
    labels_23 = entity_labels_23[valid_23]
    log(
        f"源年验证区可评价实体：{len(scores_23):,}"
        f"（良性 {int((labels_23 == 0).sum()):,}，正例 {int((labels_23 == 1).sum()):,}）"
    )

    tau_source = calibrate_threshold(scores_23[labels_23 == 0], BUDGET_FPR)
    source_calibration = rates(scores_23, labels_23, tau_source)
    log(
        f"源年校准阈值（logit）={tau_source:.6f}；"
        f"源侧 FPR={source_calibration['entity_fpr']:.6f} DR={source_calibration['entity_dr']:.6f}"
    )

    del source
    torch.cuda.empty_cache()

    # ---- 目标年（LSPR24）迁移评价 ----
    log("加载目标年冻结缓存（LSPR24）")
    target = legacy.load_arrays(cache_root, legacy.TARGET_ARRAYS)
    if target["X24"].shape != (20_227_356, 83):
        raise RuntimeError(f"LSPR24 冻结缓存形状不符：{target['X24'].shape}")
    key = np.array(
        [
            left + "|" + right if left <= right else right + "|" + left
            for left, right in zip(target["s24"], target["d24"])
        ],
        dtype=object,
    )
    _, flow_entity_24 = np.unique(key, return_inverse=True)
    del key
    entity_count_24 = int(flow_entity_24.max()) + 1
    entity_labels_24 = np.zeros(entity_count_24, dtype=np.float32)
    np.maximum.at(entity_labels_24, flow_entity_24, target["y24"])
    if entity_count_24 != EXPECTED_TARGET_ENTITY_COUNT or int(entity_labels_24.sum()) != EXPECTED_TARGET_POSITIVE_ENTITIES:
        raise RuntimeError(
            f"LSPR24 实体与标签自检失败：entity_count={entity_count_24} positive={int(entity_labels_24.sum())}"
        )
    log(f"目标年实体自检通过：{entity_count_24:,} 实体，正例 {int(entity_labels_24.sum()):,}")

    flow_count_24 = len(target["y24"])
    log(f"目标年全量前向（logit，一次覆盖 {flow_count_24:,} 流），target_year_arrays_read=1")
    flow_logit_24, seen_24 = score_target_logit(
        model, target["X24"], target["I24"], target["M24"], flow_count_24, device
    )

    path_max_24 = legacy.entity_scores(flow_logit_24, seen_24, flow_entity_24, entity_count_24, None)
    valid_24 = np.isfinite(path_max_24)
    scores_24 = path_max_24[valid_24]
    labels_24 = entity_labels_24[valid_24]
    log(
        f"目标年可评价实体：{len(scores_24):,}"
        f"（良性 {int((labels_24 == 0).sum()):,}，正例 {int((labels_24 == 1).sum()):,}）"
    )

    # 迁移评价：直接复用源年校准阈值，零目标年参与阈值选择
    target_migrated = rates(scores_24, labels_24, tau_source)
    log(f"迁移阈值下目标年：FPR={target_migrated['entity_fpr']:.6f} DR={target_migrated['entity_dr']:.6f}")

    # 事后参考：用目标标签重新校准，只作病灶存在性证明，不可部署
    tau_target_posthoc = calibrate_threshold(scores_24[labels_24 == 0], BUDGET_FPR)
    target_posthoc = rates(scores_24, labels_24, tau_target_posthoc)
    log(
        f"目标年事后参考阈值（logit）={tau_target_posthoc:.6f}；"
        f"FPR={target_posthoc['entity_fpr']:.6f} DR={target_posthoc['entity_dr']:.6f}"
    )

    fpr_budget_utilization = target_migrated["entity_fpr"] / BUDGET_FPR
    dr_gap_points = (target_posthoc["entity_dr"] - target_migrated["entity_dr"]) * 100.0
    positive_n_source = int((labels_23 == 1).sum())
    source_dr = source_calibration["entity_dr"]
    source_dr_se = float(np.sqrt(max(source_dr * (1 - source_dr), 0.0) / max(positive_n_source, 1)))

    result = {
        "schema_version": "ch4-mlp-o11-crossyear-threshold-transfer-diag-v1",
        "run_id": RUN_ID,
        "screening_only": True,
        "target_informed": True,
        "formal_paper_evidence": False,
        "target_year_arrays_read_count": 1,
        "resource_contention": True,
        "resource_contention_note": "服务器上 TabM32 评价与 ResNet 重评并发运行，时间与吞吐按并发条件实测",
        "budget_entity_fpr": BUDGET_FPR,
        "checkpoint": {
            "path": str(args.checkpoint),
            "sha256": checkpoint_sha256,
            "identity": identity,
        },
        "source_split": split_stats,
        "source_calibration": {
            "score_space": "logit",
            "aggregation": "path_max",
            "validation_sequences": int(len(validation_rows)),
            "evaluable_entities": int(len(scores_23)),
            "positive_entities": positive_n_source,
            "benign_entities": int((labels_23 == 0).sum()),
            **source_calibration,
            "detection_rate_se_binomial": source_dr_se,
        },
        "target_migrated_evaluation": {
            "score_space": "logit",
            "aggregation": "path_max",
            "evaluable_entities": int(len(scores_24)),
            "positive_entities": int((labels_24 == 1).sum()),
            "benign_entities": int((labels_24 == 0).sum()),
            "threshold_reused_from_source": tau_source,
            **target_migrated,
        },
        "target_posthoc_reference": {
            "score_space": "logit",
            "aggregation": "path_max",
            "note": "用目标年标签校准，只作病灶存在性证明，不可部署",
            **target_posthoc,
        },
        "mismatch_summary": {
            "fpr_budget_utilization_ratio": fpr_budget_utilization,
            "fpr_budget_utilization_pct": fpr_budget_utilization * 100.0,
            "dr_gap_points_posthoc_minus_migrated": dr_gap_points,
        },
        "target_entity_self_check": {
            "entity_count": entity_count_24,
            "positive_entities": int(entity_labels_24.sum()),
        },
    }
    legacy.atomic_json(output_root / "crossyear-threshold-transfer-results.json", result)
    log("结果写入 crossyear-threshold-transfer-results.json")
    log(
        "六数汇总："
        f"源校准阈值(logit)={tau_source:.6f} 源侧FPR={source_calibration['entity_fpr']:.6f} 源侧DR={source_calibration['entity_dr']:.6f} | "
        f"迁移FPR={target_migrated['entity_fpr']:.6f} 迁移DR={target_migrated['entity_dr']:.6f} | "
        f"事后参考FPR={target_posthoc['entity_fpr']:.6f} 事后参考DR={target_posthoc['entity_dr']:.6f}"
    )
    print("CROSSYEAR_THRESHOLD_TRANSFER_DIAG_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
