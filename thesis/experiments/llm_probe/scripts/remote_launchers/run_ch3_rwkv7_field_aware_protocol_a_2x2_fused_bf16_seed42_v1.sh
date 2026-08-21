#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-rwkv7-field-aware-protocol-a-2x2-fused-bf16-seed42-v1
readonly SCREEN_NAME=ch3-rwkv7-r2-k0-fused-bf16-s42-v1
readonly TEMPLATE_CONFIG="$PROJECT_ROOT/configs/$RUN_ID.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_rwkv7_field_aware_protocol_a_2x2_fused_bf16.py"
readonly PURE_TOOL_PATH="$PROJECT_ROOT/tools/ch3_rwkv7_field_aware_protocol_a_2x2_bf16.py"
readonly BACKEND_PATH="$PROJECT_ROOT/tools/rwkv7_k0_fused_backend.py"
readonly BENCHMARK_TOOL="$PROJECT_ROOT/tools/ch3_rwkv7_k0_fused_benchmark.py"
readonly BENCHMARK_CONFIG="$PROJECT_ROOT/configs/ch3-rwkv7-k0-fused-benchmark-v1.json"
readonly VENDOR_MANIFEST="$PROJECT_ROOT/vendor/rwkv7_k0_fused/manifest.json"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_rwkv7_field_aware_protocol_a_2x2_fused_bf16_seed42_v1.sh"
readonly PRECISION_CONFIG="$PROJECT_ROOT/configs/neural-precision-profiles-v1.json"
readonly PRECISION_RUNTIME="$PROJECT_ROOT/tools/neural_precision_runtime.py"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly EXTENSION_BUILD_ROOT="$OUTPUT_ROOT/torch-extensions"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly RESOLVED_CONFIG="$LAUNCHER_ROOT/resolved-config.json"
readonly RESOURCE_RECEIPT="$OUTPUT_ROOT/resource-receipt.json"
readonly RESOURCE_SAMPLES="$OUTPUT_ROOT/resource-samples.tsv"
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=ns3-rwkv-lspr24

cd "$PROJECT_ROOT"
source tools/env/activate.sh

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-rwkv7-k0-fused-bf16-launcher-status-v1",
    "run_id": sys.argv[2], "display_name": "RWKV-7任务化R2-K0 CUDA融合数值变体BF16协议A四格正式资格",
    "state": sys.argv[3], "stage": sys.argv[4], "detail": sys.argv[5],
    "exit_code": None if sys.argv[6] == "null" else int(sys.argv[6]),
    "updated_at_unix": time.time(), "operator_backend": "rwkv7_k0_cuda_fused",
    "transparent_replacement_eligible": False, "independent_numeric_variant_authorized": True,
    "pure_pytorch_checkpoint_compatible": False,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$LAUNCHER_ROOT/status.json" "$RUN_ID" "$state" "$stage" "$detail" "$exit_code"
}

