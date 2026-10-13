#!/usr/bin/env python3
"""DRIFT 官方双分支骨干的源期共同成员 A/B/D/G/F/UQ 筛选运行器。

UQ（Uniform-q 对照，2026-10-13）：候选核与 D/F 完全相同，唯一差量为选择规则
（同池均匀随机取同配额 64，无组内中心化、无跨组配额竞争），用于隔离「候选核」
与「组中心化选择规则」两个混杂因素。

固定哈希源训练与源验证成员从现有 Parquet 按需读取；本入口是源期筛选，
指标仍使用历史 0.5 阈值与筛选攻击面板，不代表正式低误报评价。
每臂每轮保存完整训练断点，运行状态和单臂结果保存在独占运行目录。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import resource
import sys
import time
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path

import fcntl

import numpy as np
import pyarrow.parquet as pq
import torch

# 环境变量 LLM_PROBE_ROOT 覆盖项目根（服务器设为 /root/autodl-tmp/thesis/experiments/llm_probe）
ROOT = Path(os.environ.get(
    "LLM_PROBE_ROOT",
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe",
))
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import ch3_drift_official_branch_conflict_diagnostic as diag
import ch3_drift_official_checkpoint_t17_eval as official
import ch3_drift_f_source_eligibility as eligibility
import ch3_drift_formal_contract as formal_contract

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
ALPHA_REVERSE = {official.CHAR_TO_ID[c]: c for c in ALPHA}
ARM_DISPLAY_NAMES = {
    "A": "干净微调",
    "B": "朴素字符增广",
    "D": "组中心跨组选择",
    "G": "良性条件误报补偿",
    "F": "组中心选择＋良性补偿",
    "MP": "混合曝光＋误报保护",
    "UQ": "均匀同配额选择（同 D/F 候选核，隔离选择规则）",
    "CAND4": "四候选二位核（隔离候选数 1→4，编辑位数固定 2）",
    "EDIT4": "单位编辑四位累积核（隔离编辑位数 2→4，候选数固定 1）",
    "CURRICULUM": "编辑预算课程（参数化核 q_t 1→2→4：2 位 → 累积 4 位 → 4 候选累积 4 位）",
    "C1R": "恒定一比一随机离散增广（隔离增广配比）",
    "ESAT": "ESAT 式固定子集对抗训练（任务化迁移）",
    "DRICHEL": "Drichel 式离散域对抗训练（任务化迁移）",
    "CEQ": "全局交叉熵难例 top-q 选择（同候选池同配额）",
    "CBN": "固定良性类权重（隔离良性侧代价重加权）",
}
SAFE_RESULT_NAME = re.compile(r"[A-Za-z0-9._-]+\Z")
CACHE_SCHEMA_VERSION = "drift-source-screen-cache-v1"
CACHE_POLICY_BY_ARM = {
    "A": "none_v1",
    "B": "source_screen_b_if_missing_v1",
    "D": "source_screen_d_base4_if_missing_v1",
    "G": "none_v1",
    "F": "source_screen_f_base4_if_missing_v1",
    "UQ": "source_screen_uq_base4_if_missing_v1",
    "CAND4": "source_screen_cand4_if_missing_v1",
    "EDIT4": "source_screen_edit4_if_missing_v1",
    "CURRICULUM": "source_screen_curriculum_if_missing_v1",
    "C1R": "source_screen_c1r_if_missing_v1",
    "ESAT": "source_screen_esat_if_missing_v1",
    "DRICHEL": "source_screen_drichel_if_missing_v1",
    "CEQ": "source_screen_ceq_base4_if_missing_v1",
    "CBN": "none_v1",
}
# CAND4/EDIT4/CURRICULUM（2026-10-13 追加，D-6/D-7）：
# 候选核成分分解与编辑预算课程。三臂的选择规则、配额、损失加权、超参与 D 逐项相同，
# 唯一差量 = 候选生成：
#   CAND4：4 个候选，每个均由原串各做一次 perturb2（2 位）——隔离「候选数 1→4」；
#   EDIT4：1 个候选，在原串上连续两次 perturb2（累积 4 位）——隔离「编辑位数 2→4」；
#   CURRICULUM：epoch 1 用 B 的弱核（1 个候选 × 2 位），epoch 2–3 用 D/F 的强核
#     （共享 base 的 4 候选 × 累积 4 位）——隔离「弱→强课程调度」。
# 注意：EDIT4 与 CURRICULUM 的 epoch 1 候选池 = 每批恶意样本数（约 64，随机波动），
# 当池 < 64 时 selection 取 min(64, |池|)，入批变体数无法恒定 64；该偏差已实测登记。
# UQ（Uniform-q）候选核与 D/F 完全相同（共享 base 上的两阶段复合四候选），
# 唯一差量为选择规则：从同一候选池均匀随机取同配额 64，不做组内中心化、
# 不做跨组配额竞争。选择使用独立 uniform_rng 流，避免扰动攻击 RNG 使候选池偏离 D/F。
# P1 近邻/内部对照五臂（2026-10-13 追加，实施计划 .Codex/docs/2026-10-13-外部基准与第二骨干/）：
#   C1R（Drichel 2024 §4.4 配比迁移）：每批恶意侧恒定 1:1 —— 批内恶意样本的前 ceil(m/2) 个
#     （idx 顺序，批序已由 SEED+ep shuffle 随机化）原串被替换为其 perturb2 变体，其余保留。
#     与 B 差别只在配比（B 每恶意样本追加 1 变体；C1R 恶意侧原串:变体 ≈ 1:1），核与
#     变体生成流（主 rng、遇序逐样本生成、缓存同键）与 B 逐字一致。
#   ESAT（Losch et al. ICLR 2024 式(2)(3) 任务化迁移）：训练前用独立非鲁棒参照模型
#     （A 臂逐 epoch 快照）的跨快照平均预测熵在全源训练集排序，取熵最高固定比例子集 A
#     （ρ=0.5，|A|=7500/30000；ESAT 原文 CIFAR 中点配置 25000/50000 的同比例映射，
#     待主代理确认）。训练时只对属于 A 的恶意样本生成 1 个 perturb2 变体（B 核），
#     其余恶意样本按原样入批；熵计算与排序独立于训练（ESAT §4.2）。
#   DRICHEL（Drichel et al. ASIA CCS 2024 §4.3 HotFlip 任务化迁移）：对每批恶意样本用
#     HotFlip 式一阶贪心在固定预算 2（与 perturb2 同名义）内生成离散白盒攻击：每步对每个
#     可编辑位置枚举 ALPHA 37 字符，一阶近似 ΔL ≈ (E_c − E_x)·∂L/∂E_x 取最大者应用，
#     重新前向后迭代至预算用尽（greedy，beam=1；原论文为 beam-search，计划冻结为贪心）。
#     每恶意样本 1 个攻击变体，按 UQ 同构的独立均匀流取 min(64, m) 入批（无组内中心化）。
#     变体跨轮重新生成（白盒攻击随模型演化），缓存键 (样本, epoch)。
#   CEQ（Average Top-k Loss，Fan et al. §2 式(1) 任务化迁移）：与 D/F 同候选池、同入批
#     配额，按未中心化交叉熵 ce = −log p 全局降序取 top-64（并列按候选池顺序）；
#     不做组内中心化、不做跨组配额竞争。
#   CBN（ConstBenign 反事实）：对所有真良性样本施加固定类权重 3.0（沿用组件 2 已登记
#     系数，清单 §3.1），不依赖当前误报；无对抗增广，其余同 A。


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, payload: dict) -> None:
    partial = path.with_name(path.name + ".partial")
    with partial.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(partial, path)


def write_checkpoint_atomic(path: Path, payload: dict) -> None:
    partial = path.with_name(path.name + ".partial")
    with partial.open("wb") as stream:
        torch.save(payload, stream)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(partial, path)


def rss_mib() -> float:
    # macOS 的 ru_maxrss 单位为字节；该值是进程历史峰值。
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)


def arm_label(arm: str) -> str:
    """返回同时包含稳定短键和机制展示名的日志标签。"""
    display_name = ARM_DISPLAY_NAMES.get(arm)
    return f"{arm}（{display_name}）" if display_name else arm


def result_name_arg(value: str) -> str:
    """校验结果文件名，拒绝路径分隔符和特殊文件名。"""
    if value in {".", ".."} or not SAFE_RESULT_NAME.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "结果文件名只能包含 ASCII 字母、数字、点、下划线和连字符，且不能是 . 或 .."
        )
    return value


def source_roots(domains: list[str], labels: np.ndarray) -> tuple[str, str]:
    """计算源顺序根和标签根；仅返回摘要，不保留逐实体身份材料。"""
    if len(domains) != len(labels):
        raise ValueError("源域名与标签长度不一致，不能建立缓存身份")
    order_digest = hashlib.sha256()
    label_digest = hashlib.sha256()
    for index, (domain, label) in enumerate(zip(domains, labels, strict=True)):
        order_digest.update(formal_contract.length_prefix_encode(str(index), domain))
        label_digest.update(formal_contract.length_prefix_encode(str(index), str(int(label))))
    return order_digest.hexdigest(), label_digest.hexdigest()


def cache_summary(cache: dict[int, list[str]], policy_id: str,
                  source_order_sha256: str) -> dict[str, int | str]:
    """生成不含缓存明文、逐索引摘要或索引清单的缓存收据。"""
    root = hashlib.sha256()
    root.update(formal_contract.length_prefix_encode(
        CACHE_SCHEMA_VERSION, policy_id, source_order_sha256,
    ))
    value_count = 0
    for source_index in sorted(cache):
        values = cache[source_index]
        value_count += len(values)
        value_hashes = [
            formal_contract.sha256_bytes(value.encode("utf-8"))
            for value in values
        ]
        entry_digest = formal_contract.sha256_bytes(
            formal_contract.length_prefix_encode(
                policy_id,
                str(source_index),
                str(len(values)),
                *value_hashes,
            )
        )
        root.update(formal_contract.length_prefix_encode(entry_digest))
    return {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "cache_policy_id": policy_id,
        "cache_entry_count": len(cache),
        "cache_value_count": value_count,
        "cache_root_sha256": root.hexdigest(),
    }


def rebuild_first_epoch_cache(arm: str, domains: list[str], labels: np.ndarray,
                              completed_epoch: int) -> dict[int, list[str]]:
    """用隔离的局部 RNG 重放完整首轮缓存，不污染训练随机状态。"""
    cache: dict[int, list[str]] = {}
    # CURRICULUM 的缓存按 (样本, epoch) 键、跨轮不同，无法在恢复时仅靠首轮重放重建；
    # ESAT 的重放需要熵子集（选择器快照集合）作为外部输入，DRICHEL 的变体是白盒攻击
    # （随当前模型演化、跨轮重新生成）。三者均不进入本函数（与 L 臂同样不支持中断恢复，
    # 失败时保留原断点）。
    if arm not in {"B", "D", "F", "UQ", "CAND4", "EDIT4", "C1R", "CEQ"} or completed_epoch == 0:
        return cache
    order = list(range(len(domains)))
    random.Random(SEED + 1).shuffle(order)
    replay_rng = random.Random(SEED)
    for source_index in order:
        if labels[source_index] != 1:
            continue
        original = domains[source_index]
        if arm == "B":
            cache[source_index] = [perturb2(original, replay_rng)]
        elif arm == "C1R":
            # C1R 与 B 同核同流：每恶意样本 1 个 perturb2 变体，键与值结构逐字一致。
            cache[source_index] = [perturb2(original, replay_rng)]
        elif arm == "CAND4":
            cache[source_index] = [perturb2(original, replay_rng) for _ in range(4)]
        elif arm == "EDIT4":
            cache[source_index] = [perturb2(perturb2(original, replay_rng), replay_rng)]
        elif arm == "CURRICULUM":
            cache[(source_index, 1)] = make_candidates_course(
                original, COURSE_BUDGET_BY_EPOCH[1], replay_rng
            )
        else:
            base = perturb2(original, replay_rng)
            cache[source_index] = [perturb2(base, replay_rng) for _ in range(4)]
    return cache


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


# CURRICULUM（D-7，2026-10-13 改为参数化课程核）：核是**同一个函数**，课程只把预算
# 参数 q_t 按轮次取值 —— 不是「弱核/强核」两个常量分支。
# 退化等式（共享底座上的可分组件，机制方案的机械证据）：
#   q_t=1 -> (base 链步数 0, 候选链步数 1, 候选数 1) = 1 候选 × 2 位       = B 核
#   q_t=2 -> (0, 2, 1)                              = 1 候选 × 累积 4 位  = EDIT4 核
#   q_t=4 -> (1, 1, 4)                              = 4 候选 × 累积 4 位  = D/F 核
# 主代理 2026-10-13 裁决：q_t 取值域冻结为 {1,2,4}，本轮**不实现** q_t=8 分支
# （理由：预算公平——静态臂均为 3 轮同预算；退化等式——末轮换 8 会破坏与既有臂的逐项对应）。
COURSE_CORE_BY_QT = {1: (0, 1, 1), 2: (0, 2, 1), 4: (1, 1, 4)}
COURSE_BUDGET_BY_EPOCH = {1: 1, 2: 2, 3: 4}


def make_candidates_course(domain: str, q_t: int, rng: random.Random) -> list:
    """课程核：单一函数，候选由预算参数 q_t 决定。

    `COURSE_CORE_BY_QT[q_t] = (base 链步数, 候选链步数, 候选数)`；base 先按 base 链步数
    链式 `perturb2`，多候选共享同一 base。实际编辑位数会因跨步位置碰撞而低于名义值
    （实测见 `.Codex/docs/2026-10-13-正式编辑预算科学筛选/训练核名义位数的碰撞饱和实测.md`）。
    """
    if q_t not in COURSE_CORE_BY_QT:
        raise ValueError(f"CURRICULUM 的 q_t 冻结为 {sorted(COURSE_CORE_BY_QT)}，收到 {q_t}")
    base_steps, cand_steps, count = COURSE_CORE_BY_QT[q_t]
    base = domain
    for _ in range(base_steps):
        base = perturb2(base, rng)
    if count == 1:
        candidate = base
        for _ in range(cand_steps):
            candidate = perturb2(candidate, rng)
        return [candidate]
    return [perturb2(base, rng) for _ in range(count)]


def hotflip_variants(domains: list[str], model, tokenizer) -> list[str]:
    """HotFlip 式一阶贪心离散白盒攻击（Drichel 2024 §4.3 任务化迁移，D-8）。

    每步对每个可编辑位置枚举 ALPHA 37 字符，一阶近似 ΔL ≈ (E_c − E_x)·∂L/∂E_x 取
    最大者应用，应用后重新前向迭代至预算用尽（greedy，beam=1；原论文为 beam-search，
    实施计划冻结为贪心一阶）。可编辑位置 = SLD body 字符位置（与 perturb2 同界），
    可编辑字符集 = ALPHA 37 项（与 perturb2 同集）。攻击目标 = 增大恶意类 CE。
    返回与输入同序的攻击变体列表。
    """
    budget = 2  # 固定编辑预算：与 perturb2 同名义 2 位（实施计划「固定编辑预算内」）
    chars = list(domains)  # 工作副本（逐步施加替换）
    b_chars = [d.rsplit(".", 1)[0] if "." in d else d for d in chars]
    b_lens = [len(s) for s in b_chars]
    char_ids = official.encode_char(chars).to(DEVICE)
    for _ in range(budget):
        token_ids = official.encode_subword(chars, tokenizer).to(DEVICE)
        # 子词分支无梯度（HotFlip 打分只需要 ∂L/∂(char 嵌入)）
        with torch.no_grad():
            token_embedding = model.embedding_t(token_ids)
            token_values = model.positional_encoding_t(token_embedding)
            token_mask = model.create_padding_mask(token_ids)
            token_output = model.transformer_encoder_t(token_values, mask=token_mask)
            token_valid = (~token_mask).float().unsqueeze(-1)
            token_mean = (token_output * token_valid).sum(dim=1) / token_valid.sum(dim=1).clamp(min=1)
            token_max = token_output.masked_fill(token_valid == 0, -1e9).max(dim=1).values
            token_feature = torch.cat([token_max, token_mean], dim=1)
        # 字符分支带梯度：输入嵌入设为叶变量，反传得 ∂L/∂E_x（对输入的梯度，非参数梯度）
        char_emb = model.embedding_c(char_ids).detach().requires_grad_(True)
        char_values = model.positional_encoding_c(char_emb)
        char_mask = model.create_padding_mask(char_ids)
        char_output = model.transformer_encoder_c(char_values, mask=char_mask)
        char_valid = (~char_mask).float().unsqueeze(-1)
        char_mean = (char_output * char_valid).sum(dim=1) / char_valid.sum(dim=1).clamp(min=1)
        char_max = char_output.masked_fill(char_valid == 0, -1e9).max(dim=1).values
        char_feature = torch.cat([char_max, char_mean], dim=1)
        logits = model.classifier_head(torch.cat([token_feature, char_feature], dim=1))
        loss = torch.nn.functional.cross_entropy(
            logits.float(), torch.ones(len(chars), dtype=torch.long, device=DEVICE)
        )
        loss.backward()
        g = char_emb.grad  # [B, 77, 256]
        if g is None:
            raise RuntimeError("HotFlip 一阶打分未获得输入梯度")
        emb_table = model.embedding_c.embedding.weight.detach()  # [43, 256]（TokenEmbedding 内部 nn.Embedding）
        # S[b,i,c] = g[b,i]·(E[c] − E[x_bi])：替换位置 i 的字符为 c 的一阶近似损失增量
        dot_table = torch.einsum("bid,vd->biv", g, emb_table)
        dot_self = (g * char_emb).sum(dim=-1, keepdim=True)
        scores = dot_table - dot_self  # [B, 77, 43]
        # 合法位置掩码：char 序列位置 1..len(body)（BOS 占 0；encode_char 截断 domain[:75]）
        position_ids = torch.arange(77, device=DEVICE)
        body_len_t = torch.tensor(b_lens, device=DEVICE)
        valid_pos = (position_ids[None, :] >= 1) & (position_ids[None, :] <= body_len_t[:, None])
        # 合法字符掩码：c ∈ ALPHA（id 5..41）且 ≠ 当前字符（替换必须改变字符）
        alpha_ids = torch.tensor([official.CHAR_TO_ID[c] for c in ALPHA], device=DEVICE)
        alpha_mask = torch.zeros(43, dtype=torch.bool, device=DEVICE)
        alpha_mask[alpha_ids] = True
        alpha_ids_full = torch.full((43,), -1, dtype=torch.long, device=DEVICE)
        alpha_ids_full[alpha_ids] = alpha_ids
        cur_char = char_ids.unsqueeze(-1)  # [B, 77, 1]
        valid_char = alpha_mask[None, None, :] & (alpha_ids_full[None, None, :] != cur_char)
        scores = scores.masked_fill(
            ~(valid_pos.unsqueeze(-1) & valid_char), float("-inf")
        )
        best_flat = scores.view(len(chars), -1).argmax(dim=1)  # [B]
        best_pos = (best_flat // 43).tolist()
        best_ch = (best_flat % 43).tolist()
        for b in range(len(chars)):
            i = best_pos[b]
            if scores[b, i, best_ch[b]].item() == float("-inf"):
                continue  # 无合法替换（body<1 等极端情形）——保持原样
            c_id = best_ch[b]
            s_pos = i - 1  # 字符串位置 = char 序列位置 − 1（BOS 占 0）
            s = list(chars[b])
            s[s_pos] = ALPHA_REVERSE[c_id]
            chars[b] = "".join(s)
            char_ids[b, i] = int(c_id)
    return chars


def load_split(limit: int) -> tuple[list[str], np.ndarray]:
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_benign_train.parquet").to_pylist()[:limit]
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_dga_train.parquet").to_pylist()[:limit]
    domains = [str(r["domain"]) for r in tb] + [str(r["domain"]) for r in td]
    labels = np.asarray([0] * len(tb) + [1] * len(td), dtype=np.int64)
    return domains, labels


def disable_nested_tensor(model) -> None:
    encoders = [module for module in model.modules() if isinstance(module, torch.nn.TransformerEncoder)]
    if len(encoders) != 2:
        raise RuntimeError(f"预期两个TransformerEncoder，实际为{len(encoders)}")
    for encoder in encoders:
        encoder.enable_nested_tensor = False
        encoder.use_nested_tensor = False


def load_mps_model():
    model = official.load_model(REF, CKPT, DEVICE)
    disable_nested_tensor(model)
    return model


def load_fixed_source_members(candidate_spec_value: str, purpose: str) -> tuple[list[str], np.ndarray, list[dict]]:
    if purpose not in {"source_train", "source_validation"}:
        raise ValueError("共同成员入口只允许源训练或源验证用途")
    config, _ = formal_contract.load_config("configs/ch3-drift-formal-evaluation-v1.json")
    spec_path = formal_contract.resolve_repo_relative(candidate_spec_value, must_exist=True)
    spec = eligibility.load_spec(spec_path)
    role_map = {role["role"]: role for role in config["input_roles"]}
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise RuntimeError("共同成员入口需要PyArrow") from exc
    domains: list[str] = []
    labels: list[int] = []
    receipts: list[dict] = []
    for entry in spec["roles"][purpose]:
        role_started = time.time()
        print(
            f"[源成员选择] 开始 purpose={purpose} role={entry['role']} count={entry['count']}",
            file=sys.stderr,
            flush=True,
        )
        role = role_map.get(entry["role"])
        if role is None:
            raise ValueError(f"成员角色不在正式配置中：{entry['role']}")
        valid = role["scope"] == "source" and (
            role["split"] in {"train", "test"} if purpose == "source_train" else role["split"] == "val"
        )
        if not valid:
            raise ValueError(f"成员角色用途不符：{entry['role']}")
        path = formal_contract.resolve_repo_relative(role["path"], must_exist=True)
        selected, receipt = eligibility.select_role(
            parquet=parquet,
            path=path,
            role=role,
            count=entry["count"],
            revision=config["data_revision"],
            namespace=spec["corpus_namespace"],
        )
        domains.extend(selected)
        labels.extend([0 if role["class"] == "benign" else 1] * len(selected))
        receipts.append(receipt)
        print(
            f"[源成员选择] 完成 role={entry['role']} raw_rows={receipt['raw_rows']} "
            f"selected={len(selected)} elapsed={time.time() - role_started:.1f}s",
            file=sys.stderr,
            flush=True,
        )
    if not domains or len(domains) != len(labels):
        raise RuntimeError(f"{purpose} 共同成员为空或标签错位")
    return domains, np.asarray(labels, dtype=np.int64), receipts


def source_feature_means(model, tokenizer, domains: list[str]) -> tuple[np.ndarray, np.ndarray]:
    token_sum = None
    char_sum = None
    count = 0
    model.eval()
    with torch.inference_mode():
        for offset in range(0, len(domains), EVAL_BATCH):
            chunk = domains[offset:offset + EVAL_BATCH]
            token_ids = official.encode_subword(chunk, tokenizer).to(DEVICE)
            char_ids = official.encode_char(chunk).to(DEVICE)
            token_feature, char_feature = diag.branch_features(model, token_ids, char_ids)
            token_value = token_feature.detach().cpu().numpy().sum(axis=0, dtype=np.float64)
            char_value = char_feature.detach().cpu().numpy().sum(axis=0, dtype=np.float64)
            token_sum = token_value if token_sum is None else token_sum + token_value
            char_sum = char_value if char_sum is None else char_sum + char_value
            count += len(chunk)
    if count != len(domains) or token_sum is None or char_sum is None:
        raise RuntimeError("源特征均值计算未覆盖全部共同成员")
    return (token_sum / count).astype(np.float32), (char_sum / count).astype(np.float32)


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
              epochs: int, ref_model=None, checkpoint_path: Path | None = None,
              run_identity: dict | None = None, progress=None,
              esat_subset: set[int] | None = None,
              selector_snapshot_dir: Path | None = None) -> dict:
    if arm not in CACHE_POLICY_BY_ARM:
        raise ValueError(f"本筛选入口不再接受未验收历史臂：{arm}")
    # 每臂使用相同的模型随机轨迹起点；断点恢复随后覆盖为保存的状态。
    torch.manual_seed(SEED)
    model = load_mps_model()
    n_params = sum(p.numel() for p in model.parameters())
    # 分层 lr：官方模型参数名无 "backbone"，按分类头匹配（classifier_head=1e-4，骨干=1e-6）
    opt = torch.optim.Adam([
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" not in n_], "lr": LR_BACKBONE},
        {"params": [p_ for n_, p_ in model.named_parameters() if "classifier_head" in n_], "lr": LR_HEAD},
    ])
    n_head = sum(p_.numel() for n_, p_ in model.named_parameters() if "classifier_head" in n_)
    label = arm_label(arm)
    print(f"[{label}] 分层 lr：骨干 {sum(p_.numel() for p_ in model.parameters()) - n_head} 参数 @1e-6，分类头 {n_head} 参数 @1e-4", file=sys.stderr, flush=True)
    print(f"[{label}] 官方模型 {n_params} 参数，训练 {len(train_d)} 样本 × {epochs} epochs", file=sys.stderr, flush=True)
    fpr_curve: list = []
    ec, ey = eval_clean
    ea, eay = eval_adv
    rng = random.Random(SEED)
    adv_cache: dict[int, list[str]] = {}
    adv_cache_p: dict[int, list] = {}  # P 臂 K=8 扩展缓存
    adv_cache_l: dict[tuple, list] = {}  # L 臂课程缓存（键含 epoch）
    adv_cache_drichel: dict[tuple, list] = {}  # DRICHEL 白盒攻击缓存（键=(样本, epoch)）
    adv_cache_m: dict[tuple, list] = {}  # M 臂 Mix 缓存（键=(样本, 档位)）
    benign_cache: dict[int, list[str]] = {}
    benign_rng = random.Random(SEED + 7)  # 良性变体独立种子，不与恶意变体序列耦合
    # UQ 臂均匀选择专用独立流：使攻击 RNG（候选生成）与 D/F 保持同一序列，
    # 候选池逐条相同；只有选择规则不同。
    uniform_rng = random.Random(SEED + 13)
    tau_val = torch.tensor(0.5, device=DEVICE)  # J 臂对偶变量 τ（RU 形式 min_τ）
    first_epoch = 1
    source_order_sha256, source_label_sha256 = source_roots(train_d, train_y)
    if checkpoint_path is not None and checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
        forbidden_cache_keys = {
            "adv_cache", "adv_cache_p", "adv_cache_l", "adv_cache_m", "benign_cache",
            "adv_cache_drichel",
        }
        if forbidden_cache_keys.intersection(checkpoint):
            raise RuntimeError(f"{label} 断点含旧明文缓存字段，拒绝迁移并保留原断点")
        if checkpoint["identity"] != run_identity or checkpoint["arm"] != arm:
            raise RuntimeError(f"{label} 断点身份与当前运行不一致")
        completed_epoch = int(checkpoint["completed_epoch"])
        if not 0 <= completed_epoch <= epochs:
            raise RuntimeError(f"{label} 断点轮次越界：{completed_epoch}")
        if checkpoint.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
            raise RuntimeError(f"{label} 断点缓存模式缺失或过期，拒绝恢复并保留原断点")
        if checkpoint.get("source_order_sha256") != source_order_sha256:
            raise RuntimeError(f"{label} 断点源顺序根不一致，拒绝恢复并保留原断点")
        if checkpoint.get("source_label_sha256") != source_label_sha256:
            raise RuntimeError(f"{label} 断点源标签根不一致，拒绝恢复并保留原断点")
        policy_id = CACHE_POLICY_BY_ARM[arm]
        if checkpoint.get("cache_policy_id") != policy_id:
            raise RuntimeError(f"{label} 断点缓存策略不一致，拒绝恢复并保留原断点")
        adv_cache = rebuild_first_epoch_cache(arm, train_d, train_y, completed_epoch)
        rebuilt_summary = cache_summary(adv_cache, policy_id, source_order_sha256)
        saved_summary = {
            key: checkpoint.get(key)
            for key in (
                "cache_schema_version", "cache_policy_id", "cache_entry_count",
                "cache_value_count", "cache_root_sha256",
            )
        }
        if rebuilt_summary != saved_summary:
            raise RuntimeError(f"{label} 缓存重放摘要不一致，拒绝恢复并保留原断点")

        # 只有源身份与缓存重放均核对通过后，才恢复训练状态和 RNG。
        model.load_state_dict(checkpoint["model"])
        opt.load_state_dict(checkpoint["optimizer"])
        rng.setstate(checkpoint["attack_rng"])
        benign_rng.setstate(checkpoint["benign_rng"])
        if arm == "UQ":
            if "uniform_rng" not in checkpoint:
                raise RuntimeError(f"{label} 断点缺 UQ 选择 RNG 状态，拒绝恢复并保留原断点")
            uniform_rng.setstate(checkpoint["uniform_rng"])
        torch.set_rng_state(checkpoint["cpu_rng"])
        if DEVICE.type == "mps":
            torch.mps.set_rng_state(checkpoint["mps_rng"])
        elif DEVICE.type == "cuda":
            torch.cuda.set_rng_state(checkpoint["cuda_rng"])
        tau_val = checkpoint["tau_val"].to(DEVICE)
        fpr_curve = checkpoint["fpr_curve"]
        first_epoch = completed_epoch + 1
        print(f"[{label} 恢复] 已完成 {completed_epoch}/{epochs} 轮，从第 {first_epoch} 轮继续", file=sys.stderr, flush=True)
    if progress is not None:
        progress(arm, "running", first_epoch - 1, 0, 0, None, None)
    n = len(train_d)
    for ep in range(first_epoch, epochs + 1):
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
            elif arm == "C1R":
                # C1R（恒定 1:1 随机离散增广，Drichel 2024 §4.4 配比迁移）：每批恶意样本
                # 的前 ceil(m/2) 个（idx 顺序，批序已由 SEED+ep shuffle 随机化）原串被
                # **替换**为其 perturb2 变体，其余恶意原串保留；批大小不变（128）。
                # 与 B 的差别只在配比（B 每恶意样本追加 1 变体；C1R 恶意侧原串:变体 =
                # floor(m/2):ceil(m/2) ≈ 1:1）；核（perturb2）、变体生成流（主 rng 遇序
                # 逐样本生成、缓存同键同结构）与 B 逐字一致。
                mal_seq = [i for i in idx if train_y[i] == 1]
                n_rep = (len(mal_seq) + 1) // 2  # ceil(m/2)
                replacements: dict[int, str] = {}
                for k, i in enumerate(mal_seq):
                    if k < n_rep:
                        if i not in adv_cache:
                            adv_cache[i] = [perturb2(train_d[i], rng)]
                        replacements[i] = adv_cache[i][0]
                if replacements:
                    batch_d = [replacements.get(i, train_d[i]) for i in idx]
            elif arm == "ESAT":
                # ESAT（Losch et al. ICLR 2024 式(2)(3) 任务化迁移）：训练前已用独立非鲁棒
                # 参照模型（A 臂逐 epoch 快照）的跨快照平均预测熵在全源训练集排序并冻结子集
                # esat_subset（训练前一次性，ESAT §4.2）。训练时只对属于 A 的恶意样本生成
                # 1 个 perturb2 变体（B 核），其余恶意样本按原样入批（干净 CE 项）。
                adv_batch = []
                for i in idx:
                    if train_y[i] == 1 and esat_subset is not None and i in esat_subset:
                        if i not in adv_cache:
                            adv_cache[i] = [perturb2(train_d[i], rng)]
                        adv_batch.append(adv_cache[i][0])
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            elif arm == "DRICHEL":
                # Drichel 式离散域对抗训练（ASIA CCS 2024 §4.3 HotFlip 任务化迁移）：
                # 对每批恶意样本用 HotFlip 式一阶贪心在固定预算 2（与 perturb2 同名义）
                # 内生成离散白盒攻击，每恶意样本 1 个攻击变体；按 UQ 同构的独立均匀流
                # 取 min(64, m) 入批（无组内中心化、无跨组竞争）。变体跨轮重新生成
                # （白盒攻击随当前模型演化），缓存键 (样本, epoch)。
                mal_idx = [i for i in idx if train_y[i] == 1]
                variants = []
                if mal_idx:
                    model.eval()
                    variants = hotflip_variants(
                        [train_d[i] for i in mal_idx], model, tokenizer
                    )
                    model.train()
                for i, v in zip(mal_idx, variants, strict=True):
                    adv_cache_drichel[(i, ep)] = [v]
                sel_order = list(range(len(mal_idx)))
                uniform_rng.shuffle(sel_order)
                adv_batch = [adv_cache_drichel[(mal_idx[j], ep)][0] for j in sel_order[:64]]
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            elif arm in ("N", "N2"):
                # N 臂（per-group top-1 训练对照，BiB-CP 型分析参照算子）与
                # N2 臂（per-group 选择 + 良性误报加权×3.0）：
                # 与 D 同预算（64 变体、批 192）、同变体生成（perturb2）、同组结构（K=4），
                # 唯一差量 = 选择算子：每组内取 u 最大（s 最小=最难）的 1 个入批，
                # 无跨组竞争、无中心化。N2 在 N 基础上加组件 2（误报加权），对照 F（cross-group+加权）。
                # 训练级发现（N 首轮）：per-group 检出优于 cross-group（反 V1 捕获率序）——
                # 覆盖-强度权衡实证（chatgpt4 预警、对象三式 3.3 组重加权项）。
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
                    groups: dict[int, list[int]] = {}
                    for j, o in enumerate(cand_owner):
                        groups.setdefault(o, []).append(j)
                    for js in groups.values():  # 每组取 s 最小（最难）1 个，无跨组竞争
                        adv_batch.append(cands[js[int(np.argmin(p_cand[js]))]])
                    model.train()
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
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
            elif arm == "P":
                # P 臂（搜索预算扩展，定理 3/V3 的训练级检验）：与 D 唯一差量 = K 4→8
                # （每干净恶意域名 8 个 perturb2 变体、候选池 256→512、配额不变 64）——
                # V3 预测每干净样本覆盖缺口从 0.30 收至 ~0.16（Uniform 1/9），
                # 若训练收益随覆盖单调则 P 优于 D。判据同 v2 口径（Mask 改善+FPR 门）。
                mal_idx = [i for i in idx if train_y[i] == 1]
                cands: list[str] = []
                cand_owner: list[int] = []
                for i in mal_idx:
                    if i not in adv_cache_p:
                        base = perturb2(train_d[i], rng)
                        adv_cache_p[i] = [perturb2(base, rng) for _ in range(8)]
                    for v in adv_cache_p[i]:
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
            elif arm in ("M", "MP"):
                # M 臂（Mix 对照，HARD-GATE 外审 §4.2）：三档候选池每批均匀混合、无课程顺序，
                # 选择机制与 L/D 完全一致。归因结构：L−M = 课程顺序增量；M−D = 新增曝光增量。
                # MP 臂（混合曝光＋误报保护）：复用 M 的候选生成与跨组选择，
                # 并在损失分支复用 F 的真良性误报 hard ×3.0 加权；除此之外不改变训练合同。
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
            elif arm in ("D", "E", "F", "H", "UQ", "CAND4", "EDIT4", "CURRICULUM", "CEQ"):
                # CAND4/EDIT4/CURRICULUM（2026-10-13 追加，D-6/D-7）：下游选择（组内中心化
                # top-64 跨组竞争）、配额、损失加权与 D 逐行相同，唯一差量在候选生成：
                # CAND4 四候选二位、EDIT4 单位编辑四位累积、CURRICULUM 弱核→强核按轮切换。
                # 既有 D/E/F/H/UQ 的 RNG 调用顺序保持不变（base 只在原分支生成）。
                # UQ 臂（Uniform-q 对照，2026-10-13）：候选核与 D/F 逐行相同
                # （共享 base 的两阶段复合四候选，每组 K=4），候选评分前向同样保留，
                # 唯一差量 = 入损失的 64 个变体由「组内中心化优势 top-64 跨组竞争」
                # 换为「同一候选池上均匀随机取 64」，无组内中心化、无跨组配额竞争。
                # 用途：与 D/F 同核同配额 ⇒ 隔离选择规则；与 B 同均匀配额 ⇒ 隔离候选核。
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
                    if arm == "CURRICULUM":
                        q_t = COURSE_BUDGET_BY_EPOCH.get(ep)
                        if q_t is None:
                            raise ValueError(f"CURRICULUM 未冻结 epoch {ep} 的 q_t（仅 {sorted(COURSE_BUDGET_BY_EPOCH)}）")
                        key = (i, ep)
                        if key not in adv_cache:
                            adv_cache[key] = make_candidates_course(train_d[i], q_t, rng)
                        variants = adv_cache[key]
                    else:
                        if i not in adv_cache:
                            if arm == "CAND4":
                                adv_cache[i] = [perturb2(train_d[i], rng) for _ in range(4)]
                            elif arm == "EDIT4":
                                adv_cache[i] = [perturb2(perturb2(train_d[i], rng), rng)]
                            else:
                                base = perturb2(train_d[i], rng)
                                adv_cache[i] = [perturb2(base, rng) for _ in range(4)]
                        variants = adv_cache[i]
                    for v in variants:
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
                    if arm == "UQ":
                        # 唯一差量：在同一候选池上均匀随机取同配额 64（min(64, |池|)）；
                        # group/fooled/scored 的计算保留以维持与 D/F 逐行相同的路径，
                        # 但不参与选择。组内中心化与跨组配额竞争均不生效。
                        sel_order = list(range(len(cands)))
                        uniform_rng.shuffle(sel_order)
                        adv_batch = [cands[j] for j in sel_order[:64]]
                    elif arm == "CEQ":
                        # CEQ（Average Top-k Loss，Fan et al. §2 式(1) 任务化迁移）：
                        # 与 D/F 同候选池、同入批配额，按未中心化交叉熵 ce = −log p_mal
                        # 全局降序取 top-64（并列按候选池顺序，np.argsort stable）；
                        # 不做组内中心化、不做跨组配额竞争。ce 从候选评分前向的 p_cand
                        # 计算（clip 1e-12 防数值下溢；CE 与 p 单调等价，clip 不改变排序）。
                        ce_cand = -np.log(np.clip(p_cand, 1e-12, None))
                        ce_order = np.argsort(-ce_cand, kind="stable")[:64]
                        adv_batch = [cands[j] for j in ce_order]
                    else:
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
                elif arm in ("F", "G", "N2", "MP"):
                    # F 臂 = D + 良性误报加权（双侧组相对的良性侧最简形式）；
                    # G 臂 = 只组件 2（无对抗增广、仅良性误报加权）——四臂消融的对称单臂；
                    # N2 臂 = N（per-group 选择）+ 组件 2——对照 F（cross-group+加权）的选择算子检验。
                    # MP 臂 = M（三档混合曝光＋跨组选择）+ 本分支的良性误报保护。
                    # batch 内当前模型判恶意的真良性样本 CE ×3.0，把分布上移的误报拉回。
                    # 权重 3.0 为任务化设定（无文献精确值）：对冲 64 变体配额的恶意侧压力量级，
                    # 源侧标定；若有效再升级为良性 CharBot 近邻组相对完整形态
                    fooled_b = (p_[:, 1] >= 0.5) & (sub_y == 0)
                    w = torch.ones(len(sub_y), device=DEVICE)
                    w[fooled_b] = 3.0
                    loss_s = (ce * w).sum() / n_tot
                elif arm == "CBN":
                    # CBN（ConstBenign 反事实，清单 §3.1）：对**所有**真良性样本施加固定
                    # 类权重 3.0（沿用组件 2 已登记系数，不依赖当前误报、不新选数值）；
                    # 无对抗增广（走 A 的路径），其余同 A。与 F/G 的差量 = 条件误报门 vs
                    # 静态类代价。
                    w = torch.ones(len(sub_y), device=DEVICE)
                    w[sub_y == 0] = 3.0
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
            if not math.isfinite(loss_log):
                raise RuntimeError(f"{label} 第 {ep} 轮第 {bi + 1} 批损失非有限值")
            if bi == 0 or (bi + 1) % 20 == 0 or bi + 1 == nb:
                elapsed = time.time() - t0
                rate = (bi + 1) / max(elapsed, 1e-9)
                eta = (nb - bi - 1) / max(rate, 1e-9)
                print(
                    f"[{label} 心跳] epoch={ep}/{epochs} batch={bi + 1}/{nb} "
                    f"loss={loss_log:.6f} elapsed={elapsed:.1f}s "
                    f"rate={rate:.3f}批/s eta={eta / 60:.1f}min rss_peak={rss_mib():.1f}MiB",
                    file=sys.stderr,
                    flush=True,
                )
                if progress is not None:
                    progress(arm, "running", ep, bi + 1, nb, loss_log, None)
        # 逐 epoch 干净 FPR 曲线（文献代理 Q1 裁决：识别"验证损失上升段"，防瞬态误判）
        model.eval()
        clean_now = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)
        adv_now = metrics(model, tokenizer, ea, eay, tok_mean, char_mean)
        fpr_curve.append({"epoch": ep, "clean_FPR": clean_now["FPR"], "attack_FNR": adv_now["FNR"], "attack_AP": adv_now["AP"]})
        print(
            f"[{label} 里程碑] epoch {ep}/{epochs} 完成，"
            f"干净FPR={clean_now['FPR']:.4f} 攻击FNR={adv_now['FNR']:.4f} "
            f"攻击AP={adv_now['AP']:.4f} 耗时={time.time()-t0:.1f}s",
            file=sys.stderr,
            flush=True,
        )
        if checkpoint_path is not None:
            cache_metadata = cache_summary(
                adv_cache, CACHE_POLICY_BY_ARM[arm], source_order_sha256,
            )
            state = {
                "identity": run_identity,
                "arm": arm,
                "completed_epoch": ep,
                "model": model.state_dict(),
                "optimizer": opt.state_dict(),
                "attack_rng": rng.getstate(),
                "benign_rng": benign_rng.getstate(),
                "uniform_rng": uniform_rng.getstate(),
                "cpu_rng": torch.get_rng_state(),
                "mps_rng": torch.mps.get_rng_state() if DEVICE.type == "mps" else None,
                "cuda_rng": torch.cuda.get_rng_state() if DEVICE.type == "cuda" else None,
                "source_order_sha256": source_order_sha256,
                "source_label_sha256": source_label_sha256,
                **cache_metadata,
                "tau_val": tau_val.detach().cpu(),
                "fpr_curve": fpr_curve,
            }
            write_checkpoint_atomic(checkpoint_path, state)
            # ESAT 选择器快照（A 臂重跑专用）：每轮末把模型权重存为选择器快照。
            # 快照是独立制品（不改既有 A 臂运行目录），由 ESAT 子集计算脚本消费。
            if selector_snapshot_dir is not None and arm == "A":
                snapshot_path = selector_snapshot_dir / f"selector-snapshot-ep{ep}.pt"
                partial = snapshot_path.with_name(snapshot_path.name + ".partial")
                with partial.open("wb") as stream:
                    torch.save({
                        "epoch": ep,
                        "model": {k: v.detach().cpu() for k, v in model.state_dict().items()},
                        "arm": arm,
                        "identity": run_identity,
                    }, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(partial, snapshot_path)
                print(f"[{label} 选择器快照] epoch {ep} -> {snapshot_path.name}", file=sys.stderr, flush=True)
        if progress is not None:
            progress(arm, "checkpointed", ep, nb, nb, None, fpr_curve[-1])
    model.eval()
    clean = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)
    adv = metrics(model, tokenizer, ea, eay, tok_mean, char_mean)
    return {"clean": clean, "adv": adv, "n_params": n_params, "fpr_curve": fpr_curve, "_model": model}


def run_pipeline(dry: int, arms: tuple[str, ...], epochs: int, out_name: str,
                 candidate_spec: str, identity: dict, status: dict, status_path: Path,
                 esat_subset: set[int] | None = None,
                 selector_snapshot_dir: Path | None = None) -> None:
    torch.manual_seed(SEED); np.random.seed(SEED); random.seed(SEED)
    tokenizer = official.PreTrainedTokenizerFast(
        tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json")
    )
    tr_d, tr_y, train_receipts = load_fixed_source_members(candidate_spec, "source_train")
    ec, ey, validation_receipts = load_fixed_source_members(candidate_spec, "source_validation")
    if dry:
        tr_d, tr_y = tr_d[:dry], tr_y[:dry]
        ec, ey = ec[:dry], ey[:dry]
    td = [domain for domain, label in zip(ec, ey, strict=True) if label == 1]
    ey = ey.astype(bool)
    rng = random.Random(SEED)
    ea_k2 = [perturb2(domain, rng) for domain in td]
    ea_krand = [perturb2(domain, rng) for domain in td]  # k∈U{1..4} 预算随机化组
    ea_mask = [perturb_half(domain, rng) for domain in td]  # MaskDGA 半替换强攻击面板
    eval_clean = (ec, ey)
    eval_adv_k2 = (ea_k2, np.ones(len(ea_k2), dtype=bool))
    eval_adv_krand = (ea_krand, np.ones(len(ea_krand), dtype=bool))
    eval_adv_mask = (ea_mask, np.ones(len(ea_mask), dtype=bool))
    print(f"[官方 P2/P3] 训练 {len(tr_d)}、评价干净 {len(ec)}、对抗 k2 {len(ea_k2)}/krand {len(ea_krand)}/maskdga {len(ea_mask)}", file=sys.stderr, flush=True)

    model0 = load_mps_model()
    tok_mean, char_mean = source_feature_means(model0, tokenizer, tr_d)
    del model0

    results: dict = {}
    adv_panels = {"k2": eval_adv_k2, "krand": eval_adv_krand, "maskdga": eval_adv_mask}
    ref_model = None
    if any(a_ == "E" for a_ in arms):
        ref_model = load_mps_model()
        ref_model.eval()
        print("[E 臂] 参考模型已加载（冻结初始判别器，KL 锚定用）", file=sys.stderr, flush=True)

    def progress(arm: str, phase: str, epoch: int, batch: int, total: int,
                 loss: float | None, metrics_now: dict | None) -> None:
        arm_status = status["arms"].setdefault(arm, {})
        arm_status.update({
            "phase": phase,
            "epoch": epoch,
            "batch": batch,
            "total_batches": total,
            "last_heartbeat": now_utc(),
            "rss_peak_mib": round(rss_mib(), 1),
        })
        if loss is not None:
            arm_status["last_loss"] = loss
        if metrics_now is not None:
            arm_status["last_epoch_metrics"] = metrics_now
        status["phase"] = phase
        status["current_arm"] = arm
        write_json_atomic(status_path, status)

    for arm in arms:
        arm_result_path = OUT / f"arm-{arm}-result.json"
        if arm_result_path.exists():
            saved = json.loads(arm_result_path.read_text(encoding="utf-8"))
            if saved["identity"] != identity or saved["arm"] != arm:
                raise RuntimeError(f"{arm_label(arm)} 已完成结果身份不一致")
            results[arm] = saved["result"]
            progress(arm, "completed", epochs, 0, 0, None, None)
            print(f"[{arm_label(arm)} 恢复] 已完成单臂结果，跳过重复训练", file=sys.stderr, flush=True)
            continue
        t0 = time.time()
        r = train_arm(
            arm, tr_d, tr_y, tokenizer, tok_mean, char_mean,
            eval_clean, eval_adv_k2, epochs, ref_model=ref_model,
            checkpoint_path=OUT / f"arm-{arm}-checkpoint.pt",
            run_identity=identity,
            progress=progress,
            esat_subset=esat_subset,
            selector_snapshot_dir=selector_snapshot_dir,
        )
        r["wall_seconds"] = round(time.time() - t0, 1)
        arm_model = r.pop("_model")
        if arm in ARM_DISPLAY_NAMES:
            r["display_name"] = ARM_DISPLAY_NAMES[arm]
        results[arm] = r
        # 双分组评价（该臂模型）：k=2 与 k∈U{1..4}
        for pname, (pa, pay) in adv_panels.items():
            results[arm][f"adv_{pname}"] = metrics(arm_model, tokenizer, pa, pay, tok_mean, char_mean)
        write_json_atomic(arm_result_path, {"identity": identity, "arm": arm, "result": results[arm]})
        progress(arm, "completed", epochs, 0, 0, None, None)
        print(f"[里程碑] {arm_label(arm)}: clean={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['clean'].items()})} adv={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['adv'].items()})}", file=sys.stderr, flush=True)
        del arm_model

    if "A" in results and "B" in results and "C" in results and len(results) == 3:
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
        # 非 A/B/C 组合（如 L/M/D、单臂）：verdict 由主代理按冻结判据从 results 手工裁决
        verdict = {"note": f"custom arms {sorted(results)} — manual adjudication per frozen criteria"}
    payload = {"source_members": {"train": train_receipts, "validation": validation_receipts}, "results": results, "verdict": verdict}
    write_json_atomic(OUT / out_name, payload)
    status["phase"] = "completed"
    status["completed_at"] = now_utc()
    status["current_arm"] = None
    write_json_atomic(status_path, status)
    print(f"[里程碑] {json.dumps(verdict, ensure_ascii=False)} -> {out_name}", file=sys.stderr, flush=True)


def main(dry: int = 0, arms_arg: str | None = None, result_name: str | None = None,
         candidate_spec: str | None = None, esat_subset_arg: str | None = None,
         selector_snapshot_dir_arg: str | None = None) -> None:
    if candidate_spec is None:
        raise ValueError("共同预算训练必须显式提供 candidate-spec")
    if dry < 0:
        raise ValueError("dry-run 不能为负数")
    arms = tuple(arms_arg.split(",")) if arms_arg else (("A",) if dry else ("A", "B", "D", "G", "F"))
    if not arms or any(not re.fullmatch(r"[A-Z][A-Z0-9]*", arm) for arm in arms):
        raise ValueError("训练臂列表不合法")
    unsupported_arms = sorted(set(arms) - set(CACHE_POLICY_BY_ARM))
    if unsupported_arms:
        raise ValueError(f"本筛选入口仅接受已验收臂 A/B/D/G/F/UQ：{unsupported_arms}")
    if len(set(arms)) != len(arms):
        raise ValueError("训练臂不能重复")
    epochs = 1 if dry else EPOCHS
    out_name = result_name_arg(result_name) if result_name else (
        "official-p2p3-DRYRUN.json" if dry else "official-p2p3-result.json"
    )
    spec_path = formal_contract.resolve_repo_relative(candidate_spec, must_exist=True)
    selector_snapshot_dir: Path | None = (
        Path(selector_snapshot_dir_arg) if selector_snapshot_dir_arg else None
    )
    esat_subset: set[int] | None = None
    if esat_subset_arg:
        subset_path = formal_contract.resolve_repo_relative(esat_subset_arg, must_exist=True)
        subset_payload = json.loads(Path(subset_path).read_text(encoding="utf-8"))
        if subset_payload.get("schema_version") != "drift-esat-subset-v1":
            raise ValueError(f"ESAT 子集清单 schema 不符：{subset_path}")
        if subset_payload.get("candidate_spec_sha256") != sha256_file(spec_path):
            raise ValueError("ESAT 子集清单与当前 candidate-spec 不匹配")
        if len(subset_payload.get("subset_indices", [])) == 0:
            raise ValueError("ESAT 子集清单为空")
        esat_subset = set(subset_payload["subset_indices"])
    identity = {
        "code_sha256": sha256_file(Path(__file__).resolve()),
        "member_selector_sha256": sha256_file(Path(eligibility.__file__).resolve()),
        "model_loader_sha256": sha256_file(Path(official.__file__).resolve()),
        "feature_adapter_sha256": sha256_file(Path(diag.__file__).resolve()),
        "candidate_spec_sha256": sha256_file(spec_path),
        "checkpoint_sha256": sha256_file(CKPT),
        "source_revision": DATA.name,
        "arms": list(arms),
        "epochs": epochs,
        "batch": BATCH,
        "seed": SEED,
        "device": str(DEVICE),
        "precision": "bf16" if USE_BF16 else "fp32",
        "result_name": out_name,
        "dry_run": dry,
        "esat_subset_sha256": (
            sha256_file(Path(esat_subset_arg).resolve()) if esat_subset_arg else None
        ),
        "selector_snapshot_dir": selector_snapshot_dir_arg,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    status_path = OUT / "run-status.json"
    with (OUT / "run.lock").open("w") as lock_stream:
        try:
            fcntl.flock(lock_stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"运行目录已有活动进程：{OUT}") from exc
        if status_path.exists():
            status = json.loads(status_path.read_text(encoding="utf-8"))
            if status["identity"] != identity:
                raise RuntimeError("运行目录身份不一致，拒绝覆盖既有制品")
            if status["phase"] == "completed":
                if not (OUT / out_name).is_file():
                    raise RuntimeError("状态为已完成但总结果文件缺失")
                print(f"[恢复] 运行已完成：{OUT / out_name}", file=sys.stderr, flush=True)
                return
        else:
            allowed = {"run.lock", "console.log"}
            unexpected = sorted(path.name for path in OUT.iterdir() if path.name not in allowed)
            if unexpected:
                raise RuntimeError(f"新运行目录含既有制品，拒绝覆盖：{unexpected}")
            status = {
                "schema": "drift-source-screen-v1",
                "identity": identity,
                "phase": "loading_source",
                "started_at": now_utc(),
                "pid": os.getpid(),
                "current_arm": None,
                "arms": {},
            }
            write_json_atomic(status_path, status)
        status["pid"] = os.getpid()
        status["resumed_at"] = now_utc()
        write_json_atomic(status_path, status)
        try:
            run_pipeline(dry, arms, epochs, out_name, candidate_spec, identity, status, status_path,
                         esat_subset=esat_subset, selector_snapshot_dir=selector_snapshot_dir)
        except BaseException as exc:
            status["phase"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
            status["failed_at"] = now_utc()
            status["last_error"] = f"{type(exc).__name__}: {exc}"
            write_json_atomic(status_path, status)
            raise


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=0)
    ap.add_argument("--arms", default=None, help="逗号分隔臂列表，如 A,B,D,F,G（默认五臂/干跑 A）")
    ap.add_argument("--result-name", type=result_name_arg, default=None, help="结果文件名，不得含路径或特殊字符")
    ap.add_argument("--candidate-spec", required=True, help="仓库相对固定哈希源成员规格")
    ap.add_argument("--esat-subset", default=None,
                    help="ESAT 臂专用：熵排序固定子集清单 JSON（schema drift-esat-subset-v1）")
    ap.add_argument("--selector-snapshot-dir", default=None,
                    help="A 臂重跑专用：每轮末保存选择器快照的目录")
    a = ap.parse_args()
    main(dry=a.dry_run, arms_arg=a.arms, result_name=a.result_name, candidate_spec=a.candidate_spec,
         esat_subset_arg=a.esat_subset, selector_snapshot_dir_arg=a.selector_snapshot_dir)
