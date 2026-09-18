#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID="${GRANDE_RUN_ID:-ch3-grande-c00-protocolA-source-q0-seed42-v1}"
readonly SCREEN_NAME="${GRANDE_SCREEN_NAME:-ch3-grande-pa-src-q0-s42-v1}"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$OUTPUT_ROOT/status.json"
readonly CONFIG_PATH="${GRANDE_CONFIG_PATH:-$PROJECT_ROOT/configs/ch3-grande-c00-protocol-a-source-q0-seed42-v1.json}"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_grande_protocol_a_source_q0.py"
readonly SCRIPT_PATH="${GRANDE_SCRIPT_PATH:-$PROJECT_ROOT/scripts/remote_launchers/run_ch3_grande_c00_protocol_a_source_q0_seed42_v1.sh}"
readonly REUSE_COMPLETED_G_A="${GRANDE_REUSE_COMPLETED_G_A:-false}"
readonly PRECISION_PROFILE="${GRANDE_PRECISION_PROFILE:-fp32-all-ops-v1}"
readonly VENDOR_ROOT="$PROJECT_ROOT/vendor/grande"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=ns3-rwkv-lspr24
readonly GPU_FREE_MIN_MIB=12288
readonly CGROUP_AVAILABLE_MIN_BYTES=32212254720
readonly DISK_FREE_MIN_KIB=10485760
readonly RESOURCE_RECEIPT_PATH="$OUTPUT_ROOT/resource-receipt.json"
readonly RESOURCE_SAMPLES_PATH="$OUTPUT_ROOT/resource-samples.tsv"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
RUN_STARTED_AT=$(date +%s.%N)
readonly RUN_STARTED_AT

cd "$PROJECT_ROOT"
source tools/env/activate.sh

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    local partial="$LAUNCHER_ROOT/status.json.partial.$$"
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-grande-protocol-a-source-q0-launcher-status-v1",
    "run_id": sys.argv[2], "state": sys.argv[3], "stage": sys.argv[4],
    "detail": sys.argv[5], "exit_code": None if sys.argv[6] == "null" else int(sys.argv[6]),
    "updated_at_unix": time.time(), "source_year_only": True,
    "target_year_arrays_read": 0, "target_year_paths_enumerated": 0,
    "downstream_entry_generated": False,
}
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
' "$partial" "$RUN_ID" "$state" "$stage" "$detail" "$exit_code"
    mv -f -- "$partial" "$LAUNCHER_ROOT/status.json"
}

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
    uv run --no-sync python -c '
import hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1]); manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
for name, item in manifest["files"].items():
    digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if digest != item["sha256"]: raise SystemExit(f"vendor sha mismatch: {name}")
' "$VENDOR_ROOT"
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
candidates = config["candidates"]
valid = (
    config["run_id"] == sys.argv[2]
    and config["paths"]["output_root"] == sys.argv[3]
    and config["source_arrays"] == ["X23", "y23", "I23", "M23", "E23", "T23"]
    and all("24" not in name for name in config["source_arrays"])
    and [(item["unit_key"], item["depth"], item["n_estimators"]) for item in candidates]
        == [("G-A", 4, 512), ("G-B", 5, 1024)]
    and config["training"]["cell"] == "C00"
    and config["training"]["epochs"] == 20
    and config["training"]["steps_per_epoch"] == 1000
    and config["source_year_only"] is True
    and config["target_year_arrays_read"] == 0
    and config["target_year_paths_enumerated"] == 0
    and config["swanlab"]["workspace"] == sys.argv[4]
    and config["swanlab"]["project"] == sys.argv[5]
)
raise SystemExit(0 if valid else 78)
' "$CONFIG_PATH" "$RUN_ID" "$OUTPUT_ROOT" "$SWANLAB_WORKSPACE" "$SWANLAB_PROJECT"
}

validate_inputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
root = pathlib.Path(config["paths"]["cache_root"])
arrays = config["source_arrays"]
required = [root / f"{name}.npy" for name in arrays]
valid = len(required) == 6 and all("24" not in path.stem for path in required) and all(path.is_file() for path in required)
raise SystemExit(0 if valid else 66)
' "$CONFIG_PATH"
}

validate_tracking() {
    mkdir -p -- "$LAUNCHER_ROOT/tracking-gate"
    uv run --no-sync swanlab ping > "$LAUNCHER_ROOT/tracking-gate/swanlab-ping.log" 2>&1
    uv run --no-sync swanlab verify > "$LAUNCHER_ROOT/tracking-gate/swanlab-verify.log" 2>&1
}

