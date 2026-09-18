---
schema: paper-note-search/v1
title: "Character Level Based Detection of DGA Domain Names"
title_zh: "基于字符级模型的DGA域名检测"
authors: [Bin Yu, Jie Pan, Jiaming Hu, Anderson Nascimento, Martine De Cock]
year: 2018
date: 2026-09-07
journal: "International Joint Conference on Neural Networks"
doi: "10.1109/IJCNN.2018.8489147"
arxiv_id: null
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2018-Yu-Character-Level-DGA-Detection.pdf]]"
tags: [DGA检测, CNN, RNN, LSTM, 模型比较, 类型/论文]
aliases: [Yu2018, MIT NYU DGA]
tasks: [DGA二分类]
datasets: [Alexa, 多个DGA家族, 约200万域名]
methods: [MIT CNN-LSTM, NYU字符CNN, Endgame LSTM, 字符文本CNN]
metrics: [Accuracy, AUC, 训练时间, 推理时间]
key_finding:
  - "约200万域名上的统一比较显示多种CNN/RNN/LSTM架构准确率差异很小，作者据此偏好更简单、更快且较不易过拟合的架构（PDF物理第1、6至8页）。"
supports: ["MIT和NYU代表字符深度模型谱系", "复杂架构须超过简单字符模型"]
cannot_support: ["时间漂移", "未见家族", "低FPR部署", "现代数据去重"]
related: ["[[2016-Woodbridge-LSTM-DGA检测]]", "[[2020-Drichel-DGA分类器真实适用性]]"]
---

# Yu 等字符级 DGA 模型比较

> 页码锚点：本地PDF共8页；架构见 PDF 物理第2至4页，数据和比较见 PDF 物理第5至8页。

## 一句话

该文定义了 DRIFT 所称 MIT/NYU 的字符 CNN/CNN-LSTM 对照，并说明静态同分布下架构复杂度并未带来明显差异。

## 论文可以支持

- 简单字符 CNN、LSTM、CNN-LSTM 应作为公平基础模型。

## 论文不能支持

- 不能证明任何模型在未来年份、未见家族或低 FPR 下更强。

## 实验结果与负证据

- 静态约200万域名比较，多模型准确率接近。
- 没有跨年、主体隔离、种子方差或对抗规避实验。

## 与本课题的关系

C00 选择不能只看 DRIFT 表 VI；需在冻结 DRIFT 协议下比较轻量 B-ResNet/字符 CNN 与官方双分支。

## 文献信息

- DOI `10.1109/IJCNN.2018.8489147`。
