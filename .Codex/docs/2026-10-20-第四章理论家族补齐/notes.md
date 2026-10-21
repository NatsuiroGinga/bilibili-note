# 第四章理论家族补齐：核验与执行笔记

## 0. 环境与入口

- 工作树：`/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908`
- MinerU：`/Users/bilibili/.local/bin/mineru-open-api`，`MINERU_TOKEN` 已设置（未回显）。
- 转换中间目录：`/tmp/drebin-extract/`、`/tmp/krogh-extract/`、`/tmp/deepens-extract/`。

## 1. 题录核验（API/官方页，2026-10-21 实测）

### DREBIN

- Crossref `GET https://api.crossref.org/works/10.14722/ndss.2014.23247` 返回 `status: ok`。
- DOI：`10.14722/ndss.2014.23247`（**假设成立**）。
- 题名：*Drebin: Effective and Explainable Detection of Android Malware in Your Pocket*。
- 作者：Daniel Arp, Michael Spreitzenbarth, Malte Hübner, Hugo Gascon, Konrad Rieck。
- 容器：*Proceedings 2014 Network and Distributed System Security Symposium*；event `NDSS 2014`，San Diego, CA；出版者 Internet Society；年份 2014。
- Crossref resource primary URL：<https://www.ndss-symposium.org/ndss2014/programme/drebin-effective-and-explainable-detection-android-malware-your-pocket/>。
- 官方页面内 PDF 链接：<https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf>。

### Krogh & Vedelsby 1995

- 官方 proceedings 页（papers.nips.cc）：
  <https://papers.nips.cc/paper_files/paper/1994/hash/b8c37e33defde51cf91e1e03e51657da-Abstract.html>
- 题名：*Neural Network Ensembles, Cross Validation, and Active Learning*。
- 作者：Krogh, Anders; Vedelsby, Jesper。
- `citation_journal_title`：*Advances in Neural Information Processing Systems*；`citation_volume`：7；
  `citation_publication_date`：**1994**。
- **年份口径说明**：官方页面目录与 `citation_publication_date` 为 1994（NIPS 7 会议年），
  通行引用与任务口径为 **1995**（NIPS 7 论文集出版年）。本笔记按任务要求采用 1995，
  同时在题录节保留 1994 官方字段，避免把两者混写。
- 官方 PDF：<https://proceedings.neurips.cc/paper_files/paper/1994/file/b8c37e33defde51cf91e1e03e51657da-Paper.pdf>。

### Lakshminarayanan et al. 2017

- arXiv API `id_list=1612.01474` 返回 1 条：
  - `arxiv:1612.01474v3`，题名 *Simple and Scalable Predictive Uncertainty Estimation using Deep Ensembles*；
  - 作者 Balaji Lakshminarayanan, Alexander Pritzel, Charles Blundell；
  - `arxiv:comment`：`NIPS 2017`；主分类 stat.ML；v3 更新 2017-11-04。
- **ID 假设成立**。
- NeurIPS 官方 proceedings 页：
  <https://papers.nips.cc/paper_files/paper/2017/hash/9ef2ed4b7fd2c810847ffa5fa85bce38-Abstract.html>；
  官方 camera-ready PDF：<https://proceedings.neurips.cc/paper_files/paper/2017/file/9ef2ed4b7fd2c810847ffa5fa85bce38-Paper.pdf>。

## 2. 下载与落盘

| 论文 | 官方来源 | 本地原件 | SHA-256 |
| --- | --- | --- | --- |
| DREBIN | NDSS 2014 页面链接 `https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf` | `raw/papers/methodology/2014-Arp-DREBIN-AndroidMalware.pdf`（12 页） | `95f3e6273ddf7854a6895e9648b016a30ed64e1d08dd2813823dffaf17bfbf7b` |
| Krogh & Vedelsby | NIPS proceedings `https://proceedings.neurips.cc/paper_files/paper/1994/file/b8c37e33defde51cf91e1e03e51657da-Paper.pdf` | `raw/papers/methodology/1995-Krogh-神经网络集成歧义分解.pdf`（8 页） | `0bc7ab6c6cd2d92309fab02464934114020151ff501e8c3d808131ba995389bf` |
| Lakshminarayanan et al. | NeurIPS 2017 官方 camera-ready `https://proceedings.neurips.cc/paper_files/paper/2017/file/9ef2ed4b7fd2c810847ffa5fa85bce38-Paper.pdf` | `raw/papers/methodology/2017-Lakshminarayanan-DeepEnsembles.pdf`（12 页） | `835735938688c03e411b23ffd8fff172b3b2db3ad33e29e7d6b567c8b94694a0` |

