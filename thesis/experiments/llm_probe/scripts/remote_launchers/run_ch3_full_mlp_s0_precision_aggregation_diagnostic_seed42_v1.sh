#!/usr/bin/env bash

set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-full-mlp-s0-precision-aggregation-diagnostic-seed42-v1
readonly DISPLAY_NAME='全容量多层感知机S0双精度双聚合空间零训练诊断'
readonly SCREEN_NAME=ch3-full-mlp-s0-prec-agg-s42-v1
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-full-mlp-s0-precision-aggregation-diagnostic-seed42-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_full_mlp_s0_precision_aggregation_diagnostic.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_full_mlp_s0_precision_aggregation_diagnostic_seed42_v1.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly RESOURCE_RECEIPT="$OUTPUT_ROOT/resource-receipt.json"
readonly RESOURCE_SAMPLES="$OUTPUT_ROOT/resource-samples.tsv"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly PARENT_RUN_ROOT="$PROJECT_ROOT/runs/diagnostics/ch3-full-mlp-complete-entity-lp-protocol-a-q0-seed42-v1-bf16-v1"
readonly CACHE_ROOT="$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache"
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=ns3-rwkv-lspr24
readonly GPU_FREE_MIN_MIB=20480
readonly CGROUP_AVAILABLE_MIN_BYTES=32212254720
readonly DISK_FREE_MIN_KIB=10485760
readonly MEMORY_GATE_GIB=30
readonly PEER_PATTERN='python.*[c]h3_full_mlp_s0_precision_aggregation_diagnostic[.]py'

mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
if [[ -r "$HOME/.bashrc" ]]; then
    # 本脚本用 set -Eeuo pipefail。`.bashrc` 第 9 行引用 PS1，而非交互 shell 没有该
    # 变量，`set -u` 会在 source 内部触发中止；`|| true` 只吞退出码，吞不掉这次中止。
    # 故加载期间临时关闭 nounset 与 errexit，加载完立即恢复。
    set +u +e
    source "$HOME/.bashrc" >> "$LAUNCHER_ROOT/shell-init.log" 2>&1 || true
    set -u -e
fi
cd "$PROJECT_ROOT"
source tools/env/activate.sh

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-full-mlp-s0-launcher-status-v1",
    "run_id": sys.argv[2], "display_name": sys.argv[3], "state": sys.argv[4],
    "stage": sys.argv[5], "detail": sys.argv[6],
    "exit_code": None if sys.argv[7] == "null" else int(sys.argv[7]),
    "updated_at_unix": time.time(),
    "training_runs": 0, "parameter_updates": 0, "new_checkpoints_written": 0,
    "per_flow_scores_persisted": False, "per_entity_scores_persisted": False,
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
parent = config["parent_selection"]
resources = config["resource_contract"]
isolation = config["isolation"]
valid = (
    config["run_id"] == sys.argv[2]
    and config["display_name"] == sys.argv[3]
    and config["paths"]["output_root"] == sys.argv[4]
    and config["paths"]["parent_run_root"] == sys.argv[5]
    and config["paths"]["cache_root"] == sys.argv[6]
    and config["tracking"]["workspace"] == sys.argv[7]
    and config["tracking"]["project"] == sys.argv[8]
    and config["tracking_lifecycle"]["maximum_online_init_attempts"] == 2
    and config["tracking_lifecycle"]["retry_exit_code"] == 91
    and config["tracking_lifecycle"]["second_attempt_requires_fresh_python_process"] is True
    and config["tracking_lifecycle"]["unknown_inflight_forbids_new_init"] is True
    and parent["run_id"] == "ch3-full-mlp-complete-entity-lp-protocol-a-q0-seed42-v1-bf16-v1"
    and list(parent["checkpoints"]) == ["B00", "B10", "O01", "O11"]
    and config["target_arrays"] == ["X24", "y24", "I24", "M24", "s24", "d24"]
    and isolation["training_runs"] == 0
    and isolation["parameter_updates"] == 0
    and isolation["new_checkpoints_written"] == 0
    and isolation["target_load_after_source_seal"] is True
    and isolation["independent_test"] is False
    and config["artifact_policy"]["persist_per_flow_scores"] is False
    and config["artifact_policy"]["persist_per_entity_scores"] is False
    and config["artifact_policy"]["persist_new_checkpoints"] is False
    and resources["minimum_free_gpu_memory_mib"] == 20480
    and resources["minimum_cgroup_available_memory_gib"] == 30
    and resources["minimum_free_disk_gib"] == 10
    and resources["wall_clock_limit"] is None
)
raise SystemExit(0 if valid else 78)
' "$CONFIG_PATH" "$RUN_ID" "$DISPLAY_NAME" "$OUTPUT_ROOT" "$PARENT_RUN_ROOT" "$CACHE_ROOT" \
        "$SWANLAB_WORKSPACE" "$SWANLAB_PROJECT"
}

