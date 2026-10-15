# 检索笔记：第四章鲁棒家族补查

> 每完成一组查询立即追加。证据等级：`本地全文` / `在线全文已下载` / `仅摘要` / `仅题录`。

## P0 本地盘点（2026-10-15）

- 本地相关原件：
  - `raw/papers/methodology/2024-Pham-Nonstationary-Domain-Generalization.pdf`（3.0 MB）→ 已有结构化笔记 `wiki/papers/methodology/2024-Pham-非平稳域泛化AIRL.md`，证据等级 **本地全文**。
  - `raw/papers/attack-detection/2025-Feng-Wasserstein-DRO-Reachability-CPS-FDI-Detection.pdf` → 已有全文转换 `wiki/papers/attack-detection/2025-Feng-Wasserstein-DRO-Reachability-CPS-FDI-Detection-全文.md`，证据等级 **本地全文**（但为 CPS 控制类，非恶意软件）。
- 库内已有方法论近邻（`wiki/papers/methodology/INDEX.md`）：
  - GroupDRO 2020（群体移位）、DIVERSIFY（2024 潜在域时序 OOD）、FOIL（2024 时序 OOD 不变）、Pham AIRL（2024 非平稳 DG）、Ahuja IIB（2021 不变性不足）。
- **缺口确认**：`rg` 全库 `Gulrajani|Lost Domain Generalization|DomainBed` 零命中（仅命中 Krawczyk 笔记里同姓的 WGAN-GP 作者 Ishaan Gulrajani，非 DomainBed）。SWAD 零命中。
- 本地混合索引已坏（不修），用 `rg` + Zotero 语义检索替代。

## 工具可用性

- `mineru-open-api`：`~/.local/bin/mineru-open-api` 可用。
- `scholar`：`~/.local/bin/scholar` 可用；默认无代理环境变量，需内联 `HTTPS_PROXY=http://127.0.0.1:7890`。

## P2 问 1：ERM vs DG 批评的后续（检索中）

### 检索式与来源

1. WebSearch `"In Search of Lost Domain Generalization" DomainBed follow-up 2024 2025 ERM still competitive`
2. WebSearch `SWAD stochastic weight averaging densely domain generalization`
3. Zotero semantic: `domain generalization benchmark ERM in search of lost domain generalization`

### 命中

| 候选 | 作者/年份 | Venue | 证据等级 | 相关性 | 状态 |
|---|---|---|---|---|---|
| In Search of Lost Domain Generalization (DomainBed) | Gulrajani & Lopez-Paz 2021 | ICLR 2021 (arXiv 2007.01434) | 仅题录（待取全文） | **核心缺口**：统一协议重评，ERM 追平/超过多数 DG 方法 | 库内零命中，待入库 |
| SWAD: Domain Generalization by Seeking Flat Minima | Cha et al. 2021 | NeurIPS 2021 (arXiv 2102.08604) | 仅摘要 | ERM 求平坦极小；Dense SWA，+1.6% 平均 OOD，成为强基线 | 待取全文 |
| Lost Domain Generalization Is a Natural Consequence of Lack of Training Domains | 2024 | AAAI 2024 | 仅摘要 | **对 Gulrajani 结论的理论解释**：训练域太少（≤6）是根因，证明需要 Ω(1/ε²) 训练域 | 待核 |
| Is Large-scale Pretraining the Secret to Good Domain Generalization? | 2024 | arXiv 2412.02856 | 仅摘要 | 提出 DomainBed-OOP / DomainBed-IP 新协议变体 | 待核 |

### 关键结论（初判）

- Gulrajani 结论**未被推翻**：2024–2025 仍以 DomainBed 为协议、ERM（ERM++）为参照基线。
- 后续主要有三条：(a) 提升 ERM 本身（SWAD 平坦极小）；(b) 理论解释 ERM 为何难被打败（训练域数量不足）；(c) 新协议变体（DomainBed-OOP/IP、大规模预训练）。
- Zotero 库含 Pham (4CDFBCI3)，说明已有相关条目但无 DomainBed。

