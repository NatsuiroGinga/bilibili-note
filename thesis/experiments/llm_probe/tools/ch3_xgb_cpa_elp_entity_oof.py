# -*- coding: utf-8 -*-
"""第三章 XGBoost 适配 CPA 与 ELP：源年实体折外选择和目标年四格评价。

为什么做这一行：第三章的贡献是两个机制而不是某个骨干。核心表是「骨干 × 有无机制」。
已有四个神经骨干的实测（实体平均精确率，主口径）：感知机 33.50→51.84、一维卷积
27.94→43.52、全注意力 9.17→21.68、门控循环 16.48→19.21。XGBoost 的无机制水平是
51.29，是全部骨干里最高的无机制起点，也是最难改进的一行；它同时跨越神经与树两大类，
机制若在其上仍有增益，普适性论断显著变硬。

=====================================================================================
一、两个机制在树模型上的挂载点，以及与神经骨干的**实质差异**
=====================================================================================
机制一「因果前缀跨流聚合」
  神经骨干：作用于**编码器输出的隐藏表示** h=f(x)。见 tools/ch3_2x2_fairsel.py 第
            124-127 行（式 (3-7) 对应代码）：
                h = f(x) * m
                c = cumsum(h, 1) / cumsum(m, 1).clamp(min=1) * m
                out = o(g(cat([h, c])))
            前缀均值在**学到的表示空间**里做，f 与 g 端到端一起训练。
  树骨干  ：树模型没有可学表示，也没有可反向传播的中间层。挂载点改到**输入层**：
                x_ctx[i] = mean_{k<=j, 同序列} x[I[r,k]]        （含本流，掩码累计为分母）
                输入 = concat(x[i], x_ctx[i])                   83 → 166 维
            分母是前缀内的有效流数，与式 (3-7) 的 cumsum(m,1).clamp(min=1) 一致；
            序列切分、时间序、掩码语义全部沿用缓存里的 I/M，未新建口径。
  ★ 必须写明的差异：**一个作用于学到的表示，一个作用于原始特征，不是同一个算子。**
    正文引用时不得表述为「同一算子在两种骨干上的实现」，只能表述为「同一机制思想
    （因果前缀跨流上下文）在两种骨干上的对应挂载」。两者的容量、可学性与信息瓶颈
    都不同：神经侧前缀均值可被 g 非线性重组，树侧前缀均值是固定的输入特征。

机制二「实体级可学幂平均池化」
  神经骨干：p 由梯度学习（Model.p_log，见 ch3_2x2_fairsel.py 第 118-121、108-110 行），
            并有一路序列级辅助损失把梯度送回 p。
  树骨干  ：树模型不能反向传播，p 不可学。改为**在源年 LSPR23 上按实体分组做折外预测，
            再在折外分数上网格搜索 p**：
                s_ent = (mean_{i in ent} clip(s_i, 1e-7, 1)^p)^(1/p)
            选择准则是折外实体平均精确率（pooled OOF）。
  ★ 必须写明的差异：**一个是端到端可学参数，一个是源年选出的固定超参数。**
    正文不得表述为「可学幂平均」，只能表述为「幂平均池化，指数由源年折外选择」。

=====================================================================================
二、四格
=====================================================================================
  C00  原始 83 维输入，实体聚合取最大        ← 同设备科学基线（见第三节裁决）
  C01  原始 83 维输入，实体聚合用源年折外选出的 p
  C10  前缀拼接 166 维输入，实体聚合取最大
  C11  前缀拼接 166 维输入，实体聚合用源年折外选出的 p

  只需两路最终模型：83 维模型服务 C00/C01，166 维模型服务 C10/C11；
  四格的差别只在实体聚合算子。因此 LSPR24 只打两次分，比每格各打一次更强的隔离。

=====================================================================================
三、设备裁决（本轮最容易出错的地方，已在此写死）
=====================================================================================
既有 51.29 是 CPU 上跑的（runs/diagnostics/ch3-baselines-full，device="cpu"，
n_jobs=128）。换到 GPU 会改变直方图分箱草图与归约顺序，subsample/colsample 的随机流
也不同（CPU 用 CPU RNG，GPU 用 grow_gpu_hist 的设备侧采样），因此**不能预期 GPU 复现
CPU 的逐位数字**。若把「C00 必须复现 0.512899」设成失败门，一旦不复现就无法区分差异来自
设备还是来自本脚本的实现，且会重犯 2026-08-18 旧卷积运行的错误（把相对历史运行的绝对
偏差误设为失败门，导致在更高验证 AP 时退出且未读目标年）。

  ★ 裁决：**四格全部在 GPU 重跑，同次运行的 C00 就是本行的科学基线。**
    既有 CPU 的 0.512899 降为**诊断参照**，只报差值、不作失败门。
    该身份写入结果 JSON 的 `c00_baseline_identity` 字段，正文引用本行时必须用同设备
    C00，不得把 CPU 的 51.29 与 GPU 的 C11 并排相减。

=====================================================================================
四、回归比对门禁（**失败门**，与设备无关）
=====================================================================================
既然 C00 的绝对复现被降级为诊断，失败门改为**结构性核验**：本脚本的实体构造、实体聚合、
实体平均精确率与固定告警预算检出率四段代码，必须与既有脚本逐字一致。

判据不是读代码，是**用既有 CPU 运行落盘的逐流分数当输入，跑本脚本自己的评价代码**：
    runs/diagnostics/ch3-baselines-full/scores_xgboost_dijk2026.npy
        → 本脚本的 ent_ap / dr_at_fpr
        → 必须逐位重现 0.2223914545997109 / 0.512898847990404 / 0.6928191489361702
输入分数完全相同，所以任何偏差都只能来自评价实现，与设备无关。不通过即写明差异并退出。
该门禁在真实全量数据上执行、嵌在主流程内，不是人工构造的对照物。

它的位置在阶段二开头（LSPR24 首次载入、自检通过之后，四格打分之前）：既能在任何格的
数字产生之前拦住实现缺陷，又不破坏「选择冻结前不碰目标年」的隔离。

诊断项（**不作失败门**）：C00(GPU) − 0.512899 的差值，按 |Δ| 分级记录。

=====================================================================================
五、预注册判读（跑前写死，不得看结果后改）
=====================================================================================
主量：LSPR24 实体平均精确率，各格用其自身设计的聚合算子（C00/C10 取最大，C01/C11 用
源年折外选出的 p）。单次运行，种子 42。

波动幅度怎么定——**如实处理，不硬套**：
  · 本章既有的 11.59 个百分点取自**感知机骨干的逐流口径三次重复**，骨干不同、评价单元
    不同（逐流 vs 实体）、随机性来源不同，**不搬到这里**。
  · XGBoost 固定种子、固定设备后是确定性训练，重复训练的方差为零，「重复训练波动」在这里
    没有意义，不能拿来当波动幅度。
  · 这里真实存在的不确定性是**评价集的抽样波动**：LSPR24 只有 47,115 个实体、752 个正实体，
    实体平均精确率对哪些实体进入评价很敏感。
  ★ 因此波动幅度用**实体级配对自助法**度量：对 47,115 个实体有放回重采样 B=1000 次
    （RandomState(20260818)，四格共用同一批重采样下标，保证配对），每次重算四格的实体
    平均精确率，取差值分布的 95% 百分位区间。该区间只覆盖评价集抽样波动，**不覆盖**
    p 的选择波动（p 在源年选定后固定），此限制写入结果 JSON。

四种情形的判读（对 Δ = C11 − C00）：
  情形一 增益显著为正：配对自助 95% 区间整体大于 0。
  情形二 落在波动幅度内：区间跨 0。此时不得声称机制在树骨干上有效。
  情形三 增益为负：区间整体小于 0。如实报告为「机制在树骨干上失效」，不得删格、不得换口径。
  情形四 单独效应方向：A = C10 − C00（只加机制一）、B = C01 − C00（只加机制二）、
         交互 = C11 − C10 − C01 + C00，各自给点估计与配对自助 95% 区间与符号。
         另记录四种符号组合（A>0/B>0、A>0/B≤0、A≤0/B>0、A≤0/B≤0）中本次落在哪一种。
点估计另与本章既有四个骨干的增益（+18.34 / +15.58 / +12.51 / +2.73）并列，仅作量级背景，
不作门槛。

另有两条预注册的诚实性条款：
  · 若源年折外选出的 p 落在网格上界（P_GRID 末元），说明幂平均在树骨干上退化为近似取最大，
    此时 C01≈C00、C11≈C10 是**信息**而非失败，必须原样报告并标注 `p_at_grid_edge=true`。
  · 必须报告折外 AP 随 p 的整条曲线与「最优 p 相对 p=1 与相对取最大的增量」，
    曲线平坦意味着 p 的选择不稳，C01/C11 的增益要按此打折解读。

=====================================================================================
六、隔离
=====================================================================================
  · 阶段一只读 LSPR23：宽表、标签、序列索引与掩码、实体键。folds、p 网格搜索、两路最终
    模型全部在此完成，结果写盘冻结。此刻进程内不存在任何 LSPR24 数组。
  · 阶段闸门：SELECTION_FROZEN=True 且 selection_frozen_xgb2x2.json 已落盘。
  · 阶段二才首次读入 LSPR24，磁盘读入恰 1 次，逐流打分恰 2 次（两路最终模型各一次），
    四格由这两个分数向量派生。断言写在代码里。
  · p 的选择只用 LSPR23，绝不碰 LSPR24。

自检必须对上：LSPR24 实体 47,115 / 正例实体 752 / 逐流正例率 0.0257073138。

只保存模型、聚合指标和运行收据，不保存逐流折外分数或目标年分数。
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()
_LAST_BEAT = [T0]


def log(m):
    print(f"[{time.time() - T0:8.1f}s] {m}", flush=True)


def beat(stage, done, total, t_start, every=30.0):
    """限频业务进度心跳：已处理量、总量、吞吐、累计耗时、预计剩余。"""
    now = time.time()
    if now - _LAST_BEAT[0] < every and done < total:
        return
    _LAST_BEAT[0] = now
    el = now - t_start
    rate = done / max(el, 1e-9)
    eta = (total - done) / max(rate, 1e-9)
    log(f"  [{stage}] {done:,}/{total:,} ({done/max(total,1):.1%}) "
        f"吞吐 {rate:,.0f}/s 累计 {el:.0f}s 预计剩余 {eta:.0f}s")


def prefix_mean_kernel(value, mask):
    weighted = value * mask[:, :, None]
    numerator = np.cumsum(weighted, axis=1, dtype=np.float64)
    denominator = np.cumsum(mask, axis=1, dtype=np.float64)
    np.maximum(denominator, 1.0, out=denominator)
    return (numerator / denominator[:, :, None]) * mask[:, :, None]


def assert_prefix_formula_truth():
    value = np.asarray([[[1.0], [2.0], [3.0], [4.0], [99.0]]], np.float64)
    mask = np.asarray([[1.0, 1.0, 1.0, 1.0, 0.0]], np.float64)
    actual = prefix_mean_kernel(value, mask).reshape(-1)
    expected = np.asarray([1.0, 1.5, 2.0, 2.5, 0.0], np.float64)
    assert np.array_equal(actual, expected), f"前缀解析真值不符：{actual.tolist()}"


# =====================================================================================
# 常量与路径
# =====================================================================================
ROOT = str(Path(__file__).resolve().parents[1])
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
BASE_FULL = f"{ROOT}/runs/diagnostics/ch3-baselines-full"
_dijk_module_root = f"{ROOT}/tools/dijk2026_replication"
if _dijk_module_root not in sys.path:
    sys.path.insert(0, _dijk_module_root)

from dijk_fields import DIJK_FEATURES  # noqa: E402

CATEGORICAL_NAMES = (
    "SrcPort",
    "DstPort",
    "Protocol",
    "L3/L4 Protocol",
    "Int/Ext Dst IP",
)
BOOLEAN_NAMES = ("External_src", "External_dst")
CATEGORICAL_IDX = tuple(DIJK_FEATURES.index(name) for name in CATEGORICAL_NAMES)
BOOLEAN_IDX = tuple(DIJK_FEATURES.index(name) for name in BOOLEAN_NAMES)
NUMERIC_IDX = tuple(
    idx
    for idx in range(len(DIJK_FEATURES))
    if idx not in CATEGORICAL_IDX and idx not in BOOLEAN_IDX
)
assert len(DIJK_FEATURES) == 83
assert len(NUMERIC_IDX) == 76

_parser = argparse.ArgumentParser(description="XGBoost 适配 CPA 与 ELP 的源年折外选择和目标年四格实验")
_parser.add_argument(
    "--config",
    default=f"{ROOT}/configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json",
)
_parser.add_argument("--validate-config", action="store_true")
_args = _parser.parse_args()
with open(_args.config, encoding="utf-8") as _fh:
    CONFIG = json.load(_fh)

_required = {
    "run_id",
    "seed",
    "n_fold",
    "p_grid",
    "num_boost_round",
    "xgb_params",
    "effective_config_float_compare",
    "tracking",
}
_missing = sorted(_required - set(CONFIG))
if _missing:
    raise SystemExit(f"配置缺少字段：{_missing}")
EXPECTED_RUN_ID = "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
if CONFIG["run_id"] != EXPECTED_RUN_ID:
    raise SystemExit(f"运行身份与本轮重跑协议不符：{CONFIG['run_id']}")
if int(CONFIG["n_fold"]) != 3:
    raise SystemExit("冻结协议要求三折实体折外选择")
if list(CONFIG["p_grid"]) != [0.5, 1.0, 2.0, 4.0, 8.0]:
    raise SystemExit("p 网格与冻结协议不符")
if int(CONFIG["seed"]) != 42 or int(CONFIG["num_boost_round"]) != 800:
    raise SystemExit("种子或提升轮数与冻结协议不符")
_expected_xgb_params = {
    "tree_method": "hist",
    "device": "cuda",
    "max_depth": 8,
    "eta": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "lambda": 1.0,
    "max_bin": 256,
    "objective": "binary:logistic",
    "eval_metric": "aucpr",
    "seed": 42,
    "nthread": 32,
}
if CONFIG["xgb_params"] != _expected_xgb_params:
    raise SystemExit("XGBoost 超参与冻结协议不符")
if CONFIG["effective_config_float_compare"] != {
    "rel_tol": 1e-7,
    "abs_tol": 1e-12,
}:
    raise SystemExit("XGBoost 有效配置浮点比较容差与冻结协议不符")
if CONFIG.get("adapters") != ["mean166", "semantic168"]:
    raise SystemExit("CPA 适配器集合与冻结协议不符")
if CONFIG.get("artifact_policy") != {
    "persist_fold_models": True,
    "persist_final_models": True,
    "persist_oof_scores": False,
    "persist_target_scores": False,
}:
    raise SystemExit("制品策略与冻结协议不符")
AUTHORIZED_SWANLAB_WORKSPACE = "mortiswang"
AUTHORIZED_SWANLAB_PROJECT = "ns3-rwkv-lspr24"
if CONFIG["tracking"].get("workspace") != AUTHORIZED_SWANLAB_WORKSPACE:
    raise SystemExit("SwanLab 工作空间与本轮授权目的地不符")
if CONFIG["tracking"].get("project") != AUTHORIZED_SWANLAB_PROJECT:
    raise SystemExit("SwanLab 项目与本轮授权目的地不符")
if _args.validate_config:
    print("CONFIG_VALID", flush=True)
    raise SystemExit(0)

OUT = os.environ.get("XGB2X2_OUT", f"{ROOT}/runs/diagnostics/{CONFIG['run_id']}")
os.makedirs(OUT, exist_ok=True)

RUN_NAME = str(CONFIG["run_id"])
SEED = int(CONFIG["seed"])
TARGET_FPR = 0.04
L = 128                       # 序列长度，与缓存 I/M 的第二维一致
D_RAW = 83                    # Dijk 2026 附录 A 字段预算
N_FLOW_23 = 16_353_511
N_FLOW_24 = 20_227_356
N_ENT_24_EXPECT = 47_115
N_POS_ENT_24_EXPECT = 752
FLOW_PI_24_EXPECT = 0.0257073138
N_ENT_23_EXPECT = 150_680

# ---- 折外选择 ----
N_FOLD = int(CONFIG["n_fold"])
# p 网格：写死，跑前冻结。
#   下界 0.25：p→0 是几何平均，0.25 已明显偏向「要求整条边普遍可疑」的一端；
#   1.0 是算术平均；神经骨干学到的 p 落在 0.61~1.22（ch3_full C01=0.6069、C11=1.2236，
#   ch3_2x2_fairsel C11=1.0562），故 [0.25, 1.5] 区间用 0.25 步长密集覆盖；
#   1.5 以上转几何式加密到 32，用来探「近似取最大」的一端，使「无增益」这一结论不会
#   是网格太窄造成的假象。
#   上界 32：冻结聚合式在 float64 下直接算 s^p，分数下限被 clip 到 1e-7；
#   1e-7^32 = 1e-224 仍是正规数，而 p≈44 起会下溢成 0 并制造并列，故截到 32。
P_GRID = tuple(float(v) for v in CONFIG["p_grid"])
# 并列裁决规则（跑前写死）：折外实体 AP 最大者胜；完全并列时取 |p−1| 最小者；再并列取较小的 p。

# ---- 自助法 ----
BOOT_B = int(os.environ.get("XGB2X2_BOOT", "1000"))
BOOT_SEED = 20260818
TARGET_FPR_GRID = tuple(float(v) for v in CONFIG["target_fpr_grid"])

# ---- XGBoost 超参：与 ch3_baselines_full_trees.py 第 220-223 行的冻结 XGB_PARAMS 一一对应 ----
#   n_estimators=800   → num_boost_round=800
#   learning_rate=0.05 → eta
#   max_depth=8        → max_depth
#   subsample=0.8      → subsample
#   colsample_bytree   → colsample_bytree
#   reg_lambda=1.0     → lambda
#   tree_method=hist   → tree_method
#   eval_metric=aucpr  → eval_metric
#   random_state=42    → seed
#   n_jobs             → nthread
#   device="cpu"       → device="cuda"   ★ 唯一有意的改动，理由见第三节
#   无 scale_pos_weight（Dijk 2026 公开配置与 Q0 run-config.json 均无此项）
N_ROUND = int(CONFIG["num_boost_round"])
NTHREAD = int(os.environ.get("XGB2X2_NTHREAD", "32"))   # 208 核里只取 32，给并发作业留 CPU
XGB_PARAMS = {
    "tree_method": "hist",
    "device": "cuda",
    "max_depth": 8,
    "eta": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "lambda": 1.0,
    "max_bin": 256,
    "objective": "binary:logistic",
    "eval_metric": "aucpr",
    "seed": SEED,
    "nthread": NTHREAD,
}
XGB_PARAMS.update(CONFIG["xgb_params"])
# 训练后从 booster.save_config() 机械核对的有效值（防止参数名拼错被静默忽略）。
# 整数、字符串与布尔等离散值按 XGBoost 序列化值精确比较；只有浮点超参使用
# math.isclose。rel_tol=1e-7 仅覆盖 XGBoost 3.2.0 的 float32 回读误差，远小于可影响实验的超参改动。
EFFECTIVE_EXACT_EXPECT = {
    ("learner", "generic_param", "device"): "cuda:0",
    ("learner", "gradient_booster", "gbtree_train_param", "updater"): "grow_gpu_hist",
    ("learner", "learner_train_param", "objective"): "binary:logistic",
    ("learner", "gradient_booster", "tree_train_param", "max_depth"): "8",
    ("learner", "gradient_booster", "tree_train_param", "max_bin"): "256",
}
EFFECTIVE_FLOAT_EXPECT = {
    ("learner", "gradient_booster", "tree_train_param", "eta"): 0.05,
    ("learner", "gradient_booster", "tree_train_param", "subsample"): 0.8,
    ("learner", "gradient_booster", "tree_train_param", "colsample_bytree"): 0.8,
    ("learner", "gradient_booster", "tree_train_param", "lambda"): 1.0,
}
EFFECTIVE_FLOAT_REL_TOL = float(CONFIG["effective_config_float_compare"]["rel_tol"])
EFFECTIVE_FLOAT_ABS_TOL = float(CONFIG["effective_config_float_compare"]["abs_tol"])
EFFECTIVE_CONFIG_COMPARISON_POLICY = {
    "exact_fields": "XGBoost 序列化值精确相等",
    "float_fields": "math.isclose",
    "rel_tol": EFFECTIVE_FLOAT_REL_TOL,
    "abs_tol": EFFECTIVE_FLOAT_ABS_TOL,
}
EFFECTIVE_CONFIG_RECEIPT_PATH = f"{OUT}/effective_config_receipts.json"
EFFECTIVE_CONFIG_RECEIPTS = []

# ---- 批大小：训练矩阵按批送入 QuantileDMatrix，推理按批调用，二者共同钉住显存 ----
DM_BATCH = int(os.environ.get("XGB2X2_DM_BATCH", "1000000"))
PRED_BATCH = int(os.environ.get("XGB2X2_PRED_BATCH", "2000000"))
SEQ_BATCH = 2048                       # 前缀构造每批序列数

# ---- 显存护栏：本进程保守峰值与硬性下限，低于下限即退出，绝不挤已在跑的作业 ----
GPU_NEED_GIB = float(os.environ.get("XGB2X2_GPU_NEED_GIB", "11"))
GPU_FLOOR_GIB = float(os.environ.get("XGB2X2_GPU_FLOOR_GIB", "8"))

# ---- 回归比对门禁的锚点：既有 CPU 运行的全精度值 ----
CPU_ANCHOR = {
    "flow_ap": 0.2223914545997109,
    "ent_ap_max": 0.512898847990404,
    "dr_at_fpr_max": 0.6928191489361702,
}
CPU_SCORES_NPY = f"{BASE_FULL}/scores_xgboost_dijk2026.npy"
GATE_TOL = 1e-10                       # 同一份分数走同一段代码，允许的只有浮点噪声

# ---- 本章既有骨干的增益（点估计背景，不作门槛）----
BACKBONE_CONTEXT = {
    "感知机": {"no_mech": 0.3350, "with_mech": 0.5184, "gain_points": 18.34},
    "一维卷积": {"no_mech": 0.2794, "with_mech": 0.4352, "gain_points": 15.58},
    "全注意力": {"no_mech": 0.0917, "with_mech": 0.2168, "gain_points": 12.51},
    "门控循环": {"no_mech": 0.1648, "with_mech": 0.1921, "gain_points": 2.73},
}

# =====================================================================================
# 阶段闸门与计数器
# =====================================================================================
SELECTION_FROZEN = False
_N24_LOADS = 0
_SCORE24_CALLS = 0
_SCORE24_LEDGER = []


def guarded_load(name, allow_pickle=False, path=None):
    """所有 np.load 的唯一入口。选择阶段禁止读入任何名字含 '24' 的数组。"""
    assert SELECTION_FROZEN or "24" not in name, \
        f"阶段闸门未开：选择阶段禁止读入 {name}"
    return np.load(path or f"{CACHE}/{name}.npy", allow_pickle=allow_pickle)


def assert_sequence_time_monotonic(t_flow, I, M, tag):
    """全量核验每个有效序列位置的起始时间非降，防止前缀包含未来流。"""
    assert len(t_flow) in (N_FLOW_23, N_FLOW_24)
    assert np.isfinite(t_flow).all(), f"{tag} 时间戳含非有限值"
    reversed_pairs = 0
    checked_pairs = 0
    for a in range(0, len(I), 20000):
        idx = I[a : a + 20000]
        valid = M[a : a + 20000] > 0
        timestamp = t_flow[idx]
        adjacent = valid[:, 1:] & valid[:, :-1]
        checked_pairs += int(adjacent.sum())
        reversed_pairs += int(((timestamp[:, 1:] < timestamp[:, :-1]) & adjacent).sum())
    assert reversed_pairs == 0, f"{tag} 序列存在 {reversed_pairs} 个时间逆序相邻对"
    log(f"{tag} 时间非降核验通过：检查 {checked_pairs:,} 个有效相邻对")


# =====================================================================================
# 阶段零：环境与设备核验（先查文档再落笔，此处只做运行时机械核验）
# =====================================================================================
log("=" * 116)
log(f"运行名 {RUN_NAME}  输出目录 {OUT}")
log("阶段零 环境核验")
assert_prefix_formula_truth()
log("  前缀解析真值通过：[1,2,3,4] → [1,1.5,2,2.5]")

import xgboost as xgb  # noqa: E402
import torch  # noqa: E402
import swanlab  # noqa: E402

_bi = xgb.build_info()
log(f"  xgboost {xgb.__version__}  USE_CUDA={_bi.get('USE_CUDA')}  torch {torch.__version__}")
assert xgb.__version__ == "3.2.0", f"XGBoost 版本应为 3.2.0，实为 {xgb.__version__}"
assert _bi.get("USE_CUDA") is True, "本轮要求 GPU 训练，但 xgboost 未编译 CUDA 支持"
assert torch.cuda.is_available(), "CUDA 不可用，拒绝以 CPU 冒充 GPU 运行"

_free0, _tot = torch.cuda.mem_get_info()
log(f"  GPU 总显存 {_tot/2**30:.2f} GiB，当前可用 {_free0/2**30:.2f} GiB，"
    f"本进程保守峰值 {GPU_NEED_GIB:.1f} GiB，硬性下限 {GPU_FLOOR_GIB:.1f} GiB")
try:
    _smi = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory",
                           "--format=csv,noheader"], capture_output=True, text=True)
    for _ln in _smi.stdout.strip().splitlines():
        log(f"  同卡在跑：{_ln}")
except OSError as _e:
    log(f"  nvidia-smi 不可用（{type(_e).__name__}），跳过同卡进程枚举")
if _free0 / 2**30 < GPU_NEED_GIB:
    log(f"  ★ 可用显存 {_free0/2**30:.2f} GiB < 需要 {GPU_NEED_GIB:.1f} GiB，拒绝启动，不挤占同卡作业")
    sys.exit(21)


def gpu_guard(where):
    """每次建矩阵/训练前复查显存，低于下限就干净退出，绝不把同卡作业挤爆。"""
    free = torch.cuda.mem_get_info()[0] / 2 ** 30
    if free < GPU_FLOOR_GIB:
        log(f"  ★ {where}：可用显存 {free:.2f} GiB < 下限 {GPU_FLOOR_GIB:.1f} GiB，主动退出")
        json.dump({"aborted_at": where, "gpu_free_gib": free},
                  open(f"{OUT}/abort_gpu_floor.json", "w"), ensure_ascii=False, indent=2)
        sys.exit(22)
    return free


_self_sha = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
log(f"  本脚本 SHA-256={_self_sha}")
_feature_schema = {
    "raw83": list(DIJK_FEATURES),
    "mean166": list(DIJK_FEATURES) + [f"prefix_mean::{name}" for name in DIJK_FEATURES],
    "semantic168": (
        list(DIJK_FEATURES)
        + [f"numeric_residual::{DIJK_FEATURES[idx]}" for idx in NUMERIC_IDX]
        + [f"prefix_same_value_frequency::{DIJK_FEATURES[idx]}" for idx in CATEGORICAL_IDX]
        + [f"prefix_truth_rate::{DIJK_FEATURES[idx]}" for idx in BOOLEAN_IDX]
        + ["log1p_prefix_count", "is_segment_start"]
    ),
}
_feature_schema_bytes = json.dumps(
    _feature_schema, ensure_ascii=False, separators=(",", ":")
).encode("utf-8")
_feature_schema_sha = hashlib.sha256(_feature_schema_bytes).hexdigest()
json.dump(
    {"schema": _feature_schema, "sha256": _feature_schema_sha},
    open(f"{OUT}/feature_schema.json", "w"),
    ensure_ascii=False,
    indent=2,
)

_tracking = CONFIG["tracking"]
swanlab.init(
    workspace=_tracking["workspace"],
    project=_tracking["project"],
    name=RUN_NAME,
    config={
        "seed": SEED,
        "n_fold": N_FOLD,
        "p_grid": list(P_GRID),
        "xgboost_version": xgb.__version__,
        "script_sha256": _self_sha,
    },
    mode=_tracking["mode"],
    logdir=f"{OUT}/swanlog",
)


# =====================================================================================
# 训练与推理的统一入口
# =====================================================================================
class RowBatchIter(xgb.DataIter):
    """按行下标分批喂给 QuantileDMatrix。

    为什么必须走迭代器而不是直接把整块矩阵交给 xgboost：
      · 主机侧：折内训练用的是 80% 的行，直接 X[rows] 会额外复制约 8 GiB；
        迭代器每批只复制 DM_BATCH 行。
      · 设备侧：单块 16,353,511×166 float32 送上卡是 10.11 GiB，加上量化后的
        ellpack 会把峰值推到 15 GiB 以上，同卡还有别的作业，不能这么用。
    2026-08-18 实测（xgboost 3.2.0）：torch CUDA 张量走不通，xgboost 的
    `__cuda_array_interface__` 分支会 `import cupy`，本环境无 cupy，直接 ModuleNotFoundError；
    主机 numpy 批 + `device="cuda"` 可用，实测 updater=grow_gpu_hist、device=cuda:0。
    """

    def __init__(self, X, y, rows, batch):
        self._X, self._y, self._rows, self._b = X, y, rows, batch
        self._i = 0
        self._t0 = time.time()
        super().__init__()

    def reset(self):
        self._i = 0
        self._t0 = time.time()

    def next(self, input_data):
        a = self._i * self._b
        if a >= len(self._rows):
            return False
        sel = self._rows[a:a + self._b]
        input_data(data=self._X[sel], label=self._y[sel])
        self._i += 1
        beat("建量化矩阵", min(a + self._b, len(self._rows)), len(self._rows), self._t0)
        return True


def _dig(cfg, path):
    cur = cfg
    for k in path:
        cur = cur[k]
    return cur


def assert_effective_config(bst, tag):
    """从 booster 的实际配置回读有效超参，拦住「参数名写错被静默忽略」。"""
    cfg = json.loads(bst.save_config())
    bad = []
    checks = []
    for path, want in EFFECTIVE_EXACT_EXPECT.items():
        got = _dig(cfg, path)
        passed = got == want
        checks.append(
            {
                "path": ".".join(path),
                "comparison": "exact",
                "actual": got,
                "expected": want,
                "passed": passed,
            }
        )
        if not passed:
            bad.append(f"{'.'.join(path)}: 实际 {got} != 期望 {want}")
    for path, want in EFFECTIVE_FLOAT_EXPECT.items():
        got_serialized = _dig(cfg, path)
        got = float(got_serialized)
        passed = math.isclose(
            got,
            want,
            rel_tol=EFFECTIVE_FLOAT_REL_TOL,
            abs_tol=EFFECTIVE_FLOAT_ABS_TOL,
        )
        checks.append(
            {
                "path": ".".join(path),
                "comparison": "math.isclose",
                "actual_serialized": got_serialized,
                "actual": got,
                "expected": want,
                "absolute_delta": abs(got - want),
                "rel_tol": EFFECTIVE_FLOAT_REL_TOL,
                "abs_tol": EFFECTIVE_FLOAT_ABS_TOL,
                "passed": passed,
            }
        )
        if not passed:
            bad.append(
                f"{'.'.join(path)}: 实际 {got} 与期望 {want} 超出 "
                f"math.isclose(rel_tol={EFFECTIVE_FLOAT_REL_TOL:g}, "
                f"abs_tol={EFFECTIVE_FLOAT_ABS_TOL:g})"
            )
    EFFECTIVE_CONFIG_RECEIPTS.append(
        {
            "tag": tag,
            "passed": not bad,
            "comparison_policy": EFFECTIVE_CONFIG_COMPARISON_POLICY,
            "checks": checks,
        }
    )
    receipt_partial = f"{EFFECTIVE_CONFIG_RECEIPT_PATH}.partial"
    with open(receipt_partial, "w", encoding="utf-8") as fh:
        json.dump(EFFECTIVE_CONFIG_RECEIPTS, fh, ensure_ascii=False, indent=2)
    os.replace(receipt_partial, EFFECTIVE_CONFIG_RECEIPT_PATH)
    if bad:
        for b in bad:
            log(f"  ★ 有效超参核对失败 [{tag}] {b}")
        raise SystemExit(f"有效超参与冻结配置不符：{tag}")
    log(f"  有效超参核对通过 [{tag}]：device={_dig(cfg, ('learner','generic_param','device'))} "
        f"updater={_dig(cfg, ('learner','gradient_booster','gbtree_train_param','updater'))} "
        f"浮点容差=math.isclose(rel_tol={EFFECTIVE_FLOAT_REL_TOL:g}, "
        f"abs_tol={EFFECTIVE_FLOAT_ABS_TOL:g})")
    return cfg


def train_booster(X, y, rows, tag):
    """在给定行子集上训练一棵提升树集成。返回 booster 与耗时。"""
    gpu_guard(f"{tag}/建矩阵前")
    t0 = time.time()
    dm = xgb.QuantileDMatrix(RowBatchIter(X, y, rows, DM_BATCH), max_bin=XGB_PARAMS["max_bin"])
    t_dm = time.time() - t0
    free = gpu_guard(f"{tag}/训练前")
    log(f"  [{tag}] 量化矩阵完成 {dm.num_row():,}×{dm.num_col()} 用时 {t_dm:.0f}s，"
        f"训练前可用显存 {free:.2f} GiB")
    assert dm.num_row() == len(rows), f"{tag} 量化矩阵行数 {dm.num_row()} 与请求 {len(rows)} 不符"
    t0 = time.time()
    bst = xgb.train(XGB_PARAMS, dm, num_boost_round=N_ROUND)
    t_tr = time.time() - t0
    log(f"  [{tag}] 训练完成 {N_ROUND} 轮，用时 {t_tr/60:.2f} 分，"
        f"训练后可用显存 {torch.cuda.mem_get_info()[0]/2**30:.2f} GiB")
    assert_effective_config(bst, tag)
    del dm
    return bst, t_dm, t_tr


def predict_rows(bst, X, rows, tag):
    """按批推理，返回与 rows 等长的 float32 分数。"""
    out = np.empty(len(rows), np.float32)
    t0 = time.time()
    for a in range(0, len(rows), PRED_BATCH):
        sel = rows[a:a + PRED_BATCH]
        out[a:a + PRED_BATCH] = np.asarray(bst.inplace_predict(X[sel]), np.float32)
        beat(f"推理/{tag}", min(a + PRED_BATCH, len(rows)), len(rows), t0)
    log(f"  [{tag}] 推理完成 {len(rows):,} 行，用时 {time.time()-t0:.0f}s")
    assert np.isfinite(out).all(), f"{tag} 的逐流分数含非有限值"
    return out


# =====================================================================================
# 实体聚合与评价：逐字照抄 ch3_full.py 第 213-240 行（含末尾 .astype(np.float32)）
# 回归比对门禁核验的就是下面这三个函数
# =====================================================================================
def ent_scores(sc, ent, n_ent, p=None):
    if p is None:
        es = np.full(n_ent, -np.inf, np.float32)
        np.maximum.at(es, ent, sc)
        return es
    num = np.zeros(n_ent, np.float64)
    cnt = np.zeros(n_ent, np.float64)
    np.add.at(num, ent, np.clip(sc, 1e-7, 1.0).astype(np.float64) ** p)
    np.add.at(cnt, ent, 1.0)
    return np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)


def ent_ap_from(es, lab):
    ok = np.isfinite(es)
    return float(average_precision_score(lab[ok], es[ok])), int(ok.sum())


def dr_at_fpr_from(es, lab, target=TARGET_FPR):
    ok = np.isfinite(es)
    v = es[ok]
    l = lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0:
        return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


# =====================================================================================
# 前缀拼接：机制一在树骨干上的输入层实现
# =====================================================================================
def build_prefix_matrix(x_path, n_flow, I, M, tag):
    """返回 (n_flow, 166) float32：左 83 列是原始特征，右 83 列是因果前缀均值。

    前缀均值定义与式 (3-7) 的掩码累计一致：
        pre[r, j] = sum_{k<=j} x[I[r,k]] * M[r,k] / max(sum_{k<=j} M[r,k], 1)
    并逐行核验覆盖：每条流必须恰好被一个序列位置写到一次。
    """
    assert I.shape[1] == L and M.shape == I.shape, f"{tag} 序列形状异常 I={I.shape} M={M.shape}"
    # 用整型计数，不能用 M.sum()：M 是 float32，2^24 以上的整数无法精确表示，
    # LSPR24 的 20,227,356 会被 float32 求和算错。
    n_valid = int((M > 0).sum())
    assert n_valid == n_flow, f"{tag} 掩码有效位 {n_valid:,} 与流数 {n_flow:,} 不符，序列未覆盖全部流"
    log(f"  [{tag}] 序列 {len(I):,} 条，有效位 {n_valid:,}，与流数一致")

    XC = np.empty((n_flow, 2 * D_RAW), np.float32)
    src = np.load(x_path, mmap_mode="r")
    assert src.shape == (n_flow, D_RAW), f"{tag} 原始宽表形状 {src.shape} 不符"
    t0 = time.time()
    for a in range(0, n_flow, PRED_BATCH):
        b = min(a + PRED_BATCH, n_flow)
        XC[a:b, :D_RAW] = src[a:b]
        beat(f"{tag}/读入原始特征", b, n_flow, t0)
    del src
    log(f"  [{tag}] 原始 {D_RAW} 维已就位，用时 {time.time()-t0:.0f}s")

    # 覆盖核验用布尔标记而非计数：上面已断言「有效位数 == 流数」，
    # 若再证明「每条流至少被写到一次」，由鸽笼原理即得「恰好一次」。
    cover = np.zeros(n_flow, bool)
    t0 = time.time()
    for a in range(0, len(I), SEQ_BATCH):
        idx = I[a:a + SEQ_BATCH]
        msk = M[a:a + SEQ_BATCH]
        b, ln = idx.shape
        flat = idx.reshape(-1)
        g = XC[flat, :D_RAW].reshape(b, ln, D_RAW)
        cs = prefix_mean_kernel(g, msk)
        fm = msk.reshape(-1) > 0
        tgt = flat[fm]
        XC[tgt, D_RAW:] = cs.reshape(-1, D_RAW)[fm]
        cover[tgt] = True
        beat(f"{tag}/前缀均值", min(a + SEQ_BATCH, len(I)), len(I), t0)
        del g, cs
    log(f"  [{tag}] 前缀均值完成，用时 {time.time()-t0:.0f}s")
    bad = int((~cover).sum())
    assert bad == 0, f"{tag} 覆盖核验失败：{bad:,} 条流未被任何序列位置写到"
    log(f"  [{tag}] 覆盖核验通过：{n_flow:,} 条流各被恰好一个序列位置写入一次")
    return XC


def build_semantic_matrix(x_path, n_flow, I, M, tag):
    """构造语义感知的 168 维 CPA 输入，并保持逐流覆盖与因果边界。"""
    assert I.shape[1] == L and M.shape == I.shape
    n_valid = int((M > 0).sum())
    assert n_valid == n_flow
    dim = D_RAW + len(NUMERIC_IDX) + len(CATEGORICAL_IDX) + len(BOOLEAN_IDX) + 2
    assert dim == 168
    out = np.empty((n_flow, dim), np.float32)
    src = np.load(x_path, mmap_mode="r")
    for a in range(0, n_flow, PRED_BATCH):
        b = min(a + PRED_BATCH, n_flow)
        out[a:b, :D_RAW] = src[a:b]
    del src

    cover = np.zeros(n_flow, bool)
    lower = np.tri(L, L, dtype=bool)
    t0 = time.time()
    for a in range(0, len(I), SEQ_BATCH):
        idx = I[a : a + SEQ_BATCH]
        mask = M[a : a + SEQ_BATCH] > 0
        batch, width = idx.shape
        flat = idx.reshape(-1)
        current = out[flat, :D_RAW].reshape(batch, width, D_RAW)
        count = np.cumsum(mask, axis=1, dtype=np.int32)
        denom = np.maximum(count, 1).astype(np.float32)
        target = flat[mask.reshape(-1)]

        numeric = current[:, :, NUMERIC_IDX]
        numeric_sum = np.cumsum(numeric * mask[:, :, None], axis=1, dtype=np.float64)
        residual = numeric - numeric_sum / denom[:, :, None]
        cursor = D_RAW
        out[target, cursor : cursor + len(NUMERIC_IDX)] = residual.reshape(
            -1, len(NUMERIC_IDX)
        )[mask.reshape(-1)]
        cursor += len(NUMERIC_IDX)

        prefix_mask = lower[None, :, :] & mask[:, None, :]
        for feature_idx in CATEGORICAL_IDX:
            value = current[:, :, feature_idx]
            equal = value[:, :, None] == value[:, None, :]
            frequency = (equal & prefix_mask).sum(axis=2) / denom
            out[target, cursor] = frequency.reshape(-1)[mask.reshape(-1)]
            cursor += 1

        for feature_idx in BOOLEAN_IDX:
            truth = (current[:, :, feature_idx] > 0) & mask
            truth_rate = np.cumsum(truth, axis=1) / denom
            out[target, cursor] = truth_rate.reshape(-1)[mask.reshape(-1)]
            cursor += 1

        out[target, cursor] = np.log1p(count).reshape(-1)[mask.reshape(-1)]
        cursor += 1
        out[target, cursor] = (count == 1).reshape(-1)[mask.reshape(-1)]
        cursor += 1
        assert cursor == dim
        cover[target] = True
        beat(f"{tag}/语义前缀", min(a + SEQ_BATCH, len(I)), len(I), t0)
        del current, numeric, numeric_sum, residual, prefix_mask
    assert bool(cover.all()), f"{tag} 语义前缀覆盖不完整"
    assert np.isfinite(out).all(), f"{tag} 语义前缀含非有限值"
    log(f"  [{tag}] semantic168 完成，用时 {time.time()-t0:.0f}s")
    return out


# =====================================================================================
# 阶段一：只读入 LSPR23，完成 fold 训练、p 选择与两路最终模型
# =====================================================================================
log("=" * 116)
log("阶段一 选择：只读入 LSPR23，LSPR24 不进入本进程")

y23 = guarded_load("y23")
I23 = guarded_load("I23")
M23 = guarded_load("M23")
E23 = guarded_load("E23")
ent23 = guarded_load("ent23")
t23_flow = guarded_load("t23_flow")
assert len(y23) == N_FLOW_23, f"LSPR23 流数自检失败：{len(y23):,}"
assert len(ent23) == N_FLOW_23, f"LSPR23 实体键长度自检失败：{len(ent23):,}"
N_ENT_23 = int(ent23.max()) + 1
assert N_ENT_23 == N_ENT_23_EXPECT, f"LSPR23 实体数自检失败：{N_ENT_23:,}"
lab23 = np.zeros(N_ENT_23, np.float32)
np.maximum.at(lab23, ent23, y23)
N_POS_ENT_23 = int(lab23.sum())
log(f"LSPR23 流={len(y23):,} 序列={len(I23):,} 实体={N_ENT_23:,} 正例实体={N_POS_ENT_23:,} "
    f"逐流正例率={float(y23.mean()):.10f}")
assert N_POS_ENT_23 >= 100, f"LSPR23 正例实体仅 {N_POS_ENT_23}，折外选择无分辨力，停止"

# 序列级实体键与逐流实体键必须一致，否则前缀均值跨了实体
_t0 = time.time()
for _a in range(0, len(I23), 20000):
    _idx = I23[_a:_a + 20000]
    _msk = M23[_a:_a + 20000] > 0
    _e = np.where(_msk, ent23[_idx], E23[_a:_a + 20000, None])
    assert (_e == E23[_a:_a + 20000, None]).all(), f"序列 {_a} 起的实体键与逐流实体键不一致"
log(f"序列-逐流实体键一致性核验通过，用时 {time.time()-_t0:.0f}s")
assert_sequence_time_monotonic(t23_flow, I23, M23, "LSPR23")
del t23_flow
del E23

# ---- 实体分组分层折：同一实体只出现在一折，正例实体在各折间轮转均分 ----
_rs = np.random.RandomState(SEED)
fold_of_ent = np.empty(N_ENT_23, np.int64)
for _grp in (0.0, 1.0):
    _ids = np.flatnonzero(lab23 == _grp)
    _ids = _ids[_rs.permutation(len(_ids))]
    fold_of_ent[_ids] = np.arange(len(_ids)) % N_FOLD
fold_of_flow = fold_of_ent[ent23]
FOLD_STAT = []
for _k in range(N_FOLD):
    _em = fold_of_ent == _k
    _fm = fold_of_flow == _k
    FOLD_STAT.append({"fold": _k, "n_entity": int(_em.sum()),
                      "n_pos_entity": int(lab23[_em].sum()),
                      "n_flow": int(_fm.sum()), "n_pos_flow": int(y23[_fm].sum())})
    log(f"  折 {_k}: 实体 {_em.sum():,}（正例 {int(lab23[_em].sum())}） 流 {_fm.sum():,}"
        f"（正例 {int(y23[_fm].sum()):,}）")
log(f"实体分组 {N_FOLD} 折已建：同一实体只在一折，正例实体逐折轮转均分")

# ---- 三路源年候选输入 ----
log("-" * 116)
log("构造 raw83、mean166 与 semantic168；上下文适配器只在源年折外结果上选择")
XM23 = build_prefix_matrix(f"{CACHE}/X23.npy", N_FLOW_23, I23, M23, "LSPR23/mean166")
XS23 = build_semantic_matrix(f"{CACHE}/X23.npy", N_FLOW_23, I23, M23, "LSPR23/semantic168")
del I23, M23
MATRICES = {
    "raw83": XM23[:, :D_RAW],
    "mean166": XM23,
    "semantic168": XS23,
}
INPUT_DIMS = {name: int(matrix.shape[1]) for name, matrix in MATRICES.items()}
log(
    "LSPR23 三路输入就位："
    + "，".join(f"{name}={matrix.shape}" for name, matrix in MATRICES.items())
)


def view_of(name):
    return MATRICES[name]


# ---- 折外预测 ----
log("=" * 116)
log(f"折外预测：{len(MATRICES)} 路输入 × {N_FOLD} 折 = {len(MATRICES)*N_FOLD} 次训练，只用 LSPR23")
OOF = {}
FOLD_TIME = {}
for vname in MATRICES:
    Xv = view_of(vname)
    oof = np.full(N_FLOW_23, np.nan, np.float32)
    tsum = 0.0
    for k in range(N_FOLD):
        tr_rows = np.flatnonzero(fold_of_flow != k)
        ho_rows = np.flatnonzero(fold_of_flow == k)
        tag = f"{vname}/fold{k}"
        log(f"--- {tag}: 训练 {len(tr_rows):,} 行，留出 {len(ho_rows):,} 行 ---")
        bst, t_dm, t_tr = train_booster(Xv, y23, tr_rows, tag)
        bst.save_model(f"{OUT}/model_oof_{vname}_fold{k}.json")
        oof[ho_rows] = predict_rows(bst, Xv, ho_rows, tag)
        tsum += t_dm + t_tr
        del bst
        torch.cuda.empty_cache()
    assert np.isfinite(oof).all(), f"{vname} 折外分数存在未覆盖的流"
    OOF[vname] = oof
    FOLD_TIME[vname] = tsum
    log(f"{vname} 折外分数仅驻内存，折内训练累计 {tsum/60:.1f} 分")

# ---- p 网格搜索：只用 LSPR23 折外分数 ----
log("=" * 116)
log("机制二的 p 选择：在源年实体分组折外分数上网格搜索，绝不使用 LSPR24")
PSEL = {}
for vname in MATRICES:
    oof = OOF[vname]
    es_max = ent_scores(oof, ent23, N_ENT_23, None)
    ap_max, _ = ent_ap_from(es_max, lab23)
    curve = []
    for p in P_GRID:
        es = ent_scores(oof, ent23, N_ENT_23, p)
        ap, nok = ent_ap_from(es, lab23)
        fold_ap = [
            float(average_precision_score(lab23[fold_of_ent == k], es[fold_of_ent == k]))
            for k in range(N_FOLD)
        ]
        curve.append({"p": p, "oof_ent_ap": ap, "fold_ent_ap": fold_ap,
                      "n_ent_scored": nok})
        log(f"  {vname}  p={p:>6.2f}  折外实体AP={ap:.6f}")
    log(f"  {vname}  取最大聚合（p→∞ 参照）折外实体AP={ap_max:.6f}")
    best_ap = max(c["oof_ent_ap"] for c in curve)
    tied = [c for c in curve if c["oof_ent_ap"] == best_ap]
    tied.sort(key=lambda c: (abs(np.log2(c["p"])), c["p"]))
    p_star = tied[0]["p"]
    at1 = next(c["oof_ent_ap"] for c in curve if c["p"] == 1.0)
    fold_selected = []
    for k in range(N_FOLD):
        fold_best = max(c["fold_ent_ap"][k] for c in curve)
        fold_tied = [c for c in curve if c["fold_ent_ap"][k] == fold_best]
        fold_tied.sort(key=lambda c: (abs(np.log2(c["p"])), c["p"]))
        fold_selected.append(float(fold_tied[0]["p"]))
    PSEL[vname] = {
        "p_selected": p_star, "oof_ent_ap_at_p": best_ap,
        "oof_ent_ap_at_p1": at1, "oof_ent_ap_at_max": ap_max,
        "gain_vs_p1": best_ap - at1, "gain_vs_max": best_ap - ap_max,
        "n_tied": len(tied), "p_at_grid_edge": bool(p_star == P_GRID[-1]),
        "curve": curve,
        "fold_selected_p": fold_selected,
        "curve_spread": float(max(c["oof_ent_ap"] for c in curve)
                              - min(c["oof_ent_ap"] for c in curve)),
    }
    log(f"  ★ {vname} 选中 p={p_star}（折外实体AP={best_ap:.6f}；相对 p=1 {best_ap-at1:+.6f}，"
        f"相对取最大 {best_ap-ap_max:+.6f}；曲线极差 {PSEL[vname]['curve_spread']:.6f}；"
        f"并列 {len(tied)} 个；落在网格上界={PSEL[vname]['p_at_grid_edge']}）")
    del es_max

_context_candidates = ("mean166", "semantic168")
CONTEXT_SELECTED = sorted(
    _context_candidates,
    key=lambda name: (-PSEL[name]["oof_ent_ap_at_max"], INPUT_DIMS[name], name),
)[0]
ADAPTER_SELECTION = {
    "criterion": "LSPR23 三折实体折外 CPA 单机制实体 AP（最大聚合）",
    "selected": CONTEXT_SELECTED,
    "candidates": {
        name: {
            "input_dim": INPUT_DIMS[name],
            "oof_ent_ap_at_max": PSEL[name]["oof_ent_ap_at_max"],
        }
        for name in _context_candidates
    },
    "tie_break": "完全并列时先取维数较小者，再按名称稳定排序",
}
log(f"★ 源年上下文适配器选中 {CONTEXT_SELECTED}：{ADAPTER_SELECTION['candidates']}")

# ---- 两路最终模型：全量 LSPR23 ----
log("=" * 116)
log("两路最终模型：raw83 与源年选中的上下文适配器在全量 LSPR23 上训练")
ALL_ROWS = np.arange(N_FLOW_23, dtype=np.int64)
FINAL = {}
FINAL_TIME = {}
FINAL_VIEWS = ("raw83", CONTEXT_SELECTED)
for vname in FINAL_VIEWS:
    tag = f"{vname}/final"
    bst, t_dm, t_tr = train_booster(view_of(vname), y23, ALL_ROWS, tag)
    bst.save_model(f"{OUT}/model_{vname}.json")
    FINAL[vname] = bst
    FINAL_TIME[vname] = {"dmatrix_seconds": t_dm, "train_seconds": t_tr,
                         "n_tree": int(bst.num_boosted_rounds())}
    log(f"  {tag} 已落盘 {OUT}/model_{vname}.json，树数 {bst.num_boosted_rounds()}")
    torch.cuda.empty_cache()

del XM23, XS23, MATRICES, Xv, OOF, oof, tr_rows, ho_rows
del ALL_ROWS, y23, fold_of_flow, ent23, lab23, fold_of_ent
log(f"LSPR23 输入矩阵已释放")

# =====================================================================================
# 阶段闸门：选择结果写盘冻结，之后才允许读入 LSPR24
# =====================================================================================
FROZEN = {
    "run_name": RUN_NAME,
    "script_sha256": _self_sha,
    "protocol": "树模型无 epoch 概念与检查点选择；机制二的 p 只在 LSPR23 实体分组折外分数上"
                "按预注册网格与并列规则选出；两路最终模型在全量 LSPR23 上训到底；"
                "LSPR24 只在全部选择冻结后读入一次、打分两次",
    "seed": SEED, "device": "cuda", "xgb_params": XGB_PARAMS, "num_boost_round": N_ROUND,
    "effective_config_comparison": EFFECTIVE_CONFIG_COMPARISON_POLICY,
    "xgboost_version": xgb.__version__,
    "n_fold": N_FOLD, "fold_stat": FOLD_STAT,
    "p_grid": list(P_GRID),
    "p_tie_break_rule": "折外实体AP最大者胜；完全并列取 |log2(p)| 最小者；再并列取较小的 p",
    "lspr23": {"n_flow": N_FLOW_23, "n_entity": N_ENT_23, "n_pos_entity": N_POS_ENT_23},
    "p_selection": PSEL,
    "adapter_selection": ADAPTER_SELECTION,
    "final_models": FINAL_TIME,
    "fold_train_seconds": FOLD_TIME,
    "preregistered_readout": {
        "primary": "LSPR24 实体平均精确率，各格用其自身聚合算子（C00/C10 取最大，C01/C11 用选出的 p）",
        "band": "实体级配对自助法 95%% 百分位区间，B=%d，种子 %d；只覆盖评价集抽样波动，"
                "不覆盖 p 的选择波动" % (BOOT_B, BOOT_SEED),
        "case_1": "增益显著为正：C11−C00 的 95% 区间整体大于 0",
        "case_2": "落在波动幅度内：区间跨 0，不得声称机制在树骨干上有效",
        "case_3": "增益为负：区间整体小于 0，如实报告机制在树骨干上失效",
        "case_4": "单独效应方向：A=C10−C00、B=C01−C00、交互=C11−C10−C01+C00，各给点估计与区间",
        "not_used": "感知机骨干逐流口径三次重复得到的 11.59 个百分点不适用于本行："
                    "骨干不同、评价单元不同；XGBoost 固定种子固定设备后训练确定性，"
                    "重复训练波动为零，不能充当波动幅度",
    },
}
json.dump(FROZEN, open(f"{OUT}/selection_frozen_xgb2x2.json", "w"),
          ensure_ascii=False, indent=2, default=str)
SELECTION_FROZEN = True
log("=" * 116)
log(f"选择阶段结束，已冻结写盘 {OUT}/selection_frozen_xgb2x2.json")
for vname in ("raw83", CONTEXT_SELECTED):
    log(f"  {vname}: p={PSEL[vname]['p_selected']}  折外实体AP={PSEL[vname]['oof_ent_ap_at_p']:.6f}")

# =====================================================================================
# 阶段二：首次读入 LSPR24
# =====================================================================================
log("=" * 116)
log("阶段二 评价：首次读入 LSPR24（选择已冻结）")
assert SELECTION_FROZEN, "阶段闸门未开"
_N24_LOADS += 1
assert _N24_LOADS == 1, f"LSPR24 只允许从磁盘读入一次，当前第 {_N24_LOADS} 次"
y24 = guarded_load("y24")
I24 = guarded_load("I24")
M24 = guarded_load("M24")
s24 = guarded_load("s24", True)
d24 = guarded_load("d24", True)
t24 = guarded_load("t24")
assert len(y24) == N_FLOW_24, f"LSPR24 流数自检失败：{len(y24):,}"
assert_sequence_time_monotonic(t24, I24, M24, "LSPR24")
del t24

key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT_24 = int(ent24.max()) + 1
ent_lab = np.zeros(N_ENT_24, np.float32)
np.maximum.at(ent_lab, ent24, y24)
FLOW_PI_24 = float(y24.astype(np.float64).mean())
log(f"LSPR24 流={len(y24):,} 实体={N_ENT_24:,} 正例实体={int(ent_lab.sum()):,} "
    f"逐流正例率={FLOW_PI_24:.10f}")
assert N_ENT_24 == N_ENT_24_EXPECT, f"LSPR24 实体数自检失败：{N_ENT_24}"
assert int(ent_lab.sum()) == N_POS_ENT_24_EXPECT, f"LSPR24 正例实体自检失败：{int(ent_lab.sum())}"
assert abs(FLOW_PI_24 - FLOW_PI_24_EXPECT) < 1e-9, f"LSPR24 逐流正例率自检失败：{FLOW_PI_24:.12f}"
log(f"LSPR24 自检通过：实体 {N_ENT_24_EXPECT:,} / 正例实体 {N_POS_ENT_24_EXPECT} / "
    f"逐流正例率 {FLOW_PI_24_EXPECT}")
del key24, s24, d24

# -------------------------------------------------------------------------------------
# 回归比对门禁（失败门，与设备无关）：用既有 CPU 运行落盘的逐流分数跑本脚本的评价代码
# -------------------------------------------------------------------------------------
log("-" * 116)
log("回归比对门禁：性质=失败门；判据=用既有 CPU 运行的逐流分数重算，必须逐位重现三个锚点")
log(f"  输入分数 {CPU_SCORES_NPY}（既有 CPU 运行的产物，与设备无关）")
assert os.path.exists(CPU_SCORES_NPY), f"回归比对门禁缺输入：{CPU_SCORES_NPY}"
_cpu_sc = guarded_load("scores_xgboost_dijk2026", path=CPU_SCORES_NPY)
assert len(_cpu_sc) == N_FLOW_24, f"锚点分数长度 {len(_cpu_sc):,} 与 LSPR24 流数不符"
_es = ent_scores(_cpu_sc, ent24, N_ENT_24, None)
_re = {
    "flow_ap": float(average_precision_score(y24, _cpu_sc)),
    "ent_ap_max": ent_ap_from(_es, ent_lab)[0],
    "dr_at_fpr_max": dr_at_fpr_from(_es, ent_lab),
}
GATE = {"nature": "失败门", "kind": "结构性核验（同一份分数走本脚本评价代码）",
        "tolerance": GATE_TOL, "anchor": CPU_ANCHOR, "recomputed": _re, "delta": {}}
_bad = []
for k, want in CPU_ANCHOR.items():
    d = _re[k] - want
    GATE["delta"][k] = d
    log(f"  {k:<16} 重算 {_re[k]:.12f}  锚点 {want:.12f}  Δ={d:+.3e}")
    if abs(d) > GATE_TOL:
        _bad.append(k)
GATE["passed"] = not _bad
if _bad:
    GATE["failed_keys"] = _bad
    json.dump(GATE, open(f"{OUT}/regression_gate_failure.json", "w"), ensure_ascii=False, indent=2)
    log(f"  ★ 回归比对门禁不通过：{_bad}。本脚本的实体聚合或评价判据与既有脚本不一致，"
        f"差异已写 {OUT}/regression_gate_failure.json，停止。")
    raise SystemExit(f"回归比对门禁失败：{_bad}")
log(f"  回归比对门禁通过（全部 |Δ| ≤ {GATE_TOL}）：实体构造、聚合、AP 与 DR 判据与既有脚本一致")
del _cpu_sc, _es

# -------------------------------------------------------------------------------------
# 只构造源年选中的目标年上下文输入，两路最终模型各打一次分
# -------------------------------------------------------------------------------------
log("-" * 116)
if CONTEXT_SELECTED == "mean166":
    XC24 = build_prefix_matrix(f"{CACHE}/X24.npy", N_FLOW_24, I24, M24, "LSPR24/mean166")
elif CONTEXT_SELECTED == "semantic168":
    XC24 = build_semantic_matrix(f"{CACHE}/X24.npy", N_FLOW_24, I24, M24, "LSPR24/semantic168")
else:
    raise AssertionError(f"未知上下文适配器：{CONTEXT_SELECTED}")
del I24, M24
log(f"LSPR24 输入矩阵 {XC24.shape} 就位，常驻 {XC24.nbytes/2**30:.2f} GiB")
MATRICES = {"raw83": XC24[:, :D_RAW], CONTEXT_SELECTED: XC24}

ALL24 = np.arange(N_FLOW_24, dtype=np.int64)
SC24 = {}
for vname in FINAL_VIEWS:
    _SCORE24_CALLS += 1
    _SCORE24_LEDGER.append({"call": _SCORE24_CALLS, "view": vname})
    assert _SCORE24_CALLS <= len(FINAL_VIEWS), f"LSPR24 打分次数超预算：第 {_SCORE24_CALLS} 次"
    log(f"LSPR24 打分 #{_SCORE24_CALLS}/{len(FINAL_VIEWS)} ← {vname}")
    gpu_guard(f"{vname}/目标年推理前")
    SC24[vname] = predict_rows(FINAL[vname], view_of(vname), ALL24, f"{vname}/LSPR24")
    torch.cuda.empty_cache()
del XC24, MATRICES, ALL24
assert _SCORE24_CALLS == len(FINAL_VIEWS), f"LSPR24 打分次数应为 {len(FINAL_VIEWS)}，实为 {_SCORE24_CALLS}"
assert _N24_LOADS == 1
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，逐流打分 {_SCORE24_CALLS} 次，"
    f"均在选择冻结之后；四格由这 {len(FINAL_VIEWS)} 个分数向量派生")

# =====================================================================================
# 四格
# =====================================================================================
CELLS = [("C00", "raw83", None), ("C01", "raw83", "p"),
         ("C10", CONTEXT_SELECTED, None), ("C11", CONTEXT_SELECTED, "p")]
RES = {}
ES = {}
log("=" * 116)
log("四格：主口径 = 实体平均精确率，各格用其自身聚合算子")
for cid, vname, mode in CELLS:
    p = float(PSEL[vname]["p_selected"]) if mode == "p" else None
    sc = SC24[vname]
    es = ent_scores(sc, ent24, N_ENT_24, p)
    ES[cid] = es
    ap, nok = ent_ap_from(es, ent_lab)
    RES[cid] = {
        "display_name": {"C00": "XGBoost 原始输入＋取最大聚合",
                         "C01": "XGBoost 原始输入＋源年选定幂平均聚合",
                         "C10": "XGBoost 前缀拼接输入＋取最大聚合",
                         "C11": "XGBoost 前缀拼接输入＋源年选定幂平均聚合"}[cid],
        "input_view": vname, "input_dim": INPUT_DIMS[vname],
        "mech1_prefix_context": vname != "raw83",
        "mech2_power_mean": mode == "p", "p": p,
        "ent_ap": ap, "n_ent_scored": nok,
        "dr_at_fpr": dr_at_fpr_from(es, ent_lab),
        "dr_curve": {
            f"fpr_{fpr:g}": dr_at_fpr_from(es, ent_lab, fpr)
            for fpr in TARGET_FPR_GRID
        },
        "flow_ap": float(average_precision_score(y24, sc)),
        "flow_auc": float(roc_auc_score(y24, sc)),
    }
    log(f"  {cid} {RES[cid]['display_name']:<34} 输入 {RES[cid]['input_dim']:>3} 维  "
        f"p={'取最大' if p is None else f'{p:g}'}  实体AP={ap:.6f}  "
        f"DR@4%FPR={RES[cid]['dr_at_fpr']:.6f}  逐流AP={RES[cid]['flow_ap']:.6f}")

# ---- C00 的身份与 CPU 诊断参照 ----
_c00 = RES["C00"]["ent_ap"]
_d_cpu = _c00 - CPU_ANCHOR["ent_ap_max"]
C00_ID = {
    "role": "本行的同设备科学基线",
    "device": "cuda",
    "value_ent_ap": _c00,
    "cpu_reference_ent_ap": CPU_ANCHOR["ent_ap_max"],
    "cpu_reference_device": "cpu",
    "cpu_reference_source": f"{BASE_FULL}/trees_results.json",
    "delta_vs_cpu_reference": _d_cpu,
    "delta_nature": "诊断，不作失败门",
    "why": "GPU 直方图草图与归约顺序、subsample/colsample 随机流均与 CPU 不同，"
           "不预期逐位复现；把绝对复现设为失败门会混淆设备差异与实现差异",
}
log("-" * 116)
log(f"C00 身份：同设备（cuda）科学基线，实体AP={_c00:.6f}")
log(f"  CPU 诊断参照 {CPU_ANCHOR['ent_ap_max']:.6f}（device=cpu），Δ={_d_cpu:+.6f} 个点="
    f"{_d_cpu*100:+.2f}；性质=诊断，不作失败门")

# =====================================================================================
# 配对自助法：预注册的波动幅度
# =====================================================================================
log("=" * 116)
log(f"实体级配对自助法 B={BOOT_B}，种子 {BOOT_SEED}：四格共用同一批重采样下标")
_brs = np.random.RandomState(BOOT_SEED)
_boot = {c: np.empty(BOOT_B, np.float64) for c in RES}
_t0 = time.time()
_ok = {c: np.isfinite(ES[c]) for c in ES}
for b in range(BOOT_B):
    idx = _brs.randint(0, N_ENT_24, N_ENT_24)
    lb = ent_lab[idx]
    if lb.max() <= 0:
        for c in RES:
            _boot[c][b] = np.nan
        continue
    for c in RES:
        m = _ok[c][idx]
        _boot[c][b] = average_precision_score(lb[m], ES[c][idx][m])
    beat("自助法", b + 1, BOOT_B, _t0, every=60.0)
log(f"  自助法完成，用时 {time.time()-_t0:.0f}s")


def ci_of(v):
    v = v[np.isfinite(v)]
    return {"n": int(len(v)), "mean": float(v.mean()),
            "lo95": float(np.percentile(v, 2.5)), "hi95": float(np.percentile(v, 97.5))}


def verdict(ci):
    if ci["lo95"] > 0:
        return "显著为正"
    if ci["hi95"] < 0:
        return "显著为负"
    return "落在波动幅度内"


CONTRAST = {}
for name, expr in [("combo_C11_minus_C00", lambda d: d["C11"] - d["C00"]),
                   ("mech1_only_C10_minus_C00", lambda d: d["C10"] - d["C00"]),
                   ("mech2_only_C01_minus_C00", lambda d: d["C01"] - d["C00"]),
                   ("interaction", lambda d: d["C11"] - d["C10"] - d["C01"] + d["C00"])]:
    point = expr({c: RES[c]["ent_ap"] for c in RES})
    ci = ci_of(expr(_boot))
    CONTRAST[name] = {"point": point, "point_points": point * 100, "ci95": ci,
                      "verdict": verdict(ci)}
    log(f"  {name:<26} 点估计 {point:+.6f}（{point*100:+.2f} 个点）  "
        f"95% 区间 [{ci['lo95']:+.6f}, {ci['hi95']:+.6f}]  → {verdict(ci)}")

_A = CONTRAST["mech1_only_C10_minus_C00"]["point"]
_B = CONTRAST["mech2_only_C01_minus_C00"]["point"]
SIGN_PATTERN = ("A>0 且 B>0" if (_A > 0 and _B > 0) else
                "A>0 且 B≤0" if _A > 0 else
                "A≤0 且 B>0" if _B > 0 else "A≤0 且 B≤0")
MAIN_CASE = {"显著为正": "情形一 增益显著为正",
             "落在波动幅度内": "情形二 落在波动幅度内",
             "显著为负": "情形三 增益为负"}[CONTRAST["combo_C11_minus_C00"]["verdict"]]
log(f"  ★ 主判读：{MAIN_CASE}；情形四 单独效应方向：{SIGN_PATTERN}")

# =====================================================================================
# 汇总
# =====================================================================================
W = 118
log("=" * W)
log("XGBoost 骨干 2×2（LSPR24 全量，单次运行，种子 42，device=cuda）")
log(f"{'格':<5}{'名称':<34}{'输入维':>7}{'聚合':>12}{'实体AP':>11}{'DR@4%FPR':>11}{'逐流AP':>10}")
for cid, _, _m in CELLS:
    r = RES[cid]
    agg_txt = "取最大" if r["p"] is None else "p=%g" % r["p"]
    log(f"{cid:<5}{r['display_name']:<34}{r['input_dim']:>7}{agg_txt:>12}"
        f"{r['ent_ap']:>11.6f}{r['dr_at_fpr']:>11.6f}{r['flow_ap']:>10.6f}")
log("-" * W)
log(f"核心表两个数：无机制 C00={RES['C00']['ent_ap']*100:.2f}  "
    f"两机制 C11={RES['C11']['ent_ap']*100:.2f}  "
    f"增益 {CONTRAST['combo_C11_minus_C00']['point_points']:+.2f} 个点")
log("本章既有骨干增益（点估计背景，不作门槛）：" +
    "  ".join(f"{k} {v['no_mech']*100:.2f}→{v['with_mech']*100:.2f}（{v['gain_points']:+.2f}）"
             for k, v in BACKBONE_CONTEXT.items()))
log("=" * W)

RESULT = {
    "run_name": RUN_NAME, "script_sha256": _self_sha,
    "device_ruling": C00_ID["why"],
    "c00_baseline_identity": C00_ID,
    "regression_gate": GATE,
    "seed": SEED, "device": "cuda", "xgboost_version": xgb.__version__,
    "xgb_params": XGB_PARAMS, "num_boost_round": N_ROUND,
    "effective_config_comparison": EFFECTIVE_CONFIG_COMPARISON_POLICY,
    "mechanism_mapping": {
        "mech1": "因果前缀跨流聚合：树骨干无可学隐藏表示，先在 LSPR23 三折实体折外结果上比较"
                 "mean166 与 semantic168，再冻结较优适配器；两者均只使用同一 128 流段内 i≤t 的信息。",
        "mech2": "实体级幂平均池化：神经骨干用梯度学指数 p；树骨干不能反向传播，改为在 LSPR23 上"
                 "按实体分组做折外预测、在折外分数上按预注册网格搜索 p。"
                 "★ 两者不是同一个算子：一个是端到端可学参数，一个是源年选出的固定超参数。",
    },
    "cells": RES, "contrast": CONTRAST,
    "main_case": MAIN_CASE, "sign_pattern_case4": SIGN_PATTERN,
    "bootstrap": {"B": BOOT_B, "seed": BOOT_SEED, "unit": "实体",
                  "covers": "评价集抽样波动", "does_not_cover": "p 的选择波动（p 在源年选定后固定）",
                  "why_not_11_59": "11.59 个百分点取自感知机骨干逐流口径三次重复，骨干与评价单元均不同；"
                                   "XGBoost 固定种子固定设备后训练确定性，重复训练波动为零"},
    "p_selection": PSEL, "adapter_selection": ADAPTER_SELECTION,
    "n_fold": N_FOLD, "fold_stat": FOLD_STAT, "p_grid": list(P_GRID),
    "lspr23": {"n_flow": N_FLOW_23, "n_entity": N_ENT_23, "n_pos_entity": N_POS_ENT_23},
    "lspr24": {"n_flow": N_FLOW_24, "n_entity": N_ENT_24,
               "n_pos_entity": int(ent_lab.sum()), "flow_pos_rate": FLOW_PI_24},
    "backbone_context": BACKBONE_CONTEXT,
    "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_score_calls": _SCORE24_CALLS,
                  "ledger": _SCORE24_LEDGER,
                  "target_labels_read_after_selection_frozen": True,
                  "oof_scores_persisted": False,
                  "target_scores_persisted": False,
                  "note": "四格由两个内存分数向量派生，不保存逐样本分数"},
    "timing": {"fold_train_seconds": FOLD_TIME, "final": FINAL_TIME,
               "total_seconds": time.time() - T0},
}
json.dump(RESULT, open(f"{OUT}/xgb_cpa_elp_results.json", "w"),
          ensure_ascii=False, indent=2, default=str)

swanlab.log(
    {
        "target/C00_entity_ap": RES["C00"]["ent_ap"],
        "target/C01_entity_ap": RES["C01"]["ent_ap"],
        "target/C10_entity_ap": RES["C10"]["ent_ap"],
        "target/C11_entity_ap": RES["C11"]["ent_ap"],
        "target/C11_minus_C00": CONTRAST["combo_C11_minus_C00"]["point"],
        "target/C11_dr_at_fpr_0.04": RES["C11"]["dr_at_fpr"],
        "target/C11_flow_ap": RES["C11"]["flow_ap"],
        "source/selected_adapter_oof_ap": PSEL[CONTEXT_SELECTED]["oof_ent_ap_at_max"],
        "runtime/total_seconds": RESULT["timing"]["total_seconds"],
    },
    step=0,
)
swanlab.finish()
RESULT["tracking"] = {
    "completed": True,
    "aggregate_only": True,
    "workspace": _tracking["workspace"],
    "project": _tracking["project"],
}
json.dump(RESULT, open(f"{OUT}/xgb_cpa_elp_results.json", "w"),
          ensure_ascii=False, indent=2, default=str)
_manifest_names = [
    "feature_schema.json",
    "effective_config_receipts.json",
    "selection_frozen_xgb2x2.json",
    "xgb_cpa_elp_results.json",
] + [f"model_oof_{name}_fold{k}.json" for name in ("raw83", "mean166", "semantic168")
     for k in range(N_FOLD)] + [f"model_{name}.json" for name in FINAL_VIEWS]
_manifest = {
    "run_id": RUN_NAME,
    "script_sha256": _self_sha,
    "feature_schema_sha256": _feature_schema_sha,
    "per_sample_artifacts_persisted": False,
    "files": {},
}
for _name in _manifest_names:
    _path = f"{OUT}/{_name}"
    assert os.path.isfile(_path), f"清单缺少制品：{_name}"
    with open(_path, "rb") as _fh:
        _manifest["files"][_name] = {
            "bytes": os.path.getsize(_path),
            "sha256": hashlib.sha256(_fh.read()).hexdigest(),
        }
json.dump(_manifest, open(f"{OUT}/manifest.json", "w"), ensure_ascii=False, indent=2)
log(f"结果已存 {OUT}/xgb_cpa_elp_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
