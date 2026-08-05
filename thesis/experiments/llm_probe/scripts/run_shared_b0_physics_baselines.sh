#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

mode=${1:-}
baseline=${2:-}
script_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
project_root=$(cd "$(dirname "$script_path")/.." && pwd)
config_path=configs/shared_b0_physics_baselines_seed42_200_v1.yaml
model_path=${SHARED_B0_PHYSICS_MODEL_PATH:-/root/autodl-tmp/thesis/models/Qwen3-1.7B}
dataset_root=runs/data-frozen/dataset-v1-shared-b0
sidecar_root=runs/data-frozen/dataset-v1-shared-b0-physics-v1
minimum_free_bytes=$((5 * 1024 * 1024 * 1024))

usage() {
  printf '用法：bash %s formal state_supervision|standard_pinn\n' "${BASH_SOURCE[0]}" >&2
}

if [[ $# -ne 2 || "$mode" != formal ]]; then
  usage
  exit 2
fi

case "$baseline" in
  state_supervision)
    output_dir=runs/baselines/shared-b0-qwen-state-supervision-seed42-200-v1
    baseline_tag=state-supervision
    ;;
  standard_pinn)
    output_dir=runs/baselines/shared-b0-qwen-standard-pinn-seed42-200-v1
    baseline_tag=standard-pinn
    ;;
  *)
    usage
    exit 2
    ;;
esac

cd "$project_root"

screen_name="shared-b0-${baseline_tag}-s42-200-v1"
run_name="shared-b0-${baseline_tag}-s42-200-v1"
dynamic_tags=(shared-b0 "$baseline_tag" seed42 steps200 run-formal review-pending)

require_command() {
  local name=$1
  if ! command -v "$name" >/dev/null 2>&1; then
    printf '服务器缺少必需命令：%s\n' "$name" >&2
    return 1
  fi
}

write_status() {
  local launcher_dir=$1
  local status=$2
  local temporary="$launcher_dir/status.txt.partial.$$"
  printf '%s\n' "$status" >"$temporary"
  mv "$temporary" "$launcher_dir/status.txt"
}

run_with_log() {
  local log_path=$1
  shift
  mkdir -p "$(dirname "$log_path")"
  : >"$log_path"
  set +e
  "$@" 2>&1 | tee "$log_path"
  local pipeline_status=("${PIPESTATUS[@]}")
  set -e
  local command_status=${pipeline_status[0]}
  local tee_status=${pipeline_status[1]}
  if [[ ! -s "$log_path" ]]; then
    printf '%s\n' '运行日志为空。' >>"$log_path"
    if [[ "$command_status" -eq 0 && "$tee_status" -eq 0 ]]; then
      command_status=1
    fi
  fi
  if [[ "$command_status" -ne 0 ]]; then
    return "$command_status"
  fi
  return "$tee_status"
}

write_capabilities() {
  local target=$1
  uv run --no-sync python -c '
import json
import os
import platform
import torch

cuda_available = bool(torch.cuda.is_available())
bf16_supported = bool(cuda_available and torch.cuda.is_bf16_supported())
payload = {
    "cuda_available": cuda_available,
    "bf16_supported": bf16_supported,
    "cuda_device": torch.cuda.get_device_name(0) if cuda_available else None,
    "cuda_memory_bytes": (
        int(torch.cuda.get_device_properties(0).total_memory) if cuda_available else 0
    ),
    "cpu": platform.processor() or platform.machine(),
    "logical_cpu_count": os.cpu_count(),
    "torch_version": torch.__version__,
}
print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
if not cuda_available:
    raise SystemExit("未检测到 CUDA，正式共享 B0 大模型训练不支持无卡运行")
if not bf16_supported:
    raise SystemExit("当前 GPU 不支持正式训练所需的 BF16")
' >"$target"
  test -s "$target"
}

