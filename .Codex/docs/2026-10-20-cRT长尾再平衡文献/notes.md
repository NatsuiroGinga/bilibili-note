# cRT / 延迟重加权 / 先验校正文献入库检查点

> 每完成一篇或一组查询立即追加。字段：查询式 / 来源 URL / 原件路径 / 元数据核验 / 证据等级 / 页码锚点 / 与 M2' 关系 / wiki / Zotero。

## 0. 题录核验与 ID 纠错（2026-10-20）

任务下达时给出三篇第一优先文献，其中**两个 arXiv ID 与题名不符**。以 arXiv API 与 Crossref 返回为准：

| 短名 | 任务给定 | 实际 | 核验来源 | 结论 |
|---|---|---|---|---|
| BalancedSoftmax | arXiv:2007.10742 | **arXiv:2007.10740** | `https://export.arxiv.org/api/query?id_list=2007.10740`；`arxiv:comment` = "NeurIPS 2020 camera-ready" | 给定 ID 是 Willmore 能量数学论文（题名 *Approximation of the Willmore energy by a discrete geometry model*），**已修正** |
| LogitAdjust | arXiv:2007.07314 | arXiv:2007.07314 | 同上；`arxiv:comment` = "Published as a conference paper in ICLR 2021" | 正确 |
| LADE | arXiv:2103.17084 | **arXiv:2012.00321** | 同上；`arxiv:comment` = "CVPR 2021"；Crossref DOI `10.1109/CVPR46437.2021.00656` | 给定 ID 是 DA-DETR 目标检测论文，**已修正** |

题录字段（arXiv API 实际返回）：

- BSM：Jiawei Ren, Cunjun Yu, Shunan Sheng, Xiao Ma, Haiyu Zhao, Shuai Yi, Hongsheng Li；2020-07-21 提交；NeurIPS 2020。
- LA：Aditya Krishna Menon, Sadeep Jayasumana, Ankit Singh Rawat, Himanshu Jain, Andreas Veit, Sanjiv Kumar；2020-07-14 提交；ICLR 2021。
- LADE：Youngkyu Hong, Seungju Han, Kwanghee Choi, Seokjun Seo, Beomsu Kim, Buru Chang；2020-12-01 提交；CVPR 2021；DOI `10.1109/CVPR46437.2021.00656`。

## 1. BSM（Balanced Meta-Softmax）

- **查询式/来源**：arXiv API `id_list=2007.10740`；题名检索 `ti:"Balanced Meta-Softmax for Long-Tailed Visual Recognition"`。
- **原件**：`raw/papers/methodology/2020-Ren-Balanced-Meta-Softmax.pdf`（24 页，sha256 `e3af957b2387cd2bfdfa3fe50eb90b6865d1ab9b80fad9f0cdfb5f22625722c8`）。
- **全文转换**：MinerU `extract` → `/tmp/2026-10-20-cRT长尾再平衡文献/md/bsm/bsm.md`；页码索引 `/tmp/2026-10-20-cRT长尾再平衡文献/mdjson/bsm.json`。
- **证据等级**：本地全文（L1）。
- **页码锚点**：Theorem 1/Eq. 3–4 p3；泛化界 Eq. 8/10 p4；Meta Sampler §3.2 p5–6；Table 2–3 p7；Table 4 p8；Table 5 p8–9；附录 C.3 训练细节 p20；Table 8 p23。
- **与 M2' 关系**：Balanced Softmax = 二分类下的先验 logit 偏移（等价于阈值平移）；不需要改采样。其 label shift 前提是 \(p(x\mid y)\) 不变，故只作基线/诊断。Table 8 再次支持“自然采样学表示、分类器再平衡”。
- **wiki**：`wiki/papers/methodology/2020-Ren-平衡元Softmax.md`。
- **Zotero**：已入库，key `LAV9HUZX`（arXiv abs 页面导入后改为 preprint；PDF 已附）。

## 2. LA（Logit Adjustment）

