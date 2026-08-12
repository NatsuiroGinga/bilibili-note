---
title: "ET-BERT: A Contextualized Datagram Representation with Pre-training Transformers for Encrypted Traffic Classification"
authors:
  - Xinjie Lin
  - Gang Xiong
  - Gaopeng Gou
  - Zhen Li
  - Junzheng Shi
  - Jing Yu
year: 2022
date: 2026-08-08
journal: "WWW 2022；arXiv:2202.06335v2"
source_pdf: "[[raw/papers/traffic-foundation-models/2202.06335_ET-BERT_加密流量预训练.pdf]]"
tags:
  - 流量基础模型
  - ET-BERT
  - BURST
  - BPE分词
  - 加密载荷
  - 类型/论文
key_finding: "ET-BERT 把 BURST（同向连续包）的十六进制串按 bigram + BPE 编成词表 65,536、序列长 512 的 BERT-base 输入，只用载荷（显式删掉以太网头、IP 头和 TCP 端口），用 MBM + SBP 两个自监督任务预训练 30GB 流量；其对'加密载荷仍含信息'的论证只是 15 项 NIST 随机性检验的 p 值不为 1，属弱论证。"
---

# ET-BERT

> Lin 等, 2022, WWW 2022 · 11 页

## 一句话

流量预训练模型的事实起点与最常被引的基线；它的输入形态（纯载荷 bigram token）与本课题的字段/统计特征基本不兼容，其历史价值在于确立了 BURST 结构和"包级 vs 流级微调"的评测口径。

## 论文证据

- 第 3 页 §3.1：网络主体为 12 层 bi-directional Transformer、每层 12 头、隐藏维 `H=768`、**输入 token 数 512**（BERT-base 同构）。
- 第 3 页 §3.2.1：BURST 定义为单条会话流中"来自请求方或响应方的时间相邻包集合"，即同向连续包；作者用 DOM 树渲染产生语义片段来论证 BURST 的合理性（第 3 页），这是一个网页场景的类比论证而非流量层面的实证。
- 第 3 页 §3.2.2：**bigram 编码**——把十六进制序列中每两个相邻字节连成一个 4 位十六进制单元，再用 BPE 建表，token 取值 0—65535，词表上限 65,536；另加 [CLS]/[SEP]/[PAD]/[MASK]。一个 BURST 被均分为两个 sub-BURST 供 SBP 任务用。
- 第 4 页 §3.3：两个预训练任务——MBM（掩码 BURST 模型，掩码率 **15%**，80/10/10 替换策略，负对数似然）与 SBP（同源 BURST 预测，50% 正例，二分类）；总损失 `L = L_MBM + L_SBP`。
- 第 5 页 §3.3 末：**预训练语料约 30GB**，其中约 15GB 来自公开集、约 15GB 为 CSTNET 被动采集；含 QUIC/TLS/FTP/HTTP/SSH 等协议。
- 第 5 页 §3.4：两种微调策略——packet 级（单包输入）与 flow 级（**流内 `M=5` 个连续包拼接**）。
- 第 5 页 §4.1.2（去偏做法）：移除 ARP/DHCP；"为避免包头在有限集合中引入带强标识信息的偏置（如 IP 和端口），我们**移除了以太网头、IP 头以及 TCP 头的协议端口**"。微调阶段每类最多随机取 500 条流、5,000 个包，8:1:1 划分。
- 第 6 页 §4.1.3：预训练 batch 32、总步数 500,000、lr 2e-5、warmup 0.1；微调 AdamW 10 epoch、flow 级 lr 6e-5、packet 级 2e-5、batch 32、dropout 0.5；V100S GPU。
- 第 6 页表 2/表 3：ET-BERT(packet) 在 ISCX-VPN-Service F1 0.9890、ISCX-VPN-App 0.9937、ISCX-Tor 0.9921、USTC-TFC 0.9916、CSTNET-TLS1.3 0.9741、CP-iOS 0.9754、CP-Android 0.9206；**ET-BERT(flow) 系统性更低**（ISCX-VPN-App 仅 0.7306、ISCX-Tor 0.5886）。摘要宣称的 "ISCX-VPN-Service 98.9% (5.2%↑)"用的是 packet 级。
- 第 7 页表 4（ISCX-VPN-App 上的消融，每类最多 100 样本）：完整 packet 模型 F1 0.9395；去 SBP 降 3.97%、去 MBM 降 9.33%、把 BURST 换成随机相邻包（w/o BURST）仅降 1.37%；flow 级 0.7387、concatenated-flow 0.6961；**去预训练直接掉到 0.5638（-37.57%）**。
- 第 7—8 页 §4.4.1 表 5（可解释性，本文对"加密载荷是否有信息"的唯一论证）：对 AES(GCM)/AES(CBC)/CHACHA20/ARC4/3DES 跑 15 项 NIST 随机性检验，p 值散布在 0.0096—0.9856；作者仅据此得出"这些密码确实未达到完美随机"。第 8 页 §4.4.2 进一步用"含 RC4、3DES 等弱随机性密码的数据集上 F1 接近 100%"作为佐证。
- 第 8 页 §4.5 与图 4：ISCX-VPN-Service 每类 500 样本，取 40%/20%/10% 时 ET-BERT(packet) F1 分别 95.78%/98.33%/91.55%（**注意 20% 高于 40%，非单调**）。
- 第 8 页 §5 讨论：自陈两条局限——泛化性（模式随互联网服务内容随时间变化而失效；TLS 1.3 的 ECH 机制未来会让 SNI 标注失效）与预训练安全性（可被投毒植入后门，但"如何构造加密流量的毒化 token 尚未被研究"）。

