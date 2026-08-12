# 跨年度迁移学习候选方案证据台账

## 研究合同摘要

- 研究对象：LSPR23 有标签源年度到 LSPR24 无标签目标前缀的跨年度网络攻击状态检测。
- 目标失效：源验证近饱和而目标开发 PR-AUC 显著下降；源冻结阈值可能导致恶意召回为零。
- 决策指标：目标开发 PR-AUC、固定告警预算召回、恶意 F1、校准、域可分性、负迁移诊断和效率。
- 证据等级：全文核验 > 正式元数据/摘要 > 二手线索；只有前者可支持方法细节和公式陈述。

## 5W1H 研究问题卡

- **做什么**：识别能同时改善跨年排序与有限告警预算召回的迁移机制。
- **为什么**：现有真实 Q0 结果表明跨年性能崩塌，单纯源域风险训练与目标状态校正均未晋级。
- **面向谁**：论文第三章方法设计与后续共同预算实验。
- **何时**：源训练发生在 LSPR23；目标适应只能使用 LSPR24 前 10% 前缀，并在随后 70% 开发区评价。
- **何处**：输入、表示、状态、分类头、先验/决策阈值五个可分作用层。
- **怎么做**：以失效诊断决定是否启用类条件对齐、受污染门控状态适应、标签移位校正、局部支持传输或不变风险机制。

## 检索日志

### 2026-08-12 第一轮广搜与题名核验

- 查询式：`2023 2024 2025 unsupervised domain adaptation network intrusion detection temporal drift paper`
- 查询式：`2023 2024 2025 test-time adaptation anomaly detection contaminated stream paper`
- 查询式：`2023 2024 2025 time series unsupervised domain adaptation partial open set negative transfer paper`
- 查询式：`2023 2024 2025 optimal transport domain adaptation partial support label shift paper`
- 题名核验：`"Domain Adaptation for Time Series Under Feature and Label Shifts"`、`"Boosting Transferability and Discriminability for Time Series Domain Adaptation"`、`"Label Alignment Regularization for Distribution Shift"`、`"Can We Evaluate Domain Adaptation Models Without Target-Domain Labels?"`。
- 命中：RAINCOAT、ACON、标签对齐正则、迁移分数、原型部分最优传输、WARMPOT、DI-NIDS、ReCDA 及其期刊扩展。
- 去重：以题名、数字对象标识符和正式会议页去重；RAINCOAT、ACON、标签对齐正则、迁移分数均未在既有 Zotero 题名盘点中发现。
- 排序影响：时间—频率联合表示和通用域适应已有强近邻，不能作为独立原创；“无标签负迁移门禁”和“支持不重叠下的部分传输”进入候选核心机制。

### 2026-08-12 安全领域精确追踪

- 查询式：`"Self-Supervised Adaptation Method to Concept Drift for Network Intrusion Detection" pdf author`
- 查询式：`"DI-NIDS" "Domain invariant network intrusion detection system" pdf`
- 查询式：`ReCDA concept drift adaptation representation enhancement network intrusion detection KDD 2024 pdf`
- 查询式：`site:dl.acm.org "RecDA" concept drift`
- 查询式：`"10.1109/TDSC.2025.3599321" pdf`
- 结果：DI-NIDS 取得公开全文；KDD 2024 的 ReCDA 与 2025 年 IEEE TDSC 扩展仅取得正式元数据和摘要，尚未找到合法公开全文。
- 纠错：搜索线索曾把 `arXiv:2402.19407` 错配为 ReCDA；核验首页发现其实际为 MENTOR，已从 `raw/` 移到临时隔离目录，不纳入全文计数、索引或 Zotero。

### 2026-08-12 第二轮机制查重

- 查询式：`2024 2025 rare class imbalanced partial optimal transport unsupervised domain adaptation paper`
- 查询式：`2024 2025 negative transfer unsupervised domain adaptation model selection without target labels paper`
- 查询式：`2023 2024 2025 label shift anomaly detection time series domain adaptation paper`
- 查询式：`2023 2024 2025 causal invariant domain adaptation nonstationary time series paper`
- 高相关命中：NeurIPS 2024 *Towards Reliable Model Selection for Unsupervised Domain Adaptation*；2025/2026 *Time Series Domain Adaptation via Latent Invariant Causal Mechanism*；2025 *Bi-level Unbalanced Optimal Transport for Partial Domain Adaptation*；2023 *Context-aware Domain Adaptation for Time Series Anomaly Detection*。
- 当前证据等级：仅完成正式页/摘要初筛，尚未下载、全文核验、去重或纳入计数；不得据此形成公式或有效性论断。
- 初步排序影响：尚未改变“部分传输必须增加稀有恶意质量保护”和“无标签门禁不能依赖单一代理分数”的前两项判断；因果机制候选是否保留必须等全文核验，不得提前晋级。

