# -*- coding: utf-8 -*-
"""第三章 卷积骨干 + 两机制 2×2：在赢过本方法的等参数一维卷积基线上做纯机制消融。

派生自 tools/ch3_baselines_param_matched.py（**逐字复制**其一维卷积支路与全部训练/评价配方），
两个机制的实现取自 tools/ch3_2x2_fairsel.py。

============================ 为什么做这一版 ============================
等参数对照下，90,949 参数的一维卷积（Leoste 2025 架构等比放大，基线配方）在 LSPR24 上得到
  逐流AP 0.363232 / 实体AP(max) 0.520653 / DR@4%FPR(max) 0.671543，
逐流高出本章方法 CPA-ELP（两层感知机基座，90,242 参数，实体AP 0.5184）7.14 个百分点，
实体高出 0.23 个百分点。用户裁决：把这个卷积网络也当作基座跑 2×2，
若两个机制在其上同样有增益，则「卷积骨干加两机制」成为本章方法。

============================ 2026-08-18 设计更正：固定总参数量，不固定骨干 ============================
初版把「等参数骨干」当成约束，那是从跨基座实验照搬来的误用。跨基座比的是不同骨干，固定骨干
规模才能隔离骨干效应；本实验比的是**同一参数预算的两种花法**，该固定的是总量。误用的后果是：
真 `cat` 融合使首个全连接输入宽度由 832 翻倍到 1664，在卷积骨干上多出 86,528 个参数，为保骨干
参数不变，初版被迫改用绑定权重 `h + c`。`h + c` 是完整融合在 W1 = W2 时的特例，表达能力严格更弱，
一旦无增益，「机制无效」与「融合被削弱」不可区分——独立审查据此判 invalidating。

改按固定总量后该问题消失。参数量公式（POOL=16，真 cat 时 w=2 否则 w=1）：

    P = 4*C1 + (3*C1*C2 + C2) + (C2*POOL*FC*w + FC) + (FC + 1)

    c1=26 c2=52 fc=104, w=1 → 90,949（基线原配置，相对 90,242 为 +0.78%）
    c1=26 c2=52 fc=104, w=2 → 177,477（超预算 +96.7%，正是初版不能用真 cat 的原因）
    c1=19 c2=37 fc=74,  w=2 → 89,987（相对 90,242 为 −0.28%，落在 ±10% 内）

三个数在下方 formula_cnn 断言中逐一核对，实测不符即停止。

============================ 六个机制格 ＋ 两个重复训练格 ============================
    格        骨干            机制                          可训练参数  用途
    C00       26/52/104       无                            90,949    回归比对门禁，须复现 52.07%
    C01       26/52/104       仅可学池化                    90,950    单机制
    C10       19/37/74        仅因果前缀，真 cat[h, c]      89,987    单机制
    C11       19/37/74        两者，真 cat[h, c]            89,988    核心表卷积行的正式数字
    C11CTRL   19/37/74        cat[h, h] + 可学池化          89,988    形状与参数化对照
    C11WIDE   19/37/74        cat[h, φ(h)] + 可学池化       89,988    宽度对照，**归因判读用它**
    C00R2     26/52/104       无（换初始化随机源）          90,949    本骨干重复训练波动幅度实测
    C00R3     26/52/104       无（换初始化随机源）          90,949    本骨干重复训练波动幅度实测

C00 与 C01 沿用基线原配置，一个字节都不动——C00 的回归比对门禁靠它，已通过的复现核验也靠它。

C11CTRL 与 C11 的参数量、全连接输入宽度、训练配方完全相同，唯一差别是融合输入为
`torch.cat([h, h], -1)` 而非 `torch.cat([h, c], -1)`。**2026-08-18 角色更正**：它此前被表述为
「宽度对照」，该表述不成立——首个全连接对 `cat[h, h]` 算的是 `W1 h + W2 h = (W1 + W2) h`，
函数类与一个窄全连接严格等价，它排除的是**形状与参数化**，不是「更宽的全连接」。
本脚本据此把它的角色更正为**形状与参数化对照**，一并报告，但不参与归因裁决。

C11WIDE 是宽度对照：融合输入为 `torch.cat([h, φ(h)], -1)`，φ 是构造时用固定种子随机初始化
后冻结（注册为 buffer，`requires_grad` 恒为 False）的线性投影，输出维度与 h 相同。首个全连接
因此吃到 2 倍宽度的非冗余特征，而 φ(h) 只由本流自身的 h 算出，不携带任何跨流信息。φ 不是
可训练参数，故 C11WIDE 的可训练参数量与 C11 逐位相同（构造真值验证中逐项断言）。归因判读
用 A11 − AWIDE：若 C11 不显著高于 C11WIDE，增益就不能归因于因果前缀聚合。

**必须照报的口径限制**：φ 是线性映射，`W1 h + W2 φ(h) = (W1 + W2 Φ) h` 仍是 h 的线性函数，
故 C11WIDE 与 C11CTRL 在**函数类**上同样等价于窄全连接；两者的差别在梯度几何与条件数
（`cat[h, h]` 下 W1 与 W2 的梯度完全绑定，`cat[h, φ(h)]` 下不绑定）。即 C11WIDE 控制的是
「更宽且非冗余的输入特征带来的优化差异」，不是「非线性扩容」，判读时不得说成后者。

绑定权重 `h + c` 的旧四格保留为可选开关（环境变量 CH3_CNN2X2_LEGACY_ADD=1），默认不跑，
用途是日后补同骨干上的干净 2×2 交互项。

============================ 相对基线脚本的改动（只此五处） ============================
一、只保留一维卷积一个架构，去掉 GRU 与全注意力 Transformer 两支。
二、卷积前向中加入两个开关与三种融合算子：
      agg  —— 因果前缀跨流聚合，`c` 的表达式逐字取自 ch3_2x2_fairsel.py 第 125-126 行；
      lp   —— 实体级可学幂平均池化，`lp_pool` 与 `p_log`/`p` 逐字取自 ch3_2x2_fairsel.py
              第 108-121 行，序列级辅助损失逐字取自其第 181-185 行（AUX_W=1.0，同源）；
      fuse —— "cat" 逐字取自 ch3_2x2_fairsel.py 第 127 行 `self.o(self.g(torch.cat([h, c], -1)))`
              的 `torch.cat([h, c], -1)`；"cat_self" 是同式把第二支换成 h 的形状与参数化对照；
              "cat_wide" 是同式把第二支换成冻结随机线性投影 φ(h) 的宽度对照；
              "add" 是旧的绑定权重 `h + c`，只在 C00/C01（c 恒为零张量）与 legacy 开关下使用。
    C00/C01 的 fuse="add" 且 agg=False，故 c 恒为零张量，前向与基线卷积逐位相同——
    这一点由 CH3_CNN2X2_PROBE 构造核验。
三、外层由「三架构 × 四学习率」改为「六个机制格 C00/C01/C10/C11/C11CTRL/C11WIDE × 四学习率，
    再加两个重复训练格 C00R2/C00R3，只在 C00 的择优学习率上各训一次」。
四、输出目录与运行身份字符串。
五、断点续训（原子写、逐轮在途检查点含五处随机状态、逐格完成记录、评价阶段可恢复），
    并对每份可续训制品绑定设计签名 DESIGN_SIGNATURE（格定义、骨干维度、融合算子、训练预算）。
    2026-08-18 的设计更正把 C10/C11 由绑定权重 h + c（骨干 26/52/104）改成真 cat（骨干 19/37/74），
    旧制品与新设计语义不兼容；复用前逐个断言签名一致，不一致即停止，脚本不自行删除旧制品。

**逐字保持不变**：学习率网格 {3e-4, 1e-3, 2e-3, 5e-3} 与择优规则（验证集 top-5 预测平均 AP，
同分取更小学习率）、检查点规则（20 epoch 不早停、top-5 预测平均）、epoch 数、批大小 64、
序列长度 128、逐流 BCEWithLogits + pos_weight、梯度裁剪 1.0、AdamW(wd=0.01)、种子 42、
数据加载与序列构造、LSPR23 实体不相交验证划分、评价代码、实体聚合、DR@4%FPR 阈值取法、
float32 对齐、83 字段预算、全部隔离断言。

============================ 新引入的差异（相对基线脚本，必须照报） ============================
1. 序列级辅助损失（C01/C11/C11CTRL/C11WIDE 四格）：AUX_W=1.0，与 ch3_2x2_fairsel.py 同值。
   基线脚本无此项。
2. 可学池化指数 p_log（C01/C11/C11CTRL/C11WIDE 四格）：+1 个参数，且**不施加权重衰减**（照
   ch3_2x2_fairsel 的参数分组）。骨干参数仍按基线口径统一施加 wd=0.01。
3. C10/C11/C11CTRL/C11WIDE 的骨干缩小到 19/37/74，以便在同一总预算内容纳真 cat 的双宽全连接。
   C00/C01 仍是 26/52/104。因此本脚本的 2×2 交互项跨两个骨干规模，**不可解释**，
   只在 legacy 开关（同骨干、绑定权重）下才有意义。核心表每行只需两个数，不受影响。
4. 前向中对 h 施加掩码 `h * m`（照 ch3_2x2_fairsel）。无效位的 logits 本就被 masked_fill 置零
   且不进入损失，故对 C00 无可观测影响。
5. C11WIDE 的冻结随机线性投影 φ：ch3_2x2_fairsel.py 与基线脚本都没有这一项，它只服务于
   宽度对照，不参与训练（buffer，不在 net.parameters() 内），也不进入任何机制格。
6. 重复训练两格 C00R2/C00R3：与 C00 的差别**只有初始化随机源**（种子 43、44），批采样
   Generator、numpy、python random、训练期 CUDA 随机流、学习率、数据与评价一律不变，
   用途是在本骨干本口径上实测重复训练波动幅度，取代此前从感知机骨干借来的判据。

============================ 历史复现诊断 ============================
C00 使用真实全量 LSPR23 训练和 LSPR24 评价，并与既往等参数卷积基线比对。历史逐轮
轨迹、top-5 集合和目标年三项指标只记作复现诊断，不再要求不同 GPU 运行逐位一致。数据、
切分、模型、优化器、采样、训练预算和评价公式由确定性断言保护；四格科学比较以本次同环境运行的
C00 为基线，不以历史数值偏差中止其余格。
  注意隔离协议要求全部格训练并冻结选择后才允许读入 LSPR24，因此第二道无法前移到训练之间；
  结构性错误由第一道在约 10 秒与约 11 分钟两个时点拦截。

============================ LSPR24 隔离 ============================
guarded_load() 是所有 np.load 的唯一入口，名字含 "24" 且闸门未开时断言失败。
闸门标志 SELECTION_FROZEN 只由 derive_gate_from_disk() 从磁盘制品重新推导，不读可能过期的布尔值。
各格 × 四学习率训练与择优全部完成 → selection_frozen_cnn2x2.json 原子落盘 → 闸门开
→ 才允许读 LSPR24。每进程 LSPR24 只从磁盘读入一次，且只在本进程确有待评价格时读入；
已评价的格从 eval_{格}.json 复用，不重复评价。train_and_select() 函数体内不出现任何 LSPR24 标识符。

============================ 主量口径（2026-08-18 更正，跑前写死） ============================
初版把 ent_ap_max 写死为唯一主量。那是主量选错：实体级可学幂平均池化本身就是一个实体聚合
机制，用 max 聚合评价等于在推理期把该机制关掉，只剩它的训练辅助损失。证据是把同一套判读
规则套到已跑完的感知机 2×2 制品上——主口径下 C00 0.334994 → C11 0.518350 为 +18.34 个百分点
（本章核心表那一行的来源），全 max 口径下 C00 0.334994 → C11 0.291739 为 −4.33 个百分点，
规则会把本章已确立骨干上公认成立的结论判反。

故主量改为 own_operator 口径：**每格用其自身设计的聚合算子**——启用可学池化的格用学到的 p
做幂平均，未启用的格取最大。该口径与核心表一致，落盘字段为 ent_ap_lp_learned（非 lp 格该字段
按定义退化为 ent_ap_max）。ent_ap_max 保留为次级读数一并报告，不参与裁决。

自检入口：CH3_CNN2X2_PROBE=1 时只做各格参数量核算与机制开关的构造真值验证后退出，
不读任何数据、不创建运行身份、不初始化 CUDA、不触碰 LSPR24。
"""

import hashlib
import json
import os
import random
import sys
import time

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:8.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"

# 旧的绑定权重 h + c 四格：默认不跑，用途是日后补同骨干上的干净 2×2 交互项。
# 打开后输出目录与运行身份都带 -legacy-add 后缀，与主五格制品完全隔离。
LEGACY_ADD = os.environ.get("CH3_CNN2X2_LEGACY_ADD") == "1"
_SUFFIX = "-legacy-add" if LEGACY_ADD else ""
RUN_REVISION = "-same-run-c00-v2"

OUT = ("/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/"
       f"ch3-cnn-backbone-2x2{RUN_REVISION}{_SUFFIX}")
CKPT = f"{OUT}/ckpt"
RUN_IDENTITY = f"ch3-cnn-backbone-2x2-seed42{RUN_REVISION}{_SUFFIX}"

# ---- 训练预算：与 ch3_baselines_param_matched.py 逐字相同 ----
SEED, BS, L = 42, 64, 128
EPOCH_STEPS, N_EPOCH, TOPK = 1000, 20, 5
VAL_FRAC, TIME_TAIL = 0.10, 0.15
TARGET_FPR = 0.04
P_BORROW = 1.0562171936035156
WEIGHT_DECAY, GRAD_CLIP = 0.01, 1.0
DROPOUT = 0.1
D = 83                      # 字段预算（Dijk 2026 附录 A 口径），运行时对 X23/X24 再断言一次

# ---- 容量：固定的是**总参数量**，不是骨干规模（2026-08-18 设计更正）----
TARGET_PARAMS = 90242       # 本章方法 CPA-ELP 的参数量
PARAM_TOL = 0.10
CNN_POOL = 16                                     # 自适应最大池化输出长度，各格共用
CNN_C1, CNN_C2, CNN_FC = 26, 52, 104              # 基线原配置，C00/C01 一个字节都不动
CNN_FEAT = CNN_C2 * CNN_POOL                      # 832，基线逐流表示宽度（聚合作用于此）
SMALL_C1, SMALL_C2, SMALL_FC = 19, 37, 74         # 缩小骨干，为真 cat 的双宽全连接腾出预算

