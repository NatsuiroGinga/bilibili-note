#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

mode=${1:-}
config_path=${2:-}
resume_output=${3:-}
script_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
project_root=$(cd "$(dirname "$script_path")/.." && pwd)
cd "$project_root"

MAX_SWANLAB_ATTEMPTS=2
LAST_COMMAND_STATUS=0
LAST_TEE_STATUS=0

usage() {
  printf '用法：\n' >&2
  printf '  bash %s formal configs/e2_hard_domain_seed42.yaml\n' "${BASH_SOURCE[0]}" >&2
  printf '  bash %s resume configs/e2_hard_domain_seed42.yaml runs/e2-hard-domain/<已有运行目录>\n' \
    "${BASH_SOURCE[0]}" >&2
}

write_status() {
  local directory=$1
  local status=$2
  local temporary="$directory/status.txt.partial.$$"
  printf '%s\n' "$status" >"$temporary"
  mv "$temporary" "$directory/status.txt"
}

require_command() {
  local command_name=$1
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf '缺少正式 E2 必需命令：%s\n' "$command_name" >&2
    return 1
  fi
}

validate_arguments() {
  case "$config_path" in
    configs/e2_hard_domain_seed42.yaml | configs/e2_hard_domain_seed43.yaml | configs/e2_hard_domain_seed44.yaml) ;;
    *)
      printf '不允许的 E2 正式配置：%s\n' "$config_path" >&2
      return 2
      ;;
  esac
  case "$mode" in
    formal)
      if [[ $# -ne 2 ]]; then
        usage
        return 2
      fi
      ;;
    resume)
      if [[ $# -ne 3 || -z "$resume_output" ]]; then
        usage
        return 2
      fi
      case "$resume_output" in
        runs/e2-hard-domain/*) ;;
        *)
          printf '恢复目录必须位于 runs/e2-hard-domain/：%s\n' "$resume_output" >&2
          return 2
          ;;
      esac
      case "$resume_output" in
        ../* | */../* | */..)
          printf '恢复目录不得包含上级路径：%s\n' "$resume_output" >&2
          return 2
          ;;
      esac
      ;;
    *)
      usage
      return 2
      ;;
  esac
}

write_capabilities() {
  local target=$1
  {
    printf 'rg=%s\n' "$(command -v rg)"
    printf 'uv=%s\n' "$(command -v uv)"
    printf 'screen=%s\n' "$(command -v screen)"
    printf 'sha256sum=%s\n' "$(command -v sha256sum)"
    uname -a
    df -h "$project_root"
    if command -v nvidia-smi >/dev/null 2>&1; then
      nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    else
      printf '%s\n' 'gpu=unavailable'
    fi
  } >"$target"
}

capture_legacy_swanlab_evidence() {
  local launcher_dir=$1
  local output_dir=$2
  local formal_launcher="runs/launchers/e2-hard-domain-${output_dir##*/}"
  local binding_path="$formal_launcher/binding.txt"
  local log_path="$formal_launcher/launcher.log"
  local receipt="$launcher_dir/legacy-swanlab-evidence.json"
  local binding_sha256
  local log_sha256

  if [[ ! -e "$binding_path" && ! -e "$log_path" ]]; then
    return 0
  fi
  if [[ -L "$formal_launcher" || -L "$binding_path" || -L "$log_path" || ! -f "$binding_path" || ! -f "$log_path" ]]; then
    printf '原 formal launcher 证据缺失或不是普通文件：%s\n' "$formal_launcher" >&2
    return 1
  fi
  binding_sha256=$(sha256sum -- "$binding_path")
  binding_sha256=${binding_sha256%% *}
  log_sha256=$(sha256sum -- "$log_path")
  log_sha256=${log_sha256%% *}
  jq -n \
    --arg schema_version flow_probe_e2_legacy_swanlab_evidence_v1 \
    --arg status captured \
    --arg output_dir "$output_dir" \
    --arg formal_launcher "$formal_launcher" \
    --arg binding_path "$binding_path" \
    --arg binding_sha256 "$binding_sha256" \
    --arg launcher_log_path "$log_path" \
    --arg launcher_log_sha256 "$log_sha256" \
    '{schema_version:$schema_version,status:$status,output_dir:$output_dir,formal_launcher:$formal_launcher,binding_path:$binding_path,binding_sha256:$binding_sha256,launcher_log_path:$launcher_log_path,launcher_log_sha256:$launcher_log_sha256}' \
    >"$receipt.partial.$$"
  mv "$receipt.partial.$$" "$receipt"
  printf '%s\n' "$receipt"
}

