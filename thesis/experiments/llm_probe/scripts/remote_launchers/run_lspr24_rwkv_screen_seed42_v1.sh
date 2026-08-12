#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

project_root="/root/autodl-tmp/thesis/experiments/llm_probe"
manifest="$project_root/runs/data-prepared/lspr24-screen-wide-v1/dataset-manifest.json"
output_root="$project_root/runs/candidates/lspr24-rwkv-screen-seed42-v1"
cache_dir="$output_root/shared-cache"
launcher_dir="$project_root/runs/launchers/lspr24-rwkv-screen-seed42-v1"
gate_output="$launcher_dir/batch-size-gate.json"
session_name="lspr24-rwkv-s42-v1"
run_name_prefix="lspr24-rwkv-screen-seed42-v1"
script_path="$project_root/scripts/remote_launchers/run_lspr24_rwkv_screen_seed42_v1.sh"
variants=(B1 B1F A2 B3)

cd "$project_root"
source tools/env/activate.sh

write_status() {
  local status=$1
  local temporary="$launcher_dir/status.txt.partial.$$"
  printf '%s\n' "$status" >"$temporary"
  mv "$temporary" "$launcher_dir/status.txt"
}

run_logged_stage() {
  local stage=$1
  shift
  set +e
  "$@" 2>&1 | tee "$launcher_dir/${stage}.log"
  local pipeline_status=("${PIPESTATUS[@]}")
  set -e
  local command_code=${pipeline_status[0]}
  local tee_code=${pipeline_status[1]}
  printf '%s\n' "$command_code" >"$launcher_dir/${stage}-command-exit-code.txt"
  printf '%s\n' "$tee_code" >"$launcher_dir/${stage}-tee-exit-code.txt"
  if [[ "$command_code" -ne 0 ]]; then
    return "$command_code"
  fi
  return "$tee_code"
}

run_variant() {
  local variant=$1
  local batch_size=$2
  local variant_slug
  variant_slug=$(printf '%s' "$variant" | tr '[:upper:]' '[:lower:]')
  local variant_output="$output_root/$variant"
  local variant_log="$launcher_dir/${variant}-console.log"
  local variant_run_name="${run_name_prefix}-${variant_slug}"

  set +e
  bash scripts/run_lspr24_rwkv_screen.sh train \
    "$manifest" \
    "$cache_dir" \
    "$variant_output" \
    "$variant_run_name" \
    "$variant" \
    "$batch_size" 2>&1 | tee "$variant_log"
  local pipeline_status=("${PIPESTATUS[@]}")
  set -e
  local model_code=${pipeline_status[0]}
  local tee_code=${pipeline_status[1]}
  printf '%s\n' "$model_code" >"$launcher_dir/${variant}-model-exit-code.txt"
  printf '%s\n' "$tee_code" >"$launcher_dir/${variant}-tee-exit-code.txt"
  if [[ -d "$variant_output" && -s "$variant_log" ]]; then
    cp -p "$variant_log" "$variant_output/console.log"
  fi
  if [[ "$model_code" -ne 0 ]]; then
    return "$model_code"
  fi
  return "$tee_code"
}

write_controller_summary() {
  local batch_size=$1
  local overall_status=$2
  local temporary="$launcher_dir/controller-summary.json.partial.$$"
  {
    printf '{\n'
    printf '  "schema_version": "lspr24-rwkv-parallel-controller-v1",\n'
    printf '  "status": "%s",\n' "$overall_status"
    printf '  "seed": 42,\n'
    printf '  "batch_size": %s,\n' "$batch_size"
    printf '  "parallel_efficiency_comparable": false,\n'
    printf '  "variants": {\n'
    local index=0
    local variant
    for variant in "${variants[@]}"; do
      local model_code
      local tee_code
      model_code=$(<"$launcher_dir/${variant}-model-exit-code.txt")
      tee_code=$(<"$launcher_dir/${variant}-tee-exit-code.txt")
      index=$((index + 1))
      printf '    "%s": {"model_exit_code": %s, "tee_exit_code": %s}' "$variant" "$model_code" "$tee_code"
      if [[ "$index" -lt "${#variants[@]}" ]]; then
        printf ','
      fi
      printf '\n'
    done
    printf '  }\n'
    printf '}\n'
  } >"$temporary"
  mv "$temporary" "$launcher_dir/controller-summary.json"
}

