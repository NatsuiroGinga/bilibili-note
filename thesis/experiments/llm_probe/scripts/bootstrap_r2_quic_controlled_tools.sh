#!/usr/bin/env bash

# 在项目隔离目录安装受控 QUIC 采集工具，不修改系统软件包状态。
source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT="${1:-/root/autodl-tmp/thesis/experiments/llm_probe}"
RUN_ID="${2:-r2-quic-tools-v1-attempt-2}"
ACTION="${3:-install}"
BUILD_JOBS="${CARGO_BUILD_JOBS:-1}"
TOOLS_ROOT="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-v1"
LAUNCHER_ROOT="${PROJECT_ROOT}/runs/launchers/${RUN_ID}"
STATUS_PATH="${LAUNCHER_ROOT}/status.json"
LOG_PATH="${LAUNCHER_ROOT}/launcher.log"
APT_ROOT="${TOOLS_ROOT}/apt-root"
APT_LIBRARY_PATH="${APT_ROOT}/usr/lib/x86_64-linux-gnu"
AIOQUIC_ENV="${TOOLS_ROOT}/aioquic-venv"
AIOQUIC_SOURCE="${TOOLS_ROOT}/sources/aioquic-1.3.0"
QUICHE_SOURCE="${TOOLS_ROOT}/sources/quiche-0.24.5"
CARGO_HOME="${TOOLS_ROOT}/cargo-home"
QUICHE_ARCHIVE="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-offline-bundles-v1/quiche-0.24.5-offline-source-vendor-v2.tar.gz"
QUICHE_MANIFEST="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-offline-bundles-v1/source-manifest-v2.json"
RUST_ARCHIVE="${PROJECT_ROOT}/runs/tools/rust-1.85.0-x86_64-unknown-linux-gnu-relay/rust-1.85.0-x86_64-unknown-linux-gnu.tar.xz"
RUST_SOURCE="${TOOLS_ROOT}/sources/rust-1.85.0-x86_64-unknown-linux-gnu"
RUST_TOOLCHAIN_ROOT="${TOOLS_ROOT}/rust-toolchain-1.85.0"
RUST_BIN="${RUST_TOOLCHAIN_ROOT}/bin"
RUST_RECEIPT="${TOOLS_ROOT}/rust-relay-receipt.json"
LIBCLANG_BUNDLE="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-offline-bundles-v1/libclang-jammy-amd64-v1"
LIBLLVM_DEB="${LIBCLANG_BUNDLE}/libllvm14_14.0.0-1ubuntu1.1_amd64.deb"
LIBCLANG_DEB="${LIBCLANG_BUNDLE}/libclang1-14_14.0.0-1ubuntu1.1_amd64.deb"
LIBCLANG_COMMON_DEB="${LIBCLANG_BUNDLE}/libclang-common-14-dev_14.0.0-1ubuntu1.1_amd64.deb"
LIBCLANG_MANIFEST="${LIBCLANG_BUNDLE}/source-manifest.json"
LIBCLANG_RUNTIME="${TOOLS_ROOT}/libclang-14-runtime"
LIBCLANG_LIBRARY="${LIBCLANG_RUNTIME}/usr/lib/x86_64-linux-gnu/libclang-14.so.14.0.0"
LIBCLANG_RESOURCE_DIR="${LIBCLANG_RUNTIME}/usr/lib/llvm-14/lib/clang/14.0.0"
LIBCLANG_RESOURCE_HEADER="${LIBCLANG_RESOURCE_DIR}/include/stddef.h"
LIBCLANG_RECEIPT="${TOOLS_ROOT}/libclang-offline-receipt.json"
NETWORK_RUNTIME_BUNDLE="${PROJECT_ROOT}/runs/tools/r2-quic-controlled-offline-bundles-v1/network-runtime-jammy-amd64-v1"
NETWORK_RUNTIME_MANIFEST="${NETWORK_RUNTIME_BUNDLE}/source-manifest.json"
LIBBPF_DEB="${NETWORK_RUNTIME_BUNDLE}/libbpf0_0.5.0-1ubuntu22.04.1_amd64.deb"
LIBMNL_DEB="${NETWORK_RUNTIME_BUNDLE}/libmnl0_1.0.4-3build2_amd64.deb"
LIBXTABLES_DEB="${NETWORK_RUNTIME_BUNDLE}/libxtables12_1.8.7-1ubuntu5_amd64.deb"
LIBPCAP_DEB="${NETWORK_RUNTIME_BUNDLE}/libpcap0.8_1.10.1-4ubuntu1.22.04.1_amd64.deb"
NETWORK_RUNTIME_RECEIPT="${TOOLS_ROOT}/network-runtime-offline-receipt.json"

