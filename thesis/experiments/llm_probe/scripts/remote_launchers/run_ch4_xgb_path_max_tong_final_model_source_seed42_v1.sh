#!/usr/bin/env bash
source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch4-xgb-path-max-tong-final-model-source-seed42-v1-rerun2
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch4_xgb_path_max_tong_final_model_source_seed42.py"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch4-xgb-path-max-tong-final-model-source-seed42-v1.json"
readonly PARENT_CONFIG_PATH="$PROJECT_ROOT/configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch4_xgb_path_max_tong_final_model_source_seed42_v1.sh"
readonly PARENT_RUN_ID=ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1
readonly PARENT_RUN_ROOT="$PROJECT_ROOT/runs/diagnostics/$PARENT_RUN_ID"
readonly MODEL_NAME=model_semantic168_final_source_seed42.json
readonly RUN_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly RESUME_RUN_ROOT="$PROJECT_ROOT/runs/candidates/ch4-xgb-path-max-tong-final-model-source-seed42-v1-rerun1"
readonly LAUNCH_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$RUN_ROOT/status.json"
readonly HOST_ADMISSION_GIB=20.0
readonly GPU_FLOOR_MIB=20480

write_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    printf '{"run_id":"%s","source_year":"LSPR23","seed":42,"target_year_arrays_read":0,"state":"%s","stage":"%s","detail":"%s","exit_code":%s}\n' \
        "$RUN_ID" "$state" "$stage" "$detail" "$exit_code" > "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

write_resource_receipt() {
    local memory_max=$1 memory_current=$2 available_gib=$3 disk_available_mib=$4
    local gpu_free_mib=$5 admission_exit=$6 passed=$7
    local partial="$RUN_ROOT/launcher-resource-receipt.json.partial.$$"
    printf '{"schema_version":"ch4-xgb-path-max-tong-final-model-launcher-resource-v1","estimated_wall_minutes":[5,10],"estimated_peak_host_gib":17.0,"host_admission_gib":20.0,"estimated_peak_gpu_gib":18.0,"required_gpu_count":1,"required_gpu_memory_class_gib":24,"cgroup_memory_max_bytes":%s,"cgroup_memory_current_bytes":%s,"cgroup_available_gib":%s,"disk_available_mib":%s,"gpu_free_mib":%s,"memory_admission_exit":%s,"passed":%s}\n' \
        "$memory_max" "$memory_current" "$available_gib" "$disk_available_mib" \
        "$gpu_free_mib" "$admission_exit" "$passed" > "$partial"
    mv -f -- "$partial" "$RUN_ROOT/launcher-resource-receipt.json"
}

resource_gate() {
    local memory_max memory_current available_gib disk_available_mib gpu_free_mib admission_exit
    memory_max=$(< /sys/fs/cgroup/memory.max)
    memory_current=$(< /sys/fs/cgroup/memory.current)
    if [[ -z "$memory_max" || "$memory_max" == max ]]; then
        write_status failed resource_gate cgroup_limit_unavailable 12
        return 12
    fi
    available_gib=$(awk -v m="$memory_max" -v c="$memory_current" 'BEGIN {printf "%.2f", (m-c)/1073741824}')
    disk_available_mib=$(df -Pk "$PROJECT_ROOT" | awk 'NR==2 {printf "%d", $4/1024}')
    gpu_free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR==1 {print $1}')

    set +e
    bash "$PROJECT_ROOT/tools/memory_admission_gate.sh" "$HOST_ADMISSION_GIB" "$RUN_ID" \
        > "$RUN_ROOT/memory-admission-gate.log" 2>&1
    admission_exit=$?
    set -e
    if [[ "$admission_exit" -ne 0 ]]; then
        write_resource_receipt "$memory_max" "$memory_current" "$available_gib" \
            "$disk_available_mib" "$gpu_free_mib" "$admission_exit" false
        write_status failed resource_gate memory_admission_failed "$admission_exit"
        return "$admission_exit"
    fi
    if ! awk -v a="$available_gib" 'BEGIN {exit !(a >= 22.0)}'; then
        write_resource_receipt "$memory_max" "$memory_current" "$available_gib" \
            "$disk_available_mib" "$gpu_free_mib" "$admission_exit" false
        write_status failed resource_gate host_memory_insufficient 10
        return 10
    fi
    if [[ "$disk_available_mib" -lt 10240 ]]; then
        write_resource_receipt "$memory_max" "$memory_current" "$available_gib" \
            "$disk_available_mib" "$gpu_free_mib" "$admission_exit" false
        write_status failed resource_gate disk_insufficient 13
        return 13
    fi
    if [[ -z "$gpu_free_mib" || "$gpu_free_mib" -lt "$GPU_FLOOR_MIB" ]]; then
        write_resource_receipt "$memory_max" "$memory_current" "$available_gib" \
            "$disk_available_mib" "${gpu_free_mib:-0}" "$admission_exit" false
        write_status failed resource_gate gpu_memory_insufficient 14
        return 14
    fi
    write_resource_receipt "$memory_max" "$memory_current" "$available_gib" \
        "$disk_available_mib" "$gpu_free_mib" "$admission_exit" true
}