## 全文核验记录

### 检查点一：新增全文 1–4

#### 1. RAINCOAT：特征与标签移位下的时间序列域适应

- 题录：Huan He 等，*Domain Adaptation for Time Series Under Feature and Label Shifts*，ICML 2023，PMLR 202:12746–12774，`arXiv:2302.03133`。
- 正式来源：https://proceedings.mlr.press/v202/he23b.html；作者项目/官方源码：https://github.com/mims-harvard/Raincoat 。
- 原件：`raw/papers/methodology/2023-He-RAINCOAT-Time-Series-Domain-Adaptation.pdf`；SHA-256：`64db1dc8780b3277aa8818cf19b0c04f8679833acf50229e61ebc90b62d4e4e7`。
- 证据等级：正式开放全文，已核验方法、算法、消融和附录；结构化 `wiki` 笔记与 Zotero 条目待本轮补齐。
- 关键位置：正文第 5.1–5.6 节给出时间—频率编码、Sinkhorn 对齐和“先对齐后纠正”；算法 1 给出两阶段训练；公式（6）定义 Sinkhorn 散度；表 2 分离频率编码、Sinkhorn 与纠正步骤。
- 机制判断：其目标纠正阶段以重构目标样本并度量对齐前后到原型的位移来发现目标私有类，已占据“时间—频率表示 + Sinkhorn + 纠正”的通用组合。
- 纳入理由：直接覆盖时间序列特征移位、类别集合变化和支持错位，是普通 MMD/全量最优传输的强基线与原创边界。
- 与本任务关系：LSPR24 的恶意稀有类不能被全局质量搬运强制压入良性原型；若使用最优传输，必须增加稀有类质量下限、局部支持拒绝和因果前缀门禁，而不能照搬 RAINCOAT。
- 局限：论文按完整目标数据集离线适应；其通用域设定与“同一二分类标签空间但攻击族/支持变化”不等价，也未研究含恶意污染的在线前缀。

#### 2. ACON：时间—频率互学习与相关子空间对抗

- 题录：Mingyang Liu 等，*Boosting Transferability and Discriminability for Time Series Domain Adaptation*，NeurIPS 2024，DOI `10.52202/079017-3187`。
- 正式来源：https://proceedings.neurips.cc/paper_files/paper/2024/hash/b61da4f02b271cb7b5e3d538e2b78fb9-Abstract-Conference.html；官方源码：https://github.com/mingyangliu1024/ACON 。
- 原件：`raw/papers/methodology/2024-Liu-ACON-Time-Series-Domain-Adaptation.pdf`；SHA-256：`52025907ec4397292c7cfe1ca94ec680dd2970033dbd78880e6adec1fd9d83f6`。
- 证据等级：正式开放全文，已核验方法、消融、资源和局限；`wiki`/Zotero 待补。
- 关键位置：第 4.1 节为多周期频率表示；第 4.2 节以双向知识蒸馏分别增强源时间特征判别性和目标频率特征可迁移性；第 4.3 节在时间—频率外积相关子空间做域对抗；表 4、表 9 给出逐机制消融。
- 纳入理由：是“频率更具域内判别性、时间更具跨域可迁移性”假设的强近邻，并明确把域对抗从原表示移到相关子空间。
- 与本任务关系：可作为有训练开销的强表示适应基线，但 LSPR 的目标对象是字段状态/包级表示而非规则采样传感器波形，频谱归纳偏置需先由真实可观测量证实。
- 局限：作者报告大方差时间序列上不稳定；目标无标签时各损失权重固定为 1，未解决稀有攻击类污染、先验变化和无标签模型选择。

#### 3. 标签对齐正则：只调整分类头的目标谱子空间适应