mkdir -p "${TOOLS_ROOT}" "${TOOLS_ROOT}/sources" "${APT_ROOT}" "${LAUNCHER_ROOT}"

write_status() {
  local status="$1"
  local detail="$2"
  local temp_path="${STATUS_PATH}.tmp"
  printf '{"schema_version":"flow_probe_r2_quic_bootstrap_status_v1","status":"%s","detail":"%s","updated_at":"%s"}\n' \
    "${status}" "${detail}" "$(date -Iseconds)" > "${temp_path}"
  mv "${temp_path}" "${STATUS_PATH}"
}

write_rust_receipt() {
  local archive_sha archive_bytes rustc_version cargo_version temp_path
  archive_sha="$(sha256sum "${RUST_ARCHIVE}" | cut -d ' ' -f 1)"
  archive_bytes="$(stat -c '%s' "${RUST_ARCHIVE}")"
  rustc_version="$("${RUST_BIN}/rustc" --version)"
  cargo_version="$("${RUST_BIN}/cargo" --version)"
  printf '%s\n' "${rustc_version}" | rg '^rustc 1\.85\.0 '
  printf '%s\n' "${cargo_version}" | rg '^cargo 1\.85\.0 '
  [[ "${archive_sha}" == "6f8b323ed2a34ccf0031631b85d79e1133da662094566bc910432da9bd3a5b42" ]]
  [[ "${archive_bytes}" == "182464920" ]]
  temp_path="${RUST_RECEIPT}.tmp"
  printf '{"schema_version":"flow_probe_r2_quic_rust_relay_receipt_v1","source":"official_standalone_relay","archive":"%s","archive_bytes":%s,"archive_sha256":"%s","install_root":"%s","rustc":"%s","cargo":"%s","global_rust_modified":false,"verified_at":"%s"}\n' \
    "${RUST_ARCHIVE}" "${archive_bytes}" "${archive_sha}" "${RUST_TOOLCHAIN_ROOT}" \
    "${rustc_version}" "${cargo_version}" "$(date -Iseconds)" > "${temp_path}"
  mv "${temp_path}" "${RUST_RECEIPT}"
}

if [[ "${ACTION}" == "mark_relay_switch" ]]; then
  write_status "interrupted" "interrupted_by_explicit_relay_switch"
  exit 0
fi
if [[ "${ACTION}" == "mark_local_relay_policy" ]]; then
  write_status "interrupted" "interrupted_by_local_relay_policy"
  exit 0
fi
if [[ "${ACTION}" == "write_rust_receipt" ]]; then
  write_rust_receipt
  exit 0
fi
if [[ "${ACTION}" != "install" ]]; then
  printf '未知引导动作：%s\n' "${ACTION}" >&2
  exit 2
fi
if [[ -s "${STATUS_PATH}" ]]; then
  printf '工具链启动状态已存在，拒绝覆盖：%s\n' "${STATUS_PATH}" >&2
  exit 1
fi

fail() {
  local exit_code=$?
  write_status "failed" "bootstrap_exit_${exit_code}"
  exit "${exit_code}"
}
trap fail ERR

write_status "running" "installing_project_local_tools"
exec > >(tee -a "${LOG_PATH}") 2>&1

command -v rg >/dev/null
command -v fdfind >/dev/null
command -v jq >/dev/null
command -v sha256sum >/dev/null
command -v dpkg-deb >/dev/null

