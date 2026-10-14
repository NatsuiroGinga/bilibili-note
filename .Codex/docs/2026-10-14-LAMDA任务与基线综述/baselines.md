# 外部基线清单（按候选任务分组，含证据等级）

- 日期：2026-10-14
- 规则：**摘要级（E1）证据不得写成可对比基线**；不同宿主上的已发表数字不能直接搬进
  LAMDA 协议比较（必须重跑才能进对比表），故每条标注「可直接引用的数字」与「需要重跑」。
- 证据等级：`E3` 本地全文（raw+wiki 笔记）｜`E2` 在线全文已取得｜`E1` 摘要/题录｜`E0` 未核。
  本清单不使用 E0。

## 共同说明

- LAMDA 原论文基线（LightGBM/MLP/SVM/XGBoost + Naive/Joint/ER）都是 `E3`，
  其 LAMDA 数字就是协议内数字，**可直接引用**；表 7 继承全时期预处理泄漏，
  引用时注明「原协议读数」边界。
- CITADEL 是**唯一在 LAMDA 上给出适应方法已发表读数**的工作（`E2+` 本地 PDF）：
  F1 `77.7±0.1`、FNR `24.0`、FPR `2.3`（月预算 400），预算 50 → `70.9±1.2`，
  不更新只增强 `30.9`（表 6、表 4）。

---

## C1（零/低标签时间泛化 + 固定 FPR 工作点）

### 可直接引用的已发表 LAMDA 数字

| 方法 | venue | 数据集 | 指标值 | 证据 |
| --- | --- | --- | --- | --- |
| LAMDA 静态 4 基线 | ICLR 2026 | LAMDA | FAR F1 `41.86–47.59`、FNR `64.10–69.93`、FPR `1.14–1.69`（表 7） | `E3` |
| LAMDA Domain-IL | ICLR 2026 | LAMDA | Joint `88.52±0.46` vs Naive `72.71±0.83`（2025 平均 F1，附录 J） | `E3` |
| CADE（转引） | USENIX Sec 2020 | APIGraph vs LAMDA | F1 `0.8904`（APIGraph）vs `0.4407`（LAMDA，附录 H 表 14） | `E3`（转引） |
| CITADEL | arXiv `2511.11979` | LAMDA | `77.7±0.1`@预算400；`70.9±1.2`@预算50；不更新 `30.9` | `E2+` |

### 可作为机制对照、需在我们协议下重跑的基线

| 方法 | venue | 原宿主 | 原宿主数字（引用边界） | 证据 |
| --- | --- | --- | --- | --- |
| TRANSCENDENT | USENIX Sec 2022 | TESSERACT 5 年 Android | 超越 Transcend；ICE/CCE 低开销保形评价器；无单一汇总数 | `E3`（drift 树笔记） |
| MADCAT | arXiv `2505.18734` | APIGraph 特征 | 无结果表（数字在图内），须按官方代码重跑 | `E3`（限制已登记） |
| DREAM | CCS 2025 | Drebin 3,317 / Malradar 2,589（8 家族） | AUC 相对 Transcendent/CADE/Probability +`11.95/15.64/12.4%`（Drebin）；预算梯度 +`89.1%→4.5%` | `E2` |
| DRMD | AAAI 2026 | TESSERACT 系 Android 数据 | AUT +`8.66/10.90`、ΔBase `9.77`（172 设置×5 种子） | `E2` |
| A-GEM | ICLR 2019 | 各 CL 基准 | 更新型机制对照 | `E3` |
| ER（reservoir） | 经典 | 各 CL 域 | 本课题已有阶段 A 制品可复用 | `E3` |

### 仅登记存在性、不得作基线（E1）

- DeepTrust（ESWA 2025，`2510.12310`）：对抗鲁棒线。
- PLCDroid（Computer Journal 2026）：伪标签校正，付费墙未核。
- FL-CL-IDS（IEEE Access 2026）：联邦 CL。
- MalNet（`2011.07682`）、Malware-OSR 两篇（`2505.12750`/`2205.06918`）、Miller 2015（`1510.07338`）。

