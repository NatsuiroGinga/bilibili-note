#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=genis-60s-scenario-holdout-safe-core-baselines-seed42-v1
readonly SCREEN_NAME=genis-scenario-holdout-baselines-s42-v1
readonly OUTPUT_ROOT=/root/autodl-tmp/thesis/experiments/genis/runs/baselines/$RUN_ID
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/genis-scenario-holdout-baselines-60s-seed42-v1.json"
readonly MODULE_PATH="$PROJECT_ROOT/src/flow_probe/genis_scenario_holdout_baselines.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_genis_scenario_holdout_baselines_60s_seed42_v1.sh"
readonly MODULE=flow_probe.genis_scenario_holdout_baselines
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=malicious-traffic-llm

cd "$PROJECT_ROOT"
source tools/env/activate.sh

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
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

worker() {
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || return 75
    write_status running matrix started null
    set +e
    uv run --no-sync python -m "$MODULE" run --config "$CONFIG_PATH" \
        2>&1 | tee "$LAUNCHER_ROOT/matrix.log"
    local matrix_code=${PIPESTATUS[0]}
    set -e
    if [[ "$matrix_code" -ne 0 ]]; then
        write_status failed matrix command_failed "$matrix_code"
        return "$matrix_code"
    fi
    uv run --no-sync python -m "$MODULE" swanlab-publish --config "$CONFIG_PATH" \
        --authorized-workspace "$SWANLAB_WORKSPACE" \
        --authorized-project "$SWANLAB_PROJECT" \
        2>&1 | tee "$LAUNCHER_ROOT/swanlab.log"
    write_status finished complete matrix_and_upload_finished 0
}

if [[ ${1:-} == --worker ]]; then
    set +e
    worker 2>&1 | tee "$LAUNCHER_ROOT/controller.log"
    code=${PIPESTATUS[0]}
    set -e
    if [[ "$code" -ne 0 ]]; then
        write_status failed controller worker_failed "$code"
    fi
    exit "$code"
fi

if [[ $# -ne 0 || -e "$OUTPUT_ROOT" ]]; then
    printf '参数错误或唯一运行根已存在。\n' >&2
    exit 73
fi
if [[ ! -s "$CONFIG_PATH" || ! -s "$MODULE_PATH" || ! -s "$SCRIPT_PATH" ]]; then
    printf '生产文件不存在。\n' >&2
    exit 66
fi
if [[ ! -s /root/autodl-tmp/thesis/raw/datasets/GeNIS-2025/2-flows.zip \
    || ! -s /root/autodl-tmp/thesis/raw/datasets/GeNIS-2025/3-scenarios.zip ]]; then
    printf 'Track B 原始 ZIP 不完整。\n' >&2
    exit 66
fi
if ! command -v screen >/dev/null 2>&1 || ! command -v flock >/dev/null 2>&1; then
    printf '远端缺少 screen 或 flock。\n' >&2
    exit 69
fi
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名 screen 已运行。\n' >&2
    exit 75
fi
if [[ "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)" -ne 0 ]]; then
    printf 'GPU 已有计算进程。\n' >&2
    exit 75
fi
mkdir -p -- "$LAUNCHER_ROOT"
uv run --no-sync python -c 'import joblib, numpy, sklearn, swanlab, xgboost'
sha256sum "$CONFIG_PATH" "$MODULE_PATH" "$SCRIPT_PATH" \
    /root/autodl-tmp/thesis/raw/datasets/GeNIS-2025/2-flows.zip \
    /root/autodl-tmp/thesis/raw/datasets/GeNIS-2025/3-scenarios.zip \
    > "$LAUNCHER_ROOT/input-sha256.txt"
write_status prepared launch contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'GENIS_SCENARIO_HOLDOUT_STARTED session=%s output=%s\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT"
