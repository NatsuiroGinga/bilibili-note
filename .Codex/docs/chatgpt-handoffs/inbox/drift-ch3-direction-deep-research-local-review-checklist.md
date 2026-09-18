# 第三章方向定点排重本地复核清单

日期：2026-09-08
输入：`drift-ch3-direction-deep-research-raw.md`
状态：只读整理；不重做检索，不修改 N12/N13/N14、G2、路线总控或恢复卡。

## 结论

旧网页报告新增六篇直接近邻。当前仓库未发现这六篇各自的独立 `raw/` 原件与规范化全文笔记，因此六篇均仍是**网页全文候选，待本地原件入库与逐页复核**。已在本地成对保存原件和笔记的 GradNorm、PCGrad、ForkMerge、MADCAT、SoTTA、MalMoE 与 DRIFT 可先作为复核锚点，但不能替代六篇新候选的原文。

## 六篇新增候选

| 候选与稳定标识 | 对当前候选的具体关系 | 网页报告给出的待核位置 | 本地状态与下一核验 |
| --- | --- | --- | --- |
| Feature-Critic Networks for Heterogeneous Domain Generalization；arXiv `1901.11448`；PMLR 97 | **N12 最近邻**：源域拆分为训练/留出环境，以有无辅助更新后的留出主任务收益作反馈。它压缩“留出环境反馈选择辅助更新”的新颖性；family 隔离能否外推仍待证。 | §§3.2-3.4，PDF pp.3-5，式(3)-(5)，算法1；另核异质目标任务是否使用目标训练标签。 | 未发现独立本地 PDF/全文笔记。下载作者稿后核公式、算法输入和异质实验协议。 |
| Auto-Lambda: Disentangling Dynamic Task Relationships；arXiv `2202.03091v2`；TMLR 2022 | **N12 最危险近邻**：主任务验证损失驱动单模型动态任务权重。若 PF-FAC 只是把验证目标换成 family-macro BCE，则可能只是任务化实例；独立良性硬约束是否不可被标量目标吸收是关键。 | §4，PDF pp.5-7，式(3)-(7)，`Swapping Training Data`；核训练/验证批次来源与双层近似。 | 未发现独立本地 PDF/全文笔记；仅其他本地论文参考文献出现题录。须本地入库并逐式核对。 |
| Test-Time Training with Self-Supervision for Generalization under Distribution Shifts；arXiv `1909.13231v3`；PMLR 119 | **N13 基础结构近邻**：冻结主任务分支、用自监督目标更新共享特征。它不证明 DGA 字符重构有益，也不能替代到达顺序和严格在线协议裁决。 | §2，PDF p.2，式(2)-(3)；p.3 的样本顺序；§4 的有益更新条件。 | 未发现独立本地 PDF/全文笔记。须核主任务参数冻结范围、批式/在线协议与顺序处理。 |
| Efficient Test-Time Model Adaptation without Forgetting；arXiv `2204.02610`；PMLR 162 | **N13 伤害控制近邻**：低熵/非冗余筛选、轻量参数更新和 Fisher 正则。保护原分布不等于满足良性风险与低误报护栏；其额外 ID 参考集资格必须核清。 | §4，PDF pp.4-5，式(2)-(9)，算法1；式(9)的 Fisher 数据来源；图区分动机排序与实际在线算法。 | 未发现独立本地 PDF/全文笔记。须核参考集、更新参数、筛样和评估信息范围。 |
| MORPH: Towards Automated Concept Drift Adaptation for Malware Detection；arXiv `2401.12790v1`；DOI `10.48550/arXiv.2401.12790` | **N13 恶意软件漂移近邻**：不对称伪标签筛选加原始带标签样本再训练。它不是纯重构自监督；低误报前提与年月协议是关键反例。 | §4，PDF pp.7-9，算法1 p.8，半监督损失 p.9，§5.1 p.10；核 2018 验证月与 2019-2021 叙述。 | 未发现独立本地 PDF/全文笔记；本地 MADCAT 等全文仅把它列为引用。须独立取得 MORPH 原文后再判断协议。 |
| META-DES: A dynamic ensemble selection framework using meta-learning；DOI `10.1016/j.patcog.2014.12.003`；作者稿 arXiv `1810.01270v1` | **N14 最近邻**：用历史带标签 DSEL 的局部元特征预测专家正确性，再做动态选择。它压缩“局部键预测专家可靠性”的新颖性；N14 仍须证明键预测净可救回收益，而非单专家难度。 | §3，PDF pp.9-16，算法1 p.12，§3.2.3 推断选择；核 DSEL 标签、元特征和共同错误边界。 | 未发现独立本地 PDF/全文笔记。须核 2015 正式题录与 2018 作者稿页序，不能把 arXiv 年当首次发表年。 |

