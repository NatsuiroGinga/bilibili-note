# 联网补齐 — 工作笔记（滚动落盘，不事后补写）

RESEARCH_ROUTE=RWKV。建立：2026-08-19。执行者：联网补齐代理（Claude Opus 5）。

**本文件是本任务目录既有检查点体系的第四份滚动笔记**，与 `notes.md`（CP-01…CP-09）、
`轴A-1.2.1-分组框架与核验notes.md`（CP-A0…CP-A2）、`轴二-notes.md`（CP-B01…CP-B04）并列。
未另起任务目录。**未新建目录、未修改 `thesis/`、未启动 GPU 或远程命令。**

---

## CP-C00　本轮开工前的状态重建（实测，必读）

任务简报按 `盘点结论.md` 第八节的 30 条派单，但**盘点之后已有两个并行代理联网补过一轮**，
简报中的多条实际已关闭。开工前逐条实测核对如下，后续代理不要重做。

实测命令与结果：

```
Glob raw/papers/**/*.pdf                        → 457（盘点时 446，已新增 11）
Glob raw/papers/traffic-classification-evolution/*  → 5
Glob raw/papers/attack-detection/drift/*            → 6
```

**已由 `轴A` 代理关闭（原件已入库，笔记已写，见 CP-A2）**：
Sommer & Paxson、Deep Packet（Lotfollahi）、Rezaei & Liu 综述、Moore & Zuev、Karagiannis BLINC。
落点 `raw/papers/traffic-classification-evolution/`。

**已由 `轴二` 代理关闭（原件已入库，笔记已写，见 CP-B04）**：
Jordaney TRANSCEND、Yang CADE、Andresini INSOMNIA、Barbero TRANSCENDENT、
陈子涵《计算机学报》综述、Azizzadenesheli RLLS 可读副本。
落点 `raw/papers/attack-detection/drift/` 与 `chinese-surveys/`。

**已由 `notes.md` CP-09 关闭的题录**：Zhang ACSAC 2023 pp.565-579、Clausen CBAM
*Computers* 10(6):79、Hu BAYWATCH pp.479-490、Li Sensors 24(7):2122、Kim TTA-AD pp.13113-13121、
Ben-David JMLR W&CP 9:129-136、Jacobs CCS'22 pp.1537-1551。
**已由 CP-A2 关闭**：Arp USENIX Sec 22 pp.3971-3988、Cui CBSeq IEEE TIFS 18:5011-5025。

**结论：简报 30 条中已关闭 21 条。本轮真实剩余 = 优先级二的 GeM 1 条
＋ 优先级一未关闭的 8 条 ＋ 题录页码未关闭的 8 条 ＋ 损坏原件未关闭的 3 条
＋ 付费墙遗留 3 条。**

---

## CP-C01　本轮的硬工具约束（**影响交付形态，必须让主代理知悉**）

本代理的可用工具集为 `Read / Write / WebSearch / WebFetch / Grep / Glob` 加 Zotero 系列。
**没有 `Bash`，也没有 `Edit` 与 `Skill` 工具。**

由此产生两条不可回避的后果：

1. **本代理无法把 PDF 二进制写入 `raw/papers/`。** `Write` 只能写文本，`WebFetch` 只返回
   转换后的 markdown 而非原始字节。因此本轮**不可能**独立完成 `raw/AGENTS.md` 要求的
   「原件落盘」动作。可行替代路径是 Zotero 导入：`zotero_add_items_by_identifier`
   会把 PDF 下载进 `/Users/bilibili/Zotero/storage/<8位键>/`，该路径可用 `Read` 直接读取全文。
   **本轮据此把「取得可核验全文」与「原件落盘」拆成两步**：本代理完成前者并给出
   精确的 `源 URL → 目标路径` 落盘清单，后者由具备 `Bash` 的主代理一次性执行。
