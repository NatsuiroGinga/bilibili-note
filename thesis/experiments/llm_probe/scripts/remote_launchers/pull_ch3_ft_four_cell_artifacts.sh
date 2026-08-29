#!/usr/bin/env bash
# 从服务器回传 CEM-BER 四格全部制品到本机，防止服务器回收或损毁导致证据丢失。
#
# 存在理由（2026-08-29）：此前四格制品只存在于服务器，本机零副本。两次关机后，
# compile 路径 C00 的实体 AP 数值取不回来；仓库规则本就要求「服务器不得保存唯一
# 代码、数据合同或结果副本」，此前未执行。
#
# 体积估算：FT 主干 924,283 参数，fp32 权重约 3.5 MiB；含优化器动量态的检查点约
# 11 MiB，每臂 selected-by-flow / selected-by-entity / inflight 三份约 33 MiB，
# 四格连同日志与收据约 130 MiB。全量回传成本远低于重跑一臂的 52 分钟。
#
# 用法（在本机项目根 thesis/experiments/llm_probe 下执行）：
#   GPU_SSH=... GPU_PWD=... bash scripts/remote_launchers/pull_ch3_ft_four_cell_artifacts.sh
#   加 --light 只拉收据、状态与日志，跳过检查点（约 2 MiB，适合训练进行中反复查看）
#
# 凭据只从环境变量读取，脚本不打印、不写盘、不进日志。
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_ROOT="$(cd "$HERE/../.." && pwd)"
REMOTE_ROOT="${REMOTE_PROJECT_ROOT:-/root/autodl-tmp/thesis/experiments/llm_probe}"
PULL_EXP="$HERE/gpu-rsync-pull.exp"

LIGHT=0
[ "${1:-}" = "--light" ] && LIGHT=1

RUN_IDS=(
  ch3-ft-c00-dual-selection-cuda-formal-v1
  ch3-ft-c10-entity-memory-cuda-formal-v1
  ch3-ft-c01-entity-ranking-cuda-formal-v1
  ch3-ft-c11-cem-ber-cuda-formal-v1
)

stamp() { date '+%Y-%m-%d %H:%M:%S'; }

if [ -z "${GPU_SSH:-}" ] || [ -z "${GPU_PWD:-}" ]; then
  echo "[$(stamp)] 缺少 GPU_SSH 或 GPU_PWD 环境变量，停止。" >&2
  exit 2
fi
if [ ! -f "$PULL_EXP" ]; then
  echo "[$(stamp)] 找不到回传脚本 $PULL_EXP" >&2
  exit 2
fi

failures=0

# 轻量轮一次性拉整个运行目录并按体积跳过检查点，而不是逐项拉。
# 2026-08-29 实测：逐项拉 4 臂 × 9 项 = 36 次 SSH 握手，单轮超过两分钟，
# 用作周期守护时每轮都超时。整目录一次 rsync 把握手降到 4 次，轻量轮回到秒级。
# 阈值 5m：收据与日志都在 KiB–百 KiB 量级，检查点最小的 3.7 MiB（选轮权重）
# 也要排除，最大的 810 MiB（含每实体记忆队列）更要排除，取 5m 有足够余量。
LIGHT_MAX_SIZE=5m

