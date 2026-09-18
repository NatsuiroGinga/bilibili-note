#!/usr/bin/env python3
"""DRIFT 正锚点核查（零训练探针，恢复卡唯一下一动作）。

问题（跑前冻结）：分支分歧特征能否预测"哪支在该样本上更可靠"？
- 反事实语义（复刻 ch3_drift_official_branch_conflict_diagnostic.py）：
  以源侧类无关均值中和单支 → 反事实分支概率。
  正锚点目标 = 在融合错误样本上，subword 反事实支是否比 char 反事实支更可靠。
- gate 特征（全部源侧可观测）：两反事实支概率、|概率差|、融合概率、
  域长、数字占比、连字符数、唯一字符数、字符熵。
- 判据（冻结）：LR 选择器预测"subword 支更可靠" AUC >= 0.60 且 T17→T18 方向
  一致 → 正锚点成立；两年 AUC < 0.60 → 关闭选择/路由族（N14 撤销）。
- 运行：MPS 前向官方 24.2M 参数模型，T17/T18 val 全量（各 30 万域），无标签泄漏。
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch

ROOT = Path("/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe")
sys.path.insert(0, str(ROOT / "tools"))
import ch3_drift_official_branch_conflict_diagnostic as _diag

branch_features = _diag.branch_features  # 原工具实现，属性名与 mask 语义以它为准
REF = ROOT / "runs/source-snapshots" / "2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
CKPT = ROOT / "runs/models" / "drift-official-dsn2026" / "finetuning.pt"
DATA = ROOT / "runs/data-raw" / "drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521"
OUT = Path(__file__).resolve().parent
BATCH = 4096
DEVICE = torch.device("mps")


def string_stats(domains: list[str]) -> np.ndarray:
    feats = []
    for d in domains:
        s = d.lower()
        n = max(len(s), 1)
        digits = sum(c.isdigit() for c in s) / n
        hyphens = s.count("-") / n
        uniq = len(set(s)) / n
        freq: dict[str, int] = {}
        for c in s:
            freq[c] = freq.get(c, 0) + 1
        ent = -sum((v / n) * math.log2(v / n) for v in freq.values())
        feats.append([len(s), digits, hyphens, uniq, ent])
    return np.asarray(feats, dtype=np.float32)


def main(limit: int | None = None) -> None:
    import ch3_drift_official_checkpoint_t17_eval as official

    model = official.load_model(REF, CKPT, DEVICE)
    tokenizer = official.PreTrainedTokenizerFast(
        tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json")
    )
    print("模型加载完成", file=sys.stderr)

    # 源侧类无关均值 + T17 特征缓存：一次前向两用（均值=特征均值，逐样本=缓存特征过分类头）
    t17b = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_benign_val.parquet").to_pylist()
    t17d = pq.read_table(DATA / "DRIFT_input_eSLD" / "T17_dga_val.parquet").to_pylist()
    if limit:
        t17b, t17d = t17b[:limit], t17d[:limit]
        print(f"[DRY-RUN] 每类截取前 {limit} 行", file=sys.stderr)
    neutral_domains = [str(r["domain"]) for r in t17b] + [str(r["domain"]) for r in t17d]
    print(f"T17 特征提取开始（{len(neutral_domains)} 域，缓存复用）", file=sys.stderr)
    import ch3_drift_official_branch_conflict_diagnostic as diag
    cache = Path(f"/tmp/drift-anchor-t17-features-{len(neutral_domains)}.npz")
    if cache.is_file():
        saved = np.load(cache)
        tok_feat, char_feat = saved["tok"], saved["char"]
        print(f"断点恢复：从 {cache} 加载特征缓存", file=sys.stderr)
    else:
        tok_feat, char_feat = diag.extract_features(model, tokenizer, neutral_domains, DEVICE, BATCH)
        np.savez(cache, tok=tok_feat, char=char_feat)
        print(f"特征缓存已落盘：{cache}", file=sys.stderr)
    tok_mean = tok_feat.mean(axis=0, dtype=np.float64).astype(np.float32)
    char_mean = char_feat.mean(axis=0, dtype=np.float64).astype(np.float32)
    print("均值与 T17 特征缓存完成", file=sys.stderr)
    t17_probs = diag.probabilities(model, tok_feat, char_feat, tok_mean, char_mean, DEVICE, BATCH)
    del tok_feat, char_feat

    results: dict = {}
    per_year: dict[str, dict] = {}
    for year, rows, cached in (("T17", t17b + t17d, t17_probs), ("T18", None, None)):
        if rows is None:
            tb = pq.read_table(DATA / "DRIFT_input_eSLD" / f"{year}_benign_val.parquet").to_pylist()
            td = pq.read_table(DATA / "DRIFT_input_eSLD" / f"{year}_dga_val.parquet").to_pylist()
            if limit:
                tb, td = tb[:limit], td[:limit]
            rows = tb + td
        domains = [str(r["domain"]) for r in rows]
        labels = np.asarray([int(r["label"]) for r in rows], dtype=np.int64)
        probs = cached if cached is not None else forward_all_chunked(model, tokenizer, domains, tok_mean, char_mean)
        if "stats" not in probs:
            probs["stats"] = string_stats(domains)
        print(f"[里程碑] {year}: 三路判定与特征完成（n={len(domains)}）", file=sys.stderr, flush=True)
        fusion = probs["static_fusion"]
        pred = fusion >= 0.5
        wrong = pred != (labels == 1)
        rec_char = probs["char_counterfactual"] >= 0.5
        rec_sub = probs["subword_counterfactual"] >= 0.5
        n_err = int(wrong.sum())
        # 目标变量：在融合错误样本上，subword 反事实支更可靠（挽回）而 char 支失败
        target = wrong & rec_sub & ~rec_char  # subword 挽回、char 没挽回
        neg = wrong & rec_char & ~rec_sub  # char 挽回、subword 没挽回
        gate = gate_features(domains, probs)
        # —— 两问式正锚点（对齐深度研究报告设计，零梯度 lookup 优先）——
        pred_c = probs["char_counterfactual"] >= 0.5
        pred_s = probs["subword_counterfactual"] >= 0.5
        labels01 = labels == 1
        # exclusive-correct 子集：恰有一个反事实支正确
        exc_c = (pred_c == labels01) & (pred_s != labels01)  # char 支对
        exc_s = (pred_s == labels01) & (pred_c != labels01)  # subword 支对
        # 键 K1：三路判定模式；K2：融合-支路置信差符号；K3：|p_c-p_s| 分位箱（源年分位）
        conf_c = np.abs(probs["char_counterfactual"] - 0.5)
        conf_s = np.abs(probs["subword_counterfactual"] - 0.5)
        k1 = (pred.astype(int) * 4) + (pred_c.astype(int) * 2) + pred_s.astype(int)
        k2 = (conf_c > conf_s).astype(int)
        if year == "T17":
            edges = np.quantile(np.abs(probs["char_counterfactual"] - probs["subword_counterfactual"]), [0.25, 0.5, 0.75])
        k3 = np.digitize(np.abs(probs["char_counterfactual"] - probs["subword_counterfactual"]), edges)
        cell = (k1 * 8) + (k2 * 4) + k3
        per_year[year] = {
            "labels": labels01, "exc_c": exc_c, "exc_s": exc_s, "cell": cell,
            "wrong": wrong, "pred_c": pred_c, "pred_s": pred_s,
            "fusion_pred": pred, "conf_c": conf_c, "conf_s": conf_s,
            "n": len(domains), "fusion_errors": n_err,
            "target_n": int(target.sum()), "neg_n": int(neg.sum()),
            "gate": gate,
        }
        results[year] = {
            "n": len(domains),
            "fusion_errors": n_err,
            "fusion_error_rate": round(n_err / len(domains), 6),
            "subword_recovers": int((wrong & rec_sub).sum()),
            "char_recovers": int((wrong & rec_char).sum()),
            "either_recovers": int((wrong & (rec_sub | rec_char)).sum()),
            "both_recover": int((wrong & rec_sub & rec_char).sum()),
            "anchor_target_n": int(target.sum()),
            "anchor_neg_n": int(neg.sum()),
            "exclusive_correct_c": int(exc_c.sum()),
            "exclusive_correct_s": int(exc_s.sum()),
        }
        # LR 选择器补充（T17 训练 → T18 验证）
        if year == "T17":
            from sklearn.linear_model import LogisticRegression
            m = target | neg
            y_arr = np.r_[np.ones(target.sum()), np.zeros(neg.sum())]
            if len(np.unique(y_arr)) < 2:
                results[year]["selector_skipped"] = "单类样本不足（小样本干跑正常现象）"
                print("[WARN] LR 选择器跳过：目标单类", file=sys.stderr)
            else:
                sel = LogisticRegression(max_iter=500, C=1.0).fit(gate[m], y_arr)
                results[year]["selector_trained"] = True
        else:
            from sklearn.metrics import roc_auc_score
            m = target | neg
            if "selector_trained" in results.get("T17", {}):
                auc = roc_auc_score(np.r_[np.ones(target.sum()), np.zeros(neg.sum())], sel.decision_function(gate[m]))
                results[year]["anchor_auc_T17_to_T18"] = round(float(auc), 4)
            else:
                results[year]["anchor_auc_T17_to_T18"] = None
    # —— 两问式 lookup 判读（T17 表 → T18 验证）——
    if "T17" in per_year and "T18" in per_year:
        a, b = per_year["T17"], per_year["T18"]
        # 问一：which-branch。T17 的 exclusive-correct 样本按 cell 统计 char 偏好 → T18 同 cell 验证
        cells = np.unique(a["cell"][a["exc_c"] | a["exc_s"]])
        pref = {}
        for c in cells:
            m17 = a["cell"] == c
            nc, ns = int((m17 & a["exc_c"]).sum()), int((m17 & a["exc_s"]).sum())
            if nc + ns >= 30:
                pref[int(c)] = "c" if nc > ns else "s"
        hit = tot = 0
        for c, p in pref.items():
            m18 = b["cell"] == int(c)
            if p == "c":
                hit += int((m18 & b["exc_c"]).sum()); tot += int((m18 & (b["exc_c"] | b["exc_s"])).sum())
            else:
                hit += int((m18 & b["exc_s"]).sum()); tot += int((m18 & (b["exc_c"] | b["exc_s"])).sum())
        lookup_choice = {"cells_used": len(pref), "covered_n": int(tot), "correct_n": int(hit),
                          "balanced_accuracy_proxy": round(hit / tot, 4) if tot else None}
        # 负锚点对照：confidence 启发式（conf 大者赢）在同覆盖子集上的正确率
        hit_h = tot_h = 0
        for c in pref:
            m18 = b["cell"] == int(c)
            if not (m18 & (b["exc_c"] | b["exc_s"])).any():
                continue
            prefer_c = b["conf_c"][m18 & (b["exc_c"] | b["exc_s"])] >= b["conf_s"][m18 & (b["exc_c"] | b["exc_s"])]
            hit_h += int((prefer_c & b["exc_c"][m18 & (b["exc_c"] | b["exc_s"])]).sum()) + int(
                (~prefer_c & b["exc_s"][m18 & (b["exc_c"] | b["exc_s"])]).sum())
            tot_h += int((m18 & (b["exc_c"] | b["exc_s"])).sum())
        lookup_choice["confidence_heuristic_correct_rate"] = round(hit_h / tot_h, 4) if tot_h else None
        # 问二：override。T17 按 cell 学 argmax_u（rescue-harm 效用），T18 上执行，计 coverage/rescued/induced
        u17 = {}
        for c in cells:
            m17 = a["cell"] == c
            if m17.sum() < 50:
                continue
            # u_k = 挽回数 - 改错数（cell 内，T17）；挽回=融合错而支对，改错=融合对而支错
            r_c = int((m17 & a["wrong"] & (a["pred_c"] == a["labels"])).sum())
            i_c = int((m17 & ~a["wrong"] & (a["pred_c"] != a["fusion_pred"])).sum())
            r_s = int((m17 & a["wrong"] & (a["pred_s"] == a["labels"])).sum())
            i_s = int((m17 & ~a["wrong"] & (a["pred_s"] != a["fusion_pred"])).sum())
            u17[int(c)] = {"u_c": r_c - i_c, "u_s": r_s - i_s, "n": int(m17.sum())}
        # T18 执行 lookup：cell 最优效用支为正 → 覆盖采纳该支判定
        cov = resc = ind = 0
        labels18 = b["labels"]
        for c, u in u17.items():
            m18 = b["cell"] == int(c)
            if not m18.any():
                continue
            best = max(("u_c", "u_s"), key=lambda k: u[k])
            if u[best] <= 0:
                continue
            rec = b["pred_c"] if best == "u_c" else b["pred_s"]
            use = m18 & (rec != b["fusion_pred"])  # 支路判定与融合不同才实际覆盖
            cov += int(use.sum())
            resc += int((use & (rec == labels18)).sum())
            ind += int((use & (rec != labels18)).sum())
        lookup_override = {"coverage": int(cov), "rescued": int(resc), "induced": int(ind),
                           "net": int(resc - ind), "rescue_rate_in_covered": round(resc / cov, 4) if cov else None}
        results["lookup_two_question"] = {
            "question1_which_branch": lookup_choice,
            "question2_override": lookup_override,
            "criteria": {"q1_pass": bool(lookup_choice["balanced_accuracy_proxy"] and lookup_choice["balanced_accuracy_proxy"] > 0.5),
                         "q2_pass": bool(lookup_override["coverage"] > 0 and lookup_override["net"] > 0)},
        }
    out_name = "positive-anchor-result-DRYRUN.json" if limit else "positive-anchor-result.json"
    (OUT / out_name).write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"结果写入 {out_name}", file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False, indent=2))


def extract_means(model, tokenizer, domains):
    import ch3_drift_official_checkpoint_t17_eval as official

    parts_tok, parts_char = [], []
    with torch.inference_mode():
        for off in range(0, len(domains), BATCH):
            cur = domains[off : off + BATCH]
            tok_ids = official.encode_subword(cur, tokenizer).to(DEVICE)
            char_ids = official.encode_char(cur).to(DEVICE)
            tf, cf = branch_features(model, tok_ids, char_ids)
            parts_tok.append(tf.cpu().numpy())
            parts_char.append(cf.cpu().numpy())
    return np.concatenate(parts_tok).mean(axis=0), np.concatenate(parts_char).mean(axis=0)


def forward_all(model, tokenizer, domains, tok_mean, char_mean):
    import ch3_drift_official_branch_conflict_diagnostic as diag

    tok_feat, char_feat = diag.extract_features(model, tokenizer, domains, DEVICE, BATCH)
    probs = diag.probabilities(model, tok_feat, char_feat, tok_mean, char_mean, DEVICE, BATCH)
    probs["stats"] = string_stats(domains)
    return probs


def forward_all_chunked(model, tokenizer, domains, tok_mean, char_mean, n_chunks: int = 10):
    """分块前向并打心跳（每块完成打印进度与耗时），块间结果等价于整批。"""
    import time

    import ch3_drift_official_branch_conflict_diagnostic as diag

    size = (len(domains) + n_chunks - 1) // n_chunks
    tok_parts, char_parts = [], []
    t0 = time.time()
    for i in range(0, len(domains), size):
        chunk = domains[i : i + size]
        tf, cf = diag.extract_features(model, tokenizer, chunk, DEVICE, BATCH)
        tok_parts.append(tf)
        char_parts.append(cf)
        done = min(i + size, len(domains))
        rate = done / (time.time() - t0)
        eta = (len(domains) - done) / max(rate, 1)
        print(f"[心跳] 特征提取 {done}/{len(domains)}（{rate:.0f} 域/s，ETA {eta/60:.1f} min）", file=sys.stderr, flush=True)
    tok_feat = np.concatenate(tok_parts)
    char_feat = np.concatenate(char_parts)
    probs = diag.probabilities(model, tok_feat, char_feat, tok_mean, char_mean, DEVICE, BATCH)
    probs["stats"] = string_stats(domains)
    return probs


def gate_features(domains, probs):
    fusion = probs["static_fusion"]
    ccf = probs["char_counterfactual"]
    scf = probs["subword_counterfactual"]
    return np.column_stack(
        [
            ccf,
            scf,
            np.abs(ccf - scf),
            fusion,
            np.abs(fusion - ccf),
            np.abs(fusion - scf),
            probs["stats"],
        ]
    )


if __name__ == "__main__":
    import argparse as _ap

    _p = _ap.ArgumentParser()
    _p.add_argument("--dry-run", type=int, default=None, help="每类截取前 N 行干跑")
    _a = _p.parse_args()
    main(limit=_a.dry_run)
