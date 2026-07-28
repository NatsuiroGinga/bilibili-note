#!/usr/bin/env bash

set -euo pipefail

uv_bin="${UV_BIN:-uv}"
sample_dir="${1:-runs/data-sampled/genis-hierarchical-v1-seed42}"
output_dir="${2:-runs/multiclass-baselines/genis-hierarchical-v1-seed42}"
seed="${3:-42}"
launcher_log="${output_dir}.launcher.log"

if [[ ! -f "${sample_dir}/sample_manifest.json" ]]; then
  printf '缺少分层采样清单：%s\n' "${sample_dir}/sample_manifest.json" >&2
  exit 1
fi
if [[ -e "${output_dir}" || -e "${launcher_log}" ]]; then
  printf '输出路径已存在，拒绝覆盖：%s\n' "${output_dir}" >&2
  exit 1
fi

mkdir -p "$(dirname "${output_dir}")"
"${uv_bin}" run flow-probe-multiclass-baselines \
  --sample-dir "${sample_dir}" \
  --output-dir "${output_dir}" \
  --seed "${seed}" \
  --run-name "multiclass-baselines-genis-hierarchical-seed${seed}" \
  --max-known-rejection-rate 0.05 \
  2>&1 | tee "${launcher_log}"
mv "${launcher_log}" "${output_dir}/launcher.log"
