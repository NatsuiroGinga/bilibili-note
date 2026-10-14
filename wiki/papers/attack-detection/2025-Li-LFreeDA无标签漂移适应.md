---
schema: paper-note-search/v1
title: "LFreeDA: Label-Free Drift Adaptation for Windows Malware Detection"
title_zh: "LFreeDA：Windows 恶意软件检测的无标签漂移适应"
authors: [Adrian Shuai Li, Elisa Bertino]
year: 2025
date: 2026-10-14
journal: "arXiv 2511.14963（预印本）"
doi: null
arxiv_id: "2511.14963"
evidence_level: "在线全文已下载"
source_pdf: "[[raw/papers/attack-detection/2025-Li-LFreeDA-Label-Free-Drift-Adaptation-Windows-Malware.pdf]]"
tags:
  - Windows恶意软件
  - 概念漂移
  - 无标签适应
  - 无监督域适应
  - 伪标签
  - 控制流图
  - 类型/论文
tasks: [Windows PE 二分类, Windows 恶意软件家族分类, 无标签漂移适应]
datasets: [MB-24+, BIG-15, MalwareDrift]
methods: [MaxDIRep 无监督域适应（图像）, 置信度+类内离群检测伪标签筛选, AdvDA+GIN / Warm-start 适应]
metrics: [Accuracy, Macro-F1, 伪标签准确率, 覆盖率, ACS]
key_finding:
  - "LFreeDA 用恶意软件图像上的无监督域适应生成伪标签、再以 CFG 上的域适应做最终适应，全程不用目标域标签、也不做漂移检测。"
  - "它把『无标签适应』从空白推成已发表结果：MB-24+ 上平均准确率 82%、F1 79%，仅比全监督上界低约 3–4 个百分点；但效果强烈依赖每个目标类至少有约 244 个样本，MalwareDrift 的稀疏类上失效。"
method: "三步：图像上训 MaxDIRep（DIRep/DDRep 分解，KL 约束 + 对抗域不变）→ 置信度 0.95 + 类内离群检测（LOF 最优）筛伪标签 → 用源标签 + 选中伪标签训 AdvDA+GIN（CFG）"
baseline: "AdvDA+GIN、AdvDA+CNN、DAN+GIN、DAN+CNN；Warm-start ResNet-50 / GIN；no-adaptation 下界与全监督上界"
aliases:
  - LFreeDA
  - Li2025-LFreeDA
related:
  - "[[2025-Alam-ADAPT伪标签抗概念漂移]]"
  - "[[2025-Haque-CITADEL半监督主动漂移适应]]"
  - "[[2025-Roh-MADCAT自监督测试时适应]]"
---

# LFreeDA：Windows 恶意软件检测的无标签漂移适应

> 页码锚点：标题与摘要位于 PDF 物理第 1 页；本文其余引用按 MinerU 保留的章节号（§1–§9 与附录 A–E）给出。证据等级：在线全文已下载（MinerU 转换自 `raw/papers/attack-detection/2025-Li-LFreeDA-Label-Free-Drift-Adaptation-Windows-Malware.pdf`）。取得版本为 arXiv 2511.14963 预印本。

## 抽取字段表

| 字段 | 内容 |
| --- | --- |
| 实验数据集 | MB-24+（MalwareBazaar 2024-03 至 2024-12 月度 Windows 恶意软件流，Table 1）+ BIG-15（Microsoft 挑战赛，重聚类标签）+ MalwareDrift（7 个家族的漂移前后）；**未使用 LAMDA** |
| 特征表示 | 恶意软件**图像**（原始字节流重排为灰度图，统一缩放 56×56）+ **控制流图 CFG**（基本块节点，PalmTree 指令嵌入均值） |
| 平台 | Windows |
| 监督设定 | **完全无标签适应**：源域已标注、目标域（当月）无标签；真值仅用于评估伪标签质量（§2.1.2、§2.4.4）。对照组 AdvDA 使用目标真标签 50（BIG-15）/ 300（MB-24+）/ 每类 10（MalwareDrift） |
| 是否有固定 FPR 工作点 | **无**。报告 Accuracy、macro-F1、伪标签准确率/覆盖率/ACS，未设固定 FPR 运行点 |
| 评价指标 | Accuracy、macro-F1、伪标签准确率、覆盖率、Accuracy-Coverage Score（ACS，式 8）；混淆/洗牌对照（§3.3） |
| 报告的主结果数字 | §3.2.3：MB-24+ 上 AdvDA+GIN 平均准确率 `82%`、F1 `79%`，比下界提升 7.6–12.6%（准确率）/ 9.1–11.1%（F1），比全监督上界低 2.8–4%（准确率）/ 2–3.4%（F1）；§4.2.3：BIG-15 最高平均准确率 `98%`；§5.2.3：MalwareDrift AdvDA+GIN 准确率 `52.9%`（低于 AdvDA 用每类 10 标签） |
| 与 LAMDA 本课题的关系 | **直接近邻**（占据「零目标标签漂移适应」，即 C1 零标签端）+ **部件来源**（UDA 伪标签 + 类内离群选样） |

## 一、论文原结论（带章节号）

