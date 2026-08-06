#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -lt 3 ]]; then
  printf '%s\n' '用法：bash scripts/run_lspr24_g0_tabular_baselines.sh <G0-D运行根> <开发标签受限根> <唯一输出目录>' >&2
  exit 64
fi

g0_run_root=$1
restricted_root=$2
output_dir=$3

case "$g0_run_root|$restricted_root|$output_dir" in
  *final-test*|*sealed*)
    printf '%s\n' '拒绝最终区或封存区路径。' >&2
    exit 64
    ;;
esac

if [[ -e "$output_dir" ]]; then
  printf '%s\n' '输出目录已存在，必须使用唯一新目录。' >&2
  exit 64
fi

exec uv run --no-sync python -m flow_probe.lspr24_g0_tabular_adapter \
  --g0-run-root "$g0_run_root" \
  --restricted-root "$restricted_root" \
  --output-dir "$output_dir" \
  --model hgb \
  --model xgboost \
  --seed 42
