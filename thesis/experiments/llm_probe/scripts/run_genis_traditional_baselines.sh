#!/usr/bin/env bash

set -euo pipefail

uv_bin="${UV_BIN:-uv}"
prepared_dir="${1:-runs/data-prepared/genis-hybrid-forward-v1-20260719-v3}"
output_dir="${2:-runs/traditional-baselines/genis-hybrid-forward-v3-seed42}"
seed="${3:-42}"
launcher_log="${output_dir}.launcher.log"

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
    printf '缺少基线输入文件：%s\n' "${path}" >&2
    exit 1
  fi
done
if [[ -e "${output_dir}" || -e "${launcher_log}" ]]; then
  printf '输出路径已存在，拒绝覆盖：%s\n' "${output_dir}" >&2
  exit 1
fi

mkdir -p "$(dirname "${output_dir}")"
"${uv_bin}" run flow-probe-traditional-baselines \
  --train "${prepared_dir}/train.jsonl" \
  --evaluation "validation=${prepared_dir}/validation.jsonl" \
  --evaluation "test=${prepared_dir}/test.jsonl" \
  --evaluation "ood-dos-icmp=${prepared_dir}/ood_dos-icmp.jsonl" \
  --evaluation "ood-dos-pushack=${prepared_dir}/ood_dos-pushack.jsonl" \
  --evaluation "ood-dos-udp=${prepared_dir}/ood_dos-udp.jsonl" \
  --output-dir "${output_dir}" \
  --seed "${seed}" \
  --run-name "traditional-baselines-genis-hybrid-forward-seed${seed}" \
  2>&1 | tee "${launcher_log}"
mv "${launcher_log}" "${output_dir}/launcher.log"
