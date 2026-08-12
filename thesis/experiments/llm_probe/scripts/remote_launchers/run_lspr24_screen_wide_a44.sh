#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
RUN_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr24-screen-wide-v1"
LAUNCH_ROOT="$PROJECT_ROOT/runs/launchers/lspr24-screen-wide-v1"
CONFIG_PATH=tools/lspr24_g0/configs/lspr24-development-wide-screen-v1.json
BINARY_PATH=tools/lspr24_g0/target/release/lspr24_development_wide
SESSION_NAME=lspr24-screen-wide-v1
SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_lspr24_screen_wide_a44.sh"

export PATH="/root/.cargo/bin:$PATH"
source "$PROJECT_ROOT/tools/env/activate.sh"

write_state() {
    local state=$1
    local exit_code=$2
    local temporary="$LAUNCH_ROOT/status.json.new"
    printf '{"state":"%s","exit_code":%s,"run_root":"%s"}\n' \
        "$state" "$exit_code" "$RUN_ROOT" > "$temporary"
    mv "$temporary" "$LAUNCH_ROOT/status.json"
}

run_worker() {
    cd "$PROJECT_ROOT"
    printf '%s\n' "$$" > "$LAUNCH_ROOT/materialize.pid"
    write_state running null
    set +e
    "$BINARY_PATH" "$CONFIG_PATH" 2>&1 | tee "$LAUNCH_ROOT/launcher-attempt-9.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local materialize_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$materialize_code" > "$LAUNCH_ROOT/materialize.exit-code"
    printf '%s\n' "$tee_code" > "$LAUNCH_ROOT/tee.exit-code"
    if [[ "$materialize_code" -eq 0 && "$tee_code" -eq 0 ]]; then
        write_state finished 0
        return 0
    fi
    local failure_code=$materialize_code
    if [[ "$failure_code" -eq 0 ]]; then
        failure_code=$tee_code
    fi
    write_state failed "$failure_code"
    return "$failure_code"
}

if [[ "${1:-}" == "--worker" ]]; then
    run_worker
    exit $?
fi

cd "$PROJECT_ROOT"
command -v cargo >/dev/null
command -v rustc >/dev/null
command -v screen >/dev/null
mkdir -p "$RUN_ROOT" "$LAUNCH_ROOT"

for artifact in \
    field-manifest.json \
    working \
    development-wide.parquet \
    development-labels.parquet \
    temporal-relations.parquet \
    development-wide-receipt.json \
    dataset-manifest.json; do
    if [[ -e "$RUN_ROOT/$artifact" ]]; then
        printf '正式运行目录已有制品：%s\n' "$RUN_ROOT/$artifact" >&2
        exit 3
    fi
done

if screen -list | rg -F ".$SESSION_NAME" >/dev/null; then
    printf '持久会话已存在：%s\n' "$SESSION_NAME" >&2
    exit 4
fi

set +e
cargo build --manifest-path tools/lspr24_g0/Cargo.toml --release --locked \
    --bin lspr24_development_wide 2>&1 | tee "$LAUNCH_ROOT/build-remote-attempt-9.log"
build_status=("${PIPESTATUS[@]}")
set -e
if [[ "${build_status[0]}" -ne 0 || "${build_status[1]}" -ne 0 ]]; then
    failure_code=${build_status[0]}
    if [[ "$failure_code" -eq 0 ]]; then
        failure_code=${build_status[1]}
    fi
    write_state failed "$failure_code"
    exit "$failure_code"
fi

printf '%s\n' \
    "$BINARY_PATH $CONFIG_PATH" > "$LAUNCH_ROOT/command.txt"
write_state prepared null
screen -dmS "$SESSION_NAME" bash "$SCRIPT_PATH" --worker
printf 'REMOTE_LSPR24_STARTED session=%s\n' "$SESSION_NAME"
