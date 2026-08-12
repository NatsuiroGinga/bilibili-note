#!/usr/bin/env bash

LLM_PROBE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

prepend_path() {
    local candidate="$1"
    if [[ -d "$candidate" && ":${PATH}:" != *":${candidate}:"* ]]; then
        PATH="${candidate}:${PATH}"
    fi
}

prepend_path "${LLM_PROBE_ROOT}/.venv/bin"
prepend_path "${LLM_PROBE_ROOT}/tools/bin"
prepend_path "${LLM_PROBE_ROOT}/tools/runtime/rust-1.85.0/bin"
prepend_path "${HOME}/.local/bin"
prepend_path "${HOME}/.cargo/bin"
for rust_toolchain_bin in "${HOME}"/.rustup/toolchains/stable-*/bin; do
    prepend_path "${rust_toolchain_bin}"
done

export LLM_PROBE_ROOT
export UV_CACHE_DIR="${UV_CACHE_DIR:-${LLM_PROBE_ROOT}/runs/cache/uv}"
export PATH
