#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1
set -Eeuo pipefail
export OMP_NUM_THREADS=1

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
CONFIG="$PROJECT_ROOT/configs/ch3-cuda-rwkv-raw83-qualification-seed42-v1.json"
ENTRY="$PROJECT_ROOT/tools/ch3_cuda_rwkv_raw83_qualification.py"
RUN_ID="ch3-cuda-rwkv-raw83-qualification-seed42-v1"
RUN_ROOT="$PROJECT_ROOT/runs/diagnostics/$RUN_ID"
LAUNCHER_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
SOURCE_MANIFEST="$PROJECT_ROOT/runs/data-prepared/ch3-protocol-a-raw83-shared-v1/generations/source-v1/dataset-manifest.json"
TARGET_MANIFEST="$PROJECT_ROOT/runs/data-prepared/ch3-protocol-a-raw83-target-v1/generations/year-v1/dataset-manifest.json"
SOURCE_SEAL="$RUN_ROOT/seals/source-qualification-seal.json"
SOURCE_RESOURCE_SAMPLES="$RUN_ROOT/resource-samples.tsv"
TARGET_RESOURCE_SAMPLES="$RUN_ROOT/target-resource-samples.tsv"
ACTION="${1:-source}"
RESOURCE_SAMPLES="$SOURCE_RESOURCE_SAMPLES"
if [ "$ACTION" = "target" ]; then
    RESOURCE_SAMPLES="$TARGET_RESOURCE_SAMPLES"
fi
LOCK_PATH="$LAUNCHER_ROOT/run.lock"
LOCK_TOKEN=""
RESOURCE_ADMISSION_RECEIPT=""
ACTIVE_SAMPLER_PID=""

cd "$PROJECT_ROOT"
source tools/env/activate.sh
export OMP_NUM_THREADS=1
CUDA_HOME="/usr/local/cuda"
if [ ! -d "$CUDA_HOME" ]; then
    printf '%s\n' "CUDA-RWKV 冻结 CUDA_HOME 不是可用目录：$CUDA_HOME" >&2
    exit 69
fi
CUDA_HOME_RESOLVED="$(cd -P "$CUDA_HOME" && pwd)"
case "$CUDA_HOME_RESOLVED" in
    /usr/local/cuda|/usr/local/cuda-13.0)
        ;;
    *)
        printf '%s\n' "CUDA-RWKV CUDA_HOME 物理落点非法：$CUDA_HOME_RESOLVED" >&2
        exit 69
        ;;
esac
CUDA_NVCC="$CUDA_HOME/bin/nvcc"
CUDA_LIBRARY_PATH="$CUDA_HOME/lib64"
if [ ! -x "$CUDA_NVCC" ]; then
    printf '%s\n' "CUDA-RWKV 冻结 nvcc 不可执行：$CUDA_NVCC" >&2
    exit 69
fi
if [ ! -d "$CUDA_LIBRARY_PATH" ]; then
    printf '%s\n' "CUDA-RWKV 冻结 CUDA lib64 目录缺失：$CUDA_LIBRARY_PATH" >&2
    exit 69
fi
export CUDA_HOME
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_LIBRARY_PATH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
NVCC_DISCOVERED="$(command -v nvcc || true)"
if [ "$NVCC_DISCOVERED" != "$CUDA_NVCC" ]; then
    printf '%s\n' "CUDA-RWKV nvcc PATH 首命中漂移：$NVCC_DISCOVERED" >&2
    exit 69
fi
mkdir -p "$RUN_ROOT" "$LAUNCHER_ROOT"

release_run_lock() {
    if [ -n "$ACTIVE_SAMPLER_PID" ]; then
        kill "$ACTIVE_SAMPLER_PID" 2>/dev/null || true
        wait "$ACTIVE_SAMPLER_PID" 2>/dev/null || true
        ACTIVE_SAMPLER_PID=""
    fi
    if [ -n "$LOCK_TOKEN" ] && [ -f "$LOCK_PATH/token" ]; then
        local observed_token
        observed_token="$(< "$LOCK_PATH/token")"
        if [ "$observed_token" = "$LOCK_TOKEN" ]; then
            rm -f "$LOCK_PATH/owner.json" "$LOCK_PATH/token"
            rmdir "$LOCK_PATH" 2>/dev/null || true
        fi
    fi
}

acquire_run_lock() {
    if ! mkdir "$LOCK_PATH" 2>/dev/null; then
        printf '%s\n' "CUDA-RWKV 原子运行锁已被占用：$LOCK_PATH" >&2
        return 75
    fi
    if [ ! -r /proc/sys/kernel/random/uuid ]; then
        printf '%s\n' "CUDA-RWKV 无法生成原子运行锁令牌" >&2
        return 1
    fi
    LOCK_TOKEN="$(< /proc/sys/kernel/random/uuid)"
    printf '%s\n' "$LOCK_TOKEN" > "$LOCK_PATH/token"
    printf '{"schema_version":"cuda-rwkv-run-lock-owner-v1","run_id":"%s","action":"%s","token":"%s","launcher_pid":%s}\n' \
        "$RUN_ID" "$ACTION" "$LOCK_TOKEN" "$$" > "$LOCK_PATH/owner.json.partial.$$"
    mv "$LOCK_PATH/owner.json.partial.$$" "$LOCK_PATH/owner.json"
}

