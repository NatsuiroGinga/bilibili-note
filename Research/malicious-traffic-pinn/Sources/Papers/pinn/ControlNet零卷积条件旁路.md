---
title: "Adding Conditional Control to Text-to-Image Diffusion Models"
authors:
  - Lvmin Zhang
  - Anyi Rao
  - Maneesh Agrawala
year: 2023
date: 2026-07-23
journal: "IEEE/CVF International Conference on Computer Vision"
source_pdf: "[[raw/papers/pinn/2023-Zhang-ControlNet.pdf]]"
tags:
  - 类型/论文
  - 主题/条件生成
  - 主题/恒等初始化
  - 主题/旁路网络
key_finding: "ControlNet 冻结原生成网络，并以零初始化连接层接入条件分支；其公式直接证明第一步前向与原网络相等，但完整复制编码器的成本不适合直接迁移到 Qwen。"
method: "冻结主干、条件侧分支、零卷积、残差注入"
baseline: "普通微调、轻量条件分支、无条件扩散模型"
aliases:
  - ControlNet
  - Zhang2023-ControlNet
---

# ControlNet 零卷积条件旁路

## 一句话

ControlNet 为“新增条件结构在初始化时严格等价于原模型”提供了最清楚的代数证明，但其复制主干的做法只能作为结构原理，不能直接照搬。

## 方法核心

PDF 第 4 页公式（2）写为：

$$
y_c=F(x;\Theta)+Z\!\left(F(x+Z(c;\Theta_{z1});\Theta_c);\Theta_{z2}\right),
$$

其中原网络参数 $\Theta$ 冻结，$Z$ 的权重和偏置均初始化为零。第一步两个 $Z$ 都输出零，因此公式（3）得到 $y_c=y$。

## 全文证据

- PDF 第 2 至 4 页给出冻结分支、可训练副本和两个零连接层的完整结构。
- PDF 第 4 页明确证明第一步输出等于原模型，并解释零连接层阻止随机条件噪声直接污染冻结特征。
- 论文报告从少于五万到超过一百万样本的条件训练，并在部分任务使用单张 RTX 3090 Ti；这些规模和成本不能直接外推到文本大模型。

## 对本课题的可迁移机制

保留“冻结检测主干 + 零初始化条件残差 + 恒等旁路”，删除“复制完整主干”。物理条件分支只使用低秩投影和小型交叉注意力，并加入显式范数上界。

## 不可直接声称

- 零连接只保证初始化等价，训练后条件分支仍可能损害原任务。
- 图像空间条件具有直接监督，本课题公开流量缺少真实队列状态，物理条件可靠性更弱。
- 复制完整 Qwen 主干不满足参数高效和 RTX 5090 成本约束。

## 文献信息

- CVF 官方论文页：[ICCV 2023](https://openaccess.thecvf.com/content/ICCV2023/html/Zhang_Adding_Conditional_Control_to_Text-to-Image_Diffusion_Models_ICCV_2023_paper.html)
- arXiv：[2302.05543](https://arxiv.org/abs/2302.05543)
