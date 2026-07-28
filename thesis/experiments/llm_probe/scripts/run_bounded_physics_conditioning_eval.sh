#!/usr/bin/env bash
set -eo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  printf '用法：%s <e1|e2> [42|43|44]\n' "$0" >&2
  exit 2
fi

VARIANT="$1"
SEED="${2:-42}"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG="configs/bounded_physics_conditioning_seed${SEED}_eval300.yaml"

if [[ "$SEED" != "42" && "$SEED" != "43" && "$SEED" != "44" ]]; then
  printf '评估训练种子只允许 42、43、44：%s\n' "$SEED" >&2
  exit 2
fi

if [[ "$VARIANT" == "e1" && "$SEED" != "42" ]]; then
  printf '种子 43、44 只预注册 E2 复现评估\n' >&2
  exit 2
fi

case "$VARIANT" in
  e1)
    TRAINING_DIR="runs/bounded-physics-conditioning/qwen3-1.7b-seed${SEED}-e1-structure-only-full202-v1"
    OUTPUT_DIR="runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed${SEED}-e1-structure-only-eval300-v1"
    ;;
  e2)
    TRAINING_DIR="runs/bounded-physics-conditioning/qwen3-1.7b-seed${SEED}-e2-pinn-combined-full202-v1"
    OUTPUT_DIR="runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed${SEED}-e2-pinn-combined-eval300-v1"
    ;;
  *)
    printf '未知评估变体：%s；只允许 e1、e2\n' "$VARIANT" >&2
    exit 2
    ;;
esac

LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"
if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi
if [[ ! -f "$CONFIG" ]]; then
  printf '评估配置不存在：%s\n' "$CONFIG" >&2
  exit 2
fi
if [[ -e "$OUTPUT_DIR" || -e "$LAUNCHER_LOG" ]]; then
  printf '评估目录或启动日志已存在，拒绝复用：%s\n' "$OUTPUT_DIR" >&2
  exit 2
fi
if [[ ! -f "${TRAINING_DIR}/training_summary.json" || ! -f "${TRAINING_DIR}/structure_state.pt" ]]; then
  printf '固定训练制品不完整：%s\n' "$TRAINING_DIR" >&2
  exit 2
fi

source /root/.bashrc
set -u
mkdir -p "$(dirname "$OUTPUT_DIR")"

set +e
{
  printf 'BOUNDED_PHYSICS_EVALUATION=开始\n'
  printf 'VARIANT=%s\n' "$VARIANT"
  printf 'TRAINING_DIR=%s\n' "$TRAINING_DIR"
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  uv run --no-sync flow-probe-evaluate-bounded-physics \
    --config "$CONFIG" \
    --variant "$VARIANT"
  status=$?
  printf 'BOUNDED_PHYSICS_EVALUATION_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