---

## C2（标注管线时间退化）

### 可直接引用的数字

| 对象 | 数字 | 证据 |
| --- | --- | --- |
| LAMDA 附录 F | 2017 年 `5.19%` 原恶意样本当前判良性 | `E3` |
| 本地家族标签审计 | 单例质量占比 2013 `3.7%`→2024 `84.7%`；跨年复现家族 236/四年全复现 11 | `E3`（本地制品） |
| LAMDA 正例率 | 2013 `51.35%` → 2025 `0.05%` | `E3`（本地实测） |

### 机制对照（需重跑或改造）

- **Beyond the TESSERACT**（SaTML 2026，`2506.23814`，`E2`）：VT 阈值/时间戳/市场等构建要素
  对评价的影响——协议修正型对照；v2 §XI 评论 LAMDA。
- **LAMDA 附录 G/H 阈值敏感性**（`E3`）：表 11/12 口径混用缺陷已登记，重跑须用一致口径。
- 学习噪声标签方法族（Co-teaching 等）：**本地未入库（E0），不得引用数字或当基线**；
  若中选 C2 需先全文入库。
- PLCDroid：`E1`，仅作相关工作报告。

---

## C3（Domain-IL 标签版本感知安全回归）

### 可直接引用的数字

| 对象 | 数字 | 证据 |
| --- | --- | --- |
| Joint vs Naive | `88.52±0.46` vs `72.71±0.83`（2025 平均 F1，附录 J 表 15） | `E3` |
| ER 资格读数 | FPR/翻转下降、AP/FNR 略差（阶段 A 本地制品） | `E3` |

### 机制对照（需重跑）

| 方法 | venue | 原宿主 | 证据 |
| --- | --- | --- | --- |
| Regression-aware | IEEE TIFS 2026（`2507.18313`） | Android（非 LAMDA） | `E3` |
| A-GEM | ICLR 2019 | 各 CL 基准 | `E3` |
| CBRS | ICML 2020 | 各 CL 基准 | `E3` |
| GSS | NeurIPS 2019 | 各 CL 域 | `E3` |
| MIR | NeurIPS 2019 | 各 CL 基准 | `E3` |
| PBR | ACM MM 2024 | 长尾 CL | `E3` |
| MADAR | arXiv `2502.05760` | 恶意软件 CL | `E3` |
| ECBRS/PAPA | NeurIPS 2023 | NIDS | `E3` |

---

## 汇总：每个候选的「可直接引用」边界

- **C1**：LAMDA 表 7（4 基线）、附录 H（CADE）、附录 J（Domain-IL）、CITADEL 表 4/6——
  全部 `E3`/`E2+` 可直接引用（表 7 注明预处理泄漏边界）。TRANSCENDENT/MADCAT/DREAM/DRMD
  需重跑；DeepTrust/PLCDroid/FL-CL-IDS 只作相关工作。
- **C2**：LAMDA 附录 F/G + 本地审计 + Beyond the TESSERACT 协议对照（`E2`）；
  噪声标签方法族须先入库。
- **C3**：附录 J + 本地阶段 A 制品 + 六家族记忆方法 + Regression-aware，全部 `E3` 可重跑。

## 尚未入库、若中选必须先全文入库的候选基线

- **MADCAT 官方代码仓库未核准**（本地笔记已登记）；TRANSCENDENT 原件与笔记在 drift 工作树，
  本工作树内无独立笔记（`[[2019-Pendlebury-TESSERACT时空实验偏置与AUT]]` 等为悬空链接）——
  中选 C1 时先把 TRANSCENDENT 原件迁入本工作树并建 wiki 笔记。
- DREAM/DRMD 原件未入库（本轮在线全文已读，HTML 缓存在本任务目录）——中选 C1 时按
  `raw/AGENTS.md` 入库。
- PLCDroid、FL-CL-IDS、DeepTrust：付费墙/未核，仅登记。
