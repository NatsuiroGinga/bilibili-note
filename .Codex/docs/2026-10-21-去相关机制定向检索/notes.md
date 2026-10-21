# 检索笔记：第四章机制二第三轮——去相关机制定向检索

> 规则：每条在线命中只作候选；无 `raw/` 原件与 `wiki/` 全文笔记者不得升级为全文证据。
> 本文件只登记与推荐，不做存废裁决；不 commit。
> 日期：2026-10-21。工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`。

## 0. 起始事实

- NCL 正源：Liu & Yao 1999, IEEE Trans. SMC-B 29(6):716–725, DOI `10.1109/3477.809027`；本地全文 `raw/papers/methodology/1999-Liu-NegativeCorrelationLearning.pdf`；笔记 `wiki/papers/methodology/1999-Liu-负相关学习NCL.md`。
- NCL 惩罚（分类用式 11）：$p_i=(F_i-F)\sum_{j\ne i}(F_j-F)$。
- 先导失败诊断（父代理提供，本次未回原始日志核）：$p_i=-(f_i-\bar f)^2$ 在成员重合处梯度恒零；$\lambda|p|/\mathrm{BCE}$ 实测 1e-3~7e-2。
- 第三轮假设：改用尺度稳定去相关项；引用与形式均待核实。

## 1. 任务一：Rosen 1996 正源核实与入库

### 1.1 题录核实（已核实）

| 项 | 值 | 来源 |
|---|---|---|
| 题名 | **Ensemble Learning Using Decorrelated Neural Networks** | Crossref / OpenAlex / S2 |
| 作者 | Bruce E. Rosen | 同上 |
| 出处 | **Connection Science, 8(3–4):373–384** | Crossref / OpenAlex |
| 年份 | 1996（1996-12） | Crossref / OpenAlex |
| DOI | **10.1080/095400996116820** | Crossref / OpenAlex |
| DBLP 键 | `journals/connection/Rosen96` | S2 externalIds |
| 出版社 | Taylor & Francis / Informa | Crossref |

- **修正任务假设**：题名不是 “Ensemble Diversity Using Decorrelated Neural Networks”，出处也不是 WCNN/INNS；Crossref、OpenAlex、S2/DBLP 三方一致支持上述期刊条目，未发现同题会议版。
- **独立链接证据**：Liu & Yao 1999 的 Crossref 参考文献第 6 条即本 DOI，说明 NCL 所对比的 “Rosen 的去相关网络” 就是本篇。
- DBLP 站点被 Anubis 反爬拦截，curl 与浏览器 UA 均返回挑战页；改用 S2 的 DBLP 外部键。

### 1.2 开放副本与本地归档

- OpenAlex 第二 location：CiteSeerX `10.1.1.8.9813`，原始 URL `http://www.cs.ucla.edu/~rosen/rosen/decor.ps`。
- 作者页现 403；Wayback CDX 有 2003-05-13 与 2006-02-08 的 `application/postscript` 快照。
- 下载 `https://web.archive.org/web/20060208215016id_/http://www.cs.ucla.edu:80/~rosen/rosen/decor.ps`（381,965 bytes，SHA-256 `d26e9aa27db85b8ac213bf14d29a6b8fd6ec27b0313d381d245d3d079537ecf0`）。
- PS 头：`%%Title: connection_science.dvi`、`%%Pages: 14`；用 Ghostscript 10.08.0 转 PDF（本机 `brew install ghostscript`），14 页、Letter、406,001 bytes，SHA-256 **`0cb89ced75c38baf92e37c34af0d27e46f8a780292a80be1bcba69e93d4f1865`**。
- 归档：`raw/papers/methodology/1996-Rosen-去相关神经网络集成.pdf`；MinerU `extract -l en` 14/14 页。
- wiki 笔记：`wiki/papers/methodology/1996-Rosen-去相关神经网络集成.md`；已更新 `wiki/papers/methodology/INDEX.md`。
- **版本边界**：本地为作者预印本（首页 “To appear in Connections Science”，原文笔误），非出版社 12 页版；期刊版在付费墙后，未取得。下文页码均为预印本物理页。

### 1.3 全文关键事实（已渲染页视觉复核）

| 项 | 内容 | 页码 |
|---|---|---|
| 成员误差 | $E_j=\sum_p[(y_p-f_j)^2+\sum_{i=1}^{j-1}\lambda(t)d(i,j)P]$ | 第 4 页，式 (7) |
| 惩罚函数 | $P=(y-f_i)(y-f_j)$，两网络误差乘积 | 第 6 页，式 (8) |
| 指示函数 | 只选 $i=j-1$；或只选偶数号与前一个 | 第 6 页，式 (9)–(10) |
| $\lambda(t)$ | 常数或时变；脚注 1：通常由交叉验证确定 | 第 6 页 |
| 退火 | 惩罚过大会抬高个体误差；先强制不同映射，再退火回模式误差 | 第 5 页 |
| 0–1 分类域 | 式 (8) 惩罚**恒非负**，只能压低正相关 | 第 8 页 |
| $\lambda$ 实例 | 3 Parity：$1/i$；带噪正弦：$100/(Nt)$；非线性：常数 | 第 7、8、9 页 |
| 结果 | 带噪正弦集成 1-2：0.0034→0.0030；非线性集成 1-5：0.14780→0.14641 | 第 14 页，表 1–2 |

