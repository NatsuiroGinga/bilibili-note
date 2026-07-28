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
launcher_log="${output_dir}.launcher.log"

if [[ ! -f "${bundle_dir}/bundle_manifest.json" ]]; then
  printf '缺少多任务数据清单：%s\n' "${bundle_dir}/bundle_manifest.json" >&2
  exit 1
fi
if [[ -e "${output_dir}" || -e "${launcher_log}" ]]; then
  printf '输出路径已存在，拒绝覆盖：%s\n' "${output_dir}" >&2
  exit 1
fi

mkdir -p "$(dirname "${output_dir}")"
{
  printf '=== SwanLab 连通性 ===\n'
  .venv/bin/swanlab ping
  .venv/bin/swanlab verify
  printf '=== GPU 状态 ===\n'
  nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
  printf '=== 数据盘状态 ===\n'
  df -h /root/autodl-tmp
  printf '=== 启动 Qwen 分层多任务训练 ===\n'
  "${uv_bin}" run --no-sync flow-probe-train \
    --config "${config_path}" \
    --model-path "${model_path}"
} 2>&1 | tee "${launcher_log}"

mv "${launcher_log}" "${output_dir}/launcher.log"
