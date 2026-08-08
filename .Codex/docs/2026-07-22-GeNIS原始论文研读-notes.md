# GeNIS 与 HIKARI 论文研读证据笔记

## GeNIS 来源核验

- 初始 PDF：`raw/papers/1-s2.0-S2352340925002197-main.pdf`，SHA-256 为 `db5ee7b93ee9f9158354a036cdaf0c7c7d445a71ef97c0ccc75359b1abcfe1b2`。
- 第二份 PDF：`raw/papers/1-s2.0-S2352340925002197-main (2).pdf`，SHA-256 为 `58d2180a12b7e89739d384c0b27a4f1af3904213e67a483c43edf64049f76ad5`。
- 两份文件题名、作者、期刊、年份、DOI 和 14 页元数据相同，均为 GeNIS 原始数据论文。
- 初始 PDF 页面树损坏，只能读出印刷页 1、8 至 14；第二份可完整读出印刷页 1 至 14。
- 初始 PDF 可读页与第二份对应页的逐页文本 SHA-256 全部相同，因此第一份是缺页下载副本，不是独立版本。
- 逐页事实引用以完整的第二份 PDF 为准；`source_pdf` 仍保留用户最初指定的文件，并在笔记中增加完整副本字段。

## GeNIS 论文事实

- 题名：`GeNIS: A modular dataset for network intrusion detection and classification`。
- 作者：Miguel Silva、Daniela Pinto、João Vitorino、José Gonçalves、Eva Maia、Isabel Praça。
- 期刊：`Data in Brief`，第 60 卷，文章号 111487，2025 年。
- DOI：`10.1016/j.dib.2025.111487`。
- 数据在 Airbus CyberRange 上生成，2025-02-06 至 2025-02-12 采集；良性活动为 6 至 7 日，背景为 8 日，攻击为 10 至 12 日（PDF 第 5 至 6 页）。
- 图 1 展示 DMZ、服务器、管理员、用户、远程用户和路由互联段；攻击者位于用户网与远程用户网（PDF 第 6 至 8 页、图 1）。
- 八个攻击场景均由 DNS 发现、NMAP 侦察和具体攻击组成，中间约暂停 5 分钟；攻击包括 Hulk、Slowloris、UDP、ICMP、Push/Ack、SMB 暴力破解、SSH 暴力破解及 SSH+FTP 暴力破解（PDF 第 8 至 12 页、表 4 至 11）。
- 数据按 `0-info`、`1-packets`、`2-flows`、`3-scenarios`、`4-preprocessed` 五层组织；流间隔为 5、10、30、60 秒（PDF 第 3 至 5 页）。
- `4-preprocessed` 仅说明采用打乱与分层形成训练集和留出集，没有验证集，也没有时间、会话或场景防泄漏协议（PDF 第 5 页）。
- 论文报告 37,681,001 个包、2,737,930,223 字节；四种间隔分别形成 2,806,168、1,504,184、607,933、368,556 条流（PDF 第 12 页、表 12）。
- 官方限制是攻击机器、协议和 LAN 覆盖有限，良性活动不能覆盖复杂网络的全部变化（PDF 第 13 页）。

## GeNIS 官方字段字典

- 论文第 4 页明确说明 `0-info/genis-features.csv` 是完整字段字典，但正文未逐项打印。
- 从 Zenodo DOI `10.5281/zenodo.14919237` 下载的 `0-info.zip` 官方 MD5 为 `432ada3813f0261ac8b5e371ea4d729e`；本次临时副本 SHA-256 为 `7ef636cc758586f18a5d9958e68eede9b85925610331283cce802f45542701bc`。
- 字典共有 125 个字段，其中 122 个记录、流量或协议字段，3 个标签字段。
- 显式单位只有：`Load/SrcLoad/DstLoad` 为比特每秒，`Rate/SrcRate/DstRate` 为包每秒，源/目的到达间隔与抖动字段为毫秒，包/字节计数和比例按名称及字典说明确定。其余持续时间、TCP 时延、窗口、头部和包长字段的单位未在该字典中完整声明，不应补猜。
- 标签体系为 `BinaryLabel`、`CategoryLabel`、`SubCategoryLabel`；大类为 benign、bruteforce、dos、recon，共 13 个子类。

