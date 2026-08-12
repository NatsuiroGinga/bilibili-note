---
title: "SNL-UCSB/netFound：网络流量基础模型代码仓库"
authors:
  - SNL-UCSB (UC Santa Barbara)
year: 2026
date: 2026-08-08
journal: "GitHub 代码仓库"
resource_type: 代码仓库
url: "https://github.com/SNL-UCSB/netFound"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 代码仓库
  - netFound
  - 流量基础模型
key_finding: "MIT 许可、最后提交 2026-05-15、仍在活跃维护的唯一主流开源流量基础模型全流程仓库；权重走 HF，1.2TB 预训练数据走课题组自建服务器，16GB 样本走 Zenodo。"
---

# SNL-UCSB/netFound

## 一句话

从原始 PCAP 到预训练再到微调的完整开源链路，是本课题工程复用性最强的外部代码基础。

## 实测事实（GitHub API + README，核验日期 2026-08-08）

- 许可证 `MIT`（SPDX 确认）。
- 最后提交 2026-05-15T15:16:00Z，提交信息 `Merge pull request #7 from pommino/fix/empty-pcap`；仓库未归档，仍在维护。
- Stars 40（相对 ET-BERT 669、TrafficLLM 453 明显偏低）。
- 输入形态：**原始 PCAP**，预处理为 tokenized Arrow 格式后训练。分层 Transformer 建模 burst 与 flow 层级，并使用 burst 元数据（到达间隔、每 burst 字节数等）。
- 权重分发：Hugging Face（`snlucsb/netFound-small` / `-base` / `-large`）。
- 数据分发：Zenodo 上 16GB 样本（6000 万流）；完整 1.2TB 预训练集在 `snl-server-1.cs.ucsb.edu/dataset/netfound/`。
- **README 未声明 Python / torch / CUDA 版本要求**（对 RTX 5090 需 CUDA 12.8+ 的兼容性无法从文档判断）。

## 与本课题的关系

- 它的输入形态（原始 PCAP → burst → flow 分层）与本课题三类数据的匹配度最高；"burst 元数据 + 字段"正好对应已测结论"字段交互是主信号（无历史 69.5%、有历史 47.5%）"。
- MIT + 活跃维护 + HF 权重，是唯一同时满足"可复现、可改造、可发布"的候选。
- 分层结构给 RWKV 状态注入提供天然位置：burst 内保留 attention 做字段交互，burst 间换成 RWKV 递归状态。这与"有效历史仅约 4 窗"的实测不冲突（跨 burst 需要的记忆本来就短）。

## 待验证

- 依赖的 torch/CUDA 版本与 5090（sm_120）兼容性（阻塞判断，需 clone 后读 `requirements.txt` / `pyproject.toml` 实测，待验证）。
- Zenodo 16GB 样本的具体 DOI（README 未在抓取内容中给出）（待验证）。
- 1.2TB 数据的下载可达性与是否需申请（待验证）。
