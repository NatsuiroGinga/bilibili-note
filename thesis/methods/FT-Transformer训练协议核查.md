# FT-Transformer 训练协议核查：常数学习率是原论文惯例还是本课题简化

核查日期：2026-09-03
核查范围：原论文 + 6 篇后续/相关工作的训练协议（优化器、学习率、调度器、轮数、早停、批量）
证据规则：PDF 一律用 MinerU（`mineru-open-api flash-extract`）逐页转换，数值与引文回到具体物理页码；
仅有摘要或题录的来源不支撑"该工作如此训练"的论断，本次核查全部数据点均为**本地全文**级证据。

## 一句话结论

**本课题的常数学习率（无 `LambdaLR`/`Cosine`/`OneCycle`/`StepLR`）是原论文 Gorishniy et al. (2021) 的主动设计选择，不是本课题的简化或遗漏**：原文明确把"学习率预热、学习率衰减"与预训练、数据增强、蒸馏并列为**主动排除**的模型无关训练技巧，目的是隔离架构本身的贡献（物理页 5）。本课题引用的默认优化器数值（`AdamW`、`lr=1e-4`、`weight_decay=1e-5`）与官方调参空间几何中位重合的说法（`sqrt(1e-5×1e-3)=1e-4`），均在原论文 Table 12/13（物理页 18）逐字核实为真。检索到的 6 篇后续/相关工作中，**5 篇延续无调度器惯例，只有 1 篇（物理层面偏离 Gorishniy 默认配方的 IoT 攻击检测工作）明确使用了学习率衰减**，且该工作未做消融、不能证明因果。**C00-half 后期震荡不能简单归因于"缺少学习率衰减"这一个变量**：一方面这正是原论文与其研究谱系的共同惯例而非本课题特例，另一方面唯一报告过 FT-Transformer 训练期震荡的文献（Matérn-KAN 工作）把震荡归因于数据集规模过小，而非优化器设置，与本课题的规模、震荡阶段特征均不可比。

---

## 问题一：原论文（Gorishniy et al. 2021）实际训练协议

原件：`raw/papers/methodology/2021-Gorishniy-Revisiting-Deep-Learning-Tabular-Data.pdf`（25 物理页，NeurIPS 2021，arXiv:2106.11959v5）。
笔记：`wiki/papers/methodology/2021-Gorishniy-表格数据深度学习模型再审视.md`（本次已补充训练协议专节）。

| 项 | 原论文取值 | 页码/位置 |
| --- | --- | --- |
| 优化器 | AdamW（TabNet/GrowNet 例外，用原始实现的 Adam） | 物理页 6，§3 "Neural networks" |
| 学习率调度 | **无**——"We do not apply learning rate schedules." | 物理页 6 |
| 该选择的性质 | **主动排除**，与预训练、数据增强、蒸馏、学习率预热/衰减并列，目的是"评估不同模型架构施加的归纳偏置的影响" | 物理页 5，§3 正文 |
| 早停 | patience=16（连续 16 轮验证集无提升后停止），对全部算法统一适用 | 物理页 6 |
| 轮数上限 | 无固定值，由早停决定 | 物理页 6（同上） |
| 批量大小 | 按数据集预先指定（"predefined batch size for all algorithms"），未给出跨数据集统一单一数值 | 物理页 6 |
| 默认优化器数值（Table 12） | `AdamW`、`lr=1e-4`、`weight_decay=1e-5`（对 Feature Tokenizer/LayerNorm/偏置取 0.0） | 物理页 18，§E.2 |
| 调参空间（Table 13，group A，含 HI/Higgs Small） | 学习率 `LogUniform[1e-5,1e-3]`；权重衰减 `LogUniform[1e-6,1e-3]`（两组相同） | 物理页 18，§E.2 |
| 调参空间（Table 13，group B） | 学习率 `LogUniform[3e-5,3e-4]`（更窄） | 物理页 18，§E.2 |

逐字引文（物理页 5）：

