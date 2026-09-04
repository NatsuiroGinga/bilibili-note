# 第四章机制一：EAS 的家族谱系（安全筛除／梯度稀疏）

**用途**：为 [第四章机制一-EAS 空活动集短路](第四章机制一-EAS空活动集短路.md) 建立可引用的家族谱系，
并对抗性检验其新颖性主张。**本文件只做文献定位，不裁决 EAS 的存废**——那须由该文档第八节的实验判据决定。

- 日期：2026-09-04
- 调研记录：`.Codex/docs/RWKV/2026-09-04-EAS家族谱系调研/task_plan.md`
- 检索路径：本地混合索引 → Zotero（**不可用，见 §3.5**）→ arXiv API／OpenAlex → 全文入库

> **与同日对抗性审核的关系**（`.Codex/docs/RWKV/2026-09-04-EAS方案对抗性审核.md`）：
> 该审核以实测推翻了 EAS 文档 §1 的若干事实主张（活动率单调性等）。
> **本文件不引用 EAS 文档的任何实测数字**，结论只依赖外部文献，故不受那些修订影响。
> 本文件 §3.2 的判断（去掉对偶后无已知手段给出前向前证书）与该审核 B6
> 「给不出 `ε(Δθ)` 真上界的证明则删除 EAS-full」**方向一致且相互独立**——
> 一条来自文献缺位，一条来自预算实测。**两者同时指向 EAS-full 而非 EAS-lite。**

## 证据等级约定

| 标记 | 含义 |
| --- | --- |
| `本地全文` | `raw/` 有原件、`wiki/` 有全文笔记或 MinerU 全文转换，页码／小节可核 |
| `在线全文已下载` | 本轮下载并转换，已入库（等同于 `本地全文`，此处不再单列） |
| `在线摘要` | 只核验了 arXiv／OpenAlex 题录与摘要，**未取全文** |
| `仅题录` | 只核验了题名、作者、标识符 |

**本轮六条主线全部达到 `本地全文`。** 补充条目多为 `在线摘要`，已逐条标注。

---

## 一、谱系总览

时间线分三段：**凸问题的可证明精确筛除** → **深度网络的近似梯度稀疏** → **深度网络的精确零梯度剔除**。

| 年份 | 作者 | 简称 | 筛掉什么 | 可证明精确 | 证据等级 | 与 EAS 的关系 |
| --- | --- | --- | --- | --- | --- | --- |
| 2010／2011 | El Ghaoui, Viallon, Rabbani | **SAFE** | **特征**（LASSO 的 `w_k`） | **是**（对偶可行域论证） | `本地全文` | 家族开山。判据范式同构；凸性与对偶间隙不可迁移 |
| 2013／2014 | Ogawa, Suzuki, Suzumura, Takeuchi | **Ball／Intersection Test** | **样本**（非支持向量） | **是**（球形可行域） | `本地全文` | 从特征稀疏迁到样本稀疏，与 EAS 的「跳过候选」同维；仍是凸对偶 |
| 2016 | Shibagaki, Karasuyama, Hatano, Takeuchi | 双稀疏同时筛除 | 特征 ＋ 样本 | 是（对偶间隙） | `在线摘要` | 证明特征与样本可同时筛；EAS 只筛步与袋，不筛参数 |
| 2016 | Ndiaye, Fercoq, Gramfort, Salmon | **GAP Safe rules** | 特征（稀疏正则族） | 是（对偶间隙收敛） | `在线摘要` | 边界随迭代收紧，与 EAS「每 `K` 步刷新上界」的动机相近 |
| 2020 | Mialon, d'Aspremont, Mairal | **椭球 ERM 筛除** | **数据点**（ERM 样本） | **是**（椭球可行域） | `本地全文` | 家族最一般的凸形式；**明确不要求强凸**，但仍要求凸与对偶稀疏 |
| 2017 | Sun, Ren, Ma, Wang | **meProp** | **梯度坐标**（top-`k`） | **否**（显式近似） | `本地全文` | 深度网络、有收益，但是**启发式**。EAS 的「可靠性」优势正是相对它成立 |
| 2023 | Nikdan, Pegolotti, Iofinova, Kurtic, Alistarh | **SparseProp** | **权重结构零**（既有掩码） | 是（但**不做筛除判定**） | `本地全文` | 证明稀疏反传能拿到真实墙钟收益；稀疏性是**给定**的，不是**推出**的 |
| 2023 | Schultheis, Babbar | **隐式负例挖掘** | **负标签**（平方合页零梯度） | **是**（逐点数学精确） | `本地全文` | **最近的先例**。同为深度网络＋精确零＋时间收益；零的来源与粒度不同 |
| — | 本课题 | **EAS-lite** | **整步**（`|A| = 0` 时的反传） | 是（平凡） | 待验证 | 与 Schultheis 同格，但判据在**步级**而非标签级 |
| — | 本课题 | **EAS-full** | **整步的前向 ＋ 反传** | **未证明** | 待验证 | **谱系中的空格**，详见 §3 |

