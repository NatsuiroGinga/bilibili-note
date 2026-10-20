# 第二机制方向定向检索 - 检索笔记

状态：第一轮完成（2026-10-20）
任务目录：`.Codex/docs/2026-10-20-第二机制方向文献检索/`

## 0. 方法、通道与限制（先读）

### 0.1 实际可用的通道

| 通道 | 状态 | 说明 |
| --- | --- | --- |
| 本地混合索引 `scripts.literature_search` | **未能运行** | 本次会话未提供 Bash 工具，无法执行 `uv run --project scripts/literature_search ...`；向量通道未运行 |
| 本地知识库文件级检索 | 已执行 | 用关键词联合式在 `wiki/papers/**` 上做文件级词法检索（等价于 `--mode lexical` 的降级替代，但不是官方索引） |
| Zotero arXiv 导入 | 已执行 | `zotero_add_items_by_arxiv(["2002.06715"])` → item `Z76PRWPW`，返回标题/作者/日期/ID 并附 PDF |
| WebFetch（arXiv/Crossref/S2/OpenReview/dblp API） | **全部被域名安全策略拦截** | 无法直接调用题录 API；改用 WebSearch 多源交叉 + Zotero arXiv 导入 |
| WebSearch | 已执行 | 返回链接与摘要；题录以多源一致为准，逐条标注验证等级 |

**证据等级定义**：`E1` 本地全文；`E2` 在线全文（本次未取得）；`E3` 官方 API/出版社元数据；`E4` 多源搜索结果一致（题名+作者+venue/DOI）；`E5` 仅单一搜索摘要或作者/页码待核。

### 0.2 检索式记录（组 1，方向 A）

1. `dynamic ensemble size selection adaptive number of ensemble members neural network paper`
2. `ensemble size selection accuracy diversity trade-off paper "ensemble size"`
3. `conditional computation early exit adaptive compute per sample neural network survey`
4. `class imbalance ensemble learning undersampling balanced bagging random forest paper`
5. 题录追查：`"A dynamic ensemble learning algorithm for neural networks" Alam ... DOI`；`"Less Is More" "Number of Components of Ensemble Classifiers" ...`；`"Conditional computation in neural networks" ... arXiv`；`"Exploratory undersampling..." Liu Wu Zhou`；`Chen Liaw Breiman "Using Random Forest to Learn Imbalanced Data"`；`"PonderNet" "Learning to Ponder"`

### 0.3 检索式记录（组 2，方向 B）

1. `mixture of experts routing by task domain continual learning paper`
2. `parameter isolation continual learning PackNet HAT progressive neural networks catastrophic forgetting`
3. `"BatchEnsemble" lifelong learning split CIFAR one ensemble member per task cyclic learning rate`
4. `per-task adapters multi-domain learning shared backbone task-specific adapter paper Houlsby`
5. 题录追查：`"Expert Gate" ... Aljundi`；`"PackNet..." Mallya Lazebnik`；`"Overcoming Catastrophic Forgetting with Hard Attention..." Serra`；`Rusu "Progressive Neural Networks" 1606.04671`；`Houlsby "Parameter-Efficient Transfer Learning..."`；`"Efficient Continual Learning with Modular Networks and Task-Driven Priors"`；`"Dynamic Ensemble Member Selection for Data Stream Classification" authors`

### 0.4 本地命中（文件级词法）

命中但未逐篇打开的：`wiki/papers/attack-detection/lamda-related/2026-Han-DMAE...`、`.../2025-Seo-预算化在线持续学习...`、`wiki/papers/attack-detection/encrypted/2026-Tan-MalMoE...`、`wiki/papers/traffic-foundation-models/2601.00357_Traffic-MoE...`、`wiki/papers/pinn/*`（MoE 系列）。

其中两篇已读并确认与方向直接相关：

- **DMAE（2026，Han 等）**：类不平衡 + 概念漂移 + **自适应集成规模** + 成员准入/替换；全文转换稿已在库，**无需重复入库**，但缺结构化笔记。方向 A 的库内最强先例。
- **MalMoE（2026，Tan 等，INFOCOM 2026）**：按漂移类型硬选择聚合算子专家；已是 E3 结构化笔记。方向 B 的领域内 MoE 先例。

