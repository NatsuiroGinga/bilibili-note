# -*- coding: utf-8 -*-
"""第三章基座对照（协议 A）v2：**按骨干独立运行 + 断点续训**。

本文件由 tools/ch3_backbone_protocolA.py 复制后**只增加持久化与运行编排**，
不改动任何选择语义、训练语义或指标语义。

v1 的教训（2026-08-17）：20 个格的权重全压在内存里，要等全部训完才写 selection_frozen.json，
磁盘上一个权重都没有。实例在 2 小时 46 分宕机，已训完的 14 格（GRU 四格 26.2 分、
Transformer 四格 15.7 分、一维 CNN 四格 9.0 分、RWKV-7 两格 88.5 分）全部作废。
v1 幸存的 runs/diagnostics/ch3-backbone-protocolA/impl_verification.json 已证明四个骨干实现正确
（参数量 gru 90,134 / transformer 90,631 / cnn 91,082 / rwkv7 91,730；掩码决定性、补零位输出、
因果性三项对四个骨干全部为 0.0），故 v2 不重写模型代码。

================= v2 相对 v1 的全部改动（逐条列出，便于核对协议同一性）=================
【A 类 只增加持久化，不触碰语义】
  A1 原子写：所有落盘一律先写 <path>.tmp、flush、fsync，再 os.replace(<path>.tmp, <path>)。
  A2 逐轮在途检查点 cells/{backbone}-{cell}/inflight.pt，每个 epoch 结束后覆盖写。
     含 epoch / model.state_dict / optimizer.state_dict / best / hist / 累计训练秒数
     以及**全部 RNG 状态**：torch.get_rng_state、torch.cuda.get_rng_state_all、
     np.random.get_state、random.getstate、批采样 torch.Generator 的 gen.get_state。
     最后一项是关键：训练循环里的 gen 决定每一批取哪些序列，不存它恢复后取到的批次就会偏离。
  A3 逐格完成检查点 cells/{backbone}-{cell}/selected.pt，并向 progress.jsonl 追加 stage=trained。
  A4 评价阶段逐格落盘 cells/{backbone}-{cell}/eval.json，并向 eval_progress.jsonl 追加 stage=evaluated。
  A5 恢复逻辑：已 trained 的格跳过训练、直接载入 selected.pt；有 inflight.pt 但未 trained 的格
     从 epoch+1 继续，**先恢复全部 RNG 状态再继续**；已 evaluated 的格跳过评价、直接载入 eval.json。
【B 类 只改运行编排，不触碰语义】
  B1 新增 --backbone，一个进程只管一个骨干的四格加评价加落盘。
     四格之间本来就相互独立（train_and_select 首行 torch.manual_seed(seed) 重置全部 RNG），
     骨干之间同理，因此拆进程不改变任何一格的数值结果，只改变失败的爆炸半径。
  B2 输出根改为 runs/diagnostics/ch3-backbone-protocolA-v2/{backbone}/。
  B3 阶段闸门 SELECTION_FROZEN **从磁盘重新推导**（四格 progress 都为 trained 且 selected.pt 都在
     才置真），不从任何文件里读一个可能过期的布尔值。
  B4 每个进程内 LSPR24 仍只加载一次，仍只在闸门开后加载；已评价的格不重复评价。
     原有全部隔离断言保留，并针对恢复路径新增 R1-R6 六条（见代码中「恢复路径断言」注释）。
  B5 _impl_verify 的参数量核对仍覆盖全部五个骨干（廉价），掩码/因果性质只验本进程的骨干
     （v1 已对四个骨干全部验过并留有收据）。
【C 类 纯报告，不参与训练、选择、闸门与任何指标计算】
  C1 逐 epoch 日志的「累计 N 分」改为跨重启累计。
  C2 交互项、MLP 参照、XGB 参照只对本进程的骨干打印。
【不变量：以下一律逐字保持 v1】
  切分代码、val_ap()、训练循环、优化器、损失、AUX_W、梯度裁剪、best 更新规则、
  LSPR24 评价与指标计算（含 float32 对齐）、
  SEED / N_EPOCH / EPOCH_STEPS / BS / lr / VAL_FRAC / AUX_W / L、
  五个骨干的隐藏维与参数量公式。
=====================================================================================

协议 A 定义（与 ch3_2x2_fairsel.py 完全一致）：
  逐 epoch 在 LSPR23 实体不相交验证集上算逐流 AP，取 AP 最大的那个**单个** epoch 的检查点，
  不做任何平均、不早停、训满 20 epoch。

MLP 骨干不在本脚本重跑；其协议 A 四格数字在阶段二从冻结制品
runs/diagnostics/ch3-2x2-fairsel/ch3_2x2_fairsel_results.json 只读读取并硬校验。

============================ LSPR24 隔离保证（本任务的核心）============================
不是靠注释约定，是靠**加载顺序**与**机械断言**：

  阶段一「选择」：进程内只从磁盘读入 LSPR23（X23/y23/I23/M23/E23/T23）。
                  本骨干四格全部训练完，逐 epoch 只在 LSPR23 验证集上打分并选出 epoch，
                  随后把「每格选中的 epoch + 该 epoch 的验证 AP」写盘冻结。
                  此刻 LSPR24 的任何数组**根本不存在于本进程**——没有 open()，没有 np.load()。
  阶段闸门      ：SELECTION_FROZEN 由磁盘推导为 True，且 selection_frozen.json 已落盘。
  阶段二「评价」：LSPR24 的 np.load 之前先断言 SELECTION_FROZEN。
                  score24() 首行同样断言，并对每格计数，最后断言本进程评价次数加恢复次数 == 4。
                  MLP 参照 JSON（含 LSPR24 指标）同样只在闸门之后读取。

  训练/选择函数 train_and_select() 的函数体内不出现任何 24 相关标识符；
  它只能访问模块级的 gX23/gy23/gI23/gM23/gtr/gval。
  按骨干拆进程后，每个进程在自己冻结前从未见过 LSPR24，隔离比 v1 的单进程二十格更干净。
=====================================================================================
"""

import argparse
import json
import math
import os
import random
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
PROD_OUT_ROOT = f"{ROOT}/runs/diagnostics/ch3-backbone-protocolA-v2"
MLP_REF = (f"{ROOT}/runs/diagnostics/ch3-2x2-fairsel/ch3_2x2_fairsel_results.json")

ALL_CELLS = [("C00", False, False), ("C01", False, True),
             ("C10", True, False), ("C11", True, True)]

_ap = argparse.ArgumentParser(description="第三章基座对照协议 A v2：单骨干、可断点续训")
_ap.add_argument("--backbone", required=True, choices=["gru", "transformer", "cnn", "rwkv7"],
                 help="本进程负责的骨干；一个进程只跑一个骨干的四格")
_ap.add_argument("--out-root", default=PROD_OUT_ROOT, help="输出根；正式运行不要改")
_ap.add_argument("--n-epoch", type=int, default=20, help="仅供实现验证降规模用；正式运行必须 20")
_ap.add_argument("--epoch-steps", type=int, default=1000, help="仅供实现验证降规模用；正式运行必须 1000")
_ap.add_argument("--cells", default="C00,C01,C10,C11", help="仅供实现验证降规模用；正式运行必须四格全跑")
_ap.add_argument("--skip-impl-verify", action="store_true", help="仅供实现验证降规模用；正式运行禁止")
ARGS = _ap.parse_args()

BK = ARGS.backbone
OUT = os.path.join(os.path.abspath(ARGS.out_root), BK)
IS_PROD = os.path.abspath(ARGS.out_root) == os.path.abspath(PROD_OUT_ROOT)
CELL_SEL = [c.strip() for c in ARGS.cells.split(",") if c.strip()]
CELLS = [t for t in ALL_CELLS if t[0] in CELL_SEL]
assert len(CELLS) == len(CELL_SEL), f"未知格：{set(CELL_SEL) - {t[0] for t in ALL_CELLS}}"

# ---- 正式输出根的降规模防护：不允许用调试参数污染正式运行目录 ----
if IS_PROD:
    assert ARGS.n_epoch == 20, f"正式运行 n_epoch 必须为 20，实为 {ARGS.n_epoch}"
    assert ARGS.epoch_steps == 1000, f"正式运行 epoch_steps 必须为 1000，实为 {ARGS.epoch_steps}"
    assert len(CELLS) == 4, "正式运行必须四格全跑"
    assert not ARGS.skip_impl_verify, "正式运行禁止跳过实现验证"

