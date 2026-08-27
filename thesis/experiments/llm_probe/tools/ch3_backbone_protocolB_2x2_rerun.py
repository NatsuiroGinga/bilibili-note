# -*- coding: utf-8 -*-
"""第三章基座消融协议 B：全注意力（transformer）与门控循环（gru）重跑。

唯一需求来源（逐字执行，不得自行改设计）：
  `.Codex/docs/RWKV/2026-08-27-三骨干消融本机筛选重跑/服务器正式重跑合同.md`

本文件是协议 A（`ch3_backbone_protocolA_v2.py`）针对该合同两项预注册修订的独立实现，
**不修改协议 A 的任何历史结果**，运行身份、输出根、判据全部与协议 A 区分：

修订一（选轮指标）：逐 epoch 选择信号从「LSPR23 实体不相交验证逐流 AP」换成
  「LSPR23 实体不相交验证实体 AP」，并列取最早、无早停；逐流 AP 继续记录但不参与选择。
修订二（学习率网格）：废除协议 A 对全部骨干硬编码 `lr=2e-3`；改为网格
  `{2e-3, 3.162277660168379e-4}`，只在 C00 上用修订一的指标比较，胜出值冻结后四格齐用。
  本文件对 transformer 与 gru **同规则**：两个 lr 候选都在 C00 上真实训练比较——
  协调方曾建议因「2026-08-17-第三章实验台账.md:316」显示 transformer 择优 lr=2e-3 而跳过
  该骨干的候选训练，但核验该行引用的是「等参数基线 Transformer」（83,105 参数，Leoste 2025
  同类等参数改造），与本文件重跑的「跨基座 transformer」（90,631 参数，
  `ch3_backbone_models.TR_D=77/TR_HEADS=7`）是两个不同架构，证据不可跨模型套用，
  故未采纳该建议，仍按合同对两骨干等规则跑满 lr-select。

判据（预注册，不得改）：封印后 LSPR24 描述性评价（每格恰好一次）上，
  `C01 > C00`（仅 ELP） 且 `C10 > C00`（仅 CPA） 且 `C11 >= max(C01, C10)`。
  三项全过即该骨干通过纳入判据；任一不过按 U6 定案剔除，不追调不重跑，如实报告。

四格语义沿用 `ch3_backbone_protocolA_v2.py` 的 `ALL_CELLS`：
  C00=(agg=False, lp=False)　C01=(agg=False, lp=True，仅 ELP)
  C10=(agg=True, lp=False，仅 CPA)　C11=(agg=True, lp=True)

============================ 阶段与 LSPR24 隔离保证 ============================
阶段一 lr-select：只在 C00 上，对 LR_GRID 的每个候选各训练一次（20 epoch 不早停），
  逐 epoch 只用 LSPR23 验证集算实体 AP（选择信号）与逐流 AP（仅记录），
  两个候选训练完毕后按验证实体 AP 比较，胜出 lr 落盘冻结（`lr_select_frozen.json`）。
  此刻 LSPR24 的任何数组不存在于本进程。
阶段二 cells：胜出 lr 复制进 C00 的正式格结果；C01/C10/C11 用胜出 lr 各训练一次。
  四格全部 trained 后，闸门从磁盘重新推导（不读任何可能过期的布尔值）。
阶段三 target-eval：闸门开启后才第一次读入 LSPR24，每格恰好评价一次，
  `target_year_arrays_read` 计数在此之前恒为 0，之后记为已读入的目标年数组个数（7）。

============================ 模型与评价函数复用（不复制粘贴重写）============================
Model / RWKV7TimeMix / rwkv7_op / npar_formula / hid_of / lp_pool /
split_lspr23_entity_disjoint：从 `ch3_backbone_models.py` import（该文件是从
`ch3_backbone_protocolA_v2.py` 抽取的纯定义模块，逻辑逐字未变）。
build_flow_entity / entity_scores / evaluate_entity_branch / dr_at_fpr /
complete_budget_curve：从 `ch3_full_mlp_complete_entity_lp_protocol_a_q0.py` import
（该文件对 GPU 依赖缺失时把 torch/np 置 None 而不在顶层执行任何训练，已被
`..._q0_bf16.py` 验证为可安全 import 的纯函数库）。这些函数使 LSPR23 验证期与
LSPR24 目标期的实体级评价共用同一套久经检验的实现，而不是本文件重新手写一份。

精度：按 `configs/neural-precision-profiles-v1.json` 的默认 profile
`cuda-bf16-amp-fp32-sensitive-v1`，经 `tools/neural_precision_runtime.py` 接入——
前向计算在 CUDA autocast(bfloat16) 下进行，损失、概率归一化、熵相关的敏感计算
在 `fp32_island` 内以 fp32 完成，模型参数与优化器状态全程 fp32，不用 GradScaler。
单步有效批（64 条流）在显存充裕、无需梯度累积的前提下一次性反向，
故不引入 `EffectiveBatchAccumulator`（累积步数恒为 1 时它是恒等操作）。
"""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
PROD_OUT_ROOT = f"{ROOT}/runs/diagnostics/ch3-backbone-2x2-rerun-protocol-b-seed42-v1"
PRECISION_CONTRACT_PATH = f"{ROOT}/configs/neural-precision-profiles-v1.json"

_TOOL_DIR = Path(__file__).resolve().parent
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

from ch3_backbone_models import (  # noqa: E402
    D,
    Model,
    hid_of,
    lp_pool,
    npar_formula,
    split_lspr23_entity_disjoint,
)
import neural_precision_runtime as precision  # noqa: E402
from ch3_full_mlp_complete_entity_lp_protocol_a_q0 import (  # noqa: E402
    DR_FPR_GRID,
    build_flow_entity,
    entity_scores,
    evaluate_entity_branch,
)

ALL_CELLS = [("C00", False, False), ("C01", False, True),
             ("C10", True, False), ("C11", True, True)]
LR_GRID = (2e-3, 3.162277660168379e-4)  # 冻结数值：服务器正式重跑合同.md 修订二

_ap = argparse.ArgumentParser(description="第三章基座消融协议 B：lr 网格 + 实体 AP 选轮的 2x2 重跑")
_ap.add_argument("--backbone", required=True, choices=["gru", "transformer"],
                 help="本进程负责的骨干；一个进程只跑一个骨干的 lr-select + 四格 + 目标评价")
_ap.add_argument("--out-root", default=PROD_OUT_ROOT, help="输出根；正式运行不要改")
_ap.add_argument("--n-epoch", type=int, default=20, help="仅供实现验证降规模用；正式运行必须 20")
_ap.add_argument("--epoch-steps", type=int, default=1000, help="仅供实现验证降规模用；正式运行必须 1000")
_ap.add_argument("--skip-impl-verify", action="store_true", help="仅供实现验证降规模用；正式运行禁止")
_ap.add_argument("--fixed-lr", type=float, default=None,
                 help="紧急操作指令专用：跳过 lr-select 两候选比较，直接冻结该 lr 训练四格。"
                      "2026-08-27 GPU 窗口仅余约 2 小时时由协调方下达，仅对下达时刻标的骨干生效，"
                      "结果收据 lr_select_frozen.json 会如实记录 mode=directive_fixed_skip_comparison，"
                      "不冒充已完成的两候选实体AP比较。")
