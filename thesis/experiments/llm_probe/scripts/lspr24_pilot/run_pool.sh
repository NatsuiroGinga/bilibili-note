#!/usr/bin/env bash
source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
ROOT=/root/autodl-tmp/ab-pilot
PY=/root/autodl-tmp/thesis/experiments/llm_probe/.venv/bin/python
cd "$ROOT"
"$PY" -u pooled_history.py "$ROOT/ab_windows_cache.npz" > pool.log 2>&1
