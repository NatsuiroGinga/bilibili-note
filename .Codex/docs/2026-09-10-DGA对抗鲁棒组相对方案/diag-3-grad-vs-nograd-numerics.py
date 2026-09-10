#!/usr/bin/env python3
"""E-A1 修复安全性验证：带梯度前向 vs inference_mode 前向的数值一致性。
同时量化 MPS 位级非确定性（同模式两次前向），以区分两种差异来源。
"""
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch

ROOT = Path("/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe")
sys.path.insert(0, str(ROOT / "tools"))
import ch3_drift_official_branch_conflict_diagnostic as diag  # noqa: E402
import ch3_drift_official_checkpoint_t17_eval as official  # noqa: E402

REF = ROOT / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
CKPT = ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"
DATA = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521"
DEVICE = torch.device("mps")

model = official.load_model(REF, CKPT, DEVICE)
tokenizer = official.PreTrainedTokenizerFast(
    tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json"))
td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_dga_val.parquet").to_pylist()[:512]
domains = [str(r["domain"]) for r in td]
tk = official.encode_subword(domains, tokenizer).to(DEVICE)
ch = official.encode_char(domains).to(DEVICE)


def run(mode: str):
    if mode == "grad":
        tf, cf = diag.branch_features(model, tk, ch)
    else:
        with torch.inference_mode():
            tf, cf = diag.branch_features(model, tk, ch)
    return tf.detach().cpu().numpy(), cf.detach().cpu().numpy()


g1 = run("grad")
g2 = run("grad")
n1 = run("nograd")
n2 = run("nograd")


def report(tag, a, b):
    d = np.abs(a - b)
    print(f"{tag}: max|Δ|={d.max():.3e} mean|Δ|={d.mean():.3e} 非零元素={int((d > 0).sum())}/{d.size}", flush=True)


report("token_feature  grad#1 vs grad#2 ", g1[0], g2[0])
report("token_feature  grad#1 vs nograd#1", g1[0], n1[0])
report("token_feature  nograd#1 vs nograd#2", n1[0], n2[0])
report("char_feature   grad#1 vs grad#2 ", g1[1], g2[1])
report("char_feature   grad#1 vs nograd#1", g1[1], n1[1])
report("char_feature   nograd#1 vs nograd#2", n1[1], n2[1])

with torch.inference_mode():
    s_g = diag.probabilities(model, g1[0], g1[1], np.zeros(512, "float32"),
                             np.zeros(512, "float32"), DEVICE, 512)["static_fusion"]
    s_n = diag.probabilities(model, n1[0], n1[1], np.zeros(512, "float32"),
                             np.zeros(512, "float32"), DEVICE, 512)["static_fusion"]
print(f"static_fusion: grad vs nograd max|Δ|={np.abs(s_g - s_n).max():.3e} "
      f"跨 0.5 判定的翻转数={int(((s_g >= 0.5) != (s_n >= 0.5)).sum())}/{len(s_g)}", flush=True)
