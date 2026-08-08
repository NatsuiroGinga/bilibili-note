# QUIC 完整动力学数据集证据笔记

## 研究问题

公开 QUIC 数据集中，哪些能够支持完整 QUIC 动力学残差，并同时或间接服务恶意流量检测 R2？

## 证据门槛

“完整动力学”至少要求包号空间、确认关系、端点丢包判定、往返时延和在途字节均有可靠来源。拥塞窗口、控制器、路径迁移和探测超时属于增强真值。只有抓包、密钥、聚合流字段或旋转位时，不把端点内部状态当作真值。qlog 规范允许省略大量字段，因此“存在 qlog”不是通过条件，必须逐迹线审计。

## 候选证据

### 条件 A：QUIC-MedNetCom

- 原始论文：`raw/papers/datasets/quic/Experimental-Assessment-QUIC-Congestion-Control-Cellular-2021.pdf`。
- 官方仓库：`https://github.com/Mohmoulay/QUIC-MedNetCom`，核验提交 `f237a20360b83868a197488c5b557f53e4b7e53c`。
- 规模：89 个 qlog，合计 630,227,334 字节；整个受跟踪树 695,847,552 字节。
- 实测字段：样本含包号、ACK、往返时延、在途字节和拥塞窗口；至少一条样本含端点 `packet_lost` 事件及丢包触发原因。
- 局限：2020 年前后 draft-27；无恶意标签；仓库根目录没有清晰的数据许可；不同实现和迹线字段不齐。
- 裁决：技术上最强的动力学教师，逐迹线通过字段门禁后为 A。

### 条件 A：QUIC Interop Runner

- 原始论文：`raw/papers/datasets/quic/Automating-QUIC-Interoperability-Testing-Seemann-Iyengar-2020.pdf`。
- 官方仓库与滚动归档：`https://github.com/quic-interop/quic-interop-runner`、`https://interop.seemann.io/quic`。
- 归档同时可能提供双端日志、模拟器 PCAP、TLS 密钥和 qlog，但是否存在取决于实现。
- 实测现代归档样本：普通场景 qlog 中有包号、ACK 范围、往返时延、在途字节和拥塞窗口；`transferloss` 服务端样本含 68 个 `packet_lost` 事件、2436 次在途字节更新、132 次拥塞窗口更新。
- 局限：无恶意标签；网页为滚动归档，当前保留范围和总容量会变化；没有固定 DOI、冻结 manifest 或明确归档数据许可。
- 裁决：适合冻结少量现代 QUIC 运行作为条件补充，不应把滚动网页直接称为可复现数据集。

### 条件 A：EPIQ 2020

- 原始论文：`raw/papers/datasets/quic/Same-Standards-Different-Decisions-QUIC-Implementation-Diversity-2020.pdf`。
- 官方数据：`https://qlog.edm.uhasselt.be/epiq/files/dataset.zip`。
- 实测容量：19,057,641 字节压缩，331,166,430 字节解压，64 项；完整性测试通过。
- quic-go 样本含包号、ACK、丢包、丢包定时器、往返时延、在途字节、拥塞窗口和包号空间。
- 局限：2020 年 draft-25 至 draft-27；部分实现样本缺拥塞窗口；无恶意标签；数据页没有单列数据许可。
- 裁决：只作实现多样性和旧 qlog 模式转换验证，不作为主教师。

### B+：H23Q

- 原始论文：`raw/papers/datasets/quic/H23Q-HTTP3-Security-Public-Dataset-arXiv2208.06722.pdf`。
- 官方页面：`https://icsdweb.aegean.gr/awid/h23q`。
- 官方标称 30 GB，60 个 PCAP，即 10 类攻击乘 6 个服务端，并提供 CSV；全文确认配套 TLS 密钥随数据提供。
- PCAP 与密钥可恢复可见 QUIC 包型、包号和 ACK，并近似构造线上往返时延与在途字节。
- 没有端点 qlog，不能保证端点丢包宣告、探测超时、拥塞窗口或控制器状态。
- 下载需机构邮箱、用途说明和人工审批，数据许可未在下载页明确给出。
- 裁决：唯一强攻击桥接候选，但只是 B+；已降为条件备选，审批不得阻塞 R2 当前路线。