# 内联 expect 而非复用 gpu-rsync-pull.exp：后者接口固定为两个路径参数，
# 无法传 --exclude，而轻量轮必须排除 checkpoints 才能保持秒级。
# 不修改 gpu-rsync-pull.exp，因为其他工具依赖它的既有接口。
#
# 2026-08-29 事故留痕：本函数原先写成 bash "$PULL_EXP"，用 bash 去跑 Tcl 脚本，
# 一读 shebang 之后的语法就报错；错误被 >/dev/null 吞掉、退出码被管道掩盖，
# 于是每一次必然失败的回传都被报成「可能尚未产生」。三重掩盖使故障完全不可见。
# 教训：语法检查通过不等于能跑，交付前必须真实执行一次。
# 参数经环境变量传入：expect -c 不会把命令行尾随参数填进 argv
# （2026-08-29 实测：写成 expect -c 'script' a b 会在 lrange $argv 报错）。
# 轻量轮用 --max-size 而非 --exclude 路径：检查点是运行目录里唯一的大文件，
# 按体积过滤比维护路径清单更不易漏。
pull_rsync() {
  local label="$3"
  local out rc
  out="$(RSYNC_REMOTE="$1" RSYNC_DST="$2" RSYNC_MAXSIZE="${4:-}" expect -c '
    set timeout 1800
    set remote $env(RSYNC_REMOTE)
    set dst $env(RSYNC_DST)
    set maxsize $env(RSYNC_MAXSIZE)
    set ssh_command [split $env(GPU_SSH) " "]
    set remote_host [lindex $ssh_command end]
    set remote_shell [join [lrange $ssh_command 0 end-1] " "]
    set opts [list -rt --partial]
    if {$maxsize ne ""} { lappend opts --max-size=$maxsize }
    eval spawn rsync $opts -e {$remote_shell} {$remote_host:$remote} {$dst}
    expect {
      -re {(?i)are you sure you want to continue connecting} { send -- "yes\r"; exp_continue }
      -re {(?i)password:} { send -- "$env(GPU_PWD)\r"; exp_continue }
      eof
    }
    set result [wait]
    exit [lindex $result 3]
  ' 2>&1)"
  rc=$?
  [ "$rc" -eq 0 ] && return 0
  if printf '%s' "$out" | grep -qE 'No such file or directory|change_dir.*failed|link_stat.*failed'; then
    echo "[$(stamp)] $label：远端尚无该项，跳过"
    return 0
  fi
  echo "[$(stamp)] $label：回传失败（退出码 $rc）" >&2
  printf '%s\n' "$out" | grep -viE 'password|passwd' | tail -5 >&2
  return 1
}

for run_id in "${RUN_IDS[@]}"; do
  local_dir="$LOCAL_ROOT/runs/diagnostics/$run_id"
  remote_dir="$REMOTE_ROOT/runs/diagnostics/$run_id"
  mkdir -p "$local_dir"

  if [ "$LIGHT" -eq 1 ]; then
    pull_rsync "$remote_dir/" "$local_dir/" "$run_id（轻量）" "$LIGHT_MAX_SIZE" \
      || failures=$((failures + 1))
  else
    pull_rsync "$remote_dir/" "$local_dir/" "$run_id（全量）" || failures=$((failures + 1))
  fi
done

# 四格汇总本身也回传；它是数值的规范落点。
pull_rsync "$REMOTE_ROOT/runs/diagnostics/ch3-ft-four-cell-summary.json" \
  "$LOCAL_ROOT/runs/diagnostics/" "四格汇总" || failures=$((failures + 1))

echo "[$(stamp)] 回传完成。本机四格读数："
# 本机重算用 miniconda rwkv 环境：项目 .venv 无 NumPy/PyTorch（根 AGENTS.md 实验环境索引），
# 而汇总脚本只用标准库，任一可用解释器均可。activate.sh 必须 source 而非执行，
# 这里不需要它，直接选解释器更可靠。
LOCAL_PY=/opt/miniconda3/envs/rwkv/bin/python
[ -x "$LOCAL_PY" ] || LOCAL_PY=python3
"$LOCAL_PY" "$LOCAL_ROOT/tools/ch3_ft_emit_four_cell_summary.py" \
  --runs-root "$LOCAL_ROOT/runs/diagnostics" \
  || echo "[$(stamp)] 本机汇总重算失败，直接查看 runs/diagnostics/ch3-ft-four-cell-summary.json"

if [ "$failures" -gt 0 ]; then
  echo "[$(stamp)] 有 $failures 项回传失败，见上方 stderr" >&2
fi
exit "$failures"