- **查询式/来源**：arXiv API `id_list=2007.07314`。
- **原件**：`raw/papers/methodology/2021-Menon-Logit-Adjustment.pdf`（27 页，sha256 `1a4289fcc090ca05f711ff6002f2a4ff77ea2ae55d4bedc09448287dfd4f0209`）。
- **全文转换**：MinerU `extract` → `/tmp/2026-10-20-cRT长尾再平衡文献/md/la/la.md`；JSON `.../mdjson/la.json`。
- **证据等级**：本地全文（L1）。
- **页码锚点**：Eq. 7–8 p5；Eq. 9 p5；Eq. 10 p6；Eq. 11 p7；Theorem 1 p7；Table 3 p9；Table 4 p10；附录 D 训练细节 p23。
- **与 M2' 关系**：最便宜的 post-hoc 先验校正；对平衡误差 Fisher 一致；前提是固定类条件、只变先验。若 \(p(x\mid y)\) 漂移，则误设定。
- **wiki**：`wiki/papers/methodology/2021-Menon-对数几率调整.md`。
- **Zotero**：已入库，key `IFIFVMX8`（arXiv abs 页面导入后改为 preprint；PDF 已附）。

## 3. LADE（PC Softmax + LADER）

- **查询式/来源**：题名检索 `ti:"Disentangling Label Distribution for Long-tailed Visual Recognition"`；Crossref 题名检索。
- **原件**：`raw/papers/methodology/2021-Hong-LADE-Label-Distribution-Disentangling.pdf`（15 页，sha256 `e88bff49bdbf54407597a044487bd62af75fb39b55b917b88b2a69d7c1c0cf05`）。
- **全文转换**：MinerU `extract` → `/tmp/2026-10-20-cRT长尾再平衡文献/md/lade/lade.md`；JSON `.../mdjson/lade.json`。
- **证据等级**：本地全文（L1）。
- **页码锚点**：label shift 假设 §2.2/§3.1 p2–3；PC Eq. 4、Theorem 1 p3；DV Eq. 9、LADER Eq. 15–16、Eq. 17、LADE Eq. 18–20 p4；Table 2–5 p6；Table 6 p7；附录训练细节 p12。
- **与 M2' 关系**：PC Softmax 提供“任意目标先验”的零训练后处理接口；LADE 的额外增益相对 PC 很小（+0.1~+0.7），不作为首选。前提同样是 \(p_s(x\mid y)=p_t(x\mid y)\)。
- **wiki**：`wiki/papers/methodology/2021-Hong-LADE标签分布解耦.md`。
- **Zotero**：已入库，key `V3UP8CV5`（DOI 导入，PDF 已附）。

## 4. cRT 精确协议（Kang et al. 2020，本地全文复核）

- **来源**：`raw/papers/methodology/2020-Kang-Decoupling-Representation-Classifier.pdf`；MinerU 转换 `/tmp/2026-10-20-cRT长尾再平衡文献/md/kang/2020-Kang-Decoupling-Representation-Classifier.md`；JSON `.../mdjson/2020-Kang-Decoupling-Representation-Classifier.json`。
- **第一阶段（表示）**：实例平衡（自然）采样；SGD 动量 0.9、batch 512、cosine 学习率 0.2→0；通常 90 epoch（§5.1，物理第 5 页）。
- **第二阶段（cRT）**：**冻结骨干网络**；**随机重初始化分类器 \(W,b\)**；**类平衡采样**；**交叉熵**；**10 epoch**；SGD 动量 0.9、batch 512、cosine 学习率重启 0.2→0（§4 第 4 页 + §5.1 第 5 页）。
- **增益**：ImageNet-LT ResNeXt-50 Joint `44.4`→cRT `49.5`（+5.1）；ResNet-10 `34.8`→`41.8`（+7.0）；ResNeXt-152 `47.8`→`52.4`（+4.6）。Places-LT ResNet-152 `30.2`→`36.7`（+6.5）。iNat ResNet-50 90/200 epoch：`61.7/65.8`→`65.2/67.6`（+3.5/+1.8）。见 Table 2–3（物理第 8 页）。
- **与 NCM 的区别**：NCM 不训练、不采样；直接计算每类训练样本的均值特征，用余弦/欧氏距离（L2 归一化）做最近邻（§4，第 4 页）。NCM 在 few-shot 分片接近 cRT，但整体低于 cRT：ImageNet-LT `47.3` vs `49.5`；Places-LT `36.4` vs `36.7`；iNat 90 epoch `58.2` vs `65.2`（Table 2–3）。
- **对 PAAT 的关键问题**：cRT 假设有一个“冻结的、跨类共享的表示”。PAAT 编码器按年度更新；若在年度末 cRT，需要决定冻结哪一年的编码器，以及是否让重训后的分类头影响下一年。LT-CIL（Liu et al. 2022）的证据是：在增量设定下应冻结旧头，否则表示漂移。

