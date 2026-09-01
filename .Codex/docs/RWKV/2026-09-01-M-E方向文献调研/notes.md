# 调研笔记（逐条落盘，不事后补写）

格式：每条记录查询式/来源、路径、证据等级、关键位置、与 M-E 的关系。

---

## 0. 索引状态

- `status --json`：schema v3，built 2026-08-31T11:56Z，note_count=1459，papers=528（chunks 8004），stale 未报。
- raw/papers/ 下已有相关原件：`methodology/2022-Gorishniy-On-Embeddings-Numerical-Features-Tabular.pdf`（PLR 原始论文，已有全文笔记）、`2106.11959v5.pdf`（FT-Transformer，已被 8-28 审计核对）、`2012.06678v1.pdf`（TabTransformer，同上）。

## 1. 本地混合检索（4+4 个查询，--scope paper --mode hybrid）

查询式：FiLM 调制 / 超网络条件化 / 实体历史条件表示 / 条件嵌入门控 / 概念漂移 / 冷启动 / 时间切分表格基准 / MoE 门控。命中且与本任务直接相关的本地全文级笔记：

| 论文 | 本地笔记 | 与 M-E 的关系 |
| --- | --- | --- |
| Gorishniy 2022 PLR（arXiv:2203.05556） | wiki/papers/methodology/2022-Gorishniy-表格深度学习数值特征嵌入.md | M-E 的 ε_t 基（PLE）唯一直接来源 |
| TabReD（ICLR 2025，arXiv:2406.19380v4） | wiki/papers/methodology/2025-Rubachev-TabReD工业级时间切分表格基准.md | 时间切分下只有「数值嵌入＋集成」两类技术存活（第 7 页表 3、第 8 页图 1）；检索增强/长训练配方失效 |
| Cai & Ye ICML 2025（arXiv:2502.20260v2） | wiki/papers/methodology/2025-Cai-时间漂移下深度表格方法的极限.md | 时间漂移病灶拆成训练滞后＋验证偏置；表示层需显式时间嵌入补周期/趋势 |
| RevIN（ICLR 2022） | wiki/papers/methodology/2022-Kim-RevIN可逆实例归一化.md | 实例自身统计量归一化对抗训练-测试分布差异（Eq.1-3 第 4-5 页；4.2.2 第 8 页明确论证全局统计量不能缩小差异）——弱点 (b) 的正面处理方式 |
| FATA-Trans（CIKM 2023） | wiki/papers/methodology/ft-mechanisms/2023-Zhang-FATA-Trans字段时间感知序列表格.md | 已占用「历史统计作为字段」大类（物理第 4-6 页公式 4-10）；其历史统计未证明严格过去 |
| TabR（ICLR 2024） | wiki/papers/methodology/tree-inspired/2024-Gorishniy-TabR检索增强表格网络.md | 检索式条件化；规模硬门（300 万样本 18h）＋TabReD 上失效，已被本仓库裁决不进候选 |
| TabM（2025 Gorishniy） | wiki/papers/methodology/2025-Gorishniy-TabM参数高效集成.md | 参数高效集成——TabReD 上存活的第二类技术；候选 A 素材 |
| BatchEnsemble（2020 Wen） | wiki/papers/methodology/2020-Wen-BatchEnsemble秩一因子高效集成.md | 秩一因子集成，TabM 的机制内核 |
| Bartos 2016（USENIX Security） | wiki/papers/methodology/2016-Bartos-优化不变表示检测未见恶意软件变种.md | 安全域先例：按袋归一化获得对变种/漂移的不变表示——候选 B 素材 |
| Ilse 2018 注意力 MIL | wiki/papers/methodology/2018-Ilse-基于注意力的深度多示例学习.md | 集合聚合结构层备选素材 |
| Engram（DeepSeek 2026，arXiv:2601.07372） | wiki/papers/deepseek/Engram-条件记忆模块.md | 条件记忆查表：O(1) 哈希查表无运行时演化状态，但为 LLM 尺度设计 |

本地**没有**的关键原件：FiLM（Perez 2018）、条件 BatchNorm（de Vries 2017）、LHUC（Swietojanski & Renals）、Hypernetworks（Ha 2017）、Galanti & Wolf 超网络模块化理论、冷启动元嵌入系。→ 需联网下载核验。

## 2. 仓库既有裁决（过程文档，非文献）