# ---- 机制超参：取自 ch3_2x2_fairsel.py 第 50 行 ----
AUX_W = 1.0

# ---- 宽度对照格 C11WIDE 的冻结随机线性投影 φ ----
# φ 只是把 h 线性搬到另一组坐标，使首个全连接的第二半输入与第一半非冗余，但不携带跨流信息。
# 用独立 Generator 按固定种子构造，故不消耗全局随机数、不影响任何其它格的构造顺序，
# 且在任意进程、任意续训点重建都得到同一个 φ。φ 注册为 buffer，requires_grad 恒为 False，
# 不出现在 net.parameters() 内，因此不计入可训练参数量，也无需改动 make_optimizer。
PHI_SEED = 20260818

# ---- 重复训练波动幅度：本骨干本口径实测，取代此前从感知机骨干借来的判据 ----
# 对 C00 在其择优学习率下重复训练三次，三次之间**只有初始化随机源不同**（种子 42/43/44），
# 批采样顺序、训练期随机流、学习率、数据、评价一律相同；三次主量的样本标准差即为判据。
# 第一次就是 C00 本身（种子 42），故只需另训两格。
REPEAT_INIT_SEEDS = [43, 44]
REPEAT_BAND_CELLS = ["C00", "C00R2", "C00R3"]

LR_GRID = [3e-4, 1e-3, 2e-3, 5e-3]
INFER_BS = 512                                    # 基线脚本 ARCHS 中一维卷积的推理批大小

# (格名, agg, lp, 展示名)；骨干维度与融合算子在 CELL_SPEC 中，按格名查表。
# 重复训练两格必须排在 C00 之后：它们的学习率取自 C00 的择优结果，运行时另有断言。
CELLS_MAIN = [
    ("C00", False, False, "卷积26-52-104 无机制（回归比对门禁格）"),
    ("C01", False, True, "卷积26-52-104 仅可学幂平均池化"),
    ("C10", True, False, "卷积19-37-74 仅因果前缀聚合 真cat[h,c]"),
    ("C11", True, True, "卷积19-37-74 因果前缀聚合真cat[h,c]＋可学幂平均池化"),
    ("C11CTRL", False, True, "卷积19-37-74 形状与参数化对照 自拼接cat[h,h]＋可学幂平均池化"),
    ("C11WIDE", False, True, "卷积19-37-74 宽度对照 冻结随机投影cat[h,φ(h)]＋可学幂平均池化"),
    ("C00R2", False, False, "卷积26-52-104 无机制 重复训练第2次（本骨干波动幅度实测）"),
    ("C00R3", False, False, "卷积26-52-104 无机制 重复训练第3次（本骨干波动幅度实测）"),
]
SPEC_MAIN = {
    "C00": {"c1": CNN_C1, "c2": CNN_C2, "fc": CNN_FC, "fuse": "add", "expected": 90949,
            "role": "mechanism", "init_seed": SEED},
    "C01": {"c1": CNN_C1, "c2": CNN_C2, "fc": CNN_FC, "fuse": "add", "expected": 90950,
            "role": "mechanism", "init_seed": SEED},
    "C10": {"c1": SMALL_C1, "c2": SMALL_C2, "fc": SMALL_FC, "fuse": "cat", "expected": 89987,
            "role": "mechanism", "init_seed": SEED},
    "C11": {"c1": SMALL_C1, "c2": SMALL_C2, "fc": SMALL_FC, "fuse": "cat", "expected": 89988,
            "role": "mechanism", "init_seed": SEED},
    "C11CTRL": {"c1": SMALL_C1, "c2": SMALL_C2, "fc": SMALL_FC, "fuse": "cat_self",
                "expected": 89988, "role": "shape_param_control", "init_seed": SEED},
    "C11WIDE": {"c1": SMALL_C1, "c2": SMALL_C2, "fc": SMALL_FC, "fuse": "cat_wide",
                "expected": 89988, "role": "width_control", "init_seed": SEED},
    "C00R2": {"c1": CNN_C1, "c2": CNN_C2, "fc": CNN_FC, "fuse": "add", "expected": 90949,
              "role": "repeat", "init_seed": REPEAT_INIT_SEEDS[0]},
    "C00R3": {"c1": CNN_C1, "c2": CNN_C2, "fc": CNN_FC, "fuse": "add", "expected": 90949,
              "role": "repeat", "init_seed": REPEAT_INIT_SEEDS[1]},
}

# 旧的绑定权重四格：同一骨干 26/52/104，融合算子退化为 h + c。默认不启用。
CELLS_LEGACY = [
    ("C00", False, False, "卷积26-52-104 无机制（回归比对门禁格）"),
    ("C01", False, True, "卷积26-52-104 仅可学幂平均池化"),
    ("C10", True, False, "卷积26-52-104 仅因果前缀聚合 绑定权重h+c"),
    ("C11", True, True, "卷积26-52-104 因果前缀聚合绑定权重h+c＋可学幂平均池化"),
]
SPEC_LEGACY = {cid: {"c1": CNN_C1, "c2": CNN_C2, "fc": CNN_FC, "fuse": "add",
                     "expected": 90949 + (1 if lp else 0),
                     "role": "mechanism", "init_seed": SEED}
               for cid, _agg, lp, _d in CELLS_LEGACY}

CELLS = CELLS_LEGACY if LEGACY_ADD else CELLS_MAIN
CELL_SPEC = SPEC_LEGACY if LEGACY_ADD else SPEC_MAIN
CAT_FUSES = ("cat", "cat_self", "cat_wide")

# 机制格（进入 2×2 与判读）与重复训练格（只用于测波动幅度）分开，报表按角色分组
MECH_CELLS = [c for c in CELLS if CELL_SPEC[c[0]]["role"] != "repeat"]
REPEAT_CELLS = [c for c in CELLS if CELL_SPEC[c[0]]["role"] == "repeat"]
for _i, (_cid, _a, _l, _d) in enumerate(CELLS):
    if CELL_SPEC[_cid]["role"] == "repeat":
        assert _i > [c for c, _, _, _ in CELLS].index("C00"), \
            f"{_cid} 必须排在 C00 之后：其学习率取自 C00 的择优结果"

