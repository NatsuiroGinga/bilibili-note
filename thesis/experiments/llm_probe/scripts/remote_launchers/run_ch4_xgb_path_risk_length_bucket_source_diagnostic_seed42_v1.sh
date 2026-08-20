#!/usr/bin/env bash
source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch4-xgb-path-risk-length-bucket-lspr23-diagnostic-seed42-v1
readonly SCREEN_NAME=ch4-xgb-path-risk-length-bucket-s42-v1
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch4_xgb_path_risk_length_bucket_source_diagnostic.py"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch4-xgb-path-risk-length-bucket-source-diagnostic-seed42-v1.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch4_xgb_path_risk_length_bucket_source_diagnostic_seed42_v1.sh"
readonly PARENT_MODEL_ROOT="$PROJECT_ROOT/runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
readonly PARENT_M1_SUMMARY="$PROJECT_ROOT/runs/diagnostics/ch4-xgb-entity-path-max-tong-same-model-q0-seed42-v1/summary.json"
readonly PARENT_M1_SUMMARY_SHA256=2e4bbfe044b9ce9407090af765220fc7bc5829188cadcdfb33284002f633d462
readonly RUN_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCH_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$RUN_ROOT/status.json"

write_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    local partial="$STATUS_PATH.partial"
    printf '{"run_id":"%s","state":"%s","stage":"%s","detail":"%s","exit_code":%s,"screen":"%s"}\n' \
        "$RUN_ID" "$state" "$stage" "$detail" "$exit_code" "$SCREEN_NAME" > "$partial"
    mv "$partial" "$STATUS_PATH"
}

resource_gate() {
    local memory_max memory_current available_gib disk_available_mib
    memory_max=$(cat /sys/fs/cgroup/memory.max)
    memory_current=$(cat /sys/fs/cgroup/memory.current)
    if [[ -z "$memory_max" || "$memory_max" == max ]]; then
        write_status failed resource_gate cgroup_limit_unavailable 12
        return 12
    fi
    available_gib=$(awk -v m="$memory_max" -v c="$memory_current" 'BEGIN {printf "%.2f", (m-c)/1073741824}')
    if ! awk -v a="$available_gib" 'BEGIN {exit !(a >= 17.0)}'; then
        write_status failed resource_gate host_memory_insufficient 10
        return 10
    fi
    disk_available_mib=$(df -Pk "$PROJECT_ROOT" | awk 'NR==2 {printf "%d", $4/1024}')
    if [[ "$disk_available_mib" -lt 30720 ]]; then
        write_status failed resource_gate disk_insufficient 13
        return 13
    fi
    printf '资源门通过：cgroup可用=%sGiB 磁盘可用=%sMiB 推理设备=CPU GPU显存需求=0MiB\n' \
        "$available_gib" "$disk_available_mib"
}

worker() {
    cd "$PROJECT_ROOT"
    exec 9>"$LAUNCH_ROOT/run.lock"
    flock -n 9 || return 75
    source tools/env/activate.sh
    write_status running resource_gate checking_live_resources null
    resource_gate
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config || {
        local code=$?
        write_status failed preflight config_invalid "$code"
        return "$code"
    }
    write_status running source_diagnostic started null
    set +e
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" 2>&1 | tee "$RUN_ROOT/run.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local python_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$python_code" > "$RUN_ROOT/python-exit-code.txt"
    printf '%s\n' "$tee_code" > "$RUN_ROOT/tee-exit-code.txt"
    if [[ "$python_code" -eq 78 ]]; then
        write_status failed input_contract INVALID_INPUT_CONTRACT "$python_code"
        return "$python_code"
    fi
    if [[ "$python_code" -ne 0 ]]; then
        write_status failed source_diagnostic python_failed "$python_code"
        return "$python_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        write_status failed source_diagnostic tee_failed "$tee_code"
        return "$tee_code"
    fi
    for artifact in aggregate-results.json input-receipt.json resource-summary.json manifest.json run.log; do
        if [[ ! -s "$RUN_ROOT/$artifact" ]]; then
            write_status failed postflight required_artifact_missing 15
            return 15
        fi
    done
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
for command in uv screen flock sha256sum rg; do
    command -v "$command" >/dev/null 2>&1 || { printf '缺少命令：%s\n' "$command" >&2; exit 69; }
done
for path in "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" "$PARENT_M1_SUMMARY"; do
    [[ -s "$path" ]] || { printf '生产输入缺失：%s\n' "$path" >&2; exit 67; }
done
printf '%s  %s\n' "$PARENT_M1_SUMMARY_SHA256" "$PARENT_M1_SUMMARY" | sha256sum -c -
for model_name in model_oof_semantic168_fold0.json model_oof_semantic168_fold1.json model_oof_semantic168_fold2.json; do
    [[ -s "$PARENT_MODEL_ROOT/$model_name" ]] || { printf '父折模型缺失：%s\n' "$model_name" >&2; exit 66; }
done
for cache_name in X23 y23 I23 M23 E23 ent23 t23_flow; do
    [[ "$cache_name" != *24* ]] || { printf '源年白名单出现目标年数组。\n' >&2; exit 65; }
    cache_path="$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache/${cache_name}.npy"
    [[ -r "$cache_path" && -s "$cache_path" ]] || { printf '缓存缺失或不可读：%s\n' "$cache_path" >&2; exit 66; }
done
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名诊断已经启动。\n'
    exit 0
fi
if pgrep -f 'python.*[c]h4_xgb_path_risk_length_bucket_source_diagnostic.py' >/dev/null; then
    printf '同名诊断进程已经运行。\n' >&2
    exit 75
fi
if [[ -e "$RUN_ROOT" || -e "$LAUNCH_ROOT" ]]; then
    printf '同名运行目录已存在，禁止覆盖：%s\n' "$RUN_ROOT" >&2
    exit 73
fi
mkdir -p "$RUN_ROOT" "$LAUNCH_ROOT"
uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
sha256sum "$TOOL_PATH" "$CONFIG_PATH" "$SCRIPT_PATH" "$PARENT_M1_SUMMARY" > "$LAUNCH_ROOT/input-sha256.txt"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCH_ROOT/screen-session.txt"
write_status prepared launch queued null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'CH4_PATH_RISK_LENGTH_BUCKET_DIAGNOSTIC_STARTED session=%s run=%s\n' "$SCREEN_NAME" "$RUN_ROOT"
