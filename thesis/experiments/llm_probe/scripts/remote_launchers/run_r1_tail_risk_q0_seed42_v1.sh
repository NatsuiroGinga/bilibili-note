#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=r1-source-time-environment-tail-risk-q0-seed42-v1
readonly SCREEN_NAME=r1-tail-risk-q0-s42-v1
readonly RUN_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/r1-tail-risk-q0-seed42-v1.json"
readonly CACHE_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"
readonly REPRESENTATION_ROOT="$PROJECT_ROOT/runs/candidates/c12-phase-a-balanced-sequence-pools-q0-seed42-v2-threshold-sentinel-rerun1/frozen-representations"
readonly RECEIVER_CHECKPOINT="$PROJECT_ROOT/runs/candidates/c12-phase-a-balanced-sequence-pools-q0-seed42-v2-threshold-sentinel-rerun1/shared-receiver/checkpoints/best.pt"
readonly TARGET_PREFIX_REPRESENTATION_ROOT="$RUN_ROOT/target-prefix-representation"
readonly ENVIRONMENT_ROOT="$RUN_ROOT/environments"
readonly VARIANT_ROOT="$RUN_ROOT/variants"
readonly RISK_ROOT="$RUN_ROOT/risks"
readonly EVALUATION_ROOT="$RUN_ROOT/evaluation"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_r1_tail_risk_q0_seed42_v1.sh"
readonly MODULE=flow_probe.r1_tail_risk
readonly ENCODER_MODULE=flow_probe.c12_crossyear_train
readonly -a VARIANTS=(ERM GROUPDRO VREX CVAR TAILRISK)

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

write_status() {
    local state=$1
    local stage=$2
    local detail=$3
    local exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    mkdir -p -- "$LAUNCHER_ROOT"
    printf '{\n' > "$partial"
    printf '  "schema_version": "r1-tail-risk-launcher-status-v1",\n' >> "$partial"
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

variant_slug() {
    case "$1" in
        ERM) printf '%s\n' erm ;;
        GROUPDRO) printf '%s\n' groupdro ;;
        VREX) printf '%s\n' vrex ;;
        CVAR) printf '%s\n' cvar ;;
        TAILRISK) printf '%s\n' tailrisk ;;
        *) return 64 ;;
    esac
}

