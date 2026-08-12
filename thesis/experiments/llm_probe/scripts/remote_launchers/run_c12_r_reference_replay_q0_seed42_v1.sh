#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly CONFIG="$PROJECT_ROOT/configs/c12-r-reference-replay-q0-seed42-v1.json"
readonly MODULE=flow_probe.c12_r_reference_replay
readonly RUN_ID=c12-r-nondestructive-dual-reference-replay-q0-seed42-v1
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly LAUNCHER_DIR="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_DIR/status.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_c12_r_reference_replay_q0_seed42_v1.sh"
readonly SESSION_NAME=c12-r-reference-replay-q0-s42
readonly MAX_PARALLEL_VARIANTS="${C12_R_MAX_PARALLEL_VARIANTS:-2}"
readonly -a VARIANTS=(
    DREF
    DREF_QUALIFIED_GATE
    DREF_QUALIFIED_GATE_CLIP
    DREF_QUALIFIED_GATE_CLIP_BUDGET
    DREF_QUALIFIED_GATE_CLIP_BUDGET_ROLLBACK
    DREF_RANDOM_GATE_MATCHED_CLIP
)

if [[ ! "$MAX_PARALLEL_VARIANTS" =~ ^[1-3]$ ]]; then
    printf 'C12-R 最大并发数必须为 1、2 或 3：%s\n' "$MAX_PARALLEL_VARIANTS" >&2
    exit 64
fi

cd "$PROJECT_ROOT"
source tools/env/activate.sh

write_status() {
    local state=$1
    local stage=$2
    local detail=$3
    local exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    mkdir -p -- "$LAUNCHER_DIR"
    printf '{\n' > "$partial"
    printf '  "schema_version": "c12-r-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "maximum_parallel_variants": %s,\n' "$MAX_PARALLEL_VARIANTS" >> "$partial"
    printf '  "training_performed": false,\n' >> "$partial"
    printf '  "target_prefix_labels_used": false,\n' >> "$partial"
    printf '  "target_development_labels_connected_after_seal": true,\n' >> "$partial"
    printf '  "screening_only": true,\n' >> "$partial"
    printf '  "formal_paper_evidence": false,\n' >> "$partial"
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

run_logged() {
    local log_name=$1
    shift
    set +e
    "$@" 2>&1 | tee "$LAUNCHER_DIR/${log_name}.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$LAUNCHER_DIR/${log_name}-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_DIR/${log_name}-tee-exit-code.txt"
    if [[ "$command_code" -ne 0 ]]; then
        return "$command_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        return "$tee_code"
    fi
}

variant_slug() {
    printf '%s\n' "${1,,}" | tr '_' '-'
}

run_variant() (
    local variant=$1
    local measurement_mode=${2:-concurrent}
    local slug
    slug=$(variant_slug "$variant")
    local run_dir="$OUTPUT_ROOT/$variant"
    local lock_dir="$LAUNCHER_DIR/variant-locks/$variant.lock"
    if [[ -s "$run_dir/status.json" ]] && uv run --no-sync python -c \
        'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "finished" else 1)' \
        "$run_dir/status.json"; then
        printf 'C12-R 变体已有完成状态，跳过：%s\n' "$variant"
        return 0
    fi
    if ! mkdir -- "$lock_dir" 2>/dev/null; then
        printf 'C12-R 变体已有调度锁：%s\n' "$variant" >&2
        return 76
    fi
    trap 'rmdir -- "$lock_dir" 2>/dev/null || true' EXIT
    if [[ -e "$run_dir" ]]; then
        printf 'C12-R 变体目录存在但未完成，保留证据并阻断：%s\n' "$run_dir" >&2
        return 73
    fi
    run_logged "replay-${slug}" \
        uv run --no-sync python -m "$MODULE" replay \
        --config "$CONFIG" \
        --output-dir "$run_dir" \
        --variant "$variant" \
        --resource-measurement-mode "$measurement_mode"
    run_logged "evaluate-${slug}" \
        uv run --no-sync python -m "$MODULE" evaluate \
        --config "$CONFIG" \
        --run-dir "$run_dir"
)

run_remaining_variants() {
    local next_index=1
    local failed=0
    while [[ "$next_index" -lt "${#VARIANTS[@]}" ]]; do
        local -a pids=()
        local -a batch=()
        local slot=0
        while [[ "$slot" -lt "$MAX_PARALLEL_VARIANTS" && "$next_index" -lt "${#VARIANTS[@]}" ]]; do
            local variant=${VARIANTS[$next_index]}
            run_variant "$variant" concurrent &
            pids+=("$!")
            batch+=("$variant")
            next_index=$((next_index + 1))
            slot=$((slot + 1))
        done
        local index
        for index in "${!pids[@]}"; do
            local code
            set +e
            wait "${pids[$index]}"
            code=$?
            set -e
            printf '%s\n' "$code" > "$LAUNCHER_DIR/$(variant_slug "${batch[$index]}")-pipeline-exit-code.txt"
            if [[ "$code" -ne 0 ]]; then
                failed=1
            fi
        done
    done
    if [[ "$failed" -ne 0 ]]; then
        return 80
    fi
}

worker_main() {
    write_status running preflight none null
    if ! command -v uv >/dev/null 2>&1 || ! command -v rg >/dev/null 2>&1; then
        printf '远端 uv 或 rg 不可用。\n' >&2
        return 69
    fi
    if [[ ! -s "$CONFIG" ]]; then
        printf 'C12-R 配置不存在：%s\n' "$CONFIG" >&2
        return 66
    fi
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys, torch
config = json.load(open(sys.argv[1], encoding="utf-8"))
paths = config["paths"]
dref = pathlib.Path(paths["dref_run"])
status = json.load(open(dref / "status.json", encoding="utf-8"))
contract = json.load(open(dref / "source-frozen-control-contract.json", encoding="utf-8"))
checkpoint = torch.load(dref / "checkpoints/best.pt", map_location="cpu", weights_only=False)
valid = (
    config.get("training_performed") is False
    and config.get("final_accessed") is False
    and status.get("state") == "finished"
    and status.get("variant") == "C12-DREF"
    and status.get("final_accessed") is False
    and checkpoint.get("variant") == "C12-DREF"
    and contract.get("selection_roles") == ["source-train", "source-validation"]
    and contract.get("target_prefix_used_for_thresholds") is False
    and contract.get("target_development_label_used") is False
    and contract.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$CONFIG" || {
        printf 'C12-R 历史 DREF 权重或隔离合同门禁失败。\n' >&2
        return 79
    }
    if [[ "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)" -ne 0 ]]; then
        printf 'GPU 已有计算进程，拒绝叠加 C12-R。\n' >&2
        return 75
    fi
    mkdir -p -- "$OUTPUT_ROOT" "$LAUNCHER_DIR/variant-locks"
    write_status running isolated-dref-measurement none null
    run_variant DREF isolated
    uv run --no-sync python -c '
import json, pathlib, sys
run = pathlib.Path(sys.argv[1])
status = json.load(open(run / "status.json", encoding="utf-8"))
usage = json.load(open(run / "resource-usage.json", encoding="utf-8"))
valid = (
    status.get("state") == "finished"
    and status.get("final_accessed") is False
    and usage.get("resource_measurement_mode") == "isolated"
    and usage.get("single_process_efficiency_metrics_valid") is True
    and usage.get("training_performed") is False
    and usage.get("peak_gpu_memory_bytes", 0) > 0
    and usage.get("total_replay_seconds", 0) > 0
)
raise SystemExit(0 if valid else 1)
' "$OUTPUT_ROOT/DREF" || {
        printf '隔离 DREF 真实时长或显存收据不合法，停止其余变体。\n' >&2
        return 79
    }
    write_status running parallel-independent-replays none null
    run_remaining_variants
    write_status finished complete all_variants_evaluated 0
}