- `.Codex/docs/RWKV/2026-08-28-FT新机制五篇文献审计/审计结论.md`：**M-E（状态条件化 PLR）在 8-28 审计中已被排为第 4 位候选**，判词「tokenizer 大类高度拥挤」「精确新颖性低」「备选骨干适配」，且预注册退出条款：「若实验只证明普通 PLR 有效而状态条件化无额外增益，则不保留我方改造」。已占用边界清单：线性 token（FT 2021）、单层非线性（SAINT 2021）、PLE/PLR/周期（Gorishniy 2022）、分位数离散（TabFormer/FATA-Trans/STEP）、静态动态字段+时间感知（FATA-Trans）、KAN/Matérn（MKAFT 2025）、跨行列注意力（Fieldy 2024）。
- `.Codex/docs/RWKV/2026-08-31-M-E门作用域源年量化.md`（实测，target_reads=0）：门恒零片段 55.43%；有激活片段的实体仅 2.22%；验证集 20 个正实体中门可达 13 个（65%），350/13509 负实体可达；门输入判别力上界为 C00 的 6.3%（c 的实体 AP 0.043 vs C00 0.684）。**M-E 全部增益空间＝13 个正实体与 350 个负实体的重排，与实现质量无关。**
- `RWKV第三章恢复卡.md`：C01（BER）目标年实体 AP +0.0566 过门；C10（CEM）-0.0390 否决；下一候选只按预注册 LSPR23 证据选择。主基座 FT-Transformer d=192、3 层、8 头，裸骨干 924,283 参数，CEM 曾加 150,913（16.33%）。CEM 死因之一：检查点 99.5% 是每实体记忆状态（794 MiB），状态无界增长。
- LSPR23 实体历史诊断：恶意实体流链中位 112 vs 良性 2；多片段实体 2.22% 覆盖 96.09% 流。

## 3. 联网阶段：新下载原件（全部 arXiv 合法来源，已核对公式与物理页码）

全部入库 `raw/papers/methodology/`，sha256 见下；每篇均已 pdftotext 后回原文核对。

### 3.1 FiLM（Perez, Strub, de Vries, Dumoulin, Courville，AAAI 2018，arXiv:1709.07871）【全文级】

- 原件：`raw/papers/methodology/2018-Perez-FiLM-Visual-Reasoning.pdf`，sha256 `765acea6…cdcd363`
- 物理第 2 页式 (1)(2)：`γ_{i,c}=f_c(x_i)`、`β_{i,c}=h_c(x_i)`；`FiLM(F_{i,c}|γ,β)=γ_{i,c}·F_{i,c}+β_{i,c}`。
- 物理第 3 页 Related Work 三条统一论断（逐字核对）：
  1. 拼接条件信息等价于 feature-wise conditional bias，「equivalent to FiLM with γ = 1」；
  2. 门控式（LSTM 门、SE 网络）「amounts to a feature-wise, conditional scaling, restricted to between 0 and 1」，即 σ 限幅门是 FiLM 的受限特例；
  3. 「FiLM can be viewed as using one network to generate parameters of another network, making it a form of hypernetwork (Ha, Dai, and Le 2016)」。
- **与 M-E 的精确关系**：M-E 的 `γ_θ(s_e)=σ(MLP(s_e))∈(0,1)` 是「独立条件输入 + σ 限幅 + 标量共享」的条件缩放，作用于 PLE 位移支路；线性 token 支路系数恒为 1。按 FiLM 第 3 页分类法，M-E 落在 FiLM 家族「限幅缩放特例」子类中（γ 退化为标量、β≡0、仅作用于一条支路）。M-E 不是逐字换名（FiLM 无 PLE 基、无实体历史条件、无 1[c≥1] 硬门），但其条件化算子本身无新颖性可主张。

### 3.2 LHUC（Swietojanski, Li, Renals，IEEE/ACM TASLP vol.24 no.8, 2016，arXiv:1601.02828）【全文级】

- 原件：`raw/papers/methodology/2016-Swietojanski-LHUC-Unsupervised-Adaptation.pdf`，sha256 `d9732801…3423b4`
- 物理第 3 页式 (3)：`h^{l,s}_j = ξ(r^{l,s}_j) ∘ ψ_j(w_j^T x + b_j)`；振幅函数 ξ: R→R+「typically a sigmoid with range (0, 2)」。
- **与 M-E 的关系**：按说话人（=分组身份）用 σ 门重标定隐藏单元振幅，正是「按实体身份门控表示分量」的 2016 年先例；M-E 把「说话人码」换成实体历史统计 s_e、把逐单元门换成标量门。振幅门控条件化这一算子已被占用十年。

### 3.3 条件 BatchNorm（de Vries et al.，NeurIPS 2017，arXiv:1707.00683）【全文级】

- 原件：`raw/papers/methodology/2017-deVries-Conditional-BatchNorm-Modulating-Visual.pdf`，sha256 `ee492d47…bcc774`
- 式 (4)(5)（正文方法节）：`Δβ=MLP(e_q)`、`Δγ=MLP(e_q)`；`β̂_c=β_c+Δβ_c`、`γ̂_c=γ_c+Δγ_c`——用 MLP 从条件嵌入预测归一化仿射参数的增量。FiLM 的直接前身；「小 MLP 从条件向量出仿射参数」的构造已发表。

