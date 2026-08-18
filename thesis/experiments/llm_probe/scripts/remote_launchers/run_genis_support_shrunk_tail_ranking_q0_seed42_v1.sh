#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=genis-60s-support-shrunk-extreme-tail-ranking-q0-seed42-v1
readonly SCREEN_NAME=genis-tail-q0-s42-v1
readonly OUTPUT_ROOT=/root/autodl-tmp/thesis/experiments/genis/runs/q0/$RUN_ID
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/genis-support-shrunk-tail-ranking-q0-seed42-v1.json"
readonly MODULE_PATH="$PROJECT_ROOT/src/flow_probe/genis_support_shrunk_tail_ranking_q0.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_genis_support_shrunk_tail_ranking_q0_seed42_v1.sh"
readonly CORRECTED_MODULE_PATH="$PROJECT_ROOT/src/flow_probe/genis_scenario_holdout_corrected_v2.py"
readonly CORRECTED_CONFIG_PATH="$PROJECT_ROOT/configs/genis-scenario-holdout-corrected-v2-parallel-seed42.json"
readonly MODULE=flow_probe.genis_support_shrunk_tail_ranking_q0
readonly ARCHIVE=/root/autodl-tmp/thesis/raw/datasets/GeNIS-2025/3-scenarios.zip
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=malicious-traffic-llm

cd "$PROJECT_ROOT"
source tools/env/activate.sh

GPU_MEMORY_USED_MIB=$(nvidia-smi --query-gpu=memory.used \
    --format=csv,noheader,nounits 2>/dev/null || true)
GPU_UTILIZATION_PERCENT=$(nvidia-smi --query-gpu=utilization.gpu \
    --format=csv,noheader,nounits 2>/dev/null || true)
GPU_PROCESS_COUNT=$(nvidia-smi --query-compute-apps=pid \
    --format=csv,noheader,nounits 2>/dev/null | wc -l)
[[ "$GPU_MEMORY_USED_MIB" =~ ^[0-9]+$ ]] || GPU_MEMORY_USED_MIB=null
[[ "$GPU_UTILIZATION_PERCENT" =~ ^[0-9]+$ ]] || GPU_UTILIZATION_PERCENT=null
[[ "$GPU_PROCESS_COUNT" =~ ^[0-9]+$ ]] || GPU_PROCESS_COUNT=0
readonly GPU_MEMORY_USED_MIB GPU_UTILIZATION_PERCENT GPU_PROCESS_COUNT

write_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    mkdir -p -- "$LAUNCHER_ROOT"
    printf '{\n' > "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "contract_version": "support-shrunk-tail-ranking-q0-v1",\n' >> "$partial"
    printf '  "total_evaluation_units": 112,\n' >> "$partial"
    printf '  "max_outer_concurrency": 2,\n' >> "$partial"
    printf '  "max_xgboost_concurrency": 1,\n' >> "$partial"
    printf '  "unrelated_gpu_processes_allowed": true,\n' >> "$partial"
    printf '  "memory_admission_gate": false,\n' >> "$partial"
    printf '  "launch_gpu_process_count": %s,\n' "$GPU_PROCESS_COUNT" >> "$partial"
    printf '  "launch_gpu_memory_used_mib": %s,\n' "$GPU_MEMORY_USED_MIB" >> "$partial"
    printf '  "launch_gpu_utilization_percent": %s,\n' "$GPU_UTILIZATION_PERCENT" >> "$partial"
    printf '  "screening_only": true,\n' >> "$partial"
    printf '  "formal_paper_evidence": false,\n' >> "$partial"
    printf '  "official_test_accessed": false,\n' >> "$partial"
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

worker() {
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || return 75
    write_status running evaluation_matrix started null
    set +e
    uv run --no-sync python -m "$MODULE" run --config "$CONFIG_PATH" \
        2>&1 | tee "$LAUNCHER_ROOT/matrix.log"
    local matrix_status=("${PIPESTATUS[@]}")
    set -e
    if [[ "${matrix_status[0]}" -ne 0 || "${matrix_status[1]}" -ne 0 ]]; then
        local matrix_exit=${matrix_status[0]}
        [[ "$matrix_exit" -ne 0 ]] || matrix_exit=${matrix_status[1]}
        write_status failed evaluation_matrix command_or_log_failed "$matrix_exit"
        return "$matrix_exit"
    fi
    set +e
    uv run --no-sync python -m "$MODULE" swanlab-publish --config "$CONFIG_PATH" \
        --authorized-workspace "$SWANLAB_WORKSPACE" \
        --authorized-project "$SWANLAB_PROJECT" \
        2>&1 | tee "$LAUNCHER_ROOT/swanlab.log"
    local publish_status=("${PIPESTATUS[@]}")
    set -e
    if [[ "${publish_status[0]}" -ne 0 || "${publish_status[1]}" -ne 0 ]]; then
        local publish_exit=${publish_status[0]}
        [[ "$publish_exit" -ne 0 ]] || publish_exit=${publish_status[1]}
        write_status failed swanlab command_or_log_failed "$publish_exit"
        return "$publish_exit"
    fi
    write_status finished complete evaluation_and_upload_finished 0
}

if [[ ${1:-} == --worker ]]; then
    set +e
    worker 2>&1 | tee "$LAUNCHER_ROOT/controller.log"
    controller_status=("${PIPESTATUS[@]}")
    set -e
    controller_exit=${controller_status[0]}
    [[ "$controller_exit" -ne 0 ]] || controller_exit=${controller_status[1]}
    if [[ "${controller_status[0]}" -ne 0 || "${controller_status[1]}" -ne 0 ]]; then
        write_status failed controller worker_or_log_failed "$controller_exit"
    fi
    exit "$controller_exit"
fi

if [[ $# -ne 0 || -e "$OUTPUT_ROOT" || -e "$LAUNCHER_ROOT" ]]; then
    printf '参数错误，或 Q0 唯一运行根/启动器根已存在。\n' >&2
    exit 73
fi
if [[ ! -s "$CONFIG_PATH" || ! -s "$MODULE_PATH" || ! -s "$SCRIPT_PATH" \
    || ! -s "$CORRECTED_MODULE_PATH" || ! -s "$CORRECTED_CONFIG_PATH" \
    || ! -s "$ARCHIVE" ]]; then
    printf 'Q0、corrected-v2 生产文件或 3-scenarios.zip 不完整。\n' >&2
    exit 66
fi
if ! command -v screen >/dev/null 2>&1 || ! command -v flock >/dev/null 2>&1; then
    printf '远端缺少 screen 或 flock。\n' >&2
    exit 69
fi
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名 Q0 screen 已运行。\n' >&2
    exit 75
fi
if pgrep -f "flow_probe[.]genis_support_shrunk_tail_ranking_q0|${RUN_ID}" >/dev/null; then
    printf 'Q0 同模块或同运行身份进程已存在。\n' >&2
    exit 75
fi
mkdir -p -- "$LAUNCHER_ROOT"
uv run --no-sync python -c 'import joblib, numpy, sklearn, swanlab, xgboost'
uv run --no-sync python -m "$MODULE" --help > "$LAUNCHER_ROOT/cli-help.txt"
sha256sum "$CONFIG_PATH" "$MODULE_PATH" "$SCRIPT_PATH" \
    "$CORRECTED_MODULE_PATH" "$CORRECTED_CONFIG_PATH" "$ARCHIVE" \
    > "$LAUNCHER_ROOT/input-sha256.txt"
write_status prepared launch q0_contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'GENIS_TAIL_Q0_STARTED session=%s output=%s max_outer_concurrency=2 max_xgboost_concurrency=1\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT"
