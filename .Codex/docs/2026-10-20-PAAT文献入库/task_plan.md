# PAAT 理论家族文献入库计划

> 任务日期：2026-10-20
> 目标：为第四章 PAAT（原型锚定年度训练）补齐 M1 原型/对比表示学习与 M2 类不平衡/平衡回合训练的经典锚点文献，并把全文纳入 `raw/` + `wiki/` + INDEX + Zotero。
> 约束：不 commit；不改既有笔记正文；PDF 只用 MinerU `extract`；题录只取工具返回值。

## 目标文献

### 第一优先（M1/M2 直接锚点）

| 短名 | arXiv | 对应机制 | PDF 落点 | wiki 笔记 | 状态 |
|---|---|---|---|---|---|
| ProtoNet | 1703.05175 | M1 原型表示 | `raw/papers/methodology/2017-Snell-Prototypical-Networks-Few-Shot.pdf` | `wiki/papers/methodology/2017-Snell-原型网络少样本学习.md` | 完成 |
| SupCon | 2004.11362 | M1 对比表示 | `raw/papers/methodology/2020-Khosla-Supervised-Contrastive-Learning.pdf` | `wiki/papers/methodology/2020-Khosla-监督对比学习.md` | 完成 |
| ClassBalanced | 1901.05555 | M2 类不平衡加权 | `raw/papers/methodology/2019-Cui-Class-Balanced-Loss.pdf` | `wiki/papers/methodology/2019-Cui-有效样本数类平衡损失.md` | 完成 |
| LDAM | 1906.07413 | M2 标签分布感知间隔 | `raw/papers/methodology/2019-Cao-LDAM-Label-Distribution-Aware-Margin.pdf` | `wiki/papers/methodology/2019-Cao-LDAM标签分布感知间隔.md` | 完成 |
| Decoupling | 1910.09217 | M2 表示/分类器解耦 | `raw/papers/methodology/2020-Kang-Decoupling-Representation-Classifier.pdf` | `wiki/papers/methodology/2020-Kang-长尾解耦表示与分类器.md` | 完成 |

### 第二优先（时间允许）

- FaceNet（arXiv:1503.03832）
- Focal Loss（arXiv:1708.02002）
- DeepFM（arXiv:1703.04247）
- PNN（arXiv:1611.00144）
- Factorization Machines（Rendle ICDM 2010，DOI 10.1109/ICDM.2010.127）

## 执行步骤

1. arXiv API 核验题录（题名/作者/年份/venue/标识），Crossref 补 DOI；DPBL/会议页补 venue。
2. 下载 PDF 到 `raw/papers/methodology/`，不覆盖已有文件；已存在则复用登记。
3. `mineru-open-api auth --show` 预检，`mineru-open-api extract` 转 Markdown 到 `/tmp/2026-10-20-PAAT文献入库/`；读全文。
4. 写 `wiki/papers/methodology/` 结构化笔记：frontmatter 八字段 + 核心机制 + 与 PAAT M1/M2 的可迁移点 + 不可迁移边界 + 公式/页码锚点。
5. 追加 `wiki/papers/methodology/INDEX.md`。
6. Zotero 查重后 `zotero_add_items_by_arxiv` 入库。
7. 在 `notes.md` 逐篇追加检查点；任务结束输出报告。不 commit。

## 停止条件

- 第一优先 5 篇全部完成（或明确失败原因）。
- 预期总时长 ≤ 1.5 小时；第二优先仅在时间允许时执行。

## 验收

- 每篇 PDF 可打开且页数与 arXiv 一致。
- 每篇 wiki 笔记的 `source_pdf` 指向实际原件。
- INDEX 中每篇有一行可点击链接 + 一句话说明。
- 报告区分「本地全文核验」与「仅题录/摘要」，不用摘要冒充全文。
