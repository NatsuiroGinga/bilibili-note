#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=genis-60s-trainonly-inmemory-baseline-qualification-seed42-v1
readonly SCREEN_NAME=genis-inmemory-baseline-qualification-s42-v1
readonly OUTPUT_ROOT=/root/autodl-tmp/thesis/experiments/genis/runs/baselines/$RUN_ID
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/genis-baseline-qualification-trainonly-seed42-v1.json"
readonly MODULE_PATH="$PROJECT_ROOT/src/flow_probe/genis_baseline_qualification.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_genis_baseline_qualification_trainonly_seed42_v1.sh"
readonly ARCHIVE_PATH=/root/autodl-tmp/thesis/raw/datasets/GeNIS-2025/4-preprocessed.zip
readonly MODULE=flow_probe.genis_baseline_qualification
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=malicious-traffic-llm

cd "$PROJECT_ROOT"
source tools/env/activate.sh

write_status() {
    local state=$1
    local stage=$2
    local detail=$3
    local exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    mkdir -p -- "$LAUNCHER_ROOT"
    printf '{\n' > "$partial"
    printf '  "schema_version": "genis-inmemory-baseline-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "updated_at": "%s",\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$partial"
    printf '  "screening_only": true,\n' >> "$partial"
    printf '  "formal_paper_evidence": false,\n' >> "$partial"
    printf '  "official_test_accessed": false,\n' >> "$partial"
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

run_logged() {
    local stage=$1
    shift
    write_status running "$stage" started null
    set +e
    "$@" 2>&1 | tee "$LAUNCHER_ROOT/${stage}.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$LAUNCHER_ROOT/${stage}-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_ROOT/${stage}-tee-exit-code.txt"
    if [[ "$command_code" -ne 0 ]]; then
        write_status failed "$stage" command_failed "$command_code"
        return "$command_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        write_status failed "$stage" tee_failed "$tee_code"
        return "$tee_code"
    fi
}

validate_contract() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))
project = pathlib.Path(sys.argv[1]).resolve().parent.parent
output = (project / config["paths"]["run_root"]).resolve()
valid = (
    config["schema_version"] == "genis-inmemory-baseline-qualification-config-v1"
    and config["contract_version"] == "genis-60s-trainonly-inmemory-qualification-v1"
    and config["seed"] == 42
    and config["runtime"]["fit_count"] == 40
    and set(config["models"]) == {"xgboost", "random_forest"}
    and config["models"]["xgboost"]["device"] == "cuda"
    and config["data"]["allowed_member"] == "4-preprocessed/genis-60-sec-train.csv"
    and len(config["data"]["forbidden_members"]) == 7
    and output == pathlib.Path(sys.argv[2]).resolve()
)
raise SystemExit(0 if valid else 1)
' "$CONFIG_PATH" "$OUTPUT_ROOT"
}

validate_results() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
results = json.load(open(root / "results.json", encoding="utf-8"))
forbidden = {".npy", ".npz", ".parquet", ".csv"}
written = [str(path) for path in root.rglob("*") if path.is_file() and path.suffix in forbidden]
valid = (
    status.get("state") == "FINISHED"
    and status.get("completed_fits") == 40
    and len(results.get("cells", {})) == 8
    and results.get("official_test_accessed") is False
    and results.get("final_accessed") is False
    and not written
)
raise SystemExit(0 if valid else 1)
' "$OUTPUT_ROOT"
}

worker_main() {
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    if ! flock -n 9; then
        printf '同一运行工作锁已被占用。\n' >&2
        return 75
    fi
    validate_contract
    uv run --no-sync python -c 'import joblib, numpy, sklearn, swanlab, xgboost'
    run_logged matrix uv run --no-sync python -m "$MODULE" run \
        --config "$CONFIG_PATH" --archive-path "$ARCHIVE_PATH" --output-root "$OUTPUT_ROOT"
    validate_results
    run_logged swanlab-publish uv run --no-sync python -m "$MODULE" swanlab-publish \
        --config "$CONFIG_PATH" --output-root "$OUTPUT_ROOT" \
        --authorized-workspace "$SWANLAB_WORKSPACE" --authorized-project "$SWANLAB_PROJECT"
    validate_results
    sha256sum "$OUTPUT_ROOT/status.json" "$OUTPUT_ROOT/results.json" \
        "$OUTPUT_ROOT/swanlab_publish_receipt.json" > "$LAUNCHER_ROOT/result-sha256.txt"
    write_status finished complete matrix_and_upload_finished 0
}

worker_entry() {
    trap 'write_status interrupted signal received 130; exit 130' HUP INT TERM
    set +e
    worker_main 2>&1 | tee "$LAUNCHER_ROOT/controller.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local worker_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$worker_code" > "$LAUNCHER_ROOT/controller-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$LAUNCHER_ROOT/controller-tee-exit-code.txt"
    if [[ "$worker_code" -ne 0 ]]; then
        write_status failed controller worker_failed "$worker_code"
        return "$worker_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        write_status failed controller tee_failed "$tee_code"
        return "$tee_code"
    fi
}

if [[ ${1:-} == --worker ]]; then
    worker_entry
    exit $?
fi

if [[ $# -ne 0 ]]; then
    printf '用法：bash %s\n' "$SCRIPT_PATH" >&2
    exit 64
fi
if [[ -e "$OUTPUT_ROOT" ]]; then
    printf '唯一运行目录已存在，拒绝覆盖。\n' >&2
    exit 73
fi
if [[ ! -s "$CONFIG_PATH" || ! -s "$MODULE_PATH" || ! -s "$SCRIPT_PATH" || ! -s "$ARCHIVE_PATH" ]]; then
    printf '配置、模块、启动器或原始 ZIP 不存在。\n' >&2
    exit 66
fi
if ! command -v rg >/dev/null 2>&1 || ! command -v uv >/dev/null 2>&1 \
    || ! command -v screen >/dev/null 2>&1 || ! command -v flock >/dev/null 2>&1; then
    printf '远端缺少 rg、uv、screen 或 flock。\n' >&2
    exit 69
fi
validate_contract
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名 screen 已在运行。\n' >&2
    exit 75
fi
if [[ "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)" -ne 0 ]]; then
    printf 'GPU 已有计算进程，拒绝叠加启动。\n' >&2
    exit 75
fi
mkdir -p -- "$LAUNCHER_ROOT"
sha256sum "$CONFIG_PATH" "$MODULE_PATH" "$SCRIPT_PATH" "$ARCHIVE_PATH" \
    > "$LAUNCHER_ROOT/input-sha256.txt"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_ROOT/command.txt"
write_status prepared launch contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'GENIS_INMEMORY_BASELINE_STARTED session=%s launcher=%s output=%s\n' \
    "$SCREEN_NAME" "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
