#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG="configs/physics_m012_seed42_pilot.yaml"
MODEL="/root/autodl-tmp/thesis/models/Qwen3-1.7B"
MODE="${1:-}"
REVISION="${3:-v1}"

if [[ "${PWD}" != "${PROJECT_ROOT}" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "${PROJECT_ROOT}" >&2
  exit 2
fi

case "${MODE}" in
  smoke)
    STEPS=2
    SUFFIX="smoke"
    VALIDATION_ARGS=(--validation-limit 16)
    ;;
  pilot50)
    STEPS=50
    SUFFIX="pilot50"
    VALIDATION_ARGS=()
    ;;
  *)
    printf '用法：%s smoke|pilot50 [M0|M1|M2] [vN]\n' "$0" >&2
    exit 2
    ;;
esac

if [[ $# -ge 2 ]]; then
  VARIANTS=("${2^^}")
else
  VARIANTS=(M0 M1 M2)
fi

if [[ ! "${REVISION}" =~ ^v[0-9]+$ ]]; then
  printf '运行修订号必须采用 vN 格式：%s\n' "${REVISION}" >&2
  exit 2
fi

for VARIANT in "${VARIANTS[@]}"; do
  case "${VARIANT}" in
    M0 | M1 | M2) ;;
    *)
      printf '未知训练变体：%s\n' "${VARIANT}" >&2
      exit 2
      ;;
  esac
  LOWER_VARIANT="${VARIANT,,}"
  RUN_NAME="qwen3-1.7b-seed42-${LOWER_VARIANT}-${SUFFIX}-${REVISION}"
  uv run --no-sync flow-probe-train-physics \
    --config "${CONFIG}" \
    --variant "${VARIANT}" \
    --output-dir "runs/physics-m012/${RUN_NAME}" \
    --run-name "${RUN_NAME}" \
    --max-steps "${STEPS}" \
    --model-path "${MODEL}" \
    "${VALIDATION_ARGS[@]}"
done
