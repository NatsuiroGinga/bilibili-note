---
title: "ConFIG: Towards Conflict-Free Training of Physics Informed Neural Networks"
authors:
  - Qiang Liu
  - Mengyu Chu
  - Nils Thuerey
year: 2025
date: 2026-07-21
journal: "International Conference on Learning Representations 2025"
source_pdf: "[[raw/papers/pinn/2408.11104-ConFIG.pdf]]"
tags:
  - PINN
  - 梯度冲突
  - 多目标学习
  - 类型/论文
aliases:
  - ConFIG
  - Liu2025-ConFIG
key_finding: "ConFIG 为多个损失构造与每个损失梯度均为正投影的共同更新，并平衡各目标的下降速率；三目标情形比简单两目标投影更符合当前生成、状态、物理训练。"
method: "多损失梯度伪逆合成与交替动量加速"
baseline: "Adam、PCGrad、IMTL-G、LRA、MinMax、ReLoBRaLo 和多任务优化方法"
---

# ConFIG：PINN 多目标无冲突训练

## 核心结论

- 最终更新与每个损失梯度保持正投影，并使各目标获得一致的投影下降速率。
- 两损失时与部分投影方法方向相近；三个以上损失时，ConFIG 才体现同时保护全部目标的区别。
- 论文在四类 PINN 基准和 CelebA 多任务实验中取得稳定改善，并报告完整与动量加速版本。

## 适用边界

- PINN 证据来自小型坐标网络；CelebA 只能说明一般多任务可用性。
- 完整版本需分别反向传播各损失；动量版的梯度会随任务数增加而陈旧。
- 不存在共同下降方向时，更新可能趋近于零；消除一阶冲突也不保证全局最优。

## 与任务九的关系

M2P 只处理生成梯度与物理梯度，未保证最终共享更新降低状态损失，最终状态误差大幅恶化。ConFIG 的三目标共同下降正好针对这一缺口，但只有物理项在稀疏监督下先证明有新增信息后才值得实现。

## 可证伪实验

在固定稀疏状态掩码下，记录最终共享更新与生成、状态、物理三个梯度的点积。若点积满足非负但生成或未标注状态仍劣于匹配 M1，或者大量步更新近零，则删除该机制。

## 文献信息

- [ICLR 会议原文](https://proceedings.iclr.cc/paper_files/paper/2025/file/94e85561a342de88b559b72c9b29f638-Paper-Conference.pdf)