run_static_gates() {
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --validate-config
    if [ "$ACTION" = "source" ] && [ ! -f "$RUN_ROOT/dependency-closure.json" ]; then
        uv run --no-sync python "$ENTRY" --config "$CONFIG" --write-dependency-closure
    fi
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --check-dependency-closure
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --check-target-isolation
}

run_compute_resource_gates() {
    local mode="$1"
    local receipt_path="$RUN_ROOT/resource-admission/${LOCK_TOKEN}-${mode}.json"
    mkdir -p "$RUN_ROOT/resource-admission"
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --check-storage-gate
    MEMORY_SAFETY_MARGIN=1 bash tools/memory_admission_gate.sh 40 "$RUN_ID"
    local gpu_rows gpu_free_mib compute_pids
    gpu_rows="$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits)"
    if [ "$(printf '%s\n' "$gpu_rows" | awk 'NF{count++} END{print count+0}')" -ne 1 ]; then
        printf '%s\n' "CUDA-RWKV 资源门要求唯一可见 GPU" >&2
        return 1
    fi
    gpu_free_mib="$(printf '%s\n' "$gpu_rows" | awk 'NF{gsub(/ /, "", $0); print int($0)}')"
    if [ "$gpu_free_mib" -lt 20480 ]; then
        printf '%s\n' "CUDA-RWKV 可用显存 ${gpu_free_mib} MiB < 20480 MiB" >&2
        return 1
    fi
    compute_pids="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | awk 'NF && $1 != "No" {print $1}')"
    if [ -n "$compute_pids" ]; then
        printf '%s\n' "CUDA-RWKV 检测到未授权 GPU 计算进程，拒绝启动" >&2
        return 1
    fi
    uv run --no-sync python "$ENTRY" --config "$CONFIG" \
        --write-resource-admission-receipt \
        --resource-action "$mode" \
        --resource-admission-receipt "$receipt_path" \
        --run-lock-path "$LOCK_PATH" \
        --run-lock-token "$LOCK_TOKEN" >/dev/null
    RESOURCE_ADMISSION_RECEIPT="$receipt_path"
}

sample_resources() {
    local stop_path="$1"
    local stopped_path="$2"
    local mode="$3"
    if [ ! -s "$RESOURCE_SAMPLES" ]; then
        printf 'timestamp\tgpu_process_memory_mib\tcgroup_memory_bytes\tdisk_available_kib\n' >> "$RESOURCE_SAMPLES"
    fi
    while [ ! -f "$stop_path" ]; do
        local timestamp gpu_mib cgroup_bytes disk_kib
        timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        gpu_mib="$(nvidia-smi --query-compute-apps=used_memory --format=csv,noheader,nounits 2>/dev/null | awk 'NF && $1 != "No" {sum+=$1} END{print int(sum+0)}')"
        if [ -r /sys/fs/cgroup/memory.current ]; then
            cgroup_bytes="$(< /sys/fs/cgroup/memory.current)"
        elif [ -r /sys/fs/cgroup/memory/memory.usage_in_bytes ]; then
            cgroup_bytes="$(< /sys/fs/cgroup/memory/memory.usage_in_bytes)"
        else
            cgroup_bytes="-1"
        fi
        disk_kib="$(df -Pk "$RUN_ROOT" | awk 'NR==2 {print $4}')"
        printf '%s\t%s\t%s\t%s\n' "$timestamp" "$gpu_mib" "$cgroup_bytes" "$disk_kib" >> "$RESOURCE_SAMPLES"
        sleep 5
    done
    printf '{"schema_version":"cuda-rwkv-resource-sampler-stopped-v1","run_id":"%s","action":"%s","lock_token":"%s"}\n' \
        "$RUN_ID" "$mode" "$LOCK_TOKEN" > "$stopped_path.partial.$$"
    mv "$stopped_path.partial.$$" "$stopped_path"
}

