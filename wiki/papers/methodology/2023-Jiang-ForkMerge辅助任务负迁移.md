---
title: "ForkMerge: Mitigating Negative Transfer in Auxiliary-Task Learning"
authors: [Junguang Jiang, Baixu Chen, Junwei Pan, Ximei Wang, Dapeng Liu, Jie Jiang, Mingsheng Long]
year: 2023
date: 2026-08-20
journal: "Advances in Neural Information Processing Systems 36"
source_pdf: "[[raw/papers/methodology/auxiliary-learning/2023-Jiang-ForkMerge辅助任务负迁移.pdf]]"
doi: "10.52202/075280-1322"
sha256: "597e00c0b973a5ba96b031efc4e60b9be277846d484252252c009f7a72a2f9de"
tags:
  - 辅助任务学习
  - 负迁移
  - 模型分支合并
  - 类型/论文
key_finding: "论文实验证明负梯度夹角与负迁移并非充要关系，并提出周期性训练目标任务分支与联合任务分支，再按目标验证性能选择凸组合，以过滤有害辅助更新。"
method: "把模型周期性分成目标任务单独训练和目标加辅助任务联合训练两个分支，在若干步后用目标验证集搜索两套参数的凸组合，合并并同步后进入下一周期。"
baseline: "单任务、等权联合、Post-train、GCS、OL_AUX、ARML、Auto-lambda、GradNorm、PCGrad、IMTL、CAGrad、NashMTL 等"
aliases:
  - ForkMerge
  - Jiang2023-ForkMerge
---

# ForkMerge：辅助任务学习中的负迁移过滤

> Jiang 等，NeurIPS 2023，23 个物理页。官方全文来自 NeurIPS 会议论文页。

## 一句话

负梯度夹角不能单独裁决辅助任务是否有害；ForkMerge 同时训练“只有主任务”和“主任务加辅助任务”两条分支，再用主任务验证性能选择参数凸组合，从而允许保留有益更新并把有害分支权重降到零。

## 论文原结论

- 物理 pp.3–4 定义辅助任务的迁移增益、弱负迁移与强负迁移：如果存在某个正辅助权重可以避免退化，则属于弱负迁移；如果所有正权重都退化，则仅调权不能解决。
- 物理 p.4 的 Finding 1 指出，负梯度夹角不一定导致负迁移，梯度同向也不保证正迁移。作者将训练优化与验证泛化分开解释，要求最终以目标任务验证表现裁决。
- 物理 p.5 的 Finding 2 把负迁移与辅助任务引入后训练分布相对目标测试分布的偏移联系起来；这是论文在 DomainNet 上的实验发现，不是无条件定理。
- 物理 pp.5–6 的公式（5）至（8）和算法 1：从同一参数分叉两条分支，一条仅优化目标损失，另一条优化目标加辅助损失；每隔 `Delta t` 步，用目标验证性能选择两套参数的凸组合，再同步进入下一轮。
- 物理 pp.8–10 的表 1 至表 6：DomainNet 上等权联合相对单任务平均退化 `9.62%`，ForkMerge 平均提升 `2.00%`；NYUv2 上 ForkMerge 的综合相对提升为 `4.03%`。这些结果来自图像、多任务、推荐与半监督基准，不是网络流量证据。

## 机制边界

1. ForkMerge 不依赖“负梯度夹角就是根因”的假设，梯度相似度只作为对比方法。
2. 两分支版本的训练计算约为单分支的两倍，并额外需要周期性目标验证搜索。多辅助任务版本复杂度随分支数线性增长，论文用早期剪枝降低成本。
3. 参数凸组合依赖两个分支从同一起点出发且处在可合并区域；论文给出经验与局部分析，不保证任意模型、任意间隔都可安全线性合并。
4. 方法需要可反复读取的目标任务验证集。若验证正例极少，频繁搜索会过拟合；论文也明确指出单步估计噪声和验证过拟合风险，因此把搜索扩展到多个训练步。

## 与第三章 CPA-ELP 的关系

- **论文原结论**：固定辅助损失权重可能产生负迁移；负梯度夹角不足以判断辅助任务是否有害；以主任务验证表现选择辅助更新是一个已发表方案。
- **本课题映射**：逐流损失是主训练信号，ELP 的序列级损失是辅助信号。当前固定 `lambda=1` 的朴素相加与论文公式（1）同形，但本课题的主评价还包括实体 AP 和告警预算曲线，不能把逐流验证 AP 单独当作完整主任务性能。
- **可迁移机制**：从同一源年检查点比较“逐流损失分支”和“逐流加实体/序列辅助分支”，只用 LSPR23 实体折外验证选择辅助更新是否保留。它替换的是 CPA 与 ELP 的组合训练方式，不替换二者的前向算子。
- **不可直接声称**：ResMLP2 的 C11 失败由辅助任务负迁移造成；ForkMerge 必然修复跨年度性能；梯度冲突诊断可以省略实体级源验证；论文在 LSPR 或网络攻击检测中验证过该方法。

## 最小可证伪实验

1. 先以源年三折实体折外预测比较固定 `lambda=0` 与现有 `lambda=1`，判断属于可通过辅助权重改善的弱负迁移，还是所有已注册正权重均无益的强负迁移候选。
2. 只有源年实体主指标支持辅助分支时才运行两分支合并；同时保留固定权重、仅主任务、PCGrad 或 Recon 式结构隔离作为同预算对照。
3. 若源年验证仍只用协议 A 的约 20 个正实体，则不得执行周期性合并选择；必须使用实体不相交三折 OOF 或另行证明统计功效。

## 证据与题录

- 正式页：<https://proceedings.neurips.cc/paper_files/paper/2023/hash/60f9118a849e8e9a0c67e2a36ad80ebf-Abstract-Conference.html>
- 正式 PDF：<https://proceedings.neurips.cc/paper_files/paper/2023/file/60f9118a849e8e9a0c67e2a36ad80ebf-Paper-Conference.pdf>
- DOI：<https://doi.org/10.52202/075280-1322>
- 全文核验：23 页；关键位置为物理 pp.3–6、8–10。
- Zotero：新父条目键 `2BJKQX8P`，BibTeX 键 `Jiang2023_2BJKQX8P`，正式全文链接附件键 `DN72B3ES`。导入后复核发现既有同 DOI 条目 `85H7UAAE`；导入前完整题名检索曾错误返回零项。当前保留两项并标记待人工合并，未擅自删除。
