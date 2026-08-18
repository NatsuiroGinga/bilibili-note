#!/usr/bin/env bash
# Dijk 2026 复现前的只读环境勘察脚本
set -uo pipefail

echo "=== 主机与根目录 ==="
hostname
pwd
ls -d /root/autodl-tmp 2>/dev/null || echo "no autodl-tmp"

echo "=== 磁盘 ==="
df -h /root /root/autodl-tmp 2>/dev/null

echo "=== cgroup 内存上限与当前用量 ==="
for f in /sys/fs/cgroup/memory.max /sys/fs/cgroup/memory.current \
         /sys/fs/cgroup/memory/memory.limit_in_bytes /sys/fs/cgroup/memory/memory.usage_in_bytes; do
  [ -r "$f" ] && echo "$f = $(cat "$f")"
done

echo "=== 项目根 ==="
for d in /root/autodl-tmp/note /root/note /root/autodl-tmp/llm_probe; do
  [ -d "$d" ] && echo "FOUND $d"
done

echo "=== LSPR 数据文件搜索（只读） ==="
find /root -maxdepth 6 -iname '*lspr*' -size +10M -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -40

echo "=== ls23/ls24 相关任意大小 ==="
find /root -maxdepth 7 -iname '*ls23*' -o -maxdepth 7 -iname '*ls24*' -o -maxdepth 7 -iname '*lspr23*' 2>/dev/null | head -40

echo "=== GPU ==="
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader

echo "=== 运行中的 python 进程 ==="
ps -eo pid,etime,rss,comm,args --sort=-rss 2>/dev/null | head -12

echo "=== screen 会话 ==="
screen -ls 2>&1 | head -20

echo "RECON_DONE"
