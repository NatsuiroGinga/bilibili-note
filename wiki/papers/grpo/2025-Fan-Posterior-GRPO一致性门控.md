---
title: "Posterior-GRPO / ReCode: Rewarding Reasoning Processes in Code Generation"
authors: [Lishui Fan, Yu Zhang, Mouxiang Chen, Zhongxin Liu]
year: 2025
date: 2026-09-10
journal: "arXiv:2508.05170（2025-08-07 首版，v1 题名 Posterior-GRPO；最新版改名 ReCode: Reinforcing Code Generation with Reasoning-Process Rewards，19 页，浙江大学）"
source_pdf: "[[raw/papers/grpo/2025-Fan-Posterior-GRPO-Rewarding-Reasoning-Processes.pdf]]"
tags:
  - GRPO
  - 强化学习
  - 代码生成
  - 过程奖励模型
  - 奖励破解防护
  - 门控
  - 类型/论文
key_finding: "把**过程奖励**接进 RL 时会被策略破解——模型学会抬高过程分而不提升正确性。本文的对策是把神经过程奖励**用执行结果硬门控**：`R_i = R_fmt^((i)) + R_out^((i)) + I(R_out^((i))=1)·R_proc^((i))`（§2.2，p.3），即过程奖励只在最终代码**通过全部测试用例**时才激活。副产品：标准 GRPO 在一组样本全对时优势为零，而门控项在功能正确的解之间**因推理质量差异引入非零方差**，恢复了学习信号（p.3）。配套的 **CRPL** 用合成"优化／退化"推理变体训练过程奖励模型，并新建 **LCB-RB** 基准评测其判别力（§2.1、§3）。7B 模型在 HumanEval(+)、MBPP(+)、LiveCodeBench、BigCodeBench 上比基座提升 **16.1%**，达到 GPT-4-Turbo 同级；并扩展到数学域。"
method: "ReCode = CRPL（对比式推理过程奖励学习）＋ CG-GRPO（Consistency-Gated GRPO，式(1)，p.3）；优势与裁剪沿用 GRPO，KL 项替换为 clip-higher 策略"
baseline: "基座 Qwen2.5-Coder-7B-Instruct；outcome-only RL（只有结果奖励的 RL）为直接对照，比其平均高 4.5%（摘要、§5）"
aliases:
  - P-GRPO
  - Posterior-GRPO
  - ReCode
  - CG-GRPO
  - Fan2025-PosteriorGRPO
related:
  - "[[2024-Shao-DeepSeekMath与GRPO开山]]"
  - "[[2025-Yu-DAPO解耦裁剪与动态采样]]"
  - "[[2025-Shrivastava-GFPO组过滤策略优化]]"
  - "[[GRPO变体群-方法选型]]"
---

# Posterior-GRPO / ReCode：用执行结果门控过程奖励

> Lishui Fan 等（浙江大学），2025，arXiv:2508.05170 · 19 页 · 原件 `raw/papers/grpo/2025-Fan-Posterior-GRPO-Rewarding-Reasoning-Processes.pdf`

## 证据等级

**E3 全文级**。原件已下载（arXiv 2508.05170，1.5 MB，19 页），正文逐节读完；公式经 MinerU `extract` 模式转 LaTeX 后回原文页核对，页码锚点用逐页文本索引确认（`pypdf` 只读检索，2026-09-10）。

**题录变更警示（必须记录）**：该论文 v1 题名为《Posterior-GRPO: Rewarding Reasoning Processes in Code Generation》，算法称 **P-GRPO**；**最新版本已改名为《ReCode: Reinforcing Code Generation with Reasoning-Process Rewards》**，算法改称 **CG-GRPO（Consistency-Gated GRPO）**。经逐页文本检索确认：当前 PDF 正文中 **"Posterior" 零命中**。因此：
- 按 "P-GRPO" 或 "Posterior-GRPO" 检索到的题名与当前 arXiv 元数据不一致，**属同一篇**；
- 引用时应使用**当前**题名与算法名（ReCode／CG-GRPO），或注明"v1 曾用名 Posterior-GRPO／P-GRPO"。

## 一句话

过程奖励单独用会被策略破解，把它挂在一个**不可破解的硬门**（代码真的跑通了）后面，就能既拿到过程信号又不牺牲正确性。

## 机制（§2，p.2–4）

### 奖励结构（§2.2，式(1)，p.3）

回答被显式拆为推理过程 `t`（`<think>` 块内）与解 `o`（`<answer>` 块内），`y = (t, o)`。

`R_i = R_fmt^((i)) + R_out^((i)) + I(R_out^((i)) = 1)·R_proc^((i))` …(1)

| 项 | 定义 | 位置 |
|---|---|---|
| `R_fmt` | 结构合规二值奖励（`<think>`／`<answer>` 标签用对） | §2.2，p.3 |
| `R_out` | 严格二值：解通过全部测试用例为 1，否则 0 | §2.2，p.3 |
| `R_proc` | CRPL 训练出的奖励模型 `s_θ` 给出的连续分 `r ∈ [0,1]` | §2.1、§2.2 |

作者明确指出：线性相加（`R = R_fmt + R_out + R_proc`）会让策略抬高过程分而不改善正确性；门控使**正确性成为硬约束**（p.3）。

### 门控的第二个作用：恢复全对组的学习信号（p.3）

标准 GRPO 下若一组 G 个样本全对，`R_out` 全为 1、奖励无方差、优势为零。而门控项 `I(R_out=1)·R_proc` 在功能正确的解之间**引入了因推理质量而异的非零方差**，使这些组重新产生梯度。这与 [[2025-Shrivastava-GFPO组过滤策略优化]] 的"保留子集内算优势"是同一类思想。