### 1.4 与 NCL 的精确关系（代数推论，非原文陈述）

- Rosen：$P_{ij}=e_i e_j$，只对 $i<j$ 求和，**顺序训练**，参考目标 $y$；训练 $j$ 时 $e_i=y-f_i$ 固定，$\partial P/\partial f_j=-(y-f_i)$，成员重合时也不为零（除非前网络完美）。
- NCL 分类形式：$p_i=(F_i-F)\sum_{j\ne i}(F_j-F)$；令 $e_k=F_k-F$，则 $\sum_k e_k=0$，故 $p_i=e_i\sum_{j\ne i}e_j=-e_i^2$，$\partial p_i/\partial F_i=-2(1-1/M)e_i$。**先导观测到的消失梯度是「参考对象换成集成均值」的代数后果，不是 Rosen 式 (8) 的性质。**
- 但 Rosen 不解决尺度：$P$ 双线性、未归一化；0–1 域恒非负，无法制造负相关。
- 结论：Rosen 可作「配对 + 目标参照」正源，不能直接当作「尺度稳定、可正可负」的去相关项。

### 1.5 证据等级

- 题录：Crossref + OpenAlex + S2（DBLP 键）+ NCL 参考文献 DOI 四方一致，**已核实**。
- 全文：作者预印本，14 页，**本地全文已入库**；出版社版未取得（付费墙）。
- 公式：式 (7)、(8)–(10)、分类非负性、表 1–2 已回渲染页视觉复核。

## 2. 检索方法总览

- 本地索引：`status` 显示缺失；`build`（默认向量）失败：`EmbeddingBackend.__init__() got an unexpected keyword argument 'device'`。按 README 降级 `build --lexical-only` 成功（14.1 s，2064 notes，98,693 chunks）。**本轮本地查询仅词法通道，向量通道未运行**。
- 本地词法查询命中：NCL、Rosen、Fort 2019、BatchEnsemble、TabM；未发现 Chen & Yao、Brown & Wyatt、Harangi、VICReg/Barlow 等外部文献的本地笔记。
- Zotero：`negative correlation learning`、`decorrelated neural networks`、`diversity regularization deep ensembles` 三组精确检索均无条目；语义检索返回无关结果（负相似度），未采用。
- 在线：Crossref、OpenAlex、Semantic Scholar（多次 429）、Google Scholar `scholar` CLI、arXiv、AAAI、MDPI、作者主页。DBLP 被 Anubis 拦截，用 S2 的 DBLP 键替代。
- 所有外部全文只登记，**未入库**（任务要求仅 Rosen 全文入库）。

## 3. 组 1：NCL 变体与后续——是否指出 $p_i$ 消失梯度/尺度问题，怎么修

### 3.1 检索式与来源

1. 本地：`query "negative correlation learning" --scope paper --mode lexical --top-k 8` → NCL、Rosen、GRPO 等；无 NCL 后续文献。
2. OpenAlex：`https://api.openalex.org/works?filter=title_and_abstract.search:%22negative%20correlation%20learning%22&per-page=25&sort=cited_by_count:desc` → 270 条；代表：Liu & Yao 1999 Neural Networks、Ren et al. 2016 综述、Higuchi et al. 2000、Brown 2005、Islam et al. 2003、Shi et al. 2018、Alhamdoosh & Wang 2014、Chen & Yao 2009/2010、Zhang et al. 2019、Wang et al. 2010、Perales-González et al. 2022。
3. Crossref：`query.bibliographic=negative correlation learning neural network ensemble&rows=20` → 含 Chan & Kasabov 2005、Liu & Yao 1999、Chen/Cohn/Yao 2012 等。
4. Google Scholar：`scholar lookup "negative correlation learning penalty gradient vanishing ensemble" --json --limit 8` → Brown & Wyatt 2003、Wang et al. 2010、Zhao et al. 2025、Ye & Yu 2022。
5. Semantic Scholar：多次 429，未取得可用检索结果。

### 3.2 精读命中

#### (1) Brown & Wyatt 2003——最直接的尺度/λ 代数分析（全文）

- 题录：*Negative Correlation Learning and the Ambiguity Family of Ensemble Methods*，MCS 2003，LNCS 2709:266–275，DOI `10.1007/3-540-44938-8_27`。
- 全文：作者页 PDF `https://profgavinbrown.github.io/files/brown2003mcs.pdf`，10 页，SHA-256 `4d30653fd98e666aff89de162b3ed7b91594875ced5bf041124f2f9f11fb3c7c`。
- 关键公式（页码为 PDF 物理页）：
  - 式 (1)（第 2 页）：$\epsilon_i=\frac12(f_i-d)^2+\lambda p_i$。
  - 式 (2)（第 2 页）：$p_i=(f_i-\bar f)\sum_{j\ne i}(f_j-\bar f)$，$\bar f$ 为全体成员上一时刻平均输出。
  - 式 (4)（第 3 页）：$p_i=-(f_i-\bar f)^2$；前提是去掉 Liu 的 “$\bar f$ 对 $f_i$ 为常数” 假设，且成员权重均匀 $1/M$。
  - 式 (8)（第 4 页）：不去掉该假设时，$\partial\epsilon_i/\partial f_i=f_i-d-\lambda[2\frac{M-1}{M}(f_i-\bar f)]$；Liu 的推导让确定性因子 $2(M-1)/M$ 消失。
  - 式 (9)（第 4 页）：$\lambda=\gamma[2\frac{M-1}{M}]$，$\gamma$ 才是问题相关缩放。
  - 二阶导（第 5 页）：$1-\lambda(1-\frac1M)$；若为负则损失只有局部极大/拐点，梯度信息失效。上界 $\lambda_{\rm upper}=M/(M-1)$、$\gamma_{\rm upper}=M^2/[2(M-1)^2]$；$M\to\infty$ 时分别趋于 1 和 0.5。
  - 实证（第 5–6 页）：两个网络时 $\gamma=\lambda$；乳腺癌数据最优 $\gamma=1.7$（相对 $\gamma=0$ 错误率降 21%），$\gamma>1.8$ 后误差失控；心脏病数据 $\gamma>1.45$ 后失控。原文明确质疑 Liu 的 $[0,1]$ 上界。
