#!/usr/bin/env bash

set -euo pipefail

full_training_session="${1:-qwen-hier-v2-s42-full-epoch1}"
config_path="${2:-configs/genis_hierarchical_v2_qwen3_1_7b_seed42_pilot200_eval50.yaml}"
model_path="${3:-/root/autodl-tmp/thesis/models/Qwen3-1.7B}"
adapter_path="${4:-runs/qwen-multitask/genis-hierarchical-v2-seed42-pilot200/final_adapter}"
full_manifest="${5:-runs/qwen-multitask/genis-hierarchical-v2-seed42-full-epoch1/artifact_manifest.json}"

if command -v uv >/dev/null 2>&1; then
  uv_bin="$(command -v uv)"
elif [[ -x /root/.local/bin/uv ]]; then
  uv_bin=/root/.local/bin/uv
else
  printf '未找到 uv 命令\n' >&2
  exit 1
fi
if [[ ! -f "${config_path}" || ! -d "${model_path}" || ! -d "${adapter_path}" ]]; then
  printf '评估配置、模型或适配器缺失\n' >&2
  exit 1
fi

output_dir="$(
  .venv/bin/python -c \
    'import sys, yaml; print(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["evaluation"]["output_dir"])' \
    "${config_path}"
)"
launcher_log="${output_dir}.launcher.log"
if [[ -e "${output_dir}" || -e "${launcher_log}" ]]; then
  printf '评估输出路径已存在，拒绝覆盖：%s\n' "${output_dir}" >&2
  exit 1
fi

printf '等待完整训练会话结束：%s\n' "${full_training_session}"
while screen -list 2>/dev/null | rg -q "[.]${full_training_session}[[:space:]]"; do
  sleep 10
done
if [[ ! -f "${full_manifest}" ]]; then
  printf '完整训练结束但缺少制品清单：%s\n' "${full_manifest}" >&2
  exit 1
fi
if ! jq -e '.status == "finished"' "${full_manifest}" >/dev/null; then
  printf '完整训练未成功完成，拒绝自动接续评估\n' >&2
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
  printf '=== 启动分层生成式评估 ===\n'
  "${uv_bin}" run --no-sync python -c \
    'from flow_probe.hierarchical_evaluation import main; main()' \
    --config "${config_path}" \
    --model-path "${model_path}" \
    --adapter-path "${adapter_path}"
} 2>&1 | tee "${launcher_log}"

mv "${launcher_log}" "${output_dir}/launcher.log"