RUN_ID = f"ch3-backbone-protocolA-v2-{BK}-2x2-seed42"
CELLS_DIR = f"{OUT}/cells"
PROG = f"{OUT}/progress.jsonl"
EVAL_PROG = f"{OUT}/eval_progress.jsonl"
os.makedirs(CELLS_DIR, exist_ok=True)

# ---- 超参：逐字照抄 ch3_full.py 第 52、106-107 行 ----
L, BS, HID = 128, 64, 192
SEED, AUX_W = 42, 1.0
EPOCH_STEPS = ARGS.epoch_steps
N_EPOCH = ARGS.n_epoch            # 20 epoch × 1000 步 = 20000 步，与冻结预算相同
# ---- 验证划分：逐字照抄 select_signal.py 第 103 行 ----
VAL_FRAC, TIME_TAIL = 0.10, 0.15

# ---- 骨干隐藏维（唯一新增的超参，只为对齐 MLP 的 90,242 参数预算）----
MLP_NPAR = 90242
GRU_HID = 111                     # 5h² + (3D+8)h + 2 = 90,134，偏 -0.120%
TR_D, TR_HEADS = 77, 7            # 6d² + 2·d·ff + ff + (D+12)d + 2 = 90,631，偏 +0.431%；head_dim = 11
TR_FF = 4 * TR_D                  # 标准 4× 前馈宽度 = 308
CNN_C, CNN_K, CNN_LAYERS = 92, 3, 3   # (2k+2)c² + (kD+5)c + 2 = 91,082，偏 +0.931%
RWKV_C, RWKV_HEAD, RWKV_LORA = 112, 16, 8   # 6C² + 6·C·lora + (D+16)C + 2 = 91,730，偏 +1.649%
ALL_BACKBONES = ["gru", "transformer", "cnn", "rwkv7"]

# ---- 阶段闸门与计数器 ----
SELECTION_FROZEN = False
_N24_LOADS = 0
_EVAL24_CALLS = 0
_EVAL24_RESUMED = 0
_EVAL24_KEYS = set()
_GATE_DERIVED_AT = None


# =====================================================================================
# 持久化原语：一律先写 .tmp、fsync、再 os.replace（POSIX rename 原子，断电不留半截文件）
# torch 2.13.0+cu130 实测：os.replace(src, dst, *, src_dir_fd=None, dst_dir_fd=None)
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
    """读 jsonl 台账，按 cell_key 取该 stage 的最后一条记录。"""
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
                continue          # 断电可能留下半行；半行不算完成，重跑该格
            if r.get("stage") == stage and r.get("cell_key"):
                out[r["cell_key"]] = r
    return out


# torch 2.13.0+cu130 实测：torch.load 默认 weights_only=True，
# 载入含 np.random.get_state() 与 random.getstate() 的检查点会抛 UnpicklingError，必须显式关掉。
def load_ckpt(path):
    return torch.load(path, map_location="cpu", weights_only=False)


# =====================================================================================
# RNG 快照与恢复
# torch 2.13.0+cu130 实测签名与返回：
#   torch.get_rng_state() -> Tensor uint8 (5056,)          ；torch.set_rng_state(state)
#   torch.cuda.get_rng_state_all() -> list[Tensor uint8 (16,)]；torch.cuda.set_rng_state_all(states)
#   torch.Generator().get_state() -> Tensor uint8 (5056,)  ；Generator.set_state(state)（往返实测一致）
# =====================================================================================
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
# 阶段一：只读入 LSPR23
# =====================================================================================
log("=" * 96)
log(f"运行身份 {RUN_ID}")
log(f"骨干 {BK} | 输出根 {OUT} | {N_EPOCH} epoch × {EPOCH_STEPS} 步 | 格 {[c[0] for c in CELLS]}"
    f" | {'正式' if IS_PROD else '非正式（降规模）'}")
log("阶段一 选择：只读入 LSPR23，LSPR24 不进入本进程")
# 数据身份：X23/X24 是 dijk 复现管线标准化后的特征矩阵（非有限值置 0 → 按 LSPR23 逐列均值和
# 标准差标准化 → 裁剪 [-10, 10]），不是 raw83 原值；形状、dtype 与文件字节数都与 raw83 产品相同
# 但内容不同。只有训练侧同样消费这份缓存的模型才可直接用。见该缓存目录的 README.md。
X23 = np.load(f"{CACHE}/X23.npy")
y23 = np.load(f"{CACHE}/y23.npy")
I23 = np.load(f"{CACHE}/I23.npy")
M23 = np.load(f"{CACHE}/M23.npy")
E23 = np.load(f"{CACHE}/E23.npy")
T23 = np.load(f"{CACHE}/T23.npy")
D = X23.shape[1]
assert D == 83, f"特征数应为 83（Dijk 2026 附录 A 口径），实为 {D}"
log(f"LSPR23 流={len(y23):,} 特征数={D} 序列={len(I23):,}")

# ---- 三种验证划分：逐字照抄 select_signal.py 第 151-168 行（本任务只用「实体不相交」）----
rs = np.random.RandomState(SEED)
uent = np.unique(E23)
perm = rs.permutation(len(uent))
val_ent = set(uent[perm[:max(1, int(len(uent) * VAL_FRAC))]].tolist())
m_ent = np.fromiter((e in val_ent for e in E23), bool, len(E23))     # 实体不相交
t_cut = np.quantile(T23, 1.0 - TIME_TAIL)
m_time = T23 >= t_cut                                                 # 时间尾部（本任务不用作信号）
tr_mask = ~(m_ent | m_time)                                           # 训练区：两者都排除
tr_idx = np.flatnonzero(tr_mask)
val_idx = np.flatnonzero(m_ent & ~m_time)                             # 唯一选择信号的来源
assert len(np.intersect1d(val_idx, tr_idx)) == 0, "验证集与训练区有交叠"
log(f"LSPR23 实体 {len(uent):,} | 训练序列 {len(tr_idx):,} | 实体不相交验证 {len(val_idx):,}")
assert len(uent) == 150680, f"LSPR23 实体数自检失败：{len(uent)}"
assert len(tr_idx) == 208598, f"训练序列数自检失败：{len(tr_idx)}"
assert len(val_idx) == 22444, f"实体不相交验证序列数自检失败：{len(val_idx)}"
log("切分自检通过：150,680 实体 / 208,598 训练序列 / 22,444 验证序列，与 select_signal 完全一致")

