#!/bin/bash
# 唯一训练启动入口：启动远程训练的**同时**起本机回传守护，两者不可分离。
#
# 存在理由（2026-09-01）：恢复卡第 88 行早就记载了回传守护 watch_and_pull_ch3_ft.sh，
# 它正是为「服务器保存唯一副本」这一已发生过的事故而建。但它需要人记得单独启动，
# 结果 2026-09-01 水库筛选臂整轮跑完后服务器关机，本机 0 个制品——同类事故第二次发生。
# 修法不是「下次记得起」，而是把回传并入启动动作本身：训练起来了，回传就一定在跑。
#
# 用法：
#   GPU_SSH_ACTIVE=... GPU_PWD_ACTIVE=... \
#   bash scripts/remote_launchers/launch_run_with_pull.sh <配置相对路径> <run_id> [运行参数] [Python入口]
#
# 例：
#   bash scripts/remote_launchers/launch_run_with_pull.sh \
#     configs/ch3-ft-c00-bare-eager-formal-v2.json ch3-ft-c00-bare-eager-formal-v2
#
# 凭据只从环境变量取，绝不写入文件、日志或参数。

set -euo pipefail

CONFIG_PATH="${1:-}"
RUN_ID="${2:-}"
# 第三个参数透传给训练入口，用于 --resume 等模式。默认 --run。
RUN_MODE="${3:---run}"
# 第四个参数允许同一启动与回传入口服务其他训练工具；省略时保持历史行为。
PYTHON_ENTRYPOINT="${4:-tools/ch3_ft_c00_dual_selection.py}"
PULL_INTERVAL_SECONDS="${PULL_INTERVAL_SECONDS:-300}"
PULL_MAX_SIZE="${PULL_MAX_SIZE:-5m}"

if [ -z "$CONFIG_PATH" ] || [ -z "$RUN_ID" ]; then
  echo "用法：launch_run_with_pull.sh <配置相对路径> <run_id> [运行参数] [Python入口]" >&2
  exit 2
fi
for name in GPU_SSH_ACTIVE GPU_PWD_ACTIVE; do
  if [ -z "${!name}" ]; then
    echo "缺少必需环境变量：$name" >&2
    exit 2
  fi
done

LOCAL_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
REMOTE_RUN_DIR="$REMOTE_ROOT/runs/diagnostics/$RUN_ID"
LOCAL_RUN_DIR="$LOCAL_ROOT/runs/diagnostics/$RUN_ID"
PULL_LOG="$LOCAL_ROOT/runs/diagnostics/$RUN_ID.pull.log"

cd "$LOCAL_ROOT" || exit 2
mkdir -p "$LOCAL_RUN_DIR"

echo "[1/2] 在服务器启动训练：$RUN_ID"
expect tools/remote_exec/gpu_env_quiet.exp \
  "cd $REMOTE_ROOT && mkdir -p logs runs/diagnostics/$RUN_ID && touch logs/$RUN_ID.log && if [ -e runs/diagnostics/$RUN_ID/run.log ]; then [ logs/$RUN_ID.log -ef runs/diagnostics/$RUN_ID/run.log ]; else ln logs/$RUN_ID.log runs/diagnostics/$RUN_ID/run.log; fi && source tools/env/activate.sh >/dev/null 2>&1 && setsid -f nohup uv run --no-sync python \"$PYTHON_ENTRYPOINT\" --config \"$CONFIG_PATH\" $RUN_MODE < /dev/null >> logs/$RUN_ID.log 2>&1; echo __CODEX_RESULT_BEGIN__; echo launched; echo __CODEX_RESULT_END__" \
  2>/dev/null | tail -2

# 回传守护：与训练同时起，脱离当前会话，会话结束后继续存活。
# 只拉轻量制品（默认 5 MiB 以下），避免每轮把大检查点拖回来；
# 训练结束后再拉一次全量由人工或后续步骤触发。
echo "[2/2] 起本机回传守护：每 ${PULL_INTERVAL_SECONDS} 秒一次，单文件上限 ${PULL_MAX_SIZE}"
# 用 nohup 而非 setsid：本机是 macOS，没有 setsid（Linux 命令）。
# nohup 忽略 HUP 信号，配合 & 与后面的 disown 即可让守护脱离当前 shell 存活。
nohup bash -c '
  while true; do
    GPU_SSH_ACTIVE="'"$GPU_SSH_ACTIVE"'" GPU_PWD_ACTIVE="'"$GPU_PWD_ACTIVE"'" GPU_RSYNC_MAX_SIZE="'"$PULL_MAX_SIZE"'" \
      expect '"$LOCAL_ROOT"'/tools/remote_exec/gpu_rsync_pull.exp \
      "'"$REMOTE_RUN_DIR"'/" "'"$LOCAL_RUN_DIR"'/" >> "'"$PULL_LOG"'" 2>&1
    printf "%s 轮询回传完成\n" "$(date "+%Y-%m-%d %H:%M:%S")" >> "'"$PULL_LOG"'"
    sleep '"$PULL_INTERVAL_SECONDS"'
  done
' < /dev/null >> "$PULL_LOG" 2>&1 &

PULL_PID=$!
disown 2>/dev/null || true

# 立刻核验守护真的活着——不核验就等于没起。历史教训：setsid 在 macOS 不存在，
# 而 bash -n 只查语法不查命令是否可用，静默失败会让"回传已起"变成假象。
sleep 2
if kill -0 "$PULL_PID" 2>/dev/null; then
  echo "回传守护 PID=$PULL_PID 已存活，日志：$PULL_LOG"
else
  echo "回传守护启动失败，请查看 $PULL_LOG" >&2
  exit 5
fi
echo "本机运行目录：$LOCAL_RUN_DIR"
