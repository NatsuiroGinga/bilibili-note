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
LAUNCHER_SCHEMA_VERSION="$(
  "${PROJECT_ROOT}/.venv/bin/python" -c '
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(config.get("determinism_contract", {}).get("launcher_schema_version", "flow_probe_r2_quic_launcher_v3"))
' "${CONFIG_PATH}"
)"
if [[ "${LAUNCHER_SCHEMA_VERSION}" != "flow_probe_r2_quic_launcher_v3" && "${LAUNCHER_SCHEMA_VERSION}" != "flow_probe_r2_quic_launcher_v4" ]]; then
  printf '不支持的 QUIC 启动器模式：%s\n' "${LAUNCHER_SCHEMA_VERSION}" >&2
  exit 1
fi
if [[ "${STOP_AFTER}" == "-" ]]; then
  STOP_AFTER=""
fi
if [[ -n "${OUTPUT_ROOT}" && "${OUTPUT_ROOT}" != /* ]]; then
  OUTPUT_ROOT="${PROJECT_ROOT}/${OUTPUT_ROOT}"
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
  local started_at="$4"
  local finished_at="$5"
  local temporary="${STATUS_PATH}.tmp"
  local started_json="null"
  local finished_json="null"
  if [[ -n "${started_at}" ]]; then
    started_json="\"${started_at}\""
  fi
  if [[ -n "${finished_at}" ]]; then
    finished_json="\"${finished_at}\""
  fi
  printf '{"schema_version":"%s","status":"%s","phase":"%s","run_id":"%s","output_root":"%s","config_path":"%s","driver_exit":%s,"tee_exit":%s,"started_at":%s,"finished_at":%s,"updated_at":"%s"}\n' \
    "${LAUNCHER_SCHEMA_VERSION}" "${status}" "${PHASE}" "${RUN_ID}" "${OUTPUT_ROOT}" "${CONFIG_PATH}" \
    "${driver_exit}" "${tee_exit}" "${started_json}" "${finished_json}" \
    "$(date -Iseconds)" > "${temporary}"
  mv "${temporary}" "${STATUS_PATH}"
}

if [[ "${R2_QUIC_IN_SCREEN:-0}" != "1" ]]; then
  if [[ -f "${STATUS_PATH}" ]]; then
    printf '启动目录已存在状态文件，拒绝重复启动：%s\n' "${STATUS_PATH}" >&2
    exit 1
  fi
  write_status "prepared" "null" "null" "" ""
  screen -dmS "${RUN_ID}" env R2_QUIC_IN_SCREEN=1 bash "${SCRIPT_PATH}" \
    "${PHASE}" "${RUN_ID}" "${STOP_AFTER}" "${ONLY_INDEX}" "${OUTPUT_ROOT}" \
    "${CONFIG_PATH}"
  printf '%s\n' "${LAUNCHER_ROOT}"
  exit 0
fi

started_at="$(date -Iseconds)"
write_status "running" "null" "null" "${started_at}" ""
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
  write_status "finished" "${driver_exit}" "${tee_exit}" "${started_at}" "$(date -Iseconds)"
  exit 0
fi
write_status "failed" "${driver_exit}" "${tee_exit}" "${started_at}" "$(date -Iseconds)"
exit 1