## 1. 关键题录核实：BatchEnsemble（最高优先）

### 1.1 核实结果

| 项 | 值 | 来源与等级 |
| --- | --- | --- |
| 题名 | BatchEnsemble: An Alternative Approach to Efficient Ensemble and Lifelong Learning | Zotero arXiv 导入（E3） |
| 作者 | Yeming Wen, Dustin Tran, Jimmy Ba | Zotero arXiv 导入（E3）；PDF 第 1 页一致 |
| arXiv ID | **2002.06715**（v2，2020-02-20） | Zotero 导入返回 URL；PDF 第 1 页页脚 `arXiv:2002.06715v2 [cs.LG] 20 Feb 2020` |
| 会议 | **ICLR 2020** | PDF 每页页眉 `Published as a conference paper at ICLR 2020`（物理第 1 页起） |
| 年份 | 2020 | arXiv 首发 2020-02-17（Zotero），v2 2020-02-20 |

结论：**题录假设属实**。arXiv ID、作者、题名、ICLR 2020 全部核实；ICLR 状态不是来自 arXiv 元数据（其 comments 字段未含会议），而是来自 PDF 页眉。

### 1.2 页码锚点（物理页 = PDF 页）

| 内容 | 页码 |
| --- | --- |
| 标题、作者、单位 | 1 |
| 式 (1) `W_i = W ∘ r_i s_i^T` | 4 |
| 式 (5) 批内向量化 | 5 |
| §3.2 计算/内存开销；ResNet-32 规模 4 参数 +10% | 5 |
| §3.3 终身学习；式 (6)(7)；一任务一成员 | 5 |
| 表 1 计算/内存对照；作者自述两条局限 | 6 |
| §4.1 Split-CIFAR100（20 任务）/ Split-ImageNet（100 任务）；4× 加速、50× 内存节省、20% 参数开销 | 6–7 |
| §5 多样性分析（数据越少，秩一集成越接近独立初始化） | 10 |
| 附录 B 快权重随机符号初始化、成员独立子批 | 15 |
| 附录 E 多样性随训练数据比例变化 | 17–19 |

### 1.3 关键事实（用于方向 B）

- **每任务一个成员**：`W^t = W ∘ (r_t s_t^T)`；首任务训练 `W, s_1, r_1`（式 6），后续任务只训练 `s_t, r_t`（式 7）（第 5 页）。
- 共享权重只在首任务训练，旧任务模型逐位不变，**无回放缓冲**；作者明确「只有第一任务知识能显式迁移，第二与第三任务之间没有显式迁移」（第 6 页）。
- 每任务一个**不同的最终分类层**（Split-CIFAR100/ImageNet），利用任务描述符；测试时按任务描述符选成员，不是跨成员平均（第 5、7 页）。
- 作者自述边界：秩一扰动表达能力在任务差异大时是真实担忧（第 6 页）。
- 多样性分析：训练数据越少，BatchEnsemble 与独立初始化朴素集成的多样性越接近，增益越大；CIFAR-100 每类 500 样本的增益大于 CIFAR-10 每类 5000（第 10 页、附录 E）。**这是方向 A 的机制线索，但原文的稀缺是总样本量，不是正例稀缺度，且集成规模固定。**

### 1.4 入库状态

- 已写入全文笔记：`wiki/papers/methodology/2020-Wen-BatchEnsemble高效集成与终身学习.md`
- 已更新索引：`wiki/papers/methodology/INDEX.md`（新增「参数高效集成与终身学习」节）
- Zotero：item `Z76PRWPW`，PDF 已附。
- **未完成**：仓库原件 `raw/papers/methodology/2020-Wen-BatchEnsemble.pdf` 未复制；SHA-256 未计算；MinerU 未运行。原因：本次会话无 Bash。PDF 实际位于 `/Users/bilibili/Zotero/storage/MYN6DVSJ/Wen 等 - 2020 - BatchEnsemble ....pdf`。补做时需复制、算哈希并回填笔记 `sha256` 字段。