ARGS = _ap.parse_args()
FIXED_LR = ARGS.fixed_lr

BK = ARGS.backbone
OUT = os.path.join(os.path.abspath(ARGS.out_root), BK)
IS_PROD = os.path.abspath(ARGS.out_root) == os.path.abspath(PROD_OUT_ROOT)

if IS_PROD:
    assert ARGS.n_epoch == 20, f"正式运行 n_epoch 必须为 20，实为 {ARGS.n_epoch}"
    assert ARGS.epoch_steps == 1000, f"正式运行 epoch_steps 必须为 1000，实为 {ARGS.epoch_steps}"
    assert not ARGS.skip_impl_verify, "正式运行禁止跳过实现验证"

RUN_ID = f"ch3-backbone-2x2-rerun-protocol-b-{BK}-seed42-v1"
LR_SELECT_DIR = f"{OUT}/lr_select"
CELLS_DIR = f"{OUT}/cells"
PROG = f"{OUT}/progress.jsonl"
EVAL_PROG = f"{OUT}/eval_progress.jsonl"
os.makedirs(LR_SELECT_DIR, exist_ok=True)
os.makedirs(CELLS_DIR, exist_ok=True)

# ---- 超参：逐字照抄协议 A（lr 除外——本文件的核心修订二）----
L, BS = 128, 64
SEED, AUX_W = 42, 1.0
EPOCH_STEPS = ARGS.epoch_steps
N_EPOCH = ARGS.n_epoch
VAL_FRAC, TIME_TAIL = 0.10, 0.15

# ---- 阶段闸门与计数器 ----
SELECTION_FROZEN = False
TARGET_YEAR_ARRAYS_READ = 0
_EVAL24_CALLS = 0
_EVAL24_RESUMED = 0
_EVAL24_KEYS = set()
_GATE_DERIVED_AT = None


