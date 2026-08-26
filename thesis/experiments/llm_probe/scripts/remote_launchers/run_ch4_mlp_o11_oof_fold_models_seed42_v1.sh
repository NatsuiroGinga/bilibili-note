#!/usr/bin/env bash
# 第四章 D0：全容量 MLP O11 三折折外评分模型物化启动器
# 用法：bash run_ch4_mlp_o11_oof_fold_models_seed42_v1.sh [verify|run|resume|fold <0|1|2>]
set -Eeuo pipefail

P=/root/autodl-tmp/thesis/experiments/llm_probe
CONFIG="$P/configs/ch4-mlp-o11-oof-fold-models-seed42-v1.json"
TOOL="$P/tools/ch4_mlp_o11_oof_fold_models.py"
RUN_ROOT="$P/runs/diagnostics/ch4-mlp-o11-oof-fold-models-seed42-v1"
LOG_DIR="$RUN_ROOT/logs"

cd "$P"
set +u
source tools/env/activate.sh
set -u
export PYTHONPATH="$P/tools:${PYTHONPATH:-}"

mkdir -p "$LOG_DIR"

# 披露性资源快照（只打印，不阻断）
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null \
  | sed 's/^/[disclosure] gpu /' || true
df -h /root/autodl-tmp | tail -1 | sed 's/^/[disclosure] disk /' || true

MODE="${1:-run}"
STAMP="$(date +%Y%m%d-%H%M%S)"

case "$MODE" in
  verify)
    uv run --no-sync python "$TOOL" --config "$CONFIG" --validate-config
    ;;
  run|resume)
    EXTRA=""
    if [ "$MODE" = "resume" ]; then EXTRA="--resume"; fi
    LOG="$LOG_DIR/${MODE}-${STAMP}.log"
    set +e
    uv run --no-sync python "$TOOL" --config "$CONFIG" $EXTRA 2>&1 | tee "$LOG"
    STATUS=("${PIPESTATUS[@]}")
    set -e
    echo "${STATUS[0]}" > "$LOG.command-exit-code.txt"
    echo "${STATUS[1]}" > "$LOG.tee-exit-code.txt"
    exit "${STATUS[0]}"
    ;;
  fold)
    K="${2:?用法：fold <0|1|2>}"
    LOG="$LOG_DIR/fold${K}-${STAMP}.log"
    set +e
    uv run --no-sync python "$TOOL" --config "$CONFIG" --fold "$K" --resume 2>&1 | tee "$LOG"
    STATUS=("${PIPESTATUS[@]}")
    set -e
    echo "${STATUS[0]}" > "$LOG.command-exit-code.txt"
    echo "${STATUS[1]}" > "$LOG.tee-exit-code.txt"
    exit "${STATUS[0]}"
    ;;
  *)
    printf '%s\n' "用法：bash $0 [verify|run|resume|fold <0|1|2>]" >&2
    exit 64
    ;;
esac
