#!/usr/bin/env bash
set -Eeuo pipefail

project_root="${1:-/root/autodl-tmp/thesis/experiments/llm_probe}"
source_root="${project_root}/runs/tools/r2-quic-controlled-v6"
target_name="${2:-r2-quic-controlled-v8-1}"
target_root="${project_root}/runs/tools/${target_name}"
receipt_patch="${project_root}/scripts/r2_quic_v8_1_aioquic_receipt.patch"
binding_marker="${project_root}/configs/r2_quic_v8_1_tool_binding.txt"

if [[ ! -d "${source_root}" ]]; then
  printf '缺少 v6 工具树：%s\n' "${source_root}" >&2
  exit 2
fi
if [[ -e "${target_root}" ]]; then
  printf '拒绝覆盖既有 v8.1 工具树：%s\n' "${target_root}" >&2
  exit 3
fi
if [[ ! -f "${receipt_patch}" ]]; then
  printf '缺少 v8.1 时间语义补丁：%s\n' "${receipt_patch}" >&2
  exit 4
fi
if [[ ! -f "${binding_marker}" ]]; then
  printf '缺少 v8.1 工具绑定标记：%s\n' "${binding_marker}" >&2
  exit 5
fi

cp -a --reflink=auto "${source_root}" "${target_root}"
patch --batch --forward --no-backup-if-mismatch -p1 \
  -d "${target_root}/aioquic-overlay" \
  -i "${receipt_patch}"
cp "${binding_marker}" "${target_root}/versions-v8-1.txt"

export PYTHONPATH="${target_root}/aioquic-overlay"
"${target_root}/aioquic-venv/bin/python" -c \
  'import aioquic.asyncio.protocol as p; print(p.__file__)'
sha256sum "${target_root}/aioquic-overlay/aioquic/asyncio/protocol.py"
