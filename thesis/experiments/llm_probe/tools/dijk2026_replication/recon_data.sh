#!/usr/bin/env bash
# 只读勘察 LSPR23/LSPR24 原始数据
set -uo pipefail
ROOT=/root/autodl-tmp/thesis/experiments/llm_probe

echo "=== data/raw 列表 ==="
ls -la $ROOT/data/raw/ 2>/dev/null
echo "--- lspr23-v1 ---"
ls -la $ROOT/data/raw/lspr23-v1/ 2>/dev/null
echo "--- data 顶层 ---"
ls -la $ROOT/data/ 2>/dev/null

echo "=== 全部 >100M 的数据文件 ==="
find $ROOT/data $ROOT/runs/data-raw $ROOT/runs/data-frozen $ROOT/runs/data-downloads -maxdepth 4 -type f -size +100M -exec ls -la {} \; 2>/dev/null | head -40

echo "=== lspr24 parquet 定位 ==="
find $ROOT -maxdepth 6 -type f -name '*.parquet' -size +100M -exec ls -la {} \; 2>/dev/null | head -20

echo "=== runs/data-prepared 目录 ==="
ls -la $ROOT/runs/data-prepared/ 2>/dev/null | head -30

echo "=== uv 与依赖 ==="
cd $ROOT && ls tools/env/activate.sh
source $ROOT/tools/env/activate.sh >/dev/null 2>&1
which uv
uv run --no-sync python -c "import xgboost,pyarrow,numpy,sklearn;print('xgboost',xgboost.__version__);print('pyarrow',pyarrow.__version__);print('numpy',numpy.__version__);print('sklearn',sklearn.__version__)"
echo "RECON_DATA_DONE"
