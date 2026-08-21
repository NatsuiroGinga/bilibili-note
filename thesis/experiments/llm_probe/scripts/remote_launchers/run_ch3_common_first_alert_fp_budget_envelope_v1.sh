#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-common-first-alert-fp-budget-envelope-v1
readonly DISPLAY_NAME='五系统共同实际首次告警FP预算包络'
readonly SCREEN_NAME=ch3-common-first-alert-envelope-v1
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-common-first-alert-fp-budget-envelope-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_common_first_alert_fp_budget_envelope.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_common_first_alert_fp_budget_envelope_v1.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly RUN_LOG="$OUTPUT_ROOT/run.log"
readonly ADMISSION_RECEIPT="$LAUNCHER_ROOT/resource-admission.json"
readonly MEMORY_GATE="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly EXPECTED_GPU_NAME='NVIDIA GeForce RTX 5090'
readonly MINIMUM_FREE_GPU_MIB=12288
readonly MINIMUM_CGROUP_MEMORY_GIB=48
readonly MINIMUM_DISK_FREE_KIB=10485760
readonly MAXIMUM_DISK_USED_PERCENT=80
readonly PEER_PATTERN='python.*[c]h3_common_first_alert_fp_budget_envelope[.]py.*--stage'

cd "$PROJECT_ROOT"
source tools/env/activate.sh

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
methods = config["methods"]
valid = (
    config["run_id"] == sys.argv[2]
    and config["display_name"] == sys.argv[3]
    and config["artifact_policy"]["output_root"] == sys.argv[4]
    and config["resource_contract"]["authorized_server"] == "B76"
    and config["resource_contract"]["minimum_free_gpu_memory_mib"] == 12288
    and config["resource_contract"]["minimum_cgroup_available_memory_gib"] == 48
    and config["resource_contract"]["maximum_parallel_units"] == 1
    and config["resource_contract"]["wall_clock_limit"] is None
    and config["training_runs"] == 0
    and config["hyperparameter_selection_runs"] == 0
    and list(methods) == [
        "full_mlp_o11",
        "xgb_cpa_elp_c11",
        "cnn_published_max",
        "gru_published_max",
        "transformer_published_max",
    ]
    and sum(item["logical_target_score_calls"] for item in methods.values()) == 1
    and sum(item["logical_target_inference_calls"] for item in methods.values()) == 1
    and all(item["target_retrained"] is False for item in methods.values())
    and config["common_budget"]["interpolation"] is False
    and config["common_budget"]["exact_fpr_intersection"] is False
    and config["common_budget"]["tie_group_rule"]
        == "complete_benign_path_max_tie_groups_never_split"
    and config["common_budget"]["common_integer_budgets"] == [46, 231, 463, 927, 1854, 3709]
    and config["evaluation"]["first_alert_axis"] == "exposure_index"
    and config["evaluation"]["exposure_index_base"] == 1
    and config["evaluation"]["time_delay_available"] is False
    and config["artifact_policy"]["persist_per_flow_scores"] is False
    and config["artifact_policy"]["persist_per_entity_scores"] is False
    and config["artifact_policy"]["persist_per_entity_first_alert"] is False
    and config["artifact_policy"]["persist_entity_mapping"] is False
    and config["artifact_policy"]["persist_derived_matrices"] is False
)
raise SystemExit(0 if valid else 78)
' "$CONFIG_PATH" "$RUN_ID" "$DISPLAY_NAME" "runs/diagnostics/$RUN_ID"
}

validate_server_and_inputs() {
    local actual_gpu path
    actual_gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader | awk 'NR == 1 {print $0}')
    [[ "$actual_gpu" == "$EXPECTED_GPU_NAME" ]] || {
        printf '服务器身份门失败：期望 %s，实际 %s。\n' "$EXPECTED_GPU_NAME" "$actual_gpu" >&2
        return 69
    }
    for path in \
        "$TOOL_PATH" \
        "$CONFIG_PATH" \
        "$SCRIPT_PATH" \
        "$MEMORY_GATE" \
        "$PROJECT_ROOT/tools/ch3_xgb_cpa_elp_operational_backfill.py" \
        "$PROJECT_ROOT/tools/ch3_full_mlp_complete_entity_lp_protocol_a_q0_bf16.py" \
        "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/y24.npy" \
        "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/s24.npy" \
        "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/d24.npy" \
        "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/X24.npy" \
        "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/I24.npy" \
        "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/M24.npy"; do
        [[ -r "$path" && -s "$path" ]] || {
            printf '生产输入缺失、为空或不可读：%s\n' "$path" >&2
            return 66
        }
    done
}