2. **本代理不写 `wiki/papers/` 笔记。** `wiki/AGENTS.md` 第 19 行要求 `source_pdf`
   必须指向 `raw/papers/` 中**存在的**原件。在原件尚未落盘时写笔记，会制造
   `盘点结论.md` 第 3.1 节实测为 **0 篇**的「有笔记无原件」缺陷。
   本轮改为：全文证据（含精确页码与公式号）写入本检查点，
   待主代理落盘原件后按既有体例转写为 `wiki/papers/` 笔记。

**与技能链路的偏差（显式声明，不静默择一）**：任务简报要求用 `Skill` 工具显式调用
`planning-with-files`、`literature-reviewer`、`citation-verification`。
**本会话不存在 `Skill` 工具**（与 `盘点结论.md` 第九节记录的
「`literature-reviewer` 不在技能清单中」属同型环境限制）。
本轮按三者的**方法要求**执行——接续既有检查点而不另起、每组查询立即落盘、
题录逐条回稳定标识符核验——但无法产生 `Skill` 工具的调用记录。

**与 `citation-verification` 的既有冲突，沿用前一轮裁决**：该技能要求以 Google Scholar
确认并取 BibTeX；`raw/AGENTS.md` 第 21 行要求用 DOI／arXiv／出版社稳定标识符，
第 24 行禁止用搜索引擎结论冒充证据。**采纳仓库规则**。
本轮所有题录取自 **CrossRef（出版商存缴元数据）** 或 **PMLR 官方论文页**，
`WebSearch` 只用作发现入口，其返回的页码一律**不采信**、一律回 CrossRef 复核。
实例：Bilge 与 Yen 两条的页码先由 `WebSearch` 提示，随后经
`api.crossref.org/works/<DOI>` 独立确认后才登记。

---

## CP-C02　题录核验（11 条全部关闭，来源＝CrossRef 或 PMLR 官方页）

**证据等级：出版商存缴元数据（A）。查询式与来源 URL 逐条列出，可复核。**

| # | 条目 | 关闭结果 | 来源 URL |
| --- | --- | --- | --- |
| 1 | Lipton BBSE（第三章 `[5]`） | ICML 2018，**PMLR 80: 3122-3130** | `https://proceedings.mlr.press/v80/lipton18a.html` |
| 2 | Ilse 注意力 MIL（第三章 `[7]`） | ICML 2018，**PMLR 80: 2127-2136** | `https://proceedings.mlr.press/v80/ilse18a.html` |
| 3 | Alexandari MLLS（轴二 B14） | ICML 2020，**PMLR 119: 222-232** | `https://proceedings.mlr.press/v119/alexandari20a.html` |
| 4 | Zhu MIDAM（轴二 B34） | ICML 2023，**PMLR 202: 43205-43227** | `https://proceedings.mlr.press/v202/zhu23l.html` |
| 5 | Bilge DISCLOSURE（轴二 B26） | ACSAC'12，**pp. 129-138**，DOI `10.1145/2420950.2420969` | `https://api.crossref.org/works/10.1145/2420950.2420969` |
| 6 | Yen Beehive（轴二 B27） | ACSAC'13，**pp. 199-208**，DOI `10.1145/2523649.2523670` | `https://api.crossref.org/works/10.1145/2523649.2523670` |
| 7 | Andresini INSOMNIA（轴二 B2） | AISec'21，**pp. 111-122**，DOI `10.1145/3474369.3486864` | `https://api.crossref.org/works/10.1145/3474369.3486864` |
| 8 | Gulcehre Lp 池化（第三章 `[8]`） | ECML PKDD 2014，LNCS，**pp. 530-546**，DOI `10.1007/978-3-662-44848-9_34`，ISBN 978-3-662-44847-2 / 978-3-662-44848-9 | `https://api.crossref.org/works/10.1007/978-3-662-44848-9_34` |
| 9 | Pevný & Somol 树结构 MIL（轴二 B29） | **AISec'16，pp. 83-91**，DOI `10.1145/2996758.2996761` | `https://api.crossref.org/works/10.1145/2996758.2996761` |
| 10 | Pevný & Somol 神经网络形式化（第三章 `[6]`） | **ISNN 2017，LNCS，pp. 135-142**，DOI `10.1007/978-3-319-59072-1_17` | CrossRef 题录检索 `query.bibliographic` |
| 11 | Radenović GeM（第三章 `[9]`／轴二 B4） | **IEEE TPAMI, 2019, 41(7): 1655-1668**，DOI `10.1109/TPAMI.2018.2846566` | Zotero 经 CrossRef 导入，条目键 `IMX3RMZ9` |