dev = "cuda" if torch.cuda.is_available() else "cpu"
gX23 = torch.from_numpy(X23).to(dev)
gy23 = torch.from_numpy(y23).to(dev)
gI23 = torch.from_numpy(I23).to(dev)
gM23 = torch.from_numpy(M23).to(dev)
gtr = torch.from_numpy(tr_idx).to(dev)
gval = torch.from_numpy(val_idx).to(dev)
log(f"LSPR23 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


# ---- 模型与损失：逐字照抄 ch3_full.py 第 150-172 行；仅 Model 内部编码器加骨干开关 ----
def lp_pool(s, m, p):
    ls = torch.log(s.clamp(min=1e-7)); n = m.sum(1).clamp(min=1.0)
    return torch.exp((torch.logsumexp((p * ls).masked_fill(m < 0.5, -1e30), 1) - torch.log(n)) / p)


def npar_formula(backbone):
    """解析参数量公式；与 torch 实测逐项核对。

    mlp        ：f(Dh+h) + g(2h²+h) + o(h+1) + p_log(1)          = 2h² + (D+3)h + 2
    gru        ：GRU(3h²+3Dh+6h) + g(2h²+h) + o(h+1) + p_log(1)  = 5h² + (3D+8)h + 2
    transformer：inp(Dd+d) + MHA(4d²+4d) + 2×LN(4d)
                 + FFN(2·d·ff + ff + d) + g(2d²+d) + o(d+1) + p_log(1)
               = 6d² + 2·d·ff + ff + (D+12)d + 2
    cnn        ：conv1(kDc+c) + (n-1)×conv(kc²+c) + g(2c²+c) + o(c+1) + p_log(1)
               = (k(n-1)+2)c² + (kD + n + 2)c + 2      本脚本 n=3, k=3
    rwkv7      ：inp(DC+C)
                 + 块内向量 13C（x_r/x_w/x_k/x_v/x_a/x_g 各 C，w0、a0、k_k、k_a、r_k 各 C，ln_x 权重与偏置 2C）
                 + 三组 LoRA 6·C·lora（w1/w2、a1/a2、g1/g2）
                 + r/k/v/output 四个无偏置方阵 4C²
                 + g(2C²+C) + o(C+1) + p_log(1)
               = 6C² + 6·C·lora + (D+16)C + 2
      单块即官方 layer_id=0，该层不做 value residual（v_first = v），故不含 v0/v1/v2，
      不把不参与前向的死参数计入预算。
    """
    if backbone == "mlp":
        h = HID
        return 2 * h * h + (D + 3) * h + 2
    if backbone == "gru":
        h = GRU_HID
        return 5 * h * h + (3 * D + 8) * h + 2
    if backbone == "transformer":
        d, ff = TR_D, TR_FF
        return 6 * d * d + 2 * d * ff + ff + (D + 12) * d + 2
    if backbone == "cnn":
        c, k, n = CNN_C, CNN_K, CNN_LAYERS
        return (k * (n - 1) + 2) * c * c + (k * D + n + 2) * c + 2
    if backbone == "rwkv7":
        c, r = RWKV_C, RWKV_LORA
        return 6 * c * c + 6 * c * r + (D + 16) * c + 2
    raise ValueError(f"未知骨干：{backbone}")


def hid_of(backbone):
    return {"mlp": HID, "gru": GRU_HID, "transformer": TR_D,
            "cnn": CNN_C, "rwkv7": RWKV_C}[backbone]


def rwkv7_op(r, w, k, v, a, b, head):
    """RWKV-7 状态递归，官方纯 PyTorch 参考路径。

    逐字照 BlinkDL/RWKV-LM 固定提交 952102498e9ed367ea0a59ee64106916d474d30f 的
    RWKV-v7/rwkv_v7_demo.py 第 168-200 行（RWKV7_OP 在 USE_CUDA_KERNEL=False 时的分支），
    只把文件级常量 HEAD_SIZE 改为入参 head，并去掉末尾向 DTYPE 的回转（本脚本全程 fp32）。
    未使用官方 CUDA 内核 wkv7.cu / wkv7_cuda_fp32.cu。
    """
    B, T, C = r.size()
    H = C // head
    N = head
    r = r.view(B, T, H, N).float()
    k = k.view(B, T, H, N).float()
    v = v.view(B, T, H, N).float()
    a = a.view(B, T, H, N).float()
    b = b.view(B, T, H, N).float()
    w = torch.exp(-torch.exp(w.view(B, T, H, N).float()))
    out = torch.zeros((B, T, H, N), device=r.device, dtype=torch.float)
    state = torch.zeros((B, H, N, N), device=r.device, dtype=torch.float)

    for t in range(T):
        kk = k[:, t, :].view(B, H, 1, N)
        rr = r[:, t, :].view(B, H, N, 1)
        vv = v[:, t, :].view(B, H, N, 1)
        aa = a[:, t, :].view(B, H, N, 1)
        bb = b[:, t, :].view(B, H, 1, N)
        state = state * w[:, t, :, None, :] + state @ aa @ bb + vv @ kk
        out[:, t, :] = (state @ rr).view(B, H, N)

    return out.view(B, T, C)


class RWKV7TimeMix(nn.Module):
    """RWKV-7 单个时间混合块，以官方源码为参照实现。

    参照：BlinkDL/RWKV-LM，提交 952102498e9ed367ea0a59ee64106916d474d30f，Apache-2.0。
      结构与前向：RWKV-v7/rwkv_v7_demo.py 第 209-289 行 class RWKV_Tmix_x070。
      初始化常数：RWKV-v7/train_temp/rwkv7_train_simplified.py 第 66-146 行同名类
                  （x_* 的幂次、w0 的 www/zigzag、a0、k_k、k_a、r_k、四个线性层的均匀初始化尺度、
                    ortho_init 与 D_*_LORA=8 的小模型取值）。
      状态递归：rwkv_v7_demo.py 第 168-200 行的纯 PyTorch 参考路径（非 CUDA 内核）。
    单块对应官方 layer_id=0：ratio_0_to_1 = 0/(n_layer-1) = 0，ratio_1_to_almost0 = 1 - 0/n_layer = 1，
    且该层 v_first = v、不做 value residual，故不含 v0/v1/v2。
    """

    def __init__(self, c=RWKV_C, head=RWKV_HEAD, lora=RWKV_LORA):
        super().__init__()
        C, N = c, head
        assert C % N == 0, f"RWKV-7 通道 {C} 必须能被 head_size {N} 整除"
        H = C // N
        self.C, self.N, self.H = C, N, H
        with torch.no_grad():
            ratio_0_to_1 = 0.0            # layer_id / (n_layer - 1)，单块即 layer_id=0
            ratio_1_to_almost0 = 1.0      # 1 - layer_id / n_layer，单块即 layer_id=0
            ddd = torch.ones(1, 1, C)
            for i in range(C):
                ddd[0, 0, i] = i / C
            self.x_r = nn.Parameter(1.0 - torch.pow(ddd, 0.2 * ratio_1_to_almost0))
            self.x_w = nn.Parameter(1.0 - torch.pow(ddd, 0.9 * ratio_1_to_almost0))
            self.x_k = nn.Parameter(1.0 - torch.pow(ddd, 0.7 * ratio_1_to_almost0))
            self.x_v = nn.Parameter(1.0 - torch.pow(ddd, 0.7 * ratio_1_to_almost0))
            self.x_a = nn.Parameter(1.0 - torch.pow(ddd, 0.9 * ratio_1_to_almost0))
            self.x_g = nn.Parameter(1.0 - torch.pow(ddd, 0.2 * ratio_1_to_almost0))

            def ortho_init(x, scale):
                with torch.no_grad():
                    shape = x.shape
                    if len(shape) == 2:
                        gain = math.sqrt(shape[0] / shape[1]) if shape[0] > shape[1] else 1
                        nn.init.orthogonal_(x, gain=gain * scale)
                    elif len(shape) == 3:
                        gain = math.sqrt(shape[1] / shape[2]) if shape[1] > shape[2] else 1
                        for i in range(shape[0]):
                            nn.init.orthogonal_(x[i], gain=gain * scale)
                    else:
                        assert False
                    return x

            www = torch.zeros(C)
            zigzag = torch.zeros(C)
            linear = torch.zeros(C)
            for n in range(C):
                linear[n] = n / (C - 1) - 0.5
                zigzag[n] = ((n % N) - ((N - 1) / 2)) / ((N - 1) / 2)
                zigzag[n] = zigzag[n] * abs(zigzag[n])
                www[n] = -6 + 6 * (n / (C - 1)) ** (1 + 1 * ratio_0_to_1 ** 0.3)

            self.w1 = nn.Parameter(torch.zeros(C, lora))
            self.w2 = nn.Parameter(ortho_init(torch.zeros(lora, C), 0.1))
            self.w0 = nn.Parameter(www.reshape(1, 1, C) + 0.5 + zigzag * 2.5)

            self.a1 = nn.Parameter(torch.zeros(C, lora))
            self.a2 = nn.Parameter(ortho_init(torch.zeros(lora, C), 0.1))
            self.a0 = nn.Parameter(torch.zeros(1, 1, C) - 0.19 + zigzag * 0.3 + linear * 0.4)

            self.g1 = nn.Parameter(torch.zeros(C, lora))
            self.g2 = nn.Parameter(ortho_init(torch.zeros(lora, C), 0.1))

            self.k_k = nn.Parameter(torch.zeros(1, 1, C) + 0.71 - linear * 0.1)
            self.k_a = nn.Parameter(torch.zeros(1, 1, C) + 1.02)
            self.r_k = nn.Parameter(torch.zeros(H, N) - 0.04)

            self.time_shift = nn.ZeroPad2d((0, 0, 1, -1))
            self.receptance = nn.Linear(C, C, bias=False)
            self.key = nn.Linear(C, C, bias=False)
            self.value = nn.Linear(C, C, bias=False)
            self.output = nn.Linear(C, C, bias=False)
            self.ln_x = nn.GroupNorm(H, C, eps=64e-5)

            self.receptance.weight.data.uniform_(-0.5 / (C ** 0.5), 0.5 / (C ** 0.5))
            self.key.weight.data.uniform_(-0.05 / (C ** 0.5), 0.05 / (C ** 0.5))
            self.value.weight.data.uniform_(-0.5 / (C ** 0.5), 0.5 / (C ** 0.5))
            self.output.weight.data.zero_()

    def forward(self, x):
        B, T, C = x.size()
        H = self.H
        xx = self.time_shift(x) - x

        xr = x + xx * self.x_r
        xw = x + xx * self.x_w
        xk = x + xx * self.x_k
        xv = x + xx * self.x_v
        xa = x + xx * self.x_a
        xg = x + xx * self.x_g

        r = self.receptance(xr)
        w = -F.softplus(-(self.w0 + torch.tanh(xw @ self.w1) @ self.w2)) - 0.5   # 软钳到 (-inf, -0.5)
        k = self.key(xk)
        v = self.value(xv)                       # 单块即 layer_id=0：v_first = v，无 value residual
        a = torch.sigmoid(self.a0 + (xa @ self.a1) @ self.a2)                    # 上下文内学习率
        g = torch.sigmoid(xg @ self.g1) @ self.g2

        kk = k * self.k_k
        kk = F.normalize(kk.view(B, T, H, -1), dim=-1, p=2.0).view(B, T, C)
        k = k * (1 + (a - 1) * self.k_a)

        y = rwkv7_op(r, w, k, v, -kk, kk * a, self.N)
        y = self.ln_x(y.view(B * T, C)).view(B, T, C)
        y = y + ((r.view(B, T, H, -1) * k.view(B, T, H, -1) * self.r_k).sum(dim=-1, keepdim=True)
                 * v.view(B, T, H, -1)).view(B, T, C)
        y = self.output(y * g)
        return y


class Model(nn.Module):
    """结构与 ch3_full.Model 相同；只有逐流编码器 encode() 随 backbone 切换。

    五个骨干共用同一组合头 g、同一输出头 o 与同一 p_log，因果前缀均值 c 与
    Lp 池化、辅助损失、评价口径一律不动。
    """

    def __init__(self, backbone, agg, lp, hid=None, dp=0.1):
        super().__init__(); self.agg, self.lp = agg, lp
        self.backbone = backbone
        hid = hid_of(backbone) if hid is None else hid
        if backbone == "mlp":
            self.f = nn.Sequential(nn.Linear(D, hid), nn.ReLU(), nn.Dropout(dp))
        elif backbone == "gru":
            self.f = nn.GRU(input_size=D, hidden_size=hid, num_layers=1, bias=True,
                            batch_first=True, bidirectional=False)
        elif backbone == "transformer":
            self.inp = nn.Linear(D, hid)
            self.att = nn.MultiheadAttention(embed_dim=hid, num_heads=TR_HEADS,
                                             dropout=dp, batch_first=True)
            self.n1 = nn.LayerNorm(hid); self.n2 = nn.LayerNorm(hid)
            self.ff = nn.Sequential(nn.Linear(hid, TR_FF), nn.ReLU(), nn.Dropout(dp),
                                    nn.Linear(TR_FF, hid))
        elif backbone == "cnn":
            self.conv = nn.ModuleList(
                [nn.Conv1d(D if i == 0 else hid, hid, CNN_K) for i in range(CNN_LAYERS)])
            self.act = nn.ReLU(); self.drop = nn.Dropout(dp)
        elif backbone == "rwkv7":
            self.inp = nn.Linear(D, hid)
            self.tmix = RWKV7TimeMix(hid, RWKV_HEAD, RWKV_LORA)
        else:
            raise ValueError(f"未知骨干：{backbone}")
        self.hid = hid
        self.g = nn.Sequential(nn.Linear(hid * 2, hid), nn.ReLU(), nn.Dropout(dp))
        self.o = nn.Linear(hid, 1); self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

    @property
    def p(self): return torch.exp(self.p_log).clamp(1e-3, 1e3)

    def encode(self, x, m):
        """逐流编码器。输出恒为掩码后的 (B, L, hid)，补零位严格为 0，且位置 t 只依赖 <= t。"""
        if self.backbone == "mlp":
            return self.f(x) * m.unsqueeze(-1)
        if self.backbone == "gru":
            # lengths 必须在 CPU 上；enforce_sorted=False 由 PyTorch 内部排序再还原顺序
            lens = m.sum(1).to(torch.int64).clamp(min=1).cpu()
            packed = pack_padded_sequence(x, lens, batch_first=True, enforce_sorted=False)
            out, _ = self.f(packed)
            h, _ = pad_packed_sequence(out, batch_first=True, total_length=x.shape[1])
            return h * m.unsqueeze(-1)
        if self.backbone == "cnn":
            # 因果一维卷积：只在左侧补 k-1 个零，位置 t 的感受野落在 [t-(k-1), t]
            h = (x * m.unsqueeze(-1)).transpose(1, 2)
            for conv in self.conv:
                h = self.drop(self.act(conv(F.pad(h, (CNN_K - 1, 0)))))
            return h.transpose(1, 2) * m.unsqueeze(-1)
        if self.backbone == "rwkv7":
            h0 = self.inp(x * m.unsqueeze(-1)) * m.unsqueeze(-1)
            return self.tmix(h0) * m.unsqueeze(-1)
        # transformer：单层因果掩码自注意力编码器块
        n = x.shape[1]
        mv = m.unsqueeze(-1) > 0.5
        h0 = self.inp(x) * m.unsqueeze(-1)
        cm = torch.triu(torch.full((n, n), float("-inf"), device=x.device, dtype=h0.dtype),
                        diagonal=1)                                   # 位置 t 只能看 <= t
        a, _ = self.att(h0, h0, h0, attn_mask=cm, key_padding_mask=(m < 0.5),
                        need_weights=False)
        a = torch.where(mv, a, torch.zeros_like(a))                   # 全掩码行不产生 NaN
        z = self.n1(h0 + a)
        h = self.n2(z + self.ff(z))
        return h * m.unsqueeze(-1)

    def forward(self, x, m):
        h = self.encode(x, m)
        c = ((torch.cumsum(h, 1) / torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)) * m.unsqueeze(-1)
             if self.agg else torch.zeros_like(h))
        return self.o(self.g(torch.cat([h, c], -1))).squeeze(-1)


