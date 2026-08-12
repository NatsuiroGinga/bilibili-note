#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=candidate-b-physical-time-rwkv-q0-seed42-v1
readonly SCREEN_NAME=candidate-b-time-q0-s42-v1
readonly RUN_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/candidate-b-physical-time-rwkv-q0-seed42-v1.json"
readonly CACHE_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"
readonly REPRESENTATION_ROOT="$PROJECT_ROOT/runs/candidates/c12-phase-a-balanced-sequence-pools-q0-seed42-v2-threshold-sentinel-rerun1/frozen-representations"
readonly RECEIVER_CHECKPOINT="$PROJECT_ROOT/runs/candidates/c12-phase-a-balanced-sequence-pools-q0-seed42-v2-threshold-sentinel-rerun1/shared-receiver/checkpoints/best.pt"
readonly TARGET_PREFIX_REPRESENTATION_ROOT="$PROJECT_ROOT/runs/candidates/r1-source-time-environment-tail-risk-q0-seed42-v1/target-prefix-representation"
readonly PREPARATION_ROOT="$RUN_ROOT/preparation"
readonly VARIANT_ROOT="$RUN_ROOT/variants"
readonly EVALUATION_ROOT="$RUN_ROOT/evaluation"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_candidate_b_physical_time_q0_seed42_v1.sh"
readonly STATE_MODULE_PATH="$PROJECT_ROOT/src/flow_probe/candidate_b_time_state.py"
readonly TRAIN_MODULE_PATH="$PROJECT_ROOT/src/flow_probe/candidate_b_time_train.py"
readonly MODULE=flow_probe.candidate_b_time_train
readonly -a VARIANTS=(
    B-DISCRETE-RWKV
    B-DELTA-FEATURE
    B-DYG-SPAN
    B-LINEAR-CLIPPED
    B-ROLE-SEPARATED
)

FD_CMD=

cd "$PROJECT_ROOT"
source tools/env/activate.sh

config_integer() {
    local key=$1
    uv run --no-sync python -c '
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))[sys.argv[2]]
if not isinstance(value, int):
    raise SystemExit(1)
print(value)
' "$CONFIG_PATH" "$key"
}

readonly MAX_CONCURRENT="$(config_integer maximum_concurrent_variants)"

write_status() {
    local state=$1
    local stage=$2
    local detail=$3
    local exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    mkdir -p -- "$LAUNCHER_ROOT"
    printf '{\n' > "$partial"
    printf '  "schema_version": "candidate-b-physical-time-launcher-status-v1",\n' >> "$partial"
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

discover_capabilities() {
    if ! command -v rg >/dev/null 2>&1 || ! command -v uv >/dev/null 2>&1; then
        printf '远端 rg 或 uv 不可用。\n' >&2
        return 69
    fi
    if command -v fd >/dev/null 2>&1; then
        FD_CMD=$(command -v fd)
    elif command -v fdfind >/dev/null 2>&1; then
        FD_CMD=$(command -v fdfind)
    else
        printf '远端 fd 与 fdfind 均不可用。\n' >&2
        return 69
    fi
    printf 'fd=%s\nrg=%s\nuv=%s\n' \
        "$FD_CMD" "$(command -v rg)" "$(command -v uv)" \
        > "$LAUNCHER_ROOT/capabilities.txt"
    "$FD_CMD" --version >> "$LAUNCHER_ROOT/capabilities.txt"
    rg --version | head -n 1 >> "$LAUNCHER_ROOT/capabilities.txt"
    uv --version >> "$LAUNCHER_ROOT/capabilities.txt"
}

variant_slug() {
    case "$1" in
        B-DISCRETE-RWKV) printf '%s\n' b-discrete-rwkv ;;
        B-DELTA-FEATURE) printf '%s\n' b-delta-feature ;;
        B-DYG-SPAN) printf '%s\n' b-dyg-span ;;
        B-LINEAR-CLIPPED) printf '%s\n' b-linear-clipped ;;
        B-ROLE-SEPARATED) printf '%s\n' b-role-separated ;;
        *) return 64 ;;
    esac
}

