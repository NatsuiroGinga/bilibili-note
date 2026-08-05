#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_root"

config=configs/shared_b0_qwen_seed42_200_tqhc2_batch16_v1.yaml
adapter_path=runs/baselines/shared-b0-qwen-seed42-200/checkpoint-200
test_file=runs/data-frozen/dataset-v1-shared-b0/validation/tqhc2_qwen.jsonl
output_dir=runs/baselines/shared-b0-qwen-seed42-200/evaluation-tqhc2-batch16-v1
launcher_log="${output_dir}.launcher.log"
state_file="${output_dir}.launcher-state.txt"
exit_code_file="${output_dir}.launcher-exit-code.txt"

for required_path in "$config" "$adapter_path" "$test_file"; do
  if [[ ! -e "$required_path" ]]; then
    printf '缺少正式评测输入：%s\n' "$required_path" >&2
    exit 1
  fi
done

if [[ -f "$output_dir/predictions.jsonl" ]]; then
  printf '正式评测已经完成，拒绝重复运行：%s\n' "$output_dir" >&2
  exit 1
fi

write_state() {
  local state=$1
  local temporary="${state_file}.partial"
  printf 'state=%s\nupdated_at=%s\n' "$state" "$(date --iso-8601=seconds)" >"$temporary"
  mv "$temporary" "$state_file"
}

write_state running
{
  printf 'config_sha256='
  sha256sum "$config" | cut -d ' ' -f 1
  printf 'test_file_sha256='
  sha256sum "$test_file" | cut -d ' ' -f 1
  printf 'evaluation_code_sha256='
  sha256sum src/flow_probe/evaluate_model.py | cut -d ' ' -f 1
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
} >"${output_dir}.launcher-binding.txt"

.venv/bin/flow-probe-evaluate \
  --config "$config" \
  --adapter-path "$adapter_path" 2>&1 | tee "$launcher_log"
status=${PIPESTATUS[0]}
printf '%s\n' "$status" >"$exit_code_file"

if [[ "$status" -eq 0 ]]; then
  write_state completed
else
  write_state failed
fi
exit "$status"
