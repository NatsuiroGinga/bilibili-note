# 跨年数据集替代调研证据笔记

## 任务合同

- 研究问题：是否存在比 LSPR23/24 更适合、更完整或更新、且当前可实际下载的数据集，支持跨年度加密恶意流量和实体级低误报告警。
- 用户裁决：LSPR25 不可获取。即使发现 OpenAIRE、Zenodo 或 DOI 题录，也只能记为“题录存在但实际不可用”，不得进入可执行推荐。
- 证据顺序：本地混合索引 → Zotero → 在线官方或原始论文 → 全文核验。
- 证据等级：本地全文、在线全文已下载、在线官方数据页、在线摘要、仅题录。

## 已恢复的本地锚点

- LSPR 直接证据综述：`.Codex/docs/2026-09-07-LSPR论文与跨年目标/lspr/证据综述.md`。
- CESNET-TLS-Year22 全文笔记：`wiki/papers/datasets/2024-Hynek-CESNET-TLS-Year22跨年度TLS流量数据集.md`。
- CESNET-TLS-Year22 原始论文：`raw/papers/datasets/2024-Hynek-CESNET-TLS-Year22.pdf`。
- LSPR25 状态：用户已裁决为实际不可用；本轮只核验题录与下载断点，不重新开放推荐。

## 查询日志

### Q0：工作树本地文件与全文关键词扫描

- 查询式：`LSPR25|CESNET-TLS-Year22|CICIoT2023|Edge-IIoTset|TON-IoT|HIKARI|USTC-TFC|IoT-23`。
- 工具：`fd` 与 `rg`。
- 结果：找到 CESNET-TLS-Year22 本地原始论文及全文笔记、HIKARI 原始/二次论文与既有实物核验记录、LSPR 三年度直接论文笔记；其余常见 IoT 数据主要为二次引用，仍需原始来源核验。
- 证据等级：混合，尚未据此形成候选裁决。

## 待核问题

- CESNET-TLS-Year22 是自然时间漂移数据，但其标签是否只覆盖 TLS 服务类别而非恶意性。
- CESNET 后续公开数据是否同时满足恶意标签、稳定实体键和长期时间戳。
- IoT 常用数据集是否只是单次实验场景的多日采集，不能冒充跨年度协议。
- 所谓实体键是稳定主机、设备或用户标识，还是可由标签或场景直接泄漏的攻击端点。
- 每个数据集在严格时间前向、跨期或实体隔离协议下是否已有可复现强结果；若只有随机切分高分，不能判定任务饱和。
- CESNET-TLS-Year22、CESNET-QUICEXT-25 与 CipherSpectrum 虽不一定有恶意标签，但可作为外部时间泛化或加密表示机制验证集；若升格为主数据，必须明确检测任务会变成何种服务分类任务。

## 新增裁决门：真实可优化余量

- 记录最佳公开模型、协议、主指标、随机种子或区间、错误数量或测量分辨率。
- 单独核查低误报、少数类与跨时段分面是否仍有明显错误；不能用任意准确率阈值代替误差分析。
- 若现实协议主要指标及运营分面均接近测量上界，归入不推荐；若只在随机切分饱和、跨时段显著下降，则保留。

## 本地混合检索与 Zotero

- 本地查询覆盖“跨年度网络安全时间漂移”“CESNET/CipherSpectrum”“恶意软件时间数据”“2025/2026 新数据”“CIC-YNU-IoTMal/DRIFT/HiGraph”和“RWKV 长序列流量”。
- 主要本地命中：CESNET-TLS-Year22、LSPR 证据链、TabReD 时间切分方法论、低误报 EMBER/SOREL 全文、NetMamba/Traffic-MoE 状态空间流量论文。
- 索引在其他代理写入期间两次变旧；最终增量构建完成，含 1983 篇笔记、150595 个分块。只使用成功返回结果，不把等待锁或陈旧索引错误记为无命中。
- Zotero 已入库直接命中：CESNET-TLS-Year22（`QNZBK4SZ`）、加密流量漂移实证（`J52MSFUI`）、NetFlow 时间分析（`CUX69W2P`）、NetMamba（`FZ2V7G5U`）、MambaNetBurst（`LHMCT94Z`）。
- Zotero 题录和摘要只用于发现；字段、下载和许可回到官方数据页核验。

## 在线原始来源与全文核验

### DRIFT-DGA，2026

- 原始论文：`https://arxiv.org/abs/2605.10436`；代码：`https://github.com/snsec-net/2026-DSN-DRIFT`；数据：`https://huggingface.co/datasets/snsec-net/dga-detection-drift26dsn`。
- 全文已用 `mineru-open-api extract` 提取到会话临时文件 `/tmp/drift-dga-2605.10436.md`。
- 2017–2025 九年；约 4940 万唯一良性域名、1.494 亿唯一 DGA 域名、148 个家族；Hugging Face 打包 12 GB。
- 协议为 2017–2019 训练/验证，2020–2025 逐年未来测试。年度 `train/test` 名称只是年内分片，不是时间角色。
- DRIFT 在 2020–2025 微平均 Accuracy `0.952763`、Precision `0.981770`、Recall `0.948077`、F1 `0.964630`；2025 FPR `0.096520`、FNR `0.066817`；未来未见家族 FNR `0.143913`。低误报与未知家族明显未饱和。
- 本轮未定位到多种子区间，标待证。域名字串有自然字符顺序与因果前缀，但很短、每个域名独立重置，且无主机连续事件键；RWKV 适配为中。

