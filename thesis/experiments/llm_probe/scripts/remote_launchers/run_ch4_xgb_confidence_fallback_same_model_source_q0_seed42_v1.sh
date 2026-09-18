#!/usr/bin/env bash
source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch4-xgb-confidence-fallback-same-model-source-q0-seed42-v1
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch4_xgb_confidence_fallback_same_model_source_q0.py"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch4-xgb-confidence-fallback-same-model-source-q0-seed42-v1.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch4_xgb_confidence_fallback_same_model_source_q0_seed42_v1.sh"
readonly PARENT_RUN_ID=ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1
readonly PARENT_RUN_ROOT="$PROJECT_ROOT/runs/diagnostics/$PARENT_RUN_ID"
readonly PARENT_CONFIG_PATH="$PROJECT_ROOT/configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json"
readonly RECOVERY_PROOF_PATH="$PROJECT_ROOT/runs/recovery/${PARENT_RUN_ID}-for-ch4-xgb-pbc-q0-seed42-v1-rerun2-v1/parent-recovery-proof.json"
readonly RUN_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly LAUNCH_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"

write_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    printf '{"run_id":"%s","source_year_only":true,"target_year_arrays_read":0,"new_models_trained":0,"state":"%s","stage":"%s","detail":"%s","exit_code":%s}\n' \
        "$RUN_ID" "$state" "$stage" "$detail" "$exit_code" > "$RUN_ROOT/status.json.partial.$$"
    mv -f -- "$RUN_ROOT/status.json.partial.$$" "$RUN_ROOT/status.json"
}

run_tool() {
    uv run --no-sync python "$TOOL_PATH" \
        --config "$CONFIG_PATH" \
        --parent-run-root "$PARENT_RUN_ROOT" \
        --parent-config "$PARENT_CONFIG_PATH" \
        --parent-recovery-proof "$RECOVERY_PROOF_PATH" \
        --out "$RUN_ROOT" "$@"
}

worker() {
    cd "$PROJECT_ROOT"
    source tools/env/activate.sh
    write_status running source_q0 started null
    set +e
    run_tool 2>&1 | tee "$RUN_ROOT/run.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    if [[ "${pipeline_status[0]}" -ne 0 ]]; then
        write_status failed source_q0 python_failed "${pipeline_status[0]}"
        return "${pipeline_status[0]}"
    fi
    if [[ "${pipeline_status[1]}" -ne 0 ]]; then
        write_status failed source_q0 tee_failed "${pipeline_status[1]}"
        return "${pipeline_status[1]}"
    fi
    write_status finished complete success 0
}

if [[ ${1:-} == --worker ]]; then
    worker
    exit $?
fi

cd "$PROJECT_ROOT"
source tools/env/activate.sh
if [[ -e "$RUN_ROOT" || -e "$LAUNCH_ROOT" ]]; then
    printf '同名运行目录已存在，禁止覆盖：%s\n' "$RUN_ROOT" >&2
    exit 73
fi
run_tool --validate-inputs
mkdir -p "$RUN_ROOT" "$LAUNCH_ROOT"
write_status prepared launch queued null
nohup setsid bash "$SCRIPT_PATH" --worker > "$LAUNCH_ROOT/launcher.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$LAUNCH_ROOT/worker.pid"
printf 'MECHANISM2_SAME_MODEL_SOURCE_Q0_STARTED run=%s pid=%s\n' "$RUN_ROOT" "$!"