printf '%s  %s\n' "d5883b9906b3bdac371ccc12d618547f0fd680c1967b3081419ce2791eba1271" "${LIBBPF_DEB}" | sha256sum -c -
printf '%s  %s\n' "e0ed2e88526830896a9efcef75a3d019b40cdac5a56d6605c426296979708f4a" "${LIBMNL_DEB}" | sha256sum -c -
printf '%s  %s\n' "85ee2abbf1609cebd97bc14ef9233c8cd7f30b07b9a74cdb492cd1d361bd26d9" "${LIBXTABLES_DEB}" | sha256sum -c -
printf '%s  %s\n' "ba5ae645363bdd2c892a239427f363ba698198768252270956a33824d4e83d5e" "${LIBPCAP_DEB}" | sha256sum -c -
test "$(jq -r '.target_platform.codename' "${NETWORK_RUNTIME_MANIFEST}")" = "jammy"
test "$(jq -r '.target_platform.architecture' "${NETWORK_RUNTIME_MANIFEST}")" = "amd64"
test "$(dpkg-deb -f "${LIBBPF_DEB}" Package)" = "libbpf0"
test "$(dpkg-deb -f "${LIBBPF_DEB}" Version)" = "1:0.5.0-1ubuntu22.04.1"
test "$(dpkg-deb -f "${LIBMNL_DEB}" Package)" = "libmnl0"
test "$(dpkg-deb -f "${LIBMNL_DEB}" Version)" = "1.0.4-3build2"
test "$(dpkg-deb -f "${LIBXTABLES_DEB}" Package)" = "libxtables12"
test "$(dpkg-deb -f "${LIBXTABLES_DEB}" Version)" = "1.8.7-1ubuntu5"
test "$(dpkg-deb -f "${LIBPCAP_DEB}" Package)" = "libpcap0.8"
test "$(dpkg-deb -f "${LIBPCAP_DEB}" Version)" = "1.10.1-4ubuntu1.22.04.1"
for package in "${LIBBPF_DEB}" "${LIBMNL_DEB}" "${LIBXTABLES_DEB}" "${LIBPCAP_DEB}"; do
  dpkg-deb -x "${package}" "${APT_ROOT}"
done
test -e "${APT_LIBRARY_PATH}/libbpf.so.0"
test -e "${APT_LIBRARY_PATH}/libmnl.so.0"
test -e "${APT_LIBRARY_PATH}/libxtables.so.12"
test -e "${APT_LIBRARY_PATH}/libpcap.so.0.8"
export LD_LIBRARY_PATH="${APT_LIBRARY_PATH}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

test -x "${APT_ROOT}/bin/ip"
test -x "${APT_ROOT}/sbin/tc"
test -x "${APT_ROOT}/usr/bin/tcpdump"
for executable in "${APT_ROOT}/bin/ip" "${APT_ROOT}/sbin/tc" "${APT_ROOT}/usr/bin/tcpdump"; do
  if ldd "${executable}" | rg 'not found'; then
    printf '项目隔离网络工具仍有未解析依赖：%s\n' "${executable}" >&2
    exit 1
  fi
done
printf '{"schema_version":"flow_probe_r2_quic_network_runtime_receipt_v1","runtime_root":"%s","library_path":"%s","packages":["libbpf0=1:0.5.0-1ubuntu22.04.1","libmnl0=1.0.4-3build2","libxtables12=1.8.7-1ubuntu5","libpcap0.8=1.10.1-4ubuntu1.22.04.1"],"manifest_sha256":"%s","ldd_resolved":true,"global_install":false,"verified_at":"%s"}\n' \
  "${APT_ROOT}" "${APT_LIBRARY_PATH}" \
  "$(sha256sum "${NETWORK_RUNTIME_MANIFEST}" | cut -d ' ' -f 1)" \
  "$(date -Iseconds)" > "${NETWORK_RUNTIME_RECEIPT}"

test -x "${AIOQUIC_ENV}/bin/python"
"${AIOQUIC_ENV}/bin/python" -c 'from importlib.metadata import version; assert version("aioquic") == "1.3.0"; assert version("starlette") == "0.47.3"; assert version("wsproto") == "1.2.0"'