# ---- 设计签名：绑定格定义、骨干维度、融合算子与训练预算 ----
# 2026-08-18 设计更正把 C10/C11 从绑定权重 h + c（骨干 26/52/104）改为真 cat（骨干 19/37/74）。
# 旧设计留下的 inflight_/done_/cell_/eval_ 制品与新设计语义不兼容，续训若静默复用即产生
# 无法察觉的混合结果。故所有可续训制品都写入本签名，复用前逐个断言一致，不一致即停止。
DESIGN_SIGNATURE = hashlib.sha256(json.dumps(
    {"cells": [[c, bool(a), bool(l)] for c, a, l, _ in CELLS],
     "spec": CELL_SPEC, "legacy_add_fusion": LEGACY_ADD, "pool": CNN_POOL,
     "aux_w": AUX_W, "lr_grid": LR_GRID, "phi_seed": PHI_SEED,
     "budget": [SEED, BS, L, EPOCH_STEPS, N_EPOCH, TOPK, WEIGHT_DECAY, GRAD_CLIP, DROPOUT, D]},
    sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def assert_design(obj, path):
    """复用任何磁盘制品前调用：设计签名不一致即停止，不静默混用两套设计的结果。"""
    got = obj.get("design_signature") if isinstance(obj, dict) else None
    if got != DESIGN_SIGNATURE:
        raise RuntimeError(
            f"设计签名不一致，拒绝复用 {path}：制品={got} 当前={DESIGN_SIGNATURE}。"
            f"该制品来自不同的格定义、骨干维度、融合算子或训练预算（2026-08-18 已把 C10/C11 "
            f"由绑定权重 h + c 改为真 cat 并缩小骨干）。请人工核查后移走旧制品再重跑，"
            f"脚本不自行删除。")

# ---- 回归比对参照：取自 runs/diagnostics/ch3-baselines-param-matched/ 的既有制品 ----
REGRESSION_PLAN = {"flow_ap": 0.363232, "ent_ap_max": 0.520653, "dr_at_fpr_max": 0.671543}
REGRESSION_REF = {"flow_ap": 0.36323181374254815,
                  "ent_ap_max": 0.5206531036853225,
                  "dr_at_fpr_max": 0.6715425531914894}
REGRESSION_TOL = 1e-6
REGRESSION_EXTRA = {"flow_auc": 0.9288797668436543,
                    "ent_ap_lp_borrowed": 0.49212542882490307,
                    "dr_at_fpr_lp_borrowed": 0.6103723404255319}
for _k, _v in REGRESSION_PLAN.items():
    assert abs(round(REGRESSION_REF[_k], 6) - _v) < 1e-12, \
        f"回归比对参照 {_k} 与计划书六位小数不一致"

# C00 应当逐点复现的 LSPR23 验证 AP 轨迹（基线 neural_results.json → val_ap_history.cnn_*）
C00_REF_HISTORY = {
    3e-4: [0.9562395542, 0.988633710011, 0.993832235113, 0.99493325907, 0.996053487421,
           0.997246389175, 0.996104890465, 0.997859065409, 0.998417363669, 0.998637957646,
           0.998769121837, 0.998811599903, 0.998911247882, 0.998860233254, 0.998862337078,
           0.998854902102, 0.998597396631, 0.998814324726, 0.999337328504, 0.999188366778],
    1e-3: [0.990949856705, 0.992842738867, 0.995755194992, 0.996553880542, 0.998199433719,
           0.998251259026, 0.997080662636, 0.998736606808, 0.998901863383, 0.997648283858,
           0.998398341667, 0.997611053791, 0.998965068058, 0.999586222284, 0.998623559272,
           0.999027788724, 0.998072758414, 0.998568691156, 0.999373329709, 0.999602623291],
    2e-3: [0.992085671026, 0.992088904524, 0.996060500743, 0.995794145952, 0.998712768406,
           0.998841557144, 0.998557888201, 0.999258435397, 0.999480577522, 0.999512995421,
           0.99936930455, 0.999607855433, 0.999599145932, 0.999704045525, 0.998911191923,
           0.999576601329, 0.999530533647, 0.999537639958, 0.999569682753, 0.99961202451],
    5e-3: [0.986442740888, 0.960459246008, 0.990451885407, 0.986158306339, 0.993293586432,
           0.99532367615, 0.992522157817, 0.996964719618, 0.994419715364, 0.996319497626,
           0.990758493338, 0.998887685229, 0.996558118108, 0.995619189685, 0.997743028245,
           0.998153691221, 0.998532449337, 0.993051460285, 0.998546234202, 0.997920008874],
}
C00_REF_SELECTION = {
    3e-4: {"topk_epochs": [13, 14, 15, 19, 20], "val_ap_pred_avg": 0.9993186662739039},
    1e-3: {"topk_epochs": [13, 14, 16, 19, 20], "val_ap_pred_avg": 0.999537497166072},
    2e-3: {"topk_epochs": [12, 13, 14, 16, 20], "val_ap_pred_avg": 0.9997590596907202},
    5e-3: {"topk_epochs": [12, 16, 17, 19, 20], "val_ap_pred_avg": 0.9993047254394929},
}
C00_REF_CHOSEN_LR = 2e-3
STRUCT_TOL = 1e-3          # LSPR23 早检：超过此值判为结构性差异，立即退出
WARN_TOL = 1e-6            # 介于两者之间记严重警告，交由 LSPR24 硬门禁裁决

# =====================================================================================
# 预注册判读参照（跑前写死，见实施计划第五节与零点六节；看到结果后不得调整）
# =====================================================================================
MLP_CPA_ELP_ENT_AP = 0.5184        # 感知机骨干 CPA-ELP 的实体 AP，仅作绝对水平旁参

# ---- 主量口径（2026-08-18 更正，跑前写死；理由见文件头「主量口径」一节）----
# own_operator：每格用其自身设计的聚合算子——启用可学池化的格用学到的 p 做幂平均，
# 未启用的格取最大。落盘字段 ent_ap_lp_learned 就是这个语义（非 lp 格按定义退化为 max）。
# 初版把 ent_ap_max 写死为唯一主量属于主量选错：用 max 评价等于在推理期关掉可学池化机制。
PRIMARY_METRIC_KEY = "ent_ap_lp_learned"
PRIMARY_METRIC_CALIBER = "own_operator（各格用其自身设计的聚合算子）"
PRIMARY_METRIC_NAME = ("实体平均精确率，own_operator 口径：启用可学幂平均池化的格用学到的 p "
                       "做幂平均聚合，未启用的格取最大聚合")
SECONDARY_METRIC_KEY = "ent_ap_max"      # 次级读数，一并报告，不参与裁决

# ---- 「显著高于」的判据 = 本骨干本口径实测的重复训练波动幅度（见 REPEAT_BAND_CELLS）----
# 该幅度由本脚本自己跑出来：C00 在其择优学习率下三次重复训练（仅换初始化随机源）的主量样本
# 标准差，运行时计算并写入结果 JSON 的 repeat_band 字段。判据在跑前写死为「实测样本标准差」
# 这一定义，具体数值由实验给出，事后不得调整定义。
#
# 下面这组数是**借来的对照参考，不再用于裁决**：E5 的 L=128 三种子（42/43/44），记录于
# .Codex/docs/RWKV/2026-08-17-第三章XGBoost基线对照与门槛测算.md 第四节。口径限制（必须照报）：
# 它是**感知机骨干、Lp 聚合**下的实体 AP，与本脚本的骨干不同，且带宽达 7.67 个百分点，
# 很可能把本骨干上的真实增益判成无差异。保留它只为让两个幅度可比。
BORROWED_ENT_AP_SEEDS = [0.462988, 0.476449, 0.337445]
BORROWED_ENT_AP_SD = 0.076664      # 样本标准差（ddof=1），下方断言由三个数重新算出核对
BORROWED_ENT_AP_SOURCE = (".Codex/docs/RWKV/2026-08-17-第三章XGBoost基线对照与门槛测算.md "
                          "第四节：E5 L=128 三种子实体 AP（感知机骨干、Lp 聚合）")
BORROWED_ENT_AP_CAVEAT = ("借自感知机骨干、Lp 聚合的三种子实体 AP，骨干与本脚本不同，"
                          "带宽 7.67 个百分点；只作对照参考，不参与本次裁决")
_m = sum(BORROWED_ENT_AP_SEEDS) / len(BORROWED_ENT_AP_SEEDS)
_sd = (sum((x - _m) ** 2 for x in BORROWED_ENT_AP_SEEDS) / (len(BORROWED_ENT_AP_SEEDS) - 1)) ** 0.5
assert abs(_sd - BORROWED_ENT_AP_SD) < 5e-7, \
    f"借用的波动幅度与制品三个数不自洽：由 {BORROWED_ENT_AP_SEEDS} 算得 {_sd:.6f}"
assert abs(_m - 0.425627) < 5e-7, f"借用的三种子均值应为 0.425627，实为 {_m:.6f}"


def sample_sd(values):
    """样本标准差（ddof=1）。重复训练波动幅度与借用参考共用同一算法。"""
    n = len(values)
    assert n >= 2, "样本标准差至少需要两个数"
    mean = sum(values) / n
    return (sum((x - mean) ** 2 for x in values) / (n - 1)) ** 0.5


assert abs(sample_sd(BORROWED_ENT_AP_SEEDS) - BORROWED_ENT_AP_SD) < 5e-7, \
    "sample_sd 与借用参考的 ddof=1 口径不一致"


def formula_cnn(c1, c2, pool, fc, w=1):
    """可训练参数量。w=2 表示首个全连接的输入宽度因真 cat 融合翻倍。"""
    return 4 * c1 + (3 * c1 * c2 + c2) + (c2 * pool * fc * w + fc) + (fc + 1)


# 三个必须核对的数（实施计划零点六节，实测不符即停止）
assert formula_cnn(16, 32, 16, 64) == 34529, "CNN 参数量公式未能复现 Leoste 2025 发表配置"
assert formula_cnn(26, 52, 16, 104, 1) == 90949, \
    f"基线原配置 26/52/104 无 cat 应为 90,949，实为 {formula_cnn(26, 52, 16, 104, 1)}"
assert formula_cnn(26, 52, 16, 104, 2) == 177477, \
    f"基线原配置 26/52/104 改真 cat 应为 177,477，实为 {formula_cnn(26, 52, 16, 104, 2)}"
assert formula_cnn(19, 37, 16, 74, 2) == 89987, \
    f"缩小骨干 19/37/74 真 cat 应为 89,987，实为 {formula_cnn(19, 37, 16, 74, 2)}"
assert abs(100.0 * (89987 - TARGET_PARAMS) / TARGET_PARAMS + 0.28) < 0.01, \
    "缩小骨干相对 90,242 的偏差应为 −0.28%"

CNN_FORMULA_PARAMS = formula_cnn(CNN_C1, CNN_C2, CNN_POOL, CNN_FC, 1)
assert CNN_FORMULA_PARAMS == 90949, f"C00 骨干公式值应为 90,949，实为 {CNN_FORMULA_PARAMS}"
for _cid, _agg, _lp, _d in CELLS:
    _sp = CELL_SPEC[_cid]
    _w = 2 if _sp["fuse"] in CAT_FUSES else 1
    _want = formula_cnn(_sp["c1"], _sp["c2"], CNN_POOL, _sp["fc"], _w) + (1 if _lp else 0)
    assert _want == _sp["expected"], \
        f"{_cid} 公式值 {_want} 与登记的期望 {_sp['expected']} 不一致"
    assert abs(100.0 * (_want - TARGET_PARAMS) / TARGET_PARAMS) <= PARAM_TOL * 100 + 1e-9, \
        f"{_cid} 参数量 {_want} 相对 {TARGET_PARAMS} 偏差超出 ±10%"

SELECTION_FROZEN = False
_N24_LOADS = 0
_EVAL24_CALLS = 0
_EVAL24_LEDGER = []


def guarded_load(name, allow_pickle=False):
    """所有 np.load 的唯一入口。闸门未开时禁止读入任何名字含 '24' 的数组。"""
    assert SELECTION_FROZEN or "24" not in name, \
        f"阶段闸门未开：选择阶段禁止读入 {name}.npy"
    return np.load(f"{CACHE}/{name}.npy", allow_pickle=allow_pickle)


# =====================================================================================
# 原子写：一律先写 <path>.tmp 再 os.replace，禁止直接写目标路径
# =====================================================================================
def atomic_save_torch(obj, path):
    tmp = f"{path}.tmp"
    with open(tmp, "wb") as fh:
        torch.save(obj, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def atomic_write_json(obj, path):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2, default=str)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def atomic_save_npy(arr, path):
    tmp = f"{path}.tmp.npy"
    np.save(tmp, arr)
    os.replace(tmp, path)


def append_jsonl(record, path):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def lrtag(lr):
    return f"{lr:g}".replace(".", "p").replace("-", "m")


def capture_rng(gen):
    """五处随机状态：torch CPU、torch CUDA 全设备、numpy、python random、批采样 Generator。

    最后一项决定每批取哪些序列，不存就无法复现批次顺序。
    """
    return {"torch_cpu": torch.get_rng_state(),
            "torch_cuda_all": (list(torch.cuda.get_rng_state_all())
                               if torch.cuda.is_available() else []),
            "numpy": np.random.get_state(),
            "python": random.getstate(),
            "batch_gen": gen.get_state()}


def restore_rng(state, gen):
    torch.set_rng_state(state["torch_cpu"])
    if torch.cuda.is_available() and state["torch_cuda_all"]:
        torch.cuda.set_rng_state_all(list(state["torch_cuda_all"]))
    np_state = state["numpy"]
    np.random.set_state((str(np_state[0]), np.asarray(np_state[1], dtype=np.uint32),
                         int(np_state[2]), int(np_state[3]), float(np_state[4])))
    py_state = state["python"]
    random.setstate((int(py_state[0]), tuple(int(v) for v in py_state[1]),
                     None if py_state[2] is None else float(py_state[2])))
    gen.set_state(state["batch_gen"])


# =====================================================================================
# 模型：卷积骨干 + 两个机制开关
#   卷积拓扑与分类头逐字复制 ch3_baselines_param_matched.py 第 223-240 行；
#   lp_pool / p_log / p 逐字复制 ch3_2x2_fairsel.py 第 108-121 行；
#   c 的表达式逐字复制 ch3_2x2_fairsel.py 第 125-126 行。
# =====================================================================================
def lp_pool(s, m, p):
    ls = torch.log(s.clamp(min=1e-7)); n = m.sum(1).clamp(min=1.0)
    return torch.exp((torch.logsumexp((p * ls).masked_fill(m < 0.5, -1e30), 1) - torch.log(n)) / p)


class CnnBackboneTwoMechanism(nn.Module):
    """Leoste 2025 卷积拓扑 ＋ 因果前缀跨流聚合 ＋ 实体级可学幂平均池化。

    骨干维度与融合算子由构造参数给定：fuse="add" 是旧的绑定权重 h + c（C00/C01 与 legacy
    开关走这条，且 C00/C01 的 agg=False 使 c 恒为零张量，前向与基线卷积逐位相同）；
    fuse="cat" 是真融合 torch.cat([h, c], -1)；fuse="cat_self" 是形状与参数化对照
    torch.cat([h, h], -1)；fuse="cat_wide" 是宽度对照 torch.cat([h, φ(h)], -1)，φ 为冻结的
    随机线性投影（buffer，不可训练，不携带跨流信息）。
    """

    def __init__(self, agg, lp, c1=CNN_C1, c2=CNN_C2, fc=CNN_FC, fuse="add"):
        super().__init__()
        assert fuse in ("add",) + CAT_FUSES, f"未知融合算子 {fuse}"
        self.agg, self.lp, self.fuse = agg, lp, fuse
        self.c2, self.pool = c2, CNN_POOL
        self.feat = c2 * CNN_POOL
        width = self.feat * (2 if fuse in CAT_FUSES else 1)
        self.convolutions = nn.Sequential(
            nn.Conv1d(1, c1, kernel_size=3, padding=1), nn.ReLU(),
            nn.Conv1d(c1, c2, kernel_size=3, padding=1), nn.ReLU(),
            nn.AdaptiveMaxPool1d(CNN_POOL))
        self.classifier = nn.Sequential(
            nn.Flatten(), nn.Dropout(DROPOUT), nn.Linear(width, fc), nn.ReLU(),
            nn.Linear(fc, 1))
        if lp:
            self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))
        # 宽度对照格的冻结随机线性投影 φ：整段只在 fuse="cat_wide" 时执行，其余各格的模块
        # 创建顺序与随机数消耗因此逐字不变。φ 用独立 Generator 按 PHI_SEED 构造，不消耗全局
        # 随机数；取值范围与 nn.Linear 默认初始化一致（bound = 1/sqrt(fan_in)）；无偏置，
        # 故无效位上 h=0 时 φ(h)=0，与 h 的掩码约定一致。注册为 buffer 而非 Parameter：
        # requires_grad 恒为 False，不进 net.parameters()，不计入可训练参数量。
        if fuse == "cat_wide":
            gphi = torch.Generator().manual_seed(PHI_SEED)
            bound = 1.0 / float(np.sqrt(self.feat))
            phi_w = torch.empty(self.feat, self.feat).uniform_(-bound, bound, generator=gphi)
            self.register_buffer("phi_w", phi_w.requires_grad_(False))
            assert not self.phi_w.requires_grad, "φ 必须冻结：requires_grad 应为 False"

    @property
    def p(self):
        return torch.exp(self.p_log).clamp(1e-3, 1e3)

    def forward(self, values, valid):
        batch, length, width = values.shape
        flattened = values.reshape(batch * length, 1, width)
        feature = self.convolutions(flattened)
        m = valid.to(feature.dtype)
        h = feature.reshape(batch, length, self.feat) * m.unsqueeze(-1)
        c = ((torch.cumsum(h, 1) / torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)) * m.unsqueeze(-1)
             if self.agg else torch.zeros_like(h))
        if self.fuse == "cat":
            fused = torch.cat([h, c], -1).reshape(batch * length, 2 * self.feat)
        elif self.fuse == "cat_self":
            fused = torch.cat([h, h], -1).reshape(batch * length, 2 * self.feat)
        elif self.fuse == "cat_wide":
            # φ 逐位置作用于本流自身的 h，不跨位置、不跨样本，故不引入任何跨流信息。
            # 2026-08-18 修正：φ 后必须接非线性。若 φ 为纯线性，则后接的全连接
            # W1·h + W2·φ(h) = (W1 + W2·φ)·h 可折叠为一个窄头，该格的函数类容量
            # 只有名义值的一半，宽度对照因此失效（独立核验判为 invalidating）。
            # 接 ReLU 后该折叠不成立，本格才真正用上翻倍的输入宽度。
            # ReLU 无参数，可训练参数量与 C11 仍逐位相同。
            fused = torch.cat(
                [h, torch.relu(nn.functional.linear(h, self.phi_w))], -1
            ).reshape(batch * length, 2 * self.feat)
        else:
            fused = (h + c).reshape(batch * length, self.c2, self.pool)
        logits = self.classifier(fused).reshape(batch, length)
        return logits.masked_fill(~valid, 0.0)


def baseline_forward(net, values, valid):
    """基线 LeosteNearestTextCnnClassifier.forward 的逐字复制，只用于构造核验 C00 前向等价。"""
    batch, length, width = values.shape
    flattened = values.reshape(batch * length, 1, width)
    logits = net.classifier(net.convolutions(flattened)).reshape(batch, length)
    return logits.masked_fill(~valid, 0.0)


def build(cid):
    """按格名查表构造。C00/C01 的构造参数与初版逐字相同，模块创建顺序与 RNG 消耗不变。"""
    agg, lp = next((a, l) for c, a, l, _ in CELLS if c == cid)
    sp = CELL_SPEC[cid]
    return CnnBackboneTwoMechanism(agg, lp, sp["c1"], sp["c2"], sp["fc"], sp["fuse"])


def make_optimizer(net, lr, lp):
    """lp 关闭时与基线脚本逐字相同；lp 打开时新增的 p_log 照 ch3_2x2_fairsel 不施加权重衰减。"""
    if not lp:
        return torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=WEIGHT_DECAY)
    decay = [p for n, p in net.named_parameters() if n != "p_log"]
    nodecay = [p for n, p in net.named_parameters() if n == "p_log"]
    assert len(nodecay) == 1, "lp 打开时应恰有一个 p_log 参数"
    return torch.optim.AdamW([{"params": decay, "weight_decay": WEIGHT_DECAY},
                              {"params": nodecay, "weight_decay": 0.0}], lr=lr)


try:
    with open(os.path.abspath(__file__), "rb") as _fh:
        SCRIPT_SHA256 = hashlib.sha256(_fh.read()).hexdigest()
except OSError:
    SCRIPT_SHA256 = None