tracking_gate() {
    local gate_root="$RUN_ROOT/tracking-gates/attempt-1"
    local ping_exit verify_exit passed
    mkdir -p "$gate_root"
    set +e
    uv run --no-sync swanlab ping > "$gate_root/swanlab-ping.log" 2>&1
    ping_exit=$?
    uv run --no-sync swanlab verify > "$gate_root/swanlab-verify.log" 2>&1
    verify_exit=$?
    set -e
    if [[ "$ping_exit" -eq 0 && "$verify_exit" -eq 0 ]]; then passed=true; else passed=false; fi
    printf '{"schema_version":"ch4-xgb-path-max-tong-final-model-swanlab-gate-v1","workspace":"mortiswang","project":"ns3-rwkv-lspr24","aggregate_only":true,"ping_exit":%s,"verify_exit":%s,"passed":%s}\n' \
        "$ping_exit" "$verify_exit" "$passed" > "$gate_root/gate.json.partial.$$"
    mv -f -- "$gate_root/gate.json.partial.$$" "$gate_root/gate.json"
    if [[ "$passed" != true ]]; then
        write_status failed tracking_gate swanlab_preinit_failed 15
        return 15
    fi
}

run_tool() {
    uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" \
        --parent-run-root "$PARENT_RUN_ROOT" \
        --parent-config "$PARENT_CONFIG_PATH" \
        --resume-run-root "$RESUME_RUN_ROOT" \
        --out "$RUN_ROOT" "$@"
}

worker() {
    cd "$PROJECT_ROOT"
    exec 9> "$LAUNCH_ROOT/run.lock"
    flock -n 9 || return 75
    source tools/env/activate.sh
    write_status running resource_gate checking_live_resources null
    nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader \
        > "$RUN_ROOT/gpu-processes-at-launch.log" || true
    resource_gate
    tracking_gate
    run_tool --validate-inputs
    write_status running final_single_model_source started null
    set +e
    run_tool 2>&1 | tee "$RUN_ROOT/run.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local python_exit=${pipeline_status[0]}
    local tee_exit=${pipeline_status[1]}
    if [[ "$python_exit" -ne 0 ]]; then
        write_status failed final_single_model_source python_failed "$python_exit"
        return "$python_exit"
    fi
    if [[ "$tee_exit" -ne 0 ]]; then
        write_status failed final_single_model_source tee_failed "$tee_exit"
        return "$tee_exit"
    fi
    for name in model_semantic168_final_source_seed42.json final_model_receipt.json model_bound_threshold_receipt.json source_six_arm_results.json input_receipt.json resource_receipt.json swanlab_receipt.json manifest.json; do
        if [[ ! -s "$RUN_ROOT/$name" ]]; then
            write_status failed postcondition required_artifact_missing 16
            return 16
        fi
    done
    if [[ $(jq -er '.target_year_arrays_read' "$RUN_ROOT/manifest.json") -ne 0 ]]; then
        write_status failed postcondition target_year_read_nonzero 17
        return 17
    fi
    if [[ $(jq -er '.training_runs_started' "$RUN_ROOT/manifest.json") -ne 0 ]]; then
        write_status failed postcondition training_run_count_invalid 18
        return 18
    fi
    write_status finished complete success 0
}

if [[ ${1:-} == --worker ]]; then
    worker
    exit $?
fi
if [[ $# -ne 0 ]]; then
    printf '启动器不接受参数。\n' >&2
    exit 64
fi

cd "$PROJECT_ROOT"
source tools/env/activate.sh
for command in uv swanlab flock nvidia-smi sha256sum rg jq nohup setsid; do
    command -v "$command" >/dev/null 2>&1 || {
        printf '缺少命令：%s\n' "$command" >&2
        exit 69
    }
done
for path in "$TOOL_PATH" "$CONFIG_PATH" "$PARENT_CONFIG_PATH" "$SCRIPT_PATH" \
    "$RESUME_RUN_ROOT/$MODEL_NAME" \
    "$RESUME_RUN_ROOT/final_model_receipt.json" \
    "$RESUME_RUN_ROOT/model_bound_threshold_receipt.json"; do
    [[ -s "$path" ]] || {
        printf '生产文件缺失：%s\n' "$path" >&2
        exit 67
    }
done
for name in selection_frozen_xgb2x2.json effective_config_receipts.json; do
    [[ -r "$PARENT_RUN_ROOT/$name" && -s "$PARENT_RUN_ROOT/$name" ]] || {
        printf '父冻结收据缺失或不可读：%s\n' "$PARENT_RUN_ROOT/$name" >&2
        exit 66
    }
done
for cache_name in X23 y23 I23 M23 E23 ent23 t23_flow; do
    cache_path="$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/${cache_name}.npy"
    [[ -r "$cache_path" && -s "$cache_path" ]] || {
        printf '源年缓存缺失或不可读：%s\n' "$cache_path" >&2
        exit 66
    }
done
if pgrep -f 'python.*[c]h4_xgb_path_max_tong_final_model_source_seed42.py' >/dev/null; then
    printf '同名最终单模型源年进程已经运行。\n' >&2
    exit 75
fi
if [[ -e "$RUN_ROOT" || -e "$LAUNCH_ROOT" ]]; then
    printf '同名运行目录已存在，禁止覆盖：%s\n' "$RUN_ROOT" >&2
    exit 73
fi

run_tool --validate-config
mkdir -p "$RUN_ROOT" "$LAUNCH_ROOT"
sha256sum "$TOOL_PATH" "$CONFIG_PATH" "$PARENT_CONFIG_PATH" "$SCRIPT_PATH" \
    "$PARENT_RUN_ROOT/selection_frozen_xgb2x2.json" \
    "$PARENT_RUN_ROOT/effective_config_receipts.json" > "$LAUNCH_ROOT/input-sha256.log"
write_status prepared launch queued null
nohup setsid bash "$SCRIPT_PATH" --worker \
    > "$LAUNCH_ROOT/launcher.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$LAUNCH_ROOT/worker.pid"
printf 'CH4_PATH_MAX_TONG_FINAL_MODEL_SOURCE_SEED42_STARTED run=%s pid=%s\n' "$RUN_ROOT" "$!"