run_logged() {
    local stage=$1
    shift
    mkdir -p -- "$LAUNCHER_ROOT"
    write_status running "$stage" started null
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

validate_static_config() {
    uv run --no-sync python -c '
import json, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))
paths = config.get("paths", {})
valid = (
    config.get("schema_version") == "candidate-b-physical-time-rwkv-q0-config-v1"
    and config.get("seed") == 42
    and config.get("epochs") == 4
    and config.get("batch_size_sequences") == 16
    and config.get("steps_per_epoch") == 183
    and config.get("total_training_steps") == 732
    and config.get("maximum_concurrent_variants") == 3
    and [item.get("key") for item in config.get("variants", [])] == [
        "B-DISCRETE-RWKV", "B-DELTA-FEATURE", "B-DYG-SPAN",
        "B-LINEAR-CLIPPED", "B-ROLE-SEPARATED"
    ]
    and config.get("frequency_branch_enabled") is False
    and config.get("comparison_thresholds", {}).get("minimum_ap_gain_over_discrete") == 0.002
    and config.get("comparison_thresholds", {}).get("shared_xgboost_ap") == 0.038902589823969644
    and config.get("swanlab", {}).get("workspace") == "mortiswang"
    and config.get("swanlab", {}).get("project") == "malicious-traffic-llm"
    and config.get("swanlab", {}).get("mode") == "online"
    and config.get("swanlab", {}).get("upload_policy") == "aggregate_metrics_and_protocol_metadata_only"
    and paths.get("output_root") == sys.argv[2]
    and paths.get("launcher_root") == sys.argv[3]
    and paths.get("cache_root") == sys.argv[4]
    and paths.get("representation_root") == sys.argv[5]
    and paths.get("receiver_checkpoint") == sys.argv[6]
    and paths.get("target_prefix_representation_root") == sys.argv[7]
    and config.get("screening_only") is True
    and config.get("formal_paper_evidence") is False
    and config.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$CONFIG_PATH" "$RUN_ROOT" "$LAUNCHER_ROOT" "$CACHE_ROOT" \
        "$REPRESENTATION_ROOT" "$RECEIVER_CHECKPOINT" \
        "$TARGET_PREFIX_REPRESENTATION_ROOT"
}

