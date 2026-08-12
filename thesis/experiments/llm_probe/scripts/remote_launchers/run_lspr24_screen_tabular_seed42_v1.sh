#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

project_root="/root/autodl-tmp/thesis/experiments/llm_probe"
manifest="$project_root/runs/data-prepared/lspr24-screen-wide-v1/dataset-manifest.json"
output_dir="$project_root/runs/baselines/lspr24-screen-tabular-seed42-v1"
launcher_dir="$project_root/runs/launchers/lspr24-screen-tabular-seed42-v1"
run_name="lspr24-screen-tabular-seed42-v1"

cd "$project_root"
source tools/env/activate.sh

if [[ ! -s "$manifest" ]]; then
  printf '%s\n' "阻断：数据清单不存在或为空：$manifest" >&2
  exit 66
elif [[ ! -f scripts/run_lspr24_screen_baselines.sh ]]; then
  printf '%s\n' '阻断：统一基线启动脚本不存在。' >&2
  exit 67
elif [[ ! -f src/flow_probe/lspr24_screen_dataset.py || ! -f src/flow_probe/lspr24_screen_baselines.py ]]; then
  printf '%s\n' '阻断：统一基线数据加载器或模型入口不存在。' >&2
  exit 68
elif [[ -e "$launcher_dir" || -e "$output_dir" ]]; then
  printf '%s\n' '阻断：本次唯一运行目录已存在，拒绝覆盖或重复启动。' >&2
  exit 73
fi

mkdir -p "$launcher_dir"
printf '%s\n' 'running' >"$launcher_dir/status.txt"
date -u +'%Y-%m-%dT%H:%M:%SZ' >"$launcher_dir/started_at.txt"

set +e
bash scripts/run_lspr24_screen_baselines.sh \
  "$manifest" \
  "$output_dir" \
  "$run_name" 2>&1 | tee "$launcher_dir/launcher.log"
pipeline_status=("${PIPESTATUS[@]}")
set -e

model_code="${pipeline_status[0]}"
tee_code="${pipeline_status[1]}"
printf '%s\n' "$model_code" >"$launcher_dir/model-exit-code.txt"
printf '%s\n' "$tee_code" >"$launcher_dir/tee-exit-code.txt"
date -u +'%Y-%m-%dT%H:%M:%SZ' >"$launcher_dir/finished_at.txt"

if [[ "$model_code" -eq 0 && "$tee_code" -eq 0 ]]; then
  printf '%s\n' 'finished' >"$launcher_dir/status.txt"
  exit 0
fi

printf '%s\n' 'failed' >"$launcher_dir/status.txt"
if [[ "$model_code" -ne 0 ]]; then
  exit "$model_code"
fi
exit "$tee_code"
