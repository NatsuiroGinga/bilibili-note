#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_root"

run_root=runs/verification/shared-b0-generation-preflight-20260730
adapter_path=runs/baselines/shared-b0-qwen-seed42-200/checkpoint-200
batch1_config=configs/shared_b0_qwen_seed42_eval128_batch1.yaml
batch16_config=configs/shared_b0_qwen_seed42_eval128_batch16.yaml
state_file="$run_root/preflight_state.txt"

mkdir -p "$run_root/logs" "$run_root/comparison"
for required_path in \
  "$adapter_path" \
  "$batch1_config" \
  "$batch16_config" \
  "$run_root/genis_eval128.jsonl"; do
  if [[ ! -e "$required_path" ]]; then
    printf '缺少预检输入：%s\n' "$required_path" >&2
    exit 1
  fi
done

write_state() {
  local state=$1
  local temporary="${state_file}.partial"
  printf 'state=%s\nupdated_at=%s\n' "$state" "$(date --iso-8601=seconds)" >"$temporary"
  mv "$temporary" "$state_file"
}

run_evaluation() {
  local name=$1
  local config=$2
  local log_file="$run_root/logs/${name}.log"

  write_state "${name}_running"
  .venv/bin/flow-probe-evaluate \
    --config "$config" \
    --adapter-path "$adapter_path" 2>&1 | tee "$log_file"
  local status=${PIPESTATUS[0]}
  printf '%s\n' "$status" >"$run_root/logs/${name}.exit-code.txt"
  if [[ "$status" -ne 0 ]]; then
    write_state "${name}_failed"
    exit "$status"
  fi
}

run_evaluation batch1 "$batch1_config"
run_evaluation batch16 "$batch16_config"

jq -Sc '{sample_id,generated_text,parsed_label,is_valid,expected_output_key}' \
  "$run_root/batch1/predictions.jsonl" >"$run_root/comparison/batch1_predictions.jsonl"
jq -Sc '{sample_id,generated_text,parsed_label,is_valid,expected_output_key}' \
  "$run_root/batch16/predictions.jsonl" >"$run_root/comparison/batch16_predictions.jsonl"

if ! diff -u \
  "$run_root/comparison/batch1_predictions.jsonl" \
  "$run_root/comparison/batch16_predictions.jsonl" \
  >"$run_root/comparison/prediction_equivalence.diff"; then
  write_state prediction_mismatch
  printf '批量生成与单条生成的预测不一致，详见：%s\n' \
    "$run_root/comparison/prediction_equivalence.diff" >&2
  exit 1
fi

sha256sum \
  "$run_root/genis_eval128.jsonl" \
  "$run_root/batch1/evaluation_summary.json" \
  "$run_root/batch1/predictions.jsonl" \
  "$run_root/batch16/evaluation_summary.json" \
  "$run_root/batch16/predictions.jsonl" \
  >"$run_root/comparison/artifact_sha256.txt"

write_state completed
printf '吞吐预检完成，逐条预测完全一致。结果目录：%s\n' "$run_root"
