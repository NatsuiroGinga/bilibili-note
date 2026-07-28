#!/usr/bin/env bash
set -eo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  printf '用法：%s S1|S2|S3|S4 输出目录 [训练步数]\n' "$0" >&2
  exit 2
fi

GROUP="${1^^}"
OUTPUT_DIR="$2"
MAX_STEPS="${3:-202}"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG="configs/physics_sparse_seed42.yaml"
MODEL="/root/autodl-tmp/thesis/models/Qwen3-1.7B"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"

case "$GROUP" in
  S1)
    VARIANT="M1"
    MODE="anchor0_only"
    ;;
  S2)
    VARIANT="M2"
    MODE="anchor0_only"
    ;;
  S3)
    VARIANT="M1"
    MODE="anchor0_plus_one"
    ;;
  S4)
    VARIANT="M2"
    MODE="anchor0_plus_one"
    ;;
  *)
    printf '未知实验组：%s；只允许 S1、S2、S3、S4\n' "$GROUP" >&2
    exit 2
    ;;
esac

if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi

source /root/.bashrc
set -u
mkdir -p "$(dirname "$OUTPUT_DIR")"

set +e
{
  printf 'PHYSICS_SPARSE=开始\n'
  printf 'GROUP=%s\n' "$GROUP"
  printf 'VARIANT=%s\n' "$VARIANT"
  printf 'STATE_SUPERVISION_MODE=%s\n' "$MODE"
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  printf 'MAX_STEPS=%s\n' "$MAX_STEPS"
  uv run --no-sync flow-probe-train-physics \
    --config "$CONFIG" \
    --variant "$VARIANT" \
    --state-supervision-mode "$MODE" \
    --lambda-physics 0.01 \
    --output-dir "$OUTPUT_DIR" \
    --run-name "$(basename "$OUTPUT_DIR")" \
    --max-steps "$MAX_STEPS" \
    --model-path "$MODEL"
  status=$?
  printf 'PHYSICS_SPARSE_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
