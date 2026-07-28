#!/usr/bin/env bash
set -eo pipefail

source ~/.bashrc
set -u

if [[ $# -ne 4 ]]; then
  printf '用法：%s <ns-3根目录> <配置清单> <唯一输出目录> <运行名称>\n' "$0" >&2
  exit 2
fi

NS3_ROOT=$1
MANIFEST_PATH=$2
OUTPUT_DIR=$3
RUN_NAME=$4
PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

export PATH="/root/autodl-tmp/thesis/ns3/.tools/ns3-cmake-3.25.2/bin:${PATH}"
cd "$PROJECT_ROOT"

exec uv run --no-sync python -m flow_probe.ns3_domain_experiment \
  --ns3-root "$NS3_ROOT" \
  --source-path "$PROJECT_ROOT/ns3/domain_randomized_queue_scenario.cc" \
  --manifest-path "$MANIFEST_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --run-name "$RUN_NAME"
