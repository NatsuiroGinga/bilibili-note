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
RESOURCE_SAMPLES="$RUN_ROOT/resource-samples.tsv"
ACTION="${1:-source}"

cd "$PROJECT_ROOT"
source tools/env/activate.sh
export OMP_NUM_THREADS=1
mkdir -p "$RUN_ROOT" "$LAUNCHER_ROOT"

run_static_gates() {
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --validate-config
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --write-dependency-closure
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --check-dependency-closure
    uv run --no-sync python "$ENTRY" --config "$CONFIG" --check-target-isolation
}

run_compute_resource_gates() {
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
}

sample_resources() {
    if [ ! -s "$RESOURCE_SAMPLES" ]; then
        printf 'timestamp\tgpu_process_memory_mib\tcgroup_memory_bytes\tdisk_available_kib\n' >> "$RESOURCE_SAMPLES"
    fi
    while true; do
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
}

run_compute_action() {
    local mode="$1"
    local log_path="$LAUNCHER_ROOT/${mode}.log"
    local sampler_pid command_code tee_code
    local -a pipeline_codes
    sample_resources &
    sampler_pid=$!
    set +e
    if [ "$mode" = "source" ]; then
        uv run --no-sync python "$ENTRY" --config "$CONFIG" --run-source --resume 2>&1 | tee "$log_path"
    else
        uv run --no-sync python "$ENTRY" --config "$CONFIG" --run-target 2>&1 | tee "$log_path"
    fi
    pipeline_codes=("${PIPESTATUS[@]}")
    command_code="${pipeline_codes[0]}"
    tee_code="${pipeline_codes[1]}"
    set -e
    kill "$sampler_pid" 2>/dev/null || true
    wait "$sampler_pid" 2>/dev/null || true
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

run_static_gates

case "$ACTION" in
    source)
        if [ ! -f "$SOURCE_MANIFEST" ] || [ -L "$SOURCE_MANIFEST" ]; then
            printf '%s\n' "CUDA-RWKV 源年清单缺失或为符号链接，拒绝启动" >&2
            exit 1
        fi
        uv run --no-sync python "$ENTRY" --config "$CONFIG" --check-source-product
        run_compute_resource_gates
        run_compute_action source
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
        run_compute_resource_gates
        run_compute_action target
        ;;
    publish)
        run_publish
        ;;
    *)
        printf '%s\n' "用法：bash $0 [source|target|publish]" >&2
        exit 2
        ;;
esac
