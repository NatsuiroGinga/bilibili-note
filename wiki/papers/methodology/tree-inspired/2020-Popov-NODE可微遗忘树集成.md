---
title: "Neural Oblivious Decision Ensembles for Deep Learning on Tabular Data"
authors: [Sergei Popov, Stanislav Morozov, Artem Babenko]
year: 2020
date: 2026-08-20
journal: "International Conference on Learning Representations 2020"
source_pdf: "[[raw/papers/methodology/tree-inspired/2020-Popov-NODE.pdf]]"
arxiv: "1909.06312"
sha256: "daa0d574fed6c3ecd279fc9670052183df6bd60c956fcc214b9437e24a342810"
zotero_item_key: "D4KH9JT8"
tags: [表格数据, 可微决策树, 遗忘树, entmax, 类型/论文]
aliases: [NODE, Neural Oblivious Decision Ensembles]
key_finding: "NODE 把等深遗忘树的特征选择、阈值和叶响应软化为可微运算，并用多层稠密连接实现端到端训练；论文在 HIGGS 的 1050 万训练样本上运行，但官方实现明确自述显存低效，后续跨基准研究也显示其稳健性弱于 XGBoost。"
related: ["[[2022-ShwartzZiv-表格数据深度学习并非必需]]", "[[2022-Grinsztajn-树模型为何优于表格深度学习]]"]
---

# NODE：可微遗忘决策树集成

## 论文原方法

- 单层包含 `m` 棵同深度 `d` 的可微遗忘树；同一深度共享分裂特征和阈值，叶表有 `2^d` 项（物理页 3 至 4，第 3.1 节）。
- `entmax` 同时软化特征选择与左右路由，阈值、温度和叶响应均由小批量梯度下降联合训练；多层 NODE 把前层树输出与原输入连接（物理页 3 至 5）。
- 默认结构为一层、2048 棵、深度 6；论文说明该设置继承 CatBoost 的遗忘树配置，而非本任务最优值（物理页 6）。

## 规模与结果边界

- HIGGS 使用 1050 万训练样本、50 万测试样本和 28 个特征；另含 40 万至 80 万规模的数据集（物理页 10，表 5）。
- 官方仓库为 `Qwicen/node`，MIT；README 明确称实现显存低效，CPU 比 GPU 慢约 8 至 10 倍。
- Shwartz-Ziv 等的跨数据集重评中，NODE 的平均相对劣化为 14.21%，明显差于 XGBoost 3.34%；因此 NODE 只能作为树启发强基线，不能预设升级。

## 对当前任务的可迁移接口

- 83 字段可直接作为数值输入；端口、协议等低基数字段可先沿用共同预处理，首轮不增加目标编码或目标年统计。
- 逐流表示可取最后一层各树输出的连接向量，再送入因果前缀聚合与实体幂平均池化；实体损失可沿池化、前缀聚合和树路由回到全部骨干参数。
- 2048×深度 6 只能作为论文默认参照。进入实验前必须用真实批次测峰值显存与吞吐，并在共同 4.5 GPU 小时上限内冻结可完成的容量。

## 不能支持

- 论文没有极端不平衡实体 AP、告警预算曲线、跨年度迁移、CPA 或 ELP。
- HIGGS 大规模可运行不等于当前官方实现能在 32.6 GiB 显存下完成 LSPR23 配方。
