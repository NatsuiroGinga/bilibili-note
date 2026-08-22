#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly GATE_ID=ch3-rwkv-cuda-self-gate-v1
readonly SCREEN_NAME=ch3-rwkv-cuda-self-gate-v1
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-rwkv-cuda-self-gate-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_rwkv_cuda_self_gate.py"
readonly BACKEND_PATH="$PROJECT_ROOT/tools/rwkv7_k0_fused_backend.py"
readonly VENDOR_ROOT="$PROJECT_ROOT/vendor/rwkv7_k0_fused"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_rwkv_cuda_self_gate_v1.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$GATE_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$GATE_ID"
readonly FROZEN_CUDA_HOME=/usr/local/cuda

cd "$PROJECT_ROOT"
source tools/env/activate.sh

[[ -d "$FROZEN_CUDA_HOME" ]] || {
    printf '冻结CUDA工具链目录不存在：%s\n' "$FROZEN_CUDA_HOME" >&2
    exit 68
}
CUDA_HOME_RESOLVED=$(cd "$FROZEN_CUDA_HOME" && pwd -P)
readonly CUDA_HOME_RESOLVED
case "$CUDA_HOME_RESOLVED" in
    /usr/local/cuda | /usr/local/cuda-13.0) ;;
    *)
        printf '冻结CUDA工具链目录发生符号逃逸：%s -> %s\n' \
            "$FROZEN_CUDA_HOME" "$CUDA_HOME_RESOLVED" >&2
        exit 68
        ;;
esac
[[ -x "$FROZEN_CUDA_HOME/bin/nvcc" ]] || {
    printf '冻结nvcc不可执行：%s\n' "$FROZEN_CUDA_HOME/bin/nvcc" >&2
    exit 68
}
export CUDA_HOME="$FROZEN_CUDA_HOME"
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib64:${LD_LIBRARY_PATH:-}"

write_status() {
    local state=$1 stage=$2 exit_code=$3
    mkdir -p -- "$LAUNCHER_ROOT/status-history"
    local temporary="$LAUNCHER_ROOT/status.json.partial.$$"
    printf '{\n  "schema_version": "ch3-rwkv-cuda-self-gate-launcher-status-v1",\n  "gate_id": "%s",\n  "state": "%s",\n  "stage": "%s",\n  "exit_code": %s\n}\n' \
        "$GATE_ID" "$state" "$stage" "$exit_code" > "$temporary"
    mv -- "$temporary" "$LAUNCHER_ROOT/status.json"
    cp -- "$LAUNCHER_ROOT/status.json" \
        "$LAUNCHER_ROOT/status-history/$(date -u +%Y%m%dT%H%M%SZ)-$$-$state.json"
}

validate_files() {
    local path
    for path in \
        "$CONFIG_PATH" \
        "$TOOL_PATH" \
        "$BACKEND_PATH" \
        "$SCRIPT_PATH" \
        "$VENDOR_ROOT/LICENSE" \
        "$VENDOR_ROOT/manifest.json" \
        "$VENDOR_ROOT/upstream/rwkv7_clampw.cpp" \
        "$VENDOR_ROOT/upstream/rwkv7_clampw.cu" \
        "$VENDOR_ROOT/derived/rwkv7_k0_clampw.cpp"; do
        [[ -f "$path" && ! -L "$path" ]] || {
            printf 'CUDA-RWKV资格门文件缺失或为符号链接：%s\n' "$path" >&2
            return 67
        }
    done
}

validate_commands() {
    local command
    for command in rg uv screen flock sha256sum tee jq nvcc ninja c++; do
        command -v "$command" >/dev/null 2>&1 || {
            printf 'CUDA-RWKV资格门缺少命令：%s\n' "$command" >&2
            return 69
        }
    done
    [[ $(command -v nvcc) == "$CUDA_HOME/bin/nvcc" ]] || {
        printf 'nvcc解析路径不符：%s\n' "$(command -v nvcc)" >&2
        return 69
    }
}

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" --validate-config
    uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" --print-contract
    uv run --no-sync python "$BACKEND_PATH" --contract
}

