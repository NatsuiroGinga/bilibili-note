#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_root"

run_root=runs/verification/shared-b0-generation-preflight-20260730
adapter_path=runs/baselines/shared-b0-qwen-seed42-200/checkpoint-200
state_file="$run_root/batch-diagnostic-state.txt"

mkdir -p "$run_root/logs" "$run_root/comparison"

write_state() {
  local state=$1
  local temporary="${state_file}.partial"
  printf 'state=%s\nupdated_at=%s\n' "$state" "$(date --iso-8601=seconds)" >"$temporary"
  mv "$temporary" "$state_file"
}

run_candidate() {
  local name=$1
  local config=$2
  local log_file="$run_root/logs/${name}.log"

  if [[ -f "$run_root/$name/predictions.jsonl" ]]; then
    printf '候选 %s 已有完整预测，跳过生成。\n' "$name"
    return
  fi
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

if [[ ! -f "$run_root/batch1/predictions.jsonl" ]]; then
  printf '%s\n' '缺少批量1基线预测，拒绝启动一致性诊断。' >&2
  exit 1
fi

run_candidate batch2 configs/shared_b0_qwen_seed42_eval128_batch2.yaml
run_candidate batch4 configs/shared_b0_qwen_seed42_eval128_batch4.yaml
run_candidate batch8 configs/shared_b0_qwen_seed42_eval128_batch8.yaml
run_candidate batch16-nobucket configs/shared_b0_qwen_seed42_eval128_batch16_nobucket.yaml
run_candidate batch16-nobucket-repeat configs/shared_b0_qwen_seed42_eval128_batch16_nobucket_repeat.yaml

jq -Sc '{sample_id,generated_text,parsed_label,is_valid,expected_output_key}' \
  "$run_root/batch16-nobucket/predictions.jsonl" \
  >"$run_root/comparison/batch16-nobucket_predictions.jsonl"
jq -Sc '{sample_id,generated_text,parsed_label,is_valid,expected_output_key}' \
  "$run_root/batch16-nobucket-repeat/predictions.jsonl" \
  >"$run_root/comparison/batch16-nobucket-repeat_predictions.jsonl"
if ! diff -u \
  "$run_root/comparison/batch16-nobucket_predictions.jsonl" \
  "$run_root/comparison/batch16-nobucket-repeat_predictions.jsonl" \
  >"$run_root/comparison/batch16-repeatability.diff"; then
  write_state batch16_repeatability_mismatch
  printf '%s\n' '相同批量16配置重复运行的预测不一致，拒绝冻结批量协议。' >&2
  exit 1
fi

for candidate in batch2 batch4 batch8 batch16-nobucket batch16-nobucket-repeat batch16; do
  jq -n \
    --arg candidate "$candidate" \
    --slurpfile baseline "$run_root/batch1/predictions.jsonl" \
    --slurpfile current "$run_root/$candidate/predictions.jsonl" \
    --slurpfile baseline_progress "$run_root/batch1/evaluation_progress.json" \
    --slurpfile current_progress "$run_root/$candidate/evaluation_progress.json" \
    '{
      baseline: "batch1",
      candidate: $candidate,
      sample_count: ($baseline | length),
      sample_id_mismatch_count: ([
        range(0; ($baseline | length)) as $index
        | select($baseline[$index].sample_id != $current[$index].sample_id)
      ] | length),
      generated_text_mismatch_count: ([
        range(0; ($baseline | length)) as $index
        | select($baseline[$index].generated_text != $current[$index].generated_text)
      ] | length),
      parsed_label_mismatch_count: ([
        range(0; ($baseline | length)) as $index
        | select($baseline[$index].parsed_label != $current[$index].parsed_label)
      ] | length),
      mismatched_sample_ids: [
        range(0; ($baseline | length)) as $index
        | select($baseline[$index].parsed_label != $current[$index].parsed_label)
        | $baseline[$index].sample_id
      ],
      baseline_samples_per_second: $baseline_progress[0].samples_per_second,
      candidate_samples_per_second: $current_progress[0].samples_per_second,
      speedup: (
        $current_progress[0].samples_per_second
        / $baseline_progress[0].samples_per_second
      ),
      candidate_peak_gpu_mib: $current_progress[0].gpu_peak_mib
    }' >"$run_root/comparison/${candidate}_vs_batch1.json"
done

jq -s '.' \
  "$run_root/comparison/batch2_vs_batch1.json" \
  "$run_root/comparison/batch4_vs_batch1.json" \
  "$run_root/comparison/batch8_vs_batch1.json" \
  "$run_root/comparison/batch16-nobucket_vs_batch1.json" \
  "$run_root/comparison/batch16-nobucket-repeat_vs_batch1.json" \
  "$run_root/comparison/batch16_vs_batch1.json" \
  >"$run_root/comparison/batch_consistency_summary.json"

write_state completed
jq -c '.[] | {candidate,parsed_label_mismatch_count,speedup,candidate_peak_gpu_mib}' \
  "$run_root/comparison/batch_consistency_summary.json"