## 2. 组 1：方向 A（缺口加权集成容量调度）锚点表

> 只登记候选，不做存废裁决。`全文入库` 列是建议，不是决定。

| # | 论文（题名 / 作者 / 年 / venue / ID） | 题录验证 | 证据等级 | 与方向 A 的关系 | 全文入库 |
| --- | --- | --- | --- | --- | --- |
| A1 | **A dynamic ensemble learning algorithm for neural networks**. Alam, Siddique & Adeli. 2020. *Neural Computing and Applications* 32(12):8675–8690. DOI 10.1007/s00521-019-04359-7 | 多源一致（Springer/ACM/NSTL/Mendeley），DOI 可解析（E4） | E4（摘要级） | 用构造式策略**自动决定集成规模**、各成员隐藏节点数与训练样本；以负相关学习维持多样性。与「按稀缺度调制成员数」最接近的通用先例 | **建议（首选）** |
| A2 | **Less Is More: A Comprehensive Framework for the Number of Components of Ensemble Classifiers**. Bonab & Can. 2019. *IEEE TNNLS* 30(9):2735–2745. DOI 10.1109/TNNLS.2018.2886341 | PubMed + dblp + Semantic Scholar 一致（E4） | E4（摘要级） | 给出成员数的几何框架：加权多数投票下理想成员数约等于类别数（独立性/强度假设下）；为「成员数不是越多越好」提供理论锚点 | 建议（理论锚点，篇幅短） |
| A3 | **Conditional computation in neural networks: Principles and research trends**. Scardapane 等. 2024. arXiv:2403.07965；*Intelligenza Artificiale* 18(1):175–190，DOI 10.3233/IA-240035 | arXiv ID + 期刊 DOI 多源一致；**作者顺序待核**（arXiv 列表以 Scardapane 为首，期刊引用页显示 Baiocchi 在前）（E4/E5） | E4 | 把 early-exit、MoE、token selection 统一为「按输入激活子图」的容量调度框架；方向 A 的上位概念地图 | 建议（综述，低成本） |
| A4 | **PonderNet: Learning to Ponder**. Banino, Balaguer & Blundell. 2021. arXiv:2107.05407 | arXiv ID + 多源一致（E4） | E4（摘要级） | 用学习到的 halting 分布按难度决定计算步数；是「动态容量」的可微实现参考，但分配对象是深度步数，不是集成成员数 | 可选（机制参考） |
| A5 | **Exploratory undersampling for class-imbalance learning**. Liu, Wu & Zhou. 2009. *IEEE TSMC-B* 39(2):539–550. DOI 10.1109/TSMCB.2008.2007853 | PubMed + ACM 一致（E4） | E4（摘要级） | EasyEnsemble / BalanceCascade：用多个欠采样成员覆盖多数类，把**成员数与不平衡处理**直接耦合；方向 A 的正统 class-imbalance + ensemble 锚点 | **建议（首选）** |
| A6 | **Using Random Forest to Learn Imbalanced Data**. Chen, Liaw & Breiman. 2004. UC Berkeley Tech Report 666 | 多源一致（E4） | E4（摘要级） | Balanced Random Forest：每棵树在平衡欠采样子集上训练；「成员各自见平衡子样本」的直接先例 | 可选（技术报告，经典） |
| A7 | **Dynamic Ensemble Member Selection for Data Stream Classification**. Sun, Pfahringer, Gomes & Bifet. 2025. *CIKM '25*. DOI 10.1145/3746252.3761072 | 多源一致（ACM/Semantic Scholar/作者主页）（E4） | E4（摘要级） | 全在线成员选择：用实时精度与模拟预测 margin 排序并维护成员集合；方向 A 的「流式成员调度」最近邻 | **建议（首选）** |
| A8 | **DMAE: dual-memory active ensemble learning for multi-class imbalanced concept-drifting data streams**. Han 等. 2026. 期刊待核 | **已在库**（全文转换稿） | **E1（本地全文）** | 类不平衡 + 概念漂移 + **自适应集成规模** + 候选成员试用/软替换；与方向 A 的场景最同构 | 无需重复入库；建议补结构化笔记 |
| A9 | Pareto analysis for the selection of classifier ensembles. Dos Santos 等. 2008. GECCO | 仅单一搜索摘要，作者/页码待核（E5） | E5 | 把集成误差、规模、多样性作为三目标做帕累托分析；可作为 A2 的补充 | 暂不推荐（题录不全） |

