#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch3-resmlp2-cpa-elp-source-oof-gate-seed42-v1
readonly SCREEN_NAME=ch3-resmlp2-source-oof-s42-v1
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly STATUS_PATH="$OUTPUT_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch3-resmlp2-cpa-elp-source-oof-gate-seed42-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch3_neural_backbone_source_oof_gate.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch3_resmlp2_cpa_elp_source_oof_gate_seed42_v1.sh"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly MLP_REFERENCE_ROOT="$PROJECT_ROOT/runs/diagnostics/ch4-e1-source-entity-oof-gate-seed42-v1"
readonly XGB_PARENT_ROOT="$PROJECT_ROOT/runs/diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
readonly XGB_RECOVERY_PROOF="$PROJECT_ROOT/runs/recovery/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-for-ch4-xgb-pbc-q0-seed42-v1-v1/parent-recovery-proof.json"
readonly XGB_INPUT_SHA256_RECEIPT="$PROJECT_ROOT/runs/launchers/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1/input-sha256.txt"
readonly SWANLAB_WORKSPACE=mortiswang
readonly SWANLAB_PROJECT=ns3-rwkv-lspr24
readonly GPU_FREE_SERIAL_MIN_MIB=10240
readonly GPU_FREE_PARALLEL_MIN_MIB=24576
readonly CGROUP_AVAILABLE_SERIAL_MIN_BYTES=42949672960
readonly CGROUP_AVAILABLE_PARALLEL_MIN_BYTES=69793218560
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
    "schema_version": "ch3-neural-backbone-source-oof-launcher-status-v1",
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
allowed = config["input_contract"]["allowed_arrays"]
resources = config["resource_contract"]
valid = (
    allowed == ["X23", "y23", "I23", "M23", "E23"]
    and all(name.endswith("23") for name in allowed)
    and config["model_key"] == "resmlp2"
    and config["candidate"]["parameter_count"] == 89796
    and config["candidate"]["residual_blocks"] == 1
    and config["candidate"]["hidden_size"] == 139
    and config["target_year_arrays_read"] == 0
    and config["swanlab"]["workspace"] == sys.argv[2]
    and config["swanlab"]["project"] == sys.argv[3]
    and config["paths"]["output_root"] == sys.argv[4]
    and config["paths"]["mlp_reference_root"] == sys.argv[5]
    and config["paths"]["xgb_parent_root"] == sys.argv[6]
    and config["paths"]["xgb_recovery_proof"] == sys.argv[7]
    and config["paths"]["xgb_input_sha256_receipt"] == sys.argv[8]
    and config["parent_contract"]["historical_xgb_per_array_hash_persisted"] is False
    and config["training"]["positive_weight_scope"] == "train_rows_reachable_labels_only"
    and config["training"]["selection_evidence_scope"] == "source_screening_not_independent_oof"
    and resources["serial_minimum_free_gpu_memory_gib"] == 10
    and resources["serial_minimum_cgroup_available_memory_gib"] == 40
    and resources["parallel_minimum_free_gpu_memory_gib"] == 24
    and resources["parallel_minimum_cgroup_available_memory_gib"] == 65
    and resources["minimum_free_disk_gib"] == 10
    and resources["maximum_parallel_training_units"] == 2
    and resources["adaptive_parallelism"] is True
)
raise SystemExit(0 if valid else 78)
' "$CONFIG_PATH" "$SWANLAB_WORKSPACE" "$SWANLAB_PROJECT" "$OUTPUT_ROOT" \
    "$MLP_REFERENCE_ROOT" "$XGB_PARENT_ROOT" "$XGB_RECOVERY_PROOF" \
    "$XGB_INPUT_SHA256_RECEIPT"
}

