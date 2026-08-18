#!/usr/bin/env bash
# 启动 ch3_2x2_fairsel.py：唯一 GPU 进程，四格进程内串行，日志落唯一运行目录。
set -uo pipefail
ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
OUT="$ROOT/runs/diagnostics/ch3-2x2-fairsel"
LOG="$OUT/run.log"
mkdir -p "$OUT"

if [ -f "$ROOT/tools/env/activate.sh" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/tools/env/activate.sh" >/dev/null 2>&1 || true
fi

if screen -ls | grep -q ch3fairsel; then
  echo "已有 ch3fairsel 会话，拒绝重复启动"
  screen -ls | grep ch3fairsel
  exit 3
fi
if nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q .; then
  echo "GPU 上已有计算进程，拒绝启动"
  nvidia-smi --query-compute-apps=pid,used_memory --format=csv
  exit 4
fi

cd "$ROOT" || exit 1
screen -dmS ch3fairsel bash -c "cd $ROOT && uv run --no-sync python tools/ch3_2x2_fairsel.py > $LOG 2>&1; echo EXIT=\$? >> $LOG"
sleep 5
echo "已启动，会话："
screen -ls | grep ch3fairsel
echo "日志：$LOG"
