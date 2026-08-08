#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    printf '%s\n' '用法: bash rollback_cuda13_system_changes_and_verify.sh <params.json>' >&2
    exit 64
fi

PARAMS_PATH=$1
OUTPUT_DIR=$(jq -er '.output_dir' "$PARAMS_PATH")
PYTHON_BIN=$(jq -er '.python_bin' "$PARAMS_PATH")
VENV_DIR=$(jq -er '.venv_dir' "$PARAMS_PATH")
CUDA_ROOT=$(jq -er '.cuda_root' "$PARAMS_PATH")

case "$OUTPUT_DIR" in
    /root/autodl-tmp/thesis/experiments/llm_probe/runs/toolchain/*) ;;
    *)
        printf '非法输出目录: %s\n' "$OUTPUT_DIR" >&2
        exit 65
        ;;
esac

[[ "$PYTHON_BIN" == /root/autodl-tmp/thesis/experiments/llm_probe/.venv/bin/python ]]
[[ "$VENV_DIR" == /root/autodl-tmp/thesis/experiments/llm_probe/.venv ]]
[[ "$CUDA_ROOT" == /usr/local/cuda-13.0 ]]

LOG_PATH="$OUTPUT_DIR/rollback-and-final-verify.log"
exec >"$LOG_PATH" 2>&1

write_state() {
    local status=$1
    local reason=${2:-}
    local state_tmp="$OUTPUT_DIR/rollback_state.json.tmp"
    jq -n \
        --arg status "$status" \
        --arg reason "$reason" \
        --arg updated_at "$(date --iso-8601=seconds)" \
        '{status: $status, reason: $reason, updated_at: $updated_at}' >"$state_tmp"
    mv "$state_tmp" "$OUTPUT_DIR/rollback_state.json"
}

on_error() {
    local exit_code=$?
    write_state failed "精确回滚与最终验证在第 ${BASH_LINENO[0]} 行退出，状态码 ${exit_code}"
    exit "$exit_code"
}
trap on_error ERR

exec 9>/var/lock/rwkv-cuda13-compiler-install.lock
if ! flock -n 9; then
    write_state failed '另一个 CUDA 13.0 工具链任务正在运行'
    exit 75
fi

write_state running ''

SYSTEM_NINJA_VERSION=$(/usr/bin/ninja --version)
VENV_NINJA_VERSION=$(
    "$VENV_DIR/bin/ninja" --version
)
[[ "$SYSTEM_NINJA_VERSION" == 1.10.1 ]]
[[ "$VENV_NINJA_VERSION" == 1.13.0* ]]
"$PYTHON_BIN" -c 'import importlib.metadata as m; assert m.version("ninja") == "1.13.0"'

SOURCE_LIST=/etc/apt/sources.list.d/cuda-ubuntu2204-x86_64.list
KEY_PATH=/usr/share/keyrings/cuda-archive-keyring.gpg
PIN_PATH=/etc/apt/preferences.d/cuda-repository-pin-600
PROFILE_PATH=/etc/profile.d/cuda-13-0.sh
APT_INRELEASE='/var/lib/apt/lists/developer.download.nvidia.com_compute_cuda_repos_ubuntu2204_x86%5f64_InRelease'
APT_PACKAGES='/var/lib/apt/lists/developer.download.nvidia.com_compute_cuda_repos_ubuntu2204_x86%5f64_Packages.lz4'

[[ "$(sha256sum "$SOURCE_LIST" | awk '{print $1}')" == c3edadf5367af06a1f8c9790baf6cb5dc34de8e74ac2c1a45c17eec0da02fd72 ]]
[[ "$(sha256sum "$KEY_PATH" | awk '{print $1}')" == 25100d6f2eccaee7d6719a70e3c0c6145064aa9edc2c32148f693ac4c524a376 ]]
[[ "$(sha256sum "$PIN_PATH" | awk '{print $1}')" == dd00df91301f85f920a43641113793b3e8d6006e058e36fc69f44eadaebf648a ]]
[[ "$(sha256sum "$PROFILE_PATH" | awk '{print $1}')" == 73053e095b73436f6b10666f4a05c041eb16dbd189f328f07d3ce98b42cf81c3 ]]
[[ -f /root/.gnupg/pubring.kbx ]]
[[ -f /root/.gnupg/trustdb.gpg ]]

apt-get --simulate remove ninja-build >"$OUTPUT_DIR/apt-remove-ninja-simulate.txt"
[[ "$(awk '/^Remv / {print $2}' "$OUTPUT_DIR/apt-remove-ninja-simulate.txt")" == ninja-build ]]
[[ "$(awk '/^Remv / {count += 1} END {print count + 0}' "$OUTPUT_DIR/apt-remove-ninja-simulate.txt")" == 1 ]]

DEBIAN_FRONTEND=noninteractive apt-get remove -y ninja-build
apt-mark auto cuda-compiler-13-0

rm -- "$SOURCE_LIST"
rm -- "$KEY_PATH"
rm -- "$PIN_PATH"
rm -- "$PROFILE_PATH"
rm -- "$APT_INRELEASE"
rm -- "$APT_PACKAGES"
rm -- /root/.gnupg/pubring.kbx
rm -- /root/.gnupg/trustdb.gpg
rmdir /root/.gnupg

[[ ! -e "$SOURCE_LIST" ]]
[[ ! -e "$KEY_PATH" ]]
[[ ! -e "$PIN_PATH" ]]
[[ ! -e "$PROFILE_PATH" ]]
[[ ! -e /root/.gnupg ]]
if rg 'developer\.download\.nvidia\.com|cuda/repos' \
    /etc/apt/sources.list /etc/apt/sources.list.d --line-number; then
    printf '%s\n' '回滚后仍存在 NVIDIA CUDA 软件源配置' >&2
    exit 73
fi

dpkg-query -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' \
    cuda-compiler-13-0 cuda-libraries-dev-13-0 ninja-build \
    >"$OUTPUT_DIR/packages-final.tsv" || true
apt-mark showmanual cuda-compiler-13-0 cuda-libraries-dev-13-0 \
    >"$OUTPUT_DIR/apt-manual-final.txt"
if rg '^cuda-compiler-13-0$' "$OUTPUT_DIR/apt-manual-final.txt"; then
    printf '%s\n' 'cuda-compiler-13-0 仍被本任务标记为手动安装' >&2
    exit 74
fi
rg '^cuda-libraries-dev-13-0$' "$OUTPUT_DIR/apt-manual-final.txt"

RUNTIME_ENV="$OUTPUT_DIR/cuda13-runtime.env.sh"
cat >"$RUNTIME_ENV" <<'ENV_EOF'
# RWKV/Mamba CUDA 扩展编译的项目级可复现环境。
export CUDA_HOME=/usr/local/cuda-13.0
export VIRTUAL_ENV=/root/autodl-tmp/thesis/experiments/llm_probe/.venv
export PATH="$VIRTUAL_ENV/bin:$CUDA_HOME/bin${PATH:+:${PATH}}"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
ENV_EOF
chmod 0644 "$RUNTIME_ENV"
source "$RUNTIME_ENV"

[[ "$CUDA_HOME" == "$CUDA_ROOT" ]]
[[ "$(command -v nvcc)" == "$CUDA_ROOT/bin/nvcc" ]]
[[ "$(command -v ninja)" == "$VENV_DIR/bin/ninja" ]]
[[ "$(ninja --version)" == 1.13.0* ]]

SOURCE_PATH="$OUTPUT_DIR/minimal_cuda_smoke.cu"
[[ "$(sha256sum "$SOURCE_PATH" | awk '{print $1}')" == 29c354755f46d08696c0a0a3c728ddc14ccfb16a23e7877552e2dbaa4dd9b7db ]]

FINAL_BUILD_PATH="$OUTPUT_DIR/build-project-env.ninja"
FINAL_BINARY_PATH="$OUTPUT_DIR/minimal_cuda_smoke_project_env"
[[ ! -e "$FINAL_BUILD_PATH" ]]
[[ ! -e "$FINAL_BINARY_PATH" ]]

cat >"$FINAL_BUILD_PATH" <<'NINJA_EOF'
nvcc = /usr/local/cuda-13.0/bin/nvcc

rule cuda_compile_and_link
  command = $nvcc -std=c++17 -O2 -lineinfo -arch=sm_120 $in -o $out
  description = NVCC $out

build minimal_cuda_smoke_project_env: cuda_compile_and_link minimal_cuda_smoke.cu

default minimal_cuda_smoke_project_env
NINJA_EOF

"$VENV_DIR/bin/ninja" -C "$OUTPUT_DIR" -f build-project-env.ninja -v \
    >"$OUTPUT_DIR/cuda-project-env-compile.log" 2>&1
timeout 60 "$FINAL_BINARY_PATH" \
    >"$OUTPUT_DIR/cuda-project-env-run.json" \
    2>"$OUTPUT_DIR/cuda-project-env-run.stderr"
rg -F '"status":"ok"' "$OUTPUT_DIR/cuda-project-env-run.json"
rg -F '"result":42' "$OUTPUT_DIR/cuda-project-env-run.json"
rg -F '"capability":"12.0"' "$OUTPUT_DIR/cuda-project-env-run.json"

"$PYTHON_BIN" -c 'import json, os, shutil, torch; from torch.utils.cpp_extension import CUDA_HOME; print(json.dumps({"env_cuda_home": os.environ.get("CUDA_HOME"), "nvcc": shutil.which("nvcc"), "ninja": shutil.which("ninja"), "torch": torch.__version__, "torch_cuda": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "device": torch.cuda.get_device_name(0), "capability": torch.cuda.get_device_capability(0), "cpp_extension_cuda_home": CUDA_HOME}))' \
    >"$OUTPUT_DIR/final-project-environment.json"
rg -F '"env_cuda_home": "/usr/local/cuda-13.0"' "$OUTPUT_DIR/final-project-environment.json"
rg -F '"nvcc": "/usr/local/cuda-13.0/bin/nvcc"' "$OUTPUT_DIR/final-project-environment.json"
rg -F '"ninja": "/root/autodl-tmp/thesis/experiments/llm_probe/.venv/bin/ninja"' "$OUTPUT_DIR/final-project-environment.json"
rg -F '"torch_cuda": "13.0"' "$OUTPUT_DIR/final-project-environment.json"
rg -F '"cpp_extension_cuda_home": "/usr/local/cuda-13.0"' "$OUTPUT_DIR/final-project-environment.json"

nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader \
    >"$OUTPUT_DIR/gpu-final.csv"
cmp "$OUTPUT_DIR/gpu-before.csv" "$OUTPUT_DIR/gpu-final.csv"
df -B1 / >"$OUTPUT_DIR/disk-root-final.txt"
df -B1 /root/autodl-tmp >"$OUTPUT_DIR/disk-data-final.txt"
sha256sum "$RUNTIME_ENV" "$FINAL_BUILD_PATH" "$FINAL_BINARY_PATH" \
    >"$OUTPUT_DIR/final-project-artifacts.sha256"

write_state finished ''
trap - ERR
