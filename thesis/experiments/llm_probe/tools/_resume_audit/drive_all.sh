#!/usr/bin/env bash
set -u
cd /root/autodl-tmp/thesis/experiments/llm_probe || exit 90
R=$PWD/runs/diagnostics/_resume_audit_tmp
bash tools/_resume_audit/run_case.sh transformer C11 3 1000 "$R"
bash tools/_resume_audit/run_full4.sh cnn 3 400 "$R"
bash tools/_resume_audit/run_case.sh rwkv7 C11 3 500 "$R"
echo "ALL_DONE"
