---
title: "Varnish: Cache-Aware Load Balancing for CDN Edge Proxies in Telco Networks"
authors:
  - Zhihao Zhang
  - Rui Zhang
  - Wenlong Li
  - Zizhao Wang
  - Haiyang Jiang
  - Yujun Gao
  - Xu Zhang
year: 2026
date: 2026-07-14
journal: ACM SIGCOMM 2025 / arXiv preprint
doi: "arXiv:2504.13592"
source_pdf: "[[raw/papers/2504.13592v2.pdf]]"
tags:
  - CDN
  - 负载均衡
  - 缓存
  - 电信网络
  - 边缘计算
  - 类型/论文
aliases:
  - Varnish
  - 缓存感知负载均衡
  - Zhang2025-Varnish
key_finding: "提出 Varnish 缓存感知负载均衡方案，通过维护边缘节点的缓存内容视图（Cache View），在保持高缓存命中率的前提下将负载均衡度提升 24%，跨节点请求转发开销降低 83%。已在 Bilibili 生产 CDN 部署验证"
method: "Cache View（节点缓存内容视图）+ 一致性哈希 + 两层决策（PDP/RL 在线学习用于流量分配 + LPM 节点级判断用于请求转发）"
baseline: "Random（随机分配）、Consistent Hashing（一致性哈希）、Weighted RR（加权轮询）"
---

# Varnish: Cache-Aware Load Balancing for CDN Edge Proxies in Telco Networks

> Zhihao Zhang, Rui Zhang, Wenlong Li 等 · ACM SIGCOMM 2025（短文，4页）· v2: 2026-04

---

## 一句话

在电信 CDN 边缘代理之间，不仅要看谁有空闲算力（传统负载均衡），还要看谁缓存了这个内容——Varnish 维护每个节点的 Cache View，在缓存命中率和负载均衡之间做最优权衡。已部署在 Bilibili CDN。

---

## 背景：CDN 边缘负载均衡的困境

### 电信 CDN 的架构特点

```
用户请求 → CDN 边缘代理（多个节点）
              ├── 节点 A：缓存了内容 X（命中！）
              └── 节点 B：没缓存 X → 需要从上游拉（慢 + 上游压力）
```

传统负载均衡只看节点的 CPU、带宽、连接数等资源指标——谁空闲就分给谁。但 CDN 场景下有一个关键因素被忽略了：**缓存状态**。

### 不看缓存的代价

| 场景 | 传统 LB 行为 | 后果 |
|------|------------|------|
| 节点 A 缓存了内容 X，但负载高 | 请求分到节点 B（有空闲） | 节点 B 需要从上游拉内容 → 延迟增加 + 上游带宽浪费 |
| 节点 A 没缓存内容 X | 请求分到节点 A | 同样需要从上游拉 |

**核心矛盾**：缓存命中率和负载均衡是**天然冲突**的两个目标——把请求都发给有缓存的节点会过载它，均匀分散请求又会降低缓存命中率。

---

## 方法：Varnish 的三层设计

### 整体架构

```
                  ┌──────────────────────┐
                  │   CDN 负载均衡器      │
                  │   (PDP/RL Online)    │
                  └──────┬───────────────┘
                         │ 做出"分给哪个节点"的决策
                         ▼
              ┌──────────────────┐
              │  边缘代理 节点    │
              │  (LPM 判断)      │
              │  ├── 命中 → 直接服务
              │  └── 未命中 → 转发给有缓存的兄弟节点
              └──────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │   Cache View     │  ← 核心数据结构
              │   每个节点维护    │
              └──────────────────┘
```

### 第一层：Cache View——节点缓存内容视图

这是 Varnish 的核心创新。每个边缘节点维护一个轻量级的 **Cache View**（缓存视图）：

- **内容**：本节点缓存了哪些内容 URL 的摘要
- **大小**：使用 Bloom Filter 压缩，内存开销极低
- **更新**：随缓存增删实时更新

### 第二层：PDP/RL 在线学习——决定流量如何分到各节点

负载均衡器使用 **策略决策过程（PDP）** 或 **强化学习（RL）** 来做流量分配决策：

- **输入**：各节点的 Cache View + 当前负载（CPU、带宽、连接数）
- **输出**：请求 X 应该发给节点 Y
- **目标**：最大化缓存命中率的同时，保持各节点负载均衡

### 第三层：LPM（Local Proxy Manager）——节点级的请求转发

如果一个请求分到了节点 A，但节点 A 没缓存这个内容：

1. 节点 A 查 Cache View：哪个兄弟节点有这个内容的缓存？
2. 如果兄弟节点 B 有：**直接转发给 B**（节点间转发），由 B 直接服务
3. 如果都没有：从上游拉取

这个设计的关键是：**负载均衡器做粗粒度决策（哪个节点负责哪类流量），LPM 做细粒度转发**。两层分工明确，避免了负载均衡器需要实时感知缓存变化的复杂性问题。

---

## 实验结果

