#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch4-entity-uniform-direct-ap-q0-seed42-v1-rerun2
readonly SCREEN_NAME=ch4-entity-ap-q0-s42-rerun2
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly STATUS_PATH="$OUTPUT_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch4-entity-uniform-direct-ap-q0-seed42-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch4_entity_uniform_direct_ap_q0.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch4_entity_uniform_direct_ap_q0_seed42_v1.sh"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=ns3-rwkv-lspr24

cd "$PROJECT_ROOT"
source tools/env/activate.sh

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    local root="$PROJECT_ROOT/runs/launchers/$RUN_ID"
    local status="$root/status.json"
    local partial="$status.partial.$$"
    mkdir -p -- "$root"
    uv run --no-sync python -c '
import json, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch4-entity-ap-launcher-status-v1",
    "run_id": sys.argv[2], "state": sys.argv[3], "stage": sys.argv[4],
    "detail": sys.argv[5], "exit_code": None if sys.argv[6] == "null" else int(sys.argv[6]),
    "updated_at_unix": time.time(), "screening_only": True,
    "formal_paper_evidence": False, "independent_test": False,
}
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
' "$partial" "$RUN_ID" "$state" "$stage" "$detail" "$exit_code"
    mv -f -- "$partial" "$status"
}

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
destination = config["swanlab"]
resources = config["resource_contract"]
valid = (
    destination["workspace"] == sys.argv[2]
    and destination["project"] == sys.argv[3]
    and resources["minimum_free_gpu_memory_gib"] == 18
    and resources["minimum_admitted_host_memory_gib"] == 40
    and config["paths"]["output_root"] == sys.argv[4]
)
raise SystemExit(0 if valid else 78)
' "$CONFIG_PATH" "$SWANLAB_WORKSPACE" "$SWANLAB_PROJECT" "$OUTPUT_ROOT"
}

validate_inputs() {
    uv run --no-sync python -c '
import json, pathlib, sys, zipfile
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
paths = config["paths"]
required = [paths["lspr23_zip"], paths["archived_c11_checkpoint"], paths["diagnostic_results"]]
required += [str(pathlib.Path(paths["cache_root"]) / f"{name}.npy") for name in ("X23", "y23", "I23", "M23", "X24", "y24", "I24", "M24", "s24", "d24")]
if any(not pathlib.Path(path).is_file() for path in required):
    raise SystemExit(66)
archive = pathlib.Path(paths["lspr23_zip"])
if archive.stat().st_size != config["input_contract"]["lspr23_zip_bytes"]:
    raise SystemExit(65)
with zipfile.ZipFile(archive) as handle:
    info = handle.getinfo(paths["lspr23_zip_member"])
if info.file_size != config["input_contract"]["lspr23_csv_uncompressed_bytes"]:
    raise SystemExit(65)
' "$CONFIG_PATH"
}

validate_resources() {
    bash "$MEMORY_GATE_PATH" 40 "$RUN_ID" > "$PROJECT_ROOT/runs/launchers/$RUN_ID/memory-admission-gate.log" 2>&1
    local free_mib
    free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1 | tr -d ' ')
    if [[ ! "$free_mib" =~ ^[0-9]+$ ]] || (( free_mib < 18432 )); then
        printf 'GPU 空闲显存不足 18 GiB：%s MiB\n' "$free_mib" >&2
        return 69
    fi
    nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu --format=csv,noheader,nounits \
        > "$PROJECT_ROOT/runs/launchers/$RUN_ID/gpu-resource.txt"
    local disk_fields
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    local available_kib used_percent
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    if [[ ! "$available_kib" =~ ^[0-9]+$ || ! "$used_percent" =~ ^[0-9]+$ ]] \
        || (( available_kib < 10485760 || used_percent >= 80 )); then
        printf '磁盘资源门失败：available_kib=%s used_percent=%s\n' \
            "$available_kib" "$used_percent" >&2
        return 69
    fi
    printf 'available_kib=%s\nused_percent=%s\n' "$available_kib" "$used_percent" \
        > "$PROJECT_ROOT/runs/launchers/$RUN_ID/disk-resource.txt"
}

