#!/usr/bin/env bash

set -Eeuo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
source tools/env/activate.sh

usage() {
  printf '%s\n' '用法：' >&2
  printf '%s\n' '  bash scripts/run_lspr24_rwkv_screen.sh prepare-cache <绝对清单> <绝对缓存目录>' >&2
  printf '%s\n' '  bash scripts/run_lspr24_rwkv_screen.sh probe-cache <绝对清单> <绝对缓存目录> [cpu|cuda]' >&2
  printf '%s\n' '  bash scripts/run_lspr24_rwkv_screen.sh gpu-gate <绝对清单> <绝对缓存目录> <绝对门禁结果>' >&2
  printf '%s\n' '  bash scripts/run_lspr24_rwkv_screen.sh train <绝对清单> <绝对缓存目录> <绝对输出目录> <运行名称> <B1|B1F|A2|B3> <256|512>' >&2
  exit 64
}

require_absolute_safe_path() {
  local path=$1
  local description=$2
  if [[ "$path" != /* ]]; then
    printf '%s\n' "阻断：${description}必须使用绝对路径：$path" >&2
    exit 64
  fi
  case "$path" in
    *final-test*|*final_test*|*sealed*|*/final/*)
      printf '%s\n' "阻断：${description}不得指向最终区或封存区：$path" >&2
      exit 64
      ;;
  esac
}

if [[ $# -lt 1 ]]; then
  usage
fi

mode=$1
shift

case "$mode" in
  prepare-cache)
    [[ $# -eq 2 ]] || usage
    manifest=$1
    cache_dir=$2
    require_absolute_safe_path "$manifest" '数据清单'
    require_absolute_safe_path "$cache_dir" '共享缓存目录'
    [[ -s "$manifest" ]] || { printf '%s\n' '阻断：数据清单不存在或为空。' >&2; exit 66; }
    [[ ! -e "$cache_dir" ]] || { printf '%s\n' '阻断：共享缓存目录已存在。' >&2; exit 73; }
    exec uv run --no-sync python -m flow_probe.lspr24_rwkv_screen prepare-cache \
      --dataset-manifest "$manifest" \
      --cache-dir "$cache_dir" \
      --seed 42 \
      --train-limit 100000 \
      --validation-limit 20000
    ;;
  probe-cache)
    [[ $# -eq 2 || $# -eq 3 ]] || usage
    manifest=$1
    cache_dir=$2
    device=${3:-cuda}
    require_absolute_safe_path "$manifest" '数据清单'
    require_absolute_safe_path "$cache_dir" '共享缓存目录'
    [[ "$device" == 'cpu' || "$device" == 'cuda' ]] || usage
    exec uv run --no-sync python -m flow_probe.lspr24_rwkv_screen probe-cache \
      --dataset-manifest "$manifest" \
      --cache-dir "$cache_dir" \
      --batch-size 8 \
      --device "$device"
    ;;
  gpu-gate)
    [[ $# -eq 3 ]] || usage
    manifest=$1
    cache_dir=$2
    gate_output=$3
    require_absolute_safe_path "$manifest" '数据清单'
    require_absolute_safe_path "$cache_dir" '共享缓存目录'
    require_absolute_safe_path "$gate_output" '显存门禁结果'
    [[ ! -e "$gate_output" ]] || { printf '%s\n' '阻断：显存门禁结果已存在。' >&2; exit 73; }
    exec uv run --no-sync python -m flow_probe.lspr24_rwkv_screen gpu-gate \
      --dataset-manifest "$manifest" \
      --cache-dir "$cache_dir" \
      --output "$gate_output" \
      --process-count 4
    ;;
  train)
    [[ $# -eq 6 ]] || usage
    manifest=$1
    cache_dir=$2
    output_dir=$3
    run_name=$4
    variant=$5
    batch_size=$6
    require_absolute_safe_path "$manifest" '数据清单'
    require_absolute_safe_path "$cache_dir" '共享缓存目录'
    require_absolute_safe_path "$output_dir" '变体输出目录'
    case "$variant" in
      B1|B1F|A2|B3) ;;
      *) usage ;;
    esac
    [[ "$batch_size" == '512' || "$batch_size" == '256' ]] || usage
    [[ ! -e "$output_dir" ]] || { printf '%s\n' '阻断：变体输出目录已存在。' >&2; exit 73; }
    exec uv run --no-sync python -m flow_probe.lspr24_rwkv_screen train \
      --dataset-manifest "$manifest" \
      --cache-dir "$cache_dir" \
      --output-dir "$output_dir" \
      --run-name "$run_name" \
      --variant "$variant" \
      --seed 42 \
      --batch-size "$batch_size" \
      --epochs 5
    ;;
  *) usage ;;
esac
