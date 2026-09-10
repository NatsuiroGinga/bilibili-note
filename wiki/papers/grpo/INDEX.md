---
title: GRPO 家族论文索引
date: 2026-09-10
tags:
  - GRPO
  - 强化学习
  - MOC
  - 类型/MOC
aliases:
  - GRPO 家族索引
  - GRPO 论文索引
related:
  - "[[GRPO变体群-方法选型]]"
  - "[[../../INDEX|wiki 总索引]]"
---

# GRPO 家族论文索引

本索引聚合 `wiki/papers/grpo/` 下的论文笔记。原件在 `raw/papers/grpo/`，`source_pdf` 字段逐篇指向原件。

> **2026-09-10 全谱系盘点**：本轮对家族做了全谱系核验（题录源：OpenRLHF README 的 `--algo.advantage.estimator` 实现清单、两份外部综述候选线索、本地既有 17 篇变体清单）。共核验 **32 个去重后的算法条目**（主干 4 ＋ 本轮新增家族成员 9 ＋ 本地既有变体 15 ＋ 根节点与家族外范式 4），新增入库 **13 篇全文级笔记**，纠错 **2 处编号/命名**，发现 **3 组同名冲突**。**无任何算法"检索未获"**——零命中项全部是缩写检索式或线索源误记，不是文献不存在。过程记录见 `.Codex/docs/2026-09-10-RL家族盘点/notes.md`。

## 家族全景表（2026-09-10）

状态口径：**已入库**＝本轮之前已有全文级笔记；**新增**＝本轮新下载原件＋新建全文级笔记；**变体笔记**＝收在 `GRPO变体群-方法选型.md` 的合并笔记内；**未入库**＝题录已核验但本轮未取全文。

### 根节点与家族外范式

| 算法 | 状态 | 一句话机制 | arXiv |
|---|---|---|---|
| PPO | **新增** | 裁剪代理目标替代 TRPO 的约束优化；actor-critic | `1707.06347` |
| DPO | **新增** | 用策略与参考策略的对数比作隐式奖励，偏好对齐化为分类问题，无 RL 循环 | `2305.18290` |
| REINFORCE++ | **新增** | 优势归一化从提示级搬到全局批次，对抗局部归一化的过拟合 | `2501.03262` |
| RLOO | **新增** | 同 prompt 其余样本作留一法基线；实测裁剪使用率 <5%，裁剪与部分完成建模均不必要 | `2402.14740` |

### GRPO 主干（四条互不重叠的修正线）

| 算法 | 状态 | 一句话机制 | arXiv |
|---|---|---|---|
| GRPO（DeepSeekMath） | 已入库 | 去 critic，组内奖励均值／标准差作相对优势 | `2402.03300` |
| DAPO | 已入库 | 修裁剪区间＋采样过滤＋损失归约：Clip-Higher／Dynamic Sampling／token 级损失／超长塑形 | `2503.14476` |
| Dr. GRPO | 已入库 | 修优势归一化：去长度偏置（`/|o_i|`）与难度偏置（组内 `std`） | `2503.20783` |
| GSPO | 已入库 | 修重要性比率粒度：序列级比率 `s_i=(π_θ/π_old)^{1/|y_i|}` 与序列级裁剪 | `2507.18071` |

### 本轮新增的家族成员（9 篇）

| 算法 | 状态 | 一句话机制 | arXiv |
|---|---|---|---|
| SAPO | **新增** | 用温度控制的 sigmoid 软门替代硬裁剪；正负优势不对称温度（1.0／1.05），兼得序列一致性与 token 自适应 | `2511.20347` |
| GMPO | **新增** | 把 token 级奖励的**算术平均**换成**几何平均**，抑制重要性比率的异常值 | `2507.20673` |
| GFPO | **新增** | 组内拒绝采样：按目标属性（长度／token 效率）保留 top-k，优势只在保留子集内算 | `2508.09726` |
| LitePPO | **新增** | 隔离评测全部技巧后只剩两项有效：组级均值＋批次级标准差、token 级损失聚合 | `2508.08221` |
| GTPO（Tan）／GRPO-S | **新增** | 动态熵加权：成功序列的高熵 token 奖励加成、失败序列的低熵 token 加重惩罚 | `2508.04349` |
| GTPO（Simoni） | **新增** | 冲突感知梯度修正（冲突 token 跳过负更新、正更新加倍）＋完成项熵过滤，去 KL | `2508.03772` |
| P-GRPO／ReCode | **新增** | 过程奖励被执行结果硬门控 `I(R_out=1)·R_proc`，防奖励破解并恢复全对组的学习信号 | `2508.05170` |
| VAPO | **新增** | 反其道保留价值模型：Value-Pretraining ＋ Decoupled-GAE ＋ Length-Adaptive GAE 等七项 | `2504.05118` |
| SRPO | **新增** | 两阶段跨域课程（先数学后代码）＋ epoch 级 History Resampling 剔除全对组 | `2504.14286` |

