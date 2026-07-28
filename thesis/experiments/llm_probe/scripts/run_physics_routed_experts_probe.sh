#!/usr/bin/env bash
set -eo pipefail

if [[ $# -ne 3 ]]; then
  printf '用法：%s <single|routed> <唯一输出目录> <2|50>\n' "$0" >&2
  exit 2
fi

VARIANT="$1"
OUTPUT_DIR="$2"
MAX_STEPS="$3"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
MODEL="/root/autodl-tmp/thesis/models/Qwen3-1.7B"
CONFIG="configs/physics_routed_experts_seed42.yaml"
DETECTION_ADAPTER="runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/final_adapter"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"

case "$VARIANT" in
  single | routed) ;;
  *)
    printf '未知变体：%s；只允许 single、routed\n' "$VARIANT" >&2
    exit 2
    ;;
esac

if [[ "$MAX_STEPS" != "2" && "$MAX_STEPS" != "50" ]]; then
  printf '训练步数只允许 2（冒烟）或 50（方向探针）：%s\n' "$MAX_STEPS" >&2
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
  printf 'PHYSICS_ROUTED_EXPERTS=开始\n'
  printf 'VARIANT=%s\n' "$VARIANT"
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  printf 'MAX_STEPS=%s\n' "$MAX_STEPS"
  printf 'DETECTION_ADAPTER=%s\n' "$DETECTION_ADAPTER"
  uv run --no-sync python -m flow_probe.physics_routed_experts_train \
    --config "$CONFIG" \
    --variant "$VARIANT" \
    --detection-adapter-path "$DETECTION_ADAPTER" \
    --output-dir "$OUTPUT_DIR" \
    --run-name "$(basename "$OUTPUT_DIR")" \
    --max-steps "$MAX_STEPS" \
    --model-path "$MODEL"
  status=$?
  printf 'PHYSICS_ROUTED_EXPERTS_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1

