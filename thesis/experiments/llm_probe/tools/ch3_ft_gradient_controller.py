# -*- coding: utf-8 -*-
"""机制二：梯度控制器——单向 PCGrad 投影 + 范数上限（spec 5.5 节）。

公式（按 spec 5.5 节原样实现，不加下限夹紧、不改上限基准）：

    g_r^+ = g_r - (<g_r,g_f>/||g_f||^2) g_f   若 <g_r,g_f><0 且 ||g_f||>0（单向投影，只保护主任务）
    g_r^+ = g_r                                若 <g_r,g_f>>=0
    g_r^+ = 0                                  若 ||g_f||=0

    c = min(1, ||g_f|| / ||g_r^+||)   若 ||g_r^+||>0，否则 c=0
    g = g_f + z2 * c * g_r^+

该组合满足一阶不变量 <g,g_f> >= ||g_f||^2 且 ||c*g_r^+|| <= ||g_f||（由构造
保证，见本文件 `verify_first_order_invariants` 的核验与推导注释）。

设计前提（已实测，不要重新推导，见
`.Codex/docs/RWKV/2026-08-28-机制二梯度信号实测裁决.md`）：此前登记的
「范数上限在逐流梯度趋零时把排序梯度压至零」是推演错误，已被实测推翻——
收敛模型上 12 批中 9 批 c=1，控制器不压制排序梯度（收敛模型的 ||g_r|| 比
||g_f|| 塌缩得更快，故 ||g_f||/||g_r^+|| 恒大于 1）。本模块因此不引入下限
夹紧 c_min、不改上限基准 1，忠实实现 spec 5.5 节的原始形式。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))


def require(condition: bool, message: str) -> None:
    """运行断言：条件不满足即视为无效结果，立即停止，不吞掉错误。"""
    if not condition:
        raise RuntimeError(message)


def combine_gradients(g_flow: torch.Tensor, g_rank: torch.Tensor) -> tuple[torch.Tensor, dict[str, Any]]:
    """单向 PCGrad 投影 + 范数上限（spec 5.5 节原始形式）。

    g_flow: (P,) 逐流损失对共享参数的梯度（展平）；g_rank: (P,) 排序损失对
    共享参数的梯度（展平，未受控原始形式）。计算全程使用 FP32（阈值状态、
    CVaR 归约、梯度范数与投影按仓库合同须为 FP32，调用方须保证传入张量已是
    该精度；本函数不做隐式类型转换，以免掩盖上游精度错误）。

    返回 (合成梯度 g, 诊断字典)。诊断含两梯度范数、内积、余弦、投影是否触发、
    上限 c 的取值、受控后排序步长范数。
    """
    require(g_flow.dim() == 1 and g_rank.dim() == 1, "g_flow 与 g_rank 须为展平的一维张量")
    require(g_flow.shape == g_rank.shape, "g_flow 与 g_rank 形状须一致")
    require(g_flow.dtype == torch.float32 and g_rank.dtype == torch.float32, "梯度控制器要求 FP32 输入")

    norm_f = g_flow.norm()
    norm_r = g_rank.norm()
    inner = torch.dot(g_flow, g_rank)

    if float(norm_f) == 0.0:
        g_rank_plus = torch.zeros_like(g_rank)
        projection_triggered = False
    elif float(inner) < 0.0:
        g_rank_plus = g_rank - (inner / (norm_f**2)) * g_flow
        projection_triggered = True
    else:
        g_rank_plus = g_rank
        projection_triggered = False

    norm_r_plus = g_rank_plus.norm()
    if float(norm_r_plus) > 0.0:
        c = min(1.0, float(norm_f) / float(norm_r_plus))
    else:
        c = 0.0

    combined = g_flow + c * g_rank_plus

    diagnostics = {
        "grad_norm_flow": float(norm_f),
        "grad_norm_rank": float(norm_r),
        "grad_norm_rank_projected": float(norm_r_plus),
        "inner_product": float(inner),
        "cosine": float(inner / (norm_f * norm_r)) if float(norm_f) > 0 and float(norm_r) > 0 else 0.0,
        "projection_triggered": projection_triggered,
        "c_scaling": c,
        "controlled_rank_step_norm": float(c * norm_r_plus),
    }
    return combined, diagnostics


def verify_first_order_invariants(
    combined: torch.Tensor,
    g_flow: torch.Tensor,
    diagnostics: dict[str, Any],
    rtol: float = 1e-4,
) -> dict[str, Any]:
    """机械核验一阶不变量：<g,g_f> >= ||g_f||^2 且 ||c*g_r^+|| <= ||g_f||。

    推导（由 combine_gradients 的构造保证，本函数只做数值核验，不重新推导）：
    g = g_f + c*g_r^+，故 <g,g_f> = ||g_f||^2 + c*<g_r^+,g_f>。投影保证
    <g_r^+,g_f> >= 0（未投影时原本就 >=0；投影后恰好消去负分量至 0），c>=0，
    故乘积恒 >=0，第一个不变量恒成立。第二个不变量由 c=min(1,||g_f||/||g_r^+||)
    的定义直接给出：c*||g_r^+|| = min(||g_r^+||, ||g_f||) <= ||g_f||。

    rtol 是 FP32 舍入容差（相对容差，量级参考梯度范数本身），不是放宽数学
    定义——两个不等式在精确算术下均为等号或更强，容差只用于吸收浮点误差。
    """
    norm_f = g_flow.norm()
    inner_combined_flow = torch.dot(combined, g_flow)
    lhs1 = float(inner_combined_flow)
    rhs1 = float(norm_f**2)
    tol1 = rtol * max(abs(lhs1), abs(rhs1), 1e-12)
    invariant_1_holds = lhs1 >= rhs1 - tol1

    controlled_rank_step_norm = diagnostics["controlled_rank_step_norm"]
    tol2 = rtol * max(controlled_rank_step_norm, float(norm_f), 1e-12)
    invariant_2_holds = controlled_rank_step_norm <= float(norm_f) + tol2

    return {
        "invariant_1_inner_ge_norm_f_sq": {
            "holds": bool(invariant_1_holds),
            "lhs_inner_g_gf": lhs1,
            "rhs_norm_f_sq": rhs1,
            "margin": lhs1 - rhs1,
        },
        "invariant_2_controlled_rank_le_norm_f": {
            "holds": bool(invariant_2_holds),
            "lhs_controlled_rank_step_norm": controlled_rank_step_norm,
            "rhs_norm_f": float(norm_f),
            "margin": float(norm_f) - controlled_rank_step_norm,
        },
        "both_hold": bool(invariant_1_holds and invariant_2_holds),
    }


# --------------------------------------------------------------------------
# 真实数据核验：用任务 2 的真实 logit 产生 g_f 与 g_r，不用合成张量
# --------------------------------------------------------------------------


def _flat_grad(loss: torch.Tensor, params: list[torch.nn.Parameter]) -> torch.Tensor:
    """对共享参数求梯度并展平；未参与计算图的参数补零。"""
    grads = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True)
    pieces = [
        (torch.zeros_like(p) if g is None else g).reshape(-1) for p, g in zip(params, grads)
    ]
    return torch.cat(pieces).to(torch.float32)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument(
        "--checkpoint",
        default="runs/diagnostics/ch4-mlp-o11-oof-fold-models-seed42-v1/fold-0/checkpoints/selected-O11.pt",
    )
    parser.add_argument("--n-pos", type=int, default=2, help="诊断用，非冻结训练配置")
    parser.add_argument("--n-neg", type=int, default=64, help="诊断用，非冻结训练配置")
    parser.add_argument("--beta", type=float, default=0.04, help="诊断用 CVaR 预算比例，对齐探针脚本")
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    from ch3_ft_entity_ranking_loss import cvar_pauc_loss, prefix_scores
    from ch3_ft_entity_stratified_sampler import (
        EntityStratifiedSampler,
        EntityStratifiedSamplerConfig,
    )
    from ch4_mlp_o11_oof_fold_models_local_screen import LocalFullMLP

    cache_root = Path(args.cache_root).resolve()
    for name in ("X24", "y24", "I24", "M24", "E24", "T24"):
        require(not (cache_root / f"{name}.npy").is_file(), f"检测到目标年文件 {name}.npy")

    E = np.load(cache_root / "E23.npy")
    I = np.load(cache_root / "I23.npy", mmap_mode="r")
    M = np.load(cache_root / "M23.npy", mmap_mode="r")
    T = np.load(cache_root / "T23.npy")
    y = np.load(cache_root / "y23.npy")
    X = np.load(cache_root / "X23.npy", mmap_mode="r")
    print(f"缓存就绪：{len(E):,} 片段", flush=True)

    config = EntityStratifiedSamplerConfig(n_pos=args.n_pos, n_neg=args.n_neg)
    sampler = EntityStratifiedSampler(E, I, M, T, y, config)

    checkpoint_path = Path(args.checkpoint).resolve()
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    trained = LocalFullMLP(aggregate=True)
    trained.load_state_dict(payload["model"])
    trained.eval()
    print(f"加载检查点：{checkpoint_path}", flush=True)

    def _cap_segments_per_entity(rows: np.ndarray, entity_of_row: np.ndarray, max_segments: int) -> np.ndarray:
        """诊断脚本专用：每实体最多保留因果最早的 max_segments 个片段，避免吃到
        极端大袋（同 ch3_ft_entity_ranking_loss.py 的同名工具，独立实现避免耦合）。
        """
        if rows.size == 0:
            return rows
        boundaries = np.flatnonzero(np.r_[True, entity_of_row[1:] != entity_of_row[:-1]])
        ends = np.r_[boundaries[1:], len(entity_of_row)]
        parts = [rows[start : min(start + max_segments, end)] for start, end in zip(boundaries, ends)]
        return np.concatenate(parts)

    rng = np.random.default_rng(args.seed)
    params = [p for p in trained.parameters() if p.requires_grad]
    all_invariants_hold = True
    c_values: list[float] = []
    records: list[dict[str, Any]] = []

    for repeat in range(args.repeats):
        batch = sampler.sample(rng)
        rows = _cap_segments_per_entity(batch["segment_rows"], E[batch["segment_rows"]], max_segments=8)
        idx = np.asarray(I[rows])[:, :128]
        valid_np = np.asarray(M[rows])[:, :128] > 0
        values = torch.from_numpy(np.asarray(X[idx.reshape(-1)])).reshape(len(rows), 128, 83)
        valid = torch.from_numpy(valid_np)

        entity_raw = E[rows]
        unique_entities, segment_owner_np = np.unique(entity_raw, return_inverse=True)
        segment_owner = torch.from_numpy(segment_owner_np.astype(np.int64))
        entity_is_positive = torch.from_numpy(np.isin(unique_entities, batch["positive_entities"]))

        logits = trained(values, valid)
        flow_labels = torch.from_numpy(y[idx.reshape(-1)]).reshape(len(rows), 128)
        flow_loss = torch.nn.functional.binary_cross_entropy_with_logits(logits[valid], flow_labels[valid])

        entity_scores, _src = prefix_scores(logits, valid, segment_owner)
        pos_scores = entity_scores[entity_is_positive]
        neg_scores = entity_scores[~entity_is_positive]
        pairwise = torch.nn.functional.softplus(neg_scores.unsqueeze(0) - pos_scores.unsqueeze(1))
        n_neg = neg_scores.numel()
        k_cvar = max(1, int(np.ceil(args.beta * n_neg)))
        topk_vals, _ = torch.topk(pairwise, k=min(k_cvar, n_neg), dim=1)
        xi_cvar = topk_vals[:, -1].detach().unsqueeze(1)
        loss_cvar, _diag = cvar_pauc_loss(pos_scores, neg_scores, [k_cvar], xi_cvar)

        g_f = _flat_grad(flow_loss, params)
        g_r = _flat_grad(loss_cvar, params)

        combined, diag = combine_gradients(g_f, g_r)
        invariants = verify_first_order_invariants(combined, g_f, diag)

        all_invariants_hold = all_invariants_hold and invariants["both_hold"]
        c_values.append(diag["c_scaling"])
        records.append({"diagnostics": diag, "invariants": invariants})
        print(
            f"批 {repeat + 1}/{args.repeats}  ||g_f||={diag['grad_norm_flow']:.6g}  "
            f"||g_r||={diag['grad_norm_rank']:.6g}  c={diag['c_scaling']:.6g}  "
            f"投影触发={diag['projection_triggered']}  "
            f"不变量①={invariants['invariant_1_inner_ge_norm_f_sq']['holds']}  "
            f"不变量②={invariants['invariant_2_controlled_rank_le_norm_f']['holds']}",
            flush=True,
        )

    c_array = np.asarray(c_values)
    print("=== 汇总 ===", flush=True)
    print(f"c 中位数 = {float(np.median(c_array)):.6g}", flush=True)
    print(f"c==1 的批数 = {int((c_array >= 1.0 - 1e-9).sum())}/{args.repeats}", flush=True)
    print(f"投影触发批数 = {sum(1 for r in records if r['diagnostics']['projection_triggered'])}/{args.repeats}", flush=True)
    print(f"两条一阶不变量在全部 {args.repeats} 批上均成立 = {all_invariants_hold}", flush=True)
    print(
        f"参照：机制二梯度信号实测裁决报告——收敛模型 12 批中 9 批 c=1"
        "（本次用不同随机批与不同 xi 初始化，量级可比但具体计数不要求相同）",
        flush=True,
    )
    require(all_invariants_hold, "一阶不变量在真实梯度上不成立，按阻断条件停止")
    print("CH3_FT_GRADIENT_CONTROLLER_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
