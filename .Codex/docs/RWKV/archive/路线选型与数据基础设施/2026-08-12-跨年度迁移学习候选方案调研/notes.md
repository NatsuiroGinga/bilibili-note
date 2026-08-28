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
- 当前证据等级：4 篇均已完成正式页去重、公开全文下载与逐篇方法/实验/局限核验；EnsV 正文与补充材料合计只计 1 篇。精确原件、哈希和裁决见检查点三。
- 排序影响：无标签选模可作为停机/回滚的一项证据，但多数类预测共识会遮蔽稀有恶意排序崩塌，不能独立充当门禁；双层非平衡传输仍缺少恶意质量下限，强化第一候选的实质改造边界；潜在因果全模型与上下文窗口适应均依赖弱序列骨干或强结构假设，结合真实 Q0 结果后不进入前三候选。

### 2026-08-12 真实实验硬证据与候选约束

- 共同 XGBoost 的目标开发 PR-AUC 为 `0.03890259`，Dijk 约束 XGBoost 为 `0.0368559`。
- 1D-CNN 为 `0.0176996`；候选 B 最佳离散 RWKV 为 `0.01920596`，角色分离物理时间变体为 `0.01012302`。
- C12 最佳 K-DELTA 为 `0.01697728`；C12-R 六格均不超过 `0.00927448`，且源冻结阈值下恶意召回均为 `0`；R1 最佳 GroupDRO 为 `0.0128779`。
- 证据解释：树模型显著领先全部小型序列模型，当前优先修复跨年可迁移表示与排序，不在弱排序器上继续叠加时间衰减、门控、回退或阈值；C12-R 的局部预算改善伴随 PR-AUC 下降，纯决策校准不得作为主创新；候选 B 的时间机制确实改变输出但恶化排序，时间/频率分支暂缓。
- 方案硬约束：第一候选保留 XGBoost 强锚，研究“稀有恶意质量保护的非对称部分传输 + 无标签负迁移停机/回滚”；第二候选为“XGBoost 分数或叶表示 + 有界 RWKV 残差”；第三候选的谱分类头校正只有在不使用目标标签且非单调地改变排序时才保留，纯单调校准直接淘汰。全部仍为“实验待证”。

### 2026-08-12 第三轮窄查重与停止裁决

- 查询式：`2023 2024 2025 "gradient boosted trees" domain adaptation transfer learning paper`
- 查询式：`2023 2024 2025 XGBoost leaf representation domain adaptation paper`
- 查询式：`2023 2024 2025 minority class protected mass partial optimal transport domain adaptation`
- 查询式：`2023 2024 2025 unsupervised domain adaptation ranking model selection without target labels rare class`
- 查询式：`2023 2024 2025 XGBoost RWKV residual hybrid tabular time series paper`
- 查询式：`2023 2024 2025 gradient boosting leaf embedding neural residual domain adaptation`
- 查询式：`2023 2024 2025 spectral classifier head unsupervised domain adaptation minority rare class`
- 查询式：`2023 2024 2025 label alignment regularization anomaly ranking domain shift`
- 高相关新增：ICML 2025 *PROTOCOL: Partial Optimal Transport-enhanced Contrastive Learning for Imbalanced Multi-view Clustering*。该文已把部分传输、渐进质量、非平衡类别边缘与少数类表示再平衡组合，因此“质量约束”或“少数类再平衡”本身也不能作为原创。
- 去重与排除：未检出 2023–2026 年把 XGBoost 叶表示、RWKV 有界残差与无标签跨年度域适应同构组合起来的正式原论文；命中的树流式增量学习、分布值梯度提升和监督适应不满足本任务的无标签目标前缀合同，不纳入全文集合。谱头检索回到已核验的标签对齐正则，未发现改变第三候选边界的新机制。
- 排序结果：PROTOCOL 收紧但不推翻第一候选；第一候选的独立性必须落在“有标签源恶意质量下限 + 源/目标非对称支持拒绝 + XGBoost 叶/分数锚 + 只用目标前缀的停机回滚”，而非普通 POT/UOT、渐进质量或通用少数类再平衡。第二、第三候选排序不变。
- 停止裁决：第二轮与第三轮均未改变前三名次；第三轮仅收紧第一候选原创边界。直接全文达到 12 篇，安全/异常与域适应理论覆盖达到任务门槛，停止继续扩展检索。

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