_sl = (y23[I23.reshape(-1)].reshape(I23.shape) * M23).max(1) > 0
_spw = float((1 - _sl.mean()) / max(_sl.mean(), 1e-8))
_pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
_lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=_pos)
_bs = nn.BCELoss(reduction="none")
log(f"逐流 pos_weight={_pos.item():.6f}  序列级 spw={_spw:.6f}（口径照抄 ch3_full，用全量 LSPR23）")
del _sl


@torch.no_grad()
def val_ap(net):
    """LSPR23 实体不相交验证集上的逐流 AP。照抄 select_signal.py ap_on()。

    本函数是唯一的模型选择信号来源，只触碰 gX23/gy23/gI23/gM23/gval。
    注意：eval 模式下 dropout 不抽样，本函数不消耗任何 RNG，
    因此「训练步之后」与「验证之后」的 RNG 快照等价，检查点放在验证之后不影响恢复语义。
    """
    net.eval(); P = []; Y = []
    for a in range(0, len(val_idx), 2048):
        sel = gval[a:a + 2048]; idx = gI23[sel][:, :L]; msk = gM23[sel][:, :L]; b = idx.shape[0]
        lo = net(gX23[idx.reshape(-1)].reshape(b, L, D), msk)
        fm = msk.reshape(-1) > 0
        P.append(torch.sigmoid(lo).reshape(-1)[fm].cpu().numpy())
        Y.append(gy23[idx.reshape(-1)].reshape(-1)[fm].cpu().numpy())
    net.train()
    P = np.concatenate(P); Y = np.concatenate(Y)
    assert Y.max() > 0, "验证集无正例，选择信号无效"
    return float(average_precision_score(Y, P))


