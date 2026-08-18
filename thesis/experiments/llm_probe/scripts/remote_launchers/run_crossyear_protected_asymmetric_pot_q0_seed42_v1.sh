#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly CONFIG="$PROJECT_ROOT/configs/crossyear-protected-asymmetric-pot-q0-seed42-v1.json"
readonly MODULE=flow_probe.crossyear_protected_partial_ot
readonly RUN_ID=crossyear-rare-mass-protected-asymmetric-pot-q0-seed42-v1-rerun2
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_crossyear_protected_asymmetric_pot_q0_seed42_v1.sh"
readonly MODULE_PATH="$PROJECT_ROOT/src/flow_probe/crossyear_protected_partial_ot.py"
readonly CACHE_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"
readonly CPU_BASELINE_ROOT="$PROJECT_ROOT/runs/baselines/lspr-crossyear-tabular-q0-seed42-v2/xgboost"
readonly SESSION_NAME=crossyear-protected-pot-q0-s42-v1-rerun2
readonly HEARTBEAT_SECONDS=60

cd "$PROJECT_ROOT"
source tools/env/activate.sh

write_status() {
    local state=$1
    local stage=$2
    local detail=$3
    local exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    mkdir -p -- "$LAUNCHER_ROOT"
    printf '{\n' > "$partial"
    printf '  "schema_version": "crossyear-protected-pot-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "screening_only": true,\n' >> "$partial"
    printf '  "formal_paper_evidence": false,\n' >> "$partial"
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

run_logged() {
    local name=$1
    shift
    mkdir -p -- "$LAUNCHER_ROOT"
    set +e
    "$@" 2>&1 | tee "$LAUNCHER_ROOT/${name}.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$LAUNCHER_ROOT/${name}-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_ROOT/${name}-tee-exit-code.txt"
    if [[ "$command_code" -ne 0 ]]; then
        return "$command_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        return "$tee_code"
    fi
    if [[ ! -s "$LAUNCHER_ROOT/${name}.log" ]]; then
        printf '阶段日志为空：%s\n' "$name" >&2
        return 74
    fi
}

heartbeat() {
    local worker_pid=$1
    local started=$SECONDS
    while kill -0 "$worker_pid" 2>/dev/null; do
        sleep "$HEARTBEAT_SECONDS"
        if kill -0 "$worker_pid" 2>/dev/null; then
            local elapsed=$((SECONDS - started))
            local gpu_summary
            gpu_summary=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | head -n 1 || printf '不可用')
            printf 'P0 心跳：阶段=完整流水线 累计=%s秒 GPU=%s 输出=%s\n' \
                "$elapsed" "$gpu_summary" "$OUTPUT_ROOT" | tee -a "$LAUNCHER_ROOT/heartbeat.log"
        fi
    done
}

discover_capabilities() {
    local fd_cmd
    if command -v fd >/dev/null 2>&1; then
        fd_cmd=$(command -v fd)
    elif command -v fdfind >/dev/null 2>&1; then
        fd_cmd=$(command -v fdfind)
    else
        fd_cmd=unavailable
    fi
    local rg_cmd
    local uv_cmd
    rg_cmd=$(command -v rg || true)
    uv_cmd=$(command -v uv || true)
    printf '{"schema_version":"crossyear-protected-pot-capabilities-v1","fd":"%s","rg":"%s","uv":"%s","final_accessed":false}\n' \
        "$fd_cmd" "$rg_cmd" "$uv_cmd" > "$LAUNCHER_ROOT/capabilities.json"
    if [[ "$fd_cmd" == unavailable || -z "$rg_cmd" || -z "$uv_cmd" ]]; then
        printf '远端 fd/fdfind、rg 或 uv 不可用。\n' >&2
        return 69
    fi
}

validate_config() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))
paths = config["paths"]
variants = config["variants"]
valid = (
    config.get("schema_version") == "crossyear-protected-asymmetric-pot-q0-config-v1"
    and config.get("run_id") == "crossyear-rare-mass-protected-asymmetric-pot-q0-seed42-v1-rerun2"
    and config.get("target_prefix_labels_available") is False
    and config.get("target_labels_used_for_tuning") is False
    and config.get("target_labels_opened_after_all_probability_seals") is True
    and config.get("final_accessed") is False
    and config["xgboost"].get("tree_method") == "hist"
    and config["xgboost"].get("device") == "cuda"
    and config["swanlab"].get("workspace") == "mortiswang"
    and config["swanlab"].get("project") == "malicious-traffic-llm"
    and paths.get("project_root") == sys.argv[2]
    and paths.get("output_root") == sys.argv[3]
    and [item["key"] for item in variants] == [
        "B0_XGB_ANCHOR", "U1_FULL_OT", "U2_ASYM_POT_NO_FLOOR",
        "M1_PROTECTED_ASYM_POT", "M1_M2_SAFE_ROLLBACK"
    ]
)
raise SystemExit(0 if valid else 1)
' "$CONFIG" "$PROJECT_ROOT" "$OUTPUT_ROOT"
}