### 3.4 Hypernetworks（Ha, Dai, Le，ICLR 2017，arXiv:1609.09106）【全文级，仅取定义】

- 原件：`raw/papers/methodology/2016-Ha-HyperNetworks.pdf`，sha256 `cc7057fe…610b3e`
- 用一个网络为另一个网络生成权重的原始定义来源；FiLM 第 3 页明言 FiLM 属于其特例。

### 3.5 Galanti & Wolf（NeurIPS 2020，arXiv:2002.10006）【全文级】——理论更厚的条件化形式

- 原件：`raw/papers/methodology/2020-Galanti-Wolf-Modularity-of-Hypernetworks.pdf`，sha256 `3bc73488…279c25`
- 物理第 5 页 Theorem 1：对 Sobolev 类 `W_{r,m}` 达到 ε 逼近的网络类参数量下界 `Ω(ε^{-m/r})`（sigmoid/tanh/clipped-ReLU 均满足条件）。
- 物理第 6 页 Theorem 2：嵌入法（把条件 e(I) 拼进主网络 q(x,e(I))）在 `W_{1,m}` 上要求主网络复杂度 `Ω(ε^{-(m1+m2)})`——随 x 维与 I 维之和指数；Theorem 3 推广到 e 输出维依赖 ε 的情形。
- 同节结论：超网络可为每个条件实例 I 提供复杂度 `O(ε^{-m1/r})` 的独立逼近器（模块性），嵌入法不具备。
- **判读**：这是「条件化表示」方向已知最硬的理论工具——超网络式条件化与拼接/嵌入式条件化之间存在可证明的参数复杂度分离。M-E 的标量门是最弱的超网络（生成 0 维参数）；若要理论厚度，同方向的自然升级是「s_e 经低秩超网络生成分词器位移向量」，可直接引用 Thm 1–3 作表达力依据。代价：参数与漂移敏感性同升，见报告。

### 3.6 Meta-Embedding 冷启动（Pan et al.，SIGIR 2019，arXiv:1904.11547）【全文级】

- 原件：`raw/papers/methodology/2019-Pan-Meta-Embedding-Cold-Start-CTR.pdf`，sha256 `0491344d…c0039`
- 方法：对从未出现过的 ID（=无历史实体），不用零向量，而是用基于内容特征的嵌入生成器（MAML 式两阶段：冷启动损失＋热身损失联合训练，方法节第 2–3 页，图 2）产出初始嵌入。
- **对 M-E 弱点 (a) 的对应**：文献处理「条件信号缺失」的标准做法是**学习先验替代硬零**；M-E 的 `1[c≥1]` 硬门（55.43% 片段恒零、35% 验证正实体不可达）在该文献线里对应「trivial cold-start with zero/random init」这一被改进的基线。

### 3.7 DAIN（Passalis et al.，2019，arXiv:1902.07892，IEEE TNNLS 2020 版前身）【全文级】

- 原件：`raw/papers/methodology/2019-Passalis-DAIN-Deep-Adaptive-Input-Normalization.pdf`，sha256 `83338bed…14ae21`
- 物理第 2–3 页式 (1)–(9)：三层自适应输入归一化——移位 `α(i)=W_a a(i)`（式 3，a(i) 为实例摘要，式 2）、缩放 `β(i)`、门控 `γ(i)=σ(W_c c(i)+d)`，端到端训练（式 9）；明言全局 z-score 是其特例。
- **对弱点 (b) 的对应**：条件量由「当前实例自身摘要」给出而非跨数据集校准常数——与 RevIN 同一原则。M-E 的 `s_e` 归一化分母 `log(1+C)`、`log(1+D)` 是源年冻结常数，正是该文献线明确反对的「全局统计量」构造。

### 3.8 ICLAD（Wei & Armanfard，McGill/Mila，arXiv:2603.19497v1，2026-03-19）【全文级】——最近的结构近邻

- 原件：`raw/papers/methodology/2026-ICLAD-InContext-Tabular-Anomaly-Detection.pdf`，sha256 `ef5adc19…5ac827`
- 物理第 9 页「FiLM Label Conditioning」：`x̃ = (1 + γ(c)) ⊙ x + β(c)`，γ、β 为线性映射；**「Unlabeled samples correspond to c = 0, for which FiLM reduces to the identity transformation」**——条件缺失时恒等退化，与 M-E 零门退化命题同构且已发表。
- **判读**：表格异常检测中「FiLM 条件化＋条件缺失恒等退化」的组合已于 2026-03 发表（条件是标签嵌入而非实体历史）。M-E 的零门退化「理论」在近邻文献中只是实现约定，不构成理论贡献。