validate_inputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
root = pathlib.Path(config["paths"]["cache_root"])
allowed = config["input_contract"]["allowed_arrays"]
required = [root / f"{name}.npy" for name in allowed]
parent_paths = [
    pathlib.Path(config["paths"]["mlp_reference_root"]) / "aggregate-results.json",
    pathlib.Path(config["paths"]["mlp_reference_root"]) / "fold-results.json",
    pathlib.Path(config["paths"]["mlp_reference_root"]) / "manifest.json",
    pathlib.Path(config["paths"]["xgb_parent_root"]) / "selection_frozen_xgb2x2.json",
    pathlib.Path(config["paths"]["xgb_recovery_proof"]),
    pathlib.Path(config["paths"]["xgb_input_sha256_receipt"]),
]
valid = len(required) == 5 and all(path.is_file() for path in [*required, *parent_paths])
raise SystemExit(0 if valid else 66)
' "$CONFIG_PATH"
}

validate_resources() {
    mkdir -p -- "$LAUNCHER_ROOT"
    bash "$MEMORY_GATE_PATH" 30 "$RUN_ID" > "$LAUNCHER_ROOT/memory-admission-gate.log" 2>&1
    local free_mib cgroup_max cgroup_current cgroup_available actual_parallelism selection_reason
    free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | awk 'NR == 1 {gsub(/ /, "", $0); print $0}')
    if [[ -r /sys/fs/cgroup/memory.max ]]; then
        cgroup_max=$(< /sys/fs/cgroup/memory.max)
        cgroup_current=$(< /sys/fs/cgroup/memory.current)
    elif [[ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]]; then
        cgroup_max=$(< /sys/fs/cgroup/memory/memory.limit_in_bytes)
        cgroup_current=$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)
    else
        printf '无法读取 cgroup 主存上限，拒绝启动。\n' >&2
        return 69
    fi
    if [[ ! "$free_mib" =~ ^[0-9]+$ || ! "$cgroup_max" =~ ^[0-9]+$ || ! "$cgroup_current" =~ ^[0-9]+$ ]]; then
        printf '资源读数不是有限整数，拒绝启动。\n' >&2
        return 69
    fi
    cgroup_available=$((cgroup_max - cgroup_current))
    if (( free_mib >= GPU_FREE_PARALLEL_MIN_MIB && cgroup_available >= CGROUP_AVAILABLE_PARALLEL_MIN_BYTES )); then
        actual_parallelism=2
        selection_reason=parallel_thresholds_satisfied
    elif (( free_mib >= GPU_FREE_SERIAL_MIN_MIB && cgroup_available >= CGROUP_AVAILABLE_SERIAL_MIN_BYTES )); then
        actual_parallelism=1
        selection_reason=parallel_thresholds_not_satisfied_serial_thresholds_satisfied
    else
        printf '资源门失败：GPU空闲=%sMiB，cgroup可用=%s字节。\n' "$free_mib" "$cgroup_available" >&2
        return 69
    fi
    nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu --format=csv,noheader,nounits \
        > "$LAUNCHER_ROOT/gpu-resource.txt"
    local disk_fields available_kib used_percent
    disk_fields=$(df -Pk "$PROJECT_ROOT" | tail -n 1)
    available_kib=$(printf '%s\n' "$disk_fields" | awk '{print $4}')
    used_percent=$(printf '%s\n' "$disk_fields" | awk '{gsub(/%/, "", $5); print $5}')
    if [[ ! "$available_kib" =~ ^[0-9]+$ || ! "$used_percent" =~ ^[0-9]+$ ]] \
        || (( available_kib < DISK_FREE_MIN_KIB || used_percent >= 80 )); then
        printf '磁盘资源门失败：available_kib=%s used_percent=%s\n' "$available_kib" "$used_percent" >&2
        return 69
    fi
    printf 'available_kib=%s\nused_percent=%s\n' "$available_kib" "$used_percent" \
        > "$LAUNCHER_ROOT/disk-resource.txt"
    printf '%s\n' "$actual_parallelism" > "$LAUNCHER_ROOT/actual-parallelism.txt"
    uv run --no-sync python -c '
