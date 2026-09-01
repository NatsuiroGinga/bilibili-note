# 任务计划：ATk Loss 与 SoRR 全文入库 + 聚合式差异核对

- 日期：2026-09-01
- 代理：`atk_sorr_ingestion_opus`（模型 opus，effort 继承会话设置）
- 路线：`RESEARCH_ROUTE=RWKV`，第三章机制一「实体内尾部聚合」
- 触发原因：`.Codex/docs/RWKV/2026-09-01-第三章公式来源与改造实质盘点.md`（提交 `e304d2a`）
  第 4.2 节登记的文献债务——ATk 与 SoRR 只有摘要级，违反 `raw/AGENTS.md`
  「检索到即入库」「下载即写笔记」。

## 待核对的本课题公式（内层）

```
S_e = (1/⌈αm⌉) · Σ_{top-⌈αm⌉} l_{e,t}      α = 0.5，m = 实体 e 的有效流数
```

外层：BER 多预算 CVaR-pAUC 排序损失 `L_pn = softplus(S_n − S_p)`，六档预算。

## 任务边界

| 编号 | 任务 | 验收 |
| --- | --- | --- |
| T1 | 下载 ATk（arXiv:1705.08826）与 SoRR（arXiv:2106.03300）全文 | `raw/papers/methodology/ranking/` 下有原件，SHA-256 已记 |
| T2 | `pdf-converter`（`mineru-open-api extract`）全文提取，禁止 `pdftotext` | `wiki/papers/methodology/ranking/*-全文提取-mineru.md` 落盘 |
| T3 | 两份结构化笔记，沿用 `2022-Wang-FCCO与SOX.md` 的三段结构 + 「不可直接声称」 | `wiki/papers/methodology/ranking/` 下两份笔记，含物理页码 |
| T4 | 更新 `wiki/papers/methodology/INDEX.md` | 排序方向条目新增两条 |
| T5 | 五问差异核对（对象／k 的定义／饱和／与排序损失复合／理论迁移），逐条给精确公式与物理页码 | `核对报告.md` |
| T6 | 核实「FCCO 见 Hu 2023 物理页 8 式(8)–(9)」这一引用不一致 | 结论写入 FCCO 笔记证据记录 + 核对报告 |

## 硬约束

- 读 PDF 一律 `pdf-converter`，禁止 `pdftotext`；含公式判断必须来自 `extract` 输出并附页码。
- 摘要级不得支撑任何论断。
- 不连服务器、不占 GPU（C00 训练中）。
- 逐项提交，`git add <精确路径>`，禁止 `git add .`。
- 搜索 `rg`，找文件 `fd`；禁止 `sed`、`black`。
- 需要 Python 时用 `/opt/miniconda3/envs/rwkv/bin/python`。

## 状态

见 `notes.md`。
