---
title: "DeepGBM: A Deep Learning Framework Distilled by GBDT for Online Prediction Tasks"
authors: [Guolin Ke, Zhenhui Xu, Jia Zhang, Jiang Bian, Tie-Yan Liu]
year: 2019
date: 2026-08-20
journal: "Proceedings of the 25th ACM SIGKDD Conference"
doi: "10.1145/3292500.3330858"
source_pdf: "[[raw/papers/methodology/tree-inspired/2019-Ke-DeepGBM-KDD.pdf]]"
sha256: "027ae80f0113c512eb3961efa6ca7609df2807f8a8ae205f09e56538cd6c282f"
zotero_item_key: "UTS5MJAS"
tags: [表格数据, GBDT蒸馏, 在线预测, 类型/论文]
aliases: [DeepGBM, GBDT2NN]
key_finding: "DeepGBM 先把离线 GBDT 按树分组并蒸馏为可在线更新的 GBDT2NN，再与类别特征网络联合训练；论文覆盖 4580 万样本 Criteo，具备规模证据，但官方代码仓库没有许可证，按当前硬门排除。"
related: ["[[2020-Popov-NODE可微遗忘树集成]]"]
---

# DeepGBM：GBDT 蒸馏神经网络

## 论文原方法

- GBDT2NN 将树分组，学习叶索引嵌入与数值特征到树组输出的神经近似；CatNN 处理稀疏类别字段，两个分支以可训练权重联合（物理页 4 至 6，式 11 至 15）。
- 初始训练同时使用真值损失与 GBDT 蒸馏损失；在线更新阶段去掉 GBDT 教师，只用新数据真值更新神经模型（物理页 6）。
- 数据包含 4580 万样本、13 数值加 26 类别字段的 Criteo，以及 892 万 Malware 等大规模任务（物理页 7，表 2）。

## 当前裁决

- 学生推理和在线更新本身可微，源年 GBDT 教师不使用目标年标签，机制上可作为树知识初始化。
- 官方仓库 `motefly/DeepGBM` 当前 HEAD `6926d35bdcc3249befc127973d313e3c061f2bb2`，但根目录无 LICENSE，GitHub 未识别许可证；依赖 PyTorch 0.4.1 与 LightGBM 2.2.1。
- 按任务硬门“许可证不明者排除”，不进入候选。若作者补充许可证，可另立现代重实现与教师公平预算合同。