**读表要点**：前五行的「精确」全部来自**凸问题的对偶结构**（最优解落在已知可行域内）；
后三行的「精确」只能来自**损失函数的逐点性质**（某区间导数恒为零）。
深度网络里没有可用的对偶间隙，**这条分界线决定了 EAS-full 能不能成立**（§3.2）。

---

## 二、逐条详述

### 2.1 El Ghaoui, Viallon & Rabbani —— SAFE（家族开山）

- **题录**：El Ghaoui L, Viallon V, Rabbani T. Safe Feature Elimination for the LASSO and Sparse
  Supervised Learning Problems. arXiv:1009.4219v2, 2010（v1 2010-09-21，v2 2011-05-18；
  arXiv 注记 “Submitted to JMLR in April 2011”）。
  **该文另有期刊发表版本的说法未经本轮核验，引用时只写 arXiv 标识。**
- **证据等级**：`本地全文`（原件 `raw/papers/methodology/training-efficiency/2011-ElGhaoui-Safe-Feature-Elimination-LASSO.pdf`，
  `sha256:898c364d…`；全文转换见同名 `-全文.md`）
- **机制内核**：筛掉的是**特征**。LASSO 最优性条件为 `|θ*ᵀx_k| < λ ⟹ (w*)_k = 0`。
  把不可知的对偶最优点 `θ*` 换成一个**已知包含它的集合 `Θ`**，若 `max_{θ∈Θ}|θᵀx_k| < λ` 对整个 `Θ` 成立，
  则该特征在最优解处必为零（§2.2 基本思想，§2.4 SAFE-LASSO 定理）。
  `Θ = Θ₁ ∩ Θ₂`：`Θ₁` 由对偶目标下界 `γ`（式 4）给出，`Θ₂` 由 `λ₀` 处的一阶最优性条件给出；
  该最大化问题有闭式解（附录 A）。
- **可证明精确**：**是**。原文措辞：只剔除「保证在求解完整问题后必然缺席」的特征（摘要、§1）。
  代价「大致等于一次梯度步」（摘要）。§4 推广到一般 `ℓ₁` 正则凸问题，§4.4 稀疏 SVM，§4.5 稀疏逻辑回归。
- **与 EAS 的关系**
  - **同构点**：判据范式完全一致——*把未知最优解圈进一个已知区域，再用该区域上的最值给出确定性充分条件*。
    EAS-full §3.2 的「负例分数全局上界 `Ŝ_n`」正是这个范式在分数空间的实例。
    「保守取值只损失收益、不损害正确性」这一性质也共享。
  - **不可迁移点**：SAFE 全部依赖 **LASSO 对偶问题的凸性、强对偶与解的唯一性**。
    `Θ₁` 的构造直接用了对偶目标值的下界，这在深度网络中**没有对应物**。
    EAS 的排序损失非凸、参数化为神经网络、无解析可行域，**必须另起炉灶推导**，
    不能套用式 (4)–(6) 的任何一条。

### 2.2 Ogawa, Suzuki, Suzumura & Takeuchi —— SVM 安全样本筛选

- **题录**：Ogawa K, Suzuki Y, Suzumura S, Takeuchi I. Safe Sample Screening for Support Vector
  Machines. arXiv:1401.6740, 2014（扩展自 Ogawa K, Suzuki Y, Takeuchi I. Safe screening of
  non-support vectors in pathwise SVM computation. ICML 2013）。
- **证据等级**：`本地全文`（**入库在先**，原件与结构化全文笔记均已存在，本轮未重复下载）
  - 全文笔记：`wiki/papers/methodology/training-efficiency/2014-Ogawa-SVM安全样本筛选.md`
  - MinerU 全文：同目录 `2014-Ogawa-Safe-Sample-Screening-SVM-全文.md`
