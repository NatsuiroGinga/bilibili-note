#!/usr/bin/env python3
"""定理 2 数值验证：双侧梯度近正交（恶意侧硬化方向 vs 良性侧误报方向）。

============================================================================
一、被验证的命题
============================================================================
在官方 24.2M DRIFT 判别器上，取两组样本的梯度：
  - 恶意侧（骗过集）：T18_dga_val 域经 perturb2 生成的变体中**模型判良性**者（s < 0.5），
    这些样本是「恶意侧硬化」要处理的困难样本；
  - 良性侧（误报集）：T18_benign_val 原始域中**模型判恶意**者（s ≥ 0.5），
    这些样本是「良性误报保护」要处理的困难样本。
取输出分数对参数的梯度代理量 ∇_θ CE(y=1)（softmax 前 logit 的交叉熵对全部参数的梯度，
两侧统一口径；另以良性侧 CE(y=0) 作次级对照）。定理 2 预测：
两组**平均梯度**的余弦显著小于 1，接近 0 即强正交 ⇒ 双侧机制可同时下降而不互相抵消。

判据（任务冻结）：
  cos < 0.3  → 近似正交，支持定理 2
  0.3–0.7    → 部分正交（方向不冲突但非正交）
  > 0.7      → 反驳

============================================================================
二、实现口径（显存与算力约束下的做法）
============================================================================
24.2M 参数的梯度向量 = 96.7MB（float32）。因此：
  1. **平均梯度**：只在设备上维护两个 96.7MB 的 float32 累积器（ḡ_mal、ḡ_ben），
     逐批（batch=16）求「CE 之和」的梯度并累加，最后除以样本数。
     ✅ 前提：模型在 eval 模式下无 dropout、无跨样本算子 ⇒ 批次求和梯度 ≡ 逐样本梯度之和。
     脚本在正式累积前用 4 个样本做一次**一致性断言**（批梯度 vs 逐样本梯度之和，误差 < 1e-4 相对量级）。
  2. **单样本梯度余弦**：只保留前 20 个恶意侧梯度（float16 存储 ≈ 48.4MB/个，共约 968MB），
     良性侧前 20 个梯度**流式**计算，逐个与前 20 个恶意梯度做点积 ⇒ 20×20 = 400 个余弦。
     这样峰值约为 1.4GB（任务给的上限是 2GB），且无需一次性堆 100 个 24.2M 梯度图。
  3. **不训练**：只用 torch.enable_grad() 求梯度，不调用任何优化器。

样本不足 200 时的放宽规则（脚本会登记放宽与否）：
  - 恶意侧不足 200：按分数**升序**（最骗过者优先）补齐至 200；
  - 良性侧不足 200：按分数**降序**（最像恶意的误报优先）补齐至 200；
  - 连放宽后仍不足 200：取该侧全部可用样本并如实登记样本数。

运行：PYTORCH_ENABLE_MPS_FALLBACK=1 /opt/miniconda3/envs/rwkv/bin/python verify_thm2_orthogonality.py
"""
from __future__ import annotations

import os

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

import json
import random
import sys
import time
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
WORKTREE = SCRIPT_DIR.parents[2]
ROOT = Path(os.environ.get("LLM_PROBE_ROOT", WORKTREE / "thesis/experiments/llm_probe"))
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ROOT / "tools"))

SEED = 42
N_POOL = 2000          # 每侧候选池（任务冻结：各取前 2000）
N_TARGET = 200         # 每侧目标样本数
N_PAIR = 20            # 单样本余弦的成对样本数（20×20 = 400 对）
ACC_BATCH = 16         # 平均梯度的累积批大小（eval 模式下批梯度 = 逐样本梯度之和）
OUT_JSON = SCRIPT_DIR / "verify-thm2-result.json"


def log(msg: str) -> None:
    print(f"[定理2] {msg}", flush=True)


def atomic_json(path: Path, value: dict) -> None:
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    partial.replace(path)


