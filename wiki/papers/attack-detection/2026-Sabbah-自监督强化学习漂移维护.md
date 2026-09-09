---
schema: paper-note-search/v1
title: "Concept Drift Adaptation Using Self-Supervised and Reinforcement Learning in Android Malware Detection"
title_zh: "Android恶意软件检测中的自监督与强化学习概念漂移适应"
authors: [Ahmed Sabbah, Mohammad Kharma, Mohammad Alkhanafseh, Radi Jarrar, Samer Zein, David Mohaisen]
year: 2026
date: 2026-09-08
journal: "arXiv 2605.24294v1（2026-05-22，预印本）"
doi: null
arxiv_id: "2605.24294"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/lamda-related/2026-Sabbah-SSL-RL-Android-Malware-Drift.pdf]]"
tags:
  - Android恶意软件
  - 概念漂移
  - 强化学习
  - 自监督学习
  - 模型维护
  - 类型/论文
tasks: [Android恶意软件二分类, 概念漂移维护, 强化学习]
datasets: [Android emulator malware, Android real-device malware]
methods: [自监督编码器, 适配器, PPO, 潜在漂移统计]
metrics: [AUT, 平衡准确率, 宏F1, 记忆准确率, 维护成本]
key_finding:
  - "该预印本把漂移维护定义为 PPO 在保持、分类头、适配器、联合更新和重置之间选动作。"
  - "它明确假设每个新窗口标签立即可用，并把当前评价子集的 F1/平衡准确率用于状态和奖励，不能直接支持 LAMDA 最终未来测试上的无标签强化学习。"
supports: [标签可用的漂移维护可以形成序贯决策, RL应与同动作集合固定规则比较]
cannot_support: [LAMDA上的RL效果, 无标签RL适应, 使用最终测试标签训练策略]
method: "冻结自监督编码器、潜在漂移统计、轻量适配器、PPO 成本感知维护控制器"
baseline: "Frozen-init、Head-Tune、Adapter-Tune、Joint-Tune、Periodic-Joint、Drift-Rule"
aliases:
  - Sabbah2026-SSL-RL
related:
  - "[[2026-Haque-LAMDA-Android恶意软件长期漂移基准]]"
---

# 自监督表示与强化学习漂移维护

> 页码锚点：标题位于 PDF 物理第 1 页；状态、动作与奖励见第 IV-F 节，结果见表 II，物理页码待 MinerU 输出修复后补。

## 证据与题录

- arXiv `2605.24294v1`，2026-05-22，当前为预印本。
- 本地 PDF SHA-256 `ce9f9f857872d9da76cfed3de93ff4949d7da1130f4347a4bc0d353ef8f74a27`。
- arXiv 官方 HTML 全文和 MinerU 路径均已核；MinerU 并发转换未生成该文件，故表号从官方 HTML 复核。
- Zotero：`DYVZDW5Z`，题录已导入，未自动附加 PDF。

## 方法

- 前 K 个时间窗拟合缩放器并自监督预训练编码器，之后冻结编码器。
- 每个新窗口计算相对上一窗和初始化参考的潜在漂移。
- PPO 从五个动作中选择：不更新、只调分类头、只调适配器、联合更新、重置适配器后联合更新。
- 状态包含当前评价子集的平衡准确率和宏 F1、记忆集准确率、漂移统计、上一动作、模型年龄和成本；奖励继续使用动作后的评价 F1/准确率、记忆保留与动作成本（第 IV-F 节式 9 后、奖励式）。

## 结果范围

- 在 real-dynamic 中，RL 的平均准确率约 0.628，但 Periodic-Joint(2) 的宏 F1 更高，约 0.473；作者把 RL 的价值定位为跨设置的成本折衷，而非每项指标最优（表 II）。
- 论文使用 2008–2020 的年度窗口、六个种子和每类分层的 2,000 样本训练/评价/记忆预算。
- 威胁有效性小节明确承认这是“标签可用维护”设置，不评估标签延迟或无反馈在线适应。

## 对 LAMDA 的强化学习资格门

该论文引用 LAMDA 作为大规模漂移证据，但没有在 LAMDA 上给出结果。若迁移到 LAMDA，至少必须满足：

- 状态在动作时真实可见，不能含最终测试标签计算的 F1/准确率。
- 奖励有合法延迟反馈或只在源期策略训练中计算；策略冻结后才进入最终未来年份。
- 动作确实改变后续状态与成本，且存在跨窗口长期权衡；否则普通规则、上下文 bandit 或直接超参选择更合适。
- 与同一动作集合的固定规则和成本匹配搜索比较；若 RL 只复现周期更新，应否决其必要性。

## 论文可以支持

- 标签可用的长期维护可形式化为状态、动作、收益和成本的序贯问题。

## 论文不能支持

- 不能支持在 LAMDA 最终未来年份上使用无标签 RL，也不能允许评价标签进入冻结策略。

## 实验结果与负证据

- RL 并非所有指标最优；其优势是跨设置成本折衷。论文明确不评估标签延迟和完全在线无反馈。

## 与本课题的关系

- 只在存在合法延迟回报、策略训练/最终测试隔离和非平凡长期动作影响时保留资格。

## Evidence Record

Evidence ID: `SABBAH-RL-E1`
Source: arXiv `2605.24294v1`
Source type: preprint | full paper
Supports: Android 漂移维护可以形式化为状态—动作—成本问题
Contradicts: “该方法已证明无标签 RL 在 LAMDA 最终未来测试有效”
Method / dataset / metric: PPO 维护；AUT、平衡准确率、宏 F1、记忆准确率、成本
Limitation: 标签即时可用；未在 LAMDA 实验；评价子集参与状态和奖励
Project relevance: RL 的条件资格和反泄漏门
Claim strength: observed

## 文献信息

- arXiv：https://arxiv.org/abs/2605.24294
