# FM/PNN 家族三篇文献入库计划

> 任务日期：2026-10-20
> 目标：把 FM／PNN 家族三篇从「仅题录」升级为「本地全文 + wiki 全文笔记 + Zotero」。
> 约束：不 commit；不改既有笔记正文；题录只取工具返回值；不运行训练。

## 目标文献

| 短名 | 稳定标识（待核验） | PDF 落点（计划） | wiki 笔记（计划） | 状态 |
|---|---|---|---|---|
| Rendle FM | DOI 10.1109/ICDM.2010.127 | `raw/papers/methodology/2010-Rendle-FactorizationMachines.pdf` | `wiki/papers/methodology/2010-Rendle-因子分解机.md` | **仅题录**（PDF 阻塞，见 notes.md） |
| PNN | arXiv:1611.00144 | `raw/papers/methodology/2016-Qu-Product-based-Neural-Networks.pdf` | `wiki/papers/methodology/2016-Qu-乘积神经网络PNN.md` | 全文已核验；raw/ 迁移待补 |
| Li 2018（文档误记为 xDeepFM） | arXiv:1805.11843 | `raw/papers/methodology/2018-Li-Android-Malware-Factorization-Machine.pdf` | `wiki/papers/methodology/2018-Li-安卓恶意软件因子分解机.md` | 全文已核验；raw/ 迁移待补 |

## 关键题录核验

- **arXiv:1805.11843 不是 xDeepFM**。`zotero_add_items_by_arxiv` 按 arXiv API 返回的题名为
  “Android Malware Detection based on Factorization Machine”（Li Chenglin 等 6 人，2018-05-30，v2 2019-08-13）。
  父任务简报中的「疑似 xDeepFM, KDD 2018」假设被工具返回否决；本次以实际 arXiv 记录入库。
- arXiv:1611.00144 返回 “Product-based Neural Networks for User Response Prediction”（Qu Yanru 等 7 人，2016-11-01）。

## 执行步骤

1. 查重：`rg` 本地 `wiki/papers/`、`raw/papers/`；Zotero 检索三篇。
2. 题录核验：Zotero 的 arXiv / DOI 导入工具（其元数据来自 arXiv API 与 Crossref）。
3. 全文：从 Zotero 附件 PDF 直接读取（本代理无 shell，PDF 无法复制进 `raw/`）。
4. 写 wiki 笔记：frontmatter 八字段 + 一句话／题录与原件／论文原方法／直接参数与协议／与本课题关系／不能支持的论断／证据等级。
5. 更新 `wiki/papers/methodology/INDEX.md`。
6. `notes.md` 逐篇记录查询式、URL、原件路径、证据等级、关键页码。

## 已知工具限制（重要）

本代理会话**没有 Bash/shell 工具**，因此下列任务要求无法执行：

- 不能 `cp` Zotero 存储中的 PDF 到 `raw/papers/methodology/`；
- 不能 `shasum -a 256` 计算原件哈希；
- 不能运行 `mineru-open-api extract`（改以 Zotero 附件全文提取 + 直接读取原始 PDF 页码核验）；
- 不能运行 `git status --short` 做改文档前快照检查。

上述四项留给主代理用 shell 补齐；wiki 笔记已在 frontmatter 与正文显式标注迁移状态，未伪装为已完成。

## 验收

- 每篇 wiki 笔记的公式、数字、消融回到原始 PDF 页码。
- 报告明确区分「本地全文」「仅题录」，不以摘要冒充全文。