# =====================================================================================
# 实现验证（合成数据，真值由构造给定；不创建运行身份、不产生任何指标、不进结果表）
#   性质一 掩码决定性：补零位输入换成 1e3 噪声，真实位输出必须逐位不变，且补零位输出恒为 0
#   性质二 因果性    ：改动位置 > t 的输入，位置 <= t 的输出必须不变
#   性质三 参数量解析公式与 torch 实测一致（仍覆盖全部五个骨干）
# 判据一律 <1e-6；超阈先做 TF32 归因诊断，不放宽阈值，也不改训练与评价的默认精度设置。
# v2 只对本进程的骨干验性质一与性质二；v1 已对四个骨干全部验过，收据
# runs/diagnostics/ch3-backbone-protocolA/impl_verification.json 三项全部 0.0。
# =====================================================================================
def _impl_verify():
    log("=" * 96)
    log("实现验证（合成数据，真值由构造给定；只报通过/不通过，不进结果表）")
    rep = {"backbone_verified": BK}
    for bk in ["mlp"] + ALL_BACKBONES:
        want = npar_formula(bk)
        got = sum(p.numel() for p in Model(bk, True, True).parameters())
        assert got == want, f"{bk} 参数量公式 {want} 与 torch 实测 {got} 不一致"
        rep[f"npar_{bk}"] = got
        log(f"  参数量 {bk:<11} 公式={want:,} torch实测={got:,} 一致 | "
            f"相对 MLP {100.0*(got-MLP_NPAR)/MLP_NPAR:+.3f}%")

    torch.manual_seed(SEED)
    b = 8
    xs = torch.randn(b, L, D, device=dev)
    lens = torch.tensor([1, 3, 17, 64, 96, 127, 128, 128], device=dev)
    ms = (torch.arange(L, device=dev).unsqueeze(0) < lens.unsqueeze(1)).to(xs.dtype)
    pad = (ms < 0.5).unsqueeze(-1)
    T_PROBE = [0, 1, 5, 31, 63, 100, 126]

    def _causal_worst(net, tf32):
        _mm, _cd = torch.backends.cuda.matmul.allow_tf32, torch.backends.cudnn.allow_tf32
        torch.backends.cuda.matmul.allow_tf32 = tf32
        torch.backends.cudnn.allow_tf32 = tf32
        w = 0.0
        with torch.no_grad():
            base = net.encode(xs, ms)
            for t in T_PROBE:
                xt = xs.clone()
                xt[:, t + 1:, :] = torch.randn_like(xt[:, t + 1:, :]) * 1e3
                ht = net.encode(xt, ms)
                w = max(w, (ht[:, :t + 1] - base[:, :t + 1]).abs().max().item())
        torch.backends.cuda.matmul.allow_tf32 = _mm
        torch.backends.cudnn.allow_tf32 = _cd
        return w

    for bk in [BK]:
        net = Model(bk, True, True).to(dev).eval()
        with torch.no_grad():
            h0 = net.encode(xs, ms)
            x2 = torch.where(pad, torch.randn_like(xs) * 1e3, xs)
            h1 = net.encode(x2, ms)
            d_mask = (h1 - h0).abs().max().item()
            d_pad = h0.masked_select(pad.expand_as(h0)).abs().max().item()
        rep[f"{bk}_mask_determinism_maxabs"] = d_mask
        rep[f"{bk}_pad_output_maxabs"] = d_pad
        log(f"  性质一 {bk:<11} 掩码决定性：补零位改 1e3 噪声后真实位最大差={d_mask:.3e}（判据 <1e-6）"
            f"；补零位输出最大绝对值={d_pad:.3e}（判据 =0）")
        assert d_mask < 1e-6, f"{bk} 掩码决定性不通过：{d_mask:.3e}"
        assert d_pad == 0.0, f"{bk} 补零位输出非零：{d_pad:.3e}"

        worst = _causal_worst(net, torch.backends.cuda.matmul.allow_tf32)
        rep[f"{bk}_causality_maxabs"] = worst
        log(f"  性质二 {bk:<11} 因果性：改动位置>t 后位置<=t 最大差={worst:.3e}（判据 <1e-6）")
        if worst >= 1e-6:
            log("         超阈，先做归因诊断：关闭 TF32 重测（不改变训练与评价的默认精度设置）")
            w2 = _causal_worst(net, False)
            rep[f"{bk}_causality_maxabs_tf32_off"] = w2
            log(f"         TF32 关闭后最大差={w2:.3e}")
        assert worst < 1e-6, f"{bk} 因果性不通过：{worst:.3e}"
        del net
        torch.cuda.empty_cache()

    atomic_json(rep, f"{OUT}/impl_verification.json")
    log(f"  实现验证全部通过，收据 {OUT}/impl_verification.json")
    return rep


if ARGS.skip_impl_verify:
    log("已按 --skip-impl-verify 跳过实现验证（仅允许非正式输出根）")
    IMPL = {"skipped": True}
else:
    IMPL = _impl_verify()


