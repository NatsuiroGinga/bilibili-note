#!/usr/bin/env bash
set -euo pipefail

CONFIG="configs/ch3-drift-n10-conservative-fusion-pilot-v1.json"
RUN_ROOT="ch3-drift-n10-conservative-fusion-pilot-batch1024-v2"
STAGE="${1:-p0_c00}"
ARM="${2:-c00}"

case "${STAGE}:${ARM}" in
  p0_c00:c00|p1_gate:dynamic|p1_gate:qmf|p1_gate:conservative_correction|p1_gate:constant) ;;
  *)
    printf '%s\n' "用法：$0 [p0_c00 c00|p1_gate dynamic|p1_gate qmf|p1_gate conservative_correction|p1_gate constant]" >&2
    exit 2
    ;;
esac

RUN_ID="${RUN_ROOT}"

PULL_INTERVAL_SECONDS=30 PULL_MAX_SIZE=5m \
  bash scripts/remote_launchers/launch_run_with_pull.sh \
  "${CONFIG}" "${RUN_ID}" \
  "--project-root . --run-dir runs/diagnostics/${RUN_ROOT} --stage ${STAGE} --arm ${ARM} --resume" \
  "tools/ch3_drift_n10_conservative_fusion_publication_repair.py"
