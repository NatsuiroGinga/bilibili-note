---
title: "Physics-Informed Graph Convolutional Recurrent Network for Cyber-Attack Detection in Chemical Process Networks"
authors:
  - Guoquan Wu
  - Haohao Zhang
  - Wanlu Wu
  - Yujia Wang
  - Zhe Wu
year: 2025
date: 2026-07-15
journal: Industrial & Engineering Chemistry Research, 2025, 64: 3370-3382
source_pdf: "[[physics-informed-graph-convolutional-recurrent-network-for-cyber-attack-detection-in-chemical-process-networks.pdf]]"
tags:
  - PINN
  - 化工过程
  - 图卷积
  - CPS
  - 攻击检测
  - 物理信息
  - 类型/论文
aliases:
  - PIGCRN
  - 化工过程PIGCRN
key_finding: 提出 PIGCRN——把化工过程拓扑建成有向图（GCN 捕获空间依赖）+ LSTM 捕获时间依赖，将 first-principles 非线性动力学与攻击模式先验嵌入物理信息损失，在自构造 Aspen Plus 仿真上小样本下优于纯数据驱动方法。
method: 过程拓扑→有向图（节点=测量量，边=物理/控制通路，权重=互信息）+ GCN+LSTM(GCRN) + 物理信息损失（first-principles ODE ẋ=F(x,u) 约束 + 几何攻击模式先验）
baseline: 传统数据驱动 CNN/ML 方法
---

# PIGCRN: 化工过程网络攻击检测

> Wu Guoquan 等 · I&EC Research 2025 · 13 页 · DOI 10.1021/acs.iecr.4c03601

> 注：改进素材参考文献 [1]。原素材作者"吴刚, 张辉"、页码"64(4):1982-1993"均错——真实作者 Guoquan Wu 等 5 人、页码 64:3370-3382。

## 一句话

化工过程有拓扑、有时序、有小样本痛点——把过程建成图、把 first-principles 动力学方程和攻击模式都塞进损失函数，用 GCN+LSTM 同时抓空间和时间，小样本下检测胜过纯数据驱动。

## "物理"是什么（对本课题最直接的参照）

这是三篇 PINN-IDS 应用里**最严谨、最值得参照**的一篇，"物理信息"三层：

1. **first-principles 动力学**：子系统非线性 ODE $\dot{x}_i = F_i(x, u_i)$（Lipschitz），传感器测量 $\bar{x}_i = s_i(x_i)$，无攻击时 $s_i(x_i)=x_i$。攻击打破的是"测量应满足过程动力学"。
2. **过程拓扑先验**：把单元操作/物流管线/控制回路建成有向图，节点=过程变量，边=物理通路与功能依赖（上游影响下游）。边权用**互信息**（数据驱动，避开难推导的 first-principles 模型）。
3. **攻击模式先验**：几何攻击 $\bar{x}_{t_k}=x_{t_k}+\beta(1+\alpha)^{k-k_0}$ 等模式嵌入物理信息损失。

物理信息损失 = 数据拟合 + 动力学/攻击模式约束。检测信号是模型预测与实测的偏差。

## 数据集（关键：自构造仿真）

- **自构造**：两个反应器的化工过程网络，用 **Aspen Plus Dynamics** 仿真生成。
- 这正面印证了开题"公开数据集不够、需自构造测试床"的判断——严谨的 PINN-IDS 工作普遍用自构造仿真，因为公开数据没有可算物理残差的信号。

## 对开题的意义

1. **"物理"可分层定义**：不必非得是单一 PDE——first-principles 动力学 + 拓扑先验 + 攻击模式先验都是"物理信息"。开题的守恒不变量 + 协议状态先验可类比此分层。
2. **拓扑图 + 互信息边权**：网络流量的"节点=交换机/主机、边=链路、边权=流量相关性"可直接借鉴，做图级守恒检测。
3. **自构造仿真是标配**：进一步支撑开题数据集构建章的必要性。
4. **小样本优势是 PINN 的核心卖点**：与 INVARLLM 一致——物理约束减少对标注数据的依赖。

## 局限 / 疑问

- 化工过程有明确 first-principles ODE；网络流量的"动力学方程"是什么？这正是开题要回答的（守恒不变量 vs TCP 流体）。
- 互信息边权是数据驱动的，严格说不是"物理"——开题若用，需说明这是拓扑先验而非物理律。
- 仅仿真验证，无真实流量。
