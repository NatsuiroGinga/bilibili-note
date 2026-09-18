# LAMDA 第三章候选方法源年筛选审查：资料库回收

**来源：** ChatGPT 资料库制品《LAMDA 第三章候选方法源年筛选审查：以“修复恶意漏判且不提高 FPR”为硬约束》；资料库显示大小 `538 KB`、时间 `15:25`。原始入口：[ChatGPT 资料库](https://chatgpt.com/library)。

**来源类型：** 网页深度研究审查报告，不是本项目运行制品。报告声明 `actual_model=GPT-5.5 Thinking`、`actual_effort=high / deep-research`、`actual_mode=Deep Research`、`used_apps=web.run`，代码执行为“未运行”。

## 1. 核心筛选结论

报告把第三章的首要问题定为：**修复恶意漏判，同时不提高 FPR**。它建议的候选优先级为：

1. 先完成缺口修复与条件安全门控的最小四臂；不在读出前新增 MIR、GSS、DGR、TERM、课程学习或主动学习 GPU 臂。
2. 若修复项有信号而安全边界不足，下一候选为 **双玩家 FPR／历史恶意速率约束**，即模型玩家负责修复，安全玩家负责更新速率约束乘子。
3. PCT／Focal Distillation 保留一个公开回归感知基线臂，不改名为创新机制。
4. MIR、GSS、TERM 只有在本地证据分别指向历史干扰、记忆代表性或风险加权瓶颈时才进入。
5. 课程学习、DGR 和当前固定标签合同下的主动学习直接臂停止；IWMS 只在另行冻结延迟标签协议时进入。

该排序是网页意见，必须与本地制品复核；不能替代 LAMDA 源年实验。

## 2. 与本地证据的对应

报告使用的本地历史证据包括：

- ER 开发期锚点：AP `0.987243`、FPR `0.013148`、FNR `0.059478`。
- 始终双风险投影：FPR `0.012232`、旧恶意负向翻转率 `0.031984`，但 FNR `0.070306`。
- 等单位风险损失：FPR `0.013148→0.089252`，不支持无约束风险倾斜。

本地最新 PCT 预筛已经另行分析：PCT、缺口修复及联合臂均未通过开发期门槛；网页报告中的“当前四臂进行中”属于生成时点的旧状态，不能覆盖本地最新收据。

## 3. 双玩家候选的理论边界

报告建议把目标写成数据依赖的速率约束，而不是任意损失加权：

\[
\min_\theta L_{base}(\theta)+\eta L_{repair}(\theta)
\quad\text{s.t.}\quad
g_B(\theta)\le 0,\;g_M(\theta)\le 0.
\]

其中 `g_B` 约束良性 FPR，`g_M` 约束旧恶意回归。Cotter／TFCO 的 proxy-Lagrangian 用可微代理供模型玩家更新，同时由约束玩家评估原始非光滑速率；不能把硬 FPR 直接送入 SGD 后声称获得 TFCO 保证。

报告还强调独立约束参考与最终 source-dev 评价应分离，避免约束过拟合。Kumar 等人的 ICO 把“固定 FPR 下最小化 FNR”列为典型目标，但其隐式阈值自由度不应改变本项目固定阈值合同。

## 4. 方法职责分离

| 方法 | 应承担的作用 | 不能替代 |
| --- | --- | --- |
| 缺口修复 | 修复当前已标注恶意中旧模型漏判者 | FPR 安全约束 |
| PCT／FD | 保护旧模型原来正确的决策 | 当前恶意漏判修复 |
| A-GEM／条件投影 | 修正当前步与参考梯度的局部冲突 | 跨步硬 FPR 保证 |
| TFCO／双玩家 | 维持长期速率约束预算 | 自动产生恶意修复信号 |
| MIR | 选择预计受当前更新干扰的历史样本 | 当前漏判恶意筛选 |
| GSS | 提高有限记忆的梯度方向覆盖 | FPR 约束 |
| TERM | 风险敏感重加权 | 约束可行性 |

## 5. 推荐门槛与信息集合

报告建议以 ER 开发锚点作为不可移动比较基准：

- FPR 候选不得高于 `0.013148`；
- FNR 应低于 `0.059478`；
- 旧恶意负向翻转率不得高于 `0.052107`；
- 不得用最终 source-dev 反复调约束，再把同一集合作为泛化证明；
- 不得使用 `2018--2025` 封印年标签、未来漂移统计或未来预处理状态。

双玩家的良性代理集合应来自此前已到达并确认的训练分片；独立良性 gate 只用于训练结束后的验收，不能进入参数或乘子更新。

## 6. 对本项目的裁决影响

- L11“双玩家安全约束回放”有充分的成熟方法依据，但仍是 `conditional_candidate`，尚未在 LAMDA 上验证。
- PCT 已完成本机预筛且被开发期门槛否决，保留为直接近邻基线，不再为它追加 CUDA 重训。
- 本地缺口修复和条件投影的失败并不等于双玩家方案已被否定；双玩家改变的是跨步速率预算，而不是简单叠加损失或每步投影。
- 在双玩家实现前，必须冻结 `G_t^0` 的训练来源、独立 gate、乘子更新规则、停止条件和完整指标；不能沿用历史阶段 C 的错误保护集合定义。

## 7. 文献与官方实现（报告列出的公开来源）

- LAMDA：IQSeC-Lab/LAMDA，按年份构造 Domain-IL experiences。
- Cotter 等，JMLR 2019，proxy-Lagrangian 非可微速率约束；官方 `tensorflow_constrained_optimization`。
- Cotter 等，ICML 2019，独立验证集上的数据依赖约束泛化。
- Kumar 等，ICML 2021，固定 FPR 下最小化 FNR 的速率约束优化。
- Yan 等，CVPR 2021，PCT／Focal Distillation。
- Chaudhry 等，ICLR 2019，A-GEM 条件冲突投影。
- Aljundi 等，NeurIPS 2019，MIR；GSS；TERM；IWMS；Chen 等 Android 主动学习工作。

## 8. 使用边界

这份回收记录只作为候选排序和实验设计依据。网页中的其他数据集数值、课程结果和主动学习结果不能写成 LAMDA 本地结果；最终方法是否有效仍由源年真实实验决定。

## 9. 参考文献入库状态

### 已有本地原件与结构化笔记

- LAMDA 原论文及 ICLR 2026 演示版。
- Cotter 等 JMLR 2019、ICML 2019；Kumar 等 ICML 2021。
- Yan 等 CVPR 2021 PCT；Ghiani 等 Android malware regression-aware 论文。
- Chaudhry 等 A-GEM；Aljundi 等 MIR、Wei 等 GSS；Chrysakis 等 CBRS；Amalapuram 等 ECBRS/PAPA。
- Chen 等 Android malware continual learning、Haque 等 CITADEL、Mohamed 等 MADAR、Asadi 等 FreeMOCA。

这些条目均可在 `raw/papers/` 找到原件，并在 `wiki/papers/attack-detection/` 或 `wiki/papers/datasets/` 找到结构化笔记；Cotter、Kumar、PCT 等还在本轮 PCT／双玩家计划中登记了公式位置和哈希。

### 资料库报告提到但当前未完整入库

- TERM：当前只有资料库报告中的题录和方法摘要，没有本地 TERM 原始 PDF／结构化笔记。
- IWMS（Label Delay in Online Continual Learning）：当前只有报告中的题录和方法摘要，没有本地原始 PDF／结构化笔记。
- DGR（Deep Generative Replay）：当前只有报告中的候选说明，没有本地原始 PDF／结构化笔记。

上述三类属于条件或后置候选，不影响当前双玩家源年筛选；在它们被提升为直接实验或正文证据前，必须先按 `raw/`→`wiki/` 流程补齐全文、版本、页码／公式和官方代码核验。