validate_file_inventory() {
    local path cell name
    for path in "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH" \
        "$PARENT_RUN_ROOT/selection_frozen.json"; do
        [[ -r "$path" && -s "$path" ]] || {
            printf '生产输入缺失或不可读：%s\n' "$path" >&2
            return 66
        }
    done
    for cell in B00 B10 O01 O11; do
        path="$PARENT_RUN_ROOT/checkpoints/selected-${cell}.pt"
        [[ -r "$path" && -s "$path" ]] || {
            printf '封印检查点缺失或不可读：%s\n' "$path" >&2
            return 66
        }
    done
    for name in X23 y23 I23 M23 E23 T23 X24 y24 I24 M24 s24 d24; do
        path="$CACHE_ROOT/${name}.npy"
        [[ -r "$path" && -s "$path" ]] || {
            printf '冻结缓存缺失或不可读：%s\n' "$path" >&2
            return 66
        }
    done
}

tracking_gate() {
    local attempt=$1
    local gate_root="$OUTPUT_ROOT/swanlab-attempts/attempt-$attempt/tracking-gate" ping_code verify_code
    mkdir -p -- "$gate_root"
    if [[ -s "$gate_root/health-receipt.json" ]]; then
        uv run --no-sync python -c '
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if value.get("passed") is True and value.get("attempt") == int(sys.argv[2]) else 69)
' "$gate_root/health-receipt.json" "$attempt"
        return $?
    fi
    set +e
    uv run --no-sync swanlab ping > "$gate_root/swanlab-ping.log" 2>&1
    ping_code=$?
    uv run --no-sync swanlab verify > "$gate_root/swanlab-verify.log" 2>&1
    verify_code=$?
    set -e
    printf '%s\n' "$ping_code" > "$gate_root/swanlab-ping.exit-code.txt"
    printf '%s\n' "$verify_code" > "$gate_root/swanlab-verify.exit-code.txt"
    uv run --no-sync python -c '
import hashlib, json, os, pathlib, sys
path = pathlib.Path(sys.argv[1])
def record(filename):
    value = path.parent / filename
    payload = value.read_bytes()
    return {"relative_path": filename, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
receipt = {
    "schema_version": "ch3-full-mlp-s0-swanlab-health-v2",
    "run_id": sys.argv[2],
    "attempt": int(sys.argv[3]),
    "ping_exit_code": int(sys.argv[4]),
    "verify_exit_code": int(sys.argv[5]),
    "passed": int(sys.argv[4]) == 0 and int(sys.argv[5]) == 0,
    "logs": {"ping": record("swanlab-ping.log"), "verify": record("swanlab-verify.log")},
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$gate_root/health-receipt.json" "$RUN_ID" "$attempt" "$ping_code" "$verify_code"
    if (( ping_code != 0 || verify_code != 0 )); then
        printf 'SwanLab 前置门失败：ping=%s verify=%s\n' "$ping_code" "$verify_code" >&2
        return 15
    fi
}

swanlab_attempt_state() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1]) / "swanlab-attempts"
success = []
for attempt in (1, 2):
    path = root / f"attempt-{attempt}" / "success-receipt.json"
    if path.is_file():
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("completed") is True and value.get("attempt") == attempt:
            success.append(attempt)
