#!/usr/bin/env bash
source ~/.bashrc >/dev/null 2>&1
set -u
cd /root/autodl-tmp/thesis/experiments/llm_probe

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

launcher_dir="runs/baselines/theory-selection/genis-v0/launchers/genis-family-20260729-v1"
mkdir -p "$launcher_dir"

printf 'state=running\nstarted_at=%s\nmodel=xgboost\n' "$(date -Is)" >"$launcher_dir/xgboost-batch.status.tmp"
mv "$launcher_dir/xgboost-batch.status.tmp" "$launcher_dir/xgboost-batch.status"

for seed in 42 43 44; do
  output_dir="runs/baselines/theory-selection/genis-v0/family-xgboost-seed${seed}"
  status_file="$launcher_dir/xgboost-seed${seed}.status"
  command_file="$launcher_dir/xgboost-seed${seed}.command.txt"
  log_file="$launcher_dir/xgboost-seed${seed}.launcher.log"

  if test -f "$status_file" && rg -q '^exit_code=0$' "$status_file"; then
    continue
  fi
  if test -e "$output_dir"; then
    printf 'state=interrupted_or_existing\nchecked_at=%s\nexit_code=97\noutput_dir=%s\n' \
      "$(date -Is)" "$output_dir" >"$status_file.tmp"
    mv "$status_file.tmp" "$status_file"
    exit 97
  fi

  printf '%s\n' \
    "uv run --no-sync flow-probe-tabular-baselines" \
    "  --protocol-dir runs/data-frozen/dataset-candidate-genis-v0/protocol" \
    "  --stage theory_selection" \
    "  --expected-protocol-version data-protocol-v1.0-rc1" \
    "  --tuning-trial-index 0" \
    "  --train-manifest splits/genis-family-development-train.jsonl" \
    "  --evaluation validation=splits/genis-family-development-validation.jsonl" \
    "  --label-field family_label" \
    "  --model xgboost" \
    "  --output-dir $output_dir" \
    "  --seed $seed" \
    "  --run-name theory-selection-genis-family-xgboost-seed${seed}" >"$command_file"

  printf 'state=running\nstarted_at=%s\nmodel=xgboost\nseed=%s\noutput_dir=%s\n' \
    "$(date -Is)" "$seed" "$output_dir" >"$status_file.tmp"
  mv "$status_file.tmp" "$status_file"

  uv run --no-sync flow-probe-tabular-baselines \
    --protocol-dir runs/data-frozen/dataset-candidate-genis-v0/protocol \
    --stage theory_selection \
    --expected-protocol-version data-protocol-v1.0-rc1 \
    --tuning-trial-index 0 \
    --train-manifest splits/genis-family-development-train.jsonl \
    --evaluation validation=splits/genis-family-development-validation.jsonl \
    --label-field family_label \
    --model xgboost \
    --output-dir "$output_dir" \
    --seed "$seed" \
    --run-name "theory-selection-genis-family-xgboost-seed${seed}" >"$log_file" 2>&1
  exit_code=$?

  if test "$exit_code" -eq 0; then
    state=finished
  else
    state=failed
  fi
  printf 'state=%s\nfinished_at=%s\nmodel=xgboost\nseed=%s\nexit_code=%s\noutput_dir=%s\n' \
    "$state" "$(date -Is)" "$seed" "$exit_code" "$output_dir" >"$status_file.tmp"
  mv "$status_file.tmp" "$status_file"
  if test "$exit_code" -ne 0; then
    exit "$exit_code"
  fi
done

printf 'state=finished\nfinished_at=%s\nmodel=xgboost\nexit_code=0\n' "$(date -Is)" >"$launcher_dir/xgboost-batch.status.tmp"
mv "$launcher_dir/xgboost-batch.status.tmp" "$launcher_dir/xgboost-batch.status"
