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

## 9. 干净:对抗配比核查（2026-09-10，主代理 P2/P3 提问）

**问题**：Drichel 联合 AT 中对抗样本与干净样本的混合比是多少？配比有无已知影响规律？

**确证答案：1:1。** minibatch 共 **512 = 256 干净 + 256 对抗**。证据是 **Fig 1 与 Fig 2 的批次构成条带（p.7）**：两条带 0–256 段标注 "Benign Samples"，256–512 段为各对抗攻击；§4.4.3 的 "we already split the **256** samples among 32 attacks" 仅指**对抗半批**。

> **修正我先前的错误表述**：上一轮与笔记初稿写作"离散域 AT 的批为 256 个样本"，遗漏了干净半批。正确为 512 = 256 干净 + 256 对抗。笔记已改。

**配比影响规律：Drichel 未提供。** 全文无配比消融；§7（p.12）只把"嵌入空间批 vs 离散域批"的权重列为**未调**项，不涉干净:对抗配比。其引用的 Kurakin et al. [33] 在 §4.4.1（p.7）被用于支持**扰动预算随机化**，与配比无关；核验该文摘要（arXiv:1611.01236）亦只提"对抗训练可降低干净输入上的测试误差"，**未给出配比规律**。→ **该规律属未验证命题，不得据 Drichel 断言。**

**对 P2/P3 的裁定**：
- 配比 1:1 **可登记为"对齐 Drichel"**，不是"无文献依据的任务化设定"。
- 但"**无干净代价**"（(e) 的 +1.56% AUC）**不可直接类比**，三点差异：① epoch 预算 Drichel 为固定 50（并因 AT 下**早停失效**、验证损失先升后降而禁用早停），数 epoch 的短跑很可能仍处上升段；② 判据不同——Drichel 用真实世界有界 ROC-AUC/未知 DGA TPR/固定 FPR 下 TPR，"干净 FPR 不增"更严，本文结果不能证明其成立；③ 模型与数据规模不同（偏差约简 ResNet、约 25 万平衡样本、84 DGA）。
- 且 Drichel 存在**反向家族** bigviktor/qsnatch/chaes（Table 5，p.16–17），说明其"无代价"即便在原文内部也只是均值陈述。

## 10. 完成清单

- [x] 题录核验（含线索纠错登记）
- [x] 全文提取（三篇，含 JSON 页码锚点）
- [x] 重写 CharBot 结构化笔记
- [x] 重写 MaskDGA 结构化笔记
- [x] 新增 Drichel 2024 结构化笔记
- [x] Zotero 新增第三篇（集合归属待用户手动完成，见 §5）
- [x] INDEX.md 更新（三条目 + 查重结论）
- [x] 主代理 E-A1 算子忠实度答复
- [x] git 提交（8b8c597、869e068、e6786e7）

---

# 第二批任务：report (8) 引用文献入库（2026-09-10 起）