validate_shared_inputs() {
    if [[ ! -s "$CACHE_ROOT/cache-manifest.json" || ! -s "$CPU_BASELINE_ROOT/run_state.json" \
        || ! -s "$CPU_BASELINE_ROOT/probability_seal.json" || ! -s "$CPU_BASELINE_ROOT/metrics.json" ]]; then
        printf '只读缓存或共享 CPU XGBoost v2 收据不完整。\n' >&2
        return 66
    fi
    uv run --no-sync python -c '
import json, pathlib, sys
cache = json.load(open(pathlib.Path(sys.argv[1]) / "cache-manifest.json", encoding="utf-8"))
baseline = pathlib.Path(sys.argv[2])
status = json.load(open(baseline / "run_state.json", encoding="utf-8"))
seal = json.load(open(baseline / "probability_seal.json", encoding="utf-8"))
metrics = json.load(open(baseline / "metrics.json", encoding="utf-8"))
valid = (
    cache.get("schema_version") == "lspr-crossyear-python-cache-v1"
    and cache.get("final_accessed") is False
    and set(cache.get("arrays", {})) == {"source-train", "source-validation", "target-prefix", "target-development"}
    and "labels" not in cache["arrays"]["target-prefix"]
    and status.get("state") == "finished"
    and status.get("model") == "xgboost"
    and status.get("final_accessed") is False
    and seal.get("row_count") == cache["arrays"]["target-development"]["sample_id"]["shape"][0]
    and metrics.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$CACHE_ROOT" "$CPU_BASELINE_ROOT"
}

validate_resources() {
    if ! command -v nvidia-smi >/dev/null 2>&1 || ! command -v flock >/dev/null 2>&1; then
        printf '远端 nvidia-smi 或 flock 不可用。\n' >&2
        return 69
    fi
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader \
        > "$LAUNCHER_ROOT/gpu-preflight.txt"
    df -Pk "$PROJECT_ROOT" > "$LAUNCHER_ROOT/disk-preflight.txt"
    uv run --no-sync python -c '
import json, pathlib, shutil, subprocess, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))
resources = config["resources"]
query = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], text=True)
gpu_free = sum(float(line.strip()) for line in query.splitlines() if line.strip()) / 1024
usage = shutil.disk_usage(pathlib.Path(sys.argv[2]))
disk_free = usage.free / 1024**3
disk_fraction = usage.used / usage.total
receipt = {
    "gpu_free_gib": gpu_free,
    "disk_free_gib": disk_free,
    "disk_usage_fraction": disk_fraction,
    "passed": gpu_free >= resources["minimum_free_gpu_memory_gib"]
        and disk_free >= resources["minimum_free_disk_gib"]
        and disk_fraction < resources["maximum_disk_usage_fraction"],
    "final_accessed": False,
}
print(json.dumps(receipt, sort_keys=True))
raise SystemExit(0 if receipt["passed"] else 1)
' "$CONFIG" "$PROJECT_ROOT" > "$LAUNCHER_ROOT/resource-gate.json"
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
    printf '{"schema_version":"crossyear-protected-pot-swanlab-gate-v1","workspace":"mortiswang","project":"malicious-traffic-llm","ping_exit":%s,"verify_exit":%s,"passed":%s,"final_accessed":false}\n' \
        "$ping_exit" "$verify_exit" \
        "$([[ "$ping_exit" -eq 0 && "$verify_exit" -eq 0 ]] && printf true || printf false)" \
        > "$LAUNCHER_ROOT/swanlab-gate.json"
    if [[ "$ping_exit" -ne 0 || "$verify_exit" -ne 0 ]]; then
        printf 'SwanLab 在线门禁失败：ping=%s verify=%s\n' "$ping_exit" "$verify_exit" >&2
        return 76
    fi
}

preflight() {
    mkdir -p -- "$LAUNCHER_ROOT"
    write_status running preflight started null
    discover_capabilities
    validate_config
    validate_shared_inputs
    validate_resources
    if ! uv run --no-sync python -c 'import joblib, numpy, scipy, sklearn, swanlab, xgboost'; then
        printf 'P0 锁定依赖不可导入。\n' >&2
        return 69
    fi
    run_swanlab_gate
    run_logged audit uv run --no-sync python -m "$MODULE" audit --config "$CONFIG" --cache-root "$CACHE_ROOT"
}