### 待办

- 取 DomainBed / SWAD / AAAI2024 全文并入库。
- 补检 DG 综述（2023–2025）。

## P3 问 2：非平稳／持续域泛化（2023–2026）

### 检索式
- WebSearch `continual domain generalization survey 2024 2025 non-stationary environments benchmark`
- WebSearch `continual domain generalization sequential domains method 2024 2025 temporal domain generalization paper`

### 关键结论：存在成熟子领域 **Temporal Domain Generalization (TDG)** / **Evolving Domain Generalization**

TDG 的问题设置与本课题「按年份有序域、目标为未来域」高度同构：给定连续源域 D_1…D_T，泛化到未见未来域 D_{T+1}。家族代表（时间序）：

| 候选 | 作者/年份 | Venue | 证据等级 | 相关性 |
|---|---|---|---|---|
| Non-stationary Domain Generalization: Theory and Algorithm (AIRL) | Pham, Zhang, Zhang 2024 | PMLR 244 (ACML) | **本地全文** | 有序源域间学自适应不变表示；已入库 |
| Temporal DG with Drift-Aware Dynamic Neural Networks (DRAIN) | Bai, Ling, Zhao 2022 | NeurIPS 2022 (arXiv 2205.10664) | 在线全文已下载 | TDG 奠基作；贝叶斯递归 + 动态网络 |
| Evolving Standardization / Dynamic Latent Rep. | AAAI 2024 | AAAI 2024 | 仅摘要 | 持续 DG over temporal drift |
| Generalizing Across Temporal Domains with Koopman Operators | 2024 | AAAI 2024 | 仅摘要 | 用 Koopman 算子建模时间演化 |
| Continuous Temporal Domain Generalization | 2024 | NeurIPS 2024 | 仅摘要 | 连续（非离散）TDG |
| CODA: Temporal DG via Concept Drift Simulator | Chang et al. 2025 | KDD 2025 (arXiv 2310.01508) | 在线全文已下载 | 模型无关、数据中心；预测未来特征相关矩阵生成未来数据 |
| SYNC: Time-Aware Causal Representation for Evolving Domains | He et al. 2025 | ICML 2025 (PMLR 267) | 仅摘要 | 时序 SCM + 序列 VAE 学时间感知因果表示 |
| Scalable TDG via Prompting | 2025 | ICML 2025 | 仅摘要 | 提示/prompting 的 TDG |
| EvoCL: Continual Learning over Evolving Domains | 2025 | WACV 2025 | 仅摘要 | 超网络 + 域嵌入预测下一域 |
| FreKoo: Learning Robust Spectral Dynamics for TDG | 2025 | arXiv 2505.12585 | 在线全文已下载（未深读） | Koopman + 频域，处理复杂/周期漂移 |
| TEA: Scaling Up TDG via Temporal Experts Averaging | 2025 | arXiv | 仅摘要 | 时序专家权重平均 |

### 判断

- 这一支**已成熟**（有独立子领域命名、跨 venue 系列、多篇 2024–2025）。库内目前只有 Pham 一篇 + DIVERSIFY/FOIL（潜在域时序 OOD），**代表性不足**。
- DRAIN 是奠基锚点，CODA 是最新（KDD 2025）且模型无关，二者最值得入库。

## P4 问 3：按时序/组分组的 DRO

### 检索式
- WebSearch `temporal distributionally robust optimization group DRO time series distribution shift 2023 2024`
- WebSearch `distributionally robust optimization malware detection concept drift Android annual distribution shift`
- WebSearch `group DRO new variant 2024 2025 worst-group robustness`

### (a) 时序 DRO（DRO over time）

