#!/usr/bin/env bash

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
if [[ -r "${HOME}/.bashrc" ]]; then
    source "${HOME}/.bashrc" >/dev/null 2>&1
fi
source "$PROJECT_ROOT/tools/env/activate.sh"
set -Eeuo pipefail
umask 027

readonly RUN_ID=lspr-dijk2024-author-example-rf80k-seed42-v2
readonly SCREEN_NAME=lspr-dijk2024-author-example-rf80k-seed42-v2
readonly RUN_ROOT="$PROJECT_ROOT/runs/replications/$RUN_ID"
readonly LOG_PATH="$RUN_ROOT/run.log"
readonly STATUS_PATH="$RUN_ROOT/status.json"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/lspr-published-protocol-replication-v1.json"
readonly MODULE=flow_probe.lspr_published_protocol_replication
readonly SWANLAB_MODULE_PATH="$PROJECT_ROOT/src/flow_probe/lspr_published_protocol_replication.py"
readonly FLOW_CSV=${LSPR23_FLOW_CSV:-}

if ! rg -q --fixed-strings 'PROJECT = "malicious-traffic-llm"' "$SWANLAB_MODULE_PATH" ||
    ! rg -q --fixed-strings 'WORKSPACE = "mortiswang"' "$SWANLAB_MODULE_PATH"; then
    printf 'SwanLab 目的地与用户授权不一致，拒绝启动。\n' >&2
    exit 78
fi

write_status() {
    local state=$1
    local stage=$2
    local exit_code=$3
    local partial="$STATUS_PATH.partial.$$"
    printf '{"run_id":"%s","state":"%s","stage":"%s","exit_code":%s,"log_path":"%s","author_code_example":true,"paper_reported_experiment_reproduced":false,"formal_comparison_forbidden":true,"screening_only":true,"formal_paper_evidence":false,"formal_paper_evidence_candidate":false,"final_accessed":false}\n' \
        "$RUN_ID" "$state" "$stage" "$exit_code" "$LOG_PATH" > "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

worker_main() {
    if [[ -z "$FLOW_CSV" || ! -s "$FLOW_CSV" ]]; then
        printf '必须通过 LSPR23_FLOW_CSV 指向 LSPR23 原始流 CSV。\n' >&2
        return 66
    fi
    if [[ ! -s "$CONFIG_PATH" ]]; then
        printf '已发表论文原协议复现配置不存在：%s\n' "$CONFIG_PATH" >&2
        return 66
    fi
    if ! command -v uv >/dev/null 2>&1 || ! command -v rg >/dev/null 2>&1; then
        printf '远端 uv 或 rg 不可用。\n' >&2
        return 69
    fi
    if ! uv run --no-sync python -c 'import pandas, sklearn, swanlab' >/dev/null 2>&1; then
        printf '作者示例复跑所需的 pandas、scikit-learn 或 SwanLab 不可导入。\n' >&2
        return 69
    fi
    write_status running author-code-example null
    printf '开始复跑 Dijk 2024 作者后续 80k 代码示例，时间=%s\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -m "$MODULE" \
        run-author-code-example \
        --flow-csv "$FLOW_CSV" \
        --config "$CONFIG_PATH" \
        --output-dir "$RUN_ROOT/example"
    printf '{"state":"finished","author_code_example":true,"paper_reported_experiment_reproduced":false,"formal_comparison_forbidden":true,"screening_only":true,"formal_paper_evidence":false,"formal_paper_evidence_candidate":false,"final_accessed":false}\n' \
        > "$RUN_ROOT/finished.json"
    write_status finished complete 0
}

worker_entry() {
    trap 'write_status interrupted signal 130; exit 130' HUP INT TERM
    set +e
    worker_main 2>&1 | tee "$LOG_PATH"
    local pipeline_status=("${PIPESTATUS[@]}")
    set -e
    local worker_code=${pipeline_status[0]}
    local tee_code=${pipeline_status[1]}
    printf '%s\n' "$worker_code" > "$RUN_ROOT/command-exit-code.txt"
    printf '%s\n' "$tee_code" > "$RUN_ROOT/tee-exit-code.txt"
    if [[ "$worker_code" -ne 0 ]]; then
        write_status failed controller "$worker_code"
        return "$worker_code"
    fi
    if [[ "$tee_code" -ne 0 ]]; then
        write_status failed tee "$tee_code"
        return "$tee_code"
    fi
}

if [[ ${1:-} == --worker ]]; then
    mkdir -p -- "$RUN_ROOT"
    worker_entry
    exit $?
fi

if ! command -v screen >/dev/null 2>&1; then
    printf '远端缺少 screen。\n' >&2
    exit 69
fi
if [[ -z "$FLOW_CSV" || ! -s "$FLOW_CSV" || ! -s "$CONFIG_PATH" ]]; then
    printf 'LSPR23 原始流 CSV 或复现配置不存在，拒绝创建运行目录。\n' >&2
    exit 66
fi
if screen -ls 2>/dev/null | rg -q "[.]${SCREEN_NAME}[[:space:]]"; then
    printf '同名 screen 已在运行：%s\n' "$SCREEN_NAME"
    exit 0
fi
if [[ -s "$STATUS_PATH" ]] && uv run --no-sync python -c \
    'import json,sys; raise SystemExit(0 if json.load(open(sys.argv[1], encoding="utf-8")).get("state") == "finished" else 1)' \
    "$STATUS_PATH"; then
    printf 'Dijk 2024 作者代码示例已复跑，不重复启动：%s\n' "$RUN_ID"
    exit 0
fi
if [[ -e "$RUN_ROOT" ]]; then
    printf '运行根已存在但未完成，保留证据并阻断：%s\n' "$RUN_ROOT" >&2
    exit 73
fi
mkdir -p -- "$RUN_ROOT"
printf '%s\n' "$SCREEN_NAME" > "$RUN_ROOT/screen-session.txt"
printf 'LSPR23_FLOW_CSV=<已配置路径> %s --worker\n' "$0" > "$RUN_ROOT/command.txt"
sha256sum \
    "$CONFIG_PATH" \
    "$PROJECT_ROOT/src/flow_probe/lspr_published_protocol_replication.py" \
    "$0" > "$RUN_ROOT/input-sha256.txt"
write_status prepared launch null
screen -dmS "$SCREEN_NAME" bash "$0" --worker
printf 'LSPR_DIJK2024_AUTHOR_EXAMPLE_STARTED session=%s output=%s final_accessed=false formal_paper_evidence=false\n' \
    "$SCREEN_NAME" "$RUN_ROOT"
