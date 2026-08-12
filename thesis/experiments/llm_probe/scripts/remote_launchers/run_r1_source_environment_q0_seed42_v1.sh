#!/usr/bin/env bash

if [[ -r "${HOME}/.bashrc" ]]; then
    source "${HOME}/.bashrc" >/dev/null 2>&1
fi
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=r1-source-time-environment-robust-state-q0-seed42-v1
readonly SCREEN_NAME=r1-source-env-q0-s42-v1
readonly RUN_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly ENVIRONMENT_ROOT="$RUN_ROOT/environments"
readonly VARIANT_ROOT="$RUN_ROOT/variants"
readonly EVALUATION_ROOT="$RUN_ROOT/evaluation"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/r1-source-environment-q0-seed42-v1.json"
readonly CACHE_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"
readonly REPRESENTATION_ROOT="$PROJECT_ROOT/runs/candidates/c12-phase-a-balanced-sequence-pools-q0-seed42-v2-threshold-sentinel-rerun1/frozen-representations"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_r1_source_environment_q0_seed42_v1.sh"
readonly MODULE=flow_probe.r1_source_environment
readonly MAX_CONCURRENT=3
readonly -a VARIANTS=(B0 GROUPDRO M1)

cd "$PROJECT_ROOT"
source tools/env/activate.sh

write_status() {
    local state=$1
    local stage=$2
    local detail=$3
    local exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    printf '{\n' > "$partial"
    printf '  "schema_version": "r1-source-environment-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "maximum_concurrent_variants": %s,\n' "$MAX_CONCURRENT" >> "$partial"
    printf '  "output_root": "%s",\n' "$RUN_ROOT" >> "$partial"
    printf '  "updated_at": "%s",\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$partial"
    printf '  "screening_only": true,\n' >> "$partial"
    printf '  "formal_paper_evidence": false,\n' >> "$partial"
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

run_logged() {
    local stage=$1
    shift
    write_status running "$stage" none null
    set +e
    "$@" 2>&1 | tee "$LAUNCHER_ROOT/${stage}.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$LAUNCHER_ROOT/${stage}-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_ROOT/${stage}-tee-exit-code.txt"
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
        B0) printf '%s\n' b0 ;;
        GROUPDRO) printf '%s\n' groupdro ;;
        M1) printf '%s\n' m1 ;;
        *) return 64 ;;
    esac
}

validate_environment() {
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
manifest = json.load(open(root / "environment-manifest.json", encoding="utf-8"))
valid = (
    manifest.get("schema_version") == "r1-source-time-environments-q0-v1"
    and manifest.get("observability_gate") == "passed"
    and manifest.get("labels_used_for_partition") is False
    and manifest.get("environment_or_group_used_as_model_input") is False
    and manifest.get("final_accessed") is False
)
for name, record in manifest.get("arrays", {}).items():
    path = root / name
    valid = valid and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == record.get("sha256")
raise SystemExit(0 if valid else 1)
' "$ENVIRONMENT_ROOT"
}

validate_variant() {
    local run_dir=$1
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
receipt = json.load(open(root / "training-receipt.json", encoding="utf-8"))
valid = (
    status.get("state") in {"probabilities_sealed_evaluation_pending", "finished"}
    and status.get("final_accessed") is False
    and receipt.get("state") == "probabilities_sealed_evaluation_pending"
    and receipt.get("planned_epochs") == receipt.get("actual_epochs") == 4
    and receipt.get("planned_steps") == receipt.get("actual_steps")
    and receipt.get("target_development_labels_used") is False
    and receipt.get("final_accessed") is False
    and (root / "checkpoints/final.pt").is_file()
    and (root / "predictions/source-validation.npz").is_file()
    and (root / "predictions/target-development.npz").is_file()
    and (root / "representations/manifest.json").is_file()
)
raise SystemExit(0 if valid else 1)
' "$run_dir"
}

run_swanlab_gate() {
    local variant=$1
    local slug
    slug=$(variant_slug "$variant")
    local ping_log="$LAUNCHER_ROOT/${slug}-swanlab-ping.log"
    local verify_log="$LAUNCHER_ROOT/${slug}-swanlab-verify.log"
    local receipt="$LAUNCHER_ROOT/${slug}-swanlab-gate.json"
    local ping_exit
    local verify_exit
    set +e
    uv run --no-sync swanlab ping > "$ping_log" 2>&1
    ping_exit=$?
    uv run --no-sync swanlab verify > "$verify_log" 2>&1
    verify_exit=$?
    set -e
    printf '{"schema_version":"r1-swanlab-gate-v1","variant":"%s","ping_exit":%s,"verify_exit":%s,"passed":%s,"checked_at":"%s","final_accessed":false}\n' \
        "$variant" "$ping_exit" "$verify_exit" \
        "$([[ "$ping_exit" -eq 0 && "$verify_exit" -eq 0 ]] && printf true || printf false)" \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$receipt.partial.$$"
    mv -f -- "$receipt.partial.$$" "$receipt"
    if [[ "$ping_exit" -ne 0 || "$verify_exit" -ne 0 ]]; then
        printf 'SwanLab 门禁失败：variant=%s ping=%s verify=%s\n' \
            "$variant" "$ping_exit" "$verify_exit" >&2
        return 76
    fi
}

