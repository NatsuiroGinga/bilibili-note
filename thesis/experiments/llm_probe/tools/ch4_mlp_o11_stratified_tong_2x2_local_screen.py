# -*- coding: utf-8 -*-
"""第四章 S_a/S_b 本机筛选：MLP 底座长度分层 Tong 证书 2×2 消融（screening_only）。

四臂『Tong 证书×长度分层』2×2 消融，同一分数底座（D0 三折折外 O11）：
  C00 = 固定阈值（无证书、无分层）；
  C01 = 仅分层校准（各层独立阈值，无 Tong 池化联合重校准）；
  C10 = 仅池化 Tong（=M1'，字面复用 ``ch4_mlp_o11_tong_pooled_q0_local_screen.run_m1_prime``）；
  C11 = 分层 Tong（六方向×四证书层阈值表）。

四臂共用同一六方向切半（同种子 42、同构造函数，见 Task1），保证四格严格
可比（仅阈值构造逻辑不同，评价人群与切分完全一致）。C00/C10 与构造版本
无关，两种构造下完全相同；C01/C11 按 ``--construction`` 切换构造逻辑。

**构造 A（默认，``--construction a``，2026-08-27 首版）**：证书对象＝『层窗口
边际风险』——每层 τ_b 各自独立通过 CP 上界（或纯经验）校准，只保证『该层
自己的窗口内、该层良性实体的告警率≤预算』。方案 A 单调性设计（实施计划
四点五-4，恢复选项 A）：校准分组键＝实体『固定属性』（最终观测长度所在层，
仅作记账），决策事件＝在整条路径上按『决策时刻已观测曝光计数』在线因果
查表，一旦命中即告警。

**构造 A 的败因（2026-08-27 真实数据诊断，登记进计划四点九）**：24 格证书
逐格成立，但聚合到『实体最终层』后 FPR 远超预算（101+ 层实测 17.07%），
根因是『分层证书只保证单层边际风险，未控制实体跨层累计（序贯检验）风险』
——一个最终落入长层的实体，其路径必然依次经过更短层的窗口，每个窗口都要
与该窗口独立校准的阈值比较一次，相当于对同一实体做多次序贯检验，各自边际
合规不代表并集事件合规。

**构造 B（``--construction b``，实施计划四点九，源自构造 A 败因诊断）**：
  1. 证书对象换掉：不再证层窗口边际，改证『按实体最终层分组的条件事件——
     该实体整条路径上曾按阈值表告警』（即方案 A 的记账事件本身作为被证
     对象，直接对齐聚合口径与门①②③衡量的量，修复构造 A 的校准-评价口径
     不一致）。
  2. 阈值族改一维参数化（计划四点五-4 恢复选项 B）：公共分位水平 λ 驱动
     全部层阈值 τ_b(λ)＝层 b 良性校准分数的 (1−λ) 分位——λ 单调驱动全部层
     阈值同向变化，是 Bates Thm 1 要求的嵌套单调族（构造 A 的分坐标单调
     重放已证明『任一 τ_b 独立抬高，各组计数非增』，λ 驱动的联合变化是
     该性质的直接推论）。在校准半上选最大 λ 使每个最终层组的『整条路径
     曾告警』条件率的 CP 上界≤q=0.04（δ 分配沿用 6 方向×4 层=24 份，
     δ'=0.05/24，与构造 A 相同）；C01（无 Tong 证书）用相同一维族但改选
     『经验率≤q』的最大 λ（无 CP 上界margin）。
  3. 决策规则仍在线因果（按当前层查 τ_b(λ)）；六方向同模型交叉结构不变。
  4. 五门定义不改，单调性重放照跑（对最终选中的阈值表逐坐标扰动核验）。

CP 证书数学（``cp_upper_bound`` 等）与六方向切半、池化 Tong（C10=M1'）
均复用 Task1 ``ch4_mlp_o11_tong_pooled_q0_local_screen`` 模块，不重写。

证据边界：``screening_only=true``，fp32 折外模型（本机），结果不进论文；
正式再确认在服务器资源恢复后按冻结合同重跑。LSPR24 零读取。依赖
``ch4_mlp_o11_oof_fold_models_local_screen.py`` 产出的三折折外检查点，
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

import ch4_mlp_o11_tong_pooled_q0_local_screen as pooled_q0  # noqa: E402
from ch4_mlp_o11_oof_fold_models_local_screen import (  # noqa: E402
    RUN_ID as D0_RUN_ID,
    atomic_json,
    prepare,
)
from ch4_mlp_o11_pathology_diagnostics_local_screen import (  # noqa: E402
    BUDGET_FPR,
    LENGTH_BUCKETS,
    build_flow_entity,
    calibrate_threshold,
    entity_tables,
    oof_flow_scores,
)

# 运行身份改名为 -recal-v1 家族（2026-08-27，解冻执行指令），与 Task1/D1D2
# 诊断的家族命名保持一致；本工具依赖的 threshold_for_allowed_count 已在
# pooled_q0 模块自查修复（见该模块 -recal-v1 重命名处的说明）。
# 构造 A（旧、默认，保留旧结果）与构造 B（新，四点九）分别使用独立运行身份，
# 互不覆盖；具体选用见 main() 内 --construction 分支。
RUN_ID_CONSTRUCTION_A = "ch4-mlp-o11-stratified-tong-2x2-local-screen-recal-v1"
RUN_ID_CONSTRUCTION_B = "ch4-mlp-o11-stratified-tong-2x2-local-screen-sb-v1"
RUN_ID = RUN_ID_CONSTRUCTION_A  # 向后兼容：模块级默认导出仍指构造 A
SEED = pooled_q0.SEED
FOLD_COUNT = pooled_q0.FOLD_COUNT
DIRECTION_COUNT = pooled_q0.DIRECTION_COUNT
DELTA_GLOBAL = pooled_q0.DELTA_GLOBAL

LAYER_BOUNDS: tuple[tuple[int, int | None], ...] = ((1, 2), (3, 10), (11, 100), (101, None))
LAYER_COUNT = len(LAYER_BOUNDS)
DELTA_PER_CELL = DELTA_GLOBAL / (DIRECTION_COUNT * LAYER_COUNT)  # 0.05/24，六方向×四证书层均分
MONOTONICITY_PERTURBATIONS: tuple[float, ...] = (0.0, 0.02, 0.10)
# 构造 B 的一维公共分位 λ 二分迭代数：2^24≈16.7M 远超任何一层校准良性实体数
# （最大约 17,500），保证收敛到整数级精度而非仅浮点数值精度。
LAMBDA_SEARCH_ITERATIONS = 24
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


# ---------------------------------------------------------------------------
# 长度层与在线逐位置序列
# ---------------------------------------------------------------------------


def layer_of_length(length: np.ndarray) -> np.ndarray:
    """按证书层界（1-2/3-10/11-100/101+）把长度（或累计曝光位置）映射为层号 0..3。"""
    ids = np.full(len(length), -1, dtype=np.int64)
    for layer, (low, high) in enumerate(LAYER_BOUNDS):
        upper = high if high is not None else np.iinfo(np.int64).max
        ids[(length >= low) & (length <= upper)] = layer
    if (ids < 0).any():
        raise RuntimeError("存在长度落在证书层界之外的实体或位置")
    return ids


def entity_flow_sequences(
    scores: np.ndarray, seen: np.ndarray, flow_entity: np.ndarray, entity_labels: np.ndarray
) -> dict[str, np.ndarray]:
    """按（实体，冻结流索引升序）重建逐位置分数序列，供在线分层判定使用。

    排序逻辑与 pathology 模块 ``entity_tables`` 同构（该函数只出聚合值，
    S_a 的在线分层决策需要逐位置序列，故这里独立重建，不修改被复用函数）。
    """
    flow_ids = np.flatnonzero(seen & (flow_entity >= 0))
    entities = flow_entity[flow_ids]
    order = np.lexsort((flow_ids, entities))
    ordered_flow = flow_ids[order]
    ordered_entity = entities[order]
    ordered_scores = scores[ordered_flow].astype(np.float64)
    starts = np.flatnonzero(np.r_[True, ordered_entity[1:] != ordered_entity[:-1]])
    lengths = np.diff(np.r_[starts, len(ordered_entity)]).astype(np.int64)
    entity_ids = ordered_entity[starts]
    positions = np.arange(len(ordered_entity), dtype=np.int64)
    group_start_repeated = np.repeat(starts, lengths)
    local_index = positions - group_start_repeated + 1
    layer_id = layer_of_length(local_index)
    covered = np.zeros(len(entity_labels), dtype=bool)
    covered[entity_ids] = True
    if not covered.all():
        raise RuntimeError(f"{int((~covered).sum())} 个实体无任何被打分流（在线序列构造）")
    return {
        "scores": ordered_scores,
        "starts": starts,
        "lengths": lengths,
        "entity_ids": entity_ids,
        "layer_id": layer_id,
    }


def direction_subsequence(
    sequences: dict[str, np.ndarray], entities: np.ndarray, total_entities: int
) -> dict[str, np.ndarray]:
    """从全局逐位置序列中抽取某方向评价半对应实体的子序列（压缩重排 starts）。"""
    belongs = np.zeros(total_entities, dtype=bool)
    belongs[entities] = True
    entity_mask = belongs[sequences["entity_ids"]]
    position_mask = np.repeat(entity_mask, sequences["lengths"])
    sub_lengths = sequences["lengths"][entity_mask]
    if len(sub_lengths):
        sub_starts = np.r_[0, np.cumsum(sub_lengths)[:-1]].astype(np.int64)
    else:
        sub_starts = np.zeros(0, dtype=np.int64)
    return {
        "scores": sequences["scores"][position_mask],
        "starts": sub_starts,
        "lengths": sub_lengths,
        "entity_ids": sequences["entity_ids"][entity_mask],
        "layer_id": sequences["layer_id"][position_mask],
    }


def cummax_sequence(ordered_scores: np.ndarray, starts: np.ndarray, lengths: np.ndarray) -> np.ndarray:
    """预计算逐位置运行最大值序列（不依赖阈值）。构造 B 的 λ 二分需要在同一
    子序列上反复试探不同阈值表，把与阈值无关的 O(实体数) Python 循环拆出来
    只算一次，供多次阈值比较复用，避免 λ 搜索重复付出该循环成本。"""
    if len(ordered_scores) == 0:
        return np.zeros(0, dtype=np.float64)
    cummax = np.empty_like(ordered_scores, dtype=np.float64)
    for start, length in zip(starts.tolist(), lengths.tolist()):
        end = start + length
        cummax[start:end] = np.maximum.accumulate(ordered_scores[start:end])
    return cummax


def crossing_from_cummax(
    cummax: np.ndarray, starts: np.ndarray, lengths: np.ndarray, threshold_at_position: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """给定预计算的运行最大值序列与逐位置阈值，向量化求『运行最大值首次达到
    位置阈值』的实体级告警状态与首次命中的段内 1-based 曝光位置（未告警为 -1）。
    不含 Python 循环，是 ``first_crossing`` 可复用的阈值比较核心。

    在线因果：位置阈值只依赖决策时刻已观测的累计曝光计数（层号=f(该计数)），
    不使用实体最终长度——四点五对位表新增冻结项，避免事后信息泄漏进决策。
    """
    if len(cummax) == 0:
        return np.zeros(0, dtype=bool), np.zeros(0, dtype=np.int64)
    crossing = cummax >= threshold_at_position
    sentinel = len(cummax)
    marked = np.where(crossing, np.arange(len(cummax)), sentinel)
    first_global = np.minimum.reduceat(marked, starts)
    ends = starts + lengths
    alerted = first_global < ends
    first_local_position = np.where(alerted, first_global - starts + 1, -1)
    return alerted, first_local_position


def first_crossing(
    ordered_scores: np.ndarray, starts: np.ndarray, lengths: np.ndarray, threshold_at_position: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """``cummax_sequence`` + ``crossing_from_cummax`` 的薄封装，行为与重构前
    完全一致；单次阈值比较（评价期、单调性重放）仍走这条一次性路径。"""
    cummax = cummax_sequence(ordered_scores, starts, lengths)
    return crossing_from_cummax(cummax, starts, lengths, threshold_at_position)


# ---------------------------------------------------------------------------
# 逐层校准（方案 A：分组键=实体最终长度层，仅作校准记账）
# ---------------------------------------------------------------------------


def layer_calibration_groups(entities: np.ndarray, entity_length: np.ndarray) -> list[np.ndarray]:
    if len(entities) == 0:
        return [np.zeros(0, dtype=np.int64) for _ in range(LAYER_COUNT)]
    group_key = layer_of_length(entity_length[entities])
    return [entities[group_key == layer] for layer in range(LAYER_COUNT)]


def layer_thresholds_for_direction(
    calibration_benign: np.ndarray,
    entity_length: np.ndarray,
    path_max: np.ndarray,
    delta_per_cell: float | None,
    budget: float,
) -> list[dict[str, Any]]:
    """逐层独立阈值：delta_per_cell=None 为 C01（纯经验），否则为 C11（CP 证书）。"""
    groups = layer_calibration_groups(calibration_benign, entity_length)
    receipts: list[dict[str, Any]] = []
    for layer, members in enumerate(groups):
        scores = path_max[members]
        if len(scores) == 0:
            receipts.append(
                {
                    "layer": layer,
                    "n": 0,
                    "threshold": math.inf,
                    "available": False,
                    "empirical_exceedances": 0,
                    "empirical_rate": 0.0,
                    "certificate_valid": False,
                    "note": "该方向该层校准良性实体为空，阈值退化为正无穷（永不告警）",
                }
            )
            continue
        if delta_per_cell is None:
            allowed = int(len(scores) * budget)
            threshold = pooled_q0.threshold_for_allowed_count(scores, allowed)
            exceed = int((scores >= threshold).sum())
            receipts.append(
                {
                    "layer": layer,
                    "n": int(len(scores)),
                    "threshold": threshold,
                    "allowed_count": allowed,
                    "empirical_exceedances": exceed,
                    "empirical_rate": exceed / len(scores),
                    "certificate_valid": None,
                }
            )
        else:
            cert = pooled_q0.certificate_threshold(scores, delta_per_cell, budget)
            receipts.append({"layer": layer, **cert})
    return receipts


# ---------------------------------------------------------------------------
# 构造 B：一维公共分位 λ 嵌套族（实施计划四点九，源自构造 A 败因诊断）
# ---------------------------------------------------------------------------


def layer_calibration_score_pools(
    calibration_benign: np.ndarray, entity_length: np.ndarray, path_max: np.ndarray
) -> tuple[list[np.ndarray], list[int]]:
    """按最终层分组的校准良性 path_max 分数池——τ_b(λ) 分位阈值的分母，与
    构造 A 的 ``layer_calibration_groups`` 使用同一分组口径（仅作校准记账）。"""
    groups = layer_calibration_groups(calibration_benign, entity_length)
    pools = [path_max[members] for members in groups]
    sizes = [int(len(members)) for members in groups]
    return pools, sizes


def lambda_threshold_table(layer_score_pools: list[np.ndarray], lam: float) -> np.ndarray:
    """一维公共分位水平 λ 驱动的逐层阈值表：τ_b(λ)=层 b 良性校准分数的
    (1−λ) 分位（计划四点五-4 恢复选项 B）。λ 越大，全部层阈值同步降低、
    越容易告警——嵌套单调族，Bates Thm 1 直接适用。分位阈值复用
    ``pooled_q0.threshold_for_allowed_count``（已修复的『预算内尽量压低阈值』
    语义），配额=floor(λ*n_b)。"""
    thresholds = np.empty(LAYER_COUNT, dtype=np.float64)
    for layer, scores in enumerate(layer_score_pools):
        n_b = len(scores)
        if n_b == 0:
            thresholds[layer] = math.inf
            continue
        allowed = int(math.floor(lam * n_b))
        thresholds[layer] = pooled_q0.threshold_for_allowed_count(scores, allowed)
    return thresholds


def replay_group_counts_from_cummax(
    cummax: np.ndarray,
    starts: np.ndarray,
    lengths: np.ndarray,
    layer_id: np.ndarray,
    thresholds: np.ndarray,
    group_key: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """给定预计算 cummax 与阈值表，重放『整条路径是否曾按阈值表告警』的在线
    判定，按 group_key（实体最终层）汇总告警计数——构造 B 的被证对象直接是
    该重放结果本身，不再是单层窗口边际（修复构造 A 的败因：校准检查的是
    层内局部风险，评价聚合的却是跨层并集风险，二者口径不一致）。"""
    alerted, _ = crossing_from_cummax(cummax, starts, lengths, thresholds[layer_id])
    counts = np.bincount(group_key, weights=alerted.astype(np.float64), minlength=LAYER_COUNT).astype(np.int64)
    return alerted, counts


def select_lambda(
    sub_calibration: dict[str, np.ndarray],
    cummax_calibration: np.ndarray,
    layer_score_pools: list[np.ndarray],
    layer_sizes: list[int],
    group_key_calibration: np.ndarray,
    feasible_cell: Any,
    iterations: int = LAMBDA_SEARCH_ITERATIONS,
) -> dict[str, Any]:
    """二分求满足『每个最终层组 feasible_cell(n_b,k_b(λ))』的最大共享 λ。

    可行性关于 λ 单调不增：λ 越大，全层阈值越低，各层重放告警计数只增不减，
    经验率或 CP 上界随之只增不减——标准二分求根收敛到最大可行 λ。
    ``feasible_cell`` 只是可行性谓词，C01 传经验率判据、C11 传 CP 上界判据，
    共享同一搜索框架，不为两臂各写一套二分。
    """

    def feasible(lam: float) -> tuple[bool, np.ndarray]:
        thresholds = lambda_threshold_table(layer_score_pools, lam)
        _, counts = replay_group_counts_from_cummax(
            cummax_calibration,
            sub_calibration["starts"],
            sub_calibration["lengths"],
            sub_calibration["layer_id"],
            thresholds,
            group_key_calibration,
        )
        ok = all(feasible_cell(layer_sizes[b], int(counts[b])) for b in range(LAYER_COUNT))
        return ok, counts

    zero_ok, zero_counts = feasible(0.0)
    if not zero_ok:
        return {
            "available": False,
            "lambda": 0.0,
            "thresholds": lambda_threshold_table(layer_score_pools, 0.0).tolist(),
            "calibration_group_counts": zero_counts.tolist(),
            "calibration_group_sizes": layer_sizes,
        }
    low, high = 0.0, 1.0
    for _ in range(iterations):
        mid = (low + high) / 2.0
        ok, _ = feasible(mid)
        if ok:
            low = mid
        else:
            high = mid
    thresholds = lambda_threshold_table(layer_score_pools, low)
    _, counts = replay_group_counts_from_cummax(
        cummax_calibration,
        sub_calibration["starts"],
        sub_calibration["lengths"],
        sub_calibration["layer_id"],
        thresholds,
        group_key_calibration,
    )
    return {
        "available": True,
        "lambda": low,
        "thresholds": thresholds.tolist(),
        "calibration_group_counts": counts.tolist(),
        "calibration_group_sizes": layer_sizes,
    }


def c01_feasible_cell(n_b: int, k_b: int) -> bool:
    """C01（无 Tong 证书）判据：整条路径条件告警经验率≤预算，无 CP 上界margin。"""
    if n_b == 0:
        return True
    return (k_b / n_b) <= BUDGET_FPR


def c11_feasible_cell_factory(delta_per_cell: float) -> Any:
    """C11（Tong 证书）判据：整条路径条件告警计数的 CP 上界≤预算，δ'=0.05/24。"""

    def _feasible(n_b: int, k_b: int) -> bool:
        if n_b == 0:
            return True
        return pooled_q0.cp_upper_bound(n_b, k_b, delta_per_cell) <= BUDGET_FPR

    return _feasible


