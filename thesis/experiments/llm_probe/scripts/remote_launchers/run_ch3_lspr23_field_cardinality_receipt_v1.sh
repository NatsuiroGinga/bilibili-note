#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-lspr23-field-cardinality-receipt-v1
readonly SCREEN_NAME=ch3-lspr23-field-cardinality-receipt-v1
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-lspr23-field-cardinality-receipt-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_lspr23_field_cardinality_receipt.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_lspr23_field_cardinality_receipt_v1.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly RESOURCE_RECEIPT="$OUTPUT_ROOT/resource-receipt.json"
readonly RESOURCE_SAMPLES="$OUTPUT_ROOT/resource-samples.tsv"
readonly DISK_FREE_MIN_KIB=10485760

cd "$PROJECT_ROOT"
source tools/env/activate.sh
export CUDA_VISIBLE_DEVICES=0

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1]); value = {
    "schema_version": "ch3-lspr23-field-cardinality-launcher-status-v1",
    "run_id": sys.argv[2], "state": sys.argv[3], "stage": sys.argv[4],
    "detail": sys.argv[5], "exit_code": None if sys.argv[6] == "null" else int(sys.argv[6]),
    "updated_at_unix": time.time(), "execution_device": "cpu", "cuda_visible_devices": "0",
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); os.replace(temporary, path)
' "$LAUNCHER_ROOT/status.json" "$RUN_ID" "$state" "$stage" "$detail" "$exit_code"
}

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
valid = (
    config["run_id"] == sys.argv[2]
    and config["paths"]["output_root"] == sys.argv[3]
    and config["source_arrays"] == ["X23", "I23", "M23", "E23", "T23"]
    and config["target_year_arrays_read"] == 0 and config["source_year_only"] is True
    and config["resource_contract"]["execution_device"] == "cpu"
)
raise SystemExit(0 if valid else 78)
' "$CONFIG_PATH" "$RUN_ID" "$OUTPUT_ROOT"
}

validate_inputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")); root = pathlib.Path(config["paths"]["cache_root"])
names = config["source_arrays"]
raise SystemExit(0 if all((root / f"{name}.npy").is_file() for name in names) else 66)
' "$CONFIG_PATH"
}

admit_resources() {
    mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
    local disk_fields available_kib used_percent gpu_free_mib=unavailable
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    if [[ ! "$available_kib" =~ ^[0-9]+$ || ! "$used_percent" =~ ^[0-9]+$ ]] \
        || (( available_kib < DISK_FREE_MIN_KIB || used_percent >= 80 )); then
        printf '磁盘资源门失败：available_kib=%s used_percent=%s\n' "$available_kib" "$used_percent" >&2
        return 69
    fi
    if command -v nvidia-smi >/dev/null 2>&1; then
        gpu_free_mib=$(nvidia-smi --id=0 --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
    fi
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1]); value = {
    "schema_version": "ch3-lspr23-field-cardinality-resource-receipt-v1", "run_id": sys.argv[2],
    "execution_device": "cpu", "cuda_visible_devices": "0", "started_at_unix": time.time(),
    "disk_available_kib": int(sys.argv[3]), "disk_used_percent": int(sys.argv[4]), "gpu0_free_mib_at_admission": sys.argv[5],
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); os.replace(temporary, path)
' "$RESOURCE_RECEIPT" "$RUN_ID" "$available_kib" "$used_percent" "$gpu_free_mib"
}