- **对消失梯度的意义**：式 (4) 已给出 $p_i=-e_i^2$，式 (8) 的惩罚梯度因子是 $(f_i-\bar f)$；成员重合（所有 $f_i=\bar f$）时 $p_i=0$ 且惩罚项梯度为零。**Brown 没有明说 “消失梯度”，这是本笔记由式 (4)/(8) 直接推出的**；他的修法是 λ 重新参数化 + 上界，不恢复重合处的非零惩罚梯度。
- 证据等级：全文 PDF，公式已对照 MinerU 文本与 PDF 页；题录 Crossref 已核实。

#### (2) Chen & Yao 2009/2010——λ 与过拟合的批评（仅摘要）

- *Regularized Negative Correlation Learning for Neural Network Ensembles*，IEEE TNN 20(12):1962–1979，DOI `10.1109/TNN.2009.2034144`。
- *Multiobjective Neural Network Ensembles Based on Regularized Negative Correlation Learning*，IEEE TKDE，DOI `10.1109/TKDE.2010.26`。
- 摘要要点：NCL 在 $\lambda=1$ 时等价于把整个集成当作单个学习机、只最小化 MSE 而无正则，因而容易拟合噪声；**用交叉验证调 $\lambda$ 不能克服该过拟合**；提出 RNCL/MRNCL，给整个集成增加正则项，并做多目标进化或贝叶斯解释。
- 这是 **λ/正则化尺度** 的批评与修法，不是消失梯度修法；两篇均未取得全文，**只作摘要级证据**。

#### (3) Wang, Chen & Yao 2010——分类 NCL 的理论缺口（全文）

- 题录：*Negative Correlation Learning for Classification Ensembles*，IJCNN 2010，DOI `10.1109/IJCNN.2010.5596702`。
- 全文：作者页 PDF `http://staff.ustc.edu.cn/~hchen/papers/IJCNN2010-NCL.pdf`，8 页。
- 要点：
  - CELS 的 NCL 惩罚式 (1)–(2)（第 2 页）与 Liu & Yao 相同；$\lambda\in[0,1]$；NCCD 的 $\lambda\in[0,0.5)$（第 3 页）。
  - 摘要与第 1 页：既有 NCL（CELS、NCCD）及其理论都在**回归语境**；分类的歧义分解不同，直接套用有理论缺口。
  - AdaBoost.NC 改用 0–1 误差下的歧义项，并把惩罚放进样本权重（第 4 页）；$\lambda$ 不再有界，实验取 0.25–12，且不敏感（第 5 页）。
- 这是**分类场景换惩罚形式**的先例，但没有给出尺度稳定的可微去相关项，也没有消失梯度分析。

#### (4) Shui et al. 2018——深度集成中的 NCL 惩罚（全文，预印本）

- 题录：*Diversity regularization in deep ensembles*，arXiv:1802.07881，6 页；OpenAlex 只登记 arXiv（submittedVersion），**未见同行评审出版记录**。
- Algorithm 1（第 2 页）：$E_i=L(y,h_i(x))+\lambda\,\mathrm{div}(h_i(x);h_{1:M})$；$\mathrm{div}=(h_i-\bar h)[\sum_{j\ne i}(h_j-\bar h)]$；**$\bar h$ 在反向传播时视为常数**；$\lambda=0.1$，$M=7$，VGG11，CIFAR-100。
- 结果：NC 正则降低 ECE、保持精度；$M=3$ 时几乎无影响，$M$ 较大时效果明显（第 2 页及附录）。
- **没有讨论成员重合/坍缩/消失梯度**；这是 NCL 惩罚在深度集成中的直接沿用，不是尺度修正。

#### (5) 其他 NCL 变体（仅题录，未精读）

- Liu & Yao 1999, *Ensemble learning via negative correlation*, Neural Networks 12(10):1399–1404, DOI `10.1016/S0893-6080(99)00073-8`（与本地 T-SMC-B 版为同主题姊妹篇）。
- Higuchi, Yao & Liu 2000, IEEE TEC, DOI `10.1109/4235.887237`（EENCL）。
- Islam, Yao & Murase 2003, IEEE TNN, DOI `10.1109/TNN.2003.813832`（CNNE）。
- Alhamdoosh & Wang 2014, Information Sciences, DOI `10.1016/j.ins.2013.12.016`（Fast decorrelated NN ensembles with random weights）。
- Shi et al. 2018, CVPR, DOI `10.1109/CVPR.2018.00564`；Zhang et al., IEEE TPAMI 43(3):982–998（2019 早期访问/2021 正式卷期），DOI `10.1109/TPAMI.2019.2943860`（Deep NCL）。
- Perales-González et al. 2022, IEEE TNNLS, DOI `10.1109/TNNLS.2021.3055734`（GNCL）。
- 以上均未取得全文，不得支撑具体公式或 λ 结论。

