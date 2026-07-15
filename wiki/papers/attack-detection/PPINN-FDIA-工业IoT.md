---
title: "Robust Industrial IoT Security Leveraging Parallel Physics-Informed Neural Networks to Combat False Data Injection"
authors:
  - Basi Reddy A.
  - R. Yogesh
  - M. Sriram
year: 2025
date: 2026-07-15
journal: International Journal of Information Technology & Decision Making, 2025
source_pdf: "[[robust-industrial-iot-security-leveraging-parallel-physics-informed-neural-networks-to-combat-false-data-injection.pdf]]"
tags:
  - PINN
  - 工业IoT
  - 虚假数据注入
  - FDIA
  - 攻击检测
  - 物理信息
  - 类型/论文
aliases:
  - PPINN-FDIA
  - 工业IoT并行PINN
key_finding: 用并行 PINN（PPINN，域分解+自动微分算 PDE 残差）+ 分布式集员融合滤波预处理 + Giza 金字塔优化调参，检测 IIoT 虚假数据注入攻击（简单/隐蔽/串通 FDIA），声称 F1 比现有方法高 23-28%。
method: DSMFF 去噪 → PPINN（数据 MSE + PDE 残差 MSE，阈值判攻击）→ GPCO 优化权重 → DADBN 清洗
baseline: 多个 FDIA 检测方法（联邦学习、图自编码器、RLR 等）
---

# PPINN-FDIA: 工业 IoT 虚假数据注入检测

> Basi Reddy A. 等 · Bharath Institute · Intl. J. of Information Technology & Decision Making 2025 · 26 页 · DOI 10.1142/s0219622025501081

> 注：改进素材参考文献 [2]。原素材作者"ALAM/RAHMAN/ISLAM"、期刊"IJPRAI"均错——真实作者 Basi Reddy/Yogesh/Sriram、期刊 IT&DM。

## 一句话

用并行 PINN 检测 IIoT 传感器虚假数据注入，损失里加 PDE 残差项，配一个金字塔元启发式调参。

## ⚠️ 质量警示（对本课题的负面参照）

这是三篇里**质量最弱**的一篇，作为"反面教材"参考：

1. **"物理"定义不清**：通篇说"PDE 残差""governing PDEs"，但**从未明确电负荷数据服从什么物理方程**。数据是 US EIA 小时用电负荷——这并非受 PDE 支配的物理过程，"PDE 残差"成了空壳术语。这与开题要警惕的"给正则项贴 PINN 标签"是同一类问题。
2. **方法拼凑**：DSMFF 预处理 + PPINN + Giza 金字塔构造优化（GPCO，gimmicky 元启发式）+ DADBN 清洗，组件堆叠，论证不紧密。
3. **写作质量低**：符号混乱（"NRT"记号含义不清）、表述生硬、实验对照基准描述粗糙。
4. **数据集与 FDIA 任务的匹配存疑**：用 EIA 用电负荷数据评估 FDIA 检测，缺少典型电力系统状态估计/坏数据检测的对照。

## 对开题的意义（主要作为风险警示）

1. **"physics-informed" 不能空喊**：必须明确"什么物理定律、残差怎么算、为何攻击会打破它"。本篇正因为没定义清楚，PINN 名不副实。开题引此为戒——守恒不变量必须落到可计算的具体方程。
2. **不要 gimmicky 优化器堆叠**：GPCO 这类元启发式调参在严肃方法学里易被质疑。开题应用成熟的 GRPO/课程机制，而非堆砌。
3. **数据集要匹配任务**：EIA 负荷数据做 FDIA 检测的合理性被作者跳过。开题自构造数据集必须论证"数据能支撑物理残差计算"。

## 局限 / 疑问

- PDE 残差项到底对应什么物理？论文未交代，引用时**不可采信其"PINN"声明**。
- 23-28% F1 提升的对照基准是否公平，存疑。
- 此文可作为开题"相关工作局限性"的反例：现有 PINN-IDS 有物理定义不清、方法拼凑的问题，凸显本课题明确定义守恒物理的必要性。
