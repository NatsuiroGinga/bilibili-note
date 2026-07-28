#!/usr/bin/env bash
set -eo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  printf '用法：%s constant_state|state_supervision|standard_pinn 42|43|44 输出目录 [formal|smoke2]\n' "$0" >&2
  exit 2
fi

BASELINE="$1"
SEED="$2"
OUTPUT_DIR="$3"
MODE="${4:-formal}"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG="configs/ns3_physics_baselines_star_v1.yaml"
INPUT_DIR="runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2"
FORMAL_ROOT="runs/baselines/theory-selection/ns3-star-physics/review-pending-3393d76e-v1"
SMOKE_ROOT="runs/smoke/ns3-star-physics"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"

case "$BASELINE" in
  constant_state | state_supervision | standard_pinn) ;;
  *)
    printf '未知物理基线：%s\n' "$BASELINE" >&2
    exit 2
    ;;
esac

case "$SEED" in
  42|43|44) ;;
  *)
    printf '模型随机种子只允许 42、43、44：%s\n' "$SEED" >&2
    exit 2
    ;;
esac

EXTRA_ARGS=()
case "$MODE" in
  formal)
    RUN_KIND="formal"
    EXPECTED_RELATIVE_OUTPUT="${FORMAL_ROOT}/${BASELINE}-seed${SEED}"
    EXPECTED_ABSOLUTE_OUTPUT="${PROJECT_ROOT}/${EXPECTED_RELATIVE_OUTPUT}"
    if [[ "$OUTPUT_DIR" != "$EXPECTED_RELATIVE_OUTPUT" && "$OUTPUT_DIR" != "$EXPECTED_ABSOLUTE_OUTPUT" ]]; then
      printf '正式运行输出目录必须固定为：%s\n' "$EXPECTED_RELATIVE_OUTPUT" >&2
      exit 2
    fi
    ;;
  smoke2)
    RUN_KIND="smoke"
    EXTRA_ARGS=(--smoke-max-epochs 2)
    if [[ "$OUTPUT_DIR" != "$SMOKE_ROOT/"* && "$OUTPUT_DIR" != "$PROJECT_ROOT/$SMOKE_ROOT/"* ]]; then
      printf '冒烟运行只能写入：%s/\n' "$SMOKE_ROOT" >&2
      exit 2
    fi
    ;;
  *)
    printf '运行模式只允许 formal 或 smoke2：%s\n' "$MODE" >&2
    exit 2
    ;;
esac

if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi
if [[ ! -d "$INPUT_DIR" ]]; then
  printf '冻结星型输入目录不存在：%s\n' "$INPUT_DIR" >&2
  exit 2
fi
if [[ -e "$OUTPUT_DIR" || -e "$LAUNCHER_LOG" ]]; then
  printf '输出目录或启动器日志已存在，不得复用：%s\n' "$OUTPUT_DIR" >&2
  exit 2
fi

source /root/.bashrc
set -u
mkdir -p "$(dirname "$OUTPUT_DIR")"
RUN_NAME="ns3-star-${BASELINE}-seed${SEED}-$(basename "$OUTPUT_DIR")"

set +e
{
  printf 'NS3_PHYSICS_BASELINE=开始\n'
  printf 'BASELINE=%s\n' "$BASELINE"
  printf 'SEED=%s\n' "$SEED"
  printf 'MODE=%s\n' "$MODE"
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  uv run --no-sync flow-probe-ns3-physics-baseline run \
    --config "$CONFIG" \
    --baseline "$BASELINE" \
    --seed "$SEED" \
    --output-dir "$OUTPUT_DIR" \
    --run-name "$RUN_NAME" \
    --run-kind "$RUN_KIND" \
    "${EXTRA_ARGS[@]}"
  status=$?
  printf 'NS3_PHYSICS_BASELINE_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