validate_resources() {
    mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
    bash "$MEMORY_GATE_PATH" 30 "$RUN_ID" > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1
    local free_mib cgroup_max cgroup_current cgroup_available disk_fields available_kib used_percent
    free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
    if [[ -r /sys/fs/cgroup/memory.max ]]; then
        cgroup_max=$(< /sys/fs/cgroup/memory.max)
        cgroup_current=$(< /sys/fs/cgroup/memory.current)
    elif [[ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]]; then
        cgroup_max=$(< /sys/fs/cgroup/memory/memory.limit_in_bytes)
        cgroup_current=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
    else
        printf '无法读取控制组主存上限，拒绝启动。\n' >&2
        return 69
    fi
    if [[ ! "$free_mib" =~ ^[0-9]+$ || ! "$cgroup_max" =~ ^[0-9]+$ || ! "$cgroup_current" =~ ^[0-9]+$ ]]; then
        printf '资源读数不是有限整数，拒绝启动。\n' >&2
        return 69
    fi
    cgroup_available=$((cgroup_max - cgroup_current))
    if (( free_mib < GPU_FREE_MIN_MIB || cgroup_available < CGROUP_AVAILABLE_MIN_BYTES )); then
        printf '串行资源门失败：GPU空闲=%sMiB，控制组可用=%s字节。\n' "$free_mib" "$cgroup_available" >&2
        return 69
    fi
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    if [[ ! "$available_kib" =~ ^[0-9]+$ || ! "$used_percent" =~ ^[0-9]+$ ]] \
        || (( available_kib < DISK_FREE_MIN_KIB || used_percent >= 80 )); then
        printf '磁盘资源门失败：available_kib=%s used_percent=%s\n' "$available_kib" "$used_percent" >&2
        return 69
    fi
    nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu --format=csv,noheader,nounits \
        > "$LAUNCHER_ROOT/gpu-resource.txt"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-grande-protocol-a-source-q0-resource-receipt-v1",
    "run_started_at_unix": float(sys.argv[2]), "observed_at_unix": time.time(),
    "gpu_free_mib_at_admission": int(sys.argv[3]), "cgroup_limit_bytes": int(sys.argv[4]),
    "cgroup_current_bytes_at_admission": int(sys.argv[5]),
    "cgroup_available_bytes_at_admission": int(sys.argv[6]),
    "actual_parallelism": 1, "maximum_parallelism": 1,
    "selection_reason": "candidate_order_and_single_gpu_efficiency_isolation",
    "thresholds": {"serial_gpu_gib": 12, "serial_memory_gib": 30, "disk_gib": 10},
    "source_year_only": True,
    "target_year_arrays_read": 0, "target_year_paths_enumerated": 0,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$RESOURCE_RECEIPT_PATH" "$RUN_STARTED_AT" "$free_mib" "$cgroup_max" \
        "$cgroup_current" "$cgroup_available"
}

resource_monitor() {
    printf 'unix_time\tgpu_used_mib\tcgroup_current_bytes\n' > "$RESOURCE_SAMPLES_PATH"
    while true; do
        local gpu_used cgroup_current
        gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
        if [[ -r /sys/fs/cgroup/memory.current ]]; then
            cgroup_current=$(< /sys/fs/cgroup/memory.current)
        else
            cgroup_current=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
        fi
        printf '%s\t%s\t%s\n' "$(date +%s)" "$gpu_used" "$cgroup_current" >> "$RESOURCE_SAMPLES_PATH"
        sleep 5
    done
}

finalize_resource_receipt() {
    uv run --no-sync python -c '
import json, os, pathlib, sys
receipt, samples = map(pathlib.Path, sys.argv[1:3])
value = json.loads(receipt.read_text(encoding="utf-8"))
rows = [tuple(map(int, line.split("\t"))) for line in samples.read_text(encoding="utf-8").splitlines()[1:] if line.count("\t") == 2]
if not rows:
    raise SystemExit("资源采样为空")
value.update({
    "training_started_at_unix": float(sys.argv[3]), "training_finished_at_unix": float(sys.argv[4]),
    "training_wall_seconds": float(sys.argv[4]) - float(sys.argv[3]), "sample_interval_seconds": 5,
    "sample_count": len(rows), "peak_gpu_used_mib_overall": max(row[1] for row in rows),
    "peak_cgroup_current_bytes_overall": max(row[2] for row in rows),
})
temporary = receipt.with_name(receipt.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, receipt)
' "$RESOURCE_RECEIPT_PATH" "$RESOURCE_SAMPLES_PATH" "$1" "$2"
}

