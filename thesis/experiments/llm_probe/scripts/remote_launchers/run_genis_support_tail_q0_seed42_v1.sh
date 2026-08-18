#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=track-a-60s-subcategory13-xgb-support-tail-seed42-v1
readonly SCREEN_NAME=genis-support-tail-q0-seed42-v1
readonly OUTPUT_ROOT=/root/autodl-tmp/thesis/experiments/genis/runs/q0/$RUN_ID
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$LAUNCHER_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/genis-support-tail-q0-seed42-v1.json"
readonly MODULE_PATH="$PROJECT_ROOT/src/flow_probe/genis_support_tail_q0.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_genis_support_tail_q0_seed42_v1.sh"
readonly ARCHIVE_PATH=/root/autodl-tmp/thesis/raw/datasets/GeNIS-2025/4-preprocessed.zip
readonly MODULE=flow_probe.genis_support_tail_q0
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=malicious-traffic-llm
readonly ESTIMATED_PEAK_GIB=8
readonly MINIMUM_FREE_DISK_GIB=10

FD_CMD=

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
    printf '  "schema_version": "genis-support-tail-q0-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "updated_at": "%s",\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$partial"
    printf '  "screening_only": true,\n' >> "$partial"
    printf '  "formal_paper_evidence": false,\n' >> "$partial"
    printf '  "final_accessed": false\n' >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

discover_capabilities() {
    if ! command -v rg >/dev/null 2>&1 || ! command -v uv >/dev/null 2>&1; then
        printf '远端 rg 或 uv 不可用。\n' >&2
        return 69
    fi
    if command -v fd >/dev/null 2>&1; then
        FD_CMD=$(command -v fd)
    elif command -v fdfind >/dev/null 2>&1; then
        FD_CMD=$(command -v fdfind)
    else
        printf '远端 fd 与 fdfind 均不可用。\n' >&2
        return 69
    fi
    {
        printf 'fd=%s\nrg=%s\nuv=%s\n' "$FD_CMD" "$(command -v rg)" "$(command -v uv)"
        "$FD_CMD" --version
        rg --version | head -n 1
        uv --version
    } > "$LAUNCHER_ROOT/capabilities.txt"
}

validate_static_config() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))
project_root = pathlib.Path(sys.argv[1]).resolve().parent.parent
configured_output = (project_root / config.get("paths", {}).get("output_root", "")).resolve()
valid = (
    config.get("schema_version") == "genis-support-tail-q0-config-v1"
    and config.get("contract_version") == "genis-q0-track-a-60s-subcategory13-v1"
    and config.get("seed") == 42
    and config.get("classes") == config.get("data", {}).get("class_order")
    and len(config.get("classes", [])) == 13
    and len(config.get("feature_budget", {}).get("fields", [])) == 76
    and config.get("xgboost", {}).get("fixed", {}).get("tree_method") == "hist"
    and config.get("xgboost", {}).get("fixed", {}).get("device") == "cuda"
    and config.get("weighting", {}).get("alpha") == 0.005
    and config.get("variants", {}).keys() == {"B0", "S1", "T1", "ST"}
    and config.get("evidence") == {
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    and configured_output == pathlib.Path(sys.argv[2]).resolve()
)
raise SystemExit(0 if valid else 1)
' "$CONFIG_PATH" "$OUTPUT_ROOT"
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
    if [[ ! -s "$LAUNCHER_ROOT/${stage}.log" ]]; then
        write_status failed "$stage" empty_log 74
        return 74
    fi
}

run_memory_gate() {
    local log_path="$LAUNCHER_ROOT/memory-admission-gate-before-screen.log"
    set +e
    bash tools/memory_admission_gate.sh "$ESTIMATED_PEAK_GIB" "$SCREEN_NAME" \
        > "$log_path" 2>&1
    local gate_code=$?
    set -e
    cat "$log_path"
    printf '%s\n' "$gate_code" > "$LAUNCHER_ROOT/memory-admission-gate-exit-code.txt"
    if [[ "$gate_code" -ne 0 ]]; then
        write_status failed memory-admission-gate rejected "$gate_code"
        return "$gate_code"
    fi
}