AIOQUIC_ARCHIVE="${TOOLS_ROOT}/sources/aioquic-1.3.0.tar.gz"
printf '%s  %s\n' "28d070b2183e3e79afa9d4e7bd558960d0d53aeb98bc0cf0a358b279ba797c92" "${AIOQUIC_ARCHIVE}" | sha256sum -c -
if [[ ! -d "${AIOQUIC_SOURCE}" ]]; then
  tar -xzf "${AIOQUIC_ARCHIVE}" -C "${TOOLS_ROOT}/sources"
fi
test -f "${AIOQUIC_SOURCE}/examples/http3_client.py"

export CARGO_HOME
export PATH="${RUST_BIN}:${PATH}"
mkdir -p "${CARGO_HOME}"
printf '%s  %s\n' "6f8b323ed2a34ccf0031631b85d79e1133da662094566bc910432da9bd3a5b42" "${RUST_ARCHIVE}" | sha256sum -c -
if [[ ! -f "${RUST_SOURCE}/install.sh" ]]; then
  tar -xJf "${RUST_ARCHIVE}" -C "${TOOLS_ROOT}/sources"
fi
if [[ ! -x "${RUST_BIN}/cargo" || ! -x "${RUST_BIN}/rustc" ]]; then
  bash "${RUST_SOURCE}/install.sh" --prefix="${RUST_TOOLCHAIN_ROOT}" --disable-ldconfig
fi
"${RUST_BIN}/rustc" --version | rg '^rustc 1\.85\.0 '
"${RUST_BIN}/cargo" --version | rg '^cargo 1\.85\.0 '

printf '%s  %s\n' "9044b614a6c7fb6262e7cbeb13dc731fc0c92bed96281c1a3920dd706442ee8e" "${LIBLLVM_DEB}" | sha256sum -c -
printf '%s  %s\n' "b75b743f5d5effaab97790c1379fb1855d1a20bd5432a2387bf4dc82d86d45e3" "${LIBCLANG_DEB}" | sha256sum -c -
printf '%s  %s\n' "a190eb2456b0cd398f04423eee53140d65f5f90d2353ad957e7e5884276d90b9" "${LIBCLANG_COMMON_DEB}" | sha256sum -c -
test "$(stat -c '%s' "${LIBLLVM_DEB}")" = "23967046"
test "$(stat -c '%s' "${LIBCLANG_DEB}")" = "6792182"
test "$(stat -c '%s' "${LIBCLANG_COMMON_DEB}")" = "5975328"
test "$(jq -r '.target_platform.codename' "${LIBCLANG_MANIFEST}")" = "jammy"
test "$(jq -r '.target_platform.architecture' "${LIBCLANG_MANIFEST}")" = "amd64"
test "$(dpkg-deb -f "${LIBLLVM_DEB}" Package)" = "libllvm14"
test "$(dpkg-deb -f "${LIBLLVM_DEB}" Version)" = "1:14.0.0-1ubuntu1.1"
test "$(dpkg-deb -f "${LIBCLANG_DEB}" Package)" = "libclang1-14"
test "$(dpkg-deb -f "${LIBCLANG_DEB}" Version)" = "1:14.0.0-1ubuntu1.1"
test "$(dpkg-deb -f "${LIBCLANG_COMMON_DEB}" Package)" = "libclang-common-14-dev"
test "$(dpkg-deb -f "${LIBCLANG_COMMON_DEB}" Version)" = "1:14.0.0-1ubuntu1.1"
if [[ ! -f "${LIBCLANG_LIBRARY}" ]]; then
  mkdir -p "${LIBCLANG_RUNTIME}"
  dpkg-deb -x "${LIBLLVM_DEB}" "${LIBCLANG_RUNTIME}"
  dpkg-deb -x "${LIBCLANG_DEB}" "${LIBCLANG_RUNTIME}"
