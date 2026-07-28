---
title: "NewtonianVAE: Proportional Control and Goal Identification from Pixels via Physical Latent Spaces"
authors:
  - Miguel Jaques
  - Michael Burke
  - Timothy M. Hospedales
year: 2021
date: 2026-07-22
journal: "IEEE/CVF Conference on Computer Vision and Pattern Recognition"
source_pdf: "[[raw/papers/manifold/NewtonianVAE-CVPR2021.pdf]]"
tags:
  - 类型/论文
  - 主题/物理表征
  - 主题/潜在动力学
  - 主题/可控表示
key_finding: "NewtonianVAE 把位置、速度和控制作用写入潜在转移先验，未来观测由转移后的物理潜变量解码，因此物理潜状态对主输出具有严格前向依赖。"
method: "带牛顿运动先验的变分自编码器、对角可控转移、像素到潜在位置和速度推断"
baseline: "LSTM、E2C、DVBF、Kalman VAE、GAIL 及潜空间控制消融"
aliases:
  - NewtonianVAE
  - Jaques2021-NewtonianVAE
---

# NewtonianVAE: Proportional Control and Goal Identification from Pixels via Physical Latent Spaces

> Miguel Jaques, Michael Burke, Timothy M. Hospedales, 2021, CVPR · PDF 10 页

## 一句话

NewtonianVAE 证明了一条可迁移的结构原则：先从观测推断满足物理转移的潜状态，再由转移状态解码主输出；这样物理约束与生成任务共享同一条可微前向路径。

## 研究问题与方法

普通生成潜空间不保证动作方向与状态变化方向一致，导致简单比例控制仍需额外控制器补偿。论文将潜变量解释为系统位置 $x$，用相邻位置差分得到速度 $v$，并以牛顿型二阶动力学约束转移。

## 前向结构与关键公式

连续动力学写为：

$$
\frac{dx}{dt}=v,
\qquad
\frac{dv}{dt}=A(x,v)x+B(x,v)v+C(x,v)u.
$$

离散生成模型包括：

$$
p(I_{t+1}\mid x_{t+1}),
\qquad
p(x_t\mid x_{t-1},u_{t-1},v_t),
$$

$$
x_t\sim\mathcal N(x_{t-1}+\Delta t\,v_t,\sigma_t^2),
$$

$$
v_t=v_{t-1}+\Delta t\bigl(Ax_{t-1}+Bv_{t-1}+Cu_{t-1}\bigr).
$$

为强化可控性，$A,B,C$ 取对角结构，$C$ 被约束为正，$B$ 被约束为负。公式 6 至 11 及其解释位于 PDF 第 4 页。

## 严格前向依赖判定

- 未来图像由 $x_{t+1}$ 解码，因此 $\partial \hat I_{t+1}/\partial \hat x_{t+1}\neq 0$ 在结构上成立。
- 物理状态由图像后验推断，速度由相邻潜在位置差分获得；推理无需位置或速度真值标签，但需要连续图像，控制场景还需要已执行动作。
- 物理转移先验进入生成证据下界，不是仅由输入计算且对模型参数梯度为零的辅助残差（PDF 第 4 页）。

## 实验与消融证据

- 实验包含模拟点质量、机械臂、Fetch 任务以及真实 PR2 视觉数据（PDF 第 6 页起）。
- 表 1 的切换式比例控制任务中，单个干净示范下 NewtonianVAE 得分为 $3.0\pm0.0$，LSTM 为 $0.81\pm0.35$；噪声示范下分别为 $2.17\pm0.32$ 与 $0.27\pm0.20$。使用 100 个示范的 GAIL 得分为 0.62（PDF 第 7 页）。
- 真实 PR2 数据实验使用 636 帧训练 NewtonianVAE，并用 100 帧留出数据训练目标识别模型，识别出六个目标或片段（PDF 第 7 至 8 页）。这属于真实视觉表征验证，不是从仿真策略直接迁移到真实机器人的证据。

## 成本与推理路径

推理时需要编码连续观测、差分速度、执行一次潜在转移并解码，物理状态标签不在推理接口中。论文没有报告统一壁钟时间、显存、参数量或浮点运算量，不能与 Qwen3-1.7B 的训练成本直接比较。

## 局限与反证

方法假设系统近似满足比例可控的牛顿型动力学，并依赖足够高频的视觉观测。真实实验只覆盖固定目标集合，作者指出需要更多样化示范；高速运动、非牛顿网络动力学和离散攻击过程并未验证（PDF 第 8 页）。对角 $A,B,C$ 提高可解释性，同时也可能限制耦合动力学表达能力。

## 与本课题的关系

- **A 类，物理状态显式融合：高相关。** 状态预测、动力学转移和生成解码处于同一可微链路。
- **B 类，共享/私有表征与负迁移：中等相关。** 结构化物理潜变量替代任意潜空间，但没有显式共享/私有分支。
- **C 类，仿真到真实与状态可辨识：中等相关。** 支持无状态标签的视觉状态推断，但真实实验不是严格仿真到真实迁移。

第三章若预测队列状态，应仿照该结构让文本生成器消费 $\hat q$，而不是只让 $\hat q$ 接受辅助监督；同时要检验预测状态是否可辨识，而非仅具有低状态损失。

## 原始摘要

> 摘要要点经原 PDF 第 1 页核验：论文从像素学习符合牛顿动力学和比例控制关系的潜空间，并在控制与目标识别上验证。此处仅保留中文转述。

## 文献信息

- DOI：[10.1109/CVPR46437.2021.00443](https://doi.org/10.1109/CVPR46437.2021.00443)
- arXiv：[2006.01959](https://arxiv.org/abs/2006.01959)
- 会议论文集：[CVF Open Access](https://openaccess.thecvf.com/content/CVPR2021/html/Jaques_NewtonianVAE_Proportional_Control_and_Goal_Identification_From_Pixels_via_Physical_Latent_CVPR_2021_paper.html)
