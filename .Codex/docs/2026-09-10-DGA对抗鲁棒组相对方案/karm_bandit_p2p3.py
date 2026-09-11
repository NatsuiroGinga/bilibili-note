#!/usr/bin/env python3
"""K 臂：MAB-Malware 式 stateless bandit 字符攻击者（方向 a 最小可行实验，P3.5 攻击者资格门）。

机制来源（本地全文核验）
  MAB-Malware（RAID 2020，arXiv:2003.03100v3）：
  - §3.2（p.3）无状态建模：动作基本独立、少数动作即足够 → 用多臂强盗替代长轨迹 MDP，
    避免状态组合爆炸；
  - §3.2（p.3）「动作—内容」对作为整体单元：内容与动作同等重要；
  - §2.1（p.2）黑盒、仅硬标签。
  本地笔记：wiki/papers/attack-detection/2020-Song-MAB-Malware学习型黑盒规避.md
  GRPO 侧隔离：本脚本**不含**任何组相对优势／KL／裁剪项——K 臂与 D 臂的检测器侧完全同构，
  唯一差量是"变体生成机制"（见下），单因素归因干净。

K 臂与 D 臂的唯一差量
  D 臂（official_p2p3.py）：每恶意样本 K=4 变体由 **随机算子** perturb2 生成（CharBot 2 位替换），
    变体在 epoch1 生成后缓存复用；
  K 臂（本脚本）：每恶意样本 K=4 变体由 **学习型 stateless bandit 策略 π_φ** 采样生成，
    策略随批次更新（不复用缓存，每 batch 重新采样）；
  两者检测器侧完全相同：同起点检查点、同批内主样本、同组相对 top-64 过滤
  （GFPO 2508.09726 式(2) 任务化形态，与 D 臂逐行同构）、同分层 lr、同 3 epochs、同种子 42、
  同 MPS 128 子批梯度累积等效、同评价面板与阈值 0.5。

攻击者模型（上下文无关 categorical bandit，stateless）
  - 动作空间：对 SLD（首个点号之前的主体）的每个位置独立采样一个动作。
    动作 = 保留（keep）或 替换为该位置原字符之外的任一字符（replace，36 种）。
  - 策略参数 = 位置桶 × 操作类型 × 字符 的价值表。任务书写作 V[3, op_types, 40]；
    **本脚本实际为 编辑门 gate[3] ＋ 字符表 V[3, 2, 37]**——字符表维度 37 而非 40，因为
    代码库既有的 CharBot/MaskDGA 半替换算子字符表为 'a'-'z','0'-'9','-' 共 37 字符
    （official_p2p3.ALPHA，与 E-A1 v2 同源），扩到 40 会使策略动作空间与评价面板算子不一致；
    编辑门独立于操作维度，理由见 StatelessBandit 类文档（softmax 竞争偏置的实测修正）。
  - 采样（两段式）：位置 i 先以编辑门概率 gate[桶(i)] 的 Bernoulli 决定"是否编辑"
    （初值 0.5，实现任务书要求的 Bernoulli(0.5)＋探索保留，上下界 [0.05, 0.95] 防熵塌缩）；
    发起编辑的位置再从 V[桶(i), 1, ·] 的 softmax 中采样新字符（排除原字符，无效动作被
    结构性排除）。**无状态**——任意位置的取值不依赖其他位置，也不依赖样本身份。
  - 更新：每生成一个变体后用当前检测器打分 s(x̃)，奖励
      r = 1[s < 0.5] + 0.1 · (0.5 − s)          （骗过=1；形状项为连续部分奖励）
    对本变体参与的每个动作 a 做即时更新 V[a] += η_bandit · (r − V[a])（无折扣、无轨迹）。
    一次前向同时服务"组相对过滤 top-64"与"bandit 奖励"两处用途，不额外增加前向次数
    （共同预算口径与 D 臂一致：每 batch 一次候选打分前向）。

判据（冻结 v1，写死在下方常量，脚本不得按结果改动）
  K vs D（同 screening 规格、同 T17 源年、同检查点起点、seed=42、K=4、top-64 配额）：
    maskdga 面板检出进一步改善（K 的 maskdga FNR < D 的 0.0085）
    或 同检出下 FPR 更低  → 学习型攻击者在固定预算下有增量，方向 a 成立；
    否则 方向 a 在固定预算下不成立，登记负结果（不得改判据、不得换面板）。
  报告补充列：clean FPR、k2/krand 面板、bandit 诊断（编辑率／keep 占比／动作熵）。
  D 臂冻结读数（官方 24.2M，2026-09-10 滚动实验登记于 task_plan.md §5.6.2）：
    clean AP 0.99724 / clean FPR 0.02360 / maskdga FNR 0.00853。
  **数值参照为单次运行的登记读数（单种子），本轮不做统计显著性主张。**

与 MAB-Malware 的三处已知差异（必须随结论一起转述，不得冒充忠实复现）
  1. 本脚本**未实现动作最小化**（原文 §4.3 算法 2：删冗余动作＋宏动作拆微动作）。
     原文的精确 reward 归因依赖该过程；本脚本按任务书采用"位置级即时奖励"（同一变体内
     各位置共享该变体奖励），**信用分配精度低于原文**，可能把必要动作与冗余动作一起奖励。
  2. 本脚本**未实现成功 payload 池的跨样本复用**（原文 §3.2 洞察②）。价值表本身承载了
     跨样本复用（同一桶/字符的统计被所有域共享），但不复现"动作—内容对整池入池复用"。
  3. 原文是纯黑盒硬标签；本脚本使用连续分数 s(x̃) 计算形状奖励与组相对优势（白盒分数）。
     这使奖励信号严于原文设定（硬标签则形状项恒零、组相对过滤退化为二值）。
  以上任一差异都可能使 K 臂表现**低于**原文所能达到的水平，故本脚本的负结果只能支持
  "该最小实现无增量"，不构成"学习型攻击者在本问题上必然无增量"的一般结论。

位置桶口径（top/mid/tail 三段）
  bucket(i, L) = min(2, 3·i // L)，i 为 SLD 内 0 基位置，L 为 SLD 长度。
  实测边界（T17 dga train 前 3 万，SLD 长度 min 5 / max 43 / mean 16.09 / p99 34）：
  桶边界与文档描述对齐，短域名下三桶仍均有覆盖（L≥3 即三桶非空）。
  说明：任务书"位置桶 top/mid/tail 三桶"未固定边界口径，此为任务化实现选择（已登记）。

运行
  本机（MPS）：/opt/miniconda3/envs/rwkv/bin/python karm_bandit_p2p3.py --dry-run 200 --arms K
    （脚本自行 setdefault `PYTORCH_ENABLE_MPS_FALLBACK=1`，复现既有官方/代理运行的 MPS 配置；
      该变量的既有运行证据见同目录 official-p2p3-console.log 第 28 行 UserWarning）
  服务器（CUDA，正式全量由主代理调度）：
    source tools/env/activate.sh && P2P3_OUT=<输出目录> uv run --no-sync python karm_bandit_p2p3.py --arms K
  本脚本**不启动**全量 screening、不做多种子、不触碰 T19–T25（screening_only=true 口径）。
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

# MPS 兼容：候选变体批的 padding mask 会触发 nn.Transformer 的嵌套张量快速路径检查
# torch._nested_tensor_from_mask_left_aligned，该算子在 MPS 上未实现（本机实测 2026-09-11
# 复现 NotImplementedError）。既有官方/代理运行均以环境变量 PYTORCH_ENABLE_MPS_FALLBACK=1
# 运行（见 official-p2p3-console.log 第 28 行 UserWarning），此处显式复现同一运行配置。
# 须在 torch 导入前设置（backend 初始化时读取）；只影响该掩码对齐检查，不改前向数值语义。
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import numpy as np
import pyarrow.parquet as pq
import torch

from official_p2p3 import (  # 复用骨架：数据加载、编解码、模型加载、评价协议、算子、评价面板构造
    ALPHA,
    BATCH,
    CKPT,
    DATA,
    EVAL_BATCH,
    EPOCHS,
    LR_BACKBONE,
    LR_HEAD,
    OUT,
    REF,
    SEED,
    autocast_ctx,
    diag,
    load_split,
    metrics,
    official,
    perturb2,
    perturb_half,
)

# ---------------------------------------------------------------- 冻结判据常量
D_ARM_REF_MASKDGA_FNR = 0.0085   # D 臂冻结读数（task_plan §5.6.2），K 的对照基线
D_ARM_REF_CLEAN_FPR = 0.02360    # D 臂 clean FPR 冻结读数（"同检出下 FPR 更低"分支用）
D_ARM_REF_CLEAN_AP = 0.99724     # D 臂 clean AP 冻结读数（报告补充列）

# ------------------------------------------------------- 攻击者与训练超参（任务化设定）
K_VARIANTS = 4          # 每恶意样本变体数 K，与 D 臂一致（固定预算前提）
TOP_Q = 64              # 组相对过滤配额，与 D 臂一致
N_BUCKETS = 3           # 位置桶数：top/mid/tail
N_OPS = 2               # 操作类型数：0=保留(keep)、1=替换(replace)
GATE_INIT = 0.5         # 编辑门初值：中性 0.5，对应任务书"位置数 Bernoulli(0.5)"的探索口径
GATE_MIN = 0.05         # 编辑概率下界（熵塌缩防护：策略可学习到"少改"，但不能塌成全保留）
GATE_MAX = 0.95         # 编辑概率上界（同上：不能塌成全替换）
V_INIT = 0.5            # 字符价值表初值：中性先验（奖励恒正，零初值会让价值表单向漂移到饱和）
ETA_BANDIT = 0.05       # 任务化设定（无文献精确值）：bandit 学习率；MAB-Malware 为
                        #   Bayesian Beta 后验（Thompson 采样），无 η 这一步，故无直接文献依据
LAMBDA_SHAPE = 0.1      # 任务化设定（无文献精确值）：形状奖励权重，量级取 1/10 使
                        #   "未被骗"态的奖励落在 [0, 0.05]，严格小于"骗过"态（≥1.0），
                        #   保证二值项主导、形状项只做同态内排序（缓解 K=4 全 0 奖励的稀疏）
INIT_NOISE = 0.05       # V 初始化：小高斯（破对称），避免全零导致的固定初始偏好
MAX_SLD = 75            # 与官方 encode_char 的 75 字符截断对齐（超长域名的末段不参与攻击）


class StatelessBandit:
    """上下文无关 stateless bandit。两段式动作：先定"是否编辑"（编辑门），再定"换成哪个字符"。

    价值表形状：gate[N_BUCKETS]（编辑门 logit）＋ V[N_BUCKETS, N_OPS, len(ALPHA)]（字符价值表）。
    任务书写作 V[3, op_types, 40]；代码库既有 CharBot/MaskDGA 算子字符表为 37 字符
    （'a'-'z','0'-'9','-'，见 official_p2p3.ALPHA，与 E-A1 v2 同源），故实际为 [3, 2, 37]；
    「40」疑为任务书笔误。差异已登记，不擅自扩表（扩表会与既有面板算子不一致）。

    编辑门为何独立于 softmax 动作空间（设计决策，2026-09-11 本机实测修正）
      若按"每位置在 {keep}∪{36 种替换} 上做一次 softmax"，keep 仅 1 个 logit 对抗 36 个替换 logit，
      随机初始化下初始编辑率实测 0.979（远超任务书要求的 Bernoulli(0.5)），且该偏置结构性存在、
      无法被学习信号拉回，违反任务书"编辑位置数 Bernoulli(0.5)＋探索保留"。
      故改为两段式：编辑门直接给出编辑概率（初值 0.5），替换字符从 V[桶,1,·] 的 softmax 采样。
    门的更新空间（第二处实测修正）
      奖励 r∈[0,1.05] 与 logit 不同量纲；在 logit 空间做 V+=η(r−V) 会让门单向漂移到饱和
      （2026-09-11 实跑：单 epoch 编辑概率 0.44→0.72 并继续上升），与"熵塌缩防护"冲突。
      故门在概率空间更新并钳制到 [GATE_MIN, GATE_MAX]：策略可学"少改/多改"，但不会塌到两端。
    """

    def __init__(self, seed: int) -> None:
        rng = np.random.default_rng(seed)
        # 编辑门按**概率**存储并更新（不走 logit 空间）：奖励 r∈[0,1.05] 与 logit 不同量纲，
        # 在 logit 空间做 V += η(r−V) 会让门单向漂移到饱和（2026-09-11 本机实跑：一个 epoch 内
        # 编辑概率 0.44→0.72 并持续上升），违反任务书的熵塌缩防护。概率空间更新＋上下界钳制
        # 使策略仍可学习"少改/多改"，但不会塌成全保留或全替换。
        self.gate = np.full(N_BUCKETS, GATE_INIT, dtype=np.float64)
        self.V = np.full((N_BUCKETS, N_OPS, len(ALPHA)), V_INIT, dtype=np.float64)
        # 字符选择上的微小平局打破（不影响编辑门；全部 37 字符已被原字符排除逻辑限制）
        self.V[:, 1, :] += rng.normal(0.0, INIT_NOISE, size=(N_BUCKETS, len(ALPHA)))
        self.n_updates = 0            # 动作级更新次数（每动作每变体计一次）
        self.n_gate_updates = 0       # 编辑门更新次数（单独计数，便于核验更新语义）
        self.n_rewards = 0            # 奖励观测次数（每变体每样本计一次）
        self._bucket = self._build_bucket_index()

    @staticmethod
    def _build_bucket_index() -> np.ndarray:
        """预计算 bucket(i, L)：形状 [MAX_SLD+1, MAX_SLD]，第 L 行只用前 L 列。"""
        table = np.zeros((MAX_SLD + 1, MAX_SLD), dtype=np.int64)
        for length in range(1, MAX_SLD + 1):
            positions = np.arange(length)
            table[length, :length] = np.minimum(N_BUCKETS - 1, 3 * positions // length)
        return table

    def sample_positions(self, sld: str, rng: np.random.Generator) -> tuple[str, list[tuple[int, int, int]]]:
        """对 SLD 逐位置独立采样动作；返回 (变体域名字符串, 动作索引序列)。

        两段式采样（上下文无关、无状态——不依赖其他位置取值，也不依赖样本身份）：
          第一段：位置 i 以 σ(gate[bucket(i)]) 的伯努利概率决定"编辑与否"（keep=0 / 发起编辑）；
          第二段：发起编辑的位置，从 V[bucket(i), 1, ·] 上做 softmax 采样新字符（排除原字符，
                  "替换成原字符"属无效动作，被结构性排除）。
        动作索引为 (桶, 操作, 字符下标)：op=0 表示编辑门动作（cur=原字符下标），
        op=1 表示字符选择动作（cur=新字符下标）。
        """
        length = min(len(sld), MAX_SLD)
        buckets = self._bucket[length, :length]
        n_char = len(ALPHA)
        sld_idx = np.array([ALPHA.index(c) if c in ALPHA else -1 for c in sld[:length]], dtype=np.int64)
        # 第一段：编辑门（逐位置独立 Bernoulli，概率 = σ(gate[桶])）
        p_edit = self.gate[buckets]          # 逐位置编辑概率（桶内共享，无状态）
        will_edit = rng.random(length) < p_edit
        # 第二段：字符选择（仅对发起编辑的位置采样；排除原字符）
        all_idx = np.arange(n_char)[None, :]
        sel = np.repeat(all_idx, length, axis=0) != sld_idx[:, None]
        replace_ok = np.where(sel, all_idx, n_char)    # 原字符被顶到 n_char 处，切片时自动剔除
        replace_ok.sort(axis=1)
        n_ok = n_char - 1
        variant = list(sld[:length]) + list(sld[length:])   # 超长域名的尾部原样保留
        # 动作序列按位置索引落位（与 SLD 位置一一对应，便于逐位置奖励归因与核验）
        actions: list[tuple[int, int, int] | None] = [None] * length
        if will_edit.any():
            rows = np.flatnonzero(will_edit)
            cand = replace_ok[rows, :n_ok]                        # 形状 [n_edit, n_ok]
            logits = self.V[buckets[rows][:, None], 1, cand]      # 高级索引：形状 [n_edit, n_ok]
            logits = logits - logits.max(axis=1, keepdims=True)
            probs = np.exp(logits)
            probs /= probs.sum(axis=1, keepdims=True)
            cum = np.cumsum(probs, axis=1)
            pick = (cum < rng.random(len(rows))[:, None]).sum(axis=1).clip(0, n_ok - 1)
            for r, i in enumerate(rows):
                ch = int(cand[r, pick[r]])
                variant[i] = ALPHA[ch]
                actions[i] = (int(buckets[i]), 1, ch)
        for i in np.flatnonzero(~will_edit):
            cur = int(sld_idx[i]) if sld_idx[i] >= 0 else 0
            actions[i] = (int(buckets[i]), 0, cur)                 # 保留动作的"字符"= 原字符下标
        return "".join(variant), [a for a in actions if a is not None]

    def update(self, actions: list[tuple[int, int, int]], reward: float) -> None:
        """即时奖励更新（无折扣、无轨迹）：编辑门与字符表都按 V[a] += η(r − V[a]) 更新。

        编辑门在概率空间更新并钳制到 [GATE_MIN, GATE_MAX]；字符表在价值空间更新。
        """
        for (b, op, ch) in actions:
            if op == 0:
                p = self.gate[b] + ETA_BANDIT * (reward - self.gate[b])
                self.gate[b] = float(np.clip(p, GATE_MIN, GATE_MAX))
                self.n_gate_updates += 1
            else:
                self.V[b, op, ch] += ETA_BANDIT * (reward - self.V[b, op, ch])
            self.n_updates += 1
        self.n_rewards += 1

    def gate_probs(self) -> list:
        """当前编辑门的逐位置编辑概率，用于核验初始 0.5 附近与学习走向。"""
        return [float(v) for v in self.gate]

    def diagnostics(self) -> dict:
        """价值表维度与统计（验收要求 2：维度/更新次数打印）。"""
        return {
            "gate_shape": list(self.gate.shape),
            "V_shape": list(self.V.shape),
            "V_size": int(self.V.size),
            "n_params_total": int(self.V.size + self.gate.size),
            "n_updates": int(self.n_updates),
            "n_gate_updates": int(self.n_gate_updates),
            "n_rewards": int(self.n_rewards),
            "gate_edit_prob": self.gate_probs(),
            "V_mean_replace": float(self.V[:, 1, :].mean()),
            "V_mean_by_bucket": [float(self.V[b].mean()) for b in range(N_BUCKETS)],
            "V_min": float(self.V.min()),
            "V_max": float(self.V.max()),
        }


def _probe_edit_rate(bandit: StatelessBandit, body: str = "a1b2c3d4e5f6g7h8", n: int = 50) -> float:
    """初始策略的编辑率诊断（只读探针，不更新 V）：衡量随机初始化下的先验编辑倾向。"""
    rng = np.random.default_rng(12345)
    rates = [sum(1 for (_, op, _) in bandit.sample_positions(body, rng)[1] if op == 1) / len(body)
             for _ in range(n)]
    return float(np.mean(rates))


def _char_entropy(hist: dict[int, int]) -> float:
    """被选中新字符分布的香农熵（bit）：熵塌缩诊断——接近 0 表示策略退化为常量替换。"""
    total = sum(hist.values())
    if total == 0:
        return 0.0
    p = np.asarray([v / total for v in hist.values()])
    return float(-(p * np.log2(p)).sum())


def filter_top64(cands: list[str], owner: list[int], p_cand: np.ndarray) -> list[str]:
    """组相对过滤（与 D 臂逐行同构）：组内「fooled − 组均值」降序取 top-64 入批。"""
    fooled = (p_cand < 0.5).astype(np.float64)
    groups: dict[int, list[int]] = {}
    for j, o in enumerate(owner):
        groups.setdefault(o, []).append(j)
    scored: list[tuple[float, int]] = []
    for js in groups.values():
        f = fooled[js]
        adv_g = f - f.mean()
        scored.extend((float(adv_g[k]), j) for k, j in enumerate(js))
    scored.sort(key=lambda t: -t[0])
    return [cands[j] for _, j in scored[:TOP_Q]]


def score_candidates(model, tokenizer, domains_list: list[str]) -> np.ndarray:
    """用当前检测器对候选变体打连续分数（组相对过滤与 bandit 奖励共用一次前向）。"""
    model.eval()
    parts: list[np.ndarray] = []
    with torch.inference_mode():
        for off in range(0, len(domains_list), EVAL_BATCH):
            chunk = domains_list[off:off + EVAL_BATCH]
            tok = official.encode_subword(chunk, tokenizer).to(DEVICE)
            ch = official.encode_char(chunk).to(DEVICE)
            with autocast_ctx():
                tf, cf = diag.branch_features(model, tok, ch)
            logits2 = model.classifier_head(torch.cat([tf, cf], dim=1))
            parts.append(torch.softmax(logits2.float(), dim=1)[:, 1].cpu().numpy())
    return np.concatenate(parts)


def train_k_arm(train_d: list[str], train_y: np.ndarray, tokenizer, tok_mean, char_mean,
                eval_clean: tuple[list[str], np.ndarray], epochs: int) -> dict:
    """K 臂训练：每 batch 采样变体 → 组相对 top-64 → 检测器更新一步 → bandit 奖励更新。"""
    model = official.load_model(REF, CKPT, DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.Adam([
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" not in n_], "lr": LR_BACKBONE},
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" in n_], "lr": LR_HEAD},
    ])
    print(f"[K] 官方模型 {n_params} 参数，训练 {len(train_d)} 样本 × {epochs} epochs", file=sys.stderr, flush=True)
    bandit = StatelessBandit(seed=SEED + 11)
    rng = np.random.default_rng(SEED + 13)   # 变体采样随机流（策略外生噪声源）
    print(f"[K] bandit 参数：编辑门 {list(bandit.gate.shape)}（桶 {N_BUCKETS}，初值 {GATE_INIT}）"
          f"＋ 字符价值表 {list(bandit.V.shape)}（桶 {N_BUCKETS} × 操作 {N_OPS} × 字符 {len(ALPHA)}），"
          f"合计 {bandit.V.size + bandit.gate.size} 参数，η_bandit={ETA_BANDIT}，形状奖励系数 {LAMBDA_SHAPE}",
          file=sys.stderr, flush=True)
    init_edit = _probe_edit_rate(bandit)
    print(f"[K] 初始策略平均编辑率 = {init_edit:.3f}（应为 ~{GATE_INIT}：位置数 Bernoulli({GATE_INIT})）；"
          f"两段式采样：编辑门定是否编辑 → 字符表选新字符", file=sys.stderr, flush=True)
    ec, ey = eval_clean
    fpr_curve: list = []
    diag_epochs: list = []
    n = len(train_d)
    for ep in range(1, epochs + 1):
        model.train()
        order = list(range(n))
        random.Random(SEED + ep).shuffle(order)
        t0 = time.time()
        nb = (n + BATCH - 1) // BATCH
        # 逐 batch 诊断累加器（编辑率按"编辑位置数 / 总位置数"统计，分母是位置数不是批次数）
        acc_edit, acc_pos = 0, 0
        acc_r, acc_fooled, acc_ncand, acc_batches = 0.0, 0, 0, 0
        acc_char_hist: dict[int, int] = {}   # 被选中新字符的频次（熵塌缩诊断：是否塌成单一常量替换）
        for bi in range(nb):
            idx = order[bi * BATCH:(bi + 1) * BATCH]
            batch_d = [train_d[i] for i in idx]
            batch_y = train_y[idx]
            mal_idx = [i for i in idx if train_y[i] == 1]
            # (i) 用当前 π_φ 对每恶意样本独立采样 K 个变体（无缓存复用——策略在动）
            cands: list[str] = []
            owner: list[int] = []
            acts: list[list[tuple[int, int, int]]] = []
            for i in mal_idx:
                body = train_d[i].rsplit(".", 1)[0]
                for _ in range(K_VARIANTS):
                    variant, actions = bandit.sample_positions(body, rng)
                    cands.append(variant)
                    owner.append(i)
                    acts.append(actions)
            adv_batch: list[str] = []
            if cands:
                # (ii)+(iii) 一次前向：连续分数 → 组相对过滤 top-64（与 D 臂同构）
                p_cand = score_candidates(model, tokenizer, cands)
                adv_batch = filter_top64(cands, owner, p_cand)
                # (iv) bandit 即时奖励更新（无折扣、无轨迹；奖励用打分时的检测器状态）
                rewards = np.where(
                    p_cand < 0.5, 1.0, 0.0) + LAMBDA_SHAPE * np.clip(0.5 - p_cand, 0.0, None)
                for j, act in enumerate(acts):
                    bandit.update(act, float(rewards[j]))
                    acc_pos += len(act)
                    for (_, op, ch) in act:
                        if op == 1:
                            acc_edit += 1
                            acc_char_hist[ch] = acc_char_hist.get(ch, 0) + 1
                acc_r += float(rewards.mean())
                acc_fooled += int((p_cand < 0.5).sum())
                acc_ncand += len(cands)
                acc_batches += 1
                model.train()
            if adv_batch:
                # 检测器侧与 D 臂逐行同构：主样本 + top-64 变体（标签 1），MPS 128 子批梯度累积
                batch_d = batch_d + adv_batch
                batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            y_t = torch.from_numpy(batch_y).long().to(DEVICE)
            opt.zero_grad(set_to_none=True)
            loss_log = 0.0
            n_tot = len(batch_d)
            for s in range(0, n_tot, BATCH):
                sub_d = batch_d[s:s + BATCH]
                sub_y = y_t[s:s + BATCH]
                tok = official.encode_subword(sub_d, tokenizer).to(DEVICE)
                ch = official.encode_char(sub_d).to(DEVICE)
                with autocast_ctx():
                    tf, cf = diag.branch_features(model, tok, ch)
                    logits2 = model.classifier_head(torch.cat([tf, cf], dim=1))
                logits2 = logits2.float()
                loss_s = torch.nn.functional.cross_entropy(logits2, sub_y, reduction="sum") / n_tot
                loss_s.backward()
                loss_log += loss_s.item()
            opt.step()
            if bi % 20 == 0:
                eta = (time.time() - t0) / (bi + 1) * (nb - bi - 1)
                print(f"[K 心跳] epoch {ep} 批 {bi+1}/{nb} loss={loss_log:.4f} "
                      f"编辑率={acc_edit/max(acc_pos,1):.3f} 骗过率={acc_fooled/max(acc_ncand,1):.3f} "
                      f"动作更新={bandit.n_updates} ETA {eta/60:.1f} min", flush=True, file=sys.stderr)
        # 逐 epoch 干净 FPR 曲线（与 D 臂同规格，防瞬态误判）
        model.eval()
        fpr_now = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)["FPR"]
        fpr_curve.append({"epoch": ep, "clean_FPR": fpr_now})
        diag_epochs.append({
            "epoch": ep,
            "mean_edit_rate": acc_edit / max(acc_pos, 1),
            "mean_reward": acc_r / max(acc_batches, 1),
            "mean_fooled_rate": acc_fooled / max(acc_ncand, 1),
            "char_choice_entropy_bit": _char_entropy(acc_char_hist),
            "gate_edit_prob": bandit.gate_probs(),
            "n_updates_cum": bandit.n_updates,
            "n_gate_updates_cum": bandit.n_gate_updates,
        })
        print(f"[K 里程碑] epoch {ep}/{epochs} 完成，干净 FPR={fpr_now:.4f}，"
              f"平均编辑率={diag_epochs[-1]['mean_edit_rate']:.3f}，"
              f"字符选择熵={diag_epochs[-1]['char_choice_entropy_bit']:.2f} bit，"
              f"编辑概率={[round(v, 3) for v in bandit.gate_probs()]}，"
              f"bandit 动作更新累计={bandit.n_updates}（{time.time()-t0:.1f}s）", file=sys.stderr, flush=True)
    model.eval()
    clean = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)
    bd = bandit.diagnostics()
    print(f"[K bandit] 价值表 V 形状 {bd['V_shape']}（{bd['V_size']} 参数），"
          f"动作级更新 {bd['n_updates']} 次 / 奖励观测 {bd['n_rewards']} 次；"
          f"V 均值 replace={bd['V_mean_replace']:.4f}，"
          f"分桶均值={[round(v, 4) for v in bd['V_mean_by_bucket']]}", file=sys.stderr, flush=True)
    return {"clean": clean, "n_params": n_params, "fpr_curve": fpr_curve,
            "bandit": bd, "bandit_epochs": diag_epochs, "_model": model}


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "mps")


def main(dry: int = 0, arms_arg: str | None = None) -> None:
    torch.manual_seed(SEED); np.random.seed(SEED); random.seed(SEED)
    tokenizer = official.PreTrainedTokenizerFast(
        tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json")
    )
    tr_d, tr_y = load_split(dry if dry else 30000)
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_benign_val.parquet").to_pylist()[:(dry or 7500)]
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_dga_val.parquet").to_pylist()[:(dry or 7500)]
    ec = [str(r["domain"]) for r in tb] + [str(r["domain"]) for r in td]
    ey = np.asarray([0] * len(tb) + [1] * len(td), dtype=bool)
    rng = random.Random(SEED)
    # 评价面板与 official_p2p3 同序同种子生成，保证与 D 臂读数可比
    ea_k2 = [perturb2(str(r["domain"]), rng) for r in td[:(dry or 7500)]]
    ea_krand = [perturb2(str(r["domain"]), rng) for r in td[:(dry or 7500)]]
    ea_mask = [perturb_half(str(r["domain"]), rng) for r in td[:(dry or 7500)]]
    eval_clean = (ec, ey)
    adv_panels = {
        "k2": (ea_k2, np.ones(len(ea_k2), dtype=bool)),
        "krand": (ea_krand, np.ones(len(ea_krand), dtype=bool)),
        "maskdga": (ea_mask, np.ones(len(ea_mask), dtype=bool)),
    }
    print(f"[K 臂] 训练 {len(tr_d)}、评价干净 {len(ec)}、对抗 k2 {len(ea_k2)}/krand {len(ea_krand)}/maskdga {len(ea_mask)}；"
          f"判据对照 D 臂冻结 maskdga FNR={D_ARM_REF_MASKDGA_FNR}（同检出分支用 clean FPR={D_ARM_REF_CLEAN_FPR}）",
          file=sys.stderr, flush=True)

    cache = Path("/tmp/drift-anchor-t17-features-300000.npz")
    if cache.exists():
        z = np.load(cache)
        tok_mean = z["tok"].mean(axis=0, dtype=np.float64).astype(np.float32)
        char_mean = z["char"].mean(axis=0, dtype=np.float64).astype(np.float32)
    else:
        model0 = official.load_model(REF, CKPT, DEVICE)
        _tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_benign_val.parquet").to_pylist()
        _td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_dga_val.parquet").to_pylist()
        _dom = [str(r["domain"]) for r in _tb] + [str(r["domain"]) for r in _td]
        _tok, _char = diag.extract_features(model0, tokenizer, _dom, DEVICE, EVAL_BATCH)
        tok_mean = _tok.mean(axis=0, dtype=np.float64).astype(np.float32)
        char_mean = _char.mean(axis=0, dtype=np.float64).astype(np.float32)
        print(f"[均值] 缓存缺失，现场重算：{len(_dom)} 域", file=sys.stderr, flush=True)
        del model0, _tok, _char

    arms = tuple(arms_arg.split(",")) if arms_arg else ("K",)
    epochs = 1 if dry else EPOCHS
    assert set(arms) <= {"K"}, f"本脚本只实现 K 臂，收到 {arms}"
    results: dict = {}
    for arm in arms:
        t0 = time.time()
        r = train_k_arm(tr_d, tr_y, tokenizer, tok_mean, char_mean, eval_clean, epochs)
        r["wall_seconds"] = round(time.time() - t0, 1)
        arm_model = r.pop("_model")
        results[arm] = r
        for pname, (pa, pay) in adv_panels.items():
            results[arm][f"adv_{pname}"] = metrics(arm_model, tokenizer, pa, pay, tok_mean, char_mean)
        print(f"[K 里程碑] {arm}: clean={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['clean'].items()})} "
              f"maskdga={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['adv_maskdga'].items()})}",
              file=sys.stderr, flush=True)

    mask = results["K"]["adv_maskdga"]
    clean_fpr = results["K"]["clean"]["FPR"]
    verdict = {
        "criterion_version": "v1（K vs D 同 screening 规格，冻结于脚本 docstring）",
        "D_arm_ref": {"maskdga_FNR": D_ARM_REF_MASKDGA_FNR, "clean_FPR": D_ARM_REF_CLEAN_FPR,
                      "clean_AP": D_ARM_REF_CLEAN_AP, "source": "task_plan.md §5.6.2 官方 24.2M 滚动实验登记"},
        "K_arm": {"maskdga_FNR": round(mask["FNR"], 5), "clean_FPR": round(clean_fpr, 5),
                  "clean_AP": round(results["K"]["clean"]["AP"], 5)},
        "branch_detection_improve": bool(mask["FNR"] < D_ARM_REF_MASKDGA_FNR),
        "branch_same_detection_lower_fpr": bool(
            abs(mask["FNR"] - D_ARM_REF_MASKDGA_FNR) <= 0.005 and clean_fpr < D_ARM_REF_CLEAN_FPR),
        "direction_a_pass": bool(mask["FNR"] < D_ARM_REF_MASKDGA_FNR or (
            abs(mask["FNR"] - D_ARM_REF_MASKDGA_FNR) <= 0.005 and clean_fpr < D_ARM_REF_CLEAN_FPR)),
        "note": ("方向 a 成立（学习策略有增量）" if (mask["FNR"] < D_ARM_REF_MASKDGA_FNR or (
            abs(mask["FNR"] - D_ARM_REF_MASKDGA_FNR) <= 0.005 and clean_fpr < D_ARM_REF_CLEAN_FPR))
            else "方向 a 在固定预算下不成立（登记负结果，不得改判据或换面板）"),
        "dry_run_samples": dry,
    }
    out_name = "karm-bandit-p2p3-DRYRUN.json" if dry else "karm-bandit-p2p3-result.json"
    (OUT / out_name).write_text(json.dumps({"results": results, "verdict": verdict}, ensure_ascii=False, indent=2),
                                encoding="utf-8")
    print(f"[K 里程碑] 判据（dry-run 样本 {dry}，仅供参考，不作裁决）: {json.dumps(verdict['K_arm'], ensure_ascii=False)} "
          f"-> {out_name}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=0, help="训练/评价样本数上限，0 为全量")
    ap.add_argument("--arms", default=None, help="本脚本只实现 K 臂；默认 K")
    a = ap.parse_args()
    main(dry=a.dry_run, arms_arg=a.arms)
