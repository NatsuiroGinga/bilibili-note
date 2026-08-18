#!/usr/bin/env bash
# llm_probe 实验内存准入门禁（幂等、单入口）。
#
# 存在原因：2026-08-12 C56 上三个实验并发运行导致容器内存耗尽、整机重启。
# 事故根因是三个启动器的资源门禁只检查磁盘与显存，且余量判断读宿主机 `free`
# （报 754 GiB）而非容器 cgroup 上限（实为 90 GiB），相差 8.4 倍。
# 取证见 .Codex/docs/RWKV/2026-08-12-C56三进程并发内存耗尽事故取证.md
#
# 用法：
#   bash tools/memory_admission_gate.sh <预计峰值GiB> <运行名>
# 退出码：
#   0 允许启动；10 内存不足；11 已有并发实验占用；12 无法读取 cgroup 上限
set -uo pipefail

ESTIMATED_PEAK_GIB="${1:?用法: memory_admission_gate.sh <预计峰值GiB> <运行名>}"
RUN_NAME="${2:?用法: memory_admission_gate.sh <预计峰值GiB> <运行名>}"
SAFETY_MARGIN="${MEMORY_SAFETY_MARGIN:-1.3}"   # 预计峰值需留 30% 余量

# ---- 1. 读取容器真实内存上限，禁止使用 free ----
CGROUP_MAX=""
CGROUP_CUR=""
if [ -r /sys/fs/cgroup/memory.max ]; then                 # cgroup v2
  CGROUP_MAX=$(cat /sys/fs/cgroup/memory.max)
  CGROUP_CUR=$(cat /sys/fs/cgroup/memory.current 2>/dev/null || echo 0)
elif [ -r /sys/fs/cgroup/memory/memory.limit_in_bytes ]; then  # cgroup v1
  CGROUP_MAX=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes)
  CGROUP_CUR=$(cat /sys/fs/cgroup/memory/memory.usage_in_bytes 2>/dev/null || echo 0)
fi

if [ -z "$CGROUP_MAX" ] || [ "$CGROUP_MAX" = "max" ]; then
  echo "[准入门禁] 无法读取 cgroup 内存上限，拒绝启动（禁止回退到 free 判断）"
  exit 12
fi

LIMIT_GIB=$(awk -v b="$CGROUP_MAX" 'BEGIN{printf "%.2f", b/1073741824}')
USED_GIB=$(awk -v b="$CGROUP_CUR" 'BEGIN{printf "%.2f", b/1073741824}')
AVAIL_GIB=$(awk -v l="$LIMIT_GIB" -v u="$USED_GIB" 'BEGIN{printf "%.2f", l-u}')
NEEDED_GIB=$(awk -v p="$ESTIMATED_PEAK_GIB" -v m="$SAFETY_MARGIN" 'BEGIN{printf "%.2f", p*m}')

echo "[准入门禁] 运行=$RUN_NAME"
echo "[准入门禁] cgroup 上限=${LIMIT_GIB} GiB  已用=${USED_GIB} GiB  可用=${AVAIL_GIB} GiB"
echo "[准入门禁] 预计峰值=${ESTIMATED_PEAK_GIB} GiB  含 ${SAFETY_MARGIN}× 余量后需要=${NEEDED_GIB} GiB"

# ---- 2. 跨运行并发检查：任何 flow_probe 进程都算占用 ----
# 匹配口径：项目 venv 起的任何 Python，或任何跑在 runs/ 下的脚本。
# 2026-08-12 教训：原先只枚举已知脚本名（flow_probe|cpu_gate.py|a1_error_anatomy.py|
# a1_history_ceiling.py），新脚本一律漏检，等于没有并发保护。禁止再退回白名单枚举。
CONCURRENT=$(ps -eo pid,rss,cmd --no-headers 2>/dev/null \
  | grep -E "llm_probe/\.venv/bin/python|llm_probe/runs/|flow_probe" \
  | grep -v grep \
  | grep -v "memory_admission_gate" \
  | grep -v "tools/(check_state|probe_tl1|preflight_dtype)" || true)
if [ -n "$CONCURRENT" ]; then
  echo "[准入门禁] 检测到已在运行的 llm_probe 实验进程："
  echo "$CONCURRENT" | awk '{printf "           pid=%s rss=%.2fGiB %s\n", $1, $2/1048576, $3}'
  CONCURRENT_GIB=$(echo "$CONCURRENT" | awk '{s+=$2} END{printf "%.2f", s/1048576}')
  echo "[准入门禁] 并发进程当前合计 RSS=${CONCURRENT_GIB} GiB"
  if [ "${ALLOW_CONCURRENT:-0}" != "1" ]; then
    echo "[准入门禁] 拒绝启动：默认禁止并发。确认内存预算后用 ALLOW_CONCURRENT=1 显式放行。"
    exit 11
  fi
  echo "[准入门禁] ALLOW_CONCURRENT=1 已显式放行，继续检查余量"
fi

# ---- 3. 余量判定 ----
PASS=$(awk -v a="$AVAIL_GIB" -v n="$NEEDED_GIB" 'BEGIN{print (a>=n)?1:0}')
if [ "$PASS" != "1" ]; then
  echo "[准入门禁] 拒绝启动：可用 ${AVAIL_GIB} GiB < 需要 ${NEEDED_GIB} GiB"
  exit 10
fi

echo "[准入门禁] 通过：可用 ${AVAIL_GIB} GiB >= 需要 ${NEEDED_GIB} GiB"
exit 0
