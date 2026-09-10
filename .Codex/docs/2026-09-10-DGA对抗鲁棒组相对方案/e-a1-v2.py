#!/usr/bin/env python3
"""E-A1 v2：DGA 对抗规避病灶本地复现（零训练）。

判据（冻结 v2，2026-09-10，按文献代理对 CharBot/MaskDGA 原文的页码级核验修正）：
  良性流（T18 benign val）标定 FPR=1% 与 FPR=0.1% 阈值（CharBot §V p.5 口径）；
  对抗变体在该阈值下检出率相对干净 DGA 检出率的相对下降：
    >= 0.5 → 病灶坐实（CharBot 原文把未针对训练模型 TPR 压至 5.58%，相对降幅 >90%）；
    < 0.2  → 病灶不成立；之间 → 留主代理裁量。score<0.5 口径仅作参考（无文献对应）。
算子（冻结 v2，文献忠实版）：
  charbot2      随机替换 SLD 2 个不同位置，替换字符 [a-z0-9-] 均匀且异于原字符
                （CharBot 算法 1 §III p.4：仅替换、恰好 2 位、1 变体/域名、无优化）；
  maskdga-approx 随机替换 SLD 一半位置（MaskDGA 为 JSMA 显著度选择，本臂为无梯度
                随机近似，标注"非原文复现"；每位置只替换一次、禁止非点→点，§9 p.10）。
攻击面语义：扰动 DGA 域名 = MaskDGA 语义（对 AGD 加扰），不是 CharBot 复现。
协议：零训练；良性流仅阈值标定（无标签）；不读 T20+。样本 3 万（加速版，CharBot 原文 1 万）。
埋点三类；结果原子落盘。
"""
from __future__ import annotations

import argparse
import json
import random
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
DEVICE = torch.device("mps")
BATCH = 1024
ALPHA = "abcdefghijklmnopqrstuvwxyz0123456789-"


