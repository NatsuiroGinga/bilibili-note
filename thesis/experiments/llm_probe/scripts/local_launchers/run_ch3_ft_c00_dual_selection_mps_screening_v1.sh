#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON="/opt/miniconda3/envs/rwkv/bin/python"
TOOL="tools/ch3_ft_c00_dual_selection.py"
CONFIG="configs/ch3-ft-c00-dual-selection-mps-screening-v1.json"

cd "${ROOT}"
exec "${PYTHON}" "${TOOL}" --config "${CONFIG}" "$@"
