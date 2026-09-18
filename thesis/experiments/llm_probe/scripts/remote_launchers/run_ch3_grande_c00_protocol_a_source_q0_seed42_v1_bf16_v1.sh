#!/usr/bin/env bash

set -Eeuo pipefail

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly SHARED_LAUNCHER="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_grande_c00_protocol_a_source_q0_seed42_v1.sh"

export GRANDE_RUN_ID=ch3-grande-c00-protocolA-source-q0-seed42-v1-bf16-v1
export GRANDE_SCREEN_NAME=ch3-grande-pa-bf16-s42-v1
export GRANDE_CONFIG_PATH="$PROJECT_ROOT/configs/ch3-grande-c00-protocol-a-source-q0-seed42-v1-bf16-v1.json"
export GRANDE_SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_grande_c00_protocol_a_source_q0_seed42_v1_bf16_v1.sh"
export GRANDE_REUSE_COMPLETED_G_A=false
export GRANDE_PRECISION_PROFILE=cuda-bf16-amp-fp32-sensitive-v1

exec bash "$SHARED_LAUNCHER" "$@"
