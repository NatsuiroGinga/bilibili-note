# 第四章引用缺口补齐：执行笔记

> 逐篇落盘；每完成一项立即追加，不等任务结束。

## 待办

- [x] Liu & Yao 1999 题录核实
- [x] Liu & Yao 1999 开放副本获取
- [x] Keskar 2017 题录核实与下载
- [x] Fort et al. 2019 题录核实与下载
- [x] Brown et al. 2005 题录与可得性
- [x] MinerU 转换 ×3
- [x] wiki 笔记 ×3
- [x] INDEX 更新
- [x] 汇总表

## 记录

### 1. Liu & Yao 1999（NCL 正源）

**查询式与 API**

- Crossref：`query.bibliographic=Simultaneous training of negatively correlated neural networks in an ensemble`。
- 返回（`total-results` 第一条即目标）：DOI `10.1109/3477.809027`；题名
  *Simultaneous training of negatively correlated neural networks in an ensemble*；
  作者 Yong Liu、Xin Yao；容器
  *IEEE Transactions on Systems, Man and Cybernetics, Part B (Cybernetics)*；
  卷 29、期 6、页 716–725；1999 年；类型 journal-article。
- Semantic Scholar（`paper/DOI:10.1109/3477.809027`）返回同一题录，
  `externalIds.DBLP = journals/tsmc/LiuY99`，`venue = IEEE Trans. Syst. Man Cybern. Part B`；
  **据此交叉核到 DBLP 记录键**（DBLP 网页本身被 Anubis 人机校验拦截，未能直接取 JSON）。
- OpenAlex（`works/https://doi.org/10.1109/3477.809027`）返回
  `biblio.volume=29, issue=6, first_page=716, last_page=725`，源刊名与 Crossref 一致。

**修正待验证假设**：题名完全成立；出处不是 **Part A**，而是
**IEEE Transactions on Systems, Man and Cybernetics, Part B (Cybernetics)**。
任何正文引用必须写 Part B，卷期页 29(6):716–725。

**开放副本**

- Semantic Scholar `openAccessPdf.url =
  http://www.cs.bham.ac.uk/~xin/papers/published_tsmcB_dec99.pdf`（status GREEN）。
- 直接访问该 URL 已变为伯明翰大学新站首页（返回 HTML，非 PDF）。
- Wayback Machine 快照可用：
  `https://web.archive.org/web/20200709160753id_/https://www.cs.bham.ac.uk/~xin/papers/published_tsmcB_dec99.pdf`；
  返回 `application/pdf`，10 个物理页；PDF 元数据标题为
  “Simultaneous training of negatively correlated neural networks in an ensemble -
  Systems, Man and Cybernetics, Part B, IEEE Transactions on”，Creator “IEEE Copyright”，
  与 Crossref 题录一致。属作者主页副本，不是不可信镜像。
- 落盘：`raw/papers/methodology/1999-Liu-NegativeCorrelationLearning.pdf`；
  SHA-256 `de7e5d3d74471bb161a672c146a6c80e119eb8a0ca21484408a002bdbe88cfe3`。
- MinerU：`extract -l en --ocr -o /tmp/ch4-refgap-extract/liu/`，10/10 页完成；
  关键公式已回 PDF 物理页视觉复核（第 716–724 页）。

**关键读数（物理页码）**

- 第 716 页：误差负相关时平均最有效、正相关时几乎无收益（Introduction 首段）。
- 第 717 页：式 (7) 偏差–方差–协方差分解；方差按 $1/M$ 衰减而协方差有限。
- 第 718 页：式 (8) 误差函数 $\frac1N\sum[\frac12(d-F_i)^2+\lambda p_i]$；
  $0\le\lambda\le1$；式 (9)(10)(11) 三种 $p_i$；式 (12) 仅对无噪声式 (10) 给出梯度。
- 第 719 页：Table I，无噪声回归 $\lambda\approx0.9$ 时 MSE 最小；
  $E_{var}$ 随 $\lambda$ 升、$E_{cov}$ 随 $\lambda$ 降，协方差变负。
- 第 720 页：$A_{10}$ 的 28 个成员间相关系数中 21 个为负；
  独立训练全部为正；式 (25) 相关系数定义。
- 第 721 页：有噪声条件 $0<\lambda\le0.75$ 优于独立训练；测试值中 $\lambda=0.5$ 最优。
- 第 723 页：Mackey–Glass 用 $\eta=0.25$、$\lambda=1.0$；
  分类实验（Australian credit card）用 $\eta=0.1$、$\lambda=1.0$，式 (11)。
- 第 724 页：Table X，CELS($\lambda=1.0$) 四个成员正确集交集 113，
  独立训练为 146，说明成员确实分工；但简单平均的测试误差与独立训练相近，
  winner-take-all 才明显改善。

**与本课题先导的接口**

