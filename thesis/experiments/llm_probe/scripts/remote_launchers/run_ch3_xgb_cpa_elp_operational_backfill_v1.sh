#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-xgb-cpa-elp-c11-operational-backfill-v1-rerun1
readonly DISPLAY_NAME='XGBoost＋CPA-ELP C11目标年完整运营指标零训练回填'
readonly SCREEN_NAME=ch3-xgb-c11-op-backfill-r1
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-xgb-cpa-elp-operational-backfill-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_xgb_cpa_elp_operational_backfill.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_xgb_cpa_elp_operational_backfill_v1.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly RESOURCE_RECEIPT="$OUTPUT_ROOT/resource-receipt.json"
readonly RESOURCE_SAMPLES="$OUTPUT_ROOT/resource-samples.tsv"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly PARENT_RUN_ROOT="$PROJECT_ROOT/runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
readonly PARENT_EVAL_ROOT="$PROJECT_ROOT/runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2"
readonly RECOVERY_PROOF="$PROJECT_ROOT/runs/recovery/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-for-ch4-xgb-pbc-q0-seed42-v1-rerun2-v1/parent-recovery-proof.json"
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=ns3-rwkv-lspr24
readonly GPU_FREE_MIN_MIB=11264
readonly CGROUP_AVAILABLE_MIN_BYTES=51539607552
readonly DISK_FREE_MIN_KIB=10485760
readonly PEER_PATTERN='python.*[c]h3_xgb_cpa_elp_operational_backfill[.]py.*--compute'

cd "$PROJECT_ROOT"
source tools/env/activate.sh

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-xgb-cpa-elp-operational-backfill-launcher-status-v1",
    "run_id": sys.argv[2], "display_name": sys.argv[3], "state": sys.argv[4],
    "stage": sys.argv[5], "detail": sys.argv[6],
    "exit_code": None if sys.argv[7] == "null" else int(sys.argv[7]),
    "updated_at_unix": time.time(), "target_retrained": False,
    "target_score_calls": 1, "target_scores_persisted": False,
    "wall_clock_limit": None,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$LAUNCHER_ROOT/status.json" "$RUN_ID" "$DISPLAY_NAME" "$state" "$stage" "$detail" "$exit_code"
}

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
parent = config["parent_contract"]
resources = config["resource_contract"]
valid = (
    config["run_id"] == sys.argv[2]
    and config["display_name"] == sys.argv[3]
    and config["target_arrays"] == ["X24", "y24", "I24", "M24", "s24", "d24", "t24"]
    and parent["run_id"] == "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
    and parent["selected_adapter"] == "semantic168"
    and parent["power_mean_p"] == 1.0
    and parent["num_boost_round"] == 800
    and parent["semantic168_model_sha256"] == "1805e15d96ac4ebb57df910640a4c5e1af58f692659db2eb80b724851efe42e9"
    and parent["target_retrained"] is False
    and parent["target_score_calls"] == 1
    and parent["target_scores_persisted"] is False
    and resources["minimum_free_gpu_memory_gib"] == 11
    and resources["minimum_cgroup_available_memory_gib"] == 48
    and resources["minimum_free_disk_gib"] == 10
    and resources["wall_clock_limit"] is None
    and config["artifact_policy"]["persist_per_flow_scores"] is False
    and config["artifact_policy"]["persist_per_entity_scores"] is False
    and config["paths"]["output_root"] == sys.argv[4]
    and config["tracking"]["workspace"] == sys.argv[5]
    and config["tracking"]["project"] == sys.argv[6]
)
raise SystemExit(0 if valid else 78)
' "$CONFIG_PATH" "$RUN_ID" "$DISPLAY_NAME" "$OUTPUT_ROOT" "$SWANLAB_WORKSPACE" "$SWANLAB_PROJECT"
}

validate_file_inventory() {
    local path cache_name
    for path in "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH" \
        "$PARENT_RUN_ROOT/selection_frozen_xgb2x2.json" \
        "$PARENT_RUN_ROOT/effective_config_receipts.json" \
        "$PARENT_RUN_ROOT/model_semantic168.json" \
        "$PARENT_EVAL_ROOT/xgb_cpa_elp_results.json" \
        "$PARENT_EVAL_ROOT/manifest.json" "$PARENT_EVAL_ROOT/status.json" \
        "$RECOVERY_PROOF"; do
        [[ -r "$path" && -s "$path" ]] || {
            printf '生产输入缺失或不可读：%s\n' "$path" >&2
            return 66
        }
    done
    for cache_name in X24 y24 I24 M24 s24 d24 t24; do
        path="$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/${cache_name}.npy"
        [[ -r "$path" && -s "$path" ]] || {
            printf '目标缓存缺失或不可读：%s\n' "$path" >&2
            return 66
        }
    done
}

