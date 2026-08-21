#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-published-neural-operational-backfill-v1
readonly DISPLAY_NAME='已发表神经基线目标年完整运营指标零训练回填'
readonly SCREEN_NAME=ch3-published-neural-op-v1
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-published-neural-operational-backfill-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_published_neural_operational_backfill.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_published_neural_operational_backfill_v1.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly RUN_LOG="$OUTPUT_ROOT/run.log"
readonly MEMORY_GATE="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly EXPECTED_GPU_NAME='NVIDIA GeForce RTX 5090'
readonly MINIMUM_DISK_FREE_KIB=10485760
readonly PEER_PATTERN='python.*[c]h3_published_neural_operational_backfill[.]py.*--compute'

cd "$PROJECT_ROOT"
source tools/env/activate.sh

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
valid = (
    config["run_id"] == sys.argv[2]
    and config["display_name"] == sys.argv[3]
    and config["resource_contract"]["authorized_server"] == "B76"
    and config["resource_contract"]["device"] == "cpu"
    and config["resource_contract"]["gpu_count"] == 0
    and config["resource_contract"]["gpu_array_reads"] == 0
    and config["resource_contract"]["peak_gpu_memory_mib"] == 0
    and config["resource_contract"]["estimated_peak_process_memory_gib"] == 4
    and config["resource_contract"]["estimated_input_read_gib"] == 1.32
    and config["resource_contract"]["estimated_output_mib_upper_bound"] == 6
    and set(config["models"]) == {"transformer", "cnn", "gru"}
    and config["artifact_policy"]["output_root"] == sys.argv[4]
    and config["artifact_policy"]["persist_per_flow_scores"] is False
    and config["artifact_policy"]["persist_per_entity_scores"] is False
    and config["artifact_policy"]["persist_per_entity_first_alert"] is False
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
        "$PROJECT_ROOT/runs/diagnostics/ch3-baselines-full/scores_transformer_dijk2026.npy" \
        "$PROJECT_ROOT/runs/diagnostics/ch3-baselines-full/scores_cnn_leoste2025.npy" \
        "$PROJECT_ROOT/runs/diagnostics/ch3-baselines-full/scores_gru_dijk2026.npy" \
        "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/y24.npy" \
        "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/s24.npy" \
        "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/d24.npy"; do
        [[ -r "$path" && -s "$path" ]] || {
            printf '生产输入缺失、为空或不可读：%s\n' "$path" >&2
            return 66
        }
    done
}

admit_resources() {
    local disk_fields available_kib used_percent
    ALLOW_CONCURRENT=1 bash "$MEMORY_GATE" 4 "$RUN_ID" \
        > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    if [[ ! "$available_kib" =~ ^[0-9]+$ || ! "$used_percent" =~ ^[0-9]+$ ]]; then
        printf '磁盘资源读数无效，拒绝启动。\n' >&2
        return 69
    fi
    if (( available_kib < MINIMUM_DISK_FREE_KIB || used_percent >= 80 )); then
        printf '磁盘门失败：可用=%s KiB，使用率=%s%%。\n' "$available_kib" "$used_percent" >&2
        return 69
    fi
    printf 'disk_available_kib=%s\ndisk_used_percent=%s\nio_inputs_readable=true\nio_output_parent_writable=true\n' \
        "$available_kib" "$used_percent" > "$LAUNCHER_ROOT/io-disk-admission.txt"
}

run_compute_logged() {
    local code
    set +e
    CUDA_VISIBLE_DEVICES='' uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" \
        --project-root "$PROJECT_ROOT" \
        --compute \
        --resume 2>&1 | tee -a "$RUN_LOG"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    printf '%s\n' "${pipeline_status[0]}" > "$LAUNCHER_ROOT/compute-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$LAUNCHER_ROOT/tee-exit-code.txt"
    code=${pipeline_status[0]}
    (( code != 0 || pipeline_status[1] == 0 )) || code=${pipeline_status[1]}
    return "$code"
}

worker() {
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || {
        printf '同名运行锁已占用。\n' >&2
        return 75
    }
    validate_static_contract
    if [[ -s "$OUTPUT_ROOT/manifest.json" ]]; then
        CUDA_VISIBLE_DEVICES='' uv run --no-sync python "$TOOL_PATH" \
            --config "$CONFIG_PATH" \
            --project-root "$PROJECT_ROOT" \
            --finalize \
            --resume
        return 0
    fi
    run_compute_logged
    CUDA_VISIBLE_DEVICES='' uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" \
        --project-root "$PROJECT_ROOT" \
        --finalize \
        --resume
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
    CUDA_VISIBLE_DEVICES='' uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" \
        --project-root "$PROJECT_ROOT" \
        --finalize \
        --resume
    printf 'PUBLISHED_NEURAL_OPERATIONAL_BACKFILL_ALREADY_COMPLETE run=%s\n' "$OUTPUT_ROOT"
    exit 0
fi
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名运营回填已经启动。\n'
    exit 0
fi
if pgrep -f "$PEER_PATTERN" >/dev/null 2>&1; then
    printf '同名运营回填进程已经运行。\n' >&2
    exit 75
fi
admit_resources
sha256sum "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" \
    "$PROJECT_ROOT/runs/diagnostics/ch3-baselines-full/scores_transformer_dijk2026.npy" \
    "$PROJECT_ROOT/runs/diagnostics/ch3-baselines-full/scores_cnn_leoste2025.npy" \
    "$PROJECT_ROOT/runs/diagnostics/ch3-baselines-full/scores_gru_dijk2026.npy" \
    "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/y24.npy" \
    "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/s24.npy" \
    "$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/d24.npy" \
    > "$LAUNCHER_ROOT/input-sha256.txt"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'PUBLISHED_NEURAL_OPERATIONAL_BACKFILL_STARTED session=%s run=%s display=%s\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT" "$DISPLAY_NAME"
