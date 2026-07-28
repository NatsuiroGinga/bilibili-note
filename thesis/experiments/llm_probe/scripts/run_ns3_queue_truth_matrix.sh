#!/usr/bin/env bash
set -eo pipefail

source ~/.bashrc
set -u

if [[ $# -lt 3 || $# -gt 5 ]]; then
  printf '用法：%s <ns-3根目录> <唯一输出目录> <运行名称> [随机种子列表] [场景列表]\n' "$0" >&2
  exit 2
fi

NS3_ROOT=$1
OUTPUT_DIR=$2
RUN_NAME=$3
SEEDS=${4:-42,43,44}
SCENARIOS=${5:-benign-low,benign-high,benign-capacity-shift,benign-random-loss,dos-udp-medium,dos-udp-high,dos-udp-capacity-shift}
PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

export PATH="/root/autodl-tmp/thesis/ns3/.tools/ns3-cmake-3.25.2/bin:${PATH}"
cd "$PROJECT_ROOT"

exec uv run --no-sync python -m flow_probe.ns3_experiment \
  --ns3-root "$NS3_ROOT" \
  --source-path "$PROJECT_ROOT/ns3/queue_truth_scenario.cc" \
  --output-dir "$OUTPUT_DIR" \
  --run-name "$RUN_NAME" \
  --seeds "$SEEDS" \
  --scenarios "$SCENARIOS"
