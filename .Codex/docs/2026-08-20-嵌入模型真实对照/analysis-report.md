# 嵌入模型真实对照严格分析

## 分析问题

1. E5-base 或 BGE-M3 是否在预注册真实用户集与跨作用域集上相对当前 E5-small 形成明确非支配优势？
2. 人工构造回归集上的提升是否能迁移到真实用户意图？
3. 模型容量、构建时间、冷加载、热查询和索引代价是否可接受？
4. 失败主要来自嵌入模型，还是拒答与 collection 融合合同？

## 比较单位与有效性

- 效果比较单位是冻结查询，不是随机种子、折或独立实验重复。
- `curated-regression-v1` 有 14 条正例和 2 条负例，只作回归。
- `real-user-query-v1` 有 7 条正例和 1 条负例，是独立验收。
- `cross-scope-query-v1` 有 5 条正例和 1 条负例，是独立验收。
- 三模型使用同一冻结语料、分块、词法实现、RRF 参数、Top-k 和查询集合。
- 三次热查询重复只用于本机延迟中位数与 P95，不作为效果显著性样本。

比较在工程上有效，但样本不是从未来用户分布随机抽取，不能作总体显著性推断。

## 主要发现

### 真实用户向量检索

E5-small 相对 E5-base 的 `Recall@5/Recall@10/MRR/nDCG` 绝对差为 `+0.1000/+0.2143/+0.2045/+0.1128`。相对 BGE-M3 为 `+0.0286/0.0000/+0.1464/+0.0295`。

E5-base 的错 collection 率比 E5-small 低 `0.0143`，但这只对应 70 个 Top-10 结果中的 1 个结果，且没有伴随相关性指标改善。

### 真实用户混合检索

三模型的 Recall@5 与 Recall@10 相同。E5-small 相对 E5-base 和 BGE-M3 的 MRR 均高约 `0.0119`，nDCG 均高约 `0.0099`。差异小，主要结论是两个大模型没有带来独立验收收益，而不是 E5-small 大幅领先。

### 跨作用域检索

E5-small 的向量模式相对 E5-base 在四个指标上分别高 `0.1000/0.3000/0.1000/0.1440`，相对 BGE-M3 高 `0.1000/0.3000/0.0900/0.1353`。

混合模式下，E5-small 相对 E5-base 高 `0.1000/0.1000/0.1714/0.1226`，相对 BGE-M3 高 `0.1000/0.0000/0.1614/0.0784`。

### 回归集与迁移失败

BGE-M3 在回归集向量模式的 MRR 为 `0.9286`，高于 E5-small 的 `0.8571`；混合模式 MRR 为 `0.9167`，高于 E5-small 的 `0.8988`。这些提升没有迁移到两个独立验收集，说明人工目的性查询不能单独承担模型选择。

### 工程代价

- E5-base 构建墙钟是 E5-small 的约 `3.05` 倍。
- BGE-M3 构建墙钟是 E5-small 的约 `10.62` 倍。
- E5-base 权重是 E5-small 的约 `2.36` 倍。
- BGE-M3 权重是 E5-small 的约 `4.83` 倍。
- BGE-M3 的真实用户混合热查询中位数是 E5-small 的约 `1.32` 倍，跨作用域混合查询约为 `2.24` 倍。

## 失败归因

所有模型对所有负例均返回 10 条结果，拒答率为 0。换模型没有改变该行为。

`scope=all` 的错 collection 率为 0.80 至 0.88。当前联邦融合给每个 collection 的首位相同 RRF 先验，使 collection 混排成为主要误差源。模型替换只能改变 collection 内次序，不能消除该结构性偏差。

## Claim Candidates

### 候选一

- Claim：两个新候选均未在本轮预注册独立验收集上相对 E5-small 形成明确非支配优势。
- Source evidence：`comparison.csv`、`raw_results.json`。
- Allowed wording：在本轮三个候选和两套预注册独立验收集内，继续使用 E5-small 有效果与成本依据。
- Forbidden stronger wording：E5-small 是所有中英检索任务的最优模型；E5-small 显著优于 BGE-M3。
- Uncertainty：查询数少且不是随机样本，没有总体置信区间。
- Next check：扩大独立真实查询，但继续禁止用验收集调参。
- Decision：keep。

### 候选二

- Claim：BGE-M3 在人工回归集上的提升没有迁移到真实用户与跨作用域验收。
- Source evidence：三套集合分别报告的 Recall、MRR 和 nDCG。
- Allowed wording：目的性回归集不应单独决定生产嵌入模型。
- Forbidden stronger wording：BGE-M3 不适合任何项目文档检索。
- Uncertainty：本轮只使用 BGE-M3 的稠密向量能力，没有评价其稀疏或多向量通道。
- Next check：无；当前不值得继续扩展，除非未来需求转为长文档或多向量检索。
- Decision：keep。

### 候选三

- Claim：当前拒答和跨 collection 融合是独立于嵌入模型的主要系统问题。
- Source evidence：三模型负例拒答率均为 0，错 collection 率均为 0.80 至 0.88，混合结果高度相似。
- Allowed wording：下一轮应使用新的开发集评估路由、collection 先验和拒答，而不是继续扩大嵌入模型。
- Forbidden stronger wording：修正 collection 融合必然提高所有查询指标。
- Uncertainty：尚未执行路由或融合消融。
- Next check：另建开发集和最小路由消融，独立验收集只做最终验收。
- Decision：keep。

