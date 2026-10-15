---
schema: paper-note-search/v1
title: "Uncertainty-Driven Hierarchical Sampling for Unbalanced Continual Malware Detection with Time-Series Update-Based Retrieval"
title_zh: "UGSR：不确定性驱动分层采样与时序更新检索的非平衡持续恶意软件检测"
authors: [Yi Xie, Ziyuan Yang, Yongqiang Huang, Yinyu Chen, Lei Zhang, Liang Liu, Yi Zhang]
year: 2025
date: 2026-10-15
journal: "arXiv 2509.07532v1（2025-09-09，IEEE 期刊格式预印本）"
doi: null
arxiv_id: "2509.07532"
evidence_level: "本地全文（MinerU extract）"
source_pdf: "[[raw/papers/attack-detection/lamda-related/2025-Xie-不确定性驱动分层采样-非平衡持续恶意软件检测.pdf]]"
tags:
  - Android恶意软件
  - 持续学习
  - 主动学习
  - 类不平衡
  - 回放
  - 类型/论文
tasks: [Android恶意软件二分类, 持续学习, 主动学习, 类不平衡回放]
datasets: [APIGraph, AndroZoo]
methods: [分层不确定性采样, Dempster-Shafer 证据多分类器, 类平衡 codebook 检索, ETF 特征正则, memory bank 回放]
metrics: [TPR, TNR, F2, G-mean, mACC]
key_finding:
  - "UGSR 在月标注预算 50 的严格低标签条件下取得 TPR 92.95%、mACC 94.26%（摘要、§IV.E）；同预算下 Chen-AL（USENIX23）基线偏向良性多数类。"
  - "「标什么」由固定预算 B=50/月 的分层不确定性采样（μB 多分类 + (1−μ)B 二分类，μ=0.5，另设 10% 良性配额下限）决定；「存什么」是已标注样本累积入 memory bank M（微调用其中约 20%），检测端另设每类 top-50 嵌入的类平衡 codebook——两者是同一框架内两个机制，但预算只压在标注侧，存储侧非固定预算、非联合配置量。"
supports: [固定标注预算+类不平衡+持续恶意软件检测的组合已存在直接近邻, 标注选择与存储选择可作为同框架内两个分离机制]
cannot_support: [双预算联合配置已被研究, 极端正例稀缺（0.05% 量级）已被处理, LAMDA Domain-IL 官方协议下的读数]
method: "分层不确定性采样（多分类+二分类双级）→ 专家标注 → memory bank 累积 → 双模块微调；检测时类平衡 codebook 相似检索 + ETF 正则"
baseline: "Chen-AL/USENIX23（对比损失+主动学习）、CADE OOD 分数选样、pseudo-loss 选样"
aliases:
  - UGSR
  - Xie2025-UGSR
related:
  - "[[2025-Haque-CITADEL半监督主动漂移适应]]"
  - "[[2026-Amalapuram-SEED预算半监督持续检测]]"
  - "[[2023-Chen-Android恶意软件持续学习]]"
---

# UGSR：不确定性驱动分层采样的非平衡持续恶意软件检测

> 页码锚点：按 MinerU 保留的章节号（§I–§V）与算法 1、表 I–IV 引用。证据等级：本地全文（`mineru-open-api extract`，PDF 11 页转出 516 行 Markdown）。

## 一、协议与预算（与待核任务逐项对照）

- **标注预算**：§IV.E「We apply a monthly budget of 50 samples for analyst labeling to ensure a fair comparison across all methods.」算法 1 第 22–26 行：B 为 sample budget，选 μB 多分类不确定 + (1−μ)B 二分类不确定（式 15，μ=0.5），并在良性欠代表时以 10% 良性配额替换低分恶意样本。另设 few-shot 变体预算 Count=2/10（表 III/IV）。
- **存储机制**：被选样本由专家标注后「added to the memory bank M」；学习阶段「combines the currently selected samples D′_n with part of the historical data, M, from the memory bank (usually 20%)」微调。M 随月度标注累积，**论文未给 M 设固定容量或替换策略**。检测端 codebook V「only the top 50 representative benign and malware embeddings」，是唯一有界存储结构。
- **类不平衡**：核心动机之一。两数据集良性:恶意约 9:1（§IV.A）；论点是不确定性选样天然偏向良性多数类（§I、§II.A）；对策是分层平衡采样 + 加权 BCE（式 10 w-bce）。
- **协议**：APIGraph 2012–2018、AndroZoo 2019–2021 的月度流式持续学习；**非 LAMDA、非 Domain-IL 官方协议、无每年度 10 轮/批 1024/缓冲 200 的设定**。
- **与持续学习的关系**：就是 CL 框架（static → continual → test 三阶段），采样与检索都在 CL 内。

## 二、与目标任务的差量（逐项）

| 维度 | 目标任务 | UGSR |
| --- | --- | --- |
| 标注预算 | 固定 | 固定（50/月，另有 2/10 few-shot） |
| 存储预算 | 固定（缓冲 200） | **不设固定容量**；仅 codebook top-50/类有界 |
| 双预算联合配置 | 是（同一配置问题） | 否——两个机制并置，无联合优化/配置 |
| 正例稀缺 | 2024 年 1.64%、2025 年 0.05% | 9:1（约 10%），处理但未到极端稀缺 |
| 协议 | LAMDA Domain-IL 官方 | APIGraph/AndroZoo 月度流 |
| 域 | Android 恶意软件 | 同 |

## 三、论文可支持/不可支持

- 可支持：「固定标注预算 + 类不平衡 + 持续恶意软件检测」组合已有直接近邻；分层采样与检索式存储可在同一框架内协同。
- 不可支持：双预算联合配置已存在；极端正例稀缺已解决；LAMDA 协议读数。

## 四、入库与 Zotero

- PDF：`raw/papers/attack-detection/lamda-related/2025-Xie-不确定性驱动分层采样-非平衡持续恶意软件检测.pdf`（1.43 MB，PDF 1.7，8 页正文）。
- 全文转换件：`wiki/papers/attack-detection/lamda-related/2025-Xie-UGSR-不确定性驱动分层采样与非平衡持续恶意软件检测-全文.md`。
- Zotero：本轮未导入（检索代理只做 raw/wiki 入库）。
- OpenAlex 同时命中其 Zenodo 代码件 `10.5281/zenodo.22259088`（Jesse1103/malware-detection）。
