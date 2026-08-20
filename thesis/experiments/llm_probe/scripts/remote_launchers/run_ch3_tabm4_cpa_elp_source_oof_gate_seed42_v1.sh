#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-tabm4-cpa-elp-source-oof-gate-seed42-v1
readonly SCREEN_NAME=ch3-tabm4-source-oof-s42-v1
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$OUTPUT_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-tabm4-cpa-elp-source-oof-gate-seed42-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_tabm_cpa_elp_source_oof_gate.py"
readonly BASE_TOOL_PATH="$PROJECT_ROOT/tools/ch3_neural_backbone_source_oof_gate.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_tabm4_cpa_elp_source_oof_gate_seed42_v1.sh"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly MLP_REFERENCE_ROOT="$PROJECT_ROOT/runs/diagnostics/ch4-e1-source-entity-oof-gate-seed42-v1"
readonly XGB_PARENT_ROOT="$PROJECT_ROOT/runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
readonly XGB_RECOVERY_PROOF="$PROJECT_ROOT/runs/recovery/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-for-ch4-xgb-pbc-q0-seed42-v1-v1/parent-recovery-proof.json"
readonly XGB_INPUT_SHA256_RECEIPT="$PROJECT_ROOT/runs/launchers/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1/input-sha256.txt"
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=ns3-rwkv-lspr24
readonly GPU_FREE_MIN_MIB=12288
readonly CGROUP_AVAILABLE_MIN_BYTES=42949672960
readonly DISK_FREE_MIN_KIB=10485760
readonly RESOURCE_RECEIPT_PATH="$OUTPUT_ROOT/resource-receipt.json"
readonly RESOURCE_SAMPLES_PATH="$OUTPUT_ROOT/resource-samples.tsv"
RUN_STARTED_AT=$(date +%s.%N)
readonly RUN_STARTED_AT

cd "$PROJECT_ROOT"
source tools/env/activate.sh

launcher_status() {
    local state=$1 stage=$2 detail=$3 exit_code=$4
    local partial="$LAUNCHER_ROOT/status.json.partial.$$"
    mkdir -p -- "$LAUNCHER_ROOT"
    uv run --no-sync python -c '
import json, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-tabm-source-oof-launcher-status-v1",
    "run_id": sys.argv[2], "state": sys.argv[3], "stage": sys.argv[4],
    "detail": sys.argv[5], "exit_code": None if sys.argv[6] == "null" else int(sys.argv[6]),
    "updated_at_unix": time.time(), "screening_only": True,
    "formal_paper_evidence": False, "target_year_arrays_read": 0,
}
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
' "$partial" "$RUN_ID" "$state" "$stage" "$detail" "$exit_code"
    mv -f -- "$partial" "$LAUNCHER_ROOT/status.json"
}

validate_static_contract() {
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --validate-config
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
resources = config["resource_contract"]
valid = (
    config["allowed_arrays"] == ["X23", "y23", "I23", "M23", "E23"]
    and config["input_contract"]["allowed_arrays"] == config["allowed_arrays"]
    and config["model_key"] == "tabm4"
    and config["candidate"]["ensemble_members"] == 4
    and config["candidate"]["hidden_size"] == 186
    and config["candidate"]["parameter_count"] == 90175
    and config["candidate"]["share_training_batches"] is False
    and config["candidate"]["inference_member_reduction"] == "mean_sigmoid_probability"
    and config["training"]["positive_weight_scope"] == "train_rows_reachable_labels_only"
    and config["training"]["selection_evidence_scope"] == "source_screening_not_independent_oof"
    and config["parent_contract"]["historical_xgb_per_array_hash_persisted"] is False
    and config["target_year_arrays_read"] == 0
    and config["paths"]["output_root"] == sys.argv[2]
    and config["paths"]["mlp_reference_root"] == sys.argv[3]
    and config["paths"]["xgb_parent_root"] == sys.argv[4]
    and config["paths"]["xgb_recovery_proof"] == sys.argv[5]
    and config["paths"]["xgb_input_sha256_receipt"] == sys.argv[6]
    and config["swanlab"]["workspace"] == sys.argv[7]
    and config["swanlab"]["project"] == sys.argv[8]
    and resources == {
        "serial_minimum_free_gpu_memory_gib": 12,
        "serial_minimum_cgroup_available_memory_gib": 40,
        "minimum_free_disk_gib": 10,
        "maximum_parallel_training_units": 1,
        "initial_run_parallelism": 1,
        "parallel_resume_requires_first_unit_resource_receipt": True,
    }
)
raise SystemExit(0 if valid else 78)
' "$CONFIG_PATH" "$OUTPUT_ROOT" "$MLP_REFERENCE_ROOT" "$XGB_PARENT_ROOT" \
        "$XGB_RECOVERY_PROOF" "$XGB_INPUT_SHA256_RECEIPT" \
        "$SWANLAB_WORKSPACE" "$SWANLAB_PROJECT"
}

