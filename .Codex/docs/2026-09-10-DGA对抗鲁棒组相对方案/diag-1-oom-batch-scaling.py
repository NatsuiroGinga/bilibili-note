#!/usr/bin/env python3
"""E-A1 干跑 OOM 只读诊断：量化 MPS 内存随 batch 与前向模式的变化。
不修改实验脚本、不改判据；仅读取同一模型/同一数据。
"""
import sys
import time
from pathlib import Path

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


def gib(x: int) -> str:
    return f"{x / 2**30:.3f}"


model = official.load_model(REF, CKPT, DEVICE)
n_params = sum(p.numel() for p in model.parameters())
n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"[diag] 总参数 {n_params / 1e6:.2f}M，requires_grad {n_train / 1e6:.2f}M，"
      f"权重 fp32 ≈ {n_params * 4 / 2**30:.3f} GiB", flush=True)
print(f"[diag] 模型加载后 MPS current={gib(torch.mps.current_allocated_memory())} GiB "
      f"driver={gib(torch.mps.driver_allocated_memory())} GiB", flush=True)
print(f"[diag] recommended_max_working_set = {gib(torch.mps.recommended_max_memory())} GiB", flush=True)

tokenizer = official.PreTrainedTokenizerFast(
    tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json"))
td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_dga_val.parquet").to_pylist()[:2048]
domains = [str(r["domain"]) for r in td]

for bs in (64, 256, 512, 1024):
    torch.mps.empty_cache()
    base = torch.mps.current_allocated_memory()
    chunk = domains[:bs]
    tk = official.encode_subword(chunk, tokenizer).to(DEVICE)
    ch = official.encode_char(chunk).to(DEVICE)
    t0 = time.time()
    try:
        with torch.no_grad():
            tf_n, cf_n = diag.branch_features(model, tk, ch)
        peak_ng = torch.mps.current_allocated_memory()
        t_ng = time.time() - t0
        del tf_n, cf_n
    except RuntimeError as exc:
        print(f"bs={bs}: no_grad OOM -> {str(exc)[:120]}", flush=True)
        break
    torch.mps.empty_cache()
    base2 = torch.mps.current_allocated_memory()
    t0 = time.time()
    try:
        tf_g, cf_g = diag.branch_features(model, tk, ch)
        peak_g = torch.mps.current_allocated_memory()
        t_g = time.time() - t0
        print(f"bs={bs:5d}: no_grad 峰值 +{gib(peak_ng - base)} GiB ({t_ng:.1f}s) | "
              f"带梯度 峰值 +{gib(peak_g - base2)} GiB ({t_g:.1f}s)", flush=True)
        del tf_g, cf_g
    except RuntimeError as exc:
        print(f"bs={bs:5d}: no_grad 峰值 +{gib(peak_ng - base)} GiB ({t_ng:.1f}s) | "
              f"带梯度 OOM -> {str(exc)[:110]}", flush=True)
        break
    del tk, ch
    torch.mps.empty_cache()
