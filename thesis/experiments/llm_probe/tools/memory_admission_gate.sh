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
CGROUP_RECLAIMABLE=0
if [ -r /sys/fs/cgroup/memory.max ]; then                 # cgroup v2
  CGROUP_MAX=$(cat /sys/fs/cgroup/memory.max)
  CGROUP_CUR=$(cat /sys/fs/cgroup/memory.current 2>/dev/null || echo 0)
  if [ -r /sys/fs/cgroup/memory.stat ]; then
    # 可回收量 = 干净页缓存（inactive_file + active_file）− tmpfs/shmem。
    # shmem 无 swap 时不可回收，必须扣除；其余文件页内核在有压力时按需回收，
    # 从不导致 OOM。
    #
    # 2026-08-25 B76 实测：active_file 达 31.49 GiB，全部是读 X24.npy（6.7 GB）
    # 等冻结制品留下的干净页缓存。旧口径只计 inactive_file（2.69 GiB），把这
    # 31.49 GiB 记成永久占用，算出"可用 44.41 GiB < 需要 62.40 GiB"并以退出码
    # 10 连续拦下本可正常进行的 N-16 共同预算包络实验；同一时刻真实可用为
    # 90.00 − anon 13.84 − slab 0.16 ≈ 76.0 GiB。取证见对应运行目录的
    # memory-admission-gate.log。
    #
    # 本次只修正可回收量口径，不放宽预计峰值，也不放宽 1.3× 安全余量：
    # 进程真实占用（anon）紧张时该门仍然照常拒绝。
    CGROUP_RECLAIMABLE=$(awk '
      $1 == "inactive_file" {inactive = $2}
      $1 == "active_file"   {active = $2}
      $1 == "shmem"         {shmem = $2}
      # 必须用 %.0f 而非 %d：本机 awk 为 mawk，%d 走 32 位整型，超过 2^31 的
      # 字节数会饱和成 2147483648（2026-08-25 实测把 34.14 GiB 截成 2.00 GiB）。
      END {value = inactive + active - shmem; if (value < 0) value = 0; printf "%.0f", value}
    ' /sys/fs/cgroup/memory.stat)
  fi
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
RECLAIMABLE_GIB=$(awk -v b="$CGROUP_RECLAIMABLE" 'BEGIN{printf "%.2f", b/1073741824}')
EFFECTIVE_USED_GIB=$(awk -v c="$CGROUP_CUR" -v r="$CGROUP_RECLAIMABLE" 'BEGIN{v=c-r; if (v<0) v=0; printf "%.2f", v/1073741824}')
AVAIL_GIB=$(awk -v m="$CGROUP_MAX" -v c="$CGROUP_CUR" -v r="$CGROUP_RECLAIMABLE" 'BEGIN{v=m-c+r; if (v>m) v=m; printf "%.2f", v/1073741824}')
NEEDED_GIB=$(awk -v p="$ESTIMATED_PEAK_GIB" -v m="$SAFETY_MARGIN" 'BEGIN{printf "%.2f", p*m}')

echo "[准入门禁] 运行=$RUN_NAME"
echo "[准入门禁] cgroup 上限=${LIMIT_GIB} GiB  当前=${USED_GIB} GiB  可回收页缓存=${RECLAIMABLE_GIB} GiB"
echo "[准入门禁] 有效已用=${EFFECTIVE_USED_GIB} GiB  有效可用=${AVAIL_GIB} GiB"
echo "[准入门禁] 预计峰值=${ESTIMATED_PEAK_GIB} GiB  含 ${SAFETY_MARGIN}× 余量后需要=${NEEDED_GIB} GiB"

# 机器可读收据行。启动器按 `^cgroup_available_gib=([0-9.]+)$` 解析本行写入资源
# 准入收据；本行此前从未输出，导致解析空值 + pipefail + errexit 静默终止启动器
# （见 run_ch3_common_first_alert_fp_budget_envelope_v1.sh 的 admit_resources）。
# 必须在任何 exit 之前输出，使拒绝路径同样留下可追溯读数。
echo "cgroup_available_gib=${AVAIL_GIB}"

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
