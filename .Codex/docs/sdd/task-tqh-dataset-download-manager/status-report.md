# TQH-C2 下载与派生处理状态报告

- **状态时间**：2026-07-28 14:09 CST
- **总体状态**：A/B 下载后验收与无损解压完成；A 包级暂定物化与验收完成；B 受限门禁首版实现完成但独立审查发现 3 个重要问题，修复与重新审查前继续阻塞 B 物化；C 暂定提取完成
- **最终数据冻结**：未开始
- **候选协议阶段**：`data-protocol-v1.0-rc1` / `theory_selection` / `review_pending`
- **服务器上传**：修复版处理后候选已同步并回读验证，原始 PCAP 未上传
- **GPU 训练**：TQH-C2 C 候选基线已解除数据门禁，仍须标记 `review_pending`

## 当前资源

| 项目              | 状态                                                                                    |
| ----------------- | --------------------------------------------------------------------------------------- |
| 本机可用空间      | A/B 解压后约 `96.8 GiB`，高于 `40 GiB` 停止门槛                                         |
| C/HTTP+AES 原始包 | 大小、MD5、SHA-256、ZIP 12/12 通过并已无损解压                                          |
| A/TLS             | 下载验收与无损解压完成；顶层 12 个 PCAP 合计 `33,399,373,586` 字节                       |
| B/QUIC/HTTP3      | 下载验收与无损解压完成；顶层 12 个 PCAP 合计 `18,228,424,224` 字节                       |

## A/B 下载后验收

- A/TLS 于 `2026-07-25 01:42:56 CST` 下载完成；实测大小 `33,399,375,434` 字节，MD5 `a48cd911df671193c207f2d0589be259`，SHA-256 `699669d05c7afa990b25197aed6a79d8ecf323f1b5edf84839719aa52cd386b0`，均与既有官方记录一致。
- B/QUIC/HTTP3 于 `2026-07-25 01:17:31 CST` 下载完成；实测大小 `18,228,425,928` 字节，MD5 `fd1ce38e33bc64305fc8f6be246312e4`，SHA-256 `ae8ecd9347b94fa8aa97b8ccdce5b81beb2ad7476a8e9dd759d5b7a61e5db1d9`，均与既有官方记录一致。
- `SHA256SUMS.txt` 的 A/B 条目已独立回读；`unzip -t` 分别通过 `12/12` 个 PCAP，未发现 CRC 或 ZIP 结构错误。
- ZIP 中央目录给出的未压缩量为 A `33,399,373,586` 字节、B `18,228,424,224` 字节，合计约 `48.08 GiB`。解压前文件系统可用约 `146 GiB`，预计解压后约 `97.9 GiB`，允许继续。
- 当前无 `screen` 下载会话，未发现 `.aria2` 续传元数据。B 下载包装脚本在 aria2 明确报告完成后出现一次 `line 87: n: command not found`；由于大小、两类哈希和 ZIP 全量测试全部通过，该尾随脚本错误不影响归档有效性，但已保留日志并记入错误记录。
- A/B 已使用 `unzip -n` 无损解压到 `raw/datasets/TQH-C2-2026/extracted/`；归档继续保留。解压后分别存在 12 个顶层 cell 和 12 个 PCAP，文件总字节与 ZIP 中央目录精确一致；解压后文件系统可用约 `96.8 GiB`。

## A/B 标签预审

- A/TLS 使用现有处理器的 `audit_profile` 通过：12 个标签 cell 与 12 个 PCAP cell 一一对应，标签行数 `181,556`，UID 连接率 `1.0`，官方计数与逐行重计差异 cell 为 `0`。
- B/QUIC 在任何派生目录创建前被现有处理器拒绝：官方 12/12 个 `gate.json` 的总体状态均为 `FAIL`。所有 B cell 均未通过 `H3_balance` 与 `H7_unknown_ratio`，三个 i30 cell 还未通过 `H1_c2_signal`；全部 cell 的 `H6_no_invariant_violation` 均为 `violations=0`。
- B 的失败是官方质量门槛语义与当前处理器“只接受总体 PASS”的合同冲突，不是 ZIP、PCAP 或标签文件损坏。官方 README 明确说明 QUIC 会把多个 beacon 复用到长寿命 UDP 流，且较高 unknown 比例主要来自 QUIC 握手与基础设施伪影。
- 当前不得静默放宽 gate，也不得把 B 排除后伪称完整 A/B/C。UID 集合、五元组、标签元数据和逐行计数已独立验证；2026-07-28 用户正式批准仅适用于 B v1.0.1 的受限例外，现按 `writing-plans` → `subagent-driven-development` 实现并准备由新审查代理复核。
- B 独立只读审计已完成：12 个 cell 共 `115,734` 条标签和 `115,734` 条 `conn.log`；UID 逐 cell 唯一，缺失标签 UID、缺失连接 UID、UID 后五元组不一致、标签元数据不一致和非法标签均为 `0`。
- B 的 1.0.1 `labeled.jsonl.counts.json` 与逐行重计全部一致，当前 `malicious_c2` 合计 `5,398`；stale `manifest.json`/`gate.json` 只记录 `2,432`。这与 README 1.0.1 变更记录“全部 12 个 B cell 修正旧脚本低计数，逐流标签不变”一致。
- 裁决：B 原始标签和 UID 连接证据可用。受限例外必须同时满足版本/profile、允许失败集合、H4/H5/H6、UID、五元组、元数据、合法标签、不变量、修订计数与 C2 下限合同，并在处理器中保留 `source_gate_status=FAIL`、失败项和“1.0.1 修订计数优先于 stale gate 计数”的显式质量状态；未完成实现与独立审查前仍不得物化 B。
- 已落盘批准设计与实施计划：`2026-07-28-tqh-b-exception-and-abc-design.md`、`2026-07-28-tqh-b-exception-and-abc-implementation-plan.md`。首版实现报告为 `b-gate-implementation-report.md`，独立审查报告为 `b-gate-review-report.md`。
- 首轮独立审查裁决为严重 0、重要 3：顶层默认版本绕过显式声明、gate capture_id 未绑定当前 cell、五元组缺失或异常类型可被折叠为一致。当前未创建 B 派生目录，也未修改原始数据；修复与新审查通过前不得开机验收或物化 B。

