# 第四章实体矩 AP 原创性审计笔记

- **日期**：2026-08-13
- **路线**：`RESEARCH_ROUTE=RWKV`
- **用途**：逐查询、逐全文记录来源、证据位置、纳入／排除理由、与候选关系及 Zotero 状态。

## 证据记录模板

### 来源：待填写

- 书目信息：
- 稳定标识：
- 原论文页：
- 全文状态：
- 仓库原件：
- 结构化笔记：
- Zotero 状态：
- 关键位置：
- 原文支持的事实：
- 与候选的关系：
- 被占用点：
- 仍可主张点：
- 纳入／排除理由：
- 待办：

## 查询台账

| 查询式 | 来源 | 日期 | 新增命中 | 结果与下一步 |
| --- | --- | --- | --- | --- |
| `"stochastic optimization" "average precision" SOAP` | NeurIPS 正式论文页 | 2026-08-13 | SOAP | 全文核验 AP 复合目标、逐正样本状态与“有偏随机梯度估计”原文。 |
| `"finite-sum coupled compositional" average precision SOX` | PMLR 正式论文页 | 2026-08-13 | FCCO／SOX | 全文核验 AP、`p`-norm push 与列表排序的通用 FCCO 归纳。 |
| `"multi-instance" stochastic pooling AUC` | PMLR 正式论文页 | 2026-08-13 | MIDAM | 全文核验朴素小包非线性池化偏差与逐包状态跟踪。 |
| `"size-invariance" loss multi-object` | PMLR 正式论文页 | 2026-08-13 | Size-Invariance | 全文核验大对象支配分解、等对象指标与损失。 |
| `"learned-norm pooling" p` | arXiv 原文与本地原件 | 2026-08-13 | Learned-Norm Pooling | 复用已核验全文；确认 `p=1+softplus(ρ)` 保证 `p≥1`。 |
| `"generalized mean pooling" "average precision"` | CVF、Wiley 正式页与原文 | 2026-08-13 | Revaud 2019；Yao 2023 | 两篇全文直接占用“GeM／可学习幂池化＋直接 AP”宽泛组合。 |
| `"Horvitz-Thompson" "average precision"` | ACM DOI、作者全文 | 2026-08-13 | statAP | 全文核验 AP 评价中的两阶段不等概率抽样、HT 组成估计与广义比率。 |
| `"multiple-instance" "average precision" "stochastic pooling" optimization` | 原论文页定向检索 | 2026-08-13 | 无完全同构命中 | 在本轮有界检索中未定位同时包含实体 `p` 阶矩、包内无放回估计、实体均匀设计权重与 AP 训练的原文；不外推为“不存在”。 |

## 当前事实边界

1. 固定同一个 `p>0` 时，`x↦x^{1/p}` 在 `x≥0` 上严格递增，因此 `S_e` 与 `M_e` 同序；这是恒等层面的排序不变性，不是算法创新。
2. 条件于固定参数和固定 `p`，对实体内有限集合等概率无放回抽 `K` 条，样本均值是完整实体 `p` 阶矩的无偏估计；这是标准有限总体抽样事实。
3. 上述无偏性只覆盖线性矩本身。把随机矩放入非线性、跨实体耦合的 AP 代理，通常有 `E[L(\hat M)]≠L(M)`，梯度无偏也需另证。
4. 外层逆概率加权恢复实体均匀测度是标准设计型抽样事实；是否能与具体 SOAP／SOX 状态变量共同形成无偏或一致优化器，需要按其目标分解方式逐式核验。

## 本地候选与分桶证据检查点

### 输入文档

