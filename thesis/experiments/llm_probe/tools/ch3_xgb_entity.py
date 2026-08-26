# -*- coding: utf-8 -*-
"""XGBoost 基线的实体级评价，与冻结 C11 逐字对齐。

目的只有一个：把已发表基线放到第三章正文所用的评价单元上，得到一个可以与
冻结 C11 并排的数字。不训练神经模型、不改机制、不创建新的评价口径。

对齐方式（逐字复刻 ch3_full.py，行号见注释）：
  实体键     ch3_full.py:130-133  sortlex{srcIP,dstIP}，实体标签取组内逐流标签的最大值
  Lp 聚合    ch3_full.py:221-223  (sum s^p / n)^(1/p)，最后转 float32
  max 聚合   ch3_full.py:219      组内最大，float32
  DR@FPR     ch3_full.py:236-240  负实体分数降序，取第 int(n_neg*target) 位作阈值
  Lp 指数    冻结 C11 学到的 1.2235541820526123；max 聚合不需要 p

自检：启动时先用 ch3-full 落盘的 scores_C11.npy / seen_C11.npy 重算 C11 的三个
数字，与 run.log 第 16 行逐位比对。比对不过说明本文件的聚合或判据实现与冻结口径
不一致，直接停止，不允许带着未对齐的实现去跑 XGBoost。

XGBoost 超参逐字取服务器既有 tools/entity_eval.py（等价于 dijk_fields.py 的冻结
XGBOOST_PARAMS + §5.6 的 800 棵树），故本次逐流 AP 可直接与该脚本已得的
0.2244424863 对表。字段预算与 C11 完全相同（83 字段，DROP 清单一致），
两者的差异只来自模型与聚合，不来自可见信息量。

输入取 dijk-repro/cache 下的 X23/X24——这是 C11 训练与评价所用的同一份矩阵，
其中非有限值已被置 0（ch3_full.py:91）。entity_eval.py 当年把非有限值置为 NaN
并交给 XGBoost 原生缺失处理，所以本次逐流 AP 与 0.2244424863 会有小幅偏离；
用缓存换取的是「XGBoost 与 C11 看到逐位相同的输入」，这是并排比较更需要的性质。
"""
import json
import os
import time

import numpy as np
from sklearn.metrics import average_precision_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
CH3 = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-full"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-xgb-entity"
os.makedirs(OUT, exist_ok=True)
# C11 学到的 Lp 指数：取 ch3-full/results.json 的全精度值，不用日志里四舍五入的 1.2236
P_LEARNED = 1.2235541820526123
TARGET_FPR = 0.04
# 冻结 C11 的对照数字，全精度取自 ch3-full 结果 JSON 的 cells.C11（run.log 第 16 行是其四舍五入）
C11 = {"flow_ap": 0.2315713900260571, "ent_ap_max": 0.3858276572759182,
       "ent_ap_lp": 0.46298806991944896, "dr_at_fpr": 0.6954787234042553}
# entity_eval.py 当年在 NaN-缺失输入上得到的锚点，只作量级参照，不进正文表
ANCHOR = {"flow_ap": 0.2244424863, "ent_ap_n1": 0.523326, "ent_ap_n100": 0.547484}

DEVICE = os.environ.get("XGB_DEVICE", "cpu")
N_JOBS = int(os.environ.get("XGB_NJOBS", "96"))