- **机制内核**：筛掉的是**样本**。构造一个已知含 `w*` 的球 `Θ`（中心 `m`、半径 `r`），
  则 `y_i f(x_i)` 有闭式上下界 `ℓ = z_iᵀm − r‖z_i‖`、`u = z_iᵀm + r‖z_i‖`（Lemma 1）。
  `ℓ > 1` 则该样本必为非支持向量（`α* = 0`），`u < 1` 则必有 `α* = C`。
  三条必要条件 NC1–NC3 组合成 Ball Test 1／2，取交集得 Intersection Test（Theorem 8）。
- **可证明精确**：**是**，且原文把它与 LIBSVM 的 `shrinking` 启发式明确对立——
  后者的预测步「不安全」，可能误判支持向量因而必须回查（§I、§V-C）。
- **关键页码**：Lemma 1 见 §III-B；Theorem 8 见 §III-D；耗时表 Table III 在印刷第 9 页，
  Intersection Test 筛选率 `0.51 / 0.125 / 0.136 / 0.139`；
  §I 的「接近 `90%`」是定性描述，**不是实测典型值**，引用须区分。
- **与 EAS 的关系**
  - **同构点**：EAS 空活动集短路文档 §2.2 已将本条列为直接对位——都是「先给最优解划可行域，
    再推出某些候选必不活动」。**「可靠但不必完备」这一设计取舍两者一致**。
  - **不可迁移点**：本文的界建立在 SVM 对偶的 KKT 划分（`R`／`E`／`L`）上，`w*` 唯一且问题凸。
    EAS 的活动集由**成对违序关系**定义，不是单样本的 KKT 归属；
    且 EAS 的负实体池每步重新分层抽样（该文档 §3.3 障碍 1），
    **Ogawa 的「样本固定、参考解已知」前提在本课题不成立**。

### 2.3 Mialon, d'Aspremont & Mairal —— ERM 椭球区域安全筛选

- **题录**：Mialon G, d'Aspremont A, Mairal J. Screening Data Points in Empirical Risk Minimization
  via Ellipsoidal Regions and Safe Loss Functions. arXiv:1912.02566v3, 2020；AISTATS 2020
  （venue 来自 arXiv comment 字段）。
- **证据等级**：`本地全文`（本轮下载并转换，原件
  `raw/papers/methodology/training-efficiency/2020-Mialon-Screening-Data-Points-ERM-Ellipsoidal-AISTATS.pdf`，
  `sha256:9652cfd2…`）
- **机制内核**：筛掉的是 **ERM 中的数据点**。两个部件：
  1. **安全损失函数**（Definition 2.3）——损失须有一段**平坦区间** `T`，使对偶解稀疏；
     §4 给出把一般凸损失正则化成安全损失的方法（如 safe logistic）。
  2. **椭球测试域**（§3.2，Algorithm 1）——用椭球法迭代逼近最优解所在区域，
     椭球上的线性最值有闭式解（Lemma 3.3），再加一条次梯度线性约束把椭球「切掉约一半」。
  筛除总代价 `O(npk)`，相对不筛除的 `O(npT)`（`T ≫ k`）。
- **可证明精确**：**是**，且**不要求强凸**——这是它相对 Shibagaki 等对偶间隙方法的一般性优势（§5.1 分类段）。
- **关键数字**：Table 1（`ℓ₁` safe logistic 的筛除百分比，随初始化 epoch 与 `λ` 变化，
  MNIST 在 `λ = 10⁻⁵`、30 epoch 下达 `65%`）；Table 2（`ℓ₂` 平方合页，椭球／对偶间隙对照，
  MNIST `λ = 1.0` 为 `89 / 89`）。作者自陈：筛除只有在求解器已到达较好迭代点后才启动，
  故**最适合正则化路径或计算预算宽松的场景**（§5.1 末）。
- **与 EAS 的关系**
  - **同构点**：这是家族里**最接近 EAS 抽象形式**的一条——它不要求特定模型（SVM／LASSO），
    只要求「凸 ＋ 损失有平坦区」。**BER 的 CVaR-pAUC 合页型损失确实有平坦区**（违序为零处），
    这是 EAS 得以自称本家族的最强形式依据。
  - **不可迁移点**：`x ∈ ℝᵖ` 是**线性模型参数**，椭球法在参数空间上迭代，
    复杂度 `O(p² log(RL/ε))`，作者自陈「对高维问题不实用」。
    深度网络的 `p` 是百万级，**椭球路线在本课题算术上直接不可行**。
    且椭球初始化需要目标函数的强凸常数或对偶间隙上界，两者本课题都没有。

