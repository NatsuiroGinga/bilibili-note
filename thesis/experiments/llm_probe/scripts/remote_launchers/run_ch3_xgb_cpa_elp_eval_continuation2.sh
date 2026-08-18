#!/usr/bin/env bash
source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly PARENT_RUN_ID=ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1
readonly RUN_ID="${PARENT_RUN_ID}-eval-continuation2"
readonly SCREEN_NAME=ch3-xgb-target-eval-cont2
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_xgb_cpa_elp_eval_continuation.py"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_xgb_cpa_elp_eval_continuation2.sh"
readonly PARENT_RUN_ROOT="$PROJECT_ROOT/runs/diagnostics/$PARENT_RUN_ID"
readonly RUN_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCH_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$RUN_ROOT/status.json"

write_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    local partial="$STATUS_PATH.partial"
    printf '{"run_id":"%s","parent_run_id":"%s","state":"%s","stage":"%s","detail":"%s","exit_code":%s,"screen":"%s"}\n' \
        "$RUN_ID" "$PARENT_RUN_ID" "$state" "$stage" "$detail" "$exit_code" "$SCREEN_NAME" > "$partial"
    mv "$partial" "$STATUS_PATH"
}

resource_gate() {
    local memory_max memory_current available_gib disk_available_mib gpu_free_mib
    memory_max=$(< /sys/fs/cgroup/memory.max)
    memory_current=$(< /sys/fs/cgroup/memory.current)
    if [[ -z "$memory_max" || "$memory_max" == max ]]; then
        write_status failed resource_gate cgroup_limit_unavailable 12
        return 12
    fi
    available_gib=$(awk -v m="$memory_max" -v c="$memory_current" 'BEGIN {printf "%.2f", (m-c)/1073741824}')
    if ! awk -v a="$available_gib" 'BEGIN {exit !(a >= 52.0)}'; then
        write_status failed resource_gate host_memory_insufficient 10
        return 10
    fi
    disk_available_mib=$(df -Pk "$PROJECT_ROOT" | awk 'NR==2 {printf "%d", $4/1024}')
    if [[ "$disk_available_mib" -lt 30720 ]]; then
        write_status failed resource_gate disk_insufficient 13
        return 13
    fi
    gpu_free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR==1 {print $1}')
    if [[ "$gpu_free_mib" -lt 11264 ]]; then
        write_status failed resource_gate gpu_memory_insufficient 14
        return 14
    fi
    printf '资源门通过：cgroup可用=%sGiB 磁盘可用=%sMiB GPU可用=%sMiB\n' \
        "$available_gib" "$disk_available_mib" "$gpu_free_mib"
}

tracking_gate() {
    local gate_root="$RUN_ROOT/tracking-gates/attempt-1"
    mkdir -p "$gate_root"
    set +e
    uv run --no-sync swanlab ping > "$gate_root/swanlab-ping.log" 2>&1
    local ping_code=$?
    uv run --no-sync swanlab verify > "$gate_root/swanlab-verify.log" 2>&1
    local verify_code=$?
    set -e
    printf '%s\n' "$ping_code" > "$gate_root/swanlab-ping.exit-code.txt"
    printf '%s\n' "$verify_code" > "$gate_root/swanlab-verify.exit-code.txt"
    if [[ "$ping_code" -ne 0 || "$verify_code" -ne 0 ]]; then
        write_status failed tracking_gate swanlab_preinit_failed 15
        return 15
    fi
}