### 检查点三：新增全文 8–11

#### 8. EnsV：只用无标签目标预测的域适应模型选择

- 题录：Hao Hu 等，*Towards Reliable Model Selection for Unsupervised Domain Adaptation: A Transferability-Based Approach*，NeurIPS 2024 数据集与基准赛道，DOI `10.52202/079017-4316`。
- 正式来源：https://papers.nips.cc/paper_files/paper/2024/hash/f50cebc22663df45ce619645bfabb3b3-Abstract-Datasets_and_Benchmarks_Track.html；官方源码：https://github.com/LHXXHB/EnsV 。
- 原件：正文 `raw/papers/methodology/2024-Hu-EnsV-Reliable-UDA-Model-Selection.pdf`，21 页，SHA-256 `b862cc17aaa0cfe0c213c8739df8dd52f8883effc6d750ed8ec64f08597cdc76`；补充材料 `raw/papers/methodology/2024-Hu-EnsV-Reliable-UDA-Model-Selection-Supplement.pdf`，8 页，SHA-256 `f62cec09c4381ff483091009820ffe2d72b5a811230d0e1a90539acc78284fa5`。两文件按一篇论文计数。
- 证据等级：正式会议正文和补充材料均已核验；`wiki`/Zotero 待补。
- 理论与方法：命题以负对数似然和预测映射不完全相同为条件，由 Jensen 不等式得到“预测集成损失小于成员平均损失，因而小于最差成员损失”。EnsV 把候选模型在无标签目标样本上的预测集成作为角色模型，再按目标预测相似度选择候选；不需要源数据、目标标签或额外训练。
- 可复用点：适合作为适应候选池的一个停机/回滚证据，并可把共同 XGBoost 强锚纳入候选池，避免选择器只在弱神经模型之间比较。
- 关键限制：理论只保证集成在负对数似然下优于最差成员，不保证所选模型改善 PR-AUC、预算召回或逼近最佳成员；正文明确列出“集成本身次优”“一个好模型被多个坏模型淹没”“模型过于相似”“候选池被差模型支配”等失败条件。低基率二分类中，多数良性预测共识还可能遮蔽恶意排序崩塌。
- 与本任务关系：不能把 EnsV 单独作为安全门禁，必须联合源恶意排序保持、传输未匹配质量、目标前缀扰动稳定性和预测率包络；门禁输出只决定停机/回滚，不能用目标开发标签调参。
- 资源：论文生成候选模型使用单张 16GB RTX TITAN；已有候选预测之后，EnsV 本身仅需目标预测矩阵上的低成本计算，RTX 5090 不是瓶颈。

#### 9. LCA：潜在不变因果机制的时间序列域适应

- 题录：Ruichu Cai 等，*Time Series Domain Adaptation via Latent Invariant Causal Mechanism*，`arXiv:2502.16637`，2025；正式发表于 IEEE TPAMI 2026，DOI `10.1109/TPAMI.2025.3642245`，页 3622–3639。
- 正式/作者来源：https://arxiv.org/abs/2502.16637；官方源码：https://github.com/DMIRLAB-Group/LCA 。
- 原件：`raw/papers/methodology/2025-Cai-LCA-Latent-Causal-Time-Series-Domain-Adaptation.pdf`，19 页，SHA-256 `4eb3d5ce629536eef421514552b13eb6ee353c82aef6d5d0bd78b618f8197fa6`。
- 证据等级：作者公开全文，已核验假设、可辨识性、目标函数、实验和资源；`wiki`/Zotero 待补。
- 理论假设：观测 `x_t=g(z_t)` 来自可逆非线性混合；源/目标潜在条件转移可变，但潜在因果结构满足 `A^S=A^T`。可辨识结论还要求充分历史变化、条件独立、稀疏因果作用及无潜在混杂等条件，结论只到置换与逐分量可逆变换。
- 方法：变分证据下界联合重构与预测；以潜在转移雅可比的 `L1` 范数促进稀疏；阈值化源/目标因果结构后用异或掩码定位不一致边，并以停止梯度的目标结构对齐源结构；总目标由任务、重构、KL、稀疏与结构对齐五项组成。
- 可复用点：提供“只迁移稳定结构而不是所有表征”的理论参照，也可派生为只读诊断：检查 XGBoost 叶/分数在跨年无标签前缀中的条件转移是否满足近似稳定结构。
- 关键限制：上述可逆混合、无混杂、充足历史变化与稳定稀疏结构在 77 个工程字段及非连续流量样本上尚未成立；论文任务为常规时间序列分类/预测，模型选择协议沿用目标验证做法，不能直接迁入严格无标签前缀合同；实验使用 24GB GTX 3090。
- 候选裁决：当前 XGBoost `0.03890259` 明显高于所有小型序列模型，完整 LCA 会以弱神经骨干替换强树锚且训练复杂，因此不进入前三候选。只保留为因果/不变迁移覆盖与失败诊断，不据文献宣称本任务有效。