- 三份 PDF 均用 `curl -L` 从官方域名取得，未使用镜像。
- MinerU 正式转换（`mineru-open-api extract ... -l en`）全部 exit 0：
  - `/tmp/drebin-extract/2014-Arp-DREBIN-AndroidMalware.md`
  - `/tmp/krogh-extract/1995-Krogh-神经网络集成歧义分解.md`
  - `/tmp/deepens-extract/2017-Lakshminarayanan-DeepEnsembles.md`
- 转换稿不保留物理分页，页码由 PDF 逐页定位（pypdf）并对公式页渲染复核（pdftoppm，130 dpi）。

## 3. 页码锚点（物理页，已视觉复核）

### DREBIN 页码锚点

- p1：题名、摘要、94% @ 1% FPR 的主摘要陈述。
- pp. 2–3：8 类字符串特征（manifest：硬件组件 S1、请求权限 S2、应用组件 S3、过滤意图 S4；dex：受限 API S5、已用权限 S6、可疑 API S7、网络地址 S8）。
- p3：联合集合 $S:=S_1\cup\cdots\cup S_8$；前缀避免跨集合碰撞；**约 545,000 个不同特征**。
- p4：映射 $\varphi:X\to\{0,1\}^{|S|}$、指示函数；线性 SVM $f(x)=\langle\varphi(x),w\rangle=\sum_{s\in x}w_s$；每条样本仅 $m$ 个非零维。
- p5：解释机制（保留 top-$k$ 权重）、Table I 解释模板、GoldDream 示例（Fig. 3）；数据集段开始。
- p6：最终数据集 **123,453 良性 + 5,560 恶意**；**随机 66%/33% 划分，重复 10 次**；**1% FPR 下检出 94%**；Table II 全数据集 93.90%、Malgenome 95.90%；反病毒引擎 FPR 0–0.3%。
- p7：按家族的检测（平均 93% @ 1% FPR；Gappusin 例外）；未知家族实验（10 个样本使平均检出提高 25% 以上）。
- p9：手机平均约 10 秒、桌面 750 ms、模型约 280 KB。
- p10：静态分析边界（反射、字节码加密、模仿/投毒攻击）。
- p11：数据发布 URL。

### Krogh & Vedelsby 1995 页码锚点

- p1（印刷 231）：摘要与引言；明确 "regression" 语境。
- p2（222 → 实为 232）：式 (1) 集成加权平均；式 (2) 歧义；式 (3)–(4) 成员/集成平方误差；式 (5)–(6) $e(x)=\bar\epsilon(x)-\bar a(x)$。
- p3（233）：式 (7)–(9) 对输入分布取平均；**式 (10) $E=\bar E-\bar A$**；**式 (11) 均匀权重下 $E\le\frac1N\sum_\alpha E^\alpha$**；"increase ambiguity while not increasing individual errors" 的解释。
- p4（234）：Figure 1 方波示例；交叉验证集成。
- p5（235）：Figure 2；**作者自述交叉验证实验结果不稳定**："the curve can take on almost any form"、"it is still unclear under which circumstances one can expect a drop"。
- p6（236）：式 (13) 相关矩阵、式 (14) 二次型权重优化；§5 主动学习开始；**式 (15) $\bar\epsilon(x)\ge\bar a(x)$**。
- p7（237）：Figure 3 主动/被动学习曲线。
- p8（238）：结论与参考文献。

### Lakshminarayanan et al. 2017 页码锚点

- p1：摘要；NIPS 2017 页脚。
- p2：引言与贡献；明确非贝叶斯立场，区分 BMA 与 model combination。
- p3：§2；proper scoring rule；**式 (1) 回归异方差高斯 NLL**。
- p4：§2.3 对抗训练；§2.4 集成训练（全量数据、随机初始化与洗牌、不做 bagging）。
- p5：Algorithm 1；**等权混合 $p(y|\mathbf x)=M^{-1}\sum_m p_{\theta_m}$**；回归混合高斯的均值/方差：
  $\mu_*(\mathbf x)=M^{-1}\sum_m\mu_{\theta_m}(\mathbf x)$，
  $\sigma_*^2(\mathbf x)=M^{-1}\sum_m(\sigma_{\theta_m}^2(\mathbf x)+\mu_{\theta_m}^2(\mathbf x))-\mu_*^2(\mathbf x)$。
