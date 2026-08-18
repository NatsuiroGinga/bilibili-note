# -*- coding: utf-8 -*-
"""第三章已发表基线重跑（树模型族）：随机森林 + XGBoost，全量冻结缓存。

为什么重跑：服务器既有的 runs/baselines/lspr-baseline-dual-track-q0-seed42-v1/ 全部是
Q0 筛选制品（budget_tier=Q0, screening_only=true, formal_paper_evidence=false），训练只用
142,069 条流、测试用 261,839 条开发集、字段 77 而非 83，结果已退化到随机水平之下，不可进正文。
本脚本用与第三章方法逐位相同的输入矩阵重跑，产出可与 CPA-ELP 并排的主比较表。

============================ 统一协议 ============================
  训练集    LSPR23 全量 16,353,511 条流（树模型不做序列切分，直接逐流训练）
  测试集    LSPR24 全量 20,227,356 条流
  字段预算  83 维，直接取 X23/X24（非有限值已在 ch3_full.py:91 置 0）
  实体键    2-IP 无向对，LSPR24 得 47,115 实体 / 752 恶意实体
  种子      42
  模型超参  取自 Q0 的 run-config.json，只把数据规模改成全量，模型配置本身不动

============================ 模型配置来源 ============================
随机森林（Dijk 2024 装袋树）
  取自 track-a/dijk2024_rf_visible_full_extension/run-config.json 的 parameters：
    n_estimators=100, max_depth=None, bootstrap=True, class_weight=None
  本脚本自定：n_jobs（并行度，不影响模型定义）、random_state=42（Q0 由 seed 注入）
XGBoost（Dijk 2026 提升树）
  取自 track-a/dijk2026_xgboost/run-config.json 的 parameters，与 tools/ch3_xgb_entity.py
  第 125-128 行的冻结 PARAMS 完全一致（min_child_weight=1.0 / max_bin=256 即 xgboost 默认值）：
    n_estimators=800, learning_rate=0.05, max_depth=8, subsample=0.8,
    colsample_bytree=0.8, reg_lambda=1.0, tree_method=hist, eval_metric=aucpr
  **无 scale_pos_weight**（Dijk 2026 未使用，Q0 配置亦无此项）。
  n_jobs=128 取自锚点运行 runs/diagnostics/ch3-xgb-entity/xgb_entity.json 记录的实际值。

============================ 评价口径（逐字复刻 ch3_full.py）============================
  实体构造  ch3_full.py:130-133      ent_ap  ch3_full.py:213-225（Lp 含末尾 .astype(np.float32)）
  DR@FPR    ch3_full.py:236-240
  聚合算子  主表一律用 max（基线没有可学习的 Lp 指数）。额外报一列「借用本章
            p=1.0562171936035156 的 Lp 聚合」作敏感性参照，不进主表。

============================ LSPR24 隔离 ============================
  guarded_load() 是所有 np.load 的唯一入口，名字含 "24" 且 SELECTION_FROZEN 为假时断言失败。
  两个模型全部训练完 → selection_frozen.json 落盘 → SELECTION_FROZEN=True → 才允许读 LSPR24。
  score24() 每调用一次记一次，本进程合法总次数 == 2（树模型族 2 个）。
  神经模型族在 tools/ch3_baselines_full_neural.py 中另计 3 次，合并后总计 5 次。

不创建 SwanLab 运行身份。
"""

import json
import os
import time

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:8.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-baselines-full"
os.makedirs(OUT, exist_ok=True)

SEED = 42
TARGET_FPR = 0.04
# 本章 CPA-ELP（ch3_2x2_fairsel C11）学到的 Lp 指数全精度值，只作敏感性参照列
P_BORROW = 1.0562171936035156

# ---- XGBoost 锚点：runs/diagnostics/ch3-xgb-entity/xgb_entity.json，用于校验实现无偏差 ----
XGB_ANCHOR = {"flow_ap": 0.2223914545997109, "ent_ap_max": 0.512898847990404,
              "dr_at_fpr_max": 0.6928191489361702, "ent_ap_lp_at_p_borrow": 0.533104}
ANCHOR_TOL = 2e-4

