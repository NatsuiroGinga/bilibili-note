#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-grande-swanlab-publish-repair-v1
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-grande-swanlab-publish-repair-v1.json"
readonly ALIAS_PATH="$PROJECT_ROOT/configs/swanlab-tag-aliases-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_grande_swanlab_publish_repair.py"
readonly TRACKING_PATH="$PROJECT_ROOT/src/flow_probe/tracking.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_grande_swanlab_publish_repair_v1.sh"
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=ns3-rwkv-lspr24

cd "$PROJECT_ROOT"
source tools/env/activate.sh

for command in uv swanlab sha256sum; do
    command -v "$command" >/dev/null 2>&1 \
        || { printf '发布修复环境缺少命令：%s\n' "$command" >&2; exit 69; }
done
for path in "$CONFIG_PATH" "$ALIAS_PATH" "$TOOL_PATH" "$TRACKING_PATH" "$SCRIPT_PATH"; do
    [[ -s "$path" ]] || { printf '发布修复生产文件缺失：%s\n' "$path" >&2; exit 67; }
done

tool_command=(uv run --no-sync python "$TOOL_PATH"
    --config "$CONFIG_PATH"
    --alias-config "$ALIAS_PATH"
    --authorized-swanlab-workspace "$SWANLAB_WORKSPACE"
    --authorized-swanlab-project "$SWANLAB_PROJECT")

"${tool_command[@]}" --validate-config
uv run --no-sync python -c 'import swanlab; from flow_probe.tracking import initialize_swanlab_run'

if [[ -e "$OUTPUT_ROOT" ]] && "${tool_command[@]}" --verify-completed; then
    printf 'GRANDE_SWANLAB_PUBLISH_REPAIR_ALREADY_COMPLETE output=%s\n' "$OUTPUT_ROOT"
    exit 0
fi

resume_second_attempt=false
if [[ -e "$OUTPUT_ROOT" ]]; then
    [[ -s "$OUTPUT_ROOT/status.json" && -s "$OUTPUT_ROOT/manifest.json" ]] \
        || { printf '发布修复输出根不完整，拒绝继续。\n' >&2; exit 73; }
    if uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.loads((root / "status.json").read_text(encoding="utf-8"))
valid = (
    status.get("state") == "failed"
    and status.get("attempt") == 1
    and status.get("retryable_zero_step_init_401") is True
    and not (root / "attempts" / "attempt-2").exists()
)
raise SystemExit(0 if valid else 1)
' "$OUTPUT_ROOT"; then
        resume_second_attempt=true
    else
        printf '既有输出既非完整成功，也非可重试的首次零步初始化 401。\n' >&2
        exit 73
    fi
fi

if [[ "$resume_second_attempt" == false ]]; then
    [[ ! -e "$LAUNCHER_ROOT" ]] || { printf '发布修复启动器目录已存在，拒绝覆盖。\n' >&2; exit 73; }
    mkdir -p -- "$LAUNCHER_ROOT"
    printf '%s\n' "bash $SCRIPT_PATH" > "$LAUNCHER_ROOT/command.txt"
    sha256sum "$CONFIG_PATH" "$ALIAS_PATH" "$TOOL_PATH" "$TRACKING_PATH" "$SCRIPT_PATH" \
        > "$LAUNCHER_ROOT/input-sha256.txt"
    set +e
    "${tool_command[@]}" --publish --attempt 1
    attempt_one_code=$?
    set -e
    printf '%s\n' "$attempt_one_code" > "$LAUNCHER_ROOT/attempt-1-exit-code.txt"
    if (( attempt_one_code != 0 )); then
        if uv run --no-sync python -c '
import json, pathlib, sys
status = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if status.get("retryable_zero_step_init_401") is True else 1)
' "$OUTPUT_ROOT/status.json"; then
            resume_second_attempt=true
        else
            exit "$attempt_one_code"
        fi
    fi
fi

if [[ "$resume_second_attempt" == true ]]; then
    set +e
    "${tool_command[@]}" --publish --attempt 2
    attempt_two_code=$?
    set -e
    printf '%s\n' "$attempt_two_code" > "$LAUNCHER_ROOT/attempt-2-exit-code.txt"
    (( attempt_two_code == 0 )) || exit "$attempt_two_code"
fi

"${tool_command[@]}" --verify-completed
printf 'GRANDE_SWANLAB_PUBLISH_REPAIR_COMPLETE output=%s parent=%s\n' \
    "$OUTPUT_ROOT" ch3-grande-c00-protocolA-source-q0-seed42-v1-bf16-v1
