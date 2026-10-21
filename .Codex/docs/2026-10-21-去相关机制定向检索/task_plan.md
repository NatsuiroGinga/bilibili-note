# 任务计划：第四章机制二第三轮——去相关机制定向检索

- 日期：2026-10-21
- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`
- 任务性质：文献定向检索与正源核实，**只登记与推荐，不做存废裁决，不 commit**
- 背景：NCL（Liu & Yao 1999）先导失败；诊断为其惩罚 $p_i=-(f_i-\bar f)^2$ 在成员重合处梯度为零，$\lambda|p|/\mathrm{BCE}$ 仅 $10^{-3}\sim7\times10^{-2}$。第三轮拟改尺度稳定去相关项，需文献依据。

## 任务一（最高优先）：Rosen 1996 正源核实与入库

1. 用 Crossref / OpenAlex / Semantic Scholar / DBLP / Google Scholar 核实题名、作者、年份、出处、DOI。
2. 定位开放副本（作者页、CiteSeerX、S2 OA、机构库）；合法可得则下载。
3. 若取得全文：`raw/papers/methodology/1996-Rosen-去相关神经网络集成.pdf` + SHA-256 + MinerU 转换 + `wiki/papers/methodology/` 笔记（精确形式、与 NCL $p_i$ 关系、尺度行为、页码锚点）。
4. 若付费墙且无开放副本：在 notes.md 登记阻塞（题录、出版社页、建议文件名），不伪造全文笔记。

## 任务二：三组定向检索

| 组 | 主题 | 查询数 | 需要回答 |
|---|---|---|---|
| 1 | NCL 变体与后续 | 2–3 | 是否指出 $p_i$ 消失梯度/尺度问题，如何修 |
| 2 | 联合训练中成员相似化/坍缩 | 2–3 | 谱系锚点（member similarity during joint training、functional diversity decay） |
| 3 | 尺度稳定去相关损失 | 2–3 | 已发表形式（batch 内余弦/相关惩罚、多头自集成、冗余约减）与 λ 设定 |

## 检索顺序与工具

- 本地：`uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json`，再 `query ... --scope paper --mode hybrid --json`。
- 本地 Zotero：`zotero_semantic_search` / `zotero_search_items`（避免重复入库）。
- 在线：Crossref、OpenAlex、Semantic Scholar、DBLP、Google Scholar（`scholar` CLI，单主题 ≤3 条）。
- 所有在线命中只作候选；无 `raw/` 原件与 `wiki/` 全文笔记者不得升级为全文证据。

## 收尾

- `notes.md` 给出裁决输入表：(a) Rosen 正源形式与可得性；(b) NCL 尺度问题先例与修法；(c) 最有谱系的尺度稳定形式及出处；(d) 每项证据等级。
- 回报 ≤12 行，简体中文。
- 仅当任务一取得全文时执行入库；其余只登记。不 commit。

## 完成状态（2026-10-21）

- [x] 任务一：Rosen 题录核实；作者预印本取得、归档、MinerU、wiki 笔记、INDEX 更新。
- [x] 组 1：NCL 变体与尺度问题；Brown & Wyatt 2003、Wang 2010 全文；Chen & Yao 2009/2010 摘要；Shui 2018 全文。
- [x] 组 2：Repulsive 2021、Fort 2019、MOD 2020、Shui 2018；多头自集成现状。
- [x] 组 3：Harangi 2023（Pearson 相关惩罚）、Barlow Twins、VICReg、Repulsive；λ 设定。
- [x] `notes.md` 裁决输入表与阻塞清单。
- [ ] 未 commit（按任务要求）。
