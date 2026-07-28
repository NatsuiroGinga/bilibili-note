---
title: "Domain Separation Networks"
authors:
  - Konstantinos Bousmalis
  - George Trigeorgis
  - Nathan Silberman
  - Dilip Krishnan
  - Dumitru Erhan
year: 2016
date: 2026-07-22
journal: "Advances in Neural Information Processing Systems 29"
source_pdf: "[[raw/papers/manifold/DomainSeparationNetworks-NeurIPS2016.pdf]]"
tags:
  - 类型/论文
  - 主题/共享私有分解
  - 主题/域适应
  - 主题/正交表示
key_finding: "DSN 用共享编码器承担分类，用共享与私有编码共同承担重构，并以软正交损失分离两者；私有表示不进入分类头，因此该结构不能单独保证物理私有分支影响检测或生成输出。"
method: "共享/私有编码器、重构、域相似性损失、软子空间正交约束"
baseline: "DANN、MMD、无差异损失和无重构损失等消融"
aliases:
  - DSN
  - Bousmalis2016-DSN
---

# Domain Separation Networks

> Konstantinos Bousmalis 等, 2016, NeurIPS · PDF 9 页

## 一句话

DSN 说明共享/私有分解需要同时约束“共享表示跨域一致”和“私有表示与共享表示分离”，但其任务分类器只读取共享表示，不能作为物理状态显式进入主任务的证据。

## 研究问题与方法

无监督域适应希望从有标签源域迁移到无标签目标域。论文为两个域设置共享编码器 $E_c$，并分别设置私有编码器 $E_p^s,E_p^t$。共享表示用于分类，共享与私有表示相加后用于重构。图 1 和正文明确给出：

$$
\hat x=D(E_c(x)+E_p(x)),
\qquad
\hat y=G(E_c(x)).
$$

该结构位于 PDF 第 3 页。

## 前向结构与关键公式

总损失为：

$$
\mathcal L=\mathcal L_{\mathrm{task}}
+\alpha\mathcal L_{\mathrm{recon}}
+\beta\mathcal L_{\mathrm{difference}}
+\gamma\mathcal L_{\mathrm{similarity}}.
$$

共享与私有表示的差异损失采用软正交约束：

$$
\mathcal L_{\mathrm{difference}}
=\left\|H_c^\top H_p\right\|_F^2.
$$

域相似性可由对抗域分类器或最大均值差异实现。总目标和差异损失分别见 PDF 第 3 至 4 页。

## 严格前向依赖判定

- 对分类输出，$\hat y=G(E_c(x))$，所以对私有表示 $q=E_p(x)$ 有 $\partial\hat y/\partial q=0$。
- 私有表示只通过重构损失间接影响共享编码器的训练，推理分类路径不消费私有表示。
- 这是一条直接反证：若第三章把物理状态当作“私有分支”但只用于辅助重构或正交损失，就不能宣称生成输出依赖该物理状态。

## 实验与消融证据

- 论文主要验证 MNIST、MNIST-M、SVHN、合成数字等域迁移。表 1 中 DSN-DANN 在多个方向优于 DANN，例如 MNIST 到 MNIST-M 的准确率为 83.2%，DANN 为 77.4%（PDF 第 6 页）。
- 表 3 的损失消融中，完整模型四个任务结果为 83.23/91.22/82.78/93.01；移除差异损失后为 80.26/89.21/80.54/91.89（PDF 第 8 页）。该结果支持软正交分解的增量，但只覆盖图像域适应。
- 并非所有组合、方向和相似性损失都同幅度改善，论文结果不支持“正交必然消除负迁移”。

## 成本与推理路径

训练时每个域增加一个私有编码器，并使用共享解码器和域相似性损失。任务推理只保留共享编码器与分类器，不需要目标域标签或私有表示。论文未报告统一训练时间、显存或浮点运算量。

## 局限与反证

论文主要假设两个域标签空间相同，且域差异更多体现在低层外观；作者还使用少量目标域有标签验证集选择超参数（PDF 第 5 至 6 页）。这比“完全无标签真实域迁移”更弱。网络流量中的场景差异可能同时改变高层攻击语义，不能直接套用该假设。

## 与本课题的关系

- **A 类，物理状态显式融合：反例相关。** 私有分支不进入任务头，严格依赖不成立。
- **B 类，共享/私有表征与负迁移：高相关。** 给出差异损失、共享重构与域相似性组合。
- **C 类，仿真到真实与状态可辨识：中等相关。** 是无监督域适应模板，但不是物理参数辨识。

第三章若采用共享/私有分解，应保留 DSN 的正交或去相关思想，但必须修改任务头为 $\hat y=G(h_c,\hat q)$ 或显式门控结构，避免物理分支只承担辅助重构。

## 原始摘要

> 摘要要点经原 PDF 第 1 页核验：论文将跨域共享因素与域私有因素分离，并以重构、相似性和差异损失改进无监督域适应。此处仅保留中文转述。

## 文献信息

- arXiv：[1608.06019](https://arxiv.org/abs/1608.06019)
- 会议论文集：[NeurIPS Proceedings](https://proceedings.neurips.cc/paper/2016/hash/45f31d16b1058d586fc3be7207b58053-Abstract.html)
- DOI：会议原始页面未给出 DOI，不补造标识符。