run_swanlab_gate() {
  local launcher_dir=$1
  local variant=$2
  local attempt=$3
  local gate_receipt=$4
  local variant_slug=${variant,,}
  local ping_log="$launcher_dir/${variant_slug}-attempt-${attempt}-swanlab-ping.log"
  local verify_log="$launcher_dir/${variant_slug}-attempt-${attempt}-swanlab-verify.log"
  local checked_at
  local ping_exit
  local verify_exit
  local gate_status=passed

  set +e
  uv run --no-sync swanlab ping >"$ping_log" 2>&1
  ping_exit=$?
  uv run --no-sync swanlab verify >"$verify_log" 2>&1
  verify_exit=$?
  set -e
  checked_at=$(date +%s)
  {
    printf '=== %s 尝试 %s：SwanLab ping ===\n' "$variant" "$attempt"
    cat "$ping_log"
    printf '=== %s 尝试 %s：SwanLab verify ===\n' "$variant" "$attempt"
    cat "$verify_log"
  } >>"$launcher_dir/launcher.log"
  if ((ping_exit != 0 || verify_exit != 0)); then
    gate_status=failed
  fi
  jq -n \
    --arg schema_version flow_probe_e2_swanlab_gate_v1 \
    --arg status "$gate_status" \
    --arg variant "$variant" \
    --argjson attempt "$attempt" \
    --argjson ping_exit "$ping_exit" \
    --argjson verify_exit "$verify_exit" \
    --argjson checked_at "$checked_at" \
    '{schema_version:$schema_version,status:$status,variant:$variant,attempt:$attempt,ping_exit:$ping_exit,verify_exit:$verify_exit,checked_at:$checked_at}' \
    >"$gate_receipt.partial.$$"
  mv "$gate_receipt.partial.$$" "$gate_receipt"
  if [[ "$gate_status" != passed ]]; then
    return 1
  fi
}

run_variant_attempt() {
  local launcher_dir=$1
  local output_dir=$2
  local variant=$3
  local attempt=$4
  local gate_receipt=$5
  local legacy_failure_evidence=${6:-}
  local variant_slug=${variant,,}
  local attempt_log="$launcher_dir/${variant_slug}-attempt-${attempt}.log"
  local attempt_receipt="$launcher_dir/${variant_slug}-attempt-${attempt}-exit.json"
  local command=(
    uv run --no-sync python -m flow_probe.e2_hard_domain_train
    --config "$config_path"
    --output-dir "$output_dir"
    --variant "$variant"
    --attempt "$attempt"
    --swanlab-gate-receipt "$gate_receipt"
  )
  if [[ -e "$output_dir" || -L "$output_dir" ]]; then
    command+=(--resume)
  fi
  if [[ -n "$legacy_failure_evidence" ]]; then
    command+=(--legacy-swanlab-evidence-receipt "$legacy_failure_evidence")
  fi

  set +e
  "${command[@]}" 2>&1 | tee -a "$launcher_dir/launcher.log" "$attempt_log"
  local pipeline_status=("${PIPESTATUS[@]}")
  set -e
  LAST_COMMAND_STATUS=${pipeline_status[0]}
  LAST_TEE_STATUS=${pipeline_status[1]}
  jq -n \
    --arg variant "$variant" \
    --argjson attempt "$attempt" \
    --argjson command_exit "$LAST_COMMAND_STATUS" \
    --argjson tee_exit "$LAST_TEE_STATUS" \
    --arg log "$attempt_log" \
    '{variant:$variant,attempt:$attempt,command_exit:$command_exit,tee_exit:$tee_exit,log:$log}' \
    >"$attempt_receipt.partial.$$"
  mv "$attempt_receipt.partial.$$" "$attempt_receipt"
  if ((LAST_COMMAND_STATUS != 0)); then
    return "$LAST_COMMAND_STATUS"
  fi
  if ((LAST_TEE_STATUS != 0)); then
    return "$LAST_TEE_STATUS"
  fi
}

