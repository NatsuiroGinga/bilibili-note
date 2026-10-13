---
title: "RS-Del: Edit Distance Robustness Certificates for Sequence Classifiers via Randomized Deletion"
authors:
  - Zhuoqun Huang
  - Neil G. Marchant
  - Keane Lucas
  - Lujo Bauer
  - Olga Ohrimenko
  - Benjamin I. P. Rubinstein
year: 2023
date: 2026-10-13
journal: "NeurIPS 2023（第 37 届神经信息处理系统大会）；本地原件 PDF 为 arXiv:2302.01757v3（2024-01-24）相机就绪版，页眉标注 `37th Conference on Neural Information Processing Systems (NeurIPS 2023)`"
source_pdf: "[[raw/papers/attack-detection/2023-Huang-RS-Del序列分类器编辑距离证书.pdf]]"
tags:
  - 认证鲁棒性
  - 随机平滑
  - 编辑距离
  - 序列分类器
  - 恶意软件检测
  - Levenshtein距离
  - 类型/论文
aliases:
  - RS-Del
  - Huang2023-RSDel
  - 随机删除平滑
key_finding: 用「随机删除（RS-Del）」平滑离散序列分类器，即可在 Levenshtein/编辑距离威胁模型（删除、插入、替换任意子集，含块级编辑）下给出可证明的认证半径；证明不走 Neyman-Pearson 而围绕最长公共子序列（LCS）组织，且对任意基分类器成立。
method: 随机删除平滑机制（每个元素以概率 p_del 独立删除）+ 可调决策阈值 η；围绕 LCS 的认证推导（Lemma 4 等价编辑、Theorem 5、Table 1、Theorem 7 Levenshtein 证书）；块级 chunking；Monte-Carlo 下置信界（BinLCB）；并用删除扰动序列训练基分类器
baseline: 非平滑非认证 MalConv（NS）、随机消融平滑 RS-Abn（仅 Hamming 距离证书，O={sub}）
---

# RS-Del: Edit Distance Robustness Certificates for Sequence Classifiers via Randomized Deletion

> Huang, Marchant, Lucas, Bauer, Ohrimenko, Rubinstein · NeurIPS 2023 · 正文 + 附录（正文约 9 页，附录至物理页 35+）

> 原件状态：本笔记基于 **Zotero 中该条的官方 PDF 附件**全文提取撰写（条目 key `CW84X3AT`，URL `https://arxiv.org/abs/2302.01757`）。PDF 属于 NeurIPS 2023 相机就绪版。**`raw/papers/attack-detection/` 下的同名 PDF 副本已于 2026-10-13 由主代理补齐**（812 KB，`file` 核验为 `PDF document, version 1.5`），`source_pdf` 链接**现已有效**。原始阻塞记录见 `.Codex/docs/2026-10-13-编辑距离证书文献核查/notes.md`（历史）。所有引文锚定到章节号/式号/表号，物理页码仅在可确证处标注。

## 一句话

随机平滑此前几乎只用于图像等连续定长输入的 `ℓ_p` 威胁模型；本文把它搬到**离散、变长序列**上，提出**只做随机删除**的平滑机制 RS-Del，证明它足以同时对抗**删除、插入、替换**三种编辑操作（任意子集 O ⊆ {del, ins, sub}），在**编辑距离**下给出认证半径；证明不依赖 Neyman-Pearson 而围绕**最长公共子序列（LCS）**组织，且证书对任意基分类器成立、可黑盒调用。

## 背景：问题的演进

- 既有认证鲁棒性几乎都假设**连续、定长输入** + `ℓ_p` 范数有界扰动（凸松弛、逐层界、随机平滑三类方法，§1）。
- 真实攻击并不止于连续模态：二进制可执行文件、源码、PDF 等**离散输入**上的攻击已被大量演示（§1 引 [17–22]）。
- 离散模态下已有认证工作主要限于 **Hamming（`ℓ_0`）距离**，即攻击者只能**覆盖**内容（替换），**不覆盖插入/删除**——而插入/删除会改变序列长度，是防规避场景（如恶意软件加壳/改节）的核心手段（§1）。
- 本文补上这一空白：给出**编辑距离**（含 del/ins/sub）的认证框架，并允许**块级编辑**。