> "In our work, we focus on the relative performance of different architectures and do not employ various model-agnostic DL practices, such as pretraining, additional loss functions, data augmentation, distillation, learning rate warmup, learning rate decay and many others."

逐字引文（物理页 6）：

> "For all other algorithms, we use the AdamW optimizer (Loshchilov and Hutter, 2019). We do not apply learning rate schedules. ... we set patience = 16 for all algorithms."

**结论**：常数学习率不是原论文遗漏，而是为了让"架构差异"成为唯一自变量所作的方法论选择；训练时长由早停而非固定轮数控制。这与本课题实现（`thesis/experiments/llm_probe/tools/ch3_ft_transformer_field_token_protocol_a.py` 第 3130 行注释"协议 A 无学习率调度……官方 FT-T 配方无梯度裁剪"）的判断方向一致，且现在有了明确的原文页码支撑。

---

## 问题二：本课题 `lr=1e-4`、`wd=1e-5` 是否为原论文默认值；调参空间巧合是否属实

**两项均核实为真**，证据见上表 Table 12/13（物理页 18）：

1. 本课题代码 `OPTIMIZER_CANDIDATES` 中 "FT-Transformer-论文默认优化器"（`learning_rate=1e-4`、`weight_decay=1e-5`）与 Table 12 逐字相符。Table 12 标题即"Default FT-Transformer used in the main text"，且原文自陈"该配方是'有根据的猜测'，我们没有在其调参上投入太多资源"（物理页 18），即默认值本身不是系统调参的最优解，只是作者的经验估计——本课题沿用它作为"论文默认配方"这一定位准确，但不应把它误读为"论文证明过的最优超参"。
2. 本课题代码注释"官方调参空间 `[1e-5,1e-3]`""`sqrt(1e-5×1e-3)=1e-4`，已知，不是笔误"——核实为真。Table 13 中 group (A) = {CA, AD, HE, JA, HI}，HI 即 Higgs Small，对应官方仓库路径 `output/higgs_small/ft_transformer/tuning/0.toml`（与本课题代码常量 `OFFICIAL_TUNING_SPACE_FILE` 指向的文件一致），其学习率调参区间精确为 `LogUniform[1e-5,1e-3]`，几何中位恰为 `1e-4`，与默认学习率重合。权重衰减调参空间 `LogUniform[1e-6,1e-3]` 的几何中位 `3.1622776601683794e-05`，与代码"官方调参空间对数中位优化器"候选的 `weight_decay` 取值逐位相符。

**需要注意的边界**：这个"几何中位=默认值"的重合，只在 group (A)/HI 这一特定官方 `.toml` 文件上成立；group (B) 的学习率调参空间是更窄的 `[3e-5,3e-4]`，几何中位约 `1.03e-4`，与默认值近似但不精确相等。本课题代码引用的正是 group (A)/HI 对应的文件，因此该巧合的引用是准确的，但不应泛化成"任意官方调参空间的几何中位都等于默认学习率"。

---

## 问题三：后续/相关工作的训练协议对照表

检索路径：本地 `raw/papers/`、`wiki/papers/` 已有笔记（TabM、TabR、SAINT）→ 新增全文核验（XTab、TabTransformer、Matérn-KAN、electronics IoT）→ 本地混合文献检索确认无遗漏候选。Zotero MCP 本次连接失败（`Connection refused`，本地 Zotero 应用未运行），未能通过语义检索补充候选，该检索通道缺口予以披露。

