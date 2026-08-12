---
title: "IDP-code/TrafficFormer：流量预训练模型代码仓库"
authors:
  - IDP-code（作者身份未在仓库标明）
year: 2025
date: 2026-08-08
journal: "GitHub 代码仓库"
resource_type: 代码仓库
url: "https://github.com/IDP-code/TrafficFormer"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 代码仓库
  - TrafficFormer
  - 加密流量
key_finding: "MIT 许可、torch==2.0.1 钉死、最后提交 2025-01-18 后停更；README 不含论文引用与会议信息，代码自述基于 ET-BERT 与 UER-py，权重仅 Google Drive。"
---

# IDP-code/TrafficFormer

## 一句话

ET-BERT 的衍生实现，工程上更新，但学术归属与维护状态都不清晰。

## 实测事实（GitHub API + README + requirements.txt，核验日期 2026-08-08）

- 许可证 `MIT`（SPDX 确认）。
- 最后提交 2025-01-18T02:09:53Z，信息 `Update README.md`；此后停更约 19 个月；未归档；Stars 108；仅 8 次提交。
- `requirements.txt` 关键钉死项：`torch==2.0.1`、`torchvision==0.15.1`、`scapy==2.5.0`、`flowcontainer==7.2`、`numpy==2.1.2`、`scikit_learn==1.3.1`、`sentencepiece==0.1.99`。
- **torch 2.0.1 与 numpy 2.1.2 组合本身可疑**：torch 2.0.1 早于 NumPy 2.0 ABI 变更，二者同装通常报 `_ARRAY_API not found`。该依赖清单大概率未经完整验证（推论，需实测）。
- 权重分发：Google Drive 单链接。数据：不提供成品数据集，需用户自行从 pcap 生成。
- 输入形态：pcapng/pcap → burst 数据集 → bigram 十六进制表示，按流组织。
- README 明确自述基于 ET-BERT 与 UER-py；**未给出对应论文、会议或 arXiv 编号**。

## 与本课题的关系

- 与 ET-BERT 同属"字节 bigram 语言化"路线，对本课题主要价值是基线复现，不是骨干候选。
- 依赖钉死 torch 2.0.1，与 RTX 5090 需要的 CUDA 12.8+ 不兼容，须整体升级（阻塞项）。

## 待验证

- 对应论文与发表venue（README 未标；外部常见说法是 IEEE S&P 2025 的 TrafficFormer，但本次核验未在仓库内找到任何引用，**标为待验证，不得直接写入论文**）。
- torch 2.0.1 + numpy 2.1.2 是否真能共存（待验证，需实测）。
- Google Drive 权重链接有效性（待验证）。