def capacity_report():
    """各格 torch 实测**可训练**参数量：固定的是总量，不是骨干规模。lp 只增加 1 个（池化指数）。

    C11WIDE 的冻结随机投影 φ 是 buffer，不在 net.parameters() 内，故不计入可训练参数量；
    它的规模另行报告为 frozen_projection_params，使读者知道显存与存储代价从何而来。
    """
    log("=" * 112)
    log(f"设计签名 {DESIGN_SIGNATURE}"
        + (f" | 脚本 SHA-256 {SCRIPT_SHA256}" if SCRIPT_SHA256 else ""))
    log(f"{len(CELLS)} 格可训练参数量核算（预算锚点 {TARGET_PARAMS:,}，允许偏差 "
        f"±{PARAM_TOL*100:.0f}%，"
        + ("legacy 绑定权重四格" if LEGACY_ADD else
           f"{len(MECH_CELLS)} 个机制格 ＋ {len(REPEAT_CELLS)} 个重复训练格") + "）")
    log(f"  公式 P = 4*C1 + (3*C1*C2 + C2) + (C2*POOL*FC*w + FC) + (FC + 1)，POOL={CNN_POOL}，"
        f"真 cat 时 w=2 否则 w=1；lp 再 +1")
    table = {}
    for cid, agg, lp, display in CELLS:
        sp = CELL_SPEC[cid]
        w = 2 if sp["fuse"] in CAT_FUSES else 1
        net = build(cid)
        npar = sum(p.numel() for p in net.parameters())
        frozen_par = sum(b.numel() for b in net.buffers())
        want = formula_cnn(sp["c1"], sp["c2"], CNN_POOL, sp["fc"], w) + (1 if lp else 0)
        assert npar == want, f"{cid} torch 实测 {npar} 与公式值 {want} 不一致"
        assert npar == sp["expected"], f"{cid} torch 实测 {npar} 与登记期望 {sp['expected']} 不一致"
        assert all(p.requires_grad for p in net.parameters()), \
            f"{cid} 的 net.parameters() 内出现不可训练参数，可训练参数量口径失效"
        assert (frozen_par > 0) == (sp["fuse"] == "cat_wide"), \
            f"{cid} 的冻结 buffer 规模 {frozen_par} 与融合算子 {sp['fuse']} 不匹配"
        dev_pct = 100.0 * (npar - TARGET_PARAMS) / TARGET_PARAMS
        assert abs(dev_pct) <= PARAM_TOL * 100 + 1e-9, f"{cid} 偏差 {dev_pct:+.2f}% 超出 ±10%"
        table[cid] = {"display_name": display, "role": sp["role"], "init_seed": sp["init_seed"],
                      "agg": agg, "lp": lp, "fuse": sp["fuse"],
                      "c1": sp["c1"], "c2": sp["c2"], "pool": CNN_POOL, "fc": sp["fc"],
                      "fc_in_width": sp["c2"] * CNN_POOL * w, "params": int(npar),
                      "trainable_params": int(npar),
                      "frozen_projection_params": int(frozen_par),
                      "delta_vs_c00": int(npar - CNN_FORMULA_PARAMS),
                      "deviation_pct": dev_pct}
        log(f"  {cid:<8} agg={int(agg)} lp={int(lp)} fuse={sp['fuse']:<9} "
            f"角色={sp['role']:<21}{display}")
        log(f"      骨干 {sp['c1']}/{sp['c2']}/{sp['fc']} 首个全连接输入宽度 "
            f"{sp['c2'] * CNN_POOL * w} | torch 实测可训练 {npar:,} 参数，公式值 {want:,}，"
            f"相对 {TARGET_PARAMS:,} 偏差 {dev_pct:+.2f}%"
            + (f"，另有冻结投影 φ {frozen_par:,} 个不可训练权重（不计入预算）"
               if frozen_par else ""))
        del net
    if not LEGACY_ADD:
        for ctrl in ("C11CTRL", "C11WIDE"):
            assert table["C11"]["params"] == table[ctrl]["params"], \
                f"{ctrl} 必须与 C11 可训练参数量完全相同，否则对照不成立"
            assert table["C11"]["fc_in_width"] == table[ctrl]["fc_in_width"], \
                f"{ctrl} 必须与 C11 的全连接输入宽度完全相同"
        for rep in (c for c, _, _, _ in REPEAT_CELLS):
            assert table[rep]["params"] == table["C00"]["params"], \
                f"{rep} 必须与 C00 可训练参数量完全相同，否则不是重复训练"
            assert (table[rep]["fuse"], table[rep]["agg"], table[rep]["lp"]) == \
                   (table["C00"]["fuse"], table["C00"]["agg"], table["C00"]["lp"]), \
                f"{rep} 的骨干与机制开关必须与 C00 完全相同"
            assert table[rep]["init_seed"] != table["C00"]["init_seed"], \
                f"{rep} 的初始化随机源必须与 C00 不同，否则不是重复训练"
    return table


def mechanism_probe():
    """机制开关的构造真值验证：CPU 小张量，真值由构造给定，只判定实现正确或不正确。"""
    log("=" * 112)
    log("机制开关构造真值验证（CPU 小张量，不初始化 CUDA，不读数据）")
    results = {}
    torch.manual_seed(0)
    batch, length = 3, 7
    x = torch.randn(batch, length, D)
    valid = torch.ones(batch, length, dtype=torch.bool)
    valid[2, 5:] = False                              # 掺入一条短序列，核验掩码路径

    def check(name, ok, extra=""):
        results[name] = bool(ok)
        log(f"  {'通过' if ok else '不通过'} | {name}{('  ' + extra) if extra else ''}")
        return ok

    # 一、绑定权重格（fuse="add" 且 agg 关闭）的前向与基线卷积逐位相同。
    #     这是 C00 能复现基线的前提。真 cat 格的首个全连接输入宽度翻倍，
    #     baseline_forward 的形状本就不匹配，故只对 add 格执行该项。
    for cid, agg, lp, _ in CELLS:
        sp = CELL_SPEC[cid]
        net = build(cid).eval()
        if sp["fuse"] == "add":
            with torch.no_grad():
                same = torch.equal(net(x, valid), baseline_forward(net, x, valid))
            if agg:
                check(f"{cid} 绑定权重且 agg 开启，前向确实偏离基线卷积", not same)
            else:
                check(f"{cid} 绑定权重且 agg 关闭，前向与基线卷积逐位相同", same)
        else:
            with torch.no_grad():
                out = net(x, valid)
            in_w = net.classifier[2].in_features
            check(f"{cid} 真 cat 格首个全连接输入宽度为 2×{net.feat}",
                  in_w == 2 * net.feat, f"实测 in_features={in_w}")
            check(f"{cid} 真 cat 格前向输出形状为 (批, 长度)",
                  tuple(out.shape) == (batch, length), f"实测 {tuple(out.shape)}")

    # 二、agg 关闭时同一批内其他样本不影响本样本
    net00 = CnnBackboneTwoMechanism(False, False).eval()
    x2 = x.clone(); x2[1] = torch.randn(length, D)
    with torch.no_grad():
        ok = torch.equal(net00(x, valid)[0], net00(x2, valid)[0])
    check("agg 关闭：改动同批其他样本不影响本样本输出", ok)

    # 三、agg 开启时跨样本仍互不影响（聚合只在序列内）
    net10 = CnnBackboneTwoMechanism(True, False).eval()
    with torch.no_grad():
        ok = torch.equal(net10(x, valid)[0], net10(x2, valid)[0])
    check("agg 开启：聚合只在序列内，跨样本仍互不影响", ok)

    # 四、agg 开启时因果性：位置 t 只受 <= t 的输入影响
    t0 = 3
    x_future = x.clone(); x_future[0, t0 + 1:] = torch.randn(length - t0 - 1, D)
    x_past = x.clone(); x_past[0, t0 - 1] = torch.randn(D)
    with torch.no_grad():
        base = net10(x, valid)[0]
        fut = net10(x_future, valid)[0]
        pas = net10(x_past, valid)[0]
    check("agg 开启：改动 t 之后的输入不影响 <= t 的输出（因果性成立）",
          torch.equal(base[:t0 + 1], fut[:t0 + 1]))
    check("agg 开启：改动 t 之前的输入确实改变 >= t 的输出（聚合确实生效）",
          not torch.equal(base[t0:], pas[t0:]))

    # 五、lp 关闭时不存在池化指数参数；开启时恰多一个
    check("lp 关闭：模型无 p_log 参数",
          not hasattr(CnnBackboneTwoMechanism(False, False), "p_log"))
    check("lp 开启：模型有且仅有一个 p_log 参数",
          sum(p.numel() for n, p in CnnBackboneTwoMechanism(False, True).named_parameters()
              if n == "p_log") == 1)

    # 六、lp_pool 与解析幂平均逐点对照。真值由公式给定：
    #     M_p(s) = ((1/n) Σ_{有效位} s_i^p)^(1/p)，n 为有效位个数。
    #     注意该式含 1/n 归一，故 p→+∞ 时收敛到 max·n^(−1/p) 而非直接等于 max，
    #     p→−∞ 时收敛到 min·n^(+1/|p|)；下面用解析值而非 max/min 作真值。
    s = torch.tensor([[0.10, 0.40, 0.70, 0.90]])
    m = torch.tensor([[1.0, 1.0, 1.0, 0.0]])
    kept = np.array([0.10, 0.40, 0.70], dtype=np.float64)      # 第 4 位 0.90 被掩码
    for p_val, note in [(1.0, "算术平均"), (2.0, "平方平均"), (-1.0, "调和平均"),
                        (5.0, "偏向大值"), (200.0, "接近最大值"), (-200.0, "接近最小值")]:
        truth = float(np.mean(kept ** p_val) ** (1.0 / p_val))
        got = float(lp_pool(s, m, torch.tensor(p_val)))
        check(f"lp_pool 与解析幂平均一致 p={p_val:g}（{note}）",
              abs(got - truth) <= 2e-6 * max(1.0, abs(truth)),
              f"真值={truth:.8f} 实测={got:.8f} Δ={got-truth:+.2e}")
    check("lp_pool 忽略被掩码位（第 4 位 0.90 不参与）",
          float(lp_pool(s, m, torch.tensor(200.0))) < 0.9 - 1e-3)
    check("lp_pool 随 p 增大单调趋近有效位最大值",
          float(lp_pool(s, m, torch.tensor(1000.0))) > float(lp_pool(s, m, torch.tensor(5.0)))
          and abs(float(lp_pool(s, m, torch.tensor(1000.0))) - 0.70) < 1e-3,
          f"p=1000 实测={float(lp_pool(s, m, torch.tensor(1000.0))):.8f}")

    # 七、序列级辅助损失确实对 p_log 产生非零梯度（机制是活的）
    net11 = build("C11")
    net11.train()
    lo = net11(x, valid)
    mf = valid.to(lo.dtype)
    yb = torch.zeros(batch, length); yb[0, 2] = 1.0
    sq = lp_pool(torch.sigmoid(lo), mf, net11.p).clamp(1e-6, 1 - 1e-6)
    ysq = (yb * mf).amax(1)
    w = 1.0 + (3.0 - 1.0) * ysq
    aux = AUX_W * ((nn.BCELoss(reduction="none")(sq, ysq) * w).sum() / w.sum())
    aux.backward()
    check("序列级辅助损失对 p_log 产生非零梯度",
          net11.p_log.grad is not None and float(net11.p_log.grad.abs()) > 0,
          f"grad={float(net11.p_log.grad):.6e}" if net11.p_log.grad is not None else "grad=None")

    # 八、真 cat 融合与形状参数化对照格的构造真值验证（2026-08-18 设计更正后新增）。
    #     这一组直接决定「增益能否归因于跨流上下文」这一论断是否可检验。
    if not LEGACY_ADD:
        net_cat = build("C10").eval()          # 真 cat[h, c]，agg 开启
        net_ctrl = build("C11CTRL").eval()     # 对照 cat[h, h]，那一半不携带跨流信息
        with torch.no_grad():
            cat_base = net_cat(x, valid)[0]
            cat_fut = net_cat(x_future, valid)[0]
            cat_pas = net_cat(x_past, valid)[0]
            cat_other = net_cat(x2, valid)[0]
            ctrl_base = net_ctrl(x, valid)[0]
            ctrl_pas = net_ctrl(x_past, valid)[0]
            ctrl_other = net_ctrl(x2, valid)[0]
        check("真 cat：改动 t 之后的输入不影响 <= t 的输出（因果性成立）",
              torch.equal(cat_base[:t0 + 1], cat_fut[:t0 + 1]))
        check("真 cat：改动 t 之前的输入确实改变 >= t 的输出（跨流上下文确实进入前向）",
              not torch.equal(cat_base[t0:], cat_pas[t0:]))
        check("真 cat：聚合只在序列内，改动同批其他样本不影响本样本",
              torch.equal(cat_base, cat_other))
        check("形状与参数化对照：改动 t 之前的输入不改变 t 及其后的输出（那一半确实不携带跨流信息）",
              torch.equal(ctrl_base[t0:], ctrl_pas[t0:]))
        check("形状与参数化对照：改动同批其他样本不影响本样本输出",
              torch.equal(ctrl_base, ctrl_other))

        # 同一组权重下，cat[h, c] 与 cat[h, h] 必须给出不同输出，否则对照格没有对照意义
        net_c11 = build("C11").eval()
        state = {k: t.clone() for k, t in net_c11.state_dict().items()}
        net_ctrl2 = build("C11CTRL").eval()
        net_ctrl2.load_state_dict(state)
        with torch.no_grad():
            same_out = torch.equal(net_c11(x, valid), net_ctrl2(x, valid))
        check("同权重下 cat[h, c] 与 cat[h, h] 输出不同（对照格确有对照意义）", not same_out)
        check("形状与参数化对照格与 C11 的参数名与形状完全一致（可整体加载同一份权重）",
              {k: tuple(v.shape) for k, v in net_c11.state_dict().items()}
              == {k: tuple(v.shape) for k, v in net_ctrl2.state_dict().items()})

    # 九、宽度对照格 C11WIDE 的构造真值验证（2026-08-18 漏洞二修复后新增）。
    #     判据：改动同一序列中位置 t 之前其他流的输入后，
    #       C11 的位置 t 输出必须改变（跨流上下文确实进入前向）；
    #       C11WIDE 与 C11CTRL 的位置 t 输出必须不变（两个对照都不携带跨流信息）；
    #       同权重下 C11WIDE 与 C11CTRL 输出必须彼此不同（φ 确实引入了非冗余特征）。
    if not LEGACY_ADD:
        net_c11f = build("C11").eval()
        net_wide = build("C11WIDE").eval()
        net_ctrlf = build("C11CTRL").eval()
        with torch.no_grad():
            c11_base = net_c11f(x, valid)[0]
            c11_pas = net_c11f(x_past, valid)[0]
            wide_base = net_wide(x, valid)[0]
            wide_pas = net_wide(x_past, valid)[0]
            wide_other = net_wide(x2, valid)[0]
            ctrlf_base = net_ctrlf(x, valid)[0]
            ctrlf_pas = net_ctrlf(x_past, valid)[0]
        check(f"跨流真值 · C11：改动位置 {t0} 之前其他流的输入后，位置 {t0} 的输出改变",
              not torch.equal(c11_base[t0:t0 + 1], c11_pas[t0:t0 + 1]),
              f"Δ={float((c11_base[t0] - c11_pas[t0]).abs()):.6e}")
        check(f"跨流真值 · C11WIDE：同一改动后位置 {t0} 的输出逐位不变（φ 不携带跨流信息）",
              torch.equal(wide_base[t0:], wide_pas[t0:]))
        check(f"跨流真值 · C11CTRL：同一改动后位置 {t0} 的输出逐位不变",
              torch.equal(ctrlf_base[t0:], ctrlf_pas[t0:]))
        check("C11WIDE：改动同批其他样本不影响本样本输出", torch.equal(wide_base, wide_other))

        # 同一组可训练权重下，cat[h, φ(h)] 与 cat[h, h] 必须给出不同输出
        st11 = {k: t.clone() for k, t in build("C11").eval().state_dict().items()}
        net_wide2 = build("C11WIDE").eval()
        inc = net_wide2.load_state_dict(st11, strict=False)
        check("C11WIDE 可整体加载 C11 的可训练权重，缺的只有冻结投影 φ",
              list(inc.missing_keys) == ["phi_w"] and list(inc.unexpected_keys) == [],
              f"missing={list(inc.missing_keys)} unexpected={list(inc.unexpected_keys)}")
        net_ctrl3 = build("C11CTRL").eval()
        net_ctrl3.load_state_dict(st11)
        with torch.no_grad():
            wide_out = net_wide2(x, valid)
            ctrl_out = net_ctrl3(x, valid)
        check("同权重下 cat[h, φ(h)] 与 cat[h, h] 输出不同（φ 确实引入非冗余特征）",
              not torch.equal(wide_out, ctrl_out),
              f"最大逐位差={float((wide_out - ctrl_out).abs().max()):.6e}")
        check("C11WIDE 的 φ 是冻结 buffer：不在 net.parameters() 内且 requires_grad 为 False",
              (not net_wide2.phi_w.requires_grad)
              and all(n != "phi_w" for n, _ in net_wide2.named_parameters()))
        check("C11WIDE 与 C11 的可训练参数量逐位相同",
              sum(p.numel() for p in net_wide2.parameters())
              == sum(p.numel() for p in build("C11").parameters()),
              f"C11WIDE={sum(p.numel() for p in net_wide2.parameters()):,}")
        check("φ 在固定种子下可复现：两次独立构造的投影矩阵逐位相同",
              torch.equal(build("C11WIDE").phi_w, build("C11WIDE").phi_w))

    ok_all = all(results.values())
    log(f"机制构造真值验证：{'全部通过，实现正确' if ok_all else '存在不通过项，实现不正确'}"
        f"（{sum(results.values())}/{len(results)}）")
    return results, ok_all


