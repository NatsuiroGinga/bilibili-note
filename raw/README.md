---
title: raw 层说明
date: 2026-07-14
tags:
  - 类型/参考
  - raw
---

# raw 层 — 源材料

## 规则

**只增不改。** raw/ 下的所有文件是知识的源头——PDF 原文、原始数据、外部导出文件。它们的价值在于**保持原貌**，不能被后续编辑覆盖。

- ✅ 新增源材料（放入 PDF / 文件）
- ❌ 修改已有源材料的内容
- ✅ 可以重命名使文件名更清晰
- ❌ 删除（除非确认是误入的无关文件）

## 当前内容清单

`raw/papers/` 按研究方向分子目录组织。Obsidian wikilink `[[文件名.pdf]]` 按文件名全局解析，子目录移动不影响链接。

### raw/papers/attack-detection/ — 网络攻击检测课题（PINN + 课程式 RL）

| 文件 | 主题 | wiki 笔记 | 状态 |
|------|------|:----:|:----:|
| `2211.10833.pdf` | TCP/AQM 二维流体模型（方案 A 根基） | [[TCP-AQM二维流体模型]] | ✅ 已有 |
| `2411.10918.pdf` | INVARLLM：LLM 提取物理不变量做 CPS 异常检测 | [[INVARLLM-物理不变量提取]] | ✅ 已有 |
| `2604.03790.pdf` | 数字孪生 + 受约束 LLM 做 CPS 异常检测 | [[数字孪生约束LLM-CPS异常检测]] | ✅ 已有 |
| `2601.04443.pdf` | LLM 检测智能电网保护继电器攻击 | [[LLM-智能电网继电器攻击检测]] | ✅ 已有 |
| `2605.15254.pdf` | 课程式 PINN（空间相关） | [[课程式PINN-空间相关]] | ✅ 已有 |
| `2605.19263.pdf` | 课程式 PINN（高斯混合 CGMPINN） | [[课程式PINN-高斯混合]] | ✅ 已有 |
| `2602.06996.pdf` | 课程式 VSR-PINN（双曲 PDE） | [[课程式VSR-PINN-双曲PDE]] | ✅ 已有 |
| `2512.09485.pdf` | SecLoop/SA-GRPO 零触网络安全 | [[SecLoop-SA-GRPO零触网络安全]] | ✅ 已有 |
| `2507.03051.pdf` | GRPO 漏洞检测推理 | [[GRPO-漏洞检测推理]] | ✅ 已有 |
| `2602.00513.pdf` | Minerva：CTI 可验证奖励 RLVR | [[Minerva-CTI可验证奖励]] | ✅ 已有 |
| `2504.13592v2.pdf` | GRPO-RCS 意图检测泛化（初版引文） | [[GRPO-RCS-意图检测泛化]] | ✅ 已有 |
| `2508.17901.pdf` | Stiefel 流形 LoRA 黎曼优化（初版引文，已降级） | [[Stiefel流形LoRA黎曼优化]] | ✅ 已有 |
| `2605.29317.pdf` | FoRA Fisher 正交秩适配（已降级） | [[FoRA-Fisher正交秩适配]] | ✅ 已有 |
| `physics-informed-graph-convolutional-...chemical-process-networks.pdf` | [1] 化工过程 PINN 图卷积攻击检测（I&EC Res 2025） | [[PIGCRN-化工过程攻击检测]] | ✅ 已有 |
| `robust-industrial-iot-...false-data-injection.pdf` | [2] 工业 IoT 并行 PINN 抗虚假数据注入（质量弱，反面教材） | [[PPINN-FDIA-工业IoT]] | ✅ 已有 |
| `Enhancing_Intrusion_Detection_..._Random_Forest.pdf` | [3] 电力网物理信息随机森林（仅特征工程，提升边际） | [[PI-RF-电力网入侵检测]] | ✅ 已有 |
| `Stability_analysis_..._TCP_AQM_networks.pdf` | [17] TCP/AQM 流体模型分岔混沌脉冲控制（WCICA 2010） | [[TCP-AQM流体模型分岔混沌控制]] | ✅ 已有 |
| `朱焱雷.pdf` | 东南大学硕士论文：加密流量博弈对抗防御与高效训练（2026，⭐同门高价值参考） | [[朱焱雷-加密流量博弈对抗与高效训练]] | ✅ 已有 |
| `课程式学习.pdf` | Shi Lianghe《A Closer Look at Curriculum Adversarial Training: From an Online Perspective》(武大, 9 页) —— 课程式对抗训练的在线学习理论分析；文件名易误解（非入侵检测） | [[课程式对抗训练-在线视角]] | ✅ 已有 |