def perturb(domain: str, rng: random.Random) -> dict[str, str]:
    parts = domain.rsplit(".", 1)
    body = parts[0] if len(parts) == 2 else domain
    tail = "." + parts[1] if len(parts) == 2 else ""
    if len(body) < 4:
        return {}
    out: dict[str, str] = {}
    idxs = rng.sample(range(len(body)), 2)
    b = list(body)
    for i in idxs:
        c = rng.choice(ALPHA)
        while c == b[i]:
            c = rng.choice(ALPHA)
        b[i] = c
    v = "".join(b) + tail
    if v != domain:
        out["charbot2"] = v
    b = list(body)
    half = max(1, len(body) // 2)
    for i in rng.sample(range(len(body)), half):
        c = rng.choice(ALPHA)
        while c == b[i]:
            c = rng.choice(ALPHA)
        b[i] = c
    v2 = "".join(b) + tail
    if v2 != domain and v2 != out.get("charbot2"):
        out["maskdga-approx"] = v2
    return out


def score_domains(model, tokenizer, domains: list[str], tok_mean, char_mean) -> np.ndarray:
    parts = []
    with torch.inference_mode():  # 执行代理诊断缺陷 A 的修复：零训练评价必须包 inference_mode
        for off in range(0, len(domains), BATCH):
            chunk = domains[off:off + BATCH]
            tok = official.encode_subword(chunk, tokenizer).to(DEVICE)
            ch = official.encode_char(chunk).to(DEVICE)
            tf, cf = diag.branch_features(model, tok, ch)
            s = diag.probabilities(model, tf.cpu().numpy(), cf.cpu().numpy(),
                                   tok_mean, char_mean, DEVICE, BATCH)
            parts.append(s["static_fusion"])
            if (off // BATCH) % 20 == 0:
                done = min(off + BATCH, len(domains))
                print(f"[心跳] {done}/{len(domains)}", file=sys.stderr, flush=True)
    return np.concatenate(parts)


def main(limit: int = 15000, seed: int = 42) -> None:
    model = official.load_model(REF, CKPT, DEVICE)
    tokenizer = official.PreTrainedTokenizerFast(
        tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json")
    )
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_benign_val.parquet").to_pylist()[:limit]
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_dga_val.parquet").to_pylist()[:limit]
    benign = [str(r["domain"]) for r in tb]
    dga = [str(r["domain"]) for r in td]
    print(f"[E-A1 v2] 良性 {len(benign)} + DGA {len(dga)}", file=sys.stderr, flush=True)

    z = np.load("/tmp/drift-anchor-t17-features-300000.npz")
    tok_mean = z["tok"].mean(axis=0, dtype=np.float64).astype(np.float32)
    char_mean = z["char"].mean(axis=0, dtype=np.float64).astype(np.float32)

    # 1) 良性流分数 → FPR 标定阈值
    ben_scores = score_domains(model, tokenizer, benign, tok_mean, char_mean)
    th_fpr1 = float(np.quantile(ben_scores, 0.99))
    th_fpr01 = float(np.quantile(ben_scores, 0.999))
    th_half = 0.5
    print(f"[标定] FPR=1% 阈值={th_fpr1:.6f}  FPR=0.1% 阈值={th_fpr01:.6f}", file=sys.stderr, flush=True)

    # 2) 干净 DGA 检出率（各阈值）
    dga_scores = score_domains(model, tokenizer, dga, tok_mean, char_mean)
    res: dict = {}
    for name, th in (("fpr1", th_fpr1), ("fpr01", th_fpr01), ("half", th_half)):
        clean_det = float((dga_scores >= th).mean())
        res[name] = {"threshold": round(th, 6), "clean_detection": round(clean_det, 4)}

    # 3) 对抗变体生成与评价
    rng = random.Random(seed)
    variants: list[str] = []
    owner: list[int] = []
    kind: list[str] = []
    t0 = time.time()
    for idx, d in enumerate(dga):
        for op, v in perturb(d, rng).items():
            variants.append(v)
            owner.append(idx)
            kind.append(op)
    print(f"[生成] 变体 {len(variants)} 个，耗时 {time.time()-t0:.1f}s", file=sys.stderr, flush=True)
    adv_scores = score_domains(model, tokenizer, variants, tok_mean, char_mean)
    adv = np.asarray(adv_scores)
    kind_arr = np.asarray(kind)
    owner_arr = np.asarray(owner)

    for name, th in (("fpr1", th_fpr1), ("fpr01", th_fpr01), ("half", th_half)):
        for op in ("charbot2", "maskdga-approx"):
            sel = kind_arr == op
            det = float((adv[sel] >= th).mean())
            rel = 1 - det / res[name]["clean_detection"] if res[name]["clean_detection"] else None
            res[name][op] = {"adv_detection": round(det, 4), "relative_drop": round(rel, 4) if rel is not None else None}

    # 4) 裁决（主判据 = fpr1 阈值下两算子相对下降的最大值）
    drops = [res["fpr1"].get(op, {}).get("relative_drop") for op in ("charbot2", "maskdga-approx")]
    best = max((d for d in drops if d is not None), default=None)
    verdict = {"best_relative_drop": best,
               "criteria": {"病灶坐实": bool(best is not None and best >= 0.5),
                            "病灶不成立": bool(best is not None and best < 0.2),
                            "中间带（留裁量）": bool(best is not None and 0.2 <= best < 0.5)}}
    out_name = "ea1-result-DRYRUN.json" if limit < 15000 else "ea1-result.json"
    (OUT / out_name).write_text(json.dumps({"n_benign": len(benign), "n_dga": len(dga),
                                            "thresholds": {k: res[k]["threshold"] for k in res},
                                            "results": res, "verdict": verdict},
                                           ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[里程碑] {json.dumps(verdict, ensure_ascii=False)} -> {out_name}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=15000, help="每类样本数（全量 15000）")
    a = ap.parse_args()
    main(limit=a.limit)