### 本地既有变体（合并笔记内，17 条）

ABC-GRPO `2601.03895` · NGRPO `2509.18851` · MMR-GRPO `2601.09085` · Pro-GRPO `2512.15347` · TA-GRPO `2601.22478` · Feng-RCS `2504.13592` · Constrained GRPO `2602.05863` · CW-GRPO `2605.11538` · Scaf-GRPO `2510.19807` · SGPO `2505.11595` · S-GRPO `2505.07686` · GRPO-norm `2601.23135` · Pan 离线策略重解读 `2509.24203` · Learning Without Critics `2511.03527` · TIC-GRPO `2508.02833` · DeepSeekMath `2402.03300` · Dr. GRPO `2503.20783`（详见 [[GRPO变体群-方法选型]]）

### 题录已核验、本轮未入库（家族外或同名近邻）

| 条目 | arXiv | 未入库理由 |
|---|---|---|
| IPO | `2310.12036` | DPO 变体，属离线偏好优化线，不在本轮 GRPO 家族范围 |
| KTO | `2402.01306` | 同上 |
| SimPO | `2405.14734` | 同上 |
| VAPO 理论分析 | `2505.17997` | 对 VAPO 的独立理论分析，非家族成员 |
| SAPO 同名近邻 | `2602.19345`／`2603.10069`／`2608.19842`／`2605.17648` | 四个不同的 SAPO，非本课题语境所指 |
| SRPO 同名近邻 | `2506.01713`／`2511.15605`／`2608.23493`／`2609.08452` | 四个不同的 SRPO |

## 题录纠错与同名冲突（强制登记）

### 编号／命名纠错（2 处）

1. **SAPO 的编号**：外部线索给的 `2510.08625` 经 arXiv API 直查为《Adjusting Initial Noise to Mitigate Memorization in Text-to-Image Diffusion Models》（文生图扩散模型），**与策略优化无关，该编号作废**。按题名重定为 **`2511.20347`《Soft Adaptive Policy Optimization》**（Qwen Team）。线索中的"Hybrid Swap-Based"在 arXiv 全文与题名检索中**均零命中**，判定为线索源误记。
2. **GSPO 的描述**：外部线索把 GSPO 描述为 "Length-Normalized"，但本目录 GSPO 笔记（`2507.18071`）是 Qwen 的 **Group Sequence Policy Optimization**（序列级重要性比率）。判为**线索源表述错误**，非独立算法。

### 同名冲突（3 组，引用必须带编号）

| 缩写 | 冲突项 | 处置 |
|---|---|---|
| **GTPO** | `2508.04349`（Tan 等，Group **Token** Policy Optimization，熵加权）vs `2508.03772`（Simoni 等，Group-relative **Trajectory**-based Policy Optimization，梯度与熵控制） | 两篇**均已入库**，分别见 [[2025-Tan-GTPO与GRPO-S熵加权]]、[[2025-Simoni-GTPO梯度与熵控制]]；不带编号的 "GTPO" 无法区分 |
| **SAPO** | `2511.20347`（本文）／`2602.19345`／`2603.10069`／`2608.19842`／`2605.17648` | 只入 `2511.20347` |
| **SRPO** | `2504.14286`（本文）／`2506.01713`／`2511.15605`／`2608.23493`／`2609.08452` | 只入 `2504.14286` |

### 检索未获正式论文（登记，不猜）

