"""告警预算曲线重分析：对已落盘的 LSPR24 逐流分数重新计算实体级检出率随假阳率的曲线、
前 k 个实体的精确率与曲线交叉点。本脚本不训练任何模型，只读取既有预测制品。

实体映射与标签构造语义照抄 tools/ch3_2x2_fairsel.py 的 key24/ent24/ent_lab 段：
无向 IP 对为实体键，实体标签取该实体内逐流标签的最大值。
本实现用整数编码的无向对代替字符串拼接键，划分完全等价（另有随机子样本双射核验），
并保留三项自检：47,115 实体 / 752 正实体 / 逐流正例率 0.0257073138。
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout)
logger = logging.getLogger("ch3_alert_budget")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAG = os.path.join(ROOT, "runs", "diagnostics")
CACHE = os.path.join(DIAG, "dijk-repro", "cache")
OUT = os.path.join(DIAG, "ch3-alert-budget-curve")
os.makedirs(OUT, exist_ok=True)

N_ENT_EXPECT = 47115
N_POS_EXPECT = 752
FLOW_POS_EXPECT = 0.0257073138

# 各方法自身设计的聚合算子：max 为按实体取逐流最高分；lp 为学习到的幂平均指数。
P_C11 = 1.0562171936035156       # 取自 ch3-2x2-fairsel/ch3_2x2_fairsel_results.json cells.C11.p
P_XGB = 1.2235541820526123       # 取自 ch3-xgb-entity/xgb_entity.json p_learned

TARGETS = [0.001, 0.005, 0.01, 0.02, 0.04, 0.08]
TOPK = [10, 25, 50, 100, 250, 500, 752]


@dataclass(frozen=True)
class Method:
    """一个待分析方法：展示名、逐流分数路径、覆盖掩码路径、自身聚合算子。"""

    key: str
    display: str
    scores_path: str
    seen_path: Optional[str]
    own_agg: str               # "max" 或 "lp"
    p: Optional[float]         # own_agg == "lp" 时的幂指数


METHODS: List[Method] = [
    Method("ours_c11", "本方法（队列聚合＋学习幂平均，等参数90K）",
           f"{DIAG}/ch3-2x2-fairsel/scores_C11.npy",
           f"{DIAG}/ch3-2x2-fairsel/seen_C11.npy", "lp", P_C11),
    Method("transformer_full", "全注意力Transformer（Dijk 2026 发表配置，10.73M参数）",
           f"{DIAG}/ch3-baselines-full/scores_transformer_dijk2026.npy", None, "max", None),
    Method("transformer_pm90k", "全注意力Transformer（Dijk 2026 注意力骨干，等参数90K）",
           f"{DIAG}/ch3-baselines-param-matched/scores_transformer_dijk2026_pm90k.npy",
           None, "max", None),
    Method("xgboost_full", "XGBoost（Dijk 2026 提升树，发表配置）",
           f"{DIAG}/ch3-xgb-entity/scores_xgb.npy", None, "max", None),
    Method("cnn_pm90k", "一维CNN（Leoste 2025 卷积，等参数90K）",
           f"{DIAG}/ch3-baselines-param-matched/scores_cnn_leoste2025_pm90k.npy",
           None, "max", None),
]


# =====================================================================================
# 实体映射
# =====================================================================================
def build_entity_mapping() -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """构造实体编号、实体标签、逐流标签与逐流正例率，带缓存。"""
    ent_cache = os.path.join(CACHE, "ent24_local.npy")
    y24 = np.load(os.path.join(CACHE, "y24.npy"))
    flow_pos = float(y24.astype(np.float64).mean())

    if os.path.exists(ent_cache):
        ent24 = np.load(ent_cache)
        logger.info("实体映射缓存命中 %s", ent_cache)
    else:
        t0 = time.time()
        s24 = np.load(os.path.join(CACHE, "s24.npy"), allow_pickle=True)
        codes_s, uniq_s = pd.factorize(s24)
        logger.info("源地址编码完成 唯一值=%d 用时 %.1f 秒", len(uniq_s), time.time() - t0)
        del s24

        d24 = np.load(os.path.join(CACHE, "d24.npy"), allow_pickle=True)
        idx = pd.Index(uniq_s)
        codes_d = idx.get_indexer(d24)
        miss = codes_d < 0
        n_miss = int(miss.sum())
        if n_miss:
            extra_codes, extra_uniq = pd.factorize(d24[miss])
            codes_d[miss] = extra_codes + len(uniq_s)
            n_uniq = len(uniq_s) + len(extra_uniq)
        else:
            n_uniq = len(uniq_s)
        logger.info("目的地址编码完成 新增唯一值=%d 总唯一地址=%d 用时 %.1f 秒",
                    n_miss, n_uniq, time.time() - t0)
        del d24, idx, uniq_s

        lo = np.minimum(codes_s, codes_d).astype(np.int64)
        hi = np.maximum(codes_s, codes_d).astype(np.int64)
        del codes_s, codes_d
        pair = lo * np.int64(n_uniq) + hi
        del lo, hi
        _, ent24 = np.unique(pair, return_inverse=True)
        ent24 = ent24.astype(np.int32)
        del pair
        np.save(ent_cache, ent24)
        logger.info("实体编号构造完成 用时 %.1f 秒，已缓存 %s", time.time() - t0, ent_cache)

    n_ent = int(ent24.max()) + 1
    ent_lab = np.zeros(n_ent, np.float32)
    np.maximum.at(ent_lab, ent24, y24)

    assert n_ent == N_ENT_EXPECT, f"LSPR24 实体数自检失败：{n_ent}"
    assert int(ent_lab.sum()) == N_POS_EXPECT, f"LSPR24 正例实体自检失败：{int(ent_lab.sum())}"
    assert abs(flow_pos - FLOW_POS_EXPECT) < 1e-9, f"LSPR24 逐流正例率自检失败：{flow_pos:.12f}"
    logger.info("自检通过：实体 %d / 正例实体 %d / 逐流正例率 %.10f", n_ent, int(ent_lab.sum()), flow_pos)
    return ent24, ent_lab, y24, flow_pos


def verify_partition_against_string_key(ent24: np.ndarray, n_sample: int = 200_000) -> Dict:
    """在随机子样本上核验整数编码划分与原字符串键划分是否为同一划分。"""
    rng = np.random.default_rng(20260818)
    pick = rng.choice(len(ent24), size=n_sample, replace=False)
    pick.sort()
    s24 = np.load(os.path.join(CACHE, "s24.npy"), allow_pickle=True)
    a = s24[pick]
    del s24
    d24 = np.load(os.path.join(CACHE, "d24.npy"), allow_pickle=True)
    b = d24[pick]
    del d24
    key = np.array([x + "|" + y if x <= y else y + "|" + x for x, y in zip(a, b)], object)
    _, ref = np.unique(key, return_inverse=True)
    mine = ent24[pick]
    # 同一划分的充要条件：两个方向的分组映射都是函数（单值）。
    df = pd.DataFrame({"ref": ref, "mine": mine})
    fwd = int(df.groupby("ref")["mine"].nunique().max())
    bwd = int(df.groupby("mine")["ref"].nunique().max())
    ok = (fwd == 1) and (bwd == 1)
    logger.info("子样本划分核验：样本=%d 组数=%d 正向最大像数=%d 反向最大像数=%d 结论=%s",
                n_sample, int(df["ref"].nunique()), fwd, bwd, "一致" if ok else "不一致")
    assert ok, "整数编码划分与字符串键划分不一致"
    return {"n_sample": n_sample, "n_group": int(df["ref"].nunique()),
            "max_forward_images": fwd, "max_backward_images": bwd, "identical": ok}


# =====================================================================================
# 实体级聚合
# =====================================================================================
class Aggregator:
    """按实体分段聚合逐流分数。预排序一次，后续所有方法复用。"""

    def __init__(self, ent24: np.ndarray, n_ent: int):
        self.n_ent = n_ent
        t0 = time.time()
        self.order = np.argsort(ent24, kind="stable")
        e = ent24[self.order]
        self.starts = np.flatnonzero(np.r_[True, e[1:] != e[:-1]])
        assert len(self.starts) == n_ent, f"分段数 {len(self.starts)} 与实体数 {n_ent} 不符"
        assert np.array_equal(e[self.starts], np.arange(n_ent, dtype=e.dtype)), "分段起点与实体编号不对齐"
        logger.info("实体分段排序完成 用时 %.1f 秒", time.time() - t0)

    def entity_scores(self, sc: np.ndarray, seen: np.ndarray, p: Optional[float]) -> np.ndarray:
        """p 为 None 时取实体内最大值；否则取幂平均，语义照抄冻结实现。"""
        if p is None:
            v = np.where(seen, sc, np.float32(-np.inf)).astype(np.float32)[self.order]
            es = np.maximum.reduceat(v, self.starts)
            return es.astype(np.float32)
        w = np.where(seen, np.clip(sc, 1e-7, 1.0).astype(np.float64) ** p, 0.0)[self.order]
        c = seen.astype(np.float64)[self.order]
        num = np.add.reduceat(w, self.starts)
        cnt = np.add.reduceat(c, self.starts)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf)
        return es.astype(np.float32)


# =====================================================================================
# 指标
# =====================================================================================
def budget_curve(es: np.ndarray, ent_lab: np.ndarray) -> Dict[str, np.ndarray]:
    """完整告警预算曲线。

    阈值取自负实体分数的降序序列：允许 j 个负实体排在阈值之前时，阈值为 neg[j]，
    检出率为分数不低于该阈值的正实体比例。这与冻结实现 dr_at_fpr 在
    j = int(n_neg * target) 处逐点等价。
    """
    ok = np.isfinite(es)
    v = es[ok]
    lab = ent_lab[ok]
    pos = np.sort(v[lab == 1])
    neg = np.sort(v[lab == 0])[::-1]
    n_pos, n_neg = len(pos), len(neg)
    thr = neg                                            # j -> 阈值
    dr = (n_pos - np.searchsorted(pos, thr, side="left")) / n_pos
    neg_asc = neg[::-1]
    n_fp = n_neg - np.searchsorted(neg_asc, thr, side="left")   # 实际触发的假阳实体数
    return {"thr": thr, "dr": dr, "nominal_fpr": np.arange(n_neg) / n_neg,
            "realized_fpr": n_fp / n_neg, "n_fp": n_fp,
            "n_pos": n_pos, "n_neg": n_neg, "n_scored": int(ok.sum())}


def dr_at_targets(curve: Dict, targets: List[float]) -> Dict[str, Dict[str, float]]:
    out = {}
    n_neg = curve["n_neg"]
    for t in targets:
        j = min(int(n_neg * t), n_neg - 1)
        n_fp = int(curve["n_fp"][j])
        n_tp = float(curve["dr"][j]) * curve["n_pos"]
        out[f"{t:.4f}"] = {
            "target_fpr": t,
            "dr": float(curve["dr"][j]),
            "realized_fpr": float(curve["realized_fpr"][j]),
            "n_false_positive_entity": n_fp,
            "n_true_positive_entity": int(round(n_tp)),
            "alert_precision": float(n_tp / max(n_tp + n_fp, 1e-9)),
        }
    return out


def precision_at_k(es: np.ndarray, ent_lab: np.ndarray, ks: List[int]) -> Dict[str, Dict[str, float]]:
    ok = np.isfinite(es)
    v = es[ok]
    lab = ent_lab[ok]
    order = np.argsort(-v, kind="stable")
    hits = np.cumsum(lab[order] == 1)
    out = {}
    for k in ks:
        n_hit = int(hits[k - 1])
        out[str(k)] = {"k": k, "precision": n_hit / k, "n_hit": n_hit,
                       "recall": n_hit / int((lab == 1).sum())}
    return out


def find_crossings(curve_a: Dict, curve_b: Dict) -> List[Dict]:
    """在共同的假阳预算网格上找 a 与 b 的检出率曲线符号变化点。"""
    n = min(len(curve_a["dr"]), len(curve_b["dr"]))
    diff = curve_a["dr"][:n] - curve_b["dr"][:n]
    sign = np.sign(diff)
    nz = sign != 0
    idx = np.flatnonzero(nz)
    crossings = []
    if len(idx) == 0:
        return crossings
    prev = idx[0]
    for i in idx[1:]:
        if sign[i] != sign[prev]:
            crossings.append({
                "j_before": int(prev), "j_after": int(i),
                "nominal_fpr_before": float(curve_a["nominal_fpr"][prev]),
                "nominal_fpr_after": float(curve_a["nominal_fpr"][i]),
                "n_fp_before": int(curve_a["n_fp"][prev]), "n_fp_after": int(curve_a["n_fp"][i]),
                "diff_before": float(diff[prev]), "diff_after": float(diff[i]),
                "sign_before": float(sign[prev]), "sign_after": float(sign[i]),
            })
        prev = i
    return crossings


# =====================================================================================
# 主流程
# =====================================================================================
def main() -> None:
    t_all = time.time()
    ent24, ent_lab, y24, flow_pos = build_entity_mapping()
    n_ent = len(ent_lab)
    part = verify_partition_against_string_key(ent24)
    agg = Aggregator(ent24, n_ent)
    del ent24

    results: Dict[str, Dict] = {}
    curves: Dict[str, Dict] = {}
    for m in METHODS:
        if not os.path.exists(m.scores_path):
            logger.warning("缺少分数文件，跳过 %s：%s", m.key, m.scores_path)
            continue
        t0 = time.time()
        sc = np.load(m.scores_path)
        seen = np.load(m.seen_path) if m.seen_path else np.ones(len(sc), bool)
        assert len(sc) == len(y24), f"{m.key} 分数长度 {len(sc)} 与标签长度 {len(y24)} 不符"
        entry: Dict = {"display_name": m.display, "own_aggregator": m.own_agg,
                       "p": m.p, "flow_coverage": float(seen.mean()),
                       "scores_path": os.path.relpath(m.scores_path, ROOT)}
        for tag, p in [("max", None), ("lp", m.p)]:
            if tag == "lp" and p is None:
                continue
            es = agg.entity_scores(sc, seen, p)
            cur = budget_curve(es, ent_lab)
            okm = np.isfinite(es)
            entry[tag] = {
                "entity_ap": float(average_precision_score(ent_lab[okm], es[okm])),
                "n_ent_scored": int(okm.sum()),
                "dr_at_fpr": dr_at_targets(cur, TARGETS),
                "precision_at_k": precision_at_k(es, ent_lab, TOPK),
            }
            curves[f"{m.key}|{tag}"] = cur
            del es
        entry["primary"] = entry[m.own_agg]
        results[m.key] = entry
        logger.info("%s 完成 用时 %.1f 秒 主口径实体AP=%.6f DR@4%%FPR=%.6f",
                    m.key, time.time() - t0, entry["primary"]["entity_ap"],
                    entry["primary"]["dr_at_fpr"]["0.0400"]["dr"])
        del sc, seen

    # 冻结数值复现自检
    checks = []
    if "ours_c11" in results:
        checks.append(("本方法 实体AP(lp)", results["ours_c11"]["lp"]["entity_ap"], 0.5183504153978865))
        checks.append(("本方法 DR@4%FPR(lp)", results["ours_c11"]["lp"]["dr_at_fpr"]["0.0400"]["dr"],
                       0.7034574468085106))
        checks.append(("本方法 实体AP(max)", results["ours_c11"]["max"]["entity_ap"], 0.2917386097674079))
    if "transformer_full" in results:
        checks.append(("发表配置Transformer 实体AP(max)",
                       results["transformer_full"]["max"]["entity_ap"], 0.35361998859558863))
        checks.append(("发表配置Transformer DR@4%FPR(max)",
                       results["transformer_full"]["max"]["dr_at_fpr"]["0.0400"]["dr"],
                       0.7406914893617021))
    if "xgboost_full" in results:
        checks.append(("XGBoost 实体AP(max)", results["xgboost_full"]["max"]["entity_ap"], 0.512898847990404))
        checks.append(("XGBoost DR@4%FPR(max)",
                       results["xgboost_full"]["max"]["dr_at_fpr"]["0.0400"]["dr"], 0.6928191489361702))
    if "cnn_pm90k" in results:
        checks.append(("等参数CNN 实体AP(max)", results["cnn_pm90k"]["max"]["entity_ap"], 0.5206531036853225))
        checks.append(("等参数CNN DR@4%FPR(max)",
                       results["cnn_pm90k"]["max"]["dr_at_fpr"]["0.0400"]["dr"], 0.6715425531914894))
    if "transformer_pm90k" in results:
        checks.append(("等参数Transformer 实体AP(max)",
                       results["transformer_pm90k"]["max"]["entity_ap"], 0.32925269120940276))
    check_rows = []
    for name, got, want in checks:
        d = abs(got - want)
        check_rows.append({"item": name, "recomputed": got, "frozen": want, "abs_diff": d,
                           "pass": bool(d < 1e-6)})
        logger.info("复现自检 %s 重算=%.12f 冻结=%.12f 差=%.3e %s",
                    name, got, want, d, "通过" if d < 1e-6 else "不通过")

    # 交叉点
    cross: Dict[str, Dict] = {}
    if "ours_c11|lp" in curves and "transformer_full|max" in curves:
        a, b = curves["ours_c11|lp"], curves["transformer_full|max"]
        cs = find_crossings(a, b)
        cross["ours_lp_vs_transformer_full_max"] = {
            "note": "本方法（学习幂平均）减 发表配置全注意力Transformer（max）",
            "first_crossings": cs[:8], "last_crossings": cs[-8:], "n_crossing": len(cs),
            "sign_at_targets": {f"{t:.4f}": float(np.sign(
                a["dr"][min(int(a["n_neg"] * t), a["n_neg"] - 1)]
                - b["dr"][min(int(b["n_neg"] * t), b["n_neg"] - 1)])) for t in TARGETS}}
    if "ours_c11|max" in curves and "transformer_full|max" in curves:
        cs = find_crossings(curves["ours_c11|max"], curves["transformer_full|max"])
        cross["ours_max_vs_transformer_full_max"] = {
            "note": "同为 max 聚合的对照", "first_crossings": cs[:8],
            "last_crossings": cs[-8:], "n_crossing": len(cs)}

    # 细网格曲线导出（供后续画图）
    grid = np.unique(np.r_[
        np.round(np.geomspace(1, 200, 60)).astype(int),
        np.round(np.geomspace(200, 46362, 140)).astype(int)])
    grid = grid[grid < min(len(c["dr"]) for c in curves.values())]
    export = {"j": grid.tolist()}
    for name, c in curves.items():
        export[f"dr__{name}"] = np.round(c["dr"][grid], 8).tolist()
        export[f"realized_fpr__{name}"] = np.round(c["realized_fpr"][grid], 8).tolist()
    pd.DataFrame(export).to_csv(f"{OUT}/budget_curve_grid.csv", index=False)

    payload = {
        "protocol": "对已落盘的 LSPR24 逐流分数重新分析，不训练模型、不重新推理",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "lspr24": {"n_flow": int(len(y24)), "n_entity": n_ent,
                   "n_pos_entity": int(ent_lab.sum()), "flow_pos_rate": flow_pos,
                   "entity_prior": float(ent_lab.mean())},
        "partition_verification": part,
        "targets": TARGETS, "topk": TOPK,
        "methods": results, "frozen_reproduction_check": check_rows,
        "crossings": cross,
        "elapsed_seconds": time.time() - t_all,
    }
    with open(f"{OUT}/alert_budget_curves.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("结果已写入 %s/alert_budget_curves.json，总用时 %.1f 秒", OUT, time.time() - t_all)


if __name__ == "__main__":
    main()
