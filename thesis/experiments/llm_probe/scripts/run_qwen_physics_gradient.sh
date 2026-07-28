#!/usr/bin/env bash
set -eo pipefail

if [[ $# -lt 4 || $# -gt 5 ]]; then
  printf '用法：%s 基座模型目录 适配器目录 输出目录 运行名称 [随机种子]\n' "$0" >&2
  exit 2
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_PATH="$1"
ADAPTER_PATH="$2"
OUTPUT_DIR="$3"
RUN_NAME="$4"
SEED="${5:-42}"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"

mkdir -p "$(dirname "$OUTPUT_DIR")"
cd "$PROJECT_ROOT"
source /root/.bashrc
set -u

set +e
{
  printf 'QWEN_PHYSICS_GRADIENT=开始\n'
  printf 'MODEL_PATH=%s\n' "$MODEL_PATH"
  printf 'ADAPTER_PATH=%s\n' "$ADAPTER_PATH"
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  printf 'RUN_NAME=%s\n' "$RUN_NAME"
  printf 'SEED=%s\n' "$SEED"
  uv run --no-sync python -m flow_probe.qwen_physics_gradient \
    --model-path "$MODEL_PATH" \
    --adapter-path "$ADAPTER_PATH" \
    --output-dir "$OUTPUT_DIR" \
    --run-name "$RUN_NAME" \
    --seed "$SEED"
  status=$?
  printf 'QWEN_PHYSICS_GRADIENT_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
