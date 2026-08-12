---
title: "linwhitehat/ET-BERT：加密流量表示预训练代码仓库"
authors:
  - Xinjie Lin 等
year: 2022
date: 2026-08-08
journal: "GitHub 代码仓库（WWW 2022）"
resource_type: 代码仓库
url: "https://github.com/linwhitehat/ET-BERT"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 代码仓库
  - ET-BERT
  - 加密流量
key_finding: "MIT 许可、最后提交 2026-07-23（六个仓库中最新）、Stars 669 最高；但依赖只声明 torch>=1.1 与 CUDA 11.4，权重仅走 Google Drive 分享链接，长期可得性无保障。"
---

# linwhitehat/ET-BERT

## 一句话

加密流量预训练领域被引用最多的开源基线，仍在维护，但分发方式与依赖声明都很陈旧。

## 实测事实（GitHub API + README，核验日期 2026-08-08）

- 许可证 `MIT`（SPDX 确认）。
- 最后提交 2026-07-23T09:04:52Z，信息 `Fix encoding and update line reading logic`；未归档；Stars 669。
- 依赖声明：`torch >= 1.1`，CUDA 11.4，实验硬件 Tesla V100S。**无上界约束**，实际能否在新版 torch 运行未知。
- 权重分发：Google Drive 单文件链接（`pretrained_model.bin`），README 用 `wget -O` 直接拉 Drive 的 `/view` 链接——该写法对大文件通常失败（需 gdown 或确认码），属于已知的分发缺陷。
- 数据：CSTNET-TLS 1.3，2021 年 3—7 月采自中国科技网，仅发布匿名化数据；其他对比实验用公开数据集。
- 输入形态：pcap → 按 burst 切分 → 十六进制 bigram token；packet 级分类用 `.tsv` 组织。

## 与本课题的关系

- ET-BERT 的 bigram 十六进制 token 化是"把字节当语言"的代表路线，与 netFound 的"字段+元数据分层"路线对立。本课题已测"字段交互是主信号"，更支持后者，这可作为选型依据。
- MIT + 高 star，可作为必备对照基线。
- 数据自 2021 年，TLS 1.3 之后的协议与指纹已漂移，直接引用其数字需注明时效。

## 负面信息

- Google Drive 分发无版本号、无校验和，复现声明脆弱。
- CSTNET-TLS 1.3 为作者自采且仅匿名发布，第三方无法完整复现预训练。
- CUDA 11.4 / V100S 的环境声明与 RTX 5090（需 CUDA 12.8+）之间存在两代硬件差距，需要重建环境（待验证）。

## 待验证

- 在 torch ≥2.7 + cu128 下能否直接运行（依赖声明只有下界，需实测）。
- Google Drive 权重链接当前是否仍可下载（待验证）。
