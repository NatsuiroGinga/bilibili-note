#!/usr/bin/env bash

set -euo pipefail

dataset_root="${DEDALE_DATASET_ROOT:-/root/autodl-tmp/thesis/datasets/DEDALE-2.0}"
zeek_dir="${DEDALE_ZEEK_ORANGE_DMZ_DIR:-${dataset_root}/extracted/zeek_orange_dmz/orange_dmz}"
cic_zip="${DEDALE_CIC_ORANGE_DMZ_ZIP:-${dataset_root}/cicflowmeter_orange_dmz.zip}"
uv_bin="${UV_BIN:-uv}"
output_dir="${1:-runs/data-audit/dedale-orange-dmz-v2-20260721}"

if [[ ! -d "${zeek_dir}" ]]; then
  printf '缺少 DEDALE Zeek 目录：%s\n' "${zeek_dir}" >&2
  exit 1
fi
if [[ ! -f "${cic_zip}" ]]; then
  printf '缺少 DEDALE CICFlowMeter 归档：%s\n' "${cic_zip}" >&2
  exit 1
fi
if [[ -e "${output_dir}" ]]; then
  printf '拒绝复用 DEDALE 审计输出目录：%s\n' "${output_dir}" >&2
  exit 1
fi

shopt -s nullglob
zeek_files=("${zeek_dir}"/D*_*/conn_labeled.csv)
if [[ ${#zeek_files[@]} -ne 28 ]]; then
  printf 'DEDALE Zeek 日文件必须正好为 28 个，实际为：%s\n' "${#zeek_files[@]}" >&2
  exit 1
fi

mkdir -p "${output_dir}"
"${uv_bin}" run --no-sync python -m flow_probe.dedale_audit \
  --zeek-dir "${zeek_dir}" \
  --cic-zip "${cic_zip}" \
  --start-tolerance-seconds 1.0 \
  --output "${output_dir}/audit.json" \
  --manifest-output "${output_dir}/input_manifest.json" \
  2>&1 | tee "${output_dir}/console.log"