### 三处纠正既有记录的发现（**逐条影响正文写法**）

1. **第三章 `[6]` 可由预印本升为正式发表。** 引注核验报告记「原件首页未见正式会议或期刊名」，
   按预印本著录。实测存在正式版：**ISNN 2017, LNCS, pp. 135-142, DOI `10.1007/978-3-319-59072-1_17`**。
   该条支撑的是多示例学习的定义性表述，升级后证据等级由预印本变为同行评议正式发表。
2. **第三章 `[8]` 与轴二 B29 的「文件名标注无原件依据」是文件名对的、原件缺版权页。**
   `2014-Gulcehre-…-ECMLPKDD.pdf` 与 `2016-Pevny-…-AISec.pdf` 两处，
   此前因原件文本层查不到会议名而判为「文件名标注不可采信」。
   实测两者的正式载体**恰好就是文件名所标的 ECML PKDD 与 AISec**。
   原判定「不可采信」应改为「原件为作者版/预印本，正式载体经 CrossRef 核定」。
   **交叉校验**：Pevný AISec'16 的 DOI 前缀 `10.1145/2996758` 与本库已有的
   Anderson & McGrew AISec'16（pp. 35-46，DOI `10.1145/2996758.2996768`）同属一册论文集，互证成立。
3. **Radenović 的年份是 2019 不是 2018。** `盘点结论.md` 与第三章核验报告均写「TPAMI 2018」，
   那是 DOI 与在线优先出版的年份；**正式卷期为 2019 年第 41 卷第 7 期**。
   GB/T 7714 著录须写 2019, 41(7): 1655-1668。

---

## CP-C03　GeM 原始定义的全文核验（**关闭第三章阻断项 B4**）

- Zotero 条目：`IMX3RMZ9`；随附 PDF 实测路径
  `/Users/bilibili/Zotero/storage/ZFFNL4Q9/Radenovic 等 - 2019 - Fine-Tuning CNN Image Retrieval with No Human Annotation.pdf`（7.4 MB）。
- **该副本是 arXiv 版（arXiv:1711.02512），页码为 arXiv 自身页序，不是 TPAMI 的 1655-1668。**
  下列页码定位一律按 arXiv 版页序，正式引用页码须用 CP-C02 第 11 行的 TPAMI 卷期页。
- 证据等级：**A（全文核验）**，但正文引用须注明本机可读副本为作者版。

**关键位置（arXiv 版 p.4，§3.2「Generalized-mean pooling and image descriptor」）**

- 式 (1) 为最大池化（MAC 向量），式 (2) 为平均池化（SPoC 向量）。
- **式 (3)** 给出广义均值：
  `f^(g)_k = ( (1/|X_k|) · Σ_{x∈X_k} x^{p_k} )^{1/p_k}`
- 同页原文：`Pooling methods (1) and (2) are special cases of GeM pooling given in (3),
  i.e. max pooling when p_k → ∞ and average pooling for p_k = 1.`
- 同页原文：`The pooling parameter p_k can be manually set or learned since this operation
  is differentiable and can be part of the back-propagation.`
  式 (4)、式 (5) 分别给出对 `x_i` 与对 `p_k` 的偏导。
- arXiv 版 p.5：可每个特征图一个 `p_k`，也可全局共享 `p_k = p, ∀k ∈ [1,K]`；
  图 3 图题记微调后的 VGG 用单一 `p`，**收敛到 2.92**。
