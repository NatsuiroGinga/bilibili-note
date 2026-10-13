# 核查笔记（2026-10-13）

每完成一篇全文即落盘。**全文证据来源：Zotero 官方 PDF 附件（非摘要）。**

## 环境阻塞（重要）

本任务执行环境**无 shell、外网 WebFetch 全域名被阻断**（papers.nips.cc / arxiv.org / openreview.net / github.com / huggingface.co / ar5iv.org 均报 "Unable to verify if domain is safe to fetch"）。可用通道：`WebSearch`（返回可含 PDF 正文片段）、Zotero MCP（可导入并服务端抓取 PDF、可提取全文）。

**后果**：**无法把二进制 PDF 写入 `raw/papers/attack-detection/`**。两篇 wiki 笔记的 `source_pdf` 暂为悬空，已在笔记顶部与评估报告 §五登记。补齐命令已写入评估报告 §五。

## 论文 A：RS-Del（Huang 等，NeurIPS 2023）

- 状态：**全文级已读**（Zotero 全文提取，官方 PDF，NeurIPS 2023 相机就绪版，arXiv:2302.01757v3）
- Zotero：导入成功，key `CW84X3AT`，**PDF 已附加**
- 官方页：https://proceedings.neurips.cc/paper_files/paper/2023/hash/3ba82362eb0aa75487069f19fde794fe-Abstract-Conference.html
- PDF：https://papers.nips.cc/paper_files/paper/2023/file/3ba82362eb0aa75487069f19fde794fe-Paper-Conference.pdf
- 代码：https://github.com/Dovermore/randomized-deletion
- wiki 笔记：`wiki/papers/attack-detection/2023-Huang-RS-Del编辑距离认证鲁棒性.md`

关键锚点：§3.1 式2/3（平滑分类器+阈值）；§3.2 Remark 2（平滑算子无需对齐威胁模型）；§3.3（Training：须用删除扰动训练；chunking）；§4.1–4.3（Lemma 4、Theorem 5 式14、Table 1、Theorem 7）；§5（MalConv、91%@128B、Table 2 物理页 8）；Appendix D.3/E.1（FPR 校准 0.5%、非对称 η、582 字节，Table 8 物理页 27）；Prop 11 证明物理页 35。

待核：Table 1 中 `{del,ins}` 行在抽取文本中与 `{ins}` 行相同，须回原件复核。

## 论文 B：Curriculum as Transport（Shin & Alvarez-Melis，COLM 2026）

- 状态：**全文级已读**（Zotero 全文提取，官方 PDF，页眉 `Published as a conference paper at COLM 2026`）
- Zotero：导入成功，key `I3L65FTP`，**PDF 已附加**
- PDF：https://export.arxiv.org/pdf/2609.09099 ；OpenReview：https://openreview.net/pdf?id=vksN9ocqqh
- wiki 笔记：`wiki/papers/attack-detection/2026-Shin-课程学习与Wasserstein测地线.md`
- **本次首次完成该文入库**（此前仅见于 `.Codex/docs/chatgpt-handoffs/`，`课程式对抗训练-在线视角` 笔记已登记须引本篇）。

关键锚点：§3.1（P_t 测地线插值、τ 端点平滑度、γ 遍历节奏、默认 τ=1/γ=1）；§3.2（12 任务 33 难度轴）；§4（context-dependent；easy-to-hard > 等曝光静态；99/99、92/99）；§5（9×9 τ,γ 网格）；§8（结构化难度空间）；Appendix D（预训练 SFT 上效应大幅减弱）。**全文无定理。**

## 交付清单

- [x] wiki 笔记两篇
- [x] INDEX.md 更新（新增「编辑距离证书与课程运输理论」一节）
- [x] Zotero 入库两篇（含 PDF 附件）
- [x] 评估报告 `thesis/methods/第三章-编辑距离证书与课程理论评估.md`
- [ ] **raw/ PDF 副本（阻塞：无 shell，主代理执行）**

## 裁决摘要（详见评估报告）

- **RS-Del**：层次修正——与本课题**训练方法**不在同一层（它是推理时认证），**互补但需补缺口**；其证书**不直接适用于**本课题「共享前缀替换」邻域（几何不匹配，须重做 §4.3 邻域最小化）；不作竞争证据，也不作证书背书。
- **Curriculum as Transport**：修正——**下调**课程增益先验（预训练/真实数据上效应减弱）；**不动 D-7 判据**；其 τ/γ 精细化与 D-7 的 2 档硬阶跃粒度不匹配，只能作 D-7 **之后**的候选。
- 两篇**均不推翻**机制方案。
