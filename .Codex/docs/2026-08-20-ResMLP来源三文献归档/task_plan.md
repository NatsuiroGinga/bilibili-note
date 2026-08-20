# ResMLP 来源三文献归档计划

## 目标

把三篇指定论文从合法原文入口完整归档到 `raw/`、`wiki/`、方法论索引和 Zotero，并记录可追溯页码、公式、文件哈希及其对当前 `resmlp2` 的支持边界。

## 文件范围

- `raw/papers/methodology/2016-He-Deep-Residual-Learning.pdf`
- `raw/papers/methodology/2021-Gorishniy-Revisiting-Deep-Learning-Tabular-Data.pdf`
- `raw/papers/methodology/2021-Touvron-ResMLP.pdf`
- `wiki/papers/methodology/2016-He-深度残差学习.md`
- `wiki/papers/methodology/2021-Gorishniy-表格数据深度学习模型再审视.md`
- `wiki/papers/methodology/2021-Touvron-ResMLP图像前馈网络.md`
- `wiki/papers/methodology/INDEX.md`
- 本目录下的计划、笔记与归档报告
- 上述三篇论文的 Zotero 条目

## 阶段

- [x] 阶段一：读取规则、去重检查并冻结路径
- [x] 阶段二：从 arXiv 官方入口下载三份 PDF，核验题录、页数和 SHA-256
- [x] 阶段三：逐页读取全文，记录公式、实验与论断边界
- [x] 阶段四：创建三份结构化论文笔记并最小更新方法论索引
- [x] 阶段五：去重后导入 Zotero 条目，核对条目键与 BibTeX 键
- [ ] 阶段六：验证链接、元数据、原件哈希和 Git 范围，只提交本任务文件

## 关键问题

1. 三篇论文分别能支撑当前 `resmlp2` 的哪些构件来源？
2. 哪些结论只适用于图像或通用表格数据，不能外推到加密恶意流量检测？
3. 当前 `resmlp2` 与 Touvron 的 ResMLP 是否同一结构，还是仅共享残差多层感知机这一宽泛思想？

## 决策

- 三篇均归入 `methodology`：它们提供残差优化、表格神经基线与图像 ResMLP 的方法来源，而不是当前检测任务的直接实证。
- 只依据原始 PDF 写确定性主张；自动提取文本只作定位辅助。

## 错误与阻塞

- zsh 批量核验首次误用特殊数组变量名 `path`，只造成循环内命令未找到；改用 `pdf_file` 后完成，原件未被覆盖。
- Zotero 搜索首次误用不存在的 `--query` 与 `--limit`；读取本机命令帮助后改用位置参数完成，未产生错误条目。
- 当前无阻塞。

## 状态

当前处于阶段六：制品与哈希已核验，等待仅提交本任务文件并写最终归档报告。