## 3.9 MinerU 复核（2026-09-01，主进程当轮更正后执行）

主进程更正：读 PDF 一律用 `mineru-open-api extract`，报告中的公式对比必须来自 MinerU 提取的 LaTeX。已对全部 6 处承载公式的页面用 `--pages` 重新提取（输出在会话 scratchpad，文件名含页范围），**逐条与第 3.1–3.8 节的 pdftotext 读数比对，全部一致，无需更正**：

| 论文 | 提取范围 | MinerU LaTeX 核验结果 |
| --- | --- | --- |
| FiLM | p2–3 | 式(1) `\gamma_{i,c}=f_c(x_i), \beta_{i,c}=h_c(x_i)`；式(2) `FiLM(F_{i,c}|γ,β)=\gamma_{i,c}F_{i,c}+\beta_{i,c}`；第 3 页三条统一论断逐字一致 |
| LHUC | p3 | 式(3) `h_j^{l,s}=\xi(r_j^{l,s})\circ\psi_j(w_j^{l\top}x+b_j^l)`；ξ: R→R+，「typically a sigmoid with range (0, 2)」 |
| CBN | p4 | 式(4) `\Delta\beta=MLP(e_q), \Delta\gamma=MLP(e_q)`；式(5) `\hat\beta_c=\beta_c+\Delta\beta_c, \hat\gamma_c=\gamma_c+\Delta\gamma_c`；零均值小方差初始化恢复原模型的动机段逐字一致 |
| Galanti-Wolf | p5–6 | Thm 1 `N_f=\Omega(\epsilon^{-m/r})`；Thm 2 `N_q=\Omega(\epsilon^{-(m_1+m_2)})`；Thm 3 `N_q=\Omega(\epsilon^{-\min(m,2m_1)})`；**新增：Thm 4（Modularity of Hypernetworks，第 6 页）显式陈述 `N_g=O(\epsilon^{-m_1/r})`**——比此前引用的第 4 节文字更精确，报告引用升级为 Thm 2/3 vs Thm 4 |
| DAIN | p2–3 | 式(1) `\tilde x_j=(x_j-\alpha^{(i)})\oslash\beta^{(i)}`；式(2)–(5) 摘要与线性移位/缩放；式(6)(7) `\gamma^{(i)}=\mathrm{sigm}(W_c c^{(i)}+d)` 门控——此前写「式1–9」，精确应为式(1)–(9)中的 (1)–(7) 承载本论断 |
| ICLAD | p9 | `\tilde x=(1+\gamma(c))\odot x+\beta(c)`；「Unlabeled samples correspond to c = 0, for which FiLM reduces to the identity transformation」逐字一致 |

## 3.10 主进程新证据（07147ad，朱第三章 MinerU 重读）对本调研判据的影响

- 朱表 3-7（印刷页 42）交互项（该文档计算）：BUPT-CNN `I=+3.80`、ET-BERT `I=+3.30`；DS 单独在 CNN 上仅 `+0.90`——**单机制弱不构成否决，判据是交互项**。
- 朱的「定理 1」实为两行一阶泰勒（式 3.24–3.25），无条件、无误差界；**「理论深度」不是参照论文的实际标准**，M-E 的形式化程度不低于 DS。
- 真实差距是「两机制是否共享数学框架」：朱的 DS/RGO 同属一个 Stackelberg 双层问题的内/外层；M-E×BER 目前无共享框架，交互为正无先验机制理由（07147ad 第 4.3 节，设计推理非实验结论）。
- **对本调研结论的影响**：原推荐（换候选）建立在「理论厚度」判据上，该判据已被 07147ad 以 MinerU 证据修正；重新裁决见调研报告修订版。

## 4. 联网检索记录（摘要级，不支撑论断）

- 查询 1：`FiLM feature-wise modulation tabular deep learning conditional numerical embedding 2024 2025`（WebSearch）。结论：FiLM 与数值嵌入两条线在表格 DL 中基本分离，最近交点即 ICLAD（已升级为全文级）；另见 FiLM-Ensemble（OpenReview 7vDt4_ulNyB，摘要级，FiLM 做隐式集成——佐证 FiLM 与集成两线可融合，未用于本论断）。
- 查询 2：`entity history conditioned feature embedding network intrusion detection transformer gating`（WebSearch）。结论：NIDS 文献覆盖 transformer 嵌入、门控、流分组三构件，但无「实体历史条件化特征嵌入」精确近邻——与 8-28 审计的饱和检索结论一致。TASNN（PMC12920788，摘要级）为最近组合，未下载。
- 本地查询共 8 组（见第 1 节），全部 `--scope paper --mode hybrid`。
