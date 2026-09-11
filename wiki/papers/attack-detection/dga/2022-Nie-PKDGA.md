---
schema: paper-note-search/v1
title: "PKDGA: A Partial Knowledge-based Domain Generation Algorithm for Botnets"
title_zh: "PKDGA：面向僵尸网络的部分知识域生成算法"
authors: [Yuxuan Nie, Yongxin Shan, Zhen Ling, Xinwen Fu, Wei Yu, Chen Zhao, Wenjia Wu, Junzhou Luo]
year: 2022
date: 2026-09-11
journal: "arXiv:2212.04234v1（预印本；会议归属未在本地核验）"
arxiv_id: "2212.04234v1"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2022-Nie-PKDGA.pdf]]"
tags: [DGA生成, 强化学习, 策略梯度, 对抗规避, 概念漂移, 类型/论文]
aliases: [PKDGA, Nie2022PKDGA]
tasks: [RL生成AGD, 黑盒规避, 对抗训练抵抗, 增量检测博弈]
datasets: [Alexa top 1M（10万良性）, DGArchive（10万AGD，93家族）, 各DGA单独10万测试集]
methods: [LSTM策略网络, REINFORCE式策略梯度, 蒙特卡洛rollout估计中间奖励, DNS反馈奖励, 私有DNS试验床]
metrics: [AUC, 反检测能力%(≈1−AUC), 训练/推理时间, 内存占用]
key_finding:
  - "**「RL 学 DGA 生成器」的完整先例（本节即报告所称最危险 RL-DGA 近邻）**：把域名的**每个 token 当作一个 action**（式 6）、已生成 token 序列为 state（式 4）、`date` 为 seed（式 5）、DNS 注册反馈为 reward（式 10）、并用 **likelihood-ratio 策略梯度**（式 13–14）＋**蒙特卡洛搜索**估计中间状态奖励（式 16–17，超参 `m = 10/15/20`）。⇒ **「字符级 policy gradient 做 DGA」不能再作为本课题创新点。**"
  - "**反检测能力**（＝`1 − AUC` 口径，见 §V-C 自述「approaches 50%, i.e., the corresponding detection AUC is approximately 50%」）：零知识设定下 PKDGA 平均 `26.53%`（Kraken `8.29%`、Gozi `22.87%`、Suppobox `23.47%`、Khaos `23.01%`）；部分知识设定下相对 Khaos／Kraken／Gozi／Suppobox 分别提升 `24.52%／39.24%／24.67%／24.07%`；全知识设定对 NN 检测器平均 `49.19%`，略低于 Khaos `50.68%`（差距 `1.49%`）。"
  - "**Finding #2：PKDGA 能抵抗对抗训练**（§V-C-2）：在「训练 DGA 与测试 DGA 相同」的对抗训练场景下 PKDGA 仍保持高反检测能力，而传统 DGA 表现很差（如 Suppobox 低至 `2.10%`）；作者解释为学习式策略可持续产出**新的**对抗域名。⇒ **「学习型攻击器可穿越对抗训练」在 DGA 上已有先例。**"
  - "**§VI 提出「博弈式防御」＝交替循环的又一先例**（式 21–22）：反复执行「训练 PKDGA 攻破 `D_target`」→「用新 AGD 增量训练 `D_target`」直至攻击失效；作者自陈**实践受限**（需反编译 bot 样本以取得在用的 DGA，成本高且对手更新后需重新获取），未来工作转向「增量 NN 检测器 vs 本地 PKDGA」的博弈。"
  - "**概念漂移是本篇的核心动机**（§II-B Observation #2、§II-C）：全知识 DGA（如 Khaos，WGAN）依赖目标梯度回传，一旦目标与真实检测器不同即出现 concept drift、反检测能力显著下降；PKDGA 只用可观测反馈，因而规避该问题。"
supports:
  - "「学习型攻击器 → 持续产出新规避样本 → 检测器需反复增训」这一非平稳结构在 DGA 上确有先例（本篇 §V-C-2 与 §VI）"
  - "只用可观测反馈（DNS 注册／检测器判定）即可训练攻击器——与本课题「只用黑盒 detector 分数构造 reward」同构"
cannot_support:
  - "本课题「源条件化、预算受限的一步扰动策略」等价于 PKDGA（本篇是从 seed 自回归生成**完整域名**）"
  - "PKDGA 的 AUC／反检测能力数字可迁移到本课题的字符级 Transformer 与跨年面板"
  - "本课题首次提出「攻击者—检测器交替训练」"
related: ["[[2016-Anderson-DeepDGA]]", "[[2019-Corley-DomainGAN]]", "[[2019-Peck-CharBot规避攻击]]", "[[2024-Drichel-DGA检测鲁棒分类]]"]
---

# PKDGA

> **锚点说明**：本地 PDF 共 **12 页**；MinerU 转换产物**无页标记**，本笔记一律用**节号与式号**锚定（`§III-B`、式(10)–(17) 等），**页码待补**。
> 本笔记依本地 PDF **全文**写成（2026-09-11 入库；arXiv `2212.04234v1`，正文读至 §VIII 结论，参考文献未逐条录入）。

## 一、机制（按节号）