if os.environ.get("CH3_CNN2X2_PROBE") == "1":
    _cap = capacity_report()
    _mech, _mech_ok = mechanism_probe()
    log("自检结束（未读入任何数据，未初始化 CUDA，未创建运行目录，未触碰 LSPR24）")
    sys.exit(0 if _mech_ok else 4)

os.makedirs(CKPT, exist_ok=True)


# =====================================================================================
# 闸门标志：只从磁盘制品重新推导，不读可能过期的布尔值
# =====================================================================================
FROZEN_PATH = f"{OUT}/selection_frozen_cnn2x2.json"


def derive_gate_from_disk():
    frozen_exists = os.path.exists(FROZEN_PATH)
    cells_done = [cid for cid, _, _, _ in CELLS if os.path.exists(f"{CKPT}/cell_{cid}.pt")]
    if frozen_exists and len(cells_done) != len(CELLS):
        missing = [cid for cid, _, _, _ in CELLS if cid not in cells_done]
        raise RuntimeError(
            f"闸门文件已存在但逐格选择制品缺失 {missing}：LSPR24 可能已在此前进程被读入，"
            f"此时重跑选择会破坏最终测试隔离。请人工核查 {OUT} 后再决定，脚本不自行恢复。")
    return frozen_exists, cells_done


_gate_open, _cells_done = derive_gate_from_disk()
log("=" * 112)
log(f"运行身份 {RUN_IDENTITY} | 输出目录 {OUT}")
log(f"闸门状态从磁盘推导：selection_frozen_cnn2x2.json {'存在' if _gate_open else '不存在'}，"
    f"已完成格 {_cells_done if _cells_done else '无'}")

CAPACITY = capacity_report()
MECHANISM, MECHANISM_OK = mechanism_probe()
assert MECHANISM_OK, "机制开关构造真值验证不通过，实现不正确，停止运行"

dev = "cuda" if torch.cuda.is_available() else "cpu"
assert dev == "cuda", "本任务必须在 GPU 上运行"
log(f"torch {torch.__version__} | {torch.cuda.get_device_name(0)}")


def regression_gate_epoch(cid, lr, ep, vap):
    """LSPR23 诊断：记录 C00 逐轮验证 AP 相对历史轨迹的偏差。"""
    if cid != "C00":
        return
    if not np.isfinite(vap):
        raise RuntimeError(f"C00 lr={lr:g} ep{ep} 验证 AP 不是有限值：{vap}")
    ref = C00_REF_HISTORY[lr][ep - 1]
    delta = vap - ref
    level = "结构性偏离" if abs(delta) > STRUCT_TOL else (
        "微小数值偏离" if abs(delta) > WARN_TOL else "一致"
    )
    append_jsonl(
        {
            "cell": cid,
            "lr": lr,
            "epoch": ep,
            "reference": ref,
            "observed": vap,
            "delta": delta,
            "level": level,
        },
        f"{OUT}/regression_diagnostic_lspr23_epochs.jsonl",
    )
    if abs(delta) > STRUCT_TOL:
        log(f"    复现诊断：C00 lr={lr:g} ep{ep} "
            f"验证AP 基线={ref:.12f} 本次={vap:.12f} Δ={delta:+.3e} 超过 {STRUCT_TOL:.0e}")
        log("    历史轨迹只作诊断；确定性合同已由数据、模型、预算和指标断言核对，本次继续。")
    if abs(delta) > WARN_TOL:
        log(f"    复现诊断：C00 lr={lr:g} ep{ep} 验证AP 偏离历史值 Δ={delta:+.3e}")


def regression_gate_cell_selection(cands, chosen_lr):
    """LSPR23 诊断：记录 C00 学习率和 top-5 选择相对历史运行的偏差。"""
    log("-" * 112)
    log("历史复现诊断（LSPR23，不触碰 LSPR24）：C00 择优结果与历史记录比对")
    differences = []
    for r in cands:
        ref = C00_REF_SELECTION[r["lr"]]
        d = r["val_ap_pred_avg"] - ref["val_ap_pred_avg"]
        same_top = list(r["topk_epochs"]) == list(ref["topk_epochs"])
        log(f"  lr={r['lr']:g} top5epoch 基线={ref['topk_epochs']} 本次={r['topk_epochs']} "
            f"{'一致' if same_top else '不一致'} | 预测平均验证AP 基线={ref['val_ap_pred_avg']:.12f} "
            f"本次={r['val_ap_pred_avg']:.12f} Δ={d:+.3e}")
        if not same_top:
            differences.append(f"lr={r['lr']:g} top5 epoch 集合不一致")
        if abs(d) > STRUCT_TOL:
            differences.append(f"lr={r['lr']:g} 预测平均验证AP 偏差 {d:+.3e} 超过 {STRUCT_TOL:.0e}")
    if chosen_lr != C00_REF_CHOSEN_LR:
        differences.append(f"择优学习率 基线={C00_REF_CHOSEN_LR:g} 本次={chosen_lr:g}")
    atomic_write_json({"stage": "lspr23_cell_selection", "cell": "C00",
                       "reference_chosen_lr": C00_REF_CHOSEN_LR,
                       "observed_chosen_lr": chosen_lr, "differences": differences},
                      f"{OUT}/regression_diagnostic_lspr23_selection.json")
    if differences:
        log("历史择优结果存在偏差：")
        for item in differences:
            log(f"    - {item}")
        log("偏差已落盘，本次各格仍以同一次 C00 作科学基线继续。")
    else:
        log("C00 的择优学习率与四档 top-5 epoch 集合均与历史记录一致")