# 数据身份：X23/X24 是 dijk 复现管线标准化后的特征矩阵（非有限值置 0 → 按 LSPR23 逐列均值和
# 标准差标准化 → 裁剪 [-10, 10]），不是 raw83 原值；形状、dtype 与文件字节数都与 raw83 产品相同
# 但内容不同。本脚本训练与评价都用它，口径自洽；换成 raw83 拟合的模型则不可直接读。见缓存 README.md。
X23 = np.load(f"{CACHE}/X23.npy"); y23 = np.load(f"{CACHE}/y23.npy")
X24 = np.load(f"{CACHE}/X24.npy"); y24 = np.load(f"{CACHE}/y24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
log(f"缓存命中：LSPR23 {X23.shape} LSPR24 {X24.shape}")
assert X23.shape[1] == 83 and X24.shape[1] == 83, "字段预算必须是 83，与 C11 一致"
FLOW_PI = float(y24.mean())
log(f"LSPR24 逐流正例率={FLOW_PI:.10f}")
assert abs(FLOW_PI - 0.0257073138) < 1e-10, f"逐流正例率 {FLOW_PI} 与冻结口径不符"

# ---- 实体构造：逐字复刻 ch3_full.py:130-133 ----
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = int(ent24.max()) + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
log(f"LSPR24 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 先验={ent_lab.mean():.10f}")
assert N_ENT == 47115, f"实体数 {N_ENT} 与冻结口径 47,115 不符，实体构造未对齐"
assert int(ent_lab.sum()) == 752, f"正例实体 {int(ent_lab.sum())} 与冻结口径 752 不符"
del key24, s24, d24


def ent_scores(sc, p=None, m=None):
    """ch3_full.py:219-223 的聚合，包含最后的 float32 转换。m 即 ch3_full 的 seen 掩码。"""
    if m is None:
        e, s = ent24, sc
    else:
        e, s = ent24[m], sc[m]
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, e, s)
        return es
    num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
    np.add.at(num, e, np.clip(s, 1e-7, 1.0).astype(np.float64) ** p)
    np.add.at(cnt, e, 1.0)
    return np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)


def ent_ap(es):
    """ch3_full.py:224-225：只在有分数的实体上算 AP。"""
    ok = np.isfinite(es)
    return float(average_precision_score(ent_lab[ok], es[ok]))


def dr_at_fpr(es, target=TARGET_FPR):
    """ch3_full.py:236-240 的判据，逐字复刻，含同一处取整方式。"""
    ok = np.isfinite(es); v = es[ok]; l = ent_lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0:
        return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


# ---- 对齐自检：用冻结的 C11 分数重算三个数字 ----
sc11 = np.load(f"{CH3}/scores_C11.npy"); seen11 = np.load(f"{CH3}/seen_C11.npy")
chk = {"flow_ap": float(average_precision_score(y24[seen11], sc11[seen11])),
       "ent_ap_max": ent_ap(ent_scores(sc11, None, seen11)),
       "ent_ap_lp": ent_ap(ent_scores(sc11, P_LEARNED, seen11)),
       "dr_at_fpr": dr_at_fpr(ent_scores(sc11, P_LEARNED, seen11))}
log(f"C11 覆盖={seen11.mean():.6f}  自检重算 {json.dumps({k: round(v, 10) for k, v in chk.items()})}")
for k, want in C11.items():
    assert abs(chk[k] - want) < 1e-8, f"自检失败 {k}: 重算 {chk[k]} 与冻结 {want} 不符，聚合或判据未对齐"
log("自检通过：本文件的聚合与 DR 判据与冻结 C11 口径逐位一致")
del sc11, seen11

# ---- XGBoost：逐字取 entity_eval.py 的超参（= dijk_fields.XGBOOST_PARAMS + 800 树）----
import xgboost as xgb

PARAMS = dict(n_estimators=800, learning_rate=0.05, max_depth=8,
              subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
              tree_method="hist", device=DEVICE, eval_metric="aucpr",
              n_jobs=N_JOBS, random_state=42)
log(f"xgboost {xgb.__version__}  device={DEVICE} n_jobs={N_JOBS}")

# 先用 25 棵树测真实速度，给出全程 ETA，避免长任务无进度可观测
t_probe = time.time()
xgb.XGBClassifier(**{**PARAMS, "n_estimators": 25}).fit(X23, y23, verbose=False)
per_tree = (time.time() - t_probe) / 25
log(f"速度探针：25 棵树用时 {time.time()-t_probe:.0f}s，单棵约 {per_tree:.1f}s，"
    f"800 棵预计 {per_tree*800/60:.0f} 分（含建矩阵开销，实际会略少）")

t_fit = time.time()
clf = xgb.XGBClassifier(**PARAMS)
clf.fit(X23, y23, verbose=False)
log(f"训练完成，用时 {(time.time()-t_fit)/60:.1f} 分")
del X23, y23