| 检索对象 | 检索式 | 结果 |
|---|---|---|
| "Hybrid Swap-Based SAPO" | arXiv `all:` 全文与 `ti:` 题名双路 + WebSearch | **零命中**；判定为线索源误记，不作为算法登记 |
| `LitePPO` | `ti:"LitePPO"` | 零命中；正式题名为《Part I: Tricks or Traps? A Deep Dive into RL for LLM Reasoning》 |
| `GMPO` | `ti:"GMPO"` | 零命中；正式题名为《Geometric-Mean Policy Optimization》 |
| `P-GRPO` / `Posterior-GRPO` | `ti:"P-GRPO"`、`all:"Posterior-GRPO"` | 题名零命中；该文 v1 题名 Posterior-GRPO，**最新版已改名《ReCode: Reinforcing Code Generation with Reasoning-Process Rewards》**，算法改称 CG-GRPO（当前 PDF 正文 "Posterior" 零命中，已逐页确认） |

**检索日期**：2026-09-10。**检索工具**：arXiv API（`export.arxiv.org/api/query`）、WebSearch。后续如另有编号线索，须先回 arXiv API 核验再入库。

## 家族原文（2026-09-10 入库，E3 全文级）

四篇共同构成本课题用到的 GRPO 谱系：**GRPO 原文 → 三条互不重叠的修正线**。引用「GRPO 有偏/不稳」时必须指明是哪一条修正，不得合并成笼统结论。

- **[[2024-Shao-DeepSeekMath与GRPO开山|DeepSeekMath：GRPO 的首次提出（arXiv:2402.03300）]]** — 去掉 PPO 的价值模型，改用组内奖励均值作基线，KL 写成损失项而非奖励整形（式(3)，p.13）；优势的两种实例化：结果监督（§4.1.2，p.14）与过程监督（§4.1.3，p.14）。另给出统一范式（数据来源×奖励函数×梯度系数，表 10，p.19）与 **RL 提升 Maj@K 但不提升 Pass@K** 的诊断结论（图 7，p.21）。
- **[[2025-Yu-DAPO解耦裁剪与动态采样|DAPO：解耦裁剪与动态采样（arXiv:2503.14476）]]** — 修的是**裁剪区间、采样过滤与损失归约**：Clip-Higher（ε_low=0.2, ε_high=0.28）、Dynamic Sampling（滤掉全对/全错组）、Token-Level Policy Gradient Loss、Overlong Reward Shaping（式(10)–(13)，p.5–7）；逐项记账 30→50（表 1，p.9）。
- **[[2025-Liu-DrGRPO无偏优化与R1-Zero再审视|Dr. GRPO：无偏优化与 R1-Zero 再审视（arXiv:2503.20783）]]** — 修的是**优势归一化**：除以 `|o_i|` 造成响应级长度偏置、除以组内 `std(R)` 造成问题级难度偏置（§3.1，p.6）；并指出多个开源 PPO 实现按响应长度归一化损失、与公式不符（表 2，p.7）。**题录注意**：正确编号 2503.20783，非 2503.20796。
- **[[2025-Zheng-GSPO序列级重要性比率|GSPO：序列级重要性比率（arXiv:2507.18071）]]** — 修的是**重要性比率的计算粒度**：`s_i(θ)=(π_θ(y_i|x)/π_θold(y_i|x))^{1/|y_i|}` 与序列级裁剪（式(5)–(7)，p.3）；论证 GRPO 的 token 级权重在 N=1 的样本上不是分布校正而是噪声注入，导致不可逆坍塌（§3，p.2–3）。

## 本轮新增笔记（13 篇，2026-09-10，E3 全文级）

全部已下载原件、MinerU `extract` 模式转换、逐页核对页码锚点、导入 Zotero。

### GRPO 家族变体（9 篇）