resolve_frozen_receipts() {
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import hashlib, json, math, os, pathlib, sys
template_path, output_path = map(pathlib.Path, sys.argv[1:3])
config = json.loads(template_path.read_text(encoding="utf-8"))
architecture = config["architecture_selection"]
capacity_path = pathlib.Path(architecture["capacity_receipt_path"])
if not capacity_path.is_file(): raise SystemExit("R2/K0结构封印收据缺失")
capacity = json.loads(capacity_path.read_text(encoding="utf-8"))
if not (capacity.get("schema_version") == "ch3-rwkv7-capacity-selection-v1"
        and capacity.get("selected_adapter") == "R2"
        and capacity.get("selected_capacity") == "K0"
        and capacity.get("target_arrays_loaded") == 0
        and architecture.get("selected_capacity") is None
        and architecture.get("capacity_receipt_sha256") is None):
    raise SystemExit("旧结构收据未封印R2/K0或触碰了目标年")
architecture["selected_capacity"] = "K0"
architecture["capacity_receipt_sha256"] = hashlib.sha256(capacity_path.read_bytes()).hexdigest()
variant = config["cuda_fused_variant"]
eligibility_path = pathlib.Path(variant["benchmark_receipt_path"])
if not eligibility_path.is_file(): raise SystemExit("CUDA融合资格收据缺失")
receipt = json.loads(eligibility_path.read_text(encoding="utf-8"))
valid = (
    receipt.get("schema_version") == "ch3-rwkv7-k0-fused-eligibility-v1"
    and receipt.get("benchmark_id") == "ch3-rwkv7-k0-fused-equivalence-speed-v1"
    and receipt.get("synthetic_equivalence_passed") is True
    and receipt.get("lspr23_first_batch_equivalence_passed") is True
    and receipt.get("eligible_for_new_training_identity") is False
    and math.isclose(receipt.get("selection_metric_absolute_delta", -1), 0.004199787, rel_tol=0, abs_tol=5e-7)
    and math.isclose(receipt.get("throughput_ratio_fused_over_pytorch", -1), 8.668993, rel_tol=0, abs_tol=5e-7)
    and math.isclose(receipt.get("peak_reserved_memory_ratio_fused_over_pytorch", -1), 1.099476, rel_tol=0, abs_tol=5e-7)
    and variant["disclosure"]["independent_numeric_variant_authorized"] is True
    and variant["disclosure"]["transparent_replacement_eligible"] is False
    and variant.get("benchmark_receipt_sha256") is None
)
if not valid: raise SystemExit("CUDA融合资格事实或独立数值变体授权不符")
variant["benchmark_receipt_sha256"] = hashlib.sha256(eligibility_path.read_bytes()).hexdigest()
temporary = output_path.with_name(output_path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, output_path)
' "$TEMPLATE_CONFIG" "$RESOLVED_CONFIG"
}

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$TEMPLATE_CONFIG" --validate-config
    resolve_frozen_receipts
    uv run --no-sync python "$TOOL_PATH" --config "$RESOLVED_CONFIG" --validate-config --require-resolved
    uv run --no-sync python "$BACKEND_PATH" --contract > "$LAUNCHER_ROOT/backend-contract.json"
    uv run --no-sync python -c '
import json, pathlib, sys
c = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")); v = c["cuda_fused_variant"]
valid = (c["run_id"] == sys.argv[2] and c["paths"]["output_root"] == sys.argv[3]
         and c["paths"]["extension_build_root"] == sys.argv[4]
         and c["architecture_selection"]["selected_adapter"] == "R2"
         and c["architecture_selection"]["selected_capacity"] == "K0"
         and list(c["capacities"]) == ["K0"] and list(c["cells"]) == ["C00", "C01", "C10", "C11"]
         and c["training"]["epochs"] == 20 and c["training"]["steps_per_epoch"] == 1000
         and c["training"]["checkpoint_interval_optimizer_steps"] == 20
         and c["precision"]["scaler"] is None and c["target_year_arrays_read_before_source_cells_frozen"] == 0
         and c["evaluation"]["dr_fpr_grid"] == [0.001, 0.005, 0.01, 0.02, 0.04, 0.08]
         and c["first_alert_contract"]["axis"] == "exposure_index"
         and v["operator_backend"] == "rwkv7_k0_cuda_fused"
         and v["disclosure"]["checkpoint_compatibility"] == "same_cuda_fused_variant_only"
         and v["disclosure"]["user_authorization_is_effect_evidence"] is False)
raise SystemExit(0 if valid else 78)
' "$RESOLVED_CONFIG" "$RUN_ID" "$OUTPUT_ROOT" "$EXTENSION_BUILD_ROOT"
}

validate_inputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
c=json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")); root=pathlib.Path(c["paths"]["cache_root"])
names=[*c["source_arrays"], *c["target_arrays"]]
raise SystemExit(0 if len(names)==13 and all((root/f"{name}.npy").is_file() for name in names) else 66)
' "$RESOLVED_CONFIG"
}

