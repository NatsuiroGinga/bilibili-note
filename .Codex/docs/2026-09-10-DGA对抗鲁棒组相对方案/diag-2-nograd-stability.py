#!/usr/bin/env python3
"""E-A1 修复可行性验证：inference_mode 下连续多 batch 的 MPS 内存稳定性。
不修改实验脚本；模拟真实脚本的连续循环（不手动 empty_cache）。
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
BATCH = 1024

model = official.load_model(REF, CKPT, DEVICE)
tokenizer = official.PreTrainedTokenizerFast(
    tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json"))
td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_dga_val.parquet").to_pylist()
domains = [str(r["domain"]) for r in td]
print(f"[stab] 载入 {len(domains)} 域名；模型加载后 MPS current="
      f"{torch.mps.current_allocated_memory() / 2**30:.3f} GiB", flush=True)

n_batches = (len(domains) + BATCH - 1) // BATCH
t0 = time.time()
peak = 0
for off in range(0, len(domains), BATCH):
    chunk = domains[off:off + BATCH]
    with torch.inference_mode():
        tk = official.encode_subword(chunk, tokenizer).to(DEVICE)
        ch = official.encode_char(chunk).to(DEVICE)
        tf, cf = diag.branch_features(model, tk, ch)
        s = diag.probabilities(model, tf.cpu().numpy(), cf.cpu().numpy(),
                               __import__("numpy").zeros(512, dtype="float32"),
                               __import__("numpy").zeros(512, dtype="float32"), DEVICE, BATCH)
    cur = torch.mps.current_allocated_memory()
    drv = torch.mps.driver_allocated_memory()
    peak = max(peak, cur)
    idx = off // BATCH
    if idx % 20 == 0 or idx == n_batches - 1:
        el = time.time() - t0
        print(f"[stab] batch {idx + 1}/{n_batches} current={cur / 2**30:.3f} GiB "
              f"driver={drv / 2**30:.3f} GiB 累计 {el:.1f}s", flush=True)

el = time.time() - t0
print(f"[stab] 完成 {n_batches} 批，峰值 current={peak / 2**30:.3f} GiB，"
      f"总耗时 {el:.1f}s，均 {el / n_batches:.2f}s/批", flush=True)
