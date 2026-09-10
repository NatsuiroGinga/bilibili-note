# 2026-09-10 DGA 对抗规避病灶文献入库检查点

工作树：`/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908`（分支 `exp/ch3-drift-20260908`）
用途：为第三章 DGA 对抗鲁棒（组相对对抗优化）方案提供病灶原文的全文核验笔记，并履行对抗训练先例查重义务。

## 1. 题录核验（arXiv API + PDF 元数据实录）

查询命令：`curl -sL "https://export.arxiv.org/api/query?id_list=1804.01979,1902.08909,1905.01078"`

| 目标 | 任务给定线索 | 核验结果 | 裁定 |
| --- | --- | --- | --- |
| MaskDGA | 「作者 Pier Luca Lanzi 等」 | **arXiv:1902.08909v1**，`MaskDGA: A Black-box Evasion Technique Against DGA Classifiers and Adversarial Defenses`，作者 **Lior Sidi, Asaf Nadler, Asaf Shabtai**，2019-02-24 | 线索作者有误，编号题名正确 |
| CharBot | 「S.S.H. Joseph 等，NDSS'22 或类似」 | **arXiv:1905.01078v2**，`CharBot: A Simple and Effective Method for Evading DGA Classifiers`，作者 **Jonathan Peck, Claire Nie, Raaghavi Sivaguru, Charles Grumer, Femi Olumofin, Bin Yu, Anderson Nascimento, Martine De Cock**，2019-05-03 | 线索作者与刊物均有误，编号题名正确 |
| 「arXiv 约 1804.01979」 | 任务给的 MaskDGA 编号 | **实为 `Vortex core ordering in Abrikosov lattices`（Madhuparna Karmakar, R. Ganesh）**，凝聚态物理，与 DGA 无关 | **编号错误，已登记** |

线索人名复核：`rg -il "lanzi"` 全库仅命中 1 个无关文件；arXiv `au:"Pier Luca Lanzi" AND all:"DGA"` 零命中；`S.S.H. Joseph` 库内无 DGA 相关命中。判定为线索记忆偏差。

PDF 元数据佐证：
- `2019-Sidi-MaskDGA.pdf`：Author `Lior Sidi, Asaf Nadler, and Asaf Shabtai`；Keywords `Adversarial learning, Deep learning, Botnets, DGA`；acmart 排版，12 页
- `2019-Peck-CharBot.pdf`：正文首页作者与 arXiv 一致；pdfTeX 2019-05-31 生成，12 页

**重要修正**：任务书描述 MaskDGA 为「MCMC/遗传式字符替换」，**与原文不符**。原文是 JSMA（雅可比显著图）改造的**梯度显著度驱动替换**，无 MCMC、无遗传算法（§4.4–§4.5，p.4）。任务书描述 CharBot 为「插入/替换/重复字符」，**与原文不符**。原文是**只有替换**、恰好 2 个位置、均匀随机采样（§III 算法 1，p.4；§VI-A，p.9）。

## 2. 既有制品状态（入库前）

**raw 与 wiki 的这两篇均已存在，但全部处于未提交状态**（`git status` 显示 `??`）。既有笔记题录**正确**，但内容为精简索引式，未覆盖攻击机制精确形式、威胁模型、被评测模型清单与对抗训练消融原始数字。本轮依本地 PDF 全文重写补全。

## 3. 全文提取

MinerU token 模式（`mineru-open-api extract -l en`，v0.5.9），非 flash-extract。为避免猜测页码，**同时提取 `-f json` 以取得 `page_idx`**，全部页码锚点由 JSON 实测而非估算：

- `/tmp/dga-adv-20260910/charbot/`（md）与 `/charbot-json/`（json），12 页
- `/tmp/dga-adv-20260910/maskdga/` 与 `/maskdga-json/`，12 页
- `/tmp/dga-adv-20260910/robust/` 与 `/robust-json/`，17 页

中间物在 `/tmp/` 下，不进入 `raw/`、`wiki/`。

