#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -uo pipefail

if [[ $# -ne 1 ]]; then
  printf '用法：%s <物理预训练配置>\n' "$0" >&2
  exit 2
fi

project_root="/root/autodl-tmp/thesis/experiments/llm_probe"
config="$1"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
seed_name="$(basename "$config" .yaml)"
launcher_root="$project_root/runs/launchers/r2-final-physics-fit/$seed_name-$timestamp"
log_path="$launcher_root/launcher.log"
status_path="$launcher_root/status.txt"

mkdir -p "$launcher_root"
cd "$project_root" || exit 2
printf 'running\n' >"$status_path"

set +e
R2_EQUAL_CAPACITY_REQUIRED=1 R2_ZERO_COLLAPSE_REQUIRED=1 \
  uv run python -m flow_probe.r2_final_physics_fit \
  --config "$config" \
  --trusted-root "$project_root" 2>&1 | tee "$log_path"
pipeline_status=("${PIPESTATUS[@]}")
main_exit_code=${pipeline_status[0]}
tee_exit_code=${pipeline_status[1]}
set -e
log_nonempty=0
if [[ -s "$log_path" ]]; then
  log_nonempty=1
fi

if [[ $main_exit_code -eq 0 && $tee_exit_code -eq 0 && $log_nonempty -eq 1 ]]; then
  printf 'finished\n' >"$status_path"
  exit_code=0
else
  exit_code=$main_exit_code
  if [[ $exit_code -eq 0 ]]; then
    exit_code=$tee_exit_code
  fi
  if [[ $exit_code -eq 0 ]]; then
    exit_code=1
  fi
  printf 'failed:main=%s:tee=%s:log_nonempty=%s\n' \
    "$main_exit_code" "$tee_exit_code" "$log_nonempty" \
    >"$status_path"
fi
exit "$exit_code"