validate_swanlab_contract() {
  local tags
  tags=$(IFS=,; printf '%s' "${dynamic_tags[*]}")
  SHARED_B0_SWANLAB_RUN_NAME="$run_name" \
    SHARED_B0_SWANLAB_TAGS="$tags" \
    uv run --no-sync python -c '
import os
import sys
from pathlib import Path

import yaml

from flow_probe.tracking import TrackingSettings

raw = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
tracking = dict(raw["tracking"])
tracking["run_name"] = os.environ["SHARED_B0_SWANLAB_RUN_NAME"]
tracking["tags"] = [
    *tracking["tags"],
    *os.environ["SHARED_B0_SWANLAB_TAGS"].split(","),
]
settings = TrackingSettings.from_mapping(tracking)
if settings.mode != "online":
    raise SystemExit("SwanLab 必须使用在线模式")
print("SwanLab 在线配置与动态短标签预检通过")
' "$config_path"
}

preflight_common() {
  local launcher_dir=$1
  local required_path
  for required_path in \
    "$config_path" \
    "$script_path" \
    src/flow_probe/shared_b0_physics_train.py \
    src/flow_probe/shared_b0_physics_sidecar.py \
    src/flow_probe/train_sft.py \
    "$dataset_root/candidate/qwen_train.jsonl" \
    "$dataset_root/validation/genis_qwen.jsonl" \
    "$sidecar_root/candidate/ns3_physics_train.jsonl" \
    "$sidecar_root/dataset_manifest.json" \
    "$sidecar_root/source_manifest.json" \
    "$sidecar_root/join_audit.json" \
    "$sidecar_root/materialization_audit.json" \
    "$model_path/config.json"; do
    if [[ ! -f "$required_path" ]]; then
      printf '缺少正式训练输入：%s\n' "$required_path" >&2
      return 1
    fi
  done

  local free_bytes
  free_bytes=$(df -PB1 "$project_root" | awk 'NR == 2 {print $4}')
  if ((free_bytes < minimum_free_bytes)); then
    printf '服务器可用空间不足 5 GiB：%s 字节\n' "$free_bytes" >&2
    return 1
  fi

  write_capabilities "$launcher_dir/capabilities.json"
  validate_swanlab_contract
  uv run --no-sync flow-probe-train-shared-b0-physics \
    --config "$config_path" \
    --baseline "$baseline" \
    --output-dir "$output_dir" \
    --preflight-only >"$launcher_dir/training-preflight.json"
  test -s "$launcher_dir/training-preflight.json"

  {
    sha256sum "$config_path"
    sha256sum "$script_path"
    sha256sum src/flow_probe/shared_b0_physics_train.py
    sha256sum src/flow_probe/shared_b0_physics_sidecar.py
    sha256sum src/flow_probe/train_sft.py
    sha256sum "$dataset_root/candidate/qwen_train.jsonl"
    sha256sum "$dataset_root/validation/genis_qwen.jsonl"
    sha256sum "$sidecar_root/candidate/ns3_physics_train.jsonl"
    sha256sum "$sidecar_root/dataset_manifest.json"
    sha256sum "$sidecar_root/source_manifest.json"
    sha256sum "$sidecar_root/join_audit.json"
    sha256sum "$sidecar_root/materialization_audit.json"
    sha256sum "$model_path/config.json"
  } >"$launcher_dir/bindings.sha256"
  test -s "$launcher_dir/bindings.sha256"
}

validate_completed_run() {
  jq -e '
    .status == "completed" and
    .optimization_step == 200 and
    .physics_micro_step == 400 and
    .generation_cursor == 800 and
    .physics_cursor == 2421
  ' "$output_dir/run_state.json" >/dev/null
  jq -e '
    .status == "completed" and
    .max_steps == 200 and
    .metrics_count == 200 and
    .nonfinite_count == 0
  ' "$output_dir/train_summary.json" >/dev/null
  jq -e '.status == "completed" and (.artifacts | length > 0)' \
    "$output_dir/artifact_manifest.json" >/dev/null
  test -d "$output_dir/checkpoints/checkpoint-000200"
  test "$(wc -l <"$output_dir/step_metrics.jsonl" | tr -d ' ')" -eq 200
  local swanlog_files=''
  if [[ -d "$output_dir/swanlog" ]]; then
    swanlog_files=$(rg --files "$output_dir/swanlog" 2>/dev/null || true)
  fi
  if [[ -z "$swanlog_files" ]]; then
    printf '正式训练缺少本地 SwanLab 日志：%s/swanlog\n' "$output_dir" >&2
    return 1
  fi
}

