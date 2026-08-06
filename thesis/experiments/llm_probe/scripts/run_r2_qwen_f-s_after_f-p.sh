#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

project_root="/root/autodl-tmp/thesis/experiments/llm_probe"
f_p_result="$project_root/runs/r2-qwen-candidate/qwen3-0.6b-v2/seed-42/f-p/result.json"
f_p_state="$project_root/runs/r2-qwen-candidate/qwen3-0.6b-v2/seed-42/f-p/run_state.json"

while [[ ! -f "$f_p_result" ]]; do
  if [[ -f "$f_p_state" ]]; then
    status="$(jq -r '.status // ""' "$f_p_state")"
    if [[ "$status" == "failed" || "$status" == "interrupted" ]]; then
      printf 'F-P 未完成，拒绝启动 F-S：%s\n' "$status" >&2
      exit 1
    fi
  fi
  sleep 10
done

if [[ "$(jq -r '.status // ""' "$f_p_result")" != "finished" ]]; then
  printf 'F-P 结果不是 finished，拒绝启动 F-S\n' >&2
  exit 1
fi

cd "$project_root"
exec bash scripts/run_r2_final_qwen_probe.sh \
  configs/r2_final_qwen3_0_6b_f-s_seed42.yaml \
  F-S
