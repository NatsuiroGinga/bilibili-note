#!/bin/bash
# 等 C00 v2 正常结束后串行启动 C01 v2。
#
# 存在理由：两格显存之和超过单卡容量（C00 实测 23.7 GiB，C01 修复后峰值约 15.2 GiB，
# 合计 38.9 GiB > 31.36 GiB），必须串行；而 C00 需约 1.5 小时，超过本机会话的后台任务时长，
# 故把等待逻辑放到服务器端，不依赖任何本机会话存活。
#
# 安全性：只在 C00 的 status.json 明确为 finished 且 exit_code 为 0 时才启动 C01。
# C00 失败或状态异常时本脚本退出且不启动 C01，把失败留给人工判断。

set -o pipefail

ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
C00_STATUS="$ROOT/runs/diagnostics/ch3-ft-c00-bare-eager-formal-v2/status.json"
C01_CONFIG=configs/ch3-ft-c01-ranking-eager-formal-v2.json
C01_LOG="$ROOT/logs/c01-ranking-eager-formal-v2.log"
GUARD_LOG="$ROOT/logs/c01-after-c00-guard.log"

MAX_WAIT_SECONDS=$((6 * 3600))
POLL_SECONDS=60

cd "$ROOT" || exit 2
mkdir -p "$ROOT/logs"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$GUARD_LOG"
}

log "守护启动：等待 C00 v2 结束后启动 C01 v2"

waited=0
while [ "$waited" -lt "$MAX_WAIT_SECONDS" ]; do
  if [ -f "$C00_STATUS" ]; then
    state=$(tr -d ' \n' < "$C00_STATUS" | grep -o '"state":"[a-z]*"' | head -1)
    code=$(tr -d ' \n' < "$C00_STATUS" | grep -o '"exit_code":[0-9]*' | head -1)
    if [ "$state" = '"state":"finished"' ] && [ "$code" = '"exit_code":0' ]; then
      log "C00 v2 已完成且退出码为 0，开始启动 C01 v2"
      break
    fi
    if [ "$state" = '"state":"failed"' ]; then
      log "C00 v2 状态为 failed，按设计不启动 C01，守护退出"
      exit 3
    fi
  fi
  sleep "$POLL_SECONDS"
  waited=$((waited + POLL_SECONDS))
done

if [ "$waited" -ge "$MAX_WAIT_SECONDS" ]; then
  log "等待超过 ${MAX_WAIT_SECONDS} 秒仍未见 C00 v2 完成，守护退出，不启动 C01"
  exit 4
fi

# shellcheck disable=SC1091
source tools/env/activate.sh > /dev/null 2>&1

log "执行 C01 v2：$C01_CONFIG"
uv run --no-sync python tools/ch3_ft_c00_dual_selection.py --config "$C01_CONFIG" --run \
  >> "$C01_LOG" 2>&1
status=$?
log "C01 v2 结束，退出码 $status"
exit "$status"