- `.Codex/docs/RWKV/2026-08-05-RWKV第四章早期决策与公平基线设计.md`：历史最优停止候选，仅用于确认第四章路线已发生变化；不作为当前实体 AP 机制证据。
- `.Codex/docs/RWKV/2026-08-13-第四章实体AP提升文献与候选矩阵.md`：已有 17 篇全文证据矩阵，核心包括 SOAP、FCCO／SOX、MIDAM、Size-Invariance、Learned-Norm Pooling、多示例学习及领域近邻。
- `.Codex/docs/RWKV/2026-08-13-第四章实体流数分桶诊断实施与运行报告.md`：真实单种子筛选诊断，四格复现零差，覆盖 `47,115` 个实体、`752` 个正实体。
- `.Codex/docs/RWKV/2026-08-13-第四章实体均匀训练与直接实体AP优化方案册.md`：当前冻结 Q0 方案；本审计需修正其抽样与梯度表述，不启动该方案。

### 分桶结果及允许解释

| LSPR24 实体流数桶 | 实体数 | 正实体数 | `C11−C00` 实体 AP | `C11−C00` `DR@4%FPR` |
| --- | ---: | ---: | ---: | ---: |
| `1–2` | `26,770` | `103` | `+0.123948` | `+0.048544` |
| `3–10` | `10,894` | `206` | `+0.239138` | `+0.276699` |
| `11–100` | `4,993` | `319` | `+0.137851` | `+0.172414` |
| `101–1000` | `3,316` | `84` | `−0.322915` | `−0.238095` |
| `1001+` | `1,142` | `40` | `−0.302212` | `−0.325000` |

- 允许：现有 C11 的跨年度实体排序具有强烈长度异质性，且长实体方向反转。
- 不允许：把方向反转归因于训练测度错配、随机池化偏差或 `p`；该运行没有针对这些因果解释做单变量干预。

### 当前方案中新增识别的数学风险

1. **先抽流再编码的依赖风险**：第三章 C11 含因果前缀跨流聚合。若 `s_{ef}` 在抽样后用删减历史重新计算，则它不是完整实体中固定的有限总体值；`K^{-1}Σs_{ef}^p` 不再自动无偏估计完整历史下的 `M_e`。无偏结论只适用于先在完整因果历史上定义固定 `s_{ef}(θ)`，再从这些固定值抽样，或另行证明删减历史编码器的估计性质。
2. **代理非单调不变**：固定共同 `p>0` 时，`S_e` 与 `M_e` 对精确 AP 同序；SOAP 的平方铰链／平滑代理依赖分数差和尺度。用 `M_e` 训练与用 `S_e` 或其 logit 训练不等价，不能由精确 AP 同序推出代理目标或梯度相同。
3. **嵌套非线性偏差**：对 `M_e` 的无偏估计代入 AP 的比率复合代理后，目标值与梯度通常有偏。SOAP／SOX 的状态跟踪与收敛分析不能简化成“每步梯度无偏”。
4. **抽样术语**：若每步按 `ρ_e` 有放回抽实体，权重 `v_e/ρ_e` 对应 Hansen–Hurwitz 型估计；若按固定大小无放回抽实体，HT 必须使用一阶包含概率 `π_e`，而不是单次抽取概率 `q(e)`。按标签池自归一化会成为 Hájek 型比率估计，通常有限样本有偏。
5. **可学习 `p`**：在固定参数无关抽样、固定支持和可微条件下，`∂_p \hat M=K^{-1}Σs^p\log s` 对 `∂_pM` 无偏；这仍不推出完整 AP 代理的 `p` 梯度无偏。`0<p<1` 且分数可达零时，模型参数梯度可能奇异；需保证分数下界或约束 `p≥1`。

## 待关闭问题

- `p` 是固定超参数、全局可学习标量，还是依实体／批次变化；三者的同序与梯度结论不同。
- 分数 `s_{ef}` 的值域是否严格非负、是否允许零；`p<1` 和零分数会影响 `∂s^p/∂p=s^p log s` 的定义与支配条件。
- 实体抽样是固定大小无放回设计、泊松抽样，还是有放回按 `q(e)` 抽样；HT 权重应使用包含概率 `π_e`，不能把每次抽取概率 `q(e)` 与包含概率混用。
- SOAP／SOX 实现是否以带偏但一致的小批量状态估计换取可扩展性；不得把论文的收敛保证误写为逐步梯度严格无偏。