if len(success) == 1:
    print(f"success:{success[0]}")
    raise SystemExit(0)
failure = root / "attempt-1" / "failure-receipt.json"
if failure.is_file():
    value = json.loads(failure.read_text(encoding="utf-8"))
    if value.get("retryable_zero_step_init_401") is True and value.get("attempt") == 1:
        print("retryable:2")
' "$OUTPUT_ROOT"
}

peer_process_count() {
    local count
    count=$(pgrep -fc "$PEER_PATTERN" || true)
    [[ "$count" =~ ^[0-9]+$ ]] || count=0
    printf '%s\n' "$count"
}

admit_resources() {
    mkdir -p -- "$OUTPUT_ROOT" "$LAUNCHER_ROOT"
    bash "$MEMORY_GATE_PATH" "$MEMORY_GATE_GIB" "$RUN_ID" > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1 \
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
    peer_count=$(peer_process_count)
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
    "schema_version": "ch3-full-mlp-s0-resource-v1",
    "run_id": sys.argv[2], "started_at_unix": time.time(), "finalized": False,
    "wall_clock_limit": None,
    "admission": {
        "minimum_free_gpu_memory_mib": 20480,
        "minimum_cgroup_available_memory_gib": 30,
        "minimum_free_disk_gib": 10,
        "gpu_free_mib": int(sys.argv[3]), "gpu_used_mib": int(sys.argv[4]),
        "cgroup_limit_bytes": int(sys.argv[5]), "cgroup_current_bytes": int(sys.argv[6]),
        "cgroup_available_bytes": int(sys.argv[7]), "disk_available_kib": int(sys.argv[8]),
        "disk_used_percent": int(sys.argv[9]), "actual_parallel_runs": 1,
    },
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$RESOURCE_RECEIPT" "$RUN_ID" "$free_mib" "$used_mib" "$cgroup_max" "$cgroup_current" \
        "$cgroup_available" "$available_kib" "$used_percent"
}

validate_admitted_resource_receipt() {
    uv run --no-sync python -c '
import json, pathlib, sys
value = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
admission = value.get("admission", {})
valid = (
    value.get("run_id") == sys.argv[2]
    and value.get("wall_clock_limit") is None
    and admission.get("minimum_free_gpu_memory_mib") == 20480
    and admission.get("minimum_cgroup_available_memory_gib") == 30
    and admission.get("minimum_free_disk_gib") == 10
    and admission.get("actual_parallel_runs") == 1
)
raise SystemExit(0 if valid else 69)
' "$RESOURCE_RECEIPT" "$RUN_ID"
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
        peer_count=$(peer_process_count)
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

stage_resume_flag() {
    local year=$1 matches
    matches=$(compgen -G "$OUTPUT_ROOT/unit-aggregates/$year/*.json" || true)
    if [[ -n "$matches" ]]; then
        printf '%s\n' "--resume"
    fi
    return 0
}

validate_outputs() {
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1]); manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
required = {
    "config.json", "input-validation-receipt-source.json", "input-validation-receipt-target.json",
    "s0-seal.json", "aggregate-results.json",
    "precision-receipt.json", "compute-resource-receipt.json", "resource-receipt.json",
    "swanlab-receipt.json", "swanlab-tag-receipt.json", "status.json",
}
attempt = json.loads((root / "swanlab-receipt.json").read_text(encoding="utf-8"))["attempt"]
attempt_root = f"swanlab-attempts/attempt-{attempt}"
required.update({
    f"{attempt_root}/inflight-receipt.json", f"{attempt_root}/success-receipt.json",
    f"{attempt_root}/swanlab-tag-receipt.json",
    f"{attempt_root}/tracking-gate/health-receipt.json",
    f"{attempt_root}/tracking-gate/swanlab-ping.log",
    f"{attempt_root}/tracking-gate/swanlab-verify.log",
})
for year in ("source", "target"):
    for cell in ("B00", "B10", "O01", "O11"):
        required.add(f"unit-aggregates/{year}/{cell}.json")
        required.add(f"curves/{year}/{cell}.npz")
        required.add(f"curves/{year}/{cell}-receipt.json")
