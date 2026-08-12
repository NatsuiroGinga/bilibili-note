#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly CACHE_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"
readonly PHASE_A_ROOT="$PROJECT_ROOT/runs/candidates/c12-phase-a-balanced-sequence-pools-q0-seed42-v2-threshold-sentinel-rerun1"
readonly RECEIVER_DIR="$PHASE_A_ROOT/shared-receiver"
readonly REPRESENTATION_DIR="$PHASE_A_ROOT/frozen-representations"
readonly PHASE_A_GATE="$PROJECT_ROOT/runs/launchers/c12-phase-a-balanced-sequence-pools-q0-seed42-v2-threshold-sentinel-rerun1/gpu-gate.json"
readonly RUN_ID=c12-phase-b-drift-bounded-control-dual-reference-q0-seed42-v1
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly PREFIX_REPRESENTATION_DIR="$OUTPUT_ROOT/shared-target-prefix-representation"
readonly LAUNCHER_DIR="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_DIR/status.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_c12_phase_b_q0_seed42_v1.sh"
readonly SESSION_NAME=c12-phase-b-main-q0-s42
readonly MODULE=flow_probe.c12_crossyear_train
readonly EPOCHS=4
readonly SEED=42
readonly MAX_PARALLEL_VARIANTS="${C12_PHASE_B_MAX_PARALLEL_VARIANTS:-2}"
readonly -a VARIANTS=(C12-CTRL C12-DREF C12-FULL)
readonly -a PHASE_A_VARIANTS=(RX-TR K-RWKV7 K-DELTA K-GDELTA GRU)

if [[ ! "$MAX_PARALLEL_VARIANTS" =~ ^[1-3]$ ]]; then
    printf '阶段 B 最大并发数必须为 1、2 或 3：%s\n' "$MAX_PARALLEL_VARIANTS" >&2
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
    printf '{\n' > "$partial"
    printf '  "schema_version": "c12-phase-b-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "updated_at": "%s",\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$partial"
    printf '  "maximum_parallel_variants": %s,\n' "$MAX_PARALLEL_VARIANTS" >> "$partial"
    if [[ "$MAX_PARALLEL_VARIANTS" == 1 ]]; then
        printf '  "single_gpu_serial": true,\n' >> "$partial"
        printf '  "single_process_efficiency_metrics_valid": true,\n' >> "$partial"
    else
        printf '  "single_gpu_serial": false,\n' >> "$partial"
        printf '  "single_process_efficiency_metrics_valid": false,\n' >> "$partial"
    fi
    printf '  "target_prefix_labels_used": false,\n' >> "$partial"
    printf '  "target_development_labels_connected_after_seal": true,\n' >> "$partial"
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

run_logged_variant() {
    local stage=$1
    shift
    set +e
    "$@" 2>&1 | tee "$LAUNCHER_DIR/${stage}.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$LAUNCHER_DIR/${stage}-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_DIR/${stage}-tee-exit-code.txt"
    if [[ "$command_code" -ne 0 ]]; then
        return "$command_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        return "$tee_code"
    fi
}

run_logged() {
    local stage=$1
    shift
    write_status running "$stage" none null
    set +e
    "$@" 2>&1 | tee "$LAUNCHER_DIR/${stage}.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$LAUNCHER_DIR/${stage}-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_DIR/${stage}-tee-exit-code.txt"
    if [[ "$command_code" -ne 0 ]]; then
        write_status failed "$stage" command_failed "$command_code"
        return "$command_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        write_status failed "$stage" tee_failed "$tee_code"
        return "$tee_code"
    fi
}

variant_slug() {
    case "$1" in
        C12-CTRL) printf '%s\n' drift-triggered-bounded-state-control ;;
        C12-DREF) printf '%s\n' trusted-dual-reference-calibration ;;
        C12-FULL) printf '%s\n' drift-bounded-control-trusted-dual-reference ;;
        *) return 64 ;;
    esac
}