def monotonicity_replay_direction(
    sub: dict[str, np.ndarray],
    base_thresholds: np.ndarray,
    entity_length_for_sub: np.ndarray,
    perturbations: tuple[float, ...] = MONOTONICITY_PERTURBATIONS,
) -> dict[str, Any]:
    """方案 A 单调性重放核验（四点五-4）：固定其余层阈值，单独抬高第 b 层阈值，
    断言按『实体最终长度层』分组的告警计数逐坐标非增。校准分组用最终长度，
    决策仍按 ``first_crossing`` 的在线因果逻辑，两者互不冲突（记账 vs 决策）。
    """
    if len(sub["entity_ids"]) == 0:
        return {"perturbations": list(perturbations), "cells": [], "violations": [], "monotonic": True}
    group_key = layer_of_length(entity_length_for_sub)
    violations: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    for layer_index in range(LAYER_COUNT):
        counts_by_step: list[np.ndarray] = []
        for step in perturbations:
            trial = base_thresholds.copy()
            trial[layer_index] = trial[layer_index] + step
            threshold_at_position = trial[sub["layer_id"]]
            alerted, _ = first_crossing(sub["scores"], sub["starts"], sub["lengths"], threshold_at_position)
            counts = np.bincount(group_key, weights=alerted.astype(np.float64), minlength=LAYER_COUNT)
            counts_by_step.append(counts.astype(np.int64))
        cells.append({"layer_index": layer_index, "counts_by_step": [c.tolist() for c in counts_by_step]})
        for group in range(LAYER_COUNT):
            series = [int(counts[group]) for counts in counts_by_step]
            non_increasing = all(series[i] >= series[i + 1] for i in range(len(series) - 1))
            if not non_increasing:
                violations.append({"layer_index": layer_index, "group": group, "counts_by_step": series})
    return {
        "perturbations": list(perturbations),
        "cells": cells,
        "violations": violations,
        "monotonic": len(violations) == 0,
    }


