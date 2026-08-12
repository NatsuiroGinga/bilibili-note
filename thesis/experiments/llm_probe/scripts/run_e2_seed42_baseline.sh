#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_root"

protocol_dir=""
panel=""
model=""
seed="42"
max_iterations="100"
output_dir=""
launcher_dir=""

while (($#)); do
  case "$1" in
    --protocol-dir)
      protocol_dir=${2:?缺少 --protocol-dir 参数值}
      shift 2
      ;;
    --panel)
      panel=${2:?缺少 --panel 参数值}
      shift 2
      ;;
    --model)
      model=${2:?缺少 --model 参数值}
      shift 2
      ;;
    --seed)
      seed=${2:?缺少 --seed 参数值}
      shift 2
      ;;
    --max-iterations)
      max_iterations=${2:?缺少 --max-iterations 参数值}
      shift 2
      ;;
    --output-dir)
      output_dir=${2:?缺少 --output-dir 参数值}
      shift 2
      ;;
    --launcher-dir)
      launcher_dir=${2:?缺少 --launcher-dir 参数值}
      shift 2
      ;;
    *)
      printf '未知参数：%s\n' "$1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$protocol_dir" || -z "$panel" || -z "$model" || -z "$output_dir" || -z "$launcher_dir" ]]; then
  printf '%s\n' '缺少必要参数。' >&2
  exit 2
fi

case "$panel" in
  abd_to_c | ab_to_c) ;;
  *)
    printf '不支持的面板：%s\n' "$panel" >&2
    exit 2
    ;;
esac

case "$model" in
  hgb | xgboost | random_forest | mlp | groupdro) ;;
  *)
    printf '本包装器不支持的基线：%s\n' "$model" >&2
    exit 2
    ;;
esac

for command_name in rg uv sha256sum tee; do
  command -v "$command_name" >/dev/null 2>&1 || {
    printf '缺少命令：%s\n' "$command_name" >&2
    exit 2
  }
done

if [[ ! -d "$protocol_dir" ]]; then
  printf '协议目录不存在：%s\n' "$protocol_dir" >&2
  exit 2
fi
if [[ -e "$output_dir" || -e "$launcher_dir" ]]; then
  printf '输出或启动目录已存在，拒绝覆盖：%s %s\n' "$output_dir" "$launcher_dir" >&2
  exit 2
fi

mkdir -p "$launcher_dir" "$(dirname "$output_dir")"

write_status() {
  local value=$1
  local temporary="$launcher_dir/status.txt.partial.$$"
  printf '%s\n' "$value" >"$temporary"
  mv "$temporary" "$launcher_dir/status.txt"
}

write_status prepared
{
  printf 'panel=%s\n' "$panel"
  printf 'model=%s\n' "$model"
  printf 'seed=%s\n' "$seed"
  printf 'max_iterations=%s\n' "$max_iterations"
  printf 'protocol_dir=%s\n' "$protocol_dir"
  printf 'output_dir=%s\n' "$output_dir"
} >"$launcher_dir/binding.txt"

{
  sha256sum \
    src/flow_probe/e2_hard_domain_data.py \
    src/flow_probe/e2_hard_domain_metrics.py \
    src/flow_probe/e2_hard_domain_baselines.py \
    pyproject.toml
  rg --files "$protocol_dir" | sort | xargs sha256sum
} >"$launcher_dir/input.sha256"

{
  printf 'uv=%s\n' "$(command -v uv)"
  printf 'python=%s\n' "$(uv run --no-sync python -c 'import sys; print(sys.version.split()[0])')"
  printf 'cpu_count=%s\n' "$(uv run --no-sync python -c 'import os; print(os.cpu_count())')"
} >"$launcher_dir/capabilities.txt"

write_status running
set +e
uv run --no-sync python -m flow_probe.e2_hard_domain_baselines \
  --protocol-dir "$protocol_dir" \
  --panel "$panel" \
  --model "$model" \
  --output-dir "$output_dir" \
  --seed "$seed" \
  --max-iterations "$max_iterations" 2>&1 | tee "$launcher_dir/launcher.log"
pipeline_status=("${PIPESTATUS[@]}")
set -e

command_status=${pipeline_status[0]}
tee_status=${pipeline_status[1]}
printf '%s\n' "$command_status" >"$launcher_dir/command-exit-code.txt"
printf '%s\n' "$tee_status" >"$launcher_dir/tee-exit-code.txt"

if ((command_status != 0 || tee_status != 0)); then
  write_status failed
  exit 1
fi
if [[ ! -s "$output_dir/summary.json" || ! -s "$output_dir/predictions.jsonl" ]]; then
  printf '%s\n' '运行退出为零，但缺少有效摘要或逐样本预测。' >>"$launcher_dir/launcher.log"
  write_status failed
  exit 1
fi

sha256sum "$output_dir/summary.json" "$output_dir/predictions.jsonl" >"$launcher_dir/output.sha256"
write_status finished
