# 检查点笔记：表格模型机制提取

日期：2026-09-02

## 已完成（全部已提交）

| 阶段 | 提交 | 内容 |
| --- | --- | --- |
| 族 C | `95223ca` | TabTransformer RTD／MLM、SAINT 样本间注意力与对比预训练 |
| 族 B | `f0c0bb9` | XTab 三目标与可共享组件规则、TransTab VPCL |
| 族 A ＋ 冲突关闭 | `16b644b` | TabPFN／PFN 三候选全否；Rubachev 2022 关闭全标注冲突 |
| 卡片与汇总 | `a80260d` | 两张 Research Question Card、三档清单 |
| SCARF 核验 | `61c93e3` | 关闭破坏率／`τ`／数值 RTD 三条待核项；补第三条全标注证据 |

产出：`thesis/methods/表格模型可借鉴机制提取.md`（约 1050 行）。

## 检索与证据

- 本地混合索引三次查询（自监督预训练／样本间注意力／对比学习）——无族 B、族 C 的既有笔记。
- 在线：直接从 arXiv 取全文，未用在线检索技能（候选论文由可行性调研已列出，无需再检索）。
- 八篇原件全部入库 `raw/papers/methodology/tabular-pretraining/`（TabTransformer 原件已在 `raw/papers/2012.06678v1.pdf`）。
- 转写落 `wiki/papers/methodology/tabular-pretraining/<名>-全文提取-mineru.md`。

## 转写工具的一处实测

- `mineru-open-api flash-extract` 上限 `10 MB`；SCARF（`12.7 MB`）超限报
  `[-30001] file size exceeds lightweight API limit`。
- 本机无 `qpdf`／`gs`／`mutool`／`pypdf`／`Quartz`，PDF 无法本地切分。
- **`mineru-open-api extract`（精度模式）已认证可用**，`--pages 1-10` 成功。
  今后遇到 `>10 MB` 的 PDF 直接用 `extract`，不要试图本地切分。
- `PDF_Tools` MCP 的沙箱只允许 `~/Documents`、`~/Downloads`、`~/Desktop`，
  且对该文件 `split_pdf` 超出其资源预算，不可用。

## 未完成／交由他处

- **`wiki/papers/methodology/INDEX.md` 的更新**：待两个笔记子代理返回后由主代理统一执行。
- **SCARF 的笔记**：由主代理直接撰写（主代理已读原文 p1–10）。
- 两条只读诊断（C-V1 时间因果协议、C-V2 完整袋分布）与卡二的类条件分布诊断
  **本任务不执行**——它们属实验前置，由主代理与用户裁定时序。

## 未核验的遗留（已在产出文档 §6.4 登记）

时间因果协议相容性、完整袋大小分位数、SAINT 附录 C 的 `q/k/v` 维度口径、
XTab 胜率的效应量、`λ_pt` 在本课题的取值、`p(x^j|ŷ)` 在二分类下的区分度、
`1199` 万行规模的外推、族 A 其他成员的行注意力细节。
