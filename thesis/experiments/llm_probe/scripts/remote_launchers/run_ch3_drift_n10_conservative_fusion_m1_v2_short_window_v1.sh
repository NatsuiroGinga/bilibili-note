#!/usr/bin/env bash
set -euo pipefail

CONFIG="configs/ch3-drift-n10-conservative-fusion-m1-v2-short-window-v1.json"
ARM="${1:-scale_free_primal_dual}"
case "${ARM}" in
  scale_free_primal_dual|unit_hinge_control) ;;
  *) printf '%s\n' "用法：$0 [scale_free_primal_dual|unit_hinge_control]" >&2; exit 2 ;;
esac
RUN_ID="ch3-drift-n10-conservative-fusion-m1-v2-short-window-v1-${ARM}"
PULL_INTERVAL_SECONDS=30 PULL_MAX_SIZE=5m \
  bash scripts/remote_launchers/launch_run_with_pull.sh \
  "${CONFIG}" "${RUN_ID}" \
  "--project-root . --run-dir runs/diagnostics/ch3-drift-n10-conservative-fusion-m1-v2-short-window-v1 --arm ${ARM} --resume" \
  "tools/ch3_drift_n10_conservative_fusion_m1_v2_short_window.py"