| 工作 | 年份 | 是否用 FT-Transformer 作骨干/基线 | 优化器 | 学习率 | 调度器 | 轮数/早停 | 批量 | 证据等级与页码 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **本课题** | — | 是（当前骨干） | AdamW | `1e-4` 常数 | **无**——`ch3_ft_transformer_field_token_protocol_a.py` 全文搜索 `LambdaLR`/`Cosine`/`OneCycle`/`StepLR`/`ReduceLROnPlateau`/`lr_scheduler` 零命中（本次复核确认）。**注意此为该文件范围内的结论，非全仓库**：仓库内其他模型（DistilBERT 基线、RWKV 筛选、GRANDE 树集成等）确实使用 `CosineAnnealingLR`/`LambdaLR`，本课题并非整体排斥调度器，只是 FT-Transformer 这一具体训练工具未使用 | 早停（配置见协议 A） | 见配置 | 本地全文（代码） |
| Gorishniy et al. 2021（原论文） | 2021 | 是（提出者） | AdamW | `1e-4`（Table 12 默认） | **无**（物理页 6 明文排除） | patience=16，无固定轮数上限 | 按数据集预设，未给统一值 | 本地全文，物理页 5/6/18 |
| XTab（Zhu et al.，ICML 2023） | 2023 | 是（骨干即 FT-Transformer） | AdamW | `1e-4`（预训练与微调两阶段相同，明确"Following Gorishniy et al. 2021"） | **无**（全文零命中"schedul"） | Light: 固定 3 epoch；Heavy: patience=3，轮数上限设为无穷；FTT-best: patience=20 | 128（两阶段固定） | 本地全文，物理页 5/6 |
| TabM（Gorishniy et al.，ICLR 2025） | 2025 | 否（MLP 集成，非 FT-Transformer，但同一研究谱系） | AdamW | 调参空间 `LogUniform[1e-4,5e-3]`；官方代码默认 `0.002` | **无**（物理页 18 明文"不使用学习率调度"），另加全局梯度裁剪 `1.0` | patience=16，无固定轮数上限 | 按数据集预设 | 本地全文，既有笔记页 18（第 D.2 节） |
| TabTransformer（Huang et al.，2020） | 2020 | 否（架构独立，早于 FT-Transformer 一年，非逐字段数值 Token） | AdamW | 常数（原文明文"a constant learning rate was applied throughout"），调参空间 `[1e-6,1e-3]` | **无** | patience=15 | 未见统一数值 | 本地全文，物理页 10 |
| Matérn-KAN（Zhou & Chen，IEEE Access 2025） | 2025 | 是（直接改造 FT-Transformer 特征标记器；基线 FT-T） | **Adam**（非 AdamW，偏离原论文） | `1e-4`（初始值，与原论文默认同量级） | 未提及（全文零命中 schedul/warmup/cosine/decay rate/gamma） | patience=16 | 2048 | 本地全文，物理页 7 |
| **electronics IoT（Li et al.，Electronics 2026）** | 2026 | 是（IoT 攻击检测应用） | AdamW | `1e-3`（比原论文默认高一个数量级，落在 Table 13 调参空间上界） | **有**——"learning rate decay"（未披露具体机制：步长、系数、触发条件均未说明） | 早停（未给出耐心值） | 2048 | 本地全文，物理页 7/10 |
| TabReD（Rubachev et al.，2025） | 2025 | 否（基准论文，DL 方法含 FT-Transformer 类模型，非专属骨干） | AdamW | 未在正文重新列出（"沿用 Gorishniy et al. (2024)"，即 TabM 一系的协议） | 未见新增说明，随 TabM 协议同为无调度器 | 早停（同 TabM 协议） | 未在正文单列 | 本地全文，物理页 6（既有笔记同步核验） |

**结构与超参偏离原论文默认值的工作单独标注**：Matérn-KAN 用朴素 Adam 而非 AdamW；electronics IoT 的 `d_token=64`、`n_layers=4`、`lr=1e-3` 均偏离 Gorishniy 2021 的 `d_token=192`、`n_layers=3`、`lr=1e-4`——这两篇是"用 FT-Transformer 但自行调整了配方"的工作，不是"照搬默认值"的工作。

**已排除的候选**：`3712285.3759853.pdf`（"FT-Transformer: Resilient and Reliable Transformer with End-to-End Fault Tolerant Attention"，UC Riverside/USF）经核实是容错计算领域的同名撞车论文（Fault-Tolerant Transformer），与表格深度学习的 Feature Tokenizer Transformer 无关，未纳入本次统计。

---

## 核心判断：常数学习率是这一系列工作的常规做法，还是本课题的简化

