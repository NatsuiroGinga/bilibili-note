#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

mode=${1:-launch}
launcher_dir_arg=${2:-}
script_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
project_root=$(cd "$(dirname "$script_path")/.." && pwd)
output_root=runs/r2-transformer-sidecar-probe/distilbert-v0
launcher_root=runs/launchers
screen_prefix=r2-distilbert-sidecar
minimum_launch_free_bytes=$((7 * 1024 * 1024 * 1024))

cd "$project_root"

usage() {
  printf '用法：bash %s launch|worker [启动证据目录]\n' "${BASH_SOURCE[0]}" >&2
}

require_command() {
  local command_name=$1
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf '服务器缺少必需命令：%s\n' "$command_name" >&2
    return 1
  fi
}

write_state() {
  local launcher_dir=$1
  local status=$2
  local current_seed=${3:-}
  local exit_code=${4:-}
  local message=${5:-}
  local state_path="$launcher_dir/state.json"
  local temporary="${state_path}.tmp.$$"
  local screen_name
  local run_id
  local current_seed_json=null
  local exit_code_json=null

  screen_name=$(jq -er '.screen_name' "$launcher_dir/launcher-config.json")
  run_id=$(jq -er '.run_id' "$launcher_dir/launcher-config.json")
  if [[ -n "$current_seed" ]]; then
    current_seed_json=$current_seed
  fi
  if [[ -n "$exit_code" ]]; then
    exit_code_json=$exit_code
  fi
  jq -n \
    --arg status "$status" \
    --arg run_id "$run_id" \
    --arg screen_name "$screen_name" \
    --arg output_root "$output_root" \
    --arg launcher_dir "$launcher_dir" \
    --arg message "$message" \
    --arg updated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --argjson current_seed "$current_seed_json" \
    --argjson exit_code "$exit_code_json" \
    '{schema_version: 1, status: $status, run_id: $run_id, screen_name: $screen_name, output_root: $output_root, launcher_dir: $launcher_dir, current_seed: $current_seed, exit_code: $exit_code, message: $message, updated_at: $updated_at}' \
    >"$temporary"
  mv "$temporary" "$state_path"
}

log_event() {
  local launcher_dir=$1
  shift
  local message=$*
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$message" >>"$launcher_dir/launcher.log"
  printf '%s\n' "$message"
}

required_paths() {
  printf '%s\n' \
    scripts/run_r2_distilbert_sidecar_probe.sh \
    src/flow_probe/r2_distilbert_sidecar_probe.py \
    src/flow_probe/r2_physics_sidecar_signal.py \
    src/flow_probe/r2_protocol_contract.py \
    src/flow_probe/shared_b0_view.py \
    src/flow_probe/shared_b0_distilbert_baseline.py \
    src/flow_probe/tracking.py \
    configs/r2_distilbert_sidecar_probe_seed42.yaml \
    configs/r2_distilbert_sidecar_probe_seed43.yaml \
    configs/r2_distilbert_sidecar_probe_seed44.yaml \
    runs/r2-physics-sidecar-pilot/inputs/input-summary.json \
    runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-detection-view.parquet \
    runs/r2-physics-sidecar-pilot/inputs/tqhc2/tqhc2-pilot-sidecar.parquet \
    /root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased/config.json \
    /root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased/model.safetensors
}