run_variant() {
    local variant=$1
    local slug
    slug=$(variant_slug "$variant")
    local run_dir="$VARIANT_ROOT/$slug"
    local lock_path="$LAUNCHER_ROOT/${slug}.lock"
    local log_path="$run_dir/run.log"
    mkdir -p -- "$run_dir"
    exec 9> "$lock_path"
    if ! flock -n 9; then
        printf '变体锁已被占用，拒绝重复启动：%s\n' "$variant" >&2
        return 75
    fi
    if [[ -s "$run_dir/status.json" ]] && validate_variant "$run_dir"; then
        printf '变体已有合法封存概率，幂等跳过：%s\n' "$variant"
        return 0
    fi
    if [[ -e "$run_dir/config.json" && ! -s "$run_dir/checkpoints/latest.pt" ]]; then
        printf '变体存在不完整证据且无恢复检查点，保留并阻断：%s\n' "$run_dir" >&2
        return 73
    fi
    set +e
    uv run --no-sync python -m "$MODULE" train \
        --cache-root "$CACHE_ROOT" \
        --representation-root "$REPRESENTATION_ROOT" \
        --environment-root "$ENVIRONMENT_ROOT" \
        --output-dir "$run_dir" \
        --config "$CONFIG_PATH" \
        --variant "$variant" \
        --run-name "${RUN_ID}-${slug}" 2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$run_dir/command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$run_dir/tee-exit-code.txt"
    if [[ "$command_code" -ne 0 ]]; then
        return "$command_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        return "$tee_code"
    fi
    validate_variant "$run_dir"
}

