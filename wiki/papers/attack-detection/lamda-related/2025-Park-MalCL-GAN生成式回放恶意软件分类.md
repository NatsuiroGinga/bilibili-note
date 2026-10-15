---
title: "MalCL: Leveraging GAN-Based Generative Replay to Combat Catastrophic Forgetting in Malware Classification（MalCL：GAN 生成式回放对抗恶意软件分类灾难性遗忘）"
authors: "Jimin Park, AHyun Ji, Minji Park, Mohammad Saidur Rahman, Se Eun Oh"
year: 2025
date: 2025-01-02
journal: "AAAI 2025（第 39 届 AAAI；arXiv:2501.01110v1）"
source_pdf: "raw/papers/attack-detection/lamda-related/2025-Park-MalCL-GAN生成式回放恶意软件分类.pdf"
tags:
  - 恶意软件
  - 持续学习
  - 生成式回放
  - GAN
  - 类型/论文
key_finding: "用带特征匹配损失的 GAN 生成历史恶意样本、以隐藏表示做回放样本选择，在 Windows(EMBER)/Android(AZ-Class) 恶意家族类增量分类上，Windows 平均准确率 55%、较 GR/BI-R 等生成式回放基线高 28%，但整体仍远低于 Joint 上界（88.7）。"
---

# MalCL: GAN-Based Generative Replay for Malware Classification

## 证据等级
**在线全文已下载并 MinerU 精读**（arXiv 2501.01110v1 = AAAI 2025）。**公开代码**：`https://github.com/MalwareReplayGAN/MalCL`；数据（EMBER 子集 / AZ-Class）在 Zenodo。

## 方法与设定（原文章节）
- 任务：**恶意软件家族类增量分类（Class-IL）**，每个任务引入新家族；EMBER（Windows，100 家族，337,035 样本）、AZ-Class（Android，100 家族，285,582 样本，Drebin 特征）。
- 架构：生成器=4 层 1D CNN + 2 FC + 3 反卷积；判别器=2 卷积 + 2 FC（用第二卷积层展平 logits 做特征匹配）；分类器=**3 层 1D CNN + FC**，SGD(lr=1e-3, mom=0.9, wd=1e-7)，批 256（§架构节）。
- 回放样本选择：按分类器隐藏表示（到 one-hot 标签 / 类别均值 / logits 的 L1/L2 距离）挑选合成样本（§selection）。
- 结果（表 1，EMBER）：None 27.5、Joint 88.7、GR 26.8、BI-R 27.0；MalCL 最好配置 54.5（Mean）。

## 三问
1. **能否在固定 200 条预算下运行？** **不能（原样）**。这是**生成式回放**：需保存并持续训练一个 GAN（额外生成模型 + 判别器），且分类器为 CNN；不以"固定 200 条原始样本"为约束。其存储/计算开销是与本文约束正交的一轴。
2. **能否挂 MLP？** **不能直接**。原文分类器与生成器均为 1D CNN 架构，绑定序列/卷积假设；本文为 4,561 维无序二值表格特征，无自然序列结构。
3. **有无公开代码？** **有**：`https://github.com/MalwareReplayGAN/MalCL`。

## 与本文第三章的关系
- **问题域最接近的当代恶意软件 CL 工作之一**（Android 家族、Drebin 特征），可作"恶意软件域持续学习"当代对照的引用，说明"生成式回放"是与本文"样本选择回放"并列的另一条路线。
- **不宜作可跑基线**：生成式回放需 GAN，与本文固定 200 条原始样本 + MLP 的合同不兼容；且它是 Class-IL 家族分类，非 Domain-IL 二分类。

## 不能直接声称
- 不能把其 EMBER/AZ-Class 家族分类数值与 LAMDA 二分类结果并列比较（任务、指标、标签空间均不同）。
- 其"优于 GR/BI-R 28%"的基线是生成式回放内部比较，不含强判别基线。