### 2.4 Sun, Ren, Ma & Wang —— meProp（启发式对照）

- **题录**：Sun X, Ren X, Ma S, Wang H. meProp: Sparsified Back Propagation for Accelerated Deep
  Learning with Reduced Overfitting. ICML 2017；arXiv:1706.06197v5。
- **证据等级**：`本地全文`（本轮下载并转换，`sha256:7ff1eb81…`）
- **机制内核**：筛掉的是**梯度坐标**。前向照常；反传时只保留输出梯度向量中**幅值最大的 top-`k`** 个分量，
  其余置零（§2.1）。因而只有 `k` 行／列权重被更新，计算量线性下降。
  多隐层时每层输出都要重做 top-`k`（§2.2.1），选择用最小堆，`O(n log k)`（§2.2.2）。
- **可证明精确**：**否，且作者明说是近似**——原文反复使用 “approximate gradient”（§2.1、§2.2）。
  没有任何充分条件保证被丢弃的分量真为零。
- **关键数字**：只更新 `1–4%` 的权重而不增加迭代次数，**准确率反而略升**（作者归因于类 dropout 的正则效应，摘要、§4.2）。
  GPU 合成矩阵乘（§4.8 Table 7，`h = 8192`，batch 1024）：基线反传 `308.00 ms`，
  `k = 8` 时 `8.37 ms`（`36.8×`）；MNIST 大隐层（Table 8）整体反传 `17,696.2 ms → 1,501.5 ms`（`11.8×`）。
- **与 EAS 的关系**
  - **同构点**：同在深度网络里削减反传，且证明了「反传稀疏化能拿到真实 GPU 墙钟收益」。
  - **不可迁移点／对照价值**：**这是 EAS 必须区分开的反例。** meProp 的收益以**改变梯度**为代价，
    需要经验验证不掉点；EAS-lite 的跳过是**逐位精确**的加零，不需要任何精度论证。
    EAS 空活动集短路文档 §3.1 所称「相对启发式加速方法的结构性优势」，
    **对位的正是 meProp 与 Selective-Backprop 这一支**。
  - **一条反向警示**：meProp 的准确率不降反升说明——在深度网络里，
    「精确」并不天然优于「近似」。**EAS 的卖点必须落在「无需精度论证」的工程确定性上，
    不能落在「比近似方法更准」上**，后者 meProp 的数据不支持。

### 2.5 Nikdan et al. —— SparseProp（系统侧可行性证据）

- **题录**：Nikdan M, Pegolotti T, Iofinova E, Kurtic E, Alistarh D. SparseProp: Efficient Sparse
  Backpropagation for Faster Training of Neural Networks. arXiv:2302.04852v1, 2023。
  **arXiv 元数据无 `journal_ref`；会议归属未核验，引用时只写 arXiv 标识。**
- **证据等级**：`本地全文`（本轮下载并转换，`sha256:7b280f1b…`）
- **机制内核**：筛掉的是**权重矩阵中的结构零**。给定一个**已经稀疏**的网络（掩码由剪枝／稀疏训练给出），
  提供复杂度**与层密度成线性**的反传实现，支持任意非结构化稀疏与线性／卷积层（§3.2、§3.3），
  用 AVX2 在通用 CPU 上向量化。
- **可证明精确**：实现层面精确（它计算的就是该稀疏模型的真实梯度），
  但**它不做任何筛除判定**——稀疏性是输入，不是推论。**严格说它不属于 safe screening，属于稀疏反传的系统支持。**
- **关键数字**：稀疏迁移端到端最高 `1.85×`；只计反向算子时在 `95%` 稀疏度下 `3.6×`；
  从零稀疏训练端到端最高 `1.4×`（§1 贡献段、§4.2）。**平台是 CPU，不是 GPU。**
- **与 EAS 的关系**
  - **同构点**：为 EAS 提供**系统侧可行性论据**——稀疏反传的理论节省确实能落成墙钟收益。
  - **不可迁移点**：SparseProp 的稀疏是**静态掩码**（每次前向反向固定）；
    EAS 的活动集**逐步动态变化**，且判定发生在运行时。
    其 CPU／AVX2 实现路径与本课题的 CUDA 场景不通用。
  - **与 Schultheis 的一条共同警告**：二者都说明收益必须在**算子内部**取得。
    EAS 空活动集短路文档 §6 已据此解释候选一 ASB「逐位不变但无收益」——本条是该解释的第二个外部支撑。

