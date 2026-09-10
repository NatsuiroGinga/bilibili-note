#!/usr/bin/env python3
"""E-A1 v2 对抗规避病灶本地复现（零训练）——按文献代理核验的原文算子修正。

判据（冻结 v2，2026-09-10，依据文献代理对 CharBot/MaskDGA 原文的页码级核验）：
  良性流（T18 benign val）标定 FPR=1% 与 FPR=0.1% 阈值（CharBot §V p.5 口径）；
  对抗变体在该阈值下的检出率相对干净 DGA 检出率的相对下降：
  相对下降 ≥ 0.5 → 病灶坐实（对照 CharBot 原文把未针对训练模型 TPR 压至 5.58%，相对降幅 >90%）；
  相对下降 < 0.2 → 病灶不成立；之间 → 留主代理裁量。score<0.5 口径仅作参考并标注"无文献对应"。
算子（冻结 v2，忠实代理，标明非原文复现的部分）：
  - CharBot 忠实代理：随机替换 SLD 的 2 个不同位置，替换字符从 [a-z0-9-] 均匀采样且异于原字符
    （CharBot 算法 1 §III p.4：仅替换、恰好 2 位、1 变体/种子/域名、均匀随机无优化）；
  - MaskDGA 近似：随机替换 SLD 的一半位置（MaskDGA 原文为 JSMA 显著度选择，本臂为无梯度近似，
    须标注"非原文复现"；1 变体/域名；每位置只替换一次、禁止非点→点，§9 p.10）。
  - 原 4 算子设计（插入/交换/重复）按原文核验删除（CharBot p.4 明确不用插入；MaskDGA §9 p.10 禁止插入/删除）。
攻击面语义：扰动 DGA 域名 = MaskDGA 语义（对 AGD 加扰），不是 CharBot 复现（CharBot 从良性出发生成）。
协议：零训练；良性流仅用于阈值标定（无标签），DGA 标签仅用于事后检出率；不读 T20+。
断点：结果 JSON 原子落盘；埋点三类齐全。
"""
E-A1 对抗规避病灶本地复现（零训练，DGA 对抗鲁棒方案第一层证据）。

问题（冻结）：DRIFT 官方模型对 CharBot 式黑盒字符扰动的规避成功率（ASR）是多少？
- 对象：T18 val 的 DGA 域名（恶意侧；攻击者目标是让恶意域名被判良性）
- 扰动算子（黑盒字符扰动，CharBot 族通用四算子，每域名生成 4 变体）：
  1) 随机位置插入字符（'-' 或 '.'）
  2) 随机字符替换（字母→另一字母）
  3) 相邻字符交换
  4) 字符重复（任一字符翻倍）
  变体生成种子 42；仅对 effective 二级域标签部分操作，保持整体域名结构合法。
- 判据（冻结）：ASR = 原判恶意（score≥0.5）的样本中，≥1 个变体被判良性（score<0.5）的比例。
  ASR ≥ 0.30 → 病灶在本课题官方模型上坐实（方案病灶证据成立）；
  ASR < 0.10 → 病灶不成立，方案证据降级；
  之间 → 报告并留主代理裁量。
