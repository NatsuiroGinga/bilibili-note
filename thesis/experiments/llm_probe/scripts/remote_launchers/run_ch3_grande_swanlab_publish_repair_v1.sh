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

if [[ -s "$OUTPUT_ROOT/status.json" ]] && uv run --no-sync python -c '
import json, pathlib, sys
status = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if status.get("state") == "complete" and status.get("exit_code") == 0 else 1)
' "$OUTPUT_ROOT/status.json"; then
    printf 'GRANDE_SWANLAB_PUBLISH_REPAIR_ALREADY_COMPLETE output=%s\n' "$OUTPUT_ROOT"
    exit 0
fi
[[ ! -e "$OUTPUT_ROOT" ]] || { printf '发布修复输出根已存在且未完成，拒绝覆盖。\n' >&2; exit 73; }
[[ ! -e "$LAUNCHER_ROOT" ]] || { printf '发布修复启动器目录已存在，拒绝覆盖。\n' >&2; exit 73; }

uv run --no-sync python "$TOOL_PATH" \
    --config "$CONFIG_PATH" \
    --alias-config "$ALIAS_PATH" \
    --validate-config \
    --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" \
    --authorized-swanlab-project "$SWANLAB_PROJECT"
uv run --no-sync python -c 'import swanlab; from flow_probe.tracking import initialize_swanlab_run'

mkdir -p -- "$LAUNCHER_ROOT"
printf '%s\n' "bash $SCRIPT_PATH" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$CONFIG_PATH" "$ALIAS_PATH" "$TOOL_PATH" "$TRACKING_PATH" "$SCRIPT_PATH" \
    > "$LAUNCHER_ROOT/input-sha256.txt"

set +e
uv run --no-sync python "$TOOL_PATH" \
    --config "$CONFIG_PATH" \
    --alias-config "$ALIAS_PATH" \
    --publish \
    --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" \
    --authorized-swanlab-project "$SWANLAB_PROJECT"
code=$?
set -e
printf '%s\n' "$code" > "$LAUNCHER_ROOT/exit-code.txt"
(( code == 0 )) || exit "$code"

uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.loads((root / "status.json").read_text(encoding="utf-8"))
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
required = ["parent-binding.json", "tag-receipt.json", "swanlab-receipt.json", "status.json", "manifest.json", "publish-repair.log"]
valid = (
    status.get("state") == "complete"
    and status.get("exit_code") == 0
    and manifest.get("published_existing_aggregate_metrics_only") is True
    and manifest.get("new_cells_trained") == []
    and manifest.get("training_data_read") is False
    and manifest.get("gpu_read") is False
    and all((root / name).is_file() for name in required)
)
raise SystemExit(0 if valid else 7)
' "$OUTPUT_ROOT"
printf 'GRANDE_SWANLAB_PUBLISH_REPAIR_COMPLETE output=%s parent=%s\n' \
    "$OUTPUT_ROOT" ch3-grande-c00-protocolA-source-q0-seed42-v1-bf16-v1
