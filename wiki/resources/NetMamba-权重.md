---
title: "wangtz/NetMamba：NetMamba 预训练权重"
authors:
  - Tongze Wang 等
year: 2024
date: 2026-08-08
journal: "Hugging Face 模型仓库"
resource_type: 模型权重
url: "https://huggingface.co/wangtz/NetMamba"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 模型权重
  - NetMamba
  - 状态空间模型
key_finding: "仓库只有一个 26.19MB 的 pre-train.pth（约 6.5M 参数量级），无任何许可证声明，无下载量统计；是最轻的线性复杂度流量模型权重，但法律状态与参数量都未标明。"
---

# wangtz/NetMamba

## 一句话

ICNP 2024 NetMamba 的唯一公开检查点，体量极小且许可证空白。

## 实测事实（HF 文件列表与元数据，核验日期 2026-08-08）

- 仓库文件仅三个：`.gitattributes`(1519B)、`README.md`(276B)、`pre-train.pth`(26,188,650 B ≈ 26.19MB，LFS)。
- **无 license 标签**，tags 为 `network` `mamba` `netmamba` `mae` `en` `arxiv:2405.11449`。
- likes 4；HF 元数据**未给出参数量**，也未显示下载量。
- 最后更新 2024-08-13。
- 权重为 `.pth`（PyTorch pickle），非 safetensors——加载时存在反序列化执行风险，须用 `weights_only=True`。

## 与本课题的关系

- NetMamba 是"线性复杂度序列模型 + 流量"的最直接前例，是本课题 RWKV 路线的正面对照：若 Mamba 已能吃下流量长序列，需说明 RWKV-7 的状态更新为何更适合。
- 26MB 权重意味着骨干极小，"基础模型"名义与实际容量不匹配，可作为论文中"现有流量基础模型规模不足"的证据点之一（需先核对参数量再写入正文）。
- 无许可证 = 默认保留全部权利，衍生发布有法律风险。

## 待验证

- 从 `pre-train.pth` 实测参数量（26.19MB / fp32 ≈ 6.5M 参数，为推论，需实际加载求和确认）。
- 掩码自编码（MAE）预训练目标的具体掩码率：README（GitHub）给出 `--mask_ratio 0.9`，但权重是否用该配置产出（待验证）。
- 许可证需向作者确认（阻塞项）。