tracking_gate() {
    local gate_root="$LAUNCHER_ROOT/tracking-gates/attempt-1" ping_code verify_code
    mkdir -p -- "$gate_root"
    set +e
    uv run --no-sync swanlab ping > "$gate_root/swanlab-ping.log" 2>&1
    ping_code=$?
    uv run --no-sync swanlab verify > "$gate_root/swanlab-verify.log" 2>&1
    verify_code=$?
    set -e
    printf '%s\n' "$ping_code" > "$gate_root/swanlab-ping.exit-code.txt"
    printf '%s\n' "$verify_code" > "$gate_root/swanlab-verify.exit-code.txt"
    if (( ping_code != 0 || verify_code != 0 )); then
        printf 'SwanLab 前置门失败：ping=%s verify=%s\n' "$ping_code" "$verify_code" >&2
        return 15
    fi
}

admit_resources() {
    mkdir -p -- "$OUTPUT_ROOT" "$LAUNCHER_ROOT"
    bash "$MEMORY_GATE_PATH" 48 "$RUN_ID" > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1 \
        || return $?
    local free_mib used_mib cgroup_max cgroup_current cgroup_available
    local disk_fields available_kib used_percent peer_count
    free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
    used_mib=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
    if [[ -r /sys/fs/cgroup/memory.max ]]; then
        cgroup_max=$(< /sys/fs/cgroup/memory.max)
        cgroup_current=$(< /sys/fs/cgroup/memory.current)
    elif [[ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]]; then
        cgroup_max=$(< /sys/fs/cgroup/memory/memory.limit_in_bytes)
        cgroup_current=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
    else
        printf '无法读取控制组主存，拒绝启动。\n' >&2
        return 69
    fi
    if [[ ! "$free_mib" =~ ^[0-9]+$ || ! "$used_mib" =~ ^[0-9]+$ \
        || ! "$cgroup_max" =~ ^[0-9]+$ || ! "$cgroup_current" =~ ^[0-9]+$ ]]; then
        printf '资源读数无效，拒绝启动。\n' >&2
        return 69
    fi
    cgroup_available=$((cgroup_max - cgroup_current))
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    peer_count=$(pgrep -fc "$PEER_PATTERN" 2>/dev/null || true)
    if (( free_mib < GPU_FREE_MIN_MIB || cgroup_available < CGROUP_AVAILABLE_MIN_BYTES \
        || available_kib < DISK_FREE_MIN_KIB || used_percent >= 80 || peer_count > 0 )); then
        printf '资源门失败：GPU空闲=%sMiB，控制组可用=%s字节，磁盘可用=%sKiB，使用率=%s%%，同任务=%s。\n' \
            "$free_mib" "$cgroup_available" "$available_kib" "$used_percent" "$peer_count" >&2
        return 69
    fi
    nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu --format=csv,noheader,nounits \
        > "$LAUNCHER_ROOT/gpu-resource.txt"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-xgb-cpa-elp-operational-backfill-resource-v1",
    "run_id": sys.argv[2], "started_at_unix": time.time(), "finalized": False,
    "wall_clock_limit": None,
    "admission": {
        "minimum_free_gpu_memory_gib": 11,
        "minimum_cgroup_available_memory_gib": 48,
        "minimum_free_disk_gib": 10,
        "gpu_free_mib": int(sys.argv[3]), "gpu_used_mib": int(sys.argv[4]),
        "cgroup_limit_bytes": int(sys.argv[5]), "cgroup_current_bytes": int(sys.argv[6]),
        "cgroup_available_bytes": int(sys.argv[7]), "disk_available_kib": int(sys.argv[8]),
        "disk_used_percent": int(sys.argv[9]), "parallel_compute_units": 1,
    },
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$RESOURCE_RECEIPT" "$RUN_ID" "$free_mib" "$used_mib" "$cgroup_max" "$cgroup_current" \
        "$cgroup_available" "$available_kib" "$used_percent"
}

