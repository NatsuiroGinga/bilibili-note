#!/usr/bin/env bash

# 用 uv 缓存重建 r3 自包含 aioquic 运行时，并断开对已删除 v1 的转发引用。
source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT="${1:-/root/autodl-tmp/thesis/experiments/llm_probe}"
TOOL_ROOT="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v8-1-r3"
RUNTIME="${TOOL_ROOT}/aioquic-runtime"
WRAPPER="${TOOL_ROOT}/aioquic-venv/bin/python"
RECEIPT="${TOOL_ROOT}/aioquic-runtime-r3.json"

test -d "${TOOL_ROOT}"
test ! -e "${RUNTIME}"
test ! -e "${RECEIPT}"
uv venv --python 3.11 "${RUNTIME}"
uv pip install --offline --python "${RUNTIME}/bin/python" \
  'aioquic==1.3.0' 'starlette==0.47.3' 'wsproto==1.2.0'

WRAPPER_TEMP="${WRAPPER}.r3.tmp"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -Eeuo pipefail' \
  'TOOL_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"' \
  'export R2_QUIC_V5_PACING_RECEIPTS=1' \
  'export PYTHONPATH="${TOOL_ROOT}/aioquic-overlay${PYTHONPATH:+:${PYTHONPATH}}"' \
  'exec "${TOOL_ROOT}/aioquic-runtime/bin/python" "$@"' > "${WRAPPER_TEMP}"
chmod 0755 "${WRAPPER_TEMP}"
mv "${WRAPPER_TEMP}" "${WRAPPER}"

"${WRAPPER}" -c '
from importlib.metadata import version
assert version("aioquic") == "1.3.0"
assert version("starlette") == "0.47.3"
assert version("wsproto") == "1.2.0"
from aioquic.asyncio.protocol import QuicConnectionProtocol
print(QuicConnectionProtocol.__module__)
'

FREEZE_PATH="${TOOL_ROOT}/aioquic-runtime-r3.freeze.txt"
uv pip freeze --python "${RUNTIME}/bin/python" > "${FREEZE_PATH}"
FREEZE_SHA256="$(sha256sum "${FREEZE_PATH}" | cut -d ' ' -f 1)"
WRAPPER_SHA256="$(sha256sum "${WRAPPER}" | cut -d ' ' -f 1)"
printf '{"schema_version":"flow_probe_r2_quic_aioquic_runtime_r3","python":"3.11","offline_cache":true,"aioquic":"1.3.0","starlette":"0.47.3","wsproto":"1.2.0","freeze_sha256":"%s","wrapper_sha256":"%s","v1_dependency":false}\n' \
  "${FREEZE_SHA256}" "${WRAPPER_SHA256}" > "${RECEIPT}"

VERSIONS_TEMP="${TOOL_ROOT}/versions.txt.r3.tmp"
cp "${TOOL_ROOT}/versions.txt" "${VERSIONS_TEMP}"
{
  printf 'aioquic_runtime=r3_self_contained_uv_offline\n'
  printf 'aioquic_runtime_freeze_sha256=%s\n' "${FREEZE_SHA256}"
  printf 'aioquic_wrapper_sha256=%s\n' "${WRAPPER_SHA256}"
} >> "${VERSIONS_TEMP}"
mv "${VERSIONS_TEMP}" "${TOOL_ROOT}/versions.txt"
cat "${RECEIPT}"
