#!/usr/bin/env bash
set -eo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  printf '用法：%s <d1|d2|d3> 输出目录 [训练步数]\n' "$0" >&2
  exit 2
fi

SHORT_MODE="$1"
OUTPUT_DIR="$2"
MAX_STEPS="${3:-202}"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
MODEL="/root/autodl-tmp/thesis/models/Qwen3-1.7B"
CONFIG="configs/asymmetric_diagnostic_seed42.yaml"
DETECTION_ADAPTER="runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/final_adapter"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"

case "$SHORT_MODE" in
  d1) DIAGNOSTIC_MODE="generation_only" ;;
  d2) DIAGNOSTIC_MODE="physics_only" ;;
  d3) DIAGNOSTIC_MODE="joint_warmup_cosine" ;;
  *)
    printf '未知诊断模式：%s；只允许 d1、d2、d3\n' "$SHORT_MODE" >&2
    exit 2
    ;;
esac

if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi
if [[ -e "$OUTPUT_DIR" || -e "$LAUNCHER_LOG" ]]; then
  printf '输出目录或启动日志已存在，拒绝复用：%s\n' "$OUTPUT_DIR" >&2
  exit 2
fi

source /root/.bashrc
set -u
mkdir -p "$(dirname "$OUTPUT_DIR")"

set +e
{
  printf 'ASYMMETRIC_DIAGNOSTIC=开始\n'
  printf 'SHORT_MODE=%s\n' "$SHORT_MODE"
  printf 'DIAGNOSTIC_MODE=%s\n' "$DIAGNOSTIC_MODE"
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  printf 'MAX_STEPS=%s\n' "$MAX_STEPS"
  printf 'DETECTION_ADAPTER=%s\n' "$DETECTION_ADAPTER"
  uv run --no-sync flow-probe-train-asymmetric-physics \
    --config "$CONFIG" \
    --detection-adapter-path "$DETECTION_ADAPTER" \
    --output-dir "$OUTPUT_DIR" \
    --run-name "$(basename "$OUTPUT_DIR")" \
    --max-steps "$MAX_STEPS" \
    --model-path "$MODEL" \
    --diagnostic-mode "$DIAGNOSTIC_MODE"
  status=$?
  printf 'ASYMMETRIC_DIAGNOSTIC_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
