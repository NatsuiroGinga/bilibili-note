# 第四章理论家族补齐：任务计划

- 任务日期：2026-10-20（执行跨至 2026-10-21）
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`
- 分支：`exp/ch3-lamda-20260908`
- 状态：进行中

## 背景

第四章理论家族清点（对话已裁决）：

- 家族 C（集成统计与隐式正则）**零全文锚点**；
- DREBIN 仅为题录级，未入库全文；
- 家族 B 只做可得性登记，不下载。

## 第一组（必做）：DREBIN 全文入库

1. Crossref 核验 DOI `10.14722/ndss.2014.23247`；
2. 从 NDSS 官方页取开放获取 PDF；
3. 落盘 `raw/papers/methodology/2014-Arp-DREBIN-AndroidMalware.pdf`；
4. `shasum -a 256`；
5. MinerU 正式转换到 `/tmp/drebin-extract/`；
6. 写 `wiki/papers/methodology/2014-Arp-DREBIN安卓恶意软件静态检测.md`，frontmatter 八字段，正文含
   一句话/题录与原件/特征体系 8 类 545 万特征/检测方法/与本课题 4561 维特征格式的谱系关系/不能支持的论断/证据等级，全部带物理页码锚点。

## 第二组（必做）：家族 C 两篇经典全文入库

1. Krogh & Vedelsby 1995（NIPS 7）——歧义分解正源；
   - API/官方 proceedings 页核验题录；下载官方 PDF；
   - 落盘 `raw/papers/methodology/1995-Krogh-神经网络集成歧义分解.pdf`；
   - MinerU 转换；wiki 笔记重点：歧义分解公式与页码锚点。
2. Lakshminarayanan et al. 2017（NeurIPS）——Deep Ensembles；
   - arXiv API 核验 `1612.01474`；优先下载 NeurIPS 官方 camera-ready；
   - 落盘 `raw/papers/methodology/2017-Lakshminarayanan-DeepEnsembles.pdf`；
   - MinerU 转换；wiki 笔记重点：方差缩减论证。

## 第三组（仅登记，不下载）：家族 B 可得性核查

- Expert Gate（Aljundi et al., CVPR 2017）——CVF openaccess 直链；
- Veniat et al. 2020 modular networks——arXiv ID 核实；
- ACL 2025 Domain-IL SMoE——题录补全。

每篇登记：题录验证状态、PDF 直链或阻塞、与「成员-年度锚定」的关系一句话。

## 收尾

- 更新 `wiki/papers/methodology/INDEX.md`：新增「集成统计与隐式正则」小节，DREBIN 归入合适小节；
- `notes.md` 给汇总表（状态/arXiv 或 DOI/SHA 前 8 位/笔记路径）。

## 纪律与验收

- 题录一律 API/官方 proceedings 页核实，禁止凭记忆；
- 付费墙取不到即登记 URL 并标「仅题录」；
- 不修改其他文件，不 commit；
- 验收：三份 PDF 在 raw 落盘且 SHA 可复算；三份 wiki 笔记的 `source_pdf` 指向原件；
  INDEX 可解析；notes 汇总表完整。

## 执行记录

- [x] 建任务目录与计划
- [x] DREBIN 入库
- [x] Krogh 1995 入库
- [x] Lakshminarayanan 2017 入库
- [x] 家族 B 登记
- [x] INDEX 与汇总表
