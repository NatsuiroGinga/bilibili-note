#!/usr/bin/env bash

set -euo pipefail

dataset_dir="${GENIS_10S_DIR:-/root/autodl-tmp/thesis/datasets/GeNIS-2025/extracted/2-flows/flows-10-sec}"
uv_bin="${UV_BIN:-uv}"
output_dir="${1:-runs/data-audit/genis-10s-20260718}"

files=(
  attack-bruteforce-ftp.csv
  attack-bruteforce-smb.csv
  attack-bruteforce-ssh.csv
  attack-dos-hulk.csv
  attack-dos-icmp.csv
  attack-dos-pushack.csv
  attack-dos-slowloris.csv
  attack-dos-udp.csv
  benign-admin-activity.csv
  benign-background-activity.csv
  benign-user-activity.csv
)

command=("${uv_bin}" run flow-probe-audit-genis)
for file in "${files[@]}"; do
  path="${dataset_dir}/${file}"
  if [[ ! -f "${path}" ]]; then
    printf '缺少 GeNIS 输入文件：%s\n' "${path}" >&2
    exit 1
  fi
  command+=(--input "${path}")
done

mkdir -p "${output_dir}"
"${command[@]}" --output "${output_dir}/audit.json" 2>&1 | tee "${output_dir}/console.log"