## 逐篇全文证据卡

### Qi 等 2021：SOAP

- 书目：Qi Qi, Youzhi Luo, Zhao Xu, Shuiwang Ji, Tianbao Yang. *Stochastic Optimization of Areas Under Precision-Recall Curves with Provable Convergence*. NeurIPS 2021, 1752–1765。
- 稳定来源：<https://proceedings.neurips.cc/paper/2021/hash/0dd1bc593a91620daecf7723d2235624-Abstract.html>。
- 原件：`raw/papers/methodology/ranking/2021-Qi-SOAP-AUPRC-NeurIPS.pdf`，14 个物理页，SHA256 `99fbcb99c4b0a052f14f56bb6f3e845548ed1440a59c76d7d05d513a8e3c8ec2`。
- 关键位置：物理第 3 页公式（1）与公式（2）—（4）；第 4 页逐正样本状态；第 5 页算法 1 和假设 1；第 6 页定理。
- 核心裁决：SOAP 的即时估计在算法原文中被称为“有偏随机梯度估计”；论文证明状态跟踪下的收敛，不是每步无偏。
- 结构化笔记：`wiki/papers/methodology/ranking/2021-Qi-SOAP直接优化AUPRC.md`。Zotero：`MHNH9QBM`。

### Wang 与 Yang 2022：FCCO／SOX

- 书目：Bokun Wang, Tianbao Yang. *Finite-Sum Coupled Compositional Stochastic Optimization: Theory and Applications*. ICML 2022, PMLR 162:23292–23317。
- 稳定来源：<https://proceedings.mlr.press/v162/wang22ak.html>。
- 原件：`raw/papers/methodology/ranking/2022-Wang-FCCO-SOX-ICML.pdf`，26 页，SHA256 `902dbdcac4f36b7a683243cbb1dec460525a35775ca4650c4cea526a50a3b62f`。
- 关键位置：第 1 页公式（1）；第 2 页 AP、`p`-norm push、ListNet、ListMLE、NDCG 实例；第 2–4 页插件式小批量偏差与 SOX 状态。
- 核心裁决：实体 AP 在结构上已落入 FCCO；本候选另增包内矩估计，形成更深的嵌套随机复合，不能直接继承 SOX 结论而省略新误差层。
- 结构化笔记：`wiki/papers/methodology/ranking/2022-Wang-FCCO与SOX.md`。Zotero：`XJVCGLYL`。

### Zhu 等 2023：MIDAM

- 书目：Dixian Zhu, Bokun Wang, Zhi Chen, Yaxing Wang, Milan Sonka, Xiaodong Wu, Tianbao Yang. *Provable Multi-instance Deep AUC Maximization with Stochastic Pooling*. ICML 2023, PMLR 202:43205–43227。
- 稳定来源：<https://proceedings.mlr.press/v202/zhu23l.html>。
- 原件：`raw/papers/methodology/multiple-instance/2023-Zhu-MIDAM-Stochastic-Pooling-ICML.pdf`，23 页，SHA256 `3b0b6d177057430dda190132bb5209b373e27c1ec625d94c674964360a657e87`。
- 关键位置：第 3 页池化形式；第 4 页朴素小包平滑最大偏差；第 4–5 页公式（7）—（8）与算法 1；第 6 页定理。
- 核心裁决：“大包随机池化＋逐包状态跟踪”已被占用；其目标是 AUROC，不含实体均匀测度、HT／HH 或 AP。
- 结构化笔记：`wiki/papers/methodology/multiple-instance/2023-Zhu-MIDAM随机池化.md`。Zotero：`N3WQX553`。

### Li 等 2024：Size-Invariance