### 3.3 组 1 结论

- **有尺度/λ 批评**：Brown & Wyatt 2003 给出 $p_i=-e_i^2$、$2(M-1)/M$ 因子、$\lambda=\gamma[2(M-1)/M]$ 与二阶导上界；Chen & Yao 2009/2010 指出 $\lambda=1$ 无正则、CV 调 λ 不能解决过拟合。
- **有分类场景修法**：Wang et al. 2010 改用 0–1 歧义项/样本权重，λ 范围放宽；但这不是尺度稳定的可微去相关项。
- **没有文献明确写“$p_i$ 在成员重合处梯度恒零”**；最接近的是 Brown 2003 的式 (4)/(8) 代数，本笔记据此推出，须标注为推论。
- **没有文献给出既保留配对去相关、又归一化尺度的 NCL 修法**；Shui 2018 只是原样搬到深度集成（λ=0.1）。

## 4. 组 2：联合训练中成员相似化/坍缩的谱系锚点

### 4.1 检索式与来源

1. 本地：`query "ensemble diversity regularization"`、`"member similarity joint training ensemble"` → Fort 2019、BatchEnsemble、NCL、DMAE。
2. OpenAlex：`title_and_abstract.search:"diversity regularization" AND ensemble` → Shui 2018、Mehrtens 2022、Li/Yu/Zhou 2012、Wen et al. 2020、Zhang et al. 2020。
3. OpenAlex：`title_and_abstract.search:"deep ensemble" AND diversity` → Fort 2019、Wenzel 2020、MOD 2020、Repulsive 2021、Abe et al. 2022 等。
4. OpenAlex：`title_and_abstract.search:"joint training" AND "ensemble diversity"` → 仅 2 条（均 2026），说明该精确短语在文献中很少见。
5. OpenAlex：`title_and_abstract.search:"shared backbone" AND ensemble AND diversity` → Packed-Ensembles 2022、Multi-headed Neural Ensemble Search 2021 等。
6. OpenAlex：`title_and_abstract.search:"diversity collapse"` → 多为 2026 视频/扩散模型文献；经典集成语境用 “uncertainty collapse”（MOD）或 “collapse to the same function/mode”（Repulsive）。

### 4.2 精读命中

#### (1) D'Angelo & Fortuin 2021——最直接的“联合训练成员合流”锚点（全文）

- 题录：*Repulsive Deep Ensembles are Bayesian*，NeurIPS 2021（官方摘要页未列页码；DBLP `conf/nips/DAngeloF21`；NeurIPS poster 26888）；arXiv:2106.11642。
- 摘要（第 1 页）与 §2（第 3 页）：
  - “maintaining functional diversity between ensemble members that are independently trained with gradient descent is challenging.”
  - 增加成员会出现**性能饱和**，集成收敛到单个模型的表现；不仅是预测，还包括不确定性/OOD。
  - “the absence of a constraint that prevents particles from converging to the same mode.”
  - 引 Geiger et al. 2020：参数趋于无穷时，集成的经验测试误差收敛到单个训练模型。
- 形式：
  - 式 (3)（第 3 页）：$\phi(w_i^t)=\nabla_{w_i}\log p(w_i^t|D)-\mathcal R(\{\nabla k(w_i^t,w_j^t)\})$；最简单取 $\beta\sum_j\nabla k$，$\beta>0$。
  - RBF 核 $k(w_i,w_j)=\exp(-\frac1h\|w_i-w_j\|^2)$，梯度把成员推开（第 3 页）。
  - 归一化 KDE 形式 $\mathcal R=(\sum_j k)^{-1}\sum_j\nabla k$（第 6 页）；另有 SGE/SSGE。
  - 函数空间版本：核作用在 $\pi_B(f_i)$（一个 batch 的函数值投影），再用 Jacobian 投回参数（第 4、7 页）。
  - 带宽用 median heuristic，自适应带宽优于固定值（第 8 页）。
- 证据等级：全文 PDF（arXiv）+ NeurIPS 2021 题录（DBLP/NeurIPS 页面）；已读摘要、§2、§2.1、§2.2、§3.2、§3.4、实验设置。

#### (2) Fort, Hu & Lakshminarayanan 2019——独立初始化与同一子空间相似（本地全文笔记）

- 本地笔记：`wiki/papers/methodology/2019-Fort-深度集成的损失面视角.md`（arXiv:1912.02757v2，预印本）。
- 要点：不同随机初始化探索函数空间的不同 mode；**同一轨迹及其子空间内的函数预测高度相似**；独立初始化在 diversity–accuracy 平面优于 dropout/对角高斯/低秩高斯/随机子空间；SVHN 上独立运行 JS 散度 0.384，子空间方法 0.034–0.155（物理第 7 页）。
- 边界（笔记已写明）：论文**没有研究**「联合训练/共享梯度是否会让不同 mode 合流」；这一后半句是本课题自己的假设。它只支持「独立初始化提供函数多样性」与「同一子空间成员高度相似」。

#### (3) Jain et al. 2020（MOD）——不确定性坍缩（全文）

