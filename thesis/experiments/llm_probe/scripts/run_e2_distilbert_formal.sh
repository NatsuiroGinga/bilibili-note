#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

mode=${1:-}
argument=${2:-}
script_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
project_root=$(cd "$(dirname "$script_path")/.." && pwd)
protocol_dir="$project_root/runs/data-prepared/tqh-c2-v120-e1-dev-seed42-v1-20260806T092613Z/protocol"
model_source=/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased
cd "$project_root"

usage() {
  printf '用法：bash %s formal <基础模型绑定SHA-256>\n' "${BASH_SOURCE[0]}" >&2
  printf '恢复检查：bash %s recover <启动证据目录>\n' "${BASH_SOURCE[0]}" >&2
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
    printf '缺少 E2 DistilBERT 正式运行命令：%s\n' "$command_name" >&2
    return 1
  fi
}

validate_binding() {
  local binding=$1
  if [[ ! "$binding" =~ ^[0-9a-f]{64}$ ]]; then
    printf '%s\n' '基础模型绑定必须是 64 位小写 SHA-256。' >&2
    return 2
  fi
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
    nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader
    uv run --no-sync python -c 'import swanlab, torch, transformers; print(f"torch={torch.__version__} transformers={transformers.__version__} swanlab={swanlab.__version__}")'
  } >"$target"
}

write_input_hashes() {
  local target=$1
  sha256sum \
    scripts/e2_distilbert_formal_driver.py \
    scripts/run_e2_distilbert_formal.sh \
    src/flow_probe/e2_distilbert.py \
    src/flow_probe/e2_hard_domain_baselines.py \
    src/flow_probe/e2_hard_domain_data.py \
    src/flow_probe/e2_hard_domain_metrics.py \
    src/flow_probe/tracking.py \
    pyproject.toml >"$target"
  while IFS= read -r path; do
    sha256sum "$path"
  done < <(rg --files "$protocol_dir" | sort) >>"$target"
  while IFS= read -r path; do
    sha256sum "$path"
  done < <(rg --files "$model_source" | sort) >>"$target"
  for path in \
    "${model_source}.manifest.json" \
    "${model_source}.checksums.sha256"; do
    if [[ -f "$path" ]]; then
      sha256sum "$path" >>"$target"
    fi
  done
}

run_worker() {
  local model_binding=$1
  local launcher_dir=${E2_DISTILBERT_LAUNCHER_DIR:?缺少启动证据目录}
  local output_dir=${E2_DISTILBERT_OUTPUT_DIR:?缺少唯一运行目录}
  local run_name=${E2_DISTILBERT_RUN_NAME:?缺少 SwanLab 运行名}
  local command_name
  for command_name in rg uv screen sha256sum jq tee nvidia-smi; do
    require_command "$command_name"
  done
  validate_binding "$model_binding"
  for path in \
    "$protocol_dir" \
    "$model_source" \
    scripts/e2_distilbert_formal_driver.py \
    scripts/run_e2_distilbert_formal.sh \
    src/flow_probe/e2_distilbert.py \
    src/flow_probe/e2_hard_domain_baselines.py; do
    if [[ ! -e "$path" ]]; then
      printf '缺少 E2 DistilBERT 正式输入：%s\n' "$path" >&2
      write_status "$launcher_dir" failed
      return 1
    fi
  done
  if [[ -e "$output_dir" || -L "$output_dir" ]]; then
    printf '唯一运行目录已存在，拒绝覆盖：%s\n' "$output_dir" >&2
    write_status "$launcher_dir" failed
    return 1
  fi

  write_capabilities "$launcher_dir/capabilities.txt"
  printf '%s\n' "$model_binding" >"$launcher_dir/model-binding.sha256"
  write_input_hashes "$launcher_dir/input.sha256"
  write_status "$launcher_dir" running
  trap 'write_status "$launcher_dir" interrupted; exit 130' INT TERM HUP

  set +e
  uv run --no-sync python scripts/e2_distilbert_formal_driver.py \
    --protocol-dir "$protocol_dir" \
    --output-dir "$output_dir" \
    --model-source "$model_source" \
    --model-binding-sha256 "$model_binding" \
    --run-name "$run_name" 2>&1 | tee "$launcher_dir/launcher.log"
  local pipeline_status=("${PIPESTATUS[@]}")
  set -e
  trap - INT TERM HUP
  local command_status=${pipeline_status[0]}
  local tee_status=${pipeline_status[1]}
  printf '%s\n' "$command_status" >"$launcher_dir/command-exit-code.txt"
  printf '%s\n' "$tee_status" >"$launcher_dir/tee-exit-code.txt"
  if ((command_status != 0 || tee_status != 0)); then
    write_status "$launcher_dir" failed
    if ((command_status != 0)); then
      return "$command_status"
    fi
    return "$tee_status"
  fi

  jq -e '.status == "finished" and .panel == "abd_to_c" and .seed == 42' \
    "$output_dir/run_state.json" >/dev/null
  jq -e '.status == "finished" and .tracking_mode == "online"' \
    "$output_dir/artifact_manifest.json" >/dev/null
  test -s "$output_dir/results/summary.json"
  test -s "$output_dir/results/predictions.jsonl"
  test -s "$output_dir/distilbert_training.json"
  test -s "$output_dir/metrics.jsonl"
  test -s "$output_dir/checkpoint-final/model.safetensors"
  test -s "$output_dir/checkpoint-final/checkpoint_manifest.json"
  rg --files --hidden --no-ignore "$output_dir/swanlog" | rg '.' >/dev/null
  while IFS= read -r path; do
    sha256sum "$path"
  done < <(rg --files --hidden --no-ignore "$output_dir" | sort) >"$launcher_dir/output.sha256"
  write_status "$launcher_dir" finished
}

