---
schema: paper-note-search/v1
title: "Analyzing the Real-World Applicability of DGA Classifiers"
title_zh: "DGA分类器真实世界适用性分析"
authors: [Arthur Drichel, Ulrike Meyer, Samuel Schüppen, Dominik Teubert]
year: 2020
date: 2026-09-07
journal: "ARES 2020"
doi: "10.1145/3407023.3407030"
arxiv_id: "2006.11103"
fulltext_verified: true
source_pdf: "[[raw/papers/attack-detection/2020-Drichel-Real-World-DGA-Classifiers.pdf]]"
tags: [DGA检测, ResNet, 时间泛化, 未见家族, 真实流量, 类型/论文]
aliases: [Drichel2020, B-ResNet, M-ResNet]
tasks: [DGA二分类, 家族多分类, 跨网络泛化, 时间泛化, 对抗评估]
datasets: [DGArchive, 大学NXD, 企业NXD]
methods: [B-ResNet, M-ResNet, FANCI, Endgame, NYU]
metrics: [Accuracy, TPR, TNR, FPR, FNR, 吞吐]
key_finding:
  - "B-ResNet在20次数据集重复中做跨网络和1/17个月外推；17个月时平均FNR 0.00226、FPR 0.00221，但四个测试新家族推动FNR上升（PDF物理第8至9页，表8）。"
  - "3.7亿条真实企业NXD月数据产生约69个误报/小时，说明极低比例FPR仍可形成可观告警量（PDF物理第10页）。"
supports: ["B-ResNet是DRIFT之前最强轻量外推基线", "评价必须含跨网络/时间、未见家族、绝对告警量"]
cannot_support: ["九年漂移", "当前DRIFT去重协议", "默认阈值直接可部署"]
related: ["[[2018-Schuppen-FANCI]]", "[[2023-Drichel-DGA分类器偏差审计]]", "[[2026-Lee-DRIFT-DGA-Temporal-Drift]]"]
---

# DGA 分类器真实适用性

> 页码锚点：本地PDF共11个物理页；统一基线在第4至7页，网络/时间泛化表8在第8至9页，真实月测试在第10页。

## 一句话

B-ResNet 是目前最适合作为 DRIFT 并列 C00 的轻量强基线，因为它不仅静态高分，还报告跨网络、跨时间、未知家族与真实告警量。

## 论文可以支持

- B-ResNet/M-ResNet 是 Endgame/NYU 之后的强残差谱系。
- 新家族而非生成日期本身是17个月 FNR 上升的主要来源之一。

## 论文不能支持

- 不能把真实 NXD 结果直接搬到 DRIFT 全域名数据；协议和良性分布不同。

## 实验结果与负证据

- 17个月平均 FPR 0.00221，FNR 0.00226；未知家族 Wd TPR 最低0.89690。
- 真实月测试 FPR 0.00182 仍约69误报/小时。
- 所有核心实验做20份数据集重复，但没有公开精确样本清单与完整种子。

## 与本课题的关系

已发表最低表必须包含 B-ResNet；C00 最终在 B-ResNet 与 DRIFT 双分支间以共同协议、资源和病灶余量裁决。

## B-ResNet 架构规格（2026-09-11 补齐；以**官方实现**为准，含三处原文矛盾登记）

> 原笔记只有结论、无架构规格。以下为回原件（§3.1–§3.2，p.3）与**官方实现**核验所得。
> **官方实现**：`https://gitlab.com/rwth-itsec/robust-dga-detection` → `src/robust_dga_detection/models/cnn_resnet.py`，类 `CNNResNetWithEmbedding`，docstring 逐字写明 *"A PyTorch implementation of the **'B-ResNet'** model introduced by Drichel et al."* 并引 2020 ARES 论文与 DOI。
> **证据边界**：该仓库只含 `models/`、`attacks/`、`defenses/`、`utils/`，**无训练脚本** ⇒ **训练超参无官方配置可核**，只能回论文；而论文 §3.2 只给出损失（BCE）、优化器（Adam）与 batch（128）。

| 项 | 规格 |
| --- | --- |
| 输入 | `[BATCH, SEQ_LEN, 128]` |
| 嵌入 | `nn.Embedding(40, 128)` |
| **残差块数** | **1 个** |
| 块内 | Conv1d(k=4, padding='same') → ReLU → Conv1d(k=4, padding='same') → 与输入相加 |
| 块后 | ReLU → `max_pool1d(kernel_size=4, padding=2)` |
| 展平 | `128 × ceil(seq_len/4)`；`seq_len=63` ⇒ **2048** |
| 输出 | `Linear(2048, 1)`；默认 logits，`with_sigmoid_output()` 才 sigmoid |
| 训练 | BCE + Adam，batch **128** |

**三处必须登记的差异（引用前必读）**：

1. **残差块数＝1，图注「6 Residuals」是矛盾项**：论文 §3.2 正文逐字 *"For binary classification, **we use a single residual block**."*，官方代码亦只实例化一个 `ResidualITsec`；但**图 1(a) 的文字层含「6 Residuals」**，与正文和代码都矛盾（M-ResNet 是 11 块，也对不上）。**以正文＋代码为准，不得写 6 块。**
2. **输入长度两个口径**：论文 §3.1 用**完整域名**（明确「不删 TLD」）左零填充到 **253**；官方代码默认 `seq_len=63` 且注明用于 **e2LD**（剥离 TLD）。**两者不是同一输入视图。**
3. **2020 论文本身没有作者自有代码链接**：该版 PDF 全文检索仅见参考文献中 Bader 的 DGA 实现；本节所用实现出自 **2024 年**的 `robust-dga-detection` 库。引用「官方实现」须写明是哪个仓库。

**该规格已用于本课题第二骨干适配设计**：见 `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/zhuh-ch3-benchmark.md` §7（含与 DRIFT 字符编码的接口差异表与工作量估算）。

## 文献信息

- <https://arxiv.org/abs/2006.11103>
- 官方实现：`https://gitlab.com/rwth-itsec/robust-dga-detection`（2026-09-11 核验；模型定义内引 2020 ARES 论文）
