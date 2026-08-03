#!/usr/bin/env bash

if [[ -f "$HOME/.bashrc" ]]; then
  source "$HOME/.bashrc" >/dev/null 2>&1
fi
set -Eeuo pipefail

if [[ "$#" -ne 1 ]]; then
  printf '%s\n' '用法：bash scripts/run_r2_protocol_tqhc2_handoff.sh <参数JSON>' >&2
  exit 2
fi

params_path="$1"
if [[ ! -f "$params_path" || -L "$params_path" ]]; then
  printf 'TQH 正式移交参数不是普通文件：%s\n' "$params_path" >&2
  exit 2
fi

schema_version="$(jq -er '.schema_version' "$params_path")"
host_role="$(jq -er '.host_role' "$params_path")"
project_root="$(jq -er '.project_root' "$params_path")"
python_executable="$(jq -er '.python_executable' "$params_path")"
receipt_path="$(jq -er '.receipt_path' "$params_path")"
if [[ "$schema_version" != 'flow_probe_r2_tqhc2_handoff_params_v1' ]]; then
  printf '%s\n' 'TQH 正式移交参数模式版本不符合合同' >&2
  exit 2
fi
if [[ "$host_role" != 'local_producer' ]]; then
  printf '%s\n' 'TQH 正式移交只允许 local_producer' >&2
  exit 2
fi
if [[ ! -x "$python_executable" ]]; then
  printf '正式 Python 解释器不可执行：%s\n' "$python_executable" >&2
  exit 2
fi

run_root="$(dirname "$receipt_path")"
mkdir -p "$run_root"
status_path="$run_root/status.txt"
log_path="$run_root/launcher.log"
capabilities_path="$run_root/capabilities.json"
for output_path in "$status_path" "$log_path" "$capabilities_path" "$receipt_path"; do
  if [[ -e "$output_path" || -L "$output_path" ]]; then
    printf 'TQH 正式移交输出已存在，拒绝覆盖：%s\n' "$output_path" >&2
    exit 2
  fi
done

printf '%s\n' 'prepared' >"$status_path"
jq -n \
  --arg schema_version 'flow_probe_r2_tqhc2_handoff_capabilities_v1' \
  --arg host_role "$host_role" \
  --arg python_executable "$python_executable" \
  --arg jq_path "$(command -v jq)" \
  '{schema_version:$schema_version,host_role:$host_role,python_executable:$python_executable,jq_path:$jq_path}' \
  >"$capabilities_path"
printf '%s\n' 'running' >"$status_path"

set +e
CUDA_VISIBLE_DEVICES='' PYTHONPATH="$project_root/src" \
  "$python_executable" -B -m flow_probe.r2_protocol_tqhc2 \
  handoff --params "$params_path" 2>&1 | tee "$log_path"
pipeline_status=("${PIPESTATUS[@]}")
set -e
python_status="${pipeline_status[0]}"
tee_status="${pipeline_status[1]}"
if [[ "$python_status" -ne 0 || "$tee_status" -ne 0 || ! -s "$log_path" ]]; then
  printf 'failed:%s:%s\n' "$python_status" "$tee_status" >"$status_path"
  if [[ "$python_status" -ne 0 ]]; then
    exit "$python_status"
  fi
  if [[ "$tee_status" -ne 0 ]]; then
    exit "$tee_status"
  fi
  exit 1
fi
if [[ ! -f "$receipt_path" || -L "$receipt_path" ]]; then
  printf '%s\n' 'TQH 正式移交没有生成普通文件回执' >"$status_path"
  exit 1
fi
printf '%s\n' 'finished' >"$status_path"
