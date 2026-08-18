#!/usr/bin/env bash
# 启动 ch3_hparam_fairsel_v2.py：唯一 GPU 进程，两组共 28 次训练进程内串行，
# 数据只加载一次，日志落唯一运行目录 runs/diagnostics/ch3-hparam-fairsel-v2/run.log。
set -uo pipefail
ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
OUT="$ROOT/runs/diagnostics/ch3-hparam-fairsel-v2"
LOG="$OUT/run.log"
PIDF="$OUT/run.pid"
mkdir -p "$OUT"

if [ -f "$ROOT/tools/env/activate.sh" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/tools/env/activate.sh" >/dev/null 2>&1 || true
fi

# 门禁一：不得重复启动
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
  echo "GATE_FAIL 已有 v2 进程 pid=$(cat "$PIDF")，拒绝重复启动"
  exit 3
fi
# 门禁二：GPU 必须空闲
if nvidia-smi --query-compute-apps=pid --format=csv,noheader | grep -q .; then
  echo "GATE_FAIL GPU 上已有计算进程，拒绝启动"
  nvidia-smi --query-compute-apps=pid,used_memory --format=csv
  exit 4
fi
# 门禁三：源码与缓存就位
[ -f "$ROOT/tools/ch3_hparam_fairsel_v2.py" ] || { echo "GATE_FAIL 缺 v2 脚本"; exit 5; }
for f in X23 y23 ent23 t23_flow I23 M23 E23 T23 X24 y24 s24 d24 t24 I24 M24; do
  [ -f "$ROOT/runs/diagnostics/dijk-repro/cache/$f.npy" ] || { echo "GATE_FAIL 缺缓存 $f.npy"; exit 6; }
done
# 门禁四：不得覆盖上一轮 v1 的 run.log
[ -f "$ROOT/runs/diagnostics/ch3-hparam-fairsel/run.log" ] || echo "WARN v1 run.log 不存在（不阻断）"

cd "$ROOT" || exit 1
nohup setsid uv run --no-sync python tools/ch3_hparam_fairsel_v2.py > "$LOG" 2>&1 &
echo $! > "$PIDF"
sleep 20
echo "GATE_OK 已启动 pid=$(cat "$PIDF")"
echo "--- 日志前 20 行 ---"
head -20 "$LOG"