## 5. DRW 精确调度（LDAM，本地全文复核）

- **来源**：`raw/papers/methodology/2019-Cao-LDAM-Label-Distribution-Aware-Margin.pdf`；MinerU 转换 `/tmp/2026-10-20-cRT长尾再平衡文献/md/ldam/2019-Cao-LDAM-Label-Distribution-Aware-Margin.md`；JSON `.../mdjson/2019-Cao-LDAM-Label-Distribution-Aware-Margin.json`。
- **Algorithm 1（物理第 6 页）**：
  - \(t=1,\ldots,T_0\)：自然 mini-batch，LDAM 损失，普通 SGD；可选在学习率退火时 \(\alpha\leftarrow\alpha/\tau\)。
  - \(t=T_0,\ldots,T\)：每个样本按 \(n_y^{-1}\) 重加权，梯度再除以 \(\sum_{B} n_y^{-1}\) 归一化；学习率较小。
- **\(T_0\) 的实测设定**：
  - CIFAR-10/100：200 epoch，学习率在第 160/180 epoch 各衰减一次；Figure 3（第 10 页）明确“在 epoch 160 退火”，DRW 从此点开始 → \(T_0=160\)，比例 0.80。
  - iNat 2018：90 epoch，在第 30/60 epoch 退火；“从 epoch 60 开始再平衡” → \(T_0=60\)，比例 0.667（附录 B，第 15 页）。
  - Tiny ImageNet：120 epoch，第 90 epoch 衰减 → \(T_0=90\)，比例 0.75（附录 B，第 15 页）。
  - **原文 §4 的措辞“until the last learning rate decay”与 CIFAR 的 160/180 两次衰减存在歧义**；以 Figure 3 和实现细节为准。结论：\(T_0\) 绑定学习率退火点，不是固定比例。
- **任务化到 PAAT 的 10 epoch 年度协议（本文建议，未经实验验证）**：
  - 先测 \(T_0=8\)（0.8，对应 CIFAR 比例），自然 ERM 8 epoch + 再平衡 2 epoch；
  - 同时测 \(T_0=7\)（0.7）和 \(T_0=6\)（0.6）作为敏感性；
  - 由于 PAAT 每年只有 10 epoch，表示学习本身可能不足，不能假设“8 epoch 的 ERM 已经学到好表示”；必须与“全程自然”“全程平衡”同时跑。
  - 若年度训练使用 cosine 调度，则“退火点”不是离散事件；建议以 epoch 比例定义，并记录该选择是任务化假设。
- **DRW 与 cRT 的区别**：DRW 在**同一个训练过程**内延迟改变损失权重/采样；cRT 是**两阶段**，第二阶段冻结表示并重训分类器。PAAT 的 M2' 可以选择其中任一条，或两者组合；但不要与全程平衡采样叠加。

## 6. 第二优先检索记录

检索日期 2026-10-20。入口：arXiv API（题名/摘要）；Crossref 补 DOI；Zotero 查重。Google Scholar 未使用（arXiv/Crossref 已足够，避免限流）。

### Q1 长尾类增量学习

