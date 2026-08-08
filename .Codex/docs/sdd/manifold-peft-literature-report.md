# 流形约束与参数高效微调文献核验报告

## 执行结论

- 本轮结构化筛选 14 个候选条目，完整纳入并逐页核验 6 篇，排除或延期 8 篇。
- 纳入文献覆盖两条证据链：Stiefel/正交低秩适配 3 篇，mHC/Hyper-Connections/Birkhoff 3 篇。
- 3 份已有 PDF 经标题、作者、页数和散列核验后直接复用，没有重复下载；3 份新增 PDF 均来自官方 arXiv。
- 更新 3 篇既有笔记，新建 3 篇笔记。所有笔记均记录约束对象、核心公式、页码、实验数字、成本、负面证据和当前课题映射。
- 没有遇到付费墙，也没有使用镜像、博客或二手网页作为论文证据。
- 最重要的裁决是：现有论文只证明权重子空间或残差混合的几何性质，**没有一篇直接证明流形约束能改善恶意流量物理状态到生成表征的耦合**。mHC 的两篇后续论文还给出流坍缩、近恒等退化、单独微调不如 LoRA 等反例。

## 证据协议

1. `output/Physics Manifold Constrained Representation.md` 与 `output/deep-research-report.md` 只用于发现关键词、标识符和候选引用链，不作为事实来源。
2. 题名、作者、版本、年份和载体优先以官方 arXiv、会议论文集或出版社页面核验。
3. 公式、实验数字、限制和成本均回到本地原始 PDF 阅读；笔记中的页码按 PDF 阅读器页码计数。
4. 新增论文只有在官方元数据与题名一致后才下载；已有 PDF 不重新下载。
5. Scite MCP 本轮返回月度配额耗尽，未能补充引用语境。该限制不影响本文对原始 PDF 的核验，但不能据此声称已完成独立引用支持/反驳统计。
6. 已按 `pdf-converter` 技能补做转换器检查：精确 `extract` 因本机未配置 MinerU 令牌不可用；对 19 页 StelLA 的官方 `flash-extract` 请求已成功提交，但 5 分钟内未完成并超时，未生成临时制品。24 页 mHC 微调论文超过快速模式的 20 页上限，因此按技能规则回退到本地 `pdfinfo`、`pdftotext` 与原 PDF 逐页核验，没有把低保真输出冒充公式或表格证据。

## 纳入文献

