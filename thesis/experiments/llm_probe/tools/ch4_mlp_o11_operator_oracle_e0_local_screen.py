# -*- coding: utf-8 -*-
"""第四章 E0 本机筛选：多聚合算子 oracle 上界诊断（screening_only）。

机制 2 换候选（长度状态门控多聚合算子，机制 2'，实施计划四点十二乙）后的
第一个存废实验：仿 MalMoE 原文图 3 的立题逻辑——先证 oracle（逐实体选优
算子）相对单算子有真实差距，才有资格继续做门控实现。算子族取自冻结评价
p 网格 `{0.5,1,2,4,8}`（0.5 弃用，见四点十二乙），加既有 max 读出：
`{L∞(=max), L1(=mean), L2, L4, L8}`。全部为『前缀运行值，在线因果口径』
的幂平均：``Lp(x_1..x_i) = (mean(x_1^p..x_i^p))^(1/p)``，``L∞=max``。

三层对照（同一批 D0 三折折外分数、同一六方向切半，量纲一致）：

1. **单算子基线**：每个算子单独作全局聚合，直接复用
   ``ch4_mlp_o11_tong_pooled_q0_local_screen.run_m1_prime``（六方向 CP 证书
   Tong 池化，只把 ``tables["path_max"]`` 换成该算子的全路径聚合值）——
   L∞ 列与既有 C10/M1′ 结果字面等价（自校）。
2. **固定状态门上界**：每〈方向,证书层〉在校准半上，对 5 个算子各自求
   经验阈值（budget=0.04，tie-safe，修复版 ``calibrate_threshold``），选
   校准半 DR 最优且校准半 FPR≤预算的算子（平局：优先 max，再按 p 降序），
   评价半按所选〈算子,阈值〉读出——机制 2″固定门形态的可达性能。
3. **oracle 上界**：同一批 120 个〈方向,层,算子〉阈值作『菜单』，逐实体
   按真标签挑『对它最有利』的算子——正实体取菜单中任一算子命中即算检出
   （并集，最容易过阈）、良性取全部算子都命中才算误报（交集，最难过阈）。
   仅作算子异质性的理论天花板诊断，**不可部署**（用了真标签）。

分组口径：证书层用『实体固定属性』（最终观测长度所在层，方案 A 记账），
与既有 S_a/S_b/S_c 工具一致；沿用同一 `layer_of_length`/
`layer_calibration_groups`（从 `ch4_mlp_o11_stratified_tong_2x2_local_screen`
导入复用，不重写）。项 2/3 用『校准半选、评价半读』的实体级最终聚合值
比较（不做在线逐位置重放）——E0 是立题诊断，不需要 S_b/S_c 那套跨层
序贯证书机制；层内 CP 证书留给『机制 2″ 全量四臂』任务（若 E0 判过）。

证伪判据（预注册，冻结项目级噪声底线 `SE(0.036)`，第三章多份研究契约
沿用同一常数，如 `2026-08-25-第三章机制改造研究契约/研究问题卡.md:60`、
`2026-08-26-第三章跨骨干机制实验负结果档案.md:25`）：oracle 相对最优单
算子的池化 DR 增益（同等池化合规下）`<1×SE(0.036)` → 算子异质性在本数据
无 juice，MalMoE 路线否决；`>=1×SE` → 路线立住。

证据边界：``screening_only=true``，fp32/MPS 折外模型（本机），结果不进
论文；oracle 列使用真标签仅作诊断，正文与任何部署阈值选择禁止引用。
LSPR24 零读取。依赖三折折外检查点（本机 local-screen 布局或服务器 bf16
布局二选一，见 ``pooled_q0.d0_checkpoints_missing``），未就绪时清晰诊断
退出，不伪装完成。
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

import ch4_mlp_o11_stratified_tong_2x2_local_screen as sa  # noqa: E402
import ch4_mlp_o11_tong_pooled_q0_local_screen as pooled_q0  # noqa: E402
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
)

RUN_ID = "ch4-mlp-o11-operator-oracle-e0-v1"
OPERATORS: tuple[str, ...] = ("Linf", "L1", "L2", "L4", "L8")
OPERATOR_P: dict[str, float] = {"Linf": math.inf, "L1": 1.0, "L2": 2.0, "L4": 4.0, "L8": 8.0}
# 平局规则预注册（四点十二乙）：优先 max，再按 p 降序。
OPERATOR_TIE_ORDER: tuple[str, ...] = ("Linf", "L8", "L4", "L2", "L1")
# 冻结项目级噪声底线（第三章多份研究契约沿用，见模块 docstring 引用）。
NOISE_FLOOR_SE = 0.036
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def entity_operator_aggregates(
    scores: np.ndarray,
    seen: np.ndarray,
    flow_entity: np.ndarray,
    entity_labels: np.ndarray,
    path_max: np.ndarray,
) -> dict[str, np.ndarray]:
    """每算子的实体级全路径聚合值。``Linf`` 直接复用既有 ``path_max``
    （不重算，保证与 C10/M1′ 字面等价）；``Lp`` 为全路径幂平均，向量化
    ``np.add.reduceat`` 实现，不含 Python 循环。"""
    flow_ids = np.flatnonzero(seen & (flow_entity >= 0))
    entities = flow_entity[flow_ids]
    order = np.lexsort((flow_ids, entities))
    ordered_flow = flow_ids[order]
    ordered_entity = entities[order]
    ordered_scores = scores[ordered_flow].astype(np.float64)
    starts = np.flatnonzero(np.r_[True, ordered_entity[1:] != ordered_entity[:-1]])
    lengths = np.diff(np.r_[starts, len(ordered_entity)]).astype(np.int64)
    entity_ids = ordered_entity[starts]
    covered = np.zeros(len(entity_labels), dtype=bool)
    covered[entity_ids] = True
    if not covered.all():
        raise RuntimeError(f"{int((~covered).sum())} 个实体无任何被打分流（算子聚合构造）")

    aggregates: dict[str, np.ndarray] = {"Linf": np.asarray(path_max, dtype=np.float64)}
    for name in ("L1", "L2", "L4", "L8"):
        p = OPERATOR_P[name]
        powered = np.clip(ordered_scores, 1e-7, None) ** p
        sums = np.add.reduceat(powered, starts)
        means = sums / lengths
        values = means ** (1.0 / p)
        full = np.zeros(len(entity_labels), dtype=np.float64)
        full[entity_ids] = values
        aggregates[name] = full
    return aggregates


def single_operator_baseline(
    tables: dict[str, np.ndarray],
    aggregates: dict[str, np.ndarray],
    labels: np.ndarray,
    fold_of_entity: np.ndarray,
) -> dict[str, dict[str, Any]]:
    """项 1：单算子基线，逐算子复用 ``run_m1_prime``（六方向 CP 证书 Tong）。"""
    results: dict[str, dict[str, Any]] = {}
    for name in OPERATORS:
        operator_tables = {"first": tables["first"], "path_max": aggregates[name], "length": tables["length"]}
        outcome = pooled_q0.run_m1_prime(operator_tables, labels, fold_of_entity)
        results[name] = {
            "pooled": outcome["metrics"]["M1_path_max_tong"],
            "layers": sa.layer_rates(outcome["global_alerts"]["M1"], labels, tables["length"]),
            "certificates_valid": outcome["certificates_valid"],
        }
    return results


def per_cell_operator_thresholds(
    aggregates: dict[str, np.ndarray],
    labels: np.ndarray,
    fold_of_entity: np.ndarray,
    tables_length: np.ndarray,
) -> tuple[list[dict[str, Any]], np.ndarray, tuple[dict[str, int], ...]]:
    """六方向×四证书层×五算子=120 格经验阈值（budget=0.04，修复版
    ``calibrate_threshold``），附校准半 FPR/DR，供项 2 选算子、项 3 oracle
    菜单共用。"""
    halves, direction_defs = pooled_q0.make_six_directions(fold_of_entity, labels, pooled_q0.SEED)
    cells: list[dict[str, Any]] = []
    for direction in direction_defs:
        calibration, evaluation = pooled_q0.direction_entities(fold_of_entity, halves, direction)
        calibration_benign = calibration[labels[calibration] == 0]
        calibration_positive = calibration[labels[calibration] == 1]
        groups_benign = sa.layer_calibration_groups(calibration_benign, tables_length)
        groups_positive = sa.layer_calibration_groups(calibration_positive, tables_length)
        for layer in range(sa.LAYER_COUNT):
            benign_members = groups_benign[layer]
            positive_members = groups_positive[layer]
            n_b = int(len(benign_members))
            for name in OPERATORS:
                agg = aggregates[name]
                if n_b == 0:
                    threshold = math.inf
                    calibration_fpr = 0.0
                else:
                    threshold = calibrate_threshold(agg[benign_members], BUDGET_FPR)
                    calibration_fpr = float((agg[benign_members] >= threshold).sum()) / n_b
                calibration_dr = (
                    float((agg[positive_members] >= threshold).sum()) / len(positive_members)
                    if len(positive_members)
                    else 0.0
                )
                cells.append(
                    {
                        "direction": direction["direction"],
                        "layer": layer,
                        "operator": name,
                        "threshold": float(threshold),
                        "n_benign": n_b,
                        "n_positive": int(len(positive_members)),
                        "calibration_fpr": calibration_fpr,
                        "calibration_dr": calibration_dr,
                    }
                )
    return cells, halves, direction_defs


def select_fixed_gate_operator(cell_group: list[dict[str, Any]]) -> dict[str, Any]:
    """校准半 DR 最优且 FPR≤预算的算子；全部超预算时退化为全体最优 DR
    （并在 receipt 中如实标注 ``compliant=False``，不静默丢弃这一异常）。"""
    compliant = [c for c in cell_group if c["calibration_fpr"] <= BUDGET_FPR]
    pool = compliant if compliant else cell_group
    best_dr = max(c["calibration_dr"] for c in pool)
    candidates = [c for c in pool if c["calibration_dr"] == best_dr]
    chosen = None
    for name in OPERATOR_TIE_ORDER:
        for candidate in candidates:
            if candidate["operator"] == name:
                chosen = candidate
                break
        if chosen is not None:
            break
    if chosen is None:
        chosen = candidates[0]
    return {**chosen, "compliant": bool(compliant)}


def fixed_state_gate_evaluation(
    cells: list[dict[str, Any]],
    direction_defs: tuple[dict[str, int], ...],
    halves: np.ndarray,
    aggregates: dict[str, np.ndarray],
    labels: np.ndarray,
    fold_of_entity: np.ndarray,
    tables_length: np.ndarray,
    total_entities: int,
) -> dict[str, Any]:
    """项 2：固定状态门——每〈方向,层〉选定的算子在评价半直接读出。"""
    selections: dict[tuple[int, int], dict[str, Any]] = {}
    for direction in direction_defs:
        for layer in range(sa.LAYER_COUNT):
            cell_group = [c for c in cells if c["direction"] == direction["direction"] and c["layer"] == layer]
            selections[(direction["direction"], layer)] = select_fixed_gate_operator(cell_group)

    global_alerts = np.zeros(total_entities, dtype=bool)
    for direction in direction_defs:
        _, evaluation = pooled_q0.direction_entities(fold_of_entity, halves, direction)
        groups_eval = sa.layer_calibration_groups(evaluation, tables_length)
        for layer in range(sa.LAYER_COUNT):
            selected = selections[(direction["direction"], layer)]
            members = groups_eval[layer]
            if len(members) == 0:
                continue
            agg = aggregates[selected["operator"]]
            global_alerts[members] = agg[members] >= selected["threshold"]

    selection_receipts = [
        {"direction": direction, "layer": layer, **selections[(direction, layer)]}
        for direction in [d["direction"] for d in direction_defs]
        for layer in range(sa.LAYER_COUNT)
    ]
    return {
        "pooled": pooled_q0.alert_rates(global_alerts, labels),
        "layers": sa.layer_rates(global_alerts, labels, tables_length),
        "selections": selection_receipts,
        "alerts": global_alerts,
    }


def oracle_evaluation(
    cells: list[dict[str, Any]],
    direction_defs: tuple[dict[str, int], ...],
    halves: np.ndarray,
    aggregates: dict[str, np.ndarray],
    labels: np.ndarray,
    fold_of_entity: np.ndarray,
    tables_length: np.ndarray,
    total_entities: int,
) -> dict[str, Any]:
    """项 3：oracle 上界——正实体『并集』（任一算子命中即算检出），
    良性实体『交集』（全部算子命中才算误报）；用同一批 120 格阈值菜单。"""
    global_alerts = np.zeros(total_entities, dtype=bool)
    for direction in direction_defs:
        _, evaluation = pooled_q0.direction_entities(fold_of_entity, halves, direction)
        groups_eval = sa.layer_calibration_groups(evaluation, tables_length)
        for layer in range(sa.LAYER_COUNT):
            members = groups_eval[layer]
            if len(members) == 0:
                continue
            cell_group = [c for c in cells if c["direction"] == direction["direction"] and c["layer"] == layer]
            crosses = np.zeros((len(OPERATORS), len(members)), dtype=bool)
            for idx, name in enumerate(OPERATORS):
                threshold = next(c["threshold"] for c in cell_group if c["operator"] == name)
                crosses[idx] = aggregates[name][members] >= threshold
            any_cross = crosses.any(axis=0)
            all_cross = crosses.all(axis=0)
            member_labels = labels[members]
            global_alerts[members] = np.where(member_labels == 1, any_cross, all_cross)
    return {
        "pooled": pooled_q0.alert_rates(global_alerts, labels),
        "layers": sa.layer_rates(global_alerts, labels, tables_length),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章 E0 本机筛选：多聚合算子 oracle 上界诊断（MLP 底座）")
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--d0-root", default=f"runs/diagnostics/{D0_RUN_ID}")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    args = parser.parse_args()
    cache_root = Path(args.cache_root)
    d0_root = Path(args.d0_root)
    output_root = Path(args.output_root)

    missing_folds = pooled_q0.d0_checkpoints_missing(d0_root)
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
    total_entities = len(labels)

    log("构建五算子实体级全路径聚合值（Linf 复用 path_max，Lp 向量化幂平均）")
    aggregates = entity_operator_aggregates(scores, seen, flow_entity, labels, tables["path_max"])

    log("项1：单算子基线（六方向 CP 证书 Tong，逐算子复用 run_m1_prime）")
    single_results = single_operator_baseline(tables, aggregates, labels, fold_of_entity)
    linf_pooled = single_results["Linf"]["pooled"]
    m1_reference_path = Path(f"runs/diagnostics/{pooled_q0.RUN_ID}/results.json")
    self_check: dict[str, Any] = {"m1_reference_path": str(m1_reference_path), "checked": False}
    if m1_reference_path.is_file():
        import json as _json

        reference = _json.loads(m1_reference_path.read_text(encoding="utf-8"))
        reference_metrics = reference.get("metrics", {}).get("M1_path_max_tong", {})
        matches = (
            reference_metrics.get("entity_fpr") == linf_pooled["entity_fpr"]
            and reference_metrics.get("entity_dr") == linf_pooled["entity_dr"]
            and reference_metrics.get("false_positive_entities") == linf_pooled["false_positive_entities"]
            and reference_metrics.get("true_positive_entities") == linf_pooled["true_positive_entities"]
        )
        self_check = {
            "m1_reference_path": str(m1_reference_path),
            "checked": True,
            "matches_existing_m1_prime": bool(matches),
            "reference_metrics": reference_metrics,
            "linf_metrics": linf_pooled,
        }
        log(f"Linf 自校：与既有 M1′ 结果{'完全一致' if matches else '不一致（异常，需排查）'}")
    else:
        log(f"自校跳过：未找到既有 M1′ 结果 {m1_reference_path}")

    log("项2/3 共用：六方向×四层×五算子=120 格经验阈值")
    cells, halves, direction_defs = per_cell_operator_thresholds(aggregates, labels, fold_of_entity, tables["length"])

    log("项2：固定状态门上界")
    fixed_gate = fixed_state_gate_evaluation(
        cells, direction_defs, halves, aggregates, labels, fold_of_entity, tables["length"], total_entities
    )

    log("项3：oracle 上界（用真标签，仅作诊断，不可部署）")
    oracle = oracle_evaluation(
        cells, direction_defs, halves, aggregates, labels, fold_of_entity, tables["length"], total_entities
    )

    compliant_single = {
        name: r["pooled"] for name, r in single_results.items() if r["pooled"]["entity_fpr"] <= BUDGET_FPR
    }
    if compliant_single:
        best_single_name = max(compliant_single, key=lambda name: compliant_single[name]["entity_dr"])
        best_single_dr = compliant_single[best_single_name]["entity_dr"]
    else:
        best_single_name = max(single_results, key=lambda name: single_results[name]["pooled"]["entity_dr"])
        best_single_dr = single_results[best_single_name]["pooled"]["entity_dr"]
    oracle_dr = oracle["pooled"]["entity_dr"]
    gain_over_best_single = oracle_dr - best_single_dr
    gain_over_fixed_gate = oracle_dr - fixed_gate["pooled"]["entity_dr"]
    falsified = bool(gain_over_best_single < NOISE_FLOOR_SE)

    result = {
        "schema_version": "ch4-mlp-o11-operator-oracle-e0-v1",
        "run_id": RUN_ID,
        "screening_only": True,
        "formal_paper_evidence": False,
        "target_year_arrays_read": 0,
        "precision": "fp32",
        "device_type": device.type,
        "fold_assignment_sha256": context["fold_sha"],
        "seed": pooled_q0.SEED,
        "operators": list(OPERATORS),
        "operator_p": {name: (None if math.isinf(p) else p) for name, p in OPERATOR_P.items()},
        "operator_tie_order": list(OPERATOR_TIE_ORDER),
        "budget_entity_fpr": BUDGET_FPR,
        "noise_floor_se": NOISE_FLOOR_SE,
        "evaluation_population": {"entities": total_entities, "positive_entities": int(labels.sum())},
        "single_operator_baseline": single_results,
        "single_operator_self_check_linf_vs_m1_prime": self_check,
        "per_cell_operator_thresholds_120": cells,
        "fixed_state_gate": {
            "pooled": fixed_gate["pooled"],
            "layers": fixed_gate["layers"],
            "selections": fixed_gate["selections"],
        },
        "oracle_upper_bound": {
            "pooled": oracle["pooled"],
            "layers": oracle["layers"],
            "not_deployable_uses_true_labels": True,
        },
        "falsification": {
            "best_single_operator": best_single_name,
            "best_single_operator_dr": best_single_dr,
            "best_single_operator_pooled_compliant": bool(compliant_single),
            "oracle_dr": oracle_dr,
            "gain_over_best_single_operator": gain_over_best_single,
            "gain_over_fixed_state_gate": gain_over_fixed_gate,
            "noise_floor_se": NOISE_FLOOR_SE,
            "rule": "gain_over_best_single_operator < 1xSE(0.036) => MalMoE route rejected; >= 1xSE => route stands",
            "falsified": falsified,
            "verdict": "MALMOE_ROUTE_REJECTED_NO_OPERATOR_HETEROGENEITY_SIGNAL" if falsified else "MALMOE_ROUTE_STANDS",
        },
    }
    atomic_json(output_root / "results.json", result)
    log(
        f"E0 判读={'否决' if falsified else '立住'}：最优单算子={best_single_name}(DR={best_single_dr:.6f}) "
        f"固定门DR={fixed_gate['pooled']['entity_dr']:.6f} oracleDR={oracle_dr:.6f} "
        f"增益(oracle-最优单算子)={gain_over_best_single:.6f} (阈值 SE={NOISE_FLOOR_SE})"
    )
    print("LOCAL_SCREEN_OPERATOR_ORACLE_E0_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
