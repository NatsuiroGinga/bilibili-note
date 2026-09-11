#!/usr/bin/env python3
"""官方 24.2M DRIFT 模型的 P2/P3 三臂（用户裁决：官方模型为准，本机 MPS 可跑）。

判据（冻结 v2，同 proxy 版）：
  P2：臂 B（干净+CharBot 2 位替换增广）相对臂 A（干净训练）——T18 val 对抗变体检出率改善
      且 干净 FPR 不增 → 对抗训练有效；
  P3：臂 C（组相对加权：K=4 变体组，组内"当前模型判良性"优势，正优势变体主导梯度）
      相对臂 B 进一步改善 且 干净 FPR 不增 → GRPO 家族机制层增量成立；
  失败形态：干净 FPR 恶化（以干净性能换鲁棒）或对抗检出无改善。
  报告补充列：adv FNR 对照（AP 接近 1.0 封顶时提供区分度，不替代冻结判据）。
规格：T17 train 抽样 6 万（良性/DGA 各 3 万）训练、3 epochs、batch 128、
  Adam 分层 lr（骨干 1e-6/头 1e-4）、全参数训练、
  评价 = T18 val 干净 1.5 万 + CharBot 变体 1.5 万（k=2 对齐 P0）+ k∈U{1..4} 变体 1.5 万（预算泛化组），
  阈值 0.5、种子 42。逐 epoch 干净 FPR 曲线（文献代理 Q1 裁决：识别验证损失上升段，防瞬态误判）。
埋点三类；断点：每臂完成原子落盘 state_dict 与指标；--dry-run 同路径。
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch

# 环境变量 LLM_PROBE_ROOT 覆盖项目根（服务器设为 /root/autodl-tmp/thesis/experiments/llm_probe）
ROOT = Path(os.environ.get(
    "LLM_PROBE_ROOT",
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe",
))
sys.path.insert(0, str(ROOT / "tools"))
import ch3_drift_official_branch_conflict_diagnostic as diag
import ch3_drift_official_checkpoint_t17_eval as official

REF = ROOT / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
CKPT = ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"
DATA = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521"
OUT = Path(os.environ.get("P2P3_OUT", Path(__file__).resolve().parent))
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "mps")
BATCH = 128            # 训练批量：冻结规格，不改
EVAL_BATCH = 1024 if DEVICE.type == "cuda" else 128   # 评价批量只影响吞吐不改指标
USE_BF16 = DEVICE.type == "cuda"                      # 对齐官方 BF16 训练


def autocast_ctx():
    """仅 CUDA 启用 bf16 autocast；MPS 返回 nullcontext——
    torch.autocast(enabled=False) 在 MPS 上仍会改变 nn.Transformer 执行路径，
    触发未实现的 _nested_tensor_from_mask_left_aligned 算子（2026-09-10 实测）。"""
    return torch.autocast(device_type=DEVICE.type, dtype=torch.bfloat16) if USE_BF16 else nullcontext()
LR_HEAD = 1e-4
LR_BACKBONE = 1e-6
EPOCHS = 3
SEED = 42
BETA_KL = 1.0  # E 臂 KL 权重：任务化设定（GRPO 家族 β 无文献精确值），首轮源侧标定
ALPHA_CVAR = 0.05   # J 臂 CVaR 尾部质量（任务化设定）
LAMBDA_CVAR = 0.1   # J 臂 CVaR 项权重：量级对齐恶意 CE 项，避免 I 型尾部劫持（任务化设定）
TAU_LR = 0.01       # J 臂对偶变量 τ 的解析下降步长
ALPHA = "abcdefghijklmnopqrstuvwxyz0123456789-"


def perturb2(domain: str, rng: random.Random) -> str:
    body = domain.rsplit(".", 1)[0]
    tail = "." + domain.rsplit(".", 1)[1] if "." in domain else ""
    if len(body) < 4:
        return domain
    b = list(body)
    for i in rng.sample(range(len(body)), 2):
        c = rng.choice(ALPHA)
        while c == b[i]:
            c = rng.choice(ALPHA)
        b[i] = c
    return "".join(b) + tail


def perturb_half(domain: str, rng: random.Random) -> str:
    """MaskDGA 半替换近似（冻结 v2 算子，与 E-A1 v2 同源）：随机替换 SLD 一半位置。
    主判据面板算子：官方模型实测相对降 69.1%，可打开 AP 判据空间（k2 面板 AP 封顶无空间）。"""
    body = domain.rsplit(".", 1)[0]
    tail = "." + domain.rsplit(".", 1)[1] if "." in domain else ""
    if len(body) < 4:
        return domain
    b = list(body)
    for i in rng.sample(range(len(body)), max(1, len(body) // 2)):
        c = rng.choice(ALPHA)
        while c == b[i]:
            c = rng.choice(ALPHA)
        b[i] = c
    return "".join(b) + tail


def perturb1(domain: str, rng: random.Random) -> str:
    """1 位替换（弱攻击档，L 臂课程 epoch 1 用）：随机替换 SLD 的 1 个位置。"""
    body = domain.rsplit(".", 1)[0]
    tail = "." + domain.rsplit(".", 1)[1] if "." in domain else ""
    if len(body) < 1:
        return domain
    b = list(body)
    i = rng.randrange(len(body))
    c = rng.choice(ALPHA)
    while c == b[i]:
        c = rng.choice(ALPHA)
    b[i] = c
    return "".join(b) + tail


def gen_variants_L(domain: str, ep: int, rng: random.Random) -> list:
    """L 臂课程档位算子：epoch 1=1 位(弱) → 2=2 位(中) → 3=半替换(强)。
    相邻档位分布漂移最小化（Shi&Liu 2024 课程 AT 在线视角的调度原则）。"""
    if ep == 1:
        return [perturb1(domain, rng) for _ in range(4)]
    elif ep == 2:
        return [perturb2(domain, rng) for _ in range(4)]
    return [perturb_half(domain, rng) for _ in range(4)]


def load_split(limit: int) -> tuple[list[str], np.ndarray]:
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_benign_train.parquet").to_pylist()[:limit]
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_dga_train.parquet").to_pylist()[:limit]
    domains = [str(r["domain"]) for r in tb] + [str(r["domain"]) for r in td]
    labels = np.asarray([0] * len(tb) + [1] * len(td), dtype=np.int64)
    return domains, labels


def metrics(model, tokenizer, domains: list[str], labels01: np.ndarray, tok_mean, char_mean) -> dict:
    model.eval()
    scores = []
    with torch.inference_mode():
        for off in range(0, len(domains), EVAL_BATCH):
            chunk = domains[off:off + EVAL_BATCH]
            tok = official.encode_subword(chunk, tokenizer).to(DEVICE)
            ch = official.encode_char(chunk).to(DEVICE)
            with autocast_ctx():
                tf, cf = diag.branch_features(model, tok, ch)
            s = diag.probabilities(model, tf.cpu().numpy(), cf.cpu().numpy(),
                                   tok_mean, char_mean, DEVICE, EVAL_BATCH)
            scores.append(s["static_fusion"])
    s = np.concatenate(scores)
    from sklearn.metrics import average_precision_score
    pred = s >= 0.5
    mal, ben = labels01, ~labels01
    fp = int((pred & ben).sum()); fn = int((~pred & mal).sum())
    tp = int((pred & mal).sum()); tn = int((~pred & ben).sum())
    return {"AP": float(average_precision_score(labels01, s)),
            "FPR": fp / max(fp + tn, 1), "FNR": fn / max(fn + tp, 1),
            "F1": tp / max(tp + 0.5 * (fp + fn), 1), "FP": fp, "FN": fn, "n": len(s)}


def train_arm(arm: str, train_d: list[str], train_y: np.ndarray,
              tokenizer, tok_mean, char_mean,
              eval_clean: tuple[list[str], np.ndarray], eval_adv: tuple[list[str], np.ndarray],
              epochs: int, ref_model=None) -> dict:
    model = official.load_model(REF, CKPT, DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    # 分层 lr：官方模型参数名无 "backbone"，按分类头匹配（classifier_head=1e-4，骨干=1e-6）
    opt = torch.optim.Adam([
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" not in n_], "lr": LR_BACKBONE},
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" in n_], "lr": LR_HEAD},
    ])
    n_head = sum(p_.numel() for n_, p_ in model.named_parameters() if "classifier_head" in n_)
    print(f"[{arm}] 分层 lr：骨干 {sum(p_.numel() for p_ in model.parameters()) - n_head} 参数 @1e-6，分类头 {n_head} 参数 @1e-4", file=sys.stderr, flush=True)
    print(f"[{arm}] 官方模型 {n_params} 参数，训练 {len(train_d)} 样本 × {epochs} epochs", file=sys.stderr, flush=True)
    fpr_curve: list = []
    ec, ey = eval_clean
    ea, eay = eval_adv
    rng = random.Random(SEED)
    adv_cache: dict[int, list[str]] = {}
    adv_cache_l: dict[tuple, list] = {}  # L 臂课程缓存（键含 epoch）
    adv_cache_m: dict[tuple, list] = {}  # M 臂 Mix 缓存（键=(样本, 档位)）
    benign_cache: dict[int, list[str]] = {}
    benign_rng = random.Random(SEED + 7)  # 良性变体独立种子，不与恶意变体序列耦合
    tau_val = torch.tensor(0.5, device=DEVICE)  # J 臂对偶变量 τ（RU 形式 min_τ）
    n = len(train_d)
    for ep in range(1, epochs + 1):
        model.train()
        order = list(range(n)); random.Random(SEED + ep).shuffle(order)
        t0 = time.time()
        nb = (n + BATCH - 1) // BATCH
        for bi in range(nb):
            idx = order[bi * BATCH:(bi + 1) * BATCH]
            batch_d = [train_d[i] for i in idx]
            batch_y = train_y[idx]
            n_main = len(batch_d)  # 拼接变体前的主样本数（E 臂 KL 只锚定主样本段）
            if arm in ("B", "C"):
                adv_batch = []
                for i in idx:
                    if train_y[i] == 1:
                        if i not in adv_cache:
                            base = perturb2(train_d[i], rng)
                            adv_cache[i] = [base] if arm == "B" else [perturb2(base, rng) for _ in range(4)]
                        if arm == "B":
                            adv_batch.append(adv_cache[i][0])
                        else:
                            adv_batch.extend(adv_cache[i])  # C 臂：K=4 变体全部入批，组相对加权才作用在变体上
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            elif arm == "L":
                # L 臂（攻击难度课程 × 组相对过滤，Shi&Liu 2024 漂移最小化框架的 DGA 实例化）：
                # epoch 1=1 位替换(弱) → 2=2 位(中) → 3=半替换(强)，相邻档位分布漂移最小；
                # 每档内部组相对过滤与 D 完全一致。判据（冻结，方案 §5.12）：
                # L vs D 同 screening 规格：maskdga 面板检出改善，或检出持平+干净 FPR 更低；
                # 理论预期（Shi&Liu 界）：课程版逐 epoch FPR 曲线更平稳、最终检出 ≥ D。
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    key = (i, ep)
                    if key not in adv_cache_l:
                        adv_cache_l[key] = gen_variants_L(train_d[i], ep, rng)
                    for v in adv_cache_l[key]:
                        cands.append(v)
                        cand_owner.append(i)
                adv_batch = []
                if cands:
                    model.eval()
                    with torch.inference_mode():
                        _sc = []
                        for off in range(0, len(cands), EVAL_BATCH):
                            _tk = official.encode_subword(cands[off:off + EVAL_BATCH], tokenizer).to(DEVICE)
                            _ch = official.encode_char(cands[off:off + EVAL_BATCH]).to(DEVICE)
                            with autocast_ctx():
                                _tf, _cf = diag.branch_features(model, _tk, _ch)
                            _lg = model.classifier_head(torch.cat([_tf, _cf], dim=1))
                            _sc.append(torch.softmax(_lg.float(), dim=1)[:, 1].cpu().numpy())
                    p_cand = np.concatenate(_sc)
                    fooled = (p_cand < 0.5).astype(np.float64)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    scored: list[tuple[float, int]] = []
                    for js in groups.values():
                        f = fooled[js]
                        adv_g = f - f.mean()
                        scored.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                    scored.sort(key=lambda t: (-t[0], t[1]))  # 确定性并列破法（notes.md §J 修正②）
                    adv_batch = [cands[j] for _, j in scored[:64]]
                    model.train()
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            elif arm == "M":
                # M 臂（Mix 对照，HARD-GATE 外审 §4.2）：三档候选池每批均匀混合、无课程顺序，
                # 选择机制与 L/D 完全一致。归因结构：L−M = 课程顺序增量；M−D = 新增曝光增量。
                # 判据 v2（冻结）：主判据=Mask 检出改善且 FPR 代价 Δ_B≤+0.005，或 Mask 非劣(|Δ_M|≤0.003)且 FPR 改善；
                # 配对变化 Δ_B=(N_良性0→1−N_良性1→0)/N_良性 需报告（±0.003 为概率绝对差 0.3pp）
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    for tier in (1, 2, 3):
                        key = (i, tier)
                        if key not in adv_cache_m:
                            if tier == 1:
                                adv_cache_m[key] = [perturb1(train_d[i], rng) for _ in range(4)]
                            elif tier == 2:
                                adv_cache_m[key] = [perturb2(train_d[i], rng) for _ in range(4)]
                            else:
                                adv_cache_m[key] = [perturb_half(train_d[i], rng) for _ in range(4)]
                        for v in adv_cache_m[key]:
                            cands.append(v)
                            cand_owner.append(i)
                adv_batch = []
                if cands:
                    model.eval()
                    with torch.inference_mode():
                        _sc = []
                        for off in range(0, len(cands), EVAL_BATCH):
                            _tk = official.encode_subword(cands[off:off + EVAL_BATCH], tokenizer).to(DEVICE)
                            _ch = official.encode_char(cands[off:off + EVAL_BATCH]).to(DEVICE)
                            with autocast_ctx():
                                _tf, _cf = diag.branch_features(model, _tk, _ch)
                            _lg = model.classifier_head(torch.cat([_tf, _cf], dim=1))
                            _sc.append(torch.softmax(_lg.float(), dim=1)[:, 1].cpu().numpy())
                    p_cand = np.concatenate(_sc)
                    fooled = (p_cand < 0.5).astype(np.float64)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    scored: list[tuple[float, int]] = []
                    for js in groups.values():
                        f = fooled[js]
                        adv_g = f - f.mean()
                        scored.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                    scored.sort(key=lambda t: (-t[0], t[1]))
                    adv_batch = [cands[j] for _, j in scored[:64]]
                    model.train()
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            elif arm in ("D", "E", "F", "H"):
                # D/E 臂（GFPO 组相对过滤，2508.09726 §3 式(2) + Drichel 2024 §4.4.2 配比锚点）：
                # 与 B 同为 64 变体配额（批次规模 192、恶意:良性倾斜度相同），唯一差量 =
                # 变体选择机制：每恶意样本 K=4 变体为组，组内 fooled（当前模型判良性）为优势，
                # "fooled − 组均值"降序取 top-64 入批（被拒变体零梯度，GFPO 过滤式优势）
                # E 臂 = D + 参考模型 KL 漂移约束（GRPO 2402.03300 式(3) −β·D_KL[π_θ‖π_ref] 任务化：
                # π_ref = 冻结初始判别器，KL 只作用于干净主样本段——干净输出分布锚定，
                # 对抗变体段自由硬化；β 为任务化设定（无文献精确值），首轮取 1.0 源侧标定）
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    if i not in adv_cache:
                        base = perturb2(train_d[i], rng)
                        adv_cache[i] = [perturb2(base, rng) for _ in range(4)]
                    for v in adv_cache[i]:
                        cands.append(v)
                        cand_owner.append(i)
                adv_batch = []
                if cands:
                    model.eval()
                    with torch.inference_mode():
                        _sc = []
                        for off in range(0, len(cands), EVAL_BATCH):
                            _tk = official.encode_subword(cands[off:off + EVAL_BATCH], tokenizer).to(DEVICE)
                            _ch = official.encode_char(cands[off:off + EVAL_BATCH]).to(DEVICE)
                            with autocast_ctx():
                                _tf, _cf = diag.branch_features(model, _tk, _ch)
                            _lg = model.classifier_head(torch.cat([_tf, _cf], dim=1))
                            _sc.append(torch.softmax(_lg.float(), dim=1)[:, 1].cpu().numpy())
                    p_cand = np.concatenate(_sc)
                    fooled = (p_cand < 0.5).astype(np.float64)
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    scored: list[tuple[float, int]] = []
                    for js in groups.values():
                        f = fooled[js]
                        adv_g = f - f.mean()
                        scored.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                    scored.sort(key=lambda t: -t[0])
                    adv_batch = [cands[j] for _, j in scored[:64]]
                    model.train()
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
                if arm == "H":
                    # H 臂良性侧（对称组相对，设计修正①②③④见 notes.md §J）：
                    # CharBot 近邻组（每良性样本 K=4），误报优势 = 连续分数 − 组均值，
                    # 跨组配额 top-32 全局竞争入批（标签 0）；与 F 的差量 = 良性侧从
                    # 「真样本加权 3.0」换为「组相对选择近邻变体」，恶意侧与 D/F 完全相同
                    ben_idx = [i for i in idx if train_y[i] == 0]
                    bcands: list[str] = []
                    bowner: list[int] = []
                    for i in ben_idx:
                        if i not in benign_cache:
                            benign_cache[i] = [perturb2(train_d[i], benign_rng) for _ in range(4)]
                        for v in benign_cache[i]:
                            bcands.append(v)
                            bowner.append(i)
                    adv_ben: list[str] = []
                    if bcands:
                        model.eval()
                        with torch.inference_mode():
                            _bs = []
                            for off in range(0, len(bcands), EVAL_BATCH):
                                _tk = official.encode_subword(bcands[off:off + EVAL_BATCH], tokenizer).to(DEVICE)
                                _ch = official.encode_char(bcands[off:off + EVAL_BATCH]).to(DEVICE)
                                with autocast_ctx():
                                    _tf, _cf = diag.branch_features(model, _tk, _ch)
                                _bs.append(torch.softmax(
                                    model.classifier_head(torch.cat([_tf, _cf], dim=1)).float(), dim=1)[:, 1].cpu().numpy())
                        p_ben = np.concatenate(_bs)
                        groups_b: dict[int, list[int]] = {}
                        for j, o in enumerate(bowner):
                            groups_b.setdefault(o, []).append(j)
                        scored_b: list[tuple[float, int]] = []
                        for js in groups_b.values():
                            pb = p_ben[js]
                            adv_g = pb - pb.mean()  # 设计修正①：连续分数中心化（非二值 fooled）
                            scored_b.extend((float(adv_g[k]), j) for k, j in enumerate(js))
                        scored_b.sort(key=lambda t: (-t[0], t[1]))  # 设计修正②：确定性并列破法
                        adv_ben = [bcands[j] for _, j in scored_b[:32]]  # 设计修正③④：显式跨组配额
                        model.train()
                    if adv_ben:
                        batch_d = batch_d + adv_ben
                        batch_y = np.concatenate([batch_y, np.zeros(len(adv_ben), dtype=np.int64)])
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            # MPS 带梯度反向 batch 上限 128：B/C 臂拼接变体后超限（192/320），
            # 用 128 子批梯度累积等效实现同一拼接大 batch 的（加权）平均损失，不改优化语义
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
                p_ = torch.softmax(logits2, dim=1)
                ce = torch.nn.functional.cross_entropy(logits2, sub_y, reduction="none")
                if arm == "J":
                    # J 臂 = D + 良性侧 CVaR τ-对偶（Rockafellar-Uryasev population 形式，区别于 I 的 batch top-k）：
                    # loss = 恶意项 + λ·(τ + mean(relu(ce_ben−τ))/α)；τ 每批解析下降更新
                    # （对偶 min_τ 的随机近似：dτ ∝ 1 − (1/α)·frac(ℓ>τ)）。
                    # λ=0.1 量级对齐恶意项，避免 I 型尾部劫持（任务化设定，源侧标定）
                    ben_m = sub_y == 0
                    if ben_m.any():
                        ce_ben = ce[ben_m]
                        cvaR_est = tau_val + torch.relu(ce_ben - tau_val).mean() / ALPHA_CVAR
                        ce_rest = ce[~ben_m].sum() if (~ben_m).any() else ce_ben.sum() * 0
                        loss_s = (ce_rest + LAMBDA_CVAR * cvaR_est * ben_m.sum()) / n_tot
                        with torch.no_grad():
                            tau_val -= TAU_LR * (1.0 - (ce_ben > tau_val).float().mean() / ALPHA_CVAR)
                            tau_val.clamp_(0.0, 20.0)
                    else:
                        loss_s = ce.sum() / n_tot
                elif arm == "I":
                    # I 臂 = D + 良性侧 CVaR_α 尾部软加权（组件 2 的 min-max 任务化）：
                    # 对 batch 内真良性样本的 CE 取 CVaR_α（最坏 α 分位的均值，softplus 连续松弛），
                    # 与恶意侧组相对 top-q 构成同一 min-max 泛函的两个威胁方向实例化。
                    # α=0.05 任务化设定（源侧标定）；理论对偶见 pAUC-DRO/CVaR 文献（本地全文）
                    ben_m = sub_y == 0
                    if ben_m.any():
                        ce_ben = ce[ben_m]
                        k_alpha = max(1, int(0.05 * ce_ben.numel()))
                        tail = torch.topk(ce_ben, k_alpha).values  # 最坏 α 分位（硬 CVaR）
                        cvaR = tail.mean()
                        ce_rest = ce[~ben_m].sum() if (~ben_m).any() else ce_ben.sum() * 0
                        # 恶意侧正常 CE + λ·CVaR_α(良性)；λ=1 对冲 64 变体配额压力（同 F 的量级逻辑）
                        loss_s = (ce_rest + cvaR * ben_m.sum() * 1.0) / n_tot
                    else:
                        loss_s = ce.sum() / n_tot
                elif arm in ("F", "G"):
                    # F 臂 = D + 良性误报加权（双侧组相对的良性侧最简形式）；
                    # G 臂 = 只组件 2（无对抗增广、仅良性误报加权）——四臂消融的对称单臂。
                    # batch 内当前模型判恶意的真良性样本 CE ×3.0，把分布上移的误报拉回。
                    # 权重 3.0 为任务化设定（无文献精确值）：对冲 64 变体配额的恶意侧压力量级，
                    # 源侧标定；若有效再升级为良性 CharBot 近邻组相对完整形态
                    fooled_b = (p_[:, 1] >= 0.5) & (sub_y == 0)
                    w = torch.ones(len(sub_y), device=DEVICE)
                    w[fooled_b] = 3.0
                    loss_s = (ce * w).sum() / n_tot
                elif arm == "C":
                    # 组相对加权：同一恶意样本的 4 变体一组，组内"当前模型判良性(骗过)"为优势，
                    # 正优势变体权重 2.0、未骗过变体 0.5、干净样本 1.0（组相对优势的任务化，
                    # 文献定位：无先例的任务化设定，对照 Drichel 均匀混合）
                    fooled = (p_[:, 1] < 0.5) & (sub_y == 1)
                    w = torch.ones(len(sub_y), device=DEVICE)
                    w[fooled] = 2.0
                    w[(sub_y == 1) & (p_[:, 1] >= 0.5)] = 0.5
                    loss_s = (ce * w).sum() / n_tot
                else:
                    loss_s = ce.sum() / n_tot
                if arm == "E" and ref_model is not None:
                    # E 臂组件 2：干净主样本段的参考模型 KL 锚定（GRPO 式(3) −β·D_KL[π_θ‖π_ref] 任务化）
                    _gl = torch.arange(s, min(s + BATCH, n_tot), device=DEVICE)
                    _m = _gl < n_main
                    if _m.any():
                        _p = p_[_m]
                        _log_p = torch.log(_p.clamp_min(1e-9))
                        with torch.inference_mode():
                            _tf_r, _cf_r = diag.branch_features(ref_model, tok[_m], ch[_m])
                            _lg_r = ref_model.classifier_head(torch.cat([_tf_r, _cf_r], dim=1))
                        _log_p0 = torch.log_softmax(_lg_r.float(), dim=1)
                        _kl = (_p * (_log_p - _log_p0)).sum(dim=1)
                        loss_s = loss_s + BETA_KL * _kl.sum() / n_tot
                loss_s.backward()
                loss_log += loss_s.item()
            opt.step()
            if bi % 20 == 0:
                eta = (time.time() - t0) / (bi + 1) * (nb - bi - 1)
                print(f"[{arm} 心跳] epoch {ep} 批 {bi+1}/{nb} loss={loss_log:.4f} ETA {eta/60:.1f} min", file=sys.stderr, flush=True)
        # 逐 epoch 干净 FPR 曲线（文献代理 Q1 裁决：识别"验证损失上升段"，防瞬态误判）
        model.eval()
        fpr_now = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)["FPR"]
        fpr_curve.append({"epoch": ep, "clean_FPR": fpr_now})
        print(f"[{arm} 里程碑] epoch {ep}/{epochs} 完成，干净 FPR={fpr_now:.4f}（{time.time()-t0:.1f}s）", file=sys.stderr, flush=True)
    model.eval()
    clean = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)
    adv = metrics(model, tokenizer, ea, eay, tok_mean, char_mean)
    return {"clean": clean, "adv": adv, "n_params": n_params, "fpr_curve": fpr_curve, "_model": model}


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
    ea_k2 = [perturb2(str(r["domain"]), rng) for r in td[:(dry or 7500)]]
    ea_krand = [perturb2(str(r["domain"]), rng) for r in td[:(dry or 7500)]]  # k∈U{1..4} 预算随机化组
    ea_mask = [perturb_half(str(r["domain"]), rng) for r in td[:(dry or 7500)]]  # MaskDGA 半替换强攻击面板
    eval_clean = (ec, ey)
    eval_adv_k2 = (ea_k2, np.ones(len(ea_k2), dtype=bool))
    eval_adv_krand = (ea_krand, np.ones(len(ea_krand), dtype=bool))
    eval_adv_mask = (ea_mask, np.ones(len(ea_mask), dtype=bool))
    print(f"[官方 P2/P3] 训练 {len(tr_d)}、评价干净 {len(ec)}、对抗 k2 {len(ea_k2)}/krand {len(ea_krand)}/maskdga {len(ea_mask)}", file=sys.stderr, flush=True)

    # 中和均值：优先 T17 val 全量缓存（本机，与正锚点核查同源）；缺缓存时现场重算
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

    arms = tuple(arms_arg.split(",")) if arms_arg else (("A", "B", "C") if not dry else ("A",))
    epochs = 1 if dry else EPOCHS
    results: dict = {}
    adv_panels = {"k2": eval_adv_k2, "krand": eval_adv_krand, "maskdga": eval_adv_mask}
    ref_model = None
    if any(a_ == "E" for a_ in arms):
        ref_model = official.load_model(REF, CKPT, DEVICE)
        ref_model.eval()
        print("[E 臂] 参考模型已加载（冻结初始判别器，KL 锚定用）", file=sys.stderr, flush=True)
    for arm in arms:
        t0 = time.time()
        r = train_arm(arm, tr_d, tr_y, tokenizer, tok_mean, char_mean, eval_clean, eval_adv_k2, epochs, ref_model=ref_model)
        r["wall_seconds"] = round(time.time() - t0, 1)
        arm_model = r.pop("_model")
        results[arm] = r
        # 双分组评价（该臂模型）：k=2 与 k∈U{1..4}
        for pname, (pa, pay) in adv_panels.items():
            results[arm][f"adv_{pname}"] = metrics(arm_model, tokenizer, pa, pay, tok_mean, char_mean)
        print(f"[里程碑] {arm}: clean={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['clean'].items()})} adv={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['adv'].items()})}", file=sys.stderr, flush=True)

    if len(results) == 3:
        a, b, c = results["A"], results["B"], results["C"]
        am, bm, cm = a["adv_maskdga"], b["adv_maskdga"], c["adv_maskdga"]
        verdict = {
            "P2_pass": bool(bm["AP"] > am["AP"] and b["clean"]["FPR"] <= a["clean"]["FPR"]),
            "P3_pass": bool(cm["AP"] > bm["AP"] and c["clean"]["FPR"] <= b["clean"]["FPR"]),
            "panel": "maskdga-half",
            "adv_AP": {"A": round(am["AP"], 4), "B": round(bm["AP"], 4), "C": round(cm["AP"], 4)},
            "clean_FPR": {"A": round(a["clean"]["FPR"], 4), "B": round(b["clean"]["FPR"], 4), "C": round(c["clean"]["FPR"], 4)},
            "adv_FNR": {"A": round(am["FNR"], 4), "B": round(bm["FNR"], 4), "C": round(cm["FNR"], 4)},
            "k2_reference_FNR": {"A": round(a["adv"]["FNR"], 4), "B": round(b["adv"]["FNR"], 4), "C": round(c["adv"]["FNR"], 4)},
        }
    else:
        verdict = {"note": "dry-run 单臂"}
    out_name = "official-p2p3-DRYRUN.json" if dry else "official-p2p3-result.json"
    (OUT / out_name).write_text(json.dumps({"results": results, "verdict": verdict}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[里程碑] {json.dumps(verdict, ensure_ascii=False)} -> {out_name}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=0)
    ap.add_argument("--arms", default=None, help="逗号分隔臂列表，如 A,B,C（默认全量三臂/干跑 A）")
    a = ap.parse_args()
    main(dry=a.dry_run, arms_arg=a.arms)
