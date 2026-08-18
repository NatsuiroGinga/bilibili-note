#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly CONFIG="$PROJECT_ROOT/configs/tqhc2-strict-crossmember-q0-seed42-v1.json"
readonly MODULE=flow_probe.tqhc2_strict_crossmember_q0
readonly RUN_ID=tqhc2-strict-crossmember-low-fpr-residual-admission-q0-seed42-v1
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_tqhc2_strict_crossmember_q0_seed42_v1.sh"
readonly SESSION_NAME=tqhc2-strict-crossmember-q0-s42-v1
readonly WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=malicious-traffic-llm
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
    printf '  "schema_version": "tqhc2-strict-crossmember-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "screening_only": true,\n' >> "$partial"
    printf '  "formal_paper_evidence": false,\n' >> "$partial"
    printf '  "formal_final_role_created": false,\n' >> "$partial"
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
    printf '{"schema_version":"tqhc2-strict-crossmember-capabilities-v1","fd":"%s","rg":"%s","uv":"%s","final_accessed":false}\n' \
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
valid = (
    config.get("schema_version") == "tqhc2-strict-crossmember-q0-config-v1"
    and config.get("run_id") == sys.argv[2]
    and config.get("seed") == 42
    and len(config.get("identities", [])) == 17
    and config.get("evidence") == {
        "screening_only": True,
        "formal_paper_evidence": False,
        "formal_final_role_created": False,
        "final_accessed": False,
    }
    and config["resources"].get("maximum_identity_concurrency") == 1
    and config["swanlab"].get("workspace") == sys.argv[5]
    and config["swanlab"].get("project") == sys.argv[6]
    and paths.get("project_root") == sys.argv[3]
    and paths.get("output_root") == sys.argv[4]
)
raise SystemExit(0 if valid else 1)
' "$CONFIG" "$RUN_ID" "$PROJECT_ROOT" "$OUTPUT_ROOT" "$WORKSPACE" "$SWANLAB_PROJECT"
}

validate_environment() {
    if ! command -v flock >/dev/null 2>&1 || ! command -v screen >/dev/null 2>&1; then
        printf '远端 flock 或 screen 不可用。\n' >&2
        return 69
    fi
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        printf '冻结神经身份要求 GPU，但 nvidia-smi 不可用。\n' >&2
        return 69
    fi
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv,noheader \
        > "$LAUNCHER_ROOT/gpu-preflight.txt"
    df -Pk "$PROJECT_ROOT" > "$LAUNCHER_ROOT/disk-preflight.txt"
    uv run --no-sync python -c \
        'import joblib, numpy, pandas, pyarrow, sklearn, swanlab, torch, xgboost'
    uv run --no-sync python -m "$MODULE" --help > "$LAUNCHER_ROOT/cli-help.txt"
}

validate_swanlab_destination() {
    local ping_exit
    local verify_exit
    set +e
    uv run --no-sync swanlab ping > "$LAUNCHER_ROOT/swanlab-ping.log" 2>&1
    ping_exit=$?
    uv run --no-sync swanlab verify > "$LAUNCHER_ROOT/swanlab-verify.log" 2>&1
    verify_exit=$?
    set -e
    printf '{"schema_version":"tqhc2-strict-crossmember-swanlab-gate-v1","workspace":"%s","project":"%s","ping_exit":%s,"verify_exit":%s,"passed":%s,"final_accessed":false}\n' \
        "$WORKSPACE" "$SWANLAB_PROJECT" "$ping_exit" "$verify_exit" \
        "$([[ "$ping_exit" -eq 0 && "$verify_exit" -eq 0 ]] && printf true || printf false)" \
        > "$LAUNCHER_ROOT/swanlab-gate.json"
    if [[ "$ping_exit" -ne 0 || "$verify_exit" -ne 0 ]]; then
        printf 'SwanLab 在线与授权门禁失败。\n' >&2
        return 76
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
            gpu_summary=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total \
                --format=csv,noheader,nounits 2>/dev/null | head -n 1 || printf '不可用')
            printf 'TQH-C2 Q0心跳：阶段=严格跨成员流水线 累计=%s秒 GPU=%s 输出=%s\n' \
                "$elapsed" "$gpu_summary" "$OUTPUT_ROOT" | tee -a "$LAUNCHER_ROOT/heartbeat.log"
        fi
    done
}

