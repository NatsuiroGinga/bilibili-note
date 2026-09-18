#!/usr/bin/env bash
set -euo pipefail

CONFIG="configs/ch3-drift-t17-equal3-auxheads-gradient-base-v1.json"
ARM="${1:-char}"
case "${ARM}" in
  char) RUN_ID="ch3-drift-t17-equal3-auxheads-char-gradient-base-v1" ;;
  subword) RUN_ID="ch3-drift-t17-equal3-auxheads-subword-gradient-base-v1" ;;
  *) printf '%s\n' "用法：$0 [char|subword]" >&2; exit 2 ;;
esac

PULL_INTERVAL_SECONDS=30 PULL_MAX_SIZE=512m \
  bash scripts/remote_launchers/launch_run_with_pull.sh \
  "${CONFIG}" "${RUN_ID}" \
  "--project-root . --run-dir runs/diagnostics/${RUN_ID} --arm ${ARM} --resume" \
  "tools/ch3_drift_t17_equal3_auxheads_gradient_base.py"
