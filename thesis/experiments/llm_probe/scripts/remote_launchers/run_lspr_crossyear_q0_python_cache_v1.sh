#!/usr/bin/env bash

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
if [[ -r "${HOME}/.bashrc" ]]; then
    source "${HOME}/.bashrc" >/dev/null 2>&1
fi
source "$PROJECT_ROOT/tools/env/activate.sh"
set -Eeuo pipefail
umask 027

readonly RUN_ID=lspr23-lspr24-q0-python-cache-seed42-v1
readonly RUN_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly LOG_PATH="$RUN_ROOT/cache.log"
readonly STATUS_PATH="$RUN_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/lspr-crossyear-c12-seed42-q0-v1.json"
readonly OUTPUT_DIR="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"
readonly RECEIPT_PATH="$OUTPUT_DIR/cache-manifest.json"

write_status() {
    local state=$1
    local exit_code=$2
    local finished_at=$3
    local partial="$STATUS_PATH.partial"
    printf '{\n' > "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "finished_at": %s,\n' "$finished_at" >> "$partial"
    printf '  "config_path": "%s",\n' "$CONFIG_PATH" >> "$partial"
    printf '  "output_dir": "%s",\n' "$OUTPUT_DIR" >> "$partial"
    printf '  "log_path": "%s",\n' "$LOG_PATH" >> "$partial"
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

handle_signal() {
    write_status interrupted 130 "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
    exit 130
}

trap handle_signal HUP INT TERM
mkdir -p -- "$RUN_ROOT"

if [[ -s "$RECEIPT_PATH" ]]; then
    printf 'Q0 Python 缓存已存在成功收据，不重复运行：%s\n' "$RECEIPT_PATH"
    write_status finished 0 "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
    exit 0
fi
if [[ -e "$OUTPUT_DIR" ]]; then
    printf '发现无成功收据的既有缓存目录，拒绝覆盖：%s\n' "$OUTPUT_DIR" >&2
    write_status blocked 73 "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
    exit 73
fi

write_status running null null
printf 'Q0 Python 缓存开始：%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
printf '配置：%s\n' "$CONFIG_PATH"
printf '输出：%s\n' "$OUTPUT_DIR"

set +e
PYTHONPATH="$PROJECT_ROOT/src" python -c \
    'from pathlib import Path; from flow_probe.lspr_crossyear_dataset import prepare_crossyear_cache; prepare_crossyear_cache(Path("/root/autodl-tmp/thesis/experiments/llm_probe/configs/lspr-crossyear-c12-seed42-q0-v1.json"), Path("/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"))' \
    2>&1 | tee "$LOG_PATH"
pipeline_status=("${PIPESTATUS[@]}")
set -e

readonly cache_code=${pipeline_status[0]}
readonly tee_code=${pipeline_status[1]}
if [[ "$cache_code" -ne 0 || "$tee_code" -ne 0 ]]; then
    printf 'Q0 Python 缓存失败：cache=%s tee=%s\n' "$cache_code" "$tee_code" >&2
    write_status failed "$cache_code" "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
    exit "$cache_code"
fi
if [[ ! -s "$RECEIPT_PATH" ]]; then
    printf '进程退出 0，但缓存收据不存在或为空：%s\n' "$RECEIPT_PATH" >&2
    write_status failed 74 "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
    exit 74
fi

write_status finished 0 "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
printf 'Q0 Python 缓存完成：%s\n' "$RECEIPT_PATH"