# =====================================================================================
# 持久化原语：逐字照抄 ch3_backbone_protocolA_v2.py 的实现（先写 .tmp、fsync、再 os.replace）
# =====================================================================================
def _fsync_dir(path):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd = os.open(d, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    _fsync_dir(path)


def atomic_torch_save(obj, path):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        torch.save(obj, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    _fsync_dir(path)


def atomic_npy(arr, path):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        np.save(f, arr, allow_pickle=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    _fsync_dir(path)


def append_jsonl(path, rec):
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def read_stage(path, stage):
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("stage") == stage and r.get("cell_key"):
                out[r["cell_key"]] = r
    return out


def load_ckpt(path):
    return torch.load(path, map_location="cpu", weights_only=False)


def rng_snapshot(gen):
    return {"torch_cpu": torch.get_rng_state(),
            "torch_cuda_all": (torch.cuda.get_rng_state_all()
                               if torch.cuda.is_available() else []),
            "numpy": np.random.get_state(),
            "python": random.getstate(),
            "batch_gen": gen.get_state()}


def rng_restore(s, gen):
    torch.set_rng_state(s["torch_cpu"].cpu() if torch.is_tensor(s["torch_cpu"]) else s["torch_cpu"])
    if torch.cuda.is_available() and len(s["torch_cuda_all"]) > 0:
        assert len(s["torch_cuda_all"]) == torch.cuda.device_count(), \
            f"检查点 CUDA 设备数 {len(s['torch_cuda_all'])} 与当前 {torch.cuda.device_count()} 不符"
        torch.cuda.set_rng_state_all([t.cpu() for t in s["torch_cuda_all"]])
    np.random.set_state(s["numpy"])
    random.setstate(s["python"])
    gen.set_state(s["batch_gen"].cpu() if torch.is_tensor(s["batch_gen"]) else s["batch_gen"])


# =====================================================================================
# 精度 profile：与本章其他正式神经运行同一冻结 profile 才能科学比较
# =====================================================================================
_CONTRACT = precision.load_and_validate_contract(PRECISION_CONTRACT_PATH)
PROFILE_ID = precision.DEFAULT_PROFILE_ID
dev = "cuda" if torch.cuda.is_available() else "cpu"
assert dev == "cuda", "正式神经训练要求可用 CUDA（B76 GPU）"
_PROFILE = precision.validate_runtime_profile(_CONTRACT, PROFILE_ID, "cuda", torch)
log(f"精度 profile={PROFILE_ID} compute_dtype={_PROFILE['compute_dtype']} "
    f"autocast={_PROFILE['autocast']} grad_scaler={_PROFILE['grad_scaler']}")

# =====================================================================================
# 阶段一：只读入 LSPR23
# =====================================================================================
log("=" * 96)
log(f"运行身份 {RUN_ID}")
log(f"骨干 {BK} | 输出根 {OUT} | lr 网格 {LR_GRID} | {N_EPOCH} epoch × {EPOCH_STEPS} 步"
    f" | {'正式' if IS_PROD else '非正式（降规模）'}")
log("阶段一 lr-select + cells：只读入 LSPR23，LSPR24 不进入本进程")
X23 = np.load(f"{CACHE}/X23.npy")
y23 = np.load(f"{CACHE}/y23.npy")
I23 = np.load(f"{CACHE}/I23.npy")
M23 = np.load(f"{CACHE}/M23.npy")
E23 = np.load(f"{CACHE}/E23.npy")
T23 = np.load(f"{CACHE}/T23.npy")
assert X23.shape[1] == D, f"特征数应为 83（Dijk 2026 附录 A 口径），实为 {X23.shape[1]}"
log(f"LSPR23 流={len(y23):,} 特征数={D} 序列={len(I23):,}")

uent = np.unique(E23)
tr_idx, val_idx = split_lspr23_entity_disjoint(E23, T23, SEED, VAL_FRAC, TIME_TAIL)
log(f"LSPR23 实体 {len(uent):,} | 训练序列 {len(tr_idx):,} | 实体不相交验证 {len(val_idx):,}")
assert len(uent) == 150680, f"LSPR23 实体数自检失败：{len(uent)}"
assert len(tr_idx) == 208598, f"训练序列数自检失败：{len(tr_idx)}"
assert len(val_idx) == 22444, f"实体不相交验证序列数自检失败：{len(val_idx)}"
log("切分自检通过：150,680 实体 / 208,598 训练序列 / 22,444 验证序列，与协议 A 完全一致")

dev_t = torch.device(dev)
gX23 = torch.from_numpy(X23).to(dev)
gy23 = torch.from_numpy(y23).to(dev)
gI23 = torch.from_numpy(I23).to(dev)
gM23 = torch.from_numpy(M23).to(dev)
gtr = torch.from_numpy(tr_idx).to(dev)
gval = torch.from_numpy(val_idx).to(dev)
log(f"LSPR23 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

# ---- 修订一所需：LSPR23 全量（训练+验证+时间尾部）流到实体的映射，供验证期实体 AP 使用 ----
# 用 build_flow_entity(全量 I23/M23/E23) 而不是只用 val_idx，是因为该函数要求覆盖率满
# （每条流恰好落在一个实体），与 ch3_full_mlp_complete_entity_lp_protocol_a_q0.py 的
# evaluate_source_gate() 用法完全一致；验证期实际只会用到 val_idx 对应实体的分数（其余为 NaN）。
flow_entity23 = build_flow_entity(I23, M23, E23, len(y23))
entity_count23 = int(flow_entity23.max()) + 1
entity_labels23 = np.zeros(entity_count23, dtype=np.float32)
np.maximum.at(entity_labels23, flow_entity23, y23)
log(f"LSPR23 全量实体分组完成：{entity_count23:,} 个实体（用于验证期实体 AP 的选轮信号）")

# ---- 模型与损失：逐字照抄协议 A（ch3_full.py 第 150-172 行）----
_sl = (y23[I23.reshape(-1)].reshape(I23.shape) * M23).max(1) > 0
_spw = float((1 - _sl.mean()) / max(_sl.mean(), 1e-8))
_pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
_lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=_pos)
_bs = nn.BCELoss(reduction="none")
log(f"逐流 pos_weight={_pos.item():.6f}  序列级 spw={_spw:.6f}（口径照抄 ch3_full，用全量 LSPR23）")
del _sl


@torch.no_grad()
def val_metrics(net, lp):
    """LSPR23 实体不相交验证集：同时算实体 AP（修订一的选轮信号）与逐流 AP（仅记录）。

    实体级读出与目标年评价同规则：lp=True 用模型当前学到的 p 做 Lp 池化，
    lp=False 退化为逐实体取最大（与 evaluate_entity_branch 对 p_value=None 的语义一致）。
    """
    net.eval()
    sc = torch.zeros(len(y23), device=dev)
    sn = torch.zeros(len(y23), dtype=torch.bool, device=dev)
    for a in range(0, len(val_idx), 2048):
        sel = gval[a:a + 2048]; idx = gI23[sel][:, :L]; msk = gM23[sel][:, :L]; b = idx.shape[0]
        with precision.autocast_context(_PROFILE, dev, torch):
            lo = net(gX23[idx.reshape(-1)].reshape(b, L, D), msk)
        with precision.fp32_island(lo, device_type=dev, torch_module=torch) as (lo32,):
            pr = torch.sigmoid(lo32)
        fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
        sc[fi[fm]] = pr.reshape(-1)[fm]; sn[fi[fm]] = True
    net.train()
    sc_np = sc.cpu().numpy(); sn_np = sn.cpu().numpy()
    flow_ap = float(average_precision_score(y23[sn_np], sc_np[sn_np]))
    p_value = float(net.p.item()) if lp else None
    ent_sc = entity_scores(sc_np, sn_np, flow_entity23, entity_count23, p_value)
    ok = np.isfinite(ent_sc)
    assert ok.sum() > 0, "验证期实体评分为空，选轮信号无效"
    entity_ap = float(average_precision_score(entity_labels23[ok], ent_sc[ok]))
    return entity_ap, flow_ap, p_value


# =====================================================================================
# 实现验证（合成数据，真值由构造给定；不创建运行身份、不产生任何指标、不进结果表）
# 只验参数量：性质一（掩码决定性）与性质二（因果性）已由协议 A v2 对同一份 Model 实现
# 逐字验过（收据 runs/diagnostics/ch3-backbone-protocolA-v2/{backbone}/impl_verification.json，
# 三项判据全部 0.0），本文件与协议 A 现共用同一 ch3_backbone_models.Model，不重复验证。
# =====================================================================================
def _impl_verify():
    log("=" * 96)
    log("实现验证（合成数据，只核参数量；掩码/因果性质见协议 A v2 已有收据，共用同一 Model 不重跑）")
    rep = {"backbone_verified": BK, "shares_model_definition_with": "ch3_backbone_protocolA_v2"}
    want = npar_formula(BK)
    got = sum(p.numel() for p in Model(BK, True, True).parameters())
    assert got == want, f"{BK} 参数量公式 {want} 与 torch 实测 {got} 不一致"
    rep[f"npar_{BK}"] = got
    log(f"  参数量 {BK:<11} 公式={want:,} torch实测={got:,} 一致")
    atomic_json(rep, f"{OUT}/impl_verification.json")
    return rep


if ARGS.skip_impl_verify:
    log("已按 --skip-impl-verify 跳过实现验证（仅允许非正式输出根）")
    IMPL = {"skipped": True}
else:
    IMPL = _impl_verify()


def train_and_select(backbone, agg, lp, seed, lr, tag, cell_dir):
    """训练 N_EPOCH 个 epoch 不早停，逐 epoch 用 LSPR23 验证实体 AP 选检查点（修订一）；

    支持断点续训；lr 为参数化学习率（修订二），不再硬编码。
    函数体内不出现任何 LSPR24 标识符；此时进程内也没有 LSPR24 数据。
    """
    torch.manual_seed(seed); np.random.seed(seed)
    net = Model(backbone, agg, lp).to(dev)
    dec = [p for n, p in net.named_parameters() if not (n.endswith(".bias") or n == "p_log")]
    nod = [p for n, p in net.named_parameters() if (n.endswith(".bias") or n == "p_log")]
    opt = torch.optim.AdamW([{"params": dec, "weight_decay": 0.01},
                             {"params": nod, "weight_decay": 0.0}], lr=lr)
    precision.validate_model_optimizer_fp32(net, opt, torch)
    gen = torch.Generator().manual_seed(seed)
    best = {"entity_ap": -1.0, "flow_ap": None, "epoch": None, "p": None, "state": None}
    hist = []
    start_ep = 1
    prev_seconds = 0.0
    inflight = os.path.join(cell_dir, "inflight.pt")

    if os.path.exists(inflight):
        ck = load_ckpt(inflight)
        assert ck["tag"] == tag and ck["backbone"] == backbone, f"{tag} 在途检查点身份不符"
        assert ck["agg"] == agg and ck["lp"] == lp, f"{tag} 在途检查点 agg/lp 不符"
        assert ck["seed"] == seed, f"{tag} 在途检查点 seed 不符"
        assert abs(ck["lr"] - lr) < 1e-15, f"{tag} 在途检查点 lr 不符：{ck['lr']} vs {lr}"
        assert ck["n_epoch"] == N_EPOCH and ck["epoch_steps"] == EPOCH_STEPS, \
            f"{tag} 在途检查点训练预算不符：{ck['n_epoch']}×{ck['epoch_steps']}"
        assert ck["npar"] == npar_formula(backbone), f"{tag} 在途检查点参数量不符"
        assert len(ck["hist"]) == int(ck["epoch"]), \
            f"{tag} 在途检查点 hist 长度 {len(ck['hist'])} 与 epoch {ck['epoch']} 不符"
        assert [h[0] for h in ck["hist"]] == list(range(1, int(ck["epoch"]) + 1)), \
            f"{tag} 在途检查点 hist 的 epoch 序列不连续"
        net.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        best = ck["best"]
        hist = list(ck["hist"])
        prev_seconds = float(ck["train_seconds"])
        rng_restore(ck["rng"], gen)
        start_ep = int(ck["epoch"]) + 1
        log(f"  {tag} 从在途检查点恢复：已完成 epoch {ck['epoch']}，"
            f"当前最优 epoch={best['epoch']} 验证实体AP={best['entity_ap']:.6f}，"
            f"已用 {prev_seconds/60:.2f} 分，从 epoch {start_ep} 继续")
        if start_ep > N_EPOCH:
            log(f"  {tag} 全部 {N_EPOCH} 轮已在此前完成，只补写逐格完成检查点")

    t0 = time.time()
    net.train()
    for ep in range(start_ep, N_EPOCH + 1):
        for _ in range(EPOCH_STEPS):
            sel = gtr[torch.randint(0, len(tr_idx), (BS,), generator=gen).to(dev)]
            idx = gI23[sel][:, :L]; msk = gM23[sel][:, :L]
            xb = gX23[idx.reshape(-1)].reshape(BS, L, D)
            yb = gy23[idx.reshape(-1)].reshape(BS, L)
            opt.zero_grad(set_to_none=True)
            with precision.autocast_context(_PROFILE, dev, torch):
                lo = net(xb, msk)
            with precision.fp32_island(lo, yb, msk, device_type=dev, torch_module=torch) as (
                lo32, yb32, msk32,
            ):
                yb32 = yb32.float()
                loss = (_lf(lo32, yb32) * msk32).sum() / msk32.sum().clamp(min=1)
                if lp:
                    pr32 = torch.sigmoid(lo32)
                    sq = lp_pool(pr32, msk32, net.p).clamp(1e-6, 1 - 1e-6)
                    ysq = (yb32 * msk32).amax(1)
                    w = 1.0 + (_spw - 1.0) * ysq
                    loss = loss + AUX_W * ((_bs(sq, ysq) * w).sum() / w.sum())
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
        v_ent, v_flow, pv = val_metrics(net, lp)
        hist.append([ep, v_ent, v_flow, pv])
        star = ""
        if v_ent > best["entity_ap"]:
            best = {"entity_ap": v_ent, "flow_ap": v_flow, "epoch": ep, "p": pv,
                    "state": {k: t.detach().clone() for k, t in net.state_dict().items()}}
            star = "  ← 当前最优（按实体AP）"
        cum = prev_seconds + (time.time() - t0)
        atomic_torch_save({"tag": tag, "backbone": backbone, "cell": tag.split("-")[-1],
                           "agg": agg, "lp": lp, "seed": seed, "lr": lr,
                           "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS,
                           "npar": sum(p.numel() for p in net.parameters()),
                           "epoch": ep, "model": net.state_dict(), "opt": opt.state_dict(),
                           "best": best, "hist": hist, "train_seconds": cum,
                           "rng": rng_snapshot(gen)}, inflight)
        log(f"  {tag} ep {ep:>2}/{N_EPOCH} 验证实体AP={v_ent:.6f} 验证逐流AP={v_flow:.6f} "
            f"p={pv if pv is not None else float('nan'):.4f} 累计{cum/60:.1f}分{star}")
    tr_t = prev_seconds + (time.time() - t0)
    log(f"  {tag} 训练完成 {tr_t/60:.2f} 分，选中 epoch {best['epoch']}"
        f"（验证实体AP={best['entity_ap']:.6f} 验证逐流AP={best['flow_ap']:.6f}）")
    return best, hist, tr_t, sum(p.numel() for p in net.parameters())


# =====================================================================================
# 阶段一 lr-select：只在 C00 上，对 LR_GRID 每个候选各训练一次，用验证实体 AP 比较
# 禁止逐格选学习率，禁止依据目标年调整——此处只训练 C00，且此时 LSPR24 尚未进入本进程
# =====================================================================================
log("=" * 96)
log(f"lr-select 阶段：C00 在 {len(LR_GRID)} 个候选 lr 上各训练一次，"
    f"按 LSPR23 验证实体 AP 比较（修订一 + 修订二）")
_trained_rec = read_stage(PROG, "trained")
LR_RESULTS = {}
if FIXED_LR is not None:
    log(f"** 紧急操作指令：跳过 lr-select 两候选比较，直接冻结 lr={FIXED_LR:.10g}（协调方 GPU 窗口紧迫下达）**")
for idx, lr in enumerate(LR_GRID) if FIXED_LR is None else []:
    key = f"{BK}-lrselect-lr{idx}-C00"
    cell_dir = f"{LR_SELECT_DIR}/lr{idx}"
    os.makedirs(cell_dir, exist_ok=True)
    sel_path = f"{cell_dir}/selected.pt"
    if key in _trained_rec and os.path.exists(sel_path):
        s = load_ckpt(sel_path)
        assert s["backbone"] == BK and s["cell"] == "C00" and s["seed"] == SEED, f"{key} 逐格检查点身份不符"
        assert abs(s["lr"] - lr) < 1e-15, f"{key} 逐格检查点 lr 不符"
        assert s["agg"] is False and s["lp"] is False, f"{key} 逐格检查点 agg/lp 不符"
        assert s["n_epoch"] == N_EPOCH and s["epoch_steps"] == EPOCH_STEPS, f"{key} 逐格检查点训练预算不符"
        assert s["npar"] == npar_formula(BK), f"{key} 逐格检查点参数量不符"
        assert len(s["hist"]) == N_EPOCH, f"{key} 逐格检查点 hist 长度 {len(s['hist'])} 应为 {N_EPOCH}"
        LR_RESULTS[idx] = {"lr": lr, "entity_ap": s["entity_ap"], "flow_ap": s["flow_ap"],
                           "epoch": s["epoch"], "p": s["p"], "hist": s["hist"],
                           "train_seconds": s["train_seconds"], "state": s["state"], "npar": s["npar"]}
        log(f"--- {key} (lr={lr:.10g}) 已完成，跳过训练："
            f"选中 epoch={s['epoch']} 验证实体AP={s['entity_ap']:.6f} ---")
        continue
    log(f"--- {key} (lr={lr:.10g}) ---")
    best, hist, tr_t, npar = train_and_select(BK, False, False, SEED, lr, key, cell_dir)
    assert npar == npar_formula(BK), f"{key} 参数量 {npar} 与公式 {npar_formula(BK)} 不一致"
    atomic_torch_save({"backbone": BK, "cell": "C00", "agg": False, "lp": False, "seed": SEED, "lr": lr,
                       "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS, "npar": npar,
                       "epoch": best["epoch"], "entity_ap": best["entity_ap"], "flow_ap": best["flow_ap"],
                       "p": best["p"], "state": best["state"], "hist": hist,
                       "train_seconds": tr_t}, sel_path)
    append_jsonl(PROG, {"backbone": BK, "cell": "C00", "cell_key": key, "stage": "trained",
                        "lr": lr, "selected_epoch": best["epoch"], "entity_ap": best["entity_ap"],
                        "flow_ap": best["flow_ap"], "p": best["p"], "train_seconds": tr_t,
                        "npar": npar, "run_id": RUN_ID, "ts": time.time()})
    LR_RESULTS[idx] = {"lr": lr, "entity_ap": best["entity_ap"], "flow_ap": best["flow_ap"],
                       "epoch": best["epoch"], "p": best["p"], "hist": hist,
                       "train_seconds": tr_t, "state": best["state"], "npar": npar}

if FIXED_LR is None:
    assert len(LR_RESULTS) == len(LR_GRID), "lr-select 候选未全部完成"
    # 胜出规则：验证实体AP 最高者胜；并列则取更早收敛（epoch 更小）者；仍并列则取更大 lr
    # （与协议 A 原硬编码值 2e-3 保持最小偏离）。三级并列在真实随机训练下概率极低，
    # 该 tie-break 仅为工程确定性兜底，全过程落盘可审计，不依据目标年调整。
    _ranked = sorted(range(len(LR_GRID)),
                     key=lambda i: (-LR_RESULTS[i]["entity_ap"], LR_RESULTS[i]["epoch"], -LR_GRID[i]))
    WINNER_IDX = _ranked[0]
    WINNER_LR = LR_GRID[WINNER_IDX]
    _lr_select_frozen = {
        "run_id": RUN_ID, "backbone": BK, "seed": SEED,
        "mode": "two_candidate_entity_ap_comparison",
        "selection_metric": "lspr23_entity_disjoint_validation_entity_ap",
        "selection_rule": "single_epoch_argmax_earliest_tie_no_early_stopping",
        "lr_grid": list(LR_GRID),
        "candidates": {str(i): {"lr": LR_RESULTS[i]["lr"], "selected_epoch": LR_RESULTS[i]["epoch"],
                                "validation_entity_ap": LR_RESULTS[i]["entity_ap"],
                                "validation_flow_ap": LR_RESULTS[i]["flow_ap"],
                                "p_at_selection": LR_RESULTS[i]["p"],
                                "train_seconds": LR_RESULTS[i]["train_seconds"]}
                      for i in range(len(LR_GRID))},
        "winner_idx": WINNER_IDX, "winner_lr": WINNER_LR,
        "tie_break_rule": "max_entity_ap_then_min_epoch_then_max_lr",
    }
    atomic_json(_lr_select_frozen, f"{OUT}/lr_select_frozen.json")
    _lr_candidate_summary = [f"{LR_RESULTS[i]['lr']:.10g}:{LR_RESULTS[i]['entity_ap']:.6f}"
                             for i in range(len(LR_GRID))]
    log("=" * 96)
    log(f"lr-select 完成，胜出 lr={WINNER_LR:.10g}（候选 {_lr_candidate_summary}）")

    # ---- 把胜出候选的 C00 结果复制为正式格 C00（不重复训练，"零训练成本"复用）----
    C00_DIR = f"{CELLS_DIR}/{BK}-C00"
    os.makedirs(C00_DIR, exist_ok=True)
    _c00_sel_path = f"{C00_DIR}/selected.pt"
    _cells_trained_rec = read_stage(PROG, "trained")
    if f"{BK}-C00" not in _cells_trained_rec or not os.path.exists(_c00_sel_path):
        _winner = LR_RESULTS[WINNER_IDX]
        atomic_torch_save({"backbone": BK, "cell": "C00", "agg": False, "lp": False, "seed": SEED,
                           "lr": WINNER_LR, "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS,
                           "npar": _winner["npar"], "epoch": _winner["epoch"],
                           "entity_ap": _winner["entity_ap"], "flow_ap": _winner["flow_ap"],
                           "p": _winner["p"], "state": _winner["state"], "hist": _winner["hist"],
                           "train_seconds": _winner["train_seconds"],
                           "source_lr_select_candidate_idx": WINNER_IDX}, _c00_sel_path)
        append_jsonl(PROG, {"backbone": BK, "cell": "C00", "cell_key": f"{BK}-C00", "stage": "trained",
                            "lr": WINNER_LR, "selected_epoch": _winner["epoch"],
                            "entity_ap": _winner["entity_ap"], "flow_ap": _winner["flow_ap"],
                            "p": _winner["p"], "train_seconds": _winner["train_seconds"],
                            "npar": _winner["npar"], "run_id": RUN_ID,
                            "copied_from_lr_select_candidate": WINNER_IDX, "ts": time.time()})
        log(f"C00 正式格已由 lr-select 胜出候选（lr={WINNER_LR:.10g}）复制生成，未重复训练")
    else:
        log("C00 正式格已存在，跳过复制")
else:
    WINNER_IDX = None
    WINNER_LR = FIXED_LR
    _lr_select_frozen = {
        "run_id": RUN_ID, "backbone": BK, "seed": SEED,
        "mode": "directive_fixed_skip_comparison",
        "reason": "2026-08-27 服务器 GPU 窗口仅余约 2 小时，协调方下达紧急操作指令跳过两候选 lr "
                  "比较、直接冻结该 lr；未通过修订一指标（LSPR23 验证实体 AP）实际比较两个候选，"
                  "与合同预注册的选择程序不同，如实披露不隐藏。",
        "lr_grid": list(LR_GRID), "fixed_lr": FIXED_LR, "winner_lr": WINNER_LR,
        "candidates": {}, "winner_idx": None,
    }
    atomic_json(_lr_select_frozen, f"{OUT}/lr_select_frozen.json")
    log("=" * 96)
    log(f"lr-select 已按紧急操作指令跳过，直接冻结 lr={WINNER_LR:.10g}（未做两候选实体AP比较，"
        f"C00 将随 C01/C10/C11 一起正常训练）")

# =====================================================================================
# 阶段二 cells：C01/C10/C11 用冻结胜出 lr 各训练一次
# =====================================================================================
SEL = {}
log("=" * 96)
log(f"骨干 {BK}（隐藏维 {hid_of(BK)}，参数 {npar_formula(BK):,}）× 4 格，冻结 lr={WINNER_LR:.10g}，"
    f"seed={SEED}，{N_EPOCH} epoch × {EPOCH_STEPS} 步，不早停，串行训练")
if FIXED_LR is None:
    # C00 已通过 lr-select 胜出候选复制得到，计入"本次可用"但非"本进程训练"，不再进循环重训
    _TRAINED_NOW, _TRAINED_RESUMED = 1, 0
    _c00 = load_ckpt(_c00_sel_path)
    SEL["C00"] = {"backbone": BK, "cell": "C00", "agg": False, "lp": False,
                 "best": {"ap": _c00["entity_ap"], "epoch": _c00["epoch"], "p": _c00["p"],
                          "state": _c00["state"], "flow_ap": _c00["flow_ap"]},
                 "hist": _c00["hist"], "tr": _c00["train_seconds"], "npar": _c00["npar"]}
    _CELLS_TO_TRAIN = [t for t in ALL_CELLS if t[0] != "C00"]
else:
    # 紧急操作指令跳过 lr-select：C00 与 C01/C10/C11 一起正常走本循环训练
    _TRAINED_NOW, _TRAINED_RESUMED = 0, 0
    _CELLS_TO_TRAIN = list(ALL_CELLS)
_trained_rec = read_stage(PROG, "trained")
for cid, agg, lp in _CELLS_TO_TRAIN:
    key = f"{BK}-{cid}"
    cell_dir = f"{CELLS_DIR}/{key}"
    os.makedirs(cell_dir, exist_ok=True)
    sel_path = f"{cell_dir}/selected.pt"
    if key in _trained_rec and os.path.exists(sel_path):
        s = load_ckpt(sel_path)
        assert s["backbone"] == BK and s["cell"] == cid and s["seed"] == SEED, f"{key} 逐格检查点身份不符"
        assert s["agg"] == agg and s["lp"] == lp, f"{key} 逐格检查点 agg/lp 不符"
        assert abs(s["lr"] - WINNER_LR) < 1e-15, f"{key} 逐格检查点 lr 与冻结胜出 lr 不符"
        assert s["n_epoch"] == N_EPOCH and s["epoch_steps"] == EPOCH_STEPS, f"{key} 逐格检查点训练预算不符"
        assert s["npar"] == npar_formula(BK), f"{key} 逐格检查点参数量不符"
        assert len(s["hist"]) == N_EPOCH, f"{key} 逐格检查点 hist 长度 {len(s['hist'])} 应为 {N_EPOCH}"
        SEL[cid] = {"backbone": BK, "cell": cid, "agg": agg, "lp": lp,
                    "best": {"ap": s["entity_ap"], "epoch": s["epoch"], "p": s["p"],
                             "state": s["state"], "flow_ap": s["flow_ap"]},
                    "hist": s["hist"], "tr": s["train_seconds"], "npar": s["npar"]}
        _TRAINED_RESUMED += 1
        log(f"--- {key} (agg={agg}, lp={lp}) 已完成，跳过训练："
            f"选中 epoch={s['epoch']} 验证实体AP={s['entity_ap']:.6f} ---")
        continue
    log(f"--- {key} (agg={agg}, lp={lp}) lr={WINNER_LR:.10g} ---")
    best, hist, tr_t, npar = train_and_select(BK, agg, lp, SEED, WINNER_LR, key, cell_dir)
    assert npar == npar_formula(BK), f"{key} 参数量 {npar} 与公式 {npar_formula(BK)} 不一致"
    atomic_torch_save({"backbone": BK, "cell": cid, "agg": agg, "lp": lp, "seed": SEED, "lr": WINNER_LR,
                       "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS, "npar": npar,
                       "epoch": best["epoch"], "entity_ap": best["entity_ap"], "flow_ap": best["flow_ap"],
                       "p": best["p"], "state": best["state"], "hist": hist,
                       "train_seconds": tr_t}, sel_path)
    append_jsonl(PROG, {"backbone": BK, "cell": cid, "cell_key": key, "stage": "trained",
                        "lr": WINNER_LR, "selected_epoch": best["epoch"], "entity_ap": best["entity_ap"],
                        "flow_ap": best["flow_ap"], "p": best["p"], "train_seconds": tr_t,
                        "npar": npar, "run_id": RUN_ID, "ts": time.time()})
    _TRAINED_NOW += 1
    SEL[cid] = {"backbone": BK, "cell": cid, "agg": agg, "lp": lp,
               "best": {"ap": best["entity_ap"], "epoch": best["epoch"], "p": best["p"],
                        "state": best["state"], "flow_ap": best["flow_ap"]},
               "hist": hist, "tr": tr_t, "npar": npar}

# =====================================================================================
# 阶段闸门：从磁盘重新推导，再把选择结果写盘冻结，之后才允许读入 LSPR24
# =====================================================================================
def gate_from_disk():
    ev = {}
    rec = read_stage(PROG, "trained")
    for cid, _, _ in ALL_CELLS:
        k = f"{BK}-{cid}"
        p = f"{CELLS_DIR}/{k}/selected.pt"
        ev[k] = {"in_progress_jsonl": k in rec, "selected_pt_exists": os.path.exists(p)}
    ok = all(v["in_progress_jsonl"] and v["selected_pt_exists"] for v in ev.values())
    return ok, ev


SELECTION_FROZEN, _GATE_EVIDENCE = gate_from_disk()
_GATE_DERIVED_AT = time.time()
assert SELECTION_FROZEN, f"阶段闸门未开（磁盘推导）：{_GATE_EVIDENCE}"
assert len(SEL) == 4, f"闸门已开但进程内只有 {len(SEL)} 格，制品与内存不一致"
assert TARGET_YEAR_ARRAYS_READ == 0, f"源年阶段目标年数组读取计数应为 0，实为 {TARGET_YEAR_ARRAYS_READ}"

_frozen = {"protocol": "协议B：逐epoch在LSPR23实体不相交验证集上取实体AP最大的epoch（并列取最早），"
                       "无末轮平均，不早停；lr 由 C00 两候选比较冻结",
           "run_id": RUN_ID, "backbone": BK, "seed": SEED, "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS,
           "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
           "winner_lr": WINNER_LR, "lr_select": _lr_select_frozen,
           "gate_evidence": _GATE_EVIDENCE,
           "cells": {c: {"backbone": SEL[c]["backbone"], "cell_id": SEL[c]["cell"],
                        "selected_epoch": SEL[c]["best"]["epoch"],
                        "val_entity_ap_at_selected": SEL[c]["best"]["ap"],
                        "val_flow_ap_at_selected": SEL[c]["best"]["flow_ap"],
                        "p_at_selected": SEL[c]["best"]["p"],
                        "val_history_epoch_entity_flow_p": SEL[c]["hist"],
                        "train_seconds": SEL[c]["tr"]} for c in SEL}}
atomic_json(_frozen, f"{OUT}/selection_frozen.json")
log("=" * 96)
log(f"选择阶段结束（闸门由磁盘推导），结果已冻结写盘 {OUT}/selection_frozen.json")
log(f"本次进程训练 {_TRAINED_NOW} 格，从磁盘恢复 {_TRAINED_RESUMED} 格")
for c in SEL:
    log(f"  {c}: 选中 epoch={SEL[c]['best']['epoch']:>2} 验证实体AP={SEL[c]['best']['ap']:.6f} "
        f"验证逐流AP={SEL[c]['best']['flow_ap']:.6f}")

del gX23, gy23, gI23, gM23, gtr, gval, X23, y23, I23, M23, E23, T23
torch.cuda.empty_cache()
log(f"LSPR23 已释放，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

# =====================================================================================
# 阶段三：此刻才第一次读入 LSPR24，每格只评价一次
# =====================================================================================
assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段读入 LSPR24"
assert _GATE_DERIVED_AT is not None and _GATE_DERIVED_AT <= time.time(), "闸门推导时刻缺失"
assert TARGET_YEAR_ARRAYS_READ == 0, f"LSPR24 在闸门开启前已被读入，计数={TARGET_YEAR_ARRAYS_READ}"
log("=" * 96)
log("阶段三 目标评价：首次读入 LSPR24（选择已冻结）")
X24 = np.load(f"{CACHE}/X24.npy"); TARGET_YEAR_ARRAYS_READ += 1
y24 = np.load(f"{CACHE}/y24.npy"); TARGET_YEAR_ARRAYS_READ += 1
I24 = np.load(f"{CACHE}/I24.npy"); TARGET_YEAR_ARRAYS_READ += 1
M24 = np.load(f"{CACHE}/M24.npy"); TARGET_YEAR_ARRAYS_READ += 1
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True); TARGET_YEAR_ARRAYS_READ += 1
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True); TARGET_YEAR_ARRAYS_READ += 1
t24 = np.load(f"{CACHE}/t24.npy"); TARGET_YEAR_ARRAYS_READ += 1
assert TARGET_YEAR_ARRAYS_READ == 7, f"目标年数组读取计数应为 7，实为 {TARGET_YEAR_ARRAYS_READ}"
assert X24.shape[1] == D

key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
_flow_pos = float(y24.astype(np.float64).mean())
log(f"LSPR24 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 实体先验={ent_lab.mean():.10f} 逐流正例率={_flow_pos:.10f}")
assert N_ENT == 47115, f"LSPR24 实体数自检失败：{N_ENT}"
assert int(ent_lab.sum()) == 752, f"LSPR24 正例实体自检失败：{int(ent_lab.sum())}"
assert abs(_flow_pos - 0.0257073138) < 1e-9, f"LSPR24 逐流正例率自检失败：{_flow_pos:.12f}"
log("LSPR24 自检通过：实体 47,115 / 正例实体 752 / 逐流正例率 0.0257073138")
del key24, s24, d24, t24

gX24 = torch.from_numpy(X24).to(dev)
gI24 = torch.from_numpy(I24).to(dev)
gM24 = torch.from_numpy(M24).to(dev)
del X24
log(f"LSPR24 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


@torch.no_grad()
def score24(net):
    """LSPR24 逐流打分：与协议 A 的 score24() 同一批处理与掩码口径。"""
    global _EVAL24_CALLS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段评价 LSPR24"
    _EVAL24_CALLS += 1
    net.eval()
    sc = torch.zeros(len(y24), device=dev)
    sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    for a in range(0, len(I24), 2048):
        idx = gI24[a:a + 2048][:, :L]; msk = gM24[a:a + 2048][:, :L]; b = idx.shape[0]
        with precision.autocast_context(_PROFILE, dev, torch):
            lo = net(gX24[idx.reshape(-1)].reshape(b, L, D), msk)
        with precision.fp32_island(lo, device_type=dev, torch_module=torch) as (lo32,):
            pr = torch.sigmoid(lo32)
        fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
        sc[fi[fm]] = pr.reshape(-1)[fm]; sn[fi[fm]] = True
    return sc.cpu().numpy(), sn.cpu().numpy()


RES = {}
_eval_rec = read_stage(EVAL_PROG, "evaluated")
log("=" * 96)
log("每格加载选中 epoch 的权重，在 LSPR24 上评价一次（已评价的格跳过）；"
    "实体级读出复用 ch3_full_mlp_complete_entity_lp_protocol_a_q0.evaluate_entity_branch")
for cid, agg, lp in ALL_CELLS:
    key = f"{BK}-{cid}"
    eval_json = f"{CELLS_DIR}/{key}/eval.json"
    if key in _eval_rec and os.path.exists(eval_json):
        r = json.load(open(eval_json, encoding="utf-8"))
        assert r["backbone"] == BK and r["cell"] == cid, f"{key} eval.json 身份不符"
        assert r["agg"] == agg and r["lp"] == lp, f"{key} eval.json agg/lp 不符"
        assert r["sel_epoch"] == SEL[cid]["best"]["epoch"], \
            f"{key} eval.json 选中 epoch {r['sel_epoch']} 与 selected.pt {SEL[cid]['best']['epoch']} 不符"
        assert abs(r["val_entity_ap"] - SEL[cid]["best"]["ap"]) < 1e-12, f"{key} eval.json 验证实体AP 与 selected.pt 不符"
        assert r["npar"] == SEL[cid]["npar"], f"{key} eval.json 参数量不符"
        RES[key] = r
        _EVAL24_RESUMED += 1
        log(f"{key}: 已评价，跳过（实体AP(主)={r['target']['entity_average_precision']:.6f} "
            f"DR@4%FPR={r['target']['dr_at_fpr']['fpr_0.04']:.6f}）")
        continue
    assert key not in _EVAL24_KEYS, f"{key} 在本进程内被重复评价"
    _EVAL24_KEYS.add(key)
    net = Model(BK, agg, lp).to(dev)
    net.load_state_dict(SEL[cid]["best"]["state"])
    p = net.p.item()
    assert abs(p - SEL[cid]["best"]["p"]) < 1e-9, f"{key} 权重回载后 p 不一致"
    t1 = time.time()
    sc, seen = score24(net)
    ev_t = time.time() - t1
    p_value = p if lp else None
    metrics, ent_sc, curve = evaluate_entity_branch(sc, seen, y24, ent24, ent_lab, p_value, list(DR_FPR_GRID))
    RES[key] = {"backbone": BK, "cell": cid, "agg": agg, "lp": lp,
               "sel_epoch": SEL[cid]["best"]["epoch"],
               "val_entity_ap": SEL[cid]["best"]["ap"], "val_flow_ap": SEL[cid]["best"]["flow_ap"],
               "p": p, "npar": SEL[cid]["npar"], "tr": SEL[cid]["tr"], "ev": ev_t,
               "target": metrics}
    log(f"{key}: epoch={SEL[cid]['best']['epoch']:>2} 验证实体AP={SEL[cid]['best']['ap']:.6f} p={p:.4f} | "
        f"目标年逐流AP={metrics['flow_average_precision']:.6f} 实体AP(主)={metrics['entity_average_precision']:.6f} "
        f"实体AP(max)={metrics['maximum_entity_average_precision']:.6f} "
        f"DR@4%FPR={metrics['dr_at_fpr']['fpr_0.04']:.6f} 覆盖实体={metrics['entities_scored']:,} "
        f"训练{SEL[cid]['tr']/60:.2f}分 推理{ev_t:.1f}秒")
    if cid == "C11":
        atomic_npy(sc, f"{OUT}/scores_{BK}_C11.npy")
        atomic_npy(seen, f"{OUT}/seen_{BK}_C11.npy")
    atomic_json(RES[key], eval_json)
    append_jsonl(EVAL_PROG, {"backbone": BK, "cell": cid, "cell_key": key, "stage": "evaluated",
                             "entity_ap_main": metrics["entity_average_precision"],
                             "dr_at_4pct_fpr": metrics["dr_at_fpr"]["fpr_0.04"],
                             "flow_ap": metrics["flow_average_precision"], "run_id": RUN_ID,
                             "ts": time.time()})
    del sc, seen, net
    torch.cuda.empty_cache()

_N_EXPECT = len(ALL_CELLS)
assert _EVAL24_CALLS == len(_EVAL24_KEYS), \
    f"本进程 score24 调用 {_EVAL24_CALLS} 次但只有 {len(_EVAL24_KEYS)} 格，存在重复评价"
assert _EVAL24_CALLS + _EVAL24_RESUMED == _N_EXPECT, \
    f"评价覆盖应为 {_N_EXPECT} 格（本次 {_EVAL24_CALLS} + 恢复 {_EVAL24_RESUMED}）"
assert set(RES) == {f"{BK}-{c}" for c, _, _ in ALL_CELLS}, "评价结果的格集合不完整"
log(f"隔离断言通过：LSPR24 磁盘读入数组 {TARGET_YEAR_ARRAYS_READ} 个，本进程评价 {_EVAL24_CALLS} 次、"
    f"从磁盘恢复 {_EVAL24_RESUMED} 格，合计 {_N_EXPECT} 格恰各一次，均发生在选择冻结之后")

# =====================================================================================
# 判据（预注册，与合同一致，不再改动）：C01>C00 且 C10>C00 且 C11>=max(C01,C10)
# 主口径 = evaluate_entity_branch 的 entity_average_precision（lp 格用 Lp 池化，非 lp 格退化为 max，
# 与协议 A 的 e_lp 字段语义完全一致）
# =====================================================================================
C_MAIN = {cid: RES[f"{BK}-{cid}"]["target"]["entity_average_precision"] for cid, _, _ in ALL_CELLS}
crit_elp = C_MAIN["C01"] > C_MAIN["C00"]
crit_cpa = C_MAIN["C10"] > C_MAIN["C00"]
crit_joint = C_MAIN["C11"] >= max(C_MAIN["C01"], C_MAIN["C10"])
JUDGMENT_PASSED = bool(crit_elp and crit_cpa and crit_joint)
log("=" * 96)
log(f"【{BK} 判据（预注册，主口径实体AP）】C00={C_MAIN['C00']:.6f} C01={C_MAIN['C01']:.6f} "
    f"C10={C_MAIN['C10']:.6f} C11={C_MAIN['C11']:.6f}")
log(f"  判据一 C01>C00（仅ELP）: {'通过' if crit_elp else '不通过'}（{(C_MAIN['C01']-C_MAIN['C00'])*100:+.4f} 点）")
log(f"  判据二 C10>C00（仅CPA）: {'通过' if crit_cpa else '不通过'}（{(C_MAIN['C10']-C_MAIN['C00'])*100:+.4f} 点）")
log(f"  判据三 C11>=max(C01,C10): {'通过' if crit_joint else '不通过'}"
    f"（C11 - max = {(C_MAIN['C11']-max(C_MAIN['C01'],C_MAIN['C10']))*100:+.4f} 点）")
log(f"  ★ {BK} 三项判据{'全部通过，纳入判据' if JUDGMENT_PASSED else '未全部通过，按 U6 定案剔除，不再追调不重跑'}")

FINAL = {"protocol": _frozen["protocol"], "run_id": RUN_ID, "seed": SEED, "backbone": BK,
        "winner_lr": WINNER_LR, "lr_select": _lr_select_frozen,
        "hid": hid_of(BK), "npar": npar_formula(BK),
        "impl_verification": IMPL,
        "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
        "lspr24": {"n_entity": int(N_ENT), "n_pos_entity": int(ent_lab.sum()),
                  "flow_pos_rate": _flow_pos},
        "cells": RES, "selection": _frozen["cells"],
        "judgment": {"selection_metric": "lspr23_entity_disjoint_validation_entity_ap",
                    "readout_field": "entity_average_precision",
                    "C00": C_MAIN["C00"], "C01": C_MAIN["C01"], "C10": C_MAIN["C10"], "C11": C_MAIN["C11"],
                    "crit_elp_c01_gt_c00": bool(crit_elp), "crit_cpa_c10_gt_c00": bool(crit_cpa),
                    "crit_joint_c11_ge_max": bool(crit_joint), "passed": JUDGMENT_PASSED},
        "resume": {"cells_trained_this_process": _TRAINED_NOW,
                  "cells_resumed_from_disk": _TRAINED_RESUMED,
                  "cells_evaluated_this_process": _EVAL24_CALLS,
                  "cells_eval_resumed_from_disk": _EVAL24_RESUMED,
                  "gate_evidence": _GATE_EVIDENCE},
        "isolation": {"target_year_arrays_read": TARGET_YEAR_ARRAYS_READ,
                     "lspr24_evals_this_process": _EVAL24_CALLS,
                     "lspr24_evals_resumed": _EVAL24_RESUMED,
                     "lspr24_evals_total": _EVAL24_CALLS + _EVAL24_RESUMED},
        "precision": {"profile_id": PROFILE_ID, "compute_dtype": _PROFILE["compute_dtype"],
                     "autocast": _PROFILE["autocast"], "grad_scaler": _PROFILE["grad_scaler"]}}
atomic_json(FINAL, f"{OUT}/ch3_backbone_protocolB_results.json")
log(f"全部结果已存 {OUT}/ch3_backbone_protocolB_results.json")

# =====================================================================================
# SwanLab（正式 GPU 实验用在线模式；workspace/project 抄自本章既有冻结配置，
# 三次重试失败则降级 local 并如实记录，不让遥测抖动作废真实训练结果）
# =====================================================================================
SWAN_WORKSPACE, SWAN_PROJECT = "mortiswang", "malicious-traffic-llm"
try:
    import swanlab
    _sw, _sw_mode = None, "online"
    for _try in range(3):
        try:
            _sw = swanlab.init(workspace=SWAN_WORKSPACE, project=SWAN_PROJECT, name=RUN_ID,
                               mode="online",
                               config={"run_id": RUN_ID, "backbone": BK, "seed": SEED,
                                      "winner_lr": WINNER_LR, "lr_grid": list(LR_GRID),
                                      "protocol": "backbone_2x2_rerun_protocol_b",
                                      "selection_metric": "lspr23_entity_disjoint_validation_entity_ap",
                                      "precision_profile_id": PROFILE_ID})
            break
        except Exception as e:
            log(f"  SwanLab 建 run 失败（第 {_try+1}/3 次）：{type(e).__name__}: {e}")
            time.sleep(10 * (_try + 1))
    if _sw is None:
        _sw_mode = "local"
        _sw = swanlab.init(project=SWAN_PROJECT, name=RUN_ID, mode="local",
                           config={"run_id": RUN_ID, "backbone": BK})
        log("  SwanLab 三次建 run 均失败，本次降级为 local 模式，结果照常落盘")
    log(f"  SwanLab[{_sw_mode}]: id={_sw.id} name={_sw.name}")
    _metrics = {}
    for cid, _, _ in ALL_CELLS:
        r = RES[f"{BK}-{cid}"]
        _metrics[f"select/{cid}_epoch"] = float(r["sel_epoch"])
        _metrics[f"select/{cid}_val_entity_ap"] = float(r["val_entity_ap"])
        _metrics[f"select/{cid}_val_flow_ap"] = float(r["val_flow_ap"])
        _metrics[f"target/{cid}_entity_ap_main"] = float(r["target"]["entity_average_precision"])
        _metrics[f"target/{cid}_flow_ap"] = float(r["target"]["flow_average_precision"])
        _metrics[f"target/{cid}_dr_4pct_fpr"] = float(r["target"]["dr_at_fpr"]["fpr_0.04"])
    _metrics["judgment/passed"] = float(JUDGMENT_PASSED)
    _metrics["judgment/crit_elp"] = float(crit_elp)
    _metrics["judgment/crit_cpa"] = float(crit_cpa)
    _metrics["judgment/crit_joint"] = float(crit_joint)
    _metrics["winner_lr"] = float(WINNER_LR)
    swanlab.log(_metrics, step=0)
    swanlab.finish()
    FINAL["swanlab"] = {"mode": _sw_mode, "id": _sw.id, "name": _sw.name}
    atomic_json(FINAL, f"{OUT}/ch3_backbone_protocolB_results.json")
except Exception as e:  # noqa: BLE001 — 遥测失败不得作废已完成的真实训练与评价
    log(f"SwanLab 记录失败（不影响已落盘的训练与评价结果）：{type(e).__name__}: {e}")

log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