### B/B+：其他公开来源

- VisQUIC：100,664 条 QUIC PCAP，部分带密钥和网络日志；无恶意标签、无端点拥塞真值，B+。
- QUIC 旋转位数据集：17.7 GB 压缩，提供端点 qlog RTT 与收发包时间、旋转位、包号；缺 ACK、丢包、在途字节和拥塞窗口，B。
- CESNET-QUIC22：21 GB 压缩、153M 流、102 个服务标签；只有流统计及前 30 个包的长度、方向和到达间隔，B。
- CESNET-QUICEXT-25：28.2 GB 压缩、2024-06 至 2025-05、1:100 采样；有握手与包序列元数据，无端点状态，B。
- QUIC 隐蔽信道集：16 个 CSV、实际文件合计 878.3 MB；标签为正常、ASCII 隐蔽信道和 AES 隐蔽信道，依赖 Retry Token 特征，无完整动力学，B-。
- QUIC 网站指纹集：831 MB 处理集和 28 GB 原始集；QUIC 迹线实际是 WireGuard 隧道中的 QUIC/TCP 混合 PCAP，并带开发者工具日志，不含端点动力学，B。

### C：不可直接使用

- QUICsand：官方明确因隐私不公开原始数据，Zenodo 只有 1.5 MB 软件制品。
- RISE Demonstration Experiment 2：记录标称开放，但下载返回登录页；元数据只说明好吞吐，未证明含 qlog。
- MonroeQL：论文说明原始实验存为 qlog，并从中聚合出 188 个 RTT、拥塞窗口、时长和吞吐特征；作者官方仓只公开代码、合成数据和决策树，不公开 MonroeQL 原始 qlog 或 CSV，聚合表也缺包号、ACK 与逐包丢包。

## 观测边界

- 当前 qlog 事件规范包含包发送/接收、确认、丢包、往返时延、在途字节、拥塞窗口和定时器等事件，但许多字段是可选项。
- 解密 PCAP 可以重建线上包与帧，不能重建端点内部为何、何时判丢，也不能可靠得到发送端拥塞窗口。
- 完整物理教师应使用端点 qlog；带标签 PCAP 只能提供安全桥接和线上可观测残差。

## 推荐合同

1. 主教师使用 QUIC-MedNetCom 中通过字段门禁的轨迹。
2. 从 QUIC Interop Runner 冻结少量现代 QUIC、丢包和跨流场景，记录运行时间、实现、文件哈希和下载 URL。
3. EPIQ 只用于实现多样性与旧模式兼容诊断。
4. 当前恶意检测继续使用已冻结安全数据；H23Q 获批后再作为外部攻击桥接，不是启动前置条件。
5. 端点私有状态只在训练期作为状态监督或教师信号；推理输入不得偷偷加入 qlog、标签、测试床标识或不可部署字段。

## 容量口径

- 最小动力学教师：MedNetCom 20—50 条字段完整轨迹约 0.15—0.35 GiB，建议预留 0.5 GiB。
- 现代补充：Interop 20—40 条轨迹建议预留 0.3—1 GiB，实际取决于 PCAP。
- H23Q 条件桥接：完整集官方标称 30 GB，因无公开 manifest，完整保存建议预留 35—45 GB；只取 4—12/60 组时粗估 2—6 GB，须获批后校准。
- EPIQ 完整备份：约 18.18 MiB 压缩、315.82 MiB 解压。

## Zotero 状态

- 2026-08-03 核验 Zotero 9.0.6，本地 API 与 Connector 均返回 200。
- 指定集合 `Research-QUIC-Dynamics-Datasets-2026` 不存在，当前选择目标为“我的文库”。
- 本地辅助工具只能导入当前选择的文库或集合，不能创建集合。为避免误导入根库，本轮没有执行导入；需人工创建并选中集合后再导入书目。

## 访问与许可阻塞

- H23Q 需审批，但已降为条件备选，不阻塞当前实验。
- Interop 是滚动归档，需自行冻结 manifest。
- MedNetCom、EPIQ 和 Interop 的数据许可需在公开发布前向作者确认。