write_capabilities() {
  local launcher_dir=$1
  {
    printf 'rg_path=%s\n' "$(command -v rg)"
    rg --version
    printf 'uv_path=%s\n' "$(command -v uv)"
    uv --version
    printf 'jq_path=%s\n' "$(command -v jq)"
    jq --version
    printf 'sha256sum_path=%s\n' "$(command -v sha256sum)"
    sha256sum --version
    printf 'screen_path=%s\n' "$(command -v screen)"
    screen --version
    if command -v fd >/dev/null 2>&1; then
      printf 'fd_path=%s\n' "$(command -v fd)"
      fd --version
    elif command -v fdfind >/dev/null 2>&1; then
      printf 'fd_path=%s\n' "$(command -v fdfind)"
      fdfind --version
    else
      printf '%s\n' 'fd=unavailable'
    fi
    printf 'nvidia_smi_path=%s\n' "$(command -v nvidia-smi)"
    nvidia-smi --query-gpu=index,name,memory.total,memory.used,utilization.gpu \
      --format=csv,noheader,nounits
    uname -a
    df -PB1 "$project_root"
  } >"$launcher_dir/capabilities.txt"
  test -s "$launcher_dir/capabilities.txt"
}

formal_preflight() {
  local launcher_dir=$1
  local required_path
  local free_bytes

  for command_name in rg uv jq sha256sum screen nvidia-smi; do
    require_command "$command_name"
  done
  while IFS= read -r required_path; do
    if [[ ! -f "$required_path" || -L "$required_path" ]]; then
      printf '缺少正式探针输入或路径不是普通文件：%s\n' "$required_path" >&2
      return 1
    fi
  done < <(required_paths)
  free_bytes=$(df -PB1 "$project_root" | awk 'NR == 2 {print $4}')
  if ((free_bytes < minimum_launch_free_bytes)); then
    printf '正式入口磁盘门禁失败：至少需要 7 GiB，当前可用 %s 字节。\n' "$free_bytes" >&2
    return 1
  fi
  write_capabilities "$launcher_dir"
  required_paths | while IFS= read -r required_path; do
    sha256sum "$required_path"
  done >"$launcher_dir/bindings.sha256"
  test -s "$launcher_dir/bindings.sha256"
}

run_worker() {
  local launcher_dir=$1
  local current_seed=''
  local global_exit_path="$launcher_dir/exit-code.txt"

  on_error() {
    local status=$?
    trap - ERR
    printf '%s\n' "$status" >"$global_exit_path"
    write_state "$launcher_dir" failed "$current_seed" "$status" '串行启动器发生未处理错误'
    exit "$status"
  }
  on_interrupt() {
    local status=$1
    trap - ERR INT TERM
    printf '%s\n' "$status" >"$global_exit_path"
    write_state "$launcher_dir" interrupted "$current_seed" "$status" '串行启动器收到中断信号'
    exit "$status"
  }
  trap on_error ERR
  trap 'on_interrupt 130' INT
  trap 'on_interrupt 143' TERM

  : >"$launcher_dir/launcher.log"
  write_state "$launcher_dir" prepared '' '' '正在执行正式启动阶段运行时断言'
  formal_preflight "$launcher_dir"

  for current_seed in 42 43 44; do
    local config_path="configs/r2_distilbert_sidecar_probe_seed${current_seed}.yaml"
    local seed_log="$launcher_dir/seed-${current_seed}.log"
    local seed_exit_json="$launcher_dir/seed-${current_seed}-exit.json"
    local python_status
    local tee_status
    local status
    local pipeline_status

    write_state "$launcher_dir" running "$current_seed" '' "正在运行种子 ${current_seed}"
    log_event "$launcher_dir" "启动种子 ${current_seed}：四组严格串行，每组固定 192 个优化步。"
    : >"$seed_log"
    set +e
    uv run --frozen python -m flow_probe.r2_distilbert_sidecar_probe \
      --config "$config_path" 2>&1 | tee "$seed_log"
    pipeline_status=("${PIPESTATUS[@]}")
    set -e
    python_status=${pipeline_status[0]}
    tee_status=${pipeline_status[1]}
    status=$python_status
    if [[ "$tee_status" -ne 0 ]]; then
      status=$tee_status
    fi
    if [[ ! -s "$seed_log" ]]; then
      printf '%s\n' '正式种子日志为空。' >>"$seed_log"
      if [[ "$status" -eq 0 ]]; then
        status=1
      fi
    fi
    jq -n \
      --argjson seed "$current_seed" \
      --argjson python_exit_code "$python_status" \
      --argjson tee_exit_code "$tee_status" \
      --argjson effective_exit_code "$status" \
      --arg finished_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '{seed: $seed, python_exit_code: $python_exit_code, tee_exit_code: $tee_exit_code, effective_exit_code: $effective_exit_code, finished_at: $finished_at}' \
      >"${seed_exit_json}.tmp.$$"
    mv "${seed_exit_json}.tmp.$$" "$seed_exit_json"
    if [[ "$status" -ne 0 ]]; then
      printf '%s\n' "$status" >"$global_exit_path"
      write_state "$launcher_dir" failed "$current_seed" "$status" "种子 ${current_seed} 失败"
      log_event "$launcher_dir" "种子 ${current_seed} 失败，退出码 ${status}；停止后续种子。"
      exit "$status"
    fi
    log_event "$launcher_dir" "种子 ${current_seed} 已完成并通过正式入口收尾。"
  done

  printf '%s\n' 0 >"$global_exit_path"
  write_state "$launcher_dir" finished 44 0 '种子 42、43、44 全部完成'
  log_event "$launcher_dir" '三个种子已全部完成。'
}

