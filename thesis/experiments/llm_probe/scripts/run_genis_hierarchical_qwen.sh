#!/usr/bin/env bash

set -euo pipefail

config_path="${1:-configs/genis_hierarchical_v2_qwen3_1_7b_seed42_pilot.yaml}"
model_path="${2:-models/Qwen3-1.7B}"

if [[ ! -f "${config_path}" ]]; then
  printf '缺少 Qwen 分层实验配置：%s\n' "${config_path}" >&2
  exit 1
fi
if [[ ! -d "${model_path}" ]]; then
  printf '缺少本地 Qwen 模型目录：%s\n' "${model_path}" >&2
  exit 1
fi
if [[ ! -x .venv/bin/python || ! -x .venv/bin/swanlab ]]; then
  printf '缺少项目虚拟环境或 SwanLab 命令，请先使用 uv 同步环境\n' >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  uv_bin="$(command -v uv)"
elif [[ -x /root/.local/bin/uv ]]; then
  uv_bin=/root/.local/bin/uv
else
  printf '未找到 uv 命令\n' >&2
  exit 1
fi

output_dir="$(
  .venv/bin/python -c \
    'import sys, yaml; print(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["training"]["output_dir"])' \
    "${config_path}"
)"
train_file="$(
  .venv/bin/python -c \
    'import sys, yaml; print(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["training"]["train_file"])' \
    "${config_path}"
)"
bundle_dir="$(dirname "${train_file}")"

if [[ ! -f "${bundle_dir}/bundle_manifest.json" ]]; then
  printf '缺少多任务数据清单：%s\n' "${bundle_dir}/bundle_manifest.json" >&2
  exit 1
fi

run_mode=fresh
resume_checkpoint=
if [[ -e "${output_dir}" ]]; then
  if [[ ! -d "${output_dir}" ]]; then
    printf '训练输出路径不是目录：%s\n' "${output_dir}" >&2
    exit 1
  fi
  if ! resume_checkpoint="$(
    .venv/bin/python -c '
import json
import sys
from pathlib import Path

import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.train_sft import (
    build_training_binding,
    build_training_settings,
    resolve_resume_checkpoint,
)

config_path = Path(sys.argv[1])
model_path = Path(sys.argv[2])
raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
probe = override_model_id(ProbeConfig.from_mapping(raw["probe"]), str(model_path))
settings = build_training_settings(probe, raw["training"])
if settings.resume_from_checkpoint != "auto":
    raise SystemExit("恢复预检失败：resume_from_checkpoint 必须为 auto")
state_path = settings.output_dir / "run_state.json"
try:
    state = json.loads(state_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as error:
    raise SystemExit(f"恢复预检失败：无法读取 run_state.json：{error}") from error
status = state.get("status")
if status not in {"prepared", "running", "interrupted"}:
    raise SystemExit(f"恢复预检失败：运行状态不可恢复：{status}")
try:
    binding = build_training_binding(probe, settings, model_path)
    checkpoint = resolve_resume_checkpoint(
        settings.output_dir,
        binding,
        settings.resume_from_checkpoint,
    )
except (OSError, ValueError) as error:
    raise SystemExit(f"恢复预检失败：{error}") from error
if checkpoint is None:
    raise SystemExit("恢复预检失败：未找到绑定一致的完整检查点")
print(checkpoint)
' "${config_path}" "${model_path}"
  )"; then
    exit 1
  fi
  run_mode=resume
fi

attempt_number=1
while true; do
  attempt_id="$(printf '%04d' "${attempt_number}")"
  launcher_name="launcher.attempt-${attempt_id}.log"
  final_launcher_log="${output_dir}/${launcher_name}"
  staging_launcher_log="${output_dir}.launcher.attempt-${attempt_id}.log"
  if [[ ! -e "${final_launcher_log}" && ! -e "${staging_launcher_log}" ]]; then
    break
  fi
  attempt_number=$((attempt_number + 1))
done

mkdir -p "$(dirname "${output_dir}")"
if [[ "${run_mode}" == resume ]]; then
  active_launcher_log="${final_launcher_log}"
else
  active_launcher_log="${staging_launcher_log}"
fi

finalize_launcher_log() {
  local status=$?
  trap - EXIT
  if [[ "${active_launcher_log}" != "${final_launcher_log}" \
    && -f "${active_launcher_log}" \
    && -d "${output_dir}" ]]; then
    if [[ -e "${final_launcher_log}" ]]; then
      printf '目标启动日志已存在，拒绝覆盖：%s\n' "${final_launcher_log}" >&2
      status=1
    elif ! mv "${active_launcher_log}" "${final_launcher_log}"; then
      printf '无法把启动日志移入运行目录：%s\n' "${final_launcher_log}" >&2
      status=1
    fi
  fi
  exit "${status}"
}
trap finalize_launcher_log EXIT

run_attempt() {
  printf '=== 启动尝试 %s ===\n' "${attempt_id}"
  if [[ "${run_mode}" == resume ]]; then
    printf '=== 恢复预检 ===\n'
    printf '恢复检查点：%s\n' "${resume_checkpoint}"
  else
    printf '=== 新训练预检 ===\n'
  fi
  printf '=== SwanLab 连通性 ===\n'
  .venv/bin/swanlab ping || return
  .venv/bin/swanlab verify || return
  printf '=== GPU 状态 ===\n'
  nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader || return
  printf '=== 数据盘状态 ===\n'
  df -h /root/autodl-tmp || return

  if [[ "${run_mode}" == resume && -f "${output_dir}/artifact_manifest.json" ]]; then
    manifest_archive="${output_dir}/artifact_manifest.before-attempt-${attempt_id}.json"
    if [[ -e "${manifest_archive}" ]]; then
      printf '历史制品清单归档路径已存在，拒绝覆盖：%s\n' "${manifest_archive}" >&2
      return 1
    fi
    printf '归档历史制品清单：%s\n' "${manifest_archive}"
    mv "${output_dir}/artifact_manifest.json" "${manifest_archive}" || return
  fi

  printf '=== 启动 Qwen 分层多任务训练 ===\n'
  "${uv_bin}" run --no-sync flow-probe-train \
    --config "${config_path}" \
    --model-path "${model_path}"
}

run_attempt 2>&1 | tee "${active_launcher_log}"