### 方向 A 推荐全文入库（按优先级）

1. **A7 Sun et al. 2025（DEMS）**：最新的在线成员选择，最接近「按当前需求维护成员集合」。
2. **A1 Alam et al. 2020**：唯一明确「自动决定集成规模 + 成员训练样本 + 多样性」的神经网络方法。
3. **A5 Liu, Wu & Zhou 2009**：不平衡驱动的多成员覆盖，给方向 A 提供「稀缺→多成员」的经典依据。

可选补充：A3 综述（快速建立 early-exit/MoE 的概念边界）、A2 理论锚点。

## 3. 组 2：方向 B（成员-年度锚定）锚点表

| # | 论文（题名 / 作者 / 年 / venue / ID） | 题录验证 | 证据等级 | 与方向 B 的关系 | 全文入库 |
| --- | --- | --- | --- | --- | --- |
| B1 | **BatchEnsemble: An Alternative Approach to Efficient Ensemble and Lifelong Learning**. Wen, Tran & Ba. 2020. ICLR 2020. arXiv:2002.06715v2 | **已 API 核实 + 全文直读**（E3+E1） | **E1** | **正源**：一任务一成员，共享慢权重 + 任务快权重；无回放、构造性无遗忘；推理需任务描述符 | **已完成** |
| B2 | **Expert Gate: Lifelong Learning With a Network of Experts**. Aljundi, Chakravarty & Tuytelaars. 2017. CVPR 2017. arXiv:1611.06194 | 多源一致（CVF/arXiv/Avalanche 文档）（E4） | E4（摘要级） | 每任务一个 expert + 每任务一个 gating autoencoder；测试时按重构误差**无任务标签路由**。方向 B 若年度描述符不可得，这是关键先例 | **建议（首选）** |
| B3 | **Efficient Continual Learning with Modular Networks and Task-Driven Priors**. Veniat, Denoyer & Ranzato. 2021. ICLR 2021. arXiv:2012.12631 | 多源一致（HAL/Semantic Scholar/SlidesLive）（E4） | E4（摘要级） | 每任务学习「每层选一个模块」的布局，模块跨任务共享，只训练新模块；参数/计算随任务数**次线性**增长。固定 k 个成员覆盖 12 年的直接结构参考 | **建议（首选）** |
| B4 | **PackNet: Adding Multiple Tasks to a Single Network by Iterative Pruning**. Mallya & Lazebnik. 2018. CVPR 2018, pp. 7765–7773. arXiv:1711.05769；DOI 10.1109/CVPR.2018.00810 | 多源一致（CVF/arXiv/IEEE）（E4） | E4（摘要级） | 迭代剪枝 + 任务 mask；单网络多任务、容量不增长 | 题录级确认即可（按任务要求） |
| B5 | **Overcoming Catastrophic Forgetting with Hard Attention to the Task**. Serrà, Surís, Miron & Karatzoglou. 2018. ICML 2018, PMLR 80:4548–4557. arXiv:1801.01423 | 多源一致（PMLR/arXiv/GitHub）（E4） | E4（摘要级） | 每任务近二值硬注意力 mask，冻结旧任务重要参数 | 题录级确认即可（按任务要求） |
| B6 | **Progressive Neural Networks**. Rusu 等. 2016. arXiv:1606.04671 | 多源一致（arXiv/引用）（E4） | E4（摘要级） | 每任务一列新网络 + 侧连接，旧列冻结；方向 B 的「任务隔离」原型，但参数线性增长 | 题录级确认即可（按任务要求） |
| B7 | **Parameter-Efficient Transfer Learning for NLP**. Houlsby 等. 2019. ICML 2019, PMLR 97:2790–2799. arXiv:1902.00751 | 多源一致（PMLR/ACL 引用）（E4） | E4（摘要级） | 共享冻结骨干 + 任务专属 bottleneck adapter；per-task adapter 正源，参数量 0.5–5% | 可选（若方向 B 走 adapter 路线） |
| B8 | **Advancing SMoE for Continuous Domain Adaptation of MLLMs: Adaptive Router and Domain-Specific Loss**. ACL 2025 Long 1290 | 题名/venue 由 ACL Anthology URL 确认；作者待核（E5） | E5 | **Domain-IL** 下每个新域学一个 domain-specific SMoE 模块 + 自适应阈值路由；与方向 B 最同构的近期工作 | 建议先补题录再决定 |
| B9 | **MoTE: Mixture of task-specific experts for pre-trained model-based Class-incremental learning**. *Knowledge-Based Systems*（PII S095070512500841X） | 题名/venue 由 ScienceDirect URL 确认；作者/年待核（E5） | E5 | 每任务一个轻量 adapter，测试时做专家过滤与加权联合推理，避免显式 router 被覆盖 | 暂不推荐（题录不全） |
| B10 | **Beyond Routing Saturation: A Long-Horizon Class-Incremental Perspective on Expert Routing...**. arXiv:2608.01437 | arXiv ID 来自搜索结果 URL；作者待核（E5） | E5 | 警告：任务身份泄漏会让路由过于容易；提出 34 任务 FLEX 基准。方向 B 必须区分「年度描述符可用」与「需无标签路由」两种设定 | 暂不推荐（题录不全，但结论值得记录） |
| B11 | **MalMoE: Mixture-of-Experts Enhanced Encrypted Malicious Traffic Detection Under Graph Drift**. Tan 等. 2026. INFOCOM 2026. arXiv 2602.10157v1 | **已在库，E3 结构化笔记** | **E1/E3** | 按漂移类型硬选择聚合算子专家；领域内 MoE 先例，说明「专家=机制」而非「专家=年度」 | 无需重复入库 |

