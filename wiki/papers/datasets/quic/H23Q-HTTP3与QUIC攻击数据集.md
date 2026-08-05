---
title: "H23Q：HTTP/3 与 QUIC 攻击数据集"
authors: [Efstratios Chatzoglou, Vasileios Kouliaridis, Georgios Kambourakis, Georgios Karopoulos, Stefanos Gritzalis]
year: 2022
date: 2026-08-03
journal: "Computers & Security 123"
source_pdf: "[[raw/papers/datasets/quic/H23Q-HTTP3-Security-Public-Dataset-arXiv2208.06722.pdf]]"
tags:
  - QUIC
  - HTTP3
  - 网络攻击
  - PCAP
  - 数据集
  - 类型/论文
aliases:
  - H23Q
  - Chatzoglou2022-H23Q
key_finding: "H23Q 提供 10 类攻击、6 个 HTTP/3 服务端的 PCAP、CSV 和 TLS 密钥，是最强的 QUIC 攻击桥接候选；但没有端点 qlog，无法给出完整拥塞动力学真值。"
---

# H23Q：HTTP/3 与 QUIC 攻击数据集

## 一句话

H23Q 解决“攻击标签”问题，不解决“端点完整动力学”问题；当前应作为审批成功后追加的条件外部测试，而不是 R2 启动前置数据。

## 数据构成

官方页面与论文均称数据集约 30 GB，提供 PCAP 和 CSV。测试床包含 13 个客户端、攻击者和 6 种 HTTP/3 服务端，形成 10 类攻击乘 6 个服务端的 60 个 PCAP。攻击覆盖 HTTP/3 洪泛、模糊测试、慢速流、QUIC 洪泛、QUIC 慢速连接、加密 QUIC 攻击、请求走私及 HTTP/2 相关攻击。

全文明确说明客户端保存 TLS 密钥，数据集随附密钥。因此可以受控解密包号和 ACK 帧，并从线上事件近似计算 RTT、确认关系和在途字节。

## 为什么不是 A 级

PCAP 记录“线上发生了什么”，端点 qlog 还记录“端点何时、为何判定丢包，以及拥塞窗口如何变化”。H23Q 没有公开端点 qlog、拥塞窗口、探测超时或控制器内部状态，不能把被动近似当作端点真值。

## 对 R2 的作用

获批后可选取 QUIC/HTTP3 专属攻击和多个服务端，验证由 qlog 教师学得的状态表征能否迁移到真实攻击 PCAP。TLS 密钥只用于生成训练/审计真值；公平推理仍应只读取部署可见字段。

当前合同中，H23Q 已降为条件备选。审批失败不阻塞 MedNetCom 加 Interop 的动力学路线，也不阻塞在现有冻结安全数据上的分类实验。

## 访问、许可与容量

- 下载要求大学或机构邮箱、用途说明和人工审批。
- 官方下载页没有明确数据许可；论文正文为开放获取不等于数据可再分发。
- 官方未公开文件 manifest 和压缩率。完整保存建议预留 35—45 GB；4—12/60 组的 2—6 GB 只是按均匀体量做的预算估算，不能当成实测值。

## 文献信息

- DOI：<https://doi.org/10.1016/j.cose.2022.103051>
- arXiv：<https://arxiv.org/abs/2208.06722>
- 官方页面：<https://icsdweb.aegean.gr/awid/h23q>
