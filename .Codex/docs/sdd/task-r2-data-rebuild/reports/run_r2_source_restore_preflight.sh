#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

project_root=/root/autodl-tmp/thesis/experiments/llm_probe
repository_root=/root/autodl-tmp/thesis
log_dir="$project_root/runs/validation/r2-source-restore-preflight-20260731"
ops_dir="$project_root/runs/validation/r2-source-restore-preflight-20260731.ops"

cd "$project_root"
test -d "$log_dir"
test -f "$ops_dir/r2_source_restore_preflight.py"

{
  printf 'rg=' && command -v rg
  printf 'uv=' && command -v uv
  rg --version | head -n 1
  uv --version
  df -B1 --output=avail,pcent,target /root/autodl-tmp
  sha256sum \
    src/flow_probe/r2_protocol_contract.py \
    configs/r2_protocol_data_v1.yaml \
    tests/test_r2_protocol_contract.py
} >"$log_dir/environment.txt"

set +e
CUDA_VISIBLE_DEVICES='' uv run --no-sync pytest -q \
  tests/test_r2_protocol_contract.py 2>&1 | tee "$log_dir/task01-tests.log"
test_statuses=("${PIPESTATUS[@]}")
set -e
printf '%s\n' "${test_statuses[0]}" >"$log_dir/task01-tests.exit-code"
printf '%s\n' "${test_statuses[1]}" >"$log_dir/task01-tests-tee.exit-code"
if [[ "${test_statuses[0]}" -ne 0 || "${test_statuses[1]}" -ne 0 ]]; then
  exit "${test_statuses[0]}"
fi

set +e
CUDA_VISIBLE_DEVICES='' uv run --no-sync python \
  "$ops_dir/r2_source_restore_preflight.py" \
  --project-root "$project_root" \
  --repository-root "$repository_root" \
  --genis-archive /root/autodl-tmp/thesis/datasets/GeNIS-2025/2-flows.zip \
  --config "$project_root/configs/r2_protocol_data_v1.yaml" \
  --source-lock-output "$project_root/runs/data-freeze-configs/r2-protocol-v1" \
  --log-dir "$log_dir" 2>&1 | tee "$log_dir/task01-source-preflight.log"
preflight_statuses=("${PIPESTATUS[@]}")
set -e
printf '%s\n' "${preflight_statuses[0]}" >"$log_dir/task01-source-preflight.exit-code"
printf '%s\n' "${preflight_statuses[1]}" >"$log_dir/task01-source-preflight-tee.exit-code"
exit "${preflight_statuses[0]}"