- 题录：*Maximizing Overall Diversity for Improved Uncertainty Estimates in Deep Ensembles*，AAAI 2020，DOI `10.1609/aaai.v34i04.5849`；全文 8 页。
- 第 1 页：定义 **uncertainty collapse**——小集成可能在远离训练数据的区域“碰巧一致”，给出虚假高置信。
- 第 2 页：目标 $\min_{\theta_1,\ldots,\theta_M} L_{in}-\gamma L_{out}$，$L_{out}=\mathbb E_Q[\sigma_{mod}^2]$（集成均值预测方差），$\gamma>0$ 由验证集选为“不损害 $L_{in}$ 的最大值”；实验取 $\gamma=3,10$，Wiki 图像搜索 0,2,5,10,20,40,80。
- 第 4 页：把 NCL/NegCorr 作为基线，明确给出 $\sum_m[(\mu_m-\bar\mu)\sum_{m'\ne m}(\mu_{m'}-\bar\mu)]$ 的惩罚形式，并说它 “minimizes the empirical correlation”。
- 与本任务的关系：提供“集成成员在低密度区碰巧一致”的坍缩语言；但它是 OOD 不确定性坍缩，不是共享主干联合训练中的参数/函数合流。

#### (4) Shui et al. 2018——联合训练 + NCL 惩罚的深度集成（全文，预印本）

- 见 §3.2(4)：联合训练多个深度成员并加 NCL 惩罚，λ=0.1；没有测量成员相似度随训练的变化，也没有坍缩分析。

#### (5) 参数高效/多头自集成（本地全文笔记与题录）

- **BatchEnsemble**（Wen, Tran & Ba, ICLR 2020；本地笔记 `wiki/papers/methodology/2020-Wen-BatchEnsemble高效集成与终身学习.md`）：共享慢权重 × 成员秩一快权重；终身学习中每个任务绑定一个成员；无显式成员相似度/去相关惩罚（笔记已核）。
- **TabM**（Gorishniy, Kotelnikov & Babenko, ICLR 2025；本地笔记 `wiki/papers/methodology/2025-Gorishniy-TabM参数高效集成.md`）：共享主干 + 成员专属低开销适配，$k=32$ 默认，成员独立损失/概率平均；无显式去相关惩罚。
- Packed-Ensembles（Laurent et al. 2022, arXiv:2210.09184）与 Multi-headed Neural Ensemble Search（Narayanan et al. 2021, arXiv:2107.04369）：仅题录候选，未取得全文，不作论断。
- 含义：多头/共享主干自集成文献主要靠随机初始化与适配器差异获得多样性，**未把“成员相似化”作为显式惩罚对象**；这为第三轮提供了空白，但也意味着没有现成的多头去相关超参可照抄。

### 4.3 组 2 结论

- 最强谱系锚点是 **Repulsive Deep Ensembles (NeurIPS 2021)**：明确说独立训练成员的功能多样性难以维持、增加成员会饱和并收敛到单模型、缺少约束时粒子会收敛到同一 mode；给出 RBF 核排斥（median heuristic）作为抗合流手段。
- **Fort 2019** 支持“同一轨迹/子空间成员高度相似、独立初始化才分开 mode”，但没有检验联合训练合流；引用时必须带这条边界。
- MOD 提供“uncertainty collapse”术语，但场景是 OOD 不确定性，不是共享主干参数合流。
- **没有找到**直接测量“共享主干联合训练过程中成员相似度上升/功能多样性衰减”的论文；S1' 的合流发现目前只能由 Repulsive 的定性陈述 + Fort 的子空间相似性 + 本课题实测共同支撑，不能声称已有文献复现了同一现象。

## 5. 组 3：尺度稳定的去相关损失形式与 λ 设定

### 5.1 检索式与来源

1. 本地：`query "decorrelation redundancy reduction"`、`"cosine similarity diversity loss"` → 无直接命中（DSN、流量模型等弱相关）。
2. OpenAlex：`title_and_abstract.search:"correlation penalty" AND ensemble` → NCL、Chen & Yao、Semitic NCL 等。
3. OpenAlex：`title_and_abstract.search:"cosine similarity" AND "ensemble diversity"` → 仅 1 条（2026 snapshot ensembles），说明“余弦”在集成惩罚中不是主流术语。
4. OpenAlex：`title_and_abstract.search:"decorrelation" AND ensemble AND loss` → Fort 2019、DeeSCo、InSAR 等；相关性弱。
5. OpenAlex：`title_and_abstract.search:"redundancy reduction" AND ensemble` → 多为无关领域；VICReg/Barlow 不在该检索面内，改用 arXiv 定向核实。
6. 定向：Harangi et al. 2023（MDPI DOI）、Barlow Twins（arXiv:2103.03230）、VICReg（arXiv:2105.04906）、Repulsive（arXiv:2106.11642）。

### 5.2 精读命中

#### (1) Harangi et al. 2023——集成成员输出的 Pearson 相关惩罚（全文，最直接的集成专用先例）

