#!/bin/bash
# 并发启动两个类别条件风险单机制资格探针，并为每个运行绑定回传守护。

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONFIG="configs/ch3-drift-bresnet-dual-condrisk-screen-v1.json"
ENTRYPOINT="tools/ch3_drift_bresnet_dual_condrisk_screen.py"

cd "$ROOT"
for arm in c10 c01; do
  run_id="ch3-drift-bresnet-dual-condrisk-screen-v1-${arm}"
  PULL_INTERVAL_SECONDS=30 PULL_MAX_SIZE=5m \
    bash scripts/remote_launchers/launch_run_with_pull.sh \
      "$CONFIG" \
      "$run_id" \
      "--arm $arm --run-dir runs/diagnostics/$run_id --resume" \
      "$ENTRYPOINT"
done