- **[[2025-Gao-SAPO软自适应门控|SAPO：软自适应门控替代硬裁剪（arXiv:2511.20347）]]** — 软门式(6)、梯度式(7)(8)（p.3）；统一门控视角下与 GRPO／GSPO 的等价与差异（式(10)–(15)，p.4–6）；正负不对称温度由负向梯度的词表扩散论证（式(9)，p.3–4）。
- **[[2025-Zhao-GMPO几何平均策略优化|GMPO：几何平均抑制 token 级异常值（arXiv:2507.20673）]]** — 只换聚合算子（式(3)(4)，p.3）；权重来源粒度分析（p.4）；R1-Distill-7B 平均 Pass@1 63.4 vs 59.3（表 1，p.5）。
- **[[2025-Shrivastava-GFPO组过滤策略优化|GFPO：组内过滤 + 过滤优势（arXiv:2508.09726）]]** — 过滤优势式(2)（p.3–4）；长度膨胀削减 46–71%／71–85%（摘要）；自适应难度 GFPO（算法 2，p.4）。
- **[[2025-Liu-LitePPO极简组合|Lite PPO：技巧隔离评测后的最小组合（arXiv:2508.08221）]]** — 三条 Takeaway：去 std（p.4–6）、组级均值+批次级 std（p.7）、token 级损失；Lite PPO 定义见 §5（p.11–12）。
- **[[2025-Tan-GTPO与GRPO-S熵加权|GTPO/GRPO-S：动态熵加权（arXiv:2508.04349）]]** — 细粒度信用分配（§2.1，p.2）；正奖励质量守恒命题 2.2、渐近无偏命题 2.3、与 DAPO 同全局最优定理 2.4（p.5）。
- **[[2025-Simoni-GTPO梯度与熵控制|GTPO：梯度与熵控制（arXiv:2508.03772）]]** — 冲突掩码 `λ∈{0,1,2}`（式(9)，p.4）与总信号守恒；完成项熵过滤（式(10)）与熵正则（式(11)）（p.5）。
- **[[2025-Fan-Posterior-GRPO一致性门控|Posterior-GRPO/ReCode：一致性门控（arXiv:2508.05170）]]** — 门控奖励式(1)（p.3）；CRPL 与 LCB-RB 基准（§2.1、§3）；7B 相对基座 +16.1%／相对 outcome-only +4.5%（§5）。
- **[[2025-Yue-VAPO价值模型增强PPO|VAPO：保留价值模型的长 CoT RL（arXiv:2504.05118）]]** — 七项技术表与消融落差（表 1，p.6）；Length-Adaptive GAE 的 `0.95^100≈0.006` 论证（p.3）。
- **[[2025-Zhang-SRPO跨域大规模RL|SRPO：两阶段课程 + 历史重采样（arXiv:2504.14286）]]** — 近 50% 组零优势（图 8）与 epoch 级重建规则（§3.3，p.7）。

### 根节点与家族外范式（4 篇）

- **[[2017-Schulman-PPO裁剪代理目标|PPO：裁剪代理目标（arXiv:1707.06347）]]** — 式(7)（p.3）与 `min` 的不对称性；自适应 KL 替代（式(8)，p.4）；多轮 minibatch 更新是 off-policy 比率的来源（Algorithm 1，p.5）。
- **[[2023-Rafailov-DPO直接偏好优化|DPO：直接偏好优化（arXiv:2305.18290）]]** — 推导链式(4)–(7)（p.4）；隐式奖励与 actor-critic 不稳定性论证（§5.1–5.2，p.6）。
- **[[2025-Hu-REINFORCE-plus-plus全局优势归一化|REINFORCE++：全局优势归一化（arXiv:2501.03262）]]** — 式(4)(5)（p.3）；30 题过拟合对照（GRPO 训练 95.0／OOD 0.0 vs REINFORCE++ 71.0／2.5，§4.2.1，p.5–6）。
- **[[2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE风格|RLOO：Back to Basics（arXiv:2402.14740）]]** — RLOO 估计量（§2.3，p.5）；裁剪使用率 <5%（§3.2，p.8）；bandit 归约论证（§3.3，p.8）。

## 课题汇总笔记

- **[[GRPO变体群-方法选型]]** — 本地 17 篇变体的合并笔记，按「训练稳定／采样课程／多目标约束／过程监督／推理效率／理论」六条线整理，是开题创新点 2 的方法选型池（含作者勘误表与**本轮新增的题录纠错表**）。

## 本目录其余笔记

其余按 `arXiv 编号` 命名的单篇笔记与早期自动入库产物（如 `2402.03300.md`、`2511.03527.md`、`2512.15347.md`、`2601.22478.md` 四个约 1.2 KB 的文件）**元数据明显错误**（`year` 字段为浮点时间戳、`journal` 为无关期刊、`key_finding: 待补充`），**引用前须核对原文与页码，不得直接采信其 frontmatter**。

## 代码实现参考（2026-09-10 登记）

> **用途声明**：本节是**实现参考池**，不是论文证据。本课题若任务化某个家族机制，**优先参考其官方实现**的默认超参与工程 trick；**引用边界照旧**——机制思想可用，**算法名不得冒充本课题创新**（PIC-GRPO 的命名与差异化句仍按 [[GRPO变体群-方法选型]] 的定稿执行，不得因参考了某家族实现就声称该算法是本课题贡献）。登记内容以**访问当日仓库现状**为准，日后不保证一致；许可证以仓库声明为准，**未声明许可证者不得直接复用其代码**。

