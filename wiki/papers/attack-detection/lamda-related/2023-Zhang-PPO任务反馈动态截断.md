---
title: "2023-Zhang-PPO任务反馈动态截断"
authors: "Zhang, Tonghan; Xu, Jiahui; Zhuang, Zhongxia; Zhang, Hantao; Liu, Jianzhao"
year: 2023
date: 2026-10-15
journal: "AAAI 2024 / arXiv:2312.07624"
source_pdf: "raw/papers/attack-detection/lamda-related/2023-Zhang-PPO任务反馈动态截断.pdf"
tags:
  - 类型/论文
  - attack-detection
  - 机制/截断界闭环化
key_finding: "Pb-PPO 把 PPO 的固定截断界换成双层优化：以候选界集合 ζ 为臂、按 Return 反馈用 UCB 选 ε\*。证明「截断界本身可闭环」是活跃方向；但其反馈信号是任务回报，与我们的预算约束型目标不同构，仅作存在性引用。"
---

# Pb-PPO：截断界本身可闭环（存在性引用）

## 背景与定位

PPO 固定截断界 ε 限制探索、影响稳定性；Pb-PPO 用多臂老虎机 + UCB 在候选界集合 ζ={ε₀,…,ε_n} 中按训练回报反馈选界。与 PPO 原文的另一条路（KL 惩罚系数闭环）互补：一个调「惩罚量」，一个调「截断量」。

## 方法核心（原文）

- 双层优化：外层 `ε* = argmax_ε U(ε) + λ·Û(ε)`（UCB），内层 PPO 以 ε\* 训练。
- 反馈信号：用候选界训练后的策略 rollout k 次取平均 Return，更新该臂期望。
- 实现细节：k=2 或 10，λ=5，10 个候选界均匀采样。

## 与缺陷 A 的关系（本课题推论）

- 判读：「把固定截断换成反馈选择」是活跃方向（ICLR 2026 BAPO 同向），我们任务给定的「cap 已是解法的一部分」与该方向一致。
- 不可直接移植的原因：bandit 的反馈是任务回报；我们的复用倍数目标 m\*=4 是预算约束，不是要最大化的量，没有等价回报信号——**仅作存在性引用，不落式**。
- 处理 (i)：是（界随反馈移动）；处理 (ii)：否。

## 不可直接声称的内容

- Pb-PPO 处理的是 RL 回报意义上的界选择，没有凸映射或分布漂移分析。
- 其优势结论来自机器人连续控制任务（Gym-Mujoco、legged-gym），不能平移到恶意软件检测训练。