## 方法核心

### 1. 平滑分类器与可调决策阈值（§3.1）

基分类器 `f_b : X → Y`，平滑机制 `φ : X → D(X)`（把输入映射到扰动输入的分布），合成平滑分类器 `f`：

$$f(x) := \arg\max_{y\in Y}\ \{\,p_y(x; f_b, \phi) - \eta_y\,\} \qquad (2)$$

$$p_y(x; f_b, \phi) = \Pr_{z\sim\phi(x)}[\,f_b(z) = y\,] \qquad (3)$$

- `η = {η_y}_{y∈Y}` 是**一组实数可调决策阈值**。原文强调：此前随机平滑的定义（如 [13,14]）**不含决策阈值**，等价于 `η = 0`；引入 `η` 是为了**在类间权衡错误率与鲁棒性**（Remark 1，§3.1）。
- 该阈值设计对**误分类代价不对称**的场景有用——见下方案例研究（恶意软件检测）。

### 2. 随机删除机制 RS-Del（§3.2）

- 对序列 `x`（元素索引集 `[x] = {1, …, |x|}`），**每个元素以概率 `p_del` 独立删除**。
- **关键反直觉点**（Remark 2，§3.2）：「随机平滑要求机制与威胁模型的操作集 O 完全对齐」是**误解**。鲁棒性层面只要求：机制对输入与其邻域返回的分布**统计接近**即可。因此**只用删除**就能覆盖包含插入/替换的威胁模型。
- 删除机制附带两个好处：输入变短（**提升计算效率**，见 Appendix G），且实验显示对精度只有轻微影响（§5）。
- 平滑机制 `φ` 具体为把 `z` 的分布 `Pr[φ(x) = z]` 定义在 `apply(x, ε)` 上（式 6 一帯）。

### 3. 认证推导：围绕 LCS 而非 Neyman-Pearson（§4）

- **为什么不用 Neyman-Pearson**：编辑距离邻域下 Neyman-Pearson 方法**不可解**（intractable），故作者改用**代表性最长公共子序列**作为「平滑空间中两输入之间的参照点」来界置信度（§1、§4.1）。
- **充分条件（Proposition 3，§4.2）**：`ρ(x, μ_y) ≥ ν_y(η)`，其中
  $$\rho(x, \mu_y) := \min_{\bar x \in N_r(x)}\ \min_{h \in \mathcal F(x,\mu_y)} p_y(\bar x; h) \qquad (9)$$
  是类别 `y` 置信度的**紧下界**；阈值
  $$\nu_y(\eta) = \tfrac12 + \eta_y - \min_{y' \ne y}\eta_{y'}\quad (\eta_y \ge \min_{y'\ne y}\eta_{y'},\ |Y|>2) \qquad (10)$$
  （多类/二类分支不同，见原文式 10 上下）。
- **Lemma 4（等价编辑）**：设 `z*` 是 `x̄` 与 `x` 的一个 LCS，取使 `apply(x̄, ε̄*)=apply(x, ε*)=z*` 的编辑 `ε̄*∈E(x̄)`、`ε*∈E(x)`；则存在双射 `m : 2^{ε̄*} → 2^{ε*}` 使 `apply(x̄,ε̄)=apply(x,ε)`，且 `s(ε̄,x̄;h)` 与 `s(ε,x;h)` 成比例。
- **Theorem 5（§4.2，式 14）**：对任意 `x̄, x ∈ X`，
  $$\rho(\bar x, x, \mu_y) \ \ge\ \tilde\rho(\bar x, x, \mu_y) = p_{del}^{|\bar x| - |x|}\,\mu_y - 1 + p_{del}^{\frac12(\mathrm{dist}_{\mathrm{LCS}}(\bar x, x) + |x| - |\bar x|)}$$
  其中 `dist_LCS` 是 **LCS 距离**（脚注 2：LCS 距离 ≡ 操作集 O={del, ins} 的广义编辑距离），且 `dist_LCS(x̄,x) = |x̄| + |x| − 2|z*|`。

