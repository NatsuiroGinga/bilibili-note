#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail
umask 027

readonly PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
readonly RUN_ID=ch4-entity-length-bucket-diagnostic-seed42-v1
readonly SCREEN_NAME=ch4-entity-bucket-s42-v1
readonly OUTPUT_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
readonly STATUS_PATH="$OUTPUT_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/ch4-entity-length-bucket-diagnostic-seed42-v1.json"
readonly TOOL_PATH="$PROJECT_ROOT/tools/ch4_entity_length_bucket_diagnostic.py"
readonly SCRIPT_PATH="$PROJECT_ROOT/scripts/remote_launchers/run_ch4_entity_length_bucket_diagnostic_seed42_v1.sh"
readonly MEMORY_GATE_PATH="$PROJECT_ROOT/tools/memory_admission_gate.sh"
readonly FROZEN_RESULTS_PATH="$PROJECT_ROOT/runs/diagnostics/ch3-full/ch3_full_results.json"
readonly CACHE_ROOT="$PROJECT_ROOT/runs/diagnostics/dijk-repro/cache"
readonly LSPR23_ZIP="$PROJECT_ROOT/data/raw/lspr23-v1/ls23pr_flows.zip"
readonly LSPR24_SCHEMA="$PROJECT_ROOT/data/raw/lspr24-v1/lspr24_v2.parquet"

cd "$PROJECT_ROOT"
source tools/env/activate.sh

