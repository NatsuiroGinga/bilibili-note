#!/usr/bin/env bash

# 从冻结 v5 二进制与 v1 完整 aioquic 安装包构建独立 v6 覆盖层。
source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT="${1:-/root/autodl-tmp/thesis/experiments/llm_probe}"
V1_ROOT="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v1"
V5_ROOT="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v5"
FINAL_ROOT="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v6"
STAGING_ROOT="${FINAL_ROOT}.partial"
VERIFY_SCRIPT="${PROJECT_ROOT}/scripts/verify_r2_quic_v6_aioquic_overlay.py"
LAUNCHER_ROOT="${PROJECT_ROOT}/runs/launchers/r2-quic-v6-toolchain-build"
STATUS_PATH="${LAUNCHER_ROOT}/status.json"
LOG_PATH="${LAUNCHER_ROOT}/launcher.log"
SCRIPT_PATH="${PROJECT_ROOT}/scripts/build_r2_quic_v6_toolchain.sh"

SOURCE_TREE_SHA="0b3fc8d7768afe5238ddf30a025031a614205d115eaadeb2589759bb5e9d7610"
BUFFER_SHA="1300527251f5be7d9a001c32a452597740dc7d619b9245e11e2a677cdd5fcf62"
CRYPTO_SHA="64c07c18ad6a3189a770d53a847b950a6a72495157d7d8a55fe187955d9dd369"
PATCHED_PROTOCOL_SHA="d70c3457cae59122ce5ca20a77dabf2c6e08c4074a9077aa754f24c9263ad034"

write_status() {
  local status="$1"
  local detail="$2"
  local temporary="${STATUS_PATH}.tmp"
  printf '{"schema_version":"flow_probe_r2_quic_v6_toolchain_build_v1","status":"%s","detail":"%s","updated_at":"%s"}\n' \
    "${status}" "${detail}" "$(date -Iseconds)" > "${temporary}"
  mv "${temporary}" "${STATUS_PATH}"
}

mkdir -p "${LAUNCHER_ROOT}"
if [[ "${R2_QUIC_V6_BUILD_IN_SCREEN:-0}" != "1" ]]; then
  if [[ -e "${STATUS_PATH}" || -e "${FINAL_ROOT}" || -e "${STAGING_ROOT}" ]]; then
    printf 'v6 工具构建身份或目标已存在，拒绝重复构建\n' >&2
    exit 1
  fi
  write_status "prepared" "detached"
  screen -dmS r2-quic-v6-toolchain-build env R2_QUIC_V6_BUILD_IN_SCREEN=1 \
    bash "${SCRIPT_PATH}" "${PROJECT_ROOT}"
  printf '%s\n' "${LAUNCHER_ROOT}"
  exit 0
fi

exec >> "${LOG_PATH}" 2>&1
write_status "running" "copy_binary_overlay"
trap 'write_status "failed" "line_${LINENO}"' ERR

test -d "${V1_ROOT}"
test -d "${V5_ROOT}"
test -f "${VERIFY_SCRIPT}"
SITE_ROOT="$("${V1_ROOT}/aioquic-venv/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
SOURCE_PACKAGE_ROOT="${SITE_ROOT}/aioquic"
test -d "${SOURCE_PACKAGE_ROOT}"

mkdir -p "${STAGING_ROOT}"
rsync -a --exclude '/quiche-target/' --exclude '/aioquic-venv/' --exclude '/pycache/' \
  "${V5_ROOT}/" "${STAGING_ROOT}/"
mkdir -p "${STAGING_ROOT}/aioquic-overlay/aioquic"
rsync -a --exclude '__pycache__/' --exclude '*.pyc' \
  "${SOURCE_PACKAGE_ROOT}/" "${STAGING_ROOT}/aioquic-overlay/aioquic/"
cp "${V5_ROOT}/sources/aioquic-1.3.0/src/aioquic/asyncio/protocol.py" \
  "${STAGING_ROOT}/aioquic-overlay/aioquic/asyncio/protocol.py"

mkdir -p "${STAGING_ROOT}/aioquic-venv/bin"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -Eeuo pipefail' \
  'TOOL_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"' \
  'BASE_ROOT="$(cd "${TOOL_ROOT}/.." && pwd)/r2-quic-controlled-v1"' \
  'export R2_QUIC_V5_PACING_RECEIPTS=1' \
  'export PYTHONPATH="${TOOL_ROOT}/aioquic-overlay${PYTHONPATH:+:${PYTHONPATH}}"' \
  'exec "${BASE_ROOT}/aioquic-venv/bin/python" "$@"' \
  > "${STAGING_ROOT}/aioquic-venv/bin/python"
chmod 0755 "${STAGING_ROOT}/aioquic-venv/bin/python"

PYTHONPYCACHEPREFIX="${STAGING_ROOT}/pycache" \
  "${STAGING_ROOT}/aioquic-venv/bin/python" -m py_compile \
  "${STAGING_ROOT}/aioquic-overlay/aioquic/asyncio/protocol.py"
"${STAGING_ROOT}/aioquic-venv/bin/python" "${VERIFY_SCRIPT}" \
  --tool-root "${STAGING_ROOT}" \
  --source-package-root "${SOURCE_PACKAGE_ROOT}" \
  --expected-source-tree-sha256 "${SOURCE_TREE_SHA}" \
  --expected-buffer-sha256 "${BUFFER_SHA}" \
  --expected-crypto-sha256 "${CRYPTO_SHA}" \
  --expected-protocol-sha256 "${PATCHED_PROTOCOL_SHA}" \
  > "${STAGING_ROOT}/aioquic-overlay-verification.json"

cp "${V5_ROOT}/versions.txt" "${STAGING_ROOT}/versions.txt"
OVERLAY_SHA="$("${V1_ROOT}/aioquic-venv/bin/python" -c 'import json,sys; print(json.load(open(sys.argv[1]))["overlay_tree_sha256"])' "${STAGING_ROOT}/aioquic-overlay-verification.json")"
{
  printf 'v6_tool_binding=flow_probe_r2_quic_tool_binding_v6\n'
  printf 'v6_source_package_tree_sha256=%s\n' "${SOURCE_TREE_SHA}"
  printf 'v6_overlay_tree_sha256=%s\n' "${OVERLAY_SHA}"
  printf 'v6_buffer_sha256=%s\n' "${BUFFER_SHA}"
  printf 'v6_crypto_sha256=%s\n' "${CRYPTO_SHA}"
  printf 'v6_patched_protocol_sha256=%s\n' "${PATCHED_PROTOCOL_SHA}"
} >> "${STAGING_ROOT}/versions.txt"

mv "${STAGING_ROOT}" "${FINAL_ROOT}"
write_status "finished" "v6_toolchain_ready"
trap - ERR