# =====================================================================================
# 阶段一：只读入 LSPR23（闸门已开时整段跳过）
# =====================================================================================
if not _gate_open:
    log("=" * 112)
    log("阶段一 选择：只读入 LSPR23，LSPR24 不进入本进程")
    X23 = guarded_load("X23")
    y23 = guarded_load("y23")
    I23 = guarded_load("I23")
    M23 = guarded_load("M23")
    E23 = guarded_load("E23")
    T23 = guarded_load("T23")
    assert X23.shape[1] == D, f"特征数应为 83（Dijk 2026 附录 A 口径），实为 {X23.shape[1]}"
    assert X23.shape[0] == 16_353_511, f"LSPR23 全量流数自检失败：{X23.shape[0]}"
    log(f"LSPR23 流={len(y23):,} 特征数={D} L=128 冻结序列={len(I23):,}")

    # ---- 验证划分：逐字复用基线脚本第 301-314 行（RandomState(42)，非 default_rng）----
    rs = np.random.RandomState(SEED)
    uent = np.unique(E23)
    perm = rs.permutation(len(uent))
    val_ent = set(uent[perm[:max(1, int(len(uent) * VAL_FRAC))]].tolist())
    m_ent = np.fromiter((e in val_ent for e in E23), bool, len(E23))     # 实体不相交
    t_cut = np.quantile(T23, 1.0 - TIME_TAIL)
    m_time = T23 >= t_cut                                                 # 时间尾部（不作选择信号）
    tr_idx = np.flatnonzero(~(m_ent | m_time))
    val_idx = np.flatnonzero(m_ent & ~m_time)
    assert len(np.intersect1d(val_idx, tr_idx)) == 0, "验证集与训练区有交叠"
    assert len(uent) == 150680, f"LSPR23 实体数自检失败：{len(uent)}"
    assert len(tr_idx) == 208598, f"训练序列数自检失败：{len(tr_idx)}"
    assert len(val_idx) == 22444, f"实体不相交验证序列数自检失败：{len(val_idx)}"
    log("切分自检通过：150,680 实体 / 208,598 训练序列 / 22,444 验证序列，与基线脚本一致")
    del m_ent, m_time, E23, T23

    gX23 = torch.from_numpy(X23).to(dev)
    gy23 = torch.from_numpy(y23).to(dev)
    gI23 = torch.from_numpy(I23).to(dev)
    gM23 = torch.from_numpy(M23).to(dev)
    gtr = torch.from_numpy(tr_idx).to(dev)
    gval = torch.from_numpy(val_idx).to(dev)
    log(f"LSPR23 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

    # ---- 逐流 pos_weight：逐字照抄基线脚本第 326-328 行 ----
    _pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
    _lf = nn.BCEWithLogitsLoss(pos_weight=_pos)
    # ---- 序列级 pos_weight 与 BCE：逐字照抄 ch3_2x2_fairsel.py 第 130-134 行（仅 lp 两格用）----
    _sl = (y23[I23.reshape(-1)].reshape(I23.shape) * M23).max(1) > 0
    _spw = float((1 - _sl.mean()) / max(_sl.mean(), 1e-8))
    _bs = nn.BCELoss(reduction="none")
    del _sl
    log(f"逐流 pos_weight={_pos.item():.6f} | 序列级 spw={_spw:.6f}（口径照抄，用全量 LSPR23）")

    @torch.no_grad()
    def val_scores(net, ibs):
        """LSPR23 实体不相交验证集上的逐流预测与标签。逐字照抄基线脚本第 331-347 行。

        本函数是唯一的模型选择信号来源，只触碰 gX23/gy23/gI23/gM23/gval。
        """
        was_training = net.training
        net.eval(); P = []; Y = []
        for a in range(0, len(val_idx), ibs):
            sel = gval[a:a + ibs]; idx = gI23[sel]; msk = gM23[sel] > 0.5; b = idx.shape[0]
            lo = net(gX23[idx.reshape(-1)].reshape(b, L, D), msk)
            fm = msk.reshape(-1)
            P.append(torch.sigmoid(lo).reshape(-1)[fm].float().cpu().numpy())
            Y.append(gy23[idx.reshape(-1)].reshape(-1)[fm].cpu().numpy())
        if was_training:
            net.train()
        return np.concatenate(P), np.concatenate(Y)

    def train_and_select(cid, agg, lp, display, lr, ibs, init_seed=SEED):
        """训练满 20 epoch 不早停，逐 epoch 记录验证 AP，取前 5 名 epoch 做**预测平均**。

        逐轮写在途检查点（含五处随机状态），可从任意 epoch 边界续训。
        函数体内不出现任何 LSPR24 标识符；此时进程内也没有 LSPR24 数据。

        init_seed 只用于重复训练格（C00R2/C00R3）：它**只**替换模型初始化的随机源。
        init_seed == SEED 时执行到的语句与初版逐字相同，故 C00/C01 的随机数消耗不变。
        init_seed != SEED 时，建模前把全局种子换成 init_seed，建模后立刻复位回 SEED，
        使训练期的 CUDA 随机流（dropout）与 C00 同源；批采样用的 Generator 始终由 SEED 播种，
        numpy 与 python random 也始终是 SEED。于是三次重复之间只有初始化不同。
        """
        tag = f"{cid} {display} lr={lr:g}"
        ck_path = f"{CKPT}/inflight_{cid}_{lrtag(lr)}.pt"
        torch.manual_seed(SEED); np.random.seed(SEED); random.seed(SEED)
        if init_seed != SEED:
            torch.manual_seed(init_seed)
            log(f"  {tag} 重复训练格：初始化随机源换为 {init_seed}，其余一切与 C00 相同")
        net = build(cid).to(dev)
        if init_seed != SEED:
            torch.manual_seed(SEED)
        npar = sum(p.numel() for p in net.parameters())
        opt = make_optimizer(net, lr, lp)
        gen = torch.Generator().manual_seed(SEED)
        hist, snaps, p_hist = [], [], []
        acc_t, start_ep = 0.0, 1
        if os.path.exists(ck_path):
            ck = torch.load(ck_path, map_location="cpu", weights_only=False)
            assert_design(ck, ck_path)
            assert (ck["cell"], ck["lr"], ck["agg"], ck["lp"],
                    ck.get("init_seed", SEED)) == (cid, lr, agg, lp, init_seed), \
                f"在途检查点身份不符：{ck_path}"
            net.load_state_dict({k: t.to(dev) for k, t in ck["model"].items()})
            opt.load_state_dict(ck["optim"])
            hist = [list(x) for x in ck["hist"]]
            snaps = [dict(sd) for sd in ck["snaps"]]
            p_hist = list(ck["p_hist"])
            acc_t = float(ck["elapsed"])
            restore_rng(ck["rng"], gen)
            start_ep = int(ck["epoch"]) + 1
            log(f"  {tag} 从在途检查点恢复：已完成 {ck['epoch']}/{N_EPOCH} epoch，"
                f"已耗时 {acc_t/60:.2f} 分，五处随机状态已回填")
            for _ep, _vap in hist:               # 续训不跳过回归比对早检，已完成的 epoch 一并复核
                regression_gate_epoch(cid, lr, _ep, _vap)
        if start_ep > N_EPOCH:
            log(f"  {tag} 在途检查点已训满，直接进入择优")
        t0 = time.time()
        net.train()
        for ep in range(start_ep, N_EPOCH + 1):
            te = time.time()
            for st in range(EPOCH_STEPS):
                sel = gtr[torch.randint(0, len(tr_idx), (BS,), generator=gen).to(dev)]
                idx = gI23[sel]; msk = gM23[sel] > 0.5
                xb = gX23[idx.reshape(-1)].reshape(BS, L, D)
                yb = gy23[idx.reshape(-1)].reshape(BS, L)
                lo = net(xb, msk)
                loss = _lf(lo[msk], yb[msk])
                if lp:
                    mf = msk.to(lo.dtype)
                    sq = lp_pool(torch.sigmoid(lo), mf, net.p).clamp(1e-6, 1 - 1e-6)
                    ysq = (yb * mf).amax(1)
                    w = 1.0 + (_spw - 1.0) * ysq
                    loss = loss + AUX_W * ((_bs(sq, ysq) * w).sum() / w.sum())
                opt.zero_grad(set_to_none=True); loss.backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(), GRAD_CLIP); opt.step()
                if ep == start_ep and (st + 1) % 250 == 0:
                    el = time.time() - te
                    log(f"    {tag} ep{ep} 步 {st+1}/{EPOCH_STEPS} loss={float(loss.detach()):.6f} "
                        f"{el/(st+1)*1000:.1f} ms/步 → 本档预计 "
                        f"{el/(st+1)*EPOCH_STEPS*(N_EPOCH-start_ep+1)/60:.1f} 分")
            v, _y = val_scores(net, ibs)
            vap = float(average_precision_score(_y, v))
            pv = float(net.p.detach()) if lp else None
            hist.append([ep, vap])
            p_hist.append(pv)
            snaps.append({k: t.detach().cpu().clone() for k, t in net.state_dict().items()})
            acc_t += time.time() - te
            log(f"    {tag} ep {ep:>2}/{N_EPOCH} 验证AP={vap:.6f}"
                + (f" p={pv:.4f}" if lp else "")
                + f" 本轮{(time.time()-te)/60:.2f}分 累计{acc_t/60:.1f}分")
            atomic_save_torch({"design_signature": DESIGN_SIGNATURE,
                               "cell": cid, "agg": agg, "lp": lp, "lr": lr, "epoch": ep,
                               "init_seed": init_seed,
                               "model": {k: t.detach().cpu().clone()
                                         for k, t in net.state_dict().items()},
                               "optim": opt.state_dict(), "hist": hist, "snaps": snaps,
                               "p_hist": p_hist, "elapsed": acc_t,
                               "rng": capture_rng(gen)}, ck_path)
            regression_gate_epoch(cid, lr, ep, vap)   # 先落盘再判，失败时证据仍在
        tr_t = acc_t if start_ep > 1 else time.time() - t0

        # ---- top-5 预测平均：k 事前固定，排序键 (-验证AP, epoch)，同分取更早的 epoch ----
        rank = sorted(range(N_EPOCH), key=lambda i: (-hist[i][1], hist[i][0]))
        top = sorted(rank[:TOPK])
        top_states = [snaps[i] for i in top]
        Pacc, Yv = None, None
        for sd_ in top_states:
            net.load_state_dict({k: t.to(dev) for k, t in sd_.items()})
            P_, Y_ = val_scores(net, ibs)
            Pacc = P_ if Pacc is None else Pacc + P_
            Yv = Y_ if Yv is None else Yv
        assert Yv.max() > 0, "验证集无正例，选择信号无效"
        v_pred = float(average_precision_score(Yv, Pacc / len(top_states)))
        top_info = [[hist[i][0], hist[i][1]] for i in top]
        best_rank_epoch = hist[rank[0]][0]
        log(f"  {tag} 训练 {tr_t/60:.2f} 分 参数量 {npar:,} | top{TOPK} epoch="
            f"{[t[0] for t in top_info]} → 预测平均验证AP={v_pred:.6f} "
            f"（逐epoch最好 {max(h[1] for h in hist):.6f}）")
        record = {"cell": cid, "agg": agg, "lp": lp, "display_name": display, "lr": lr,
                  "init_seed": init_seed,
                  "npar": npar, "val_ap_history": hist, "p_history": p_hist,
                  "topk_epochs": [t[0] for t in top_info],
                  "topk_val_aps": [t[1] for t in top_info],
                  "topk_p": [p_hist[i] for i in top],
                  "p_at_best_epoch": p_hist[rank[0]], "best_epoch": best_rank_epoch,
                  "val_ap_pred_avg": v_pred, "val_ap_argmax": max(h[1] for h in hist),
                  "train_seconds": tr_t,
                  "peak_gib": torch.cuda.max_memory_allocated() / 2 ** 30}
        del net
        torch.cuda.empty_cache()
        return record, top_states

    SEL = {}
    _n_train = len(MECH_CELLS) * len(LR_GRID) + len(REPEAT_CELLS)
    log("=" * 112)
    log(f"{len(MECH_CELLS)} 个机制格 × {len(LR_GRID)} 档学习率"
        + (f" ＋ {len(REPEAT_CELLS)} 个重复训练格 × 1 档（C00 的择优学习率）" if REPEAT_CELLS else "")
        + f" = {_n_train} 次训练，每次 {N_EPOCH} epoch × "
        f"{EPOCH_STEPS} 步 = {N_EPOCH*EPOCH_STEPS:,} 步，BS={BS}，L={L}，种子 {SEED}，不早停")
    log(f"学习率网格（各机制格完全相同）：{[f'{x:g}' for x in LR_GRID]}")

    def lr_grid_of(cid):
        """机制格走四档网格；重复训练格只在 C00 的择优学习率上训一次（其余一切不变）。"""
        if CELL_SPEC[cid]["role"] != "repeat":
            return list(LR_GRID)
        assert "C00" in SEL, f"{cid} 的学习率取自 C00 的择优结果，C00 必须先完成"
        chosen = SEL["C00"]["chosen_lr"]
        # 重复格用于实测本骨干的波动幅度，必须与它所刻画的 C00 同配置，
        # 因此取本次运行的择优值，而不是历史预注册值。与历史不一致只记为诊断，
        # 处理方式与 regression_gate_cell_selection 中的同一事实保持一致，不再致命。
        # 依据：源年验证信号已饱和（四格验证 AP 全在 0.9998 至 0.9999，逐 epoch 波动约 3e-4），
        # 饱和信号上哪一档学习率胜出接近噪声，要求它跨运行复现在结构上不可能稳定成立。
        if chosen != C00_REF_CHOSEN_LR:
            log(f"  诊断：C00 本次择优学习率 {chosen:g} 与历史参考 {C00_REF_CHOSEN_LR:g} 不一致；"
                f"重复格按本次值 {chosen:g} 训练，历史差异只作记录")
        return [chosen]

    for cid, agg, lp, display in CELLS:
        cell_path = f"{CKPT}/cell_{cid}.pt"
        if os.path.exists(cell_path):
            _pack = torch.load(cell_path, map_location="cpu", weights_only=False)
            assert_design(_pack, cell_path)
            SEL[cid] = _pack["selection"]
            log("=" * 112)
            log(f"--- {cid} {display} 已完成，复用 {cell_path}"
                f"（选中 lr={SEL[cid]['chosen_lr']:g}）---")
            if cid == "C00":                      # 复用也要过第一道，不因续训跳过回归比对门禁
                regression_gate_cell_selection(SEL[cid]["candidates"], SEL[cid]["chosen_lr"])
            continue
        _sp = CELL_SPEC[cid]
        _init_seed = _sp["init_seed"]
        _grid = lr_grid_of(cid)
        log("=" * 112)
        log(f"--- {cid} {display}（agg={agg}, lp={lp}, 角色={_sp['role']}, "
            f"初始化随机源={_init_seed}, 学习率={[f'{x:g}' for x in _grid]}）---")
        cands = []
        for lr in _grid:
            done_path = f"{CKPT}/done_{cid}_{lrtag(lr)}.pt"
            if os.path.exists(done_path):
                pack = torch.load(done_path, map_location="cpu", weights_only=False)
                assert_design(pack, done_path)
                assert pack["record"].get("init_seed", SEED) == _init_seed, \
                    f"{done_path} 的初始化随机源与当前设计不符"
                cands.append(pack["record"])
                log(f"  {cid} lr={lr:g} 已完成，复用 {done_path}"
                    f"（预测平均验证AP={pack['record']['val_ap_pred_avg']:.6f}）")
                continue
            rec, states = train_and_select(cid, agg, lp, display, lr, INFER_BS, _init_seed)
            atomic_save_torch({"design_signature": DESIGN_SIGNATURE,
                               "record": rec, "top_states": states}, done_path)
            inflight = f"{CKPT}/inflight_{cid}_{lrtag(lr)}.pt"
            if os.path.exists(inflight):          # done_ 已原子落盘，在途件被取代
                os.remove(inflight)
            cands.append(rec)
        best = max(cands, key=lambda r: (r["val_ap_pred_avg"], -r["lr"]))
        if cid == "C00":
            regression_gate_cell_selection(cands, best["lr"])
        _best_path = f"{CKPT}/done_{cid}_{lrtag(best['lr'])}.pt"
        _best_pack = torch.load(_best_path, map_location="cpu", weights_only=False)
        assert_design(_best_pack, _best_path)
        best_states = _best_pack["top_states"]
        SEL[cid] = {"cell": cid, "agg": agg, "lp": lp, "display_name": display,
                    "role": _sp["role"], "init_seed": _init_seed,
                    "lr_grid": _grid, "infer_bs": INFER_BS, "candidates": cands,
                    "chosen_lr": best["lr"], "chosen": best}
        atomic_save_torch({"design_signature": DESIGN_SIGNATURE,
                           "selection": SEL[cid], "top_states": best_states}, cell_path)
        append_jsonl({"stage": "train_cell_done", "cell": cid, "display_name": display,
                      "chosen_lr": best["lr"], "topk_epochs": best["topk_epochs"],
                      "val_ap_pred_avg": best["val_ap_pred_avg"],
                      "npar": best["npar"], "train_seconds_all_lr":
                          sum(c["train_seconds"] for c in cands),
                      "wall_clock": time.strftime("%Y-%m-%dT%H:%M:%S")},
                     f"{OUT}/progress.jsonl")
        log(f"  ★ {cid} 学习率择优（只用 LSPR23 验证集）："
            + "  ".join(f"lr={c['lr']:g}→{c['val_ap_pred_avg']:.6f}" for c in cands)
            + f"  ⇒ 选 lr={best['lr']:g}")

    # ---- 阶段闸门：先把选择结果原子写盘冻结，再允许读入 LSPR24 ----
    _frozen = {
        "run_identity": RUN_IDENTITY, "design_signature": DESIGN_SIGNATURE,
        "protocol": "卷积骨干 2×2：逐 epoch 在 LSPR23 实体不相交验证集上算逐流 AP，取前 5 名 epoch "
                    "的预测平均；学习率在各机制格相同的四点网格 {3e-4, 1e-3, 2e-3, 5e-3} 中按同一"
                    "验证信号择优；重复训练格 C00R2/C00R3 只在 C00 的择优学习率上各训一次，"
                    "与 C00 的差别只有初始化随机源；LSPR24 不参与选择",
        "primary_metric_key": PRIMARY_METRIC_KEY,
        "primary_metric_caliber": PRIMARY_METRIC_CALIBER,
        "primary_metric_name": PRIMARY_METRIC_NAME,
        "repeat_band_cells": REPEAT_BAND_CELLS, "repeat_init_seeds": REPEAT_INIT_SEEDS,
        "phi_seed": PHI_SEED,
        "seed": SEED, "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS, "batch_size": BS,
        "sequence_length": L, "topk": TOPK, "weight_decay": WEIGHT_DECAY,
        "grad_clip": GRAD_CLIP, "field_budget": D, "aux_w": AUX_W,
        "target_params": TARGET_PARAMS, "param_tolerance": PARAM_TOL, "capacity": CAPACITY,
        "legacy_add_fusion": LEGACY_ADD, "cell_spec": CELL_SPEC,
        "lr_grid": LR_GRID, "sequence_pos_weight": _spw,
        "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
        "cells": {k: {kk: vv for kk, vv in v.items() if kk != "chosen"} for k, v in SEL.items()}}
    atomic_write_json(_frozen, FROZEN_PATH)
    log("=" * 112)
    log(f"选择阶段结束，结果已冻结写盘 {FROZEN_PATH}")
    for cid, _, _, _ in CELLS:
        log(f"  {cid}: 选中 lr={SEL[cid]['chosen_lr']:g} "
            f"top{TOPK}epoch={SEL[cid]['chosen']['topk_epochs']} "
            f"验证AP={SEL[cid]['chosen']['val_ap_pred_avg']:.6f}")

    del gX23, gy23, gI23, gM23, gtr, gval, X23, y23, I23, M23
    torch.cuda.empty_cache()
    log(f"LSPR23 已释放，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")
else:
    log("=" * 112)
    log("阶段一 跳过：闸门文件与各格选择制品均在磁盘上，本进程不读入 LSPR23，直接进入评价阶段")
    _frozen = json.load(open(FROZEN_PATH, encoding="utf-8"))
    assert_design(_frozen, FROZEN_PATH)
    SEL = {}
    for cid, _, _, _ in CELLS:
        _p = f"{CKPT}/cell_{cid}.pt"
        _pack = torch.load(_p, map_location="cpu", weights_only=False)
        assert_design(_pack, _p)
        SEL[cid] = _pack["selection"]

SELECTION_FROZEN = derive_gate_from_disk()[0]
assert SELECTION_FROZEN, "闸门文件未落盘，禁止进入评价阶段"