#### 10. BUOT：样本—类别双层非平衡最优传输

- 题录：Chen 等，*Bi-level Unbalanced Optimal Transport for Partial Domain Adaptation*，`arXiv:2506.08020`，2025；Pattern Recognition 174:112998，2026，DOI `10.1016/j.patcog.2025.112998`。
- 正式来源：ScienceDirect 期刊页与作者公开预印本；截至本轮检索未发现作者正式页指向的可信官方源码，Papers with Code 亦未列实现。
- 原件：`raw/papers/methodology/2025-Chen-BUOT-Bilevel-Unbalanced-Optimal-Transport.pdf`，32 页，SHA-256 `3b54835d81ea6b22cedc23f0e1c8fa59bc2ea7c4b97338f726029b733e48b376`。
- 证据等级：作者公开全文与正式期刊元数据交叉核验，已核验公式、算法、消融和复杂度；`wiki`/Zotero 待补。
- 方法：以样本传输计划 `Γ_1` 与类别传输计划 `Γ_2` 相互引导；非平衡最优传输放松边缘约束，使离群样本获得较小质量；标签感知成本对同类使用预测差异平方、异类使用预测和平方；定理 1 将四阶张量运算化为矩阵乘法，样本与类别更新复杂度分别降为 `O(nK^2)` 和 `O(n^2K)`；恢复的两层边缘形成源权重，联合加权源交叉熵与目标熵训练。
- 同任务缺陷：论文部分域设定是目标标签集合为源标签集合的真子集，目的是丢弃源私有类；其类级权重会伤害目标少数类，样本级预测权重又易受伪标签错误影响。作者用双层耦合缓解两者，但仍以暖启动后的目标伪标签构造标签感知成本。
- 与本任务关系：低基率二分类中，无约束非平衡质量会优先保留廉价良性匹配并丢弃稀有恶意质量，和原任务目标相反。因此候选必须加入源恶意质量下限、支持拒绝松弛、XGBoost 叶/分数强锚与无标签负迁移停机；普通 UOT、BUOT 或双层耦合本身均不是原创。
- 消融参照：论文分别比较仅权重、仅对齐、联合两者，以及普通 OT/UOT、标签感知成本和运行时间，可转化为本任务的“无保护传输—恶意质量保护—保护加停机”递进对照。

#### 11. ContexTDA：面向异常域适应的上下文窗口策略

- 题录：Kwei-Herng Lai 等，*Context-aware Domain Adaptation for Time Series Anomaly Detection*，SDM 2023，页 676–684，DOI `10.1137/1.9781611977653.ch76`，`arXiv:2304.07453`。
- 正式来源：https://epubs.siam.org/doi/10.1137/1.9781611977653.ch76；公开全文：https://arxiv.org/abs/2304.07453 。Papers with Code 截至本轮未列实现，也未发现作者官方源码。
- 原件：`raw/papers/attack-detection/2023-Lai-Context-Aware-Domain-Adaptation-Time-Series-Anomaly.pdf`，13 页，SHA-256 `7619779959bc398433686d65b6d6f2928d67b6a77ec4be05fe3480a648a69dc4`。
- 证据等级：正式会议元数据与公开全文交叉核验，已核验定义、奖励、推断、实验与消融；`wiki`/Zotero 待补。
- 方法：把源/目标 LSTM 编码拼接为马尔可夫决策过程状态，动作是下一时间点两域上下文窗口长度；奖励为源加权分类损失、源/目标重构损失、对齐损失与负号域判别损失的组合倒数；DQN 选择窗口，异常分数为源分类器置信度与目标重构误差乘积。
- 同任务缺陷：论文明确指出普通 MMD/对抗联合在上下文不匹配时会造成异常少数分布负迁移，且随机逐实例选择会破坏时间依赖。这直接支持“不可把普通 DANN/MMD 作为原创”和“少数异常必须单独保护”。
- 关键限制：奖励依赖四个损失及多组超参数，正文调参建议使用源/目标相似性和异常行为相似性等事后信息；评价为宏平均 F1 与 ROC-AUC，不是 PR-AUC/固定预算召回；异常率为 4.1%–15.0%，远高于本任务低基率；使用完整目标序列联合训练而非严格因果前缀；若 LSPR 行不构成连续同实体序列，窗口动作的语义不成立。
- 候选裁决：候选 B 时间机制已经改变输出但显著恶化排序，且所有小型序列模型落后 XGBoost，因此不再提出上下文窗口、时间衰减或强化学习采样主候选。该文只作为异常少数负迁移和目标时序约束的安全边界。