- 书目：Feiran Li, Qianqian Xu, Shilong Bao, Zhiyong Yang, Runmin Cong, Xiaochun Cao, Qingming Huang. *Size-Invariance Matters: Rethinking Metrics and Losses for Imbalanced Multi-object Salient Object Detection*. ICML 2024, PMLR 235:28989–29021。
- 稳定来源：<https://proceedings.mlr.press/v235/li24bx.html>。
- 原件：`raw/papers/methodology/multiple-instance/2024-Li-Size-Invariance-ICML.pdf`，33 页，SHA256 `2776b9508c5beef3041a7b07bd7809da9b71065583c260aa3e1f58c80e5a4c84`。
- 关键位置：第 3 页公式（3）—（6）；第 4 页公式（7）、（13）—（15）；第 5–6 页公式（16）、命题 4.1 与定理 4.2。
- 核心裁决：“显式拆出大对象支配＋等对象训练”是已有原则；网络实体的测度错配仅可作任务特定实例。
- 结构化笔记：`wiki/papers/methodology/multiple-instance/2024-Li-大小不变多对象损失.md`。Zotero：`6HJZ9IA2`。

### Gülçehre 等 2014：Learned-Norm Pooling

- 书目：Çağlar Gülçehre, Kyunghyun Cho, Razvan Pascanu, Yoshua Bengio. *Learned-Norm Pooling for Deep Feedforward and Recurrent Neural Networks*. ECML PKDD 2014；arXiv:1311.1780v7。
- 原件：`raw/papers/methodology/multiple-instance/2014-Gulcehre-Learned-Norm-Pooling-ECMLPKDD.pdf`，17 页，SHA256 `78be80b3efeb98d442921ba5f7f71a8f33fd0285f17732a1664942da74015ff9`。
- 关键位置：第 3 页公式（3）；第 4 页 `p=1+log(1+exp(ρ))`；第 5 页均值／均方根／最大池化特例。
- 核心裁决：可学习 `p` 的归一化 `Lp` 池化已被占用；论文为保证真正的范数约束 `p≥1`，正好暴露当前 `p>0` 口径的命名过度。
- 结构化笔记：`wiki/papers/methodology/2014-Gulcehre-可学习范数池化Lp单元.md`。

### Revaud 等 2019：AP-GeM

- 书目：Jérôme Revaud, Jon Almazán, Rafael S. Rezende, César Roberto de Souza. *Learning With Average Precision: Training Image Retrieval With a Listwise Loss*. ICCV 2019, 5107–5116。
- 稳定来源：<https://openaccess.thecvf.com/content_ICCV_2019/html/Revaud_Learning_With_Average_Precision_Training_Image_Retrieval_With_a_Listwise_ICCV_2019_paper.html>。
- 原件：`raw/papers/methodology/ranking/2019-Revaud-AP-GeM-ICCV.pdf`，10 页，SHA256 `b16a3fd4c48b7a4cef0eaf8147a730fb31178e6982875a8946361c620aea7e12`。
- 关键位置：第 3–4 页公式（2）—（12）的可微 AP；第 5 页多阶段反传；第 6–7 页 GeM 幂次反传学习与 `GeM (AP)` 结果。
- 核心裁决：这是最直接的机制近邻；“可学习 GeM／`Lp`＋直接列表 AP”已被实质占用。
- 结构化笔记：`wiki/papers/methodology/ranking/2019-Revaud-APGeM图像检索.md`。Zotero 规范条目：`JMWPSGXB`；重复条目：`HYETU4UY`。

### Yao 等 2023：GeM 与 Smooth-AP