- 论文第 (3) 条贡献自述：`We propose a trainable pooling layer that generalizes existing
  popular pooling schemes for CNNs.`

**对本课题的意义（两处，一次补齐关两个阻断）**

1. **第三章 `[9]` 的 B4 可按「提出＋应用」两条引注著录**：Radenović 等 2019 为幂平均可学池化的
   提出方，Revaud 等 2019 ICCV（pp. 5107-5116，本机有原件）为检索目标联合训练的应用方。
   原 B4 的第二方案（只引 Revaud、措辞不暗示首创）仍然成立，本轮把成本更高但更稳的第一方案备齐。
2. **第二章 2.3 的幂平均定义式有了父概念出处**：式 (3) 与「`p→∞` 取最大、`p=1` 取平均」
   的插值语义，正是机制二可学幂平均池化的算子族来源。
   与轴二 B34（Zhu MIDAM 的 `smoothed-max`）构成同族两条近邻，1.2.2 须同时对比。

---

## CP-C04　Zotero 批量导入结果（17 条，实测逐条状态）

方法：`zotero_add_items_by_identifier`，标识符一律取 DOI 或 arXiv 编号，
**不凭记忆写编号**（本仓库已有两起凭记忆写标识符导致误下载的事故，见 `轴二-notes.md` CP-B04）。
对未自动附 PDF 者再跑一次 `zotero_find_and_attach_pdfs`，**9 条全部仍未取得**。

| 条目 | 标识符 | Zotero 键 | PDF | 轴 |
| --- | --- | --- | --- | --- |
| Radenović GeM, TPAMI | `10.1109/TPAMI.2018.2846566` | `IMX3RMZ9` | **有** | 轴二／第二章 2.3 |
| Panchenko 网站指纹（互联网规模） | `10.14722/ndss.2016.23477` | `RDT8GVZJ` | **有** | 轴一 A7 |
| Taylor 等 TIFS 2018（AppScanner 期刊版） | `10.1109/TIFS.2017.2737970` | `3BS8TBSZ` | **有** | 轴一 A6 |
| Garg 标签移位统一视角 | `arXiv:2003.07554` | `UIBQVTXN` | **有** | 轴二（损坏件替代） |
| Hassan NoDoze, NDSS 2019 | `10.14722/ndss.2019.23349` | `3K6INJU2` | **有** | 轴二（前序付费墙） |
| Velan 等加密流量分类综述 | `10.1002/nem.1901` | `N3WMX8TK` | 无 | 轴一 A1 |
| Papadogiannaki & Ioannidis, ACM CSUR | `10.1145/3457904` | `2FS2AZZ4` | 无 | 轴一 A1 |
| **Axelsson 基率谬误, ACM TISSEC** | `10.1145/357830.357849` | `3QFDD6RX` | 无 | 轴一 A3 |
| Draper-Gil 等 ISCX VPN-nonVPN | `10.5220/0005740704070414` | `EHABEJ79` | 无 | 轴一 A5 |
| Taylor 等 AppScanner, EuroS&P 2016 | `10.1109/EuroSP.2016.40` | `QU339MQ5` | 无 | 轴一 A6 |
| Sirinam 等 Deep Fingerprinting, CCS 2018 | `10.1145/3243734.3243768` | `T99JRF4S` | 无 | 轴一 A7 |
| Korczyński & Duda, INFOCOM 2014 | `10.1109/INFOCOM.2014.6848005` | `6URUWVAX` | 无 | 轴一 A8 |
| Aceto 等 MIMETIC, Computer Networks | `10.1016/j.comnet.2019.106944` | `GFTFERTD` | 无 | 轴一 A11 |
| **Saerens 等 2002, Neural Computation** | `10.1162/089976602753284446` | `IGZE6PN7` | 无 | 轴二（标签移位树根） |
| van der Laan 等 Super Learner | `10.2202/1544-6115.1309` | `K7EG9WMU` | 无 | 轴一 A10 |
| Apruzzese 等, NCA 2017 | `10.1109/NCA.2017.8171326` | `RIKJPMBD` | 无 | 轴二（前序付费墙） |
| Wang Wei 等一维卷积, ISI 2017 | `10.1109/ISI.2017.8004872` | `6589ITE3` | 无 | 轴一 A9 |

