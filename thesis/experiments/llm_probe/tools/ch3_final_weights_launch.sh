#!/usr/bin/env bash
# 启动 ch3_final_weights_freeze.py：后台运行，日志落唯一运行目录。
# 与 ch3_fairsel_launch.sh 的差别：不再要求 GPU 上无任何计算进程，改为要求空闲显存 >= 14 GiB，
# 因为本机可能有其它实验在跑，绝不杀别人的进程。
set -uo pipefail
ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
OUT="$ROOT/runs/diagnostics/ch3-final-weights"
LOG="$OUT/run.log"
MIN_FREE_MIB=14336
mkdir -p "$OUT"

if [ -f "$ROOT/tools/env/activate.sh" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/tools/env/activate.sh" >/dev/null 2>&1 || true
fi

if pgrep -f ch3_final_weights_freeze.py >/dev/null 2>&1; then
  echo "已有 ch3_final_weights_freeze.py 进程，拒绝重复启动"
  pgrep -af ch3_final_weights_freeze.py
  exit 3
fi

FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
echo "GPU 空闲显存 ${FREE} MiB（门槛 ${MIN_FREE_MIB} MiB）"
if [ "$FREE" -lt "$MIN_FREE_MIB" ]; then
  echo "空闲显存不足，拒绝启动；不得杀死他人进程"
  nvidia-smi --query-compute-apps=pid,used_memory --format=csv
  exit 4
fi
echo "GPU 上现有计算进程（只做记录，不干预）："
nvidia-smi --query-compute-apps=pid,used_memory --format=csv

cd "$ROOT" || exit 1
nohup setsid bash -c "cd $ROOT && uv run --no-sync python tools/ch3_final_weights_freeze.py > $LOG 2>&1; echo EXIT=\$? >> $LOG" >/dev/null 2>&1 &
sleep 6
echo "已启动，进程："
pgrep -af ch3_final_weights_freeze.py || echo "（未见进程，检查日志）"
echo "日志：$LOG"
tail -5 "$LOG" 2>/dev/null