**访问日期：2026-09-10。**

### 主参考：OpenRLHF

仓库 <https://github.com/OpenRLHF/OpenRLHF> · 许可证 **Apache-2.0** · `main` 分支 HEAD `ebc9e245b8c859ba52cbacc8b2e48fb024b64cb7`（pushed `2026-09-10T07:40:06Z`）。README 的 "State-of-the-Art RL Algorithms" 表列出 **PPO／REINFORCE++／REINFORCE++-baseline／RLOO／GRPO／Dr. GRPO** 六档，GSPO 与 DAPO 以损失类型与开关形式支持。

| 算法 | CLI 档位／开关 | 实现位置（main 分支，行号为 2026-09-10 快照） |
|---|---|---|
| PPO | `--algo.advantage.estimator` 默认（`gae`） | `openrlhf/trainer/ppo_utils/experience_maker.py` L292（优势分派）；`openrlhf/models/loss.py` L116 `class PolicyLoss`（默认 `policy_loss_type="ppo"`，`clip_eps_low/high=0.2`） |
| REINFORCE++ | `--algo.advantage.estimator reinforce` | `experience_maker.py` L292 |
| REINFORCE++-baseline | `--algo.advantage.estimator reinforce_baseline` | `experience_maker.py` L267 |
| RLOO | `--algo.advantage.estimator rloo` | `experience_maker.py` L264 |
| GRPO | `--algo.advantage.estimator group_norm` | `experience_maker.py` L269 |
| Dr. GRPO | `--algo.advantage.estimator dr_grpo`（README 注"Removes local `/std` norm"） | `experience_maker.py` L267（与 `reinforce_baseline` 同分支） |
| GSPO | `--actor.policy_loss_type gspo`（`choices=["ppo","gspo"]`，默认 `ppo`） | CLI：`openrlhf/cli/train_ppo_ray.py` L420；实现：`openrlhf/models/loss.py` **L170–171**（源码注释直接引 `https://arxiv.org/pdf/2507.18071`，即本目录 GSPO 原文）；GSPO 要求序列级损失见 `loss.py` L142 |
| DAPO | `--algo.dynamic_filtering_enable`（动态过滤）；`--reward.overlong_buffer_len`／`--reward.overlong_penalty_factor`（超长软惩罚） | `openrlhf/trainer/ppo_utils/length_penalty.py` L16 `apply_overlong_penalty`（文件头注明 "DAPO Overlong Penalty"）；示例 `examples/scripts/train_dapo_ray_hybrid_engine.sh` |
| DPO | `openrlhf/cli/train_dpo.py` | `openrlhf/trainer/dpo_trainer.py`；`openrlhf/models/loss.py` L300 `class DPOLoss` |

**参数命名约定**：该仓库用嵌套命名 `--algo.*`（算法层）、`--actor.*`（策略层）、`--reward.*`（奖励层）。核验方式：逐文件 `curl` raw 内容后 `rg` 定位，非凭记忆。

### 其它家族成员的官方实现