**是这一系列工作（尤其是 Gorishniy/Rubachev 团队的原生谱系）的常规做法，不是本课题的简化。**

统计口径：本次核查覆盖的 7 篇工作（含本课题）中，**5 篇（本课题、Gorishniy 2021、XTab、TabM、TabTransformer）明确无学习率调度器**，**2 篇（Matérn-KAN、TabReD）未在可读到的正文中提及调度器细节但也未明确使用**，**仅 1 篇（electronics IoT）明确使用了学习率衰减**。Yandex 团队的原生谱系（Gorishniy 2021 → XTab → TabM → TabReD）内部高度一致：AdamW + 无调度器 + patience=16 早停，是一条贯穿多篇论文、跨越 2021 至 2025 年的稳定传统，且这一传统在 Gorishniy 2021 中有明确的方法论理由（隔离架构贡献），并非无意识的默认选择。唯一的例外 electronics IoT 论文同时也偏离了原论文的结构超参（`d_token`、`n_layers`）与默认学习率取值，说明它是"重新设计了一套配方"而非"在 Gorishniy 默认配方基础上加一个调度器"，不能作为"应该给 Gorishniy 默认配方加调度器"的证据。

**该震荡是否可归因于缺少学习率衰减：证据不支持这一简单归因，理由分三层：**

1. **本课题的做法与原论文及其研究谱系一致，不是"偏离常规"的简化**——如果"缺少调度器"本身就会系统性导致后期震荡，那么 Gorishniy 2021 报告的 11 个数据集、XTab 的 heavy finetuning（patience=3、轮数上限无穷，即训练到收敛为止）、TabM 的 46 个数据集实验都应普遍观察到同类现象，但原论文与后续工作均未把"无调度器"列为已知的稳定性风险点（本次全文检索均未发现相关讨论）。
2. **唯一报告过 FT-Transformer 训练期震荡的文献（Matérn-KAN，物理页 8）明确把原因归为数据集规模过小**（"largely due to the extremely small size of the Pmat‡ dataset"），而非学习率调度缺失；该文献本身也没有加调度器，其余数据集上同样没有出现震荡。这提示"震荡"更可能与数据规模、批大小、具体数据分布相关，而非调度器有无这一单一变量。
3. **唯一使用调度器的工作（electronics IoT）没有做消融**——它只是在报告"训练稳定、无明显震荡"时把这归功于"学习率衰减 + 早停"的组合，但没有对照"不加衰减会怎样"的实验，因此这条证据只能算方向一致的经验性佐证，强度不足以支撑因果结论。

**如实报告的局限**：本次核查是文献层面的横向对照，不是本课题自身的消融实验；"是否加学习率衰减能缓解 C00-half 的后期震荡"这一问题，**只能通过在本课题数据上实际做一次"加/不加衰减"的对照实验来回答**，文献证据只能说明"缺少调度器不是这一研究谱系的反常做法"，不能替代本课题自己的因果验证。

---

## 无法核实的部分

- 本课题批量大小、原论文各数据集具体批量数值：原论文只说"按数据集预先指定"，未给出跨数据集统一表格，本次核查未逐一定位附录数据集统计表中的批量数值（非核查重点，如需可另行核实）。
- Zotero 语义检索通道本次连接失败（`[Errno 61] Connection refused`），未能据此补充候选文献；本次候选发现依赖本地已有笔记 + 用户提供的文件清单 + 一次本地混合检索确认，不排除仍有个别使用 FT-Transformer 的工作未被覆盖。
- electronics IoT 论文"learning rate decay"的具体实现机制（衰减类型、系数、触发条件）全文未披露，无法进一步比对其与本课题若采用衰减时的候选实现是否同构。
- TabReD 论文附录 C（声称给出"精确调参超参数空间"）在本次转换的两段 PDF（物理页 1-20、21-35）中均未检索到对应的 AdamW/学习率/调度器关键词，可能是该部分以外部链接或补充材料形式提供，本次未继续追踪。