validate_inputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
root = pathlib.Path(config["paths"]["cache_root"])
arrays = config["input_contract"]["allowed_arrays"]
required = [root / f"{name}.npy" for name in arrays]
parents = [
    pathlib.Path(config["paths"]["mlp_reference_root"]) / "aggregate-results.json",
    pathlib.Path(config["paths"]["mlp_reference_root"]) / "fold-results.json",
    pathlib.Path(config["paths"]["mlp_reference_root"]) / "manifest.json",
    pathlib.Path(config["paths"]["xgb_parent_root"]) / "selection_frozen_xgb2x2.json",
    pathlib.Path(config["paths"]["xgb_recovery_proof"]),
    pathlib.Path(config["paths"]["xgb_input_sha256_receipt"]),
]
raise SystemExit(0 if len(required) == 5 and all(path.is_file() for path in [*required, *parents]) else 66)
' "$CONFIG_PATH"
}

validate_resources() {
    mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
    bash "$MEMORY_GATE_PATH" 30 "$RUN_ID" > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1
    local free_mib cgroup_max cgroup_current cgroup_available available_kib used_percent disk_fields
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
    printf 'available_kib=%s\nused_percent=%s\n' "$available_kib" "$used_percent" \
        > "$LAUNCHER_ROOT/disk-resource.txt"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-tabm-source-oof-resource-receipt-v1",
    "run_started_at_unix": float(sys.argv[2]), "observed_at_unix": time.time(),
    "gpu_free_mib_at_admission": int(sys.argv[3]), "cgroup_limit_bytes": int(sys.argv[4]),
    "cgroup_current_bytes_at_admission": int(sys.argv[5]),
    "cgroup_available_bytes_at_admission": int(sys.argv[6]), "actual_parallelism": 1,
    "maximum_parallelism": 1, "selection_reason": "tabm_initial_run_forced_serial",
    "thresholds": {"serial_gpu_gib": 12, "serial_memory_gib": 40},
    "parallel_faster_claimed": False,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$RESOURCE_RECEIPT_PATH" "$RUN_STARTED_AT" "$free_mib" "$cgroup_max" \
        "$cgroup_current" "$cgroup_available"
}

run_python_phase() {
    local phase=$1 log_path=$2
    shift 2
    mkdir -p -- "$OUTPUT_ROOT"
    set +e
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --phase "$phase" \
        --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" \
        --authorized-swanlab-project "$SWANLAB_PROJECT" "$@" 2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    printf '%s\n' "${pipeline_status[0]}" > "$log_path.command-exit-code.txt"
    printf '%s\n' "${pipeline_status[1]}" > "$log_path.tee-exit-code.txt"
    (( pipeline_status[1] == 0 )) || return "${pipeline_status[1]}"
    return "${pipeline_status[0]}"
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

publish_aggregate() {
    local attempt log_path code
    for attempt in 1 2; do
        mkdir -p -- "$OUTPUT_ROOT/tracking-gates/aggregate/attempt-$attempt"
        uv run --no-sync swanlab ping > "$OUTPUT_ROOT/tracking-gates/aggregate/attempt-$attempt/swanlab-ping.log" 2>&1 || true
        uv run --no-sync swanlab verify > "$OUTPUT_ROOT/tracking-gates/aggregate/attempt-$attempt/swanlab-verify.log" 2>&1 || true
        log_path="$OUTPUT_ROOT/publish-aggregate-attempt-$attempt.log"
        if run_python_phase publish-aggregate "$log_path" --tracking-attempt "$attempt"; then
            return 0
        else
            code=$?
        fi
        (( code == 81 && attempt == 1 )) || return "$code"
    done
}

validate_outputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
result = json.loads((root / "aggregate-results.json").read_text(encoding="utf-8"))
required = ["config.json", "input-identity.json", "fold-assignment-receipt.json", "baseline-receipt.json",
            "resume-receipt.json", "fold-results.json", "aggregate-results.json", "resource-receipt.json",
            "swanlab-receipt.json", "manifest.json", "status.json"]
required += [f"checkpoints/selected-{cell}-fold{fold}.pt" for cell in ("C00", "C11") for fold in range(3)]
required += [f"receipts/unit-{cell}-fold{fold}.json" for cell in ("C00", "C11") for fold in range(3)]
units = [unit for values in result["cells"].values() for unit in values]
verdict = result["mechanical_verdict"]
valid = (
    result["model"]["model_key"] == "tabm4" and result["model"]["parameter_count"] == 90175
    and result["model"]["ensemble_members"] == 4 and result["model"]["elp_shared_p_count"] == 1
    and result["coverage"]["fits_completed"] == 6 and result["input"]["target_year_arrays_read"] == 0
    and result["evidence"]["historical_xgb_per_array_hash_persisted"] is False
    and result["evidence"]["selection_bias_free_independent_oof_claimed"] is False
    and all(unit["share_training_batches"] is False and unit["member_count"] == 4 for unit in units)
    and all(unit["training_label_balance"]["holdout_labels_used_for_weights"] is False for unit in units)
    and sum(bool(verdict[key]) for key in ("source_qualified", "source_rejected", "invalid")) == 1
    and result["resource"]["actual_parallelism"] == 1
    and result["resource"]["optimizer_steps"] == 120000
    and result["resource"]["encoded_sequences"] == 7680000
    and all((root / name).is_file() for name in required)
)
raise SystemExit(0 if valid else 7)
' "$OUTPUT_ROOT"
}