| 家族成员 | 官方（或所属框架）实现 | 许可证 | 来源与核验 |
|---|---|---|---|
| **SAPO** `2511.20347` | **ms-swift** `--loss_type sapo` | Apache-2.0 | **论文正文无仓库链接**。ms-swift 实现：`swift/rlhf_trainers/grpo_trainer.py` **L1045**（`elif self.loss_type == 'sapo':`）、L1088；示例 `examples/train/grpo/internal/sapo.sh`、`examples/megatron/grpo/sapo.sh`；文档 `docs/source_en/Instruction/GRPO/AdvancedResearch/SAPO.md`（2026-09-10 直接核验） |
| **Dr. GRPO** `2503.20783` | `sail-sg/oat` | Apache-2.0 | 论文参考文献列表给出 `github.com/sail-sg/oat`（本地全文 `2503.20783-全文.md` 第 255 行）；另有 `sail-sg/understand-r1-zero`（MIT，1275 stars）仓库存在，但**本轮未从论文正文核到该链接**，故不登记为官方 |
| **GSPO** `2507.18071` | OpenRLHF `--actor.policy_loss_type gspo` | Apache-2.0 | 见上主表；论文原文本轮未检索到作者自带仓库链接 |
| **DAPO** `2503.14476` | `verl`（原 `volcengine/verl`，现 **`verl-project/verl`**） | Apache-2.0 | 论文正文给出 `https://github.com/volcengine/verl`；仓库已迁移改名（2026-09-10 核验重定向）；DAPO 说明 `docs/algo/dapo.md`，优势与策略损失实现 `verl/trainer/ppo/core_algos.py` |
| **GMPO** `2507.20673` | `callsys/GMPO` | **无许可证声明** | 论文正文 p.1 直接给出该链接；105 stars（2026-09-10 核验） |
| **LitePPO** `2508.08221` | **alibaba/ROLL** | Apache-2.0 | 论文正文给出 `https://github.com/alibaba/ROLL`；算法文档 `docs_roll/docs/User Guides/Algorithms/LitePPO.md`（2026-09-10 核验存在）；**具体实现文件本轮未定位** |
| **GTPO**（Simoni）`2508.03772` | `winstonsmith1897/GTPO` | **无许可证声明** | 论文正文脚注给出；42 stars（2026-09-10 核验） |
| **P-GRPO／ReCode** `2508.05170` | `ZJU-CTAG/ReCode` | **无许可证声明** | 论文正文脚注给出；0 stars（2026-09-10 核验） |
| **SRPO** `2504.14286` | 模型权重 `huggingface.co/Kwaipilot/SRPO-Qwen-32B` | 未核 | 论文正文给出；**训练代码未见提供** |
| 通用基座（PPO／RLOO／DPO／GRPO） | `huggingface/trl` | Apache-2.0 | GFPO 论文自述以 TRL 为训练框架；**TRL 自身的算法清单本轮未逐项核验** |

### 未获公开官方实现（登记，不猜）

以下条目的**判定依据**统一为：对论文 PDF 做逐页 `pypdf` 文本抽取后，检索 `github.com`／`huggingface.co`／`hf.co` 链接（2026-09-10）。

| 家族成员 | 结论 | 备注 |
|---|---|---|
| **VAPO** `2504.05118` | **无公开官方实现**（论文无代码或权重链接） | 逐页检索零命中 |
| **GFPO** `2508.09726` | **无公开官方实现**（论文仅引用 TRL 为训练框架与 AIME 数据集链接） | 逐页检索仅命中 TRL 与 HuggingFace datasets |
| **SAPO** `2511.20347` | **论文未提供官方仓库**；可用实现见 ms-swift（上表） | 逐页检索零命中 |
| **GTPO／GRPO-S**（Tan）`2508.04349` | **无公开官方实现** | 逐页检索仅命中一篇 HuggingFace 博客（非本方法实现） |
| **PPO** `1707.06347` | 原论文（2017）无代码链接；现代实现见 OpenRLHF／verl／TRL | — |
| **RLOO** `2402.14740` | 论文无独立仓库；实现见 OpenRLHF `rloo` 与 TRL | — |
| **DPO** `2305.18290` | 论文无代码链接；实现见 OpenRLHF `train_dpo.py` 与 TRL | 逐页检索仅命中无关链接 |

**许可证风险提示（强制）**：`callsys/GMPO`、`winstonsmith1897/GTPO`、`ZJU-CTAG/ReCode` 三个仓库**未声明许可证**。按本仓库安全与合规边界，**不得直接把其代码复制进本课题代码库**；如需复用，只能参考其**方法描述**并自行实现，或先与作者确认许可。

## 引用纪律（本轮盘点后新增）

1. **引用「GRPO 不稳、有偏」必须指明修正线**：裁剪区间（DAPO）、归一化（Dr. GRPO）、比率粒度（GSPO）、聚合算子（GMPO）、裁剪算子（SAPO）五条互不重叠。
2. **同名缩写必须带 arXiv 编号**：GTPO（`2508.04349` vs `2508.03772`）、SAPO、SRPO 三组。
3. **题名变更须指版本**：`2508.05170` 的 v1（P-GRPO）与最新版（ReCode／CG-GRPO）题名不同。
4. **单篇结论不得跨模型族外推**：LitePPO 明确限定只用 Qwen3 系列（§6）；GMPO、GSPO、SAPO 的实验均为 LLM 推理任务，**均无表格数据或分类任务证据**。
5. **增益数字必须带参照系**：ReCode 的 `16.1%` 相对基座、`4.5%` 相对 outcome-only RL，混用即失真；GMPO 的 `+4.1` 是最优情形非全域结论。