launch_formal() {
  local model_binding=$1
  local command_name
  for command_name in rg uv screen sha256sum jq tee nvidia-smi; do
    require_command "$command_name"
  done
  validate_binding "$model_binding"
  local run_id
  run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
  local output_dir="runs/baselines/e2-distilbert-seed42-abd-to-c-v1-$run_id"
  local launcher_dir="runs/launchers/e2-distilbert-seed42-abd-to-c-v1-$run_id"
  local screen_name="e2-distilbert-s42-$run_id"
  local run_name="e2-distilbert-s42-abd-c-$run_id"
  if [[ -e "$output_dir" || -e "$launcher_dir" ]]; then
    printf '%s\n' 'E2 DistilBERT 运行身份冲突，拒绝复用目录。' >&2
    return 1
  fi
  mkdir -p "$launcher_dir" "$(dirname "$output_dir")"
  write_status "$launcher_dir" prepared
  {
    printf 'panel=abd_to_c\n'
    printf 'seed=42\n'
    printf 'protocol_dir=%s\n' "$protocol_dir"
    printf 'model_source=%s\n' "$model_source"
    printf 'output_dir=%s\n' "$output_dir"
    printf 'screen_name=%s\n' "$screen_name"
    printf 'run_name=%s\n' "$run_name"
    printf 'run_id=%s\n' "$run_id"
  } >"$launcher_dir/binding.txt"
  screen -L -Logfile "$launcher_dir/screen.log" -DmS "$screen_name" \
    env E2_DISTILBERT_LAUNCHER_DIR="$launcher_dir" \
    E2_DISTILBERT_OUTPUT_DIR="$output_dir" \
    E2_DISTILBERT_RUN_NAME="$run_name" \
    bash "$script_path" worker "$model_binding"
  sleep 2
  if screen -S "$screen_name" -Q select . >/dev/null 2>&1; then
    write_status "$launcher_dir" running
    printf 'E2_DISTILBERT_SCREEN=%s\nE2_DISTILBERT_OUTPUT=%s\nE2_DISTILBERT_LAUNCHER=%s\n' \
      "$screen_name" "$output_dir" "$launcher_dir"
    return 0
  fi
  if [[ -s "$launcher_dir/command-exit-code.txt" ]]; then
    write_status "$launcher_dir" failed
    printf 'E2 DistilBERT 正式入口快速失败：%s\n' "$launcher_dir" >&2
    return 1
  fi
  write_status "$launcher_dir" failed
  printf 'E2 DistilBERT screen 未保持运行且没有退出收据：%s\n' "$launcher_dir" >&2
  return 1
}

recover_run() {
  local launcher_dir=$1
  if [[ ! -d "$launcher_dir" || ! -s "$launcher_dir/binding.txt" ]]; then
    printf '启动证据目录无效：%s\n' "$launcher_dir" >&2
    return 2
  fi
  local output_dir=''
  local screen_name=''
  local key
  local value
  while IFS='=' read -r key value; do
    case "$key" in
      output_dir) output_dir=$value ;;
      screen_name) screen_name=$value ;;
    esac
  done <"$launcher_dir/binding.txt"
  if [[ -s "$launcher_dir/status.txt" ]] && [[ "$(<"$launcher_dir/status.txt")" == "finished" ]]; then
    printf 'E2 DistilBERT 已完成：%s\n' "$output_dir"
    return 0
  fi
  if [[ -n "$screen_name" ]] && screen -S "$screen_name" -Q select . >/dev/null 2>&1; then
    printf 'E2 DistilBERT 仍在运行：%s\n' "$screen_name"
    return 0
  fi
  write_status "$launcher_dir" interrupted_no_resumable_checkpoint
  {
    printf 'status=interrupted_no_resumable_checkpoint\n'
    printf 'output_dir=%s\n' "$output_dir"
    printf '%s\n' 'reason=当前适配器没有保存优化器、调度器和随机状态，禁止静默续跑或覆盖旧目录。'
  } >"$launcher_dir/restart-recovery.txt"
  printf '运行已中断且不可续训，保留证据并用新身份重跑：%s\n' "$launcher_dir" >&2
  return 1
}

case "$mode" in
  formal)
    if [[ $# -ne 2 ]]; then
      usage
      exit 2
    fi
    launch_formal "$argument"
    ;;
  worker)
    if [[ $# -ne 2 ]]; then
      usage
      exit 2
    fi
    run_worker "$argument"
    ;;
  recover)
    if [[ $# -ne 2 ]]; then
      usage
      exit 2
    fi
    recover_run "$argument"
    ;;
  *)
    usage
    exit 2
    ;;
esac