def train_and_select(backbone, agg, lp, seed, tag, cell_dir):
    """训练 N_EPOCH 个 epoch 不早停，逐 epoch 用 LSPR23 验证 AP 选检查点；支持断点续训。

    函数体内不出现任何 LSPR24 标识符；此时进程内也没有 LSPR24 数据。
    """
    torch.manual_seed(seed); np.random.seed(seed)
    net = Model(backbone, agg, lp).to(dev)
    dec = [p for n, p in net.named_parameters() if not (n.endswith(".bias") or n == "p_log")]
    nod = [p for n, p in net.named_parameters() if (n.endswith(".bias") or n == "p_log")]
    opt = torch.optim.AdamW([{"params": dec, "weight_decay": 0.01},
                             {"params": nod, "weight_decay": 0.0}], lr=2e-3)
    gen = torch.Generator().manual_seed(seed)
    best = {"ap": -1.0, "epoch": None, "p": None, "state": None}
    hist = []
    start_ep = 1
    prev_seconds = 0.0
    inflight = os.path.join(cell_dir, "inflight.pt")

    if os.path.exists(inflight):
        ck = load_ckpt(inflight)
        # 恢复路径断言 R4：在途检查点的身份与当前配置必须完全一致，否则拒绝续训
        assert ck["tag"] == tag and ck["backbone"] == backbone, f"{tag} 在途检查点身份不符"
        assert ck["agg"] == agg and ck["lp"] == lp, f"{tag} 在途检查点 agg/lp 不符"
        assert ck["seed"] == seed, f"{tag} 在途检查点 seed 不符"
        assert ck["n_epoch"] == N_EPOCH and ck["epoch_steps"] == EPOCH_STEPS, \
            f"{tag} 在途检查点训练预算不符：{ck['n_epoch']}×{ck['epoch_steps']}"
        assert ck["npar"] == npar_formula(backbone), f"{tag} 在途检查点参数量不符"
        # 恢复路径断言 R5：hist 必须是 1..epoch 的连续序列，长度等于已完成轮数
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
            f"当前最优 epoch={best['epoch']} 验证AP={best['ap']:.6f}，"
            f"已用 {prev_seconds/60:.2f} 分，全部 RNG 状态已恢复，从 epoch {start_ep} 继续")
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
            lo = net(xb, msk); loss = (_lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
            if lp:
                sq = lp_pool(torch.sigmoid(lo), msk, net.p).clamp(1e-6, 1 - 1e-6)
                ysq = (yb * msk).amax(1)
                w = 1.0 + (_spw - 1.0) * ysq
                loss = loss + AUX_W * ((_bs(sq, ysq) * w).sum() / w.sum())
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        v = val_ap(net); pv = net.p.item()
        hist.append([ep, v, pv])
        star = ""
        if v > best["ap"]:
            best = {"ap": v, "epoch": ep, "p": pv,
                    "state": {k: t.detach().clone() for k, t in net.state_dict().items()}}
            star = "  ← 当前最优"
        cum = prev_seconds + (time.time() - t0)
        atomic_torch_save({"tag": tag, "backbone": backbone, "cell": tag.split("-")[-1],
                           "agg": agg, "lp": lp, "seed": seed,
                           "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS,
                           "npar": sum(p.numel() for p in net.parameters()),
                           "epoch": ep, "model": net.state_dict(), "opt": opt.state_dict(),
                           "best": best, "hist": hist, "train_seconds": cum,
                           "rng": rng_snapshot(gen)}, inflight)
        log(f"  {tag} ep {ep:>2}/{N_EPOCH} 验证AP={v:.6f} p={pv:.4f} 累计{cum/60:.1f}分{star}")
    tr_t = prev_seconds + (time.time() - t0)
    log(f"  {tag} 训练完成 {tr_t/60:.2f} 分，选中 epoch {best['epoch']}（验证AP={best['ap']:.6f} p={best['p']:.4f}）")
    return best, hist, tr_t, sum(p.numel() for p in net.parameters())


SEL = {}
_TRAINED_NOW, _TRAINED_RESUMED = 0, 0
log("=" * 96)
log(f"骨干 {BK}（隐藏维 {hid_of(BK)}，参数 {npar_formula(BK):,}）× {len(CELLS)} 格 seed={SEED}，"
    f"{N_EPOCH} epoch × {EPOCH_STEPS} 步 = {N_EPOCH*EPOCH_STEPS} 步，不早停，串行训练")
_trained_rec = read_stage(PROG, "trained")
for cid, agg, lp in CELLS:
    key = f"{BK}-{cid}"
    cell_dir = f"{CELLS_DIR}/{key}"
    os.makedirs(cell_dir, exist_ok=True)
    sel_path = f"{cell_dir}/selected.pt"
    if key in _trained_rec and os.path.exists(sel_path):
        s = load_ckpt(sel_path)
        assert s["backbone"] == BK and s["cell"] == cid and s["seed"] == SEED, f"{key} 逐格检查点身份不符"
        assert s["agg"] == agg and s["lp"] == lp, f"{key} 逐格检查点 agg/lp 不符"
        assert s["n_epoch"] == N_EPOCH and s["epoch_steps"] == EPOCH_STEPS, f"{key} 逐格检查点训练预算不符"
        assert s["npar"] == npar_formula(BK), f"{key} 逐格检查点参数量不符"
        assert len(s["hist"]) == N_EPOCH, f"{key} 逐格检查点 hist 长度 {len(s['hist'])} 应为 {N_EPOCH}"
        SEL[key] = {"backbone": BK, "cell": cid, "agg": agg, "lp": lp,
                    "best": {"ap": s["val_ap"], "epoch": s["epoch"], "p": s["p"], "state": s["state"]},
                    "hist": s["hist"], "tr": s["train_seconds"], "npar": s["npar"]}
        _TRAINED_RESUMED += 1
        log(f"--- {key} (agg={agg}, lp={lp}) 已完成，跳过训练："
            f"选中 epoch={s['epoch']} 验证AP={s['val_ap']:.6f} p={s['p']:.4f}")
        continue
    log(f"--- {key} (agg={agg}, lp={lp}) ---")
    best, hist, tr_t, npar = train_and_select(BK, agg, lp, SEED, key, cell_dir)
    assert npar == npar_formula(BK), f"{key} 参数量 {npar} 与公式 {npar_formula(BK)} 不一致"
    atomic_torch_save({"backbone": BK, "cell": cid, "agg": agg, "lp": lp, "seed": SEED,
                       "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS, "npar": npar,
                       "epoch": best["epoch"], "val_ap": best["ap"], "p": best["p"],
                       "state": best["state"], "hist": hist,
                       "train_seconds": tr_t}, sel_path)
    append_jsonl(PROG, {"backbone": BK, "cell": cid, "cell_key": key, "stage": "trained",
                        "selected_epoch": best["epoch"], "val_ap": best["ap"], "p": best["p"],
                        "train_seconds": tr_t, "npar": npar, "run_id": RUN_ID,
                        "ts": time.time()})
    _TRAINED_NOW += 1
    SEL[key] = {"backbone": BK, "cell": cid, "agg": agg, "lp": lp,
                "best": best, "hist": hist, "tr": tr_t, "npar": npar}

# =====================================================================================
# 阶段闸门：从磁盘重新推导，再把选择结果写盘冻结，之后才允许读入 LSPR24
# 恢复路径断言 R1：闸门不读任何持久化的布尔值，只由「四格都有 trained 台账且 selected.pt 都在」推导
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


if len(CELLS) < len(ALL_CELLS):
    # 只在非正式输出根才可能走到这里（IS_PROD 已断言四格全跑）。
    # 不足四格无法开闸，进程在闸门前干净退出，LSPR24 一次都不会被读入。
    log("=" * 96)
    log(f"本进程只跑 {len(CELLS)} 格（非正式降规模），阶段闸门不开，"
        f"在读入 LSPR24 之前干净退出；LSPR24 读入次数 {_N24_LOADS}")
    raise SystemExit(0)

SELECTION_FROZEN, _GATE_EVIDENCE = gate_from_disk()
_GATE_DERIVED_AT = time.time()
assert SELECTION_FROZEN, f"阶段闸门未开（磁盘推导）：{_GATE_EVIDENCE}"
assert len(SEL) == 4, f"闸门已开但进程内只有 {len(SEL)} 格，制品与内存不一致"

_frozen = {"protocol": "逐epoch在LSPR23实体不相交验证集上取逐流AP最大的epoch，无末5平均，不早停",
           "run_id": RUN_ID, "backbone": BK,
           "seed": SEED, "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS,
           "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
           "gate_evidence": _GATE_EVIDENCE,
           "cells": {c: {"backbone": SEL[c]["backbone"], "cell_id": SEL[c]["cell"],
                         "selected_epoch": SEL[c]["best"]["epoch"],
                         "val_ap_at_selected": SEL[c]["best"]["ap"],
                         "p_at_selected": SEL[c]["best"]["p"],
                         "val_ap_history": SEL[c]["hist"],
                         "train_seconds": SEL[c]["tr"]} for c in SEL}}
atomic_json(_frozen, f"{OUT}/selection_frozen.json")
log("=" * 96)
log(f"选择阶段结束（闸门由磁盘推导），结果已冻结写盘 {OUT}/selection_frozen.json")
log(f"本次进程训练 {_TRAINED_NOW} 格，从磁盘恢复 {_TRAINED_RESUMED} 格")
for c in SEL:
    log(f"  {c}: 选中 epoch={SEL[c]['best']['epoch']:>2} 验证AP={SEL[c]['best']['ap']:.6f}")

# 释放 LSPR23 显存后再读 LSPR24，压低峰值
del gX23, gy23, gI23, gM23, gtr, gval, X23, y23, I23, M23, E23, T23
torch.cuda.empty_cache()
log(f"LSPR23 已释放，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

# =====================================================================================
# 阶段二：此刻才第一次读入 LSPR24，每格只评价一次
# 恢复路径断言 R2：LSPR24 读入必须严格晚于闸门推导时刻，且本进程此前读入次数为 0
# =====================================================================================
assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段读入 LSPR24"
assert _GATE_DERIVED_AT is not None and _GATE_DERIVED_AT <= time.time(), "闸门推导时刻缺失"
assert _N24_LOADS == 0, f"LSPR24 在闸门开启前已被读入 {_N24_LOADS} 次"
_N24_LOADS += 1
log("=" * 96)
log("阶段二 评价：首次读入 LSPR24（选择已冻结）")
# 数据身份：X24 与上面的 X23 同源，是标准化后的特征矩阵，不是 raw83 原值。见缓存目录 README.md。
X24 = np.load(f"{CACHE}/X24.npy")
y24 = np.load(f"{CACHE}/y24.npy")
I24 = np.load(f"{CACHE}/I24.npy")
M24 = np.load(f"{CACHE}/M24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
t24 = np.load(f"{CACHE}/t24.npy")
assert X24.shape[1] == D

# ---- 实体构造：逐字照抄 ch3_full.py 第 130-141 行 ----
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
del key24, s24, d24

_ord = np.lexsort((t24, ent24))
_e = ent24[_ord]
_start = np.flatnonzero(np.r_[True, _e[1:] != _e[:-1]])
_rank = np.empty(len(_ord), np.int64)
_rank[_ord] = np.arange(len(_ord)) - np.repeat(_start, np.diff(np.r_[_start, len(_ord)]))
del _ord, _e, _start, t24

gX24 = torch.from_numpy(X24).to(dev)
gI24 = torch.from_numpy(I24).to(dev)
gM24 = torch.from_numpy(M24).to(dev)
del X24
log(f"LSPR24 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


# ---- 评价口径：逐字照抄 ch3_full.py 第 213-240 行（含末尾 .astype(np.float32)）----
def ent_ap(sc, seen, p=None, first_k=None):
    """实体级 AP。first_k 不为空时只用每个实体按时间的前 k 条流（延迟约束）。"""
    m = seen.copy()
    if first_k is not None: m &= (_rank < first_k)
    if not m.any(): return float("nan"), 0
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[m], sc[m])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[m], np.clip(sc[m], 1e-7, 1.0).astype(np.float64) ** p); np.add.at(cnt, ent24[m], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    ok = np.isfinite(es)
    return average_precision_score(ent_lab[ok], es[ok]), int(ok.sum())


def dr_at_fpr(sc, seen, target=0.04, p=None, first_k=None):
    m = seen.copy()
    if first_k is not None: m &= (_rank < first_k)
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[m], sc[m])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[m], np.clip(sc[m], 1e-7, 1.0).astype(np.float64) ** p); np.add.at(cnt, ent24[m], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    ok = np.isfinite(es); v = es[ok]; l = ent_lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0: return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


@torch.no_grad()
def score24(net):
    """LSPR24 逐流打分。推理循环逐字照抄 ch3_full.py 第 199-207 行（单检查点，无平均）。"""
    global _EVAL24_CALLS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段评价 LSPR24"
    _EVAL24_CALLS += 1
    net.eval()
    sc = torch.zeros(len(y24), device=dev)
    sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    for a in range(0, len(I24), 2048):
        idx = gI24[a:a + 2048][:, :L]; msk = gM24[a:a + 2048][:, :L]; b = idx.shape[0]
        pr = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, L, D), msk))
        fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
        sc[fi[fm]] = pr.reshape(-1)[fm]; sn[fi[fm]] = True
    return sc.cpu().numpy(), sn.cpu().numpy()