run_python() {
    local phase=$1
    local resume_flag=${2:-}
    local structure=${3:-}
    local log_path="$OUTPUT_ROOT/${phase}${2:+-resume}.log"
    local command=(uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH"
        --phase "$phase"
        --resource-receipt "$RESOURCE_RECEIPT_PATH"
        --authorized-swanlab-workspace "$SWANLAB_WORKSPACE"
        --authorized-swanlab-project "$SWANLAB_PROJECT")
    [[ "$resume_flag" == --resume ]] && command+=(--resume)
    [[ -n "$structure" ]] && command+=(--structure "$structure")
    set +e
    "${command[@]}" 2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    printf '%s\n' "${pipeline_status[0]}" > "$log_path.command-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$log_path.tee-exit-code.txt"
    (( pipeline_status[1] == 0 )) || return "${pipeline_status[1]}"
    return "${pipeline_status[0]}"
}

validate_outputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
result = json.loads((root / "source-screen-results.json").read_text(encoding="utf-8"))
seal = json.loads((root / "backbone_selection_frozen.json").read_text(encoding="utf-8"))
status = json.loads((root / "status.json").read_text(encoding="utf-8"))
required = ["config.json", "input-identity.json", "dependency-receipt.json",
    "structure-candidates-frozen.json", "source-input-receipt.json", "parent-baseline-receipt.json",
    "gradient-gate-receipt.json", "resource-calibration-G-A.json", "backbone_selection_frozen.json",
    "grande-c00-source-results.json", "source-screen-results.json", "complete-alert-budget-curves.npz",
    "complete-alert-budget-curves-receipt.json", "node-fallback-receipt.json", "resource-receipt.json",
    "swanlab-receipt.json", "manifest.json", "status.json"]
if sys.argv[2] == "true":
    required += ["g-a-migration-receipt.json", "g-b-memory-policy-receipt.json", "resource-calibration-G-B.json"]
if sys.argv[3] == "cuda-bf16-amp-fp32-sensitive-v1":
    required += ["precision-memory-policy-receipt.json", "resource-calibration-G-B.json"]
candidates = seal["completed_structures"]
required += [f"checkpoints/selected-{item[\"unit_key\"]}.pt" for item in candidates]
required += [f"receipts/selection-{item[\"unit_key\"]}.json" for item in candidates]
verdict = result["verdict"]
valid = (
    result["schema_version"] == "ch3-grande-protocol-a-source-q0-results-v1"
    and 1 <= result["fits_completed"] <= 2
    and 1 <= len(candidates) <= 2
    and all(len(item["history"]) == 20 and item["optimizer_steps"] == 20000 for item in candidates)
    and (
        sys.argv[2] != "true"
        or next(item for item in candidates if item["unit_key"] == "G-B")["flow_microbatch_size"] == 2048
    )
    and (
        sys.argv[3] != "cuda-bf16-amp-fp32-sensitive-v1"
        or (
            result["precision_profile"] == sys.argv[3]
            and all(item["precision_profile"] == sys.argv[3] for item in candidates)
            and all(item["precision_mode"] == "cuda_bf16_autocast" for item in candidates)
            and all(item["flow_microbatch_size"] == 2048 for item in candidates)
            and all(item["user_authorized_bf16_for_runtime"] is True for item in candidates)
        )
    )
    and all(len(item["diagnostic_entity"]["dr_at_fpr"]) == 6 for item in candidates)
    and isinstance(verdict["passed"], bool)
    and result["target_year_arrays_read"] == 0 and seal["target_year_arrays_read"] == 0
    and result["target_year_paths_enumerated"] == 0 and seal["target_entry_generated"] is False
    and status["state"] == "complete" and status["exit_code"] == 0
    and all((root / name).is_file() for name in required)
)
raise SystemExit(0 if valid else 7)
' "$OUTPUT_ROOT" "$REUSE_COMPLETED_G_A" "$PRECISION_PROFILE"
}

