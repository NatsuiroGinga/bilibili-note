# 检查点：RLOO 攻击者方向采纳与五＋一篇近邻入库（2026-09-11）

> **任务来源**：用户裁决（a 方向修正为「条件化一步攻击策略 ＋ RLOO policy gradient」）＋ ChatGPT 方法升级调研报告 [deep-research-report (13).md](../chatgpt-handoffs/inbox/deep-research-report%20(13).md)（**外部候选**，主代理裁决采纳）。
> **本文件用途**：入库过程的**可恢复检查点**（原件、标识、哈希、页数、笔记路径、阻塞、待办）。**结论性内容不在此处**——机制与差量见方案 `task_plan.md` §5.10，来源索引见 [第三章-方法来源台账](../../../thesis/methods/第三章-方法来源台账.md)。

## 一、入库清单（五＋一篇）

| # | 文献 | 稳定标识 | 原件（`raw/`） | SHA-256（前 16） | 页数 | 笔记（`wiki/`） | 证据等级 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | DeepDGA | arXiv `1610.01969v1`；ACM AISec 2016 | `raw/papers/attack-detection/2016-Anderson-DeepDGA.pdf` | `4938680dd68fc80a…` | 9 | `wiki/papers/attack-detection/dga/2016-Anderson-DeepDGA.md` | 报告 B → **本地全文** |
| 2 | PKDGA | arXiv `2212.04234v1` | `raw/papers/attack-detection/2022-Nie-PKDGA.pdf` | `8cf08a87244cb0f1…` | 12 | `wiki/papers/attack-detection/dga/2022-Nie-PKDGA.md` | 报告 A → **本地全文** |
| 3 | DomainGAN | arXiv `1911.06285v3` | `raw/papers/attack-detection/2019-Corley-DomainGAN.pdf` | `62b9d052b476838d…` | 10 | `wiki/papers/attack-detection/dga/2019-Corley-DomainGAN.md` | 报告 B → **本地全文** |
| 4 | Anderson 2018 RL malware | arXiv `1801.08917v2` | `raw/papers/attack-detection/2018-Anderson-RL-Malware-Evasion.pdf` | `cdab73d6a688666c…` | 9 | `wiki/papers/attack-detection/2018-Anderson-RL-Malware-Evasion.md` | 报告 A → **本地全文** |
| 5 | MAB-Malware | RAID 2020；arXiv `2003.03100v3` | `raw/papers/attack-detection/2020-Song-MAB-Malware.pdf` | **本地原已有** | — | `wiki/papers/attack-detection/2020-Song-MAB-Malware学习型黑盒规避.md` | 本地已有全文笔记 ⇒ **无需重复入库** |
| 6 | RLOO（Ahmadian 2024） | arXiv `2402.14740v2` | `raw/papers/grpo/2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE-Style.pdf` | **本地原已有** | — | `wiki/papers/grpo/2024-Ahmadian-Back-to-Basics-RLOO-REINFORCE风格.md` | 本地已有全文笔记 ⇒ **无需重复入库** |

**下载方式**：`curl` 直取 arXiv PDF（arXiv 官方源，合法可信）；四篇全部通过 `pdfinfo` 核验页数与文件完整性，SHA-256 见上（完整值见 git 提交与原件）。

## 二、转换与阅读

- 转换工具：**MinerU `extract`**（精度模式，token 已配置），产物落 `/tmp/ch3-rloo-ingest-20260911/<篇名>/`（**临时目录，不入库**）。
- 逐篇**全文阅读**（正文至结论；参考文献未逐条录入）。
- **共同限制（已写入各笔记）**：MinerU 转换产物**无页标记** ⇒ 四篇笔记一律按**节号／式号／表号**锚定，**页码待补**（正文引用数字前须回 PDF 逐页核对后回填）。

## 三、阻塞与待办

1. **页码待补**（四篇全部）：正文若需 `p.N` 级引用，须用 PDF 阅读器逐页核对；在此之前只写节号。
2. **Zotero 未导入**（四篇）：本轮只做 `raw/` ＋ `wiki/`，未走 Zotero MCP 导入；若后续要在正文引用，按 `raw/AGENTS.md` 补导入与题录核验。
3. **版本提示**：PKDGA 与 DomainGAN 的**会议归属未核验**（本地只有 arXiv 预印本），引用须注明版本。
4. **报告节号只作线索**：外部报告给出的节号（如 PKDGA `§III-B`、Anderson `§5–6`）已在本地全文核对；**正文引用一律以本地笔记的节号／表号为准**。
5. **DeepDGA 会议版本**：本地为 arXiv `1610.01969v1`；AISec 2016 正式版未比对分页。
6. **五篇共同用途**：只作**排重与旁证**，不作本课题任何数值的比较基准（已写入各笔记的 `cannot_support`）。

## 四、与其它文件的关系

- 机制与差量定位（四层）→ 方案 `task_plan.md` §5.10.5。
- 入库登记表（方案侧）→ `task_plan.md` §5.10.6。
- 来源索引（台账侧）→ `thesis/methods/第三章-方法来源台账.md` §三（Anderson 2018／MAB-Malware）与 §四（DeepDGA／PKDGA／DomainGAN）。
- 全局索引 → `wiki/papers/attack-detection/INDEX.md`（DGA 生成侧新块 ＋ 第 2 层 Anderson 2018 条目）。
- 恢复卡状态 → `.Codex/docs/DRIFT/DRIFT第三章恢复卡.md` §五／§六。
