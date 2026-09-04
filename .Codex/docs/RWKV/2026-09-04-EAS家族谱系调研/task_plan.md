# EAS 家族谱系调研 · 任务计划

- 日期：2026-09-04
- 代理：文献子代理，模型 `opus`，effort 继承会话设置（Claude Code `Agent` 工具无 `effort` 入参）
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819`
- 产出文件（唯一）：`thesis/methods/第四章机制一-EAS家族谱系.md`

## 目标

为第四章机制一 EAS（空活动集短路）所属的「安全筛除／梯度稀疏」家族建立完整谱系与可引用题录，
并对抗性地检验「EAS 落在谱系空白处」这一新颖性主张。

## 六条必覆盖主线

| # | 主线 | 初始状态 |
| --- | --- | --- |
| 1 | Ghaoui et al., Safe Feature Elimination for LASSO（arXiv:1009.4219） | 未入库 |
| 2 | Ogawa et al., SVM 安全样本筛选 | **已入库**（raw + wiki 全文笔记） |
| 3 | ERM 椭球区域安全筛选（arXiv:1912.02566） | 未入库 |
| 4 | meProp（arXiv:1706.06197） | 未入库 |
| 5 | SparseProp（arXiv:2302.04852） | 未入库 |
| 6 | Schultheis & Babbar 隐式负例挖掘（arXiv:2306.03725） | **已入库**（raw + wiki 全文笔记） |

补充建议（非硬性）：Selective Backprop（**已入库**）、dynamic screening（Bonnefoy）、
GAP safe rules（Ndiaye）。

## 执行顺序（强制）

1. 本地混合索引 → 2. Zotero 语义检索 → 3. 在线技能／MCP → 4. 入库（raw PDF + wiki 全文笔记 + INDEX）

## 纪律

- 每完成一条文献立即写入产出文件并 `git commit`，禁止攒到最后。
- 每条标注四级证据等级之一：`本地全文` / `在线全文已下载` / `在线摘要` / `仅题录`。
- arXiv ID 逐个核验可打开；检索不到写「未检索到」，不编造题录。
- 读 PDF 只用 `pdf-converter`（MinerU），禁 `pdftotext`。
- 本机不执行任何实验计算。
- 不修改 `thesis/methods/第四章机制一-EAS空活动集短路.md` 与
  `.Codex/docs/RWKV/2026-09-04-EAS方案对抗性审核.md`。

## 第三节对抗性检索（必须做）

查询式：safe screening ranking loss、safe screening AUC optimization、
screening pairwise loss、active set pairwise ranking。
**若找到已做 pairwise/ranking loss 安全筛除的工作，直接判定 EAS 新颖性主张不成立。**
