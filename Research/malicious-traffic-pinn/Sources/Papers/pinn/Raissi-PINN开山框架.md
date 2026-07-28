---
title: "Physics Informed Deep Learning (Part I & II): 数据驱动的 PDE 求解与发现"
authors:
  - Maziar Raissi
  - Paris Perdikaris
  - George Em Karniadakis
year: 2017
date: 2026-07-15
journal: arXiv 预印本（2017 Part I/II；正式版 JCP 2019, 378:686-707）
source_pdf: "[[1711.10561.pdf]]"
tags:
  - PINN
  - 偏微分方程
  - 自动微分
  - 物理信息
  - 奠基论文
  - 类型/论文
aliases:
  - Raissi-PINN开山
  - PINN开山论文
key_finding: 提出 PINN——神经网络在监督学习的同时，通过自动微分把 PDE 残差作为约束嵌入损失，自然编码物理定律为先验，形成数据高效的通用函数逼近器；Part I 解 PDE（data-driven solution），Part II 发现 PDE（data-driven discovery）。
method: NN 作解函数逼近器 → 自动微分算 PDE 残差 → 联合损失 = 数据拟合 + PDE 残差 + 边界/初值约束；分连续时间与离散时间两类模型
baseline: 传统数值方法、纯数据驱动 NN
---

# Raissi PINN 开山框架（Part I + Part II）

> Raissi, Perdikaris, Karniadakis · Brown Univ / UPenn · arXiv:1711.10561 (Part I) + 1711.10566 (Part II) · 2017

> 引用规范：学术引用统一以 **2019 JCP 版**（Journal of Computational Physics, 378:686-707, DOI 10.1016/j.jcp.2018.10.045）为准；本 vault 存的是 2017 两篇 arXiv 预印本（Part I=解 PDE，Part II=发现 PDE），内容即 JCP 版来源。Part II 见 [[1711.10566.pdf]]。

## 一句话

让神经网络学数据的同时，把物理定律（PDE）当硬约束塞进损失函数——用自动微分算残差，物理律就成了先验，少样本也能学好。

## PINN 标准框架（本课题所有"物理信息"的根基）

1. **解函数逼近**：NN $u_\theta(x,t)$ 逼近 PDE 解。
2. **自动微分算残差**：对 NN 输出求导，代入 PDE $f(x,t;u,\nabla u,\ldots)=0$ 得物理残差 $r_\theta$。
3. **联合损失**：$\mathcal{L} = \mathcal{L}_{data} + \mathcal{L}_{PDE} + \mathcal{L}_{BC/IC}$，数据拟合 + 物理残差 + 边界/初值约束。
4. **两类模型**：连续时间（残差在连续时空配点）与离散时间（用 Runge-Kutta 等离散）。
5. **两类问题**：Part I 正问题（解 PDE），Part II 逆问题（从数据发现 PDE 参数/形式）。

## 对开题的意义（定义"PINN"的基准）

1. **这是"PINN"一词的来源**——开题用 PINN 必引此为定义锚。所有"物理信息"创新点都要对照此基准说明自己的"物理"是什么 PDE/守恒律。
2. **"物理残差"的标准定义**：自动微分算 PDE 残差。开题方案 B（守恒不变量残差）属此框架的特例——守恒律即 PDE，残差即违反度。
3. **数据高效是核心卖点**：物理约束减少对标注数据的依赖——与 [[INVARLLM-物理不变量提取]]、[[PIGCRN-化工过程攻击检测]] 的小样本优势一致。
4. **逆问题思路可借**：Part II 的"从数据发现 PDE"可启发开题——若网络流量的"动力学"未知，能否用数据驱动发现其守恒关系（呼应 INVARLLM 的 LLM 提取不变量）。

## 局限 / 疑问

- 原始 PINN 解的是已知 PDE；网络流量的"守恒 PDE"需开题自己定义并验证（见 [[TCP-AQM二维流体模型]] 的数据可行性问题）。
- PINN 训练有收敛/梯度病态问题——这正是 [[课程式PINN-高斯混合]]、[[课程式PINN-空间相关]] 改进的对象，也呼应开题课程式学习的动机。
