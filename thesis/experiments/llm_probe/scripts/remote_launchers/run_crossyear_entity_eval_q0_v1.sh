#!/usr/bin/env bash
# 跨年度实体级评价与决策层适应 Q0 启动器。
#
# 用法：
#   bash scripts/remote_launchers/run_crossyear_entity_eval_q0_v1.sh --preflight
#   bash scripts/remote_launchers/run_crossyear_entity_eval_q0_v1.sh --stage alignment-gate
#   bash scripts/remote_launchers/run_crossyear_entity_eval_q0_v1.sh --stage full
#
# --preflight 在前台只读核验；--stage 先过内存准入门禁再用 screen 后台运行。
# 主进程退出码：0 通过；3 协议对齐门不通过（阻断，非故障）；其他为失败。

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
if [[ -r "${HOME}/.bashrc" ]]; then
    source "${HOME}/.bashrc" >/dev/null 2>&1
fi
source "$PROJECT_ROOT/tools/env/activate.sh"
set -Eeuo pipefail
umask 027

readonly RUN_ID=crossyear-entity-level-eval-q0-seed42-v1
readonly RUN_ROOT="$PROJECT_ROOT/runs/candidates/$RUN_ID"
readonly LAUNCH_ROOT="$PROJECT_ROOT/runs/launchers/$RUN_ID"
readonly DATASET_ROOT="$PROJECT_ROOT/runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1"
readonly SEED=42
readonly ESTIMATED_PEAK_GIB=8

usage() {
    printf '用法：%s --preflight | --stage {preflight|alignment-gate|full}\n' "$0" >&2
}

write_launch_status() {
    local stage=$1
    local state=$2
    local exit_code=$3
    mkdir -p -- "$LAUNCH_ROOT"
    local partial="$LAUNCH_ROOT/status.$stage.json.partial"
    printf '{"run_id":"%s","stage":"%s","state":"%s","exit_code":%s,"log_path":"%s","final_accessed":false}\n' \
        "$RUN_ID" "$stage" "$state" "$exit_code" "$LAUNCH_ROOT/$stage.log" > "$partial"
    mv -f -- "$partial" "$LAUNCH_ROOT/status.$stage.json"
}

check_capability() {
    local missing=0
    local tool
    for tool in uv screen rg; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            printf '缺少必需命令：%s\n' "$tool" >&2
            missing=1
        fi
    done
    return "$missing"
}

execute_stage() {
    local stage=$1
    local log_path="$LAUNCH_ROOT/$stage.log"
    mkdir -p -- "$LAUNCH_ROOT" "$RUN_ROOT"
    if [[ ! -d "$DATASET_ROOT" ]]; then
        printf '冻结数据根不存在：%s\n' "$DATASET_ROOT" >&2
        write_launch_status "$stage" blocked 74
        return 74
    fi
    write_launch_status "$stage" running null
    set +e
    {
        printf '阶段=%s 开始：%s\n' "$stage" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -m flow_probe.crossyear_entity_eval_run \
            --dataset-root "$DATASET_ROOT" \
            --output-root "$RUN_ROOT" \
            --stage "$stage" \
            --seed "$SEED"
        main_code=$?
        printf '阶段=%s 主进程退出码=%s 结束：%s\n' "$stage" "$main_code" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        exit "$main_code"
    } 2>&1 | tee "$log_path"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    if [[ ! -s "$log_path" ]]; then
        printf '日志缺失或为空：%s\n' "$log_path" >&2
        write_launch_status "$stage" failed 75
        return 75
    fi
    if [[ "${pipeline_status[1]}" -ne 0 ]]; then
        printf 'tee 失败，退出码=%s\n' "${pipeline_status[1]}" >&2
        write_launch_status "$stage" failed "${pipeline_status[1]}"
        return "${pipeline_status[1]}"
    fi
    case "${pipeline_status[0]}" in
        0)
            write_launch_status "$stage" finished 0
            return 0
            ;;
        3)
            write_launch_status "$stage" blocked_alignment_gate 3
            printf '协议对齐门不通过，已写阻断收据，不进入 M1/M2/M3。\n'
            return 3
            ;;
        *)
            write_launch_status "$stage" failed "${pipeline_status[0]}"
            return "${pipeline_status[0]}"
            ;;
    esac
}

STAGE=""
MODE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --preflight)
            STAGE=preflight
            MODE=foreground
            shift
            ;;
        --stage)
            STAGE="${2:-}"
            MODE=background
            shift 2
            ;;
        --exec)
            STAGE="${2:-}"
            MODE=exec
            shift 2
            ;;
        *)
            usage
            exit 2
            ;;
    esac
done

if [[ -z "$STAGE" ]]; then
    usage
    exit 2
fi
case "$STAGE" in
    preflight|alignment-gate|full) ;;
    *)
        printf '未知阶段：%s\n' "$STAGE" >&2
        exit 2
        ;;
esac

if ! check_capability; then
    exit 76
fi

if [[ "$MODE" == "exec" || "$MODE" == "foreground" ]]; then
    if execute_stage "$STAGE"; then
        exit 0
    fi
    exit $?
fi

if [[ -s "$RUN_ROOT/status.json" ]] && rg -q 'blocked_alignment_gate' "$RUN_ROOT/status.json"; then
    printf '协议对齐门已判定不通过，拒绝继续启动后续阶段：%s\n' "$RUN_ROOT/status.json" >&2
    exit 70
fi

set +e
bash "$PROJECT_ROOT/tools/memory_admission_gate.sh" "$ESTIMATED_PEAK_GIB" "$RUN_ID"
gate_code=$?
set -e
if [[ "$gate_code" -ne 0 ]]; then
    printf '内存准入门禁拒绝启动，退出码=%s\n' "$gate_code" >&2
    exit "$gate_code"
fi

SCREEN_NAME="$RUN_ID-$STAGE"
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '已存在同名 screen，不重复启动：%s\n' "$SCREEN_NAME"
    exit 0
fi
screen -dmS "$SCREEN_NAME" bash "$0" --exec "$STAGE"
printf '已启动 screen：%s\n' "$SCREEN_NAME"