admit_resources() {
    mkdir -p -- "$OUTPUT_ROOT" "$LAUNCHER_ROOT"
    bash "$MEMORY_GATE_PATH" 30 "$RUN_ID" > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1
    local free_mib cgroup_max cgroup_current cgroup_available disk_fields available_kib used_percent
    free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR==1 {gsub(/ /,"",$0); print $0}')
    if [[ -r /sys/fs/cgroup/memory.max ]]; then
        cgroup_max=$(< /sys/fs/cgroup/memory.max); cgroup_current=$(< /sys/fs/cgroup/memory.current)
    else
        cgroup_max=$(< /sys/fs/cgroup/memory/memory.limit_in_bytes); cgroup_current=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
    fi
    cgroup_available=$((cgroup_max-cgroup_current))
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/,"",$5); print $5}')
    (( free_mib >= 20480 && cgroup_available >= 42949672960 && available_kib >= 26214400 && used_percent < 80 )) || return 69
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
p=pathlib.Path(sys.argv[1]); v={"schema_version":"ch3-rwkv7-k0-fused-bf16-resource-receipt-v1",
"run_started_at_unix":time.time(),"gpu_free_mib_at_admission":int(sys.argv[2]),"cgroup_limit_bytes":int(sys.argv[3]),
"cgroup_current_bytes_at_admission":int(sys.argv[4]),"cgroup_available_bytes_at_admission":int(sys.argv[5]),
"disk_available_kib":int(sys.argv[6]),"disk_used_percent":int(sys.argv[7]),"operator_backend":"rwkv7_k0_cuda_fused",
"resource_measurement_contended":False,"fair_efficiency_evidence":True,"wall_clock_limit":None,"resume_count":0}
t=p.with_name(p.name+f".partial.{os.getpid()}"); t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); os.replace(t,p)
' "$RESOURCE_RECEIPT" "$free_mib" "$cgroup_max" "$cgroup_current" "$cgroup_available" "$available_kib" "$used_percent"
}

resource_monitor() {
    printf 'unix_time\tgpu_used_mib\tcgroup_current_bytes\n' > "$RESOURCE_SAMPLES"
    while true; do
        local gpu_used current
        gpu_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk 'NR==1 {gsub(/ /,"",$0); print $0}')
        [[ -r /sys/fs/cgroup/memory.current ]] && current=$(< /sys/fs/cgroup/memory.current) || current=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
        printf '%s\t%s\t%s\n' "$(date +%s)" "$gpu_used" "$current" >> "$RESOURCE_SAMPLES"
        sleep 5
    done
}

run_logged() {
    local log_path=$1; shift; mkdir -p -- "$(dirname "$log_path")"
    set +e; "$@" 2>&1 | tee "$log_path"; local statuses=("${PIPESTATUS[@]}"); set -e
    printf '%s\n' "${statuses[0]}" > "$log_path.command-exit-code.txt"
    printf '%s\n' "${statuses[1]}" > "$log_path.tee-exit-code.txt"
    (( statuses[1] == 0 )) || return "${statuses[1]}"; return "${statuses[0]}"
}