admit_resources() {
    local disk_fields available_kib used_percent free_gpu_mib cgroup_available_gib
    ALLOW_CONCURRENT=1 bash "$MEMORY_GATE" "$MINIMUM_CGROUP_MEMORY_GIB" "$RUN_ID" \
        > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1
    free_gpu_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR == 1 {print $1}')
    if [[ ! "$free_gpu_mib" =~ ^[0-9]+$ || "$free_gpu_mib" -lt "$MINIMUM_FREE_GPU_MIB" ]]; then
        printf 'GPU 空闲显存门失败：读数=%s MiB，下限=%s MiB。\n' \
            "$free_gpu_mib" "$MINIMUM_FREE_GPU_MIB" >&2
        return 69
    fi
    cgroup_available_gib=$(rg -o '^cgroup_available_gib=([0-9.]+)$' -r '$1' \
        "$LAUNCHER_ROOT/memory-admission-gate.log" | tail -n 1)
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    if [[ ! "$available_kib" =~ ^[0-9]+$ || ! "$used_percent" =~ ^[0-9]+$ ]]; then
        printf '磁盘资源读数无效，拒绝启动。\n' >&2
        return 69
    fi
    if (( available_kib < MINIMUM_DISK_FREE_KIB || used_percent >= MAXIMUM_DISK_USED_PERCENT )); then
        printf '磁盘门失败：可用=%s KiB，使用率=%s%%。\n' "$available_kib" "$used_percent" >&2
        return 69
    fi
    uv run --no-sync python -c '
import json, os, pathlib, sys
receipt = {
    "schema_version": "ch3-common-first-alert-resource-admission-v1",
    "run_id": sys.argv[1],
    "authorized_server": "B76",
    "expected_gpu_name": sys.argv[2],
    "free_gpu_mib_at_admission": int(sys.argv[3]),
    "minimum_free_gpu_memory_mib": int(sys.argv[4]),
    "cgroup_available_gib_at_admission": sys.argv[5] or None,
    "minimum_cgroup_available_memory_gib": int(sys.argv[6]),
    "disk_available_kib_at_admission": int(sys.argv[7]),
    "disk_used_percent_at_admission": int(sys.argv[8]),
    "minimum_free_disk_gib": 10,
    "maximum_parallel_units": 1,
    "wall_clock_limit": None,
    "gpu_hour_limit": None,
    "concurrency_contamination_possible": True,
    "fair_efficiency_evidence": False,
}
path = pathlib.Path(sys.argv[9])
temporary = path.with_name(path.name + ".partial." + str(os.getpid()))
temporary.write_text(
    json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
os.replace(temporary, path)
' "$RUN_ID" "$EXPECTED_GPU_NAME" "$free_gpu_mib" "$MINIMUM_FREE_GPU_MIB" \
        "${cgroup_available_gib:-}" "$MINIMUM_CGROUP_MEMORY_GIB" \
        "$available_kib" "$used_percent" "$ADMISSION_RECEIPT"
}

run_compute_logged() {
    local code
    set +e
    uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" \
        --project-root "$PROJECT_ROOT" \
        --stage compute \
        --resume 2>&1 | tee -a "$RUN_LOG"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    printf '%s\n' "${pipeline_status[0]}" > "$LAUNCHER_ROOT/compute-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$LAUNCHER_ROOT/tee-exit-code.txt"
    code=${pipeline_status[0]}
    (( code != 0 || pipeline_status[1] == 0 )) || code=${pipeline_status[1]}
    return "$code"
}

finalize_only() {
    local code
    set +e
    uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" \
        --project-root "$PROJECT_ROOT" \
        --stage finalize \
        --resume \
        --admission-receipt "$ADMISSION_RECEIPT" > "$LAUNCHER_ROOT/finalize.log" 2>&1
    code=$?
    set -e
    printf '%s\n' "$code" > "$LAUNCHER_ROOT/finalize-exit-code.txt"
    return "$code"
}

worker() {
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || {
        printf '同名运行锁已占用。\n' >&2
        return 75
    }
    validate_static_contract
    run_compute_logged
    finalize_only
}

if [[ ${1:-} == --worker && $# -eq 1 ]]; then
    worker
    exit $?
fi
if [[ $# -ne 0 ]]; then
    printf '启动器不接受外部参数。\n' >&2
    exit 64
fi

for command in uv screen flock nvidia-smi sha256sum rg awk df tail tee pgrep; do
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
validate_server_and_inputs
if [[ -s "$OUTPUT_ROOT/manifest.json" ]]; then
    finalize_only
    printf 'COMMON_FIRST_ALERT_ENVELOPE_ALREADY_COMPLETE run=%s\n' "$OUTPUT_ROOT"
    exit 0
fi
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名共同预算包络已经启动。\n'
    exit 0
fi
if pgrep -f "$PEER_PATTERN" >/dev/null 2>&1; then
    printf '同名共同预算包络进程已经运行。\n' >&2
    exit 75
fi
admit_resources
sha256sum "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" \
    "$PROJECT_ROOT/tools/ch3_xgb_cpa_elp_operational_backfill.py" \
    "$PROJECT_ROOT/tools/ch3_full_mlp_complete_entity_lp_protocol_a_q0_bf16.py" \
    "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/y24.npy" \
    "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/s24.npy" \
    "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/d24.npy" \
    > "$LAUNCHER_ROOT/input-sha256.txt"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'COMMON_FIRST_ALERT_ENVELOPE_STARTED session=%s run=%s display=%s\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT" "$DISPLAY_NAME"