- 题录：Harangi, Baran, Beregi-Kovács & Hajdu, *Composing Diverse Ensembles of Convolutional Neural Networks by Penalization*, Mathematics 2023, 11(23):4730, DOI `10.3390/math11234730`（MDPI，OA，19 页）。
- 形式（第 5–6 页）：
  - 式 (1)：Pearson 相关
    $$\varrho(X,Y)=\frac{\sum_{i=1}^K(X_i-\bar X)(Y_i-\bar Y)}{\sqrt{\sum_i(X_i-\bar X)^2\sum_i(Y_i-\bar Y)^2}}.$$
  - 对每个样本 $n$，$C^{(n)}$ 是成员 softmax 输出向量 $F_1^{(n)},\ldots,F_N^{(n)}$ 与 $-d^{(n)}$ 的 $(N+1)\times(N+1)$ 相关矩阵（相关系数在**类别维 $L$** 上计算）。
  - 式 (2)：$E=\frac1M\sum_{n=1}^M[\sum_{i=1}^N\sum_{j=i}^N C_{ij}^{(n)}+N\sum_{i=1}^{N+1}C_{i,N+1}^{(n)}]$。
  - 式 (3)：$\mathcal L_f=\mathcal L+\lambda E$，$\lambda\ge0$。
- 动机（第 3–4 页）：NCL 的简单相关惩罚被 **Pearson 相关惩罚**替代；既能支持“正确决策的相关”，又能惩罚“同时错在同一类”；使用交叉熵而非 MSE；成员在架构层拼接后**同时训练**。
- λ 实测（第 7–10 页，表 1–5）：扫描 $\lambda\in\{0,0.5,1,5\}$。
  - ISINI/AlexNet：λ=1 最好 0.9650（λ=0 为 0.9543），λ=5 降到 0.9617。
  - CIFAR-10/AlexNet：λ=1 最好 0.6683（λ=0 为 0.6471），λ=5 为 0.6646。
  - CIFAR-10/VGG16：λ=1 最好 0.8931（λ=0 为 0.8743），λ=5 为 0.8892。
  - DR 医学集：λ=0.5 最好 0.6707（λ=0 为 0.6584），λ=1 为 0.6662，λ=5 为 0.6599。
  - ISIC 皮肤集：λ=1 最好 0.7355（λ=0 为 0.7011），λ=5 为 0.7011。
  - 原文结论：λ 过高会牺牲精度，应像学习率一样调参；λ=1 附近最稳，λ=5 普遍过强。
- **关键边界**：相关是在**每个样本的类别维（softmax 向量长度 L）**上算的，再对样本平均；不是“batch 内跨样本的相关”。对于本课题的二分类单分数（L=1 或 2），该轴退化/仅取 ±1，不能直接照搬。它提供的是「用 Pearson 归一化取代 NCL 乘积」的集成专用先例；若用于二分类，应把相关轴改为 **batch 内成员分数向量（长度 B）**。
- 证据等级：全文 PDF（MDPI OA），式 (1)–(3) 与表 1–5 已回渲染页/MinerU 文本复核。

#### (2) Barlow Twins 2021——batch 内归一化互相关（全文 HTML）

- 题录：Zbontar, Jing, Misra, LeCun & Deny, *Barlow Twins: Self-Supervised Learning via Redundancy Reduction*, ICML 2021；arXiv:2103.03230。
- 式 (1)（§2.1）：$\mathcal L_{BT}=\sum_i(1-\mathcal C_{ii})^2+\lambda\sum_i\sum_{j\ne i}\mathcal C_{ij}^2$。
- 式 (2)（§2.1）：$\mathcal C_{ij}=\frac{\sum_b z^A_{b,i}z^B_{b,j}}{\sqrt{\sum_b(z^A_{b,i})^2}\sqrt{\sum_b(z^B_{b,j})^2}}$；实现中先对每个单元做 batch 均值中心化与标准差归一化，再算相关。
- λ：**$5\times10^{-3}$**；原文称对 λ 不很敏感。
- 尺度行为：分母是各单元 batch 范数，**尺度不变**；这是“成员/单元向量相关惩罚”的直接可移植形式。跨域来源（自监督表征），不是集成成员惩罚。

#### (3) VICReg 2022——std hinge + 协方差惩罚（全文 HTML）

