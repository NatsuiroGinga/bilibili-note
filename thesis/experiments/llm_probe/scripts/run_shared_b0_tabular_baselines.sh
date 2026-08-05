#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

script_project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if [[ "${SHARED_B0_LAUNCHER_TEST_MODE:-0}" == "1" ]]; then
  project_root=${SHARED_B0_TEST_PROJECT_ROOT:?测试模式必须设置 SHARED_B0_TEST_PROJECT_ROOT}
  dataset_dir=${SHARED_B0_TEST_DATASET_DIR:?测试模式必须设置 SHARED_B0_TEST_DATASET_DIR}
  output_dir=${SHARED_B0_TEST_OUTPUT_DIR:?测试模式必须设置 SHARED_B0_TEST_OUTPUT_DIR}
  python_bin=${SHARED_B0_TEST_PYTHON_BIN:?测试模式必须设置 SHARED_B0_TEST_PYTHON_BIN}
  run_name=shared-b0-tabular-launcher-test
else
  project_root=$script_project_root
  dataset_dir=runs/data-frozen/dataset-v1-shared-b0
  output_dir=runs/baselines/shared-b0-tabular-seed42-theory-selection-review-pending-v2
  python_bin=.venv/bin/python
  run_name=shared-b0-tabular-seed42-v2
fi
cd "$project_root"

launcher_log="$output_dir/launcher.log"
state_file="$output_dir/launcher-state.json"
exit_code_file="$output_dir/launcher-exit-code.txt"
binding_file="$output_dir/launcher-binding.txt"
capabilities_file="$output_dir/launcher-capabilities.txt"

if [[ -e "$output_dir" || -L "$output_dir" ]]; then
  printf '正式运行路径已存在，拒绝覆盖：%s\n' "$output_dir" >&2
  exit 1
fi
mkdir -p "$(dirname "$output_dir")"
if [[ ! -w "$(dirname "$output_dir")" ]]; then
  printf '正式运行父目录不可写：%s\n' "$(dirname "$output_dir")" >&2
  exit 1
fi
mkdir "$output_dir"

write_state() {
  local state=$1
  local temporary="${state_file}.partial"
  printf '{\n  "state": "%s",\n  "updated_at": "%s"\n}\n' \
    "$state" "$(date --iso-8601=seconds)" >"$temporary"
  mv "$temporary" "$state_file"
}

completed=0
final_status=
on_exit() {
  local observed_status=$?
  if [[ "$completed" -eq 1 ]]; then
    return
  fi
  local status=${final_status:-$observed_status}
  if [[ "$status" -eq 0 ]]; then
    status=1
  fi
  printf '%s\n' "$status" >"${exit_code_file}.partial" 2>/dev/null || true
  mv "${exit_code_file}.partial" "$exit_code_file" 2>/dev/null || true
  write_state failed 2>/dev/null || true
}
trap on_exit EXIT

write_state prepared
: >"$launcher_log"

run_formal() {
  write_state running

  if ! command -v rg >/dev/null 2>&1; then
    printf '%s\n' '服务器缺少 rg，停止正式运行。' >&2
    return 1
  fi
  if ! command -v uv >/dev/null 2>&1; then
    printf '%s\n' '服务器缺少 uv，停止正式运行。' >&2
    return 1
  fi

  local required_paths=(
    "$python_bin"
    src/flow_probe/shared_b0_tabular_baselines.py
    src/flow_probe/tabular_baselines.py
    scripts/run_shared_b0_tabular_baselines.sh
    "$dataset_dir/candidate/common_features.parquet"
    "$dataset_dir/candidate/bert_train.parquet"
    "$dataset_dir/validation/genis_common_features.parquet"
    "$dataset_dir/validation/genis_bert.parquet"
    "$dataset_dir/validation/tqhc2_common_features.parquet"
    "$dataset_dir/validation/tqhc2_bert.parquet"
    "$dataset_dir/manifests/checksums.json"
    "$dataset_dir/manifests/freeze_manifest.json"
  )
  local required_path
  for required_path in "${required_paths[@]}"; do
    if [[ ! -e "$required_path" ]]; then
      printf '缺少共享 B0 正式输入：%s\n' "$required_path" >&2
      return 1
    fi
  done

  {
    printf 'shared_loader_sha256='
    sha256sum src/flow_probe/shared_b0_tabular_baselines.py | cut -d ' ' -f 1
    printf 'tabular_executor_sha256='
    sha256sum src/flow_probe/tabular_baselines.py | cut -d ' ' -f 1
    printf 'launcher_sha256='
    sha256sum scripts/run_shared_b0_tabular_baselines.sh | cut -d ' ' -f 1
    printf 'checksums_sha256='
    sha256sum "$dataset_dir/manifests/checksums.json" | cut -d ' ' -f 1
    printf 'freeze_manifest_sha256='
    sha256sum "$dataset_dir/manifests/freeze_manifest.json" | cut -d ' ' -f 1
  } >"$binding_file"

  {
    printf 'rg_path=%s\n' "$(command -v rg)"
    rg --version
    printf 'uv_path=%s\n' "$(command -v uv)"
    uv --version
    if command -v fd >/dev/null 2>&1; then
      printf 'fd_path=%s\n' "$(command -v fd)"
      fd --version
    else
      printf '%s\n' 'fd=unavailable'
    fi
    uname -a
    df -h "$project_root"
  } >"$capabilities_file"

  "$python_bin" -m flow_probe.shared_b0_tabular_baselines \
    --dataset-dir "$dataset_dir" \
    --output-dir "$output_dir" \
    --seed 42 \
    --run-name "$run_name" \
    --model hgb \
    --model xgboost \
    --allow-prepared-output
}

set +e
run_formal 2>&1 | tee "$launcher_log"
pipeline_status=("${PIPESTATUS[@]}")
set -e

python_status=${pipeline_status[0]}
tee_status=${pipeline_status[1]}
status=$python_status
if [[ "$tee_status" -ne 0 ]]; then
  status=$tee_status
fi
if [[ ! -s "$launcher_log" ]]; then
  printf '%s\n' '启动日志为空，正式运行无效。' >&2
  printf '%s\n' '启动日志为空，正式运行无效。' >>"$launcher_log"
  if [[ "$status" -eq 0 ]]; then
    status=1
  fi
fi
if [[ "$status" -ne 0 ]]; then
  final_status=$status
  exit "$status"
fi

printf '%s\n' '0' >"${exit_code_file}.partial"
mv "${exit_code_file}.partial" "$exit_code_file"
write_state finished
if ! "$python_bin" -m flow_probe.shared_b0_tabular_baselines finalize \
  --run-root "$output_dir"; then
  final_status=1
  exit 1
fi

completed=1
exit 0
