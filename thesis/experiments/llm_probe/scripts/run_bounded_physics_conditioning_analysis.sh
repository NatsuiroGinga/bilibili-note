#!/usr/bin/env bash
set -eo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  printf '用法：%s <e1|e2|e2-vs-e1> [42|43|44]\n' "$0" >&2
  exit 2
fi

VARIANT="$1"
SEED="${2:-42}"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
S3_OUTPUT="runs/physics-detection-evaluation/qwen3-1.7b-seed42-s3-anchor0-plus-one-eval300-v1"
S3_TRAINING="runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1"

if [[ "$SEED" != "42" && "$SEED" != "43" && "$SEED" != "44" ]]; then
  printf '候选训练种子只允许 42、43、44：%s\n' "$SEED" >&2
  exit 2
fi

if [[ "$VARIANT" != "e2" && "$SEED" != "42" ]]; then
  printf '种子 43、44 只预注册 E2 对 S3 统计\n' >&2
  exit 2
fi

case "$VARIANT" in
  e1)
    CANDIDATE_OUTPUT="runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed42-e1-structure-only-eval300-v1"
    OUTPUT_DIR="runs/bounded-physics-conditioning-evaluation/s3-e1-seed42-eval300-comparison-v1"
    ;;
  e2)
    CANDIDATE_OUTPUT="runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed${SEED}-e2-pinn-combined-eval300-v1"
    OUTPUT_DIR="runs/bounded-physics-conditioning-evaluation/s3-e2-seed${SEED}-eval300-comparison-v1"
    ;;
  e2-vs-e1)
    S3_OUTPUT="runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed42-e1-structure-only-eval300-v1"
    S3_TRAINING="${S3_OUTPUT}/analysis_training_view"
    CANDIDATE_OUTPUT="runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed42-e2-pinn-combined-eval300-v1"
    OUTPUT_DIR="runs/bounded-physics-conditioning-evaluation/e1-e2-seed42-eval300-comparison-v1"
    ;;
  *)
    printf '未知统计变体：%s；只允许 e1、e2、e2-vs-e1\n' "$VARIANT" >&2
    exit 2
    ;;
esac

CANDIDATE_TRAINING="${CANDIDATE_OUTPUT}/analysis_training_view"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"
if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi
if [[ -e "$OUTPUT_DIR" || -e "$LAUNCHER_LOG" ]]; then
  printf '统计目录或启动日志已存在，拒绝复用：%s\n' "$OUTPUT_DIR" >&2
  exit 2
fi
if [[ ! -f "${S3_OUTPUT}/selected_samples_manifest.json" || ! -f "${S3_TRAINING}/training_summary.json" ]]; then
  printf '参照评估或训练摘要不完整：%s\n' "$S3_OUTPUT" >&2
  exit 2
fi
if [[ ! -f "${CANDIDATE_OUTPUT}/selected_samples_manifest.json" || ! -f "${CANDIDATE_TRAINING}/training_summary.json" ]]; then
  printf '候选评估或统计兼容训练摘要不完整：%s\n' "$CANDIDATE_OUTPUT" >&2
  exit 2
fi

source /root/.bashrc
set -u
mkdir -p "$(dirname "$OUTPUT_DIR")"

set +e
{
  printf 'BOUNDED_PHYSICS_ANALYSIS=开始\n'
  printf 'VARIANT=%s\n' "$VARIANT"
  printf 'CANDIDATE_KEYS=s4（历史字段名，仅表示当前 E1/E2 候选）\n'
  uv run --no-sync python -m flow_probe.s3_s4_detection_analysis \
    --s3-output "$S3_OUTPUT" \
    --s4-output "$CANDIDATE_OUTPUT" \
    --s3-training "$S3_TRAINING" \
    --s4-training "$CANDIDATE_TRAINING" \
    --output "$OUTPUT_DIR" \
    --bootstrap-repetitions 2000 \
    --seed 42
  status=$?
  printf 'BOUNDED_PHYSICS_ANALYSIS_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
