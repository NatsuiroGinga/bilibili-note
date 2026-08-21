#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-rwkv7-field-aware-protocol-a-2x2-seed42-v1-bf16-v1
readonly SCREEN_NAME=ch3-rwkv7-field-aware-protocol-a-bf16-s42-v1
readonly TEMPLATE_CONFIG="$PROJECT_ROOT/configs/$RUN_ID.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_rwkv7_field_aware_protocol_a_2x2_bf16.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_rwkv7_field_aware_protocol_a_2x2_seed42_v1_bf16_v1.sh"
readonly PRECISION_CONFIG="$PROJECT_ROOT/configs/neural-precision-profiles-v1.json"
readonly PRECISION_RUNTIME="$PROJECT_ROOT/tools/neural_precision_runtime.py"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly RESOLVED_CONFIG="$LAUNCHER_ROOT/resolved-config.json"
readonly RESOURCE_RECEIPT="$OUTPUT_ROOT/resource-receipt.json"
readonly RESOURCE_SAMPLES="$OUTPUT_ROOT/resource-samples.tsv"
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=ns3-rwkv-lspr24
readonly GPU_FREE_MIN_MIB=20480
readonly CGROUP_AVAILABLE_MIN_BYTES=42949672960
readonly DISK_FREE_MIN_KIB=26214400

cd "$PROJECT_ROOT"
source tools/env/activate.sh

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-rwkv7-fixed-bf16-launcher-status-v1",
    "run_id": sys.argv[2], "state": sys.argv[3], "stage": sys.argv[4],
    "detail": sys.argv[5], "exit_code": None if sys.argv[6] == "null" else int(sys.argv[6]),
    "updated_at_unix": time.time(), "precision_profile_id": "cuda-bf16-amp-fp32-sensitive-v1",
    "target_previously_accessed": True, "independent_test": False,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$LAUNCHER_ROOT/status.json" "$RUN_ID" "$state" "$stage" "$detail" "$exit_code"
}

resolve_architecture() {
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import hashlib, json, os, pathlib, sys
template_path = pathlib.Path(sys.argv[1])
output_path = pathlib.Path(sys.argv[2])
config = json.loads(template_path.read_text(encoding="utf-8"))
architecture = config["architecture_selection"]
receipt_path = pathlib.Path(architecture["capacity_receipt_path"])
if not receipt_path.is_file():
    raise SystemExit("旧 FP32 capacity_selection_frozen.json 尚未生成，拒绝启动 BF16")
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
selected_capacity = receipt.get("selected_capacity")
valid = (
    receipt.get("schema_version") == "ch3-rwkv7-capacity-selection-v1"
    and receipt.get("selected_adapter") == "R2"
    and selected_capacity in {"K0", "K1", "K2"}
    and receipt.get("target_arrays_loaded") == 0
    and architecture.get("selected_adapter") == "R2"
    and architecture.get("selected_capacity") is None
    and architecture.get("capacity_receipt_sha256") is None
)
if not valid:
    raise SystemExit("旧 FP32 容量选择收据尚未合法封印 R2 与最终 K")
architecture["selected_capacity"] = selected_capacity
architecture["capacity_receipt_sha256"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
temporary = output_path.with_name(output_path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, output_path)
' "$TEMPLATE_CONFIG" "$RESOLVED_CONFIG"
}

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$TEMPLATE_CONFIG" --validate-config
    resolve_architecture
    uv run --no-sync python "$TOOL_PATH" --config "$RESOLVED_CONFIG" --validate-config --require-resolved
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
architecture = config["architecture_selection"]
training = config["training"]
valid = (
    config["run_id"] == sys.argv[2]
    and config["paths"]["output_root"] == sys.argv[3]
    and architecture["selected_adapter"] == "R2"
    and architecture["selected_capacity"] in ["K0", "K1", "K2"]
    and architecture["precision_changed_after_architecture_selection"] is True
    and architecture["bf16_architecture_search_repeated"] is False
    and training["effective_batch_sequences"] == 64
    and training["microbatch_sequences"] == 8
    and training["accumulation_steps"] == 8
    and training["flow_normalization_unit"] == "flow"
    and training["auxiliary_normalization_unit"] == "sequence"
    and training["precision_profile_id"] == "cuda-bf16-amp-fp32-sensitive-v1"
    and config["precision"]["scaler"] is None
    and config["resource_contract"]["wall_clock_limit"] is None
    and list(config["cells"]) == ["C00", "C01", "C10", "C11"]
    and config["swanlab"]["workspace"] == sys.argv[4]
    and config["swanlab"]["project"] == sys.argv[5]
)
raise SystemExit(0 if valid else 78)
' "$RESOLVED_CONFIG" "$RUN_ID" "$OUTPUT_ROOT" "$SWANLAB_WORKSPACE" "$SWANLAB_PROJECT"
}

