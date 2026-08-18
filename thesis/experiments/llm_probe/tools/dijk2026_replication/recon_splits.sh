#!/usr/bin/env bash
set -uo pipefail
ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
D=$ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1
echo "=== 全部文件 ==="
find $D -type f -printf '%s\t%p\n' 2>/dev/null | sort -k2
echo "=== splits 相关 json ==="
for f in $(find $D -type f -name '*.json' | rg -i 'split|input|dataset|manifest' ); do
  echo "----- $f -----"
  head -c 8000 "$f"; echo
done
echo "DONE"