run_plain_phase() {
    local phase=$1
    local log_path="$PROJECT_ROOT/runs/launchers/$RUN_ID/process-logs/$phase.log"
    mkdir -p -- "$(dirname "$log_path")"
    set +e
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" \
        --phase "$phase" \
        --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" \
        --authorized-swanlab-project "$SWANLAB_PROJECT" \
        2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$log_path.command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$log_path.tee-exit-code.txt"
    if [[ "$tee_code" -ne 0 ]]; then
        return "$tee_code"
    fi
    return "$command_code"
}

run_swanlab_preinit_gate() {
    local role=$1 attempt=$2
    local gate_root="$OUTPUT_ROOT/tracking-gates/$role/attempt-$attempt"
    mkdir -p -- "$gate_root"
    set +e
    uv run --no-sync swanlab ping > "$gate_root/swanlab-ping.log" 2>&1
    local ping_code=$?
    uv run --no-sync swanlab verify > "$gate_root/swanlab-verify.log" 2>&1
    local verify_code=$?
    set -e
    printf '%s\n' "$ping_code" > "$gate_root/swanlab-ping.exit-code.txt"
    printf '%s\n' "$verify_code" > "$gate_root/swanlab-verify.exit-code.txt"
}

run_tracking_attempt() {
    local role=$1 attempt=$2
    shift 2
    run_swanlab_preinit_gate "$role" "$attempt"
    local worker_root="$OUTPUT_ROOT/tracking-workers/$role"
    local worker_log="$worker_root/attempt-$attempt.log"
    mkdir -p -- "$worker_root"
    set +e
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" \
        "$@" --tracking-attempt "$attempt" \
        --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" \
        --authorized-swanlab-project "$SWANLAB_PROJECT" \
        2>&1 | tee "$worker_log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$worker_root/attempt-$attempt.command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$worker_root/attempt-$attempt.tee-exit-code.txt"
    if [[ "$tee_code" -ne 0 ]]; then
        return "$tee_code"
    fi
    return "$command_code"
}

run_tracking_role() {
    local role=$1
    shift
    local first_code
    if run_tracking_attempt "$role" 1 "$@"; then
        return 0
    else
        first_code=$?
    fi
    if [[ "$first_code" -ne 81 ]]; then
        return "$first_code"
    fi
    printf '%s\n' \
        "$role 首次 SwanLab init 返回 401，保留失败身份并仅在新进程重试一次。"
    run_tracking_attempt "$role" 2 "$@"
}