RES = {}
_eval_rec = read_stage(EVAL_PROG, "evaluated")
log("=" * 96)
log("每格加载选中 epoch 的权重，在 LSPR24 上评价一次（已评价的格跳过）")
for cid, agg, lp in ALL_CELLS:
    key = f"{BK}-{cid}"
    eval_json = f"{CELLS_DIR}/{key}/eval.json"
    if key in _eval_rec and os.path.exists(eval_json):
        r = json.load(open(eval_json, encoding="utf-8"))
        # 恢复路径断言 R3：磁盘上的评价结果必须与本进程 selected.pt 的身份逐项一致，否则说明制品跨运行漂移
        assert r["backbone"] == BK and r["cell"] == cid, f"{key} eval.json 身份不符"
        assert r["agg"] == agg and r["lp"] == lp, f"{key} eval.json agg/lp 不符"
        assert r["sel_epoch"] == SEL[key]["best"]["epoch"], \
            f"{key} eval.json 选中 epoch {r['sel_epoch']} 与 selected.pt {SEL[key]['best']['epoch']} 不符"
        assert abs(r["val_ap"] - SEL[key]["best"]["ap"]) < 1e-12, f"{key} eval.json 验证AP 与 selected.pt 不符"
        assert abs(r["p"] - SEL[key]["best"]["p"]) < 1e-9, f"{key} eval.json p 与 selected.pt 不符"
        assert r["npar"] == SEL[key]["npar"], f"{key} eval.json 参数量不符"
        if cid == "C11":
            assert os.path.exists(f"{OUT}/scores_{BK}_C11.npy"), f"{key} 已评价但逐流分数缺失"
            assert os.path.exists(f"{OUT}/seen_{BK}_C11.npy"), f"{key} 已评价但覆盖掩码缺失"
        RES[key] = r
        _EVAL24_RESUMED += 1
        log(f"{key}: 已评价，跳过（实体AP(主)={r['e_lp']:.6f} DR@4%FPR={r['dr_main']:.6f}）")
        continue
    # 恢复路径断言 R6：同一进程内任何一格不得评价两次
    assert key not in _EVAL24_KEYS, f"{key} 在本进程内被重复评价"
    _EVAL24_KEYS.add(key)
    net = Model(BK, agg, lp).to(dev)
    net.load_state_dict(SEL[key]["best"]["state"])
    p = net.p.item()
    assert abs(p - SEL[key]["best"]["p"]) < 1e-9, f"{key} 权重回载后 p 不一致"
    t1 = time.time()
    sc, seen = score24(net)
    ev_t = time.time() - t1
    fap = average_precision_score(y24[seen], sc[seen])
    fauc = roc_auc_score(y24[seen], sc[seen])
    e_max, n_ent_ok = ent_ap(sc, seen)
    e_lp, _ = ent_ap(sc, seen, p if lp else None)     # ch3_full 口径：lp=False 时退化为 max
    dr_main = dr_at_fpr(sc, seen, 0.04, p if lp else None)
    dr_max = dr_at_fpr(sc, seen, 0.04, None)
    RES[key] = {"backbone": BK, "cell": cid, "agg": agg, "lp": lp,
                "sel_epoch": SEL[key]["best"]["epoch"],
                "val_ap": SEL[key]["best"]["ap"], "p": p,
                "fap": float(fap), "fauc": float(fauc),
                "e_max": float(e_max), "e_lp": float(e_lp),
                "dr_main": float(dr_main), "dr_max": float(dr_max),
                "n_ent_scored": int(n_ent_ok), "tr": SEL[key]["tr"], "ev": ev_t,
                "npar": SEL[key]["npar"]}
    log(f"{key}: epoch={SEL[key]['best']['epoch']:>2} 验证AP={SEL[key]['best']['ap']:.6f} p={p:.4f} | "
        f"逐流AP={fap:.6f} AUC={fauc:.6f} 实体AP(max)={e_max:.6f} 实体AP(Lp)={e_lp:.6f} "
        f"DR@4%FPR={dr_main:.6f} (max口径={dr_max:.6f}) 覆盖实体={n_ent_ok:,} "
        f"训练{SEL[key]['tr']/60:.2f}分 推理{ev_t:.1f}秒")
    if cid == "C11":
        atomic_npy(sc, f"{OUT}/scores_{BK}_C11.npy")
        atomic_npy(seen, f"{OUT}/seen_{BK}_C11.npy")
        log(f"  {BK} C11 逐流分数已存 {OUT}/scores_{BK}_C11.npy")
    atomic_json(RES[key], eval_json)
    append_jsonl(EVAL_PROG, {"backbone": BK, "cell": cid, "cell_key": key, "stage": "evaluated",
                             "e_lp": RES[key]["e_lp"], "dr_main": RES[key]["dr_main"],
                             "fap": RES[key]["fap"], "run_id": RUN_ID, "ts": time.time()})
    del sc, seen, net
    torch.cuda.empty_cache()

_N_EXPECT = len(ALL_CELLS)
assert _EVAL24_CALLS == len(_EVAL24_KEYS), \
    f"本进程 score24 调用 {_EVAL24_CALLS} 次但只有 {len(_EVAL24_KEYS)} 格，存在重复评价"
assert _EVAL24_CALLS + _EVAL24_RESUMED == _N_EXPECT, \
    f"评价覆盖应为 {_N_EXPECT} 格（本次 {_EVAL24_CALLS} + 恢复 {_EVAL24_RESUMED}）"
assert _N24_LOADS == 1, f"LSPR24 应只从磁盘读入 1 次，实为 {_N24_LOADS}"
assert set(RES) == {f"{BK}-{c}" for c, _, _ in ALL_CELLS}, "评价结果的格集合不完整"
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，本进程评价 {_EVAL24_CALLS} 次、"
    f"从磁盘恢复 {_EVAL24_RESUMED} 格，合计 {_N_EXPECT} 格恰各一次，均发生在选择冻结之后")