查询式：`all:"long-tailed" AND all:"class-incremental learning"`；`all:"long-tailed" AND all:"continual learning"`。

主要命中：

| arXiv | 题名 | 判断 |
|---|---|---|
| 2210.00266 | Long-Tailed Class Incremental Learning | **入库**（ECCV 2022，两阶段 LWS，直接相关） |
| 2404.04476 | DELTA: Decoupling Long-Tailed Online Continual Learning | **入库**（CVPRW 2024，在线长尾解耦，直接相关） |
| 2408.14976 | Prior-free Balanced Replay | 候选，未入库（prior-free 回放，不是分类器再平衡主线） |
| 2009.03632 | Imbalanced Continual Learning with Partitioning Reservoir Sampling | 候选，未入库（多标签、回放采样） |
| 2306.13275 | On The Relationship Between Continual Learning and Long-Tailed Recognition | 候选，未入库（理论关系，非直接方法） |

### Q2 漂移 + 标签移位

查询式：`all:"label shift" AND all:"concept drift"`；`all:"label shift" AND all:"drift"`；`all:"prior shift" AND all:"streaming"`；`all:"class prior" AND all:"concept drift"`；`all:"deferred rebalancing" AND all:"drift"`。

主要命中：

| arXiv | 题名 | 判断 |
|---|---|---|
| 2305.19570 | Online Label Shift: Optimal Dynamic Regret meets Practical Algorithms | **入库**（NeurIPS 2023，显式 label shift + 动态遗憾） |
| 2206.05181 | Lightweight Conditional Model Extrapolation for Streaming Data under Class-Prior Shift | **入库**（ICPR 2022，流式类先验 + bias 校正） |
| 2604.01651 | Label Shift Estimation With Incremental Prior Update | 候选，未入库（2026 预印本，后验先验更新；与本题关系较远） |
| 2604.01651 等 2026 预印本 | — | 未入库；只作候选，证据等级不足 |

### Q3 cRT/DRW 用于时间漂移

查询式：`all:"deferred rebalancing" AND all:"drift"`（0 命中）；`all:"classifier rebalancing" AND all:"continual learning"`（0 命中）。

**结论：未检得**把 cRT/DRW 直接用于“时间漂移而非静态长尾”的论文。最接近的是：
- LT-CIL（2210.00266）：类增量 + 长尾，不是同标签空间漂移；
- DELTA（2404.04476）：在线长尾持续学习，不是同标签空间概念漂移；
- OLS（2305.19570）/ LIMES（2206.05181）：标签比例漂移，但显式假设 \(p(x\mid y)\) 不变。

### Q4 是否有「漂移 + 长尾」联合证据

**未检得**同时满足以下三条的论文：
1. 训练分布长尾；
2. 部署期 \(p(x\mid y)\) 发生漂移（不只是 \(p(y)\)）；
3. 用分类器再平衡/延迟重加权处理。

现有文献分成两条平行线，假设互不兼容：
- 长尾 + 序列/在线任务（LT-CIL、DELTA）：处理类频不平衡 + 新类/流式，但不建模 \(p(x\mid y)\) 漂移；
- 标签比例漂移（OLS、LIMES）：显式假设 \(p(x\mid y)\) 不变，不处理长尾训练分布。

因此，不能把静态长尾的 cRT/DRW 或纯 label shift 的 OLS/LIMES 结论冒充“漂移 + 长尾”联合证据。

## 7. 第二优先四篇的检查点

### 7.1 LT-CIL（2210.00266）

