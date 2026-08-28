#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    printf '%s\n' '用法: bash verify_cuda13_compiler_env.sh <params.json>' >&2
    exit 64
fi

PARAMS_PATH=$1
OUTPUT_DIR=$(jq -er '.output_dir' "$PARAMS_PATH")
PYTHON_BIN=$(jq -er '.python_bin' "$PARAMS_PATH")
CUDA_ROOT=$(jq -er '.cuda_root' "$PARAMS_PATH")
EXPECTED_CAPABILITY=$(jq -er '.expected_capability' "$PARAMS_PATH")

case "$OUTPUT_DIR" in
    /root/autodl-tmp/thesis/experiments/llm_probe/runs/toolchain/*) ;;
    *)
        printf '非法输出目录: %s\n' "$OUTPUT_DIR" >&2
        exit 65
        ;;
esac

[[ "$PYTHON_BIN" == /root/autodl-tmp/thesis/experiments/llm_probe/.venv/bin/python ]]
[[ "$CUDA_ROOT" == /usr/local/cuda-13.0 ]]
[[ "$EXPECTED_CAPABILITY" == 12.0 ]]
[[ -f /etc/profile.d/cuda-13-0.sh ]]

source /etc/profile.d/cuda-13-0.sh
[[ "$CUDA_HOME" == "$CUDA_ROOT" ]]
[[ "$(command -v nvcc)" == "$CUDA_ROOT/bin/nvcc" ]]
command -v ninja
command -v timeout

write_state() {
    local status=$1
    local reason=${2:-}
    local state_tmp="$OUTPUT_DIR/cuda_smoke_state.json.tmp"
    jq -n \
        --arg status "$status" \
        --arg reason "$reason" \
        --arg updated_at "$(date --iso-8601=seconds)" \
        '{status: $status, reason: $reason, updated_at: $updated_at}' >"$state_tmp"
    mv "$state_tmp" "$OUTPUT_DIR/cuda_smoke_state.json"
}

on_error() {
    local exit_code=$?
    write_state failed "CUDA 最小编译验证在第 ${BASH_LINENO[0]} 行退出，状态码 ${exit_code}"
    exit "$exit_code"
}
trap on_error ERR

write_state running ''

SOURCE_PATH="$OUTPUT_DIR/minimal_cuda_smoke.cu"
BUILD_PATH="$OUTPUT_DIR/build.ninja"
BINARY_PATH="$OUTPUT_DIR/minimal_cuda_smoke"

cat >"$SOURCE_PATH" <<'CUDA_EOF'
#include <cuda_runtime.h>

#include <cstdio>

#define CUDA_CHECK(call)                                                        \
    do {                                                                        \
        const cudaError_t error = (call);                                       \
        if (error != cudaSuccess) {                                             \
            std::fprintf(stderr, "CUDA 错误: %s (%s:%d)\n",                    \
                         cudaGetErrorString(error), __FILE__, __LINE__);         \
            return 1;                                                           \
        }                                                                       \
    } while (0)

__global__ void add_one(int* value) {
    if (threadIdx.x == 0 && blockIdx.x == 0) {
        *value += 1;
    }
}

int main() {
    cudaDeviceProp properties{};
    CUDA_CHECK(cudaGetDeviceProperties(&properties, 0));

    int host_value = 41;
    int result = 0;
    int* device_value = nullptr;
    CUDA_CHECK(cudaMalloc(&device_value, sizeof(int)));
    CUDA_CHECK(cudaMemcpy(device_value, &host_value, sizeof(int), cudaMemcpyHostToDevice));

    add_one<<<1, 1>>>(device_value);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
    CUDA_CHECK(cudaMemcpy(&result, device_value, sizeof(int), cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaFree(device_value));

    if (result != 42 || properties.major != 12 || properties.minor != 0) {
        std::fprintf(stderr,
                     "验证值不符: result=%d capability=%d.%d\n",
                     result,
                     properties.major,
                     properties.minor);
        return 2;
    }

    std::printf(
        "{\"status\":\"ok\",\"result\":%d,\"device\":\"%s\",\"capability\":\"%d.%d\"}\n",
        result,
        properties.name,
        properties.major,
        properties.minor);
    return 0;
}
CUDA_EOF

cat >"$BUILD_PATH" <<'NINJA_EOF'
nvcc = /usr/local/cuda-13.0/bin/nvcc

rule cuda_compile_and_link
  command = $nvcc -std=c++17 -O2 -lineinfo -arch=sm_120 $in -o $out
  description = NVCC $out

build minimal_cuda_smoke: cuda_compile_and_link minimal_cuda_smoke.cu

default minimal_cuda_smoke
NINJA_EOF

ninja -C "$OUTPUT_DIR" -f build.ninja -v >"$OUTPUT_DIR/cuda-smoke-compile.log" 2>&1
timeout 60 "$BINARY_PATH" >"$OUTPUT_DIR/cuda-smoke-run.json" 2>"$OUTPUT_DIR/cuda-smoke-run.stderr"
rg -F '"status":"ok"' "$OUTPUT_DIR/cuda-smoke-run.json"
rg -F '"result":42' "$OUTPUT_DIR/cuda-smoke-run.json"
rg -F '"capability":"12.0"' "$OUTPUT_DIR/cuda-smoke-run.json"

sha256sum "$SOURCE_PATH" "$BUILD_PATH" "$BINARY_PATH" \
    >"$OUTPUT_DIR/cuda-smoke-artifacts.sha256"
file "$BINARY_PATH" >"$OUTPUT_DIR/cuda-smoke-binary-file.txt"
ldd "$BINARY_PATH" >"$OUTPUT_DIR/cuda-smoke-binary-ldd.txt"

"$PYTHON_BIN" -c 'import json, os, torch; from torch.utils.cpp_extension import CUDA_HOME; print(json.dumps({"env_cuda_home": os.environ.get("CUDA_HOME"), "nvcc": os.popen("command -v nvcc").read().strip(), "torch": torch.__version__, "torch_cuda": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "device": torch.cuda.get_device_name(0), "capability": torch.cuda.get_device_capability(0), "cpp_extension_cuda_home": CUDA_HOME}))' \
    >"$OUTPUT_DIR/final-environment.json"
rg -F '"env_cuda_home": "/usr/local/cuda-13.0"' "$OUTPUT_DIR/final-environment.json"
rg -F '"nvcc": "/usr/local/cuda-13.0/bin/nvcc"' "$OUTPUT_DIR/final-environment.json"
rg -F '"torch_cuda": "13.0"' "$OUTPUT_DIR/final-environment.json"
rg -F '"cpp_extension_cuda_home": "/usr/local/cuda-13.0"' "$OUTPUT_DIR/final-environment.json"

nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader \
    >"$OUTPUT_DIR/gpu-after-smoke.csv"
cmp "$OUTPUT_DIR/gpu-before.csv" "$OUTPUT_DIR/gpu-after-smoke.csv"

write_state finished ''
trap - ERR
