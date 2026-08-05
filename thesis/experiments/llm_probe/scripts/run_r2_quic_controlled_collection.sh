#!/usr/bin/env bash

# 以唯一身份启动可恢复 QUIC CPU 采集，并完整保留主管道与 tee 退出码。
source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
PHASE="${1:-field}"
RUN_ID="${2:-r2-quic-${PHASE}-v1}"
STOP_AFTER="${3:-}"
ONLY_INDEX="${4:-}"
OUTPUT_ROOT="${5:-}"
CONFIG_ARGUMENT="${6:-}"
if [[ -z "${CONFIG_ARGUMENT}" ]]; then
  CONFIG_PATH="${PROJECT_ROOT}/configs/r2_quic_controlled_collection_userspace_v1.json"
elif [[ "${CONFIG_ARGUMENT}" == /* ]]; then
  CONFIG_PATH="${CONFIG_ARGUMENT}"
else
  CONFIG_PATH="${PROJECT_ROOT}/${CONFIG_ARGUMENT}"
fi
if [[ "${STOP_AFTER}" == "-" ]]; then
  STOP_AFTER=""
fi
LAUNCHER_ROOT="${PROJECT_ROOT}/runs/launchers/${RUN_ID}"
LOG_PATH="${LAUNCHER_ROOT}/launcher.log"
STATUS_PATH="${LAUNCHER_ROOT}/status.json"
SCRIPT_PATH="${PROJECT_ROOT}/scripts/run_r2_quic_controlled_collection.sh"
APT_LIBRARY_PATH="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v1/apt-root/usr/lib/x86_64-linux-gnu"

export LD_LIBRARY_PATH="${APT_LIBRARY_PATH}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

mkdir -p "${LAUNCHER_ROOT}"

write_status() {
  local status="$1"
  local driver_exit="$2"
  local tee_exit="$3"
  local temporary="${STATUS_PATH}.tmp"
  printf '{"schema_version":"flow_probe_r2_quic_launcher_v1","status":"%s","phase":"%s","driver_exit":%s,"tee_exit":%s,"updated_at":"%s"}\n' \
    "${status}" "${PHASE}" "${driver_exit}" "${tee_exit}" "$(date -Iseconds)" > "${temporary}"
  mv "${temporary}" "${STATUS_PATH}"
}

if [[ "${R2_QUIC_IN_SCREEN:-0}" != "1" ]]; then
  if [[ -f "${STATUS_PATH}" ]]; then
    printf '启动目录已存在状态文件，拒绝重复启动：%s\n' "${STATUS_PATH}" >&2
    exit 1
  fi
  write_status "prepared" "null" "null"
  screen -dmS "${RUN_ID}" env R2_QUIC_IN_SCREEN=1 bash "${SCRIPT_PATH}" \
    "${PHASE}" "${RUN_ID}" "${STOP_AFTER}" "${ONLY_INDEX}" "${OUTPUT_ROOT}" \
    "${CONFIG_PATH}"
  printf '%s\n' "${LAUNCHER_ROOT}"
  exit 0
fi

write_status "running" "null" "null"
driver_command=(
  "${PROJECT_ROOT}/.venv/bin/python"
  "${PROJECT_ROOT}/scripts/r2_quic_controlled_collect.py"
  --project-root "${PROJECT_ROOT}"
  --config "${CONFIG_PATH}"
  --phase "${PHASE}"
)
if [[ -n "${STOP_AFTER}" ]]; then
  driver_command+=(--stop-after "${STOP_AFTER}")
fi
if [[ -n "${ONLY_INDEX}" ]]; then
  driver_command+=(--only-index "${ONLY_INDEX}")
fi
if [[ -n "${OUTPUT_ROOT}" ]]; then
  driver_command+=(--output-root "${OUTPUT_ROOT}")
fi

set +e
"${driver_command[@]}" 2>&1 | tee "${LOG_PATH}"
pipeline_status=("${PIPESTATUS[@]}")
set -e
driver_exit="${pipeline_status[0]}"
tee_exit="${pipeline_status[1]}"
if [[ "${driver_exit}" -eq 0 && "${tee_exit}" -eq 0 && -s "${LOG_PATH}" ]]; then
  write_status "finished" "${driver_exit}" "${tee_exit}"
  exit 0
fi
write_status "failed" "${driver_exit}" "${tee_exit}"
exit 1