论文是 SIGCOMM 短文（4 页），实验部分相对精简但直接切中生产指标：

| 指标 | 传统 LB（随机 + 一致性哈希） | Varnish | 改善 |
|------|:--:|:--:|:--:|
| 负载均衡度 | 基线 | 提升 | **+24%** |
| 跨节点转发开销 | 100% | 17% | **-83%** |
| 缓存命中率 | 基线 | 持平或略优 | 不退化 |

### 生产部署

论文声称已在 **Bilibili CDN 生产环境**中部署 Varnish。这是一个关键信号：论文的核心方法不只在模拟器中有效，而是经受了实际电商/视频流量的检验。

---

## 我的理解

这篇论文解决了一个 CDN 领域长期存在但一直被绕过的问题：**缓存和负载均衡是矛盾的，但之前没人系统性地解决这个矛盾**。

传统方案的选择其实就两种：

1. **一致性哈希**：把相同 URL 的请求固定到一个节点 → 缓存命中率高 → 但热点内容会过载该节点
2. **随机/加权轮询**：均匀分散请求 → 负载均衡 → 但缓存命中率掉到地板上

Varnish 的方案是第三条路：**保留一致性哈希作为基础映射，但在节点间加入了"互相帮助"机制**——当节点 A 有缓存但负载高时，可以不把请求发给 A，而是发给有空闲的节点 B，然后 B 发现自己没缓存时，通过 Cache View 找到 A 并转发给 A。

这相当于在负载均衡层增加了一个**缓存感知的维度**。类比：传统 LB 只看谁有空位（资源指标），Varnish 的 LB 还看谁有货（缓存索引）。机场柜台分配类似——不是派人去最短的队，而是如果你有行李要在柜台 X 处理，即使 X 队更长也应该去 X。

**值得注意的细节**：Cache View 用 Bloom Filter 实现，内存开销极低但有一定假阳性率（Bloom Filter 说"有缓存"但实际没有）。在 CDN 场景下假阳性的代价很小——不过是多一次节点间转发（反正比从上游拉快得多），但假阴性（Bloom Filter 说"没缓存"但实际有）的代价是被迫上游拉取。Bloom Filter 的参数选择应该偏向避免假阴性，论文是否讨论了这个细节值得确认。

**与你现有笔记的关系**：这篇论文直接涉及 GO-OP 中 MCDN 节点的调度逻辑（[[北斗资源上下线及踢点策略技术文档]] 中提到的调度器线路可用率策略）。Varnish 的 Cache View 思想可以用于改进 MCDN 内部节点间的请求分配策略。

---

## 与相关工作的关系

- **一致性哈希**（Karger et al. 1997）：Varnish 的基础映射方式
- **CDN 请求路由**（Akamai、Cloudflare 的 DNS-based routing）：传统方法，无缓存感知
- **Bilibili MCDN 和北斗调度系统**：这篇论文直接部署在 Bilibili CDN 生产环境，与该 vault 中的运维知识高度相关
- **Bloom Filter**（Bloom 1970）：Cache View 的实现基础，权衡空间效率和正确率
- **SIGCOMM 2025 简短论文**：4 页格式意味着核心 idea 被会议认可但实验深度受限

---

## 疑问 / 待验证

- Bloom Filter 的假阳性率在多大节点规模下会开始显著影响性能？论文是否给出了推荐的 BF 参数（bits per element、hash 函数数量）？
- PDP/RL 的在线学习收敛速度如何？CDN 流量有强烈的时间模式（晚高峰 vs 深夜），模型是否能快速适应？
- 跨节点转发引入了额外的网络延迟——在节点间跨机房或跨地域的场景下，这个延迟是否可接受？
- 论文只比较了随机/一致性哈希/加权轮询，但没有对比 WRR + 主动缓存预热的方案（即在负载均衡层面配合缓存预热来减少冷启动）
- 从 Bilibili CDN 的生产部署经验来看，Cache View 的更新延迟（缓存增删 → Bloom Filter 更新 → 同步到 LB）在多大规模下会成为瓶颈？

---

## 原始摘要

> Current CDN load balancing approaches in telco networks overlook cache states, which leads to poor cache hit ratios and inefficient resource utilization. In this paper, we propose Varnish, a cache-aware load balancing scheme for CDN edge proxy deployments in telco networks. Varnish introduces a Cache View to maintain consistent, lightweight view of cached contents across distributed edge proxies. A two-tier decision architecture operates in tandem: a Policy Decision Process (PDP) that uses reinforcement learning for intelligent traffic distribution, and a Local Proxy Manager (LPM) that handles forwarding and retrieval of uncached content. Extensive simulations and real-world deployment in Bilibili's production CDN demonstrate that Varnish improves load balancing by 24% while reducing cross-node request forwarding overhead by 83% compared to existing L4/L7 load balancing schemes.

---

## 文献信息

- arXiv: [2504.13592](https://arxiv.org/abs/2504.13592)（v2: 2026-04）
- 会议：ACM SIGCOMM 2025（短文）
- 页数：4 页