### 4. 邻域最小化与主证书（§4.3、Table 1）

对 `ρ̃` 在**编辑距离邻域** `N_r(x)` 上取最小，得到各操作子集下的认证半径 `r*`（Table 1，`μ_y` 为预测类置信度、`ν_y` 为阈值）：

| 允许的编辑操作 O | 认证半径 r* |
| --- | --- |
| {del} | `log((1−μ_y)/(1−ν_y)) / log p_del` |
| {ins} | `log(ν_y/μ_y) / log p_del` |
| {del, ins} | `log(ν_y/μ_y) / log p_del` |
| {del, ins, sub}（Levenshtein，含 sub 的其余组合） | `⌊log(1+ν_y−μ_y) / log p_del⌋` |

（`{del}|{ins}|{del,ins}` 三行的公式取自 Table 1 原文；因 PDF 抽取中该表格单元格线性化，`{del,ins}` 一行与 `{ins}` 一行在抽取文本中同为 `log(ν_y/μ_y)/log p_del`，若需精确引用请回原件 Table 1 复核。）

- **Theorem 7（Levenshtein 距离证书，§4.3）**：`O = {del, ins, sub}` 时，`N_r(x)` 内置信度下界
  $$\tilde\rho(x; \mu_y) = \mu_y - 1 + p_{del}^{\,r}$$
  故**认证半径** `r* = ⌊log(1 + ν_y(η) − μ_y) / log p_del⌋`。对约束在任意 O 上的情形可「直接适配」，全部组合见 Table 1。
- **块级编辑（chunking，§3.3）**：把序列重解释为**块序列**（如整条机器指令、地址、PE 头字段），得到更紧的证书：半径 `r`（块）下的下界为
  $$\tilde\rho(x;\mu_y) = \mu_y - 1 + \frac{\binom{|x|-r}{\,k(|x|)\,}}{\binom{|x|}{\,k(|x|)\,}}$$
  认证半径为满足 `μ_y − 1 + C(|x|−r,k(|x|))/C(|x|,k(|x|)) − ν_y(η) ≥ 0` 的最大整数 `r`。案例中用 **Ghidra 反汇编器**把字节切成机器指令块（§5、Fig. 3、Appendix C.3）。

### 5. 与 RS-Abn 的关系（Proposition 11）

对相同平滑强度 `p_del = p_ab = p`，**RS-Del 的认证半径严格不小于 RS-Abn**（RS-Abn 是 Jia 等的 randomized ablation 机制，只给 Hamming 证书 O={sub}）；且 RS-Del 的编辑距离球**包含** RS-Abn 的 Hamming 球，覆盖输入集更大（§5、Appendix I、物理页 35 附近有证明）。

### 6. 认证算法（Figure 1）

`RS-Del(x; f_b, p_del, η, α, n_pred, n_bnd)`：① 采样预测样本估计各类置信度 `μ̂_y`；② `ŷ ← argmax_y{μ̂_y − η_y}`；③ 另采样求下置信界 `μ_ŷ ← BinLCB(...)`；④ 用 Table 1 算 `r*`；⑤ 若 `μ_ŷ < η_ŷ` 则 **abstain（弃权）**。证书**只依赖** `x`、`ŷ`、置信度 `μ_y`、阈值 `η_y` 与平滑机制 `φ`，**不依赖基分类器 `f_b` 的架构**——故对任意基分类器成立、可仅以推理 API 黑盒查询。

### 7. 它是训练方法还是推理时认证？（§3.3 "Training"）