launch_worker() {
  require_command jq
  require_command screen
  require_command rg
  mkdir -p "$launcher_root"
  if screen -ls 2>/dev/null | rg -q "[.]${screen_prefix}-"; then
    printf '%s\n' '已有 R2 DistilBERT 正式探针 screen 会话，拒绝重复启动。' >&2
    return 1
  fi

  local run_id
  local screen_name
  local launcher_dir
  run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
  screen_name="${screen_prefix}-${run_id}"
  launcher_dir="${launcher_root}/${screen_name}"
  if [[ -e "$launcher_dir" || -L "$launcher_dir" ]]; then
    printf '启动证据目录已存在，拒绝覆盖：%s\n' "$launcher_dir" >&2
    return 1
  fi
  mkdir "$launcher_dir"
  jq -n \
    --arg run_id "$run_id" \
    --arg screen_name "$screen_name" \
    --arg launcher_dir "$launcher_dir" \
    --arg output_root "$output_root" \
    --arg script_path "$script_path" \
    --arg created_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{schema_version: 1, run_id: $run_id, screen_name: $screen_name, launcher_dir: $launcher_dir, output_root: $output_root, script_path: $script_path, created_at: $created_at}' \
    >"$launcher_dir/launcher-config.json"
  write_state "$launcher_dir" prepared '' '' '已创建唯一启动身份，等待 screen 工作者'
  screen -L -Logfile "$launcher_dir/screen.log" -DmS "$screen_name" \
    bash "$script_path" worker "$launcher_dir"
  sleep 3
  if screen -S "$screen_name" -Q select . >/dev/null 2>&1; then
    printf 'FORMAL_SCREEN=%s\nFORMAL_OUTPUT=%s\nFORMAL_LAUNCHER=%s\n' \
      "$screen_name" "$output_root" "$launcher_dir"
    return 0
  fi
  if [[ -s "$launcher_dir/exit-code.txt" ]]; then
    printf '正式探针在启动确认前退出，退出码=%s，证据=%s\n' \
      "$(<"$launcher_dir/exit-code.txt")" "$launcher_dir" >&2
    return 1
  fi
  printf '正式探针 screen 未保持运行且没有退出码：%s\n' "$launcher_dir" >&2
  return 1
}

case "$mode" in
  launch)
    launch_worker
    ;;
  worker)
    if [[ -z "$launcher_dir_arg" || ! -d "$launcher_dir_arg" ]]; then
      printf '%s\n' 'worker 模式缺少有效启动证据目录。' >&2
      exit 2
    fi
    run_worker "$launcher_dir_arg"
    ;;
  *)
    usage
    exit 2
    ;;
esac
