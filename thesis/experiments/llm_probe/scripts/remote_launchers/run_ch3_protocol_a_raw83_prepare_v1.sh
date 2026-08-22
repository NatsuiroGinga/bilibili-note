#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-protocol-a-raw83-shared-v1
readonly DISPLAY_NAME=协议A训练区Raw83共享预处理
readonly SCREEN_NAME=ch3-protocol-a-raw83-shared-v1
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-protocol-a-raw83-shared-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_protocol_a_raw83_prepare.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_protocol_a_raw83_prepare_v1.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/data-prepared/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly LOG_PATH="$OUTPUT_ROOT/run.log"
readonly RESOURCE_SAMPLES="$OUTPUT_ROOT/resource-samples.tsv"

usage() {
    printf '%s\n' "用法：bash $SCRIPT_PATH [--help|--worker]"
    printf '%s\n' "默认启动持久会话，仅执行源年 P0-P5。"
}

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-protocol-a-raw83-launcher-status-v1",
    "run_id": sys.argv[2], "display_name": sys.argv[3], "state": sys.argv[4],
    "stage": sys.argv[5], "detail": sys.argv[6],
    "exit_code": None if sys.argv[7] == "null" else int(sys.argv[7]),
    "updated_at_unix": time.time(),
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$STATUS_PATH" "$RUN_ID" "$DISPLAY_NAME" "$state" "$stage" "$detail" "$exit_code"
}

run_logged() {
    local log_path=$1
    shift
    mkdir -p -- "$(dirname "$log_path")"
    set +e
    "$@" 2>&1 | tee -a "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    printf '%s\n' "${pipeline_status[0]}" > "$log_path.command-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$log_path.tee-exit-code.txt"
    ((pipeline_status[1] == 0)) || return "${pipeline_status[1]}"
    return "${pipeline_status[0]}"
}

resource_monitor() {
    printf 'unix_time\tcgroup_current_bytes\tdisk_available_kib\tdisk_used_percent\n' > "$RESOURCE_SAMPLES"
    while true; do
        local current=unavailable disk_fields available used
        if [[ -r /sys/fs/cgroup/memory.current ]]; then
            current=$(< /sys/fs/cgroup/memory.current)
        fi
        disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
        available=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
        used=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
        printf '%s\t%s\t%s\t%s\n' "$(date +%s)" "$current" "$available" "$used" >> "$RESOURCE_SAMPLES"
        sleep 30
    done
}

validate_static_contract() {
    for path in "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" \
        "$PROJECT_ROOT/src/flow_probe/protocol_a_raw83.py" \
        "$PROJECT_ROOT/src/flow_probe/protocol_a_preprocessing.py" \
        "$PROJECT_ROOT/vendor/rtdl_revisiting_models/manifest.json" \
        "$PROJECT_ROOT/vendor/rtdl_revisiting_models/LICENSE" \
        "$PROJECT_ROOT/vendor/rtdl_revisiting_models/lib/data.py"; do
        [[ -s "$path" && ! -L "$path" ]] || {
            printf '生产文件未完整同步或为符号链接：%s\n' "$path" >&2
            return 67
        }
    done
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
}

admit_resources() {
    local plan disk_fields available_kib used_percent required_bytes required_kib maximum_used
    plan=$(uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --print-resource-requirements)
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    required_bytes=$(printf '%s' "$plan" | uv run --no-sync python -c 'import json,sys; print(json.load(sys.stdin)["required_free_bytes"])')
    required_kib=$(((required_bytes + 1023) / 1024))
    maximum_used=$(uv run --no-sync python -c 'import json,sys; print(json.load(open(sys.argv[1]))["resources"]["maximum_disk_used_percent"])' "$CONFIG_PATH")
    if [[ ! "$available_kib" =~ ^[0-9]+$ || ! "$used_percent" =~ ^[0-9]+$ ]] \
        || ((available_kib < required_kib || used_percent >= maximum_used)); then
        printf '资源门失败：available_kib=%s required_kib=%s used_percent=%s maximum_used=%s\n' \
            "$available_kib" "$required_kib" "$used_percent" "$maximum_used" >&2
        return 69
    fi
    mkdir -p -- "$OUTPUT_ROOT/receipts"
    printf '%s\n' "$plan" > "$OUTPUT_ROOT/receipts/launcher-resource-admission.json"
}

worker() {
    local monitor_pid= code=0
    mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || {
        printf '同名运行锁已占用。\n' >&2
        return 75
    }
    trap '[[ -n ${monitor_pid:-} ]] && kill "$monitor_pid" 2>/dev/null || true; launcher_status interrupted signal received 130; exit 130' HUP INT TERM
    validate_static_contract
    admit_resources
    launcher_status running p0-p5 source-only-materialization-started null
    resource_monitor &
    monitor_pid=$!
    if run_logged "$LOG_PATH" uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --through-stage P5; then
        code=0
    else
        code=$?
    fi
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
    monitor_pid=
    if ((code != 0)); then
        launcher_status failed p0-p5 tool-exited "$code"
        return "$code"
    fi
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-product \
        > "$OUTPUT_ROOT/receipts/launcher-product-validation.json"
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.loads((root / "status.json").read_text(encoding="utf-8"))
manifest = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
valid = (
    status.get("state") == "finished" and status.get("sealed_through_stage") == "P5"
)
raise SystemExit(0 if valid else 7)
' "$OUTPUT_ROOT" "$PROJECT_ROOT/runs/data-prepared/$RUN_ID/generations/source-v1/dataset-manifest.json"
    launcher_status finished p5 source-only-materialization-sealed 0
}

if [[ ${1:-} == --help ]]; then
    usage
    exit 0
fi
if [[ ${1:-} == --worker ]]; then
    [[ $# -eq 1 ]] || { usage >&2; exit 64; }
    cd "$PROJECT_ROOT"
    source tools/env/activate.sh
    worker
    exit $?
fi
[[ $# -eq 0 ]] || { usage >&2; exit 64; }

cd "$PROJECT_ROOT"
source tools/env/activate.sh
for command in awk df flock rg screen sha256sum tee uv; do
    command -v "$command" >/dev/null 2>&1 || {
        printf '缺少命令：%s\n' "$command" >&2
        exit 69
    }
done
validate_static_contract
if [[ -s "$OUTPUT_ROOT/status.json" ]] && uv run --no-sync python -c '
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if value.get("state") == "finished" and value.get("sealed_through_stage") == "P5" else 1)
' "$OUTPUT_ROOT/status.json"; then
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-product >/dev/null
    printf '同名源年产品已完成，不重复启动：%s\n' "$OUTPUT_ROOT"
    exit 0
fi
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]" \
    || pgrep -f 'python.*[c]h3_protocol_a_raw83_prepare.py' >/dev/null; then
    printf '同名会话或进程已运行。\n' >&2
    exit 75
fi
mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf '已启动%s：screen -r %s\n' "$DISPLAY_NAME" "$SCREEN_NAME"
