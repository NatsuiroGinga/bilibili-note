#!/usr/bin/env bash
# TQH-C2 v1.2.0 验收门槛 3、4：ZIP 完整性检查 + 收据落盘。
# 依据 .Codex/docs/2026-08-06-TQH-C2-v1.2.0下载与替换计划.md 第 18-25 行。
# 只读校验，不删除任何文件；删除由独立脚本执行且要求本收据存在。
set -uo pipefail

ROOT=/Users/bilibili/personal/note/raw/datasets/TQH-C2-v1.2.0
RECEIPT=/Users/bilibili/personal/note/.Codex/docs/2026-08-12-TQH-C2-v1.2.0验收收据.md
cd "$ROOT" || exit 3

echo "===== 门槛 1：清单完整性 ====="
EXPECTED=(
  README_v120.md SHA256SUMS_v120.txt
  TQH-C2_features_D.zip TQH-C2_features_v110.zip
  TQH-C2_labels_D.zip TQH-C2_labels_v110.zip
  TQH-C2_pcap_A_sliver_tls.zip TQH-C2_pcap_B_merlin_quic_v110.zip
  TQH-C2_pcap_C_mythic_http.zip TQH-C2_pcap_D_merlin_h2.zip
  TQH-C2_scripts.zip
)
MISSING=0
for f in "${EXPECTED[@]}"; do
  if [ -f "$f" ]; then
    printf "  OK   %-40s %s 字节\n" "$f" "$(stat -f %z "$f")"
  else
    printf "  缺失 %s\n" "$f"; MISSING=$((MISSING + 1))
  fi
done
echo "缺失数=$MISSING"

echo
echo "===== 门槛 2：官方 SHA-256 ====="
SHA_OUT=$(shasum -a 256 -c SHA256SUMS_v120.txt 2>&1)
echo "$SHA_OUT"
SHA_FAIL=$(echo "$SHA_OUT" | grep -c "FAILED" || true)
echo "校验失败数=$SHA_FAIL"

echo
echo "===== 门槛 3：ZIP 完整性 ====="
ZIP_FAIL=0
ZIP_LINES=""
for z in *.zip; do
  START=$(date +%s)
  if unzip -t "$z" > /dev/null 2>&1; then
    RESULT="OK"
  else
    RESULT="FAILED"; ZIP_FAIL=$((ZIP_FAIL + 1))
  fi
  ELAPSED=$(( $(date +%s) - START ))
  printf "  %-6s %-40s %s 秒\n" "$RESULT" "$z" "$ELAPSED"
  ZIP_LINES="${ZIP_LINES}| \`${z}\` | ${RESULT} | ${ELAPSED} 秒 |"$'\n'
done
echo "ZIP 失败数=$ZIP_FAIL"

echo
echo "===== 门槛 4：收据落盘 ====="
if [ "$MISSING" -eq 0 ] && [ "$SHA_FAIL" -eq 0 ] && [ "$ZIP_FAIL" -eq 0 ]; then
  VERDICT="全部通过，允许执行旧版删除"
else
  VERDICT="未通过，禁止删除旧版"
fi

{
  echo "# TQH-C2 v1.2.0 验收收据"
  echo
  echo "- **生成时间**：$(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "- **官方记录**：https://zenodo.org/records/21523144"
  echo "- **版本**：1.2.0，发布日期 2026-07-24，DOI \`10.5281/zenodo.21523144\`"
  echo "- **许可证**：Creative Commons Attribution 4.0 International"
  echo "- **作者**：Jeon, Deokjo（aSSIST）；Park, DongGue（Soonchunhyang University）"
  echo "- **本机目录**：\`raw/datasets/TQH-C2-v1.2.0/\`"
  echo "- **验收依据**：[下载与替换计划](2026-08-06-TQH-C2-v1.2.0下载与替换计划.md) 第 18-25 行"
  echo
  echo "## 裁决"
  echo
  echo "**$VERDICT**"
  echo
  echo "| 门槛 | 结果 |"
  echo "| --- | --- |"
  echo "| 1 清单十一项齐全 | 缺失 $MISSING 项 |"
  echo "| 2 官方 SHA-256 | 失败 $SHA_FAIL 项 |"
  echo "| 3 ZIP 完整性 | 失败 $ZIP_FAIL 项 |"
  echo "| 4 收据落盘 | 本文件 |"
  echo
  echo "## ZIP 完整性明细"
  echo
  echo "| 文件 | 结果 | 耗时 |"
  echo "| --- | --- | --- |"
  printf '%s' "$ZIP_LINES"
  echo
  echo "## SHA-256 明细"
  echo
  echo '```'
  echo "$SHA_OUT"
  echo '```'
  echo
  echo "## 官方数据集构成（Zenodo 记录）"
  echo
  echo "- 测试床 A：Sliver over TLS"
  echo "- 测试床 B：Merlin over HTTP/3/QUIC"
  echo "- 测试床 C：Mythic over HTTP，AES 加密载荷"
  echo "- 测试床 D：Merlin over HTTP/2（v1.2.0 新增）"
  echo "- 网格：36 格 = 3 种加密配置 × 4 个信标间隔（30/300/1800/3600 秒）× 3 个抖动档（0/30/70%），每格含并发良性流量"
  echo "- 交付物：逐格原始 PCAP、Zeek 日志、逐流 MITRE ATT&CK 标签（\`labeled.jsonl\`）、Parquet 特征表（含 JA4/JA4S/JA4H 指纹）、可复现的采集/标注/特征提取代码、SHA-256 清单"
  echo
  echo "## 旧版处置"
  echo
  echo "旧版目录 \`raw/datasets/TQH-C2-2026/\`（v1.0.1）按用户裁决采用分级删除："
  echo
  echo "- **删除**：\`extracted/\`（约 49 GB，旧版 PCAP 解压副本）、\`pcap_archives/TQH-C2_pcap_B_merlin_quic.zip\`（18.2 GB，官方已废弃的失效单向采集）"
  echo "- **保留**：\`README.md\`、\`SHA256SUMS.txt\`、\`TQH-C2_features.zip\`、\`TQH-C2_labels.zip\`（合计约 78 MB），因为 \`.Codex/docs/sdd/task-dataset-protocol-review/evidence-table.md\` 的证据 D01 按行号引用旧版 README.md，\`wiki/papers/datasets/data-protocol/INDEX.md\` 亦有 wikilink"
  echo "- **保留**：\`pcap_archives/TQH-C2_pcap_A_sliver_tls.zip\`、\`TQH-C2_pcap_C_mythic_http.zip\`、\`TQH-C2_scripts.zip\`——实测与 v1.2.0 同 inode（\`11513430\`、\`11454904\`），是硬链接，删除不释放空间"
} > "$RECEIPT"

echo "收据已写入 $RECEIPT"
echo
echo "最终裁决：$VERDICT"
[ "$MISSING" -eq 0 ] && [ "$SHA_FAIL" -eq 0 ] && [ "$ZIP_FAIL" -eq 0 ]