resource_monitor() {
    printf 'unix_time\tgpu_used_mib\tcgroup_current_bytes\tpeer_job_running\n' > "$RESOURCE_SAMPLES"
    while true; do
        local gpu_used cgroup_current peer_job_running=0 peer_count
        gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
        if [[ -r /sys/fs/cgroup/memory.current ]]; then
            cgroup_current=$(< /sys/fs/cgroup/memory.current)
        else
            cgroup_current=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
        fi
        peer_count=$(pgrep -fc "$PEER_PATTERN" 2>/dev/null || true)
        (( peer_count > 1 )) && peer_job_running=1
        printf '%s\t%s\t%s\t%s\n' "$(date +%s)" "$gpu_used" "$cgroup_current" "$peer_job_running" >> "$RESOURCE_SAMPLES"
        sleep 5
    done
}

finalize_resources() {
    [[ -s "$RESOURCE_RECEIPT" && -s "$RESOURCE_SAMPLES" ]] || return 1
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
receipt = pathlib.Path(sys.argv[1]); samples = pathlib.Path(sys.argv[2])
value = json.loads(receipt.read_text(encoding="utf-8"))
rows = [tuple(map(int, line.split("\t"))) for line in samples.read_text(encoding="utf-8").splitlines()[1:] if line.count("\t") == 3]
if not rows: raise SystemExit("资源采样为空")
value.update({
    "finished_at_unix": time.time(), "finalized": True, "sample_interval_seconds": 5,
    "sample_count": len(rows), "peak_gpu_used_mib": max(row[1] for row in rows),
    "peak_cgroup_current_bytes": max(row[2] for row in rows),
    "resource_measurement_contended": any(row[3] for row in rows),
    "fair_efficiency_evidence": not any(row[3] for row in rows),
    "wall_clock_limit": None,
})
temporary = receipt.with_name(receipt.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, receipt)
' "$RESOURCE_RECEIPT" "$RESOURCE_SAMPLES"
}

validate_admitted_resource_receipt() {
    uv run --no-sync python -c '
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
value = json.loads(path.read_text(encoding="utf-8"))
admission = value.get("admission", {})
valid = (
    value.get("run_id") == sys.argv[2]
    and value.get("finalized") is False
    and value.get("wall_clock_limit") is None
    and admission.get("minimum_free_gpu_memory_gib") == 11
    and admission.get("minimum_cgroup_available_memory_gib") == 48
    and admission.get("minimum_free_disk_gib") == 10
    and admission.get("parallel_compute_units") == 1
)
raise SystemExit(0 if valid else 69)
' "$RESOURCE_RECEIPT" "$RUN_ID"
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

validate_outputs() {
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1]); manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
required = {
    "config.json", "input-validation-receipt.json", "target-year-metrics.json",
    "complete-alert-budget-curves.npz", "complete-alert-budget-curves-receipt.json",
    "first-alert-timing-curves.npz", "first-alert-timing-receipt.json",
    "compute-complete-receipt.json", "resource-receipt.json", "swanlab-receipt.json",
    "operational-backfill-receipt.json", "stage-status.json",
}
valid = (
    manifest["run_id"] == sys.argv[2] and manifest["complete"] is True
    and manifest["target_retrained"] is False and manifest["target_score_calls"] == 1
    and manifest["target_scores_persisted"] is False
    and manifest["per_entity_scores_persisted"] is False
    and manifest["per_entity_first_alert_persisted"] is False
    and manifest["complete_negative_tie_groups"] is True
    and manifest["time_delay_available"] is False
    and required <= set(manifest["files"])
    and manifest["forbidden_artifacts_absent"] is True
)
for name, receipt in manifest["files"].items():
    path = root / name
    valid = valid and path.is_file() and path.stat().st_size == receipt["bytes"]
    if path.is_file(): valid = valid and hashlib.sha256(path.read_bytes()).hexdigest() == receipt["sha256"]
raise SystemExit(0 if valid else 7)
' "$OUTPUT_ROOT" "$RUN_ID"
}

