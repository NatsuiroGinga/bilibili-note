---
schema: paper-note-search/v1
title: "Drift Forensics of Malware Classifiers"
title_zh: "恶意软件分类器的漂移取证"
authors: [Theo Chow, Zeliang Kan, Lorenz Linhardt, Lorenzo Cavallaro, Daniel Arp, Fabio Pierazzi]
year: 2023
date: 2026-09-08
journal: "16th ACM Workshop on Artificial Intelligence and Security（AISec 2023），197–207"
doi: "10.1145/3605764.3623918"
arxiv_id: null
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/lamda-related/2023-Chow-Drift-Forensics-Malware-Classifiers.pdf]]"
tags: [Android恶意软件, 概念漂移, 漂移取证, 可解释性, 家族演化, 类型/论文]
aliases: [Drift Forensics, Chow2023-DriftForensics]
tasks: [Android恶意软件二分类, 漂移根因分析]
datasets: [Transcendent Android malware dataset]
methods: [线性SVM, Oracle对照, Gradient乘Input, 家族分面]
metrics: [F1, Recall, 特征权重]
key_finding:
  - "在 2014–2018 Transcendent 数据上，Dnotua 与 Airpush 两个家族解释了主要性能坠落，说明总体漂移可由少数家族组成变化主导。"
  - "良性样本的总体影响较小，但具体良性特征与恶意家族特征重叠仍会改变分类边界。"
supports: [家族组成和家族内特征演化是Android漂移的重要分面, Oracle差值可用于事后根因定位]
cannot_support: [部署时无标签漂移检测, LAMDA上的相同家族结论, 用最终测试Oracle选择生产机制]
related: ["[[2026-Haque-LAMDA-Android恶意软件长期漂移基准]]", "[[2019-Pendlebury-TESSERACT时空实验偏置与AUT]]"]
---

# Android 恶意软件分类器漂移取证

> 页码锚点：PDF 物理第 1 页摘要给出两家族主导结论；数据与三项研究问题见第 4–5 页附近，MinerU 快速提取已完成。

- 原件 SHA-256：`8d81cf75d27eaae8bbd92ff1feaa84eaae5bd937d94a92bfd5d0d823c10c4752`。
- Zotero：条目键 `H4HNRY22`，题录已导入，未自动附加 PDF。

## 一句话

论文不直接提出在线适应器，而是用含当前测试月一半样本的 Oracle 分类器定位性能拐点，再沿家族和特征解释追查漂移根因。

## 方法与结果

- 数据为 Transcendent 的 2014–2018 Android APK，重扫 VirusTotal 并用 AVClass2 得到 177 个家族；主分析保留最大 5 个家族。
- `C_Base` 只用最初 6 个月；`C_1` 额外看到目标月一半良恶样本；`C_2` 只额外看到目标月恶意样本。Oracle 只用于事后取证，不是部署模型。
- Dnotua 与 Airpush 是最主要的性能坠落驱动；例如 `googletagmanager.com` 出现在 88.6% Dnotua 和 37.15% 良性样本中，说明共享静态特征会改变边界。
- Airpush 的关键特征随月份显著变化，而 Revmob 的主导域名特征相对稳定，支持“家族组成漂移”和“家族内演化”应分开测量。

## 论文可以支持

- Android 时间退化应按家族与良性/恶意特征重叠做根因分面，而不是只看总体 F1。

## 论文不能支持

- Oracle 使用目标月标签，不能进入生产选择或最终测试；五大族结论不能直接外推到 LAMDA 的 1,380 个家族。

## 实验结果与负证据

- 良性总体漂移影响较小，但并非“良性永远稳定”；论文也承认只分析最大 5 个家族，忽略小家族长期尾部。

## 与本课题的关系

- LAMDA 应在源期冻结家族分面后报告家族组成、家族内演化和良恶特征重叠；最终未来年份只用于锁定评价，不用于 Oracle 选机制。

## Evidence Record

Evidence ID: `DRIFT-FORENSICS-E1`
Source: AISec 2023 作者公开全文，DOI `10.1145/3605764.3623918`
Source type: full paper
Supports: 家族组成与家族内演化的漂移根因分面
Contradicts: “总体性能退化天然均匀分布在所有家族”
Method / dataset / metric: Transcendent；Oracle SVM；F1、Recall、特征解释
Limitation: 事后目标月标签；只分析最大五个家族
Project relevance: LAMDA 家族分面与机制资格诊断
Claim strength: strong

## 文献信息

- DOI：https://doi.org/10.1145/3605764.3623918
- 开放全文：https://www.mlsec.org/docs/2023b-aisec.pdf