run_variant() (
    local variant=$1
    local batch_size=$2
    local slug
    slug=$(variant_slug "$variant")
    local run_dir="$OUTPUT_ROOT/$variant"
    local status="$run_dir/status.json"
    local lock_dir="$LAUNCHER_DIR/variant-locks/$variant.lock"

    if [[ -s "$status" ]] && uv run --no-sync python -c \
        'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "finished" else 1)' \
        "$status"; then
        printf '阶段 B 变体已有完成状态，跳过：%s（%s）\n' "$variant" "$slug"
        return 0
    fi
    if ! mkdir -- "$lock_dir" 2>/dev/null; then
        printf '阶段 B 变体已有调度锁，拒绝重复运行：%s\n' "$lock_dir" >&2
        return 76
    fi
    trap 'rmdir -- "$lock_dir" 2>/dev/null || true' EXIT

    if [[ -s "$status" ]] && uv run --no-sync python -c \
        'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "finished" else 1)' \
        "$status"; then
        printf '阶段 B 变体获锁后确认已完成，跳过：%s（%s）\n' "$variant" "$slug"
        return 0
    fi
    if [[ -s "$status" ]] && uv run --no-sync python -c \
        'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "predictions_sealed_evaluation_pending" else 1)' \
        "$status"; then
        run_logged_variant "evaluate-${slug}" \
            uv run --no-sync python -m "$MODULE" evaluate \
            --cache-root "$CACHE_ROOT" \
            --run-dir "$run_dir"
        return 0
    fi
    if [[ -e "$run_dir" ]]; then
        printf '阶段 B 变体目录存在但不可安全续跑，保留证据并阻断：%s\n' "$run_dir" >&2
        return 73
    fi

    local resource_measurement_mode=concurrent
    if [[ "$MAX_PARALLEL_VARIANTS" == 1 ]]; then
        resource_measurement_mode=isolated
    fi
    run_logged_variant "train-${slug}" \
        uv run --no-sync python -m "$MODULE" train-phase-b-variant \
        --cache-root "$CACHE_ROOT" \
        --representation-root "$REPRESENTATION_DIR" \
        --target-prefix-representation-root "$PREFIX_REPRESENTATION_DIR" \
        --receiver-checkpoint "$RECEIVER_DIR/checkpoints/best.pt" \
        --output-dir "$run_dir" \
        --run-name "${RUN_ID}-${slug}" \
        --variant "$variant" \
        --batch-size "$batch_size" \
        --epochs "$EPOCHS" \
        --seed "$SEED" \
        --resource-measurement-mode "$resource_measurement_mode"
    run_logged_variant "evaluate-${slug}" \
        uv run --no-sync python -m "$MODULE" evaluate \
        --cache-root "$CACHE_ROOT" \
        --run-dir "$run_dir"
)

write_parallel_exit_summary() {
    local partial="$LAUNCHER_DIR/parallel-exit-summary.json.partial.$$"
    local variant
    local separator=''
    local all_succeeded=true
    printf '{\n  "schema_version": "c12-phase-b-parallel-exit-summary-v1",\n' > "$partial"
    printf '  "maximum_parallel_variants": %s,\n' "$MAX_PARALLEL_VARIANTS" >> "$partial"
    printf '  "variants": [' >> "$partial"
    for variant in "${VARIANTS[@]}"; do
        local exit_path="$LAUNCHER_DIR/$(variant_slug "$variant")-pipeline-exit-code.txt"
        local exit_code=125
        if [[ -s "$exit_path" ]]; then
            exit_code=$(<"$exit_path")
        fi
        if [[ "$exit_code" -ne 0 ]]; then
            all_succeeded=false
        fi
        printf '%s\n    {"variant": "%s", "exit_code": %s}' \
            "$separator" "$variant" "$exit_code" >> "$partial"
        separator=','
    done
    printf '\n  ],\n  "all_succeeded": %s,\n' "$all_succeeded" >> "$partial"
    printf '  "single_process_efficiency_metrics_valid": %s,\n' \
        "$([[ "$MAX_PARALLEL_VARIANTS" == 1 ]] && printf true || printf false)" >> "$partial"
    printf '  "final_accessed": false\n}\n' >> "$partial"
    mv -f -- "$partial" "$LAUNCHER_DIR/parallel-exit-summary.json"
}