write_worker_failure() {
  local launcher_dir=$1
  local output_dir=$2
  local variant=$3
  local attempt=$4
  local failure_code=$5
  printf '%s\n' "$LAST_COMMAND_STATUS" >"$launcher_dir/command-exit-code.txt"
  printf '%s\n' "$LAST_TEE_STATUS" >"$launcher_dir/tee-exit-code.txt"
  write_status "$launcher_dir" failed
  jq -n \
    --arg output_dir "$output_dir" \
    --arg variant "$variant" \
    --argjson attempt "$attempt" \
    --arg failure_code "$failure_code" \
    --argjson command_exit "$LAST_COMMAND_STATUS" \
    --argjson tee_exit "$LAST_TEE_STATUS" \
    '{status:"failed",output_dir:$output_dir,variant:$variant,attempt:$attempt,failure_code:$failure_code,command_exit:$command_exit,tee_exit:$tee_exit}' \
    >"$launcher_dir/failure-receipt.json.partial.$$"
  mv "$launcher_dir/failure-receipt.json.partial.$$" "$launcher_dir/failure-receipt.json"
}

validate_completed_output() {
  local run_mode=$1
  local output_dir=$2
  local variant

  jq -e '.status == "finished" and (.finished_variants | length) == 4' \
    "$output_dir/run_state.json" >/dev/null || return 1
  jq -e '.status == "finished" and (.variants | length) == 4' \
    "$output_dir/summary.json" >/dev/null || return 1
  for variant in e2-a e2-s e2-p e2-x; do
    test -s "$output_dir/variants/$variant/summary.json" || return 1
    test -s "$output_dir/variants/$variant/metrics.jsonl" || return 1
    test -s "$output_dir/variants/$variant/predictions/target_c.jsonl" || return 1
    test -s "$output_dir/variants/$variant/predictions/source_calibration.jsonl" || return 1
    if [[ "$run_mode" == formal || "$variant" != e2-a ]]; then
      test -s "$output_dir/variants/$variant/swanlab-gate.json" || return 1
    fi
    # 运行目录受 Git 忽略，且 swanlog 自带 `*` 规则；枚举必须关闭忽略规则。
    rg --files --hidden --no-ignore "$output_dir/variants/$variant/checkpoints" \
      | rg 'checkpoint-[0-9]+\.pt$' >/dev/null || return 1
    rg --files --hidden --no-ignore "$output_dir/variants/$variant/swanlog" \
      | rg '.' >/dev/null || return 1
  done
}

