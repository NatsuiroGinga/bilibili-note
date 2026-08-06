#!/usr/bin/env bash

if [[ -f ~/.bashrc ]]; then
    source ~/.bashrc
fi
set -Eeuo pipefail

PROJECT_ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
SOURCE_ROOT="$PROJECT_ROOT/runs/r2-minimal-sidecar-physics-fit/tcp-udp-v2-seed-42"
ARCHIVE_PARENT="$PROJECT_ROOT/runs/superseded-archives/r2-minimal-sidecar-physics-fit"
IDENTITY="superseded-by-probe-fix-$(date -u +%Y%m%dT%H%M%SZ)-$$"
ARCHIVE_ROOT="$ARCHIVE_PARENT/$IDENTITY"
RECEIPT_PATH=""

readonly REQUIRED_ARTIFACTS=(
    checkpoint-latest.pt
    checkpoint-binding-manifest.json
    zero-collapse-receipt.json
    result.json
    metrics.jsonl
)

fail() {
    printf '归档失败：%s\n' "$1" >&2
    exit 1
}

sha256_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
        return
    fi
    shasum -a 256 "$1" | awk '{print $1}'
}

device_id() {
    if stat -c '%d' "$1" >/dev/null 2>&1; then
        stat -c '%d' "$1"
        return
    fi
    stat -f '%d' "$1"
}

cleanup_unmoved_receipt() {
    if [[ -n "$RECEIPT_PATH" && -e "$RECEIPT_PATH" && ! -e "$ARCHIVE_ROOT" ]]; then
        rm -f "$RECEIPT_PATH"
    fi
}

trap cleanup_unmoved_receipt EXIT

[[ $# -eq 0 ]] || fail "不接受参数"
[[ -d "$SOURCE_ROOT" ]] || fail "成功物理拟合源根不存在：$SOURCE_ROOT"

if pgrep -f '[r]2_final_physics_fit|[r]un_r2_final_physics_fit\.sh|[r]2-minimal-sidecar-physics-fit' >/dev/null || \
    pgrep -f '[r]2_final_distilbert_probe|[r]un_r2_final_probe\.sh' >/dev/null; then
    fail "检测到活动物理拟合或旁路探针进程"
fi

for artifact in "${REQUIRED_ARTIFACTS[@]}"; do
    [[ -s "$SOURCE_ROOT/$artifact" ]] || fail "缺少或为空的成功制品：$artifact"
done

[[ ! -e "$ARCHIVE_ROOT" ]] || fail "归档目标已存在：$ARCHIVE_ROOT"
mkdir -p "$ARCHIVE_PARENT"
[[ "$(device_id "$SOURCE_ROOT")" == "$(device_id "$ARCHIVE_PARENT")" ]] || \
    fail "源根与归档父根不在同一文件系统"

CHECKPOINT_SHA256="$(sha256_file "$SOURCE_ROOT/checkpoint-latest.pt")"
MANIFEST_SHA256="$(sha256_file "$SOURCE_ROOT/checkpoint-binding-manifest.json")"
ZERO_COLLAPSE_RECEIPT_SHA256="$(sha256_file "$SOURCE_ROOT/zero-collapse-receipt.json")"
RESULT_SHA256="$(sha256_file "$SOURCE_ROOT/result.json")"
METRICS_SHA256="$(sha256_file "$SOURCE_ROOT/metrics.jsonl")"

RECEIPT_PATH="$SOURCE_ROOT/archive-receipt.json"
[[ ! -e "$RECEIPT_PATH" ]] || fail "源根已存在归档收据，拒绝覆盖"
{
    printf '{\n'
    printf '  "status": "finished",\n'
    printf '  "archive_identity": "%s",\n' "$IDENTITY"
    printf '  "source_root": "%s",\n' "$SOURCE_ROOT"
    printf '  "artifact_sha256": {\n'
    printf '    "checkpoint-latest.pt": "%s",\n' "$CHECKPOINT_SHA256"
    printf '    "checkpoint-binding-manifest.json": "%s",\n' "$MANIFEST_SHA256"
    printf '    "zero-collapse-receipt.json": "%s",\n' "$ZERO_COLLAPSE_RECEIPT_SHA256"
    printf '    "result.json": "%s",\n' "$RESULT_SHA256"
    printf '    "metrics.jsonl": "%s"\n' "$METRICS_SHA256"
    printf '  }\n'
    printf '}\n'
} > "$RECEIPT_PATH"

[[ ! -e "$ARCHIVE_ROOT" ]] || fail "归档目标已存在：$ARCHIVE_ROOT"
mv "$SOURCE_ROOT" "$ARCHIVE_ROOT"
mkdir -p "$SOURCE_ROOT"
rmdir "$SOURCE_ROOT" || fail "重建后的源根非空"
mkdir "$SOURCE_ROOT"

printf 'archive_root=%s\n' "$ARCHIVE_ROOT"
printf 'source_root=%s\n' "$SOURCE_ROOT"
printf 'old_checkpoint_sha256=%s\n' "$CHECKPOINT_SHA256"
printf 'old_manifest_sha256=%s\n' "$MANIFEST_SHA256"
printf 'status=finished\n'
