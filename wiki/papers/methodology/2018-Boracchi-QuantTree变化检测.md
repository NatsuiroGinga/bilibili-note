---
title: "QuantTree：多变量数据流变化检测直方图"
authors: [Giacomo Boracchi, Diego Carrera, Cristiano Cervellera, Danilo Macciò]
year: 2018
date: 2026-08-11
journal: "ICML 2018"
source_pdf: "[[raw/papers/methodology/2018-Boracchi-QuantTree-Change-Detection.pdf]]"
tags: [变化点检测, 数据流, 非参数检验, 类型/论文]
key_finding: "用递归二分构造基线等概率直方图区间，使检验统计量在稳定期不依赖未知多变量分布并可校准假阳性率。"
---

# QuantTree：多变量数据流变化检测直方图

## 全文核验结论

QuantTree 从稳定训练样本构造有限个自适应直方图区间，设计使区间概率不依赖未知基线分布；Pearson或总变差统计量的阈值可用合成单变量数据校准。证据位于 PDF 第1至5页。

## LSPR 角色

可监控无标签 RWKV 状态或分数分布是否改变，并作为是否切换 M2 校准器的诊断。它本身不学习攻击排序，也不生成攻击标签。

## 最小证伪与边界

在已知时间断点前后报告平均运行长度、误报与检测延迟，再检查触发是否改善预算决策。若只检测到采集规模变化且不改善目标告警，降级为日志诊断。其机制与已否决 C12 漂移触发空间高度重叠，不作为主创新。

## 证据记录

- 全文状态：完成逐项核验。
- 官方来源：PMLR 80:639–648。
- Zotero：`TB75VQBZ`。
- 课题角色：变化检测强基线，不入前三主路线。