def layer_rates(alerts: np.ndarray, labels: np.ndarray, entity_length: np.ndarray) -> list[dict[str, Any]]:
    group_key = layer_of_length(entity_length)
    result = []
    for layer in range(LAYER_COUNT):
        mask = group_key == layer
        result.append(
            {
                "layer": layer,
                "entities": int(mask.sum()),
                **pooled_q0.alert_rates(alerts[mask], labels[mask]),
            }
        )
    return result


def five_bucket_rates(alerts: np.ndarray, labels: np.ndarray, entity_length: np.ndarray) -> dict[str, Any]:
    """诊断口径保持五桶披露（1-2/3-10/11-100/101-1000/1001+），与 D2 诊断沿用同一桶界。"""
    result: dict[str, Any] = {}
    for low, high in LENGTH_BUCKETS:
        key = f"{low}-{high if high else '+'}"
        upper = high if high is not None else np.iinfo(np.int64).max
        mask = (entity_length >= low) & (entity_length <= upper)
        result[key] = {"entities": int(mask.sum()), **pooled_q0.alert_rates(alerts[mask], labels[mask])}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章 S_a/S_b 本机筛选：长度分层 Tong 证书 2x2（MLP 底座）")
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--d0-root", default=f"runs/diagnostics/{D0_RUN_ID}")
    parser.add_argument(
        "--construction",
        choices=("a", "b"),
        default="a",
        help=(
            "C01/C11 阈值构造：a=构造 A（默认，独立分层 CP/经验阈值，保留旧结果）；"
            "b=构造 B（一维公共分位 λ 嵌套族，四点九，证书对象改为整条路径条件事件）"
        ),
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help="默认按 --construction 选择运行身份目录（a→RUN_ID_CONSTRUCTION_A，b→RUN_ID_CONSTRUCTION_B）",
    )
    args = parser.parse_args()
    run_id = RUN_ID_CONSTRUCTION_A if args.construction == "a" else RUN_ID_CONSTRUCTION_B
    cache_root = Path(args.cache_root)
    d0_root = Path(args.d0_root)
    output_root = Path(args.output_root) if args.output_root else Path(f"runs/diagnostics/{run_id}")

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

    log("C10=M1'：复用 Task1 六方向池化 Tong（同种子同切半）")
    m1_outcome = pooled_q0.run_m1_prime(tables, labels, fold_of_entity, seed=SEED)
    halves = m1_outcome["halves"]
    directions = tuple(receipt for receipt in m1_outcome["directions"])
    # 六方向定义需与 Task1 一致，直接复算（纯函数、同种子、同输入必给同输出）
    _, direction_defs = pooled_q0.make_six_directions(fold_of_entity, labels, SEED)

    log("构建逐位置在线序列（供 C01/C10 位置版/C11 在线分层决策使用）")
    sequences = entity_flow_sequences(scores, seen, flow_entity, labels)

    global_c00 = np.zeros(total_entities, dtype=bool)
    global_c01 = np.zeros(total_entities, dtype=bool)
    global_c11 = np.zeros(total_entities, dtype=bool)
    first_position_c10 = np.full(total_entities, -1, dtype=np.int64)
    first_position_c11 = np.full(total_entities, -1, dtype=np.int64)
    evaluation_coverage = np.zeros(total_entities, dtype=np.int32)

    certificate_table_11: list[dict[str, Any]] = []
    layer_receipts_table_01: list[dict[str, Any]] = []
    direction_reports: list[dict[str, Any]] = []
    monotonicity_reports: list[dict[str, Any]] = []

    for direction_def, m1_direction in zip(direction_defs, directions):
        calibration, evaluation = pooled_q0.direction_entities(fold_of_entity, halves, direction_def)
        calibration_benign = calibration[labels[calibration] == 0]
        evaluation_coverage[evaluation] += 1

        # C00：固定阈值（无证书、无分层），复用 pathology 模块的 tie-safe 经验校准
        tau_c00 = calibrate_threshold(tables["path_max"][calibration_benign], BUDGET_FPR)
        global_c00[evaluation] = tables["path_max"][evaluation] >= tau_c00

        if args.construction == "a":
            # 构造 A：C01 仅分层经验校准，C11 分层 CP 证书（δ'=0.05/24），
            # 两者各层独立校准，校准统计量=path_max 聚合值（不重放在线决策）。
            receipts_01 = layer_thresholds_for_direction(
                calibration_benign, tables["length"], tables["path_max"], None, BUDGET_FPR
            )
            thresholds_01 = np.array([r["threshold"] for r in receipts_01], dtype=np.float64)

            receipts_11 = layer_thresholds_for_direction(
                calibration_benign, tables["length"], tables["path_max"], DELTA_PER_CELL, BUDGET_FPR
            )
            thresholds_11 = np.array([r["threshold"] for r in receipts_11], dtype=np.float64)
            lambda_receipt_01: dict[str, Any] | None = None
            lambda_receipt_11: dict[str, Any] | None = None
        else:
            # 构造 B：一维公共分位 λ 驱动全部层阈值，校准检查直接重放『整条路径
            # 是否曾按当前阈值表告警』（first_crossing 在线因果逻辑），按最终层
            # 分组统计条件告警率，与评价期聚合口径一致（四点九）。
            sub_calibration = direction_subsequence(sequences, calibration_benign, total_entities)
            cummax_calibration = cummax_sequence(
                sub_calibration["scores"], sub_calibration["starts"], sub_calibration["lengths"]
            )
            group_key_calibration = layer_of_length(tables["length"][sub_calibration["entity_ids"]])
            pools, sizes = layer_calibration_score_pools(
                calibration_benign, tables["length"], tables["path_max"]
            )

            lambda_receipt_01 = select_lambda(
                sub_calibration, cummax_calibration, pools, sizes, group_key_calibration, c01_feasible_cell
            )
            thresholds_01 = np.array(lambda_receipt_01["thresholds"], dtype=np.float64)
            receipts_01 = [
                {
                    "layer": layer,
                    "n": sizes[layer],
                    "threshold": float(thresholds_01[layer]),
                    "lambda": lambda_receipt_01["lambda"],
                    "calibration_replay_count": lambda_receipt_01["calibration_group_counts"][layer],
                    "empirical_rate": (
                        lambda_receipt_01["calibration_group_counts"][layer] / sizes[layer]
                        if sizes[layer]
                        else 0.0
                    ),
                    "certificate_valid": None,
                }
                for layer in range(LAYER_COUNT)
            ]

            c11_feasible_cell = c11_feasible_cell_factory(DELTA_PER_CELL)
            lambda_receipt_11 = select_lambda(
                sub_calibration, cummax_calibration, pools, sizes, group_key_calibration, c11_feasible_cell
            )
            thresholds_11 = np.array(lambda_receipt_11["thresholds"], dtype=np.float64)
            receipts_11 = []
            for layer in range(LAYER_COUNT):
                n_b = sizes[layer]
                k_b = lambda_receipt_11["calibration_group_counts"][layer]
                cp_upper = pooled_q0.cp_upper_bound(n_b, k_b, DELTA_PER_CELL) if n_b else None
                receipts_11.append(
                    {
                        "layer": layer,
                        "n": n_b,
                        "max_k": k_b,
                        "threshold": float(thresholds_11[layer]),
                        "lambda": lambda_receipt_11["lambda"],
                        "cp_upper_bound_at_k": cp_upper,
                        "empirical_rate": (k_b / n_b if n_b else 0.0),
                        "certificate_valid": bool(cp_upper <= BUDGET_FPR) if n_b else True,
                    }
                )

        sub = direction_subsequence(sequences, evaluation, total_entities)
        alerted_01, _ = first_crossing(sub["scores"], sub["starts"], sub["lengths"], thresholds_01[sub["layer_id"]])
        alerted_11, position_11 = first_crossing(
            sub["scores"], sub["starts"], sub["lengths"], thresholds_11[sub["layer_id"]]
        )

        # C10 位置版：单一方向阈值广播到全部位置，求首告警位置；与 M1' 布尔结果做一致性断言
        tau_c10 = m1_direction["m1_certificate"]["threshold"]
        alerted_10, position_10 = first_crossing(
            sub["scores"], sub["starts"], sub["lengths"], np.full(len(sub["scores"]), tau_c10)
        )
        expected_10 = m1_outcome["global_alerts"]["M1"][sub["entity_ids"]]
        if not np.array_equal(alerted_10, expected_10):
            raise RuntimeError("C10 位置版重放与 M1' 池化结果不一致，六方向切半或阈值绑定有误")

        global_c01[sub["entity_ids"]] = alerted_01
        global_c11[sub["entity_ids"]] = alerted_11
        first_position_c10[sub["entity_ids"]] = position_10
        first_position_c11[sub["entity_ids"]] = position_11

        replay = monotonicity_replay_direction(sub, thresholds_11, tables["length"][sub["entity_ids"]])
        monotonicity_reports.append({"direction": direction_def["direction"], **replay})

        for receipt in receipts_01:
            layer_receipts_table_01.append({"direction": direction_def["direction"], **receipt})
        for receipt in receipts_11:
            certificate_table_11.append({"direction": direction_def["direction"], **receipt})

        direction_reports.append(
            {
                "direction": direction_def["direction"],
                "fold": direction_def["fold"],
                "calibration_half": direction_def["calibration_half"],
                "evaluation_half": direction_def["evaluation_half"],
                "calibration_benign_entities": int(len(calibration_benign)),
                "evaluation_entities": int(len(evaluation)),
                "c00_threshold": tau_c00,
                "c10_threshold": tau_c10,
                "c01_layer_thresholds": thresholds_01.tolist(),
                "c11_layer_thresholds": thresholds_11.tolist(),
                "lambda_receipt_01": lambda_receipt_01,
                "lambda_receipt_11": lambda_receipt_11,
            }
        )
        lambda_summary = (
            f" λ(C01)={lambda_receipt_01['lambda']:.6f} λ(C11)={lambda_receipt_11['lambda']:.6f}"
            if args.construction == "b"
            else ""
        )
        log(
            f"方向{direction_def['direction']} 完成：C00τ={tau_c00:.6f} C10τ={tau_c10:.6f} "
            f"C11证书成立={all(r.get('certificate_valid') for r in receipts_11)} "
            f"单调性={'过' if replay['monotonic'] else '不过'}{lambda_summary}"
        )

    if not np.array_equal(evaluation_coverage, np.ones(total_entities, dtype=np.int32)):
        raise RuntimeError("六方向评价半未恰好覆盖全部实体一次，S_a/S_b 池化汇总失效")

    global_c10 = m1_outcome["global_alerts"]["M1"]
    metrics = {
        "C00_fixed_threshold": pooled_q0.alert_rates(global_c00, labels),
        "C01_stratified_only": pooled_q0.alert_rates(global_c01, labels),
        "C10_pooled_tong": pooled_q0.alert_rates(global_c10, labels),
        "C11_stratified_tong": pooled_q0.alert_rates(global_c11, labels),
    }
    five_bucket = {
        "C00_fixed_threshold": five_bucket_rates(global_c00, labels, tables["length"]),
        "C01_stratified_only": five_bucket_rates(global_c01, labels, tables["length"]),
        "C10_pooled_tong": five_bucket_rates(global_c10, labels, tables["length"]),
        "C11_stratified_tong": five_bucket_rates(global_c11, labels, tables["length"]),
    }
    c11_layer_rates = layer_rates(global_c11, labels, tables["length"])

    positive = labels == 1
    common = positive & global_c10 & global_c11
    common_count = int(common.sum())
    if common_count == 0:
        gate5 = True
        gate5_detail = {
            "common_positive_entities": 0,
            "note": "无共同检出正实体，配对中位数比较真空成立",
        }
    else:
        median_c10 = float(np.median(first_position_c10[common]))
        median_c11 = float(np.median(first_position_c11[common]))
        gate5 = bool(median_c11 <= median_c10)
        gate5_detail = {
            "common_positive_entities": common_count,
            "median_first_alert_position_c10": median_c10,
            "median_first_alert_position_c11": median_c11,
            "not_worsened": gate5,
        }

    gate1 = metrics["C11_stratified_tong"]["entity_fpr"] <= BUDGET_FPR
    gate2 = all(layer["entity_fpr"] <= BUDGET_FPR for layer in c11_layer_rates)
    gate3 = metrics["C11_stratified_tong"]["entity_dr"] >= metrics["C10_pooled_tong"]["entity_dr"]
    gate4 = all(cell.get("certificate_valid") for cell in certificate_table_11)
    monotonic_overall = all(report["monotonic"] for report in monotonicity_reports)
    qualified = bool(gate1 and gate2 and gate3 and gate4 and gate5)

    lambda_summary_top = (
        None
        if args.construction == "a"
        else [
            {
                "direction": d["direction"],
                "lambda_c01": d["lambda_receipt_01"]["lambda"],
                "lambda_c11": d["lambda_receipt_11"]["lambda"],
                "lambda_c01_available": d["lambda_receipt_01"]["available"],
                "lambda_c11_available": d["lambda_receipt_11"]["available"],
            }
            for d in direction_reports
        ]
    )

    result = {
        "schema_version": (
            "ch4-mlp-o11-stratified-tong-2x2-local-screen-recal-v1"
            if args.construction == "a"
            else "ch4-mlp-o11-stratified-tong-2x2-local-screen-sb-v1"
        ),
        "run_id": run_id,
        "construction": args.construction,
        "screening_only": True,
        "formal_paper_evidence": False,
        "target_year_arrays_read": 0,
        "precision": "fp32",
        "device_type": device.type,
        "calibration_fix": {
            "fixed_2026_08_27_before_first_run": True,
            "note": (
                "C00/C01/C10/C11 全部经由 pooled_q0.threshold_for_allowed_count / "
                "pathology 模块 calibrate_threshold 取阈值，两者均已在首次真实运行前"
                "自查并对齐 983ff49/a43909c 的『预算内尽量压低阈值』修复语义，"
                "详见 ch4_mlp_o11_tong_pooled_q0_local_screen.py 的同名字段"
            ),
        },
        "fold_assignment_sha256": context["fold_sha"],
        "half_assignment_sha256": m1_outcome["halves_sha256"],
        "seed": SEED,
        "direction_count": DIRECTION_COUNT,
        "layer_count": LAYER_COUNT,
        "layer_bounds": [[low, high] for low, high in LAYER_BOUNDS],
        "delta_global": DELTA_GLOBAL,
        "delta_per_cell": DELTA_PER_CELL,
        "budget_entity_fpr": BUDGET_FPR,
        "evaluation_population": {"entities": total_entities, "positive_entities": int(labels.sum())},
        "directions": direction_reports,
        "metrics": metrics,
        "five_bucket_diagnostic_disclosure": five_bucket,
        "c11_layer_rates": c11_layer_rates,
        "c01_layer_threshold_table": layer_receipts_table_01,
        "c11_certificate_table_24": certificate_table_11,
        "lambda_search": (
            None
            if args.construction == "a"
            else {"iterations": LAMBDA_SEARCH_ITERATIONS, "per_direction": lambda_summary_top}
        ),
        "monotonicity_replay": {
            "perturbations": list(MONOTONICITY_PERTURBATIONS),
            "per_direction": monotonicity_reports,
            "monotonic_overall": monotonic_overall,
        },
        "paired_common_positive_alert_position": gate5_detail,
        "gates": {
            "gate1_pooled_fpr_le_budget": bool(gate1),
            "gate2_all_certificate_layers_fpr_le_budget": bool(gate2),
            "gate3_dr_c11_ge_c10": bool(gate3),
            "gate4_all_24_certificates_valid": bool(gate4),
            "gate5_paired_median_not_worsened": bool(gate5),
        },
        "mechanical_verdict": {
            "qualified": qualified,
            "monotonicity_replay_passed": monotonic_overall,
            "verdict": (
                f"S_{args.construction.upper()}_STRATIFIED_TONG_LOCAL_SCREEN_"
                f"{'SUPPORTED' if qualified else 'NOT_SUPPORTED'}"
            ),
            "rule": (
                "gate1 AND gate2 AND gate3 AND gate4 AND gate5"
                "（任一失败=>机制a否决或缩小，四-S_a预注册；构造 B 沿用同一预注册规则）"
            ),
        },
    }
    atomic_json(output_root / "results.json", result)
    log(
        f"S_{args.construction} 门={'过' if qualified else '不过'}：g1={gate1} g2={gate2} g3={gate3} "
        f"g4={gate4} g5={gate5} 单调性重放={'过' if monotonic_overall else '不过'}"
    )
    print(f"LOCAL_SCREEN_STRATIFIED_2X2_{args.construction.upper()}_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