validate_finished() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
decision = json.load(open(root / "decision.json", encoding="utf-8"))
valid = (
    status.get("state") == "finished"
    and status.get("exit_code") == 0
    and status.get("final_accessed") is False
    and decision.get("target_labels_used_for_tuning") is False
    and decision.get("target_labels_opened_after_all_probability_seals") is True
    and decision.get("screening_only") is True
    and decision.get("formal_paper_evidence") is False
    and decision.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$OUTPUT_ROOT"
}

worker_main() {
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    if ! flock -n 9; then
        printf 'P0 工作锁已被占用，拒绝重复启动。\n' >&2
        return 75
    fi
    preflight
    if [[ -e "$OUTPUT_ROOT" ]]; then
        if [[ -s "$OUTPUT_ROOT/status.json" ]] && validate_finished; then
            printf 'P0 已合法完成，幂等跳过：%s\n' "$OUTPUT_ROOT"
            write_status finished complete idempotent_skip 0
            return 0
        fi
        printf 'P0 运行根已存在但未合法完成，保留并阻断：%s\n' "$OUTPUT_ROOT" >&2
        return 73
    fi
    write_status running q0-pipeline started null
    mkdir -p -- "$(dirname "$OUTPUT_ROOT")"
    set +e
    uv run --no-sync python -m "$MODULE" run --config "$CONFIG" 2>&1 | tee "$LAUNCHER_ROOT/pipeline.log" &
    local pipeline_pid=$!
    heartbeat "$pipeline_pid" &
    local heartbeat_pid=$!
    wait "$pipeline_pid"
    local pipeline_code=$?
    wait "$heartbeat_pid" || true
    set -e
    printf '%s\n' "$pipeline_code" > "$LAUNCHER_ROOT/pipeline-exit-code.txt"
    if [[ "$pipeline_code" -ne 0 ]]; then
        return "$pipeline_code"
    fi
    if [[ ! -s "$LAUNCHER_ROOT/pipeline.log" ]]; then
        printf 'P0 主流水线日志为空。\n' >&2
        return 74
    fi
    validate_finished
    local variant
    for variant in B0_XGB_ANCHOR U1_FULL_OT U2_ASYM_POT_NO_FLOOR M1_PROTECTED_ASYM_POT M1_M2_SAFE_ROLLBACK; do
        run_logged "swanlab-${variant,,}" uv run --no-sync python -m "$MODULE" swanlab-publish \
            --config "$CONFIG" --output-root "$OUTPUT_ROOT" --variant "$variant"
    done
    validate_finished
    sha256sum "$OUTPUT_ROOT/status.json" "$OUTPUT_ROOT/decision.json" \
        "$OUTPUT_ROOT/resource-usage.json" > "$LAUNCHER_ROOT/result-sha256.txt"
    write_status finished complete evaluation_and_upload_finished 0
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

mkdir -p -- "$LAUNCHER_ROOT"
validate_config
discover_capabilities
if ! command -v screen >/dev/null 2>&1; then
    printf '远端缺少 screen。\n' >&2
    exit 69
fi
if screen -ls 2>/dev/null | rg -q "[.]${SESSION_NAME}[[:space:]]"; then
    printf '同名 P0 screen 已在运行：%s\n' "$SESSION_NAME"
    exit 0
fi
if [[ -s "$STATUS_PATH" ]] && uv run --no-sync python -c \
    'import json,sys; value=json.load(open(sys.argv[1], encoding="utf-8")); raise SystemExit(0 if value.get("state") == "finished" and value.get("final_accessed") is False else 1)' \
    "$STATUS_PATH"; then
    printf 'P0 已完成，不重复启动：%s\n' "$RUN_ID"
    exit 0
fi
if [[ -e "$OUTPUT_ROOT" ]]; then
    printf 'P0 运行根已存在，启动前拒绝覆盖：%s\n' "$OUTPUT_ROOT" >&2
    exit 73
fi
printf '%s\n' "$SESSION_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$CACHE_ROOT/cache-manifest.json" "$CPU_BASELINE_ROOT/run_state.json" \
    "$CPU_BASELINE_ROOT/probability_seal.json" "$CONFIG" "$MODULE_PATH" "$SCRIPT_PATH" \
    > "$LAUNCHER_ROOT/input-sha256.txt"
write_status prepared launch static_contract_passed null
screen -dmS "$SESSION_NAME" bash "$SCRIPT_PATH" --worker
printf 'CROSSYEAR_PROTECTED_POT_Q0_STARTED session=%s launcher=%s output=%s final_accessed=false formal_paper_evidence=false\n' \
    "$SESSION_NAME" "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
