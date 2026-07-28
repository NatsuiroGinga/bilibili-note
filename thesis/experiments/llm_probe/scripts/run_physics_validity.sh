#!/usr/bin/env bash
set -eo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  printf '用法：%s 输出目录 运行名称 [随机种子]\n' "$0" >&2
  exit 2
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$1"
RUN_NAME="$2"
SEED="${3:-42}"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"

mkdir -p "$(dirname "$OUTPUT_DIR")"
cd "$PROJECT_ROOT"
source /root/.bashrc
set -u

set +e
{
  printf 'PHYSICS_VALIDITY=开始\n'
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  printf 'RUN_NAME=%s\n' "$RUN_NAME"
  printf 'SEED=%s\n' "$SEED"
  uv run --no-sync python -m flow_probe.physics_validity \
    --output-dir "$OUTPUT_DIR" \
    --run-name "$RUN_NAME" \
    --device cuda \
    --seed "$SEED"
  status=$?
  printf 'PHYSICS_VALIDITY_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