## A 暂定包级物化

- 输出：`runs/data-frozen/dataset-v1-provisional/tqh-c2-A-20260728-v1/`；`_INCOMPLETE` 已移除，处理器退出码为 `0`，目录约 `178 MiB`。
- 提取器 SHA-256：`7daa2b2de3878660bb02860f416892d5a64aba3cc7edf5de561faa575047a617`；12 个 cell、`181,556` 条主记录、`15,761,376` 条包观测，`181,556` 个 `sample_id` 全局唯一。
- 标签分布：恶意 `12,038`、良性 `169,518`；全部记录为 `mapped` 且 `join_status=matched_packets`，无会话缺包。
- `15,777,707` 个可解析 IP 包中，匹配 `15,761,376`、未匹配 `16,331`、歧义 `0`；总体包连接率约 `99.8965%`，cell 最小/最大连接率为 `99.8754%/99.9589%`。该结果低于 C 的 100%，已作为可复核差异保留，未伪造全连接结论。
- 另计非 IP 帧 `574,166`、负相邻时间差 `433`；负间隔按既有处理器规则计数并钳为 0。12 个 cell 的标签计数差异为 0，UID 缺失为 0。
- `artifact_checksums.provisional.json` 登记的 8 个制品全部通过 SHA-256 回读；主记录和包 Parquet 可读，包表 schema 与处理器合同一致，敏感模型字段命中为 0。

## C 暂定提取

- 已验收输入：`runs/data-frozen/dataset-v1-provisional/tqh-c2-C-20260724-v8/`。
- 字节重复副本：`runs/data-frozen/dataset-v1-provisional/tqh-c2-C-20260724-v9/`。
- 主记录 `36,671` 条，包观测 `396,271` 条，12/12 cell gate 通过。
- `uid`、包连接和有包会话覆盖率均为 100%；未连接和歧义均为 0。
- 二分类映射 `35,351` 条：良性 `22,547`、恶意 `12,804`；辅助 `880`、未解析 `440` 不进入二分类候选。

## 修复后候选协议

- 生产源码：`src/flow_probe/tqh_c2_candidate.py`，SHA-256 `62b1c38e0539a7c824b1c4c57e027fdb192f020e6c54151deb1415c820aea4df`。
- 测试：`tests/test_tqh_c2_candidate.py`，SHA-256 `349b5872dfa5eacac626a466e1c969ae8a8cda8ad90cc0e8e7788d6e85bc9972`。
- 双份输出：`/tmp/tqh-candidate-c-reviewfix-a-20260724/` 与 `/tmp/tqh-candidate-c-reviewfix-b-20260724/`。
- 本地正式路径：`runs/data-frozen/dataset-candidate-c-v0/protocol/`。
- 服务器正式路径：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-frozen/dataset-candidate-c-v0/protocol/`。
- 三份目录逐字节一致；协议 SHA-256 均为 `c779ef9ae5513262ddd1ce3a14b571d01ea5e6eff17c98d13f6a634d646030d9`。
- 每份 `audit/artifact-sha256.txt` 的 12 个非自引用制品均通过；`protocol.yaml` 共登记 13 个制品。
- 样本 `35,351` 条、完整 cell `12` 个；训练/验证/开发测试为 `29,175/2,749/3,427`。
- 37 个树模型字段均为有限数值，敏感字段命中为 0，全部划分同时包含良性和恶意标签。
- 独立审查初查发现 2 个重要问题：固定标签映射未逐行验证、TCP 标志未直接受适用掩码控制。修复后独立复核为严重 0、重要 0。
- 53 个跨开发划分的同观测哈希涉及 260 条 1 至 2 包极短流，标签冲突为 0，均来自不同源捕获；基线报告必须增加去除这些哈希后的敏感性分析。

## 发布与失效记录

- 旧本地候选已原子移到 `runs/data-frozen/dataset-candidate-c-v0/protocol.invalid-review-20260724-1/`。
- 旧服务器候选已移到同名 `protocol.invalid-review-20260724-1/`，不得复用。
- 修复源码与测试在服务器的 SHA-256 与本地一致；精确测试为 `7 passed in 0.96s`。
- 服务器暂存与原子发布后的正式目录均成功加载 `35,351` 条样本和 3 份划分清单，协议 SHA-256 为 `c779ef9ae5513262ddd1ce3a14b571d01ea5e6eff17c98d13f6a634d646030d9`。
- 本地正式目录与修复 A 逐字节一致；服务器 12 个非自引用制品哈希全部通过。

## 两阶段边界

- 当前候选只允许 `theory_selection`，不能冻结最终超参数或形成论文结论。
- A/B 完成并生成完整 `dataset-v1` 后，胜出方法必须在完整训练/验证清单上重新执行 `final_tuning`。
- 最终测试 cell、GeNIS `U_test` 和留一 profile 测试域不得参与任何调参。
