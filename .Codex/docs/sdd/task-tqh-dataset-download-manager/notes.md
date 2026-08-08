# TQH-C2 数据集下载与派生处理笔记

## 2026-07-24 初始盘点

- 本机初始可用空间：`201 GiB`；C 解压和 A 启动后为 `198 GiB`。
- TQH-C2 原始目录当前占用：`436 MiB`。
- 已存在 `TQH-C2_pcap_C_mythic_http.zip`、特征包、标签包、脚本包、来源说明和 SHA-256 清单。
- C 包既有报告值：大小 `379187915` 字节，MD5 `d29f8f2c9cfb05847cae7e39de957d69`，ZIP 完整性通过；仍需本任务独立回读复核并写入下载清单。
- A/TLS 与 B/QUIC 当前未发现本地压缩包。
- 文献协议代理尚在做参考文献、Zotero 和最终验收；所有本轮字段、划分和视图均为临时状态。

## C 包验收

- 实际大小：`379187915` 字节，与期望值一致。
- 实际 MD5：`d29f8f2c9cfb05847cae7e39de957d69`，与既有官方值一致。
- 实际 SHA-256：`522ab75ed1de642492f24d4276cc79004a69d09931b4ad3d1f1998f9b8121cbf`，与官方 `SHA256SUMS.txt` 一致。
- `unzip -t`：12/12 个 PCAP 通过，压缩包无错误。
- 无损解压目录：`raw/datasets/TQH-C2-2026/extracted/`，12 个 C cell 共 12 个 PCAP。
- 标签、特征和脚本包的 SHA-256 均与官方清单一致并已无损解压。

## 标签审计发现

- 12 个 C cell 的 `labeled.jsonl` 与随包 `label_v3_topo.py` 重生成结果逐字节一致。
- 3 个未修订 cell 的计数摘要也逐字节一致。
- README 说明的 9 个 C cell 的 1.0.1 修订计数与随包脚本重生成摘要不同。
- 根因证据：随包脚本仍把 `REJ`、`S0` 或双向零字节的 `malicious_c2` 从主类计数扣出，但 1.0.1 修订计数按逐流标签行计数。例如 `C_i30_j70` 官方为 `2369`，脚本重生成为 `2359`。
- 处理决策：逐流标签不变；全部类别统计由 `labeled.jsonl` 重新计数，官方 counts 和脚本 counts 仅作交叉审计。

## A 下载状态

- 后台会话：`tqh-c2-download-A`。
- 控制台日志：`thesis/experiments/llm_probe/runs/data-downloads/tqh-c2-pcap-20260724/A/console.log`。
- 目标文件：`raw/datasets/TQH-C2-2026/pcap_archives/TQH-C2_pcap_A_sliver_tls.zip`。
- 期望大小：`33399375434` 字节；官方 MD5：`a48cd911df671193c207f2d0589be259`；官方 SHA-256：`699669d05c7afa990b25197aed6a79d8ecf323f1b5edf84839719aa52cd386b0`。
- 2026-07-24 15:38 实际落盘约 `280 MiB`，8 连接速率约 `0.4 MiB/s`，预计约 `22` 小时。
- 范围测速：API 端点 `36,353 B/s`；官方记录页端点 `97,127 B/s`。后者仍低于现有 8 连接总速率，因此不切换、不重启、不删除 `.aria2` 进度。
- 本机不存在 `/etc/network_turbo`，该测速项不可用。

## B 下载状态

- 后台会话：`tqh-c2-download-B`，与 A 独立运行。
- 控制台日志：`thesis/experiments/llm_probe/runs/data-downloads/tqh-c2-pcap-20260724/B/console.log`。
- 目标文件：`raw/datasets/TQH-C2-2026/pcap_archives/TQH-C2_pcap_B_merlin_quic.zip`，续传元数据为同名 `.aria2`。
- 期望大小：`18228425928` 字节；官方 MD5：`fd1ce38e33bc64305fc8f6be246312e4`；官方 SHA-256：`ae8ecd9347b94fa8aa97b8ccdce5b81beb2ad7476a8e9dd759d5b7a61e5db1d9`。
- 2026-07-24 16:14 最新约 `19 MiB/16 GiB`，8 连接速率约 `293 KiB/s`，aria2 估算约 `16` 小时 `49` 分钟。

## 2026-07-28 A/B 下载后验收

