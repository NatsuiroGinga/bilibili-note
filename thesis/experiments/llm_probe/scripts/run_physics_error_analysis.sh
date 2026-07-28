#!/usr/bin/env bash

source /root/.bashrc
set -euo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
BASE_MODEL="/root/autodl-tmp/thesis/models/Qwen3-1.7B"
M1_RUN="runs/physics-m012/qwen3-1.7b-seed42-m1-fullphys202-v1"
M2_RUN="runs/physics-m012/qwen3-1.7b-seed42-m2-lp0p01-fullphys202-v1"
DATA="runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/validation.jsonl"
OUTPUT="${1:-runs/physics-error-analysis/qwen3-1.7b-seed42-m1-vs-m2-fullphys202-validation-v1}"

if [[ "${PWD}" != "${PROJECT_ROOT}" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "${PROJECT_ROOT}" >&2
  exit 2
fi

uv run --no-sync flow-probe-analyze-physics-errors \
  --base-model "${BASE_MODEL}" \
  --run "M1=${M1_RUN}" \
  --run "M2=${M2_RUN}" \
  --data "${DATA}" \
  --output "${OUTPUT}" \
  --tracking-mode online
