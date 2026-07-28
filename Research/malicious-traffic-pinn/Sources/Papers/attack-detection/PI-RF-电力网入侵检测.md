---
title: "Enhancing Intrusion Detection in Electric Networks Using Physics-Informed Random Forest"
authors:
  - Mehmet Bozdal
  - Alper Savaşci
year: 2024
date: 2026-07-15
journal: 2024 Innovations in Intelligent Systems and Applications Conference (ASYU), IEEE, 1-5
source_pdf: "[[Enhancing_Intrusion_Detection_in_Electric_Networks_Using_Physics-Informed_Random_Forest.pdf]]"
tags:
  - 物理信息
  - 随机森林
  - 电力网
  - 入侵检测
  - 特征工程
  - 类型/论文
aliases:
  - PI-RF
  - 电力网物理信息随机森林
key_finding: 从电气基本原理派生物理特征（复功率 S=V·I*、阻抗 Z）加入 PMU 测量，配 SelectKBest 特征选择喂随机森林，55 特征下准确率 0.9667/F1 0.9664，略优于基线 RF；作者自承"提升边际"。
method: 物理派生特征工程（复功率、阻抗）+ SelectKBest(mutual information) 特征选择 + Random Forest 分类
baseline: 标准随机森林（仅 V/I 原始特征）、ML-RF、ADA-JRIP
---

# Physics-Informed Random Forest: 电力网入侵检测

> Bozdal, Savaşci · Abdullah Gül Univ · ASYU 2024 · 5 页 · DOI 10.1109/asyu62119.2024.10757087

> 注：改进素材参考文献 [3]。原素材作者"ALOTAIBI/ALKHALDI/ALSHARIF"、会议"ICCEP/CPEE"均错——真实作者 Bozdal/Savaşci、会议 ASYU 2024。

## 一句话

"physics-informed" 在这里**只是特征工程**——从 V/I 算出复功率和阻抗当新特征喂随机森林，不是 PINN。

## "物理"是什么（光谱的最宽松端）

这篇定义了"physics-informed IDS"光谱的**最宽松一端**：

- "物理"= 电气基本定律派生的特征：复功率 $S = V \circ I^*$、阻抗 $Z = (V_i - V_j) \triangle I$。
- **没有 PDE 残差、没有物理约束损失、没有自动微分**——纯粹把物理量当额外特征。
- 检测靠随机森林分类，物理只参与特征构造。

## 数据集与结果

- ORNL/Mississippi State 电力系统攻击数据集：3 母线 2 线拓扑，RTDS 实时仿真 + PMU 硬件在环，128 路测量，15 子集 37 事件。
- 物理+选择(55 特征)：准确率 0.9667 / F1 0.9664；基线 RF：0.9576 / 0.9570。**提升约 0.9 个百分点**。
- 作者诚实承认"improvements were marginal"。

## 对开题的意义（定位"physics-informed"光谱）

1. **"physics-informed" 是个光谱**，从宽到严：
   - 宽：物理派生特征（本篇 [3]）——几乎不算 PINN
   - 中：物理不变量/守恒残差作约束（[[INVARLLM-物理不变量提取]]）
   - 严：first-principles PDE/ODE 残差损失（[[PIGCRN-化工过程攻击检测]]、Raissi 开山）
2. **开题必须明确定位在哪一端**。本课题应走"中-严"（守恒不变量残差作物理损失），并明确说明不是 [3] 这种特征工程。
3. **诚实报告边际提升**：[3] 坦承提升小——开题若有类似情况应如实报告，不夸大。
4. **物理特征选择思路可借鉴**：SelectKBest+互信息选特征，对开题"哪些守恒不变量区分力强"的筛选有参考。

## 局限 / 疑问

- 仅特征工程，无物理约束损失，"physics-informed"名号偏宽。
- 提升边际，实用价值有限。
- 仅电力网 PMU 数据，非通用网络流量。