**题录已核，全文未得 = 12 条。** 按 `raw/AGENTS.md` 第 25 行登记为访问阻塞，
**不得写成「不存在」，也不得用摘要冒充全文**。这 12 条在补到全文前只能作背景，
不得支撑任何页码级论断。

**排除项（本轮按协调者新约束下调，不再找原件）**：
第三章正文已裁定不写字段预算、排除清单与泄漏防护，专门支撑「字段选择／泄漏防护」
的文献降级为背景。判定单元、实体级聚合、跨年度漂移、告警预算四类仍为刚需，
上表 12 条阻塞中属这四类的是 Axelsson（告警预算）、Saerens（跨年度先验校正树根）、
Apruzzese（实体级周期通信）三条，优先级最高。

---

## CP-C05　可执行落盘清单（交给具备 `Bash` 的主代理，一次跑完）

本代理已取得可读全文但无法写入 `raw/`。**5 篇 PDF 现已在 Zotero 存储中，可直接复制**：

| Zotero 存储路径 | 建议落盘路径 |
| --- | --- |
| `/Users/bilibili/Zotero/storage/ZFFNL4Q9/Radenovic 等 - 2019 - ….pdf` | `raw/papers/methodology/ranking/2019-Radenovic-GeM-Fine-Tuning-CNN-Image-Retrieval-TPAMI-arXiv1711.02512.pdf` |
| Panchenko NDSS 2016（键 `RDT8GVZJ`） | `raw/papers/attack-detection/fingerprinting/2016-Panchenko-Website-Fingerprinting-Internet-Scale-NDSS.pdf` |
| Taylor TIFS 2018（键 `3BS8TBSZ`） | `raw/papers/attack-detection/fingerprinting/2018-Taylor-Robust-Smartphone-App-Identification-TIFS.pdf` |
| Garg 标签移位统一视角（键 `UIBQVTXN`） | `raw/papers/methodology/2020-Garg-Unified-View-Label-Shift-Estimation-arXiv2003.07554.pdf`（**注意本库同名正常件已存在，须先查重**） |
| Hassan NoDoze NDSS 2019（键 `3K6INJU2`） | `raw/papers/attack-detection/entity-granularity/2019-Hassan-NoDoze-Threat-Alert-Triage-NDSS.pdf` |

落盘后须按 `raw/AGENTS.md`「下载即写笔记」补 `wiki/papers/` 笔记并更新 `INDEX.md`。
**Garg 一条须先与既有 `2020-Garg-Unified-View-Label-Shift-Estimation.pdf`（21 页，正常）比对，
确认是否同一论文；若同一篇则不重复落盘，只把损坏的 `2020-Garg-Unified-Label-Shift.pdf` 标记为废弃。**

---

## CP-C06　下一个代理的精确接续点

已完成：CP-C00 状态重建、CP-C01 工具约束声明、CP-C02 题录 11 条全关、
CP-C03 GeM 全文核验、CP-C04 Zotero 导入 17 条、CP-C05 落盘清单。

未完成，按优先级：
1. 上表 12 条无 PDF 者的开放获取入口尝试（作者主页、机构库、arXiv 对应版本）。
   **已试且失败的入口：Zotero 内置 PDF 级联（含 Unpaywall）对这 12 条全部返回未取得。**
2. 剩余题录：TESSERACT 的 USENIX Sec 2019 载体页码、TRANSCENDENT 的 IEEE S&P 2022 载体页码、
   Lo E-GraphSAGE 的 NOMS 2022 页码、Prasse 的正式载体、Sun 在线阈值的正式出处。
3. 损坏原件重下：Super Learner 两篇（题录已核，全文未得）。
