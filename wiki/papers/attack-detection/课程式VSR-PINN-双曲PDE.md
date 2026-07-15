---
title: "Curriculum-Learned Vanishing Stacked Residual PINNs for Hyperbolic PDE State Reconstruction"
authors:
  - Katayoun Eshkofti
  - Matthieu Barreau
year: 2026
date: 2026-07-15
journal: arXiv preprint (KTH Royal Institute of Technology)
source_pdf: "[[2602.06996.pdf]]"
tags:
  - PINN
  - 课程式学习
  - 双曲PDE
  - 自适应采样
  - 物理信息
  - 类型/论文
aliases:
  - VSR-PINN
  - 课程式VSR-PINN
key_finding: 把三种课程方法（原始-对偶优化、因果推进、自适应采样）集成进 vanishing stacked residual PINN（VSR-PINN），用于双曲 PDE 状态重建；强制因果使点均方误差中位数及跨 run 方差系统性下降，比非因果训练提升近一个数量级。
method: VSR-PINN（递减粘性+堆叠残差，从抛物区平滑过渡到双曲区）+ 三种课程：原始-对偶平衡物理/数据损失、因果推进（尊重时间与梯度演化解锁更深堆栈）、自适应采样（瞄准高残差区）
baseline: 非因果 VSR-PINN、基线变体
---

# Curriculum-Learned VSR-PINN for Hyperbolic PDE State Reconstruction

> Eshkofti, Barreau · KTH · arXiv:2602.06996 · 2026-01 · 7 页

> 注：本论文是改进素材参考文献 [7]。原素材把 arXiv 编号写成 2601.13742 是错的（该编号实为语音评测论文），正确编号为 **2602.06996**。

## 一句话

双曲 PDE 有激波/间断，普通 PINN 难收敛——用"递减粘性+堆叠残差"先把问题软化好解，再叠加三种课程（损失平衡、因果、自适应采样）逐步逼近硬解。

## 对开题的意义（创新点 2 技术参考）

1. **"递减粘性"= 一种难度调控**：先解软化的易问题，再逐步加硬——与课程学习"由易到难"同构。开题的"困惑区→熟练区"三级分区可类比。
2. **三种课程可组合**：损失加权课程 + 因果课程 + 自适应采样课程——证明多课程机制可叠加。开题的"物理残差 + 决策方差"双维度课程是其叠加思想在检测场景的延伸。
3. **自适应采样瞄准高残差区**：与开题"提高困惑区采样权重"直接对应。

## 局限（gap）

- 双曲 PDE 状态重建（物理交通流重建），非网络攻击检测。
- 课程集成在 PDE 求解框架内，无 RL/GRPO。
- "traffic reconstruction" 指物理交通流，勿与网络流量混淆。

## 疑问 / 待验证

- "递减粘性"软化思路在网络攻击检测中是否有对应物？（如先学显性攻击、再学隐蔽攻击的"软化"机制）
- 三课程叠加的协同/冲突，对开题双维度课程的设计有何教训？