- **原件**：`raw/papers/methodology/2022-Liu-Long-Tailed-Class-Incremental-Learning.pdf`（19 页）。
- **元数据**：ECCV 2022；作者 Xialei Liu, Yu-Song Hu, Xu-Sheng Cao, Andrew D. Bagdanov, Ke Li, Ming-Ming Cheng。
- **全文**：`/tmp/2026-10-20-cRT长尾再平衡文献/md/ltcil/ltcil.md`；JSON `.../mdjson/ltcil.json`。
- **页码锚点**：两阶段 §3.3 p6–7；冻结旧头理由 p7；Table 1 p9；Table 2 p10；Fig. 8 p12。
- **与 M2' 关系**：跨年度再平衡应冻结旧头/只学缩放；不要把修改后的分类头反传进编码器。
- **wiki**：`wiki/papers/methodology/2022-Liu-长尾类增量学习.md`。
- **Zotero**：已入库，key `YXSSPY5R`（arXiv 导入，PDF 已附）。

### 7.2 DELTA（2404.04476）

- **原件**：`raw/papers/methodology/2024-Raghavan-DELTA-Long-Tailed-Online-Continual.pdf`（11 页）。
- **元数据**：CVPRW 2024；DOI `10.1109/CVPRW63382.2024.00409`；作者 Siddeshwar Raghavan, Jiangpeng He, Fengqing Zhu。
- **全文**：`/tmp/2026-10-20-cRT长尾再平衡文献/md/delta/delta.md`；JSON `.../mdjson/delta.json`。
- **页码锚点**：LTOCL §3 p4；Stage 1/2 §4 p4；Eq. 1 p4；Equalization Loss p4–5；Table 1–3 p7。
- **与 M2' 关系**：流式长尾下“冻结表示 + 分类器阶段再平衡”的直接证据；但任务是新增类，不是同标签空间漂移，且不含显式 label shift。
- **wiki**：`wiki/papers/methodology/2024-Raghavan-DELTA长尾在线持续学习.md`。
- **Zotero**：已入库，key `BJ6CG2AT`（DOI 导入，PDF 已附）。

### 7.3 Online Label Shift（2305.19570）

- **原件**：`raw/papers/methodology/2023-Baby-Online-Label-Shift.pdf`（42 页）。
- **元数据**：NeurIPS 2023；DOI `10.52202/075280-2868`；作者 Dheeraj Baby, Saurabh Garg, Tzu-Ching Yen, Sivaraman Balakrishnan, Zachary Chase Lipton, Yu-Xiang Wang。
- **全文**：`/tmp/2026-10-20-cRT长尾再平衡文献/md/ols/ols.md`；JSON `.../mdjson/ols.json`。
- **页码锚点**：OLS 定义 §2 p3；UOLS 重加权 §3 p4；Algorithm 2/Theorem 2 p5–6；SOLS/Theorem 6 p10；Table 1–2 p9–10；限制 Appendix A p16。
- **与 M2' 关系**：最清晰的“先验漂移”形式化与动态遗憾；但显式假设 \(Q_t(x\mid y)\) 不变，且不是长尾方法。适合做诊断臂，不适合作为机制主张。
- **wiki**：`wiki/papers/methodology/2023-Baby-在线标签移位.md`。
- **Zotero**：已入库，key `ZW67265D`（DOI 导入，PDF 已附）。

### 7.4 LIMES（2206.05181）

- **原件**：`raw/papers/methodology/2022-Tomaszewska-LIMES-Class-Prior-Shift.pdf`（9 页）。
- **元数据**：ICPR 2022；DOI `10.1109/ICPR56361.2022.9956195`；作者 Paulina Tomaszewska, Christoph H. Lampert。
- **全文**：`/tmp/2026-10-20-cRT长尾再平衡文献/md/limes/limes.md`；JSON `.../mdjson/limes.json`。
- **页码锚点**：设定 §2.1 p3；class-prior shift §2.3 p4；Eq. 7/9 p4；外推 §2.4 p5；Table 1 p6–7。
- **与 M2' 关系**：最轻量的“年度先验 bias 校正 + 外推”；但假设 \(q(x\mid y)=p(x\mid y)\)，且漂移是周期性/可外推的。
- **wiki**：`wiki/papers/methodology/2022-Tomaszewska-LIMES流式类先验漂移.md`。
- **Zotero**：已入库，key `NX7JYS84`（DOI 导入，PDF 已附）。

## 8. 四个必答问题的结论