fi
test -f "${LIBCLANG_LIBRARY}"
if [[ ! -f "${LIBCLANG_RESOURCE_HEADER}" ]]; then
  dpkg-deb -x "${LIBCLANG_COMMON_DEB}" "${LIBCLANG_RUNTIME}"
fi
test -f "${LIBCLANG_RESOURCE_HEADER}"
export LIBCLANG_PATH="${LIBCLANG_RUNTIME}/usr/lib/llvm-14/lib"
export LD_LIBRARY_PATH="${LIBCLANG_RUNTIME}/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export BINDGEN_EXTRA_CLANG_ARGS="-resource-dir=${LIBCLANG_RESOURCE_DIR}"
if ldd "${LIBCLANG_LIBRARY}" | rg 'not found'; then
  printf '项目隔离 libclang 仍有未解析依赖\n' >&2
  exit 1
fi
LIBCLANG_LIBRARY="${LIBCLANG_LIBRARY}" \
  /usr/bin/python3 -c 'import ctypes, os; ctypes.CDLL(os.environ["LIBCLANG_LIBRARY"])'
printf '{"schema_version":"flow_probe_r2_libclang_offline_receipt_v1","libclang_package":"libclang1-14=1:14.0.0-1ubuntu1.1","libllvm_package":"libllvm14=1:14.0.0-1ubuntu1.1","resource_headers_package":"libclang-common-14-dev=1:14.0.0-1ubuntu1.1","runtime_root":"%s","libclang_path":"%s","resource_header":"%s","resource_dir":"%s","bindgen_extra_clang_args":"%s","libllvm_sha256":"%s","libclang_sha256":"%s","resource_headers_sha256":"%s","manifest_sha256":"%s","ldd_resolved":true,"ctypes_load":true,"resource_header_present":true,"global_install":false,"verified_at":"%s"}\n' \
  "${LIBCLANG_RUNTIME}" "${LIBCLANG_PATH}" "${LIBCLANG_RESOURCE_HEADER}" \
  "${LIBCLANG_RESOURCE_DIR}" "${BINDGEN_EXTRA_CLANG_ARGS}" \
  "$(sha256sum "${LIBLLVM_DEB}" | cut -d ' ' -f 1)" \
  "$(sha256sum "${LIBCLANG_DEB}" | cut -d ' ' -f 1)" \
  "$(sha256sum "${LIBCLANG_COMMON_DEB}" | cut -d ' ' -f 1)" \
  "$(sha256sum "${LIBCLANG_MANIFEST}" | cut -d ' ' -f 1)" \
  "$(date -Iseconds)" > "${LIBCLANG_RECEIPT}"

printf '%s  %s\n' "2530b3499f2e3e3f5606cae92022432a5503b4423956d70485aefe4a2b894009" "${QUICHE_ARCHIVE}" | sha256sum -c -
test "$(jq -r '.bundle.sha256' "${QUICHE_MANIFEST}")" = "2530b3499f2e3e3f5606cae92022432a5503b4423956d70485aefe4a2b894009"
test "$(jq -r '.quiche.repository.commit' "${QUICHE_MANIFEST}")" = "5ea8d8e3569c1ed34b895e2211e62791e77c29ab"
test "$(jq -r '.quiche.boringssl.commit' "${QUICHE_MANIFEST}")" = "f1c75347daa2ea81a941e953f2263e0a4d970c8d"
test "$(jq -r '.cargo.vendor.crate_directories' "${QUICHE_MANIFEST}")" = "344"
if [[ ! -f "${QUICHE_SOURCE}/Cargo.toml" ]]; then
  mkdir -p "${QUICHE_SOURCE}"
  tar -xzf "${QUICHE_ARCHIVE}" -C "${QUICHE_SOURCE}"
fi
test -f "${QUICHE_SOURCE}/Cargo.lock"
test -f "${QUICHE_SOURCE}/.cargo/config.toml"
test -f "${QUICHE_SOURCE}/quiche/deps/boringssl/CMakeLists.txt"
if [[ ! -x "${QUICHE_SOURCE}/target/release/quiche-client" || ! -x "${QUICHE_SOURCE}/target/release/quiche-server" ]]; then
  pushd "${QUICHE_SOURCE}" >/dev/null
  "${RUST_BIN}/cargo" build --release --features qlog --bin quiche-client --bin quiche-server --offline --frozen -j "${BUILD_JOBS}"
  popd >/dev/null