# =====================================================================================
# 交互项与组合创新判据（本骨干）
# =====================================================================================
INTER = {}
log("=" * 96)
log("2x2 交互项：交互 = C11 − C10 − C01 + C00；组合创新 = 交互>0 且 组合>单模块之和")
for label, key in [("实体AP(主口径: lp格用Lp, 非lp格用max)", "e_lp"),
                   ("实体AP(全格 max 口径)", "e_max"),
                   ("DR@4%FPR(主口径)", "dr_main"),
                   ("DR@4%FPR(全格 max 口径)", "dr_max"),
                   ("逐流AP", "fap")]:
    v = {c: RES[f"{BK}-{c}"][key] for c in ["C00", "C01", "C10", "C11"]}
    eA = v["C10"] - v["C00"]; eB = v["C01"] - v["C00"]; eAB = v["C11"] - v["C00"]
    inter = eAB - (eA + eB)
    c1 = inter > 0; c2 = eAB > (eA + eB); c3 = eAB > 0
    INTER[f"{BK}-{key}"] = {"backbone": BK, "label": label,
                            "C00": v["C00"], "C01": v["C01"], "C10": v["C10"], "C11": v["C11"],
                            "A": eA, "B": eB, "sum": eA + eB, "combo": eAB, "interaction": inter,
                            "crit_interaction_pos": bool(c1), "crit_combo_gt_sum": bool(c2),
                            "crit_combo_pos": bool(c3), "combo_innovation": bool(c1 and c3)}
    log(f"\n【{BK} | {label}】")
    log(f"  C00={v['C00']:.6f}  C01={v['C01']:.6f}  C10={v['C10']:.6f}  C11={v['C11']:.6f}")
    log(f"  A(仅聚合)={eA:+.6f}  B(仅Lp)={eB:+.6f}  之和={eA+eB:+.6f}  组合={eAB:+.6f}  交互={inter:+.6f}")
    log(f"  判据一 交互>0: {'通过' if c1 else '不通过'} | 判据二 组合>基线: {'通过' if c3 else '不通过'}"
        f" | ★ 组合创新{'成立' if (c1 and c3) else '不成立'}")

# ---- 与 MLP 骨干（同为协议 A）的逐格对比：数字取自冻结制品 ch3_2x2_fairsel_results.json ----
assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段读入含 LSPR24 指标的 MLP 参照"
_mref = json.load(open(MLP_REF))
assert _mref["seed"] == SEED and _mref["isolation"]["lspr24_evals"] == 4, "MLP 参照制品身份不符"
MLP_A = {c: {k: _mref["cells"][c][k] for k in
             ["sel_epoch", "val_ap", "p", "fap", "fauc", "e_max", "e_lp", "dr_main", "dr_max",
              "npar", "tr", "ev"]}
         for c in ["C00", "C01", "C10", "C11"]}
_EXP_MLP_ELP = {"C00": 0.334994, "C01": 0.408513, "C10": 0.385970, "C11": 0.518350}
for c, want in _EXP_MLP_ELP.items():
    got = MLP_A[c]["e_lp"]
    assert abs(got - want) < 5e-7, f"MLP 参照 {c} 实体AP(主口径) 应为 {want}，实为 {got:.6f}"
    assert MLP_A[c]["npar"] == MLP_NPAR, f"MLP 参照 {c} 参数量应为 {MLP_NPAR}"
log("=" * 96)
log("MLP 参照自检通过（协议 A 冻结数字）：C00 0.334994 / C01 0.408513 / C10 0.385970 / C11 0.518350")
log(f"--- 骨干 {BK} 相对 MLP 骨干（同协议 A）的逐格差 ---")
for cid in ["C00", "C01", "C10", "C11"]:
    r = RES[f"{BK}-{cid}"]; m = MLP_A[cid]
    log(f"  {cid}: 逐流AP {m['fap']:.6f}→{r['fap']:.6f} ({r['fap']-m['fap']:+.6f}) | "
        f"实体AP(主) {m['e_lp']:.6f}→{r['e_lp']:.6f} ({r['e_lp']-m['e_lp']:+.6f}) | "
        f"实体AP(max) {m['e_max']:.6f}→{r['e_max']:.6f} ({r['e_max']-m['e_max']:+.6f}) | "
        f"DR@4%FPR {m['dr_main']:.6f}→{r['dr_main']:.6f} ({r['dr_main']-m['dr_main']:+.6f})")
d = RES[f"{BK}-C11"]["e_lp"] - RES[f"{BK}-C00"]["e_lp"]
dm = MLP_A["C11"]["e_lp"] - MLP_A["C00"]["e_lp"]
log(f"  C11−C00 实体AP(主口径) 增益：{BK} {d:+.6f}（{d*100:+.2f} 点） vs MLP {dm:+.6f}（{dm*100:+.2f} 点）")

# ---- 与 XGBoost 实体基线对比 ----
XGB = {"e_lp": 0.531917, "dr_main": 0.816489, "fap": 0.222391}
log("=" * 96)
log("与 XGBoost 实体基线对比（XGB: 实体AP(Lp)=0.531917 DR@4%FPR=0.816489 逐流AP=0.222391）")
for cid in ["C00", "C01", "C10", "C11"]:
    r = RES[f"{BK}-{cid}"]
    log(f"  {BK}-{cid}: 实体AP {r['e_lp']:.6f} ({r['e_lp']-XGB['e_lp']:+.6f}) | "
        f"DR@4%FPR {r['dr_main']:.6f} ({r['dr_main']-XGB['dr_main']:+.6f}) | "
        f"逐流AP {r['fap']:.6f} ({r['fap']-XGB['fap']:+.6f})")

atomic_json({"protocol": _frozen["protocol"], "run_id": RUN_ID, "seed": SEED, "backbone": BK,
             "backbones": {bk: {"hid": hid_of(bk), "npar": npar_formula(bk),
                                "npar_rel_mlp": (npar_formula(bk) - MLP_NPAR) / MLP_NPAR}
                           for bk in ["mlp"] + ALL_BACKBONES},
             "transformer_config": {"d_model": TR_D, "num_heads": TR_HEADS,
                                    "head_dim": TR_D // TR_HEADS, "ffn_dim": TR_FF},
             "gru_config": {"hidden": GRU_HID, "num_layers": 1, "bidirectional": False},
             "cnn_config": {"channels": CNN_C, "kernel": CNN_K, "layers": CNN_LAYERS,
                            "causal_left_pad": CNN_K - 1,
                            "receptive_field": CNN_LAYERS * (CNN_K - 1) + 1},
             "rwkv7_config": {"channels": RWKV_C, "head_size": RWKV_HEAD,
                              "n_head": RWKV_C // RWKV_HEAD, "lora_dim": RWKV_LORA,
                              "source_repo": "https://github.com/BlinkDL/RWKV-LM",
                              "source_commit": "952102498e9ed367ea0a59ee64106916d474d30f",
                              "source_license": "Apache-2.0",
                              "structure_ref": "RWKV-v7/rwkv_v7_demo.py 第209-289行 RWKV_Tmix_x070",
                              "init_ref": "RWKV-v7/train_temp/rwkv7_train_simplified.py 第66-146行",
                              "recurrence_ref": "RWKV-v7/rwkv_v7_demo.py 第168-200行 纯PyTorch参考路径",
                              "cuda_kernel_used": False},
             "impl_verification": IMPL,
             "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
             "lspr24": {"n_entity": int(N_ENT), "n_pos_entity": int(ent_lab.sum()),
                        "flow_pos_rate": _flow_pos, "entity_prior": float(ent_lab.mean())},
             "cells": RES, "selection": _frozen["cells"], "interaction": INTER,
             "mlp_protocolA_reference": MLP_A, "xgb_reference": XGB,
             "resume": {"cells_trained_this_process": _TRAINED_NOW,
                        "cells_resumed_from_disk": _TRAINED_RESUMED,
                        "cells_evaluated_this_process": _EVAL24_CALLS,
                        "cells_eval_resumed_from_disk": _EVAL24_RESUMED,
                        "gate_evidence": _GATE_EVIDENCE},
             "isolation": {"lspr24_disk_loads": _N24_LOADS,
                           "lspr24_evals_this_process": _EVAL24_CALLS,
                           "lspr24_evals_resumed": _EVAL24_RESUMED,
                           "lspr24_evals_total": _EVAL24_CALLS + _EVAL24_RESUMED}},
            f"{OUT}/ch3_backbone_protocolA_results.json")
log(f"全部结果已存 {OUT}/ch3_backbone_protocolA_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