1. **cRT 精确协议**：冻结骨干；随机重初始化分类器；类平衡采样 + CE；10 epoch；SGD 动量 0.9、batch 512、cosine 0.2→0（Kang §4、§5.1）。增益：ImageNet-LT `44.4`→`49.5`（ResNeXt-50）、`34.8`→`41.8`（ResNet-10）；Places-LT `30.2`→`36.7`；iNat `61.7/65.8`→`65.2/67.6`（Table 2–3）。与 NCM 的区别：NCM 不训练、不采样，直接类均值最近邻；NCM 在 few-shot 分片接近 cRT，整体低 2–7 个点。
2. **Balanced Softmax / Logit Adjustment 是否假设 label shift**：是。两者都假设 \(p(x\mid y)\) 固定、只变 \(p(y)\)（BSM §3.1 第 3 页；LA Eq. 7–8 第 5 页）。在 \(p(x\mid y)\) 也漂移时前提不成立：先验偏移无法吸收特征分布变化。**结论：可迁移为基线/诊断，不可迁移为机制主张。** 本课题已实测 \(p(x\mid y)\) 跨年漂移为 **33.5× 采样噪声**（最相似的一对年度仍 5.6×；`thesis/experiments/llm_probe/runs/diagnostics/ch4-prior-shift-diagnostic/prior_shift_diag.json` 的 `per_label["0"].ratio=33.5316`；`.Codex/docs/LAMDA/LAMDA路线总控.md` 第 521 行已据此否决“先验／标签转移校正”方向）。因此 label shift 前提在本课题**已不成立**，先验校正只能作诊断/基线。
3. **DRW 精确调度**：\(t\le T_0\) 自然 ERM；\(t>T_0\) 用 \(n_y^{-1}\) 重加权并归一化学习率（Algorithm 1，第 6 页）。\(T_0\) 绑定学习率退火点：CIFAR 200 epoch / 160 退火 → \(T_0=160\)（0.80）；iNat 90 epoch / 60 再平衡 → \(T_0=60\)（0.667）；Tiny ImageNet 120 epoch / 90 衰减 → \(T_0=90\)（0.75）。10 epoch 年度协议的任务化：先测 \(T_0=8\)，并测 7/6 作为敏感性；这是假设，需实验。
4. **漂移 + 长尾联合证据**：**未检得**。LT-CIL/DELTA 是长尾 + 序列/在线任务（新增类），OLS/LIMES 是标签比例漂移 + 类条件不变；没有论文同时处理 \(p(x\mid y)\) 漂移 + 长尾 + 分类器再平衡。

## 9. Zotero 状态

- 已入库（7/7）：
  - LADE `V3UP8CV5`（DOI 导入，PDF 已附）
  - LT-CIL `YXSSPY5R`（arXiv 导入，PDF 已附）
  - DELTA `BJ6CG2AT`（DOI 导入，PDF 已附）
  - OLS `ZW67265D`（DOI 导入，PDF 已附）
  - LIMES `NX7JYS84`（DOI 导入，PDF 已附）
  - BSM `LAV9HUZX`（arXiv abs 页面导入后改为 preprint；arXiv API 多次 429/timeout；PDF 已附）
  - LA `IFIFVMX8`（同上；PDF 已附）
- 查重：入库前按题名检索 Zotero，7 篇均无既有条目。
- 说明：BSM/LA 的条目字段（作者、日期、arXiv ID、venue）已用 arXiv API 返回值核对并手工写入；网页导入的 `needs-metadata` 标签已移除。PDF 由 `zotero_find_and_attach_pdfs` 附加。

## 10. 待办 / 阻塞

- [x] BSM、LA 的 Zotero 入库（改用 arXiv abs 页面导入 + preprint 更新）。
- [x] 用 `yaml` 解析器校验 7 篇笔记的 frontmatter（全部 OK）。
- [x] 核对 INDEX 中的链接文件名与实际文件一致（全部 OK）。
- [ ] 不 commit（任务要求）。