| 候选 | 作者/年份 | Venue | 证据等级 | 相关性 |
|---|---|---|---|---|
| Data-driven DRO over Time | Aigner et al. 2023 | INFORMS J. Optimization 5(4):376-394 (arXiv 2304.05377) | 在线全文已下载 | 在线学习 + 数据流，**regret O(log T/√T)**；随时间收缩模糊集 |
| TDRO: Temporally and Distributionally Robust Optimization for Cold-Start Recommendation | Lin et al. 2024 | AAAI 2024 (arXiv 2312.09901) | 在线全文已下载 | **worst-case 因子 + shifting 因子**双目标；组分权 + 流式损失估计 |

### (b) GroupDRO 新变体（2024–2025）

| 候选 | 年份 | Venue | 证据等级 | 要点 |
|---|---|---|---|---|
| MEDRO: Multi-Expert DRO for OOD Generalization | 2025 | NeurIPS 2025 | 仅摘要 | 共享特征提取 + 多专家，扩展 GroupDRO 应对大环境间差异 |
| Hierarchical Ambiguity Sets for Spurious Correlation | 2025 | NeurIPS 2025 | 仅摘要 | 分层模糊集，兼顾组间 + 组内不确定性（Wasserstein） |
| Group-DRO under Group-Level Distributional Uncertainty | 2025 | arXiv 2509.08942 | 仅摘要 | Wasserstein DRO 覆盖组内分布不确定性 |
| Bitrate-Constrained DRO (BR-DRO) | 2022 | NeurIPS 2022 | 仅摘要 | 无需训练期组标注即可匹配 GroupDRO |
| CTC-DRO | 2025 | arXiv 2502.01777 | 仅摘要 | 组权重更新平滑 + 长度匹配批，处理损失尺度导致的伪组差 |

### (c) DRO 用于恶意软件/入侵检测

- **未发现**把 Wasserstein/DRO 明确用于「年度序列 Android 恶意软件」的工作（这是一处空白）。
- 最接近：
  - **TIF: Learning Temporal Invariance in Android Malware Detectors**（Zheng, Yang, Ngai, Jana, Cavallaro; arXiv 2502.05098）——**IRM 家族**：把 AndroZoo 2014–2023 按提交日期切成不相交环境，用 MPC + IGA（IRM 梯度对齐）学时序不变表示，直接对抗 detector aging。**与本课题第四章候选最贴近的近邻。** 证据等级：在线全文已下载。
  - **Adversarial Vulnerability Under Temporal Concept Drift: A Longitudinal Study of Android Malware Detection**（Sabbah et al.; arXiv 2605.23623）——纵向年度研究（same-year / cross-year / expanding-window），提出 AAF 等时序指标；结论为 expanding-window 重训缓解但不消除鲁棒性损失。证据等级：在线全文已下载。
  - Feng et al. 2025 Wasserstein-DRO（本地全文）——CPS 控制 FDI 检测，非恶意软件。

### 待办
- 入库上述核心 PDF 并写结构化笔记。

## P5 入库完成（2026-10-15）

- 10 篇 PDF 入 `raw/papers/`（8 methodology + 2 lamda-related），10 篇结构化笔记入 `wiki/papers/`（八字段齐全），10 篇 `-全文.md` 经 MinerU `extract` 生成。
- INDEX 更新：methodology 新增三节、attack-detection 新增一节。
- Zotero 入库 10 条：DomainBed `H5RVGBAW`、SWAD `CW762DBG`、TIF `VXKEXXMB`、DRAIN `RT2R6QBM`、CODA `HPM8N46B`、TDRO `EMPDGQKG`、DRO-overtime `RGMKCCST`、Teterwak `CXBA8E67`、Sabbah `JEKQND2B`、LostDG-AAAI24 `J296PXGR`。
- 报告：`.Codex/docs/2026-10-15-第四章鲁棒家族补查/报告.md`。

## 工具故障

- `scholar` CLI 全程 429（4 次），未取得结果。
- 论文检索类 MCP 本会话未加载；citation-verification 技能未用（改 arXiv/DOI 元数据直查）。
- 本地混合索引坏（按要求不修）。