worker_entry() {
    trap 'write_status interrupted signal received 130; exit 130' HUP INT TERM
    set +e
    worker_main 2>&1 | tee "$LAUNCHER_DIR/controller.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local worker_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$worker_code" > "$LAUNCHER_DIR/controller-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_DIR/controller-tee-exit-code.txt"
    if [[ "$worker_code" -ne 0 ]]; then
        write_status failed controller worker_failed "$worker_code"
        return "$worker_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        write_status failed controller tee_failed "$tee_code"
        return "$tee_code"
    fi
}

if [[ ${1:-} == --worker ]]; then
    worker_entry
    exit $?
fi

if ! command -v screen >/dev/null 2>&1; then
    printf '远端缺少 screen。\n' >&2
    exit 69
fi
if screen -ls 2>/dev/null | rg -q "[.]${SESSION_NAME}[[:space:]]"; then
    printf '同名 C12-R screen 已在运行：%s\n' "$SESSION_NAME"
    exit 0
fi
if [[ -s "$STATUS_PATH" ]] && uv run --no-sync python -c \
    'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "finished" else 1)' \
    "$STATUS_PATH"; then
    printf 'C12-R 已完成，不重复启动：%s\n' "$RUN_ID"
    exit 0
fi
mkdir -p -- "$LAUNCHER_DIR"
printf '%s\n' "$SESSION_NAME" > "$LAUNCHER_DIR/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_DIR/command.txt"
sha256sum "$CONFIG" src/flow_probe/c12_r_reference_replay.py "$SCRIPT_PATH" \
    > "$LAUNCHER_DIR/code-input-sha256.txt"
write_status prepared launch none null
screen -dmS "$SESSION_NAME" bash "$SCRIPT_PATH" --worker
printf 'C12_R_STARTED session=%s launcher=%s output=%s\n' \
    "$SESSION_NAME" "$LAUNCHER_DIR" "$OUTPUT_ROOT"
