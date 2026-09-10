import sys
from pathlib import Path
import pyarrow.parquet as pq
import torch
ROOT = Path("/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe")
sys.path.insert(0, str(ROOT / "tools"))
import ch3_drift_official_branch_conflict_diagnostic as diag
import ch3_drift_official_checkpoint_t17_eval as official
REF = ROOT / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
CKPT = ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"
DATA = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521"
DEVICE = torch.device("mps")
model = official.load_model(REF, CKPT, DEVICE)
tkz = official.PreTrainedTokenizerFast(tokenizer_file=str(REF / "artifacts/tokenizer/tokenizer-0-30522-both.json"))
td = pq.read_table(DATA / "DRIFT_input_eSLD" / "T18_dga_val.parquet").to_pylist()[:64]
d = [str(r["domain"]) for r in td]
tok = official.encode_subword(d, tkz).to(DEVICE)
ch = official.encode_char(d).to(DEVICE)
tf, cf = diag.branch_features(model, tok, ch)
print("tf.requires_grad =", tf.requires_grad, "| cf.requires_grad =", cf.requires_grad, "| grad_fn =", type(tf.grad_fn).__name__ if tf.grad_fn else None, flush=True)
try:
    _ = tf.cpu().numpy()
    print("tf.cpu().numpy() -> OK（未报错）", flush=True)
except RuntimeError as e:
    print("tf.cpu().numpy() -> RuntimeError:", str(e)[:200], flush=True)
