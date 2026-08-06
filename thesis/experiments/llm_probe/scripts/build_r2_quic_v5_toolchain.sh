#!/usr/bin/env bash

# 从冻结 v1 工具构建独立 v5 端点节奏工具，不覆盖旧源码或二进制。
source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT="${1:-/root/autodl-tmp/thesis/experiments/llm_probe}"
BASE_ROOT="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v1"
FINAL_ROOT="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v5"
STAGING_ROOT="${FINAL_ROOT}.partial"
PATCH_PATH="${PROJECT_ROOT}/scripts/r2_quic_v5_endpoint_pacing.patch"
LAUNCHER_ROOT="${PROJECT_ROOT}/runs/launchers/r2-quic-v5-toolchain-build"
STATUS_PATH="${LAUNCHER_ROOT}/status.json"
LOG_PATH="${LAUNCHER_ROOT}/launcher.log"
SCRIPT_PATH="${PROJECT_ROOT}/scripts/build_r2_quic_v5_toolchain.sh"

write_status() {
  local status="$1"
  local detail="$2"
  local temporary="${STATUS_PATH}.tmp"
  printf '{"schema_version":"flow_probe_r2_quic_v5_toolchain_build_v1","status":"%s","detail":"%s","updated_at":"%s"}\n' \
    "${status}" "${detail}" "$(date -Iseconds)" > "${temporary}"
  mv "${temporary}" "${STATUS_PATH}"
}

mkdir -p "${LAUNCHER_ROOT}"
if [[ "${R2_QUIC_V5_BUILD_IN_SCREEN:-0}" != "1" ]]; then
  if [[ -e "${STATUS_PATH}" || -e "${FINAL_ROOT}" || -e "${STAGING_ROOT}" ]]; then
    printf 'v5 工具构建身份或目标已存在，拒绝重复构建\n' >&2
    exit 1
  fi
  write_status "prepared" "detached"
  screen -dmS r2-quic-v5-toolchain-build env R2_QUIC_V5_BUILD_IN_SCREEN=1 \
    bash "${SCRIPT_PATH}" "${PROJECT_ROOT}"
  printf '%s\n' "${LAUNCHER_ROOT}"
  exit 0
fi

exec >> "${LOG_PATH}" 2>&1
write_status "running" "copy_and_build"
trap 'write_status "failed" "line_${LINENO}"' ERR

test -d "${BASE_ROOT}"
test -f "${PATCH_PATH}"
printf '%s  %s\n' \
  '7a605aa9916c162f32d883d201ca5cd8c43435d500cba5725703d4f0d4656d25' \
  "${PATCH_PATH}" | sha256sum -c -
printf '%s  %s\n' \
  '0030292e29c0d58d3a864f3a621c1162be9ed92d6452cb99a6064e45d70f0f96' \
  "${BASE_ROOT}/sources/quiche-0.24.5/apps/src/client.rs" | sha256sum -c -
printf '%s  %s\n' \
  '76330f02a1fbf917333edb4a59687221980e31422782d5ede17d83d4ec910be0' \
  "${BASE_ROOT}/sources/quiche-0.24.5/apps/src/sendto.rs" | sha256sum -c -
printf '%s  %s\n' \
  'fba619a474aa51c1f1ccce8d43dd7da5792af850ea2aedaecbf8c990ff873e72' \
  "${BASE_ROOT}/sources/quiche-0.24.5/apps/src/bin/quiche-server.rs" | sha256sum -c -
printf '%s  %s\n' \
  'd87759d24c3bba979d2e27e6d4ff3dcdaa1a9395280a32352c38c1d352bab936' \
  "${BASE_ROOT}/sources/aioquic-1.3.0/src/aioquic/asyncio/protocol.py" | sha256sum -c -

mkdir -p "${STAGING_ROOT}/sources"
rsync -a --exclude '/target/' --exclude '/.git/' \
  "${BASE_ROOT}/sources/quiche-0.24.5/" \
  "${STAGING_ROOT}/sources/quiche-0.24.5/"
rsync -a --exclude '/.git/' \
  "${BASE_ROOT}/sources/aioquic-1.3.0/" \
  "${STAGING_ROOT}/sources/aioquic-1.3.0/"
