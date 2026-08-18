#!/usr/bin/env bash
set -uo pipefail
ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
cd "$ROOT"
source "$ROOT/tools/env/activate.sh" >/dev/null 2>&1
uv run --no-sync python tools/dijk2026_replication/recon_schema.py