- 完整题名：*Learning global image representation with generalized‐mean pooling and smoothed average precision for large‐scale CBIR*。
- 完整作者：Jinliang Yao, Yongqing Li, Bing Yang, Chenrui Wang。
- 期刊：*IET Image Processing* 17(9):2748–2763, 2023。DOI：<https://doi.org/10.1049/ipr2.12825>。
- 用户原件：`/Users/bilibili/Downloads/IET Image Processing - 2023 - Yao - Learning global image representation with generalized‐mean pooling and smoothed average.pdf`。
- 仓库原件：`raw/papers/methodology/ranking/2023-Yao-GeM-SmoothAP-IET.pdf`，16 页，2,771,758 字节，SHA256 `3b9188f6d31a04bf1385dda111fa31a064f8d64666cb66df8adb10c3500adc8d`；`cmp` 返回 0，与用户原件字节一致。
- 许可：PDF 物理第 1 页声明为开放获取的 Creative Commons Attribution-NonCommercial 许可；不在未定位具体版本号时追加“4.0”。
- 关键位置：第 4 页公式（5）GeM；第 5–6 页公式（7）—（12）Smooth-AP；第 8 页表 2；第 14 页局限与结论。
- 核心裁决：文中称 `p` 可训练，却又明言实验经验设为 `p=3.0`，不可把其实验写成已验证“AP 学习 `p`”。但它无疑直接占用“GeM＋Smooth-AP”组合。
- 结构化笔记：`wiki/papers/methodology/ranking/2023-Yao-GeM与SmoothAP图像检索.md`。Zotero 规范条目：`W7FTP9TU`；重复条目：`7CPF6R3Q`。规范条目下现有附件 `ZP36CCDA` 只是 1 页、2,436 字节的元数据摘要 PDF，不是 Wiley 16 页原文；远程附件修复因本地条目未同步而返回 404。

### Carterette 等 2008：statAP

- 书目：Ben Carterette, Virgil Pavlu, Evangelos Kanoulas, Javed A. Aslam, James Allan. *Evaluation Over Thousands of Queries*. SIGIR 2008, 651–658。DOI：<https://doi.org/10.1145/1390334.1390445>。
- 原件：`raw/papers/methodology/ranking/2008-Carterette-statAP-SIGIR.pdf`，8 页，SHA256 `c5ebe7e09014089e3e11a4f85f35566441d34f7e3ad1fbbdf71722a5d8d20f23`。
- 关键位置：第 2 页 AP 表达与两阶段分层抽样；第 2–3 页 HT 组成估计、广义比率 statAP 与包含概率方差。
- 核心裁决：“AP＋不等概率抽样＋HT 组成估计”已有直接评价先例；HT 总量无偏不推出最终比率无偏。
- 结构化笔记：`wiki/papers/methodology/ranking/2008-Carterette-statAP抽样评价.md`。Zotero：`W6DEX8GX`。

## 数学审计草稿

### 共同 `p` 下的排序恒等

令 `s_{ef}≥0`、`p>0` 在所有实体之间共享，`M_e=n_e^{-1}Σ_fs_{ef}^p≥0`，`S_e=M_e^{1/p}`。因为 `x↦x^{1/p}` 在 `[0,∞)` 上严格递增，故对任意实体 `e,e'`：

`S_e<S_{e'}` 当且仅当 `M_e<M_{e'}`，且它们保留相等关系。

因此在**同一平局处理规则**下精确实体 AP 完全相同。这是单调变换恒等式。若 `p` 按实体不同，结论失效；若 `p` 每个训练步更新但该步内共享，该步内仍成立。代理损失依赖分数差尺度，故不随严格单调变换保持。

### 包内简单随机无放回抽样

对当前模型与 `p` 条件化，令 `X_{ef}=s_{ef}^p`、`K_e=min(K,n_e)`，从实体 `e` 的 `n_e` 个固定值中等概率无放回抽 `K_e` 个：

`\hat M_e=K_e^{-1}Σ_{f∈A_e}X_{ef}`。

则

`E[\hat M_e∣θ,p]=M_e`，

`Var(\hat M_e∣θ,p)=(1-K_e/n_e)S_{X,e}^2/K_e`，

其中 `S_{X,e}^2=(n_e-1)^{-1}Σ_f(X_{ef}-M_e)^2`。`K_e=n_e` 时方差为 0。这是标准有限总体抽样事实，不是新算法。

### `p` 与模型参数梯度的精确条件

对有限固定总体，若：（1）抽样设计与 `θ,p` 无关；（2）每个 `s_{ef}(θ)` 是抽样前已定义的同一个完整历史分数；（3）各项导数存在且有限；则对有限和可逐项求导，且

