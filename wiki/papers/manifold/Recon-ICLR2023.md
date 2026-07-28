---
title: "Recon-ICLR2023"
date: 2026-07-23
authors:
  - 
year: 2023
journal: "ACM Transactions on Storage"
source_pdf: [[raw/papers/manifold/Recon-ICLR2023.pdf]]
tags:
  - 博弈论
  - PINN
  - 网络异常流量检测
  - 类型/论文
key_finding: "待补充"
---

# Recon-ICLR2023

> 论文来源：CrossRef
> 识别文件：raw/papers/manifold/Recon-ICLR2023.pdf

## 一句话

File system bugs that corrupt metadata on disk are insidious. Existing reliability methods, such as checksums, redundancy, or transactional updates, merely ensure that the corruption is reliably preserved. Typical workarounds, based on using backups or repairing the file system, are painfully slow. Worse, the recovery may result in further corruption.
          We present Recon, a system that protects file system metadata from buggy file system operations. Our approach leverages file systems that provide crash consistency using transactional updates. We define declarative statements called consistency invariants for a file system. These invariants must be satisfied by each transaction being committed to disk to preserve file system integrity. Recon checks these invariants at commit, thereby minimizing the damage caused by buggy file systems.
          The major challenges to this approach are specifying invariants and interpreting file system behavior correctly without relying on the file system code. Recon provides a framework for file-system specific metadata interpretation and invariant checking. We show the feasibility of interpreting metadata and writing consistency invariants for the Linux ext3 file system using this framework. Recon can detect random as well as targeted file-system corruption at runtime as effectively as the offline e2fsck file-system checker, with low overhead.

## 结构化摘要

### 研究目的

待补充：未解析到稳定段落，建议人工确认

### 模型架构

待补充：未解析到稳定模型结构描述

### 实验数据集

待补充：未解析到稳定数据集描述

### 核心结论

待补充：未解析到稳定结论句

### 参考文献要点

待补充：未提取到可用参考要点

## 元数据补全状态

- DOI：10.1145/2385603.2385608
- 年份：2023
- 期刊/出版源：ACM Transactions on Storage
- 全文提取方式：strings
- 缺失字段：authors
