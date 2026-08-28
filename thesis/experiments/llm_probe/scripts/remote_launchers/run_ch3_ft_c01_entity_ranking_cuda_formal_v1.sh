#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
TOOL="tools/ch3_ft_c00_dual_selection.py"
CONFIG="configs/ch3-ft-c01-entity-ranking-cuda-formal-v1.json"

cd "${ROOT}"
source tools/env/activate.sh
exec uv run --no-sync python "${TOOL}" --config "${CONFIG}" "$@"
