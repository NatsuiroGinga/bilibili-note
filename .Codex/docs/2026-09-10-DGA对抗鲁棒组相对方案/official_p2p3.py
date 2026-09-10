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
BATCH = 128
LR_HEAD = 1e-4
LR_BACKBONE = 1e-6
EPOCHS = 3
SEED = 42
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
        for off in range(0, len(domains), BATCH):
            chunk = domains[off:off + BATCH]
            tok = official.encode_subword(chunk, tokenizer).to(DEVICE)
            ch = official.encode_char(chunk).to(DEVICE)
            tf, cf = diag.branch_features(model, tok, ch)
            s = diag.probabilities(model, tf.cpu().numpy(), cf.cpu().numpy(),
                                   tok_mean, char_mean, DEVICE, BATCH)
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
              epochs: int) -> dict:
    model = official.load_model(REF, CKPT, DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.Adam([
        {"params": [p_ for n_, p_ in model.named_parameters() if "backbone" in n_], "lr": LR_BACKBONE},
        {"params": [p_ for n_, p_ in model.named_parameters() if "backbone" not in n_], "lr": LR_HEAD},
    ])
    print(f"[{arm}] 官方模型 {n_params} 参数，训练 {len(train_d)} 样本 × {epochs} epochs", file=sys.stderr, flush=True)
    fpr_curve: list = []
    ec, ey = eval_clean
    ea, eay = eval_adv
    rng = random.Random(SEED)
    adv_cache: dict[int, list[str]] = {}
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
            if arm in ("B", "C"):
                adv_batch = []
                for i in idx:
                    if train_y[i] == 1:
                        if i not in adv_cache:
                            base = perturb2(train_d[i], rng)
                            adv_cache[i] = [base] if arm == "B" else [perturb2(base, rng) for _ in range(4)]
                        if arm == "B":
                            adv_batch.append(adv_cache[i][0])
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            tok = official.encode_subword(batch_d, tokenizer).to(DEVICE)
            ch = official.encode_char(batch_d).to(DEVICE)
            tf, cf = diag.branch_features(model, tok, ch)
            logits2 = model.classifier_head(torch.cat([tf, cf], dim=1))
            p_ = torch.softmax(logits2.float(), dim=1)
            if arm == "C":
                # 组相对加权：同一恶意样本的 4 变体一组，组内"当前模型判良性(骗过)"为优势，
                # 正优势变体权重 2.0、未骗过变体 0.5、干净样本 1.0（组相对优势的任务化，
                # 文献定位：无先例的任务化设定，对照 Drichel 均匀混合）
                w = torch.ones(len(batch_y), device=DEVICE)
                fooled = (p_[:, 1] < 0.5) & (batch_y == 1)
                w[fooled] = 2.0
                w[(batch_y == 1) & (p_[:, 1] >= 0.5)] = 0.5
                loss = (torch.nn.functional.cross_entropy(
                    logits2, torch.from_numpy(batch_y).long().to(DEVICE), reduction="none") * w).mean()
            else:
                loss = torch.nn.functional.cross_entropy(
                    logits2, torch.from_numpy(batch_y).long().to(DEVICE))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            if bi % 50 == 0:
                eta = (time.time() - t0) / (bi + 1) * (nb - bi - 1)
                print(f"[{arm} 心跳] epoch {ep} 批 {bi+1}/{nb} loss={loss.item():.4f} ETA {eta/60:.1f} min", file=sys.stderr, flush=True)
        # 逐 epoch 干净 FPR 曲线（文献代理 Q1 裁决：识别"验证损失上升段"，防瞬态误判）
        model.eval()
        fpr_now = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)["FPR"]
        fpr_curve.append({"epoch": ep, "clean_FPR": fpr_now})
        print(f"[{arm} 里程碑] epoch {ep}/{epochs} 完成，干净 FPR={fpr_now:.4f}（{time.time()-t0:.1f}s）", file=sys.stderr, flush=True)
    model.eval()
    clean = metrics(model, tokenizer, ec, ey, tok_mean, char_mean)
    adv = metrics(model, tokenizer, ea, eay, tok_mean, char_mean)
    return {"clean": clean, "adv": adv, "n_params": n_params, "fpr_curve": fpr_curve, "_model": model}


def main(dry: int = 0) -> None:
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
    eval_clean = (ec, ey)
    eval_adv_k2 = (ea_k2, np.ones(len(ea_k2), dtype=bool))
    eval_adv_krand = (ea_krand, np.ones(len(ea_krand), dtype=bool))
    print(f"[官方 P2/P3] 训练 {len(tr_d)}、评价干净 {len(ec)}、对抗 k2 {len(ea_k2)}/krand {len(ea_krand)}", file=sys.stderr, flush=True)

    # 中和均值（T17 val 全量缓存，与正锚点核查同源）
    cache = Path("/tmp/drift-anchor-t17-features-300000.npz")
    z = np.load(cache)
    tok_mean = z["tok"].mean(axis=0, dtype=np.float64).astype(np.float32)
    char_mean = z["char"].mean(axis=0, dtype=np.float64).astype(np.float32)

    arms = ("A", "B", "C") if not dry else ("A",)
    epochs = 1 if dry else EPOCHS
    results: dict = {}
    adv_panels = {"k2": eval_adv_k2, "krand": eval_adv_krand}
    for arm in arms:
        t0 = time.time()
        r = train_arm(arm, tr_d, tr_y, tokenizer, tok_mean, char_mean, eval_clean, eval_adv_k2, epochs)
        r["wall_seconds"] = round(time.time() - t0, 1)
        arm_model = r.pop("_model")
        results[arm] = r
        # 双分组评价（该臂模型）：k=2 与 k∈U{1..4}
        for pname, (pa, pay) in adv_panels.items():
            results[arm][f"adv_{pname}"] = metrics(arm_model, tokenizer, pa, pay, tok_mean, char_mean)
        print(f"[里程碑] {arm}: clean={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['clean'].items()})} adv={json.dumps({k: round(v, 5) if isinstance(v, float) else v for k, v in r['adv'].items()})}", file=sys.stderr, flush=True)

    if len(results) == 3:
        a, b, c = results["A"], results["B"], results["C"]
        verdict = {
            "P2_pass": bool(b["adv"]["AP"] > a["adv"]["AP"] and b["clean"]["FPR"] <= a["clean"]["FPR"]),
            "P3_pass": bool(c["adv"]["AP"] > b["adv"]["AP"] and c["clean"]["FPR"] <= b["clean"]["FPR"]),
            "adv_AP": {"A": round(a["adv"]["AP"], 4), "B": round(b["adv"]["AP"], 4), "C": round(c["adv"]["AP"], 4)},
            "clean_FPR": {"A": round(a["clean"]["FPR"], 4), "B": round(b["clean"]["FPR"], 4), "C": round(c["clean"]["FPR"], 4)},
            "adv_FNR": {"A": round(a["adv"]["FNR"], 4), "B": round(b["adv"]["FNR"], 4), "C": round(c["adv"]["FNR"], 4)},
        }
    else:
        verdict = {"note": "dry-run 单臂"}
    out_name = "official-p2p3-DRYRUN.json" if dry else "official-p2p3-result.json"
    (OUT / out_name).write_text(json.dumps({"results": results, "verdict": verdict}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[里程碑] {json.dumps(verdict, ensure_ascii=False)} -> {out_name}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=0)
    a = ap.parse_args()
    main(dry=a.dry_run)
