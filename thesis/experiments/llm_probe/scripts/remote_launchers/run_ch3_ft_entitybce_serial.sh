#!/usr/bin/env bash
# 第三章新四格（含共同底座实体级 BCE）＋ 无底座参照臂的串行执行器。
#
# 2026-09-04 用户裁决（方案 A）：沿用协议 A 冻结划分 validation_fraction=0.10、
# 新四格（含共同底座实体级 BCE，w_e=1303 实测标定）、half 档。
# 0.20 划分被协议 A 的冻结切分统计断言阻断（该文件被 36 份配置以 tool_sha256 冻结引用），
# 故不改划分；无底座参照直接用既有 C00-half 0.650418 与 C01-half 0.886216。
# 四臂即主四格。「实体级 BCE 是否稀释 BER 增益」用既有 0.10 无底座读数作参照，
# 无需另跑参照臂——这是选择方案 A 的直接收益。
#
# 串行而非并行：单卡，且并行会污染步速与显存读数。
# 每臂结束后核对退出码；某臂失败即停止后续，保留现场供诊断，不自动重试。

set -u

ROOT="/root/autodl-tmp/thesis/experiments/llm_probe"
LOGDIR="${ROOT}/runs/diagnostics/logs"
mkdir -p "${LOGDIR}"

ARMS=(
  "ch3-ft-c00-entitybce-halfwidth-screening-v1"
  "ch3-ft-c10-entitybce-halfwidth-screening-v1"
  "ch3-ft-c01-entitybce-halfwidth-screening-v1"
  "ch3-ft-c11-entitybce-halfwidth-screening-v1"
)

cd "${ROOT}" || exit 1
echo "=== 串行链启动 $(date '+%F %T') 共 ${#ARMS[@]} 臂（新四格，0.10 划分） ==="

for arm in "${ARMS[@]}"; do
  log="${LOGDIR}/${arm}.log"
  echo "--- 启动 ${arm} $(date '+%F %T') ---"
  uv run --no-sync python tools/ch3_ft_c00_dual_selection.py \
    --config "configs/${arm}.json" --run > "${log}" 2>&1
  rc=$?
  echo "--- ${arm} 结束 $(date '+%F %T') 退出码 ${rc} ---"
  if [ "${rc}" -ne 0 ]; then
    echo "!!! ${arm} 失败，链停止；现场保留在 ${log} 与 runs/diagnostics/${arm}/"
    exit "${rc}"
  fi
done

echo "=== 四臂全部完成 $(date '+%F %T') ==="
