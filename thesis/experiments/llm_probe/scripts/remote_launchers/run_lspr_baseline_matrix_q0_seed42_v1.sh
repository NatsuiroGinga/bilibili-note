#!/usr/bin/env bash

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
if [[ -r "${HOME}/.bashrc" ]]; then
    source "${HOME}/.bashrc" >/dev/null 2>&1
fi
source "$PROJECT_ROOT/tools/env/activate.sh"
set -Eeuo pipefail
umask 027

readonly RUN_ID=lspr-baseline-dual-track-q0-seed42-v1
readonly SCREEN_NAME=lspr-baseline-dual-track-q0-seed42-v1
readonly RUN_ROOT="$PROJECT_ROOT/runs/baselines/$RUN_ID"
readonly CACHE_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/experiments/c12-seed42-q0-2ip-v1/python-cache-v1"
readonly CONFIG_A="$PROJECT_ROOT/configs/lspr-baseline-matrix-track-a-q0-seed42-v1.json"
readonly CONFIG_B="$PROJECT_ROOT/configs/lspr-baseline-matrix-track-b-q0-seed42-v1.json"
readonly LOG_PATH="$RUN_ROOT/launcher.log"
readonly STATUS_PATH="$RUN_ROOT/status.json"

write_status() {
    local state=$1
    local exit_code=$2
    local partial="$STATUS_PATH.partial"
    printf '{"run_id":"%s","state":"%s","exit_code":%s,"final_accessed":false}\n' \
        "$RUN_ID" "$state" "$exit_code" > "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

if [[ -z "${STY:-}" ]]; then
    if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
        printf '已存在同名 screen，不重复启动：%s\n' "$SCREEN_NAME"
        exit 0
    fi
    screen -dmS "$SCREEN_NAME" bash "$0"
    printf '已启动 LSPR 双轨基线 screen：%s\n' "$SCREEN_NAME"
    exit 0
fi

mkdir -p -- "$RUN_ROOT"
exec > >(tee -a "$LOG_PATH") 2>&1

if [[ -e "$RUN_ROOT/finished.json" ]]; then
    printf '已存在成功收据，幂等跳过：%s\n' "$RUN_ROOT/finished.json"
    exit 0
fi
for required in "$CACHE_ROOT/cache-manifest.json" "$CONFIG_A" "$CONFIG_B"; do
    if [[ ! -s "$required" ]]; then
        printf '必要输入不存在：%s\n' "$required" >&2
        write_status blocked 74
        exit 74
    fi
done
if [[ "$(jq -r '.final_accessed' "$CACHE_ROOT/cache-manifest.json")" != false ]]; then
    printf '缓存 final_accessed 不是 false，拒绝启动。\n' >&2
    write_status blocked 65
    exit 65
fi
if [[ "$(jq -r '.swanlab.workspace + "/" + .swanlab.project' "$CONFIG_A")" != "mortiswang/malicious-traffic-llm" ]] ||
   [[ "$(jq -r '.swanlab.workspace + "/" + .swanlab.project' "$CONFIG_B")" != "mortiswang/malicious-traffic-llm" ]]; then
    printf 'SwanLab 目的地与授权不一致，拒绝加载数据。\n' >&2
    write_status blocked 65
    exit 65
fi

PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -m flow_probe.lspr_baseline_matrix_train audit --config "$CONFIG_A" > "$RUN_ROOT/audit-track-a.json"
PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -m flow_probe.lspr_baseline_matrix_train audit --config "$CONFIG_B" > "$RUN_ROOT/audit-track-b.json"

cpu_count=$(nproc)
mem_available_kib=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
cpu_by_core=$(( cpu_count / 8 ))
cpu_by_memory=$(( mem_available_kib / 16777216 ))
cpu_parallel=$cpu_by_core
if (( cpu_by_memory < cpu_parallel )); then cpu_parallel=$cpu_by_memory; fi
if (( cpu_parallel < 1 )); then cpu_parallel=1; fi
if (( cpu_parallel > 4 )); then cpu_parallel=4; fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
    printf '神经基线要求GPU，但正式环境没有nvidia-smi。\n' >&2
    write_status blocked 69
    exit 69
fi
gpu_free_mib=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1 | tr -d ' ')
if (( gpu_free_mib < 18432 )); then
    printf '空闲显存不足18432 MiB，拒绝让神经基线静默退回CPU：%s MiB\n' "$gpu_free_mib" >&2
    write_status blocked 69
    exit 69
fi
gpu_parallel=$(( gpu_free_mib / 18432 ))
if (( gpu_parallel > 2 )); then gpu_parallel=2; fi

printf '资源并发收据：CPU核=%s，可用内存KiB=%s，CPU并发=%s，空闲显存MiB=%s，GPU并发=%s\n' \
    "$cpu_count" "$mem_available_kib" "$cpu_parallel" "$gpu_free_mib" "$gpu_parallel"
