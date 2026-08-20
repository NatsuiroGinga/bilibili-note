---
title: "GRANDE: Gradient-Based Decision Tree Ensembles"
authors: [Sascha Marton, Stefan Luedtke, Christian Bartelt, Heiner Stuckenschmidt]
year: 2024
date: 2026-08-20
journal: "International Conference on Learning Representations 2024"
source_pdf: "[[raw/papers/methodology/tree-inspired/2024-Marton-GRANDE.pdf]]"
arxiv: "2309.17130"
sha256: "819a8c23270f5b71018d6481782d043a4bf4d8bdd5e1af62776e5c56fdb96f98"
zotero_item_key: "4L4MLPEB"
tags: [表格数据, 可微决策树, 轴对齐分裂, 直通估计, 类型/论文]
aliases: [GRANDE, Gradient-Based Decision Tree Ensembles]
key_finding: "GRANDE 用直通估计联合学习硬轴对齐分裂、阈值、叶值与样本依赖树权重，是当前候选中最接近 XGBoost 分段常数归纳偏置的端到端可微模型；但原论文最大数据集仅 96,320 样本，20M 流可扩展性没有实证。"
related: ["[[2020-Popov-NODE可微遗忘树集成]]", "[[2022-Grinsztajn-树模型为何优于表格深度学习]]"]
---

# GRANDE：梯度树集成

## 论文原方法

- 前向使用硬、轴对齐分裂，反向以直通估计传播特征选择与取整梯度；所有树的分裂位置、特征、叶值联合训练（物理页 1 至 3）。
- 实例级叶权重为每个样本动态组合树，允许少数树充当局部专家；树集成采用张量化密集表示并行计算（物理页 3 至 5）。
- 原论文比较 19 个二分类数据集，以 250 次 Optuna 和 5×2 交叉验证选择；最大数据集 numerai28.6 为 96,320 样本、21 特征（物理页 6、13，表 2、表 5）。

## 官方实现与规模边界

- 官方仓库 `s-marton/GRANDE`，MIT；当前 HEAD `07f7278b30ab9ebbbdc544e5f9a91f1b5df7fecb`。
- 当前 PyTorch 示例默认深度 5、1024 棵、批量 256、最多 250 个周期；这是 2026 年仓库当前实现，包含论文后更新，不能冒充 ICLR 2024 原始复现配置。
- 原论文在最大数据集上的平均运行约 39 秒，但规模不足 10 万；该数字不能外推至 1635 万流。

## 对当前任务的可迁移接口

- 83 字段天然适配轴对齐分裂，是与 XGBoost 归纳偏置最接近的候选。
- 逐流表示可采用每棵树的叶输出与实例权重向量；因果前缀聚合后再预测，实体幂平均损失能回传至树权重、叶值、阈值和分裂特征参数。
- 首个真实数据门必须只验证一批前向/反向、梯度有限非零、峰值显存和投影吞吐；不能先启动全容量 1024 树全量训练。

## 不能支持

- 原论文没有百万级以上训练证据、极端不平衡 AP、实体级目标或时间迁移。
- 直通估计提供代理梯度，不保证分裂优化稳定；必须报告梯度饱和、无效树比例与数值失败。