- 先导惩罚式 $p_i=(s_i-\bar s)\sum_{j\ne i}(s_j-\bar s)$ 对应论文式 (11)
  （$F(n)$ 取简单平均即 $\bar s$），形式一致；论文的分类实验输出是 1-of-$m$
  编码、我们的是 sigmoid 分数，属任务化适配。
- 先导 $\lambda$ 预声明为 {0.5, 2.0}。论文明确 $0\le\lambda\le1$，全部实验
  $\lambda\le1$；**$\lambda=2.0$ 超出论文范围，无文献依据**，只能记为任务化外推。
  先导文档已自述“λ 数值无文献依据”，此处补充论文边界。
- 论文只对式 (10)（无噪声、目标 $d$ 已知）给出式 (12) 梯度；
  式 (11)（用集成均值替代 $d$）没有给显式梯度，我们由自动微分实现。
- 论文证据是回归 MSE 与一个小规模分类集，不含年度漂移、共享主干或 F1/AUC；
  不能直接支撑“NCL 在年度稀缺年提升 F1”，只能支撑机制来源与惩罚项形式。

### 2. Keskar et al. 2017

**查询式与 API**

- arXiv API：`id_list=1609.04836,1912.02759`（后者的核实见下一篇）。
- 返回 `arxiv:1609.04836v2`，题名 *On Large-Batch Training for Deep Learning:
  Generalization Gap and Sharp Minima*；作者 Nitish Shirish Keskar、Dheevatsa Mudigere、
  Jorge Nocedal、Mikhail Smelyanskiy、Ping Tak Peter Tang；
  `arxiv:comment = Accepted as a conference paper at ICLR 2017`；
  published 2016-09-15，updated 2017-02-09。**ID 假设成立。**
- 下载 `https://arxiv.org/pdf/1609.04836v2`，16 个物理页。

**落盘**

- `raw/papers/methodology/2017-Keskar-大批量与尖锐极小.pdf`
- SHA-256 `bcd5497ace654f4dc354a32cfe68cfdf5dc88e823150726d3e6a9cfa680557ad`
- MinerU `extract -l en`，16/16 页；关键论证已回物理页复核（第 1–9 页）。

**关键读数（物理页码）**

- 第 1 页摘要：大批量收敛到尖锐极小、泛化更差；小批量收敛到平坦极小。
- 第 2 页：泛化差距在较小网络上也可达 5%。
- 第 3 页主观察框：尖锐极小有大量大的正特征值；平坦极小的特征值小；
  MDL 解释“低精度可描述 ⇒ 泛化更好”。
- 第 4 页：Table 1/2；明确排除过拟合/过训练解释。
- 第 5 页：式 (3)(4) 定义 $(\mathcal C_\epsilon,A)$-锐度；
  $\epsilon$ 控制邻域盒，$p=100$ 维随机子空间。
- 第 6 页：Table 3/4 显示 SB 与 LB 锐度差 1–2 个数量级；
  尖锐极小并非各方向都陡，只在约 5% 的低维子空间陡。
- 第 7 页：批量阈值；梯度噪声把迭代推出尖锐极小的吸引域；
  warm-start 实验；LB 倾向停在初始点附近的极小，SB 走得更远。
- 第 9 页：SB 与 LB 解到初始点的距离比约 3–10 倍；结论与开放问题。

### 3. Fort, Hu & Lakshminarayanan 2019

**修正待验证假设**：任务给的 arXiv `1912.02759` **不是本文**。
arXiv API 返回 `1912.02759v2 = “Duty to Warn in Strategic Games”`（Naumov & Tao，AAMAS 2020）。
按题名检索得到正确 ID **`1912.02757v2`**：*Deep Ensembles: A Loss Landscape Perspective*；
作者 Stanislav Fort、Huiyi Hu、Balaji Lakshminarayanan；
published 2019-12-05，updated 2020-06-25；PDF 标注 `arXiv:1912.02757v2 [stat.ML] 25 Jun 2020`。
**arXiv 预印本，无会议/期刊题录。**

**落盘**

- `raw/papers/methodology/2019-Fort-深度集成的损失面视角.pdf`
- SHA-256 `e3dff57975a369960b68c486738e9df6943b5950d4173f789e1e2b45bb61df6e`
- MinerU `extract -l en`，15/15 页；关键论证已回物理页复核（第 1–8 页）。

**关键读数（物理页码）**

- 第 1 页摘要：随机初始化探索完全不同的模式；同一轨迹及其子空间内的函数在预测空间聚成一类。
- 第 2 页：Deep Ensembles = $M$ 个不同初始化重复最小化；脚注 3 把 “mode” 定义为唯一函数。
- 第 3 页：实验设置；函数空间分歧率 = 预测标签不同的样本比例。
- 第 4 页：Fig 2/3；同一轨迹内高度相似，不同初始化之间显著不同；
  两个初始化的权重向量几乎正交，预测差异与任意两解相当。