### CESNET-QUICEXT-25，2025

- 官方发布：`https://zenodo.org/records/17249078`；工具：`https://cesnet.github.io/cesnet-datazoo/`。
- 发布 2025-10-02；采集 2024-06-01 至 2025-05-31。约 1.94 亿 QUIC 流、50 应用类和 3 背景类；12 月文件共 28.2 GB，直接下载。
- 真实 ISP 流，统一 `1:100` 抽样且不平衡。字段含小时化时间、匿名目的主机/子网、QUIC 连接标识、SNI、用户代理、TLS 扩展和前 30 包 PPI。
- 不含客户端 IP；目的主机和 SNI 接近服务标签，不能当无风险输入或实体键。官方数据说明论文仍在准备；2026 时间切分预印本的同行评审、多种子和完整分面待证。
- PPI 顺序天然因果但仅 30 包，跨流无客户端键；RWKV 适配为中低。

### CESNET-TLS-Year22 与 CESNET-TimeSeries24

- CESNET-TLS-Year22 本地全文已核验：发布 2024、采集 2022 全年、约 5.07 亿 TLS 流、180 服务和 24 类。同期验证准确率 `97.2%`，T+1 `96.3%`，T+8 `90.5%`，说明时间误差未饱和。第 10 周导出器升级形成采集漂移，必须分段。
- CESNET-TimeSeries24 官方数据：`https://zenodo.org/records/13382427`；工具：`https://github.com/CESNET/cesnet-tszoo`。论文发布 2025，采集 2023–2024 共 40 周，含 275124 IP、548 子网、283 机构，提供 10 分钟/小时/天序列。完整 41.5 GB，样本 170.9 MB。
- TimeSeries24 的时间轴、因果前缀、实体重置键和跨窗口依赖最适合 RWKV，但没有原生恶意标签；监督低误报前沿不可测，不能直接替代主任务。

### CipherSpectrum、EMBER2024、HiGraph、CIC-YNU-IoTMal

- CipherSpectrum 官方页：`https://cgi.cse.unsw.edu.au/~cspectrum/`。S&P 2025 发布，采集 2024-01 至 2024-03；120000 个 TLS 1.3 PCAP 会话、40 域名、三套密码；CC BY-NC 4.0，填短表即下载。只有三个月受控浏览器流、平衡标签、无恶意与稳定实体，不能作时间漂移主数据。
- EMBER2024：`https://arxiv.org/abs/2506.05074`、`https://github.com/FutureComputing4AI/EMBER2024`。KDD 2025，超过 320 万文件、六种格式、七类任务和逃逸挑战；特征/标签公开，Apache-2.0，原始文件需 VirusTotal。公开输入是一文件一行静态特征，RWKV 状态适配低。
- HiGraph：`https://www.higraph.org/`。2025 发布，当前官方页记 499981 个 Android 应用，2012–2022，50661 恶意、449320 良性、683 家族；CC BY-NC-SA 4.0。arXiv 早期摘要约 595K，与当前版冲突待核。层次图没有唯一因果遍历，RWKV 适配低。
- CIC-YNU-IoTMal：`https://www.unb.ca/cic/datasets/ynu-iot-2026.html`。2026 发布，10000 个 IoT 恶意样本在 QEMU/OpenWrt 沙箱执行，含 PCAP/STRACE/SAR；良性由大语言模型生成。未给多年轴或前向强基线，只能列探索候选。

### 传统候选

- SOREL-20M：2000 万 PE、首见时间、5 种子 LightGBM/FFNN 和低 FPR条件较完整，但训练特征约 172 GB、完整数据约 8 TB，且是静态行。
- BODMAS：2019-08 至 2020-09，57293 恶意、77142 良性、581 家族；约 250 MB 特征和 12 MB 元数据公开，适合廉价时间漂移基线，但无自然跨样本状态。
- EMBER2017/2018：可做时间测试，但两年度选择准则不一致，官方明确警告；优先级低于 EMBER2024。
- AndroZoo/TESSERACT：已有 2014–2018 五年严格时间实验，但数据访问和 VirusTotal 标签有门槛，不是开箱即用数据集。

## 工具异常与引用核验

- `scholar lookup --json` 已尝试核验 DRIFT、CESNET-QUICEXT-25 和 EMBER2024，但本机 Scholar CLI 无认证 cookie，三次均返回 `No cookies found`。未为本轮启动浏览器认证。
- 题录改由官方论文页、DOI、出版社或官方仓库交叉核验。
- MinerU 首次在沙箱内因二进制权限失败；经允许调用已认证 `extract` 成功提取 DRIFT 全文，全程未输出令牌。

## RWKV-8 候选输入合同补充

- ROSA：仅把重复、离散、因果的符号/事件后缀视为直接适配。DRIFT 域名字符最干净；CIC-YNU 系统调用次之；CESNET 与 LSPR 只有协议事件直接适配，连续包长、间隔和流统计必须量化并做独立消融。
- DeepEmbed：DRIFT 字符/子词、CIC-YNU 系统调用和 LSPR 协议/字段类别可形成可解释词表；跨期须报告 OOV。IP、域名、主机哈希等身份字段禁作无约束嵌入。
- DeepEmbedAttention：官方定义未在本轮核验，保持待证，不依据名称推断能力。