patch -p1 -d "${STAGING_ROOT}/sources" < "${PATCH_PATH}"

export LIBCLANG_PATH="${BASE_ROOT}/libclang-14-runtime/usr/lib/llvm-14/lib"
export LD_LIBRARY_PATH="${BASE_ROOT}/libclang-14-runtime/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export BINDGEN_EXTRA_CLANG_ARGS="-resource-dir=${BASE_ROOT}/libclang-14-runtime/usr/lib/llvm-14/lib/clang/14.0.0"
export PATH="${BASE_ROOT}/rust-toolchain-1.85.0/bin:${PATH}"
export CARGO_TARGET_DIR="${STAGING_ROOT}/quiche-target"
pushd "${STAGING_ROOT}/sources/quiche-0.24.5" >/dev/null
"${BASE_ROOT}/rust-toolchain-1.85.0/bin/cargo" build \
  --release --features qlog --bin quiche-client --bin quiche-server --offline --frozen -j 8
popd >/dev/null

mkdir -p "${STAGING_ROOT}/sources/quiche-0.24.5/target/release"
cp "${CARGO_TARGET_DIR}/release/quiche-client" \
  "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-client-r2-v5"
cp "${CARGO_TARGET_DIR}/release/quiche-server" \
  "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-server-r2-v5"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -Eeuo pipefail' \
  'export R2_QUIC_V5_USERSPACE_PACING=1' \
  'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"' \
  'exec "${SCRIPT_DIR}/quiche-client-r2-v5" "$@"' \
  > "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-client"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -Eeuo pipefail' \
  'export R2_QUIC_V5_USERSPACE_PACING=1' \
  'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"' \
  'exec "${SCRIPT_DIR}/quiche-server-r2-v5" "$@"' \
  > "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-server"
chmod 0755 \
  "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-client" \
  "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-server"

mkdir -p "${STAGING_ROOT}/aioquic-venv/bin"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -Eeuo pipefail' \
  'TOOL_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"' \
  'BASE_ROOT="$(cd "${TOOL_ROOT}/.." && pwd)/r2-quic-controlled-v1"' \
  'export R2_QUIC_V5_PACING_RECEIPTS=1' \
  'export PYTHONPATH="${TOOL_ROOT}/sources/aioquic-1.3.0/src${PYTHONPATH:+:${PYTHONPATH}}"' \
  'exec "${BASE_ROOT}/aioquic-venv/bin/python" "$@"' \
  > "${STAGING_ROOT}/aioquic-venv/bin/python"
chmod 0755 "${STAGING_ROOT}/aioquic-venv/bin/python"
ln -s "${BASE_ROOT}/apt-root" "${STAGING_ROOT}/apt-root"

PYTHONPYCACHEPREFIX="${STAGING_ROOT}/pycache" \
  "${STAGING_ROOT}/aioquic-venv/bin/python" -m py_compile \
  "${STAGING_ROOT}/sources/aioquic-1.3.0/src/aioquic/asyncio/protocol.py"

cp "${BASE_ROOT}/versions.txt" "${STAGING_ROOT}/versions.txt"
{
  printf 'v5_tool_binding=flow_probe_r2_quic_tool_binding_v5\n'
  printf 'v5_pacing_patch_sha256=%s\n' "$(sha256sum "${PATCH_PATH}" | cut -d ' ' -f 1)"
  printf 'v5_quiche_client_sha256=%s\n' "$(sha256sum "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-client-r2-v5" | cut -d ' ' -f 1)"
  printf 'v5_quiche_server_sha256=%s\n' "$(sha256sum "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-server-r2-v5" | cut -d ' ' -f 1)"
  printf 'v5_aioquic_protocol_sha256=%s\n' "$(sha256sum "${STAGING_ROOT}/sources/aioquic-1.3.0/src/aioquic/asyncio/protocol.py" | cut -d ' ' -f 1)"
} >> "${STAGING_ROOT}/versions.txt"

test -x "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-client"
test -x "${STAGING_ROOT}/sources/quiche-0.24.5/target/release/quiche-server"
test -x "${STAGING_ROOT}/aioquic-venv/bin/python"
mv "${STAGING_ROOT}" "${FINAL_ROOT}"
write_status "finished" "v5_toolchain_ready"
trap - ERR
