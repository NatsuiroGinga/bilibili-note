#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

mode=${1:-}
script_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
project_root=$(cd "$(dirname "$script_path")/.." && pwd)
config_path=configs/shared_b0_distilbert_seed42_v1.yaml
model_path=/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased
dataset_root=runs/data-frozen/dataset-v1-shared-b0
formal_output=runs/baselines/shared-b0-distilbert-seed42-theory-selection-review-pending-v1
formal_screen=shared-b0-distilbert-seed42-v1
minimum_free_bytes=$((5 * 1024 * 1024 * 1024))

cd "$project_root"

usage() {
  printf '用法：bash %s test|smoke|formal\n' "${BASH_SOURCE[0]}" >&2
}

require_command() {
  local name=$1
  if ! command -v "$name" >/dev/null 2>&1; then
    printf '服务器缺少必需命令：%s\n' "$name" >&2
    return 1
  fi
}

write_capabilities() {
  local target=$1
  {
    printf 'rg_path=%s\n' "$(command -v rg)"
    rg --version
    printf 'uv_path=%s\n' "$(command -v uv)"
    uv --version
    if command -v fd >/dev/null 2>&1; then
      printf 'fd_path=%s\n' "$(command -v fd)"
      fd --version
    elif command -v fdfind >/dev/null 2>&1; then
      printf 'fd_path=%s\n' "$(command -v fdfind)"
      fdfind --version
    else
      printf '%s\n' 'fd=unavailable'
    fi
    printf 'python_path=%s\n' "$(uv run --frozen python -c 'import sys; print(sys.executable)')"
    uv run --frozen python -c 'import torch, transformers, swanlab; print(f"torch={torch.__version__}"); print(f"transformers={transformers.__version__}"); print(f"swanlab={swanlab.__version__}"); print(f"cuda={torch.cuda.is_available()}")'
    uname -a
    df -h "$project_root"
  } >"$target"
  test -s "$target"
}

preflight_common() {
  local capability_path=$1
  require_command rg
  require_command uv
  require_command jq
  require_command sha256sum
  local required_path
  for required_path in \
    "$config_path" \
    src/flow_probe/shared_b0_distilbert_baseline.py \
    scripts/run_shared_b0_distilbert_training.sh \
    "$dataset_root/manifests/checksums.json" \
    "$dataset_root/manifests/freeze_manifest.json" \
    "$dataset_root/manifests/input_binding.json" \
    "$dataset_root/manifests/statistics.json" \
    "$dataset_root/candidate/bert_train.parquet" \
    "$dataset_root/validation/genis_bert.parquet" \
    "$model_path/config.json" \
    "$model_path/model.safetensors"; do
    if [[ ! -f "$required_path" ]]; then
      printf '缺少 DistilBERT 运行输入：%s\n' "$required_path" >&2
      return 1
    fi
  done
  local free_bytes
  free_bytes=$(df -PB1 "$project_root" | awk 'NR == 2 {print $4}')
  if ((free_bytes < minimum_free_bytes)); then
    printf '服务器可用空间不足 5 GiB：%s 字节\n' "$free_bytes" >&2
    return 1
  fi
  write_capabilities "$capability_path"
}

run_test() {
  require_command uv
  local test_nodes=(
    tests/test_shared_b0_distilbert_baseline.py::test_real_config_parses_without_importing_model_runtime
    tests/test_shared_b0_distilbert_baseline.py::test_prepare_frozen_inputs_binds_exact_three_files_and_label_mapping
    tests/test_shared_b0_distilbert_baseline.py::test_smoke16_skips_tqhc2_uses_fixed_rows_and_isolates_output
    tests/test_shared_b0_distilbert_baseline.py::test_prepare_frozen_inputs_rejects_hash_mismatch
    tests/test_shared_b0_distilbert_baseline.py::test_prepare_frozen_inputs_rejects_overlap_after_hash_refresh
    tests/test_shared_b0_distilbert_baseline.py::test_prepare_frozen_inputs_rejects_order_or_label_violation
    tests/test_shared_b0_distilbert_baseline.py::test_binary_metrics_include_detection_calibration_and_brier_values
    tests/test_shared_b0_distilbert_baseline.py::test_cpu_stub_forward_preserves_batch_order_and_probability_range
    tests/test_shared_b0_distilbert_baseline.py::test_resume_selects_latest_legal_checkpoint_and_restores_prepared_state
    tests/test_shared_b0_distilbert_baseline.py::test_swanlab_scalar_events_are_flat_and_finish_explicitly
  )
  uv run --frozen pytest -q "${test_nodes[@]}"
}

run_with_log() {
  local log_path=$1
  shift
  mkdir -p "$(dirname "$log_path")"
  : >"$log_path"
  set +e
  "$@" 2>&1 | tee "$log_path"
  local pipeline_status=("${PIPESTATUS[@]}")
  set -e
  local command_status=${pipeline_status[0]}
  local tee_status=${pipeline_status[1]}
  if [[ ! -s "$log_path" ]]; then
    printf '%s\n' '运行日志为空。' >>"$log_path"
    if [[ "$command_status" -eq 0 && "$tee_status" -eq 0 ]]; then
      command_status=1
    fi
  fi
  if [[ "$command_status" -ne 0 ]]; then
    return "$command_status"
  fi
  return "$tee_status"
}