record_identity() {
    mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
    local temporary="$LAUNCHER_ROOT/input-sha256.txt.partial.$$"
    sha256sum \
        configs/ch3-rwkv-cuda-self-gate-v1.json \
        tools/ch3_rwkv_cuda_self_gate.py \
        tools/rwkv7_k0_fused_backend.py \
        scripts/remote_launchers/run_ch3_rwkv_cuda_self_gate_v1.sh \
        vendor/rwkv7_k0_fused/LICENSE \
        vendor/rwkv7_k0_fused/manifest.json \
        vendor/rwkv7_k0_fused/upstream/rwkv7_clampw.cpp \
        vendor/rwkv7_k0_fused/upstream/rwkv7_clampw.cu \
        vendor/rwkv7_k0_fused/derived/rwkv7_k0_clampw.cpp \
        > "$temporary"
    mv -- "$temporary" "$LAUNCHER_ROOT/input-sha256.txt"
    sha256sum "$LAUNCHER_ROOT/input-sha256.txt" \
        | awk '{print $1}' > "$LAUNCHER_ROOT/input-identity-sha256.txt"
}

run_logged() {
    local log_path=$1
    shift
    mkdir -p -- "$(dirname "$log_path")"
    set +e
    "$@" 2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    printf '%s\n' "${pipeline_status[0]}" > "$log_path.command-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$log_path.tee-exit-code.txt"
    (( pipeline_status[1] == 0 )) || return "${pipeline_status[1]}"
    return "${pipeline_status[0]}"
}

worker_preflight() {
    validate_files
    validate_commands
    validate_static_contract
    record_identity
}

worker() {
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || {
        printf 'CUDA-RWKV资格门工作锁已占用。\n' >&2
        return 75
    }
    trap 'write_status interrupted signal 130; exit 130' HUP INT TERM
    local preflight_stamp preflight_log preflight_code
    preflight_stamp=$(date -u +%Y%m%dT%H%M%SZ)-$$
    preflight_log="$LAUNCHER_ROOT/logs/$preflight_stamp-preflight.log"
    preflight_code=0
    if run_logged "$preflight_log" worker_preflight; then
        preflight_code=0
    else
        preflight_code=$?
    fi
    if (( preflight_code != 0 )); then
        write_status failed preflight "$preflight_code"
        return "$preflight_code"
    fi
    local attempt_stamp log_path code
    attempt_stamp=$(date -u +%Y%m%dT%H%M%SZ)-$$
    log_path="$OUTPUT_ROOT/logs/$attempt_stamp.log"
    write_status running cuda-self-gate null
    code=0
    if run_logged "$log_path" uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" --run; then
        code=0
    else
        code=$?
    fi
    if (( code != 0 )); then
        write_status failed cuda-self-gate "$code"
        return "$code"
    fi
    jq -e '.passed == true' "$OUTPUT_ROOT/completion-receipt.json" >/dev/null
    write_status finished complete 0
}

if [[ ${1:-} == --worker ]]; then
    worker
    exit $?
fi

if [[ $# -ne 0 ]]; then
    printf '本启动器不接受参数，只执行固定自身资格门。\n' >&2
    exit 64
fi

validate_files
validate_commands
validate_static_contract
mkdir -p -- "$PROJECT_ROOT/runs/launchers/.locks" "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
exec 8> "$PROJECT_ROOT/runs/launchers/.locks/$GATE_ID.lock"
flock -n 8 || {
    printf 'CUDA-RWKV资格门启动锁已占用。\n' >&2
    exit 75
}
record_identity
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]" \
    || pgrep -f 'python.*[c]h3_rwkv_cuda_self_gate.py' >/dev/null; then
    printf '同名CUDA-RWKV资格门已运行。\n' >&2
    exit 75
fi
write_status prepared launch null
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'CUDA_RWKV_SELF_GATE_STARTED session=%s output=%s\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT"
