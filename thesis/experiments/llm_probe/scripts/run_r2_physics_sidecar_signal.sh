#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_root"

output_root=runs/r2-physics-sidecar-signal/formal-v0
for command_name in rg uv; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf '服务器缺少必需命令：%s\n' "$command_name" >&2
    exit 1
  fi
done
if [[ ! -x .venv/bin/python ]]; then
  printf '%s\n' '服务器项目虚拟环境缺少 Python。' >&2
  exit 1
fi
for seed in 42 43 44; do
  config="configs/r2_physics_sidecar_signal_seed${seed}.yaml"
  if [[ ! -f "$config" ]]; then
    printf '缺少三种子冻结配置：%s\n' "$config" >&2
    exit 1
  fi
  if ! rg -q '^status: ready$' "$config" || rg -q 'sha256: PENDING' "$config"; then
    printf '旁路配置的前置门禁尚未解除，零写入停止：%s\n' "$config" >&2
    exit 1
  fi
done
if [[ -e "$output_root" || -L "$output_root" ]]; then
  printf '正式旁路实验目录已存在，拒绝覆盖：%s\n' "$output_root" >&2
  exit 1
fi
mkdir -p "$output_root"

for seed in 42 43 44; do
  config="configs/r2_physics_sidecar_signal_seed${seed}.yaml"
  run_dir="$output_root/seed-${seed}"
  mkdir "$run_dir"
  launcher_log="$run_dir/launcher.log"
  state_file="$run_dir/launcher-state.json"
  exit_code_file="$run_dir/launcher-exit-code.txt"
  capabilities_file="$run_dir/launcher-capabilities.txt"
  binding_file="$run_dir/launcher-binding.txt"

  printf '{"state":"prepared","seed":%s}\n' "$seed" >"$state_file"
  {
    printf 'seed=%s\n' "$seed"
    printf 'config_sha256='
    sha256sum "$config" | cut -d ' ' -f 1
    printf 'implementation_sha256='
    sha256sum src/flow_probe/r2_physics_sidecar_signal.py | cut -d ' ' -f 1
    printf 'launcher_sha256='
    sha256sum scripts/run_r2_physics_sidecar_signal.sh | cut -d ' ' -f 1
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
  printf '{"state":"running","seed":%s}\n' "$seed" >"$state_file"

  set +e
  .venv/bin/python -m flow_probe.r2_physics_sidecar_signal \
    --config "$config" \
    --project-root "$project_root" \
    --output-dir "$run_dir" \
    --run-name "r2-sidecar-hgb-seed${seed}-dev" 2>&1 | tee "$launcher_log"
  pipeline_status=("${PIPESTATUS[@]}")
  set -e
  python_status=${pipeline_status[0]}
  tee_status=${pipeline_status[1]}
  status=$python_status
  if [[ "$tee_status" -ne 0 ]]; then
    status=$tee_status
  fi
  if [[ ! -s "$launcher_log" ]]; then
    printf '%s\n' '启动日志为空，旁路实验无效。' >>"$launcher_log"
    if [[ "$status" -eq 0 ]]; then
      status=1
    fi
  fi
  printf '%s\n' "$status" >"$exit_code_file"
  if [[ "$status" -ne 0 ]]; then
    printf '{"state":"failed","seed":%s,"exit_code":%s}\n' "$seed" "$status" >"$state_file"
    exit "$status"
  fi
  printf '{"state":"finished","seed":%s,"exit_code":0}\n' "$seed" >"$state_file"
  .venv/bin/python -m flow_probe.r2_physics_sidecar_signal \
    --finalize-run-root "$run_dir"
done

.venv/bin/python -m flow_probe.r2_physics_sidecar_signal \
  --aggregate-root "$output_root"