| 类别     | 论文                                                                         | 原始元数据                                                                        | 页数 | 约束对象                            | 笔记                                                      |
| -------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---: | ----------------------------------- | --------------------------------------------------------- |
| Stiefel  | Riemannian Optimization for LoRA on the Stiefel Manifold                     | [arXiv:2508.17901](https://arxiv.org/abs/2508.17901)，Findings of EMNLP 2025      |   15 | LoRA 的 \(B\) 权重因子              | `wiki/papers/attack-detection/Stiefel流形LoRA黎曼优化.md` |
| Stiefel  | FoRA: Fisher-orthogonal Rank Adaptation for Parameter-Efficient Fine-Tuning  | [arXiv:2605.29317](https://arxiv.org/abs/2605.29317)，arXiv 元数据注明 EMNLP 2026 |   17 | Fisher 选层后的 LoRA \(B\) 因子     | `wiki/papers/attack-detection/FoRA-Fisher正交秩适配.md`   |
| Stiefel  | StelLA: Subspace Learning in Low-rank Adaptation using Stiefel Manifold      | [arXiv:2510.01938](https://arxiv.org/abs/2510.01938)，NeurIPS 2025 Spotlight      |   19 | \(USV^\top\) 的输入与输出子空间因子 | `wiki/papers/manifold/StelLA-Stiefel子空间低秩适配.md`    |
| Birkhoff | mHC: Manifold-Constrained Hyper-Connections                                  | [arXiv:2512.24880](https://arxiv.org/abs/2512.24880)，arXiv v2                    |   19 | 多流残差混合矩阵                    | `wiki/papers/deepseek/mHC-流形约束超连接.md`              |
| Birkhoff | Manifold-Constrained Hyper-Connections for Parameter-Efficient Finetuning    | [arXiv:2607.18130](https://arxiv.org/abs/2607.18130)，arXiv v1                    |   24 | 冻结主干上的残差读写与混合路由      | `wiki/papers/manifold/mHC参数高效微调.md`                 |
| 负面机制 | Analyzing Stream Collapse in Hyper-Connections: From Diagnosis to Mitigation | [arXiv:2606.03483](https://arxiv.org/abs/2606.03483)，ICML 2026 研讨会            |   13 | 多流残差的角色分配与对称性          | `wiki/papers/manifold/超连接流坍缩诊断.md`                |

## PDF 真实性与散列

| 状态            | 本地路径                                     | PDF 元数据页数 | SHA-256                                                            |
| --------------- | -------------------------------------------- | -------------: | ------------------------------------------------------------------ |
| 已有，未重下    | `raw/papers/attack-detection/2508.17901.pdf` |             15 | `f8301a2688e1ab53aaecf4f3c1e134bbe477d5ec71eb73f480f1aed88890451d` |
| 已有，未重下    | `raw/papers/attack-detection/2605.29317.pdf` |             17 | `01844fc57444ac140b70370b45316456c577dcca694ce713bd4cd64992574162` |
| 已有，未重下    | `raw/papers/deepseek/2512.24880v2.pdf`       |             19 | `d849f4709ed29bfb2751f51e24dc836403f31271d1764dddfba0768d326a75d9` |
| 官方 arXiv 新增 | `raw/papers/manifold/2510.01938v2.pdf`       |             19 | `06c2125827295f11fb98b74017fe3b53220f4888a869242519fe06a2c66376c2` |
| 官方 arXiv 新增 | `raw/papers/manifold/2607.18130v1.pdf`       |             24 | `9493db14999372d3bdd8285856d654ccbfa05684d28b4eb2b57a2430198aac44` |
| 官方 arXiv 新增 | `raw/papers/manifold/2606.03483v1.pdf`       |             13 | `0ddedbb697397ef2b75bfbec7d94b90bad7c2ec9d3f7862220ea74c401b41f9b` |

所有 6 份文件均可被 `pdfinfo` 与 `pdftotext` 正常解析，PDF 内嵌标题和作者与官方元数据一致。

## 关键证据

### Stiefel 与正交低秩适配

1. **Stiefel-LoRA**：第 4--5 页用切空间投影和 QR 回缩约束 \(B^\top B=I\)；第 7 页与第 15 页显示有效秩接近满秩。第 8 页表 4 是重要反例：固定随机 \(A\) 只训练 \(B\) 时，Stiefel 平均 50.1，低于 AdamW 的 57.1，说明正交性必须与任务相关的另一因子共同学习。论文没有墙钟、吞吐和显存表。
2. **FoRA**：第 2--4 页用静态对角 Fisher 选择少量层，再用 Cayley 更新和周期 QR 保持列正交。第 4 页主表通常用约一半参数优于 LoRA，但第 12 页跨模型表中 Gemma-3-270M 的普通 LoRA 高于 FoRA，Gemma-2-9B、Qwen-3-4B 和 LLaMA-2-13B 的纯 Stiefel 高于 FoRA。Cayley 更新额外增加约 10%--15% 单步时间。
3. **StelLA**：第 3--4 页同时约束 \(U,V\) 并用极分解回缩；第 19 页报告单张 H100 上 4.5 小时对 5.2 小时，约慢 15%。第 9 页的商流形消融证明三因子表示仍有等价自由度，产品 Stiefel 形式没有“消除规范自由度”。第 19 页还明确承认实际 \(\gamma=\alpha/r\) 不保证其推导的理论尺度稳定。

共同边界：三篇论文约束的都是模型权重因子，没有把预测队列状态作为样本相关输入，也没有验证 \(\partial\hat y/\partial\hat q\neq0\)。把这些方法移植到物理投影只是可实验假设。

### Birkhoff 与多流残差

1. **原始 mHC**：第 8--9 页把 \(H^{res}\) 约束到 Birkhoff 多面体并执行 20 次 Sinkhorn。双随机矩阵的谱范数不超过 1、对乘法闭包，但这只支持非扩张与凸混合，不支持严格能量守恒或信息无损。第 14 页表明有限步 Sinkhorn 后组合最大增益仍约 1.6。27B 主表多数任务优于 HC，但 MATH 为 26.0，低于 HC 的 26.4。
2. **mHC 参数高效微调**：第 9 页固定 \(H^{res}=I\) 在所有流数上优于学习残差混合并减少参数。第 10--11 页的 7B 同预算比较中，mHC 测试损失 1.095/1.076，明显高于 LoRA 的 1.016/0.995；mHC+LoRA 只从 0.981 改善到 0.980，八项下游指标各有胜负。正文称 320,000 条训练样本，附录又称固定分层子集截断到 20,000 条，且承认 LoRA 可能到 30,000--40,000 步才平台，存在协议表述与欠训练风险。
3. **流坍缩诊断**：第 2--4 页发现残差混合常接近恒等，读写信号、范数和可解释特征集中到单条流。0.12B 模型固定大多数残差混合为恒等后四项困惑度全部改善；0.36B 则变差，说明效应依规模和分布而变。LSS 对称性破缺多数有效，但 mHC-lite 0.36B 的 C4 仍从 50.95 退化到 51.23。

共同边界：Birkhoff 约束能限制数值放大，却不能保证多条流形成互补语义，更不能保证其中一条自然成为物理流。

## 两份自动检索报告的真实性审计

| 来源与原主张                                                                       | 核验结果                                                                                                                                                  | 处理                                           |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `Physics Manifold Constrained Representation.md` 把 StelLA 标为 `arXiv:2512.11989` | 错误。官方 [arXiv:2512.11989](https://arxiv.org/abs/2512.11989) 是星系天文学论文 NGDEEP；StelLA 正确编号为 [2510.01938](https://arxiv.org/abs/2510.01938) | 记录为明确元数据错误，不沿用其 BibTeX          |
| 同报告称 StelLA 消除规范自由度与缩放模糊性                                         | 夸大。原文第 9 页明确讨论三因子不唯一，并另做商流形消除等价关系                                                                                           | 笔记改为“不唯一性仍存在”                       |
| 同报告称 StelLA 可直接承载并保护物理状态                                           | 未验证。原文只约束权重因子，没有动态物理输入或恶意流量实验                                                                                                | 降级为待验证的实现假设                         |
| 同报告称 Birkhoff 混合实现严格能量守恒、信息无损                                   | 错误推论。谱范数不超过 1 只表示非扩张，允许收缩；有限 Sinkhorn 的组合增益仍约 1.6                                                                         | 只保留非扩张、闭包和凸混合结论                 |
| 同报告把 mHC 列为 ICLR 2026，并称其直接支持物理双流                                | 本轮官方 arXiv 页面可核验预印本，但未以正式会议元数据替代 `journal`；原文没有物理流                                                                       | 载体写为 arXiv，物理映射标为外推               |
| `deep-research-report.md` 称 mHC “几乎直接支撑”方案 C                              | 后续 2607.18130 和 2606.03483 显示近恒等退化、流坍缩和单独 mHC 不如 LoRA                                                                                  | mHC 优先级下调，恒等混合与普通门控列为强制基线 |
| 同报告把 6.7% 预训练开销迁移为 Qwen PEFT 成本依据                                  | 不成立。原始论文没有硬件/吞吐成本表，且该数字依赖融合内核、重计算和特定预训练系统                                                                         | 不用于单卡 RTX 5090 成本估计                   |
| 同报告称 Stiefel 与 Birkhoff 证据已足够构成物理耦合稳定性论证                      | 只能构成方法背景。物理投影的梯度路径、可观测性、有限 Sinkhorn 误差和生成损失均需重新定义与证明                                                            | 禁止在方法章写成已有理论定理                   |

两份报告中的内嵌 `turn...` 引用标记不可在仓库外复现，未作为可引用文献证据。

## 排除与延期条目

| 条目                                                                        | 官方核验                                                                                           | 决策与原因                                                                                           |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `arXiv:2512.11989`                                                          | [NGDEEP 天文学论文](https://arxiv.org/abs/2512.11989)                                              | 与课题无关；由错误 StelLA 编号产生，排除                                                             |
| OPLoRA                                                                      | [AAAI 2026，DOI 10.1609/aaai.v40i40.40703](https://ojs.aaai.org/index.php/AAAI/article/view/40703) | 真实论文，研究灾难性遗忘的双侧正交投影；受 6 篇全文上限与主题重叠限制，延期，不下载                  |
| OrthoGeoLoRA                                                                | [arXiv:2601.09185](https://arxiv.org/abs/2601.09185)                                               | 真实预印本，但任务是多语句子编码器上的社会科学概念检索，与 StelLA/FoRA 重叠且迁移面窄，延期，不下载  |
| Orthogonal Finetuning Made Scalable                                         | [arXiv:2506.19847](https://arxiv.org/abs/2506.19847)，EMNLP 2025 Main                              | 真实论文，提供 OFTv2/QOFT 工程成本，但不是低秩 Stiefel 或 Birkhoff 核心证据；受篇数限制延期，不下载  |
| ELLA                                                                        | [ACL Anthology 2026.eacl-long.84](https://aclanthology.org/2026.eacl-long.84/)                     | 真实 EACL 2026 论文，摘要提供“严格正交抑制共享”的负面线索；本轮未全文核验，不把摘要论断写入 6 篇笔记 |
| Subspace Geometry Governs Catastrophic Forgetting in Low-Rank Adaptation    | [arXiv:2603.02224](https://arxiv.org/abs/2603.02224)                                               | 真实预印本，偏持续学习理论；受篇数限制只做元数据筛选，不引用其公式或实验数字                         |
| Hyper-Connections                                                           | [arXiv:2409.19606](https://arxiv.org/abs/2409.19606)                                               | 真实母结构；本轮优先精读约束版本和两篇负面后续，未重复扩展到第 7 篇                                  |
| Beyond the Birkhoff Polytope: Spectral-Sphere-Constrained Hyper-Connections | [arXiv:2603.20896](https://arxiv.org/abs/2603.20896)                                               | 真实预印本，其摘要批评 Birkhoff 身份退化和非负性限制；只作为后续线索，未全文核验，不纳入结论         |

## 对实验优先级的建议

1. **首选对照**：保持普通 QLoRA 和单流残差，先验证普通线性物理投影或门控注入能否使生成输出真实依赖预测状态。
2. **几何增量**：只有普通物理投影有效后，再仅对物理投影做单侧 Stiefel 或 StelLA 三因子约束；必须同预算比较无约束、软正交和硬正交。
3. **mHC 降级**：完整 Birkhoff 多流不是当前优先方案。若仍验证，必须包含固定恒等 \(H^{res}\)、普通门控、无约束混合、流间相似度和离恒等距离。
4. **判定指标**：除生成质量与状态误差，还需报告正交误差、有效秩、\(S\) 奇异值、行列和误差、混合谱范数、每流读写份额、每流范数、墙钟、峰值显存和吞吐。
5. **论文措辞**：可写“Stiefel 与 Birkhoff 提供候选几何约束”，不可写“已有文献证明其能稳定注入恶意流量物理状态”。

## 文件变更

### 更新

- `wiki/papers/attack-detection/Stiefel流形LoRA黎曼优化.md`
- `wiki/papers/attack-detection/FoRA-Fisher正交秩适配.md`
- `wiki/papers/deepseek/mHC-流形约束超连接.md`
- `output/第一创新点实验总控.md`：按主代理追加要求，仅同步已验收的文献与任务十六进度。

### 新建

- `raw/papers/manifold/2510.01938v2.pdf`
- `raw/papers/manifold/2607.18130v1.pdf`
- `raw/papers/manifold/2606.03483v1.pdf`
- `wiki/papers/manifold/StelLA-Stiefel子空间低秩适配.md`
- `wiki/papers/manifold/mHC参数高效微调.md`
- `wiki/papers/manifold/超连接流坍缩诊断.md`
- `.Codex/docs/sdd/manifold-peft-literature-report.md`

### 明确未改动

- 未修改任何 `INDEX.md`。
- 未整理或改写总控历史，也未修改其他共享进度文档。
- 未连接 GPU 服务器，未运行实验，未创建 Git 提交。

## 验证门禁

- PDF 标题、作者、页数与 SHA-256：已核验。
- 笔记必填字段 `title`、`authors`、`year`、`journal`、`source_pdf`、`key_finding`：6 篇均已通过自动检查。
- `source_pdf` 本地目标存在性：6 个目标均存在且非空。
- 本任务修改的 7 个 Markdown 文件：已通过 Prettier 检查。
- `git diff --check` 与暂存区空白检查：均已通过。
