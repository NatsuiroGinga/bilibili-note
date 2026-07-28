---
title: 博弈论训练优化论文索引
date: 2026-07-21
tags:
  - 博弈论
  - 多目标优化
  - 梯度协调
  - MOC
  - 类型/MOC
aliases:
  - 博弈论论文 MOC
  - 博弈论训练优化索引
related:
  - "[[PINN 论文阅读索引]]"
  - "[[朱焱雷-加密流量博弈对抗与高效训练]]"
---

# 博弈论训练优化论文索引

本索引区分两类用途：一类直接研究多任务或主辅任务的梯度协调，另一类研究具有独立策略空间的主从学习或攻击防御。当前第三章只把前者作为直接训练证据，把后者作为参数分组与更新动态的候选启发。

## 多目标与辅助任务协调

- **[[Nash-MTL-多任务对称议价训练|Nash-MTL 对称议价训练]]** — 把各任务梯度视为地位相同的玩家，以比例公平共同方向处理梯度冲突；适合作为三目标对称基线。
- **[[AuxiNash-辅助学习非对称议价训练|AuxiNash 非对称议价训练]]** — 用主任务验证性能学习议价偏好；与生成主任务、状态辅助任务和物理辅助任务的关系最接近。

## 主从学习与双时间尺度

- **[[SCORER-表征与强化学习斯塔克尔伯格耦合|SCORER 双时间尺度主从耦合]]** — 以控制网络领导、表征网络跟随，通过停梯度和快慢更新近似主从均衡；只能迁移结构思想，不能照搬强化学习目标。
- **[[raw/papers/game/2109.12286v1.pdf|Stackelberg Actor-Critic 原始 PDF]]** — 用领导者全导数处理策略与价值网络相互响应，适合比较显式反应梯度与一阶双时间尺度的差异。

## 斯塔克尔伯格与纳什基础材料

- **[[raw/papers/game/stackelberg-vs-nash_2011_kiekintveld.pdf|安全博弈中的斯塔克尔伯格与纳什比较]]** — 讨论安全博弈中均衡概念和承诺优势，不直接提供共享参数梯度协调算法。
- **[[raw/papers/game/korzhyk-2010_complexity-Optimal-Stackelberg-Strategies.pdf|最优斯塔克尔伯格策略复杂度]]** — 提供求解复杂度与策略空间背景，不可直接外推到深度网络训练。
- **[[raw/papers/game/dobss-2008_pita-etal_Bayesian_Stackelberg_Game.pdf|贝叶斯斯塔克尔伯格安全博弈]]** — 面向不完全信息下的防御资源配置，适合作为安全博弈背景。
- **[[raw/papers/game/klp_game_theoretic_foundations_2014.pdf|安全博弈理论基础]]** — 梳理安全博弈的玩家、资源和均衡概念。

## 网络安全场景材料

- **[[raw/papers/game/2211.01508_2022_Partially-Observable_Security_Games_for_Automating_Attack-Defense_Analysis.pdf|部分可观测攻击防御安全博弈]]** — 用于攻击者、防御者和观测不完备的威胁建模。
- **[[raw/papers/game/s10207-025-01012-4_2025_Enhancing_Network_Security_Through_Integration_of_Game_Theory_in_SDN.pdf|博弈论增强软件定义网络安全]]** — 用于网络防御决策背景，不是多目标训练方法证据。
- **[[raw/papers/game/s10207-025-01026-y_2025_Detecting_Malicious_Nodes_using_Game_Theory_and_Reinforcement_Learning_in_SDNs.pdf|博弈论与强化学习检测软件定义网络恶意节点]]** — 用于安全响应与恶意节点场景，不直接支持生成、状态和物理三目标协调。
- **[[raw/papers/game/s40747-024-01553-6_2024_PPSO_and_Bayesian_Game_for_Intrusion_Detection_in_WSN.pdf|无线传感器网络入侵检测中的贝叶斯博弈]]** — 用于入侵检测博弈背景，需与共享模型训练问题区分。

## 当前课题的证据分工

| 文献                     | 可直接承担的角色                           | 不能直接声称                             |
| ------------------------ | ------------------------------------------ | ---------------------------------------- |
| Nash-MTL                 | 对称三目标梯度协调基线                     | 生成主任务受到优先保护                   |
| AuxiNash                 | 主辅非对称协调强基线与方法启发             | 已解决物理可靠性和生成性能硬约束         |
| SCORER                   | 参数分组、角色顺序、停梯度和双时间尺度消融 | 其强化学习目标可直接用于恶意流量生成训练 |
| Stackelberg Actor-Critic | 显式反应梯度或主从全导数比较               | 当前损失天然构成策略网络与价值网络关系   |
| 攻击防御安全博弈         | 威胁模型或原型系统响应策略背景             | 攻击者与防御者博弈等于训练损失之间的博弈 |

## 阅读顺序

1. 先读 Nash-MTL，理解对称议价的效用与共同方向。
2. 再读 AuxiNash，理解主辅任务不对称和偏好元学习。
3. 最后读 SCORER，判断是否需要把共享模型拆成主从参数块，而不是把三个损失机械改名为玩家。
