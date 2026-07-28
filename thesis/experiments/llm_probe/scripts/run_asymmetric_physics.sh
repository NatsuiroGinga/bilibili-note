#!/usr/bin/env bash
set -eo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  printf '用法：%s 输出目录 [训练步数]\n' "$0" >&2
  exit 2
fi

OUTPUT_DIR="$1"
MAX_STEPS="${2:-202}"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
MODEL="/root/autodl-tmp/thesis/models/Qwen3-1.7B"
CONFIG="configs/asymmetric_physics_seed42.yaml"
DETECTION_ADAPTER="runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/final_adapter"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"

if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi

source /root/.bashrc
set -u
mkdir -p "$(dirname "$OUTPUT_DIR")"

set +e
{
  printf 'ASYMMETRIC_PHYSICS=开始\n'
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  printf 'MAX_STEPS=%s\n' "$MAX_STEPS"
  printf 'DETECTION_ADAPTER=%s\n' "$DETECTION_ADAPTER"
  uv run --no-sync flow-probe-train-asymmetric-physics \
    --config "$CONFIG" \
    --detection-adapter-path "$DETECTION_ADAPTER" \
    --output-dir "$OUTPUT_DIR" \
    --run-name "$(basename "$OUTPUT_DIR")" \
    --max-steps "$MAX_STEPS" \
    --model-path "$MODEL"
  status=$?
  printf 'ASYMMETRIC_PHYSICS_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
