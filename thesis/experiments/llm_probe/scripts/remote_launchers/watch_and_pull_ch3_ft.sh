#!/usr/bin/env bash
# 本机侧回传守护：周期性把服务器上的四格轻量制品拉回本机，并在每臂完成时拉全量。
#
# 存在理由（2026-08-29）：服务器按周期开关机且随时可能回收，制品若只存在服务器上，
# 关机即失去证据。此前「记得回传」是人工动作，两次关机都没做到。本脚本把它变成进程行为。
#
# 轻量轮（默认每 5 分钟）：status.json、日志、收据、四格汇总，KiB 量级，可高频拉。
# 全量轮：某臂 status.json 出现 finished 且 exit_code=0 时，对该臂拉一次含检查点的全量，
#         之后不再重复拉该臂（用 .pulled-full 标记），避免反复传输 850 MiB 的记忆状态。
#
# 凭据只从环境变量 GPU_SSH / GPU_PWD 继承，脚本不落盘、不打印、不写日志。
#
# 用法（本机项目根 thesis/experiments/llm_probe 下）：
#   GPU_SSH="..." GPU_PWD="..." nohup bash scripts/remote_launchers/watch_and_pull_ch3_ft.sh \
#     > runs/watch-and-pull.log 2>&1 &
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_ROOT="$(cd "$HERE/../.." && pwd)"
PULL="$HERE/pull_ch3_ft_four_cell_artifacts.sh"
INTERVAL="${WATCH_INTERVAL_SECONDS:-300}"
MAX_ROUNDS="${WATCH_MAX_ROUNDS:-288}"   # 288 × 5 分钟 = 24 小时上界，防止无人值守时无限运行

RUN_IDS=(
  ch3-ft-c00-dual-selection-cuda-formal-v1
  ch3-ft-c10-entity-memory-cuda-formal-v1
  ch3-ft-c01-entity-ranking-cuda-formal-v1
  ch3-ft-c11-cem-ber-cuda-formal-v1
)

stamp() { date '+%Y-%m-%d %H:%M:%S'; }

if [ -z "${GPU_SSH:-}" ] || [ -z "${GPU_PWD:-}" ]; then
  echo "[$(stamp)] 缺少 GPU_SSH 或 GPU_PWD，停止。" >&2
  exit 2
fi

cell_finished_locally() {
  # 只看本机已回传的 status.json；不额外连服务器，避免每轮多开一次 SSH。
  local status="$LOCAL_ROOT/runs/diagnostics/$1/status.json"
  [ -f "$status" ] || return 1
  grep -q '"state": *"finished"' "$status" && grep -q '"exit_code": *0' "$status"
}

round=0
while [ "$round" -lt "$MAX_ROUNDS" ]; do
  round=$((round + 1))
  echo "[$(stamp)] 第 $round 轮：拉取轻量制品"
  bash "$PULL" --light 2>&1 | grep -vE '远端尚无该项' || true

  # 已完成且尚未全量回传过的臂，补一次含检查点的全量。
  for run_id in "${RUN_IDS[@]}"; do
    marker="$LOCAL_ROOT/runs/diagnostics/$run_id/.pulled-full"
    if cell_finished_locally "$run_id" && [ ! -f "$marker" ]; then
      echo "[$(stamp)] $run_id 已完成，拉取全量（含检查点）"
      if bash "$PULL" 2>&1 | tail -20; then
        date '+%Y-%m-%dT%H:%M:%S%z' > "$marker"
        echo "[$(stamp)] $run_id 全量回传完成，已标记"
      else
        echo "[$(stamp)] $run_id 全量回传未成功，下轮重试" >&2
      fi
    fi
  done

  # 四格全部完成即退出，不再空转。
  all_done=1
  for run_id in "${RUN_IDS[@]}"; do
    cell_finished_locally "$run_id" || all_done=0
  done
  if [ "$all_done" -eq 1 ]; then
    echo "[$(stamp)] 四格全部完成且已回传，守护退出"
    exit 0
  fi

  sleep "$INTERVAL"
done

echo "[$(stamp)] 达到轮次上界 $MAX_ROUNDS，守护退出（未必四格已完成）" >&2
exit 1
