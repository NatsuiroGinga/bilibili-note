---
title: "wangtz19/NetMamba：单向 Mamba 流量分类代码仓库"
authors:
  - Tongze Wang, Xiaohui Xie, Wenduo Wang, Chuyi Wang, Youjian Zhao, Yong Cui
year: 2024
date: 2026-08-08
journal: "GitHub 代码仓库（ICNP 2024, arXiv:2405.11449）"
resource_type: 代码仓库
url: "https://github.com/wangtz19/NetMamba"
verified_on: 2026-08-08
tags:
  - 外部资源
  - 代码仓库
  - NetMamba
  - 状态空间模型
  - 依赖风险
key_finding: "无许可证声明；安装说明钉死 torch 2.1.1+cu121、Python 3.10.13、vendored mamba-1p1p1、causal-conv1d==1.1.0，在 RTX 5090（Blackwell，需 CUDA 12.8+）上确定不可直接复现，属于高兼容性风险资源。"
---

# wangtz19/NetMamba

## 一句话

线性复杂度流量模型的直接前例，但依赖栈钉死在 cu121，与本课题目标硬件不兼容。

## 实测事实（GitHub API + README + requirements.txt，核验日期 2026-08-08）

- 许可证：GitHub API 返回 `None`——**仓库无 LICENSE 文件**。
- 最后提交 2026-04-05T09:15:39Z，信息 `update readme for netmamba+`；Stars 179；未归档。
- 论文：ICNP 2024，arXiv:2405.11449。README 更新记录显示 2026-04-05 发布了期刊版 **NetMamba+**（arXiv:2601.21792），代码在独立仓库 `wangtz19/NetMambaPlus`。
- 环境（README 原文）：`conda create -n NetMamba python=3.10.13`；`pip install torch==2.1.1 torchvision==0.16.1 --index-url .../cu121`；Mamba 1.1.1 通过仓库内 `mamba-1p1p1` 目录 `pip install -e .` 本地安装。
- `requirements.txt` 中 `causal-conv1d==1.1.0`（全文件为完全钉死的 `==` 版本清单，含 `datasets==2.15.0`、`einops==0.7.0` 等）。
- 权重分发：Hugging Face（`wangtz/NetMamba`，仅 26.19MB `pre-train.pth`）。数据分发：Google Drive（作者处理后的数据集）。
- 输入形态：按类别/划分（train/test/valid）组织的目录结构，每样本一个文件；由 pcap 经仓库 `dataset/` 下预处理脚本生成。
- 训练超参（README 示例）：预训练 `--mask_ratio 0.9`、`--steps 150000`、`--blr 1e-3`、`--no_amp`；微调 `--epochs 120`、`--blr 2e-3`、`--no_amp`。

## 兼容性判断（本课题目标卡 RTX 5090）

- torch 2.1.1+cu121 不支持 sm_120，**确定无法在 5090 上按原说明运行**。
- 需要升级到 torch ≥2.7 + cu128，并重编 `mamba-ssm` / `causal-conv1d`；vendored 的 mamba-1p1p1 与新版 CUDA 的内核 API 是否兼容未知（待验证，需实测编译）。
- `--no_amp` 表明作者训练时关闭混合精度，迁移到 bf16 需重新验证数值稳定性。

## 负面信息

- 无许可证 = 保留全部权利，复现和衍生发布均有法律风险。
- 数据集只走 Google Drive，无永久标识符，存在失效风险，且不利于复现声明。
- 主仓库已被作者引导至 NetMambaPlus，本仓库事实上进入维护尾声。

## 与本课题的关系

- 作为"线性状态模型已被用于流量"的既有工作，必须在相关工作中讨论并给出差异化。
- 其 MAE 掩码率 0.9 与仅 26MB 的骨干规模，是"现有工作把流量当图像补全"的证据，与本课题"字段交互是主信号"的实测形成对比。

## 待验证

- NetMamba+ (arXiv:2601.21792) 是否修正了依赖与规模问题（待验证，需读全文）。
- 在 cu128 环境重编后能否复现原论文指标（待验证，需实测）。
