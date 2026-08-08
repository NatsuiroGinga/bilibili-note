#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    printf '%s\n' '用法: bash install_cuda13_compiler_env.sh <params.json>' >&2
    exit 64
fi

PARAMS_PATH=$1
if [[ ! -f "$PARAMS_PATH" ]]; then
    printf '参数文件不存在: %s\n' "$PARAMS_PATH" >&2
    exit 66
fi

OUTPUT_DIR=$(jq -er '.output_dir' "$PARAMS_PATH")
PYTHON_BIN=$(jq -er '.python_bin' "$PARAMS_PATH")
EXPECTED_TORCH_CUDA=$(jq -er '.expected_torch_cuda' "$PARAMS_PATH")
CUDA_ROOT=$(jq -er '.cuda_root' "$PARAMS_PATH")
CUDA_REPO_BASE=$(jq -er '.cuda_repo_base' "$PARAMS_PATH")

case "$OUTPUT_DIR" in
    /root/autodl-tmp/thesis/experiments/llm_probe/runs/toolchain/*) ;;
    *)
        printf '非法输出目录: %s\n' "$OUTPUT_DIR" >&2
        exit 65
        ;;
esac

[[ "$PYTHON_BIN" == /root/autodl-tmp/thesis/experiments/llm_probe/.venv/bin/python ]]
[[ "$EXPECTED_TORCH_CUDA" == 13.0 ]]
[[ "$CUDA_ROOT" == /usr/local/cuda-13.0 ]]
[[ "$CUDA_REPO_BASE" == https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64 ]]

mkdir -p "$OUTPUT_DIR"
LOG_PATH="$OUTPUT_DIR/install.log"
exec >"$LOG_PATH" 2>&1

write_state() {
    local status=$1
    local reason=${2:-}
    local state_tmp="$OUTPUT_DIR/run_state.json.tmp"
    jq -n \
        --arg status "$status" \
        --arg reason "$reason" \
        --arg updated_at "$(date --iso-8601=seconds)" \
        '{status: $status, reason: $reason, updated_at: $updated_at}' >"$state_tmp"
    mv "$state_tmp" "$OUTPUT_DIR/run_state.json"
}

on_error() {
    local exit_code=$?
    write_state failed "安装脚本在第 ${BASH_LINENO[0]} 行退出，状态码 ${exit_code}"
    exit "$exit_code"
}
trap on_error ERR

exec 9>/var/lock/rwkv-cuda13-compiler-install.lock
if ! flock -n 9; then
    write_state failed '另一个 CUDA 13.0 编译环境安装正在运行'
    exit 75
fi

write_state running ''
printf '开始时间: %s\n' "$(date --iso-8601=seconds)"

source /etc/os-release
[[ "$ID" == ubuntu ]]
[[ "$VERSION_ID" == 22.04 ]]
[[ "$(dpkg --print-architecture)" == amd64 ]]

command -v rg
command -v fdfind
command -v uv
command -v jq
command -v curl
command -v gpg
command -v flock
command -v apt-get
command -v apt-cache

rg --version | head -n 1
fdfind --version
uv --version

if [[ ! -x "$PYTHON_BIN" ]]; then
    printf '正式 Python 不可执行: %s\n' "$PYTHON_BIN" >&2
    exit 69
fi

ACTUAL_TORCH_CUDA=$(
    "$PYTHON_BIN" -c 'import torch; print(torch.version.cuda or "")'
)
if [[ "$ACTUAL_TORCH_CUDA" != "$EXPECTED_TORCH_CUDA" ]]; then
    printf 'PyTorch CUDA 版本不符: 期望 %s，实际 %s\n' \
        "$EXPECTED_TORCH_CUDA" "$ACTUAL_TORCH_CUDA" >&2
    exit 78
fi

"$PYTHON_BIN" -c 'import torch; assert torch.cuda.is_available(); print(torch.__version__); print(torch.cuda.get_device_name(0)); print(torch.cuda.get_device_capability(0))'
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader \
    >"$OUTPUT_DIR/gpu-before.csv"
df -B1 / >"$OUTPUT_DIR/disk-root-before.txt"
df -B1 /root/autodl-tmp >"$OUTPUT_DIR/disk-data-before.txt"
dpkg-query -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' \
    cuda-compiler-13-0 cuda-libraries-dev-13-0 ninja-build \
    >"$OUTPUT_DIR/packages-before.tsv" || true

KEY_PATH="$OUTPUT_DIR/cuda-archive-keyring.gpg"
PIN_PATH="$OUTPUT_DIR/cuda-ubuntu2204.pin"
curl -fL --retry 3 --retry-delay 2 \
    "$CUDA_REPO_BASE/cuda-archive-keyring.gpg" \
    -o "$KEY_PATH"
curl -fL --retry 3 --retry-delay 2 \
    "$CUDA_REPO_BASE/cuda-ubuntu2204.pin" \
    -o "$PIN_PATH"
sha256sum "$KEY_PATH" "$PIN_PATH" >"$OUTPUT_DIR/repository-files.sha256"
gpg --show-keys --with-colons "$KEY_PATH" >"$OUTPUT_DIR/repository-key.txt"
rg '^fpr:::::::::EB693B3035CD5710E231E123A4B469963BF863CC:' \
    "$OUTPUT_DIR/repository-key.txt"

SOURCE_LIST=/etc/apt/sources.list.d/cuda-ubuntu2204-x86_64.list
SOURCE_LINE="deb [signed-by=/usr/share/keyrings/cuda-archive-keyring.gpg] $CUDA_REPO_BASE/ /"
if [[ -e "$SOURCE_LIST" ]] && ! rg -Fx "$SOURCE_LINE" "$SOURCE_LIST"; then
    printf '已有 NVIDIA CUDA 源配置与冻结值不一致: %s\n' "$SOURCE_LIST" >&2
    exit 73
fi

install -m 0644 "$KEY_PATH" /usr/share/keyrings/cuda-archive-keyring.gpg
install -m 0644 "$PIN_PATH" /etc/apt/preferences.d/cuda-repository-pin-600
printf '%s\n' "$SOURCE_LINE" >"$SOURCE_LIST"

apt-get update
apt-cache policy cuda-compiler-13-0 cuda-libraries-dev-13-0 ninja-build \
    >"$OUTPUT_DIR/apt-policy.txt"
rg -F "$CUDA_REPO_BASE" "$OUTPUT_DIR/apt-policy.txt"

CUDA_COMPILER_VERSION=$(apt-cache policy cuda-compiler-13-0 | awk '/Candidate:/ {print $2; exit}')
CUDA_LIBRARIES_DEV_VERSION=$(apt-cache policy cuda-libraries-dev-13-0 | awk '/Candidate:/ {print $2; exit}')
NINJA_VERSION=$(apt-cache policy ninja-build | awk '/Candidate:/ {print $2; exit}')

[[ "$CUDA_COMPILER_VERSION" == 13.0.* ]]
[[ "$CUDA_LIBRARIES_DEV_VERSION" == 13.0.* ]]
[[ "$NINJA_VERSION" != '(none)' ]]

SIMULATION_PATH="$OUTPUT_DIR/apt-simulate.txt"
DEBIAN_FRONTEND=noninteractive apt-get --simulate --no-install-recommends install \
    "cuda-compiler-13-0=$CUDA_COMPILER_VERSION" \
    "cuda-libraries-dev-13-0=$CUDA_LIBRARIES_DEV_VERSION" \
    "ninja-build=$NINJA_VERSION" \
    >"$SIMULATION_PATH"

if rg '^Remv ' "$SIMULATION_PATH"; then
    printf '%s\n' '安装模拟包含卸载操作，停止' >&2
    exit 74
fi

while IFS= read -r package_name; do
    case "$package_name" in
        cuda|cuda-13-0|cuda-toolkit|cuda-toolkit-13-0|nvidia-cuda-toolkit|cuda-drivers*|nvidia-driver-*|nvidia-open*|libnvidia-*)
            printf '安装模拟命中禁止软件包: %s\n' "$package_name" >&2
            exit 74
            ;;
    esac
done < <(awk '/^Inst / {print $2}' "$SIMULATION_PATH")

DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    "cuda-compiler-13-0=$CUDA_COMPILER_VERSION" \
    "cuda-libraries-dev-13-0=$CUDA_LIBRARIES_DEV_VERSION" \
    "ninja-build=$NINJA_VERSION"

PROFILE_TMP=$(mktemp)
cat >"$PROFILE_TMP" <<'PROFILE_EOF'
# CUDA 13.0 编译环境，不包含驱动安装。
export CUDA_HOME=/usr/local/cuda-13.0
export PATH="$CUDA_HOME/bin${PATH:+:${PATH}}"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
PROFILE_EOF
install -m 0644 "$PROFILE_TMP" /etc/profile.d/cuda-13-0.sh
rm -f "$PROFILE_TMP"

export CUDA_HOME="$CUDA_ROOT"
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"

nvcc --version >"$OUTPUT_DIR/nvcc-version.txt"
ninja --version >"$OUTPUT_DIR/ninja-version.txt"
"$PYTHON_BIN" -c 'import json, torch; from torch.utils.cpp_extension import CUDA_HOME; print(json.dumps({"torch": torch.__version__, "torch_cuda": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "device": torch.cuda.get_device_name(0), "capability": torch.cuda.get_device_capability(0), "cpp_extension_cuda_home": CUDA_HOME}))' \
    >"$OUTPUT_DIR/torch-after.json"

rg -F '"torch_cuda": "13.0"' "$OUTPUT_DIR/torch-after.json"
rg -F '"cpp_extension_cuda_home": "/usr/local/cuda-13.0"' "$OUTPUT_DIR/torch-after.json"

nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader \
    >"$OUTPUT_DIR/gpu-after.csv"
cmp "$OUTPUT_DIR/gpu-before.csv" "$OUTPUT_DIR/gpu-after.csv"
df -B1 / >"$OUTPUT_DIR/disk-root-after.txt"
df -B1 /root/autodl-tmp >"$OUTPUT_DIR/disk-data-after.txt"
dpkg-query -W -f='${binary:Package}\t${Version}\t${db:Status-Status}\n' \
    cuda-compiler-13-0 cuda-libraries-dev-13-0 ninja-build \
    >"$OUTPUT_DIR/packages-after.tsv"

write_state finished ''
trap - ERR
printf '完成时间: %s\n' "$(date --iso-8601=seconds)"
