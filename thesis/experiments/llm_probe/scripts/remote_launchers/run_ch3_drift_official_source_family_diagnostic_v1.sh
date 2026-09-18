#!/usr/bin/env bash
set -euo pipefail
CONFIG="configs/ch3-drift-official-source-family-diagnostic-v1.json"
RUN_ID="ch3-drift-official-source-family-diagnostic-v1"
PULL_INTERVAL_SECONDS=30 PULL_MAX_SIZE=5m bash scripts/remote_launchers/launch_run_with_pull.sh "$CONFIG" "$RUN_ID" "--run-dir runs/diagnostics/$RUN_ID --parallel-years --resume" "tools/ch3_drift_official_source_family_diagnostic.py"
