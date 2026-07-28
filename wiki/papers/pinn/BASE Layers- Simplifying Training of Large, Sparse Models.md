---
title: "BASE Layers: Simplifying Training of Large, Sparse Models"
date: 2026-07-23
authors:
  - Mike Lewis
  - Shruti Bhosale
  - Tim Dettmers
  - Naman Goyal
  - Luke Zettlemoyer
  - LaTeX with hyperref
year: 2021
journal: "Proceedings of the International Conference on Machine Learning 2021"
source_pdf: [[raw/papers/pinn/2021-Lewis-BASE-Layers.pdf]]
tags:
  - 博弈论
  - PINN
  - 网络异常流量检测
  - 类型/论文
key_finding: "待补充"
---

# BASE Layers: Simplifying Training of Large, Sparse Models

> 论文来源：CrossRef
> 识别文件：raw/papers/pinn/2021-Lewis-BASE-Layers.pdf

## 一句话

The remarkable success of Large Language Models (LLMs) relies heavily on their substantial scale, which poses significant challenges during model deployment in terms of latency and memory consumption. Recently, numerous studies have attempted to compress LLMs using one-shot pruning methods. However, these methods often suffer from considerable performance degradation on complex language understanding tasks, raising concerns about the feasibility of pruning in LLMs. To address this issue, we propose Adaptive Sparse Trainer (AST), a novel and efficient retraining framework tailored for semi-structured sparse models. AST enables models to learn optimal masks during the weight update process without incurring additional computational overhead. Furthermore, we demonstrate that incorporating knowledge distillation significantly improves retraining efficiency and enhances model performance under fixed computational constraints. Additionally, a supplementary set of well-initialized parameters is integrated to further augment the model's efficacy. AST achieves state-of-the-art performance with minimal training cost. When applied to the LLaMA2-7B model, AST reduces the perplexity and zero-shot accuracy gap between dense and 2:4 semi-structured sparse models to 0.6 and 1.16%, respectively, utilizing less than 0.4% of the pretraining tokens and GPU hours. Our work demonstrates the feasibility of deploying semi-structured sparse LLMs and offers a promising alternative for achieving highly compressed models when combined with existing quantization techniques.

## 结构化摘要

### 研究目的

待补充：未解析到稳定段落，建议人工确认

### 模型架构

Models) >> 191 0 obj << /Subtype /XML /Type /Metadata /Length 1757 >> <?xpacket begin=' ' id='W5M0MpCehiHzreSzNTczkc9d'?> <?adobe-xap-filters esc="CRLF"?> <x:xmpmeta xmlns:x='adobe:ns:meta/' x:xmptk='XMP toolkit 2.9.1-13

### 实验数据集

待补充：未解析到稳定数据集描述

### 核心结论

待补充：未解析到稳定结论句

### 参考文献要点

待补充：未提取到可用参考要点

## 元数据补全状态

- DOI：10.1609/aaai.v39i23.34592
- 年份：2021
- 期刊/出版源：Proceedings of the International Conference on Machine Learning 2021
- 全文提取方式：strings
- 缺失字段：无