valid = (
    manifest["run_id"] == sys.argv[2] and manifest["complete"] is True
    and manifest["training_runs"] == 0 and manifest["parameter_updates"] == 0
    and manifest["new_checkpoints_written"] == 0
    and manifest["per_flow_scores_persisted"] is False
    and manifest["per_entity_scores_persisted"] is False
    and manifest["per_entity_first_alert_persisted"] is False
    and manifest["exposure_matrix_persisted"] is False
    and manifest["complete_negative_tie_groups"] is True
    and manifest["time_delay_available"] is False
    and manifest["forbidden_artifacts_absent"] is True
    and required <= set(manifest["files"])
)
identity_paths = {
    "tool": pathlib.Path(sys.argv[3]), "config": pathlib.Path(sys.argv[4]),
    "launcher": pathlib.Path(sys.argv[5]), "tracking_module": pathlib.Path(sys.argv[6]),
    "tag_aliases": pathlib.Path(sys.argv[7]),
}
identities = manifest.get("production_identity", {})
valid = valid and set(identities) == set(identity_paths)
for key, path in identity_paths.items():
    payload = path.read_bytes()
    valid = valid and identities[key] == {
        "path": str(path.resolve()), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()
    }
current_names = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
valid = valid and current_names == set(manifest["files"]) | {"manifest.json"}
status = json.loads((root / "status.json").read_text(encoding="utf-8"))
results = json.loads((root / "aggregate-results.json").read_text(encoding="utf-8"))
valid = valid and status["state"] == "complete" and status["exit_code"] == 0
valid = valid and results["years_evaluated"] == ["source", "target"]
for name, receipt in manifest["files"].items():
    path = root / name
    valid = valid and path.is_file() and path.stat().st_size == receipt["bytes"]
    if path.is_file(): valid = valid and hashlib.sha256(path.read_bytes()).hexdigest() == receipt["sha256"]
raise SystemExit(0 if valid else 7)
' "$OUTPUT_ROOT" "$RUN_ID" "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" \
    "$PROJECT_ROOT/src/flow_probe/tracking.py" "$PROJECT_ROOT/configs/swanlab-tag-aliases-v1.json"
}

stop_monitor() {
    if [[ -n ${MONITOR_PID:-} ]]; then
        kill "$MONITOR_PID" 2>> "$LAUNCHER_ROOT/monitor-stop.log" || true
        wait "$MONITOR_PID" 2>> "$LAUNCHER_ROOT/monitor-stop.log" || true
        MONITOR_PID=
    fi
}

run_stage() {
    local stage=$1 detail=$2 code=0
    shift 2
    launcher_status running "$stage" "$detail" null
    set +e
    run_logged "$OUTPUT_ROOT/run-$stage.log" uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" --stage "$stage" "$@"
    code=$?
    set -e
    return "$code"
}

run_finalize_attempt() {
    local attempt=$1 code=0
    launcher_status running finalize "swanlab_attempt_$attempt" null
    set +e
    run_logged "$LAUNCHER_ROOT/finalize-attempt-$attempt.log" uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" --stage finalize --resume \
        --resource-receipt "$RESOURCE_RECEIPT" \
        --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" \
        --authorized-swanlab-project "$SWANLAB_PROJECT" \
        --swanlab-attempt "$attempt" \
        --swanlab-health-receipt \
        "$OUTPUT_ROOT/swanlab-attempts/attempt-$attempt/tracking-gate/health-receipt.json"
    code=$?
    set -e
    return "$code"
}

