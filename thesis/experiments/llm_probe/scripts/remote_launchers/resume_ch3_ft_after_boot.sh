#!/usr/bin/env bash
# 服务器开机后的四格接续单入口：把「先推修复、再启训练、同时开回传」三步固化为一条命令。
#
# 存在理由（2026-08-31）：服务器按周期开关机，每次开机都要按固定顺序做三件事，
# 顺序错一步就要重跑整臂。2026-08-31 的实测教训是 C01 因排序阶段显存溢出在首步崩溃，
# 修复提交 3344e0f 当时未能推上服务器（推送时连接中断），若开机后直接启动守护脚本，
# C11 会以同样方式崩掉。把顺序写进脚本，不再依赖操作者记得。
#
# 用法（本机项目根 thesis/experiments/llm_probe 下）：
#   GPU_SSH="ssh -p <端口> -o StrictHostKeyChecking=no root@<主机>" \
#   GPU_PWD="<密码>" \
#   bash scripts/remote_launchers/resume_ch3_ft_after_boot.sh
#
# 凭据只从环境变量继承，脚本不落盘、不打印、不写日志。
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_ROOT="$(cd "$HERE/../.." && pwd)"
REMOTE_ROOT="${REMOTE_PROJECT_ROOT:-/root/autodl-tmp/thesis/experiments/llm_probe}"

# 必须先推送的文件：排序阶段梯度检查点修复（提交 3344e0f）。
# 两条前向路径都在这个文件里，C01 已验证有效，C11 依赖同一修复。
PUSH_FILES=(
  tools/ch3_ft_c00_dual_selection.py
  tools/ch3_ft_emit_four_cell_summary.py
  scripts/remote_launchers/run_ch3_ft_four_cell_serial.sh
)

stamp() { date '+%Y-%m-%d %H:%M:%S'; }

if [ -z "${GPU_SSH:-}" ] || [ -z "${GPU_PWD:-}" ]; then
  echo "[$(stamp)] 缺少 GPU_SSH 或 GPU_PWD 环境变量，停止。" >&2
  exit 2
fi

remote_host="${GPU_SSH##* }"
remote_shell="${GPU_SSH% *}"

run_remote() {
  RSH_CMD="$1" expect -c '
    set timeout 600
    set ssh_command [split $env(GPU_SSH) " "]
    set remote_host [lindex $ssh_command end]
    set opts [lrange $ssh_command 0 end-1]
    eval spawn $opts {$remote_host} {$env(RSH_CMD)}
    expect {
      -re {(?i)are you sure you want to continue connecting} { send -- "yes\r"; exp_continue }
      -re {(?i)password:} { send -- "$env(GPU_PWD)\r"; exp_continue }
      eof
    }
    set result [wait]
    exit [lindex $result 3]
  '
}

push_file() {
  RSYNC_SRC="$1" RSYNC_DST="$2" expect -c '
    set timeout 900
    set ssh_command [split $env(GPU_SSH) " "]
    set remote_host [lindex $ssh_command end]
    set remote_shell [join [lrange $ssh_command 0 end-1] " "]
    eval spawn rsync -rt -e {$remote_shell} {$env(RSYNC_SRC)} {$remote_host:$env(RSYNC_DST)}
    expect {
      -re {(?i)are you sure you want to continue connecting} { send -- "yes\r"; exp_continue }
      -re {(?i)password:} { send -- "$env(GPU_PWD)\r"; exp_continue }
      eof
    }
    set result [wait]
    exit [lindex $result 3]
  '
}

# ---- 步骤 0：可达性 ----
host_only="${remote_host#*@}"
port="$(printf '%s' "$remote_shell" | sed -n 's/.*-p \([0-9]\{1,\}\).*/\1/p')"
if [ -n "$port" ]; then
  if ! nc -z -w 5 "$host_only" "$port" >/dev/null 2>&1; then
    echo "[$(stamp)] 服务器 $host_only 端口不可达，未开机或端口已变，停止。" >&2
    exit 3
  fi
  echo "[$(stamp)] 步骤 0：端口可达"
fi

# ---- 步骤 1：推送修复（顺序不可颠倒）----
echo "[$(stamp)] 步骤 1：推送 OOM 修复与汇总脚本"
for f in "${PUSH_FILES[@]}"; do
  if push_file "$LOCAL_ROOT/$f" "$REMOTE_ROOT/$(dirname "$f")/" >/dev/null 2>&1; then
    echo "  已推送 $f"
  else
    echo "[$(stamp)] 推送 $f 失败，停止——未修复的 C11 会在首步显存溢出" >&2
    exit 4
  fi
done

# ---- 步骤 2：只读核验环境 ----
echo "[$(stamp)] 步骤 2：只读核验"
run_remote "cd $REMOTE_ROOT && df -h . | tail -1 && nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader && ls runs/diagnostics/ch3-ft-c11-cem-ber-cuda-formal-v1/checkpoints/ 2>/dev/null | head -3" 2>&1 | rg -v 'password|spawn' || true

# ---- 步骤 3：启动四格守护（幂等，自动跳过已完成的三臂）----
echo "[$(stamp)] 步骤 3：启动四格守护"
run_remote "cd $REMOTE_ROOT && setsid nohup bash scripts/remote_launchers/run_ch3_ft_four_cell_serial.sh > runs/four-cell-serial.log 2>&1 < /dev/null & sleep 3; echo 已启动" >/dev/null 2>&1 \
  && echo "  守护已启动，C00/C10/C01 会被跳过，只跑 C11" \
  || { echo "[$(stamp)] 守护启动失败" >&2; exit 5; }

# ---- 步骤 4：本机回传守护 ----
echo "[$(stamp)] 步骤 4：启动本机回传守护"
if pgrep -f watch_and_pull_ch3_ft >/dev/null 2>&1; then
  echo "  回传守护已在运行，跳过"
else
  mkdir -p "$LOCAL_ROOT/runs"
  nohup bash "$HERE/watch_and_pull_ch3_ft.sh" > "$LOCAL_ROOT/runs/watch-and-pull.log" 2>&1 &
  echo "  回传守护已启动（PID $!），每 5 分钟拉一次，臂完成自动全量备份"
fi

echo
echo "[$(stamp)] 接续完成。四格跑完后的下一步（需人工确认判据后执行）："
echo "  1. uv run --no-sync python tools/ch3_ft_lspr24_descriptive_eval.py --dry-run"
echo "  2. 判据通过后去掉 --dry-run 出目标年读数"
echo "  3. python tools/ch3_build_metrics_table.py --config configs/ch3-metrics-table-sources-v1.json --out <目录>"
echo "  4. results-analysis → results-report → 按论断台账填正文"