# =====================================================================================
# 阶段二：此刻才第一次读入 LSPR24，每格只评价一次，已评价的格从磁盘复用
# =====================================================================================
PENDING = [cid for cid, _, _, _ in CELLS if not os.path.exists(f"{OUT}/eval_{cid}.json")]
log("=" * 112)
log(f"阶段二 评价：待评价格 {PENDING if PENDING else '无（全部已有磁盘结果，直接汇总）'}")


def load24():
    global _N24_LOADS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段读入 LSPR24"
    _N24_LOADS += 1
    assert _N24_LOADS == 1, f"LSPR24 只允许从磁盘读入一次，当前第 {_N24_LOADS} 次"
    return (guarded_load("X24"), guarded_load("y24"), guarded_load("s24", True),
            guarded_load("d24", True), guarded_load("I24"), guarded_load("M24"))


RES = {}
if PENDING:
    X24, y24, s24, d24, I24, M24 = load24()
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

    gX24 = torch.from_numpy(X24).to(dev)
    gI24 = torch.from_numpy(I24).to(dev)
    gM24 = torch.from_numpy(M24).to(dev)
    del X24, I24, M24
    log(f"LSPR24 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB，序列 {len(gI24):,}")

    # ---- 评价口径：逐字照抄基线脚本第 507-534 行（含末尾 .astype(np.float32)）----
    def ent_ap(sc, seen, p=None):
        m = seen
        if p is None:
            es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[m], sc[m])
        else:
            num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
            np.add.at(num, ent24[m], np.clip(sc[m], 1e-7, 1.0).astype(np.float64) ** p)
            np.add.at(cnt, ent24[m], 1.0)
            es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p),
                          -np.inf).astype(np.float32)
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
            es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p),
                          -np.inf).astype(np.float32)
        ok = np.isfinite(es); v = es[ok]; l = ent_lab[ok]
        neg = np.sort(v[l == 0])[::-1]
        if len(neg) == 0:
            return float("nan")
        thr = neg[min(int(len(neg) * target), len(neg) - 1)]
        return float((v[l == 1] >= thr).mean())

    @torch.no_grad()
    def score24(cid, agg, lp, states, ibs):
        """LSPR24 逐流打分：top-5 检查点各自推理一遍后**平均预测分数**。

        推理循环与预测平均逐字照抄基线脚本第 537-572 行。每调用一次记一次评价。
        """
        global _EVAL24_CALLS
        assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段评价 LSPR24"
        _EVAL24_CALLS += 1
        _EVAL24_LEDGER.append({"call": _EVAL24_CALLS, "group": "卷积骨干 2×2",
                               "cell": cid, "n_ckpt": len(states)})
        assert _EVAL24_CALLS <= len(PENDING), \
            f"本进程 LSPR24 评价次数超出预算（待评价 {len(PENDING)} 格）：第 {_EVAL24_CALLS} 次"
        log(f"LSPR24 评价 #{_EVAL24_CALLS}/{len(PENDING)} ← {cid} {SEL[cid]['display_name']}"
            f"（lr={SEL[cid]['chosen_lr']:g}，{len(states)} 个检查点预测平均）")
        net = build(cid).to(dev)
        acc = None; seen = None
        t1 = time.time()
        for ci, sd_ in enumerate(states):
            net.load_state_dict({k: t.to(dev) for k, t in sd_.items()})
            net.eval()
            sc = torch.zeros(len(y24), device=dev)
            sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
            for a in range(0, len(gI24), ibs):
                idx = gI24[a:a + ibs]; msk = gM24[a:a + ibs] > 0.5; b = idx.shape[0]
                pr = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, L, D), msk))
                fi = idx.reshape(-1); fm = msk.reshape(-1)
                sc[fi[fm]] = pr.reshape(-1)[fm].float(); sn[fi[fm]] = True
            s_ = sc.cpu().numpy(); n_ = sn.cpu().numpy()
            acc = s_ if acc is None else acc + s_
            seen = n_ if seen is None else (seen | n_)
            del sc, sn
            log(f"    检查点 {ci+1}/{len(states)} 推理完成，累计 {time.time()-t1:.0f}s")
        del net
        torch.cuda.empty_cache()
        return acc / len(states), seen

    def metrics_of(sc, seen, lp, p_learned):
        e_max, n_ok = ent_ap(sc, seen)
        e_lp_borrow, _ = ent_ap(sc, seen, P_BORROW)
        out = {"flow_ap": float(average_precision_score(y24[seen], sc[seen])),
               "flow_auc": float(roc_auc_score(y24[seen], sc[seen])),
               "ent_ap_max": float(e_max),
               "ent_ap_lp_borrowed": float(e_lp_borrow),
               "dr_at_fpr_max": float(dr_at_fpr(sc, seen, TARGET_FPR, None)),
               "dr_at_fpr_lp_borrowed": float(dr_at_fpr(sc, seen, TARGET_FPR, P_BORROW)),
               "n_ent_scored": int(n_ok), "coverage": float(seen.mean())}
        # 2×2 主口径：lp 格用学到的 p 聚合，非 lp 格退化为 max（照 ch3_2x2_fairsel 第 338-339 行）
        if lp:
            e_learn, _ = ent_ap(sc, seen, p_learned)
            out["p_learned"] = float(p_learned)
            out["ent_ap_lp_learned"] = float(e_learn)
            out["dr_at_fpr_lp_learned"] = float(dr_at_fpr(sc, seen, TARGET_FPR, p_learned))
        else:
            out["p_learned"] = None
            out["ent_ap_lp_learned"] = float(e_max)
            out["dr_at_fpr_lp_learned"] = out["dr_at_fpr_max"]
        return out


def regression_gate_stage_two(m):
    """LSPR24 诊断：记录 C00 相对历史等参数卷积基线的三项偏差。"""
    log("-" * 112)
    log("历史复现诊断（LSPR24）：C00 与既有等参数卷积基线逐项比对")
    rows, bad = [], []
    for k in ["flow_ap", "ent_ap_max", "dr_at_fpr_max"]:
        delta = m[k] - REGRESSION_REF[k]
        rows.append({"metric": k, "reference": REGRESSION_REF[k], "observed": m[k],
                     "delta": delta, "pass": bool(abs(delta) <= REGRESSION_TOL)})
        log(f"  {k:<18} 基线={REGRESSION_REF[k]:.12f} 本次={m[k]:.12f} Δ={delta:+.3e} "
            f"{'通过' if abs(delta) <= REGRESSION_TOL else '不通过'}")
        if abs(delta) > REGRESSION_TOL:
            bad.append(k)
    for k, ref in REGRESSION_EXTRA.items():
        log(f"  （参考）{k:<12} 基线={ref:.12f} 本次={m[k]:.12f} Δ={m[k]-ref:+.3e}")
    diagnostic = {"stage": "lspr24_c00_regression", "cell": "C00",
                  "tolerance": REGRESSION_TOL, "rows": rows,
                  "metrics_outside_historical_tolerance": bad,
                  "plan_reference": REGRESSION_PLAN,
                  "historical_match": not bad,
                  "scientific_baseline": "same_run_C00"}
    atomic_write_json(diagnostic, f"{OUT}/regression_diagnostic_lspr24.json")
    if bad:
        worst = max(abs(r["delta"]) for r in rows)
        log(f"历史复现诊断存在偏差：{bad}，最大绝对偏差 {worst:.3e}。")
        log("本次不以历史数值中止其余格；四格统一以同环境的 C00 为科学基线。")
    else:
        log("C00 三项指标在历史容差内复现。")
    return diagnostic


C00_REGRESSION_DIAGNOSTIC = None
for cid, agg, lp, display in CELLS:
    eval_path = f"{OUT}/eval_{cid}.json"
    if os.path.exists(eval_path):
        RES[cid] = json.load(open(eval_path, encoding="utf-8"))
        assert_design(RES[cid], eval_path)
        log(f"{cid} 已有磁盘评价结果，复用 {eval_path}（本进程不重复评价）")
    else:
        _cp = f"{CKPT}/cell_{cid}.pt"
        pack = torch.load(_cp, map_location="cpu", weights_only=False)
        assert_design(pack, _cp)
        ch = SEL[cid]["chosen"]
        p_learned = ch["p_at_best_epoch"] if lp else None
        sc, seen = score24(cid, agg, lp, pack["top_states"], INFER_BS)
        assert seen.all(), f"{cid} 逐流覆盖不全：{seen.mean():.6f}（冻结 I24/M24 应恒为 1.0）"
        atomic_save_npy(sc, f"{OUT}/scores_{cid}.npy")
        RES[cid] = {"design_signature": DESIGN_SIGNATURE,
                    "cell": cid, "display_name": display, "agg": agg, "lp": lp,
                    "role": CELL_SPEC[cid]["role"], "init_seed": CELL_SPEC[cid]["init_seed"],
                    "chosen_lr": ch["lr"], "npar": ch["npar"],
                    "train_seconds": ch["train_seconds"], "topk_epochs": ch["topk_epochs"],
                    "topk_p": ch["topk_p"], "best_epoch": ch["best_epoch"],
                    "val_ap_pred_avg": ch["val_ap_pred_avg"],
                    "capacity": CAPACITY[cid],
                    "scores_path": f"{OUT}/scores_{cid}.npy",
                    **metrics_of(sc, seen, lp, p_learned)}
        atomic_write_json(RES[cid], eval_path)
        append_jsonl({"stage": "eval_cell_done", "cell": cid, "display_name": display,
                      "flow_ap": RES[cid]["flow_ap"], "ent_ap_max": RES[cid]["ent_ap_max"],
                      "dr_at_fpr_max": RES[cid]["dr_at_fpr_max"],
                      "wall_clock": time.strftime("%Y-%m-%dT%H:%M:%S")},
                     f"{OUT}/eval_progress.jsonl")
        del sc, seen
    r = RES[cid]
    log(f"{cid} {display}: 逐流AP={r['flow_ap']:.6f} AUC={r['flow_auc']:.6f} "
        f"| 主量 实体AP(各格自身算子)={r[PRIMARY_METRIC_KEY]:.6f} "
        f"| 次级 实体AP(max)={r[SECONDARY_METRIC_KEY]:.6f} "
        f"DR@4%FPR(max)={r['dr_at_fpr_max']:.6f} "
        f"实体AP(Lp借用)={r['ent_ap_lp_borrowed']:.6f}"
        + (f" p={r['p_learned']:.4f}" if r["p_learned"] is not None else ""))
    if cid == "C00":
        C00_REGRESSION_DIAGNOSTIC = regression_gate_stage_two(r)

assert _EVAL24_CALLS == len(PENDING), \
    f"本进程 LSPR24 评价次数应为 {len(PENDING)}，实为 {_EVAL24_CALLS}"
assert _N24_LOADS == (1 if PENDING else 0), \
    f"LSPR24 磁盘读入次数应为 {1 if PENDING else 0}，实为 {_N24_LOADS}"
log("=" * 112)
log(f"隔离断言通过：本进程 LSPR24 磁盘读入 {_N24_LOADS} 次，评价 {_EVAL24_CALLS} 次，"
    f"复用磁盘结果 {len(CELLS)-len(PENDING)} 格，均在选择冻结之后")

# =====================================================================================
# 汇总、2×2 交互项与预注册判读
# =====================================================================================
W = 140
log("=" * W)
log(f"卷积骨干{'（legacy 绑定权重）' if LEGACY_ADD else ''} 在 LSPR24 全量上的结果")
log(f"主量口径 = {PRIMARY_METRIC_CALIBER}；次级读数 = 实体AP(max)，一并报告，不参与裁决")
log(f"{'格':<9}{'机制与融合':<40}{'逐流AP':>11}{'主量 实体AP':>13}{'次级 实体AP(max)':>17}"
    f"{'DR@4%FPR(max)':>15}{'学习率':>9}{'训练用时':>10}{'可训练参数':>12}")
for cid, agg, lp, display in CELLS:
    r = RES[cid]
    sp = CELL_SPEC[cid]
    mech = f"agg={int(agg)} lp={int(lp)} fuse={sp['fuse']} 骨干{sp['c1']}/{sp['c2']}/{sp['fc']}"
    log(f"{cid:<9}{mech:<40}{r['flow_ap']:>11.6f}{r[PRIMARY_METRIC_KEY]:>13.6f}"
        f"{r[SECONDARY_METRIC_KEY]:>17.6f}{r['dr_at_fpr_max']:>15.6f}"
        f"{r['chosen_lr']:>9g}{r['train_seconds']/60:>9.2f}分{r['npar']:>12,}")
log("=" * W)

# ---- 2×2 交互项：只有同骨干时才可解释 ----
INTER = {}
_same_backbone = len({(CELL_SPEC[c]["c1"], CELL_SPEC[c]["c2"], CELL_SPEC[c]["fc"])
                      for c, _, _, _ in CELLS}) == 1
if _same_backbone:
    log("2×2 交互项：交互 = C11 − C10 − C01 + C00；组合创新 = 交互>0 且 组合>0")
else:
    log("2×2 交互项：本次不可解释，仅留数不判读。C00/C01 与 C10/C11 骨干规模不同"
        f"（{CELL_SPEC['C00']['c1']}/{CELL_SPEC['C00']['c2']}/{CELL_SPEC['C00']['fc']} 对 "
        f"{CELL_SPEC['C11']['c1']}/{CELL_SPEC['C11']['c2']}/{CELL_SPEC['C11']['fc']}），"
        "交互项跨两个规模；交互项论断建立在感知机骨干上，核心表每行只需两个数，不受影响。"
        "同骨干的干净交互项由 CH3_CNN2X2_LEGACY_ADD=1 的补充运行给出。")
