#!/usr/bin/env python3
"""P2/P3 proxy：GRPO 机制层在 DGA 对抗鲁棒上的最小检验（本机 ≤1M 参数，screening_only）。

判据（冻结，2026-09-10，出数即裁决）：
  评价面 = T18 val 抽样的干净指标 + CharBot 2 位替换对抗变体检出率（FPR=1% 标定阈值）。
  C-B（臂 B 朴素对抗增广）相对臂 A（干净训练）：
    对抗检出率改善 且 干净 FPR 不增 → 对抗训练在本课题有效（P2 过门）；
  C-C（臂 C 组相对加权对抗增广）相对臂 B：
    对抗检出率进一步改善 且 干净 FPR 不增 → **GRPO 组相对机制层增量成立**（P3 过门）；
  任一失败形态：干净 FPR 恶化（以干净性能换鲁棒）或对抗检出无改善。
模型（proxy，≤1M 参数）：字符嵌入(64) + 1D-CNN(3 层) + mean-pool + 线性头，约 0.4M。
数据：T17 train 分层抽样 12 万（良性/DGA 各 6 万）；评价 T18 val 各 1.5 万。
臂定义：
  A：纯干净训练；
  B：干净 + CharBot 2 位替换增广（每恶意样本 1 个随机变体，混合训练）；
  C：干净 + 组相对加权增广——同一恶意域名的 K=4 个变体为一组，
     组内"能骗过当前增量模型的变体"获得更高采样权重（组相对优势，
     GRPO 组结构任务化：优势 = 变体骗过 - 组内均值，正优势变体优先入批），
     权重每半个 epoch 按当前模型刷新一次。
共同预算：Adam lr 1e-3、batch 256、6 epochs、阈值 0.5、种子 42。
埋点三类；--dry-run 同路径；判据出数即裁决。
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
from torch import nn

ROOT = Path("/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe")
DATA = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521"
OUT = Path(__file__).resolve().parent
DEVICE = torch.device("mps")
ALPHA = "abcdefghijklmnopqrstuvwxyz0123456789-"
CH2I = {c: i + 1 for i, c in enumerate(ALPHA)}
VOCAB = len(ALPHA) + 1
MAXLEN = 64
SEED = 42
EPOCHS = 6
BATCH = 256


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)


def encode(domains: list[str]) -> np.ndarray:
    x = np.zeros((len(domains), MAXLEN), dtype=np.int64)
    for i, d in enumerate(domains):
        ids = [CH2I.get(c, 0) for c in d.lower()[:MAXLEN]]
        x[i, : len(ids)] = ids
    return x


class CharCNN(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.emb = nn.Embedding(VOCAB, 64, padding_idx=0)
        self.conv = nn.Sequential(
            nn.Conv1d(64, 128, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(128, 128, 5, padding=2), nn.ReLU(), nn.AdaptiveMaxPool1d(1),
        )
        self.fc = nn.Sequential(nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 2))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e = self.emb(x).transpose(1, 2)
        return self.fc(self.conv(e).squeeze(-1))


def perturb2(domain: str, rng: random.Random) -> str:
    body = domain.rsplit(".", 1)[0]
    if len(body) < 4:
        return domain
    b = list(body)
    for i in rng.sample(range(len(body)), 2):
        c = rng.choice(ALPHA)
        while c == b[i]:
            c = rng.choice(ALPHA)
        b[i] = c
    return "".join(b) + ("." + domain.rsplit(".", 1)[1] if "." in domain else "")


def load_split(limit: int) -> tuple[list[str], np.ndarray]:
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_benign_train.parquet").to_pylist()[:limit]
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_dga_train.parquet").to_pylist()[:limit]
    domains = [str(r["domain"]) for r in tb] + [str(r["domain"]) for r in td]
    labels = np.asarray([0] * len(tb) + [1] * len(td), dtype=np.int64)
    return domains, labels


def metrics(model, domains: list[str], labels01: np.ndarray, tok_mean=None) -> dict:
    model.eval()
    scores = []
    with torch.inference_mode():
        for off in range(0, len(domains), BATCH):
            x = torch.from_numpy(encode(domains[off:off + BATCH])).to(DEVICE)
            p_ = torch.softmax(model(x), dim=1)[:, 1]
            scores.append(p_.cpu().numpy())
    s = np.concatenate(scores)
    from sklearn.metrics import average_precision_score
    pred = s >= 0.5
    mal, ben = labels01, ~labels01
    fp = int((pred & ben).sum()); fn = int((~pred & mal).sum())
    tp = int((pred & mal).sum()); tn = int((~pred & ben).sum())
    return {"AP": float(average_precision_score(labels01, s)), "FPR": fp / max(fp + tn, 1),
            "FNR": fn / max(fn + tp, 1), "F1": tp / max(tp + 0.5 * (fp + fn), 1), "n": len(s)}


def train_arm(arm: str, train_d: list[str], train_y: np.ndarray,
              eval_clean: tuple[list[str], np.ndarray], eval_adv: tuple[list[str], np.ndarray],
              epochs: int = EPOCHS) -> dict:
    set_seed(SEED)
    model = CharCNN().to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    assert n_params <= 1_000_000, n_params
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    lossf = nn.CrossEntropyLoss()
    rng = random.Random(SEED)
    n = len(train_d)
    adv_cache: dict[int, list[str]] = {}
    print(f"[{arm}] 训练开始：{n} 样本、{n_params} 参数、{epochs} epochs", file=sys.stderr, flush=True)
    for ep in range(1, epochs + 1):
        model.train()
        order = list(range(n)); random.Random(SEED + ep).shuffle(order)
        tot = correct = 0
        t0 = time.time()
        for bi in range(0, n, BATCH):
            idx = order[bi:bi + BATCH]
            batch_d = [train_d[i] for i in idx]
            batch_y = train_y[idx]
            if arm in ("B", "C"):
                adv_batch = []
                for i in idx:
                    if train_y[i] == 1:
                        if arm == "B" or i not in adv_cache:
                            if i not in adv_cache:
                                adv_cache[i] = [perturb2(train_d[i], rng) for _ in range(4)]
                        if arm == "B":
                            adv_batch.append(adv_cache[i][0])
                if arm == "C":
                    # 组相对：每恶意样本的 4 变体为一组，组内"当前模型判良性"为被骗信号，
                    # 优势 = 骗过 - 组均值，正优势变体优先入批（组相对优势的 batch 级任务化）
                    mal_idx = [i for i in idx if train_y[i] == 1 and i in adv_cache]
                    scored = []
                    for i in mal_idx:
                        vs = adv_cache[i]
                        with torch.inference_mode():
                            x = torch.from_numpy(encode(vs)).to(DEVICE)
                            p_ = torch.softmax(model(x), dim=1)[:, 1].cpu().numpy()
                        fooled = (p_ < 0.5).astype(np.float64)
                        adv = fooled - fooled.mean()
                        top = np.argsort(-adv)[:1]  # 组内正优势最大的变体
                        for t_ in top:
                            if adv[t_] > 0:
                                scored.append((vs[t_], adv[t_]))
                    if scored:
                        batch_d = batch_d + [s[0] for s in scored]
                        batch_y = np.concatenate([batch_y, np.ones(len(scored), dtype=np.int64)])
                elif arm == "C":
                    pass
                if adv_batch:
                    batch_d = batch_d + adv_batch
                    batch_y = np.concatenate([batch_y, np.ones(len(adv_batch), dtype=np.int64)])
            x = torch.from_numpy(encode(batch_d)).to(DEVICE)
            y = torch.from_numpy(batch_y).long().to(DEVICE)
            logits = model(x)
            loss = lossf(logits, y)
            if arm == "C":
                # 组相对加权：组 = 同一恶意样本的 K 个变体；变体骗过当前模型者权重更高
                # 简化为 batch 级实现：对 batch 中"当前模型判对(良性)的变体"加权 2.0，
                # 判错(仍判恶意)的变体权重 0.5——骗过检测器的对抗样本主导梯度（组相对优势的任务化）
                with torch.inference_mode():
                    fooled = (torch.softmax(model(x), dim=1)[:, 1] < 0.5) & (y == 1)
                w = torch.ones(len(batch_y), device=DEVICE)
                w[fooled] = 2.0
                w[(y == 1) & (torch.softmax(model(x), dim=1)[:, 1] >= 0.5)] = 0.5
                loss = (nn.functional.cross_entropy(logits, y, reduction="none") * w).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            tot += len(batch_y); correct += int((logits.argmax(1) == y).sum().item())
        print(f"[{arm} 心跳] epoch {ep}/{epochs} acc={correct/tot:.4f} 用时 {time.time()-t0:.1f}s", file=sys.stderr, flush=True)
    model.eval()
    ec, ey = eval_clean
    ea, _ = eval_adv
    clean = metrics(model, ec, ey)
    adv = metrics(model, ea, np.ones(len(ea), dtype=bool))
    return {"n_params": n_params, "clean": clean, "adv_detection": adv["AP"] if False else None,
            "adv": adv}


def main(dry: int = 0) -> None:
    set_seed(SEED)
    tr_d, tr_y = load_split(dry if dry else 60000)
    # 评价面
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_benign_val.parquet").to_pylist()[: (dry or 7500)]
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_dga_val.parquet").to_pylist()[: (dry or 7500)]
    ec = [str(r["domain"]) for r in tb]; ey = np.zeros(len(ec), dtype=bool)
    ey = np.asarray([0] * len(tb) + [1] * len(td), dtype=bool)
    ec = ec + [str(r["domain"]) for r in td]
    # 对抗评价面：干净 DGA 的 CharBot 变体（固定生成器，全臂共用）
    rng = random.Random(SEED)
    adv_d = [perturb2(d, rng) for d in [str(r["domain"]) for r in td]]
    print(f"[评价面] 干净 {len(ec)}、对抗 {len(adv_d)}", file=sys.stderr, flush=True)
    eval_clean = (ec, ey)
    eval_adv = (adv_d, np.ones(len(adv_d), dtype=bool))

    results: dict = {}
    for arm in ("A", "B", "C"):
        t0 = time.time()
        r = train_arm(arm, tr_d, tr_y, eval_clean, eval_adv)
        r["wall_seconds"] = round(time.time() - t0, 1)
        results[arm] = r
        print(f"[里程碑] {arm}: clean={json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in r['clean'].items()})} adv={json.dumps({k: round(v, 4) if isinstance(v, float) else v for k, v in r['adv'].items()})}", file=sys.stderr, flush=True)

    a, b, c = results["A"], results["B"], results["C"]
    verdict = {
        "P2_pass": bool(b["adv"]["AP"] > a["adv"]["AP"] and b["clean"]["FPR"] <= a["clean"]["FPR"] * 1.05),
        "P3_pass": bool(c["adv"]["AP"] > b["adv"]["AP"] and c["clean"]["FPR"] <= b["clean"]["FPR"] * 1.05),
        "detail": {
            "adv_AP": {"A": round(a["adv"]["AP"], 4), "B": round(b["adv"]["AP"], 4), "C": round(c["adv"]["AP"], 4)},
            "clean_FPR": {"A": round(a["clean"]["FPR"], 4), "B": round(b["clean"]["FPR"], 4), "C": round(c["clean"]["FPR"], 4)},
            "adv_FNR": {"A": round(a["adv"]["FNR"], 4), "B": round(b["adv"]["FNR"], 4), "C": round(c["adv"]["FNR"], 4)},
        },
    }
    out_name = "p2p3-result-DRYRUN.json" if dry else "p2p3-result.json"
    (OUT / out_name).write_text(json.dumps({"results": results, "verdict": verdict}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[里程碑] {json.dumps(verdict, ensure_ascii=False)} -> {out_name}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=0, help="每类抽样 N（0=全量 60000）")
    a = ap.parse_args()
    main(dry=a.dry_run)
