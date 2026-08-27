# -*- coding: utf-8 -*-
"""第四章 M1' 本机筛选：MLP 底座池化 Tong 路径最大证书（screening_only）。

复刻 XGB Tong 链『同模型交叉校准』六方向结构（恢复卡 §5.3），但底座换成
D0 本机筛选三折折外 O11 模型的逐流分数：每折实体按标签分层随机等分为两半，
校准/评价角色互换，得 3 折×2 互换 = 6 方向。每方向在校准半良性实体的路径
最大分数上，用精确二项 Clopper-Pearson（CP）上界求可证阈值（δ'=0.05/6，
本任务无长度分层，留给 S_a 四格工具），在评价半计数。六方向的评价半两两
互补、合并后恰好覆盖全部实体一次，池化得到全量源年折外人群（150,680 实体、
239 正实体）上的三臂比较，规避 XGB 链『评价集仅 40 正实体、功效不足』的
教训（评价人群预注册，见实施计划四-M1'）。

三臂：
  B0'（首曝经验校准阈值，无证书）——纯经验基线；
  B1'（B0' 阈值套用到全曝光路径最大，无证书）——曝光累积但不换阈值；
  M1'（六方向路径最大 CP 证书阈值）——本工具的候选机制。

CP 数学（``cp_upper_bound``）用纯 Python/NumPy 实现（不依赖 SciPy），
经二分求解 p 使 P(Bin(n,p)<=k)=delta'；与
``scipy.stats.beta.ppf(1-delta', k+1, n-k)`` 逐点对拍见实现报告。

证据边界：``screening_only=true``，fp32 折外模型（本机），结果不进论文；
正式再确认在服务器资源恢复后按冻结合同重跑。LSPR24 零读取。依赖
``tools/ch4_mlp_o11_oof_fold_models_local_screen.py`` 产出的三折折外检查点
（``runs/diagnostics/ch4-mlp-o11-oof-fold-models-local-screen-v1/checkpoints/``），
未就绪时清晰诊断退出，不伪装完成。
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch4_mlp_o11_oof_fold_models as d0  # noqa: E402
from ch4_mlp_o11_oof_fold_models_local_screen import (  # noqa: E402
    RUN_ID as D0_RUN_ID,
    atomic_json,
    prepare,
)
from ch4_mlp_o11_pathology_diagnostics_local_screen import (  # noqa: E402
    BUDGET_FPR,
    build_flow_entity,
    calibrate_threshold,
    entity_tables,
    oof_flow_scores,
    rates,
)

RUN_ID = "ch4-mlp-o11-tong-pooled-q0-local-screen-v1"
SEED = 42
FOLD_COUNT = 3
DIRECTION_COUNT = 6
DELTA_GLOBAL = 0.05
DELTA_PER_DIRECTION = DELTA_GLOBAL / DIRECTION_COUNT  # 0.05/6，本任务无分层
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


# ---------------------------------------------------------------------------
# CP 上界数学：纯 Python/NumPy 实现，不依赖 SciPy。
# 验收对拍目标：scipy.stats.beta.ppf(1-delta, k+1, n-k)。
# 数学关系：CP 单侧上界 p_U 满足 P(Bin(n,p_U)<=k)=delta；
# 因 P(Bin(n,p)<=k) 关于 p 严格递减，对 p 二分求根即可，见实现报告推导。
# ---------------------------------------------------------------------------


def log_binomial_pmf(n: int, k: int, p: float) -> float:
    """Binomial(n,p) 在 k 处的对数概率质量（math.lgamma，双精度稳定）。"""
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log1p(-p)
    )


def binomial_survival(n: int, k: int, p: float) -> float:
    """P(X>=k)，X~Binomial(n,p)；对数空间峰值平移求和，数值稳定。"""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    log_terms = np.fromiter(
        (log_binomial_pmf(n, j, p) for j in range(k, n + 1)),
        dtype=np.float64,
        count=n - k + 1,
    )
    peak = float(log_terms.max())
    tail = math.exp(peak) * float(np.exp(log_terms - peak).sum())
    return min(1.0, tail)


def cp_upper_bound(n: int, k: int, delta: float) -> float:
    """精确二项 Clopper-Pearson 单侧上界：满足 P(Bin(n,p_U)<=k)=delta 的 p_U。

    等价闭式 ``scipy.stats.beta.ppf(1-delta, k+1, n-k)``（k<n 时）；本函数
    改用二分求根（对 P(Bin(n,p)<=k) 关于 p 的单调递减性），避免 SciPy
    生产依赖。k>=n 时上界退化为 1.0（全部校准点都超限，无法出具证书）。
    """
    if n <= 0:
        raise ValueError("n 必须为正")
    if k < 0:
        raise ValueError("k 不得为负")
    if k >= n:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(100):
        mid = (low + high) / 2.0
        cdf_le_k = 1.0 - binomial_survival(n, k + 1, mid)
        if cdf_le_k > delta:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def max_certified_exceedances(n: int, delta: float, budget: float) -> dict[str, Any]:
    """二分查找满足 CP 上界<=budget 的最大整数超限配额 k（CP 上界随 k 单调不减）。"""
    if n <= 0:
        return {"available": False, "max_k": -1, "cp_upper_bound_at_k": None, "n": n}
    bound_at_zero = cp_upper_bound(n, 0, delta)
    if bound_at_zero > budget:
        return {
            "available": False,
            "max_k": -1,
            "cp_upper_bound_at_k": bound_at_zero,
            "n": n,
        }
    low, high = 0, n - 1
    while low < high:
        mid = (low + high + 1) // 2
        if cp_upper_bound(n, mid, delta) <= budget:
            low = mid
        else:
            high = mid - 1
    return {
        "available": True,
        "max_k": low,
        "cp_upper_bound_at_k": cp_upper_bound(n, low, delta),
        "n": n,
    }


def threshold_for_allowed_count(benign_scores: np.ndarray, allowed: int) -> float:
    """良性实体分数上取恰好<=allowed 个>=阈值的最大阈值（并列组整体处理）。

    与 pathology 模块 ``calibrate_threshold`` 同一 tie-safe 惯例（``>=`` 比较，
    从大到小扫描候选阈值），改为直接接受整数配额而非浮点预算比例，供
    CP 证书调用。"""
    ordered = np.sort(np.asarray(benign_scores, np.float64))[::-1]
    if len(ordered) == 0:
        raise RuntimeError("空校准良性分数集合")
    if allowed < 0:
        return float(np.nextafter(ordered[0], np.inf))
    candidates = np.unique(ordered)[::-1]
    for threshold in candidates:
        if int((ordered >= threshold).sum()) <= allowed:
            return float(threshold)
    return float(np.nextafter(ordered[0], np.inf))


def certificate_threshold(benign_scores: np.ndarray, delta: float, budget: float) -> dict[str, Any]:
    """CP 证书阈值：校准良性分数 -> (阈值、证书上界、是否成立、证书税)。

    『证书税』= budget - 经验超限率，量化有限样本证书相对经验校准的保守代价
    （台账口径，见实施计划三、五点五）。"""
    ordered = np.asarray(benign_scores, np.float64)
    n = len(ordered)
    search = max_certified_exceedances(n, delta, budget)
    if not search["available"]:
        fallback = float(np.nextafter(np.max(ordered), np.inf)) if n else math.inf
        return {
            **search,
            "threshold": fallback,
            "empirical_exceedances": 0,
            "empirical_rate": 0.0,
            "certificate_valid": False,
            "certificate_tax": None,
        }
    allowed = search["max_k"]
    threshold = threshold_for_allowed_count(ordered, allowed)
    exceed = int((ordered >= threshold).sum())
    return {
        **search,
        "threshold": threshold,
        "empirical_exceedances": exceed,
        "empirical_rate": exceed / n,
        "certificate_valid": bool(search["cp_upper_bound_at_k"] <= budget),
        "certificate_tax": budget - exceed / n,
    }


# ---------------------------------------------------------------------------
# 六方向切半（同模型交叉校准，复刻 XGB Tong 链结构，恢复卡 §5.3）
# ---------------------------------------------------------------------------


def make_six_directions(
    fold_of_entity: np.ndarray, entity_labels: np.ndarray, seed: int
) -> tuple[np.ndarray, tuple[dict[str, int], ...]]:
    """每折实体按标签分层随机等分为两半，校准/评价角色互换，得 3 折×2 互换=6 方向。"""
    halves = np.full(len(entity_labels), -1, np.int8)
    rng = np.random.RandomState(seed)
    for fold in range(FOLD_COUNT):
        for label in (0, 1):
            members = np.flatnonzero((fold_of_entity == fold) & (entity_labels == label))
            shuffled = members[rng.permutation(len(members))]
            halves[shuffled] = np.arange(len(shuffled), dtype=np.int64) % 2
    if np.any(halves < 0):
        raise RuntimeError("六方向切半未覆盖全部实体")
    directions = tuple(
        {
            "direction": fold * 2 + role,
            "fold": fold,
            "calibration_half": role,
            "evaluation_half": 1 - role,
        }
        for fold in range(FOLD_COUNT)
        for role in (0, 1)
    )
    return halves, directions


def direction_entities(
    fold_of_entity: np.ndarray, halves: np.ndarray, direction: dict[str, int]
) -> tuple[np.ndarray, np.ndarray]:
    fold_mask = fold_of_entity == direction["fold"]
    calibration = np.flatnonzero(fold_mask & (halves == direction["calibration_half"]))
    evaluation = np.flatnonzero(fold_mask & (halves == direction["evaluation_half"]))
    return calibration, evaluation


def alert_rates(alerts: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    benign = labels == 0
    positive = labels == 1
    fp = int((alerts & benign).sum())
    tp = int((alerts & positive).sum())
    neg = int(benign.sum())
    pos = int(positive.sum())
    return {
        "entity_fpr": fp / neg if neg else 0.0,
        "entity_dr": tp / pos if pos else 0.0,
        "false_positive_entities": fp,
        "true_positive_entities": tp,
        "negative_entities": neg,
        "positive_entities": pos,
    }


def run_m1_prime(
    tables: dict[str, np.ndarray],
    labels: np.ndarray,
    fold_of_entity: np.ndarray,
    seed: int = SEED,
    delta_per_direction: float = DELTA_PER_DIRECTION,
    budget: float = BUDGET_FPR,
) -> dict[str, Any]:
    """核心六方向池化 Tong 计算；被本工具 main() 与 S_a 四格工具 C10 臂共同复用，
    保证『C10=仅池化Tong(=M1')』的字面等价（同种子、同六方向切半、同证书数学）。"""
    halves, directions = make_six_directions(fold_of_entity, labels, seed)

    global_b0 = np.zeros(len(labels), dtype=bool)
    global_b1 = np.zeros(len(labels), dtype=bool)
    global_m1 = np.zeros(len(labels), dtype=bool)
    evaluation_coverage = np.zeros(len(labels), dtype=np.int32)
    late_detected = 0
    direction_receipts: list[dict[str, Any]] = []

    for direction in directions:
        calibration, evaluation = direction_entities(fold_of_entity, halves, direction)
        calibration_benign = calibration[labels[calibration] == 0]

        tau_first = calibrate_threshold(tables["first"][calibration_benign], budget)
        cert = certificate_threshold(tables["path_max"][calibration_benign], delta_per_direction, budget)

        eval_first = tables["first"][evaluation]
        eval_path_max = tables["path_max"][evaluation]
        eval_labels = labels[evaluation]

        alerts_b0 = eval_first >= tau_first
        alerts_b1 = eval_path_max >= tau_first
        alerts_m1 = eval_path_max >= cert["threshold"]

        global_b0[evaluation] = alerts_b0
        global_b1[evaluation] = alerts_b1
        global_m1[evaluation] = alerts_m1
        evaluation_coverage[evaluation] += 1

        late_detected += int(
            (
                (eval_first < cert["threshold"])
                & (eval_path_max >= cert["threshold"])
                & (eval_labels == 1)
            ).sum()
        )

        direction_receipts.append(
            {
                "direction": direction["direction"],
                "fold": direction["fold"],
                "calibration_half": direction["calibration_half"],
                "evaluation_half": direction["evaluation_half"],
                "calibration_benign_entities": int(len(calibration_benign)),
                "evaluation_entities": int(len(evaluation)),
                "b0_threshold": tau_first,
                "m1_certificate": cert,
            }
        )

    if not np.array_equal(evaluation_coverage, np.ones(len(labels), dtype=np.int32)):
        raise RuntimeError("六方向评价半未恰好覆盖全部实体一次，池化汇总失效")

    metrics = {
        "B0_first_calibrated": alert_rates(global_b0, labels),
        "B1_all_exposure_same_threshold": alert_rates(global_b1, labels),
        "M1_path_max_tong": alert_rates(global_m1, labels),
    }
    certificates_valid = all(
        receipt["m1_certificate"]["certificate_valid"] for receipt in direction_receipts
    )
    return {
        "halves": halves,
        "directions": direction_receipts,
        "global_alerts": {"B0": global_b0, "B1": global_b1, "M1": global_m1},
        "metrics": metrics,
        "late_detected_positive_entities": late_detected,
        "certificates_valid": certificates_valid,
        "halves_sha256": d0.sha256_array(halves),
    }


def d0_checkpoints_missing(d0_root: Path) -> list[int]:
    return [
        fold
        for fold in range(FOLD_COUNT)
        if not (d0_root / "checkpoints" / f"selected-O11-fold{fold}.pt").is_file()
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章 M1' 本机筛选：池化 Tong 路径最大证书（MLP 底座）")
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--d0-root", default=f"runs/diagnostics/{D0_RUN_ID}")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    args = parser.parse_args()
    cache_root = Path(args.cache_root)
    d0_root = Path(args.d0_root)
    output_root = Path(args.output_root)

    missing_folds = d0_checkpoints_missing(d0_root)
    if missing_folds:
        log(f"D0 检查点未就绪，缺失折 {missing_folds}（期望目录 {d0_root / 'checkpoints'}）")
        log("本工具依赖三折折外模型，先运行 ch4_mlp_o11_oof_fold_models_local_screen.py 补齐后重试")
        print("D0_CHECKPOINTS_MISSING", flush=True)
        return 3

    output_root.mkdir(parents=True, exist_ok=True)
    context = prepare(cache_root)
    X = np.load(cache_root / "X23.npy")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    log(f"设备 {device.type}；折哈希 {context['fold_sha'][:16]}…")
    scores, seen = oof_flow_scores(context, X, d0_root, device)
    flow_entity = build_flow_entity(context["source"])
    labels = context["entity_labels"]
    tables = entity_tables(scores, seen, flow_entity, labels)
    fold_of_entity = context["fold_of_entity"]

    log("六方向切半 + 逐方向 CP 证书阈值 + 池化汇总")
    outcome = run_m1_prime(tables, labels, fold_of_entity)
    metrics = outcome["metrics"]
    gate = (
        outcome["certificates_valid"]
        and metrics["M1_path_max_tong"]["entity_fpr"] <= BUDGET_FPR
        and metrics["M1_path_max_tong"]["entity_dr"] >= metrics["B0_first_calibrated"]["entity_dr"]
    )

    result = {
        "schema_version": "ch4-mlp-o11-tong-pooled-q0-local-screen-v1",
        "run_id": RUN_ID,
        "screening_only": True,
        "formal_paper_evidence": False,
        "target_year_arrays_read": 0,
        "precision": "fp32",
        "device_type": device.type,
        "fold_assignment_sha256": context["fold_sha"],
        "half_assignment_sha256": outcome["halves_sha256"],
        "seed": SEED,
        "direction_count": DIRECTION_COUNT,
        "delta_global": DELTA_GLOBAL,
        "delta_per_direction": DELTA_PER_DIRECTION,
        "budget_entity_fpr": BUDGET_FPR,
        "evaluation_population": {
            "entities": int(len(labels)),
            "positive_entities": int(labels.sum()),
        },
        "directions": outcome["directions"],
        "metrics": metrics,
        "late_detected_positive_entities": outcome["late_detected_positive_entities"],
        "mechanical_verdict": {
            "all_certificates_valid": outcome["certificates_valid"],
            "pooled_fpr_le_budget": bool(metrics["M1_path_max_tong"]["entity_fpr"] <= BUDGET_FPR),
            "dr_m1_ge_b0": bool(
                metrics["M1_path_max_tong"]["entity_dr"] >= metrics["B0_first_calibrated"]["entity_dr"]
            ),
            "qualified": bool(gate),
            "verdict": (
                "M1_PRIME_LOCAL_SCREEN_SUPPORTED" if gate else "M1_PRIME_LOCAL_SCREEN_NOT_SUPPORTED"
            ),
            "rule": "all_direction_certificates_valid AND pooled_FPR<=0.04 AND DR(M1')>=DR(B0')",
        },
    }
    atomic_json(output_root / "results.json", result)
    log(
        f"M1' 门={'过' if gate else '不过'}："
        f"池化FPR={metrics['M1_path_max_tong']['entity_fpr']:.6f} "
        f"DR(M1')={metrics['M1_path_max_tong']['entity_dr']:.6f} "
        f"DR(B0')={metrics['B0_first_calibrated']['entity_dr']:.6f}"
    )
    print("LOCAL_SCREEN_M1_PRIME_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