### 2.6 Schultheis & Babbar —— 隐式负例挖掘（最近的先例）

- **题录**：Schultheis E, Babbar R. Towards Memory-Efficient Training for Extremely Large Output
  Spaces —— Learning with 500k Labels on a Single Commodity GPU. arXiv:2306.03725, 2023；
  DOI `10.1007/978-3-031-43418-1_41`（该 DOI 出现在 arXiv 元数据中，本轮已核验；
  对应 ECML PKDD 2023，**出版方页面未独立核验**）。
- **证据等级**：`本地全文`（**入库在先**，全文笔记
  `wiki/papers/methodology/training-efficiency/2023-Schultheis-隐式负例挖掘跳过零梯度反传.md`）
- **机制内核**：筛掉的是**负标签的反传**。平方合页损失 `ℓ(y,ŷ) = max(0, 1 − yŷ)²` 的导数
  `∂ℓ/∂ŷ = −2y·max(0, 1 − yŷ)`，**在 `yŷ ≥ 1` 时精确为零**（§3.3 原文：“exactly zero whenever `yŷ ≥ 1`”），
  据此整片跳过反传。配自定义 CUDA 实现。
- **可证明精确**：**是**，数学精确而非近似。但**零的来源是逐点损失的平坦区，不是可行域论证**——
  这一点与 §2.1–2.3 的凸分支有本质区别。
- **关键数字**：§4.4 表 4，SQH 对 BCE 同架构同稀疏度，每轮时间「降约三分之一」。
- **两条对 EAS 的硬约束**（EAS 空活动集短路文档 §6 已采纳，此处确认无误）
  1. 作者自陈**仍需完整前向**——所以「只跳反传」有天花板，这正是 EAS 必须做到 full 档的理由。
  2. **框架层乘零掩码不省任何事**，收益须在反向 kernel 内部跳过内存查找。
- **与 EAS 的关系**
  - **同构点**：深度网络 ＋ 精确零梯度 ＋ 真实时间收益，三项俱全。
    **「首次在深度网络里做可证明精确的反传剔除」这一主张因此不成立**，
    EAS 空活动集短路文档 §6 的收窄是正确的，本轮独立复核确认。
  - **不可迁移点**：其零来自**逐点 margin 损失、标签维度**；
    EAS 的零来自**成对／CVaR-pAUC 排序损失、实体袋维度**。
    逐点损失的零可以对每个标签独立判定；成对损失的零是**整个候选对集合的联合性质**，
    判据须独立推导，不能由 §3.3 的一行导数得到。

### 2.7 补充条目（`在线摘要`，未取全文）

这些不构成 EAS 的直接对位，但界定了凸分支的成熟度，说明该分支已被充分开垦。

| 条目 | 标识 | 一句话 | 等级 |
| --- | --- | --- | --- |
| Bonnefoy 等，动态筛除 | arXiv:1412.4080（2014） | 一阶算法迭代过程中反复收紧筛除边界，非一次性判定 | `在线摘要` |
| Shibagaki 等，双稀疏同时筛除 | arXiv:1602.02485（2016） | 首次把特征筛除与样本筛除合并；依赖对偶间隙与强凸 | `在线摘要` |
| Ndiaye 等，GAP Safe rules | arXiv:1611.05780（2016） | 用对偶间隙构造安全区域，随迭代收敛而收紧 | `在线摘要` |
| Narasimhan & Agarwal，pAUC 支持向量算法 | arXiv:1605.04337（2016） | **pAUC 的凸代理 ＋ 割平面求解**，见 §3.3 的专门讨论 | `在线摘要` |

**这四条均未下载全文，不得用于支撑正文论断或候选存废裁决。**

---

## 三、家族线的空白：EAS 落在哪里，谁已经占了这个位置

### 3.1 把谱系拆成两个轴

家族的真实结构不是一条时间线，而是**两个轴的交叉**：

- **横轴：证书从哪里来。** `对偶可行域`（凸分支）／ `逐点损失平坦区`（深度分支）／ `外部给定`（SparseProp）／ `无证书`（meProp）
- **纵轴：在计算的哪个位置生效。** `求解前`（凸分支，一次判定）／ `前向后反传前`（Schultheis、EAS-lite）／ `前向前`（**EAS-full**）

