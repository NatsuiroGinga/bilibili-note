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
#   bash scripts/remote_launchers/launch_run_with_pull.sh <配置相对路径> <run_id>
#
# 例：
#   bash scripts/remote_launchers/launch_run_with_pull.sh \
#     configs/ch3-ft-c00-bare-eager-formal-v2.json ch3-ft-c00-bare-eager-formal-v2
#
# 凭据只从环境变量取，绝不写入文件、日志或参数。

set -o pipefail

CONFIG_PATH="$1"
RUN_ID="$2"
PULL_INTERVAL_SECONDS="${PULL_INTERVAL_SECONDS:-300}"
PULL_MAX_SIZE="${PULL_MAX_SIZE:-5m}"

if [ -z "$CONFIG_PATH" ] || [ -z "$RUN_ID" ]; then
  echo "用法：launch_run_with_pull.sh <配置相对路径> <run_id>" >&2
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
  "cd $REMOTE_ROOT && mkdir -p logs runs/diagnostics/$RUN_ID && source tools/env/activate.sh >/dev/null 2>&1 && setsid nohup uv run --no-sync python tools/ch3_ft_c00_dual_selection.py --config $CONFIG_PATH --run < /dev/null > logs/$RUN_ID.log 2>&1 & echo __CODEX_RESULT_BEGIN__; echo launched; echo __CODEX_RESULT_END__" \
  2>/dev/null | tail -2

# 回传守护：与训练同时起，脱离当前会话，会话结束后继续存活。
# 只拉轻量制品（默认 5 MiB 以下），避免每轮把大检查点拖回来；
# 训练结束后再拉一次全量由人工或后续步骤触发。
echo "[2/2] 起本机回传守护：每 ${PULL_INTERVAL_SECONDS} 秒一次，单文件上限 ${PULL_MAX_SIZE}"
setsid nohup bash -c '
  while true; do
    GPU_SSH_ACTIVE="'"$GPU_SSH_ACTIVE"'" GPU_PWD_ACTIVE="'"$GPU_PWD_ACTIVE"'" \
      expect '"$LOCAL_ROOT"'/tools/remote_exec/gpu_rsync_pull.exp \
      "'"$REMOTE_RUN_DIR"'/" "'"$LOCAL_RUN_DIR"'/" >> "'"$PULL_LOG"'" 2>&1
    printf "%s 轮询回传完成\n" "$(date "+%Y-%m-%d %H:%M:%S")" >> "'"$PULL_LOG"'"
    sleep '"$PULL_INTERVAL_SECONDS"'
  done
' < /dev/null >> "$PULL_LOG" 2>&1 &

echo "回传守护 PID=$!，日志：$PULL_LOG"
echo "本机运行目录：$LOCAL_RUN_DIR"