run_formal_worker() {
  local launcher_dir=${SHARED_B0_PHYSICS_LAUNCHER_DIR:?缺少正式启动证据目录}
  export SHARED_B0_SWANLAB_RUN_NAME="$run_name"
  export SHARED_B0_SWANLAB_TAGS
  SHARED_B0_SWANLAB_TAGS=$(IFS=,; printf '%s' "${dynamic_tags[*]}")
  export SWANLAB_MODE=cloud

  local status=0
  write_status "$launcher_dir" running
  run_with_log "$launcher_dir/launcher.log" \
    uv run --no-sync flow-probe-train-shared-b0-physics \
    --config "$config_path" \
    --baseline "$baseline" \
    --output-dir "$output_dir" \
    --resume auto || status=$?
  printf '%s\n' "$status" >"$launcher_dir/exit-code.txt"
  if [[ "$status" -ne 0 ]]; then
    write_status "$launcher_dir" failed
    return "$status"
  fi

  if ! validate_completed_run >>"$launcher_dir/launcher.log" 2>&1; then
    status=$?
    if [[ "$status" -eq 0 ]]; then
      status=1
    fi
    printf '%s\n' "$status" >"$launcher_dir/exit-code.txt"
    write_status "$launcher_dir" failed
    return "$status"
  fi
  write_status "$launcher_dir" finished
}

for command_name in rg uv jq sha256sum screen; do
  require_command "$command_name"
done

if [[ "${SHARED_B0_PHYSICS_FORMAL_WORKER:-0}" == 1 ]]; then
  run_formal_worker
  exit $?
fi

if [[ -f "$output_dir/run_state.json" ]] && \
  jq -e '.status == "completed"' "$output_dir/run_state.json" >/dev/null 2>&1; then
  printf '正式训练已经完成，拒绝覆盖：%s\n' "$output_dir" >&2
  exit 3
fi
if screen -S "$screen_name" -Q select . >/dev/null 2>&1; then
  printf '正式训练会话已在运行：%s\n' "$screen_name" >&2
  exit 4
fi

run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
launcher_dir="runs/launchers/shared-b0-physics-formal-${baseline_tag}-${run_id}"
if [[ -e "$launcher_dir" || -L "$launcher_dir" ]]; then
  printf '启动证据目录已存在，拒绝复用：%s\n' "$launcher_dir" >&2
  exit 5
fi
mkdir -p "$launcher_dir" "$(dirname "$output_dir")"
write_status "$launcher_dir" prepared

preflight_status=0
run_with_log "$launcher_dir/preflight.log" preflight_common "$launcher_dir" || preflight_status=$?
if [[ "$preflight_status" -ne 0 ]]; then
  printf '%s\n' "$preflight_status" >"$launcher_dir/exit-code.txt"
  write_status "$launcher_dir" failed
  exit "$preflight_status"
fi

screen -L -Logfile "$launcher_dir/screen.log" -DmS "$screen_name" \
  env SHARED_B0_PHYSICS_FORMAL_WORKER=1 \
  SHARED_B0_PHYSICS_LAUNCHER_DIR="$launcher_dir" \
  bash "$script_path" formal "$baseline"
sleep 1
if screen -S "$screen_name" -Q select . >/dev/null 2>&1; then
  write_status "$launcher_dir" running
  printf 'FORMAL_SCREEN=%s\nFORMAL_OUTPUT=%s\nFORMAL_LAUNCHER=%s\n' \
    "$screen_name" "$output_dir" "$launcher_dir"
  exit 0
fi
if [[ -s "$launcher_dir/exit-code.txt" ]]; then
  worker_status=$(<"$launcher_dir/exit-code.txt")
  if [[ "$worker_status" =~ ^[0-9]+$ ]] && [[ "$worker_status" -eq 0 ]]; then
    printf '正式训练已快速完成：%s\n' "$output_dir"
    exit 0
  fi
  printf '正式训练在启动检查前退出，退出码=%s，证据=%s\n' \
    "$worker_status" "$launcher_dir" >&2
  exit "$worker_status"
fi
write_status "$launcher_dir" failed
printf '正式训练 screen 未保持运行且没有退出码：%s\n' "$launcher_dir" >&2
exit 6
