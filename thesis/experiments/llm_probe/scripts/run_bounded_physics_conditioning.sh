#!/usr/bin/env bash
set -eo pipefail

if [[ $# -lt 2 || $# -gt 4 ]]; then
  printf '用法：%s <e1|e2> <唯一输出目录> [2|202] [配置路径]\n' "$0" >&2
  exit 2
fi

GROUP="$1"
OUTPUT_DIR="$2"
MAX_STEPS="${3:-202}"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG="${4:-configs/bounded_physics_conditioning_seed42.yaml}"
MODEL="/root/autodl-tmp/thesis/models/Qwen3-1.7B"
DETECTION_ADAPTER="runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/final_adapter"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"

case "$GROUP" in
  e1)
    VARIANT="structure_only"
    ;;
  e2)
    VARIANT="combined"
    ;;
  *)
    printf '未知实验组：%s；只允许 e1、e2\n' "$GROUP" >&2
    exit 2
    ;;
esac

if [[ "$MAX_STEPS" != "2" && "$MAX_STEPS" != "202" ]]; then
  printf '训练步数只允许 2（冒烟）或 202（正式）：%s\n' "$MAX_STEPS" >&2
  exit 2
fi

if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi

if [[ ! -f "$CONFIG" ]]; then
  printf '配置文件不存在：%s\n' "$CONFIG" >&2
  exit 2
fi

if [[ -e "$OUTPUT_DIR" || -L "$OUTPUT_DIR" ]]; then
  printf '输出目录必须预先不存在：%s\n' "$OUTPUT_DIR" >&2
  exit 2
fi

if [[ -e "$LAUNCHER_LOG" || -L "$LAUNCHER_LOG" ]]; then
  printf '启动日志已存在，拒绝覆盖：%s\n' "$LAUNCHER_LOG" >&2
  exit 2
fi

source /root/.bashrc
set -u
mkdir -p "$(dirname "$OUTPUT_DIR")"

set +e
{
  printf 'BOUNDED_PHYSICS_CONDITIONING=开始\n'
  printf 'GROUP=%s\n' "$GROUP"
  printf 'VARIANT=%s\n' "$VARIANT"
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  printf 'MAX_STEPS=%s\n' "$MAX_STEPS"
  printf 'DETECTION_ADAPTER=%s\n' "$DETECTION_ADAPTER"
  uv run --no-sync flow-probe-train-bounded-physics \
    --config "$CONFIG" \
    --variant "$VARIANT" \
    --detection-adapter-path "$DETECTION_ADAPTER" \
    --output-dir "$OUTPUT_DIR" \
    --run-name "$(basename "$OUTPUT_DIR")" \
    --max-steps "$MAX_STEPS" \
    --model-path "$MODEL"
  status=$?
  printf 'BOUNDED_PHYSICS_CONDITIONING_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
