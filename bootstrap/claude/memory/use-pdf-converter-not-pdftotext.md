---
name: use-pdf-converter-not-pdftotext
description: 读 PDF 一律用 pdf-converter（MinerU），禁止 pdftotext——后者丢失公式符号
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4bf71861-639f-455d-b431-5dbc10e3331a
  modified: 2026-09-01T03:52:34.778Z
---

读任何 PDF 论文一律用 `pdf-converter` 技能（`mineru-open-api extract`，已配置 token），
**不用 `pdftotext`**。长文档一次转全并落盘到 `wiki/papers/<方向>/<名>-全文提取-mineru.md`，
之后直接读该文件，不反复转换。派子代理读论文时，在提示里明确要求用同一入口。

**Why**：2026-09-01 用 `pdftotext -layout` 读朱焱雷学位论文第三章，公式被还原成
`ò ( )  L( f ( x), y)  ò‖ x L( f ( x), y)‖*` 这类残缺文本，δ/θ/ε 等符号大量丢失。
我据此判断「定理 1 是两行泰勒展开」——结论碰巧对，但**推导过程是在猜公式**。
换 MinerU 后同一段还原为完整 LaTeX，才拿到可核验的依据。
同仓库的 PLR 论文当初就是用 MinerU 核对的，方法早就在，是我没沿用。

**How to apply**：`mineru-open-api extract <pdf> -o <出路径.md>`；只要局部时加
`--pages a-b`，且 `-o` 必须是**含页范围的显式文件路径**（同名目录输出会互相覆盖）。
相关：[[consult-sources-before-asserting]]、[[download-and-note-every-cited-paper]]。
