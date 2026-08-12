---
title: "ZGC-LLM-Safety/TrafficLLM：面向流量分析的大模型适配框架"
authors:
  - ZGC-LLM-Safety
year: 2025
date: 2026-08-08
journal: "GitHub 代码仓库（arXiv:2504.04222）"
resource_type: 代码仓库
url: "https://github.com/ZGC-LLM-Safety/TrafficLLM"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 代码仓库
  - TrafficLLM
  - 大模型适配
key_finding: "无 LICENSE 文件；基座为 ChatGLM2-6B（兼容 Llama2/GLM4），依赖钉死 transformers==4.30.2 且 torch>=2.0；训练数据 0.4M 流量样本 + 9K 指令全部走 Google Drive；最后提交 2025-11-05。"
---

# ZGC-LLM-Safety/TrafficLLM

## 一句话

把流量当文本喂给通用大模型的代表工作，是本课题"骨干选型"必须正面回应的对照路线。

## 实测事实（GitHub API + README + requirements.txt，核验日期 2026-08-08）

- 许可证：GitHub API 返回 `None`——**无 LICENSE 文件**。
- 最后提交 2025-11-05T17:27:01Z，信息 `Update README.md`；未归档；Stars 453；56 次提交（master 分支）。
- 依赖（requirements.txt 实测）：`transformers==4.30.2`（**钉死在 2023 年 6 月版本**）、`torch>=2.0`（无上界）。未声明 CUDA 版本。
- 基座 LLM：主要 ChatGLM2（6B），另支持 Llama2 与 GLM4。基座权重从 HuggingFace / 官方仓库获取，微调后的检查点走 Google Drive。
- 数据：0.4M 流量样本 + 9K 指令，Google Drive 分发；由 USTC TFC 2016、ISCX Botnet 2014 等公开数据集预处理而来。
- 输入形态：推理时 `Instruction Text + <packet>: + Traffic Data`；训练数据为 instruction/output 的 JSON 对。
- 论文：arXiv:2504.04222，《Enhancing Large Language Models for Network Traffic Analysis with Generic Traffic Representation》（预印本）。

## 与本课题的关系

- 它代表"通用 LLM 骨干 + 流量文本化"这条路线；本课题构思是"取基础模型骨干 + 注入 RWKV 核心机制"，两者骨干选择相近但机制不同，必须在方法论上区分：TrafficLLM 不改动骨干内部算子，本课题要改。
- 6B 基座 + 文本化输入意味着推理成本远高于流量线速要求；已测真实 soho 端点连接率中位 67/h、p90 198/h，可用来论证部署侧的吞吐可行性差异（该对比属本课题自有实测，不来自 TrafficLLM）。
- 训练数据来自 USTC TFC 2016 与 ISCX Botnet 2014，这两个数据集均有公认的捷径问题（时间久远、采集环境单一）。其报告指标不能直接当作能力证据（待验证：需读全文核对评测协议）。

## 负面信息

- 无许可证 + Google Drive 分发 + transformers 钉死在 4.30.2，三项叠加使得完整复现门槛高且法律状态不明。
- `transformers==4.30.2` 与 `torch>=2.0` 组合在 CUDA 12.8 / Blackwell 环境下的可用性未知（ChatGLM2 依赖 remote code，与新版 transformers 不兼容是已知问题）（待验证）。

## 待验证

- 论文的评测协议是否按流/按时间划分，是否存在训练测试同源 pcap（待验证，需读 arXiv:2504.04222 全文）。
- ChatGLM2-6B 权重当前在 HF 上的可得性与许可条款（待验证）。