run_variants_parallel() {
    local batch_size=$1
    local next_index=0
    local any_failed=0
    while [[ "$next_index" -lt "${#VARIANTS[@]}" ]]; do
        local -a pids=()
        local -a batch_variants=()
        local slot=0
        while [[ "$slot" -lt "$MAX_PARALLEL_VARIANTS" && "$next_index" -lt "${#VARIANTS[@]}" ]]; do
            local variant=${VARIANTS[$next_index]}
            run_variant "$variant" "$batch_size" &
            pids+=("$!")
            batch_variants+=("$variant")
            next_index=$((next_index + 1))
            slot=$((slot + 1))
        done
        local batch_index
        for batch_index in "${!pids[@]}"; do
            local exit_code
            set +e
            wait "${pids[$batch_index]}"
            exit_code=$?
            set -e
            printf '%s\n' "$exit_code" > \
                "$LAUNCHER_DIR/$(variant_slug "${batch_variants[$batch_index]}")-pipeline-exit-code.txt"
            if [[ "$exit_code" -ne 0 ]]; then
                any_failed=1
            fi
        done
    done
    write_parallel_exit_summary
    if [[ "$any_failed" -ne 0 ]]; then
        return 80
    fi
}

worker_main() {
    write_status running preflight none null
    if [[ ! -s "$CACHE_ROOT/cache-manifest.json" ]]; then
        printf 'Q0 Python 缓存清单不存在：%s\n' "$CACHE_ROOT/cache-manifest.json" >&2
        return 66
    fi
    if [[ ! -s "$RECEIVER_DIR/checkpoints/best.pt" || ! -s "$RECEIVER_DIR/status.json" || ! -s "$RECEIVER_DIR/training-pool-receipt.json" || ! -s "$REPRESENTATION_DIR/representation-manifest.json" ]]; then
        printf '阶段 A 共同接收器或冻结表示不完整。\n' >&2
        return 67
    fi
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
receipt = json.load(open(root / "training-pool-receipt.json", encoding="utf-8"))
best = root / "checkpoints/best.pt"
valid = (
    status.get("state") == "finished"
    and status.get("final_accessed") is False
    and receipt.get("state") == "finished"
    and receipt.get("planned_epochs") == receipt.get("actual_epochs") == 4
    and receipt.get("planned_steps") == receipt.get("actual_steps") == 732
    and receipt.get("malicious_sequence_pool_count") == 116
    and receipt.get("all_benign_sequence_pool_count") == 2810
    and receipt.get("malicious_sequences_per_batch") == receipt.get("all_benign_sequences_per_batch") == 8
    and receipt.get("actual_malicious_draws_total") == receipt.get("planned_malicious_draws_total")
    and receipt.get("actual_all_benign_draws_total") == receipt.get("planned_all_benign_draws_total")
    and receipt.get("every_batch_equal_pool_counts") is True
    and receipt.get("final_accessed") is False
    and best.is_file() and best.stat().st_size > 0
)
raise SystemExit(0 if valid else 1)
' "$RECEIVER_DIR" || {
        printf '阶段 A v2 共同接收器完成门禁失败。\n' >&2
        return 79
    }
    if [[ ! -s "$PHASE_A_GATE" ]]; then
        printf '阶段 A 真实显存门禁收据不存在。\n' >&2
        return 67
    fi
    local phase_a_variant
    for phase_a_variant in "${PHASE_A_VARIANTS[@]}"; do
        local phase_a_run="$PHASE_A_ROOT/$phase_a_variant"
        if [[ ! -s "$phase_a_run/status.json" || ! -s "$phase_a_run/training-pool-receipt.json" || ! -s "$phase_a_run/threshold-receipt.json" || ! -s "$phase_a_run/predictions/source-validation.npz" || ! -s "$phase_a_run/predictions/source-validation-receipt.json" ]]; then
            printf '阶段 A v2 有效性制品不完整：%s\n' "$phase_a_variant" >&2
            return 67
        fi
        uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