填进已知工作：

| | 求解／前向**之前** | 前向后、反传前 | 无位置（改梯度） |
| --- | --- | --- | --- |
| **对偶可行域证书** | El Ghaoui、Ogawa、Mialon、GAP、Shibagaki | —— | —— |
| **逐点损失平坦区** | —— | **Schultheis** | —— |
| **成对／排序损失** | **← EAS-full 主张落此** | **← EAS-lite 落此** | —— |
| **无证书（启发式）** | —— | Selective-Backprop | meProp |

**两个格子是空的**：「成对／排序损失 × 前向前」与「成对／排序损失 × 前向后」。
EAS-lite 占后者，EAS-full 主张占前者。

### 3.2 空格为什么空——**这是对 EAS 最不利的一条发现**

凸分支能做到「求解前判定」，**唯一原因是有对偶**：最优解的可行域可以由对偶目标值、对偶间隙或 KKT 条件圈出来。
深度分支**没有对偶可用**，所以 Schultheis 只能退到「前向之后」——他自陈仍需完整前向，
**这不是他偷懒，是他没有别的选择**。

于是 EAS-full 面对的是一个**结构性问题而非疏漏**：

> 谱系中「深度网络 × 前向前」这个格子是空的，不是因为没人想到，
> 而是因为**去掉对偶之后，没有已知手段在付出前向之前圈定分数的范围**。

EAS 空活动集短路文档 §3.3 已经自行识别出这一点的具体形态（需要 Transformer 对参数的 Lipschitz 常数，
无紧估计，界会很松，可能退化为 lite 加额外开销）。**本轮文献调研的结论与该自我判断一致，且更强**：
整个家族没有任何一条工作提供过绕开对偶的前向前证书，**EAS-full 没有可借用的技术先例**。

**这既是新颖性的来源，也是失败风险的来源，两者是同一件事。**
文档 §3.3 把该路线的最小证伪实验列为待办是恰当的；在该实验出结果前，
**不得把「谱系空白」表述为「本方法填补了空白」**——空白目前只是空白。

### 3.3 对抗性检索：有没有人已经对排序／成对损失做过安全筛除

按任务要求，专门检索是否存在 pairwise／ranking loss 的安全筛除工作。**结论：未检索到。**

**检索式与结果**（arXiv API，`all:` 字段覆盖题名／摘要／注记，**不含全文**；2026-09-04 执行）

| 检索式 | 结果 |
| --- | --- |
| `"safe screening" AND ranking` | **零命中** |
| `"safe screening" AND AUC` | **零命中** |
| `"safe screening" AND pairwise` | **零命中** |
| `"safe screening" AND "neural network"` | **零命中** |
| `"safe screening" AND "multiple instance"` | **零命中** |
| `"active set" AND "pairwise ranking"` | **零命中** |
| `"RankSVM" AND screening` | 1 条，为药物虚拟筛选，无关 |
| `screening AND pairwise AND hinge` | 1 条，为 arXiv:1605.04337，见下 |

**零命中的可信度**：同一接口的对照检索 `"safe screening" AND lasso` 返回 14 条正确结果
（GAP Safe、Celer、Hybrid safe-strong 等），`"safe screening"` 单独检索返回 15 条正确结果，
**证明检索式与 AND 运算符工作正常，零命中是真实的负结果**。
但须注意两条边界：**该字段不含论文全文**，且**只覆盖 arXiv**；
OpenAlex 上同类查询被生物医学的 “screening” 淹没，未能提供有效补充。
故本结论的准确表述是：**在 arXiv 题名／摘要一级，未见任何将安全筛除用于排序或成对损失的工作。**

**唯一需要单独处理的近邻**：arXiv:1605.04337，Narasimhan & Agarwal，
*Support Vector Algorithms for Optimizing the Partial Area Under the ROC Curve*。

- 它命中检索**是因为摘要里的 “biometric screening”**，与 safe screening 无关（`在线摘要`级核验）。
- 但它在**目标函数**上是 BER 的凸祖先：直接优化两个 FPR 之间的 **partial AUC**，
  用 Joachims 结构化 SVM 框架构造凸代理，**割平面法求解**。
- **割平面法确实维护一个约束活动集**，这是家族外最接近「排序损失 ＋ 活动集」的结构。
  但割平面的保证是「收敛到 `ε` 最优」，**不是「证明某约束永不活动」**——
  它是求解器策略，不是安全筛除。**因此不构成 EAS 的先例，但构成一条必须在正文中主动区分的近邻。**
