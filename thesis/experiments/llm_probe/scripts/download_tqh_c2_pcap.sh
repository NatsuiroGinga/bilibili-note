#!/usr/bin/env bash

set -euo pipefail

profile="${1:-}"
dataset_dir="${TQH_C2_DIR:-/Users/bilibili/personal/note/raw/datasets/TQH-C2-2026}"
output_dir="${2:-/Users/bilibili/personal/note/thesis/experiments/llm_probe/runs/data-downloads/tqh-c2-pcap-20260724}"
archive_dir="${dataset_dir}/pcap_archives"

case "${profile}" in
  A)
    filename="TQH-C2_pcap_A_sliver_tls.zip"
    expected_md5="a48cd911df671193c207f2d0589be259"
    expected_sha256="699669d05c7afa990b25197aed6a79d8ecf323f1b5edf84839719aa52cd386b0"
    expected_size="33399375434"
    ;;
  B)
    filename="TQH-C2_pcap_B_merlin_quic.zip"
    expected_md5="fd1ce38e33bc64305fc8f6be246312e4"
    expected_sha256="ae8ecd9347b94fa8aa97b8ccdce5b81beb2ad7476a8e9dd759d5b7a61e5db1d9"
    expected_size="18228425928"
    ;;
  C)
    filename="TQH-C2_pcap_C_mythic_http.zip"
    expected_md5="d29f8f2c9cfb05847cae7e39de957d69"
    expected_sha256="522ab75ed1de642492f24d4276cc79004a69d09931b4ad3d1f1998f9b8121cbf"
    expected_size="379187915"
    ;;
  *)
    printf '用法：%s {A|B|C} [日志目录]\n' "$0" >&2
    exit 2
    ;;
esac

url="https://zenodo.org/api/records/21435571/files/${filename}/content"
archive_path="${archive_dir}/${filename}"
profile_output_dir="${output_dir}/${profile}"

mkdir -p "${archive_dir}" "${profile_output_dir}"
exec > >(tee -a "${profile_output_dir}/console.log") 2>&1

calculate_md5() {
  local path="$1"
  if command -v md5 >/dev/null 2>&1; then
    md5 -q "${path}"
    return
  fi

  local checksum
  read -r checksum _ < <(md5sum "${path}")
  printf '%s\n' "${checksum}"
}

calculate_sha256() {
  local path="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${path}" | awk '{print $1}'
    return
  fi

  local checksum
  read -r checksum _ < <(sha256sum "${path}")
  printf '%s\n' "${checksum}"
}

verify_archive() {
  local path="$1"
  local actual_size actual_md5 actual_sha256

  actual_size="$(wc -c < "${path}")"
  actual_size="${actual_size//[[:space:]]/}"
  if [[ "${actual_size}" != "${expected_size}" ]]; then
    printf '文件大小校验失败：expected=%s actual=%s\n' \
      "${expected_size}" "${actual_size}" >&2
    return 1
  fi

  actual_md5="$(calculate_md5 "${path}")"
  if [[ "${actual_md5}" != "${expected_md5}" ]]; then
    printf 'MD5 校验失败：expected=%s actual=%s\n' \
      "${expected_md5}" "${actual_md5}" >&2
    return 1
  fi

  actual_sha256="$(calculate_sha256 "${path}")"
  if [[ "${actual_sha256}" != "${expected_sha256}" ]]; then
    printf 'SHA-256 校验失败：expected=%s actual=%s\n' \
      "${expected_sha256}" "${actual_sha256}" >&2
    return 1
  fi

  if ! unzip -t "${path}" >/dev/null; then
    printf 'ZIP 完整性校验失败：%s\n' "${path}" >&2
    return 1
  fi

  printf '%s  %s\n' "${actual_md5}" "${filename}" \
    > "${profile_output_dir}/MD5SUMS.txt"
  printf '%s  %s\n' "${actual_sha256}" "${filename}" \
    > "${profile_output_dir}/SHA256SUMS.txt"
  printf '大小、MD5、SHA-256 和 ZIP 完整性均通过：%s\n' "${path}"
}

printf '下载配置：profile=%s file=%s expected_size=%s\n' \
  "${profile}" "${filename}" "${expected_size}"

if [[ -f "${archive_path}" ]]; then
  if [[ -f "${archive_path}.aria2" ]]; then
    printf '检测到 aria2 续传元数据，跳过未完成文件的整包哈希：%s\n' \
      "${archive_path}.aria2"
  elif verify_archive "${archive_path}"; then
    printf '文件已存在且全部校验通过：%s\n' "${archive_path}"
    exit 0
  else
    printf '现有文件校验未通过，将尝试从断点继续：%s\n' "${archive_path}"
  fi
fi

if command -v aria2c >/dev/null 2>&1; then
  aria2c \
    --continue=true \
    --max-connection-per-server=8 \
    --split=8 \
    --min-split-size=1M \
    --file-allocation=none \
    --auto-file-renaming=false \
    --max-tries=20 \
    --retry-wait=5 \
    --dir="${archive_dir}" \
    --out="${filename}" \
    "${url}"
else
  curl \
    --fail \
    --location \
    --continue-at - \
    --retry 20 \
    --retry-delay 5 \
    --retry-all-errors \
    --output "${archive_path}" \
    "${url}"
fi

verify_archive "${archive_path}"
