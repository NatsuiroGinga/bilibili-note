#!/usr/bin/env bash
set -eo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG="configs/s3_same_split_physics.yaml"
OUTPUT_DIR="runs/bounded-physics-conditioning-evaluation/qwen3-1.7b-s3-same-split-physics-test-v1"
LAUNCHER_LOG="${OUTPUT_DIR}.launcher.log"
S3_DIR="runs/physics-sparse/qwen3-1.7b-seed42-s3-anchor0-plus-one-fullphys202-v1"
TEST_FILE="runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/test.jsonl"

if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  printf '必须从服务端项目根目录运行：%s\n' "$PROJECT_ROOT" >&2
  exit 2
fi
if [[ ! -f "$CONFIG" || ! -f "$TEST_FILE" ]]; then
  printf '固定配置或 seed44 测试集不存在\n' >&2
  exit 2
fi
if [[ ! -f "${S3_DIR}/final_adapter/adapter_model.safetensors" || ! -f "${S3_DIR}/state_head.pt" ]]; then
  printf '冻结 S3 适配器或状态头不完整：%s\n' "$S3_DIR" >&2
  exit 2
fi
if [[ -e "$OUTPUT_DIR" || -e "$LAUNCHER_LOG" ]]; then
  printf '输出目录或启动日志已存在，拒绝复用：%s\n' "$OUTPUT_DIR" >&2
  exit 2
fi

source /root/.bashrc
set -u
mkdir -p "$(dirname "$OUTPUT_DIR")"

set +e
{
  printf 'S3_SAME_SPLIT_PHYSICS=开始\n'
  printf 'OUTPUT_DIR=%s\n' "$OUTPUT_DIR"
  uv run --no-sync python -m flow_probe.s3_same_split_physics --config "$CONFIG"
  status=$?
  printf 'S3_SAME_SPLIT_PHYSICS_EXIT=%s\n' "$status"
  if [[ -d "$OUTPUT_DIR" ]]; then
    cp "$LAUNCHER_LOG" "$OUTPUT_DIR/launcher.log"
  fi
  exit "$status"
} >"$LAUNCHER_LOG" 2>&1