run_smoke() {
  local run_id
  run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
  local output_dir="runs/smoke/shared-b0-distilbert-smoke16-seed42-${run_id}"
  local launcher_dir="runs/launchers/shared-b0-distilbert-smoke16-${run_id}"
  mkdir -p "$launcher_dir" "$(dirname "$output_dir")"
  preflight_common "$launcher_dir/capabilities.txt"
  if [[ -e "$output_dir" || -L "$output_dir" ]]; then
    printf '冒烟输出目录已存在，拒绝复用：%s\n' "$output_dir" >&2
    return 1
  fi
  {
    sha256sum "$config_path"
    sha256sum src/flow_probe/shared_b0_distilbert_baseline.py
    sha256sum scripts/run_shared_b0_distilbert_training.sh
    sha256sum "$dataset_root/candidate/bert_train.parquet"
    sha256sum "$dataset_root/validation/genis_bert.parquet"
  } >"$launcher_dir/bindings.sha256"
  run_with_log "$launcher_dir/launcher.log" \
    uv run --frozen python -m flow_probe.shared_b0_distilbert_baseline \
    --config "$config_path" \
    --model-path "$model_path" \
    --gpu-smoke16-output "$output_dir"
  jq -e '
    .mode == "smoke16" and
    .sample_counts.train == 16 and
    .sample_counts.genis == 16 and
    (.training_loss | numbers) and
    .optimizer_steps == 1 and
    .tqhc2_access == "forbidden"
  ' "$output_dir/summary.json" >/dev/null
  jq -e '.status == "finished" and .tqhc2_evaluation_status == "not_started"' \
    "$output_dir/run_state.json" >/dev/null
  jq -e -s '
    length == 16 and
    all(.[]; (.probability_malicious >= 0 and .probability_malicious <= 1))
  ' "$output_dir/predictions/genis_predictions.jsonl" >/dev/null
  jq -e -s '
    any(.[]; .event == "optimizer_step" and (.metrics["train/loss"] | numbers)) and
    any(.[]; .event == "smoke_genis_evaluation")
  ' "$output_dir/swanlab_metrics.jsonl" >/dev/null
  printf 'SMOKE_OUTPUT=%s\n' "$output_dir"
}

run_formal_worker() {
  local launcher_dir=${SHARED_B0_DISTILBERT_LAUNCHER_DIR:?缺少正式启动证据目录}
  preflight_common "$launcher_dir/capabilities.txt"
  if [[ ! -f "$dataset_root/validation/tqhc2_bert.parquet" ]]; then
    printf '%s\n' '正式运行缺少 TQH-C2 固定外部验证输入。' >&2
    return 1
  fi
  {
    sha256sum "$config_path"
    sha256sum src/flow_probe/shared_b0_distilbert_baseline.py
    sha256sum scripts/run_shared_b0_distilbert_training.sh
    sha256sum "$dataset_root/candidate/bert_train.parquet"
    sha256sum "$dataset_root/validation/genis_bert.parquet"
    sha256sum "$dataset_root/validation/tqhc2_bert.parquet"
  } >"$launcher_dir/bindings.sha256"
  local status=0
  run_with_log "$launcher_dir/launcher.log" \
    uv run --frozen python -m flow_probe.shared_b0_distilbert_baseline \
    --config "$config_path" \
    --model-path "$model_path" || status=$?
  printf '%s\n' "$status" >"$launcher_dir/exit-code.txt"
  if [[ "$status" -eq 0 ]]; then
    printf '%s\n' finished >"$launcher_dir/status.txt"
  else
    printf '%s\n' failed >"$launcher_dir/status.txt"
  fi
  return "$status"
}

launch_formal() {
  require_command screen
  if [[ -e "$formal_output" || -L "$formal_output" ]]; then
    printf '正式运行目录已存在，拒绝覆盖或复用：%s\n' "$formal_output" >&2
    return 1
  fi
  if screen -S "$formal_screen" -Q select . >/dev/null 2>&1; then
    printf '正式训练会话已存在：%s\n' "$formal_screen" >&2
    return 1
  fi
  local run_id
  run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
  local launcher_dir="runs/launchers/shared-b0-distilbert-formal-${run_id}"
  mkdir -p "$launcher_dir" "$(dirname "$formal_output")"
  printf '%s\n' prepared >"$launcher_dir/status.txt"
  screen -L -Logfile "$launcher_dir/screen.log" -DmS "$formal_screen" \
    env SHARED_B0_DISTILBERT_FORMAL_WORKER=1 \
    SHARED_B0_DISTILBERT_LAUNCHER_DIR="$launcher_dir" \
    bash "$script_path" formal
  sleep 2
  if screen -S "$formal_screen" -Q select . >/dev/null 2>&1; then
    printf '%s\n' running >"$launcher_dir/status.txt"
    printf 'FORMAL_SCREEN=%s\nFORMAL_OUTPUT=%s\nFORMAL_LAUNCHER=%s\n' \
      "$formal_screen" "$formal_output" "$launcher_dir"
    return 0
  fi
  if [[ -s "$launcher_dir/exit-code.txt" ]]; then
    printf '%s\n' failed >"$launcher_dir/status.txt"
    printf '正式训练在启动检查前退出，退出码=%s，证据=%s\n' \
      "$(<"$launcher_dir/exit-code.txt")" "$launcher_dir" >&2
    return 1
  fi
  printf '%s\n' failed >"$launcher_dir/status.txt"
  printf '正式训练 screen 未保持运行且没有退出码：%s\n' "$launcher_dir" >&2
  return 1
}

case "$mode" in
  test)
    run_test
    ;;
  smoke)
    run_smoke
    ;;
  formal)
    if [[ "${SHARED_B0_DISTILBERT_FORMAL_WORKER:-0}" == "1" ]]; then
      run_formal_worker
    else
      launch_formal
    fi
    ;;
  *)
    usage
    exit 2
    ;;
esac
