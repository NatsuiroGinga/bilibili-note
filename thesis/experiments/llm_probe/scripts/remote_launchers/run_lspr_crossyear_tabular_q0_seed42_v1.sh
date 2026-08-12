#!/usr/bin/env bash

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
if [[ -r "${HOME}/.bashrc" ]]; then
    source "${HOME}/.bashrc" >/dev/null 2>&1
fi
source "$PROJECT_ROOT/tools/env/activate.sh"
set -Eeuo pipefail
umask 027

readonly RUN_ID=lspr-crossyear-tabular-q0-seed42-v2
readonly SCREEN_NAME=lspr-crossyear-tabular-q0-seed42-v2
readonly RUN_ROOT="$PROJECT_ROOT/runs/baselines/$RUN_ID"
readonly LOG_PATH="$RUN_ROOT/run.log"
readonly STATUS_PATH="$RUN_ROOT/status.json"
readonly CACHE_MANIFEST="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1/cache-manifest.json"

write_status() {
    local state=$1
    local exit_code=$2
    local partial="$STATUS_PATH.partial"
    printf '{"run_id":"%s","state":"%s","exit_code":%s,"log_path":"%s","final_accessed":false}\n' "$RUN_ID" "$state" "$exit_code" "$LOG_PATH" > "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

if [[ -z "${STY:-}" ]]; then
    if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
        printf '已存在同名 screen，会话不重复启动：%s\n' "$SCREEN_NAME"
        exit 0
    fi
    screen -dmS "$SCREEN_NAME" bash "$0"
    printf '已启动 screen：%s\n' "$SCREEN_NAME"
    exit 0
fi

mkdir -p -- "$RUN_ROOT"
if [[ -e "$RUN_ROOT/finished.json" ]]; then
    printf '已存在成功收据，拒绝重复运行：%s\n' "$RUN_ROOT/finished.json"
    exit 0
fi
if [[ ! -s "$CACHE_MANIFEST" ]]; then
    printf '缓存清单不存在：%s\n' "$CACHE_MANIFEST" >&2
    write_status blocked 74
    exit 74
fi
if [[ -e "$RUN_ROOT/hgb" || -e "$RUN_ROOT/random_forest" || -e "$RUN_ROOT/xgboost" ]]; then
    printf '发现既有模型输出，拒绝覆盖：%s\n' "$RUN_ROOT" >&2
    write_status blocked 73
    exit 73
fi

write_status running null
set +e
{
    printf '开始 HGB：%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -m flow_probe.lspr_crossyear_tabular_baselines --cache-manifest "$CACHE_MANIFEST" --output-dir "$RUN_ROOT/hgb" --model hgb --seed 42
    hgb_code=$?
    if [[ "$hgb_code" -ne 0 ]]; then exit "$hgb_code"; fi
    printf '开始随机森林：%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -m flow_probe.lspr_crossyear_tabular_baselines --cache-manifest "$CACHE_MANIFEST" --output-dir "$RUN_ROOT/random_forest" --model random_forest --seed 42
    rf_code=$?
    if [[ "$rf_code" -ne 0 ]]; then exit "$rf_code"; fi
    if PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -c 'import xgboost' >/dev/null 2>&1; then
        printf '开始 XGBoost：%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -m flow_probe.lspr_crossyear_tabular_baselines --cache-manifest "$CACHE_MANIFEST" --output-dir "$RUN_ROOT/xgboost" --model xgboost --seed 42
    else
        printf 'XGBoost 不可用，已跳过且不阻塞 HGB/随机森林。\n'
        printf '{"status":"unavailable"}\n' > "$RUN_ROOT/xgboost-unavailable.json"
    fi
} 2>&1 | tee "$LOG_PATH"
pipeline_status=("${PIPESTATUS[@]}")
set -e
if [[ "${pipeline_status[0]}" -ne 0 || "${pipeline_status[1]}" -ne 0 ]]; then
    write_status failed "${pipeline_status[0]}"
    exit "${pipeline_status[0]}"
fi
printf '{"state":"finished","final_accessed":false}\n' > "$RUN_ROOT/finished.json"
write_status finished 0