resource_monitor() {
    printf 'unix_time\tcgroup_current_bytes\tgpu0_used_mib\n' > "$RESOURCE_SAMPLES"
    while true; do
        local cgroup_current=unavailable gpu_used=unavailable
        if [[ -r /sys/fs/cgroup/memory.current ]]; then cgroup_current=$(< /sys/fs/cgroup/memory.current); fi
        if command -v nvidia-smi >/dev/null 2>&1; then
            gpu_used=$(nvidia-smi --id=0 --query-gpu=memory.used --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
        fi
        printf '%s\t%s\t%s\n' "$(date +%s)" "$cgroup_current" "$gpu_used" >> "$RESOURCE_SAMPLES"
        sleep 5
    done
}

run_logged() {
    local log_path=$1; shift
    mkdir -p -- "$(dirname "$log_path")"
    set +e; "$@" 2>&1 | tee "$log_path"; local pipeline_status=("${PIPESTATUS[@]}"); set -e
    printf '%s\n' "${pipeline_status[0]}" > "$log_path.command-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$log_path.tee-exit-code.txt"
    (( pipeline_status[1] == 0 )) || return "${pipeline_status[1]}"
    return "${pipeline_status[0]}"
}

finalize_resources() {
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
receipt = pathlib.Path(sys.argv[1]); samples = pathlib.Path(sys.argv[2])
value = json.loads(receipt.read_text(encoding="utf-8")); rows = [line.split("\t") for line in samples.read_text(encoding="utf-8").splitlines()[1:] if line.count("\t") == 2]
value.update({"finished_at_unix": time.time(), "sample_interval_seconds": 5, "sample_count": len(rows)})
temporary = receipt.with_name(receipt.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); os.replace(temporary, receipt)
' "$RESOURCE_RECEIPT" "$RESOURCE_SAMPLES"
}

worker() {
    local monitor_pid= code=0
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || { printf '同名运行锁已占用。\n' >&2; return 75; }
    trap '[[ -n ${monitor_pid:-} ]] && kill "$monitor_pid" 2>/dev/null || true; launcher_status interrupted signal received 130; exit 130' HUP INT TERM
    validate_static_contract; validate_inputs; admit_resources
    launcher_status running cardinality_receipt source_only_scan_started null
    resource_monitor & monitor_pid=$!
    if run_logged "$OUTPUT_ROOT/run.log" uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH"; then code=0; else code=$?; fi
    kill "$monitor_pid" 2>/dev/null || true; wait "$monitor_pid" 2>/dev/null || true; monitor_pid=
    finalize_resources
    (( code == 0 )) || return "$code"
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1]); receipt = json.loads((root / "field-cardinality-receipt.json").read_text(encoding="utf-8")); status = json.loads((root / "status.json").read_text(encoding="utf-8"))
valid = receipt.get("complete") is True and receipt["identity"]["target_year_arrays_read"] == 0 and status.get("state") == "finished"
raise SystemExit(0 if valid else 7)
' "$OUTPUT_ROOT"
    launcher_status finished complete source_only_receipt_finished 0
}

if [[ ${1:-} == --worker ]]; then worker; exit $?; fi
[[ $# -eq 0 ]] || { printf '本启动器不接受参数。\n' >&2; exit 64; }
for command in rg uv screen flock sha256sum; do command -v "$command" >/dev/null 2>&1 || { printf '缺少命令：%s\n' "$command" >&2; exit 69; }; done
for path in "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH"; do [[ -s "$path" ]] || { printf '生产文件未完整同步：%s\n' "$path" >&2; exit 67; }; done
if [[ -s "$OUTPUT_ROOT/status.json" ]] && uv run --no-sync python -c 'import json, pathlib, sys; value=json.loads(pathlib.Path(sys.argv[1]).read_text()); raise SystemExit(0 if value.get("state") == "finished" and value.get("exit_code") == 0 else 1)' "$OUTPUT_ROOT/status.json"; then
    printf '同名收据已完成，不重复启动：%s\n' "$OUTPUT_ROOT"
    exit 0
fi
[[ ! -e "$LAUNCHER_ROOT" ]] || { printf '启动器证据目录已存在且未完成，拒绝覆盖。\n' >&2; exit 73; }
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]" || pgrep -f 'python.*[c]h3_lspr23_field_cardinality_receipt.py' >/dev/null; then
    printf '同名会话或进程已运行。\n' >&2; exit 75
fi
mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf '已启动 CPU 只读字段基数收据：screen -r %s\n' "$SCREEN_NAME"