- 题录：Ehsan Imani 等，*Label Alignment Regularization for Distribution Shift*，JMLR 25(247):1–32，2024，`arXiv:2211.14960`。
- 正式来源：https://www.jmlr.org/papers/v25/23-0899.html；官方源码：https://github.com/EhsanEI/lar 。
- 原件：`raw/papers/methodology/2024-Imani-Label-Alignment-Regularization.pdf`；SHA-256：`f0f70fd9201edda79a6dfea7a22a965f891603e08b1294d264c7e2fdf1d8fffa`。
- 证据等级：正式期刊开放全文，已核验公式、算法、理论、实验选择协议和局限；`wiki`/Zotero 待补。
- 关键位置：第 4 节公式（6）在源平方损失中去除源尾部隐式谱正则，并惩罚预测落入目标低奇异值子空间；算法 1 通过源/目标协方差特征分解求解；第 5 节证明在给定假设下解落入目标顶端右奇异向量张成空间。
- 纳入理由：不同于 DANN/CORAL/MMD，它冻结或复用表示而适应分类头，适合先在现有缓存上做低成本证伪。
- 与本任务关系：可导出“恶意方向保留的目标谱头校正”：在目标顶端子空间约束之外，显式保护源恶意排序方向，避免稀有攻击信号恰好位于低方差子空间时被抹除。
- 关键限制：论文实验主要是二分类线性/浅层模型，并使用少量目标标签选择正则强度；这在 LSPR24 合同下不可接受。任何候选必须预注册秩/强度或以纯无标签门禁选择，且把目标恶意方向被投影掉列为硬否决条件。

#### 4. 迁移分数：无目标标签的域适应模型评价

- 题录：Jianfei Yang 等，*Can We Evaluate Domain Adaptation Models Without Target-Domain Labels?*，ICLR 2024，`arXiv:2305.18712`。
- 正式来源：https://proceedings.iclr.cc/paper_files/paper/2024/hash/96c6f409a374b5c81d2efa4bc5526f27-Abstract-Conference.html；官方项目：https://ntunlpsg.github.io/projects/transfer-score/ 。
- 原件：`raw/papers/methodology/2024-Yang-Transfer-Score-UDA-Evaluation.pdf`；SHA-256：`136d7aaed5e9aee3a1fd9f0788ff435b76eb0b1c6dade4a63bcb6657ebf26012`。
- 证据等级：正式会议开放全文，已核验公式、模型选择实验和失败讨论；`wiki`/Zotero 待补。
- 关键位置：第 4 节将分类器空间均匀性、Hopkins 聚类统计和预测互信息组合成无标签迁移分数；第 5 节分别检验方法选择、超参数选择与检查点选择；附录讨论直接优化互信息可“迎合”指标及特征过度集中问题。
- 纳入理由：直接服务于“目标前缀无标签时如何发现负迁移”，可作为启用、停机或回滚诊断的一项输入。
- 与本任务关系：应与源域排序保持、预测率变化、传输未匹配质量和多视图一致性共同构成门禁，不能单独决定候选优劣。
- 关键限制：其类别多样性/互信息假设与稀有恶意二分类冲突；把预测推向均衡可能虚增分数。因此必须预注册只作安全门禁而非训练目标，并在源保持与稀有率包络内解释。
- 检查点状态：上述四篇均完成全文核验；下载不计核验的边界已执行。下一组为原型部分最优传输、WARMPOT 与 DI-NIDS。

### 检查点二：新增全文 5–7

#### 5. 原型部分最优传输：通用域适应中的已知/未知质量分离

