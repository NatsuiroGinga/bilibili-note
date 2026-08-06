---
title: "ETGuard: Malicious Encrypted Traffic Detection in Blockchain-Based Power Grid Systems"
authors: [Peng Zhou, Yongdong Liu, Lixun Ma, Weiye Zhang, Haohan Tan, Zhenguang Liu, Butian Huang]
year: 2025
date: 2026-08-06
journal: "Blockchain and Web3.0 Technology Innovation and Application"
source_pdf: "[[raw/papers/attack-detection/encrypted/2024-Zhou-ETGuard.pdf]]"
tags:
  - 加密恶意流量检测
  - 增量学习
  - 电力系统
  - 类型/论文
key_finding: "ETGuard 把动态新增攻击作为核心问题，通过记忆回放和增量损失缓解遗忘；静态检测在三套数据上达到 0.86-0.94 F1。"
method: "GRU 自编码器提取前 50 个包的表征，记忆缓冲与增量损失保持旧攻击模式，MLP 分类。"
baseline: "RAPIER、FS、CoinFlip、PacketLen；ER、DER、DER++、GSS、SI；ETGuard-V 消融与 FULL 上界。"
zotero_key: "S86LBXDM"
aliases:
  - Zhou2025-ETGuard
  - ETGuard
---

# ETGuard: Malicious Encrypted Traffic Detection in Blockchain-Based Power Grid Systems

## 一句话

ETGuard 不把协议变化设为主问题，而把连续出现的新攻击与灾难性遗忘设为主线，形成静态检测、逐轮增量、消融和全量训练上界的证据链。

## 问题与方法

- 针对区块链电力系统中攻击类型持续增加，使用 GRU 自编码器提取包序列表征。
- 通过记忆样本、旧表征保持和按新旧损失动态调节的平滑项进行增量学习。
- 最终使用 MLP 以降低实时资源消耗。

## 数据与划分

- DoHBrw：688,489 条正常、6,112 条恶意；CIC-AndMal2017：894,367 条正常、62,972 条恶意；GridET：43,611 条正常、27,141 条恶意。
- 静态实验分别在三套数据上训练和测试，但正文未披露具体比例及按主机、捕获或时间分组方式。
- 增量实验把 DoHBrw 良性与 CIC 恶意组合成 A0-A5；A0 预训练，其余五组逐轮更新；第 i 轮测试集覆盖 0 到 i 轮已经出现的所有攻击类型。
- 证据：预印本 PDF 第 6-8 页，第 4.1-4.3 节与表 1。

## 主要结果

- ETGuard 在 DoHBrw、CIC、GridET 上的 F1 分别为 0.92、0.86、0.94；相应最强对比 RAPIER 为 0.88、0.84、0.83。
- 增量实验比较五种方法，另设去掉增量模块的 ETGuard-V 和使用全部攻击样本训练的 FULL 上界。
- 论文图 3-4 显示 ETGuard 的平均准确率与逐轮准确率通常优于 ETGuard-V，且轮次增加时差距扩大；正文未给出图中所有精确数值。
- 证据：预印本 PDF 第 7 页表 3；第 8-9 页图 3-4。

## 限制

- 静态数据划分披露不足，无法审计泄漏风险。
- DoHBrw/CIC 增量数据由不同来源拼接，新增攻击类型与数据源/采集环境可能混杂。
- GridET 是作者自建场景数据，公开性与复现细节需要另行核验。
- 本地原件是 2024 年 arXiv 预印本；正式书章出版于 2025 年，笔记采用正式出版年。

## 与本课题的边界

- **论文原结论**：ETGuard 在三套数据的静态检测和其构造的逐轮增量设置中优于所列基线。
- **可迁移机制**：预训练轮、逐轮新增类、累积测试集、去模块消融与全量训练上界。
- **不可直接声称**：增量攻击学习不能直接等同于跨加密协议泛化。
- **仍需验证**：在同一采集环境内控制数据来源后，增量模块的贡献是否保持。

## 文献信息

- DOI：[10.1007/978-981-97-9412-6_40](https://doi.org/10.1007/978-981-97-9412-6_40)
- arXiv 原件：[2408.10657](https://arxiv.org/abs/2408.10657)
- Zotero 条目键：`S86LBXDM`
