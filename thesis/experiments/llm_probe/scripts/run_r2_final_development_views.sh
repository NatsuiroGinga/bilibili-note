#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG_PATH="configs/r2_final_development_views_v1.yaml"
MATERIALIZER_PATH="scripts/r2_final_development_views_materialize.py"
OUTPUT_ROOT="runs/data-prepared/r2-final-sidecar-candidate-v1-server"
LAUNCH_ROOT="runs/launchers/r2-final-development-views-v1"
LOG_PATH="${LAUNCH_ROOT}/launcher.log"
STATUS_PATH="${LAUNCH_ROOT}/status.json"

write_status() {
  local status="$1"
  local materializer_exit="$2"
  local tee_exit="$3"
  local temporary="${STATUS_PATH}.tmp"
  printf '{"schema_version":"flow_probe_r2_final_development_launcher_v1","status":"%s","materializer_exit":%s,"tee_exit":%s}\n' \
    "$status" "$materializer_exit" "$tee_exit" >"$temporary"
  mv "$temporary" "$STATUS_PATH"
}

cd "$PROJECT_ROOT"
if [[ -e "$LAUNCH_ROOT" ]]; then
  printf '%s\n' "启动目录已存在，拒绝复用：${LAUNCH_ROOT}" >&2
  exit 2
fi
if [[ -e "$OUTPUT_ROOT" || -e "${OUTPUT_ROOT}.partial" ]]; then
  printf '%s\n' "输出目录或阶段目录已存在，拒绝覆盖：${OUTPUT_ROOT}" >&2
  exit 2
fi

mkdir -p "$LAUNCH_ROOT"
write_status "prepared" -1 -1

if command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
elif [[ -x /root/.local/bin/uv ]]; then
  UV_BIN="/root/.local/bin/uv"
else
  write_status "failed" 127 -1
  printf '%s\n' "服务器未找到 uv" >&2
  exit 127
fi

write_status "running" -1 -1
set +e
"$UV_BIN" run --frozen python "$MATERIALIZER_PATH" \
  --config "$CONFIG_PATH" \
  --project-root "$PROJECT_ROOT" 2>&1 | tee "$LOG_PATH"
pipe_status=("${PIPESTATUS[@]}")
set -e

materializer_exit="${pipe_status[0]}"
tee_exit="${pipe_status[1]}"
if [[ "$materializer_exit" -ne 0 || "$tee_exit" -ne 0 ]]; then
  write_status "failed" "$materializer_exit" "$tee_exit"
  if [[ "$materializer_exit" -ne 0 ]]; then
    exit "$materializer_exit"
  fi
  exit "$tee_exit"
fi
if [[ ! -s "$LOG_PATH" || ! -s "${OUTPUT_ROOT}/artifact-manifest.json" ]]; then
  write_status "failed" 3 0
  printf '%s\n' "成功进程未生成非空日志或制品清单" >&2
  exit 3
fi

write_status "finished" 0 0
