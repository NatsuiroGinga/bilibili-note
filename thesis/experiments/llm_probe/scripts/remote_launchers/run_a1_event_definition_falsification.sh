#!/usr/bin/env bash
# E1 证伪实验启动器：验证集事件切分对删失窗的敏感性（时间容差重定义）。
# 只读 val_scores.parquet（冻结分数）与元数据列，不加载 408 维特征矩阵，
# 预计峰值 < 6 GiB，因此不需要 GPU 显存检查。
set -uo pipefail
BASE=/root/autodl-tmp/thesis/experiments/llm_probe
OUT="$BASE/runs/diagnostics/lspr24-a1-event-definition-falsification-v1"
mkdir -p "$OUT"
cd "$BASE" || exit 3

# 预计峰值：元数据 ~250MB + 冻结分数 ~100MB + 前缀和数组 ~70MB +
# temporal-relations 单个 row group ~25MB + pandas/pyarrow 基线开销，
# 报 4 GiB 留出充足冗余（远低于 6 GiB 上限）。
bash tools/memory_admission_gate.sh 4 lspr24-a1-event-definition-falsification-v1
GATE=$?
if [ "$GATE" -ne 0 ]; then
  echo "准入门禁未通过，退出码 $GATE，不启动"
  exit "$GATE"
fi

if screen -ls | grep -q a1-event-def-falsification; then
  echo "已有 a1-event-def-falsification 会话，拒绝重复启动"
  exit 1
fi

LOG="$OUT/run.log"
echo "[runner] script=a1_event_definition_falsification.py" > "$LOG"
screen -dmS a1-event-def-falsification bash -c \
  "cd $BASE && uv run --no-sync python $OUT/a1_event_definition_falsification.py >> $LOG 2>&1; echo \"[runner] exit_code=\$?\" >> $LOG"

sleep 5
echo "--- screen"
screen -ls | grep a1-event-def-falsification || echo "警告：未见会话"
echo "--- 首批日志"
head -20 "$LOG"
