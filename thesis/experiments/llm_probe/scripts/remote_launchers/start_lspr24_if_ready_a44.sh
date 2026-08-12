#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
INPUT_PATH="$PROJECT_ROOT/data/raw/lspr24-v1/lspr24_v2.parquet"
EXPECTED_SIZE=2775972952
EXPECTED_SHA256=1d96f0a023de583397cc300143ba98b84b9e9bd2270f0b8b61346ca19963057a

if [[ ! -f "$INPUT_PATH" ]]; then
    printf 'LSPR24 输入不存在：%s\n' "$INPUT_PATH" >&2
    exit 2
fi

actual_size=$(stat -c '%s' "$INPUT_PATH")
actual_hash_line=$(sha256sum "$INPUT_PATH")
actual_hash=${actual_hash_line%% *}

if [[ "$actual_size" == "$EXPECTED_SIZE" && "$actual_hash" == "$EXPECTED_SHA256" ]]; then
    printf 'LSPR24_INPUT_READY size=%s sha256=%s\n' "$actual_size" "$actual_hash"
    exec bash "$PROJECT_ROOT/scripts/remote_launchers/run_lspr24_screen_wide_a44.sh"
else
    printf 'LSPR24_INPUT_INVALID expected_size=%s actual_size=%s expected_sha256=%s actual_sha256=%s\n' \
        "$EXPECTED_SIZE" "$actual_size" "$EXPECTED_SHA256" "$actual_hash" >&2
    exit 3
fi
