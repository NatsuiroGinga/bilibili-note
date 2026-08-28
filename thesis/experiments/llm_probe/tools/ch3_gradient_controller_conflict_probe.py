# -*- coding: utf-8 -*-
"""机制二梯度控制器冲突实测：在已收敛模型上量 ‖g_f‖ 与 ‖g_r‖。

被检验的论断（此前只有公式推演，无实测）：机制二 5.5 节的范数上限

    c = min(1, ‖g_f‖ / ‖g_r⁺‖),   g = g_f + z2 · c · g_r⁺

在逐流梯度范数趋零时把排序梯度压至零，而逐流饱和正是机制二的立题场景。

实测设计：用第四章已训练收敛的 MLP O11 折外模型（LSPR23 源年，bf16 服务器训练）
在同一批数据上分别求逐流 BCE 与实体排序损失对共享参数的梯度，报告

- ‖g_f‖、‖g_r‖、两者夹角余弦；
- c = min(1, ‖g_f‖/‖g_r‖) 与受控后的排序步长 ‖c·g_r⁺‖；
- 与随机初始化模型的同口径对照，给出「训练前→收敛后」的变化倍数。

若收敛模型上 c 远小于 1 且 ‖c·g_r⁺‖ 相对未受控的 ‖g_r‖ 下降一个数量级以上，
则冲突为实测确认；若 c 接近 1，则该顾虑不成立。

证据边界：MLP 骨干、单折、单批次量级诊断，用于裁决控制器设计，不用于任何
模型效果论断。LSPR24 读取为 0。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from ch4_mlp_o11_oof_fold_models_local_screen import LocalFullMLP  # noqa: E402

RUN_ID = "ch3-gradient-controller-conflict-probe-v1"
SCHEMA_VERSION = "ch3-gradient-controller-conflict-receipt-v1"
SERVER_D0_RUN_ID = "ch4-mlp-o11-oof-fold-models-seed42-v1"
SEQ_LEN = 128
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:6.1f}s] {message}", flush=True)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def flat_grad(loss: torch.Tensor, params: list[torch.nn.Parameter]) -> torch.Tensor:
    """对共享参数求梯度并展平；未参与计算图的参数补零。"""
    grads = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True)
    pieces = [
        (torch.zeros_like(p) if g is None else g).reshape(-1)
        for p, g in zip(params, grads)
    ]
    return torch.cat(pieces)


def entity_scores(
    logits: torch.Tensor,
    valid: torch.Tensor,
    entity_ids: torch.Tensor,
    entity_positive: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor] | None:
    """实体路径最大分数与标签；与部署侧的路径最大口径一致。"""
    scores: dict[int, torch.Tensor] = {}
    labels: dict[int, bool] = {}
    for row in range(logits.shape[0]):
        row_valid = valid[row]
        if not bool(row_valid.any()):
            continue
        entity = int(entity_ids[row])
        row_max = logits[row][row_valid].max()
        scores[entity] = row_max if entity not in scores else torch.maximum(scores[entity], row_max)
        labels[entity] = labels.get(entity, False) or bool(entity_positive[row])
    positives = [scores[e] for e, is_pos in labels.items() if is_pos]
    negatives = [scores[e] for e, is_pos in labels.items() if not is_pos]
    if not positives or not negatives:
        return None
    return torch.stack(positives), torch.stack(negatives)


def ranking_loss(
    logits: torch.Tensor,
    valid: torch.Tensor,
    entity_ids: torch.Tensor,
    entity_positive: torch.Tensor,
    beta: float | None = None,
) -> torch.Tensor | None:
    """实体排序损失。

    ``beta=None``：普通 RankNet，对全部负实体取均值——即「随机负例」基线。
    ``beta=b``：CVaR 形式，每个正实体只对损失最高的前 ``ceil(b·N_-)`` 个负实体取均值，
    对应机制二 5.3 节按假阳率预算聚焦最难良性实体的设计。两者共享同一实体分数，
    唯一差别是负实体的聚合方式，因此可直接归因。
    """
    pair = entity_scores(logits, valid, entity_ids, entity_positive)
    if pair is None:
        return None
    pos, neg = pair
    losses = torch.nn.functional.softplus(neg.unsqueeze(0) - pos.unsqueeze(1))
    if beta is None:
        return losses.mean()
    k = max(1, int(np.ceil(beta * neg.numel())))
    topk, _ = torch.topk(losses, k=k, dim=1)
    return topk.mean()


def measure(
    model: torch.nn.Module,
    values: torch.Tensor,
    valid: torch.Tensor,
    flow_labels: torch.Tensor,
    entity_ids: torch.Tensor,
    entity_positive: torch.Tensor,
    beta: float = 0.04,
) -> dict[str, Any] | None:
    params = [p for p in model.parameters() if p.requires_grad]
    logits = model(values, valid)
    flow_loss = torch.nn.functional.binary_cross_entropy_with_logits(
        logits[valid], flow_labels[valid]
    )
    rank = ranking_loss(logits, valid, entity_ids, entity_positive, beta=None)
    rank_cvar = ranking_loss(logits, valid, entity_ids, entity_positive, beta=beta)
    if rank is None or rank_cvar is None:
        return None
    g_f = flat_grad(flow_loss, params)
    g_r = flat_grad(rank, params)
    g_r_cvar = flat_grad(rank_cvar, params)
    norm_f = float(g_f.norm())
    norm_r = float(g_r.norm())
    norm_r_cvar = float(g_r_cvar.norm())
    inner = float(torch.dot(g_f, g_r))
    cosine = inner / (norm_f * norm_r) if norm_f > 0 and norm_r > 0 else 0.0
    # 单向 PCGrad 投影：只在冲突时投影
    if inner < 0 and norm_f > 0:
        g_r_proj = g_r - (inner / (norm_f**2)) * g_f
    else:
        g_r_proj = g_r
    norm_r_proj = float(g_r_proj.norm())
    c = min(1.0, norm_f / norm_r_proj) if norm_r_proj > 0 else 0.0
    return {
        "flow_loss": float(flow_loss.detach()),
        "ranking_loss": float(rank.detach()),
        "ranking_loss_cvar": float(rank_cvar.detach()),
        "grad_norm_flow": norm_f,
        "grad_norm_rank": norm_r,
        "grad_norm_rank_cvar": norm_r_cvar,
        "cvar_over_plain_grad_ratio": (norm_r_cvar / norm_r) if norm_r > 0 else float("inf"),
        "grad_norm_rank_projected": norm_r_proj,
        "cosine": cosine,
        "projection_triggered": bool(inner < 0),
        "c_scaling": c,
        "controlled_rank_step_norm": c * norm_r_proj,
        "rank_step_attenuation": (c * norm_r_proj / norm_r) if norm_r > 0 else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--d0-root", default=f"runs/diagnostics/{SERVER_D0_RUN_ID}")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    parser.add_argument("--fold", type=int, default=0)
    parser.add_argument("--batch-sequences", type=int, default=64)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    cache_root = Path(args.cache_root).resolve()
    output_root = Path(args.output_root).resolve()
    atomic_json(output_root / "status.json", {"run_id": RUN_ID, "state": "running", "target_reads": 0})

    X = np.load(cache_root / "X23.npy", mmap_mode="r")
    I = np.load(cache_root / "I23.npy", mmap_mode="r")
    M = np.load(cache_root / "M23.npy", mmap_mode="r")
    E = np.load(cache_root / "E23.npy")
    y = np.load(cache_root / "y23.npy")
    log(f"缓存就绪：{len(E):,} 片段")

    checkpoint_path = Path(args.d0_root).resolve() / f"fold-{args.fold}" / "checkpoints" / "selected-O11.pt"
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    identity = payload.get("identity", {})
    if identity.get("run_id") != SERVER_D0_RUN_ID or identity.get("fold") != args.fold:
        raise RuntimeError(f"检查点身份不符：{checkpoint_path}")
    log(f"加载已训练检查点 fold-{args.fold}")

    trained = LocalFullMLP(aggregate=True)
    trained.load_state_dict(payload["model"])
    trained.eval()
    torch.manual_seed(42)
    untrained = LocalFullMLP(aggregate=True)
    untrained.eval()

    rng = np.random.default_rng(42)
    records: dict[str, list[dict[str, Any]]] = {"trained": [], "untrained": []}
    attempts = 0
    while len(records["trained"]) < args.repeats and attempts < args.repeats * 20:
        attempts += 1
        rows = rng.choice(len(E), size=args.batch_sequences, replace=False)
        rows = np.sort(rows)
        idx = np.asarray(I[rows])[:, :SEQ_LEN]
        valid_np = np.asarray(M[rows])[:, :SEQ_LEN] > 0
        values = torch.from_numpy(np.asarray(X[idx.reshape(-1)])).reshape(
            len(rows), SEQ_LEN, 83
        )
        valid = torch.from_numpy(valid_np)
        labels = torch.from_numpy(y[idx.reshape(-1)]).reshape(len(rows), SEQ_LEN)
        entity_ids = torch.from_numpy(E[rows])
        seq_positive = torch.from_numpy(
            np.array([bool(y[idx[r][valid_np[r]]].max() > 0.5) if valid_np[r].any() else False
                      for r in range(len(rows))])
        )
        if not bool(seq_positive.any()):
            continue
        result_trained = measure(trained, values, valid, labels, entity_ids, seq_positive)
        result_untrained = measure(untrained, values, valid, labels, entity_ids, seq_positive)
        if result_trained is None or result_untrained is None:
            continue
        records["trained"].append(result_trained)
        records["untrained"].append(result_untrained)
        log(
            f"批 {len(records['trained'])}/{args.repeats}  已训练 ‖g_f‖={result_trained['grad_norm_flow']:.6g} "
            f"‖g_r‖={result_trained['grad_norm_rank']:.6g} c={result_trained['c_scaling']:.6g}"
        )

    def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
        keys = [
            "flow_loss", "ranking_loss", "ranking_loss_cvar",
            "grad_norm_flow", "grad_norm_rank", "grad_norm_rank_cvar",
            "cvar_over_plain_grad_ratio",
            "cosine", "c_scaling", "controlled_rank_step_norm", "rank_step_attenuation",
        ]
        return {k: float(np.median([item[k] for item in items])) for k in keys}

    trained_summary = summarize(records["trained"])
    untrained_summary = summarize(records["untrained"])
    verdict = {
        "controller_conflict_confirmed": bool(
            trained_summary["c_scaling"] < 0.1
            and trained_summary["c_scaling"] < untrained_summary["c_scaling"]
        ),
        "controller_criterion": "收敛模型上 c<0.1 且低于随机初始化时的 c，则确认控制器在逐流饱和后压制排序梯度",
        "plain_ranking_signal_collapsed": bool(
            trained_summary["grad_norm_rank"] < 1e-6 * max(trained_summary["grad_norm_flow"], 1e-12)
        ),
        "plain_ranking_criterion": "收敛模型上普通 RankNet 梯度范数比逐流梯度低六个数量级以上，则确认随机负例无排序信号",
        "cvar_restores_signal": bool(trained_summary["cvar_over_plain_grad_ratio"] > 10.0),
        "cvar_criterion": "CVaR 梯度范数比普通 RankNet 高一个数量级以上，则确认按预算聚焦最难负例可恢复排序信号",
    }

    atomic_json(
        output_root / "gradient-controller-conflict.json",
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": RUN_ID,
            "evidence_tier": "screening_only_single_fold_mlp_backbone",
            "target_reads": 0,
            "checkpoint": str(checkpoint_path),
            "fold": args.fold,
            "batch_sequences": args.batch_sequences,
            "batches": len(records["trained"]),
            "trained_median": trained_summary,
            "untrained_median": untrained_summary,
            "verdict": verdict,
            "per_batch": records,
        },
    )
    atomic_json(
        output_root / "status.json",
        {"run_id": RUN_ID, "state": "finished", "exit_code": 0, "target_reads": 0},
    )
    log("=== 中位数结果 ===")
    for name, summary in (("已训练收敛", trained_summary), ("随机初始化", untrained_summary)):
        log(
            f"{name}: 逐流损失={summary['flow_loss']:.6g} ‖g_f‖={summary['grad_norm_flow']:.6g} "
            f"‖g_r‖(普通)={summary['grad_norm_rank']:.6g} ‖g_r‖(CVaR)={summary['grad_norm_rank_cvar']:.6g} "
            f"CVaR/普通={summary['cvar_over_plain_grad_ratio']:.6g} c={summary['c_scaling']:.6g}"
        )
    log(f"裁决①控制器冲突={verdict['controller_conflict_confirmed']}")
    log(f"裁决②普通排序信号消失={verdict['plain_ranking_signal_collapsed']}")
    log(f"裁决③CVaR 恢复信号={verdict['cvar_restores_signal']}")
    print("CH3_GRADIENT_CONTROLLER_PROBE_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
