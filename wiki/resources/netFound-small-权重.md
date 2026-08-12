---
title: "snlucsb/netFound-small：netFound 小号预训练权重"
authors:
  - snlucsb (SNL-UCSB)
year: 2026
date: 2026-08-08
journal: "Hugging Face 模型仓库"
resource_type: 模型权重
url: "https://huggingface.co/snlucsb/netFound-small"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 模型权重
  - netFound
  - 流量基础模型
key_finding: "53.4M 参数、MIT 许可、safetensors 格式的最小号 netFound 权重，是本课题唯一可直接商用改造的流量基础模型骨干候选；但下载量仅 128，社区验证薄弱。"
---

# snlucsb/netFound-small

## 一句话

netFound 家族里参数量最小、许可最宽松的公开权重，适合当"注入 RWKV 机制"的低成本消融骨干。

## 实测事实（HF 元数据，核验日期 2026-08-08）

- 参数量 53.4M；架构标识 `netFound`；权重格式 `safetensors`。
- 许可证 `mit`；tags 含 `license:mit`、`region:us`。
- 最后更新 2026-03-09；下载量 128，likes 2。
- 仓库归属 `snlucsb`，与 GitHub `SNL-UCSB/netFound` 同一课题组。

## 与本课题的关系

- 输入形态是原始 PCAP（见 netFound 代码仓库笔记），与本课题"字段交互是主信号"的实测一致：netFound 的分层 Transformer 显式建模 burst 内报文字段。
- 53.4M 规模在 RTX 5090 上做全参微调与机制消融的显存压力最小，适合先做 RWKV 状态核注入的可行性验证。
- MIT 许可对论文开源与后续衍生无阻碍。

## 待验证

- 模型卡未在元数据中给出 hidden size / 层数 / 最大序列长度，需下载 `config.json` 核对（待验证）。
- 预训练语料是否与 LSPR24、TQH-C2 分布重叠、是否存在评测泄漏（待验证）。
- 是否属于 netFound-v2 家族（netFound-640M-base 模型卡称 v1 已被 v2 家族取代，但未点名 small/base/large 归属哪一代）（待验证）。
