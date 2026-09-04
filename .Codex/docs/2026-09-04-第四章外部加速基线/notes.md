# 调研笔记：第四章外部加速基线（查询式与证据台账）

- 日期：2026-09-04
- 交付：`thesis/methods/第四章外部加速基线清单.md`
- **本次全部在线来源最高只到「在线摘要」**（无 Bash，无法下载 PDF 入 `raw/`，
  无法调 `pdf-converter`）。

## 一、本地检索（词法通道，rg 内核；向量通道未运行）

| 查询 | 路径 | 结果 |
| --- | --- | --- |
| `wiki/papers/**/*.md` 全量 glob | 仓库根 | `880` 篇笔记，确认知识层规模 |
| `**/朱焱雷*` | 仓库根 | 原件 `raw/papers/attack-detection/朱焱雷.pdf`；**全文提取 `wiki/papers/attack-detection/朱焱雷-全文.md`**（关键） |
| `对比方法\|基线方法\|4\.6\.1\|实验设置` | `朱焱雷-全文.md` | 命中行 `2135` 起，定位第四章实验设置 |
| `^\[7[4-8]\]` | `朱焱雷-全文.md` | 取到 `[75]`／`[76]`／`[77]` 的完整题录 |
| `^#{1,4}` | `第四章效率机制文献调研.md` | 取到七节骨架，定位 6.5「基线为零」 |
| `thesis/methods/*.md` glob | 仓库根 | **发现 `第四章外部基线清单.md` 已存在**（10 条），据此把本次任务改为增量 |

**注**：`朱焱雷-全文.md` 含 `\0` 字节，Grep 会报 `binary file matches`
但仍返回文本行，Read 可正常读取。

## 二、Zotero

| 调用 | 结果 |
| --- | --- |
| `zotero_search_items("training efficiency sparse backpropagation", everything)` | **`[Errno 61] Connection refused`** — 本地服务未运行。**本次未做 Zotero 去重**，如实登记为阻塞 |

## 三、在线检索台账

| # | 查询式 | 主要收获 | 证据等级 |
| --- | --- | --- | --- |
| Q1 | `safe screening rules pairwise learning AUC maximization exact solution discard samples` | **零结果**：未见针对成对 AUC 损失的精确安全筛除。返回给出结构性原因（筛一样本消 `O(n)` 对；筛除规则依赖凸对偶） | 在线摘要 |
| Q2 | `safe screening rule CVaR superquantile top-k loss exact equivalence training acceleration` | **零结果**：CVaR 加速主流走平滑化（改目标），非「保目标省计算」。定位 `arXiv:2009.14575`、`sqwash` 库 | 在线摘要 |
| Q3 | `InfoBatch lossless training speed up unbiased dynamic data pruning ICLR 2024` | InfoBatch 全套信息：ICLR 2024 Oral、arXiv:2303.04947、省 `40%`、官方 3 行接入 | 在线摘要 |
| Q4 | `CRAIG GradMatch coreset selection gradient matching efficient training speedup ICML` | CRAIG(ICML 2020)／GRAD-MATCH(ICML 2021, arXiv:2103.00123) 机制与 CORDS 库；**旁证：DeepCore 实证「随机选择仍是强基线」** | 在线摘要 |
| Q5 | `efficient partial AUC optimization pairwise loss O(n^2) avoid materializing pairs sampling stochastic algorithm` | **关键结构发现**：`O(n²)` 规避分「采样近似」与「等价重构」两条路线，数值语义不同 | 在线摘要 |
| Q6 | `meProp sparsified back propagation top-k gradient exact minimal effort backprop` | meProp(ICML 2017) 是**有损 top-k**，非精确；GPU 需统一 batch 内 top-k 模式 | 在线摘要 |
| Q7 | `Wu "Towards Efficient Adversarial Training on Vision Transformers" ECCV 2022 ...` | `[75]` 实为 **AGAT 丢 patch**，非算子优化 → **发现参照论文著录－描述不一致** | 在线摘要 |
| Q8 | `FlashAttention Dao exact attention IO-aware speedup training wall-clock reported` | FlashAttention 数字全在长序列（`512`–`4K`）测得 → 本课题短序列（`n≈83`）收益存疑 | 在线摘要 |
| Q9 | `Xhonneux "Efficient Adversarial Training in LLMs with Continuous Attacks" ...` | `[77]` 实为**连续 embedding 攻击**，与显存/检查点无关 → **第二处著录－描述不一致** | 在线摘要 |
| Q10 | `PyTorch 2 torch.compile TorchDynamo TorchInductor ASPLOS 2024 speedup geomean` | 训练 `1.41×` 几何平均（A100 fp32，180+ 模型）；TorchDynamo 单独 `1.0×` | 在线摘要 |
| Q11 | `Ying Wen Lyu "Stochastic Online AUC Maximization" NIPS 2016 min-max ...` | **SOLAM** 题录确认：Ying, Wen, Lyu, NIPS 2016；鞍点重构使成对损失变逐样本均值，`O(d)`／步；**评审明确指出只适用最小二乘损失** | 在线摘要 |
| Q12 | `skip backward pass samples with exactly zero gradient hinge loss active set neural network training speedup exact` | **本次最重要发现**：margin 损失的**精确零梯度 → 跳过反传**这一路线在深度学习里已有先例；另定位 SparseProp(权重稀疏，正交)、激活稀疏(ReLU) | 在线摘要 |
| Q13 | `extreme multi-label classification squared hinge loss gradient sparsity skip backward implicit negative mining exact ...` | 确认该机制名为 **implicit negative mining**；Schultheis & Babbar 2023 §4.4 量化：SQH 相对 BCE **每轮训练时间降约 `1/3`**；arXiv:2109.13122 报 **约 `3×`**（部分来自该效应） | 在线摘要 |

### 两次 WebFetch（arXiv 摘要页，权威题录）

| URL | 用途 | 结果 |
| --- | --- | --- |
| `arxiv.org/abs/2306.03725` | 核实 Schultheis & Babbar 题录 | 题名／作者／DOI `10.1007/978-3-031-43418-1_41` 确认。**重要更正：其摘要通篇讲稀疏连接的显存问题，未提 margin 梯度稀疏**——Q12 检索返回把该机制归给本文属二手转述，机制描述须以 Q13 的 §4.4 定位为准，且**仍未读全文** |
| `arxiv.org/abs/2302.04852` | 核实 SparseProp | Nikdan, Pegolotti, Iofinova, Kurtic, Alistarh；**权重**稀疏，与本课题正交；摘要未给具体倍数 |

## 四、本次已识别的两类误差（写入交付文件）

1. **参照论文的著录－描述不一致**（`[75]`、`[77]` 两处），已写入交付文件 1.2 节。
2. **检索返回的二手归属错误**（Q12 把 implicit negative mining 归给 2306.03725 的摘要范围），
   已由 WebFetch 当场纠正。**这是「检索摘要不得直接当证据」的一次实例**。

## 五、待办（未关闭）

- 全部 `11` 条新增条目**无一取得全文**，待入库清单见交付文件第十节。
- Zotero 去重未做。
- 本地混合索引向量通道未跑。
- 交付文件与本笔记**均未提交**（无 Bash）。
