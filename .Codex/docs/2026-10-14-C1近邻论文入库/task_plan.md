# 任务计划：C1 近邻论文入库（2026-10-14）

## 一、触发原因（**这是本任务存在的全部理由**）

用户要求重试引用图检索。改用程序化引用图 API（OpenAlex / arXiv API，绕开需要 Chrome 调试端口的
scholar CLI）后，**推翻了 2026-10-14 任务综述代理的一条关键结论**：

> 综述原文（`task-candidates.md` 行 34–35）：「标签预算 0 → 400 的整条曲线之间**没有已发表读数**；
> 零标签端（`30.9` 与监督静态 `47.59` 之间、以及 FNR@固定FPR 的工作点）是**明确空位**。」

**实测反驳**：`title_and_abstract.search:android malware concept drift adaptation` 全空间仅 **16 条**
（2026-10-14 实测），其中 2025–2026 的新近邻把 C1 的预算轴占住了：

| arXiv | 年月 | 标题 | 为什么打到 C1 |
| --- | --- | --- | --- |
| `2605.24903` | 2026-05 | SEED: Semi-supervised Continual MalwarE Detection for Tackling ConcEpt Drift on a BuDget | **预算下的半监督持续检测**——与 C1 的标签预算轴正面重合 |
| `2511.14963` | 2025-11 | LFreeDA: **Label-Free** Drift Adaptation for Windows Malware Detection | 名字就是「无标签漂移适应」 |
| `2609.26352` | 2026-09 | HYDRA: Proactive Android Malware Drift Adaptation via Hierarchical Graph Contrastive Learning | 主动式（非事后）漂移适应 |
| `2508.18839` | 2025-08 | DRMD: Deep Reinforcement Learning for Malware Detection under Concept Drift（AAAI 2026） | 策略式适应 |
| `2507.08597` | 2025-07 | ADAPT: A Pseudo-labeling Approach to Combat Concept Drift in Malware Detection（RAID 2025） | 伪标签——C1 伪标签门的直接对照 |
| `2405.04095` | 2024-05 | Combating Concept Drift with Explanatory Detection and Adaptation for Android Malware | 已含解释驱动的适应 |
| `2401.12790` | 2024-01 | MORPH: Towards Automated Concept Drift Adaptation for Malware Detection | 自动化适应 |
| `2605.24294` | 2026-05 | Concept Drift Adaptation Using Self-Supervised and Reinforcement Learning in Android Malware Detection | 自监督＋RL |

本地已有并**无需重复入库**：MADCAT（`2025-Roh-…`）、CITADEL（`2025-Haque-…`）、FreeMOCA（`2026-Asadi-…`）。

## 二、要交付什么

1. `raw/papers/attack-detection/` 下的 8 份**真实全文 PDF**（已下载并逐份校验文件类型）
2. `wiki/papers/attack-detection/` 下的 8 份**基于全文的结构化笔记**（frontmatter 八字段 +
   `source_pdf` 指向 raw 原件 + 关键页码/公式）
3. 更新 `wiki/papers/attack-detection/INDEX.md`
4. **结论写回**：`thesis/methods/第三章-LAMDA候选任务对照（供裁决）.md` 与
   `.Codex/docs/2026-10-14-LAMDA任务与基线综述/task-candidates.md` 中 C1 的「空位」论断
   **必须按实测修正**——这是用户规则「实质冲突必须如实记录」的强制项，不得只在聊天里提。

## 三、工具与口径（强制）

- **读 PDF 只用 `pdf-converter`（MinerU）**，禁止 `pdftotext`（丢公式符号，本仓库出过事故）
- 网络：`curl -sL -x http://127.0.0.1:7890`；**arXiv API 仅 `https://` + 显式代理可用**
  （`http://export.arxiv.org` 直连**静默返回空**，2026-10-14 实测；已据此修正检查点）
- 证据等级：本次为**在线全文已下载**；结构化笔记完成前不得作为正文论断依据
- 每篇笔记必须区分：**论文原结论 / 本课题推论 / 可迁移机制 / 不可直接声称内容 / 待验证假设**

## 四、阻塞与边界

- DRMD(AAAI) 与 ADAPT(RAID) 均有 arXiv 预印本，已取；若最终版与预印本有差异，笔记须标注取得版本
- 不修改 `raw/` 下任何既有原件
- 本任务**不下任何候选存废裁决**——只把事实补齐，重排优先级交主代理与用户