validate_static_config() {
    uv run --no-sync python -c '
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
config = json.load(open(path, encoding="utf-8"))
paths = config.get("paths", {})
baselines = config.get("comparison_baselines", {})
valid = (
    config.get("schema_version") == "r1-tail-risk-q0-config-v1"
    and config.get("seed") == 42
    and config.get("epochs") == 4
    and config.get("steps_per_epoch") == 183
    and config.get("total_training_steps") == 732
    and config.get("maximum_concurrent_variants") == 3
    and [item.get("key") for item in config.get("variants", [])]
        == ["ERM", "GROUPDRO", "VREX", "CVAR", "TAILRISK"]
    and config.get("swanlab", {}).get("workspace") == "mortiswang"
    and config.get("swanlab", {}).get("project") == "malicious-traffic-llm"
    and config.get("swanlab", {}).get("mode") == "online"
    and baselines.get("promotion_ap_threshold") == 0.038902589823969644
    and baselines.get("dijk_2026_xgboost", {}).get("average_precision")
        == 0.03469597079642003
    and any(
        item.get("name") == "Dijk 2024 作者 8 万行示例"
        for item in baselines.get("excluded", [])
    )
    and paths.get("output_root") == sys.argv[2]
    and paths.get("launcher_root") == sys.argv[3]
    and paths.get("representation_root") == sys.argv[4]
    and paths.get("representation_manifest_schema")
        == "c12-crossyear-receiver-representations-v1"
    and config.get("screening_only") is True
    and config.get("formal_paper_evidence") is False
    and config.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$CONFIG_PATH" "$RUN_ROOT" "$LAUNCHER_ROOT" "$REPRESENTATION_ROOT"
}

validate_environment() {
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
manifest = json.load(open(root / "environment-manifest.json", encoding="utf-8"))
sampling = json.load(open(root / "training-sampling-receipt.json", encoding="utf-8"))
valid = (
    manifest.get("schema_version") == "r1-source-time-environments-q0-v1"
    and manifest.get("observability_gate") == "passed"
    and manifest.get("labels_used_for_partition") is False
    and manifest.get("environment_or_group_used_as_model_input") is False
    and manifest.get("tail_risk_variants")
        == ["ERM", "GROUPDRO", "VREX", "CVAR", "TAILRISK"]
    and sampling.get("shared_by_variants")
        == ["ERM", "GROUPDRO", "VREX", "CVAR", "TAILRISK"]
    and sampling.get("fixed_budget_steps") == 732
    and manifest.get("final_accessed") is False
)
for name, record in manifest.get("arrays", {}).items():
    path = root / name
    valid = valid and path.is_file()
    if path.is_file():
        valid = valid and hashlib.sha256(path.read_bytes()).hexdigest() == record.get("sha256")
raise SystemExit(0 if valid else 1)
' "$ENVIRONMENT_ROOT"
}

validate_target_prefix_representation() {
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
cache = pathlib.Path(sys.argv[2]) / "cache-manifest.json"
receipt = json.load(open(root / "target-prefix-representation-manifest.json", encoding="utf-8"))
path = root / "phi.npy"
valid = (
    receipt.get("schema_version") == "c12-target-prefix-representation-v1"
    and receipt.get("role") == "target-prefix"
    and receipt.get("labels_read") is False
    and receipt.get("cache_manifest_sha256") == hashlib.sha256(cache.read_bytes()).hexdigest()
    and path.is_file()
    and hashlib.sha256(path.read_bytes()).hexdigest() == receipt.get("sha256")
    and receipt.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$TARGET_PREFIX_REPRESENTATION_ROOT" "$CACHE_ROOT"
}

validate_variant() {
    local run_dir=$1
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
receipt = json.load(open(root / "training-receipt.json", encoding="utf-8"))
roles = ("source-train", "source-validation", "target-prefix", "target-development")
valid = (
    status.get("state") in {"probabilities_sealed_evaluation_pending", "finished"}
    and status.get("all_four_role_probabilities_sealed") is True
    and receipt.get("planned_epochs") == receipt.get("actual_epochs") == 4
    and receipt.get("planned_steps") == receipt.get("actual_steps") == 732
    and receipt.get("model_class") == "SharedStateScorer"
    and receipt.get("target_prefix_labels_used") is False
    and receipt.get("target_development_labels_used") is False
    and receipt.get("final_accessed") is False
    and (root / "checkpoints/final.pt").is_file()
    and (root / "states/manifest.json").is_file()
    and all((root / "predictions" / f"{role}.npz").is_file() for role in roles)
    and all((root / "predictions" / f"{role}-receipt.json").is_file() for role in roles)
)
raise SystemExit(0 if valid else 1)
' "$run_dir"
}

validate_risk() {
    local risk_dir=$1
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
receipt = json.load(open(root / "risk-model-receipt.json", encoding="utf-8"))
valid = (
    status.get("state") == "risk_scores_sealed_evaluation_pending"
    and receipt.get("state") == "risk_scores_sealed_evaluation_pending"
    and receipt.get("target_prefix_labels_read") is False
    and receipt.get("target_development_labels_read") is False
    and receipt.get("scores_sealed_before_target_label_connection") is True
    and receipt.get("final_accessed") is False
    and (root / "risk-score.npz").is_file()
    and (root / "context-bucket-receipt.json").is_file()
    and (root / "stability-diagnostic.json").is_file()
)
raise SystemExit(0 if valid else 1)
' "$risk_dir"
}

validate_evaluation() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
result = json.load(open(root / "results.json", encoding="utf-8"))
valid = (
    status.get("state") == "finished"
    and result.get("target_label_connected_after_all_probability_and_risk_seals") is True
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
    printf '{"schema_version":"r1-tail-risk-swanlab-gate-v1","workspace":"mortiswang","project":"malicious-traffic-llm","ping_exit":%s,"verify_exit":%s,"passed":%s,"checked_at":"%s","final_accessed":false}\n' \
        "$ping_exit" "$verify_exit" \
        "$([[ "$ping_exit" -eq 0 && "$verify_exit" -eq 0 ]] && printf true || printf false)" \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$LAUNCHER_ROOT/swanlab-gate.json.partial.$$"
    mv -f -- "$LAUNCHER_ROOT/swanlab-gate.json.partial.$$" "$LAUNCHER_ROOT/swanlab-gate.json"
    if [[ "$ping_exit" -ne 0 || "$verify_exit" -ne 0 ]]; then
        printf 'SwanLab 在线门禁失败：ping=%s verify=%s\n' "$ping_exit" "$verify_exit" >&2
        return 76
    fi
}

run_variant() {
    local variant=$1
    local slug
    slug=$(variant_slug "$variant")
    local run_dir="$VARIANT_ROOT/$slug"
    local lock_path="$LAUNCHER_ROOT/train-${slug}.lock"
    mkdir -p -- "$run_dir"
    exec 9> "$lock_path"
    if ! flock -n 9; then
        printf '训练锁已被占用，拒绝重复启动：%s\n' "$variant" >&2
        return 75
    fi
    if [[ -s "$run_dir/status.json" ]] && validate_variant "$run_dir"; then
        printf '变体已有合法四角色封存概率，幂等跳过：%s\n' "$variant"
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
        --target-prefix-representation-root "$TARGET_PREFIX_REPRESENTATION_ROOT" \
        --environment-root "$ENVIRONMENT_ROOT" \
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

run_risk() {
    local variant=$1
    local slug
    slug=$(variant_slug "$variant")
    local risk_dir="$RISK_ROOT/$slug"
    local lock_path="$LAUNCHER_ROOT/risk-${slug}.lock"
    exec 9> "$lock_path"
    if ! flock -n 9; then
        printf '风险拟合锁已被占用，拒绝重复启动：%s\n' "$variant" >&2
        return 75
    fi
    if [[ -s "$risk_dir/status.json" ]] && validate_risk "$risk_dir"; then
        printf '变体已有合法封存风险分数，幂等跳过：%s\n' "$variant"
        return 0
    fi
    if [[ -e "$risk_dir" ]]; then
        printf '风险目录存在但未合法完成，保留并阻断：%s\n' "$risk_dir" >&2
        return 73
    fi
    set +e
    uv run --no-sync python -m "$MODULE" fit-risk \
        --cache-root "$CACHE_ROOT" \
        --representation-root "$REPRESENTATION_ROOT" \
        --environment-root "$ENVIRONMENT_ROOT" \
        --run-dir "$VARIANT_ROOT/$slug" \
        --output-dir "$risk_dir" \
        --config "$CONFIG_PATH" 2>&1 | tee "$LAUNCHER_ROOT/fit-risk-${slug}.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$LAUNCHER_ROOT/fit-risk-${slug}-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_ROOT/fit-risk-${slug}-tee-exit-code.txt"
    if [[ "$command_code" -ne 0 ]]; then
        return "$command_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        return "$tee_code"
    fi
    validate_risk "$risk_dir"
}

run_parallel_stage() {
    local stage=$1
    local function_name=$2
    local -a pids=()
    local -a names=()
    local failed=0
    local variant
    local index
    write_status running "$stage" "max_concurrent_${MAX_CONCURRENT}" null
    for variant in "${VARIANTS[@]}"; do
        "$function_name" "$variant" &
        pids+=("$!")
        names+=("$variant")
        if [[ "${#pids[@]}" -ge "$MAX_CONCURRENT" ]]; then
            set +e
            for index in "${!pids[@]}"; do
                wait "${pids[$index]}"
                local code=$?
                printf '%s\n' "$code" > "$LAUNCHER_ROOT/${stage}-$(variant_slug "${names[$index]}")-exit-code.txt"
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
        printf '%s\n' "$code" > "$LAUNCHER_ROOT/${stage}-$(variant_slug "${names[$index]}")-exit-code.txt"
        if [[ "$code" -ne 0 ]]; then
            failed=1
        fi
    done
    set -e
    if [[ "$failed" -ne 0 ]]; then
        write_status failed "$stage" variant_failed 1
        return 1
    fi
}

preflight() {
    write_status running preflight started null
    validate_static_config
    discover_capabilities
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
    if [[ ! -s "$RECEIVER_CHECKPOINT" ]]; then
        printf '阶段 A v2 接收器检查点不存在。\n' >&2
        return 66
    fi
    if [[ ! -s "$CONFIG_PATH" || ! -s "$PROJECT_ROOT/src/flow_probe/r1_tail_risk.py" ]]; then
        printf 'R1 双层尾部风险配置或入口不存在。\n' >&2
        return 67
    fi
    if ! uv run --no-sync python -c 'import numpy, pyarrow, scipy, sklearn, swanlab, torch'; then
        printf 'R1 双层尾部风险依赖不可导入。\n' >&2
        return 69
    fi
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
cache = pathlib.Path(sys.argv[1])
representations = pathlib.Path(sys.argv[2])
cache_receipt = json.load(open(cache / "cache-manifest.json", encoding="utf-8"))
receipt = json.load(open(representations / "representation-manifest.json", encoding="utf-8"))
valid = (
    cache_receipt.get("schema_version") == "lspr-crossyear-python-cache-v1"
    and set(cache_receipt.get("roles", {}))
        == {"source-train", "source-validation", "target-prefix", "target-development"}
    and cache_receipt.get("final_accessed") is False
    and receipt.get("schema_version") == "c12-crossyear-receiver-representations-v1"
    and receipt.get("excluded_roles") == ["target-prefix"]
    and receipt.get("cache_manifest_sha256")
        == hashlib.sha256((cache / "cache-manifest.json").read_bytes()).hexdigest()
    and receipt.get("receiver_checkpoint_sha256")
        == hashlib.sha256(pathlib.Path(sys.argv[3]).read_bytes()).hexdigest()
    and receipt.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$CACHE_ROOT" "$REPRESENTATION_ROOT" "$RECEIVER_CHECKPOINT"
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
import json, pathlib, subprocess, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))
query = subprocess.check_output([
    "nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"
], text=True)
free_gib = sum(float(line.strip()) for line in query.splitlines() if line.strip()) / 1024
disk = pathlib.Path(sys.argv[2])
stat = __import__("shutil").disk_usage(disk)
disk_free_gib = stat.free / 1024**3
valid = (
    free_gib >= float(config["conservative_total_peak_gpu_memory_gib"])
    and disk_free_gib >= float(config["minimum_free_disk_gib"])
)
print(json.dumps({"gpu_free_gib": free_gib, "disk_free_gib": disk_free_gib, "passed": valid}))
raise SystemExit(0 if valid else 1)
' "$CONFIG_PATH" "$PROJECT_ROOT" > "$LAUNCHER_ROOT/resource-gate.json"
    run_swanlab_gate
}

worker_main() {
    mkdir -p -- "$LAUNCHER_ROOT" "$RUN_ROOT" "$VARIANT_ROOT" "$RISK_ROOT"
    preflight
    if [[ -s "$TARGET_PREFIX_REPRESENTATION_ROOT/target-prefix-representation-manifest.json" ]]; then
        validate_target_prefix_representation
        printf '目标前缀冻结表示已有合法收据，幂等跳过。\n'
    else
        if [[ -e "$TARGET_PREFIX_REPRESENTATION_ROOT" ]]; then
            printf '目标前缀表示目录存在但未合法完成，保留并阻断。\n' >&2
            return 73
        fi
        run_logged encode-target-prefix \
            uv run --no-sync python -m "$ENCODER_MODULE" encode-target-prefix \
            --cache-root "$CACHE_ROOT" \
            --receiver-checkpoint "$RECEIVER_CHECKPOINT" \
            --output-dir "$TARGET_PREFIX_REPRESENTATION_ROOT" \
            --batch-size 16
        validate_target_prefix_representation
    fi
    if [[ -s "$ENVIRONMENT_ROOT/environment-manifest.json" ]]; then
        validate_environment
        printf '环境侧车已有合法收据，幂等跳过。\n'
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
    run_parallel_stage parallel-training run_variant
    local variant
    for variant in "${VARIANTS[@]}"; do
        validate_variant "$VARIANT_ROOT/$(variant_slug "$variant")"
    done
    run_parallel_stage parallel-risk-fitting run_risk
    for variant in "${VARIANTS[@]}"; do
        validate_risk "$RISK_ROOT/$(variant_slug "$variant")"
    done
    if [[ -s "$EVALUATION_ROOT/status.json" ]] && validate_evaluation; then
        printf '独立评价已有合法完成状态，幂等跳过。\n'
    else
        if [[ -e "$EVALUATION_ROOT" ]]; then
            printf '评价目录存在但未合法完成，保留并阻断。\n' >&2
            return 73
        fi
        run_logged evaluate \
            uv run --no-sync python -m "$MODULE" evaluate \
            --cache-root "$CACHE_ROOT" \
            --representation-root "$REPRESENTATION_ROOT" \
            --environment-root "$ENVIRONMENT_ROOT" \
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
    printf 'R1 双层尾部风险 Q0 已完成，不重复启动：%s\n' "$RUN_ID"
    exit 0
fi
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_ROOT/command.txt"
sha256sum \
    "$CACHE_ROOT/cache-manifest.json" \
    "$REPRESENTATION_ROOT/representation-manifest.json" \
    "$RECEIVER_CHECKPOINT" \
    "$CONFIG_PATH" \
    "$PROJECT_ROOT/src/flow_probe/r1_tail_risk.py" \
    "$PROJECT_ROOT/src/flow_probe/r1_source_environment.py" \
    "$PROJECT_ROOT/src/flow_probe/c12_crossyear_models.py" \
    "$PROJECT_ROOT/src/flow_probe/c12_crossyear_train.py" \
    "$SCRIPT_PATH" > "$LAUNCHER_ROOT/input-sha256.txt"
write_status prepared launch static_contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'R1_TAIL_RISK_Q0_STARTED session=%s launcher=%s output=%s max_concurrent=%s final_accessed=false formal_paper_evidence=false\n' \
    "$SCREEN_NAME" "$LAUNCHER_ROOT" "$RUN_ROOT" "$MAX_CONCURRENT"