- 题录：Bardes, Ponce & LeCun, *VICReg: Variance-Invariance-Covariance Regularization for Self-Supervised Learning*, ICLR 2022；arXiv:2105.04906。
- 式 (5)（§4.1）：$s(Z,Z')=\frac1n\sum_i\|z_i-z'_i\|_2^2$（不变项）。
- 式 (1)–(2)：$v(Z)=\frac1d\sum_j\max(0,\gamma-S(z^j,\epsilon))$，$S(x,\epsilon)=\sqrt{\mathrm{Var}(x)+\epsilon}$，$\gamma=1$（方差 hinge）。
- 式 (3)–(4)：$C(Z)=\frac1{n-1}\sum_i(z_i-\bar z)(z_i-\bar z)^T$，$c(Z)=\frac1d\sum_{i\ne j}[C(Z)]_{ij}^2$（协方差项）。
- 式 (6)–(7)：$\ell=\lambda s(Z,Z')+\mu[v(Z)+v(Z')]+\nu[c(Z)+c(Z')]$；默认 **λ=25, μ=25, ν=1, γ=1, ε=1e-4**；附录 D.4：λ=μ>1、ν<μ 时收敛稳定。
- **对本任务最关键的原文**（§4.1 与附录）：若把方差 hinge 直接写成方差（而非标准差），梯度在 $x\approx\bar x$ 时**接近 0**，导致坍缩；用标准差可避免。这正是父代理诊断的“成员重合处梯度消失”在表征正则中的对应问题与修法。
- 尺度行为：VICReg **不**把协方差除以 std；它用方差 hinge 把每维 std 保持在 γ 以上，从而约束协方差的量级。它是“尺度受控”而非“严格尺度不变”。

#### (4) Repulsive Deep Ensembles 2021——RBF 核排斥（全文）

- 见 §4.2(1)。形式：$k(w_i,w_j)=\exp(-\frac1h\|w_i-w_j\|^2)$，$R=(\sum_j k)^{-1}\sum_j\nabla k$，$\beta>0$，带宽 median heuristic。
- 特点：尺度自适应（median heuristic），直接针对“成员收敛到同一函数”；但它是**排斥项**，不是相关惩罚，且作用于权重/函数而非 batch 内分数。

#### (5) Shui et al. 2018——NCL 惩罚在深度集成的 λ=0.1（全文，预印本）

- 见 §3.2(4)。形式未归一化，λ=0.1；在成员重合处惩罚梯度消失，**不能作为尺度稳定方案**，只能作为“深度集成已有人用 NCL 惩罚”的先例。

### 5.3 组 3 结论

- **集成专用、尺度归一化的最直接先例是 Harangi et al. 2023 的 Pearson 相关惩罚**：$L_f=L+\lambda E$，λ≈0.5–1 最稳，λ=5 过强；它明确用 Pearson 取代 NCL 的简单乘积。但它的相关轴是样本内的类别维，二分类单分数需改为 batch 内跨样本相关。
- **batch 内跨样本归一化相关的最成熟形式是 Barlow Twins 式 (2)**：分母为各向量 batch 范数，尺度不变，λ=5e-3；可直接把“成员分数向量”当作被相关对象。
- **抗坍缩最完整的是 VICReg**：std hinge（不是方差）+ 协方差项；默认 λ=25, μ=25, ν=1；原文明确警告“用方差会让梯度在均值附近消失并导致坍缩”。这与本课题的消失梯度诊断同型，可作为修法的跨域依据。
- **Repulsive Deep Ensembles** 提供 ensemble-specific 的抗合流项（RBF 排斥 + median heuristic），但不是相关惩罚，不能直接替代去相关项。
- **λ 设定没有跨任务常数**：Harangi λ≈0.5–1（λ=5 过强）；Barlow λ=5e-3；VICReg λ=25/μ=25/ν=1；Rosen λ(t)=1/i 或 100/(Nt) 或交叉验证；NCL λ∈[0,1] 且问题相关。第三轮必须重新按本数据/本损失尺度标定，不能沿用先导的 λ=2.0。

## 6. 裁决输入表（只登记与推荐，不裁决）

| 项 | 结论 | 关键出处 | 证据等级 |
|---|---|---|---|
| (a) Rosen 正源形式与可得性 | 正源为 *Ensemble Learning Using Decorrelated Neural Networks*, Connection Science 8(3–4):373–384, 1996, DOI `10.1080/095400996116820`。形式：$E_j=\sum_p[(y_p-f_j)^2+\sum_{i<j}\lambda(t)d(i,j)(y_p-f_i)(y_p-f_j)]$；顺序训练、只与此前成员配对；$\lambda(t)$ 常数/衰减/交叉验证。 | Crossref/OpenAlex/S2(DBLP)/NCL 参考文献；作者预印本第 4、6 页 | 题录已核实；全文为作者预印本（非出版社版），已入库 |
| (a) 与 NCL 的关系 | NCL 的 $p_i=\sum_{j\ne i}P_{ij}$（目标参照）且同时训练；NCL 分类式用 $F$ 后 $p_i=-e_i^2$，惩罚梯度在成员重合处为零。Rosen 顺序、目标参照，$\partial P/\partial f_j=-(y-f_i)$ 在重合处不消失；但 $P$ 未归一化，0–1 域恒非负。 | 两篇全文公式；本笔记代数推导 | 全文公式已核；关系为推论，非原文陈述 |
| (b) NCL 尺度问题先例与修法 | 有：Brown & Wyatt 2003 给出 $p_i=-e_i^2$、$2(M-1)/M$ 因子、$\lambda=\gamma[2(M-1)/M]$、二阶导上界；Chen & Yao 2009/2010 指出 λ=1 无正则且 CV 调 λ 不能解决过拟合；Wang et al. 2010 指出分类需换歧义项。**没有文献明说“重合处梯度恒零”**；最接近的是 Brown 式 (4)/(8)，本笔记据此推出。 | Brown 2003 全文；Chen & Yao 摘要；Wang 2010 全文 | Brown/Wang 全文；Chen & Yao 仅摘要 |
| (c) 最有谱系的尺度稳定形式 | 推荐**batch 内 Pearson 相关惩罚**（成员分数向量长度 B，按成员 std 归一化；可加 VICReg 式 std hinge/ε 防分母坍缩）。集成专用先例：Harangi et al. 2023，$L_f=L+\lambda E$，λ≈0.5–1（λ=5 过强）。跨域归一化形式：Barlow Twins 式 (2)（λ=5e-3）；抗坍缩：VICReg（λ=25, μ=25, ν=1，std 而非方差）。 | Harangi 2023 第 5–6 页式 (1)–(3)、表 1–5；Barlow Twins §2.1 式 (1)–(2)；VICReg §4.1 式 (1)–(7) | Harangi 全文+渲染页；Barlow/VICReg 全文 HTML；均为外部候选，未入库 |
| (c) 备选：集成本身抗合流 | Repulsive Deep Ensembles (NeurIPS 2021) 用 RBF 核排斥（median heuristic），明确针对成员收敛到同一 mode；是排斥项而非相关惩罚。 | arXiv:2106.11642；NeurIPS 2021 官方摘要页 | 全文+题录已核实 |
| (d) 组 2 谱系锚点 | Repulsive 2021 最强；Fort 2019 支持独立初始化/子空间相似但未测联合训练；MOD 2020 提供 uncertainty collapse；**没有**直接测量共享主干联合训练成员相似度上升的论文。 | 各组精读条目 | 见各条 |
| (d) 多头自集成现状 | BatchEnsemble、TabM 等共享主干/多头方法靠随机初始化与适配器差异，未加显式成员相似度惩罚；无现成多头去相关超参可抄。 | 本地 BatchEnsemble/TabM 笔记 | 全文笔记（已入库） |

## 7. 检索式与 URL 清单（便于复核）

### 本地

- `uv run --project scripts/literature_search --locked python -m scripts.literature_search status --json`
- `... build --json`（失败：`EmbeddingBackend.__init__() got an unexpected keyword argument 'device'`）
- `... build --lexical-only --json`（成功）
- `... query "<q>" --scope paper --mode lexical --top-k 8 --json --no-auto-build`，q ∈ {negative correlation learning, ensemble diversity regularization, decorrelation redundancy reduction, member similarity joint training ensemble, cosine similarity diversity loss}

### 在线

- Crossref: `https://api.crossref.org/works?query.bibliographic=<title>&rows=...`
- Crossref DOI: `https://api.crossref.org/works/10.1080/095400996116820`, `/10.1109/3477.809027`, `/10.1007/3-540-44938-8_27`
- OpenAlex: `https://api.openalex.org/works?filter=title_and_abstract.search:<phrase>&per-page=...&sort=cited_by_count:desc`
- OpenAlex DOI: `https://api.openalex.org/works/https://doi.org/<doi>`
- S2: `https://api.semanticscholar.org/graph/v1/paper/DOI:10.1080/095400996116820?fields=...`（成功）；检索端点多次 429
- Google Scholar: `scholar lookup "negative correlation learning penalty gradient vanishing ensemble" --json --limit 8`
- 开放副本：`https://web.archive.org/web/20060208215016id_/http://www.cs.ucla.edu:80/~rosen/rosen/decor.ps`
- Brown 2003: `https://profgavinbrown.github.io/files/brown2003mcs.pdf`
- Wang 2010: `http://staff.ustc.edu.cn/~hchen/papers/IJCNN2010-NCL.pdf`
- Shui 2018: `https://arxiv.org/pdf/1802.07881`
- Repulsive 2021: `https://arxiv.org/pdf/2106.11642`
- MOD 2020: `https://ojs.aaai.org/index.php/AAAI/article/download/5849/5705`
- Harangi 2023: `https://mdpi-res.com/d_attachment/mathematics/mathematics-11-04730/article_deploy/mathematics-11-04730.pdf`
- Barlow Twins: `https://ar5iv.labs.arxiv.org/html/2103.03230`
- VICReg: `https://ar5iv.labs.arxiv.org/html/2105.04906`

## 8. 阻塞与未完成

1. **Rosen 出版社版不可得**：Taylor & Francis 付费墙；本地为作者预印本，页码与期刊版不同。若正文必须引期刊页码，需用户提供出版社 PDF。
2. **DBLP API 被 Anubis 拦截**：用 S2 的 DBLP 外部键与 DBLP 网页检索结果替代；未直接读到 DBLP JSON。
3. **Semantic Scholar 频繁 429**：部分检索改用 OpenAlex/Crossref/Google Scholar；未取得 S2 的完整引用网络。
4. **本地向量通道未运行**：`build` 默认模式因 `EmbeddingBackend.__init__() got an unexpected keyword argument 'device'` 失败；只建了词法索引。本轮所有本地检索均为 lexical，向量召回缺失。该错误属工具代码与依赖接口不匹配，未修改工具代码。
5. **Chen & Yao 2009/2010 仅摘要**：IEEE 付费墙，未取得全文；其“λ=1 无正则/过拟合/CV 不能解决”只能作摘要级证据。
6. **DeCov 2016 未取得全文**：下载失败，未纳入证据；若需要更早的协方差去相关谱系，可补。
7. **Harangi 2023 的相关轴**：是样本内类别维（softmax 向量长度 L），不是 batch 内跨样本；二分类单分数不能直接照搬，需改写为 batch 内成员分数相关。
8. **未发现直接测量共享主干联合训练成员相似度上升的论文**：S1' 的合流现象目前只有 Repulsive 的定性陈述 + Fort 的子空间相似性 + 本课题实测支撑，不能写成“文献已复现”。

## 9. 文件变更（不 commit）

- 新增：`.Codex/docs/2026-10-21-去相关机制定向检索/task_plan.md`
- 新增：`.Codex/docs/2026-10-21-去相关机制定向检索/notes.md`（本文件）
- 新增：`raw/papers/methodology/1996-Rosen-去相关神经网络集成.pdf`
- 新增：`wiki/papers/methodology/1996-Rosen-去相关神经网络集成.md`
- 修改：`wiki/papers/methodology/INDEX.md`（新增 Rosen 条目并更新本节篇数）
- 未修改：`thesis/` 下任何文件；未 commit。
