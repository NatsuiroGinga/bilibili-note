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

# 轻量制品：收据、状态、配置、日志。训练进行中也可反复拉，体积以 KiB 计。
LIGHT_ITEMS=(
  status.json
  launch.log
  run.log
  config.json
  science-identity.json
  runtime-identity.json
  environment-receipt.json
  budget-receipt.json
  receipts
)

for run_id in "${RUN_IDS[@]}"; do
  local_dir="$LOCAL_ROOT/runs/diagnostics/$run_id"
  remote_dir="$REMOTE_ROOT/runs/diagnostics/$run_id"
  mkdir -p "$local_dir"

  for item in "${LIGHT_ITEMS[@]}"; do
    # 单项缺失是常态（未启动的臂没有收据），只记不停。
    if ! bash "$PULL_EXP" "$remote_dir/$item" "$local_dir/" >/dev/null 2>&1; then
      echo "[$(stamp)] $run_id：$item 未回传（可能尚未产生）"
    fi
  done

  if [ "$LIGHT" -eq 0 ]; then
    mkdir -p "$local_dir/checkpoints"
    if bash "$PULL_EXP" "$remote_dir/checkpoints/" "$local_dir/checkpoints/"; then
      echo "[$(stamp)] $run_id：检查点已回传"
    else
      echo "[$(stamp)] $run_id：检查点未回传（可能尚未产生）"
    fi
  fi
done

# 四格汇总本身也回传；它是数值的规范落点。
if ! bash "$PULL_EXP" "$REMOTE_ROOT/runs/diagnostics/ch3-ft-four-cell-summary.json" \
     "$LOCAL_ROOT/runs/diagnostics/" >/dev/null 2>&1; then
  echo "[$(stamp)] 四格汇总未回传（可能尚未生成，先在服务器运行 ch3_ft_emit_four_cell_summary.py）"
  failures=$((failures + 1))
fi

echo "[$(stamp)] 回传完成。本机四格读数："
if [ -f "$LOCAL_ROOT/runs/diagnostics/ch3-ft-four-cell-summary.json" ]; then
  "$LOCAL_ROOT/tools/env/activate.sh" >/dev/null 2>&1 || true
  uv run --no-sync python "$LOCAL_ROOT/tools/ch3_ft_emit_four_cell_summary.py" \
    --runs-root "$LOCAL_ROOT/runs/diagnostics" 2>&1 || \
    echo "[$(stamp)] 本机汇总重算失败，直接查看回传的 ch3-ft-four-cell-summary.json"
fi

exit "$failures"