worker() {
    local resume_flag=${1:-} training_started training_finished monitor_pid code cell fold
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    flock -n 9 || { printf '同名运行锁已占用。\n' >&2; return 75; }
    trap 'launcher_status interrupted signal received 130; exit 130' HUP INT TERM
    launcher_status running precheck started null
    validate_static_contract
    validate_inputs
    uv run --no-sync python -c 'import numpy, sklearn, swanlab, torch; assert torch.cuda.is_available()' \
        > "$LAUNCHER_ROOT/dependency-check.txt"
    validate_resources
    launcher_status running prepare source_identity_and_folds_started null
    run_python_phase prepare "$OUTPUT_ROOT/prepare${resume_flag:+-resume}.log" ${resume_flag:+--resume}
    training_started=$(date +%s.%N)
    resource_monitor &
    monitor_pid=$!
    code=0
    : > "$OUTPUT_ROOT/unit-exit-codes.tsv"
    for cell in C00 C11; do
        for fold in 0 1 2; do
            launcher_status running training "${cell}_fold${fold}" null
            mkdir -p -- "$OUTPUT_ROOT/units/${cell}-fold${fold}"
            if run_python_phase train-unit "$OUTPUT_ROOT/units/${cell}-fold${fold}/train${resume_flag:+-resume}.log" \
                --cell "$cell" --fold "$fold" ${resume_flag:+--resume}; then
                code=0
            else
                code=$?
            fi
            printf '%s/fold%s\t%s\n' "$cell" "$fold" "$code" >> "$OUTPUT_ROOT/unit-exit-codes.tsv"
            (( code == 0 )) || break 2
        done
    done
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
    training_finished=$(date +%s.%N)
    finalize_resource_receipt "$training_started" "$training_finished"
    (( code == 0 )) || return "$code"
    launcher_status running aggregate pooled_oof_started null
    run_python_phase aggregate "$OUTPUT_ROOT/aggregate.log" --actual-parallelism 1 \
        --resource-receipt "$RESOURCE_RECEIPT_PATH" ${resume_flag:+--resume}
    launcher_status running publish aggregate_only_started null
    publish_aggregate
    validate_outputs
    launcher_status finished complete source_oof_finished 0
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
for path in "$CONFIG_PATH" "$TOOL_PATH" "$BASE_TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH"; do
    [[ -s "$path" ]] || { printf '生产文件未完整同步：%s\n' "$path" >&2; exit 67; }
done
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]" \
    || pgrep -f 'python.*[c]h3_tabm_cpa_elp_source_oof_gate.py' >/dev/null; then
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
printf '%s\n' "$SCRIPT_PATH --worker ${resume_flag}" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$CONFIG_PATH" "$TOOL_PATH" "$BASE_TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH" \
    "$MLP_REFERENCE_ROOT/aggregate-results.json" "$MLP_REFERENCE_ROOT/fold-results.json" \
    "$MLP_REFERENCE_ROOT/manifest.json" "$XGB_PARENT_ROOT/selection_frozen_xgb2x2.json" \
    "$XGB_RECOVERY_PROOF" "$XGB_INPUT_SHA256_RECEIPT" > "$LAUNCHER_ROOT/input-sha256.txt"
launcher_status prepared launch static_contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker "$resume_flag"
printf 'CH3_TABM4_SOURCE_OOF_STARTED session=%s output=%s units=6 parallelism=1 serial_gate=12GiB/40GiB disk_gate=10GiB\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT"
