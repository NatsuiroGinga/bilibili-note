#!/usr/bin/env bash
set -eo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
S3_OUTPUT="runs/physics-detection-evaluation/qwen3-1.7b-seed42-s3-anchor0-plus-one-eval300-v1"
S3_PHYSICS="runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-s3-same-split-physics-test-v1"

if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi
if [[ ! -f "${S3_PHYSICS}/artifact_manifest.json" ]]; then
  printf 'S3 同分区物理评估尚未完成：%s\n' "$S3_PHYSICS" >&2
  exit 2
fi

source /root/.bashrc
set -u

for seed in 42 43 44; do
  E2_OUTPUT="runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-seed${seed}-e2-pinn-combined-eval300-v1"
  S3_TRAINING="${S3_PHYSICS}/mask-seed${seed}/analysis_training_view"
  E2_TRAINING="${E2_OUTPUT}/analysis_training_view"
  OUTPUT="runs/bounded-physics-conditioning-evaluation/s3-e2-seed${seed}-eval300-same-split-v2"
  LAUNCHER_LOG="${OUTPUT}.launcher.log"
  if [[ ! -f "${E2_OUTPUT}/evaluation_summary.json" || ! -f "${S3_TRAINING}/training_summary.json" ]]; then
    printf '种子 %s 的固定输入制品不完整\n' "$seed" >&2
    exit 2
  fi
  if [[ -f "${OUTPUT}/comparison_summary.json" && -f "$LAUNCHER_LOG" ]] && \
    rg -q 'S3_E2_SAME_SPLIT_COMPARISON_EXIT=0' "$LAUNCHER_LOG"; then
    printf '种子 %s 的同分区比较已完成，核验后跳过\n' "$seed"
    continue
  fi
  if [[ -e "$OUTPUT" || -e "$LAUNCHER_LOG" ]]; then
    printf '种子 %s 存在不完整比较目录或日志，拒绝覆盖\n' "$seed" >&2
    exit 2
  fi
  set +e
  {
    printf 'S3_E2_SAME_SPLIT_COMPARISON=开始\n'
    printf 'TRAINING_SEED=%s\n' "$seed"
    uv run --no-sync python -m flow_probe.s3_s4_detection_analysis \
      --s3-output "$S3_OUTPUT" \
      --s4-output "$E2_OUTPUT" \
      --s3-training "$S3_TRAINING" \
      --s4-training "$E2_TRAINING" \
      --output "$OUTPUT" \
      --bootstrap-repetitions 2000 \
      --seed 42
    status=$?
    printf 'S3_E2_SAME_SPLIT_COMPARISON_EXIT=%s\n' "$status"
    if [[ -d "$OUTPUT" ]]; then
      cp "$LAUNCHER_LOG" "$OUTPUT/launcher.log"
    fi
  } >"$LAUNCHER_LOG" 2>&1
  set -e
  if [[ "$status" -ne 0 ]]; then
    exit "$status"
  fi
done

printf 'S3_E2_SAME_SPLIT_COMPARISON=全部完成\n'