- **总体（`§III-A`）**：把「AGD 的 token」当 **action**、把「反馈」当 **reward**、把「检测器」当 **environment**，用 RL 探索域生成器；两阶段＝**模型训练**（生成→注册→反馈→更新生成器）与 **domain fluxing**（把学到的生成器替换进 Mirai 等恶意软件，C&C 与 bot 用同一 seed 生成同一批候选域名）。
- **RL 形式化（`§III-B`）**：state `s_t = [y_0,…,y_{t−1}]`（式 4，`y_0` 为 seed，本篇取 **date**，式 5）；action `a_i ∈ Y`（式 6，token 字典含字母／数字／连字符）；按 `argmax π_θ(a_i|s_t)` 选 token（式 7）、`s_{t+1} = [s_t, y_t]`（式 8）；**reward `R(Y) = DNS(Y)`**（式 10）；目标 `argmax_θ E[R(Y)]`（式 11）、策略梯度式 (13)(14)。
- **中间奖励用 Monte Carlo 估计（`§III-B`、式 16–17）**：末状态奖励可直接算；中间状态的奖励由 **`m` 次 MC rollout** 补全后继 token 后取平均。`m` 是超参（网格搜索取值 `10/15/20`）。**这是「完整序列只在终局得到奖励」的标准处理**——本课题的一步扰动只需**一次终局分数**，因此不需要该复杂度。
- **策略网络（`§III-C`）**：LSTM（避免长序列梯度爆炸／消失）；`d_y` ＝ token 字典大小，`d_h`、`d_e`、层数 `N_l` 均由网格搜索定（`TABLE III`：最优 `N_l = 1, d_e = 32, d_h = 64, m = 20, lr = 0.001, b = 64`）。
- **实现（`§IV`）**：自建**私有 DNS**（用 dnsmasq）以指定被攻击检测器；模拟反馈 `DNS(Y) = D(Y)·N(Y)`（式 18–19）＝「被检测器判为合法」×「域名未注册（novel）」；bot 用 Mirai。
- **评测（`§V-A`）**：训练集 10 万良性（Alexa top 1M）＋10 万 AGD（DGArchive，93 家族）；检测器＝Statistics／WordGraph／FANCI／CNN／LSTM／Bi-LSTM；指标 **AUC**，并换算为**反检测能力（%）**。
- **§VI 博弈式防御**：交替「训练 PKDGA → 增量训练检测器」（式 21–22）；NN 检测器（LSTM／BiLSTM／CNN）经增量学习可达 **≥80% 检测 AUC**，而非 NN 检测器（如 FANCI 只能改叶节点／子树）效果差。作者明确指出**该防御代价高**：须反编译 bot 样本以取得在用的 PKDGA，且对手更新后要重新获取。

## 二、原文关键数字

| 项 | 数值 | 位置 |
| --- | --- | --- |
| 零知识设定（平均反检测能力） | PKDGA `26.53%`；Khaos `23.01%`；Suppobox `23.47%`；Gozi `22.87%`；Kraken `8.29%` | `§V-C-1` |
| 部分知识设定（相对提升） | vs Khaos `+24.52%`；vs Kraken `+39.24%`；vs Gozi `+24.67%`；vs Suppobox `+24.07%` | `§V-C-1` |
| 全知识设定（对 NN） | PKDGA 平均 `49.19%` vs Khaos `50.68%`（差 `1.49%`） | `§V-C-1` |
| 训练集稳健性 | 无论检测器用哪个 DGA 训练，PKDGA 保持 `≥ 39.7%`；对照 Gozi 在 FANCI 上由 `72.7%` 掉到 `2.60%` | `§V-C-2`、`Finding #1` |
| 对抗训练抵抗 | 自训自测场景下 PKDGA 仍高；Suppobox 低至 `2.10%` | `§V-C-2`、`Finding #2` |
| 开销 | 训练 60 epochs ≈ 600 分钟（2080Ti）；推理 1–3 ms／域名；C++ 版内存约为 Python 版 1/30（Python > 152.8 MB） | `§V-D` |

## 三、与本课题的关系（差量四层的第二层）

- **该层做什么**：**从 seed 自回归生成完整域名**（token 级 MDP ＋ 终局反馈 ＋ 策略梯度 ＋ MC rollout）。
- **本课题的边界**：本课题**不生成完整域名**——动作是**对已知恶意域名的一次结构化编辑元组**（位置／替换字符，含编辑预算 `B` 与 hard mask），reward 来自检测器的**连续分数**而非 DNS 注册反馈；且本课题的检测器**会被更新**（交替训练），而 PKDGA 的生成器训练针对**固定（或模拟）目标**（其检测器更新只出现在 `§VI` 的**防御提案**里，不是它自己的方法）。
- **可直接引用的三条支持／警示**：
  1. **只用可观测反馈即可训练攻击器**（`§III-A`、`§IV`）——与本课题「黑盒 detector 分数作 reward」同构，说明本课题的攻击器设计**不需要**白盒梯度；
  2. **学习型攻击器可穿越对抗训练**（`§V-C-2` `Finding #2`）——本课题方向 a 的**强动机**：AT 未必能修复「可学习攻击者」造成的威胁；
  3. **交替循环已有先例**（`§VI` 式 21–22「训练攻击器→增量训练检测器」）——本课题**不得**把「交替训练」本身写成首创；差量只能落在**源条件化扰动动作 ＋ 同源多样本 RLOO ＋ 跨源配额分配 ＋ benign-FP 保护**这一组合上。
- **不可用**：`§V-C` 的 AUC／反检测能力数字**不可迁移**到本课题（模型、数据、威胁模型、指标口径全不同）。

## 四、引用纪律

- **表述禁用项**：「首次用 RL／策略梯度学 DGA 生成器」「首次做字符级 policy gradient DGA」「首次做攻击者—检测器交替训练」——本篇前三项均有直接对应（第三项见 `§VI`）。
- **页码待补**：正文引用数字时须回 PDF 逐页核对页码后回填；在此之前只写节号与式号。
- **版本提示**：本地原件为 **arXiv `2212.04234v1`**，会议归属（若有）未核验，引用须注明为本预印本版本。
