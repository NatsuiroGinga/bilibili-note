#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -uo pipefail

if [[ $# -ne 2 ]]; then
  printf '用法：%s <单组配置> <F-A|F-P|F-S>\n' "$0" >&2
  exit 2
fi

project_root="/root/autodl-tmp/thesis/experiments/llm_probe"
config="$1"
variant="$2"
case "$variant" in
  F-A | F-P | F-S) ;;
  *)
    printf '非法组别：%s\n' "$variant" >&2
    exit 2
    ;;
esac

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
config_name="$(basename "$config" .yaml)"
launcher_root="$project_root/runs/launchers/r2-qwen-candidate/$config_name-$timestamp"
log_path="$launcher_root/launcher.log"
status_path="$launcher_root/status.txt"

mkdir -p "$launcher_root"
cd "$project_root" || exit 2
printf 'running\n' >"$status_path"

set +e
R2_QWEN_CANDIDATE_REQUIRED=1 \
  uv run --no-sync python -m flow_probe.r2_final_qwen_probe \
  --config "$config" \
  --trusted-root "$project_root" \
  --variant "$variant" 2>&1 | tee "$log_path"
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
  exit 0
fi
exit_code=$main_exit_code
if [[ $exit_code -eq 0 ]]; then
  exit_code=$tee_exit_code
fi
if [[ $exit_code -eq 0 ]]; then
  exit_code=1
fi
printf 'failed:main=%s:tee=%s:log_nonempty=%s\n' \
  "$main_exit_code" "$tee_exit_code" "$log_nonempty" >"$status_path"
exit "$exit_code"