# ---- 随机森林规模护栏：探针外推的森林体积超过此值就改用分组构建，避免 OOM ----
RF_MEM_GUARD_GIB = 40.0
RF_PROBE_TREES = 4
RF_N_ESTIMATORS = 100
RF_NJOBS = int(os.environ.get("RF_NJOBS", "32"))
XGB_NJOBS = int(os.environ.get("XGB_NJOBS", "128"))
PRED_BATCH = 2_000_000

# 2026-08-17 事故：首次运行按 free -g 报告的 754 GB 主机内存设 n_jobs=104，进程在 RF 全量拟合
# 起步处被 SIGKILL，日志无 traceback。实测容器 cgroup memory.max = 90 GiB，free 报的是宿主机。
# sklearn 随机森林每个并行树需要自己的 bootstrap 权重(float64)、bincount(int64)、样本索引与
# 分裂器缓冲，约 6 份 n_samples 长的数组；n_samples=16,353,511 时单线程约 0.75 GiB。
# 下面按容器实际可用内存机械地反推并行度上限，不再凭主机内存猜。
RF_BYTES_PER_THREAD = 6 * 16_353_511 * 8          # 保守估计：6 份 8 字节 × n_samples
RF_MEM_SAFETY = 0.55                              # 只用可用内存的 55% 给并行缓冲


def _cgroup_limit_bytes():
    for p in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            v = open(p).read().strip()
            if v and v != "max":
                return int(v)
        except OSError:
            continue
    return None


def _cgroup_current_bytes():
    for p in ("/sys/fs/cgroup/memory.current", "/sys/fs/cgroup/memory/memory.usage_in_bytes"):
        try:
            return int(open(p).read().strip())
        except OSError:
            continue
    return 0

SELECTION_FROZEN = False
_N24_LOADS = 0
_EVAL24_CALLS = 0
_EVAL24_LEDGER = []


def guarded_load(name, allow_pickle=False):
    """所有 np.load 的唯一入口。选择阶段禁止读入任何名字含 '24' 的数组。"""
    assert SELECTION_FROZEN or "24" not in name, \
        f"阶段闸门未开：选择阶段禁止读入 {name}.npy"
    return np.load(f"{CACHE}/{name}.npy", allow_pickle=allow_pickle)


# =====================================================================================
# 阶段一：只读入 LSPR23，训练两个树模型
# =====================================================================================
log("=" * 112)
log("阶段一 训练：只读入 LSPR23，LSPR24 不进入本进程")
X23 = guarded_load("X23")
y23 = guarded_load("y23")
D = X23.shape[1]
assert D == 83, f"特征数应为 83（Dijk 2026 附录 A 口径），实为 {D}"
assert X23.shape[0] == 16_353_511, f"LSPR23 全量流数自检失败：{X23.shape[0]}"
y23i = y23.astype(np.int8)
log(f"LSPR23 全量 {X23.shape[0]:,} 条流 × {D} 字段，正例率={float(y23.mean()):.10f}")

TRAINED = {}

# ------------------------------------------------------------------ 随机森林
log("=" * 112)
log("随机森林（Dijk 2024 装袋树）：先用探针测单棵树的耗时与节点数，再决定构建方式")
from sklearn.ensemble import RandomForestClassifier

RF_PARAMS = dict(n_estimators=RF_N_ESTIMATORS, max_depth=None, bootstrap=True,
                 class_weight=None, random_state=SEED)
log(f"  配置（取自 Q0 run-config.json）：{ {k: v for k, v in RF_PARAMS.items()} }")