## 4. 第三篇查重（对抗训练用于 DGA）——**有明确命中，已入库**

**arXiv:2404.06236《Towards Robust Domain Generation Algorithm Classification》**，Arthur Drichel, Marc Meyer, Ulrike Meyer（RWTH Aachen），2024-04-09；正式出处 **ACM ASIA CCS '24**，DOI `10.1145/3634737.3656287`，17 页。

- 这是**「离散扰动对抗训练用于 DGA」的正式先例**：32 种白盒攻击（19 种未硬化模型 FNR≈100%）、可控离散化把嵌入向量映射回合法 e2LD、提出「联合对抗训练」（嵌入空间 + 离散域交替）。
- **查重结论：本课题不得再把"离散扰动对抗训练用于 DGA 检测"作为新机制主张**；增量必须落在该文未覆盖的维度。
- 原件已下载：`raw/papers/attack-detection/2024-Drichel-Robust-DGA-Classification.pdf`（1.0 MB，17 页）
- 开源库：<https://gitlab.com/rwth-itsec/robust-dga-detection>

其他检索命中（未入库，登记为候选）：SMAD（Machine Learning with Applications 2026，改进注意力机制的鲁棒 DGA 检测，对抗 DGA 上 AUC 0.72）；一篇对抗域生成与防御的系统性文献综述（同刊 2026，32 篇原始研究，指出对抗训练是最常见防御，占 65.63%）。

本地混合索引：**向量通道不可用**（`intfloat/multilingual-e5-small` 非本地缓存且无法解析），lexical 降级亦因建索引需向量模型而失败。**登记为「本地索引未能运行」，非「本地无此内容」。**

## 5. Zotero

| 条目 | 状态 |
| --- | --- |
| CharBot（preprint） | **已在库**，key `CPILDEPS`，且已在 `attack-detection` 集合内（与 PDF 附件 `H3PWHIIV`） |
| MaskDGA（preprint） | **已在库**，key `K3VYSJSY`，且已在 `attack-detection` 集合内（与 PDF 附件 `6A67NG7A`） |
| Drichel 2024（2404.06236） | **本次新增**，key `QVI7J5QD`，paper + PDF 附件 `KDM2P543` 均已生成 |

**未关闭阻塞**：新增条目 **未能写入 `attack-detection` 集合**。原因：`zotero_move_items_to_collection` / `zotero_update_item` 的写路径指向 **Web 库**（`api.zotero.org/users/21101662`），而该 Web 库既无 `QVI7J5QD` 条目、也无 `attack-detection` 集合（Web 库仅 6 个集合，本地库 16 个）；本地 HTTP API（`localhost:23119`）对写操作返回 `501 Method not implemented`。**需用户在 Zotero 桌面端手动把 `QVI7J5QD` 拖入 `attack-detection` 集合**，或先完成一次同步。

## 6. 主代理 E-A1 探针的算子忠实度答复（2026-09-10 已回发）

已针对 `.Codex/docs/2026-09-10-DGA对抗鲁棒组相对方案/e-a1-attack-success-probe.py` 给出四条必改项：

1. **删除「插入 '.'」**——两篇原文都不做插入；MaskDGA §5.3 p.6 硬编码禁止非点→点。
2. **删除「相邻交换」「字符重复」**——两篇原文均无；重复字符直接抬高 B-RF/FANCI 的 Ratio of Repeated Characters 特征（CharBot 表 II，p.6）。
3. **修 bug**：探针 `ALPHA[26:]` = `"0123456789-"`，实际把字母替换成数字/连字符，与其 docstring「字母→另一字母」不符；按 §III p.4 应从字母+数字+连字符全集均匀采样且不等于原字符。
4. **口径与预算**：CharBot 判定用固定 FPR（0.1%/1%）标定阈值，MaskDGA 用多类 argmax；`score<0.5` 无文献对应。两篇均**每输入域名恰好 1 个对抗域名**，P0 的 4 变体须分别报 per-variant 与 any-of-4 ASR。
5. **语义登记**：P0 扰动 DGA 域名，对应 **MaskDGA** 而非 CharBot——CharBot 从良性 Alexa 出发生成新域名，**不扰动 DGA 样本**。

