#!/usr/bin/env bash
set -eo pipefail
source ~/.bashrc >/dev/null 2>&1
set -u
if [[ $# -ne 1 ]]; then
  printf '用法：%s <受控参数JSON>\n' "$0" >&2
  exit 2
fi
if [[ "$PWD" != "/root/autodl-tmp/thesis/experiments/llm_probe" ]]; then
  printf '必须从服务器项目根运行\n' >&2
  exit 2
fi
export CUDA_VISIBLE_DEVICES=""
export SWANLAB_MODE=disabled
exec uv run --no-sync python -m flow_probe.r2_ns3_protocol_dynamics_v2_parallel_runner --params "$1"