printf '{"cpu_count":%s,"memory_available_kib":%s,"cpu_parallel":%s,"gpu_free_mib":%s,"gpu_parallel":%s,"final_accessed":false}\n' \
    "$cpu_count" "$mem_available_kib" "$cpu_parallel" "$gpu_free_mib" "$gpu_parallel" > "$RUN_ROOT/resource-plan.json"

run_one() {
    local track=$1
    local config=$2
    local model=$3
    local model_root="$RUN_ROOT/track-${track,,}/$model"
    local exit_path="$RUN_ROOT/track-${track,,}/$model.exit-code"
    mkdir -p -- "$(dirname "$model_root")"
    if [[ -s "$model_root/run-state.json" ]] && [[ "$(jq -r '.state' "$model_root/run-state.json")" == finished ]]; then
        printf '模型已有成功状态，幂等跳过：track=%s model=%s\n' "$track" "$model"
        printf '0\n' > "$exit_path"
        return 0
    fi
    if [[ -e "$model_root" ]]; then
        printf '模型目录已存在但未成功，拒绝覆盖：%s\n' "$model_root" >&2
        printf '73\n' > "$exit_path"
        return 73
    fi
    printf '开始模型：track=%s model=%s time=%s\n' "$track" "$model" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    set +e
    PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -m flow_probe.lspr_baseline_matrix_train run \
        --config "$config" \
        --cache-root "$CACHE_ROOT" \
        --output-dir "$model_root" \
        --model "$model" 2>&1 | tee "$RUN_ROOT/track-${track,,}/$model.log"
    pipeline_status=("${PIPESTATUS[@]}")
    set -e
    code=${pipeline_status[0]}
    if [[ "${pipeline_status[1]}" -ne 0 ]] && [[ "$code" -eq 0 ]]; then code=${pipeline_status[1]}; fi
    printf '%s\n' "$code" > "$exit_path"
    printf '结束模型：track=%s model=%s exit=%s time=%s\n' "$track" "$model" "$code" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    return "$code"
}

run_group() {
    local maximum=$1
    shift
    local active=0
    local specification track config model
    for specification in "$@"; do
        IFS='|' read -r track config model <<< "$specification"
        while (( active >= maximum )); do
            set +e
            wait -n
            set -e
            active=$(( active - 1 ))
        done
        run_one "$track" "$config" "$model" &
        active=$(( active + 1 ))
    done
    while (( active > 0 )); do
        set +e
        wait -n
        set -e
        active=$(( active - 1 ))
    done
}

cpu_jobs=(
    "A|$CONFIG_A|dijk2024_rf_visible_full_extension"
    "A|$CONFIG_A|leoste2025_rf_with_iat"
    "A|$CONFIG_A|leoste2025_rf_without_iat"
    "A|$CONFIG_A|dijk2026_xgboost"
    "B|$CONFIG_B|leoste2025_rf_with_iat"
    "B|$CONFIG_B|leoste2025_rf_without_iat"
    "B|$CONFIG_B|dijk2026_xgboost"
)
gpu_jobs=(
    "A|$CONFIG_A|leoste_1d_cnn_nearest_text"
    "A|$CONFIG_A|dijk2026_gru"
    "A|$CONFIG_A|dijk2026_full_attention_transformer"
    "A|$CONFIG_A|dijk2026_bigbird"
    "A|$CONFIG_A|dijk2026_longformer"
    "B|$CONFIG_B|leoste_1d_cnn_nearest_text"
    "B|$CONFIG_B|dijk2026_gru"
    "B|$CONFIG_B|dijk2026_full_attention_transformer"
    "B|$CONFIG_B|dijk2026_bigbird"
    "B|$CONFIG_B|dijk2026_longformer"
)

write_status running null
run_group "$cpu_parallel" "${cpu_jobs[@]}" &
cpu_group_pid=$!
run_group "$gpu_parallel" "${gpu_jobs[@]}" &
gpu_group_pid=$!
set +e
wait "$cpu_group_pid"
wait "$gpu_group_pid"
set -e

failed=0
for specification in "${cpu_jobs[@]}" "${gpu_jobs[@]}"; do
    IFS='|' read -r track _ model <<< "$specification"
    exit_path="$RUN_ROOT/track-${track,,}/$model.exit-code"
    if [[ ! -s "$exit_path" ]] || [[ "$(tr -d '[:space:]' < "$exit_path")" != 0 ]]; then
        failed=$(( failed + 1 ))
    fi
done
if (( failed > 0 )); then
    printf '双轨矩阵存在失败模型：%s\n' "$failed" >&2
    write_status failed 1
    exit 1
fi
printf '{"state":"finished","model_run_count":17,"final_accessed":false}\n' > "$RUN_ROOT/finished.json"
write_status finished 0
