---
title: 笔记索引
date: 2026-07-13
tags:
  - MOC
  - 索引
aliases:
  - 主页
  - Home
  - Index
---

# Bilibili CDN 基础设施运维笔记

## 项目域

### go-op — 运维平台后端

Bilibili 运维平台 Go 微服务项目，负责 MCDN 节点上下线（踢点）、调度分发、运维门户。

- **[[go-op MOC|项目架构与核心知识]]** — 域入口，架构、服务、配置、常用命令
- **[[北斗资源上下线及踢点策略技术文档]]** — 踢点/恢复/熔断/线路可用率完整策略（基于代码分析）
- **[[mysql|msg_data_all 表知识库]]** — MySQL 表结构、索引、性能注意事项

#### 设计文档

| 主题 | 笔记 |
|------|------|
| 丢包率监控 | **[[mcdn-packet-loss-design\|丢包率指标与告警]]** → **[[2026-07-08-mcdn-cross-isp-ping\|跨运营商探测改造]]** → **[[mcdn-cross-isp-ping-change-summary\|改造总结]]** |
| 自动上线 | **[[autoonline-v-packetloss-strategy\|区分 v 机器丢包率场景]]** |
| 线路可用率 | **[[line-availability\|MCDN 线路可用率]]** |
| 带宽监控 | **[[investigation-plan-reserve-bw-drop\|带宽埋点需求]]** → **[[mcdn_lost_band_prom-delivery\|Prometheus 交付格式]]** |
| 性能优化 | **[[msgdata查询性能问题排查与修复总结\|msgdata 查询性能修复]]** |

#### CPU 高负载排查

> 核心结论：回源带宽 ↑ → si↑ + bvc↑ → CPU busy > 80% → 下线

- **[[MCDN CPU 高负载机器总览\|六台机器总览]]** — 历史对比 + 实时状态 + 根因分析
- **[[checkstatus-design\|checkStatus CPU 健康检查方案]]** — 基于 MCDN 资源 API 的恢复前 CPU 检查
- 单机分析：
  - [[CPU 分析 - v-1169 (jstz 电信)|v-1169]] — bvc 16.8核 + si 53.8%，blink_collect 已修
  - [[CPU 分析 - v-1109 (jstz 电信)|v-1109]] — busy 92.7%，已触发下线
  - [[CPU 分析 - v-1125 (jstz 电信)|v-1125]] — 重新上线后仍暴冲，回源带宽暴冲验证
  - [[CPU 分析 - v-337 (hbwh 电信)|v-337]] — check.miku.stat 45个 + md5sum 38个待清理
  - [[CPU 分析 - v-344 (hljqqhe 电信)|v-344]] — octopus-local 38个 + bvc 暴涨 4.8x
  - [[CPU 分析 - v-308 (jsnj 电信)|v-308]] — 7 次下线，ss/docker/python 非业务进程

---

### te（bili-tellurium）— 网络遥测

从 Prometheus 采集指标，流水线模式（Collection → Data Cube → Intent Model → Action）做自动化决策。

- **[[te MOC|项目架构与核心知识]]** — 域入口，架构、构建、测试、开发任务
- **[[bili-tellurium 版本历史|CHANGELOG]]** — 版本历史

#### 设计文档

- **[[MCDN 带宽利用率水位线检测设计\|水位线检测]]** — mcdn 独立阈值 (70%)，直发企微告警
- **[[双通道配置版本巡检告警设计\|双通道配置巡检设计]]** → **[[dual-channel-config-version-check-plan\|实现计划]]** — 点直播兜底 SDK 配置一致性格检查

---

### 论文阅读

DeepSeek 等团队的论文笔记，按研究方向分类。

> 笔记格式：frontmatter（作者/年份/DOI/tags）+ 一句话 + 背景演进 + 方法核心 + 实验结果 + 我的理解 + 疑问

- **[[mHC]]** — DeepSeek 提出的流形约束超连接（Stiefel + Birkhoff），27B Dense 稳定训练 → 671B MoE 实际收益，额外开销仅 0.6%

---

### 方法论

知识库本身的设计哲学和工作流优化。

- **[[AI 知识库设计原则]]** — Obsidian-AI 知识库设计方法论（58 页）：原子化笔记、MOC 分层、frontmatter 规范、AI 友好的双向链接、定期维护、新式笔记范式

---

## 标签索引

| 标签 | 相关笔记 |
|------|---------|
| #MOC | 3 篇（本页、go-op MOC、te MOC） |
| #go-op | go-op 域全部笔记 |
| #te | te 域全部笔记 |
| #MCDN | 跨域笔记（go-op + te） |
| #CPU | 7 篇 CPU 排查笔记 |
| #北斗 | 1 篇踢点策略 |
| #丢包率 | 3 篇（监控 → 改造 → 总结） |
| #带宽 | 3 篇（埋点 → 交付 → 水位线） |
| #MySQL | 2 篇（知识库 → 性能修复） |
| #配置巡检 | 2 篇（设计 → 计划） |
| #深度学习 | 1 篇（mHC 架构设计） |
| #DeepSeek | 1 篇（mHC） |
| #方法论 | 1 篇（Obsidian AI 知识库设计原则） |
| #Obsidian | 1 篇（知识库设计原则） |