# ---- 并行度门禁：按容器 cgroup 实际可用内存反推，不用 free 报告的宿主机内存 ----
_lim = _cgroup_limit_bytes()
_cur = _cgroup_current_bytes()
if _lim:
    _budget = max(_lim - _cur, 0) * RF_MEM_SAFETY
    _cap = max(1, int(_budget // RF_BYTES_PER_THREAD))
    log(f"  容器内存 cgroup 上限 {_lim/2**30:.1f} GiB，当前已用 {_cur/2**30:.1f} GiB，"
        f"按 {RF_MEM_SAFETY:.0%} 余量给并行缓冲 = {_budget/2**30:.1f} GiB")
    log(f"  单并行树估算缓冲 {RF_BYTES_PER_THREAD/2**30:.2f} GiB → 并行度上限 {_cap}")
    if _cap < RF_NJOBS:
        log(f"  ★ 请求的 n_jobs={RF_NJOBS} 超出内存上限，下调为 {_cap}")
        RF_NJOBS = _cap
else:
    log("  未读到 cgroup 内存上限，沿用请求的并行度")
log(f"  随机森林并行度 n_jobs={RF_NJOBS}")

_t = time.time()
_probe = RandomForestClassifier(**{**RF_PARAMS, "n_estimators": RF_PROBE_TREES},
                                n_jobs=RF_PROBE_TREES)
_probe.fit(X23, y23i)
_probe_s = time.time() - _t
_nodes = [int(e.tree_.node_count) for e in _probe.estimators_]
_depths = [int(e.tree_.max_depth) for e in _probe.estimators_]
# sklearn 每节点约 56 字节结构体 + n_classes*n_outputs*8 字节的 value
_bytes_per_node = 56 + 2 * 8
_proj_gib = float(np.mean(_nodes)) * RF_N_ESTIMATORS * _bytes_per_node / 2 ** 30
log(f"  探针 {RF_PROBE_TREES} 棵并行用时 {_probe_s/60:.2f} 分；单棵节点数 {_nodes}，最大深度 {_depths}")
log(f"  外推 {RF_N_ESTIMATORS} 棵森林体积 ≈ {_proj_gib:.1f} GiB（护栏 {RF_MEM_GUARD_GIB} GiB）")
del _probe
import gc
gc.collect()
log(f"  探针内存已回收，容器当前占用 {_cgroup_current_bytes()/2**30:.1f} GiB")

assert _proj_gib <= RF_MEM_GUARD_GIB, \
    f"外推森林体积 {_proj_gib:.1f} GiB 超过护栏 {RF_MEM_GUARD_GIB} GiB，先排查再跑"

# ---- 分波构建：每波只并行 RF_NJOBS 棵，把峰值内存钉死在一波的缓冲上，同时获得进度可观测性 ----
# sklearn 的 warm_start 在 BaseForest.fit 里显式执行
#   random_state.randint(MAX_INT, size=len(self.estimators_))
# 把随机流推进到「没用 warm_start 时本该到达的位置」，所以分波长成的 100 棵与一次性
# n_estimators=100, random_state=42 的森林**逐棵同分布且同随机流**，不是近似。
log(f"  分波构建 {RF_N_ESTIMATORS} 棵：每波 {RF_NJOBS} 棵（warm_start，随机流与一次性构建一致）")
_rf = RandomForestClassifier(**{**RF_PARAMS, "n_estimators": min(RF_NJOBS, RF_N_ESTIMATORS)},
                             n_jobs=RF_NJOBS, warm_start=True)
_t = time.time()
_grown = 0
while _grown < RF_N_ESTIMATORS:
    _grown = min(_grown + RF_NJOBS, RF_N_ESTIMATORS)
    _rf.set_params(n_estimators=_grown)
    _rf.fit(X23, y23i)
    log(f"  已长成 {_grown}/{RF_N_ESTIMATORS} 棵，累计 {(time.time()-_t)/60:.2f} 分，"
        f"容器占用 {_cgroup_current_bytes()/2**30:.1f} GiB")
RF_SECONDS = time.time() - _t
_rf_models = [_rf]
RF_TREES = len(_rf.estimators_)
RF_NODES = sum(int(e.tree_.node_count) for e in _rf.estimators_)
RF_DEPTH = max(int(e.tree_.max_depth) for e in _rf.estimators_)
RF_GROUPED = False
RF_GROUPS = 1
assert RF_TREES == RF_N_ESTIMATORS, f"随机森林树数不符：{RF_TREES}"
log(f"随机森林训练完成：{RF_TREES} 棵 / 节点 {RF_NODES:,} / 最大深度 {RF_DEPTH} / "
    f"用时 {RF_SECONDS/60:.2f} 分")
TRAINED["random_forest_dijk2024"] = {
    "display_name": "随机森林（Dijk 2024 装袋树）", "family": "装袋树",
    "train_seconds": RF_SECONDS, "n_trees": RF_TREES, "total_nodes": RF_NODES,
    "max_depth_reached": RF_DEPTH, "grouped_build": RF_GROUPED,
    "n_groups": RF_GROUPS, "params": {k: v for k, v in RF_PARAMS.items()},
    "scale": f"{RF_TREES} 棵树 / {RF_NODES:,} 节点"}

# ------------------------------------------------------------------ XGBoost
log("=" * 112)
log("XGBoost（Dijk 2026 提升树）：逐字沿用 tools/ch3_xgb_entity.py 的冻结 PARAMS")
import xgboost as xgb

XGB_PARAMS = dict(n_estimators=800, learning_rate=0.05, max_depth=8,
                  subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                  tree_method="hist", device="cpu", eval_metric="aucpr",
                  n_jobs=XGB_NJOBS, random_state=SEED)
log(f"  xgboost {xgb.__version__}  {XGB_PARAMS}")
log("  注意：无 scale_pos_weight，与 Dijk 2026 公开配置及 Q0 run-config.json 一致")

# 25 棵树的速度探针，与 ch3_xgb_entity.py 第 132-136 行同一顺序，保证锚点可复现
_t = time.time()
xgb.XGBClassifier(**{**XGB_PARAMS, "n_estimators": 25}).fit(X23, y23, verbose=False)
_per_tree = (time.time() - _t) / 25
log(f"  速度探针：25 棵用时 {time.time()-_t:.0f}s，单棵约 {_per_tree:.1f}s，"
    f"800 棵预计 {_per_tree*800/60:.0f} 分")

_t = time.time()
XGB_MODEL = xgb.XGBClassifier(**XGB_PARAMS)
XGB_MODEL.fit(X23, y23, verbose=False)
XGB_SECONDS = time.time() - _t
log(f"XGBoost 训练完成，用时 {XGB_SECONDS/60:.2f} 分")
TRAINED["xgboost_dijk2026"] = {
    "display_name": "XGBoost（Dijk 2026 提升树）", "family": "提升树",
    "train_seconds": XGB_SECONDS, "n_trees": 800, "params": XGB_PARAMS,
    "xgboost_version": xgb.__version__, "scale": "800 棵树 / 深度 8"}

del X23, y23, y23i

# =====================================================================================
# 阶段闸门：先把训练结果写盘冻结，再允许读入 LSPR24
# =====================================================================================
_frozen = {
    "protocol": "树模型无 epoch 概念与检查点选择，直接按各自论文配置训到底；"
                "LSPR24 只在训练全部结束后评价一次",
    "seed": SEED, "field_budget": D, "n_train_flows": 16_353_511,
    "models": {k: {kk: vv for kk, vv in v.items()} for k, v in TRAINED.items()}}
json.dump(_frozen, open(f"{OUT}/selection_frozen_trees.json", "w"), ensure_ascii=False,
          indent=2, default=str)
SELECTION_FROZEN = True
log("=" * 112)
log(f"训练阶段结束，结果已冻结写盘 {OUT}/selection_frozen_trees.json")

# =====================================================================================
# 阶段二：此刻才第一次读入 LSPR24，每个模型只评价一次
# =====================================================================================


def load24():
    global _N24_LOADS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在训练阶段读入 LSPR24"
    _N24_LOADS += 1
    assert _N24_LOADS == 1, f"LSPR24 只允许从磁盘读入一次，当前第 {_N24_LOADS} 次"
    return (guarded_load("X24"), guarded_load("y24"),
            guarded_load("s24", True), guarded_load("d24", True))


log("=" * 112)
log("阶段二 评价：首次读入 LSPR24（训练已冻结）")
X24, y24, s24, d24 = load24()
assert X24.shape[1] == D
assert X24.shape[0] == 20_227_356, f"LSPR24 全量流数自检失败：{X24.shape[0]}"

# ---- 实体构造：逐字照抄 ch3_full.py 第 130-133 行 ----
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
_flow_pos = float(y24.astype(np.float64).mean())
log(f"LSPR24 流={len(y24):,} 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} "
    f"逐流正例率={_flow_pos:.10f}")
assert N_ENT == 47115, f"LSPR24 实体数自检失败：{N_ENT}"
assert int(ent_lab.sum()) == 752, f"LSPR24 正例实体自检失败：{int(ent_lab.sum())}"
assert abs(_flow_pos - 0.0257073138) < 1e-9, f"LSPR24 逐流正例率自检失败：{_flow_pos:.12f}"
log("LSPR24 自检通过：实体 47,115 / 正例实体 752 / 逐流正例率 0.0257073138")
del key24, s24, d24


# ---- 评价口径：逐字照抄 ch3_full.py 第 213-240 行（含末尾 .astype(np.float32)）----
def ent_ap(sc, seen, p=None):
    m = seen
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[m], sc[m])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[m], np.clip(sc[m], 1e-7, 1.0).astype(np.float64) ** p)
        np.add.at(cnt, ent24[m], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    ok = np.isfinite(es)
    return average_precision_score(ent_lab[ok], es[ok]), int(ok.sum())


def dr_at_fpr(sc, seen, target=TARGET_FPR, p=None):
    m = seen
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[m], sc[m])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[m], np.clip(sc[m], 1e-7, 1.0).astype(np.float64) ** p)
        np.add.at(cnt, ent24[m], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    ok = np.isfinite(es); v = es[ok]; l = ent_lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0:
        return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


def score24(predict_batch, key, display):
    """LSPR24 逐流打分。每调用一次记一次评价；本进程合法总次数 == 2。"""
    global _EVAL24_CALLS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在训练阶段评价 LSPR24"
    _EVAL24_CALLS += 1
    _EVAL24_LEDGER.append({"call": _EVAL24_CALLS, "group": "树模型族", "model": key})
    assert _EVAL24_CALLS <= 2, f"本进程 LSPR24 评价次数超出预算：第 {_EVAL24_CALLS} 次"
    log(f"LSPR24 评价 #{_EVAL24_CALLS}/2 ← {display}")
    sc = np.empty(len(y24), np.float32)
    t1 = time.time()
    for a in range(0, len(y24), PRED_BATCH):
        sc[a:a + PRED_BATCH] = predict_batch(X24[a:a + PRED_BATCH])
        done = min(a + PRED_BATCH, len(y24))
        el = time.time() - t1
        log(f"    推理进度 {done:,}/{len(y24):,}  累计 {el:.0f}s  "
            f"预计剩余 {el/max(done,1)*(len(y24)-done):.0f}s")
    log(f"  推理完成，用时 {time.time()-t1:.0f}s")
    assert np.isfinite(sc).all(), f"{key} 的逐流分数含非有限值"
    return sc


def metrics_of(sc, seen):
    e_max, n_ok = ent_ap(sc, seen)
    e_lp, _ = ent_ap(sc, seen, P_BORROW)
    return {"flow_ap": float(average_precision_score(y24[seen], sc[seen])),
            "flow_auc": float(roc_auc_score(y24[seen], sc[seen])),
            "ent_ap_max": float(e_max), "ent_ap_lp_borrowed": float(e_lp),
            "dr_at_fpr_max": float(dr_at_fpr(sc, seen, TARGET_FPR, None)),
            "dr_at_fpr_lp_borrowed": float(dr_at_fpr(sc, seen, TARGET_FPR, P_BORROW)),
            "n_ent_scored": int(n_ok), "coverage": float(seen.mean())}


SEEN_ALL = np.ones(len(y24), bool)   # 树模型逐流打分，覆盖率恒为 1.0
RES = {}

# ---- XGBoost 先评价：它有锚点，实现有偏差要尽早暴露 ----
sc_xgb = score24(lambda b: XGB_MODEL.predict_proba(b)[:, 1].astype(np.float32),
                 "xgboost_dijk2026", TRAINED["xgboost_dijk2026"]["display_name"])
np.save(f"{OUT}/scores_xgboost_dijk2026.npy", sc_xgb)
RES["xgboost_dijk2026"] = {**TRAINED["xgboost_dijk2026"], **metrics_of(sc_xgb, SEEN_ALL)}
_r = RES["xgboost_dijk2026"]
log("-" * 112)
log("XGBoost 锚点复现核对（对照 runs/diagnostics/ch3-xgb-entity/xgb_entity.json）")
_delta = {}
for _k, _want in [("flow_ap", XGB_ANCHOR["flow_ap"]),
                  ("ent_ap_max", XGB_ANCHOR["ent_ap_max"]),
                  ("dr_at_fpr_max", XGB_ANCHOR["dr_at_fpr_max"]),
                  ("ent_ap_lp_borrowed", XGB_ANCHOR["ent_ap_lp_at_p_borrow"])]:
    _delta[_k] = _r[_k] - _want
    log(f"  {_k:<22} 本次 {_r[_k]:.10f}  锚点 {_want:.10f}  Δ={_delta[_k]:+.10f}")
_bad = [k for k, v in _delta.items() if abs(v) > ANCHOR_TOL]
if _bad:
    log(f"  ★ 锚点不符（容差 {ANCHOR_TOL}）：{_bad}。实现存在偏差，先排查，不继续。")
    json.dump({"anchor_delta": _delta, "xgb": _r}, open(f"{OUT}/anchor_failure.json", "w"),
              ensure_ascii=False, indent=2)
    raise SystemExit(f"XGBoost 锚点复现失败：{_bad}")
log(f"  锚点复现通过（全部 |Δ| ≤ {ANCHOR_TOL}），本文件的训练与评价实现与冻结口径一致")
del sc_xgb, XGB_MODEL

# ---- 随机森林 ----
def _rf_predict(batch):
    acc = None
    for m in _rf_models:
        p = m.predict_proba(batch)[:, 1]
        acc = p if acc is None else acc + p
    return (acc / len(_rf_models)).astype(np.float32)


sc_rf = score24(_rf_predict, "random_forest_dijk2024",
                TRAINED["random_forest_dijk2024"]["display_name"])
np.save(f"{OUT}/scores_random_forest_dijk2024.npy", sc_rf)
RES["random_forest_dijk2024"] = {**TRAINED["random_forest_dijk2024"],
                                 **metrics_of(sc_rf, SEEN_ALL)}
del sc_rf, _rf_models

assert _EVAL24_CALLS == 2, f"本进程 LSPR24 评价次数应为 2，实为 {_EVAL24_CALLS}"
assert _N24_LOADS == 1, f"LSPR24 应只从磁盘读入 1 次，实为 {_N24_LOADS}"
log("=" * 112)
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，评价 {_EVAL24_CALLS} 次，均在训练冻结之后")

W = 116
log("=" * W)
log("树模型族基线在 LSPR24 全量上的结果（主口径 = max 聚合）")
log(f"{'基线':<28}{'架构族':<10}{'逐流AP':>11}{'实体AP(max)':>14}{'DR@4%FPR(max)':>15}"
    f"{'实体AP(Lp借用)':>16}{'训练用时':>11}")
for k in ["random_forest_dijk2024", "xgboost_dijk2026"]:
    r = RES[k]
    log(f"{r['display_name']:<28}{r['family']:<10}{r['flow_ap']:>11.6f}{r['ent_ap_max']:>14.6f}"
        f"{r['dr_at_fpr_max']:>15.6f}{r['ent_ap_lp_borrowed']:>16.6f}"
        f"{r['train_seconds']/60:>10.2f}分")
log("=" * W)

json.dump({"protocol": _frozen["protocol"], "seed": SEED, "field_budget": D,
           "p_borrowed_for_lp_sensitivity": P_BORROW, "target_fpr": TARGET_FPR,
           "n_train_flows": 16_353_511, "n_test_flows": int(len(y24)),
           "lspr24": {"n_entity": int(N_ENT), "n_pos_entity": int(ent_lab.sum()),
                      "flow_pos_rate": _flow_pos},
           "models": RES, "xgb_anchor": XGB_ANCHOR, "xgb_anchor_delta": _delta,
           "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals": _EVAL24_CALLS,
                         "ledger": _EVAL24_LEDGER}},
          open(f"{OUT}/trees_results.json", "w"), ensure_ascii=False, indent=2, default=str)
log(f"树模型族结果已存 {OUT}/trees_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