validate_prepare() {
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
manifest = json.load(open(root / "data_manifest.json", encoding="utf-8"))
contract = json.load(open(root / "contract.json", encoding="utf-8"))
def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()
required = [
    "contract.json", "data_manifest.json", "feature_manifest.json",
    "split_manifest.parquet", "split_audit.json",
    "data/fit/features.npy", "data/fit/labels.npy",
    "data/calibration/features.npy", "data/calibration/labels.npy",
    "data/q0_eval/features.npy", "data/q0_eval_labels/labels.npy",
]
valid = (
    status.get("state") == "DATA_GATE_PASSED"
    and status.get("final_accessed") is False
    and manifest.get("forbidden_members_opened") == []
    and manifest.get("q0_eval_labels_opened") is False
    and all((root / item).is_file() and (root / item).stat().st_size > 0 for item in required)
    and all(
        (root / relative).is_file() and digest(root / relative) == expected
        for relative, expected in manifest.get("artifacts", {}).items()
    )
    and contract.get("config_sha256") == digest(pathlib.Path(sys.argv[2]))
    and contract.get("code_sha256") == digest(pathlib.Path(sys.argv[3]))
    and contract.get("data_manifest_sha256") == digest(root / "data_manifest.json")
)
raise SystemExit(0 if valid else 1)
' "$OUTPUT_ROOT" "$CONFIG_PATH" "$MODULE_PATH"
}

write_prepared_input_hashes() {
    sha256sum "$CONFIG_PATH" "$MODULE_PATH" "$SCRIPT_PATH" \
        "$OUTPUT_ROOT/contract.json" "$OUTPUT_ROOT/data_manifest.json" \
        > "$LAUNCHER_ROOT/input-sha256.txt"
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
manifest = json.load(open(root / "data_manifest.json", encoding="utf-8"))
for relative in sorted(manifest["artifacts"]):
    path = root / relative
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    print(f"{value.hexdigest()}  {path}")
' "$OUTPUT_ROOT" >> "$LAUNCHER_ROOT/input-sha256.txt"
}

validate_select() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
freeze = json.load(open(root / "evaluation_freeze.json", encoding="utf-8"))
required = [
    "selected_xgb_params.json", "oof_weight_audit.parquet", "threshold_audit.json",
    "weight_freeze.json", "evaluation_freeze.json",
    *[f"models/{key}.ubj" for key in ("B0", "S1", "T1", "ST")],
]
valid = (
    status.get("state") == "SELECTION_FROZEN"
    and status.get("q0_eval_labels_opened") is False
    and freeze.get("selection_used_q0_eval") is False
    and freeze.get("q0_eval_labels_opened") is False
    and all((root / item).is_file() and (root / item).stat().st_size > 0 for item in required)
)
raise SystemExit(0 if valid else 1)
' "$OUTPUT_ROOT"
}

validate_evaluate() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.load(open(root / "status.json", encoding="utf-8"))
metrics = json.load(open(root / "metrics.json", encoding="utf-8"))
required = [
    "metrics.json", "per_class_metrics.csv", "confusion_matrices.json",
    "runtime.json", "status.json",
]
gates = status.get("promotion_gates", {})
valid = (
    status.get("state") == "FINISHED"
    and status.get("q0_eval_labels_opened_after_freeze") is True
    and status.get("final_accessed") is False
    and set(gates) == {
        "recall_gain_vs_B0", "macro_f1_delta_vs_B0", "fpr_budget",
        "recall_gain_vs_best_single",
    }
    and set(metrics.get("variants", {})) == {"B0", "S1", "T1", "ST"}
    and all((root / item).is_file() and (root / item).stat().st_size > 0 for item in required)
)
raise SystemExit(0 if valid else 1)
' "$OUTPUT_ROOT"
}