validate_preparation() {
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
manifest = json.load(open(root / "preparation-manifest.json", encoding="utf-8"))
order = root / "training-sequence-order.npy"
valid = (
    manifest.get("schema_version") == "candidate-b-physical-time-rwkv-q0-preparation-v1"
    and manifest.get("fixed_budget_steps") == 732
    and manifest.get("shared_by_variants") == [
        "B-DISCRETE-RWKV", "B-DELTA-FEATURE", "B-DYG-SPAN",
        "B-LINEAR-CLIPPED", "B-ROLE-SEPARATED"
    ]
    and manifest.get("source_train_statistics_only") is True
    and manifest.get("target_statistics_used") is False
    and order.is_file()
    and hashlib.sha256(order.read_bytes()).hexdigest() == manifest.get("training_order_sha256")
    and manifest.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$PREPARATION_ROOT"
}

validate_variant() {
    local run_dir=$1
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
receipt = json.load(open(root / "training-receipt.json", encoding="utf-8"))
variant = status.get("variant")
roles = ("source-train", "source-validation", "target-prefix", "target-development")
diagnostics = ("stable-time-shuffle", "fixed-source-median-time")
time_variants = {
    "B-DELTA-FEATURE", "B-DYG-SPAN", "B-LINEAR-CLIPPED", "B-ROLE-SEPARATED"
}
valid = (
    status.get("state") in {"probabilities_sealed_evaluation_pending", "finished"}
    and status.get("all_required_probabilities_sealed") is True
    and receipt.get("planned_epochs") == receipt.get("actual_epochs") == 4
    and receipt.get("planned_steps") == receipt.get("actual_steps") == 732
    and len(set(receipt.get("matched_trainable_parameter_counts", {}).values())) == 1
    and receipt.get("target_development_labels_used") is False
    and receipt.get("time_diagnostics_retrained") is False
    and receipt.get("final_accessed") is False
    and (root / "checkpoints/final.pt").is_file()
    and all((root / "predictions" / f"{role}.npz").is_file() for role in roles)
)
if variant in time_variants:
    valid = valid and all(
        (root / "predictions" / f"target-development--{diagnostic}.npz").is_file()
        for diagnostic in diagnostics
    )
else:
    valid = valid and receipt.get("time_diagnostic_receipts") == {}
raise SystemExit(0 if valid else 1)
' "$run_dir"
}

validate_evaluation() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
result = json.load(open(root / "results.json", encoding="utf-8"))
valid = (
    status.get("state") == "finished"
    and result.get("target_label_connected_after_all_probability_seals") is True
    and result.get("decision", {}).get("frequency_branch_tested") is False
    and result.get("screening_only") is True
    and result.get("formal_paper_evidence") is False
    and result.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$EVALUATION_ROOT"
}

run_swanlab_gate() {
    local ping_exit
    local verify_exit
    set +e
    uv run --no-sync swanlab ping > "$LAUNCHER_ROOT/swanlab-ping.log" 2>&1
    ping_exit=$?
    uv run --no-sync swanlab verify > "$LAUNCHER_ROOT/swanlab-verify.log" 2>&1
    verify_exit=$?
    set -e
    printf '{"schema_version":"candidate-b-swanlab-gate-v1","workspace":"mortiswang","project":"malicious-traffic-llm","upload_policy":"aggregate_metrics_and_protocol_metadata_only","ping_exit":%s,"verify_exit":%s,"passed":%s,"checked_at":"%s","final_accessed":false}\n' \
        "$ping_exit" "$verify_exit" \
        "$([[ "$ping_exit" -eq 0 && "$verify_exit" -eq 0 ]] && printf true || printf false)" \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$LAUNCHER_ROOT/swanlab-gate.json.partial.$$"
    mv -f -- "$LAUNCHER_ROOT/swanlab-gate.json.partial.$$" "$LAUNCHER_ROOT/swanlab-gate.json"
    if [[ "$ping_exit" -ne 0 || "$verify_exit" -ne 0 ]]; then
        printf 'SwanLab 在线门禁失败：ping=%s verify=%s\n' "$ping_exit" "$verify_exit" >&2
        return 76
    fi
}

preflight() {
    write_status running preflight started null
    validate_static_config
    discover_capabilities
    if ! command -v flock >/dev/null 2>&1 || ! command -v nvidia-smi >/dev/null 2>&1; then
        printf '远端 flock 或 nvidia-smi 不可用。\n' >&2
        return 69
    fi
    if [[ ! -s "$CACHE_ROOT/cache-manifest.json" \
        || ! -s "$REPRESENTATION_ROOT/representation-manifest.json" \
        || ! -s "$TARGET_PREFIX_REPRESENTATION_ROOT/target-prefix-representation-manifest.json" \
        || ! -s "$RECEIVER_CHECKPOINT" ]]; then
        printf '候选 B 冻结缓存、表示或接收器制品不完整。\n' >&2
        return 66
    fi
    if [[ ! -s "$CONFIG_PATH" || ! -s "$STATE_MODULE_PATH" || ! -s "$TRAIN_MODULE_PATH" ]]; then
        printf '候选 B 四个生产文件未完整同步。\n' >&2
        return 67
    fi
    if ! uv run --no-sync python -c 'import numpy, sklearn, swanlab, torch'; then
        printf '候选 B 训练依赖不可导入。\n' >&2
        return 69
    fi
    local gpu_name
    gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
    if [[ "$gpu_name" != *"RTX 5090"* ]]; then
        printf '当前 GPU 不是 C56 预期 RTX 5090：%s\n' "$gpu_name" >&2
        return 69
    fi
    local gpu_process_count
    gpu_process_count=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)
    if [[ "$gpu_process_count" -ne 0 ]]; then
        printf 'GPU 已有计算进程，拒绝叠加启动：count=%s\n' "$gpu_process_count" >&2
        return 75
    fi
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader \
        > "$LAUNCHER_ROOT/gpu-preflight.txt"
    df -Pk "$PROJECT_ROOT" > "$LAUNCHER_ROOT/disk-preflight.txt"
    uv run --no-sync python -c '
import json, pathlib, shutil, subprocess, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))
query = subprocess.check_output([
    "nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"
], text=True)
free_gib = sum(float(line.strip()) for line in query.splitlines() if line.strip()) / 1024
disk_free_gib = shutil.disk_usage(pathlib.Path(sys.argv[2])).free / 1024**3
valid = (
    free_gib >= float(config["conservative_total_peak_gpu_memory_gib"])
    and disk_free_gib >= float(config["minimum_free_disk_gib"])
)
print(json.dumps({"gpu_free_gib": free_gib, "disk_free_gib": disk_free_gib, "passed": valid}))
raise SystemExit(0 if valid else 1)
' "$CONFIG_PATH" "$PROJECT_ROOT" > "$LAUNCHER_ROOT/resource-gate.json"
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
cache = pathlib.Path(sys.argv[1])
representations = pathlib.Path(sys.argv[2])
prefix = pathlib.Path(sys.argv[3])
checkpoint = pathlib.Path(sys.argv[4])
cache_receipt = json.load(open(cache / "cache-manifest.json", encoding="utf-8"))
representation_receipt = json.load(open(representations / "representation-manifest.json", encoding="utf-8"))
prefix_receipt = json.load(open(prefix / "target-prefix-representation-manifest.json", encoding="utf-8"))
valid = (
    cache_receipt.get("schema_version") == "lspr-crossyear-python-cache-v1"
    and cache_receipt.get("final_accessed") is False
    and representation_receipt.get("schema_version") == "c12-crossyear-receiver-representations-v1"
    and representation_receipt.get("excluded_roles") == ["target-prefix"]
    and representation_receipt.get("cache_manifest_sha256") == hashlib.sha256((cache / "cache-manifest.json").read_bytes()).hexdigest()
    and representation_receipt.get("receiver_checkpoint_sha256") == hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    and representation_receipt.get("final_accessed") is False
    and prefix_receipt.get("schema_version") == "c12-target-prefix-representation-v1"
    and prefix_receipt.get("labels_read") is False
    and prefix_receipt.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$CACHE_ROOT" "$REPRESENTATION_ROOT" "$TARGET_PREFIX_REPRESENTATION_ROOT" \
        "$RECEIVER_CHECKPOINT"
    run_swanlab_gate
}

