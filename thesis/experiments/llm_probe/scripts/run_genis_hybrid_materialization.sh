#!/usr/bin/env bash

set -euo pipefail

dataset_dir="${GENIS_10S_DIR:-/root/autodl-tmp/thesis/datasets/GeNIS-2025/extracted/2-flows/flows-10-sec}"
uv_bin="${UV_BIN:-uv}"
assignments_path="${1:-runs/data-splits/genis-hybrid-forward-v1-20260719/session_assignments.jsonl}"
output_dir="${2:-runs/data-prepared/genis-hybrid-forward-v1-20260719}"
console_log="${output_dir}.console.log"

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

if [[ ! -f "${assignments_path}" ]]; then
  printf '缺少会话分配文件：%s\n' "${assignments_path}" >&2
  exit 1
fi
if [[ -e "${output_dir}" || -e "${console_log}" ]]; then
  printf '输出路径已存在，拒绝覆盖：%s\n' "${output_dir}" >&2
  exit 1
fi

command=("${uv_bin}" run flow-probe-materialize-genis --assignments "${assignments_path}")
for file in "${files[@]}"; do
  path="${dataset_dir}/${file}"
  if [[ ! -f "${path}" ]]; then
    printf '缺少 GeNIS 输入文件：%s\n' "${path}" >&2
    exit 1
  fi
  command+=(--input "${path}")
done

mkdir -p "$(dirname "${output_dir}")"
"${command[@]}" --output-dir "${output_dir}" 2>&1 | tee "${console_log}"
mv "${console_log}" "${output_dir}/console.log"
