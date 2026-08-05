---
title: "随机服务网络的带宽估计基础"
authors: [Ralf Lübben, Markus Fidler, Jörg Liebeherr]
year: 2010
date: 2026-07-30
journal: "arXiv 1008.0050"
source_pdf: "[[raw/papers/pinn/network-calculus-boundary/2010-Luebben-Foundation-Stochastic-Bandwidth.pdf]]"
key_finding: "随机服务可用带违约概率的有效服务曲线估计，但需要多档常速探测、足够长的包列和重复测量，精度与置信度不能由单条被动流量记录免费获得。"
tags: [PINN, 网络演算, 随机服务, 主动探测, 类型/论文]
aliases: [Luebben2010, Foundation Stochastic Bandwidth]
---

# 随机服务网络的带宽估计基础

## 一句话

论文把常速包列的时延分位数转为带违约概率的有效服务曲线，并显式讨论包列长度、探测速率和重复次数。

## 方法与证据

- PDF 第 1 页概括迭代常速探测与自适应包列长度。
- 第 3 节由不同探测速率的稳态时延分位数拼出分段有效服务曲线；增加速率档位也会通过联合界累积违约概率。
- 真实网络并非普遍最小加线性，论文使用统计最大加/最小加系统论收窄主张。

## 本课题裁决

R3 的校准目标应是“服务下界覆盖率/违约率”，而不是仅校准分类置信度。ns-3 必须生成跨速率、跨交叉流量的重复轨迹；单个固定拓扑和单一速率不足以验证该机制。

## 文献信息

- arXiv: https://arxiv.org/abs/1008.0050
- Zotero: `9CEVSMMQ`
