#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly CACHE_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"
readonly RUN_ID=c12-phase-a-q0-seed42-v1
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly RECEIVER_DIR="$OUTPUT_ROOT/shared-receiver"
readonly REPRESENTATION_DIR="$OUTPUT_ROOT/frozen-representations"
readonly LAUNCHER_DIR="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_DIR/status.json"
readonly GATE_PATH="$LAUNCHER_DIR/gpu-gate.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_c12_phase_a_q0_seed42_v1.sh"
readonly SESSION_NAME=c12-phase-a-q0-s42
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
    printf '  "schema_version": "c12-phase-a-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "updated_at": "%s",\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$partial"
    printf '  "single_gpu_serial": true,\n' >> "$partial"
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
        printf '变体已有完成状态，跳过：%s\n' "$variant"
        return 0
    fi
    if [[ -s "$status" ]] && uv run --no-sync python -c \
        'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "predictions_sealed_evaluation_pending" else 1)' \
        "$status"; then
        run_logged "evaluate-${slug}" \
            uv run --no-sync python -m "$MODULE" evaluate \
            --cache-root "$CACHE_ROOT" \
            --run-dir "$run_dir"
        return 0
    fi
    if [[ -e "$run_dir" ]]; then
        printf '变体目录存在但不可安全续跑，保留证据并阻断：%s\n' "$run_dir" >&2
        return 73
    fi

    run_logged "train-${slug}" \
        uv run --no-sync python -m "$MODULE" train-variant \
        --cache-root "$CACHE_ROOT" \
        --representation-root "$REPRESENTATION_DIR" \
        --output-dir "$run_dir" \
        --run-name "${RUN_ID}-${slug}" \
        --variant "$variant" \
        --batch-size "$batch_size" \
        --epochs "$EPOCHS" \
        --seed "$SEED"
    run_logged "evaluate-${slug}" \
        uv run --no-sync python -m "$MODULE" evaluate \
        --cache-root "$CACHE_ROOT" \
        --run-dir "$run_dir"
}

worker_main() {
    write_status running preflight none null
    if [[ ! -s "$CACHE_ROOT/cache-manifest.json" ]]; then
        printf 'Q0 Python 缓存清单不存在：%s\n' "$CACHE_ROOT/cache-manifest.json" >&2
        return 66
    fi
    if [[ ! -s src/flow_probe/c12_crossyear_models.py || ! -s src/flow_probe/c12_crossyear_train.py ]]; then
        printf '阶段 A Python 实现不完整。\n' >&2
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
            printf '共同接收器目录存在但无完成状态，保留证据并阻断：%s\n' "$RECEIVER_DIR" >&2
            return 73
        fi
        run_logged train-receiver \
            uv run --no-sync python -m "$MODULE" train-receiver \
            --cache-root "$CACHE_ROOT" \
            --output-dir "$RECEIVER_DIR" \
            --run-name "${RUN_ID}-shared-receiver" \
            --batch-size "$batch_size" \
            --epochs "$EPOCHS" \
            --seed "$SEED"
    elif ! uv run --no-sync python -c \
        'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "finished" else 1)' \
        "$RECEIVER_DIR/status.json"; then
        printf '共同接收器不是完成状态，拒绝覆盖。\n' >&2
        return 73
    fi

    if [[ ! -s "$REPRESENTATION_DIR/representation-manifest.json" ]]; then
        if [[ -e "$REPRESENTATION_DIR" ]]; then
            printf '冻结表示目录存在但无清单，保留证据并阻断：%s\n' "$REPRESENTATION_DIR" >&2
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
    printf '同名 screen 已在运行：%s\n' "$SESSION_NAME"
    exit 0
fi
if [[ -s "$STATUS_PATH" ]] && uv run --no-sync python -c \
    'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "finished" else 1)' \
    "$STATUS_PATH"; then
    printf '阶段 A 已完成，不重复启动：%s\n' "$RUN_ID"
    exit 0
fi
mkdir -p -- "$LAUNCHER_DIR" "$OUTPUT_ROOT"
printf '%s\n' "$SESSION_NAME" > "$LAUNCHER_DIR/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_DIR/command.txt"
sha256sum \
    "$CACHE_ROOT/cache-manifest.json" \
    src/flow_probe/c12_crossyear_models.py \
    src/flow_probe/c12_crossyear_train.py \
    "$SCRIPT_PATH" > "$LAUNCHER_DIR/input-sha256.txt"
write_status prepared launch none null
screen -dmS "$SESSION_NAME" bash "$SCRIPT_PATH" --worker
printf 'C12_PHASE_A_STARTED session=%s launcher=%s output=%s\n' \
    "$SESSION_NAME" "$LAUNCHER_DIR" "$OUTPUT_ROOT"
