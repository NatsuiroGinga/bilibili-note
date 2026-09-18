#!/usr/bin/env bash
set -euo pipefail

CONFIG="configs/ch3-drift-n10-conservative-fusion-t18-selection-v1.json"
RUN_ID="ch3-drift-n10-conservative-fusion-t18-selection-v1"
PULL_INTERVAL_SECONDS=30 PULL_MAX_SIZE=5m \
  bash scripts/remote_launchers/launch_run_with_pull.sh \
  "${CONFIG}" "${RUN_ID}" \
  "--project-root . --run-dir runs/diagnostics/${RUN_ID}" \
  "tools/ch3_drift_n10_conservative_fusion_t18_selection.py"
