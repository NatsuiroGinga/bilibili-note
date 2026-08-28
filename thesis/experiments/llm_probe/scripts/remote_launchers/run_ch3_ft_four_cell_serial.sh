#!/usr/bin/env bash
# CEM-BER 四格串行守护：按 C00 → C10 → C01 → C11 顺序跑完，中断后自动续训。
#
# 设计依据：服务器按周期开关机，2026-08-28 已发生一次关机导致 C10 第 13/20 轮作废。
# 检查点 schema v2 起 mechanism_state 已纳入调度器游标、EntityMemoryState（稀疏）、
# CVaR 阈值与 numpy 采样 RNG，z1/z2 臂支持原子续训，故本脚本可安全地对任一臂重入。
#
# 幂等：已 finished 且 exit_code=0 的臂直接跳过；有 inflight.pt 的臂用 --resume 续；
# 都没有则全新启动。重复执行本脚本不会重跑已完成的臂。
set -uo pipefail

ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
cd "$ROOT" || exit 2
RUNS="$ROOT/runs/diagnostics"

# 顺序固定：C00 是基线，三个机制臂都要与它比；C11 放最后，因为它同时依赖两个机制。
CELLS=(
  "ch3-ft-c00-dual-selection-cuda-formal-v1:run_ch3_ft_c00_dual_selection_cuda_formal_v1.sh"
  "ch3-ft-c10-entity-memory-cuda-formal-v1:run_ch3_ft_c10_entity_memory_cuda_formal_v1.sh"
  "ch3-ft-c01-entity-ranking-cuda-formal-v1:run_ch3_ft_c01_entity_ranking_cuda_formal_v1.sh"
  "ch3-ft-c11-cem-ber-cuda-formal-v1:run_ch3_ft_c11_cem_ber_cuda_formal_v1.sh"
)

stamp() { date '+%Y-%m-%d %H:%M:%S'; }

cell_finished() {
  local status="$1/status.json"
  [ -f "$status" ] || return 1
  grep -q '"state": *"finished"' "$status" && grep -q '"exit_code": *0' "$status"
}

for entry in "${CELLS[@]}"; do
  run_id="${entry%%:*}"
  launcher="${entry##*:}"
  out="$RUNS/$run_id"

  if cell_finished "$out"; then
    echo "[$(stamp)] 跳过 $run_id：已完成且 exit_code=0"
    continue
  fi

  mkdir -p "$out"
  if [ -f "$out/checkpoints/inflight.pt" ]; then
    mode="--run --resume"
    echo "[$(stamp)] 续训 $run_id：发现 inflight.pt"
  else
    mode="--run"
    echo "[$(stamp)] 启动 $run_id：全新运行"
  fi

  # shellcheck disable=SC2086
  bash "scripts/remote_launchers/$launcher" $mode >> "$out/launch.log" 2>&1
  code=$?
  echo "[$(stamp)] $run_id 退出码=$code"

  if [ "$code" -ne 0 ]; then
    echo "[$(stamp)] $run_id 非零退出，停止后续臂以免在错误状态上继续" >&2
    exit "$code"
  fi
done

echo "[$(stamp)] 四格全部完成"