- **建议**：若第四章正文要声称「排序损失上的安全筛除尚无先例」，
  应当先取得该文全文并确认其割平面实现的活动集语义，否则该主张有被审稿人用这篇反驳的风险。
  **本轮未下载其全文，该建议标为待办。**

### 3.4 新颖性主张的可用表述与不可用表述

| 判定 | 表述 |
| --- | --- |
| **不成立** | 「首次在深度网络里做可证明精确的反传剔除」——Schultheis 已做（§2.6） |
| **不成立** | 「首个利用损失平坦区跳过计算的方法」——Mialon 的安全损失、Schultheis 均已做 |
| **不成立** | 「首次证明稀疏反传能带来真实墙钟收益」——meProp、SparseProp、Schultheis 均已报告 |
| **目前成立，但仅在 arXiv 摘要级证据下** | 「安全筛除此前未被用于成对／CVaR-pAUC 排序损失」（§3.3） |
| **目前成立，且有结构性理由** | 「深度网络中的精确剔除此前均须完整前向；前向前证书无先例」（§3.2） |
| **禁止使用** | 「首次」「首个」——EAS 空活动集短路文档 §6 已冻结该措辞禁令，本轮确认应继续执行 |

**最稳的一句**（同时满足证据充分与不越界）：

> 已有的精确剔除工作要么依赖凸问题的对偶结构，要么依赖逐点损失的平坦区并因此必须付出完整前向；
> 本机制的判据建立在成对排序损失的联合性质上，其可行性由本章实验判定。

**该句不含「首次」，不声称填补空白，且每个分句都能指向本文件的具体条目。**

### 3.5 检索过程中的两个缺口（如实登记）

1. **Zotero 语义检索不可用。** 本轮调用 `zotero_semantic_search` 与 `zotero_search_items`
   均返回 `[Errno 61] Connection refused`（Zotero 桌面端本地 API 未运行）。
   语义索引返回了 15 个 item key 但无法取回任何元数据，相似度全为负值。
   **因此「本地 Zotero 是否已收录这些条目」未能核实**，本轮改以仓库 `raw/`／`wiki/` 与
   本地混合索引去重，四篇新入库论文经 `fd`／目录列举确认此前不在库。
2. **本地混合索引 `stale = true`**（`stale_reasons: source_added, source_changed`）。
   索引存在（`140,184` 向量，`vector_dimension = 384`，`mps:0`），
   查询正常返回且 Ogawa 稳定排首位，但**索引未包含本轮新增的四篇全文**。
   本轮结论不依赖索引的完备性——四篇新论文的证据直接来自 MinerU 全文，不来自索引检索。

---

## 四、可直接引用的参考文献表

**入库状态**：`✔` 表示 `raw/` 有原件且 `wiki/` 有全文；`○` 表示仅在线摘要核验，**不得支撑正文论断**。

### 4.1 GB/T 7714 格式

- `✔` [1] EL GHAOUI L, VIALLON V, RABBANI T. Safe feature elimination for the LASSO and sparse
  supervised learning problems[EB/OL]. arXiv:1009.4219, 2010.
- `✔` [2] OGAWA K, SUZUKI Y, SUZUMURA S, 等. Safe sample screening for support vector
  machines[EB/OL]. arXiv:1401.6740, 2014.
- `✔` [3] OGAWA K, SUZUKI Y, TAKEUCHI I. Safe screening of non-support vectors in pathwise SVM
  computation[C]//Proceedings of the 30th International Conference on Machine Learning (ICML).
  2013.（[2] 的会议前身，题录转引自 [2] 附录 B 与参考文献第 22 号，**未取原件**）
- `✔` [4] MIALON G, D'ASPREMONT A, MAIRAL J. Screening data points in empirical risk minimization
  via ellipsoidal regions and safe loss functions[C]//Proceedings of the 23rd International
  Conference on Artificial Intelligence and Statistics (AISTATS). 2020. arXiv:1912.02566.
- `✔` [5] SUN X, REN X, MA S, 等. meProp: sparsified back propagation for accelerated deep learning
  with reduced overfitting[C]//Proceedings of the 34th International Conference on Machine
  Learning (ICML). 2017. arXiv:1706.06197.