- 检查点状态：第二轮 4 篇全部完成全文核验，正文与补充材料文件合计 5 份但论文计数为 4。至此本任务新增全文为 11 篇；连同已复用的 DANN、Courty OT、BBSE、JCPOT、加权保形、TTA-AD、RTTAD、CANDI、OWAD、SoTTA、FOIL、DIVERSIFY，停止条件中的直接全文数量与安全/异常覆盖均已满足。下一步只进行一轮针对树锚/叶表示传输和稀有排序的窄查重；若不改变前三排序即停止扩展。

### 检查点四：新增全文 12 与检索停止

#### 12. PROTOCOL：不平衡无监督聚类中的渐进部分传输

- 题录：Xuqian Xue、Yiming Lei、Qi Cai、Hongming Shan、Junping Zhang，*PROTOCOL: Partial Optimal Transport-enhanced Contrastive Learning for Imbalanced Multi-view Clustering*，ICML 2025，PMLR 267:70105–70119，`arXiv:2506.12408`。
- 正式来源：https://proceedings.mlr.press/v267/xue25c.html；正式页链接的官方源码：https://github.com/Scarlett125/PROTOCOL ，核验时 HEAD 为 `e17f095b38c81251caccdc4456696060b126882a`。
- 原件：`raw/papers/methodology/2025-Xue-PROTOCOL-Imbalanced-Partial-Optimal-Transport.pdf`，15 页，SHA-256 `06e9a44e413def93ecc0943dd3fbcadde5584dab2a3e01aae5583741a092b1fa`。
- 证据等级：PMLR 正式全文，已核验目标、公式、算法、消融和官方源码；`wiki`/Zotero 待补。
- 方法：在无监督多视图聚类中，以部分传输自标注矩阵 `T` 连接样本与潜在簇；目标由预测负对数代价、类别边缘加权 KL 和总传输质量组成。传输质量 `λ` 以 S 形日程从高置信样本逐渐扩到困难样本；未分配质量由虚拟簇吸收，采用熵正则缩放算法求解。
- 第二机制：POT 伪标签进一步驱动特征级对数几率调整和类别级类别敏感对比学习，显式提高尾类在成对学习和优化中的权重。表 5 分离 Base、POT、自标注加类别再平衡；正文还按头/中/尾类报告聚类结果。
- 原创边界：该文说明“部分传输 + 渐进质量约束 + 非平衡类别边缘 + 少数类再平衡”已有正式先例。候选一不能把这些宽泛构件作为原创，只能主张任务特定的源恶意真标签质量下限、跨年源/目标非对称支持拒绝、固定 XGBoost 强排序锚与无标签负迁移停机组合。
- 不可直接迁移：论文没有源—目标域、有标签源恶意类、攻击污染或因果前缀；以视觉多视图聚类的 ACC/NMI/Purity 评价；渐进日程按训练进度而非支持证据增加质量，可能把错误目标伪簇逐步纳入。完整网络需 200 轮重构预训练、50–100 轮一致性与 50–100 轮不平衡学习，和本任务优先在固定树叶表示上做小规模传输不同。
- 候选关系：不改变第一候选排名，但新增硬消融：普通 POT、渐进 POT、带源恶意质量下限的非对称 POT，以及后者加停机；若渐进 POT 已达到同等增益，则本任务的恶意质量保护机制未获独立支持。

- 检查点状态：新增 12 篇直接全文全部核验完成；检查点按 4、3、4、1 篇落盘，最后 1 篇是停止前窄查重揭示的原创边界材料。检索停止，转入 `wiki`、索引、Zotero、参考书目与候选文档闭合。