- p6：Table 1 回归基准（NLL 多数优于/持平 PBP 与 MC-dropout，RMSE 部分更差）；Figure 1。
- p7：Figure 2 MNIST/SVHN 随集成规模 $M$ 的误差、NLL、Brier；对抗训练在 $M=1$ 后增益下降。
- p8：§3.5 已知/未知类别的熵；ImageNet 表：$M=1$ top-1 22.166%、$M=5$ 19.104%、$M=10$ 18.675%；NLL 0.959/0.809/0.789。
- p9：Figure 6 置信度—准确率；§4 Discussion："two sources of uncertainty"（proper scoring rule 捕捉目标歧义，集成捕捉模型不确定性，对抗训练提供局部平滑）。
- pp. 10–12：致谢与参考文献。

## 4. 第三组：家族 B 可得性登记（不下载）

| 论文 | 题录验证 | PDF 直链/阻塞 | 与成员-年度锚定的关系 |
| --- | --- | --- | --- |
| Aljundi, Chakravarty & Tuytelaars, *Expert Gate: Lifelong Learning with a Network of Experts*, CVPR 2017 | Crossref DOI `10.1109/CVPR.2017.753`；CVF 页面 `citation_title` 与 `citation_publication_date=2017` 一致 | CVF 开放获取直链 HTTP 200：`https://openaccess.thecvf.com/content_cvpr_2017/papers/Aljundi_Expert_Gate_Lifelong_CVPR_2017_paper.pdf`（1,194,049 字节） | 每个新任务新增一个专家，由门控自编码器在测试时按输入选择专家；提供「一任务一成员」的直接先例，但 gating 不读取年度元数据，且实验中任务标识由输入分布隐式推断。 |
| Veniat, Denoyer & Ranzato, *Efficient Continual Learning with Modular Networks and Task-Driven Priors*, 2020 | arXiv API `2012.12631v2`（2020-12-23），题名与三位作者一致；`arxiv:comment` 为 "Accepted as a conference paper at ICLR 2021" | arXiv 直链：`https://arxiv.org/pdf/2012.12631v2` | 模块表示原子技能，学新任务等价于选择复用哪些旧模块、实例化哪些新模块；提供「按任务组合成员」的参数高效路径，但模块选择由任务驱动先验学习，不是显式年度绑定。 |
| Zhang, Lu, Meng, Li, Zhou & Su, *Advancing SMoE for Continuous Domain Adaptation of MLLMs: Adaptive Router and Domain-Specific Loss*, ACL 2025 (Long) | ACL Anthology `2025.acl-long.1290`：题名、6 位作者、pp. 26584–26602、DOI `10.18653/v1/2025.acl-long.1290` 全部由页面 meta 核验 | ACL 直链：`https://aclanthology.org/2025.acl-long.1290.pdf` | 每个新领域在每个 FFN 子层学习一个领域专属 SMoE 模块，配合 DSAL 在推理时选择模块；这是「一领域一成员」的最近设计，但领域指指令领域、基座为 MLLM，且不含年度序列。 |

## 5. 汇总表

| 论文 | 状态 | DOI / arXiv | SHA-256 前 8 位 | 笔记路径 |
| --- | --- | --- | --- | --- |
| Arp et al., DREBIN, NDSS 2014 | 全文入库 + 笔记完成 | DOI `10.14722/ndss.2014.23247` | `95f3e627` | `wiki/papers/methodology/2014-Arp-DREBIN安卓恶意软件静态检测.md` |
| Krogh & Vedelsby, NIPS 7 | 全文入库 + 笔记完成 | 无 DOI；官方页目录 1994、`citation_volume=7`，通行引用 1995 | `0bc7ab6c` | `wiki/papers/methodology/1995-Krogh-神经网络集成歧义分解.md` |
| Lakshminarayanan et al., Deep Ensembles | 全文入库 + 笔记完成 | arXiv `1612.01474v3`；NeurIPS 2017 | `83573593` | `wiki/papers/methodology/2017-Lakshminarayanan-深度集成预测不确定性.md` |
| Aljundi et al., Expert Gate, CVPR 2017 | 仅登记，未下载 | DOI `10.1109/CVPR.2017.753` | — | — |
| Veniat et al., Modular Networks, 2020 | 仅登记，未下载 | arXiv `2012.12631v2`（ICLR 2021） | — | — |
| Zhang et al., SMoE for Domain-IL, ACL 2025 | 仅登记，未下载 | DOI `10.18653/v1/2025.acl-long.1290` | — | — |

## 6. 完成情况

- [x] 三份 PDF 落盘与 SHA
- [x] MinerU 转换与页码复核
- [x] 三份 wiki 笔记（frontmatter 八字段 + 页码锚点）
- [x] INDEX 新增「恶意软件静态特征与二值向量表示」「集成统计与隐式正则」两节
- [x] 家族 B 三篇可得性登记
- [x] 汇总表