- A 于 `2026-07-25 01:42:56 CST` 完成，实测大小 `33,399,375,434` 字节；MD5 为 `a48cd911df671193c207f2d0589be259`，SHA-256 为 `699669d05c7afa990b25197aed6a79d8ecf323f1b5edf84839719aa52cd386b0`。
- B 于 `2026-07-25 01:17:31 CST` 完成，实测大小 `18,228,425,928` 字节；MD5 为 `fd1ce38e33bc64305fc8f6be246312e4`，SHA-256 为 `ae8ecd9347b94fa8aa97b8ccdce5b81beb2ad7476a8e9dd759d5b7a61e5db1d9`。
- A/B 的大小、MD5 和 SHA-256 均与官方记录一致；`unzip -t` 分别通过 12/12 个 PCAP。
- A/B 未压缩总量为 `51,627,797,810` 字节，约 `48.08 GiB`。解压前可用约 `146 GiB`，解压后预计约 `97.9 GiB`，通过主任务规定的 `40 GiB` 停止门槛。
- 当前无下载 `screen` 会话，未发现 `.aria2` 文件。B 下载包装脚本在下载完成后出现 `line 87: n: command not found`，但归档全部验收门禁通过，判定为不影响数据的尾随脚本错误。
- A/B 使用 `unzip -n` 解压到既有 `extracted/` 根目录，未覆盖 `extracted/A/`、`extracted/B/` 标签目录或既有 C PCAP。A/B 各 12 个顶层 PCAP，文件总字节分别为 `33,399,373,586` 与 `18,228,424,224`，和 ZIP 中央目录一致。
- 解压后 `raw/datasets/TQH-C2-2026/` 约占 `98 GiB`，其中 `extracted/` 约占 `49 GiB`；文件系统可用 `101,483,192 KiB`，约 `96.8 GiB`。
- 首次 A 文件统计命令因 zsh 数组换行展开错误把 12 个路径合成一个参数，`stat` 只读失败；改用 `fd -x stat` 后验证通过，数据未受影响。

## A/B 标签预审阻塞

- A 的 `audit_profile` 通过：`cell_count=12`、`label_rows=181556`、`uid_join_rate=1.0`、`counts_difference_cells=0`。
- B 的 12 个 `gate.json` 总体均为 `FAIL`。共同失败项为 `H3_balance` 和 `H7_unknown_ratio`；i30/j0、i30/j30、i30/j70 还失败 `H1_c2_signal`，各自只有 15 个流级 C2 连接。
- 所有 B cell 的 `H6_no_invariant_violation` 均通过且 violations 为 0。README 说明 B/QUIC 把多个 beacon 复用进长寿命 UDP 流，流级 C2 数不等于 beacon 数；unknown 主要是 QUIC 0-RTT/握手和网络基础设施伪影。
- 现有 `_load_cell_records` 在任何逐行 UID 与五元组检查之前强制总体 gate 必须为 PASS，因此无法区分数据破损与 B 的已知质量失败。不能临时删除这项检查；应增加只对已知 B 失败模式生效的显式审计合同，并保留原始 gate 状态、失败项和训练排除规则。
- 独立 `jq` 审计 12 个 B cell：标签与 `conn.log` 各 `115,734` 行；标签 UID 和连接 UID 均逐 cell 唯一；缺失连接 UID、缺失标签 UID、五元组不一致、capture/profile/interval/jitter 元数据不一致、非法标签均为 0。
- 1.0.1 计数文件与逐行标签重计全部一致，B 当前 `malicious_c2=5,398`；stale manifest/gate 合计仅 `2,432`。各 cell 当前 C2 为 i30 `98/105/105`、i300 `532/629/705`、i1800 `460/540/612`、i3600 `458/542/612`，与 README 实测范围一致。
- 安全例外只能基于以下同时成立的条件：profile 固定为 B；版本固定为 1.0.1；UID/五元组/元数据/标签/计数审计全部通过；H4/H5/H6 等身份与不变量门禁通过；失败项仅属于已解释的 QUIC 长流、类平衡或 unknown 比例；输出保留源 gate 失败状态，训练主任务排除 `unknown`。

## A 暂定包级物化结果

- 输出目录 `runs/data-frozen/dataset-v1-provisional/tqh-c2-A-20260728-v1/`，约 `178 MiB`；主记录 Parquet 约 `18 MiB`，包观测 Parquet 约 `154 MiB`。
- 处理器版本 SHA-256 为 `7daa2b2de3878660bb02860f416892d5a64aba3cc7edf5de561faa575047a617`。运行生成 12 cell、181,556 条主记录、15,761,376 条包记录和 246 个包 Parquet row group。
- 主记录 `sample_id` 唯一数为 181,556；profile 仅 A；全部 `join_status` 为 `matched_packets`。标签为良性 169,518、恶意 12,038。
- 16,351,873 个 PCAP 帧中，574,166 个非 IP；15,777,707 个可解析 IP 包中匹配 15,761,376、未匹配 16,331、歧义 0。总体连接率约 99.8965%，12 个 cell 均有 100% 会话覆盖。
- 负相邻时间差 433 个；按处理器固定规则记录并将模型间隔钳为 0。所有 8 个登记制品哈希通过，敏感字段命中为 0。

## C 暂定物化审计