worker() {
    local resume_flag=${1:-} monitor_pid= code=0
    exec 9> "$LAUNCHER_ROOT/worker.lock"; flock -n 9 || return 75
    trap '[[ -n ${monitor_pid:-} ]] && kill "$monitor_pid" 2>/dev/null || true; launcher_status interrupted signal received 130; exit 130' HUP INT TERM
    validate_static_contract; validate_inputs
    uv run --no-sync python -c 'import numpy, sklearn, swanlab, torch; assert torch.cuda.is_available() and torch.cuda.is_bf16_supported()' > "$LAUNCHER_ROOT/dependency-check.txt"
    admit_resources
    uv run --no-sync python "$BACKEND_PATH" --validate-build-environment --load-extension --build-root "$EXTENSION_BUILD_ROOT" > "$LAUNCHER_ROOT/backend-load-receipt.json"
    launcher_status running source-four-cells cuda_fused_training_started null
    resource_monitor & monitor_pid=$!
    if run_logged "$OUTPUT_ROOT/run${resume_flag:+-resume}.log" uv run --no-sync python "$TOOL_PATH" --config "$RESOLVED_CONFIG" --resource-receipt "$RESOURCE_RECEIPT" ${resume_flag:+--resume}; then code=0; else code=$?; fi
    kill "$monitor_pid" 2>/dev/null || true; wait "$monitor_pid" 2>/dev/null || true; monitor_pid=
    (( code == 0 )) || { launcher_status failed runtime "experiment_exit_${code}" "$code"; return "$code"; }
    uv run --no-sync swanlab ping > "$OUTPUT_ROOT/swanlab-ping.log" 2>&1
    uv run --no-sync swanlab verify > "$OUTPUT_ROOT/swanlab-verify.log" 2>&1
    run_logged "$OUTPUT_ROOT/publish.log" uv run --no-sync python "$TOOL_PATH" --config "$RESOLVED_CONFIG" --publish-only --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" --authorized-swanlab-project "$SWANLAB_PROJECT"
    launcher_status finished complete cuda_fused_protocol_a_finished 0
}

if [[ ${1:-} == --worker ]]; then worker "${2:-}"; exit $?; fi
resume_flag=
if [[ ${1:-} == --resume && $# -eq 1 ]]; then resume_flag=--resume; elif [[ $# -ne 0 ]]; then printf '仅接受可选参数 --resume。\n' >&2; exit 64; fi
for command in rg uv swanlab screen flock nvidia-smi sha256sum; do command -v "$command" >/dev/null 2>&1 || { printf '缺少命令：%s\n' "$command" >&2; exit 69; }; done
for path in "$TEMPLATE_CONFIG" "$TOOL_PATH" "$PURE_TOOL_PATH" "$BACKEND_PATH" "$BENCHMARK_TOOL" "$BENCHMARK_CONFIG" "$VENDOR_MANIFEST" "$SCRIPT_PATH" "$PRECISION_CONFIG" "$PRECISION_RUNTIME" "$MEMORY_GATE_PATH"; do [[ -s "$path" ]] || { printf '生产文件未完整同步：%s\n' "$path" >&2; exit 67; }; done
mkdir -p -- "$PROJECT_ROOT/runs/launchers/.locks" "$LAUNCHER_ROOT"
exec 8> "$PROJECT_ROOT/runs/launchers/.locks/$RUN_ID.lock"; flock -n 8 || exit 75
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]" || pgrep -f 'python.*[c]h3_rwkv7_field_aware_protocol_a_2x2_fused_bf16.py' >/dev/null; then exit 75; fi
validate_static_contract; validate_inputs
if [[ -e "$OUTPUT_ROOT" ]]; then
    if [[ -s "$OUTPUT_ROOT/status.json" ]] && uv run --no-sync python -c 'import json,pathlib,sys; s=json.loads(pathlib.Path(sys.argv[1]).read_text()); raise SystemExit(0 if s.get("state")=="complete" and s.get("exit_code")==0 else 1)' "$OUTPUT_ROOT/status.json"; then exit 0; fi
    resume_flag=--resume
elif [[ "$resume_flag" == --resume ]]; then exit 73; fi
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH ${resume_flag}" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$TEMPLATE_CONFIG" "$RESOLVED_CONFIG" "$TOOL_PATH" "$PURE_TOOL_PATH" "$BACKEND_PATH" "$BENCHMARK_TOOL" "$BENCHMARK_CONFIG" "$VENDOR_MANIFEST" "$SCRIPT_PATH" "$PRECISION_CONFIG" "$PRECISION_RUNTIME" "$MEMORY_GATE_PATH" > "$LAUNCHER_ROOT/input-sha256.txt"
launcher_status prepared launch frozen_receipts_and_backend_identity_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker "$resume_flag"
printf 'CH3_RWKV7_R2_K0_FUSED_BF16_STARTED session=%s output=%s resume=%s\n' "$SCREEN_NAME" "$OUTPUT_ROOT" "${resume_flag:-false}"
