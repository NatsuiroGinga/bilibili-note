---
title: A two dimensional fluid model for TCP/AQM analysis
authors:
  - Sadek Belamfedel Alaoui
  - Alejandro J. Rojas
  - Abdelaziz Hmamed
  - El Houssaine Tissir
year: 2022
date: 2026-07-14
journal: arXiv preprint (eess.SY)
source_pdf: "[[2211.10833.pdf]]"
tags:
  - 网络安全
  - TCP/AQM
  - 流体模型
  - 控制理论
  - 物理信息
  - 类型/论文
aliases:
  - TCP-AQM二维流体模型
  - Belamfedel2022-TCP流体
key_finding: 提出一个二维（路由器队列时间基 + 拥塞窗口时间基）非线性流体模型描述 TCP/AQM 拥塞控制，并构造二阶 Bessel-Legendre Lyapunov 泛函做局部稳定性分析与反馈控制器综合。
method: 双时间基（horizontal=TCP cwnd 更新，vertical=AQM 丢包动作）推导 2D 非线性流体方程 → 在平衡点一阶 Taylor 线性化 → 2D 时滞系统 LMI 稳定性判据 + 反馈增益综合
baseline: Xu et al. (2015) 的一维流体模型（本文模型可退化为该模型）
---

# A two dimensional fluid model for TCP/AQM analysis

> Belamfedel Alaoui 等 · arXiv:2211.10833 · 2022-11 · 9 页

## 一句话

把 TCP/AQM 拥塞控制拆成"窗口演化"和"队列丢包"两个时间基，导出一组二维非线性流体微分方程，用来做稳定性分析和控制器设计——**这是一篇控制理论论文，不是攻击检测论文**。

## 状态量与方程

模型的状态变量（也是开题报告里"物理建模"想用的量）：

- $W(t) \in [0, \bar W]$：平均拥塞窗口大小（包数）
- $q(t) \in [0, Q_{max}]$：队列长度（包数）
- $\tau(t) = q(t)/C(t) + T_p$：往返时延 RTT
- $p(t) \in [0,1]$：丢包/标记概率
- $C$：链路容量（包/秒），$T_p$：传播时延，$N$：TCP 会话数，$\lambda$：窗口分布参数

核心方程按 TCP 三种模式（慢启动 / 拥塞避免 / 快恢复）分场景给出 $\partial W^h/\partial t_1$、$\partial q/\partial t$ 的耦合 ODE。本质是 **AIMD（加性增乘性减）** 行为的连续化微分方程。

## 我的理解（对开题方案 A 的意义）

这篇是开题报告改进稿（第一份 md）选作 PINN"物理先验"的 TCP/AQM 流体方程原文。读完后的判断：

1. **方程本身真实、成熟**：是网络流体动力学领域公认模型（Mathis/Kelly/Low/Misra 线），用作"支配方程"在方法论上站得住。
2. **但它是 TCP 专属的聚合拥塞动力学**：状态量是 cwnd/队列/RTT/丢包概率，描述的是**响应式 TCP 流的拥塞行为**。三个前提对 IDS 场景很硬：
   - IDS2018 的 CICFlowMeter CSV **不提供** cwnd、队列长度、丢包概率——这些是路由器/端侧内部量，流级特征里没有。
   - UDP/ICMP 洪泛（DDoS 主力）**不服从 TCP 流体方程**，会被一律判为残差异常 → 误报。
   - 方程描述的是"正常拥塞演化"，攻击（端口扫描、漏洞利用）未必通过打破拥塞方程来体现。
3. **它是控制论文，非检测论文**：原文目标是设计 AQM 反馈控制器，没有任何攻击检测的实验或论述。把它直接当 PINN 检测的物理先验，需要自己补"残差→攻击"的整条论证链。

**结论**：方案 A（TCP 流体）的"物理"最像教科书 PINN，但与通用 IDS 数据集 + 非 TCP 攻击匹配度最差。若坚持用，必须把研究场景**限定在 TCP 聚合流量**且解决 cwnd/队列的重建问题。

## 疑问 / 待验证

- 能否从 CICFlowMeter 的 `Init_Win_bytes`、`min/max Packet Length`、`Flow Duration` 等字段近似重建窗口/队列时间序列？需实测，疑似不可行。
- 是否存在 TCP 流体方程在 IDS2018 上算残差的已有工作？目前未检索到。
- 与 [[INVARLLM-物理不变量提取]] 的"守恒律不变量"路线相比，哪条更适合通用网络攻击检测？倾向于后者。