### CRPL：过程奖励模型的训练（§2.1，p.2–3）

沿"事实准确性、逻辑严谨性、连贯性"等维度系统性地**优化与退化**推理路径，构造高质量偏好对，再训练奖励模型；避免手工标注细粒度偏好数据的瓶颈。

### 基准：LCB-RB（§3，p.4）

从 **880** 个 LiveCodeBench v5 问题构造偏好对（**187 对**），用 GPT-4o 作外部校验器过滤，评测奖励模型对推理过程优劣的判别力。

## 实验结果（§5，p.5–6）

| 项 | 内容 | 位置 |
|---|---|---|
| 通用提升 | 7B 模型比基座提升 **16.1%**，达到 GPT-4-Turbo 同级 | 摘要、§5.1 |
| 对 outcome-only RL | 平均高 **4.5%** | 摘要 |
| LiveCodeBench | 50.4% → **57.4%**（相对 outcome-only 基线 18.1%） | §5.1 |
| 数学域外推 | Qwen2.5-Math-7B 上比 outcome-only 相对提升 **7.3%** | §5.3 |
| 基准 | HumanEval(+)、MBPP(+)、LiveCodeBench、BigCodeBench | §5.1 |

**必须随结论一起转述的作者限定**：`β=0.5`（过程奖励权重，§摘要相关段）、KL 惩罚被替换为 clip-higher 策略（§2.2）；全部实验为 **7B 级代码／数学模型**，**没有检测、分类或表格数据任务**。`16.1%` 是**相对基座**的提升，不是相对 outcome-only 基线（后者是 `+4.5%`）——两个数字不可混用。

## 可迁移机制

1. **"可验证信号做硬门、神经信号做细粒度区分"**（式(1)，p.3）：把不可靠的神经网络奖励放在可靠信号的**下游**而不是与之**并列相加**。这是本目录内**对"部分可验证／部分不可验证"混合奖励最直接可迁移的构造**——本课题若同时有"可程序核验的标签／规则"与"不可核验的物理自洽评分"，可直接采用该门控形式，避免神经评分主导优化。
2. **门控同时解决"零优势组"**（p.3）：当一组样本在硬信号上全对时，神经信号接管提供方差。这与 DAPO 的 Dynamic Sampling（直接丢弃全对组）形成对照：**一个是丢弃，一个是榨取**。
3. **用合成变体训练奖励模型**（§2.1，p.2）：沿指定维度做"优化／退化"生成偏好对，绕开人工标注瓶颈。**本课题若需要"证据链质量"评分器，可复用该构造**：对同一样本生成更完整／更残缺的证据链，构成偏好对。
4. **搭配专用基准验证判别力**（§3，p.4）：不直接信奖励模型的分数，而是先建一个"能区分优劣过程"的评测集。**引入任何神经评分器前应先做这一步**。

## 不能直接声称内容

- **不能按 v1 题名／算法名引用而不加说明**：当前版本已改名 ReCode／CG-GRPO；同一 arXiv 编号下 v1 与最新版题名不同，引用须指版本。
- **不能把 `16.1%` 与 `+4.5%` 混用**：前者相对基座、后者相对 outcome-only RL，参照系不同。
- **不能把门控写成"提升正确性"**：门控的作用是**防止过程奖励损害正确性**并恢复全对组的学习信号；正确性提升来自 outcome 奖励本身。
- **不能声称该方法支持完全不可验证的奖励**：门控项 `I(R_out=1)` 恰恰**要求存在一个可验证的硬信号**（测试用例通过与否）。本文**没有**解决"硬信号完全不存在"的情形。
- **不能把代码／数学域的结论外推到序列标注或分类**：任务结构（离散可执行输出）是门控成立的关键前提。
- **不能把 LCB-RB 的规模当作通用基准**：它只有 187 对偏好数据、源自 880 个 LiveCodeBench 问题（§3），是**为本文场景定制**的判别力测试。

## 与课题的关系

- **对本课题的"无标签适应"最需要警惕的一篇**：DRIFT 第三章的 N13 方向（测试时适应）恰好是**无标签**场景，而本文的门控**要求一个可验证硬信号**。因此本文不能作为无标签场景的方法依据，只能作为"存在部分可验证信号时"的构造参考。
- 与 [[2025-Gao-SAPO软自适应门控]] 的分工：SAPO 处理**没有可验证奖励**时的更新规则（门函数只读重要性比率），ReCode 处理**有可验证硬信号 + 有神经评分**时的奖励组合。两者互补而非替代。

## 疑问 / 待验证

- 论文未报告：训练算力、种子与方差、奖励模型的规模对结论的敏感性。
- CRPL 构造的"退化"推理变体由谁生成（GPT-4o？），该生成器本身的偏差是否会传递到奖励模型，论文未讨论。
- 门控项在**硬信号稀疏**（通过率极低）时是否仍有足够梯度，论文的实验任务通过率较高，未覆盖该情形。

## 文献信息

- arXiv:2508.05170（2025-08-07 提交；v1 题名 Posterior-GRPO，最新版题名 ReCode）· 浙江大学区块链与数据安全全国重点实验室 · 4 位作者
- 题录核验：arXiv API 直查 `id_list=2508.05170` 返回当前题名《ReCode: Reinforcing Code Generation with Reasoning-Process Rewards》、作者、日期（2026-09-10 核验）；Zotero key `78VJPJI4`
- 原件：`raw/papers/grpo/2025-Fan-Posterior-GRPO-Rewarding-Reasoning-Processes.pdf`
