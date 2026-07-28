#!/usr/bin/env bash
set -eo pipefail

if [[ $# -ne 1 ]]; then
  printf '用法：%s <d1|d2|d3>\n' "$0" >&2
  exit 2
fi

SHORT_MODE="$1"
PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
MODEL="/root/autodl-tmp/thesis/models/Qwen3-1.7B"
DETECTION_ADAPTER="runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1/final_adapter"

case "$SHORT_MODE" in
  d1)
    EXPECTED_MODE="generation_only"
    TRAINING_DIR="runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d1-generation-only-full202-v1"
    CONFIG="configs/asymmetric_diagnostic_d1_seed42_eval300.yaml"
    OUTPUT_DIR="runs/asymmetric-physics-diagnostic-evaluation/qwen3-1.7b-seed42-d1-generation-only-eval300-v1"
    ;;
  d2)
    EXPECTED_MODE="physics_only"
    TRAINING_DIR="runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d2-physics-only-full202-v1"
    CONFIG="configs/asymmetric_diagnostic_d2_seed42_eval300.yaml"
    OUTPUT_DIR="runs/asymmetric-physics-diagnostic-evaluation/qwen3-1.7b-seed42-d2-physics-only-eval300-v1"
    ;;
  d3)
    EXPECTED_MODE="joint_warmup_cosine"
    TRAINING_DIR="runs/asymmetric-physics-diagnostics/qwen3-1.7b-seed42-d3-joint-warmup-cosine-full202-v1"
    CONFIG="configs/asymmetric_diagnostic_d3_seed42_eval300.yaml"
    OUTPUT_DIR="runs/asymmetric-physics-diagnostic-evaluation/qwen3-1.7b-seed42-d3-joint-warmup-cosine-eval300-v1"
    ;;
  *)
    printf '未知诊断模式：%s；只允许 d1、d2、d3\n' "$SHORT_MODE" >&2
    exit 2
    ;;
esac

TRAINING_SUMMARY="${TRAINING_DIR}/training_summary.json"
TASK_ADAPTER="${TRAINING_DIR}/final_private_adapter/physics_private"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"
if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi
if [[ -e "$OUTPUT_DIR" || -e "$LAUNCHER_LOG" ]]; then
  printf '评估目录或启动日志已存在，拒绝复用：%s\n' "$OUTPUT_DIR" >&2
  exit 2
fi
if [[ ! -f "$TRAINING_SUMMARY" || ! -d "$TASK_ADAPTER" ]]; then
  printf '固定训练摘要或私有适配器不存在：%s\n' "$TRAINING_DIR" >&2
  exit 2
fi

source /root/.bashrc
set -u
uv run --no-sync python -c '
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
expected_mode = sys.argv[2]
expected_adapter = Path(sys.argv[3]).resolve()
summary = json.loads(summary_path.read_text(encoding="utf-8"))
contract = summary.get("diagnostic_contract")
actual_mode = contract.get("mode") if isinstance(contract, dict) else None
if actual_mode != expected_mode:
    raise SystemExit(
        f"诊断模式不匹配：期望 {expected_mode}，实际 {actual_mode}"
    )
actual_adapter_raw = summary.get("private_adapter_path")
if not isinstance(actual_adapter_raw, str) or not actual_adapter_raw:
    raise SystemExit("训练摘要缺少 private_adapter_path")
actual_adapter = Path(actual_adapter_raw).resolve()
if actual_adapter != expected_adapter:
    raise SystemExit(
        f"私有适配器路径不匹配：期望 {expected_adapter}，实际 {actual_adapter}"
    )
' "$TRAINING_SUMMARY" "$EXPECTED_MODE" "$TASK_ADAPTER"
mkdir -p "$(dirname "$OUTPUT_DIR")"

set +e
{
  printf 'ASYMMETRIC_DIAGNOSTIC_EVAL=开始\n'
  printf 'SHORT_MODE=%s\n' "$SHORT_MODE"
  printf 'TASK_ADAPTER=%s\n' "$TASK_ADAPTER"
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  uv run --no-sync flow-probe-evaluate-hierarchical \
    --config "$CONFIG" \
    --model-path "$MODEL" \
    --adapter-path "$DETECTION_ADAPTER" \
    --task-adapter-path "$TASK_ADAPTER"
  status=$?
  printf 'ASYMMETRIC_DIAGNOSTIC_EVAL_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
