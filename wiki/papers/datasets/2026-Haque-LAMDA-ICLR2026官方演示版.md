---
title: "LAMDA: A Longitudinal Android Malware Benchmark for Concept Drift Analysis（ICLR 2026 官方演示版）"
authors: [Md Ahsanul Haque, Ismail Hossain, Md Mahmuduzzaman Kamol, Md Jahangir Alam, Suresh Kumar Amalapuram, Sajedul Talukder, Mohammad Saidur Rahman]
year: 2026
date: 2026-09-09
journal: "The Fourteenth International Conference on Learning Representations（ICLR 2026）官方演示文稿"
source_pdf: "[[raw/papers/10011850_e9IemFB.pdf]]"
tags:
  - Android恶意软件
  - 概念漂移
  - 数据集
  - ICLR2026
  - 类型/论文
key_finding: "官方演示版确认 LAMDA 的 2013--2025 年度规模、80/20 年内切分、4561 维基线和 2013--2014→2016--2025 的 IID/NEAR/FAR 展示协议。"
method: "AndroZoo 采样、VirusTotal 检出数标签、Drebin 式静态特征、全局词表与方差阈值、时间漂移和持续学习展示"
baseline: "Linear SVM、LightGBM、MLP、XGBoost、DetectBERT、ViT；持续学习 Domain-IL 与 Class-IL"
aliases:
  - LAMDA ICLR 2026 演示版
  - LAMDA 官方幻灯片
related:
  - "[[2026-Haque-LAMDA-Android恶意软件长期漂移基准]]"
  - "[[LAMDA-2026-原论文与时间漂移相关工作综述|LAMDA 原论文与时间漂移相关工作综述]]"
---

# LAMDA：ICLR 2026 官方演示版

> 证据性质：17 页横向会议演示文稿；第一页写有 `Presenter: Md Ahsanul Haque`。它是官方会议制品，不是论文全文，不能替代 arXiv `2505.18551v1` 的逐节核验。

## 原件与版本

- 本地原件：`raw/papers/10011850_e9IemFB.pdf`。
- SHA-256：`37c1a03cc1ab3d01459695eb6855d109e10fbebe01c6824735fb0405a71f61dd`。
- PDF 物理页数：17；文件创建时间元数据为 2026-03-25。
- 官方入口：<https://github.com/iqsec-lab/lamda>；会议页面与论文标识见主笔记。
- 版本边界：本制品只作为 ICLR 2026 会议演示、规模表和展示协议的补充来源；正式论文数字仍按 arXiv v1 与官方 HTML 笔记分开引用。

## 可核验内容

### 数据规模与构建

- 第 4 页把 LAMDA 与 API Graph 对比为约 1,008,381 个样本、约 369,906 个恶意样本、1,380 个恶意家族和约 150,000 个单例，时间跨度 12 年。
- 第 6--7 页展示 AndroZoo、VirusTotal 检出数标签、APK 反编译和静态特征提取流程；第 6 页列出良性 `VT_detection = 0`、恶意 `VT_detection >= 4`。
- 第 8 页给出年度计数：2013--2025，缺 2015；总量 1,008,381，恶意 369,906，良性 638,475；每年按 80% 训练、20% 测试切分。

### 表示与时间协议

- 第 9 页展示全局词表约 969 万维，以及方差阈值 `0.001`、`0.0001`、`0.01` 对应的 4,561、25,460、925 维变体。
- 第 10 页展示监督时间协议：2013--2014 为训练/IID，2016--2017 为 NEAR，2018--2025 为 FAR；列出的模型包括 Linear SVM、LightGBM、MLP、XGBoost、DetectBERT、ViT。
- 第 14--15 页展示 Chen-AL 主动适应和 Domain-IL、Task-IL、Class-IL 等后续用途。演示版没有给出完整训练参数、种子方差或逐年混淆矩阵。

### 展示性结果

- 第 11 页概括 LAMDA 的 IID F1 约 97.4%、NEAR F1 约 59.4%、FAR F1 约 47.2%；该页是演示版汇总，不能替代主论文表 7 的模型、标准差和指标列。
- 这些数字可用于核对演示内容与主论文叙事一致，不能单独支撑严格源期预处理或新算法有效性。

## 与第三章的关系

- 该演示版补齐了“ICLR 2026 官方会议制品已存在”的原件证据，并独立保存其页面级规模和协议信息。
- 它没有展示安全回归约束、经验回放变体或本课题实验；本课题仍须以自己的源期信息合同、未来标签隔离和逐年实体指标为准。
- 第 9 页明确展示全局词表和多阈值变体，但未说明 4,561 维文件与当前实验制品的生成调用身份；这不能消除主论文和代码中的预处理资格缺口。

## 疑问与待验证

- 演示版没有完整参考文献、附录、训练参数和随机种子，不能代替论文全文的引用核验。
- 第 11 页的汇总数值没有给出精确表号和标准差，正式论文引用应回到 arXiv v1 表 1／表 7。

## 文献信息

- arXiv 论文：<https://arxiv.org/abs/2505.18551>
- ICLR 2026 会议入口：<https://iclr.cc/virtual/2026/poster/10011850>
- 官方项目：<https://iqsec-lab.github.io/LAMDA/>
- 官方代码：<https://github.com/iqsec-lab/lamda>
