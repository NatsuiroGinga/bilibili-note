#!/usr/bin/env bash

PROJECT_ROOT=/root/autodl-tmp/thesis/experiments/llm_probe
if [[ -r "${HOME}/.bashrc" ]]; then
    source "${HOME}/.bashrc" >/dev/null 2>&1
fi
source "$PROJECT_ROOT/tools/env/activate.sh"
set -Eeuo pipefail
umask 027

readonly RUN_ID=lspr-published-protocol-strict-audit-v1
readonly RUN_ROOT="$PROJECT_ROOT/runs/replications/$RUN_ID"
readonly LOG_PATH="$RUN_ROOT/audit.log"
readonly STATUS_PATH="$RUN_ROOT/status.json"
readonly AUDIT_ROOT="$RUN_ROOT/protocol-audit"
readonly CONFIG_PATH="$PROJECT_ROOT/configs/lspr-published-protocol-replication-v1.json"
readonly MODULE=flow_probe.lspr_published_protocol_replication
readonly MODULE_PATH="$PROJECT_ROOT/src/flow_probe/lspr_published_protocol_replication.py"

write_status() {
    local state=$1
    local stage=$2
    local exit_code=$3
    local partial="$STATUS_PATH.partial.$$"
    printf '{"run_id":"%s","state":"%s","stage":"%s","exit_code":%s,"log_path":"%s","training_started":false,"strict_paper_training_available":false,"screening_only":true,"formal_paper_evidence":false,"formal_paper_evidence_candidate":false,"final_accessed":false}\n' \
        "$RUN_ID" "$state" "$stage" "$exit_code" "$LOG_PATH" > "$partial"
    mv -f -- "$partial" "$STATUS_PATH"
}

if [[ ! -s "$CONFIG_PATH" || ! -s "$MODULE_PATH" ]]; then
    printf '严格论文协议审计配置或模块不存在，拒绝创建运行目录。\n' >&2
    exit 66
fi
if ! command -v uv >/dev/null 2>&1; then
    printf '远端 uv 不可用，无法执行协议审计。\n' >&2
    exit 69
fi
if [[ -e "$RUN_ROOT" ]]; then
    printf '严格论文协议审计目录已存在，拒绝覆盖：%s\n' "$RUN_ROOT" >&2
    exit 73
fi

mkdir -p -- "$RUN_ROOT"
sha256sum "$CONFIG_PATH" "$MODULE_PATH" "$0" > "$RUN_ROOT/input-sha256.txt"
write_status running protocol-audit null
set +e
PYTHONPATH="$PROJECT_ROOT/src" uv run --no-sync python -m "$MODULE" audit \
    --config "$CONFIG_PATH" \
    --output-dir "$AUDIT_ROOT" 2>&1 | tee "$LOG_PATH"
pipeline_status=("${PIPESTATUS[@]}")
set -e
readonly audit_code=${pipeline_status[0]}
readonly tee_code=${pipeline_status[1]}
printf '%s\n' "$audit_code" > "$RUN_ROOT/audit-exit-code.txt"
printf '%s\n' "$tee_code" > "$RUN_ROOT/tee-exit-code.txt"
if [[ "$audit_code" -ne 0 ]]; then
    write_status failed protocol-audit "$audit_code"
    exit "$audit_code"
fi
if [[ "$tee_code" -ne 0 ]]; then
    write_status failed tee "$tee_code"
    exit "$tee_code"
fi

readonly GATE_RECEIPT="$AUDIT_ROOT/strict_training_gate_receipt.json"
if [[ ! -s "$GATE_RECEIPT" ]]; then
    printf '严格训练门禁收据缺失：%s\n' "$GATE_RECEIPT" >&2
    write_status failed strict-training-gate 65
    exit 65
fi
if ! uv run --no-sync python -c \
    'import json,sys; value=json.load(open(sys.argv[1], encoding="utf-8")); raise SystemExit(0 if value.get("decision") == "no-trainable-strict-paper-experiment" and value.get("strict_trainable_protocol_count") == 0 and value.get("author_examples_formal_comparison_forbidden") is True else 1)' \
    "$GATE_RECEIPT"; then
    printf '严格训练门禁收据未证明“无可训练严格论文实验”。\n' >&2
    write_status failed strict-training-gate 65
    exit 65
fi

printf '严格协议审计完成：无可训练严格论文实验；未启动 Leoste RF 或 Dijk 2026 XGBoost；Dijk 2024 作者 80k 示例仍仅可通过独立作者示例入口复跑且永久禁止正式比较。\n'
write_status finished no-trainable-strict-paper-experiment 0
