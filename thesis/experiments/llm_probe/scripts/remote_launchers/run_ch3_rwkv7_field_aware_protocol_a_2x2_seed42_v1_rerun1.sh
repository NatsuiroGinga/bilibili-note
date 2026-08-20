#!/usr/bin/env bash

set -Eeuo pipefail

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
export RWKV_RUN_ID=ch3-rwkv7-field-aware-protocol-a-2x2-seed42-v1-rerun1
export RWKV_SCREEN_NAME=ch3-rwkv7-field-aware-protocol-a-s42-v1-rerun1
export RWKV_SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_rwkv7_field_aware_protocol_a_2x2_seed42_v1_rerun1.sh"
export RWKV_MIGRATE_FROM_RUN_ROOT="$PROJECT_ROOT/runs/diagnostics/ch3-rwkv7-field-aware-protocol-a-2x2-seed42-v1"

exec bash "$PROJECT_ROOT/scripts/remote_launchers/run_ch3_rwkv7_field_aware_protocol_a_2x2_seed42_v1.sh" "$@"