**两者都有，且训练是必要的**：原文指出随机平滑**对常规训练的分类器效果很差**，因此作者**专门训练**用于 RS-Del 的基分类器——做法是**在训练时用从 `φ` 采样的扰动（删除）序列替换原始序列**（§3.3 "Training"）。即：**训练阶段**使用删除扰动做数据增广式训练；**推理阶段**用 Monte-Carlo 采样 + 下置信界给出认证半径。

## 实验结果（§5、Appendix E/F）

- **数据集**：两个 Windows 恶意软件数据集 **Sleipnir2**（依 Al-Dujaili 等从公开源编译）与 **VTFeed**（取自 VirusTotal）；样本量见 Table 3。
- **模型**：基于 **MalConv**（对原始字节序列端到端学习，嵌入维度 8、窗长 500、通道 128、输入截断 2 MB）的三个变体：**NS**（未平滑、未认证）、**RS-Abn**（Hamming 证书）、**RS-Del**（编辑距离证书）。
- **动机数字**：在 VTFeed 样本上，**83% 的 YARA 规则命中由少于 128 字节触发** ⇒ 编辑 <128 字节即可规避多数规则。
- **主结果**：**certified accuracy 91% @ 编辑距离半径 128 字节**，用约 `10^3` 次模型查询；暴力认证同半径需 `> 10^308` 次查询（§1、§5）。
- **Table 2（物理页 8，Sleipnir2，字节级 Levenshtein，O={del,ins,sub}）**：

  | p_del | 干净准确率 | 中位认证半径 CR（字节） | 中位 NCR（%） |
  | ---: | ---: | ---: | ---: |
  | NS | 98.9% | — | — |
  | 90% | 97.1% | 6 | 0.0023 |
  | 95% | 97.8% | 13 | 0.0052 |
  | 97% | 97.4% | 22 | 0.0093 |
  | 99% | 98.1% | 68 | 0.0262 |
  | **99.5%** | **96.5%** | **137** | **0.0555** |
  | 99.9% | 83.7% | 688 | 0.2269 |

  正文表述：`p_del = 99.5%` 是较好折中，干净准确率相对 NS 只降 2–3%；`p_del = 99.9%` 时干净准确率掉超过 10%。VTFeed 上 RS-Del 为 97%→干净 92.1%/CR 22、99%→86.9%/CR 68。
- **块级（INSN）结果**见 Fig. 5（按反汇编指令块编辑）。
- **非对称证书（低误报相关工作点，Appendix D.3/E.1，Table 8 在物理页 27）**：
  - 作者先把**基 MalConv 的决策阈值校准到目标 FPR = 0.5%**（理由：恶意软件检测器通常调到低 FPR，如 < 0.1–1%，假报太多困扰用户；Appendix D.3）。
  - 在 `p_del = 99.5%` 上变动**平滑层阈值 `η₁`**：FNR 基本稳定（约 7%），但**中位认证半径随类变化**——`η₁ = 50%` 时恶意/良性类的中位 CR 均衡，`η₁` 调小则**偏向恶意类**；`η₁ = 5%` 时恶意类中位 CR 可升至 **582 字节**（Table 8）。原文总结：**可非对称认证，某些情形把恶意实例的认证半径提升至 4 倍**。
- **经验鲁棒性**：对若干已发表攻击（Disp、Slack、HDOS、HField 等，Appendix F）测试 `RS-Del`，观察到**攻击成功率下降**，鲁棒性超出认证半径之外。

## 我的理解

- **核心直觉**：随机删除后，攻击者无论做删除/插入/替换，都很难在**被保留元素构成的子序列**上稳定改变分类器输出；两块输入若 LCS 相同（或高度重叠），其删除分布就**统计接近**，因此认证可以围绕 LCS 组织，而无需让平滑算子枚举全部编辑类型。
- **「机制不必与威胁模型操作集一致」** 是本文最有迁移价值的观念（Remark 2）：认证半径只要求平滑分布在邻域内接近，**不要求平滑算子实现威胁模型允许的每一种操作**。
- **它是「先平滑后认证」的推理侧工具**，但要生效**必须配套训练**（用删除扰动训练基分类器）。

