#!/usr/bin/env bash
set -uo pipefail
ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
D=$ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1
echo "=== 目录树 ==="
find $D -maxdepth 3 -type f -printf '%s\t%p\n' 2>/dev/null | sort -k2 | head -60
echo "=== 收据文件内容（只打印 json，非敏感） ==="
for f in $(find $D -maxdepth 2 -name '*.json' 2>/dev/null | sort); do
  echo "----- $f -----"
  head -c 6000 "$f"
  echo
done
echo "RECON_RECEIPTS_DONE"
