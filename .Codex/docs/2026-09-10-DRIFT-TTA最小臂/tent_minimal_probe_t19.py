#!/usr/bin/env python3
"""TENT 式测试时适应最小臂（DRIFT TTA 家族第一棒，N13）。

判据（冻结，2026-09-10，出数即裁决）：
  适应后 vs 适应前（同流 T18 test 全量）：ΔFPR ≤ 0 且（ΔFNR < 0 或 ΔAP > 0）
  → TTA 家族获得 DRIFT 正增益资格；
  FPR 恶化 = "熵陷阱"预注册失败形态；
  两者皆无 = 无改善，TTA 家族在 DRIFT 关闭（转下一家族）。
规格（冻结）：
  - 更新对象：全部 nn.LayerNorm 的 affine（weight/bias），主干其余与分类头冻结
  - 损失：预测熵 mean(-Σ p log p)（softmax 两类）
  - 协议：online 单 pass——批 i 到达→当前模型预测并记录→以该批熵更新→下一批
  - 适应数据：T18 val 无标签流（文档代理 D2 核验：T18 test 已在官方训练集内，val 为留出流；标签只用于事后评价）
  - 优化器：Adam lr=1e-4（TENT 原文起始值，任务化设定，无最优声明）
  - 评价：适应前静态锚（同脚本先算）与适应后全量对比；单列"TTA 适应协议"表，
    披露"目标知情（无标签输入分布参与适应）"，不入静态基线表
埋点：进度（批级）、生效性（参数更新是否非零）、异常（梯度范数）三类。
断点：适应后 state_dict 原子落盘；--dry-run 走同一代码路径。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch

ROOT = Path("/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe")
sys.path.insert(0, str(ROOT / "tools"))
import ch3_drift_official_branch_conflict_diagnostic as diag
import ch3_drift_official_checkpoint_t17_eval as official

REF = ROOT / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
CKPT = ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"
DATA = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521"
OUT = Path(__file__).resolve().parent
BATCH = 128  # TENT 原文值（§3.3：BS=128/LR=0.001 配对）；batch 1024 反向 MPS OOM 实测
DEVICE = torch.device("mps")
LR = 1e-3  # TENT 原文（§3.3 非数据集：Adam, LR=0.001, BS=128）；原文页码已入库 raw/papers/attack-detection/tent-iclr2021-wang.pdf


def load_test_domains(limit: int | None = None) -> tuple[list[str], np.ndarray]:
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T19_benign_val.parquet").to_pylist()
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T19_dga_val.parquet").to_pylist()
    if limit:
        tb, td = tb[: limit // 2], td[: limit // 2]
    domains = [str(r["domain"]) for r in tb] + [str(r["domain"]) for r in td]
    labels = np.asarray([0] * len(tb) + [1] * len(td), dtype=np.int64)
    # TENT 原文 §3.3："We control for ordering by shuffling and sharing the order across methods."
    rng = np.random.default_rng(42)
    order = rng.permutation(len(domains))
    return [domains[i] for i in order], labels[order]


def forward_probs(model, tokenizer, domains: list[str], tok_mean, char_mean) -> dict[str, np.ndarray]:
    tok_feat, char_feat = diag.extract_features(model, tokenizer, domains, DEVICE, BATCH)
    probs = diag.probabilities(model, tok_feat, char_feat, tok_mean, char_mean, DEVICE, BATCH)
    return probs


def metrics(labels01: np.ndarray, scores: np.ndarray, threshold: float = 0.5) -> dict:
    from sklearn.metrics import average_precision_score, roc_auc_score

    pred = scores >= threshold
    mal, ben = labels01, ~labels01
    fp = int((pred & ben).sum())
    fn = int((~pred & mal).sum())
    tp = int((pred & mal).sum())
    tn = int((~pred & ben).sum())
    return {
        "AP": float(average_precision_score(labels01, scores)),
        "AUROC": float(roc_auc_score(labels01, scores)),
        "FPR": fp / max(fp + tn, 1),
        "FNR": fn / max(fn + tp, 1),
        "F1": tp / max(tp + 0.5 * (fp + fn), 1),
        "FP": fp, "FN": fn, "TP": tp, "TN": tn, "n": int(len(labels01)),
    }


def main(limit: int | None = None, lr: float = LR) -> None:
    model = official.load_model(REF, CKPT, DEVICE)
    tokenizer = official.PreTrainedTokenizerFast(
        tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json")
    )
    domains, labels = load_test_domains(limit)
    labels01 = labels == 1  # shuffle 后与 domains 对齐
    print(f"[TENT] T19 流：{len(domains)} 域（无标签适应，标签仅事后评价）", file=sys.stderr, flush=True)

    # 适应前静态锚
    probs0 = forward_probs(model, tokenizer, domains, None, None) if False else None
    # 静态评价需要中和均值：用 T17 缓存特征均值（与正锚点核查同源）
    cache = Path("/tmp/drift-anchor-t17-features-300000.npz") if limit is None else Path(f"/tmp/drift-anchor-t17-features-{2*limit}.npz")
    if not cache.is_file():
        # 干跑缓存缺失：从 T17 val 头部提取等量域的特征并落盘（与全量同语义）
        t17b = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_benign_val.parquet").to_pylist()
        t17d = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_dga_val.parquet").to_pylist()
        neutral = [str(r["domain"]) for r in (t17b + t17d)[: cache.stem.split("-")[-1] and int(cache.stem.split("-")[-1])]]
        tok_feat, char_feat = diag.extract_features(model, tokenizer, neutral, DEVICE, BATCH)
        np.savez(cache, tok=tok_feat, char=char_feat)
        print(f"[断点] 干跑缓存已提取落盘：{cache}", file=sys.stderr, flush=True)
    z = np.load(cache)
    tok_mean = z["tok"].mean(axis=0, dtype=np.float64).astype(np.float32)
    char_mean = z["char"].mean(axis=0, dtype=np.float64).astype(np.float32)
    probs0 = forward_probs(model, tokenizer, domains, tok_mean, char_mean)
    m0 = metrics(labels01, probs0["static_fusion"])
    print(f"[静态锚 C00] {json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in m0.items()})}", file=sys.stderr, flush=True)

    # 冻结非 LN-affine 参数
    ln_params = []
    for name, p_ in model.named_parameters():
        if "layer_norm" in name.lower() or ("norm" in name.lower() and p_.dim() == 1 and "embedding" not in name.lower()):
            p_.requires_grad_(True)
            ln_params.append(name)
        else:
            p_.requires_grad_(False)
    print(f"[生效性] LN affine 参数张量数={len(ln_params)}，可训练参数量={sum(p.numel() for n, p in model.named_parameters() if p.requires_grad)}", file=sys.stderr, flush=True)
    opt = torch.optim.Adam([p_ for p_ in model.parameters() if p_.requires_grad], lr=lr)

    # online 单 pass：批 i → 当前模型预测记录 → 熵更新
    model.eval()  # LN 平移变体登记：TENT 原文 train 模式是为 BN 统计重估（LN 无统计）；本模型 head 有 Dropout，train 模式会污染熵计算——偏离点已登记方案 §九
    preds_online: list[np.ndarray] = []
    ent_online: list[float] = []
    t0 = time.time()
    n_batches = (len(domains) + BATCH - 1) // BATCH
    grad_norms: list[float] = []
    for bi in range(n_batches):
        chunk = domains[bi * BATCH : (bi + 1) * BATCH]
        tok_ids = official.encode_subword(chunk, tokenizer).to(DEVICE)
        char_ids = official.encode_char(chunk).to(DEVICE)
        tf, cf = diag.branch_features(model, tok_ids, char_ids)
        logits = model.classifier_head(torch.cat([tf, cf], dim=1))
        p_ = torch.softmax(logits.float(), dim=1)
        preds_online.append(p_[:, 1].detach().cpu().numpy())
        ent = -(p_ * torch.log(p_.clamp(min=1e-12))).sum(dim=1).mean()
        opt.zero_grad(set_to_none=True)
        ent.backward()
        gnorm = torch.nn.utils.clip_grad_norm_([p_ for p_ in model.parameters() if p_.requires_grad], 1e9).item()
        grad_norms.append(gnorm)
        opt.step()
        ent_online.append(float(ent.item()))
        if bi % 20 == 0 or bi == n_batches - 1:
            eta = (time.time() - t0) / (bi + 1) * (n_batches - bi - 1)
            print(f"[心跳] 适应批 {bi+1}/{n_batches} 熵={ent_online[-1]:.4f} 梯度范数={gnorm:.4f} ETA {eta/60:.1f} min", file=sys.stderr, flush=True)

    # 适应后全量评价（eval 模式）
    model.eval()
    probs1 = forward_probs(model, tokenizer, domains, tok_mean, char_mean)
    m1 = metrics(labels01, probs1["static_fusion"])
    print(f"[适应后] {json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in m1.items()})}", file=sys.stderr, flush=True)

    delta = {k: m1[k] - m0[k] for k in ("AP", "AUROC", "FPR", "FNR", "F1")}
    verdict = {
        "delta": {k: round(v, 6) for k, v in delta.items()},
        "criteria_pass": bool(delta["FPR"] <= 0 and (delta["FNR"] < 0 or delta["AP"] > 0)),
        "entropy_trap": bool(delta["FPR"] > 0),
        "no_improvement": bool(delta["FNR"] >= 0 and delta["AP"] <= 0 and delta["FPR"] >= 0),
    }
    # 适应后 state_dict 原子落盘
    sd_path = Path(f"/tmp/drift-tent-t19-lr{lr}{'-dry' if limit else ''}.pt")
    tmp = sd_path.with_suffix(".tmp")
    torch.save(model.state_dict(), tmp)
    tmp.replace(sd_path)
    out = {
        "static_before": m0, "adapted_after": m1, "verdict": verdict,
        "entropy_trace_head": ent_online[:10], "grad_norm_head": grad_norms[:10],
        "ln_param_tensors": len(ln_params), "lr": lr,
        "protocol": "TTA 适应协议（目标知情：无标签 test 输入分布参与适应；标签仅事后评价）",
        "screening_only": True,
    }
    out_name = "tent-result-T19-DRYRUN.json" if limit else "tent-result-T19.json"
    (OUT / out_name).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[里程碑] 完成，判定 {json.dumps(verdict)} -> {out_name}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=None, help="每类截取前 N/2 行干跑")
    ap.add_argument("--lr", type=float, default=LR)
    a = ap.parse_args()
    main(limit=a.dry_run, lr=a.lr)