### 方向 B 推荐全文入库（按优先级）

1. **B2 Expert Gate（Aljundi 2017）**：解决「推理时没有年度标签」的第一候选；每任务 autoencoder 做无标签路由。
2. **B3 Veniat et al. 2021（Modular Networks）**：固定/次线性模块数 + 每任务布局，最接近「k 个成员覆盖 12 年」的参数预算问题。
3. **B8 ACL 2025 SMoE Domain-IL**（先补作者/页码）：设定最同构的近期工作，若题录补齐则优先。

B1 已完成全文入库；B4–B6 按要求只做题录级确认。

## 4. 两方向的交叉判断（只记事实，不做裁决）

- **方向 A 的文献缺口**：现有工作调节的是「成员数/成员选择」或「每样本计算量」，**没有**按「年度正例稀缺度」调制集成容量。BatchEnsemble 只提供「数据越少，集成多样性收益越大」的相关证据（第 10 页），不是调度机制。
- **方向 B 的文献缺口**：一任务一成员有明确正源（B1），但所有正源都假设**任务边界与任务描述符可得**；LAMDA 的年度边界可得（按年切分），但年度描述符在推理时是否可用取决于评测协议。B2 提供无标签路由，B10 警告路由饱和。
- **与 TabM4 的预算冲突**：BatchEnsemble 的终身学习成员数 = 任务数（20/100），TabM4 固定 k=4；固定 k 覆盖 12 年没有原文证据，需自行定义「年度组」并做同预算消融。

## 5. 未关闭事项

1. 补做 BatchEnsemble 的 `raw/` 原件、SHA-256、MinerU 转换（需 Bash）。
2. 本地混合索引（`scripts.literature_search`）未运行；下次有 Bash 时应重跑 `status --json` 与 `query ... --scope paper --mode hybrid --json`，确认本笔记的文件级词法结果没有漏检。
3. B8/B9/B10 的作者、年份、页码待补；补齐前不得写入正文。
4. A9 题录待补，暂不作为锚点。
5. Zotero 中 BatchEnsemble 已入库（`Z76PRWPW`），其余候选未导入；是否批量导入待用户裁决。