run_worker() {
  local launcher_dir=${E2_HARD_DOMAIN_LAUNCHER_DIR:?缺少 E2 启动证据目录}
  local output_dir=${E2_HARD_DOMAIN_OUTPUT_DIR:?缺少 E2 唯一运行目录}
  local run_mode=${E2_HARD_DOMAIN_RUN_MODE:?缺少 E2 运行模式}
  local variants=(E2-A E2-S E2-P E2-X)
  local variant
  local attempt
  local gate_receipt
  local failure_code
  local variant_finished
  local legacy_failure_evidence=

  for command_name in rg uv screen sha256sum jq tee; do
    require_command "$command_name"
  done
  for required_path in \
    "$config_path" \
    src/flow_probe/e2_hard_domain_data.py \
    src/flow_probe/e2_hard_domain_metrics.py \
    src/flow_probe/e2_shared_pinn.py \
    src/flow_probe/e2_hard_domain_train.py \
    scripts/run_e2_hard_domain.sh \
    pyproject.toml; do
    if [[ ! -f "$required_path" ]]; then
      printf '缺少 E2 正式输入：%s\n' "$required_path" >&2
      return 1
    fi
  done
  if [[ "$run_mode" == formal && ( -e "$output_dir" || -L "$output_dir" ) ]]; then
    printf 'E2 唯一运行目录已存在，拒绝覆盖：%s\n' "$output_dir" >&2
    return 1
  fi
  if [[ "$run_mode" == resume && ( -L "$output_dir" || ! -d "$output_dir" ) ]]; then
    printf 'E2 恢复目录不存在或不是普通目录：%s\n' "$output_dir" >&2
    return 1
  fi

  : >"$launcher_dir/launcher.log"
  write_capabilities "$launcher_dir/capabilities.txt"
  sha256sum \
    "$config_path" \
    src/flow_probe/e2_hard_domain_data.py \
    src/flow_probe/e2_hard_domain_metrics.py \
    src/flow_probe/e2_shared_pinn.py \
    src/flow_probe/e2_hard_domain_train.py \
    scripts/run_e2_hard_domain.sh \
    pyproject.toml >"$launcher_dir/code-config.sha256"
  write_status "$launcher_dir" running
  if [[ "$run_mode" == resume ]]; then
    legacy_failure_evidence=$(capture_legacy_swanlab_evidence "$launcher_dir" "$output_dir")
  fi

  for variant in "${variants[@]}"; do
    variant_finished=0
    for ((attempt = 1; attempt <= MAX_SWANLAB_ATTEMPTS; attempt++)); do
      gate_receipt="$launcher_dir/${variant,,}-attempt-${attempt}-swanlab-gate.json"
      if run_swanlab_gate "$launcher_dir" "$variant" "$attempt" "$gate_receipt"; then
        :
      else
        LAST_COMMAND_STATUS=1
        LAST_TEE_STATUS=0
        write_worker_failure "$launcher_dir" "$output_dir" "$variant" "$attempt" swanlab_gate_failed
        return 1
      fi

      if run_variant_attempt "$launcher_dir" "$output_dir" "$variant" "$attempt" "$gate_receipt" "$legacy_failure_evidence"; then
        variant_finished=1
        break
      fi
      failure_code=unknown_failure
      if [[ -s "$launcher_dir/${variant,,}-attempt-${attempt}-failure.json" ]]; then
        failure_code=$(jq -r '.code // "unknown_failure"' "$launcher_dir/${variant,,}-attempt-${attempt}-failure.json")
      elif [[ -s "$output_dir/failure.json" ]]; then
        failure_code=$(jq -r '.code // "unknown_failure"' "$output_dir/failure.json")
      fi
      if [[ "$failure_code" == "swanlab_init_unauthorized" && "$LAST_TEE_STATUS" -eq 0 && "$attempt" -lt "$MAX_SWANLAB_ATTEMPTS" ]]; then
        printf 'SwanLab 初始化返回 HTTP 401；保留失败证据并在新进程中执行唯一一次重试：%s\n' \
          "$variant" >>"$launcher_dir/launcher.log"
        continue
      fi
      write_worker_failure "$launcher_dir" "$output_dir" "$variant" "$attempt" "$failure_code"
      return 1
    done
    if ((variant_finished != 1)); then
      write_worker_failure "$launcher_dir" "$output_dir" "$variant" "$MAX_SWANLAB_ATTEMPTS" exhausted
      return 1
    fi
  done

  if ! validate_completed_output "$run_mode" "$output_dir"; then
    LAST_COMMAND_STATUS=1
    LAST_TEE_STATUS=0
    write_worker_failure "$launcher_dir" "$output_dir" E2-X "$MAX_SWANLAB_ATTEMPTS" output_validation_failed
    return 1
  fi
  sha256sum \
    "$output_dir/run_state.json" \
    "$output_dir/input_binding.json" \
    "$output_dir/physics_binding.json" \
    "$output_dir/summary.json" \
    "$output_dir/artifact_manifest.json" >"$launcher_dir/output.sha256"
  printf '0\n' >"$launcher_dir/command-exit-code.txt"
  printf '0\n' >"$launcher_dir/tee-exit-code.txt"
  write_status "$launcher_dir" finished
}

