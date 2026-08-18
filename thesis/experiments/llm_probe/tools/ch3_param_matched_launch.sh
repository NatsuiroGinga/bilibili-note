#!/usr/bin/env bash
# 启动 ch3_baselines_param_matched.py：等参数预算（90,242±10%）神经基线三架构 × 四档学习率，
# 进程内串行，数据只加载一次，日志落唯一运行目录
# runs/diagnostics/ch3-baselines-param-matched/run.log。
#
# 与 ch3_fairsel_v2_launch.sh 的门禁差异：本轮 GPU 上有正在运行的 ch3_backbone_protocolA.py
# （约 10.6 GiB），不能要求 GPU 完全空闲；改为检查剩余显存是否足够本进程的保守峰值。
set -uo pipefail
ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
OUT="$ROOT/runs/diagnostics/ch3-baselines-param-matched"
LOG="$OUT/run.log"
PIDF="$OUT/run.pid"
NEED_GPU_GIB=9          # 上一轮同数据同评价流程的实测显存峰值 7.33 GiB，留到 9 GiB
NEED_RAM_GIB=20         # CPU 常驻峰值保守估计（X24 6.26 GiB + s24/d24/key24 对象数组）
mkdir -p "$OUT"

if [ -f "$ROOT/tools/env/activate.sh" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/tools/env/activate.sh" >/dev/null 2>&1 || true
fi

# 门禁一：不得重复启动
if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
  echo "GATE_FAIL 已有等参数基线进程 pid=$(cat "$PIDF")，拒绝重复启动"
  exit 3
fi

# 门禁二：源码与缓存就位，且脚本 SHA-256 与本机一致
[ -f "$ROOT/tools/ch3_baselines_param_matched.py" ] || { echo "GATE_FAIL 缺等参数脚本"; exit 5; }
ACTUAL_SHA=$(sha256sum "$ROOT/tools/ch3_baselines_param_matched.py" | awk '{print $1}')
if [ -n "${EXPECT_SHA:-}" ] && [ "$ACTUAL_SHA" != "$EXPECT_SHA" ]; then
  echo "GATE_FAIL 脚本 SHA-256 不匹配：远端 $ACTUAL_SHA"
  exit 7
fi
echo "GATE_OK 脚本 SHA-256=$ACTUAL_SHA"
for f in X23 y23 I23 M23 E23 T23 X24 y24 s24 d24 I24 M24; do
  [ -f "$ROOT/runs/diagnostics/dijk-repro/cache/$f.npy" ] || { echo "GATE_FAIL 缺缓存 $f.npy"; exit 6; }
done

# 门禁三：不得覆盖已完成的发表配置版结果目录
if [ "$OUT" = "$ROOT/runs/diagnostics/ch3-baselines-full" ]; then
  echo "GATE_FAIL 输出目录指向已完成的发表配置版，拒绝启动"
  exit 8
fi
if [ -f "$OUT/neural_results.json" ]; then
  echo "GATE_FAIL 本轮结果已存在，拒绝覆盖：$OUT/neural_results.json"
  exit 9
fi

# 门禁四：剩余显存足够（不与 ch3_backbone_protocolA.py 抢到溢出）
FREE_MIB=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
FREE_GIB=$(awk -v m="$FREE_MIB" 'BEGIN{printf "%.2f", m/1024}')
echo "GPU 剩余显存 ${FREE_GIB} GiB，本进程保守峰值 ${NEED_GPU_GIB} GiB"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
if awk -v f="$FREE_GIB" -v n="$NEED_GPU_GIB" 'BEGIN{exit (f>=n)?0:1}'; then
  echo "GATE_OK 显存余量充足"
else
  echo "GATE_FAIL 显存不足：剩余 ${FREE_GIB} GiB < 需要 ${NEED_GPU_GIB} GiB"
  exit 4
fi

# 门禁五：内存准入（沿用项目单入口脚本；已知 protocolA 在跑，显式放行并发）
ALLOW_CONCURRENT=1 bash "$ROOT/tools/memory_admission_gate.sh" "$NEED_RAM_GIB" \
  ch3-baselines-param-matched || { echo "GATE_FAIL 内存准入未通过"; exit 10; }

cd "$ROOT" || exit 1
nohup setsid uv run --no-sync python tools/ch3_baselines_param_matched.py > "$LOG" 2>&1 &
echo $! > "$PIDF"
sleep 25
echo "GATE_OK 已启动 pid=$(cat "$PIDF")"
echo "--- 日志前 30 行 ---"
head -30 "$LOG"