worker_main() {
    write_status running preflight none null
    if ! command -v uv >/dev/null 2>&1 || ! command -v rg >/dev/null 2>&1; then
        printf '远端 uv 或 rg 不可用。\n' >&2
        return 69
    fi
    if ! command -v flock >/dev/null 2>&1 || ! command -v nvidia-smi >/dev/null 2>&1; then
        printf '远端 flock 或 nvidia-smi 不可用。\n' >&2
        return 69
    fi
    if [[ ! -s "$CACHE_ROOT/cache-manifest.json" ]]; then
        printf 'Q0 Python 缓存清单不存在。\n' >&2
        return 66
    fi
    if [[ ! -s "$REPRESENTATION_ROOT/representation-manifest.json" ]]; then
        printf '阶段 A v2 冻结表示清单不存在。\n' >&2
        return 66
    fi
    if [[ ! -s "$CONFIG_PATH" || ! -s "$PROJECT_ROOT/src/flow_probe/r1_source_environment.py" ]]; then
        printf 'R1 配置或 Python 入口不存在。\n' >&2
        return 67
    fi
    if ! uv run --no-sync python -c 'import numpy, pyarrow, sklearn, swanlab, torch'; then
        printf 'R1 所需依赖不可导入。\n' >&2
        return 69
    fi
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))
valid = (
    config.get("maximum_concurrent_variants") == 3
    and config.get("conservative_total_peak_gpu_memory_gib", 99) < 8.01
    and config.get("final_accessed") is False
    and config.get("promotion_thresholds", {}).get("m1_ap_delta_groupdro_minimum") == -0.002
)
raise SystemExit(0 if valid else 1)
' "$CONFIG_PATH"
    local gpu_process_count
    gpu_process_count=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
    if [[ "$gpu_process_count" -ne 0 ]]; then
        printf 'GPU 已有计算进程，拒绝叠加启动：count=%s\n' "$gpu_process_count" >&2
        return 75
    fi
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader \
        > "$LAUNCHER_ROOT/gpu-preflight.txt"

    if [[ -s "$ENVIRONMENT_ROOT/environment-manifest.json" ]]; then
        validate_environment
        printf '环境侧车已有合法完成状态，幂等跳过。\n'
    else
        if [[ -e "$ENVIRONMENT_ROOT" ]]; then
            printf '环境侧车目录存在但未合法完成，保留并阻断。\n' >&2
            return 73
        fi
        run_logged prepare-environments \
            uv run --no-sync python -m "$MODULE" prepare-environments \
            --cache-root "$CACHE_ROOT" \
            --representation-root "$REPRESENTATION_ROOT" \
            --output-dir "$ENVIRONMENT_ROOT" \
            --config "$CONFIG_PATH"
        validate_environment
    fi

    local variant
    for variant in "${VARIANTS[@]}"; do
        run_swanlab_gate "$variant"
    done

    write_status running parallel-training max_concurrent_3 null
    local -a pids=()
    local -a names=()
    for variant in "${VARIANTS[@]}"; do
        run_variant "$variant" &
        pids+=("$!")
        names+=("$variant")
    done
    local failed=0
    local index
    set +e
    for index in "${!pids[@]}"; do
        wait "${pids[$index]}"
        local code=$?
        printf '%s\n' "$code" > "$LAUNCHER_ROOT/$(variant_slug "${names[$index]}")-worker-exit-code.txt"
        if [[ "$code" -ne 0 ]]; then
            printf '变体训练失败：variant=%s exit=%s\n' "${names[$index]}" "$code" >&2
            failed=1
        fi
    done
    set -e
    if [[ "$failed" -ne 0 ]]; then
        write_status failed parallel-training variant_failed 1
        return 1
    fi
    for variant in "${VARIANTS[@]}"; do
        validate_variant "$VARIANT_ROOT/$(variant_slug "$variant")"
    done

    if [[ -s "$EVALUATION_ROOT/status.json" ]] && uv run --no-sync python -c \
        'import json,sys; value=json.load(open(sys.argv[1], encoding="utf-8")); raise SystemExit(0 if value.get("state") == "finished" and value.get("final_accessed") is False else 1)' \
        "$EVALUATION_ROOT/status.json"; then
        printf '四格评价已有完成状态，幂等跳过。\n'
    else
        if [[ -e "$EVALUATION_ROOT" ]]; then
            printf '评价目录存在但未合法完成，保留并阻断。\n' >&2
            return 73
        fi
        run_logged evaluate-grid \
            uv run --no-sync python -m "$MODULE" evaluate-grid \
            --cache-root "$CACHE_ROOT" \
            --representation-root "$REPRESENTATION_ROOT" \
            --environment-root "$ENVIRONMENT_ROOT" \
            --run-root "$RUN_ROOT" \
            --output-dir "$EVALUATION_ROOT" \
            --config "$CONFIG_PATH"
    fi
    write_status finished complete evaluation_finished 0
}

worker_entry() {
    trap 'write_status interrupted signal received 130; exit 130' HUP INT TERM
    set +e
    worker_main 2>&1 | tee "$LAUNCHER_ROOT/controller.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local worker_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$worker_code" > "$LAUNCHER_ROOT/controller-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_ROOT/controller-tee-exit-code.txt"
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
    mkdir -p -- "$LAUNCHER_ROOT" "$RUN_ROOT"
    worker_entry
    exit $?
fi

if ! command -v screen >/dev/null 2>&1; then
    printf '远端缺少 screen。\n' >&2
    exit 69
fi
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名 screen 已在运行：%s\n' "$SCREEN_NAME"
    exit 0
fi
if [[ -s "$STATUS_PATH" ]] && uv run --no-sync python -c \
    'import json,sys; value=json.load(open(sys.argv[1], encoding="utf-8")); raise SystemExit(0 if value.get("state") == "finished" and value.get("final_accessed") is False else 1)' \
    "$STATUS_PATH"; then
    printf 'R1 Q0 已完成，不重复启动：%s\n' "$RUN_ID"
    exit 0
fi
mkdir -p -- "$LAUNCHER_ROOT" "$RUN_ROOT"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_ROOT/command.txt"
sha256sum \
    "$CACHE_ROOT/cache-manifest.json" \
    "$REPRESENTATION_ROOT/representation-manifest.json" \
    "$CONFIG_PATH" \
    "$PROJECT_ROOT/src/flow_probe/r1_source_environment.py" \
    "$PROJECT_ROOT/src/flow_probe/c12_crossyear_models.py" \
    "$PROJECT_ROOT/src/flow_probe/c12_crossyear_train.py" \
    "$SCRIPT_PATH" > "$LAUNCHER_ROOT/input-sha256.txt"
write_status prepared launch none null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'R1_SOURCE_ENVIRONMENT_Q0_STARTED session=%s launcher=%s output=%s final_accessed=false formal_paper_evidence=false\n' \
    "$SCREEN_NAME" "$LAUNCHER_ROOT" "$RUN_ROOT"