- 题录：Yucheng Yang、Xiang Gu、Jian Sun，*Prototypical Partial Optimal Transport for Universal Domain Adaptation*，AAAI 2023，37(9):10852–10860，DOI `10.1609/aaai.v37i9.26287`。
- 正式来源：https://ojs.aaai.org/index.php/AAAI/article/view/26287；作者公开全文：https://xjtu-xgu.github.io/xianggu/docs/AAAI2023_Prototypical_Partial_Optimal_Transport_for_Universal_Domain_Adaptation.pdf 。
- 原件：`raw/papers/methodology/2024-Yang-Prototypical-Partial-Optimal-Transport.pdf`；文件为作者于 2024 年上传的 AAAI 2023 正式论文版本，题录年份按正式会议记为 2023；SHA-256：`a3c1d40fef8e5e843016ba4955bfda61a3d465f057c66e8785a501e7693cd05f`。
- 证据等级：正式会议全文，已核验定义、定理、训练损失和消融；未找到由论文正式页直接指向的可信官方源码，`wiki`/Zotero 待补。
- 关键位置：第 4.1 节假设共享类别样本间传输成本低于私有—共享或私有—私有成本；公式（5）以共享比例控制传输质量；定义 1/公式（6）把源样本替换为源类原型；公式（7）为小批量 PPOT；命题 1 与定理 1 给出上界；公式（11）–（13）用传输计划边缘重加权目标熵和源交叉熵；表 4 分离 PPOT、普通部分传输与去重加权。
- 纳入理由：直接说明全量最优传输在类别集合/局部支持错配时会发生负迁移，并提供“未传输质量”这一可观测量。
- 与本任务关系：LSPR 二分类标签名相同并不保证攻击族支持相同。可把源恶意与良性原型分别设质量上下限，用未匹配目标质量、源原型行和与类间传输熵诊断支持错配。
- 关键限制：其核心前提是共享类之间比非共享类更近；跨年攻击表征若比良性漂移更大，该假设可能反转。论文以视觉多类准确率/H 分数评价，并把目标熵最小化用于“已知”样本，未处理低基率恶意污染和固定告警预算。

#### 6. WARMPOT：部分最优传输的目标风险界与构造性源权重

- 题录：Jayadev Naram 等，*Theoretical Performance Guarantees for Partial Domain Adaptation via Partial Optimal Transport*，ICML 2025，PMLR 267:45663–45681，`arXiv:2506.02712`。
- 正式来源：https://proceedings.mlr.press/v267/naram25a.html；正式页链接的官方源码：https://github.com/JayD2106/WARMPOT ，MIT 许可证。
- 原件：`raw/papers/methodology/2025-Naram-WARMPOT-Partial-Domain-Adaptation.pdf`；SHA-256：`bbd09b2caab7e87d9c29a28291be8199a057a17fe6a9c3039585b4464093be84`。
- 证据等级：正式会议开放全文，已核验主要界、算法、实验协议、超参数和官方源码；`wiki`/Zotero 待补。
- 关键位置：定义 3.1/公式（3）–（4）定义传输总质量为 `α` 的部分 Wasserstein 距离；定理 3.2 的公式（5）给出“构造性加权源经验损失 + 部分 Wasserstein + 目标边缘总变差 + 不可计算任务难度项”的目标经验风险界；定理 3.3 将成本扩展为特征距离与源标签—目标预测损失；公式（19）给出 WARMPOT 目标；第 4 节解释 `β` 控制参与匹配的源质量、`α` 控制参与匹配的目标质量；第 5.3 节与表 1 比较不同源权重。
- 纳入理由：为部分传输边缘作为源样本权重提供理论来源，也明确界中仍存在不可计算任务难度项，避免把“小传输距离”误称为目标风险保证。
- 与本任务关系：可把传输计划边缘用于源样本/环境加权，并以 `α、β` 非对称控制目标污染和源支持；但必须把恶意质量下限另行加入，因为无约束最小成本计划很可能优先搬运占绝大多数的良性质量。
- 关键限制：论文的标准部分域适应假设是目标标签集合为源标签集合子集，和 LSPR 的同名二分类/攻击族变化并不一致；实验仅为图像数据。正文固定 Office-Home 的 `(α,β)=(0.8,0.35)`，附录说明参数经搜索取得，不能把该数值迁入 LSPR；风险界依赖有界度量损失、分类头 Lipschitz 性和不可计算的任务难度项。

#### 7. DI-NIDS：DANN 表示后的一类异常检测

