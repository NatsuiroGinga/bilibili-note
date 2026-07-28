#!/usr/bin/env bash

set -euo pipefail

uv_bin="${UV_BIN:-uv}"
prepared_dir="${1:-runs/data-prepared/genis-hybrid-forward-v1-20260719-v4}"
output_dir="${2:-runs/data-sampled/genis-hierarchical-v1-seed42}"
seed="${3:-42}"
console_log="${output_dir}.console.log"

required_files=(
  train.jsonl
  validation.jsonl
  test.jsonl
  ood_dos-icmp.jsonl
  ood_dos-pushack.jsonl
  ood_dos-udp.jsonl
  materialization_summary.json
)
for file in "${required_files[@]}"; do
  path="${prepared_dir}/${file}"
  if [[ ! -f "${path}" ]]; then
    printf '缺少分层采样输入文件：%s\n' "${path}" >&2
    exit 1
  fi
done
if [[ -e "${output_dir}" || -e "${console_log}" ]]; then
  printf '输出路径已存在，拒绝覆盖：%s\n' "${output_dir}" >&2
  exit 1
fi

mkdir -p "$(dirname "${output_dir}")"
"${uv_bin}" run flow-probe-sample-hierarchical \
  --source-dir "${prepared_dir}" \
  --output-dir "${output_dir}" \
  --seed "${seed}" \
  2>&1 | tee "${console_log}"
mv "${console_log}" "${output_dir}/console.log"