worker() {
    local monitor_pid= code=0 resume_flag= cleanup_needed=0
    trap '
        if [[ -n ${monitor_pid:-} ]]; then kill "$monitor_pid" 2>/dev/null || true; wait "$monitor_pid" 2>/dev/null || true; fi
        if (( ${cleanup_needed:-0} == 1 )); then finalize_resources || true; fi
        launcher_status interrupted signal received 130
        exit 130
    ' HUP INT TERM
    validate_static_contract
    if [[ -s "$OUTPUT_ROOT/manifest.json" ]]; then
        uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --finalize \
            --resource-receipt "$RESOURCE_RECEIPT" --resume
        validate_outputs
        launcher_status finished complete already_complete 0
        return 0
    fi
    validate_file_inventory
    tracking_gate
    [[ -s "$OUTPUT_ROOT/compute-complete-receipt.json" ]] && resume_flag=--resume
    if [[ -z "$resume_flag" ]]; then
        validate_admitted_resource_receipt
        cleanup_needed=1
        resource_monitor &
        monitor_pid=$!
        launcher_status running compute semantic168_once_gpu_score_once null
        if run_logged "$OUTPUT_ROOT/run-compute.log" uv run --no-sync python "$TOOL_PATH" \
            --config "$CONFIG_PATH" --compute; then
            code=0
        else
            code=$?
        fi
        kill "$monitor_pid" 2>/dev/null || true
        wait "$monitor_pid" 2>/dev/null || true
        monitor_pid=
        finalize_resources
        cleanup_needed=0
        (( code == 0 )) || return "$code"
    else
        uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --compute --resume
        if [[ ! -s "$RESOURCE_RECEIPT" ]] || ! uv run --no-sync python -c '
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
raise SystemExit(0 if path.is_file() and json.loads(path.read_text())["finalized"] is True else 1)
' "$RESOURCE_RECEIPT"; then
            finalize_resources
        fi
    fi
    launcher_status running finalize resource_and_tracking_publish null
    run_logged "$OUTPUT_ROOT/run-finalize.log" uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" --finalize --resource-receipt "$RESOURCE_RECEIPT" --resume
    validate_outputs
    launcher_status finished complete operational_backfill_complete 0
}

worker_entry() {
    local code
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || {
        printf '同名运行锁已占用。\n' >&2
        return 75
    }
    if [[ ! -s "$OUTPUT_ROOT/manifest.json" \
        && ! -s "$OUTPUT_ROOT/compute-complete-receipt.json" ]]; then
        launcher_status running resource_gate checking_live_resources_before_controller_tee null
        set +e
        admit_resources
        code=$?
        set -e
        if (( code != 0 )); then
            launcher_status failed resource_gate admission_failed_before_controller_tee "$code"
            return "$code"
        fi
    fi
    set +e
    worker 2>&1 | tee "$LAUNCHER_ROOT/controller.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    code=${pipeline_status[0]}
    (( code != 0 || pipeline_status[1] == 0 )) || code=${pipeline_status[1]}
    if (( code != 0 )); then
        launcher_status failed controller worker_or_tee_failed "$code"
        return "$code"
    fi
}

if [[ ${1:-} == --worker && $# -eq 1 ]]; then
    worker_entry
    exit $?
fi
if [[ $# -ne 0 ]]; then
    printf '启动器不接受外部参数。\n' >&2
    exit 64
fi

for command in uv swanlab screen flock nvidia-smi sha256sum rg awk df pgrep; do
    command -v "$command" >/dev/null 2>&1 || {
        printf '缺少命令：%s\n' "$command" >&2
        exit 69
    }
done
mkdir -p -- "$PROJECT_ROOT/runs/launchers/.locks" "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
exec 8> "$PROJECT_ROOT/runs/launchers/.locks/$RUN_ID.lock"
flock -n 8 || {
    printf '同名启动器锁已占用。\n' >&2
    exit 75
}
validate_static_contract
if [[ -s "$OUTPUT_ROOT/manifest.json" ]]; then
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --finalize \
        --resource-receipt "$RESOURCE_RECEIPT" --resume
    validate_outputs
    printf 'XGBOOST_CPA_ELP_OPERATIONAL_BACKFILL_ALREADY_COMPLETE run=%s\n' "$OUTPUT_ROOT"
    exit 0
fi
validate_file_inventory
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名运营回填已经启动。\n'
    exit 0
fi
if pgrep -f "$PEER_PATTERN" >/dev/null 2>&1; then
    printf '同名运营回填进程已经运行。\n' >&2
    exit 75
fi
launcher_status prepared launch queued null
sha256sum "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" \
    "$PARENT_RUN_ROOT/selection_frozen_xgb2x2.json" \
    "$PARENT_RUN_ROOT/effective_config_receipts.json" \
    "$PARENT_RUN_ROOT/model_semantic168.json" \
    "$PARENT_EVAL_ROOT/xgb_cpa_elp_results.json" "$PARENT_EVAL_ROOT/manifest.json" \
    "$RECOVERY_PROOF" > "$LAUNCHER_ROOT/input-sha256.txt"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'XGBOOST_CPA_ELP_OPERATIONAL_BACKFILL_STARTED session=%s run=%s display=%s\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT" "$DISPLAY_NAME"