import json, os, pathlib, sys, time
path = pathlib.Path(sys.argv[1])
value = {
    "schema_version": "ch3-neural-backbone-source-oof-resource-receipt-v1",
    "run_started_at_unix": float(sys.argv[2]),
    "observed_at_unix": time.time(),
    "gpu_free_mib_at_admission": int(sys.argv[3]),
    "cgroup_limit_bytes": int(sys.argv[4]),
    "cgroup_current_bytes_at_admission": int(sys.argv[5]),
    "cgroup_available_bytes_at_admission": int(sys.argv[6]),
    "actual_parallelism": int(sys.argv[7]),
    "maximum_parallelism": 2,
    "selection_reason": sys.argv[8],
    "thresholds": {"serial_gpu_gib": 10, "serial_memory_gib": 40,
                   "parallel_gpu_gib": 24, "parallel_memory_gib": 65},
    "parallel_faster_claimed": False,
}
temporary = path.with_name(path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, path)
' "$RESOURCE_RECEIPT_PATH" "$RUN_STARTED_AT" "$free_mib" "$cgroup_max" "$cgroup_current" \
        "$cgroup_available" "$actual_parallelism" "$selection_reason"
}

run_python_phase() {
    local phase=$1 log_path=$2
    shift 2
    mkdir -p -- "$OUTPUT_ROOT"
    set +e
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --phase "$phase" \
        --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" \
        --authorized-swanlab-project "$SWANLAB_PROJECT" \
        "$@" 2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$log_path.command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$log_path.tee-exit-code.txt"
    if [[ "$tee_code" -ne 0 ]]; then
        return "$tee_code"
    fi
    return "$command_code"
}

run_training_unit() {
    local cell=$1 fold=$2 resume_flag=$3
    local unit_root="$OUTPUT_ROOT/units/${cell}-fold${fold}"
    local log_path="$unit_root/train.log"
    if [[ "$resume_flag" == --resume ]]; then
        log_path="$unit_root/train-resume-$(date -u +%Y%m%dT%H%M%SZ).log"
    fi
    mkdir -p -- "$unit_root"
    run_python_phase train-unit "$log_path" --cell "$cell" --fold "$fold" ${resume_flag:+--resume}
}