- **问题与动机**（§1）：既有方法（漂移检测 + 选择性标注、自训练）都仍需人工标注或显式漂移检测；作者主张**已观测到的无标签样本本身携带信息**，可在无漂移检测、无标注下适应。
- **方法三步**（§2.2–§2.5）：① 图像表示上训 MaxDIRep——把表示分解为域不变 `DIRep` 与域相关 `DDRep`，以重建损失、KL 约束（DDRep→N(0,I)）与对抗域损失联合优化（式 1–7）；② 伪标签筛选——置信度 `P ≥ 0.95` **且** 在 DIRep 空间为其预测类的内点（5 种离群算法中 **LOF 的 ACS 最高**，§3.2.2，保留约 61% 样本、准确率 88.2%，较初始 79.8% 提升 8.4 个百分点）；③ 用源标签 + 选中伪标签训最终模型，比较 AdvDA 与 warm-start，并以 CFG 承载最终适应。
- **关键设计权衡**（§2.1.1、§2.4.3）：图像用于可扩展的伪标注，CFG 用于高保真的最终适应——因为图自编码器在数千节点以上的 CFG 上有二次内存开销与重建退化。
- **自然漂移结果**（§3.2.3、§3.1.2）：采用滚动更新（7→8、8→9、…、11→12 月），AdvDA+GIN 最优，平均准确率 82%、F1 79%，比两个下界高 7.6–12.6% / 9.1–11.1%，比两个全监督上界低 2.8–4% / 2–3.4%；与 AdvDA 用 300 真标签相当（作者称对比保守，因为本文覆盖 6 个月、对照组只覆盖 3 个月）。
- **混淆稳健性**（§3.3）：测试集为 Hyperion 加壳样本、训练不含混淆样本时，Step III 准确率下降约 1–3.5%、F1 下降 1–3.0%（AdvDA+GIN 降幅最大）。
- **受控漂移**（§4–§5）：BIG-15 最高平均准确率 98%（与 AdvDA 用 50 真标签相当）；MalwareDrift 上方法整体下降，AdvDA+GIN 准确率 52.9%，**低于** AdvDA 用每类 10 标签的结果（§5.3）。
- **明确作用边界**（§5.3、§6）：伪标签质量与 Step I 预测准确率强相关；经验上每类至少需约 244 个目标样本（源+目标合计约 463）才有明显增益；**开放集未处理**（§7），因未知类会破坏聚类结构。

## 二、本课题推论（我方判断，**均为推论**）

- 【推论】LFreeDA 是 C1 零标签端当前最强、最直接的已发表近邻：它证明「无目标标签、无漂移检测」在 Windows 上可行，从而**削弱**了「零标签端是明确空位」的论断（与 task_plan 记录的实测一致）。
- 【推论】其作用边界（每类 ≥244 样本）提示：LAMDA 若按年份/家族切窗，稀少年份或稀有家族的伪标签会失效；这一风险与 MADCAT（无标签 TTA）不同——LFreeDA 依赖类内样本量而非时间窗长度。
- 【推论】LFreeDA 无固定 FPR 工作点，其准确率/F1 不能作为 LAMDA 的 FNR@固定FPR 对照读数。

## 三、可迁移机制（借用边界）

- **MaxDIRep 的 DIRep/DDRep 分解 + KL 约束**：借用边界是它是「无标签生成伪标签」的表示学习部件，可迁移到 LAMDA 的零标签端；但它原本面向图像分类，作者自己指出直接套到 CFG 不可行（图自编码器内存问题）。
- **置信度 + 类内离群的双条件伪标签筛选**：可直接借为 C1 伪标签门的筛选部件；边界是离群算法需在目标表示空间运行，作者报告 LOF 在三个数据集上 ACS 最高但**未在 LAMDA 验证**。
- **方案分工（图像做伪标注、CFG 做适应）**：借用边界是 LAMDA 只有静态特征（无 CFG），该分工不能照搬。

## 四、不可直接声称内容（论文没证明的）

- 没有在 LAMDA 上做实验，**不得**说「LFreeDA 在 LAMDA 上达到某指标」。
- 未处理开放集（§7 自述），**不得**声称其在开放集/新家族场景下有效。
- 无固定 FPR 工作点，**不得**引用其准确率/F1 当作 FPR 约束下的读数。
- 伪标签筛选用真值**仅评估**、不参与生成（§2.4.4），但也意味着其筛选参数（阈值 0.95、离群比例 20%）是在已知标签分布下调的，**不得**声称该阈值可直接部署。

## 五、待验证假设

- 假设 A：在 LAMDA 的年度窗口上，逐类样本量是否满足 LFreeDA 的经验门槛（≥244/类）？**最小验证**：统计 LAMDA 各年良性/恶意样本量与家族分布。
- 假设 B：把 LFreeDA 的「置信度 + 类内离群」筛选用到 LAMDA 的二值静态特征上，能否在不抬 FPR 的前提下降 FNR？**最小验证**：LAMDA 源期模型输出伪标签，比较仅置信度筛选 vs 叠加离群筛选的 ΔFNR/ΔFPR。

## 文献信息

- arXiv：https://arxiv.org/abs/2511.14963
- 直接前身：Li et al. 2025 NDSS（AdvDA，Windows 概念漂移最小样本适应）
