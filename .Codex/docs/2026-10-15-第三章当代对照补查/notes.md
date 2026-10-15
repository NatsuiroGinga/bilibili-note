# 检索笔记：第三章当代对照补查

> 每完成一组查询立即落盘。证据等级：`本地全文` / `在线全文已下载` / `仅摘要` / `仅题录`。

## 0. 环境与工具实测（2026-10-15）
- `scholar` CLI 存在（`/Users/bilibili/.local/bin/scholar`），挂代理 `HTTPS_PROXY=http://127.0.0.1:7890` 仍**持续 429 Too Many Requests**（多次重试均失败）→ 改用 WebSearch ＋ arXiv API ＋ 直接 PDF 下载。
- `mcp__zotero__zotero_semantic_search` 返回**不相关结果**（RWKV/LLM 主题，相似度全为负）→ 语义库未覆盖本主题，不可用；本地查重改 rg。
- 任务简报提到的 `mcp__990aea2c-*`/`mcp__4cfe5157-*`/`mcp__6874b72c-*`/`mcp__50ccb3c5-*`/`mcp__d0a01844-*` **不在本代理工具表**，未使用。
- 可用且有效：WebSearch、WebFetch、arXiv API（curl＋代理）、Bash 直连 PDF。

## 1. LAMDA ICLR 2026 原论文协议核验（本地 wiki 已有 + WebSearch 复核）
- Domain-IL：固定标签空间（恶意/良性），二分类 BCE；head 为**两层 MLP（各 100 单元，dropout 0.2，sigmoid）**；骨干四层 MLP（512/384/256/128 ReLU）；SGD(lr=0.01,mom=0.9,wd=1e-6)。**与本文第三章设定一致。**
- 原论文 CL 基线只有三个：**Naive / Replay / Joint**。→ 这就是"当代对照偏薄"的根源：LAMDA 自身只要这三个。
- 原论文结论：Domain-IL 上遗忘相对有限，**主要挑战是适应分布漂移而非遗忘**；Naive/Replay 表现都不差。
- LAMDA 其他适应方法对照：CADE / Chen-AL / TRANSCENDENT，标注预算 50/100/200/400。
- 证据等级：本地全文（wiki/papers/malware/LAMDA-2026-...md）＋ 在线 ICLR 2026 proceedings PDF（未下载）

## 2. 本轮新发现候选（在线检索）

### 问 1：2024–2026 固定预算 CL 方法
| 论文 | ID/venue | 年份 | 证据等级 | 与本文竞争点 |
| --- | --- | --- | --- | --- |
| Leveraging Complementary Embeddings for Replay Selection (MERS) | arXiv 2604.08336v2 | 2026-04 | 在线全文已下载 | 小缓冲回放选样，coverage-based，drop-in 无架构改动，可替换 ER 缓冲更新规则 |
| Non-Uniform Memory Sampling in Experience Replay | arXiv 2502.11305v1 | 2025-02 | 在线全文已下载 | 固定缓冲内容下改**采样概率**（非存什么），直接竞争"复用倍数/分配" |
| Unlocking the Power of Rehearsal in CL: A Theoretical Perspective | arXiv 2506.00205 (ICML 2025) | 2025-05 | 在线全文已下载 | 遗忘界 O(√(T/m))、m≥O(d/ε²)、uniform vs progressive 缓冲分配 |
| PDAC: Probability Density-Aware Coreset Selection | arXiv (Nov 2025) | 2025-11 | 仅摘要 | 密度感知核心集，PGM 模型 + 流式 EM |
| PIL: Practical Incremental Learning | Neurocomputing 2025 | 2025 | 仅摘要 | 解耦存储与缓冲，DCDA |
| Coresets are more than replay: a data-centric view | Neural Computing and Applications 2026 | 2026 | 仅题录 | — |
| CSReL: Coreset Selection via Reducible Loss | ICLR 2025 | 2025 | **本地全文**（已在库） | 可约损失核心集，已有 |

### 问 2：2024–2026 恶意软件 CL
| 论文 | ID/venue | 年份 | 证据等级 | 是否 LAMDA |
| --- | --- | --- | --- | --- |
| MalCL: GAN-based Generative Replay | arXiv 2501.01110 | 2025-01 | 在线全文已下载 | 否（EMBER/AZ-Class）|
| DAHT: Domain-Aware Hierarchical Transformer | Zenodo 22206206 / IJCRST | 2026-08 | 仅摘要（Zenodo）| **是**（LAMDA，但静态前向训练，非 CL 记忆预算；venue 存疑）|
| Drift-Aware Federated CL for Android Malware | IEEE 11683755 | 2026 | 仅摘要 | 否（AndMal2020/DREBIN-215/CICMalDroid/TUANDROMD）|
| FreeMOCA / MADAR / UGSR / CITADEL / SEED / DMAE / Ghiani | — | 2025-26 | 已在库 | 部分 |

## 3. arXiv 元数据核验（curl arXiv API，2026-10-15）
- 2502.11305v1 "Non-Uniform Memory Sampling in Experience Replay"，Andrii Krutsylo，2025-02-16
- 2506.00205v1 "Unlocking the Power of Rehearsal in Continual Learning: A Theoretical Perspective"，Junze Deng, Qinhang Wu, Peizhong Ju, Sen Lin, Yingbin Liang, Ness Shroff，2025-05-30
- 2604.08336v2 "Leveraging Complementary Embeddings for Replay Selection in CL with Small Buffers"，Danit Yanowsky, Daphna Weinshall，2026-04-09
- 2501.01110v1 "MalCL: ..."，Jimin Park, AHyun Ji, Minji Park, Mohammad Saidur Rahman, Se Eun Oh，2025-01-02

## 4. 完成情况（2026-10-15 收尾）
- [x] DAHT 全文（Zenodo）已取并转：**非 CL 静态前向 + 弱 venue，不作基线**
- [x] MinerU `extract` 转换 7 篇（MERS / NonUniform / Deng-rehearsal / MalCL / OWMMD / AttenMLP / DAHT）→ 三问已判
- [x] Q1 扩展到表格 CL（AttenMLP/IMLP、MFTCL、伪排练 buffer200）与 CVPR/ICLR 2025-26 多篇
- [x] Q2 LAMDA：仅 DAHT（非 CL）；**未发现 LAMDA 上固定预算 CL 新方法**
- [x] 报告已写：`.Codex/docs/2026-10-15-第三章当代对照补查/报告.md`

## 5. 三问总表（已核全文者）
| 方法 | ①200 条 | ②MLP | ③代码 |
|---|---|---|---|
| Krutsylo 2025 非均匀采样 | 能 | 能 | 有 |
| CSReL (ICLR25) | 能 | 能 | 有（在库） |
| MADAR (CAMLIS25) | 需适配 | 能 | 有 MIT（在库） |
| Seo 2025 | 能 | 需核实 | 有（在库，已引） |
| Deng Hybrid Rehearsal (ICML25) | 能 | 能 | 无 |
| OWMMD (KBS25) | 能（200 明列） | 能 | 未定位 |
| AttenMLP | 口径不同 | 能（原生 MLP） | 未定位 |
| MERS | 能 | 受限（SimCLR） | 无 |
| MalCL (AAAI25) | 不能（GAN） | 不能直接（1D CNN） | 有 |
| DAHT | 不适用 | N/A | 未定位 |

## 6. 未决 / 移交
- Zotero 条目未建（语义库离线）；raw 已有 PDF，可后续补录
- 表格 CL 方向（MFTCL/伪排练/TRIL3）仅摘要，建议人工取全文——对本课题最贴切但覆盖不足
