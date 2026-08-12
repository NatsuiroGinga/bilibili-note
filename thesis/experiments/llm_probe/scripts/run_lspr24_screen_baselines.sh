#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 3 ]]; then
  printf '%s\n' '用法：bash scripts/run_lspr24_screen_baselines.sh <dataset-manifest.json> <唯一输出目录> <运行名称>' >&2
  exit 64
fi

dataset_manifest=$1
output_dir=$2
run_name=$3

if [[ ! -f "$dataset_manifest" ]]; then
  printf '%s\n' '数据清单不存在。' >&2
  exit 64
fi
if [[ -e "$output_dir" ]]; then
  printf '%s\n' '输出目录已存在，必须使用唯一新目录。' >&2
  exit 64
fi
case "$dataset_manifest|$output_dir" in
  *final-test*|*final_test*|*sealed*)
    printf '%s\n' '拒绝最终区或封存区路径。' >&2
    exit 64
    ;;
esac

exec uv run --no-sync python -m flow_probe.lspr24_screen_baselines \
  --dataset-manifest "$dataset_manifest" \
  --output-dir "$output_dir" \
  --run-name "$run_name" \
  --seed 42
