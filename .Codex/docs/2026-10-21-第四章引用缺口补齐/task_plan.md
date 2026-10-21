# 第四章骨架引用缺口补齐：任务计划

- 任务日期：2026-10-21
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`
- 分支：`codex/ch3-cpa-elp-20260820`
- 状态：已完成（未 commit）
- 不 commit。

## 背景

`thesis/methods/第四章-单次预算下的年度风险最小化形式化.md` 与两份理论文档引用了三处文献缺口：

1. Liu & Yao 1999（NCL 正源）——题录待核，需开放全文；
2. Keskar et al. 2017（H2a 平坦极小值锚点）——arXiv 1609.04836 待核；
3. Fort, Hu & Lakshminarayanan 2019（成员分歧的初始化解释）——arXiv 1912.02759 待核；
4. Brown et al. 2005（diversity creation methods 综述）——只核题录与可得性。

## 步骤

### 第一组：题录核实（全部 API，禁止凭记忆）

- Liu & Yao 1999：DBLP API → Crossref 交叉核对；题名与出处作为待验证假设。
- Keskar 2017：arXiv API `id_list=1609.04836`。
- Fort et al. 2019：arXiv API `id_list=1912.02759`。
- Brown 2005：Crossref `query.bibliographic` + DBLP 核对。

### 第二组：开放副本获取与全文入库

- Liu & Yao：Semantic Scholar `openAccessPdf`、CiteSeerX、作者主页；拿到 PDF 才入库，
  否则如实登记「仅题录 + 阻塞」。
- Keskar：arXiv 官方 PDF → `raw/papers/methodology/2017-Keskar-大批量与尖锐极小.pdf`。
- Fort：arXiv 官方 PDF → `raw/papers/methodology/2019-Fort-深度集成的损失面视角.pdf`。
- 每份原件 `shasum -a 256` 记录。

### 第三组：MinerU 转换与笔记

- 转换中间文件写 `/tmp/ch4-refgap-extract/<slug>/`，不进入仓库。
- 英文论文 `extract -l en`；公式、数字、页码回到 PDF 物理页视觉复核。
- 笔记落 `wiki/papers/methodology/`，frontmatter 八字段 + 页码锚点。
- Liu & Yao 重点：$p_i$ 原始定义与符号、$\lambda$ 取值建议、成员相关性动机表述。
- Keskar 重点：锐度与泛化核心论证、与 H2a 的接口（接口定义先回读理论文档）。
- Fort 重点：独立初始化→不同 basin→成员分歧的论证、与随机符号首适配的关系。

### 收尾

- 更新 `wiki/papers/methodology/INDEX.md`「集成统计与隐式正则」节：追加 Liu&Yao、Keskar、Fort；
  Brown 登记行。
- `notes.md` 汇总表（状态 / API / 稳定标识 / SHA 前 8 位 / 笔记路径）。

## 验收

- 三份 PDF 落盘且 SHA 可复算（Liu & Yao 若付费墙则 notes 明确阻塞）。
- 三份 wiki 笔记 `source_pdf` 指向原件；公式与页码锚点已回原文核对。
- INDEX 可解析；notes 汇总表完整；未改动其他文件；未 commit。

## 执行记录

- [x] 建任务目录与计划
- [x] 题录核实：Liu & Yao（Crossref + Semantic Scholar/DBLP + OpenAlex）、
      Keskar（arXiv API）、Fort（arXiv API，ID 修正为 1912.02757v2）、
      Brown（Crossref + Semantic Scholar/DBLP + OpenAlex）
- [x] Liu & Yao 开放副本：作者主页 Wayback 快照，10 页，SHA `de7e5d3d`
- [x] Keskar 官方 PDF，16 页，SHA `bcd5497a`
- [x] Fort 官方 PDF，15 页，SHA `e3dff579`
- [x] MinerU 转换 ×3（`/tmp/ch4-refgap-extract/{liu,keskar,fort}/`）
- [x] wiki 笔记 ×3（frontmatter 八字段，YAML 解析通过）
- [x] INDEX「集成统计与隐式正则」节追加三篇 + Brown 登记行
- [x] notes 汇总表与关键发现
- [x] Brown 2005：题录已核，无可用开放副本，登记付费墙阻塞
- [ ] 未 commit（按任务要求）