validate_inputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
root = pathlib.Path(config["paths"]["cache_root"])
names = [*config["source_arrays"], *config["target_arrays"]]
raise SystemExit(0 if len(names) == 13 and all((root / f"{name}.npy").is_file() for name in names) else 66)
' "$RESOLVED_CONFIG"
}

admit_resources() {
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
        printf '无法读取控制组主存，拒绝启动。\n' >&2
        return 69
    fi
    cgroup_available=$((cgroup_max - cgroup_current))
    (( free_mib >= GPU_FREE_MIN_MIB && cgroup_available >= CGROUP_AVAILABLE_MIN_BYTES )) || {
        printf '资源门失败：GPU空闲=%sMiB，控制组可用=%s字节。\n' "$free_mib" "$cgroup_available" >&2
        return 69
    }
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    if [[ ! "$available_kib" =~ ^[0-9]+$ || ! "$used_percent" =~ ^[0-9]+$ ]] \
        || (( available_kib < DISK_FREE_MIN_KIB || used_percent >= 80 )); then
        printf '磁盘资源门失败：available_kib=%s used_percent=%s\n' "$available_kib" "$used_percent" >&2
        return 69
    fi
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-rwkv7-fixed-bf16-resource-receipt-v1",
    "run_started_at_unix": time.time(), "gpu_free_mib_at_admission": int(sys.argv[2]),
    "cgroup_limit_bytes": int(sys.argv[3]), "cgroup_current_bytes_at_admission": int(sys.argv[4]),
    "cgroup_available_bytes_at_admission": int(sys.argv[5]), "disk_available_kib": int(sys.argv[6]),
    "disk_used_percent": int(sys.argv[7]), "actual_parallel_runs_at_admission": 1,
    "minimum_free_gpu_memory_mib": 20480, "precision_profile_id": "cuda-bf16-amp-fp32-sensitive-v1",
    "resource_measurement_contended": False, "fair_efficiency_evidence": True,
    "wall_clock_limit": None,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$RESOURCE_RECEIPT" "$free_mib" "$cgroup_max" "$cgroup_current" "$cgroup_available" "$available_kib" "$used_percent"
}

resource_monitor() {
    printf 'unix_time\tgpu_used_mib\tcgroup_current_bytes\n' > "$RESOURCE_SAMPLES"
    while true; do
        local gpu_used cgroup_current
        gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
        if [[ -r /sys/fs/cgroup/memory.current ]]; then
            cgroup_current=$(< /sys/fs/cgroup/memory.current)
        else
            cgroup_current=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
        fi
        printf '%s\t%s\t%s\n' "$(date +%s)" "$gpu_used" "$cgroup_current" >> "$RESOURCE_SAMPLES"
        sleep 5
    done
}

finalize_resources() {
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
receipt = pathlib.Path(sys.argv[1]); samples = pathlib.Path(sys.argv[2]); result_path = pathlib.Path(sys.argv[3])
value = json.loads(receipt.read_text(encoding="utf-8"))
rows = [tuple(map(int, line.split("\t"))) for line in samples.read_text(encoding="utf-8").splitlines()[1:] if line.count("\t") == 2]
if not rows: raise SystemExit("资源采样为空")
value.update({"finished_at_unix": time.time(), "sample_interval_seconds": 5, "sample_count": len(rows),
              "peak_gpu_used_mib": max(row[1] for row in rows), "peak_cgroup_current_bytes": max(row[2] for row in rows)})
temporary = receipt.with_name(receipt.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); os.replace(temporary, receipt)
if result_path.is_file():
    result = json.loads(result_path.read_text(encoding="utf-8")); result["resource"]["launcher_final_receipt"] = value
    temporary = result_path.with_name(result_path.name + f".partial.{os.getpid()}")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); os.replace(temporary, result_path)
' "$RESOURCE_RECEIPT" "$RESOURCE_SAMPLES" "$OUTPUT_ROOT/aggregate-results.json"
}

run_logged() {
    local log_path=$1
    shift
    mkdir -p -- "$(dirname "$log_path")"
    set +e
    "$@" 2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    printf '%s\n' "${pipeline_status[0]}" > "$log_path.command-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$log_path.tee-exit-code.txt"
    (( pipeline_status[1] == 0 )) || return "${pipeline_status[1]}"
    return "${pipeline_status[0]}"
}