### raw/papers/pinn/ — PINN 基础与综述

| 文件 | 主题 | wiki 笔记 | 状态 |
|------|------|:----:|:----:|
| `1711.10561.pdf` | Raissi PINN 开山预印本 Part I（JCP 2019 引用版） | [[Raissi-PINN开山框架]] | ✅ 已有 |
| `1711.10566.pdf` | Raissi PINN 开山预印本 Part II | [[Raissi-PINN开山框架]] | ✅ 已有 |
| `MDPI-ApplSci-2025-15-8092-PINN综述.pdf` | Ren 2025 PINN 方法演进全景综述 | [[PINN综述群]] | ✅ 已有 |
| `基于物理信息的神经网络：最新进展与展望.pdf` | 李野/陈松灿 中文综述（计算机科学 2022） | [[PINN综述群]] | ✅ 已有 |
| `2501.06572.pdf` | PINN 进化优化综述（Evo-PINN） | [[PINN综述群]] | ✅ 已有 |
| `2410.13228.pdf` | From PINNs to PIKANs（Karniadakis 团队 2024） | [[PINN综述群]] | ✅ 已有 |

### raw/papers/deepseek/ — DeepSeek 架构

| 文件 | 主题 | wiki 笔记 | 状态 |
|------|------|:----:|:----:|
| `2512.24880v2.pdf` | mHC: 流形约束超连接 | [[mHC-流形约束超连接]] | ✅ 已有 |
| `2601.07372_Engram-DeepSeek.pdf` | Engram 条件记忆模块 | [[Engram-条件记忆模块]] | ✅ 已有 |

### raw/papers/llm/ — LLM 架构/推理

| 文件 | 主题 | wiki 笔记 | 状态 |
|------|------|:----:|:----:|
| `2605.12460v1.pdf` | Multi-Stream LLMs 并行多流架构 | [[Multi-Stream-LLMs-并行多流架构]] | ✅ 已有 |

### raw/papers/cdn-ops/ — CDN / Bilibili 运维

| 文件 | 主题 | wiki 笔记 | 状态 |
|------|------|:----:|:----:|
| `atc24-zhang-rui-xiao.pdf` | USENIX ATC'24 论文 | — | ⏳ 待读 |
| `nsdi22-paper-zhou.pdf` | NSDI'22 论文 | — | ⏳ 待读 |
| `Proactive_Video_Push_CDN-P2P_VoD.pdf` | CDN-P2P 主动视频推送 | — | ⏳ 待读 |
| `视频CDN技术.pdf` | 视频 CDN 技术总览（Bilibili） | — | ⏳ 待读 |
| `2401.15839v1.pdf` | Swarm：P2P 视频内容分发 | — | ⏳ 待读 |
| `北斗资源上下线&踢点逻辑.pdf` | 北斗踢点逻辑原始文档 | [[北斗资源上下线及踢点策略技术文档]] | ✅ 已有 |

### raw/papers/methodology/ — 知识库方法论

| 文件 | 主题 | wiki 笔记 | 状态 |
|------|------|:----:|:----:|
| `Obsidian-AI-v1.0.0.pdf` | Obsidian-AI 知识库设计原则 | [[AI 知识库设计原则]] | ✅ 已有 |

### raw/ 根目录 — 开题报告材料

| 文件 | 主题 |
|------|------|
| `Word_基于流形约束与课程式强化学习的网络攻击检测大模型研究_王童童.pdf` | 初版开题报告原件（H-ORL 方向，待改写为 PINN+课程 RL） |
| `网络攻击检测：融合物理信息神经网络与课程式强化学习的创新框架.md` | 改进方案诊断与重构建议 |
| `攻击检测原型系统设计与实现.md` | 原型系统章节素材 |

### raw/datasets/ — 数据集（gitignore，不入版本库）

| 目录 | 内容 |
|------|------|
| `CSE-CIC-IDS2018/` | IDS2018 处理后 ML CSV，10 文件 6.41GB |

> 缺失：Karniadakis 等《Physics-informed machine learning》Nature Reviews Physics 2021 —— 无开放获取版本，待手动获取。

## 与 wiki 层的关系

`raw/` 的每个 PDF 应该在 `wiki/` 中有一篇对应的结构化笔记（`类型/论文`）。
wiki 笔记通过 `source_pdf` 字段指向 raw 原件，建立显式关联。