preflight() {
    local mode=$1
    discover_capabilities
    validate_static_config
    if [[ ! -s "$CONFIG_PATH" || ! -s "$MODULE_PATH" || ! -s "$SCRIPT_PATH" ]]; then
        printf 'GeNIS Q0 配置、模块或启动器不存在。\n' >&2
        return 66
    fi
    if [[ "$mode" == raw_archive ]]; then
        if [[ ! -s "$ARCHIVE_PATH" ]]; then
            printf 'GeNIS 冻结归档不存在：%s\n' "$ARCHIVE_PATH" >&2
            return 66
        fi
        if [[ -e "$OUTPUT_ROOT" ]]; then
            printf '唯一运行目录已存在，拒绝覆盖或续写：%s\n' "$OUTPUT_ROOT" >&2
            return 73
        fi
    elif [[ "$mode" == from_prepared ]]; then
        if [[ ! -d "$OUTPUT_ROOT" ]]; then
            printf '远端已准备运行根不存在：%s\n' "$OUTPUT_ROOT" >&2
            return 66
        fi
        validate_prepare
    else
        printf '未知工作模式：%s\n' "$mode" >&2
        return 64
    fi
    if ! uv run --no-sync python -c '
import json, sys
status = json.load(open(sys.argv[1], encoding="utf-8"))
valid = status.get("state") == "prepared" and status.get("stage") == "launch"
raise SystemExit(0 if valid else 1)
' "$STATUS_PATH"; then
        printf '工作进程缺少合法 prepared 状态。\n' >&2
        return 74
    fi
    write_status running preflight started null
    if ! command -v flock >/dev/null 2>&1 || ! command -v nvidia-smi >/dev/null 2>&1; then
        printf '远端 flock 或 nvidia-smi 不可用。\n' >&2
        return 69
    fi
    if [[ ! -s "$LAUNCHER_ROOT/memory-admission-gate-before-screen.log" ]] \
        || ! rg -q '\[准入门禁\] 通过：' "$LAUNCHER_ROOT/memory-admission-gate-before-screen.log"; then
        printf '工作进程缺少启动前已通过的内存门禁收据。\n' >&2
        return 74
    fi
    uv run --no-sync python -c 'import numpy, pyarrow, sklearn, swanlab, xgboost'
    {
        printf 'hostname=%s\n' "$(hostname)"
        printf 'kernel=%s\n' "$(uname -srmo)"
        printf 'project_root=%s\n' "$PROJECT_ROOT"
        if [[ "$mode" == raw_archive ]]; then
            printf 'archive_path=%s\n' "$ARCHIVE_PATH"
        else
            printf 'archive_path=not_used_from_prepared\n'
        fi
        if [[ -r /sys/fs/cgroup/memory.max ]]; then
            printf 'cgroup_memory_max=%s\n' "$(cat /sys/fs/cgroup/memory.max)"
            printf 'cgroup_memory_current=%s\n' "$(cat /sys/fs/cgroup/memory.current)"
        elif [[ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]]; then
            printf 'cgroup_memory_max=%s\n' "$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes)"
            printf 'cgroup_memory_current=%s\n' "$(cat /sys/fs/cgroup/memory/memory.usage_in_bytes)"
        else
            printf '无法读取 cgroup 内存身份。\n' >&2
            return 69
        fi
    } > "$LAUNCHER_ROOT/environment-identity.txt"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader \
        > "$LAUNCHER_ROOT/gpu-preflight.txt"
    local gpu_name
    gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
    if [[ "$gpu_name" != *"RTX 5090"* ]]; then
        printf '当前 GPU 不是 C56 预期 RTX 5090：%s\n' "$gpu_name" >&2
        return 69
    fi
    if [[ "$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | wc -l)" -ne 0 ]]; then
        printf 'GPU 已有计算进程，拒绝叠加启动。\n' >&2
        return 75
    fi
    df -Pk "$PROJECT_ROOT" > "$LAUNCHER_ROOT/disk-preflight.txt"
    uv run --no-sync python -c '
import json, pathlib, shutil, sys
root = pathlib.Path(sys.argv[1])
free = shutil.disk_usage(root).free / 1024**3
minimum = float(sys.argv[2])
print(json.dumps({"disk_free_gib": free, "minimum_free_gib": minimum, "passed": free >= minimum}))
raise SystemExit(0 if free >= minimum else 1)
' "$PROJECT_ROOT" "$MINIMUM_FREE_DISK_GIB" > "$LAUNCHER_ROOT/disk-gate.json"
    uv run --no-sync python -c '
import json, sys
config = json.load(open(sys.argv[1], encoding="utf-8"))["swanlab"]
valid = (
    config.get("workspace") == sys.argv[2]
    and config.get("project") == sys.argv[3]
    and config.get("mode") == "online"
)
raise SystemExit(0 if valid else 1)
' "$CONFIG_PATH" "$SWANLAB_WORKSPACE" "$SWANLAB_PROJECT"
}