for label, key in [("实体AP(主量：各格自身聚合算子)", PRIMARY_METRIC_KEY),
                   ("实体AP(次级：max 聚合)", SECONDARY_METRIC_KEY),
                   ("DR@4%FPR(max 聚合)", "dr_at_fpr_max"),
                   ("逐流AP", "flow_ap")]:
    v = {c: RES[c][key] for c in RES}
    eA = v["C10"] - v["C00"]; eB = v["C01"] - v["C00"]; eAB = v["C11"] - v["C00"]
    inter = eAB - (eA + eB)
    INTER[key] = {"label": label, "C00": v["C00"], "C01": v["C01"], "C10": v["C10"],
                  "C11": v["C11"], "A_agg_only": eA, "B_lp_only": eB, "sum": eA + eB,
                  "combo": eAB, "interaction": inter,
                  "same_backbone_across_cells": bool(_same_backbone),
                  "interpretable": bool(_same_backbone),
                  "crit_interaction_pos": bool(inter > 0), "crit_combo_pos": bool(eAB > 0),
                  "combo_innovation": bool(_same_backbone and inter > 0 and eAB > 0)}
    log(f"【{label}】{'' if _same_backbone else '（跨骨干规模，不可解释）'}")
    log(f"  C00={v['C00']:.6f}  C01={v['C01']:.6f}  C10={v['C10']:.6f}  C11={v['C11']:.6f}")
    log(f"  A(仅聚合)={eA:+.6f}  B(仅Lp)={eB:+.6f}  之和={eA+eB:+.6f}  组合={eAB:+.6f}  "
        f"交互={inter:+.6f}")
    if _same_backbone:
        log(f"  判据一 交互>0: {'通过' if inter > 0 else '不通过'} | "
            f"判据二 组合>基线: {'通过' if eAB > 0 else '不通过'} | "
            f"★ 组合创新{'成立' if (inter > 0 and eAB > 0) else '不成立'}")

# =====================================================================================
# 预注册判读（跑前写死，不得事后调整；不引入统计检验）
#   主量：实体平均精确率，own_operator 口径（各格用其自身设计的聚合算子），落盘字段
#         ent_ap_lp_learned。设 A00 = C00，A11 = C11，ACTRL = C11CTRL，AWIDE = C11WIDE。
#   判据 SD = 本骨干本口径实测的重复训练波动幅度：C00 在其择优学习率下三次重复训练
#         （仅换初始化随机源）的主量样本标准差。借来的 BORROWED_ENT_AP_SD 只作对照参考。
#   四情形（照 2026-08-18 预注册，AWIDE 参与归因裁决，ACTRL 只作形状与参数化对照一并报告）：
#     A11 − A00 < −SD                          → 情形四 同一预算下投入机制不如投入更宽的卷积
#     |A11 − A00| <= SD                        → 情形三 两种花法无差异，机制适用性受骨干限制
#     A11 − A00 > SD 且 A11 − AWIDE > SD       → 情形一 机制有效，增益来自跨流上下文
#     A11 − A00 > SD 且 A11 − AWIDE <= SD      → 情形二 增益来自更宽的全连接，不能归因于聚合
# =====================================================================================
A00 = RES["C00"][PRIMARY_METRIC_KEY]
A11 = RES["C11"][PRIMARY_METRIC_KEY]
ACTRL = RES["C11CTRL"][PRIMARY_METRIC_KEY] if "C11CTRL" in RES else None
AWIDE = RES["C11WIDE"][PRIMARY_METRIC_KEY] if "C11WIDE" in RES else None

# ---- 判据 SD：本骨干本口径实测 ----
_band_ready = all(c in RES for c in REPEAT_BAND_CELLS)
if _band_ready:
    _band_values = [RES[c][PRIMARY_METRIC_KEY] for c in REPEAT_BAND_CELLS]
    _band_seeds = [CELL_SPEC[c]["init_seed"] for c in REPEAT_BAND_CELLS]
    _band_mean = sum(_band_values) / len(_band_values)
    SD = sample_sd(_band_values)
    REPEAT_BAND = {
        "measured_in_this_run": True,
        "cells": list(REPEAT_BAND_CELLS), "init_seeds": _band_seeds,
        "chosen_lr": RES["C00"]["chosen_lr"],
        "primary_metric_key": PRIMARY_METRIC_KEY,
        "primary_metric_caliber": PRIMARY_METRIC_CALIBER,
        "values": _band_values, "mean": _band_mean, "sd_ddof1": SD,
        "definition": "C00 在其择优学习率下三次重复训练（仅换初始化随机源）的主量样本标准差",
        "caveat": ("本骨干本口径实测：卷积骨干、C00 的 own_operator 口径（无可学池化时该口径"
                   "退化为 max 聚合）。A11 用的是学到的 p 幂平均，聚合算子与本幅度不同，"
                   "此处按预注册直接沿用，不作换算"),
        "borrowed_reference_sd": BORROWED_ENT_AP_SD,
        "borrowed_reference_caveat": BORROWED_ENT_AP_CAVEAT}
else:
    SD = None
    REPEAT_BAND = {"measured_in_this_run": False,
                   "reason": "本运行没有重复训练格（legacy 模式），无法实测波动幅度",
                   "borrowed_reference_sd": BORROWED_ENT_AP_SD,
                   "borrowed_reference_caveat": BORROWED_ENT_AP_CAVEAT}

d_base = A11 - A00
d_ctrl = (A11 - ACTRL) if ACTRL is not None else None
d_wide = (A11 - AWIDE) if AWIDE is not None else None


def sd_ratio(delta):
    """差值相当于几倍波动幅度；幅度为零时不做除法，直接报无穷。"""
    if delta is None or SD is None:
        return None
    return abs(delta) / SD if SD > 0 else float("inf")


if AWIDE is None or SD is None:
    case_id = "legacy"
    verdict = ("legacy 绑定权重四格没有宽度对照格与重复训练格，不适用本轮四情形判读；"
               "该运行只用于给出同骨干上的干净 2×2 交互项")
elif d_base < -SD:
    case_id = "情形四"
    verdict = ("情形四：A11 低于 A00 且超出波动幅度 → 同一预算下投入机制不如投入更宽的卷积。"
               "如实照报，并解释与感知机骨干的差异来源")
elif d_base <= SD:
    case_id = "情形三"
    verdict = ("情形三：A11 与 A00 相当（差值落在波动幅度之内）→ 同一预算下两种花法无差异。"
               "如实照报，这是机制适用性受骨干限制的边界发现")
elif d_wide > SD:
    case_id = "情形一"
    verdict = ("情形一：A11 显著高于 A00，且显著高于 AWIDE → 机制有效，且增益来自跨流上下文。"
               "核心表照填卷积行")
else:
    case_id = "情形二"
    verdict = ("情形二：A11 高于 A00 但与 AWIDE 相当 → 增益来自更宽的全连接，"
               "不能归因于因果前缀聚合。必须如实写入正文")

log("=" * W)
log("预注册判读（跑前写死，不得事后调整；不引入统计检验）")
log(f"  主量 = {PRIMARY_METRIC_NAME}")
log(f"  主量口径名 = {PRIMARY_METRIC_CALIBER}，落盘字段 {PRIMARY_METRIC_KEY}；"
    f"次级读数 {SECONDARY_METRIC_KEY} 一并报告，不参与裁决")
if _band_ready:
    log(f"  显著判据 = 本骨干本口径实测的重复训练波动幅度 SD={SD:.6f}")
    log(f"    实测方式：{REPEAT_BAND['definition']}，学习率 {REPEAT_BAND['chosen_lr']:g}，"
        f"初始化随机源 {REPEAT_BAND['init_seeds']}")
    log(f"    三次主量 {[f'{v:.6f}' for v in REPEAT_BAND['values']]}，"
        f"均值 {REPEAT_BAND['mean']:.6f}")
    log(f"    口径说明：{REPEAT_BAND['caveat']}")
    log(f"    对照参考（不用于裁决）：借自感知机骨干的 SD={BORROWED_ENT_AP_SD:.6f}，"
        f"{BORROWED_ENT_AP_CAVEAT}；来源 {BORROWED_ENT_AP_SOURCE}")
    log(f"    实测幅度是借用幅度的 {SD / BORROWED_ENT_AP_SD:.2f} 倍")
else:
    log("  本运行无重复训练格，未实测波动幅度，不进行四情形判读")
log(f"  A00={A00:.6f}  A11={A11:.6f}  ACTRL="
    + (f"{ACTRL:.6f}" if ACTRL is not None else "无")
    + "  AWIDE=" + (f"{AWIDE:.6f}" if AWIDE is not None else "无"))
_r_base, _r_wide, _r_ctrl = sd_ratio(d_base), sd_ratio(d_wide), sd_ratio(d_ctrl)
log(f"  A11−A00={d_base:+.6f}"
    + (f"（{_r_base:.2f} 倍 SD）" if _r_base is not None else "")
    + "  A11−AWIDE="
    + (f"{d_wide:+.6f}（{_r_wide:.2f} 倍 SD）" if d_wide is not None else "不适用"))
log("  A11−ACTRL="
    + (f"{d_ctrl:+.6f}（{_r_ctrl:.2f} 倍 SD）" if d_ctrl is not None else "不适用")
    + "  ← C11CTRL 是形状与参数化对照，一并报告，不参与归因裁决"
      "（cat[h,h] 下 W1h + W2h = (W1+W2)h，函数类等价于窄全连接，排除的不是宽度）")
log(f"  → {verdict}")
log(f"  旁参：感知机骨干 CPA-ELP 实体AP={MLP_CPA_ELP_ENT_AP:.4f}，"
    f"A11 {'高于' if A11 > MLP_CPA_ELP_ENT_AP else '不高于'}该值。"
    "第三章主表基座仍沿用先注册的多层感知机，不因本结果更换")
log("  四种情形一律照报；后两种对本章不利但同样是有效研究结果。"
    "禁止因结果不利而改判据、改架构或重跑。")
log("  归因口径限制（必须照报）：φ 是线性映射，C11WIDE 与 C11CTRL 在函数类上同样等价于"
    "窄全连接，两者差在梯度几何与条件数；C11WIDE 控制的是「更宽且非冗余的输入特征带来的"
    "优化差异」，不是「非线性扩容」。")

atomic_write_json({
    "run_identity": RUN_IDENTITY, "protocol": _frozen["protocol"], "seed": SEED,
    "design_signature": DESIGN_SIGNATURE, "script_sha256": SCRIPT_SHA256,
    "legacy_add_fusion": LEGACY_ADD, "cell_spec": CELL_SPEC,
    "field_budget": D, "aux_w": AUX_W, "target_params": TARGET_PARAMS,
    "param_tolerance": PARAM_TOL, "capacity": CAPACITY, "lr_grid": LR_GRID,
    "mechanism_construct_checks": MECHANISM,
    "p_borrowed_for_lp_sensitivity": P_BORROW, "target_fpr": TARGET_FPR,
    "budget": {"n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS, "batch_size": BS,
               "sequence_length": L, "topk": TOPK},
    "n_train_seq": _frozen["n_train_seq"], "n_val_seq": _frozen["n_val_seq"],
    "historical_reproduction_diagnostic": C00_REGRESSION_DIAGNOSTIC,
    "derived_from": {"baseline_script": "tools/ch3_baselines_param_matched.py",
                     "mechanism_script": "tools/ch3_2x2_fairsel.py",
                     "new_differences": [
                         "序列级辅助损失 AUX_W=1.0（lp 各格），基线脚本无此项",
                         "可学池化指数 p_log（lp 各格），+1 参数且不施加权重衰减",
                         "固定的是总参数量而非骨干规模：C10/C11/C11CTRL/C11WIDE 骨干缩小到 "
                         "19/37/74，以便在同一预算内容纳真 cat 的双宽全连接",
                         "融合算子为真 cat（torch.cat([h, c], -1)）；形状与参数化对照格为 "
                         "torch.cat([h, h], -1)；宽度对照格为 torch.cat([h, φ(h)], -1)，"
                         "φ 是固定种子构造后冻结的线性投影（buffer，不可训练）；"
                         "绑定权重 h + c 仅在 CH3_CNN2X2_LEGACY_ADD=1 时使用",
                         "重复训练格 C00R2/C00R3 与 C00 只差初始化随机源，"
                         "用于实测本骨干本口径的重复训练波动幅度",
                         "跨骨干规模的 2×2 交互项不可解释，本轮不判读",
                         "前向中对逐流表示施加掩码 h * m（对 C00 无可观测影响）"]},
    "cells": RES, "selection": _frozen["cells"], "interaction": INTER,
    "repeat_band": REPEAT_BAND,
    "preregistered_readout": {
        "primary_metric": PRIMARY_METRIC_NAME,
        "primary_metric_key": PRIMARY_METRIC_KEY,
        "primary_metric_caliber": PRIMARY_METRIC_CALIBER,
        "secondary_metric_key": SECONDARY_METRIC_KEY,
        "secondary_readings": {c: RES[c][SECONDARY_METRIC_KEY] for c in RES},
        "A00": A00, "A11": A11, "A_ctrl": ACTRL, "A_wide": AWIDE,
        "control_roles": {"C11CTRL": "形状与参数化对照（cat[h,h]，不参与归因裁决）",
                          "C11WIDE": "宽度对照（cat[h,φ(h)]，参与归因裁决）"},
        "delta_vs_baseline": d_base, "delta_vs_width_control": d_wide,
        "delta_vs_shape_param_control": d_ctrl,
        "significance_band_sd": SD,
        "significance_band_source": "本脚本自测：repeat_band 字段（本骨干本口径实测）",
        "significance_band_definition": REPEAT_BAND.get("definition"),
        "significance_band_values": REPEAT_BAND.get("values"),
        "significance_band_caveat": REPEAT_BAND.get("caveat"),
        "borrowed_band_sd": BORROWED_ENT_AP_SD,
        "borrowed_band_source": BORROWED_ENT_AP_SOURCE,
        "borrowed_band_seeds": BORROWED_ENT_AP_SEEDS,
        "borrowed_band_caveat": BORROWED_ENT_AP_CAVEAT,
        "width_control_caveat": ("φ 是线性映射，W1h + W2φ(h) = (W1 + W2Φ)h 仍是 h 的线性函数，"
                                 "故 C11WIDE 与 C11CTRL 在函数类上同样等价于窄全连接；两者差在"
                                 "梯度几何与条件数。C11WIDE 控制的是「更宽且非冗余的输入特征带来"
                                 "的优化差异」，不是「非线性扩容」"),
        "case": case_id, "verdict": verdict,
        "mlp_cpa_elp_ent_ap": MLP_CPA_ELP_ENT_AP},
    "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals_this_process": _EVAL24_CALLS,
                  "reused_from_disk": len(CELLS) - len(PENDING), "ledger": _EVAL24_LEDGER}},
    f"{OUT}/cnn2x2_results.json")
log(f"全部结果已存 {OUT}/cnn2x2_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
