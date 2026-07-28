#!/usr/bin/env bash
set -eo pipefail

if [[ $# -ne 1 ]]; then
  printf '用法：%s <d1|d2|d3>\n' "$0" >&2
  exit 2
fi

SHORT_MODE="$1"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
S3_OUTPUT="runs/physics-detection-evaluation/qwen3-1.7b-seed42-s3-anchor0-plus-one-eval300-v1"
S3_TRAINING="runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1"

case "$SHORT_MODE" in
  d1)
    CANDIDATE_OUTPUT="runs/asymmetric-physics-diagnostic-evaluation/qwen3-1.7b-seed42-d1-generation-only-eval300-v1"
    CANDIDATE_TRAINING="runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d1-generation-only-full202-v1"
    OUTPUT_DIR="runs/asymmetric-physics-diagnostic-evaluation/s3-d1-seed42-eval300-comparison-v1"
    ;;
  d2)
    CANDIDATE_OUTPUT="runs/asymmetric-physics-diagnostic-evaluation/qwen3-1.7b-seed42-d2-physics-only-eval300-v1"
    CANDIDATE_TRAINING="runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d2-physics-only-full202-v1"
    OUTPUT_DIR="runs/asymmetric-physics-diagnostic-evaluation/s3-d2-seed42-eval300-comparison-v1"
    ;;
  d3)
    CANDIDATE_OUTPUT="runs/asymmetric-physics-diagnostic-evaluation/qwen3-1.7b-seed42-d3-joint-warmup-cosine-eval300-v1"
    CANDIDATE_TRAINING="runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d3-joint-warmup-cosine-full202-v1"
    OUTPUT_DIR="runs/asymmetric-physics-diagnostic-evaluation/s3-d3-seed42-eval300-comparison-v1"
    ;;
  *)
    printf '未知诊断模式：%s；只允许 d1、d2、d3\n' "$SHORT_MODE" >&2
    exit 2
    ;;
esac

LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"
if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi
if [[ -e "$OUTPUT_DIR" || -e "$LAUNCHER_LOG" ]]; then
  printf '统计目录或启动日志已存在，拒绝复用：%s\n' "$OUTPUT_DIR" >&2
  exit 2
fi

source /root/.bashrc
set -u
mkdir -p "$(dirname "$OUTPUT_DIR")"

set +e
{
  printf 'ASYMMETRIC_DIAGNOSTIC_ANALYSIS=开始\n'
  printf 'SHORT_MODE=%s\n' "$SHORT_MODE"
  printf 'CANDIDATE_KEYS=s4（历史字段名，仅表示当前候选）\n'
  uv run --no-sync python -m flow_probe.s3_s4_detection_analysis \
    --s3-output "$S3_OUTPUT" \
    --s4-output "$CANDIDATE_OUTPUT" \
    --s3-training "$S3_TRAINING" \
    --s4-training "$CANDIDATE_TRAINING" \
    --output "$OUTPUT_DIR" \
    --bootstrap-repetitions 2000 \
    --seed 42
  status=$?
  printf 'ASYMMETRIC_DIAGNOSTIC_ANALYSIS_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