launch_formal_or_resume() {
  for command_name in screen rg uv sha256sum jq tee; do
    require_command "$command_name"
  done
  if [[ ! -f "$config_path" ]]; then
    printf 'E2 配置不存在：%s\n' "$config_path" >&2
    return 1
  fi
  local config_stem=${config_path##*/}
  config_stem=${config_stem%.yaml}
  local run_id
  local output_dir
  local launcher_dir
  local screen_name
  local worker_args=("$mode" "$config_path")
  run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
  if [[ "$mode" == formal ]]; then
    output_dir="runs/e2-hard-domain/${config_stem}-${run_id}"
    launcher_dir="runs/launchers/e2-hard-domain-${config_stem}-${run_id}"
    screen_name="e2-${config_stem#e2_hard_domain_}-${run_id}"
    if [[ -e "$output_dir" || -L "$output_dir" ]]; then
      printf '%s\n' 'E2 运行身份冲突，拒绝复用目录。' >&2
      return 1
    fi
    mkdir -p "$(dirname "$output_dir")"
  else
    output_dir=$resume_output
    worker_args+=("$resume_output")
    launcher_dir="runs/launchers/e2-hard-domain-resume-${config_stem}-${run_id}"
    screen_name="e2-resume-${config_stem#e2_hard_domain_}-${run_id}"
    if [[ -L "$output_dir" || ! -d "$output_dir" ]]; then
      printf 'E2 恢复目录不存在或不是普通目录：%s\n' "$output_dir" >&2
      return 1
    fi
  fi
  if [[ -e "$launcher_dir" || -L "$launcher_dir" ]]; then
    printf 'E2 启动器身份冲突，拒绝复用目录：%s\n' "$launcher_dir" >&2
    return 1
  fi
  mkdir -p "$launcher_dir"
  write_status "$launcher_dir" prepared
  {
    printf 'mode=%s\n' "$mode"
    printf 'config=%s\n' "$config_path"
    printf 'output=%s\n' "$output_dir"
    printf 'screen=%s\n' "$screen_name"
    printf 'run_id=%s\n' "$run_id"
  } >"$launcher_dir/binding.txt"
  screen -L -Logfile "$launcher_dir/screen.log" -DmS "$screen_name" \
    env E2_HARD_DOMAIN_FORMAL_WORKER=1 \
    E2_HARD_DOMAIN_RUN_MODE="$mode" \
    E2_HARD_DOMAIN_LAUNCHER_DIR="$launcher_dir" \
    E2_HARD_DOMAIN_OUTPUT_DIR="$output_dir" \
    bash "$script_path" "${worker_args[@]}"
  sleep 2
  if screen -S "$screen_name" -Q select . >/dev/null 2>&1; then
    write_status "$launcher_dir" running
    printf 'E2_SCREEN=%s\nE2_OUTPUT=%s\nE2_LAUNCHER=%s\n' \
      "$screen_name" "$output_dir" "$launcher_dir"
    return 0
  fi
  if [[ "$(cat "$launcher_dir/status.txt")" == finished ]]; then
    printf 'E2_OUTPUT=%s\nE2_LAUNCHER=%s\n' "$output_dir" "$launcher_dir"
    return 0
  fi
  write_status "$launcher_dir" failed
  printf 'E2 正式入口快速失败，证据目录：%s\n' "$launcher_dir" >&2
  return 1
}

validate_arguments "$@"
if [[ "${E2_HARD_DOMAIN_FORMAL_WORKER:-0}" == 1 ]]; then
  run_worker
else
  launch_formal_or_resume
fi