run_training_batch() {
    local resume_flag=$1
    shift
    local specifications=("$@") pids=() labels=() specification cell fold pid code first_failure=0 index
    for specification in "${specifications[@]}"; do
        cell=${specification%%:*}
        fold=${specification##*:}
        run_training_unit "$cell" "$fold" "$resume_flag" &
        pid=$!
        pids+=("$pid")
        labels+=("$cell/fold$fold")
    done
    for index in "${!pids[@]}"; do
        if wait "${pids[$index]}"; then
            code=0
        else
            code=$?
        fi
        printf '%s\t%s\n' "${labels[$index]}" "$code" >> "$OUTPUT_ROOT/unit-exit-codes.tsv"
        if (( code != 0 && first_failure == 0 )); then
            first_failure=$code
        fi
    done
    return "$first_failure"
}

run_all_training_units() {
    local resume_flag=$1 parallelism=$2 index=0
    local units=(C00:0 C00:1 C00:2 C11:0 C11:1 C11:2)
    : > "$OUTPUT_ROOT/unit-exit-codes.tsv"
    while (( index < ${#units[@]} )); do
        if (( parallelism == 2 && index + 1 < ${#units[@]} )); then
            run_training_batch "$resume_flag" "${units[$index]}" "${units[$((index + 1))]}" || return $?
            index=$((index + 2))
        else
            run_training_batch "$resume_flag" "${units[$index]}" || return $?
            index=$((index + 1))
        fi
    done
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

finalize_training_resource_receipt() {
    local training_started=$1 training_finished=$2
    uv run --no-sync python -c '
import json, os, pathlib, sys
receipt_path, samples_path = map(pathlib.Path, sys.argv[1:3])
value = json.loads(receipt_path.read_text(encoding="utf-8"))
rows = []
for line in samples_path.read_text(encoding="utf-8").splitlines()[1:]:
    fields = line.split("\t")
    if len(fields) == 3:
        rows.append(tuple(int(item) for item in fields))
if not rows:
    raise SystemExit("资源采样为空")
value.update({
    "training_started_at_unix": float(sys.argv[3]),
    "training_finished_at_unix": float(sys.argv[4]),
    "training_wall_seconds": float(sys.argv[4]) - float(sys.argv[3]),
    "sample_interval_seconds": 5,
    "sample_count": len(rows),
    "peak_gpu_used_mib_overall": max(row[1] for row in rows),
    "peak_cgroup_current_bytes_overall": max(row[2] for row in rows),
})
temporary = receipt_path.with_name(receipt_path.name + f".partial.{os.getpid()}")
temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.replace(temporary, receipt_path)
' "$RESOURCE_RECEIPT_PATH" "$RESOURCE_SAMPLES_PATH" "$training_started" "$training_finished"
}

run_swanlab_preinit_gate() {
    local attempt=$1
    local gate_root="$OUTPUT_ROOT/tracking-gates/aggregate/attempt-$attempt"
    mkdir -p -- "$gate_root"
    set +e
    uv run --no-sync swanlab ping > "$gate_root/swanlab-ping.log" 2>&1
    local ping_code=$?
    uv run --no-sync swanlab verify > "$gate_root/swanlab-verify.log" 2>&1
    local verify_code=$?
    set -e
    printf '%s\n' "$ping_code" > "$gate_root/swanlab-ping.exit-code.txt"
    printf '%s\n' "$verify_code" > "$gate_root/swanlab-verify.exit-code.txt"
}

publish_attempt() {
    local attempt=$1
    run_swanlab_preinit_gate "$attempt"
    local log_path="$OUTPUT_ROOT/publish-aggregate-attempt-$attempt.log"
    set +e
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" --phase publish-aggregate \
        --tracking-attempt "$attempt" \
        --authorized-swanlab-workspace "$SWANLAB_WORKSPACE" \
        --authorized-swanlab-project "$SWANLAB_PROJECT" 2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$log_path.command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$log_path.tee-exit-code.txt"
    if [[ "$tee_code" -ne 0 ]]; then
        return "$tee_code"
    fi
    return "$command_code"
}

publish_aggregate() {
    local first_code
    if publish_attempt 1; then
        return 0
    else
        first_code=$?
    fi
    if [[ "$first_code" -ne 81 ]]; then
        return "$first_code"
    fi
    printf 'SwanLab 首次初始化返回 401，仅在新进程有界重试一次。\n'
    publish_attempt 2
}

validate_outputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
status = json.loads((root / "status.json").read_text(encoding="utf-8"))
result = json.loads((root / "aggregate-results.json").read_text(encoding="utf-8"))
required = [
    "config.json", "input-identity.json", "fold-assignment-receipt.json",
    "baseline-receipt.json", "resume-receipt.json", "fold-results.json", "aggregate-results.json",
    "resource-receipt.json", "swanlab-receipt.json", "manifest.json", "status.json",
]
required += [f"checkpoints/selected-{cell}-fold{fold}.pt" for cell in ("C00", "C11") for fold in range(3)]
required += [f"receipts/unit-{cell}-fold{fold}.json" for cell in ("C00", "C11") for fold in range(3)]
required += [f"units/{cell}-fold{fold}/status.json" for cell in ("C00", "C11") for fold in range(3)]
resource = result["resource"]
verdict = result["mechanical_verdict"]
xgb = result["baselines"]["xgb"]
valid = (
    status.get("state") == "complete"
    and status.get("exit_code") == 0
    and result["coverage"]["fits_completed"] == 6
    and result["coverage"]["each_entity_oof_exactly_once"] is True
    and result["coverage"]["train_holdout_entity_intersection"] == 0
    and result["input"]["arrays"] == ["X23", "y23", "I23", "M23", "E23"]
    and result["input"]["target_year_arrays_read"] == 0
    and result["model"]["model_key"] == "resmlp2"
    and result["model"]["parameter_count"] == 89796
    and result["evidence"]["holdout_epoch_selection_used"] is True
    and result["evidence"]["selection_bias_free_independent_oof_claimed"] is False
    and result["evidence"]["historical_xgb_per_array_hash_persisted"] is False
    and result["evidence"]["qualification_evidence_limitations"] == [
        "historical_xgb_per_array_hash_not_persisted",
        "holdout_epoch_selection_bias",
    ]
    and result["baselines"]["historical_xgb_per_array_hash_persisted"] is False
    and xgb["historical_xgb_per_array_hash_persisted"] is False
    and xgb["historical_xgb_current_array_cryptographic_identity_claimed"] is False
    and xgb["current_arrays_match_mlp_e1_input_identity"] is True
    and len(xgb["effective_config_receipts_sha256"]) == 64
    and len(xgb["source_fold_models"]) == 3
    and all(
        len(model["sha256"]) == 64 and model["num_boosted_rounds"] == 800
        for model in xgb["source_fold_models"].values()
    )
    and sum(bool(verdict[key]) for key in ("source_qualified", "source_rejected", "invalid")) == 1
    and verdict["invalid"] is False
    and result["artifact_policy"]["per_flow_scores_persisted"] is False
    and result["artifact_policy"]["per_entity_scores_persisted"] is False
    and resource["maximum_parallel_training_units"] == 2
    and resource["actual_parallelism"] in (1, 2)
    and resource["launcher_receipt"]["training_wall_seconds"] > 0
    and resource["launcher_receipt"]["peak_gpu_used_mib_overall"] >= 0
    and resource["launcher_receipt"]["peak_cgroup_current_bytes_overall"] > 0
    and resource["optimizer_steps"] == 120000
    and resource["sequences_per_step"] == 64
    and resource["encoded_sequences"] == 7680000
    and resource["encoded_effective_flows"] > 0
    and all(
        unit["training_label_balance"]["scope"] == "train_rows_reachable_labels_only"
        and unit["training_label_balance"]["holdout_labels_used_for_weights"] is False
        and unit["training_label_balance"]["train_sequences"] > 0
        and unit["training_label_balance"]["train_effective_flows"] > 0
        and unit["training_label_balance"]["flow_positive_weight"] > 0
        and unit["training_label_balance"]["sequence_positive_weight"] > 0
        for units in result["cells"].values() for unit in units
    )
    and all(unit["wall_seconds"] is not None and unit["resource"] for units in result["cells"].values() for unit in units)
    and all((root / name).is_file() for name in required)
)
raise SystemExit(0 if valid else 7)
' "$OUTPUT_ROOT"
}

worker() {
    local resume_flag=${1:-}
    exec 9> "$LAUNCHER_ROOT/worker.lock"
    if ! flock -n 9; then
        printf '同名运行锁已占用。\n' >&2
        return 75
    fi
    trap 'launcher_status interrupted signal received 130; exit 130' HUP INT TERM
    launcher_status running precheck started null
    validate_static_contract
    validate_inputs
    uv run --no-sync python -c 'import numpy, sklearn, swanlab, torch; assert torch.cuda.is_available()' \
        > "$LAUNCHER_ROOT/dependency-check.txt"
    if [[ "$resume_flag" == --resume && -s "$RESOURCE_RECEIPT_PATH" ]]; then
        cp -p -- "$RESOURCE_RECEIPT_PATH" \
            "$OUTPUT_ROOT/resource-receipt-before-resume-$(date -u +%Y%m%dT%H%M%SZ).json"
    fi
    validate_resources
    local actual_parallelism training_started training_finished monitor_pid training_code
    actual_parallelism=$(< "$LAUNCHER_ROOT/actual-parallelism.txt")
    launcher_status running prepare source_identity_and_folds_started null
    run_python_phase prepare "$OUTPUT_ROOT/prepare${resume_flag:+-resume}.log" ${resume_flag:+--resume}
    launcher_status running training "six_units_parallelism_${actual_parallelism}" null
    training_started=$(date +%s.%N)
    resource_monitor &
    monitor_pid=$!
    set +e
    run_all_training_units "$resume_flag" "$actual_parallelism"
    training_code=$?
    set -e
    kill "$monitor_pid" 2>/dev/null || true
    wait "$monitor_pid" 2>/dev/null || true
    training_finished=$(date +%s.%N)
    finalize_training_resource_receipt "$training_started" "$training_finished"
    if (( training_code != 0 )); then
        return "$training_code"
    fi
    launcher_status running aggregate pooled_oof_started null
    run_python_phase aggregate "$OUTPUT_ROOT/aggregate.log" \
        --actual-parallelism "$actual_parallelism" --resource-receipt "$RESOURCE_RECEIPT_PATH" \
        ${resume_flag:+--resume}
    launcher_status running publish aggregate_only_started null
    publish_aggregate
    validate_outputs
    launcher_status finished complete source_oof_finished 0
}

worker_entry() {
    local resume_flag=${1:-}
    local controller_log="$LAUNCHER_ROOT/controller.log"
    if [[ "$resume_flag" == --resume ]]; then
        controller_log="$LAUNCHER_ROOT/controller-resume-$(date -u +%Y%m%dT%H%M%SZ).log"
    fi
    set +e
    worker "$resume_flag" 2>&1 | tee "$controller_log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local worker_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$worker_code" > "$controller_log.command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$controller_log.tee-exit-code.txt"
    if [[ "$worker_code" -ne 0 ]]; then
        launcher_status failed controller worker_failed "$worker_code"
        return "$worker_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        launcher_status failed controller tee_failed "$tee_code"
        return "$tee_code"
    fi
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
    if ! command -v "$command" >/dev/null 2>&1; then
        printf '远端缺少命令：%s\n' "$command" >&2
        exit 69
    fi
done
for path in "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH"; do
    if [[ ! -s "$path" ]]; then
        printf '生产文件未完整同步：%s\n' "$path" >&2
        exit 67
    fi
done
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名持久会话已运行：%s\n' "$SCREEN_NAME" >&2
    exit 75
fi
if pgrep -f 'python.*[c]h3_neural_backbone_source_oof_gate.py' >/dev/null; then
    printf '同名门禁进程已运行。\n' >&2
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
    if [[ "$resume_flag" != --resume ]]; then
        printf '同名输出根已存在且未完成；须显式 --resume，禁止覆盖：%s\n' "$OUTPUT_ROOT" >&2
        exit 73
    fi
elif [[ "$resume_flag" == --resume ]]; then
    printf '输出根不存在，不能恢复：%s\n' "$OUTPUT_ROOT" >&2
    exit 73
fi
if [[ -e "$LAUNCHER_ROOT" && "$resume_flag" != --resume ]]; then
    printf '同名启动器目录已存在，保留证据并阻断：%s\n' "$LAUNCHER_ROOT" >&2
    exit 73
fi
mkdir -p -- "$LAUNCHER_ROOT" "$OUTPUT_ROOT"
validate_static_contract
validate_inputs
printf '%s\n' "$SCREEN_NAME" > "$LAUNCHER_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker ${resume_flag}" > "$LAUNCHER_ROOT/command.txt"
sha256sum "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH" \
    "$MLP_REFERENCE_ROOT/aggregate-results.json" "$MLP_REFERENCE_ROOT/fold-results.json" \
    "$MLP_REFERENCE_ROOT/manifest.json" "$XGB_PARENT_ROOT/selection_frozen_xgb2x2.json" \
    "$XGB_RECOVERY_PROOF" "$XGB_INPUT_SHA256_RECEIPT" \
    > "$LAUNCHER_ROOT/input-sha256.txt"
launcher_status prepared launch static_contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker "$resume_flag"
printf 'CH3_RESMLP2_SOURCE_OOF_STARTED session=%s output=%s units=6 adaptive_parallelism=1_or_2 serial_gate=10GiB/40GiB parallel_gate=24GiB/65GiB disk_free_gate_gib=10\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT"
