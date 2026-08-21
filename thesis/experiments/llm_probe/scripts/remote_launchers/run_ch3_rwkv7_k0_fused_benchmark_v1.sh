#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly BENCHMARK_ID=ch3-rwkv7-k0-fused-equivalence-speed-v1
readonly SCREEN_NAME=ch3-rwkv7-k0-fused-benchmark-v1
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-rwkv7-k0-fused-benchmark-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_rwkv7_k0_fused_benchmark.py"
readonly BACKEND_PATH="$PROJECT_ROOT/tools/rwkv7_k0_fused_backend.py"
readonly VENDOR_ROOT="$PROJECT_ROOT/vendor/rwkv7_k0_fused"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_rwkv7_k0_fused_benchmark_v1.sh"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$BENCHMARK_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$BENCHMARK_ID"

cd "$PROJECT_ROOT"
source tools/env/activate.sh

write_status() {
    local state=$1 stage=$2 exit_code=$3
    mkdir -p -- "$LAUNCHER_ROOT"
    local temporary="$LAUNCHER_ROOT/status.json.partial.$$"
    printf '{\n  "schema_version": "ch3-rwkv7-k0-fused-launcher-status-v1",\n  "benchmark_id": "%s",\n  "state": "%s",\n  "stage": "%s",\n  "exit_code": %s,\n  "target_year_paths_enumerated": 0\n}\n' \
        "$BENCHMARK_ID" "$state" "$stage" "$exit_code" > "$temporary"
    mv -- "$temporary" "$LAUNCHER_ROOT/status.json"
}

validate_files() {
    local path
    for path in \
        "$CONFIG_PATH" \
        "$TOOL_PATH" \
        "$BACKEND_PATH" \
        "$SCRIPT_PATH" \
        "$MEMORY_GATE_PATH" \
        "$VENDOR_ROOT/LICENSE" \
        "$VENDOR_ROOT/manifest.json" \
        "$VENDOR_ROOT/upstream/rwkv7_clampw.cpp" \
        "$VENDOR_ROOT/upstream/rwkv7_clampw.cu" \
        "$VENDOR_ROOT/derived/rwkv7_k0_clampw.cpp"; do
        [[ -s "$path" ]] || {
            printf '融合核基准文件缺失：%s\n' "$path" >&2
            return 67
        }
    done
}

validate_commands() {
    local command
    for command in rg uv screen flock nvidia-smi nvcc ninja sha256sum tee; do
        command -v "$command" >/dev/null 2>&1 || {
            printf '融合核基准缺少命令：%s\n' "$command" >&2
            return 69
        }
    done
}

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
    uv run --no-sync python "$BACKEND_PATH" --contract
}

record_inputs() {
    mkdir -p -- "$LAUNCHER_ROOT"
    sha256sum \
        "$CONFIG_PATH" \
        "$TOOL_PATH" \
        "$BACKEND_PATH" \
        "$SCRIPT_PATH" \
        "$VENDOR_ROOT/LICENSE" \
        "$VENDOR_ROOT/manifest.json" \
        "$VENDOR_ROOT/upstream/rwkv7_clampw.cpp" \
        "$VENDOR_ROOT/upstream/rwkv7_clampw.cu" \
        "$VENDOR_ROOT/derived/rwkv7_k0_clampw.cpp" \
        > "$LAUNCHER_ROOT/input-sha256.txt"
    printf 'uv run --no-sync python %s --config %s --phase all\n' \
        "$TOOL_PATH" "$CONFIG_PATH" > "$LAUNCHER_ROOT/benchmark-command.txt"
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

worker() {
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || {
        printf '融合核基准工作锁已占用。\n' >&2
        return 75
    }
    trap 'write_status interrupted signal 130; exit 130' HUP INT TERM
    validate_files
    validate_commands
    validate_static_contract
    uv run --no-sync python "$BACKEND_PATH" --validate-build-environment \
        > "$LAUNCHER_ROOT/build-environment.json"
    bash "$MEMORY_GATE_PATH" 20 "$BENCHMARK_ID" \
        > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1
    write_status running benchmark null
    local code=0
    if run_logged "$OUTPUT_ROOT/run.log" \
        uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --phase all; then
        code=0
    else
        code=$?
    fi
    if (( code != 0 )); then
        write_status failed benchmark "$code"
        return "$code"
    fi
    write_status finished complete 0
}

if [[ ${1:-} == --worker ]]; then
    worker
    exit $?
fi

if [[ $# -ne 0 ]]; then
    printf '本启动器不接受参数，唯一正式路径执行 all 阶段。\n' >&2
    exit 64
fi

validate_files
validate_commands
validate_static_contract
mkdir -p -- "$PROJECT_ROOT/runs/launchers/.locks" "$LAUNCHER_ROOT"
exec 8> "$PROJECT_ROOT/runs/launchers/.locks/$BENCHMARK_ID.lock"
flock -n 8 || {
    printf '融合核基准启动锁已占用。\n' >&2
    exit 75
}
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]" \
    || pgrep -f 'python.*[c]h3_rwkv7_k0_fused_benchmark.py' >/dev/null; then
    printf '同名融合核基准已运行。\n' >&2
    exit 75
fi
if [[ -e "$OUTPUT_ROOT" ]]; then
    printf '融合核基准运行根已存在，拒绝覆盖：%s\n' "$OUTPUT_ROOT" >&2
    exit 73
fi
mkdir -p -- "$OUTPUT_ROOT"
record_inputs
write_status prepared launch null
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'RWKV7_K0_FUSED_BENCHMARK_STARTED session=%s output=%s\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT"