validate_finished() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
target = json.load(open(root / "target_development_aggregate.json", encoding="utf-8"))
decision = json.load(open(root / "decision.json", encoding="utf-8"))
audit = json.load(open(root / "artifact_audit_receipt.json", encoding="utf-8"))
valid = (
    status.get("state") == "evaluated"
    and status.get("C_read_count") == 1
    and target.get("C_read_count") == 1
    and target.get("capture_count") == 12
    and audit.get("passed") is True
    and decision.get("screening_only") is True
    and decision.get("formal_paper_evidence") is False
    and decision.get("formal_final_role_created") is False
    and decision.get("final_accessed") is False
)
raise SystemExit(0 if valid else 1)
' "$OUTPUT_ROOT"
}

worker_main() {
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    if ! flock -n 9; then
        printf '同名 Q0 工作锁已被占用，拒绝重复启动。\n' >&2
        return 75
    fi
    write_status running preflight started null
    discover_capabilities
    validate_config
    validate_environment
    validate_swanlab_destination
    if [[ -e "$OUTPUT_ROOT" ]]; then
        printf '同名运行根已存在，拒绝覆盖或自动重试：%s\n' "$OUTPUT_ROOT" >&2
        return 73
    fi
    write_status running pipeline started null
    set +e
    uv run --no-sync python -m "$MODULE" run --config "$CONFIG" \
        2>&1 | tee "$LAUNCHER_ROOT/pipeline.log" &
    local pipeline_pid=$!
    heartbeat "$pipeline_pid" &
    local heartbeat_pid=$!
    wait "$pipeline_pid"
    local pipeline_code=$?
    wait "$heartbeat_pid" || true
    set -e
    printf '%s\n' "$pipeline_code" > "$LAUNCHER_ROOT/pipeline-command-exit-code.txt"
    if [[ "$pipeline_code" -ne 0 || ! -s "$LAUNCHER_ROOT/pipeline.log" ]]; then
        return "$([[ "$pipeline_code" -ne 0 ]] && printf '%s' "$pipeline_code" || printf '74')"
    fi
    validate_finished
    run_logged swanlab-publish uv run --no-sync python -m "$MODULE" swanlab-publish \
        --config "$CONFIG" --authorized-workspace "$WORKSPACE" \
        --authorized-project "$SWANLAB_PROJECT"
    validate_finished
    sha256sum "$OUTPUT_ROOT/training_freeze_receipt.json" \
        "$OUTPUT_ROOT/target_development_aggregate.json" "$OUTPUT_ROOT/decision.json" \
        "$OUTPUT_ROOT/artifact_audit_receipt.json" > "$LAUNCHER_ROOT/result-sha256.txt"
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
if screen -ls 2>/dev/null | rg -q "[.]${SESSION_NAME}[[:space:]]"; then
    printf '同名 Q0 screen 已在运行：%s\n' "$SESSION_NAME" >&2
    exit 75
fi
if pgrep -af "python.*-m ${MODULE}" > "$LAUNCHER_ROOT/module-process-check.txt"; then
    printf '同名 Q0 模块已有进程，拒绝重复启动。\n' >&2
    exit 75
fi
if [[ -e "$OUTPUT_ROOT" ]]; then
    printf '同名 Q0 运行根已存在，拒绝覆盖：%s\n' "$OUTPUT_ROOT" >&2
    exit 73
fi
printf '%s\n' "$SESSION_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "bash $SCRIPT_PATH --worker" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$CONFIG" "$PROJECT_ROOT/src/flow_probe/tqhc2_strict_crossmember_data.py" \
    "$PROJECT_ROOT/src/flow_probe/tqhc2_strict_crossmember_models.py" \
    "$PROJECT_ROOT/src/flow_probe/tqhc2_strict_crossmember_q0.py" "$SCRIPT_PATH" \
    > "$LAUNCHER_ROOT/input-sha256.txt"
write_status prepared launch static_contract_passed null
screen -dmS "$SESSION_NAME" bash "$SCRIPT_PATH" --worker
printf 'TQHC2_STRICT_CROSSMEMBER_Q0_STARTED session=%s launcher=%s output=%s screening_only=true formal_paper_evidence=false\n' \
    "$SESSION_NAME" "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