worker() {
    local resume_flag=${1:-} monitor_pid= code=0
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || { printf '同名 BF16 运行锁已占用。\n' >&2; return 75; }
    trap '[[ -n ${monitor_pid:-} ]] && kill "$monitor_pid" 2>/dev/null || true; launcher_status interrupted signal received 130; exit 130' HUP INT TERM
    validate_static_contract
    validate_inputs
    uv run --no-sync python -c 'import numpy, sklearn, swanlab, torch; assert torch.cuda.is_available(); assert torch.cuda.is_bf16_supported()' > "$LAUNCHER_ROOT/dependency-check.txt"
    admit_resources
    launcher_status running source_fixed_architecture source_training_started null
    resource_monitor &
    monitor_pid=$!
    if run_logged "$OUTPUT_ROOT/run${resume_flag:+-resume}.log" \
        uv run --no-sync python "$TOOL_PATH" --config "$RESOLVED_CONFIG" \
        --resource-receipt "$RESOURCE_RECEIPT" ${resume_flag:+--resume}; then
        code=0
    else
        code=$?
    fi
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
    monitor_pid=
    finalize_resources
    if (( code != 0 )); then
        launcher_status failed runtime "experiment_exit_${code}" "$code"
        return "$code"
    fi
    uv run --no-sync swanlab ping > "$OUTPUT_ROOT/swanlab-ping.log" 2>&1
    uv run --no-sync swanlab verify > "$OUTPUT_ROOT/swanlab-verify.log" 2>&1
    run_logged "$OUTPUT_ROOT/publish.log" uv run --no-sync python "$TOOL_PATH" \
        --config "$RESOLVED_CONFIG" --publish-only \
        --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" \
        --authorized-swanlab-project "$SWANLAB_PROJECT"
    launcher_status finished complete protocol_a_bf16_finished 0
}

if [[ ${1:-} == --worker ]]; then
    worker "${2:-}"
    exit $?
fi

resume_flag=
if [[ ${1:-} == --resume && $# -eq 1 ]]; then
    resume_flag=--resume
elif [[ $# -ne 0 ]]; then
    printf '仅接受可选参数 --resume。\n' >&2
    exit 64
fi
for command in rg uv swanlab screen flock nvidia-smi sha256sum; do
    command -v "$command" >/dev/null 2>&1 || { printf '缺少命令：%s\n' "$command" >&2; exit 69; }
done
for path in "$TEMPLATE_CONFIG" "$TOOL_PATH" "$SCRIPT_PATH" "$PRECISION_CONFIG" "$PRECISION_RUNTIME" "$MEMORY_GATE_PATH"; do
    [[ -s "$path" ]] || { printf '生产文件未完整同步：%s\n' "$path" >&2; exit 67; }
done
mkdir -p -- "$PROJECT_ROOT/runs/launchers/.locks" "$LAUNCHER_ROOT"
exec 8> "$PROJECT_ROOT/runs/launchers/.locks/$RUN_ID.lock"
flock -n 8 || { printf '同一 BF16 运行身份的启动器锁已占用。\n' >&2; exit 75; }
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]" \
    || pgrep -f 'python.*[c]h3_rwkv7_field_aware_protocol_a_2x2_bf16.py' >/dev/null; then
    printf '同名 BF16 会话或进程已运行。\n' >&2
    exit 75
fi
validate_static_contract
validate_inputs
if [[ -e "$OUTPUT_ROOT" ]]; then
    if [[ -s "$OUTPUT_ROOT/status.json" ]] && uv run --no-sync python -c '
import json, pathlib, sys
status = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if status.get("state") == "complete" and status.get("exit_code") == 0 else 1)
' "$OUTPUT_ROOT/status.json"; then
        printf '同名 BF16 运行已完成，不重复启动：%s\n' "$OUTPUT_ROOT"
        exit 0
    fi
    resume_flag=--resume
elif [[ "$resume_flag" == --resume ]]; then
    printf 'BF16 输出根不存在，不能恢复。\n' >&2
    exit 73
fi
mkdir -p -- "$OUTPUT_ROOT"
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH ${resume_flag}" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$TEMPLATE_CONFIG" "$RESOLVED_CONFIG" "$TOOL_PATH" "$SCRIPT_PATH" "$PRECISION_CONFIG" "$PRECISION_RUNTIME" "$MEMORY_GATE_PATH" > "$LAUNCHER_ROOT/input-sha256.txt"
launcher_status prepared launch static_contract_and_architecture_receipt_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker "$resume_flag"
printf 'CH3_RWKV7_FIXED_ARCHITECTURE_BF16_STARTED session=%s output=%s resume=%s\n' "$SCREEN_NAME" "$OUTPUT_ROOT" "${resume_flag:-false}"