两篇笔记已把上述算子精确形式（含"未使用哪些算子"的表）写入正文，供 P0 修正直接引用。

## 7. Drichel 2404.06236 精读答复（2026-09-10，主代理五问）

本地 PDF 已由 `mineru-open-api extract`（token 模式，md + json 双格式，后者提供 `page_idx` 页码锚点）转换，逐节精读正文 §1–§8 与附录 A。以下页码为本地 PDF 物理页。

**(a) 联合对抗训练的精确形式**
- **内层（对抗域生成）**：不是 RL 采样，是"每种攻击各生成一批样本"。算子即 32 种攻击本身：5 种嵌入空间梯度攻击（PGD $L_2$/$L_\infty$、C&W $L_2$、BAT $L_2$/$L_\infty$）× 6 种离散化方案（{LCO, LBF} × {$L_2$,$L_\infty$,$D_c$}）+ HotFlip + MaskDGA-WB（§4.3.1–§4.3.3，p.5–7）。
- **样本量**：离散域 AT 批为 **256 样本**，分 7 份（5 份嵌入空间攻击 + HotFlip + MaskDGA-WB），每份再按 6 种离散化细分，**部分攻击每批仅 6 个样本**（§4.4.2，p.7）。
- **超参每 minibatch 重采样**：$\varepsilon_2 \sim U(0.5,\sqrt{63\cdot128})$、$\varepsilon_\infty \sim U(0.01,1)$、HotFlip $n \sim U\{1..10\}$、C&W $\kappa \sim U(0,100)$ 且半数强制 $\kappa=0$（§4.4.1，p.7）。
- **外层**：混合 minibatch 上的标准监督梯度更新。**早停失效**（验证损失先升后降），改用**固定 50 epoch 上限**（§4.4，p.7）。
- **交替**：**随机交替，无固定轮数、无权重调度**（§4.4.3，p.7 原话 "randomly alternating"）；作者自述 batch 类型权重是**可调而未调**的超参（§7，p.12）。
- **复现缺口**：未报告分类器训练的优化器、学习率、批大小与损失函数。

**(b) 32 种攻击是否覆盖本方两个算子**
- **MaskDGA 式半替换：已覆盖**。作者把 MaskDGA 重实现为白盒攻击 `MaskDGA-WB`（§4.3.3，p.7）；附录 **A.3（p.16）给出算子级佐证**：`We do not list the Levenshtein distance as it either matches the number of flips for HotFlip or **half of the average domain length for MaskDGA-WB**`。Table 4（p.16）MaskDGA-WB FNR 0.99533。
- **CharBot 式 2 位替换：未覆盖**。全文仅出现在 §2.4 Table 1（p.4）相关工作对比表与参考文献 [46]，**不属于 36 个攻击中的任何一个**；ReplaceDGA [26] 同表亦只列不实现。

**(c) 评价协议**
- 分层五折交叉验证，每折 75% 训练 / 5% 验证 / 20% 测试（§4.2，p.5）；基线早停 patience=5。
- **攻击隔离**：对抗样本只在该折**测试集**的 AGD 上生成，确保未进训练（§4.2，p.5）。
- 主指标 FNR，五折平均。FPR 工作点：真实世界只展示 ≤0.01；§7（p.11–12）报 **FPR=0.001 与 0.01** 的 TPR。
- **无 F1 护栏**（全文 `F1` 零命中）；干净性能由**有界 ROC-AUC + 未知 DGA TPR + 固定 FPR 下 TPR** 三件套承载。
- LOGO 逐组留出、不做成对留出（§5.3，p.10）。
- 附录 Table 3（p.15）另报 useable 率、唯一域名比、嵌入/编辑距离与置信度。
- **与 P0 的差异**：P0 的 `score<0.5` 无文献对应——本文用 FNR 与 FPR 标定工作点。