## 与相关工作的关系

- 直接前驱：随机平滑（Cohen 等 2019；Salman 等 2019）——连续 `ℓ_p`；随机消融 RS-Abn（Jia 等）——Hamming 距离离散证书。本文把离散认证从 **Hamming 推广到编辑距离**。
- 与 Hamming-only 离散认证（[23–30]）的差别：那些只覆盖「覆盖/替换」攻击者，**不覆盖插入/删除**（§1）。
- 本课题内相关：**[[课程式学习-全文|Shi & Liu AAAI-24 课程式对抗训练在线视角]]**（同为对抗训练理论，但对象是 `ℓ_p` 连续扰动、且是**训练期**泛化界）；**[[dga/2024-Drichel-DGA检测鲁棒分类|Drichel 2024 鲁棒 DGA 分类]]**（离散扰动对抗训练的已发表先例，本课题查重关键命中）。RS-Del 与二者不在同一层次：它是**推理时认证**，不是训练机制。

## 疑问 / 待验证

- 本课题的编辑算子是**共享前缀替换**（冻结点号、只改可编辑位），而 RS-Del 的平滑用**随机删除**——RS-Del 的证书是否适用于「纯替换型」编辑距离算子？**原文的答案是「适用于任意 O ⊆ {del, ins, sub}」**（O={sub} 即纯替换、对应 Hamming 证书；Theorem 7 与 Table 1 覆盖全部组合）。但需注意：**RS-Del 的平滑器是删除**，证书针对的邻域才是操作集 O；「替换型编辑距离」在 RS-Del 里是被认证的**威胁模型**，而非被实现的平滑算子。
- RS-Del 的认证是**逐样本**（给定 `x` 与阈值给出 `r*`），与「域名字符串序列」的迁移还需核对：域名长度远小于恶意软件二进制（`NCR` 归一化口径、`p_del` 选择、abstain 率）在本课题未见证据。
- 是否可作为本课题正文的「威胁模型/认证工具」层次引用，取决于评估报告（见 `thesis/methods/第三章-编辑距离证书与课程理论评估.md`）。

## 原始摘要

> Randomized smoothing is a leading approach for constructing classifiers that are certifiably robust against adversarial examples. Existing work on randomized smoothing has focused on classifiers with continuous inputs, such as images, where ℓ_p-norm bounded adversaries are commonly studied. However, there has been limited work for classifiers with discrete or variable-size inputs, such as for source code, which require different threat models and smoothing mechanisms. In this work, we adapt randomized smoothing for discrete sequence classifiers to provide certified robustness against edit distance-bounded adversaries. Our proposed smoothing mechanism randomized deletion (RS-Del) applies random deletion edits, which are (perhaps surprisingly) sufficient to confer robustness against adversarial deletion, insertion and substitution edits. Our proof of certification deviates from the established Neyman-Pearson approach, which is intractable in our setting, and is instead organized around longest common subsequences. We present a case study on malware detection—a binary classification problem on byte sequences where classifier evasion is a well-established threat model. When applied to the popular MalConv malware detection model, our smoothing mechanism RS-Del achieves a certified accuracy of 91% at an edit distance radius of 128 bytes.

## 文献信息

- arXiv：`2302.01757`（v3，2024-01-24）；会议：NeurIPS 2023（第 37 届）。
- 代码：<https://github.com/Dovermore/randomized-deletion>
- 官方页：<https://proceedings.neurips.cc/paper_files/paper/2023/hash/3ba82362eb0aa75487069f19fde794fe-Abstract-Conference.html>
- Zotero 条目：key `CW84X3AT`（类型 preprint，含 PDF 附件）。