- 题录：Siamak Layeghy、Mahsa Baktashmotlagh、Marius Portmann，*DI-NIDS: Domain Invariant Network Intrusion Detection System*，Knowledge-Based Systems 273:110626，2023，DOI `10.1016/j.knosys.2023.110626`；公开预印本 `arXiv:2210.08252`。
- 正式元数据：https://about.uq.edu.au/experts-publication/24474/all；公开全文：https://arxiv.org/abs/2210.08252 。
- 原件：`raw/papers/attack-detection/2022-Layeghy-DI-NIDS-Domain-Invariant.pdf`；文件名按预印本年份保留，正式引用按 2023 期刊版；SHA-256：`2a54e452d3ebe2e69510be598baafc04e68c2f316ed265a31bf228a81b97bf3b`。
- 证据等级：作者公开预印本全文与机构正式题录交叉核验；未发现作者官方源码；`wiki`/Zotero 待补。
- 关键位置：第 3 节给出两阶段架构：以有标签源和无标签目标训练 DANN，再在域不变表示上训练一类支持向量机；公式（6）是源分类与源/目标域判别对抗目标；公式（9）是一类支持向量机目标；第 4 节做 NFv2-CIC-2018 与 NFv2-UNSW-NB15 双向跨数据集评价；表 5、表 6 显示跨域方向高度非对称，普通 DANN 在两个方向分别为 17.31% 和 61.94% F1。
- 纳入理由：直接属于跨域网络入侵检测，并明确指出一般域适应在高度不平衡异常任务上表现有限。
- 与本任务关系：DANN + 一类检测应列强基线；其结果也支持“域不可分不等于恶意排序保留”，必须额外监控源恶意排序方向和目标预算告警结构。
- 关键限制：训练 DANN 时使用整个目标数据集而非严格的因果前缀；论文只报告 F1，未报告 PR-AUC、固定预算召回或校准；没有攻击污染缓冲、类条件错配或负迁移回滚；因此普通 DANN 和普通一类检测均不能构成本任务原创。

- 检查点状态：新增 7 篇均完成全文核验；其中 6 篇为 2023–2025 正式论文、1 个原件以 2022 预印本对应 2023 期刊版。下一步执行第二轮受控查重，重点搜索稀有类部分传输、无标签负迁移选择、标签移位与因果/不变时间序列迁移。

## 综合发现

待阶段五填写。

## 未关闭疑点

1. LSPR24 前缀恶意污染率是否足以破坏熵最小化、批归一化统计或伪标签自训练？
2. 目标年度类先验变化与类条件分布变化能否被仅无标签前缀可靠区分？
3. 共同 77 字段在两年度是否存在局部支持不重叠，导致全局 DANN/CORAL/MMD/OT 强行对齐？
4. 固定告警预算下的阈值失效主要来自排序退化、先验变化还是概率校准漂移？
5. 哪些机制与候选 B 的角色分离物理时间状态、C12 的目标状态更新与双参照空间重叠？

## 下一检查点

### 2026-08-12 中断恢复检查点

- 已完成：规则与路线恢复；本地综述/C12 邻近工作/Zotero 盘点；两轮联网检索；7 篇新增全文逐篇核验；两次按 3–4 篇落盘的检查点；7 个原件哈希核验。
- 已验收原件：RAINCOAT、ACON、标签对齐正则、迁移分数、原型部分最优传输、WARMPOT、DI-NIDS，精确路径和 SHA-256 见上文各条。
- 已复用核心全文但尚未在本任务中重新逐条计数：DANN、Courty 最优传输、BBSE、JCPOT、加权保形、TTA-AD、RTTAD、CANDI、OWAD、SoTTA、FOIL、DIVERSIFY，以及既有 C12 近邻核验中的相关原件/笔记。
- 未完成：第二轮命中全文核验；7 篇 `wiki/papers` 结构化笔记；`raw/papers/INDEX.md` 与 `wiki/papers/INDEX.md` 最小追加；官方源码资源笔记；Zotero 导入及键回填；`references.bib`；主综述；候选总览；3–5 个候选详案与快速消融；停止条件复核。
- 未公开全文：ReCDA（KDD 2024，DOI `10.1145/3637528.3672007`）及其 IEEE TDSC 2025 扩展（DOI `10.1109/TDSC.2025.3599321`）。两者只有正式元数据/摘要，不计全文，不支持方法细节论断。
- 唯一续接入口：先读取本文件与 `task_plan.md`，随后从第二轮四个精确查询命中的正式全文去重开始；优先核验 NeurIPS 2024 无标签选模与 2025/2026 潜在因果机制，再决定候选排序。
- 当前候选只可视为方向草案：①稀有恶意质量保护的非对称部分传输 + 负迁移停机；②恶意方向保留的目标谱分类头校正 + 标签移位/预算校准；③污染隔离的因果前缀/状态适应 + 源排序锚。全部状态均为“实验待证”，名称、公式与排序尚未冻结。