**(d) 决定性答案：三项机制一个都没用**
- 零命中：`entropy` **0**、`trust region`/`trust-region` **0**、`reward` **0**、`policy gradient` **0**、`reinforcement` **0**。
- 非零但全为误命中：`advantage` 2（英文日常义）、`group` 5（leave-one-**group**-out / "we group the attacks"）、`critic` 7（"**critic**al analysis"）、`KL` 5（脚注/参考文献如 `rklk_ySYPB`、`Klensin`、`Khaled`）。
- **结论：其联合 AT 是纯监督式混合批对抗训练，不含组相对优势聚合、不含熵受控项、不含信任域软门 → GRPO 机制层差量存活，本文不构成占位。**
- 限定：§7（p.12）把 batch 类型权重列为未调项，§5.4（p.10）观察到不同折收敛到不同局部最优——"训练动态控制"是其自认空白，但**不得声称该文做过这些控制**。

**(e) 对抗训练的干净指标代价**
- 有界 ROC-AUC（Siemens 3.73 亿良性 NXD，§6.1，p.11）：**0.81335 → 0.82894（+1.56%）**。
- TPR@FPR=0.001：69.0% → ≥73.3%；TPR@FPR=0.01：89.5% → ≤91.5%（§7，p.11–12）。
- 未知 DGA 平均 TPR（Table 5，p.16–17）：**0.75810 → 0.80525（+4.71 个百分点）**，27 个中 21 个升高。
- **未观察到鲁棒性—性能权衡**（摘要 p.1、§6.1、§8 三处重申），归因于 AT 的正则效应；训练与测试相隔约 17 个月。
- **反向个案**：bigviktor 0.32320→0.28760、qsnatch 0.12244→0.08677、chaes 0.00440→0.00330——"无代价"是均值陈述。
- **口径**：该"无代价"仅指干净/真实世界指标；对抗鲁棒性未清零（HotFlip 仍 96% FNR）。

## 8. 2024–2026 DGA 对抗鲁棒补充检索（arXiv API 题录级）

检索式与结果（全部按 `submittedDate` 降序，只登记题录级命中，摘要级不计入结论）：

| 检索式 | 2024 起命中 |
| --- | --- |
| `ti:"domain generation algorithm"` | 2603.03270、2411.03307、2404.06236（2409.17063 为病理学 DG，排除） |
| `abs:"domain generation algorithm" AND abs:"adversarial"` | 2404.06236（2403.06174 为域泛化，排除） |
| `abs:"DGA classifier" AND abs:"robust"` | 2605.10436、2404.06236 |
| `ti:"DGA"` / `ti:"domain generation"` | 被 "Domain Generalization" 大量污染，已弃用该式 |

去重后 2024–2026 相关命中 **4 篇**：`2404.06236`（本次精读对象）、`2411.03307`（LLM DGA 检测，**已入库**）、`2605.10436`（DRIFT，**已入库，本课题对象论文**）、`2603.03270`（Gravity Falls：面向移动端 smishing 的 DGA 检测方法比较，2026-03-03，Dorion Wong & Hastings）。

**结论：2024–2026 未出现第三篇"DGA 对抗训练/对抗鲁棒"的 arXiv 新论文。** `2603.03270` 是 DGA 检测泛化评价（半合成 smishing 数据集、四类技术簇），**不属对抗方向**，登记为候选未入库。

## 9. 完成清单

- [x] 题录核验（含线索纠错登记）
- [x] 全文提取（三篇，含 JSON 页码锚点）
- [x] 重写 CharBot 结构化笔记
- [x] 重写 MaskDGA 结构化笔记
- [x] 新增 Drichel 2024 结构化笔记
- [x] Zotero 新增第三篇（集合归属待用户手动完成，见 §5）
- [x] INDEX.md 更新（三条目 + 查重结论）
- [x] 主代理 E-A1 算子忠实度答复
- [ ] git 提交