- `tqh-c2-C-20260724-v2` 生成 36,671 条主记录与 396,271 条包观测；12/12 gate 通过。
- 36,671 个 `uid` 全部连接，缺失为 0；396,271 个可用 IP 包全部唯一连接，未连接与歧义均为 0，所有主记录均至少有一个包。
- 526,835 个 PCAP 帧中有 130,564 个非 IP 帧按规则隔离；文件顺序内发现 50 个负相邻时间差，已计数并将模型间隔钳为 0。
- 880 条 `malicious_recon` 按候选协议标为 `auxiliary`，440 条 `unknown` 标为 `unresolved`；二者不进入 C2 主任务二元映射，属于预期行为。
- 独立回读发现 `sample_id` 在泄漏审计元数据中被误列为模型输入。处理器将其保留为包表关联键，但字段角色改为 `audit_only`，模型输入清单排除该列。

## 待核实

- A、B、C 的许可证记录已确认 CC BY 4.0；下载地址、期望大小、MD5 与 SHA-256 已获得，仍需 A/B 完成后实测核对。
- 特征、标签、脚本包的内部目录结构及 36 个完整采集单元映射。
- 本机没有 `tshark`、`capinfos`、`editcap`，但有 `/usr/sbin/tcpdump`；项目锁定的 `pyarrow==25.0.0` 已安装到既有 `.venv`。
- 已受控核对，无旧 `aria2c`、`curl`、`wget` 或 TQH-C2 下载进程。

## 风险

- 约 51 GiB 指压缩包还是展开后大小尚未核实；解压前必须估算总空间。
- 官方若未发布 A/B 校验值，不得伪造“官方哈希”；应明确记录“官方未提供”，同时保存本机 SHA-256。
- 不能把目录名或文件名直接推断为标签；标签连接必须以官方标签表或脚本契约为准。

## C 组首次物化失败

- 输出目录：`runs/data-frozen/dataset-v1-provisional/tqh-c2-C-20260724-v1/`，保留不删除。
- 失败发生在 PCAP 扫描和 Parquet 写入前，错误为包观测字段预算拒绝 `capture_truncated`。
- 根因：敏感字段检查按下划线分词，合法的截断掩码名称含有敏感词 `capture`，属于名称误报，不是数据泄漏。
- 单点修复：模型视图列改名为 `truncation_mask`；内部 `ParsedPacket.capture_truncated` 仍保持原语义。

## C-only 候选协议验收

- 当前生产源码 SHA-256：`62b1c38e0539a7c824b1c4c57e027fdb192f020e6c54151deb1415c820aea4df`。
- 当前测试 SHA-256：`349b5872dfa5eacac626a466e1c969ae8a8cda8ad90cc0e8e7788d6e85bc9972`。
- 修复后双份目录 `/tmp/tqh-candidate-c-reviewfix-a-20260724/` 与 `/tmp/tqh-candidate-c-reviewfix-b-20260724/` 逐字节一致，协议 SHA-256 均为 `c779ef9ae5513262ddd1ce3a14b571d01ea5e6eff17c98d13f6a634d646030d9`。
- 候选含 `35,351` 条 mapped 样本和 12 个完整 cell；训练、验证、开发测试分别为 `29,175`、`2,749`、`3,427`。
- 模型视图固定 37 个有限数值字段，不包含样本身份、标签、地址、端口、路径、cell、profile、interval、jitter、capture 或来源哈希。
- P0 子集筛查发现 53 个跨开发划分的相同观测序列哈希，涉及 260 条 1 至 2 包极短流；全部标签一致且源捕获不同。完整 cell 约束下不删除样本，基线必须补充去除这些哈希后的敏感性分析。

## 独立审查修复

- 初查发现 2 个重要问题：候选输入未逐行验证 `native_label → binary_label/label_status` 固定映射；TCP 标志位特征未直接受 `tcp_flags_applicable` 控制。
- 修复后逐行拒绝错误标签映射；要求 TCP 标志适用掩码与传输族一致、掩码为假时非零值直接失败，并让标志位特征显式受掩码控制。
- 固定夹具覆盖非 TCP 合法空 `tcp_flags`、三类错误标签契约和掩码为假时非零标志。
- 独立复核最终为严重 0、重要 0；服务器精确测试 `7 passed in 0.96s`。
- 旧候选在本地和服务器均保留为 `protocol.invalid-review-20260724-1/`，不得复用。

## 正式候选发布

- 本地正式路径：`runs/data-frozen/dataset-candidate-c-v0/protocol/`。
- 服务器正式路径：`/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-frozen/dataset-candidate-c-v0/protocol/`。
- 服务器暂存目录的 12 个非自引用制品哈希全部通过；暂存与原子发布后的正式路径均加载 `35,351` 条样本和 3 份清单，协议 SHA-256 一致。
- 当前协议为 `data-protocol-v1.0-rc1` / `theory_selection` / `review_pending`，只允许暂定理论筛选。完整 A/B 与三源 `dataset-v1` 完成后必须重新执行 `final_tuning`。
