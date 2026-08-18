#!/usr/bin/env bash
# TQH-C2 旧版（v1.0.1）分级删除。用户 2026-08-12 明确授权方案 A。
#
# 前置：必须先由 tqh_c2_v120_acceptance.sh 产出收据且裁决为"全部通过"。
# 只删两项独占且已作废的制品；硬链接文件与证据锚点元数据一律保留。
set -uo pipefail

OLD=/Users/bilibili/personal/note/raw/datasets/TQH-C2-2026
NEW=/Users/bilibili/personal/note/raw/datasets/TQH-C2-v1.2.0
RECEIPT=/Users/bilibili/personal/note/.Codex/docs/2026-08-12-TQH-C2-v1.2.0验收收据.md

echo "===== 前置断言 ====="

if [ ! -f "$RECEIPT" ]; then
  echo "拒绝：验收收据不存在，先运行 tools/tqh_c2_v120_acceptance.sh"; exit 10
fi
if ! grep -q "全部通过，允许执行旧版删除" "$RECEIPT"; then
  echo "拒绝：收据裁决不是「全部通过」"; exit 11
fi
echo "  收据存在且裁决通过"

# 新版必须完整：11 个文件一个都不能少
NEW_COUNT=$(ls -1 "$NEW" | wc -l | tr -d ' ')
if [ "$NEW_COUNT" -lt 11 ]; then
  echo "拒绝：v1.2.0 目录只有 $NEW_COUNT 项，少于 11"; exit 12
fi
echo "  v1.2.0 目录 $NEW_COUNT 项"

# 硬链接断言：A 与 C 必须与新版同 inode，否则删除会毁掉唯一副本
for pair in "TQH-C2_pcap_A_sliver_tls.zip" "TQH-C2_pcap_C_mythic_http.zip"; do
  I_OLD=$(stat -f %i "$OLD/pcap_archives/$pair" 2>/dev/null || echo x)
  I_NEW=$(stat -f %i "$NEW/$pair" 2>/dev/null || echo y)
  if [ "$I_OLD" != "$I_NEW" ]; then
    echo "拒绝：$pair 新旧 inode 不同（$I_OLD vs $I_NEW），不是硬链接"; exit 13
  fi
  echo "  $pair 硬链接确认 inode=$I_OLD"
done

echo
echo "===== 删除目标（仅此两项）====="
TARGETS=(
  "$OLD/extracted"
  "$OLD/pcap_archives/TQH-C2_pcap_B_merlin_quic.zip"
)
for t in "${TARGETS[@]}"; do
  if [ -e "$t" ]; then
    printf "  %-70s %s\n" "$t" "$(du -sh "$t" 2>/dev/null | cut -f1)"
  else
    printf "  %-70s （已不存在）\n" "$t"
  fi
done

echo
echo "===== 保留清单 ====="
echo "  $OLD/README.md            证据 D01 按行号引用"
echo "  $OLD/SHA256SUMS.txt"
echo "  $OLD/TQH-C2_features.zip  v1.0.1 特征，历史结果复现锚"
echo "  $OLD/TQH-C2_labels.zip"
echo "  $OLD/pcap_archives/TQH-C2_pcap_A_sliver_tls.zip   硬链接，删了不释放空间"
echo "  $OLD/pcap_archives/TQH-C2_pcap_C_mythic_http.zip  硬链接"
echo "  $OLD/TQH-C2_scripts.zip                            硬链接"

BEFORE=$(df -g /Users/bilibili/personal/note | awk 'NR==2 {print $4}')
echo
echo "===== 执行 ====="
echo "删除前可用磁盘：${BEFORE} GiB"

for t in "${TARGETS[@]}"; do
  if [ -e "$t" ]; then
    rm -rf "$t"
    echo "  已删除 $t"
  fi
done

AFTER=$(df -g /Users/bilibili/personal/note | awk 'NR==2 {print $4}')
echo "删除后可用磁盘：${AFTER} GiB"
echo "释放约 $((AFTER - BEFORE)) GiB"

echo
echo "===== 删除后旧目录残留 ====="
du -sh "$OLD" 2>/dev/null
ls -la "$OLD"
echo
echo "===== v1.2.0 完好性复查 ====="
ls -1 "$NEW" | wc -l
du -sh "$NEW" 2>/dev/null
