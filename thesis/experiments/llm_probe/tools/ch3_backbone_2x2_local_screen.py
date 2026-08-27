# -*- coding: utf-8 -*-
"""第三章 Transformer / GRU 双骨干四格本机筛选（screening_only）。

唯一需求来源：.Codex/docs/RWKV/2026-08-27-三骨干消融本机筛选重跑/实施计划.md（U6 执行，筛选级）。
范围只含 transformer、gru 两骨干；一维卷积按 U6 定案剔除，不在本工具处理。

============================ Model 类的“import 复用”是怎么做到的 ============================
`ch3_backbone_protocolA_v2.py` 没有 `if __name__ == "__main__":` 守卫，是一个顶层脚本：
argparse 在模块顶层解析（第 109 行 `ARGS = _ap.parse_args()`）、LSPR23 六数组在模块顶层用
硬编码服务器路径加载（第 93-94 行 `ROOT="/root/autodl-tmp/..."`、第 271 行起 `np.load(...)`），
`Model` 类反而定义在这些顶层语句之后（第 502-578 行）。裸 `import` 该模块会先尝试解析我们自己的
sys.argv（缺 --backbone 会报错退出），即便侥幸绕过也会立刻在 np.load 里因为服务器绝对路径在本机
不存在而崩溃——且这一切都发生在 Model 类被定义之前。

本文件用以下受控方式让 Model 类等定义真正被“import 复用”而不是被复制重写：
  1. 用 `importlib.util.spec_from_file_location` 按磁盘路径构造模块对象，自己持有该对象的引用
     （不经 `import` 语句，也不写入 `sys.modules`——多进程/多次调用互不干扰）。
  2. 临时接管 `sys.argv`，传入 `--cells ""`（空格集合）与本机 scratch 输出根。源码里
     `CELL_SEL/CELLS` 由此变成空列表，`len(CELLS) < len(ALL_CELLS)` 恒真，源码第 833-839 行会在
     「阶段闸门」之前干净 `raise SystemExit(0)`——即闸门之前从不触碰 LSPR24，训练循环也不会执行。
  3. 临时把 `numpy.load` 重定向到本机真实缓存目录（源码硬编码的 CACHE 前缀是服务器路径，本机
     没有也不应该在文件系统里伪造出这个绝对路径）。
  4. `exec_module` 期间只捕获 `SystemExit(0)`；发生在 Model 类定义（502-578 行）与训练循环入口
     （833 行）之间的这次退出，不会撤销退出之前已经执行的顶层语句——`Model`、`RWKV7TimeMix`、
     `lp_pool`、`npar_formula`、`hid_of`、六个 LSPR23 数组、切分、损失权重全部已经写入
     `module.__dict__`。退出后立刻用 `module.__file__` 核验它确实来自
     `ch3_backbone_protocolA_v2.py`，而不是别的什么东西。
  5. 复用完毕立刻恢复 `sys.argv`、`numpy.load`，不污染调用方后续状态。

这样拿到的 `module.Model` 与服务器上真实训练时实例化的类是同一份代码对象，不是另写的“同构”副本；
副作用是顺带真实执行了一次 `_impl_verify()`（合成数据的掩码决定性/因果性检查，针对本次 --backbone），
其收据落在本工具的 import scratch 目录里，可作为额外的实现正确性证据。

本机训练循环（epoch 步进、优化器、断点、验证、源年实体 AP 评价）按该模块 train_and_select()/val_ap()
的训练语义在本文件内重写：剥离 CUDA 依赖，全程 fp32；X23 常驻 CPU（numpy），按批切片再 `.to(device)`
上卡，模式照 `ch4_mlp_o11_oof_fold_models_local_screen.py`。冻结配方（seed42、批 64、序列 128、
20 epoch×1000 步、实体不相交验证、逐 epoch argmax 选择、AdamW 权重衰减分组、梯度裁剪 1.0、
AUX_W=1.0 的 Lp 池化辅助损失）全部从 import 得到的 module 读取，不在本文件重复硬编码；
唯一按格/按骨干变化的超参数是学习率 lr。

============================ 学习率网格与出处（强制登记，见实施计划第二节）============================
每骨干 lr 网格 = {2e-3（原协议值，tools/ch3_backbone_protocolA_v2.py:705）}
              ∪ {该骨干在 .Codex/docs/RWKV/2026-08-17-第三章实验台账.md「等参数基线」章节
                 登记的选中 lr}，取并集去重：
  - transformer：台账选中 lr = 0.002（.Codex/docs/RWKV/2026-08-17-第三章实验台账.md:316，
    Transformer 等参数行）——与原协议值相同，网格坍缩为单点，lr-select 阶段直接冻结、无需 C00 对决。
  - gru        ：台账选中 lr = 0.0003（.Codex/docs/RWKV/2026-08-17-第三章实验台账.md:315，
    GRU 等参数行）——与原协议值不同，网格含两点，lr-select 阶段跑两次 C00 全量训练用 argmax
    验证逐流 AP 对决。台账 340 行明确该值只是网格下界（四档单调下降，网格未向下扩），
    非“已充分调参”，已作为 caveat 写入 lr_selection.json。

============================ 证据边界 ============================
`screening_only=true`，本机结果不进论文正式结果；`target_year_arrays_read` 全程为 0——本工具从不
加载 X24/y24/I24/M24/s24/d24/t24。判据用「源年（LSPR23）实体 AP 代理」代替正式的 LSPR24 实体 AP
（`evaluate_epoch()` 有完整口径说明），这是本机筛选与正式判据的口径差异，已在收据
`criterion.note` 显式登记；源年通过只作“值得上服务器”的信号，不等于正式通过。

============================ 2026-08-27 协调者更新（会话续接）============================
本骨干池选轮指标（逐流 AP）实测已饱和：格间差 3.39e-06 < 格内波动 6.37e-06，argmax 选轮的
分辨力很低。**仍按原冻结选轮规则实现，不擅自更换指标**——上面这句话只是解释了为什么额外
持久化了下面这条：每格收据（lr-select 的 C00 对决与 cells 的四格）现在都带一份
`epoch_history`（每 epoch 一条：`validation_flow_ap`——真正驱动 argmax 选择的信号，
`source_year_entity_ap`——诊断用的源年实体 AP 代理，二者由 `evaluate_epoch()` 单次前向
一并算出，不额外多扫一遍验证集），供事后诊断选轮盲区，不改变选择规则本身。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import average_precision_score

T0 = time.time()
TOOL_DIR = Path(__file__).resolve().parent
PROTOCOL_A_V2_PATH = TOOL_DIR / "ch3_backbone_protocolA_v2.py"
# 逐字取自 ch3_backbone_protocolA_v2.py 第 93-94 行 ROOT/CACHE 拼接结果（服务器路径，仅用于识别
# 该脚本会尝试 np.load 的前缀，再重定向到本机真实缓存目录；本机文件系统里不会出现这个路径）。
REMOTE_CACHE_PREFIX = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
RUN_ID_PREFIX = "ch3-backbone-2x2-local-screen-v1"

LEDGER_PATH = ".Codex/docs/RWKV/2026-08-17-第三章实验台账.md"
LR_GRID_SOURCE = {
    "transformer": {
        "ledger_best_lr": 0.002,
        "ledger_citation": f"{LEDGER_PATH}:316（Transformer 等参数行，选中 lr 列）",
    },
    "gru": {
        "ledger_best_lr": 0.0003,
        "ledger_citation": f"{LEDGER_PATH}:315（GRU 等参数行，选中 lr 列）",
        "ledger_caveat": (
            "GRU 择优 lr 落在网格下界：四档 0.0003/0.001/0.002/0.005 验证 AP 单调下降，网格只向上扩"
            "未向下扩，该值只能算下界，正文不得写「已充分调参」"
            f"（{LEDGER_PATH}:340）"
        ),
    },
}
ORIGINAL_PROTOCOL_LR = 2e-3
ORIGINAL_PROTOCOL_LR_CITATION = "tools/ch3_backbone_protocolA_v2.py:705（硬编码 2e-3，保偶然性对照）"


def log(msg: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {msg}", flush=True)


# =====================================================================================
# 原子写原语（重实现自 ch3_backbone_protocolA_v2.py 的持久化原语，纯 IO 工具函数，
# 与 Model 类等语义无关，按 ch4_mlp_o11_oof_fold_models_local_screen.py 的先例本地重写）
# =====================================================================================
def _fsync_dir(path: Path) -> None:
    fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    _fsync_dir(path)


def atomic_torch_save(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        torch.save(obj, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    _fsync_dir(path)


def load_ckpt(path: Path) -> Any:
    # torch 2.13.0 默认 weights_only=True 会拒绝反序列化 RNG 状态等对象，须显式关闭。
    return torch.load(path, map_location="cpu", weights_only=False)


def rng_snapshot(gen: torch.Generator) -> dict:
    return {
        "torch_cpu": torch.get_rng_state(),
        "numpy": np.random.get_state(),
        "python": random.getstate(),
        "batch_gen": gen.get_state(),
    }


def rng_restore(state: dict, gen: torch.Generator) -> None:
    torch.set_rng_state(state["torch_cpu"])
    np.random.set_state(state["numpy"])
    random.setstate(state["python"])
    gen.set_state(state["batch_gen"])
    # 已知放松：MPS 算子（如 Dropout）内部随机状态未单独快照——torch 2.13.0 未公开逐设备 MPS RNG
    # 状态 API。screening_only 场景可接受，恢复后数值不保证与不中断逐位相同，只保证训练能继续推进。


# =====================================================================================
# 数据就绪检查：X23.npy 可能仍在拉取（部分文件形如 .X23.npy.<random>），未就绪时清晰诊断退出，
# 不读取任何真实训练数据、不触发下面的 import 复用（该复用本身也需要 X23 才能走完）。
# =====================================================================================
def check_x23_ready(cache_root: Path) -> None:
    x23 = cache_root / "X23.npy"
    if x23.exists():
        return
    lines = [f"X23.npy 未就绪：{x23} 不存在。"]
    partials = sorted(cache_root.glob(".X23.npy.*"))
    if partials:
        sizes = ", ".join(f"{p.name}={p.stat().st_size / 2**30:.2f}GiB" for p in partials)
        lines.append(f"检测到下载中的部分文件：{sizes}（目标约 5.4GiB，需与最终文件大小核对）。")
    else:
        lines.append("未检测到 .X23.npy.* 部分文件，下载可能尚未开始或已用别的临时名。")
    lines.append("本工具在 X23 就绪前不读取任何真实训练数据，清晰退出（退出码 3）。")
    print("\n".join(lines), file=sys.stderr, flush=True)
    raise SystemExit(3)


# =====================================================================================
# Model 类等的“受控 import 复用”，见文件头长注释
# =====================================================================================
def import_protocolA_v2_reused(backbone: str, cache_root: Path, scratch_root: Path):
    original_load = np.load

    def _redirected_load(file, *args, **kwargs):
        s = str(file)
        if s.startswith(REMOTE_CACHE_PREFIX):
            rel = s[len(REMOTE_CACHE_PREFIX):].lstrip("/")
            file = str(cache_root / rel)
        return original_load(file, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "_ch3_backbone_protocolA_v2_reused_for_local_screen", PROTOCOL_A_V2_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法为 {PROTOCOL_A_V2_PATH} 构造 import spec")
    module = importlib.util.module_from_spec(spec)

    saved_argv = sys.argv
    sys.argv = [
        "ch3_backbone_protocolA_v2.py",
        "--backbone", backbone,
        "--out-root", str(scratch_root),
        "--cells", "",
    ]
    np.load = _redirected_load
    log(
        f"受控执行 {PROTOCOL_A_V2_PATH.name}（--cells 空集合）以 import 复用 Model 类，"
        "预期在阶段闸门前 SystemExit(0)"
    )
    try:
        spec.loader.exec_module(module)
        raise RuntimeError(
            f"{PROTOCOL_A_V2_PATH.name} 未按预期在空格集合分支 SystemExit——源码结构可能已变化，"
            "import 复用假设失效，须人工核对该文件第 833-839 行"
        )
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise RuntimeError(
                f"{PROTOCOL_A_V2_PATH.name} 以非零码 {exc.code} 退出，import 复用失败"
            ) from exc
    finally:
        sys.argv = saved_argv
        np.load = original_load

    if module.__file__ is None or Path(module.__file__).resolve() != PROTOCOL_A_V2_PATH.resolve():
        raise RuntimeError(
            f"模块来源核验失败：module.__file__={module.__file__!r} != {PROTOCOL_A_V2_PATH}"
        )
    required = (
        "Model", "lp_pool", "npar_formula", "hid_of", "ALL_CELLS",
        "D", "L", "BS", "SEED", "AUX_W", "VAL_FRAC", "TIME_TAIL",
        "TR_D", "TR_HEADS", "TR_FF", "GRU_HID", "HID", "N_EPOCH", "EPOCH_STEPS",
        "X23", "y23", "I23", "M23", "E23", "T23", "tr_idx", "val_idx",
        "_pos", "_spw",
    )
    missing = [name for name in required if not hasattr(module, name)]
    if missing:
        raise RuntimeError(f"import 复用后缺少属性：{missing}；源文件结构可能已变化")
    log(
        f"import 复用成功：module.__file__={module.__file__}，module.Model={module.Model!r}"
        "（确系同一份代码，非复制重写）"
    )
    return module


# =====================================================================================
# 设备与优化器
# =====================================================================================
def select_device(name: str) -> torch.device:
    if name == "cpu":
        return torch.device("cpu")
    if name == "mps":
        if not torch.backends.mps.is_available():
            raise RuntimeError("请求 --device mps 但当前环境 MPS 不可用")
        return torch.device("mps")
    return torch.device("mps" if torch.backends.mps.is_available() else "cpu")


def build_optimizer(model: torch.nn.Module, lr: float) -> torch.optim.Optimizer:
    # 权重衰减分组逐字照抄 ch3_backbone_protocolA_v2.py 第 702-705 行。
    decay = [p for n, p in model.named_parameters() if not (n.endswith(".bias") or n == "p_log")]
    no_decay = [p for n, p in model.named_parameters() if (n.endswith(".bias") or n == "p_log")]
    return torch.optim.AdamW(
        [{"params": decay, "weight_decay": 0.01}, {"params": no_decay, "weight_decay": 0.0}],
        lr=lr,
    )


# =====================================================================================
# lr 网格（去重后的并集，含出处）
# =====================================================================================
def lr_grid_for(backbone: str) -> list[dict]:
    src = LR_GRID_SOURCE[backbone]
    candidates = [
        {"lr": ORIGINAL_PROTOCOL_LR, "origin": "protocolA_v2_original", "citation": ORIGINAL_PROTOCOL_LR_CITATION},
        {"lr": src["ledger_best_lr"], "origin": "ledger_best", "citation": src["ledger_citation"]},
    ]
    dedup: dict[float, dict] = {}
    for c in candidates:
        key = float(c["lr"])
        if key in dedup:
            dedup[key]["origins"].append(c["origin"])
            dedup[key]["citations"].append(c["citation"])
        else:
            dedup[key] = {"lr": key, "origins": [c["origin"]], "citations": [c["citation"]]}
    grid = sorted(dedup.values(), key=lambda d: d["lr"])
    if "ledger_caveat" in src:
        for entry in grid:
            if "ledger_best" in entry["origins"]:
                entry["caveat"] = src["ledger_caveat"]
    return grid


# =====================================================================================
# 单次前向扫过 LSPR23 实体不相交验证集，同时产出两个指标：
#   1) flow_ap        ：逐流 AP，语义照抄 ch3_backbone_protocolA_v2.py 的 val_ap()（第 590-608
#                       行）——冻结选轮信号，argmax 规则不变（2026-08-27 协调者更新：该指标已
#                       实测饱和，格间差 3.39e-06 < 格内波动 6.37e-06，选轮分辨力很低，但仍按
#                       计划用原冻结选轮规则实现，不擅自更换指标）。
#   2) entity_ap      ：源年（LSPR23）实体级 AP 代理，仅作诊断——不是正式判据用的 ent_ap()。
#                       正式 ent_ap() 按 s24/d24 拼出的流级实体键 ent24 聚合流级分数；LSPR23
#                       缓存只暴露序列级实体号 E23（切分用途，非逐流实体键），因此改为两级聚合：
#                         第一级 序列内：把该验证序列内逐流概率聚合成一个序列级分数——lp=True 用
#                           模型自身学到的 p 做 Lp 池化（module.lp_pool，即 ELP 机制本身）；
#                           lp=False 取序列内最大值（与正式 ent_ap 的 max 口径一致）。
#                         第二级 序列间：同一实体（E23 相同）可能有多条验证序列，取这些序列级
#                           分数的最大值作为该实体的最终预测分；实体标签取其名下验证序列标签
#                           （序列内 amax）的最大值。
#                       这一构造与正式 LSPR24 的 ent_ap() 不是同一函数、不是同一数据，只用作
#                       本机筛选/选轮盲区诊断信号，metric 字段固定标注 source_year_proxy，
#                       调用方不得把它当成正式判据数字使用。
# 两个指标合并成一次前向扫描（而不是分别调用两个函数各扫一遍验证集），是应协调者
#（2026-08-27）要求——「每格收据额外持久化逐轮源年实体AP，若成本允许」——采取的效率设计：
# 复用同一批 logits/概率，避免每 epoch 对 22,444 条验证序列多做一次完整前向。
# =====================================================================================
@torch.no_grad()
def evaluate_epoch(model: torch.nn.Module, module, device: torch.device, seq_len: int, lp: bool) -> dict:
    model.eval()
    X23, y23, I23, M23, E23 = module.X23, module.y23, module.I23, module.M23, module.E23
    val_idx = module.val_idx
    p_value = float(model.p.item()) if lp else None

    flow_preds: list[np.ndarray] = []
    flow_labels: list[np.ndarray] = []
    seq_scores = np.empty(len(val_idx), dtype=np.float64)
    seq_labels = np.empty(len(val_idx), dtype=np.float64)
    chunk = 1024
    for start in range(0, len(val_idx), chunk):
        rows = val_idx[start:start + chunk]
        idx = I23[rows][:, :seq_len]
        valid_np = M23[rows][:, :seq_len] > 0
        values = torch.from_numpy(X23[idx.reshape(-1)]).reshape(len(rows), seq_len, module.D).to(device)
        mask = torch.from_numpy(valid_np.astype(np.float32)).to(device)
        probs = torch.sigmoid(model(values, mask))
        flat_mask = valid_np.reshape(-1)
        flow_preds.append(probs.reshape(-1).float().cpu().numpy()[flat_mask])
        flow_labels_np = y23[idx.reshape(-1)].reshape(idx.shape)
        flow_labels.append(flow_labels_np.reshape(-1)[flat_mask])
        if lp:
            pooled = module.lp_pool(probs.clamp(1e-7, 1.0), mask, model.p)
        else:
            pooled = torch.where(mask > 0.5, probs, torch.zeros_like(probs)).amax(dim=1)
        seq_scores[start:start + len(rows)] = pooled.double().cpu().numpy()
        seq_labels[start:start + len(rows)] = (flow_labels_np * valid_np).max(axis=1)
    model.train()

    flow_p = np.concatenate(flow_preds)
    flow_y = np.concatenate(flow_labels)
    assert flow_y.max() > 0, "验证集无正例，选择信号无效"
    flow_ap = float(average_precision_score(flow_y, flow_p))

    ent = E23[val_idx]
    uniq_ent = np.unique(ent)
    remap = {int(e): i for i, e in enumerate(uniq_ent)}
    ent_pos = np.fromiter((remap[int(e)] for e in ent), dtype=np.int64, count=len(ent))
    ent_score = np.full(len(uniq_ent), -np.inf, dtype=np.float64)
    ent_label = np.zeros(len(uniq_ent), dtype=np.float64)
    np.maximum.at(ent_score, ent_pos, seq_scores)
    np.maximum.at(ent_label, ent_pos, seq_labels)
    entity_ap = float(average_precision_score(ent_label, ent_score))

    return {
        "flow_ap": flow_ap,
        "entity_ap": entity_ap, "entity_ap_metric": "source_year_proxy",
        "n_entities": int(len(uniq_ent)), "n_positive_entities": int(ent_label.sum()),
        "p_used": p_value,
    }


# =====================================================================================
# 可断点续训的单格训练：lr-select 阶段的 C00 对决与 cells 阶段的四格训练共用本函数。
# 训练循环语义照抄 ch3_backbone_protocolA_v2.py 的 train_and_select()（第 695-774 行），
# 剥离 CUDA 依赖、改为按批 CPU→device 上卡，lr 改为入参而非硬编码 2e-3。
# =====================================================================================
def train_cell(
    *, module, backbone: str, agg: bool, lp: bool, lr: float, seed: int,
    n_epoch: int, epoch_steps: int, batch_size: int, seq_len: int,
    device: torch.device, cell_dir: Path, tag: str,
) -> dict:
    selected_path = cell_dir / "selected.pt"
    inflight_path = cell_dir / "inflight.pt"
    if selected_path.exists():
        payload = load_ckpt(selected_path)
        log(f"{tag} 已完成，跳过训练：选中 epoch={payload['epoch']} 验证AP={payload['val_ap']:.6f}")
        return payload

    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    model = module.Model(backbone, agg, lp).to(device)
    optimizer = build_optimizer(model, lr)
    generator = torch.Generator().manual_seed(seed)
    pos_weight = module._pos.to(device)
    spw = float(module._spw)
    flow_loss_fn = torch.nn.BCEWithLogitsLoss(reduction="none", pos_weight=pos_weight)
    aux_loss_fn = torch.nn.BCELoss(reduction="none")

    best: dict[str, Any] = {"ap": -1.0, "epoch": None, "p": None, "state": None,
                            "entity_ap": None, "entity_ap_detail": None}
    history: list[dict[str, Any]] = []
    start_epoch = 1
    prev_seconds = 0.0

    if inflight_path.exists():
        ck = load_ckpt(inflight_path)
        assert ck["tag"] == tag, f"{tag} 在途检查点身份不符：{ck['tag']}"
        assert ck["lr"] == lr, f"{tag} 在途检查点 lr 不符：{ck['lr']} != {lr}"
        model.load_state_dict(ck["model"])
        optimizer.load_state_dict(ck["optimizer"])
        best = ck["best"]
        history = list(ck["history"])
        prev_seconds = float(ck["train_seconds"])
        rng_restore(ck["rng"], generator)
        start_epoch = int(ck["epoch"]) + 1
        log(f"{tag} 从在途检查点恢复：已完成 epoch {ck['epoch']}，从 epoch {start_epoch} 继续")

    train_rows = module.tr_idx
    X23, y23, I23, M23 = module.X23, module.y23, module.I23, module.M23
    started = time.time()
    model.train()
    for epoch in range(start_epoch, n_epoch + 1):
        running_loss = 0.0
        for step in range(1, epoch_steps + 1):
            positions = torch.randint(0, len(train_rows), (batch_size,), generator=generator).numpy()
            rows = train_rows[positions]
            idx = I23[rows][:, :seq_len]
            valid_np = M23[rows][:, :seq_len] > 0
            values = torch.from_numpy(X23[idx.reshape(-1)]).reshape(batch_size, seq_len, module.D).to(device)
            labels = torch.from_numpy(y23[idx.reshape(-1)].reshape(idx.shape)).to(device)
            mask = torch.from_numpy(valid_np.astype(np.float32)).to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(values, mask)
            loss = (flow_loss_fn(logits, labels.float()) * mask).sum() / mask.sum().clamp(min=1)
            if lp:
                probs = torch.sigmoid(logits)
                pooled = module.lp_pool(probs, mask, model.p).clamp(1e-6, 1 - 1e-6)
                seq_labels_t = (labels.float() * mask).amax(1)
                weights = 1.0 + (spw - 1.0) * seq_labels_t
                loss = loss + module.AUX_W * ((aux_loss_fn(pooled, seq_labels_t) * weights).sum() / weights.sum())
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            running_loss += float(loss.detach())
            if step % 250 == 0:
                elapsed = time.time() - started
                done = (epoch - 1) * epoch_steps + step
                total = n_epoch * epoch_steps
                remain_min = (elapsed / max(done, 1)) * (total - done) / 60
                log(f"{tag} epoch={epoch}/{n_epoch} step={step}/{epoch_steps} 剩余约={remain_min:.1f}分")
        metrics = evaluate_epoch(model, module, device, seq_len, lp)
        val_ap = metrics["flow_ap"]
        entity_ap = metrics["entity_ap"]
        p_value = float(model.p.item())
        history.append({
            "epoch": epoch, "validation_flow_ap": val_ap, "p": p_value,
            "source_year_entity_ap": entity_ap, "source_year_entity_ap_n_entities": metrics["n_entities"],
        })
        star = ""
        if val_ap > best["ap"]:
            best = {
                "ap": val_ap, "epoch": epoch, "p": p_value,
                "state": {k: v.detach().cpu().clone() for k, v in model.state_dict().items()},
                "entity_ap": entity_ap, "entity_ap_detail": metrics,
            }
            star = "  ← 当前最优"
        cum = prev_seconds + (time.time() - started)
        atomic_torch_save(
            {
                "tag": tag, "backbone": backbone, "agg": agg, "lp": lp, "lr": lr, "seed": seed,
                "epoch": epoch, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                "best": best, "history": history, "train_seconds": cum, "rng": rng_snapshot(generator),
            },
            inflight_path,
        )
        log(
            f"{tag} ep {epoch:>2}/{n_epoch} 验证逐流AP={val_ap:.6f} 源年实体AP代理={entity_ap:.6f} "
            f"p={p_value:.4f} 平均损失={running_loss / epoch_steps:.4f} 累计{cum / 60:.1f}分{star}"
        )
    train_seconds = prev_seconds + (time.time() - started)
    payload = {
        "tag": tag, "backbone": backbone, "agg": agg, "lp": lp, "lr": lr, "seed": seed,
        "n_epoch": n_epoch, "epoch_steps": epoch_steps, "epoch": best["epoch"],
        "val_ap": best["ap"], "p": best["p"], "state": best["state"],
        "entity_ap": best["entity_ap"], "entity_ap_detail": best["entity_ap_detail"],
        "history": history,
        "train_seconds": train_seconds, "screening_only": True, "target_year_arrays_read": 0,
    }
    atomic_torch_save(payload, selected_path)
    log(
        f"{tag} 训练完成 {train_seconds / 60:.2f} 分，选中 epoch={best['epoch']} "
        f"验证逐流AP={best['ap']:.6f} 源年实体AP代理={best['entity_ap']:.6f}"
    )
    return payload


# =====================================================================================
# --stage lr-select
# =====================================================================================
def lr_select_stage(args: argparse.Namespace, module) -> dict:
    backbone = args.backbone
    grid = lr_grid_for(backbone)
    out_dir = Path(args.output_root) / backbone
    receipt_path = out_dir / "lr_selection.json"
    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        log(f"{backbone} lr-select 已完成（{receipt_path}），跳过：selected_lr={existing['selected_lr']}")
        return existing

    base_receipt = {
        "run_id": f"{RUN_ID_PREFIX}-{backbone}-lr-select", "backbone": backbone,
        "screening_only": True, "target_year_arrays_read": 0, "grid": grid,
    }
    if len(grid) == 1:
        selected = grid[0]
        receipt = {
            **base_receipt, "collapsed": True,
            "collapse_note": "原协议值与台账择优 lr 相同，网格坍缩为单点，无需 C00 对决",
            "duels": [], "selected_lr": selected["lr"], "selected_origin": selected["origins"],
            "selected_citations": selected["citations"], "ts": time.time(),
        }
        atomic_json(receipt_path, receipt)
        log(f"{backbone} lr 网格坍缩为单点 lr={selected['lr']:g}，直接冻结，出处：{selected['citations']}")
        return receipt

    duels = []
    for candidate in grid:
        lr = candidate["lr"]
        tag = f"{backbone}-lrselect-lr{lr:g}-C00"
        cell_dir = out_dir / "lr_select" / f"lr-{lr:g}"
        payload = train_cell(
            module=module, backbone=backbone, agg=False, lp=False, lr=lr, seed=module.SEED,
            n_epoch=module.N_EPOCH, epoch_steps=module.EPOCH_STEPS, batch_size=module.BS,
            seq_len=module.L, device=args.torch_device, cell_dir=cell_dir, tag=tag,
        )
        duels.append({
            "lr": lr, "origins": candidate["origins"], "citations": candidate["citations"],
            "caveat": candidate.get("caveat"), "selected_epoch": payload["epoch"],
            "val_ap": payload["val_ap"], "train_seconds": payload["train_seconds"],
            "source_year_entity_ap": payload.get("entity_ap"),
            "epoch_history": payload["history"],
        })
        log(f"{backbone} lr={lr:g} C00 对决完成：验证AP={payload['val_ap']:.6f}")

    winner = max(duels, key=lambda d: d["val_ap"])
    receipt = {
        **base_receipt, "collapsed": False, "duels": duels,
        "selected_lr": winner["lr"], "selected_origin": winner["origins"],
        "selected_citations": winner["citations"],
        "selection_rule": "argmax 验证逐流 AP（LSPR23 实体不相交验证集，C00 单元）", "ts": time.time(),
    }
    atomic_json(receipt_path, receipt)
    log(f"{backbone} lr-select 完成，胜出 lr={winner['lr']:g}（验证AP={winner['val_ap']:.6f}）")
    return receipt


# =====================================================================================
# --stage cells
# =====================================================================================
def cells_stage(args: argparse.Namespace, module) -> dict:
    backbone = args.backbone
    out_dir = Path(args.output_root) / backbone
    lr_receipt_path = out_dir / "lr_selection.json"
    if not lr_receipt_path.exists():
        raise SystemExit(
            f"{backbone} 缺少 {lr_receipt_path}，请先运行 --stage lr-select 冻结学习率再跑 cells"
        )
    lr_receipt = json.loads(lr_receipt_path.read_text(encoding="utf-8"))
    lr = float(lr_receipt["selected_lr"])

    results_path = out_dir / "ch3_backbone_2x2_local_screen_results.json"
    if results_path.exists():
        existing = json.loads(results_path.read_text(encoding="utf-8"))
        log(f"{backbone} cells 已完成（{results_path}），跳过")
        return existing

    cells: dict[str, dict] = {}
    for cell_id, agg, lp in module.ALL_CELLS:
        tag = f"{backbone}-{cell_id}"
        cell_dir = out_dir / "cells" / tag
        payload = train_cell(
            module=module, backbone=backbone, agg=agg, lp=lp, lr=lr, seed=module.SEED,
            n_epoch=module.N_EPOCH, epoch_steps=module.EPOCH_STEPS, batch_size=module.BS,
            seq_len=module.L, device=args.torch_device, cell_dir=cell_dir, tag=tag,
        )
        # entity_ap 已在 train_cell 选中 best 的那一 epoch 由 evaluate_epoch() 算出并随
        # payload 落盘（同一次前向复用，见 evaluate_epoch 文档），此处不再重建模型重跑一遍。
        entity_ap = payload["entity_ap"]
        cells[cell_id] = {
            "cell": cell_id, "agg": agg, "lp": lp, "selected_epoch": payload["epoch"],
            "validation_flow_ap": payload["val_ap"], "p_at_selection": payload["p"],
            "train_seconds": payload["train_seconds"],
            "source_year_entity_ap": entity_ap, "source_year_entity_ap_detail": payload["entity_ap_detail"],
            "epoch_history": payload["history"],
        }
        log(f"{tag} 源年实体AP代理={entity_ap:.6f}")

    c00 = cells["C00"]["source_year_entity_ap"]
    c01 = cells["C01"]["source_year_entity_ap"]
    c10 = cells["C10"]["source_year_entity_ap"]
    c11 = cells["C11"]["source_year_entity_ap"]
    criterion = {
        "metric": "source_year_entity_ap_proxy",
        "note": (
            "判据用源年（LSPR23）实体AP代理，本机无目标年（LSPR24）——与正式判据口径不同，"
            "源年通过只作值得上服务器的信号，不等于正式通过"
        ),
        "c01_gt_c00": bool(c01 > c00), "c10_gt_c00": bool(c10 > c00),
        "c11_ge_max": bool(c11 >= max(c00, c01, c10)),
    }
    criterion["screening_pass"] = bool(
        criterion["c01_gt_c00"] and criterion["c10_gt_c00"] and criterion["c11_ge_max"]
    )
    result = {
        "run_id": f"{RUN_ID_PREFIX}-{backbone}-cells", "backbone": backbone,
        "screening_only": True, "target_year_arrays_read": 0,
        "lr_selection": {"selected_lr": lr, "receipt": str(lr_receipt_path)},
        "cells": cells, "criterion": criterion, "ts": time.time(),
    }
    atomic_json(results_path, result)
    log(
        f"{backbone} 四格完成，判据={'通过' if criterion['screening_pass'] else '不通过'}："
        f"C00={c00:.6f} C01={c01:.6f} C10={c10:.6f} C11={c11:.6f}"
    )
    return result


# =====================================================================================
# --smoke-test：跑通首个 optimizer step 的最小真实检查（验收第 3 条），不算科学验证，
# 独立于 --stage 的断点/收据体系，不与 lr-select/cells 的产物混写。
# =====================================================================================
def smoke_stage(args: argparse.Namespace, module) -> dict:
    backbone = args.backbone
    device = args.torch_device
    torch.manual_seed(module.SEED)
    np.random.seed(module.SEED)
    model = module.Model(backbone, True, True).to(device)  # C11 同时覆盖 agg 与 lp 两条前向路径
    optimizer = build_optimizer(model, lr=ORIGINAL_PROTOCOL_LR)
    rows = module.tr_idx[: module.BS]
    idx = module.I23[rows][:, : module.L]
    valid_np = module.M23[rows][:, : module.L] > 0
    values = torch.from_numpy(module.X23[idx.reshape(-1)]).reshape(len(rows), module.L, module.D).to(device)
    labels = torch.from_numpy(module.y23[idx.reshape(-1)].reshape(idx.shape)).to(device)
    mask = torch.from_numpy(valid_np.astype(np.float32)).to(device)
    flow_loss_fn = torch.nn.BCEWithLogitsLoss(reduction="none", pos_weight=module._pos.to(device))
    aux_loss_fn = torch.nn.BCELoss(reduction="none")

    optimizer.zero_grad(set_to_none=True)
    logits = model(values, mask)
    loss = (flow_loss_fn(logits, labels.float()) * mask).sum() / mask.sum().clamp(min=1)
    probs = torch.sigmoid(logits)
    pooled = module.lp_pool(probs, mask, model.p).clamp(1e-6, 1 - 1e-6)
    seq_labels_t = (labels.float() * mask).amax(1)
    weights = 1.0 + (float(module._spw) - 1.0) * seq_labels_t
    loss = loss + module.AUX_W * ((aux_loss_fn(pooled, seq_labels_t) * weights).sum() / weights.sum())
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
    optimizer.step()

    loss_value = float(loss.detach().cpu())
    grad_value = float(grad_norm.detach().cpu())
    ok = math.isfinite(loss_value) and loss_value > 0 and math.isfinite(grad_value) and grad_value > 0
    receipt = {
        "backbone": backbone, "device": str(device), "loss": loss_value, "grad_norm": grad_value,
        "finite_nonzero_ok": bool(ok), "note": "最小真实检查，不算科学验证（验收第 3 条）",
        "screening_only": True, "target_year_arrays_read": 0, "ts": time.time(),
    }
    out_path = Path(args.output_root) / backbone / "_smoke" / "first_optimizer_step.json"
    atomic_json(out_path, receipt)
    log(f"{backbone} smoke：loss={loss_value:.6f} grad_norm={grad_value:.6f} 通过={ok}")
    if not ok:
        raise SystemExit(f"{backbone} smoke 检查未通过：loss={loss_value} grad_norm={grad_value}")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="第三章 Transformer/GRU 双骨干四格本机筛选（screening_only）")
    parser.add_argument("--backbone", required=True, choices=["transformer", "gru"])
    parser.add_argument("--stage", choices=["lr-select", "cells"], default=None)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "mps"])
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID_PREFIX}")
    parser.add_argument(
        "--smoke-test", action="store_true",
        help="只跑首个 optimizer step 的最小真实检查（验收第3条），忽略 --stage",
    )
    args = parser.parse_args()
    if not args.smoke_test and args.stage is None:
        parser.error("--stage {lr-select,cells} 是必需参数（除非使用 --smoke-test）")

    cache_root = Path(args.cache_root)
    check_x23_ready(cache_root)

    args.torch_device = select_device(args.device)
    log(f"骨干={args.backbone} 阶段={'smoke-test' if args.smoke_test else args.stage} 设备={args.torch_device}")

    output_root = Path(args.output_root)
    scratch_root = output_root / args.backbone / "_protocolA_v2_import_scratch"
    module = import_protocolA_v2_reused(args.backbone, cache_root, scratch_root)

    if args.smoke_test:
        smoke_stage(args, module)
    elif args.stage == "lr-select":
        lr_select_stage(args, module)
    else:
        cells_stage(args, module)
    return 0


if __name__ == "__main__":
    sys.exit(main())
