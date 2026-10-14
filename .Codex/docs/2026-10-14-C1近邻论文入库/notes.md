# 检索笔记：C1 近邻论文入库（2026-10-14）

## 一、工具与通路的实测结论（**下次直接用，不要重试错的方式**）

| 通路 | 结果 | 备注 |
| --- | --- | --- |
| scholar CLI | ✗ 不可用 | 需 Chrome 调试端口，本会话无 |
| Semantic Scholar API | ✗ `429 Too Many Requests` | 重试两次均 429，无 key 不可用 |
| **OpenAlex API** | ✅ **可用，无需 key** | `https://api.openalex.org/works`，直连即可 |
| **arXiv API** | ✅ **仅 `https://` + `-x http://127.0.0.1:7890`** | `http://export.arxiv.org` 直连**静默返回空**（不报错）——差点被当成「论文不存在」 |
| arXiv abs 页面 | ✅ `https://arxiv.org/abs/<id>` + 代理 | 用于复核标题 |

**关键教训**：`http://export.arxiv.org/api/query` 直连**返回空字符串且 exit 0**，
我的解析器据此输出「未找到」——**包括本地已存全文的 MADCAT**。这是
「某工具取不到 ≠ 来源不可达」的又一次复发（检查点 §八已登记，仍复发）。
**凡解析器报「未找到」，必须先看原始返回字节数再下结论。**

**另一个错误**：OpenAlex 的 `search=` 是全文模糊匹配，按 `cited_by_count` 排序只会返回
高被引综述（实测首条是 SVM 综述，2365 次引用）。**正确用法是
`filter=title_and_abstract.search:<短语>` + `sort=publication_year:desc`。**

## 二、查询式与命中（逐条留痕）

| # | 查询式 | 命中 | 用途 |
| --- | --- | --- | --- |
| 1 | `title_and_abstract.search:android malware concept drift adaptation` | **16** | C1 空间全扫（最有效的一条） |
| 2 | `title_and_abstract.search:malware test-time adaptation` | 28 | MADCAT 同类 |
| 3 | `title_and_abstract.search:malware label noise temporal degradation detection` | **1** | C2 空间（几乎空） |
| 4 | `title_and_abstract.search:continual learning malware catastrophic forgetting domain incremental` | **5** | C3 空间 |
| 5 | `title_and_abstract.search:android malware label quality annotation reliability` | **0** | C2 空间的标签质量侧 |
| 6 | arXiv `ti:"ADAPT" AND abs:"pseudo-labeling" AND abs:"malware"` | 3 | 意外带出 LFreeDA |

## 三、三个候选空间占位（2026-10-14 实测，**同日同比**）

| 候选 | 空间规模 | 占位情况 |
| --- | --- | --- |
| **C1** 零/低标签时间泛化 | 16 条（含 8 篇 2025–2026 新作） | **拥挤**：SEED(预算半监督)、LFreeDA(无标签)、MADCAT(无标签 TTA)、CITADEL(主动学习 400)、HYDRA、MORPH、ADAPT |
| **C2** 标注管线时间退化 | **1 条**（且是 LLM few-shot，非时间退化） | **近乎无人**；但见 task_plan 的评价循环性风险 |
| **C3** Domain-IL 安全回归 | 5 条（MalCL、FreeMOCA、BinAdapter、Adapter-based） | 中等；本地已有 9 个否决实现铺在同路 |

**⇒ 与 2026-10-14 综述代理结论的直接冲突**：综述称 C1 的零标签端「是明确空位」，
**C2 未被占用只作「第二落点」**。实测是反过来——**C1 空位已被占，C2 的空间反而近乎无人**。
该冲突必须写回候选对照文档与综述索引（task_plan §二.4）。

## 四、下载台账（全部落 `raw/papers/attack-detection/`）

| 文件 | arXiv | 月份 | 大小 |
| --- | --- | --- | --- |
| `2026-Amalapuram-SEED-Semi-Supervised-Continual-Malware-Drift-Budget.pdf` | 2605.24903 | 2026-05 | 2.1M |
| `2026-Chen-HYDRA-Proactive-Android-Malware-Drift-Adaptation.pdf` | 2609.26352 | 2026-09 | 2.0M |
| `2026-Concept-Drift-Adaptation-Self-Supervised-Reinforcement-Learning-Android.pdf` | 2605.24294 | 2026-05 | 4.5M |
| `2025-Li-LFreeDA-Label-Free-Drift-Adaptation-Windows-Malware.pdf` | 2511.14963 | 2025-11 | 4.3M |
| `2025-McFadden-DRMD-Deep-Reinforcement-Learning-Malware-Drift.pdf` | 2508.18839 | 2025-08 | 324K |
| `2025-Alam-ADAPT-Pseudo-Labeling-Concept-Drift.pdf` | 2507.08597 | 2025-07 | 3.4M |
| `2024-He-Combating-Concept-Drift-Explanatory-Detection-Adaptation.pdf` | 2405.04095 | 2024-05 | 4.1M |
| `2024-Alam-MORPH-Automated-Concept-Drift-Adaptation.pdf` | 2401.12790 | 2024-01 | 3.4M |

**全部经 `file -b` 校验为真 PDF**（非 HTML 错误页）——下载后必须做这一步，
历史上出过 `hf download` 静默失败却报成功的事故。

## 五、待办

- [ ] MinerU 转全文（`pdf-converter`），中间文件写 `/tmp` 任务目录
- [ ] 8 份结构化笔记（frontmatter 八字段 + `source_pdf` + 页码）
- [ ] 更新 `wiki/papers/attack-detection/INDEX.md`
- [ ] **冲突写回**：候选对照文档 + `task-candidates.md` 的 C1 空位论断
- [ ] MADCAT 引用图：OpenAlex 记 `cited_by_count: 0`（2026-10-14）；S2 因 429 未取得，**待补**
