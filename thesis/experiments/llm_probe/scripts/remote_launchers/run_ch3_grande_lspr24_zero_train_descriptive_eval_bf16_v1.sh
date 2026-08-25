#!/usr/bin/env bash

set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-grande-lspr24-zero-train-descriptive-eval-bf16-v1
readonly SCREEN_NAME=ch3-grande-lspr24-zero-eval-v1
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-grande-lspr24-zero-train-descriptive-eval-bf16-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_grande_lspr24_zero_train_descriptive_eval.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_grande_lspr24_zero_train_descriptive_eval_bf16_v1.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly RESOURCE_RECEIPT="$OUTPUT_ROOT/resource-receipt.json"
readonly MEMORY_GATE="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly PARENT_ROOT="$PROJECT_ROOT/runs/diagnostics/ch3-grande-c00-protocolA-source-q0-seed42-v1-bf16-v1"

mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
if [[ -r "$HOME/.bashrc" ]]; then
    source "$HOME/.bashrc" >> "$LAUNCHER_ROOT/shell-init.log" 2>&1 || true
fi
cd "$PROJECT_ROOT"
source tools/env/activate.sh

write_launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-grande-lspr24-zero-train-launcher-status-v1",
    "run_id": sys.argv[2], "state": sys.argv[3], "stage": sys.argv[4],
    "detail": sys.argv[5], "exit_code": None if sys.argv[6] == "null" else int(sys.argv[6]),
    "updated_at_unix": time.time(), "training_runs": 0, "optimizer_steps": 0,
    "parameter_updates": 0, "new_checkpoints_written": 0,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$LAUNCHER_ROOT/status.json" "$RUN_ID" "$state" "$stage" "$detail" "$exit_code"
}

validate_inputs() {
    local path structure name
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
    for path in "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" "$MEMORY_GATE" \
        "$PARENT_ROOT/config.json" "$PARENT_ROOT/backbone_selection_frozen.json"; do
        [[ -r "$path" && -s "$path" ]] || {
            printf '必需输入缺失或不可读：%s\n' "$path" >&2
            return 66
        }
    done
    for structure in G-A G-B; do
        for path in "$PARENT_ROOT/checkpoints/selected-${structure}.pt" \
            "$PARENT_ROOT/receipts/selection-${structure}.json"; do
            [[ -r "$path" && -s "$path" ]] || {
                printf '父结构制品缺失或不可读：%s\n' "$path" >&2
                return 66
            }
        done
    done
    for name in X24 y24 s24 d24; do
        path="$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/${name}.npy"
        [[ -r "$path" && -s "$path" ]] || {
            printf '目标数组缺失或不可读：%s\n' "$path" >&2
            return 66
        }
    done
}

admit_resources() {
    local gpu_free disk_available disk_used
    bash "$MEMORY_GATE" 30 "$RUN_ID" > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1
    gpu_free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
    disk_available=$(df -Pk "$PROJECT_ROOT" | awk 'NR == 2 {print $4}')
    disk_used=$(df -Pk "$PROJECT_ROOT" | awk 'NR == 2 {gsub(/%/, "", $5); print $5}')
    if [[ ! "$gpu_free" =~ ^[0-9]+$ || ! "$disk_available" =~ ^[0-9]+$ || ! "$disk_used" =~ ^[0-9]+$ ]]; then
        printf '资源读数无效。\n' >&2
        return 69
    fi
    if (( gpu_free < 12288 || disk_available < 10485760 || disk_used >= 80 )); then
        printf '资源门失败：GPU空闲=%sMiB，磁盘可用=%sKiB，使用率=%s%%。\n' \
            "$gpu_free" "$disk_available" "$disk_used" >&2
        return 69
    fi
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-grande-lspr24-zero-train-resource-v1",
    "run_id": sys.argv[2], "recorded_at_unix": time.time(),
    "admission": {"gpu_free_mib": int(sys.argv[3]), "disk_available_kib": int(sys.argv[4]),
                  "disk_used_percent": int(sys.argv[5]), "minimum_cgroup_available_memory_gib": 30},
    "wall_clock_limit": None,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$RESOURCE_RECEIPT" "$RUN_ID" "$gpu_free" "$disk_available" "$disk_used"
}

worker() {
    local code=0 resume_flag= pipeline_status
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || {
        printf '同名运行锁已占用。\n' >&2
        return 75
    }
    validate_inputs
    if [[ -s "$OUTPUT_ROOT/artifact-manifest.json" ]]; then
        write_launcher_status finished complete already_complete 0
        return 0
    fi
    admit_resources
    [[ -d "$OUTPUT_ROOT/units" ]] && resume_flag=--resume
    write_launcher_status running evaluate target_arrays_once_two_structures_once null
    set +e
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" \
        ${resume_flag:+$resume_flag} --resource-receipt "$RESOURCE_RECEIPT" \
        2>&1 | tee "$LAUNCHER_ROOT/controller.log"
    pipeline_status=("${PIPESTATUS[@]}")
    set -e
    code=${pipeline_status[0]}
    (( code != 0 || pipeline_status[1] == 0 )) || code=${pipeline_status[1]}
    printf '%s\n' "${pipeline_status[0]}" > "$LAUNCHER_ROOT/controller.command-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$LAUNCHER_ROOT/controller.tee-exit-code.txt"
    if (( code != 0 )); then
        write_launcher_status failed evaluate tool_or_tee_failed "$code"
        return "$code"
    fi
    [[ -s "$OUTPUT_ROOT/aggregate-results.json" && -s "$OUTPUT_ROOT/artifact-manifest.json" ]] || {
        write_launcher_status failed validate_outputs missing_aggregate_or_manifest 7
        return 7
    }
    write_launcher_status finished complete descriptive_evaluation_complete 0
}

if [[ ${1:-} == --worker && $# -eq 1 ]]; then
    worker
    exit $?
fi
if [[ $# -ne 0 ]]; then
    printf '启动器不接受外部参数。\n' >&2
    exit 64
fi

for command_name in uv screen flock nvidia-smi awk df tee; do
    command -v "$command_name" >/dev/null || {
        printf '缺少命令：%s\n' "$command_name" >&2
        exit 69
    }
done
validate_inputs
if [[ -s "$OUTPUT_ROOT/artifact-manifest.json" ]]; then
    printf 'CH3_GRANDE_LSPR24_ZERO_TRAIN_DESCRIPTIVE_EVAL_ALREADY_COMPLETE run=%s\n' "$OUTPUT_ROOT"
    exit 0
fi
screen_sessions=$(screen -ls || true)
if printf '%s\n' "$screen_sessions" | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名 GRANDE LSPR24 描述性评价已启动。\n'
    exit 0
fi
write_launcher_status prepared launch queued null
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'CH3_GRANDE_LSPR24_ZERO_TRAIN_DESCRIPTIVE_EVAL_STARTED session=%s run=%s\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT"