run_variant() {
    local variant=$1
    local slug
    slug=$(variant_slug "$variant")
    local run_dir="$VARIANT_ROOT/$slug"
    local lock_path="$LAUNCHER_ROOT/train-${slug}.lock"
    exec 9> "$lock_path"
    if ! flock -n 9; then
        printf '训练锁已被占用，拒绝重复启动：%s\n' "$variant" >&2
        return 75
    fi
    if [[ -s "$run_dir/status.json" ]] && validate_variant "$run_dir"; then
        printf '变体已有合法概率封存，幂等跳过：%s\n' "$variant"
        return 0
    fi
    if [[ -e "$run_dir" && ! -s "$run_dir/checkpoints/latest.pt" ]]; then
        printf '变体存在不完整证据且无恢复检查点，保留并阻断：%s\n' "$run_dir" >&2
        return 73
    fi
    mkdir -p -- "$run_dir"
    set +e
    uv run --no-sync python -m "$MODULE" train \
        --cache-root "$CACHE_ROOT" \
        --representation-root "$REPRESENTATION_ROOT" \
        --target-prefix-representation-root "$TARGET_PREFIX_REPRESENTATION_ROOT" \
        --preparation-root "$PREPARATION_ROOT" \
        --output-dir "$run_dir" \
        --config "$CONFIG_PATH" \
        --variant "$variant" \
        --run-name "${RUN_ID}-${slug}" 2>&1 | tee "$run_dir/run.log"
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

run_parallel_training() {
    local -a pids=()
    local -a names=()
    local failed=0
    local variant
    local index
    write_status running parallel-training max_concurrent_3 null
    for variant in "${VARIANTS[@]}"; do
        run_variant "$variant" &
        pids+=("$!")
        names+=("$variant")
        if [[ "${#pids[@]}" -ge "$MAX_CONCURRENT" ]]; then
            set +e
            for index in "${!pids[@]}"; do
                wait "${pids[$index]}"
                local code=$?
                printf '%s\n' "$code" > "$LAUNCHER_ROOT/train-$(variant_slug "${names[$index]}")-exit-code.txt"
                if [[ "$code" -ne 0 ]]; then
                    failed=1
                fi
            done
            set -e
            pids=()
            names=()
        fi
    done
    set +e
    for index in "${!pids[@]}"; do
        wait "${pids[$index]}"
        local code=$?
        printf '%s\n' "$code" > "$LAUNCHER_ROOT/train-$(variant_slug "${names[$index]}")-exit-code.txt"
        if [[ "$code" -ne 0 ]]; then
            failed=1
        fi
    done
    set -e
    if [[ "$failed" -ne 0 ]]; then
        write_status failed parallel-training variant_failed 1
        return 1
    fi
}

worker_main() {
    mkdir -p -- "$LAUNCHER_ROOT" "$RUN_ROOT" "$VARIANT_ROOT"
    preflight
    if [[ -s "$PREPARATION_ROOT/preparation-manifest.json" ]]; then
        validate_preparation
        printf '候选 B 共同准备制品合法，幂等跳过。\n'
    else
        if [[ -e "$PREPARATION_ROOT" ]]; then
            printf '准备目录存在但未合法完成，保留并阻断：%s\n' "$PREPARATION_ROOT" >&2
            return 73
        fi
        run_logged prepare \
            uv run --no-sync python -m "$MODULE" prepare \
            --cache-root "$CACHE_ROOT" \
            --representation-root "$REPRESENTATION_ROOT" \
            --target-prefix-representation-root "$TARGET_PREFIX_REPRESENTATION_ROOT" \
            --output-dir "$PREPARATION_ROOT" \
            --config "$CONFIG_PATH"
        validate_preparation
    fi
    run_parallel_training
    local variant
    for variant in "${VARIANTS[@]}"; do
        validate_variant "$VARIANT_ROOT/$(variant_slug "$variant")"
    done
    if [[ -s "$EVALUATION_ROOT/status.json" ]] && validate_evaluation; then
        printf '候选 B 独立评价已有合法完成状态，幂等跳过。\n'
    else
        if [[ -e "$EVALUATION_ROOT" ]]; then
            printf '评价目录存在但未合法完成，保留并阻断：%s\n' "$EVALUATION_ROOT" >&2
            return 73
        fi
        run_logged evaluate \
            uv run --no-sync python -m "$MODULE" evaluate \
            --cache-root "$CACHE_ROOT" \
            --preparation-root "$PREPARATION_ROOT" \
            --run-root "$RUN_ROOT" \
            --output-dir "$EVALUATION_ROOT" \
            --config "$CONFIG_PATH"
        validate_evaluation
    fi
    write_status finished complete evaluation_finished 0
}

worker_entry() {
    trap 'write_status interrupted signal received 130; exit 130' HUP INT TERM
    mkdir -p -- "$LAUNCHER_ROOT"
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
    worker_entry
    exit $?
fi

mkdir -p -- "$LAUNCHER_ROOT" "$RUN_ROOT"
validate_static_config
discover_capabilities
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
    printf '候选 B Q0 已完成，不重复启动：%s\n' "$RUN_ID"
    exit 0
fi
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_ROOT/command.txt"
sha256sum \
    "$CACHE_ROOT/cache-manifest.json" \
    "$REPRESENTATION_ROOT/representation-manifest.json" \
    "$RECEIVER_CHECKPOINT" \
    "$TARGET_PREFIX_REPRESENTATION_ROOT/target-prefix-representation-manifest.json" \
    "$CONFIG_PATH" \
    "$STATE_MODULE_PATH" \
    "$TRAIN_MODULE_PATH" \
    "$SCRIPT_PATH" > "$LAUNCHER_ROOT/input-sha256.txt"
write_status prepared launch static_contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'CANDIDATE_B_PHYSICAL_TIME_Q0_STARTED session=%s launcher=%s output=%s max_concurrent=%s final_accessed=false formal_paper_evidence=false\n' \
    "$SCREEN_NAME" "$LAUNCHER_ROOT" "$RUN_ROOT" "$MAX_CONCURRENT"