## HIKARI 指定论文身份

- 指定 PDF 是 2022 年 Rui Fernandes 与 Nuno Lopes 的二次分类评估论文，不是 Ferriyan 等 2021 年 HIKARI-2021 原始数据论文。
- 题名：`Network Intrusion Detection Packet Classification with the HIKARI-2021 Dataset: a study on ML Algorithms`。
- 会议：第 10 届数字取证与安全国际研讨会（ISDFS 2022）。
- DOI：`10.1109/ISDFS55398.2022.9800807`。
- 论文使用 555,278 条记录，称有 83 个特征；采用卡方检验选取 22 个特征，但没有公布 22 个字段名（PDF 第 2 至 3 页）。
- 数据先打乱，再按 80%/20% 随机拆分训练与测试；没有时间、会话、端点或捕获场景分组（PDF 第 3 页）。
- 基线为 KNN、MLP、SVM、随机森林；KNN 与随机森林在 22 特征下仍高分，MLP 与 SVM 明显下降（PDF 第 3 至 4 页、表 I 至 III）。
- 平衡实验每类只取 1,500 或 750 条，作者承认仅使用全部数据约 1.2%（PDF 第 4 页）。

## HIKARI 原始数据与真实表头补核

- Ferriyan 等原始数据论文为 `Generating Network Intrusion Detection Dataset Based on Real and Encrypted Synthetic Attack Traffic`，`Applied Sciences` 2021，DOI `10.3390/app11177868`。
- 原始论文图 2、4.1 节：攻击网有两台 CentOS 7/8，受害网有三台 Debian 8/9，运行 Joomla、Drupal、WordPress。
- 原始论文 4.2 至 4.5 节：背景流量来自未设过滤器或防火墙的受害网；Selenium 生成 HTTPS 良性行为；攻击为浏览器暴力破解、XML-RPC 暴力破解和漏洞探测；2021-03-28 至 2021-05-04 非连续采集，每次 3 至 5 小时。
- 原始论文表 2 给出六类与计数；表 3 列出 86 个正式字段，其中包含 84 个输入或元数据字段和两个标签。
- 服务器当前 CSV 实测为 88 列，比官方表 3 多一个空列和一个 `Unnamed: 0` 索引列；这两列不是网络特征。
- 当前 CSV 无绝对时间戳；555,278 个 `uid` 全部唯一，`Unnamed: 0` 不唯一且不单调，不能构造有时间语义的四窗口历史。
- 当前 CSV 六类计数为 Background 170,151、Benign 347,431、Bruteforce 5,884、Bruteforce-XML 5,145、Probing 23,388、XMRIGCC CryptoMiner 3,279；二元标签为 0 共 517,582、1 共 37,696。
- HIKARI 论文未逐项说明单位；项目真实数据审计只确认 `flow_iat.avg` 按微秒解释并除以 1000 转为毫秒。其他时间、头部、窗口和 bulk rate 字段不应仅凭名称断言单位。

## 对任务十七的综合裁决

- 当前候选五字段是 `total_packets`、`total_bytes`、`packet_length_mean`、`packet_rate`、`byte_rate`。
- 它们只是可派生的同名工程接口，不是严格物理语义交集：GeNIS 是双向事务总字节，HIKARI 是负载字节，ns-3 是瓶颈队列 L3 字节；公开数据按流，ns-3 按 0.1 秒队列窗口。
- 当前严格同名字段交集为空；包数虽量纲相同，统计对象仍不同。正式任务十七必须先统一聚合对象和协议层口径。
- GeNIS 原始数据能按 `FlowID`、`StartTime`、`LastTime` 形成受限历史；HIKARI 汇总 CSV 不能形成真实历史。
- 五字段接口舍弃了方向性、波动与突发、到达间隔、TCP 标志与握手、丢失与重传、活动/空闲状态、协议和连接上下文；这些信息正是区分慢速攻击、扫描、暴力破解和队列状态的重要候选观测。
- 论文证据支持先做输入充分性与域口径诊断，不支持直接把五字段状态估计结果写成公开数据上的真实队列恢复。
