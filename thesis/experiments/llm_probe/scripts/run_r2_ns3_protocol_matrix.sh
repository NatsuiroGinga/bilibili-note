#!/usr/bin/env bash
set -eo pipefail

source ~/.bashrc >/dev/null 2>&1
set -u

if [[ $# -ne 1 ]]; then
  printf '用法：%s <受控参数JSON>\n' "$0" >&2
  exit 2
fi

PARAMS_PATH=$1
PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe

if [[ ! -f "$PARAMS_PATH" || -L "$PARAMS_PATH" ]]; then
  printf '受控参数必须是普通JSON文件：%s\n' "$PARAMS_PATH" >&2
  exit 2
fi
if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务器项目根运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi
if ! command -v uv >/dev/null 2>&1; then
  printf 'uv 不在 PATH，禁止启动任务05正式运行\n' >&2
  exit 2
fi
if ! command -v rg >/dev/null 2>&1; then
  printf 'rg 不在 PATH，禁止启动任务05正式运行\n' >&2
  exit 2
fi

export CUDA_VISIBLE_DEVICES=""
export SWANLAB_MODE=disabled
export PATH="/root/autodl-tmp/thesis/ns3/.tools/ns3-cmake-3.25.2/bin:${PATH}"

exec uv run --no-sync python -m flow_probe.r2_ns3_protocol_runner \
  --params "$PARAMS_PATH"