fi

test -x "${QUICHE_SOURCE}/target/release/quiche-client"
test -x "${QUICHE_SOURCE}/target/release/quiche-server"

VERSIONS_PATH="${TOOLS_ROOT}/versions.txt"
{
  printf 'aioquic='; "${AIOQUIC_ENV}/bin/python" -c 'import aioquic; print(aioquic.__version__)'
  printf 'quiche=0.24.5\n'
  printf 'rustc='; "${RUST_BIN}/rustc" --version
  printf 'cargo='; "${RUST_BIN}/cargo" --version
  printf 'rust_source=official_standalone_relay\n'
  printf 'rust_archive_sha256='; sha256sum "${RUST_ARCHIVE}" | cut -d ' ' -f 1
  printf 'iproute2='; "${APT_ROOT}/sbin/tc" -V
  printf 'tcpdump='; "${APT_ROOT}/usr/bin/tcpdump" --version | head -n 1
  printf 'network_runtime_packages=libbpf0=1:0.5.0-1ubuntu22.04.1,libmnl0=1.0.4-3build2,libxtables12=1.8.7-1ubuntu5,libpcap0.8=1.10.1-4ubuntu1.22.04.1\n'
  printf 'network_runtime_source=local_relay_huaweicloud_ubuntu_mirror\n'
  printf 'network_runtime_manifest_sha256='; sha256sum "${NETWORK_RUNTIME_MANIFEST}" | cut -d ' ' -f 1
  printf 'libbpf_deb_sha256='; sha256sum "${LIBBPF_DEB}" | cut -d ' ' -f 1
  printf 'libmnl_deb_sha256='; sha256sum "${LIBMNL_DEB}" | cut -d ' ' -f 1
  printf 'libxtables_deb_sha256='; sha256sum "${LIBXTABLES_DEB}" | cut -d ' ' -f 1
  printf 'libpcap_deb_sha256='; sha256sum "${LIBPCAP_DEB}" | cut -d ' ' -f 1
  printf 'aioquic_source_sha256='; sha256sum "${AIOQUIC_ARCHIVE}" | cut -d ' ' -f 1
  printf 'quiche_tag_source_sha256=7d2dff9ac5b9a53eb32d98af9b5fae944dcc7176a9fcfe1877f682b1ec935663\n'
  printf 'quiche_offline_bundle_sha256='; sha256sum "${QUICHE_ARCHIVE}" | cut -d ' ' -f 1
  printf 'quiche_manifest_sha256='; sha256sum "${QUICHE_MANIFEST}" | cut -d ' ' -f 1
  printf 'libclang=libclang1-14 1:14.0.0-1ubuntu1.1\n'
  printf 'libllvm=libllvm14 1:14.0.0-1ubuntu1.1\n'
  printf 'libclang_resource_headers=libclang-common-14-dev 1:14.0.0-1ubuntu1.1\n'
  printf 'bindgen_extra_clang_args=%s\n' "${BINDGEN_EXTRA_CLANG_ARGS}"
  printf 'libclang_source=local_relay_huaweicloud_ubuntu_mirror\n'
  printf 'libclang_deb_sha256='; sha256sum "${LIBCLANG_DEB}" | cut -d ' ' -f 1
  printf 'libllvm_deb_sha256='; sha256sum "${LIBLLVM_DEB}" | cut -d ' ' -f 1
  printf 'libclang_resource_headers_deb_sha256='; sha256sum "${LIBCLANG_COMMON_DEB}" | cut -d ' ' -f 1
  printf 'libclang_manifest_sha256='; sha256sum "${LIBCLANG_MANIFEST}" | cut -d ' ' -f 1
} > "${VERSIONS_PATH}"

write_status "finished" "all_project_local_tools_ready"
trap - ERR
