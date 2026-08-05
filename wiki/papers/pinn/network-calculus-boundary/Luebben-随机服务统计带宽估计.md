---
title: "随机服务网络中的统计带宽估计"
authors: [Ralf Lübben, Markus Fidler, Jörg Liebeherr]
year: 2014
date: 2026-07-30
journal: "IEEE/ACM Transactions on Networking"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2014-Luebben-Stochastic-Bandwidth-Random-Service.pdf]]"
key_finding: "平均可用带宽会系统性高估短时可用服务，随机服务必须按时间尺度和违约概率刻画，且突发交叉流量会显著增加所需观测长度。"
tags: [PINN, 网络演算, 随机服务, 不确定性, 类型/论文]
aliases: [Luebben2014, Stochastic Bandwidth Random Service]
---

# 随机服务网络中的统计带宽估计

## 一句话

期刊版本进一步证明“平均服务率”不能替代短窗口服务下界，这直接否决 R3 用全局均值速率构造物理真值。

## 方法与证据

- PDF 第 4 页说明长时可用带宽会忽略系统时延并高估短时服务。
- PDF 第 6 页证明期望意义的量会系统性高估实际离开过程。
- 受控实验使用多次 UDP 探测并报告时延分位数和 0.95 置信区间；突发重尾交叉流量需要更长包列。

## 本课题裁决

R3 应在多个窗口尺度分别预测有效服务下界，并以校准覆盖率控制保守程度。任何仅用 `bytes / duration` 的单点服务率都只能作为弱基线，不能称网络演算保证。

## 文献信息

- DOI: https://doi.org/10.1109/TNET.2013.2261914
- Zotero: `N58M62XU`