run_q0_pipeline() {
    run_plain_phase prepare
    local active_cells_text
    active_cells_text=$(uv run --no-sync python -c '
import json, pathlib, sys
plan = json.loads((pathlib.Path(sys.argv[1]) / "execution-plan.json").read_text(encoding="utf-8"))
print(" ".join(plan["active_cells"]))
' "$OUTPUT_ROOT")
    local active_cells=()
    read -r -a active_cells <<< "$active_cells_text"
    local cell
    for cell in "${active_cells[@]}"; do
        run_tracking_role "$cell" --phase cell --cell "$cell"
    done
    run_plain_phase finalize
    run_tracking_role aggregate --phase publish-aggregate
}

worker() {
    local launcher_root="$PROJECT_ROOT/runs/launchers/$RUN_ID"
    exec 9> "$launcher_root/worker.lock"
    if ! flock -n 9; then
        printf '同名运行锁已占用。\n' >&2
        return 75
    fi
    trap 'launcher_status interrupted signal received 130; exit 130' HUP INT TERM
    launcher_status running precheck started null
    validate_static_contract
    validate_inputs
    uv run --no-sync python -c 'import numpy, pyarrow, safetensors, sklearn, swanlab, torch; assert torch.cuda.is_available()' \
        > "$launcher_root/dependency-check.txt"
    validate_resources
    launcher_status running q0 started null
    set +e
    run_q0_pipeline 2>&1 | tee "$OUTPUT_ROOT/run.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$launcher_root/command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$launcher_root/tee-exit-code.txt"
    if [[ "$command_code" -ne 0 ]]; then
        launcher_status failed q0 command_failed "$command_code"
        return "$command_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        launcher_status failed q0 tee_failed "$tee_code"
        return "$tee_code"
    fi
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.loads((root / "status.json").read_text(encoding="utf-8"))
aggregate = json.loads((root / "aggregate-results.json").read_text(encoding="utf-8"))
allowed = {"COMPLETED_M_ONLY_DIAGNOSTIC", "COMPLETED_Q0_SUPPORTED", "COMPLETED_Q0_REJECTED"}
required = ("config.json", "input-hashes.json", "source-index-receipt.json", "lp-estimator-gate.json", "execution-plan.json", "sampling-receipt.json", "selection-seal.json", "aggregate-results.json", "resource-usage.json", "swanlab-receipt.json", "manifest.json", "status.json", "run.log")
valid = status.get("state") in allowed and status.get("exit_code") == 0 and aggregate.get("status") in allowed and all((root / name).is_file() for name in required)
raise SystemExit(0 if valid else 7)
' "$OUTPUT_ROOT"
    launcher_status finished complete q0_finished 0
}

worker_entry() {
    local launcher_root="$PROJECT_ROOT/runs/launchers/$RUN_ID"
    set +e
    worker 2>&1 | tee "$launcher_root/controller.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local worker_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$worker_code" > "$launcher_root/controller-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$launcher_root/controller-tee-exit-code.txt"
    if [[ "$worker_code" -ne 0 ]]; then
        launcher_status failed controller worker_failed "$worker_code"
        return "$worker_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        launcher_status failed controller tee_failed "$tee_code"
        return "$tee_code"
    fi
}

if [[ ${1:-} == --worker ]]; then
    worker_entry
    exit $?
fi
if [[ $# -ne 0 ]]; then
    printf '启动器不接受参数。\n' >&2
    exit 64
fi
for command in rg uv swanlab screen flock nvidia-smi sha256sum; do
    if ! command -v "$command" >/dev/null 2>&1; then
        printf '远端缺少命令：%s\n' "$command" >&2
        exit 69
    fi
done
for path in "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH"; do
    if [[ ! -s "$path" ]]; then
        printf '生产文件未完整同步：%s\n' "$path" >&2
        exit 67
    fi
done
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名持久会话已运行：%s\n' "$SCREEN_NAME" >&2
    exit 75
fi
if pgrep -f 'python.*[c]h4_entity_uniform_direct_ap_q0.py' >/dev/null; then
    printf '同名 Q0 进程已运行。\n' >&2
    exit 75
fi
if [[ -e "$OUTPUT_ROOT" ]]; then
    if [[ -s "$STATUS_PATH" ]] && uv run --no-sync python -c '
import json, pathlib, sys
status = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if status.get("exit_code") == 0 and str(status.get("state", "")).startswith("COMPLETED_") else 1)
' "$STATUS_PATH"; then
        printf '同名 Q0 已完成，不重复启动：%s\n' "$OUTPUT_ROOT"
        exit 0
    fi
    printf '同名输出根已存在且未合法完成，保留证据并阻断：%s\n' "$OUTPUT_ROOT" >&2
    exit 73
fi

readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
if [[ -e "$LAUNCHER_ROOT" ]]; then
    printf '同名启动器目录已存在，保留证据并阻断：%s\n' "$LAUNCHER_ROOT" >&2
    exit 73
fi
mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
validate_static_contract
validate_inputs
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH" > "$LAUNCHER_ROOT/input-sha256.txt"
launcher_status prepared launch static_contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'CH4_ENTITY_AP_Q0_STARTED session=%s output=%s cells=serial gpu_free_gate_gib=18 host_memory_gate_gib=40\n' "$SCREEN_NAME" "$OUTPUT_ROOT"
