#!/usr/bin/env bash
# E5 机制余量证伪启动器：内存准入门禁 -> 只读冻结分数分析。
# 不重训、不改写 val_scores.parquet、不触及最终封存区。
set -uo pipefail

PROJ=/root/autodl-tmp/thesis/experiments/llm_probe
RUN="$PROJ/runs/diagnostics/lspr24-decision-rule-headroom-v1"
mkdir -p "$RUN"
cd "$PROJ" || exit 1

echo "[E5] 内存准入门禁（预计峰值 5 GiB）"
bash tools/memory_admission_gate.sh 5 lspr24-decision-rule-headroom-v1
GATE_RC=$?
if [ "$GATE_RC" -ne 0 ]; then
  echo "[E5] 门禁未通过 rc=$GATE_RC，中止启动"
  exit "$GATE_RC"
fi

echo "[E5] 门禁通过，开始只读分析"
uv run --no-sync python "$RUN/e5_decision_rule_headroom.py"
RC=$?
echo "[E5] 退出码=$RC"
exit "$RC"
