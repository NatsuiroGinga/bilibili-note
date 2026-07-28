---
title: "BayesSim: Adaptive Domain Randomization Via Probabilistic Inference for Robotics Simulators"
authors:
  - Fabio Ramos
  - Rafael Carvalhaes Possas
  - Dieter Fox
year: 2019
date: 2026-07-22
journal: "Robotics: Science and Systems XV"
source_pdf: "[[raw/papers/manifold/BayesSim-RSS2019.pdf]]"
tags:
  - 类型/论文
  - 主题/仿真到真实
  - 主题/系统辨识
  - 主题/概率推断
key_finding: "BayesSim 用模拟轨迹学习多模态参数后验，并据目标轨迹调整策略训练的随机化分布；它处理参数不可辨识性，但后验不进入部署策略前向，且论文机器人实验仍在 OpenAI Gym 模拟环境。"
method: "无似然条件密度估计、混合高斯后验、随机傅里叶特征、自适应域随机化"
baseline: "均匀先验、拒绝式 ABC、epsilon-Free、BayesSim 神经网络与随机傅里叶特征版本"
aliases:
  - BayesSim
  - Ramos2019-BayesSim
---

# BayesSim: Adaptive Domain Randomization Via Probabilistic Inference for Robotics Simulators

> Fabio Ramos, Rafael Carvalhaes Possas, Dieter Fox, 2019, RSS · PDF 10 页

## 一句话

BayesSim 的主要价值是把“真实参数可能不可唯一辨识”显式表示为多模态后验，再用后验收缩训练分布；它不是预测状态条件化主策略，也没有真实机器人实证。

## 研究问题与方法

均匀域随机化可能在大量与目标无关的参数上浪费训练。BayesSim 从模拟器采样参数 $\theta$ 与轨迹摘要 $x$，学习条件密度 $q_\phi(\theta\mid x)$，再用目标轨迹摘要估计后验，并按后验随机化策略训练参数。

## 前向结构与关键公式

当训练提议分布 $\tilde p(\theta)$ 与先验 $p(\theta)$ 不同时，后验校正为：

$$
\hat p(\theta\mid x^r)\propto
\frac{p(\theta)}{\tilde p(\theta)}q_\phi(\theta\mid x^r).
$$

条件密度用混合高斯表示，并可用随机傅里叶特征替代深层网络。推导与公式 1 至 5 位于 PDF 第 3 至 5 页。多峰后验允许不同参数组合解释相似轨迹，避免把不可辨识问题强行压成单点回归。

## 严格前向依赖判定

- 后验 $\hat p(\theta\mid x^r)$ 用于选择策略训练时的随机化分布，部署策略本身不以该后验或参数估计为输入。
- 因而对部署输出，$\partial\hat y/\partial\hat q=0$；它属于训练分布适配，不是显式状态融合。
- 目标轨迹不需要参数标签，但模拟器训练样本必须带参数真值，并需要人工或学习得到的轨迹充分统计量。

## 实验与消融证据

- 表 1 在七类系统参数上比较预测对数概率。BayesSim 的随机傅里叶特征版本在多项上较稳定，但不是每一行都最优（PDF 第 7 页）。
- CartPole 策略使用约 2M 环境步；Fetch 推动和滑动任务使用 DDPG+HER，训练 200 个周期、每周期 100 次 rollout（PDF 第 7 至 8 页）。
- 论文说明用正确参数模拟 10 条轨迹作为“真实观测”；Fetch 来自 OpenAI Gym。这里的“真实”是目标模拟器实例，不是物理机器人（PDF 第 7 至 8 页）。

## 成本与推理路径

除策略训练外，还需生成带参数标签的模拟数据、训练条件密度估计器、收集目标轨迹并重建后验。部署策略不增加状态估计分支。论文给出环境步和周期设置，但未报告统一壁钟时间、显存或后验估计总成本。

## 局限与反证

作者指出，轨迹充分统计量需人工设计；端到端 LSTM 摘要可能过拟合模拟器（PDF 第 9 页）。目标系统参数若不在提议分布内，后验校正也无法补救。论文没有物理机器人验证，因此不能写成真实域迁移已被证明。

## 与本课题的关系

- **A 类，物理状态显式融合：低相关且严格判据不成立。** 后验只改变训练分布。
- **B 类，共享/私有表征与负迁移：低相关。** 没有共享/私有结构。
- **C 类，仿真到真实与状态可辨识：高相关。** 提醒状态可能只在后验意义上可辨识，并提供目标无标签校准方法。

第三章可借鉴“多组 ns-3 参数可能产生相似窗口”的不可辨识性诊断，报告状态后验或等价类，而不是只报告单点均方误差。若主张状态耦合，仍需另设 $\hat y=f(x,\hat q)$ 前向路径。

## 原始摘要

> 摘要要点经原 PDF 第 1 页核验：论文以无似然概率推断估计模拟器参数后验，并据此收缩域随机化分布。此处仅保留中文转述。

## 文献信息

- DOI：[10.15607/RSS.2019.XV.029](https://doi.org/10.15607/RSS.2019.XV.029)
- arXiv：[1906.01728](https://arxiv.org/abs/1906.01728)
- 会议论文集：[RSS Proceedings](https://www.roboticsproceedings.org/rss15/p29.html)
