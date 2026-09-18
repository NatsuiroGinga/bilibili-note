#!/usr/bin/env bash
set -euo pipefail

CONFIG="configs/ch3-drift-condmem-source-qualification-v1.json"
RUN_ID="ch3-drift-condmem-source-qualification-v1"

PULL_INTERVAL_SECONDS=30 PULL_MAX_SIZE=512m \
  bash scripts/remote_launchers/launch_run_with_pull.sh \
  "${CONFIG}" "${RUN_ID}" \
  "--project-root . --run-dir runs/diagnostics/${RUN_ID} --resume" \
  "tools/ch3_drift_condmem_source_qualification.py"
