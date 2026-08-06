#!/usr/bin/env bash

source ~/.bashrc >/dev/null 2>&1 || true
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
  printf '用法：%s <third-prep-YYYYMMDDTHHMMSSZ|fourth-prep-YYYYMMDDTHHMMSSZ>\n' "$0" >&2
  exit 2
fi

archive_id="$1"
if [[ ! "$archive_id" =~ ^(third|fourth)-prep-[0-9]{8}T[0-9]{6}Z$ ]]; then
  printf '归档身份格式非法：%s\n' "$archive_id" >&2
  exit 2
fi

project_root="/root/autodl-tmp/thesis/experiments/llm_probe"
source_root="$project_root/runs/r2-minimal-sidecar-physics-fit/tcp-udp-v2-seed-42"
archive_parent="$project_root/runs/failed-archives/r2-minimal-sidecar-physics-fit"
archive_root="$archive_parent/$archive_id"

if pgrep -f 'flow_probe\.r2_final_physics_fit' >/dev/null; then
  printf '仍有物理拟合进程，拒绝归档。\n' >&2
  exit 3
fi
if [[ ! -d "$source_root" ]]; then
  printf '固定物理输出根不存在，拒绝伪造归档。\n' >&2
  exit 4
fi
if [[ -e "$archive_root" ]]; then
  printf '唯一归档目标已存在，拒绝覆盖：%s\n' "$archive_root" >&2
  exit 5
fi

mkdir -p "$archive_parent"
mv -- "$source_root" "$archive_root"
mkdir -p "$source_root"

if [[ -n "$(rg --files "$source_root")" ]]; then
  printf '固定物理输出根重建后非空。\n' >&2
  exit 6
fi

printf 'archive_root=%s\n' "$archive_root"
printf 'source_root=%s\n' "$source_root"
printf 'status=finished\n'