run_compute_action() {
    local mode="$1"
    local resource_receipt="$2"
    local log_path="$LAUNCHER_ROOT/${mode}.log"
    local sampler_stop_path="$RUN_ROOT/resource-admission/${LOCK_TOKEN}-${mode}.sampler-stop"
    local sampler_stopped_path="$RUN_ROOT/resource-admission/${LOCK_TOKEN}-${mode}.sampler-stopped"
    local sampler_pid command_code tee_code
    local -a pipeline_codes
    sampler_pid=""
    if [ ! -f "$RUN_ROOT/${mode}-action-manifest.json" ]; then
        sample_resources "$sampler_stop_path" "$sampler_stopped_path" "$mode" &
        sampler_pid=$!
        ACTIVE_SAMPLER_PID="$sampler_pid"
    fi
    set +e
    if [ "$mode" = "source" ]; then
        uv run --no-sync python "$ENTRY" --config "$CONFIG" --run-source --resume \
            --resource-admission-receipt "$resource_receipt" 2>&1 | tee -a "$log_path"
    else
        uv run --no-sync python "$ENTRY" --config "$CONFIG" --run-target \
            --resource-admission-receipt "$resource_receipt" 2>&1 | tee -a "$log_path"
    fi
    pipeline_codes=("${PIPESTATUS[@]}")
    command_code="${pipeline_codes[0]}"
    tee_code="${pipeline_codes[1]}"
    set -e
    if [ -n "$sampler_pid" ]; then
        kill "$sampler_pid" 2>/dev/null || true
        wait "$sampler_pid" 2>/dev/null || true
        ACTIVE_SAMPLER_PID=""
    fi
    if [ "$tee_code" -ne 0 ]; then
        printf '%s\n' "CUDA-RWKV 启动日志 tee 失败，退出码=$tee_code" >&2
        return "$tee_code"
    fi
    return "$command_code"
}

run_tracking_gate() {
    local attempt="$1"
    local attempt_root="$RUN_ROOT/tracking-attempts/attempt-$attempt"
    mkdir -p "$attempt_root"
    if [ -f "$attempt_root/success-receipt.json" ] \
        || [ -f "$attempt_root/failure-receipt.json" ] \
        || [ -f "$attempt_root/inflight-receipt.json" ]; then
        return 0
    fi
    uv run --no-sync swanlab ping > "$attempt_root/swanlab-ping.log" 2>&1
    uv run --no-sync swanlab verify > "$attempt_root/swanlab-verify.log" 2>&1
}

run_publish() {
    local workspace project first_code second_code first_tee_code second_tee_code
    local -a pipeline_codes
    workspace="${AUTHORIZED_SWANLAB_WORKSPACE:?publish 需要 AUTHORIZED_SWANLAB_WORKSPACE}"
    project="${AUTHORIZED_SWANLAB_PROJECT:?publish 需要 AUTHORIZED_SWANLAB_PROJECT}"
    run_tracking_gate 1
    set +e
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --publish-attempt 1 \
        --authorized-swanlab-workspace "$workspace" \
        --authorized-swanlab-project "$project" 2>&1 | tee "$LAUNCHER_ROOT/publish-attempt-1.log"
    pipeline_codes=("${PIPESTATUS[@]}")
    first_code="${pipeline_codes[0]}"
    first_tee_code="${pipeline_codes[1]}"
    set -e
    if [ "$first_tee_code" -ne 0 ]; then
        return "$first_tee_code"
    fi
    printf '%s\n' "$first_code" > "$LAUNCHER_ROOT/publish-attempt-1-exit-code.txt"
    if [ "$first_code" -eq 0 ]; then
        return 0
    fi
    if [ "$first_code" -ne 91 ]; then
        return "$first_code"
    fi
    run_tracking_gate 2
    set +e
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --publish-attempt 2 \
        --authorized-swanlab-workspace "$workspace" \
        --authorized-swanlab-project "$project" 2>&1 | tee "$LAUNCHER_ROOT/publish-attempt-2.log"
    pipeline_codes=("${PIPESTATUS[@]}")
    second_code="${pipeline_codes[0]}"
    second_tee_code="${pipeline_codes[1]}"
    set -e
    if [ "$second_tee_code" -ne 0 ]; then
        return "$second_tee_code"
    fi
    printf '%s\n' "$second_code" > "$LAUNCHER_ROOT/publish-attempt-2-exit-code.txt"
    return "$second_code"
}

acquire_run_lock
trap release_run_lock EXIT
trap 'exit 130' HUP INT TERM
run_static_gates

case "$ACTION" in
    source)
        if [ ! -f "$SOURCE_MANIFEST" ] || [ -L "$SOURCE_MANIFEST" ]; then
            printf '%s\n' "CUDA-RWKV 源年清单缺失或为符号链接，拒绝启动" >&2
            exit 1
        fi
        uv run --no-sync python "$ENTRY" --config "$CONFIG" --check-source-product
        run_compute_resource_gates source
        run_compute_action source "$RESOURCE_ADMISSION_RECEIPT"
        ;;
    target)
        if [ ! -f "$SOURCE_SEAL" ] || [ -L "$SOURCE_SEAL" ]; then
            printf '%s\n' "CUDA-RWKV 目标评价缺少源年资格封印" >&2
            exit 1
        fi
        if [ ! -f "$TARGET_MANIFEST" ] || [ -L "$TARGET_MANIFEST" ]; then
            printf '%s\n' "CUDA-RWKV 目标评价缺少封印后 P6 清单" >&2
            exit 1
        fi
        run_compute_resource_gates target
        run_compute_action target "$RESOURCE_ADMISSION_RECEIPT"
        ;;
    publish)
        run_publish
        ;;
    *)
        printf '%s\n' "用法：bash $0 [source|target|publish]" >&2
        exit 2
        ;;
esac
