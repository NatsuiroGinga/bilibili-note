#!/usr/bin/env bash
set -eo pipefail

if [[ $# -ne 1 ]]; then
  printf '用法：%s 物理私有适配器目录\n' "$0" >&2
  exit 2
fi

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
MODEL="/root/autodl-tmp/thesis/models/Qwen3-1.7B"
CONFIG="configs/asymmetric_physics_seed42_eval300.yaml"
DETECTION_ADAPTER="runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/final_adapter"
TASK_ADAPTER="$1"
OUTPUT_DIR="runs/asymmetric-physics-evaluation/qwen3-1.7b-seed42-asymmetric-physics-eval300-v1"
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
  printf 'ASYMMETRIC_PHYSICS_EVAL=开始\n'
  printf 'TASK_ADAPTER=%s\n' "$TASK_ADAPTER"
  uv run --no-sync flow-probe-evaluate-hierarchical \
    --config "$CONFIG" \
    --model-path "$MODEL" \
    --adapter-path "$DETECTION_ADAPTER" \
    --task-adapter-path "$TASK_ADAPTER"
  status=$?
  printf 'ASYMMETRIC_PHYSICS_EVAL_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