## 已有本地全文锚点

- N12： [GradNorm 原件](../../../../raw/papers/methodology/auxiliary-learning/2018-Chen-GradNorm.pdf)、[GradNorm 笔记](../../../../wiki/papers/methodology/auxiliary-learning/2018-Chen-GradNorm梯度归一化.md)、[PCGrad 原件](../../../../raw/papers/methodology/auxiliary-learning/2020-Yu-PCGrad-Gradient-Surgery-MTL.pdf)、[PCGrad 笔记](../../../../wiki/papers/methodology/auxiliary-learning/2020-Yu-PCGrad梯度手术.md)、[ForkMerge 原件](../../../../raw/papers/methodology/auxiliary-learning/2023-Jiang-ForkMerge辅助任务负迁移.pdf)、[ForkMerge 全文笔记](../../../../wiki/papers/methodology/auxiliary-learning/2023-Jiang-ForkMerge辅助任务负迁移-全文.md)。
- N13： [MADCAT 原件](../../../../raw/papers/attack-detection/2025-Roh-MADCAT-TTA-Malware-Concept-Drift.pdf)、[MADCAT 全文](../../../../wiki/papers/attack-detection/2025-Roh-MADCAT-TTA-Malware-Concept-Drift-全文.md)、[SoTTA 原件](../../../../raw/papers/attack-detection/2023-Gong-SoTTA-Noisy-Streams.pdf)、[SoTTA 全文](../../../../wiki/papers/attack-detection/2023-Gong-SoTTA-Noisy-Streams-全文.md)。
- N14： [MalMoE 原件](../../../../raw/papers/attack-detection/encrypted/2026-Tan-MalMoE-Graph-Drift-MoE.pdf)、[MalMoE 全文](../../../../wiki/papers/attack-detection/encrypted/2026-Tan-MalMoE-Graph-Drift-MoE-全文.md)。
- 共同来源： [DRIFT 原件](../../../../raw/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.pdf)、[DRIFT 结构化全文](../../../../wiki/papers/datasets/2026-Lee-DRIFT-DGA-Temporal-Drift.md)。

## 最小核验顺序

1. N12 优先入库 Auto-Lambda，再入库 Feature-Critic；先核信息预算、验证目标、更新操作和是否单参数轨迹。该核验不阻塞也不改写当前 G2。
2. 若 N13 获用户协议批准，再入库 TTT、EATA、MORPH；重点核到达顺序、参考集、更新对象、标签使用和静态/适应分表。
3. 只有 N12 独立通过且 N14 重新获准时，再入库 META-DES；先核专家互补、DSEL 标签资格和净可救回收益。
4. 每篇取得本地 PDF 后用 PDF 工作流逐页核上表位置，建立 `raw/` 原件、`wiki/` 全文笔记和索引；网页报告不能直接升级为正文论断或候选存废依据。

## 明确不变

- N12 当前仍是 G1 仅准入 G2；本清单不评价正在运行的 G2。
- N13 仍需先裁决信息协议，当前不实现。
- N14 仍降权，不与 N12 同时实现，也不恢复 R02/R07 旧形式。
- 旧、新网页报告均是外部候选，待本地全文和实验复核。
