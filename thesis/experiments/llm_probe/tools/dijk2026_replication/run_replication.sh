#!/usr/bin/env bash
# 服务器端单入口：内存准入门禁 → Dijk 2026 XGBoost 跨年度复现全流程。
#
# 用法（远程）：
#   bash tools/dijk2026_replication/run_replication.sh "<阶段列表>"
# 阶段列表默认 config,train,score,label,metrics
set -uo pipefail

ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
RUN_NAME=dijk2026-xgboost-replication-v1
RUN_ROOT="$ROOT/runs/candidates/$RUN_NAME"
STAGES="${1:-config,train,score,label,metrics}"

# 峰值内存估算（GiB），算式见下：
#   LSPR23 特征矩阵      上界 2.0e7 行 × 83 列 × 4 B = 6.64 GB（np.empty 惰性占页，实际按行数增长）
#   训练/验证切分副本    1.0 倍矩阵大小 = 6.64 GB
#   Arrow 批次与索引缓冲 约 1.5 GB
#   XGBoost 主机侧临时   约 1.5 GB
#   合计上界             约 16.3 GB → 申报 16 GiB
ESTIMATED_PEAK_GIB=16

cd "$ROOT" || exit 1
mkdir -p "$RUN_ROOT/logs"

echo "[启动器] $(date -Is) 运行=$RUN_NAME 阶段=$STAGES"
echo "[启动器] 峰值估算=${ESTIMATED_PEAK_GIB} GiB（算式见脚本注释）"

if ! bash tools/memory_admission_gate.sh "$ESTIMATED_PEAK_GIB" "$RUN_NAME"; then
  echo "[启动器] 内存准入门禁未通过，停止启动"
  exit 10
fi

# shellcheck disable=SC1091
source "$ROOT/tools/env/activate.sh" >/dev/null 2>&1

echo "[启动器] $(date -Is) 依赖解析与入口检查开始"
uv run --no-sync python -c "import xgboost, pyarrow, sklearn, numpy; print('deps ok', xgboost.__version__)" || exit 11
uv run --no-sync python -m py_compile \
  tools/dijk2026_replication/dijk_fields.py \
  tools/dijk2026_replication/dijk_ingest.py \
  tools/dijk2026_replication/replicate_dijk_xgboost.py || exit 12
echo "[启动器] $(date -Is) 入口检查通过，进入正式运行"

uv run --no-sync python -u tools/dijk2026_replication/replicate_dijk_xgboost.py --stages "$STAGES"
STATUS=$?
echo "[启动器] $(date -Is) 主流程退出码=$STATUS"
exit $STATUS