worker_main() {
  write_status running
  date -u +'%Y-%m-%dT%H:%M:%SZ' >"$launcher_dir/started_at.txt"

  run_logged_stage prepare-cache \
    bash scripts/run_lspr24_rwkv_screen.sh prepare-cache "$manifest" "$cache_dir"
  run_logged_stage real-cache-forward \
    bash scripts/run_lspr24_rwkv_screen.sh probe-cache "$manifest" "$cache_dir" cuda
  run_logged_stage gpu-gate \
    bash scripts/run_lspr24_rwkv_screen.sh gpu-gate "$manifest" "$cache_dir" "$gate_output"

  local batch_size
  batch_size=$(uv run --no-sync python -c \
    'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["selected_batch_size"])' \
    "$gate_output")
  if [[ "$batch_size" != '512' && "$batch_size" != '256' ]]; then
    printf '%s\n' "阻断：显存门禁返回非法统一批量：$batch_size" >&2
    return 78
  fi
  printf '%s\n' "$batch_size" >"$launcher_dir/selected-batch-size.txt"
  printf '%s\n' "统一批量门禁通过：batch_size=$batch_size；开始并行四变体。"

  declare -A pids=()
  local variant
  for variant in "${variants[@]}"; do
    run_variant "$variant" "$batch_size" &
    pids["$variant"]=$!
  done

  local overall_code=0
  set +e
  for variant in "${variants[@]}"; do
    wait "${pids[$variant]}"
    local wait_code=$?
    printf '%s\n' "$wait_code" >"$launcher_dir/${variant}-wait-exit-code.txt"
    if [[ "$wait_code" -ne 0 ]]; then
      overall_code=1
    fi
  done
  set -e

  date -u +'%Y-%m-%dT%H:%M:%SZ' >"$launcher_dir/finished_at.txt"
  if [[ "$overall_code" -eq 0 ]]; then
    write_controller_summary "$batch_size" finished
    write_status finished
    return 0
  fi
  write_controller_summary "$batch_size" failed
  write_status failed
  return 1
}

worker_entry() {
  trap 'write_status interrupted' INT TERM HUP
  set +e
  worker_main 2>&1 | tee "$launcher_dir/controller.log"
  local pipeline_status=("${PIPESTATUS[@]}")
  set -e
  local controller_code=${pipeline_status[0]}
  local tee_code=${pipeline_status[1]}
  printf '%s\n' "$controller_code" >"$launcher_dir/controller-exit-code.txt"
  printf '%s\n' "$tee_code" >"$launcher_dir/controller-tee-exit-code.txt"
  if [[ "$controller_code" -ne 0 || "$tee_code" -ne 0 ]]; then
    write_status failed
  fi
  if [[ "$controller_code" -ne 0 ]]; then
    return "$controller_code"
  fi
  return "$tee_code"
}

if [[ ${1:-} == '--worker' ]]; then
  worker_entry
  exit $?
fi

if [[ ! -s "$manifest" ]]; then
  printf '%s\n' "阻断：数据清单不存在或为空：$manifest" >&2
  exit 66
elif [[ ! -f scripts/run_lspr24_rwkv_screen.sh ]]; then
  printf '%s\n' '阻断：RWKV 快速消融包装器不存在。' >&2
  exit 67
elif [[ ! -f src/flow_probe/lspr24_rwkv_screen.py || ! -f src/flow_probe/lspr24_rwkv_screen_models.py ]]; then
  printf '%s\n' '阻断：RWKV 快速消融 Python 入口或模型组件不存在。' >&2
  exit 68
elif [[ -e "$launcher_dir" || -e "$output_root" ]]; then
  printf '%s\n' '阻断：唯一启动目录或输出目录已存在，拒绝覆盖或重复启动。' >&2
  exit 73
elif ! command -v screen >/dev/null 2>&1; then
  printf '%s\n' '阻断：远程环境缺少 screen。' >&2
  exit 69
elif ! command -v rg >/dev/null 2>&1; then
  printf '%s\n' '阻断：远程环境缺少 rg。' >&2
  exit 69
elif screen -ls 2>/dev/null | rg -q "[.]${session_name}[[:space:]]"; then
  printf '%s\n' "阻断：同名 screen 会话已存在：$session_name" >&2
  exit 73
fi

mkdir -p "$launcher_dir"
printf '%s\n' "$session_name" >"$launcher_dir/screen-session.txt"
printf '%s\n' "$script_path --worker" >"$launcher_dir/command.txt"
sha256sum \
  "$manifest" \
  src/flow_probe/lspr24_rwkv_screen_models.py \
  src/flow_probe/lspr24_rwkv_screen.py \
  scripts/run_lspr24_rwkv_screen.sh \
  "$script_path" >"$launcher_dir/input-sha256.txt"
write_status prepared
screen -dmS "$session_name" bash "$script_path" --worker
printf '%s\n' "LSPR24_RWKV_SCREEN_STARTED session=$session_name launcher=$launcher_dir"