write_status() {
    local state=$1
    local stage=$2
    local detail=$3
    local exit_code=$4
    local partial="$STATUS_PATH.partial.$$"
    mkdir -p -- "$OUTPUT_ROOT"
    printf '{\n' > "$partial"
    printf '  "schema_version": "ch4-entity-length-bucket-launcher-status-v1",\n' >> "$partial"
    printf '  "run_id": "%s",\n' "$RUN_ID" >> "$partial"
    printf '  "state": "%s",\n' "$state" >> "$partial"
    printf '  "stage": "%s",\n' "$stage" >> "$partial"
    printf '  "detail": "%s",\n' "$detail" >> "$partial"
    printf '  "exit_code": %s,\n' "$exit_code" >> "$partial"
    printf '  "output_root": "%s",\n' "$OUTPUT_ROOT" >> "$partial"
    printf '  "screening_only": true,\n' >> "$partial"
    printf '  "formal_paper_evidence": false,\n' >> "$partial"
    printf '  "independent_test": false,\n' >> "$partial"
    printf '  "unrelated_gpu_processes_allowed": true,\n' >> "$partial"
    printf '  "updated_at": "%s"\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >> "$partial"
    printf '}\n' >> "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

validate_static_contract() {
    uv run --no-sync python -c '
import json, pathlib, sys
config = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
paths = config.get("paths", {})
valid = (
    config.get("schema_version") == "ch4-entity-length-bucket-diagnostic-config-v1"
    and config.get("run_id") == "ch4-entity-length-bucket-diagnostic-seed42-v1"
    and config.get("seed") == 42
    and config.get("hidden_size") == 192
    and config.get("sequence_length") == 128
    and config.get("batch_size") == 64
    and config.get("learning_rate") == 0.002
    and config.get("weight_decay") == 0.01
    and config.get("gradient_clip_norm") == 1.0
    and config.get("training_steps") == 20000
    and config.get("snapshot_interval_steps") == 1000
    and config.get("averaged_snapshot_count") == 5
    and config.get("required_dependency_versions") == {"safetensors": "0.8.0"}
    and config.get("persist_per_flow_scores") is False
    and paths.get("cache_root") == sys.argv[2]
    and paths.get("lspr23_zip") == sys.argv[3]
    and paths.get("lspr24_schema_parquet") == sys.argv[4]
    and paths.get("frozen_results_json") == sys.argv[5]
    and paths.get("output_root") == sys.argv[6]
)
raise SystemExit(0 if valid else 1)
' "$CONFIG_PATH" "$CACHE_ROOT" "$LSPR23_ZIP" "$LSPR24_SCHEMA" \
        "$FROZEN_RESULTS_PATH" "$OUTPUT_ROOT"
}

write_resource_receipt() {
    nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu \
        --format=csv,noheader,nounits > "$OUTPUT_ROOT/gpu-resource.txt"
    uv run --no-sync python -c '
import json, pathlib, sys
line = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").strip().splitlines()[0]
name, total, free, utilization = [part.strip() for part in line.split(",")]
receipt = {
    "schema_version": "ch4-entity-length-bucket-resource-v1",
    "gpu_name": name,
    "gpu_total_memory_mib": int(total),
    "gpu_free_memory_mib": int(free),
    "gpu_utilization_percent": int(utilization),
    "unrelated_gpu_processes_allowed": True,
    "estimated_peak_gpu_memory_gib": 16,
    "estimated_peak_cpu_memory_gib": 32,
    "estimated_wall_clock_minutes": 20,
}
pathlib.Path(sys.argv[2]).write_text(
    json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
raise SystemExit(0 if int(free) >= 16 * 1024 else 1)
' "$OUTPUT_ROOT/gpu-resource.txt" "$OUTPUT_ROOT/resources.json"
}

validate_runtime_dependencies() {
    uv run --no-sync python -c '
import importlib.metadata
import numpy
import pyarrow
import sklearn
import torch
import safetensors
assert importlib.metadata.version("safetensors") == "0.8.0"
assert torch.cuda.is_available()
print(
    "numpy=" + numpy.__version__,
    "pyarrow=" + pyarrow.__version__,
    "scikit-learn=" + sklearn.__version__,
    "torch=" + torch.__version__,
    "safetensors=" + safetensors.__version__,
)
' > "$OUTPUT_ROOT/dependency-versions.txt"
}

validate_inputs() {
    local name
    for name in X23 y23 X24 y24 I23 M23 I24 M24 s24 d24; do
        if [[ ! -s "$CACHE_ROOT/$name.npy" ]]; then
            printf '冻结缓存缺失且禁止补写：%s\n' "$CACHE_ROOT/$name.npy" >&2
            return 66
        fi
    done
    if [[ ! -s "$LSPR23_ZIP" || ! -s "$LSPR24_SCHEMA" || ! -s "$FROZEN_RESULTS_PATH" ]]; then
        printf 'LSPR23 原始归档、LSPR24 schema 或第三章冻结结果缺失。\n' >&2
        return 66
    fi
}

validate_outputs() {
    uv run --no-sync python -c '
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
result = json.loads((root / "aggregate-results.json").read_text(encoding="utf-8"))
manifest = json.loads(
    (root / "model_package" / "manifest.json").read_text(encoding="utf-8")
)
checkpoints = list((root / "model_package" / "checkpoints").glob("*/*.safetensors"))
valid = (
    result.get("status") == "passed"
    and result.get("research_decision_emitted") is True
    and result.get("seen_all") is True
    and result.get("model_checkpoint_count") == 20
    and result.get("flow_scores_persisted") is False
    and len(checkpoints) == 20
    and manifest.get("file_count") == len(manifest.get("files", []))
)
raise SystemExit(0 if valid else 1)
' "$OUTPUT_ROOT"
}

worker() {
    exec 9> "$OUTPUT_ROOT/worker.lock"
    if ! flock -n 9; then
        printf '同名运行文件锁已被占用：%s\n' "$RUN_ID" >&2
        return 75
    fi
    trap 'write_status interrupted signal received 130; exit 130' HUP INT TERM
    write_status running preflight started null
    validate_static_contract
    validate_inputs
    validate_runtime_dependencies
    write_resource_receipt
    bash "$MEMORY_GATE_PATH" 32 "$RUN_ID" \
        > "$OUTPUT_ROOT/memory-admission-gate.log" 2>&1
    write_status running training started null
    set +e
    uv run --no-sync python "$TOOL_PATH" --config "$CONFIG_PATH" \
        2>&1 | tee "$OUTPUT_ROOT/run.log"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local command_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$command_code" > "$OUTPUT_ROOT/command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$OUTPUT_ROOT/tee-exit-code.txt"
    if [[ "$command_code" -ne 0 ]]; then
        write_status failed training command_failed "$command_code"
        return "$command_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        write_status failed training tee_failed "$tee_code"
        return "$tee_code"
    fi
    validate_outputs
    write_status finished complete diagnostic_and_archive_finished 0
}

worker_entry() {
    set +e
    worker 2>&1 | tee "$OUTPUT_ROOT/controller.log"
    local controller_status=("${PIPESTATUS[@]}")
    set -e
    local worker_code=${controller_status[0]}
    local tee_code=${controller_status[1]}
    printf '%s\n' "$worker_code" > "$OUTPUT_ROOT/controller-command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$OUTPUT_ROOT/controller-tee-exit-code.txt"
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
    printf '启动器不接受参数。\n' >&2
    exit 64
fi
if ! command -v rg >/dev/null 2>&1 || ! command -v uv >/dev/null 2>&1 \
    || ! command -v screen >/dev/null 2>&1 || ! command -v flock >/dev/null 2>&1 \
    || ! command -v nvidia-smi >/dev/null 2>&1; then
    printf '远端缺少 rg、uv、screen、flock 或 nvidia-smi。\n' >&2
    exit 69
fi
if [[ ! -s "$CONFIG_PATH" || ! -s "$TOOL_PATH" || ! -s "$SCRIPT_PATH" \
    || ! -s "$MEMORY_GATE_PATH" ]]; then
    printf '第四章生产文件或内存准入门禁未完整同步。\n' >&2
    exit 67
fi
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名持久会话已在运行：%s\n' "$SCREEN_NAME" >&2
    exit 75
fi
if pgrep -f 'python.*[c]h4_entity_length_bucket_diagnostic.py' >/dev/null; then
    printf '同名诊断进程已在运行：%s\n' "$RUN_ID" >&2
    exit 75
fi
if [[ -e "$OUTPUT_ROOT" ]]; then
    if [[ -s "$STATUS_PATH" ]] && uv run --no-sync python -c '
import json, pathlib, sys
status = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
raise SystemExit(0 if status.get("state") == "finished" else 1)
' "$STATUS_PATH"; then
        printf '同名运行已完成，不重复启动：%s\n' "$OUTPUT_ROOT"
        exit 0
    fi
    printf '同名输出根已存在且未合法完成，保留证据并阻断：%s\n' "$OUTPUT_ROOT" >&2
    exit 73
fi

mkdir -p -- "$OUTPUT_ROOT"
validate_static_contract
validate_inputs
printf '%s\n' "$SCREEN_NAME" > "$OUTPUT_ROOT/screen-session.txt"
printf '%s\n' "$SCRIPT_PATH --worker" > "$OUTPUT_ROOT/command.txt"
sha256sum "$CONFIG_PATH" "$TOOL_PATH" "$SCRIPT_PATH" "$MEMORY_GATE_PATH" \
    "$FROZEN_RESULTS_PATH" > "$OUTPUT_ROOT/input-sha256.txt"
write_status prepared launch static_contract_passed null
screen -dmS "$SCREEN_NAME" bash "$SCRIPT_PATH" --worker
printf 'CH4_ENTITY_BUCKET_DIAGNOSTIC_STARTED session=%s output=%s unrelated_gpu_processes_allowed=true\n' \
    "$SCREEN_NAME" "$OUTPUT_ROOT"