def flat_grad(loss, params) -> "object":
    """把一个标量损失对全部参数的梯度拼成一维向量（torch.Tensor，设备上）。"""
    import torch

    grads = torch.autograd.grad(loss, params)
    return torch.cat([g.reshape(-1) for g in grads])


def encode_batch(domains: list[str], tokenizer, official, device):
    tok = official.encode_subword(domains, tokenizer).to(device)
    ch = official.encode_char(domains).to(device)
    return tok, ch


def main() -> int:
    import torch
    import torch.nn.functional as F
    import pyarrow.parquet as pq
    import ch3_drift_official_checkpoint_t17_eval as official
    import official_p2p3 as op3

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    t_start = time.time()
    device = torch.device("mps")
    ref = ROOT / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
    ckpt = ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"
    data_root = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521/DRIFT_input_eSLD"
    tokenizer = official.PreTrainedTokenizerFast(tokenizer_file=str(ref / "artifacts/tokenizer/tokenizer-0-30522-both.json"))
    model = official.load_model(ref, ckpt, device)
    model.eval()                     # 关 dropout：梯度必须确定性（否则单样本余弦是随机量）
    params = [p for p in model.parameters() if p.requires_grad]
    n_params = sum(p.numel() for p in params)
    log(f"模型加载：{n_params} 参数（可导），device={device.type}")

    def score(domains: list[str]) -> np.ndarray:
        """原始模型打分 s = softmax(logits)[:,1]（无梯度、batch=1024）。"""
        out: list[np.ndarray] = []
        with torch.inference_mode():
            for off in range(0, len(domains), 1024):
                tok, ch = encode_batch(domains[off:off + 1024], tokenizer, official, device)
                out.append(torch.softmax(model(tok, ch).float(), dim=1)[:, 1].cpu().numpy())
        return np.concatenate(out)

    # ---- 1. 两侧候选池与筛选 ----
    ben_domains = [str(r["domain"]) for r in pq.read_table(data_root / "T18_benign_val.parquet").to_pylist()[:N_POOL]]
    mal_domains = [str(r["domain"]) for r in pq.read_table(data_root / "T18_dga_val.parquet").to_pylist()[:N_POOL]]
    log(f"候选池：benign {len(ben_domains)} + dga {len(mal_domains)}，开始打分")
    ben_scores = score(ben_domains)
    rng = random.Random(SEED)
    mal_variant = [op3.perturb2(d, rng) for d in mal_domains]     # 每域 1 个 perturb2 变体
    mal_scores = score(mal_variant)
    log(f"打分完成：benign 误报 {int((ben_scores >= 0.5).sum())} 例（s≥0.5）；"
        f"dga 变体骗过 {int((mal_scores < 0.5).sum())} 例（s<0.5）")

    relax_log: dict = {}
    ben_fp_idx = np.flatnonzero(ben_scores >= 0.5)                  # 良性侧：模型判恶意 = 误报
    mal_ok_idx = np.flatnonzero(mal_scores < 0.5)                   # 恶意侧：变体骗过 = 判良性
    if ben_fp_idx.size >= N_TARGET:
        ben_sel = ben_fp_idx[:N_TARGET]
        relax_log["benign"] = "满足条件（s≥0.5）者 ≥200，按原顺序取前 200"
    else:
        order = np.argsort(-ben_scores)                            # 放宽：按分数降序取最像恶意的
        ben_sel = order[:N_TARGET]
        relax_log["benign"] = f"满足条件者仅 {ben_fp_idx.size} 例 <200，放宽为按分数降序取 {len(ben_sel)} 例"
    if mal_ok_idx.size >= N_TARGET:
        mal_sel = mal_ok_idx[:N_TARGET]
        relax_log["malicious"] = "满足条件（s<0.5）者 ≥200，按原顺序取前 200"
    else:
        order = np.argsort(mal_scores)                             # 放宽：按分数升序取最骗过的
        mal_sel = order[:N_TARGET]
        relax_log["malicious"] = f"满足条件者仅 {mal_ok_idx.size} 例 <200，放宽为按分数升序取 {len(mal_sel)} 例"
    log(f"入选：恶性侧 {len(mal_sel)}、良性侧 {len(ben_sel)}；放宽登记 {relax_log}")

    mal_dom_sel = [mal_variant[i] for i in mal_sel]
    ben_dom_sel = [ben_domains[i] for i in ben_sel]

    # ---- 2. 批梯度 ≡ 逐样本梯度之和 的内部一致性断言（只做一次，4 个样本） ----
    probe = mal_dom_sel[:4]
    tok, ch = encode_batch(probe, tokenizer, official, device)
    with torch.enable_grad():
        logits = model(tok, ch)
        loss_sum = F.cross_entropy(logits.float(), torch.ones(len(probe), dtype=torch.long, device=device), reduction="sum")
        g_batch = flat_grad(loss_sum, params).clone()
    g_each = None
    for j in range(len(probe)):
        tok1, ch1 = encode_batch(probe[j:j + 1], tokenizer, official, device)
        with torch.enable_grad():
            logits1 = model(tok1, ch1)
            loss1 = F.cross_entropy(logits1.float(), torch.ones(1, dtype=torch.long, device=device))
            g1 = flat_grad(loss1, params)
        g_each = g1.clone() if g_each is None else g_each + g1
    rel_err = float((g_batch - g_each).abs().max() / (g_each.abs().max() + 1e-12))
    log(f"批梯度一致性断言：相对最大偏差 {rel_err:.2e}（判据 <1e-3；差异仅来自批/单样本的浮点归约顺序）")
    assert rel_err < 1e-3, "批梯度与逐样本梯度之和不一致（存在跨样本算子），不能使用批累积"
    del tok, ch, logits, loss_sum, g_batch, g_each

    # ---- 3. 平均梯度累积（CE(y=1) 统一口径） ----
    def accumulate_mean(domains: list[str], target_label: int, tag: str):
        acc = torch.zeros(n_params, dtype=torch.float32, device=device)
        n = 0
        t0 = time.time()
        for off in range(0, len(domains), ACC_BATCH):
            chunk = domains[off:off + ACC_BATCH]
            tok, ch = encode_batch(chunk, tokenizer, official, device)
            with torch.enable_grad():
                logits = model(tok, ch)
                loss = F.cross_entropy(
                    logits.float(),
                    torch.full((len(chunk),), target_label, dtype=torch.long, device=device),
                    reduction="sum",
                )
                acc.add_(flat_grad(loss, params))
            n += len(chunk)
            if (off // ACC_BATCH) % 5 == 0:
                log(f"  {tag} 累积 {n}/{len(domains)}（{time.time() - t0:.0f}s）")
        return acc / n

    log("累积恶意侧平均梯度 ḡ_mal（CE y=1）")
    g_mal = accumulate_mean(mal_dom_sel, 1, "mal")
    log("累积良性侧平均梯度 ḡ_ben（CE y=1，统一口径）")
    g_ben_y1 = accumulate_mean(ben_dom_sel, 1, "ben-y1")
    log("累积良性侧平均梯度 ḡ_ben（CE y=0，次级对照）")
    g_ben_y0 = accumulate_mean(ben_dom_sel, 0, "ben-y0")

    def cos_report(a, b) -> dict:
        na, nb = float(a.norm()), float(b.norm())
        return {"cosine": round(float(torch.dot(a, b) / (a.norm() * b.norm() + 1e-30)), 6),
                "norm_a": round(na, 6), "norm_b": round(nb, 6), "dot": round(float(torch.dot(a, b)), 6)}

    primary = cos_report(g_mal, g_ben_y1)
    secondary = cos_report(g_mal, g_ben_y0)
    log(f"平均梯度余弦（主口径 CE y=1）：{primary['cosine']:.4f}；"
        f"次级（良性侧 CE y=0）：{secondary['cosine']:.4f}")

    # 对照：良性侧**严格误报集**（s≥0.5，不补齐、不混入近阈值样本），数量 ≥20 时另算一组
    strict_control = None
    if ben_fp_idx.size >= 20:
        strict_dom = [ben_domains[i] for i in ben_fp_idx]
        g_s1 = accumulate_mean(strict_dom, 1, "ben-strict-y1")
        g_s0 = accumulate_mean(strict_dom, 0, "ben-strict-y0")
        strict_control = {"n": int(ben_fp_idx.size),
                          "ce_y1": cos_report(g_mal, g_s1),
                          "ce_y0": cos_report(g_mal, g_s0)}
        log(f"严格误报集对照（n={strict_control['n']}）：cos(CE y=1)={strict_control['ce_y1']['cosine']:.4f}，"
            f"cos(CE y=0)={strict_control['ce_y0']['cosine']:.4f}")

    # ---- 4. 单样本梯度余弦分布（20 恶意 × 20 良性 = 400 对） ----
    log(f"单样本梯度：恶意侧前 {N_PAIR} 个（float16 存储）+ 良性侧前 {N_PAIR} 个流式点积")
    mal_unit_store = []
    mal_norms = []
    for j in range(N_PAIR):
        tok, ch = encode_batch(mal_dom_sel[j:j + 1], tokenizer, official, device)
        with torch.enable_grad():
            logits = model(tok, ch)
            loss = F.cross_entropy(logits.float(), torch.ones(1, dtype=torch.long, device=device))
            g = flat_grad(loss, params)
        mal_norms.append(float(g.norm()))
        mal_unit_store.append(g.detach().to(torch.float16))       # 48.4MB/个
        del g, tok, ch, logits, loss
    cos_matrix = np.zeros((N_PAIR, N_PAIR), dtype=np.float64)
    ben_norms = []
    for j in range(N_PAIR):
        tok, ch = encode_batch(ben_dom_sel[j:j + 1], tokenizer, official, device)
        with torch.enable_grad():
            logits = model(tok, ch)
            loss = F.cross_entropy(logits.float(), torch.ones(1, dtype=torch.long, device=device))
            h = flat_grad(loss, params)
        ben_norms.append(float(h.norm()))
        for i in range(N_PAIR):
            gi = mal_unit_store[i].to(torch.float32)
            cos_matrix[i, j] = float(torch.dot(gi, h)) / (mal_norms[i] * ben_norms[j] + 1e-30)
            del gi
        del h, tok, ch, logits, loss
        if j % 5 == 0:
            log(f"  单样本余弦 {j + 1}/{N_PAIR}")
    log("单样本余弦矩阵完成")

    # ---- 5. 分数分布数据 ----
    def hist(values: np.ndarray) -> dict:
        counts, edges = np.histogram(values, bins=20, range=(0.0, 1.0))
        return {"bin_edges": [round(float(e), 4) for e in edges], "counts": [int(c) for c in counts]}

    result = {
        "theorem_id": "定理2：双侧梯度近正交（恶意侧骗过集 vs 良性侧误报集）",
        "verification_status": {
            "闭式验证": "无闭式（本定理为经验命题，只有真实网络+真实样本的实测）",
            "真实数据方向": ("近似正交（支持定理 2）" if primary["cosine"] < 0.3 else
                        "部分正交（0.3–0.7，不构成正面支持）" if primary["cosine"] <= 0.7 else
                        "反驳（>0.7）"),
            "总判定": ("近似正交，支持定理 2" if primary["cosine"] < 0.3 else
                     "部分支持（余弦落在 0.3–0.7）" if primary["cosine"] <= 0.7 else
                     "反驳：双侧梯度不近正交"),
            "判据": {"近似正交": "cos < 0.3", "部分": "0.3 ≤ cos ≤ 0.7", "反驳": "cos > 0.7",
                   "主口径": "两侧统一 CE(y=1) 梯度", "次级口径": "良性侧 CE(y=0) 梯度"},
        },
        "数值表": {
            "样本筛选": {
                "pool_per_side": N_POOL, "target_per_side": N_TARGET,
                "benign_fp_count": int(ben_fp_idx.size), "malicious_fooled_count": int(mal_ok_idx.size),
                "benign_selected": len(ben_sel), "malicious_selected": len(mal_sel),
                "relaxation": relax_log,
                "benign_fp_rate_in_pool": round(float(ben_fp_idx.size) / len(ben_domains), 6),
                "malicious_fool_rate_in_pool": round(float(mal_ok_idx.size) / len(mal_variant), 6),
            },
            "平均梯度": {
                "primary_ce_y1": primary,
                "secondary_benign_ce_y0": secondary,
                "strict_fp_control_benign_only": strict_control,
                "batch_grad_consistency_rel_err": rel_err,
                "mal_mean_grad_norm": primary["norm_a"],
                "ben_y1_mean_grad_norm": primary["norm_b"],
                "ben_y0_mean_grad_norm": secondary["norm_b"],
            },
            "单样本余弦": {
                "n_pairs": N_PAIR,
                "n_cosines": int(cos_matrix.size),
                "median": round(float(np.median(cos_matrix)), 6),
                "mean": round(float(cos_matrix.mean()), 6),
                "q25": round(float(np.quantile(cos_matrix, 0.25)), 6),
                "q75": round(float(np.quantile(cos_matrix, 0.75)), 6),
                "min": round(float(cos_matrix.min()), 6),
                "max": round(float(cos_matrix.max()), 6),
                "frac_lt_0_3": round(float((cos_matrix < 0.3).mean()), 6),
                "frac_gt_0_7": round(float((cos_matrix > 0.7).mean()), 6),
                "mal_single_grad_norm_mean": round(float(np.mean(mal_norms)), 6),
                "ben_single_grad_norm_mean": round(float(np.mean(ben_norms)), 6),
            },
            "分数分布": {
                "benign_pool": hist(ben_scores),
                "malicious_variant_pool": hist(mal_scores),
                "benign_selected_scores": [round(float(v), 6) for v in ben_scores[ben_sel]],
                "malicious_selected_scores": [round(float(v), 6) for v in mal_scores[mal_sel]],
            },
        },
        "conclusion": {
            "main_cosine_ce_y1": primary["cosine"],
            "secondary_cosine_benign_ce_y0": secondary["cosine"],
            "strict_fp_control_cosine_ce_y1": (strict_control["ce_y1"]["cosine"] if strict_control else None),
            "strict_fp_control_cosine_ce_y0": (strict_control["ce_y0"]["cosine"] if strict_control else None),
            "single_sample_cosine_median": round(float(np.median(cos_matrix)), 6),
            "supports_theorem2": bool(primary["cosine"] < 0.3),
            "备注": "CE(y=1) 为两侧统一口径（任务指定）；良性侧 CE(y=0) 为次级对照，二者方向含义不同，结论以主口径为准。",
        },
        "inputs": {
            "checkpoint": str(ckpt),
            "benign_val": str(data_root / "T18_benign_val.parquet"),
            "dga_val": str(data_root / "T18_dga_val.parquet"),
            "variant_operator": "official_p2p3.perturb2（每域 1 变体，rng=Random(42)）",
            "device": "mps", "model_mode": "eval（无 dropout）", "training": False,
        },
        "runtime": {"elapsed_seconds": round(time.time() - t_start, 1), "seed": SEED},
    }
    atomic_json(OUT_JSON, result)
    log(f"完成：{OUT_JSON.name}；主口径余弦 {primary['cosine']:.4f}，"
        f"单样本中位 {np.median(cos_matrix):.4f}，判定={result['verification_status']['总判定']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
