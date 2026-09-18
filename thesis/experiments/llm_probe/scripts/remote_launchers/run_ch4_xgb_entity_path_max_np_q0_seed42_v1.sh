#!/usr/bin/env bash
source ~/.bashrc >/dev/null 2>&1 || true
set -uo pipefail

ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
RUN_ID=ch4-xgb-entity-path-max-tong-same-model-q0-seed42-v1
SCREEN_NAME=ch4-xgb-entity-path-max-tong-same-model-s42-v1
RUN_ROOT="$ROOT/runs/diagnostics/$RUN_ID"
LAUNCH_ROOT="$ROOT/runs/launchers/$RUN_ID"
CONFIG="$ROOT/configs/ch4-xgb-entity-path-max-np-q0-seed42-v1.json"
TOOL="$ROOT/tools/ch4_xgb_entity_path_max_np_q0.py"

write_launcher_status() {
  local state="$1" stage="$2" detail="$3" code="$4"
  mkdir -p "$LAUNCH_ROOT"
  printf '{"state":"%s","stage":"%s","detail":"%s","exit_code":%s}\n' \
    "$state" "$stage" "$detail" "$code" >"$LAUNCH_ROOT/status.json"
}

if [[ "${1:-}" != "--worker" ]]; then
  if [[ -e "$RUN_ROOT" || -e "$LAUNCH_ROOT" ]]; then
    printf '运行身份已存在，禁止覆盖：%s\n' "$RUN_ID" >&2
    exit 17
  fi
  mkdir -p "$LAUNCH_ROOT"
  write_launcher_status running launch screen_started null
  screen -dmS "$SCREEN_NAME" bash "$0" --worker
  printf '已启动 %s\n' "$SCREEN_NAME"
  exit 0
fi

cd "$ROOT" || exit 91
source tools/env/activate.sh
write_launcher_status running preflight started null

uv run --no-sync python "$TOOL" --config "$CONFIG" --validate-config \
  >"$LAUNCH_ROOT/config-check.log" 2>&1 || {
    code=$?
    write_launcher_status failed preflight config_invalid "$code"
    exit "$code"
  }

bash tools/memory_admission_gate.sh 58 "$RUN_ID" \
  >"$LAUNCH_ROOT/resource-gate.log" 2>&1 || {
    code=$?
    write_launcher_status failed preflight resource_gate_failed "$code"
    exit "$code"
  }

free_gpu_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1)
if [[ -z "$free_gpu_mib" || "$free_gpu_mib" -lt 11264 ]]; then
  write_launcher_status failed preflight gpu_memory_insufficient 14
  exit 14
fi

write_launcher_status running experiment python_started null
set +e
uv run --no-sync python "$TOOL" --config "$CONFIG" 2>&1 | tee "$LAUNCH_ROOT/run.log"
codes=("${PIPESTATUS[@]}")
set -e
python_code="${codes[0]}"
tee_code="${codes[1]}"
if [[ "$python_code" -ne 0 ]]; then
  write_launcher_status failed experiment python_failed "$python_code"
  exit "$python_code"
fi
if [[ "$tee_code" -ne 0 ]]; then
  write_launcher_status failed experiment log_write_failed "$tee_code"
  exit "$tee_code"
fi
if [[ ! -s "$RUN_ROOT/summary.json" || ! -s "$RUN_ROOT/manifest.json" ]]; then
  write_launcher_status failed postflight required_artifact_missing 15
  exit 15
fi
write_launcher_status finished complete success 0
