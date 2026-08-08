# 非对称共享私有多任务适配文献任务计划

## 目标

核验并全文研读非对称主辅学习、共享私有表示、任务专用适配器、适配器混合专家与物理约束多任务训练的一手论文，形成可直接支持第三章唯一修复实验的证据链，同时明确不能由文献直接推出的结论。

## 阶段

- [x] 阶段一：读取强制恢复文档、笔记规范和文献工作流，核对当前 S3/S4 失败事实。
- [x] 阶段二：检索并核验候选论文的原始出版页、标识符和公开全文。
- [x] 阶段三：下载新增 PDF，提取全文并逐篇核对机制、公式、实验与局限。
- [x] 阶段四：建立或补充结构化中文论文笔记，更新主题索引。
- [x] 阶段五：完成综合报告，检查引用真实性、文件链接和证据边界。

## 固定研究问题

1. 为什么当前家族任务退化、子类与未知攻击改善的证据更适合任务级参数隔离，而不是再次调整博弈权重？
2. 家族分支保持不变需要哪些结构、冻结、路由和确定性前提？
3. 双锚点状态监督与有限队列残差如何只训练物理私有分支，同时不把未知攻击标签用于训练？
4. 多物理专家与学习型词元级 Top-K 路由是否适合当前修复，专家塌缩和路由不稳定如何限制其可用性？
5. 哪些文献只能支持结构先例，不能支持本课题的检测增益或物理语义结论？

## 强制核验清单

以下 11 篇必须逐篇核对本地原件并形成全文阅读笔记：

1. DeepSeekMoE，arXiv `2401.06066`。
2. Asymmetric Multi-task Learning Based on Task Relatedness and Loss，ICML 2016。
3. Domain Separation Networks，NeurIPS 2016。
4. AdapterFusion，arXiv `2005.00247`，正式版 EACL 2021。
5. MixLoRA，arXiv `2404.15159`。
6. Mixture of LoRA Experts，arXiv `2404.13628`。
7. Augmented Physics-Informed Neural Networks，arXiv `2211.08939`。
8. Scaling Physics-Informed Hard Constraints with Mixture-of-Experts，arXiv `2402.13412`，ICLR 2024。
9. Dense Backpropagation Improves Routing for Sparsely-Gated Mixture-of-Experts，PMLR 262。
10. BASE Layers，PMLR 139。
11. LoRA-Switch，OpenReview `NIG8O2zQSQ`；必须区分投稿状态与正式发表状态。

已下载并判定有补充价值的 Deep-AMTFL、对抗式多任务文本分类、Recon、MTLoRA、MoDULA、LoRA-Flow、Switch Transformer、StableMoE 和辅助任务 PINN 也纳入结构化笔记或已有笔记复核。

## 产物

- 新增原始 PDF：`raw/papers/pinn/` 或已有更合适的论文目录。
- 论文笔记：优先 `wiki/papers/pinn/`，已有规范笔记不重复创建。
- 索引：`wiki/papers/pinn/INDEX.md`。
- 综合报告：`.Codex/docs/非对称共享私有多任务适配文献综述.md`。
- 过程证据：本目录 `notes.md`。

## 边界

- 不修改 GPU 实验代码、实验配置、运行目录或两份强制恢复文档。
- 不把共享私有结构或专家路由称为新的物理定律；它们只处理物理训练信号对检测任务的参数干扰与条件分配。
- 多专家路由只做后续可行性评估，不改变当前唯一修复实验的固定结构。
- 不使用摘要替代全文，不引用无法核验的题录，不照抄文献公式。

## 错误记录

- 沙箱默认禁止在 `.Codex/docs/sdd/` 新建目录；经授权创建目标目录后继续。

## 当前状态

**已完成**：强制清单 11 篇与扩展清单 9 篇均有本地可解析全文和结构化笔记；主题索引、综合报告、发表状态与证据边界终检通过。
