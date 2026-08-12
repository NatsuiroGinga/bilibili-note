#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly CACHE_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"
readonly RUN_ID=c12-phase-a-balanced-sequence-pools-q0-seed42-v2-threshold-sentinel-rerun1
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly RECEIVER_DIR="$OUTPUT_ROOT/shared-receiver"
readonly REPRESENTATION_DIR="$OUTPUT_ROOT/frozen-representations"
readonly LAUNCHER_DIR="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_DIR/status.json"
readonly GATE_PATH="$LAUNCHER_DIR/gpu-gate.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_c12_phase_a_q0_seed42_v2.sh"
readonly PHASE_B_SCRIPT="$PROJECT_ROOT/scripts/remote_launchers/run_c12_phase_b_q0_seed42_v1.sh"
readonly SESSION_NAME=c12-phase-a-balanced-q0-s42-v2
readonly MODULE=flow_probe.c12_crossyear_train
readonly EPOCHS=4
readonly SEED=42
readonly -a VARIANTS=(RX-TR K-RWKV7 K-DELTA K-GDELTA GRU)

cd "$PROJECT_ROOT"
source tools/env/activate.sh

write_status() {
    local state=$1
    local stage=$2
    local detail=$3
    local exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    printf '{\n' > "$partial"
    printf '  "schema_version": "c12-phase-a-v2-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "updated_at": "%s",\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$partial"
    printf '  "balanced_sequence_pools_required": true,\n' >> "$partial"
    printf '  "observable_probability_group_threshold_required": true,\n' >> "$partial"
    printf '  "source_validation_probabilities_required": true,\n' >> "$partial"
    printf '  "target_prefix_adaptation": false,\n' >> "$partial"
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
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

validate_pool_receipt() {
    local receipt=$1
    uv run --no-sync python -c '
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
valid = (
    value.get("malicious_sequence_pool_count") == 116
    and value.get("all_benign_sequence_pool_count") == 2810
    and value.get("malicious_sequences_per_batch") == value.get("all_benign_sequences_per_batch")
    and value.get("malicious_draws_per_epoch") == value.get("all_benign_draws_per_epoch")
    and value.get("every_batch_equal_pool_counts") is True
    and value.get("fixed_budget_steps") == 732
    and value.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$receipt"
}

validate_receiver_contract() {
    local receiver_dir=$1
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status_path = root / "status.json"
receipt_path = root / "training-pool-receipt.json"
best_path = root / "checkpoints/best.pt"
if not status_path.is_file() or not receipt_path.is_file() or not best_path.is_file():
    raise SystemExit(1)
status = json.load(open(status_path, encoding="utf-8"))
receipt = json.load(open(receipt_path, encoding="utf-8"))
valid = (
    status.get("state") == "finished"
    and status.get("final_accessed") is False
    and receipt.get("state") == "finished"
    and receipt.get("planned_epochs") == 4
    and receipt.get("planned_steps") == 732
    and receipt.get("actual_epochs") == 4
    and receipt.get("actual_steps") == 732
    and receipt.get("malicious_sequence_pool_count") == 116
    and receipt.get("all_benign_sequence_pool_count") == 2810
    and receipt.get("malicious_sequences_per_batch") == receipt.get("all_benign_sequences_per_batch") == 8
    and receipt.get("actual_malicious_draws_total") == receipt.get("planned_malicious_draws_total")
    and receipt.get("actual_all_benign_draws_total") == receipt.get("planned_all_benign_draws_total")
    and receipt.get("every_batch_equal_pool_counts") is True
    and receipt.get("final_accessed") is False
    and best_path.stat().st_size > 0
)
raise SystemExit(0 if valid else 1)
' "$receiver_dir"
}

validate_variant_contract() {
    local run_dir=$1
    validate_pool_receipt "$run_dir/training-pool-receipt.json"
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
import numpy as np
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
threshold = json.load(open(root / "threshold-receipt.json", encoding="utf-8"))
receipt = json.load(open(root / "predictions/source-validation-receipt.json", encoding="utf-8"))
path = root / "predictions/source-validation.npz"
digest = hashlib.sha256(path.read_bytes()).hexdigest()
with np.load(path, allow_pickle=False) as values:
    valid_arrays = (
        values["probability"].shape == (262136,)
        and values["sample_id"].shape[0] == 262136
        and values["sequence_id"].shape[0] == 262136
        and values["position"].shape == (262136,)
        and values["valid_length"].shape == (262136,)
        and np.isfinite(values["probability"]).all()
    )
valid = (
    status.get("state") == "finished"
    and status.get("final_accessed") is False
    and threshold.get("schema_version") == "c12-source-validation-threshold-v2"
    and threshold.get("same_probability_group_split") is False
    and threshold.get("false_positive_budget_verified") is True
    and threshold.get("actual_false_positives", 1) <= threshold.get("allowed_false_positives", 0)
    and receipt.get("schema_version") == "c12-source-validation-predictions-v2"
    and receipt.get("prediction_sha256") == digest
    and receipt.get("target_label_used") is False
    and receipt.get("final_accessed") is False
    and valid_arrays
)
raise SystemExit(0 if valid else 1)
' "$run_dir"
}

run_variant() {
    local variant=$1
    local batch_size=$2
    local slug
    slug=$(printf '%s' "$variant" | tr '[:upper:]' '[:lower:]')
    local run_dir="$OUTPUT_ROOT/$variant"
    local status="$run_dir/status.json"

    if [[ -s "$status" ]] && uv run --no-sync python -c \
        'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "finished" else 1)' \
        "$status"; then
        validate_variant_contract "$run_dir"
        printf '阶段 A v2 变体已有有效完成状态，跳过：%s\n' "$variant"
        return 0
    fi
    if [[ -s "$status" ]] && uv run --no-sync python -c \
        'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "predictions_sealed_evaluation_pending" else 1)' \
        "$status"; then
        run_logged "evaluate-${slug}" \
            uv run --no-sync python -m "$MODULE" evaluate \
            --cache-root "$CACHE_ROOT" \
            --run-dir "$run_dir"
        validate_variant_contract "$run_dir"
        return 0
    fi
    if [[ -e "$run_dir" ]]; then
        printf '阶段 A v2 变体目录存在但不可安全续跑，保留证据并阻断：%s\n' "$run_dir" >&2
        return 73
    fi

    run_logged "train-${slug}" \
        uv run --no-sync python -m "$MODULE" train-variant \
        --cache-root "$CACHE_ROOT" \
        --representation-root "$REPRESENTATION_DIR" \
        --output-dir "$run_dir" \
        --run-name "${RUN_ID}-${slug}-balanced-sequence-pools" \
        --variant "$variant" \
        --batch-size "$batch_size" \
        --epochs "$EPOCHS" \
        --seed "$SEED"
    run_logged "evaluate-${slug}" \
        uv run --no-sync python -m "$MODULE" evaluate \
        --cache-root "$CACHE_ROOT" \
        --run-dir "$run_dir"
    validate_variant_contract "$run_dir"
}

worker_main() {
    write_status running preflight none null
    if [[ ! -s "$CACHE_ROOT/cache-manifest.json" ]]; then
        printf 'Q0 Python 缓存清单不存在。\n' >&2
        return 66
    fi
    if [[ ! -s src/flow_probe/c12_crossyear_models.py || ! -s src/flow_probe/c12_crossyear_train.py ]]; then
        printf '阶段 A v2 Python 实现不完整。\n' >&2
        return 67
    fi
    if [[ ! -s "$PHASE_B_SCRIPT" ]]; then
        printf '阶段 B 衔接启动器不存在。\n' >&2
        return 67
    fi
    if ! command -v uv >/dev/null 2>&1 || ! command -v rg >/dev/null 2>&1; then
        printf '远端 uv 或 rg 不可用。\n' >&2
        return 69
    fi
    if [[ "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)" -ne 0 ]]; then
        printf 'GPU 已有计算进程，拒绝叠加启动。\n' >&2
        return 75
    fi

    run_logged probe \
        uv run --no-sync python -m "$MODULE" probe \
        --cache-root "$CACHE_ROOT" \
        --batch-size 2 \
        --device cuda
    run_logged gpu-gate \
        uv run --no-sync python -m "$MODULE" gpu-gate \
        --cache-root "$CACHE_ROOT" \
        --output "$GATE_PATH"

    local batch_size
    batch_size=$(uv run --no-sync python -c \
        'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["selected_batch_size_sequences"])' \
        "$GATE_PATH")
    if [[ "$batch_size" != 16 && "$batch_size" != 8 && "$batch_size" != 4 ]]; then
        printf '显存门禁返回非法批量：%s\n' "$batch_size" >&2
        return 78
    fi
    printf '%s\n' "$batch_size" > "$LAUNCHER_DIR/selected-batch-size.txt"

    if [[ ! -s "$RECEIVER_DIR/status.json" ]]; then
        if [[ -e "$RECEIVER_DIR" ]]; then
            printf 'v2 共同接收器目录存在但无完成状态，保留证据并阻断。\n' >&2
            return 73
        fi
        run_logged train-receiver \
            uv run --no-sync python -m "$MODULE" train-receiver \
            --cache-root "$CACHE_ROOT" \
            --output-dir "$RECEIVER_DIR" \
            --run-name "${RUN_ID}-shared-receiver-balanced-sequence-pools" \
            --batch-size "$batch_size" \
            --epochs "$EPOCHS" \
            --seed "$SEED"
    fi
    if ! validate_receiver_contract "$RECEIVER_DIR"; then
        printf '共同接收器不是完整完成状态，保留证据并阻断：%s\n' "$RECEIVER_DIR" >&2
        return 73
    fi

    if [[ ! -s "$REPRESENTATION_DIR/representation-manifest.json" ]]; then
        if [[ -e "$REPRESENTATION_DIR" ]]; then
            printf 'v2 冻结表示目录存在但无清单，保留证据并阻断。\n' >&2
            return 73
        fi
        run_logged encode-receiver \
            uv run --no-sync python -m "$MODULE" encode-receiver \
            --cache-root "$CACHE_ROOT" \
            --receiver-checkpoint "$RECEIVER_DIR/checkpoints/best.pt" \
            --output-dir "$REPRESENTATION_DIR" \
            --batch-size "$batch_size"
    fi

    local variant
    for variant in "${VARIANTS[@]}"; do
        run_variant "$variant" "$batch_size"
    done
    write_status finished complete all_variants_validated 0
    run_logged launch-phase-b bash "$PHASE_B_SCRIPT"
    write_status finished complete all_variants_validated_phase_b_started 0
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
    printf '阶段 A v2 已完成，不重复启动：%s\n' "$RUN_ID"
    exit 0
fi
mkdir -p -- "$LAUNCHER_DIR" "$OUTPUT_ROOT"
printf '%s\n' "$SESSION_NAME" > "$LAUNCHER_DIR/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_DIR/command.txt"
sha256sum \
    "$CACHE_ROOT/cache-manifest.json" \
    src/flow_probe/c12_crossyear_models.py \
    src/flow_probe/c12_crossyear_train.py \
    "$SCRIPT_PATH" \
    "$PHASE_B_SCRIPT" > "$LAUNCHER_DIR/input-sha256.txt"
write_status prepared launch none null
screen -dmS "$SESSION_NAME" bash "$SCRIPT_PATH" --worker
printf 'C12_PHASE_A_V2_STARTED session=%s launcher=%s output=%s\n' \
    "$SESSION_NAME" "$LAUNCHER_DIR" "$OUTPUT_ROOT"
