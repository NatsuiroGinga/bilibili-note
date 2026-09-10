# RL 策略优化家族盘点与缺口入库 — 检查点笔记

任务目录：`.Codex/docs/2026-09-10-RL家族盘点/`
工作树：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908`
开始时间：2026-09-10

## 任务范围

GRPO 算法家族全谱系盘点：构建权威清单 → 逐个核验正式论文存在性 → 缺口下载 PDF + mineru extract 转换 + wiki 结构化笔记 + Zotero 入库 → 更新 INDEX 与家族全景表 → 写回 DRIFT 恢复卡。

## 候选线索源（只作线索，不作事实）

1. ChatGPT 交接 `grpo 算法家族.md`（ch3-lamda 工作树 inbox）
2. PPO/DPO/GRPO 综述 `__主题__：PPO、DPO、GRPO 及其变体策略优化算法综述*.md`
3. OpenRLHF README（`--algo.advantage.estimator` 实现清单）
4. 本地 `wiki/papers/grpo/GRPO变体群-方法选型.md`（17 条）

## 已有覆盖盘点（2026-09-10 首查）

### wiki/papers/grpo/ 已有 37 文件

**4 篇核心笔记（E3 全文级，带页码）**
- GRPO — 2402.03300（DeepSeekMath）
- DAPO — 2503.14476
- Dr. GRPO — 2503.20783
- GSPO — 2507.18071

**16/17 篇变体合并笔记 `GRPO变体群-方法选型.md`**（含作者勘误表）
| 编号 | 算法 | arXiv | 备注 |
|---|---|---|---|
| [1] | DeepSeekMath/GRPO | 2402.03300 | 同核心笔记 |
| [2] | ABC-GRPO | 2601.03895 | |
| [3] | NGRPO | 2509.18851 | |
| [4] | Dr. GRPO | 2503.20783 | 同核心笔记 |
| [5] | MMR-GRPO | 2601.09085 | |
| [6] | Pro-GRPO | 2512.15347 | |
| [7] | TA-GRPO | 2601.22478 | |
| [8] | Feng-RCS | 2504.13592 | 笔记在 wiki/papers/llm/ |
| [9] | Constrained GRPO | 2602.05863 | |
| [10] | CW-GRPO | 2605.11538 | |
| [11] | Scaf-GRPO | 2510.19807 | |
| [12] | SGPO | 2505.11595 | |
| [13] | S-GRPO | 2505.07686 | |
| [14] | GRPO-norm | 2601.23135 | |
| [15] | Pan 离线策略重解读 | 2509.24203 | |
| [16] | Learning Without Critics | 2511.03527 | |
| [17] | TIC-GRPO | 2508.02833 | |

**已知问题（本轮不修，登记）**：`2402.03300.md` / `2511.03527.md` / `2512.15347.md` / `2601.22478.md` 四个小文件（约 1.2 KB）是早期自动入库产物，frontmatter 的 `journal`/`year` 字段明显错误（如 `year: 1784096900.9771295`、`journal: Medicine & Science in Sports & Exercise`），`key_finding: 待补充`，属元数据垃圾；本目录 INDEX 已声明「完整度未经本轮核验」。

### raw/papers/grpo/ 已有 19 PDF
2402.03300、2503.20783、2504.13592v2(1)、2505.07686、2505.11595、2508.02833、2509.18851、2509.24203、2510.19807、2511.03527、2512.15347、2601.03895、2601.09085、2601.22478、2601.23135、2602.05863、2605.11538、2025-Yu-DAPO、2025-Zheng-GSPO-Group-Sequence-Policy-Optimization

## 待核验候选（本轮）

来自三份线索源合并、本地尚无笔记者：
VAPO、SRPO、GFPO、GTPO/GRPO-S、P-GRPO、LitePPO、GMPO、SAPO(2510.08625 已知)、
PPO、DPO、IPO、KTO、SimPO、REINFORCE++、REINFORCE++-baseline、RLOO。

### 已知矛盾点（需核验）

- **GSPO 名称撞车**：ChatGPT 交接把 GSPO 描述为 "Length-Normalized"（长度归一化），但本地 GSPO 笔记是 Qwen 的 **Group Sequence Policy Optimization**（序列级重要性比率，2507.18071）。两者机制不同，疑为同名不同物或线索源有误。
- **GMPO 机制矛盾**：两份二手来源对 GMPO 机制描述不一致（几何平均 vs 其他），必须回到原文核验。

## 核验结果（2026-09-10，arXiv API 直查 + WebSearch 交叉）

### 题录纠错（2 处，均须登记）

| 任务书原文 | 核验结果 | 处置 |
|---|---|---|
| "SAPO 已核验：arXiv:2510.08625，Hybrid Swap-Based，支持非可验证奖励" | **2510.08625 = 《Adjusting Initial Noise to Mitigate Memorization in Text-to-Image Diffusion Models》**（文生图扩散模型），与策略优化无关。且"Hybrid Swap-Based"在 arXiv 全文检索零命中 | **编号作废**。按题名重定为 **arXiv:2511.20347《Soft Adaptive Policy Optimization》**（Qwen Team），已入库 |
| GSPO 被交接材料描述为 "Length-Normalized" | 本地 GSPO 笔记是 Qwen 的 **Group Sequence Policy Optimization**（序列级重要性比率，2507.18071）。二者机制不同 | 判为**线索源表述错误**；2507.18071 已入库，无需新增 |

### 同名冲突（3 组，必须在索引中标注）

| 缩写 | 冲突项 | 处置 |
|---|---|---|
| **GTPO** | Tan 等 `2508.04349`《GTPO and GRPO-S: Token and Sequence-Level Reward Shaping with Policy Entropy》（Group Token Policy Optimization）vs Simoni 等 `2508.03772`《GTPO: Stabilizing GRPO via Gradient and Entropy Control》（Group-relative Trajectory-based Policy Optimization） | **两篇均入库**，索引标注必须带编号 |
| **SAPO** | `2511.20347` 软自适应（本文）／`2602.19345` 平滑门函数／`2603.10069` 搜索智能体一行代码／`2608.19842` 单 rollout 自回归／`2605.17648` 分步对齐推荐 | 只入 `2511.20347`；其余登记为同名近邻，未取全文 |
| **SRPO** | `2504.14286` 跨域大规模 RL（Kuaishou，本文）／`2506.01713` 多模态反思／`2511.15605` VLA 自指／`2608.23493` 自反思／`2609.08452` Setwise 多智能体 | 本地 `2505.07686` 参考文献列表明确引用 `2504.14286`（"Srpo: A cross-domain implementation of large-scale reinforcement learning on llm"），据此定为本课题所指 SRPO |

### 题录变更（1 处）

**P-GRPO / Posterior-GRPO（`2508.05170`）已改名**：《ReCode: Reinforcing Code Generation with Reasoning-Process Rewards》，算法改称 CG-GRPO。当前 PDF 正文 "Posterior" 零命中（逐页文本检索确认）。笔记中已登记。

### 已核验清单（arXiv API id_list 直查，2026-09-10）

`2511.20347` Soft Adaptive Policy Optimization（SAPO）·
`2507.20673` Geometric-Mean Policy Optimization（GMPO）·
`2508.09726` Sample More to Think Less（GFPO）·
`2508.08221` Part I: Tricks or Traps?（Lite PPO）·
`2504.05118` VAPO ·
`2508.04349` GTPO and GRPO-S（Tan）·
`2508.03772` GTPO（Simoni）·
`2508.05170` ReCode / P-GRPO ·
`2504.14286` SRPO ·
`2501.03262` REINFORCE++ ·
`2402.14740` Back to Basics（RLOO）·
`1707.06347` PPO ·
`2305.18290` DPO ·
`2310.12036` IPO ·
`2402.01306` KTO ·
`2405.14734` SimPO

## 已下载原件（13 个新 PDF，`raw/papers/grpo/`）

2017-Schulman-PPO-Proximal-Policy-Optimization.pdf ·
2023-Rafailov-DPO-Direct-Preference-Optimization.pdf ·
2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE-Style.pdf ·
2025-Fan-Posterior-GRPO-Rewarding-Reasoning-Processes.pdf ·
2025-Hu-REINFORCE-plus-plus-Global-Advantage-Normalization.pdf ·
2025-Liu-LitePPO-Tricks-or-Traps-RL-for-LLM-Reasoning.pdf ·
2025-Shrivastava-GFPO-Sample-More-to-Think-Less.pdf ·
2025-Simoni-GTPO-Gradient-and-Entropy-Control.pdf ·
2025-Soft-Adaptive-Policy-Optimization-SAPO.pdf ·
2025-Tan-GTPO-and-GRPO-S-Token-Sequence-Entropy.pdf ·
2025-Yue-VAPO-Efficient-and-Reliable-RL.pdf ·
2025-Zhang-SRPO-Cross-Domain-Large-Scale-RL.pdf ·
2025-Zhao-GMPO-Geometric-Mean-Policy-Optimization.pdf

转换：`mineru-open-api extract --list ... -o /tmp/grpo-md-continue/out/`，13/13 成功，57.7 s（token 模式，未用 flash-extract）。
页码锚点：`/tmp/grpo-md-continue/findpage.py`（`pypdf` 只读逐页检索，miniconda `rwkv` 环境）。

Zotero：`zotero_add_items_by_arxiv` 13 条全部导入成功并附 PDF，key 见各笔记「文献信息」节。

## 状态

- [x] 盘点现有覆盖
- [x] 合成总候选清单
- [x] arXiv 逐个核验（含 2 处纠错、3 组同名冲突、1 处题录变更）
- [x] 下载 13 个新 PDF
- [x] mineru extract 转换 13/13
- [x] Zotero 导入 13/13
- [x] wiki 结构化笔记 8/13（SAPO、GMPO、GFPO、LitePPO、VAPO、GTPO-Tan、GTPO-Simoni、P-GRPO）
- [ ] wiki 结构化笔记 5/13（SRPO、REINFORCE++、RLOO、PPO、DPO）
- [ ] INDEX / 全景表更新
- [ ] DRIFT 恢复卡写回
- [ ] git 提交

## 检索未获正式论文（登记，不猜）

见 `GRPO变体群-方法选型.md` 家族全景表「检索未获」栏。本轮范围内：
- "Hybrid Swap-Based SAPO"：全文与题名检索均零命中，判定为**线索源误记**，不作为算法登记。
