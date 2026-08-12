#!/usr/bin/env bash

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
if [[ -r "${HOME}/.bashrc" ]]; then
    source "${HOME}/.bashrc" >/dev/null 2>&1
fi
source "$PROJECT_ROOT/tools/env/activate.sh"
set -Eeuo pipefail
umask 027

readonly RUN_ID=lspr23-lspr24-bounded-q0-seed42-v1
readonly RUN_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly LOG_PATH="$RUN_ROOT/materialize.log"
readonly STATUS_PATH="$RUN_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/lspr-crossyear-c12-seed42-q0-v1.json"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1"
readonly TEMPORARY_ROOT="$PROJECT_ROOT/runs/data-prepared/.lspr23-lspr24-bounded-quick-q0-v1-work"
readonly RECEIPT_PATH="$OUTPUT_ROOT/receipts/materialization.json"

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
    printf '  "log_path": "%s",\n' "$LOG_PATH" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
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
if [[ -e "$RECEIPT_PATH" ]]; then
    printf 'Q0 有界缓存已存在成功收据，不重复运行：%s\n' "$RECEIPT_PATH"
    write_status finished 0 "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
    exit 0
fi
if [[ -e "$OUTPUT_ROOT" || -e "$TEMPORARY_ROOT" ]]; then
    printf '发现既有输出或工作根，拒绝覆盖：%s 或 %s\n' "$OUTPUT_ROOT" "$TEMPORARY_ROOT" >&2
    write_status blocked 73 "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
    exit 73
fi

write_status running null null
printf 'Q0 有界缓存开始：%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
printf '配置：%s\n' "$CONFIG_PATH"
printf '日志：%s\n' "$LOG_PATH"

set +e
cargo run --release --locked --offline \
    --manifest-path "$PROJECT_ROOT/tools/lspr24_g0/Cargo.toml" \
    --bin lspr_crossyear_materialize -- \
    --config "$CONFIG_PATH" 2>&1 | tee "$LOG_PATH"
pipeline_status=("${PIPESTATUS[@]}")
set -e

readonly materialize_code=${pipeline_status[0]}
readonly tee_code=${pipeline_status[1]}
if [[ "$materialize_code" -ne 0 || "$tee_code" -ne 0 ]]; then
    printf 'Q0 有界缓存失败：materialize=%s tee=%s\n' "$materialize_code" "$tee_code" >&2
    write_status failed "$materialize_code" "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
    exit "$materialize_code"
fi
if [[ ! -s "$RECEIPT_PATH" ]]; then
    printf '进程退出 0，但成功收据不存在或为空：%s\n' "$RECEIPT_PATH" >&2
    write_status failed 74 "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
    exit 74
fi

write_status finished 0 "\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\""
printf 'Q0 有界缓存完成：%s\n' "$RECEIPT_PATH"
