#!/usr/bin/env bash
# 实跑归档包里的 inference.py，并把输出与既有 ch3-2x2-fairsel/scores_C11.npy 逐位比对。
# 这是选择冻结之后的只读复核，不产生任何选择信号，也不改动既有制品。
set -uo pipefail
ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
PKG="$ROOT/runs/diagnostics/ch3-final-weights"
CACHE="$ROOT/runs/diagnostics/dijk-repro/cache"
REF="$ROOT/runs/diagnostics/ch3-2x2-fairsel"
cd "$ROOT" || exit 1

echo "== 执行命令 =="
cat <<'CMD'
uv run --no-sync python runs/diagnostics/ch3-final-weights/inference.py \
  --package-root runs/diagnostics/ch3-final-weights \
  --cell C11 \
  --x-npy     runs/diagnostics/dijk-repro/cache/X24.npy \
  --index-npy runs/diagnostics/dijk-repro/cache/I24.npy \
  --mask-npy  runs/diagnostics/dijk-repro/cache/M24.npy \
  --input-convention standardized-cache \
  --out-npy      runs/diagnostics/ch3-final-weights/inference_check_C11.npy \
  --out-seen-npy runs/diagnostics/ch3-final-weights/inference_check_seen_C11.npy
CMD

echo "== 运行输出 =="
uv run --no-sync python "$PKG/inference.py" \
  --package-root "$PKG" \
  --cell C11 \
  --x-npy "$CACHE/X24.npy" \
  --index-npy "$CACHE/I24.npy" \
  --mask-npy "$CACHE/M24.npy" \
  --input-convention standardized-cache \
  --out-npy "$PKG/inference_check_C11.npy" \
  --out-seen-npy "$PKG/inference_check_seen_C11.npy"
RC=$?
echo "inference.py 退出码=$RC"
[ $RC -ne 0 ] && exit $RC

echo "== 与既有 scores_C11.npy 逐位比对 =="
uv run --no-sync python - "$PKG/inference_check_C11.npy" "$PKG/inference_check_seen_C11.npy" "$REF/scores_C11.npy" "$REF/seen_C11.npy" <<'PY'
import hashlib
import sys

import numpy as np

new_s, new_m, ref_s, ref_m = (np.load(p) for p in sys.argv[1:5])
eq_s = bool(np.array_equal(new_s, ref_s))
eq_m = bool(np.array_equal(new_m, ref_m))
d = np.abs(new_s.astype(np.float64) - ref_s.astype(np.float64))
print(f"分数 np.array_equal={eq_s}  掩码 np.array_equal={eq_m}")
print(f"元素数={new_s.size:,} 不同元素={int((new_s != ref_s).sum()):,} 最大绝对差={d.max():.6e}")
print("sha256(新分数字节)=" + hashlib.sha256(new_s.tobytes()).hexdigest())
print("sha256(既有分数字节)=" + hashlib.sha256(ref_s.tobytes()).hexdigest())
sys.exit(0 if (eq_s and eq_m) else 9)
PY
echo "比对退出码=$?"
