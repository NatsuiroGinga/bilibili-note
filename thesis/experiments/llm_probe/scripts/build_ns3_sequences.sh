#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  printf '用法：%s <ns-3 真值输入目录> <唯一序列输出目录>\n' "$0" >&2
  exit 2
fi

exec uv run --no-sync flow-probe-build-ns3-sequences \
  --input-dir "$1" \
  --output-dir "$2"