worker() {
    local resume_flag=${1:-} training_started training_finished monitor_pid code
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || { printf '同名运行锁已占用。\n' >&2; return 75; }
    trap 'launcher_status interrupted signal received 130; exit 130' HUP INT TERM
    launcher_status running precheck started null
    validate_static_contract
    validate_inputs
    uv run --no-sync python -c 'import numpy, sklearn, swanlab, torch; assert torch.cuda.is_available()' \
        > "$LAUNCHER_ROOT/dependency-check.txt"
    validate_tracking
    validate_resources
    training_started=$(date +%s.%N)
    resource_monitor &
    monitor_pid=$!
    trap '[[ -z ${monitor_pid:-} ]] || kill "$monitor_pid" 2>/dev/null || true; [[ -z ${monitor_pid:-} ]] || wait "$monitor_pid" 2>/dev/null || true' EXIT
    trap '[[ -z ${monitor_pid:-} ]] || kill "$monitor_pid" 2>/dev/null || true; [[ -z ${monitor_pid:-} ]] || wait "$monitor_pid" 2>/dev/null || true' EXIT
    code=0
    launcher_status running prepare static_contract_and_vendor null
    run_python prepare "$resume_flag"
    if [[ "$REUSE_COMPLETED_G_A" == true ]]; then
        [[ -s "$OUTPUT_ROOT/g-a-migration-receipt.json" \
            && -s "$OUTPUT_ROOT/receipts/selection-G-A.json" \
            && -s "$OUTPUT_ROOT/checkpoints/selected-G-A.pt" ]] \
            || { printf 'G-A 迁移制品不完整，禁止训练 G-B。\n' >&2; return 67; }
        launcher_status running migration G-A_reused_without_retraining null
    else
        launcher_status running resource-calibrate G-A_R0_R1 null
        run_python resource-calibrate "$resume_flag" G-A
        launcher_status running train-unit G-A_remaining_epochs null
        run_python train-unit --resume G-A
    fi
    launcher_status running resource-calibrate G-B_R1_resource_observation null
    run_python resource-calibrate --resume G-B
    launcher_status running train-unit G-B_remaining_epochs null
    run_python train-unit --resume G-B
    launcher_status running aggregate source_metrics_and_verdict null
    run_python aggregate --resume
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
    training_finished=$(date +%s.%N)
    finalize_resource_receipt "$training_started" "$training_finished"
    (( code == 0 )) || return "$code"
    launcher_status running publish aggregate_metrics_only null
    run_python publish-aggregate --resume
    validate_outputs
    launcher_status finished complete grande_protocol_a_source_q0_finished 0
}

worker_entry() {
    local resume_flag=${1:-} controller_log="$LAUNCHER_ROOT/controller.log" code
    [[ "$resume_flag" == --resume ]] && controller_log="$LAUNCHER_ROOT/controller-resume-$(date -u +%Y%m%dT%H%M%SZ).log"
    set +e
    worker "$resume_flag" 2>&1 | tee "$controller_log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    code=${pipeline_status[0]}
    (( code != 0 || pipeline_status[1] == 0 )) || code=${pipeline_status[1]}
    (( code == 0 )) || {
        launcher_status failed controller worker_or_tee_failed "$code"
        return "$code"
    }
}

if [[ ${1:-} == --worker ]]; then
    worker_entry "${2:-}"
    exit $?
fi

resume_flag=""
if [[ ${1:-} == --resume && $# -eq 1 ]]; then
    resume_flag=--resume
elif [[ $# -ne 0 ]]; then
    printf '仅接受可选参数 --resume。\n' >&2
    exit 64
fi
for command in rg uv swanlab screen flock nvidia-smi sha256sum; do
    command -v "$command" >/dev/null 2>&1 || { printf '远端缺少命令：%s\n' "$command" >&2; exit 69; }
done
for path in "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH" \
    "$VENDOR_ROOT/core.py" "$VENDOR_ROOT/LICENSE" "$VENDOR_ROOT/manifest.json"; do
    [[ -s "$path" ]] || { printf '生产文件未完整同步：%s\n' "$path" >&2; exit 67; }
done
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]" \
    || pgrep -f 'python.*[c]h3_grande_protocol_a_source_q0.py' >/dev/null; then
    printf '同名会话或进程已运行。\n' >&2
    exit 75
fi
if [[ -e "$OUTPUT_ROOT" ]]; then
    if [[ -s "$STATUS_PATH" ]] && uv run --no-sync python -c '
import json, pathlib, sys
status = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if status.get("state") == "complete" and status.get("exit_code") == 0 else 1)
' "$STATUS_PATH"; then
        printf '同名运行已完成，不重复启动：%s\n' "$OUTPUT_ROOT"
        exit 0
    fi
    [[ "$resume_flag" == --resume ]] || { printf '同名输出根存在，须显式 --resume。\n' >&2; exit 73; }
elif [[ "$resume_flag" == --resume ]]; then
    printf '输出根不存在，不能恢复。\n' >&2
    exit 73
fi
[[ ! -e "$LAUNCHER_ROOT" || "$resume_flag" == --resume ]] \
    || { printf '启动器证据目录已存在，拒绝覆盖。\n' >&2; exit 73; }
mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
validate_static_contract
validate_inputs
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH ${resume_flag}" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH" \
    "$VENDOR_ROOT/core.py" "$VENDOR_ROOT/LICENSE" "$VENDOR_ROOT/manifest.json" \
    "$PROJECT_ROOT/uv.lock" "$PROJECT_ROOT/pyproject.toml" \
    > "$LAUNCHER_ROOT/input-sha256.txt"
launcher_status prepared launch static_contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker "$resume_flag"
printf 'CH3_GRANDE_PROTOCOL_A_SOURCE_Q0_STARTED session=%s output=%s structures=2 reuse_G_A=%s precision=%s parallelism=1 runtime_cap=none resource_gate=12GiB_GPU/30GiB_RAM/10GiB_disk\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT" "$REUSE_COMPLETED_G_A" "$PRECISION_PROFILE"