来源：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/.Codex/docs/chatgpt-handoffs/inbox/deep-research-report (8).md`（52,701 字节，1103 行，25 处 ✅、27 处 ◐）。
目标：入库台账中标记 ✅ 与 ◐ 的文献（CharBot/MaskDGA/Drichel 2404.06236 已于本文件前段入库，不重复）。

## 11. 题录核验（arXiv API 实录，编号以核验为准）

**重要：我初始凭记忆给出的三个 arXiv 编号全部错误，均被 arXiv API 拦下**——

| 我记忆的编号 | 实际是什么 | 正确的目标编号 |
| --- | --- | --- |
| `1802.04821` | Evolved Policy Gradients（Houthooft 等） | **IDSGAN = `1809.02077v5`**（Lin, Shi, Xue） |
| `2001.01878` | Phase Transitions for the Information Bottleneck（Wu & Fischer） | **MAB-Malware = `2003.03100v3`**（Song 等） |
| `1911.09575` | Insider threats in Cyber Security（Mazzarolo & Jurcut） | **Problem Space = `1911.02142v3`**（Cortellazzi, Pendlebury, Arp, Quiring, Pierazzi, Cavallaro） |

核验通过的完整清单（题名、作者、日期均取自 arXiv API 返回）：

| # | 文献 | arXiv | 首版日期 | 状态 |
| --- | --- | --- | --- | --- |
| 1 | MAB-Malware: A Reinforcement Learning Framework for Attacking Static Malware Classifiers | `2003.03100v3` | 2020-03-06 | Song, Li, Afroz, Garg, Kuznetsov, Yin |
| 2 | Deep Reinforcement Learning based Evasion GAN for Botnet Detection（RELEVAGAN） | `2210.02840v1` | 2022-10-06 | Randhawa, Aslam, Alauthman, Khalid, Rafiq |
| 3 | Adversarial Co-Evolution of Malware and Detection Models: A Bilevel Optimization | `2604.22569v1` | 2026-04-24 | Jurečková, Jureček, Kozák, Lórencz |
| 4 | Multi-Agent Actor-Critic for Mixed Cooperative-Competitive Environments（MADDPG） | `1706.02275v4` | 2017-06-07 | Lowe, Wu, Tamar, Harb, Abbeel, Mordatch |
| 5 | Generating Adversarial Malware Examples for Black-Box Attacks Based on GAN（MalGAN） | `1702.05983v1` | 2017-02-20 | Hu, Tan |
| 6 | IDSGAN | `1809.02077v5` | 2018-09-06 | Lin, Shi, Xue |
| 7 | A Unified Game-Theoretic Approach to Multiagent RL（PSRO） | `1711.00832v2` | 2017-11-02 | Lanctot 等 |
| 8 | Stabilising Experience Replay for Deep Multi-Agent RL | `1702.08887v3` | 2017-02-28 | Foerster 等 |
| 9 | A Survey of Learning in Multiagent Environments: Dealing with Non-Stationarity | `1707.09183v2` | 2017-07-28 | Hernandez-Leal, Kaisers, Baarslag, de Cote |
| 10 | Intriguing Properties of Adversarial ML Attacks in the Problem Space [Extended] | `1911.02142v3` | 2019-11-05 | Cortellazzi, Pendlebury, Arp, Quiring, Pierazzi, Cavallaro |
| 11 | Graph-GRPO: Stabilizing Multi-Agent Topology Learning via Group Relative Policy Optimization | `2603.02701v1` | 2026-03-03 | Cang, Zhang, Zhao, Ji, Liu, He, Ning 等 |
| 12 | M²GRPO: Mamba-based Multi-Agent Group Relative Policy Optimization | `2604.19404v1` | 2026-04-21 | （按 `all:"M2GRPO"` 命中） |
| 13 | OPERA: A RL-Enhanced Orchestrated Planner-Executor Architecture | `2508.16438v4` | 2025-08-22 | Liu, Liu, Yuan, Cao 等 |
| 14 | Learning with Opponent-Learning Awareness（LOLA） | `1709.04326v4` | 2017-09-13 | Foerster, Chen, Al-Shedivat, Whiteson, Abbeel, Mordatch |
| — | DeepSeekMath（GRPO 原始定义） | `2402.03300v3` | 2024-02-05 | **已入库，不重复** |

**库内重复排查结果**：
- **DeepSeekMath 完整已入库**：`wiki/papers/grpo/2024-Shao-DeepSeekMath与GRPO开山.md`（结构化笔记，含 §4.1 p.11–13 页码锚点）+ `2402.03300-全文.md` + `raw/papers/grpo/2402.03300.pdf`。本次下载件经 sha256 比对（`6cc20b3c…7e7b`）与既有原件**字节一致**，已删除本次重复下载，**不新建笔记**。
- RELEVAGAN 在 arXiv 用 `ti:"RELEVAGAN"` **零命中**，是缩写所致；改按作者 `au:Randhawa AND abs:botnet` 才命中全称 `2210.02840v1`。登记该检索经验。
- M²GRPO 用 `ti:"M2GRPO"` 零命中；改 `all:"M2GRPO"` 命中 `2604.19404v1`（题名含 LaTeX `M$^{2}$GRPO`，故题名检索失败）。登记。

## 12. 下载与转换

- 15 个 PDF 下载至 `raw/papers/attack-detection/`，全部 `http=200`；`pdfinfo` 逐一核验题名与页数一致（MAB-Malware 15 页、MADDPG 16 页、PSRO 27 页、Non-Stationarity 综述 64 页、Problem Space 36 页、Graph-GRPO 10 页、M²GRPO 9 页、OPERA 17 页、LOLA 14 页等）。
- MinerU 转换脚本 `/tmp/dga-adv-20260910/run_extract.sh`（`mineru-open-api extract -l en -f md,json`，**幂等**：产物存在即 SKIP、可重入）。产物 `/tmp/dga-adv-20260910/marl/<name>/`，日志 `extract-run.log`。

## 13. 待办

- [ ] 转换全部完成
- [ ] 撰写结构化笔记（重点：**与 P4 的距离四级表**层级、非平稳性处理方式、与 DGA 单步扰动博弈的可迁移机制）
- [ ] Zotero 入库
- [ ] INDEX 更新
- [ ] git 提交

## 14. 第二批执行记录（2026-09-10）

**Zotero 入库 14 篇（全部成功，均含 PDF 附件）**：
MAB-Malware `WV4SU9BU`／RELEVAGAN `8NWW4DW2`／Jurečková `SYD8BRPX`／MADDPG `FRK28IKF`／MalGAN `2BELS66E`／IDSGAN `ULAVEPZA`／PSRO `Q4VRGZN4`／Foerster-Stabilising `4U8FS56U`／Hernandez-Leal `EZ7Q48VD`／Problem Space `SV6RR4D2`／Graph-GRPO `2PB965QI`／M²GRPO `6VDKBCFS`／OPERA `RN7T3D7E`／LOLA `48HFHNNY`。
**集合归属仍受阻**（同 §5）：写路径指向 Web 库，该库无 `attack-detection` 集合；14 篇均在 My Library 但未入集合，需用户桌面端手动拖入。

**DeepSeekMath 去重**：`raw/papers/grpo/2402.03300.pdf` 已存在且与本次下载件 **sha256 一致**（`6cc20b3c…7e7b`），已删除重复下载，不新建笔记（既有结构化笔记 `wiki/papers/grpo/2024-Shao-DeepSeekMath与GRPO开山.md` 已含 §4.1 p.11–13 页码锚点）。

**笔记撰写分工**：MAB-Malware、Problem Space、Graph-GRPO、M²GRPO、OPERA 由本代理自写；RELEVAGAN＋Jurečková、MADDPG＋PSRO＋LOLA、MalGAN＋IDSGAN＋Foerster-Stabilising＋Hernandez-Leal 由 3 个子代理并行撰写（各自 PDF 已就位、页码锚点由 json 的 `page_idx` 实测）。

**转换**：脚本 `/tmp/dga-adv-20260910/run_extract.sh`（幂等、可重入），14 篇全部 `rc=0`，md + json 双产物。

## 15. LLM 生成 DGA 攻击的调研（2026-09-10，第二次追加任务）

**结论：检索未获。** arXiv API 上不存在"用 LLM 生成恶意域名／DGA 域名以规避检测"的正式论文。12 个检索式的完整命中表、线索纠正（WebSearch 声称的 "LADB" 实为扩散模型域迁移论文；"MaskDGA 是 BERT-style masked LM" 已被本代理全文精读证伪）以及三篇邻近命中（DomainGAN `1911.06285`、伪 C2 生成 `2606.21349`、非 IID 流量分类 `2505.20866`）已写入 **`.Codex/docs/DRIFT/DRIFT第三章恢复卡.md` 的「文献综述更新」节**（含"弱病灶下机制增量可测性"三条邻近证据）。

## 16. 完成清单（第二批）

- [x] 15 篇 PDF 下载 + `pdfinfo` 题名/页数逐一核验
- [x] 14 篇 MinerU 转换（DeepSeekMath 去重）
- [x] 14 篇结构化笔记（5 篇自写 + 9 篇子代理）
- [x] Zotero 14 篇
- [x] INDEX 新增「博弈 × 强化学习 × MARL × 对抗鲁棒」节
- [x] DRIFT 恢复卡写回（LLM 生成 DGA 盘点 + 弱信号可测性线索）
- [ ] git 提交
