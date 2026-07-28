---
title: "LLaMA-Adapter: Efficient Fine-tuning of Large Language Models with Zero-initialized Attention"
authors:
  - Renrui Zhang
  - Jiaming Han
  - Chris Liu
  - Aojun Zhou
  - Pan Lu
  - Yu Qiao
  - Hongsheng Li
  - Peng Gao
year: 2024
date: 2026-07-23
journal: "International Conference on Learning Representations"
source_pdf: "[[raw/papers/pinn/2023-Zhang-LLaMA-Adapter.pdf]]"
tags:
  - 类型/论文
  - 主题/大语言模型
  - 主题/参数高效微调
  - 主题/零初始化注意力
key_finding: "LLaMA-Adapter 通过分离提示词元与原词元的注意力归一化，并用从零初始化的有界门控只缩放提示贡献，在冻结 LLaMA 上渐进注入条件信息；随机初始化消融显著退化。"
method: "冻结 LLaMA、适配提示、分离归一化、零初始化多头门控"
baseline: "随机初始化门控、全量微调、LoRA、提示微调"
aliases:
  - LLaMA-Adapter
  - Zhang2024-LLaMAAdapter
---

# LLaMA-Adapter 零初始化注意力

## 一句话

这篇论文比普通残差门控更进一步：新增条件和原有词元分别归一化，原词元注意力分布不乘门控，条件贡献才由零初始化门控控制。

## 方法核心

论文在高层 Transformer 中加入可学习适配提示。PDF 第 4 页公式（7）将提示和原词元的注意力分开归一化：

$$
S_l^g=
\left[
\operatorname{softmax}(S_l^K)\tanh(g_l);
\operatorname{softmax}(S_l^{M+1})
\right]^{\top}.
$$

$g_l$ 从零初始化，且 $\tanh$ 将其限制在 $[-1,1]$。原词元项不乘任何系数，因此初始阶段保留冻结模型原有注意力分布。论文对不同注意力头独立学习门控。

## 全文证据

- PDF 第 3 至 4 页给出适配提示、分离注意力和零初始化门控的完整计算图。
- PDF 第 8 页表 5 显示，随机初始化版本在 ScienceQA 验证集为 `40.77%`，零初始化版本相对提高 `43.08` 个百分点；图 7 同时显示随机初始化收敛明显更慢。
- PDF 第 8 页还指出插入层数存在取舍，过早干预底层编码可能损害效果。
- 论文在语言、视觉和多模态任务验证该门控，但实验基座与本课题不同。

## 对本课题的可迁移机制

物理条件词元和流量文本词元可以采用分离归一化。检测主分支维持原注意力，物理条件只通过零初始化的附加项进入上层生成表征。该计算图不同于已失败的静态私有 LoRA 和单向量门控投影。

## 不可直接声称

- 论文没有证明训练后原任务输出保持不变。
- ScienceQA 的消融幅度不能迁移为恶意流量检测增益。
- 适配提示是自由参数；本课题的物理词元必须由可微状态头和有限队列残差生成，并额外验证物理语义。

## 待验证假设

只在 Qwen3-1.7B 的固定高层插入物理条件注意力，可减少对通用流量编码的扰动；若未知攻击召回或校准仍失败，则说明零初始化和分离归一化不足以保护开放集边界。

## 文献信息

- arXiv：[2303.16199](https://arxiv.org/abs/2303.16199)
- 载体：ICLR 2024 会议论文