`∂_pM_e=n_e^{-1}Σ_fs_{ef}^p log s_{ef}`，

`∇_θM_e=n_e^{-1}Σ_fp s_{ef}^{p-1}∇_θs_{ef}`，

相应样本均值梯度分别对这两个完整矩梯度无偏。当 `s=0`、固定 `p>0` 时，`s^p log s` 可用连续延拓定义为 0；但 `0<p<1` 且 `s` 可到 0 时，`∂s^p/∂s=p s^{p-1}` 可奇异或不存在。因此应约束 `p≥1` 或保证严格正的分数下界；前者更稳妥，也与 Learned-Norm Pooling 一致。

若 `p=φ(α)`，对参数 `α` 的梯度再乘 `φ'(α)`。若包内包含概率依赖 `θ` 或 `p`，最简洁的无偏条件不再满足：可以把当前包含概率作为设计常数停梯度，对逐项导数做 HT 估计；若要对随机抽样设计本身求导，必须增加得分函数校正，不能直接自动微分离散选择。

### 从矩到 AP 的非线性断点

`∇\hat M_e` 无偏不意味 `∇F(\hat M_1,…,\hat M_N)` 对 `∇F(M_1,…,M_N)` 无偏，因为 AP 代理包含成对非线性、比率或平滑排名。精确 AP 本身对非平局分数局部分段常数，不能按普通光滑损失直接优化。SOAP 与 SOX 用状态跟踪控制复合偏差；MIDAM 也用状态处理包内非线性。因此本候选若只将 `\hat M` 插入现有 AP 代理，只能声称可计算的有偏随机近似，不能声称整体梯度无偏。

### 外层实体提议分布

- 固定样本量无放回设计：若一阶包含概率为 `π_e>0`，均匀实体均值 `N^{-1}Σ_eh_e` 的 HT 估计是 `N^{-1}Σ_{e∈A}h_e/π_e`。
- 有放回独立按提议 `ρ(e)>0` 抽 `B` 次：` B^{-1}Σ_b h_{E_b}/[Nρ(E_b)]` 是 Hansen–Hurwitz 型估计，不应称为 HT。
- 如果对权重再用批内总权重归一化，得到 Hájek／自归一化重要性估计，通常有限样本有偏。
- AP 的正样本外层与全实体内层有不同目标测度，需分别写正实体提议 `ρ_+` 和全实体提议 `ρ`，不能用一个含混的 `q(e)` 直接口头表述。

### 因果跨流编码的目标身份问题

第三章 C11 的流分数依赖实体因果前缀。若先抽 K 流再用删减的历史重新编码，抽中流的 `s_{ef}` 就不是完整实体有限总体中的固定值，上述无偏定理无法应用。可行边界只有：

1. 先对完整因果历史编码，再抽损失位置，反传保留所需前缀；
2. 冻结上游并预计算完整历史分数；
3. 明确把“抽样上下文目标”定义为新的优化对象，不再声称它无偏估计原 C11 完整历史目标。

## Zotero 与人工下载状态

- 规范条目已导入：SOAP `MHNH9QBM`，FCCO／SOX `XJVCGLYL`，MIDAM `N3WQX553`，Size-Invariance `6HJZ9IA2`，AP-GeM `JMWPSGXB`，Yao 2023 `W7FTP9TU`，statAP `W6DEX8GX`。
- 待人工清理：AP-GeM 重复顶层条目 `HYETU4UY`；Yao 2023 重复顶层条目 `7CPF6R3Q`；误解析的 2013 无关条目 `6DRLF6F6`、`DY4ARPC2`。本任务未授权删除，故保留可恢复状态。
- Yao 规范条目下的现有 1 页元数据 PDF 不是正式全文；完整原文已由 `raw/papers/methodology/ranking/2023-Yao-GeM-SmoothAP-IET.pdf` 作为仓库事实源。
- **人工下载清单：空。** Yao 2023 正式全文已由用户提供，本轮用于裁决的 8 篇核心论文均有完整本地原文。