sc = np.empty(len(y24), np.float32)
B = 2_000_000
for a in range(0, len(y24), B):
    sc[a:a + B] = clf.predict_proba(X24[a:a + B])[:, 1].astype(np.float32)
    log(f"  推理进度 {min(a+B, len(y24)):,}/{len(y24):,}")
del X24
log("LSPR24 推理完成")
np.save(f"{OUT}/scores_xgb.npy", sc)

es_max, es_lp = ent_scores(sc, None), ent_scores(sc, P_LEARNED)
row = {"flow_ap": float(average_precision_score(y24, sc)),
       "ent_ap_max": ent_ap(es_max), "ent_ap_lp": ent_ap(es_lp),
       "dr_at_fpr_max": dr_at_fpr(es_max), "dr_at_fpr_lp": dr_at_fpr(es_lp)}

W = 96
print("\n" + "=" * W, flush=True)
print("XGBoost 基线与冻结 CPA-ELP（C11）在同一评价单元下的对照", flush=True)
print(f"{'方法':<26}{'逐流 AP':>12}{'实体 AP(max)':>14}{'实体 AP(Lp)':>14}"
      f"{'DR@4%FPR(max)':>15}{'DR@4%FPR(Lp)':>14}", flush=True)
print(f"{'XGBoost（Dijk 配置）':<26}{row['flow_ap']:>12.6f}{row['ent_ap_max']:>14.6f}"
      f"{row['ent_ap_lp']:>14.6f}{row['dr_at_fpr_max']:>15.4f}{row['dr_at_fpr_lp']:>14.4f}", flush=True)
print(f"{'CPA-ELP（冻结 C11）':<26}{C11['flow_ap']:>12.6f}{C11['ent_ap_max']:>14.6f}"
      f"{C11['ent_ap_lp']:>14.6f}{'—':>15}{C11['dr_at_fpr']:>14.4f}", flush=True)
print("-" * W, flush=True)
best_xgb_ap = max(row["ent_ap_max"], row["ent_ap_lp"])
best_xgb_dr = max(row["dr_at_fpr_max"], row["dr_at_fpr_lp"])
print(f"实体 AP：C11 最佳 {C11['ent_ap_lp']:.6f} − XGB 最佳 {best_xgb_ap:.6f} "
      f"= {C11['ent_ap_lp']-best_xgb_ap:+.6f}", flush=True)
print(f"DR@4%FPR：C11 {C11['dr_at_fpr']:.4f} − XGB 最佳 {best_xgb_dr:.4f} "
      f"= {C11['dr_at_fpr']-best_xgb_dr:+.4f}", flush=True)
print(f"逐流 AP：本次 {row['flow_ap']:.6f}   本仓库 NaN-缺失口径 {ANCHOR['flow_ap']:.6f}"
      f"（差 {row['flow_ap']-ANCHOR['flow_ap']:+.6f}）   Dijk 2026 表 5 = 0.2416"
      f"（差 {row['flow_ap']-0.2416:+.6f}）", flush=True)
print(f"参照：entity_eval.py 在 NaN-缺失输入上的实体 AP(n=1)={ANCHOR['ent_ap_n1']:.6f}", flush=True)
print(f"注：XGBoost 无学得的 Lp 指数，Lp 列借用 C11 的 p={P_LEARNED:.6f}，只作同口径参照。", flush=True)
print("=" * W, flush=True)

json.dump({"xgb": row, "c11_frozen": C11, "c11_recomputed_selfcheck": chk,
           "anchor_entity_eval_nan_missing": ANCHOR, "p_learned": P_LEARNED,
           "target_fpr": TARGET_FPR, "n_entity": N_ENT,
           "n_pos_entity": int(ent_lab.sum()), "flow_pi": FLOW_PI,
           "xgb_params": PARAMS, "xgboost_version": xgb.__version__,
           "cache": CACHE, "note": "输入取 C11 同一份缓存（非有限值置 0），与 NaN-缺失口径不同"},
          open(f"{OUT}/xgb_entity.json", "w"), ensure_ascii=False, indent=2)
log(f"结果已存 {OUT}/xgb_entity.json")
