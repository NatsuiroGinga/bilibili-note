#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  printf '用法：bash %s <源JSONL> <输出目录> [样本数]\n' "$0" >&2
  exit 2
fi

source_file=$1
output_dir=$2
sample_count=${3:-128}

if [[ ! -f "$source_file" ]]; then
  printf '源文件不存在：%s\n' "$source_file" >&2
  exit 1
fi
if [[ ! "$sample_count" =~ ^[1-9][0-9]*$ ]]; then
  printf '样本数必须为正整数：%s\n' "$sample_count" >&2
  exit 2
fi

mkdir -p "$output_dir"
subset_file="$output_dir/genis_eval${sample_count}.jsonl"
partial_file="${subset_file}.partial"
manifest_file="$output_dir/subset_manifest.txt"
manifest_partial="${manifest_file}.partial"

cleanup() {
  rm -f "$partial_file" "$manifest_partial"
}
trap cleanup EXIT

LC_ALL=C head -n "$sample_count" "$source_file" >"$partial_file"
actual_count=$(wc -l <"$partial_file")
actual_count=${actual_count//[[:space:]]/}
if [[ "$actual_count" != "$sample_count" ]]; then
  printf '样本不足：期望 %s 条，实际 %s 条\n' "$sample_count" "$actual_count" >&2
  exit 1
fi

read -r source_sha _ < <(sha256sum "$source_file")
read -r subset_sha _ < <(sha256sum "$partial_file")
printf 'source_file=%s\nsource_sha256=%s\nsubset_file=%s\nsubset_sha256=%s\nsample_count=%s\n' \
  "$source_file" \
  "$source_sha" \
  "$subset_file" \
  "$subset_sha" \
  "$sample_count" >"$manifest_partial"

mv "$partial_file" "$subset_file"
mv "$manifest_partial" "$manifest_file"
trap - EXIT

printf '已发布预检子集：%s（%s 条，SHA-256=%s）\n' \
  "$subset_file" \
  "$sample_count" \
  "$subset_sha"
