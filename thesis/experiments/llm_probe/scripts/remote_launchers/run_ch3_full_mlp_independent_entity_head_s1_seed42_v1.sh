#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG="configs/ch3-full-mlp-independent-entity-head-s1-seed42-v1.json"
TOOL="tools/ch3_full_mlp_independent_entity_head_s1.py"
RUN_ID="ch3-full-mlp-independent-entity-head-s1-seed42-v1"
SCREEN_NAME="ch3-mlp-entity-head-s1"
OUTPUT_ROOT="runs/diagnostics/${RUN_ID}"

cd "${ROOT}"
source tools/env/activate.sh
uv run --no-sync python "${TOOL}" --config "${CONFIG}" --validate-config

if [[ -f "${OUTPUT_ROOT}/status.json" ]] && rg -q '"state": "finished"' "${OUTPUT_ROOT}/status.json"; then
  printf '运行已完成：%s\n' "${RUN_ID}"
  exit 0
fi

mkdir -p "${OUTPUT_ROOT}"
if [[ "${1:-}" == "--worker" ]]; then
  set +e
  uv run --no-sync python "${TOOL}" --config "${CONFIG}" --run 2>&1 | tee "${OUTPUT_ROOT}/run.log"
  codes=("${PIPESTATUS[@]}")
  set -e
  exit "${codes[0]}"
fi

if screen -list 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
  printf '持久会话已存在：%s\n' "${SCREEN_NAME}"
  exit 0
fi

screen -dmS "${SCREEN_NAME}" bash "$0" --worker
printf '已启动：screen=%s run_id=%s\n' "${SCREEN_NAME}" "${RUN_ID}"
