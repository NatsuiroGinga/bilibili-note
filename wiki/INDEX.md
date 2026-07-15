---
title: 笔记索引
date: 2026-07-13
tags:
  - MOC
  - 索引
  - 类型/MOC
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

### 网络攻击检测大模型（开题）

王童童·东南大学网安学院·工程硕士开题。方向：**物理信息神经网络 + 课程式强化学习** 的网络攻击检测大模型。初版 H-ORL（流形约束+课程 RL）拟改写为 PINN+课程 RL。

- **研究方向决策**：方案 A（TCP 流体，[[TCP-AQM二维流体模型]]）vs 方案 B（守恒不变量，[[INVARLLM-物理不变量提取]]）——倾向 B，待 IDS2018 字段普查定夺
- **两个创新点**：① PINN 物理信息检测（[[Raissi-PINN开山框架]] 为基）② 物理感知双维度课程式 GRPO（[[GRPO变体群-方法选型]] 为选型池，[[GRPO-RCS]] 为对标）
- **数据集构建**：IDS2018（6.4GB，raw/datasets/）+ 自构造测试床——见 `output/数据集构建章节设计_开题实施计划.md`
- **文献核验**：`output/参考文献核验报告_开题报告改进素材.md`（17 条核验，5 条错误已修正）
- **同门参考**：[[朱焱雷-加密流量博弈对抗与高效训练]]（课程学习+高效训练+原型系统范本）
- **术语体系**：[[开题术语体系]] — PIC-GRPO/CI-PRD 命名决策、命名原则、方向决策、被否候选（论文写作单一术语来源）
- 课题论文笔记全部在 `wiki/papers/attack-detection/`、`wiki/papers/pinn/`、`wiki/papers/grpo/`

---

### 论文阅读

DeepSeek 等团队的论文笔记，按研究方向分类。

> 笔记格式参见 SCHEMA.md「论文类」——frontmatter（作者/年份/DOI/source_pdf）+ 一句话 + 背景演进 + 方法核心 + 实验结果 + 我的理解 + 疑问

| 方向 | 论文 |
|------|------|
| DeepSeek 架构 | **[[mHC]]** — 流形约束超连接（Stiefel+Birkhoff），27B Dense 稳定训练→671B MoE 收益，开销+0.6% |
| | **[[Engram]]** — O(1) n-gram 哈希条件记忆模块，MoE 之外的第二条稀疏化轴线，长文本检索 84→97 |
| LLM 架构/推理 | **[[Multi-Stream LLMs]]** — 多流并行架构（马普所/ETH），TTFT 降 40%+，prompt injection 免疫 |
| | **[[Varnish]]** — Bilibili CDN 缓存感知负载均衡（SIGCOMM'25），命中率不退化+均衡度+24% |
| | **[[GRPO-RCS]]** — GRPO+课程采样意图检测泛化（腾讯PCG+哈工大），SFT 准确率 0%→83%+ |
| 攻击检测应用 | **[[INVARLLM-物理不变量提取]]** — LLM 提取物理不变量做 CPS 异常检测（方案B 支撑，100% 精度零误报） |
| | **[[PIGCRN-化工过程攻击检测]]** — first-principles+拓扑图 PINN（严谨参照，自构造仿真） |
| | **[[数字孪生约束LLM-CPS异常检测]]** — 两级流水线+受约束 LLM 先例（原型系统架构来源） |
| | **[[Minerva-CTI可验证奖励]]** — RLVR 可验证奖励，解初版 `<check>` 奖励作弊 |
| | **[[朱焱雷-加密流量博弈对抗与高效训练]]** — ⭐同门参考，课程学习+高效训练+原型系统 |
| PINN 基础 | **[[Raissi-PINN开山框架]]** — PINN 标准框架（自动微分 PDE 残差损失，JCP 2019） |
| | **[[PINN综述群]]** — 4 篇综述合并，训练优化是核心难题（创新点2 动机） |
| GRPO 变体 | **[[GRPO变体群-方法选型]]** — 16 篇 GRPO 合并，创新点2 方法选型池（含 9 篇作者勘误） |

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
| #方法论 | 1 篇（Obsidian AI 知识库设计原则） |
| #Obsidian | 1 篇（知识库设计原则） |
| #LLM | 5 篇（论文阅读：DeepSeek 架构 / LLM 架构 / 推理） |
| #DeepSeek | 3 篇（mHC + Engram + Varnish） |
| #攻击检测 | 19 篇（attack-detection/：PINN-IDS + GRPO-安全 + 课程式PINN + 同门论文） |
| #PINN | 9 篇（Raissi 开山 + 综述群 + 课程式PINN×3 + PIGCRN/PPINN-FDIA/PI-RF + TCP-AQM×2） |
| #GRPO | 17 篇（GRPO变体群 + GRPO-RCS + SecLoop/漏洞检测/Minerva） |
| #课程学习 | 6 篇（课程式PINN×3 + Feng-RCS + 朱焱雷 + 对抗训练在线理论） |
| #物理信息 | 跨 PINN/攻击检测 多篇（守恒不变量 + first-principles + PINN 框架） |

---

## 维护日历

> 知识库会随时间自然衰减——过时的内容、断裂的链接、新的笔记没有加入 MOC。定期维护是为了让 AI 在进入仓库时始终能看到最新、最全的索引。

| 频率 | 检查项 | 方法 | 下次执行 |
|:----:|------|------|:----:|
| **月** | 孤岛笔记 | Obsidian 图谱视图 → 过滤「孤立节点」，确认是否应在某 MOC 中引用 | 2026-08-13 |
| **月** | 断裂链接 | Obsidian 设置 → 文件与链接 → 检查断裂链接 | 2026-08-13 |
| **季** | 过时内容 | 扫描 `date` 字段超过 6 个月的笔记，更新或标记 `#待更新` | 2026-10-13 |
| **季** | MOC 完整性 | 检查每个域 MOC 是否覆盖了该域所有笔记（`fd -e md` 对比 MOC 的 `[[链接]]` 列表） | 2026-10-13 |
| **季** | 重复笔记 | 确认没有内容高度重叠的笔记，如有则合并并用 `aliases` 保留旧标题作为别名 | 2026-10-13 |
| **半年** | 标签体系审核 | 检查 `类型/` 和主题标签是否有新生/废弃的维度，清理无效标签 | 2027-01-13 |
| **每篇新笔记** | 入链检查 | 新笔记创建后确认至少被一个 MOC 或相关笔记引用 | 即时 |