- `✔` [6] NIKDAN M, PEGOLOTTI T, IOFINOVA E, 等. SparseProp: efficient sparse backpropagation for
  faster training of neural networks[EB/OL]. arXiv:2302.04852, 2023.
- `✔` [7] SCHULTHEIS E, BABBAR R. Towards memory-efficient training for extremely large output
  spaces: learning with 500k labels on a single commodity GPU[C]//Machine Learning and Knowledge
  Discovery in Databases (ECML PKDD). 2023. DOI: 10.1007/978-3-031-43418-1_41. arXiv:2306.03725.
- `✔` [8] JIANG A H, WONG D L K, ZHOU G, 等. Accelerating deep learning by focusing on the biggest
  losers[EB/OL]. arXiv:1910.00762, 2019.（启发式对照，已入库）
- `○` [9] BONNEFOY A, EMIYA V, RALAIVOLA L, 等. Dynamic screening: accelerating first-order
  algorithms for the Lasso and group-Lasso[EB/OL]. arXiv:1412.4080, 2014.
- `○` [10] SHIBAGAKI A, KARASUYAMA M, HATANO K, 等. Simultaneous safe screening of features and
  samples in doubly sparse modeling[EB/OL]. arXiv:1602.02485, 2016.
- `○` [11] NDIAYE E, FERCOQ O, GRAMFORT A, 等. Gap safe screening rules for sparsity enforcing
  penalties[EB/OL]. arXiv:1611.05780, 2016.
- `○` [12] NARASIMHAN H, AGARWAL S. Support vector algorithms for optimizing the partial area under
  the ROC curve[EB/OL]. arXiv:1605.04337, 2016.（**近邻，须取全文后再决定是否引用**，见 §3.3）

### 4.2 BibTeX

```bibtex
@article{elghaoui2010safe,
  title  = {Safe Feature Elimination for the {LASSO} and Sparse Supervised Learning Problems},
  author = {El Ghaoui, Laurent and Viallon, Vivian and Rabbani, Tarek},
  journal= {arXiv preprint arXiv:1009.4219},
  year   = {2010}
}
@article{ogawa2014safe,
  title  = {Safe Sample Screening for Support Vector Machines},
  author = {Ogawa, Kohei and Suzuki, Yoshiki and Suzumura, Shinya and Takeuchi, Ichiro},
  journal= {arXiv preprint arXiv:1401.6740},
  year   = {2014}
}
@inproceedings{mialon2020screening,
  title    = {Screening Data Points in Empirical Risk Minimization via Ellipsoidal Regions and Safe Loss Functions},
  author   = {Mialon, Gr\'egoire and d'Aspremont, Alexandre and Mairal, Julien},
  booktitle= {Proceedings of the 23rd International Conference on Artificial Intelligence and Statistics (AISTATS)},
  year     = {2020},
  note     = {arXiv:1912.02566}
}
@inproceedings{sun2017meprop,
  title    = {{meProp}: Sparsified Back Propagation for Accelerated Deep Learning with Reduced Overfitting},
  author   = {Sun, Xu and Ren, Xuancheng and Ma, Shuming and Wang, Houfeng},
  booktitle= {Proceedings of the 34th International Conference on Machine Learning (ICML)},
  year     = {2017},
  note     = {arXiv:1706.06197}
}
@article{nikdan2023sparseprop,
  title  = {{SparseProp}: Efficient Sparse Backpropagation for Faster Training of Neural Networks},
  author = {Nikdan, Mahdi and Pegolotti, Tommaso and Iofinova, Eugenia and Kurtic, Eldar and Alistarh, Dan},
  journal= {arXiv preprint arXiv:2302.04852},
  year   = {2023}
}
@inproceedings{schultheis2023towards,
  title    = {Towards Memory-Efficient Training for Extremely Large Output Spaces: Learning with 500k Labels on a Single Commodity GPU},
  author   = {Schultheis, Erik and Babbar, Rohit},
  booktitle= {Machine Learning and Knowledge Discovery in Databases (ECML PKDD)},
  year     = {2023},
  doi      = {10.1007/978-3-031-43418-1_41},
  note     = {arXiv:2306.03725}
}
```

**引用纪律**：`○` 级条目（[9]–[12]）只可出现在过程文档；写入正文前须先按 `raw/AGENTS.md`
取得全文并按 `wiki/AGENTS.md` 建立结构化笔记。
[3] 的题录转引自 [2]，**本仓库未持有其原件**，若正文需要单独引用会议版须先补原件。
