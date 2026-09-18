#!/usr/bin/env bash
set -euo pipefail

CONFIG="configs/ch3-drift-update-expert-mixture-fold0-short-step-v1.json"
TOOL="tools/ch3_drift_update_expert_mixture_fold0_short_step.py"
SCRIPT="scripts/remote_launchers/run_ch3_drift_update_expert_mixture_fold0_short_step_v1.sh"
RUN_ID="ch3-drift-update-expert-mixture-fold0-short-step-v1"
LOCAL_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"

for path in "$CONFIG" "$TOOL" "$SCRIPT"; do
  [[ -s "$LOCAL_ROOT/$path" ]] || { printf '本机生产文件不存在或为空：%s\n' "$path" >&2; exit 67; }
done

# 在统一启动和回传入口前同步本次三个新文件，避免远端缺脚本而错误复用旧版本。
for path in "$CONFIG" "$TOOL" "$SCRIPT"; do
  expect "$LOCAL_ROOT/tools/remote_exec/gpu_env_quiet.exp" "mkdir -p '$REMOTE_ROOT/$(dirname "$path")'" >/dev/null
  expect "$LOCAL_ROOT/tools/remote_exec/gpu_rsync_push.exp" "$LOCAL_ROOT/$path" "$REMOTE_ROOT/$path" >/dev/null
done

for path in "$CONFIG" "$TOOL" "$SCRIPT"; do
  local_hash="$(shasum -a 256 "$LOCAL_ROOT/$path" | awk '{print $1}')"
  remote_hash="$(expect "$LOCAL_ROOT/tools/remote_exec/gpu_env_quiet.exp" "cd '$REMOTE_ROOT' && sha256sum '$path' | cut -d ' ' -f 1" 2>/dev/null | tail -n 1)"
  [[ "$local_hash" == "$remote_hash" ]] || { printf '远端同步哈希不匹配：%s\n' "$path" >&2; exit 68; }
done

cd "$LOCAL_ROOT"
PULL_INTERVAL_SECONDS=30 PULL_MAX_SIZE=512m \
  bash scripts/remote_launchers/launch_run_with_pull.sh \
  "$CONFIG" "$RUN_ID" \
  "--project-root . --run-dir runs/diagnostics/${RUN_ID} --resume" \
  "$TOOL"