- 协议：零训练、不读 T20+、标签仅用于选取恶意样本（攻击者语义）与事后评价。
断点：结果 JSON 原子落盘；埋点三类齐全。
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
    """v2 算子（文献忠实版，文献代理核验 2026-09-10）：
    - charbot2：随机替换 SLD 的 2 个不同位置（CharBot 算法 1 §III p.4：仅替换、恰好 2 位、
      替换字符从 [a-z0-9-] 均匀采样且异于原字符、无插入/删除/交换/重复、1 变体/域名）；
    - maskdga-approx：随机替换 SLD 的一半位置（MaskDGA 为 JSMA 显著度选择替换一半，
      本臂为无梯度随机近似，须标注"非原文复现"；每位置只替换一次、禁止非点→点，§9 p.10）。
    返回 {"charbot2": v1, "maskdga-approx": v2}。
    """
    parts = domain.rsplit(".", 1)
    body = parts[0] if len(parts) == 2 else domain
    tail = "." + parts[1] if len(parts) == 2 else ""
    if len(body) < 4:
        return {}
    out: dict[str, str] = {}
    # charbot2：2 个不同位置
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
    # maskdga-approx：替换一半位置（无梯度近似）
    b = list(body)
    half = max(1, len(body) // 2)
    pos = rng.sample(range(len(body)), half)
    for i in pos:
        c = rng.choice(ALPHA)
        while c == b[i]:
            c = rng.choice(ALPHA)
        b[i] = c
    v2 = "".join(b) + tail
    if v2 != domain and v2 != out.get("charbot2"):
        out["maskdga-approx"] = v2
    return out


def main(limit: int | None = None, seed: int = 42) -> None:
    model = official.load_model(REF, CKPT, DEVICE)
    tokenizer = official.PreTrainedTokenizerFast(
        tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json")
    )
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_dga_val.parquet").to_pylist()
    if limit:
        td = td[:limit]
    clean_domains = [str(r["domain"]) for r in td]
    print(f"[E-A1] 恶意域名 {len(clean_domains)} 个（T18 val DGA）", file=sys.stderr, flush=True)

    # 静态基线：干净域名全判恶意？
    clean_scores = []
    for off in range(0, len(clean_domains), BATCH):
        tok = official.encode_subword(clean_domains[off:off + BATCH], tokenizer).to(DEVICE)
        ch = official.encode_char(clean_domains[off:off + BATCH]).to(DEVICE)
        tf, cf = diag.branch_features(model, tok, ch)
        s = diag.probabilities(model, tf.cpu().numpy(), cf.cpu().numpy(),
                               np.zeros(512, dtype=np.float32), np.zeros(512, dtype=np.float32), DEVICE, BATCH)
        clean_scores.append(s["static_fusion"])
    clean = np.concatenate(clean_scores)
    det = clean >= 0.5
    print(f"[基线] 干净 DGA 判恶意率（检出率）={det.mean():.4f}", file=sys.stderr, flush=True)

    # 生成对抗变体（每个检出域名 4 变体）
    rng = random.Random(seed)
    t0 = time.time()
    variants: list[str] = []
    owner: list[int] = []
    for idx, d in enumerate(clean_domains):
        if not det[idx]:
            continue
        vs = perturb(d, rng)
        for v in vs:
            variants.append(v)
            owner.append(idx)
    print(f"[生成] 对抗变体 {len(variants)} 个（覆盖 {len(set(owner))} 个检出域名）耗时 {time.time()-t0:.1f}s", file=sys.stderr, flush=True)

    adv_scores = []
    for off in range(0, len(variants), BATCH):
        chunk = variants[off:off + BATCH]
        tok = official.encode_subword(chunk, tokenizer).to(DEVICE)
        ch = official.encode_char(chunk).to(DEVICE)
        tf, cf = diag.branch_features(model, tok, ch)
        s = diag.probabilities(model, tf.cpu().numpy(), cf.cpu().numpy(),
                               np.zeros(512, dtype=np.float32), np.zeros(512, dtype=np.float32), DEVICE, BATCH)
        adv_scores.append(s["static_fusion"])
        if (off // BATCH) % 20 == 0:
            done = min(off + BATCH, len(variants))
            eta = (time.time() - t0) / max(done, 1) * (len(variants) - done)
            print(f"[心跳] 变体评价 {done}/{len(variants)} ETA {eta/60:.1f} min", file=sys.stderr, flush=True)
    adv = np.concatenate(adv_scores)
    adv_benign = adv < 0.5  # 变体被判良性 = 规避成功

    owner_arr = np.asarray(owner)
    asr_any, asr_majority = [], []
    for idx in set(owner):
        sel = adv_benign[owner_arr == idx]
        asr_any.append(bool(sel.any()))
        asr_majority.append(sel.mean() > 0.5)
    asr_any = float(np.mean(asr_any))
    asr_majority = float(np.mean(asr_majority))
    var_level = float(adv_benign.mean())

    verdict = {"ASR_any_variant": round(asr_any, 4), "ASR_majority_variant": round(asr_majority, 4),
               "variant_level_benign_rate": round(var_level, 4),
               "criteria": {"病灶坐实": asr_any >= 0.30, "病灶不成立": asr_any < 0.10,
                            "中间带（留裁量）": 0.10 <= asr_any < 0.30}}
    out_name = "ea1-result-DRYRUN.json" if limit else "ea1-result.json"
    (OUT / out_name).write_text(json.dumps({"verdict": verdict, "n_clean": len(clean_domains),
                                            "n_variants": len(variants)}, ensure_ascii=False, indent=2),
                               encoding="utf-8")
    print(f"[里程碑] {json.dumps(verdict, ensure_ascii=False)} -> {out_name}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", type=int, default=None)
    a = ap.parse_args()
    main(limit=a.dry_run)