- 第 5 页：四种子空间采样；子空间函数留在各自轨迹邻域，不与另一初始化重叠。
- 第 6 页：diversity–accuracy 平面；独立初始化（红星）优于全部子空间方法。
- 第 7 页：集成与子空间互补；SVHN 上 JS 散度：独立运行 0.384、
  轨迹内 0.153、随机子空间 0.155、rank-5 PCA 高斯 0.087、对角高斯 0.034。
- 第 8 页：结论明确“随机初始化轨迹探索不同模式”解释 deep ensembles；
  未来方向包括**显式去相关**与**参数高效隐式集成**。

### 4. Brown et al. 2005

**查询式与 API**

- Crossref：`query.bibliographic=Diversity creation methods in ensemble systems Brown 2005 Information Fusion`。
- 返回：DOI `10.1016/j.inffus.2004.04.004`；题名
  *Diversity creation methods: a survey and categorisation*；
  作者 Gavin Brown、Jeremy Wyatt、Rachel Harris、Xin Yao；
  *Information Fusion* 6(1):5–20；issued 2005-03；Elsevier。
- Semantic Scholar 同一 DOI：`externalIds.DBLP = journals/inffus/BrownWHY05`，
  但它标注的 open access PDF
  `http://www.cs.bham.ac.uk/~nah/bibtex/papers/brown04survey.pdf` 实测 301→307，
  最终重定向到伯明翰大学学院主页，**不是 PDF**。
- OpenAlex：`oa_status = closed`，`any_repository_has_fulltext = false`；
  仅列出 CiteSeerX 的 submittedVersion 记录
  （`10.1.1.101.7806`、`10.1.1.5.8636`、`10.1.1.67.2144` 等），均无 `pdf_url`。
- CiteSeerX 访问 301 到 Wayback 后返回 429；Manchester 旧链接 404。

**结论**：题录已核实；**当前未找到可用开放副本，按付费墙登记，仅题录**。
建议文件名（若用户后续取得）：`raw/papers/methodology/2005-Brown-集成多样性创建方法综述.pdf`。
阻塞：需要用户通过机构订阅或出版社页面手动下载；取得 PDF 后再执行 MinerU 转换与
`wiki/papers/methodology/2005-Brown-集成多样性创建方法综述.md` 笔记。

## 汇总表

| 篇目 | 状态 | 题录核实 API | 稳定标识 | SHA-256 前 8 位 | 笔记路径 |
|---|---|---|---|---|---|
| Liu & Yao 1999 NCL | **全文入库**（10 页） | Crossref + Semantic Scholar（DBLP 键）+ OpenAlex | DOI `10.1109/3477.809027` | `de7e5d3d` | `wiki/papers/methodology/1999-Liu-负相关学习NCL.md` |
| Keskar et al. 2017 | **全文入库**（16 页） | arXiv API | arXiv `1609.04836v2`（ICLR 2017） | `bcd5497a` | `wiki/papers/methodology/2017-Keskar-大批量训练与尖锐极小.md` |
| Fort, Hu & Lakshminarayanan 2019 | **全文入库**（15 页，ID 已修正） | arXiv API | arXiv `1912.02757v2`（预印本） | `e3dff579` | `wiki/papers/methodology/2019-Fort-深度集成的损失面视角.md` |
| Brown et al. 2005 | **仅题录 + 阻塞**（付费墙） | Crossref + Semantic Scholar（DBLP 键）+ OpenAlex | DOI `10.1016/j.inffus.2004.04.004` | — | 无全文笔记；INDEX 已登记 |

## 关键发现

- **Liu & Yao 的出处原假设有误**：是 IEEE Trans. SMC **Part B** 29(6):716–725，
  不是 Part A。题名本身正确。
- **Liu & Yao 的 $\lambda$ 范围是 $[0,1]$**：先导预声明的 $\lambda=2.0$ 超出原文范围，
  只能登记为任务化外推；原文全部实验 $\lambda\le1$。
- **Liu & Yao 的分类实验**：成员分工（正确集交集 113 对 146）成立，但简单平均
  未获益，winner-take-all 才明显改善——对本课题固定概率平均的评测合同是直接警示。
- **Fort 的 arXiv ID 原假设有误**：`1912.02759` 是 *Duty to Warn in Strategic Games*；
  正确 ID 是 `1912.02757v2`。
- **Keskar 不是 H2a 的证明**：它给出锐度↔泛化锚点，但 H2a 的成员维度方差缩减
  与 minibatch 梯度噪声不是同一量；H2a 方向仍需 D0 消融，若主张“更平坦”还需
  本课题自己的锐度诊断。
- **Brown 2005 无可用开放副本**：Semantic Scholar 的伯明翰链接已失效，
  OpenAlex 判 closed，CiteSeerX 仅有 submittedVersion 记录且无 PDF。