worker() {
    local code=0 resume_flag= swanlab_state=
    MONITOR_PID=
    CLEANUP_NEEDED=0
    trap '
        stop_monitor
        if (( ${CLEANUP_NEEDED:-0} == 1 )); then finalize_resources || true; fi
        launcher_status interrupted signal received 130
        exit 130
    ' HUP INT TERM
    validate_static_contract
    if [[ -s "$OUTPUT_ROOT/manifest.json" ]]; then
        validate_outputs
        launcher_status finished complete already_complete 0
        return 0
    fi
    validate_file_inventory
    validate_admitted_resource_receipt
    swanlab_state=$(swanlab_attempt_state)
    if [[ "$swanlab_state" == success:* ]]; then
        run_finalize_attempt "${swanlab_state#success:}"
        validate_outputs
        launcher_status finished complete s0_precision_aggregation_diagnostic_complete 0
        return 0
    fi
    if [[ "$swanlab_state" == retryable:2 ]]; then
        tracking_gate 2
        run_finalize_attempt 2
        validate_outputs
        launcher_status finished complete s0_precision_aggregation_diagnostic_complete 0
        return 0
    fi
    CLEANUP_NEEDED=1
    resource_monitor &
    MONITOR_PID=$!

    resume_flag=$(stage_resume_flag source)
    if run_stage source lspr23_four_checkpoints_two_precisions ${resume_flag:+$resume_flag}; then
        code=0
    else
        code=$?
        stop_monitor
        finalize_resources || true
        return "$code"
    fi
    if run_stage seal freeze_lesion_and_promotable_arm; then
        code=0
    else
        code=$?
        stop_monitor
        finalize_resources || true
        return "$code"
    fi
    resume_flag=$(stage_resume_flag target)
    if run_stage target lspr24_descriptive_after_seal ${resume_flag:+$resume_flag}; then
        code=0
    else
        code=$?
        stop_monitor
        finalize_resources || true
        return "$code"
    fi
    stop_monitor
    finalize_resources
    CLEANUP_NEEDED=0

    tracking_gate 1
    if run_finalize_attempt 1; then
        code=0
    else
        code=$?
    fi
    if (( code == 91 )); then
        tracking_gate 2
        run_finalize_attempt 2
    elif (( code != 0 )); then
        return "$code"
    fi
    validate_outputs
    launcher_status finished complete s0_precision_aggregation_diagnostic_complete 0
}

worker_entry() {
    local code
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || {
        printf '同名运行锁已占用。\n' >&2
        return 75
    }
    if [[ ! -s "$OUTPUT_ROOT/manifest.json" ]]; then
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

for command_name in uv swanlab screen flock nvidia-smi sha256sum rg awk df pgrep tee; do
    if ! resolved_path=$(command -v "$command_name"); then
        printf '缺少命令：%s\n' "$command_name" >&2
        exit 69
    fi
    printf '%s\t%s\n' "$command_name" "$resolved_path" >> "$LAUNCHER_ROOT/command-inventory.txt"
done
mkdir -p -- "$PROJECT_ROOT/runs/launchers/.locks"
exec 8> "$PROJECT_ROOT/runs/launchers/.locks/$RUN_ID.lock"
flock -n 8 || {
    printf '同名启动器锁已占用。\n' >&2
    exit 75
}
validate_static_contract
if [[ -s "$OUTPUT_ROOT/manifest.json" ]]; then
    validate_outputs
    printf 'CH3_FULL_MLP_S0_PRECISION_AGGREGATION_DIAGNOSTIC_ALREADY_COMPLETE run=%s\n' "$OUTPUT_ROOT"
    exit 0
fi
validate_file_inventory
screen_sessions=$(screen -ls || true)
if printf '%s\n' "$screen_sessions" | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名 S0 诊断已经启动。\n'
    exit 0
fi
if (( $(peer_process_count) > 0 )); then
    printf '同名 S0 诊断进程已经运行。\n' >&2
    exit 75
fi
launcher_status prepared launch queued null
sha256sum "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" \
    "$PARENT_RUN_ROOT/selection_frozen.json" \
    "$PARENT_RUN_ROOT/checkpoints/selected-B00.pt" \
    "$PARENT_RUN_ROOT/checkpoints/selected-B10.pt" \
    "$PARENT_RUN_ROOT/checkpoints/selected-O01.pt" \
    "$PARENT_RUN_ROOT/checkpoints/selected-O11.pt" > "$LAUNCHER_ROOT/input-sha256.txt"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'CH3_FULL_MLP_S0_PRECISION_AGGREGATION_DIAGNOSTIC_STARTED session=%s run=%s display=%s\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT" "$DISPLAY_NAME"