## 证据链闭合记录

### `raw → wiki → 索引`

- 12 篇全文均有原件与结构化笔记；EnsV 补充材料合并到正文笔记，不重复计篇。
- 方法论文笔记 10 篇写入 `wiki/papers/methodology/`，安全/异常论文笔记 2 篇写入 `wiki/papers/attack-detection/`。
- 方法索引、攻击检测索引与外部资源索引均已追加；7 个官方源码仓库记录精确 HEAD、许可证状态、依赖/复现风险与本课题边界。
- 参考书目写入 `.Codex/docs/RWKV/2026-08-12-跨年度迁移学习候选方案调研/references.bib`，共 12 条。

### Zotero 去重、导入与键

- 导入前以 12 个完整题名逐条查询，均无命中；随后通过 Zotero Connector 一次性导入 12 条，并再次逐题名查询确认每篇唯一命中。
- RAINCOAT `RVX6ZR6X`；ACON `7JVIMR49`；标签对齐正则 `BNQVGJ6Q`；迁移分数 `G322Z8X6`。
- PPOT `X4FIBAVC`；WARMPOT `3NCT6JX8`；DI-NIDS `UCJ2SKNL`；EnsV `AR53AZ34`。
- LCA `P7VT37J7`；BUOT `LHAIR4ZV`；ContexTDA `EU4B756L`；PROTOCOL `GL8RQF4U`。
- 导入目标是 Zotero 根文库；当前 CLI 没有把已有条目移入指定集合的安全接口，因此未伪称已进入 `RWKV-跨年度理论融合-20260811` 集合。条目与键已经闭合，集合归类作为非阻断性人工整理项。

## 综合发现

待阶段五填写。

## 未关闭疑点

1. LSPR24 前缀恶意污染率是否足以破坏熵最小化、批归一化统计或伪标签自训练？
2. 目标年度类先验变化与类条件分布变化能否被仅无标签前缀可靠区分？
3. 共同 77 字段在两年度是否存在局部支持不重叠，导致全局 DANN/CORAL/MMD/OT 强行对齐？
4. 固定告警预算下的阈值失效主要来自排序退化、先验变化还是概率校准漂移？
5. 哪些机制与候选 B 的角色分离物理时间状态、C12 的目标状态更新与双参照空间重叠？

## 下一检查点

### 2026-08-12 中断恢复检查点（已被检查点三取代）

- 已完成：规则与路线恢复；本地综述/C12 邻近工作/Zotero 盘点；两轮联网检索；7 篇新增全文逐篇核验；两次按 3–4 篇落盘的检查点；7 个原件哈希核验。
- 已验收原件：RAINCOAT、ACON、标签对齐正则、迁移分数、原型部分最优传输、WARMPOT、DI-NIDS，精确路径和 SHA-256 见上文各条。
- 已复用核心全文但尚未在本任务中重新逐条计数：DANN、Courty 最优传输、BBSE、JCPOT、加权保形、TTA-AD、RTTAD、CANDI、OWAD、SoTTA、FOIL、DIVERSIFY，以及既有 C12 近邻核验中的相关原件/笔记。
- 未完成：第二轮命中全文核验；7 篇 `wiki/papers` 结构化笔记；`raw/papers/INDEX.md` 与 `wiki/papers/INDEX.md` 最小追加；官方源码资源笔记；Zotero 导入及键回填；`references.bib`；主综述；候选总览；3–5 个候选详案与快速消融；停止条件复核。
- 未公开全文：ReCDA（KDD 2024，DOI `10.1145/3637528.3672007`）及其 IEEE TDSC 2025 扩展（DOI `10.1109/TDSC.2025.3599321`）。两者只有正式元数据/摘要，不计全文，不支持方法细节论断。
- 唯一续接入口：先读取本文件与 `task_plan.md`，随后从第二轮四个精确查询命中的正式全文去重开始；优先核验 NeurIPS 2024 无标签选模与 2025/2026 潜在因果机制，再决定候选排序。
- 当前候选只可视为方向草案：①稀有恶意质量保护的非对称部分传输 + 负迁移停机；②恶意方向保留的目标谱分类头校正 + 标签移位/预算校准；③污染隔离的因果前缀/状态适应 + 源排序锚。全部状态均为“实验待证”，名称、公式与排序尚未冻结。