worker_main() {
    local mode=$1
    local lock_path="$LAUNCHER_ROOT/worker.lock"
    exec 9> "$lock_path"
    if ! flock -n 9; then
        printf '同一运行工作锁已被占用。\n' >&2
        return 75
    fi
    preflight "$mode"
    if [[ "$mode" == raw_archive ]]; then
        run_logged prepare uv run --no-sync python -m "$MODULE" prepare \
            --config "$CONFIG_PATH" --output-root "$OUTPUT_ROOT"
        validate_prepare
    else
        printf 'FROM_PREPARED_GATE_PASSED output=%s archive_not_used=true\n' "$OUTPUT_ROOT"
    fi
    run_logged select uv run --no-sync python -m "$MODULE" select \
        --config "$CONFIG_PATH" --output-root "$OUTPUT_ROOT"
    validate_select
    run_logged evaluate uv run --no-sync python -m "$MODULE" evaluate \
        --config "$CONFIG_PATH" --output-root "$OUTPUT_ROOT"
    validate_evaluate
    run_logged swanlab-publish uv run --no-sync python -m "$MODULE" swanlab-publish \
        --config "$CONFIG_PATH" --output-root "$OUTPUT_ROOT" \
        --authorized-workspace "$SWANLAB_WORKSPACE" --authorized-project "$SWANLAB_PROJECT"
    validate_evaluate
    sha256sum "$OUTPUT_ROOT/status.json" "$OUTPUT_ROOT/metrics.json" \
        "$OUTPUT_ROOT/runtime.json" "$OUTPUT_ROOT/swanlab_publish_receipt.json" \
        > "$LAUNCHER_ROOT/result-sha256.txt"
    write_status finished complete evaluation_and_upload_finished 0
}

worker_entry() {
    local mode=$1
    trap 'write_status interrupted signal received 130; exit 130' HUP INT TERM
    set +e
    worker_main "$mode" 2>&1 | tee "$LAUNCHER_ROOT/controller.log"
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
    worker_entry raw_archive
    exit $?
fi

if [[ ${1:-} == --worker-from-prepared ]]; then
    worker_entry from_prepared
    exit $?
fi

readonly TOP_MODE=${1:-raw_archive}
if [[ "$TOP_MODE" != raw_archive && "$TOP_MODE" != --from-prepared ]]; then
    printf '用法：bash %s [--from-prepared]\n' "$SCRIPT_PATH" >&2
    exit 64
fi
if [[ -e "$LAUNCHER_ROOT" ]]; then
    printf '同名启动器目录已存在，拒绝覆盖：%s\n' "$LAUNCHER_ROOT" >&2
    exit 73
fi
if [[ "$TOP_MODE" == raw_archive && -e "$OUTPUT_ROOT" ]]; then
    printf '原始归档模式拒绝覆盖运行目录：%s\n' "$OUTPUT_ROOT" >&2
    exit 73
fi
if [[ "$TOP_MODE" == --from-prepared && ! -d "$OUTPUT_ROOT" ]]; then
    printf 'from-prepared 模式要求已同步的准备根：%s\n' "$OUTPUT_ROOT" >&2
    exit 66
fi
mkdir -p -- "$LAUNCHER_ROOT"
discover_capabilities
validate_static_config
if [[ "$TOP_MODE" == --from-prepared ]]; then
    validate_prepare
fi
if ! command -v screen >/dev/null 2>&1; then
    printf '远端缺少 screen。\n' >&2
    exit 69
fi
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名 screen 已在运行：%s\n' "$SCREEN_NAME" >&2
    exit 75
fi
run_memory_gate
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
if [[ "$TOP_MODE" == --from-prepared ]]; then
    printf '%s\n' "$SCRIPT_PATH --worker-from-prepared" > "$LAUNCHER_ROOT/command.txt"
    write_prepared_input_hashes
    readonly WORKER_MODE=--worker-from-prepared
else
    printf '%s\n' "$SCRIPT_PATH --worker" > "$LAUNCHER_ROOT/command.txt"
    sha256sum "$CONFIG_PATH" "$MODULE_PATH" "$SCRIPT_PATH" "$ARCHIVE_PATH" \
        > "$LAUNCHER_ROOT/input-sha256.txt"
    readonly WORKER_MODE=--worker
fi
write_status prepared launch static_contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" "$WORKER_MODE"
printf 'GENIS_SUPPORT_TAIL_Q0_STARTED mode=%s session=%s launcher=%s output=%s final_accessed=false formal_paper_evidence=false\n' \
    "$TOP_MODE" "$SCREEN_NAME" "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