worker() {
    cd "$PROJECT_ROOT"
    exec 9> "$LAUNCH_ROOT/run.lock"
    flock -n 9 || return 75
    source tools/env/activate.sh
    write_status running resource_gate checking_live_resources null
    nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader > "$RUN_ROOT/gpu-processes-at-launch.txt" || true
    resource_gate
    tracking_gate
    uv run --no-sync python "$TOOL_PATH" \
        --parent-run-root "$PARENT_RUN_ROOT" --parent-config "$CONFIG_PATH" \
        --out "$RUN_ROOT" --validate-inputs
    write_status running target_rebuild started null
    set +e
    uv run --no-sync python "$TOOL_PATH" \
        --parent-run-root "$PARENT_RUN_ROOT" --parent-config "$CONFIG_PATH" \
        --out "$RUN_ROOT" 2>&1 | tee "$RUN_ROOT/run.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local python_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$python_code" > "$RUN_ROOT/python-exit-code.txt"
    printf '%s\n' "$tee_code" > "$RUN_ROOT/tee-exit-code.txt"
    if [[ "$python_code" -ne 0 ]]; then
        write_status failed evaluation python_failed "$python_code"
        return "$python_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        write_status failed evaluation tee_failed "$tee_code"
        return "$tee_code"
    fi
    [[ -s "$RUN_ROOT/xgb_cpa_elp_results.json" && -s "$RUN_ROOT/manifest.json" ]] || {
        write_status failed postcondition required_artifacts_missing 16
        return 16
    }
    write_status finished complete success 0
}

if [[ ${1:-} == --worker ]]; then
    worker
    exit $?
fi
if [[ $# -ne 0 ]]; then
    printf '启动器不接受参数。\n' >&2
    exit 64
fi

cd "$PROJECT_ROOT"
source tools/env/activate.sh
for command in uv swanlab screen flock nvidia-smi sha256sum rg; do
    command -v "$command" >/dev/null 2>&1 || {
        printf '缺少命令：%s\n' "$command" >&2
        exit 69
    }
done
for path in "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH"; do
    [[ -s "$path" ]] || {
        printf '生产文件缺失：%s\n' "$path" >&2
        exit 67
    }
done
for name in selection_frozen_xgb2x2.json effective_config_receipts.json model_raw83.json model_semantic168.json; do
    [[ -r "$PARENT_RUN_ROOT/$name" && -s "$PARENT_RUN_ROOT/$name" ]] || {
        printf '父运行制品缺失或不可读：%s\n' "$PARENT_RUN_ROOT/$name" >&2
        exit 66
    }
done
for cache_name in X24 y24 I24 M24 s24 d24 t24; do
    cache_path="$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/${cache_name}.npy"
    [[ -r "$cache_path" && -s "$cache_path" ]] || {
        printf '缓存缺失或不可读：%s\n' "$cache_path" >&2
        exit 66
    }
done
[[ -r "$PROJECT_ROOT/runs/diagnostics/ch3-baselines-full/scores_xgboost_dijk2026.npy" ]] || {
    printf '回归锚点分数缺失。\n' >&2
    exit 66
}
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名接续评价已经启动。\n'
    exit 0
fi
if pgrep -f 'python.*[c]h3_xgb_cpa_elp_eval_continuation.py' >/dev/null; then
    printf '同名接续评价进程已经运行。\n' >&2
    exit 75
fi
if [[ -e "$RUN_ROOT" || -e "$LAUNCH_ROOT" ]]; then
    printf '同名运行目录已存在，禁止覆盖：%s\n' "$RUN_ROOT" >&2
    exit 73
fi
mkdir -p "$RUN_ROOT" "$LAUNCH_ROOT"
uv run --no-sync python "$TOOL_PATH" \
    --parent-run-root "$PARENT_RUN_ROOT" --parent-config "$CONFIG_PATH" \
    --out "$RUN_ROOT" --validate-inputs
sha256sum "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" \
    "$PARENT_RUN_ROOT/selection_frozen_xgb2x2.json" \
    "$PARENT_RUN_ROOT/effective_config_receipts.json" \
    "$PARENT_RUN_ROOT/model_raw83.json" \
    "$PARENT_RUN_ROOT/model_semantic168.json" > "$LAUNCH_ROOT/input-sha256.txt"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCH_ROOT/screen-session.txt"
write_status prepared launch queued null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'XGBOOST_CPA_ELP_EVAL_CONTINUATION_STARTED session=%s run=%s parent=%s\n' \
    "$SCREEN_NAME" "$RUN_ROOT" "$PARENT_RUN_ROOT"