pool = json.load(open(root / "training-pool-receipt.json", encoding="utf-8"))
threshold = json.load(open(root / "threshold-receipt.json", encoding="utf-8"))
receipt = json.load(open(root / "predictions/source-validation-receipt.json", encoding="utf-8"))
probability_path = root / "predictions/source-validation.npz"
valid = (
    status.get("state") == "finished"
    and status.get("final_accessed") is False
    and pool.get("every_batch_equal_pool_counts") is True
    and pool.get("malicious_sequence_pool_count") == 116
    and pool.get("all_benign_sequence_pool_count") == 2810
    and pool.get("fixed_budget_steps") == 732
    and threshold.get("same_probability_group_split") is False
    and threshold.get("false_positive_budget_verified") is True
    and threshold.get("actual_false_positives", 1) <= threshold.get("allowed_false_positives", 0)
    and receipt.get("prediction_sha256") == hashlib.sha256(probability_path.read_bytes()).hexdigest()
    and receipt.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$phase_a_run" || {
            printf '阶段 A v2 有效性门禁失败：%s\n' "$phase_a_variant" >&2
            return 79
        }
    done
    if ! command -v uv >/dev/null 2>&1 || ! command -v rg >/dev/null 2>&1; then
        printf '远端 uv 或 rg 不可用。\n' >&2
        return 69
    fi
    if [[ "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)" -ne 0 ]]; then
        printf 'GPU 已有计算进程，拒绝叠加启动。\n' >&2
        return 75
    fi

    local batch_size
    batch_size=$(uv run --no-sync python -c \
        'import json,sys; value=json.load(open(sys.argv[1], encoding="utf-8")); assert value.get("status") == "passed"; print(value["selected_batch_size_sequences"])' \
        "$PHASE_A_GATE")
    if [[ "$batch_size" != 16 && "$batch_size" != 8 && "$batch_size" != 4 ]]; then
        printf '阶段 A 显存门禁返回非法批量：%s\n' "$batch_size" >&2
        return 78
    fi
    printf '%s\n' "$batch_size" > "$LAUNCHER_DIR/selected-batch-size.txt"

    if [[ ! -s "$PREFIX_REPRESENTATION_DIR/target-prefix-representation-manifest.json" ]]; then
        if [[ -e "$PREFIX_REPRESENTATION_DIR" ]]; then
            printf '目标前缀表示目录存在但无清单，保留证据并阻断：%s\n' "$PREFIX_REPRESENTATION_DIR" >&2
            return 73
        fi
        run_logged encode-target-prefix \
            uv run --no-sync python -m "$MODULE" encode-target-prefix \
            --cache-root "$CACHE_ROOT" \
            --receiver-checkpoint "$RECEIVER_DIR/checkpoints/best.pt" \
            --output-dir "$PREFIX_REPRESENTATION_DIR" \
            --batch-size "$batch_size"
    fi

    mkdir -p -- "$LAUNCHER_DIR/variant-locks"
    write_status running parallel-main-mechanisms none null
    run_variants_parallel "$batch_size"
    write_status finished complete all_main_mechanisms_evaluated 0
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
    printf '同名 screen 已在运行：%s\n' "$SESSION_NAME"
    exit 0
fi
if [[ -s "$STATUS_PATH" ]] && uv run --no-sync python -c \
    'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "finished" else 1)' \
    "$STATUS_PATH"; then
    printf '阶段 B 已完成，不重复启动：%s\n' "$RUN_ID"
    exit 0
fi
mkdir -p -- "$LAUNCHER_DIR" "$OUTPUT_ROOT"
printf '%s\n' "$SESSION_NAME" > "$LAUNCHER_DIR/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_DIR/command.txt"
sha256sum \
    "$CACHE_ROOT/cache-manifest.json" \
    "$RECEIVER_DIR/checkpoints/best.pt" \
    "$REPRESENTATION_DIR/representation-manifest.json" \
    src/flow_probe/c12_crossyear_models.py \
    src/flow_probe/c12_crossyear_train.py \
    "$SCRIPT_PATH" > "$LAUNCHER_DIR/input-sha256.txt"
write_status prepared launch none null
screen -dmS "$SESSION_NAME" bash "$SCRIPT_PATH" --worker
printf 'C12_PHASE_B_STARTED session=%s launcher=%s output=%s\n' \
    "$SESSION_NAME" "$LAUNCHER_DIR" "$OUTPUT_ROOT"
