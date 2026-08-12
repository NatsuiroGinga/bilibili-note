#!/usr/bin/env bash

# 从已冻结 v8.1-r2 工具树和可核验 Jammy 包构造自包含抓包运行时。
source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT="${1:-/root/autodl-tmp/thesis/experiments/llm_probe}"
BASE="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v8-1-r2"
TARGET="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v8-1-r3"
PARTIAL="${TARGET}.partial"
BUNDLE="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-offline-bundles-v1/network-runtime-jammy-amd64-v1"
LIBPCAP_DEB="${BUNDLE}/libpcap0.8_1.10.1-4ubuntu1.22.04.1_amd64.deb"
TCPDUMP_DEB="${BUNDLE}/tcpdump_4.99.1-3ubuntu0.2_amd64.deb"

test -d "${BASE}"
test ! -e "${TARGET}"
test ! -e "${PARTIAL}"
printf '%s  %s\n' 'ba5ae645363bdd2c892a239427f363ba698198768252270956a33824d4e83d5e' "${LIBPCAP_DEB}" | sha256sum -c -
printf '%s  %s\n' '99d9b69491ed37afd3d3ce2fad50637a6659a12a2ac6c7df8ffc13c1bc9cc871' "${TCPDUMP_DEB}" | sha256sum -c -

mkdir -p "${PARTIAL}"
rsync -a --link-dest="${BASE}" --exclude='/apt-root' "${BASE}/" "${PARTIAL}/"
mkdir -p "${PARTIAL}/apt-root"
dpkg-deb -x "${LIBPCAP_DEB}" "${PARTIAL}/apt-root"
dpkg-deb -x "${TCPDUMP_DEB}" "${PARTIAL}/apt-root"

APT_LIBRARY_PATH="${PARTIAL}/apt-root/usr/lib/x86_64-linux-gnu"
TCPDUMP="${PARTIAL}/apt-root/usr/bin/tcpdump"
test ! -L "${PARTIAL}/apt-root"
test -x "${TCPDUMP}"
if LD_LIBRARY_PATH="${APT_LIBRARY_PATH}" ldd "${TCPDUMP}" | rg 'not found'; then
  printf 'tcpdump 仍有未解析动态库\n' >&2
  exit 1
fi
TCPDUMP_VERSION="$(LD_LIBRARY_PATH="${APT_LIBRARY_PATH}" "${TCPDUMP}" --version | head -n 1)"
printf '%s\n' "${TCPDUMP_VERSION}" | rg '^tcpdump version 4\.99\.1$'

cp "${BASE}/versions.txt" "${PARTIAL}/versions-r3.txt"
{
  printf 'runtime_revision=r3_self_contained_apt_root\n'
  printf 'tcpdump_deb_sha256=99d9b69491ed37afd3d3ce2fad50637a6659a12a2ac6c7df8ffc13c1bc9cc871\n'
  printf 'libpcap_deb_sha256=ba5ae645363bdd2c892a239427f363ba698198768252270956a33824d4e83d5e\n'
  printf 'tcpdump=%s\n' "${TCPDUMP_VERSION}"
} >> "${PARTIAL}/versions-r3.txt"
mv "${PARTIAL}/versions-r3.txt" "${PARTIAL}/versions.txt"

APT_TREE_SHA256="$({
  cd "${PARTIAL}/apt-root"
  rg --files --hidden --no-ignore | LC_ALL=C sort | while IFS= read -r path; do
    sha256sum "${path}"
  done
} | sha256sum | cut -d ' ' -f 1)"
printf '{"schema_version":"flow_probe_r2_quic_runtime_binding_r3","base_tool_root":"%s","apt_root_self_contained":true,"tcpdump_deb_sha256":"%s","libpcap_deb_sha256":"%s","apt_tree_sha256":"%s","tcpdump_version":"%s"}\n' \
  "${BASE}" \
  '99d9b69491ed37afd3d3ce2fad50637a6659a12a2ac6c7df8ffc13c1bc9cc871' \
  'ba5ae645363bdd2c892a239427f363ba698198768252270956a33824d4e83d5e' \
  "${APT_TREE_SHA256}" "${TCPDUMP_VERSION}" > "${PARTIAL}/runtime-binding-r3.json"

mv "${PARTIAL}" "${TARGET}"
printf '%s\n' "${TARGET}"