## 与本课题六个关注点的对照

- (a) 输入形态：**纯加密载荷十六进制 bigram**，显式剔除以太网头、IP 头、TCP 端口。与本课题三类数据（字段、统计、时序）几乎不重叠；其分词方案不可直接迁移。
- (b) 有效历史：packet 级为单包，flow 级为前 5 包拼接，序列上限 512 token（约 512 字节的 bigram 覆盖）。**无历史长度消融**。
- (c) 跨字段交互：由 BERT 全连接自注意力隐式承担，无显式字段结构；且因为删掉了 IP 头与端口，可用的字段信号本就很少。这与本课题"无历史 69.5%、字段交互是主信号"的结论方向相反——ET-BERT 押注的是载荷字节。
- (d) 预训练目标与规模：MBM + SBP，30GB 流量，500,000 步。
- (e) 评测缺陷：**第三方证据明确**——netFound 表 2 显示删掉 Crossmarket 的 TCP Options 时间戳后 ET-BERT 从 99.82 崩到 32.83、CIC-IDS Heartbleed 从 99.99 崩到 0.0；netFound 表 3 测其嵌入平均余弦 0.84（塌缩）。ET-BERT 本文的 packet 级评测把同一条流的不同包分到 train/test，是 Pcap-Encoder 所批评的 per-packet split。
- (f) 可得性：代码 github.com/linwhitehat/ET-BERT（摘要）；预训练权重公开可用（后续多篇论文以 PT 187.4M / FT 136.4M 参数直接加载）。

## 论文自陈局限与被回避的劣势数据

- 自陈局限见第 8 页 §5：时间漂移、ECH 使 SNI 标注失效、预训练投毒风险。
- 消融缺失：无输入长度/包数消融、无词表大小消融、无掩码率消融、无模型规模消融、无多种子。
- 被回避的劣势：flow 级结果远逊 packet 级（ISCX-VPN-App 0.7306 vs 0.9937、ISCX-Tor 0.5886 vs 0.9921），摘要与结论只引 packet 级数字；表 4 显示 BURST 结构本身只贡献 1.37%，即"BURST 是核心创新"的说法与消融不匹配；随机性检验只证明"不是完美随机"，未量化可提取的信息量，也未做"用真随机替换载荷后性能是否下降"的对照实验。
- 数字口径：摘要"ISCX-VPN-Service 98.9% (5.2%↑)"是相对 Deeppacket 93.21 的**绝对百分点**差；按错误相对下降为 (0.0679-0.0110)/0.0679 = **+83.8%**。CSTNET-TLS1.3 "10.0%↑"（87.41→97.41）对应错误相对下降 (0.1259-0.0259)/0.1259 = **+79.4%**。这些数字是在被后续工作证明含捷径的评测协议下取得的。

## 允许主张

- ET-BERT 确立了 BURST 结构、bigram+BPE 分词、MBM/SBP 双任务这套流量预训练范式，是所有后续工作的公共基线。
- 其消融明确显示预训练本身贡献最大（-37.57%），BURST 结构贡献很小（-1.37%）。
- "加密载荷不是完美随机"有 NIST 检验支持；但只到这一步。

## 禁止主张

- 不能把 ET-BERT 的 99% 级分数当作真实检测能力——第三方在去捷径数据集上实测其崩溃到 32.83 与 0.0。
- 不能声称"TLS 加密后载荷字节仍含充分可分类信息"已被本文证明；本文只证明密码实现未达完美随机，未做任何"载荷替换为真随机"的对照。
- 不能把 packet 级成绩与其他工作的 flow 级成绩直接比较。
- 不能把 BURST 说成经过验证的关键结构。

## 相关

- [[2025-Zhou-TrafficFormer-流量预训练与数据增强]]（直接批评 SBP 任务过于简单、并保留全部包头字段）
- [[2026-Beltiukov-netFound-协议感知流量基础模型]]（对 ET-BERT 捷径依赖的实测证据）
- [[2024-Wang-NetMamba-高效流量分类状态空间]]
